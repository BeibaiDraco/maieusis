from __future__ import annotations

import hmac
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..io import dump_data, load_model
from ..provenance import stable_hash
from ..providers.scientific_agents import ScientificAgentProvider, ScientificAgentSessionSnapshot
from ..schemas.planner_run import CodingAgentRunRecord, CodingAgentRunStatus
from ..schemas.planning_dialogue import (
    BranchRejectionMessage,
    ClarificationRequest,
    DatasetFeasibilityFinding,
    HumanEscalationRequest,
    OperationalizationProposal,
    PlanDraftMessage,
    PlanningMessage,
)
from ..schemas.question_family_branch import (
    QuestionFamilyBranch,
    QuestionFamilyBranchEventType,
    QuestionFamilyBranchState,
    QuestionFamilyInspectionEvidence,
)
from ..services.agents.question_owner import (
    QUESTION_OWNER_PROMPT_VERSION,
    answer_clarification_request,
    decide_operationalization,
)
from ..services.orchestration import QuestionFamilyBranchManager
from ..services.planning.evidence_claims import require_planner_evidence_unverified
from ..services.planning.planner_boundaries import assert_planner_boundary_safe


class BranchToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    branch_id: str
    state: str
    event_count: int
    latest_event_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ScientificDialogueServer:
    def __init__(
        self,
        root: str | Path,
        *,
        run_id: str,
        owner_provider: ScientificAgentProvider | None = None,
    ) -> None:
        self.root = Path(root)
        self.run_id = run_id
        self.branch_manager = QuestionFamilyBranchManager(self.root, run_id=run_id)
        self.owner_provider = owner_provider

    def branch_get_context(self, *, branch_id: str, branch_token: str) -> dict[str, Any]:
        branch = self._authorized_branch(branch_id=branch_id, branch_token=branch_token)
        branch = self.branch_manager.record_family_context(
            branch.branch_id, label="branch_get_context"
        )
        return _result(
            branch,
            payload={
                "question_family_id": branch.question_family_id,
                "context_id": branch.context_id,
                "owner_session_id": branch.owner_session_id,
                "family_intent_invariant": branch.family_intent_invariant.model_dump(mode="json"),
                "active_variant_ids": list(branch.active_variant_ids),
                "variant_intent_invariants": [
                    invariant.model_dump(mode="json")
                    for invariant in branch.variant_intent_invariants
                ],
            },
        ).model_dump(mode="json")

    def branch_get_state(self, *, branch_id: str, branch_token: str) -> dict[str, Any]:
        branch = self._authorized_branch(branch_id=branch_id, branch_token=branch_token)
        branch = self.branch_manager.record_family_context(
            branch.branch_id, label="branch_get_state"
        )
        return _result(
            branch,
            payload={
                "event_types": [event.event_type.value for event in branch.events],
                "active_variant_ids": list(branch.active_variant_ids),
            },
        ).model_dump(mode="json")

    def branch_record_inspection_evidence(
        self,
        *,
        branch_id: str,
        branch_token: str,
        evidence: dict[str, Any],
        run_record: dict[str, Any],
    ) -> dict[str, Any]:
        branch = self._authorized_branch(branch_id=branch_id, branch_token=branch_token)
        parsed_evidence = QuestionFamilyInspectionEvidence.model_validate(evidence)
        parsed_run_record = CodingAgentRunRecord.model_validate(run_record)
        require_planner_evidence_unverified(parsed_evidence)
        _assert_run_record_matches_branch(
            parsed_run_record,
            branch=branch,
            run_id=self.run_id,
            allow_prepared=True,
        )
        _assert_no_downstream_payload(parsed_evidence.model_dump(mode="json"))
        updated = self.branch_manager.record_inspection_evidence(
            branch.branch_id,
            parsed_evidence,
            provider_id=parsed_run_record.planner_adapter,
            model_id=parsed_run_record.planner_identity,
            session_id=parsed_run_record.run_record_id,
            prompt_version=parsed_run_record.prompt_version,
            input_digest=parsed_run_record.handoff_digest,
            output_digest=parsed_run_record.transcript_digest
            or stable_hash(parsed_evidence.model_dump(mode="json")),
        )
        return _result(
            updated,
            payload={"evidence_id": parsed_evidence.evidence_id},
        ).model_dump(mode="json")

    def branch_submit_clarification_request(
        self,
        *,
        branch_id: str,
        branch_token: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        return self._record_message(
            branch_id=branch_id,
            branch_token=branch_token,
            message=ClarificationRequest.model_validate(message),
        )

    def branch_ask_question_owner(
        self,
        *,
        branch_id: str,
        branch_token: str,
        planner_message: dict[str, Any],
    ) -> dict[str, Any]:
        if self.owner_provider is None:
            raise ValueError("Question Owner provider is not configured")
        branch = self._authorized_branch(branch_id=branch_id, branch_token=branch_token)
        if planner_message.get("message_type") == "clarification_request":
            parsed: ClarificationRequest | OperationalizationProposal = (
                ClarificationRequest.model_validate(planner_message)
            )
            output_model = "scientific_clarification"
        elif planner_message.get("message_type") == "operationalization_proposal":
            parsed = OperationalizationProposal.model_validate(planner_message)
            output_model = "operationalization_decision"
        else:
            raise ValueError("Question Owner can only answer clarification or operationalization")
        _assert_message_recorded(branch, parsed.message_id)
        session = self._owner_session(branch)
        if output_model == "scientific_clarification":
            owner_message: PlanningMessage = answer_clarification_request(
                session=session,
                branch=branch,
                request=parsed,  # type: ignore[arg-type]
            )
        else:
            owner_message = decide_operationalization(
                session=session,
                branch=branch,
                proposal=parsed,  # type: ignore[arg-type]
            )
        self._write_owner_snapshot(session.snapshot(), branch)
        updated = self.branch_manager.record_planning_message(branch.branch_id, owner_message)
        return _result(
            updated,
            payload={"owner_message": owner_message.model_dump(mode="json")},
        ).model_dump(mode="json")

    def branch_submit_operationalization(
        self,
        *,
        branch_id: str,
        branch_token: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        return self._record_message(
            branch_id=branch_id,
            branch_token=branch_token,
            message=OperationalizationProposal.model_validate(message),
        )

    def branch_submit_feasibility_finding(
        self,
        *,
        branch_id: str,
        branch_token: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        parsed = DatasetFeasibilityFinding.model_validate(message)
        if not parsed.evidence_ids:
            raise ValueError("Dataset feasibility findings require evidence_ids")
        _assert_no_downstream_payload(parsed.model_dump(mode="json"))
        branch = self._authorized_branch(branch_id=branch_id, branch_token=branch_token)
        _assert_feasibility_evidence_supported(branch, parsed)
        updated = self.branch_manager.record_planning_message(
            branch.branch_id,
            parsed,
            event_type=QuestionFamilyBranchEventType.VARIANT_EVIDENCE_RECORDED,
        )
        return _result(updated, payload={"message_id": parsed.message_id}).model_dump(mode="json")

    def branch_submit_plan_draft(
        self,
        *,
        branch_id: str,
        branch_token: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        return self._record_message(
            branch_id=branch_id,
            branch_token=branch_token,
            message=PlanDraftMessage.model_validate(message),
        )

    def branch_submit_rejection(
        self,
        *,
        branch_id: str,
        branch_token: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        return self._record_message(
            branch_id=branch_id,
            branch_token=branch_token,
            message=BranchRejectionMessage.model_validate(message),
        )

    def branch_request_human_review(
        self,
        *,
        branch_id: str,
        branch_token: str,
        message: dict[str, Any],
    ) -> dict[str, Any]:
        return self._record_message(
            branch_id=branch_id,
            branch_token=branch_token,
            message=HumanEscalationRequest.model_validate(message),
        )

    def _record_message(
        self,
        *,
        branch_id: str,
        branch_token: str,
        message: PlanningMessage,
        event_type: QuestionFamilyBranchEventType | None = None,
    ) -> dict[str, Any]:
        _assert_no_downstream_payload(message.model_dump(mode="json"))
        branch = self._authorized_branch(branch_id=branch_id, branch_token=branch_token)
        if self.branch_manager.dialogue_round_limit_reached(branch.branch_id, message):
            return _result(
                branch,
                payload={
                    "message_id": message.message_id,
                    "message_recorded": False,
                    "dialogue_round_limit_reached": True,
                    "owner_dialogue_closed": True,
                    "allowed_terminal_artifacts": [
                        "plan_draft.yaml",
                        "rejection.yaml",
                        "escalation.yaml",
                    ],
                    "instruction": (
                        "Do not retry owner dialogue in this scope. Preserve branch-local evidence "
                        "and write exactly one root terminal artifact: a plan when the existing "
                        "record supports one (retaining unresolved decisions), a rejection when "
                        "the dataset cannot support any sound variant, or an escalation only when "
                        "a genuinely unresolved scientific decision requires it."
                    ),
                },
            ).model_dump(mode="json")
        updated = self.branch_manager.record_planning_message(
            branch.branch_id,
            message,
            event_type=event_type,
        )
        return _result(updated, payload={"message_id": message.message_id}).model_dump(mode="json")

    def _authorized_branch(self, *, branch_id: str, branch_token: str) -> QuestionFamilyBranch:
        branch = self.branch_manager.load_branch(branch_id)
        if branch.state != QuestionFamilyBranchState.PLANNER_INSPECTING:
            raise ValueError("scientific dialogue tools require planner_started branch state")
        expected = scientific_dialogue_branch_token(branch, run_id=self.run_id)
        if not hmac.compare_digest(branch_token, expected):
            raise PermissionError("branch token mismatch")
        return branch

    def _owner_session(self, branch: QuestionFamilyBranch):
        assert self.owner_provider is not None
        snapshot_path = _owner_snapshot_path(self.root, self.run_id, branch.branch_id)
        if snapshot_path.exists():
            snapshot = load_model(snapshot_path, ScientificAgentSessionSnapshot)
            return self.owner_provider.resume_session(snapshot, branch_id=branch.branch_id)
        return self.owner_provider.start_session(
            branch_id=branch.branch_id,
            session_id=branch.owner_session_id,
            prompt_version=QUESTION_OWNER_PROMPT_VERSION,
        )

    def _write_owner_snapshot(
        self,
        snapshot: ScientificAgentSessionSnapshot,
        branch: QuestionFamilyBranch,
    ) -> Path:
        if snapshot.branch_id != branch.branch_id:
            raise ValueError("owner snapshot references another branch")
        return dump_data(snapshot, _owner_snapshot_path(self.root, self.run_id, branch.branch_id))


def scientific_dialogue_branch_token(branch: QuestionFamilyBranch, *, run_id: str) -> str:
    return stable_hash(
        {
            "run_id": run_id,
            "branch_id": branch.branch_id,
            "question_family_id": branch.question_family_id,
            "context_id": branch.context_id,
            "owner_session_id": branch.owner_session_id,
        }
    )


SCIENTIFIC_DIALOGUE_SERVER_LABEL = "maieusis-r5-scientific-dialogue"


def build_server_app(service: ScientificDialogueServer):
    """Wire the 10 branch tools onto a fresh FastMCP for an existing service instance.

    Split out from ``build_server`` so a caller that already holds a
    ``ScientificDialogueServer`` (e.g. the runner that self-hosts the dialogue
    server over localhost HTTP) can serve *that* service — same ``root`` / ``run_id`` /
    ``owner_provider`` — instead of building a second one.
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install MCP support with: uv sync --extra mcp") from exc

    mcp = FastMCP(SCIENTIFIC_DIALOGUE_SERVER_LABEL)
    mcp.tool()(service.branch_get_context)
    mcp.tool()(service.branch_get_state)
    mcp.tool()(service.branch_record_inspection_evidence)
    mcp.tool()(service.branch_submit_clarification_request)
    mcp.tool()(service.branch_ask_question_owner)
    mcp.tool()(service.branch_submit_operationalization)
    mcp.tool()(service.branch_submit_feasibility_finding)
    mcp.tool()(service.branch_submit_plan_draft)
    mcp.tool()(service.branch_submit_rejection)
    mcp.tool()(service.branch_request_human_review)
    return mcp


def build_server(
    root: str | Path,
    *,
    run_id: str,
    owner_provider: ScientificAgentProvider | None = None,
):
    service = ScientificDialogueServer(root, run_id=run_id, owner_provider=owner_provider)
    return build_server_app(service)


def _result(branch: QuestionFamilyBranch, *, payload: dict[str, Any]) -> BranchToolResult:
    latest_event_id = branch.events[-1].event_id if branch.events else ""
    return BranchToolResult(
        branch_id=branch.branch_id,
        state=branch.state.value,
        event_count=len(branch.events),
        latest_event_id=latest_event_id,
        payload=payload,
    )


def _owner_snapshot_path(root: Path, run_id: str, branch_id: str) -> Path:
    return root / run_id / "branches" / branch_id / "owner_session.yaml"


def _assert_message_recorded(branch: QuestionFamilyBranch, message_id: str) -> None:
    if not any(event.payload.planning_message_id == message_id for event in branch.events):
        raise ValueError("planner message must be submitted before asking owner")


def _assert_feasibility_evidence_supported(
    branch: QuestionFamilyBranch,
    finding: DatasetFeasibilityFinding,
) -> None:
    _validate_variant_message_identity(branch, finding.variant_id, finding.question_seed_id)
    evidence_by_id = {evidence.evidence_id: evidence for evidence in branch.inspection_evidence}
    unsupported = [
        evidence_id
        for evidence_id in finding.evidence_ids
        if evidence_id not in evidence_by_id
        or not evidence_by_id[evidence_id].can_support_variant(finding.variant_id)
    ]
    if unsupported:
        raise ValueError(
            "Dataset feasibility findings require branch-local support evidence: "
            + ", ".join(unsupported)
        )


def _assert_run_record_matches_branch(
    run_record: CodingAgentRunRecord,
    *,
    branch: QuestionFamilyBranch,
    run_id: str,
    allow_prepared: bool = False,
) -> None:
    expected = {
        "run_id": run_id,
        "branch_id": branch.branch_id,
        "question_family_id": branch.question_family_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
    }
    mismatched = [
        field
        for field, expected_value in expected.items()
        if getattr(run_record, field) != expected_value
    ]
    if mismatched:
        raise ValueError("planner run record references another " + ", ".join(mismatched))
    allowed_statuses = {CodingAgentRunStatus.RETURNED}
    if allow_prepared:
        allowed_statuses.add(CodingAgentRunStatus.PREPARED)
    if run_record.status not in allowed_statuses:
        raise ValueError("planner run record status is not valid for evidence recording")
    if run_record.source_tree_mutation_detected:
        raise ValueError("planner run record reports source-tree mutation")
    if (
        run_record.source_tree_before_digest
        and run_record.source_tree_after_digest
        and run_record.source_tree_before_digest != run_record.source_tree_after_digest
    ):
        raise ValueError("planner run record source-tree digest changed")


def _validate_variant_message_identity(
    branch: QuestionFamilyBranch,
    variant_id: str,
    question_seed_id: str,
) -> None:
    matches = [
        invariant
        for invariant in branch.variant_intent_invariants
        if invariant.variant_id == variant_id
    ]
    if len(matches) != 1:
        raise ValueError("message does not reference exactly one active branch variant")
    if matches[0].question_seed_id != question_seed_id:
        raise ValueError("message variant_id/question_seed_id mismatch")


def _assert_no_downstream_payload(value: Any) -> None:
    assert_planner_boundary_safe(value, context="scientific dialogue payload")
