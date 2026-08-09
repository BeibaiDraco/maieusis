"""Shared kernel for front-half quality gates.

Three primitives every front-half gate builds on, over the 5a-0 ``reviewer_base``:

* ``resolve_gate_outcome`` — turns a reviewer model's ``GateReviewContent`` (its say-so) into an
  EARNED ``GateOutcome``. ``accept`` is never read from the model's ``decision`` field: it is granted
  only when every required criterion is present and passed, no blocker/hallucination finding remains,
  no ``required_changes`` are outstanding, and the host confirmed evidence resolution. A model that
  claims ``accept`` with a failed criterion is DOWNGRADED (to ``reject`` if the artifact is unfaithful,
  else ``revise``), so a false accept can never slip through. Infrastructure errors are host-raised and
  never reachable from the model's text.
* ``run_gate_with_revise_loop`` — a bounded Issue-A-style retry: on ``revise`` the generator re-drafts
  with the structured ``required_changes`` and is re-reviewed, up to ``max_revise_rounds``. Exhaustion
  is recorded as ``budget_exhausted`` (an honest terminal), never silently turned into a reject.
* ``assert_cross_provider_reviewer`` — the standard-path independence rule: the reviewer's provider
  must differ from every generator's (reused from ``reviewer_base``).

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel

from ...provenance import stable_hash
from ...providers.scientific_agents import ScientificAgentSession
from ...schemas.gate_outcome import (
    GateCriterionAssessment,
    GateCriterionAuditRecord,
    GateCriterionAuditStatus,
    GateDecision,
    GateLoopResult,
    GateModelDecision,
    GateOutcome,
    GateReviewContent,
    ReviewerExecutionKind,
)
from .reviewer_base import assert_reviewer_provider_independent

T = TypeVar("T")


@dataclass(frozen=True)
class CriterionAssessmentResolution:
    """Deterministic host resolution of raw reviewer labels against one canonical criterion set."""

    canonical_assessments: tuple[GateCriterionAssessment, ...]
    audit: tuple[GateCriterionAuditRecord, ...]
    missing: tuple[str, ...]
    failed: tuple[str, ...]
    unknown: tuple[str, ...]
    conflicts: tuple[str, ...]


def normalize_gate_criterion(value: str) -> str:
    """Normalize presentation only: trim/casefold and collapse whitespace/hyphens to underscores."""

    return re.sub(r"[\s-]+", "_", value.strip().casefold())


def resolve_criterion_assessments(
    assessments: Sequence[GateCriterionAssessment],
    required_criteria: Sequence[str],
    *,
    drop_unrequired: bool = False,
) -> CriterionAssessmentResolution:
    """Resolve criterion coverage without semantic paraphrase guessing.

    Required criteria remain host-owned. Formatting-only variants map deterministically to them;
    unknown labels, genuinely missing criteria, and conflicting duplicates remain review-incomplete
    and therefore cannot earn accept. Every raw item is retained in the typed audit.
    """

    canonical_by_normalized: dict[str, str] = {}
    for raw_required in required_criteria:
        canonical = raw_required.strip()
        normalized = normalize_gate_criterion(canonical)
        if not normalized:
            raise ValueError("required gate criterion must be non-empty")
        if normalized in canonical_by_normalized:
            raise ValueError(
                "required gate criteria collide after presentation normalization: "
                f"{canonical_by_normalized[normalized]!r} and {canonical!r}"
            )
        canonical_by_normalized[normalized] = canonical

    first_by_canonical: dict[str, GateCriterionAssessment] = {}
    audit: list[GateCriterionAuditRecord] = []
    unknown: list[str] = []
    conflicts: list[str] = []
    for assessment in assessments:
        normalized = normalize_gate_criterion(assessment.criterion)
        canonical = canonical_by_normalized.get(normalized, "")
        if not canonical:
            status = GateCriterionAuditStatus.UNKNOWN
            # `drop_unrequired` is set only when the HOST has decided a criterion does not apply to
            # this artifact -- a formation trace with no citation to judge. Without it, a reviewer
            # that answers the dropped criterion anyway makes it `unknown`, and any unknown blocks
            # accept: the paper would go from a coin flip to certain death. The assessment is still
            # recorded in the audit, so nothing is hidden; it just cannot decide.
            if not drop_unrequired:
                unknown.append(assessment.criterion)
        elif canonical not in first_by_canonical:
            status = GateCriterionAuditStatus.MATCHED
            first_by_canonical[canonical] = assessment
        elif first_by_canonical[canonical].passed == assessment.passed:
            status = GateCriterionAuditStatus.DUPLICATE_CONSISTENT
        else:
            status = GateCriterionAuditStatus.DUPLICATE_CONFLICT
            if canonical not in conflicts:
                conflicts.append(canonical)
        audit.append(
            GateCriterionAuditRecord(
                raw_criterion=assessment.criterion,
                normalized_criterion=normalized,
                canonical_criterion=canonical,
                passed=assessment.passed,
                notes=assessment.notes,
                status=status,
            )
        )

    canonical_assessments = tuple(
        GateCriterionAssessment(
            criterion=canonical,
            passed=first_by_canonical[canonical].passed,
            notes=first_by_canonical[canonical].notes,
        )
        for canonical in canonical_by_normalized.values()
        if canonical in first_by_canonical
    )
    missing = tuple(
        canonical
        for canonical in canonical_by_normalized.values()
        if canonical not in first_by_canonical
    )
    failed = tuple(
        assessment.criterion for assessment in canonical_assessments if not assessment.passed
    )
    return CriterionAssessmentResolution(
        canonical_assessments=canonical_assessments,
        audit=tuple(audit),
        missing=missing,
        failed=failed,
        unknown=tuple(unknown),
        conflicts=tuple(conflicts),
    )


def clean_required_changes(changes: Sequence[str]) -> list[str]:
    """Drop blank model list items and trim presentation-only surrounding whitespace."""

    return [trimmed for item in changes if (trimmed := item.strip())]


def assert_cross_provider_reviewer(
    reviewer_provider_id: str,
    generator_provider_ids: Sequence[str],
    *,
    gate_name: str,
) -> None:
    """Standard-path independence: the reviewer provider must differ from every generator's."""
    assert_reviewer_provider_independent(
        reviewer_provider_id,
        generator_provider_ids,
        role_label=f"{gate_name} reviewer",
    )


