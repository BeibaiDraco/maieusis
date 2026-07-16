from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .question_family_branch import QuestionFamilyBranchEventScope


class ConstructProbeMatchClass(StrEnum):
    EXACT = "exact"
    DATASET_ALIAS = "dataset_alias"
    PLAUSIBLE_PROXY = "plausible_proxy"
    AMBIGUOUS = "ambiguous"
    ABSENT = "absent"


class ConstructProbeMap(BaseModel):
    """Semantic mapping between a scientific construct and observed dataset terms."""

    model_config = ConfigDict(extra="forbid")

    construct_probe_id: str
    branch_id: str
    question_family_id: str
    scope: QuestionFamilyBranchEventScope
    variant_id: str = ""
    scientific_construct: str
    expected_semantic_neighborhood: list[str]
    observed_dataset_names: list[str] = Field(default_factory=list)
    checked_dataset_sources: list[str]
    match_class: ConstructProbeMatchClass
    evidence_ids: list[str]
    mapping_rationale: str
    uncertainty: str
    owner_review_needed: bool
    created_by: str = "dataset_planner"

    @field_validator(
        "construct_probe_id",
        "branch_id",
        "question_family_id",
        "scientific_construct",
        "mapping_rationale",
        "uncertainty",
        "created_by",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ConstructProbeMap text fields must be non-empty")
        return value

    @field_validator(
        "expected_semantic_neighborhood",
        "checked_dataset_sources",
        "evidence_ids",
    )
    @classmethod
    def require_non_empty_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("ConstructProbeMap list fields must be non-empty")
        return cleaned

    @field_validator("observed_dataset_names")
    @classmethod
    def clean_observed_dataset_names(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_probe_scope_and_match(self) -> ConstructProbeMap:
        if self.scope == QuestionFamilyBranchEventScope.VARIANT and not self.variant_id.strip():
            raise ValueError("variant-scoped construct probe map requires variant_id")
        if self.scope == QuestionFamilyBranchEventScope.FAMILY and self.variant_id.strip():
            raise ValueError("family-scoped construct probe map cannot carry variant_id")
        if self.match_class != ConstructProbeMatchClass.ABSENT and not self.observed_dataset_names:
            raise ValueError("non-absent construct probe maps require observed dataset names")
        if (
            self.match_class
            in {
                ConstructProbeMatchClass.PLAUSIBLE_PROXY,
                ConstructProbeMatchClass.AMBIGUOUS,
            }
            and not self.owner_review_needed
        ):
            raise ValueError("plausible_proxy and ambiguous mappings require owner review")
        if self.match_class == ConstructProbeMatchClass.ABSENT and not self.uncertainty.strip():
            raise ValueError("absent construct probe maps require uncertainty")
        return self
