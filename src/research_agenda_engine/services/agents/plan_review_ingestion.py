"""Generation-boundary mirrors and conservative reconciliation for plan-review content.

The provider parses externally-authored owner/reviewer content into these deliberately lenient
mirrors.  Reconciliation then produces content that the unchanged strict PlanningMessage schemas
can construct.  Every repair/degrade is explicit and persisted as a typed diagnostic by the caller;
the raw model shape remains in the scientific-agent transcript.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...io import dump_data
from ...provenance import stable_hash
from ...schemas.planning_dialogue import (
    BranchDecisionKind,
    ClassifiedPlanReviewChange,
    PlanReviewChangeClass,
    PlanReviewCriterionStatus,
    PlanReviewDecisionValue,
    PlanReviewIssueLedgerEntry,
    PlanReviewIssueStatus,
    PlanReviewLateBlockerBasis,
)

MISSING_CRITERION_RATIONALE = (
    "[missing-review-detail] The reviewer supplied no rationale for this criterion."
)
MISSING_REVIEW_RATIONALE = (
    "[missing-review-detail] The reviewer supplied no overall review rationale."
)

OWNER_SEAM_ID = "services.agents.question_owner::review_plan_draft::kwargs_splat#1"
REVIEWER_SEAM_ID = "services.agents.plan_reviewer::review_plan_draft_independently::kwargs_splat#1"
CRITERION_SEAM_ID = "schemas.planning_dialogue::PlanReviewCriterionAssessment::manual#1"


class ClassifiedPlanReviewChangeMirror(BaseModel):
    """Generation-only review-change shape; scientific authority is reconciled in-repo.

    Classification and rationale are deliberately plain/optional at the provider boundary so an
    unknown label or omitted explanation can be retained and degraded instead of crashing inside
    ``generate_structured``. Only exact, fully explained values are rebuilt as the strict schema.
    """

    model_config = ConfigDict(extra="forbid")

    change_id: str = ""
    change: str = ""
    classification: str = ""
    rationale: str = ""
    hard_boundary_implicated: bool = False
    late_blocker_basis: PlanReviewLateBlockerBasis | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class OwnerPlanReviewContent(BaseModel):
    """Model-facing owner verdict mirror: shape-valid, not authority-valid."""

    model_config = ConfigDict(extra="forbid")

    decision: PlanReviewDecisionValue
    rationale: str = ""
    required_changes: list[str] = Field(default_factory=list)
    classified_required_changes: list[ClassifiedPlanReviewChangeMirror] = Field(
        default_factory=list
    )
    preserves_scientific_intent: bool
    material_revision_detected: bool = False
    novelty_recheck_required: bool = False
    # Host-owned reconciliation state. Optional in the generation schema; model values are ignored.
    review_complete: bool = True
    review_artifact_issues: list[str] = Field(default_factory=list)


def _normalized_criterion_status(value: str) -> PlanReviewCriterionStatus | None:
    """Resolve a reviewer's status label mechanically, or return None to degrade honestly.

    Mechanical ONLY -- case, surrounding whitespace, and hyphen/space against the enum's
    underscores. There is deliberately no synonym table: mapping ``needs_changes`` onto ``concern``
    or ``fail`` would be guessing at a scientific judgement the reviewer did not make, and a
    growing thesaurus is exactly the deterministic word-game this project does not want. The
    reviewer prompt states the four values; anything that still does not resolve degrades to a
    non-authoritative concern that keeps the reviewer's own prose intact.
    """

    cleaned = value.strip().lower().replace("-", "_").replace(" ", "_")
    if not cleaned:
        return None
    try:
        return PlanReviewCriterionStatus(cleaned)
    except ValueError:
        return None


class PlanReviewCriterionAssessmentMirror(BaseModel):
    """Model-facing criterion mirror; blank/missing rationale is reconciled after provider parse."""

    model_config = ConfigDict(extra="forbid")

    criterion: str
    # Deliberately `str`, not the enum. The vocabulary is stated in the reviewer prompt -- telling
    # the agent is the fix -- while this field stays tolerant so a non-conforming reply still
    # ARRIVES and can be repaired before strict construction (AGENTS.md rule 11: truth boundaries
    # hard, wording heuristics soft; repair or degrade honestly BEFORE strict construction).
    # Refusing it at the provider boundary would make a single word cost a paid reattempt, which
    # is the same over-correction rule 11 exists to prevent.
    status: str = ""
    rationale: str = ""
    evidence_ids: list[str] = Field(default_factory=list)


class IndependentPlanReviewContent(BaseModel):
    """Model-facing independent verdict mirror: cross-field trust is reconciled in-repo."""

    model_config = ConfigDict(extra="forbid")

    decision: PlanReviewDecisionValue
    rationale: str = ""
    required_changes: list[str] = Field(default_factory=list)
    classified_required_changes: list[ClassifiedPlanReviewChangeMirror] = Field(
        default_factory=list
    )
    rejection_reason: BranchDecisionKind | None = None
    criterion_assessments: list[PlanReviewCriterionAssessmentMirror] = Field(default_factory=list)
    owner_change_assessments: list[ClassifiedPlanReviewChangeMirror] = Field(default_factory=list)
    material_revision_detected: bool = False
    novelty_recheck_required: bool = False
    # Host-owned reconciliation state. Optional in the generation schema; model values are ignored.
    review_complete: bool = True
    review_artifact_issues: list[str] = Field(default_factory=list)


class IndependentNewIssueModelOutput(BaseModel):
    # Minimal model-facing shape for an issue first raised by the independent reviewer.
    model_config = ConfigDict(extra="forbid")

    change: str = ""
    classification: str = ""
    rationale: str = ""
    hard_boundary_implicated: bool = False
    late_blocker_basis: str = ""
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def discard_legacy_host_issue_id(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        cleaned = dict(value)
        cleaned.pop("change_id", None)
        return cleaned


class IndependentOwnerIssueAssessmentModelOutput(BaseModel):
    # Minimal model-facing assessment keyed to one host-owned Owner issue ID.
    model_config = ConfigDict(extra="forbid")

    change_id: str = ""
    classification: str = ""
    rationale: str = ""
    hard_boundary_implicated: bool = False
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def discard_legacy_host_restored_fields(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        cleaned = dict(value)
        cleaned.pop("change", None)
        cleaned.pop("late_blocker_basis", None)
        return cleaned


class IndependentPlanReviewModelOutput(BaseModel):
    # Provider DTO without duplicated or host-owned persisted-review fields. The host expands it
    # into the unchanged reconciliation input and strict persisted review message.
    model_config = ConfigDict(extra="forbid")

    decision: Literal["accept", "revise", "reject", "human_review"]
    rationale: str = ""
    classified_required_changes: list[IndependentNewIssueModelOutput] = Field(default_factory=list)
    # Same shape as `criterion_assessments[].status` above, latent rather than firing only because
    # no reviewer in the live corpus has yet rejected a plan (0 of 167). Its six legal values are
    # non-obvious snake_case compounds that appeared in no reviewer prompt, so the first genuine
    # rejection would have been reconciled to "no typed basis" and converted into an
    # infrastructure terminal instead of the scientific rejection it was.
    rejection_reason: BranchDecisionKind | None = None
    criterion_assessments: list[PlanReviewCriterionAssessmentMirror] = Field(default_factory=list)
    owner_change_assessments: list[IndependentOwnerIssueAssessmentModelOutput] = Field(
        default_factory=list
    )
    material_revision_detected: bool = False
    novelty_recheck_required: bool = False

    @model_validator(mode="before")
    @classmethod
    def discard_legacy_host_owned_fields(cls, value: object) -> object:
        """Keep historical replay payloads readable without adding fields to the live schema."""
        if not isinstance(value, dict):
            return value
        cleaned = dict(value)
        cleaned.pop("required_changes", None)
        cleaned.pop("review_complete", None)
        cleaned.pop("review_artifact_issues", None)
        # Historical replay payloads wrote "" for "no rejection basis"; the field is now typed, so
        # normalize the empty string back to None rather than failing an old artifact. Anything
        # else that was persisted stays as-is and is validated against the enum, which is the
        # point of the change.
        if cleaned.get("rejection_reason") == "":
            cleaned["rejection_reason"] = None
        return cleaned


def expand_independent_plan_review_model_output(
    output: IndependentPlanReviewModelOutput,
    *,
    owner_change_issues: Sequence[ClassifiedPlanReviewChange] = (),
) -> IndependentPlanReviewContent:
    """Expand the minimal DTO into the existing reconciliation input without adding authority."""

    classified_changes = [
        ClassifiedPlanReviewChangeMirror(
            change=item.change,
            classification=item.classification,
            rationale=item.rationale,
            hard_boundary_implicated=item.hard_boundary_implicated,
            late_blocker_basis=_exact_late_blocker_basis(item.late_blocker_basis),
            evidence_ids=item.evidence_ids,
        )
        for item in output.classified_required_changes
    ]
    owner_by_id = {item.change_id: item for item in owner_change_issues if item.change_id}
    unique_unkeyed_id = (
        next(iter(owner_by_id))
        if len(owner_by_id) == 1
        and len(output.owner_change_assessments) == 1
        and not output.owner_change_assessments[0].change_id.strip()
        else ""
    )
    owner_assessments: list[ClassifiedPlanReviewChangeMirror] = []
    for item in output.owner_change_assessments if owner_by_id else []:
        change_id = item.change_id.strip() or unique_unkeyed_id
        canonical = owner_by_id.get(change_id)
        owner_assessments.append(
            ClassifiedPlanReviewChangeMirror(
                change_id=change_id,
                change=canonical.change if canonical is not None else "",
                classification=item.classification,
                rationale=item.rationale,
                hard_boundary_implicated=item.hard_boundary_implicated,
                evidence_ids=item.evidence_ids,
            )
        )
    # Already typed at the provider boundary; the previous free-text parse-and-discard is gone.
    rejection_reason: BranchDecisionKind | None = output.rejection_reason
    return IndependentPlanReviewContent(
        decision=PlanReviewDecisionValue(output.decision),
        rationale=output.rationale,
        required_changes=[
            item.change for item in output.classified_required_changes if item.change.strip()
        ],
        classified_required_changes=classified_changes,
        rejection_reason=rejection_reason,
        criterion_assessments=output.criterion_assessments,
        owner_change_assessments=owner_assessments,
        material_revision_detected=output.material_revision_detected,
        novelty_recheck_required=output.novelty_recheck_required,
    )


def _exact_late_blocker_basis(value: str) -> PlanReviewLateBlockerBasis | None:
    if not value.strip():
        return None
    try:
        return PlanReviewLateBlockerBasis(value.strip())
    except ValueError:
        return None


class PlanReviewIngestionDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnostic_id: str
    code: str
    seam_id: str
    branch_id: str
    source_message_id: str
    reviewer_role: Literal["question_owner", "independent_reviewer"]
    field: str
    original_decision: PlanReviewDecisionValue
    final_decision: PlanReviewDecisionValue
    detail: str


def reconcile_owner_plan_review(
    content: OwnerPlanReviewContent,
    *,
    branch_id: str,
    source_message_id: str,
    review_round: int = 0,
    plan_digest: str = "",
    known_issues: Sequence[PlanReviewIssueLedgerEntry] = (),
) -> tuple[OwnerPlanReviewContent, list[PlanReviewIngestionDiagnostic]]:
    original = content.decision
    decision = original
    overall_rationale, rationale_pending, rationale_issues = _reconcile_overall_rationale(
        content.rationale,
        seam_id=OWNER_SEAM_ID,
    )
    required_changes = _clean_text_list(content.required_changes)
    novelty_recheck_required = content.novelty_recheck_required
    pending: list[tuple[str, str, str, str]] = list(rationale_pending)
    artifact_issues: list[str] = list(rationale_issues)

    (
        supplied_changes,
        retained_change_text,
        mirror_diagnostics,
        mirror_issues,
    ) = _strict_classified_change_mirrors(
        content.classified_required_changes,
        seam_id=OWNER_SEAM_ID,
        field="classified_required_changes",
    )
    required_changes = list(dict.fromkeys([*required_changes, *retained_change_text]))
    pending.extend(mirror_diagnostics)
    artifact_issues.extend(mirror_issues)

    if decision == PlanReviewDecisionValue.ACCEPT and not content.preserves_scientific_intent:
        artifact_issues.append("contradictory_verdict")
        pending.append(
            (
                "contradictory_verdict",
                OWNER_SEAM_ID,
                "decision,preserves_scientific_intent",
                "accept contradicted preserves_scientific_intent=false; marked review-incomplete "
                "instead of inventing a planner revision",
            )
        )

    if decision == PlanReviewDecisionValue.REVISE and not required_changes and not supplied_changes:
        artifact_issues.append("missing_required_changes")
        pending.append(
            (
                "missing_required_changes",
                OWNER_SEAM_ID,
                "required_changes",
                "revise supplied no actionable issue; marked review-incomplete without creating "
                "scientific work for the planner",
            )
        )

    if decision == PlanReviewDecisionValue.REJECT and content.preserves_scientific_intent:
        artifact_issues.append("missing_rejection_reason")
        pending.append(
            (
                "missing_rejection_reason",
                OWNER_SEAM_ID,
                "decision,preserves_scientific_intent",
                "owner reject preserved intent but supplied no typed terminal basis; marked "
                "review-incomplete rather than creating a scientific rejection or revision",
            )
        )

    (
        classified_required_changes,
        canonical_changes,
        classification_diagnostics,
        classification_issues,
    ) = _reconcile_classified_changes(
        (
            required_changes
            if decision in {PlanReviewDecisionValue.ACCEPT, PlanReviewDecisionValue.REVISE}
            or supplied_changes
            else []
        ),
        supplied_changes,
        known_issues=known_issues,
        branch_id=branch_id,
        source_message_id=source_message_id,
        reviewer_role="question_owner",
        review_round=review_round,
        plan_digest=plan_digest,
        seam_id=OWNER_SEAM_ID,
        field="classified_required_changes",
    )
    pending.extend(classification_diagnostics)
    artifact_issues.extend(classification_issues)
    if classified_required_changes:
        required_changes = list(dict.fromkeys([*canonical_changes, *retained_change_text]))

    # The count mismatch no longer withholds review authority, but it still closes this upgrade:
    # unmatched display prose may be a blocker the model never classified, and normalizing revise
    # to accept on that input is the one direction that must stay conservative.
    display_count_mismatched = any(
        code == "change_classification_count_mismatch" for code, *_ in pending
    )
    if (
        decision == PlanReviewDecisionValue.REVISE
        and not artifact_issues
        and not display_count_mismatched
    ):
        blockers = [
            item
            for item in classified_required_changes
            if item.classification == PlanReviewChangeClass.SCIENTIFIC_BLOCKER
        ]
        if not blockers:
            decision = PlanReviewDecisionValue.ACCEPT
            pending.append(
                (
                    "nonblocking_changes_cannot_force_revision",
                    OWNER_SEAM_ID,
                    "decision,classified_required_changes",
                    "owner classified every requested change as pre-execution or optional; "
                    "normalized revise to accept while retaining all change text",
                )
            )

    if content.material_revision_detected and not novelty_recheck_required:
        novelty_recheck_required = True
        pending.append(
            (
                "material_revision_requires_novelty_recheck",
                OWNER_SEAM_ID,
                "novelty_recheck_required",
                "forced true because every material scientific revision requires renewed novelty review",
            )
        )

    reconciled = content.model_copy(
        update={
            "decision": decision,
            "rationale": overall_rationale,
            "required_changes": required_changes,
            "classified_required_changes": classified_required_changes,
            "novelty_recheck_required": novelty_recheck_required,
            "review_complete": not artifact_issues,
            "review_artifact_issues": list(dict.fromkeys(artifact_issues)),
        }
    )
    return reconciled, _diagnostics(
        pending,
        branch_id=branch_id,
        source_message_id=source_message_id,
        reviewer_role="question_owner",
        original_decision=original,
        final_decision=decision,
    )


def reconcile_independent_plan_review(
    content: IndependentPlanReviewContent,
    *,
    branch_id: str,
    source_message_id: str,
    owner_required_changes: list[str] | None = None,
    owner_change_issues: Sequence[ClassifiedPlanReviewChange] = (),
    review_round: int = 0,
    plan_digest: str = "",
    known_issues: Sequence[PlanReviewIssueLedgerEntry] = (),
) -> tuple[IndependentPlanReviewContent, list[PlanReviewIngestionDiagnostic]]:
    original = content.decision
    decision = original
    overall_rationale, rationale_pending, rationale_issues = _reconcile_overall_rationale(
        content.rationale,
        seam_id=REVIEWER_SEAM_ID,
    )
    required_changes = _clean_text_list(content.required_changes)
    rejection_reason = content.rejection_reason
    novelty_recheck_required = content.novelty_recheck_required
    pending: list[tuple[str, str, str, str]] = list(rationale_pending)
    artifact_issues: list[str] = list(rationale_issues)

    (
        supplied_changes,
        retained_change_text,
        mirror_diagnostics,
        mirror_issues,
    ) = _strict_classified_change_mirrors(
        content.classified_required_changes,
        seam_id=REVIEWER_SEAM_ID,
        field="classified_required_changes",
    )
    required_changes = list(dict.fromkeys([*required_changes, *retained_change_text]))
    pending.extend(mirror_diagnostics)
    artifact_issues.extend(mirror_issues)

    (
        supplied_owner_assessments,
        _,
        owner_mirror_diagnostics,
        owner_mirror_issues,
    ) = _strict_classified_change_mirrors(
        content.owner_change_assessments,
        seam_id=REVIEWER_SEAM_ID,
        field="owner_change_assessments",
    )
    pending.extend(owner_mirror_diagnostics)
    artifact_issues.extend(owner_mirror_issues)

    canonical_owner_issues = list(owner_change_issues)
    if not canonical_owner_issues and owner_required_changes:
        # Compatibility input for callers still carrying a v2 Owner message.  It is display-only:
        # without host IDs no independent assessment can gain closeout authority.
        artifact_issues.append("owner_change_ids_missing")
        pending.append(
            (
                "owner_change_ids_missing",
                REVIEWER_SEAM_ID,
                "owner_change_assessments",
                "Owner changes lacked host-minted IDs; reviewer text was not used as an authority key",
            )
        )
    owner_change_assessments, owner_diagnostics, owner_issues = _reconcile_owner_assessments(
        canonical_owner_issues,
        supplied_owner_assessments,
    )
    pending.extend(owner_diagnostics)
    artifact_issues.extend(owner_issues)

    (
        classified_required_changes,
        canonical_changes,
        classification_diagnostics,
        classification_issues,
    ) = _reconcile_classified_changes(
        (
            required_changes
            if decision in {PlanReviewDecisionValue.ACCEPT, PlanReviewDecisionValue.REVISE}
            or supplied_changes
            else []
        ),
        supplied_changes,
        known_issues=known_issues,
        branch_id=branch_id,
        source_message_id=source_message_id,
        reviewer_role="independent_reviewer",
        review_round=review_round,
        plan_digest=plan_digest,
        seam_id=REVIEWER_SEAM_ID,
        field="classified_required_changes",
    )
    pending.extend(classification_diagnostics)
    artifact_issues.extend(classification_issues)
    if classified_required_changes:
        required_changes = list(dict.fromkeys([*canonical_changes, *retained_change_text]))
    assessments: list[PlanReviewCriterionAssessmentMirror] = []
    authoritative_assessment_indexes: set[int] = set()

    for index, assessment in enumerate(content.criterion_assessments):
        criterion = assessment.criterion.strip() or "incomplete_review_criterion"
        rationale = assessment.rationale.strip()
        assessment_complete = True
        status = _normalized_criterion_status(assessment.status)
        if status is None:
            # This ONE criterion loses its authority and says so; the review as a whole keeps its
            # decision. Operator ruling 2026-07-27: the authority boundary is the top-level
            # `decision` field -- a Literal that failed 0 of 167 live reviews -- not the wording of
            # one criterion label. Appending to `artifact_issues` here withheld review-complete
            # authority for the WHOLE review, which is how 8 live reviews were nullified outright,
            # one of them a unanimous 8-of-8 accept whose only fault was answering "satisfied".
            # AGENTS.md rule 11: never discard a traceable result for phrasing.
            status = PlanReviewCriterionStatus.CONCERN
            assessment_complete = False
            pending.append(
                (
                    "unknown_criterion_status",
                    CRITERION_SEAM_ID,
                    f"criterion_assessments[{index}].status",
                    "criterion retained with its prose, but its status label did not resolve to a "
                    "controlled value, so this criterion alone was stored as a non-authoritative "
                    "concern; the review's own decision is unaffected",
                )
            )
        if not rationale:
            rationale = MISSING_CRITERION_RATIONALE
            assessment_complete = False
            artifact_issues.append("missing_criterion_rationale")
            pending.append(
                (
                    "missing_criterion_rationale",
                    CRITERION_SEAM_ID,
                    f"criterion_assessments[{index}].rationale",
                    "criterion retained with an explicit marker because its rationale was blank",
                )
            )
        if not assessment.criterion.strip():
            assessment_complete = False
            artifact_issues.append("missing_criterion_name")
            pending.append(
                (
                    "missing_criterion_name",
                    CRITERION_SEAM_ID,
                    f"criterion_assessments[{index}].criterion",
                    "unnamed criterion retained under an explicit incomplete-review marker",
                )
            )
        assessments.append(
            assessment.model_copy(
                update={
                    "criterion": criterion,
                    "status": status,
                    "rationale": rationale,
                    "evidence_ids": _clean_text_list(assessment.evidence_ids),
                }
            )
        )
        if assessment_complete:
            authoritative_assessment_indexes.add(index)

    if not assessments:
        assessments.append(
            PlanReviewCriterionAssessmentMirror(
                criterion="review_completeness",
                status=PlanReviewCriterionStatus.CONCERN,
                rationale=MISSING_CRITERION_RATIONALE,
            )
        )
        pending.append(
            (
                "missing_criterion_assessments",
                REVIEWER_SEAM_ID,
                "criterion_assessments",
                "missing assessment list retained as one flagged incomplete assessment",
            )
        )
        artifact_issues.append("missing_criterion_assessments")

    failed = [
        item.criterion
        for index, item in enumerate(assessments)
        if index in authoritative_assessment_indexes
        and item.status == PlanReviewCriterionStatus.FAIL
    ]
    if original == PlanReviewDecisionValue.ACCEPT and failed:
        artifact_issues.append("accepted_failed_criterion")
        pending.append(
            (
                "accepted_failed_criterion",
                REVIEWER_SEAM_ID,
                "decision,criterion_assessments",
                "accept contradicted a failed criterion; original review content was retained "
                "but marked incomplete without inventing a scientific blocker or revision",
            )
        )

    blocking_owner_assessments = [
        item
        for item in owner_change_assessments
        if item.classification == PlanReviewChangeClass.SCIENTIFIC_BLOCKER
        or item.hard_boundary_implicated
    ]
    if decision == PlanReviewDecisionValue.ACCEPT and blocking_owner_assessments:
        decision = PlanReviewDecisionValue.REVISE
        for owner_assessment in blocking_owner_assessments:
            if owner_assessment.change_id not in {
                item.change_id for item in classified_required_changes
            }:
                classified_required_changes.append(owner_assessment)
                required_changes.append(owner_assessment.change)
        pending.append(
            (
                "accepted_blocking_owner_change",
                REVIEWER_SEAM_ID,
                "decision,owner_change_assessments",
                "accept contradicted a scientific-blocker or hard-boundary assessment of an "
                "Owner change; downgraded to revise",
            )
        )

    if decision == PlanReviewDecisionValue.REVISE and not classified_required_changes:
        # Adopt the reviewer's own endorsed blockers before calling the review empty. The active
        # prompt (plan_fidelity_reviewer/v6) tells the reviewer to put endorsements of Owner
        # issues in `owner_change_assessments` and reserve `classified_required_changes` for NEW
        # issues -- so a compliant reviewer produces exactly the shape this check called
        # incomplete. Measured: 11 of 11 independent `revise` verdicts in the live corpus were
        # nullified here, and 8 families burned their whole 3-round revise budget at
        # rounds_used: 0 while holding a reviewer-endorsed, change_id-bound scientific blocker.
        # The promotion itself is not new -- the ACCEPT branch directly above does the same thing
        # with the same list; this is its missing mirror image.
        for owner_assessment in blocking_owner_assessments:
            classified_required_changes.append(owner_assessment)
            required_changes.append(owner_assessment.change)
        if classified_required_changes:
            pending.append(
                (
                    "revise_adopted_endorsed_owner_blockers",
                    REVIEWER_SEAM_ID,
                    "decision,owner_change_assessments",
                    "revise raised no new issue of its own; the reviewer's endorsed blocking "
                    "Owner issues were adopted as the planner's work rather than discarding the "
                    "review",
                )
            )
    if decision == PlanReviewDecisionValue.REVISE and not classified_required_changes:
        # Genuinely uninterpretable: revise with no new issue AND no endorsed blocker leaves the
        # planner nothing to act on, so this one stays an artifact issue.
        artifact_issues.append("missing_required_changes")
        pending.append(
            (
                "missing_required_changes",
                REVIEWER_SEAM_ID,
                "required_changes",
                "revise supplied no classified issue and endorsed no blocking Owner issue; "
                "marked review-incomplete without creating scientific work for the planner",
            )
        )

    if decision == PlanReviewDecisionValue.REJECT and (
        rejection_reason is None or not rejection_reason.is_rejection
    ):
        artifact_issues.append("missing_rejection_reason")
        pending.append(
            (
                "missing_rejection_reason",
                REVIEWER_SEAM_ID,
                "decision,rejection_reason",
                "reject lacked a typed terminal basis; marked review-incomplete rather than "
                "inventing a scientific rejection or planner revision",
            )
        )

    if content.material_revision_detected and not novelty_recheck_required:
        novelty_recheck_required = True
        pending.append(
            (
                "material_revision_requires_novelty_recheck",
                REVIEWER_SEAM_ID,
                "novelty_recheck_required",
                "forced true because every material scientific revision requires renewed novelty review",
            )
        )

    reconciled = content.model_copy(
        update={
            "decision": decision,
            "rationale": overall_rationale,
            "required_changes": required_changes,
            "classified_required_changes": classified_required_changes,
            "rejection_reason": rejection_reason,
            "criterion_assessments": assessments,
            "owner_change_assessments": owner_change_assessments,
            "novelty_recheck_required": novelty_recheck_required,
            "review_complete": not artifact_issues,
            "review_artifact_issues": list(dict.fromkeys(artifact_issues)),
        }
    )
    return reconciled, _diagnostics(
        pending,
        branch_id=branch_id,
        source_message_id=source_message_id,
        reviewer_role="independent_reviewer",
        original_decision=original,
        final_decision=decision,
    )


def _reconcile_classified_changes(
    required_changes: list[str],
    supplied: list[ClassifiedPlanReviewChange],
    *,
    known_issues: Sequence[PlanReviewIssueLedgerEntry],
    branch_id: str,
    source_message_id: str,
    reviewer_role: Literal["question_owner", "independent_reviewer"],
    review_round: int,
    plan_digest: str,
    seam_id: str,
    field: str,
) -> tuple[
    list[ClassifiedPlanReviewChange],
    list[str],
    list[tuple[str, str, str, str]],
    list[str],
]:
    """Canonicalize review issues by host ID without using prose as an authority join key."""

    cleaned_required = list(dict.fromkeys(_clean_text_list(required_changes)))
    known_by_id = {item.change_id: item for item in known_issues}
    diagnostics: list[tuple[str, str, str, str]] = []
    artifact_issues: list[str] = []
    reconciled: list[ClassifiedPlanReviewChange] = []
    seen_ids: set[str] = set()
    reusable_known = [
        item for item in known_issues if item.status != PlanReviewIssueStatus.RESOLVED
    ]
    unique_unkeyed_known_id = (
        reusable_known[0].change_id
        if len(reusable_known) == 1 and len(supplied) == 1 and not supplied[0].change_id.strip()
        else ""
    )
    for index, item in enumerate(supplied):
        # A single active ledger issue has exactly one possible referent; bind it without comparing
        # prose. Multiple issues always require explicit IDs.
        change_id = item.change_id.strip() or unique_unkeyed_known_id
        change = item.change.strip()
        known = known_by_id.get(change_id) if change_id else None
        if known is not None:
            change = known.change
        elif change_id:
            artifact_issues.append("unknown_change_id")
            diagnostics.append(
                (
                    "unknown_change_id",
                    seam_id,
                    field,
                    "review supplied an unknown change_id; host minted a replacement but withheld "
                    "review-complete authority",
                )
            )
            if not change:
                continue
            change_id = ""
        if not change:
            artifact_issues.append("missing_change_text")
            diagnostics.append(
                ("missing_change_text", seam_id, field, "new review issue omitted change text")
            )
            continue
        if not change_id:
            change_id = _mint_change_id(
                branch_id=branch_id,
                source_message_id=source_message_id,
                reviewer_role=reviewer_role,
                ordinal=index,
                change=change,
            )
        if change_id in seen_ids:
            artifact_issues.append("duplicate_change_id")
            diagnostics.append(
                (
                    "duplicate_change_id",
                    seam_id,
                    field,
                    "duplicate review change_id ignored; prose was not used to disambiguate it",
                )
            )
            continue
        seen_ids.add(change_id)
        canonical = item.model_copy(update={"change_id": change_id, "change": change})
        if (
            known is not None
            and known.status == PlanReviewIssueStatus.RESOLVED
            and canonical.classification == PlanReviewChangeClass.SCIENTIFIC_BLOCKER
        ):
            artifact_issues.append("resolved_issue_reopened")
            diagnostics.append(
                (
                    "resolved_issue_reopened",
                    seam_id,
                    field,
                    "a resolved issue ID was reopened as a blocker; a genuinely revision-created "
                    "issue must be submitted as new with an explicit late_blocker_basis",
                )
            )
        if (
            review_round > 0
            and known is None
            and canonical.classification == PlanReviewChangeClass.SCIENTIFIC_BLOCKER
            and canonical.late_blocker_basis is None
        ):
            artifact_issues.append("late_blocker_basis_missing")
            diagnostics.append(
                (
                    "late_blocker_basis_missing",
                    seam_id,
                    field,
                    "new post-round-zero blocker lacked a plan-diff or hard-boundary basis; "
                    "review marked incomplete instead of moving the planner goalposts",
                )
            )
        if not plan_digest:
            artifact_issues.append("plan_digest_missing")
        reconciled.append(canonical)

    if cleaned_required and not supplied:
        artifact_issues.append("missing_change_classification")
        diagnostics.append(
            (
                "missing_change_classification",
                seam_id,
                field,
                "review changes lacked typed classifications; no scientific blocker or hard "
                "boundary was synthesized",
            )
        )
    elif cleaned_required and len(cleaned_required) != len(reconciled):
        # Diagnostic only. `required_changes` is a compatibility DISPLAY list -- the active
        # question_owner/v3 prompt says so in as many words, and the independent reviewer's DTO
        # deletes the field outright and derives it from the typed list. This check was still
        # enforcing question_owner/v2's contract, which required exact coverage, and its own
        # message admitted the incoherence: "typed issues were retained but review-complete
        # authority was withheld". It converted a unanimous owner-plus-independent ACCEPT into
        # failed_validation, with the artifact showing 4 display and 4 typed changes perfectly
        # paired -- the mismatch existed only in the raw reply, before this function repaired it.
        #
        # It does NOT lose all effect: it still blocks the revise-to-accept normalization below,
        # because unmatched display prose could be a blocker the model never classified, and
        # upgrading a verdict on ambiguous input is the one direction that must stay closed.
        diagnostics.append(
            (
                "change_classification_count_mismatch",
                seam_id,
                field,
                "display change count differed from typed issue count; the typed issues are "
                "authoritative and were retained, and the review keeps its own decision",
            )
        )
    return reconciled, [item.change for item in reconciled], diagnostics, artifact_issues


def _reconcile_overall_rationale(
    rationale: str,
    *,
    seam_id: str,
) -> tuple[str, list[tuple[str, str, str, str]], list[str]]:
    cleaned = rationale.strip()
    if cleaned:
        return cleaned, [], []
    return (
        MISSING_REVIEW_RATIONALE,
        [
            (
                "missing_review_rationale",
                seam_id,
                "rationale",
                "review retained with an explicit missing-detail marker; no review decision "
                "gained closeout or revision authority",
            )
        ],
        ["missing_review_rationale"],
    )


def _strict_classified_change_mirrors(
    supplied: Sequence[ClassifiedPlanReviewChangeMirror],
    *,
    seam_id: str,
    field: str,
) -> tuple[
    list[ClassifiedPlanReviewChange],
    list[str],
    list[tuple[str, str, str, str]],
    list[str],
]:
    """Rebuild only exact, explained classifications; preserve all other text as incomplete.

    Unknown classifications and missing rationales never default to ``scientific_blocker`` (or to
    any nonblocking class). Their change prose remains available through ``required_changes``, the
    raw provider transcript, and the typed diagnostic, while the review loses completion authority.
    """

    valid: list[ClassifiedPlanReviewChange] = []
    retained_change_text: list[str] = []
    diagnostics: list[tuple[str, str, str, str]] = []
    artifact_issues: list[str] = []
    for index, item in enumerate(supplied):
        change = item.change.strip()
        classification_text = item.classification.strip()
        rationale = item.rationale.strip()
        invalid = False
        try:
            classification = PlanReviewChangeClass(classification_text)
        except ValueError:
            invalid = True
            artifact_issues.append("unknown_change_classification")
            diagnostics.append(
                (
                    "unknown_change_classification",
                    seam_id,
                    f"{field}[{index}].classification",
                    "review change text was retained, but the unknown classification was not "
                    "mapped to a blocker or nonblocker: " + repr(item.classification),
                )
            )
            classification = None
        if not rationale:
            invalid = True
            artifact_issues.append("missing_change_rationale")
            diagnostics.append(
                (
                    "missing_change_rationale",
                    seam_id,
                    f"{field}[{index}].rationale",
                    "review change text was retained, but an unexplained classification gained "
                    "no blocker, revision, or closeout authority",
                )
            )
        if invalid or classification is None:
            if change and change not in retained_change_text:
                retained_change_text.append(change)
            continue
        payload = item.model_dump(mode="python")
        payload["classification"] = classification
        payload["rationale"] = rationale
        try:
            valid.append(ClassifiedPlanReviewChange.model_validate(payload))
        except ValueError as exc:
            if change and change not in retained_change_text:
                retained_change_text.append(change)
            artifact_issues.append("invalid_classified_change")
            diagnostics.append(
                (
                    "invalid_classified_change",
                    seam_id,
                    f"{field}[{index}]",
                    "review change content was retained in the raw transcript but failed the "
                    "strict authority shape without repair: " + str(exc),
                )
            )
    return (
        valid,
        retained_change_text,
        diagnostics,
        list(dict.fromkeys(artifact_issues)),
    )


def _reconcile_owner_assessments(
    owner_issues: Sequence[ClassifiedPlanReviewChange],
    supplied: Sequence[ClassifiedPlanReviewChange],
) -> tuple[
    list[ClassifiedPlanReviewChange],
    list[tuple[str, str, str, str]],
    list[str],
]:
    """Bind independent assessments to Owner issues by change_id only."""

    expected = {item.change_id: item for item in owner_issues if item.change_id}
    if not expected:
        # Extra assessment prose has no authority when the Owner raised no typed issue. Ignore it
        # rather than turning harmless stale model output into planner work.
        return [], [], []
    diagnostics: list[tuple[str, str, str, str]] = []
    artifact_issues: list[str] = []
    reconciled: list[ClassifiedPlanReviewChange] = []
    seen: set[str] = set()
    unique_unkeyed_id = (
        next(iter(expected))
        if len(expected) == 1 and len(supplied) == 1 and not supplied[0].change_id.strip()
        else ""
    )
    for item in supplied:
        # A single unkeyed assessment has exactly one possible referent and can be bound without
        # comparing prose. Multiple issues always require explicit IDs.
        change_id = item.change_id.strip() or unique_unkeyed_id
        owner_issue = expected.get(change_id)
        if owner_issue is None or change_id in seen:
            artifact_issues.append("unmatched_owner_change_id")
            diagnostics.append(
                (
                    "unmatched_owner_change_id",
                    REVIEWER_SEAM_ID,
                    "owner_change_assessments",
                    "ignored an unknown or duplicate owner change_id; English text was not used "
                    "as fallback authority",
                )
            )
            continue
        seen.add(change_id)
        reconciled.append(
            item.model_copy(update={"change_id": change_id, "change": owner_issue.change})
        )
    missing = sorted(set(expected) - seen)
    if missing:
        artifact_issues.append("missing_owner_change_assessment")
        diagnostics.append(
            (
                "missing_owner_change_assessment",
                REVIEWER_SEAM_ID,
                "owner_change_assessments",
                "independent review omitted Owner change IDs; no hard blocker was synthesized",
            )
        )
    return reconciled, diagnostics, artifact_issues


def _mint_change_id(
    *,
    branch_id: str,
    source_message_id: str,
    reviewer_role: Literal["question_owner", "independent_reviewer"],
    ordinal: int,
    change: str,
) -> str:
    identity = {
        "branch_id": branch_id,
        "source_message_id": source_message_id,
        "reviewer_role": reviewer_role,
        "ordinal": ordinal,
        "initial_change": " ".join(change.split()),
    }
    return f"review-change-{stable_hash(identity)[:16]}"


def persist_plan_review_ingestion_diagnostics(
    diagnostics: list[PlanReviewIngestionDiagnostic], diagnostics_dir: str | Path
) -> list[Path]:
    """Persist every emitted diagnostic under the branch review workspace."""

    root = Path(diagnostics_dir) / "plan_review_ingestion"
    return [dump_data(item, root / f"{item.diagnostic_id}.yaml") for item in diagnostics]


def _diagnostics(
    pending: list[tuple[str, str, str, str]],
    *,
    branch_id: str,
    source_message_id: str,
    reviewer_role: Literal["question_owner", "independent_reviewer"],
    original_decision: PlanReviewDecisionValue,
    final_decision: PlanReviewDecisionValue,
) -> list[PlanReviewIngestionDiagnostic]:
    diagnostics: list[PlanReviewIngestionDiagnostic] = []
    for index, (code, seam_id, field, detail) in enumerate(pending, start=1):
        identity = {
            "branch_id": branch_id,
            "source_message_id": source_message_id,
            "reviewer_role": reviewer_role,
            "code": code,
            "field": field,
            "sequence": index,
        }
        diagnostics.append(
            PlanReviewIngestionDiagnostic(
                diagnostic_id=f"review-ingest-{stable_hash(identity)[:16]}",
                code=code,
                seam_id=seam_id,
                branch_id=branch_id,
                source_message_id=source_message_id,
                reviewer_role=reviewer_role,
                field=field,
                original_decision=original_decision,
                final_decision=final_decision,
                detail=detail,
            )
        )
    return diagnostics


def _clean_text_list(items: list[str]) -> list[str]:
    return [item.strip() for item in items if item.strip()]
