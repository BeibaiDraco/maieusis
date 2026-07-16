from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .analysis_plan import AnalysisPlan


class BranchActorRole(StrEnum):
    QUESTION_SCIENTIST = "question_scientist"
    QUESTION_OWNER = "question_owner"
    DATASET_PLANNER = "dataset_planner"
    INDEPENDENT_REVIEWER = "independent_reviewer"
    HUMAN_EXPERT = "human_expert"
    BRANCH_MANAGER = "branch_manager"


class BranchDecisionKind(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    ACCEPTED_REQUIRES_NEW_SKILL = "accepted_requires_new_skill"
    REJECTED_DATASET_MISMATCH = "rejected_dataset_mismatch"
    REJECTED_OPERATIONALIZATION_FAILURE = "rejected_operationalization_failure"
    REJECTED_SCIENTIFIC_DRIFT = "rejected_scientific_drift"
    REJECTED_INSUFFICIENT_EVIDENCE = "rejected_insufficient_evidence"
    REJECTED_LOW_SCIENTIFIC_VALUE = "rejected_low_scientific_value"
    HUMAN_ESCALATION = "human_escalation"

    @property
    def is_accepted(self) -> bool:
        return self in {
            BranchDecisionKind.ACCEPTED,
            BranchDecisionKind.ACCEPTED_REQUIRES_NEW_SKILL,
        }

    @property
    def is_rejection(self) -> bool:
        return self in {
            BranchDecisionKind.REJECTED_DATASET_MISMATCH,
            BranchDecisionKind.REJECTED_OPERATIONALIZATION_FAILURE,
            BranchDecisionKind.REJECTED_SCIENTIFIC_DRIFT,
            BranchDecisionKind.REJECTED_INSUFFICIENT_EVIDENCE,
            BranchDecisionKind.REJECTED_LOW_SCIENTIFIC_VALUE,
        }


class OperationalizationDecisionValue(StrEnum):
    ACCEPT = "accept"
    REVISE = "revise"
    REJECT = "reject"
    HUMAN_REVIEW = "human_review"


class PlanReviewDecisionValue(StrEnum):
    ACCEPT = "accept"
    REVISE = "revise"
    REJECT = "reject"
    HUMAN_REVIEW = "human_review"


class FeasibilityStatus(StrEnum):
    AVAILABLE = "available"
    PARTIALLY_AVAILABLE = "partially_available"
    UNAVAILABLE = "unavailable"
    UNCERTAIN = "uncertain"


class PlannerAssessment(StrEnum):
    SERVES_QUESTION = "serves_question"
    SERVES_AFTER_MINOR_REVISION = "serves_after_minor_revision"
    MATERIAL_REVISION_REQUIRED = "material_revision_required"
    CANNOT_SERVE_QUESTION = "cannot_serve_question"


class PlanReviewCriterionStatus(StrEnum):
    PASS = "pass"
    CONCERN = "concern"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


class PlanReviewChangeClass(StrEnum):
    """Scientific authority of one requested plan change.

    Only ``scientific_blocker`` justifies another planning revision.  A
    ``pre_execution_lock`` remains visible in the dossier and must be resolved before any later
    execution bridge, while an ``optional_improvement`` is useful advice that cannot block the
    planning product.
    """

    SCIENTIFIC_BLOCKER = "scientific_blocker"
    PRE_EXECUTION_LOCK = "pre_execution_lock"
    OPTIONAL_IMPROVEMENT = "optional_improvement"


class PlanReviewLateBlockerBasis(StrEnum):
    """Why a scientific blocker first appeared after review round zero."""

    INTRODUCED_BY_PLAN_REVISION = "introduced_by_plan_revision"
    HARD_BOUNDARY_OVERSIGHT = "hard_boundary_oversight"


class PlanReviewIssueStatus(StrEnum):
    """Durable disposition of one host-identified review issue."""

    OPEN = "open"
    RESOLVED = "resolved"
    RETAINED_PRE_EXECUTION_LOCK = "retained_pre_execution_lock"
    RETAINED_OPTIONAL_IMPROVEMENT = "retained_optional_improvement"


class PlanningMessageScope(StrEnum):
    FAMILY = "family"
    VARIANT = "variant"


class FamilyVariantPlanningEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    decision: BranchDecisionKind
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("variant_id", "question_seed_id", "summary")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FamilyVariantPlanningEntry fields must be non-empty")
        return value


class VariantAnalysisPlanEntry(BaseModel):
    """One accepted family variant's inspectable, non-executable analysis plan.

    ``PlanDraftMessage`` historically carried only a short per-variant summary.  Keeping the
    detailed plan in a nested typed entry preserves that compatibility surface while giving the
    serious direct-file route enough scientific content for owner/reviewer assessment and dossier
    rendering.
    """

    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    analysis_plan: AnalysisPlan

    @field_validator("variant_id", "question_seed_id")
    @classmethod
    def require_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("VariantAnalysisPlanEntry identity fields must be non-empty")
        return value


class PlanReviewCriterionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion: str
    status: PlanReviewCriterionStatus
    rationale: str
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("criterion", "rationale")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PlanReviewCriterionAssessment fields must be non-empty")
        return value

    @field_validator("evidence_ids")
    @classmethod
    def clean_evidence_ids(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class ClassifiedPlanReviewChange(BaseModel):
    """One review request with an explicit planning-product boundary classification."""

    model_config = ConfigDict(extra="forbid")

    # ``change_id`` is host-minted when an issue first appears.  Historical v2 artifacts did not
    # carry it, so the empty default remains readable as provenance.  Active v3 review messages
    # always persist a non-empty ID and reviewers join on that ID, never on English wording.
    change_id: str = ""
    change: str = ""
    classification: PlanReviewChangeClass
    rationale: str
    hard_boundary_implicated: bool = False
    late_blocker_basis: PlanReviewLateBlockerBasis | None = None
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("change_id", "change", "rationale")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("evidence_ids")
    @classmethod
    def clean_evidence_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))

    @model_validator(mode="after")
    def hard_boundaries_are_blockers(self) -> ClassifiedPlanReviewChange:
        if not self.change_id and not self.change:
            raise ValueError("ClassifiedPlanReviewChange requires change_id or change text")
        if not self.rationale:
            raise ValueError("ClassifiedPlanReviewChange rationale must be non-empty")
        if self.hard_boundary_implicated and (
            self.classification != PlanReviewChangeClass.SCIENTIFIC_BLOCKER
        ):
            raise ValueError("a hard-boundary review change must be a scientific_blocker")
        if self.late_blocker_basis is not None and (
            self.classification != PlanReviewChangeClass.SCIENTIFIC_BLOCKER
        ):
            raise ValueError("only a scientific_blocker may carry late_blocker_basis")
        if (
            self.late_blocker_basis == PlanReviewLateBlockerBasis.HARD_BOUNDARY_OVERSIGHT
            and not self.hard_boundary_implicated
        ):
            raise ValueError("hard_boundary_oversight requires hard_boundary_implicated")
        return self


class PlanReviewIssueLedgerEntry(BaseModel):
    """One stable review issue carried across bounded plan-review rounds."""

    model_config = ConfigDict(extra="forbid")

    change_id: str
    change: str
    origin: Literal["question_owner", "independent_reviewer"]
    classification: PlanReviewChangeClass
    rationale: str
    hard_boundary_implicated: bool = False
    late_blocker_basis: PlanReviewLateBlockerBasis | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    first_seen_round: int = Field(ge=0)
    last_seen_round: int = Field(ge=0)
    introduced_by_plan_digest: str
    status: PlanReviewIssueStatus

    @field_validator("change_id", "change", "rationale")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PlanReviewIssueLedgerEntry text fields must be non-empty")
        return value

    @field_validator("introduced_by_plan_digest")
    @classmethod
    def require_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("introduced_by_plan_digest must be lowercase sha256 hex")
        return value

    @field_validator("evidence_ids")
    @classmethod
    def clean_ledger_evidence_ids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))

    @model_validator(mode="after")
    def validate_ledger_entry(self) -> PlanReviewIssueLedgerEntry:
        if self.last_seen_round < self.first_seen_round:
            raise ValueError("review issue last_seen_round cannot precede first_seen_round")
        if self.hard_boundary_implicated and (
            self.classification != PlanReviewChangeClass.SCIENTIFIC_BLOCKER
        ):
            raise ValueError("a hard-boundary review issue must be a scientific_blocker")
        expected_status = {
            PlanReviewChangeClass.SCIENTIFIC_BLOCKER: PlanReviewIssueStatus.OPEN,
            PlanReviewChangeClass.PRE_EXECUTION_LOCK: (
                PlanReviewIssueStatus.RETAINED_PRE_EXECUTION_LOCK
            ),
            PlanReviewChangeClass.OPTIONAL_IMPROVEMENT: (
                PlanReviewIssueStatus.RETAINED_OPTIONAL_IMPROVEMENT
            ),
        }[self.classification]
        if self.status not in {expected_status, PlanReviewIssueStatus.RESOLVED}:
            raise ValueError("review issue status is inconsistent with its classification")
        return self


class PlanningMessageBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_id: str
    branch_id: str
    scope: PlanningMessageScope
    variant_id: str = ""
    question_seed_id: str = ""
    context_id: str
    owner_session_id: str
    actor_role: BranchActorRole
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    parent_message_id: str = ""
    message_type: str
    provider_id: str = ""
    model_id: str = ""
    session_id: str = ""
    prompt_version: str = ""
    input_digest: str = ""
    output_digest: str = ""
    payload_digest: str

    @field_validator(
        "message_id",
        "branch_id",
        "context_id",
        "owner_session_id",
        "payload_digest",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PlanningMessage identity and digest fields must be non-empty")
        return value

    @field_validator("payload_digest", "input_digest", "output_digest")
    @classmethod
    def validate_optional_digest(cls, value: str) -> str:
        if value and (len(value) != 64 or any(char not in "0123456789abcdef" for char in value)):
            raise ValueError("PlanningMessage digest fields must be lowercase sha256 hex")
        return value

    @model_validator(mode="after")
    def require_agent_provenance(self) -> PlanningMessageBase:
        if self.actor_role in {BranchActorRole.HUMAN_EXPERT, BranchActorRole.BRANCH_MANAGER}:
            return self
        required = {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "session_id": self.session_id,
            "prompt_version": self.prompt_version,
            "input_digest": self.input_digest,
            "output_digest": self.output_digest,
        }
        missing = [field for field, value in required.items() if not value.strip()]
        if missing:
            raise ValueError("PlanningMessage agent provenance missing: " + ", ".join(missing))
        return self

    @model_validator(mode="after")
    def validate_message_scope(self) -> PlanningMessageBase:
        if self.scope == PlanningMessageScope.FAMILY:
            if self.variant_id.strip() or self.question_seed_id.strip():
                raise ValueError("family-scoped PlanningMessage cannot carry variant identity")
        elif self.scope == PlanningMessageScope.VARIANT:
            missing = [
                field
                for field, value in {
                    "variant_id": self.variant_id,
                    "question_seed_id": self.question_seed_id,
                }.items()
                if not value.strip()
            ]
            if missing:
                raise ValueError("variant-scoped PlanningMessage missing: " + ", ".join(missing))
        return self


class ClarificationRequest(PlanningMessageBase):
    message_type: Literal["clarification_request"] = "clarification_request"
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    construct: str  # type: ignore[assignment]
    why_ambiguous: str
    dataset_implication: str
    candidate_interpretations: list[str] = Field(default_factory=list)
    planner_recommendation: str
    blocking: bool = True


class ScientificClarification(PlanningMessageBase):
    message_type: Literal["scientific_clarification"] = "scientific_clarification"
    actor_role: Literal[BranchActorRole.QUESTION_OWNER] = BranchActorRole.QUESTION_OWNER
    request_message_id: str
    selected_interpretation: str
    acceptable_alternatives: list[str] = Field(default_factory=list)
    must_preserve: list[str] = Field(default_factory=list)
    forbidden_reduction: list[str] = Field(default_factory=list)
    rationale: str


class OperationalizationProposal(PlanningMessageBase):
    message_type: Literal["operationalization_proposal"] = "operationalization_proposal"
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    construct: str  # type: ignore[assignment]
    proposed_measurement: str
    dataset_binding: list[str] = Field(default_factory=list)
    direct_or_proxy: Literal["direct", "operationalized", "proxy"]
    expected_validity: str
    failure_modes: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_variant_scope(self) -> OperationalizationProposal:
        if self.scope != PlanningMessageScope.VARIANT:
            raise ValueError("OperationalizationProposal must be variant-scoped")
        return self


class OperationalizationDecision(PlanningMessageBase):
    message_type: Literal["operationalization_decision"] = "operationalization_decision"
    actor_role: Literal[BranchActorRole.QUESTION_OWNER] = BranchActorRole.QUESTION_OWNER
    proposal_message_id: str
    decision: OperationalizationDecisionValue
    rationale: str
    required_changes: list[str] = Field(default_factory=list)
    preserves_scientific_intent: bool

    @model_validator(mode="after")
    def require_variant_scope(self) -> OperationalizationDecision:
        if self.scope != PlanningMessageScope.VARIANT:
            raise ValueError("OperationalizationDecision must be variant-scoped")
        return self


class DatasetFeasibilityFinding(PlanningMessageBase):
    message_type: Literal["dataset_feasibility_finding"] = "dataset_feasibility_finding"
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    requirement_id: str
    requirement: str
    status: FeasibilityStatus
    evidence_ids: list[str] = Field(default_factory=list)
    coverage_summary: str
    limitations: list[str] = Field(default_factory=list)
    impact_on_question: str

    @model_validator(mode="after")
    def require_variant_scope(self) -> DatasetFeasibilityFinding:
        if self.scope != PlanningMessageScope.VARIANT:
            raise ValueError("DatasetFeasibilityFinding must be variant-scoped")
        return self


class PlanDraftMessage(PlanningMessageBase):
    message_type: Literal["plan_draft"] = "plan_draft"
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    analysis_plan_id: str
    summary: str
    unresolved_decisions: list[str] = Field(default_factory=list)
    planner_assessment: PlannerAssessment
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)
    # Backward-compatible: historical plan drafts remain readable with an empty list.  The serious
    # direct-file artifact validator requires complete coverage for every accepted variant.
    variant_analysis_plans: list[VariantAnalysisPlanEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_family_outcomes(self) -> PlanDraftMessage:
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "PlanDraftMessage",
        )
        detail_ids = [entry.variant_id for entry in self.variant_analysis_plans]
        if len(detail_ids) != len(set(detail_ids)):
            raise ValueError("PlanDraftMessage variant_analysis_plans must be unique")
        if self.variant_analysis_plans:
            outcomes = {entry.variant_id: entry for entry in self.variant_outcomes}
            accepted_ids = {
                entry.variant_id for entry in self.variant_outcomes if entry.decision.is_accepted
            }
            if set(detail_ids) != accepted_ids:
                raise ValueError(
                    "PlanDraftMessage detailed plans must cover exactly the accepted variants"
                )
            for detail in self.variant_analysis_plans:
                outcome = outcomes[detail.variant_id]
                if detail.question_seed_id != outcome.question_seed_id:
                    raise ValueError(
                        "PlanDraftMessage detailed plan variant/question-seed identity mismatch"
                    )
                if detail.analysis_plan.question_version_id != detail.question_seed_id:
                    raise ValueError(
                        "PlanDraftMessage detailed plan question version must match its variant"
                    )
                if detail.analysis_plan.branch_id != self.branch_id:
                    raise ValueError("PlanDraftMessage detailed plan references another branch")
        return self


class QuestionOwnerPlanReviewMessage(PlanningMessageBase):
    message_type: Literal["question_owner_plan_review"] = "question_owner_plan_review"
    actor_role: Literal[BranchActorRole.QUESTION_OWNER] = BranchActorRole.QUESTION_OWNER
    plan_draft_message_id: str
    plan_draft_packet_id: str
    analysis_plan_id: str
    decision: PlanReviewDecisionValue
    rationale: str
    required_changes: list[str] = Field(default_factory=list)
    classified_required_changes: list[ClassifiedPlanReviewChange] = Field(default_factory=list)
    preserves_scientific_intent: bool
    material_revision_detected: bool = False
    novelty_recheck_required: bool = False
    review_complete: bool = True
    review_artifact_issues: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator(
        "plan_draft_message_id", "plan_draft_packet_id", "analysis_plan_id", "rationale"
    )
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionOwnerPlanReviewMessage fields must be non-empty")
        return value

    @field_validator("required_changes", "review_artifact_issues", "evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_owner_plan_review(self) -> QuestionOwnerPlanReviewMessage:
        if self.scope != PlanningMessageScope.FAMILY:
            raise ValueError("QuestionOwnerPlanReviewMessage must be family-scoped")
        if not self.review_complete and not self.review_artifact_issues:
            raise ValueError("incomplete owner review requires review_artifact_issues")
        if self.review_complete and self.decision == PlanReviewDecisionValue.ACCEPT:
            if not self.preserves_scientific_intent:
                raise ValueError("accepted owner plan review must preserve scientific intent")
            if not self.evidence_ids:
                raise ValueError("accepted owner plan review requires evidence_ids")
        if (
            self.review_complete
            and self.decision == PlanReviewDecisionValue.REVISE
            and not self.required_changes
        ):
            raise ValueError("revised owner plan review requires required_changes")
        if self.classified_required_changes:
            active_v3 = self.prompt_version == "question_owner/v3"
            classified_keys = [
                item.change_id if active_v3 else item.change
                for item in self.classified_required_changes
            ]
            if len(classified_keys) != len(set(classified_keys)):
                raise ValueError("owner classified_required_changes must be unique")
            if active_v3 and any(not item.change_id for item in self.classified_required_changes):
                raise ValueError("question_owner/v3 review changes require host-minted change_id")
            if (
                not active_v3
                and self.review_complete
                and {item.change for item in self.classified_required_changes}
                != set(self.required_changes)
            ):
                raise ValueError(
                    "owner classified_required_changes must cover exactly required_changes"
                )
            blockers = [
                item
                for item in self.classified_required_changes
                if item.classification == PlanReviewChangeClass.SCIENTIFIC_BLOCKER
            ]
            if (
                self.review_complete
                and self.decision == PlanReviewDecisionValue.REVISE
                and not blockers
            ):
                raise ValueError("owner revise requires at least one scientific_blocker")
            if (
                self.review_complete
                and self.decision == PlanReviewDecisionValue.ACCEPT
                and blockers
            ):
                raise ValueError("owner accept cannot retain a scientific_blocker")
        if self.material_revision_detected and not self.novelty_recheck_required:
            raise ValueError("material owner plan revision requires novelty_recheck_required")
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "QuestionOwnerPlanReviewMessage",
        )
        return self


class IndependentPlanReviewMessage(PlanningMessageBase):
    message_type: Literal["independent_plan_review"] = "independent_plan_review"
    actor_role: Literal[BranchActorRole.INDEPENDENT_REVIEWER] = BranchActorRole.INDEPENDENT_REVIEWER
    plan_draft_message_id: str
    plan_draft_packet_id: str
    owner_plan_review_message_id: str
    analysis_plan_id: str
    decision: PlanReviewDecisionValue
    rationale: str
    required_changes: list[str] = Field(default_factory=list)
    classified_required_changes: list[ClassifiedPlanReviewChange] = Field(default_factory=list)
    rejection_reason: BranchDecisionKind | None = None
    criterion_assessments: list[PlanReviewCriterionAssessment]
    owner_change_assessments: list[ClassifiedPlanReviewChange] = Field(default_factory=list)
    material_revision_detected: bool = False
    novelty_recheck_required: bool = False
    review_complete: bool = True
    review_artifact_issues: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator(
        "plan_draft_message_id",
        "plan_draft_packet_id",
        "owner_plan_review_message_id",
        "analysis_plan_id",
        "rationale",
    )
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("IndependentPlanReviewMessage fields must be non-empty")
        return value

    @field_validator("required_changes", "review_artifact_issues", "evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_independent_plan_review(self) -> IndependentPlanReviewMessage:
        if self.scope != PlanningMessageScope.FAMILY:
            raise ValueError("IndependentPlanReviewMessage must be family-scoped")
        if not self.review_complete and not self.review_artifact_issues:
            raise ValueError("incomplete independent review requires review_artifact_issues")
        if self.review_complete and not self.criterion_assessments:
            raise ValueError("IndependentPlanReviewMessage requires criterion assessments")
        if self.review_complete and self.decision == PlanReviewDecisionValue.ACCEPT:
            if not self.evidence_ids:
                raise ValueError("accepted independent plan review requires evidence_ids")
            failed = [
                item.criterion
                for item in self.criterion_assessments
                if item.status == PlanReviewCriterionStatus.FAIL
            ]
            if failed:
                raise ValueError(
                    "accepted independent plan review cannot contain failed criteria: "
                    + ", ".join(failed)
                )
        if (
            self.review_complete
            and self.decision == PlanReviewDecisionValue.REVISE
            and not self.required_changes
        ):
            raise ValueError("revised independent plan review requires required_changes")
        if (
            self.review_complete
            and self.decision == PlanReviewDecisionValue.REJECT
            and (self.rejection_reason is None or not self.rejection_reason.is_rejection)
        ):
            raise ValueError("rejected independent plan review requires rejection_reason")
        if self.classified_required_changes:
            active_v3 = self.prompt_version in {
                "plan_fidelity_reviewer/v3",
                "plan_fidelity_reviewer/v4",
            }
            classified_keys = [
                item.change_id if active_v3 else item.change
                for item in self.classified_required_changes
            ]
            if len(classified_keys) != len(set(classified_keys)):
                raise ValueError("independent classified_required_changes must be unique")
            if active_v3 and any(not item.change_id for item in self.classified_required_changes):
                raise ValueError("v3 independent review changes require host-minted change_id")
            blockers = [
                item
                for item in self.classified_required_changes
                if item.classification == PlanReviewChangeClass.SCIENTIFIC_BLOCKER
            ]
            if (
                self.review_complete
                and self.decision == PlanReviewDecisionValue.REVISE
                and not blockers
            ):
                raise ValueError("independent revise requires at least one scientific_blocker")
            if (
                self.review_complete
                and self.decision == PlanReviewDecisionValue.ACCEPT
                and blockers
            ):
                raise ValueError("independent accept cannot retain a scientific_blocker")
        if self.material_revision_detected and not self.novelty_recheck_required:
            raise ValueError("material independent plan revision requires novelty_recheck_required")
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "IndependentPlanReviewMessage",
        )
        return self


class PlanRevisionContext(BaseModel):
    """Generic, dataset-agnostic revision context threaded into a bounded re-plan handoff.

    When the automated bounded revise-loop gets a non-material ``revise`` from the owner
    or the independent reviewer, it re-spawns the dataset planner with this context so the planner
    can produce a revised plan draft that ADDRESSES the union of both reviewers' ``required_changes``
    while preserving scientific intent. It is not a ``PlanningMessage``; it rides in the planner
    task packet. Carries no dataset-specific names.
    """

    model_config = ConfigDict(extra="forbid")

    revision_round: int = Field(ge=1)
    prior_plan_draft_message_id: str
    prior_analysis_plan_id: str
    owner_plan_review_message_id: str
    independent_plan_review_message_id: str
    required_changes: list[str]
    required_change_issues: list[ClassifiedPlanReviewChange] = Field(default_factory=list)
    prior_evidence_ids: list[str] = Field(default_factory=list)
    preserves_scientific_intent: bool
    novelty_recheck_required: bool = False

    @field_validator(
        "prior_plan_draft_message_id",
        "prior_analysis_plan_id",
        "owner_plan_review_message_id",
        "independent_plan_review_message_id",
    )
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PlanRevisionContext id fields must be non-empty")
        return value

    @field_validator("required_changes", "prior_evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_revision_context(self) -> PlanRevisionContext:
        if not self.required_changes:
            raise ValueError("PlanRevisionContext requires at least one required change to address")
        if self.required_change_issues:
            change_ids = [item.change_id for item in self.required_change_issues]
            if any(not change_id for change_id in change_ids):
                raise ValueError("revision-context issues require change_id")
            if len(change_ids) != len(set(change_ids)):
                raise ValueError("revision-context change_id values must be unique")
            if any(
                item.classification != PlanReviewChangeClass.SCIENTIFIC_BLOCKER
                for item in self.required_change_issues
            ):
                raise ValueError("only scientific blockers may enter a planner revision context")
        return self


class PlannerFollowupScopeMessage(PlanningMessageBase):
    message_type: Literal["planner_followup_scope"] = "planner_followup_scope"
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    scope_packet_id: str
    source_message_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    next_step: str
    summary: str
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator("scope_packet_id", "next_step", "summary")
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PlannerFollowupScopeMessage fields must be non-empty")
        return value

    @field_validator("source_message_ids", "evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_outcomes(self) -> PlannerFollowupScopeMessage:
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "PlannerFollowupScopeMessage",
        )
        return self


class StructuralAvailabilityProbeResultMessage(PlanningMessageBase):
    message_type: Literal["structural_availability_probe_result"] = (
        "structural_availability_probe_result"
    )
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    structural_packet_id: str
    source_message_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    outcome: str
    summary: str
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator("structural_packet_id", "outcome", "summary")
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("StructuralAvailabilityProbeResultMessage fields must be non-empty")
        return value

    @field_validator("source_message_ids", "evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_outcomes(self) -> StructuralAvailabilityProbeResultMessage:
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "StructuralAvailabilityProbeResultMessage",
        )
        return self


class FullLocalDataPolicyMessage(PlanningMessageBase):
    message_type: Literal["full_local_data_policy_authorized"] = "full_local_data_policy_authorized"
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    policy_packet_id: str
    source_message_ids: list[str] = Field(default_factory=list)
    source_evidence_ids: list[str] = Field(default_factory=list)
    b9_reclassification: str
    summary: str
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator("policy_packet_id", "b9_reclassification", "summary")
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FullLocalDataPolicyMessage fields must be non-empty")
        return value

    @field_validator("source_message_ids", "source_evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_outcomes(self) -> FullLocalDataPolicyMessage:
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "FullLocalDataPolicyMessage",
        )
        return self


class FullLocalStructuralProbeResultMessage(PlanningMessageBase):
    message_type: Literal["full_local_structural_probe_result"] = (
        "full_local_structural_probe_result"
    )
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    full_local_structural_packet_id: str
    source_message_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    outcome: str
    summary: str
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator("full_local_structural_packet_id", "outcome", "summary")
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FullLocalStructuralProbeResultMessage fields must be non-empty")
        return value

    @field_validator("source_message_ids", "evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_outcomes(self) -> FullLocalStructuralProbeResultMessage:
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "FullLocalStructuralProbeResultMessage",
        )
        return self


class FamilyOperationalizationProposalMessage(PlanningMessageBase):
    message_type: Literal["family_operationalization_proposal"] = (
        "family_operationalization_proposal"
    )
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    proposal_packet_id: str
    source_message_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    scientific_construct: str
    proposed_operationalization: str
    owner_decision_needed: str
    summary: str
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator(
        "proposal_packet_id",
        "scientific_construct",
        "proposed_operationalization",
        "owner_decision_needed",
        "summary",
    )
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FamilyOperationalizationProposalMessage fields must be non-empty")
        return value

    @field_validator("source_message_ids", "evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_outcomes(self) -> FamilyOperationalizationProposalMessage:
        if self.scope != PlanningMessageScope.FAMILY:
            raise ValueError("FamilyOperationalizationProposalMessage must be family-scoped")
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "FamilyOperationalizationProposalMessage",
        )
        return self


class FamilyOperationalizationDecisionMessage(PlanningMessageBase):
    message_type: Literal["family_operationalization_decision"] = (
        "family_operationalization_decision"
    )
    actor_role: Literal[BranchActorRole.QUESTION_OWNER] = BranchActorRole.QUESTION_OWNER
    proposal_message_id: str
    proposal_packet_id: str
    decision: OperationalizationDecisionValue
    rationale: str
    required_changes: list[str] = Field(default_factory=list)
    preserves_scientific_intent: bool
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator("proposal_message_id", "proposal_packet_id", "rationale")
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FamilyOperationalizationDecisionMessage fields must be non-empty")
        return value

    @field_validator("required_changes")
    @classmethod
    def clean_required_changes(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_decision(self) -> FamilyOperationalizationDecisionMessage:
        if self.scope != PlanningMessageScope.FAMILY:
            raise ValueError("FamilyOperationalizationDecisionMessage must be family-scoped")
        if self.decision == OperationalizationDecisionValue.ACCEPT and not (
            self.preserves_scientific_intent
        ):
            raise ValueError("accepted family operationalization must preserve scientific intent")
        if self.decision == OperationalizationDecisionValue.REVISE and not self.required_changes:
            raise ValueError("revised family operationalization requires required_changes")
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "FamilyOperationalizationDecisionMessage",
        )
        return self


class FamilyOperationalizationRevisionProposalMessage(PlanningMessageBase):
    message_type: Literal["family_operationalization_revision_proposal"] = (
        "family_operationalization_revision_proposal"
    )
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    revision_proposal_packet_id: str
    source_message_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    scientific_construct: str
    revised_operationalization: str
    owner_decision_needed: str
    owner_required_changes_addressed: list[str] = Field(default_factory=list)
    summary: str
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator(
        "revision_proposal_packet_id",
        "scientific_construct",
        "revised_operationalization",
        "owner_decision_needed",
        "summary",
    )
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(
                "FamilyOperationalizationRevisionProposalMessage fields must be non-empty"
            )
        return value

    @field_validator("source_message_ids", "evidence_ids", "owner_required_changes_addressed")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_outcomes(self) -> FamilyOperationalizationRevisionProposalMessage:
        if self.scope != PlanningMessageScope.FAMILY:
            raise ValueError(
                "FamilyOperationalizationRevisionProposalMessage must be family-scoped"
            )
        if not self.owner_required_changes_addressed:
            raise ValueError(
                "FamilyOperationalizationRevisionProposalMessage requires "
                "owner_required_changes_addressed"
            )
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "FamilyOperationalizationRevisionProposalMessage",
        )
        return self


class FamilyMethodSpecificationProposalMessage(PlanningMessageBase):
    message_type: Literal["family_method_specification_proposal"] = (
        "family_method_specification_proposal"
    )
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    method_specification_packet_id: str
    source_packet_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    method_gaps_closed: list[str] = Field(default_factory=list)
    owner_decision_needed: str
    summary: str
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator("method_specification_packet_id", "owner_decision_needed", "summary")
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FamilyMethodSpecificationProposalMessage fields must be non-empty")
        return value

    @field_validator("source_packet_ids", "evidence_ids", "method_gaps_closed")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_method_specification(self) -> FamilyMethodSpecificationProposalMessage:
        if self.scope != PlanningMessageScope.FAMILY:
            raise ValueError("FamilyMethodSpecificationProposalMessage must be family-scoped")
        required_lists = {
            "source_packet_ids": self.source_packet_ids,
            "evidence_ids": self.evidence_ids,
            "method_gaps_closed": self.method_gaps_closed,
        }
        missing = [name for name, values in required_lists.items() if not values]
        if missing:
            raise ValueError(
                "FamilyMethodSpecificationProposalMessage requires non-empty lists: "
                + ", ".join(missing)
            )
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "FamilyMethodSpecificationProposalMessage",
        )
        return self


class FamilyMethodSpecificationDecisionMessage(PlanningMessageBase):
    message_type: Literal["family_method_specification_decision"] = (
        "family_method_specification_decision"
    )
    actor_role: Literal[BranchActorRole.QUESTION_OWNER] = BranchActorRole.QUESTION_OWNER
    method_specification_message_id: str
    method_specification_packet_id: str
    decision: OperationalizationDecisionValue
    preserves_scientific_intent: bool
    method_specification_sufficient: bool
    rationale: str
    required_changes: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator(
        "method_specification_message_id",
        "method_specification_packet_id",
        "rationale",
    )
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FamilyMethodSpecificationDecisionMessage fields must be non-empty")
        return value

    @field_validator("required_changes", "evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_method_specification_decision(
        self,
    ) -> FamilyMethodSpecificationDecisionMessage:
        if self.scope != PlanningMessageScope.FAMILY:
            raise ValueError("FamilyMethodSpecificationDecisionMessage must be family-scoped")
        if not self.evidence_ids:
            raise ValueError("FamilyMethodSpecificationDecisionMessage requires evidence_ids")
        if self.decision == OperationalizationDecisionValue.ACCEPT:
            if not self.preserves_scientific_intent:
                raise ValueError("method-spec acceptance must preserve scientific intent")
            if not self.method_specification_sufficient:
                raise ValueError("method-spec acceptance requires sufficient method specification")
            if self.required_changes:
                raise ValueError("method-spec acceptance cannot carry required_changes")
        if self.decision == OperationalizationDecisionValue.REVISE and not self.required_changes:
            raise ValueError("method-spec revision requires required_changes")
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "FamilyMethodSpecificationDecisionMessage",
        )
        return self


class FamilyMethodSpecificationRevisionProposalMessage(PlanningMessageBase):
    message_type: Literal["family_method_specification_revision_proposal"] = (
        "family_method_specification_revision_proposal"
    )
    actor_role: Literal[BranchActorRole.DATASET_PLANNER] = BranchActorRole.DATASET_PLANNER
    method_specification_revision_packet_id: str
    source_owner_review_packet_id: str
    source_method_specification_packet_id: str
    owner_required_changes_addressed: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    owner_decision_needed: str
    summary: str
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator(
        "method_specification_revision_packet_id",
        "source_owner_review_packet_id",
        "source_method_specification_packet_id",
        "owner_decision_needed",
        "summary",
    )
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(
                "FamilyMethodSpecificationRevisionProposalMessage fields must be non-empty"
            )
        return value

    @field_validator("owner_required_changes_addressed", "evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_method_specification_revision(
        self,
    ) -> FamilyMethodSpecificationRevisionProposalMessage:
        if self.scope != PlanningMessageScope.FAMILY:
            raise ValueError(
                "FamilyMethodSpecificationRevisionProposalMessage must be family-scoped"
            )
        required_lists = {
            "owner_required_changes_addressed": self.owner_required_changes_addressed,
            "evidence_ids": self.evidence_ids,
        }
        missing = [name for name, values in required_lists.items() if not values]
        if missing:
            raise ValueError(
                "FamilyMethodSpecificationRevisionProposalMessage requires non-empty lists: "
                + ", ".join(missing)
            )
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "FamilyMethodSpecificationRevisionProposalMessage",
        )
        return self


class FamilyMethodSpecificationRevisionDecisionMessage(PlanningMessageBase):
    message_type: Literal["family_method_specification_revision_decision"] = (
        "family_method_specification_revision_decision"
    )
    actor_role: Literal[BranchActorRole.QUESTION_OWNER] = BranchActorRole.QUESTION_OWNER
    method_specification_revision_message_id: str
    method_specification_revision_packet_id: str
    source_owner_review_packet_id: str
    decision: OperationalizationDecisionValue
    preserves_scientific_intent: bool
    method_specification_sufficient: bool
    rationale: str
    required_changes: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @field_validator(
        "method_specification_revision_message_id",
        "method_specification_revision_packet_id",
        "source_owner_review_packet_id",
        "rationale",
    )
    @classmethod
    def require_text_fields(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(
                "FamilyMethodSpecificationRevisionDecisionMessage fields must be non-empty"
            )
        return value

    @field_validator("required_changes", "evidence_ids")
    @classmethod
    def clean_id_lists(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_family_method_specification_revision_decision(
        self,
    ) -> FamilyMethodSpecificationRevisionDecisionMessage:
        if self.scope != PlanningMessageScope.FAMILY:
            raise ValueError(
                "FamilyMethodSpecificationRevisionDecisionMessage must be family-scoped"
            )
        if not self.evidence_ids:
            raise ValueError(
                "FamilyMethodSpecificationRevisionDecisionMessage requires evidence_ids"
            )
        if self.decision == OperationalizationDecisionValue.ACCEPT:
            if not self.preserves_scientific_intent:
                raise ValueError("method-spec revision acceptance must preserve scientific intent")
            if not self.method_specification_sufficient:
                raise ValueError(
                    "method-spec revision acceptance requires sufficient method specification"
                )
            if self.required_changes:
                raise ValueError("method-spec revision acceptance cannot carry required_changes")
        if self.decision == OperationalizationDecisionValue.REVISE and not self.required_changes:
            raise ValueError("method-spec revision review requires required_changes")
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "FamilyMethodSpecificationRevisionDecisionMessage",
        )
        return self


class QuestionRevisionMessage(PlanningMessageBase):
    message_type: Literal["question_revision"] = "question_revision"
    revision_id: str


class BranchRejectionMessage(PlanningMessageBase):
    message_type: Literal["branch_rejection"] = "branch_rejection"
    decision: BranchDecisionKind
    reason: str
    blocking_evidence_ids: list[str] = Field(default_factory=list)
    alternatives_for_future_data: list[str] = Field(default_factory=list)
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_rejection_decision(self) -> BranchRejectionMessage:
        if self.decision in {
            BranchDecisionKind.PENDING,
            BranchDecisionKind.ACCEPTED,
            BranchDecisionKind.ACCEPTED_REQUIRES_NEW_SKILL,
        }:
            raise ValueError("BranchRejectionMessage cannot encode pending or accepted decisions")
        if not self.decision.is_rejection and self.decision != BranchDecisionKind.HUMAN_ESCALATION:
            raise ValueError("BranchRejectionMessage requires rejection or human escalation")
        evidence_required = {
            BranchDecisionKind.REJECTED_DATASET_MISMATCH,
            BranchDecisionKind.REJECTED_OPERATIONALIZATION_FAILURE,
        }
        if self.decision in evidence_required and not self.blocking_evidence_ids:
            raise ValueError("dataset/operationalization/evidence rejection requires evidence ids")
        if not self.reason.strip():
            raise ValueError("BranchRejectionMessage requires reason")
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "BranchRejectionMessage",
        )
        return self


class HumanEscalationRequest(PlanningMessageBase):
    message_type: Literal["human_escalation_request"] = "human_escalation_request"
    decision_needed: str
    why_agents_cannot_resolve: str
    options: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_family_outcomes(self) -> HumanEscalationRequest:
        _validate_family_variant_outcomes(
            self.scope,
            self.variant_outcomes,
            "HumanEscalationRequest",
        )
        return self


def _validate_family_variant_outcomes(
    scope: PlanningMessageScope,
    outcomes: list[FamilyVariantPlanningEntry],
    model_name: str,
) -> None:
    if scope == PlanningMessageScope.FAMILY and not outcomes:
        raise ValueError(f"family-scoped {model_name} requires variant_outcomes")
    if scope == PlanningMessageScope.VARIANT and outcomes:
        raise ValueError(f"variant-scoped {model_name} cannot carry variant_outcomes")


PlanningMessage = Annotated[
    ClarificationRequest
    | ScientificClarification
    | OperationalizationProposal
    | OperationalizationDecision
    | DatasetFeasibilityFinding
    | PlanDraftMessage
    | QuestionOwnerPlanReviewMessage
    | IndependentPlanReviewMessage
    | PlannerFollowupScopeMessage
    | StructuralAvailabilityProbeResultMessage
    | FullLocalDataPolicyMessage
    | FullLocalStructuralProbeResultMessage
    | FamilyOperationalizationProposalMessage
    | FamilyOperationalizationDecisionMessage
    | FamilyOperationalizationRevisionProposalMessage
    | FamilyMethodSpecificationProposalMessage
    | FamilyMethodSpecificationDecisionMessage
    | FamilyMethodSpecificationRevisionProposalMessage
    | FamilyMethodSpecificationRevisionDecisionMessage
    | QuestionRevisionMessage
    | BranchRejectionMessage
    | HumanEscalationRequest,
    Field(discriminator="message_type"),
]
