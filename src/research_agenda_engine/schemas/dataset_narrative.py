from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ._r5_firewall import assert_proposal_safe_payload


class DatasetNarrativeSourceType(StrEnum):
    DATASET_PAPER = "dataset_paper"
    DATASET_DOCUMENTATION = "dataset_documentation"
    RELEASE_NOTE = "release_note"
    METADATA_SUMMARY = "metadata_summary"
    EXPERT_NOTE = "expert_note"


class DatasetNarrativeReviewStatus(StrEnum):
    DRAFT = "draft"
    SOURCE_VERIFIED = "source_verified"
    # An independent-AI fidelity reviewer (a provider distinct from every source generator) judged the
    # fused candidate and returned ACCEPT. This is the automated-default authority:
    # proposal-ready without a human import. EXPERT_REVIEWED stays reserved for the optional post-hoc
    # human override. Only the narrator promotion path may stamp this — never fusion, never a draft.
    AUTOMATED_REVIEWED = "automated_reviewed"
    EXPERT_REVIEWED = "expert_reviewed"


class DatasetNarrativeSourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_type: DatasetNarrativeSourceType
    locator: str
    title: str = ""
    section: str = ""
    page: int | None = None
    quote_or_span: str = ""
    source_digest: str = ""
    reviewed: bool = False

    @field_validator("source_id", "locator")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("source_id and locator must be non-empty")
        return value


# The scale-fact topic taxonomy every extractor call is handed, and the canonical form that fusion
# and the narrative guard resolve a model-authored ``quantity_kind`` back onto. Defined here beside
# the scale-fact model because this module is the leaf: ``coarse_dataset_facts`` imports from it.
SCALE_FACT_TOPICS: tuple[str, ...] = (
    "subjects or participants",
    "sessions or recordings if publicly stated",
    "trials or samples if publicly stated",
    "recording units, channels, or sensors",
    "measurement sites or regions",
    "task or experimental structure",
    "behavioral or auxiliary measurements",
    "public access mode and hierarchy",
)

_TOPIC_CONNECTIVES = frozenset(
    {"a", "an", "and", "if", "in", "of", "or", "per", "publicly", "stated", "the"}
)


def scale_fact_topic_tokens(text: str) -> frozenset[str]:
    """Content tokens of a phrase, folded to singular so a restatement matches its own topic.

    Grammatical number is folded because the topics are a CLOSED taxonomy every extractor call is
    handed: one recorded run wrote "trials or samples", another "Trial counts", and an unfolded
    intersection makes those different topics. Folding number on a closed list is mechanical
    normalization, which rule 11 permits; mapping distinct words onto each other would be a synonym
    table, which it does not, and none is built here.
    """

    cleaned = "".join(char if char.isalnum() else " " for char in text.lower())
    words = (word for word in cleaned.split() if word and word not in _TOPIC_CONNECTIVES)
    return frozenset(word[:-1] if len(word) > 3 and word.endswith("s") else word for word in words)


_TOPIC_TOKEN_INDEX: tuple[tuple[str, frozenset[str]], ...] = tuple(
    (topic, scale_fact_topic_tokens(topic)) for topic in SCALE_FACT_TOPICS
)


def canonical_scale_fact_topic(quantity_kind: str) -> str:
    """Resolve a model-authored ``quantity_kind`` back onto the taxonomy it was asked for.

    ``quantity_kind`` is a TAXONOMY field, not free wording: every extractor call is handed
    ``SCALE_FACT_TOPICS`` in its packet, but the prompt never pins the strings, so each call
    restates them its own way -- recorded runs wrote ``recording units``, ``recording_units`` and
    the listed ``recording units, channels, or sensors`` for one topic. Matching on shared content
    tokens recognises which listed topic a restatement came from. That is mechanical normalization
    of a closed taxonomy, not a synonym table: nothing here maps one vocabulary onto a different
    one, and an unrecognised kind keeps its own normalized tokens, so it resolves against itself
    and never collides with a listed topic.
    """
    tokens = scale_fact_topic_tokens(quantity_kind)
    if not tokens:
        return quantity_kind.strip().lower()
    best_topic = ""
    best_overlap = 0
    for topic, topic_tokens in _TOPIC_TOKEN_INDEX:
        overlap = len(tokens & topic_tokens)
        if overlap > best_overlap:
            best_topic, best_overlap = topic, overlap
    return best_topic if best_overlap else " ".join(sorted(tokens))


class DatasetNarrativeScaleFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scale_fact_id: str
    quantity_kind: str
    value_text: str
    precision: str = "source_reported"
    source_ids: list[str] = Field(default_factory=list)
    quote_or_span: str = ""
    proposal_safe: bool = True
    planner_stage_only: bool = False

    @field_validator("scale_fact_id", "quantity_kind", "value_text")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(
                "DatasetNarrativeScaleFact identifiers and value_text must be non-empty"
            )
        return value

    @model_validator(mode="after")
    def enforce_source_support_and_safety(self) -> DatasetNarrativeScaleFact:
        if self.proposal_safe and not self.source_ids:
            raise ValueError("proposal-safe DatasetNarrativeScaleFact requires source_ids")
        assert_proposal_safe_payload(
            self.model_dump(mode="python"), context="DatasetNarrativeScaleFact"
        )
        return self


