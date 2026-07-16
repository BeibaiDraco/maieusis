from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..provenance import stable_hash
from ._r5_firewall import assert_proposal_safe_payload
from .front_half_authority import FrontHalfAuthorityCeiling
from .research_intent import ResearchIntent
from .scientific_context import TopicEvidenceClaimStatus

QUESTION_SCIENTIST_CONTEXT_V2_POLICY_VERSION = "question_scientist_context/v2"
MAX_DEFAULT_TOPIC_SOURCE_CARDS = 30
MAX_EXCERPT_CHARS = 800


class SourceQualityClass(StrEnum):
    PEER_REVIEWED_SYSTEMATIC_REVIEW = "peer_reviewed_systematic_review"
    PEER_REVIEWED_PRIMARY_STUDY = "peer_reviewed_primary_study"
    PEER_REVIEWED_METHODS_OR_RESOURCE = "peer_reviewed_methods_or_resource"
    PEER_REVIEWED_CONFERENCE_PAPER = "peer_reviewed_conference_paper"
    SCHOLARLY_PREPRINT = "scholarly_preprint"
    SCHOLARLY_THESIS_OR_TECHNICAL_REPORT = "scholarly_thesis_or_technical_report"
    AUTHORITATIVE_GUIDELINE_OR_REPORT = "authoritative_guideline_or_report"
    DATASET_REGISTRY_OR_PROTOCOL = "dataset_registry_or_protocol"
    EDITORIAL_COMMENTARY_OR_PERSPECTIVE = "editorial_commentary_or_perspective"
    CITATION_CONTEXT_ONLY = "citation_context_only"
    NON_SCHOLARLY_NEWS_OR_BLOG = "non_scholarly_news_or_blog"
    VENDOR_MARKETING_OR_PRESS_RELEASE = "vendor_marketing_or_press_release"
    SOCIAL_MEDIA_OR_FORUM = "social_media_or_forum"
    SUSPECTED_SPAM_OR_GENERATED_CONTENT = "suspected_spam_or_generated_content"
    UNCLASSIFIED_SOURCE = "unclassified_source"


class ContentAvailabilityClass(StrEnum):
    FULL_TEXT_OR_SUFFICIENT_EXCERPT_AVAILABLE = "full_text_or_sufficient_excerpt_available"
    ABSTRACT_ONLY = "abstract_only"
    TITLE_ONLY = "title_only"
    METADATA_ONLY = "metadata_only"
    BROKEN_LINK_OR_UNAVAILABLE = "broken_link_or_unavailable"
    DUPLICATE_RECORD = "duplicate_record"
    SUPERSEDED_RECORD = "superseded_record"
    OUT_OF_SCOPE_RECORD = "out_of_scope_record"


class EvidenceBasis(StrEnum):
    """Whether a gap/claim's supporting literature is fulltext-backed or only abstract-level.

    The operator decision: abstract-only evidence NEVER vetoes question development — it is surfaced as an
    honest, loud label and the user decides. This is the derived label; the veto is gone.
    """

    FULLTEXT_BACKED = "fulltext_backed"  # >=1 support source has full text / a sufficient excerpt
    ABSTRACT_ONLY = "abstract_only"  # every support source is abstract-only (no fulltext obtained)


def derive_evidence_basis(
    support_content_classes: Iterable[ContentAvailabilityClass],
) -> EvidenceBasis:
    """Single source of truth for ``evidence_basis`` — derived ONLY from ``ContentAvailabilityClass``.

    FAIL CLOSED (R1): support cards can only legitimately be ``FULL_TEXT_OR_SUFFICIENT_EXCERPT_AVAILABLE``
    or ``ABSTRACT_ONLY`` here — everything weaker (TITLE_ONLY / METADATA / broken / duplicate / …) is
    hard-blocked upstream and can never reach a gap/claim's support set. If an unexpected class DOES reach
    here, RAISE rather than silently laundering it into a wrong-but-labelled basis, so a future upstream
    change cannot quietly weaken the premise.
    """
    has_fulltext = False
    for content_class in support_content_classes:
        if content_class == ContentAvailabilityClass.FULL_TEXT_OR_SUFFICIENT_EXCERPT_AVAILABLE:
            has_fulltext = True
        elif content_class != ContentAvailabilityClass.ABSTRACT_ONLY:
            raise ValueError(
                "derive_evidence_basis received an unexpected support content class "
                f"{content_class!r}; support sources must be fulltext or abstract-only (weaker classes "
                "are hard-blocked upstream) — refusing to launder it into a basis label"
            )
    return EvidenceBasis.FULLTEXT_BACKED if has_fulltext else EvidenceBasis.ABSTRACT_ONLY


class SourceIntegrityClass(StrEnum):
    NORMAL = "normal"
    RETRACTED = "retracted"
    EXPRESSION_OF_CONCERN = "expression_of_concern"
    MAJOR_CORRECTION = "major_correction"
    METHODOLOGICAL_RED_FLAG = "methodological_red_flag"
    CONFLICT_OF_INTEREST_RED_FLAG = "conflict_of_interest_red_flag"
    UNVERIFIABLE_CITATION = "unverifiable_citation"


