from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ...assets import resolve_asset
from ...provenance import stable_hash
from ...providers.models.base import (
    StructuredModelFailureKind,
    StructuredModelProvider,
    StructuredModelProviderError,
)
from ...schemas.paper_case import EvidenceSpan, PaperCase, PaperCaseReview, PaperCaseReviewStatus
from ...schemas.paper_ingest import (
    EvidenceSpanVerification,
    ExternalPaperRecord,
    PaperExtractionSourcePacket,
    PaperExtractionWindow,
    PaperSourceChunk,
    PaperSourceSpan,
    ParseCompletenessReport,
    ParsedPaper,
    TextBBox,
)
from ...schemas.question_pattern import (
    QuestionFormationTrace,
    QuestionFormationTraceReviewStatus,
)
from .verifier import EvidenceSpanVerifier, _normalize_text

FREE_QUOTE_PROMPT_VERSION = "paper_case_extractor/v2"
SOURCE_SPAN_PROMPT_VERSION = "paper_case_extractor/v8"
SOURCE_SPAN_TEXT_VERSION = "source_span/poppler_layout_line/v1"
PDFPLUMBER_SOURCE_TEXT_VERSION = "source_span/pdfplumber_line/v1"
FALLBACK_SOURCE_TEXT_VERSION = "source_span/parsed_block_line/v1"
STRUCTURED_OUTPUT_MAX_ATTEMPTS = 3


class _ExtractionPaperCase(PaperCase):
    """Model-facing PaperCase used ONLY as the extraction ``output_model``.

    Blocker #1: the extractor asks the model to fill the WHOLE PaperCase, so the model also supplies the
    self-declared verification statuses. A ``formation_trace`` the model marks ``span_verified`` whose
    ``evidence_bindings`` cite span ids outside ``evidence_span_ids`` crashes ``PaperCase.model_validate``
    (the ⊆ rule fires DURING construction), discarding the whole good case before any in-repo logic runs.
    This variant pins the model-supplied ``formation_trace.review_status`` to DRAFT BEFORE field
    validation — the pre-validation mirror of the post-construction ``_reset_model_supplied_review_status``
    (which handles the sibling ``review.status``) — so the case survives; the repo then EARNS promotion
    from verified spans. The strict PaperCase /
    QuestionFormationTrace validators are UNCHANGED (never weakened); the extractor converts this back to
    a plain ``PaperCase`` immediately after parsing.
    """

    @model_validator(mode="before")
    @classmethod
    def _pin_model_supplied_formation_trace_status(cls, data: Any) -> Any:
        # Accept a parent PaperCase instance (mock/test providers hand back an instance, not a dict) by
        # dumping to a dict first — pydantic will not coerce a parent instance into this subclass.
        if isinstance(data, BaseModel):
            data = data.model_dump(mode="python")
        if isinstance(data, dict):
            # Pin ONLY the formation_trace status: its ⊆ validator crashes DURING construction, so the
            # post-construction reset is too late. The sibling `review.status` is intentionally left for
            # `_reset_model_supplied_review_status` (extraction.py:~106), which resets it AND records the
            # honest "ignored model-supplied review status" correction (a reset here would silence that).
            trace = data.get("formation_trace")
            if isinstance(trace, dict):
                trace["review_status"] = QuestionFormationTraceReviewStatus.DRAFT.value
        return data


def _formation_trace_span_verifiable(trace: QuestionFormationTrace) -> bool:
    """True iff ``trace`` genuinely satisfies the strict span-verified requirements — re-validated
    through the REAL ``QuestionFormationTrace`` validator (no duplicated rule logic). Gates the in-repo
    SPAN_VERIFIED promotion so an inconsistent trace is never falsely marked verified (``PaperCase`` has
    no ``validate_assignment``, so a raw ``review_status = SPAN_VERIFIED`` assignment would not catch it)."""
    try:
        QuestionFormationTrace.model_validate(
            {
                **trace.model_dump(mode="python"),
                "review_status": QuestionFormationTraceReviewStatus.SPAN_VERIFIED.value,
            }
        )
        return True
    except ValidationError:
        return False


class PaperCaseExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_case: PaperCase | None = None
    source_packet: PaperExtractionSourcePacket
    span_verifications: list[EvidenceSpanVerification] = Field(default_factory=list)
    model_called: bool = False
    blocked_reason: str = ""
    # Generator provenance: recorded so the downstream fidelity gate can attest who/what
    # produced this PaperCase and enforce cross-provider independence.
    provider_id: str = ""
    model_id: str = ""
    prompt_version: str = ""
    input_digest: str = ""
    output_digest: str = ""


