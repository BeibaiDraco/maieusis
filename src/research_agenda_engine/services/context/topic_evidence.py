from __future__ import annotations

import json
import re
from collections.abc import Sequence
from datetime import UTC, date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.json_schema import SkipJsonSchema

from ...assets import resolve_asset
from ...io import dump_data
from ...provenance import stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas.external_evidence import (
    ExternalEvidenceRightsAssertion,
    assert_secret_free_persisted_value,
)
from ...schemas.fulltext_excerpt import FulltextExcerpt
from ...schemas.inferred_research_scope import ResolvedResearchScope
from ...schemas.research_intent import ResearchIntent
from ...schemas.scientific_context import (
    TopicEvidenceBrief,
    TopicEvidenceBriefReviewStatus,
    TopicEvidenceClaim,
    TopicEvidenceClaimOrigin,
    TopicEvidenceClaimStatus,
)
from ...schemas.topic_literature import TopicSourceRecord, TopicSourceTable
from ..agents.promotion import assert_promoted_status_is_holdable
from ..retrieval.generic_topic_lanes import (
    DATASET_REUSE_QUERY_LANE,
    GENERIC_REQUIRED_LANES,
    GENERIC_SCOPE_TERM_QUERY_LANE,
    GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSION,
    build_generic_topic_evidence_query_plan,
)
from ..retrieval.topic_sources import (
    R5_TOPIC_EVIDENCE_QUERY_PLAN_VERSION,
    TopicSourceHarvester,
    build_r5_topic_evidence_query_plan,
    generic_topic_evidence_protocol_version,
)
from .dataset_narrative import ContextReviewStatus
from .evidence_requests import (
    R5ContextEvidenceRequest,
    R5ContextEvidenceRequestKind,
)
from .review_gates import (
    ArtifactGateStatus,
    gate_topic_evidence_review_item,
)

TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION = "topic_evidence_brief_synthesizer/v7"
TOPIC_FIELD_STATE_SYNTHESIZER_PROMPT_VERSION = "topic_field_state_synthesizer/v3"

REQUIRED_TOPIC_EVIDENCE_LANES = [
    "geometry_theory_methods",
    "noise_shared_variability_geometry",
    "latent_dynamics_state_space",
    "multi_area_coding_communication",
    "temporal_latency_dynamics",
    "circuit_interpretation",
    "movement_body_state_confound",
    "ibl_bwm_public_reuse",
    "cross_subject_session_lab_generalization",
    "close_priors_already_answered",
    "live_tensions_and_limitations",
]

#: The headings the field-state synthesizer must write, one section each.
#:
#: These MUST between them cover every dimension in ``GENERIC_REQUIRED_LANES``, because the
#: independent reviewer grades ``generic_lane_coverage`` and ``field_state_complete`` against those
#: dimensions while the synthesizer is asked only for these headings. The two lists were written by
#: different concerns at different times and drifted: for eleven headings' worth of runs, three
#: graded dimensions -- competing explanations/confounds, boundary conditions/generalization, and
#: dataset/resource reuse -- had NO heading to be written into. Evidence serving only those
#: dimensions therefore had nowhere to go and was dropped silently: measured across all 23 retained
#: review packets (three datasets, six sets), 15%-50% of every corpus was cited by no section, no
#: claim and no diagnostic, and the climate d3p6 leg exhausted its revision budget on
#: ``field_state_complete`` naming exactly that evidence ("never bind or discuss the retrieved
#: ENSO/QBO/snow-cover evidence cards"). ``test_field_state_sections_cover_every_graded_dimension``
#: pins the correspondence so the two lists cannot drift apart again.
TOPIC_FIELD_STATE_REQUIRED_SECTIONS = [
    "Scope and non-claims",
    "Why the field is unsettled now",
    "Background priors and core constructs",
    "Theoretical progress",
    "Experimental progress",
    "Analysis methods and inference limits",
    "Competing explanations and confounds",
    "Boundary conditions and generalization",
    "Convergences across subfields",
    "Dissociations and live tensions",
    "Close priors / already answered questions",
    "Dataset and resource reuse",
    "Gaps that could generate QuestionSeeds",
    "Evidence quality and provenance notes",
]

#: Which graded dimension each required heading answers. Every value is a member of
#: ``GENERIC_REQUIRED_LANES``; headings that serve no single dimension (scope statement, provenance
#: notes, cross-cutting synthesis) map to ``None`` and are excluded from the coverage guard.
TOPIC_FIELD_STATE_SECTION_DIMENSIONS: dict[str, str | None] = {
    "Scope and non-claims": None,
    "Why the field is unsettled now": "unresolved_tensions",
    "Background priors and core constructs": "background_core_constructs",
    "Theoretical progress": None,
    "Experimental progress": None,
    "Analysis methods and inference limits": "methods_measurement_limits",
    "Competing explanations and confounds": "competing_explanations_confounds",
    "Boundary conditions and generalization": "boundary_conditions_generalization",
    "Convergences across subfields": None,
    "Dissociations and live tensions": "unresolved_tensions",
    "Close priors / already answered questions": "close_prior_already_answered",
    "Dataset and resource reuse": "dataset_resource_reuse",
    "Gaps that could generate QuestionSeeds": "open_gaps",
    "Evidence quality and provenance notes": None,
}


class TopicSourceAbstractStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    METADATA_ONLY = "metadata_only"
    PROVIDER_ERROR = "provider_error"
    AMBIGUOUS = "ambiguous"


class TopicSourceSnippetKind(StrEnum):
    ABSTRACT = "abstract"
    TITLE_ONLY = "title_only"
    PROVIDER_SNIPPET = "provider_snippet"
    FULLTEXT_EXCERPT = "fulltext_excerpt"
    METADATA = "metadata"


class R5TopicSourceRecordEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    lane_ids: list[str] = Field(default_factory=list)
    query_ids: list[str] = Field(default_factory=list)
    title: str
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    openalex_id: str = ""
    semantic_scholar_id: str = ""
    url: str = ""
    venue: str = ""
    publication_types: list[str] = Field(default_factory=list)
    abstract_or_snippet: str = ""
    abstract_status: TopicSourceAbstractStatus = TopicSourceAbstractStatus.UNAVAILABLE
    snippet_kind: TopicSourceSnippetKind = TopicSourceSnippetKind.TITLE_ONLY
    ranking_features: dict[str, float] = Field(default_factory=dict)
    dedupe_key: str = ""
    source_quality_flags: list[str] = Field(default_factory=list)
    fulltext_rights_assertions: list[ExternalEvidenceRightsAssertion] = Field(default_factory=list)
    # The lawful, lower-authority text that existed before an enrichment attempt replaced the
    # display field with a fetched full-text excerpt.  These fields are intentionally distinct from
    # fulltext_provenance: an unverified fetched excerpt may be discarded while a retained abstract
    # or provider snippet remains usable at its original authority.
    fulltext_fallback_abstract_or_snippet: str = ""
    fulltext_fallback_snippet_kind: TopicSourceSnippetKind | None = None
    # Live-readiness LR-C: present iff this record was upgraded to FULLTEXT_EXCERPT by the OA enrichment
    # plus-on. The FulltextExcerpt validator enforces content_digest == hash(excerpt).
    fulltext_provenance: FulltextExcerpt | None = None

    @model_validator(mode="before")
    @classmethod
    def refuse_persisted_credentials(cls, value: object) -> object:
        """Keep source YAML and every later prompt/export surface credential-free."""

        assert_secret_free_persisted_value(value, path=cls.__name__)
        return value

    @field_validator("source_record_id", "title")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("R5TopicSourceRecordEvidence identifiers must be non-empty")
        return value

    @model_validator(mode="after")
    def enforce_fulltext_provenance(self) -> R5TopicSourceRecordEvidence:
        # DP-6 anti-fabrication: a FULLTEXT_EXCERPT record MUST carry provenance whose excerpt IS the
        # shown text (the FulltextExcerpt validator already enforces digest == hash(excerpt)). A fulltext
        # claim with no provenance, a digest mismatch, or a shown-text mismatch is REJECTED — a
        # fabricated "fulltext" can never masquerade as fetched evidence.
        if self.snippet_kind == TopicSourceSnippetKind.FULLTEXT_EXCERPT:
            if self.fulltext_provenance is None:
                raise ValueError(
                    "a FULLTEXT_EXCERPT record requires fulltext_provenance (fabrication guard)"
                )
            if self.fulltext_provenance.excerpt != self.abstract_or_snippet.strip():
                raise ValueError(
                    "FULLTEXT_EXCERPT record's shown text must equal its fetched provenance excerpt"
                )
        elif self.fulltext_provenance is not None:
            raise ValueError("fulltext_provenance is only valid on a FULLTEXT_EXCERPT record")
        assertion_ids = [item.assertion_id for item in self.fulltext_rights_assertions]
        if len(assertion_ids) != len(set(assertion_ids)):
            raise ValueError("R5 topic source fulltext rights assertion IDs must be unique")
        fallback_text = self.fulltext_fallback_abstract_or_snippet.strip()
        if bool(fallback_text) != (self.fulltext_fallback_snippet_kind is not None):
            raise ValueError("full-text fallback text and snippet kind must be present together")
        if self.fulltext_fallback_snippet_kind not in {
            None,
            TopicSourceSnippetKind.ABSTRACT,
            TopicSourceSnippetKind.PROVIDER_SNIPPET,
        }:
            raise ValueError("full-text fallback may be only an abstract or provider snippet")
        if fallback_text and self.snippet_kind != TopicSourceSnippetKind.FULLTEXT_EXCERPT:
            raise ValueError("full-text fallback is valid only on a FULLTEXT_EXCERPT record")
        if (
            self.snippet_kind
            in {
                TopicSourceSnippetKind.ABSTRACT,
                TopicSourceSnippetKind.PROVIDER_SNIPPET,
                TopicSourceSnippetKind.FULLTEXT_EXCERPT,
            }
            and self.abstract_status != TopicSourceAbstractStatus.AVAILABLE
        ):
            raise ValueError("claim-supporting snippet kinds require abstract_status=available")
        return self

    @property
    def can_support_claims(self) -> bool:
        if (
            self.snippet_kind == TopicSourceSnippetKind.FULLTEXT_EXCERPT
            and not fulltext_rights_are_verified(self)
        ):
            return fulltext_fallback_can_support_claims(self)
        return (
            self.abstract_status == TopicSourceAbstractStatus.AVAILABLE
            and self.snippet_kind
            not in {TopicSourceSnippetKind.TITLE_ONLY, TopicSourceSnippetKind.METADATA}
            and _contains_non_metadata_source_text(self)
        )


_RIGHTS_VERIFIED_VALUES = frozenset(
    {
        "verified",
        "rights_verified",
        "open_access_verified",
        "verified_open_access",
    }
)
_RIGHTS_UNVERIFIED_VALUES = frozenset(
    {
        "false",
        "missing",
        "not_verified",
        "rights_unverified",
        "unknown",
        "unverified",
    }
)


def fulltext_rights_are_verified(record: R5TopicSourceRecordEvidence) -> bool:
    """Return true only for an explicit, non-conflicting full-text rights decision.

    Historical ``FulltextExcerpt`` objects predate the typed rights contract.  Their route and
    source URL are provenance, not authorization, so absence of a verification marker fails low.
    The deliberately small amount of shape tolerance here lets this boundary consume the new typed
    location assertion without coupling scientific authority to its final field spelling.
    """
    if record.snippet_kind != TopicSourceSnippetKind.FULLTEXT_EXCERPT:
        return False
    provenance = record.fulltext_provenance
    if provenance is None or _explicit_rights_marker(provenance) is not True:
        return False
    assertion = getattr(provenance, "rights_assertion", None)
    attempt = getattr(provenance, "retrieval_attempt", None)
    if assertion is None or attempt is None:
        return False
    if _explicit_rights_marker(assertion) is not True:
        return False
    if getattr(attempt, "source_record_id", "") != record.source_record_id:
        return False
    if getattr(attempt, "provider", None) != getattr(assertion, "provider", None):
        return False
    matching = [
        item
        for item in record.fulltext_rights_assertions
        if item.assertion_id == assertion.assertion_id
    ]
    return len(matching) == 1 and matching[0] == assertion


def _explicit_rights_marker(value: object) -> bool | None:
    verified = getattr(value, "has_verified_rights", None)
    if type(verified) is bool:
        return verified
    authorized = getattr(value, "authorizes_short_excerpt", None)
    if type(authorized) is bool:
        return authorized
    direct = getattr(value, "rights_verified", None)
    if type(direct) is bool:
        return direct
    if isinstance(value, dict):
        payload = value
    elif hasattr(value, "model_dump"):
        payload = value.model_dump(mode="python")
    else:
        payload = vars(value) if hasattr(value, "__dict__") else {}
    for key in (
        "rights_verified",
        "rights_status",
        "verification_status",
        "access_verification_status",
    ):
        marker = payload.get(key)
        if type(marker) is bool:
            return marker
        if marker is None:
            continue
        normalized = str(getattr(marker, "value", marker)).strip().lower()
        if normalized in _RIGHTS_VERIFIED_VALUES:
            return True
        if normalized in _RIGHTS_UNVERIFIED_VALUES:
            return False
    return None


