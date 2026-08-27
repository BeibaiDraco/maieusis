"""Resolve a ``ResearchIntent`` into a ``ResolvedResearchScope`` — the 3 modes made real.

* ``topic_conditioned`` — uses the user's topic_terms / topic_description faithfully (no silent rewrite).
* ``seed_question`` — the seed question enters scope/query derivation (no degradation on missing terms).
* ``open`` — derives a typed ``InferredResearchScope`` from reviewed PatternBank + the coarse
  ``DatasetNarrative`` ONLY. This is the open-mode firewall: the ONLY inputs are two typed, already
  proposal-safe artifacts. This module imports NO planner / inspection / sample / CapabilityRegistry /
  confirmation surface — an import-lock test pins that so the firewall is structural, not prompted.

A model may read that same narrative and propose the terms (``services/context/scope_derivation.py``);
its result arrives here as DATA through ``derived_scope``, never as a callable, so this module still
does not know how to reach a provider and the firewall stays structural. Declared terms always win
over derived ones except under ``ScopeDerivationMode.AUGMENT``, where they come first and unrewritten.

The original ``ResearchIntent`` is always preserved (its digest rides on the scope); inference never
masquerades as user input. This module carries no dataset-specific names; it is enforced by the
dataset-agnostic guard.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from ...provenance import stable_hash
from ...schemas.dataset_narrative import DatasetNarrative
from ...schemas.derived_dataset_scope import DerivedDatasetScope
from ...schemas.inferred_research_scope import (
    InferredResearchScope,
    ResearchScopeSourceMode,
    ResolvedResearchScope,
)
from ...schemas.question_pattern import QuestionPatternCard
from ...schemas.research_intent import (
    ResearchIntent,
    ResearchIntentMode,
    ScopeDerivationMode,
)
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


def config_declared_scope_terms(intent: ResearchIntent) -> list[str]:
    """The scope terms a config already determines, or ``[]`` when only the run can know them.

    ``resolve_research_scope`` needs a DatasetNarrative and reviewed patterns, neither of which
    exists before a run starts, so preflight cannot call it -- yet preflight must count the pool
    behind each term the run will actually search, and a preflight that checks a different list than
    the run searches is checking nothing. So this is not a preflight-shaped copy of that logic: it
    IS that logic, and ``resolve_research_scope`` calls it for the two modes it covers. The two
    cannot drift because there is only one of them.

    ``open`` mode infers its terms from artifacts the run itself produces, so there is nothing to
    return before the run and the empty list says so.
    """

    if intent.mode == ResearchIntentMode.TOPIC_CONDITIONED:
        return _dedupe(
            [*intent.topic_terms, *intent.include_concepts, *intent.target_constructs]
        ) or _keywords(intent.topic_description)
    if intent.mode == ResearchIntentMode.SEED_QUESTION:
        return _dedupe(
            [*intent.topic_terms, *intent.target_constructs, *_keywords(intent.seed_question)]
        )
    return []


def deterministic_narrative_terms(narrative: DatasetNarrative) -> list[str]:
    """Search terms taken from the dataset's own coarse story by keyword extraction alone.

    Domain-specific to whatever the dataset is, via a domain-neutral mechanism. This is both the
    open-mode scope when no model derives one AND the fallback a failed derivation degrades to, and
    it is one function rather than two for the reason ``config_declared_scope_terms`` is: a fallback
    that is a near-copy of the thing it falls back to drifts from it, and then the run that degrades
    searches something nobody has ever inspected.
    """

    term_candidates = [
        *narrative.major_variables,
        *(kw for opp in narrative.reuse_opportunities for kw in _keywords(opp)),
        *narrative.modalities,
    ]
    return _dedupe(term_candidates) or _keywords(narrative.scientific_purpose)


def _identity_terms(derived_scope: DerivedDatasetScope | None) -> list[str]:
    """The reuse-lane vocabulary, or nothing. Never guessed from the narrative text.

    A degraded derivation returns an empty list rather than a keyword-extracted approximation: the
    name a citing paper uses for a dataset is not recoverable from the dataset's own prose, and a
    wrong name retrieves a confidently irrelevant corpus for the one dimension that had none.
    """

    if derived_scope is None:
        return []
    return [term for term in derived_scope.dataset_identity_terms if term.strip()]


def resolve_research_scope(
    intent: ResearchIntent,
    *,
    reviewed_patterns: Sequence[QuestionPatternCard],
    dataset_narrative: DatasetNarrative,
    derived_scope: DerivedDatasetScope | None = None,
) -> ResolvedResearchScope:
    """Resolve the intent's mode into a scope retrieval + the topic-evidence gate can consume.

    ``derived_scope`` is DATA, never a callable or a provider: this module must not learn how to
    reach a model, or the open-mode firewall stops being structural. The caller derives, then hands
    the result here. Only the derived TERMS cross into ``ResolvedResearchScope`` -- the deriver's
    per-term reasoning stays in the persisted artifact, because this object is passed verbatim into
    the independent topic-evidence reviewer's packet and a rationale riding along would be the
    deriver arguing its case to the reviewer that grades scope fidelity.
    """
    intent_digest = stable_hash(intent.model_dump(mode="json"))
    derived_terms = list(derived_scope.terms) if derived_scope is not None else []
    derived_constructs = list(derived_scope.construct_families) if derived_scope is not None else []
    augmenting = intent.scope_derivation == ScopeDerivationMode.AUGMENT and derived_terms

    if intent.mode == ResearchIntentMode.TOPIC_CONDITIONED:
        declared = config_declared_scope_terms(intent)
        return ResolvedResearchScope(
            dataset_identity_terms=_identity_terms(derived_scope),
            source_mode=ResearchScopeSourceMode.TOPIC_CONDITIONED,
            # Declared first, in the user's own order, never rewritten or reordered. A reader of
            # research_scope.md sees what they asked for before what the system added.
            terms=_dedupe([*declared, *derived_terms]) if augmenting else declared,
            construct_families=_dedupe(
                [*intent.target_constructs, *(derived_constructs if augmenting else [])]
            ),
            original_intent_digest=intent_digest,
        )

    if intent.mode == ResearchIntentMode.SEED_QUESTION:
        declared = config_declared_scope_terms(intent)
        return ResolvedResearchScope(
            dataset_identity_terms=_identity_terms(derived_scope),
            source_mode=ResearchScopeSourceMode.SEED_QUESTION,
            terms=_dedupe([*declared, *derived_terms]) if augmenting else declared,
            seed_question=intent.seed_question,
            construct_families=_dedupe(
                [*intent.target_constructs, *(derived_constructs if augmenting else [])]
            ),
            original_intent_digest=intent_digest,
        )

    inferred = _infer_open_scope(reviewed_patterns, dataset_narrative, derived_scope=derived_scope)
    return ResolvedResearchScope(
        dataset_identity_terms=_identity_terms(derived_scope),
        source_mode=ResearchScopeSourceMode.OPEN_INFERRED,
        terms=inferred.inferred_topic_terms,
        construct_families=inferred.inferred_construct_families,
        inferred_scope=inferred,
        original_intent_digest=intent_digest,
    )


def _infer_open_scope(
    reviewed_patterns: Sequence[QuestionPatternCard],
    narrative: DatasetNarrative,
    *,
    derived_scope: DerivedDatasetScope | None = None,
) -> InferredResearchScope:
    """Derive an InferredResearchScope from reviewed patterns + the coarse narrative ONLY (firewall)."""
    if not reviewed_patterns or not all(
        is_accepted_authority(p.review_status) for p in reviewed_patterns
    ):
        raise ValueError("open-mode scope requires reviewed (accepted) PatternBank entries")
    if not is_accepted_authority(narrative.review_status):
        raise ValueError("open-mode scope requires a reviewed (accepted) DatasetNarrative")

    # Terms come from the dataset's OWN coarse story — read by a model when one derived them, and
    # by keyword extraction over the same fields when none did. The keyword lane is not a lesser
    # copy kept for tests: it is what a run searches when the deriver has a bad night, so it stays
    # a real, inspected path.
    deterministic = deterministic_narrative_terms(narrative)
    model_derived = list(derived_scope.terms) if derived_scope is not None else []
    terms = _dedupe(model_derived) or deterministic
    construct_families = (
        _dedupe(derived_scope.construct_families) if derived_scope is not None else []
    ) or (_dedupe(narrative.major_variables) or _dedupe(terms[:5]))
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
    # A FIXED sentence per lane, never the deriver's own words. This object rides into the
    # independent reviewer's packet, and free text written by the step being judged does not belong
    # in the judge's input. The deriver's reasoning is persisted separately, for a human reader.
    if model_derived and derived_scope is not None:
        provenance = (
            "Scope derived by a model reading the coarse dataset narrative, before any literature "
            "was retrieved and without sight of any review criterion or verdict; it was not "
            "specified by the user and does not use exact schema, samples, or planner evidence."
        )
        derivation = f"{derived_scope.prompt_version}:{derived_scope.model_id}".rstrip(":")
    else:
        provenance = (
            "Scope inferred from reviewed question patterns + the coarse dataset narrative by "
            "deterministic keyword extraction; it was not specified by the user and does not use "
            "exact schema, samples, or planner evidence."
        )
        derivation = "deterministic_patterns_plus_coarse_narrative/v1"
    return InferredResearchScope(
        scope_id=f"inferred-scope-{narrative.dataset_id}",
        inferred_topic_terms=terms,
        inferred_construct_families=construct_families,
        supporting_pattern_ids=supporting_pattern_ids,
        supporting_dataset_source_ids=supporting_source_ids,
        excluded_scope=list(narrative.known_high_level_limitations),
        uncertainties=[provenance],
        derivation=derivation,
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
                f"- Derived by: `{inferred.derivation}`",
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
