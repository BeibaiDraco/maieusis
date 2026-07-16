from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path

_ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class RuntimeEnvLoadResult:
    candidate_files: list[Path] = field(default_factory=list)
    read_files: list[Path] = field(default_factory=list)
    loaded_keys: list[str] = field(default_factory=list)
    skipped_existing_keys: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def runtime_env_paths(
    *,
    project_root: Path | None = None,
    home: Path | None = None,
) -> list[Path]:
    """Return runtime env files in precedence order.

    Existing process environment variables still have the highest precedence.
    Project-local files are next, and the user-level file is a fallback.
    """

    paths: list[Path] = []
    if project_root is not None:
        root = project_root.expanduser()
        paths.extend([root / ".env.local", root / "runtime.env", root / ".env"])
    user_home = home.expanduser() if home is not None else Path.home()
    paths.append(user_home / ".config" / "maieusis" / "runtime.env")
    return paths


def load_runtime_env(
    *,
    project_root: Path | None = None,
    home: Path | None = None,
    override: bool = False,
) -> RuntimeEnvLoadResult:
    """Load local runtime environment files without evaluating shell code.

    Supported syntax is intentionally small: `KEY=value` or `export KEY=value`.
    Values may be quoted. Existing environment variables are not overwritten by
    default, so one-off command-line overrides remain authoritative.
    """

    candidate_files = runtime_env_paths(project_root=project_root, home=home)
    read_files: list[Path] = []
    loaded_keys: list[str] = []
    skipped_existing_keys: list[str] = []
    warnings: list[str] = []
    for path in candidate_files:
        expanded = path.expanduser()
        if not expanded.exists():
            continue
        read_files.append(expanded)
        assignments, parse_warnings = _parse_runtime_env_file(expanded)
        warnings.extend(parse_warnings)
        for key, value in assignments.items():
            if not override and key in os.environ:
                skipped_existing_keys.append(key)
                continue
            os.environ[key] = value
            loaded_keys.append(key)
    return RuntimeEnvLoadResult(
        candidate_files=candidate_files,
        read_files=read_files,
        loaded_keys=sorted(set(loaded_keys)),
        skipped_existing_keys=sorted(set(skipped_existing_keys)),
        warnings=warnings,
    )


def _parse_runtime_env_file(path: Path) -> tuple[dict[str, str], list[str]]:
    assignments: dict[str, str] = {}
    warnings: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return assignments, [f"{path}: could not read runtime env file: {error}"]
    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            tokens = shlex.split(stripped, comments=True, posix=True)
        except ValueError as error:
            warnings.append(f"{path}:{line_number}: could not parse line: {error}")
            continue
        if not tokens:
            continue
        if tokens[0] == "export":
            tokens = tokens[1:]
        if not tokens:
            warnings.append(f"{path}:{line_number}: export without assignment ignored")
            continue
        for token in tokens:
            if "=" not in token:
                warnings.append(f"{path}:{line_number}: token without assignment ignored")
                continue
            key, value = token.split("=", 1)
            if not _ENV_KEY_RE.fullmatch(key):
                warnings.append(f"{path}:{line_number}: invalid environment key ignored")
                continue
            assignments[key] = value
    return assignments, warnings
