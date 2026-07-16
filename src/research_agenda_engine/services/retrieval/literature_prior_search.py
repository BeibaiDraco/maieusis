from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from ...provenance import stable_hash
from ...schemas.paper_case import PaperCase
from ...schemas.topic_literature import (
    ConceptExemplarOverlap,
    ConceptNearestPriorEvidence,
    ExemplarOverlapCandidate,
    ExemplarOverlapReport,
    LiteratureCandidate,
    LiteratureQuery,
    LiteratureQueryKind,
    LiteratureQueryPack,
    LiteratureSearchTrace,
    NearestPriorCandidate,
    NearestPriorEvidenceBatch,
    NearestPriorSet,
    NearestPriorSetBatch,
    PriorSearchStatus,
    QuestionConcept,
    QuestionConceptBatch,
)

JsonGetter = Callable[[str, dict[str, str]], dict[str, Any]]

LITERATURE_QUERY_PROMPT_VERSION = "literature_query_pack/openalex/v1"
PUBLIC_PRIOR_PROMPT_VERSION = "public_prior_search/openalex/v1"


class OpenAlexPriorSearchProvider:
    """OpenAlex metadata search for public nearest-prior evidence."""

    def __init__(
        self,
        *,
        http_get_json: JsonGetter | None = None,
        enabled: bool = True,
        max_results_per_query: int = 5,
        max_candidates_per_concept: int = 8,
        openalex_email: str = "",
        openalex_api_key: str = "",
    ):
        self.http_get_json = http_get_json or _http_get_json
        self.enabled = enabled
        self.max_results_per_query = max_results_per_query
        self.max_candidates_per_concept = max_candidates_per_concept
        self.openalex_email = openalex_email or os.getenv("OPENALEX_EMAIL", "")
        self.openalex_api_key = openalex_api_key or os.getenv("OPENALEX_API_KEY", "")

    @property
    def provider_id(self) -> str:
        return "openalex" if self.enabled else "openalex_disabled"

    def search(
        self,
        concept_batch: QuestionConceptBatch,
        *,
        dataset_alias_terms: list[str] | None = None,
    ) -> tuple[LiteratureQueryPack, NearestPriorSetBatch]:
        query_pack = build_literature_query_pack(
            concept_batch,
            dataset_alias_terms=dataset_alias_terms or [],
            provider_id=self.provider_id,
        )
        prior_sets = [
            self._search_concept(concept, query_pack) for concept in concept_batch.concepts
        ]
        return (
            query_pack,
            NearestPriorSetBatch(
                batch_id=f"nearest-public-priors-{stable_hash([item.concept_id for item in prior_sets])[:12]}",
                concept_batch_id=concept_batch.batch_id,
                query_pack_id=query_pack.pack_id,
                prior_sets=prior_sets,
                provider_id=self.provider_id,
                prompt_version=PUBLIC_PRIOR_PROMPT_VERSION,
            ),
        )

    def _search_concept(
        self, concept: QuestionConcept, query_pack: LiteratureQueryPack
    ) -> NearestPriorSet:
        concept_queries = [
            query for query in query_pack.queries if query.concept_id == concept.concept_id
        ]
        if not self.enabled:
            trace = LiteratureSearchTrace(
                concept_id=concept.concept_id,
                provider_id=self.provider_id,
                query_ids=[query.query_id for query in concept_queries],
                errors=["public prior search disabled"],
                candidate_count=0,
            )
            return NearestPriorSet(
                concept_id=concept.concept_id,
                status=PriorSearchStatus.PRIOR_SEARCH_FAILED,
                candidates=[],
                rationale="Public literature prior search was disabled for this run.",
                issue_codes=["PUBLIC_PRIOR_SEARCH_DISABLED"],
                search_traces=[trace],
            )

        candidates: list[LiteratureCandidate] = []
        response_hashes: dict[str, str] = {}
        errors: list[str] = []
        concept_tokens = _tokens(_concept_prior_text(concept))
        searched_query_ids: list[str] = []
        for query in concept_queries:
            searched_query_ids.append(query.query_id)
            try:
                raw = self._openalex_search(query.sanitized_query)
                response_hashes[query.query_id] = stable_hash(raw)
                for candidate in _openalex_candidates(
                    raw,
                    query=query,
                    concept_tokens=concept_tokens,
                ):
                    candidates.append(candidate)
            except Exception as exc:
                errors.append(f"{query.query_id}: {_exception_message(exc)}")
        candidates = _dedupe_literature_candidates(candidates)
        candidates.sort(
            key=lambda item: (
                -item.similarity_score,
                -item.metadata_quality_score,
                -item.cited_by_count,
                item.title.lower(),
            )
        )
        candidates = candidates[: self.max_candidates_per_concept]
        trace = LiteratureSearchTrace(
            concept_id=concept.concept_id,
            provider_id=self.provider_id,
            query_ids=searched_query_ids,
            response_hashes=response_hashes,
            errors=errors,
            candidate_count=len(candidates),
        )
        if not candidates and errors:
            return NearestPriorSet(
                concept_id=concept.concept_id,
                status=PriorSearchStatus.PRIOR_SEARCH_FAILED,
                candidates=[],
                rationale="Public literature search failed for all usable queries.",
                issue_codes=["PUBLIC_PRIOR_SEARCH_FAILED"],
                search_traces=[trace],
            )
        if candidates and candidates[0].similarity_score >= 0.72:
            return NearestPriorSet(
                concept_id=concept.concept_id,
                status=PriorSearchStatus.POSSIBLE_DIRECT_RECAP,
                candidates=candidates,
                rationale="A public literature metadata/snippet candidate is very close.",
                issue_codes=["POSSIBLE_DIRECT_RECAP"],
                search_traces=[trace],
            )
        if candidates:
            issue_codes = ["NEAREST_PUBLIC_PRIOR_UNVERIFIED"]
            if errors:
                issue_codes.append("PUBLIC_PRIOR_SEARCH_PARTIAL_FAILURE")
            return NearestPriorSet(
                concept_id=concept.concept_id,
                status=PriorSearchStatus.NEAREST_PRIOR_UNVERIFIED,
                candidates=candidates,
                rationale="Public prior candidates exist, but direct-recap status is unresolved.",
                issue_codes=issue_codes,
                search_traces=[trace],
            )
        return NearestPriorSet(
            concept_id=concept.concept_id,
            status=PriorSearchStatus.NO_CLOSE_PRIOR_FOUND,
            candidates=[],
            rationale=(
                "No close public prior candidate was found by this metadata search trace; "
                "this is not novelty certification."
            ),
            search_traces=[trace],
        )

    def _openalex_search(self, query: str) -> dict[str, Any]:
        params = {
            "search": query,
            "per-page": str(self.max_results_per_query),
            "select": (
                "id,display_name,publication_year,doi,primary_location,"
                "abstract_inverted_index,cited_by_count,ids,type"
            ),
        }
        if self.openalex_email:
            params["mailto"] = self.openalex_email
        if self.openalex_api_key:
            params["api_key"] = self.openalex_api_key
        url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
        return self.http_get_json(url, {"User-Agent": "maieusis/phase2"})


