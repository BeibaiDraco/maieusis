from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..enums import ClaimLevel


class DatasetInspectionSourceType(StrEnum):
    DOCUMENTATION = "documentation"
    SCHEMA = "schema"
    METADATA_QUERY = "metadata_query"
    SAMPLE_INSPECTION = "sample_inspection"
    REPOSITORY_CODE = "repository_code"
    EXECUTOR_SKILL = "executor_skill"
    SYNTHETIC_PROBE = "synthetic_probe"


class DirectOrProxy(StrEnum):
    DIRECT = "direct"
    OPERATIONALIZED = "operationalized"
    PROXY = "proxy"


class DatasetInspectionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    branch_id: str
    requirement_id: str
    source_type: DatasetInspectionSourceType
    source_locator: str
    source_digest: str
    inspection_method: str
    finding: str
    scope: str
    limitations: list[str] = Field(default_factory=list)
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "evidence_id",
        "branch_id",
        "requirement_id",
        "source_locator",
        "inspection_method",
        "finding",
        "scope",
        "created_by",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DatasetInspectionEvidence core fields must be non-empty")
        return value


class ConstructOperationalization(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operationalization_id: str
    branch_id: str
    construct: str  # type: ignore[assignment]
    measurement: str
    dataset_bindings: list[str] = Field(default_factory=list)
    direct_or_proxy: DirectOrProxy
    event_or_time_reference: str
    population_scope: str
    validity_argument: str
    failure_modes: list[str] = Field(default_factory=list)
    alternatives_considered: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    owner_accepted: bool = False

    @model_validator(mode="after")
    def require_evidence_for_dataset_binding(self) -> ConstructOperationalization:
        if self.dataset_bindings and not self.evidence_ids:
            raise ValueError("dataset-bound operationalization requires evidence_ids")
        if not self.construct.strip() or not self.measurement.strip():
            raise ValueError("construct and measurement must be non-empty")
        return self


class PlanDataSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_source_id: str
    branch_id: str
    description: str
    expected_grain: str
    required_variables: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_evidence_for_variables(self) -> PlanDataSource:
        if self.required_variables and not self.evidence_ids:
            raise ValueError("PlanDataSource with required_variables requires evidence_ids")
        return self


class AnalysisPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analysis_plan_id: str
    branch_id: str
    question_version_id: str
    refined_question: str
    scientific_intent_invariant_id: str
    population_and_scope: str
    data_sources: list[PlanDataSource] = Field(default_factory=list)
    construct_operationalization_ids: list[str] = Field(default_factory=list)
    unit_of_observation: str
    unit_of_inference: str
    hierarchy_and_dependence: str
    analysis_strategy: list[str] = Field(default_factory=list)
    candidate_estimands: list[str] = Field(default_factory=list)
    validation_strategy: str
    split_strategy: str
    diagnostics: list[str] = Field(default_factory=list)
    negative_controls: list[str] = Field(default_factory=list)
    positive_controls: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    predicted_result_patterns: list[str] = Field(default_factory=list)
    claim_ceiling: ClaimLevel
    claim_ceiling_components: list[ClaimLevel] = Field(default_factory=list)
    interpretation_limits: list[str] = Field(default_factory=list)
    resource_estimate: str
    required_new_skills: list[str] = Field(default_factory=list)
    unresolved_decisions: list[str] = Field(default_factory=list)
    why_plan_serves_question: str
    evidence_ids: list[str] = Field(default_factory=list)
    contains_executable_code: Literal[False] = False

    @field_validator(
        "analysis_plan_id",
        "branch_id",
        "question_version_id",
        "refined_question",
        "scientific_intent_invariant_id",
        "unit_of_observation",
        "unit_of_inference",
        "validation_strategy",
        "split_strategy",
        "resource_estimate",
        "why_plan_serves_question",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("AnalysisPlan core fields must be non-empty")
        return value

    @model_validator(mode="after")
    def require_evidence_and_scientific_plan_detail(self) -> AnalysisPlan:
        if not self.evidence_ids:
            raise ValueError("AnalysisPlan requires evidence_ids for dataset-specific assertions")
        if not self.analysis_strategy:
            raise ValueError("AnalysisPlan requires analysis_strategy")
        if not self.alternative_explanations:
            raise ValueError("AnalysisPlan requires alternative_explanations")
        if len(self.claim_ceiling_components) != len(set(self.claim_ceiling_components)):
            raise ValueError("AnalysisPlan claim_ceiling_components must be unique")
        if (
            self.claim_ceiling_components
            and self.claim_ceiling not in self.claim_ceiling_components
        ):
            raise ValueError(
                "AnalysisPlan claim_ceiling must appear in non-empty claim_ceiling_components"
            )
        return self
