"""Auto-spawn agent runner: launch Claude Code headless (``claude -p``).

The Bash-less toy-fixture spawn came first. The real-dataset path adds an
``external_readonly`` mode that mirrors the Codex ``external_readonly`` half:
the dataset root is named only in the prompt/config and is **never** passed as ``--add-dir``,
Bash is re-enabled so the agent can read real parquet with a configured inspection Python, and
the whole thing is confined by **Claude's own native strict Bash sandbox** (``--settings``), not by
an outer ``sandbox-exec`` wrapper.

The runner plugs into the same ``AgentRunner`` seam as the in-process runners, so the shared
``RealPlannerHost`` Collect (read workspace artifacts -> validate -> assemble a
``PlannerReturnedArtifactBundle``) is reused unchanged; only the *launch* half is new.

An optional **MCP owner-dialogue mode**: when the host passes a
``dialogue_server`` (a ``ScientificDialogueServer`` carrying the real Question Owner provider),
the runner self-hosts it over localhost HTTP (``LocalDialogueMcpServer``) and wires
``--mcp-config`` into ``claude -p`` so the spawned agent can ask the real Question Owner
mid-inspection. Scope stays narrow: MCP carries owner dialogue + read context/state only;
inspection evidence and the terminal plan/rejection still travel as files (direct-file contract),
so Collect is unchanged. The owner API call happens inside THIS process; the agent only ever
reaches ``localhost`` and its paid/API-key env stays stripped.

Safety envelope (non-negotiable; see the phase plan):

- **No dollar budget.** Bound by a turn cap (``--max-turns``) plus a hard wall-clock timeout
  (``timeout_seconds``, <= 30 min). On timeout the *whole process group* is killed
  (``start_new_session=True`` + ``os.killpg``). Over-turns / timeout / no valid artifact => the run
  **fails closed** (raises; the host never builds a bundle). Paid/API-key env is stripped so the
  spawn stays subscription-billed (no metering).
- **Source tree immutable.** The Maieusis-repo source-tree digest is measured before and after the
  spawn; any change fails the run closed.
- **Config-home isolated (Layer A).** ``CLAUDE_CONFIG_DIR`` is relocated to a throwaway home under
  the workspace and the whole lead ``~/.claude`` is snapshotted before/after; any write there
  (the original 2c-1 breach) fails closed.

Dataset-access modes:

- ``add_dir`` (2c-1, toy fixture): no Bash (Read/Grep/Glob/Write only); the tiny dataset is passed
  via ``--add-dir``; an optional outer ``sandbox-exec`` (``os_process_sandbox``) may confine writes.
- ``external_readonly`` (real-dataset phase): Bash on, confined by Claude's native strict sandbox
  settings (``claude_native_sandbox_settings``): OS-level filesystem confinement (dataset read-only,
  workspace-write only) + no bash network + no unsandboxed-retry escape hatch. The dataset root is
  NOT ``--add-dir`` (so the non-sandboxed Write tool cannot target it), cwd is a repo-external launch
  dir (so no project ``CLAUDE.md`` is inherited), and a configured inspection Python/PYTHONPATH reads
  real parquet. The outer ``sandbox-exec`` wrapper is FORBIDDEN here: Claude's native sandbox is
  itself Seatbelt-based and cannot be nested inside another Seatbelt.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, NamedTuple

from ...io import load_model
from ...provenance import sha256_file, stable_hash
from ...schemas.coarse_dataset_facts import CoarseExploreRunResult
from ...schemas.planner_run import CodingAgentRunStatus, CodingAgentRunUsage
from ...schemas.question_family_branch import QuestionFamilyBranch
from ...services.planning.dataset_planner_packet import (
    DatasetPlannerHandoffManifest,
    DatasetPlannerTaskPacket,
    planner_packet_digest,
)
from ...services.planning.direct_file_artifact_contract import DIRECT_FILE_ARTIFACT_CONTRACT
from ...services.planning.planner_failures import CodingAgentProviderUnavailable
from .agent_runner import AgentRunResult, discover_output_artifacts
from .dialogue_mcp_server import DIALOGUE_MCP_SERVER_NAME, LocalDialogueMcpServer
from .spawn_sandbox import (
    BREACH_WATCH_GLOBS,
    assert_config_home_untouched,
    build_config_home,
    claude_native_sandbox_settings,
    default_lead_config_home,
    snapshot_config_home,
    wrap_argv_in_os_sandbox,
)
from .subprocess_utils import detect_repo_root as _detect_repo_root
from .subprocess_utils import kill_process_group as _kill_process_group
from .subprocess_utils import source_tree_digest
from .subprocess_utils import tail as _tail


def _claude_usage(result_json: Mapping[str, Any]) -> CodingAgentRunUsage | None:
    """Build run usage from a ``claude -p --output-format json`` result (total_cost_usd + tokens)."""
    cost = result_json.get("total_cost_usd")
    usage_obj = result_json.get("usage")
    input_tokens = usage_obj.get("input_tokens") if isinstance(usage_obj, Mapping) else None
    output_tokens = usage_obj.get("output_tokens") if isinstance(usage_obj, Mapping) else None
    total_tokens: int | None = None
    if input_tokens is not None or output_tokens is not None:
        total_tokens = int(input_tokens or 0) + int(output_tokens or 0)
    if cost is None and total_tokens is None:
        return None
    return CodingAgentRunUsage(
        input_tokens=int(input_tokens) if input_tokens is not None else None,
        output_tokens=int(output_tokens) if output_tokens is not None else None,
        total_tokens=total_tokens,
        cost_usd=float(cost) if cost is not None else None,
        source="claude_code",
    )


def _aggregate_claude_usage(
    result_payloads: Sequence[Mapping[str, Any]],
) -> CodingAgentRunUsage | None:
    """Sum usage over bounded attempts so retry provenance never reports only the last turn."""

    usages = [usage for payload in result_payloads if (usage := _claude_usage(payload)) is not None]
    if not usages:
        return None

    def optional_int_sum(field: str) -> int | None:
        present = [int(value) for usage in usages if (value := getattr(usage, field)) is not None]
        return sum(present) if present else None

    costs = [usage.cost_usd for usage in usages if usage.cost_usd is not None]

    return CodingAgentRunUsage(
        input_tokens=optional_int_sum("input_tokens"),
        output_tokens=optional_int_sum("output_tokens"),
        total_tokens=optional_int_sum("total_tokens"),
        cost_usd=sum(costs) if costs else None,
        source="claude_code_bounded_attempts",
    )


if TYPE_CHECKING:  # reserved MCP owner-dialogue collaborators
    from ...mcp import ScientificDialogueServer
    from ..scientific_agents import ScientificAgentProvider

CLAUDE_CODE_AGENT_RUNNER_NAME = "claude-code-agent-runner"
# Coarse Source-B provenance tag. Matches CLAUDE_CODE_ADAPTER_NAME in claude_code_host.py; defined
# here (not imported) because the host imports the runner, so the reverse import would be a cycle.
CLAUDE_CODE_EXPLORER_ADAPTER = "claude_code"

DatasetAccessMode = Literal["add_dir", "external_readonly"]
CLAUDE_DATASET_ACCESS_ADD_DIR: DatasetAccessMode = "add_dir"
CLAUDE_DATASET_ACCESS_EXTERNAL_READONLY: DatasetAccessMode = "external_readonly"
CLAUDE_NATIVE_SANDBOX_BASH_NETWORK_POLICY = "claude_native_bash_sandbox_no_network_localhost_only"

_DEFAULT_ALLOWED_TOOLS: tuple[str, ...] = ("Read", "Grep", "Glob", "Write")
_EXTERNAL_READONLY_TOOL = "Bash"
_DEFAULT_DISALLOWED_TOOLS: tuple[str, ...] = ("WebFetch", "WebSearch")
_DEFAULT_MAX_TURNS = 40
_DEFAULT_TIMEOUT_SECONDS = 1800  # hard <= 30-min wall-clock backstop
_DEFAULT_MODEL = "opus"
_DEFAULT_PERMISSION_MODE = "dontAsk"
_LAUNCH_DIR_PREFIX = "maieusis-claude-launch-"
_MAX_TRANSIENT_ATTEMPTS = 2
_DEFAULT_TRANSIENT_RETRY_BACKOFF_SECONDS = 2.0

# These are narrow transport/provider-host signals, not a generic exemption for a failed model
# turn.  Schema errors, max-turn exhaustion, refusals, invalid JSON, timeouts, and scientific
# terminals remain fail-closed.  The live release canary observed the first marker verbatim.
_TRANSIENT_RESULT_MARKERS: tuple[tuple[str, str], ...] = (
    ("connection closed mid-response", "connection_closed_mid_response"),
    ("connection reset", "connection_reset"),
    ("econnreset", "connection_reset"),
    ("socket hang up", "socket_hang_up"),
    ("internal server error", "provider_internal_server_error"),
    ("server_error", "provider_server_error"),
    ("overloaded", "provider_overloaded"),
    ("http 529", "provider_overloaded"),
    ("http 503", "provider_unavailable"),
    ("rate limit", "provider_rate_limit"),
    ("rate_limit", "provider_rate_limit"),
)

_TRANSIENT_RETRY_TASK_NOTE = """