def _contains_non_metadata_source_text(record: R5TopicSourceRecordEvidence) -> bool:
    """Reject a structural metadata row mislabeled as abstract/snippet evidence.

    This is an authority check, not a prose-quality score: even a terse paraphrase survives when it
    contains text beyond the record's title, identifiers, URL, year, and metadata labels.
    """
    text_tokens = re.findall(r"[a-z]+", record.abstract_or_snippet.lower())
    if not text_tokens:
        return False
    metadata_text = " ".join(
        [
            record.title,
            record.doi,
            record.pmid,
            record.openalex_id,
            record.semantic_scholar_id,
            record.url,
            record.venue,
            *record.publication_types,
            str(record.year or ""),
        ]
    ).lower()
    metadata_tokens = set(re.findall(r"[a-z]+", metadata_text)) | {
        "abstract",
        "author",
        "authors",
        "citation",
        "doi",
        "issue",
        "journal",
        "metadata",
        "pages",
        "pmid",
        "published",
        "publisher",
        "title",
        "url",
        "venue",
        "volume",
        "year",
    }
    return any(token not in metadata_tokens for token in text_tokens)


def rights_safe_source_text_and_kind(
    record: R5TopicSourceRecordEvidence,
) -> tuple[str, TopicSourceSnippetKind | None]:
    """Return only text whose authority survives the full-text rights boundary."""

    if record.snippet_kind != TopicSourceSnippetKind.FULLTEXT_EXCERPT:
        return record.abstract_or_snippet.strip(), record.snippet_kind
    if fulltext_rights_are_verified(record):
        return record.abstract_or_snippet.strip(), TopicSourceSnippetKind.FULLTEXT_EXCERPT
    fallback_text = record.fulltext_fallback_abstract_or_snippet.strip()
    if fallback_text and record.fulltext_fallback_snippet_kind in {
        TopicSourceSnippetKind.ABSTRACT,
        TopicSourceSnippetKind.PROVIDER_SNIPPET,
    }:
        return fallback_text, record.fulltext_fallback_snippet_kind
    return "", None


def fulltext_fallback_can_support_claims(record: R5TopicSourceRecordEvidence) -> bool:
    """Whether an unverified full-text record retains lawful abstract/snippet authority."""

    fallback_text, fallback_kind = rights_safe_source_text_and_kind(record)
    if fallback_kind not in {
        TopicSourceSnippetKind.ABSTRACT,
        TopicSourceSnippetKind.PROVIDER_SNIPPET,
    }:
        return False
    fallback_record = record.model_copy(
        update={
            "abstract_or_snippet": fallback_text,
            "snippet_kind": fallback_kind,
            "abstract_status": TopicSourceAbstractStatus.AVAILABLE,
            "fulltext_provenance": None,
        }
    )
    return _contains_non_metadata_source_text(fallback_record)


class R5TopicEvidenceSourceTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_id: str
    query_plan_id: str = ""
    protocol_version: str = R5_TOPIC_EVIDENCE_QUERY_PLAN_VERSION
    records: list[R5TopicSourceRecordEvidence] = Field(default_factory=list)
    lane_coverage: dict[str, int] = Field(default_factory=dict)
    source_quality_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def refuse_persisted_credentials(cls, value: object) -> object:
        assert_secret_free_persisted_value(value, path=cls.__name__)
        return value


