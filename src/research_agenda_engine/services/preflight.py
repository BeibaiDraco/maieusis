"""`maieusis check` preflight — verify every e2e input, ZERO paid calls on ANY failure.

The preflight body contains NO ``.send`` / ``.generate_structured`` / runner ``.run`` / orchestrator
call. It does cheap/static work plus, for the explicit product ``check`` command, one free OpenAlex
quota probe: file existence, ``shutil.which`` + login-presence, exact dialogue-runtime imports,
source-tree Git validation, CONSTRUCTING providers (construction is free — it proves the key is
present + the model is tier-authorized; paid ``send``/``research_structured`` calls are never reached),
CONSTRUCTING the runner (validates the inspection runtime; never spawns), static id compares, a
write-probe, and static estimates + an egress disclosure.

Zero-paid is guaranteed structurally and TESTED: ``build_provider`` /
``build_novelty_web_provider`` / ``build_runner`` are injectable so tests inject spies whose
``send`` / ``research_structured`` / ``run`` raise; every path (happy + each failure) asserts the
spy was never called. The OpenAlex probe is injectable and defaults off for non-check callers. Demo
mode (no token API) resolves the API-agent providers to ``mock`` and does NOT require token-API
keys — only the coding host is checked (F2).

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ..providers.coding_agents.spawn_sandbox import default_lead_codex_home
from ..providers.coding_agents.subprocess_utils import detect_repo_root, source_tree_digest
from ..providers.models.factory import build_model_provider
from ..providers.models.policy import ensure_model_allowed
from ..providers.models.web_search_provider import (
    build_novelty_web_search_provider,
    require_strict_novelty_web_capability,
)
from ..schemas.maieusis_project_config import (
    CodingHost,
    ConfigDatasetAccessMode,
    MaieusisProjectConfig,
    ProviderModel,
)
from ..schemas.topic_literature import TopicSourceProfile
from .dossier.development_review_dossier import _MAX_REVIEW_ARTIFACT_REATTEMPTS
from .orchestration.paperbank_import import PaperBankImportError, validate_paperbank_import
from .paper_ingest.external_lookup import ExternalLookupError, probe_openalex_quota
from .retrieval.dataset_seed_retrieval import resolve_seed_link
from .retrieval.topic_sources import resolve_topic_source_profile

_ELICIT_PROFILES = (TopicSourceProfile.ELICIT, TopicSourceProfile.HYBRID)

_KEY_ENV = {
    "openai": ("OPENAI_API_KEY", "OPENAI_MODEL"),
    "anthropic": ("ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"),
}

BuildProvider = Callable[..., object]
BuildNoveltyWebProvider = Callable[..., object]
BuildRunner = Callable[[MaieusisProjectConfig], object]
Which = Callable[[str], str | None]
OpenAlexProbe = Callable[[], None]
DialogueRuntimeProbe = Callable[[], None]
SourceTreeProbe = Callable[[str | Path], object]
DatasetSeedProbe = Callable[[str, str], list[object]]
CodexVersionProbe = Callable[[str], str]
ClaudeVersionProbe = Callable[[str], str]

_MIN_TERRA_CODEX_VERSION = (0, 144, 4)
_CODEX_VERSION_PATTERN = re.compile(r"\bcodex-cli\s+(\d+)\.(\d+)\.(\d+)\b")
# The dual-host parity floor: the Claude Code version audited at the 2026-07-19 host takeover.
_MIN_CLAUDE_CODE_VERSION = (2, 1, 201)
_CLAUDE_VERSION_PATTERN = re.compile(r"\b(\d+)\.(\d+)\.(\d+)\b")
# N-2 permits the initial scout plus at most one cite-bound ``-novelty-r1`` scout.  This is a
# scientific/product bound, not a reflection of the generic pattern-revision setting.
_NOVELTY_WEB_SCOUT_PASSES_PER_VARIANT = 2


class PreflightCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    ok: bool
    message: str
    warning: bool = False


class PreflightReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checks: list[PreflightCheck] = Field(default_factory=list)
    estimates: dict[str, str] = Field(default_factory=dict)
    egress_disclosure: list[str] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def failures(self) -> list[PreflightCheck]:
        return [check for check in self.checks if not check.ok]


def run_preflight(
    config: MaieusisProjectConfig,
    *,
    build_provider: BuildProvider = build_model_provider,
    build_novelty_web_provider: BuildNoveltyWebProvider = build_novelty_web_search_provider,
    build_runner: BuildRunner | None = None,
    which: Which = shutil.which,
    home: Path | None = None,
    probe_dataset_seed: bool = False,
    dataset_seed_probe: DatasetSeedProbe | None = None,
    probe_openalex: bool = False,
    openalex_probe: OpenAlexProbe = probe_openalex_quota,
    dialogue_runtime_probe: DialogueRuntimeProbe | None = None,
    source_tree_probe: SourceTreeProbe | None = None,
    codex_version_probe: CodexVersionProbe | None = None,
    claude_version_probe: ClaudeVersionProbe | None = None,
) -> PreflightReport:
    """Run the preflight over a validated config; return a report (never proceeds to a run)."""
    checks: list[PreflightCheck] = []

    def add(name: str, ok: bool, message: str, *, warning: bool = False) -> None:
        checks.append(PreflightCheck(name=name, ok=ok, message=message, warning=warning))

    # --- PaperBank: PDFs exist + >=1 non-empty (parseability proxy; full parse-only runs at run time) --
    inbox = config.paperbank.inbox_dir
    pdfs = sorted(inbox.glob("*.pdf")) if inbox.exists() else []
    usable = [pdf for pdf in pdfs if pdf.is_file() and pdf.stat().st_size > 0]
    add("paperbank.inbox_exists", inbox.exists(), f"PDF inbox {inbox}")
    add("paperbank.has_usable_pdf", bool(usable), f"{len(usable)} non-empty PDF(s) in {inbox}")
    # The configured parser's system binary. Without this the preflight passed, the user approved a
    # paid run, and the run then died in parsing.py on a missing binary -- after the money started.
    # Preflight is the only place that costs nothing to fail in.
    parser = config.paperbank.parser.strip().lower()
    # Demo mode never reaches the parser -- verified by running the demo end to end against a
    # pdftotext that exits non-zero if invoked; it is never called. Requiring the binary there
    # would block the zero-cost on-ramp the documentation recommends as a first step.
    if not config.is_demo and parser in {"poppler_text", "auto"}:
        # Through the injected `which`, like every other executable probe here. Calling
        # shutil.which directly made this check depend on whatever happens to be installed on the
        # machine running the tests, which turned every hermetic preflight test red on a runner
        # without Poppler.
        pdftotext = which("pdftotext")
        add(
            "paperbank.parser_binary",
            pdftotext is not None or parser == "auto",
            (
                f"parser {parser!r}: pdftotext {'found at ' + pdftotext if pdftotext else 'NOT on PATH'}"
                + (
                    ""
                    if pdftotext
                    else " -- install Poppler (brew install poppler / apt install poppler-utils)"
                )
            ),
            warning=parser == "auto" and pdftotext is None,
        )
    paperbank_import_ok = True
    if config.paperbank.import_from_run is not None:
        try:
            verified_import = validate_paperbank_import(config)
            assert verified_import is not None
            add(
                "paperbank.import_from_run",
                True,
                f"receipt-bound source run {verified_import.source_root.name!r} verified",
            )
        except PaperBankImportError as exc:
            paperbank_import_ok = False
            add("paperbank.import_from_run", False, str(exc))

    # --- Dataset seed: Source A link OR at least one readable Source D description ------------------
    seed = config.dataset.seed
    readable_docs: list[Path] = []
    for index, doc in enumerate(seed.docs):
        try:
            readable = doc.is_file() and doc.stat().st_size > 0
        except OSError:
            readable = False
        if readable:
            readable_docs.append(doc)
        add(f"dataset.doc[{index}]", readable, f"readable non-empty doc {doc}")
    add(
        "dataset.seed_source",
        bool(seed.link.strip()) or bool(readable_docs),
        "dataset seed requires a link or at least one readable non-empty description doc",
    )
    # The subscription-only demo is an offline engineering baseline and may deliberately use fixture
    # URLs. Serious standard-mode check/run/resume must prove that a real link yields substantive text.
    if probe_dataset_seed and seed.link.strip() and not config.is_demo:
        probe = dataset_seed_probe or _probe_dataset_seed_link
        try:
            excerpts = probe(seed.link, seed.dataset_id)
            substantive = [
                item
                for item in excerpts
                if not bool(getattr(item, "is_metadata_only", False))
                and bool(str(getattr(item, "excerpt", "")).strip())
            ]
            link_ok = bool(substantive)
            docs_are_fallback = bool(readable_docs)
            add(
                "dataset.seed_link_content",
                link_ok or docs_are_fallback,
                (
                    f"dataset link resolved to {len(substantive)} substantive excerpt(s)"
                    if link_ok
                    else (
                        "dataset link yielded metadata only; readable seed.docs remain available"
                        if docs_are_fallback
                        else "dataset link yielded metadata only; provide a substantive public link or seed.docs"
                    )
                ),
                warning=not link_ok and docs_are_fallback,
            )
        except Exception as exc:
            docs_are_fallback = bool(readable_docs)
            add(
                "dataset.seed_link_content",
                docs_are_fallback,
                (
                    f"dataset link probe failed ({type(exc).__name__}: {exc}); "
                    + (
                        "readable seed.docs remain available"
                        if docs_are_fallback
                        else "provide a reachable substantive public link or seed.docs"
                    )
                ),
                warning=docs_are_fallback,
            )

    # --- Inspection RUNTIME (validated by the config schema) + resources + runner construction -------
    runtime = config.dataset.inspection_runtime
    add(
        "dataset.inspection_resources",
        bool(config.dataset.allowed_inspection_resources),
        "resource list",
    )
    if runtime.dataset_access_mode == ConfigDatasetAccessMode.EXTERNAL_READONLY:
        root_ok = runtime.dataset_root is not None and runtime.dataset_root.exists()
        add("dataset.dataset_root", root_ok, f"dataset_root {runtime.dataset_root}")

    # Standard family planning always starts the local dialogue MCP service and samples a Git source
    # tree before the coding-agent spawn. Probe those exact late dependencies now, before any model
    # call. Demo uses FakePlannerHost and deliberately needs neither optional MCP dependencies nor a
    # source checkout.
    if not config.is_demo:
        runtime_probe = dialogue_runtime_probe or _probe_dialogue_runtime
        try:
            runtime_probe()
            add("dataset.dialogue_runtime", True, "MCP dialogue runtime imports successfully")
        except (AttributeError, ImportError) as exc:
            add(
                "dataset.dialogue_runtime",
                False,
                "MCP dialogue runtime is unavailable "
                f"({type(exc).__name__}: {exc}); install it with `pip install 'maieusis[mcp]'`",
            )

        git_root = runtime.source_tree_root
        tree_probe = source_tree_probe or source_tree_digest
        try:
            if git_root is None:
                git_root = detect_repo_root()
            tree_probe(git_root)
            add("dataset.source_tree_git", True, f"Git source tree with HEAD at {git_root}")
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            configured = (
                str(git_root) if git_root is not None else "auto-detected working directory"
            )
            add(
                "dataset.source_tree_git",
                False,
                f"source_tree_root {configured} is not a usable Git checkout with HEAD: {exc}",
            )

    runner_builder = build_runner or _build_default_runner
    try:
        runner_builder(config)  # constructs (validates runtime); NEVER spawns
        add("dataset.runner_constructs", True, "inspection runner constructs (no spawn)")
    except Exception as exc:
        add("dataset.runner_constructs", False, str(exc))

    # --- Coding host installed + logged in; never the silent FakePlannerHost ------------------------
    # R3 (5d-B): demo resolves the planner host to an EXPLICIT FakePlannerHost, so the coding-host
    # AUTH checks (installed + logged_in) are skipped in demo only — Standard preflight is unchanged.
    # The `not_fake` config-shape check (the config still names a real host) is kept in both modes.
    host = config.models.coding_host
    if not config.is_demo:
        if host == CodingHost.CLAUDE_CODE:
            claude_executable = which("claude")
            add("coding_host.installed", claude_executable is not None, "claude on PATH")
            add(
                "coding_host.logged_in",
                bool(os.getenv("CLAUDE_CODE_OAUTH_TOKEN")),
                "CLAUDE_CODE_OAUTH_TOKEN",
            )
            # Dual-host parity: mirror the Codex version floor with the takeover-audited
            # Claude Code version. The probe is injectable for hermetic tests.
            if claude_executable is None:
                add(
                    "coding_host.version",
                    False,
                    "Claude Code >=2.1.201 is required for the claude_code coding host",
                )
            else:
                try:
                    raw_version = (claude_version_probe or _probe_claude_version)(claude_executable)
                    parsed_version = _parse_claude_version(raw_version)
                    add(
                        "coding_host.version",
                        parsed_version >= _MIN_CLAUDE_CODE_VERSION,
                        f"{raw_version.strip()} (claude_code requires Claude Code >=2.1.201)",
                    )
                except (
                    OSError,
                    ValueError,
                    subprocess.SubprocessError,
                    RuntimeError,
                ) as exc:
                    # RuntimeError covers sandbox/egress guards that intercept host
                    # subprocess launches; an unverifiable version fails the check
                    # (fail-closed) instead of crashing preflight.
                    add(
                        "coding_host.version",
                        False,
                        f"could not verify Claude Code >=2.1.201: {exc}",
                    )
        else:
            codex_executable = which("codex")
            add("coding_host.installed", codex_executable is not None, "codex on PATH")
            # Product calls pass ``home=None``.  In that real cleanroom route the same resolver as
            # the runner honors an explicit CODEX_HOME before falling back to $HOME/.codex.  The
            # ``home`` injection remains a deterministic test seam for callers that deliberately
            # emulate a different HOME without mutating the process environment.
            codex_home = (
                default_lead_codex_home() if home is None else Path(home).expanduser() / ".codex"
            )
            auth_path = codex_home / "auth.json"
            add(
                "coding_host.logged_in",
                auth_path.is_file(),
                f"Codex ChatGPT auth file {auth_path}",
            )
            if config.models.coding_model == "gpt-5.6-terra":
                if codex_executable is None:
                    add(
                        "coding_host.version",
                        False,
                        "Codex CLI >=0.144.4 is required for gpt-5.6-terra",
                    )
                else:
                    try:
                        raw_version = (codex_version_probe or _probe_codex_version)(
                            codex_executable
                        )
                        parsed_version = _parse_codex_version(raw_version)
                        add(
                            "coding_host.version",
                            parsed_version >= _MIN_TERRA_CODEX_VERSION,
                            (f"{raw_version.strip()} (gpt-5.6-terra requires codex-cli >=0.144.4)"),
                        )
                    except (OSError, ValueError, subprocess.SubprocessError) as exc:
                        add(
                            "coding_host.version",
                            False,
                            f"could not verify Codex CLI >=0.144.4: {exc}",
                        )
    add(
        "coding_host.not_fake",
        host in (CodingHost.CODEX, CodingHost.CLAUDE_CODE),
        "real adapter, never Fake",
    )

    # --- Models / keys — MODE-AWARE (F2): demo resolves API-agents to mock, needs no token-API key ---
    if config.is_demo:
        add(
            "models.demo_mode",
            True,
            "demo: API-agent providers resolve to mock; no token-API key required",
        )
    elif not paperbank_import_ok:
        add(
            "models.import_blocked",
            True,
            "API provider construction skipped because PaperBank import identity failed",
            warning=True,
        )
    else:
        api_roles = {
            "extraction": config.paperbank.extraction,
            "pattern": config.models.effective_pattern,
            "questioner": config.models.questioner,
            "narrator": config.models.narrator,
            "topic": config.models.topic,
            "owner": config.models.owner,
            "reviewer": config.models.reviewer,
        }
        for role, pm in api_roles.items():
            _check_api_provider(
                add, role, pm, allow_pro=config.models.allow_pro_model, build=build_provider
            )
        # owner + reviewer must be DISTINCT providers (cross-check independence)
        distinct = (
            config.models.owner.provider.strip().lower()
            != config.models.reviewer.provider.strip().lower()
        )
        add(
            "models.reviewer_independent", distinct, "owner and reviewer must be distinct providers"
        )

    # N-2 stays entirely absent from default-off and demo reports.  Once explicitly enabled, every
    # no-egress property (mode, capability, identity, hard reservation, key, tier) is checked before
    # constructing its separate uncached provider seam.
    if config.novelty.web_grounding.enabled:
        _check_novelty_web_grounding(
            add,
            config,
            build=build_novelty_web_provider,
        )

    # --- Literature source profile — opt-in paid Elicit must FAIL CLOSED if forced without a key -----
    # Skipped in demo (topic retrieval is mock/injected there — no Elicit call). `public`/`auto` never
    # fail (auto honestly degrades to PUBLIC when ELICIT_API_KEY is absent); `elicit`/`hybrid` FORCE
    # Elicit, so a missing key is an honest fail — this preflight only reads env presence (os.getenv),
    # it never issues the paid call. The key is env-only and never read from the config.
    if not config.is_demo:
        profile = config.literature.source_profile
        has_key = bool(os.getenv("ELICIT_API_KEY"))
        if profile in _ELICIT_PROFILES and not has_key:
            add(
                "literature.source_profile",
                False,
                f"source_profile '{profile.value}' forces Elicit but ELICIT_API_KEY is not set "
                "(load it via runtime.env, or set literature.source_profile to auto|public)",
            )
        else:
            # `resolve` reads ELICIT_API_KEY from env when the arg is empty, so AUTO+key ⇒ HYBRID here.
            enabled = resolve_topic_source_profile(profile, elicit_api_key="") in _ELICIT_PROFILES
            add(
                "literature.source_profile",
                True,
                f"source_profile '{profile.value}'"
                + (" — Elicit enabled (paid)" if enabled else " — public sources only (free)"),
            )

        if probe_openalex and config.literature.enabled:
            try:
                openalex_probe()
                add("literature.openalex_quota", True, "OpenAlex quota probe succeeded")
            except ExternalLookupError as exc:
                if exc.status_code == 429:
                    add(
                        "literature.openalex_quota",
                        True,
                        "OpenAlex daily quota exhausted — lookups will fail",
                        warning=True,
                    )
                else:
                    add(
                        "literature.openalex_quota",
                        True,
                        f"OpenAlex quota probe unavailable: {exc}",
                        warning=True,
                    )

    # --- Output writable — cheap net-new write probe ------------------------------------------------
    add(
        "run.output_writable",
        _output_writable(config.run.output_root),
        f"output_root {config.run.output_root}",
    )

    # --- Capability truth ---------------------------------------------------------------------------
    add(
        "novelty.enabled",
        not (config.novelty.enabled and config.is_demo),
        (
            "enabled: evidence-driven novelty admission runs before shortlist/planning"
            if config.novelty.enabled and not config.is_demo
            else (
                "disabled: this run cannot claim novelty-admitted planning"
                if not config.novelty.enabled
                else "subscription-only demo cannot run live novelty admission"
            )
        ),
    )
    add(
        "novelty.literature_enabled",
        not config.novelty.enabled or config.literature.enabled,
        (
            "literature retrieval enabled for novelty admission"
            if config.literature.enabled
            else "novelty admission requires literature.enabled=true"
        ),
    )
    questioner_identity = (
        config.models.questioner.provider.strip().lower(),
        config.models.questioner.model.strip().lower(),
    )
    reviewer_identity = (
        config.models.reviewer.provider.strip().lower(),
        config.models.reviewer.model.strip().lower(),
    )
    add(
        "novelty.independent_reviewer",
        not config.novelty.enabled or questioner_identity != reviewer_identity,
        (
            "novelty reviewer is distinct from the Question Scientist"
            if questioner_identity != reviewer_identity
            else "novelty reviewer must not reuse the exact Question Scientist model identity"
        ),
    )
    add(
        "run.shortlist_path",
        config.run.shortlist_path is None,
        "unset" if config.run.shortlist_path is None else "external shortlist is not yet supported",
    )
    add(
        "run.target_family_ids",
        not config.run.target_family_ids,
        "empty"
        if not config.run.target_family_ids
        else "external target selection is not yet supported",
    )
    add(
        "run.timeout_seconds",
        config.run.legacy_timeout_seconds is None,
        "not configured"
        if config.run.legacy_timeout_seconds is None
        else (
            "use dataset.inspection_runtime.timeout_seconds for the real per-planner-spawn limit; "
            "Maieusis has no run-wide timeout"
        ),
    )

    report = PreflightReport(
        checks=checks,
        estimates=_estimates(config),
        egress_disclosure=_egress_disclosure(config),
    )
    return report


def _check_api_provider(
    add: Callable[[str, bool, str], None],
    role: str,
    pm: ProviderModel,
    *,
    allow_pro: bool,
    build: BuildProvider,
) -> None:
    provider = pm.provider.strip().lower()
    if provider == "mock":
        add(f"models.{role}", True, "mock provider (no key required)")
        return
    env = _KEY_ENV.get(provider)
    if env is None:
        add(f"models.{role}", False, f"unknown provider {provider!r}")
        return
    key_name, model_name = env
    if not os.getenv(key_name):
        add(f"models.{role}", False, f"missing {key_name} (load via runtime.env, not the config)")
        return
    model = pm.model or os.getenv(model_name, "")
    if not model:
        add(f"models.{role}", False, f"missing model (set config or {model_name})")
        return
    try:
        ensure_model_allowed(provider=provider, model=model, allow_pro_model=allow_pro)
        build(provider, model=model, allow_pro_model=allow_pro)  # CONSTRUCT only — never send
        add(f"models.{role}", True, f"{provider}:{model} present + tier-authorized")
    except Exception as exc:
        add(f"models.{role}", False, str(exc))


def _check_novelty_web_grounding(
    add: Callable[[str, bool, str], None],
    config: MaieusisProjectConfig,
    *,
    build: BuildNoveltyWebProvider,
) -> None:
    """Validate the opt-in N-2 scout without sending a web or model request.

    The strict capability lookup is deliberately performed before the factory seam.  That keeps an
    unsupported adapter (currently OpenAI) from even constructing a client for a lane whose hard
    tool-fee reservation cannot be enforced.
    """

    grounding = config.novelty.web_grounding
    eligible_mode = config.novelty.enabled and not config.is_demo
    add(
        "novelty.web_grounding",
        eligible_mode,
        (
            "enabled: strict, opt-in novelty web grounding is available in standard novelty mode"
            if eligible_mode
            else (
                "novelty web grounding requires novelty.enabled=true"
                if not config.novelty.enabled
                else "subscription-only demo cannot run novelty web grounding"
            )
        ),
    )
    if not eligible_mode:
        return

    provider = grounding.scout.provider.strip().lower()
    model = grounding.scout.model.strip()

    try:
        capabilities = require_strict_novelty_web_capability(provider)
        capability_ok = True
        add(
            "novelty.web_grounding.strict_capability",
            True,
            (
                f"{capabilities.provider_name}:{capabilities.tool_name} "
                f"{capabilities.tool_version} enforces the hard use bound and reports a complete "
                "direct-search action trace"
            ),
        )
    except Exception as exc:
        capability_ok = False
        add("novelty.web_grounding.strict_capability", False, str(exc))

    scout_model_ok = bool(provider and model)
    add(
        "novelty.web_grounding.scout_model",
        scout_model_ok,
        (
            f"explicit scout identity {provider}:{model}"
            if scout_model_ok
            else "enabled novelty web grounding requires an explicit scout provider and model"
        ),
    )
    questioner_identity = _effective_provider_model_identity(config.models.questioner)
    scout_identity = (provider, model.lower())
    distinct_from_questioner = scout_model_ok and scout_identity != questioner_identity
    add(
        "novelty.web_grounding.scout_independent",
        distinct_from_questioner,
        (
            "web scout is distinct from the Question Scientist"
            if distinct_from_questioner
            else "novelty web scout must not reuse the effective Question Scientist model identity"
        ),
    )

    try:
        reservation = _novelty_web_tool_fee_reservation_micro_usd(config)
        ceiling = grounding.hard_run_tool_spend_ceiling_micro_usd
        reservation_ok = reservation <= ceiling
        add(
            "novelty.web_grounding.tool_fee_ceiling",
            reservation_ok,
            _novelty_web_tool_fee_description(config, reservation=reservation)
            + (
                ""
                if reservation_ok
                else " Worst-case reservation exceeds the configured hard ceiling."
            ),
        )
    except Exception as exc:
        reservation_ok = False
        add("novelty.web_grounding.tool_fee_ceiling", False, str(exc))

    # No client construction precedes all static gates.  In particular, an OpenAI configuration,
    # a pro-gated scout, or an unfundable full run cannot create a web provider as a side effect.
    if not (capability_ok and scout_model_ok and distinct_from_questioner and reservation_ok):
        return

    key_env = _KEY_ENV.get(provider)
    if key_env is None:
        # This is presently unreachable after the capability check, but keeps future adapters
        # fail-closed if their provider/key policy is not registered here.
        add("models.novelty_web_scout", False, f"unknown provider {provider!r}")
        return
    key_name, _model_env = key_env
    if not os.getenv(key_name):
        add(
            "models.novelty_web_scout",
            False,
            f"missing {key_name} (load via runtime.env, not the config)",
        )
        return
    try:
        # Keep the ordinary pro-model authorization intact even when an injected test factory does
        # not implement it itself.  The real novelty-specific factory independently preserves it.
        ensure_model_allowed(
            provider=provider,
            model=model,
            allow_pro_model=config.models.allow_pro_model,
        )
        build(
            provider,
            model=model,
            allow_pro_model=config.models.allow_pro_model,
        )  # CONSTRUCT only through the dedicated N-2 seam — never research_structured/send
        add(
            "models.novelty_web_scout",
            True,
            f"{provider}:{model} present + tier-authorized through the strict novelty web seam",
        )
    except Exception as exc:
        add("models.novelty_web_scout", False, str(exc))


def _effective_provider_model_identity(provider_model: ProviderModel) -> tuple[str, str]:
    """Resolve a regular API role's model fallback solely for static identity comparison."""

    provider = provider_model.provider.strip().lower()
    configured_model = provider_model.model.strip()
    if configured_model:
        return provider, configured_model.lower()
    env = _KEY_ENV.get(provider)
    fallback_model = os.getenv(env[1], "") if env is not None else ""
    return provider, fallback_model.strip().lower()


