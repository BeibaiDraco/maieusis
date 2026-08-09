"""Stage-receipt + failure-class schema.

A durable, per-stage record of what a pipeline stage did: what it read, under which config/prompt/model
versions, what it wrote, which external calls it made, and — critically — HOW it ended. The status
taxonomy separates the three honest endings a stage can have (complete / scientific terminal /
infrastructure failure) so a downstream summary never has to guess, and a baked-in validator enforces
the project invariant: **infrastructure failure is NOT a scientific rejection.**

These are schemas only. The 5c-1a driver (5c-1b) emits + persists them; nothing here wires a driver.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FailureClass(StrEnum):
    """Why a stage/family failed. Exactly one class is scientific; the rest are infrastructure.

    A scientific failure means the work was judged and found wanting (a reject / unsound plan). Every
    other class means the machinery broke (provider down, sandbox denied, schema/validation error,
    prompt budget, an external call whose outcome is unknown) — the science was never actually judged.
    """

    SCIENTIFIC = "scientific"
    PROVIDER_FAILURE = "provider_failure"
    SANDBOX_FAILURE = "sandbox_failure"
    VALIDATION_FAILURE = "validation_failure"
    SCHEMA_ERROR = "schema_error"
    PROMPT_BUDGET = "prompt_budget"
    EXTERNAL_CALL_UNCERTAIN = "external_call_uncertain"


#: Every failure class except the single scientific one. A stage that stopped on any of these must not
#: be recorded as a scientific rejection.
INFRASTRUCTURE_FAILURE_CLASSES: frozenset[FailureClass] = frozenset(
    fc for fc in FailureClass if fc != FailureClass.SCIENTIFIC
)


class StageStatus(StrEnum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETE = "complete"
    # The stage ran and reached an honest scientific end (e.g. a gate reject) — this is science, not a
    # broken machine; failure_class may be None or SCIENTIFIC.
    SCIENTIFIC_TERMINAL = "scientific_terminal"
    # The machinery broke (provider/sandbox/schema/budget). failure_class must be an infrastructure one.
    INFRASTRUCTURE_FAILED = "infrastructure_failed"
    # An external call was issued but its outcome is unknown (timeout after send, ambiguous response).
    EXTERNAL_CALL_UNCERTAIN = "external_call_uncertain"


_PENDING_OR_OK = {StageStatus.NOT_STARTED, StageStatus.RUNNING, StageStatus.COMPLETE}


class StageReceipt(BaseModel):
    """One stage's durable receipt (see module docstring). ``extra='forbid'``."""

    model_config = ConfigDict(extra="forbid")

    stage_name: str
    status: StageStatus
    input_digests: dict[str, str] = Field(default_factory=dict)
    config_version: str = ""
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    model_versions: dict[str, str] = Field(default_factory=dict)
    output_paths: list[str] = Field(default_factory=list)
    output_digests: dict[str, str] = Field(default_factory=dict)
    # CLIM-10: a timestamp-free semantic digest per output artifact, parallel to the raw byte
    # output_digests. The reuse gate compares these so a re-run that changes only provenance
    # timestamps REUSES downstream; output_digests stays the exact-byte replay/corruption
    # identity. Additive default-empty: pre-CLIM-10 receipts fall back to byte digests.
    semantic_output_digests: dict[str, str] = Field(default_factory=dict)
    external_call_ids: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    failure_class: FailureClass | None = None
    detail: str = ""

    @model_validator(mode="after")
    def _failure_class_matches_status(self) -> StageReceipt:
        # infra ≠ scientific: enforce the status↔failure_class contract structurally.
        if self.status in _PENDING_OR_OK:
            if self.failure_class is not None:
                raise ValueError(
                    f"StageReceipt status {self.status.value!r} must not carry a failure_class"
                )
        elif self.status == StageStatus.SCIENTIFIC_TERMINAL:
            if self.failure_class not in (None, FailureClass.SCIENTIFIC):
                raise ValueError(
                    "a scientific_terminal stage cannot carry an infrastructure failure_class"
                )
        else:  # INFRASTRUCTURE_FAILED | EXTERNAL_CALL_UNCERTAIN
            if self.failure_class not in INFRASTRUCTURE_FAILURE_CLASSES:
                raise ValueError(
                    f"status {self.status.value!r} requires an infrastructure failure_class, "
                    "never SCIENTIFIC or None"
                )
        return self
