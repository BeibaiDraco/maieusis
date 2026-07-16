from __future__ import annotations

import re
from difflib import SequenceMatcher

from ...schemas.cited_literature import (
    AbstractRetrievalStatus,
    CitedWorkIdentifiers,
    CitedWorkRef,
    RawReferenceEntry,
    ReferenceResolutionStatus,
)
from ...schemas.paper_ingest import ExternalPaperRecord, LicenseClass, PaperIdentityQuery
from .citation_extraction import build_unresolved_cited_works
from .external_lookup import OpenAlexQuotaExhausted, ProcessedPaperLookupProvider


def resolve_cited_works(
    entries: list[RawReferenceEntry],
    lookup_providers: list[ProcessedPaperLookupProvider],
    *,
    min_title_similarity: float = 0.74,
    diagnostics: list[str] | None = None,
) -> list[CitedWorkRef]:
    unresolved = build_unresolved_cited_works(entries)
    if not lookup_providers:
        return [
            _mark_abstract_unavailable(work, "no_lookup_providers_configured")
            for work in unresolved
        ]

    resolved: list[CitedWorkRef] = []
    quota_disabled_providers: set[str] = set()
    for entry, work in zip(entries, unresolved, strict=True):
        best_record: ExternalPaperRecord | None = None
        best_provider = ""
        best_score = 0.0
        # P3 abstract donor: the FIRST identity-matching record (in provider order) that actually
        # carried a non-empty abstract. A DOI-exact match scores 1.0 for EVERY provider and strict `>`
        # keeps the first, so an abstract-less OpenAlex record could win identity while Crossref/Europe
        # PMC held the abstract (the live 308/308 cause). We adopt the donor's abstract + rights below.
        donor_abstract = ""
        donor_provider = ""
        donor_license = LicenseClass.UNKNOWN
        warnings: list[str] = []
        query = PaperIdentityQuery(
            doi=entry.doi_hint,
            pmid=entry.pmid_hint,
            pmcid=entry.pmcid_hint,
            arxiv_id=entry.arxiv_id_hint,
            title=entry.title_hint,
        )
        for provider in lookup_providers:
            if provider.provider_name in quota_disabled_providers:
                continue
            # Y1(b): the whole per-provider body — lookup AND scoring/donor/query-merge — lives inside
            # the try, so any per-provider error (e.g. a malformed record) degrades to a surfaced
            # warning + continue instead of propagating up to the pipeline's catch-all and discarding
            # the already-extracted PaperCase. Scoring used to sit outside this try.
            try:
                record = provider.lookup(query)
                score = _resolution_score(entry, record)
                if score > best_score:
                    best_record = record
                    best_provider = provider.provider_name
                    best_score = score
                if (
                    not donor_abstract
                    and score >= min_title_similarity
                    and record.metadata.abstract.strip()
                ):
                    donor_abstract = record.metadata.abstract.strip()
                    donor_provider = provider.provider_name
                    donor_license = _record_license_class(record)
                # Chain only identifiers earned by an accepted identity match. A weak title/year
                # candidate is still useful as a scored alternative, but its DOI/PMID must not
                # redirect every later provider to the wrong paper. The source reference hints stay
                # authoritative until a provider clears the same acceptance threshold used below.
                if score >= min_title_similarity:
                    query = PaperIdentityQuery(
                        doi=query.doi or record.identifiers.doi,
                        pmid=query.pmid or record.identifiers.pmid,
                        pmcid=query.pmcid or record.identifiers.pmcid,
                        arxiv_id=query.arxiv_id or record.identifiers.arxiv_id,
                        title=query.title or record.metadata.title,
                    )
            except OpenAlexQuotaExhausted as exc:
                quota_disabled_providers.add(provider.provider_name)
                if (
                    exc.report_diagnostic
                    and diagnostics is not None
                    and OpenAlexQuotaExhausted.diagnostic not in diagnostics
                ):
                    diagnostics.append(OpenAlexQuotaExhausted.diagnostic)
                continue
            except Exception as exc:
                warnings.append(f"{provider.provider_name}_lookup_failed: {exc}")
                continue
        if best_record is None or best_score < min_title_similarity:
            reason = "no_accepted_external_match"
            if quota_disabled_providers:
                reason = f"{reason}; {OpenAlexQuotaExhausted.diagnostic}"
            if warnings:
                reason = f"{reason}; {'; '.join(warnings)}"
            resolved.append(_mark_abstract_unavailable(work, reason))
            continue
        # P3: if the best-identity record has no abstract but a donor did, adopt the donor's abstract +
        # its rights (identity stays from best_record; abstract_source records the donor honestly).
        backfill = (
            (donor_abstract, donor_provider, donor_license)
            if not best_record.metadata.abstract.strip() and donor_abstract
            else None
        )
        resolved.append(
            _work_from_record(
                work, best_record, best_provider, best_score, abstract_backfill=backfill
            )
        )
    return resolved


