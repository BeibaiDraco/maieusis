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
from .promotion import assert_promoted_status_is_holdable, assert_promotion_binding
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


_SELECTION_SCOPE_NOTE = (
    "`cited_works` lists only the works citation-importance selection made available to the"
    " drafter, not the paper's full reference list."
)
_NO_SELECTION_NOTE = (
    "Citation-importance selection chose no cited works for this paper, so the drafter was"
    " instructed to cite none and `cited_works` is empty by construction. This is a property of"
    " the pipeline's input, not a choice by the drafter. DO NOT return a `cited_roles_correct`"
    " assessment at all: with no citation to check, there is nothing to be right or wrong about,"
    " and the host has dropped it from the required set for this paper. Assess the remaining"
    " criteria against the evidence the trace actually carries."
)


#: The required set for a paper with no citation to judge. `cited_roles_correct` reads "each cited
#: work's role in the trace matches how the paper used it" -- over an empty set there is nothing to
#: be right or wrong about, and letting it decide is a coin flip: measured, 10 outcomes failed it
#: and 8 solely, while `06-hurrell` bound zero of 48 works and PASSED on the same evidence.
_CRITERIA_WITHOUT_CITED_ROLES: tuple[str, ...] = tuple(
    criterion for criterion in FORMATION_TRACE_CRITERIA if criterion != "cited_roles_correct"
)


def _selection_note(has_visible_works: bool) -> str:
    return _SELECTION_SCOPE_NOTE if has_visible_works else _NO_SELECTION_NOTE


def review_formation_trace(
    *,
    session: ScientificAgentSession,
    trace: QuestionFormationTrace,
    paper_case: PaperCase,
    literature: PaperLocalLiteratureContext,
    allowed_cited_work_ids: Sequence[str],
    generator_provider_ids: Sequence[str],
    review_guidance: str = "",
) -> GateOutcome:
    """Run the independent formation-trace gate; returns a structurally-earned GateOutcome.

    The reviewer sees the works the DRAFTER was allowed to bind, not every resolved reference.
    Sending the full list made the two agents judge different worlds: on the 2026-07-31 climate leg
    seven papers were drafted under an explicit "cite none" instruction and then failed
    ``cited_roles_correct`` for citing none, a criterion that ranges over the trace's own citations
    and cannot be failed by an empty set. "This trace ignores available literature" is a true
    observation about the SELECTOR; routed onto this criterion it killed the paper.
    """
    allowed = set(allowed_cited_work_ids)
    visible_works = [work for work in literature.cited_works if work.cited_work_id in allowed]
    note = _selection_note(bool(visible_works))
    turn_input = FormationTraceTurnInput(
        formation_trace=trace.model_dump(mode="json"),
        paper_case_question=paper_case.scientific_question.model_dump(mode="json"),
        cited_works=[work.model_dump(mode="json") for work in visible_works],
        review_guidance=f"{review_guidance.strip()} {note}".strip(),
    )
    # With no citation in front of it, `cited_roles_correct` has nothing to be right or wrong
    # about, and letting it decide is a coin flip on a paper's life. Measured: 10 outcomes failed
    # it, 8 of them SOLELY, and 4 of those had an empty allowed set -- while `06-hurrell` bound
    # zero of 48 works and PASSED. Same evidence, opposite verdicts.
    #
    # Dropping it from the required set is NOT enough on its own, and the first draft of this
    # change was worse than the defect it replaced. `gate_kernel` counts an assessment for a
    # criterion outside the required set as `unknown`, and any unknown blocks accept -- so a
    # reviewer that ignores the note and returns `cited_roles_correct` anyway would take the paper
    # from a coin flip to certain death. Verified before landing: reduced set + a compliant reply
    # accepts; reduced set + a five-criterion reply produced `unknown=['cited_roles_correct']`.
    #
    # So the host does both halves itself: it drops the criterion AND discards any assessment of it
    # that comes back regardless. An honest not-applicable cannot depend on a model following an
    # instruction.
    if visible_works:
        return run_structured_gate_review(
            session=session,
            turn_input=turn_input,
            candidate=trace,
            gate_name=FORMATION_TRACE_GATE,
            required_criteria=FORMATION_TRACE_CRITERIA,
            evidence_resolved=_evidence_resolved(trace, paper_case, literature),
            generator_provider_ids=generator_provider_ids,
        )
    outcome = run_structured_gate_review(
        session=session,
        turn_input=turn_input,
        candidate=trace,
        gate_name=FORMATION_TRACE_GATE,
        required_criteria=_CRITERIA_WITHOUT_CITED_ROLES,
        evidence_resolved=_evidence_resolved(trace, paper_case, literature),
        generator_provider_ids=generator_provider_ids,
        drop_unrequired_criteria=True,
    )
    return outcome


def promote_formation_trace_to_ai_reviewed(
    trace: QuestionFormationTrace, outcome: GateOutcome
) -> QuestionFormationTrace:
    """Stamp ``AI_REVIEWED`` on a formation-trace-accepted draft, or raise (fail closed).

    The AI promoter never writes ``EXPERT_REVIEWED`` — an AI verdict cannot masquerade as human.
    """
    assert_promotion_binding(candidate=trace, outcome=outcome, expected_gate=FORMATION_TRACE_GATE)
    promoted = trace.model_copy(deep=True)
    promoted.review_status = QuestionFormationTraceReviewStatus.AI_REVIEWED
    assert_promoted_status_is_holdable(promoted, expected_gate=FORMATION_TRACE_GATE)
    return promoted
