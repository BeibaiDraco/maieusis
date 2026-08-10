"""Strict, host-owned inventory for one visible Maieusis run.

The manifest is deliberately thin: it indexes existing typed products and diagnostics. It is not a
workflow database, branch event store, or scientific claim ledger. Visibility never upgrades the
authority earned by an indexed artifact.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .presentation import PresentationAddonRecord

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RunProcessingState(StrEnum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


class ProductProcessingState(StrEnum):
    PRODUCED = "produced"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    NOT_REACHED = "not_reached"
    FAILED = "failed"


class ArtifactAuthority(StrEnum):
    VERIFIED = "verified"
    AGENT_REVIEWED = "agent_reviewed"
    PROVISIONAL = "provisional"
    UNKNOWN = "unknown"


class ArtifactProjectionState(StrEnum):
    CURRENT = "current"
    STALE = "stale"


class RunStage(StrEnum):
    PAPER_HALF = "paper_half"
    DATASET_HALF = "dataset_half"
    STAGE_C = "stage_c"
    STAGE_D = "stage_d"
    FRONT_LAYOUT = "front_layout"
    BACK_HALF = "back_half"


class ArtifactKind(StrEnum):
    RESOLVED_INPUTS = "resolved_inputs"
    INGEST_MANIFEST = "ingest_manifest"
    PAPER_CASE = "paper_case"
    PAPER_CASE_VIEW = "paper_case_view"
    FORMATION_TRACE = "formation_trace"
    FORMATION_TRACE_VIEW = "formation_trace_view"
    QUESTION_PATTERN = "question_pattern"
    PATTERN_BANK = "pattern_bank"
    PATTERN_REPORT = "pattern_report"
    RESEARCH_SCOPE = "research_scope"
    RETRIEVAL_SUMMARY = "retrieval_summary"
    TOPIC_EVIDENCE = "topic_evidence"
    DATASET_NARRATIVE = "dataset_narrative"
    SOURCE_ACTIVITY = "source_activity"
    CONTEXT_PAYLOAD = "context_payload"
    QUESTION_FAMILY_BATCH = "question_family_batch"
    QUESTION_FAMILIES_VIEW = "question_families_view"
    SHORTLIST = "shortlist"
    SHORTLIST_VIEW = "shortlist_view"
    PLANNER_HANDOFF = "planner_handoff"
    PLANNER_IMPORT_MANIFEST = "planner_import_manifest"
    PLANNER_RUN_RECORD = "planner_run_record"
    INSPECTION_EVIDENCE = "inspection_evidence"
    PLANNER_VALIDATION_REPORT = "planner_validation_report"
    DIALOGUE = "dialogue"
    PLAN = "plan"
    REJECTION = "rejection"
    ESCALATION = "escalation"
    MACHINE_DOSSIER = "machine_dossier"
    PUBLIC_DOSSIER_SOURCE = "public_dossier_source"
    AUDIT_SIDECAR = "audit_sidecar"
    FAMILY_DOSSIER = "family_dossier"
    DIAGNOSTIC = "diagnostic"
    SUMMARY = "summary"


class DiagnosticClass(StrEnum):
    INPUT = "input"
    SCIENTIFIC = "scientific"
    INFRASTRUCTURE = "infrastructure"
    INTEGRITY = "integrity"
    PROGRAMMER_FAULT = "programmer_fault"


class PaperDispositionKind(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    NO_CASE = "no_case"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class FamilyShortlistDisposition(StrEnum):
    NOT_REACHED = "not_reached"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    DEFERRED = "deferred"
    # An infrastructure fault stopped this family's review — never a scientific outcome.
    RUN_INCOMPLETE = "run_incomplete"


class StageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stage: RunStage
    processing_state: ProductProcessingState = ProductProcessingState.NOT_REACHED
    receipt_path: str = ""
    diagnostic_ids: list[str] = Field(default_factory=list)

    @field_validator("receipt_path")
    @classmethod
    def validate_optional_path(cls, value: str) -> str:
        return _run_relative_path(value) if value else ""


class ArtifactRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    kind: ArtifactKind
    path: str
    sha256: str
    processing_state: ProductProcessingState
    authority: ArtifactAuthority
    projection_state: ArtifactProjectionState = ArtifactProjectionState.CURRENT
    source_context_digest: str = ""
    paper_id: str = ""
    family_id: str = ""

    @field_validator("artifact_id")
    @classmethod
    def require_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("artifact_id must be non-empty")
        return value

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        return _run_relative_path(value)

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        value = value.strip().lower()
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
        return value

    @field_validator("source_context_digest")
    @classmethod
    def validate_optional_context_digest(cls, value: str) -> str:
        value = value.strip().lower()
        if value and not _SHA256_RE.fullmatch(value):
            raise ValueError("source_context_digest must be empty or lowercase sha256")
        return value

    @model_validator(mode="after")
    def require_projection_context_identity(self) -> ArtifactRecord:
        context_bound_kinds = {
            ArtifactKind.QUESTION_FAMILY_BATCH,
            ArtifactKind.QUESTION_FAMILIES_VIEW,
            ArtifactKind.SHORTLIST,
            ArtifactKind.SHORTLIST_VIEW,
        }
        if self.kind in context_bound_kinds and not self.source_context_digest:
            raise ValueError("context-bound family projections require source_context_digest")
        if (
            self.projection_state == ArtifactProjectionState.STALE
            and not self.source_context_digest
        ):
            raise ValueError("stale projections require source_context_digest")
        return self


class PaperDisposition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_identity: str
    input_path: str = ""
    paper_id: str
    disposition: PaperDispositionKind = PaperDispositionKind.PENDING
    reason: str = ""
    paper_case_path: str = ""
    formation_trace_path: str = ""

    @field_validator("input_identity", "paper_id")
    @classmethod
    def require_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("paper disposition identities must be non-empty")
        return value

    @field_validator("paper_case_path", "formation_trace_path")
    @classmethod
    def validate_product_path(cls, value: str) -> str:
        return _run_relative_path(value) if value else ""


class FamilyDisposition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family_id: str
    title: str = ""
    shortlist: FamilyShortlistDisposition = FamilyShortlistDisposition.NOT_REACHED
    planning_state: ProductProcessingState = ProductProcessingState.NOT_REACHED
    closure_state: ProductProcessingState = ProductProcessingState.NOT_REACHED
    dossier_path: str = ""
    authority: ArtifactAuthority = ArtifactAuthority.PROVISIONAL
    reason: str = ""

    @field_validator("family_id")
    @classmethod
    def require_family_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("family_id must be non-empty")
        return value

    @field_validator("dossier_path")
    @classmethod
    def validate_dossier_path(cls, value: str) -> str:
        return _run_relative_path(value) if value else ""


class DiagnosticRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnostic_id: str
    diagnostic_class: DiagnosticClass
    code: str
    public_message: str
    internal_path: str = ""
    paper_id: str = ""
    family_id: str = ""

    @field_validator("diagnostic_id", "code", "public_message")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("diagnostic fields must be non-empty")
        return value

    @field_validator("internal_path")
    @classmethod
    def validate_internal_path(cls, value: str) -> str:
        return _run_relative_path(value) if value else ""


class RunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "maieusis_run_manifest/v1"
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    run_state: RunProcessingState = RunProcessingState.INITIALIZED
    stages: list[StageRecord] = Field(default_factory=list)
    artifacts: list[ArtifactRecord] = Field(default_factory=list)
    papers: list[PaperDisposition] = Field(default_factory=list)
    families: list[FamilyDisposition] = Field(default_factory=list)
    diagnostics: list[DiagnosticRecord] = Field(default_factory=list)
    # Presentation is a redrawable add-on, not a seventh scientific stage or indexed artifact.
    # ``None`` keeps pre-add-on manifests byte-compatible unless an explicit add-on attempt occurs.
    presentation_addon: PresentationAddonRecord | None = None
    next_action: str

    @field_validator("run_id", "next_action")
    @classmethod
    def require_core_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("run manifest identity and next action must be non-empty")
        return value

    @model_validator(mode="after")
    def unique_records(self) -> RunManifest:
        for label, values in (
            ("stage", [item.stage.value for item in self.stages]),
            ("artifact", [item.artifact_id for item in self.artifacts]),
            ("paper", [item.input_identity for item in self.papers]),
            ("family", [item.family_id for item in self.families]),
            ("diagnostic", [item.diagnostic_id for item in self.diagnostics]),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"run manifest contains duplicate {label} records")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")
        return self


def _run_relative_path(value: str) -> str:
    value = value.strip().replace("\\", "/")
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or value.startswith("./"):
        raise ValueError("manifest paths must be normalized run-relative POSIX paths")
    normalized = path.as_posix()
    if normalized != value:
        raise ValueError("manifest paths must be normalized run-relative POSIX paths")
    return normalized
