from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .generic_scientific_source import DatasetClaimStatus, DatasetGroundingLevel
from .multi_family_dossier import ReviewAuthority


class GenericReviewDecisionValue(StrEnum):
    ACCEPT_FOR_DEVELOPMENT_DOSSIER = "accept_for_development_dossier"
    ACCEPT_FOR_SERIOUS_DOSSIER = "accept_for_serious_dossier"
    REVISION_REQUIRED = "revision_required"
    REJECT = "reject"
    HUMAN_ESCALATION = "human_escalation"


class GenericFamilyReviewDecisionPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_packet_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_outcome_packet_id: str
    authority: ReviewAuthority
    decision: GenericReviewDecisionValue
    decision_summary: str
    reviewer_name: str = ""
    provider_id: str = ""
    model_id: str = ""
    prompt_version: str = ""
    session_id: str = ""
    input_digest: str = ""
    output_digest: str = ""
    dataset_grounding_level: DatasetGroundingLevel = (
        DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY
    )
    dataset_claim_status: DatasetClaimStatus = DatasetClaimStatus.UNVERIFIED
    development_dossier_rendering_allowed: bool = False
    development_dossier_generation_allowed: bool = False
    human_review_imported: bool = False
    allows_dossier_generation: bool = False
    serious_mode_importable: bool = False
    replaces_human_expert: bool = False
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "decision_packet_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_outcome_packet_id",
        "decision_summary",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericFamilyReviewDecisionPacket fields must be non-empty")
        return value

    @field_validator("input_digest", "output_digest")
    @classmethod
    def validate_optional_digest(cls, value: str) -> str:
        if value and (len(value) != 64 or any(char not in "0123456789abcdef" for char in value)):
            raise ValueError("GenericFamilyReviewDecisionPacket digests must be sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_authority_boundaries(self) -> GenericFamilyReviewDecisionPacket:
        if (
            self.development_dossier_generation_allowed
            and not self.development_dossier_rendering_allowed
        ):
            self.development_dossier_rendering_allowed = True
        if (
            self.development_dossier_rendering_allowed
            and not self.development_dossier_generation_allowed
        ):
            self.development_dossier_generation_allowed = True
        if self.authority == ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE:
            self._validate_development_surrogate()
        elif self.authority == ReviewAuthority.AUTOMATED:
            self._validate_automated()
        elif self.authority == ReviewAuthority.REAL_HUMAN_EXPERT:
            self._validate_real_human()
        else:
            self._validate_non_authoritative()
        return self

    def _validate_development_surrogate(self) -> None:
        required = {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "session_id": self.session_id,
            "input_digest": self.input_digest,
            "output_digest": self.output_digest,
        }
        missing = sorted(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError("development surrogate decision requires " + ", ".join(missing))
        if self.decision == GenericReviewDecisionValue.ACCEPT_FOR_SERIOUS_DOSSIER:
            raise ValueError("development surrogate cannot accept for serious dossier")
        if (
            self.decision == GenericReviewDecisionValue.ACCEPT_FOR_DEVELOPMENT_DOSSIER
            and not self.development_dossier_rendering_allowed
        ):
            raise ValueError("development surrogate acceptance requires rendering-only allowance")
        if self.human_review_imported or self.allows_dossier_generation:
            raise ValueError(
                "development surrogate cannot import human review or unlock serious dossier"
            )
        if self.serious_mode_importable:
            raise ValueError("development surrogate cannot be serious-mode importable")
        if self.replaces_human_expert:
            raise ValueError("development surrogate cannot replace a human expert")

    def _validate_automated(self) -> None:
        required = {
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "prompt_version": self.prompt_version,
            "session_id": self.session_id,
            "input_digest": self.input_digest,
            "output_digest": self.output_digest,
        }
        missing = sorted(name for name, value in required.items() if not value.strip())
        if missing:
            raise ValueError("automated decision requires " + ", ".join(missing))
        if self.decision == GenericReviewDecisionValue.ACCEPT_FOR_SERIOUS_DOSSIER:
            raise ValueError("automated serious dossier unlock is disabled until Option B")
        if (
            self.decision == GenericReviewDecisionValue.ACCEPT_FOR_DEVELOPMENT_DOSSIER
            and not self.development_dossier_rendering_allowed
        ):
            raise ValueError("automated acceptance requires rendering-only allowance")
        if self.human_review_imported or self.allows_dossier_generation:
            raise ValueError("automated decision cannot import human review or unlock dossiers")
        if self.serious_mode_importable:
            raise ValueError("automated decision cannot be serious-mode importable until Option B")
        if self.replaces_human_expert:
            raise ValueError("automated decision cannot replace a human expert")

    def _validate_real_human(self) -> None:
        if not self.reviewer_name.strip():
            raise ValueError("real human review requires reviewer_name")
        if self.decision in {
            GenericReviewDecisionValue.ACCEPT_FOR_DEVELOPMENT_DOSSIER,
            GenericReviewDecisionValue.ACCEPT_FOR_SERIOUS_DOSSIER,
        }:
            if not self.human_review_imported:
                raise ValueError("real human acceptance requires human_review_imported")
            if not self.allows_dossier_generation:
                raise ValueError("real human acceptance requires allows_dossier_generation")
        if (
            self.decision == GenericReviewDecisionValue.ACCEPT_FOR_SERIOUS_DOSSIER
            and not self.dataset_grounding_level.supports_serious_dataset_grounding
        ):
            raise ValueError("serious dossier acceptance requires stronger dataset grounding")
        if self.replaces_human_expert:
            raise ValueError("real human review cannot replace a human expert")

    def _validate_non_authoritative(self) -> None:
        if self.human_review_imported or self.allows_dossier_generation:
            raise ValueError("non-authoritative review cannot unlock dossier generation")
        if self.serious_mode_importable:
            raise ValueError("non-authoritative review cannot be serious-mode importable")
        if self.decision == GenericReviewDecisionValue.ACCEPT_FOR_SERIOUS_DOSSIER:
            raise ValueError("non-authoritative review cannot accept for serious dossier")
