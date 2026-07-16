"""Bounded, source-locked revision of independently reviewed question patterns."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...assets import resolve_asset
from ...provenance import stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas.gate_outcome import GateOutcome
from ...schemas.question_pattern import QuestionPatternCard, QuestionPatternReviewStatus
from .formation_trace import FormationTraceRecord
from .induction import (
    _lower_single_source_transfer_scope,
    pattern_abstraction_warnings,
    validate_pattern_abstraction,
)

QUESTION_PATTERN_REVISER_PROMPT_VERSION = "question_pattern_reviser/v1"


class QuestionPatternRevisionError(ValueError):
    """A revisor response crossed the source lock or failed the proposal firewall."""


class PatternRevisionRound(BaseModel):
    """Typed provenance for one generator revision between two independent reviews."""

    model_config = ConfigDict(extra="forbid")

    pattern_id: str
    round_index: int = Field(ge=1)
    prompt_version: str = QUESTION_PATTERN_REVISER_PROMPT_VERSION
    candidate_digest_before: str
    reviewer_outcome: GateOutcome
    revision_input_digest: str
    generator_provider_id: str
    revised_candidate_digest: str
    warnings: list[str] = Field(default_factory=list)


class PatternRevisionHistory(BaseModel):
    """The complete bounded revise/re-review disposition for one induced pattern."""

    model_config = ConfigDict(extra="forbid")

    pattern_id: str
    rounds: list[PatternRevisionRound] = Field(default_factory=list)
    final_outcome: GateOutcome
    budget_exhausted: bool = False


def revise_question_pattern(
    provider: StructuredModelProvider,
    *,
    pattern: QuestionPatternCard,
    source_records: Sequence[FormationTraceRecord],
    review_outcome: GateOutcome,
    round_index: int,
    prompt_path: Path | None = None,
) -> tuple[QuestionPatternCard, PatternRevisionRound]:
    """Revise one draft without allowing the model to switch or invent its evidence sources."""
    if review_outcome.decision.value != "revise" or not review_outcome.required_changes:
        raise QuestionPatternRevisionError(
            "question-pattern revision requires a revise outcome with actionable required_changes"
        )
    expected_edges = [
        (case_id, trace_id)
        for case_id, trace_id in zip(pattern.source_case_ids, pattern.source_trace_ids, strict=True)
    ]
    records_by_edge = {
        (record.paper_case_id, record.formation_trace.trace_id): record for record in source_records
    }
    if set(expected_edges) != set(records_by_edge):
        raise QuestionPatternRevisionError(
            "question-pattern revision source records do not exactly match the candidate edges"
        )

    payload = {
        "prompt_version": QUESTION_PATTERN_REVISER_PROMPT_VERSION,
        "round_index": round_index,
        "question_pattern": pattern.model_dump(mode="json"),
        "review_feedback": {
            "decision": review_outcome.decision.value,
            "rationale": review_outcome.rationale,
            "criterion_assessments": [
                item.model_dump(mode="json") for item in review_outcome.criterion_assessments
            ],
            "required_changes": list(review_outcome.required_changes),
            "blocker_findings": list(review_outcome.blocker_findings),
            "hallucination_findings": list(review_outcome.hallucination_findings),
        },
        "source_records": [
            records_by_edge[edge].model_dump(mode="json") for edge in expected_edges
        ],
    }
    prompt = (
        prompt_path
        or resolve_asset(
            Path("prompts") / Path(QUESTION_PATTERN_REVISER_PROMPT_VERSION).with_suffix(".md")
        )
    ).read_text(encoding="utf-8")
    generated = provider.generate_structured(
        system_prompt=prompt,
        user_prompt=json.dumps(payload, ensure_ascii=False, indent=2),
        output_model=QuestionPatternCard,
    )
    revised = QuestionPatternCard.model_validate(
        {
            **generated.model_dump(mode="python"),
            "review_status": QuestionPatternReviewStatus.DRAFT,
        }
    )
    if revised.pattern_id != pattern.pattern_id:
        raise QuestionPatternRevisionError("question-pattern revision changed pattern_id")
    if revised.source_case_ids != pattern.source_case_ids:
        raise QuestionPatternRevisionError("question-pattern revision changed source_case_ids")
    if revised.source_trace_ids != pattern.source_trace_ids:
        raise QuestionPatternRevisionError("question-pattern revision changed source_trace_ids")

    revised, scope_warning = _lower_single_source_transfer_scope(revised, source_records)
    issues = validate_pattern_abstraction(revised, source_records)
    if issues:
        raise QuestionPatternRevisionError(
            "question-pattern revision failed abstraction/firewall validation: " + "; ".join(issues)
        )
    warnings = pattern_abstraction_warnings(revised, source_records)
    if scope_warning:
        warnings.insert(0, scope_warning)
    return revised, PatternRevisionRound(
        pattern_id=pattern.pattern_id,
        round_index=round_index,
        candidate_digest_before=stable_hash(pattern),
        reviewer_outcome=review_outcome,
        revision_input_digest=stable_hash(payload),
        generator_provider_id=provider.provider_id,
        revised_candidate_digest=stable_hash(revised),
        warnings=warnings,
    )