def build_literature_query_pack(
    concept_batch: QuestionConceptBatch,
    *,
    dataset_alias_terms: list[str],
    provider_id: str = "openalex",
) -> LiteratureQueryPack:
    queries: list[LiteratureQuery] = []
    for concept in concept_batch.concepts:
        raw_queries = [
            (LiteratureQueryKind.SHORT, concept.question),
            (
                LiteratureQueryKind.CONSTRUCT,
                " ".join(
                    [
                        concept.central_scientific_tension,
                        concept.source_analogy_delta or concept.novelty_delta,
                        " ".join(concept.transferable_moves),
                    ]
                ),
            ),
            (
                LiteratureQueryKind.DATASET_ALIAS,
                " ".join([*dataset_alias_terms, concept.question]),
            ),
            (
                LiteratureQueryKind.BROAD,
                " ".join(
                    [
                        "neural population coding geometry decision making",
                        " ".join(concept.competing_explanations[:3]),
                    ]
                ),
            ),
        ]
        for index, (kind, raw_query) in enumerate(raw_queries, start=1):
            sanitized = sanitize_literature_query(raw_query)
            query_id = f"{concept.concept_id}-{kind.value}-{index}"
            queries.append(
                LiteratureQuery(
                    query_id=query_id,
                    concept_id=concept.concept_id,
                    kind=kind,
                    raw_query=raw_query,
                    sanitized_query=sanitized,
                    query_hash=stable_hash({"query_id": query_id, "query": sanitized}),
                )
            )
    return LiteratureQueryPack(
        pack_id=f"literature-query-pack-{stable_hash([query.query_hash for query in queries])[:12]}",
        concept_batch_id=concept_batch.batch_id,
        queries=queries,
        provider_id=provider_id,
        prompt_version=LITERATURE_QUERY_PROMPT_VERSION,
    )


