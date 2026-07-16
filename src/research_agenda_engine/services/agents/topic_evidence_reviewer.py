"""Independent-AI topic-evidence fidelity gate.

Inverts the topic half of ``import-context-reviews``: an independent (cross-provider) reviewer judges
whether a drafted ``TopicEvidenceBrief`` faithfully serves the resolved research scope, is source-backed,
covers the generic retrieval lanes, correctly separates close-priors from still-open gaps (never claims
"novel"), and is honest about uncertainty. Runs on the 5a-1 gate kernel (structurally earned accept).
Host-side ``evidence_resolved`` folds in the shared deterministic readiness check
(``topic_evidence_readiness.evaluate_topic_evidence_readiness`` — the SAME function the V2 compiler
uses, so an accepted brief always compiles) plus generic lane coverage; the model cannot assert this.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ...assets import resolve_asset
from ...providers.scientific_agents import ScientificAgentProvider, ScientificAgentSession
from ...schemas.gate_outcome import GateOutcome
from ...schemas.inferred_research_scope import ResolvedResearchScope
from ...schemas.scientific_context import TopicEvidenceBrief, TopicEvidenceBriefReviewStatus
from ..context.topic_evidence_readiness import evaluate_topic_evidence_readiness
from ..retrieval.generic_topic_lanes import GENERIC_REQUIRED_LANES
from .gate_diagnostics import GateDiagnostic, build_gate_diagnostic
from .gate_kernel import run_structured_gate_review
from .promotion import assert_promotion_binding
from .reviewer_base import build_scientific_reviewer_provider_from_env

TOPIC_EVIDENCE_REVIEWER_PROMPT_VERSION = "topic_evidence_reviewer/v3"
TOPIC_EVIDENCE_GATE = "topic_evidence"

TOPIC_EVIDENCE_CRITERIA: tuple[str, ...] = (
    "scope_fidelity",
    "source_quality_and_claim_support",
    "generic_lane_coverage",
    "close_prior_identified",
    "open_gaps_still_open_not_novel",
    "methods_limits_confounds",
    "field_state_complete",
    "id_closure",
    "proposal_firewall",
    "uncertainty_honest",
)


class TopicEvidenceTurnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_intent: dict[str, Any]
    resolved_scope: dict[str, Any]
    recommended_brief: dict[str, Any]
    source_record_summaries: list[dict[str, Any]]
    lane_coverage: dict[str, int]
    field_state: dict[str, Any] | None
    # The canonical criterion keys the reviewer must assess — in the INPUT data, not only the
    # system prompt, so criterion_assessments can be keyed verbatim.
    required_criteria: list[str] = Field(default_factory=list)
    review_guidance: str = ""


def load_topic_evidence_reviewer_prompt(
    prompt_version: str = TOPIC_EVIDENCE_REVIEWER_PROMPT_VERSION,
) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def build_topic_evidence_reviewer_provider_from_env(
    *,
    provider: Literal["openai", "anthropic"] | None = None,
    allow_pro_model: bool = False,
    project_root: str | Path | None = None,
) -> ScientificAgentProvider:
    """Build a live independent topic-evidence reviewer provider from runtime env files."""
    return build_scientific_reviewer_provider_from_env(
        system_prompt_loader=load_topic_evidence_reviewer_prompt,
        credential_fallback=("anthropic", "openai"),
        unsupported_provider_label="topic evidence reviewer",
        provider=provider,
        allow_pro_model=allow_pro_model,
        project_root=project_root,
    )


def _evidence_resolved(
    brief: TopicEvidenceBrief,
    *,
    source_record_ids: set[str],
    claim_supporting_record_ids: set[str],
    lane_coverage: dict[str, int],
    required_lanes: Sequence[str],
) -> bool:
    """Host-side pre-check: the shared compile-readiness AND generic lane coverage."""
    ready, _issues = evaluate_topic_evidence_readiness(
        brief,
        source_record_ids=source_record_ids,
        claim_supporting_record_ids=claim_supporting_record_ids,
    )
    lanes_ok = all(lane_coverage.get(lane, 0) > 0 for lane in required_lanes)
    return ready and lanes_ok


def review_topic_evidence(
    *,
    session: ScientificAgentSession,
    brief: TopicEvidenceBrief,
    scope: ResolvedResearchScope,
    source_record_ids: set[str],
    claim_supporting_record_ids: set[str],
    lane_coverage: dict[str, int],
    research_intent: dict[str, Any],
    source_record_summaries: Sequence[dict[str, Any]],
    generator_provider_ids: Sequence[str],
    field_state: dict[str, Any] | None = None,
    required_lanes: Sequence[str] = GENERIC_REQUIRED_LANES,
    review_guidance: str = "",
) -> GateOutcome:
    """Run the independent topic-evidence gate; returns a structurally-earned GateOutcome."""
    turn_input = TopicEvidenceTurnInput(
        research_intent=research_intent,
        resolved_scope=scope.model_dump(mode="json"),
        recommended_brief=brief.model_dump(mode="json"),
        source_record_summaries=list(source_record_summaries),
        lane_coverage=dict(lane_coverage),
        field_state=field_state,
        required_criteria=list(TOPIC_EVIDENCE_CRITERIA),
        review_guidance=review_guidance,
    )
    return run_structured_gate_review(
        session=session,
        turn_input=turn_input,
        candidate=brief,
        gate_name=TOPIC_EVIDENCE_GATE,
        required_criteria=TOPIC_EVIDENCE_CRITERIA,
        evidence_resolved=_evidence_resolved(
            brief,
            source_record_ids=source_record_ids,
            claim_supporting_record_ids=claim_supporting_record_ids,
            lane_coverage=lane_coverage,
            required_lanes=required_lanes,
        ),
        generator_provider_ids=generator_provider_ids,
    )


class TopicEvidenceGateDiagnostic(GateDiagnostic):
    """WHY the topic-evidence gate did not accept — the shared GateDiagnostic plus the topic
    gate's deterministic host-side readiness + lane coverage.

    Surface-only: this artifact never changes the gate decision or the promotion binding. The
    readiness fields are recomputed with the same pure function the gate's evidence_resolved
    pre-check folded into a boolean, so a non-accept run leaves an honest, debuggable trace
    under ``runs/<id>/diagnostics/`` instead of a bare 'fail closed' message."""

    evidence_resolved: bool
    readiness_ready: bool
    readiness_issues: list[str] = Field(default_factory=list)
    required_lanes: list[str] = Field(default_factory=list)
    failed_lanes: list[str] = Field(default_factory=list)
    lane_coverage: dict[str, int] = Field(default_factory=dict)

    def _summary_parts(self) -> list[str]:
        parts = super()._summary_parts()
        # evidence_resolved right after the decision; readiness/lanes before the rationale tail.
        parts.insert(1, f"evidence_resolved={self.evidence_resolved}")
        if self.readiness_issues:
            parts.append("readiness_issues=" + "; ".join(self.readiness_issues))
        if self.failed_lanes:
            parts.append("failed_lanes=" + ",".join(self.failed_lanes))
        return parts


def build_topic_evidence_gate_diagnostic(
    outcome: GateOutcome,
    brief: TopicEvidenceBrief,
    *,
    source_record_ids: set[str],
    claim_supporting_record_ids: set[str],
    lane_coverage: dict[str, int],
    required_lanes: Sequence[str] = GENERIC_REQUIRED_LANES,
) -> TopicEvidenceGateDiagnostic:
    """Collect why the gate did not accept. The readiness issues are recomputed with the SAME
    deterministic function on the SAME inputs ``_evidence_resolved`` used, so they are exactly
    what the boolean pre-check discarded; the reviewer side is read straight off the outcome."""
    ready, issues = evaluate_topic_evidence_readiness(
        brief,
        source_record_ids=source_record_ids,
        claim_supporting_record_ids=claim_supporting_record_ids,
    )
    base = build_gate_diagnostic(outcome, TOPIC_EVIDENCE_CRITERIA)
    return TopicEvidenceGateDiagnostic(
        **base.model_dump(mode="python"),
        evidence_resolved=outcome.evidence_resolved,
        readiness_ready=ready,
        readiness_issues=issues,
        required_lanes=list(required_lanes),
        failed_lanes=[lane for lane in required_lanes if lane_coverage.get(lane, 0) == 0],
        lane_coverage=dict(lane_coverage),
    )


def promote_topic_evidence_to_ai_reviewed(
    brief: TopicEvidenceBrief, outcome: GateOutcome
) -> TopicEvidenceBrief:
    """Stamp ``AI_REVIEWED`` on a topic-evidence-accepted brief, or raise (fail closed).

    The AI promoter never writes ``EXPERT_REVIEWED`` — an AI verdict cannot masquerade as human.
    """
    assert_promotion_binding(candidate=brief, outcome=outcome, expected_gate=TOPIC_EVIDENCE_GATE)
    promoted = brief.model_copy(deep=True)
    promoted.review_status = TopicEvidenceBriefReviewStatus.AI_REVIEWED
    promoted.reviewed_at = datetime.now(UTC)
    promoted.expert_reviewer = ""
    promoted.review_notes = (
        f"Independent-AI topic-evidence gate {TOPIC_EVIDENCE_REVIEWER_PROMPT_VERSION} "
        f"(provider {outcome.reviewer_provider_id}, model {outcome.reviewer_model_id}, "
        f"session {outcome.reviewer_session_id}) accepted; reviewer independent of the generator."
    )
    return promoted
