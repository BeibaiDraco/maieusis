from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ...io import dump_data
from ...provenance import stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas.cited_literature import literature_context_digest
from ...schemas.paper_case import PaperCaseReviewStatus
from ...schemas.paper_ingest import (
    ExternalPaperRecord,
    PaperIdentityQuery,
    PaperIngestItem,
    PaperIngestRunManifest,
    PaperIngestStatus,
    paper_id_from_filename,
)
from ..paper_patterns.citation_importance import select_key_citations_product
from .cited_abstracts import build_paper_local_literature_context
from .external_lookup import (
    NullProcessedPaperLookupProvider,
    ProcessedPaperLookupProvider,
    SourceReferenceProvider,
    merge_external_records,
)
from .extraction import (
    FREE_QUOTE_PROMPT_VERSION,
    SOURCE_SPAN_PROMPT_VERSION,
    PaperCaseExtractionPipeline,
    build_source_packet,
    build_source_spans,
)
from .parsing import PdfParsingProvider, build_completeness_report, build_pdf_parser


@dataclass
class PaperIngestPipelineConfig:
    inbox_dir: Path = Path("corpus/papers/inbox")
    output_root: Path = Path("corpus")
    parser_name: str = "auto"
    provider_name: str = ""
    model_name: str = ""
    parse_only: bool = False
    external_lookup: bool = False
    cited_literature: bool = False
    select_key_citations: bool = False
    citation_prompt_char_budget: int = 120_000
    max_workers: int = 1
    resume: bool = False
    evidence_mode: str = "free_quote"
    # P1: when a paper's PDF-parsed bibliography is thinner than this, pull the paper's whole reference
    # list from a DOI-keyed source-reference provider (bypasses PDF parsing). 0 threshold + no providers
    # keeps the fallback off (unchanged default).
    min_local_reference_count: int = 10
    # Y1(c): where per-paper ingest diagnostics land (``<dir>/ingest/<paper>.yaml``). None ⇒ co-locate
    # inside the ingest tree at ``output_root/"diagnostics"``. The ingest corpus is SHARED across
    # run_ids (``config.run.output_root/ingest_corpus``), so there is no single ``runs/<id>`` at ingest
    # time; the diagnostic lives next to the cases/parsed artifacts it explains. Overridable here.
    diagnostics_dir: Path | None = None


# Y1(c): warnings whose presence (even on a SUCCESS status) means the paper survived but degraded, so
# its diagnostic should still be persisted for observability.
_INGEST_DIAGNOSTIC_WARNING_PREFIXES = (
    "cited_literature_build_failed",
    "span_extraction_failed",
    "parse_degraded",
    "supplied_text_hook_used",
)


