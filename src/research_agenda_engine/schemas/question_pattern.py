from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .review_authority import is_accepted_authority


class QuestionFormationTraceReviewStatus(StrEnum):
    DRAFT = "draft"
    SPAN_VERIFIED = "span_verified"
    # Independent-AI formation-trace gate accepted. Automated/non-human tier; see
    # schemas/review_authority.py.
    AI_REVIEWED = "ai_reviewed"
    EXPERT_REVIEWED = "expert_reviewed"


class QuestionPatternReviewStatus(StrEnum):
    DRAFT = "draft"
    NEEDS_REVISION = "needs_revision"
    # Independent-AI pattern gate accepted. Automated/non-human tier; see
    # schemas/review_authority.py.
    AI_REVIEWED = "ai_reviewed"
    EXPERT_REVIEWED = "expert_reviewed"
    REJECTED = "rejected"


class QuestionPatternHumanDecision(StrEnum):
    """The ONLY statuses a human importer may assign — deliberately WITHOUT ``ai_reviewed``.

    ``ai_reviewed`` is the automated gate's authority; it must never be reachable through the human
    import path (a forged/mistaken ``ai_reviewed`` human decision must ERROR, not be laundered to
    ``expert_reviewed``). A human ACCEPT lands ``expert_reviewed``.
    """

    DRAFT = "draft"
    NEEDS_REVISION = "needs_revision"
    ACCEPT = "expert_reviewed"
    REJECTED = "rejected"


class QuestionPatternTransferScope(StrEnum):
    CROSS_PAPER = "cross_paper"
    PAPER_SPECIFIC = "paper_specific"


class QuestionFormationLiteratureRole(StrEnum):
    MOTIVATING_PRIOR = "motivating_prior"
    UNRESOLVED_TENSION = "unresolved_tension"
    CONSTRUCT_DEFINITION = "construct_definition"
    METHOD_PRECEDENT = "method_precedent"
    DATASET_PRECEDENT = "dataset_precedent"
    QUESTION_FORMING_MOVE = "question_forming_move"
    CONTRAST_CASE = "contrast_case"
    OTHER = "other"


class QuestionFormationEvidenceBindingRole(StrEnum):
    LITERATURE_GAP = "literature_gap"
    THEORETICAL_TENSION = "theoretical_tension"
    DATASET_OPPORTUNITY = "dataset_opportunity"
    METHOD_OR_CONSTRUCT_PRECEDENT = "method_or_construct_precedent"
    QUESTION_FORMING_MOVE = "question_forming_move"
    NON_TRANSFERABLE_ASSUMPTION = "non_transferable_assumption"


class QuestionFormationEvidenceBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: QuestionFormationEvidenceBindingRole
    source_span_ids: list[str] = Field(default_factory=list)
    cited_work_ids: list[str] = Field(default_factory=list)
    citation_context_ids: list[str] = Field(default_factory=list)
    rationale: str

    @field_validator("rationale")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionFormationEvidenceBinding rationale must be non-empty")
        return value

    @model_validator(mode="after")
    def require_evidence_locator(self) -> QuestionFormationEvidenceBinding:
        if not (self.source_span_ids or self.cited_work_ids or self.citation_context_ids):
            raise ValueError("QuestionFormationEvidenceBinding requires at least one evidence ID")
        return self


class QuestionFormationLiteratureEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cited_work_id: str
    role: QuestionFormationLiteratureRole = QuestionFormationLiteratureRole.OTHER
    rationale: str
    selection_rank: int | None = Field(default=None, ge=1)
    selection_importance: str = ""
    evidence_context_ids: list[str] = Field(default_factory=list)
    abstract_evidence_used: bool = False

    @field_validator("cited_work_id", "rationale")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionFormationLiteratureEvidence fields must be non-empty")
        return value


class QuestionFormationTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    background_claims: list[str] = Field(default_factory=list)
    unresolved_gap: str
    dataset_feature_noticed: str
    opportunity_inference: str
    resulting_question: str
    expected_scientific_consequence: str
    scientific_significance: str
    transferable_reasoning_pattern: str
    non_transferable_assumptions: list[str] = Field(default_factory=list)
    evidence_span_ids: list[str] = Field(default_factory=list)
    local_literature_context_id: str = ""
    local_literature_context_digest: str = ""
    key_cited_work_ids: list[str] = Field(default_factory=list)
    literature_evidence: list[QuestionFormationLiteratureEvidence] = Field(default_factory=list)
    evidence_bindings: list[QuestionFormationEvidenceBinding] = Field(default_factory=list)
    review_status: QuestionFormationTraceReviewStatus = QuestionFormationTraceReviewStatus.DRAFT

    @field_validator(
        "trace_id",
        "unresolved_gap",
        "dataset_feature_noticed",
        "opportunity_inference",
        "resulting_question",
        "expected_scientific_consequence",
        "scientific_significance",
        "transferable_reasoning_pattern",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionFormationTrace scientific fields must be non-empty")
        return value

    @field_validator("background_claims")
    @classmethod
    def require_background_claims(cls, value: list[str]) -> list[str]:
        cleaned = [claim.strip() for claim in value if claim.strip()]
        if not cleaned:
            raise ValueError("QuestionFormationTrace requires at least one background claim")
        return cleaned

    @model_validator(mode="after")
    def require_span_evidence_for_reviewed_trace(self) -> QuestionFormationTrace:
        if (
            self.review_status != QuestionFormationTraceReviewStatus.DRAFT
            and not self.evidence_span_ids
        ):
            raise ValueError("span-verified or expert-reviewed trace requires evidence_span_ids")
        if self.review_status != QuestionFormationTraceReviewStatus.DRAFT:
            if not self.evidence_bindings:
                raise ValueError(
                    "span-verified or expert-reviewed trace requires evidence_bindings"
                )
            binding_roles = {binding.role for binding in self.evidence_bindings}
            literature_roles = {
                QuestionFormationEvidenceBindingRole.LITERATURE_GAP,
                QuestionFormationEvidenceBindingRole.THEORETICAL_TENSION,
                QuestionFormationEvidenceBindingRole.METHOD_OR_CONSTRUCT_PRECEDENT,
            }
            dataset_or_question_roles = {
                QuestionFormationEvidenceBindingRole.DATASET_OPPORTUNITY,
                QuestionFormationEvidenceBindingRole.QUESTION_FORMING_MOVE,
            }
            if not binding_roles.intersection(literature_roles):
                raise ValueError(
                    "span-verified or expert-reviewed trace requires literature-side evidence binding"
                )
            if not binding_roles.intersection(dataset_or_question_roles):
                raise ValueError(
                    "span-verified or expert-reviewed trace requires dataset/question evidence binding"
                )
            binding_span_ids = {
                span_id for binding in self.evidence_bindings for span_id in binding.source_span_ids
            }
            missing_binding_span_ids = binding_span_ids - set(self.evidence_span_ids)
            if missing_binding_span_ids:
                raise ValueError(
                    "reviewed trace evidence_bindings source_span_ids must appear in "
                    "evidence_span_ids: " + ", ".join(sorted(missing_binding_span_ids))
                )
        if self.literature_evidence:
            if not self.local_literature_context_id.strip():
                raise ValueError("literature-backed trace requires local_literature_context_id")
            if not self.local_literature_context_digest.strip():
                raise ValueError("literature-backed trace requires local_literature_context_digest")
            if self.key_cited_work_ids:
                unknown = {
                    evidence.cited_work_id
                    for evidence in self.literature_evidence
                    if evidence.cited_work_id not in self.key_cited_work_ids
                }
                if unknown:
                    raise ValueError(
                        "literature_evidence cites works outside key_cited_work_ids: "
                        + ", ".join(sorted(unknown))
                    )
            evidence_keys = [
                (evidence.cited_work_id, evidence.role.value)
                for evidence in self.literature_evidence
            ]
            duplicates = sorted({key for key in evidence_keys if evidence_keys.count(key) > 1})
            if duplicates:
                formatted = [f"{cited_work_id}:{role}" for cited_work_id, role in duplicates]
                raise ValueError(
                    "literature_evidence contains duplicate cited-work roles: "
                    + ", ".join(formatted)
                )
            if self.evidence_bindings:
                binding_cited_work_ids = {
                    cited_work_id
                    for binding in self.evidence_bindings
                    for cited_work_id in binding.cited_work_ids
                }
                unmapped_literature_ids = sorted(
                    {
                        evidence.cited_work_id
                        for evidence in self.literature_evidence
                        if evidence.cited_work_id not in binding_cited_work_ids
                    }
                )
                if unmapped_literature_ids:
                    raise ValueError(
                        "literature_evidence cited works must appear in formation "
                        "evidence_bindings: " + ", ".join(unmapped_literature_ids)
                    )
        if self.evidence_bindings:
            binding_cited_work_ids = {
                cited_work_id
                for binding in self.evidence_bindings
                for cited_work_id in binding.cited_work_ids
            }
            if binding_cited_work_ids:
                if not self.local_literature_context_id.strip():
                    raise ValueError(
                        "cited-work evidence bindings require local_literature_context_id"
                    )
                if not self.local_literature_context_digest.strip():
                    raise ValueError(
                        "cited-work evidence bindings require local_literature_context_digest"
                    )
                if self.key_cited_work_ids:
                    unknown_binding_ids = binding_cited_work_ids - set(self.key_cited_work_ids)
                    if unknown_binding_ids:
                        raise ValueError(
                            "evidence_bindings cite works outside key_cited_work_ids: "
                            + ", ".join(sorted(unknown_binding_ids))
                        )
            if self.local_literature_context_id.strip():
                literature_roles = {
                    QuestionFormationEvidenceBindingRole.LITERATURE_GAP,
                    QuestionFormationEvidenceBindingRole.THEORETICAL_TENSION,
                    QuestionFormationEvidenceBindingRole.METHOD_OR_CONSTRUCT_PRECEDENT,
                }
                dataset_or_question_roles = {
                    QuestionFormationEvidenceBindingRole.DATASET_OPPORTUNITY,
                    QuestionFormationEvidenceBindingRole.QUESTION_FORMING_MOVE,
                }
                unsupported_literature_roles = [
                    binding.role.value
                    for binding in self.evidence_bindings
                    if binding.role in literature_roles
                    and not (binding.cited_work_ids or binding.citation_context_ids)
                ]
                if unsupported_literature_roles:
                    raise ValueError(
                        "paper-local literature traces require cited-work or citation-context "
                        "evidence for literature-side bindings: "
                        + ", ".join(sorted(set(unsupported_literature_roles)))
                    )
                unsupported_dataset_roles = [
                    binding.role.value
                    for binding in self.evidence_bindings
                    if binding.role in dataset_or_question_roles and not binding.source_span_ids
                ]
                if unsupported_dataset_roles:
                    raise ValueError(
                        "paper-local literature traces require source_span_ids for "
                        "dataset/question evidence bindings: "
                        + ", ".join(sorted(set(unsupported_dataset_roles)))
                    )
        return self


class QuestionPatternCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern_id: str
    pattern_name: str
    starting_scientific_state: list[str] = Field(default_factory=list)
    unresolved_tension_pattern: str
    dataset_cues: list[str] = Field(default_factory=list)
    question_formation_move: str
    scientific_payoff: str
    positive_result_consequence: str
    negative_result_consequence: str
    common_failure_modes: list[str] = Field(default_factory=list)
    non_transferable_details: list[str] = Field(default_factory=list)
    source_case_ids: list[str] = Field(default_factory=list)
    source_trace_ids: list[str] = Field(default_factory=list)
    transfer_scope: QuestionPatternTransferScope = QuestionPatternTransferScope.CROSS_PAPER
    review_status: QuestionPatternReviewStatus = QuestionPatternReviewStatus.DRAFT

    @field_validator(
        "pattern_id",
        "pattern_name",
        "unresolved_tension_pattern",
        "question_formation_move",
        "scientific_payoff",
        "positive_result_consequence",
        "negative_result_consequence",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionPatternCard core fields must be non-empty")
        return value

    @model_validator(mode="after")
    def require_traceable_reviewed_pattern(self) -> QuestionPatternCard:
        # Applies to BOTH accepted authorities (AI_REVIEWED and EXPERT_REVIEWED): a reviewed pattern
        # must be traceable regardless of which honest tier accepted it.
        if is_accepted_authority(self.review_status):
            if not self.source_case_ids:
                raise ValueError("reviewed pattern requires source_case_ids")
            if not self.source_trace_ids:
                raise ValueError("reviewed pattern requires source_trace_ids")
            if self.transfer_scope == QuestionPatternTransferScope.CROSS_PAPER:
                if len(set(self.source_case_ids)) < 2:
                    raise ValueError("cross-paper reviewed pattern requires two source cases")
                if len(set(self.source_trace_ids)) < 2:
                    raise ValueError("cross-paper reviewed pattern requires two source traces")
            if (
                self.transfer_scope == QuestionPatternTransferScope.PAPER_SPECIFIC
                and not self.non_transferable_details
            ):
                raise ValueError(
                    "paper-specific reviewed pattern requires non-transferable details"
                )
        return self

    @property
    def is_proposal_ready(self) -> bool:
        return is_accepted_authority(self.review_status)


class QuestionPatternReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: str
    pattern_id: str
    status: QuestionPatternReviewStatus = QuestionPatternReviewStatus.DRAFT
    reviewer: str = ""
    fidelity_passed: bool = False
    transferable: bool = False
    required_changes: list[str] = Field(default_factory=list)
    notes: str = ""
    reviewed_at: datetime | None = None

    @field_validator("review_id", "pattern_id")
    @classmethod
    def require_identifier(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionPatternReview identifiers must be non-empty")
        return value

    @model_validator(mode="after")
    def require_review_decision_metadata(self) -> QuestionPatternReview:
        if self.status == QuestionPatternReviewStatus.DRAFT:
            return self
        if not self.reviewer.strip():
            raise ValueError("non-draft pattern review requires reviewer")
        if not self.notes.strip():
            raise ValueError("non-draft pattern review requires notes")
        if self.status == QuestionPatternReviewStatus.EXPERT_REVIEWED:
            if not self.fidelity_passed:
                raise ValueError("expert-reviewed pattern requires fidelity_passed")
            if not self.transferable:
                raise ValueError("expert-reviewed pattern requires transferable")
            if self.required_changes:
                raise ValueError("expert-reviewed pattern cannot have required_changes")
        if self.status == QuestionPatternReviewStatus.NEEDS_REVISION and not self.required_changes:
            raise ValueError("needs_revision pattern review requires required_changes")
        if self.reviewed_at is None:
            self.reviewed_at = datetime.now(UTC)
        return self


class QuestionPatternBankEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern_id: str
    pattern_path: str
    status: QuestionPatternReviewStatus = QuestionPatternReviewStatus.DRAFT
    transfer_scope: QuestionPatternTransferScope = QuestionPatternTransferScope.CROSS_PAPER
    source_case_ids: list[str] = Field(default_factory=list)
    source_trace_ids: list[str] = Field(default_factory=list)
    pattern_digest: str = ""

    @field_validator("pattern_id", "pattern_path")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionPatternBankEntry identifiers must be non-empty")
        return value


class QuestionPatternBankManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_id: str = "question-pattern-bank-v0"
    corpus_version: str = "r5-question-pattern-bank-v1"
    extracted_patterns_dir: str = "corpus/patterns/extracted"
    reviewed_patterns_dir: str = "corpus/patterns/reviewed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    entries: list[QuestionPatternBankEntry] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_duplicate_pattern_ids(self) -> QuestionPatternBankManifest:
        ids = [entry.pattern_id for entry in self.entries]
        duplicates = sorted({pattern_id for pattern_id in ids if ids.count(pattern_id) > 1})
        if duplicates:
            raise ValueError(
                "QuestionPatternBankManifest contains duplicate pattern_ids: "
                + ", ".join(duplicates)
            )
        return self

    def status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self.entries:
            counts[entry.status.value] = counts.get(entry.status.value, 0) + 1
        return counts
