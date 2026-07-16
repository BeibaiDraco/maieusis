from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...assets import resolve_asset
from ...provenance import stable_hash
from ...providers.scientific_agents import ScientificAgentSession
from ...schemas.planning_dialogue import (
    BranchDecisionKind,
    ClarificationRequest,
    FamilyMethodSpecificationDecisionMessage,
    FamilyMethodSpecificationProposalMessage,
    FamilyMethodSpecificationRevisionDecisionMessage,
    FamilyMethodSpecificationRevisionProposalMessage,
    FamilyOperationalizationDecisionMessage,
    FamilyOperationalizationProposalMessage,
    FamilyOperationalizationRevisionProposalMessage,
    FamilyVariantPlanningEntry,
    OperationalizationDecision,
    OperationalizationDecisionValue,
    OperationalizationProposal,
    PlanDraftMessage,
    PlanningMessageScope,
    PlanReviewDecisionValue,
    PlanReviewIssueLedgerEntry,
    QuestionOwnerPlanReviewMessage,
    ScientificClarification,
)
from ...schemas.question_family_branch import QuestionFamilyBranch
from .plan_review_ingestion import (
    OwnerPlanReviewContent,
    persist_plan_review_ingestion_diagnostics,
    reconcile_owner_plan_review,
)

QUESTION_OWNER_PROMPT_VERSION = "question_owner/v3"


class QuestionOwnerTurnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    scope: PlanningMessageScope
    variant_id: str
    question_seed_id: str
    family_title: str
    family_summary: str
    shared_scientific_tension: str
    variant_question: str
    variant_scientific_tension: str
    active_variants: list[dict[str, object]] = Field(default_factory=list)
    protected_intent: dict[str, object]
    planner_message_type: str
    planner_message: dict[str, object]
    planner_packet: dict[str, object] = Field(default_factory=dict)
    # Optional runtime review guidance. Not a prompt-version change: steers the reviewer
    # (e.g. "prefer accept/revise/reject; use human_review only when genuinely unresolvable").
    review_guidance: str = ""


class OwnerScientificClarificationContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_interpretation: str
    acceptable_alternatives: list[str] = Field(default_factory=list)
    must_preserve: list[str] = Field(default_factory=list)
    forbidden_reduction: list[str] = Field(default_factory=list)
    rationale: str


class OwnerOperationalizationDecisionContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: OperationalizationDecisionValue
    rationale: str
    required_changes: list[str] = Field(default_factory=list)
    preserves_scientific_intent: bool


class OwnerMethodSpecificationReviewContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: OperationalizationDecisionValue
    rationale: str
    required_changes: list[str] = Field(default_factory=list)
    preserves_scientific_intent: bool
    method_specification_sufficient: bool


def load_question_owner_prompt(prompt_version: str = QUESTION_OWNER_PROMPT_VERSION) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def answer_clarification_request(
    *,
    session: ScientificAgentSession,
    branch: QuestionFamilyBranch,
    request: ClarificationRequest,
) -> ScientificClarification:
    _validate_request_identity(branch, request)
    turn_input = _owner_turn_input(
        branch=branch,
        scope=request.scope,
        variant_id=request.variant_id,
        question_seed_id=request.question_seed_id,
        planner_message_type=request.message_type,
        planner_message=request.model_dump(mode="json"),
    )
    content = session.send(turn_input, OwnerScientificClarificationContent)
    record = session.snapshot().transcript[-1]
    message_payload = {
        "message_id": f"{request.message_id}-owner-clarification",
        "branch_id": branch.branch_id,
        "scope": request.scope,
        "variant_id": request.variant_id,
        "question_seed_id": request.question_seed_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
        "parent_message_id": request.message_id,
        "provider_id": record.provider_id,
        "model_id": record.model_id,
        "session_id": record.session_id,
        "prompt_version": record.prompt_version,
        "input_digest": record.input_digest,
        "output_digest": record.output_digest,
        "request_message_id": request.message_id,
        **content.model_dump(mode="json"),
    }
    return ScientificClarification(
        **message_payload,
        payload_digest=_message_digest("scientific_clarification", message_payload),
    )