def _assert_item_provenance_aligned(narrative: DatasetNarrative) -> None:
    """Per-item provenance must line up with the list it describes, or it attributes the wrong item.

    Index alignment is the whole contract: an off-by-one silently credits a source for a sentence it
    never wrote, which is the defect this field exists to remove, wearing a different hat.
    """

    for field_name, per_item in narrative.list_item_source_ids.items():
        values = getattr(narrative, field_name, None)
        if not isinstance(values, list):
            raise ValueError(
                f"DatasetNarrative list_item_source_ids names {field_name!r}, which is not a list field"
            )
        if len(per_item) != len(values):
            raise ValueError(
                f"DatasetNarrative list_item_source_ids[{field_name!r}] has {len(per_item)} entries "
                f"for {len(values)} items; per-item provenance is aligned by index"
            )


def _assert_scale_facts_resolved(scale_facts: list[DatasetNarrativeScaleFact]) -> None:
    """No scale-fact id is reused.

    This deliberately does NOT check that one SOURCE owns each quantity topic, though an earlier
    version did and it was wrong twice over. ``scale_facts[].source_ids`` holds EXCERPT ids, not feed
    identity: one source citing two of its own excerpts produced ``'user-doc:0:NOTES.md'`` and
    ``'user-doc:1:README.md'`` and was rejected as two sources, and this repository's own tracked
    ``corpus/context/dataset_narratives/ibl_bwm.dataset_narrative.yaml`` stopped loading because two
    sources CORROBORATE one figure from overlapping citation sets -- which excerpt ids cannot tell
    apart from a contradiction. The cross-source invariant is real; it belongs where feed identity is
    known, and is asserted in ``fusion.assert_scale_facts_resolved_across_feeds``.
    """

    ids = [fact.scale_fact_id for fact in scale_facts]
    repeated = sorted({value for value in ids if ids.count(value) > 1})
    if repeated:
        raise ValueError(f"DatasetNarrative scale_fact_id must be unique; repeated: {repeated}")


class DatasetNarrative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_narrative_id: str
    dataset_id: str
    title: str
    scientific_purpose: str
    population: str
    task_or_design: str
    modalities: list[str] = Field(default_factory=list)
    broad_scale: str = ""
    spatial_or_anatomical_coverage: str = ""
    temporal_structure: str = ""
    standardization: str = ""
    hierarchical_structure: list[str] = Field(default_factory=list)
    broad_interventions: list[str] = Field(default_factory=list)
    major_variables: list[str] = Field(default_factory=list)
    reuse_opportunities: list[str] = Field(default_factory=list)
    known_high_level_limitations: list[str] = Field(default_factory=list)
    scale_facts: list[DatasetNarrativeScaleFact] = Field(default_factory=list)
    field_evidence_source_ids: dict[str, list[str]] = Field(default_factory=dict)
    #: Per-ITEM provenance for the list fields: field name -> one source-id list per item, aligned
    #: by index. ``field_evidence_source_ids`` says which sources touched a FIELD, which is not the
    #: same claim and must not be stamped onto individual items -- doing so told the Question
    #: Scientist that two sources corroborated a card only one of them ever authored. Empty on a
    #: single-source narrative and on every artifact written before this field existed, so a reader
    #: falls back to the field-level list and no historical narrative is invalidated.
    list_item_source_ids: dict[str, list[list[str]]] = Field(default_factory=dict)
    source_refs: list[DatasetNarrativeSourceRef] = Field(default_factory=list)
    review_status: DatasetNarrativeReviewStatus = DatasetNarrativeReviewStatus.DRAFT
    prompt_version: str = ""
    provider_id: str = ""
    model_id: str = ""
    input_digest: str = ""
    source_packet_digest: str = ""
    dossier_digest: str = ""
    reviewed_at: datetime | None = None
    expert_reviewer: str = ""
    review_notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("dataset_narrative_id", "dataset_id", "title", "scientific_purpose")
    @classmethod
    def require_core_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DatasetNarrative core identifiers and purpose must be non-empty")
        return value

    @model_validator(mode="after")
    def require_sources_and_proposal_safety(self) -> DatasetNarrative:
        if self.review_status != DatasetNarrativeReviewStatus.DRAFT and not self.source_refs:
            raise ValueError(
                "source-verified or expert-reviewed DatasetNarrative requires source_refs"
            )
        _assert_scale_facts_resolved(self.scale_facts)
        _assert_item_provenance_aligned(self)
        assert_proposal_safe_payload(self.model_dump(mode="python"), context="DatasetNarrative")
        return self

    @property
    def is_proposal_ready(self) -> bool:
        return self.review_status in {
            DatasetNarrativeReviewStatus.SOURCE_VERIFIED,
            DatasetNarrativeReviewStatus.AUTOMATED_REVIEWED,
            DatasetNarrativeReviewStatus.EXPERT_REVIEWED,
        }
