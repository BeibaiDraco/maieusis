from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path
from typing import Any

from ...io import load_data
from ...provenance import stable_hash
from ...schemas.research_intent import ResearchIntent
from ...schemas.topic_literature import (
    TopicLensSourceFamily,
    TopicSourceElicitQueryMode,
    TopicSourceProfile,
    TopicSourceQuery,
    TopicSourceQueryPlan,
    TopicSourceRecord,
    TopicSourceSearchTrace,
    TopicSourceTable,
)
from .literature_prior_search import _exception_message, _http_get_json

JsonGetter = Callable[[str, dict[str, str]], dict[str, Any]]
JsonPoster = Callable[[str, dict[str, Any], dict[str, str]], "JsonPostResponse"]

TOPIC_SOURCE_QUERY_PLAN_VERSION = "topic_source_query_plan/v1"
R5_TOPIC_EVIDENCE_QUERY_PLAN_VERSION = "r5_topic_evidence_lanes/v1"
R5_TOPIC_SEED_SOURCE_CONFIG = Path("config/r5/topic_seed_sources/coding_geometry_bwm.yml")

PUBLIC_TOPIC_SOURCE_FAMILIES = [
    TopicLensSourceFamily.PUBMED,
    TopicLensSourceFamily.OPENALEX,
    TopicLensSourceFamily.CROSSREF,
    TopicLensSourceFamily.SEMANTIC_SCHOLAR,
]


@dataclass(frozen=True)
class JsonPostResponse:
    payload: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)
    status_code: int = 200


def build_topic_source_query_plan(
    intent: ResearchIntent,
    *,
    source_families: Iterable[TopicLensSourceFamily] | None = None,
    source_profile: TopicSourceProfile | str = TopicSourceProfile.PUBLIC,
    elicit_api_key: str = "",
    max_results_per_query: int = 5,
    elicit_query_mode: TopicSourceElicitQueryMode | str = TopicSourceElicitQueryMode.BROAD,
    elicit_max_results_per_query: int = 50,
) -> TopicSourceQueryPlan:
    """Build small online-source queries for pre-generation TopicLens background."""

    resolved_profile = resolve_topic_source_profile(
        source_profile,
        elicit_api_key=elicit_api_key,
    )
    families = list(source_families or _source_families_for_profile(resolved_profile))
    terms = _intent_terms(intent)
    queries: list[TopicSourceQuery] = []
    parsed_elicit_mode = TopicSourceElicitQueryMode(str(elicit_query_mode))
    for family in families:
        if family == TopicLensSourceFamily.ELICIT:
            queries.extend(
                _elicit_queries(
                    terms,
                    max_results=elicit_max_results_per_query,
                    query_mode=parsed_elicit_mode,
                )
            )
            continue
        for index, query_text in enumerate(_public_background_queries(terms), start=1):
            queries.append(
                TopicSourceQuery(
                    query_id=f"topic-source-{family.value}-{stable_hash({'family': family, 'query': query_text})[:8]}",
                    source_family=family,
                    query=query_text,
                    query_lane=f"background_{index}",
                    topic_terms=terms,
                    max_results=max_results_per_query,
                )
            )
    return TopicSourceQueryPlan(
        plan_id=f"topic-source-plan-{stable_hash({'terms': terms, 'profile': resolved_profile.value, 'queries': [item.model_dump(mode='json') for item in queries]})[:12]}",
        source_profile=resolved_profile,
        topic_terms=terms,
        queries=queries,
        prompt_version=TOPIC_SOURCE_QUERY_PLAN_VERSION,
    )


def build_r5_topic_evidence_query_plan(
    intent: ResearchIntent,
    *,
    source_families: Iterable[TopicLensSourceFamily] | None = None,
    source_profile: TopicSourceProfile | str = TopicSourceProfile.PUBLIC,
    elicit_api_key: str = "",
    max_results_per_query: int = 8,
) -> TopicSourceQueryPlan:
    """Build lane-specific public literature queries for TopicEvidenceBrief."""

    resolved_profile = resolve_topic_source_profile(
        source_profile,
        elicit_api_key=elicit_api_key,
    )
    families = list(source_families or _source_families_for_profile(resolved_profile))
    terms = _intent_terms(intent)
    lane_specs = _r5_topic_lane_specs(intent, terms)
    queries: list[TopicSourceQuery] = []
    for family in families:
        for lane, raw_query in lane_specs:
            provider_query = _r5_provider_query(raw_query, lane=lane, family=family)
            queries.append(
                TopicSourceQuery(
                    query_id=(
                        f"r5-topic-{family.value}-{lane}-"
                        f"{stable_hash({'family': family.value, 'lane': lane, 'query': provider_query})[:8]}"
                    ),
                    source_family=family,
                    query=provider_query,
                    query_lane=lane,
                    topic_terms=terms,
                    max_results=max_results_per_query,
                    corpus="elicit" if family == TopicLensSourceFamily.ELICIT else "",
                    search_mode="semantic" if family == TopicLensSourceFamily.ELICIT else "",
                )
            )
    return TopicSourceQueryPlan(
        plan_id=f"r5-topic-evidence-plan-{stable_hash({'terms': terms, 'profile': resolved_profile.value, 'queries': [item.model_dump(mode='json') for item in queries]})[:12]}",
        source_profile=resolved_profile,
        topic_terms=terms,
        queries=queries,
        prompt_version=R5_TOPIC_EVIDENCE_QUERY_PLAN_VERSION,
    )


def resolve_topic_source_profile(
    profile: TopicSourceProfile | str,
    *,
    elicit_api_key: str = "",
) -> TopicSourceProfile:
    parsed = TopicSourceProfile(str(profile))
    if parsed != TopicSourceProfile.AUTO:
        return parsed
    key = elicit_api_key or os.getenv("ELICIT_API_KEY", "")
    return TopicSourceProfile.HYBRID if key else TopicSourceProfile.PUBLIC


