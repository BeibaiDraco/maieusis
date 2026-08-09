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
    """Coding-host reasoning-effort values.

    Codex accepts every value and REQUIRES one. Claude Code exposes an equivalent CLI
    surface (``--effort``; verified against the official docs on 2026-07-20) accepting
    low/medium/high/xhigh; the field is OPTIONAL there and ``None`` keeps the CLI default.
    """

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


class ConfigDatasetAccessMode(StrEnum):
    ADD_DIR = "add_dir"
    EXTERNAL_READONLY = "external_readonly"


class ConfigModelThinking(StrEnum):
    """Whether a role's model reasons before answering. A closed taxonomy, so it is constrained
    at the source rather than left to prose.

    ``VENDOR_DEFAULT`` is the state this repository was actually in, and it is not the same as any
    single named value: omitting the parameter runs adaptive thinking on ``claude-sonnet-5`` and NO
    thinking on ``claude-opus-4-8``. Measured across the operator's capture archive, 249 of 489
    sonnet-5 replies carry a thinking block against 0 of 204 on opus-4-8. So a constant cannot
    restate the old behaviour for both, and picking one silently inverts the other.
    """

    VENDOR_DEFAULT = "vendor_default"
    ADAPTIVE = "adaptive"
    DISABLED = "disabled"


class ConfigModelEffort(StrEnum):
    """How much a role's model spends on reasoning and acting. Vendor-neutral names that both
    adapters map onto their own API.

    ``VENDOR_DEFAULT`` carries the same meaning as its thinking counterpart: send nothing. ``high``
    happens to be the API default on every model this repository can configure today, but pinning
    it would still put a key on the wire that was never there, and ``output_config`` is the object
    that also carries the structured-output format.
    """

    VENDOR_DEFAULT = "vendor_default"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"
    MAX = "max"


class ProviderModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str = "openai"  # mock | openai | anthropic (providers/models/factory.py)
    model: str = ""
    # Reasoning depth was a SILENT VENDOR DEFAULT until this field existed: the adapters sent no
    # thinking or effort parameter at all, so every role inherited whatever the vendor had chosen
    # that week. On the 2026-07-31 leg that meant adaptive thinking nobody asked for on the roles
    # running claude-sonnet-5, and it is where the novelty reviewer's refusals were generated -- the
    # refusing replies carry a thinking block and no text block, while every reply that parsed
    # carries a text block. Defaulting to VENDOR_DEFAULT keeps the wire byte-identical on every
    # model while making the choice exist, visible, and settable; naming a value here instead would
    # silently switch thinking ON for the claude-opus-4-8 roles, including the reviewer the release
    # gate requires.
    thinking: ConfigModelThinking = ConfigModelThinking.VENDOR_DEFAULT
    effort: ConfigModelEffort = ConfigModelEffort.VENDOR_DEFAULT


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
    #: Read each paper's citing sentences with a coding agent instead of the regex extractor.
    #: OFF by default because it needs a logged-in subscription CLI, which CI and a fresh checkout
    #: do not have -- but a profile that can spawn one should set it, because the regex it replaces
    #: covers 5.7% of cited works on an assumption (square-bracket markers) that is false for every
    #: paper measured, against 91% for the agent. When it is off the artifact says
    #: `citation_context_reader=regex_fallback` rather than leaving the reader anonymous.
    citation_contexts_by_agent: bool = False
    #: Papers read concurrently, one short session each. They do not inform each other, so this is
    #: pure wall-clock: 70 s per paper three-up against 302 s serial.
    citation_context_agent_parallel: int = Field(default=4, ge=1, le=16)
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
    # The novelty reviewer alone, when it must differ from every other reviewer role. ``None`` means
    # "use ``reviewer``", so an existing config is unchanged in behaviour AND in every digest.
    #
    # It exists because one vendor's safety classifier can make one role unusable while every other
    # role is fine, and `reviewer` is shared by the front-half gates, the plan reviewer, and four
    # stage model-identity signatures -- switching it moves all of them, and would also trip the
    # preflight rule that owner and reviewer must be distinct providers. Measured on the
    # 2026-07-31 climate leg's own packets: `claude-sonnet-5` lost 50% of reviews to a biosecurity
    # classifier firing on stratospheric wave-forcing reasoning (25% with thinking disabled), while
    # `gpt-5.6-terra` lost 0 of 60 and returned the same 50/50 pass-hold split -- i.e. its
    # robustness was not bought with laxity, unlike `gpt-5.6-luna`, which passed 17 of 22 and
    # disagreed with BOTH other reviewers in the permissive direction on three variants.
    #
    # Deliberately here rather than under ``novelty``: the Stage-D config digest dumps
    # ``config.novelty`` wholesale, so a field there would move every existing receipt and make a
    # resume re-pay the run. Nothing dumps ``config.models`` wholesale.
    novelty_reviewer: ProviderModel | None = None
    coding_host: CodingHost  # REQUIRED typed choice — never the silent FakePlannerHost
    # The coding-agent host is a subscription CLI, not one of the token-API roles above. Its model
    # is nevertheless an explicit scientific-run input and must never fall back to user-global CLI
    # configuration. Both hosts expose a reasoning-effort knob: Codex requires it; Claude Code
    # accepts an optional low/medium/high/xhigh value (None keeps the CLI default).
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
        elif self.coding_reasoning_effort is CodingReasoningEffort.MINIMAL:
            # Claude Code's effort surface has no 'minimal' level; fail closed at construction
            # instead of at CLI spawn time inside a paid run.
            raise ValueError(
                "Claude Code coding_reasoning_effort must be one of low/medium/high/xhigh"
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


class NoveltyWebToolRateCard(StrEnum):
    """Pinned vendor web-tool price snapshots permitted by strict N-2 grounding.

    This is intentionally a small, closed enum rather than a user-editable decimal price.  The
    N-2 reservation ceiling is meaningful only when the per-search tool charge is pinned to a
    reviewable rate-card identity.  It covers the vendor's web-tool fee, *not* model-token spend.
    """

    ANTHROPIC_DIRECT_WEB_SEARCH_20250305 = "anthropic_direct_web_search_20250305"


_NOVELTY_WEB_TOOL_RATE_MICRO_USD: dict[NoveltyWebToolRateCard, int] = {
    NoveltyWebToolRateCard.ANTHROPIC_DIRECT_WEB_SEARCH_20250305: 10_000,
}


def novelty_web_tool_rate_micro_usd(rate_card: NoveltyWebToolRateCard) -> int:
    """Return the fixed web-tool fee snapshot for a configured N-2 rate card."""

    return _NOVELTY_WEB_TOOL_RATE_MICRO_USD[rate_card]


class NoveltyWebGroundingConfig(BaseModel):
    """Explicit, default-off configuration for N-2's independent web scout.

    ``scout`` is deliberately separate from ``models.reviewer``.  The reviewer remains the
    citation-bound N-1 judge; the scout is a narrowly scoped tool user with independently
    configured provider/model identity.  When this lane is disabled its incomplete placeholder
    defaults cannot construct a provider or cause egress.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    scout: ProviderModel = Field(default_factory=lambda: ProviderModel(provider="anthropic"))
    max_searches_per_scout: int = Field(default=3, ge=1, le=8)
    max_leads_per_scout: int = Field(default=5, ge=1, le=8)
    # `max_tokens` bounds the WHOLE reply, including the model's digestion of the search results
    # AND — on a thinking model — the thinking block, so a three-search scout carrying fifty-odd
    # sources runs out mid-answer and returns no parsable structured output at all, losing the
    # entire paid call. Four of twelve died this way in one live leg (2026-07-25); an explicit
    # 8_192 was the fix available at the time, and the cap then FROZE the lane at that value.
    #
    # The scout on every live profile is `claude-sonnet-5` through `AnthropicWebSearchProvider`,
    # which is the same non-streaming Anthropic transport that truncated 5 of 408 gate turns at
    # 8_192 (see `ANTHROPIC_MAX_OUTPUT_TOKENS`). Same vendor, same shared budget, same exposure —
    # so the bound is that constant's value, which is itself the largest the transport accepts.
    # Written as a literal because `schemas` never imports `providers` and inverting that layering
    # for one integer would be worse than the drift; `tests/test_upd2_web_scout_gets_room.py` pins
    # the two equal instead. Operator-authorized 2026-08-03.
    #
    # The DEFAULT deliberately stays at 2_048, and the original comment here was RIGHT that moving
    # it is release truth rather than a preference -- checked the hard way. Raising it to 21_000
    # turned 34 `test_release_validation_pair` tests red with "config must keep the frozen
    # novelty-off profile": the release-pair fixtures OMIT this field, so the schema default is
    # what the frozen profile pins. Only the CAP was ever the blocker; every real profile sets the
    # value explicitly, so the raise reaches them without touching what v0.1.0 ran with.
    max_output_tokens: int = Field(default=2_048, ge=128, le=21_000)
    rate_card: NoveltyWebToolRateCard = NoveltyWebToolRateCard.ANTHROPIC_DIRECT_WEB_SEARCH_20250305
    # A hard reservation ceiling for the web-tool fee only.  The separately metered model-token
    # cost is disclosed by preflight but cannot be represented honestly as a hard total cap.
    hard_run_tool_spend_ceiling_micro_usd: int = Field(default=500_000, ge=0)

    @property
    def web_tool_rate_micro_usd(self) -> int:
        """The fixed per-search fee for the selected, reviewable rate card."""

        return novelty_web_tool_rate_micro_usd(self.rate_card)

    @model_validator(mode="after")
    def validate_enabled_grounding(self) -> NoveltyWebGroundingConfig:
        if not self.enabled:
            return self
        if not self.scout.provider.strip():
            raise ValueError("enabled novelty web grounding requires an explicit scout provider")
        if not self.scout.model.strip():
            raise ValueError("enabled novelty web grounding requires an explicit scout model")
        one_scout_reservation = self.max_searches_per_scout * self.web_tool_rate_micro_usd
        if self.hard_run_tool_spend_ceiling_micro_usd < one_scout_reservation:
            raise ValueError(
                "novelty web-tool ceiling cannot fund even one configured scout reservation"
            )
        return self


class NoveltyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Backward-compatible and spend-safe default for v0.1 projects that omit the new Card 3 gate.
    # Serious UPD2 configurations must opt in explicitly; an unassessed run cannot make a
    # novelty-admitted planning claim.
    enabled: bool = False
    # Compatibility-only recall ranking controls. They never produce the v2 scientific verdict.
    direct_recap_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    close_prior_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_candidates: int = Field(default=5, ge=1)
    # N-2 is an independent, bounded web-discovery lane.  Its nested default is disabled so
    # existing v0.1 configurations load unchanged and construct no web provider.
    web_grounding: NoveltyWebGroundingConfig = Field(default_factory=NoveltyWebGroundingConfig)

    @model_validator(mode="after")
    def require_novelty_admission_for_web_grounding(self) -> NoveltyConfig:
        if self.web_grounding.enabled and not self.enabled:
            raise ValueError("novelty web grounding requires novelty.enabled=true")
        return self


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

    @model_validator(mode="before")
    @classmethod
    def disable_demo_web_before_nested_validation(cls, value: object) -> object:
        """Let demo mode coerce an otherwise incomplete default-off web block before it validates."""

        if not isinstance(value, dict) or value.get("mode") != ProductMode.SUBSCRIPTION_ONLY_DEMO:
            return value
        copied = dict(value)
        novelty_raw = copied.get("novelty")
        novelty = dict(novelty_raw) if isinstance(novelty_raw, dict) else {}
        web_raw = novelty.get("web_grounding")
        web_grounding = dict(web_raw) if isinstance(web_raw, dict) else {}
        novelty["enabled"] = False
        web_grounding["enabled"] = False
        novelty["web_grounding"] = web_grounding
        copied["novelty"] = novelty
        return copied

    @model_validator(mode="after")
    def apply_mode_and_reject_secrets(self) -> MaieusisProjectConfig:
        # Demo disables all live literature/novelty egress and cannot earn novelty admission.
        if self.mode == ProductMode.SUBSCRIPTION_ONLY_DEMO:
            self.literature.enabled = False
            self.novelty.enabled = False
            self.novelty.web_grounding.enabled = False
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