class TopicEvidenceRightsDegradationReceipt(BaseModel):
    """Pure authority projection over an immutable persisted source table.

    The orchestration layer may persist this receipt beside a legacy artifact.  This context helper
    never rewrites that artifact; the original table digest remains the binding identity.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["topic_evidence_rights_degradation/v1"] = (
        "topic_evidence_rights_degradation/v1"
    )
    source_table_digest: str
    degraded_source_record_ids: list[str] = Field(default_factory=list)
    abstract_fallback_source_record_ids: list[str] = Field(default_factory=list)
    metadata_only_source_record_ids: list[str] = Field(default_factory=list)
    authority_after_degradation: Literal["abstract_or_metadata_only"] = "abstract_or_metadata_only"
    warning_code: Literal["fulltext_rights_unverified"] = "fulltext_rights_unverified"
    warning_message: str = (
        "Full-text rights were not verified for the listed legacy or injected records; "
        "their fetched text is excluded and they retain only an original abstract/provider "
        "snippet when recorded, otherwise metadata-only authority."
    )


def assess_fulltext_rights_degradation(
    source_table: R5TopicEvidenceSourceTable,
) -> TopicEvidenceRightsDegradationReceipt:
    """Identify legacy/injected full-text records that fail the new rights boundary."""

    degraded_ids = sorted(
        {
            record.source_record_id
            for record in source_table.records
            if record.snippet_kind == TopicSourceSnippetKind.FULLTEXT_EXCERPT
            and not fulltext_rights_are_verified(record)
        }
    )
    return TopicEvidenceRightsDegradationReceipt(
        source_table_digest=stable_hash(source_table),
        degraded_source_record_ids=degraded_ids,
        abstract_fallback_source_record_ids=[
            record.source_record_id
            for record in source_table.records
            if record.source_record_id in degraded_ids
            and fulltext_fallback_can_support_claims(record)
        ],
        metadata_only_source_record_ids=[
            record.source_record_id
            for record in source_table.records
            if record.source_record_id in degraded_ids
            and not fulltext_fallback_can_support_claims(record)
        ],
    )


class TopicEvidenceGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_id: str
    label: str
    source_record_ids: list[str] = Field(default_factory=list)
    rationale: str = ""


class SourceEvidenceCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    title: str
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    openalex_id: str = ""
    semantic_scholar_id: str = ""
    url: str = ""
    lane_ids: list[str] = Field(default_factory=list)
    subfield_tags: list[str] = Field(default_factory=list)
    abstract_or_excerpt: str = ""
    why_included: str = ""
    key_contribution: str = ""
    claims_or_gaps_supported: list[str] = Field(default_factory=list)
    can_support_claims: bool = False
    quality_flags: list[str] = Field(default_factory=list)
    exclusion_reason: str = ""

    @model_validator(mode="before")
    @classmethod
    def refuse_prompt_credentials(cls, value: object) -> object:
        # These cards are serialized directly into the field-state and Question Scientist packets.
        assert_secret_free_persisted_value(value, path=cls.__name__)
        return value

    @field_validator("source_record_id", "title")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("SourceEvidenceCard identifiers must be non-empty")
        return value


class TopicFieldStateSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str
    heading: str
    synthesis: str
    source_record_ids: list[str] = Field(default_factory=list)

    @field_validator("section_id", "heading", "synthesis")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("TopicFieldStateSection fields must be non-empty")
        return value


class TopicFieldStateDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_state_id: str
    prompt_version: str = TOPIC_FIELD_STATE_SYNTHESIZER_PROMPT_VERSION
    provider_id: str = ""
    model_id: str = ""
    input_digest: str = ""
    source_table_digest: str = ""
    sections: list[TopicFieldStateSection] = Field(default_factory=list)
    evidence_cards: list[SourceEvidenceCard] = Field(default_factory=list)
    evidence_requests: list[R5ContextEvidenceRequest] = Field(default_factory=list)
    source_quality_diagnostics: list[str] = Field(default_factory=list)
    review_status: str = "draft"

    @model_validator(mode="after")
    def enforce_draft_and_prompt(self) -> TopicFieldStateDraft:
        if self.prompt_version != TOPIC_FIELD_STATE_SYNTHESIZER_PROMPT_VERSION:
            raise ValueError("TopicFieldStateDraft uses stale prompt version")
        if self.review_status != "draft":
            raise ValueError("TopicFieldStateDraft must remain draft before human import")
        return self


class _TopicEvidenceBriefModelOutput(TopicEvidenceBrief):
    """Generation-boundary mirror of TopicEvidenceBrief: code-level fields are code-stamped,
    never model-produced. brief_id and retrieval_manifest_digest are removed from the
    model-facing JSON schema (the model is never asked for them) and tolerated when empty;
    canonical_scope stays asked (genuine content) but an empty value is defaulted from the
    local brief — and flagged — by the caller. NEVER persisted:
    build_topic_evidence_brief_draft_bundle rebuilds a strict TopicEvidenceBrief with the
    stamped values, re-running every strict validator."""

    brief_id: SkipJsonSchema[str] = ""
    retrieval_manifest_digest: SkipJsonSchema[str] = ""

    @field_validator("brief_id", "canonical_scope", "retrieval_manifest_digest")
    @classmethod
    def require_text(cls, value: str) -> str:
        # Same-name override of the strict parent validator: the generation boundary
        # tolerates empty code-level fields; the rebuilt strict brief enforces them again.
        return value.strip()


class TopicEvidenceBriefDraftBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundle_id: str
    source_table: TopicSourceTable
    r5_source_table: R5TopicEvidenceSourceTable | None = None
    local_brief: TopicEvidenceBrief
    gpt_brief: TopicEvidenceBrief
    recommended_brief: TopicEvidenceBrief
    prompt_version: str = TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION
    provider_id: str = ""
    model_id: str = ""
    input_digest: str
    local_evidence_groups: list[TopicEvidenceGroup] = Field(default_factory=list)
    source_evidence_cards: list[SourceEvidenceCard] = Field(default_factory=list)
    field_state_draft: TopicFieldStateDraft | None = None
    evidence_requests: list[R5ContextEvidenceRequest] = Field(default_factory=list)
    auto_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def force_draft_outputs(self) -> TopicEvidenceBriefDraftBundle:
        if self.prompt_version != TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION:
            raise ValueError("TopicEvidenceBrief draft bundle uses stale prompt version")
        for brief in [self.local_brief, self.gpt_brief, self.recommended_brief]:
            if brief.review_status != TopicEvidenceBriefReviewStatus.DRAFT:
                raise ValueError("TopicEvidenceBrief draft bundle can only contain draft briefs")
            _validate_claim_source_records(brief, self.source_table)
        if self.r5_source_table is not None:
            _validate_r5_source_table(self.r5_source_table, self.source_table)
        if self.field_state_draft is not None:
            _validate_field_state_draft(self.field_state_draft, self.r5_source_table)
        return self


class TopicEvidenceBriefReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: str
    bundle_id: str
    brief_id: str
    recommended_brief: TopicEvidenceBrief
    local_brief: TopicEvidenceBrief
    gpt_brief: TopicEvidenceBrief
    prompt_version: str = ""
    provider_id: str = ""
    model_id: str = ""
    input_digest: str = ""
    source_table_digest: str = ""
    r5_source_table: R5TopicEvidenceSourceTable | None = None
    local_evidence_groups: list[TopicEvidenceGroup] = Field(default_factory=list)
    source_evidence_cards: list[SourceEvidenceCard] = Field(default_factory=list)
    field_state_draft: TopicFieldStateDraft | None = None
    evidence_requests: list[R5ContextEvidenceRequest] = Field(default_factory=list)
    auto_flags: list[str] = Field(default_factory=list)


class TopicEvidenceBriefReviewPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: str
    items: list[TopicEvidenceBriefReviewItem] = Field(default_factory=list)


class TopicEvidenceBriefReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: str
    brief_id: str
    status: ContextReviewStatus = ContextReviewStatus.DRAFT
    reviewer: str = ""
    notes: str = ""
    required_changes: list[str] = Field(default_factory=list)
    evidence_request_waivers: list[str] = Field(default_factory=list)
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def enforce_decision_metadata(self) -> TopicEvidenceBriefReviewDecision:
        if self.status == ContextReviewStatus.DRAFT:
            return self
        if not self.reviewer.strip():
            raise ValueError("non-draft TopicEvidenceBrief review requires reviewer")
        if not self.notes.strip():
            raise ValueError("non-draft TopicEvidenceBrief review requires notes")
        if self.status == ContextReviewStatus.EXPERT_REVIEWED and self.required_changes:
            raise ValueError("expert-reviewed TopicEvidenceBrief cannot have required_changes")
        if self.status == ContextReviewStatus.NEEDS_REVISION and not self.required_changes:
            raise ValueError("needs_revision TopicEvidenceBrief review requires required_changes")
        if self.reviewed_at is None:
            self.reviewed_at = datetime.now(UTC)
        return self


class TopicEvidenceBriefReviewDecisionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_batch_id: str
    pack_id: str
    expert_reviewer: str = ""
    decisions: list[TopicEvidenceBriefReviewDecision] = Field(default_factory=list)


class TopicEvidenceBriefImportResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted_briefs: list[TopicEvidenceBrief] = Field(default_factory=list)
    rejected_brief_ids: list[str] = Field(default_factory=list)
    unresolved_brief_ids: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def build_topic_evidence_brief_draft_bundle(
    *,
    provider: StructuredModelProvider,
    intent: ResearchIntent,
    source_table: TopicSourceTable | None = None,
    retrieval_protocol: str = R5_TOPIC_EVIDENCE_QUERY_PLAN_VERSION,
    scope: ResolvedResearchScope | None = None,
    # Raised with the kept-record count, because a budget that silently trims is the failure the
    # raise exists to avoid. Measured 2026-08-19 with 64 records: the brief packet was 251,691 chars
    # against a 250,000 budget and the compactor trimmed 51 fields -- a corpus enlarged on paper and
    # cut before it reached the model. The consolidation gate already runs at 1,000,000, so this is
    # well inside what the product does elsewhere.
    max_prompt_chars: int = 400_000,
) -> TopicEvidenceBriefDraftBundle:
    source_table = source_table or _harvest_topic_sources(
        intent,
        retrieval_protocol=retrieval_protocol,
        scope=scope,
    )
    r5_source_table = build_r5_topic_source_table(source_table)
    local_brief = build_local_topic_evidence_brief(
        intent=intent, source_table=source_table, scope=scope
    )
    local_evidence_groups = build_local_topic_evidence_groups(source_table)
    # Q1: cards carry the SCOPE-DRIVEN off-topic decision (no hardcoded domain list); the same scope
    # feeds the gate's claim-supporting view so gate + compiler agree on what is on-topic.
    source_evidence_cards = build_source_evidence_cards(r5_source_table, scope)
    evidence_requests = build_context_evidence_requests(source_evidence_cards, r5_source_table)
    field_state_user_packet = {
        "prompt_version": TOPIC_FIELD_STATE_SYNTHESIZER_PROMPT_VERSION,
        "research_intent": intent.model_dump(mode="json"),
        "resolved_scope": {
            "terms": list(scope.terms) if scope is not None else list(intent.topic_terms),
            "declared_by_user": list(intent.topic_terms),
        },
        "required_sections": TOPIC_FIELD_STATE_REQUIRED_SECTIONS,
        # These are semantic review dimensions, not query labels. Generic v2 source cards carry only
        # truthful scope-term acquisition lineage; the model must judge dimensions from the evidence.
        "required_lanes": list(GENERIC_REQUIRED_LANES),
        "query_lineage_is_not_semantic_coverage": True,
        "source_evidence_cards": [
            card.model_dump(mode="json")
            for card in source_evidence_cards
            if card.can_support_claims
        ],
        "excluded_or_diagnostic_cards": [
            card.model_dump(mode="json")
            for card in source_evidence_cards
            if not card.can_support_claims
        ],
        "evidence_requests": [request.model_dump(mode="json") for request in evidence_requests],
        "instructions": {
            "review_status": "draft",
            "claim_level_source_ids_required": True,
            "do_not_use_title_or_metadata_only_records_for_claims": True,
            "do_not_generate_question_seeds": True,
            "do_not_include": [
                "target dataset exact schemas",
                "joint coverage",
                "capability registry",
                "operator receipts",
                "QBench",
                "confirmation outcomes",
                "QuestionCard",
                "AnalysisContract",
            ],
        },
    }
    field_state_user_prompt, field_state_compaction_flags = _compact_topic_packet(
        field_state_user_packet,
        packet_name="topic_field_state",
        max_prompt_chars=max_prompt_chars,
    )
    field_state_draft = provider.generate_structured(
        system_prompt=_load_prompt(TOPIC_FIELD_STATE_SYNTHESIZER_PROMPT_VERSION),
        user_prompt=field_state_user_prompt,
        output_model=TopicFieldStateDraft,
    )
    field_state_draft, field_state_flags = _force_field_state_draft(
        field_state_draft,
        source_evidence_cards,
        evidence_requests,
        provider_id=provider.provider_id,
        model_id=getattr(provider, "model_name", ""),
        input_digest=stable_hash(field_state_user_packet),
        source_table_digest=stable_hash(r5_source_table),
    )
    user_packet = {
        "prompt_version": TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION,
        "research_intent": intent.model_dump(mode="json"),
        "resolved_scope": {
            "terms": list(scope.terms) if scope is not None else list(intent.topic_terms),
            "declared_by_user": list(intent.topic_terms),
        },
        "allowed_source_record_ids": [record.source_record_id for record in source_table.records],
        "source_records": [_record_payload(record) for record in source_table.records],
        "r5_lane_source_table": r5_source_table.model_dump(mode="json"),
        # The INDEX, never the prose. The field-state draft is unreviewed model output, so its
        # synthesis must not cross into another model's input and be paraphrased as though it had
        # earned authority -- that rule stays. But the draft also groups the SAME source records
        # this drafter already holds, by scientific dimension, and those groupings are pointers
        # rather than findings. Withholding them made the two artifacts unable to agree while the
        # same independent reviewer grades them together: measured 2026-08-19 across two datasets
        # and ten reviewer draws each, first-draft briefs carried zero `already_answered` claims in
        # 20 of 20 draws, while the draft's own close-prior section named source-backed close
        # priors from the same packet, and the reviewer -- correctly -- called the contradiction.
        "field_state_status": "draft_synthesis_withheld_dimension_index_supplied",
        # Each entry carries the graded dimension it answers. Supplying the headings and the eight
        # dimension names as two unrelated lists reproduced, inside one packet, the drift this card
        # exists to remove: the drafter had to map fourteen English headings onto eight dimension
        # keys by reading them, and the prompt was reduced to string-matching "close-prior heading"
        # to find one. A section that answers no single dimension carries an empty string.
        "field_state_dimension_index": [
            {
                "section_id": section.section_id,
                "heading": section.heading,
                "semantic_dimension": (
                    TOPIC_FIELD_STATE_SECTION_DIMENSIONS.get(section.heading) or ""
                ),
                "source_record_ids": list(section.source_record_ids),
            }
            for section in field_state_draft.sections
        ],
        # Still empty, and still correct: nothing reviews the field state before this step, so no
        # field-state claim has review authority to lend. The slot is kept so that a future
        # reviewed field state has somewhere to arrive.
        "reviewed_field_state_claims": [],
        # These are semantic drafting dimensions. They are deliberately not acquisition labels.
        "required_lanes": list(GENERIC_REQUIRED_LANES),
        "query_lineage_is_not_semantic_coverage": True,
        "local_evidence_groups": [group.model_dump(mode="json") for group in local_evidence_groups],
        "local_candidate_claims": [claim.model_dump(mode="json") for claim in local_brief.claims],
        "instructions": {
            "review_status": "draft",
            "cite_source_record_ids": True,
            "title_or_metadata_only_records_cannot_support_claims": True,
            "separate_background_limits_methods_close_prior_and_open_tensions": True,
            "do_not_include": [
                "target dataset exact schemas",
                "joint coverage",
                "capability registry",
                "operator receipts",
                "QBench",
                "confirmation outcomes",
                "QuestionCard",
                "AnalysisContract",
            ],
        },
    }
    user_prompt, brief_compaction_flags = _compact_topic_packet(
        user_packet, packet_name="topic_evidence_brief", max_prompt_chars=max_prompt_chars
    )
    input_digest = stable_hash(user_packet)
    model_brief = provider.generate_structured(
        system_prompt=_load_prompt(TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION),
        user_prompt=user_prompt,
        output_model=_TopicEvidenceBriefModelOutput,
    )
    gpt_brief, finalize_flags = _finalize_gpt_brief(
        model_brief,
        source_table,
        local_brief=local_brief,
        provider_id=provider.provider_id,
        model_id=getattr(provider, "model_name", ""),
        input_digest=input_digest,
    )
    recommended = merge_topic_evidence_briefs(local_brief, gpt_brief, source_table)
    return TopicEvidenceBriefDraftBundle(
        bundle_id=f"topic-evidence-draft-{input_digest[:12]}",
        source_table=source_table,
        r5_source_table=r5_source_table,
        local_brief=local_brief,
        gpt_brief=gpt_brief,
        recommended_brief=recommended,
        provider_id=provider.provider_id,
        model_id=getattr(provider, "model_name", ""),
        input_digest=input_digest,
        local_evidence_groups=local_evidence_groups,
        source_evidence_cards=source_evidence_cards,
        field_state_draft=field_state_draft,
        evidence_requests=evidence_requests,
        auto_flags=[
            *_topic_bundle_flags(gpt_brief, source_table, evidence_requests),
            *finalize_flags,
            *field_state_flags,
            *field_state_compaction_flags,
            *brief_compaction_flags,
        ],
    )


def build_local_topic_evidence_brief(
    *,
    intent: ResearchIntent,
    source_table: TopicSourceTable,
    scope: ResolvedResearchScope | None = None,
) -> TopicEvidenceBrief:
    # THE RESOLVED SCOPE FIRST. `intent.topic_terms` is what the user typed -- one anchor on the
    # neuroscience legs -- while the corpus below it was retrieved for the resolved scope, which
    # adds the terms derived from the dataset's own description. Declaring the anchor as the brief's
    # scope published `canonical_scope: "noise correlations"` for a dossier built from eighteen
    # terms' literature, and the reviewer holds the brief to the resolved scope it is shown: it read
    # the narrow declaration against the wide content and called it a contradiction.
    topic_terms = (
        (list(scope.terms) if scope is not None and scope.terms else [])
        or intent.topic_terms
        or source_table.topic_terms
        or ["systems neuroscience"]
    )
    return TopicEvidenceBrief(
        brief_id=f"topic-evidence-local-{stable_hash({'terms': topic_terms, 'records': [record.source_record_id for record in source_table.records]})[:12]}",
        topic_terms=topic_terms,
        canonical_scope=", ".join(topic_terms),
        claims=[],
        nearest_dataset_reuse_work=[
            record.title
            for record in source_table.records
            if _record_can_support_claim(record)
            and "dataset" in (record.title + " " + record.snippet).lower()
        ][:5],
        questions_already_answered=[],
        unresolved_tensions=[],
        knowledge_cutoff=date.today(),
        retrieval_manifest_digest=stable_hash(source_table),
        review_status=TopicEvidenceBriefReviewStatus.DRAFT,
    )


def build_local_topic_evidence_groups(
    source_table: TopicSourceTable,
) -> list[TopicEvidenceGroup]:
    groups: list[TopicEvidenceGroup] = []
    records_by_lane: dict[str, list[TopicSourceRecord]] = {}
    lane_by_query = _lane_by_query_id(source_table)
    for record in source_table.records:
        lanes = sorted({lane_by_query.get(query_id, "unassigned") for query_id in record.query_ids})
        for lane in lanes:
            records_by_lane.setdefault(lane, []).append(record)
    for lane, records in sorted(records_by_lane.items()):
        substantive = [record for record in records if _record_can_support_claim(record)]
        groups.append(
            TopicEvidenceGroup(
                group_id=f"topic-evidence-group-{lane}",
                label=lane,
                source_record_ids=[record.source_record_id for record in substantive[:6]],
                rationale=(
                    "Local evidence group from substantive abstracts/snippets; "
                    "not a final scientific claim."
                ),
            )
        )
    return groups


def merge_topic_evidence_briefs(
    local_brief: TopicEvidenceBrief,
    gpt_brief: TopicEvidenceBrief,
    source_table: TopicSourceTable,
) -> TopicEvidenceBrief:
    _validate_claim_source_records(gpt_brief, source_table)
    claims_by_key: dict[str, TopicEvidenceClaim] = {}
    for claim in local_brief.claims:
        claims_by_key[_claim_key(claim)] = claim
    for claim in gpt_brief.claims:
        key = _claim_key(claim)
        if key in claims_by_key:
            existing = claims_by_key[key]
            claims_by_key[key] = existing.model_copy(
                update={
                    "origin": TopicEvidenceClaimOrigin.BOTH,
                    "source_refs": sorted(set(existing.source_refs) | set(claim.source_refs)),
                    "source_record_ids": sorted(
                        set(existing.source_record_ids) | set(claim.source_record_ids)
                    ),
                    "confidence": max(existing.confidence, claim.confidence),
                }
            )
        else:
            claims_by_key[key] = claim.model_copy(
                update={"origin": TopicEvidenceClaimOrigin.GPT_SYNTHESIZED}
            )
    recommended = local_brief.model_copy(deep=True)
    recommended.brief_id = f"topic-evidence-recommended-{stable_hash({'local': local_brief.brief_id, 'gpt': gpt_brief.brief_id})[:12]}"
    recommended.claims = list(claims_by_key.values())
    recommended.nearest_dataset_reuse_work = _dedupe_strings(
        [*local_brief.nearest_dataset_reuse_work, *gpt_brief.nearest_dataset_reuse_work]
    )
    # ``claims`` is the authoritative typed literature surface. This redundant reader summary has
    # no independent authority, so derive it rather than allowing a contested/open claim to acquire
    # an ``already answered`` label through separately generated prose.
    recommended.questions_already_answered = project_questions_already_answered(recommended.claims)
    recommended.unresolved_tensions = _dedupe_strings(
        [*local_brief.unresolved_tensions, *gpt_brief.unresolved_tensions]
    )
    recommended.review_status = TopicEvidenceBriefReviewStatus.DRAFT
    _validate_claim_source_records(recommended, source_table)
    return recommended


def prepare_topic_evidence_brief_review(
    bundle: TopicEvidenceBriefDraftBundle,
) -> tuple[TopicEvidenceBriefReviewPack, TopicEvidenceBriefReviewDecisionBatch, str]:
    review_id = f"review-{bundle.bundle_id}"
    pack = TopicEvidenceBriefReviewPack(
        pack_id=f"topic-evidence-review-{stable_hash(bundle)[:12]}",
        items=[
            TopicEvidenceBriefReviewItem(
                review_id=review_id,
                bundle_id=bundle.bundle_id,
                brief_id=bundle.recommended_brief.brief_id,
                recommended_brief=bundle.recommended_brief,
                local_brief=bundle.local_brief,
                gpt_brief=bundle.gpt_brief,
                prompt_version=bundle.prompt_version,
                provider_id=bundle.provider_id,
                model_id=bundle.model_id,
                input_digest=bundle.input_digest,
                source_table_digest=stable_hash(bundle.r5_source_table or bundle.source_table),
                r5_source_table=bundle.r5_source_table,
                local_evidence_groups=bundle.local_evidence_groups,
                source_evidence_cards=bundle.source_evidence_cards,
                field_state_draft=bundle.field_state_draft,
                evidence_requests=bundle.evidence_requests,
                auto_flags=bundle.auto_flags,
            )
        ],
    )
    decisions = TopicEvidenceBriefReviewDecisionBatch(
        decision_batch_id=f"{pack.pack_id}-decisions-template",
        pack_id=pack.pack_id,
        decisions=[
            TopicEvidenceBriefReviewDecision(
                review_id=review_id,
                brief_id=bundle.recommended_brief.brief_id,
            )
        ],
    )
    return pack, decisions, render_topic_evidence_brief_review_markdown(pack)


def import_topic_evidence_brief_review_decisions(
    *,
    pack: TopicEvidenceBriefReviewPack,
    decisions: TopicEvidenceBriefReviewDecisionBatch,
    require_complete: bool = True,
) -> TopicEvidenceBriefImportResult:
    by_review_id = {item.review_id: item for item in pack.items}
    decision_by_review_id = {decision.review_id: decision for decision in decisions.decisions}
    errors: list[str] = []
    accepted: list[TopicEvidenceBrief] = []
    rejected: list[str] = []
    unresolved: list[str] = []
    if require_complete:
        missing = sorted(set(by_review_id) - set(decision_by_review_id))
        if missing:
            errors.append("Missing TopicEvidenceBrief review decisions: " + ", ".join(missing))
    for review_id, item in by_review_id.items():
        decision = decision_by_review_id.get(review_id)
        if decision is None:
            unresolved.append(item.brief_id)
            continue
        if decision.status == ContextReviewStatus.EXPERT_REVIEWED:
            import_errors = _topic_brief_serious_import_errors(item, decision)
            if import_errors:
                errors.extend(import_errors)
                unresolved.append(item.brief_id)
                continue
            brief = item.recommended_brief.model_copy(deep=True)
            brief.review_status = TopicEvidenceBriefReviewStatus.EXPERT_REVIEWED
            assert_promoted_status_is_holdable(brief, expected_gate="topic_evidence_expert_import")
            brief.brief_id = "topic-evidence-expert-reviewed"
            brief.prompt_version = item.prompt_version
            brief.provider_id = item.provider_id
            brief.model_id = item.model_id
            brief.input_digest = item.input_digest
            brief.source_table_digest = item.source_table_digest
            brief.field_state_digest = (
                stable_hash(item.field_state_draft) if item.field_state_draft else ""
            )
            brief.reviewed_at = decision.reviewed_at
            brief.expert_reviewer = decision.reviewer
            brief.review_notes = decision.notes
            accepted.append(brief)
        elif decision.status == ContextReviewStatus.REJECTED:
            rejected.append(item.brief_id)
        else:
            unresolved.append(item.brief_id)
            if require_complete:
                errors.append(f"TopicEvidenceBrief decision remains {decision.status}")
    return TopicEvidenceBriefImportResult(
        accepted_briefs=accepted,
        rejected_brief_ids=rejected,
        unresolved_brief_ids=unresolved,
        errors=errors,
    )


def write_topic_evidence_brief_review_outputs(
    bundle: TopicEvidenceBriefDraftBundle,
    *,
    corpus_root: str | Path = "corpus",
) -> dict[str, Path]:
    root = Path(corpus_root) / "context" / "topic_evidence"
    source_path = dump_data(
        bundle.r5_source_table or build_r5_topic_source_table(bundle.source_table),
        root / "sources" / "research_intent.topic_source_table.yaml",
    )
    draft_path = dump_data(bundle, root / "drafts" / "research_intent.topic_evidence_draft.yaml")
    pack, decisions, markdown = prepare_topic_evidence_brief_review(bundle)
    review_root = root / "review"
    pack_path = dump_data(pack, review_root / "topic_evidence_review_pack.yaml")
    template_path = dump_data(decisions, review_root / "topic_evidence_decisions.template.yaml")
    decision_path = dump_data(decisions, review_root / "topic_evidence_decisions.yaml")
    markdown_path = review_root / "topic_evidence_review.md"
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown, encoding="utf-8")
    field_state_markdown_path = review_root / "topic_field_state_review.md"
    field_state_markdown_path.write_text(
        render_topic_field_state_review_markdown(pack),
        encoding="utf-8",
    )
    return {
        "source_table": source_path,
        "draft": draft_path,
        "review_pack": pack_path,
        "decision_template": template_path,
        "decisions": decision_path,
        "markdown": markdown_path,
        "field_state_markdown": field_state_markdown_path,
    }


def write_reviewed_topic_evidence_briefs(
    briefs: list[TopicEvidenceBrief],
    *,
    corpus_root: str | Path = "corpus",
) -> list[Path]:
    root = Path(corpus_root) / "context" / "topic_evidence"
    return [
        dump_data(brief, root / "research_intent.topic_evidence_brief.yaml") for brief in briefs
    ]


def render_topic_evidence_brief_review_markdown(pack: TopicEvidenceBriefReviewPack) -> str:
    lines = [
        "# Topic Evidence Brief Review",
        "",
        (
            "Accept only if claims are scientifically useful, cite valid source records, "
            "and the source landscape is rich enough for Question Scientist context."
        ),
        "",
    ]
    for item in pack.items:
        brief = item.recommended_brief
        lines.extend(
            [
                f"## {brief.brief_id}",
                "",
                f"- Review ID: `{item.review_id}`",
                f"- Prompt version: `{item.prompt_version or 'unknown'}`",
                f"- Canonical scope: {brief.canonical_scope}",
                f"- Auto flags: {', '.join(item.auto_flags) if item.auto_flags else 'none'}",
                "",
                "### Retrieval Acquisition Lineage",
                "",
                *_render_lane_coverage(item.r5_source_table),
                "",
                "### Local Evidence Groups",
                "",
                *[
                    _render_topic_evidence_group(group, item.r5_source_table)
                    for group in item.local_evidence_groups
                ],
                "",
                "### Complete Topic Source Table",
                "",
                *_render_complete_topic_source_table(item.r5_source_table),
                "",
                "### Claims",
            ]
        )
        lines.extend(_render_topic_claims(item))
        lines.extend(
            [
                "",
                "### Already Answered / Close Prior",
                "",
                *[f"- {item}" for item in brief.questions_already_answered],
                "",
                "### Unresolved Tensions",
                "",
                *[f"- {item}" for item in brief.unresolved_tensions],
                "",
            ]
        )
    return "\n".join(lines)


def render_topic_field_state_review_markdown(pack: TopicEvidenceBriefReviewPack) -> str:
    lines = [
        "# Topic Field-State Review",
        "",
        (
            "This is the primary scientific review surface for current-topic context. "
            "It should read like a compact, source-backed field-state dossier: what is "
            "settled, what is contested, which methods changed the field, what close "
            "priors already answered, and where proposal-worthy gaps remain."
        ),
        "",
        (
            "Do not treat this Markdown as a fourth Question Scientist input. Accepted "
            "content must compile into the typed `TopicEvidenceBrief`."
        ),
        "",
    ]
    for item in pack.items:
        field_state = item.field_state_draft
        gate = gate_topic_evidence_review_item(item)
        lines.extend(
            [
                f"## {item.brief_id}",
                "",
                "## Artifact Status",
                "",
                f"**{gate.status.value.upper()}**",
                "",
                "### Blocking Reasons",
                "",
                *_render_gate_list(gate.reasons, empty="- No blocking reasons recorded."),
                "",
                "### Reviewer Action Checklist",
                "",
                *_render_gate_list(gate.action_items, empty="- No gate actions required."),
                "",
                f"- Review ID: `{item.review_id}`",
                f"- Field-state prompt: `{field_state.prompt_version if field_state else 'missing'}`",
                f"- Brief prompt: `{item.prompt_version or 'unknown'}`",
                f"- Provider/model: `{item.provider_id or 'unknown'}` / `{item.model_id or 'unknown'}`",
                f"- Source table digest: `{item.source_table_digest or 'missing'}`",
                f"- Auto flags: {', '.join(item.auto_flags) if item.auto_flags else 'none'}",
                "",
                "## Retrieval Acquisition Lineage And Evidence Requests",
                "",
                *_render_lane_coverage(item.r5_source_table),
                "",
                "### Evidence Requests",
                "",
                *_render_context_evidence_requests(item.evidence_requests),
                "",
            ]
        )
        if not gate.is_reviewable and field_state is not None:
            lines.extend(
                [
                    "## Field-State Synthesis",
                    "",
                    "- Artifact is blocked or fixture-only. The draft synthesis below is "
                    "shown for human repair only and is not proposer-visible.",
                    "",
                    "## Draft Synthesis For Repair Only",
                    "",
                ]
            )
            section_by_heading = {
                section.heading.lower(): section for section in field_state.sections
            }
            for heading in TOPIC_FIELD_STATE_REQUIRED_SECTIONS:
                section = section_by_heading.get(heading.lower())
                lines.extend(
                    [
                        f"### {heading}",
                        "",
                        _render_field_state_section(section),
                        "",
                    ]
                )
        elif not gate.is_reviewable:
            lines.extend(
                [
                    "## Field-State Synthesis",
                    "",
                    "- Artifact is blocked or fixture-only and no field-state draft is present.",
                    "",
                ]
            )
        elif field_state is None:
            lines.extend(["## Field-State Synthesis", "", "- Missing field-state draft.", ""])
        else:
            lines.extend(["## Field-State Synthesis", ""])
            section_by_heading = {
                section.heading.lower(): section for section in field_state.sections
            }
            for heading in TOPIC_FIELD_STATE_REQUIRED_SECTIONS:
                section = section_by_heading.get(heading.lower())
                lines.extend(
                    [
                        f"### {heading}",
                        "",
                        _render_field_state_section(section),
                        "",
                    ]
                )
        lines.extend(
            [
                "## Evidence Clusters Under Important Claims",
                "",
                *_render_topic_claim_clusters(item),
                "",
                "## Close-Prior Assessments",
                "",
                *_render_close_prior_assessments(item),
                "",
                "## Open Gaps As Question Opportunities",
                "",
                *_render_open_gap_opportunities(item),
                "",
                "## Source Quality Diagnostics",
                "",
                *_render_source_quality_diagnostics(item),
                "",
                "## Source Evidence Card Appendix",
                "",
                *_render_source_evidence_cards(item.source_evidence_cards),
                "",
            ]
        )
    return "\n".join(lines)


def _harvest_topic_sources(
    intent: ResearchIntent,
    *,
    retrieval_protocol: str = R5_TOPIC_EVIDENCE_QUERY_PLAN_VERSION,
    scope: ResolvedResearchScope | None = None,
) -> TopicSourceTable:
    # Product path: the generic, domain-neutral protocol driven by the resolved scope
    # (keywords from the scope, no neuroscience constants, no coding_geometry_bwm.yml).
    if retrieval_protocol == GENERIC_TOPIC_EVIDENCE_QUERY_PLAN_VERSION:
        if scope is None:
            raise ValueError("generic topic evidence retrieval requires a ResolvedResearchScope")
        plan = build_generic_topic_evidence_query_plan(scope)
        return TopicSourceHarvester(max_records=64).harvest(plan)
    # Legacy history: the neuroscience-lane protocol.
    if retrieval_protocol != R5_TOPIC_EVIDENCE_QUERY_PLAN_VERSION:
        raise ValueError(f"unsupported R5 topic evidence retrieval protocol: {retrieval_protocol}")
    plan = build_r5_topic_evidence_query_plan(intent)
    return TopicSourceHarvester(max_records=64).harvest(plan)


def _finalize_gpt_brief(
    model_output: _TopicEvidenceBriefModelOutput,
    source_table: TopicSourceTable,
    *,
    local_brief: TopicEvidenceBrief,
    provider_id: str,
    model_id: str,
    input_digest: str,
) -> tuple[TopicEvidenceBrief, list[str]]:
    """Rebuild the strict TopicEvidenceBrief from the generation-boundary mirror, stamping
    every code-level field from the actual retrieval identity (never from the model). The
    strict validators re-run here, so an empty digest can never reach persisted state.

    Claim grounding is SANITIZED here (live-robustness, Option A): a citation to a
    nonexistent source_record_id is dropped (never fabricated) and flagged; a claim whose
    every citation was dropped has zero evidence basis and is dropped entirely, also
    flagged. _validate_claim_source_records stays strict at the bundle/persistence and
    merge call sites — after sanitization it can only fire on a real bug."""
    flags: list[str] = []
    canonical_scope = model_output.canonical_scope.strip()
    if not canonical_scope:
        canonical_scope = local_brief.canonical_scope
        flags.append("gpt_brief_canonical_scope_defaulted_from_local")
    allowed_source_ids = {record.source_record_id for record in source_table.records}
    # D5(b): a valid claim citation must point to a source that BOTH exists AND can support a claim
    # (not title-only / metadata / off-topic). Dropping non-claim-supporting citations here (in
    # addition to nonexistent ids) keeps the brief consistent with the topic gate + stage-C readiness
    # recompute, so a partially-weak brief COMPLETES instead of crashing stage C; an all-weak claim is
    # dropped entirely. The compiler-side readiness raise stays as the last-resort backstop.
    claim_supporting_ids = {
        record.source_record_id
        for record in source_table.records
        if _record_can_support_claim(record)
    }
    claims: list[TopicEvidenceClaim] = []
    dropped_unknown_ids: list[str] = []
    dropped_weak_ids: list[str] = []
    dropped_claim_ids: list[str] = []
    for claim in model_output.claims:
        valid_refs = [sid for sid in claim.source_refs if sid in claim_supporting_ids]
        valid_ids = [sid for sid in claim.source_record_ids if sid in claim_supporting_ids]
        cited = [*claim.source_refs, *claim.source_record_ids]
        dropped_unknown_ids.extend(sid for sid in cited if sid not in allowed_source_ids)
        dropped_weak_ids.extend(
            sid for sid in cited if sid in allowed_source_ids and sid not in claim_supporting_ids
        )
        if all(sid in claim_supporting_ids for sid in cited):
            claims.append(claim)
            continue
        if not (valid_refs or valid_ids):
            dropped_claim_ids.append(claim.claim_id)
            continue
        claims.append(
            claim.model_copy(update={"source_refs": valid_refs, "source_record_ids": valid_ids})
        )
    if dropped_unknown_ids:
        flags.append(
            "gpt_brief_dropped_unknown_source_citations:"
            + ",".join(sorted(set(dropped_unknown_ids)))
        )
    if dropped_weak_ids:
        flags.append(
            "gpt_brief_dropped_non_claim_supporting_citations:"
            + ",".join(sorted(set(dropped_weak_ids)))
        )
    if dropped_claim_ids:
        flags.append("gpt_brief_dropped_unsupported_claims:" + ",".join(dropped_claim_ids))
    projected_questions = project_questions_already_answered(claims)
    raw_questions = _dedupe_strings(list(model_output.questions_already_answered))
    if raw_questions and not projected_questions:
        flags.append("questions_already_answered_without_typed_close_prior_claim")
    if raw_questions != projected_questions:
        flags.append("gpt_brief_projected_close_prior_summary_from_typed_claims")
    brief = TopicEvidenceBrief.model_validate(
        {
            **model_output.model_dump(mode="python"),
            "claims": claims,
            "questions_already_answered": projected_questions,
            "brief_id": f"topic-evidence-gpt-{input_digest[:12]}",
            "canonical_scope": canonical_scope,
            "retrieval_manifest_digest": stable_hash(source_table),
            "review_status": TopicEvidenceBriefReviewStatus.DRAFT,
            "prompt_version": TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION,
            "provider_id": provider_id,
            "model_id": model_id,
            "input_digest": input_digest,
        }
    )
    _validate_claim_source_records(brief, source_table)
    return brief, flags


def _claim_from_record(record: TopicSourceRecord, *, index: int) -> TopicEvidenceClaim:
    text = record.snippet.strip() or record.title
    status = (
        TopicEvidenceClaimStatus.METHODOLOGICAL_CHANGE
        if any(token in text.lower() for token in ["method", "analysis", "model"])
        else TopicEvidenceClaimStatus.ESTABLISHED
    )
    return TopicEvidenceClaim(
        claim_id=f"topic-claim-local-{index:03d}",
        claim=text[:500],
        status=status,
        source_refs=[record.source_record_id],
        source_record_ids=[record.source_record_id],
        origin=TopicEvidenceClaimOrigin.LOCAL_SUPPORTED,
        confidence=min(0.95, 0.45 + record.metadata_quality_score),
    )


class TopicPromptBudgetError(ValueError):
    """CLIM-09: the packet exceeds the prompt budget even after floor compaction.

    Subclasses ``ValueError`` so every existing infrastructure-failure catch still classifies it;
    carries exact measurements so the honest close is auditable without re-running anything.
    """

    def __init__(
        self, *, packet_name: str, measured_chars: int, floor_chars: int, max_prompt_chars: int
    ) -> None:
        super().__init__(
            f"topic packet '{packet_name}' exceeds the prompt budget even after compaction "
            f"(measured={measured_chars}, floor_compacted={floor_chars}, "
            f"budget={max_prompt_chars})"
        )
        self.packet_name = packet_name
        self.measured_chars = measured_chars
        self.floor_chars = floor_chars
        self.max_prompt_chars = max_prompt_chars


# Only free-text evidence excerpts are compactable. Identifiers, digests, verdicts, and every
# structured field are never trimmed — compaction changes packaging density, never identity.
_COMPACTABLE_TEXT_KEYS = frozenset(
    {"snippet_or_abstract", "abstract", "snippet", "excerpt", "fulltext_excerpt", "summary"}
)
_COMPACTION_FLOOR_CHARS = 400


def _compact_topic_packet(
    packet: dict, *, packet_name: str, max_prompt_chars: int
) -> tuple[str, list[str]]:
    """CLIM-09 measured compaction: fit the packet or close with exact measurements.

    Deterministic passes trim only long free-text evidence fields (largest first, stable order)
    toward a floor; a fit returns the rendered prompt plus one measured flag that stays visible on
    the bundle. An irreducible overflow raises :class:`TopicPromptBudgetError` — never the old
    bare guard, never a raised limit. The packet is mutated in place BEFORE digesting, so the
    input digest always binds exactly what the model received.
    """
    rendered = json.dumps(packet, sort_keys=True, ensure_ascii=False)
    if len(rendered) <= max_prompt_chars:
        return rendered, []
    original_chars = len(rendered)
    leaves: list[tuple[dict, str]] = []

    def _walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if (
                    isinstance(value, str)
                    and key in _COMPACTABLE_TEXT_KEYS
                    and len(value) > _COMPACTION_FLOOR_CHARS
                ):
                    leaves.append((node, key))
                else:
                    _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(packet)
    for shrink in (0.5, 0.25, 0.0):
        for node, key in sorted(
            leaves,
            key=lambda item: (-len(item[0][item[1]]), str(item[0].get("source_record_id", ""))),
        ):
            target = max(_COMPACTION_FLOOR_CHARS, int(len(node[key]) * shrink))
            if len(node[key]) > target:
                node[key] = node[key][:target]
        rendered = json.dumps(packet, sort_keys=True, ensure_ascii=False)
        if len(rendered) <= max_prompt_chars:
            return rendered, [
                f"topic_prompt_compacted:{packet_name}:original_chars={original_chars}:"
                f"compacted_chars={len(rendered)}:budget_chars={max_prompt_chars}:"
                f"trimmed_fields={len(leaves)}"
            ]
    raise TopicPromptBudgetError(
        packet_name=packet_name,
        measured_chars=original_chars,
        floor_chars=len(rendered),
        max_prompt_chars=max_prompt_chars,
    )


def _record_payload(record: TopicSourceRecord) -> dict:
    snippet_kind = _snippet_kind(record)
    return {
        "source_record_id": record.source_record_id,
        "source_family": record.source_family.value,
        "title": record.title,
        "year": record.year,
        "url": record.url,
        "doi": record.doi,
        "pmid": record.pmid,
        "openalex_id": record.openalex_id,
        "semantic_scholar_id": record.semantic_scholar_id,
        "venue": record.venue,
        "authors": record.authors,
        "snippet_or_abstract": record.snippet,
        "abstract_status": _abstract_status(record).value,
        "snippet_kind": snippet_kind.value,
        "can_support_claims": snippet_kind
        not in {TopicSourceSnippetKind.TITLE_ONLY, TopicSourceSnippetKind.METADATA},
        "publication_types": record.publication_types,
    }


def _validate_claim_source_records(
    brief: TopicEvidenceBrief,
    source_table: TopicSourceTable,
) -> None:
    allowed = {record.source_record_id for record in source_table.records}
    unknown: list[str] = []
    for claim in brief.claims:
        cited = claim.source_record_ids or claim.source_refs
        unknown.extend(source_id for source_id in cited if source_id not in allowed)
    if unknown:
        raise ValueError(
            "TopicEvidenceBrief cites unknown source_record_ids: " + ", ".join(unknown)
        )


def _validate_r5_source_table(
    r5_source_table: R5TopicEvidenceSourceTable,
    source_table: TopicSourceTable,
) -> None:
    allowed = {record.source_record_id for record in source_table.records}
    unknown = [
        record.source_record_id
        for record in r5_source_table.records
        if record.source_record_id not in allowed
    ]
    if unknown:
        raise ValueError("R5 topic source table contains unknown source IDs: " + ", ".join(unknown))


def build_r5_topic_source_table(source_table: TopicSourceTable) -> R5TopicEvidenceSourceTable:
    lane_by_query = _lane_by_query_id(source_table)
    records: list[R5TopicSourceRecordEvidence] = []
    for record in source_table.records:
        lanes = sorted({lane_by_query.get(query_id, "unassigned") for query_id in record.query_ids})
        snippet_kind = _snippet_kind(record)
        abstract_status = _abstract_status(record)
        quality_flags = _source_quality_flags(record, snippet_kind)
        record_payload = {
            "source_record_id": record.source_record_id,
            "lane_ids": lanes,
            "query_ids": record.query_ids,
            "title": record.title,
            "year": record.year,
            "doi": record.doi,
            "pmid": record.pmid,
            "openalex_id": record.openalex_id,
            "semantic_scholar_id": record.semantic_scholar_id,
            "url": record.url,
            "venue": record.venue,
            "publication_types": record.publication_types,
            "abstract_or_snippet": record.snippet,
            "abstract_status": abstract_status,
            "snippet_kind": snippet_kind,
            "ranking_features": {
                "relevance_score": float(record.relevance_score),
                "metadata_quality_score": float(record.metadata_quality_score),
                "cited_by_count": float(record.cited_by_count or 0),
                "lane_count": float(len(lanes)),
            },
            "dedupe_key": _topic_record_dedupe_key(record),
            "source_quality_flags": quality_flags,
        }
        # Card 1 adds a typed full-text-location assertion to both source schemas.  Preserve every
        # shared typed authority field without teaching this context layer provider-specific names.
        for field_name in R5TopicSourceRecordEvidence.model_fields:
            if field_name in record_payload or not hasattr(record, field_name):
                continue
            lowered = field_name.lower()
            if "fulltext" in lowered or "rights" in lowered:
                record_payload[field_name] = getattr(record, field_name)
        records.append(R5TopicSourceRecordEvidence.model_validate(record_payload))
    # Preserve the acquisition labels actually present (vocabulary-agnostic). Generic v2 records
    # scope-term lineage; legacy tables retain their historical labels for readability. Neither is
    # promoted to semantic coverage here; the reviewer judges that from evidence content.
    present_lanes = sorted(
        {lane for record in records for lane in record.lane_ids if lane != "unassigned"}
    )
    lane_coverage = {
        lane: sum(1 for record in records if lane in record.lane_ids) for lane in present_lanes
    }
    table_flags = [
        f"lane_missing_sources:{lane}" for lane, count in lane_coverage.items() if count == 0
    ]
    table_flags.extend(
        f"record_low_quality:{record.source_record_id}"
        for record in records
        if not record.can_support_claims
    )
    return R5TopicEvidenceSourceTable(
        table_id=f"r5-topic-source-table-{stable_hash({'source_table': source_table.table_id, 'records': [record.model_dump(mode='json') for record in records]})[:12]}",
        query_plan_id=source_table.query_plan_id,
        protocol_version=(
            generic_topic_evidence_protocol_version(source_table.query_plan_id)
            or R5_TOPIC_EVIDENCE_QUERY_PLAN_VERSION
        ),
        records=records,
        lane_coverage=lane_coverage,
        source_quality_flags=table_flags,
    )


def claim_supporting_source_ids(
    source_table: R5TopicEvidenceSourceTable,
    scope: ResolvedResearchScope | None = None,
) -> set[str]:
    """Source ids with claim-capable evidence and no structural source exclusion.

    Literal overlap with scope terms is deliberately not an authority gate: relevant sources can use
    abbreviations, equations, synonyms, or field-specific terminology. A scope-token mismatch remains
    visible on the evidence card for independent review.
    """
    return {
        record.source_record_id
        for record in source_table.records
        if record.can_support_claims and not _topic_record_is_obviously_off_topic(record, scope)
    }


def build_source_evidence_cards(
    source_table: R5TopicEvidenceSourceTable,
    scope: ResolvedResearchScope | None = None,
) -> list[SourceEvidenceCard]:
    cards: list[SourceEvidenceCard] = []
    for record in source_table.records:
        rights_unverified = (
            record.snippet_kind == TopicSourceSnippetKind.FULLTEXT_EXCERPT
            and not fulltext_rights_are_verified(record)
        )
        authority_text, authority_kind = rights_safe_source_text_and_kind(record)
        fallback_used = rights_unverified and authority_kind in {
            TopicSourceSnippetKind.ABSTRACT,
            TopicSourceSnippetKind.PROVIDER_SNIPPET,
        }
        authority_record = record.model_copy(
            update={
                "abstract_or_snippet": authority_text,
                "snippet_kind": authority_kind or TopicSourceSnippetKind.METADATA,
                "abstract_status": (
                    TopicSourceAbstractStatus.AVAILABLE
                    if authority_text
                    else TopicSourceAbstractStatus.UNAVAILABLE
                ),
                "fulltext_provenance": None if rights_unverified else record.fulltext_provenance,
            }
        )
        off_topic = _topic_record_is_obviously_off_topic(authority_record, scope)
        lexical_scope_mismatch = _topic_record_lacks_scope_tokens(authority_record, scope)
        can_support = record.can_support_claims and not off_topic
        exclusion_reason = ""
        if off_topic:
            exclusion_reason = "off_topic"
        elif rights_unverified and not fallback_used:
            exclusion_reason = "fulltext_rights_unverified"
        elif not record.can_support_claims:
            exclusion_reason = "title_or_metadata_only"
        tags = _topic_record_subfield_tags(authority_record, scope)
        contribution = _topic_record_key_contribution(authority_record)
        cards.append(
            SourceEvidenceCard(
                source_record_id=record.source_record_id,
                title=record.title,
                year=record.year,
                doi=record.doi,
                pmid=record.pmid,
                openalex_id=record.openalex_id,
                semantic_scholar_id=record.semantic_scholar_id,
                url=record.url,
                lane_ids=record.lane_ids,
                subfield_tags=tags,
                abstract_or_excerpt=authority_record.abstract_or_snippet,
                why_included=_topic_record_inclusion_reason(authority_record, tags),
                key_contribution=contribution,
                claims_or_gaps_supported=_topic_record_supported_claims(
                    authority_record, tags, scope
                ),
                can_support_claims=can_support,
                quality_flags=[
                    *record.source_quality_flags,
                    *(["fulltext_rights_unverified"] if rights_unverified else []),
                    *(["fulltext_fallback_used"] if fallback_used else []),
                    *(["off_topic"] if off_topic else []),
                    *(
                        ["scope_token_mismatch_advisory"]
                        if lexical_scope_mismatch and not off_topic
                        else []
                    ),
                ],
                exclusion_reason=exclusion_reason,
            )
        )
    return cards


def build_context_evidence_requests(
    source_cards: list[SourceEvidenceCard],
    source_table: R5TopicEvidenceSourceTable,
) -> list[R5ContextEvidenceRequest]:
    requests: list[R5ContextEvidenceRequest] = []
    # Generic v2 acquisition records which scope term produced a source. It cannot mechanically
    # establish background, tension, method, confound, boundary, reuse, close-prior, or open-gap
    # meaning. Missing semantic dimensions are therefore judged from actual evidence by the
    # independent reviewer, not converted into host-built blocking requests from query labels.
    for record in source_table.records:
        if (
            record.abstract_status == TopicSourceAbstractStatus.UNAVAILABLE
            and record.snippet_kind == TopicSourceSnippetKind.TITLE_ONLY
            and not _r5_record_is_secondary_or_off_topic(record)
        ):
            requests.append(
                R5ContextEvidenceRequest(
                    request_id=f"topic-evidence-request-abstract-{record.source_record_id}",
                    kind=R5ContextEvidenceRequestKind.NEED_ABSTRACT,
                    target_source_record_id=record.source_record_id,
                    description=(
                        "Source was retrieved but lacks an abstract/snippet, so it cannot "
                        "support field-state claims yet."
                    ),
                    blocking=False,
                )
            )
    return requests


def _lane_by_query_id(source_table: TopicSourceTable) -> dict[str, str]:
    lane_by_query: dict[str, str] = {}
    for trace in source_table.search_traces:
        if trace.query_id:
            lane_by_query.setdefault(trace.query_id, _lane_from_query_id(trace.query_id))
    for record in source_table.records:
        for query_id in record.query_ids:
            lane_by_query.setdefault(query_id, _lane_from_query_id(query_id))
    return lane_by_query


# Known topic-evidence retrieval vocabularies. The ACTIVE generic path uses one scope-term
# acquisition lineage; older generic and neuroscience artifacts retain their historical query
# labels. A query_id embeds exactly one label, and no generic label is a substring of a domain label
# (or vice versa), so a union match resolves any readable legacy artifact without promoting those
# labels to scientific coverage. Longer names first prevents prefix matches.
_ALL_KNOWN_TOPIC_LANES: tuple[str, ...] = tuple(
    sorted(
        {
            GENERIC_SCOPE_TERM_QUERY_LANE,
            *GENERIC_REQUIRED_LANES,
            *REQUIRED_TOPIC_EVIDENCE_LANES,
        },
        key=len,
        reverse=True,
    )
)


def _lane_from_query_id(query_id: str) -> str:
    for lane in _ALL_KNOWN_TOPIC_LANES:
        if lane in query_id:
            return lane
    return "unassigned"


def _abstract_status(record: TopicSourceRecord) -> TopicSourceAbstractStatus:
    snippet = record.snippet.strip()
    if not snippet:
        return TopicSourceAbstractStatus.UNAVAILABLE
    if _snippet_kind(record) == TopicSourceSnippetKind.TITLE_ONLY:
        return TopicSourceAbstractStatus.METADATA_ONLY
    return TopicSourceAbstractStatus.AVAILABLE


def _snippet_kind(record: TopicSourceRecord) -> TopicSourceSnippetKind:
    snippet = record.snippet.strip()
    if not snippet:
        return TopicSourceSnippetKind.TITLE_ONLY
    if snippet.lower() == record.venue.lower() or snippet in record.publication_types:
        return TopicSourceSnippetKind.METADATA
    if snippet.casefold() == record.title.strip().casefold():
        return TopicSourceSnippetKind.TITLE_ONLY
    return TopicSourceSnippetKind.ABSTRACT


def _source_quality_flags(
    record: TopicSourceRecord,
    snippet_kind: TopicSourceSnippetKind,
) -> list[str]:
    flags: list[str] = []
    if snippet_kind in {TopicSourceSnippetKind.TITLE_ONLY, TopicSourceSnippetKind.METADATA}:
        flags.append("cannot_support_claims")
    if record.metadata_quality_score < 0.5:
        flags.append("low_metadata_quality")
    if not (record.doi or record.pmid or record.openalex_id or record.semantic_scholar_id):
        flags.append("weak_identifier")
    if _raw_topic_record_is_secondary_or_off_topic(record):
        flags.append("excluded_non_primary_or_off_topic")
    return flags


def _force_field_state_draft(
    field_state: TopicFieldStateDraft,
    source_cards: list[SourceEvidenceCard],
    evidence_requests: list[R5ContextEvidenceRequest],
    *,
    provider_id: str,
    model_id: str,
    input_digest: str,
    source_table_digest: str,
) -> tuple[TopicFieldStateDraft, list[str]]:
    """Stamp code-owned fields and SANITIZE model grounding (live-robustness, Option A):
    a real model citing a nonexistent source_record_id must not crash the run — the unknown
    citation is DROPPED (never fabricated) and honestly flagged; a section whose citations
    were all dropped is KEPT citation-less and flagged unsupported. The persistence-side
    validator (_validate_field_state_draft) stays strict: a persisted draft citing an
    unknown id after sanitization is a real bug and still raises there."""
    card_by_id = {card.source_record_id: card for card in source_cards}
    allowed_request_ids = {request.request_id for request in evidence_requests}
    flags: list[str] = []
    dropped_source_ids: list[str] = []
    unsupported_sections: list[str] = []
    sections: list[TopicFieldStateSection] = []
    for section in field_state.sections:
        valid_ids = [sid for sid in section.source_record_ids if sid in card_by_id]
        dropped = [sid for sid in section.source_record_ids if sid not in card_by_id]
        if not dropped:
            sections.append(section)
            continue
        dropped_source_ids.extend(dropped)
        if not valid_ids:
            unsupported_sections.append(section.section_id)
        sections.append(section.model_copy(update={"source_record_ids": valid_ids}))
    unknown_requests = sorted(
        {
            request.request_id
            for request in field_state.evidence_requests
            if request.request_id not in allowed_request_ids
        }
    )
    if dropped_source_ids:
        flags.append(
            "field_state_dropped_unknown_source_citations:"
            + ",".join(sorted(set(dropped_source_ids)))
        )
    if unsupported_sections:
        flags.append(
            "field_state_section_unsupported_after_sanitization:" + ",".join(unsupported_sections)
        )
    if unknown_requests:
        # Content-wise a no-op: evidence_requests below is always replaced with the
        # code-built list; the flag records that the model emitted unknown request ids.
        flags.append("field_state_dropped_unknown_evidence_requests:" + ",".join(unknown_requests))
    # Repair before strict construction: state which supplied evidence the synthesis did not use.
    # A record the synthesizer was handed and then never cited leaves NO trace otherwise, so a
    # silent drop and a deliberate exclusion are indistinguishable in the artifact -- and the
    # reviewer, which can see both the source summaries and the sections, reads the difference as
    # evidence hidden rather than evidence declined ("this omission is not flagged anywhere in
    # source_quality_diagnostics, so material retrieved evidence is silently missing from the
    # narrative", climate d3p6 round 2, the round that exhausted the revision budget).
    #
    # This sentence is mechanical and therefore always literally true: it counts citations, and it
    # says nothing about whether the omission was scientifically right. That distinction is exactly
    # what the 2026-08-14 legs got wrong when a deterministic diagnostic asserted dimensions were
    # "unresolved" from acquisition labels -- a false scientific claim that cost three runs their
    # authority. Judging the omission remains the reviewer's; disclosing it is the host's.
    uncited = _uncited_claim_supporting_records(sections, source_cards)
    if uncited:
        claim_supporting_total = sum(1 for card in source_cards if card.can_support_claims)
        flags.append(
            f"field-state coverage: {len(uncited)} of {claim_supporting_total} claim-supporting "
            f"records are cited by no field-state section: " + ", ".join(uncited)
        )
    sanitized = field_state.model_copy(
        update={
            "field_state_id": field_state.field_state_id.strip()
            or f"topic-field-state-{input_digest[:12]}",
            "prompt_version": TOPIC_FIELD_STATE_SYNTHESIZER_PROMPT_VERSION,
            "provider_id": provider_id,
            "model_id": model_id,
            "input_digest": input_digest,
            "source_table_digest": source_table_digest,
            "sections": sections,
            "evidence_cards": source_cards,
            "evidence_requests": evidence_requests,
            "source_quality_diagnostics": [*field_state.source_quality_diagnostics, *flags],
            "review_status": "draft",
        },
        deep=True,
    )
    assert_field_state_sources_accounted(sanitized)
    return sanitized, flags


def _uncited_claim_supporting_records(
    sections: Sequence[TopicFieldStateSection],
    source_cards: Sequence[SourceEvidenceCard],
) -> list[str]:
    """Claim-supporting record ids that no section cites, in source-table order.

    Only claim-supporting cards count. A metadata-only or off-topic card is handed to the
    synthesizer as explicitly unusable, so its absence from the sections is the system working.
    """

    cited = {source_id for section in sections for source_id in section.source_record_ids}
    return [
        card.source_record_id
        for card in source_cards
        if card.can_support_claims and card.source_record_id not in cited
    ]


def field_state_dimension_representation_statements(
    field_state: TopicFieldStateDraft | None,
    brief: TopicEvidenceBrief,
) -> list[str]:
    """Host observations: a graded dimension the field state evidenced and the brief does not cite.

    The second hop of the same narrowing. Closing sources -> field_state gave the confounds,
    boundary-conditions and reuse evidence a section to live in; it did nothing about
    field_state -> brief, and six reviewer draws on the repaired climate packet failed on exactly
    that, naming the section: *"Reconcile the brief's claims array with the field_state's 'Competing
    explanations and confounds' section so no field-state-synthesized dimension with eligible
    sources is silently dropped from the brief."*

    These lines are COUNTS, never verdicts. A brief is a distillation and is not required to claim
    everything the field state discusses; whether dropping a whole evidenced dimension was right for
    this scope is a scientific judgement, and the reviewer is the one holding both artifacts. The
    host's job is only to make the drop visible, which is why this rides ``host_readiness_facts`` --
    the channel whose prompt contract already states these are observations that are neither an
    automatic pass nor an automatic fail.
    """

    if field_state is None:
        return []
    claimed = {source_id for claim in brief.claims for source_id in claim.source_record_ids}
    statements: list[str] = []
    for section in field_state.sections:
        dimension = TOPIC_FIELD_STATE_SECTION_DIMENSIONS.get(section.heading)
        if dimension is None or not section.source_record_ids:
            continue
        if any(source_id in claimed for source_id in section.source_record_ids):
            continue
        statements.append(
            f"The field state's {section.heading!r} section cites "
            f"{len(section.source_record_ids)} supplied records; no brief claim cites any of them."
        )
    return statements


def assert_field_state_sources_accounted(field_state: TopicFieldStateDraft) -> None:
    """Every claim-supporting card is cited by a section, or named as uncited in the diagnostics.

    Reads ONLY the finished artifact -- its own ``sections``, ``evidence_cards`` and
    ``source_quality_diagnostics`` -- never the caller's working variables. A post-condition that
    re-derives its answer from the same map that produced the result cannot fail, and this
    repository has shipped one that could not (the first cross-feed scale-fact guard, 2026-08-21).
    Deleting the disclosure above must make this raise; ``test_field_state_accounting_guard_is_not_
    vacuous`` mutation-proves that it does.
    """

    uncited = _uncited_claim_supporting_records(field_state.sections, field_state.evidence_cards)
    if not uncited:
        return
    disclosed = " ".join(field_state.source_quality_diagnostics)
    undisclosed = [source_id for source_id in uncited if source_id not in disclosed]
    if undisclosed:
        raise ValueError(
            "TopicFieldStateDraft leaves claim-supporting records unaccounted: they are cited by "
            "no section and named in no source_quality_diagnostic: " + ", ".join(undisclosed)
        )


def _validate_field_state_draft(
    field_state: TopicFieldStateDraft,
    source_table: R5TopicEvidenceSourceTable | None,
) -> None:
    if source_table is None:
        raise ValueError("TopicFieldStateDraft requires R5 source table")
    allowed = {record.source_record_id for record in source_table.records}
    unknown = [
        source_id
        for section in field_state.sections
        for source_id in section.source_record_ids
        if source_id not in allowed
    ]
    if unknown:
        raise ValueError(
            "TopicFieldStateDraft cites source IDs outside the source table: "
            + ", ".join(sorted(set(unknown)))
        )


def _scope_content_tokens(scope: ResolvedResearchScope | None) -> set[str]:
    """Content tokens (>=4 chars) from the resolved research scope — the dataset-AGNOSTIC on-topic
    signal that replaces the old hardcoded domain whitelist. Empty when no scope is supplied."""
    if scope is None:
        return set()
    tokens: set[str] = set()
    for term in scope.terms:
        for raw in re.split(r"[^a-z0-9]+", term.lower()):
            if len(raw) >= 4:
                tokens.add(raw)
    return tokens


def _topic_record_is_obviously_off_topic(
    record: R5TopicSourceRecordEvidence, scope: ResolvedResearchScope | None = None
) -> bool:
    """Hard structural exclusions only; lexical relevance belongs to review, not authority."""
    return _r5_record_is_secondary_or_off_topic(record)


def _topic_record_lacks_scope_tokens(
    record: R5TopicSourceRecordEvidence, scope: ResolvedResearchScope | None = None
) -> bool:
    """Advisory literal-overlap signal retained for reviewer visibility."""
    scope_tokens = _scope_content_tokens(scope)
    if len(scope_tokens) < 2:
        return False
    text = " ".join([record.title, record.abstract_or_snippet]).lower()
    return not any(token in text for token in scope_tokens)


def _r5_record_is_secondary_or_off_topic(record: R5TopicSourceRecordEvidence) -> bool:
    # Structural, domain-neutral only (a secondary-publication title or a conference-abstract DOI) — no
    # hardcoded topic vocabulary. True relevance is decided by the scope-driven check + the AI gate.
    if _title_is_secondary_publication_artifact(record.title.lower().strip()):
        return True
    return "10.3389/conf." in record.doi.lower()


def _raw_topic_record_is_secondary_or_off_topic(record: TopicSourceRecord) -> bool:
    title = record.title.lower().strip()
    if _title_is_secondary_publication_artifact(title):
        return True
    return "10.3389/conf." in record.doi.lower()


def _title_is_secondary_publication_artifact(title: str) -> bool:
    return (
        title.startswith("decision letter:")
        or title.startswith("author response:")
        or title.startswith("reviewer #")
        or title.startswith("elife assessment:")
        or "(public review)" in title
        or "public review:" in title
    )


def _topic_record_subfield_tags(
    record: R5TopicSourceRecordEvidence,
    scope: ResolvedResearchScope | None = None,
) -> list[str]:
    """Which of THIS RUN'S scope terms the record's own text carries.

    Scope-driven, for the same reason the off-topic classifier beside it is: the hardcoded
    neuroscience keyword table below decides nothing about relevance, but it does decide the English
    written onto every evidence card, and that English reaches the field state, the reviewer and the
    published artifact. `check_dataset_agnostic.py` documents this function as deferred tech debt
    judged "non-crashing"; measured 2026-08-19 on a stratospheric-dynamics packet it put
    neuroscience vocabulary on 31 of 59 cards -- "wave geometry" matched the `geometry` token -- and
    the independent reviewer raised it as an integrity concern in two of ten draws. Non-crashing is
    not the same as harmless once the words are published.

    The run's own scope terms are domain vocabulary by construction, so no table can be wrong about
    a dataset it was not written for. A record with no scope supplied is a legacy artifact and keeps
    the historical labels so its cards stay readable.
    """

    text = " ".join([record.title, record.abstract_or_snippet]).lower()
    if scope is not None:
        return [term for term in scope.terms if term.strip() and term.lower() in text]
    tags: list[str] = []
    if any(token in text for token in ["caudoputamen", "striatum", "basal ganglia"]):
        tags.append("cp_region")
    if any(
        token in text
        for token in [
            "posterior thalam",
            "posterior complex",
            "posterior thalamic nucleus",
            "pom",
            "po ",
            "po/",
        ]
    ):
        tags.append("po_region")
    if any(
        token in text
        for token in [
            "lateral posterior",
            "visual thalamus",
            "pulvinar",
            "lp ",
            "lp/",
        ]
    ):
        tags.append("lp_region")
    if any(token in text for token in ["international brain laboratory", "brain-wide map", "bwm"]):
        tags.append("ibl_bwm")
    if any(token in text for token in ["movement", "body", "whisk", "pupil", "running"]):
        tags.append("movement_body_state")
    if any(token in text for token in ["geometry", "manifold", "representational", "subspace"]):
        tags.append("geometry")
    if any(
        token in text
        for token in ["covariance", "covariability", "noise correlation", "shared variability"]
    ):
        tags.append("noise_shared_variability")
    if any(
        token in text for token in ["decode", "encoding", "latent", "dimensionality", "state space"]
    ):
        tags.append("analysis_method")
    if any(token in text for token in ["multi-area", "inter-area", "communication", "distributed"]):
        tags.append("multi_area")
    if any(token in text for token in ["latency", "temporal", "trajectory", "dynamics"]):
        tags.append("temporal_dynamics")
    if any(token in text for token in ["circuit", "connectivity", "mechanism"]):
        tags.append("circuit_interpretation")
    if any(token in text for token in ["reproduc", "cross-session", "across labs"]):
        tags.append("generalization")
    if any(token in text for token in ["review", "perspective"]):
        tags.append("review_or_perspective")
    return _dedupe_strings(tags)


def _topic_record_inclusion_reason(
    record: R5TopicSourceRecordEvidence,
    tags: list[str],
) -> str:
    lanes = ", ".join(record.lane_ids) or "unassigned"
    tag_text = ", ".join(tags) if tags else "general topic evidence"
    return f"Retrieved for lane(s) {lanes}; curated as {tag_text}."


def _topic_record_key_contribution(record: R5TopicSourceRecordEvidence) -> str:
    text = record.abstract_or_snippet.strip()
    if not text:
        return "No abstract/snippet available; retained only for diagnostics."
    return text[:360]


def _topic_record_supported_claims(
    record: R5TopicSourceRecordEvidence,
    tags: list[str],
    scope: ResolvedResearchScope | None = None,
) -> list[str]:
    supported: list[str] = []
    if scope is not None:
        # `tags` are this run's own scope terms, so the sentence is written from them rather than
        # from a table of another field's nouns.
        if DATASET_REUSE_QUERY_LANE in record.lane_ids:
            supported.append("prior use of this dataset or an equivalent resource")
        if tags:
            supported.append(f"evidence bearing on {', '.join(tags[:4])}")
        if not supported and record.can_support_claims:
            supported.append("background evidence for the resolved research scope")
        return supported
    if "ibl_bwm" in tags:
        supported.append("public dataset reuse or dataset context")
    if "movement_body_state" in tags:
        supported.append("movement/body-state as confound or explanatory signal")
    if {"cp_region", "po_region", "lp_region"} & set(tags):
        supported.append("region-specific background that may later inform branch choices")
    if "geometry" in tags:
        supported.append("coding, representation, or population geometry")
    if "noise_shared_variability" in tags:
        supported.append("trial-to-trial covariability or shared variability geometry")
    if "analysis_method" in tags:
        supported.append("methodological shift or inference limit")
    if "multi_area" in tags:
        supported.append("multi-area coding or communication-like interpretation")
    if "temporal_dynamics" in tags:
        supported.append("latency, temporal evolution, or code dynamics")
    if "circuit_interpretation" in tags:
        supported.append("circuit-level interpretation within observational limits")
    if "generalization" in tags:
        supported.append("cross-session/lab generalization")
    if not supported and record.can_support_claims:
        # Domain-neutral. The neuroscience phrase this replaces was the DEFAULT, so on any dataset
        # whose text matched none of the tokens above it was written onto every usable card: 31 of
        # 59 on the 2026-08-19 climate packet.
        supported.append("background evidence for the resolved research scope")
    return supported


def _record_can_support_claim(record: TopicSourceRecord) -> bool:
    if _raw_topic_record_is_secondary_or_off_topic(record):
        return False
    return _snippet_kind(record) not in {
        TopicSourceSnippetKind.TITLE_ONLY,
        TopicSourceSnippetKind.METADATA,
    }


def _local_open_tensions(source_table: TopicSourceTable) -> list[str]:
    return []


def _topic_record_dedupe_key(record: TopicSourceRecord) -> str:
    if record.doi:
        return f"doi:{record.doi.lower()}"
    if record.pmid:
        return f"pmid:{record.pmid}"
    if record.openalex_id:
        return f"openalex:{record.openalex_id.lower()}"
    if record.semantic_scholar_id:
        return f"semantic_scholar:{record.semantic_scholar_id.lower()}"
    return f"title:{' '.join(record.title.lower().split())}:{record.year or ''}"


def _topic_brief_serious_import_errors(
    item: TopicEvidenceBriefReviewItem,
    decision: TopicEvidenceBriefReviewDecision,
) -> list[str]:
    errors: list[str] = []
    if item.prompt_version != TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION:
        errors.append(
            "TopicEvidenceBrief review pack uses stale prompt version: "
            f"{item.prompt_version or 'unknown'}"
        )
    gate = gate_topic_evidence_review_item(
        item,
        waived_request_ids=set(decision.evidence_request_waivers),
    )
    if gate.status in {ArtifactGateStatus.BLOCKED, ArtifactGateStatus.FIXTURE_NOT_FOR_REVIEW}:
        errors.append(
            "TopicEvidenceBrief review item is not serious-importable: "
            f"{gate.status.value}; " + "; ".join(gate.reasons)
        )
    if item.provider_id.startswith("mock:"):
        errors.append("TopicEvidenceBrief serious import cannot accept mock-provider output")
    if not item.input_digest:
        errors.append("TopicEvidenceBrief serious import requires input_digest")
    if not item.source_table_digest:
        errors.append("TopicEvidenceBrief serious import requires source_table_digest")
    if item.field_state_draft is None:
        errors.append("TopicEvidenceBrief serious import requires TopicFieldStateDraft")
    elif item.field_state_draft.prompt_version != TOPIC_FIELD_STATE_SYNTHESIZER_PROMPT_VERSION:
        errors.append(
            "TopicFieldStateDraft uses stale prompt version: "
            f"{item.field_state_draft.prompt_version or 'unknown'}"
        )
    waived = set(decision.evidence_request_waivers)
    unresolved_blocking = [
        request.request_id
        for request in item.evidence_requests
        if request.blocking and request.request_id not in waived
    ]
    if unresolved_blocking:
        errors.append(
            "TopicEvidenceBrief has unresolved blocking evidence requests: "
            + ", ".join(unresolved_blocking)
        )
    if item.r5_source_table is None:
        errors.append("TopicEvidenceBrief serious import requires R5 lane source table")
        return errors
    record_by_id = {record.source_record_id: record for record in item.r5_source_table.records}
    for claim in item.recommended_brief.claims:
        source_ids = claim.source_record_ids or claim.source_refs
        if not source_ids:
            errors.append(f"TopicEvidenceBrief claim lacks source IDs: {claim.claim_id}")
            continue
        for source_id in source_ids:
            record = record_by_id.get(source_id)
            if record is None:
                errors.append(
                    f"TopicEvidenceBrief claim {claim.claim_id} cites unknown source: {source_id}"
                )
            elif not record.can_support_claims:
                errors.append(
                    f"TopicEvidenceBrief claim {claim.claim_id} uses title/metadata-only source: "
                    f"{source_id}"
                )
    if not item.recommended_brief.unresolved_tensions:
        errors.append("TopicEvidenceBrief expert import requires literature-derived tensions")
    return errors


def _render_context_evidence_requests(
    requests: list[R5ContextEvidenceRequest],
) -> list[str]:
    if not requests:
        return ["- No unresolved evidence requests."]
    lines: list[str] = []
    for request in requests:
        marker = "blocking" if request.blocking else "non-blocking"
        target = (
            request.target_lane or request.target_source_record_id or request.target_dataset_field
        )
        target_text = f" target `{target}`;" if target else ""
        lines.append(
            f"- `{request.request_id}` [{request.kind.value}; {marker};{target_text}] "
            f"{request.description}"
        )
    return lines


def _render_field_state_section(section: TopicFieldStateSection | None) -> str:
    if section is None:
        return "- Missing section from field-state draft."
    sources = ", ".join(f"`{source_id}`" for source_id in section.source_record_ids)
    source_line = f"\n\nSources: {sources}" if sources else "\n\nSources: none cited"
    return section.synthesis.strip() + source_line


def _render_topic_claim_clusters(item: TopicEvidenceBriefReviewItem) -> list[str]:
    if not item.recommended_brief.claims:
        return ["- No recommended claims yet; field-state synthesis should explain why."]
    card_by_id = {card.source_record_id: card for card in item.source_evidence_cards}
    lines: list[str] = []
    for claim in item.recommended_brief.claims:
        source_ids = claim.source_record_ids or claim.source_refs
        lines.append(f"### `{claim.claim_id}` [{claim.status.value}; {claim.origin.value}]")
        lines.extend(["", claim.claim, ""])
        for source_id in source_ids:
            card = card_by_id.get(source_id)
            if card is None:
                lines.append(f"- `{source_id}`: source card missing")
                continue
            flags = ", ".join(card.quality_flags) if card.quality_flags else "none"
            validity = (
                "INVALID SUPPORT - not proposer-visible"
                if not card.can_support_claims
                else "valid for review"
            )
            lines.append(
                f"- `{source_id}` ({card.year or 'n.d.'}; {', '.join(card.lane_ids)}): "
                f"{card.key_contribution[:260]} "
                f"[{validity}; claim-supporting: {card.can_support_claims}; flags: {flags}]"
            )
        lines.append("")
    return lines


def _render_close_prior_assessments(item: TopicEvidenceBriefReviewItem) -> list[str]:
    values = item.recommended_brief.questions_already_answered
    if not values:
        return [
            "- No close-prior/already-answered item was accepted into the recommended brief. "
            "Reviewer should check whether this is a real gap or a retrieval weakness."
        ]
    return [
        f"- {value} Review whether a future QuestionSeed would be redundant with this prior."
        for value in values
    ]


def _render_open_gap_opportunities(item: TopicEvidenceBriefReviewItem) -> list[str]:
    gate = gate_topic_evidence_review_item(item)
    if not gate.is_reviewable:
        draft_values = item.recommended_brief.unresolved_tensions
        field_state_gap_sections = []
        if item.field_state_draft is not None:
            field_state_gap_sections = [
                section
                for section in item.field_state_draft.sections
                if "gap" in section.heading.lower() or "tension" in section.heading.lower()
            ]
        lines = [
            "- Accepted/exportable open gaps: 0",
            f"- Draft blocked gap candidates: {len(draft_values) + len(field_state_gap_sections)}",
            "- Rejected gap candidates: 0",
            "",
            "### Draft Blocked Gap Candidates For Repair",
            "",
        ]
        if not draft_values and not field_state_gap_sections:
            lines.append("- No draft gap candidates were produced.")
            return lines
        lines.extend([f"- Recommended brief draft tension: {value}" for value in draft_values])
        lines.extend(
            [
                f"- Field-state `{section.heading}`: {section.synthesis}"
                for section in field_state_gap_sections
            ]
        )
        return lines
    values = item.recommended_brief.unresolved_tensions
    if not values:
        return ["- No unresolved tension recorded; this should block serious import."]
    return [
        f"- {value} Potential QuestionSeed opportunity only if it can discriminate alternatives "
        "without relying on target dataset feasibility at proposal time."
        for value in values
    ]


def _render_gate_list(values: list[str], *, empty: str) -> list[str]:
    if not values:
        return [empty]
    return [f"- {value}" for value in values]


def _render_source_quality_diagnostics(item: TopicEvidenceBriefReviewItem) -> list[str]:
    diagnostics: list[str] = []
    if item.r5_source_table is not None:
        diagnostics.extend(item.r5_source_table.source_quality_flags)
    if item.field_state_draft is not None:
        diagnostics.extend(item.field_state_draft.source_quality_diagnostics)
    diagnostics.extend(item.auto_flags)
    if not diagnostics:
        return ["- No source-quality diagnostics."]
    return [f"- {flag}" for flag in _dedupe_strings(diagnostics)]


def _render_source_evidence_cards(cards: list[SourceEvidenceCard]) -> list[str]:
    if not cards:
        return ["- No source evidence cards."]
    lines: list[str] = []
    for card in cards:
        status = "included" if card.can_support_claims else f"excluded:{card.exclusion_reason}"
        identifiers = _card_identifier_text(card)
        lines.extend(
            [
                f"### `{card.source_record_id}`",
                "",
                f"- Title: {card.title}",
                f"- Year: {card.year or 'unknown'}",
                f"- IDs/URL: {identifiers or 'none recorded'}",
                f"- Lanes: {', '.join(card.lane_ids) or 'unassigned'}",
                f"- Subfield tags: {', '.join(card.subfield_tags) or 'none'}",
                f"- Synthesis status: {status}",
                *(
                    [
                        "- Rights warning: full-text rights were not verified; the fetched text "
                        + (
                            "is excluded. The retained original abstract/provider snippet is used "
                            "for scientific claim support and proposer export at abstract authority."
                            if "fulltext_fallback_used" in card.quality_flags
                            else "is excluded from scientific claim support and proposer export."
                        )
                    ]
                    if "fulltext_rights_unverified" in card.quality_flags
                    else []
                ),
                f"- Why included: {card.why_included}",
                f"- Claims/gaps supported: {'; '.join(card.claims_or_gaps_supported) or 'none'}",
                "- Key contribution/excerpt:",
                "",
                _indent_block(
                    card.key_contribution or card.abstract_or_excerpt or "[missing]", "  "
                ),
                "",
            ]
        )
    return lines


def _card_identifier_text(card: SourceEvidenceCard) -> str:
    identifiers = [
        ("doi", card.doi),
        ("pmid", card.pmid),
        ("openalex", card.openalex_id),
        ("semantic_scholar", card.semantic_scholar_id),
        ("url", card.url),
    ]
    return "; ".join(f"{label}: {value}" for label, value in identifiers if value)


def _render_lane_coverage(
    source_table: R5TopicEvidenceSourceTable | None,
) -> list[str]:
    if source_table is None:
        return ["- Missing topic source table."]
    lines = [
        f"- `{lane}`: {source_table.lane_coverage.get(lane, 0)} source(s)"
        for lane in sorted(source_table.lane_coverage)
    ]
    if not lines:
        lines.append("- No retrieval lineage recorded.")
    if source_table.source_quality_flags:
        lines.append("- Source quality flags: " + "; ".join(source_table.source_quality_flags))
    return lines


def _render_topic_evidence_group(
    group: TopicEvidenceGroup,
    source_table: R5TopicEvidenceSourceTable | None,
) -> str:
    if not group.source_record_ids:
        return f"- `{group.label}`: no substantive records"
    record_by_id = {
        record.source_record_id: record for record in (source_table.records if source_table else [])
    }
    details = []
    for source_id in group.source_record_ids:
        record = record_by_id.get(source_id)
        if record is None:
            details.append(f"`{source_id}`")
        else:
            details.append(f"`{source_id}` ({record.year or 'n.d.'}; {record.title})")
    return f"- `{group.label}`: " + "; ".join(details)


def _render_complete_topic_source_table(
    source_table: R5TopicEvidenceSourceTable | None,
) -> list[str]:
    if source_table is None:
        return ["- Missing topic source table."]
    lines: list[str] = []
    lineage_labels = sorted(
        set(source_table.lane_coverage)
        | {lane for record in source_table.records for lane in record.lane_ids}
    )
    records_by_lane: dict[str, list[R5TopicSourceRecordEvidence]] = {
        lane: [] for lane in lineage_labels
    }
    unassigned: list[R5TopicSourceRecordEvidence] = []
    for record in source_table.records:
        assigned = False
        for lane in record.lane_ids:
            if lane in records_by_lane:
                records_by_lane[lane].append(record)
                assigned = True
        if not assigned:
            unassigned.append(record)
    for lane in lineage_labels:
        records = records_by_lane[lane]
        lines.extend([f"#### `{lane}`", ""])
        if not records:
            lines.extend(["- No source records retained for this lane.", ""])
            continue
        for record in records:
            lines.extend(_render_topic_source_record(record))
        lines.append("")
    if unassigned:
        lines.extend(["#### `unassigned`", ""])
        for record in unassigned:
            lines.extend(_render_topic_source_record(record))
        lines.append("")
    return lines


def _render_topic_source_record(record: R5TopicSourceRecordEvidence) -> list[str]:
    authority_text, authority_kind = rights_safe_source_text_and_kind(record)
    rights_unverified = (
        record.snippet_kind == TopicSourceSnippetKind.FULLTEXT_EXCERPT
        and not fulltext_rights_are_verified(record)
    )
    fallback_used = rights_unverified and authority_kind in {
        TopicSourceSnippetKind.ABSTRACT,
        TopicSourceSnippetKind.PROVIDER_SNIPPET,
    }
    identifiers = _topic_record_identifier_text(record)
    can_support = "yes" if record.can_support_claims else "no"
    display_flags = [
        *record.source_quality_flags,
        *(["fulltext_rights_unverified"] if rights_unverified else []),
        *(["fulltext_fallback_used"] if fallback_used else []),
    ]
    flags = ", ".join(display_flags) if display_flags else "none"
    displayed_kind = authority_kind.value if authority_kind is not None else "metadata"
    lines = [
        f"- Source record: `{record.source_record_id}`",
        f"  - Title: {record.title}",
        f"  - Year: {record.year or 'unknown'}",
        f"  - IDs/URL: {identifiers or 'none recorded'}",
        f"  - Lanes: {', '.join(record.lane_ids) or 'unassigned'}",
        f"  - Query IDs: {', '.join(record.query_ids)}",
        (
            "  - Evidence status: "
            f"{record.abstract_status.value}; usable snippet kind `{displayed_kind}`; "
            f"can support claims: {can_support}; flags: {flags}"
        ),
        f"  - Ranking features: {_format_ranking_features(record.ranking_features)}",
        "  - Abstract/snippet:",
        "",
        _indent_block(authority_text or "[missing rights-safe abstract/snippet]", "    "),
        "",
    ]
    return lines


def _render_topic_claims(item: TopicEvidenceBriefReviewItem) -> list[str]:
    brief = item.recommended_brief
    if not brief.claims:
        return ["- No GPT-synthesized claims in this draft/recommended brief."]
    lines: list[str] = []
    for claim in brief.claims:
        lines.append(
            f"- `{claim.claim_id}` [{claim.status.value}; {claim.origin.value}; "
            f"confidence {claim.confidence:.2f}] {claim.claim} "
            f"(sources: {', '.join(claim.source_record_ids or claim.source_refs)})"
        )
    return lines


def _topic_record_identifier_text(record: R5TopicSourceRecordEvidence) -> str:
    identifiers = [
        ("doi", record.doi),
        ("pmid", record.pmid),
        ("openalex", record.openalex_id),
        ("semantic_scholar", record.semantic_scholar_id),
        ("url", record.url),
    ]
    return "; ".join(f"{label}: {value}" for label, value in identifiers if value)


def _format_ranking_features(features: dict[str, float]) -> str:
    if not features:
        return "none"
    return ", ".join(f"{key}={value:.3g}" for key, value in sorted(features.items()))


def _indent_block(text: str, prefix: str) -> str:
    return "\n".join(prefix + line if line else prefix.rstrip() for line in text.splitlines())


def _topic_bundle_flags(
    gpt_brief: TopicEvidenceBrief,
    source_table: TopicSourceTable,
    evidence_requests: list[R5ContextEvidenceRequest] | None = None,
) -> list[str]:
    flags: list[str] = []
    if not source_table.records:
        flags.append("topic_source_table_empty")
    if not gpt_brief.claims:
        flags.append("gpt_brief_missing_claims")
    uncited = [
        claim.claim_id
        for claim in gpt_brief.claims
        if not (claim.source_record_ids or claim.source_refs)
    ]
    if uncited:
        flags.append("gpt_claims_missing_source_ids:" + ",".join(uncited))
    typed_close_priors = [
        claim
        for claim in gpt_brief.claims
        if claim.status == TopicEvidenceClaimStatus.ALREADY_ANSWERED
    ]
    if gpt_brief.questions_already_answered and not typed_close_priors:
        flags.append("questions_already_answered_without_typed_close_prior_claim")
    if typed_close_priors and not gpt_brief.questions_already_answered:
        flags.append("typed_close_prior_claim_without_questions_already_answered_summary")
    blocking_requests = [
        request.request_id for request in (evidence_requests or []) if request.blocking
    ]
    if blocking_requests:
        flags.append("blocking_evidence_requests:" + ",".join(blocking_requests))
    return flags


def _claim_key(claim: TopicEvidenceClaim) -> str:
    return " ".join(claim.claim.lower().split())[:120]


def _load_prompt(prompt_version: str) -> str:
    return resolve_asset(Path("prompts") / Path(prompt_version).with_suffix(".md")).read_text(
        encoding="utf-8"
    )


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output


def project_questions_already_answered(claims: list[TopicEvidenceClaim]) -> list[str]:
    """Build the non-authoritative close-prior summary from authoritative typed claims.

    The model still authors every claim, status, source binding, rationale, and limitation. The
    host performs no semantic matching or reclassification here: it copies claim text verbatim only
    when the model's typed status is ``already_answered``. Historical artifacts are not rewritten
    on load; this function is used only while constructing fresh synthesis/revision candidates.
    """

    return _dedupe_strings(
        [
            claim.claim
            for claim in claims
            if claim.status == TopicEvidenceClaimStatus.ALREADY_ANSWERED
        ]
    )
