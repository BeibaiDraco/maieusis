"""Targeted OA fulltext-excerpt plus-on (live-readiness LR-C).

Fulltext is a PLUS-ON that strengthens evidence when legally obtainable — never a gate. For the sources
supporting open gaps / strong claims, attempt to fetch a SHORT excerpt from an OPEN-ACCESS location; on
success upgrade the record to ``FULLTEXT_EXCERPT`` (its ``evidence_basis`` then reads ``fulltext_backed``),
on failure keep it abstract-only and record the attempt honestly — a fetch failure is NEVER a run failure.

Copyright red lines (enforced by construction): OA sources only; SHORT quote-bounded excerpts only (the
``FulltextExcerpt`` schema caps length); never store or redistribute a paywalled full PDF; never bypass a
paywall; the fetch records the OA route it used.

The fetcher is INJECTABLE so unit tests stay zero-network / zero-paid (a fake fetcher); the real HTTP OA
routes run only in the operator's gated live smoke (NOT in ``make check``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from ...schemas.fulltext_excerpt import FulltextExcerpt, OaRoute, build_fulltext_excerpt
from ..context.topic_evidence import (
    R5TopicSourceRecordEvidence,
    TopicSourceAbstractStatus,
    TopicSourceSnippetKind,
)


class FulltextFetcher(Protocol):
    """Fetch a short OA excerpt for a record, or ``None`` when no legal OA fulltext is obtainable."""

    def fetch(self, record: R5TopicSourceRecordEvidence) -> FulltextExcerpt | None: ...


class NullFulltextFetcher:
    """The plus-on is OFF: never fetches, so every record stays abstract-only (the honest default)."""

    def fetch(self, record: R5TopicSourceRecordEvidence) -> FulltextExcerpt | None:
        return None


@dataclass
class FulltextEnrichmentCounts:
    """Honest per-run tally for the enrichment StageReceipt."""

    attempted: int = 0
    succeeded: int = 0
    failed_no_oa: int = 0  # the fetcher returned None (no OA location / not found / paywalled)
    failed_error: int = 0  # the fetcher raised — recorded, never fatal

    def as_dict(self) -> dict[str, int]:
        return {
            "attempted": self.attempted,
            "succeeded": self.succeeded,
            "failed_no_oa": self.failed_no_oa,
            "failed_error": self.failed_error,
        }


def enrich_records_with_fulltext(
    records: Sequence[R5TopicSourceRecordEvidence],
    *,
    fetcher: FulltextFetcher,
    target_source_ids: Iterable[str],
) -> tuple[list[R5TopicSourceRecordEvidence], FulltextEnrichmentCounts]:
    """Attempt OA fulltext for the TARGET sources; upgrade on success, keep abstract on failure.

    Only records that (a) are a target, (b) are not already fulltext, and (c) currently support claims
    (abstract-level, not title/metadata-only) are attempted — the plus-on strengthens, it never promotes
    a title-only record. Every upgraded record is re-validated, so the DP-6 anti-fabrication invariant
    fires here too (a fetcher whose excerpt does not match the stored text is rejected).
    """
    targets = set(target_source_ids)
    counts = FulltextEnrichmentCounts()
    enriched: list[R5TopicSourceRecordEvidence] = []
    for record in records:
        if (
            record.source_record_id not in targets
            or record.snippet_kind == TopicSourceSnippetKind.FULLTEXT_EXCERPT
            or not record.can_support_claims
        ):
            enriched.append(record)
            continue
        counts.attempted += 1
        try:
            excerpt = fetcher.fetch(record)
        except Exception:  # a fetch error is recorded honestly, never fatal
            counts.failed_error += 1
            enriched.append(record)
            continue
        if excerpt is None:
            counts.failed_no_oa += 1
            enriched.append(record)
            continue
        counts.succeeded += 1
        enriched.append(
            R5TopicSourceRecordEvidence.model_validate(
                {
                    **record.model_dump(mode="python"),
                    "snippet_kind": TopicSourceSnippetKind.FULLTEXT_EXCERPT.value,
                    "abstract_or_snippet": excerpt.excerpt,
                    "abstract_status": TopicSourceAbstractStatus.AVAILABLE.value,
                    "fulltext_provenance": excerpt.model_dump(mode="python"),
                }
            )
        )
    return enriched, counts


# --- real OA routes (live-only; injectable http so structure is testable without network) --------
def _oa_target(record: R5TopicSourceRecordEvidence) -> tuple[str, OaRoute] | None:
    """The legal OA (url, route) for a record, or None. arXiv/bioRxiv first, then a stored OA url."""
    doi = record.doi.lower()
    url = record.url
    if "arxiv" in doi or "arxiv.org" in url.lower():
        return (url or f"https://arxiv.org/abs/{doi}", OaRoute.ARXIV)
    if "10.1101" in doi:  # bioRxiv/medRxiv preprint DOIs are OA
        return (url or f"https://doi.org/{record.doi}", OaRoute.ARXIV)
    if url and "openalex" not in url.lower():
        # An OA location URL carried on the record (OpenAlex best_oa_location.oa_url populates this).
        return (url, OaRoute.OPENALEX_OA_LOCATION)
    return None


class OpenAccessFulltextFetcher:
    """v1 OA fetcher (OpenAlex OA location + arXiv). LIVE-ONLY; CI injects a fake ``http_get_text``."""

    def __init__(
        self,
        *,
        http_get_text: Callable[[str], str | None] | None = None,
        license_label: str = "open_access",
    ) -> None:
        self._http_get_text = http_get_text or _default_http_get_text
        self._license_label = license_label

    def fetch(self, record: R5TopicSourceRecordEvidence) -> FulltextExcerpt | None:
        target = _oa_target(record)
        if target is None:
            return None
        url, route = target
        text = self._http_get_text(url)
        if not text or not text.strip():
            return None
        return build_fulltext_excerpt(
            excerpt=text,
            source_url=url,
            oa_route=route,
            license=self._license_label,
            retrieved_at=datetime.now(UTC),
        )


def _default_http_get_text(url: str) -> str | None:  # pragma: no cover - live-only network path
    """Real OA GET → a bounded text excerpt. Exercised only in the operator's gated live smoke."""
    import urllib.request

    request = urllib.request.Request(url, headers={"User-Agent": "maieusis-oa-fulltext/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw: bytes = response.read(4000)
    text: str = raw.decode("utf-8", errors="replace")
    return text
