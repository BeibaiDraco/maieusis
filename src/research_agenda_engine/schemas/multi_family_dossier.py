from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .family_failure import sanitize_family_failure_text
from .generic_scientific_source import DatasetGroundingLevel
from .planning_dialogue import BranchDecisionKind
from .question_family_branch import QuestionFamilyBranchState


class FamilyDossierStatus(StrEnum):
    COMPLETED_DOSSIER_STACK = "completed_dossier_stack"
    QUEUED = "queued"
    BLOCKED = "blocked"
    FAILED_VALIDATION = "failed_validation"
    # A bounded retry on a transient owner/reviewer API failure (429/5xx/timeout) was exhausted.
    # A PLAIN honest terminal like FAILED_VALIDATION (authority MISSING) — deliberately NOT a
    # development-surrogate status, so it stays OUT of DEVELOPMENT_SURROGATE_STATUS_VALUES. It is
    # infrastructure, not a scientific failure.
    INFRASTRUCTURE_INCOMPLETE = "infrastructure_incomplete"
    PUBLIC_DOSSIER_REVISION_REQUIRED = "public_dossier_revision_required"
    PROVENANCE_INTEGRITY_TERMINAL = "provenance_integrity_terminal"
    # A planner/isolation/firewall integrity boundary stopped untrusted promotion. A safe family
    # summary may still render, but the run remains incomplete and siblings continue independently.
    HARD_INTEGRITY_TERMINAL = "hard_integrity_terminal"
    REJECTED = "rejected"
    HUMAN_ESCALATION = "human_escalation"
    # Automated bounded revise-loop terminals. These are honest, no-dossier terminals
    # (plain, non-surrogate authority): the accepted-plan dossier renders only on a double-accept,
    # so a reviewer-driven revise/reject/escalate/material outcome never emits an accepted dossier.
    # None is a mandatory human handoff (all are human-OPTIONAL, per AGENTS.md #10).
    REVISION_BUDGET_EXHAUSTED = "revision_budget_exhausted"
    MATERIAL_REVISION_DEFERRED = "material_revision_deferred"
    REVIEW_ESCALATED = "review_escalated"
    DEVELOPMENT_SURROGATE_PLAN = "development_surrogate_plan"
    DEVELOPMENT_SURROGATE_REJECT = "development_surrogate_reject"
    DEVELOPMENT_SURROGATE_ESCALATION = "development_surrogate_escalation"
    AUTOMATED_PLAN = "automated_plan"
    AUTOMATED_REJECT = "automated_reject"
    AUTOMATED_ESCALATION = "automated_escalation"


DEVELOPMENT_SURROGATE_STATUS_VALUES = (
    FamilyDossierStatus.DEVELOPMENT_SURROGATE_PLAN,
    FamilyDossierStatus.DEVELOPMENT_SURROGATE_REJECT,
    FamilyDossierStatus.DEVELOPMENT_SURROGATE_ESCALATION,
)
DEVELOPMENT_SURROGATE_STATUSES = frozenset(DEVELOPMENT_SURROGATE_STATUS_VALUES)
AUTOMATED_STATUS_VALUES = (
    FamilyDossierStatus.AUTOMATED_PLAN,
    FamilyDossierStatus.AUTOMATED_REJECT,
    FamilyDossierStatus.AUTOMATED_ESCALATION,
)
AUTOMATED_STATUSES = frozenset(AUTOMATED_STATUS_VALUES)


class ReviewAuthority(StrEnum):
    REAL_HUMAN_EXPERT = "real_human_expert"
    AUTOMATED = "automated"
    DEVELOPMENT_MODEL_SURROGATE = "development_model_surrogate"
    FIXTURE = "fixture"
    MISSING = "missing"
    UNKNOWN = "unknown"


class AutomatedReviewKind(StrEnum):
    """Who actually performed an `AUTOMATED` review, which the authority alone does not say."""

    INDEPENDENT_MODEL = "independent_model"
    HOST_AUTHORIZATION = "host_authorization"
    UNRESOLVED = "unresolved"


def classify_automated_review(authority: ReviewAuthority, provider_id: str) -> AutomatedReviewKind:
    """Separate a real independent review from a host authorization to render a dossier.

    `ReviewAuthority.AUTOMATED` says who was ALLOWED to authorize a dossier — no human gate
    required — and says nothing about whether an independent reviewer read it. Measured on the
    2026-08-14 climate leg: all four scientific rejections were closed by
    `provider_id: local:automated-review`, `model_id: deterministic-automated-review`, whose own
    `decision_summary` reads "Automated review allows a development dossier only." Printing
    "automated independent review" off the flag told readers a review had happened when none had.

    **This lives here because it had two implementations and only one was repaired**, which is the
    defect class this repository keeps paying for. `generic_family_dossier.py` was fixed on
    2026-08-15 and `presentation/family_page.py` was not, so the next run would have published two
    pages of the same family disagreeing about whether it was independently reviewed. Both now call
    this; neither restates the rule.

    An EMPTY `provider_id` is `UNRESOLVED`, not independent: the field defaults to `""`, and
    `"".startswith("local:")` is False, so a naive port of the sibling's check would silently call
    every unrecorded review independent.
    """
    if authority is not ReviewAuthority.AUTOMATED:
        return AutomatedReviewKind.UNRESOLVED
    identity = provider_id.strip()
    if not identity:
        return AutomatedReviewKind.UNRESOLVED
    if identity.startswith("local:"):
        return AutomatedReviewKind.HOST_AUTHORIZATION
    return AutomatedReviewKind.INDEPENDENT_MODEL


