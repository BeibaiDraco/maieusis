from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...io import load_model
from ...schemas.cited_literature import (
    CitationContextRole,
    CitationSelectionStatus,
    PaperLocalLiteratureContext,
    literature_context_digest,
)
from ...schemas.paper_case import PaperCase
from ...schemas.question_pattern import (
    QuestionFormationLiteratureEvidence,
    QuestionFormationLiteratureRole,
    QuestionFormationTrace,
)
from .citation_importance import (
    CITATION_IMPORTANCE_SELECTOR_PRODUCT_PROMPT_VERSION,
    CITATION_IMPORTANCE_SELECTOR_PROMPT_VERSION,
)

_SUPPORTED_CITATION_SELECTOR_PROMPT_VERSIONS = {
    CITATION_IMPORTANCE_SELECTOR_PROMPT_VERSION,
    CITATION_IMPORTANCE_SELECTOR_PRODUCT_PROMPT_VERSION,
}


class SelectedCitedWorkTraceEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cited_work_id: str
    title: str = ""
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    selection_rank: int = Field(ge=1)
    selection_importance: str = ""
    selection_rationale: str
    role_hints: list[QuestionFormationLiteratureRole] = Field(default_factory=list)
    evidence_context_ids: list[str] = Field(default_factory=list)
    citation_context_snippets: list[str] = Field(default_factory=list)
    abstract_status: str = ""
    abstract: str = ""
    abstract_evidence_used: bool = False

    @model_validator(mode="after")
    def validate_abstract_evidence_authority(self) -> SelectedCitedWorkTraceEvidence:
        if self.abstract_evidence_used and (
            self.abstract_status != "retrieved" or not self.abstract.strip()
        ):
            raise ValueError(
                "trace abstract evidence requires a retrieved, non-empty cited-work abstract"
            )
        return self


class PaperLocalLiteratureTraceContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_case_id: str
    local_literature_context_id: str
    local_literature_context_digest: str
    key_cited_work_ids: list[str] = Field(default_factory=list)
    selected_cited_works: list[SelectedCitedWorkTraceEvidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_selected_ids(self) -> PaperLocalLiteratureTraceContext:
        selected_ids = [work.cited_work_id for work in self.selected_cited_works]
        if selected_ids != self.key_cited_work_ids:
            raise ValueError("selected_cited_works must follow key_cited_work_ids order")
        if len(selected_ids) != len(set(selected_ids)):
            raise ValueError("selected_cited_works contains duplicate cited_work_id values")
        return self


def build_paper_local_literature_trace_context(
    *,
    paper_case: PaperCase,
    literature_context: PaperLocalLiteratureContext,
) -> PaperLocalLiteratureTraceContext:
    _validate_case_literature_links(paper_case=paper_case, literature_context=literature_context)
    selection = literature_context.importance_selection
    if selection is None or selection.selection_status != CitationSelectionStatus.SELECTED:
        raise ValueError("Paper-local literature context requires selected key citations")
    if (
        selection.prompt_version not in _SUPPORTED_CITATION_SELECTOR_PROMPT_VERSIONS
        and literature_context.review_status.value != "expert_reviewed"
    ):
        raise ValueError(
            "Paper-local literature selection uses stale prompt version "
            f"{selection.prompt_version}; regenerate with "
            f"{CITATION_IMPORTANCE_SELECTOR_PRODUCT_PROMPT_VERSION} (or the frozen "
            f"{CITATION_IMPORTANCE_SELECTOR_PROMPT_VERSION} compatibility version) or "
            "expert-review the sidecar"
        )
    works_by_id = {work.cited_work_id: work for work in literature_context.cited_works}
    contexts_by_id = {
        context.context_id: context for context in literature_context.citation_contexts
    }
    selected: list[SelectedCitedWorkTraceEvidence] = []
    for item in selection.items:
        work = works_by_id[item.cited_work_id]
        contexts = [
            contexts_by_id[context_id]
            for context_id in item.evidence_context_ids
            if context_id in contexts_by_id
        ]
        selected.append(
            SelectedCitedWorkTraceEvidence(
                cited_work_id=item.cited_work_id,
                title=work.title,
                authors=work.authors,
                year=work.year,
                selection_rank=item.rank,
                selection_importance=item.importance.value,
                selection_rationale=item.rationale,
                role_hints=_role_hints(context.inferred_role for context in contexts),
                evidence_context_ids=item.evidence_context_ids,
                citation_context_snippets=[context.local_context for context in contexts],
                abstract_status=work.abstract_status.value,
                abstract=work.abstract,
                abstract_evidence_used=item.abstract_evidence_used,
            )
        )
    return PaperLocalLiteratureTraceContext(
        paper_case_id=paper_case.paper_case_id,
        local_literature_context_id=literature_context.context_id,
        local_literature_context_digest=literature_context_digest(literature_context),
        key_cited_work_ids=selection.selected_cited_work_ids,
        selected_cited_works=selected,
    )


def validate_trace_literature_evidence(
    *,
    trace: QuestionFormationTrace,
    trace_context: PaperLocalLiteratureTraceContext,
) -> list[str]:
    issues: list[str] = []
    if not trace.literature_evidence and not trace.evidence_bindings:
        return issues
    has_literature_references = bool(trace.literature_evidence) or any(
        binding.cited_work_ids or binding.citation_context_ids
        for binding in trace.evidence_bindings
    )
    if (
        has_literature_references
        and trace.local_literature_context_id != trace_context.local_literature_context_id
    ):
        issues.append("formation_trace local_literature_context_id does not match PaperCase")
    if (
        has_literature_references
        and trace.local_literature_context_digest != trace_context.local_literature_context_digest
    ):
        issues.append("formation_trace local_literature_context_digest does not match sidecar")
    selected_ids = set(trace_context.key_cited_work_ids)
    unknown = sorted(
        evidence.cited_work_id
        for evidence in trace.literature_evidence
        if evidence.cited_work_id not in selected_ids
    )
    if unknown:
        issues.append(
            "formation_trace literature_evidence cites non-selected works: " + ", ".join(unknown)
        )
    binding_unknown = sorted(
        cited_work_id
        for binding in trace.evidence_bindings
        for cited_work_id in binding.cited_work_ids
        if cited_work_id not in selected_ids
    )
    if binding_unknown:
        issues.append(
            "formation_trace evidence_bindings cite non-selected works: "
            + ", ".join(binding_unknown)
        )
    context_ids = {
        context_id
        for work in trace_context.selected_cited_works
        for context_id in work.evidence_context_ids
    }
    context_ids_by_work = {
        work.cited_work_id: set(work.evidence_context_ids)
        for work in trace_context.selected_cited_works
    }
    unknown_contexts = sorted(
        context_id
        for evidence in trace.literature_evidence
        for context_id in evidence.evidence_context_ids
        if context_id not in context_ids
    )
    if unknown_contexts:
        issues.append(
            "formation_trace literature_evidence references unknown citation contexts: "
            + ", ".join(unknown_contexts)
        )
    binding_unknown_contexts = sorted(
        context_id
        for binding in trace.evidence_bindings
        for context_id in binding.citation_context_ids
        if context_id not in context_ids
    )
    if binding_unknown_contexts:
        issues.append(
            "formation_trace evidence_bindings reference unknown citation contexts: "
            + ", ".join(binding_unknown_contexts)
        )
    binding_wrong_work_contexts = sorted(
        context_id
        for binding in trace.evidence_bindings
        if binding.cited_work_ids
        for context_id in binding.citation_context_ids
        if context_id
        not in set().union(
            *[
                context_ids_by_work.get(cited_work_id, set())
                for cited_work_id in binding.cited_work_ids
            ]
        )
    )
    if binding_wrong_work_contexts:
        issues.append(
            "formation_trace evidence_bindings reference citation contexts from another cited work: "
            + ", ".join(binding_wrong_work_contexts)
        )
    return issues


def default_trace_literature_evidence(
    trace_context: PaperLocalLiteratureTraceContext,
) -> list[QuestionFormationLiteratureEvidence]:
    evidence: list[QuestionFormationLiteratureEvidence] = []
    for work in trace_context.selected_cited_works:
        role = work.role_hints[0] if work.role_hints else QuestionFormationLiteratureRole.OTHER
        evidence.append(
            QuestionFormationLiteratureEvidence(
                cited_work_id=work.cited_work_id,
                role=role,
                rationale=work.selection_rationale,
                selection_rank=work.selection_rank,
                selection_importance=work.selection_importance,
                evidence_context_ids=work.evidence_context_ids,
                abstract_evidence_used=work.abstract_evidence_used,
            )
        )
    return evidence


def load_paper_local_literature_trace_context(
    *,
    paper_case: PaperCase,
    corpus_root: str | Path = "corpus",
) -> PaperLocalLiteratureTraceContext | None:
    if not paper_case.local_literature_context_id:
        return None
    path = (
        Path(corpus_root)
        / "cited_literature"
        / f"{paper_case.paper_case_id}.paper_local_literature.yaml"
    )
    if not path.exists():
        return None
    context = load_model(path, PaperLocalLiteratureContext)
    return build_paper_local_literature_trace_context(
        paper_case=paper_case,
        literature_context=context,
    )


def _validate_case_literature_links(
    *,
    paper_case: PaperCase,
    literature_context: PaperLocalLiteratureContext,
) -> None:
    digest = literature_context_digest(literature_context)
    if literature_context.paper_case_id != paper_case.paper_case_id:
        raise ValueError("PaperLocalLiteratureContext paper_case_id does not match PaperCase")
    if paper_case.local_literature_context_id != literature_context.context_id:
        raise ValueError("PaperCase local_literature_context_id does not match sidecar")
    if paper_case.local_literature_context_digest != digest:
        raise ValueError("PaperCase local_literature_context_digest does not match sidecar")
    selection = literature_context.importance_selection
    if selection is not None and paper_case.key_cited_work_ids != selection.selected_cited_work_ids:
        raise ValueError("PaperCase key_cited_work_ids do not match sidecar selection")


def _role_hints(roles: Iterable[CitationContextRole]) -> list[QuestionFormationLiteratureRole]:
    mapped: list[QuestionFormationLiteratureRole] = []
    for role in roles:
        mapped_role = _role_hint(role)
        if mapped_role not in mapped:
            mapped.append(mapped_role)
    return mapped


def _role_hint(role: CitationContextRole) -> QuestionFormationLiteratureRole:
    mapping = {
        CitationContextRole.BACKGROUND: QuestionFormationLiteratureRole.MOTIVATING_PRIOR,
        CitationContextRole.NEAREST_PRIOR: QuestionFormationLiteratureRole.MOTIVATING_PRIOR,
        CitationContextRole.UNRESOLVED_TENSION: (
            QuestionFormationLiteratureRole.UNRESOLVED_TENSION
        ),
        CitationContextRole.CONSTRUCT_DEFINITION: (
            QuestionFormationLiteratureRole.CONSTRUCT_DEFINITION
        ),
        CitationContextRole.METHOD_PRECEDENT: QuestionFormationLiteratureRole.METHOD_PRECEDENT,
        CitationContextRole.DATASET_PRECEDENT: QuestionFormationLiteratureRole.DATASET_PRECEDENT,
        CitationContextRole.CONTRAST_CASE: QuestionFormationLiteratureRole.CONTRAST_CASE,
        CitationContextRole.OTHER: QuestionFormationLiteratureRole.OTHER,
    }
    return mapping[role]
