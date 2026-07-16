"""Multi-axis run/family outcome schema.

``FamilyInclusionLabel`` alone (the coarse public bucket) cannot express what actually happened to a
family across the whole pipeline: it was shortlisted, THEN a planner rejected it for a *specific*
reason, or the budget was exhausted, or a sandbox spawn failed, or the dossier failed to render. A
single coarse label loses that — so the audit sidecar needs a multi-AXIS outcome that records each
stage's honest result plus the REAL reason, even when the shortlist manifest can only bucket it coarsely
(e.g. ``run_incomplete → deferred``).

Schema only; the 5c-1b driver populates + persists it. ``infrastructure failure ≠ scientific rejection``
is enforced here too: an infrastructure stop carries an infrastructure ``failure_class``, never a
scientific reject.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .shortlist_outcome import FamilyInclusionLabel
from .stage_receipt import INFRASTRUCTURE_FAILURE_CLASSES, FailureClass


class ShortlistAxis(StrEnum):
    INCLUDED = "included"
    REJECTED_SCIENTIFIC = "rejected_scientific"
    DEFERRED_MATERIAL_REVISION = "deferred_material_revision"
    DEFERRED_INSUFFICIENT_EVIDENCE = "deferred_insufficient_evidence"
    RUN_INCOMPLETE = "run_incomplete"


class PlanningAxis(StrEnum):
    NOT_RUN = "not_run"
    PLAN = "plan"
    PLANNER_REJECTION = "planner_rejection"
    BUDGET_EXHAUSTED = "budget_exhausted"
    ESCALATION = "escalation"
    MATERIAL_DEFERRED = "material_deferred"


class ReviewAxis(StrEnum):
    NOT_RUN = "not_run"
    ACCEPT = "accept"
    REVISION_REQUIRED = "revision_required"
    # A revise decision that reached an honest bounded-loop terminal. Reviews DID run; this is
    # distinct from the mid-loop REVISION_REQUIRED state above.
    REVISION_TERMINAL = "revision_terminal"
    REJECT = "reject"
    HUMAN_ESCALATION = "human_escalation"


class DossierAxis(StrEnum):
    NOT_RUN = "not_run"
    # The accepted-plan scientific dossier passed its configured review and render gates.
    RENDERED = "rendered"
    # A user-readable terminal dossier/fallback was rendered without accepted-plan authority.
    TERMINAL_RENDERED = "terminal_rendered"
    RENDER_FAILURE = "render_failure"


class FamilyWarningClass(StrEnum):
    PROVIDER = "provider_warning"
    VALIDATION = "validation_warning"


class FamilyRunOutcome(BaseModel):
    """Every axis of one family's journey + the coarse public label + the preserved real reason."""

    model_config = ConfigDict(extra="forbid")

    question_family_id: str
    shortlist_axis: ShortlistAxis
    planning_axis: PlanningAxis = PlanningAxis.NOT_RUN
    # Free sub-classification of a planner rejection (dataset_mismatch / operationalization_failure /
    # scientific_drift / ...). Present only when planning_axis == planner_rejection.
    planner_rejection_subtype: str = ""
    review_axis: ReviewAxis = ReviewAxis.NOT_RUN
    dossier_axis: DossierAxis = DossierAxis.NOT_RUN
    # The coarse honest bucket shown in the user-facing summary (never "approved"/"novel"/"serious").
    public_summary_label: FamilyInclusionLabel
    # Set when a stage broke or terminated; None while everything is still scientific-clean.
    failure_class: FailureClass | None = None
    # Recoverable family-local degradation. Unlike failure_class, this does not point at a failed
    # shared StageReceipt and does not make an otherwise closed run incomplete.
    warning_class: FamilyWarningClass | None = None
    # An infrastructure terminal MUST point at the StageReceipt that actually failed.
    failed_stage_receipt_id: str = ""
    # A close prior directly recaps every active variant (drives the DIRECT_RECAP public label).
    novelty_direct_recap: bool = False
    # The REAL reason, preserved for the audit sidecar even when the coarse label buckets it away.
    reason: str = ""

    @classmethod
    def derive(
        cls,
        *,
        question_family_id: str,
        shortlist_axis: ShortlistAxis,
        planning_axis: PlanningAxis = PlanningAxis.NOT_RUN,
        planner_rejection_subtype: str = "",
        review_axis: ReviewAxis = ReviewAxis.NOT_RUN,
        dossier_axis: DossierAxis = DossierAxis.NOT_RUN,
        failure_class: FailureClass | None = None,
        warning_class: FamilyWarningClass | None = None,
        failed_stage_receipt_id: str = "",
        novelty_direct_recap: bool = False,
        reason: str = "",
    ) -> FamilyRunOutcome:
        """Build the outcome from the run's axes, DERIVING (not free-setting) the public label."""
        label = _derive_public_label(
            shortlist_axis=shortlist_axis,
            planning_axis=planning_axis,
            review_axis=review_axis,
            dossier_axis=dossier_axis,
            failure_class=failure_class,
            warning_class=warning_class,
            novelty_direct_recap=novelty_direct_recap,
        )
        return cls(
            question_family_id=question_family_id,
            shortlist_axis=shortlist_axis,
            planning_axis=planning_axis,
            planner_rejection_subtype=planner_rejection_subtype,
            review_axis=review_axis,
            dossier_axis=dossier_axis,
            public_summary_label=label,
            failure_class=failure_class,
            warning_class=warning_class,
            failed_stage_receipt_id=failed_stage_receipt_id,
            novelty_direct_recap=novelty_direct_recap,
            reason=reason,
        )

    @model_validator(mode="after")
    def _axes_are_internally_consistent(self) -> FamilyRunOutcome:
        if self.failure_class is not None and self.warning_class is not None:
            raise ValueError("a family outcome cannot be both a hard failure and a warning")
        if self.warning_class is not None and not (
            self.shortlist_axis == ShortlistAxis.INCLUDED
            and self.dossier_axis == DossierAxis.TERMINAL_RENDERED
        ):
            raise ValueError(
                "a family warning requires an included family with a terminal rendered dossier"
            )
        if self.planner_rejection_subtype and self.planning_axis != PlanningAxis.PLANNER_REJECTION:
            raise ValueError(
                "planner_rejection_subtype is only valid when planning_axis == planner_rejection"
            )
        # A run-incomplete shortlist outcome must carry an infrastructure failure_class (never a
        # scientific rejection).
        if (
            self.shortlist_axis == ShortlistAxis.RUN_INCOMPLETE
            and self.failure_class not in INFRASTRUCTURE_FAILURE_CLASSES
        ):
            raise ValueError(
                "a run_incomplete outcome requires an infrastructure failure_class "
                "(infrastructure failure is never a scientific rejection)"
            )
        # ANY infrastructure failure_class (a back-half infra stop on an included family too) must point
        # at the StageReceipt that actually failed — infra never floats free of its evidence.
        if (
            self.failure_class in INFRASTRUCTURE_FAILURE_CLASSES
            and not self.failed_stage_receipt_id.strip()
        ):
            raise ValueError("an infrastructure terminal must reference the failed StageReceipt id")
        # A back-half axis can only have run if the family was INCLUDED by the shortlist.
        if self.shortlist_axis != ShortlistAxis.INCLUDED and not (
            self.planning_axis == PlanningAxis.NOT_RUN
            and self.review_axis == ReviewAxis.NOT_RUN
            and self.dossier_axis == DossierAxis.NOT_RUN
        ):
            raise ValueError(
                "a non-included family cannot have run planning/review/dossier (they must be NOT_RUN)"
            )
        # An accepted scientific dossier can ONLY exist behind a planned + accepted family.
        # TERMINAL_RENDERED is deliberately separate: reject/defer/revise/provider-warning
        # families still need a human-readable closeout without gaining accepted-plan authority.
        if self.dossier_axis == DossierAxis.RENDERED and not (
            self.planning_axis == PlanningAxis.PLAN and self.review_axis == ReviewAxis.ACCEPT
        ):
            raise ValueError("a rendered dossier requires planning == plan and review == accept")
        # REVISION_REQUIRED is a mid-loop state, never a terminal outcome.
        if self.review_axis == ReviewAxis.REVISION_REQUIRED:
            raise ValueError("revision_required is not a terminal review outcome")
        # The public label is DERIVED, never a free field — reject a mismatched hand-set value.
        derived = _derive_public_label(
            shortlist_axis=self.shortlist_axis,
            planning_axis=self.planning_axis,
            review_axis=self.review_axis,
            dossier_axis=self.dossier_axis,
            failure_class=self.failure_class,
            warning_class=self.warning_class,
            novelty_direct_recap=self.novelty_direct_recap,
        )
        if self.public_summary_label != derived:
            raise ValueError(
                f"public_summary_label {self.public_summary_label.value!r} does not match the "
                f"derived label {derived.value!r} for these axes"
            )
        return self