class PaperCaseExtractionPipeline:
    def __init__(
        self,
        provider: StructuredModelProvider,
        *,
        prompt_path: Path | None = None,
        max_context_chars: int = 250_000,
        evidence_mode: str = "free_quote",
    ):
        self.provider = provider
        self.evidence_mode = _normalize_evidence_mode(evidence_mode)
        self.prompt_version = (
            SOURCE_SPAN_PROMPT_VERSION
            if self.evidence_mode == "source_span"
            else FREE_QUOTE_PROMPT_VERSION
        )
        self.prompt_path = prompt_path or _default_prompt_path(self.prompt_version)
        self.max_context_chars = max_context_chars
        self.verifier = EvidenceSpanVerifier()

    def extract(
        self,
        *,
        parsed: ParsedPaper,
        completeness: ParseCompletenessReport,
        external_record: ExternalPaperRecord | None = None,
    ) -> PaperCaseExtractionResult:
        packet = build_source_packet(
            parsed=parsed,
            completeness=completeness,
            external_record=external_record,
            max_context_chars=self.max_context_chars,
            prompt_version=self.prompt_version,
            include_chunks=self.evidence_mode != "source_span",
        )
        source_capable = bool(
            packet.source_spans if self.evidence_mode == "source_span" else packet.chunks
        )
        if not source_capable:
            return PaperCaseExtractionResult(
                source_packet=packet,
                model_called=False,
                blocked_reason="text_unavailable",
            )
        if _packet_prompt_size(packet, self._system_prompt()) > self.max_context_chars:
            packet.full_context_provided = False
            warning = "serialized_prompt_exceeds_single_call_budget; bounded extraction required"
            if warning not in packet.warnings:
                packet.warnings.append(warning)
        if not packet.full_context_provided:
            if self.evidence_mode != "source_span":
                return PaperCaseExtractionResult(
                    source_packet=packet,
                    model_called=False,
                    blocked_reason="source_packet_exceeds_single_call_budget",
                )
            windows = _bounded_source_packets(
                packet,
                system_prompt=self._system_prompt(),
                max_context_chars=self.max_context_chars,
            )
            if not windows:
                return PaperCaseExtractionResult(
                    source_packet=packet,
                    model_called=False,
                    blocked_reason="source_packet_exceeds_bounded_prompt_budget",
                )
            results = [self._extract_packet(parsed=parsed, packet=window) for window in windows]
            result = _merge_window_results(
                results,
                parsed=parsed,
                full_packet=packet,
                verifier=self.verifier,
            )
            window_input_digests = [stable_hash(window) for window in windows]
            aggregate_input_digest = stable_hash(
                {
                    "source_packet": packet.model_dump(mode="json", exclude={"extraction_windows"}),
                    "window_input_digests": window_input_digests,
                }
            )
            extraction_windows = [
                PaperExtractionWindow(
                    window_id=window.packet_id,
                    source_span_ids=[span.span_id for span in window.source_spans],
                    context_char_count=window.context_char_count,
                    input_digest=window_input_digests[index],
                    output_digest=results[index].output_digest,
                )
                for index, window in enumerate(windows)
            ]
            packet = PaperExtractionSourcePacket.model_validate(
                packet.model_copy(update={"extraction_windows": extraction_windows}).model_dump(
                    mode="python"
                )
            )
            result.source_packet = packet
            result.input_digest = aggregate_input_digest
        else:
            result = self._extract_packet(parsed=parsed, packet=packet)

        if not completeness.is_complete and result.paper_case is not None:
            request = (
                "EvidenceRequest[parse_completeness_degraded]: parser-owned text was usable, but "
                "the parse completeness report recorded limitations; review before authority raise."
            )
            if request not in result.paper_case.evidence_requests:
                result.paper_case.evidence_requests.append(request)
            result.paper_case.review = PaperCaseReview(
                status=PaperCaseReviewStatus.EXTRACTED,
                corrections=list(result.paper_case.review.corrections),
                note="Source-capable degraded parse; completeness diagnostics remain authoritative.",
            )
            result.output_digest = stable_hash(result.paper_case)
        return result

    def _extract_packet(
        self,
        *,
        parsed: ParsedPaper,
        packet: PaperExtractionSourcePacket,
    ) -> PaperCaseExtractionResult:
        model_case: _ExtractionPaperCase | None = None
        for attempt in range(1, STRUCTURED_OUTPUT_MAX_ATTEMPTS + 1):
            try:
                model_case = self.provider.generate_structured(
                    system_prompt=self._system_prompt(),
                    user_prompt=json.dumps(
                        packet.model_dump(mode="json"), ensure_ascii=False, indent=2
                    ),
                    output_model=_ExtractionPaperCase,
                )
                break
            except StructuredModelProviderError as exc:
                # A schema-invalid response is not evidence that the paper is unusable. Replay the
                # identical source packet within one clear three-attempt budget; non-schema failures
                # and the final invalid response still fail closed with the provider's original error.
                if (
                    exc.kind != StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID
                    or attempt >= STRUCTURED_OUTPUT_MAX_ATTEMPTS
                ):
                    raise
        if model_case is None:  # pragma: no cover - loop either returns a model or raises
            raise AssertionError("structured extraction ended without a model result")
        # Blocker #1(1a): the model-facing variant pinned the self-declared statuses at construction
        # (an over-claimed span_verified trace can no longer crash model_validate). Convert to a strict
        # PaperCase — the draft/extracted statuses validate clean; verification is EARNED below.
        paper_case = PaperCase.model_validate(model_case.model_dump(mode="python"))
        paper_case.review = _reset_model_supplied_review_status(paper_case.review)
        if paper_case.source_pdf and paper_case.source_pdf != parsed.source_pdf:
            paper_case.review.corrections.append(
                "Replaced model-supplied source_pdf with the parser-owned source_pdf."
            )
        if paper_case.source_sha256 and paper_case.source_sha256 != parsed.source_sha256:
            paper_case.review.corrections.append(
                "Replaced model-supplied source_sha256 "
                f"{paper_case.source_sha256} with parser-owned digest {parsed.source_sha256}."
            )
        paper_case.source_pdf = parsed.source_pdf
        paper_case.source_sha256 = parsed.source_sha256
        paper_case.review.corrections.extend(
            _anchor_parser_owned_spans(
                paper_case,
                packet,
                require_source_spans=self.evidence_mode == "source_span",
            )
        )
        paper_case.review.corrections.extend(
            _materialize_formation_trace_evidence_spans(
                paper_case,
                packet,
                require_source_spans=self.evidence_mode == "source_span",
            )
        )
        trace_requests = _formation_trace_evidence_requests(
            paper_case,
            packet,
            require_source_spans=self.evidence_mode == "source_span",
        )
        if trace_requests:
            # An inline trace is optional extraction assistance, not the PaperCase identity. Keep
            # strict parser-locator validation, but discard only the unusable draft so the valid case
            # can proceed to independent review and the dedicated trace stage can generate a fresh one.
            paper_case.formation_trace = None
            paper_case.review.corrections.append(
                "Dropped model-supplied inline formation_trace after parser-owned locator "
                "validation failed; the dedicated trace stage must generate a fresh draft."
            )
            for request in trace_requests:
                if request not in paper_case.evidence_requests:
                    paper_case.evidence_requests.append(request)
        verifications = self.verifier.verify_paper_case(
            paper_case,
            parsed,
            source_spans=packet.source_spans,
            require_source_spans=self.evidence_mode == "source_span",
        )
        repairs = _repair_wrong_page_spans(paper_case, verifications, parsed, self.verifier)
        if repairs:
            paper_case.review.corrections.extend(repairs)
            verifications = self.verifier.verify_paper_case(
                paper_case,
                parsed,
                source_spans=packet.source_spans,
                require_source_spans=self.evidence_mode == "source_span",
            )
        # Blocker #1(1b): only local verification earns SPAN_VERIFIED — and only for a trace that
        # GENUINELY satisfies the strict validator. If the model's trace can't earn it (e.g. bindings
        # cite spans outside evidence_span_ids), surface an evidence request so the gate below keeps the
        # case an honest NEEDS_REVIEW instead of the :142 assignment minting a false span_verified
        # (no validate_assignment) that would crash a later re-validate.
        if paper_case.formation_trace is not None and not _formation_trace_span_verifiable(
            paper_case.formation_trace
        ):
            request = (
                "EvidenceRequest[formation_trace_not_span_verifiable]: formation_trace evidence is "
                "inconsistent (e.g. binding source_span_ids outside evidence_span_ids); kept DRAFT."
            )
            if request not in paper_case.evidence_requests:
                paper_case.evidence_requests.append(request)
        if (
            verifications
            and all(item.verified for item in verifications)
            and not paper_case.evidence_requests
        ):
            if paper_case.formation_trace is not None:
                paper_case.formation_trace.review_status = (
                    QuestionFormationTraceReviewStatus.SPAN_VERIFIED
                )
            paper_case.review = PaperCaseReview(
                status=PaperCaseReviewStatus.SPAN_VERIFIED,
                previous_status=paper_case.review.status,
                corrections=paper_case.review.corrections,
                note="All model-cited evidence spans verified against parsed local PDF text.",
            )
        else:
            failed = [item for item in verifications if not item.verified]
            for item in failed:
                request = (
                    f"EvidenceRequest[{item.issue_code or 'unverified_span'}]: "
                    f"{item.field} page {item.page}: {item.note}"
                )
                if request not in paper_case.evidence_requests:
                    paper_case.evidence_requests.append(request)
        return PaperCaseExtractionResult(
            paper_case=paper_case,
            source_packet=packet,
            span_verifications=verifications,
            model_called=True,
            provider_id=str(getattr(self.provider, "provider_name", "")),
            model_id=str(getattr(self.provider, "model_name", "")),
            prompt_version=self.prompt_version,
            input_digest=stable_hash(packet),
            output_digest=stable_hash(paper_case),
        )

    def _system_prompt(self) -> str:
        return self.prompt_path.read_text(encoding="utf-8")