def build_exemplar_overlap_report(
    concept_batch: QuestionConceptBatch,
    local_cases: list[PaperCase],
    *,
    max_candidates_per_concept: int = 5,
) -> ExemplarOverlapReport:
    cases_by_id = {case.paper_case_id: case for case in local_cases}
    overlaps: list[ConceptExemplarOverlap] = []
    for concept in concept_batch.concepts:
        concept_tokens = _tokens(_concept_prior_text(concept))
        candidates: list[ExemplarOverlapCandidate] = []
        for case in local_cases:
            text = " ".join(
                [
                    case.citation,
                    " ".join(case.topic_tags),
                    case.scientific_question.original_question,
                    case.knowledge_state.unresolved_tension,
                    case.question_design.epistemic_move,
                    case.question_design.novelty_relative_to_parent_dataset,
                ]
            )
            score = _overlap_score(concept_tokens, _tokens(text))
            if score < 0.08 and case.paper_case_id not in set(concept.source_case_ids):
                continue
            candidates.append(
                ExemplarOverlapCandidate(
                    paper_case_id=case.paper_case_id,
                    citation=case.citation or case.paper_case_id,
                    similarity_score=round(score, 4),
                    overlap_facets=["topic", "question", "epistemic_move"],
                    rationale=(
                        "PaperCase overlap is analogy/provenance evidence only, "
                        "not public prior-work evidence."
                    ),
                )
            )
        for source_id in concept.source_case_ids:
            if source_id in cases_by_id and not any(
                candidate.paper_case_id == source_id for candidate in candidates
            ):
                case = cases_by_id[source_id]
                candidates.append(
                    ExemplarOverlapCandidate(
                        paper_case_id=case.paper_case_id,
                        citation=case.citation or case.paper_case_id,
                        similarity_score=0.0,
                        overlap_facets=["analogy_source"],
                        rationale="Cited analogy source PaperCase.",
                    )
                )
        candidates.sort(key=lambda item: (-item.similarity_score, item.paper_case_id))
        overlaps.append(
            ConceptExemplarOverlap(
                concept_id=concept.concept_id,
                candidates=candidates[:max_candidates_per_concept],
            )
        )
    return ExemplarOverlapReport(
        report_id=f"exemplar-overlap-{stable_hash([item.concept_id for item in overlaps])[:12]}",
        concept_batch_id=concept_batch.batch_id,
        overlaps=overlaps,
    )


def nearest_prior_sets_to_evidence_batch(
    prior_sets: NearestPriorSetBatch,
) -> NearestPriorEvidenceBatch:
    evidence = []
    for prior_set in prior_sets.prior_sets:
        response_hashes: dict[str, str] = {}
        for trace in prior_set.search_traces:
            response_hashes.update(trace.response_hashes)
        query_ids = [query_id for trace in prior_set.search_traces for query_id in trace.query_ids]
        evidence.append(
            ConceptNearestPriorEvidence(
                concept_id=prior_set.concept_id,
                status=prior_set.status,
                query="; ".join(query_ids),
                candidates=[
                    NearestPriorCandidate(
                        candidate_id=candidate.candidate_id,
                        source=candidate.provider,
                        title=candidate.title,
                        year=candidate.year,
                        url=candidate.url,
                        doi=candidate.doi,
                        snippet=candidate.snippet,
                        similarity_score=candidate.similarity_score,
                        overlap_facets=["public_title_abstract"],
                        evidence_id=candidate.evidence_id,
                    )
                    for candidate in prior_set.candidates
                ],
                rationale=prior_set.rationale,
                issue_codes=prior_set.issue_codes,
                response_hashes=response_hashes,
            )
        )
    return NearestPriorEvidenceBatch(
        batch_id=f"nearest-prior-evidence-{stable_hash([item.concept_id for item in evidence])[:12]}",
        concept_batch_id=prior_sets.concept_batch_id,
        evidence=evidence,
        provider_id=prior_sets.provider_id,
        prompt_version=prior_sets.prompt_version,
    )


