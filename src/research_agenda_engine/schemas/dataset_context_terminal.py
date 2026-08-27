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
    # Split out from NARRATIVE_REVIEW_NON_ACCEPT so an auditor can tell "the gate refused on sight"
    # from "the gate held through a bounded source-locked repair"; the second carries a persisted
    # revision history and is the only one of the two that cost extra model calls.
    NARRATIVE_REVISION_BUDGET_EXHAUSTED = "narrative_revision_budget_exhausted"
    # A HOST refusal of a redraft (a laundered limitation, moved evidence, a no-op repair), never a
    # scientific verdict -- N3's rule: a deterministic host check is not the reviewer speaking.
    NARRATIVE_REVISION_INVALID = "narrative_revision_invalid"
    TOPIC_EVIDENCE_REVIEW_REJECTED = "topic_evidence_review_rejected"
    TOPIC_EVIDENCE_INSUFFICIENT = "topic_evidence_insufficient"
    TOPIC_EVIDENCE_REVISION_BUDGET_EXHAUSTED = "topic_evidence_revision_budget_exhausted"
    # The sibling of budget exhaustion, and its exact counterpart at the paper gates
    # (`paperbank_gate.py:413`). The revise loop stops the moment a redraft hands back a
    # byte-identical artifact, because the reviewer asked for something this host has no lawful
    # repair for. That is a statement about the machinery, not about the science: no round was
    # spent, no verdict was reached on a repaired brief. The topic-evidence caller had no branch
    # for it, so it landed on the `else` and was filed as TOPIC_EVIDENCE_REVIEW_REJECTED with
    # FailureClass.SCIENTIFIC -- which made the run reusable by resume as a settled scientific end
    # and unshepherdable, over a repair nobody could make.
    TOPIC_EVIDENCE_REVISE_NO_REPAIR_AVAILABLE = "topic_evidence_revise_no_repair_available"
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