class SourceEvidenceRole(StrEnum):
    SUPPORTS_REVIEWED_CLAIM = "supports_reviewed_claim"
    SUPPORTS_ACCEPTED_GAP = "supports_accepted_gap"
    CLOSE_PRIOR_OR_COMPETING_WORK = "close_prior_or_competing_work"
    METHOD_LIMIT_OR_FEASIBILITY_CONSTRAINT = "method_limit_or_feasibility_constraint"
    COUNTEREVIDENCE_OR_NEGATIVE_RESULT = "counterevidence_or_negative_result"
    FIELD_STATE_BACKGROUND = "field_state_background"
    DEFINITION_OR_TAXONOMY = "definition_or_taxonomy"
    DO_NOT_USE_AS_EVIDENCE = "do_not_use_as_evidence"


class SourceExportStatus(StrEnum):
    EXPORT = "export"
    EXPORT_WITH_WARNING = "export_with_warning"
    BLOCKED_FROM_QUESTION_SCIENTIST = "blocked_from_question_scientist"


class SourceExportBlockReason(StrEnum):
    METADATA_ONLY_RECORD = "metadata_only_record"
    TITLE_ONLY_RECORD = "title_only_record"
    RAW_TABLE_ROW = "raw_table_row"
    FULL_ABSTRACT_DUMP = "full_abstract_dump"
    UNREVIEWED_SOURCE_CARD = "unreviewed_source_card"
    EXCERPT_TOO_LONG = "excerpt_too_long"
    UNSUPPORTED_CLAIM_LINK = "unsupported_claim_link"
    UNVERIFIABLE_CITATION = "unverifiable_citation"
    RETRACTED_POSITIVE_EVIDENCE = "retracted_positive_evidence"
    NON_SCHOLARLY_SOURCE = "non_scholarly_source"
    OUT_OF_SCOPE_SOURCE = "out_of_scope_source"
    DUPLICATE_SOURCE = "duplicate_source"
    BLOCKED_DRAFT_CONTENT = "blocked_draft_content"
    EMPTY_EXCERPT = "empty_excerpt"


class QuestionScientistEvidenceRequestType(StrEnum):
    MISSING_SUPPORT_FOR_CLAIM = "missing_support_for_claim"
    CLOSE_PRIOR_CHECK = "close_prior_check"
    COUNTEREVIDENCE_CHECK = "counterevidence_check"
    METHOD_FEASIBILITY_CHECK = "method_feasibility_check"
    DATASET_OR_BENCHMARK_CHECK = "dataset_or_benchmark_check"
    RECENCY_CHECK = "recency_check"
    DEFINITION_OR_TAXONOMY_CHECK = "definition_or_taxonomy_check"
    FIELD_STATE_UPDATE = "field_state_update"
    SOURCE_DETAIL_CLARIFICATION = "source_detail_clarification"
    GAP_BOUNDARY_CLARIFICATION = "gap_boundary_clarification"


class QuestionScientistEvidenceResolutionStatus(StrEnum):
    RESOLVED_WITH_NEW_CARDS = "resolved_with_new_cards"
    RESOLVED_FROM_EXISTING_PACK = "resolved_from_existing_pack"
    RESOLVED_AS_UNSUPPORTED = "resolved_as_unsupported"
    RESOLVED_AS_CLOSE_PRIOR_FOUND = "resolved_as_close_prior_found"
    UNRESOLVED_NO_SOURCES_FOUND = "unresolved_no_sources_found"
    UNRESOLVED_NEEDS_HUMAN_REVIEW = "unresolved_needs_human_review"
    REJECTED_POLICY_VIOLATION = "rejected_policy_violation"
    REJECTED_BUDGET_EXCEEDED = "rejected_budget_exceeded"


class ClaimLevel(StrEnum):
    DESCRIPTIVE = "descriptive"
    ASSOCIATIONAL = "associational"
    PREDICTIVE = "predictive"


class OpenGapKind(StrEnum):
    REPRESENTATIONAL_GEOMETRY = "representational_geometry"
    NOISE_OR_SHARED_VARIABILITY = "noise_or_shared_variability"
    LATENT_DYNAMICS = "latent_dynamics"
    MULTI_AREA_CODING = "multi_area_coding"
    TEMPORAL_OR_LATENCY_GEOMETRY = "temporal_or_latency_geometry"
    MOVEMENT_OR_STATE_CONFOUND = "movement_or_state_confound"
    CIRCUIT_INTERPRETATION_LIMIT = "circuit_interpretation_limit"
    CROSS_SESSION_OR_GENERALIZATION = "cross_session_or_generalization"
    OTHER = "other"


