from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .stage_receipt import FailureClass, StageStatus


class StageDFailureKind(StrEnum):
    ALL_QUALITY_DROPPED = "all_quality_dropped"
    PROMPT_BUDGET = "prompt_budget"
    PROVIDER_ACCOUNT_EXHAUSTED = "provider_account_exhausted"
    PROVIDER_AUTHENTICATION = "provider_authentication"
    PROVIDER_RATE_LIMIT = "provider_rate_limit"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_CONNECTION = "provider_connection"
    PROVIDER_SERVER_ERROR = "provider_server_error"
    PROVIDER_INVALID_RESPONSE = "provider_invalid_response"
    REVIEWER_PROVIDER_FAILURE = "reviewer_provider_failure"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    CONFIGURATION_UNAVAILABLE = "configuration_unavailable"


class StageDCandidateDisposition(StrEnum):
    RETAINED = "retained"
    QUALITY_DROPPED = "quality_dropped"


class StageDProcessedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_family_id: str
    disposition: StageDCandidateDisposition
    reason_codes: list[str] = Field(default_factory=list)

    @field_validator("question_family_id")
    @classmethod
    def require_family_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Stage-D processed candidate requires question_family_id")
        return value

    @model_validator(mode="after")
    def require_drop_reasons(self) -> StageDProcessedCandidate:
        if self.disposition == StageDCandidateDisposition.QUALITY_DROPPED and not self.reason_codes:
            raise ValueError("quality-dropped Stage-D candidate requires reason_codes")
        return self


class StageDOutcomeRecord(BaseModel):
    """Current Stage-D status; older private diagnostics remain immutable audit history."""

    model_config = ConfigDict(extra="forbid")

    outcome_id: str
    context_id: str
    context_digest: str
    stage_status: StageStatus
    failure_class: FailureClass | None = None
    failure_kind: StageDFailureKind | None = None
    processed_candidates: list[StageDProcessedCandidate] = Field(default_factory=list)
    retained_batch_path: str = ""
    retained_batch_digest: str = ""
    superseded_diagnostic_paths: list[str] = Field(default_factory=list)

    @field_validator("outcome_id", "context_id")
    @classmethod
    def require_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Stage-D outcome identity fields must be non-empty")
        return value

    @field_validator("context_digest")
    @classmethod
    def require_context_digest(cls, value: str) -> str:
        value = value.strip()
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("Stage-D outcome context_digest must be lowercase sha256")
        return value

    @field_validator("retained_batch_digest")
    @classmethod
    def require_optional_digest(cls, value: str) -> str:
        value = value.strip()
        if value and (len(value) != 64 or any(char not in "0123456789abcdef" for char in value)):
            raise ValueError("Stage-D outcome digests must be lowercase sha256")
        return value

    @field_validator("retained_batch_path")
    @classmethod
    def require_safe_retained_path(cls, value: str) -> str:
        return _safe_run_relative_path(value, optional=True)

    @field_validator("superseded_diagnostic_paths")
    @classmethod
    def require_safe_diagnostic_paths(cls, value: list[str]) -> list[str]:
        return [_safe_run_relative_path(path, optional=False) for path in value]

    @model_validator(mode="after")
    def bind_retained_batch(self) -> StageDOutcomeRecord:
        if bool(self.retained_batch_path) != bool(self.retained_batch_digest):
            raise ValueError("Stage-D retained batch path and digest must be present together")
        expected_state = _stage_d_expected_state(self.failure_kind)
        if (self.stage_status, self.failure_class) != expected_state:
            raise ValueError("Stage-D outcome status/failure_class contradicts failure_kind")
        if len(self.superseded_diagnostic_paths) != len(set(self.superseded_diagnostic_paths)):
            raise ValueError("Stage-D superseded diagnostic paths must be unique")
        processed_ids = [item.question_family_id for item in self.processed_candidates]
        if len(processed_ids) != len(set(processed_ids)):
            raise ValueError("Stage-D processed family IDs must be unique")
        if self.failure_kind is not None and self.superseded_diagnostic_paths:
            raise ValueError("only a successful Stage-D outcome may supersede prior diagnostics")
        retained = [
            item
            for item in self.processed_candidates
            if item.disposition == StageDCandidateDisposition.RETAINED
        ]
        if self.failure_kind is None and (not self.retained_batch_path or not retained):
            raise ValueError("successful Stage-D outcome requires a retained batch and lineage")
        if self.retained_batch_path and not retained:
            raise ValueError("retained Stage-D batch requires retained candidate lineage")
        if self.failure_kind == StageDFailureKind.ALL_QUALITY_DROPPED and (
            not self.processed_candidates
            or any(
                item.disposition != StageDCandidateDisposition.QUALITY_DROPPED
                for item in self.processed_candidates
            )
        ):
            raise ValueError(
                "all-quality-dropped Stage-D outcome requires complete quality-drop lineage"
            )
        if self.failure_kind == StageDFailureKind.ALL_QUALITY_DROPPED and self.retained_batch_path:
            raise ValueError("all-quality-dropped outcome cannot retain a batch")
        return self


def _safe_run_relative_path(value: str, *, optional: bool) -> str:
    value = value.strip()
    if optional and not value:
        return ""
    parsed = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or parsed.is_absolute()
        or ".." in parsed.parts
        or parsed.as_posix() != value
    ):
        raise ValueError("Stage-D artifact paths must be normalized run-relative paths")
    return value


def _stage_d_expected_state(
    failure_kind: StageDFailureKind | None,
) -> tuple[StageStatus, FailureClass | None]:
    if failure_kind is None:
        return StageStatus.COMPLETE, None
    if failure_kind == StageDFailureKind.ALL_QUALITY_DROPPED:
        return StageStatus.SCIENTIFIC_TERMINAL, FailureClass.SCIENTIFIC
    if failure_kind == StageDFailureKind.PROMPT_BUDGET:
        return StageStatus.INFRASTRUCTURE_FAILED, FailureClass.PROMPT_BUDGET
    if failure_kind == StageDFailureKind.CONFIGURATION_UNAVAILABLE:
        return StageStatus.INFRASTRUCTURE_FAILED, FailureClass.VALIDATION_FAILURE
    if failure_kind == StageDFailureKind.STRUCTURED_OUTPUT_INVALID:
        return StageStatus.INFRASTRUCTURE_FAILED, FailureClass.SCHEMA_ERROR
    if failure_kind == StageDFailureKind.PROVIDER_TIMEOUT:
        return StageStatus.EXTERNAL_CALL_UNCERTAIN, FailureClass.PROVIDER_FAILURE
    return StageStatus.INFRASTRUCTURE_FAILED, FailureClass.PROVIDER_FAILURE
