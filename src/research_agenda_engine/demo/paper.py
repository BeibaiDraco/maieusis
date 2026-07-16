"""Deterministic demo paper case + literature + formation-trace payloads.

The config-reachable
``subscription_only_demo`` deterministic generation assets (public_optional). Demo mode is
an explicit mock + FakePlannerHost workflow demonstration — never a scientific-quality
claim (the demo banner and development_model_surrogate authority labels flow to every
output surface).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from research_agenda_engine.schemas.cited_literature import (
    CitationContext,
    CitationContextRole,
    CitationImportance,
    CitationImportanceSelection,
    CitationImportanceSelectionItem,
    CitationSelectionPolicy,
    CitedWorkRef,
    PaperLocalLiteratureContext,
    literature_context_digest,
)
from research_agenda_engine.schemas.paper_case import (
    EvidenceSpan,
    PaperCase,
    PaperCaseReview,
    PaperCaseReviewStatus,
    PaperDatasetDescription,
    PaperKnowledgeState,
    PaperScientificQuestion,
    PaperType,
    QuestionDesignPattern,
)

_DEMO_CREATED_AT = datetime(2020, 1, 1, tzinfo=UTC)


def _linked_case_and_literature(
    *, bad_digest: bool = False
) -> tuple[PaperCase, PaperLocalLiteratureContext]:
    literature_context = _literature_context()
    selection = literature_context.importance_selection
    assert selection is not None
    digest = "bad-digest" if bad_digest else literature_context_digest(literature_context)
    paper_case = PaperCase(
        paper_case_id="paper-1",
        citation="Fixture source paper",
        paper_type=PaperType.SECONDARY_DATASET_REUSE,
        dataset_description=PaperDatasetDescription(
            dataset_name="fixture dataset",
            task_or_design="decision task",
            relevant_affordances=["reusable task cue"],
        ),
        knowledge_state=PaperKnowledgeState(
            motivating_claims=["Prior work disagrees about two accounts."],
            unresolved_tension="which account explains the behavior",
        ),
        scientific_question=PaperScientificQuestion(
            original_question="Can a reusable dataset cue separate two accounts?",
            competing_explanations=["account one", "account two"],
        ),
        question_design=QuestionDesignPattern(
            epistemic_move="use dataset cue to separate explanations",
            why_dataset_can_answer="the dataset contains the broad task cue",
            why_question_was_valuable="either result would update the debate",
            novelty_relative_to_parent_dataset="new use of an existing dataset",
        ),
        local_literature_context_id=literature_context.context_id,
        local_literature_context_digest=digest,
        key_cited_work_ids=selection.selected_cited_work_ids,
        evidence_spans=[
            EvidenceSpan(
                field="knowledge_state.unresolved_tension",
                page=1,
                section="Introduction",
                quote_or_span="Prior work disagrees about two accounts.",
                source_file="fixture.pdf",
                source_span_id="span-valid",
            )
        ],
        review=PaperCaseReview(status=PaperCaseReviewStatus.EXPERT_REVIEWED),
        created_at=_DEMO_CREATED_AT,
    )
    return paper_case, literature_context


def _literature_context() -> PaperLocalLiteratureContext:
    selection = CitationImportanceSelection(
        selection_id="selection-1",
        paper_case_id="paper-1",
        all_input_cited_work_ids=["cw-1", "cw-2"],
        selected_cited_work_ids=["cw-1", "cw-2"],
        selection_policy=CitationSelectionPolicy.EVIDENCE_DRIVEN,
        selection_size_requested=2,
        selection_size_actual=2,
        provider_id="mock",
        model_id="fixture",
        prompt_version="citation_importance_selector/v3",
        input_digest="0" * 64,
        created_at=_DEMO_CREATED_AT,
        items=[
            CitationImportanceSelectionItem(
                cited_work_id="cw-1",
                rank=1,
                importance=CitationImportance.CENTRAL,
                rationale="This cited work supplies the unresolved tension.",
                evidence_context_ids=["cc-1"],
            ),
            CitationImportanceSelectionItem(
                cited_work_id="cw-2",
                rank=2,
                importance=CitationImportance.CONTEXTUAL,
                rationale="This cited work supplies background.",
                evidence_context_ids=["cc-2"],
            ),
        ],
    )
    return PaperLocalLiteratureContext(
        context_id="pll-paper-1",
        paper_case_id="paper-1",
        source_paper_id="paper-1",
        source_sha256="abc",
        cited_works=[
            CitedWorkRef(cited_work_id="cw-1", title="Central cited work", year=2020),
            CitedWorkRef(cited_work_id="cw-2", title="Context cited work", year=2021),
        ],
        citation_contexts=[
            CitationContext(
                context_id="cc-1",
                cited_work_id="cw-1",
                source_span_id="source-span-1",
                page=1,
                section="Introduction",
                local_context="The cited work leaves the account unresolved.",
                mention_text="[1]",
                inferred_role=CitationContextRole.UNRESOLVED_TENSION,
            ),
            CitationContext(
                context_id="cc-2",
                cited_work_id="cw-2",
                source_span_id="source-span-2",
                page=1,
                section="Introduction",
                local_context="The second cited work supplies broader background.",
                mention_text="[2]",
                inferred_role=CitationContextRole.BACKGROUND,
            ),
        ],
        importance_selection=selection,
        created_at=_DEMO_CREATED_AT,
    )


def _trace_payload(
    output_model: type[BaseModel],
    *,
    cited_work_id: str = "cw-1",
    evidence_context_ids: list[str] | None = None,
    evidence_span_ids: list[str] | None = None,
    review_status: str = "draft",
    binding_cited_work_id: str | None = None,
    binding_context_ids: list[str] | None = None,
) -> Any:
    return output_model.model_validate(
        _trace_payload_dict(
            cited_work_id=cited_work_id,
            evidence_context_ids=evidence_context_ids,
            evidence_span_ids=evidence_span_ids,
            review_status=review_status,
            binding_cited_work_id=binding_cited_work_id,
            binding_context_ids=binding_context_ids,
        )
    ).model_dump(mode="json")


def _trace_payload_dict(
    *,
    cited_work_id: str = "cw-1",
    evidence_context_ids: list[str] | None = None,
    evidence_span_ids: list[str] | None = None,
    review_status: str = "draft",
    binding_cited_work_id: str | None = None,
    binding_context_ids: list[str] | None = None,
) -> dict[str, Any]:
    binding_cited_work_id = binding_cited_work_id or cited_work_id
    binding_context_ids = (
        binding_context_ids
        if binding_context_ids is not None
        else evidence_context_ids
        if evidence_context_ids is not None
        else ["cc-1"]
    )
    return {
        "trace_id": "trace-draft-paper-1",
        "background_claims": ["Prior work leaves two accounts unresolved."],
        "unresolved_gap": "The source paper targets which account survives.",
        "dataset_feature_noticed": "The dataset has a reusable task cue.",
        "opportunity_inference": "The cue can separate the accounts.",
        "resulting_question": "Can a reusable dataset cue separate two accounts?",
        "expected_scientific_consequence": "Either result would update the debate.",
        "scientific_significance": (
            "The question is valuable because it shows how reusable data can adjudicate "
            "a live scientific tension."
        ),
        "transferable_reasoning_pattern": (
            "Use selected prior literature plus a dataset cue to sharpen a gap."
        ),
        "evidence_span_ids": evidence_span_ids or ["span-valid"],
        "literature_evidence": [
            {
                "cited_work_id": cited_work_id,
                "role": "unresolved_tension",
                "rationale": "This selected citation motivates the unresolved tension.",
                "selection_rank": 1,
                "selection_importance": "central",
                "evidence_context_ids": evidence_context_ids
                if evidence_context_ids is not None
                else ["cc-1"],
            }
        ],
        "evidence_bindings": [
            {
                "role": "theoretical_tension",
                "source_span_ids": evidence_span_ids or ["span-valid"],
                "cited_work_ids": [binding_cited_work_id],
                "citation_context_ids": binding_context_ids,
                "rationale": "This binding links selected literature to the unresolved tension.",
            },
            {
                "role": "dataset_opportunity",
                "source_span_ids": evidence_span_ids or ["span-valid"],
                "rationale": "This binding links the PaperCase source span to the dataset cue.",
            },
        ],
        "review_status": review_status,
    }
