"""Smoke tests for the thin product CLI (Phase 5d-A, DEC-B locked command surface)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from research_agenda_engine import product_cli
from research_agenda_engine.config import runtime_env_paths

LOCKED_PUBLIC_COMMANDS = {"init", "check", "run", "resume", "status"}


def test_product_cli_registers_exactly_the_locked_commands() -> None:
    registered = {command.name for command in product_cli.app.registered_commands}
    assert registered == LOCKED_PUBLIC_COMMANDS


def test_product_cli_never_imports_the_legacy_dev_cli() -> None:
    """The thin CLI must not pull the giant legacy cli.py (nor the legacy schema layer)."""
    code = (
        "import sys\n"
        "import research_agenda_engine.product_cli\n"
        "forbidden = [\n"
        "    'research_agenda_engine.cli',\n"
        "    'research_agenda_engine.mcp_server',\n"
        "    'research_agenda_engine.schemas.question',\n"
        "    'research_agenda_engine.schemas.ideation',\n"
        "    'research_agenda_engine.services.pipeline',\n"
        "]\n"
        "loaded = [name for name in forbidden if name in sys.modules]\n"
        "assert not loaded, f'legacy modules loaded at import time: {loaded}'\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_credentials_resolve_from_the_users_project_not_the_packaged_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A runtime env file next to the user's config must actually be read.

    `_asset_root` and `_user_project_root` used to be one function. Runtime-env discovery asked it
    for "the project root" and got the packaged asset root, so from an installed wheel the CLI
    looked for credentials inside site-packages and never saw the file sitting beside the user's
    own `maieusis.yaml`. The shipped example told users all three local filenames worked. Only the
    user-level file and exported environment variables did, and nothing reported the difference.
    """

    project = tmp_path / "my-project"
    project.mkdir()
    (project / "runtime.env").write_text(
        "MAIEUSIS_PROBE_TOKEN=from-the-project\n", encoding="utf-8"
    )
    monkeypatch.chdir(project)

    resolved = product_cli._user_project_root()
    assert resolved == project.resolve()
    assert resolved != product_cli._asset_root()

    candidates = runtime_env_paths(project_root=resolved, home=tmp_path / "home")
    assert project / "runtime.env" in candidates
    assert not any(product_cli._asset_root() in candidate.parents for candidate in candidates)
