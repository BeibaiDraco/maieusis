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

from collections.abc import Iterable, Mapping

from ...provenance import stable_hash
from ...schemas.inferred_research_scope import ResolvedResearchScope
from ...schemas.topic_literature import (
    TopicLensSourceFamily,
    TopicSourceProfile,
    TopicSourceQuery,
    TopicSourceQueryPlan,
)
from .openalex_scope import OPENALEX_FIELD_FILTER_KEY
from .topic_sources import (
    GENERIC_TOPIC_EVIDENCE_PLAN_ID_PREFIXES,
    GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSIONS,
    _source_families_for_profile,
    resolve_topic_source_profile,
)

# v3 supersedes v2 because what is queried changed: the OpenAlex request may now carry the user's
# own research field as an additional structural condition, so a v3 plan id and a v2 plan id can
# name genuinely different literature for the same terms. The accepted-version tuple in
# ``topic_sources`` keeps v2 readable, and a guard test pins this constant inside it -- the
# selection branch there matches on the version string, so a bump that forgot the tuple would
# silently route the generic plan down the legacy selection path instead of failing.
GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSION = "generic_topic_evidence_lanes/v3"
GENERIC_TOPIC_EVIDENCE_PLAN_ID_PREFIX = "generic-topic-evidence-plan-v3-"
GENERIC_SCOPE_TERM_QUERY_LANE = "scope_term_acquisition"
#: The lane a reuse query is filed under. It is one of the eight reviewer dimensions by name,
#: so `_lane_from_query_id` already resolves it and the coverage tally already counts it.
DATASET_REUSE_QUERY_LANE = "dataset_resource_reuse"

#: Records this protocol asks each scope-term lane for. Named rather than left a bare literal in the
#: signature below because the preflight pool check refuses a term that cannot fill it, and a quota
#: the check and the plan disagreed about would refuse or admit the wrong runs.
#: Raised from 8 on 2026-08-17, measured rather than guessed. Harvesting the ibl derived scope with
#: the cap in place returned 344 raw hits across 60 queries -- and **40 of those 60 queries came back
#: with exactly 8**, i.e. the ceiling, not the literature, decided what they returned. Same number of
#: HTTP requests either way; only the rows-per-request changes, so this is free in traffic and in
#: money. It is NOT free in usefulness on its own: the candidate pool caps what survives, so this
#: constant and `TOPIC_SOURCE_CANDIDATE_POOL` only pay off together.
GENERIC_TOPIC_MAX_RESULTS_PER_QUERY = 16

