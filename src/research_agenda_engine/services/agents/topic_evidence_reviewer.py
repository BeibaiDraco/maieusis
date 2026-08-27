"""Independent-AI topic-evidence fidelity gate.

Inverts the topic half of ``import-context-reviews``: an independent (cross-provider) reviewer judges
whether a drafted ``TopicEvidenceBrief`` faithfully serves the resolved research scope, is source-backed,
covers the generic scientific dimensions, correctly separates close-priors from still-open gaps (never claims
"novel"), and is honest about uncertainty. Runs on the 5a-1 gate kernel (structurally earned accept).
Host-side ``evidence_resolved`` folds in the shared deterministic readiness check
(``topic_evidence_readiness.evaluate_topic_evidence_readiness`` — the SAME function the V2 compiler
uses, so an accepted brief always compiles). Semantic coverage is judged from rights-safe source content;
query lineage cannot establish it.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field

from ...assets import resolve_asset
from ...io import dump_data
from ...providers.scientific_agents import (
    ScientificAgentProvider,
    ScientificAgentSession,
    ScientificAgentSessionSnapshot,
)
from ...schemas.gate_outcome import (
    GateModelDecision,
    GateOutcome,
    GateReviewContent,
    ReviewerExecutionKind,
)
from ...schemas.inferred_research_scope import ResolvedResearchScope
from ...schemas.research_intent import ResearchIntent
from ...schemas.scientific_context import TopicEvidenceBrief, TopicEvidenceBriefReviewStatus
from ..context.topic_evidence import (
    R5TopicEvidenceSourceTable,
    TopicFieldStateDraft,
    field_state_dimension_representation_statements,
    rights_safe_source_text_and_kind,
)
from ..context.topic_evidence_readiness import (
    assess_topic_evidence_readiness,
    evaluate_topic_evidence_readiness,
    topic_evidence_readiness_statements,
)
from ..retrieval.generic_topic_lanes import GENERIC_REQUIRED_LANES
from .gate_diagnostics import GateDiagnostic, build_gate_diagnostic
from .gate_kernel import run_structured_gate_review
from .promotion import assert_promoted_status_is_holdable, assert_promotion_binding
from .reviewer_base import build_scientific_reviewer_provider_from_env

TOPIC_EVIDENCE_REVIEWER_PROMPT_VERSION = "topic_evidence_reviewer/v6"
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


class TopicEvidenceClaimBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    status: str
    claim: str


class TopicEvidenceSourceSummary(BaseModel):
    """Ephemeral, rights-safe reviewer transport; never persisted as a product artifact."""

    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    title: str
    year: int | None = None
    venue: str = ""
    publication_types: list[str] = Field(default_factory=list)
    evidence_text: str = ""
    snippet_kind: str
    can_support_claims: bool
    quality_flags: list[str] = Field(default_factory=list)
    claim_bindings: list[TopicEvidenceClaimBinding] = Field(default_factory=list)


class TopicEvidenceReviewContent(GateReviewContent):
    """Topic-specific typed scientific-absence axis returned by reviewer v5."""

    essential_evidence_absent: bool
    essential_evidence_gaps: list[str]


ReviewT = TypeVar("ReviewT", bound=BaseModel)


class TopicEvidenceTurnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_intent: ResearchIntent
    resolved_scope: ResolvedResearchScope
    recommended_brief: TopicEvidenceBrief
    source_record_summaries: list[TopicEvidenceSourceSummary]
    retrieval_lineage: dict[str, int]
    semantic_dimensions: list[str] = Field(default_factory=list)
    field_state: TopicFieldStateDraft | None
    # The canonical criterion keys the reviewer must assess — in the INPUT data, not only the
    # system prompt, so criterion_assessments can be keyed verbatim.
    required_criteria: list[str] = Field(default_factory=list)
    review_guidance: str = ""
    # The deterministic readiness observations, as STATED FACTS. They carry no verdict: a brief with
    # no typed close prior is exactly what a genuinely new area looks like AND exactly what a
    # retrieval failure looks like, and only a reader of the actual sources can tell those apart.
    host_readiness_facts: list[str] = Field(default_factory=list)


_ENGINEERING_DIAGNOSTIC_PREFIXES = (
    "field_state_dropped_unknown_source_citations:",
    "field_state_dropped_unknown_evidence_requests:",
)


def split_topic_field_state_for_scientific_review(
    field_state: TopicFieldStateDraft | None,
) -> tuple[TopicFieldStateDraft | None, list[str]]:
    """Keep model-shape correction flags in audit provenance, not scientific evidence.

    The exact field-state draft is persisted separately. The reviewer receives the same typed
    content with host-classified correction flags removed from ``source_quality_diagnostics``.
    A section that lost all valid citations remains explicitly unsupported and therefore stays in
    the scientific packet; only the facts that unknown model-owned IDs were dropped are separated.
    """

    if field_state is None:
        return None, []
    engineering = [
        diagnostic
        for diagnostic in field_state.source_quality_diagnostics
        if diagnostic.startswith(_ENGINEERING_DIAGNOSTIC_PREFIXES)
    ]
    scientific = [
        diagnostic
        for diagnostic in field_state.source_quality_diagnostics
        if not diagnostic.startswith(_ENGINEERING_DIAGNOSTIC_PREFIXES)
    ]
    return field_state.model_copy(update={"source_quality_diagnostics": scientific}), engineering


def build_topic_evidence_turn_input(
    *,
    brief: TopicEvidenceBrief,
    scope: ResolvedResearchScope,
    research_intent: dict[str, Any],
    source_record_summaries: Sequence[TopicEvidenceSourceSummary],
    retrieval_lineage: dict[str, int],
    source_record_ids: set[str],
    claim_supporting_record_ids: set[str],
    field_state: TopicFieldStateDraft | None = None,
    semantic_dimensions: Sequence[str] = GENERIC_REQUIRED_LANES,
    review_guidance: str = "",
) -> TopicEvidenceTurnInput:
    """Build the exact typed packet sent to the independent topic reviewer.

    The two id sets are REQUIRED rather than optional because the readiness facts are derived from
    them here. A caller that could build this packet without them could build one that silently
    omits the very fact the reviewer is now asked to judge.
    """

    scientific_field_state, _engineering = split_topic_field_state_for_scientific_review(
        field_state
    )
    return TopicEvidenceTurnInput(
        research_intent=ResearchIntent.model_validate(research_intent),
        resolved_scope=scope,
        recommended_brief=brief,
        source_record_summaries=list(source_record_summaries),
        retrieval_lineage=dict(retrieval_lineage),
        semantic_dimensions=list(semantic_dimensions),
        field_state=scientific_field_state,
        required_criteria=list(TOPIC_EVIDENCE_CRITERIA),
        review_guidance=review_guidance,
        host_readiness_facts=[
            *topic_evidence_readiness_statements(
                assess_topic_evidence_readiness(
                    brief,
                    source_record_ids=source_record_ids,
                    claim_supporting_record_ids=claim_supporting_record_ids,
                )
            ),
            # Derived from the SCIENTIFIC field state, the same object the reviewer is handed, so a
            # statement about a section can always be checked against the section it names.
            *field_state_dimension_representation_statements(scientific_field_state, brief),
        ],
    )


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
) -> bool:
    """Host-side pre-check for hard source/claim closure only.

    It now means what it always said. Folding the completeness axis in here made a brief that
    reported no already-answered prior work UNFAITHFUL by the gate kernel's definition
    (``gate_kernel.py``: ``unfaithful = hallucination_findings or not evidence_resolved``), so the
    only verdict such a brief could earn was a downgrade to reject -- for a fact about what the
    literature contained, not about whether the brief told the truth about it. The completeness axis
    still decides the authority ceiling upstream; it travels to the reviewer as a stated fact.
    """
    readiness = assess_topic_evidence_readiness(
        brief,
        source_record_ids=source_record_ids,
        claim_supporting_record_ids=claim_supporting_record_ids,
    )
    return readiness.evidence_closed


def build_topic_evidence_reviewer_source_summaries(
    *,
    brief: TopicEvidenceBrief,
    source_table: R5TopicEvidenceSourceTable,
    claim_supporting_record_ids: set[str],
) -> list[TopicEvidenceSourceSummary]:
    """Build the rights-safe evidence packet the independent reviewer actually judges."""

    claims_by_source: dict[str, list[TopicEvidenceClaimBinding]] = {}
    for claim in brief.claims:
        for source_id in claim.source_record_ids or claim.source_refs:
            claims_by_source.setdefault(source_id, []).append(
                TopicEvidenceClaimBinding(
                    claim_id=claim.claim_id,
                    status=claim.status.value,
                    claim=claim.claim,
                )
            )
    summaries: list[TopicEvidenceSourceSummary] = []
    for record in source_table.records:
        evidence_text, evidence_kind = rights_safe_source_text_and_kind(record)
        summaries.append(
            TopicEvidenceSourceSummary(
                source_record_id=record.source_record_id,
                title=record.title,
                year=record.year,
                venue=record.venue,
                publication_types=list(record.publication_types),
                evidence_text=evidence_text,
                snippet_kind=(evidence_kind.value if evidence_kind is not None else "unavailable"),
                can_support_claims=record.source_record_id in claim_supporting_record_ids,
                quality_flags=list(record.source_quality_flags),
                claim_bindings=claims_by_source.get(record.source_record_id, []),
            )
        )
    return summaries


def _adapt_topic_review_content(content: GateReviewContent) -> GateReviewContent:
    if not isinstance(content, TopicEvidenceReviewContent):
        raise TypeError("topic evidence review requires TopicEvidenceReviewContent")
    base = GateReviewContent(
        decision=content.decision,
        rationale=content.rationale,
        criterion_assessments=list(content.criterion_assessments),
        required_changes=list(content.required_changes),
        blocker_findings=list(content.blocker_findings),
        hallucination_findings=list(content.hallucination_findings),
    )
    gaps = [gap.strip() for gap in content.essential_evidence_gaps if gap.strip()]
    if not content.essential_evidence_absent and not gaps:
        return base
    findings = list(base.blocker_findings)
    findings.extend(
        f"essential evidence absent: {gap}"
        for gap in gaps
        if f"essential evidence absent: {gap}" not in findings
    )
    if not gaps:
        findings.append("essential evidence absent: reviewer did not name the gap")
    return base.model_copy(
        update={
            "decision": GateModelDecision.INSUFFICIENT_EVIDENCE,
            "blocker_findings": findings,
        }
    )


class _TopicEvidenceReviewSession(ScientificAgentSession):
    """Narrow output-schema adapter that leaves the shared red-line gate kernel unchanged."""

    def __init__(self, inner: ScientificAgentSession) -> None:
        self._inner = inner

    @property
    def branch_id(self) -> str:
        return self._inner.branch_id

    @property
    def session_id(self) -> str:
        return self._inner.session_id

    @property
    def provider_id(self) -> str:
        return self._inner.provider_id

    @property
    def model_id(self) -> str:
        return self._inner.model_id

    @property
    def prompt_version(self) -> str:
        return self._inner.prompt_version

    @property
    def execution_kind(self) -> ReviewerExecutionKind:
        return self._inner.execution_kind

    def send(self, payload: BaseModel, output_schema: type[ReviewT]) -> ReviewT:
        if output_schema is not GateReviewContent:
            raise TypeError("topic evidence adapter serves only GateReviewContent")
        raw = self._inner.send(payload, TopicEvidenceReviewContent)
        return cast(ReviewT, _adapt_topic_review_content(raw))

    def snapshot(self) -> ScientificAgentSessionSnapshot:
        return self._inner.snapshot()


def review_topic_evidence(
    *,
    session: ScientificAgentSession,
    brief: TopicEvidenceBrief,
    scope: ResolvedResearchScope,
    source_record_ids: set[str],
    claim_supporting_record_ids: set[str],
    retrieval_lineage: dict[str, int],
    research_intent: dict[str, Any],
    source_record_summaries: Sequence[TopicEvidenceSourceSummary],
    generator_provider_ids: Sequence[str],
    field_state: TopicFieldStateDraft | None = None,
    semantic_dimensions: Sequence[str] = GENERIC_REQUIRED_LANES,
    review_guidance: str = "",
    prepared_turn_input: TopicEvidenceTurnInput | None = None,
    turn_input_path: Path | None = None,
) -> GateOutcome:
    """Run the independent topic-evidence gate; returns a structurally-earned GateOutcome."""
    turn_input = prepared_turn_input or build_topic_evidence_turn_input(
        brief=brief,
        scope=scope,
        research_intent=research_intent,
        source_record_summaries=source_record_summaries,
        retrieval_lineage=retrieval_lineage,
        source_record_ids=source_record_ids,
        claim_supporting_record_ids=claim_supporting_record_ids,
        field_state=field_state,
        semantic_dimensions=semantic_dimensions,
        review_guidance=review_guidance,
    )
    if turn_input.recommended_brief != brief or turn_input.resolved_scope != scope:
        raise ValueError("prepared topic-review input is not bound to the supplied brief and scope")
    # A prepared packet is built by the caller, one revision round at a time. If its readiness facts
    # were computed against a different brief or a different source table, the reviewer would be
    # judging one artifact while reading a host observation about another -- and the host observation
    # is precisely what this gate now defers to instead of deciding alone.
    expected_readiness_facts = topic_evidence_readiness_statements(
        assess_topic_evidence_readiness(
            brief,
            source_record_ids=source_record_ids,
            claim_supporting_record_ids=claim_supporting_record_ids,
        )
    )
    if turn_input.host_readiness_facts != expected_readiness_facts:
        raise ValueError(
            "prepared topic-review input carries readiness facts that do not describe the "
            "supplied brief and source table"
        )
    if turn_input_path is not None:
        dump_data(turn_input, turn_input_path)
    return run_structured_gate_review(
        session=_TopicEvidenceReviewSession(session),
        turn_input=turn_input,
        candidate=brief,
        gate_name=TOPIC_EVIDENCE_GATE,
        required_criteria=TOPIC_EVIDENCE_CRITERIA,
        evidence_resolved=_evidence_resolved(
            brief,
            source_record_ids=source_record_ids,
            claim_supporting_record_ids=claim_supporting_record_ids,
        ),
        generator_provider_ids=generator_provider_ids,
    )


class TopicEvidenceGateDiagnostic(GateDiagnostic):
    """WHY the topic-evidence gate did not accept — the shared GateDiagnostic plus the topic
    gate's deterministic host-side readiness and non-authoritative retrieval lineage.

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
        # evidence_resolved right after the decision; readiness before the rationale tail.
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
    retrieval_lineage: dict[str, int],
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
        required_lanes=[],
        failed_lanes=[],
        lane_coverage=dict(retrieval_lineage),
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
    assert_promoted_status_is_holdable(promoted, expected_gate=TOPIC_EVIDENCE_GATE)
    promoted.reviewed_at = datetime.now(UTC)
    promoted.expert_reviewer = ""
    promoted.review_notes = (
        f"Independent-AI topic-evidence gate {TOPIC_EVIDENCE_REVIEWER_PROMPT_VERSION} "
        f"(provider {outcome.reviewer_provider_id}, model {outcome.reviewer_model_id}, "
        f"session {outcome.reviewer_session_id}) accepted; reviewer independent of the generator."
    )
    return promoted
