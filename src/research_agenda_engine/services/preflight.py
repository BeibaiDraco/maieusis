"""`maieusis check` preflight — verify every e2e input, ZERO paid calls on ANY failure.

The preflight body contains NO ``.send`` / ``.generate_structured`` / runner ``.run`` / orchestrator
call. It does cheap/static work plus, for the explicit product ``check`` command, one free OpenAlex
quota probe: file existence, ``shutil.which`` + login-presence, exact dialogue-runtime imports,
source-tree Git validation, CONSTRUCTING providers (construction is free — it proves the key is
present + the model is tier-authorized; the paid call is only ``send``, which is never reached),
CONSTRUCTING the runner (validates the inspection runtime; never spawns), static id compares, a
write-probe, and static estimates + an egress disclosure.

Zero-paid is guaranteed structurally and TESTED: ``build_provider`` / ``build_runner`` are injectable so
tests inject spies whose ``send`` / ``run`` raise; every path (happy + each failure) asserts the spy was
never called. The OpenAlex probe is injectable and defaults off for non-check callers. Demo mode (no
token API) resolves the API-agent providers to ``mock`` and does NOT require
token-API keys — only the coding host is checked (F2).

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
from ..schemas.maieusis_project_config import (
    CodingHost,
    ConfigDatasetAccessMode,
    MaieusisProjectConfig,
    ProviderModel,
)
from ..schemas.topic_literature import TopicSourceProfile
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
BuildRunner = Callable[[MaieusisProjectConfig], object]
Which = Callable[[str], str | None]
OpenAlexProbe = Callable[[], None]
DialogueRuntimeProbe = Callable[[], None]
SourceTreeProbe = Callable[[str | Path], object]
DatasetSeedProbe = Callable[[str, str], list[object]]
CodexVersionProbe = Callable[[str], str]

_MIN_TERRA_CODEX_VERSION = (0, 144, 4)
_CODEX_VERSION_PATTERN = re.compile(r"\bcodex-cli\s+(\d+)\.(\d+)\.(\d+)\b")


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
            add("coding_host.installed", which("claude") is not None, "claude on PATH")
            add(
                "coding_host.logged_in",
                bool(os.getenv("CLAUDE_CODE_OAUTH_TOKEN")),
                "CLAUDE_CODE_OAUTH_TOKEN",
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

    # --- Explicitly unsupported controls -------------------------------------------------------------
    # These knobs previously parsed while the fresh driver ignored them. Reject them instead of
    # advertising a capability that cannot affect the scientific run.
    add(
        "novelty.enabled",
        not config.novelty.enabled,
        "disabled (real novelty search not yet supported)"
        if not config.novelty.enabled
        else "enabled novelty is not yet supported by the product driver",
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
    per_family_reviews = 2 * (rounds + 1)
    per_family_spawns = 1 + rounds
    fam = str(families)
    host = config.models.coding_host
    budget = (
        f"Claude Code turn budget {config.dataset.inspection_runtime.max_turns}; "
        if host == CodingHost.CLAUDE_CODE
        else "Codex has no synthetic turn cap; "
    )
    return {
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
    return lines
