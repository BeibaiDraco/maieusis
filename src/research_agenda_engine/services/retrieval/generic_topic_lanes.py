"""Generic, domain-neutral topic-evidence retrieval protocol.

Replaces the neuroscience-specific lane specs on the ACTIVE product path. The lane TEMPLATES are
domain-neutral (background/tensions/methods/confounds/generalization/reuse/close-prior/open-gaps); the
scientific keywords come from the resolved research scope, NOT from code constants. There is no
``coding_geometry_bwm.yml`` and no neuroscience whitelist here — a non-neuro scope (e.g. a
plant/greenhouse dataset) produces domain-neutral queries with zero neuroscience terms (a functional
test enforces this; the dataset-token guard cannot).

The legacy ``r5_topic_evidence_lanes/v1`` protocol in ``topic_sources.py`` stays as history.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Iterable

from ...provenance import stable_hash
from ...schemas.inferred_research_scope import ResolvedResearchScope
from ...schemas.topic_literature import (
    TopicLensSourceFamily,
    TopicSourceProfile,
    TopicSourceQuery,
    TopicSourceQueryPlan,
)
from .topic_sources import _source_families_for_profile, resolve_topic_source_profile

GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSION = "generic_topic_evidence_lanes/v2"
GENERIC_SCOPE_TERM_QUERY_LANE = "scope_term_acquisition"

# Domain-neutral lane templates. Each is combined with the scope's OWN keywords; no domain vocabulary.
GENERIC_TOPIC_LANES: tuple[tuple[str, str], ...] = (
    ("background_core_constructs", "definition core constructs background review"),
    ("unresolved_tensions", "unresolved debate competing hypotheses controversy"),
    ("methods_measurement_limits", "methods measurement limitations validity reliability"),
    ("competing_explanations_confounds", "confounds alternative explanations controls"),
    (
        "boundary_conditions_generalization",
        "generalization boundary conditions replication robustness",
    ),
    ("dataset_resource_reuse", "public dataset reuse secondary analysis open data"),
    ("close_prior_already_answered", "prior work already answered systematic review meta-analysis"),
    ("open_gaps", "open questions future directions unanswered gaps"),
)

# Domain-neutral scientific dimensions for model review. They are not retrieval identities and
# their coverage is never inferred from query provenance.
GENERIC_REQUIRED_LANES: tuple[str, ...] = tuple(lane for lane, _ in GENERIC_TOPIC_LANES)


def build_generic_topic_evidence_query_plan(
    scope: ResolvedResearchScope,
    *,
    source_families: Iterable[TopicLensSourceFamily] | None = None,
    source_profile: TopicSourceProfile | str = TopicSourceProfile.PUBLIC,
    elicit_api_key: str = "",
    max_results_per_query: int = 8,
) -> TopicSourceQueryPlan:
    """Build one domain-neutral acquisition lineage per source family and unique scope term.

    The eight generic scientific dimensions remain reviewer criteria. They are deliberately not
    query identities: repeating one search under eight labels manufactured coverage without
    acquiring any additional evidence.
    """
    resolved_profile = resolve_topic_source_profile(source_profile, elicit_api_key=elicit_api_key)
    families = list(source_families or _source_families_for_profile(resolved_profile))
    terms = _unique_scope_terms(scope.terms)
    queries: list[TopicSourceQuery] = []
    for family in families:
        is_elicit = family == TopicLensSourceFamily.ELICIT
        for term in terms:
            # One exact scope phrase per query. OpenAlex's title-and-abstract phrase search then
            # retrieves works about that term instead of documents containing a large AND-ed bag of
            # words. Ambiguous terms remain isolated to their own lineage for later scientific review.
            queries.append(
                TopicSourceQuery(
                    query_id=(
                        f"generic-topic-{family.value}-{GENERIC_SCOPE_TERM_QUERY_LANE}-"
                        f"{stable_hash({'family': family.value, 'query': term})[:8]}"
                    ),
                    source_family=family,
                    query=term,
                    query_lane=GENERIC_SCOPE_TERM_QUERY_LANE,
                    topic_terms=[term],
                    max_results=max_results_per_query,
                    corpus="elicit" if is_elicit else "",
                    search_mode="semantic" if is_elicit else "",
                )
            )
    plan_identity = {
        "version": GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSION,
        "profile": resolved_profile.value,
        "terms": terms,
        "families": [family.value for family in families],
        "max_results_per_query": max_results_per_query,
        "queries": [query.model_dump(mode="json") for query in queries],
    }
    return TopicSourceQueryPlan(
        plan_id=(f"generic-topic-evidence-plan-v2-{stable_hash(plan_identity)[:12]}"),
        source_profile=resolved_profile,
        topic_terms=terms,
        queries=queries,
        prompt_version=GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSION,
    )


def _unique_scope_terms(values: Iterable[str]) -> list[str]:
    """Preserve first spelling/order while collapsing whitespace and case-only duplicates."""

    terms: list[str] = []
    seen: set[str] = set()
    for value in values:
        term = " ".join(value.split())
        key = term.casefold()
        if not term or key in seen:
            continue
        seen.add(key)
        terms.append(term)
    return terms
