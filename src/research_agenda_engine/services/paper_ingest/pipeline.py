from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError
from yaml import YAMLError

from ...io import dump_data, load_model
from ...provenance import sha256_file, stable_hash
from ...providers.models.base import (
    StructuredModelFailureKind,
    StructuredModelProvider,
    StructuredModelProviderError,
)
from ...schemas.cited_literature import PaperLocalLiteratureContext, literature_context_digest
from ...schemas.paper_case import PaperCase, PaperCaseReviewStatus
from ...schemas.paper_ingest import (
    ExternalPaperRecord,
    PaperIdentityQuery,
    PaperIngestItem,
    PaperIngestRunManifest,
    PaperIngestStatus,
    ParsedPaper,
    TitleCandidateResult,
    TitleConfidence,
    paper_id_from_filename,
)
from ...schemas.stage_receipt import FailureClass
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
from .source_preparation import (
    apply_source_preparation,
    derived_companion_names,
    resolve_source_preparation,
)


def _agent_citation_context_reader(*, workspace: Path, max_parallel: int):
    """Adapt the batch agent extractor to the pipeline's one-paper-at-a-time shape.

    The pipeline processes papers in a loop, so this hands the extractor a single-paper batch each
    time. `max_parallel` still matters: a paper with many cited works is one session either way,
    and the parameter keeps the batch API honest for a caller that does pass several.

    The body file is written from the parsed blocks rather than re-read from the PDF, so the agent
    sees exactly the text every downstream stage sees -- which after #155 is docling's prose rather
    than poppler's column-interleaved fragments. That is the whole reason this is worth doing: on
    the old text the agent returned fragments like "trate to successively lower altitudes".
    """
    from .citation_context_agent import (
        _body_blocks,
        claude_code_spawn,
        extract_citation_contexts_with_agent,
    )

    spawn = claude_code_spawn()

    def read(parsed, cited_works):
        cell = Path(workspace) / parsed.paper_id
        cell.mkdir(parents=True, exist_ok=True)
        body = cell / f"{parsed.paper_id}.txt"
        body.write_text("\n\n".join(block.text for block in _body_blocks(parsed)), encoding="utf-8")
        contexts, _report = extract_citation_contexts_with_agent(
            workspace=cell,
            spawn=spawn,
            parsed_by_paper={parsed.paper_id: parsed},
            cited_works_by_paper={parsed.paper_id: list(cited_works)},
            body_paths={parsed.paper_id: body},
            max_parallel=max_parallel,
        )
        return contexts.get(parsed.paper_id, [])

    return read