def _derive_public_label(
    *,
    shortlist_axis: ShortlistAxis,
    planning_axis: PlanningAxis,
    review_axis: ReviewAxis,
    dossier_axis: DossierAxis,
    failure_class: FailureClass | None,
    warning_class: FamilyWarningClass | None,
    novelty_direct_recap: bool,
) -> FamilyInclusionLabel:
    """The single deterministic axis→public-label map (used by ``derive`` AND the validator)."""
    # Hard/shared infrastructure ALWAYS wins → run_incomplete (never a scientific label).
    if failure_class in INFRASTRUCTURE_FAILURE_CLASSES:
        return FamilyInclusionLabel.RUN_INCOMPLETE
    if warning_class is not None:
        return FamilyInclusionLabel.COMPLETED_WITH_WARNINGS
    if shortlist_axis == ShortlistAxis.RUN_INCOMPLETE:
        return FamilyInclusionLabel.RUN_INCOMPLETE
    if shortlist_axis == ShortlistAxis.REJECTED_SCIENTIFIC:
        return FamilyInclusionLabel.REJECTED_SCIENTIFIC
    if shortlist_axis == ShortlistAxis.DEFERRED_MATERIAL_REVISION:
        return FamilyInclusionLabel.DEFERRED_MATERIAL_REVISION
    if shortlist_axis == ShortlistAxis.DEFERRED_INSUFFICIENT_EVIDENCE:
        return (
            FamilyInclusionLabel.DIRECT_RECAP
            if novelty_direct_recap
            else FamilyInclusionLabel.DEFERRED_INSUFFICIENT_EVIDENCE
        )
    # shortlist_axis == INCLUDED → decided by the back half.
    if dossier_axis == DossierAxis.RENDERED:
        return FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW
    if (
        planning_axis == PlanningAxis.PLAN
        and review_axis == ReviewAxis.ACCEPT
        and dossier_axis in {DossierAxis.RENDER_FAILURE, DossierAxis.TERMINAL_RENDERED}
    ):
        return FamilyInclusionLabel.PUBLIC_DOSSIER_REVISION_REQUIRED
    if review_axis == ReviewAxis.REJECT or planning_axis == PlanningAxis.PLANNER_REJECTION:
        return FamilyInclusionLabel.REJECTED_SCIENTIFIC
    if planning_axis == PlanningAxis.BUDGET_EXHAUSTED:
        return FamilyInclusionLabel.REVISION_BUDGET_EXHAUSTED
    if planning_axis in {PlanningAxis.MATERIAL_DEFERRED, PlanningAxis.ESCALATION}:
        return FamilyInclusionLabel.DEFERRED_MATERIAL_REVISION
    return FamilyInclusionLabel.DEFERRED_INSUFFICIENT_EVIDENCE


