"""Host seam for the dataset-planning coding agent.

``CodingAgentPlannerHost`` is the interface the multi-family orchestrator calls to
run branch-local feasibility planning. A host receives a prepared handoff and
returns a ``PlannerReturnedArtifactBundle`` of typed evidence + a terminal
plan / rejection / escalation message; the orchestrator imports that bundle
through ``CodingAgentHandoffBackend``.

``FakePlannerHost`` is the test/development double: it produces a deterministic
bundle for any of the three outcomes with no API calls and no live dataset
access, so the generic pipeline can be exercised (including real rejections)
without a real coding-agent adapter. It must never represent real dataset
grounding: its evidence stays a synthetic probe and carries ``adapter_name="fake"``.

Real hosts (Codex / Claude Code) use the reserved
``owner_session`` / ``dialogue_server`` collaborators; the Fake ignores them.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from ...io import dump_data
from ...provenance import stable_hash
from ...schemas.planner_run import CodingAgentRunStatus, PlannerReturnedArtifactBundle
from ...schemas.planning_dialogue import (
    BranchRejectionMessage,
    HumanEscalationRequest,
    PlanDraftMessage,
)
from ...schemas.question_family_branch import QuestionFamilyBranch
from ...services.planning.dataset_planner_packet import DatasetPlannerHandoffManifest
from ...services.planning.planner_bundle_builders import (
    family_evidence,
    human_escalation,
    plan_draft,
    rejection,
    returned_bundle,
    run_record,
)

if TYPE_CHECKING:  # reserved collaborators; the Fake ignores them
    from ...mcp import ScientificDialogueServer
    from ..scientific_agents import ScientificAgentProvider

FakePlannerOutcome = Literal["plan", "rejection", "human_escalation"]

FAKE_PLANNER_ADAPTER_NAME = "fake"
_FAKE_PLANNER_PROVIDER_ID = "fake:planner-host"
_FAKE_PLANNER_MODEL_ID = "fake-planner-host"


@runtime_checkable
class CodingAgentPlannerHost(Protocol):
    """Runs one branch-local planning pass and returns a typed artifact bundle."""

    adapter_name: str

    def run_planning(
        self,
        *,
        run_id: str,
        branch: QuestionFamilyBranch,
        handoff: DatasetPlannerHandoffManifest,
        owner_session: ScientificAgentProvider | None = None,
        dialogue_server: ScientificDialogueServer | None = None,
    ) -> PlannerReturnedArtifactBundle:
        """Inspect the branch and emit a returned-artifact bundle.

        ``owner_session`` and ``dialogue_server`` are reserved for real
        adapters (owner clarification + typed dialogue); a host may ignore them.
        """
        ...


class FakePlannerHost:
    """Deterministic, API-free planner host for tests and development runs."""

    adapter_name = FAKE_PLANNER_ADAPTER_NAME

    def __init__(self, *, outcome: FakePlannerOutcome = "plan") -> None:
        if outcome not in ("plan", "rejection", "human_escalation"):
            raise ValueError(f"unsupported fake planner outcome: {outcome}")
        self.outcome: FakePlannerOutcome = outcome
        # Bounded revise-loop re-spawn support: the same host instance is re-invoked for each
        # revision round, so successive calls must emit DISTINCT ids (the branch rejects duplicate
        # evidence ids). Call 0 keeps the historical ids byte-identical; call>0 is round-salted.
        self._call_count = 0

    def run_planning(
        self,
        *,
        run_id: str,
        branch: QuestionFamilyBranch,
        handoff: DatasetPlannerHandoffManifest,
        owner_session: ScientificAgentProvider | None = None,
        dialogue_server: ScientificDialogueServer | None = None,
    ) -> PlannerReturnedArtifactBundle:
        del owner_session, dialogue_server  # reserved for real adapters
        workspace = Path(handoff.packet_path).parent
        evidence = family_evidence(
            branch,
            evidence_id=self._id(branch, "evidence"),
            finding=(
                "Fake planner host produced deterministic development evidence covering the "
                "family's active variants. This is a synthetic planning probe, not live "
                "dataset inspection."
            ),
            source_locator=f"fake-planner-host://{branch.branch_id}/{self.outcome}",
            inspection_method="fake planner host deterministic development rehearsal",
            created_by="fake_dataset_planner",
            limitations=[
                "fake planner host only",
                "development planning rehearsal",
                "not live dataset evidence",
            ],
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
                summary=("Fake planner host plan draft with evidence-backed per-variant outcomes."),
                provider_id=_FAKE_PLANNER_PROVIDER_ID,
                model_id=_FAKE_PLANNER_MODEL_ID,
                session_id=self._id(branch, "session"),
            )
            message_path = workspace / "plan_draft.yaml"
            plan_draft_paths.append(message_path)
        elif self.outcome == "rejection":
            message = rejection(
                branch,
                message_id=self._id(branch, "rejection"),
                evidence_id=evidence.evidence_id,
                provider_id=_FAKE_PLANNER_PROVIDER_ID,
                model_id=_FAKE_PLANNER_MODEL_ID,
                session_id=self._id(branch, "session"),
            )
            message_path = workspace / "rejection.yaml"
            rejection_paths.append(message_path)
        else:
            message = human_escalation(
                branch,
                message_id=self._id(branch, "human-escalation"),
                evidence_id=evidence.evidence_id,
                provider_id=_FAKE_PLANNER_PROVIDER_ID,
                model_id=_FAKE_PLANNER_MODEL_ID,
                session_id=self._id(branch, "session"),
            )
            message_path = workspace / "dialogue" / f"{message.message_id}.yaml"
            dialogue_paths.append(message_path)
        dump_data(message.model_dump(mode="json"), message_path)

        transcript_path = workspace / "transcript.md"
        transcript = self._transcript(branch, run_id=run_id, evidence_id=evidence.evidence_id)
        transcript_path.write_text(transcript, encoding="utf-8")
        record = run_record(
            branch,
            handoff,
            run_id=run_id,
            status=CodingAgentRunStatus.RETURNED,
            transcript_path=transcript_path,
            transcript_digest=stable_hash({"transcript": transcript}),
            planner_adapter=self.adapter_name,
            planner_identity=_FAKE_PLANNER_MODEL_ID,
        )
        run_record_path = workspace / "run_record.yaml"
        dump_data(record, run_record_path)

        bundle = returned_bundle(
            branch,
            handoff,
            run_id=run_id,
            bundle_id=self._id(branch, "returned-bundle"),
            workspace=workspace,
            run_record_path=run_record_path,
            evidence_paths=[evidence_path],
            dialogue_paths=dialogue_paths,
            plan_draft_paths=plan_draft_paths,
            rejection_paths=rejection_paths,
        )
        self._call_count += 1
        return bundle

    def _id(self, branch: QuestionFamilyBranch, label: str) -> str:
        payload: dict[str, object] = {
            "branch_id": branch.branch_id,
            "outcome": self.outcome,
            "label": label,
        }
        if self._call_count:
            payload["revise_round"] = self._call_count
        digest = stable_hash(payload)
        suffix = f"-r{self._call_count}" if self._call_count else ""
        return f"fake-planner-{self.outcome}-{label}{suffix}-{digest[:12]}"

    def _transcript(self, branch: QuestionFamilyBranch, *, run_id: str, evidence_id: str) -> str:
        return (
            "# Fake Planner Host Run\n\n"
            f"run_id: {run_id}\n"
            f"branch_id: {branch.branch_id}\n"
            f"outcome: {self.outcome}\n"
            f"evidence_id: {evidence_id}\n\n"
            "Deterministic development-only rehearsal. No live dataset access, paid API "
            "call, scientific execution, or downstream bridge artifact.\n"
        )
