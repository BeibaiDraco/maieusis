"""Full generic dataset narrator — gather sources → fuse → independent fidelity gate.

Orchestrates the documentation-side sources it can from a ``DatasetSeed`` (A from the link, D from the
user docs, C via web search when a provider is given), accepts a pre-computed Source B (the agent
sample exploration is heavy + config-specific, so it is passed in rather than spawned here), fuses
them trust-ordered into one coarse ``DatasetNarrative``, and — when a reviewer session is supplied —
runs the independent-AI fidelity gate. Source C is degradable: a web-search failure is skipped and
the other sources carry the narrative. No new agent spawn here.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from ...providers.models.base import StructuredModelProvider
from ...providers.models.web_search_provider import WebSearchModelProvider
from ...providers.scientific_agents import ScientificAgentSession
from ...schemas.coarse_dataset_facts import CoarseDatasetFacts, CoarseLocalDatasetFacts
from ...schemas.dataset_narrative import DatasetNarrative
from ...schemas.dataset_seed import DatasetSeed
from ..agents.dataset_narrative_reviewer import (
    DatasetNarrativeFidelityReview,
    review_dataset_narrative_fidelity,
)
from .fusion import SourceKind, fuse_coarse_dataset_narrative
from .source_a_documentation import build_documentation_coarse_facts
from .source_c_model_research import build_model_research_coarse_facts
from .source_d_user_docs import (
    UnreadableUserDocumentationError,
    build_user_description_coarse_facts,
)


@dataclass
class NarratorResult:
    """The fused candidate narrative + the sources that fed it + the optional fidelity review."""

    candidate: DatasetNarrative
    sources: dict[SourceKind, CoarseDatasetFacts] = field(default_factory=dict)
    review: DatasetNarrativeFidelityReview | None = None
    skipped: dict[str, str] = field(default_factory=dict)


def gather_and_fuse_dataset_narrative(
    *,
    seed: DatasetSeed,
    doc_provider: StructuredModelProvider,
    web_search_provider: WebSearchModelProvider | None = None,
    local_sample_facts: CoarseLocalDatasetFacts | None = None,
    reviewer_session: ScientificAgentSession | None = None,
    review_guidance: str = "",
    max_prompt_chars: int = 250_000,
) -> NarratorResult:
    """Gather A (+ D if docs, + C if a web-search provider, + B if passed) → fuse → optional gate.

    In v0.1 nothing passes ``local_sample_facts`` (Source B) and the product driver supplies no
    web-search provider (Source C), so a run fuses A and D only. Both absences are recorded in
    ``skipped`` rather than being inferable from a source that simply never appears.
    """
    sources: dict[SourceKind, CoarseDatasetFacts] = {}
    skipped: dict[str, str] = {}

    if seed.link:
        try:
            sources[SourceKind.DOCUMENTATION] = build_documentation_coarse_facts(
                seed=seed, provider=doc_provider, max_prompt_chars=max_prompt_chars
            )
        except Exception as exc:
            # CLIM-07: an unusable Source-A seed degrades LOCALLY, exactly like Sources C and D —
            # it must never erase safe sibling contributions from the fused proposal narrative.
            skipped[SourceKind.DOCUMENTATION.value] = f"{type(exc).__name__}: {exc}"
    else:
        skipped[SourceKind.DOCUMENTATION.value] = "inactive: no dataset seed link supplied"
    if seed.docs:
        try:
            facts, doc_exclusions = build_user_description_coarse_facts(
                seed=seed, provider=doc_provider, max_prompt_chars=max_prompt_chars
            )
            sources[SourceKind.USER_DESCRIPTION] = facts
        except UnreadableUserDocumentationError as exc:
            skipped[SourceKind.USER_DESCRIPTION.value] = str(exc)
        else:
            # CLIM-08: per-document exclusions stay visible even when the source succeeds.
            for doc_name, reason in doc_exclusions.items():
                skipped[f"{SourceKind.USER_DESCRIPTION.value}.doc:{doc_name}"] = reason
    else:
        skipped[SourceKind.USER_DESCRIPTION.value] = "inactive: no user docs supplied"
    if local_sample_facts is not None:
        sources[SourceKind.LOCAL_SAMPLE] = local_sample_facts
    else:
        # Source B was the only feed whose absence left no trace: A, C and D each record why they
        # did not contribute, while B simply never appeared, and 0 of the recorded run artifacts
        # carry a `local-sample-exploration://` locator. An absence nobody writes down reads exactly
        # like a source that had nothing to say.
        skipped[SourceKind.LOCAL_SAMPLE.value] = (
            "inactive: no local-sample exploration facts supplied "
            "(no caller passes Source B in this version)"
        )
    if web_search_provider is not None:
        try:
            sources[SourceKind.MODEL_RESEARCH] = build_model_research_coarse_facts(
                seed=seed, web_search_provider=web_search_provider
            )
        except Exception as exc:
            skipped["model_research"] = f"{type(exc).__name__}: {exc}"
    else:
        skipped[SourceKind.MODEL_RESEARCH.value] = "inactive: no web-search provider configured"

    candidate = fuse_coarse_dataset_narrative(sources, dataset_id=seed.dataset_id)

    review: DatasetNarrativeFidelityReview | None = None
    if reviewer_session is not None:
        review = review_dataset_narrative_fidelity(
            session=reviewer_session,
            dataset_id=seed.dataset_id,
            candidate=candidate,
            sources=sources,
            generator_provider_ids=narrative_generator_provider_ids(sources),
            review_guidance=review_guidance,
        )
    return NarratorResult(candidate=candidate, sources=sources, review=review, skipped=skipped)


def narrative_generator_provider_ids(
    sources: Mapping[SourceKind, CoarseDatasetFacts],
) -> Sequence[str]:
    """Every provider that generated a source feed — the independence set the fidelity gate checks.

    Public because the bounded repair loop re-reviews a redraft outside this module and must assert
    independence against the SAME set the first review used.
    """
    return sorted(
        {
            str(getattr(facts, "provider_id", "") or "")
            for facts in sources.values()
            if getattr(facts, "provider_id", "")
        }
    )
