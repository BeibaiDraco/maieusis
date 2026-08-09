from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...assets import resolve_asset
from ...provenance import stable_hash
from ...providers.models.base import DEFAULT_EFFORT, DEFAULT_THINKING
from ...providers.scientific_agents import (
    ScientificAgentProvider,
    ScientificAgentSession,
)
from ...schemas.planning_dialogue import (
    BranchDecisionKind,
    FamilyVariantPlanningEntry,
    IndependentPlanReviewMessage,
    PlanDraftMessage,
    PlanningMessageScope,
    PlanReviewDecisionValue,
    PlanReviewIssueLedgerEntry,
    QuestionOwnerPlanReviewMessage,
)
from ...schemas.question_family_branch import QuestionFamilyBranch
from .plan_review_ingestion import (
    IndependentPlanReviewContent,
    IndependentPlanReviewModelOutput,
    expand_independent_plan_review_model_output,
    persist_plan_review_ingestion_diagnostics,
    reconcile_independent_plan_review,
)
from .reviewer_base import (
    assert_reviewer_session_independent,
    build_scientific_reviewer_provider_from_env,
)

PLAN_FIDELITY_REVIEWER_PROMPT_VERSION = "plan_fidelity_reviewer/v6"


class PlanFidelityReviewerTurnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    scope: PlanningMessageScope
    family_title: str
    family_summary: str
    shared_scientific_tension: str
    active_variants: list[dict[str, object]] = Field(default_factory=list)
    protected_intent: dict[str, object]
    plan_draft_packet: dict[str, object]
    plan_draft_message: dict[str, object]
    owner_plan_review_message: dict[str, object]
    # Optional runtime review guidance. Not a prompt-version change: steers the reviewer
    # (e.g. "prefer accept/revise/reject; use human_review only when genuinely unresolvable").
    review_guidance: str = ""


def load_plan_fidelity_reviewer_prompt(
    prompt_version: str = PLAN_FIDELITY_REVIEWER_PROMPT_VERSION,
) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def build_plan_fidelity_reviewer_provider_from_env(
    *,
    provider: Literal["openai", "anthropic"] | None = None,
    allow_pro_model: bool = False,
    project_root: str | Path | None = None,
    thinking: str = DEFAULT_THINKING,
    effort: str = DEFAULT_EFFORT,
) -> ScientificAgentProvider:
    """Build a live independent plan reviewer provider from runtime env files."""
    return build_scientific_reviewer_provider_from_env(
        system_prompt_loader=load_plan_fidelity_reviewer_prompt,
        credential_fallback=("openai", "anthropic"),
        unsupported_provider_label="plan reviewer",
        provider=provider,
        allow_pro_model=allow_pro_model,
        project_root=project_root,
        thinking=thinking,
        effort=effort,
    )


