"""Typed closure outcomes for failures after scientific review accepted a family."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .family_failure import SAFE_FAMILY_FAILURE_REASON, sanitize_family_failure_text
from .stage_receipt import FailureClass


class DossierClosureOutcome(StrEnum):
    PUBLIC_DOSSIER_REVISION_REQUIRED = "public_dossier_revision_required"
    PROVENANCE_INTEGRITY_TERMINAL = "provenance_integrity_terminal"


class DossierClosureDiagnostic(BaseModel):
    """Durable account of why an independently accepted dossier did not publish."""

    model_config = ConfigDict(extra="forbid")

    diagnostic_id: str
    code: DossierClosureOutcome
    stage: Literal["dossier_closure"] = "dossier_closure"
    run_id: str
    branch_id: str
    question_family_id: str
    failure_class: FailureClass | None = None
    reason: str
    errors: list[str] = Field(default_factory=list)
    retained_artifact_paths: list[str]
    omitted_public_artifact_paths: list[str] = Field(default_factory=list)
    observed_bindings: dict[str, str] = Field(default_factory=dict)
    expected_bindings: dict[str, str] = Field(default_factory=dict)
    accepted_upstream_retained: Literal[True] = True
    public_dossier_published: Literal[False] = False
    final_dossier_created: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    execution_authorized: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("diagnostic_id", "run_id", "branch_id", "question_family_id")
    @classmethod
    def require_identity_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("dossier closure identity fields must be non-empty")
        return value

    @field_validator("reason")
    @classmethod
    def sanitize_reason(cls, value: str) -> str:
        value = sanitize_family_failure_text(value)
        if not value:
            raise ValueError("dossier closure reason must be non-empty")
        return value

    @field_validator("errors")
    @classmethod
    def sanitize_errors(cls, value: list[str]) -> list[str]:
        cleaned_errors: list[str] = []
        for item in value:
            normalized = " ".join(item.split())
            cleaned = sanitize_family_failure_text(normalized)
            if cleaned and cleaned != SAFE_FAMILY_FAILURE_REASON:
                cleaned_errors.append(cleaned)
                continue
            # Keep the bounded validator category while removing the value that triggered the
            # sanitizer (for example an internal branch ID after the first colon).
            category = normalized.partition(":")[0].strip()
            safe_category = sanitize_family_failure_text(category)
            if safe_category:
                cleaned_errors.append(safe_category + ": [redacted]")
        return cleaned_errors

    @field_validator("retained_artifact_paths", "omitted_public_artifact_paths")
    @classmethod
    def clean_paths(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("dossier closure artifact paths must be unique")
        return cleaned

    @field_validator("observed_bindings", "expected_bindings")
    @classmethod
    def clean_bindings(cls, value: dict[str, str]) -> dict[str, str]:
        cleaned = {str(key).strip(): str(item).strip() for key, item in value.items()}
        if any(not key or not item for key, item in cleaned.items()):
            raise ValueError("dossier closure bindings must be non-empty strings")
        return cleaned

    @model_validator(mode="after")
    def validate_failure_taxonomy(self) -> DossierClosureDiagnostic:
        if not self.retained_artifact_paths:
            raise ValueError("dossier closure requires retained artifact paths")
        if set(self.retained_artifact_paths) & set(self.omitted_public_artifact_paths):
            raise ValueError("retained and omitted dossier paths must be disjoint")
        if self.code == DossierClosureOutcome.PUBLIC_DOSSIER_REVISION_REQUIRED:
            if self.failure_class is not None:
                raise ValueError("public dossier revision is a quality outcome, not infrastructure")
            if not self.errors:
                raise ValueError("public dossier revision requires quality errors")
            if not self.omitted_public_artifact_paths:
                raise ValueError("public dossier revision requires omitted public artifact paths")
        else:
            if self.failure_class != FailureClass.VALIDATION_FAILURE:
                raise ValueError("provenance-integrity terminal requires validation_failure")
            if not self.errors:
                raise ValueError("provenance-integrity terminal requires validation errors")
        return self
