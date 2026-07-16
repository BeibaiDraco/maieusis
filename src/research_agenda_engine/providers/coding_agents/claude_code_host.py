"""Claude Code-flavored planner host: a thin wrapper over ``RealPlannerHost``.

``ClaudeCodePlannerHost`` fixes the adapter identity
to ``"claude_code"`` and, by default, uses ``ManualAgentRunner`` (collect artifacts
an external Claude Code run or a human already left in the branch planner
workspace). All Collect (read → validate → assemble bundle) lives in
``RealPlannerHost`` and is shared with the Codex host, so both hosts return
identical typed bundles.

A real subprocess runner (``claude -p ... --output-format json``) is injected
through the same ``runner`` seam without changing this wrapper or the shared
Collect path.

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

CLAUDE_CODE_ADAPTER_NAME = "claude_code"
_DEFAULT_CLAUDE_CODE_MANUAL_IDENTITY = "claude-code-cli-manual"


class ClaudeCodePlannerHost:
    """Claude Code adapter over the shared ``RealPlannerHost`` (default: manual collect)."""

    adapter_name = CLAUDE_CODE_ADAPTER_NAME

    def __init__(
        self,
        *,
        root: str | Path,
        runner: AgentRunner | None = None,
        planner_identity: str = _DEFAULT_CLAUDE_CODE_MANUAL_IDENTITY,
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
