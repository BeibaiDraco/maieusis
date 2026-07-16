"""Agent runners for the dataset-planning coding agent.

An ``AgentRunner`` is the *launch* half of a real planner host: it is responsible
for driving a coding agent to produce branch-local scientific artifacts (typed
inspection evidence + one terminal plan / rejection / escalation message + a
transcript) under the branch planner workspace, and for reporting what it wrote
as an ``AgentRunResult``. The *collect* half — read those workspace artifacts,
validate them, and assemble a ``PlannerReturnedArtifactBundle`` — lives in the
host (``real_planner_host.py``) and is shared across every runner, so any runner
plugs into the same host.

``SyntheticAgentRunner`` is the deterministic, in-process runner used by tests and
development runs: it composes the artifacts from the shared bundle builders with
no subprocess, no real agent, and no API call. It may perform a *bounded* read of
a committed toy dataset fixture (``schema.yaml``) so its evidence is grounded in
that fixture's real table names, but its evidence stays a synthetic probe and is
never real scientific grounding.

``ManualAgentRunner`` is the "B" runner: it does not launch anything.
An external coding agent (Codex / Claude Code) or a human runs the planning task
out-of-band and leaves typed artifacts under the branch planner workspace at the
packet's declared output paths; this runner *collects* those artifacts and reports
them as an ``AgentRunResult`` so the host's shared Collect step can validate and
assemble the bundle. It spawns no subprocess and calls no API. Auto-spawn
subprocess runners (Codex / Claude Code) use the reserved
``owner_session`` / ``dialogue_server`` collaborators; the Synthetic and Manual
runners ignore them.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal, NamedTuple, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...io import dump_data, load_data, load_model
from ...provenance import stable_hash
from ...schemas.planner_run import CodingAgentRunStatus, CodingAgentRunUsage
from ...schemas.planning_dialogue import (
    BranchRejectionMessage,
    HumanEscalationRequest,
    PlanDraftMessage,
)
from ...schemas.question_family_branch import QuestionFamilyBranch
from ...services.planning.dataset_planner_packet import (
    DatasetPlannerHandoffManifest,
    DatasetPlannerTaskPacket,
)
from ...services.planning.planner_bundle_builders import (
    family_evidence,
    human_escalation,
    plan_draft,
    rejection,
)

if TYPE_CHECKING:  # reserved collaborators; the Synthetic runner ignores them
    from ...mcp import ScientificDialogueServer
    from ..scientific_agents import ScientificAgentProvider

SyntheticAgentOutcome = Literal["plan", "rejection", "human_escalation"]

MANUAL_AGENT_RUNNER_NAME = "manual-agent-runner"
SYNTHETIC_AGENT_RUNNER_NAME = "synthetic-agent-runner"
_SYNTHETIC_AGENT_PROVIDER_ID = "synthetic:agent-runner"
_SYNTHETIC_AGENT_MODEL_ID = "synthetic-agent-runner"
_SYNTHETIC_AGENT_EVIDENCE_LIMITATIONS = (
    "synthetic agent runner only",
    "development planning rehearsal",
    "not live dataset evidence",
)


class AgentRunResult(BaseModel):
    """What a runner produced in the branch planner workspace.

    The path lists are the artifacts the runner wrote; the host's Collect step
    validates them and assembles the returned bundle. Identity + transcript fields
    let the host stamp an honest ``CodingAgentRunRecord``.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    branch_id: str
    runner_name: str
    planner_identity: str
    status: CodingAgentRunStatus = CodingAgentRunStatus.RETURNED
    transcript_path: str
    transcript_digest: str
    evidence_paths: list[str] = Field(default_factory=list)
    dialogue_paths: list[str] = Field(default_factory=list)
    plan_draft_paths: list[str] = Field(default_factory=list)
    rejection_paths: list[str] = Field(default_factory=list)
    construct_probe_map_paths: list[str] = Field(default_factory=list)
    # Real subprocess runners witness the spawn, so they compute the
    # Maieusis-repo source-tree digest before/after and report it here; the host threads
    # it into the run trace. In-process runners (Synthetic / Manual) leave these empty
    # and the host falls back to its "unchanged" placeholder.
    source_tree_before_digest: str = ""
    source_tree_after_digest: str = ""
    source_tree_mutation_detected: bool = False
    blocked_actions_checked: list[str] = Field(default_factory=list)
    # Real subprocess runners witness the spawn, so they report the actual wall-clock
    # start/end and captured token/USD usage; the host threads these into the run trace. In-process
    # runners (Synthetic / Manual) leave them unset and the run_record placeholder is used.
    started_at: datetime | None = None
    ended_at: datetime | None = None
    usage: CodingAgentRunUsage | None = None
    # Exact coding-host runtime identity and host-owned budget policy.  These remain optional for
    # synthetic/manual and historical runners, while release-grade subprocess runners populate
    # them so a downstream sealer need not infer the actual launch from prose or config alone.
    planner_model_id: str = ""
    planner_reasoning_effort: str = ""
    planner_cli_version: str = ""
    planner_budget_policy: str = ""
    planner_timeout_seconds: int | None = Field(default=None, ge=1)
    # Bounded transport recovery is runner-owned.  Keep the decisions typed so Collect can
    # preserve them in the returned bundle instead of leaving retry/salvage truth only in logs.
    attempt_count: int = Field(default=1, ge=1)
    attempt_audit_digest: str = ""
    runner_warnings: list[str] = Field(default_factory=list)
    workspace_manifest_before_digest: str = ""
    workspace_manifest_after_digest: str = ""

    @field_validator(
        "workspace_manifest_before_digest",
        "workspace_manifest_after_digest",
        "attempt_audit_digest",
    )
    @classmethod
    def validate_optional_workspace_digest(cls, value: str) -> str:
        if value and (len(value) != 64 or any(char not in "0123456789abcdef" for char in value)):
            raise ValueError("AgentRunResult workspace manifest digests must be sha256 hex")
        return value

    @field_validator(
        "run_id",
        "branch_id",
        "runner_name",
        "planner_identity",
        "transcript_path",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("AgentRunResult identity fields must be non-empty")
        return value

    @field_validator(
        "planner_model_id",
        "planner_reasoning_effort",
        "planner_cli_version",
        "planner_budget_policy",
    )
    @classmethod
    def strip_optional_runtime_identity(cls, value: str) -> str:
        return value.strip()


class DiscoveredOutputArtifacts(NamedTuple):
    """Typed planner artifacts found under a packet's declared output paths."""

    evidence_paths: list[str]
    dialogue_paths: list[str]
    plan_draft_paths: list[str]
    rejection_paths: list[str]


def _yaml_files(directory: Path) -> list[str]:
    if not directory.exists():
        return []
    return sorted(str(path) for path in directory.glob("*.yaml"))


def discover_output_artifacts(packet: DatasetPlannerTaskPacket) -> DiscoveredOutputArtifacts:
    """Discover the typed artifacts a run left at the packet's declared output paths.

    Shared by every collect-side runner (``ManualAgentRunner`` and the
    subprocess runners): an external / spawned agent writes evidence, dialogue, and one
    terminal plan/rejection artifact under the branch planner workspace; this reads back
    what is present. It classifies nothing — ``validate_returned_artifacts`` remains the
    authority on artifact validity and outcome shape.
    """
    paths = packet.output_paths
    plan_draft_path = Path(paths.plan_draft_path)
    rejection_path = Path(paths.rejection_path)
    dialogue_paths = _yaml_files(Path(paths.dialogue_dir))
    # A human_escalation is a terminal message like plan_draft/rejection, and those are canonical
    # workspace-root files (plan_draft.yaml / rejection.yaml), so an agent intuitively writes the
    # escalation as a sibling `escalation.yaml` at the workspace root rather than under dialogue/.
    # Discover it there too (as a terminal dialogue message) so a valid escalation is not lost.
    escalation_path = plan_draft_path.parent / "escalation.yaml"
    if escalation_path.exists() and str(escalation_path) not in dialogue_paths:
        dialogue_paths = [*dialogue_paths, str(escalation_path)]
    return DiscoveredOutputArtifacts(
        evidence_paths=_yaml_files(Path(paths.evidence_dir)),
        dialogue_paths=dialogue_paths,
        plan_draft_paths=[str(plan_draft_path)] if plan_draft_path.exists() else [],
        rejection_paths=[str(rejection_path)] if rejection_path.exists() else [],
    )


@runtime_checkable
class AgentRunner(Protocol):
    """Launch half of a real planner host: produce branch-local planner artifacts."""

    runner_name: str

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
        """Drive the agent to write artifacts under ``workspace`` and report them.

        ``owner_session`` and ``dialogue_server`` are reserved for real
        runners (owner clarification + typed dialogue); a runner may ignore them.
        """
        ...


class SyntheticAgentRunner:
    """Deterministic, in-process runner: composes artifacts, no subprocess/API."""

    runner_name = SYNTHETIC_AGENT_RUNNER_NAME

    def __init__(
        self,
        *,
        outcome: SyntheticAgentOutcome = "plan",
        dataset_root: str | Path | None = None,
    ) -> None:
        if outcome not in ("plan", "rejection", "human_escalation"):
            raise ValueError(f"unsupported synthetic agent outcome: {outcome}")
        self.outcome: SyntheticAgentOutcome = outcome
        self.dataset_root = Path(dataset_root) if dataset_root is not None else None
        # Bounded revise-loop re-spawn support (mirrors FakePlannerHost): distinct ids per call so a
        # re-plan round does not collide with the prior round's evidence id. Call 0 stays historical.
        self._call_count = 0

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
        del handoff, owner_session, dialogue_server  # reserved for real runners
        workspace = Path(workspace)

        finding, source_locator = self._inspect(branch)
        evidence = family_evidence(
            branch,
            evidence_id=self._id(branch, "evidence"),
            finding=finding,
            source_locator=source_locator,
            inspection_method="synthetic agent runner bounded fixture inspection",
            created_by="synthetic_dataset_planner",
            limitations=list(_SYNTHETIC_AGENT_EVIDENCE_LIMITATIONS),
        )
        evidence_path = workspace / "evidence" / f"{evidence.evidence_id}.yaml"
        dump_data(evidence, evidence_path)

        dialogue_paths: list[Path] = []
        plan_draft_paths: list[Path] = []
        rejection_paths: list[Path] = []
        message: PlanDraftMessage | BranchRejectionMessage | HumanEscalationRequest
        if self.outcome == "plan":
            message = plan_draft(
                branch,
                message_id=self._id(branch, "plan"),
                analysis_plan_id=self._id(branch, "analysis-plan"),
                evidence_id=evidence.evidence_id,
                summary=(
                    "Synthetic agent runner plan draft with evidence-backed per-variant outcomes."
                ),
                provider_id=_SYNTHETIC_AGENT_PROVIDER_ID,
                model_id=_SYNTHETIC_AGENT_MODEL_ID,
                session_id=self._id(branch, "session"),
            )
            message_path = workspace / "plan_draft.yaml"
            plan_draft_paths.append(message_path)
        elif self.outcome == "rejection":
            message = rejection(
                branch,
                message_id=self._id(branch, "rejection"),
                evidence_id=evidence.evidence_id,
                provider_id=_SYNTHETIC_AGENT_PROVIDER_ID,
                model_id=_SYNTHETIC_AGENT_MODEL_ID,
                session_id=self._id(branch, "session"),
            )
            message_path = workspace / "rejection.yaml"
            rejection_paths.append(message_path)
        else:
            message = human_escalation(
                branch,
                message_id=self._id(branch, "human-escalation"),
                evidence_id=evidence.evidence_id,
                provider_id=_SYNTHETIC_AGENT_PROVIDER_ID,
                model_id=_SYNTHETIC_AGENT_MODEL_ID,
                session_id=self._id(branch, "session"),
            )
            message_path = workspace / "dialogue" / f"{message.message_id}.yaml"
            dialogue_paths.append(message_path)
        dump_data(message.model_dump(mode="json"), message_path)

        transcript = self._transcript(branch, run_id=run_id, evidence_id=evidence.evidence_id)
        transcript_path = workspace / "transcript.md"
        transcript_path.write_text(transcript, encoding="utf-8")

        result = AgentRunResult(
            run_id=run_id,
            branch_id=branch.branch_id,
            runner_name=self.runner_name,
            planner_identity=_SYNTHETIC_AGENT_MODEL_ID,
            status=CodingAgentRunStatus.RETURNED,
            transcript_path=str(transcript_path),
            transcript_digest=stable_hash({"transcript": transcript}),
            evidence_paths=[str(evidence_path)],
            dialogue_paths=[str(path) for path in dialogue_paths],
            plan_draft_paths=[str(path) for path in plan_draft_paths],
            rejection_paths=[str(path) for path in rejection_paths],
        )
        self._call_count += 1
        return result

    def _inspect(self, branch: QuestionFamilyBranch) -> tuple[str, str]:
        """Optionally read the committed toy dataset schema to ground the evidence.

        Table names are read from the fixture at runtime, so this stays dataset
        agnostic: no dataset-specific name is hardcoded in this module.
        """
        if self.dataset_root is not None:
            schema_path = self.dataset_root / "schema.yaml"
            if schema_path.exists():
                schema = load_data(schema_path)
                dataset_id = str(schema.get("dataset_id", "synthetic-dataset"))
                tables = [
                    str(table["name"])
                    for table in schema.get("tables", [])
                    if isinstance(table, dict) and table.get("name")
                ]
                table_list = ", ".join(tables) if tables else "no tables"
                finding = (
                    "Synthetic agent runner performed a bounded inspection of the toy dataset "
                    f"'{dataset_id}' and observed tables: {table_list}. This is a synthetic "
                    "development probe over a committed toy fixture, not live scientific "
                    "dataset inspection."
                )
                return finding, f"synthetic-dataset://{dataset_id}/schema.yaml"

        finding = (
            "Synthetic agent runner produced deterministic development evidence covering the "
            f"family's active variants for the '{self.outcome}' outcome. This is a synthetic "
            "planning probe, not live dataset inspection."
        )
        return finding, f"synthetic-agent-runner://{branch.branch_id}/{self.outcome}"

    def _id(self, branch: QuestionFamilyBranch, label: str) -> str:
        payload: dict[str, object] = {
            "branch_id": branch.branch_id,
            "outcome": self.outcome,
            "label": label,
            "runner": self.runner_name,
        }
        if self._call_count:
            payload["revise_round"] = self._call_count
        digest = stable_hash(payload)
        suffix = f"-r{self._call_count}" if self._call_count else ""
        return f"synthetic-agent-{self.outcome}-{label}{suffix}-{digest[:12]}"

    def _transcript(self, branch: QuestionFamilyBranch, *, run_id: str, evidence_id: str) -> str:
        return (
            "# Synthetic Agent Runner\n\n"
            f"run_id: {run_id}\n"
            f"branch_id: {branch.branch_id}\n"
            f"outcome: {self.outcome}\n"
            f"evidence_id: {evidence_id}\n\n"
            "Deterministic development-only rehearsal produced through the Runner + Collect "
            "split. No subprocess, live dataset access, paid API call, scientific execution, "
            "or downstream bridge artifact.\n"
        )


class ManualAgentRunner:
    """Collect externally-produced planner artifacts already in the workspace.

    The "B" runner: an external coding agent (Codex / Claude Code) or a
    human ran the planning task out-of-band and left typed artifacts under the
    branch planner workspace at the packet's declared output paths. This runner
    discovers those artifacts and reports them as an ``AgentRunResult``; the host's
    shared Collect step then validates and assembles the bundle. It launches
    nothing, spawns no subprocess, and calls no API.

    It fails closed if the workspace is missing the minimum an external run must
    leave behind: at least one inspection-evidence file, one terminal artifact,
    and a transcript. The terminal check (a plan draft, a rejection, or at least
    one dialogue message for an escalation) is a completeness backstop, not a
    strict outcome classifier — a clarification-only dialogue also satisfies it.
    The host's ``validate_returned_artifacts`` remains the authority on artifact
    validity and outcome shape.
    """

    runner_name = MANUAL_AGENT_RUNNER_NAME

    def __init__(
        self,
        *,
        planner_identity: str,
        transcript_name: str = "transcript.md",
    ) -> None:
        planner_identity = planner_identity.strip()
        if not planner_identity:
            raise ValueError("ManualAgentRunner requires a non-empty planner_identity")
        self.planner_identity = planner_identity
        self.transcript_name = transcript_name

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
        del owner_session, dialogue_server  # the external / manual run already happened
        workspace = Path(workspace)

        packet = load_model(handoff.packet_path, DatasetPlannerTaskPacket)
        found = discover_output_artifacts(packet)
        evidence_paths = found.evidence_paths
        dialogue_paths = found.dialogue_paths
        plan_draft_paths = found.plan_draft_paths
        rejection_paths = found.rejection_paths

        if not evidence_paths:
            raise ValueError(
                "ManualAgentRunner found no inspection evidence in the planner workspace"
            )
        if not (plan_draft_paths or rejection_paths or dialogue_paths):
            raise ValueError(
                "ManualAgentRunner found no terminal plan / rejection / escalation artifact"
            )

        transcript_path = workspace / self.transcript_name
        if not transcript_path.exists():
            raise ValueError(
                f"ManualAgentRunner requires an external transcript at {transcript_path}"
            )
        transcript = transcript_path.read_text(encoding="utf-8")

        return AgentRunResult(
            run_id=run_id,
            branch_id=branch.branch_id,
            runner_name=self.runner_name,
            planner_identity=self.planner_identity,
            status=CodingAgentRunStatus.RETURNED,
            transcript_path=str(transcript_path),
            transcript_digest=stable_hash({"transcript": transcript}),
            evidence_paths=evidence_paths,
            dialogue_paths=dialogue_paths,
            plan_draft_paths=plan_draft_paths,
            rejection_paths=rejection_paths,
        )