class PaperIngestPipeline:
    def __init__(
        self,
        *,
        parser: PdfParsingProvider | None = None,
        supplied_text_parser: PdfParsingProvider | None = None,
        model_provider: StructuredModelProvider | None = None,
        lookup_providers: list[ProcessedPaperLookupProvider] | None = None,
        source_reference_providers: list[SourceReferenceProvider] | None = None,
        config: PaperIngestPipelineConfig | None = None,
    ):
        self.config = config or PaperIngestPipelineConfig()
        # An injected parser object wins; otherwise honor the configured parser name (the product
        # config default is poppler_text — the "auto" docling preference is dev-CLI opt-in).
        self.parser = parser or build_pdf_parser(self.config.parser_name)
        # Explicit caller-supplied safe-text hook only. Never auto-discovers sidecars and never turns
        # OCR/web lookup on implicitly.
        self.supplied_text_parser = supplied_text_parser
        self.model_provider = model_provider
        self.lookup_providers = lookup_providers or [NullProcessedPaperLookupProvider()]
        # P1: DOI-keyed whole-bibliography providers (Crossref/OpenAlex reference lists). When a paper
        # parses too few local references, these backfill the reference list so cited-work resolution
        # (and its abstracts) is not starved by imperfect PDF reference extraction. Empty = off.
        self.source_reference_providers = source_reference_providers or []

    def run(self, *, pilot: str | None = None, all_papers: bool = False) -> PaperIngestRunManifest:
        pdfs = self._select_pdfs(pilot=pilot, all_papers=all_papers)
        run_id = f"paper-ingest-{stable_hash({'time': datetime.now(UTC).isoformat(), 'pdfs': [p.name for p in pdfs]})[:12]}"
        manifest = PaperIngestRunManifest(
            run_id=run_id,
            inbox_dir=self.config.inbox_dir.as_posix(),
            output_root=self.config.output_root.as_posix(),
            parser=self.parser.parser_name,
            provider=self.config.provider_name,
            model=self.config.model_name,
            parse_only=self.config.parse_only,
            external_lookup=self.config.external_lookup,
            max_workers=self.config.max_workers,
            configuration={
                "resume": self.config.resume,
                "evidence_mode": self.config.evidence_mode,
                "cited_literature": self.config.cited_literature,
                "select_key_citations": self.config.select_key_citations,
            },
        )
        manifest.items.extend(self._process_pdfs(pdfs))
        manifest_path = self._manifest_dir() / f"{run_id}.yaml"
        dump_data(manifest, manifest_path)
        return manifest

    def _process_pdfs(self, pdfs: list[Path]) -> list[PaperIngestItem]:
        if self.config.max_workers <= 1 or len(pdfs) <= 1:
            return [self._process_pdf(pdf) for pdf in pdfs]
        workers = min(self.config.max_workers, len(pdfs))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            return list(executor.map(self._process_pdf, pdfs))

    def _select_pdfs(self, *, pilot: str | None, all_papers: bool) -> list[Path]:
        if pilot and all_papers:
            raise ValueError("Use either pilot or all_papers, not both")
        if all_papers:
            pdfs = sorted(self.config.inbox_dir.glob("*.pdf"))
        else:
            selected = pilot or "paper_001_theory_reuse.pdf"
            pdfs = [self.config.inbox_dir / selected]
        if not pdfs:
            raise ValueError(f"No PDF files found under {self.config.inbox_dir}")
        missing = [path for path in pdfs if not path.exists()]
        if missing:
            raise FileNotFoundError(f"Missing PDF(s): {', '.join(path.name for path in missing)}")
        return pdfs

    def _config_signature(self) -> str:
        """F5: a stable hash of the config fields that must invalidate a resume-skip when they change
        (a stale case must not survive a real config/code change). Does NOT include the parsed source
        sha / parser internals — those need a parse; a parser CODE change under the same name still
        requires clearing ``parsed/`` (documented). Provider/model/evidence_mode/prompt/parser/citation
        knobs are all available WITHOUT re-parsing, so the common config-change class is caught cheaply."""
        return stable_hash(
            {
                "provider": self.config.provider_name,
                "model": self.config.model_name,
                "evidence_mode": self.config.evidence_mode,
                "prompt_version": _prompt_version_for_evidence_mode(self.config.evidence_mode),
                "parser": self.config.parser_name,
                "cited_literature": self.config.cited_literature,
                "select_key_citations": self.config.select_key_citations,
                "min_local_reference_count": self.config.min_local_reference_count,
            }
        )

    def _process_pdf(self, pdf_path: Path) -> PaperIngestItem:
        # Y1(c): single finalization point — persist a per-paper diagnostic on every return path
        # (failure, parse-incomplete, or survived-but-degraded) so a low live yield leaves a findable
        # record of WHY, instead of a silent discard.
        item = self._ingest_one(pdf_path)
        self._persist_ingest_diagnostic(item)
        return item

    def _persist_ingest_diagnostic(self, item: PaperIngestItem) -> None:
        """Y1(c): write the PaperIngestItem (status + errors + warnings) to
        ``<diagnostics_dir or output_root/diagnostics>/ingest/<paper>.yaml`` when the paper failed,
        parse-incompleted, or survived-but-degraded. A best-effort observability write that must
        NEVER mask the real ingest outcome — a write failure is itself surfaced as a warning."""
        degraded = any(
            w.split(":", 1)[0] in _INGEST_DIAGNOSTIC_WARNING_PREFIXES for w in item.warnings
        )
        if not (
            item.errors
            or item.status
            in (
                PaperIngestStatus.FAILED,
                PaperIngestStatus.PARSE_INCOMPLETE,
                PaperIngestStatus.TEXT_UNAVAILABLE,
                PaperIngestStatus.DEGRADED,
            )
            or degraded
        ):
            return
        base = self.config.diagnostics_dir or (self.config.output_root / "diagnostics")
        diag_dir = base / "ingest"
        try:
            diag_dir.mkdir(parents=True, exist_ok=True)
            dump_data(item, diag_dir / f"{item.paper_id}.yaml")
        except Exception as exc:  # observability write must not crash a completed ingest
            item.warnings.append(f"ingest_diagnostic_write_failed:{exc}")

    def _ingest_one(self, pdf_path: Path) -> PaperIngestItem:
        paper_id = paper_id_from_filename(pdf_path)
        item = PaperIngestItem(paper_id=paper_id, filename=pdf_path.name)
        parsed_path = self._parsed_dir() / f"{paper_id}.parsed.yaml"
        completeness_path = self._parsed_dir() / f"{paper_id}.completeness.yaml"
        external_path = self._parsed_dir() / f"{paper_id}.external.yaml"
        packet_path = self._parsed_dir() / f"{paper_id}.source_packet.yaml"
        case_path = self._cases_dir() / f"{paper_id}.paper_case.yaml"
        local_literature_path = (
            self._cited_literature_dir() / f"{paper_id}.paper_local_literature.yaml"
        )
        review_path = self._cases_dir() / f"{paper_id}.review.md"
        signature_path = self._cases_dir() / f"{paper_id}.config_signature"

        # F5: the resume-skip reuses an existing per-paper case, but the OLD check keyed on filename
        # alone (case_path.exists()) — a changed paperbank config / parser / provider / model /
        # evidence_mode / prompt_version was silently ignored (a stale case survived a real code change).
        # Skip ONLY when the persisted config signature matches the current one; a changed signature
        # falls through to a full re-extract. (A parser CODE change under the same parser_name is not in
        # the signature — that still needs a wheel rebuild + clearing parsed/, documented in the runbook.)
        if self.config.resume and case_path.exists() and not self.config.parse_only:
            stored_signature = (
                signature_path.read_text(encoding="utf-8").strip()
                if signature_path.exists()
                else ""
            )
            if stored_signature == self._config_signature():
                item.status = PaperIngestStatus.SKIPPED
                item.paper_case_artifact = case_path.as_posix()
                item.review_artifact = review_path.as_posix()
                item.warnings.append("resume_skip_existing_case")
                return item
            item.warnings.append("resume_reingest_config_changed")

        try:
            prompt_version = _prompt_version_for_evidence_mode(self.config.evidence_mode)
            parsed = self.parser.parse(pdf_path, paper_id=paper_id)
            completeness = build_completeness_report(parsed)
            if not build_source_spans(parsed) and self.supplied_text_parser is not None:
                supplied = self.supplied_text_parser.parse(pdf_path, paper_id=paper_id)
                if supplied.source_sha256 != parsed.source_sha256:
                    raise ValueError(
                        "supplied text hook source_sha256 does not match the primary PDF digest"
                    )
                if build_source_spans(supplied):
                    supplied.warnings.extend(parsed.warnings)
                    supplied.warnings.append(
                        f"supplied_text_hook_used:{self.supplied_text_parser.parser_name}"
                    )
                    parsed = supplied
                    completeness = build_completeness_report(parsed)
            external = self._lookup(parsed) if self.config.external_lookup else None
            packet = build_source_packet(
                parsed=parsed,
                completeness=completeness,
                external_record=external,
                prompt_version=prompt_version,
                include_chunks=self.config.evidence_mode != "source_span",
            )
            item.source_sha256 = parsed.source_sha256
            item.cache_key = stable_hash(
                {
                    "source": parsed.source_sha256,
                    "parser": parsed.parser_config_hash,
                    "provider": self.config.provider_name,
                    "model": self.config.model_name,
                    "parse_only": self.config.parse_only,
                    "external": external.response_hashes if external else {},
                    "evidence_mode": self.config.evidence_mode,
                    "prompt_version": prompt_version,
                }
            )
            item.parsed_artifact = dump_data(parsed, parsed_path).as_posix()
            item.completeness_artifact = dump_data(completeness, completeness_path).as_posix()
            if external is not None:
                item.external_artifact = dump_data(external, external_path).as_posix()
            item.source_packet_artifact = dump_data(packet, packet_path).as_posix()
            item.warnings.extend(parsed.warnings)
            item.warnings.extend(completeness.risks)
            item.warnings.extend(completeness.missing_or_weak_sections)
            if external:
                item.warnings.extend(external.warnings)

            item.status = PaperIngestStatus.PARSED
            if self.config.parse_only:
                return item
            if self.model_provider is None:
                item.status = PaperIngestStatus.FAILED
                item.errors.append("model_provider_required_for_extraction")
                return item

            result = PaperCaseExtractionPipeline(
                self.model_provider, evidence_mode=self.config.evidence_mode
            ).extract(
                parsed=parsed,
                completeness=completeness,
                external_record=external,
            )
            item.source_packet_artifact = dump_data(result.source_packet, packet_path).as_posix()
            if result.blocked_reason:
                if result.blocked_reason == "text_unavailable":
                    item.status = PaperIngestStatus.TEXT_UNAVAILABLE
                    item.warnings.append("text_unavailable:no parser-owned citable text")
                else:
                    item.status = PaperIngestStatus.FAILED
                    item.errors.append(result.blocked_reason)
                return item
            if result.paper_case is None:
                item.status = PaperIngestStatus.FAILED
                item.errors.append("model_returned_no_paper_case")
                return item
            paper_case = result.paper_case
            # Y1(a): persist the extracted PaperCase to disk IMMEDIATELY — before the best-effort
            # cited-literature build — so a raise inside that build degrades to a surfaced warning and
            # the good case survives (and a --resume can reuse it) instead of being discarded by the
            # outer catch-all. The literature step is enrichment layered on top of a saved case.
            item.paper_case_artifact = dump_data(result.paper_case, case_path).as_posix()
            if self.config.cited_literature or self.config.select_key_citations:
                try:
                    literature_context = build_paper_local_literature_context(
                        parsed=parsed,
                        paper_case=paper_case,
                        lookup_providers=self.lookup_providers,
                        source_reference_providers=self.source_reference_providers,
                        min_local_reference_count=self.config.min_local_reference_count,
                    )
                    if self.config.select_key_citations and literature_context.cited_works:
                        assert self.model_provider is not None
                        literature_context = select_key_citations_product(
                            self.model_provider,
                            paper_case=paper_case,
                            literature_context=literature_context,
                            max_prompt_chars=self.config.citation_prompt_char_budget,
                        )
                    item.local_literature_artifact = dump_data(
                        literature_context, local_literature_path
                    ).as_posix()
                    key_cited_work_ids = (
                        literature_context.importance_selection.selected_cited_work_ids
                        if literature_context.importance_selection is not None
                        else []
                    )
                    paper_case = paper_case.model_copy(
                        update={
                            "local_literature_context_id": literature_context.context_id,
                            "local_literature_context_digest": literature_context_digest(
                                literature_context
                            ),
                            "key_cited_work_ids": key_cited_work_ids,
                        }
                    )
                    result.paper_case = paper_case
                    # Re-dump the enriched case over the base one written above.
                    item.paper_case_artifact = dump_data(result.paper_case, case_path).as_posix()
                except Exception as exc:
                    # Honest degrade: keep the saved base case, surface the failure, continue.
                    item.warnings.append(f"cited_literature_build_failed:{exc}")
            review_path.write_text(_review_markdown(result), encoding="utf-8")
            item.review_artifact = review_path.as_posix()
            # F5: persist the config signature next to the case so a later resume can detect a config /
            # code change and re-extract instead of silently reusing a stale case.
            signature_path.write_text(self._config_signature(), encoding="utf-8")
            if not completeness.is_complete:
                item.status = PaperIngestStatus.DEGRADED
                item.warnings.append("parse_degraded:source-capable text retained with limitations")
            elif result.paper_case.review.status == PaperCaseReviewStatus.SPAN_VERIFIED:
                item.status = PaperIngestStatus.SPAN_VERIFIED
            elif result.paper_case.evidence_requests:
                item.status = PaperIngestStatus.NEEDS_REVIEW
            else:
                item.status = PaperIngestStatus.EXTRACTED
        except (TypeError, AssertionError):
            raise
        except Exception as exc:
            item.status = PaperIngestStatus.FAILED
            item.errors.append(str(exc))
        return item

    def _lookup(self, parsed) -> ExternalPaperRecord:
        query = PaperIdentityQuery(
            doi=_extract_doi(parsed.full_text),
            title=_extract_title(parsed.full_text),
            source_pdf=parsed.source_pdf,
            source_sha256=parsed.source_sha256,
        )
        records: list[ExternalPaperRecord] = []
        warnings: list[str] = []
        for provider in self.lookup_providers:
            try:
                record = provider.lookup(query)
                records.append(record)
                query = PaperIdentityQuery(
                    doi=query.doi or record.identifiers.doi,
                    pmid=query.pmid or record.identifiers.pmid,
                    pmcid=query.pmcid or record.identifiers.pmcid,
                    arxiv_id=query.arxiv_id or record.identifiers.arxiv_id,
                    title=query.title or record.metadata.title,
                    source_pdf=query.source_pdf,
                    source_sha256=query.source_sha256,
                )
            except Exception as exc:
                warnings.append(f"{provider.provider_name}_lookup_failed: {exc}")
        if not records:
            records = [NullProcessedPaperLookupProvider().lookup(query)]
        merged = merge_external_records(parsed.paper_id, records)
        merged.warnings.extend(warnings)
        return merged

    def _parsed_dir(self) -> Path:
        path = self.config.output_root / "parsed"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _cases_dir(self) -> Path:
        path = self.config.output_root / "cases" / "extracted"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _manifest_dir(self) -> Path:
        path = self.config.output_root / "indexes" / "ingest_runs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _cited_literature_dir(self) -> Path:
        path = self.config.output_root / "cited_literature"
        path.mkdir(parents=True, exist_ok=True)
        return path