def decide_operationalization(
    *,
    session: ScientificAgentSession,
    branch: QuestionFamilyBranch,
    proposal: OperationalizationProposal,
) -> OperationalizationDecision:
    _validate_request_identity(branch, proposal)
    turn_input = _owner_turn_input(
        branch=branch,
        scope=proposal.scope,
        variant_id=proposal.variant_id,
        question_seed_id=proposal.question_seed_id,
        planner_message_type=proposal.message_type,
        planner_message=proposal.model_dump(mode="json"),
    )
    content = session.send(turn_input, OwnerOperationalizationDecisionContent)
    if content.decision == OperationalizationDecisionValue.ACCEPT and not proposal.evidence_ids:
        raise ValueError("owner cannot accept operationalization without planner evidence IDs")
    record = session.snapshot().transcript[-1]
    message_payload = {
        "message_id": f"{proposal.message_id}-owner-decision",
        "branch_id": branch.branch_id,
        "scope": proposal.scope,
        "variant_id": proposal.variant_id,
        "question_seed_id": proposal.question_seed_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
        "parent_message_id": proposal.message_id,
        "provider_id": record.provider_id,
        "model_id": record.model_id,
        "session_id": record.session_id,
        "prompt_version": record.prompt_version,
        "input_digest": record.input_digest,
        "output_digest": record.output_digest,
        "proposal_message_id": proposal.message_id,
        **content.model_dump(mode="json"),
    }
    return OperationalizationDecision(
        **message_payload,
        payload_digest=_message_digest("operationalization_decision", message_payload),
    )


def decide_family_operationalization(
    *,
    session: ScientificAgentSession,
    branch: QuestionFamilyBranch,
    proposal: FamilyOperationalizationProposalMessage
    | FamilyOperationalizationRevisionProposalMessage,
) -> FamilyOperationalizationDecisionMessage:
    _validate_request_identity(branch, proposal)
    turn_input = _owner_turn_input(
        branch=branch,
        scope=proposal.scope,
        variant_id=proposal.variant_id,
        question_seed_id=proposal.question_seed_id,
        planner_message_type=proposal.message_type,
        planner_message=proposal.model_dump(mode="json"),
    )
    content = session.send(turn_input, OwnerOperationalizationDecisionContent)
    if content.decision == OperationalizationDecisionValue.ACCEPT and not proposal.evidence_ids:
        raise ValueError(
            "owner cannot accept family operationalization without planner evidence IDs"
        )
    record = session.snapshot().transcript[-1]
    message_payload = {
        "message_id": f"{proposal.message_id}-owner-decision",
        "branch_id": branch.branch_id,
        "scope": proposal.scope,
        "variant_id": proposal.variant_id,
        "question_seed_id": proposal.question_seed_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
        "parent_message_id": proposal.message_id,
        "provider_id": record.provider_id,
        "model_id": record.model_id,
        "session_id": record.session_id,
        "prompt_version": record.prompt_version,
        "input_digest": record.input_digest,
        "output_digest": record.output_digest,
        "proposal_message_id": proposal.message_id,
        "proposal_packet_id": _family_operationalization_packet_id(proposal),
        **content.model_dump(mode="json"),
        "variant_outcomes": [
            FamilyVariantPlanningEntry(
                variant_id=invariant.variant_id,
                question_seed_id=invariant.question_seed_id,
                decision=BranchDecisionKind.PENDING,
                summary=_family_variant_summary(content.decision),
                evidence_ids=list(proposal.evidence_ids),
            ).model_dump(mode="json")
            for invariant in branch.variant_intent_invariants
        ],
    }
    return FamilyOperationalizationDecisionMessage(
        **message_payload,
        payload_digest=_message_digest("family_operationalization_decision", message_payload),
    )