def sanitize_literature_query(query: str, *, max_chars: int = 220) -> str:
    query = re.sub(r"[?*]", " ", query)
    query = re.sub(r"[/\\()[\]{}:;,_|+=<>\"'`~^]", " ", query)
    query = re.sub(r"\s+", " ", query).strip()
    if len(query) <= max_chars:
        return query
    trimmed = query[:max_chars].rsplit(" ", 1)[0].strip()
    return trimmed or query[:max_chars].strip()


def _openalex_candidates(
    raw: dict[str, Any],
    *,
    query: LiteratureQuery,
    concept_tokens: set[str],
) -> list[LiteratureCandidate]:
    results = raw.get("results") if isinstance(raw, dict) else []
    candidates: list[LiteratureCandidate] = []
    for item in results or []:
        title = str(item.get("display_name") or item.get("title") or "")
        abstract = _openalex_abstract(item.get("abstract_inverted_index"))
        text = " ".join([title, abstract])
        ids = item.get("ids") or {}
        openalex_id = str(item.get("id") or ids.get("openalex") or "")
        doi = str(item.get("doi") or ids.get("doi") or "").removeprefix("https://doi.org/")
        score = _overlap_score(concept_tokens, _tokens(text))
        quality = _metadata_quality_score(title=title, abstract=abstract, doi=doi)
        candidates.append(
            LiteratureCandidate(
                candidate_id=f"openalex:{openalex_id or stable_hash(item)[:12]}",
                provider="openalex",
                title=title or "untitled OpenAlex work",
                year=item.get("publication_year"),
                doi=doi,
                url=openalex_id
                or str((item.get("primary_location") or {}).get("landing_page_url") or ""),
                openalex_id=openalex_id,
                snippet=abstract[:500],
                cited_by_count=int(item.get("cited_by_count") or 0),
                query_ids=[query.query_id],
                similarity_score=round(score, 4),
                metadata_quality_score=quality,
                evidence_id=openalex_id,
            )
        )
    return candidates


def _dedupe_literature_candidates(
    candidates: list[LiteratureCandidate],
) -> list[LiteratureCandidate]:
    by_key: dict[str, LiteratureCandidate] = {}
    for candidate in candidates:
        key = (candidate.doi or candidate.openalex_id or candidate.title).lower()
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = candidate
            continue
        merged = existing.model_copy(deep=True)
        merged.query_ids = sorted(set(existing.query_ids + candidate.query_ids))
        merged.similarity_score = max(existing.similarity_score, candidate.similarity_score)
        merged.metadata_quality_score = max(
            existing.metadata_quality_score, candidate.metadata_quality_score
        )
        merged.cited_by_count = max(existing.cited_by_count, candidate.cited_by_count)
        by_key[key] = merged
    return list(by_key.values())


def _concept_prior_text(concept: QuestionConcept) -> str:
    return " ".join(
        [
            concept.question,
            concept.central_scientific_tension,
            concept.source_analogy_delta or concept.novelty_delta,
            " ".join(concept.transferable_moves),
            " ".join(concept.competing_explanations),
        ]
    )


def _tokens(text: str) -> set[str]:
    stop = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "into",
        "does",
        "can",
        "ibl",
        "task",
        "using",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in stop
    }


def _overlap_score(query_tokens: set[str], document_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0
    return len(query_tokens & document_tokens) / len(query_tokens)


def _metadata_quality_score(*, title: str, abstract: str, doi: str) -> float:
    score = 0.0
    score += 0.35 if title.strip() else 0.0
    score += 0.45 if abstract.strip() else 0.0
    score += 0.2 if doi.strip() else 0.0
    return round(score, 4)


def _http_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body[:500]}") from exc
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object from {url}")
    return parsed


def _exception_message(exc: Exception) -> str:
    return str(exc).replace("\n", " ")[:700]


def _openalex_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, offsets in index.items():
        positions.extend((int(offset), word) for offset in offsets)
    return " ".join(word for _, word in sorted(positions))
