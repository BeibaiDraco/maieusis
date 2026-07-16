from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class R5ContextEvidenceRequestKind(StrEnum):
    NEED_ABSTRACT = "need_abstract"
    NEED_FULLTEXT_EXCERPT = "need_fulltext_excerpt"
    NEED_SOURCE_DISAMBIGUATION = "need_source_disambiguation"
    NEED_MORE_SOURCES_FOR_LANE = "need_more_sources_for_lane"
    NEED_CLOSE_PRIOR_CHECK = "need_close_prior_check"
    NEED_REGION_SPECIFIC_BACKGROUND = "need_region_specific_background"
    NEED_DATASET_DETAIL_FROM_PUBLIC_DOCS = "need_dataset_detail_from_public_docs"
    REJECT_SOURCE_AS_IRRELEVANT = "reject_source_as_irrelevant"


class R5ContextEvidenceResolutionStatus(StrEnum):
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    FAILED = "failed"
    WAIVED_BY_REVIEWER = "waived_by_reviewer"


class R5ContextEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    kind: R5ContextEvidenceRequestKind
    description: str
    target_lane: str = ""
    target_source_record_id: str = ""
    target_dataset_field: str = ""
    blocking: bool = True
    requested_by: str = "maieusis_context_gate"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("request_id", "description")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("R5 context evidence request identifiers and descriptions required")
        return value


class R5ContextEvidenceResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    status: R5ContextEvidenceResolutionStatus = R5ContextEvidenceResolutionStatus.UNRESOLVED
    resolved_source_record_ids: list[str] = Field(default_factory=list)
    query_ids: list[str] = Field(default_factory=list)
    response_digests: list[str] = Field(default_factory=list)
    failure_reason: str = ""
    reviewer_waiver_reason: str = ""
    resolved_at: datetime | None = None

    @field_validator("request_id")
    @classmethod
    def require_request_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("R5 context evidence resolution requires request_id")
        return value


class R5EvidenceExpansionRound(BaseModel):
    model_config = ConfigDict(extra="forbid")

    round_id: str
    source_artifact_digest: str = ""
    requests: list[R5ContextEvidenceRequest] = Field(default_factory=list)
    resolutions: list[R5ContextEvidenceResolution] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("round_id")
    @classmethod
    def require_round_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("R5 evidence expansion round requires round_id")
        return value