def review_plan_draft(
    *,
    session: ScientificAgentSession,
    branch: QuestionFamilyBranch,
    draft: PlanDraftMessage,
    plan_draft_packet_id: str,
    diagnostics_dir: str | Path,
    plan_draft_packet: dict[str, object] | None = None,
    review_guidance: str = "",
) -> QuestionOwnerPlanReviewMessage:
    _validate_request_identity(branch, draft)
    if not plan_draft_packet_id.strip():
        raise ValueError("plan_draft_packet_id must be non-empty")
    turn_input = _owner_turn_input(
        branch=branch,
        scope=draft.scope,
        variant_id=draft.variant_id,
        question_seed_id=draft.question_seed_id,
        planner_message_type=draft.message_type,
        planner_message=draft.model_dump(mode="json"),
        planner_packet=plan_draft_packet or {},
        review_guidance=review_guidance,
    )
    content = session.send(turn_input, OwnerPlanReviewContent)
    packet_payload = plan_draft_packet or {}
    content, diagnostics = reconcile_owner_plan_review(
        content,
        branch_id=branch.branch_id,
        source_message_id=draft.message_id,
        review_round=_packet_review_round(packet_payload),
        plan_digest=draft.payload_digest,
        known_issues=_packet_issue_ledger(packet_payload),
    )
    persist_plan_review_ingestion_diagnostics(diagnostics, diagnostics_dir)
    evidence_ids = _plan_draft_evidence_ids(draft)
    if (
        content.review_complete
        and content.decision == PlanReviewDecisionValue.ACCEPT
        and not evidence_ids
    ):
        raise ValueError("owner cannot accept plan draft without planner evidence IDs")
    record = session.snapshot().transcript[-1]
    variant_outcomes = (
        [entry.model_dump(mode="json") for entry in draft.variant_outcomes]
        if content.review_complete and content.decision == PlanReviewDecisionValue.ACCEPT
        else [
            FamilyVariantPlanningEntry(
                variant_id=entry.variant_id,
                question_seed_id=entry.question_seed_id,
                decision=_plan_review_variant_decision(content),
                summary=_owner_plan_review_variant_summary(content),
                evidence_ids=list(entry.evidence_ids),
            ).model_dump(mode="json")
            for entry in draft.variant_outcomes
        ]
    )
    message_payload = {
        "message_id": f"{draft.message_id}-owner-plan-review",
        "branch_id": branch.branch_id,
        "scope": draft.scope,
        "variant_id": draft.variant_id,
        "question_seed_id": draft.question_seed_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
        "parent_message_id": draft.message_id,
        "provider_id": record.provider_id,
        "model_id": record.model_id,
        "session_id": record.session_id,
        "prompt_version": record.prompt_version,
        "input_digest": record.input_digest,
        "output_digest": record.output_digest,
        "plan_draft_message_id": draft.message_id,
        "plan_draft_packet_id": plan_draft_packet_id,
        "analysis_plan_id": draft.analysis_plan_id,
        **content.model_dump(mode="json"),
        "evidence_ids": evidence_ids,
        # Family-level acceptance approves the closure package, not every sibling outcome.
        # Preserve the planner's honest mixed accepted/rejected/escalated decisions and each
        # variant's own evidence scope instead of stamping the family-wide verdict onto all.
        "variant_outcomes": variant_outcomes,
    }
    return QuestionOwnerPlanReviewMessage(
        **message_payload,
        payload_digest=_message_digest("question_owner_plan_review", message_payload),
    )


