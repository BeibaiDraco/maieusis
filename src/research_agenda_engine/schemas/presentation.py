"""Presentation-only add-on records for detailed human-readable run views.

These records deliberately sit outside the six scientific stage receipts and the indexed scientific
artifact inventory. A missing or damaged presentation file is therefore redrawable; it can never
change scientific processing state or authority.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PresentationAddonState(StrEnum):
    NOT_REACHED = "not_reached"
    PRODUCED = "produced"
    WARNING = "warning"


class PresentationArtifactKind(StrEnum):
    QUESTION_PATTERNS_DETAILED = "question_patterns_detailed"
    QUESTION_FAMILIES_DETAILED = "question_families_detailed"
    FAMILY_DOSSIER_DETAILED = "family_dossier_detailed"


class PresentationArtifactRecord(BaseModel):
    """One current detailed projection; never part of scientific artifact integrity."""

    model_config = ConfigDict(extra="forbid")

    kind: PresentationArtifactKind
    path: str
    sha256: str
    family_id: str = ""

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        value = value.strip().replace("\\", "/")
        path = PurePosixPath(value)
        if not value or path.is_absolute() or ".." in path.parts or value.startswith("./"):
            raise ValueError("presentation paths must be normalized run-relative POSIX paths")
        if path.as_posix() != value:
            raise ValueError("presentation paths must be normalized run-relative POSIX paths")
        return value

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        value = value.strip().lower()
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("presentation sha256 must be lowercase hexadecimal")
        return value

    @model_validator(mode="after")
    def family_identity_matches_kind(self) -> PresentationArtifactRecord:
        is_family = self.kind == PresentationArtifactKind.FAMILY_DOSSIER_DETAILED
        if is_family != bool(self.family_id.strip()):
            raise ValueError("only family dossier presentation records carry family_id")
        return self


class PresentationAddonReceipt(BaseModel):
    """Current deterministic add-on attempt, bound only to persisted typed source bytes."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["presentation_addon_receipt/v1"] = "presentation_addon_receipt/v1"
    run_id: str
    status: PresentationAddonState
    input_digests: dict[str, str] = Field(default_factory=dict)
    config_version: Literal["presentation_addon/v1"] = "presentation_addon/v1"
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    model_versions: dict[str, str] = Field(default_factory=dict)
    output_paths: list[str] = Field(default_factory=list)
    expected_output_paths: list[str] = Field(default_factory=list)
    output_digests: dict[str, str] = Field(default_factory=dict)
    external_call_ids: list[str] = Field(default_factory=list)
    warning: str = ""
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("input_digests", "output_digests")
    @classmethod
    def validate_digest_maps(cls, value: dict[str, str]) -> dict[str, str]:
        for key, digest in value.items():
            path = PurePosixPath(key)
            if (
                not key.strip()
                or path.is_absolute()
                or ".." in path.parts
                or key.startswith("./")
                or path.as_posix() != key
                or not _SHA256_RE.fullmatch(digest)
            ):
                raise ValueError("presentation receipt digest maps require named sha256 values")
        return value

    @field_validator("output_paths", "expected_output_paths")
    @classmethod
    def validate_output_paths(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            path = PurePosixPath(value)
            if (
                not value
                or path.is_absolute()
                or ".." in path.parts
                or value.startswith("./")
                or path.as_posix() != value
            ):
                raise ValueError("presentation receipt paths must be normalized run-relative paths")
            normalized.append(value)
        if len(normalized) != len(set(normalized)):
            raise ValueError("presentation receipt output paths must be unique")
        return normalized

    @model_validator(mode="after")
    def enforce_zero_call_addon(self) -> PresentationAddonReceipt:
        if not self.run_id.strip():
            raise ValueError("presentation receipt requires run_id")
        if self.prompt_versions or self.model_versions or self.external_call_ids:
            raise ValueError("presentation add-on receipts cannot record prompts, models, or calls")
        if self.ended_at < self.started_at:
            raise ValueError("presentation receipt ended_at cannot precede started_at")
        if set(self.output_paths) != set(self.output_digests):
            raise ValueError("presentation receipt output paths and digests must match")
        if self.status == PresentationAddonState.PRODUCED:
            if self.warning.strip():
                raise ValueError("a produced presentation receipt cannot carry a warning")
            if set(self.output_paths) != set(self.expected_output_paths):
                raise ValueError("a produced presentation receipt requires every expected output")
        elif self.status == PresentationAddonState.WARNING:
            if not self.warning.strip():
                raise ValueError("a warning presentation receipt requires a public warning")
        else:
            raise ValueError("an attempt receipt must be produced or warning, never not_reached")
        return self


class PresentationAddonRecord(BaseModel):
    """Soft current pointer stored in ``RunManifest`` without altering scientific state."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["presentation_addon/v1"] = "presentation_addon/v1"
    state: PresentationAddonState = PresentationAddonState.NOT_REACHED
    receipt_path: str = ""
    outputs: list[PresentationArtifactRecord] = Field(default_factory=list)
    warning: str = ""

    @field_validator("receipt_path")
    @classmethod
    def validate_optional_receipt_path(cls, value: str) -> str:
        if not value:
            return value
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or ".." in path.parts
            or value.startswith("./")
            or path.as_posix() != value
        ):
            raise ValueError("presentation receipt path must be normalized and run-relative")
        return value

    @model_validator(mode="after")
    def state_matches_current_attempt(self) -> PresentationAddonRecord:
        paths = [item.path for item in self.outputs]
        if len(paths) != len(set(paths)):
            raise ValueError("presentation output paths must be unique")
        family_ids = [
            item.family_id
            for item in self.outputs
            if item.kind == PresentationArtifactKind.FAMILY_DOSSIER_DETAILED
        ]
        if len(family_ids) != len(set(family_ids)):
            raise ValueError("presentation family dossier records must have unique family IDs")
        if self.state == PresentationAddonState.NOT_REACHED:
            if self.receipt_path or self.outputs or self.warning:
                raise ValueError("not_reached presentation record cannot carry attempt data")
        elif self.state == PresentationAddonState.PRODUCED:
            if not self.receipt_path or self.warning:
                raise ValueError("produced presentation record requires a receipt and no warning")
        elif not self.receipt_path or not self.warning.strip():
            raise ValueError("warning presentation record requires receipt and public warning")
        return self
