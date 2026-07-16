from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import EvidenceKind, EvidenceMaturity, EvidenceSourceClass, VerificationStatus


class EvidenceRef(BaseModel):
    """A compact, immutable reference to evidence supporting a scientific artifact."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    kind: EvidenceKind
    location: str = ""
    source_version: str = ""
    verification_status: VerificationStatus = VerificationStatus.PROPOSED
    maturity: EvidenceMaturity = EvidenceMaturity.E1_DECLARED
    source_class: EvidenceSourceClass = EvidenceSourceClass.USER_DECLARED
    evidence_scope: str = ""
    dataset_version: str = ""
    artifact_uri: str = ""
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    checksum: str = ""
    assertion: str = ""
    collected_by: str = ""
    note: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("checksum")
    @classmethod
    def normalize_checksum(cls, value: str) -> str:
        value = value.strip().lower()
        if value.startswith("sha256:"):
            value = value.removeprefix("sha256:")
        return value

    @property
    def trust_weight(self) -> float:
        return self.verification_status.trust_weight


class EvidenceConflict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field_path: str
    candidate_values: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    resolution: str = "unresolved"
    note: str = ""


class ArtifactDigest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str
    size_bytes: int


class ProvenanceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    inputs: list[ArtifactDigest] = Field(default_factory=list)
    outputs: list[ArtifactDigest] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    conflicts: list[EvidenceConflict] = Field(default_factory=list)
    software_versions: dict[str, str] = Field(default_factory=dict)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def digest_file(path: str | Path, *, relative_to: str | Path | None = None) -> ArtifactDigest:
    path = Path(path)
    shown = path
    if relative_to is not None:
        try:
            shown = path.relative_to(Path(relative_to))
        except ValueError:
            shown = path
    return ArtifactDigest(
        path=shown.as_posix(), sha256=sha256_file(path), size_bytes=path.stat().st_size
    )


def stable_hash(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return sha256_bytes(payload)
