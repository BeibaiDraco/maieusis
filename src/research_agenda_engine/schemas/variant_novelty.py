"""Per-variant novelty result — honest labels, NEVER a "novel" claim.

A limited nearest-prior retrieval per active QuestionFamily variant produces one of four HONEST labels,
each describing what was FOUND or NOT-FOUND-IN-THE-SEARCHED-SCOPE — never a positive novelty assertion.
This is a first-class INPUT to the shortlist gate, not a standalone verdict.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class VariantNoveltyStatus(StrEnum):
    # No nearest-prior search was attempted. This is the only honest disabled/unattempted status.
    NOT_ASSESSED = "not_assessed"
    # A prior work in the searched scope directly answers this variant's question.
    DIRECT_RECAP = "direct_recap"
    # A close prior exists in the searched scope (needs attention, not necessarily a recap).
    POSSIBLE_CLOSE_PRIOR = "possible_close_prior"
    # We searched and saw the neighbourhood; nothing close was found IN THE SEARCHED SCOPE.
    # (NOT a novelty claim — only a statement about the limited search.)
    NO_CLOSE_PRIOR_FOUND_IN_SEARCH_SCOPE = "no_close_prior_found_in_search_scope"
    # Retrieval was attempted but too thin/empty/failed to judge — honest, never a reject or claim.
    INSUFFICIENT_RETRIEVAL_EVIDENCE = "insufficient_retrieval_evidence"


class NearestPriorCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    title: str = ""
    similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    url: str = ""
    doi: str = ""


class VariantNoveltyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    status: VariantNoveltyStatus
    query: str = ""
    providers: list[str] = Field(default_factory=list)
    knowledge_cutoff: str = ""
    nearest_source_ids: list[str] = Field(default_factory=list)
    nearest_candidates: list[NearestPriorCandidate] = Field(default_factory=list)
    rationale: str = ""
    retrieval_enabled: bool = True

    @property
    def is_direct_recap(self) -> bool:
        """True when a prior directly answers this variant — a strong signal against shortlisting it."""
        return self.status == VariantNoveltyStatus.DIRECT_RECAP
