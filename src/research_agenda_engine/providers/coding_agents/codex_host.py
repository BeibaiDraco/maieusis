"""Codex-flavored planner host: a thin wrapper over the shared ``RealPlannerHost``.

``CodexPlannerHost`` fixes the adapter identity to
``"codex"`` and, by default, uses ``ManualAgentRunner`` (collect artifacts an
external Codex run or a human already left in the branch planner workspace). All
Collect (read → validate → assemble bundle) lives in ``RealPlannerHost`` and is
shared with the Claude Code host, so both hosts return identical typed bundles.

A real subprocess runner (``codex exec --json``) is injected through the same
``runner`` seam without changing this wrapper or the shared Collect path.

This module carries no dataset-specific names; it is enforced by the
dataset-agnostic guard.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ...schemas.planner_run import PlannerReturnedArtifactBundle
from ...schemas.question_family_branch import QuestionFamilyBranch
from ...services.planning.dataset_planner_packet import DatasetPlannerHandoffManifest
from .agent_runner import AgentRunner, ManualAgentRunner
from .real_planner_host import RealPlannerHost

if TYPE_CHECKING:  # reserved collaborators; forwarded to the runner
    from ...mcp import ScientificDialogueServer
    from ..scientific_agents import ScientificAgentProvider

CODEX_ADAPTER_NAME = "codex"
_DEFAULT_CODEX_MANUAL_IDENTITY = "codex-cli-manual"


class CodexPlannerHost:
    """Codex adapter over the shared ``RealPlannerHost`` (default: manual collect)."""

    adapter_name = CODEX_ADAPTER_NAME

    def __init__(
        self,
        *,
        root: str | Path,
        runner: AgentRunner | None = None,
        planner_identity: str = _DEFAULT_CODEX_MANUAL_IDENTITY,
    ) -> None:
        self._host = RealPlannerHost(
            runner=runner or ManualAgentRunner(planner_identity=planner_identity),
            root=root,
            adapter_name=self.adapter_name,
        )

    def run_planning(
        self,
        *,
        run_id: str,
        branch: QuestionFamilyBranch,
        handoff: DatasetPlannerHandoffManifest,
        owner_session: ScientificAgentProvider | None = None,
        dialogue_server: ScientificDialogueServer | None = None,
    ) -> PlannerReturnedArtifactBundle:
        return self._host.run_planning(
            run_id=run_id,
            branch=branch,
            handoff=handoff,
            owner_session=owner_session,
            dialogue_server=dialogue_server,
        )