def review_plan_draft_independently(
    *,
    session: ScientificAgentSession,
    branch: QuestionFamilyBranch,
    packet: BaseModel,
    draft: PlanDraftMessage,
    owner_review: QuestionOwnerPlanReviewMessage,
    diagnostics_dir: str | Path,
    review_guidance: str = "",
) -> IndependentPlanReviewMessage:
    _validate_identity(branch, packet=packet, draft=draft, owner_review=owner_review)
    turn_input = _reviewer_turn_input(
        branch=branch,
        packet=packet,
        draft=draft,
        owner_review=owner_review,
        review_guidance=review_guidance,
    )
    model_output = session.send(turn_input, IndependentPlanReviewModelOutput)
    content = expand_independent_plan_review_model_output(
        model_output,
        owner_change_issues=owner_review.classified_required_changes,
    )
    content, diagnostics = reconcile_independent_plan_review(
        content,
        branch_id=branch.branch_id,
        source_message_id=draft.message_id,
        owner_required_changes=(
            owner_review.required_changes
            if owner_review.decision
            in {PlanReviewDecisionValue.ACCEPT, PlanReviewDecisionValue.REVISE}
            else None
        ),
        owner_change_issues=owner_review.classified_required_changes,
        review_round=_packet_review_round(packet),
        plan_digest=draft.payload_digest,
        known_issues=_packet_issue_ledger(packet),
    )
    persist_plan_review_ingestion_diagnostics(diagnostics, diagnostics_dir)
    evidence_ids = _packet_evidence_ids(packet)
    if (
        content.review_complete
        and content.decision == PlanReviewDecisionValue.ACCEPT
        and not evidence_ids
    ):
        raise ValueError("independent reviewer cannot accept plan draft without evidence IDs")
    record = session.snapshot().transcript[-1]
    assert_reviewer_session_independent(record.session_id, owner_review.session_id)
    variant_outcomes = (
        [entry.model_dump(mode="json") for entry in draft.variant_outcomes]
        if content.review_complete and content.decision == PlanReviewDecisionValue.ACCEPT
        else [
            FamilyVariantPlanningEntry(
                variant_id=entry.variant_id,
                question_seed_id=entry.question_seed_id,
                decision=_reviewer_variant_decision(content),
                summary=_reviewer_variant_summary(content),
                evidence_ids=list(entry.evidence_ids),
            ).model_dump(mode="json")
            for entry in draft.variant_outcomes
        ]
    )
    message_payload = {
        "message_id": f"{draft.message_id}-independent-review",
        "branch_id": branch.branch_id,
        "scope": draft.scope,
        "variant_id": draft.variant_id,
        "question_seed_id": draft.question_seed_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
        "parent_message_id": owner_review.message_id,
        "provider_id": record.provider_id,
        "model_id": record.model_id,
        "session_id": record.session_id,
        "prompt_version": record.prompt_version,
        "input_digest": record.input_digest,
        "output_digest": record.output_digest,
        "plan_draft_message_id": draft.message_id,
        "plan_draft_packet_id": _packet_id(packet),
        "owner_plan_review_message_id": owner_review.message_id,
        "analysis_plan_id": draft.analysis_plan_id,
        **content.model_dump(mode="json"),
        "evidence_ids": evidence_ids,
        # A family-level accept approves a mixed closure package. Keep the planner's
        # per-variant decision and evidence bindings; do not accept a rejected sibling or
        # copy sibling-only evidence across variant boundaries.
        "variant_outcomes": variant_outcomes,
    }
    return IndependentPlanReviewMessage(
        **message_payload,
        payload_digest=_message_digest("independent_plan_review", message_payload),
    )


def _reviewer_turn_input(
    *,
    branch: QuestionFamilyBranch,
    packet: BaseModel,
    draft: PlanDraftMessage,
    owner_review: QuestionOwnerPlanReviewMessage,
    review_guidance: str = "",
) -> PlanFidelityReviewerTurnInput:
    return PlanFidelityReviewerTurnInput(
        review_guidance=review_guidance,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        scope=draft.scope,
        family_title=branch.family_intent_invariant.shared_phenomenon,
        family_summary=branch.family_intent_invariant.family_claim_boundary,
        shared_scientific_tension=branch.family_intent_invariant.shared_theoretical_tension,
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
        protected_intent=branch.family_intent_invariant.model_dump(mode="json"),
        plan_draft_packet=packet.model_dump(mode="json"),
        plan_draft_message=draft.model_dump(mode="json"),
        owner_plan_review_message=owner_review.model_dump(mode="json"),
    )


