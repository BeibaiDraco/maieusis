"""Independent-AI shortlist-worthiness gate.

Judges whether a consolidated QuestionFamily is worth shortlisting — scientific worthiness,
non-triviality, real variant distinction, and whether per-variant novelty was considered — on the 5a-1
gate kernel (cross-provider, structurally earned accept). Per-variant novelty (`VariantNoveltyResult`,
DEC-2) is a first-class INPUT: the reviewer sees each active variant's honest novelty status, but the
gate NEVER emits "novel". Host-side ``evidence_resolved`` confirms novelty was actually assessed for
every active variant (the model cannot assert it).

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
from ...schemas.question_family import QuestionFamily
from ...schemas.variant_novelty import VariantNoveltyResult
from .gate_kernel import run_structured_gate_review
from .reviewer_base import build_scientific_reviewer_provider_from_env

SHORTLIST_WORTHINESS_REVIEWER_PROMPT_VERSION = "shortlist_worthiness_reviewer/v1"
SHORTLIST_WORTHINESS_GATE = "shortlist_worthiness"

SHORTLIST_WORTHINESS_CRITERIA: tuple[str, ...] = (
    "scientific_worthiness",
    "non_triviality",
    "variant_distinction",
    "novelty_considered",
    "proposal_firewall",
    "honest_uncertainty",
)


class ShortlistWorthinessTurnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_family: dict[str, Any]
    active_variant_ids: list[str]
    variant_novelty: list[dict[str, Any]]
    review_guidance: str = ""


def load_shortlist_worthiness_reviewer_prompt(
    prompt_version: str = SHORTLIST_WORTHINESS_REVIEWER_PROMPT_VERSION,
) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def build_shortlist_worthiness_reviewer_provider_from_env(
    *,
    provider: Literal["openai", "anthropic"] | None = None,
    allow_pro_model: bool = False,
    project_root: str | Path | None = None,
) -> ScientificAgentProvider:
    """Build a live independent shortlist-worthiness reviewer provider from runtime env files."""
    return build_scientific_reviewer_provider_from_env(
        system_prompt_loader=load_shortlist_worthiness_reviewer_prompt,
        credential_fallback=("anthropic", "openai"),
        unsupported_provider_label="shortlist worthiness reviewer",
        provider=provider,
        allow_pro_model=allow_pro_model,
        project_root=project_root,
    )


def _evidence_resolved(
    active_variant_ids: Sequence[str],
    novelty_results: Sequence[VariantNoveltyResult],
) -> bool:
    """Host-side pre-check: ≥1 active variant AND novelty was assessed for every active variant."""
    if not active_variant_ids:
        return False
    novelty_by_variant = {result.variant_id for result in novelty_results}
    return all(variant_id in novelty_by_variant for variant_id in active_variant_ids)


def review_shortlist_worthiness(
    *,
    session: ScientificAgentSession,
    family: QuestionFamily,
    active_variant_ids: Sequence[str],
    novelty_results: Sequence[VariantNoveltyResult],
    generator_provider_ids: Sequence[str],
    review_guidance: str = "",
) -> GateOutcome:
    """Run the independent shortlist-worthiness gate; returns a structurally-earned GateOutcome."""
    turn_input = ShortlistWorthinessTurnInput(
        question_family=family.model_dump(mode="json"),
        active_variant_ids=list(active_variant_ids),
        variant_novelty=[result.model_dump(mode="json") for result in novelty_results],
        review_guidance=review_guidance,
    )
    return run_structured_gate_review(
        session=session,
        turn_input=turn_input,
        candidate=family,
        gate_name=SHORTLIST_WORTHINESS_GATE,
        required_criteria=SHORTLIST_WORTHINESS_CRITERIA,
        evidence_resolved=_evidence_resolved(active_variant_ids, novelty_results),
        generator_provider_ids=generator_provider_ids,
    )
