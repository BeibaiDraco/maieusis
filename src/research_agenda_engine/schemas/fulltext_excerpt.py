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
from .external_evidence import (
    ExternalEvidenceAttemptStatus,
    ExternalEvidenceFetchAttempt,
    ExternalEvidenceProvider,
    ExternalEvidenceRightsAssertion,
    RetrievalOperation,
    assert_secret_free_persisted_value,
)

# A short, fair-use excerpt — NEVER the full PDF. Bounds the stored/redistributed text.
MAX_FULLTEXT_EXCERPT_CHARS = 1500


class OaRoute(StrEnum):
    """The OPEN-ACCESS route the excerpt was legally obtained through (recorded for the license trail)."""

    OPENALEX_OA_LOCATION = "openalex_oa_location"
    ARXIV = "arxiv"
    UNPAYWALL = "unpaywall"
    PMC_OA = "pmc_oa"


class FulltextExcerpt(BaseModel):
    """A bounded excerpt with retrieval provenance.

    The two optional UPD2 fields deliberately preserve v0.1 readability.  A legacy
    object without them remains valid but ``has_verified_rights`` is false, so it must
    not be treated as authoritative full text by new context/export gates.
    """

    model_config = ConfigDict(extra="forbid")

    excerpt: str
    source_url: str
    oa_route: OaRoute
    license: str = ""
    retrieved_at: datetime
    content_digest: str
    rights_assertion: ExternalEvidenceRightsAssertion | None = None
    retrieval_attempt: ExternalEvidenceFetchAttempt | None = None

    @model_validator(mode="before")
    @classmethod
    def recursively_refuse_secrets(cls, value: object) -> object:
        assert_secret_free_persisted_value(value, path=cls.__name__)
        return value

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
        if (self.rights_assertion is None) != (self.retrieval_attempt is None):
            raise ValueError(
                "verified FulltextExcerpt provenance requires both rights_assertion and "
                "retrieval_attempt; omit both only for a readable legacy record"
            )
        if self.rights_assertion is not None and self.retrieval_attempt is not None:
            assertion = self.rights_assertion
            attempt = self.retrieval_attempt
            if not assertion.authorizes_short_excerpt:
                raise ValueError(
                    "FulltextExcerpt rights assertion does not authorize a short excerpt"
                )
            if attempt.status != ExternalEvidenceAttemptStatus.SUCCEEDED:
                raise ValueError("FulltextExcerpt retrieval_attempt must be successful")
            if attempt.assertion_id != assertion.assertion_id:
                raise ValueError(
                    "FulltextExcerpt retrieval attempt is not bound to its rights assertion"
                )
            if attempt.provider != assertion.provider:
                raise ValueError(
                    "FulltextExcerpt retrieval provider does not match its rights provider"
                )
            if attempt.rights_assertion_digest != stable_hash(assertion.model_dump(mode="json")):
                raise ValueError(
                    "FulltextExcerpt retrieval attempt does not bind the exact rights assertion"
                )
            if attempt.operation not in {
                RetrievalOperation.PAPER_FULLTEXT_EXCERPT,
                RetrievalOperation.TOPIC_FULLTEXT_EXCERPT,
            }:
                raise ValueError("FulltextExcerpt requires a full-text retrieval operation")
            if attempt.requested_url != assertion.asserted_url:
                raise ValueError("FulltextExcerpt source URL is not the asserted OA URL")
            if self.source_url != attempt.final_url:
                raise ValueError("FulltextExcerpt source URL must equal the validated final URL")
            if attempt.excerpt_digest != self.content_digest:
                raise ValueError("FulltextExcerpt retrieval attempt is not bound to its excerpt")
            if self.retrieved_at != attempt.retrieved_at:
                raise ValueError("FulltextExcerpt retrieval time must equal its attempt time")
            if self.license != assertion.license_id:
                raise ValueError("FulltextExcerpt license must equal its rights assertion license")
            expected_route = {
                ExternalEvidenceProvider.OPENALEX: OaRoute.OPENALEX_OA_LOCATION,
                ExternalEvidenceProvider.ARXIV: OaRoute.ARXIV,
                ExternalEvidenceProvider.BIORXIV: OaRoute.ARXIV,
                ExternalEvidenceProvider.MEDRXIV: OaRoute.ARXIV,
                ExternalEvidenceProvider.PMC: OaRoute.PMC_OA,
                ExternalEvidenceProvider.UNPAYWALL: OaRoute.UNPAYWALL,
            }.get(assertion.provider)
            if expected_route is None or self.oa_route != expected_route:
                raise ValueError("FulltextExcerpt OA route does not match its rights provider")
        return self

    @property
    def has_verified_rights(self) -> bool:
        """Whether this excerpt has complete UPD2 rights and response provenance."""

        return self.rights_assertion is not None and self.retrieval_attempt is not None


def build_fulltext_excerpt(
    *,
    excerpt: str,
    source_url: str,
    oa_route: OaRoute,
    retrieved_at: datetime,
    license: str = "",
    rights_assertion: ExternalEvidenceRightsAssertion | None = None,
    retrieval_attempt: ExternalEvidenceFetchAttempt | None = None,
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
        rights_assertion=rights_assertion,
        retrieval_attempt=retrieval_attempt,
    )
