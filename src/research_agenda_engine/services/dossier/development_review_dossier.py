"""Real owner + independent plan review -> generic development dossierr.

Host-agnostic (Codex reuses this): after a coding-agent planner returns and imports a family
PLAN, this module runs the REAL typed reviews and renders the translated end-user dossier:

    plan draft (imported)
      -> question_owner.review_plan_draft            (owner model)
      -> plan_reviewer.review_plan_draft_independently (a distinct model)
      -> GenericFamilyBranchOutcomePacket + GenericFamilyReviewDecisionPacket
      -> run_generic_development_dossier_pipeline (writer -> renderer -> end-user)
      -> machine/audit dossier + end-user Markdown + hidden audit sidecar

The dossier render itself is deterministic (no API); the only paid calls are the two reviews,
whose providers are injected (mock for CI, real for the gated live run). The rendered dossier
carries ``automated`` authority by default — no human-review gate is imported, so it can never be
mistaken for serious authority. This module does not touch the multi-family
orchestrator and imports none of its private builders.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ...io import dump_data
from ...provenance import stable_hash
from ...providers.scientific_agents import ScientificAgentProvider, ScientificAgentSession
from ...schemas.generic_family_outcome import (
    GenericFamilyBranchOutcomePacket,
    GenericFamilyOutcomeKind,
    GenericVariantScientificOutcome,
)
from ...schemas.generic_review_authority import (
    GenericFamilyReviewDecisionPacket,
    GenericReviewDecisionValue,
)
from ...schemas.generic_scientific_source import (
    DatasetGroundingLevel,
    QuestionFamilyScientificSourceSnapshot,
    QuestionFamilyScientificVariantSnapshot,
)
from ...schemas.multi_family_dossier import ReviewAuthority
from ...schemas.planning_dialogue import (
    BranchDecisionKind,
    ClassifiedPlanReviewChange,
    FamilyVariantPlanningEntry,
    IndependentPlanReviewMessage,
    PlanDraftMessage,
    PlanningMessageScope,
    PlanReviewChangeClass,
    PlanReviewIssueLedgerEntry,
    PlanReviewIssueStatus,
    PlanRevisionContext,
    QuestionOwnerPlanReviewMessage,
    VariantAnalysisPlanEntry,
)
from ...schemas.question_family import QuestionFamily
from ...schemas.question_family_branch import QuestionFamilyInspectionEvidence
from ..agents.plan_reviewer import (
    PLAN_FIDELITY_REVIEWER_PROMPT_VERSION,
    review_plan_draft_independently,
)
from ..agents.question_owner import QUESTION_OWNER_PROMPT_VERSION, review_plan_draft
from ..orchestration import QuestionFamilyBranchManager
from ..planning.generic_plan_revision import (
    PlanRevisionClassification,
    aggregate_required_changes,
    build_plan_revision_context,
    classify_plan_reviews,
    novelty_recheck_required,
)
from .generic_family_dossier import (
    GenericDossierPipelineResult,
    run_generic_development_dossier_pipeline,
)

# A bounded re-plan step: given a revision context (prior plan + union of required changes), re-spawn
# the planner and return the revised, already-imported+recorded family-scoped plan draft. Supplied by
# the orchestrator (closure over host/backend/dialogue_server); ``None`` keeps the single-pass path.
RevisionReplan = Callable[..., PlanDraftMessage]

# Default runtime guidance steering the real reviewers to prefer a resolvable decision. Injected as
# runtime review context supplements the active owner/reviewer prompts. ``human_review``
# (escalate) is a rare last resort.
DEFAULT_REVIEW_GUIDANCE = (
    "Prefer a decisive, resolvable outcome. Use 'accept' when the plan is sound, 'revise' with "
    "specific required_changes when it can be fixed, or 'reject' when the dataset cannot support the "
    "question. A family plan is sound when at least one variant has an evidence-backed plan and "
    "every sibling has an honest non-pending outcome; do not reject the whole family solely because "
    "one sibling is rejected or escalated. Reserve 'human_review' for cases that are genuinely "
    "unresolvable by revision or rejection; it is a rare last resort, not a default."
)

# A malformed review REPLY gets this many extra attempts before the family closes. It re-asks
# the reviewers only — never the planner — so it is bounded, cheap, and cannot alter the plan.
_MAX_REVIEW_ARTIFACT_REATTEMPTS = 2

# Development-mode authority provenance for the review decision (honest label; not human review).
_DEVELOPMENT_REVIEW_PROVIDER_ID = "local:development-review-authority"
_DEVELOPMENT_REVIEW_MODEL_ID = "development-review-authority"
_DEVELOPMENT_REVIEW_PROMPT_VERSION = "development_family_review/v1"


class DevelopmentReviewNotAccepted(Exception):
    """Raised when the real owner or independent review did not accept the plan draft.

    The reviewed-PLAN dossier path renders an ``accepted`` outcome, so it must NOT be used
    when a reviewer returned ``revise`` / ``reject`` / ``human_review`` — that is a real,
    honest scientific outcome (revision or rejection), not a clean plan. The caller decides
    what to do with it (e.g. surface it, render a revision path, or skip).
    """

    def __init__(
        self,
        *,
        owner_decision: str,
        independent_decision: str,
        owner_review_path: str = "",
        independent_review_path: str = "",
    ) -> None:
        self.owner_decision = owner_decision
        self.independent_decision = independent_decision
        self.owner_review_path = owner_review_path
        self.independent_review_path = independent_review_path
        super().__init__(
            "reviewed-plan dossier requires both reviews to accept; got "
            f"owner={owner_decision}, independent={independent_decision}. "
            f"Reviews persisted at {owner_review_path or '<unset>'} and "
            f"{independent_review_path or '<unset>'}."
        )


class DevelopmentRevisionTerminal(DevelopmentReviewNotAccepted):
    """Base for the bounded revise-loop honest terminals (no accepted dossier).

    These are raised only when a ``replan`` collaborator is available (the automated loop). Each is a
    distinct honest outcome — NOT an undifferentiated failure — that the caller maps to its own
    ``FamilyDossierStatus``. None is a mandatory human handoff. Subclassing ``DevelopmentReviewNotAccepted``
    keeps the legacy single-pass ``except`` sites working as a FAILED_VALIDATION fallback.
    """

    def __init__(
        self,
        *,
        owner_decision: str,
        independent_decision: str,
        rounds_used: int,
        owner_review_path: str = "",
        independent_review_path: str = "",
        required_changes: tuple[str, ...] | list[str] = (),
    ) -> None:
        self.rounds_used = rounds_used
        self.required_changes = list(required_changes)
        super().__init__(
            owner_decision=owner_decision,
            independent_decision=independent_decision,
            owner_review_path=owner_review_path,
            independent_review_path=independent_review_path,
        )


class DevelopmentReviewRejected(DevelopmentRevisionTerminal):
    """A reviewer returned ``reject`` — an honest terminal (does not consume a revise round)."""


class DevelopmentReviewEscalated(DevelopmentRevisionTerminal):
    """A reviewer returned ``human_review`` (escalate) — a rare honest terminal, not a handoff."""


class DevelopmentRevisionBudgetExhausted(DevelopmentRevisionTerminal):
    """Non-material ``revise`` persisted past the per-family round budget without acceptance."""


class DevelopmentReviewIncomplete(DevelopmentRevisionTerminal):
    """Reviewer metadata was incomplete; planner revision authority was never fabricated."""


class DevelopmentMaterialRevisionDeferred(DevelopmentRevisionTerminal):
    """A material revision was detected; deferred (needs front-half literature / novelty recheck).

    Not auto-completed and not escalated to a human — an honest terminal until later work wires the
    literature required for the novelty recheck.
    """

    def __init__(
        self,
        *,
        owner_decision: str,
        independent_decision: str,
        rounds_used: int,
        owner_review_path: str = "",
        independent_review_path: str = "",
        required_changes: tuple[str, ...] | list[str] = (),
        novelty_recheck_required: bool = False,
    ) -> None:
        self.novelty_recheck_required = novelty_recheck_required
        super().__init__(
            owner_decision=owner_decision,
            independent_decision=independent_decision,
            rounds_used=rounds_used,
            owner_review_path=owner_review_path,
            independent_review_path=independent_review_path,
            required_changes=required_changes,
        )


class DevelopmentPlanReviewPacket(BaseModel):
    """Bounded branch-local plan and evidence view used by both scientific reviewers."""

    model_config = ConfigDict(extra="forbid")

    plan_draft_packet_id: str
    branch_id: str
    context_id: str
    analysis_plan_id: str
    review_round: int = Field(default=0, ge=0)
    max_revise_rounds: int = Field(default=0, ge=0)
    is_final_review_round: bool = True
    prior_review_history: list[DevelopmentPlanReviewHistoryEntry] = Field(default_factory=list)
    issue_ledger: list[PlanReviewIssueLedgerEntry] = Field(default_factory=list)
    evidence_ids: list[str]
    variant_analysis_plans: list[VariantAnalysisPlanEntry] = Field(default_factory=list)
    evidence_views: list[DevelopmentReviewEvidenceView] = Field(default_factory=list)


class DevelopmentPlanReviewHistoryEntry(BaseModel):
    """Compact prior-round ledger shown to both reviewers to prevent moving goalposts."""

    model_config = ConfigDict(extra="forbid")

    review_round: int = Field(ge=0)
    plan_draft_message_id: str
    owner_decision: str
    owner_required_changes: list[str] = Field(default_factory=list)
    independent_decision: str
    independent_required_changes: list[str] = Field(default_factory=list)
    issue_ledger: list[PlanReviewIssueLedgerEntry] = Field(default_factory=list)


class DevelopmentReviewEvidenceView(BaseModel):
    """Reviewer-safe evidence content without raw rows, source paths, or provider secrets."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    scope: str
    variant_id: str = ""
    source_type: str
    finding: str = Field(max_length=4000)
    limitations: list[str] = Field(default_factory=list, max_length=12)
    dataset_claim_status: str
    evidence_digest: str


class DevelopmentReviewDossierResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    branch_id: str
    question_family_id: str
    owner_provider_id: str
    owner_model_id: str
    reviewer_provider_id: str
    reviewer_model_id: str
    owner_review_decision: str
    independent_review_decision: str
    review_closure_basis: str = "both_reviewers_accept"
    review_authority: str
    dataset_grounding_level: str
    owner_review_path: str
    independent_review_path: str
    outcome_packet_path: str
    review_decision_path: str
    machine_dossier_path: str
    end_user_dossier_path: str
    audit_sidecar_path: str
    end_user_manifest_path: str
    end_user_rendered_event_id: str
    revise_rounds_used: int = 0
    # Owner + independent review usage summed across ALL revise rounds (None if none reported).
    # Tokens come from the SDK responses; ``cost_usd`` is present only when a provider reports USD.
    review_total_tokens: int | None = None
    review_cost_usd: float | None = None


def run_development_review_and_dossier(
    *,
    output_root: str | Path,
    run_id: str,
    branch_id: str,
    family: QuestionFamily,
    plan_draft: PlanDraftMessage,
    owner_provider: ScientificAgentProvider,
    reviewer_provider: ScientificAgentProvider,
    dataset_grounding_level: DatasetGroundingLevel = DatasetGroundingLevel.SCHEMA_METADATA_INSPECTED,
    workspace: str | Path | None = None,
    replan: RevisionReplan | None = None,
    max_revise_rounds: int = 4,
    review_guidance: str = "",
    review_authority: ReviewAuthority = ReviewAuthority.AUTOMATED,
) -> DevelopmentReviewDossierResult:
    """Run the real owner + independent plan review (a bounded revise-loop) and render the dossier.

    Both reviews must ACCEPT to render an accepted dossier — the honesty gate is preserved. On a
    non-material ``revise``, when a ``replan`` collaborator is supplied, the union of both reviewers'
    ``required_changes`` is fed back to the planner for a bounded re-plan (up to ``max_revise_rounds``
    re-spawns) and the revised plan is re-reviewed. Every other non-accept outcome raises a distinct
    honest terminal (reject / escalate / material-deferred / budget-exhausted); with no ``replan`` the
    loop degrades to the legacy single pass (base ``DevelopmentReviewNotAccepted``). Each round's draft
    plus both reviews are persisted to the flat paths (decisive round) AND a per-round copy, and
    recorded as replayable branch events, so branch replay reconstructs the round history.
    """
    if max_revise_rounds < 0:
        raise ValueError("max_revise_rounds must be >= 0")
    review_artifact_reattempts = 0
    if review_authority != ReviewAuthority.AUTOMATED:
        raise ValueError("development review emits automated authority only")
    output_root = Path(output_root)
    manager = QuestionFamilyBranchManager(output_root, run_id=run_id)
    branch = manager.load_branch(branch_id)
    if plan_draft.scope != PlanningMessageScope.FAMILY:
        raise ValueError("development review requires a family-scoped plan draft")

    work = (
        Path(workspace)
        if workspace is not None
        else _default_workspace(output_root, run_id, branch_id)
    )
    work.mkdir(parents=True, exist_ok=True)
    owner_review_path = work / "owner_plan_review.yaml"
    independent_review_path = work / "independent_plan_review.yaml"

    # Owner + independent review usage, accumulated across every revise round (surfaced only on the
    # accepted return; non-accept terminals raise and do not report cost).
    review_tokens_total = 0
    review_cost_total = 0.0
    review_has_tokens = False
    review_has_cost = False

    current_plan = plan_draft
    round_index = 0
    prior_review_history: list[DevelopmentPlanReviewHistoryEntry] = []
    issue_ledger: list[PlanReviewIssueLedgerEntry] = []
    closure_basis = "both_reviewers_accept"
    while True:
        evidence_ids = _plan_evidence_ids(current_plan)
        if not evidence_ids:
            raise ValueError("plan draft cites no branch-local evidence; cannot review")
        packet = DevelopmentPlanReviewPacket(
            plan_draft_packet_id=f"development-plan-review-packet-{family.question_family_id}",
            branch_id=branch.branch_id,
            context_id=branch.context_id,
            analysis_plan_id=current_plan.analysis_plan_id,
            review_round=round_index,
            max_revise_rounds=max_revise_rounds,
            is_final_review_round=round_index >= max_revise_rounds,
            prior_review_history=list(prior_review_history),
            issue_ledger=list(issue_ledger),
            evidence_ids=evidence_ids,
            variant_analysis_plans=list(current_plan.variant_analysis_plans),
            evidence_views=_review_evidence_views(branch.inspection_evidence, evidence_ids),
        )

        # (1) Real owner plan review (owner model). Session id is owner-specific + round-scoped.
        owner_session = owner_provider.start_session(
            branch_id=branch.branch_id,
            session_id=_review_session_id(
                "owner", family.question_family_id, round_index, review_artifact_reattempts
            ),
            prompt_version=QUESTION_OWNER_PROMPT_VERSION,
        )
        owner_review = review_plan_draft(
            session=owner_session,
            branch=branch,
            draft=current_plan,
            plan_draft_packet_id=packet.plan_draft_packet_id,
            diagnostics_dir=work / "diagnostics",
            plan_draft_packet=packet.model_dump(mode="json"),
            review_guidance=review_guidance,
        )
        branch = manager.record_planning_message(branch.branch_id, owner_review)

        # Persist the paid owner verdict and reviewed plan before invoking the independent provider.
        # If that second provider is unavailable, the successful owner work must remain visible.
        # Each re-ask writes its own directory: the discarded replies are the only evidence of
        # what the reviewers actually returned, and overwriting them loses exactly that.
        round_dir = work / (
            f"round_{round_index}"
            if not review_artifact_reattempts
            else f"round_{round_index}_attempt_{review_artifact_reattempts}"
        )
        round_dir.mkdir(parents=True, exist_ok=True)
        dump_data(current_plan.model_dump(mode="json"), round_dir / "plan_draft.yaml")
        dump_data(owner_review, owner_review_path)
        dump_data(owner_review, round_dir / "owner_plan_review.yaml")
        owner_tokens, owner_cost = _session_last_usage(owner_session)
        if owner_tokens is not None:
            review_tokens_total += owner_tokens
            review_has_tokens = True
        if owner_cost is not None:
            review_cost_total += owner_cost
            review_has_cost = True

        # (2) Real independent review (a distinct model; distinct session id => independence check).
        reviewer_session = reviewer_provider.start_session(
            branch_id=branch.branch_id,
            session_id=_review_session_id(
                "independent", family.question_family_id, round_index, review_artifact_reattempts
            ),
            prompt_version=PLAN_FIDELITY_REVIEWER_PROMPT_VERSION,
        )
        independent_review = review_plan_draft_independently(
            session=reviewer_session,
            branch=branch,
            packet=packet,
            draft=current_plan,
            owner_review=owner_review,
            diagnostics_dir=work / "diagnostics",
            review_guidance=review_guidance,
        )
        branch = manager.record_planning_message(branch.branch_id, independent_review)

        # Persist the (paid) review artifacts IMMEDIATELY — before any gate — to the flat paths (the
        # decisive round; byte-compatible with the single-pass contract) AND a per-round audit copy,
        # so every round's draft + reviews are reviewable on disk even on a non-accepting outcome.
        dump_data(independent_review, independent_review_path)
        dump_data(independent_review, round_dir / "independent_plan_review.yaml")

        # The owner usage was retained before the second call; add the independent usage now.
        reviewer_tokens, reviewer_cost = _session_last_usage(reviewer_session)
        if reviewer_tokens is not None:
            review_tokens_total += reviewer_tokens
            review_has_tokens = True
        if reviewer_cost is not None:
            review_cost_total += reviewer_cost
            review_has_cost = True

        issue_ledger = _updated_review_issue_ledger(
            existing=issue_ledger,
            owner_review=owner_review,
            independent_review=independent_review,
            review_round=round_index,
            plan_digest=current_plan.payload_digest,
        )

        classification = classify_plan_reviews(
            owner_review,
            independent_review,
            allow_independent_closeout=round_index >= max_revise_rounds,
        )
        if classification in {
            PlanRevisionClassification.ACCEPTED,
            PlanRevisionClassification.ACCEPTED_BY_INDEPENDENT_CLOSEOUT,
        }:
            if classification == PlanRevisionClassification.ACCEPTED_BY_INDEPENDENT_CLOSEOUT:
                closure_basis = "independent_final_closeout_with_pre_execution_locks"
            break

        owner_decision = owner_review.decision.value
        independent_decision = independent_review.decision.value
        required_changes = aggregate_required_changes(owner_review, independent_review)
        if classification == PlanRevisionClassification.REVIEW_INCOMPLETE:
            review_artifact_issues = list(
                dict.fromkeys(
                    [
                        *owner_review.review_artifact_issues,
                        *independent_review.review_artifact_issues,
                    ]
                )
            )
            # A malformed review artifact — an unrecognized criterion status, a revise with no
            # required changes — is a reply-shape failure, not a judgement on the plan. Ending the
            # family on the first one meant a single badly formed reply destroyed work that was
            # already paid for and possibly sound: four of six families in one live leg
            # (2026-07-25). Ask the reviewers again, at most `_MAX_REVIEW_ARTIFACT_REATTEMPTS`
            # times, before treating it as terminal. This re-asks the REVIEWERS only — the planner
            # is never re-spawned, so the plan under review is unchanged and no revise round is
            # consumed.
            if review_artifact_reattempts < _MAX_REVIEW_ARTIFACT_REATTEMPTS:
                review_artifact_reattempts += 1
                continue
            raise DevelopmentReviewIncomplete(
                owner_decision=owner_decision,
                independent_decision=independent_decision,
                rounds_used=round_index,
                owner_review_path=str(owner_review_path),
                independent_review_path=str(independent_review_path),
                required_changes=review_artifact_issues,
            )
        # Distinct honest terminals — none is a mandatory human handoff (AGENTS.md #10). A reject or
        # escalate does not consume a revise round; a material revision is deferred (needs 5a
        # literature for the novelty recheck), not auto-completed.
        if classification == PlanRevisionClassification.REJECTED:
            raise DevelopmentReviewRejected(
                owner_decision=owner_decision,
                independent_decision=independent_decision,
                rounds_used=round_index,
                owner_review_path=str(owner_review_path),
                independent_review_path=str(independent_review_path),
                required_changes=required_changes,
            )
        if classification == PlanRevisionClassification.ESCALATED:
            raise DevelopmentReviewEscalated(
                owner_decision=owner_decision,
                independent_decision=independent_decision,
                rounds_used=round_index,
                owner_review_path=str(owner_review_path),
                independent_review_path=str(independent_review_path),
                required_changes=required_changes,
            )
        if classification == PlanRevisionClassification.MATERIAL_REVISION:
            raise DevelopmentMaterialRevisionDeferred(
                owner_decision=owner_decision,
                independent_decision=independent_decision,
                rounds_used=round_index,
                owner_review_path=str(owner_review_path),
                independent_review_path=str(independent_review_path),
                required_changes=required_changes,
                novelty_recheck_required=novelty_recheck_required(owner_review, independent_review),
            )

        # NON_MATERIAL_REVISE — the loopable case.
        if replan is None:
            # Legacy single pass: no re-plan collaborator, so a non-accepting review is terminal
            # (preserves the 2e-direct contract and existing tests).
            raise DevelopmentReviewNotAccepted(
                owner_decision=owner_decision,
                independent_decision=independent_decision,
                owner_review_path=str(owner_review_path),
                independent_review_path=str(independent_review_path),
            )
        if round_index >= max_revise_rounds:
            raise DevelopmentRevisionBudgetExhausted(
                owner_decision=owner_decision,
                independent_decision=independent_decision,
                rounds_used=round_index,
                owner_review_path=str(owner_review_path),
                independent_review_path=str(independent_review_path),
                required_changes=required_changes,
            )

        prior_review_history.append(
            DevelopmentPlanReviewHistoryEntry(
                review_round=round_index,
                plan_draft_message_id=current_plan.message_id,
                owner_decision=owner_review.decision.value,
                owner_required_changes=list(owner_review.required_changes),
                independent_decision=independent_review.decision.value,
                independent_required_changes=list(independent_review.required_changes),
                issue_ledger=list(issue_ledger),
            )
        )

        # Feed the union of required changes back to the planner and re-spawn for the next round.
        revision_context: PlanRevisionContext = build_plan_revision_context(
            revision_round=round_index + 1,
            prior_plan_draft=current_plan,
            owner_review=owner_review,
            independent_review=independent_review,
            prior_evidence_ids=evidence_ids,
        )
        current_plan = replan(revision_context=revision_context)
        if current_plan.scope != PlanningMessageScope.FAMILY:
            raise ValueError("revised plan draft must be family-scoped")
        branch = manager.load_branch(branch.branch_id)
        round_index += 1

    # ACCEPTED: build the generic outcome + review-decision packets (automated by default).
    evidence_ids = _plan_evidence_ids(current_plan)
    source_snapshot = _build_source_snapshot(
        branch=branch, family=family, run_id=run_id, grounding=dataset_grounding_level
    )
    outcome = _build_outcome_packet(
        branch=branch,
        family=family,
        plan_draft=current_plan,
        owner_review=owner_review,
        independent_review=independent_review,
        closure_basis=closure_basis,
        source_snapshot=source_snapshot,
        evidence_ids=evidence_ids,
        run_id=run_id,
        grounding=dataset_grounding_level,
    )
    decision = _build_review_decision(
        branch=branch,
        outcome=outcome,
        run_id=run_id,
        grounding=dataset_grounding_level,
        owner_review=owner_review,
        independent_review=independent_review,
        closure_basis=closure_basis,
        authority=review_authority,
    )

    outcome_packet_path = work / "generic_family_outcome_packet.yaml"
    review_decision_path = work / "generic_family_review_decision.yaml"
    dump_data(outcome, outcome_packet_path)
    dump_data(decision, review_decision_path)

    # Deterministic dossier pipeline -> machine dossier + end-user translation + audit sidecar.
    dossier: GenericDossierPipelineResult = run_generic_development_dossier_pipeline(
        output_root=output_root,
        run_id=run_id,
        branch_id=branch.branch_id,
        outcome_packet=outcome,
        review_decision=decision,
        source_snapshot=source_snapshot,
        family_title=family.title,
        family_summary=family.summary,
    )

    return DevelopmentReviewDossierResult(
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        owner_provider_id=owner_review.provider_id,
        owner_model_id=owner_review.model_id,
        reviewer_provider_id=independent_review.provider_id,
        reviewer_model_id=independent_review.model_id,
        owner_review_decision=owner_review.decision.value,
        independent_review_decision=independent_review.decision.value,
        review_closure_basis=closure_basis,
        review_authority=decision.authority.value,
        dataset_grounding_level=dataset_grounding_level.value,
        owner_review_path=str(owner_review_path),
        independent_review_path=str(independent_review_path),
        outcome_packet_path=str(outcome_packet_path),
        review_decision_path=str(review_decision_path),
        machine_dossier_path=dossier.machine_dossier_path,
        end_user_dossier_path=dossier.end_user_dossier_path,
        audit_sidecar_path=dossier.audit_sidecar_path,
        end_user_manifest_path=dossier.end_user_manifest_path,
        end_user_rendered_event_id=dossier.end_user_rendered_event_id,
        revise_rounds_used=round_index,
        review_total_tokens=review_tokens_total if review_has_tokens else None,
        review_cost_usd=review_cost_total if review_has_cost else None,
    )