def review_family_method_specification(
    *,
    session: ScientificAgentSession,
    branch: QuestionFamilyBranch,
    proposal: FamilyMethodSpecificationProposalMessage,
    method_specification_packet: dict[str, object],
) -> FamilyMethodSpecificationDecisionMessage:
    _validate_request_identity(branch, proposal)
    turn_input = _owner_turn_input(
        branch=branch,
        scope=proposal.scope,
        variant_id=proposal.variant_id,
        question_seed_id=proposal.question_seed_id,
        planner_message_type=proposal.message_type,
        planner_message=proposal.model_dump(mode="json"),
        planner_packet=method_specification_packet,
    )
    content = session.send(turn_input, OwnerMethodSpecificationReviewContent)
    if content.decision == OperationalizationDecisionValue.ACCEPT and not proposal.evidence_ids:
        raise ValueError("owner cannot accept method specification without planner evidence IDs")
    record = session.snapshot().transcript[-1]
    message_payload = {
        "message_id": f"{proposal.message_id}-owner-method-spec-review",
        "branch_id": branch.branch_id,
        "scope": proposal.scope,
        "variant_id": proposal.variant_id,
        "question_seed_id": proposal.question_seed_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
        "parent_message_id": proposal.message_id,
        "provider_id": record.provider_id,
        "model_id": record.model_id,
        "session_id": record.session_id,
        "prompt_version": record.prompt_version,
        "input_digest": record.input_digest,
        "output_digest": record.output_digest,
        "method_specification_message_id": proposal.message_id,
        "method_specification_packet_id": proposal.method_specification_packet_id,
        **content.model_dump(mode="json"),
        "evidence_ids": list(proposal.evidence_ids),
        "variant_outcomes": [
            FamilyVariantPlanningEntry(
                variant_id=invariant.variant_id,
                question_seed_id=invariant.question_seed_id,
                decision=_method_spec_variant_decision(content),
                summary=_method_spec_variant_summary(content),
                evidence_ids=list(proposal.evidence_ids),
            ).model_dump(mode="json")
            for invariant in branch.variant_intent_invariants
        ],
    }
    return FamilyMethodSpecificationDecisionMessage(
        **message_payload,
        payload_digest=_message_digest("family_method_specification_decision", message_payload),
    )


def review_family_method_specification_revision(
    *,
    session: ScientificAgentSession,
    branch: QuestionFamilyBranch,
    proposal: FamilyMethodSpecificationRevisionProposalMessage,
    method_specification_revision_packet: dict[str, object],
) -> FamilyMethodSpecificationRevisionDecisionMessage:
    _validate_request_identity(branch, proposal)
    turn_input = _owner_turn_input(
        branch=branch,
        scope=proposal.scope,
        variant_id=proposal.variant_id,
        question_seed_id=proposal.question_seed_id,
        planner_message_type=proposal.message_type,
        planner_message=proposal.model_dump(mode="json"),
        planner_packet=method_specification_revision_packet,
    )
    content = session.send(turn_input, OwnerMethodSpecificationReviewContent)
    if content.decision == OperationalizationDecisionValue.ACCEPT and not proposal.evidence_ids:
        raise ValueError(
            "owner cannot accept revised method specification without planner evidence IDs"
        )
    record = session.snapshot().transcript[-1]
    message_payload = {
        "message_id": f"{proposal.message_id}-owner-method-spec-revision-review",
        "branch_id": branch.branch_id,
        "scope": proposal.scope,
        "variant_id": proposal.variant_id,
        "question_seed_id": proposal.question_seed_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
        "parent_message_id": proposal.message_id,
        "provider_id": record.provider_id,
        "model_id": record.model_id,
        "session_id": record.session_id,
        "prompt_version": record.prompt_version,
        "input_digest": record.input_digest,
        "output_digest": record.output_digest,
        "method_specification_revision_message_id": proposal.message_id,
        "method_specification_revision_packet_id": (
            proposal.method_specification_revision_packet_id
        ),
        "source_owner_review_packet_id": proposal.source_owner_review_packet_id,
        **content.model_dump(mode="json"),
        "evidence_ids": list(proposal.evidence_ids),
        "variant_outcomes": [
            FamilyVariantPlanningEntry(
                variant_id=invariant.variant_id,
                question_seed_id=invariant.question_seed_id,
                decision=_method_spec_variant_decision(content),
                summary=_method_spec_variant_summary(content),
                evidence_ids=list(proposal.evidence_ids),
            ).model_dump(mode="json")
            for invariant in branch.variant_intent_invariants
        ],
    }
    return FamilyMethodSpecificationRevisionDecisionMessage(
        **message_payload,
        payload_digest=_message_digest(
            "family_method_specification_revision_decision",
            message_payload,
        ),
    )


