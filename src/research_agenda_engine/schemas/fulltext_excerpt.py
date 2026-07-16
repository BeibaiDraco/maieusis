"""Fulltext-excerpt provenance (live-readiness LR-C, DP-6 anti-fabrication).

A fulltext excerpt is a PLUS-ON that strengthens evidence when legally obtainable — never a gate. It is
a SHORT, quote-bounded, fair-use excerpt (never a stored/redistributed full PDF) fetched from an OPEN
ACCESS location, carrying complete provenance so a fabricated "fulltext" can never masquerade as fetched
evidence: the content digest MUST equal ``stable_hash(excerpt)`` (anti-tamper).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ..provenance import stable_hash

# A short, fair-use excerpt — NEVER the full PDF. Bounds the stored/redistributed text.
MAX_FULLTEXT_EXCERPT_CHARS = 1500


class OaRoute(StrEnum):
    """The OPEN-ACCESS route the excerpt was legally obtained through (recorded for the license trail)."""

    OPENALEX_OA_LOCATION = "openalex_oa_location"
    ARXIV = "arxiv"
    UNPAYWALL = "unpaywall"
    PMC_OA = "pmc_oa"


class FulltextExcerpt(BaseModel):
    """A legally-fetched OA excerpt + full provenance. The digest binds the excerpt to its fetch."""

    model_config = ConfigDict(extra="forbid")

    excerpt: str
    source_url: str
    oa_route: OaRoute
    license: str = ""
    retrieved_at: datetime
    content_digest: str

    @field_validator("excerpt", "source_url")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FulltextExcerpt excerpt and source_url must be non-empty")
        return value

    @model_validator(mode="after")
    def enforce_bounds_and_digest(self) -> FulltextExcerpt:
        if len(self.excerpt) > MAX_FULLTEXT_EXCERPT_CHARS:
            raise ValueError(
                f"FulltextExcerpt exceeds the {MAX_FULLTEXT_EXCERPT_CHARS}-char fair-use bound; store a "
                "short excerpt, never a full PDF"
            )
        if self.content_digest != stable_hash(self.excerpt):
            raise ValueError(
                "FulltextExcerpt content_digest does not match the excerpt (tampered / fabricated) — "
                "rejected"
            )
        return self


def build_fulltext_excerpt(
    *,
    excerpt: str,
    source_url: str,
    oa_route: OaRoute,
    retrieved_at: datetime,
    license: str = "",
) -> FulltextExcerpt:
    """Construct a valid excerpt with the digest computed from the (bounded) excerpt text."""
    bounded = excerpt.strip()[:MAX_FULLTEXT_EXCERPT_CHARS]
    return FulltextExcerpt(
        excerpt=bounded,
        source_url=source_url,
        oa_route=oa_route,
        license=license,
        retrieved_at=retrieved_at,
        content_digest=stable_hash(bounded),
    )