class RunTerminal(BaseModel):
    """A clean RUN-LEVEL terminal — a shared front-half (A→D) failure that produced NO families (F3).

    NOT a per-family outcome: there are no families to speak of. Two honest kinds:
    - an INFRASTRUCTURE failure of a shared stage (provider/timeout/parser/validation), pointing at
      the stage receipt that failed; and
    - a SCIENTIFIC front-half terminal — a genuine evidence insufficiency that produced no families
      to plan (e.g. the paper half accepted zero papers). This is NOT a per-family scientific
      rejection (there are no families); it is the honest run-level equivalent of the paperbank
      all-unusable / insufficient-evidence terminal, and labeling it infrastructure would be
      dishonest.
    """

    model_config = ConfigDict(extra="forbid")

    failed_stage: str
    failed_stage_receipt_id: str
    failure_class: FailureClass
    reason: str = ""

    @model_validator(mode="after")
    def _valid_terminal(self) -> RunTerminal:
        allowed = INFRASTRUCTURE_FAILURE_CLASSES | {FailureClass.SCIENTIFIC}
        if self.failure_class not in allowed:
            raise ValueError("a run-level terminal is infrastructure or a scientific insufficiency")
        if not self.failed_stage_receipt_id.strip():
            raise ValueError("a run-level terminal must reference the failed StageReceipt id")
        return self


class RunResult(BaseModel):
    """Run result with every durable family outcome plus an optional shared terminal.

    A shared back-half failure can happen after one or more sibling families have already
    completed.  Those validated outcomes remain usable and must not disappear merely because
    later shared processing stopped.  A front-half terminal still naturally has no family outcomes.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    family_outcomes: list[FamilyRunOutcome] = Field(default_factory=list)
    run_terminal: RunTerminal | None = None
    # User-facing authority: downgraded to development_model_surrogate when any reviewer ran mock (F1).
    development_surrogate: bool = False
