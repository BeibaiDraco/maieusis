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
        assert_proposal_safe_payload(self.model_dump(mode="python"), context="DatasetNarrative")
        return self

    @property
    def is_proposal_ready(self) -> bool:
        return self.review_status in {
            DatasetNarrativeReviewStatus.SOURCE_VERIFIED,
            DatasetNarrativeReviewStatus.AUTOMATED_REVIEWED,
            DatasetNarrativeReviewStatus.EXPERT_REVIEWED,
        }