def _owner_turn_input(
    *,
    branch: QuestionFamilyBranch,
    scope: PlanningMessageScope,
    variant_id: str,
    question_seed_id: str,
    planner_message_type: str,
    planner_message: dict[str, object],
    planner_packet: dict[str, object] | None = None,
    review_guidance: str = "",
) -> QuestionOwnerTurnInput:
    variant = _variant_invariant(branch, variant_id) if variant_id else None
    return QuestionOwnerTurnInput(
        review_guidance=review_guidance,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        scope=scope,
        variant_id=variant_id,
        question_seed_id=question_seed_id,
        family_title=branch.family_intent_invariant.shared_phenomenon,
        family_summary=branch.family_intent_invariant.family_claim_boundary,
        shared_scientific_tension=branch.family_intent_invariant.shared_theoretical_tension,
        variant_question=variant.invariant.central_phenomenon if variant else "",
        variant_scientific_tension=variant.invariant.theoretical_tension if variant else "",
        active_variants=[
            {
                "variant_id": invariant.variant_id,
                "question_seed_id": invariant.question_seed_id,
                "central_phenomenon": invariant.invariant.central_phenomenon,
                "theoretical_tension": invariant.invariant.theoretical_tension,
                "target_contrast": invariant.invariant.target_contrast,
                "intended_claim": invariant.invariant.intended_claim,
                "population_scope": invariant.invariant.population_scope,
            }
            for invariant in branch.variant_intent_invariants
        ],
        protected_intent=(
            variant.invariant.model_dump(mode="json")
            if variant
            else branch.family_intent_invariant.model_dump(mode="json")
        ),
        planner_message_type=planner_message_type,
        planner_message=planner_message,
        planner_packet=planner_packet or {},
    )


def _variant_invariant(branch: QuestionFamilyBranch, variant_id: str):
    for invariant in branch.variant_intent_invariants:
        if invariant.variant_id == variant_id:
            return invariant
    raise ValueError("unknown active variant")


def _validate_request_identity(
    branch: QuestionFamilyBranch,
    request: ClarificationRequest
    | OperationalizationProposal
    | FamilyOperationalizationProposalMessage
    | FamilyOperationalizationRevisionProposalMessage
    | FamilyMethodSpecificationProposalMessage
    | FamilyMethodSpecificationRevisionProposalMessage
    | PlanDraftMessage,
) -> None:
    if request.branch_id != branch.branch_id:
        raise ValueError("owner request references another branch")
    if request.context_id != branch.context_id:
        raise ValueError("owner request references another context")
    if request.owner_session_id != branch.owner_session_id:
        raise ValueError("owner request references another owner session")
    if request.scope == PlanningMessageScope.FAMILY:
        return
    variant = _variant_invariant(branch, request.variant_id)
    if request.question_seed_id != variant.question_seed_id:
        raise ValueError("owner request variant_id/question_seed_id mismatch")


def _family_operationalization_packet_id(
    proposal: FamilyOperationalizationProposalMessage
    | FamilyOperationalizationRevisionProposalMessage,
) -> str:
    if isinstance(proposal, FamilyOperationalizationRevisionProposalMessage):
        return proposal.revision_proposal_packet_id
    return proposal.proposal_packet_id


def _message_digest(
    message_type: Literal[
        "scientific_clarification",
        "operationalization_decision",
        "family_operationalization_decision",
        "question_owner_plan_review",
        "family_method_specification_decision",
        "family_method_specification_revision_decision",
    ],
    payload: dict[str, object],
) -> str:
    return stable_hash({"message_type": message_type, **payload})


def _plan_draft_evidence_ids(draft: PlanDraftMessage) -> list[str]:
    evidence_ids: list[str] = []
    for outcome in draft.variant_outcomes:
        for evidence_id in outcome.evidence_ids:
            if evidence_id not in evidence_ids:
                evidence_ids.append(evidence_id)
    return evidence_ids