def _bounded_source_packets(
    packet: PaperExtractionSourcePacket,
    *,
    system_prompt: str,
    max_context_chars: int,
) -> list[PaperExtractionSourcePacket]:
    """Partition source spans deterministically while keeping every model call under the hard bound."""
    ordered = sorted(packet.source_spans, key=lambda span: (span.page, span.span_id))
    windows: list[PaperExtractionSourcePacket] = []
    current: list[PaperSourceSpan] = []

    def candidate(spans: list[PaperSourceSpan], index: int) -> PaperExtractionSourcePacket:
        return packet.model_copy(
            update={
                "packet_id": f"{packet.packet_id}.window{index:04d}",
                "source_spans": list(spans),
                "extraction_windows": [],
                "full_context_provided": True,
                "context_char_count": sum(len(span.text_exact) for span in spans),
            },
            deep=True,
        )

    def fits(value: PaperExtractionSourcePacket) -> bool:
        return _packet_prompt_size(value, system_prompt) <= max_context_chars

    for span in ordered:
        proposed = candidate([*current, span], len(windows) + 1)
        if fits(proposed):
            current.append(span)
            continue
        if not current:
            return []
        windows.append(candidate(current, len(windows) + 1))
        current = [span]
        if not fits(candidate(current, len(windows) + 1)):
            return []
    if current:
        windows.append(candidate(current, len(windows) + 1))
    return windows


