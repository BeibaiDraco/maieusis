from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..provenance import stable_hash
from .paper_ingest import LicenseClass


class ReferenceResolutionStatus(StrEnum):
    LOCAL_REFERENCE_EXTRACTED = "local_reference_extracted"
    EXTERNAL_ONLY = "external_only"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"


class AbstractRetrievalStatus(StrEnum):
    RETRIEVED = "retrieved"
    UNAVAILABLE = "unavailable"
    NOT_ATTEMPTED = "not_attempted"


class CitationContextRole(StrEnum):
    BACKGROUND = "background"
    NEAREST_PRIOR = "nearest_prior"
    UNRESOLVED_TENSION = "unresolved_tension"
    CONSTRUCT_DEFINITION = "construct_definition"
    METHOD_PRECEDENT = "method_precedent"
    DATASET_PRECEDENT = "dataset_precedent"
    CONTRAST_CASE = "contrast_case"
    OTHER = "other"


class CitationImportance(StrEnum):
    CENTRAL = "central"
    SUPPORTING = "supporting"
    CONTEXTUAL = "contextual"
    UNCERTAIN = "uncertain"


class CitationSelectionStatus(StrEnum):
    NOT_ATTEMPTED = "not_attempted"
    SELECTED = "selected"
    CONTEXT_TOO_LARGE = "context_too_large"
    MODEL_FAILED = "model_failed"
    # The product (evidence-driven) selector found no cited work with defensible question-forming
    # support — an honest scientific terminal, NOT an infrastructure failure.
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class CitationSelectionPolicy(StrEnum):
    # Legacy 10-15 (or all-if-fewer-than-10) — FROZEN for the reproducible 15-paper EXPERT baseline.
    FIXED_COUNT = "fixed_count"
    # Product: the count is whatever the evidence supports (>= 1, may be fewer than 10). Lets the
    # citation gate's revise converge on the defensible subset.
    EVIDENCE_DRIVEN = "evidence_driven"


class PaperLocalLiteratureReviewStatus(StrEnum):
    DRAFT = "draft"
    LOCAL_REFERENCE_EXTRACTED = "local_reference_extracted"
    ABSTRACTS_ATTEMPTED = "abstracts_attempted"
    AGENT_SELECTED = "agent_selected"
    # Independent-AI citation-importance gate accepted. Automated/non-human tier; see
    # schemas/review_authority.py.
    AI_REVIEWED = "ai_reviewed"
    EXPERT_REVIEWED = "expert_reviewed"


class RawReferenceEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_reference_id: str
    source_paper_id: str
    reference_index: int = Field(ge=1)
    raw_text: str
    source_block_id: str = ""
    source_span_id: str = ""
    section_title: str = ""
    page_number: int | None = Field(default=None, ge=1)
    title_hint: str = ""
    author_hint: str = ""
    year_hint: int | None = None
    doi_hint: str = ""
    pmid_hint: str = ""
    pmcid_hint: str = ""
    arxiv_id_hint: str = ""

    @field_validator("raw_reference_id", "source_paper_id", "raw_text")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("RawReferenceEntry core fields must be non-empty")
        return value


class CitedWorkIdentifiers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    openalex_id: str = ""
    semantic_scholar_id: str = ""
    arxiv_id: str = ""


class CitedWorkRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cited_work_id: str
    raw_reference_id: str = ""
    local_reference_index: int | None = Field(default=None, ge=1)
    raw_reference: str = ""
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    identifiers: CitedWorkIdentifiers = Field(default_factory=CitedWorkIdentifiers)
    resolution_status: ReferenceResolutionStatus = ReferenceResolutionStatus.UNRESOLVED
    resolution_source: str = ""
    resolution_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    abstract: str = ""
    abstract_status: AbstractRetrievalStatus = AbstractRetrievalStatus.NOT_ATTEMPTED
    abstract_source: str = ""
    # P4: rights provenance for the retrieved abstract — the license class asserted by the provider
    # that supplied it (OpenAlex/Crossref/Europe PMC OA metadata). Honesty/audit only; no user-facing
    # surface reproduces cited-work abstracts verbatim, so this is not a render gate.
    abstract_license_class: LicenseClass = LicenseClass.UNKNOWN
    retrieval_failure_reason: str = ""
    provider_record_ids: list[str] = Field(default_factory=list)

    @field_validator("cited_work_id")
    @classmethod
    def require_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("CitedWorkRef cited_work_id must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_abstract_status(self) -> CitedWorkRef:
        if self.abstract_status == AbstractRetrievalStatus.RETRIEVED:
            if not self.abstract.strip():
                raise ValueError("retrieved cited abstract must be non-empty")
            if not self.abstract_source.strip():
                raise ValueError("retrieved cited abstract requires abstract_source")
        if (
            self.abstract_status == AbstractRetrievalStatus.UNAVAILABLE
            and not self.retrieval_failure_reason.strip()
        ):
            raise ValueError("unavailable cited abstract requires failure reason")
        return self


class CitationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context_id: str
    cited_work_id: str
    source_span_id: str
    page: int | None = Field(default=None, ge=1)
    section: str = ""
    local_context: str
    mention_text: str = ""
    inferred_role: CitationContextRole = CitationContextRole.OTHER

    @field_validator("context_id", "cited_work_id", "source_span_id", "local_context")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("CitationContext core fields must be non-empty")
        return value


class CitationImportanceSelectionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cited_work_id: str
    rank: int = Field(ge=1)
    importance: CitationImportance
    rationale: str
    evidence_context_ids: list[str] = Field(default_factory=list)
    abstract_evidence_used: bool = False

    @field_validator("cited_work_id", "rationale")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Citation selection item fields must be non-empty")
        return value


class CitationImportanceSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selection_id: str
    paper_case_id: str
    selection_status: CitationSelectionStatus = CitationSelectionStatus.SELECTED
    # Legacy default keeps the fixed 10-15 rule (byte-safe); the product selector sets EVIDENCE_DRIVEN.
    selection_policy: CitationSelectionPolicy = CitationSelectionPolicy.FIXED_COUNT
    all_input_cited_work_ids: list[str] = Field(default_factory=list)
    selected_cited_work_ids: list[str] = Field(default_factory=list)
    selection_size_requested: int = Field(default=15, ge=1)
    selection_size_actual: int = Field(default=0, ge=0)
    provider_id: str = ""
    model_id: str = ""
    prompt_version: str
    input_digest: str
    items: list[CitationImportanceSelectionItem] = Field(default_factory=list)
    failure_reason: str = ""
    # CLIM-04 partition measurements (additive with defaults — every persisted v0.1 selection
    # still loads): when the full packet exceeded the budget, the selection was produced by
    # deterministic within-budget partitioning and these fields carry the honest measurements.
    partition_count: int = Field(default=1, ge=1)
    partition_measured_chars: int = Field(default=0, ge=0)
    partition_budget_chars: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("selection_id", "paper_case_id", "prompt_version", "input_digest")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("CitationImportanceSelection core fields must be non-empty")
        return value

    @field_validator("input_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("CitationImportanceSelection input_digest must be sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_selection(self) -> CitationImportanceSelection:
        if len(self.all_input_cited_work_ids) != len(set(self.all_input_cited_work_ids)):
            raise ValueError("all_input_cited_work_ids contains duplicates")
        if len(self.selected_cited_work_ids) != len(set(self.selected_cited_work_ids)):
            raise ValueError("selected_cited_work_ids contains duplicates")
        unknown = set(self.selected_cited_work_ids) - set(self.all_input_cited_work_ids)
        if unknown:
            raise ValueError(
                "selected citations absent from model input: " + ", ".join(sorted(unknown))
            )
        item_ids = [item.cited_work_id for item in self.items]
        if item_ids != self.selected_cited_work_ids:
            raise ValueError("selected_cited_work_ids must match selection item order")
        ranks = [item.rank for item in self.items]
        if sorted(ranks) != list(range(1, len(ranks) + 1)):
            raise ValueError("Citation selection ranks must be contiguous from 1")
        if self.selection_size_actual != len(self.selected_cited_work_ids):
            raise ValueError("selection_size_actual must equal selected citation count")
        if self.selection_status == CitationSelectionStatus.SELECTED:
            self._validate_selected_count()
        elif self.selected_cited_work_ids or self.items:
            raise ValueError("non-selected citation selection cannot include selected items")
        return self

    def _validate_selected_count(self) -> None:
        selected = len(self.selected_cited_work_ids)
        if self.selection_policy == CitationSelectionPolicy.EVIDENCE_DRIVEN:
            # Evidence-driven: any count >= 1 is valid (a defensible subset, possibly < 10). Zero
            # selections is not SELECTED — it is the insufficient_evidence terminal.
            if selected < 1:
                raise ValueError("evidence-driven selection must choose at least one cited work")
            return
        total = len(self.all_input_cited_work_ids)
        if total < 10:
            if selected != total:
                raise ValueError("fewer than ten cited works requires selecting all cited works")
            return
        upper = min(15, total)
        if selected < 10 or selected > upper:
            raise ValueError("citation selection must choose between 10 and 15 cited works")


class PaperLocalLiteratureContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context_id: str
    paper_case_id: str
    source_paper_id: str
    source_sha256: str = ""
    raw_references: list[RawReferenceEntry] = Field(default_factory=list)
    cited_works: list[CitedWorkRef] = Field(default_factory=list)
    citation_contexts: list[CitationContext] = Field(default_factory=list)
    importance_selection: CitationImportanceSelection | None = None
    review_status: PaperLocalLiteratureReviewStatus = PaperLocalLiteratureReviewStatus.DRAFT
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("context_id", "paper_case_id", "source_paper_id")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PaperLocalLiteratureContext ids must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_context_closure(self) -> PaperLocalLiteratureContext:
        cited_ids = [work.cited_work_id for work in self.cited_works]
        if len(cited_ids) != len(set(cited_ids)):
            raise ValueError("PaperLocalLiteratureContext contains duplicate cited_work_id values")
        raw_ids = {entry.raw_reference_id for entry in self.raw_references}
        missing_raw = [
            work.raw_reference_id
            for work in self.cited_works
            if work.raw_reference_id and work.raw_reference_id not in raw_ids
        ]
        if missing_raw:
            raise ValueError(
                "cited works reference unknown raw references: " + ", ".join(missing_raw)
            )
        context_ids = {context.context_id for context in self.citation_contexts}
        contexts_by_id = {context.context_id: context for context in self.citation_contexts}
        works_by_id = {work.cited_work_id: work for work in self.cited_works}
        for context in self.citation_contexts:
            if context.cited_work_id not in cited_ids:
                raise ValueError("citation context references unknown cited work")
        if self.importance_selection is not None:
            if set(self.importance_selection.all_input_cited_work_ids) != set(cited_ids):
                raise ValueError("citation selector must receive every cited work id")
            for item in self.importance_selection.items:
                unknown_contexts = set(item.evidence_context_ids) - context_ids
                if unknown_contexts:
                    raise ValueError(
                        "citation selection references unknown context ids: "
                        + ", ".join(sorted(unknown_contexts))
                    )
                foreign_contexts = [
                    context_id
                    for context_id in item.evidence_context_ids
                    if contexts_by_id[context_id].cited_work_id != item.cited_work_id
                ]
                if foreign_contexts:
                    raise ValueError(
                        "citation selection evidence contexts must belong to the selected cited work: "
                        + ", ".join(sorted(foreign_contexts))
                    )
                selected_work = works_by_id[item.cited_work_id]
                if item.abstract_evidence_used and (
                    selected_work.abstract_status != AbstractRetrievalStatus.RETRIEVED
                    or not selected_work.abstract.strip()
                ):
                    raise ValueError(
                        "citation selection may use abstract evidence only for a retrieved abstract"
                    )
                contexts_for_work = [
                    context
                    for context in self.citation_contexts
                    if context.cited_work_id == item.cited_work_id
                ]
                if (
                    contexts_for_work
                    and item.importance
                    in {CitationImportance.CENTRAL, CitationImportance.SUPPORTING}
                    and not item.evidence_context_ids
                ):
                    raise ValueError(
                        "central/supporting citation selection requires evidence context ids"
                    )
        return self


def literature_context_digest(context: PaperLocalLiteratureContext) -> str:
    """Canonical ``local_literature_context_digest`` — EXCLUDES ``selection_policy`` and each cited
    work's ``abstract_license_class``.

    Both fields were added after the reproducible 15-paper EXPERT baseline was frozen. Excluding them
    keeps those on-disk digests byte-identical (they never carried the fields) while the fields still
    persist on new artifacts for reload. ``abstract_license_class`` is rights PROVENANCE, not scientific
    content, so it must not invalidate the content digest. Every builder + validator of the digest must
    route through here so the stored and recomputed digests agree.
    """
    return stable_hash(
        context.model_dump(
            mode="json",
            exclude={
                # CLIM-04 partition measurements are packaging PROVENANCE, not scientific content:
                # excluding them keeps every pre-partition on-disk digest byte-identical while the
                # fields still persist on new artifacts for reload.
                "importance_selection": {
                    "selection_policy",
                    "partition_count",
                    "partition_measured_chars",
                    "partition_budget_chars",
                },
                "cited_works": {"__all__": {"abstract_license_class"}},
            },
        )
    )