def _probe_dialogue_runtime() -> None:
    """Import the exact optional runtime used by a real family dialogue server; open no socket."""
    import uvicorn
    from mcp.server.fastmcp import FastMCP

    # Attribute access catches partially installed/incompatible packages, not only missing modules.
    _ = (FastMCP, uvicorn.Config)


def _probe_dataset_seed_link(link: str, dataset_id: str) -> list[object]:
    """Resolve the configured public seed link without invoking a model or coding agent."""
    return list(resolve_seed_link(link, dataset_id=dataset_id))


def _probe_codex_version(executable: str) -> str:
    """Read the local subscription CLI version without starting an agent or making a paid call."""
    result = subprocess.run(
        [executable, "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout.strip()


def _parse_codex_version(raw: str) -> tuple[int, int, int]:
    match = _CODEX_VERSION_PATTERN.search(raw.strip())
    if match is None:
        raise ValueError(f"unrecognized `codex --version` output: {raw.strip()!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _probe_claude_version(executable: str) -> str:
    """Read the local Claude Code CLI version without starting an agent or making a paid call."""
    result = subprocess.run(
        [executable, "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout.strip()


def _parse_claude_version(raw: str) -> tuple[int, int, int]:
    match = _CLAUDE_VERSION_PATTERN.search(raw.strip())
    if match is None:
        raise ValueError(f"unrecognized `claude --version` output: {raw.strip()!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _build_default_runner(config: MaieusisProjectConfig) -> object:
    """Construct the public runtime's real per-family host without spawning a coding agent."""
    from .orchestration.runtime_factories import build_planner_host_factory

    factory = build_planner_host_factory(config, run_root=config.run.output_root)
    return factory("preflight")


def _output_writable(output_root: Path) -> bool:
    try:
        output_root.mkdir(parents=True, exist_ok=True)
        probe = output_root / ".maieusis_preflight_probe"
        probe.write_text("probe", encoding="utf-8")
        probe.unlink()
        return True
    except Exception:
        return False


def _estimates(config: MaieusisProjectConfig) -> dict[str, str]:
    families = config.run.max_families
    rounds = config.run.max_revise_rounds
    # A malformed review REPLY is re-asked without consuming a revise round, so those calls are
    # real spend that the round arithmetic alone does not see. This line is a go/no-go before
    # ignition, so it must state the true ceiling, not a floor.
    per_family_reviews = 2 * (rounds + 1) * (1 + _MAX_REVIEW_ARTIFACT_REATTEMPTS)
    per_family_spawns = 1 + rounds
    fam = str(families)
    host = config.models.coding_host
    budget = (
        f"Claude Code turn budget {config.dataset.inspection_runtime.max_turns}; "
        if host == CodingHost.CLAUDE_CODE
        else "Codex has no synthetic turn cap; "
    )
    estimates = {
        "proposal_shape": (
            f"{families} families x {config.run.variants_per_family} variants requested per family"
        ),
        "max_model_reviews": f"~{per_family_reviews} per family x {fam} families",
        "max_agent_spawns": (
            f"~{per_family_spawns} planned invocations per family x {fam} families; each coding-"
            "agent invocation permits at most one additional process launch only for an explicit "
            "transient transport/host failure, sharing that invocation's turn/time budgets"
        ),
        "max_pattern_revision_calls": (
            f"up to 8 induced patterns x {rounds} configured revise rounds"
        ),
        "citation_reselection_calls": (
            "at most one bounded retry per paper with an empty/model-failed selection, plus one "
            "reselection when citation source closure is unresolved"
        ),
        "time_ceiling": (
            f"planner spawn timeout budget {config.dataset.inspection_runtime.timeout_seconds}s; "
            f"{budget}any transport retry shares the original host-specific budget; "
            f"{config.run.max_parallel_family_workers} families in parallel; no run-wide timeout"
        ),
    }
    # Preserve the exact default-off estimate surface.  The extra estimate is meaningful only for
    # the explicitly requested N-2 lane and names its narrow billing scope honestly.
    if config.novelty.web_grounding.enabled:
        reservation = _novelty_web_tool_fee_reservation_micro_usd(config)
        estimates["novelty_web_tool_fee_reservation"] = _novelty_web_tool_fee_description(
            config,
            reservation=reservation,
        )
    return estimates


def _novelty_web_tool_fee_reservation_micro_usd(config: MaieusisProjectConfig) -> int:
    """Return the all-variant N-2 reservation, including the one permitted re-search path."""

    grounding = config.novelty.web_grounding
    return (
        config.run.max_families
        * config.run.variants_per_family
        * _NOVELTY_WEB_SCOUT_PASSES_PER_VARIANT
        * grounding.max_searches_per_scout
        * grounding.web_tool_rate_micro_usd
    )


def _novelty_web_tool_fee_description(
    config: MaieusisProjectConfig,
    *,
    reservation: int | None = None,
) -> str:
    """Render the fixed N-2 tool-fee reservation without implying a total spend cap."""

    grounding = config.novelty.web_grounding
    total = (
        _novelty_web_tool_fee_reservation_micro_usd(config) if reservation is None else reservation
    )
    return (
        f"{config.run.max_families} families x {config.run.variants_per_family} variants x "
        f"{_NOVELTY_WEB_SCOUT_PASSES_PER_VARIANT} scout passes (initial + permitted novelty-r1) x "
        f"{grounding.max_searches_per_scout} max searches x {grounding.web_tool_rate_micro_usd} "
        f"micro-USD/search ({grounding.rate_card.value}) = {total} micro-USD; configured hard "
        f"ceiling {grounding.hard_run_tool_spend_ceiling_micro_usd} micro-USD. This is a web-tool "
        "fee only, not a total model-token cost ceiling."
    )


def _egress_disclosure(config: MaieusisProjectConfig) -> list[str]:
    if config.is_demo:
        return ["Demo mode: API-agent providers are mock; only the coding host runs locally."]
    lines = [
        "Extracted PDF text → the extraction model provider.",
        "Dataset link + literature queries → the lit-search / narrator providers.",
        "Question family / plan content → the owner + reviewer model APIs.",
        "Dataset PATH + the planning task → the coding agent (dataset read-only).",
    ]
    # Only disclose the paid Elicit egress when the resolved profile actually enables it (public/auto
    # without a key add nothing) — a public run's disclosure is byte-identical to today.
    resolved = resolve_topic_source_profile(config.literature.source_profile, elicit_api_key="")
    if resolved in _ELICIT_PROFILES:
        lines.append("Topic literature queries → Elicit semantic search (paid, opt-in source).")
    if config.novelty.enabled and config.novelty.web_grounding.enabled:
        scout = config.novelty.web_grounding.scout
        lines.append(
            "Redacted novelty-candidate projection → "
            f"N-2 web scout {scout.provider.strip().lower()}:{scout.model.strip()} "
            "(paid, opt-in direct web search; web-tool fee reservation only, not a total "
            "model-token cost ceiling)."
        )
    return lines
