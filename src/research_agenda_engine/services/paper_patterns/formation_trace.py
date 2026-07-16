from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...schemas.paper_case import PaperCase, PaperCaseReviewStatus
from ...schemas.question_pattern import QuestionFormationTrace, QuestionFormationTraceReviewStatus
from ...schemas.review_authority import is_accepted_authority
from ..retrieval.paper_case_index import PaperCaseIndex
from .literature_context import (
    PaperLocalLiteratureTraceContext,
    load_paper_local_literature_trace_context,
    validate_trace_literature_evidence,
)

# AI_REVIEWED ranks above SPAN_VERIFIED (an independent-AI gate accepted it) and below the human tier.
# Without this entry a promoted AI_REVIEWED trace KeyErrors the rank lookup below.
_TRACE_STATUS_RANK = {
    QuestionFormationTraceReviewStatus.DRAFT: 0,
    QuestionFormationTraceReviewStatus.SPAN_VERIFIED: 1,
    QuestionFormationTraceReviewStatus.AI_REVIEWED: 2,
    QuestionFormationTraceReviewStatus.EXPERT_REVIEWED: 3,
}


class FormationTraceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_case_id: str
    citation: str = ""
    paper_type: str
    dataset_name: str = ""
    original_question: str = ""
    epistemic_move: str = ""
    formation_trace: QuestionFormationTrace
    local_literature: PaperLocalLiteratureTraceContext | None = None
    evidence_issues: list[str] = Field(default_factory=list)

    @property
    def is_usable(self) -> bool:
        return not self.evidence_issues


def collect_formation_trace_records(
    cases: list[PaperCase],
    *,
    local_literature_contexts: dict[str, PaperLocalLiteratureTraceContext] | None = None,
    minimum_status: QuestionFormationTraceReviewStatus = (
        QuestionFormationTraceReviewStatus.SPAN_VERIFIED
    ),
    require_expert_reviewed_case: bool = True,
    require_local_literature: bool = False,
    product_authority: bool = False,
) -> list[FormationTraceRecord]:
    """Collect usable formation-trace records.

    Legacy default (``product_authority=False``): a case must be ``EXPERT_REVIEWED`` and a trace must
    rank at/above ``minimum_status`` — unchanged, so the 15-paper EXPERT baseline stays byte-safe.
    Product path (``product_authority=True``): a case AND its trace are admitted on EITHER honest
    accepted authority (``is_accepted_authority`` — AI-reviewed or expert-reviewed), so an automated
    front-half chain (PaperCase → AI-reviewed trace → patterns) loads without a human import.
    """
    records: list[FormationTraceRecord] = []
    for case in cases:
        if product_authority:
            if not is_accepted_authority(case.review.status):
                continue
        elif (
            require_expert_reviewed_case
            and case.review.status != PaperCaseReviewStatus.EXPERT_REVIEWED
        ):
            continue
        if case.formation_trace is None:
            continue
        if product_authority:
            if not is_accepted_authority(case.formation_trace.review_status):
                continue
        elif (
            _TRACE_STATUS_RANK[case.formation_trace.review_status]
            < _TRACE_STATUS_RANK[minimum_status]
        ):
            continue
        local_literature = (
            local_literature_contexts.get(case.paper_case_id)
            if local_literature_contexts is not None
            else None
        )
        evidence_issues = case.formation_trace_evidence_issues()
        if local_literature is None and require_local_literature:
            evidence_issues.append("missing paper-local literature trace context")
        if local_literature is not None:
            evidence_issues.extend(
                validate_trace_literature_evidence(
                    trace=case.formation_trace,
                    trace_context=local_literature,
                )
            )
        records.append(
            FormationTraceRecord(
                paper_case_id=case.paper_case_id,
                citation=case.citation,
                paper_type=case.paper_type.value,
                dataset_name=case.dataset_description.dataset_name,
                original_question=case.scientific_question.original_question,
                epistemic_move=case.question_design.epistemic_move,
                formation_trace=case.formation_trace,
                local_literature=local_literature,
                evidence_issues=evidence_issues,
            )
        )
    return records


def load_reviewed_formation_trace_records(
    corpus_root: str | Path = "corpus",
    *,
    attach_local_literature: bool = True,
    minimum_status: QuestionFormationTraceReviewStatus = (
        QuestionFormationTraceReviewStatus.SPAN_VERIFIED
    ),
) -> list[FormationTraceRecord]:
    index = PaperCaseIndex.from_corpus(corpus_root)
    local_literature_contexts = (
        _load_local_literature_contexts(index.cases, corpus_root=corpus_root)
        if attach_local_literature
        else None
    )
    return collect_formation_trace_records(
        index.cases,
        local_literature_contexts=local_literature_contexts,
        minimum_status=minimum_status,
    )


def require_usable_trace_records(records: list[FormationTraceRecord]) -> None:
    unusable = [record for record in records if record.evidence_issues]
    if unusable:
        details = [
            f"{record.paper_case_id}: {'; '.join(record.evidence_issues)}" for record in unusable
        ]
        raise ValueError("Formation traces contain invalid evidence: " + " | ".join(details))


def _load_local_literature_contexts(
    cases: list[PaperCase], *, corpus_root: str | Path
) -> dict[str, PaperLocalLiteratureTraceContext]:
    contexts: dict[str, PaperLocalLiteratureTraceContext] = {}
    for case in cases:
        context = load_paper_local_literature_trace_context(
            paper_case=case,
            corpus_root=corpus_root,
        )
        if context is not None:
            contexts[case.paper_case_id] = context
    return contexts
