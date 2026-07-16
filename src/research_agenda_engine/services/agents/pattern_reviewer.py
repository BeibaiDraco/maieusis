"""Independent-AI question-pattern fidelity gate.

Inverts the manual ``import-question-pattern-reviews`` path: an independent reviewer judges whether an
induced ``QuestionPatternCard`` is a faithful, transferable abstraction (not a restatement of one
paper's question) with complete source closure. Runs on the 5a-1 gate kernel (cross-provider,
structurally earned accept). Host-side pre-checks fold the former "unknown source id is only a warning"
gap into a HARD check: every source_case_id / source_trace_id must exist in the accepted PaperBank, and
a cross-paper pattern must rest on ≥2 distinct accepted sources. The model cannot assert this closure.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from ...assets import resolve_asset
from ...providers.scientific_agents import ScientificAgentProvider, ScientificAgentSession
from ...schemas.gate_outcome import GateOutcome
from ...schemas.question_pattern import (
    QuestionPatternCard,
    QuestionPatternReviewStatus,
    QuestionPatternTransferScope,
)
from .gate_kernel import run_structured_gate_review
from .promotion import assert_promotion_binding
from .reviewer_base import build_scientific_reviewer_provider_from_env

QUESTION_PATTERN_REVIEWER_PROMPT_VERSION = "question_pattern_reviewer/v2"
QUESTION_PATTERN_GATE = "question_pattern"

QUESTION_PATTERN_CRITERIA: tuple[str, ...] = (
    "faithful_abstraction",
    "transferable_not_paper_specific_copy",
    "no_direct_paper_question_copy",
    "source_closure_complete",
)


class QuestionPatternTurnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_pattern: dict[str, Any]
    source_paper_questions: list[dict[str, Any]]
    review_guidance: str = ""


def load_question_pattern_reviewer_prompt(
    prompt_version: str = QUESTION_PATTERN_REVIEWER_PROMPT_VERSION,
) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def build_question_pattern_reviewer_provider_from_env(
    *,
    provider: Literal["openai", "anthropic"] | None = None,
    allow_pro_model: bool = False,
    project_root: str | Path | None = None,
) -> ScientificAgentProvider:
    """Build a live independent question-pattern reviewer provider from runtime env files."""
    return build_scientific_reviewer_provider_from_env(
        system_prompt_loader=load_question_pattern_reviewer_prompt,
        credential_fallback=("anthropic", "openai"),
        unsupported_provider_label="question pattern reviewer",
        provider=provider,
        allow_pro_model=allow_pro_model,
        project_root=project_root,
    )


def _evidence_resolved(
    pattern: QuestionPatternCard,
    *,
    known_case_ids: set[str],
    known_trace_ids: set[str],
    known_trace_case_edges: set[tuple[str, str]],
) -> bool:
    """Hard source closure, including the real case↔trace pairing."""
    if len(pattern.source_case_ids) != len(pattern.source_trace_ids):
        return False
    if not set(pattern.source_case_ids) <= known_case_ids:
        return False
    if not set(pattern.source_trace_ids) <= known_trace_ids:
        return False
    if any(
        edge not in known_trace_case_edges
        for edge in zip(pattern.source_case_ids, pattern.source_trace_ids, strict=True)
    ):
        return False
    minimum = 2 if pattern.transfer_scope == QuestionPatternTransferScope.CROSS_PAPER else 1
    return (
        len(set(pattern.source_case_ids)) >= minimum
        and len(set(pattern.source_trace_ids)) >= minimum
    )


def review_question_pattern(
    *,
    session: ScientificAgentSession,
    pattern: QuestionPatternCard,
    known_case_ids: set[str],
    known_trace_ids: set[str],
    known_trace_case_edges: set[tuple[str, str]],
    source_paper_questions: Sequence[dict[str, Any]],
    generator_provider_ids: Sequence[str],
    review_guidance: str = "",
) -> GateOutcome:
    """Run the independent question-pattern gate; returns a structurally-earned GateOutcome."""
    turn_input = QuestionPatternTurnInput(
        question_pattern=pattern.model_dump(mode="json"),
        source_paper_questions=list(source_paper_questions),
        review_guidance=review_guidance,
    )
    return run_structured_gate_review(
        session=session,
        turn_input=turn_input,
        candidate=pattern,
        gate_name=QUESTION_PATTERN_GATE,
        required_criteria=QUESTION_PATTERN_CRITERIA,
        evidence_resolved=_evidence_resolved(
            pattern,
            known_case_ids=known_case_ids,
            known_trace_ids=known_trace_ids,
            known_trace_case_edges=known_trace_case_edges,
        ),
        generator_provider_ids=generator_provider_ids,
    )


def promote_pattern_to_ai_reviewed(
    pattern: QuestionPatternCard, outcome: GateOutcome
) -> QuestionPatternCard:
    """Stamp ``AI_REVIEWED`` on a pattern-accepted card, or raise (fail closed).

    The AI promoter never writes ``EXPERT_REVIEWED`` — an AI verdict cannot masquerade as human. The
    card's own traceability validator (source ids + cross-paper ≥2) re-enforces closure on construction.
    """
    assert_promotion_binding(
        candidate=pattern, outcome=outcome, expected_gate=QUESTION_PATTERN_GATE
    )
    return pattern.model_copy(
        deep=True, update={"review_status": QuestionPatternReviewStatus.AI_REVIEWED}
    )
