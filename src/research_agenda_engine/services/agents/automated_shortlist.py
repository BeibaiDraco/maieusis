"""Automated shortlist with honest labels + the HUMAN_REVIEWED fix.

Runs the shortlist-worthiness gate per family and derives a family + per-variant outcome with the DEC-1
honest, non-approval labels. Per-variant novelty (DEC-2) feeds the decision: a family is rejected on
novelty grounds ONLY when ALL its active variants are ``direct_recap`` (G-A); when only SOME are, the
family is still included and the direct-recap variants are honestly flagged/downweighted, not dropped.

Included families are stamped ``AI_REVIEWED`` — NEVER ``HUMAN_REVIEWED`` (the automated path can never
masquerade as human; the existing ``import_question_family_reviews`` stays the human override).

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from ...providers.scientific_agents import ScientificAgentSession
from ...schemas.gate_outcome import GateDecision, GateOutcome
from ...schemas.question_family import QuestionFamily, QuestionFamilyGenerationReviewStatus
from ...schemas.shortlist_outcome import (
    FamilyInclusionLabel,
    FamilyShortlistOutcome,
    VariantShortlistDisposition,
    VariantShortlistOutcome,
)
from ...schemas.variant_novelty import VariantNoveltyResult
from .shortlist_reviewer import review_shortlist_worthiness


def _variant_disposition(
    label: FamilyInclusionLabel, novelty: VariantNoveltyResult | None
) -> VariantShortlistDisposition:
    if label == FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW:
        # Included family: flag the direct-recap variants (G-A), keep the others active.
        if novelty is not None and novelty.is_direct_recap:
            return VariantShortlistDisposition.FLAGGED_DIRECT_RECAP
        return VariantShortlistDisposition.ACTIVE
    if label == FamilyInclusionLabel.REJECTED_SCIENTIFIC:
        return VariantShortlistDisposition.REJECTED
    if label == FamilyInclusionLabel.DEFERRED_MATERIAL_REVISION:
        return VariantShortlistDisposition.DEFERRED_MATERIAL_REVISION
    # deferred_insufficient_evidence / run_incomplete: variants remain candidates, pending resolution.
    return VariantShortlistDisposition.ACTIVE


def derive_family_shortlist_outcome(
    family: QuestionFamily,
    *,
    active_variant_ids: Sequence[str],
    novelty_results: Sequence[VariantNoveltyResult],
    gate_outcome: GateOutcome,
) -> FamilyShortlistOutcome:
    """Derive the honest family label + per-variant dispositions from the gate outcome + novelty (G-A)."""
    novelty_by_variant = {result.variant_id: result for result in novelty_results}
    active_novelty = [
        novelty_by_variant[variant_id]
        for variant_id in active_variant_ids
        if variant_id in novelty_by_variant
    ]
    all_direct_recap = bool(active_novelty) and all(n.is_direct_recap for n in active_novelty)

    decision = gate_outcome.decision
    if decision == GateDecision.INFRASTRUCTURE_FAILURE:
        label = FamilyInclusionLabel.RUN_INCOMPLETE  # NEVER a scientific rejection
    elif decision == GateDecision.REJECT:
        label = FamilyInclusionLabel.REJECTED_SCIENTIFIC
    elif decision == GateDecision.INSUFFICIENT_EVIDENCE:
        label = FamilyInclusionLabel.DEFERRED_INSUFFICIENT_EVIDENCE
    elif decision == GateDecision.REVISE:
        label = FamilyInclusionLabel.DEFERRED_MATERIAL_REVISION
    elif decision == GateDecision.ACCEPT:
        # G-A: reject the whole family on novelty grounds ONLY when ALL active variants are direct_recap.
        label = (
            FamilyInclusionLabel.REJECTED_SCIENTIFIC
            if all_direct_recap
            else FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW
        )
    else:
        label = FamilyInclusionLabel.DEFERRED_INSUFFICIENT_EVIDENCE

    variant_outcomes = [
        VariantShortlistOutcome(
            variant_id=variant_id,
            disposition=_variant_disposition(label, novelty_by_variant.get(variant_id)),
            novelty_status=novelty_by_variant[variant_id].status,
            rationale=novelty_by_variant[variant_id].rationale,
        )
        for variant_id in active_variant_ids
        if variant_id in novelty_by_variant
    ]
    rationale = (
        "All active variants are direct recaps of prior work (nothing novel-in-scope to pursue)."
        if (all_direct_recap and label == FamilyInclusionLabel.REJECTED_SCIENTIFIC)
        else gate_outcome.rationale
    )
    return FamilyShortlistOutcome(
        question_family_id=family.question_family_id,
        label=label,
        gate_decision=decision.value,
        variant_outcomes=variant_outcomes,
        active_variant_ids=list(active_variant_ids),
        rationale=rationale,
    )


def promote_family_to_ai_reviewed(
    family: QuestionFamily, outcome: FamilyShortlistOutcome
) -> QuestionFamily:
    """Stamp ``AI_REVIEWED`` on an included family, or raise (fail closed). Never ``HUMAN_REVIEWED``."""
    if outcome.label != FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW:
        raise ValueError(
            f"cannot shortlist QuestionFamily: automated label is {outcome.label.value!r}, "
            "not included_by_automated_review — fail closed"
        )
    return family.model_copy(
        update={"review_status": QuestionFamilyGenerationReviewStatus.AI_REVIEWED}
    )


def run_automated_family_shortlist(
    family: QuestionFamily,
    *,
    session: ScientificAgentSession,
    active_variant_ids: Sequence[str],
    novelty_results: Sequence[VariantNoveltyResult],
    generator_provider_ids: Sequence[str],
    review_guidance: str = "",
    on_gate_outcome: Callable[[GateOutcome], None] | None = None,
) -> tuple[FamilyShortlistOutcome, QuestionFamily | None]:
    """Gate one family for shortlist-worthiness → honest outcome; promote to AI_REVIEWED if included.

    ``on_gate_outcome`` (optional) is invoked with the raw gate outcome so the driver can persist a
    surface-only diagnostic without changing this function's return contract.
    """
    gate_outcome = review_shortlist_worthiness(
        session=session,
        family=family,
        active_variant_ids=active_variant_ids,
        novelty_results=novelty_results,
        generator_provider_ids=generator_provider_ids,
        review_guidance=review_guidance,
    )
    if on_gate_outcome is not None:
        on_gate_outcome(gate_outcome)
    outcome = derive_family_shortlist_outcome(
        family,
        active_variant_ids=active_variant_ids,
        novelty_results=novelty_results,
        gate_outcome=gate_outcome,
    )
    reviewed_family = (
        promote_family_to_ai_reviewed(family, outcome) if outcome.is_included else None
    )
    return outcome, reviewed_family
