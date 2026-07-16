from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .generic_scientific_source import DatasetGroundingLevel
from .multi_family_dossier import ReviewAuthority


class GenericHumanReviewOverrideDecision(StrEnum):
    ACCEPT_FOR_DOSSIER = "accept_for_dossier"
    REVISION_REQUIRED = "revision_required"
    REJECT = "reject"
    HUMAN_ESCALATION = "human_escalation"


class GenericHumanReviewOverrideCompletionStatus(StrEnum):
    COMPLETED_RECORD_CREATED = "completed_record_created"
    BLOCKED_INSUFFICIENT_GROUNDING = "blocked_insufficient_grounding"
    NON_ACCEPT_DECISION_RECORDED = "non_accept_decision_recorded"


class GenericHumanReviewOverrideTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    family_title: str
    source_authority: ReviewAuthority = ReviewAuthority.AUTOMATED
    source_dataset_grounding_level: DatasetGroundingLevel = (
        DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY
    )
    source_outcome_packet_id: str
    source_review_decision_packet_id: str
    source_outcome_packet_path: str
    source_outcome_packet_digest: str
    source_review_decision_path: str
    source_review_decision_digest: str
    source_end_user_manifest_path: str
    source_end_user_manifest_digest: str
    source_end_user_dossier_path: str
    source_end_user_dossier_digest: str
    source_end_user_artifact_path: str
    source_end_user_artifact_digest: str
    source_audit_sidecar_path: str
    source_audit_sidecar_digest: str
    human_decision: GenericHumanReviewOverrideDecision | str = ""
    reviewer_name: str = ""
    reviewer_notes: str = ""
    required_changes: list[str] = Field(default_factory=list)
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
        "template_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "family_title",
        "source_outcome_packet_id",
        "source_review_decision_packet_id",
        "source_outcome_packet_path",
        "source_review_decision_path",
        "source_end_user_manifest_path",
        "source_end_user_dossier_path",
        "source_end_user_artifact_path",
        "source_audit_sidecar_path",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("generic human review override template fields must be non-empty")
        return value

    @field_validator(
        "source_outcome_packet_digest",
        "source_review_decision_digest",
        "source_end_user_manifest_digest",
        "source_end_user_dossier_digest",
        "source_end_user_artifact_digest",
        "source_audit_sidecar_digest",
    )
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="generic human review override digest")
        return value

    @field_validator("reviewer_name", "reviewer_notes")
    @classmethod
    def strip_optional_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("required_changes")
    @classmethod
    def clean_required_changes(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_source_authority(self) -> GenericHumanReviewOverrideTemplate:
        if self.source_authority != ReviewAuthority.AUTOMATED:
            raise ValueError("generic human review override source authority must be automated")
        return self


class GenericHumanReviewOverrideImportResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    import_result_id: str
    import_result_path: str
    run_id: str
    branch_id: str
    question_family_id: str
    human_review_decision_packet_path: str
    human_review_decision_packet_digest: str
    human_review_event_recorded: bool
    human_review_event_id: str
    human_review_event_sequence: int | None = Field(default=None, ge=1)
    branch_decision: GenericHumanReviewOverrideDecision
    review_decision_value: str
    dataset_grounding_level: DatasetGroundingLevel
    completion_status: GenericHumanReviewOverrideCompletionStatus
    completion_blocker: str = ""
    completed_record_path: str = ""
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
        "import_result_id",
        "import_result_path",
        "run_id",
        "branch_id",
        "question_family_id",
        "human_review_decision_packet_path",
        "human_review_decision_packet_digest",
        "human_review_event_id",
        "review_decision_value",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("generic human review override import result fields must be non-empty")
        return value

    @field_validator("human_review_decision_packet_digest")
    @classmethod
    def validate_result_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="generic human review override result digest")
        return value


def _validate_sha256(value: str, *, field_name: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be sha256 hex")