def _session_last_usage(session: ScientificAgentSession) -> tuple[int | None, float | None]:
    """Return (total_tokens, cost_usd) from the session's most recent transcript record."""
    transcript = session.snapshot().transcript
    if not transcript:
        return (None, None)
    last = transcript[-1]
    return (last.total_tokens, last.cost_usd)


def _review_session_id(role: str, family_id: str, round_index: int, attempt: int = 0) -> str:
    """Round- and attempt-scoped review session id.

    Round 0 attempt 0 keeps the historical, un-suffixed id. The attempt suffix exists because a
    malformed reply is re-asked within the same round: without it three separately paid messages
    share one identity while carrying different output digests, which breaks the replayable
    typed-message contract and destroys the very record of WHY the replies keep coming back
    malformed.
    """
    suffix = f"-r{round_index}" if round_index else ""
    attempt_suffix = f"-a{attempt}" if attempt else ""
    return f"development-{role}-review-{family_id}{suffix}{attempt_suffix}"


def _default_workspace(output_root: Path, run_id: str, branch_id: str) -> Path:
    return output_root / run_id / "branches" / branch_id / "planner" / "development_review"


def _plan_evidence_ids(plan_draft: PlanDraftMessage) -> list[str]:
    seen: list[str] = []
    for outcome in plan_draft.variant_outcomes:
        for evidence_id in outcome.evidence_ids:
            if evidence_id and evidence_id not in seen:
                seen.append(evidence_id)
    return seen


