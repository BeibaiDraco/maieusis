"""Reusable OS-level confinement for a spawned coding-agent process (the "2c-sandbox").

The first real 2c-1 spawn leaked *outside* its workspace: because the spawn inherited the
project ``CLAUDE.md`` (with the memory-system instructions), the planner wrote a memory file
and edited ``MEMORY.md`` under the lead session's ``~/.claude/.../memory/``. The repo-only
source-tree digest can't see ``~/.claude``, and ``--add-dir`` / ``dontAsk`` did not stop it —
Claude Code's built-in ``--sandbox`` only confines *Bash* subprocesses, not the Write tool or
the memory path. This module is the containment layer that fixes that, reusable by every real
runner (the 2c-1 Claude runner now; Codex / the real-dataset runner later).

Two layers:

- **Layer A — config-home isolation (primary, low-risk, keychain-safe).** Point
  ``CLAUDE_CONFIG_DIR`` at a throwaway directory under the branch workspace, so every
  config / memory / session / history write lands there instead of the lead ``~/.claude``.
  Subscription auth is unaffected because the credentials live in the macOS **Keychain**,
  independent of the config dir — so this needs no ``--bare`` and no API key. A before/after
  snapshot of the **entire** lead config home is the containment assertion: any change → fail
  closed, discard the bundle.
- **Layer B — outer OS process sandbox (defense-in-depth; mandatory once Bash returns).**
  Wrap the whole ``claude`` argv in an OS sandbox that allows everything *except* writes
  outside the workspace / config-home / temp dir. macOS uses ``sandbox-exec`` (Seatbelt); the
  Linux (bubblewrap) backend is a documented stub until the real-dataset phase.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

CONFIG_HOME_DIRNAME = ".sandbox-claude-home"
CODEX_AUTH_FILENAME = "auth.json"
CODEX_HOME_PREFIX = "maieusis-codex-home-"

# A single lead-config-home snapshot maps each file to (mtime_ns, size).
ConfigHomeSnapshot = dict[str, tuple[int, int]]

# The exact signature of the original breach: the leaked planner wrote a memory file and
# edited MEMORY.md under ``~/.claude/projects/<hash>/memory/``. We watch ONLY files under a
# ``memory/`` directory. Everything else in ``~/.claude`` churns on its own during a normal
# session — ``backups/`` (periodic ``.claude.json`` backups), and crucially the per-session
# ``projects/<hash>/*.jsonl`` transcripts that EVERY concurrent Claude Code session on this
# machine writes — so watching wider than ``memory/`` false-trips on unrelated activity. The
# planner cannot write to the real memory dir anyway (Layer A redirects its config home); this
# is the backstop that catches a redirect failure without depending on the machine being idle.
BREACH_WATCH_GLOBS: tuple[str, ...] = ("projects/**/memory/**",)

# Codex stores normal runtime churn in sqlite/log/cache files under ``~/.codex``. The
# containment backstop is intentionally narrow and watches only memory-shaped paths, matching
# the original breach class without false-tripping on concurrent desktop sessions.
CODEX_BREACH_WATCH_GLOBS: tuple[str, ...] = ("**/memory/**",)


@dataclass(frozen=True)
class CodexHomeStaging:
    """Temporary Codex home used only to seed ChatGPT subscription auth."""

    env: dict[str, str]
    home: Path
    auth_path: Path


def build_config_home(workspace: str | Path) -> tuple[dict[str, str], Path]:
    """Layer A: a throwaway ``CLAUDE_CONFIG_DIR`` under the workspace + the env overlay.

    Returns ``(env_overlay, config_home_path)``. The overlay is merged into the subprocess
    env so the spawned agent's config / memory / session writes are isolated from the lead
    ``~/.claude``. Keychain-based subscription auth is unaffected.
    """
    # Resolve to an ABSOLUTE path: the spawn's cwd is the workspace, and ``claude`` re-resolves
    # a relative CLAUDE_CONFIG_DIR against cwd, which would nest the throwaway home inside the
    # workspace. An absolute path lands it exactly where the runner expects.
    config_home = (Path(workspace) / CONFIG_HOME_DIRNAME).resolve()
    config_home.mkdir(parents=True, exist_ok=True)
    return {"CLAUDE_CONFIG_DIR": str(config_home)}, config_home


def default_lead_codex_home() -> Path:
    """The lead session's real Codex home (what the spawn must NOT touch)."""
    override = os.environ.get("CODEX_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".codex"


def stage_codex_home(
    *,
    lead_home: str | Path | None = None,
    parent: str | Path | None = None,
) -> CodexHomeStaging:
    """Create a short-lived ``CODEX_HOME`` containing only copied ChatGPT auth.

    Codex ChatGPT subscription auth is file-backed in ``auth.json``. A nested
    ``codex exec`` needs that file to start, but generated shell commands must not be
    able to read it for the whole run. The runner deletes ``auth_path`` immediately
    after the JSONL ``thread.started`` event and removes ``home`` at process end.
    """
    source_home = (
        Path(lead_home).expanduser() if lead_home is not None else default_lead_codex_home()
    )
    source_auth = source_home / CODEX_AUTH_FILENAME
    if not source_auth.exists():
        raise ValueError(
            f"Codex ChatGPT auth file not found at {source_auth}; run `codex login` "
            "with ChatGPT auth before a live Codex planner spawn"
        )
    parent_dir = Path(parent).resolve() if parent is not None else Path(tempfile.gettempdir())
    parent_dir.mkdir(parents=True, exist_ok=True)
    home = Path(tempfile.mkdtemp(prefix=CODEX_HOME_PREFIX, dir=str(parent_dir))).resolve()
    home.chmod(0o700)
    auth_path = home / CODEX_AUTH_FILENAME
    shutil.copy2(source_auth, auth_path)
    auth_path.chmod(0o600)
    return CodexHomeStaging(env={"CODEX_HOME": str(home)}, home=home, auth_path=auth_path)


def delete_staged_codex_auth(auth_path: str | Path) -> bool:
    """Delete staged Codex auth; return true once the file is absent."""
    path = Path(auth_path)
    try:
        path.unlink()
    except FileNotFoundError:
        return True
    return not path.exists()


def cleanup_codex_home(home: str | Path) -> None:
    """Remove the short-lived Codex home, including sqlite/log/cache churn."""
    shutil.rmtree(home, ignore_errors=True)


def default_lead_config_home() -> Path:
    """The lead session's real config home (what the spawn must NOT touch)."""
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude"


def snapshot_config_home(
    root: str | Path, *, include_globs: Sequence[str] | None = None
) -> ConfigHomeSnapshot:
    """Snapshot files under ``root`` as ``{relpath: (mtime_ns, size)}``.

    ``include_globs`` (e.g. ``BREACH_WATCH_GLOBS``) restricts the snapshot to files matching
    those glob patterns (relative to ``root``, ``**`` allowed), so the containment check tracks
    only the breach signature and does not false-trip on unrelated churn (backups, per-session
    transcripts). ``None`` snapshots the whole tree. Missing paths -> skipped. Unreadable
    entries are skipped (best-effort).
    """
    root = Path(root)
    snapshot: ConfigHomeSnapshot = {}
    if not root.exists():
        return snapshot
    if include_globs is None:
        candidates: Iterable[Path] = root.rglob("*")
    else:
        # A glob ending in ``**`` (e.g. ``projects/**/memory/**``) matches only DIRECTORIES on
        # Python <= 3.12; a trailing ``**`` only began matching files in 3.13. Relying on that
        # trailing-``**`` file match silently drops the memory-home files we watch for on the
        # supported 3.11/3.12 (the exact breach a memory write would be), so the containment
        # check passes locally on 3.13 but misses the breach on CI. Expand every matched
        # directory into its files instead, so the snapshot is identical on all supported
        # Pythons regardless of the glob's trailing form.
        matched: set[Path] = set()
        for glob in include_globs:
            for path in root.glob(glob):
                if path.is_dir() and not path.is_symlink():
                    matched.update(path.rglob("*"))
                else:
                    matched.add(path)
        candidates = matched
    for path in candidates:
        try:
            if path.is_dir() and not path.is_symlink():
                continue
            stat = path.lstat()
            snapshot[str(path.relative_to(root))] = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            continue
    return snapshot


def assert_config_home_untouched(
    before: ConfigHomeSnapshot,
    after: ConfigHomeSnapshot,
    *,
    root: str | Path,
) -> None:
    """Fail closed if the lead config home changed at all during the spawn.

    The whole-tree comparison is deliberately strict (commander requirement): a spawn that
    is properly isolated by Layer A must not add, remove, or modify any file under the lead
    ``~/.claude``. Run the gated spawn with the lead desktop session quiescent.
    """
    if before == after:
        return
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(key for key in (set(before) & set(after)) if before[key] != after[key])
    raise ValueError(
        f"lead config home {root} was modified during the spawn (containment breach): "
        f"added={added[:8]} removed={removed[:8]} changed={changed[:8]}"
    )


def session_tmpdir() -> str:
    """The temp dir the spawn may write to (also allowed by the Seatbelt profile)."""
    return tempfile.gettempdir()


def _seatbelt_escape(path: str) -> str:
    return path.replace("\\", "\\\\").replace('"', '\\"')


def macos_seatbelt_profile(
    *,
    workspace: str | Path,
    config_home: str | Path,
    tmpdir: str | Path,
    deny_network: bool = False,
) -> str:
    """Layer B (macOS): allow everything EXCEPT writes outside the sandboxed directories.

    The confirmed breach was a *write* outside the workspace, so the profile denies all
    writes and re-allows only the workspace, the throwaway config home, and the temp dir.
    Reads / network / mach-lookup (Keychain auth, the Anthropic API call) stay allowed, which
    is why this is far more likely to keep ``claude`` working than a ``(deny default)`` base.

    ``deny_network`` is reserved for the real-dataset phase (when Bash returns and egress must
    be constrained); it denies outbound network wholesale here and is intended to be paired
    with an allowlisting proxy in that phase, not used for the toy-fixture 2c-1 run.
    """
    write_subpaths = [
        str(Path(workspace).resolve()),
        str(Path(config_home).resolve()),
        str(Path(tmpdir).resolve()),
    ]
    lines = [
        "(version 1)",
        "(allow default)",
        "(deny file-write*)",
    ]
    for subpath in write_subpaths:
        lines.append(f'(allow file-write* (subpath "{_seatbelt_escape(subpath)}"))')
    # /dev/null and friends must stay writable for a normal process.
    lines.append('(allow file-write-data (regex #"^/dev/"))')
    if deny_network:
        lines.append("(deny network-outbound)")
    return "\n".join(lines) + "\n"


def claude_native_sandbox_settings(
    *,
    workspace: str | Path,
    extra_allow_write: Sequence[str | Path] = (),
) -> dict[str, object]:
    """Strict Claude-native Bash-sandbox settings for a real-dataset (Bash) planner spawn.

    Returned as a ``--settings`` JSON payload for ``claude -p``. This is the ONLY correct way to
    confine a Bash-enabled Claude spawn: Claude Code's built-in sandbox is itself a Seatbelt
    (``sandbox-exec``) sandbox applied per Bash command, so it CANNOT be nested inside an outer
    ``wrap_argv_in_os_sandbox`` Seatbelt (that fails at the first command; see that function's note).
    The env var ``CLAUDE_CODE_FORCE_SANDBOX`` is deliberately NOT used: it turns the sandbox on but
    leaves the ``dangerouslyDisableSandbox`` escape hatch open, so a blocked command can be retried
    unsandboxed. This block is the strict, no-escape-hatch form (empirically verified to confine
    bash: dataset-write denied, network denied, workspace-write allowed, dataset-read allowed):

    - ``sandbox.enabled`` — OS-level (Seatbelt/bubblewrap) confinement of every Bash command;
    - ``sandbox.allowUnsandboxedCommands: false`` — the ``dangerouslyDisableSandbox`` retry is
      ignored, so a command that fails under the sandbox stays failed (no unconfined fallback);
    - ``sandbox.network.allowedDomains: []`` — Bash subprocesses get NO network (Claude's own model
      API is unaffected: the sandbox scopes to Bash, not the ``claude`` process);
    - ``sandbox.filesystem.allowWrite: [workspace, ...]`` — Bash may write only the planner
      workspace (plus any explicit extras) and the session temp dir; everything else, crucially the
      read-only external dataset, is not writable.

    Note the residual: Claude's Read/Edit/Write TOOLS bypass this sandbox (they use the permission
    system), so the dataset-read-only guarantee for the Write tool rests on not adding the dataset to
    ``--add-dir`` plus the config-home isolation + breach assertion (Layer A), not on this block.
    """
    ws = str(Path(workspace).resolve())
    allow_write = [ws, *(str(Path(path).resolve()) for path in extra_allow_write)]
    return {
        "sandbox": {
            "enabled": True,
            "allowUnsandboxedCommands": False,
            "network": {"allowedDomains": []},
            "filesystem": {"allowWrite": allow_write},
        }
    }


def wrap_argv_in_os_sandbox(
    argv: list[str],
    *,
    workspace: str | Path,
    config_home: str | Path,
    tmpdir: str | None = None,
    deny_network: bool = False,
) -> list[str]:
    """Layer B: wrap ``argv`` so writes are confined to the sandboxed directories.

    macOS -> ``sandbox-exec -p <profile> <argv>``. Other platforms raise until the real-dataset
    (bubblewrap) backend lands, so a caller never silently runs unconfined.

    **Do NOT use this to wrap a Bash-enabled Claude spawn.** Claude Code's own Bash sandbox is a
    nested ``sandbox-exec`` invocation; macOS Seatbelt cannot be nested, so a Claude spawn wrapped
    here fails at the first Bash command (``mkdir .../session-env -> EPERM``, empirically confirmed).
    For a real-dataset Claude planner, confine Bash with ``claude_native_sandbox_settings`` instead.
    This wrapper remains valid for a Bash-LESS spawn (e.g. the 2c-1 toy-fixture Claude runner, whose
    only tools are Read/Grep/Glob/Write).
    """
    tmp = tmpdir or session_tmpdir()
    if sys.platform == "darwin":
        profile = macos_seatbelt_profile(
            workspace=workspace,
            config_home=config_home,
            tmpdir=tmp,
            deny_network=deny_network,
        )
        return ["/usr/bin/sandbox-exec", "-p", profile, *argv]
    raise NotImplementedError(
        "the OS process sandbox (Layer B) has only a macOS Seatbelt backend so far; "
        "the Linux bubblewrap / @anthropic-ai/sandbox-runtime backend lands with the "
        "real-dataset planner phase"
    )
