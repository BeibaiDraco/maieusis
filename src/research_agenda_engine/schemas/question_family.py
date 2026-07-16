from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..provenance import stable_hash
from ._r5_firewall import assert_proposal_safe_payload
from .front_half_authority import FrontHalfAuthorityCeiling
from .planning_dialogue import BranchDecisionKind
from .question_seed import QuestionSeed


class QuestionFamilyVariantDistinctionAxis(StrEnum):
    THEORETICAL_TENSION = "theoretical_tension"
    TARGET_CONTRAST = "target_contrast"
    DISCRIMINATING_OBSERVATION = "discriminating_observation"
    CLAIM_LEVEL = "claim_level"
    POPULATION_SCOPE = "population_scope"
    OUTCOME_MEANING = "outcome_meaning"


class QuestionFamilyReviewStatus(StrEnum):
    SHORTLISTED = "shortlisted"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class QuestionFamilyVariantReviewStatus(StrEnum):
    ACTIVE = "active"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class QuestionFamilyGenerationReviewStatus(StrEnum):
    MODEL_GENERATED = "model_generated"
    # Independent-AI shortlist-worthiness gate accepted. Automated/non-human tier; the
    # automated shortlist path stamps THIS, never HUMAN_REVIEWED. See schemas/review_authority.py.
    AI_REVIEWED = "ai_reviewed"
    HUMAN_REVIEWED = "human_reviewed"
    REJECTED = "rejected"


class QuestionFamilyQualitySeverity(StrEnum):
    WARNING = "warning"
    BLOCKER = "blocker"


class QuestionFamilyQualityWarningKind(StrEnum):
    WEAK_VARIANT_DISTINCTION = "weak_variant_distinction"
    POSSIBLE_DUPLICATE_VARIANTS = "possible_duplicate_variants"
    MISSING_PROVENANCE = "missing_provenance"
    UNALLOWED_PROVENANCE = "unallowed_provenance"
    FIREWALL_CHECK = "firewall_check"


class QuestionFamilyConsolidationDispositionKind(StrEnum):
    KEPT = "kept"
    MERGED = "merged"
    MOVED = "moved"
    DROPPED_DUPLICATE = "dropped_duplicate"
    DEFERRED = "deferred"
    FLAGGED_UNCERTAIN = "flagged_uncertain"


class QuestionFamilyConsolidationFindingKind(StrEnum):
    SOURCE_COVERAGE = "source_coverage"
    MISSING_LINEAGE = "missing_lineage"
    FAMILY_COUNT = "family_count"
    FAMILY_BOUNDARY = "family_boundary"
    VARIANT_DISTINCTION = "variant_distinction"
    MOVEMENT_STATE_OVERPROMOTION = "movement_state_overpromotion"
    CLAIM_OVERREACH = "claim_overreach"
    FIREWALL_CHECK = "firewall_check"
    MODEL_REVIEW = "model_review"


class QuestionFamilyVariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    seed: QuestionSeed
    variant_role: str
    distinction_axes: list[QuestionFamilyVariantDistinctionAxis] = Field(default_factory=list)
    distinct_from_siblings: str
    # Compatibility/provenance only. Serious planning admission must not use
    # model-supplied branch_eligible as a dataset-feasibility gate.
    branch_eligible: bool = True
    source_variant_ids: list[str] = Field(default_factory=list)

    @field_validator("variant_id", "question_seed_id", "variant_role", "distinct_from_siblings")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionFamilyVariant text fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_variant_distinction(self) -> QuestionFamilyVariant:
        if self.question_seed_id != self.seed.question_seed_id:
            raise ValueError("QuestionFamilyVariant question_seed_id must match seed")
        if not self.distinction_axes:
            raise ValueError("QuestionFamilyVariant requires distinction_axes")
        if len(self.source_variant_ids) != len(set(self.source_variant_ids)):
            raise ValueError("QuestionFamilyVariant source_variant_ids must be unique")
        assert_proposal_safe_payload(
            self.model_dump(mode="python"),
            context="QuestionFamilyVariant",
        )
        return self


