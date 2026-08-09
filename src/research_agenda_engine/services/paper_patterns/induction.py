from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...assets import resolve_asset
from ...provenance import stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas._r5_firewall import assert_proposal_safe_payload
from ...schemas.paper_case import PaperCase
from ...schemas.question_pattern import (
    QuestionPatternCard,
    QuestionPatternReviewStatus,
    QuestionPatternTransferScope,
)
from .formation_trace import FormationTraceRecord, require_usable_trace_records

QUESTION_PATTERN_INDUCER_PROMPT_VERSION = "question_pattern_inducer/v3"

# Machine-readable prefix for the max_patterns backstop, mirroring the existing
# `pattern_dropped_abstraction_or_firewall` contract. The driver keys the run diagnostic off this
# rather than off prose, because the per-pattern `review_guidance` filter selects warnings by
# pattern_id and a truncation warning names no surviving pattern.
PATTERN_TRUNCATED_AT_CAP_WARNING = "pattern_truncated_at_cap:"


class NoInduciblePatterns(Exception):
    """Every induced pattern was dropped (abstraction/firewall). An HONEST zero-patterns signal —
    the driver degrades to the zero-patterns terminal (D4), never a bare whole-batch raise."""


class QuestionPatternInductionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str = ""
    prompt_version: str = QUESTION_PATTERN_INDUCER_PROMPT_VERSION
    source_case_ids: list[str] = Field(default_factory=list)
    source_trace_ids: list[str] = Field(default_factory=list)
    patterns: list[QuestionPatternCard] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_patterns(self) -> QuestionPatternInductionBatch:
        if not self.patterns:
            raise ValueError("QuestionPatternInductionBatch requires at least one pattern")
        return self


def induce_question_patterns(
    provider: StructuredModelProvider,
    records: list[FormationTraceRecord],
    *,
    max_patterns: int = 8,
    prompt_path: Path | None = None,
) -> QuestionPatternInductionBatch:
    if not records:
        raise ValueError("Question pattern induction requires formation trace records")
    require_usable_trace_records(records)
    prompt = (prompt_path or _default_prompt_path()).read_text(encoding="utf-8")
    payload = {
        "prompt_version": QUESTION_PATTERN_INDUCER_PROMPT_VERSION,
        "max_patterns": max_patterns,
        "formation_traces": [record.model_dump(mode="json") for record in records],
    }
    batch = provider.generate_structured(
        system_prompt=prompt,
        user_prompt=json.dumps(payload, ensure_ascii=False, indent=2),
        output_model=QuestionPatternInductionBatch,
    )
    source_case_ids = [record.paper_case_id for record in records]
    source_trace_ids = [record.formation_trace.trace_id for record in records]
    patterns: list[QuestionPatternCard] = []
    warnings = list(batch.warnings)
    if len(batch.patterns) > max_patterns:
        # The cap is carried to the model as `max_patterns` in the payload and asked for in the
        # prompt ("Produce up to `max_patterns` ..."), so this slice is only the backstop for a
        # generator that overshot. It was the ONE drop in this loop that recorded nothing, while
        # every sibling below appends a warning naming what it dropped and why. A backstop that
        # cuts in model EMISSION order — which is not a ranking of scientific value — must at
        # least say so, or a future corpus loses abstractions with no trace in the run.
        warnings.append(
            f"{PATTERN_TRUNCATED_AT_CAP_WARNING} induction returned {len(batch.patterns)} patterns "
            f"against max_patterns={max_patterns}; kept the first {max_patterns} in model emission "
            f"order and dropped {len(batch.patterns) - max_patterns} unreviewed"
        )
    for pattern in batch.patterns[:max_patterns]:
        draft = QuestionPatternCard.model_validate(
            {
                **pattern.model_dump(mode="python"),
                "review_status": QuestionPatternReviewStatus.DRAFT,
            }
        )
        draft, scope_warning = _lower_single_source_transfer_scope(draft, records)
        if scope_warning:
            warnings.append(scope_warning)
        # Firewall/integrity violations remain hard. Mechanical lexical overlap is retained as
        # reviewer guidance rather than erasing a traceable scientific abstraction.
        issues = validate_pattern_abstraction(draft, records)
        if issues:
            warnings.append(
                f"pattern_dropped_abstraction_or_firewall {draft.pattern_id}: " + "; ".join(issues)
            )
            continue
        warnings.extend(pattern_abstraction_warnings(draft, records))
        warnings.extend(_missing_source_warnings(draft, source_case_ids, source_trace_ids))
        patterns.append(draft)
    if not patterns:
        # Every induced pattern was dropped. Do NOT construct an empty QuestionPatternInductionBatch
        # (the require_patterns validator forbids it) — signal the driver, which degrades to an honest
        # zero-patterns terminal (D4).
        raise NoInduciblePatterns("; ".join(warnings) or "all induced patterns were dropped")
    return QuestionPatternInductionBatch(
        batch_id=batch.batch_id
        or f"question-pattern-induction-{stable_hash(payload | {'patterns': [p.pattern_id for p in patterns]})[:12]}",
        prompt_version=QUESTION_PATTERN_INDUCER_PROMPT_VERSION,
        source_case_ids=source_case_ids,
        source_trace_ids=source_trace_ids,
        patterns=patterns,
        warnings=warnings,
    )


