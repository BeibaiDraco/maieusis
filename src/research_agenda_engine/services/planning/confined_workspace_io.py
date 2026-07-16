"""Trusted atomic writes into an untrusted planner workspace.

Coding-agent planners may create arbitrary filesystem entries inside their branch
workspace.  Host-owned artifacts therefore cannot use ordinary ``Path.write_*``
or ``dump_data`` calls after a planner has run: an agent-planted symlink or
non-directory component must be a hard integrity failure, never a write primitive.
"""

from __future__ import annotations

import contextlib
import os
import stat
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml
from pydantic import BaseModel

from .planner_failures import HardFamilyIntegrityViolation


def assert_confined_write_target(
    *,
    workspace: str | Path,
    path: str | Path,
) -> Path:
    """Validate one existing-or-new regular-file target under ``workspace``.

    The workspace and target parents must already exist.  Symlinks, lexical
    aliases (including ``..``), non-directory parent components, and an existing
    non-regular target are rejected before any host-owned bytes are created.
    """

    root, target, relative = _resolve_confined_target(workspace=workspace, path=path)
    parent_fd = _open_confined_parent(root, relative.parts[:-1])
    try:
        _assert_regular_or_missing(parent_fd, relative.name, target=target)
    finally:
        os.close(parent_fd)
    return target


def atomic_write_confined_text(
    text: str,
    *,
    workspace: str | Path,
    path: str | Path,
) -> Path:
    """Atomically write UTF-8 text without following planner-created aliases."""

    return atomic_write_confined_bytes(
        text.encode("utf-8"),
        workspace=workspace,
        path=path,
    )


def atomic_write_confined_model(
    value: BaseModel,
    *,
    workspace: str | Path,
    path: str | Path,
) -> Path:
    """Strictly render and atomically write one host-owned YAML model."""

    payload = yaml.safe_dump(
        value.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        allow_unicode=True,
    ).encode("utf-8")
    type(value).model_validate(yaml.safe_load(payload))
    return atomic_write_confined_bytes(payload, workspace=workspace, path=path)


def atomic_write_confined_yaml_data(
    value: Any,
    *,
    workspace: str | Path,
    path: str | Path,
) -> Path:
    """Atomically write arbitrary host-normalized YAML without following aliases."""

    payload = yaml.safe_dump(value, sort_keys=False, allow_unicode=True).encode("utf-8")
    return atomic_write_confined_bytes(payload, workspace=workspace, path=path)


def atomic_write_confined_bytes(
    payload: bytes,
    *,
    workspace: str | Path,
    path: str | Path,
) -> Path:
    """Atomically replace a confined regular file using no-follow directory FDs."""

    root, target, relative = _resolve_confined_target(workspace=workspace, path=path)
    parent_fd = _open_confined_parent(root, relative.parts[:-1])
    temporary_name = f".{relative.name}.{uuid4().hex}.tmp"
    temporary_created = False
    file_fd: int | None = None
    try:
        _assert_regular_or_missing(parent_fd, relative.name, target=target)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | _required_flag("O_NOFOLLOW")
        flags |= getattr(os, "O_CLOEXEC", 0)
        file_fd = os.open(temporary_name, flags, 0o600, dir_fd=parent_fd)
        temporary_created = True
        remaining = memoryview(payload)
        while remaining:
            written = os.write(file_fd, remaining)
            if written <= 0:
                raise OSError("confined workspace write made no forward progress")
            remaining = remaining[written:]
        os.fsync(file_fd)
        os.close(file_fd)
        file_fd = None

        # Recheck the destination immediately before replacement.  ``os.replace``
        # itself never follows the destination entry, but policy requires an
        # agent-created symlink/non-regular node to be reported, not silently removed.
        _assert_regular_or_missing(parent_fd, relative.name, target=target)
        os.replace(
            temporary_name,
            relative.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        temporary_created = False
    except HardFamilyIntegrityViolation:
        raise
    except OSError as exc:
        raise HardFamilyIntegrityViolation(
            f"trusted planner-workspace write failed closed for {target}"
        ) from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if temporary_created:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary_name, dir_fd=parent_fd)
        os.close(parent_fd)
    return target