def _packet_prompt_size(packet: PaperExtractionSourcePacket, system_prompt: str) -> int:
    user = json.dumps(packet.model_dump(mode="json"), ensure_ascii=False, indent=2)
    return len(system_prompt) + len(user)


def _merge_window_results(
    results: list[PaperCaseExtractionResult],
    *,
    parsed: ParsedPaper,
    full_packet: PaperExtractionSourcePacket,
    verifier: EvidenceSpanVerifier,
) -> PaperCaseExtractionResult:
    """Merge bounded extractions without hiding identity or scientific-content conflicts."""
    if not results or any(result.paper_case is None for result in results):
        raise AssertionError("bounded extraction produced an empty PaperCase result")
    cases = [result.paper_case for result in results if result.paper_case is not None]
    base = cases[0].model_copy(deep=True)
    for case in cases[1:]:
        if case.paper_case_id != base.paper_case_id:
            raise ValueError("bounded extraction returned conflicting paper_case_id values")
        if case.source_sha256 != base.source_sha256:
            raise ValueError("bounded extraction returned conflicting source_sha256 values")
        existing_spans = {stable_hash(span) for span in base.evidence_spans}
        for span in case.evidence_spans:
            digest = stable_hash(span)
            if digest not in existing_spans:
                base.evidence_spans.append(span)
                existing_spans.add(digest)
        for request in case.evidence_requests:
            if request not in base.evidence_requests:
                base.evidence_requests.append(request)
        for correction in case.review.corrections:
            if correction not in base.review.corrections:
                base.review.corrections.append(correction)
        if _scientific_case_projection(case) != _scientific_case_projection(base):
            request = (
                "EvidenceRequest[bounded_window_scientific_conflict]: extraction windows returned "
                "different scientific descriptions; the first is retained pending review."
            )
            if request not in base.evidence_requests:
                base.evidence_requests.append(request)

    base.review = PaperCaseReview(
        status=PaperCaseReviewStatus.EXTRACTED,
        corrections=list(base.review.corrections),
        note=f"Merged deterministically from {len(cases)} bounded source-span windows.",
    )
    verifications = verifier.verify_paper_case(
        base,
        parsed,
        source_spans=full_packet.source_spans,
        require_source_spans=True,
    )
    for item in verifications:
        if item.verified:
            continue
        request = (
            f"EvidenceRequest[{item.issue_code or 'unverified_span'}]: "
            f"{item.field} page {item.page}: {item.note}"
        )
        if request not in base.evidence_requests:
            base.evidence_requests.append(request)
    validated = PaperCase.model_validate(base.model_dump(mode="python"))
    return PaperCaseExtractionResult(
        paper_case=validated,
        source_packet=full_packet,
        span_verifications=verifications,
        model_called=True,
        provider_id=results[0].provider_id,
        model_id=results[0].model_id,
        prompt_version=results[0].prompt_version,
        input_digest=stable_hash(full_packet),
        output_digest=stable_hash(validated),
    )


