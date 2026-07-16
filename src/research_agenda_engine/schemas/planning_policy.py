from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FullLocalDataPlanningPolicy(BaseModel):
    """Human-authorized local data access policy for planning-only inspection."""

    model_config = ConfigDict(extra="forbid")

    authorized: bool = False
    local_only: bool = True
    allowed_read_roots: list[str] = Field(default_factory=list)
    allowed_read_classes: list[str] = Field(default_factory=list)
    persisted_output_classes: list[str] = Field(default_factory=list)
    forbidden_persisted_outputs: list[str] = Field(default_factory=list)
    forbidden_computation_classes: list[str] = Field(default_factory=list)
    one_cache_read_allowed: bool = False
    network_allowed: bool = False
    downloads_allowed: bool = False
    credentials_allowed: bool = False
    full_analysis_allowed: bool = False
    result_computation_allowed: bool = False
    redaction_required: bool = True
    bounded_structural_reads_only: bool = True

    @field_validator(
        "allowed_read_roots",
        "allowed_read_classes",
        "persisted_output_classes",
        "forbidden_persisted_outputs",
        "forbidden_computation_classes",
    )
    @classmethod
    def require_clean_text_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_authorized_scope(self) -> FullLocalDataPlanningPolicy:
        if not self.authorized:
            return self
        required_lists = {
            "allowed_read_roots": self.allowed_read_roots,
            "allowed_read_classes": self.allowed_read_classes,
            "persisted_output_classes": self.persisted_output_classes,
            "forbidden_persisted_outputs": self.forbidden_persisted_outputs,
            "forbidden_computation_classes": self.forbidden_computation_classes,
        }
        missing = [name for name, values in required_lists.items() if not values]
        if missing:
            raise ValueError("authorized full-local policy requires " + ", ".join(missing))
        roots = "\n".join(self.allowed_read_roots).lower()
        if "bwm_ephys:" not in roots or "bwm_behavior:" not in roots:
            raise ValueError(
                "authorized full-local policy requires bwm_ephys and bwm_behavior roots"
            )
        if not self.local_only:
            raise ValueError("full-local policy must remain local_only")
        if self.network_allowed:
            raise ValueError("full-local policy cannot allow network access")
        if self.downloads_allowed:
            raise ValueError("full-local policy cannot allow downloads")
        if self.credentials_allowed:
            raise ValueError("full-local policy cannot allow credentials")
        if self.full_analysis_allowed:
            raise ValueError("full-local policy cannot allow full analysis")
        if self.result_computation_allowed:
            raise ValueError("full-local policy cannot allow result computation")
        if not self.redaction_required:
            raise ValueError("full-local policy requires redaction")
        if not self.bounded_structural_reads_only:
            raise ValueError("full-local policy requires bounded structural reads only")
        return self
