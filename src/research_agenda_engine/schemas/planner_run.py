from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CodingAgentRunStatus(StrEnum):
    PREPARED = "prepared"
    RETURNED = "returned"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class WorkspaceFileManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_id: str
    workspace_root: str
    file_paths: list[str] = Field(default_factory=list)
    file_digests: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("manifest_id", "workspace_root")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("WorkspaceFileManifest identity fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_workspace_paths(self) -> WorkspaceFileManifest:
        root = Path(self.workspace_root).resolve()
        for path in self.file_paths:
            _require_under_workspace(path, root, "workspace manifest file_paths")
        for path, digest in self.file_digests.items():
            if path not in self.file_paths:
                raise ValueError("workspace manifest digest keys must be listed in file_paths")
            _require_sha256(digest, "workspace manifest file_digests")
        return self


class CodingAgentRunUsage(BaseModel):
    """Token/cost usage captured from a real coding-agent spawn (optional; None for fakes).

    ``cost_usd`` is populated only when the runner's CLI reports it (e.g. Claude Code's
    ``total_cost_usd``); Codex reports tokens without a USD figure, so its ``cost_usd`` stays None.
    In-process runners (Synthetic / Manual) and ``FakePlannerHost`` leave usage None entirely.
    """

    model_config = ConfigDict(extra="forbid")

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    source: str = ""


class CodingAgentRunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_record_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    planner_adapter: str
    planner_identity: str
    prompt_version: str
    packet_path: str
    task_path: str
    handoff_digest: str
    status: CodingAgentRunStatus = CodingAgentRunStatus.RETURNED
    sandbox_permissions: str = "branch planning artifacts only"
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
    transcript_path: str = ""
    transcript_digest: str = ""
    workspace_manifest_before_digest: str = ""
    workspace_manifest_after_digest: str = ""
    source_tree_before_digest: str = ""
    source_tree_after_digest: str = ""
    source_tree_mutation_detected: bool = False
    blocked_actions_checked: list[str] = Field(default_factory=list)
    usage: CodingAgentRunUsage | None = None
    planner_model_id: str = ""
    planner_reasoning_effort: str = ""
    planner_cli_version: str = ""
    planner_budget_policy: str = ""
    planner_timeout_seconds: int | None = Field(default=None, ge=1)
    attempt_count: int = Field(default=1, ge=1)
    attempt_audit_digest: str = ""
    runner_warnings: list[str] = Field(default_factory=list)
    error: str = ""
    planning_only: Literal[True] = True
    execution_authorized: Literal[False] = False

    @field_validator(
        "run_record_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "planner_adapter",
        "planner_identity",
        "prompt_version",
        "packet_path",
        "task_path",
        "handoff_digest",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("CodingAgentRunRecord identity fields must be non-empty")
        return value

    @field_validator(
        "handoff_digest",
        "transcript_digest",
        "workspace_manifest_before_digest",
        "workspace_manifest_after_digest",
        "source_tree_before_digest",
        "source_tree_after_digest",
        "attempt_audit_digest",
    )
    @classmethod
    def validate_optional_digest(cls, value: str) -> str:
        if value:
            _require_sha256(value, "CodingAgentRunRecord digest fields")
        return value

    @field_validator(
        "planner_model_id",
        "planner_reasoning_effort",
        "planner_cli_version",
        "planner_budget_policy",
    )
    @classmethod
    def strip_optional_runtime_identity(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_planning_only_record(self) -> CodingAgentRunRecord:
        if "branch planning artifacts only" not in self.sandbox_permissions.lower():
            raise ValueError("CodingAgentRunRecord sandbox must be branch planning artifacts only")
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("CodingAgentRunRecord ended_at cannot precede started_at")
        return self


class PlannerArtifactPresentationRepair(BaseModel):
    """One lossless audit record for a bounded presentation-only host repair.

    ``raw_snapshot_path`` preserves the exact agent-written bytes.  ``canonical_digest`` binds the
    final host-canonical artifact after provenance restamping, so an importer can independently
    prove both sides of the transformation without trusting free-text repair notes.
    """

    model_config = ConfigDict(extra="forbid")

    repair_id: str
    artifact_path: str
    raw_snapshot_path: str
    raw_digest: str
    canonical_digest: str
    aliases: list[str] = Field(default_factory=list)
    changes: list[str]

    @field_validator("repair_id", "artifact_path", "raw_snapshot_path")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PlannerArtifactPresentationRepair fields must be non-empty")
        return value

    @field_validator("raw_digest", "canonical_digest")
    @classmethod
    def validate_digests(cls, value: str) -> str:
        _require_sha256(value, "PlannerArtifactPresentationRepair digest fields")
        return value

    @field_validator("changes")
    @classmethod
    def require_changes(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("PlannerArtifactPresentationRepair requires changes")
        return list(dict.fromkeys(cleaned))

    @field_validator("aliases")
    @classmethod
    def require_unique_aliases(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if value and len(cleaned) != len(value):
            raise ValueError("planner presentation repair aliases must be non-empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("planner presentation repair aliases must be unique")
        return cleaned


class PlannerArtifactRepairLedger(BaseModel):
    """Private branch-local ledger for deterministic presentation canonicalization."""

    model_config = ConfigDict(extra="forbid")

    ledger_id: str
    run_id: str
    branch_id: str
    planner_workspace: str
    records: list[PlannerArtifactPresentationRepair]
    planning_only: Literal[True] = True

    @field_validator("ledger_id", "run_id", "branch_id", "planner_workspace")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PlannerArtifactRepairLedger fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_records(self) -> PlannerArtifactRepairLedger:
        if not self.records:
            raise ValueError("PlannerArtifactRepairLedger requires records")
        root = Path(self.planner_workspace).resolve()
        repair_ids = [record.repair_id for record in self.records]
        artifact_paths = [record.artifact_path for record in self.records]
        if len(repair_ids) != len(set(repair_ids)):
            raise ValueError("PlannerArtifactRepairLedger repair IDs must be unique")
        if len(artifact_paths) != len(set(artifact_paths)):
            raise ValueError("PlannerArtifactRepairLedger artifact paths must be unique")
        for record in self.records:
            _require_under_workspace(
                record.artifact_path,
                root,
                "planner repair ledger artifact paths",
            )
            _require_under_workspace(
                record.raw_snapshot_path,
                root,
                "planner repair ledger raw snapshot paths",
            )
        return self


class PlannerReturnedArtifactBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundle_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    planner_workspace: str
    run_trace_path: str
    evidence_paths: list[str] = Field(default_factory=list)
    construct_probe_map_paths: list[str] = Field(default_factory=list)
    dialogue_paths: list[str] = Field(default_factory=list)
    plan_draft_paths: list[str] = Field(default_factory=list)
    rejection_paths: list[str] = Field(default_factory=list)
    validation_report_path: str = ""
    host_repair_notes: list[str] = Field(default_factory=list)
    presentation_repair_ledger_path: str = ""
    presentation_repair_raw_paths: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "bundle_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "planner_workspace",
        "run_trace_path",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PlannerReturnedArtifactBundle identity fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_workspace_boundaries(self) -> PlannerReturnedArtifactBundle:
        root = Path(self.planner_workspace).resolve()
        for path in self.all_paths:
            _require_under_workspace(path, root, "planner returned artifacts")
        if self.presentation_repair_raw_paths and not self.presentation_repair_ledger_path:
            raise ValueError("planner repair raw snapshots require a repair ledger")
        return self

    @property
    def artifact_paths(self) -> tuple[str, ...]:
        return (
            self.run_trace_path,
            *self.evidence_paths,
            *self.construct_probe_map_paths,
            *self.dialogue_paths,
            *self.plan_draft_paths,
            *self.rejection_paths,
            *([self.validation_report_path] if self.validation_report_path else []),
        )

    @property
    def repair_audit_paths(self) -> tuple[str, ...]:
        """Private audit files, intentionally excluded from ordinary artifact projection."""

        return (
            *(
                [self.presentation_repair_ledger_path]
                if self.presentation_repair_ledger_path
                else []
            ),
            *self.presentation_repair_raw_paths,
        )

    @property
    def all_paths(self) -> tuple[str, ...]:
        return (*self.artifact_paths, *self.repair_audit_paths)


class PlannerArtifactImportManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    import_id: str
    bundle_id: str
    run_record_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    evidence_ids: list[str] = Field(default_factory=list)
    construct_probe_map_ids: list[str] = Field(default_factory=list)
    imported_event_ids: list[str] = Field(default_factory=list)
    checked_paths: list[str] = Field(default_factory=list)
    validation_report_digest: str
    manifest_path: str
    presentation_repair_ledger_digest: str = ""
    imported_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    planning_only: Literal[True] = True
    execution_authorized: Literal[False] = False

    @field_validator(
        "import_id",
        "bundle_id",
        "run_record_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "validation_report_digest",
        "manifest_path",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PlannerArtifactImportManifest fields must be non-empty")
        return value

    @field_validator("validation_report_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _require_sha256(value, "PlannerArtifactImportManifest validation_report_digest")
        return value

    @field_validator("presentation_repair_ledger_digest")
    @classmethod
    def validate_optional_repair_digest(cls, value: str) -> str:
        if value:
            _require_sha256(value, "PlannerArtifactImportManifest repair ledger digest")
        return value


def _require_under_workspace(path: str, root: Path, label: str) -> None:
    resolved = Path(path).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"{label} must remain under planner_workspace")


def _require_sha256(value: str, label: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{label} must be lowercase sha256 hex")
