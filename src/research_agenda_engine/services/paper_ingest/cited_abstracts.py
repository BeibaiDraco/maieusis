from __future__ import annotations

import re

from ...provenance import stable_hash
from ...schemas.cited_literature import (
    PaperLocalLiteratureContext,
    PaperLocalLiteratureReviewStatus,
    RawReferenceEntry,
)
from ...schemas.paper_case import PaperCase
from ...schemas.paper_ingest import PaperIdentityQuery, ParsedPaper
from .citation_extraction import extract_citation_contexts, extract_raw_references
from .external_lookup import (
    ProcessedPaperLookupProvider,
    SourceReferenceProvider,
    collect_openalex_diagnostics,
    collect_openalex_request_stats,
)
from .reference_resolution import resolve_cited_works


def build_paper_local_literature_context(
    *,
    parsed: ParsedPaper,
    paper_case: PaperCase,
    lookup_providers: list[ProcessedPaperLookupProvider],
    source_reference_providers: list[SourceReferenceProvider] | None = None,
    min_local_reference_count: int = 10,
) -> PaperLocalLiteratureContext:
    raw_references = extract_raw_references(parsed)
    warnings: list[str] = []
    warnings.append(f"local_reference_count={len(raw_references)}")
    if len(raw_references) < min_local_reference_count and source_reference_providers:
        warnings.append("external_reference_fallback_attempted")
        external_references = _external_reference_entries(
            parsed=parsed,
            paper_case=paper_case,
            source_reference_providers=source_reference_providers,
        )
        merged_references = _merge_reference_entries(raw_references, external_references)
        added = len(merged_references) - len(raw_references)
        warnings.append(f"external_reference_fallback_added={added}")
        raw_references = merged_references
    cited_works = resolve_cited_works(raw_references, lookup_providers, diagnostics=warnings)
    for diagnostic in collect_openalex_diagnostics(
        lookup_providers, source_reference_providers or []
    ):
        if diagnostic not in warnings:
            warnings.append(diagnostic)
    openalex_stats = collect_openalex_request_stats(
        lookup_providers, source_reference_providers or []
    )
    if openalex_stats is not None:
        warnings.append(
            "openalex_request_stats="
            f"network:{openalex_stats.network_requests},"
            f"cache_hits:{openalex_stats.cache_hits},"
            f"negative_cache_hits:{openalex_stats.negative_cache_hits},"
            f"quota_429s:{openalex_stats.quota_429s},"
            f"breaker_open:{str(openalex_stats.breaker_open).lower()}"
        )
    citation_contexts = extract_citation_contexts(parsed, cited_works)
    context_id = (
        f"pll-{paper_case.paper_case_id}-{stable_hash([w.cited_work_id for w in cited_works])[:12]}"
    )
    warnings.append(f"reference_count={len(raw_references)}")
    warnings.append(f"citation_context_count={len(citation_contexts)}")
    if not raw_references:
        warnings.append("no_references_extracted")
    if not citation_contexts and cited_works:
        warnings.append("no_inline_citation_contexts_extracted")
    status = (
        PaperLocalLiteratureReviewStatus.ABSTRACTS_ATTEMPTED
        if cited_works
        else PaperLocalLiteratureReviewStatus.LOCAL_REFERENCE_EXTRACTED
    )
    return PaperLocalLiteratureContext(
        context_id=context_id,
        paper_case_id=paper_case.paper_case_id,
        source_paper_id=parsed.paper_id,
        source_sha256=parsed.source_sha256,
        raw_references=raw_references,
        cited_works=cited_works,
        citation_contexts=citation_contexts,
        review_status=status,
        warnings=warnings,
    )


def _external_reference_entries(
    *,
    parsed: ParsedPaper,
    paper_case: PaperCase,
    source_reference_providers: list[SourceReferenceProvider],
) -> list[RawReferenceEntry]:
    query = _source_identity_query(parsed=parsed, paper_case=paper_case)
    entries: list[RawReferenceEntry] = []
    for provider in source_reference_providers:
        try:
            entries.extend(provider.references_for_source(query, source_paper_id=parsed.paper_id))
        except Exception:
            continue
    return entries


def _source_identity_query(*, parsed: ParsedPaper, paper_case: PaperCase) -> PaperIdentityQuery:
    doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", parsed.full_text, re.IGNORECASE)
    return PaperIdentityQuery(
        doi=doi_match.group(0).rstrip(").,;") if doi_match else "",
        title=paper_case.citation,
        source_pdf=parsed.source_pdf,
    )


def _merge_reference_entries(
    local_entries: list[RawReferenceEntry],
    external_entries: list[RawReferenceEntry],
) -> list[RawReferenceEntry]:
    merged = list(local_entries)
    seen = {_entry_identity(entry) for entry in local_entries}
    for entry in external_entries:
        identity = _entry_identity(entry)
        if identity in seen:
            continue
        seen.add(identity)
        merged.append(entry)
    return merged


def _entry_identity(entry: RawReferenceEntry) -> str:
    if entry.doi_hint:
        return f"doi:{_normalize(entry.doi_hint)}"
    if entry.pmid_hint:
        return f"pmid:{entry.pmid_hint}"
    if entry.pmcid_hint:
        return f"pmcid:{entry.pmcid_hint.upper()}"
    if entry.arxiv_id_hint:
        return f"arxiv:{entry.arxiv_id_hint.lower()}"
    title = _normalize(entry.title_hint)
    author = _normalize(entry.author_hint.split(",", 1)[0])
    if title and entry.year_hint:
        return f"title-year-author:{title}:{entry.year_hint}:{author}"
    return f"raw:{stable_hash(entry.raw_text)}"


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
