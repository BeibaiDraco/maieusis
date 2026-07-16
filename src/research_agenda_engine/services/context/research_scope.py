"""Resolve a ``ResearchIntent`` into a ``ResolvedResearchScope`` — the 3 modes made real.

* ``topic_conditioned`` — uses the user's topic_terms / topic_description faithfully (no silent rewrite).
* ``seed_question`` — the seed question enters scope/query derivation (no degradation on missing terms).
* ``open`` — derives a typed ``InferredResearchScope`` from reviewed PatternBank + the coarse
  ``DatasetNarrative`` ONLY. This is the open-mode firewall: the ONLY inputs are two typed, already
  proposal-safe artifacts. This module imports NO planner / inspection / sample / CapabilityRegistry /
  confirmation surface — an import-lock test pins that so the firewall is structural, not prompted.

The original ``ResearchIntent`` is always preserved (its digest rides on the scope); inference never
masquerades as user input. This module carries no dataset-specific names; it is enforced by the
dataset-agnostic guard.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from ...provenance import stable_hash
from ...schemas.dataset_narrative import DatasetNarrative
from ...schemas.inferred_research_scope import (
    InferredResearchScope,
    ResearchScopeSourceMode,
    ResolvedResearchScope,
)
from ...schemas.question_pattern import QuestionPatternCard
from ...schemas.research_intent import ResearchIntent, ResearchIntentMode
from ...schemas.review_authority import is_accepted_authority

_STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "into",
        "over",
        "under",
        "what",
        "which",
        "does",
        "can",
        "are",
        "was",
        "were",
        "how",
        "why",
        "when",
        "will",
        "would",
        "study",
        "studies",
        "data",
        "dataset",
        "datasets",
        "using",
        "used",
        "use",
        "between",
    }
)


def _keywords(text: str) -> list[str]:
    """Domain-neutral keyword extraction: content words (len>3), lowercased, deduped, order-stable."""
    words = re.findall(r"[A-Za-z][A-Za-z0-9\-]{2,}", text.lower())
    out: list[str] = []
    seen: set[str] = set()
    for word in words:
        if word in _STOPWORDS or word in seen:
            continue
        seen.add(word)
        out.append(word)
    return out


def _dedupe(values: Sequence[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = value.strip()
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def resolve_research_scope(
    intent: ResearchIntent,
    *,
    reviewed_patterns: Sequence[QuestionPatternCard],
    dataset_narrative: DatasetNarrative,
) -> ResolvedResearchScope:
    """Resolve the intent's mode into a scope retrieval + the topic-evidence gate can consume."""
    intent_digest = stable_hash(intent.model_dump(mode="json"))

    if intent.mode == ResearchIntentMode.TOPIC_CONDITIONED:
        terms = _dedupe(
            [*intent.topic_terms, *intent.include_concepts, *intent.target_constructs]
        ) or _keywords(intent.topic_description)
        return ResolvedResearchScope(
            source_mode=ResearchScopeSourceMode.TOPIC_CONDITIONED,
            terms=terms,
            construct_families=_dedupe(intent.target_constructs),
            original_intent_digest=intent_digest,
        )

    if intent.mode == ResearchIntentMode.SEED_QUESTION:
        terms = _dedupe(
            [*intent.topic_terms, *intent.target_constructs, *_keywords(intent.seed_question)]
        )
        return ResolvedResearchScope(
            source_mode=ResearchScopeSourceMode.SEED_QUESTION,
            terms=terms,
            seed_question=intent.seed_question,
            construct_families=_dedupe(intent.target_constructs),
            original_intent_digest=intent_digest,
        )

    inferred = _infer_open_scope(reviewed_patterns, dataset_narrative)
    return ResolvedResearchScope(
        source_mode=ResearchScopeSourceMode.OPEN_INFERRED,
        terms=inferred.inferred_topic_terms,
        construct_families=inferred.inferred_construct_families,
        inferred_scope=inferred,
        original_intent_digest=intent_digest,
    )


