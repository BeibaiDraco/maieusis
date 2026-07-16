"""Per-variant nearest-prior novelty assessment.

For an active QuestionFamily variant, run a LIMITED nearest-prior retrieval (query built generically
from the variant's own question — no domain constants) and classify the result into one of the honest
``VariantNoveltyStatus`` labels. NEVER asserts "novel". The search is an injectable callable so the
logic is testable with mock candidates and no paid API; the product path wraps the existing
``literature_prior_search`` HTTP muscle. Config is an injectable ``VariantNoveltyConfig`` (Standard
default-ON; demo/cost OFF) so 5c-0 can wire it to ``MaieusisProjectConfig`` without a global constant.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from ...schemas.question_family import QuestionFamilyVariant
from ...schemas.variant_novelty import (
    NearestPriorCandidate,
    VariantNoveltyResult,
    VariantNoveltyStatus,
)

# A search takes a query string and returns ranked nearest-prior candidates (highest similarity first).
NoveltySearch = Callable[[str], Sequence[NearestPriorCandidate]]


@dataclass(frozen=True)
class VariantNoveltyConfig:
    """Injectable per-variant-novelty config. Disabled means explicitly not assessed."""

    enabled: bool = True
    direct_recap_threshold: float = 0.9
    close_prior_threshold: float = 0.7
    max_candidates: int = 5
    providers: tuple[str, ...] = field(default_factory=lambda: ("openalex",))
    knowledge_cutoff: str = ""


def _variant_query(variant: QuestionFamilyVariant) -> str:
    seed = variant.seed
    return " ".join(part for part in (seed.question, seed.scientific_tension) if part.strip())


def assess_variant_novelty(
    variant: QuestionFamilyVariant,
    *,
    search: NoveltySearch,
    config: VariantNoveltyConfig | None = None,
) -> VariantNoveltyResult:
    """Assess one variant's nearest-prior novelty; returns an honest label (never "novel")."""
    config = config or VariantNoveltyConfig()
    seed = variant.seed
    if not config.enabled:
        return VariantNoveltyResult(
            variant_id=variant.variant_id,
            question_seed_id=seed.question_seed_id,
            status=VariantNoveltyStatus.NOT_ASSESSED,
            rationale="Novelty was not assessed because no search ran.",
            retrieval_enabled=False,
        )

    query = _variant_query(variant)
    candidates = list(search(query))[: config.max_candidates]
    top_similarity = max((c.similarity for c in candidates), default=0.0)

    if not candidates:
        status = VariantNoveltyStatus.INSUFFICIENT_RETRIEVAL_EVIDENCE
        rationale = (
            "Retrieval returned no candidates; too thin to judge nearest-prior (not a claim)."
        )
    elif top_similarity >= config.direct_recap_threshold:
        status = VariantNoveltyStatus.DIRECT_RECAP
        rationale = "A prior in the searched scope closely matches this variant's question."
    elif top_similarity >= config.close_prior_threshold:
        status = VariantNoveltyStatus.POSSIBLE_CLOSE_PRIOR
        rationale = "A close prior exists in the searched scope; review before shortlisting."
    else:
        status = VariantNoveltyStatus.NO_CLOSE_PRIOR_FOUND_IN_SEARCH_SCOPE
        rationale = (
            "No close prior found in the searched scope (a limited search, not a novelty claim)."
        )

    return VariantNoveltyResult(
        variant_id=variant.variant_id,
        question_seed_id=seed.question_seed_id,
        status=status,
        query=query,
        providers=list(config.providers),
        knowledge_cutoff=config.knowledge_cutoff,
        nearest_source_ids=[c.source_record_id for c in candidates],
        nearest_candidates=candidates,
        rationale=rationale,
    )