def _lower_single_source_transfer_scope(
    pattern: QuestionPatternCard,
    records: Sequence[FormationTraceRecord],
) -> tuple[QuestionPatternCard, str]:
    """Lower a truthful single-source draft; never fabricate cross-paper support.

    A weak generator may label an otherwise traceable one-paper abstraction ``cross_paper``. When its
    sole case/trace pair is an exact edge in the induction input and paper-specific limitations are
    already explicit, the honest deterministic repair is to lower the claim to ``paper_specific``.
    Unknown/mismatched IDs and missing limitations are untouched for the reviewer to reject.
    """
    case_ids = set(pattern.source_case_ids)
    trace_ids = set(pattern.source_trace_ids)
    known_edges = {(record.paper_case_id, record.formation_trace.trace_id) for record in records}
    if (
        pattern.transfer_scope != QuestionPatternTransferScope.CROSS_PAPER
        or len(case_ids) != 1
        or len(trace_ids) != 1
        or next(iter(case_ids)) == ""
        or next(iter(trace_ids)) == ""
        or (next(iter(case_ids)), next(iter(trace_ids))) not in known_edges
        or not pattern.non_transferable_details
    ):
        return pattern, ""
    lowered = pattern.model_copy(
        update={"transfer_scope": QuestionPatternTransferScope.PAPER_SPECIFIC}
    )
    return (
        lowered,
        f"{pattern.pattern_id}: transfer_scope lowered from cross_paper to paper_specific; "
        "the induction input contains one exact source case/trace edge",
    )


def validate_pattern_abstraction(
    pattern: QuestionPatternCard,
    source_records: Sequence[FormationTraceRecord | PaperCase],
) -> list[str]:
    issues: list[str] = []
    try:
        assert_proposal_safe_payload(
            pattern.model_dump(mode="python"), context="QuestionPatternCard"
        )
    except ValueError as exc:
        issues.append(str(exc))
    return issues


def pattern_abstraction_warnings(
    pattern: QuestionPatternCard,
    source_records: Sequence[FormationTraceRecord | PaperCase],
) -> list[str]:
    warnings: list[str] = []
    banned_texts = _source_question_texts(source_records)
    candidate_texts = [
        ("pattern_name", pattern.pattern_name),
        ("unresolved_tension_pattern", pattern.unresolved_tension_pattern),
        ("question_formation_move", pattern.question_formation_move),
    ]
    for field_name, candidate in candidate_texts:
        for source_name, source_text in banned_texts:
            if _too_similar(candidate, source_text):
                warnings.append(
                    f"{pattern.pattern_id}: advisory lexical overlap: "
                    f"{field_name} directly paraphrases {source_name}"
                )
    return warnings


def _missing_source_warnings(
    pattern: QuestionPatternCard,
    source_case_ids: list[str],
    source_trace_ids: list[str],
) -> list[str]:
    warnings: list[str] = []
    missing_cases = sorted(set(pattern.source_case_ids) - set(source_case_ids))
    missing_traces = sorted(set(pattern.source_trace_ids) - set(source_trace_ids))
    if missing_cases:
        warnings.append(
            f"{pattern.pattern_id}: source_case_ids absent from induction input: "
            + ", ".join(missing_cases)
        )
    if missing_traces:
        warnings.append(
            f"{pattern.pattern_id}: source_trace_ids absent from induction input: "
            + ", ".join(missing_traces)
        )
    return warnings


def _source_question_texts(
    source_records: Sequence[FormationTraceRecord | PaperCase],
) -> list[tuple[str, str]]:
    texts: list[tuple[str, str]] = []
    for record in source_records:
        if isinstance(record, FormationTraceRecord):
            if record.citation:
                texts.append((f"{record.paper_case_id} citation", record.citation))
            if record.original_question:
                texts.append(
                    (f"{record.paper_case_id} original question", record.original_question)
                )
            texts.append(
                (
                    f"{record.paper_case_id} trace resulting question",
                    record.formation_trace.resulting_question,
                )
            )
        else:
            if record.citation:
                texts.append((f"{record.paper_case_id} citation", record.citation))
            if record.scientific_question.original_question:
                texts.append(
                    (
                        f"{record.paper_case_id} original question",
                        record.scientific_question.original_question,
                    )
                )
            if record.formation_trace is not None:
                texts.append(
                    (
                        f"{record.paper_case_id} trace resulting question",
                        record.formation_trace.resulting_question,
                    )
                )
    return texts


def _too_similar(candidate: str, source: str) -> bool:
    candidate_tokens = _tokens(candidate)
    source_tokens = _tokens(source)
    if len(candidate_tokens) < 5 or len(source_tokens) < 5:
        return False
    overlap = len(candidate_tokens & source_tokens) / min(len(candidate_tokens), len(source_tokens))
    if overlap >= 0.85:
        return True
    candidate_norm = " ".join(candidate_tokens)
    source_norm = " ".join(source_tokens)
    return candidate_norm in source_norm or source_norm in candidate_norm


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in {"the", "and", "for", "with", "from"}
    }


def _default_prompt_path() -> Path:
    return resolve_asset(
        Path("prompts") / Path(QUESTION_PATTERN_INDUCER_PROMPT_VERSION).with_suffix(".md")
    )