def _validate_identity(
    branch: QuestionFamilyBranch,
    *,
    packet: BaseModel,
    draft: PlanDraftMessage,
    owner_review: QuestionOwnerPlanReviewMessage,
) -> None:
    for label, branch_id in {
        "packet": _packet_text_field(packet, "branch_id"),
        "draft": draft.branch_id,
        "owner review": owner_review.branch_id,
    }.items():
        if branch_id != branch.branch_id:
            raise ValueError(f"independent reviewer {label} references another branch")
    if (
        _packet_text_field(packet, "context_id") != branch.context_id
        or draft.context_id != branch.context_id
    ):
        raise ValueError("independent reviewer source references another context")
    if owner_review.context_id != branch.context_id:
        raise ValueError("independent reviewer owner review references another context")
    if draft.message_id != owner_review.plan_draft_message_id:
        raise ValueError("independent reviewer owner review does not match plan draft")
    if _packet_id(packet) != owner_review.plan_draft_packet_id:
        raise ValueError("independent reviewer owner review does not match plan packet")
    if draft.analysis_plan_id != _packet_text_field(packet, "analysis_plan_id"):
        raise ValueError("independent reviewer draft does not match packet analysis_plan_id")
    if (
        draft.scope != PlanningMessageScope.FAMILY
        or owner_review.scope != PlanningMessageScope.FAMILY
    ):
        raise ValueError("independent reviewer requires family-scoped plan review inputs")


def _packet_id(packet: BaseModel) -> str:
    for field_name in (
        "plan_draft_revision_packet_id",
        "plan_draft_packet_id",
        "generic_plan_draft_packet_id",
    ):
        value = getattr(packet, field_name, "")
        if isinstance(value, str) and value.strip():
            return value
    raise ValueError("independent reviewer plan packet is missing a packet ID")


def _packet_review_round(packet: BaseModel) -> int:
    value = getattr(packet, "review_round", 0)
    return value if isinstance(value, int) and value >= 0 else 0


def _packet_issue_ledger(packet: BaseModel) -> list[PlanReviewIssueLedgerEntry]:
    raw = getattr(packet, "issue_ledger", [])
    if not isinstance(raw, list):
        return []
    return [
        item
        if isinstance(item, PlanReviewIssueLedgerEntry)
        else PlanReviewIssueLedgerEntry.model_validate(item)
        for item in raw
    ]


def _packet_evidence_ids(packet: BaseModel) -> list[str]:
    value = getattr(packet, "evidence_ids", None)
    if not isinstance(value, list):
        raise ValueError("independent reviewer plan packet is missing evidence_ids")
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _packet_text_field(packet: BaseModel, field_name: str) -> str:
    value = getattr(packet, field_name, "")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"independent reviewer plan packet is missing {field_name}")
    return value


def _reviewer_variant_decision(content: IndependentPlanReviewContent) -> BranchDecisionKind:
    if not content.review_complete:
        return BranchDecisionKind.PENDING
    if content.decision == PlanReviewDecisionValue.ACCEPT:
        return BranchDecisionKind.ACCEPTED
    if content.decision == PlanReviewDecisionValue.REJECT:
        return content.rejection_reason or BranchDecisionKind.REJECTED_OPERATIONALIZATION_FAILURE
    if content.decision == PlanReviewDecisionValue.HUMAN_REVIEW:
        return BranchDecisionKind.HUMAN_ESCALATION
    return BranchDecisionKind.PENDING


def _reviewer_variant_summary(content: IndependentPlanReviewContent) -> str:
    if not content.review_complete:
        return (
            "Independent review content was retained, but its typed review artifact was "
            "incomplete and conferred no accept, revision, or rejection authority."
        )
    if content.decision == PlanReviewDecisionValue.ACCEPT:
        return "Independent reviewer accepted this variant's B16 plan draft."
    if content.decision == PlanReviewDecisionValue.REVISE:
        return "Independent reviewer required plan-draft revision for this variant."
    if content.decision == PlanReviewDecisionValue.REJECT:
        return "Independent reviewer rejected this variant's plan draft."
    return "Independent reviewer escalated this variant's plan draft for human review."


def _message_digest(message_type: str, payload: dict[str, object]) -> str:
    return stable_hash({"message_type": message_type, **payload})