@dataclass
class PaperIngestPipelineConfig:
    #: Read citing sentences with a coding agent rather than the regex extractor. The seam existed
    #: from #156 and NOTHING constructed it, so a run still took the regex fallback -- the "#124
    #: inert" shape, a change that is design-faithful and does nothing.
    citation_contexts_by_agent: bool = False
    citation_context_agent_parallel: int = 4
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
        # Built once, used per paper. `None` means the regex fallback, which the artifact records
        # by name so a low context count is never mistaken for a finding about the paper.
        self.citation_context_reader = (
            _agent_citation_context_reader(
                workspace=self.config.output_root / "citation_context_agent",
                max_parallel=self.config.citation_context_agent_parallel,
            )
            if self.config.citation_contexts_by_agent
            else None
        )
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
            # Receipt-declared derived companions are text carriers for their originals, never
            # standalone papers.
            companions = derived_companion_names(self.config.inbox_dir)
            pdfs = sorted(
                path for path in self.config.inbox_dir.glob("*.pdf") if path.name not in companions
            )
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

    def _resume_reuse_artifacts(
        self,
        *,
        pdf_path: Path,
        parsed_path: Path,
        completeness_path: Path,
        external_path: Path,
        packet_path: Path,
        case_path: Path,
        local_literature_path: Path,
        review_path: Path,
    ) -> tuple[dict[str, str], str]:
        """Return complete reusable artifact paths, or a categorical re-ingest warning.

        The config signature alone cannot bind a case to the current paper bytes or preparation
        sidecars. Verify both identities from persisted typed artifacts before skipping paid work.
        """
        required = {
            "parsed_artifact": parsed_path,
            "completeness_artifact": completeness_path,
            "source_packet_artifact": packet_path,
            "paper_case_artifact": case_path,
            "review_artifact": review_path,
        }
        if self.config.external_lookup:
            required["external_artifact"] = external_path
        if any(not path.is_file() for path in required.values()):
            return {}, "resume_reingest_artifact_missing"

        try:
            preparation = resolve_source_preparation(pdf_path)
            paper_case = load_model(case_path, PaperCase)
            parsed = load_model(parsed_path, ParsedPaper)
            original_sha = sha256_file(pdf_path)
        except (OSError, TypeError, ValueError, YAMLError):
            return {}, "resume_reingest_artifact_invalid"

        if paper_case.source_sha256 != original_sha or parsed.source_sha256 != original_sha:
            return {}, "resume_reingest_source_changed"

        metadata = parsed.metadata
        if preparation.receipt is None:
            if metadata.get("derivative_receipt_digest") or metadata.get("derived_sha256"):
                return {}, "resume_reingest_preparation_changed"
        elif (
            metadata.get("derivative_receipt_digest") != preparation.receipt_digest
            or metadata.get("derived_sha256") != preparation.receipt.derived_sha256
        ):
            return {}, "resume_reingest_preparation_changed"

        if preparation.article_span is None:
            if any(
                metadata.get(field) is not None
                for field in ("article_page_start", "article_page_end", "article_span_reason")
            ):
                return {}, "resume_reingest_preparation_changed"
        elif (
            metadata.get("article_page_start") != preparation.article_span.page_start
            or metadata.get("article_page_end") != preparation.article_span.page_end
            or metadata.get("article_span_reason") != preparation.article_span.reason
        ):
            return {}, "resume_reingest_preparation_changed"

        if paper_case.local_literature_context_id:
            if not local_literature_path.is_file():
                return {}, "resume_reingest_artifact_missing"
            try:
                literature = load_model(local_literature_path, PaperLocalLiteratureContext)
            except (OSError, TypeError, ValueError, YAMLError):
                return {}, "resume_reingest_artifact_invalid"
            if literature_context_digest(literature) != paper_case.local_literature_context_digest:
                return {}, "resume_reingest_artifact_invalid"
            required["local_literature_artifact"] = local_literature_path
        return {field: path.as_posix() for field, path in required.items()}, ""

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
                artifacts, warning = self._resume_reuse_artifacts(
                    pdf_path=pdf_path,
                    parsed_path=parsed_path,
                    completeness_path=completeness_path,
                    external_path=external_path,
                    packet_path=packet_path,
                    case_path=case_path,
                    local_literature_path=local_literature_path,
                    review_path=review_path,
                )
                if not warning:
                    item.status = PaperIngestStatus.SKIPPED
                    for field, path in artifacts.items():
                        setattr(item, field, path)
                    item.source_sha256 = load_model(case_path, PaperCase).source_sha256
                    item.warnings.append("resume_skip_existing_case")
                    return item
                item.warnings.append(warning)
            else:
                item.warnings.append("resume_reingest_config_changed")

        try:
            prompt_version = _prompt_version_for_evidence_mode(self.config.evidence_mode)
            preparation = resolve_source_preparation(pdf_path)
            parsed = self.parser.parse(preparation.parse_path, paper_id=paper_id)
            if not build_source_spans(parsed) and self.supplied_text_parser is not None:
                supplied = self.supplied_text_parser.parse(
                    preparation.parse_path, paper_id=paper_id
                )
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
            parsed = apply_source_preparation(parsed, preparation)
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
                    "source_preparation": preparation.preparation_digest,
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
                item.failure_class = FailureClass.VALIDATION_FAILURE
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
                    item.failure_class = FailureClass.PROMPT_BUDGET
                    item.errors.append(result.blocked_reason)
                return item
            if result.paper_case is None:
                item.status = PaperIngestStatus.FAILED
                item.failure_class = FailureClass.SCHEMA_ERROR
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
                        citation_context_reader=self.citation_context_reader,
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
        except StructuredModelProviderError as exc:
            item.status = PaperIngestStatus.FAILED
            item.failure_class = (
                FailureClass.SCHEMA_ERROR
                if exc.kind
                in {
                    StructuredModelFailureKind.INVALID_RESPONSE,
                    StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID,
                    StructuredModelFailureKind.OUTPUT_TRUNCATED,
                }
                else FailureClass.PROVIDER_FAILURE
            )
            item.errors.append(f"model_provider_{exc.kind.value}")
        except ValidationError as exc:
            item.status = PaperIngestStatus.FAILED
            item.failure_class = FailureClass.SCHEMA_ERROR
            item.errors.append(f"model_output_validation_failed:{exc.error_count()}")
        except Exception as exc:
            item.status = PaperIngestStatus.FAILED
            item.failure_class = FailureClass.VALIDATION_FAILURE
            item.errors.append(f"ingest_boundary_failed:{type(exc).__name__}")
        return item

    def _lookup(self, parsed) -> ExternalPaperRecord:
        title_candidate = extract_title_candidate(parsed)
        query = PaperIdentityQuery(
            doi=_extract_front_matter_doi(parsed),
            title=title_candidate.title,
            source_pdf=parsed.source_pdf,
            source_sha256=parsed.source_sha256,
        )
        # The identity BASIS is what the paper's own bytes supplied, so it must be read before the
        # loop: `query` is rebound each iteration with `doi=query.doi or record.identifiers.doi`, so
        # testing `query.doi` afterwards asks whether any PROVIDER found a DOI, which is a different
        # question and the opposite of the risk. Measured: the label fired on 0 of 71 merged records
        # across four legs while 25 of them entered this loop with no front-matter DOI at all.
        seed_doi = query.doi
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
        if title_candidate.confidence == TitleConfidence.NO_CANDIDATE:
            merged.warnings.extend(
                f"title_candidate_rejected_{reason}" for reason in title_candidate.rejections
            )
        elif not seed_doi:
            # The whole identity rests on a page-1 line, and every provider writes
            # `title=<response> or query.title` while the Null provider stamps the query straight
            # through -- so a wrong line becomes the record's title with nothing marking it. That
            # is how 11-baldwin-dunkerton, a Science paper, became "Handbook on Synchrotron
            # Radiation": the string "10.1016" appears nowhere in its text, so that identity
            # arrived through the title search. 15 of the 2026-08-04 leg's 20 papers take this
            # route. No deterministic check can tell a title of the WRONG article from the right
            # one -- 11's line is a real title, of a news item on the same scanned page -- so this
            # records the basis and leaves the judgement to a reader or a reviewing model.
            merged.warnings.append("identity_basis_title_only")
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


_DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)


def _extract_front_matter_doi(parsed: ParsedPaper) -> str:
    """The DOI the paper prints for ITSELF, from page 1 only -- or nothing.

    Searching the whole document took the first DOI-shaped substring anywhere, which in a paper
    carrying a reference list is a CITED work's identifier. That is not a wrong title; it is a
    wrong PAPER: the record's abstract, authors, venue and year all come from the other work and
    every downstream stage inherits them. Measured over the 2026-08-04 climate corpus, 5 of 20
    papers resolved to another paper's identity -- 18-thackeray to Musselman et al. 2021,
    15-held-soden to "Has the Hadley cell been strengthening in recent decades?",
    17-wills to the CMIP6 overview it cites for methods.

    Page 1 is where a paper states its own identity, and the measurement is unambiguous: every
    correct DOI in that corpus sits on page 1 at 0.1-2.8% of the document, while every wrong one
    sits at 64-92%, on pages 10-20. `extract_title_candidate` already bounds itself the same way.

    Page 1 is not the only place a paper states its own identity. A scanned journal PDF can carry
    the publisher's "cite this article" stamp instead -- 06-hurrell's page 1 OCRs to noise (the
    scan begins mid-way through a DIFFERENT article in the same Science issue, on mouse
    embryogenesis) while its own identity sits at 99.1% of the document:

        Decadal Trends in the North Atlantic Oscillation: Regional Temperatures and Precipitation
        James W. Hurrell
        Science 269 (5224), .  DOI: 10.1126/science.269.5224.676
        View the article online
        https://www.science.org/doi/10.1126/science.269.5224.676

    A stamp like that says the same identifier TWICE, once bare and once as a publisher link to the
    article. A reference entry cites its DOI once.

    The COUNT is what the corpus exercises: 18-thackeray's borrowed identifier also appears inside
    a URL, because the reference line itself reads "https://doi.org/10.1038/s41558-021-01014-9", so
    the link test alone would have kept it. The LINK is not exercised there -- measured, zero DOIs
    in that corpus reach two occurrences without one -- and it defends a different failure: a work
    cited in the text and again in the bibliography reaches two occurrences on its own. Mutation
    testing found the link condition unguarded and it now has a constructed test, because a
    condition no test can kill is decoration, not a guard.

    Recovering the right answer, not merely refusing the wrong one: this returns 18-thackeray's OWN
    DOI, stated twice under "Extended data is available for this paper at", where the whole-text
    search returned the identity of a paper it cites.
    """
    page_one = next((page.text for page in parsed.pages if page.page_number == 1), "")
    front_matter = _DOI_PATTERN.search(page_one)
    if front_matter:
        return front_matter.group(0).rstrip(").,;")

    for match in _DOI_PATTERN.finditer(parsed.full_text):
        doi = match.group(0).rstrip(").,;")
        quoted = re.escape(doi)
        stated_twice = len(re.findall(quoted, parsed.full_text, flags=re.IGNORECASE)) >= 2
        publisher_link = re.search(rf"https?://[^\s]*{quoted}", parsed.full_text, re.IGNORECASE)
        if stated_twice and publisher_link:
            return doi
    return ""


