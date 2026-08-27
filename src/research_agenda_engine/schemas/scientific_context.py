from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ._r5_firewall import assert_proposal_safe_payload
from .dataset_narrative import DatasetNarrative
from .question_pattern import QuestionPatternCard
from .research_intent import ResearchIntent
from .review_authority import is_accepted_authority


class TopicEvidenceClaimStatus(StrEnum):
    ESTABLISHED = "established"
    CONTESTED = "contested"
    METHODOLOGICAL_CHANGE = "methodological_change"
    KNOWN_LIMITATION = "known_limitation"
    OPEN_QUESTION = "open_question"
    ALREADY_ANSWERED = "already_answered"
    #: How these data or comparable resources have already been used, and to what end.
    #:
    #: Added 2026-08-17 because the reviewer requires typed, source-bound evidence for the
    #: `dataset_resource_reuse` dimension and there was no status that could carry it. The only
    #: place a brief could put such evidence was `nearest_dataset_reuse_work: list[str]` -- a list
    #: of plain strings, structurally incapable of holding a `claim`, a `status` and
    #: `source_record_ids`. So the drafter wrote prose there and the reviewer, correctly, refused it
    #: as untyped.
    #:
    #: Measured on the 2026-08-16 climate leg: the corpus contained FIVE reanalysis-reuse records,
    #: including *Thermally Driven and Eddy-Driven Jet Variability in Reanalysis*, and the brief's
    #: own sentence -- "the supplied sources use reanalysis-based circulation analyses, including
    #: 700-hPa geopotential-height regime classification, ERA-40 jet and Rossby-wave-breaking
    #: diagnostics" -- was TRUE and was exactly the evidence being asked for. It sat in the string
    #: list, unbound, and the leg terminated on `essential_evidence_absent` for a dimension it
    #: actually covered.
    #:
    #: Every consumer of this enum tests positive membership (`== X`, `in {X, Y}`); none switches
    #: exhaustively, and the Question Scientist projection filters on source binding rather than
    #: status, so a new member reaches the packs and breaks no existing path.
    DATASET_RESOURCE_REUSE = "dataset_resource_reuse"


class TopicEvidenceClaimOrigin(StrEnum):
    LOCAL_SUPPORTED = "local_supported"
    GPT_SYNTHESIZED = "gpt_synthesized"
    BOTH = "both"


class TopicEvidenceBriefReviewStatus(StrEnum):
    DRAFT = "draft"
    SOURCE_REVIEWED = "source_reviewed"
    # Independent-AI topic-evidence gate accepted. Automated/non-human tier, same level
    # as DatasetNarrative's AUTOMATED_REVIEWED; see schemas/review_authority.py. Never a human import.
    AI_REVIEWED = "ai_reviewed"
    EXPERT_REVIEWED = "expert_reviewed"


class TopicEvidenceClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    claim: str
    status: TopicEvidenceClaimStatus
    source_refs: list[str] = Field(default_factory=list)
    source_record_ids: list[str] = Field(default_factory=list)
    origin: TopicEvidenceClaimOrigin = TopicEvidenceClaimOrigin.LOCAL_SUPPORTED
    synthesis_rationale: str = ""
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("claim_id", "claim")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("TopicEvidenceClaim id and claim must be non-empty")
        return value


class TopicEvidenceBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brief_id: str
    topic_terms: list[str] = Field(default_factory=list)
    canonical_scope: str
    claims: list[TopicEvidenceClaim] = Field(default_factory=list)
    nearest_dataset_reuse_work: list[str] = Field(default_factory=list)
    questions_already_answered: list[str] = Field(default_factory=list)
    unresolved_tensions: list[str] = Field(default_factory=list)
    knowledge_cutoff: date
    retrieval_manifest_digest: str
    review_status: TopicEvidenceBriefReviewStatus = TopicEvidenceBriefReviewStatus.DRAFT
    prompt_version: str = ""
    provider_id: str = ""
    model_id: str = ""
    input_digest: str = ""
    source_table_digest: str = ""
    field_state_digest: str = ""
    reviewed_at: datetime | None = None
    expert_reviewer: str = ""
    review_notes: str = ""

    @field_validator("brief_id", "canonical_scope", "retrieval_manifest_digest")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("TopicEvidenceBrief core fields must be non-empty")
        return value

    @model_validator(mode="after")
    def require_sources_for_reviewed_brief(self) -> TopicEvidenceBrief:
        if self.review_status != TopicEvidenceBriefReviewStatus.DRAFT:
            if not self.claims:
                raise ValueError("source-reviewed or expert-reviewed brief requires claims")
            missing_sources = [
                claim.claim_id
                for claim in self.claims
                if not (claim.source_refs or claim.source_record_ids)
            ]
            if missing_sources:
                raise ValueError(
                    "source-reviewed or expert-reviewed claims require source_refs: "
                    + ", ".join(missing_sources)
                )
        return self

    @property
    def is_proposal_ready(self) -> bool:
        # Accepted authorities (AI_REVIEWED / EXPERT_REVIEWED) plus the legacy source-verified tier.
        return (
            is_accepted_authority(self.review_status)
            or self.review_status == TopicEvidenceBriefReviewStatus.SOURCE_REVIEWED
        )


class ProposalContextPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_id: str = "r5_proposal_context_policy/v1"
    allow_demo_relaxations: bool = False
    require_source_verified_dataset: bool = True
    require_source_reviewed_topic_brief: bool = True
    require_expert_reviewed_patterns: bool = True
    forbidden_evidence_classes: list[str] = Field(
        default_factory=lambda: [
            "CapabilityRegistry",
            "JointCoverageReport",
            "OperatorProbeReceipt",
            "ExecutorReceiptBundle",
            "QBenchCase",
            "confirmation_outcome",
            "ContractReadinessProof",
            "AnalysisContract",
            "R4 readiness evidence",
        ]
    )

    def validate_payload(self, value: Any, *, context: str = "ScientificContextSnapshot") -> None:
        assert_proposal_safe_payload(value, context=context)

    @model_validator(mode="after")
    def prevent_silent_serious_mode_relaxation(self) -> ProposalContextPolicy:
        relaxed = [
            self.require_source_verified_dataset,
            self.require_source_reviewed_topic_brief,
            self.require_expert_reviewed_patterns,
        ]
        if not self.allow_demo_relaxations and not all(relaxed):
            raise ValueError(
                "serious proposal context policy cannot relax evidence requirements without "
                "allow_demo_relaxations"
            )
        return self


class ScientificContextSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context_id: str
    research_intent: ResearchIntent
    dataset_narrative: DatasetNarrative
    topic_evidence_brief: TopicEvidenceBrief
    question_patterns: list[QuestionPatternCard] = Field(default_factory=list)
    retrieved_paper_case_ids: list[str] = Field(default_factory=list)
    retrieved_paper_case_digests: dict[str, str] = Field(default_factory=dict)
    prompt_policy_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    context_digest: str
    proposal_context_policy: ProposalContextPolicy = Field(default_factory=ProposalContextPolicy)
    frozen_after_seed_generation: bool = False

    @field_validator("context_id", "prompt_policy_version", "context_digest")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ScientificContextSnapshot ids and policy version must be non-empty")
        return value

    @model_validator(mode="after")
    def enforce_proposal_context_firewall(self) -> ScientificContextSnapshot:
        self.proposal_context_policy.validate_payload(
            self.model_dump(mode="python", exclude={"proposal_context_policy"}),
            context="ScientificContextSnapshot",
        )
        if (
            self.proposal_context_policy.require_source_verified_dataset
            and not self.dataset_narrative.is_proposal_ready
        ):
            raise ValueError("serious proposal context requires source-verified DatasetNarrative")
        if (
            self.proposal_context_policy.require_source_reviewed_topic_brief
            and not self.topic_evidence_brief.is_proposal_ready
        ):
            raise ValueError("serious proposal context requires source-reviewed TopicEvidenceBrief")
        if self.proposal_context_policy.require_expert_reviewed_patterns:
            unreviewed = [
                pattern.pattern_id
                for pattern in self.question_patterns
                if not pattern.is_proposal_ready
            ]
            if unreviewed:
                raise ValueError(
                    "serious proposal context requires expert-reviewed QuestionPatternCards: "
                    + ", ".join(unreviewed)
                )
        return self
