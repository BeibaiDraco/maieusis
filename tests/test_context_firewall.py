from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from research_agenda_engine.schemas.dataset_narrative import (
    DatasetNarrative,
    DatasetNarrativeReviewStatus,
    DatasetNarrativeSourceRef,
    DatasetNarrativeSourceType,
)
from research_agenda_engine.schemas.question_pattern import (
    QuestionPatternCard,
    QuestionPatternReviewStatus,
)
from research_agenda_engine.schemas.research_intent import ResearchIntent
from research_agenda_engine.schemas.scientific_context import (
    ScientificContextSnapshot,
    TopicEvidenceBrief,
    TopicEvidenceBriefReviewStatus,
    TopicEvidenceClaim,
    TopicEvidenceClaimStatus,
)


def _source_ref() -> DatasetNarrativeSourceRef:
    return DatasetNarrativeSourceRef(
        source_id="dataset-paper",
        source_type=DatasetNarrativeSourceType.DATASET_PAPER,
        locator="paper:methods",
    )


def _dataset_narrative(**overrides) -> DatasetNarrative:
    payload = {
        "dataset_narrative_id": "dn-1",
        "dataset_id": "ibl_bwm",
        "title": "IBL BWM narrative",
        "scientific_purpose": "standardized decision-making dataset",
        "population": "mice",
        "task_or_design": "decision task",
        "source_refs": [_source_ref()],
        "review_status": DatasetNarrativeReviewStatus.SOURCE_VERIFIED,
    }
    payload.update(overrides)
    return DatasetNarrative(**payload)


def _topic_brief(**overrides) -> TopicEvidenceBrief:
    claim = TopicEvidenceClaim(
        claim_id="claim-1",
        claim="coding geometry remains theoretically contested",
        status=TopicEvidenceClaimStatus.CONTESTED,
        source_refs=["paper-1"],
        confidence=0.7,
    )
    payload = {
        "brief_id": "brief-1",
        "topic_terms": ["coding geometry"],
        "canonical_scope": "systems neuroscience",
        "claims": [claim],
        "knowledge_cutoff": date(2026, 6, 25),
        "retrieval_manifest_digest": "a" * 64,
        "review_status": TopicEvidenceBriefReviewStatus.SOURCE_REVIEWED,
    }
    payload.update(overrides)
    return TopicEvidenceBrief(**payload)


def _pattern(**overrides) -> QuestionPatternCard:
    payload = {
        "pattern_id": "pattern-1",
        "pattern_name": "test invariance",
        "starting_scientific_state": ["representations may differ by region"],
        "unresolved_tension_pattern": "shared versus local geometry",
        "dataset_cues": ["standardized task", "multiple populations"],
        "question_formation_move": "test invariance across populations",
        "scientific_payoff": "distinguishes shared from local accounts",
        "positive_result_consequence": "supports shared geometry",
        "negative_result_consequence": "supports local geometry",
        "source_case_ids": ["paper-1", "paper-2"],
        "source_trace_ids": ["trace-1", "trace-2"],
        "review_status": QuestionPatternReviewStatus.EXPERT_REVIEWED,
    }
    payload.update(overrides)
    return QuestionPatternCard(**payload)


def _context(**overrides) -> ScientificContextSnapshot:
    payload = {
        "context_id": "ctx-1",
        "research_intent": ResearchIntent(topic_terms=["coding geometry"]),
        "dataset_narrative": _dataset_narrative(),
        "topic_evidence_brief": _topic_brief(),
        "question_patterns": [_pattern()],
        "retrieved_paper_case_ids": ["paper-1"],
        "retrieved_paper_case_digests": {"paper-1": "b" * 64},
        "prompt_policy_version": "r5_question_scientist/v1",
        "context_digest": "c" * 64,
    }
    payload.update(overrides)
    return ScientificContextSnapshot(**payload)


@pytest.mark.parametrize(
    "forbidden_text",
    [
        "CapabilityRegistry declared skill",
        "JointCoverageReport passed",
        "OperatorProbeReceipt exists",
        "QBench failure example",
        "confirmation outcome was positive",
        "ContractReadinessProof is ready",
        "AnalysisContract was locked",
    ],
)
def test_scientific_context_recursively_rejects_forbidden_research_intent_text(
    forbidden_text: str,
) -> None:
    with pytest.raises(ValueError, match="proposer-forbidden"):
        _context(
            research_intent=ResearchIntent(topic_terms=["coding"], constraints=[forbidden_text])
        )


def test_dataset_narrative_rejects_precise_coverage_language() -> None:
    with pytest.raises(ValueError, match="proposer-forbidden"):
        _dataset_narrative(known_high_level_limitations=["exact columns verified in local parquet"])


def test_context_rejects_r4_readiness_digest_in_nested_payload() -> None:
    with pytest.raises(ValueError, match="proposer-forbidden"):
        _context(retrieved_paper_case_digests={"paper-1": "R4 readiness proof digest"})


def test_context_rejects_source_unverified_dataset_in_serious_mode() -> None:
    with pytest.raises(ValueError, match="source-verified DatasetNarrative"):
        _context(
            dataset_narrative=_dataset_narrative(review_status=DatasetNarrativeReviewStatus.DRAFT)
        )


def test_context_rejects_unreviewed_patterns_in_serious_mode() -> None:
    with pytest.raises(ValueError, match="expert-reviewed QuestionPatternCards"):
        _context(question_patterns=[_pattern(review_status=QuestionPatternReviewStatus.DRAFT)])


def test_context_rejects_source_unreviewed_topic_brief_in_serious_mode() -> None:
    with pytest.raises(ValueError, match="source-reviewed TopicEvidenceBrief"):
        _context(
            topic_evidence_brief=_topic_brief(review_status=TopicEvidenceBriefReviewStatus.DRAFT)
        )


def test_context_rejects_extra_capability_registry_field() -> None:
    payload = _context().model_dump(mode="python")
    payload["capability_registry"] = {"executor_id": "ibl-agent"}

    with pytest.raises(ValidationError):
        ScientificContextSnapshot.model_validate(payload)
