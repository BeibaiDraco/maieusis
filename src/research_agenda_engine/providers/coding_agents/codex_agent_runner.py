"""Auto-spawn agent runner: launch Codex non-interactively (``codex exec``).

This mirrors the Claude Code runner
behind the same ``AgentRunner`` seam while using Codex-native JSONL output,
sandbox flags, and Codex-native MCP configuration overrides. The spawned agent
writes only typed planner artifacts under the branch planner workspace; the
trusted host still owns run records, digest stamping, validation, returned-bundle
assembly, and any Question Owner API calls.

In dialogue mode, the runner self-hosts a branch-scoped localhost MCP server in
the trusted parent process. Codex receives only that ``127.0.0.1`` MCP endpoint
and a per-server allowlist for the five scientific-dialogue tools; paid owner
credentials remain outside the child environment. Codex shell execution stays
within the native ``workspace-write`` sandbox. Synthetic fixture runs use a copied
snapshot; true-data runs expose an external read-only path without adding it as a
writable Codex directory.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import threading
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, NamedTuple

from ...io import load_model
from ...provenance import sha256_file, stable_hash
from ...schemas.coarse_dataset_facts import CoarseExploreRunResult
from ...schemas.planner_run import CodingAgentRunStatus, CodingAgentRunUsage
from ...schemas.question_family_branch import QuestionFamilyBranch
from ...services.planning.confined_workspace_io import atomic_write_confined_text
from ...services.planning.dataset_planner_packet import (
    DatasetPlannerHandoffManifest,
    DatasetPlannerTaskPacket,
    planner_packet_digest,
)
from ...services.planning.direct_file_artifact_contract import DIRECT_FILE_ARTIFACT_CONTRACT
from ...services.planning.planner_failures import (
    CodingAgentProviderUnavailable,
    HardFamilyIntegrityViolation,
)
from .agent_runner import AgentRunResult, discover_output_artifacts
from .dialogue_mcp_server import (
    DIALOGUE_MCP_SERVER_NAME,
    DIALOGUE_MCP_TOOL_NAMES,
    LocalDialogueMcpServer,
)
from .spawn_sandbox import (
    CODEX_BREACH_WATCH_GLOBS,
    assert_config_home_untouched,
    cleanup_codex_home,
    default_lead_codex_home,
    delete_staged_codex_auth,
    snapshot_config_home,
    stage_codex_home,
)
from .subprocess_utils import (
    detect_repo_root,
    directory_digest,
    kill_process_group,
    source_tree_digest,
    tail,
)

if TYPE_CHECKING:
    from ...mcp import ScientificDialogueServer
    from ..scientific_agents import ScientificAgentProvider

CODEX_AGENT_RUNNER_NAME = "codex-agent-runner"
# Coarse Source-B provenance tag. Matches CODEX_ADAPTER_NAME in codex_host.py; defined here (not
# imported) because the host imports the runner, so the reverse import would be a cycle.
CODEX_EXPLORER_ADAPTER = "codex"
CODEX_BUDGET_POLICY = "timeout_only_codex_no_turn_cap_v1"
DatasetAccessMode = Literal["snapshot_copy", "external_readonly"]

CODEX_DATASET_ACCESS_SNAPSHOT_COPY: DatasetAccessMode = "snapshot_copy"
CODEX_DATASET_ACCESS_EXTERNAL_READONLY: DatasetAccessMode = "external_readonly"
CODEX_GENERATED_SHELL_NETWORK_POLICY = "codex_native_workspace_write_shell_egress_blocked_probe"


def _codex_usage(usage: Mapping[str, Any]) -> CodingAgentRunUsage | None:
    """Build run usage from a codex ``turn.completed`` usage mapping (tokens; no USD figure)."""
    if not usage:
        return None
    input_tokens = usage.get("input_tokens")
    output_tokens = usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")
    if total_tokens is None and (input_tokens is not None or output_tokens is not None):
        total_tokens = int(input_tokens or 0) + int(output_tokens or 0)
    if input_tokens is None and output_tokens is None and total_tokens is None:
        return None
    return CodingAgentRunUsage(
        input_tokens=int(input_tokens) if input_tokens is not None else None,
        output_tokens=int(output_tokens) if output_tokens is not None else None,
        total_tokens=int(total_tokens) if total_tokens is not None else None,
        cost_usd=None,
        source="codex",
    )


_DEFAULT_TIMEOUT_SECONDS = 1800
_DEFAULT_MODEL = "gpt-5.6-terra"
_DEFAULT_REASONING_EFFORT = "high"
_SUPPORTED_REASONING_EFFORTS = frozenset({"minimal", "low", "medium", "high", "xhigh"})
_DEFAULT_SANDBOX_MODE = "workspace-write"
_DEFAULT_APPROVAL_POLICY = "never"
_DATASET_SNAPSHOT_DIRNAME = "codex_dataset_snapshot"
_LAUNCH_DIR_PREFIX = "maieusis-codex-launch-"
_MAX_TRANSIENT_ATTEMPTS = 2

# Only a structured message attached to a fatal top-level JSONL event is classified. stderr,
# agent/tool text, and item events (including item.type=error) are never searched.
_TRANSIENT_FATAL_MARKERS: tuple[tuple[str, str], ...] = (
    ("connection closed mid-response", "connection_closed_mid_response"),
    ("connection reset", "connection_reset"),
    ("econnreset", "connection_reset"),
    ("socket hang up", "socket_hang_up"),
    ("stream disconnected before completion", "stream_disconnected_before_completion"),
)
_PROVIDER_UNAVAILABLE_FATAL_MARKERS: tuple[tuple[str, str], ...] = (
    ("usage limit", "provider_usage_limit"),
    ("rate limit", "provider_rate_limit"),
    ("rate_limit", "provider_rate_limit"),
    ("quota exceeded", "provider_quota_exceeded"),
    ("unauthorized", "provider_unauthorized"),
    ("authentication failed", "provider_authentication_failed"),
    ("model not found", "provider_model_unavailable"),
    ("model is not supported", "provider_model_unavailable"),
)

_TRANSIENT_RETRY_TASK_NOTE = """

# Bounded Codex transport retry

