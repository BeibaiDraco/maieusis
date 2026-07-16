from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..provenance import stable_hash
from ._r5_firewall import assert_proposal_safe_payload
from .dataset_narrative import DatasetNarrative, DatasetNarrativeReviewStatus
from .question_pattern import QuestionPatternCard, QuestionPatternReviewStatus
from .research_intent import ResearchIntent
from .scientific_context import TopicEvidenceBrief, TopicEvidenceBriefReviewStatus

QUESTION_SCIENTIST_CONTEXT_POLICY_VERSION = "question_scientist/v1"


class QuestionScientistContextPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payload_id: str
    context_id: str
    research_intent: ResearchIntent
    paperbank_question_patterns: list[QuestionPatternCard] = Field(default_factory=list)
    topic_literature_brief: TopicEvidenceBrief
    dataset_narrative: DatasetNarrative
    prompt_policy_version: str = QUESTION_SCIENTIST_CONTEXT_POLICY_VERSION
    source_artifact_digests: dict[str, str] = Field(default_factory=dict)
    context_digest: str

    @field_validator("payload_id", "context_id", "prompt_policy_version", "context_digest")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionScientistContextPayload identifiers must be non-empty")
        return value

    @field_validator("context_digest")
    @classmethod
    def require_sha256(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("context_digest must be lowercase 64-character sha256 hex")
        return value

    @model_validator(mode="after")
    def enforce_payload_gate(self) -> QuestionScientistContextPayload:
        if not self.paperbank_question_patterns:
            raise ValueError("Question Scientist payload requires reviewed PaperBank patterns")
        unreviewed = [
            pattern.pattern_id
            for pattern in self.paperbank_question_patterns
            if pattern.review_status != QuestionPatternReviewStatus.EXPERT_REVIEWED
            or not pattern.is_proposal_ready
        ]
        if unreviewed:
            raise ValueError(
                "Question Scientist payload requires expert-reviewed proposal-ready patterns: "
                + ", ".join(unreviewed)
            )
        if (
            self.topic_literature_brief.review_status
            != TopicEvidenceBriefReviewStatus.EXPERT_REVIEWED
        ):
            raise ValueError(
                "Question Scientist payload requires expert-reviewed TopicEvidenceBrief"
            )
        if not (
            self.topic_literature_brief.prompt_version
            and self.topic_literature_brief.provider_id
            and self.topic_literature_brief.input_digest
            and self.topic_literature_brief.source_table_digest
        ):
            raise ValueError(
                "Question Scientist payload requires provenance-bearing TopicEvidenceBrief"
            )
        if self.dataset_narrative.review_status != DatasetNarrativeReviewStatus.EXPERT_REVIEWED:
            raise ValueError("Question Scientist payload requires expert-reviewed DatasetNarrative")
        if not (
            self.dataset_narrative.prompt_version
            and self.dataset_narrative.provider_id
            and self.dataset_narrative.input_digest
            and self.dataset_narrative.source_packet_digest
        ):
            raise ValueError(
                "Question Scientist payload requires provenance-bearing DatasetNarrative"
            )
        assert_proposal_safe_payload(
            self.model_dump(mode="python"),
            context="QuestionScientistContextPayload",
        )
        expected = question_scientist_context_digest(self)
        if self.context_digest != expected:
            raise ValueError("context_digest does not match payload contents")
        return self


def question_scientist_context_digest(
    value: QuestionScientistContextPayload | dict[str, Any],
) -> str:
    if isinstance(value, QuestionScientistContextPayload):
        payload = value.model_dump(mode="json")
    else:
        payload = dict(value)
    payload.pop("payload_id", None)
    payload.pop("context_id", None)
    payload.pop("context_digest", None)
    return stable_hash(payload)


def question_scientist_context_ids(value: dict[str, Any]) -> tuple[str, str, str]:
    digest = question_scientist_context_digest(value)
    context_id = f"qsc-context-{digest[:12]}"
    payload_id = f"qsc-payload-{digest[:12]}"
    return payload_id, context_id, digest
