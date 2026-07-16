from __future__ import annotations

from pathlib import Path

from ...io import dump_data, load_model
from ...provenance import sha256_file
from ...schemas.dataset_narrative import DatasetNarrative
from ...schemas.question_scientist_context import (
    QUESTION_SCIENTIST_CONTEXT_POLICY_VERSION,
    QuestionScientistContextPayload,
    question_scientist_context_ids,
)
from ...schemas.research_intent import ResearchIntent
from ...schemas.scientific_context import TopicEvidenceBrief
from ..paper_patterns.retrieval import QuestionPatternBank
from .review_gates import assert_question_scientist_inputs_are_reviewed


def build_question_scientist_context_payload(
    *,
    corpus_root: str | Path = "corpus",
    intent_path: str | Path = "examples/research_intent.yaml",
    dataset_id: str = "ibl_bwm",
    pattern_limit: int = 8,
) -> QuestionScientistContextPayload:
    root = Path(corpus_root)
    intent_path = Path(intent_path)
    intent = load_model(intent_path, ResearchIntent)
    pattern_manifest_path = root / "question_pattern_manifest.yaml"
    pattern_bank = QuestionPatternBank.from_corpus(root, serious_mode=True)
    patterns = pattern_bank.retrieve(
        intent.topic_terms or intent.target_constructs, limit=pattern_limit
    )
    dataset_path = root / "context" / "dataset_narratives" / f"{dataset_id}.dataset_narrative.yaml"
    topic_path = root / "context" / "topic_evidence" / "research_intent.topic_evidence_brief.yaml"
    dataset_narrative = load_model(dataset_path, DatasetNarrative)
    topic_brief = load_model(topic_path, TopicEvidenceBrief)
    reviewed_patterns = [hit.pattern for hit in patterns]
    assert_question_scientist_inputs_are_reviewed(
        paperbank_question_patterns=reviewed_patterns,
        topic_literature_brief=topic_brief,
        dataset_narrative=dataset_narrative,
    )
    payload_dict = {
        "payload_id": "pending",
        "context_id": "pending",
        "research_intent": intent.model_dump(mode="json"),
        "paperbank_question_patterns": [
            pattern.model_dump(mode="json") for pattern in reviewed_patterns
        ],
        "topic_literature_brief": topic_brief.model_dump(mode="json"),
        "dataset_narrative": dataset_narrative.model_dump(mode="json"),
        "prompt_policy_version": QUESTION_SCIENTIST_CONTEXT_POLICY_VERSION,
        "source_artifact_digests": {
            "research_intent": sha256_file(intent_path),
            "question_pattern_manifest": sha256_file(pattern_manifest_path),
            "dataset_narrative": sha256_file(dataset_path),
            "topic_evidence_brief": sha256_file(topic_path),
        },
        "context_digest": "0" * 64,
    }
    payload_id, context_id, digest = question_scientist_context_ids(payload_dict)
    payload_dict.update(
        {
            "payload_id": payload_id,
            "context_id": context_id,
            "context_digest": digest,
        }
    )
    return QuestionScientistContextPayload.model_validate(payload_dict)


def write_question_scientist_context_payload(
    payload: QuestionScientistContextPayload,
    *,
    corpus_root: str | Path = "corpus",
) -> Path:
    path = (
        Path(corpus_root)
        / "context"
        / "question_scientist"
        / f"{payload.context_id}.question_scientist_context.yaml"
    )
    return dump_data(payload, path)