def run_structured_gate_review(
    *,
    session: ScientificAgentSession,
    turn_input: BaseModel,
    gate_name: str,
    required_criteria: Sequence[str],
    evidence_resolved: bool,
    generator_provider_ids: Sequence[str],
    candidate: BaseModel | None = None,
    candidate_digest: str | None = None,
    drop_unrequired_criteria: bool = False,
) -> GateOutcome:
    """Send ``turn_input`` to an independent reviewer session and derive the EARNED ``GateOutcome``.

    ``evidence_resolved`` is the HOST's deterministic pre-check (cited ids resolve, digests match,
    spans exist) — the model cannot assert evidence closure. The reviewer must be cross-provider from
    every generator. The model's ``decision`` is re-derived structurally by ``resolve_gate_outcome``.

    Pass the specific reviewed artifact as ``candidate`` (or its precomputed ``candidate_digest``) so the
    outcome BINDS to it — the promoter later re-hashes the same artifact and refuses a mismatch. The
    reviewer's ``execution_kind`` (live vs mock) is read type-side from the session.
    """
    digest = _resolve_candidate_digest(candidate=candidate, candidate_digest=candidate_digest)
    # Independence is checked BEFORE the (paid) send, from the session's own provider id — a same-family
    # reviewer never reaches the API. The post-send record.provider_id equals session.provider_id.
    assert_cross_provider_reviewer(session.provider_id, generator_provider_ids, gate_name=gate_name)
    content = session.send(turn_input, GateReviewContent)
    record = session.snapshot().transcript[-1]
    return resolve_gate_outcome(
        gate_name=gate_name,
        content=content,
        required_criteria=required_criteria,
        evidence_resolved=evidence_resolved,
        drop_unrequired_criteria=drop_unrequired_criteria,
        candidate_digest=digest,
        generator_provider_ids=generator_provider_ids,
        reviewer_execution_kind=session.execution_kind,
        reviewer_provider_id=record.provider_id,
        reviewer_model_id=record.model_id,
        reviewer_session_id=record.session_id,
        input_digest=record.input_digest,
        output_digest=record.output_digest,
    )


def _resolve_candidate_digest(*, candidate: BaseModel | None, candidate_digest: str | None) -> str:
    """Exactly one of ``candidate`` / ``candidate_digest`` must be given → the binding digest."""
    if (candidate is None) == (candidate_digest is None):
        raise ValueError("pass exactly one of candidate or candidate_digest")
    return candidate_digest if candidate_digest is not None else stable_hash(candidate)


