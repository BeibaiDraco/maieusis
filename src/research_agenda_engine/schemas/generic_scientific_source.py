from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DatasetGroundingLevel(StrEnum):
    UNKNOWN = "unknown"
    DOCUMENTATION_INVENTORY_ONLY = "documentation_inventory_only"
    SCHEMA_METADATA_INSPECTED = "schema_metadata_inspected"
    SAMPLE_INSPECTED = "sample_inspected"
    FULL_LOCAL_STRUCTURAL_AVAILABLE = "full_local_structural_available"

    @property
    def supports_serious_dataset_grounding(self) -> bool:
        return self in {
            DatasetGroundingLevel.SAMPLE_INSPECTED,
            DatasetGroundingLevel.FULL_LOCAL_STRUCTURAL_AVAILABLE,
        }


class DatasetClaimStatus(StrEnum):
    """Truth label for dataset statements, independent of planning-route eligibility."""

    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"


class QuestionFamilyScientificVariantSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    question: str
    scientific_tension: str
    why_scientifically_important: str
    variant_role: str
    distinction_axes: list[str] = Field(default_factory=list)
    distinct_from_siblings: str
    dataset_leverage_hypothesis: str
    competing_explanations: list[str] = Field(default_factory=list)
    discriminating_observation: str
    positive_result_consequence: str
    negative_result_consequence: str
    null_result_consequence: str
    ambiguous_constructs: list[str] = Field(default_factory=list)
    likely_implementation_challenges: list[str] = Field(default_factory=list)
    assumptions_about_dataset: list[str] = Field(default_factory=list)
    source_pattern_ids: list[str] = Field(default_factory=list)
    source_paper_case_ids: list[str] = Field(default_factory=list)
    source_variant_ids: list[str] = Field(default_factory=list)
    source_variant_digest: str

    @field_validator(
        "variant_id",
        "question_seed_id",
        "question",
        "scientific_tension",
        "why_scientifically_important",
        "variant_role",
        "distinct_from_siblings",
        "dataset_leverage_hypothesis",
        "discriminating_observation",
        "positive_result_consequence",
        "negative_result_consequence",
        "null_result_consequence",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("scientific source variant fields must be non-empty")
        return value

    @field_validator(
        "distinction_axes",
        "competing_explanations",
        "ambiguous_constructs",
        "likely_implementation_challenges",
        "assumptions_about_dataset",
        "source_pattern_ids",
        "source_paper_case_ids",
        "source_variant_ids",
    )
    @classmethod
    def clean_unique_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("scientific source variant list fields must be unique")
        return cleaned

    @field_validator("source_variant_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="scientific source variant digest")
        return value

    @model_validator(mode="after")
    def validate_variant_snapshot(self) -> QuestionFamilyScientificVariantSnapshot:
        if not self.distinction_axes:
            raise ValueError("scientific source variant requires distinction_axes")
        if len(self.competing_explanations) < 2:
            raise ValueError("scientific source variant requires competing_explanations")
        return self


class QuestionFamilyScientificSourceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_snapshot_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    family_title: str
    family_summary: str
    shared_scientific_tension: str
    semantic_axes: list[str] = Field(default_factory=list)
    non_mergeable_distinctions: list[str] = Field(default_factory=list)
    source_pattern_ids: list[str] = Field(default_factory=list)
    source_topic_claim_ids: list[str] = Field(default_factory=list)
    source_dataset_context_ids: list[str] = Field(default_factory=list)
    source_family_ids: list[str] = Field(default_factory=list)
    proposal_stage_uncertainties: list[str] = Field(default_factory=list)
    assumptions_about_dataset: list[str] = Field(default_factory=list)
    source_family_digest: str
    variants: list[QuestionFamilyScientificVariantSnapshot]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "source_snapshot_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "family_title",
        "family_summary",
        "shared_scientific_tension",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("scientific source snapshot fields must be non-empty")
        return value

    @field_validator(
        "semantic_axes",
        "non_mergeable_distinctions",
        "source_pattern_ids",
        "source_topic_claim_ids",
        "source_dataset_context_ids",
        "source_family_ids",
        "proposal_stage_uncertainties",
        "assumptions_about_dataset",
    )
    @classmethod
    def clean_unique_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("scientific source snapshot list fields must be unique")
        return cleaned

    @field_validator("source_family_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="scientific source family digest")
        return value

    @model_validator(mode="after")
    def validate_snapshot(self) -> QuestionFamilyScientificSourceSnapshot:
        if not self.variants:
            raise ValueError("scientific source snapshot requires variants")
        variant_ids = [variant.variant_id for variant in self.variants]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("scientific source snapshot variant IDs must be unique")
        seed_ids = [variant.question_seed_id for variant in self.variants]
        if len(seed_ids) != len(set(seed_ids)):
            raise ValueError("scientific source snapshot seed IDs must be unique")
        return self


def _validate_sha256(value: str, *, field_name: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be sha256 hex")
