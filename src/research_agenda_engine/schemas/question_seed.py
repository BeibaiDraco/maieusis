from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ._r5_firewall import assert_proposal_safe_payload
from .planning_dialogue import BranchActorRole


class QuestionSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_seed_id: str
    question: str
    scientific_tension: str
    why_scientifically_important: str
    relevant_literature_claims: list[str] = Field(default_factory=list)
    novelty_hypothesis: str
    closest_known_work: list[str] = Field(default_factory=list)
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
    context_id: str
    origin_provider_id: str
    prompt_version: str

    @field_validator(
        "question_seed_id",
        "question",
        "scientific_tension",
        "why_scientifically_important",
        "novelty_hypothesis",
        "dataset_leverage_hypothesis",
        "discriminating_observation",
        "context_id",
        "origin_provider_id",
        "prompt_version",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionSeed core fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_scientific_seed_not_implementation_plan(self) -> QuestionSeed:
        if not self.positive_result_consequence.strip():
            raise ValueError("QuestionSeed requires positive_result_consequence")
        if not self.negative_result_consequence.strip():
            raise ValueError("QuestionSeed requires negative_result_consequence")
        if not self.null_result_consequence.strip():
            raise ValueError("QuestionSeed requires null_result_consequence")
        if not self.source_pattern_ids and not self.source_paper_case_ids:
            raise ValueError("QuestionSeed requires source_pattern_ids or source_paper_case_ids")
        assert_proposal_safe_payload(self.model_dump(mode="python"), context="QuestionSeed")
        return self


class QuestionSeedBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str
    context_id: str
    context_digest: str
    input_digest: str
    seeds: list[QuestionSeed] = Field(default_factory=list)
    origin_provider_id: str
    prompt_version: str

    @model_validator(mode="after")
    def require_unique_seed_ids_and_context(self) -> QuestionSeedBatch:
        seed_ids = [seed.question_seed_id for seed in self.seeds]
        if len(seed_ids) != len(set(seed_ids)):
            raise ValueError("QuestionSeedBatch contains duplicate question_seed_id values")
        mismatched = [
            seed.question_seed_id for seed in self.seeds if seed.context_id != self.context_id
        ]
        if mismatched:
            raise ValueError(
                "QuestionSeedBatch contains seeds from another context: " + ", ".join(mismatched)
            )
        return self


class QuestionSeedReviewStatus(StrEnum):
    SHORTLISTED = "shortlisted"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class QuestionScientistProposerBranch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposer_branch_id: str
    context_id: str
    context_digest: str
    context_subset_digest: str
    selected_pattern_ids: list[str] = Field(default_factory=list)
    selected_source_paper_case_ids: list[str] = Field(default_factory=list)
    seed_count_requested: int = Field(ge=1, le=20)
    batch_id: str
    batch_path: str
    origin_provider_id: str
    prompt_version: str
    input_digest: str

    @model_validator(mode="after")
    def validate_branch_record(self) -> QuestionScientistProposerBranch:
        if not self.proposer_branch_id.strip():
            raise ValueError("proposer branch requires proposer_branch_id")
        if len(self.context_digest) != 64 or len(self.context_subset_digest) != 64:
            raise ValueError("proposer branch digests must be sha256 hex strings")
        if not self.selected_pattern_ids:
            raise ValueError("proposer branch requires selected_pattern_ids")
        return self


class QuestionScientistEnsembleManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ensemble_id: str
    context_id: str
    context_digest: str
    prompt_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    proposer_branches: list[QuestionScientistProposerBranch] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_ensemble_manifest(self) -> QuestionScientistEnsembleManifest:
        if len(self.proposer_branches) < 3:
            raise ValueError("QuestionScientistEnsembleManifest requires at least 3 branches")
        branch_ids = [branch.proposer_branch_id for branch in self.proposer_branches]
        if len(branch_ids) != len(set(branch_ids)):
            raise ValueError("ensemble manifest contains duplicate proposer_branch_id values")
        subset_digests = [branch.context_subset_digest for branch in self.proposer_branches]
        if len(set(subset_digests)) != len(subset_digests):
            raise ValueError("ensemble branches must record distinct context subset digests")
        if {branch.context_id for branch in self.proposer_branches} != {self.context_id}:
            raise ValueError("ensemble branches must share the manifest context_id")
        return self


class QuestionSeedDuplicateCluster(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cluster_id: str
    seed_ids: list[str] = Field(default_factory=list)
    representative_seed_id: str
    rationale: str

    @model_validator(mode="after")
    def validate_cluster(self) -> QuestionSeedDuplicateCluster:
        if len(self.seed_ids) < 2:
            raise ValueError("duplicate cluster requires at least two seed_ids")
        if self.representative_seed_id not in self.seed_ids:
            raise ValueError("representative_seed_id must be in seed_ids")
        return self


class QuestionSeedReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_item_id: str
    seed: QuestionSeed
    source_batch_id: str
    proposer_branch_id: str = ""
    duplicate_cluster_id: str = ""
    duplicate_seed_ids: list[str] = Field(default_factory=list)
    auto_flags: list[str] = Field(default_factory=list)


class QuestionSeedReviewPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: str
    context_id: str
    context_digest: str
    source_batch_ids: list[str] = Field(default_factory=list)
    source_ensemble_id: str = ""
    blind_review: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duplicate_clusters: list[QuestionSeedDuplicateCluster] = Field(default_factory=list)
    items: list[QuestionSeedReviewItem] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_review_pack(self) -> QuestionSeedReviewPack:
        seed_ids = [item.seed.question_seed_id for item in self.items]
        if not seed_ids:
            raise ValueError("QuestionSeedReviewPack requires review items")
        if len(seed_ids) != len(set(seed_ids)):
            raise ValueError("QuestionSeedReviewPack contains duplicate question_seed_id values")
        if {item.seed.context_id for item in self.items} != {self.context_id}:
            raise ValueError("QuestionSeedReviewPack items must share context_id")
        return self


class QuestionSeedReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_item_id: str
    question_seed_id: str
    status: QuestionSeedReviewStatus = QuestionSeedReviewStatus.DEFERRED
    reviewer: str = ""
    notes: str = ""
    scientific_value_notes: str = ""
    priority: int | None = Field(default=None, ge=1)
    required_changes: list[str] = Field(default_factory=list)
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_human_decision(self) -> QuestionSeedReviewDecision:
        if (
            self.status == QuestionSeedReviewStatus.DEFERRED
            and not self.reviewer.strip()
            and not self.notes.strip()
            and not self.scientific_value_notes.strip()
            and not self.required_changes
        ):
            return self
        if not self.reviewer.strip():
            raise ValueError("QuestionSeed review decision requires reviewer")
        if not self.notes.strip():
            raise ValueError("QuestionSeed review decision requires notes")
        if (
            self.status == QuestionSeedReviewStatus.SHORTLISTED
            and not self.scientific_value_notes.strip()
        ):
            raise ValueError("shortlisted QuestionSeed requires scientific_value_notes")
        if self.status == QuestionSeedReviewStatus.NEEDS_REVISION and not self.required_changes:
            raise ValueError("needs_revision QuestionSeed requires required_changes")
        if self.status != QuestionSeedReviewStatus.NEEDS_REVISION and self.required_changes:
            raise ValueError("required_changes are only allowed for needs_revision decisions")
        if self.reviewed_at is None:
            self.reviewed_at = datetime.now(UTC)
        return self


class QuestionSeedReviewDecisionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_batch_id: str
    pack_id: str
    expert_reviewer: str = ""
    decisions: list[QuestionSeedReviewDecision] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_duplicate_decisions(self) -> QuestionSeedReviewDecisionBatch:
        ids = [decision.question_seed_id for decision in self.decisions]
        duplicates = sorted({seed_id for seed_id in ids if ids.count(seed_id) > 1})
        if duplicates:
            raise ValueError(
                "QuestionSeedReviewDecisionBatch contains duplicate decisions: "
                + ", ".join(duplicates)
            )
        return self


class ShortlistedQuestionSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: QuestionSeed
    review: QuestionSeedReviewDecision
    duplicate_cluster_id: str = ""
    source_batch_id: str


class QuestionSeedShortlistManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shortlist_id: str
    pack_id: str
    context_id: str
    context_digest: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    shortlisted: list[ShortlistedQuestionSeed] = Field(default_factory=list)
    rejected_seed_ids: list[str] = Field(default_factory=list)
    needs_revision_seed_ids: list[str] = Field(default_factory=list)
    deferred_seed_ids: list[str] = Field(default_factory=list)
    contract_eligible: bool = False
    execution_authorized: bool = False

    @model_validator(mode="after")
    def preserve_r5_boundary(self) -> QuestionSeedShortlistManifest:
        if self.contract_eligible or self.execution_authorized:
            raise ValueError("QuestionSeed shortlist cannot authorize contracts or execution")
        return self


class ScientificIntentInvariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    invariant_id: str
    question_seed_id: str
    central_phenomenon: str
    theoretical_tension: str
    target_contrast: str
    intended_claim: str
    discriminating_observation: str
    population_scope: str
    positive_result_meaning: str
    negative_result_meaning: str
    allowed_refinements: list[str] = Field(default_factory=list)
    forbidden_semantic_changes: list[str] = Field(default_factory=list)
    owner_session_id: str

    @field_validator(
        "invariant_id",
        "question_seed_id",
        "central_phenomenon",
        "theoretical_tension",
        "target_contrast",
        "intended_claim",
        "discriminating_observation",
        "population_scope",
        "positive_result_meaning",
        "negative_result_meaning",
        "owner_session_id",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ScientificIntentInvariant core fields must be non-empty")
        return value


class QuestionRevisionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    central_phenomenon_changed: bool = False
    theoretical_tension_changed: bool = False
    target_contrast_changed: bool = False
    claim_level_changed: bool = False
    population_scope_changed: bool = False
    discriminating_observation_changed: bool = False
    scientific_consequence_changed: bool = False
    material_revision: bool = False
    novelty_recheck_required: bool = False
    rationale: str

    @model_validator(mode="after")
    def require_novelty_recheck_for_material_revision(
        self,
    ) -> QuestionRevisionAssessment:
        changed = any(
            [
                self.central_phenomenon_changed,
                self.theoretical_tension_changed,
                self.target_contrast_changed,
                self.claim_level_changed,
                self.population_scope_changed,
                self.discriminating_observation_changed,
                self.scientific_consequence_changed,
            ]
        )
        if changed:
            self.material_revision = True
        if self.material_revision:
            self.novelty_recheck_required = True
        if not self.rationale.strip():
            raise ValueError("QuestionRevisionAssessment requires rationale")
        return self


class QuestionRevision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision_id: str
    branch_id: str
    previous_question_version_id: str
    new_question_version_id: str
    old_question: str
    new_question: str
    what_changed: list[str] = Field(default_factory=list)
    why_changed: str
    assessment: QuestionRevisionAssessment
    proposed_by: BranchActorRole
    owner_approved: bool = False

    @model_validator(mode="after")
    def validate_revision(self) -> QuestionRevision:
        if not self.old_question.strip() or not self.new_question.strip():
            raise ValueError("QuestionRevision requires previous and revised question text")
        if self.old_question == self.new_question:
            raise ValueError("QuestionRevision must change the question text")
        if self.previous_question_version_id == self.new_question_version_id:
            raise ValueError("QuestionRevision must create a new question version id")
        if not self.what_changed:
            raise ValueError("QuestionRevision requires what_changed")
        return self