def _updated_review_issue_ledger(
    *,
    existing: list[PlanReviewIssueLedgerEntry],
    owner_review: QuestionOwnerPlanReviewMessage,
    independent_review: IndependentPlanReviewMessage,
    review_round: int,
    plan_digest: str,
) -> list[PlanReviewIssueLedgerEntry]:
    """Advance the stable issue ledger without comparing or deduplicating English prose."""

    previous_by_id = {item.change_id: item for item in existing}
    current: dict[
        str,
        tuple[
            ClassifiedPlanReviewChange,
            Literal["question_owner", "independent_reviewer"],
        ],
    ] = {}
    for item in owner_review.classified_required_changes:
        if item.change_id:
            current[item.change_id] = (item, "question_owner")
    for item in independent_review.classified_required_changes:
        if item.change_id and item.change_id not in current:
            current[item.change_id] = (item, "independent_reviewer")

    ledger: list[PlanReviewIssueLedgerEntry] = []
    for prior in existing:
        if prior.change_id in current:
            continue
        status = (
            PlanReviewIssueStatus.RESOLVED
            if prior.classification == PlanReviewChangeClass.SCIENTIFIC_BLOCKER
            else prior.status
        )
        ledger.append(prior.model_copy(update={"status": status}))

    status_by_class = {
        PlanReviewChangeClass.SCIENTIFIC_BLOCKER: PlanReviewIssueStatus.OPEN,
        PlanReviewChangeClass.PRE_EXECUTION_LOCK: (
            PlanReviewIssueStatus.RETAINED_PRE_EXECUTION_LOCK
        ),
        PlanReviewChangeClass.OPTIONAL_IMPROVEMENT: (
            PlanReviewIssueStatus.RETAINED_OPTIONAL_IMPROVEMENT
        ),
    }
    for change_id, (item, origin) in current.items():
        previous = previous_by_id.get(change_id)
        ledger.append(
            PlanReviewIssueLedgerEntry(
                change_id=change_id,
                change=item.change,
                origin=previous.origin if previous is not None else origin,
                classification=item.classification,
                rationale=item.rationale,
                hard_boundary_implicated=item.hard_boundary_implicated,
                late_blocker_basis=item.late_blocker_basis,
                evidence_ids=item.evidence_ids,
                first_seen_round=(
                    previous.first_seen_round if previous is not None else review_round
                ),
                last_seen_round=review_round,
                introduced_by_plan_digest=(
                    previous.introduced_by_plan_digest if previous is not None else plan_digest
                ),
                status=status_by_class[item.classification],
            )
        )
    return sorted(ledger, key=lambda item: (item.first_seen_round, item.change_id))


