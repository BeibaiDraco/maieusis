"""Topic-literature and retrieval-evidence types (product core).

The topic-literature and retrieval-evidence types for the product core
(topic retrieval lanes, paper-case retrieval, literature/nearest-prior evidence,
and the topic-evidence context builder). Extracted from the retired
``schemas/ideation.py``; that legacy module was deleted.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..enums import EvidenceMaturity
from .dataset import EvidenceRequest
from .paper_case import PaperType


class IdeationBranch(StrEnum):
    TOPIC = "topic"
    ADJACENT = "adjacent"
    DATASET_OPPORTUNITY = "dataset_opportunity"
    WILDCARD = "wildcard"


class PriorSearchStatus(StrEnum):
    NO_CLOSE_PRIOR_FOUND = "no_close_prior_found"
    POSSIBLE_DIRECT_RECAP = "possible_direct_recap"
    NEAREST_PRIOR_UNVERIFIED = "nearest_prior_unverified"
    PRIOR_SEARCH_FAILED = "prior_search_failed"


class DirectRecapStatus(StrEnum):
    DIRECT_RECAP_FOUND = "direct_recap_found"
    POSSIBLE_DIRECT_RECAP = "possible_direct_recap"
    NO_CLOSE_PRIOR_AFTER_REVIEW = "no_close_prior_after_review"
    PRIOR_EVIDENCE_INSUFFICIENT = "prior_evidence_insufficient"


class DirectRecapQueryFamily(StrEnum):
    IBL_BWM_REUSE = "ibl_bwm_reuse"
    DATASET_REUSE = "dataset_reuse"
    METHOD_PRIOR = "method_prior"
    TOPIC_SPECIFIC_SCIENCE = "topic_specific_science"
    USER_TOPIC = "user_topic"


class DirectRecapCandidateRelevance(StrEnum):
    DIRECT_RECAP = "direct_recap"
    POSSIBLE_DIRECT_RECAP = "possible_direct_recap"
    RELATED_BACKGROUND = "related_background"
    IRRELEVANT = "irrelevant"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class TopicLensSourceFamily(StrEnum):
    ELICIT = "elicit"
    PUBMED = "pubmed"
    MESH = "mesh"
    OPENALEX = "openalex"
    CROSSREF = "crossref"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    EUROPE_PMC = "europe_pmc"
    INTERLEX = "interlex"
    UBERON = "uberon"
    ALLEN_CCF = "allen_ccf"
    BICCN = "biccn"
    NCBI_TAXONOMY = "ncbi_taxonomy"
    IBL_DOC = "ibl_doc"
    BWM_DOC = "bwm_doc"
    ONE_OPENALYX = "one_openalyx"
    PAPER_CASE_ANALOGY = "paper_case_analogy"
    USER_PRIOR = "user_prior"
    MODEL_DRAFT = "model_draft"


class TopicSourceProfile(StrEnum):
    AUTO = "auto"
    PUBLIC = "public"
    ELICIT = "elicit"
    HYBRID = "hybrid"


class TopicSourceElicitQueryMode(StrEnum):
    BROAD = "broad"
    LANES = "lanes"


class LiteratureQueryKind(StrEnum):
    SHORT = "short"
    CONSTRUCT = "construct"
    DATASET_ALIAS = "dataset_alias"
    BROAD = "broad"


class TopicSourceQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_id: str
    source_family: TopicLensSourceFamily
    query: str
    query_lane: str = "background"
    topic_terms: list[str] = Field(default_factory=list)
    filters: dict[str, str] = Field(default_factory=dict)
    max_results: int = Field(default=5, ge=1, le=100)
    corpus: str = ""
    search_mode: str = ""


class TopicSourceQueryPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    source_profile: TopicSourceProfile = TopicSourceProfile.PUBLIC
    topic_terms: list[str] = Field(default_factory=list)
    queries: list[TopicSourceQuery] = Field(default_factory=list)
    prompt_version: str = "topic_source_query_plan/v1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TopicSourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    source_family: TopicLensSourceFamily
    query_ids: list[str] = Field(default_factory=list)
    title: str
    year: int | None = None
    url: str = ""
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    elicit_id: str = ""
    openalex_id: str = ""
    semantic_scholar_id: str = ""
    source_locator: str = ""
    venue: str = ""
    authors: list[str] = Field(default_factory=list)
    cited_by_count: int | None = None
    confirmed_source_families: list[TopicLensSourceFamily] = Field(default_factory=list)
    publication_types: list[str] = Field(default_factory=list)
    snippet: str = ""
    relevance_score: float = 0.0
    metadata_quality_score: float = 0.0
    source_payload_hash: str = ""

    @model_validator(mode="after")
    def require_locator_or_url(self) -> TopicSourceRecord:
        if not (
            self.doi
            or self.pmid
            or self.pmcid
            or self.elicit_id
            or self.openalex_id
            or self.semantic_scholar_id
            or self.url
            or self.source_locator
        ):
            raise ValueError("TopicSourceRecord requires at least one locator")
        return self


class TopicSourceSearchTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    source_family: TopicLensSourceFamily
    query_id: str
    request_url: str = ""
    request_method: str = "GET"
    request_body_hash: str = ""
    http_status: int | None = None
    response_hash: str = ""
    candidate_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    rate_limit_limit: str = ""
    rate_limit_remaining: str = ""
    rate_limit_reset: str = ""


class TopicSourceTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_id: str
    query_plan_id: str = ""
    topic_terms: list[str] = Field(default_factory=list)
    records: list[TopicSourceRecord] = Field(default_factory=list)
    search_traces: list[TopicSourceSearchTrace] = Field(default_factory=list)
    max_records: int = Field(default=20, ge=1, le=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def enforce_record_cap(self) -> TopicSourceTable:
        if len(self.records) > self.max_records:
            raise ValueError("TopicSourceTable records exceed max_records")
        return self


class PaperCaseRetrievalQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_id: str
    topic_terms: list[str] = Field(default_factory=list)
    epistemic_moves: list[str] = Field(default_factory=list)
    paper_types: list[PaperType] = Field(default_factory=list)
    exclude_paper_case_ids: list[str] = Field(default_factory=list)
    limit: int = Field(default=8, ge=1, le=12)


class PaperCaseRetrievalHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_case_id: str
    paper_type: PaperType
    score: float
    topic_score: float = 0.0
    design_score: float = 0.0
    epistemic_move_score: float = 0.0
    diversity_bonus: float = 0.0
    rationale: str = ""


class PaperCaseRetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: PaperCaseRetrievalQuery
    hits: list[PaperCaseRetrievalHit] = Field(default_factory=list)
    reviewed_case_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AnalogyPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analogy_plan_id: str
    source_case_ids: list[str] = Field(default_factory=list)
    source_question_pattern: str
    transferable_epistemic_move: str
    non_transferable_details: list[str] = Field(default_factory=list)
    ibl_affordance_used: str
    source_analogy_delta: str = ""
    novelty_delta: str = ""
    risk_of_direct_recap: str = ""
    candidate_direction: str

    @model_validator(mode="after")
    def require_traceable_analogy_delta(self) -> AnalogyPlan:
        if not self.source_analogy_delta and self.novelty_delta:
            self.source_analogy_delta = self.novelty_delta
        if not self.source_case_ids:
            raise ValueError("AnalogyPlan requires source_case_ids")
        if not self.source_analogy_delta.strip():
            raise ValueError("AnalogyPlan requires source_analogy_delta")
        return self


class QuestionConcept(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    branch: IdeationBranch = IdeationBranch.TOPIC
    question: str
    central_scientific_tension: str
    source_case_ids: list[str] = Field(default_factory=list)
    transferable_moves: list[str] = Field(default_factory=list)
    source_analogy_delta: str = ""
    novelty_delta: str = ""
    prior_grounded_novelty_delta: str = ""
    ibl_specific_leverage: str
    competing_explanations: list[str] = Field(default_factory=list)
    positive_belief_update: str
    negative_belief_update: str
    minimum_required_affordances: list[str] = Field(default_factory=list)
    major_unknowns: list[str] = Field(default_factory=list)
    analogy_plan_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_delta_and_reject_question_card_placeholders(self) -> QuestionConcept:
        if not self.source_analogy_delta and self.novelty_delta:
            self.source_analogy_delta = self.novelty_delta
        forbidden = [
            "question-specific estimand",
            "question-specific window",
            "placeholder estimand",
        ]
        lower = " ".join(
            [
                self.question,
                self.central_scientific_tension,
                self.source_analogy_delta,
                self.prior_grounded_novelty_delta,
                self.ibl_specific_leverage,
            ]
        ).lower()
        if any(token in lower for token in forbidden):
            raise ValueError("QuestionConcept cannot contain QuestionCard placeholder text")
        if not self.source_case_ids and not self.minimum_required_affordances:
            raise ValueError("QuestionConcept requires PaperCase sources or dataset affordances")
        return self


class QuestionConceptBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str
    topic_frame_id: str = ""
    topic_lens_id: str = ""
    analogy_plans: list[AnalogyPlan] = Field(default_factory=list)
    concepts: list[QuestionConcept] = Field(default_factory=list)
    provider_id: str = ""
    prompt_version: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class NearestPriorCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    source: str
    title: str
    year: int | None = None
    url: str = ""
    doi: str = ""
    paper_case_id: str = ""
    snippet: str = ""
    similarity_score: float = 0.0
    overlap_facets: list[str] = Field(default_factory=list)
    evidence_id: str = ""


class ConceptNearestPriorEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    status: PriorSearchStatus = PriorSearchStatus.NEAREST_PRIOR_UNVERIFIED
    query: str
    candidates: list[NearestPriorCandidate] = Field(default_factory=list)
    rationale: str = ""
    issue_codes: list[str] = Field(default_factory=list)
    response_hashes: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_issue_code_for_risky_status(self) -> ConceptNearestPriorEvidence:
        if self.status != PriorSearchStatus.NO_CLOSE_PRIOR_FOUND and not self.issue_codes:
            raise ValueError("non-clear nearest-prior status requires issue_codes")
        return self


class NearestPriorEvidenceBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str
    concept_batch_id: str
    evidence: list[ConceptNearestPriorEvidence] = Field(default_factory=list)
    provider_id: str = ""
    prompt_version: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DirectRecapCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    source: str
    title: str
    year: int | None = None
    url: str = ""
    doi: str = ""
    abstract_or_snippet: str = ""
    scientific_question_overlap: str = ""
    dataset_overlap: str = ""
    method_estimand_overlap: str = ""
    evidence_refs: list[str] = Field(default_factory=list)


class DirectRecapCandidateReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    scientific_question_overlap: str = ""
    dataset_overlap: str = ""
    method_estimand_overlap: str = ""
    rationale: str = ""


class DirectRecapReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    status: DirectRecapStatus = DirectRecapStatus.PRIOR_EVIDENCE_INSUFFICIENT
    verdict_rationale: str = ""
    evidence_gaps: list[str] = Field(default_factory=list)
    candidate_reviews: list[DirectRecapCandidateReview] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_gap_for_insufficient_review(self) -> DirectRecapReviewDecision:
        if self.status == DirectRecapStatus.PRIOR_EVIDENCE_INSUFFICIENT and not self.evidence_gaps:
            self.evidence_gaps = ["DirectRecap reviewer found insufficient evidence."]
        return self


class DirectRecapReviewBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str
    concept_batch_id: str = ""
    decisions: list[DirectRecapReviewDecision] = Field(default_factory=list)
    provider_id: str = ""
    prompt_version: str = "direct_recap_review/v1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DirectRecapProtocolQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_id: str
    concept_id: str
    family: DirectRecapQueryFamily
    query_text: str
    source_families: list[str] = Field(default_factory=list)
    required: bool = True
    executed: bool = False
    retrieved_candidate_count: int = 0
    reviewed_candidate_count: int = 0
    artifact_uri: str = ""
    artifact_hash: str = ""
    warnings: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)

    @property
    def has_execution_artifact(self) -> bool:
        return self.executed and bool(self.artifact_hash)


class DirectRecapReviewedCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    concept_id: str
    title: str
    year: int | None = None
    source_family: str = ""
    source_record_id: str = ""
    doi: str = ""
    url: str = ""
    query_ids: list[str] = Field(default_factory=list)
    relevance_label: DirectRecapCandidateRelevance = (
        DirectRecapCandidateRelevance.INSUFFICIENT_EVIDENCE
    )
    scientific_question_overlap: str = ""
    dataset_overlap: str = ""
    method_estimand_overlap: str = ""
    reviewed_evidence_refs: list[str] = Field(default_factory=list)
    evidence_artifact_uri: str = ""
    evidence_artifact_hash: str = ""
    reviewer_notes: str = ""

    @property
    def has_reviewed_evidence(self) -> bool:
        return bool(self.reviewed_evidence_refs or self.evidence_artifact_hash)

    @property
    def is_recap_blocker(self) -> bool:
        return self.relevance_label in {
            DirectRecapCandidateRelevance.DIRECT_RECAP,
            DirectRecapCandidateRelevance.POSSIBLE_DIRECT_RECAP,
        }


class DirectRecapProtocolReviewBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundle_id: str
    concept_id: str
    question: str = ""
    status: DirectRecapStatus = DirectRecapStatus.PRIOR_EVIDENCE_INSUFFICIENT
    query_protocol: list[DirectRecapProtocolQuery] = Field(default_factory=list)
    candidate_reviews: list[DirectRecapReviewedCandidate] = Field(default_factory=list)
    verdict_rationale: str = ""
    expert_reviewer: str = ""
    expert_signed_off: bool = False
    expert_review_artifact_uri: str = ""
    expert_review_artifact_hash: str = ""
    evidence_requests: list[EvidenceRequest] = Field(default_factory=list)
    evidence: list[Any] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def required_queries_executed(self) -> bool:
        required = [query for query in self.query_protocol if query.required]
        return bool(required) and all(query.has_execution_artifact for query in required)

    @property
    def reviewed_candidates_have_evidence(self) -> bool:
        return bool(self.candidate_reviews) and all(
            candidate.has_reviewed_evidence for candidate in self.candidate_reviews
        )

    @property
    def has_close_prior_blocker(self) -> bool:
        return any(candidate.is_recap_blocker for candidate in self.candidate_reviews)

    @property
    def supports_no_close_prior(self) -> bool:
        return (
            self.status == DirectRecapStatus.NO_CLOSE_PRIOR_AFTER_REVIEW
            and self.required_queries_executed
            and self.reviewed_candidates_have_evidence
            and not self.has_close_prior_blocker
            and self.expert_signed_off
            and bool(self.expert_review_artifact_hash)
            and not any(request.blocking for request in self.evidence_requests)
        )


class DirectRecapEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    status: DirectRecapStatus = DirectRecapStatus.PRIOR_EVIDENCE_INSUFFICIENT
    query_strategy: list[str] = Field(default_factory=list)
    candidates: list[DirectRecapCandidate] = Field(default_factory=list)
    verdict_rationale: str = ""
    evidence_gaps: list[str] = Field(default_factory=list)
    response_hashes: dict[str, str] = Field(default_factory=dict)
    review_artifact_ids: list[str] = Field(default_factory=list)
    evidence_maturity: EvidenceMaturity = EvidenceMaturity.E2_METADATA_SCREENED
    protocol_review_bundle_id: str = ""
    protocol_review_bundle_hash: str = ""
    protocol_review_status: str = ""
    expert_reviewer: str = ""
    expert_signed_off: bool = False
    executed_protocol_query_count: int = 0
    reviewed_candidate_count: int = 0

    @model_validator(mode="after")
    def require_gap_for_insufficient_evidence(self) -> DirectRecapEvidence:
        if self.status == DirectRecapStatus.PRIOR_EVIDENCE_INSUFFICIENT and not self.evidence_gaps:
            self.evidence_gaps = ["DirectRecap evidence is insufficient for D2/D3 promotion."]
        return self

    @property
    def supports_d2_promotion(self) -> bool:
        return (
            self.status == DirectRecapStatus.NO_CLOSE_PRIOR_AFTER_REVIEW
            and not self.evidence_gaps
            and self.evidence_maturity.rank >= EvidenceMaturity.E3_OPERATOR_DEMONSTRATED.rank
            and bool(self.response_hashes or self.review_artifact_ids)
            and bool(self.protocol_review_bundle_id)
            and bool(self.protocol_review_bundle_hash)
            and self.expert_signed_off
            and self.executed_protocol_query_count > 0
            and self.reviewed_candidate_count > 0
        )


class DirectRecapEvidenceBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str
    concept_batch_id: str = ""
    evidence: list[DirectRecapEvidence] = Field(default_factory=list)
    provider_id: str = ""
    prompt_version: str = "direct_recap/v2"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LiteratureQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_id: str
    concept_id: str
    kind: LiteratureQueryKind
    raw_query: str
    sanitized_query: str
    query_hash: str

    @model_validator(mode="after")
    def require_safe_query(self) -> LiteratureQuery:
        if not self.sanitized_query.strip():
            raise ValueError("LiteratureQuery requires sanitized_query")
        if "?" in self.sanitized_query or "*" in self.sanitized_query:
            raise ValueError("LiteratureQuery sanitized_query cannot contain wildcard punctuation")
        return self


class LiteratureQueryPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: str
    concept_batch_id: str
    queries: list[LiteratureQuery] = Field(default_factory=list)
    provider_id: str = ""
    prompt_version: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LiteratureCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    provider: str
    title: str
    year: int | None = None
    doi: str = ""
    url: str = ""
    openalex_id: str = ""
    snippet: str = ""
    cited_by_count: int = 0
    query_ids: list[str] = Field(default_factory=list)
    similarity_score: float = 0.0
    metadata_quality_score: float = 0.0
    evidence_id: str = ""


class LiteratureSearchTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    provider_id: str
    query_ids: list[str] = Field(default_factory=list)
    response_hashes: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    candidate_count: int = 0
    searched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class NearestPriorSet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    status: PriorSearchStatus
    candidates: list[LiteratureCandidate] = Field(default_factory=list)
    rationale: str = ""
    issue_codes: list[str] = Field(default_factory=list)
    search_traces: list[LiteratureSearchTrace] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_issue_codes_for_unclear_status(self) -> NearestPriorSet:
        if self.status != PriorSearchStatus.NO_CLOSE_PRIOR_FOUND and not self.issue_codes:
            raise ValueError("non-clear nearest-prior set status requires issue_codes")
        return self


class NearestPriorSetBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str
    concept_batch_id: str
    query_pack_id: str = ""
    prior_sets: list[NearestPriorSet] = Field(default_factory=list)
    provider_id: str = ""
    prompt_version: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ExemplarOverlapCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_case_id: str
    citation: str = ""
    similarity_score: float = 0.0
    overlap_facets: list[str] = Field(default_factory=list)
    rationale: str = ""


class ConceptExemplarOverlap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept_id: str
    candidates: list[ExemplarOverlapCandidate] = Field(default_factory=list)
    rationale: str = (
        "Reviewed PaperCases are analogy exemplars only, not novelty/direct-recap evidence."
    )


class ExemplarOverlapReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    concept_batch_id: str
    overlaps: list[ConceptExemplarOverlap] = Field(default_factory=list)
    provider_id: str = "local_paper_case_exemplar_overlap"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
