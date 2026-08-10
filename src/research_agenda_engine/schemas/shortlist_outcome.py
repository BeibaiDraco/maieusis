"""Honest automated-shortlist outcome labels — never "approved/serious/novel".

The automated shortlist emits family + per-variant outcomes with honest, NON-approval labels. The
system never certifies a scientific conclusion; ``included_by_automated_review`` means only that the
automated review passed the family (suggested reading), not that it is "approved" or "serious".
Infrastructure failure is ``run_incomplete`` — NEVER a scientific rejection.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from .variant_novelty import VariantNoveltyStatus


class FamilyInclusionLabel(StrEnum):
    INCLUDED_BY_AUTOMATED_REVIEW = "included_by_automated_review"
    REJECTED_SCIENTIFIC = "rejected_scientific"
    # A close prior directly recaps every active variant (a novelty outcome, not a scientific reject).
    DIRECT_RECAP = "direct_recap"
    DEFERRED_INSUFFICIENT_EVIDENCE = "deferred_insufficient_evidence"
    DEFERRED_MATERIAL_REVISION = "deferred_material_revision"
    # The automated bounded revise-loop exhausted its budget (an honest terminal, not a reject).
    REVISION_BUDGET_EXHAUSTED = "revision_budget_exhausted"
    PUBLIC_DOSSIER_REVISION_REQUIRED = "public_dossier_revision_required"
    # The family reached a safe, user-readable terminal, but a provider or shape warning kept it
    # from accepted-plan authority. This does not make the whole run incomplete.
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    # A run/infrastructure failure (API/timeout/validation) — NOT a scientific rejection.
    RUN_INCOMPLETE = "run_incomplete"


class VariantShortlistDisposition(StrEnum):
    ACTIVE = "active"
    # Kept in an included family but honestly flagged/downweighted because a prior directly answers it.
    FLAGGED_DIRECT_RECAP = "flagged_direct_recap"
    DEFERRED_MATERIAL_REVISION = "deferred_material_revision"
    DEFERRED_NOVELTY = "deferred_novelty"
    REJECTED = "rejected"


class VariantShortlistOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    disposition: VariantShortlistDisposition
    novelty_status: VariantNoveltyStatus
    novelty_assessment_id: str = ""
    rationale: str = ""


class FamilyShortlistOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_family_id: str
    label: FamilyInclusionLabel
    gate_decision: str
    variant_outcomes: list[VariantShortlistOutcome] = Field(default_factory=list)
    active_variant_ids: list[str] = Field(default_factory=list)
    novelty_admission_id: str = ""
    rationale: str = ""

    @property
    def is_included(self) -> bool:
        return self.label == FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW
