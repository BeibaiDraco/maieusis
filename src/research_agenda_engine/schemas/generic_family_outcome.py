from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .generic_scientific_source import DatasetClaimStatus, DatasetGroundingLevel
from .planning_dialogue import (
    BranchDecisionKind,
    FamilyVariantPlanningEntry,
    VariantAnalysisPlanEntry,
)
from .question_family_branch import QuestionFamilyBranch, QuestionFamilyInspectionEvidence


class GenericFamilyOutcomeKind(StrEnum):
    PLAN = "plan"
    REJECTION = "rejection"
    HUMAN_ESCALATION = "human_escalation"


_PLACEHOLDER_PHRASES = (
    "this branch-local item",
    "remains separately reviewed",
    "development planning path",
    "preserves its sibling distinction",
    "generic dossier rendering",
)


class GenericVariantScientificOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    scientific_question: str
    variant_role: str
    scientific_contrast: str
    discriminating_observation: str
    dataset_leverage_status: str
    competing_explanations: list[str] = Field(default_factory=list)
    outcome_meanings: list[str] = Field(default_factory=list)
    remaining_uncertainties: list[str] = Field(default_factory=list)

    @field_validator(
        "variant_id",
        "question_seed_id",
        "scientific_question",
        "variant_role",
        "scientific_contrast",
        "discriminating_observation",
        "dataset_leverage_status",
    )
    @classmethod
    def require_specific_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericVariantScientificOutcome fields must be non-empty")
        _reject_placeholder_text(value)
        return value

    @field_validator("competing_explanations", "outcome_meanings", "remaining_uncertainties")
    @classmethod
    def clean_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericVariantScientificOutcome list fields must be unique")
        for item in cleaned:
            _reject_placeholder_text(item)
        return cleaned

    @model_validator(mode="after")
    def validate_scientific_outcome(self) -> GenericVariantScientificOutcome:
        if len(self.competing_explanations) < 2:
            raise ValueError("GenericVariantScientificOutcome requires competing_explanations")
        if len(self.outcome_meanings) < 3:
            raise ValueError("GenericVariantScientificOutcome requires outcome_meanings")
        return self


class GenericFamilyBranchOutcomePacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome_packet_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_snapshot_id: str
    source_snapshot_digest: str
    dataset_grounding_level: DatasetGroundingLevel
    dataset_claim_status: DatasetClaimStatus = DatasetClaimStatus.UNVERIFIED
    outcome_kind: GenericFamilyOutcomeKind
    decision: BranchDecisionKind
    summary: str
    family_scientific_summary: str
    source_message_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    variant_outcomes: list[FamilyVariantPlanningEntry] = Field(default_factory=list)
    variant_analysis_plans: list[VariantAnalysisPlanEntry] = Field(default_factory=list)
    variant_scientific_outcomes: list[GenericVariantScientificOutcome] = Field(default_factory=list)
    accepted_plan_draft_message_id: str = ""
    accepted_plan_draft_packet_id: str = ""
    owner_plan_review_message_id: str = ""
    independent_plan_review_message_id: str = ""
    rejection_message_id: str = ""
    escalation_message_id: str = ""
    limitations: list[str] = Field(default_factory=list)
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "outcome_packet_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_snapshot_id",
        "summary",
        "family_scientific_summary",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericFamilyBranchOutcomePacket identity fields must be non-empty")
        _reject_placeholder_text(value)
        return value

    @field_validator("source_snapshot_digest")
    @classmethod
    def validate_snapshot_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError(
                "GenericFamilyBranchOutcomePacket source_snapshot_digest must be sha256 hex"
            )
        return value

    @field_validator("source_message_ids", "evidence_ids", "limitations")
    @classmethod
    def clean_text_lists(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericFamilyBranchOutcomePacket list fields must be unique")
        return cleaned

    @field_validator("variant_outcomes")
    @classmethod
    def require_unique_variant_outcomes(
        cls, value: list[FamilyVariantPlanningEntry]
    ) -> list[FamilyVariantPlanningEntry]:
        if not value:
            raise ValueError("GenericFamilyBranchOutcomePacket requires variant_outcomes")
        variant_ids = [item.variant_id for item in value]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("GenericFamilyBranchOutcomePacket variant_outcomes must be unique")
        for item in value:
            _reject_placeholder_text(item.summary)
        return value

    @field_validator("variant_scientific_outcomes")
    @classmethod
    def require_unique_scientific_outcomes(
        cls, value: list[GenericVariantScientificOutcome]
    ) -> list[GenericVariantScientificOutcome]:
        if not value:
            raise ValueError(
                "GenericFamilyBranchOutcomePacket requires variant_scientific_outcomes"
            )
        variant_ids = [item.variant_id for item in value]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError(
                "GenericFamilyBranchOutcomePacket variant_scientific_outcomes must be unique"
            )
        return value

    @model_validator(mode="after")
    def validate_outcome_kind(self) -> GenericFamilyBranchOutcomePacket:
        planning_ids = {entry.variant_id for entry in self.variant_outcomes}
        scientific_ids = {entry.variant_id for entry in self.variant_scientific_outcomes}
        if planning_ids != scientific_ids:
            raise ValueError(
                "GenericFamilyBranchOutcomePacket scientific outcomes must cover planning variants"
            )
        detail_ids = [entry.variant_id for entry in self.variant_analysis_plans]
        if len(detail_ids) != len(set(detail_ids)):
            raise ValueError(
                "GenericFamilyBranchOutcomePacket variant analysis plans must be unique"
            )
        if self.variant_analysis_plans:
            if self.outcome_kind != GenericFamilyOutcomeKind.PLAN:
                raise ValueError("only plan outcomes may carry detailed variant analysis plans")
            outcomes = {entry.variant_id: entry for entry in self.variant_outcomes}
            accepted_ids = {
                entry.variant_id for entry in self.variant_outcomes if entry.decision.is_accepted
            }
            if set(detail_ids) != accepted_ids:
                raise ValueError(
                    "detailed variant analysis plans must cover exactly accepted variants"
                )
            for detail in self.variant_analysis_plans:
                outcome = outcomes[detail.variant_id]
                if detail.question_seed_id != outcome.question_seed_id:
                    raise ValueError(
                        "detailed variant analysis plan question-seed identity mismatch"
                    )
                if detail.analysis_plan.question_version_id != detail.question_seed_id:
                    raise ValueError("detailed variant analysis plan question version mismatch")
                if detail.analysis_plan.branch_id != self.branch_id:
                    raise ValueError("detailed variant analysis plan references another branch")
                if not set(detail.analysis_plan.evidence_ids).issubset(outcome.evidence_ids):
                    raise ValueError(
                        "detailed variant analysis plan evidence is absent from variant outcome"
                    )
        if self.decision == BranchDecisionKind.PENDING:
            raise ValueError("GenericFamilyBranchOutcomePacket cannot encode pending outcome")
        if self.outcome_kind == GenericFamilyOutcomeKind.PLAN:
            if not self.decision.is_accepted:
                raise ValueError("plan outcome requires accepted decision")
            required = {
                "accepted_plan_draft_message_id": self.accepted_plan_draft_message_id,
                "accepted_plan_draft_packet_id": self.accepted_plan_draft_packet_id,
                "owner_plan_review_message_id": self.owner_plan_review_message_id,
                "independent_plan_review_message_id": self.independent_plan_review_message_id,
            }
            missing = sorted(name for name, value in required.items() if not value.strip())
            if missing:
                raise ValueError("plan outcome requires " + ", ".join(missing))
            if self.rejection_message_id or self.escalation_message_id:
                raise ValueError("plan outcome cannot carry rejection or escalation IDs")
        elif self.outcome_kind == GenericFamilyOutcomeKind.REJECTION:
            if not self.decision.is_rejection:
                raise ValueError("rejection outcome requires rejection decision")
            if not self.rejection_message_id.strip():
                raise ValueError("rejection outcome requires rejection_message_id")
            self._reject_accepted_plan_fields("rejection")
        elif self.outcome_kind == GenericFamilyOutcomeKind.HUMAN_ESCALATION:
            if self.decision != BranchDecisionKind.HUMAN_ESCALATION:
                raise ValueError("human escalation outcome requires human_escalation decision")
            if not self.escalation_message_id.strip():
                raise ValueError("human escalation outcome requires escalation_message_id")
            self._reject_accepted_plan_fields("human escalation")
        return self

    def _reject_accepted_plan_fields(self, label: str) -> None:
        accepted_fields = {
            "accepted_plan_draft_message_id": self.accepted_plan_draft_message_id,
            "accepted_plan_draft_packet_id": self.accepted_plan_draft_packet_id,
            "owner_plan_review_message_id": self.owner_plan_review_message_id,
            "independent_plan_review_message_id": self.independent_plan_review_message_id,
        }
        populated = sorted(name for name, value in accepted_fields.items() if value.strip())
        if populated:
            raise ValueError(f"{label} outcome cannot carry accepted plan fields: {populated}")


def validate_generic_family_outcome_packet(
    branch: QuestionFamilyBranch,
    *,
    packet: GenericFamilyBranchOutcomePacket | dict[str, object],
    evidence_by_id: dict[str, QuestionFamilyInspectionEvidence],
) -> list[str]:
    errors: list[str] = []
    try:
        outcome = (
            packet
            if isinstance(packet, GenericFamilyBranchOutcomePacket)
            else GenericFamilyBranchOutcomePacket.model_validate(packet)
        )
    except ValueError as exc:
        return [str(exc)]

    _validate_identity(branch, outcome, errors=errors)
    _validate_variant_coverage(branch, outcome, errors=errors)
    _validate_evidence_support(branch, outcome, evidence_by_id, errors=errors)
    return errors


def _validate_identity(
    branch: QuestionFamilyBranch,
    outcome: GenericFamilyBranchOutcomePacket,
    *,
    errors: list[str],
) -> None:
    expected = {
        "branch_id": branch.branch_id,
        "question_family_id": branch.question_family_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
    }
    mismatched = [
        field
        for field, expected_value in expected.items()
        if getattr(outcome, field) != expected_value
    ]
    if mismatched:
        errors.append("generic family outcome references another " + ", ".join(mismatched))


def _validate_variant_coverage(
    branch: QuestionFamilyBranch,
    outcome: GenericFamilyBranchOutcomePacket,
    *,
    errors: list[str],
) -> None:
    expected = {
        invariant.variant_id: invariant.question_seed_id
        for invariant in branch.variant_intent_invariants
    }
    actual = {entry.variant_id: entry.question_seed_id for entry in outcome.variant_outcomes}
    scientific = {
        entry.variant_id: entry.question_seed_id for entry in outcome.variant_scientific_outcomes
    }
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        unexpected = sorted(set(actual) - set(expected))
        detail = []
        if missing:
            detail.append("missing: " + ", ".join(missing))
        if unexpected:
            detail.append("unexpected: " + ", ".join(unexpected))
        errors.append(
            "generic family outcome variant outcomes do not cover active variants"
            + (": " + "; ".join(detail) if detail else "")
        )
    if scientific != expected:
        missing = sorted(set(expected) - set(scientific))
        unexpected = sorted(set(scientific) - set(expected))
        detail = []
        if missing:
            detail.append("missing scientific: " + ", ".join(missing))
        if unexpected:
            detail.append("unexpected scientific: " + ", ".join(unexpected))
        errors.append(
            "generic family outcome scientific outcomes do not cover active variants"
            + (": " + "; ".join(detail) if detail else "")
        )
    if outcome.outcome_kind == GenericFamilyOutcomeKind.PLAN:
        if not any(entry.decision.is_accepted for entry in outcome.variant_outcomes):
            errors.append("plan outcome requires at least one accepted variant")
        for entry in outcome.variant_outcomes:
            if entry.decision == BranchDecisionKind.PENDING:
                errors.append(f"plan outcome has pending variant decision: {entry.variant_id}")
    for entry in outcome.variant_outcomes:
        if (
            outcome.outcome_kind == GenericFamilyOutcomeKind.REJECTION
            and not entry.decision.is_rejection
        ):
            errors.append(
                f"rejection outcome has non-rejection variant decision: {entry.variant_id}"
            )
        if (
            outcome.outcome_kind == GenericFamilyOutcomeKind.HUMAN_ESCALATION
            and entry.decision != BranchDecisionKind.HUMAN_ESCALATION
        ):
            errors.append(
                f"human escalation outcome has wrong variant decision: {entry.variant_id}"
            )


def _validate_evidence_support(
    branch: QuestionFamilyBranch,
    outcome: GenericFamilyBranchOutcomePacket,
    evidence_by_id: dict[str, QuestionFamilyInspectionEvidence],
    *,
    errors: list[str],
) -> None:
    if not outcome.evidence_ids and outcome.dataset_claim_status not in {
        DatasetClaimStatus.CONDITIONAL,
        DatasetClaimStatus.UNKNOWN,
    }:
        errors.append("outcome without evidence must label dataset claims conditional or unknown")
    if outcome.decision == BranchDecisionKind.REJECTED_DATASET_MISMATCH:
        if outcome.dataset_claim_status not in {
            DatasetClaimStatus.UNVERIFIED,
            DatasetClaimStatus.VERIFIED,
        }:
            errors.append(
                "dataset-mismatch rejection requires explicitly unverified or verified "
                "dataset claims"
            )
        if not outcome.evidence_ids:
            errors.append("dataset-mismatch rejection requires branch-scoped evidence")

    for evidence_id in outcome.evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            errors.append("generic family outcome references missing evidence: " + evidence_id)
            continue
        if evidence.branch_id != branch.branch_id:
            errors.append(
                "generic family outcome evidence references another branch: " + evidence_id
            )
        if evidence.question_family_id != branch.question_family_id:
            errors.append(
                "generic family outcome evidence references another family: " + evidence_id
            )
        if (
            outcome.dataset_claim_status == DatasetClaimStatus.VERIFIED
            and evidence.dataset_claim_status != DatasetClaimStatus.VERIFIED
        ):
            errors.append("verified dataset claim lacks host-verified evidence: " + evidence_id)

    for entry in outcome.variant_outcomes:
        evidence_required = (
            outcome.dataset_claim_status == DatasetClaimStatus.VERIFIED
            or entry.decision == BranchDecisionKind.REJECTED_DATASET_MISMATCH
        )
        if not entry.evidence_ids and evidence_required:
            errors.append("generic family outcome variant lacks evidence: " + entry.variant_id)
            continue
        for evidence_id in entry.evidence_ids:
            if evidence_id not in outcome.evidence_ids:
                errors.append(
                    "generic family outcome variant evidence is absent from the outcome ledger: "
                    + evidence_id
                )
            evidence = evidence_by_id.get(evidence_id)
            if evidence is None:
                errors.append(
                    "generic family outcome variant references missing evidence: " + evidence_id
                )
            elif not evidence.can_support_variant(entry.variant_id):
                errors.append(
                    "generic family outcome evidence cannot support variant "
                    f"{entry.variant_id}: {evidence_id}"
                )
            elif (
                outcome.dataset_claim_status == DatasetClaimStatus.VERIFIED
                and evidence.dataset_claim_status != DatasetClaimStatus.VERIFIED
            ):
                errors.append(
                    "verified variant dataset claim lacks host-verified evidence: " + evidence_id
                )


def _reject_placeholder_text(value: str) -> None:
    lower = value.lower()
    if any(phrase in lower for phrase in _PLACEHOLDER_PHRASES):
        raise ValueError("generic family outcome contains placeholder scientific content")