#: A scientific paper title is a phrase, not a token, and not a paragraph. Measured over the
#: 20-paper climate corpus: the correct candidates run 7-16 words. Below them sat four non-titles
#: at 1-2 words ("ARTICLE OPEN", "1234567890():,;", "SYNCHROTRON RADIATION",
#: "Ij./l.bB&i.BPg.i.BIII."); above them sits running body prose, because the scan walks into the
#: page once the junk is skipped -- 06-hurrell's next line is a 37-word sentence about interstellar
#: C3 absorption and the ones after it are 51+. Both gaps are empty (3-6 and 17-36), so the bounds
#: sit clear of every real title on both sides.
#:
#: A floor alone is not a fix: it moved 06 from visible garbage to a fluent 37-word sentence that
#: reads like data, which is worse in an artifact a person skims. The ceiling caps that failure
#: mode; it is honest to say it changes no IDENTITY outcome on this corpus, because 06 resolves
#: through its DOI either way and 11's wrong line is 6 words. It has a constructed test rather than
#: a corpus one for exactly that reason. Deliberately length bounds and never vocabulary ones.
_TITLE_MINIMUM_WORDS = 4
_TITLE_MAXIMUM_WORDS = 30


# Journal banners, imprints, and download stamps that must never become a paper's search
# identity. A miss here degrades to a rejected candidate, never to a crash.
_TITLE_BANNER_PATTERN = re.compile(
    r"(?i)(issn\b|©|\(c\)\s*\d{4}|all rights reserved|downloaded from|www\.|https?://"
    r"|\bvol\.\s*\d|\bvolume\s+\d|\bno\.\s*\d+\s*,|\bissue\s+\d)"
)
_TITLE_PAGE_NUMBER_PATTERN = re.compile(r"(?i)^(page\s+)?[divxlcm\d]{1,7}(\s+of\s+\d+)?$")


