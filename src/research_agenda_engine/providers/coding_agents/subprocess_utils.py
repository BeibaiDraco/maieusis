"""Shared subprocess safety helpers for real coding-agent runners."""

from __future__ import annotations

import os
import signal
import subprocess
from hashlib import sha256
from pathlib import Path

from ...provenance import stable_hash


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_tree_digest(repo_root: str | Path) -> str:
    """Digest the Maieusis repo working tree, including dirty-file bytes.

    Any edit/add to a tracked source file, any new untracked (non-ignored) file,
    or a new commit changes this. Gitignored planner workspace writes do not. The
    tracked diff and untracked contents are included because porcelain status alone
    cannot detect a second edit to a file that was already dirty before the spawn.
    """
    root = Path(repo_root)
    head = _git(["rev-parse", "HEAD"], root)
    status = _git(["status", "--porcelain=v1", "--untracked-files=all"], root)
    tracked_diff = _git(["diff", "--binary", "--no-ext-diff", "HEAD", "--"], root)
    raw_untracked = _git(["ls-files", "--others", "--exclude-standard", "-z"], root)
    untracked: list[dict[str, str]] = []
    for relative in sorted(item for item in raw_untracked.split("\0") if item):
        path = root / relative
        if path.is_symlink():
            content_digest = sha256(os.readlink(path).encode("utf-8")).hexdigest()
            kind = "symlink"
        elif path.is_file():
            content_digest = _file_sha256(path)
            kind = "file"
        else:
            content_digest = stable_hash({"non_regular": relative})
            kind = "non_regular"
        untracked.append({"path": relative, "kind": kind, "content_sha256": content_digest})
    return stable_hash(
        {
            "head": head.strip(),
            "status": status,
            "tracked_diff": tracked_diff,
            "untracked": untracked,
        }
    )


def _git(args: list[str], repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"git {' '.join(args)} failed in {repo_root}: {result.stderr.strip()}")
    return result.stdout


def detect_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            "could not detect the Maieusis repo root via git; pass source_tree_root explicitly"
        )
    return Path(result.stdout.strip())


def kill_process_group(proc: subprocess.Popen[str]) -> None:
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        proc.kill()


def tail(text: str, limit: int) -> str:
    text = text.strip()
    return text[-limit:] if len(text) > limit else text


def directory_digest(root: str | Path) -> str:
    """Digest a small directory snapshot by relative path and bytes."""
    base = Path(root)
    if not base.exists():
        return stable_hash({"missing_directory": str(base)})
    parts: list[dict[str, str]] = []
    for path in sorted(item for item in base.rglob("*") if item.is_file()):
        digest = sha256(path.read_bytes()).hexdigest()
        parts.append({"path": path.relative_to(base).as_posix(), "sha256": digest})
    return stable_hash({"directory": parts})