__all__ = [
    "DATASET_REUSE_QUERY_LANE",
    "GENERIC_REQUIRED_LANES",
    "GENERIC_SCOPE_TERM_QUERY_LANE",
    "GENERIC_TOPIC_EVIDENCE_PLAN_ID_PREFIX",
    "GENERIC_TOPIC_EVIDENCE_PLAN_ID_PREFIXES",
    "GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSION",
    "GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSIONS",
    "GENERIC_TOPIC_LANES",
    "GENERIC_TOPIC_MAX_RESULTS_PER_QUERY",
    "OPENALEX_FIELD_FILTER_KEY",
    "build_generic_topic_evidence_query_plan",
]

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
    max_results_per_query: int = GENERIC_TOPIC_MAX_RESULTS_PER_QUERY,
    openalex_field_id: str = "",
) -> TopicSourceQueryPlan:
    """Build one domain-neutral acquisition lineage per source family and unique scope term.

    The eight generic scientific dimensions remain reviewer criteria. They are deliberately not
    query identities: repeating one search under eight labels manufactured coverage without
    acquiring any additional evidence.

    ``openalex_field_id`` is the user's own field as OpenAlex identifies it. It defaults to absent
    and it fails open: without it this builds byte-identical queries, and byte-identical query ids,
    to the ones this function built before the parameter existed.
    """
    resolved_profile = resolve_topic_source_profile(source_profile, elicit_api_key=elicit_api_key)
    families = list(source_families or _source_families_for_profile(resolved_profile))
    terms = _unique_scope_terms(scope.terms)
    field_id = openalex_field_id.strip()
    queries: list[TopicSourceQuery] = []
    for family in families:
        is_elicit = family == TopicLensSourceFamily.ELICIT
        # OpenAlex filters are comma-AND-able, so the user's field is one more condition on the same
        # request: no extra call and no extra cost. No other family exposes an equivalent taxonomy
        # filter, so for them this correction does not apply and their queries are unchanged.
        filters = (
            {OPENALEX_FIELD_FILTER_KEY: field_id}
            if field_id and family == TopicLensSourceFamily.OPENALEX
            else {}
        )
        for term in terms:
            # One exact scope phrase per query. OpenAlex's title-and-abstract phrase search then
            # retrieves works about that term instead of documents containing a large AND-ed bag of
            # words. Ambiguity ACROSS fields is answered by the field condition above; ambiguity
            # left after it remains isolated to its own lineage for later scientific review.
            queries.append(
                TopicSourceQuery(
                    query_id=(
                        f"generic-topic-{family.value}-{GENERIC_SCOPE_TERM_QUERY_LANE}-"
                        f"{stable_hash(_query_identity(family, term, filters))[:8]}"
                    ),
                    source_family=family,
                    query=term,
                    query_lane=GENERIC_SCOPE_TERM_QUERY_LANE,
                    topic_terms=[term],
                    filters=filters,
                    max_results=max_results_per_query,
                    corpus="elicit" if is_elicit else "",
                    search_mode="semantic" if is_elicit else "",
                )
            )
        # The single dimension that gets its own lineage, and the reason it needs one. The eight
        # dimensions are reviewer criteria and deliberately not query identities -- repeating one
        # search under eight labels manufactured coverage without acquiring evidence. But
        # `dataset_resource_reuse` asks who has already used a resource like this one, and that is
        # answered by the name a citing paper writes, not by the constructs the dataset is about.
        # The deriver is told, correctly, to keep instrument, software and consortium names OUT of
        # the scope terms, so no scope query can carry that vocabulary and the dimension had no
        # retrieval path at all: measured on two legs, every reuse record present arrived by luck
        # through some other term, and the reviewer blocked on `essential evidence absent` for it.
        for identity_term in _unique_scope_terms(scope.dataset_identity_terms):
            queries.append(
                TopicSourceQuery(
                    query_id=(
                        f"generic-topic-{family.value}-{DATASET_REUSE_QUERY_LANE}-"
                        f"{stable_hash(_query_identity(family, identity_term, filters))[:8]}"
                    ),
                    source_family=family,
                    query=identity_term,
                    query_lane=DATASET_REUSE_QUERY_LANE,
                    topic_terms=[identity_term],
                    filters=filters,
                    max_results=max_results_per_query,
                    corpus="elicit" if is_elicit else "",
                    search_mode="semantic" if is_elicit else "",
                )
            )
    plan_identity = {
        "version": GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSION,
        "dataset_identity_terms": list(scope.dataset_identity_terms),
        "profile": resolved_profile.value,
        "terms": terms,
        "families": [family.value for family in families],
        "max_results_per_query": max_results_per_query,
        "queries": [query.model_dump(mode="json") for query in queries],
    }
    return TopicSourceQueryPlan(
        plan_id=(f"{GENERIC_TOPIC_EVIDENCE_PLAN_ID_PREFIX}{stable_hash(plan_identity)[:12]}"),
        source_profile=resolved_profile,
        topic_terms=terms,
        queries=queries,
        prompt_version=GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSION,
    )


def _query_identity(
    family: TopicLensSourceFamily, query_text: str, filters: Mapping[str, str]
) -> dict[str, object]:
    """The identity a query id hashes.

    ``filters`` joins the hash only when there is one. An empty mapping would still change the
    digest of every query id in every existing run for a request that is byte-identical on the wire,
    and a default that means "unchanged" must not move an identity.
    """

    identity: dict[str, object] = {"family": family.value, "query": query_text}
    if filters:
        identity["filters"] = dict(sorted(filters.items()))
    return identity


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