class QuestionFamily(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_family_id: str
    title: str
    summary: str
    shared_scientific_tension: str
    variants: list[QuestionFamilyVariant] = Field(default_factory=list)
    semantic_axes: list[str] = Field(default_factory=list)
    non_mergeable_distinctions: list[str] = Field(default_factory=list)
    source_pattern_ids: list[str] = Field(default_factory=list)
    source_topic_claim_ids: list[str] = Field(default_factory=list)
    source_topic_pack_ids: list[str] = Field(default_factory=list)
    source_dataset_context_ids: list[str] = Field(default_factory=list)
    source_family_ids: list[str] = Field(default_factory=list)
    proposal_stage_uncertainties: list[str] = Field(default_factory=list)
    assumptions_about_dataset: list[str] = Field(default_factory=list)
    context_id: str
    origin_provider_id: str
    prompt_version: str
    review_status: QuestionFamilyGenerationReviewStatus = (
        QuestionFamilyGenerationReviewStatus.MODEL_GENERATED
    )
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED

    @field_validator(
        "question_family_id",
        "title",
        "summary",
        "shared_scientific_tension",
        "context_id",
        "origin_provider_id",
        "prompt_version",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionFamily core text fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_family(self) -> QuestionFamily:
        if not self.variants:
            raise ValueError("QuestionFamily requires variants")
        variant_ids = [variant.variant_id for variant in self.variants]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("QuestionFamily contains duplicate variant_id values")
        seed_ids = [variant.seed.question_seed_id for variant in self.variants]
        if len(seed_ids) != len(set(seed_ids)):
            raise ValueError("QuestionFamily contains duplicate question_seed_id values")
        if {variant.seed.context_id for variant in self.variants} != {self.context_id}:
            raise ValueError("QuestionFamily variants must share context_id")
        if {variant.seed.origin_provider_id for variant in self.variants} != {
            self.origin_provider_id
        }:
            raise ValueError("QuestionFamily variants must share origin_provider_id")
        if {variant.seed.prompt_version for variant in self.variants} != {self.prompt_version}:
            raise ValueError("QuestionFamily variants must share prompt_version")
        if len(self.variants) > 1 and not self.non_mergeable_distinctions:
            raise ValueError("multi-variant QuestionFamily requires non_mergeable_distinctions")
        if len(self.source_family_ids) != len(set(self.source_family_ids)):
            raise ValueError("QuestionFamily source_family_ids must be unique")
        if len(self.source_topic_pack_ids) != len(set(self.source_topic_pack_ids)):
            raise ValueError("QuestionFamily source_topic_pack_ids must be unique")
        if (
            self.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
            and not self.source_topic_pack_ids
        ):
            raise ValueError("provisional QuestionFamily requires source_topic_pack_ids")
        if not self.source_pattern_ids:
            variant_pattern_ids = {
                pattern_id
                for variant in self.variants
                for pattern_id in variant.seed.source_pattern_ids
            }
            if not variant_pattern_ids:
                raise ValueError("QuestionFamily requires source_pattern_ids")
            self.source_pattern_ids = sorted(variant_pattern_ids)
        assert_proposal_safe_payload(self.model_dump(mode="python"), context="QuestionFamily")
        return self


class QuestionFamilyBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str
    context_id: str
    context_digest: str
    input_digest: str
    families: list[QuestionFamily] = Field(default_factory=list)
    origin_provider_id: str
    prompt_version: str
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED

    @model_validator(mode="after")
    def validate_batch_identity(self) -> QuestionFamilyBatch:
        if not self.families:
            raise ValueError("QuestionFamilyBatch requires families")
        family_ids = [family.question_family_id for family in self.families]
        if len(family_ids) != len(set(family_ids)):
            raise ValueError("QuestionFamilyBatch contains duplicate question_family_id values")
        variant_seed_ids = [
            variant.seed.question_seed_id for family in self.families for variant in family.variants
        ]
        if len(variant_seed_ids) != len(set(variant_seed_ids)):
            raise ValueError("QuestionFamilyBatch contains duplicate variant seed IDs")
        variant_ids = [
            variant.variant_id for family in self.families for variant in family.variants
        ]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("QuestionFamilyBatch contains duplicate variant IDs")
        if {family.context_id for family in self.families} != {self.context_id}:
            raise ValueError("QuestionFamilyBatch families must share context_id")
        if {family.origin_provider_id for family in self.families} != {self.origin_provider_id}:
            raise ValueError("QuestionFamilyBatch families must share origin_provider_id")
        if {family.prompt_version for family in self.families} != {self.prompt_version}:
            raise ValueError("QuestionFamilyBatch families must share prompt_version")
        if {family.authority_ceiling for family in self.families} != {self.authority_ceiling}:
            raise ValueError("QuestionFamilyBatch families must share authority_ceiling")
        return self


def question_family_batch_content_digest(batch: QuestionFamilyBatch) -> str:
    return stable_hash(_drop_empty_consolidation_lineage(batch.model_dump(mode="json")))


def _drop_empty_consolidation_lineage(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _drop_empty_consolidation_lineage(child)
            for key, child in value.items()
            if not (
                key in {"source_family_ids", "source_variant_ids"}
                and isinstance(child, list)
                and not child
            )
            and not (
                (key == "authority_ceiling" and child == FrontHalfAuthorityCeiling.VERIFIED.value)
                or (key == "source_topic_pack_ids" and child == [])
            )
        }
    if isinstance(value, list):
        return [_drop_empty_consolidation_lineage(child) for child in value]
    return value


class QuestionFamilyQualityWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warning_id: str
    severity: QuestionFamilyQualitySeverity
    kind: QuestionFamilyQualityWarningKind
    message: str
    question_family_id: str = ""
    variant_ids: list[str] = Field(default_factory=list)


class QuestionFamilyQualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quality_report_id: str
    batch_id: str
    context_id: str
    context_digest: str
    batch_input_digest: str
    batch_content_digest: str
    origin_provider_id: str
    model_id: str
    prompt_version: str
    provenance_allowlist_digest: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    warnings: list[QuestionFamilyQualityWarning] = Field(default_factory=list)
    passed_firewall: bool = True

    @field_validator(
        "quality_report_id",
        "batch_id",
        "context_id",
        "context_digest",
        "batch_input_digest",
        "batch_content_digest",
        "origin_provider_id",
        "model_id",
        "prompt_version",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionFamilyQualityReport identity fields must be non-empty")
        return value

    @field_validator(
        "context_digest",
        "batch_input_digest",
        "batch_content_digest",
        "provenance_allowlist_digest",
    )
    @classmethod
    def validate_digest(cls, value: str) -> str:
        if value and (len(value) != 64 or any(char not in "0123456789abcdef" for char in value)):
            raise ValueError("QuestionFamilyQualityReport digest fields must be sha256 hex")
        return value

    @property
    def blocker_count(self) -> int:
        return sum(
            1
            for warning in self.warnings
            if warning.severity == QuestionFamilyQualitySeverity.BLOCKER
        )

    @model_validator(mode="after")
    def validate_firewall_flag(self) -> QuestionFamilyQualityReport:
        has_firewall_blocker = any(
            warning.kind == QuestionFamilyQualityWarningKind.FIREWALL_CHECK
            and warning.severity == QuestionFamilyQualitySeverity.BLOCKER
            for warning in self.warnings
        )
        if self.passed_firewall == has_firewall_blocker:
            raise ValueError(
                "QuestionFamilyQualityReport passed_firewall does not match firewall warnings"
            )
        return self


class QuestionFamilyProposerBranch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposer_branch_id: str
    context_id: str
    context_digest: str
    context_subset_digest: str
    selected_pattern_ids: list[str] = Field(default_factory=list)
    selected_source_paper_case_ids: list[str] = Field(default_factory=list)
    family_count_requested: int = Field(ge=1, le=20)
    variants_per_family: int = Field(ge=1, le=8)
    batch_id: str
    batch_path: str
    quality_report_id: str
    quality_report_path: str
    origin_provider_id: str
    prompt_version: str
    input_digest: str


class QuestionFamilyEnsembleManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ensemble_id: str
    context_id: str
    context_digest: str
    prompt_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    proposer_branches: list[QuestionFamilyProposerBranch] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ensemble_manifest(self) -> QuestionFamilyEnsembleManifest:
        if len(self.proposer_branches) < 3:
            raise ValueError("QuestionFamilyEnsembleManifest requires at least 3 branches")
        subset_digests = [branch.context_subset_digest for branch in self.proposer_branches]
        if len(subset_digests) != len(set(subset_digests)):
            raise ValueError("family ensemble branches require distinct context subsets")
        if {branch.context_id for branch in self.proposer_branches} != {self.context_id}:
            raise ValueError("family ensemble branches must share context_id")
        return self


class QuestionFamilyReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_item_id: str
    family: QuestionFamily
    source_batch_id: str
    proposer_branch_id: str = ""
    input_digest: str = ""
    context_subset_digest: str = ""
    origin_provider_id: str = ""
    model_id: str = ""
    prompt_version: str = ""
    quality_warning_ids: list[str] = Field(default_factory=list)
    auto_flags: list[str] = Field(default_factory=list)


class QuestionFamilyReviewPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: str
    context_id: str
    context_digest: str
    source_batch_ids: list[str] = Field(default_factory=list)
    source_ensemble_id: str = ""
    blind_review: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    quality_reports: list[QuestionFamilyQualityReport] = Field(default_factory=list)
    items: list[QuestionFamilyReviewItem] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    source_consolidation_plan_id: str = ""
    source_consolidation_review_report_id: str = ""
    consolidation_blocker_count: int = Field(default=0, ge=0)
    consolidation_warning_summaries: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_review_pack(self) -> QuestionFamilyReviewPack:
        if self.source_consolidation_plan_id and self.consolidation_blocker_count:
            raise ValueError("QuestionFamilyReviewPack cannot use blocked consolidation output")
        if len(self.consolidation_warning_summaries) != len(
            set(self.consolidation_warning_summaries)
        ):
            raise ValueError("QuestionFamilyReviewPack duplicate consolidation warnings")
        family_ids = [item.family.question_family_id for item in self.items]
        if not family_ids:
            raise ValueError("QuestionFamilyReviewPack requires review items")
        if not self.source_batch_ids:
            raise ValueError("QuestionFamilyReviewPack requires source_batch_ids")
        if len(self.source_batch_ids) != len(set(self.source_batch_ids)):
            raise ValueError("QuestionFamilyReviewPack contains duplicate source_batch_ids")
        if len(family_ids) != len(set(family_ids)):
            raise ValueError("QuestionFamilyReviewPack contains duplicate family IDs")
        if {item.family.context_id for item in self.items} != {self.context_id}:
            raise ValueError("QuestionFamilyReviewPack items must share context_id")
        item_batch_ids = [item.source_batch_id for item in self.items]
        if any(not batch_id.strip() for batch_id in item_batch_ids):
            raise ValueError("QuestionFamilyReviewPack items require source_batch_id")
        if set(item_batch_ids) != set(self.source_batch_ids):
            raise ValueError(
                "QuestionFamilyReviewPack source batches must match review item batches"
            )
        report_by_batch = {report.batch_id: report for report in self.quality_reports}
        if len(report_by_batch) != len(self.quality_reports):
            raise ValueError("QuestionFamilyReviewPack contains duplicate quality reports")
        if set(report_by_batch) != set(self.source_batch_ids):
            raise ValueError("QuestionFamilyReviewPack requires one quality report per batch")
        if {report.context_id for report in self.quality_reports} != {self.context_id}:
            raise ValueError("QuestionFamilyReviewPack quality reports must share context_id")
        if {report.context_digest for report in self.quality_reports} != {self.context_digest}:
            raise ValueError("QuestionFamilyReviewPack quality reports must share context_digest")
        missing_allowlists = sorted(
            report.batch_id
            for report in self.quality_reports
            if not report.provenance_allowlist_digest
        )
        if missing_allowlists:
            raise ValueError(
                "QuestionFamilyReviewPack requires allowlist-bound quality reports: "
                + ", ".join(missing_allowlists)
            )
        for batch_id in self.source_batch_ids:
            report = report_by_batch[batch_id]
            batch_items = [item for item in self.items if item.source_batch_id == batch_id]
            input_digests = {item.input_digest for item in batch_items}
            provider_ids = {item.origin_provider_id for item in batch_items}
            model_ids = {item.model_id for item in batch_items}
            prompt_versions = {item.prompt_version for item in batch_items}
            if input_digests != {report.batch_input_digest}:
                raise ValueError("QuestionFamilyReviewPack item input digests mismatch report")
            if provider_ids != {report.origin_provider_id}:
                raise ValueError("QuestionFamilyReviewPack item providers mismatch report")
            if model_ids != {report.model_id}:
                raise ValueError("QuestionFamilyReviewPack item models mismatch report")
            if prompt_versions != {report.prompt_version}:
                raise ValueError("QuestionFamilyReviewPack item prompts mismatch report")
            reconstructed = QuestionFamilyBatch(
                batch_id=batch_id,
                context_id=self.context_id,
                context_digest=self.context_digest,
                input_digest=report.batch_input_digest,
                families=[item.family for item in batch_items],
                origin_provider_id=report.origin_provider_id,
                prompt_version=report.prompt_version,
            )
            if report.batch_content_digest != question_family_batch_content_digest(reconstructed):
                raise ValueError("QuestionFamilyReviewPack quality report content digest mismatch")
        blocked = sorted(
            report.batch_id
            for report in self.quality_reports
            if report.blocker_count or not report.passed_firewall
        )
        if blocked:
            raise ValueError(
                "QuestionFamilyReviewPack cannot include blocked quality reports: "
                + ", ".join(blocked)
            )
        return self


class QuestionFamilySourceFamilyDisposition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_family_id: str
    disposition: QuestionFamilyConsolidationDispositionKind
    target_family_ids: list[str] = Field(default_factory=list)
    rationale: str

    @model_validator(mode="after")
    def validate_family_disposition(self) -> QuestionFamilySourceFamilyDisposition:
        if not self.source_family_id.strip():
            raise ValueError("source_family_id must be non-empty")
        if not self.rationale.strip():
            raise ValueError("family disposition requires rationale")
        if len(self.target_family_ids) != len(set(self.target_family_ids)):
            raise ValueError("family disposition target_family_ids must be unique")
        if (
            self.disposition
            in {
                QuestionFamilyConsolidationDispositionKind.KEPT,
                QuestionFamilyConsolidationDispositionKind.MERGED,
                QuestionFamilyConsolidationDispositionKind.MOVED,
                QuestionFamilyConsolidationDispositionKind.FLAGGED_UNCERTAIN,
            }
            and not self.target_family_ids
        ):
            raise ValueError("kept/merged/moved/flagged family disposition requires target")
        if (
            self.disposition
            in {
                QuestionFamilyConsolidationDispositionKind.DROPPED_DUPLICATE,
                QuestionFamilyConsolidationDispositionKind.DEFERRED,
            }
            and self.target_family_ids
        ):
            raise ValueError("dropped/deferred family disposition cannot have targets")
        return self


class QuestionFamilySourceVariantDisposition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_family_id: str
    source_variant_id: str
    source_question_seed_id: str
    disposition: QuestionFamilyConsolidationDispositionKind
    target_family_id: str = ""
    target_variant_id: str = ""
    rationale: str

    @model_validator(mode="after")
    def validate_variant_disposition(self) -> QuestionFamilySourceVariantDisposition:
        for field_name in ("source_family_id", "source_variant_id", "source_question_seed_id"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must be non-empty")
        if not self.rationale.strip():
            raise ValueError("variant disposition requires rationale")
        needs_target = {
            QuestionFamilyConsolidationDispositionKind.KEPT,
            QuestionFamilyConsolidationDispositionKind.MERGED,
            QuestionFamilyConsolidationDispositionKind.MOVED,
            QuestionFamilyConsolidationDispositionKind.FLAGGED_UNCERTAIN,
        }
        if self.disposition in needs_target and not (
            self.target_family_id.strip() and self.target_variant_id.strip()
        ):
            raise ValueError("kept/merged/moved/flagged variant disposition requires target")
        if self.disposition in {
            QuestionFamilyConsolidationDispositionKind.DROPPED_DUPLICATE,
            QuestionFamilyConsolidationDispositionKind.DEFERRED,
        } and (self.target_family_id.strip() or self.target_variant_id.strip()):
            raise ValueError("dropped/deferred variant disposition cannot have targets")
        return self


class QuestionFamilyConsolidatedFamilyMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consolidated_family_id: str
    title: str
    primary_scientific_object: str
    primary_contrast: str
    source_family_ids: list[str] = Field(default_factory=list)
    source_variant_ids: list[str] = Field(default_factory=list)
    non_mergeable_with_other_families: list[str] = Field(default_factory=list)
    unresolved_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_family_map(self) -> QuestionFamilyConsolidatedFamilyMap:
        for field_name in (
            "consolidated_family_id",
            "title",
            "primary_scientific_object",
            "primary_contrast",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must be non-empty")
        if not self.source_family_ids:
            raise ValueError("consolidated family map requires source_family_ids")
        if not self.source_variant_ids:
            raise ValueError("consolidated family map requires source_variant_ids")
        if len(self.source_family_ids) != len(set(self.source_family_ids)):
            raise ValueError("consolidated family source_family_ids must be unique")
        if len(self.source_variant_ids) != len(set(self.source_variant_ids)):
            raise ValueError("consolidated family source_variant_ids must be unique")
        return self


class QuestionFamilyConsolidationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    source_review_pack_id: str
    source_context_id: str
    source_context_digest: str
    source_review_pack_digest: str
    source_review_markdown_digest: str = ""
    context_payload_digest: str
    origin_provider_id: str
    model_id: str
    prompt_version: str
    input_digest: str
    consolidated_batch_id: str
    target_family_count_min: int = Field(default=5, ge=1, le=20)
    target_family_count_max: int = Field(default=8, ge=1, le=20)
    source_family_ids: list[str] = Field(default_factory=list)
    source_variant_ids: list[str] = Field(default_factory=list)
    family_dispositions: list[QuestionFamilySourceFamilyDisposition] = Field(default_factory=list)
    variant_dispositions: list[QuestionFamilySourceVariantDisposition] = Field(default_factory=list)
    family_maps: list[QuestionFamilyConsolidatedFamilyMap] = Field(default_factory=list)
    unresolved_flags: list[str] = Field(default_factory=list)
    human_review_required: bool = True
    import_eligible: bool = False

    @field_validator(
        "source_context_digest",
        "source_review_pack_digest",
        "source_review_markdown_digest",
        "context_payload_digest",
        "input_digest",
    )
    @classmethod
    def validate_digest(cls, value: str) -> str:
        if value and (len(value) != 64 or any(char not in "0123456789abcdef" for char in value)):
            raise ValueError("QuestionFamilyConsolidationPlan digest fields must be sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_plan(self) -> QuestionFamilyConsolidationPlan:
        for field_name in (
            "plan_id",
            "source_review_pack_id",
            "source_context_id",
            "origin_provider_id",
            "model_id",
            "prompt_version",
            "consolidated_batch_id",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must be non-empty")
        if self.target_family_count_min > self.target_family_count_max:
            raise ValueError("target_family_count_min cannot exceed max")
        if not self.human_review_required:
            raise ValueError("QuestionFamily consolidation requires human review")
        if self.import_eligible:
            raise ValueError("QuestionFamilyConsolidationPlan itself is not import eligible")
        if len(self.source_family_ids) != len(set(self.source_family_ids)):
            raise ValueError("source_family_ids must be unique")
        if len(self.source_variant_ids) != len(set(self.source_variant_ids)):
            raise ValueError("source_variant_ids must be unique")
        if not self.source_family_ids or not self.source_variant_ids:
            raise ValueError("consolidation plan requires source families and variants")
        family_disposition_ids = [item.source_family_id for item in self.family_dispositions]
        if sorted(family_disposition_ids) != sorted(self.source_family_ids):
            raise ValueError("family dispositions must exactly cover source_family_ids")
        variant_disposition_ids = [item.source_variant_id for item in self.variant_dispositions]
        if sorted(variant_disposition_ids) != sorted(self.source_variant_ids):
            raise ValueError("variant dispositions must exactly cover source_variant_ids")
        map_ids = [item.consolidated_family_id for item in self.family_maps]
        if not map_ids:
            raise ValueError("consolidation plan requires family_maps")
        if len(map_ids) != len(set(map_ids)):
            raise ValueError("family_maps must have unique consolidated_family_id values")
        mapped_source_families = {
            source_id
            for family_map in self.family_maps
            for source_id in family_map.source_family_ids
        }
        unknown_families = sorted(mapped_source_families - set(self.source_family_ids))
        if unknown_families:
            raise ValueError(
                "family_maps cite unknown source families: " + ", ".join(unknown_families)
            )
        mapped_source_variants = {
            source_id
            for family_map in self.family_maps
            for source_id in family_map.source_variant_ids
        }
        unknown_variants = sorted(mapped_source_variants - set(self.source_variant_ids))
        if unknown_variants:
            raise ValueError(
                "family_maps cite unknown source variants: " + ", ".join(unknown_variants)
            )
        return self


class QuestionFamilyConsolidationFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str
    severity: QuestionFamilyQualitySeverity
    kind: QuestionFamilyConsolidationFindingKind
    message: str
    family_ids: list[str] = Field(default_factory=list)
    variant_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_finding(self) -> QuestionFamilyConsolidationFinding:
        if not self.finding_id.strip():
            raise ValueError("consolidation finding_id must be non-empty")
        if not self.message.strip():
            raise ValueError("consolidation finding requires message")
        return self


class QuestionFamilyConsolidationReviewReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    plan_id: str
    consolidated_batch_id: str
    reviewer_provider_id: str
    reviewer_model_id: str
    reviewer_independence_level: str = "unknown"
    prompt_version: str
    input_digest: str
    findings: list[QuestionFamilyConsolidationFinding] = Field(default_factory=list)
    passed: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("input_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        if value and (len(value) != 64 or any(char not in "0123456789abcdef" for char in value)):
            raise ValueError("QuestionFamilyConsolidationReviewReport digest must be sha256 hex")
        return value

    @property
    def blocker_count(self) -> int:
        return sum(
            1
            for finding in self.findings
            if finding.severity == QuestionFamilyQualitySeverity.BLOCKER
        )

    @model_validator(mode="after")
    def validate_report(self) -> QuestionFamilyConsolidationReviewReport:
        for field_name in (
            "report_id",
            "plan_id",
            "consolidated_batch_id",
            "reviewer_provider_id",
            "reviewer_model_id",
            "reviewer_independence_level",
            "prompt_version",
            "input_digest",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must be non-empty")
        allowed_independence_levels = {
            "deterministic",
            "different_provider",
            "same_provider_different_model",
            "same_provider_same_model",
            "unknown",
        }
        if self.reviewer_independence_level not in allowed_independence_levels:
            raise ValueError("invalid reviewer_independence_level")
        if self.passed == bool(self.blocker_count):
            raise ValueError("consolidation review passed flag does not match blockers")
        return self


class QuestionFamilyVariantReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    status: QuestionFamilyVariantReviewStatus = QuestionFamilyVariantReviewStatus.DEFERRED
    notes: str = ""
    required_changes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_variant_decision(self) -> QuestionFamilyVariantReviewDecision:
        if self.status == QuestionFamilyVariantReviewStatus.NEEDS_REVISION:
            if not self.required_changes:
                raise ValueError("needs_revision variant requires required_changes")
        elif self.required_changes:
            raise ValueError("required_changes are only allowed for needs_revision variants")
        if self.status != QuestionFamilyVariantReviewStatus.DEFERRED and not self.notes.strip():
            raise ValueError("reviewed variant decision requires notes")
        return self


class QuestionFamilyReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_item_id: str
    question_family_id: str
    status: QuestionFamilyReviewStatus = QuestionFamilyReviewStatus.DEFERRED
    reviewer: str = ""
    notes: str = ""
    scientific_value_notes: str = ""
    priority: int | None = Field(default=None, ge=1)
    variant_decisions: list[QuestionFamilyVariantReviewDecision] = Field(default_factory=list)
    required_changes: list[str] = Field(default_factory=list)
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_family_decision(self) -> QuestionFamilyReviewDecision:
        variant_decisions_are_empty_placeholders = all(
            decision.status == QuestionFamilyVariantReviewStatus.DEFERRED
            and not decision.notes.strip()
            and not decision.required_changes
            for decision in self.variant_decisions
        )
        if (
            self.status == QuestionFamilyReviewStatus.DEFERRED
            and not self.reviewer.strip()
            and not self.notes.strip()
            and not self.scientific_value_notes.strip()
            and not self.required_changes
            and variant_decisions_are_empty_placeholders
        ):
            return self
        if not self.reviewer.strip():
            raise ValueError("QuestionFamily review decision requires reviewer")
        if not self.notes.strip():
            raise ValueError("QuestionFamily review decision requires notes")
        variant_ids = [decision.variant_id for decision in self.variant_decisions]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("QuestionFamily review contains duplicate variant decisions")
        if self.status == QuestionFamilyReviewStatus.SHORTLISTED:
            if not self.scientific_value_notes.strip():
                raise ValueError("shortlisted QuestionFamily requires scientific_value_notes")
            if not any(
                decision.status == QuestionFamilyVariantReviewStatus.ACTIVE
                for decision in self.variant_decisions
            ):
                raise ValueError("shortlisted QuestionFamily requires an active variant")
        if self.status == QuestionFamilyReviewStatus.NEEDS_REVISION and not (
            self.required_changes
            or any(
                decision.status == QuestionFamilyVariantReviewStatus.NEEDS_REVISION
                for decision in self.variant_decisions
            )
        ):
            raise ValueError("needs_revision QuestionFamily requires required_changes")
        if self.status != QuestionFamilyReviewStatus.NEEDS_REVISION and self.required_changes:
            raise ValueError("required_changes are only allowed for needs_revision families")
        if self.reviewed_at is None:
            self.reviewed_at = datetime.now(UTC)
        return self


class QuestionFamilyReviewDecisionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_batch_id: str
    pack_id: str
    expert_reviewer: str = ""
    decisions: list[QuestionFamilyReviewDecision] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_duplicate_decisions(self) -> QuestionFamilyReviewDecisionBatch:
        ids = [decision.question_family_id for decision in self.decisions]
        duplicates = sorted({family_id for family_id in ids if ids.count(family_id) > 1})
        if duplicates:
            raise ValueError(
                "QuestionFamilyReviewDecisionBatch contains duplicate decisions: "
                + ", ".join(duplicates)
            )
        return self


class ShortlistedQuestionFamily(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: QuestionFamily
    review: QuestionFamilyReviewDecision
    active_variant_ids: list[str] = Field(default_factory=list)
    source_batch_id: str

    @model_validator(mode="after")
    def validate_shortlisted_family(self) -> ShortlistedQuestionFamily:
        if self.review.status != QuestionFamilyReviewStatus.SHORTLISTED:
            raise ValueError("ShortlistedQuestionFamily requires a shortlisted review")
        if self.review.question_family_id != self.family.question_family_id:
            raise ValueError("ShortlistedQuestionFamily review references another family")
        if not self.active_variant_ids:
            raise ValueError("ShortlistedQuestionFamily requires active_variant_ids")
        if len(self.active_variant_ids) != len(set(self.active_variant_ids)):
            raise ValueError("ShortlistedQuestionFamily active_variant_ids must be unique")
        family_variant_by_id = {variant.variant_id: variant for variant in self.family.variants}
        unknown = sorted(set(self.active_variant_ids) - set(family_variant_by_id))
        if unknown:
            raise ValueError(
                "ShortlistedQuestionFamily active variants are not in family: " + ", ".join(unknown)
            )
        active_review_ids = {
            decision.variant_id
            for decision in self.review.variant_decisions
            if decision.status == QuestionFamilyVariantReviewStatus.ACTIVE
        }
        if set(self.active_variant_ids) != active_review_ids:
            raise ValueError(
                "ShortlistedQuestionFamily active variants must match ACTIVE review decisions"
            )
        return self


class QuestionFamilyShortlistManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shortlist_id: str
    pack_id: str
    context_id: str
    context_digest: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    shortlisted: list[ShortlistedQuestionFamily] = Field(default_factory=list)
    rejected_family_ids: list[str] = Field(default_factory=list)
    needs_revision_family_ids: list[str] = Field(default_factory=list)
    deferred_family_ids: list[str] = Field(default_factory=list)
    contract_eligible: bool = False
    execution_authorized: bool = False
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED
    planning_eligible: bool = True

    @model_validator(mode="after")
    def preserve_r5_boundary(self) -> QuestionFamilyShortlistManifest:
        if self.contract_eligible or self.execution_authorized:
            raise ValueError("QuestionFamily shortlist cannot authorize contracts or execution")
        shortlisted_ids = [item.family.question_family_id for item in self.shortlisted]
        if len(shortlisted_ids) != len(set(shortlisted_ids)):
            raise ValueError("QuestionFamilyShortlistManifest has duplicate shortlisted families")
        for item in self.shortlisted:
            if item.family.context_id != self.context_id:
                raise ValueError("shortlisted family context does not match manifest context")
            if item.family.authority_ceiling != self.authority_ceiling:
                raise ValueError("shortlisted family authority ceiling does not match manifest")
        bucket_ids = {
            "shortlisted": set(shortlisted_ids),
            "rejected": set(self.rejected_family_ids),
            "needs_revision": set(self.needs_revision_family_ids),
            "deferred": set(self.deferred_family_ids),
        }
        for bucket_name, ids in bucket_ids.items():
            source = (
                shortlisted_ids
                if bucket_name == "shortlisted"
                else getattr(self, f"{bucket_name}_family_ids")
            )
            if len(source) != len(ids):
                raise ValueError(
                    f"QuestionFamilyShortlistManifest has duplicate {bucket_name} family IDs"
                )
        overlaps: list[str] = []
        names = list(bucket_ids)
        for index, left_name in enumerate(names):
            for right_name in names[index + 1 :]:
                overlap = sorted(bucket_ids[left_name] & bucket_ids[right_name])
                if overlap:
                    overlaps.append(f"{left_name}/{right_name}: " + ", ".join(overlap))
        if overlaps:
            raise ValueError(
                "QuestionFamilyShortlistManifest family status buckets overlap: "
                + "; ".join(overlaps)
            )
        return self


class QuestionFamilyIntentInvariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invariant_id: str
    question_family_id: str
    shared_phenomenon: str
    shared_theoretical_tension: str
    family_claim_boundary: str
    allowed_variant_axes: list[QuestionFamilyVariantDistinctionAxis] = Field(default_factory=list)
    forbidden_semantic_merges: list[str] = Field(default_factory=list)
    owner_session_id: str

    @field_validator(
        "invariant_id",
        "question_family_id",
        "shared_phenomenon",
        "shared_theoretical_tension",
        "family_claim_boundary",
        "owner_session_id",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionFamilyIntentInvariant core fields must be non-empty")
        return value


class QuestionFamilyVariantClosure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    decision: BranchDecisionKind
    owner_accepted: bool = False
    independent_review_accepted: bool = False
    human_approved: bool = False
    evidence_ids: list[str] = Field(default_factory=list)
    novelty_recheck_required: bool = False
    novelty_recheck_completed: bool = False
    novelty_recheck_artifact_ids: list[str] = Field(default_factory=list)
    rationale: str

    @model_validator(mode="after")
    def validate_variant_closure(self) -> QuestionFamilyVariantClosure:
        if self.decision in {
            BranchDecisionKind.PENDING,
            BranchDecisionKind.REJECTED_INSUFFICIENT_EVIDENCE,
        }:
            raise ValueError(
                "QuestionFamily variant closure decision is not allowed: " + self.decision.value
            )
        if self.decision.is_accepted:
            missing = []
            if not self.owner_accepted:
                missing.append("owner_accepted")
            if not self.independent_review_accepted:
                missing.append("independent_review_accepted")
            if not self.human_approved:
                missing.append("human_approved")
            if not self.evidence_ids:
                missing.append("evidence_ids")
            if self.novelty_recheck_required:
                if not self.novelty_recheck_completed:
                    missing.append("novelty_recheck_completed")
                if not self.novelty_recheck_artifact_ids:
                    missing.append("novelty_recheck_artifact_ids")
            if missing:
                raise ValueError(
                    "accepted QuestionFamily variant closure missing: " + ", ".join(missing)
                )
        elif self.novelty_recheck_completed or self.novelty_recheck_artifact_ids:
            raise ValueError(
                "novelty recheck completion artifacts are only allowed on accepted closures"
            )
        if not self.rationale.strip():
            raise ValueError("QuestionFamily variant closure requires rationale")
        return self


class QuestionFamilyClosurePackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    closure_id: str
    branch_id: str
    question_family_id: str
    active_variant_ids: list[str] = Field(default_factory=list)
    variant_closures: list[QuestionFamilyVariantClosure] = Field(default_factory=list)
    family_summary: str
    contract_eligible: bool = False
    execution_authorized: bool = False

    @model_validator(mode="after")
    def validate_closure(self) -> QuestionFamilyClosurePackage:
        closure_variant_ids = [closure.variant_id for closure in self.variant_closures]
        if len(closure_variant_ids) != len(set(closure_variant_ids)):
            raise ValueError("QuestionFamilyClosurePackage has duplicate variant closures")
        missing = sorted(set(self.active_variant_ids) - set(closure_variant_ids))
        if missing:
            raise ValueError(
                "QuestionFamilyClosurePackage missing variant closures: " + ", ".join(missing)
            )
        extra = sorted(set(closure_variant_ids) - set(self.active_variant_ids))
        if extra:
            raise ValueError(
                "QuestionFamilyClosurePackage has non-active variant closures: " + ", ".join(extra)
            )
        if self.contract_eligible or self.execution_authorized:
            raise ValueError("QuestionFamily closure cannot authorize contracts or execution")
        if not self.family_summary.strip():
            raise ValueError("QuestionFamilyClosurePackage requires family_summary")
        return self


QuestionFamilyDecisionKind = BranchDecisionKind
QuestionFamilyScope = Literal["family", "variant"]