def _resolve_confined_target(
    *,
    workspace: str | Path,
    path: str | Path,
) -> tuple[Path, Path, Path]:
    workspace_input = Path(workspace)
    target_input = Path(path)
    lexical_root = Path(os.path.abspath(workspace_input))
    lexical_target = Path(os.path.abspath(target_input))

    try:
        resolved_root = workspace_input.resolve(strict=True)
    except OSError as exc:
        raise HardFamilyIntegrityViolation(
            "trusted planner-workspace write requires an existing workspace"
        ) from exc
    if resolved_root != lexical_root or workspace_input.is_symlink():
        raise HardFamilyIntegrityViolation(
            "trusted planner-workspace write root is non-canonical or symlink-aliased"
        )
    try:
        root_stat = lexical_root.lstat()
    except OSError as exc:
        raise HardFamilyIntegrityViolation(
            "trusted planner-workspace write root is unreadable"
        ) from exc
    if not stat.S_ISDIR(root_stat.st_mode):
        raise HardFamilyIntegrityViolation(
            "trusted planner-workspace write root is not a directory"
        )

    # A normalized spelling is required even when the target does not yet exist.
    # Resolution also exposes any symlink in an existing target component.
    if Path(os.path.normpath(str(target_input))) != target_input:
        raise HardFamilyIntegrityViolation(
            f"trusted planner-workspace target is non-canonical: {target_input}"
        )
    if target_input.resolve(strict=False) != lexical_target:
        raise HardFamilyIntegrityViolation(
            f"trusted planner-workspace target is non-canonical or symlink-aliased: {target_input}"
        )
    try:
        relative = lexical_target.relative_to(lexical_root)
    except ValueError as exc:
        raise HardFamilyIntegrityViolation(
            f"trusted planner-workspace target escaped its branch workspace: {target_input}"
        ) from exc
    if not relative.parts:
        raise HardFamilyIntegrityViolation(
            "trusted planner-workspace target cannot be the workspace directory"
        )
    return lexical_root, lexical_target, relative


def _open_confined_parent(root: Path, components: tuple[str, ...]) -> int:
    directory_flags = os.O_RDONLY | _required_flag("O_DIRECTORY") | _required_flag("O_NOFOLLOW")
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    try:
        current_fd = os.open(root, directory_flags)
    except OSError as exc:
        raise HardFamilyIntegrityViolation(
            "trusted planner-workspace root could not be opened without following aliases"
        ) from exc
    try:
        for component in components:
            try:
                next_fd = os.open(component, directory_flags, dir_fd=current_fd)
            except OSError as exc:
                raise HardFamilyIntegrityViolation(
                    "trusted planner-workspace target contains a symlink, missing, or "
                    f"non-directory component: {component}"
                ) from exc
            os.close(current_fd)
            current_fd = next_fd
        if not stat.S_ISDIR(os.fstat(current_fd).st_mode):
            raise HardFamilyIntegrityViolation(
                "trusted planner-workspace target parent is not a directory"
            )
        return current_fd
    except HardFamilyIntegrityViolation:
        with contextlib.suppress(OSError):
            os.close(current_fd)
        raise
    except OSError as exc:
        with contextlib.suppress(OSError):
            os.close(current_fd)
        raise HardFamilyIntegrityViolation(
            "trusted planner-workspace target parent could not be verified"
        ) from exc


def _assert_regular_or_missing(parent_fd: int, name: str, *, target: Path) -> None:
    try:
        target_stat = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise HardFamilyIntegrityViolation(
            f"trusted planner-workspace target is unreadable: {target}"
        ) from exc
    if not stat.S_ISREG(target_stat.st_mode) or target_stat.st_nlink != 1:
        raise HardFamilyIntegrityViolation(
            f"trusted planner-workspace target is symlinked, hard-linked, or non-regular: {target}"
        )


def _required_flag(name: str) -> int:
    value = getattr(os, name, None)
    if not isinstance(value, int):
        raise HardFamilyIntegrityViolation(
            f"trusted planner-workspace writes require operating-system {name} support"
        )
    return value