def _record_license_class(record: ExternalPaperRecord) -> LicenseClass:
    for assertion in record.open_access:
        if assertion.license_class != LicenseClass.UNKNOWN:
            return assertion.license_class
    return LicenseClass.UNKNOWN


def _resolution_score(entry: RawReferenceEntry, record: ExternalPaperRecord) -> float:
    if entry.doi_hint and _norm_doi(entry.doi_hint) == _norm_doi(record.identifiers.doi):
        return 1.0
    if entry.pmid_hint and entry.pmid_hint == record.identifiers.pmid:
        return 0.98
    if entry.pmcid_hint and entry.pmcid_hint.upper() == record.identifiers.pmcid.upper():
        return 0.98
    title = record.metadata.title or ""
    if not entry.title_hint or not title:
        return 0.0
    score = SequenceMatcher(None, _norm_title(entry.title_hint), _norm_title(title)).ratio()
    if entry.year_hint and record.metadata.year and abs(entry.year_hint - record.metadata.year) > 1:
        # Without an exact identifier, a multi-year conflict is an identity contradiction, not a
        # small ranking penalty. A title-only API fallback can echo the query title while attaching
        # an unrelated record's DOI (the Semedo 2014 → 1988 failure); cap it below the acceptance
        # threshold so that identifier cannot poison the remaining provider cascade.
        return 0.0
    if entry.author_hint and record.metadata.authors:
        # Y1(b): authors[0] can be an empty/whitespace string → "".split() == [] → [-1] IndexError
        # (the deterministic trigger that discarded good PaperCases). Guard the empty-parts case.
        parts = record.metadata.authors[0].split()
        first_author = parts[-1].lower() if parts else ""
        if first_author and first_author not in entry.author_hint.lower():
            score -= 0.1
    return max(0.0, min(1.0, score))


def _work_from_record(
    base: CitedWorkRef,
    record: ExternalPaperRecord,
    provider_name: str,
    score: float,
    *,
    abstract_backfill: tuple[str, str, LicenseClass] | None = None,
) -> CitedWorkRef:
    own_abstract = record.metadata.abstract.strip()
    if own_abstract:
        abstract, abstract_source = own_abstract, provider_name
        license_class = _record_license_class(record)
    elif abstract_backfill is not None:
        # P3/P4: the identity record had no abstract; adopt the donor provider's abstract + rights.
        abstract, abstract_source, license_class = abstract_backfill
    else:
        abstract, abstract_source, license_class = "", "", LicenseClass.UNKNOWN
    abstract_status = (
        AbstractRetrievalStatus.RETRIEVED if abstract else AbstractRetrievalStatus.UNAVAILABLE
    )
    provider_record_ids = [
        str(item.get("response_hash") or item.get("endpoint") or provider_name)
        for item in record.provider_records
    ]
    return CitedWorkRef(
        **base.model_dump(
            mode="python",
            exclude={
                "title",
                "authors",
                "year",
                "identifiers",
                "resolution_status",
                "resolution_source",
                "resolution_confidence",
                "abstract",
                "abstract_status",
                "abstract_source",
                "abstract_license_class",
                "retrieval_failure_reason",
                "provider_record_ids",
            },
        ),
        title=record.metadata.title or base.title,
        authors=record.metadata.authors or base.authors,
        year=record.metadata.year or base.year,
        identifiers=CitedWorkIdentifiers(
            doi=record.identifiers.doi or base.identifiers.doi,
            pmid=record.identifiers.pmid or base.identifiers.pmid,
            pmcid=record.identifiers.pmcid or base.identifiers.pmcid,
            openalex_id=record.identifiers.openalex_id or base.identifiers.openalex_id,
            semantic_scholar_id=(
                record.identifiers.semantic_scholar_id or base.identifiers.semantic_scholar_id
            ),
            arxiv_id=record.identifiers.arxiv_id or base.identifiers.arxiv_id,
        ),
        resolution_status=ReferenceResolutionStatus.RESOLVED,
        resolution_source=provider_name,
        resolution_confidence=score,
        abstract=abstract,
        abstract_status=abstract_status,
        abstract_source=abstract_source,
        abstract_license_class=license_class,
        retrieval_failure_reason="" if abstract else "resolved_record_has_no_abstract",
        provider_record_ids=provider_record_ids,
    )


def _mark_abstract_unavailable(work: CitedWorkRef, reason: str) -> CitedWorkRef:
    return CitedWorkRef.model_validate(
        {
            **work.model_dump(mode="python"),
            "abstract_status": AbstractRetrievalStatus.UNAVAILABLE,
            "retrieval_failure_reason": reason,
        }
    )


def _norm_doi(value: str) -> str:
    return value.lower().removeprefix("https://doi.org/").removeprefix("http://doi.org/")


def _norm_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