A prior Codex transport attempt ended at one explicit fatal JSONL event before a successful turn.
The branch-local workspace may contain useful evidence or a partially written terminal artifact.
Inspect the existing files first, preserve valid evidence, repair or replace incomplete YAML, and
finish with exactly one valid root terminal artifact. Do not duplicate Owner dialogue or retry a
scope whose dialogue limit is already closed. Every original planning, evidence, filesystem, and
confirmation-firewall rule still applies. This attempt shares the original invocation deadline.
"""

_PAID_OR_SECRET_ENV_PREFIXES: tuple[str, ...] = ("OPENAI_", "ANTHROPIC_")
_PAID_OR_SECRET_ENV_EXACT: tuple[str, ...] = (
    "OPENAI_API_KEY",
    "CODEX_API_KEY",
    "CODEX_ACCESS_TOKEN",
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "ELICIT_API_KEY",
    "OPENALEX_API_KEY",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "HF_TOKEN",
    "MAIEUSIS_ALLOW_PRO_MODEL",
    "MAIEUSIS_OPENAI_MODEL",
    "MAIEUSIS_OPENAI_PROVIDER",
)
_PAID_OR_SECRET_ENV_SUFFIXES: tuple[str, ...] = (
    "_API_KEY",
    "_TOKEN",
    "_SECRET",
    "_PASSWORD",
    "_CREDENTIAL",
    "_CREDENTIALS",
)


def _is_secret_environment_key(key: str) -> bool:
    upper = key.upper()
    return (
        upper in _PAID_OR_SECRET_ENV_EXACT
        or upper.startswith(_PAID_OR_SECRET_ENV_PREFIXES)
        or upper.endswith(_PAID_OR_SECRET_ENV_SUFFIXES)
    )


_CODEX_REINFORCEMENT = (
    "You are running headless as the Maieusis dataset-planning coding agent.\n\n"
    "Write files ONLY under the planner workspace path named in the task packet. "
    "Do not write into the launch directory, parent repositories, the Maieusis source tree, "
    "the dataset snapshot, or any Codex home/config directory. This is planning, not "
    "execution: produce only typed planning artifacts (inspection evidence and one "
    "terminal plan, rejection, or escalation).\n\n"
    "Use Codex shell only for bounded local inspection of the configured dataset surface "
    "and for writing the required YAML artifacts. Do not access networks, credentials, "
    "other branches, or hidden/user config. Do not use web search. Do not run full or "
    "long-running analyses, do not search for effects or significance, do not produce "
    "confirmatory statistics, and do not load full raw-array or neural-matrix surfaces.\n\n"
    "Do NOT compute or fill any provenance digest / hash fields (source_digest, "
    "query_or_command_digest, result_digest, input_digest, output_digest, payload_digest). "
    "Omit them or leave a short placeholder; the trusted host recomputes and stamps ALL "
    "digests when it collects your artifacts. Never invent a hash.\n\n"
    "Write exactly: inspection-evidence YAML files under the evidence directory, and a "
    "single terminal artifact (a plan draft, a rejection, or an escalation) at the path "
    "the packet specifies. Do NOT write a run_record, a returned bundle, or a validation "
    "report. Finish as soon as your evidence and the single terminal artifact are written.\n\n"
    "PlanningMessage schemas reject extra keys. Use only the fields shown in the direct-file "
    "contract for the selected message_type. In particular, a plan_draft has NO top-level "
    "evidence_ids field; family plan evidence belongs only under each "
    "variant_outcomes item.\n\n"
    "The planning firewall is behavioral, not a vocabulary ban. Ordinary scientific planning "
    "language, candidate estimands/models, and honestly labeled bounded diagnostics are allowed. "
    "Do not run a full scientific pipeline, search for significance, optimize the question against "
    "target outcomes, access confirmation outcomes, make confirmatory claims, or present a bounded "
    "planning diagnostic as a discovery."
)

_CODEX_OWNER_DIALOGUE_REINFORCEMENT = (
    "Question Owner dialogue (MCP) is active for this run.\n\n"
    "Use the branch-scoped MCP tools only when scientific ambiguity would otherwise "
    "force you to guess or silently narrow the question. The MCP server is hosted by "
    "the trusted runner on localhost; it is the only path to the Question Owner.\n\n"
    "Do not write owner-dialogue YAML files. Do not emulate, serialize, or invent MCP "
    "tool envelopes in planner artifacts. Keep inspection evidence and the single "
    "terminal plan, rejection, or escalation artifact on the direct-file contract. "
    "Owner dialogue over MCP is for clarification and operationalization review only; "
    "evidence, terminal decisions, and returned bundles remain file-based."
)


# GF-2a coarse Source-B reinforcement (external_readonly only). A lean cousin of the planner
# reinforcement: no direct-file artifact contract and no terminal-identity hint (coarse produces
# one coarse facts YAML, not evidence + a terminal plan/rejection). Authoritative coarsen-by-
# contract lives in the coarse task.md; this echoes only the safety-critical parts. Lowercase-"one".
_CODEX_COARSE_REINFORCEMENT = (
    "You are running headless as the Maieusis COARSE dataset explorer (proposal stage) on a REAL, "
    "read-only dataset SAMPLE.\n\n"
    "Write files ONLY under the workspace path named in the task. Do not write into the launch "
    "directory, parent repositories, the Maieusis source tree, or any Codex home/config directory. "
    "Use Codex shell only for bounded, coarse local inspection of the dataset sample and for "
    "writing the required YAML. Do not access networks, credentials, or hidden config. Do not run "
    "full or long-running analyses, do not search for effects or significance, and do not load "
    "full raw-array surfaces.\n\n"
    "Stay COARSE. Produce exactly one coarse facts YAML at the path the task specifies. NEVER "
    "report exact column or field names, table schemas, or exact row/trial/session/unit counts; "
    "report only coarse kinds and order-of-magnitude or approximate scale facts. Do not emit a "
    "columns / schema / table_schema field.\n\n"
    "Do NOT compute or fill any provenance / identity / digest fields; the trusted host stamps "
    "those. Never invent a hash.\n\n"
    "A strict proposal-safe firewall scans your artifact. Do NOT use result-seeking or "
    "firewall-forbidden vocabulary anywhere, including in disclaimers. Finish as soon as the "
    "single coarse facts YAML is written."
)


class _CodexSpawnResult(NamedTuple):
    stdout: str
    stderr: str
    returncode: int
    auth_deleted_after_thread_started: bool


class _CodexSpawnAborted(ValueError):
    """A killed/aborted process with enough auth state for hard-boundary classification."""

    def __init__(
        self,
        message: str,
        *,
        thread_started: bool,
        auth_deleted_after_thread_started: bool,
    ) -> None:
        super().__init__(message)
        self.thread_started = thread_started
        self.auth_deleted_after_thread_started = auth_deleted_after_thread_started


class _ParsedCodexResult(NamedTuple):
    events: list[Mapping[str, Any]]
    event_counts: Counter[str]
    thread_id: str
    usage: Mapping[str, Any]
    final_message: str


class _CodexResultFailure(NamedTuple):
    message: str
    fatal_event_type: str
    transient_marker: str | None
    provider_marker: str | None


class _CodexFatalSurface(NamedTuple):
    event_type: str
    message: str


class _CodexAttemptAudit(NamedTuple):
    attempt_index: int
    command_digest: str
    prompt_digest: str
    returncode: int
    event_counts: Mapping[str, int]
    thread_id: str
    fatal_event_type: str
    transient_marker: str | None
    provider_marker: str | None
    auth_deleted_after_thread_started: bool
    artifact_manifest_before_digest: str
    artifact_manifest_after_digest: str
    changed_terminal_files: tuple[str, ...]


class _DatasetSnapshot(NamedTuple):
    path: Path | None
    before_digest: str
    after_digest: str
    access_mode: str
    is_copied_snapshot: bool
    added_as_writable_dir: bool


def _aggregate_codex_usage(results: Sequence[_ParsedCodexResult]) -> CodingAgentRunUsage | None:
    usages = [usage for result in results if (usage := _codex_usage(result.usage)) is not None]
    if not usages:
        return None

    def summed(field: str) -> int | None:
        values = [value for usage in usages if (value := getattr(usage, field)) is not None]
        return sum(values) if values else None

    return CodingAgentRunUsage(
        input_tokens=summed("input_tokens"),
        output_tokens=summed("output_tokens"),
        total_tokens=summed("total_tokens"),
        cost_usd=None,
        source="codex",
    )


def _root_terminal_paths(packet: DatasetPlannerTaskPacket) -> tuple[Path, Path, Path]:
    plan_path = Path(packet.output_paths.plan_draft_path)
    rejection_path = Path(packet.output_paths.rejection_path)
    return plan_path, rejection_path, plan_path.parent / "escalation.yaml"


def _assert_confined_workspace_path(
    path: str | Path,
    *,
    workspace: Path,
    label: str,
    must_equal_workspace: bool = False,
) -> Path:
    """Require one canonical absolute path under the exact branch workspace."""

    raw = Path(path)
    resolved_workspace = workspace.resolve()
    if not raw.is_absolute():
        raise HardFamilyIntegrityViolation(f"{label} must be an absolute workspace path: {raw}")
    resolved = raw.resolve()
    if raw != resolved:
        raise HardFamilyIntegrityViolation(f"{label} is non-canonical or symlink-aliased: {raw}")
    if must_equal_workspace:
        if resolved != resolved_workspace:
            raise HardFamilyIntegrityViolation(
                f"{label} differs from the exact active planner workspace"
            )
    elif resolved != resolved_workspace and resolved_workspace not in resolved.parents:
        raise HardFamilyIntegrityViolation(f"{label} escaped the active planner workspace: {raw}")
    return resolved


def _assert_packet_workspace_identity(
    packet: DatasetPlannerTaskPacket,
    *,
    workspace: Path,
) -> None:
    output_paths = packet.output_paths
    _assert_confined_workspace_path(
        output_paths.planner_workspace,
        workspace=workspace,
        label="packet planner_workspace",
        must_equal_workspace=True,
    )
    for label, path in (
        ("packet evidence_dir", output_paths.evidence_dir),
        ("packet dialogue_dir", output_paths.dialogue_dir),
        ("packet plan_draft_path", output_paths.plan_draft_path),
        ("packet rejection_path", output_paths.rejection_path),
        ("packet validation_report_path", output_paths.validation_report_path),
    ):
        _assert_confined_workspace_path(path, workspace=workspace, label=label)


def _safe_workspace_digest(path: Path, *, workspace: Path) -> str:
    _assert_confined_workspace_path(path, workspace=workspace, label="planner artifact")
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise HardFamilyIntegrityViolation(
                f"planner artifact must be a single-link regular file: {path}"
            )
        return sha256_file(path)
    except OSError as exc:
        raise HardFamilyIntegrityViolation(
            f"planner artifact could not be digested as trusted workspace input: {path}"
        ) from exc


def _artifact_digest_map(
    packet: DatasetPlannerTaskPacket,
    *,
    workspace: Path,
) -> dict[str, str]:
    candidates: set[Path] = set(_root_terminal_paths(packet))
    for directory in (packet.output_paths.evidence_dir, packet.output_paths.dialogue_dir):
        root = Path(directory)
        if root.exists():
            candidates.update(root.glob("*.yaml"))
    result: dict[str, str] = {}
    for path in sorted(candidates):
        if not path.exists():
            continue
        if not path.is_file():
            raise HardFamilyIntegrityViolation(f"planner artifact is not a regular file: {path}")
        digest = _safe_workspace_digest(path, workspace=workspace)
        relative = str(path.resolve().relative_to(workspace.resolve()))
        result[relative] = digest
    return result


def _immutable_workspace_digest_map(
    packet: DatasetPlannerTaskPacket,
    *,
    workspace: Path,
) -> dict[str, str]:
    """Digest every host-owned workspace entry outside the declared mutable output surface."""

    resolved_workspace = workspace.resolve()
    mutable_roots = {
        Path(packet.output_paths.evidence_dir),
        Path(packet.output_paths.dialogue_dir),
    }
    mutable_files = set(_root_terminal_paths(packet))
    dataset_snapshot_root = resolved_workspace / _DATASET_SNAPSHOT_DIRNAME
    result: dict[str, str] = {}
    for path in sorted(resolved_workspace.rglob("*")):
        lexical = Path(path)
        if lexical == dataset_snapshot_root or dataset_snapshot_root in lexical.parents:
            continue
        if lexical in mutable_files or any(
            lexical == root or root in lexical.parents for root in mutable_roots
        ):
            continue
        try:
            metadata = lexical.lstat()
        except OSError as exc:
            raise HardFamilyIntegrityViolation(
                f"host-owned planner workspace entry could not be inspected: {lexical}"
            ) from exc
        if stat.S_ISDIR(metadata.st_mode):
            continue
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise HardFamilyIntegrityViolation(
                "host-owned planner workspace entry is symlinked, hard-linked, or non-regular: "
                f"{lexical}"
            )
        relative = lexical.relative_to(resolved_workspace).as_posix()
        result[relative] = _safe_workspace_digest(lexical, workspace=resolved_workspace)
    return result


def _terminal_digest_map(
    packet: DatasetPlannerTaskPacket,
    *,
    workspace: Path,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in _root_terminal_paths(packet):
        if not path.exists():
            continue
        if not path.is_file():
            raise HardFamilyIntegrityViolation(
                f"planner terminal artifact is not a regular file: {path}"
            )
        digest = _safe_workspace_digest(path, workspace=workspace)
        relative = str(path.resolve().relative_to(workspace.resolve()))
        result[relative] = digest
    return result


def _handoff_file_digest_map(
    handoff: DatasetPlannerHandoffManifest,
    *,
    workspace: Path,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in (
        Path(handoff.packet_path),
        Path(handoff.task_path),
        Path(handoff.manifest_path),
    ):
        if not path.is_file():
            raise HardFamilyIntegrityViolation(f"planner handoff context file is missing: {path}")
        digest = _safe_workspace_digest(path, workspace=workspace)
        relative = str(path.resolve().relative_to(workspace.resolve()))
        result[relative] = digest
    return result


def _changed_files(before: Mapping[str, str], after: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(sorted(path for path, digest in after.items() if before.get(path) != digest))


def _cleanup_dialogue_and_launch(
    dialogue: LocalDialogueMcpServer | None,
    launch_dir: Path,
) -> None:
    cleanup_error: BaseException | None = None
    if dialogue is not None:
        try:
            dialogue.stop()
        except (OSError, RuntimeError) as exc:
            cleanup_error = exc
    try:
        shutil.rmtree(launch_dir)
    except FileNotFoundError:
        pass
    except OSError as exc:
        cleanup_error = cleanup_error or exc
    if launch_dir.exists():
        cleanup_error = cleanup_error or RuntimeError(
            "isolated Codex launch directory still exists after cleanup"
        )
    if cleanup_error is not None:
        raise HardFamilyIntegrityViolation(
            "Codex dialogue/launch containment cleanup could not be proven"
        ) from cleanup_error


class CodexAgentRunner:
    """Launch ``codex exec`` to inspect a fixture and write typed planner artifacts."""

    runner_name = CODEX_AGENT_RUNNER_NAME

    def __init__(
        self,
        *,
        executable: str = "codex",
        model: str = _DEFAULT_MODEL,
        reasoning_effort: str = _DEFAULT_REASONING_EFFORT,
        timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
        sandbox_mode: str = _DEFAULT_SANDBOX_MODE,
        approval_policy: str = _DEFAULT_APPROVAL_POLICY,
        dataset_root: str | Path | None = None,
        dataset_access_mode: DatasetAccessMode = CODEX_DATASET_ACCESS_SNAPSHOT_COPY,
        inspection_python: str | Path | None = None,
        inspection_command: str | None = None,
        inspection_pythonpath: str | Path | None = None,
        inspection_extra_env: Mapping[str, str] | None = None,
        source_tree_root: str | Path | None = None,
        lead_codex_home: str | Path | None = None,
        codex_home_parent: str | Path | None = None,
        launch_parent: str | Path | None = None,
        disable_plugins: bool = True,
    ) -> None:
        if timeout_seconds <= 0 or timeout_seconds > 2400:
            raise ValueError(
                "CodexAgentRunner timeout_seconds must be in (0, 2400] (<= 40 min backstop)"
            )
        if sandbox_mode != _DEFAULT_SANDBOX_MODE:
            raise ValueError("CodexAgentRunner requires sandbox_mode='workspace-write'")
        if approval_policy != _DEFAULT_APPROVAL_POLICY:
            raise ValueError("CodexAgentRunner requires approval_policy='never'")
        model = model.strip()
        if not model:
            raise ValueError("CodexAgentRunner model must be non-empty")
        reasoning_effort = reasoning_effort.strip().lower()
        if reasoning_effort not in _SUPPORTED_REASONING_EFFORTS:
            raise ValueError(
                "CodexAgentRunner reasoning_effort must be one of "
                f"{sorted(_SUPPORTED_REASONING_EFFORTS)}"
            )
        if dataset_access_mode not in (
            CODEX_DATASET_ACCESS_SNAPSHOT_COPY,
            CODEX_DATASET_ACCESS_EXTERNAL_READONLY,
        ):
            raise ValueError("unsupported CodexAgentRunner dataset_access_mode")
        if dataset_access_mode == CODEX_DATASET_ACCESS_EXTERNAL_READONLY and dataset_root is None:
            raise ValueError("external_readonly dataset access requires dataset_root")
        self.executable = executable
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self.sandbox_mode = sandbox_mode
        self.approval_policy = approval_policy
        self.dataset_root = Path(dataset_root) if dataset_root is not None else None
        self.dataset_access_mode = dataset_access_mode
        if inspection_command is not None and inspection_python is not None:
            raise ValueError(
                "inspection_command and inspection_python are mutually exclusive; pass one"
            )
        self.inspection_python = Path(inspection_python) if inspection_python is not None else None
        # A multi-token inspection runtime (e.g. an ephemeral per-format interpreter) rendered
        # VERBATIM — never wrapped in Path()/resolve() (which would mangle a command with flags into
        # one bogus path). Mutually exclusive with the single-interpreter inspection_python.
        self.inspection_command = (
            str(inspection_command) if inspection_command is not None else None
        )
        self.inspection_pythonpath = (
            Path(inspection_pythonpath) if inspection_pythonpath is not None else None
        )
        self.inspection_extra_env = {
            str(key): str(value) for key, value in (inspection_extra_env or {}).items()
        }
        self._validate_inspection_extra_env()
        self.source_tree_root = Path(source_tree_root) if source_tree_root is not None else None
        self.lead_codex_home = Path(lead_codex_home) if lead_codex_home is not None else None
        self.codex_home_parent = Path(codex_home_parent) if codex_home_parent is not None else None
        self.launch_parent = Path(launch_parent) if launch_parent is not None else None
        self.disable_plugins = disable_plugins

    def build_command(
        self,
        *,
        workspace: Path,
        launch_dir: Path,
        dialogue_mcp_url: str | None = None,
        dialogue_tool_names: Sequence[str] | None = None,
    ) -> list[str]:
        """Return the exact ``codex exec`` argv; task text is supplied on stdin."""
        argv: list[str] = [self.executable]
        if self.disable_plugins:
            argv += ["--disable", "plugins"]
        argv += [
            "--model",
            self.model,
            "-c",
            f"model_reasoning_effort={json.dumps(self.reasoning_effort)}",
            "-a",
            self.approval_policy,
            "exec",
            "--json",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            self.sandbox_mode,
            "--cd",
            str(Path(launch_dir).resolve()),
            "--add-dir",
            str(Path(workspace).resolve()),
        ]
        if dialogue_mcp_url is not None:
            argv += self._dialogue_mcp_config_args(
                dialogue_mcp_url,
                dialogue_tool_names or DIALOGUE_MCP_TOOL_NAMES,
            )
        argv += [
            "-",
        ]
        return argv

    def run(
        self,
        *,
        run_id: str,
        branch: QuestionFamilyBranch,
        handoff: DatasetPlannerHandoffManifest,
        workspace: Path,
        owner_session: ScientificAgentProvider | None = None,
        dialogue_server: ScientificDialogueServer | None = None,
    ) -> AgentRunResult:
        del owner_session
        workspace = Path(workspace).resolve()
        try:
            repo_root = self.source_tree_root or detect_repo_root()
        except (OSError, ValueError) as exc:
            raise HardFamilyIntegrityViolation(
                "the shared source-tree identity could not be resolved at planner launch"
            ) from exc
        lead_home = self.lead_codex_home or default_lead_codex_home()
        try:
            cli_version = self._codex_cli_version()
        except ValueError as exc:
            raise HardFamilyIntegrityViolation(
                "the shared Codex CLI became unavailable or unverifiable at planner launch"
            ) from exc

        # The trusted handoff is an identity boundary, not merely prompt input. Validate all three
        # files are regular, branch-local files before reading any of them, and prove the persisted
        # manifest is exactly the in-memory object supplied by the host.
        handoff_file_baseline = _handoff_file_digest_map(handoff, workspace=workspace)
        try:
            persisted_handoff = load_model(handoff.manifest_path, DatasetPlannerHandoffManifest)
            packet = load_model(handoff.packet_path, DatasetPlannerTaskPacket)
            task_text = Path(handoff.task_path).read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            raise HardFamilyIntegrityViolation(
                "planner handoff context could not be loaded as its trusted typed surface"
            ) from exc
        if persisted_handoff != handoff:
            raise HardFamilyIntegrityViolation(
                "persisted planner handoff manifest differs from the trusted in-memory manifest"
            )
        expected_identity = (
            run_id,
            branch.branch_id,
            branch.question_family_id,
            branch.context_id,
            branch.owner_session_id,
        )
        if (
            handoff.run_id,
            handoff.branch_id,
            handoff.question_family_id,
            handoff.context_id,
            handoff.owner_session_id,
        ) != expected_identity:
            raise HardFamilyIntegrityViolation(
                "planner handoff manifest identity differs from the active run/branch"
            )
        if (
            packet.run_id,
            packet.branch_id,
            packet.question_family_id,
            packet.context_id,
            packet.owner_session_id,
        ) != expected_identity:
            raise HardFamilyIntegrityViolation(
                "planner handoff packet identity differs from the active run/branch"
            )
        _assert_packet_workspace_identity(packet, workspace=workspace)
        if planner_packet_digest(packet) != handoff.packet_digest:
            raise HardFamilyIntegrityViolation(
                "planner handoff packet digest does not match its manifest"
            )
        if stable_hash({"task": task_text}) != handoff.task_digest:
            raise HardFamilyIntegrityViolation("planner task digest does not match its manifest")
        terminal_baseline = _terminal_digest_map(packet, workspace=workspace)
        workspace_manifest_before = _artifact_digest_map(packet, workspace=workspace)
        immutable_workspace_baseline = _immutable_workspace_digest_map(packet, workspace=workspace)

        try:
            launch_dir = self._make_launch_dir()
        except OSError as exc:
            raise HardFamilyIntegrityViolation(
                "the isolated Codex launch directory could not be created"
            ) from exc
        try:
            dialogue = (
                LocalDialogueMcpServer(dialogue_server) if dialogue_server is not None else None
            )
        except (OSError, RuntimeError) as exc:
            _cleanup_dialogue_and_launch(None, launch_dir)
            raise HardFamilyIntegrityViolation(
                "the branch-scoped dialogue server could not be initialized"
            ) from exc
        dialogue_mcp_url: str | None = None
        dialogue_tool_names = tuple(DIALOGUE_MCP_TOOL_NAMES) if dialogue is not None else ()
        runner_warnings: list[str] = []
        result_payloads: list[_ParsedCodexResult] = []
        attempt_audits: list[_CodexAttemptAudit] = []
        attempt_count = 0
        argv: list[str] = []
        spawn = _CodexSpawnResult(
            stdout="", stderr="", returncode=1, auth_deleted_after_thread_started=False
        )
        result_json = _ParsedCodexResult([], Counter(), "", {}, "")
        staged_homes: list[Path] = []
        started_at = datetime.now(UTC)
        ended_at = started_at
        deadline = time.monotonic() + self.timeout_seconds
        try:
            before = source_tree_digest(repo_root)
            lead_home_before = snapshot_config_home(
                lead_home, include_globs=CODEX_BREACH_WATCH_GLOBS
            )
            launch_before = directory_digest(launch_dir)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            _cleanup_dialogue_and_launch(dialogue, launch_dir)
            raise HardFamilyIntegrityViolation(
                "coding-agent source/config/launch boundary baseline could not be proven"
            ) from exc
        after = before
        lead_home_after = lead_home_before
        launch_after = launch_before
        empty_dataset_digest = stable_hash({"dataset_snapshot": "not_prepared"})
        dataset_snapshot = _DatasetSnapshot(
            path=None,
            before_digest=empty_dataset_digest,
            after_digest=empty_dataset_digest,
            access_mode=self.dataset_access_mode,
            is_copied_snapshot=False,
            added_as_writable_dir=False,
        )
        try:
            try:
                dataset_snapshot = self._prepare_dataset_snapshot(workspace)
            except (OSError, ValueError) as exc:
                raise HardFamilyIntegrityViolation(
                    "the configured dataset boundary could not be prepared for planning"
                ) from exc
            if dialogue is not None:
                dialogue.start()
                dialogue_mcp_url = dialogue.url

            base_prompt = self._prompt(
                task_text=task_text,
                workspace=workspace,
                dataset_snapshot=dataset_snapshot,
                owner_dialogue_active=dialogue_mcp_url is not None,
            )
            for attempt_count in range(1, _MAX_TRANSIENT_ATTEMPTS + 1):
                remaining_timeout = deadline - time.monotonic()
                if remaining_timeout <= 0:
                    raise ValueError(
                        "codex exec exhausted the whole-invocation wall-clock timeout before "
                        "a bounded retry could start"
                    )
                prompt = (
                    base_prompt if attempt_count == 1 else base_prompt + _TRANSIENT_RETRY_TASK_NOTE
                )
                attempt_artifacts_before = _artifact_digest_map(packet, workspace=workspace)
                attempt_terminals_before = _terminal_digest_map(packet, workspace=workspace)
                argv = self.build_command(
                    workspace=workspace,
                    launch_dir=launch_dir,
                    dialogue_mcp_url=dialogue_mcp_url,
                    dialogue_tool_names=dialogue_tool_names,
                )

                # Every process attempt receives a distinct short-lived CODEX_HOME.  No retry
                # inherits auth/session/config bytes from the failed child.
                try:
                    staging = stage_codex_home(lead_home=lead_home, parent=self.codex_home_parent)
                except (OSError, ValueError) as exc:
                    raise HardFamilyIntegrityViolation(
                        "shared Codex subscription auth could not be staged at planner launch"
                    ) from exc
                staged_homes.append(staging.home)
                spawn_error: Exception | None = None
                cleanup_error: Exception | None = None
                try:
                    try:
                        self._assert_staged_home_location(
                            staging.home, workspace=workspace, repo_root=repo_root
                        )
                    except ValueError as exc:
                        raise HardFamilyIntegrityViolation(
                            "short-lived Codex home was staged inside a protected workspace"
                        ) from exc
                    try:
                        spawn = self._spawn(
                            argv,
                            stdin_text=prompt,
                            cwd=launch_dir,
                            env=self._subprocess_env(staging.env),
                            auth_path=staging.auth_path,
                            timeout_seconds=remaining_timeout,
                        )
                    except (OSError, ValueError) as exc:
                        # A timeout or launch failure does not get to bypass containment checks.
                        # Preserve the original error only if every hard boundary remains intact.
                        spawn_error = exc
                finally:
                    try:
                        cleanup_codex_home(staging.home)
                    except OSError as exc:
                        cleanup_error = exc
                    if cleanup_error is None and staging.home.exists():
                        cleanup_error = RuntimeError(
                            "short-lived Codex home still exists after cleanup"
                        )

                try:
                    after = source_tree_digest(repo_root)
                    lead_home_after = snapshot_config_home(
                        lead_home, include_globs=CODEX_BREACH_WATCH_GLOBS
                    )
                    launch_after = directory_digest(launch_dir)
                    dataset_snapshot = self._finish_dataset_snapshot(dataset_snapshot)
                    handoff_file_after = _handoff_file_digest_map(handoff, workspace=workspace)
                    immutable_workspace_after = _immutable_workspace_digest_map(
                        packet, workspace=workspace
                    )
                except HardFamilyIntegrityViolation:
                    raise
                except Exception as exc:
                    raise HardFamilyIntegrityViolation(
                        "coding-agent boundary state could not be re-snapshotted after "
                        f"codex exec attempt {attempt_count}"
                    ) from exc

                # Hard boundaries are checked after every attempt. A provider/transport error
                # never permits a mutation to be retried away.
                if after != before:
                    raise HardFamilyIntegrityViolation(
                        "source_tree_mutation_detected: the Maieusis source tree changed during "
                        f"codex exec attempt {attempt_count} (before={before[:12]} "
                        f"after={after[:12]}); discarding run"
                    )
                try:
                    assert_config_home_untouched(lead_home_before, lead_home_after, root=lead_home)
                except ValueError as exc:
                    raise HardFamilyIntegrityViolation(
                        "lead Codex config home changed during the isolated planner spawn"
                    ) from exc
                if launch_after != launch_before:
                    raise HardFamilyIntegrityViolation(
                        "codex exec wrote files into the isolated launch directory"
                    )
                if dataset_snapshot.before_digest != dataset_snapshot.after_digest:
                    raise HardFamilyIntegrityViolation(
                        "codex exec modified the disposable dataset snapshot"
                    )
                if handoff_file_after != handoff_file_baseline:
                    raise HardFamilyIntegrityViolation(
                        "handoff_context_mutation_detected: handoff packet, task, or manifest changed "
                        f"during codex exec attempt {attempt_count}; discarding run"
                    )
                if immutable_workspace_after != immutable_workspace_baseline:
                    raise HardFamilyIntegrityViolation(
                        "host_owned_workspace_mutation_detected: Codex changed or created a file "
                        "outside the declared evidence/dialogue/terminal output surface during "
                        f"attempt {attempt_count}; discarding run"
                    )
                if cleanup_error is not None:
                    raise HardFamilyIntegrityViolation(
                        "short-lived Codex auth/config home could not be removed after the spawn"
                    ) from cleanup_error
                if (
                    isinstance(spawn_error, _CodexSpawnAborted)
                    and spawn_error.thread_started
                    and not spawn_error.auth_deleted_after_thread_started
                ):
                    raise HardFamilyIntegrityViolation(
                        "staged Codex auth was not deleted immediately after thread.started"
                    ) from spawn_error
                if spawn_error is not None:
                    raise spawn_error

                result_json = self._parse_result_payload(spawn)
                if (
                    result_json.event_counts["thread.started"] > 0
                    and not spawn.auth_deleted_after_thread_started
                ):
                    raise HardFamilyIntegrityViolation(
                        "staged Codex auth was not deleted immediately after thread.started"
                    )
                result_payloads.append(result_json)
                failure = self._result_failure(result_json, spawn)
                attempt_artifacts_after = _artifact_digest_map(packet, workspace=workspace)
                attempt_terminals_after = _terminal_digest_map(packet, workspace=workspace)
                attempt_audits.append(
                    _CodexAttemptAudit(
                        attempt_index=attempt_count,
                        command_digest=stable_hash({"argv": argv}),
                        prompt_digest=stable_hash({"prompt": prompt}),
                        returncode=spawn.returncode,
                        event_counts=dict(result_json.event_counts),
                        thread_id=result_json.thread_id,
                        fatal_event_type=failure.fatal_event_type if failure else "",
                        transient_marker=failure.transient_marker if failure else None,
                        provider_marker=failure.provider_marker if failure else None,
                        auth_deleted_after_thread_started=(spawn.auth_deleted_after_thread_started),
                        artifact_manifest_before_digest=stable_hash(attempt_artifacts_before),
                        artifact_manifest_after_digest=stable_hash(attempt_artifacts_after),
                        changed_terminal_files=_changed_files(
                            attempt_terminals_before, attempt_terminals_after
                        ),
                    )
                )
                if failure is None:
                    break
                if failure.transient_marker and attempt_count < _MAX_TRANSIENT_ATTEMPTS:
                    runner_warnings.append(
                        "bounded Codex transport retry: "
                        f"attempt {attempt_count} ended with {failure.transient_marker}; "
                        "branch-local files and Owner-dialogue state were preserved, the next "
                        "process receives a fresh CODEX_HOME, and both attempts share the original "
                        "wall-clock deadline"
                    )
                    continue

                # A repeated explicit transport failure may still have left one invocation-fresh
                # terminal. It earns only a strict Collect candidate; the host still validates all
                # schemas, evidence scope, provenance, and firewall rules.
                found_after_failure = discover_output_artifacts(packet)
                fresh_terminals = _changed_files(
                    terminal_baseline,
                    _terminal_digest_map(packet, workspace=workspace),
                )
                if (
                    failure.transient_marker
                    and found_after_failure.evidence_paths
                    and len(fresh_terminals) == 1
                ):
                    runner_warnings.append(
                        "Codex transport remained transient after the bounded retry "
                        f"({failure.transient_marker}); invocation-fresh filesystem artifacts "
                        "were retained only as a strict host-Collect candidate"
                    )
                    break
                if failure.provider_marker:
                    raise CodingAgentProviderUnavailable(
                        failure.message + f"; explicit provider marker={failure.provider_marker}"
                    )
                raise ValueError(failure.message)
            ended_at = datetime.now(UTC)
        finally:
            _cleanup_dialogue_and_launch(dialogue, launch_dir)

        found = discover_output_artifacts(packet)
        if not found.evidence_paths:
            raise ValueError(
                "codex exec spawn produced no inspection evidence in the planner workspace"
            )
        fresh_terminals = _changed_files(
            terminal_baseline,
            _terminal_digest_map(packet, workspace=workspace),
        )
        if len(fresh_terminals) != 1:
            raise ValueError(
                "codex exec spawn must create or change exactly one terminal root artifact in "
                f"this invocation; observed {len(fresh_terminals)} fresh terminals: "
                f"{list(fresh_terminals)}"
            )
        workspace_manifest_after = _artifact_digest_map(packet, workspace=workspace)
        serialized_audits = [audit._asdict() for audit in attempt_audits]
        attempt_audit_digest = stable_hash({"attempt_audits": serialized_audits})

        transcript = self._transcript(
            run_id=run_id,
            branch=branch,
            argv=argv,
            prompt=prompt,
            result_json=result_json,
            spawn=spawn,
            source_tree_before=before,
            source_tree_after=after,
            launch_before=launch_before,
            launch_after=launch_after,
            dataset_snapshot=dataset_snapshot,
            owner_dialogue_active=dialogue_mcp_url is not None,
            dialogue_tool_names=dialogue_tool_names,
            cli_version=cli_version,
            attempt_count=attempt_count,
            runner_warnings=runner_warnings,
            attempt_audits=attempt_audits,
        )
        if "auth.json" in transcript or any(str(home) in transcript for home in staged_homes):
            raise ValueError("codex transcript would leak staged auth metadata; discarding run")
        transcript_path = workspace / "transcript.md"
        atomic_write_confined_text(
            transcript,
            workspace=workspace,
            path=transcript_path,
        )

        return AgentRunResult(
            run_id=run_id,
            branch_id=branch.branch_id,
            runner_name=self.runner_name,
            planner_identity=self._bounded_planner_identity(result_payloads),
            status=CodingAgentRunStatus.RETURNED,
            transcript_path=str(transcript_path),
            transcript_digest=stable_hash({"transcript": transcript}),
            evidence_paths=found.evidence_paths,
            dialogue_paths=found.dialogue_paths,
            plan_draft_paths=found.plan_draft_paths,
            rejection_paths=found.rejection_paths,
            source_tree_before_digest=before,
            source_tree_after_digest=after,
            source_tree_mutation_detected=False,
            blocked_actions_checked=self._blocked_actions_checked(
                dataset_snapshot,
                owner_dialogue_active=dialogue_mcp_url is not None,
                dialogue_tool_names=dialogue_tool_names,
            ),
            started_at=started_at,
            ended_at=ended_at,
            usage=_aggregate_codex_usage(result_payloads),
            planner_model_id=self.model,
            planner_reasoning_effort=self.reasoning_effort,
            planner_cli_version=cli_version,
            planner_budget_policy=CODEX_BUDGET_POLICY,
            planner_timeout_seconds=self.timeout_seconds,
            attempt_count=attempt_count,
            attempt_audit_digest=attempt_audit_digest,
            runner_warnings=runner_warnings,
            workspace_manifest_before_digest=stable_hash(workspace_manifest_before),
            workspace_manifest_after_digest=stable_hash(workspace_manifest_after),
        )

    def explore(
        self,
        *,
        task_text: str,
        workspace: Path,
        expected_artifact: Path,
        run_label: str = "",
    ) -> CoarseExploreRunResult:
        """Run a COARSE proposal-stage exploration; return one coarse facts artifact + attestations.

        A lean ``external_readonly``-only sibling of ``run()``: no branch, no owner/MCP dialogue, no
        terminal plan/rejection — one coarse facts YAML. It reuses this runner's OWN confined-spawn
        envelope (staged ``CODEX_HOME`` with mid-stream ``auth.json`` deletion, launch-dir digest,
        source-tree/config-home asserts, external read-only dataset); ``run()`` is untouched. Fails
        closed on a source-tree mutation, a lead-home write, a launch-dir/dataset-snapshot change, a
        failed spawn, or a missing coarse artifact — the same invariants ``run()`` enforces.
        """
        if self.dataset_access_mode != CODEX_DATASET_ACCESS_EXTERNAL_READONLY:
            raise ValueError("coarse explore requires dataset_access_mode=external_readonly")
        workspace = Path(workspace)
        expected_artifact = Path(expected_artifact)
        repo_root = self.source_tree_root or detect_repo_root()
        lead_home = self.lead_codex_home or default_lead_codex_home()
        cli_version = self._codex_cli_version()

        launch_dir = self._make_launch_dir()
        try:
            launch_before = directory_digest(launch_dir)
            dataset_snapshot = self._prepare_dataset_snapshot(workspace)
            prompt = self._prompt(
                task_text=task_text,
                workspace=workspace,
                dataset_snapshot=dataset_snapshot,
                coarse=True,
            )
            argv = self.build_command(workspace=workspace, launch_dir=launch_dir)

            staging = stage_codex_home(lead_home=lead_home, parent=self.codex_home_parent)
            try:
                self._assert_staged_home_location(
                    staging.home, workspace=workspace, repo_root=repo_root
                )
                subprocess_env = self._subprocess_env(staging.env)
                lead_home_before = snapshot_config_home(
                    lead_home, include_globs=CODEX_BREACH_WATCH_GLOBS
                )
                before = source_tree_digest(repo_root)
                spawn = self._spawn(
                    argv,
                    stdin_text=prompt,
                    cwd=launch_dir,
                    env=subprocess_env,
                    auth_path=staging.auth_path,
                )
                after = source_tree_digest(repo_root)
                lead_home_after = snapshot_config_home(
                    lead_home, include_globs=CODEX_BREACH_WATCH_GLOBS
                )
                launch_after = directory_digest(launch_dir)
                dataset_snapshot = self._finish_dataset_snapshot(dataset_snapshot)
            finally:
                cleanup_codex_home(staging.home)
        finally:
            shutil.rmtree(launch_dir, ignore_errors=True)

        if after != before:
            raise ValueError(
                "source_tree_mutation_detected: the Maieusis source tree changed during the coarse "
                f"codex exec explore (before={before[:12]} after={after[:12]}); discarding run"
            )
        assert_config_home_untouched(lead_home_before, lead_home_after, root=lead_home)
        # The launch dir is a disposable, repo-external scratch cwd, and Codex's workspace-write
        # sandbox legitimately permits scratch there while it runs bounded inspection code (a bare
        # "read the sample -> write one coarse YAML" task naturally scaffolds a helper in cwd). It is
        # rmtree'd above, so a launch-dir write is RECORDED, not fail-closed. This deliberately
        # diverges from the strict planner run() (whose rich workspace gives the agent no reason to
        # write to cwd) precisely because the coarse task is bare; the load-bearing boundaries below
        # and above (source tree, lead config home, dataset snapshot) stay fail-closed.
        launch_dir_scratch = launch_after != launch_before
        if dataset_snapshot.before_digest != dataset_snapshot.after_digest:
            raise ValueError("coarse codex exec modified the disposable dataset snapshot")

        result_json = self._parse_result(spawn)
        if not expected_artifact.exists():
            raise ValueError(
                f"codex exec coarse explore produced no coarse facts artifact at {expected_artifact}"
            )

        transcript = self._coarse_transcript(
            run_label=run_label,
            argv=argv,
            prompt=prompt,
            result_json=result_json,
            spawn=spawn,
            source_tree_before=before,
            source_tree_after=after,
            launch_before=launch_before,
            launch_after=launch_after,
            dataset_snapshot=dataset_snapshot,
            cli_version=cli_version,
        )
        if "auth.json" in transcript or str(staging.home) in transcript:
            raise ValueError(
                "codex coarse transcript would leak staged auth metadata; discarding run"
            )
        transcript_path = workspace / "coarse_transcript.md"
        atomic_write_confined_text(
            transcript,
            workspace=workspace,
            path=transcript_path,
        )

        display = self._inspection_runtime_display()
        return CoarseExploreRunResult(
            artifact_path=str(expected_artifact),
            transcript_path=str(transcript_path),
            explorer_adapter=CODEX_EXPLORER_ADAPTER,
            explorer_identity=self._planner_identity(result_json),
            inspection_runtime=display[1] if display else "",
            source_tree_before_digest=before,
            source_tree_after_digest=after,
            blocked_actions_checked=self._coarse_blocked_actions_checked(
                dataset_snapshot, launch_dir_scratch=launch_dir_scratch
            ),
            usage=_codex_usage(result_json.usage),
        )

    def _dialogue_mcp_config_args(
        self,
        dialogue_mcp_url: str,
        dialogue_tool_names: Sequence[str],
    ) -> list[str]:
        tools = tuple(str(name) for name in dialogue_tool_names)
        if not tools:
            raise ValueError("Codex dialogue MCP config requires at least one enabled tool")
        prefix = f"mcp_servers.{DIALOGUE_MCP_SERVER_NAME}"
        return [
            "-c",
            f"{prefix}.url={json.dumps(str(dialogue_mcp_url))}",
            "-c",
            f"{prefix}.enabled_tools={json.dumps(list(tools), separators=(',', ':'))}",
            "-c",
            f'{prefix}.default_tools_approval_mode="approve"',
        ]

    def _spawn(
        self,
        argv: list[str],
        *,
        stdin_text: str,
        cwd: Path,
        env: dict[str, str],
        auth_path: Path,
        timeout_seconds: float | None = None,
    ) -> _CodexSpawnResult:
        try:
            proc = subprocess.Popen(
                argv,
                cwd=str(cwd),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                start_new_session=True,
            )
        except FileNotFoundError as exc:
            raise ValueError(
                f"codex executable not found: {argv[0]!r}. Install the Codex CLI or pass "
                "executable=... (the live_agent spawn requires ChatGPT login)."
            ) from exc

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        thread_started = False
        auth_deleted = False

        def read_stdout() -> None:
            nonlocal auth_deleted, thread_started
            assert proc.stdout is not None
            for line in proc.stdout:
                stdout_lines.append(line)
                with contextlib.suppress(json.JSONDecodeError):
                    event = json.loads(line)
                    if isinstance(event, dict) and event.get("type") == "thread.started":
                        thread_started = True
                        try:
                            auth_deleted = delete_staged_codex_auth(auth_path)
                        except OSError:
                            auth_deleted = False

        def read_stderr() -> None:
            assert proc.stderr is not None
            for line in proc.stderr:
                stderr_lines.append(line)

        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()

        assert proc.stdin is not None
        try:
            proc.stdin.write(stdin_text)
            proc.stdin.close()
            effective_timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
            returncode = proc.wait(timeout=effective_timeout)
        except subprocess.TimeoutExpired as exc:
            kill_process_group(proc)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired as kill_exc:
                kill_process_group(proc)
                stdout_thread.join(timeout=1)
                stderr_thread.join(timeout=1)
                raise HardFamilyIntegrityViolation(
                    "codex exec process group remained alive after forced termination; "
                    "containment can no longer be proven"
                ) from kill_exc
            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)
            raise _CodexSpawnAborted(
                f"codex exec spawn exceeded {effective_timeout:.3f}s; process group killed "
                "(fail-closed, no bundle)",
                thread_started=thread_started,
                auth_deleted_after_thread_started=auth_deleted,
            ) from exc
        finally:
            with contextlib.suppress(BrokenPipeError, OSError, ValueError):
                if proc.stdin is not None and not proc.stdin.closed:
                    proc.stdin.close()

        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        if auth_path.exists():
            with contextlib.suppress(OSError):
                delete_staged_codex_auth(auth_path)
        return _CodexSpawnResult(
            stdout="".join(stdout_lines),
            stderr="".join(stderr_lines),
            returncode=returncode,
            auth_deleted_after_thread_started=auth_deleted,
        )

    def _codex_cli_version(self) -> str:
        """Return the actual executable version without trusting config or the selected model."""

        try:
            completed = subprocess.run(
                [self.executable, "--version"],
                capture_output=True,
                text=True,
                env=self._subprocess_env({}),
                timeout=10,
                check=False,
            )
        except FileNotFoundError as exc:
            raise ValueError(
                f"codex executable not found: {self.executable!r}. Install the Codex CLI or pass "
                "executable=... (the live_agent spawn requires ChatGPT login)."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ValueError("codex --version exceeded 10s (fail-closed)") from exc
        version = next(
            (line.strip() for line in completed.stdout.splitlines() if line.strip()),
            "",
        )
        if completed.returncode != 0 or not version or len(version) > 200:
            raise ValueError(
                "codex --version did not return one bounded version line (fail-closed): "
                f"returncode={completed.returncode}"
            )
        return version

    def _parse_result_payload(self, spawn: _CodexSpawnResult) -> _ParsedCodexResult:
        if not spawn.stdout.strip():
            raise ValueError(
                f"codex exec returned empty stdout (fail-closed); returncode={spawn.returncode}, "
                f"stderr={tail(spawn.stderr, 500)!r}"
            )
        events: list[Mapping[str, Any]] = []
        event_counts: Counter[str] = Counter()
        thread_id = ""
        usage: Mapping[str, Any] = {}
        final_message = ""
        for lineno, line in enumerate(spawn.stdout.splitlines(), start=1):
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"codex exec emitted malformed JSONL on line {lineno}") from exc
            if not isinstance(data, Mapping):
                raise ValueError(f"codex exec JSONL line {lineno} was not an object")
            events.append(data)
            event_type = str(data.get("type", ""))
            event_counts[event_type] += 1
            if event_type == "thread.started":
                thread_id = str(data.get("thread_id", "")).strip()
            if event_type == "turn.completed" and isinstance(data.get("usage"), Mapping):
                usage = data["usage"]
            if event_type == "item.completed":
                item = data.get("item")
                if isinstance(item, Mapping) and item.get("type") == "agent_message":
                    final_message = str(item.get("text", ""))
        return _ParsedCodexResult(
            events=events,
            event_counts=event_counts,
            thread_id=thread_id,
            usage=usage,
            final_message=final_message,
        )

    @staticmethod
    def _fatal_event_message(event: Mapping[str, Any]) -> str:
        """Extract only the documented scalar message slot from one fatal JSONL event."""

        event_type = str(event.get("type", ""))
        if event_type == "error":
            message = event.get("message")
            return str(message).strip() if isinstance(message, (str, int, float)) else ""
        if event_type == "turn.failed":
            error = event.get("error")
            if isinstance(error, Mapping):
                message = error.get("message")
                return str(message).strip() if isinstance(message, (str, int, float)) else ""
            return str(error).strip() if isinstance(error, (str, int, float)) else ""
        return ""

    @staticmethod
    def _one_marker(
        message: str,
        markers: Sequence[tuple[str, str]],
    ) -> str | None:
        searchable = message.lower()
        labels = {label for marker, label in markers if marker in searchable}
        return next(iter(labels)) if len(labels) == 1 else None

    def _canonical_fatal_surface(
        self,
        result: _ParsedCodexResult,
    ) -> _CodexFatalSurface | None:
        """Recognize only Codex's bounded fatal JSONL envelope.

        Codex 0.144.4 emits a top-level ``error`` immediately followed by a
        ``turn.failed`` carrying the exact same message and exits 1.  Some
        fixtures/versions emit only ``turn.failed``.  Any other multiplicity,
        ordering, or message disagreement remains an unknown hard failure.
        """

        indexed_errors = [
            (index, event)
            for index, event in enumerate(result.events)
            if str(event.get("type", "")) == "error"
        ]
        indexed_turn_failures = [
            (index, event)
            for index, event in enumerate(result.events)
            if str(event.get("type", "")) == "turn.failed"
        ]
        if len(indexed_turn_failures) != 1 or len(indexed_errors) > 1:
            return None
        turn_index, turn_event = indexed_turn_failures[0]
        turn_message = self._fatal_event_message(turn_event)
        if not turn_message:
            return None
        indexed_threads = [
            index
            for index, event in enumerate(result.events)
            if str(event.get("type", "")) == "thread.started"
        ]
        if len(indexed_threads) != 1 or not result.thread_id or indexed_threads[0] >= turn_index:
            return None
        indexed_turn_starts = [
            index
            for index, event in enumerate(result.events)
            if str(event.get("type", "")) == "turn.started"
        ]
        if len(indexed_turn_starts) > 1:
            return None
        if not indexed_errors:
            if indexed_turn_starts and not (
                indexed_threads[0] < indexed_turn_starts[0] < turn_index
            ):
                return None
            return _CodexFatalSurface("turn.failed", turn_message)
        error_index, error_event = indexed_errors[0]
        error_message = self._fatal_event_message(error_event)
        if error_index + 1 != turn_index or error_message != turn_message:
            return None
        if indexed_turn_starts and not (indexed_threads[0] < indexed_turn_starts[0] < error_index):
            return None
        return _CodexFatalSurface("error+turn.failed", turn_message)

    @staticmethod
    def _success_event_order_is_valid(result: _ParsedCodexResult) -> bool:
        indices: dict[str, list[int]] = {
            event_type: [
                index
                for index, event in enumerate(result.events)
                if str(event.get("type", "")) == event_type
            ]
            for event_type in ("thread.started", "turn.started", "turn.completed")
        }
        if any(len(indices[event_type]) != 1 for event_type in indices):
            return False
        return (
            indices["thread.started"][0] < indices["turn.started"][0] < indices["turn.completed"][0]
        )

    def _result_failure(
        self,
        result: _ParsedCodexResult,
        spawn: _CodexSpawnResult,
    ) -> _CodexResultFailure | None:
        """Classify strict success and one narrow fatal-event transport/provider surface."""

        fatal_events = [
            event
            for event in result.events
            if str(event.get("type", "")) in {"error", "turn.failed"}
        ]
        fatal_surface = self._canonical_fatal_surface(result)
        success = (
            spawn.returncode == 0
            and not fatal_events
            and bool(result.thread_id)
            and self._success_event_order_is_valid(result)
            and spawn.auth_deleted_after_thread_started
        )
        if success:
            return None

        fatal_event_type = fatal_surface.event_type if fatal_surface is not None else ""
        transient_marker: str | None = None
        provider_marker: str | None = None
        # Codex's documented process failure exit is 1. Other nonzero codes, a malformed fatal
        # envelope, completed-turn collision, duplicate thread, or auth-deletion failure are never
        # retryable. The mirrored error+turn.failed pair must carry one identical message.
        if (
            spawn.returncode in {0, 1}
            and fatal_surface is not None
            and result.event_counts["turn.completed"] == 0
            and result.event_counts["thread.started"] == 1
            and spawn.auth_deleted_after_thread_started
        ):
            transient_marker = self._one_marker(fatal_surface.message, _TRANSIENT_FATAL_MARKERS)
            provider_marker = self._one_marker(
                fatal_surface.message, _PROVIDER_UNAVAILABLE_FATAL_MARKERS
            )
            # A message matching both taxonomies is ambiguous/marker-colliding and therefore hard.
            if transient_marker and provider_marker:
                transient_marker = None
                provider_marker = None

        details: list[str] = [
            f"returncode={spawn.returncode}",
            f"fatal_events={len(fatal_events)}",
            f"turn_started={result.event_counts['turn.started']}",
            f"turn_completed={result.event_counts['turn.completed']}",
            f"thread_started={result.event_counts['thread.started']}",
            f"auth_deleted_after_thread_started={spawn.auth_deleted_after_thread_started}",
        ]
        if spawn.returncode != 0:
            reason = "codex exec did not exit cleanly (fail-closed)"
        elif fatal_event_type:
            reason = f"codex exec reported {fatal_event_type} (fail-closed)"
        elif result.event_counts["turn.completed"] == 0:
            reason = "codex exec JSONL did not include turn.completed (fail-closed)"
        elif not result.thread_id:
            reason = "codex exec JSONL did not include thread.started (fail-closed)"
        else:
            reason = "codex exec run did not succeed (fail-closed)"
        return _CodexResultFailure(
            message=reason + ": " + " ".join(details),
            fatal_event_type=fatal_event_type,
            transient_marker=transient_marker,
            provider_marker=provider_marker,
        )

    def _parse_result(self, spawn: _CodexSpawnResult) -> _ParsedCodexResult:
        """Strict single-attempt parser used by coarse exploration and direct tests."""

        result = self._parse_result_payload(spawn)
        if failure := self._result_failure(result, spawn):
            if failure.provider_marker:
                raise CodingAgentProviderUnavailable(
                    failure.message + f"; explicit provider marker={failure.provider_marker}"
                )
            raise ValueError(failure.message)
        return result

    def _prompt(
        self,
        *,
        task_text: str,
        workspace: Path,
        dataset_snapshot: _DatasetSnapshot,
        owner_dialogue_active: bool = False,
        coarse: bool = False,
    ) -> str:
        dataset_text = ""
        if dataset_snapshot.path is not None:
            if dataset_snapshot.access_mode == CODEX_DATASET_ACCESS_EXTERNAL_READONLY:
                dataset_text = (
                    "\n\nExternal read-only dataset root for this true-data planning run:\n"
                    f"`{dataset_snapshot.path}`\n\n"
                    "This path is NOT passed to Codex as `--add-dir`; the only writable "
                    "Codex directory is the planner workspace. Treat the external dataset "
                    "root as read-only. Do not create, remove, chmod, rename, or edit files "
                    "under it. Use it only for bounded local documentation, schema, "
                    "metadata, and small-sample inspection.\n\n" + self._inspection_runtime_text()
                )
            else:
                dataset_text = (
                    "\n\nSynthetic fixture snapshot for this 2c-2 gate:\n"
                    f"`{dataset_snapshot.path}`\n\n"
                    "Treat this snapshot as read-only. It is a development fixture for planning "
                    "contract validation, not serious scientific grounding."
                )
        if coarse:
            # Coarse Source B: no direct-file planner contract, no terminal identity hint, no MCP.
            return (
                task_text
                + dataset_text
                + "\n\n# Codex coarse explorer safety reinforcement\n\n"
                + _CODEX_COARSE_REINFORCEMENT
                + f"\n\nWorkspace: `{Path(workspace).resolve()}`\n"
                + f"Budget policy: `{CODEX_BUDGET_POLICY}` with timeout_seconds="
                + f"`{self.timeout_seconds}`.\n"
            )
        dialogue_text = (
            "\n\n# Codex Question Owner dialogue (MCP)\n\n" + _CODEX_OWNER_DIALOGUE_REINFORCEMENT
            if owner_dialogue_active
            else ""
        )
        return (
            task_text
            + dataset_text
            + "\n\n# Shared direct-file artifact contract\n\n"
            + DIRECT_FILE_ARTIFACT_CONTRACT
            + "\n\n# Codex terminal message identity hint\n\n"
            + self._terminal_identity_hint()
            + dialogue_text
            + "\n\n# Codex runner safety reinforcement\n\n"
            + _CODEX_REINFORCEMENT
            + f"\n\nPlanner workspace: `{Path(workspace).resolve()}`\n"
            + f"Budget policy: `{CODEX_BUDGET_POLICY}` with timeout_seconds="
            + f"`{self.timeout_seconds}`.\n"
        )

    def _prepare_dataset_snapshot(self, workspace: Path) -> _DatasetSnapshot:
        if self.dataset_root is None:
            empty = stable_hash({"dataset_snapshot": "not_configured"})
            return _DatasetSnapshot(
                path=None,
                before_digest=empty,
                after_digest=empty,
                access_mode=self.dataset_access_mode,
                is_copied_snapshot=False,
                added_as_writable_dir=False,
            )
        source = self.dataset_root.resolve()
        if not source.exists():
            raise ValueError(f"dataset_root does not exist: {source}")
        if self.dataset_access_mode == CODEX_DATASET_ACCESS_EXTERNAL_READONLY:
            digest = stable_hash(
                {
                    "dataset_access_mode": CODEX_DATASET_ACCESS_EXTERNAL_READONLY,
                    "dataset_root": str(source),
                }
            )
            return _DatasetSnapshot(
                path=source,
                before_digest=digest,
                after_digest=digest,
                access_mode=self.dataset_access_mode,
                is_copied_snapshot=False,
                added_as_writable_dir=False,
            )
        target = (workspace / _DATASET_SNAPSHOT_DIRNAME).resolve()
        if target.exists():
            shutil.rmtree(target)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target / source.name)
        self._make_read_only(target)
        before = directory_digest(target)
        return _DatasetSnapshot(
            path=target,
            before_digest=before,
            after_digest=before,
            access_mode=self.dataset_access_mode,
            is_copied_snapshot=True,
            added_as_writable_dir=False,
        )

    def _finish_dataset_snapshot(self, snapshot: _DatasetSnapshot) -> _DatasetSnapshot:
        if snapshot.path is None:
            return snapshot
        if not snapshot.is_copied_snapshot:
            return snapshot
        return _DatasetSnapshot(
            path=snapshot.path,
            before_digest=snapshot.before_digest,
            after_digest=directory_digest(snapshot.path),
            access_mode=snapshot.access_mode,
            is_copied_snapshot=snapshot.is_copied_snapshot,
            added_as_writable_dir=snapshot.added_as_writable_dir,
        )

    def _make_launch_dir(self) -> Path:
        parent = self.launch_parent.resolve() if self.launch_parent is not None else None
        if parent is not None:
            parent.mkdir(parents=True, exist_ok=True)
        return Path(
            tempfile.mkdtemp(prefix=_LAUNCH_DIR_PREFIX, dir=str(parent) if parent else None)
        )

    def _make_read_only(self, root: Path) -> None:
        for path in sorted(root.rglob("*"), reverse=True):
            with contextlib.suppress(OSError):
                path.chmod(0o555 if path.is_dir() else 0o444)
        with contextlib.suppress(OSError):
            root.chmod(0o555)

    def _subprocess_env(self, overlay: dict[str, str]) -> dict[str, str]:
        env = dict(os.environ)
        for key in list(env):
            if _is_secret_environment_key(key):
                env.pop(key, None)
        env.update(self._inspection_env())
        env.update(overlay)
        return env

    def _inspection_env(self) -> dict[str, str]:
        env: dict[str, str] = {}
        if (
            self.inspection_command is not None
            or self.inspection_python is not None
            or self.inspection_pythonpath is not None
        ):
            env["PYTHONDONTWRITEBYTECODE"] = "1"
        if self.inspection_pythonpath is not None:
            env["PYTHONPATH"] = str(self.inspection_pythonpath.resolve())
        env.update(self.inspection_extra_env)
        return env

    def _inspection_runtime_display(self) -> tuple[str, str] | None:
        """The (label, verbatim value) for the configured inspection runtime, or None.

        ``inspection_python`` renders the resolved interpreter path (unchanged/backward-compatible);
        ``inspection_command`` renders the multi-token command verbatim (no Path/resolve mangling).
        The two are mutually exclusive (enforced in ``__init__``).
        """
        if self.inspection_python is not None:
            return ("Configured inspection Python", str(self.inspection_python.resolve()))
        if self.inspection_command is not None:
            return ("Configured inspection command", self.inspection_command)
        return None

    def _inspection_runtime_text(self) -> str:
        parts: list[str] = []
        display = self._inspection_runtime_display()
        if display is not None:
            label, value = display
            parts.append(f"{label}: `{value}`.")
        if self.inspection_pythonpath is not None:
            parts.append(
                f"Configured inspection PYTHONPATH: `{self.inspection_pythonpath.resolve()}`."
            )
        env = self._inspection_env()
        if env:
            rendered_env = " ".join(f"{key}={value}" for key, value in sorted(env.items()))
            if display is not None:
                parts.append(
                    "Use this prefix for bounded Python checks when helpful: "
                    f"`{rendered_env} {display[1]}`."
                )
            else:
                parts.append(
                    f"The launch environment provides these inspection variables: `{rendered_env}`."
                )
        if not parts:
            return ""
        return "\n".join(parts) + "\n"

    def _validate_inspection_extra_env(self) -> None:
        for key in self.inspection_extra_env:
            if _is_secret_environment_key(key):
                raise ValueError("inspection_extra_env must not contain paid/API auth variables")

    def _blocked_actions_checked(
        self,
        snapshot: _DatasetSnapshot,
        *,
        owner_dialogue_active: bool = False,
        dialogue_tool_names: Sequence[str] = (),
    ) -> list[str]:
        common = [
            "Codex CLI subscription API call authorized for planner spawn",
            "staged CODEX_HOME auth deleted after thread.started",
            "source tree unchanged",
            "isolated launch directory unchanged",
            "no downstream bridge artifact",
            "no execution artifact",
            "branch planner workspace writes only",
        ]
        if owner_dialogue_active:
            common.extend(
                [
                    "owner dialogue via in-process localhost MCP server mcp_servers.maieusisdialogue",
                    "Codex MCP default_tools_approval_mode=approve scoped to mcp_servers.maieusisdialogue only",
                    "Codex MCP enabled_tools limited to "
                    + ", ".join(str(name) for name in dialogue_tool_names),
                    "Question Owner API credentials retained only in runner-hosted dialogue server",
                    "Codex child environment stripped of paid/API owner and reviewer credentials",
                    "owner dialogue is MCP-only; evidence and terminal artifacts remain direct-file",
                ]
            )
        if snapshot.access_mode == CODEX_DATASET_ACCESS_EXTERNAL_READONLY:
            return [
                "external dataset read access authorized for bounded planning inspection",
                "external dataset root not added as writable Codex --add-dir",
                f"generated shell network policy: {CODEX_GENERATED_SHELL_NETWORK_POLICY}",
                *common,
            ]
        return [
            "no live dataset access",
            "synthetic dataset snapshot verified unchanged",
            *common,
        ]

    def _coarse_blocked_actions_checked(
        self, snapshot: _DatasetSnapshot, *, launch_dir_scratch: bool = False
    ) -> list[str]:
        del snapshot  # coarse explore is external_readonly only; kept for signature symmetry
        launch_note = (
            "isolated launch directory is disposable repo-external scratch (removed after run"
            + ("; codex wrote bounded scratch there)" if launch_dir_scratch else ")")
        )
        return [
            "coarse proposal-stage exploration (no branch, owner, or terminal plan)",
            "external dataset read access authorized for bounded coarse inspection",
            "external dataset root not added as writable Codex --add-dir",
            f"generated shell network policy: {CODEX_GENERATED_SHELL_NETWORK_POLICY}",
            "Codex CLI subscription API call authorized for coarse explorer spawn",
            "staged CODEX_HOME auth deleted after thread.started",
            "source tree unchanged",
            launch_note,
            "no downstream bridge artifact",
            "no execution artifact",
        ]

    def _coarse_transcript(
        self,
        *,
        run_label: str,
        argv: list[str],
        prompt: str,
        result_json: _ParsedCodexResult,
        spawn: _CodexSpawnResult,
        source_tree_before: str,
        source_tree_after: str,
        launch_before: str,
        launch_after: str,
        dataset_snapshot: _DatasetSnapshot,
        cli_version: str = "",
    ) -> str:
        external_dataset_root = (
            str(dataset_snapshot.path)
            if dataset_snapshot.path is not None
            and dataset_snapshot.access_mode == CODEX_DATASET_ACCESS_EXTERNAL_READONLY
            else ""
        )
        return (
            "# Codex Coarse Local-Sample Exploration\n\n"
            f"run_label: {run_label}\n"
            f"runner: {self.runner_name}\n"
            f"executable: {self.executable}\n"
            f"cli_version: {cli_version}\n"
            f"model: {self.model}\n"
            f"reasoning_effort: {self.reasoning_effort}\n"
            f"sandbox_mode: {self.sandbox_mode}\n"
            f"approval_policy: {self.approval_policy}\n"
            f"timeout_seconds: {self.timeout_seconds}\n"
            f"budget_policy: {CODEX_BUDGET_POLICY}\n"
            f"dataset_access_mode: {dataset_snapshot.access_mode}\n"
            f"external_dataset_root: {external_dataset_root}\n"
            f"dataset_added_as_writable_dir: {dataset_snapshot.added_as_writable_dir}\n"
            f"inspection_command: {self.inspection_command or ''}\n"
            f"network_policy: {CODEX_GENERATED_SHELL_NETWORK_POLICY}\n"
            f"command_digest: {stable_hash({'argv': argv})}\n"
            f"prompt_digest: {stable_hash({'prompt': prompt})}\n"
            f"returncode: {spawn.returncode}\n"
            f"thread_id: {result_json.thread_id}\n"
            f"event_counts: {dict(result_json.event_counts)}\n"
            f"usage: {dict(result_json.usage)}\n"
            f"auth_deleted_after_thread_started: {spawn.auth_deleted_after_thread_started}\n"
            f"source_tree_before_digest: {source_tree_before}\n"
            f"source_tree_after_digest: {source_tree_after}\n"
            f"launch_dir_unchanged: {launch_before == launch_after}\n"
            f"dataset_snapshot_unchanged: "
            f"{dataset_snapshot.before_digest == dataset_snapshot.after_digest}\n"
            f"final_message_summary: {tail(result_json.final_message, 1000)}\n\n"
            "This is a coarse, proposal-safe local-sample exploration. No downstream bridge "
            "artifact, no execution authority, no branch/owner dialogue. Source tree and dataset "
            "surface verified unchanged.\n\n"
            "## stderr (tail)\n\n"
            "```\n"
            f"{tail(spawn.stderr, 4000)}\n"
            "```\n"
        )

    def _assert_staged_home_location(
        self,
        home: Path,
        *,
        workspace: Path,
        repo_root: Path,
    ) -> None:
        resolved_home = home.resolve()
        forbidden_roots = (workspace.resolve(), (repo_root / "runs").resolve())
        for forbidden in forbidden_roots:
            if self._is_relative_to(resolved_home, forbidden):
                raise ValueError(
                    "temporary CODEX_HOME must be outside the planner workspace and repo runs"
                )

    def _is_relative_to(self, path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
        except ValueError:
            return False
        return True

    def _planner_identity(self, result_json: _ParsedCodexResult) -> str:
        return f"codex:{result_json.thread_id}" if result_json.thread_id else "codex"

    def _bounded_planner_identity(
        self,
        result_payloads: Sequence[_ParsedCodexResult],
    ) -> str:
        if len(result_payloads) <= 1:
            return self._planner_identity(
                result_payloads[-1]
                if result_payloads
                else _ParsedCodexResult([], Counter(), "", {}, "")
            )
        thread_ids = [result.thread_id for result in result_payloads if result.thread_id]
        digest = stable_hash(
            {
                "model": self.model,
                "reasoning_effort": self.reasoning_effort,
                "attempt_count": len(result_payloads),
                "thread_ids": thread_ids,
            }
        )
        return f"codex:{self.model}:bounded-attempts:{digest[:12]}"

    def _terminal_identity_hint(self) -> str:
        return (
            "For terminal PlanningMessage YAML identity fields in this Codex run, use "
            f"provider_id: codex, model_id: {self.model}, "
            "session_id: codex-exec-session, prompt_version: dataset_planner/v2. "
            "The trusted host run record remains the authoritative launch identity."
        )

    def _transcript(
        self,
        *,
        run_id: str,
        branch: QuestionFamilyBranch,
        argv: list[str],
        prompt: str,
        result_json: _ParsedCodexResult,
        spawn: _CodexSpawnResult,
        source_tree_before: str,
        source_tree_after: str,
        launch_before: str,
        launch_after: str,
        dataset_snapshot: _DatasetSnapshot,
        owner_dialogue_active: bool = False,
        dialogue_tool_names: Sequence[str] = (),
        cli_version: str = "",
        attempt_count: int = 1,
        runner_warnings: Sequence[str] = (),
        attempt_audits: Sequence[_CodexAttemptAudit] = (),
    ) -> str:
        dataset_path = str(dataset_snapshot.path) if dataset_snapshot.path is not None else ""
        external_dataset_root = (
            dataset_path
            if dataset_snapshot.access_mode == CODEX_DATASET_ACCESS_EXTERNAL_READONLY
            else ""
        )
        dialogue_mcp_config = (
            f"mcp_servers.{DIALOGUE_MCP_SERVER_NAME}" if owner_dialogue_active else ""
        )
        return (
            "# Codex Dataset Planner Spawn\n\n"
            f"run_id: {run_id}\n"
            f"branch_id: {branch.branch_id}\n"
            f"runner: {self.runner_name}\n"
            f"executable: {self.executable}\n"
            f"cli_version: {cli_version}\n"
            f"model: {self.model}\n"
            f"reasoning_effort: {self.reasoning_effort}\n"
            f"sandbox_mode: {self.sandbox_mode}\n"
            f"approval_policy: {self.approval_policy}\n"
            f"timeout_seconds: {self.timeout_seconds}\n"
            f"budget_policy: {CODEX_BUDGET_POLICY}\n"
            f"dataset_access_mode: {dataset_snapshot.access_mode}\n"
            f"external_dataset_root: {external_dataset_root}\n"
            f"dataset_added_as_writable_dir: {dataset_snapshot.added_as_writable_dir}\n"
            f"inspection_python: "
            f"{self.inspection_python.resolve() if self.inspection_python else ''}\n"
            f"inspection_command: {self.inspection_command or ''}\n"
            f"inspection_pythonpath_configured: {self.inspection_pythonpath is not None}\n"
            f"network_policy: {CODEX_GENERATED_SHELL_NETWORK_POLICY}\n"
            f"owner_dialogue_active: {owner_dialogue_active}\n"
            f"owner_dialogue_mcp: "
            f"{DIALOGUE_MCP_SERVER_NAME if owner_dialogue_active else ''}\n"
            f"owner_dialogue_mcp_config: {dialogue_mcp_config}\n"
            f"owner_dialogue_mcp_approval: "
            f"{'default_tools_approval_mode=approve (per-server)' if owner_dialogue_active else ''}\n"
            f"owner_dialogue_mcp_enabled_tools: {list(dialogue_tool_names)}\n"
            f"spawn_attempts: {attempt_count}\n"
            f"runner_warnings: {json.dumps(list(runner_warnings))}\n"
            "attempt_audits: "
            f"{json.dumps([audit._asdict() for audit in attempt_audits], sort_keys=True)}\n"
            f"command_digest: {stable_hash({'argv': argv})}\n"
            f"prompt_digest: {stable_hash({'prompt': prompt})}\n"
            f"returncode: {spawn.returncode}\n"
            f"thread_id: {result_json.thread_id}\n"
            f"event_counts: {dict(result_json.event_counts)}\n"
            f"usage: {dict(result_json.usage)}\n"
            f"auth_deleted_after_thread_started: {spawn.auth_deleted_after_thread_started}\n"
            f"source_tree_before_digest: {source_tree_before}\n"
            f"source_tree_after_digest: {source_tree_after}\n"
            f"launch_dir_unchanged: {launch_before == launch_after}\n"
            f"dataset_snapshot_path: {dataset_path}\n"
            f"dataset_snapshot_unchanged: "
            f"{dataset_snapshot.before_digest == dataset_snapshot.after_digest}\n"
            f"final_message_summary: {tail(result_json.final_message, 1000)}\n\n"
            "This is a planning-only Codex spawn. "
            + (
                "Question Owner dialogue was available only through the runner-hosted "
                "localhost MCP server; paid owner credentials were not exposed to the "
                "Codex child process. "
                if owner_dialogue_active
                else "No MCP owner dialogue was configured. "
            )
            + "No downstream bridge artifact, no execution authority. Source tree and "
            "dataset surface verified unchanged.\n\n"
            "## stderr (tail)\n\n"
            "```\n"
            f"{tail(spawn.stderr, 4000)}\n"
            "```\n"
        )