def _packet_review_round(packet: dict[str, object]) -> int:
    value = packet.get("review_round", 0)
    return value if isinstance(value, int) and value >= 0 else 0


def _packet_issue_ledger(packet: dict[str, object]) -> list[PlanReviewIssueLedgerEntry]:
    raw = packet.get("issue_ledger", [])
    if not isinstance(raw, list):
        return []
    return [PlanReviewIssueLedgerEntry.model_validate(item) for item in raw]


def _plan_review_variant_decision(content: OwnerPlanReviewContent) -> BranchDecisionKind:
    if not content.review_complete:
        return BranchDecisionKind.PENDING
    if content.decision == PlanReviewDecisionValue.ACCEPT:
        return BranchDecisionKind.ACCEPTED
    if content.decision == PlanReviewDecisionValue.REJECT:
        if not content.preserves_scientific_intent:
            return BranchDecisionKind.REJECTED_SCIENTIFIC_DRIFT
        return BranchDecisionKind.REJECTED_OPERATIONALIZATION_FAILURE
    if content.decision == PlanReviewDecisionValue.HUMAN_REVIEW:
        return BranchDecisionKind.HUMAN_ESCALATION
    return BranchDecisionKind.PENDING


def _owner_plan_review_variant_summary(content: OwnerPlanReviewContent) -> str:
    if not content.review_complete:
        return (
            "Question Owner review content was retained, but its typed review artifact was "
            "incomplete and conferred no accept, revision, or rejection authority."
        )
    if content.decision == PlanReviewDecisionValue.ACCEPT:
        return "Question Owner accepted this variant's B16 plan draft for independent review."
    if content.decision == PlanReviewDecisionValue.REVISE:
        return "Question Owner required plan-draft revision for this variant."
    if content.decision == PlanReviewDecisionValue.REJECT:
        return "Question Owner rejected this variant's plan draft."
    return "Question Owner escalated this variant's plan draft for human review."


def _family_variant_summary(decision: OperationalizationDecisionValue) -> str:
    if decision == OperationalizationDecisionValue.ACCEPT:
        return (
            "Question Owner accepted the family-level operationalization for continued "
            "planning; a later issue must still draft and review a plan."
        )
    if decision == OperationalizationDecisionValue.REVISE:
        return (
            "Question Owner required revision of the family-level operationalization before "
            "plan drafting."
        )
    if decision == OperationalizationDecisionValue.REJECT:
        return (
            "Question Owner rejected the family-level operationalization; a later issue must "
            "convert this into a branch-local revision or rejection path."
        )
    return (
        "Question Owner escalated the family-level operationalization for human scientific "
        "review before planning can continue."
    )


def _method_spec_variant_decision(
    content: OwnerMethodSpecificationReviewContent,
) -> BranchDecisionKind:
    if content.decision == OperationalizationDecisionValue.ACCEPT:
        return BranchDecisionKind.ACCEPTED
    if content.decision == OperationalizationDecisionValue.REJECT:
        if not content.preserves_scientific_intent:
            return BranchDecisionKind.REJECTED_SCIENTIFIC_DRIFT
        return BranchDecisionKind.REJECTED_OPERATIONALIZATION_FAILURE
    if content.decision == OperationalizationDecisionValue.HUMAN_REVIEW:
        return BranchDecisionKind.HUMAN_ESCALATION
    return BranchDecisionKind.PENDING


def _method_spec_variant_summary(content: OwnerMethodSpecificationReviewContent) -> str:
    if content.decision == OperationalizationDecisionValue.ACCEPT:
        return "Question Owner accepted the method specification for human-review import."
    if content.decision == OperationalizationDecisionValue.REVISE:
        return "Question Owner required method-specification revision."
    if content.decision == OperationalizationDecisionValue.REJECT:
        return "Question Owner rejected the method specification."
    return "Question Owner escalated the method specification for human review."