def _scientific_case_projection(case: PaperCase) -> dict[str, Any]:
    payload = case.model_dump(mode="json")
    for field in (
        "evidence_spans",
        "evidence_requests",
        "review",
        "created_at",
        "source_pdf",
        "source_sha256",
    ):
        payload.pop(field, None)
    return payload


def extract_product_paper_case(
    provider: StructuredModelProvider,
    *,
    parsed: ParsedPaper,
    completeness: ParseCompletenessReport,
    external_record: ExternalPaperRecord | None = None,
    max_context_chars: int = 250_000,
) -> PaperCaseExtractionResult:
    """Product PaperCase extraction — ALWAYS the ``paper_case_extractor/v8`` source-span path.

    The free-quote (``paper_case_extractor/v2``) mode stays reachable only by constructing
    ``PaperCaseExtractionPipeline(evidence_mode="free_quote")`` explicitly (legacy/dev compatibility);
    the product path never silently uses it. Records generator provenance on the result.
    """
    return PaperCaseExtractionPipeline(
        provider, evidence_mode="source_span", max_context_chars=max_context_chars
    ).extract(parsed=parsed, completeness=completeness, external_record=external_record)


def _reset_model_supplied_review_status(review: PaperCaseReview) -> PaperCaseReview:
    if review.status == PaperCaseReviewStatus.EXTRACTED:
        return review
    corrections = list(review.corrections)
    corrections.append(
        f"Ignored model-supplied PaperCase review status {review.status.value}; "
        "local verification controls review promotion."
    )
    return PaperCaseReview(
        status=PaperCaseReviewStatus.EXTRACTED,
        reviewer=review.reviewer,
        reviewed_at=review.reviewed_at,
        corrections=corrections,
        note=review.note,
    )


def _repair_wrong_page_spans(
    paper_case: PaperCase,
    verifications: list[EvidenceSpanVerification],
    parsed: ParsedPaper,
    verifier: EvidenceSpanVerifier,
) -> list[str]:
    repairs: list[str] = []
    for index, verification in enumerate(verifications):
        if verification.verified or verification.issue_code != "quote_not_found":
            continue
        span = paper_case.evidence_spans[index]
        repaired_page = verifier.suggested_page_repair(span, parsed)
        if repaired_page is None:
            continue
        original_page = span.page
        span.page = repaired_page
        repairs.append(
            f"Corrected evidence page for {span.field}: {original_page} -> {repaired_page}."
        )
    return repairs


