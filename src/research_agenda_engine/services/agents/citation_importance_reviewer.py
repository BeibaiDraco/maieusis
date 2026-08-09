"""Independent-AI citation-importance gate.

Judges whether a paper's SELECTED key citations really participated in that paper's question formation
(vs. an unrelated passage being ranked "central"), whether rank/role/context are evidenced, and whether
abstract-use is honest. Runs on the 5a-1 gate kernel (cross-provider, structurally earned accept).
Deterministic evidence pre-checks are host-side: selected ids ⊆ input ids ⊆ real cited works, each
selection item's evidence_context_ids resolve to real citation contexts, and abstract_evidence_used is
only claimed where an abstract was actually retrieved. The model cannot assert this closure.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from ...assets import resolve_asset
from ...providers.scientific_agents import ScientificAgentProvider, ScientificAgentSession
from ...schemas.cited_literature import (
    PaperLocalLiteratureContext,
    PaperLocalLiteratureReviewStatus,
)
from ...schemas.gate_outcome import GateOutcome
from ...schemas.paper_case import PaperCase
from .gate_kernel import run_structured_gate_review
from .promotion import assert_promoted_status_is_holdable, assert_promotion_binding
from .reviewer_base import build_scientific_reviewer_provider_from_env

CITATION_IMPORTANCE_REVIEWER_PROMPT_VERSION = "citation_importance_reviewer/v1"
CITATION_IMPORTANCE_GATE = "citation_importance"

CITATION_IMPORTANCE_CRITERIA: tuple[str, ...] = (
    "selected_works_participated",
    "rank_and_role_evidenced",
    "citation_context_matches_cited_work",
    "abstract_use_honest",
)


class CitationImportanceTurnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_case_question: dict[str, Any]
    cited_works: list[dict[str, Any]]
    citation_contexts: list[dict[str, Any]]
    importance_selection: dict[str, Any]
    review_guidance: str = ""


def load_citation_importance_reviewer_prompt(
    prompt_version: str = CITATION_IMPORTANCE_REVIEWER_PROMPT_VERSION,
) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def build_citation_importance_reviewer_provider_from_env(
    *,
    provider: Literal["openai", "anthropic"] | None = None,
    allow_pro_model: bool = False,
    project_root: str | Path | None = None,
) -> ScientificAgentProvider:
    """Build a live independent citation-importance reviewer provider from runtime env files."""
    return build_scientific_reviewer_provider_from_env(
        system_prompt_loader=load_citation_importance_reviewer_prompt,
        credential_fallback=("anthropic", "openai"),
        unsupported_provider_label="citation importance reviewer",
        provider=provider,
        allow_pro_model=allow_pro_model,
        project_root=project_root,
    )


def _evidence_resolved(literature: PaperLocalLiteratureContext) -> bool:
    """Host-side hard closure for selection, context, and claimed abstract evidence identities."""
    selection = literature.importance_selection
    if selection is None:
        return False
    cited_ids = {work.cited_work_id for work in literature.cited_works}
    if not set(selection.all_input_cited_work_ids) <= cited_ids:
        return False
    if not set(selection.selected_cited_work_ids) <= cited_ids:
        return False
    context_ids = {context.context_id for context in literature.citation_contexts}
    work_by_id = {work.cited_work_id: work for work in literature.cited_works}
    for item in selection.items:
        if item.cited_work_id not in cited_ids:
            return False
        if not set(item.evidence_context_ids) <= context_ids:
            return False
        work = work_by_id[item.cited_work_id]
        if item.abstract_evidence_used and not work.abstract.strip():
            return False
    return True


def review_citation_importance(
    *,
    session: ScientificAgentSession,
    paper_case: PaperCase,
    literature: PaperLocalLiteratureContext,
    generator_provider_ids: Sequence[str],
    review_guidance: str = "",
) -> GateOutcome:
    """Run the independent citation-importance gate; returns a structurally-earned GateOutcome."""
    selection = literature.importance_selection
    if selection is None:
        raise ValueError("citation-importance gate requires an importance_selection to review")
    turn_input = CitationImportanceTurnInput(
        paper_case_question=paper_case.scientific_question.model_dump(mode="json"),
        cited_works=[work.model_dump(mode="json") for work in literature.cited_works],
        citation_contexts=[ctx.model_dump(mode="json") for ctx in literature.citation_contexts],
        importance_selection=selection.model_dump(mode="json"),
        review_guidance=review_guidance,
    )
    return run_structured_gate_review(
        session=session,
        turn_input=turn_input,
        candidate=literature,
        gate_name=CITATION_IMPORTANCE_GATE,
        required_criteria=CITATION_IMPORTANCE_CRITERIA,
        evidence_resolved=_evidence_resolved(literature),
        generator_provider_ids=generator_provider_ids,
    )


def promote_literature_to_ai_reviewed(
    literature: PaperLocalLiteratureContext, outcome: GateOutcome
) -> PaperLocalLiteratureContext:
    """Stamp ``AI_REVIEWED`` on a citation-accepted literature context, or raise (fail closed).

    The AI promoter never writes ``EXPERT_REVIEWED`` — an AI verdict cannot masquerade as human.
    """
    assert_promotion_binding(
        candidate=literature, outcome=outcome, expected_gate=CITATION_IMPORTANCE_GATE
    )
    promoted = literature.model_copy(deep=True)
    promoted.review_status = PaperLocalLiteratureReviewStatus.AI_REVIEWED
    assert_promoted_status_is_holdable(promoted, expected_gate=CITATION_IMPORTANCE_GATE)
    promoted.warnings = [
        *literature.warnings,
        (
            f"Independent-AI citation-importance gate {CITATION_IMPORTANCE_REVIEWER_PROMPT_VERSION} "
            f"(provider {outcome.reviewer_provider_id}, model {outcome.reviewer_model_id}, "
            f"session {outcome.reviewer_session_id}) accepted at {datetime.now(UTC).isoformat()}."
        ),
    ]
    return promoted
