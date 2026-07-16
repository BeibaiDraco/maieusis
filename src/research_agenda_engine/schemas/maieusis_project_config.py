"""MaieusisProjectConfig — the user's single ``maieusis.yaml`` for an end-to-end run.

Versioned, ``extra="forbid"`` config covering EVERY input the e2e run consumes. Secrets are NEVER in
this file: API keys/tokens load via ``config.load_runtime_env`` (``.env.local`` / ``runtime.env`` /
``~/.config/maieusis/runtime.env``); this config holds only env-var NAMES and non-secret settings, and a
validator rejects anything key-shaped.

Two modes (I/O contract): ``standard`` (token API present → full automated generation + independent
review) and ``subscription_only_demo`` (NO token API → the API-agent providers resolve to ``mock``,
novelty + literature are disabled, and a loud banner flags "workflow demo only, no scientific-quality
guarantee"). The mode fans out to those defaults.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .research_intent import ResearchIntent
from .topic_literature import TopicSourceProfile


class ProductMode(StrEnum):
    STANDARD = "standard"
    SUBSCRIPTION_ONLY_DEMO = "subscription_only_demo"


class CodingHost(StrEnum):
    CODEX = "codex"
    CLAUDE_CODE = "claude_code"


class CodingReasoningEffort(StrEnum):
    """Codex CLI reasoning-effort values; Claude Code has no equivalent config surface."""

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


class ConfigDatasetAccessMode(StrEnum):
    ADD_DIR = "add_dir"
    EXTERNAL_READONLY = "external_readonly"


class ProviderModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = "openai"  # mock | openai | anthropic (providers/models/factory.py)
    model: str = ""


class PaperBankImportConfig(BaseModel):
    """Receipt-bound reuse of a completed paper half from another Maieusis run."""

    model_config = ConfigDict(extra="forbid")

    source_run_root: Path
    expected_receipt_sha256: str

    @field_validator("expected_receipt_sha256")
    @classmethod
    def require_sha256(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", normalized):
            raise ValueError("expected_receipt_sha256 must be a lowercase SHA-256 digest")
        return normalized


class PaperBankConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inbox_dir: Path
    extraction: ProviderModel = Field(default_factory=ProviderModel)
    parser: str = "poppler_text"
    evidence_mode: str = "source_span"  # v7 product default
    max_workers: int = Field(default=4, ge=1)
    cited_literature: bool = True
    select_key_citations: bool = True
    # P1: pull a paper's whole reference list from a DOI-keyed source-reference provider (Crossref /
    # OpenAlex) when PDF reference parsing yields fewer than min_local_reference_count entries.
    external_reference_fallback: bool = True
    min_local_reference_count: int = Field(default=10, ge=0)
    crossref_mailto: str = ""
    openalex_email: str = ""
    citation_prompt_char_budget: int = Field(default=120_000, ge=1)
    # Optional cross-run paper-half reuse. The source path is operational only: the current PDF
    # filename+byte digests, receipt, config, prompts, models, and outputs remain the identity.
    import_from_run: PaperBankImportConfig | None = None


class DatasetSeedConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    # Link is optional when readable user description docs provide Source-D narrative evidence.
    link: str = ""
    docs: list[Path] = Field(default_factory=list)


class InspectionRuntimeConfig(BaseModel):
    """The per-format inspection RUNTIME — the RUNNER-constructor surface (SEPARATE from resources)."""

    model_config = ConfigDict(extra="forbid")

    dataset_root: Path | None = None
    dataset_access_mode: ConfigDatasetAccessMode = ConfigDatasetAccessMode.EXTERNAL_READONLY
    inspection_python: str = ""
    inspection_command: str = ""
    inspection_pythonpath: str = ""
    inspection_extra_env: dict[str, str] = Field(default_factory=dict)
    # Optional explicit checkout whose Git digest is sampled before/after a real coding-agent
    # spawn. Required when the installed product is launched outside a Git worktree.
    source_tree_root: Path | None = None
    max_turns: int = Field(default=40, ge=1)
    # Final-quality planning may need a little more time for a complete evidence-backed plan.
    # Keep the default at 30 minutes, but permit an explicit 40-minute bounded release profile.
    timeout_seconds: int = Field(default=1800, gt=0, le=2400)

    @model_validator(mode="after")
    def validate_runtime(self) -> InspectionRuntimeConfig:
        if self.inspection_python and self.inspection_command:
            raise ValueError("inspection_python and inspection_command are mutually exclusive")
        if (
            self.dataset_access_mode == ConfigDatasetAccessMode.EXTERNAL_READONLY
            and self.dataset_root is None
        ):
            raise ValueError("external_readonly dataset access requires dataset_root")
        return self


class DatasetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seed: DatasetSeedConfig
    inspection_runtime: InspectionRuntimeConfig
    # The allowed-resource STRING list (DatasetInspectionResources) — a DIFFERENT thing from the runtime.
    allowed_inspection_resources: list[str] = Field(default_factory=list)
    official_online_resources: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_resources(self) -> DatasetConfig:
        if not [r for r in self.allowed_inspection_resources if r.strip()]:
            raise ValueError("dataset requires at least one allowed_inspection_resource")
        return self


class ModelsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questioner: ProviderModel = Field(default_factory=ProviderModel)
    # Added after the original v1 config shipped. A before-validator copies ``questioner`` when an
    # old development YAML omits this field; new public templates always set it explicitly.
    pattern: ProviderModel = Field(default_factory=ProviderModel)
    narrator: ProviderModel = Field(default_factory=ProviderModel)
    topic: ProviderModel = Field(default_factory=ProviderModel)
    owner: ProviderModel = Field(default_factory=ProviderModel)
    reviewer: ProviderModel = Field(default_factory=lambda: ProviderModel(provider="anthropic"))
    coding_host: CodingHost  # REQUIRED typed choice — never the silent FakePlannerHost
    # The coding-agent host is a subscription CLI, not one of the token-API roles above. Its model
    # is nevertheless an explicit scientific-run input and must never fall back to user-global CLI
    # configuration. Codex additionally exposes a reasoning-effort knob; Claude Code does not.
    coding_model: str
    coding_reasoning_effort: CodingReasoningEffort | None = None
    allow_pro_model: bool = False

    @field_validator("coding_model")
    @classmethod
    def require_coding_model(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("coding_model must be a non-empty explicit coding-agent model")
        return normalized

    @model_validator(mode="after")
    def validate_coding_host_options(self) -> ModelsConfig:
        if self.coding_host == CodingHost.CODEX:
            if self.coding_reasoning_effort is None:
                raise ValueError("Codex coding_host requires coding_reasoning_effort")
        elif self.coding_reasoning_effort is not None:
            raise ValueError(
                "coding_reasoning_effort is a Codex-only option and must be omitted for Claude Code"
            )
        return self

    @model_validator(mode="before")
    @classmethod
    def legacy_pattern_falls_back_to_questioner(cls, value: object) -> object:
        if isinstance(value, dict) and "pattern" not in value:
            copied = dict(value)
            copied["pattern"] = copied.get("questioner", {})
            return copied
        return value

    @property
    def effective_pattern(self) -> ProviderModel:
        return self.pattern


class LiteratureConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    openalex_email: str = ""
    # Live-readiness LR-C: the targeted OA fulltext-excerpt plus-on (strengthens evidence, never a gate).
    # Off when literature is off; off in demo (literature is force-disabled below).
    fulltext_enrichment: bool = True
    # Opt-in paid literature source. Reuses the TopicSourceProfile taxonomy; the ELICIT key is NEVER in
    # config (it loads from runtime.env via os.getenv). `public` = free only (default); `auto` = HYBRID
    # iff ELICIT_API_KEY is present else PUBLIC (honest, no hard fail); `hybrid`/`elicit` = force (a
    # forced profile with no key fails closed in preflight). Default PUBLIC ⇒ a run with no knob spends
    # nothing on Elicit and behaves exactly as today.
    source_profile: TopicSourceProfile = TopicSourceProfile.PUBLIC


class NoveltyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Phase 6-E1: the product does not yet wire a real novelty search. Omitted means honestly off;
    # explicit true is rejected by preflight until that capability exists.
    enabled: bool = False
    direct_recap_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    close_prior_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_candidates: int = Field(default=5, ge=1)


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    output_root: Path
    shortlist_path: Path | None = None
    target_family_ids: list[str] = Field(default_factory=list)
    max_families: int = Field(default=2, ge=1)
    variants_per_family: int = Field(default=3, ge=1, le=8)
    max_parallel_family_workers: int = Field(default=2, ge=1)
    max_revise_rounds: int = Field(default=1, ge=0)
    # Parse-only migration shim. It is excluded from serialization and NEVER read by the driver.
    # The real timeout is dataset.inspection_runtime.timeout_seconds (per planner invocation,
    # shared by any bounded transport-retry process launches inside that invocation).
    legacy_timeout_seconds: int | None = Field(
        default=None, alias="timeout_seconds", exclude=True, gt=0
    )


# Reject any string value that looks like an API key/token (secrets must NEVER be in the config file).
_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"sk-ant-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{16,}\b"),
)


def _scan_for_secrets(value: object, path: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, str):
        for pattern in _SECRET_PATTERNS:
            if pattern.search(value):
                hits.append(path or "<root>")
                break
    elif isinstance(value, dict):
        for key, sub in value.items():
            hits.extend(_scan_for_secrets(sub, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, list):
        for index, sub in enumerate(value):
            hits.extend(_scan_for_secrets(sub, f"{path}[{index}]"))
    return hits


class MaieusisProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "maieusis_project_config/v1"
    mode: ProductMode
    paperbank: PaperBankConfig
    dataset: DatasetConfig
    research_intent: ResearchIntent = Field(default_factory=ResearchIntent)
    models: ModelsConfig
    literature: LiteratureConfig = Field(default_factory=LiteratureConfig)
    novelty: NoveltyConfig = Field(default_factory=NoveltyConfig)
    run: RunConfig

    @model_validator(mode="after")
    def apply_mode_and_reject_secrets(self) -> MaieusisProjectConfig:
        # Demo disables literature egress. Novelty already defaults off; an explicit true must remain
        # visible so preflight can reject the unsupported capability instead of silently coercing it.
        if self.mode == ProductMode.SUBSCRIPTION_ONLY_DEMO:
            self.literature.enabled = False
        secret_hits = _scan_for_secrets(self.model_dump(mode="python"))
        if secret_hits:
            raise ValueError(
                "MaieusisProjectConfig must not contain API keys/tokens (found key-shaped value at: "
                + ", ".join(secret_hits)
                + "). Put secrets in a runtime.env loaded by load_runtime_env."
            )
        return self

    @property
    def is_demo(self) -> bool:
        return self.mode == ProductMode.SUBSCRIPTION_ONLY_DEMO

    @property
    def demo_banner(self) -> str:
        return (
            "SUBSCRIPTION-ONLY DEMO: no token API — independent review incomplete; workflow demo only; "
            "NO scientific-quality guarantee."
        )

    def effective_provider(self, configured: ProviderModel) -> ProviderModel:
        """In demo mode every token-API (API-agent) provider resolves to ``mock`` (no token API)."""
        return ProviderModel(provider="mock", model="") if self.is_demo else configured