def _infer_open_scope(
    reviewed_patterns: Sequence[QuestionPatternCard],
    narrative: DatasetNarrative,
) -> InferredResearchScope:
    """Derive an InferredResearchScope from reviewed patterns + the coarse narrative ONLY (firewall)."""
    if not reviewed_patterns or not all(
        is_accepted_authority(p.review_status) for p in reviewed_patterns
    ):
        raise ValueError("open-mode scope requires reviewed (accepted) PatternBank entries")
    if not is_accepted_authority(narrative.review_status):
        raise ValueError("open-mode scope requires a reviewed (accepted) DatasetNarrative")

    # Terms come from the dataset's OWN coarse story (major variables / reuse opportunities / modalities
    # / purpose) — domain-specific to whatever the dataset is, via a domain-neutral mechanism.
    term_candidates = [
        *narrative.major_variables,
        *(kw for opp in narrative.reuse_opportunities for kw in _keywords(opp)),
        *narrative.modalities,
    ]
    terms = _dedupe(term_candidates) or _keywords(narrative.scientific_purpose)
    construct_families = _dedupe(narrative.major_variables) or _dedupe(terms[:5])
    supporting_pattern_ids = [p.pattern_id for p in reviewed_patterns]
    supporting_source_ids = [ref.source_id for ref in narrative.source_refs]

    input_payload = {
        "pattern_ids": supporting_pattern_ids,
        "narrative_id": narrative.dataset_narrative_id,
        "major_variables": narrative.major_variables,
        "reuse_opportunities": narrative.reuse_opportunities,
        "modalities": narrative.modalities,
    }
    input_digest = stable_hash(input_payload)
    output_digest = stable_hash({"terms": terms, "constructs": construct_families})
    return InferredResearchScope(
        scope_id=f"inferred-scope-{narrative.dataset_id}",
        inferred_topic_terms=terms,
        inferred_construct_families=construct_families,
        supporting_pattern_ids=supporting_pattern_ids,
        supporting_dataset_source_ids=supporting_source_ids,
        excluded_scope=list(narrative.known_high_level_limitations),
        uncertainties=[
            "Scope inferred from reviewed question patterns + the coarse dataset narrative; it was "
            "not specified by the user and does not use exact schema, samples, or planner evidence.",
        ],
        input_digest=input_digest,
        output_digest=output_digest,
    )


def render_research_scope_summary(scope: ResolvedResearchScope) -> str:
    """Clean human-readable ``research_scope.md`` (diagnostic, not an approval)."""
    lines = [
        "# Research scope",
        "",
        f"- Mode: `{scope.source_mode.value}`",
        f"- Query terms: {', '.join(scope.terms)}",
    ]
    if scope.seed_question:
        lines.append(f"- Seed question: {scope.seed_question}")
    inferred = scope.inferred_scope
    if inferred is not None:
        lines.extend(
            [
                "",
                "## Inferred scope (open mode)",
                "",
                f"- Inferred topics: {', '.join(inferred.inferred_topic_terms)}",
                f"- Construct families: {', '.join(inferred.inferred_construct_families)}",
                f"- Supporting patterns: {', '.join(inferred.supporting_pattern_ids)}",
                f"- Supporting dataset properties: {', '.join(inferred.supporting_dataset_source_ids)}",
            ]
        )
        if inferred.excluded_scope:
            lines.append(f"- Excluded scope: {', '.join(inferred.excluded_scope)}")
        lines.extend(["", "## Uncertainties", "", *(f"- {u}" for u in inferred.uncertainties)])
    lines.extend(
        [
            "",
            "## If this looks wrong",
            "",
            "This scope is inferred/derived, not a user approval. Set a `topic_conditioned` or "
            "`seed_question` ResearchIntent to steer it, then re-run.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
