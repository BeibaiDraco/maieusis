"""Shared, surface-only diagnostics for the front-half quality gates.

WHY a gate did not accept, written next to the run so a non-accept leaves an honest, debuggable
trace instead of a bare 'fail closed' message. This never changes a gate decision, a kernel, or a
promotion — it reads the earned ``GateOutcome`` and records it. The topic-evidence gate has a richer
subclass (readiness + lane coverage) in ``topic_evidence_reviewer``; every other front-half gate uses
the base directly.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...io import dump_data
from ...schemas.gate_outcome import GateCriterionAuditRecord, GateDecision, GateOutcome


class GateDiagnostic(BaseModel):
    """The reviewer verdict for one artifact at one gate, recorded on the non-accept path."""

    model_config = ConfigDict(extra="forbid")

    gate_name: str
    # For per-artifact gates (paper cases, patterns, families): which artifact this is about.
    artifact_label: str = ""
    decision: GateDecision
    downgraded_from: GateDecision | None = None
    rationale: str = ""
    required_changes: list[str] = Field(default_factory=list)
    blocker_findings: list[str] = Field(default_factory=list)
    hallucination_findings: list[str] = Field(default_factory=list)
    # Against THIS gate's required-criteria list.
    failed_criteria: list[str] = Field(default_factory=list)
    missing_criteria: list[str] = Field(default_factory=list)
    # The raw criterion names the reviewer actually returned — empty vs mismatched vs partial
    # at a glance.
    returned_criteria: list[str] = Field(default_factory=list)
    criterion_audit: list[GateCriterionAuditRecord] = Field(default_factory=list)
    criterion_review_complete: bool = True
    reviewer_provider_id: str = ""
    reviewer_model_id: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def _summary_parts(self) -> list[str]:
        """The shared 'why' axes; subclasses extend this before joining."""
        parts = [f"{self.gate_name} gate diagnostics: decision={self.decision.value}"]
        if self.artifact_label:
            parts.append(f"artifact={self.artifact_label}")
        if self.downgraded_from is not None:
            parts.append(f"downgraded_from={self.downgraded_from.value}")
        if self.required_changes:
            parts.append("required_changes=" + "; ".join(self.required_changes))
        if self.failed_criteria:
            parts.append("failed_criteria=" + ",".join(self.failed_criteria))
        if self.missing_criteria:
            parts.append("missing_criteria=" + ",".join(self.missing_criteria))
        if self.blocker_findings:
            parts.append("blocker_findings=" + "; ".join(self.blocker_findings))
        if self.hallucination_findings:
            parts.append("hallucination_findings=" + "; ".join(self.hallucination_findings))
        if self.rationale:
            parts.append(f"reviewer_rationale={self.rationale}")
        return parts

    def summary_line(self) -> str:
        """One compact line for a log/error message — every non-empty 'why' axis."""
        return " | ".join(self._summary_parts())


def build_gate_diagnostic(
    outcome: GateOutcome,
    required_criteria: Sequence[str],
    *,
    artifact_label: str = "",
) -> GateDiagnostic:
    """Collect why ``outcome`` did not accept, keyed against ``required_criteria``."""
    passed_by_criterion = {a.criterion: a.passed for a in outcome.criterion_assessments}
    return GateDiagnostic(
        gate_name=outcome.gate_name,
        artifact_label=artifact_label,
        decision=outcome.decision,
        downgraded_from=outcome.downgraded_from,
        rationale=outcome.rationale,
        required_changes=list(outcome.required_changes),
        blocker_findings=list(outcome.blocker_findings),
        hallucination_findings=list(outcome.hallucination_findings),
        failed_criteria=[c for c in required_criteria if passed_by_criterion.get(c) is False],
        missing_criteria=[c for c in required_criteria if c not in passed_by_criterion],
        returned_criteria=(
            [record.raw_criterion for record in outcome.criterion_audit]
            if outcome.criterion_audit
            else [a.criterion for a in outcome.criterion_assessments]
        ),
        criterion_audit=list(outcome.criterion_audit),
        criterion_review_complete=outcome.criterion_review_complete,
        reviewer_provider_id=outcome.reviewer_provider_id,
        reviewer_model_id=outcome.reviewer_model_id,
    )


def _slug(value: str) -> str:
    """A filesystem-safe artifact label for the diagnostic filename."""
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in value.strip())
    return safe.strip("-") or "artifact"


def gate_diagnostic_path(
    diagnostics_dir: Path, *, gate_name: str, artifact_label: str = ""
) -> Path:
    """``<diagnostics_dir>/<gate>/<artifact>.yaml`` for per-artifact gates, else ``<gate>.yaml``."""
    if artifact_label:
        return diagnostics_dir / gate_name / f"{_slug(artifact_label)}.yaml"
    return diagnostics_dir / f"{gate_name}.yaml"


def write_gate_diagnostic(diagnostic: GateDiagnostic, diagnostics_dir: Path) -> Path:
    """Persist ``diagnostic`` under the run's diagnostics dir; returns the written path."""
    path = gate_diagnostic_path(
        diagnostics_dir,
        gate_name=diagnostic.gate_name,
        artifact_label=diagnostic.artifact_label,
    )
    return dump_data(diagnostic, path)