def _review_evidence_views(
    evidence_items: tuple[QuestionFamilyInspectionEvidence, ...],
    evidence_ids: list[str],
) -> list[DevelopmentReviewEvidenceView]:
    """Project cited evidence into a deterministic, bounded reviewer packet."""

    by_id = {item.evidence_id: item for item in evidence_items}
    missing = [evidence_id for evidence_id in evidence_ids if evidence_id not in by_id]
    if missing:
        raise ValueError(
            "plan draft cites evidence absent from branch state: " + ", ".join(missing)
        )
    views: list[DevelopmentReviewEvidenceView] = []
    for evidence_id in evidence_ids:
        evidence = by_id[evidence_id]
        views.append(
            DevelopmentReviewEvidenceView(
                evidence_id=evidence.evidence_id,
                scope=evidence.scope.value,
                variant_id=evidence.variant_id,
                source_type=evidence.source_type.value,
                finding=_bounded_review_text(evidence.finding, limit=4000),
                limitations=[
                    _bounded_review_text(item, limit=1000) for item in evidence.limitations[:12]
                ],
                dataset_claim_status=evidence.dataset_claim_status.value,
                evidence_digest=stable_hash(evidence.model_dump(mode="json")),
            )
        )
    return views


def _bounded_review_text(value: str, *, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    marker = " [bounded reviewer view]"
    return text[: limit - len(marker)].rstrip() + marker


def _build_source_snapshot(
    *,
    branch,
    family: QuestionFamily,
    run_id: str,
    grounding: DatasetGroundingLevel,
) -> QuestionFamilyScientificSourceSnapshot:
    return QuestionFamilyScientificSourceSnapshot(
        source_snapshot_id=f"scientific-source-snapshot-{family.question_family_id}",
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=family.question_family_id,
        context_id=family.context_id,
        family_title=family.title,
        family_summary=family.summary,
        shared_scientific_tension=family.shared_scientific_tension,
        semantic_axes=list(family.semantic_axes),
        non_mergeable_distinctions=list(family.non_mergeable_distinctions),
        source_pattern_ids=list(family.source_pattern_ids),
        source_topic_claim_ids=list(family.source_topic_claim_ids),
        source_dataset_context_ids=list(family.source_dataset_context_ids),
        source_family_ids=list(family.source_family_ids),
        proposal_stage_uncertainties=list(family.proposal_stage_uncertainties),
        assumptions_about_dataset=list(family.assumptions_about_dataset),
        source_family_digest=stable_hash(family.model_dump(mode="json")),
        variants=[
            QuestionFamilyScientificVariantSnapshot(
                variant_id=variant.variant_id,
                question_seed_id=variant.question_seed_id,
                question=variant.seed.question,
                scientific_tension=variant.seed.scientific_tension,
                why_scientifically_important=variant.seed.why_scientifically_important,
                variant_role=variant.variant_role,
                distinction_axes=[axis.value for axis in variant.distinction_axes],
                distinct_from_siblings=variant.distinct_from_siblings,
                dataset_leverage_hypothesis=variant.seed.dataset_leverage_hypothesis,
                competing_explanations=list(variant.seed.competing_explanations),
                discriminating_observation=variant.seed.discriminating_observation,
                positive_result_consequence=variant.seed.positive_result_consequence,
                negative_result_consequence=variant.seed.negative_result_consequence,
                null_result_consequence=variant.seed.null_result_consequence,
                ambiguous_constructs=list(variant.seed.ambiguous_constructs),
                likely_implementation_challenges=list(
                    variant.seed.likely_implementation_challenges
                ),
                assumptions_about_dataset=list(variant.seed.assumptions_about_dataset),
                source_pattern_ids=list(variant.seed.source_pattern_ids),
                source_paper_case_ids=list(variant.seed.source_paper_case_ids),
                source_variant_ids=list(variant.source_variant_ids),
                source_variant_digest=stable_hash(variant.model_dump(mode="json")),
            )
            for variant in family.variants
        ],
    )


def _variant_scientific_outcome(
    variant: QuestionFamilyScientificVariantSnapshot,
    *,
    grounding: DatasetGroundingLevel,
) -> GenericVariantScientificOutcome:
    return GenericVariantScientificOutcome(
        variant_id=variant.variant_id,
        question_seed_id=variant.question_seed_id,
        scientific_question=variant.question,
        variant_role=variant.variant_role,
        scientific_contrast=variant.distinct_from_siblings,
        discriminating_observation=variant.discriminating_observation,
        dataset_leverage_status=(
            f"The dataset leverage hypothesis is preserved: {variant.dataset_leverage_hypothesis} "
            f"Actual dataset grounding is {grounding.value}."
        ),
        competing_explanations=variant.competing_explanations,
        outcome_meanings=[
            variant.positive_result_consequence,
            variant.negative_result_consequence,
            variant.null_result_consequence,
        ],
        remaining_uncertainties=[
            *variant.assumptions_about_dataset,
            *variant.likely_implementation_challenges,
            "Human review is optional and has not been imported for this automated dossier.",
        ],
    )


def _variant_entries(
    *,
    branch,
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
    evidence_id: str,
    grounding: DatasetGroundingLevel,
) -> list[FamilyVariantPlanningEntry]:
    by_variant = {variant.variant_id: variant for variant in source_snapshot.variants}
    entries: list[FamilyVariantPlanningEntry] = []
    for invariant in branch.variant_intent_invariants:
        variant = by_variant[invariant.variant_id]
        entries.append(
            FamilyVariantPlanningEntry(
                variant_id=invariant.variant_id,
                question_seed_id=invariant.question_seed_id,
                decision=BranchDecisionKind.ACCEPTED,
                summary=(
                    f"Reviewed development plan for '{variant.question}' preserving the role "
                    f"'{variant.variant_role}'. Distinct because {variant.distinct_from_siblings}. "
                    f"Discriminating observation: {variant.discriminating_observation}. Dataset "
                    f"grounding is {grounding.value}; human review is optional and not imported."
                ),
                evidence_ids=[evidence_id],
            )
        )
    return entries


def _build_outcome_packet(
    *,
    branch,
    family: QuestionFamily,
    plan_draft: PlanDraftMessage,
    owner_review: QuestionOwnerPlanReviewMessage,
    independent_review: IndependentPlanReviewMessage,
    closure_basis: str,
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
    evidence_ids: list[str],
    run_id: str,
    grounding: DatasetGroundingLevel,
) -> GenericFamilyBranchOutcomePacket:
    residual_locks = [
        item.change
        for item in independent_review.owner_change_assessments
        if item.classification.value == "pre_execution_lock"
    ]
    closeout_note = (
        "Both typed reviewers accepted the planning product."
        if closure_basis == "both_reviewers_accept"
        else (
            "The Question Owner retained revision requests at the final bounded round; the "
            "independent reviewer accepted the planning product after classifying every residual "
            "request as non-blocking and outside hard scientific/integrity boundaries."
        )
    )
    return GenericFamilyBranchOutcomePacket(
        outcome_packet_id=f"generic-family-outcome-plan-{family.question_family_id}",
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_snapshot_id=source_snapshot.source_snapshot_id,
        source_snapshot_digest=stable_hash(source_snapshot.model_dump(mode="json")),
        dataset_grounding_level=grounding,
        outcome_kind=GenericFamilyOutcomeKind.PLAN,
        decision=BranchDecisionKind.ACCEPTED,
        summary=(
            f"Reviewed development-mode planning outcome for {family.title}. It supports "
            f"development dossier rendering only (no human-review gate imported). {closeout_note}"
        ),
        family_scientific_summary=(
            f"{source_snapshot.family_summary} The shared tension is "
            f"{source_snapshot.shared_scientific_tension}"
        ),
        source_message_ids=[
            plan_draft.message_id,
            owner_review.message_id,
            independent_review.message_id,
        ],
        # The top-level ledger must contain the union cited by the plan's per-variant outcomes.
        # Keeping only the first item makes every additional, valid branch-local citation appear
        # absent at dossier validation time and turns an accepted multi-evidence plan into a false
        # provenance-integrity terminal.
        evidence_ids=list(evidence_ids),
        # Use the PLAN's per-variant evidence (the planner scopes evidence to each variant:
        # family-scoped + that-variant-scoped). The reviewers' variant_outcomes re-stamp ALL
        # plan evidence onto every variant, which the outcome validator rejects when the planner
        # used variant-scoped evidence (a family-scoped-only plan happened to pass before).
        variant_outcomes=list(plan_draft.variant_outcomes),
        variant_analysis_plans=list(plan_draft.variant_analysis_plans),
        variant_scientific_outcomes=[
            _variant_scientific_outcome(variant, grounding=grounding)
            for variant in source_snapshot.variants
        ],
        accepted_plan_draft_message_id=plan_draft.message_id,
        accepted_plan_draft_packet_id=owner_review.plan_draft_packet_id,
        owner_plan_review_message_id=owner_review.message_id,
        independent_plan_review_message_id=independent_review.message_id,
        limitations=[
            "Development-mode automated authority only.",
            f"Dataset grounding level: {grounding.value}.",
            "Human review is optional and has not been imported.",
            *[
                f"Pre-execution lock retained by independent closeout: {item}"
                for item in residual_locks
            ],
        ],
    )


def _build_review_decision(
    *,
    branch,
    outcome: GenericFamilyBranchOutcomePacket,
    run_id: str,
    grounding: DatasetGroundingLevel,
    owner_review: QuestionOwnerPlanReviewMessage,
    independent_review: IndependentPlanReviewMessage,
    closure_basis: str,
    authority: ReviewAuthority,
) -> GenericFamilyReviewDecisionPacket:
    review_mode = authority.value
    input_digest = stable_hash(
        {
            "run_id": run_id,
            "branch_id": branch.branch_id,
            "source_outcome_packet_id": outcome.outcome_packet_id,
            "owner_plan_review_message_id": outcome.owner_plan_review_message_id,
            "independent_plan_review_message_id": outcome.independent_plan_review_message_id,
            "review_mode": review_mode,
            "closure_basis": closure_basis,
        }
    )
    provider_id = _DEVELOPMENT_REVIEW_PROVIDER_ID
    model_id = _DEVELOPMENT_REVIEW_MODEL_ID
    session_label = "development-review-authority"
    if authority == ReviewAuthority.AUTOMATED:
        provider_id = f"automated:{owner_review.provider_id}+{independent_review.provider_id}"
        model_id = f"{owner_review.model_id}+{independent_review.model_id}"
        session_digest = stable_hash(
            {
                "owner_session_id": owner_review.session_id,
                "independent_session_id": independent_review.session_id,
            }
        )
        session_label = f"automated-review-authority-{session_digest[:12]}"
    return GenericFamilyReviewDecisionPacket(
        decision_packet_id=f"generic-development-review-decision-{branch.question_family_id}",
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_outcome_packet_id=outcome.outcome_packet_id,
        authority=authority,
        decision=GenericReviewDecisionValue.ACCEPT_FOR_DEVELOPMENT_DOSSIER,
        decision_summary=(
            (
                "Typed owner and independent plan review passed."
                if closure_basis == "both_reviewers_accept"
                else (
                    "At the bounded final round, the independent reviewer accepted the planning "
                    "product and classified every residual Owner request as a non-blocking "
                    "pre-execution lock or optional improvement with no hard boundary implicated."
                )
            )
            + " Automated development-mode authority allows a dossier render only (no "
            "human-review gate imported)."
        ),
        provider_id=provider_id,
        model_id=model_id,
        prompt_version=_DEVELOPMENT_REVIEW_PROMPT_VERSION,
        session_id=f"{session_label}-session-{branch.question_family_id}",
        input_digest=input_digest,
        output_digest=stable_hash(
            {"decision": "accept_for_development_dossier", **{"i": input_digest}}
        ),
        dataset_grounding_level=grounding,
        dataset_claim_status=outcome.dataset_claim_status,
        development_dossier_rendering_allowed=True,
        development_dossier_generation_allowed=True,
    )
