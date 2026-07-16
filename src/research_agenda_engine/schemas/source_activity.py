from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _canonical_run_relative_path(value: str) -> str:
    """Validate one persisted artifact path without silently normalizing aliases."""

    if value != value.strip() or not value or value == "." or "\\" in value:
        raise ValueError("source activity artifact paths must be canonical run-relative paths")
    parsed = PurePosixPath(value)
    if (
        parsed.is_absolute()
        or ".." in parsed.parts
        or parsed.as_posix() != value
        or any(not part for part in parsed.parts)
    ):
        raise ValueError("source activity artifact paths must be canonical run-relative paths")
    return parsed.as_posix()


class SourceActivityStatus(StrEnum):
    PRODUCED = "produced"
    PARTIAL = "partial"
    EMPTY = "empty"
    INACTIVE = "inactive"
    FAILED = "failed"


class SourceActivityItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    status: SourceActivityStatus
    input_paths: list[str] = Field(default_factory=list)
    input_digests: dict[str, str] = Field(default_factory=dict)
    artifact_paths: list[str] = Field(default_factory=list)
    artifact_digests: dict[str, str] = Field(default_factory=dict)
    detail: str = ""

    @field_validator("source_id")
    @classmethod
    def require_source_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("source activity requires source_id")
        return value

    @field_validator("input_digests", "artifact_digests")
    @classmethod
    def require_sha256_digests(cls, value: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for path, digest in value.items():
            digest = digest.strip().lower()
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("source activity digests must be sha256 hex")
            normalized[path] = digest
        return normalized

    @model_validator(mode="after")
    def bind_paths_and_digests(self) -> SourceActivityItem:
        if len(self.input_paths) != len(set(self.input_paths)) or len(self.artifact_paths) != len(
            set(self.artifact_paths)
        ):
            raise ValueError("source activity paths must be unique")
        if set(self.input_paths) != set(self.input_digests):
            raise ValueError("source activity input paths must match input digest keys")
        if set(self.artifact_paths) != set(self.artifact_digests):
            raise ValueError("source activity artifact paths must match artifact digest keys")
        canonical_paths = [_canonical_run_relative_path(path) for path in self.artifact_paths]
        canonical_digest_paths = [
            _canonical_run_relative_path(path) for path in self.artifact_digests
        ]
        if len(canonical_paths) != len(set(canonical_paths)) or len(canonical_digest_paths) != len(
            set(canonical_digest_paths)
        ):
            raise ValueError("source activity artifact paths must be canonically unique")
        if self.status == SourceActivityStatus.INACTIVE and (
            self.input_paths or self.artifact_paths
        ):
            raise ValueError("inactive source activity cannot bind inputs or artifacts")
        if self.status == SourceActivityStatus.FAILED and self.artifact_paths:
            raise ValueError("failed source activity cannot claim artifacts")
        if self.status in {SourceActivityStatus.PRODUCED, SourceActivityStatus.PARTIAL} and not (
            self.artifact_paths
        ):
            raise ValueError("produced or partial source activity requires an artifact")
        return self


class DatasetSourceActivity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    activity_id: str
    dataset_id: str
    scope_id: str
    scope_digest: str
    sources: list[SourceActivityItem] = Field(default_factory=list)
    topic_record_count: int = Field(default=0, ge=0)
    topic_claim_supporting_count: int = Field(default=0, ge=0)
    topic_lane_coverage: dict[str, int] = Field(default_factory=dict)

    @field_validator("activity_id", "dataset_id", "scope_id")
    @classmethod
    def require_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("dataset source activity identities must be non-empty")
        return value

    @field_validator("scope_digest")
    @classmethod
    def require_scope_digest(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("dataset source activity scope_digest must be sha256")
        return value

    @field_validator("topic_lane_coverage")
    @classmethod
    def require_nonnegative_lane_counts(cls, value: dict[str, int]) -> dict[str, int]:
        if any(count < 0 for count in value.values()):
            raise ValueError("topic lane counts must be nonnegative")
        return value

    @model_validator(mode="after")
    def require_unique_sources(self) -> DatasetSourceActivity:
        source_ids = [item.source_id for item in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("dataset source activity source IDs must be unique")
        if self.topic_claim_supporting_count > self.topic_record_count:
            raise ValueError("claim-supporting topic count cannot exceed total topic count")
        topic_sources = [item for item in self.sources if item.source_id == "topic_literature"]
        if not topic_sources and (
            self.topic_record_count or self.topic_claim_supporting_count or self.topic_lane_coverage
        ):
            raise ValueError("topic accounting requires a topic_literature source activity")
        if topic_sources:
            status = topic_sources[0].status
            if status in {
                SourceActivityStatus.INACTIVE,
                SourceActivityStatus.FAILED,
                SourceActivityStatus.EMPTY,
            } and (
                self.topic_record_count
                or self.topic_claim_supporting_count
                or any(self.topic_lane_coverage.values())
            ):
                raise ValueError(
                    "nonproducing topic source cannot report records, support, or lane coverage"
                )
            if status in {SourceActivityStatus.PRODUCED, SourceActivityStatus.PARTIAL} and not (
                self.topic_record_count
            ):
                raise ValueError(
                    "produced or partial topic source requires at least one topic record"
                )
        if any(count > self.topic_record_count for count in self.topic_lane_coverage.values()):
            raise ValueError("topic lane coverage cannot exceed topic record count")
        return self
