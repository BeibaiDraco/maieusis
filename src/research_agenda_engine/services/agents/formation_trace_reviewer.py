"""Independent-AI formation-trace fidelity gate.

Inverts the manual ``import-formation-trace-reviews`` path: an independent reviewer judges whether a
drafted ``QuestionFormationTrace`` faithfully reconstructs the paper's real move from literature → gap →
dataset opportunity → question, with the cited-work roles correct. Runs on the 5a-1 gate kernel
(cross-provider, structurally earned accept). Host-side evidence pre-checks re-resolve every span id,
cited-work id, and citation-context id the trace references against the accepted PaperCase + its
literature context; the model cannot assert this closure.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from ...assets import resolve_asset
from ...providers.scientific_agents import ScientificAgentProvider, ScientificAgentSession
from ...schemas.cited_literature import PaperLocalLiteratureContext
from ...schemas.gate_outcome import GateOutcome
from ...schemas.paper_case import PaperCase
from ...schemas.question_pattern import QuestionFormationTrace, QuestionFormationTraceReviewStatus
from .gate_kernel import run_structured_gate_review
from .promotion import assert_promotion_binding
from .reviewer_base import build_scientific_reviewer_provider_from_env

FORMATION_TRACE_REVIEWER_PROMPT_VERSION = "formation_trace_reviewer/v1"
FORMATION_TRACE_GATE = "formation_trace"

FORMATION_TRACE_CRITERIA: tuple[str, ...] = (
    "literature_to_gap_faithful",
    "dataset_opportunity_faithful",
    "question_move_faithful",
    "cited_roles_correct",
    "significance_and_consequence_grounded",
)


class FormationTraceTurnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    formation_trace: dict[str, Any]
    paper_case_question: dict[str, Any]
    cited_works: list[dict[str, Any]]
    review_guidance: str = ""


def load_formation_trace_reviewer_prompt(
    prompt_version: str = FORMATION_TRACE_REVIEWER_PROMPT_VERSION,
) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def build_formation_trace_reviewer_provider_from_env(
    *,
    provider: Literal["openai", "anthropic"] | None = None,
    allow_pro_model: bool = False,
    project_root: str | Path | None = None,
) -> ScientificAgentProvider:
    """Build a live independent formation-trace reviewer provider from runtime env files."""
    return build_scientific_reviewer_provider_from_env(
        system_prompt_loader=load_formation_trace_reviewer_prompt,
        credential_fallback=("anthropic", "openai"),
        unsupported_provider_label="formation trace reviewer",
        provider=provider,
        allow_pro_model=allow_pro_model,
        project_root=project_root,
    )


def _evidence_resolved(
    trace: QuestionFormationTrace,
    paper_case: PaperCase,
    literature: PaperLocalLiteratureContext,
) -> bool:
    """Host-side hard identity closure for every trace evidence locator."""
    span_ids = {span.source_span_id for span in paper_case.evidence_spans if span.source_span_id}
    cited_ids = {work.cited_work_id for work in literature.cited_works}
    context_ids = {ctx.context_id for ctx in literature.citation_contexts}

    if not set(trace.evidence_span_ids) <= span_ids:
        return False
    if not set(trace.key_cited_work_ids) <= cited_ids:
        return False
    if not {evidence.cited_work_id for evidence in trace.literature_evidence} <= cited_ids:
        return False
    for binding in trace.evidence_bindings:
        if not set(binding.source_span_ids) <= span_ids:
            return False
        if not set(binding.cited_work_ids) <= cited_ids:
            return False
        if not set(binding.citation_context_ids) <= context_ids:
            return False
    return True


def review_formation_trace(
    *,
    session: ScientificAgentSession,
    trace: QuestionFormationTrace,
    paper_case: PaperCase,
    literature: PaperLocalLiteratureContext,
    generator_provider_ids: Sequence[str],
    review_guidance: str = "",
) -> GateOutcome:
    """Run the independent formation-trace gate; returns a structurally-earned GateOutcome."""
    turn_input = FormationTraceTurnInput(
        formation_trace=trace.model_dump(mode="json"),
        paper_case_question=paper_case.scientific_question.model_dump(mode="json"),
        cited_works=[work.model_dump(mode="json") for work in literature.cited_works],
        review_guidance=review_guidance,
    )
    return run_structured_gate_review(
        session=session,
        turn_input=turn_input,
        candidate=trace,
        gate_name=FORMATION_TRACE_GATE,
        required_criteria=FORMATION_TRACE_CRITERIA,
        evidence_resolved=_evidence_resolved(trace, paper_case, literature),
        generator_provider_ids=generator_provider_ids,
    )


def promote_formation_trace_to_ai_reviewed(
    trace: QuestionFormationTrace, outcome: GateOutcome
) -> QuestionFormationTrace:
    """Stamp ``AI_REVIEWED`` on a formation-trace-accepted draft, or raise (fail closed).

    The AI promoter never writes ``EXPERT_REVIEWED`` — an AI verdict cannot masquerade as human.
    """
    assert_promotion_binding(candidate=trace, outcome=outcome, expected_gate=FORMATION_TRACE_GATE)
    promoted = trace.model_copy(deep=True)
    promoted.review_status = QuestionFormationTraceReviewStatus.AI_REVIEWED
    return promoted