class TopicSourceHarvester:
    """Retrieve compact online source records for TopicLens synthesis."""

    def __init__(
        self,
        *,
        http_get_json: JsonGetter | None = None,
        http_post_json: JsonPoster | None = None,
        enabled: bool = True,
        max_records: int = 20,
        elicit_api_key: str = "",
    ):
        self.http_get_json = http_get_json or _http_get_json
        self.http_post_json = http_post_json or _http_post_json
        self.enabled = enabled
        self.max_records = max_records
        self.elicit_api_key = elicit_api_key or os.getenv("ELICIT_API_KEY", "")

    def harvest(self, query_plan: TopicSourceQueryPlan) -> TopicSourceTable:
        records: list[TopicSourceRecord] = []
        traces: list[TopicSourceSearchTrace] = []
        for query in query_plan.queries:
            if not self.enabled:
                traces.append(
                    TopicSourceSearchTrace(
                        trace_id=_trace_id(query, "disabled"),
                        source_family=query.source_family,
                        query_id=query.query_id,
                        errors=["topic source search disabled"],
                    )
                )
                continue
            try:
                query_records, trace = self._search_query(query)
                records.extend(query_records)
                traces.append(trace)
            except Exception as exc:
                traces.append(
                    TopicSourceSearchTrace(
                        trace_id=_trace_id(query, "error"),
                        source_family=query.source_family,
                        query_id=query.query_id,
                        errors=[_exception_message(exc)],
                    )
                )
        if query_plan.prompt_version == R5_TOPIC_EVIDENCE_QUERY_PLAN_VERSION:
            records = self._enrich_r5_doi_records(_dedupe_records(records))
            filtered_records = _filter_topic_relevant_records(
                records,
                query_plan.topic_terms,
                strict_r5=True,
            )
            records = _select_r5_lane_preserving_records(
                all_records=records,
                relevant_records=_dedupe_records(filtered_records),
                query_plan=query_plan,
                max_records=self.max_records,
            )
        else:
            filtered_records = _filter_topic_relevant_records(
                records,
                query_plan.topic_terms,
                strict_r5=False,
            )
            records = _dedupe_records(filtered_records)[: self.max_records]
        return TopicSourceTable(
            table_id=f"topic-source-table-{stable_hash({'plan': query_plan.plan_id, 'records': [item.model_dump(mode='json') for item in records], 'traces': [item.model_dump(mode='json') for item in traces]})[:12]}",
            query_plan_id=query_plan.plan_id,
            topic_terms=query_plan.topic_terms,
            records=records,
            search_traces=traces,
            max_records=self.max_records,
        )

    def _enrich_r5_doi_records(self, records: list[TopicSourceRecord]) -> list[TopicSourceRecord]:
        enriched: list[TopicSourceRecord] = []
        for record in records:
            if (
                record.doi
                and _record_needs_abstract_enrichment(record)
                and not _retrieval_record_is_secondary_artifact(record)
            ):
                enriched.append(self._enrich_record_from_doi(record))
            else:
                enriched.append(record)
        return enriched

    def _enrich_record_from_doi(self, record: TopicSourceRecord) -> TopicSourceRecord:
        updates: dict[str, Any] = {}
        evidence_hashes: list[str] = []
        abstract = ""
        confirmations = set(record.confirmed_source_families or [record.source_family])
        detail_sources = [
            (
                "https://api.crossref.org/works/" + urllib.parse.quote(record.doi, safe=""),
                TopicLensSourceFamily.CROSSREF,
            ),
        ]
        if _record_has_any_lane(
            record,
            {
                "geometry_theory_methods",
                "noise_shared_variability_geometry",
                "latent_dynamics_state_space",
                "circuit_interpretation",
                "ibl_bwm_public_reuse",
            },
        ):
            detail_sources.append(
                (
                    "https://api.semanticscholar.org/graph/v1/paper/DOI:"
                    + urllib.parse.quote(record.doi, safe="")
                    + "?fields=title,abstract,year,authors,url,externalIds",
                    TopicLensSourceFamily.SEMANTIC_SCHOLAR,
                )
            )
        detail_sources.append(
            (
                "https://api.openalex.org/works/https://doi.org/"
                + urllib.parse.quote(record.doi, safe=""),
                TopicLensSourceFamily.OPENALEX,
            )
        )

        for url, family in detail_sources:
            try:
                payload = self.http_get_json(url, {})
            except Exception:
                continue
            evidence_hashes.append(stable_hash(payload))
            confirmations.add(family)
            if family == TopicLensSourceFamily.CROSSREF:
                message = payload.get("message", {})
                abstract = abstract or _strip_jats(str(message.get("abstract") or ""))
                updates["url"] = record.url or str(message.get("URL") or "")
            elif family == TopicLensSourceFamily.OPENALEX:
                abstract = abstract or _openalex_abstract(payload)
                updates["openalex_id"] = record.openalex_id or str(payload.get("id") or "")
                ids = payload.get("ids") or {}
                updates["pmid"] = record.pmid or _pmid_from_url(str(ids.get("pmid") or ""))
                primary_location = payload.get("primary_location") or {}
                updates["url"] = updates.get("url") or str(
                    primary_location.get("landing_page_url") or payload.get("id") or ""
                )
                updates["cited_by_count"] = record.cited_by_count or _optional_int(
                    payload.get("cited_by_count")
                )
            else:
                abstract = abstract or str(payload.get("abstract") or "")
                updates["semantic_scholar_id"] = record.semantic_scholar_id or str(
                    payload.get("paperId") or ""
                )
                ids = payload.get("externalIds") or {}
                updates["pmid"] = record.pmid or str(ids.get("PubMed") or "")
                updates["url"] = updates.get("url") or str(payload.get("url") or "")
                if abstract:
                    break

        if not abstract:
            return record
        updates.update(
            {
                "snippet": abstract[:800],
                "confirmed_source_families": sorted(confirmations, key=lambda item: item.value),
                "metadata_quality_score": max(
                    record.metadata_quality_score,
                    _metadata_quality(record.source_locator, record.title, record.year, abstract),
                ),
                "source_payload_hash": stable_hash(
                    {
                        "record": record.source_payload_hash,
                        "doi_detail_response_hashes": evidence_hashes,
                    }
                ),
            }
        )
        return record.model_copy(update=updates)

    def _search_query(
        self, query: TopicSourceQuery
    ) -> tuple[list[TopicSourceRecord], TopicSourceSearchTrace]:
        if query.source_family == TopicLensSourceFamily.PUBMED:
            return self._search_pubmed(query)
        if query.source_family == TopicLensSourceFamily.OPENALEX:
            return self._search_openalex(query)
        if query.source_family == TopicLensSourceFamily.CROSSREF:
            return self._search_crossref(query)
        if query.source_family == TopicLensSourceFamily.SEMANTIC_SCHOLAR:
            return self._search_semantic_scholar(query)
        if query.source_family == TopicLensSourceFamily.ELICIT:
            return self._search_elicit(query)
        return (
            [],
            TopicSourceSearchTrace(
                trace_id=_trace_id(query, "unsupported"),
                source_family=query.source_family,
                query_id=query.query_id,
                errors=[f"unsupported topic source family: {query.source_family.value}"],
            ),
        )

    def _search_pubmed(
        self, query: TopicSourceQuery
    ) -> tuple[list[TopicSourceRecord], TopicSourceSearchTrace]:
        params = urllib.parse.urlencode(
            {
                "db": "pubmed",
                "retmode": "json",
                "retmax": str(query.max_results),
                "sort": "relevance",
                "term": query.query,
            }
        )
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}"
        search = self.http_get_json(search_url, {})
        ids = search.get("esearchresult", {}).get("idlist", [])
        if not ids:
            return [], _trace(query, search_url, search, 0)
        summary_params = urllib.parse.urlencode(
            {"db": "pubmed", "retmode": "json", "id": ",".join(str(item) for item in ids)}
        )
        summary_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + summary_params
        )
        summary = self.http_get_json(summary_url, {})
        records = []
        for pmid in ids:
            item = summary.get("result", {}).get(str(pmid), {})
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            records.append(
                _record(
                    source_family=TopicLensSourceFamily.PUBMED,
                    query=query,
                    title=title,
                    year=_year(item.get("pubdate")),
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    pmid=str(pmid),
                    doi=_article_id(item, "doi"),
                    publication_types=[
                        str(pubtype) for pubtype in item.get("pubtype", []) if pubtype
                    ],
                    venue=str(item.get("fulljournalname") or item.get("source") or ""),
                    snippet="",
                    payload=item,
                    relevance_score=0.85,
                )
            )
        return records, _trace(query, summary_url, summary, len(records))

    def _search_openalex(
        self, query: TopicSourceQuery
    ) -> tuple[list[TopicSourceRecord], TopicSourceSearchTrace]:
        params = urllib.parse.urlencode(
            {
                "search": query.query,
                "per-page": str(query.max_results),
                "sort": "relevance_score:desc",
            }
        )
        url = f"https://api.openalex.org/works?{params}"
        raw = self.http_get_json(url, {})
        records = [
            _record(
                source_family=TopicLensSourceFamily.OPENALEX,
                query=query,
                title=str(item.get("display_name") or item.get("title") or "").strip(),
                year=item.get("publication_year"),
                url=(
                    (item.get("primary_location") or {}).get("landing_page_url")
                    or item.get("id")
                    or ""
                ),
                doi=_normalize_doi(item.get("doi") or ""),
                openalex_id=str(item.get("id") or ""),
                publication_types=[str(item.get("type") or "")],
                snippet=_openalex_abstract(item),
                payload=item,
                relevance_score=float(item.get("relevance_score") or 0.75),
            )
            for item in raw.get("results", [])
            if str(item.get("display_name") or item.get("title") or "").strip()
        ]
        return records, _trace(query, url, raw, len(records))

    def _search_crossref(
        self, query: TopicSourceQuery
    ) -> tuple[list[TopicSourceRecord], TopicSourceSearchTrace]:
        params = urllib.parse.urlencode(
            {
                "query.bibliographic": query.query,
                "rows": str(query.max_results),
                "sort": "relevance",
            }
        )
        url = f"https://api.crossref.org/works?{params}"
        raw = self.http_get_json(url, {})
        records = []
        for item in raw.get("message", {}).get("items", []):
            title = str((item.get("title") or [""])[0]).strip()
            if not title:
                continue
            records.append(
                _record(
                    source_family=TopicLensSourceFamily.CROSSREF,
                    query=query,
                    title=title,
                    year=_crossref_year(item),
                    url=str(item.get("URL") or ""),
                    doi=_normalize_doi(item.get("DOI") or ""),
                    publication_types=[str(item.get("type") or "")],
                    venue=str((item.get("container-title") or [""])[0]),
                    snippet=_strip_jats(str(item.get("abstract") or "")),
                    payload=item,
                    relevance_score=float(item.get("score") or 0.5),
                )
            )
        return records, _trace(query, url, raw, len(records))

    def _search_semantic_scholar(
        self, query: TopicSourceQuery
    ) -> tuple[list[TopicSourceRecord], TopicSourceSearchTrace]:
        params = urllib.parse.urlencode(
            {
                "query": query.query,
                "limit": str(query.max_results),
                "fields": "title,year,url,abstract,externalIds,publicationTypes,fieldsOfStudy",
            }
        )
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?{params}"
        raw = self.http_get_json(url, {})
        records = []
        for item in raw.get("data", []):
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            external = item.get("externalIds") or {}
            records.append(
                _record(
                    source_family=TopicLensSourceFamily.SEMANTIC_SCHOLAR,
                    query=query,
                    title=title,
                    year=item.get("year"),
                    url=str(item.get("url") or ""),
                    doi=_normalize_doi(external.get("DOI") or ""),
                    pmid=str(external.get("PubMed") or ""),
                    semantic_scholar_id=str(item.get("paperId") or ""),
                    publication_types=[
                        str(pubtype) for pubtype in (item.get("publicationTypes") or []) if pubtype
                    ],
                    snippet=str(item.get("abstract") or "")[:600],
                    payload=item,
                    relevance_score=0.7,
                )
            )
        return records, _trace(query, url, raw, len(records))

    def _search_elicit(
        self, query: TopicSourceQuery
    ) -> tuple[list[TopicSourceRecord], TopicSourceSearchTrace]:
        url = "https://elicit.com/api/v1/search"
        body = {
            "query": query.query,
            "searchMode": query.search_mode or "semantic",
            "maxResults": query.max_results,
            "corpus": query.corpus or "elicit",
        }
        if not self.elicit_api_key:
            return (
                [],
                _trace(
                    query,
                    url,
                    {"error": {"message": "ELICIT_API_KEY is not set"}},
                    0,
                    request_method="POST",
                    request_body=body,
                    errors=["ELICIT_API_KEY is not set; Elicit search skipped"],
                ),
            )
        response = self.http_post_json(
            url,
            body,
            {
                "Authorization": f"Bearer {self.elicit_api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "maieusis/0.1.0 (+https://github.com/BeibaiDraco/maieusis)",
            },
        )
        warnings = _elicit_warnings(response.payload)
        if response.status_code >= 400:
            return (
                [],
                _trace(
                    query,
                    url,
                    response.payload,
                    0,
                    request_method="POST",
                    request_body=body,
                    http_status=response.status_code,
                    warnings=warnings,
                    errors=[_elicit_error_message(response.status_code, response.payload)],
                    response_headers=response.headers,
                ),
            )
        records = []
        for index, item in enumerate(response.payload.get("papers", []), start=1):
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            urls = [str(value) for value in item.get("urls", []) if value]
            records.append(
                _record(
                    source_family=TopicLensSourceFamily.ELICIT,
                    query=query,
                    title=title,
                    year=item.get("year"),
                    url=urls[0] if urls else "",
                    doi=_normalize_doi(str(item.get("doi") or "")),
                    pmid=str(item.get("pmid") or ""),
                    elicit_id=str(item.get("elicitId") or ""),
                    venue=str(item.get("venue") or ""),
                    authors=[str(author) for author in item.get("authors", []) if author],
                    cited_by_count=_optional_int(item.get("citedByCount")),
                    publication_types=["Elicit paper search"],
                    snippet=str(item.get("abstract") or "")[:800],
                    payload=item,
                    relevance_score=max(0.1, 0.95 - (index - 1) * 0.01),
                )
            )
        return (
            records,
            _trace(
                query,
                url,
                response.payload,
                len(records),
                request_method="POST",
                request_body=body,
                http_status=response.status_code,
                warnings=warnings,
                response_headers=response.headers,
            ),
        )


def _intent_terms(intent: ResearchIntent) -> list[str]:
    terms = [
        *(intent.topic_terms or []),
        *intent.include_concepts,
        *intent.target_constructs,
        *intent.target_events,
        *_safe_public_region_terms(intent.target_regions),
    ]
    normalized = [term.strip() for term in terms if term.strip()]
    return normalized or ["systems neuroscience"]


def _r5_topic_lane_specs(intent: ResearchIntent, terms: list[str]) -> list[tuple[str, str]]:
    theme = intent.theme or " ".join(terms) or "coding geometry in neural population activity"
    constructs = " ".join(intent.target_constructs or ["neural activity"])
    specs = [
        (
            "geometry_theory_methods",
            f"{theme} representational geometry population coding neural manifolds dimensionality reduction",
        ),
        (
            "noise_shared_variability_geometry",
            (
                "noise correlations shared variability trial-to-trial covariability "
                "neural population covariance geometry"
            ),
        ),
        (
            "latent_dynamics_state_space",
            f"{theme} neural state space latent dynamics population dynamics behavior",
        ),
        (
            "multi_area_coding_communication",
            f"multi-area neural coding inter-area communication distributed representations {constructs}",
        ),
        (
            "temporal_latency_dynamics",
            f"{theme} latency temporal evolution population trajectories neural code dynamics",
        ),
        (
            "circuit_interpretation",
            (
                "neural manifolds circuits circuit interpretation population geometry "
                "systems neuroscience"
            ),
        ),
        (
            "movement_body_state_confound",
            f"{theme} movement body state behavioral state confound neural activity",
        ),
        (
            "ibl_bwm_public_reuse",
            (
                "International Brain Laboratory Brain Wide Map public dataset reuse "
                "coding geometry population analysis"
            ),
        ),
        (
            "cross_subject_session_lab_generalization",
            f"{theme} reproducibility generalization across subjects sessions laboratories",
        ),
        (
            "close_priors_already_answered",
            f"{theme} noise covariance latent dynamics public dataset already known close prior",
        ),
        (
            "live_tensions_and_limitations",
            f"{theme} unresolved debate limitation open question noise correlations neural manifolds",
        ),
    ]
    specs.extend(_r5_seed_lane_specs(R5_TOPIC_SEED_SOURCE_CONFIG))
    return _dedupe_lane_specs(specs)


def _r5_seed_lane_specs(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    loaded = load_data(path) or {}
    lanes = loaded.get("lanes", {})
    if not isinstance(lanes, dict):
        return []
    specs: list[tuple[str, str]] = []
    for lane, entries in lanes.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("curator_slot"):
                continue
            title = str(entry.get("title") or "").strip()
            doi = str(entry.get("doi") or "").strip()
            query = " ".join(value for value in [title, doi] if value).strip()
            if query:
                specs.append((str(lane), query))
    return specs


def _dedupe_lane_specs(specs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    output: list[tuple[str, str]] = []
    for lane, query in specs:
        cleaned = " ".join(query.split())
        key = (lane, cleaned.lower())
        if lane and cleaned and key not in seen:
            seen.add(key)
            output.append((lane, cleaned))
    return output


def _expanded_region_terms(regions: list[str]) -> list[str]:
    aliases = {
        "CP": "caudoputamen striatum basal ganglia",
        "PO": "posterior thalamic complex thalamus",
        "LP": "lateral posterior thalamus visual thalamus",
    }
    expanded: list[str] = []
    for region in regions:
        cleaned = region.strip()
        if not cleaned:
            continue
        expanded.append(aliases.get(cleaned.upper(), cleaned))
    return expanded


def _r5_provider_query(
    raw_query: str,
    *,
    lane: str,
    family: TopicLensSourceFamily,
) -> str:
    normalized = _normalize_query_term(raw_query)
    if family != TopicLensSourceFamily.PUBMED:
        return normalized
    terms = _pubmed_terms_for_lane(lane, normalized)
    return " AND ".join(f"({part})" for part in terms if part)


def _pubmed_terms_for_lane(lane: str, raw_query: str) -> list[str]:
    base = (
        '("neural activity"[Title/Abstract] OR "neural signal"[Title/Abstract] OR '
        "neuroscience[Title/Abstract] OR brain[Title/Abstract])"
    )
    lane_terms = {
        "geometry_theory_methods": (
            '("coding geometry"[Title/Abstract] OR "representational geometry"[Title/Abstract] OR '
            '"population geometry"[Title/Abstract] OR manifold[Title/Abstract] OR '
            '"dimensionality reduction"[Title/Abstract])'
        ),
        "noise_shared_variability_geometry": (
            '("noise correlation"[Title/Abstract] OR "noise correlations"[Title/Abstract] OR '
            '"shared variability"[Title/Abstract] OR covariability[Title/Abstract] OR '
            "covariance[Title/Abstract])"
        ),
        "latent_dynamics_state_space": (
            '("latent dynamics"[Title/Abstract] OR "state space"[Title/Abstract] OR '
            '"population dynamics"[Title/Abstract] OR "neural trajectory"[Title/Abstract])'
        ),
        "multi_area_coding_communication": (
            '("multi-area"[Title/Abstract] OR "inter-area"[Title/Abstract] OR '
            "distributed[Title/Abstract] OR communication[Title/Abstract])"
        ),
        "temporal_latency_dynamics": (
            "(latency[Title/Abstract] OR temporal[Title/Abstract] OR "
            "trajectory[Title/Abstract] OR dynamics[Title/Abstract])"
        ),
        "circuit_interpretation": (
            "(circuit[Title/Abstract] OR circuits[Title/Abstract] OR "
            "connectivity[Title/Abstract] OR mechanism[Title/Abstract])"
        ),
        "movement_body_state_confound": (
            "(movement[Title/Abstract] OR motor[Title/Abstract] OR "
            '"body state"[Title/Abstract] OR confound[Title/Abstract])'
        ),
        "ibl_bwm_public_reuse": (
            '("International Brain Laboratory"[Title/Abstract] OR IBL[Title/Abstract] OR '
            '"Brain Wide Map"[Title/Abstract] OR "brain-wide map"[Title/Abstract] OR '
            '"reproducible ephys"[Title/Abstract])'
        ),
        "cross_subject_session_lab_generalization": (
            "(reproducibility[Title/Abstract] OR generalization[Title/Abstract] OR "
            "session[Title/Abstract] OR laboratory[Title/Abstract])"
        ),
        "close_priors_already_answered": (
            '("coding geometry"[Title/Abstract] OR "population geometry"[Title/Abstract] OR '
            '"public dataset"[Title/Abstract] OR "latent dynamics"[Title/Abstract])'
        ),
        "live_tensions_and_limitations": (
            "(unresolved[Title/Abstract] OR debate[Title/Abstract] OR "
            'limitation[Title/Abstract] OR "open question"[Title/Abstract] OR '
            '"noise correlation"[Title/Abstract] OR manifold[Title/Abstract])'
        ),
    }
    return [lane_terms.get(lane, raw_query), base]


def _source_families_for_profile(profile: TopicSourceProfile) -> list[TopicLensSourceFamily]:
    if profile == TopicSourceProfile.PUBLIC:
        return list(PUBLIC_TOPIC_SOURCE_FAMILIES)
    if profile == TopicSourceProfile.ELICIT:
        return [TopicLensSourceFamily.ELICIT]
    if profile == TopicSourceProfile.HYBRID:
        return [TopicLensSourceFamily.ELICIT, *PUBLIC_TOPIC_SOURCE_FAMILIES]
    return list(PUBLIC_TOPIC_SOURCE_FAMILIES)


def _public_background_query(terms: list[str]) -> str:
    return _public_background_queries(terms)[0]


def _public_background_queries(terms: list[str]) -> list[str]:
    core = " ".join(_normalize_query_term(term) for term in terms[:5]).strip()
    if not core:
        core = "systems neuroscience"
    primary = _normalize_query_term(terms[0]) if terms else core
    concepts = " ".join(_normalize_query_term(term) for term in terms[1:4]).strip()
    queries = [
        f"{primary} systems neuroscience neural activity",
        f"{primary} neural recordings behavior reproducibility",
        f"{primary} measurement confound review",
    ]
    if concepts:
        queries.append(f"{primary} {concepts} systems neuroscience")
    lowered = f"{primary} {concepts}".lower()
    if "movement" in lowered or "decision" in lowered:
        queries.extend(
            [
                "movement decision-making neural activity motor confounds",
                "reproducible neural activity movement decision-making generalization",
            ]
        )
    if "coding" in lowered or "geometry" in lowered:
        queries.append("neural population coding representational geometry manifold")
    return _dedupe_query_texts(queries)


def _safe_public_region_terms(regions: list[str]) -> list[str]:
    safe: list[str] = []
    for region in regions:
        cleaned = region.strip()
        if not cleaned:
            continue
        if len(cleaned) <= 3 and cleaned.upper() == cleaned:
            continue
        safe.append(cleaned)
    return safe


def _normalize_query_term(term: str) -> str:
    return " ".join(term.replace("_", " ").split())


def _dedupe_query_texts(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = " ".join(value.split())
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output


def _elicit_queries(
    terms: list[str],
    *,
    max_results: int,
    query_mode: TopicSourceElicitQueryMode,
) -> list[TopicSourceQuery]:
    if query_mode == TopicSourceElicitQueryMode.BROAD:
        return [_elicit_broad_query(terms, max_results=max_results)]
    return _elicit_lane_queries(terms, max_results=max_results)


def _elicit_broad_query(terms: list[str], *, max_results: int) -> TopicSourceQuery:
    topic = _topic_phrase(terms)
    text = (
        "In systems neuroscience, what papers review, define, or empirically test "
        f"{topic}, including neural population coding, representational geometry, "
        "latent-variable or manifold analyses, state-space models, measurement methods, "
        "behavioral and motor confounds, and secondary analyses of large standardized "
        "neural datasets?"
    )
    return TopicSourceQuery(
        query_id=f"topic-source-elicit-broad_background-{stable_hash({'lane': 'broad_background', 'corpus': 'elicit', 'query': text})[:8]}",
        source_family=TopicLensSourceFamily.ELICIT,
        query=text,
        query_lane="broad_background",
        topic_terms=terms,
        max_results=max_results,
        corpus="elicit",
        search_mode="semantic",
    )


def _elicit_lane_queries(terms: list[str], *, max_results: int) -> list[TopicSourceQuery]:
    topic = _topic_phrase(terms)
    query_specs = [
        (
            "background_review",
            "elicit",
            "In systems neuroscience, what papers review or test "
            f"{topic}, including representational geometry, neural manifold structure, "
            "decision-making tasks, measurement approaches, and behavioral confounds?",
        ),
        (
            "construct_theory",
            "elicit",
            "What theoretical and empirical papers define the constructs behind "
            f"{topic} in neural population coding, representational geometry, or "
            "manifold learning?",
        ),
        (
            "measurement_operator",
            "elicit",
            "What papers describe measurements, statistical operators, or analysis "
            f"methods for studying {topic} in neural recordings or behavior?",
        ),
        (
            "confound_control",
            "elicit",
            "What papers identify behavioral, motor, sensory, sampling, or session-level "
            f"confounds when interpreting {topic} in systems neuroscience datasets?",
        ),
        (
            "dataset_reuse",
            "elicit",
            "What secondary analyses or dataset-reuse papers use large standardized "
            f"neuroscience datasets to ask new questions about {topic} or related constructs?",
        ),
    ]
    if _is_biomedical_topic(terms):
        query_specs.append(
            (
                "pubmed_background",
                "pubmed",
                "In PubMed-indexed neuroscience papers, what reviews or empirical studies "
                f"connect {topic} to neural population coding, behavior, measurements, "
                "or confounds?",
            )
        )
    queries = []
    for lane, corpus, text in query_specs:
        queries.append(
            TopicSourceQuery(
                query_id=f"topic-source-elicit-{lane}-{stable_hash({'lane': lane, 'corpus': corpus, 'query': text})[:8]}",
                source_family=TopicLensSourceFamily.ELICIT,
                query=text,
                query_lane=lane,
                topic_terms=terms,
                max_results=max_results,
                corpus=corpus,
                search_mode="semantic",
            )
        )
    return queries


def _topic_phrase(terms: list[str]) -> str:
    filtered = [term for term in terms if term.lower() != "open"]
    if not filtered:
        return "systems neuroscience research questions"
    return ", ".join(filtered[:6])


def _is_biomedical_topic(terms: list[str]) -> bool:
    text = " ".join(terms).lower()
    markers = [
        "brain",
        "neural",
        "neuron",
        "neuroscience",
        "behavior",
        "behaviour",
        "coding",
        "manifold",
        "ibl",
        "bwm",
        "mouse",
        "visual",
        "decision",
    ]
    return any(marker in text for marker in markers) or not text.strip()


def _record(
    *,
    source_family: TopicLensSourceFamily,
    query: TopicSourceQuery,
    title: str,
    payload: dict[str, Any],
    year: int | None = None,
    url: str = "",
    doi: str = "",
    pmid: str = "",
    pmcid: str = "",
    elicit_id: str = "",
    openalex_id: str = "",
    semantic_scholar_id: str = "",
    venue: str = "",
    authors: list[str] | None = None,
    cited_by_count: int | None = None,
    publication_types: list[str] | None = None,
    snippet: str = "",
    relevance_score: float = 0.0,
) -> TopicSourceRecord:
    locator = doi or pmid or pmcid or elicit_id or openalex_id or semantic_scholar_id or url
    payload_hash = stable_hash(payload)
    return TopicSourceRecord(
        source_record_id=f"topic-source-record-{stable_hash({'family': source_family, 'locator': locator, 'title': title})[:12]}",
        source_family=source_family,
        query_ids=[query.query_id],
        title=title,
        year=year,
        url=url,
        doi=doi,
        pmid=pmid,
        pmcid=pmcid,
        elicit_id=elicit_id,
        openalex_id=openalex_id,
        semantic_scholar_id=semantic_scholar_id,
        source_locator=locator,
        venue=venue,
        authors=authors or [],
        cited_by_count=cited_by_count,
        confirmed_source_families=[source_family],
        publication_types=[item for item in (publication_types or []) if item],
        snippet=snippet[:800],
        relevance_score=relevance_score,
        metadata_quality_score=_metadata_quality(locator, title, year, snippet),
        source_payload_hash=payload_hash,
    )


def _trace(
    query: TopicSourceQuery,
    request_url: str,
    response: dict[str, Any],
    candidate_count: int,
    *,
    request_method: str = "GET",
    request_body: dict[str, Any] | None = None,
    http_status: int | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    response_headers: dict[str, str] | None = None,
) -> TopicSourceSearchTrace:
    headers = response_headers or {}
    return TopicSourceSearchTrace(
        trace_id=_trace_id(query, response),
        source_family=query.source_family,
        query_id=query.query_id,
        request_url=request_url,
        request_method=request_method,
        request_body_hash=stable_hash(request_body) if request_body else "",
        http_status=http_status,
        response_hash=stable_hash(response),
        candidate_count=candidate_count,
        warnings=warnings or [],
        errors=errors or [],
        rate_limit_limit=_header_value(headers, "X-RateLimit-Limit"),
        rate_limit_remaining=_header_value(headers, "X-RateLimit-Remaining"),
        rate_limit_reset=_header_value(headers, "X-RateLimit-Reset"),
    )


def _trace_id(query: TopicSourceQuery, suffix: Any) -> str:
    return f"topic-source-trace-{stable_hash({'query': query.query_id, 'suffix': suffix})[:12]}"


def _dedupe_records(records: list[TopicSourceRecord]) -> list[TopicSourceRecord]:
    by_key: dict[str, TopicSourceRecord] = {}
    for record in sorted(
        records,
        key=lambda item: (-_record_quality(item), item.title.lower()),
    ):
        key = _dedupe_key(record)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = record
            continue
        by_key[key] = _merge_records(existing, record)
    return sorted(by_key.values(), key=lambda item: (-_record_quality(item), item.title.lower()))


def _select_r5_lane_preserving_records(
    *,
    all_records: list[TopicSourceRecord],
    relevant_records: list[TopicSourceRecord],
    query_plan: TopicSourceQueryPlan,
    max_records: int,
) -> list[TopicSourceRecord]:
    """Keep lane coverage before filling capacity without lexical hard-drops.

    Literal topic relevance is only a ranking signal on the active R5 route. Every adapter record
    here is still source-bound and remains eligible for downstream evidence review; paraphrase,
    negation, or unfamiliar vocabulary must not make it disappear before that review.
    """

    if not all_records or max_records <= 0:
        return []
    lane_order = _query_plan_lane_order(query_plan)
    lane_by_query = {query.query_id: query.query_lane for query in query_plan.queries}
    selected: dict[str, TopicSourceRecord] = {}

    target_per_lane = max(1, min(6, max_records // max(1, len(lane_order))))
    for lane in lane_order:
        candidates = _records_for_lane(relevant_records, lane=lane, lane_by_query=lane_by_query)
        candidates.extend(
            record
            for record in _records_for_lane(all_records, lane=lane, lane_by_query=lane_by_query)
            if _dedupe_key(record) not in {_dedupe_key(item) for item in candidates}
        )
        for record in candidates[:target_per_lane]:
            if len(selected) >= max_records:
                break
            selected.setdefault(_dedupe_key(record), record)

    for record in relevant_records:
        if len(selected) >= max_records:
            break
        selected.setdefault(_dedupe_key(record), record)

    for record in all_records:
        if len(selected) >= max_records:
            break
        selected.setdefault(_dedupe_key(record), record)

    return sorted(selected.values(), key=lambda item: (-_record_quality(item), item.title.lower()))


def _query_plan_lane_order(query_plan: TopicSourceQueryPlan) -> list[str]:
    lanes: list[str] = []
    for query in query_plan.queries:
        if query.query_lane and query.query_lane not in lanes:
            lanes.append(query.query_lane)
    return lanes


def _records_for_lane(
    records: list[TopicSourceRecord],
    *,
    lane: str,
    lane_by_query: dict[str, str],
) -> list[TopicSourceRecord]:
    lane_records = [
        record
        for record in records
        if any(lane_by_query.get(query_id) == lane for query_id in record.query_ids)
    ]
    return sorted(lane_records, key=lambda item: (-_record_quality(item), item.title.lower()))


def _filter_topic_relevant_records(
    records: list[TopicSourceRecord],
    topic_terms: list[str],
    *,
    strict_r5: bool = False,
) -> list[TopicSourceRecord]:
    tokens = _topic_relevance_tokens(topic_terms)
    filtered: list[TopicSourceRecord] = []
    for record in records:
        text = " ".join(
            [
                record.title,
                record.snippet,
                record.venue,
                " ".join(record.publication_types),
            ]
        ).lower()
        if strict_r5:
            keep = _is_r5_topic_relevant_text(text, tokens)
        else:
            keep = not tokens or any(token in text for token in tokens)
        if keep:
            filtered.append(record)
    return filtered


def _is_r5_topic_relevant_text(text: str, tokens: set[str]) -> bool:
    if _contains_any(
        text,
        [
            "metaverse",
            "cloud computing",
            "traffic optimization",
            "transportation mode",
            "dance/movement therapist",
            "dance therapy",
            "consumer",
            "marketing",
            "embryonic stem cell",
            "cerebral palsy",
        ],
    ):
        return False
    domain_core = _contains_any(
        text,
        [
            "neural",
            "neuron",
            "neuronal",
            "brain",
            "cortex",
            "striatal",
            "striatum",
            "caudoputamen",
            "thalam",
            "neuropixels",
            "electrophysiology",
            "spike",
            "population activity",
        ],
    )
    directness = _contains_any(
        text,
        [
            "movement",
            "motor",
            "action",
            "choice",
            "decision",
            "behavior",
            "reward",
            "feedback",
            "visual",
            "coding",
            "geometry",
            "representational",
            "covariability",
            "variability",
            "circuit",
            "dynamics",
            "caudoputamen",
            "striatum",
            "posterior thalam",
            "lateral posterior",
            "pulvinar",
            "decoding",
            "encoding",
            "latent",
            "population",
            "manifold",
            "international brain laboratory",
            "brain-wide map",
            "ibl",
            "bwm",
        ],
    )
    topic_match = not tokens or any(token in text for token in tokens)
    return domain_core and directness and topic_match


def _contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def _topic_relevance_tokens(topic_terms: list[str]) -> set[str]:
    stopwords = {
        "about",
        "around",
        "between",
        "confound",
        "generalization",
        "measurement",
        "neuroscience",
        "recordings",
        "review",
        "signals",
        "systems",
    }
    tokens: set[str] = set()
    for term in topic_terms:
        for token in re.findall(r"[a-zA-Z][a-zA-Z_'-]+", term.replace("_", " ")):
            cleaned = token.lower().strip("-'")
            if len(cleaned) < 5 or cleaned in stopwords:
                continue
            if cleaned.endswith("ing") and len(cleaned) > 7:
                tokens.add(cleaned[:-3])
            tokens.add(cleaned)
    if "coding" in tokens:
        tokens.update({"neural", "population"})
    if "geometry" in tokens:
        tokens.update({"manifold", "representational"})
    if "decision" in tokens:
        tokens.update({"choice", "behavior"})
    if "movement" in tokens:
        tokens.update({"motor", "behavior"})
    return tokens


def _dedupe_key(record: TopicSourceRecord) -> str:
    if record.doi:
        return f"doi:{record.doi.lower()}"
    if record.pmid:
        return f"pmid:{record.pmid}"
    title = " ".join(record.title.lower().split())
    return f"title:{title}:{record.year or ''}"


def _merge_records(existing: TopicSourceRecord, record: TopicSourceRecord) -> TopicSourceRecord:
    primary, secondary = (
        (existing, record)
        if _record_quality(existing) >= _record_quality(record)
        else (record, existing)
    )
    confirmations = sorted(
        set(primary.confirmed_source_families)
        | set(secondary.confirmed_source_families)
        | {primary.source_family, secondary.source_family},
        key=lambda item: item.value,
    )
    publication_types = sorted(set(primary.publication_types) | set(secondary.publication_types))
    update = {
        "query_ids": sorted(set(primary.query_ids) | set(secondary.query_ids)),
        "doi": primary.doi or secondary.doi,
        "pmid": primary.pmid or secondary.pmid,
        "pmcid": primary.pmcid or secondary.pmcid,
        "elicit_id": primary.elicit_id or secondary.elicit_id,
        "openalex_id": primary.openalex_id or secondary.openalex_id,
        "semantic_scholar_id": primary.semantic_scholar_id or secondary.semantic_scholar_id,
        "url": primary.url or secondary.url,
        "venue": primary.venue or secondary.venue,
        "authors": primary.authors or secondary.authors,
        "cited_by_count": primary.cited_by_count
        if primary.cited_by_count is not None
        else secondary.cited_by_count,
        "confirmed_source_families": confirmations,
        "publication_types": publication_types,
        "snippet": primary.snippet or secondary.snippet,
        "metadata_quality_score": max(
            primary.metadata_quality_score, secondary.metadata_quality_score
        )
        + min(0.1, 0.025 * (len(confirmations) - 1)),
        "relevance_score": max(primary.relevance_score, secondary.relevance_score),
    }
    return primary.model_copy(update=update)


def _record_quality(record: TopicSourceRecord) -> float:
    confirmations = record.confirmed_source_families or [record.source_family]
    locator_score = 0.25 if record.doi or record.pmid else 0.0
    return (
        min(record.relevance_score, 1.0)
        + record.metadata_quality_score
        + locator_score
        + min(0.3, 0.075 * len(set(confirmations)))
    )


def _metadata_quality(locator: str, title: str, year: int | None, snippet: str) -> float:
    score = 0.0
    score += 0.35 if locator else 0.0
    score += 0.25 if title else 0.0
    score += 0.15 if year else 0.0
    score += 0.25 if snippet else 0.0
    return score


def _record_needs_abstract_enrichment(record: TopicSourceRecord) -> bool:
    snippet = record.snippet.strip()
    if not snippet:
        return True
    if snippet.lower() == record.venue.lower():
        return True
    if snippet in record.publication_types:
        return True
    return len(snippet.split()) < 8


def _retrieval_record_is_secondary_artifact(record: TopicSourceRecord) -> bool:
    title = record.title.lower().strip()
    if (
        title.startswith("decision letter:")
        or title.startswith("author response:")
        or title.startswith("reviewer #")
        or title.startswith("elife assessment:")
        or "(public review)" in title
        or "public review:" in title
    ):
        return True
    if "10.3389/conf." in record.doi.lower():
        return True
    text = " ".join([record.title, record.snippet]).lower()
    return any(
        marker in text
        for marker in [
            "cancer neuroscience",
            "brain tumor",
            "brain tumors",
            "metaverse",
            "cloud computing",
            "transportation mode",
            "dance/movement",
            "embryonic stem",
        ]
    )


def _record_has_any_lane(record: TopicSourceRecord, lanes: set[str]) -> bool:
    return any(any(lane in query_id for lane in lanes) for query_id in record.query_ids)


def _strip_jats(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", unescape(value))
    return " ".join(text.split())


def _pmid_from_url(value: str) -> str:
    match = re.search(r"pubmed\.ncbi\.nlm\.nih\.gov/(\d+)", value)
    return match.group(1) if match else ""


def _http_post_json(
    url: str,
    body: dict[str, Any],
    headers: dict[str, str],
) -> JsonPostResponse:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
            parsed = json.loads(payload)
            if not isinstance(parsed, dict):
                raise ValueError(f"Expected JSON object from {url}")
            return JsonPostResponse(
                payload=parsed,
                headers={str(key): str(value) for key, value in response.headers.items()},
                status_code=response.status,
            )
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = {"error": {"message": payload[:500]}}
        if not isinstance(parsed, dict):
            parsed = {"error": {"message": payload[:500]}}
        return JsonPostResponse(
            payload=parsed,
            headers={str(key): str(value) for key, value in exc.headers.items()},
            status_code=exc.code,
        )


def _elicit_warnings(payload: dict[str, Any]) -> list[str]:
    warnings = []
    for item in payload.get("warnings", []) or []:
        if not isinstance(item, dict):
            warnings.append(str(item))
            continue
        message = str(item.get("message") or "").strip()
        details = item.get("warningDetails") or {}
        detail_messages = [
            str(value) for value in (details.get("messages") or []) if str(value).strip()
        ]
        warning = "; ".join([part for part in [message, *detail_messages] if part])
        if warning:
            warnings.append(warning)
    return warnings


def _elicit_error_message(status_code: int, payload: dict[str, Any]) -> str:
    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        message = str(error.get("message") or "").strip()
        code = str(error.get("code") or "").strip()
        if message and code:
            return f"Elicit HTTP {status_code} {code}: {message}"
        if message:
            return f"Elicit HTTP {status_code}: {message}"
    return f"Elicit HTTP {status_code}"


def _header_value(headers: dict[str, str], name: str) -> str:
    for key, value in headers.items():
        if key.lower() == name.lower():
            return str(value)
    return ""


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_doi(value: str) -> str:
    value = value.strip()
    value = value.removeprefix("https://doi.org/")
    value = value.removeprefix("http://dx.doi.org/")
    return value


def _article_id(item: dict[str, Any], kind: str) -> str:
    for article_id in item.get("articleids", []):
        if article_id.get("idtype") == kind:
            return str(article_id.get("value") or "")
    return ""


def _year(value: Any) -> int | None:
    match = str(value or "")[:4]
    return int(match) if match.isdigit() else None


def _crossref_year(item: dict[str, Any]) -> int | None:
    date_parts = item.get("issued", {}).get("date-parts") or []
    if date_parts and date_parts[0]:
        year = date_parts[0][0]
        return int(year) if isinstance(year, int) or str(year).isdigit() else None
    return None


def _openalex_abstract(item: dict[str, Any]) -> str:
    inverted = item.get("abstract_inverted_index") or {}
    words: list[tuple[int, str]] = []
    for word, positions in inverted.items():
        for position in positions:
            if isinstance(position, int):
                words.append((position, str(word)))
    words.sort()
    return " ".join(word for _, word in words[:120])