class EvidenceExcerpt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    excerpt_id: str
    source_record_id: str
    text: str
    char_count: int = Field(ge=1, le=MAX_EXCERPT_CHARS)

    @field_validator("excerpt_id", "source_record_id", "text")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("EvidenceExcerpt fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_char_count(self) -> EvidenceExcerpt:
        if self.char_count != len(self.text):
            raise ValueError("EvidenceExcerpt char_count must match text length")
        return self


class ProposerSourceEvidenceCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    title: str
    citation: str
    year: int | None = None
    venue: str = ""
    doi: str = ""
    url: str = ""
    source_quality_class: SourceQualityClass
    content_availability_class: ContentAvailabilityClass
    integrity_class: SourceIntegrityClass = SourceIntegrityClass.NORMAL
    evidence_roles: list[SourceEvidenceRole] = Field(default_factory=list)
    review_status: Literal["expert_reviewed", "ai_reviewed", "provisional"] = "expert_reviewed"
    export_status: SourceExportStatus
    export_block_reasons: list[SourceExportBlockReason] = Field(default_factory=list)
    excerpts: list[EvidenceExcerpt] = Field(default_factory=list)
    support_claim_ids: list[str] = Field(default_factory=list)
    support_gap_ids: list[str] = Field(default_factory=list)
    support_close_prior_ids: list[str] = Field(default_factory=list)
    support_method_limit_ids: list[str] = Field(default_factory=list)
    quality_flags: list[str] = Field(default_factory=list)

    @field_validator("source_record_id", "title", "citation")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ProposerSourceEvidenceCard text fields must be non-empty")
        return value

    @model_validator(mode="after")
    def enforce_export_contract(self) -> ProposerSourceEvidenceCard:
        hard_block_content = {
            ContentAvailabilityClass.TITLE_ONLY: SourceExportBlockReason.TITLE_ONLY_RECORD,
            ContentAvailabilityClass.METADATA_ONLY: SourceExportBlockReason.METADATA_ONLY_RECORD,
            ContentAvailabilityClass.BROKEN_LINK_OR_UNAVAILABLE: SourceExportBlockReason.EMPTY_EXCERPT,
            ContentAvailabilityClass.DUPLICATE_RECORD: SourceExportBlockReason.DUPLICATE_SOURCE,
            ContentAvailabilityClass.OUT_OF_SCOPE_RECORD: SourceExportBlockReason.OUT_OF_SCOPE_SOURCE,
        }
        expected_block = hard_block_content.get(self.content_availability_class)
        if (
            expected_block
            and self.export_status != SourceExportStatus.BLOCKED_FROM_QUESTION_SCIENTIST
        ):
            raise ValueError(
                "support-ineligible source cards must be blocked from Question Scientist export"
            )
        if expected_block and expected_block not in self.export_block_reasons:
            raise ValueError("blocked source card must record its export block reason")
        if self.integrity_class == SourceIntegrityClass.UNVERIFIABLE_CITATION:
            if self.export_status != SourceExportStatus.BLOCKED_FROM_QUESTION_SCIENTIST:
                raise ValueError("unverifiable citations must be blocked from export")
            if SourceExportBlockReason.UNVERIFIABLE_CITATION not in self.export_block_reasons:
                raise ValueError("unverifiable citation block reason is required")
        if self.integrity_class == SourceIntegrityClass.RETRACTED:
            if self.export_status != SourceExportStatus.BLOCKED_FROM_QUESTION_SCIENTIST:
                raise ValueError("retracted sources must be blocked from export")
            if SourceExportBlockReason.RETRACTED_POSITIVE_EVIDENCE not in self.export_block_reasons:
                raise ValueError("retracted source block reason is required")
        if self.export_status == SourceExportStatus.BLOCKED_FROM_QUESTION_SCIENTIST:
            if not self.export_block_reasons:
                raise ValueError("blocked source cards require export_block_reasons")
            return self
        if self.export_block_reasons:
            raise ValueError("exportable source cards cannot carry hard block reasons")
        if not self.excerpts:
            raise ValueError("exportable source cards require selected excerpts")
        if not self.evidence_roles:
            raise ValueError("exportable source cards require evidence_roles")
        if (
            not (
                self.support_claim_ids
                or self.support_gap_ids
                or self.support_close_prior_ids
                or self.support_method_limit_ids
            )
            and self.review_status != "provisional"
        ):
            raise ValueError("exportable source cards require claim/gap/prior/method linkage")
        return self


class ReviewedTopicClaimCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    statement: str
    status: TopicEvidenceClaimStatus
    source_record_ids: list[str] = Field(default_factory=list)
    source_excerpt_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    # Honest, loud basis label (never a veto): derived from the support cards' content availability at the
    # pack level and cross-checked there (stored==derived or the pack fails closed).
    evidence_basis: EvidenceBasis

    @field_validator("claim_id", "statement")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ReviewedTopicClaimCard fields must be non-empty")
        return value

    @model_validator(mode="after")
    def require_evidence(self) -> ReviewedTopicClaimCard:
        if not self.source_record_ids:
            raise ValueError("reviewed topic claim cards require source_record_ids")
        if not self.source_excerpt_ids:
            raise ValueError("reviewed topic claim cards require source_excerpt_ids")
        return self


class ClosePriorCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    close_prior_id: str
    statement: str
    implication: str
    source_record_ids: list[str] = Field(default_factory=list)
    source_excerpt_ids: list[str] = Field(default_factory=list)
    review_status: Literal["expert_reviewed", "ai_reviewed", "provisional"] = "expert_reviewed"

    @field_validator("close_prior_id", "statement", "implication")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ClosePriorCard fields must be non-empty")
        return value

    @model_validator(mode="after")
    def require_evidence(self) -> ClosePriorCard:
        if not self.source_record_ids or not self.source_excerpt_ids:
            raise ValueError("ClosePriorCard requires source evidence")
        return self


class MethodLimitCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method_limit_id: str
    statement: str
    consequence_for_question_generation: str
    source_record_ids: list[str] = Field(default_factory=list)
    source_excerpt_ids: list[str] = Field(default_factory=list)
    review_status: Literal["expert_reviewed", "ai_reviewed", "provisional"] = "expert_reviewed"

    @field_validator("method_limit_id", "statement", "consequence_for_question_generation")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("MethodLimitCard fields must be non-empty")
        return value

    @model_validator(mode="after")
    def require_evidence(self) -> MethodLimitCard:
        if not self.source_record_ids or not self.source_excerpt_ids:
            raise ValueError("MethodLimitCard requires source evidence")
        return self


class OpenGapCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gap_id: str
    statement: str
    gap_kind: OpenGapKind = OpenGapKind.OTHER
    why_live: str
    proposal_relevance: str
    support_claim_ids: list[str] = Field(default_factory=list)
    support_source_record_ids: list[str] = Field(default_factory=list)
    support_excerpt_ids: list[str] = Field(default_factory=list)
    close_prior_ids: list[str] = Field(default_factory=list)
    allowed_claim_levels: list[ClaimLevel] = Field(default_factory=list)
    forbidden_overclaims: list[str] = Field(default_factory=list)
    review_status: Literal["expert_reviewed", "ai_reviewed", "provisional"] = "expert_reviewed"
    # Honest, loud basis label (never a veto): derived from the support cards' content availability at the
    # pack level and cross-checked there (stored==derived or the pack fails closed).
    evidence_basis: EvidenceBasis

    @field_validator("gap_id", "statement", "why_live", "proposal_relevance")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("OpenGapCard fields must be non-empty")
        return value

    @model_validator(mode="after")
    def require_evidence_and_close_prior(self) -> OpenGapCard:
        if not self.support_source_record_ids or not self.support_excerpt_ids:
            raise ValueError("OpenGapCard requires source-backed support")
        if not self.close_prior_ids:
            raise ValueError("OpenGapCard requires close-prior status")
        if not self.allowed_claim_levels:
            raise ValueError("OpenGapCard requires allowed_claim_levels")
        return self


class ReviewedSynthesisSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str
    heading: str
    synthesis: str
    claim_ids: list[str] = Field(default_factory=list)
    source_record_ids: list[str] = Field(default_factory=list)

    @field_validator("section_id", "heading", "synthesis")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ReviewedSynthesisSection fields must be non-empty")
        return value


class LaneCoverageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lane_id: str
    source_count: int = Field(ge=0)
    claim_supporting_source_count: int = Field(ge=0)


class EvidenceQualitySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_count: int = Field(ge=0)
    exported_source_count: int = Field(ge=0)
    export_with_warning_count: int = Field(ge=0)
    blocked_source_count: int = Field(ge=0)
    notes: list[str] = Field(default_factory=list)


class SourceExclusionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata_only_count: int = Field(ge=0)
    title_only_count: int = Field(ge=0)
    diagnostic_or_offtopic_count: int = Field(ge=0)
    blocked_source_count: int = Field(ge=0)


class TopicLiteratureContextPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_pack_id: str
    source_table_digest: str
    review_id: str
    review_status: Literal["expert_reviewed", "ai_reviewed", "provisional"] = "expert_reviewed"
    brief_id: str
    brief_prompt_version: str
    field_state_prompt_version: str = ""
    lane_coverage: list[LaneCoverageSummary] = Field(default_factory=list)
    field_state_capsule: list[ReviewedSynthesisSection] = Field(default_factory=list)
    claim_cards: list[ReviewedTopicClaimCard] = Field(default_factory=list)
    open_gap_cards: list[OpenGapCard] = Field(default_factory=list)
    close_prior_cards: list[ClosePriorCard] = Field(default_factory=list)
    method_limit_cards: list[MethodLimitCard] = Field(default_factory=list)
    source_cards: list[ProposerSourceEvidenceCard] = Field(default_factory=list)
    evidence_quality_summary: EvidenceQualitySummary
    excluded_or_support_ineligible_summary: SourceExclusionSummary

    @field_validator("source_table_digest")
    @classmethod
    def require_source_table_sha256(cls, value: str) -> str:
        return _require_sha256(value, label="source_table_digest")

    @model_validator(mode="after")
    def enforce_topic_pack_export_contract(self) -> TopicLiteratureContextPack:
        provisional = self.review_status == "provisional"
        if not provisional and not self.claim_cards:
            raise ValueError("TopicLiteratureContextPack requires reviewed claim cards")
        if not provisional and not self.open_gap_cards:
            raise ValueError("TopicLiteratureContextPack requires accepted open-gap cards")
        if not provisional and not self.close_prior_cards:
            raise ValueError("TopicLiteratureContextPack requires close-prior cards")
        if provisional and not self.source_cards:
            unsupported_without_sources = any(
                (
                    self.field_state_capsule,
                    self.claim_cards,
                    self.open_gap_cards,
                    self.close_prior_cards,
                    self.method_limit_cards,
                )
            )
            if unsupported_without_sources:
                raise ValueError(
                    "provisional topic content requires source-bound cards; an empty source table "
                    "cannot carry claims, gaps, priors, limits, or field-state synthesis"
                )
            if self.evidence_quality_summary.exported_source_count:
                raise ValueError(
                    "provisional topic pack cannot report exported sources without source cards"
                )
        if len(self.source_cards) > MAX_DEFAULT_TOPIC_SOURCE_CARDS:
            raise ValueError("default TopicLiteratureContextPack exceeds source card budget")
        _require_unique([card.source_record_id for card in self.source_cards], "source_record_id")
        _require_unique([card.claim_id for card in self.claim_cards], "claim_id")
        _require_unique([card.gap_id for card in self.open_gap_cards], "gap_id")
        _require_unique([card.close_prior_id for card in self.close_prior_cards], "close_prior_id")
        _require_unique(
            [card.method_limit_id for card in self.method_limit_cards], "method_limit_id"
        )
        all_excerpts = [excerpt for card in self.source_cards for excerpt in card.excerpts]
        _require_unique([excerpt.excerpt_id for excerpt in all_excerpts], "excerpt_id")
        card_by_id = {card.source_record_id: card for card in self.source_cards}
        excerpt_owner = {excerpt.excerpt_id: excerpt.source_record_id for excerpt in all_excerpts}
        excerpt_ids = set(excerpt_owner)
        for card in self.source_cards:
            if card.export_status == SourceExportStatus.BLOCKED_FROM_QUESTION_SCIENTIST:
                raise ValueError("blocked source cards cannot enter TopicLiteratureContextPack")
            if card.integrity_class == SourceIntegrityClass.RETRACTED:
                raise ValueError("retracted sources cannot enter proposer evidence cards")
            if provisional != (card.review_status == "provisional"):
                raise ValueError("topic pack and source-card provisional authority must agree")
            for excerpt in card.excerpts:
                if excerpt.source_record_id != card.source_record_id:
                    raise ValueError(
                        f"excerpt {excerpt.excerpt_id} owner does not match containing source card"
                    )
        nested_review_statuses = {card.review_status for card in self.open_gap_cards}
        nested_review_statuses.update(card.review_status for card in self.close_prior_cards)
        nested_review_statuses.update(card.review_status for card in self.method_limit_cards)
        if any(status != self.review_status for status in nested_review_statuses):
            raise ValueError("topic pack and nested evidence-card review authority must agree")
        if not provisional:
            has_ai_card = any(card.review_status == "ai_reviewed" for card in self.source_cards)
            if self.review_status == "expert_reviewed" and has_ai_card:
                raise ValueError(
                    "expert-reviewed topic pack cannot elevate AI-reviewed source cards"
                )
        for claim in self.claim_cards:
            _require_known_sources(
                claim.source_record_ids,
                card_by_id,
                f"claim {claim.claim_id}",
            )
            _require_known_excerpts(
                claim.source_excerpt_ids,
                excerpt_ids,
                f"claim {claim.claim_id}",
            )
            _require_excerpt_ownership(
                claim.source_record_ids,
                claim.source_excerpt_ids,
                excerpt_owner,
                f"claim {claim.claim_id}",
            )
            # Veto → label: an abstract-only strong claim no longer raises; it flows with an honest
            # ``evidence_basis`` label. What STILL fails closed is a MISLABEL — the stored basis must equal
            # the value derived from the support cards, so abstract-only evidence can never be laundered
            # as fulltext-backed.
            claim_cards = [card_by_id[source_id] for source_id in claim.source_record_ids]
            derived_claim_basis = derive_evidence_basis(
                card.content_availability_class for card in claim_cards
            )
            if claim.evidence_basis != derived_claim_basis:
                raise ValueError(
                    f"claim {claim.claim_id} evidence_basis {claim.evidence_basis.value!r} does not "
                    f"match its support cards ({derived_claim_basis.value!r}); abstract-only evidence "
                    "must be labelled honestly, never mislabelled"
                )
        for prior in self.close_prior_cards:
            _require_known_sources(
                prior.source_record_ids,
                card_by_id,
                f"close prior {prior.close_prior_id}",
            )
            _require_known_excerpts(
                prior.source_excerpt_ids,
                excerpt_ids,
                f"close prior {prior.close_prior_id}",
            )
            _require_excerpt_ownership(
                prior.source_record_ids,
                prior.source_excerpt_ids,
                excerpt_owner,
                f"close prior {prior.close_prior_id}",
            )
        for method_limit in self.method_limit_cards:
            _require_known_sources(
                method_limit.source_record_ids,
                card_by_id,
                f"method limit {method_limit.method_limit_id}",
            )
            _require_known_excerpts(
                method_limit.source_excerpt_ids,
                excerpt_ids,
                f"method limit {method_limit.method_limit_id}",
            )
            _require_excerpt_ownership(
                method_limit.source_record_ids,
                method_limit.source_excerpt_ids,
                excerpt_owner,
                f"method limit {method_limit.method_limit_id}",
            )
        close_prior_ids = {card.close_prior_id for card in self.close_prior_cards}
        claim_ids = {card.claim_id for card in self.claim_cards}
        for gap in self.open_gap_cards:
            _require_known_sources(
                gap.support_source_record_ids,
                card_by_id,
                f"gap {gap.gap_id}",
            )
            _require_known_excerpts(
                gap.support_excerpt_ids,
                excerpt_ids,
                f"gap {gap.gap_id}",
            )
            _require_excerpt_ownership(
                gap.support_source_record_ids,
                gap.support_excerpt_ids,
                excerpt_owner,
                f"gap {gap.gap_id}",
            )
            missing_priors = set(gap.close_prior_ids) - close_prior_ids
            if missing_priors:
                raise ValueError(
                    f"gap {gap.gap_id} cites unknown close priors: "
                    + ", ".join(sorted(missing_priors))
                )
            missing_claims = set(gap.support_claim_ids) - claim_ids
            if missing_claims:
                raise ValueError(
                    f"gap {gap.gap_id} cites unknown claims: " + ", ".join(sorted(missing_claims))
                )
            # Veto → label (same as strong claims): an abstract-only open gap flows with an honest
            # ``evidence_basis`` label; only a MISLABEL fails closed.
            gap_cards = [card_by_id[source_id] for source_id in gap.support_source_record_ids]
            derived_gap_basis = derive_evidence_basis(
                card.content_availability_class for card in gap_cards
            )
            if gap.evidence_basis != derived_gap_basis:
                raise ValueError(
                    f"open gap {gap.gap_id} evidence_basis {gap.evidence_basis.value!r} does not "
                    f"match its support cards ({derived_gap_basis.value!r}); abstract-only evidence "
                    "must be labelled honestly, never mislabelled"
                )
        _require_reciprocal_support_links(self)
        return self


class DatasetStorySection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str
    heading: str
    text: str
    source_ids: list[str] = Field(default_factory=list)

    @field_validator("section_id", "heading", "text")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DatasetStorySection fields must be non-empty")
        return value


class ProposalSafeScaleFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scale_fact_id: str
    quantity_kind: str
    value_text: str
    source_ids: list[str] = Field(default_factory=list)
    proposal_use: Literal["broad_context_not_feasibility"] = "broad_context_not_feasibility"

    @model_validator(mode="after")
    def require_source_support(self) -> ProposalSafeScaleFact:
        if not self.source_ids:
            raise ValueError("ProposalSafeScaleFact requires source_ids")
        return self


class DatasetOpportunityCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_id: str
    statement: str
    source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_source_support(self) -> DatasetOpportunityCard:
        if not self.source_ids:
            raise ValueError("DatasetOpportunityCard requires source_ids")
        return self


class DatasetLimitationCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limitation_id: str
    statement: str
    source_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_source_support(self) -> DatasetLimitationCard:
        if not self.source_ids:
            raise ValueError("DatasetLimitationCard requires source_ids")
        return self


class DatasetContextPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    narrative_id: str
    review_id: str
    review_status: Literal["expert_reviewed", "ai_reviewed"] = "expert_reviewed"
    dataset_role: Literal["public_data_opportunity_surface"] = "public_data_opportunity_surface"
    story_sections: list[DatasetStorySection] = Field(default_factory=list)
    proposal_safe_scale_facts: list[ProposalSafeScaleFact] = Field(default_factory=list)
    broad_variable_taxonomy: list[str] = Field(default_factory=list)
    task_event_vocabulary: list[str] = Field(default_factory=list)
    opportunity_cards: list[DatasetOpportunityCard] = Field(default_factory=list)
    limitation_cards: list[DatasetLimitationCard] = Field(default_factory=list)
    forbidden_inference_notice: str

    @model_validator(mode="after")
    def require_dataset_context(self) -> DatasetContextPack:
        if not self.story_sections:
            raise ValueError("DatasetContextPack requires story_sections")
        if not self.proposal_safe_scale_facts:
            raise ValueError("DatasetContextPack requires proposal-safe scale facts")
        if not self.opportunity_cards:
            raise ValueError("DatasetContextPack requires opportunity cards")
        if not self.limitation_cards:
            raise ValueError("DatasetContextPack requires limitation cards")
        assert_proposal_safe_payload(self.model_dump(mode="python"), context="DatasetContextPack")
        return self


class FormationTraceSummaryForProposer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str
    source_paper_case_id: str
    question_forming_move: str
    literature_evidence_role: str
    dataset_or_observation_role: str
    what_to_imitate: str
    what_not_to_copy: str


class QuestionPatternForProposer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern_id: str
    title: str
    abstract_pattern: str
    scientific_move: str
    epistemic_move: str
    typical_contrast_structure: list[str] = Field(default_factory=list)
    useful_when: list[str] = Field(default_factory=list)
    avoid_when: list[str] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)
    evidence_role_template: list[str] = Field(default_factory=list)
    dataset_role_template: list[str] = Field(default_factory=list)
    formation_trace_summaries: list[FormationTraceSummaryForProposer] = Field(default_factory=list)
    review_status: Literal["expert_reviewed", "ai_reviewed"] = "expert_reviewed"
    proposal_ready: Literal[True] = True


class PatternContextPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern_pack_id: str
    review_status: Literal["expert_reviewed", "ai_reviewed"] = "expert_reviewed"
    pattern_cards: list[QuestionPatternForProposer] = Field(default_factory=list)
    diversity_guidance: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_patterns(self) -> PatternContextPack:
        if not self.pattern_cards:
            raise ValueError("PatternContextPack requires reviewed pattern cards")
        _require_unique([card.pattern_id for card in self.pattern_cards], "pattern_id")
        if self.review_status == "expert_reviewed" and any(
            card.review_status == "ai_reviewed" for card in self.pattern_cards
        ):
            raise ValueError(
                "expert-reviewed pattern pack cannot elevate AI-reviewed pattern cards"
            )
        return self


class ProposalStageGuidance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_claim_levels: list[ClaimLevel] = Field(default_factory=list)
    forbidden_outputs: list[str] = Field(default_factory=list)
    uncertainty_policy: str


class EvidenceRequestProtocol(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_request_rounds: int = Field(default=2, ge=0)
    max_requests_per_round: int = Field(default=8, ge=0)
    max_new_cards_per_request: int = Field(default=5, ge=0)
    max_new_cards_total: int = Field(default=25, ge=0)
    allowed_request_types: list[QuestionScientistEvidenceRequestType] = Field(
        default_factory=lambda: list(QuestionScientistEvidenceRequestType)
    )


class ContextProvenanceSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern_pack_digest: str
    topic_pack_digest: str
    dataset_pack_digest: str
    notes: list[str] = Field(default_factory=list)

    @field_validator("pattern_pack_digest", "topic_pack_digest", "dataset_pack_digest")
    @classmethod
    def require_pack_sha256(cls, value: str) -> str:
        return _require_sha256(value, label="pack digest")


class QuestionScientistEvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    request_type: QuestionScientistEvidenceRequestType
    target_claim_or_gap_id: str = ""
    why_needed: str
    suggested_search_terms: list[str] = Field(default_factory=list)
    desired_evidence_roles: list[SourceEvidenceRole] = Field(default_factory=list)
    max_cards_requested: int = Field(default=5, ge=1, le=5)


class QuestionScientistEvidenceResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    resolution_status: QuestionScientistEvidenceResolutionStatus
    new_source_evidence_card_ids: list[str] = Field(default_factory=list)
    updated_claim_card_ids: list[str] = Field(default_factory=list)
    updated_gap_card_ids: list[str] = Field(default_factory=list)
    unresolved_reason: str = ""
    notes_for_question_scientist: str = ""


class QuestionScientistContextPayloadV2(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contract_version: Literal["question_scientist_context/v2"] = "question_scientist_context/v2"
    payload_id: str
    context_id: str
    context_digest: str
    context_review_status: Literal[
        "expert_reviewed_exportable",
        "ai_reviewed_exportable",
        "provisional_inspiration",
    ] = "expert_reviewed_exportable"
    research_intent: ResearchIntent
    scientific_intent_invariant_digest: str
    paperbank_patterns: PatternContextPack
    topic_literature: TopicLiteratureContextPack
    dataset_context: DatasetContextPack
    proposer_guidance: ProposalStageGuidance
    evidence_request_protocol: EvidenceRequestProtocol
    provenance_summary: ContextProvenanceSummary
    source_artifact_digests: dict[str, str] = Field(default_factory=dict)

    @field_validator(
        "payload_id",
        "context_id",
        "context_digest",
        "scientific_intent_invariant_digest",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionScientistContextPayloadV2 identifiers must be non-empty")
        return value

    @field_validator("context_digest", "scientific_intent_invariant_digest")
    @classmethod
    def require_sha256(cls, value: str) -> str:
        return _require_sha256(value, label="digest field")

    @field_validator("source_artifact_digests")
    @classmethod
    def require_source_artifact_sha256(cls, value: dict[str, str]) -> dict[str, str]:
        if not value:
            raise ValueError("source_artifact_digests must record the source artifact SHA values")
        if any(not key.strip() for key in value):
            raise ValueError("source_artifact_digests keys must be non-empty")
        required = {
            "research_intent",
            "question_pattern_manifest",
            "dataset_narrative",
            "topic_evidence_brief",
            "topic_source_table",
        }
        missing = sorted(required - set(value))
        if missing:
            raise ValueError(
                "source_artifact_digests missing canonical artifacts: " + ", ".join(missing)
            )
        return {
            key: _require_sha256(digest, label=f"source artifact {key}")
            for key, digest in value.items()
        }

    @model_validator(mode="after")
    def enforce_payload_contract(self) -> QuestionScientistContextPayloadV2:
        context_is_provisional = self.context_review_status == "provisional_inspiration"
        topic_is_provisional = self.topic_literature.review_status == "provisional"
        if context_is_provisional != topic_is_provisional:
            raise ValueError(
                "context and topic-literature authority modes must agree on provisional status"
            )
        expected_intent_digest = stable_hash(self.research_intent.model_dump(mode="json"))
        if self.scientific_intent_invariant_digest != expected_intent_digest:
            raise ValueError("scientific_intent_invariant_digest does not match research_intent")
        expected_pack_digests = {
            "pattern_pack_digest": stable_hash(self.paperbank_patterns),
            "topic_pack_digest": stable_hash(self.topic_literature),
            "dataset_pack_digest": stable_hash(self.dataset_context),
        }
        for field_name, expected_digest in expected_pack_digests.items():
            if getattr(self.provenance_summary, field_name) != expected_digest:
                raise ValueError(f"provenance_summary {field_name} does not match its pack")
        child_has_ai_authority = (
            self.paperbank_patterns.review_status == "ai_reviewed"
            or self.topic_literature.review_status == "ai_reviewed"
            or self.dataset_context.review_status == "ai_reviewed"
        )
        if self.context_review_status == "expert_reviewed_exportable" and child_has_ai_authority:
            raise ValueError("expert-reviewed context cannot elevate AI-reviewed context packs")
        if self.context_review_status == "ai_reviewed_exportable" and not child_has_ai_authority:
            raise ValueError("AI-reviewed context status requires an AI-reviewed context pack")
        assert_proposal_safe_payload(
            self.model_dump(mode="python"),
            context="QuestionScientistContextPayloadV2",
        )
        expected = question_scientist_context_v2_digest(self)
        if self.context_digest != expected:
            raise ValueError("context_digest does not match V2 payload contents")
        return self

    @property
    def authority_ceiling(self) -> FrontHalfAuthorityCeiling:
        if self.context_review_status == "provisional_inspiration":
            return FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
        return FrontHalfAuthorityCeiling.VERIFIED


def question_scientist_context_v2_digest(
    value: QuestionScientistContextPayloadV2 | dict[str, Any],
) -> str:
    if isinstance(value, QuestionScientistContextPayloadV2):
        payload = value.model_dump(mode="json")
    else:
        payload = dict(value)
    payload.pop("payload_id", None)
    payload.pop("context_id", None)
    payload.pop("context_digest", None)
    return stable_hash(payload)


def question_scientist_context_v2_ids(value: dict[str, Any]) -> tuple[str, str, str]:
    digest = question_scientist_context_v2_digest(value)
    context_id = f"qsc-v2-context-{digest[:12]}"
    payload_id = f"qsc-v2-payload-{digest[:12]}"
    return payload_id, context_id, digest


def _require_known_sources(
    source_ids: list[str],
    card_by_id: dict[str, ProposerSourceEvidenceCard],
    label: str,
) -> None:
    unknown = sorted(set(source_ids) - set(card_by_id))
    if unknown:
        raise ValueError(f"{label} cites unknown source cards: " + ", ".join(unknown))


def _require_known_excerpts(
    excerpt_ids: list[str],
    known_excerpt_ids: set[str],
    label: str,
) -> None:
    unknown = sorted(set(excerpt_ids) - known_excerpt_ids)
    if unknown:
        raise ValueError(f"{label} cites unknown excerpts: " + ", ".join(unknown))


def _require_sha256(value: str, *, label: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise ValueError(f"{label} must be a lowercase 64-character sha256 hex")
    return normalized


def _require_unique(values: list[str], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"duplicate {label} values: " + ", ".join(duplicates))


def _require_excerpt_ownership(
    source_ids: list[str],
    excerpt_ids: list[str],
    excerpt_owner: dict[str, str],
    label: str,
) -> None:
    foreign = sorted(
        excerpt_id
        for excerpt_id in excerpt_ids
        if excerpt_owner.get(excerpt_id) not in set(source_ids)
    )
    if foreign:
        raise ValueError(f"{label} cites excerpts owned by other sources: " + ", ".join(foreign))


def _require_reciprocal_support_links(pack: TopicLiteratureContextPack) -> None:
    relations = (
        (
            "claim",
            {card.claim_id: card.source_record_ids for card in pack.claim_cards},
            "support_claim_ids",
        ),
        (
            "gap",
            {card.gap_id: card.support_source_record_ids for card in pack.open_gap_cards},
            "support_gap_ids",
        ),
        (
            "close prior",
            {card.close_prior_id: card.source_record_ids for card in pack.close_prior_cards},
            "support_close_prior_ids",
        ),
        (
            "method limit",
            {card.method_limit_id: card.source_record_ids for card in pack.method_limit_cards},
            "support_method_limit_ids",
        ),
    )
    for label, sources_by_target, source_link_field in relations:
        for source_card in pack.source_cards:
            linked_targets = getattr(source_card, source_link_field)
            unknown = sorted(set(linked_targets) - set(sources_by_target))
            if unknown:
                raise ValueError(
                    f"source {source_card.source_record_id} links unknown {label} ids: "
                    + ", ".join(unknown)
                )
            missing_reverse = sorted(
                target_id
                for target_id in linked_targets
                if source_card.source_record_id not in sources_by_target[target_id]
            )
            if missing_reverse:
                raise ValueError(
                    f"source {source_card.source_record_id} has non-reciprocal {label} links: "
                    + ", ".join(missing_reverse)
                )
        for target_id, source_ids in sources_by_target.items():
            for source_id in source_ids:
                source_card = next(
                    card for card in pack.source_cards if card.source_record_id == source_id
                )
                if target_id not in getattr(source_card, source_link_field):
                    raise ValueError(
                        f"{label} {target_id} lacks reciprocal source-card linkage for {source_id}"
                    )