def _running_header_lines(parsed: ParsedPaper) -> set[str]:
    """Case-folded lines appearing in the top of MULTIPLE pages — running headers, not titles."""
    counts: dict[str, int] = {}
    for page in parsed.pages:
        top_lines = {
            " ".join(line.split()).strip().casefold()
            for line in page.text.splitlines()[:3]
            if line.strip()
        }
        for line in top_lines:
            counts[line] = counts.get(line, 0) + 1
    return {line for line, count in counts.items() if count >= 2}


def extract_title_candidate(parsed: ParsedPaper) -> TitleCandidateResult:
    """Deterministic scored title-candidate pass (CLIM-01).

    A running header, page number, DOI/arXiv stamp, or journal banner is rejected with a typed
    reason; when nothing survives, the result is an honest ``NO_CANDIDATE`` and external
    identity lookup proceeds without a title instead of searching on noise.
    """

    repeated = _running_header_lines(parsed)
    rejections: list[str] = []

    def _reject(reason: str) -> None:
        if reason not in rejections:
            rejections.append(reason)

    for line in parsed.full_text.splitlines()[:30]:
        cleaned = " ".join(line.split()).strip()
        if not cleaned:
            continue
        if len(cleaned) < 12:
            if _TITLE_PAGE_NUMBER_PATTERN.fullmatch(cleaned):
                _reject("page_number_line")
            else:
                _reject("short_line")
            continue
        if cleaned.lower().startswith(("arxiv", "doi", "page ")):
            _reject("identifier_stamp")
            continue
        if cleaned.casefold() in repeated:
            _reject("running_header")
            continue
        if _TITLE_BANNER_PATTERN.search(cleaned):
            _reject("journal_banner")
            continue
        # Length LAST, so a line with a specific reason keeps it. Placed second, this bound
        # relabelled three genuinely-diagnosed lines on the 2026-08-04 corpus --
        # 16-taszarek's repeated "1234567890():,;" lost `running_header`, and two DOI-URL lines
        # lost `journal_banner` -- and those reasons are persisted as the paper's audit warnings.
        #
        # A character floor of 12 admitted "ARTICLE OPEN" (exactly 12), "1234567890():,;",
        # "SYNCHROTRON RADIATION" and "Ij./l.bB&i.BPg.i.BIII.", all stamped CONFIDENT on that leg,
        # and the title is the ONLY identity handle for the 15 of 20 papers whose front matter
        # prints no DOI -- a noise title still becomes the record's title, because every provider
        # writes `title=<response> or query.title` and the Null provider stamps the query straight
        # through. That is how 11-baldwin, a Science paper, resolved to "Handbook on Synchrotron
        # Radiation": the string "10.1016" appears nowhere in its text, so that identity arrived
        # through the title search.
        #
        # These reject a LINE, not the paper: the scan continues, which is how skipping the junk
        # recovers the real titles of 16-taszarek and 19-rousi one line below. A paper where
        # nothing survives reaches the honest NO_CANDIDATE the enum documents.
        words = len(cleaned.split())
        if words < _TITLE_MINIMUM_WORDS:
            _reject("too_few_words_for_a_title")
            continue
        if words > _TITLE_MAXIMUM_WORDS:
            _reject("too_many_words_for_a_title")
            continue
        return TitleCandidateResult(
            title=cleaned[:300],
            confidence=TitleConfidence.CONFIDENT,
            rejections=rejections,
        )
    return TitleCandidateResult(
        title="",
        confidence=TitleConfidence.NO_CANDIDATE,
        rejections=rejections,
    )


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