def build_source_packet(
    *,
    parsed: ParsedPaper,
    completeness: ParseCompletenessReport,
    external_record: ExternalPaperRecord | None = None,
    max_context_chars: int = 250_000,
    prompt_version: str = FREE_QUOTE_PROMPT_VERSION,
    include_chunks: bool = True,
) -> PaperExtractionSourcePacket:
    chunks: list[PaperSourceChunk] = []
    total = 0
    if include_chunks:
        for block in sorted(parsed.blocks, key=lambda item: (item.page_number, item.block_id)):
            text = block.text.strip()
            if not text:
                continue
            total += len(text)
            chunks.append(
                PaperSourceChunk(
                    chunk_id=block.block_id,
                    page_number=block.page_number,
                    section_title=block.section_title,
                    text=text,
                    token_estimate=max(1, len(text) // 4),
                )
            )
    warnings = list(parsed.warnings)
    source_spans = build_source_spans(parsed, warnings=warnings)
    total += sum(len(span.text_exact) for span in source_spans)
    full_context = total <= max_context_chars
    if not full_context:
        warnings.append(
            "source_packet_exceeds_single_call_budget; chunked extraction is required before GPT call"
        )
    return PaperExtractionSourcePacket(
        packet_id=f"packet-{stable_hash({'paper': parsed.paper_id, 'source': parsed.source_sha256, 'prompt': prompt_version})[:12]}",
        paper_id=parsed.paper_id,
        source_filename=Path(parsed.source_pdf).name,
        source_sha256=parsed.source_sha256,
        parser_name=parsed.parser_name,
        parser_config_hash=parsed.parser_config_hash,
        completeness=completeness,
        external_record=external_record,
        chunks=chunks,
        source_spans=source_spans,
        full_context_provided=full_context,
        context_char_count=total,
        warnings=warnings,
    )


def build_source_spans(
    parsed: ParsedPaper, *, warnings: list[str] | None = None
) -> list[PaperSourceSpan]:
    spans = _parsed_layout_line_source_spans(parsed)
    if spans:
        return spans
    spans = _pdfplumber_line_source_spans(parsed, warnings=warnings)
    if spans:
        return spans
    return _parsed_block_line_source_spans(parsed)


def _parsed_layout_line_source_spans(parsed: ParsedPaper) -> list[PaperSourceSpan]:
    spans: list[PaperSourceSpan] = []
    for page in sorted(parsed.pages, key=lambda item: item.page_number):
        for line in page.text.splitlines():
            parts = [part.strip() for part in re.split(r"\s{2,}", line.strip()) if part.strip()]
            if not parts:
                continue
            for column_index, part in enumerate(parts):
                text = " ".join(part.split())
                if len(text.split()) < 4:
                    continue
                spans.append(
                    _make_source_span(
                        parsed=parsed,
                        page=page.page_number,
                        text=text,
                        source_text_version=SOURCE_SPAN_TEXT_VERSION,
                        section_title=_section_for_page(parsed, page.page_number),
                        bbox=None,
                        column_index=column_index if len(parts) > 1 else None,
                        sequence=len(spans) + 1,
                    )
                )
    return spans


def _pdfplumber_line_source_spans(
    parsed: ParsedPaper, *, warnings: list[str] | None = None
) -> list[PaperSourceSpan]:
    pdf_path = Path(parsed.source_pdf)
    if not pdf_path.exists():
        return []
    try:
        import pdfplumber
    except ImportError:
        return []

    spans: list[PaperSourceSpan] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_index, page in enumerate(pdf.pages, start=1):
                words = page.extract_words(
                    x_tolerance=3,
                    y_tolerance=3,
                    keep_blank_chars=False,
                    use_text_flow=False,
                    expand_ligatures=True,
                )
                page_width = float(page.width or 0)
                for segment in _word_line_segments(words, page_width=page_width):
                    text = " ".join(str(word.get("text") or "") for word in segment).strip()
                    if len(text.split()) < 4:
                        continue
                    x0 = min(float(word.get("x0") or 0.0) for word in segment)
                    x1 = max(float(word.get("x1") or 0.0) for word in segment)
                    y0 = min(float(word.get("top") or 0.0) for word in segment)
                    y1 = max(float(word.get("bottom") or y0) for word in segment)
                    column_index = None
                    if page_width > 0:
                        column_index = 0 if ((x0 + x1) / 2) < (page_width / 2) else 1
                    spans.append(
                        _make_source_span(
                            parsed=parsed,
                            page=page_index,
                            text=text,
                            source_text_version=PDFPLUMBER_SOURCE_TEXT_VERSION,
                            section_title=_section_for_page(parsed, page_index),
                            bbox=TextBBox(page=page_index, x0=x0, y0=y0, x1=x1, y1=y1),
                            column_index=column_index,
                            sequence=len(spans) + 1,
                        )
                    )
    except Exception as exc:
        # Y2: was a silent `return []` that downgraded SPAN_VERIFIED→NEEDS_REVIEW (falls through to the
        # block-line fallback) AND masked real span-logic bugs. A PDF-library error (malformed PDF) is
        # expected → surface it + fall through so the paper still yields. A non-library error is a bug in
        # OUR segmentation logic → re-raise so it surfaces (Y1's per-paper diagnostic persists it) rather
        # than hiding as an empty span set. (build_source_packet runs pre-extraction, so re-raising a
        # malformed-PDF error would fail the whole paper — hence the narrow.)
        module = type(exc).__module__ or ""
        if not (module.startswith("pdfminer") or module.startswith("pdfplumber")):
            raise
        if warnings is not None:
            warnings.append(f"span_extraction_failed:{exc}")
        return []
    return spans


def _word_line_segments(
    words: list[dict[str, Any]], *, page_width: float
) -> list[list[dict[str, Any]]]:
    sorted_words = sorted(
        [word for word in words if str(word.get("text") or "").strip()],
        key=lambda word: (float(word.get("top") or 0.0), float(word.get("x0") or 0.0)),
    )
    lines: list[list[dict[str, Any]]] = []
    for word in sorted_words:
        top = float(word.get("top") or 0.0)
        if not lines:
            lines.append([word])
            continue
        previous_top = sum(float(item.get("top") or 0.0) for item in lines[-1]) / len(lines[-1])
        if abs(top - previous_top) <= 3.0:
            lines[-1].append(word)
        else:
            lines.append([word])

    segments: list[list[dict[str, Any]]] = []
    gap_threshold = max(28.0, page_width * 0.07) if page_width > 0 else 45.0
    for line in lines:
        ordered = sorted(line, key=lambda word: float(word.get("x0") or 0.0))
        current: list[dict[str, Any]] = []
        previous_x1: float | None = None
        for word in ordered:
            x0 = float(word.get("x0") or 0.0)
            if current and previous_x1 is not None and x0 - previous_x1 > gap_threshold:
                segments.append(current)
                current = []
            current.append(word)
            previous_x1 = float(word.get("x1") or x0)
        if current:
            segments.append(current)
    return segments


def _parsed_block_line_source_spans(parsed: ParsedPaper) -> list[PaperSourceSpan]:
    spans: list[PaperSourceSpan] = []
    for block in sorted(parsed.blocks, key=lambda item: (item.page_number, item.block_id)):
        lines = [line.strip() for line in block.text.splitlines() if line.strip()]
        candidates = [line for line in lines if len(line.split()) >= 4] or [block.text.strip()]
        for text in candidates:
            spans.append(
                _make_source_span(
                    parsed=parsed,
                    page=block.page_number,
                    text=text,
                    source_text_version=FALLBACK_SOURCE_TEXT_VERSION,
                    section_title=block.section_title,
                    bbox=block.bbox,
                    column_index=None,
                    sequence=len(spans) + 1,
                )
            )
    return spans


def _make_source_span(
    *,
    parsed: ParsedPaper,
    page: int,
    text: str,
    source_text_version: str,
    section_title: str,
    bbox: TextBBox | None,
    column_index: int | None,
    sequence: int,
) -> PaperSourceSpan:
    return PaperSourceSpan(
        span_id=f"{parsed.paper_id}.span{sequence:05d}",
        paper_id=parsed.paper_id,
        page=page,
        section_title=section_title,
        text_exact=text,
        source_text_version=source_text_version,
        text_norm_hash=stable_hash(_normalize_text(text)),
        bbox=bbox,
        column_index=column_index,
    )


def _section_for_page(parsed: ParsedPaper, page: int) -> str:
    for block in parsed.blocks:
        if block.page_number == page and block.section_title:
            return block.section_title
    return "full_text"


def _anchor_parser_owned_spans(
    paper_case: PaperCase,
    packet: PaperExtractionSourcePacket,
    *,
    require_source_spans: bool,
) -> list[str]:
    source_span_by_id = {span.span_id: span for span in packet.source_spans}
    corrections: list[str] = []
    for span in paper_case.evidence_spans:
        model_source_span_id = span.source_span_id
        source_span = source_span_by_id.get(model_source_span_id) if model_source_span_id else None
        if source_span is None and require_source_spans:
            if model_source_span_id:
                source_span = _find_same_page_exact_source_anchor(span, packet.source_spans)
            else:
                source_span = _find_same_page_source_anchor(span, packet.source_spans)
            if source_span is not None:
                span.source_span_id = source_span.span_id
                span.char_start = 0
                span.char_end = len(source_span.text_exact)
                corrections.append(
                    f"Anchored evidence quote for {span.field} to parser source span "
                    f"{source_span.span_id}."
                )
        if source_span is None:
            continue
        start = span.char_start if span.char_start is not None else 0
        end = span.char_end if span.char_end is not None else len(source_span.text_exact)
        if start < 0 or end < start or end > len(source_span.text_exact):
            continue
        quote = source_span.text_exact[start:end]
        if not quote:
            continue
        span.page = source_span.page
        span.section = source_span.section_title
        span.source_file = paper_case.source_pdf or packet.paper_id
        span.source_text_version = source_span.source_text_version
        span.quote_or_span = quote
    return corrections


def _formation_trace_evidence_requests(
    paper_case: PaperCase,
    packet: PaperExtractionSourcePacket,
    *,
    require_source_spans: bool,
) -> list[str]:
    trace = paper_case.formation_trace
    if trace is None:
        return []
    requests: list[str] = []
    if require_source_spans and not trace.evidence_span_ids:
        requests.append(
            "EvidenceRequest[formation_trace_missing_evidence_span_ids]: "
            "formation_trace requires parser-owned evidence_span_ids in source_span mode."
        )
        return requests
    if require_source_spans and not trace.evidence_bindings:
        requests.append(
            "EvidenceRequest[formation_trace_missing_evidence_bindings]: "
            "formation_trace requires role-specific evidence_bindings in source_span mode."
        )

    packet_span_ids = {span.span_id for span in packet.source_spans}
    case_span_ids = {
        span.source_span_id for span in paper_case.evidence_spans if span.source_span_id
    }
    missing_from_packet = sorted(set(trace.evidence_span_ids) - packet_span_ids)
    missing_from_case = sorted(set(trace.evidence_span_ids) - case_span_ids)
    if missing_from_packet:
        requests.append(
            "EvidenceRequest[formation_trace_invalid_source_span_id]: "
            "formation_trace references parser source spans not present in source packet: "
            + ", ".join(missing_from_packet)
        )
    if missing_from_case:
        requests.append(
            "EvidenceRequest[formation_trace_uncited_evidence_span_id]: "
            "formation_trace evidence_span_ids must also appear on PaperCase evidence_spans: "
            + ", ".join(missing_from_case)
        )
    binding_span_ids = {
        span_id for binding in trace.evidence_bindings for span_id in binding.source_span_ids
    }
    bindings_without_source_spans = [
        binding.role.value for binding in trace.evidence_bindings if not binding.source_span_ids
    ]
    if require_source_spans and bindings_without_source_spans:
        requests.append(
            "EvidenceRequest[formation_trace_binding_missing_source_span_ids]: "
            "source-span formation_trace evidence_bindings require source_span_ids: "
            + ", ".join(sorted(set(bindings_without_source_spans)))
        )
    binding_missing_from_packet = sorted(binding_span_ids - packet_span_ids)
    binding_missing_from_case = sorted(binding_span_ids - case_span_ids)
    if binding_missing_from_packet:
        requests.append(
            "EvidenceRequest[formation_trace_binding_invalid_source_span_id]: "
            "formation_trace evidence_bindings reference parser source spans not present "
            "in source packet: " + ", ".join(binding_missing_from_packet)
        )
    if binding_missing_from_case:
        requests.append(
            "EvidenceRequest[formation_trace_binding_uncited_source_span_id]: "
            "formation_trace evidence_bindings source_span_ids must also appear on "
            "PaperCase evidence_spans: " + ", ".join(binding_missing_from_case)
        )
    return requests


def _materialize_formation_trace_evidence_spans(
    paper_case: PaperCase,
    packet: PaperExtractionSourcePacket,
    *,
    require_source_spans: bool,
) -> list[str]:
    """Close honest trace-to-case span references from the parser-owned packet.

    The model receives parser span IDs and may cite a real packet span in the inline formation trace
    without redundantly emitting that span in ``PaperCase.evidence_spans``. The fidelity gate binds
    only against the PaperCase, so leaving that omission unrepaired turns a genuine same-PDF locator
    into a false evidence-resolution rejection. Materialize only exact IDs present in this packet;
    unknown IDs remain absent and are still surfaced by ``_formation_trace_evidence_requests`` and
    rejected by the downstream hard gate.
    """
    trace = paper_case.formation_trace
    if not require_source_spans or trace is None:
        return []

    referenced_ids = set(trace.evidence_span_ids)
    referenced_ids.update(
        span_id for binding in trace.evidence_bindings for span_id in binding.source_span_ids
    )
    case_span_ids = {
        span.source_span_id for span in paper_case.evidence_spans if span.source_span_id
    }
    packet_spans = {span.span_id: span for span in packet.source_spans}
    corrections: list[str] = []
    for span_id in sorted(referenced_ids - case_span_ids):
        source_span = packet_spans.get(span_id)
        if source_span is None:
            continue
        paper_case.evidence_spans.append(
            EvidenceSpan(
                field="formation_trace",
                page=source_span.page,
                section=source_span.section_title,
                quote_or_span=source_span.text_exact,
                source_file=packet.source_filename or paper_case.source_pdf,
                source_span_id=source_span.span_id,
                source_text_version=source_span.source_text_version,
                char_start=0,
                char_end=len(source_span.text_exact),
            )
        )
        corrections.append(
            f"Materialized formation-trace evidence from parser source span {source_span.span_id}."
        )
    return corrections


def _find_same_page_exact_source_anchor(
    span: EvidenceSpan, source_spans: list[PaperSourceSpan]
) -> PaperSourceSpan | None:
    quote = span.quote_or_span
    if not quote:
        return None
    candidates: list[PaperSourceSpan] = []
    for source_span in source_spans:
        if source_span.page != span.page:
            continue
        if quote == source_span.text_exact:
            candidates.append(source_span)
    return candidates[0] if len(candidates) == 1 else None


def _find_same_page_source_anchor(
    span: EvidenceSpan, source_spans: list[PaperSourceSpan]
) -> PaperSourceSpan | None:
    normalized_quote = _normalize_text(span.quote_or_span)
    if not normalized_quote:
        return None
    candidates: list[tuple[int, PaperSourceSpan]] = []
    for source_span in source_spans:
        if source_span.page != span.page:
            continue
        normalized_source = _normalize_text(source_span.text_exact)
        if len(normalized_source.split()) < 5:
            continue
        score = 0
        if normalized_quote in normalized_source:
            score = len(normalized_quote)
        elif normalized_source in normalized_quote:
            score = len(normalized_source)
        if score:
            candidates.append((score, source_span))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1].span_id))
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        return None
    return candidates[0][1]


def _normalize_evidence_mode(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"free_quote", "source_span"}:
        return normalized
    raise ValueError("evidence_mode must be free_quote or source_span")


def _default_prompt_path(prompt_version: str) -> Path:
    return resolve_asset(Path("prompts") / Path(prompt_version).with_suffix(".md"))
