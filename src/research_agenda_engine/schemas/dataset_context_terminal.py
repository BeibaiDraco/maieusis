"""Finite persisted causes for shared dataset-context stage terminals."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .gate_outcome import GateDecision
from .stage_receipt import FailureClass


class DatasetContextTerminalKind(StrEnum):
    NARRATIVE_REVIEW_NON_ACCEPT = "narrative_review_non_accept"
    TOPIC_EVIDENCE_REVIEW_REJECTED = "topic_evidence_review_rejected"
    TOPIC_EVIDENCE_INSUFFICIENT = "topic_evidence_insufficient"
    TOPIC_EVIDENCE_REVISION_BUDGET_EXHAUSTED = "topic_evidence_revision_budget_exhausted"
    TOPIC_EVIDENCE_REVISION_INVALID = "topic_evidence_revision_invalid"
    TOPIC_EVIDENCE_INQUIRY_INVALID = "topic_evidence_inquiry_invalid"
    TOPIC_EVIDENCE_HUMAN_ESCALATION = "topic_evidence_human_escalation"
    TOPIC_EVIDENCE_PROVIDER_FAILURE = "topic_evidence_provider_failure"
    CONFIGURATION_UNAVAILABLE = "configuration_unavailable"
    CONTEXT_READINESS_REJECTED = "context_readiness_rejected"
    CONTEXT_VALIDATION_FAILED = "context_validation_failed"


class DatasetContextTerminalRecord(BaseModel):
    """Public-safe current cause; private gate diagnostics retain the detailed evidence."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["dataset_context_terminal/v1"] = "dataset_context_terminal/v1"
    stage: Literal["dataset_half", "stage_c"]
    kind: DatasetContextTerminalKind
    failure_class: FailureClass
    gate_decision: GateDecision
    public_reason: str
    diagnostic_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
