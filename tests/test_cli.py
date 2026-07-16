"""Smoke tests for the thin product CLI (Phase 5d-A, DEC-B locked command surface)."""

from __future__ import annotations

import subprocess
import sys

from research_agenda_engine import product_cli

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
