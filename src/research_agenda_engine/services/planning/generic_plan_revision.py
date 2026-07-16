"""Generic, dataset-agnostic plan-review classification + revision context.

The automated bounded revise-loop reuses the real typed owner + independent plan reviews and, when
they do not both accept, dispatches on a single classification of the two decisions. This module is
the generic version of the earlier single-family ``shared_variability_plan_draft_revision_review``
aggregation (``_aggregate_review_outcome`` / ``_aggregate_required_changes``), with the
material-vs-non-material split the auto-loop needs — but with **no** dataset-specific names, so it
works for any dataset.

Rules (all ``owner`` **OR** ``independent``, matching the single-family revision gate packet):

* ``escalate`` (``human_review``) is a rare last-resort honest terminal;
* a ``reject`` is an honest terminal;
* a ``revise`` whose same-review ``material_revision_detected`` is set is deferred (a material revision needs a
  new question version + renewed literature/novelty recheck, which the front-half literature is not
  yet wired for);
* a plain (non-material) ``revise`` is the loopable case;
* both ``accept`` is the only path to a rendered dossier.

Classification precedence when the two reviewers disagree on kind:
``ESCALATED > REJECTED > MATERIAL_REVISION > NON_MATERIAL_REVISE > ACCEPTED`` (checks ``human_review``
first, then ``reject``, then the material flag on that revise — mirrors the single-family ordering).

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from enum import StrEnum

from ...schemas.planning_dialogue import (
    ClassifiedPlanReviewChange,
    IndependentPlanReviewMessage,
    PlanDraftMessage,
    PlanReviewChangeClass,
    PlanReviewDecisionValue,
    PlanRevisionContext,
    QuestionOwnerPlanReviewMessage,
)


class PlanRevisionClassification(StrEnum):
    """The single dispatched outcome of one owner + independent plan-review round."""

    ACCEPTED = "accepted"
    ACCEPTED_BY_INDEPENDENT_CLOSEOUT = "accepted_by_independent_closeout"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    MATERIAL_REVISION = "material_revision"
    NON_MATERIAL_REVISE = "non_material_revise"
    REVIEW_INCOMPLETE = "review_incomplete"


def material_revision_detected(
    owner_review: QuestionOwnerPlanReviewMessage,
    independent_review: IndependentPlanReviewMessage,
) -> bool:
    """A REVISE decision is material when that same reviewer flags it.

    Models occasionally populate the material flag while accepting. That inconsistent advisory bit
    must not turn another reviewer's ordinary revise into a material-deferred terminal.
    """
    return bool(
        (
            owner_review.decision == PlanReviewDecisionValue.REVISE
            and owner_review.material_revision_detected
        )
        or (
            independent_review.decision == PlanReviewDecisionValue.REVISE
            and independent_review.material_revision_detected
        )
    )


def novelty_recheck_required(
    owner_review: QuestionOwnerPlanReviewMessage,
    independent_review: IndependentPlanReviewMessage,
) -> bool:
    """A novelty recheck is required when a revising reviewer requests it."""
    return bool(
        (
            owner_review.decision == PlanReviewDecisionValue.REVISE
            and owner_review.novelty_recheck_required
        )
        or (
            independent_review.decision == PlanReviewDecisionValue.REVISE
            and independent_review.novelty_recheck_required
        )
    )


def classify_plan_reviews(
    owner_review: QuestionOwnerPlanReviewMessage,
    independent_review: IndependentPlanReviewMessage,
    *,
    allow_independent_closeout: bool = False,
) -> PlanRevisionClassification:
    """Classify one owner + independent plan-review round into a single dispatched outcome."""
    if not owner_review.review_complete or not independent_review.review_complete:
        return PlanRevisionClassification.REVIEW_INCOMPLETE
    decisions = {owner_review.decision, independent_review.decision}
    if PlanReviewDecisionValue.HUMAN_REVIEW in decisions:
        return PlanRevisionClassification.ESCALATED
    if PlanReviewDecisionValue.REJECT in decisions:
        return PlanRevisionClassification.REJECTED
    if PlanReviewDecisionValue.REVISE in decisions:
        if material_revision_detected(owner_review, independent_review):
            return PlanRevisionClassification.MATERIAL_REVISION
        if allow_independent_closeout and independent_closeout_is_safe(
            owner_review, independent_review
        ):
            return PlanRevisionClassification.ACCEPTED_BY_INDEPENDENT_CLOSEOUT
        return PlanRevisionClassification.NON_MATERIAL_REVISE
    if decisions == {PlanReviewDecisionValue.ACCEPT}:
        return PlanRevisionClassification.ACCEPTED
    # Defensive: any non-clean-accept combination loops rather than silently rendering a dossier.
    return PlanRevisionClassification.NON_MATERIAL_REVISE


def independent_closeout_is_safe(
    owner_review: QuestionOwnerPlanReviewMessage,
    independent_review: IndependentPlanReviewMessage,
) -> bool:
    """Whether a final independent reviewer can close an Owner-revise disagreement.

    This is deliberately narrow: the Owner must be the sole revising party; the independent
    reviewer must accept, must assess every Owner change exactly once, and must classify every
    residual item as a pre-execution lock or optional improvement with no hard boundary implicated.
    Unclassified, duplicated, material, provenance, identity, firewall, isolation, or genuine
    scientific blockers therefore remain fail-closed.
    """

    if owner_review.decision != PlanReviewDecisionValue.REVISE:
        return False
    if independent_review.decision != PlanReviewDecisionValue.ACCEPT:
        return False
    if owner_review.material_revision_detected or independent_review.material_revision_detected:
        return False
    if not owner_review.review_complete or not independent_review.review_complete:
        return False
    required_changes = owner_review.required_changes
    owner_issues = owner_review.classified_required_changes
    assessments = independent_review.owner_change_assessments
    if owner_issues and all(item.change_id for item in owner_issues):
        owner_ids = [item.change_id for item in owner_issues]
        assessment_ids = [item.change_id for item in assessments]
        if not owner_ids or len(assessment_ids) != len(owner_ids):
            return False
        if len(set(assessment_ids)) != len(assessment_ids):
            return False
        if set(assessment_ids) != set(owner_ids):
            return False
    elif not required_changes or len(assessments) != len(required_changes):
        return False
    else:
        # Historical v2 provenance had no change IDs. Keep its old text-keyed closeout readable;
        # active v3 reviews take only the ID branch above.
        assessed_changes = [item.change for item in assessments]
        if len(set(assessed_changes)) != len(assessed_changes):
            return False
        if set(assessed_changes) != set(required_changes):
            return False
    return all(
        not item.hard_boundary_implicated
        and item.classification
        in {
            PlanReviewChangeClass.PRE_EXECUTION_LOCK,
            PlanReviewChangeClass.OPTIONAL_IMPROVEMENT,
        }
        for item in assessments
    )


def aggregate_required_changes(
    owner_review: QuestionOwnerPlanReviewMessage,
    independent_review: IndependentPlanReviewMessage,
) -> list[str]:
    """Return planner-facing scientific blockers, with v2 text fallback for provenance."""
    issues = aggregate_blocking_change_issues(owner_review, independent_review)
    has_typed_issues = bool(
        owner_review.classified_required_changes or independent_review.classified_required_changes
    )
    if has_typed_issues:
        return [item.change for item in issues]
    changes: list[str] = []
    for item in [*owner_review.required_changes, *independent_review.required_changes]:
        if item and item not in changes:
            changes.append(item)
    return changes


def aggregate_blocking_change_issues(
    owner_review: QuestionOwnerPlanReviewMessage,
    independent_review: IndependentPlanReviewMessage,
) -> list[ClassifiedPlanReviewChange]:
    """Ordered, ID-deduplicated scientific issues that may consume a planner round."""

    issues: list[ClassifiedPlanReviewChange] = []
    seen: set[str] = set()
    for item in [
        *owner_review.classified_required_changes,
        *independent_review.classified_required_changes,
    ]:
        if item.classification != PlanReviewChangeClass.SCIENTIFIC_BLOCKER:
            continue
        key = item.change_id or f"legacy:{item.change}"
        if key in seen:
            continue
        seen.add(key)
        issues.append(item)
    return issues


def build_plan_revision_context(
    *,
    revision_round: int,
    prior_plan_draft: PlanDraftMessage,
    owner_review: QuestionOwnerPlanReviewMessage,
    independent_review: IndependentPlanReviewMessage,
    prior_evidence_ids: list[str],
) -> PlanRevisionContext:
    """Assemble the generic revision context fed back to the planner for a bounded re-plan.

    Carries the prior plan draft + evidence references and the union of both reviewers'
    ``required_changes`` so the re-spawned planner can produce a revised plan that ADDRESSES them.
    Only used for a NON-material revise (the caller classifies first); ``novelty_recheck_required``
    is threaded through for provenance but a material revision never reaches this builder.
    """
    return PlanRevisionContext(
        revision_round=revision_round,
        prior_plan_draft_message_id=prior_plan_draft.message_id,
        prior_analysis_plan_id=prior_plan_draft.analysis_plan_id,
        owner_plan_review_message_id=owner_review.message_id,
        independent_plan_review_message_id=independent_review.message_id,
        required_changes=aggregate_required_changes(owner_review, independent_review),
        required_change_issues=aggregate_blocking_change_issues(owner_review, independent_review),
        prior_evidence_ids=list(prior_evidence_ids),
        preserves_scientific_intent=owner_review.preserves_scientific_intent,
        novelty_recheck_required=novelty_recheck_required(owner_review, independent_review),
    )