class MultiFamilyCoordinationMode(StrEnum):
    IMPORT_ONLY = "import_only"
    DRY_RUN_QUEUE = "dry_run_queue"
    DEVELOPMENT_RUN = "development_run"


class DevelopmentSurrogateFamilyVariantInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    question: str
    variant_role: str
    distinction_axes: list[str]
    distinct_from_siblings: str

    @field_validator(
        "variant_id",
        "question_seed_id",
        "question",
        "variant_role",
        "distinct_from_siblings",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("development surrogate variant fields must be non-empty")
        return value

    @field_validator("distinction_axes")
    @classmethod
    def require_axes(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("development surrogate variants require distinction axes")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("development surrogate variant distinction axes must be unique")
        return cleaned


class DevelopmentSurrogateFamilyOutcomeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_packet_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    family_title: str
    family_summary: str
    shared_scientific_tension: str
    branch_state: QuestionFamilyBranchState
    active_variants: list[DevelopmentSurrogateFamilyVariantInput]
    current_blockers: list[str]
    requested_outcome_statuses: list[FamilyDossierStatus] = Field(
        default_factory=lambda: list(DEVELOPMENT_SURROGATE_STATUS_VALUES)
    )
    review_mode: Literal["development_model_surrogate"] = "development_model_surrogate"
    authority_scope: Literal["development_testing_only"] = "development_testing_only"
    replaces_human_expert: bool = False
    serious_mode_importable: bool = False
    human_review_imported: bool = False
    allows_dossier_generation: bool = False
    reviewer_actor_role: Literal["model_surrogate_reviewer"] = "model_surrogate_reviewer"
    prompt_requirements: list[str] = Field(default_factory=list)
    forbidden_outputs: list[str] = Field(default_factory=list)

    @field_validator(
        "input_packet_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "family_title",
        "family_summary",
        "shared_scientific_tension",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("development surrogate input fields must be non-empty")
        return value

    @field_validator("active_variants")
    @classmethod
    def require_unique_variants(
        cls, value: list[DevelopmentSurrogateFamilyVariantInput]
    ) -> list[DevelopmentSurrogateFamilyVariantInput]:
        if not value:
            raise ValueError("development surrogate input requires active variants")
        variant_ids = [variant.variant_id for variant in value]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("development surrogate input variant IDs must be unique")
        return value

    @field_validator("current_blockers", "prompt_requirements", "forbidden_outputs")
    @classmethod
    def clean_text_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @field_validator("requested_outcome_statuses")
    @classmethod
    def require_surrogate_statuses(
        cls, value: list[FamilyDossierStatus]
    ) -> list[FamilyDossierStatus]:
        if not value:
            raise ValueError("development surrogate input requires requested outcome statuses")
        invalid = sorted(
            status.value for status in value if status not in DEVELOPMENT_SURROGATE_STATUSES
        )
        if invalid:
            raise ValueError(
                "development surrogate input may request only surrogate statuses: "
                + ", ".join(invalid)
            )
        if len(value) != len(set(value)):
            raise ValueError("development surrogate requested statuses must be unique")
        return value

    @model_validator(mode="after")
    def validate_surrogate_input_boundaries(
        self,
    ) -> DevelopmentSurrogateFamilyOutcomeInput:
        if self.replaces_human_expert:
            raise ValueError("development surrogate input cannot replace a human expert")
        if self.serious_mode_importable:
            raise ValueError("development surrogate input cannot be serious-mode importable")
        if self.human_review_imported:
            raise ValueError("development surrogate input cannot import human review")
        if self.allows_dossier_generation:
            raise ValueError("development surrogate input cannot allow dossier generation")
        return self


class DevelopmentModelSurrogateReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_mode: Literal["development_model_surrogate"] = "development_model_surrogate"
    authority_scope: Literal["development_testing_only"] = "development_testing_only"
    replaces_human_expert: bool = False
    serious_mode_importable: bool = False
    human_review_imported: bool = False
    allows_dossier_generation: bool = False
    bridge_created: bool = False
    execution_authorized: bool = False
    reviewer_actor_role: Literal["model_surrogate_reviewer"] = "model_surrogate_reviewer"
    provider_id: str
    model_id: str
    prompt_version: str
    session_id: str
    input_digest: str
    output_digest: str
    dataset_grounding_level: DatasetGroundingLevel = (
        DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY
    )
    decision_summary: str
    requires_real_human_review_before: str = "serious_dossier_generation_or_bridge"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "provider_id",
        "model_id",
        "prompt_version",
        "session_id",
        "decision_summary",
        "requires_real_human_review_before",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("development surrogate review fields must be non-empty")
        return value

    @field_validator("input_digest", "output_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="development surrogate digest")
        return value

    @model_validator(mode="after")
    def validate_surrogate_boundaries(self) -> DevelopmentModelSurrogateReview:
        if self.replaces_human_expert:
            raise ValueError("development surrogate review cannot replace a human expert")
        if self.serious_mode_importable:
            raise ValueError("development surrogate review cannot be serious-mode importable")
        if self.human_review_imported:
            raise ValueError("development surrogate review cannot import human review")
        if self.allows_dossier_generation:
            raise ValueError("development surrogate review cannot allow dossier generation")
        if self.bridge_created:
            raise ValueError("development surrogate review cannot create bridge artifacts")
        if self.execution_authorized:
            raise ValueError("development surrogate review cannot authorize execution")
        return self


class DevelopmentSurrogateFamilyOutcomeArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_id: str
    branch_id: str
    question_family_id: str
    outcome_status: FamilyDossierStatus
    decision_summary: str
    public_markdown: str
    blockers: list[str]
    review_mode: Literal["development_model_surrogate"] = "development_model_surrogate"
    authority_scope: Literal["development_testing_only"] = "development_testing_only"
    reviewer_actor_role: Literal["model_surrogate_reviewer"] = "model_surrogate_reviewer"
    replaces_human_expert: bool = False
    serious_mode_importable: bool = False
    human_review_imported: bool = False
    allows_dossier_generation: bool = False
    bridge_created: bool = False
    execution_authorized: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False

    @field_validator("artifact_id", "branch_id", "question_family_id", "decision_summary")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("development surrogate artifact fields must be non-empty")
        return value

    @field_validator("public_markdown")
    @classmethod
    def require_authority_statement(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("development surrogate artifact requires public_markdown")
        lower = value.lower()
        required_fragments = [
            "authority: development_model_surrogate",
            "scope: development testing only",
            "not a real human review",
            "not a scientific finding",
        ]
        missing = [fragment for fragment in required_fragments if fragment not in lower]
        if missing:
            raise ValueError(
                "development surrogate public_markdown is missing authority wording: "
                + ", ".join(missing)
            )
        return value

    @field_validator("blockers")
    @classmethod
    def require_blockers(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("development surrogate artifact requires blockers")
        return cleaned

    @model_validator(mode="after")
    def validate_artifact_boundaries(self) -> DevelopmentSurrogateFamilyOutcomeArtifact:
        if self.outcome_status not in DEVELOPMENT_SURROGATE_STATUSES:
            raise ValueError("development surrogate artifact requires a surrogate outcome status")
        if self.replaces_human_expert:
            raise ValueError("development surrogate artifact cannot replace a human expert")
        if self.serious_mode_importable:
            raise ValueError("development surrogate artifact cannot be serious-mode importable")
        if self.human_review_imported:
            raise ValueError("development surrogate artifact cannot import human review")
        if self.allows_dossier_generation:
            raise ValueError("development surrogate artifact cannot allow dossier generation")
        _validate_planning_flags(
            planning_only=True,
            non_terminal=True,
            contract_eligible=False,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        return self


class FamilyDossierOutputRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str
    question_family_id: str
    branch_id: str
    context_id: str
    owner_session_id: str
    family_title: str
    variant_ids: list[str]
    status: FamilyDossierStatus
    # Rejection subtype preserved from the planner's BranchRejectionMessage.decision (dataset
    # mismatch / operationalization failure / scientific drift / ...). Populated only for
    # rejection records; the status stays DEVELOPMENT_SURROGATE_REJECT (no status explosion).
    rejection_reason: BranchDecisionKind | None = None
    branch_state: QuestionFamilyBranchState
    branch_event_count: int = Field(ge=1)
    replay_verified: bool = False
    branch_event_id: str = ""
    branch_event_sequence: int | None = Field(default=None, ge=1)
    human_review_gate_event_id: str = ""
    human_review_gate_event_sequence: int | None = Field(default=None, ge=1)
    human_review_gate_artifact_id: str = ""
    human_review_gate_artifact_digest: str = ""
    end_user_dossier_manifest_id: str = ""
    end_user_dossier_manifest_path: str = ""
    end_user_dossier_path: str = ""
    end_user_dossier_digest: str = ""
    end_user_dossier_artifact_path: str = ""
    end_user_dossier_artifact_digest: str = ""
    audit_sidecar_path: str = ""
    audit_sidecar_digest: str = ""
    provider_id: str = ""
    model_id: str = ""
    prompt_version: str = ""
    session_id: str = ""
    input_digest: str = ""
    output_digest: str = ""
    human_review_authority: ReviewAuthority = ReviewAuthority.MISSING
    human_review_status: str = "not_imported"
    dataset_grounding_level: DatasetGroundingLevel = (
        DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY
    )
    human_review_imported: bool = False
    allows_dossier_generation: bool = False
    blockers: list[str] = Field(default_factory=list)
    development_surrogate_review: DevelopmentModelSurrogateReview | None = None
    outcome_markdown_path: str = ""
    outcome_audit_path: str = ""
    development_surrogate_input_path: str = ""
    development_surrogate_artifact_path: str = ""
    development_surrogate_session_snapshot_path: str = ""
    development_surrogate_input_digest: str = ""
    development_surrogate_artifact_digest: str = ""
    development_surrogate_session_snapshot_digest: str = ""
    planning_only: bool = True
    non_terminal: bool = True
    final_dossier_created: bool = False
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "record_id",
        "question_family_id",
        "branch_id",
        "context_id",
        "owner_session_id",
        "family_title",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FamilyDossierOutputRecord identity fields must be non-empty")
        return value

    @field_validator("variant_ids")
    @classmethod
    def require_unique_variants(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("FamilyDossierOutputRecord requires variant_ids")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("FamilyDossierOutputRecord variant_ids must be unique")
        return cleaned

    @field_validator(
        "end_user_dossier_digest",
        "end_user_dossier_artifact_digest",
        "audit_sidecar_digest",
        "input_digest",
        "output_digest",
        "development_surrogate_input_digest",
        "development_surrogate_artifact_digest",
        "development_surrogate_session_snapshot_digest",
        "human_review_gate_artifact_digest",
    )
    @classmethod
    def validate_optional_digest(cls, value: str) -> str:
        if value:
            _validate_sha256(value, field_name="FamilyDossierOutputRecord digest")
        return value

    @field_validator("blockers")
    @classmethod
    def clean_blockers(cls, value: list[str]) -> list[str]:
        return [sanitized for item in value if (sanitized := sanitize_family_failure_text(item))]

    @field_validator("human_review_status")
    @classmethod
    def clean_human_review_status(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FamilyDossierOutputRecord requires human_review_status")
        return value

    @model_validator(mode="after")
    def validate_record(self) -> FamilyDossierOutputRecord:
        _validate_planning_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        if self.human_review_authority == ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE:
            if self.development_surrogate_review is None:
                raise ValueError("development surrogate family records require review provenance")
            if self.status not in DEVELOPMENT_SURROGATE_STATUSES:
                raise ValueError(
                    "development surrogate family records require surrogate-prefixed status"
                )
            if self.human_review_imported or self.allows_dossier_generation:
                raise ValueError(
                    "development surrogate family records cannot import or unlock human review"
                )
            if self.human_review_status not in {
                "awaiting_real_human_review",
                "not_imported",
            }:
                raise ValueError(
                    "development surrogate family records must remain awaiting real human review"
                )
            self._validate_development_surrogate_record()
        elif self.human_review_authority == ReviewAuthority.AUTOMATED:
            if self.status not in AUTOMATED_STATUSES:
                raise ValueError("automated family records require automated status")
            if self.development_surrogate_review is not None:
                raise ValueError("automated records cannot carry development surrogate provenance")
            if self.human_review_imported or self.allows_dossier_generation:
                raise ValueError("automated family records cannot import or unlock human review")
            if self.human_review_status not in {
                "human_review_optional_not_imported",
                "not_imported",
            }:
                raise ValueError("automated family records must keep human review optional")
            self._validate_automated_record()
        elif self.development_surrogate_review is not None:
            raise ValueError(
                "development surrogate provenance requires development_model_surrogate authority"
            )

        if (
            self.status in DEVELOPMENT_SURROGATE_STATUSES
            and self.human_review_authority != ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE
        ):
            raise ValueError("surrogate-prefixed statuses require development_model_surrogate")
        if (
            self.status in AUTOMATED_STATUSES
            and self.human_review_authority != ReviewAuthority.AUTOMATED
        ):
            raise ValueError("automated statuses require automated authority")

        if self.human_review_authority != ReviewAuthority.REAL_HUMAN_EXPERT and (
            self.human_review_imported or self.allows_dossier_generation
        ):
            raise ValueError(
                "only real_human_expert authority can import human review or unlock dossiers"
            )

        if self.status == FamilyDossierStatus.COMPLETED_DOSSIER_STACK:
            self._validate_completed_record()
        else:
            if self.final_dossier_created:
                raise ValueError("non-completed family records cannot mark final_dossier_created")
            if self.status not in {FamilyDossierStatus.QUEUED} and not self.blockers:
                raise ValueError("blocked/rejected/escalated family records require blockers")
        self._validate_branch_local_paths()
        return self

    def _validate_development_surrogate_record(self) -> None:
        assert self.development_surrogate_review is not None
        if self.replay_verified and not self.branch_event_id.strip():
            raise ValueError(
                "development surrogate records cannot be replay_verified without branch_event_id"
            )
        if self.branch_event_id.strip() and self.branch_event_sequence is None:
            raise ValueError("development surrogate replay requires branch_event_sequence")
        required_text_fields = {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "session_id": self.session_id,
            "outcome_markdown_path": self.outcome_markdown_path,
            "outcome_audit_path": self.outcome_audit_path,
            "development_surrogate_input_path": self.development_surrogate_input_path,
            "development_surrogate_artifact_path": self.development_surrogate_artifact_path,
            "development_surrogate_session_snapshot_path": (
                self.development_surrogate_session_snapshot_path
            ),
        }
        missing = sorted(name for name, value in required_text_fields.items() if not value.strip())
        if missing:
            raise ValueError("development surrogate records require " + ", ".join(missing))
        required_digests = {
            "input_digest": self.input_digest,
            "output_digest": self.output_digest,
            "development_surrogate_input_digest": self.development_surrogate_input_digest,
            "development_surrogate_artifact_digest": self.development_surrogate_artifact_digest,
            "development_surrogate_session_snapshot_digest": (
                self.development_surrogate_session_snapshot_digest
            ),
        }
        missing_digests = sorted(name for name, value in required_digests.items() if not value)
        if missing_digests:
            raise ValueError("development surrogate records require " + ", ".join(missing_digests))
        if self.input_digest != self.development_surrogate_review.input_digest:
            raise ValueError("development surrogate record input digest mismatch")
        if self.output_digest != self.development_surrogate_review.output_digest:
            raise ValueError("development surrogate record output digest mismatch")
        identity_mismatches = [
            name
            for name, record_value, review_value in [
                ("provider_id", self.provider_id, self.development_surrogate_review.provider_id),
                ("model_id", self.model_id, self.development_surrogate_review.model_id),
                (
                    "prompt_version",
                    self.prompt_version,
                    self.development_surrogate_review.prompt_version,
                ),
                ("session_id", self.session_id, self.development_surrogate_review.session_id),
            ]
            if record_value != review_value
        ]
        if identity_mismatches:
            raise ValueError(
                "development surrogate record identity mismatch: " + ", ".join(identity_mismatches)
            )
        reserved_completed_fields = {
            "end_user_dossier_manifest_id": self.end_user_dossier_manifest_id,
            "end_user_dossier_manifest_path": self.end_user_dossier_manifest_path,
            "end_user_dossier_path": self.end_user_dossier_path,
            "end_user_dossier_digest": self.end_user_dossier_digest,
            "end_user_dossier_artifact_path": self.end_user_dossier_artifact_path,
            "end_user_dossier_artifact_digest": self.end_user_dossier_artifact_digest,
            "audit_sidecar_path": self.audit_sidecar_path,
            "audit_sidecar_digest": self.audit_sidecar_digest,
        }
        populated = sorted(
            name for name, value in reserved_completed_fields.items() if str(value).strip()
        )
        if populated:
            raise ValueError(
                "development surrogate records cannot populate completed dossier fields: "
                + ", ".join(populated)
            )

    def _validate_automated_record(self) -> None:
        if self.replay_verified and not self.branch_event_id.strip():
            raise ValueError("automated records cannot be replay_verified without branch_event_id")
        if self.branch_event_id.strip() and self.branch_event_sequence is None:
            raise ValueError("automated replay requires branch_event_sequence")
        required_text_fields = {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "session_id": self.session_id,
            "outcome_markdown_path": self.outcome_markdown_path,
            "outcome_audit_path": self.outcome_audit_path,
        }
        missing = sorted(name for name, value in required_text_fields.items() if not value.strip())
        if missing:
            raise ValueError("automated records require " + ", ".join(missing))
        required_digests = {
            "input_digest": self.input_digest,
            "output_digest": self.output_digest,
        }
        missing_digests = sorted(name for name, value in required_digests.items() if not value)
        if missing_digests:
            raise ValueError("automated records require " + ", ".join(missing_digests))
        reserved_completed_fields = {
            "end_user_dossier_manifest_id": self.end_user_dossier_manifest_id,
            "end_user_dossier_manifest_path": self.end_user_dossier_manifest_path,
            "end_user_dossier_path": self.end_user_dossier_path,
            "end_user_dossier_digest": self.end_user_dossier_digest,
            "end_user_dossier_artifact_path": self.end_user_dossier_artifact_path,
            "end_user_dossier_artifact_digest": self.end_user_dossier_artifact_digest,
            "audit_sidecar_path": self.audit_sidecar_path,
            "audit_sidecar_digest": self.audit_sidecar_digest,
        }
        populated = sorted(
            name for name, value in reserved_completed_fields.items() if str(value).strip()
        )
        if populated:
            raise ValueError(
                "automated records cannot populate completed dossier fields: "
                + ", ".join(populated)
            )

    def _validate_completed_record(self) -> None:
        required_text_fields = {
            "branch_event_id": self.branch_event_id,
            "end_user_dossier_manifest_id": self.end_user_dossier_manifest_id,
            "end_user_dossier_manifest_path": self.end_user_dossier_manifest_path,
            "end_user_dossier_path": self.end_user_dossier_path,
            "end_user_dossier_artifact_path": self.end_user_dossier_artifact_path,
            "audit_sidecar_path": self.audit_sidecar_path,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "session_id": self.session_id,
        }
        missing = sorted(name for name, value in required_text_fields.items() if not value.strip())
        if missing:
            raise ValueError("completed family dossier records require " + ", ".join(missing))
        required_digests = {
            "end_user_dossier_digest": self.end_user_dossier_digest,
            "end_user_dossier_artifact_digest": self.end_user_dossier_artifact_digest,
            "audit_sidecar_digest": self.audit_sidecar_digest,
            "input_digest": self.input_digest,
            "output_digest": self.output_digest,
        }
        missing_digests = sorted(name for name, value in required_digests.items() if not value)
        if missing_digests:
            raise ValueError(
                "completed family dossier records require " + ", ".join(missing_digests)
            )
        if not self.replay_verified:
            raise ValueError("completed family dossier records require replay_verified")
        if self.branch_event_sequence is None:
            raise ValueError("completed family dossier records require branch_event_sequence")
        required_gate_fields = {
            "human_review_gate_event_id": self.human_review_gate_event_id,
            "human_review_gate_artifact_id": self.human_review_gate_artifact_id,
        }
        missing_gate = sorted(
            name for name, value in required_gate_fields.items() if not value.strip()
        )
        if missing_gate:
            raise ValueError("completed family dossier records require " + ", ".join(missing_gate))
        if self.human_review_gate_event_sequence is None:
            raise ValueError(
                "completed family dossier records require human_review_gate_event_sequence"
            )
        if not self.human_review_gate_artifact_digest:
            raise ValueError(
                "completed family dossier records require human_review_gate_artifact_digest"
            )
        if self.human_review_authority != ReviewAuthority.REAL_HUMAN_EXPERT:
            raise ValueError("completed family dossier records require real human authority")
        if not self.human_review_imported:
            raise ValueError("completed family dossier records require human_review_imported")
        if not self.allows_dossier_generation:
            raise ValueError("completed family dossier records require dossier generation gate")
        if self.human_review_status not in {"accepted_for_dossier", "imported"}:
            raise ValueError(
                "completed family dossier records require accepted human review status"
            )
        if not self.dataset_grounding_level.supports_serious_dataset_grounding:
            raise ValueError(
                "completed family dossier records require sample or full-local dataset grounding"
            )
        if not self.final_dossier_created:
            raise ValueError("completed family dossier records require final_dossier_created")

    def _validate_branch_local_paths(self) -> None:
        path_fields = {
            "end_user_dossier_manifest_path": self.end_user_dossier_manifest_path,
            "end_user_dossier_path": self.end_user_dossier_path,
            "end_user_dossier_artifact_path": self.end_user_dossier_artifact_path,
            "audit_sidecar_path": self.audit_sidecar_path,
            "outcome_markdown_path": self.outcome_markdown_path,
            "outcome_audit_path": self.outcome_audit_path,
            "development_surrogate_input_path": self.development_surrogate_input_path,
            "development_surrogate_artifact_path": self.development_surrogate_artifact_path,
            "development_surrogate_session_snapshot_path": (
                self.development_surrogate_session_snapshot_path
            ),
        }
        leaked = [
            name
            for name, path_text in path_fields.items()
            if path_text.strip() and not _is_branch_local_path(path_text, self.branch_id)
        ]
        if leaked:
            raise ValueError(
                "family dossier record branch-local paths must stay under "
                f"/branches/{self.branch_id}/planner/: " + ", ".join(leaked)
            )


class ProviderWarningActor(StrEnum):
    """Which agent boundary produced a recoverable provider-warning terminal.

    ``OWNER_OR_INDEPENDENT_REVIEWER`` is the honest combined label for the shared bounded-retry
    dialogue boundary, where the exhausted exception does not attribute a single actor. Claiming
    a single actor there would invent a fact the boundary does not know.
    """

    OWNER = "owner"
    INDEPENDENT_REVIEWER = "independent_reviewer"
    OWNER_OR_INDEPENDENT_REVIEWER = "owner_or_independent_reviewer"
    PLANNER = "planner"
    RENDERER = "renderer"


_PROVIDER_WARNING_TOKEN = re.compile(r"[A-Za-z0-9_.-]{1,80}")
_PROVIDER_WARNING_PROVIDER_ID = re.compile(r"[A-Za-z0-9_.:/-]{1,120}")


class ProviderWarningReceipt(BaseModel):
    """Typed, secret-free metadata for one recoverable provider-warning family terminal.

    Every text field is constrained to a bounded token vocabulary (enum values, exception class
    names, provider identifiers) — raw provider message text is structurally unrepresentable, so
    the no-secret guarantee is a hard truth boundary, not a wording heuristic.
    """

    model_config = ConfigDict(extra="forbid")

    actor: ProviderWarningActor
    stage: str
    provider_id: str = ""
    failure_kind: str
    attempt_count: int = Field(default=1, ge=1)
    bounded_retry_used: bool = False

    @field_validator("stage", "failure_kind")
    @classmethod
    def require_bounded_token(cls, value: str) -> str:
        value = value.strip()
        if not _PROVIDER_WARNING_TOKEN.fullmatch(value):
            raise ValueError(
                "ProviderWarningReceipt stage/failure_kind must be a bounded token "
                "([A-Za-z0-9_.-], 1-80 chars), never raw provider text"
            )
        return value

    @field_validator("provider_id")
    @classmethod
    def require_bounded_provider_id(cls, value: str) -> str:
        value = value.strip()
        if value and not _PROVIDER_WARNING_PROVIDER_ID.fullmatch(value):
            raise ValueError(
                "ProviderWarningReceipt provider_id must be a bounded identifier "
                "([A-Za-z0-9_.:/-], 1-120 chars), never raw provider text"
            )
        return value


class FamilyOutcomeAuditSidecar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_sidecar_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    status: FamilyDossierStatus
    outcome_markdown_path: str
    outcome_markdown_digest: str
    blockers: list[str]
    human_review_authority: ReviewAuthority = ReviewAuthority.MISSING
    human_review_status: str = "not_imported"
    # Additive after the frozen v0.1 baseline: optional with a None default so every persisted
    # sidecar loads unchanged; no frozen digest binds this model's dump (verified for CLIM-12).
    provider_warning: ProviderWarningReceipt | None = None
    dataset_grounding_level: DatasetGroundingLevel = (
        DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY
    )
    development_surrogate_review: DevelopmentModelSurrogateReview | None = None
    development_surrogate_input_path: str = ""
    development_surrogate_artifact_path: str = ""
    development_surrogate_session_snapshot_path: str = ""
    development_surrogate_input_digest: str = ""
    development_surrogate_artifact_digest: str = ""
    development_surrogate_session_snapshot_digest: str = ""
    planning_only: bool = True
    non_terminal: bool = True
    final_dossier_created: bool = False
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "audit_sidecar_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "outcome_markdown_path",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("FamilyOutcomeAuditSidecar identity fields must be non-empty")
        return value

    @field_validator("outcome_markdown_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="FamilyOutcomeAuditSidecar digest")
        return value

    @field_validator(
        "development_surrogate_input_digest",
        "development_surrogate_artifact_digest",
        "development_surrogate_session_snapshot_digest",
    )
    @classmethod
    def validate_optional_digest(cls, value: str) -> str:
        if value:
            _validate_sha256(value, field_name="FamilyOutcomeAuditSidecar surrogate digest")
        return value

    @field_validator("blockers")
    @classmethod
    def require_blockers(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("FamilyOutcomeAuditSidecar requires blockers")
        return cleaned

    @model_validator(mode="after")
    def validate_sidecar(self) -> FamilyOutcomeAuditSidecar:
        _validate_planning_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        if self.final_dossier_created:
            raise ValueError("development outcome sidecars cannot mark final_dossier_created")
        if self.human_review_authority == ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE:
            if self.development_surrogate_review is None:
                raise ValueError("development surrogate outcome sidecars require provenance")
            if self.status not in DEVELOPMENT_SURROGATE_STATUSES:
                raise ValueError(
                    "development surrogate outcome sidecars require surrogate-prefixed status"
                )
            required_text_fields = {
                "development_surrogate_input_path": self.development_surrogate_input_path,
                "development_surrogate_artifact_path": self.development_surrogate_artifact_path,
                "development_surrogate_session_snapshot_path": (
                    self.development_surrogate_session_snapshot_path
                ),
            }
            missing = sorted(
                name for name, value in required_text_fields.items() if not value.strip()
            )
            if missing:
                raise ValueError(
                    "development surrogate outcome sidecars require " + ", ".join(missing)
                )
            required_digests = {
                "development_surrogate_input_digest": self.development_surrogate_input_digest,
                "development_surrogate_artifact_digest": self.development_surrogate_artifact_digest,
                "development_surrogate_session_snapshot_digest": (
                    self.development_surrogate_session_snapshot_digest
                ),
            }
            missing_digests = sorted(name for name, value in required_digests.items() if not value)
            if missing_digests:
                raise ValueError(
                    "development surrogate outcome sidecars require " + ", ".join(missing_digests)
                )
        elif self.development_surrogate_review is not None:
            raise ValueError(
                "development surrogate provenance requires development_model_surrogate authority"
            )
        elif self.human_review_authority == ReviewAuthority.AUTOMATED:
            if self.status not in AUTOMATED_STATUSES:
                raise ValueError("automated outcome sidecars require automated status")
        if (
            self.status in DEVELOPMENT_SURROGATE_STATUSES
            and self.human_review_authority != ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE
        ):
            raise ValueError("surrogate-prefixed statuses require development_model_surrogate")
        if (
            self.status in AUTOMATED_STATUSES
            and self.human_review_authority != ReviewAuthority.AUTOMATED
        ):
            raise ValueError("automated statuses require automated authority")
        return self


class MultiFamilyDossierManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aggregate_manifest_id: str
    run_id: str
    shortlist_id: str
    context_id: str
    coordination_mode: MultiFamilyCoordinationMode
    max_parallel_family_workers: int = Field(default=2, ge=1, le=8)
    shortlisted_family_ids: list[str] = Field(default_factory=list)
    records: list[FamilyDossierOutputRecord]
    aggregate_report_path: str = ""
    parallel_run_report_path: str = ""
    planning_only: bool = True
    non_terminal: bool = True
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("aggregate_manifest_id", "run_id", "shortlist_id", "context_id")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("MultiFamilyDossierManifest identity fields must be non-empty")
        return value

    @field_validator("shortlisted_family_ids")
    @classmethod
    def clean_shortlisted_family_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("MultiFamilyDossierManifest shortlisted_family_ids must be unique")
        return cleaned

    @model_validator(mode="after")
    def validate_manifest(self) -> MultiFamilyDossierManifest:
        _validate_planning_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        if not self.records:
            raise ValueError("MultiFamilyDossierManifest requires records")
        if any(record.context_id != self.context_id for record in self.records):
            raise ValueError("aggregate dossier records must share the manifest context_id")
        if (
            self.coordination_mode == MultiFamilyCoordinationMode.DEVELOPMENT_RUN
            and self.shortlisted_family_ids
        ):
            expected = set(self.shortlisted_family_ids)
            actual = {record.question_family_id for record in self.records}
            if actual != expected:
                missing = sorted(expected - actual)
                unexpected = sorted(actual - expected)
                detail = []
                if missing:
                    detail.append("missing: " + ", ".join(missing))
                if unexpected:
                    detail.append("unexpected: " + ", ".join(unexpected))
                raise ValueError(
                    "development aggregate manifests must cover shortlisted families exactly "
                    "once" + (": " + "; ".join(detail) if detail else "")
                )
        _require_unique("branch_id", [record.branch_id for record in self.records])
        _require_unique(
            "question_family_id", [record.question_family_id for record in self.records]
        )
        _require_unique("owner_session_id", [record.owner_session_id for record in self.records])
        _require_unique(
            "end_user_dossier_manifest_id",
            [
                record.end_user_dossier_manifest_id
                for record in self.records
                if record.end_user_dossier_manifest_id
            ],
        )
        _require_unique(
            "end_user_dossier_artifact_digest",
            [
                record.end_user_dossier_artifact_digest
                for record in self.records
                if record.end_user_dossier_artifact_digest
            ],
        )
        _require_unique(
            "audit_sidecar_digest",
            [record.audit_sidecar_digest for record in self.records if record.audit_sidecar_digest],
        )
        surrogate_reviews = [
            record.development_surrogate_review
            for record in self.records
            if record.development_surrogate_review is not None
        ]
        _require_unique(
            "development_surrogate_review.session_id",
            [review.session_id for review in surrogate_reviews],
        )
        _require_unique(
            "development_surrogate_review.input_digest",
            [review.input_digest for review in surrogate_reviews],
        )
        _require_unique(
            "development_surrogate_review.output_digest",
            [review.output_digest for review in surrogate_reviews],
        )
        completed = [
            record
            for record in self.records
            if record.status == FamilyDossierStatus.COMPLETED_DOSSIER_STACK
        ]
        if self.coordination_mode == MultiFamilyCoordinationMode.IMPORT_ONLY and len(
            completed
        ) != len(self.records):
            raise ValueError("import_only aggregate manifests can contain only completed records")
        return self

    @property
    def completed_family_count(self) -> int:
        return sum(
            record.status == FamilyDossierStatus.COMPLETED_DOSSIER_STACK for record in self.records
        )

    @property
    def blocked_or_failed_family_count(self) -> int:
        return sum(
            record.status
            in {
                FamilyDossierStatus.BLOCKED,
                FamilyDossierStatus.FAILED_VALIDATION,
                FamilyDossierStatus.REJECTED,
                FamilyDossierStatus.HUMAN_ESCALATION,
                FamilyDossierStatus.DEVELOPMENT_SURROGATE_PLAN,
                FamilyDossierStatus.DEVELOPMENT_SURROGATE_REJECT,
                FamilyDossierStatus.DEVELOPMENT_SURROGATE_ESCALATION,
                FamilyDossierStatus.AUTOMATED_PLAN,
                FamilyDossierStatus.AUTOMATED_REJECT,
                FamilyDossierStatus.AUTOMATED_ESCALATION,
            }
            for record in self.records
        )


def _validate_sha256(value: str, *, field_name: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be sha256 hex")


def _validate_planning_flags(
    *,
    planning_only: bool,
    non_terminal: bool,
    contract_eligible: bool,
    execution_authorized: bool,
    bridge_created: bool,
    questioncard_created: bool,
    analysiscontract_created: bool,
    result_values_persisted: bool,
) -> None:
    if not planning_only:
        raise ValueError("multi-family dossier records must remain planning_only")
    if not non_terminal:
        raise ValueError("multi-family dossier records must remain non_terminal")
    forbidden_true = {
        "contract_eligible": contract_eligible,
        "execution_authorized": execution_authorized,
        "bridge_created": bridge_created,
        "questioncard_created": questioncard_created,
        "analysiscontract_created": analysiscontract_created,
        "result_values_persisted": result_values_persisted,
    }
    invalid = [name for name, value in forbidden_true.items() if value]
    if invalid:
        raise ValueError("multi-family dossier records set forbidden flags: " + ", ".join(invalid))


def _require_unique(label: str, values: list[str]) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValueError(f"duplicate {label} values in aggregate dossier manifest: {duplicates}")


def _is_branch_local_path(path_text: str, branch_id: str) -> bool:
    normalized = "/" + path_text.strip().replace("\\", "/").lstrip("/")
    return f"/branches/{branch_id}/planner/" in normalized