def _extract_doi(text: str) -> str:
    match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", text, flags=re.IGNORECASE)
    return match.group(0).rstrip(").,;") if match else ""


def _extract_title(text: str) -> str:
    for line in text.splitlines()[:30]:
        cleaned = " ".join(line.split()).strip()
        if len(cleaned) >= 12 and not cleaned.lower().startswith(("arxiv", "doi", "page ")):
            return cleaned[:300]
    return ""


def _prompt_version_for_evidence_mode(evidence_mode: str) -> str:
    if evidence_mode == "source_span":
        return SOURCE_SPAN_PROMPT_VERSION
    return FREE_QUOTE_PROMPT_VERSION


def _present_only_section(title: str, entries: list[str]) -> list[str]:
    """A review-markdown section rendered ONLY when it has content — no ``[missing]`` noise for
    fields that are legitimately absent (unlike the mandatory Focus Fields above)."""
    present = [entry for entry in entries if entry]
    if not present:
        return []
    return ["", f"## {title}", "", *present]


def _bullets(label: str, items: list[str]) -> str:
    if not items:
        return ""
    lines = "\n".join(f"  - {item}" for item in items)
    return f"- {label}:\n{lines}"


def _review_markdown(result) -> str:
    case = result.paper_case
    if case is None:
        return "# PaperCase Review\n\nNo PaperCase was extracted.\n"
    verifications = "\n".join(
        f"- {item.field} p.{item.page}: {'verified' if item.verified else item.issue_code}"
        for item in result.span_verifications
    )
    missing = "\n".join(f"- {item}" for item in case.evidence_requests) or "- none"
    trace = case.formation_trace
    q = case.scientific_question
    dataset = case.dataset_description
    enriched = [
        *_present_only_section(
            "Background",
            [
                _bullets("Motivating claims", case.knowledge_state.motivating_claims),
                _bullets("Background claims (trace)", trace.background_claims if trace else []),
            ],
        ),
        *_present_only_section(
            "Significance",
            [
                (
                    f"- Scientific significance: {trace.scientific_significance}"
                    if trace and trace.scientific_significance
                    else ""
                ),
                (
                    f"- Why the question was valuable: {case.question_design.why_question_was_valuable}"
                    if case.question_design.why_question_was_valuable
                    else ""
                ),
            ],
        ),
        *_present_only_section(
            "Scientific Question",
            [
                f"- Central contrast: {q.central_contrast}" if q.central_contrast else "",
                _bullets("Competing explanations", q.competing_explanations),
                (
                    f"- Discriminating observation: {q.discriminating_observation}"
                    if q.discriminating_observation
                    else ""
                ),
            ],
        ),
        *_present_only_section(
            "Dataset Description",
            [
                f"- Population: {dataset.population}" if dataset.population else "",
                f"- Task or design: {dataset.task_or_design}" if dataset.task_or_design else "",
                _bullets("Measurements", dataset.measurements),
            ],
        ),
    ]
    enriched_markdown = "\n".join(enriched)
    return f"""# PaperCase Review: {case.paper_case_id}

## Focus Fields

- Motivating tension: {case.knowledge_state.unresolved_tension or "[missing]"}
- Original question: {case.scientific_question.original_question or "[missing]"}
- Epistemic move: {case.question_design.epistemic_move or "[missing]"}
- Why dataset can answer: {case.question_design.why_dataset_can_answer or "[missing]"}
- Novelty delta: {case.question_design.novelty_relative_to_parent_dataset or "[missing]"}
- Non-transferable details: {", ".join(case.question_design.non_transferable_details) or "[missing]"}
{enriched_markdown}

## Evidence Requests

{missing}

## Span Verification

{verifications or "- no evidence spans returned"}
"""