# Bounded transient retry

A prior Claude Code transport attempt ended before the host received a success result. The same
branch-local workspace may therefore contain useful evidence or a partially written terminal
artifact. Inspect the existing files and current branch state first. Preserve valid evidence,
repair or replace incomplete YAML, and finish with exactly one valid root terminal artifact. Do
not duplicate owner dialogue or retry a scope whose dialogue limit is already closed. All original
planning, evidence, filesystem, and confirmation-firewall rules still apply.
"""

# Stripped from the spawn env so a stray API key can't outrank the subscription OAuth token
# (auth precedence puts ANTHROPIC_API_KEY above CLAUDE_CODE_OAUTH_TOKEN) and the run stays
# subscription-billed with no metering. CLAUDE_CODE_OAUTH_TOKEN is preserved (different prefix).
_PAID_OR_SECRET_ENV_PREFIXES: tuple[str, ...] = ("OPENAI_", "ANTHROPIC_")
_PAID_OR_SECRET_ENV_EXACT: tuple[str, ...] = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "MAIEUSIS_ALLOW_PRO_MODEL",
    "MAIEUSIS_OPENAI_MODEL",
    "MAIEUSIS_OPENAI_PROVIDER",
)

_CLAUDE_WORKSPACE_REINFORCEMENT = (
    "You are running headless as the Maieusis dataset-planning coding agent. Write files "
    "ONLY under the current working directory, which is this branch's planner workspace. "
    "Do not create, edit, move, or delete any file outside it, and do not modify the "
    "Maieusis source tree. This is planning, not execution: produce only typed planning "
    "artifacts (inspection evidence and one terminal plan, rejection, or escalation).\n\n"
    "You have NO shell in this session: the Bash tool is denied. Use only Read, Grep, "
    "Glob, and Write. Do not try to run commands, scripts, or code — those attempts are "
    "denied and only waste turns.\n\n"
    "Do NOT compute or fill any provenance digest / hash fields (source_digest, "
    "query_or_command_digest, result_digest, input_digest, output_digest, payload_digest). "
    "Omit them or leave a short placeholder; the trusted host recomputes and stamps ALL "
    "digests when it collects your artifacts. Never invent a hash. Spend your turns on the "
    "science, not on hashing.\n\n"
    "Write exactly: inspection-evidence YAML files under the evidence directory, and a "
    "single terminal artifact (a plan draft, a rejection, or an escalation) at the path the "
    "packet specifies. "
    "Do NOT write a run_record, a returned bundle, or a validation report — the host writes "
    "those. Finish as soon as your evidence and the single terminal artifact are written.\n\n"
    "The planning firewall is behavioral, not a vocabulary ban. Ordinary scientific planning "
    "language, candidate estimands/models, and honestly labeled bounded diagnostics are allowed. "
    "Do not run a full scientific pipeline, search for significance, optimize the question against "
    "target outcomes, access confirmation outcomes, make confirmatory claims, or present a bounded "
    "planning diagnostic as a discovery."
)

_CLAUDE_EXTERNAL_READONLY_REINFORCEMENT = (
    "You are running headless as the Maieusis dataset-planning coding agent on a REAL, read-only "
    "dataset. Write files ONLY under the branch planner workspace named in the task packet. Do not "
    "create, edit, move, or delete any file outside it — not the dataset, not the Maieusis source "
    "tree, not any home or config directory. This is planning, not execution: produce only typed "
    "planning artifacts (inspection evidence and one terminal plan, rejection, or escalation).\n\n"
    "You HAVE a Bash tool, confined by an OS-level sandbox: it can READ the dataset and WRITE the "
    "planner workspace, but it cannot write the dataset and has no network. Use Bash with the "
    "configured inspection Python only for BOUNDED local inspection — documentation, schema, column "
    "names, metadata queries, and small samples. Do NOT run a full or long-running analysis, do NOT "
    "search for effects or significance, do NOT produce confirmatory statistics, and do NOT load "
    "full raw-array or neural-matrix surfaces.\n\n"
    "Do NOT compute or fill any provenance digest / hash fields (source_digest, "
    "query_or_command_digest, result_digest, input_digest, output_digest, payload_digest). "
    "Omit them or leave a short placeholder; the trusted host recomputes and stamps ALL digests "
    "when it collects your artifacts. Never invent a hash.\n\n"
    "Write exactly: inspection-evidence YAML files under the evidence directory, and a single "
    "terminal artifact (a plan draft, a rejection, or an escalation) at the path the packet "
    "specifies. Do NOT write a run_record, a returned bundle, or a validation report — the host "
    "writes those. Finish as soon as your evidence and the single terminal artifact are written.\n\n"
    "The planning firewall is behavioral, not a vocabulary ban. Ordinary scientific planning "
    "language, candidate estimands/models, and honestly labeled bounded diagnostics are allowed. "
    "Do not run a full scientific pipeline, search for significance, optimize the question against "
    "target outcomes, access confirmation outcomes, make confirmatory claims, or present a bounded "
    "planning diagnostic as a discovery."
)

_WORKSPACE_ONLY_REINFORCEMENT = (
    _CLAUDE_WORKSPACE_REINFORCEMENT
    + "\n\n# Shared direct-file artifact contract\n\n"
    + DIRECT_FILE_ARTIFACT_CONTRACT
)

# Appended ONLY in dialogue mode. Overrides the direct-file contract's "the tool names in the
# packet are optional MCP owner-dialogue schema context only" note for owner dialogue specifically: those
# owner-dialogue MCP tools are now ACTIVE. Evidence + the terminal artifact still go to FILES.
_CLAUDE_DIALOGUE_REINFORCEMENT = (
    f"# Question Owner dialogue (MCP) — ACTIVE this run\n\n"
    f"You also have live MCP tools from the server `{DIALOGUE_MCP_SERVER_NAME}` that connect you "
    "to the real Question Owner for THIS branch. This SUPERSEDES the direct-file contract's note "
    "that the packet tool names are 'future context only' — for owner dialogue they are active now:\n\n"
    "- `branch_get_context` / `branch_get_state` — read the branch's scientific intent + state.\n"
    "- `branch_submit_clarification_request` then `branch_ask_question_owner` — ask the Owner to "
    "resolve a scientific ambiguity.\n"
    "- `branch_submit_operationalization` then `branch_ask_question_owner` — ask the Owner to "
    "accept / revise / reject a proposed operationalization.\n\n"
    "USE THEM WHEN a scientific ambiguity would otherwise force you to GUESS how to operationalize "
    "a construct, choose a contrast, or reduce the question — do NOT guess. Submit the message, "
    "call `branch_ask_question_owner`, and FOLLOW the Owner's ruling in your plan. If the Owner's "
    "ruling cannot be satisfied by this dataset without changing the scientific intent, write a "
    "typed rejection or escalation FILE instead of trivializing the question.\n\n"
    "SCOPE: these MCP tools are for owner dialogue + reading context/state ONLY. Do NOT submit "
    "inspection evidence, plan drafts, rejections, feasibility findings, or escalations through "
    "MCP — those STILL go to FILES per the direct-file contract above. Every message you submit "
    "must carry an explicit `scope` (family for shared clarification; variant with a matching "
    "`variant_id`/`question_seed_id` for a variant-specific operationalization).\n\n"
    "CONVERSELY, the owner dialogue lives ONLY in the MCP channel and the host records it for you: "
    "do NOT ALSO write any clarification_request, operationalization_proposal, owner-ruling, or "
    "owner-response YAML file to the dialogue directory, and do NOT add fields like `owner_ruling` "
    "or `notes` to any file. Put QuestionFamilyInspectionEvidence ONLY in the evidence directory; "
    "put any DatasetFeasibilityFinding ONLY in the dialogue directory. In dialogue mode the ONLY "
    "files you write are: inspection evidence, any dataset_feasibility_finding, and the single "
    "terminal artifact (plan/rejection/escalation)."
)


# GF-2a coarse Source-B reinforcement (external_readonly only). A lean cousin of the planner
# external_readonly reinforcement: it does NOT carry the planner direct-file artifact contract
# (coarse produces one coarse facts YAML, not evidence + a terminal plan/rejection). The
# authoritative coarsen-by-contract lives in the coarse task.md; this echoes only the safety-
# critical parts. All lowercase-"one" (the dataset-agnostic guard forbids the uppercase acronym).
_CLAUDE_COARSE_EXTERNAL_READONLY_REINFORCEMENT = (
    "You are running headless as the Maieusis COARSE dataset explorer (proposal stage) on a REAL, "
    "read-only dataset SAMPLE. Write files ONLY under the workspace named in the task. Do not "
    "create, edit, move, or delete any file outside it — not the dataset, not the Maieusis source "
    "tree, not any home or config directory.\n\n"
    "You HAVE a Bash tool, confined by an OS-level sandbox: it can READ the dataset sample and "
    "WRITE the workspace, but it cannot write the dataset and has no network. Use the configured "
    "inspection runtime only for BOUNDED, coarse inspection — documentation, coarse shape, and "
    "small samples. Do NOT run a full or long-running analysis, do NOT search for effects or "
    "significance, and do NOT load full raw-array surfaces.\n\n"
    "Stay COARSE. Produce exactly one coarse facts YAML at the path the task specifies. NEVER "
    "report exact column or field names, table schemas, or exact row/trial/session/unit counts; "
    "report only coarse kinds and order-of-magnitude or approximate scale facts. Do not emit a "
    "columns / schema / table_schema field.\n\n"
    "Do NOT compute or fill any provenance / identity / digest fields; the trusted host stamps "
    "those. Never invent a hash.\n\n"
    "A strict proposal-safe firewall scans your artifact. Do NOT use execution/analysis vocabulary "
    "anywhere — not even in a disclaimer such as 'no effect search was run'; just describe the "
    "coarse observations. Finish as soon as the single coarse facts YAML is written."
)


class _SpawnResult(NamedTuple):
    stdout: str
    stderr: str
    returncode: int


class _ClaudeResultFailure(NamedTuple):
    message: str
    transient_marker: str | None
    provider_marker: str | None


class _ClaudeAttemptAudit(NamedTuple):
    attempt_index: int
    command_digest: str
    returncode: int
    result_subtype: str
    is_error: bool
    session_id: str
    num_turns: int | None
    duration_ms: int | None
    transient_marker: str | None
    artifact_manifest_before_digest: str
    artifact_manifest_after_digest: str
    changed_terminal_files: tuple[str, ...]


def _root_terminal_paths(packet: DatasetPlannerTaskPacket) -> tuple[Path, Path, Path]:
    plan_path = Path(packet.output_paths.plan_draft_path)
    rejection_path = Path(packet.output_paths.rejection_path)
    return plan_path, rejection_path, plan_path.parent / "escalation.yaml"


def _safe_workspace_digest(path: Path, *, workspace: Path) -> str:
    resolved_workspace = workspace.resolve()
    resolved_path = path.resolve()
    if resolved_path != resolved_workspace and resolved_workspace not in resolved_path.parents:
        raise ValueError(f"planner artifact escaped workspace: {path}")
    if path.is_symlink():
        raise ValueError(f"planner artifact must not be a symlink: {path}")
    return sha256_file(path)


def _artifact_digest_map(
    packet: DatasetPlannerTaskPacket,
    *,
    workspace: Path,
) -> dict[str, str]:
    """Hash only planner-owned output surfaces, using workspace-relative path identities."""

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
            raise ValueError(f"planner artifact is not a regular file: {path}")
        digest = _safe_workspace_digest(path, workspace=workspace)
        relative = str(path.resolve().relative_to(workspace.resolve()))
        result[relative] = digest
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
            raise ValueError(f"planner terminal artifact is not a regular file: {path}")
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
    for path in (Path(handoff.packet_path), Path(handoff.task_path)):
        if not path.is_file():
            raise ValueError(f"planner handoff context file is missing: {path}")
        digest = _safe_workspace_digest(path, workspace=workspace)
        result[str(path.resolve().relative_to(workspace.resolve()))] = digest
    return result


def _changed_files(before: Mapping[str, str], after: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(sorted(path for path, digest in after.items() if before.get(path) != digest))


def _optional_nonnegative_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


class ClaudeCodeAgentRunner:
    """Launch ``claude -p`` to inspect a dataset and write typed planner artifacts."""

    runner_name = CLAUDE_CODE_AGENT_RUNNER_NAME

    def __init__(
        self,
        *,
        executable: str = "claude",
        model: str = _DEFAULT_MODEL,
        max_turns: int = _DEFAULT_MAX_TURNS,
        timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
        permission_mode: str = _DEFAULT_PERMISSION_MODE,
        allowed_tools: Sequence[str] = _DEFAULT_ALLOWED_TOOLS,
        disallowed_tools: Sequence[str] = _DEFAULT_DISALLOWED_TOOLS,
        dataset_root: str | Path | None = None,
        dataset_access_mode: DatasetAccessMode = CLAUDE_DATASET_ACCESS_ADD_DIR,
        inspection_python: str | Path | None = None,
        inspection_command: str | None = None,
        inspection_pythonpath: str | Path | None = None,
        inspection_extra_env: Mapping[str, str] | None = None,
        source_tree_root: str | Path | None = None,
        bare: bool = False,
        os_process_sandbox: bool = False,
        lead_config_home: str | Path | None = None,
        launch_parent: str | Path | None = None,
        transient_retry_backoff_seconds: float = _DEFAULT_TRANSIENT_RETRY_BACKOFF_SECONDS,
    ) -> None:
        if max_turns <= 0:
            raise ValueError("ClaudeCodeAgentRunner requires a positive max_turns cap")
        if timeout_seconds <= 0 or timeout_seconds > 2400:
            raise ValueError(
                "ClaudeCodeAgentRunner timeout_seconds must be in (0, 2400] (<= 40 min backstop)"
            )
        if transient_retry_backoff_seconds < 0 or transient_retry_backoff_seconds > 30:
            raise ValueError("transient_retry_backoff_seconds must be in [0, 30]")
        if dataset_access_mode not in (
            CLAUDE_DATASET_ACCESS_ADD_DIR,
            CLAUDE_DATASET_ACCESS_EXTERNAL_READONLY,
        ):
            raise ValueError("unsupported ClaudeCodeAgentRunner dataset_access_mode")
        allowed = tuple(allowed_tools)
        if dataset_access_mode == CLAUDE_DATASET_ACCESS_EXTERNAL_READONLY:
            if dataset_root is None:
                raise ValueError("external_readonly dataset access requires dataset_root")
            if os_process_sandbox:
                # Claude's native Bash sandbox is itself Seatbelt-based; nesting it inside our
                # outer sandbox-exec fails at the first command (empirically confirmed). The
                # native strict settings ARE the sandbox for the real-dataset Bash path.
                raise ValueError(
                    "external_readonly must not use os_process_sandbox (outer Seatbelt cannot "
                    "nest Claude's native Bash sandbox); it uses claude_native_sandbox_settings"
                )
            # Bash is required to read real parquet; it is confined by the native strict sandbox.
            if _EXTERNAL_READONLY_TOOL not in allowed:
                allowed = (*allowed, _EXTERNAL_READONLY_TOOL)
        else:
            if _EXTERNAL_READONLY_TOOL in allowed:
                # add_dir (2c-1) is deliberately Bash-less; re-enabling shell execution requires
                # the external_readonly native-sandbox path, not a flag toggle here.
                raise ValueError(
                    "ClaudeCodeAgentRunner (add_dir) must not allow Bash; use the "
                    "external_readonly native-sandbox path"
                )
        self.executable = executable
        self.model = model
        self.max_turns = max_turns
        self.timeout_seconds = timeout_seconds
        self.permission_mode = permission_mode
        self.allowed_tools = allowed
        self.disallowed_tools = tuple(disallowed_tools)
        self.dataset_root = Path(dataset_root) if dataset_root is not None else None
        self.dataset_access_mode = dataset_access_mode
        if inspection_command is not None and inspection_python is not None:
            raise ValueError(
                "inspection_command and inspection_python are mutually exclusive; pass one"
            )
        self.inspection_python = Path(inspection_python) if inspection_python is not None else None
        # A multi-token inspection runtime (e.g. an ephemeral per-format interpreter) that must be
        # rendered VERBATIM — never wrapped in Path()/resolve() (which would mangle a command with
        # flags into one bogus path). Mutually exclusive with the single-interpreter inspection_python.
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
        self.bare = bare
        # Layer B (outer OS process sandbox) is opt-in for the Bash-less 2c-1 add_dir path only;
        # external_readonly forbids it (see __init__ guard) and uses the native strict sandbox.
        self.os_process_sandbox = os_process_sandbox
        # The lead config home the spawn must not touch. Defaults to the real ~/.claude for live
        # runs; tests inject a quiescent temp dir so a concurrent lead session's writes don't trip
        # the whole-tree containment assertion.
        self.lead_config_home = Path(lead_config_home) if lead_config_home is not None else None
        self.launch_parent = Path(launch_parent) if launch_parent is not None else None
        self.transient_retry_backoff_seconds = transient_retry_backoff_seconds

    @property
    def _external_readonly(self) -> bool:
        return self.dataset_access_mode == CLAUDE_DATASET_ACCESS_EXTERNAL_READONLY

    def build_command(
        self,
        *,
        task_text: str,
        workspace: Path,
        mcp_config_json: str | None = None,
        dialogue_tool_names: Sequence[str] = (),
        coarse: bool = False,
        max_turns_override: int | None = None,
    ) -> list[str]:
        """Return the exact ``claude -p`` argv (pure; safe to unit-test without spawning).

        Dialogue mode: pass ``mcp_config_json`` (an inline ``--mcp-config`` HTTP entry)
        and ``dialogue_tool_names`` (the ``mcp__<server>__<tool>`` names). They add
        ``--mcp-config``/``--strict-mcp-config`` and extend ``--allowedTools`` so the spawned
        agent may call the owner-dialogue tools; the append-system-prompt then explains them.

        GF-2a coarse mode (``coarse=True``, external_readonly only): the only change is the
        append-system-prompt (the coarse Source-B reinforcement instead of the planner one); every
        flag — settings sandbox, workspace ``--add-dir``, dataset NOT added — is identical. The
        default (``coarse=False``) is byte-for-byte the planner path, so ``run()`` is unaffected.
        """
        workspace = Path(workspace).resolve()
        attempt_max_turns = self.max_turns if max_turns_override is None else max_turns_override
        if attempt_max_turns <= 0 or attempt_max_turns > self.max_turns:
            raise ValueError("max_turns_override must be in (0, configured max_turns]")
        dialogue = mcp_config_json is not None
        allowed = (*self.allowed_tools, *tuple(dialogue_tool_names))
        argv: list[str] = [self.executable]
        if self.bare:
            argv.append("--bare")
        argv += [
            "-p",
            task_text,
            "--output-format",
            "json",
            "--max-turns",
            str(attempt_max_turns),
            "--model",
            self.model,
            "--permission-mode",
            self.permission_mode,
            "--allowedTools",
            ",".join(allowed),
        ]
        if self.disallowed_tools:
            argv += ["--disallowedTools", ",".join(self.disallowed_tools)]
        system_prompt = (
            self._coarse_append_system_prompt(workspace)
            if coarse
            else self._append_system_prompt(workspace, dialogue=dialogue)
        )
        argv += ["--append-system-prompt", system_prompt]
        if self._external_readonly:
            # Strict native Bash sandbox (dataset RO, workspace-write only, no bash network, no
            # unsandboxed-retry escape hatch). Passed as an inline JSON string, not a file. The
            # dialogue MCP client is a runtime component, NOT a Bash subprocess, so this sandbox
            # does not confine it (probe-confirmed: the agent still reaches the localhost server).
            settings = claude_native_sandbox_settings(workspace=workspace)
            argv += ["--settings", json.dumps(settings)]
        if dialogue:
            # Only the localhost dialogue server; --strict-mcp-config forbids any other MCP server.
            argv += ["--mcp-config", str(mcp_config_json), "--strict-mcp-config"]
        argv += ["--add-dir", str(workspace)]
        if self.dataset_root is not None and not self._external_readonly:
            # add_dir (toy fixture) only: external_readonly names the dataset in the prompt and
            # never grants tool access to it, so the non-sandboxed Write tool cannot target it.
            argv += ["--add-dir", str(self.dataset_root.resolve())]
        return argv

    def _append_system_prompt(self, workspace: Path, *, dialogue: bool = False) -> str:
        if not self._external_readonly:
            base = _WORKSPACE_ONLY_REINFORCEMENT
            return f"{base}\n\n{_CLAUDE_DIALOGUE_REINFORCEMENT}" if dialogue else base
        parts = [
            _CLAUDE_EXTERNAL_READONLY_REINFORCEMENT,
            "\n\n# Shared direct-file artifact contract\n\n",
            DIRECT_FILE_ARTIFACT_CONTRACT,
            "\n\n# Read-only external dataset\n\n",
            f"Read-only external dataset root: `{self.dataset_root.resolve()}`.\n"  # type: ignore[union-attr]
            "This path is NOT passed to Claude as `--add-dir`; the only tool-writable directory is "
            "the planner workspace. Treat the dataset as strictly read-only; the OS sandbox denies "
            "writes to it. Use it only for bounded documentation, schema, metadata, and small-sample "
            "inspection.\n",
        ]
        inspection = self._inspection_runtime_text()
        if inspection:
            parts.append("\n# Inspection runtime\n\n")
            parts.append(inspection)
        parts.append(f"\nPlanner workspace: `{workspace}`.\n")
        if dialogue:
            parts.append("\n")
            parts.append(_CLAUDE_DIALOGUE_REINFORCEMENT)
            parts.append("\n")
        return "".join(parts)

    def _coarse_append_system_prompt(self, workspace: Path) -> str:
        """GF-2a coarse Source-B system prompt (external_readonly only; no planner artifact contract)."""
        parts = [
            _CLAUDE_COARSE_EXTERNAL_READONLY_REINFORCEMENT,
            "\n\n# Read-only external dataset sample\n\n",
            f"Read-only external dataset root: `{self.dataset_root.resolve()}`.\n"  # type: ignore[union-attr]
            "This path is NOT passed to Claude as `--add-dir`; the only tool-writable directory is "
            "the workspace. Treat the dataset as strictly read-only; the OS sandbox denies writes to "
            "it. Use it only for bounded, coarse documentation, shape, and small-sample inspection.\n",
        ]
        inspection = self._inspection_runtime_text()
        if inspection:
            parts.append("\n# Inspection runtime\n\n")
            parts.append(inspection)
        parts.append(f"\nWorkspace: `{workspace}`.\n")
        return "".join(parts)

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
        helpers plus the shared safety primitives (``build_config_home`` / ``snapshot_config_home`` /
        ``assert_config_home_untouched`` / ``source_tree_digest`` / ``_spawn`` / ``_parse_result``);
        ``run()`` is untouched. Fails closed on source-tree mutation, a lead-config-home write, a
        failed spawn, or a missing coarse artifact — the same invariants ``run()`` enforces.
        """
        if not self._external_readonly:
            raise ValueError("coarse explore requires dataset_access_mode=external_readonly")
        workspace = Path(workspace)
        expected_artifact = Path(expected_artifact)
        repo_root = self.source_tree_root or _detect_repo_root()

        # Layer A config-home isolation + lead-home breach snapshot (same primitives as run()).
        config_env, _config_home = build_config_home(workspace)
        subprocess_env = self._subprocess_env(config_env)
        lead_home = self.lead_config_home or default_lead_config_home()
        lead_home_before = snapshot_config_home(lead_home, include_globs=BREACH_WATCH_GLOBS)

        # external_readonly always runs from a repo-external launch dir (no project CLAUDE.md).
        launch_dir = self._make_launch_dir()
        try:
            argv = self.build_command(task_text=task_text, workspace=workspace, coarse=True)
            before = source_tree_digest(repo_root)
            spawn = self._spawn(argv, cwd=launch_dir, env=subprocess_env)
            after = source_tree_digest(repo_root)
            lead_home_after = snapshot_config_home(lead_home, include_globs=BREACH_WATCH_GLOBS)
        finally:
            shutil.rmtree(launch_dir, ignore_errors=True)

        # Safety-critical asserts, identical to run(): repo byte-identical, lead config home untouched.
        if after != before:
            raise ValueError(
                "source_tree_mutation_detected: the Maieusis source tree changed during the coarse "
                f"claude -p explore (before={before[:12]} after={after[:12]}); discarding run"
            )
        assert_config_home_untouched(lead_home_before, lead_home_after, root=lead_home)

        result_json = self._parse_result(spawn)
        usage = _claude_usage(result_json)
        if not expected_artifact.exists():
            raise ValueError(
                f"claude -p coarse explore produced no coarse facts artifact at {expected_artifact}"
            )

        transcript = self._coarse_transcript(
            run_label=run_label,
            argv=argv,
            result_json=result_json,
            spawn=spawn,
            before=before,
            after=after,
        )
        transcript_path = workspace / "coarse_transcript.md"
        transcript_path.write_text(transcript, encoding="utf-8")

        display = self._inspection_runtime_display()
        return CoarseExploreRunResult(
            artifact_path=str(expected_artifact),
            transcript_path=str(transcript_path),
            explorer_adapter=CLAUDE_CODE_EXPLORER_ADAPTER,
            explorer_identity=self._planner_identity(result_json),
            inspection_runtime=display[1] if display else "",
            source_tree_before_digest=before,
            source_tree_after_digest=after,
            blocked_actions_checked=self._coarse_blocked_actions_checked(),
            usage=usage,
        )

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
        del owner_session  # the owner provider is carried inside dialogue_server
        workspace = Path(workspace).resolve()
        repo_root = self.source_tree_root or _detect_repo_root()
        task_text = ""

        # 2c-sandbox Layer A: isolate the spawn's config/memory/session writes to a throwaway home
        # so it cannot touch the lead ~/.claude. Relocating CLAUDE_CONFIG_DIR breaks the default
        # Keychain subscription auth, so a subscription OAuth token (CLAUDE_CODE_OAUTH_TOKEN, from
        # `claude setup-token`) must be present — it authenticates independently of the config dir
        # and keeps this subscription-billed (no API key). The token is whitespace-stripped so a
        # copy/paste line-wrap doesn't produce an invalid auth header.
        config_env, config_home = build_config_home(workspace)
        subprocess_env = self._subprocess_env(config_env)
        lead_home = self.lead_config_home or default_lead_config_home()
        lead_home_before = snapshot_config_home(lead_home, include_globs=BREACH_WATCH_GLOBS)

        # Resource creation, packet parsing, and digest setup all live inside the same cleanup
        # boundary. In particular LocalDialogueMcpServer binds a socket in its constructor.
        launch_dir: Path | None = None
        cwd = workspace
        dialogue: LocalDialogueMcpServer | None = None
        dialogue_active = dialogue_server is not None
        packet: DatasetPlannerTaskPacket | None = None
        argv: list[str] = []
        runner_warnings: list[str] = []
        result_payloads: list[Mapping[str, Any]] = []
        attempt_audits: list[_ClaudeAttemptAudit] = []
        attempt_count = 0
        before = ""
        after = before
        started_at = datetime.now(UTC)
        ended_at = started_at
        deadline = time.monotonic() + self.timeout_seconds
        spawn = _SpawnResult(stdout="", stderr="", returncode=1)
        result_json: Mapping[str, Any] = {}
        terminal_baseline: dict[str, str] = {}
        workspace_manifest_before: dict[str, str] = {}
        workspace_manifest_after: dict[str, str] = {}
        handoff_file_baseline: dict[str, str] = {}
        remaining_turns = self.max_turns
        try:
            packet = load_model(handoff.packet_path, DatasetPlannerTaskPacket)
            task_text = Path(handoff.task_path).read_text(encoding="utf-8")
            if planner_packet_digest(packet) != handoff.packet_digest:
                raise ValueError("planner handoff packet digest does not match its manifest")
            if stable_hash({"task": task_text}) != handoff.task_digest:
                raise ValueError("planner task digest does not match its manifest")
            handoff_file_baseline = _handoff_file_digest_map(handoff, workspace=workspace)
            before = source_tree_digest(repo_root)
            after = before
            terminal_baseline = _terminal_digest_map(packet, workspace=workspace)
            workspace_manifest_before = _artifact_digest_map(packet, workspace=workspace)

            # external_readonly runs from a repo-external launch dir so cwd's parents never
            # include the Maieusis repo (no project CLAUDE.md inheritance).
            if self._external_readonly:
                launch_dir = self._make_launch_dir()
                cwd = launch_dir

            # Dialogue mode self-hosts one MCP server for the WHOLE bounded invocation. A retry
            # therefore preserves the same owner session, branch event store, and round budget.
            if dialogue_server is not None:
                dialogue = LocalDialogueMcpServer(dialogue_server)
            mcp_config_json: str | None = None
            dialogue_tool_names: Sequence[str] = ()
            if dialogue is not None:
                dialogue.start()
                mcp_config_json = dialogue.mcp_config_json
                dialogue_tool_names = dialogue.allowed_tool_names
            for attempt_count in range(1, _MAX_TRANSIENT_ATTEMPTS + 1):
                attempt_task = (
                    task_text if attempt_count == 1 else task_text + _TRANSIENT_RETRY_TASK_NOTE
                )
                if remaining_turns <= 0:
                    raise ValueError(
                        "claude -p exhausted the configured whole-invocation turn budget before "
                        "a bounded retry could start"
                    )
                remaining_timeout = deadline - time.monotonic()
                if remaining_timeout <= 0:
                    raise ValueError(
                        "claude -p exhausted the configured whole-invocation wall-clock timeout "
                        "before a bounded retry could start"
                    )
                attempt_artifacts_before = _artifact_digest_map(packet, workspace=workspace)
                attempt_terminals_before = _terminal_digest_map(packet, workspace=workspace)
                argv = self.build_command(
                    task_text=attempt_task,
                    workspace=workspace,
                    mcp_config_json=mcp_config_json,
                    dialogue_tool_names=dialogue_tool_names,
                    max_turns_override=remaining_turns,
                )
                if self.os_process_sandbox and not self._external_readonly:
                    # Bash-less add_dir path may still opt into the outer Seatbelt (writes-only).
                    argv = wrap_argv_in_os_sandbox(
                        argv, workspace=workspace, config_home=config_home
                    )
                spawn = self._spawn(
                    argv,
                    cwd=cwd,
                    env=subprocess_env,
                    timeout_seconds=remaining_timeout,
                )
                after = source_tree_digest(repo_root)
                lead_home_after = snapshot_config_home(lead_home, include_globs=BREACH_WATCH_GLOBS)

                # Safety boundaries are checked after EVERY attempt.  A transient provider
                # response never permits a source/config-home mutation to be retried away.
                if after != before:
                    raise ValueError(
                        "source_tree_mutation_detected: the Maieusis source tree changed during "
                        f"claude -p attempt {attempt_count} (before={before[:12]} "
                        f"after={after[:12]}); discarding run"
                    )
                assert_config_home_untouched(lead_home_before, lead_home_after, root=lead_home)
                if _handoff_file_digest_map(handoff, workspace=workspace) != handoff_file_baseline:
                    raise ValueError(
                        "handoff_context_mutation_detected: handoff_packet.yaml or task.md changed "
                        f"during claude -p attempt {attempt_count}; discarding run"
                    )

                result_json = self._parse_result_payload(spawn)
                result_payloads.append(result_json)
                failure = self._result_failure(result_json, spawn)
                reported_turns = _optional_nonnegative_int(result_json.get("num_turns"))
                if reported_turns is not None:
                    if reported_turns > remaining_turns:
                        raise ValueError(
                            "claude -p reported num_turns above the host-provided attempt cap"
                        )
                    remaining_turns -= reported_turns
                attempt_artifacts_after = _artifact_digest_map(packet, workspace=workspace)
                attempt_terminals_after = _terminal_digest_map(packet, workspace=workspace)
                attempt_audits.append(
                    _ClaudeAttemptAudit(
                        attempt_index=attempt_count,
                        command_digest=stable_hash({"argv": argv}),
                        returncode=spawn.returncode,
                        result_subtype=str(result_json.get("subtype", "")),
                        is_error=bool(result_json.get("is_error", False)),
                        session_id=str(result_json.get("session_id", "")),
                        num_turns=reported_turns,
                        duration_ms=_optional_nonnegative_int(result_json.get("duration_ms")),
                        transient_marker=failure.transient_marker if failure else None,
                        artifact_manifest_before_digest=stable_hash(attempt_artifacts_before),
                        artifact_manifest_after_digest=stable_hash(attempt_artifacts_after),
                        changed_terminal_files=_changed_files(
                            attempt_terminals_before, attempt_terminals_after
                        ),
                    )
                )
                if failure is None:
                    break
                if failure.transient_marker and reported_turns is None:
                    raise ValueError(
                        failure.message
                        + "; transient retry refused because num_turns was absent and the global "
                        "turn budget could not be enforced"
                    )
                can_retry = (
                    failure.transient_marker
                    and attempt_count < _MAX_TRANSIENT_ATTEMPTS
                    and remaining_turns > 0
                )
                if can_retry:
                    runner_warnings.append(
                        "bounded Claude Code transient retry: "
                        f"attempt {attempt_count} ended with {failure.transient_marker}; "
                        "branch-local files and owner-dialogue state were preserved; the second "
                        "spawn shares the original wall-clock and turn budgets"
                    )
                    if self.transient_retry_backoff_seconds:
                        if time.monotonic() + self.transient_retry_backoff_seconds >= deadline:
                            raise ValueError(
                                failure.message
                                + "; transient retry refused because its bounded backoff would "
                                "exceed the whole-invocation timeout"
                            )
                        time.sleep(self.transient_retry_backoff_seconds)
                    continue

                # After the single bounded retry, a repeated explicit transport failure may
                # still have left a complete artifact surface.  Return it only as a strict-
                # Collect candidate: RealPlannerHost will restamp and validate every schema,
                # evidence scope, firewall, and terminal invariant before accepting it.
                found_after_failure = discover_output_artifacts(packet)
                current_terminals = _terminal_digest_map(packet, workspace=workspace)
                fresh_terminals = _changed_files(terminal_baseline, current_terminals)
                if (
                    failure.transient_marker
                    and found_after_failure.evidence_paths
                    and len(fresh_terminals) == 1
                ):
                    runner_warnings.append(
                        "Claude Code transport remained transient after the bounded retry "
                        f"({failure.transient_marker}); complete filesystem artifacts were "
                        "retained only as a strict host-Collect candidate"
                    )
                    break
                if failure.provider_marker:
                    raise CodingAgentProviderUnavailable(
                        failure.message + f"; explicit provider marker={failure.provider_marker}"
                    )
                raise ValueError(failure.message)
            ended_at = datetime.now(UTC)
        finally:
            try:
                if dialogue is not None:
                    dialogue.stop()
            finally:
                if launch_dir is not None:
                    shutil.rmtree(launch_dir, ignore_errors=True)

        if packet is None:  # pragma: no cover - load failures raise before this point
            raise ValueError("planner task packet was not loaded")

        usage = _aggregate_claude_usage(result_payloads)

        # A valid product must include evidence and exactly one root terminal created or changed
        # during THIS invocation. Old files from a prior revise round cannot masquerade as a new
        # response. Shared Collect separately enforces exactly one schema-valid terminal overall.
        found = discover_output_artifacts(packet)
        if not found.evidence_paths:
            raise ValueError(
                "claude -p spawn produced no inspection evidence in the planner workspace"
            )
        final_terminals = _terminal_digest_map(packet, workspace=workspace)
        fresh_terminals = _changed_files(terminal_baseline, final_terminals)
        if len(fresh_terminals) != 1:
            raise ValueError(
                "claude -p spawn must create or change exactly one root terminal artifact in this "
                f"invocation; observed {len(fresh_terminals)} fresh terminals: "
                f"{list(fresh_terminals)}"
            )
        workspace_manifest_after = _artifact_digest_map(packet, workspace=workspace)

        transcript = self._transcript(
            run_id=run_id,
            branch=branch,
            argv=argv,
            result_json=result_json,
            spawn=spawn,
            dialogue_active=dialogue_active,
            attempt_count=attempt_count,
            runner_warnings=runner_warnings,
            attempt_audits=attempt_audits,
        )
        transcript_path = workspace / "transcript.md"
        transcript_path.write_text(transcript, encoding="utf-8")

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
            blocked_actions_checked=self._blocked_actions_checked(dialogue_active=dialogue_active),
            started_at=started_at,
            ended_at=ended_at,
            usage=usage,
            attempt_count=attempt_count,
            runner_warnings=runner_warnings,
            workspace_manifest_before_digest=stable_hash(workspace_manifest_before),
            workspace_manifest_after_digest=stable_hash(workspace_manifest_after),
        )

    def _spawn(
        self,
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: float | None = None,
    ) -> _SpawnResult:
        try:
            proc = subprocess.Popen(
                argv,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                start_new_session=True,  # own process group so os.killpg reaps the whole tree
            )
        except FileNotFoundError as exc:
            raise ValueError(
                f"claude executable not found: {argv[0]!r}. Install the Claude Code CLI or "
                "pass executable=... (the live_agent spawn requires a logged-in CLI)."
            ) from exc

        try:
            effective_timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds
            stdout, stderr = proc.communicate(timeout=effective_timeout)
        except subprocess.TimeoutExpired as exc:
            _kill_process_group(proc)
            with contextlib.suppress(subprocess.TimeoutExpired):
                proc.communicate(timeout=10)  # reap the killed group
            raise ValueError(
                f"claude -p spawn exceeded its remaining {effective_timeout:.3f}s "
                "whole-invocation timeout; process group killed "
                "(fail-closed, no bundle)"
            ) from exc

        return _SpawnResult(stdout=stdout or "", stderr=stderr or "", returncode=proc.returncode)

    def _subprocess_env(self, config_env: Mapping[str, str]) -> dict[str, str]:
        env = dict(os.environ)
        for key in list(env):
            if key in _PAID_OR_SECRET_ENV_EXACT or key.startswith(_PAID_OR_SECRET_ENV_PREFIXES):
                env.pop(key, None)
        env.update(self._inspection_env())
        env.update(config_env)
        token = env.get("CLAUDE_CODE_OAUTH_TOKEN")
        if token:
            env["CLAUDE_CODE_OAUTH_TOKEN"] = "".join(token.split())
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
        if env and display is not None:
            rendered_env = " ".join(f"{key}={value}" for key, value in sorted(env.items()))
            parts.append(
                "Use this prefix for bounded Python checks when helpful: "
                f"`{rendered_env} {display[1]}`."
            )
        if not parts:
            return ""
        return "\n".join(parts) + "\n"

    def _validate_inspection_extra_env(self) -> None:
        for key in self.inspection_extra_env:
            if key in _PAID_OR_SECRET_ENV_EXACT or key.startswith(_PAID_OR_SECRET_ENV_PREFIXES):
                raise ValueError("inspection_extra_env must not contain paid/API auth variables")

    def _make_launch_dir(self) -> Path:
        parent = self.launch_parent.resolve() if self.launch_parent is not None else None
        if parent is not None:
            parent.mkdir(parents=True, exist_ok=True)
        return Path(
            tempfile.mkdtemp(prefix=_LAUNCH_DIR_PREFIX, dir=str(parent) if parent else None)
        )

    def _blocked_actions_checked(self, *, dialogue_active: bool = False) -> list[str]:
        checks: list[str] = []
        if dialogue_active:
            # Owner dialogue rides an in-process localhost MCP server; the owner
            # API call is host-side, so the spawn env stays paid/API-key-stripped and the agent
            # reaches only localhost. MCP carries dialogue + read context/state, not evidence/plan.
            checks += [
                "owner dialogue via in-process localhost MCP server "
                f"({DIALOGUE_MCP_SERVER_NAME}, --strict-mcp-config)",
                "question owner API call is host-side; agent env paid/API-key stripped",
                "MCP scope limited to owner dialogue and read context/state",
                "evidence and terminal plan/rejection remain file artifacts (direct-file contract)",
            ]
        if not self._external_readonly:
            return checks
        return [
            *checks,
            "external dataset read access authorized for bounded planning inspection",
            "external dataset root not added as writable Claude --add-dir",
            f"bash network policy: {CLAUDE_NATIVE_SANDBOX_BASH_NETWORK_POLICY}",
            "claude native strict Bash sandbox (settings) enforced",
            "source tree unchanged",
            "lead config home untouched",
            "no downstream bridge artifact",
            "no execution artifact",
            "branch planner workspace writes only",
        ]

    def _coarse_blocked_actions_checked(self) -> list[str]:
        return [
            "coarse proposal-stage exploration (no branch, owner, or terminal plan)",
            "external dataset read access authorized for bounded coarse inspection",
            "external dataset root not added as writable Claude --add-dir",
            f"bash network policy: {CLAUDE_NATIVE_SANDBOX_BASH_NETWORK_POLICY}",
            "claude native strict Bash sandbox (settings) enforced",
            "source tree unchanged",
            "lead config home untouched",
            "no downstream bridge artifact",
            "no execution artifact",
            "workspace writes only",
        ]

    def _coarse_transcript(
        self,
        *,
        run_label: str,
        argv: list[str],
        result_json: Mapping[str, Any],
        spawn: _SpawnResult,
        before: str,
        after: str,
    ) -> str:
        display = self._inspection_runtime_display()
        external_dataset_root = str(self.dataset_root.resolve()) if self.dataset_root else ""
        return (
            "# Claude Code Coarse Local-Sample Exploration\n\n"
            f"run_label: {run_label}\n"
            f"runner: {self.runner_name}\n"
            f"model: {self.model}\n"
            f"dataset_access_mode: {self.dataset_access_mode}\n"
            f"external_dataset_root: {external_dataset_root}\n"
            "dataset_added_as_writable_dir: False\n"
            "sandbox_mode: claude_native_strict_settings\n"
            f"bash_network_policy: {CLAUDE_NATIVE_SANDBOX_BASH_NETWORK_POLICY}\n"
            f"inspection_command: {self.inspection_command or ''}\n"
            f"inspection_runtime: {display[1] if display else ''}\n"
            f"command_digest: {stable_hash({'argv': argv})}\n"
            f"returncode: {spawn.returncode}\n"
            f"result_subtype: {result_json.get('subtype', '')}\n"
            f"num_turns: {result_json.get('num_turns', '')}\n"
            f"total_cost_usd: {result_json.get('total_cost_usd', '')}\n"
            f"session_id: {result_json.get('session_id', '')}\n"
            f"source_tree_before_digest: {before}\n"
            f"source_tree_after_digest: {after}\n\n"
            "This is a coarse, proposal-safe local-sample exploration. No execution, no downstream "
            "bridge artifact, no branch/owner dialogue. Source tree verified unchanged.\n\n"
            "## stderr (tail)\n\n"
            "```\n"
            f"{_tail(spawn.stderr, 4000)}\n"
            "```\n"
        )

    def _parse_result_payload(self, spawn: _SpawnResult) -> Mapping[str, Any]:
        """Parse the CLI envelope without weakening its success-status decision."""

        stdout = spawn.stdout.strip()
        if not stdout:
            raise ValueError(
                f"claude -p returned empty stdout (fail-closed); returncode={spawn.returncode}, "
                f"stderr={_tail(spawn.stderr, 500)!r}"
            )
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"claude -p did not return valid JSON on stdout (fail-closed): {exc}"
            ) from exc
        if not isinstance(data, Mapping):
            raise ValueError("claude -p JSON result was not an object (fail-closed)")
        return data

    def _result_failure(
        self, data: Mapping[str, Any], spawn: _SpawnResult
    ) -> _ClaudeResultFailure | None:
        """Classify a non-success result; only explicit transport/provider markers are transient."""

        subtype = str(data.get("subtype", ""))
        is_error = bool(data.get("is_error", False))
        if spawn.returncode == 0 and subtype == "success" and not is_error:
            return None
        # Provider classification reads only the current structured result envelope.  A nonzero
        # process remains non-retryable/non-salvageable, but an explicit provider marker still
        # earns the typed provider-unavailable terminal rather than being mislabeled as validation.
        provider_messages = [
            str(data[key])
            for key in ("error", "message", "result")
            if key in data and isinstance(data[key], (str, int, float))
        ]
        searchable = "\n".join(provider_messages).lower()
        provider_marker = (
            next(
                (label for marker, label in _TRANSIENT_RESULT_MARKERS if marker in searchable),
                None,
            )
            if is_error and subtype == "success"
            else None
        )
        # Process and protocol failures are never retried.  The one retry is reserved for an
        # otherwise well-formed success envelope that explicitly reports an interruption.
        if spawn.returncode != 0 or subtype != "success" or not is_error:
            return _ClaudeResultFailure(
                message=(
                    "claude -p run did not succeed (fail-closed): "
                    f"returncode={spawn.returncode} subtype={subtype!r} is_error={is_error}"
                ),
                transient_marker=None,
                provider_marker=provider_marker,
            )
        transient_marker = next(
            (label for marker, label in _TRANSIENT_RESULT_MARKERS if marker in searchable), None
        )
        return _ClaudeResultFailure(
            message=(
                "claude -p run did not succeed (fail-closed): "
                f"returncode={spawn.returncode} subtype={subtype!r} is_error={is_error}"
            ),
            transient_marker=transient_marker,
            provider_marker=provider_marker,
        )

    def _parse_result(self, spawn: _SpawnResult) -> Mapping[str, Any]:
        """Strict single-attempt parser used by coarse exploration and legacy direct tests."""

        data = self._parse_result_payload(spawn)
        if failure := self._result_failure(data, spawn):
            if failure.provider_marker:
                raise CodingAgentProviderUnavailable(
                    failure.message + f"; explicit provider marker={failure.provider_marker}"
                )
            raise ValueError(failure.message)
        return data

    def _planner_identity(self, result_json: Mapping[str, Any]) -> str:
        session_id = str(result_json.get("session_id", "")).strip()
        base = f"claude-code:{self.model}"
        return f"{base}:{session_id}" if session_id else base

    def _bounded_planner_identity(self, result_payloads: Sequence[Mapping[str, Any]]) -> str:
        if len(result_payloads) <= 1:
            return self._planner_identity(result_payloads[-1] if result_payloads else {})
        session_ids = [
            str(payload.get("session_id", "")).strip()
            for payload in result_payloads
            if str(payload.get("session_id", "")).strip()
        ]
        digest = stable_hash(
            {
                "model": self.model,
                "attempt_count": len(result_payloads),
                "session_ids": session_ids,
            }
        )
        return f"claude-code:{self.model}:bounded-attempts:{digest[:12]}"

    def _transcript(
        self,
        *,
        run_id: str,
        branch: QuestionFamilyBranch,
        argv: list[str],
        result_json: Mapping[str, Any],
        spawn: _SpawnResult,
        dialogue_active: bool = False,
        attempt_count: int = 1,
        runner_warnings: Sequence[str] = (),
        attempt_audits: Sequence[_ClaudeAttemptAudit] = (),
    ) -> str:
        external_dataset_root = (
            str(self.dataset_root.resolve())
            if self._external_readonly and self.dataset_root is not None
            else ""
        )
        bash_network_policy = (
            CLAUDE_NATIVE_SANDBOX_BASH_NETWORK_POLICY if self._external_readonly else ""
        )
        sandbox_mode = (
            "claude_native_strict_settings"
            if self._external_readonly
            else ("outer_seatbelt" if self.os_process_sandbox else "flags_only")
        )
        inspection_python = (
            str(self.inspection_python.resolve()) if self.inspection_python is not None else ""
        )
        inspection_command = self.inspection_command or ""
        # The argv contains the full task prompt; hash it rather than dump it.
        return (
            "# Claude Code Dataset Planner Spawn\n\n"
            f"run_id: {run_id}\n"
            f"branch_id: {branch.branch_id}\n"
            f"runner: {self.runner_name}\n"
            f"executable: {self.executable}\n"
            f"model: {self.model}\n"
            f"max_turns: {self.max_turns}\n"
            f"timeout_seconds: {self.timeout_seconds}\n"
            f"permission_mode: {self.permission_mode}\n"
            f"allowed_tools: {', '.join(self.allowed_tools)}\n"
            f"disallowed_tools: {', '.join(self.disallowed_tools)}\n"
            f"dataset_access_mode: {self.dataset_access_mode}\n"
            f"external_dataset_root: {external_dataset_root}\n"
            f"dataset_added_as_writable_dir: {self.dataset_root is not None and not self._external_readonly}\n"
            f"sandbox_mode: {sandbox_mode}\n"
            f"bash_network_policy: {bash_network_policy}\n"
            f"inspection_python: {inspection_python}\n"
            f"inspection_command: {inspection_command}\n"
            f"inspection_pythonpath_configured: {self.inspection_pythonpath is not None}\n"
            f"owner_dialogue_mcp: {DIALOGUE_MCP_SERVER_NAME if dialogue_active else ''}\n"
            f"owner_dialogue_active: {dialogue_active}\n"
            f"spawn_attempts: {attempt_count}\n"
            f"runner_warnings: {json.dumps(list(runner_warnings))}\n"
            "attempt_audits: "
            f"{json.dumps([audit._asdict() for audit in attempt_audits], sort_keys=True)}\n"
            f"command_digest: {stable_hash({'argv': argv})}\n"
            f"returncode: {spawn.returncode}\n"
            f"result_subtype: {result_json.get('subtype', '')}\n"
            f"num_turns: {result_json.get('num_turns', '')}\n"
            f"duration_ms: {result_json.get('duration_ms', '')}\n"
            f"total_cost_usd: {result_json.get('total_cost_usd', '')}\n"
            f"session_id: {result_json.get('session_id', '')}\n\n"
            + (
                "This is a planning-only headless spawn with MCP owner dialogue "
                "(owner API host-side; agent reached localhost only). No execution, no downstream "
                "bridge artifact. Source tree verified unchanged.\n\n"
                if dialogue_active
                else "This is a planning-only headless spawn. No execution, no downstream bridge "
                "artifact. Source tree verified unchanged.\n\n"
            )
            + "## stderr (tail)\n\n"
            + "```\n"
            + f"{_tail(spawn.stderr, 4000)}\n"
            + "```\n"
        )
