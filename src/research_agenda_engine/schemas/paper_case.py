from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..enums import ClaimLevel
from .question_pattern import QuestionFormationTrace, QuestionFormationTraceReviewStatus
from .review_authority import is_accepted_authority


class PaperType(StrEnum):
    PURPOSE_BUILT = "purpose_built"
    PRIMARY_DATASET_RELEASE = "primary_dataset_release"
    SECONDARY_DATASET_REUSE = "secondary_dataset_reuse"
    REANALYSIS_OR_ROBUSTNESS = "reanalysis_or_robustness"


class PaperCaseReviewStatus(StrEnum):
    EXTRACTED = "extracted"
    SPAN_VERIFIED = "span_verified"
    # Independent-AI fidelity + citation gate accepted. Same automated/non-human tier as
    # DatasetNarrative's AUTOMATED_REVIEWED; see schemas/review_authority.py. Never a human import.
    AI_REVIEWED = "ai_reviewed"
    EXPERT_REVIEWED = "expert_reviewed"
    REJECTED = "rejected"


class EvidenceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    page: int = Field(ge=1)
    section: str = ""
    quote_or_span: str = Field(min_length=1)
    source_file: str
    source_span_id: str = ""
    source_text_version: str = ""
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)

    @field_validator("field", "source_file")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("field and source_file must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_source_offsets(self) -> EvidenceSpan:
        if (
            self.char_start is not None
            and self.char_end is not None
            and self.char_end < self.char_start
        ):
            raise ValueError("char_end must be greater than or equal to char_start")
        return self


class PaperDatasetDescription(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str = ""
    parent_dataset_paper: str = ""
    public_or_private: str = "unknown"
    population: str = ""
    modalities: list[str] = Field(default_factory=list)
    task_or_design: str = ""
    hierarchy: list[str] = Field(default_factory=list)
    interventions: list[str] = Field(default_factory=list)
    measurements: list[str] = Field(default_factory=list)
    relevant_affordances: list[str] = Field(default_factory=list)


class PaperKnowledgeState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    motivating_claims: list[str] = Field(default_factory=list)
    unresolved_tension: str = ""
    nearest_prior_work: list[str] = Field(default_factory=list)


class PaperScientificQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_question: str = ""
    central_contrast: str = ""
    claim_level: ClaimLevel = ClaimLevel.DESCRIPTIVE
    unit_of_inference: str = ""
    competing_explanations: list[str] = Field(default_factory=list)
    discriminating_observation: str = ""


class QuestionDesignPattern(BaseModel):
    model_config = ConfigDict(extra="forbid")

    epistemic_move: str = ""
    why_dataset_can_answer: str = ""
    why_question_was_valuable: str = ""
    novelty_relative_to_parent_dataset: str = ""
    non_transferable_details: list[str] = Field(default_factory=list)


class PaperCaseReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: PaperCaseReviewStatus = PaperCaseReviewStatus.EXTRACTED
    previous_status: PaperCaseReviewStatus | None = None
    reviewer: str = ""
    reviewed_at: datetime | None = None
    corrections: list[str] = Field(default_factory=list)
    note: str = ""

    @model_validator(mode="after")
    def validate_transition(self) -> PaperCaseReview:
        if self.previous_status is None:
            return self
        allowed = {
            PaperCaseReviewStatus.EXTRACTED: {
                PaperCaseReviewStatus.EXTRACTED,
                PaperCaseReviewStatus.SPAN_VERIFIED,
                PaperCaseReviewStatus.AI_REVIEWED,
                PaperCaseReviewStatus.REJECTED,
            },
            PaperCaseReviewStatus.SPAN_VERIFIED: {
                PaperCaseReviewStatus.SPAN_VERIFIED,
                PaperCaseReviewStatus.AI_REVIEWED,
                PaperCaseReviewStatus.EXPERT_REVIEWED,
                PaperCaseReviewStatus.REJECTED,
            },
            # An AI-reviewed case may still receive an OPTIONAL human override on top (→ EXPERT_REVIEWED).
            PaperCaseReviewStatus.AI_REVIEWED: {
                PaperCaseReviewStatus.AI_REVIEWED,
                PaperCaseReviewStatus.EXPERT_REVIEWED,
                PaperCaseReviewStatus.REJECTED,
            },
            PaperCaseReviewStatus.EXPERT_REVIEWED: {
                PaperCaseReviewStatus.EXPERT_REVIEWED,
                PaperCaseReviewStatus.REJECTED,
            },
            PaperCaseReviewStatus.REJECTED: {PaperCaseReviewStatus.REJECTED},
        }
        if self.status not in allowed[self.previous_status]:
            raise ValueError(
                f"Invalid PaperCase review transition: {self.previous_status} -> {self.status}"
            )
        return self


class PaperCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_case_id: str
    citation: str = ""
    publication_date: date | None = None
    topic_tags: list[str] = Field(default_factory=list)
    paper_type: PaperType
    source_pdf: str = ""
    source_sha256: str = ""
    dataset_description: PaperDatasetDescription = Field(default_factory=PaperDatasetDescription)
    knowledge_state: PaperKnowledgeState = Field(default_factory=PaperKnowledgeState)
    scientific_question: PaperScientificQuestion = Field(default_factory=PaperScientificQuestion)
    question_design: QuestionDesignPattern = Field(default_factory=QuestionDesignPattern)
    formation_trace: QuestionFormationTrace | None = None
    local_literature_context_id: str = ""
    local_literature_context_digest: str = ""
    key_cited_work_ids: list[str] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    evidence_requests: list[str] = Field(default_factory=list)
    review: PaperCaseReview = Field(default_factory=PaperCaseReview)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("paper_case_id")
    @classmethod
    def require_case_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("paper_case_id must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_reviewed_fields(self) -> PaperCase:
        # Applies to BOTH accepted authorities (AI_REVIEWED and EXPERT_REVIEWED): a reviewed case must
        # carry the required scientific fields + valid formation-trace evidence regardless of tier.
        if not is_accepted_authority(self.review.status):
            return self
        missing = self.missing_required_scientific_fields()
        if missing:
            raise ValueError(
                "reviewed PaperCase is missing required scientific fields: " + ", ".join(missing)
            )
        trace_issues = self.formation_trace_evidence_issues()
        if trace_issues and self.formation_trace is not None:
            raise ValueError(
                "reviewed PaperCase has invalid formation_trace evidence: "
                + "; ".join(trace_issues)
            )
        return self

    def missing_required_scientific_fields(self) -> list[str]:
        checks = {
            "knowledge_state.unresolved_tension": self.knowledge_state.unresolved_tension,
            "scientific_question.original_question": self.scientific_question.original_question,
            "question_design.epistemic_move": self.question_design.epistemic_move,
            "question_design.why_dataset_can_answer": self.question_design.why_dataset_can_answer,
            "question_design.novelty_relative_to_parent_dataset": (
                self.question_design.novelty_relative_to_parent_dataset
            ),
        }
        return [field for field, value in checks.items() if not value.strip()]

    def formation_trace_evidence_issues(self) -> list[str]:
        if self.formation_trace is None:
            return []
        trace = self.formation_trace
        issues: list[str] = []
        # Essential-coverage (evidence-provenance unification): a reviewed trace must retain ≥1
        # evidence locator of ANY kind — a span, a key cited work, a literature_evidence entry, or a
        # binding locator. A literature-only trace (spans only inside bindings, or genuinely span-less
        # but cited-work/context-grounded — e.g. a literature-gap product) is USABLE; span provenance
        # is not required. Only a trace with ZERO evidence of any kind is unusable.
        has_any_evidence = bool(
            trace.evidence_span_ids
            or trace.key_cited_work_ids
            or trace.literature_evidence
            or any(
                binding.source_span_ids or binding.cited_work_ids or binding.citation_context_ids
                for binding in trace.evidence_bindings
            )
        )
        if trace.review_status != QuestionFormationTraceReviewStatus.DRAFT and not has_any_evidence:
            issues.append("reviewed formation_trace requires at least one evidence locator")
        available = {span.source_span_id for span in self.evidence_spans if span.source_span_id}
        missing = sorted(set(trace.evidence_span_ids) - available)
        if missing:
            issues.append(
                "formation_trace evidence_span_ids are absent from evidence_spans: "
                + ", ".join(missing)
            )
        return issues


class PaperCorpusEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    filename: str
    paper_type: PaperType
    dataset_name: str = ""
    status: PaperCaseReviewStatus = PaperCaseReviewStatus.EXTRACTED
    source_sha256: str = ""
    case_path: str = ""


class PaperCorpusManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_id: str = "paper-corpus-v0"
    corpus_version: str = "phase2-paper-case-v1"
    registry_path: str = "corpus/paper_registry.csv"
    inbox_dir: str = "corpus/papers/inbox"
    parsed_dir: str = "corpus/parsed"
    extracted_cases_dir: str = "corpus/cases/extracted"
    reviewed_cases_dir: str = "corpus/cases/reviewed"
    indexes_dir: str = "corpus/indexes"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    parser_versions: dict[str, str] = Field(default_factory=dict)
    entries: list[PaperCorpusEntry] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
