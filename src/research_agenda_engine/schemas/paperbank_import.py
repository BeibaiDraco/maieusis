"""Typed provenance for a receipt-bound cross-run PaperBank import."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _require_digest(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise ValueError("expected a lowercase SHA-256 digest")
    return normalized


def _require_run_relative_paths(values: dict[str, str]) -> dict[str, str]:
    for raw_path, raw_digest in values.items():
        path = PurePosixPath(raw_path)
        if path.is_absolute() or not path.parts or ".." in path.parts or "." in path.parts:
            raise ValueError(f"imported output path must be run-relative: {raw_path!r}")
        _require_digest(raw_digest)
    return dict(sorted(values.items()))


class PaperBankImportReceipt(BaseModel):
    """What was reused, without persisting the operator's absolute source path."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "paperbank_import_receipt/v1"
    source_run_id: str
    source_paper_half_receipt_sha256: str
    source_input_digests: dict[str, str] = Field(default_factory=dict)
    imported_output_digests: dict[str, str] = Field(default_factory=dict)
    parser: str
    implementation_version: str
    config_version: str
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    model_versions: dict[str, str] = Field(default_factory=dict)
    imported_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("source_run_id")
    @classmethod
    def require_source_run_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or "/" in normalized or "\\" in normalized or normalized in {".", ".."}:
            raise ValueError("source_run_id must be one run-directory name")
        return normalized

    @field_validator("source_paper_half_receipt_sha256")
    @classmethod
    def validate_receipt_digest(cls, value: str) -> str:
        return _require_digest(value)

    @field_validator("source_input_digests")
    @classmethod
    def validate_input_digests(cls, value: dict[str, str]) -> dict[str, str]:
        return {key: _require_digest(digest) for key, digest in sorted(value.items())}

    @field_validator("imported_output_digests")
    @classmethod
    def validate_output_digests(cls, value: dict[str, str]) -> dict[str, str]:
        return _require_run_relative_paths(value)