def resolve_gate_outcome(
    *,
    gate_name: str,
    content: GateReviewContent,
    required_criteria: Sequence[str],
    evidence_resolved: bool,
    candidate_digest: str,
    drop_unrequired_criteria: bool = False,
    generator_provider_ids: Sequence[str],
    reviewer_execution_kind: ReviewerExecutionKind,
    infrastructure_error: bool = False,
    reviewer_provider_id: str = "",
    reviewer_model_id: str = "",
    reviewer_session_id: str = "",
    input_digest: str = "",
    output_digest: str = "",
) -> GateOutcome:
    """Derive the EARNED gate outcome from the reviewer content (see module docstring)."""

    criterion_resolution = resolve_criterion_assessments(
        content.criterion_assessments, required_criteria, drop_unrequired=drop_unrequired_criteria
    )
    cleaned_required_changes = clean_required_changes(content.required_changes)

    def build(
        decision: GateDecision,
        *,
        downgraded_from: GateDecision | None = None,
        required_changes: list[str] | None = None,
    ) -> GateOutcome:
        return GateOutcome(
            gate_name=gate_name,
            decision=decision,
            candidate_digest=candidate_digest,
            generator_provider_ids=list(generator_provider_ids),
            reviewer_execution_kind=reviewer_execution_kind,
            rationale=content.rationale,
            criterion_assessments=list(criterion_resolution.canonical_assessments),
            criterion_audit=list(criterion_resolution.audit),
            criterion_review_complete=not (
                criterion_resolution.missing
                or criterion_resolution.unknown
                or criterion_resolution.conflicts
            ),
            required_changes=(
                cleaned_required_changes if required_changes is None else required_changes
            ),
            blocker_findings=list(content.blocker_findings),
            hallucination_findings=list(content.hallucination_findings),
            downgraded_from=downgraded_from,
            evidence_resolved=evidence_resolved,
            reviewer_provider_id=reviewer_provider_id,
            reviewer_model_id=reviewer_model_id,
            reviewer_session_id=reviewer_session_id,
            input_digest=input_digest,
            output_digest=output_digest,
        )

    # (1) Infrastructure failure is host-raised; it can never be produced by the model's text.
    if infrastructure_error:
        return build(GateDecision.INFRASTRUCTURE_FAILURE)

    missing = list(criterion_resolution.missing)
    failed = list(criterion_resolution.failed)
    unknown = list(criterion_resolution.unknown)
    conflicts = list(criterion_resolution.conflicts)
    unfaithful = bool(content.hallucination_findings) or not evidence_resolved
    # `cleaned_required_changes` is deliberately NOT a blocker. Operator-approved minimum patch,
    # 2026-07-30: an improvement the reviewer named while passing every criterion is an accept with a
    # note, not a rejection. The old disjunct was the one member of this list with no independently
    # enforced boundary behind it -- every other member is either a criterion result the reviewer
    # itself recorded or a host-computed guard -- and the reviewer had been TOLD, by
    # paper_case_fidelity_reviewer/v2, that such an accept would not be honored, so it pre-complied by
    # returning `revise` instead. Measured across the live corpus: four verdicts where required_changes
    # was the only signal, all with every criterion passed.
    #
    # Nothing else moves. `unfaithful` (hallucination findings or a failed host evidence closure) still
    # forces REJECT, blocker findings still block, and a missing / failed / unknown / conflicting
    # criterion still blocks. The asks now ride along on the accepted outcome so they can be shown to a
    # reader instead of silently discarded.
    accept_blocked = bool(
        missing or failed or unknown or conflicts or content.blocker_findings or unfaithful
    )

    # (2) Earned accept: the model asked for accept AND nothing blocks it. Any improvement it named
    # travels with the accept -- passing while dropping the note would be worse than not passing.
    if content.decision == GateModelDecision.ACCEPT and not accept_blocked:
        return build(GateDecision.ACCEPT, required_changes=cleaned_required_changes)

    # (3) The model claimed accept but something blocks it → downgrade (never a false accept).
    if content.decision == GateModelDecision.ACCEPT and accept_blocked:
        downgraded = GateDecision.REJECT if unfaithful else GateDecision.REVISE
        changes = cleaned_required_changes or [
            *[f"criterion not satisfied: {name}" for name in (missing + failed)],
            *[f"unknown criterion returned: {name!r}" for name in unknown],
            *[f"conflicting duplicate criterion assessments: {name}" for name in conflicts],
        ]
        return build(downgraded, downgraded_from=GateDecision.ACCEPT, required_changes=changes)

    # (4) The model honestly said revise / reject / insufficient_evidence — honored as-is.
    return build(GateDecision(content.decision.value))


def run_gate_with_revise_loop(
    *,
    artifact: T,
    review: Callable[[T], GateOutcome],
    redraft: Callable[[T, GateOutcome], T],
    max_revise_rounds: int = 2,
) -> tuple[T, GateLoopResult]:
    """Review ``artifact``; on ``revise`` re-draft with the required_changes and re-review, bounded.

    Returns the (possibly re-drafted) artifact and a ``GateLoopResult``. If the loop ends still on
    ``revise`` after ``max_revise_rounds`` re-drafts, ``budget_exhausted`` is True and the final
    outcome stays ``revise`` — the caller records the honest ``revision_budget_exhausted`` terminal;
    the kernel never rewrites it to a reject.
    """
    if max_revise_rounds < 0:
        raise ValueError("max_revise_rounds must be >= 0")
    current = artifact
    outcome = review(current)
    rounds = 0
    while outcome.decision == GateDecision.REVISE and rounds < max_revise_rounds:
        current = redraft(current, outcome)
        rounds += 1
        outcome = review(current)
    budget_exhausted = outcome.decision == GateDecision.REVISE and rounds >= max_revise_rounds
    return current, GateLoopResult(
        final_outcome=outcome, rounds_used=rounds, budget_exhausted=budget_exhausted
    )
