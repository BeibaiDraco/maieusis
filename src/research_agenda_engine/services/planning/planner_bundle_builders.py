"""Reusable, side-effect-free constructors for planner returned-artifact bundles.

These builders are the single source of the four planner-outcome shapes
(direct plan / clarification-then-plan / variant rejection / human escalation).
Both the synthetic MCP harness and the ``FakePlannerHost`` compose branch-local
planner artifacts from here so the outcome logic is not duplicated.

This module depends only on schemas, provenance, and the handoff manifest type.
It must not import the coding-agent backend or the MCP dialogue server (that
would create a ``providers -> services -> providers`` import cycle).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from ...enums import ClaimLevel
from ...provenance import stable_hash
from ...schemas.analysis_plan import AnalysisPlan, DatasetInspectionSourceType, PlanDataSource
from ...schemas.planner_run import (
    CodingAgentRunRecord,
    CodingAgentRunStatus,
    CodingAgentRunUsage,
    PlannerReturnedArtifactBundle,
)
from ...schemas.planning_dialogue import (
    BranchDecisionKind,
    BranchRejectionMessage,
    ClarificationRequest,
    DatasetFeasibilityFinding,
    FamilyVariantPlanningEntry,
    FeasibilityStatus,
    HumanEscalationRequest,
    PlanDraftMessage,
    PlannerAssessment,
    VariantAnalysisPlanEntry,
)
from ...schemas.question_family_branch import (
    QuestionFamilyBranch,
    QuestionFamilyBranchEventScope,
    QuestionFamilyInspectionEvidence,
)
from .dataset_planner_packet import (
    DATASET_PLANNER_PROMPT_VERSION,
    DatasetPlannerHandoffManifest,
)


def with_payload_digest(payload: dict[str, Any]) -> dict[str, Any]:
    """Return ``payload`` with a stable ``payload_digest`` over its content."""

    return {
        **payload,
        "payload_digest": stable_hash(
            {
                key: value
                for key, value in payload.items()
                if key not in {"created_at", "payload_digest"}
            }
        ),
    }


def restamp_provenance_digests(data: dict[str, Any]) -> dict[str, Any]:
    """Host-computed provenance digests.

    A spawned coding agent writes only the *logical* content of an artifact
    (findings, decisions, reasons); it must not — and, with no code-execution tool,
    cannot — compute the sha256/``stable_hash`` provenance digests the schemas carry.
    The trusted host recomputes those digest fields deterministically from the agent's
    content when it collects the artifacts, so the agent never fabricates provenance
    and spends no turns hashing. The digests use the same formulas as the bundle
    builders, so re-stamping an already-valid artifact (Synthetic / Manual) is
    idempotent. Returns a new dict; the caller persists it before validation.
    """
    stamped = dict(data)
    # QuestionFamilyInspectionEvidence
    if "source_locator" in stamped and "evidence_id" in stamped and "message_type" not in stamped:
        evidence_id = stamped.get("evidence_id", "")
        stamped["source_digest"] = stable_hash(
            {"source": stamped.get("source_locator", ""), "evidence_id": evidence_id}
        )
        stamped["query_or_command_digest"] = stable_hash({"query": evidence_id})
        stamped["result_digest"] = stable_hash({"finding": stamped.get("finding", "")})
    # Typed planning message (plan draft / rejection / escalation / clarification / finding)
    if "message_type" in stamped and "message_id" in stamped:
        branch_id = stamped.get("branch_id", "")
        message_id = stamped.get("message_id", "")
        stamped["input_digest"] = stable_hash(
            {"branch_id": branch_id, "message_id": message_id, "input": "planner"}
        )
        stamped["output_digest"] = stable_hash(
            {"branch_id": branch_id, "message_id": message_id, "output": "planner"}
        )
        stamped["payload_digest"] = stable_hash(
            {
                key: value
                for key, value in stamped.items()
                if key not in {"created_at", "payload_digest"}
            }
        )
    return stamped


def deterministic_id(branch: QuestionFamilyBranch, label: str) -> str:
    """Deterministic branch-local id used for sessions, run records, and bundles."""

    digest = stable_hash(
        {
            "branch_id": branch.branch_id,
            "question_family_id": branch.question_family_id,
            "label": label,
        }
    )
    return f"synthetic-{label}-{digest[:12]}"


def variant_outcomes(
    branch: QuestionFamilyBranch,
    *,
    decision: BranchDecisionKind,
    evidence_id: str,
    summary: str,
) -> list[FamilyVariantPlanningEntry]:
    return [
        FamilyVariantPlanningEntry(
            variant_id=invariant.variant_id,
            question_seed_id=invariant.question_seed_id,
            decision=decision,
            summary=f"{summary} Variant: {invariant.variant_id}.",
            evidence_ids=[evidence_id],
        )
        for invariant in branch.variant_intent_invariants
    ]


def family_evidence(
    branch: QuestionFamilyBranch,
    *,
    evidence_id: str,
    finding: str,
    source_locator: str,
    inspection_method: str,
    created_by: str,
    limitations: list[str],
    source_type: DatasetInspectionSourceType = DatasetInspectionSourceType.SYNTHETIC_PROBE,
) -> QuestionFamilyInspectionEvidence:
    return QuestionFamilyInspectionEvidence(
        evidence_id=evidence_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        scope=QuestionFamilyBranchEventScope.FAMILY,
        source_type=source_type,
        source_locator=source_locator,
        source_digest=stable_hash({"source": source_locator, "evidence_id": evidence_id}),
        inspection_method=inspection_method,
        finding=finding,
        limitations=list(limitations),
        created_by=created_by,
        query_or_command_digest=stable_hash({"query": evidence_id}),
        result_digest=stable_hash({"finding": finding}),
    )


def planner_message_base(
    branch: QuestionFamilyBranch,
    *,
    message_id: str,
    message_type: str,
    scope: Literal["family", "variant"],
    provider_id: str,
    model_id: str,
    session_id: str,
    prompt_version: str = DATASET_PLANNER_PROMPT_VERSION,
    variant_id: str = "",
    question_seed_id: str = "",
) -> dict[str, Any]:
    return {
        "message_id": message_id,
        "branch_id": branch.branch_id,
        "scope": scope,
        "variant_id": variant_id,
        "question_seed_id": question_seed_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
        "actor_role": "dataset_planner",
        "message_type": message_type,
        "provider_id": provider_id,
        "model_id": model_id,
        "session_id": session_id,
        "prompt_version": prompt_version,
        "input_digest": stable_hash(
            {"branch_id": branch.branch_id, "message_id": message_id, "input": "planner"}
        ),
        "output_digest": stable_hash(
            {"branch_id": branch.branch_id, "message_id": message_id, "output": "planner"}
        ),
    }


def family_clarification(
    branch: QuestionFamilyBranch,
    *,
    message_id: str,
    provider_id: str,
    model_id: str,
    session_id: str,
) -> ClarificationRequest:
    payload = planner_message_base(
        branch,
        message_id=message_id,
        message_type="clarification_request",
        scope="family",
        provider_id=provider_id,
        model_id=model_id,
        session_id=session_id,
    )
    payload.update(
        {
            "construct": "shared family-level scientific meaning",
            "why_ambiguous": (
                "The planner cannot choose between two family-wide interpretations "
                "without owner guidance."
            ),
            "dataset_implication": (
                "The selected interpretation determines which variant-level metadata "
                "bindings remain faithful."
            ),
            "candidate_interpretations": [
                "shared construct is a family-wide planning constraint",
                "shared construct should be split into variant-local meanings",
            ],
            "planner_recommendation": (
                "Resolve the ambiguity once at family scope before variant planning."
            ),
        }
    )
    return ClarificationRequest(**with_payload_digest(payload))


def feasibility_finding(
    branch: QuestionFamilyBranch,
    *,
    message_id: str,
    variant_id: str,
    question_seed_id: str,
    evidence_id: str,
    status: FeasibilityStatus,
    coverage_summary: str,
    impact_on_question: str,
    provider_id: str,
    model_id: str,
    session_id: str,
) -> DatasetFeasibilityFinding:
    payload = planner_message_base(
        branch,
        message_id=message_id,
        message_type="dataset_feasibility_finding",
        scope="variant",
        variant_id=variant_id,
        question_seed_id=question_seed_id,
        provider_id=provider_id,
        model_id=model_id,
        session_id=session_id,
    )
    payload.update(
        {
            "requirement_id": f"{variant_id}-planning-requirement",
            "requirement": "branch-local planning evidence for the variant contrast",
            "status": status,
            "evidence_ids": [evidence_id],
            "coverage_summary": coverage_summary,
            "limitations": ["planning fixture; not live dataset evidence"],
            "impact_on_question": impact_on_question,
        }
    )
    return DatasetFeasibilityFinding(**with_payload_digest(payload))


def plan_draft(
    branch: QuestionFamilyBranch,
    *,
    message_id: str,
    analysis_plan_id: str,
    evidence_id: str,
    summary: str,
    provider_id: str,
    model_id: str,
    session_id: str,
) -> PlanDraftMessage:
    payload = planner_message_base(
        branch,
        message_id=message_id,
        message_type="plan_draft",
        scope="family",
        provider_id=provider_id,
        model_id=model_id,
        session_id=session_id,
    )
    payload.update(
        {
            "analysis_plan_id": analysis_plan_id,
            "summary": summary,
            "unresolved_decisions": [],
            "planner_assessment": PlannerAssessment.SERVES_QUESTION,
            "variant_outcomes": variant_outcomes(
                branch,
                decision=BranchDecisionKind.ACCEPTED,
                evidence_id=evidence_id,
                summary="Evidence supports a non-terminal plan draft.",
            ),
            "variant_analysis_plans": _synthetic_variant_analysis_plans(
                branch,
                analysis_plan_id=analysis_plan_id,
                evidence_id=evidence_id,
            ),
        }
    )
    return PlanDraftMessage(**with_payload_digest(payload))


def _synthetic_variant_analysis_plans(
    branch: QuestionFamilyBranch,
    *,
    analysis_plan_id: str,
    evidence_id: str,
) -> list[VariantAnalysisPlanEntry]:
    """Build detailed fixture plans so synthetic/fake hosts exercise the serious closure.

    These remain explicit planning fixtures; live coding agents author the corresponding content
    from real branch-local evidence under the direct-file contract.
    """

    entries: list[VariantAnalysisPlanEntry] = []
    for variant in branch.variant_intent_invariants:
        invariant = variant.invariant
        plan = AnalysisPlan(
            analysis_plan_id=f"{analysis_plan_id}-{variant.variant_id}",
            branch_id=branch.branch_id,
            question_version_id=variant.question_seed_id,
            refined_question=(
                f"How can the available dataset evaluate {invariant.central_phenomenon} while "
                f"preserving the contrast {invariant.target_contrast}?"
            ),
            scientific_intent_invariant_id=invariant.invariant_id,
            population_and_scope=invariant.population_scope,
            data_sources=[
                PlanDataSource(
                    data_source_id=f"source-{variant.variant_id}",
                    branch_id=branch.branch_id,
                    description="Bounded planning fixture inspected by the dataset planner.",
                    expected_grain="Dataset-specific observational unit established during planning.",
                    required_variables=[],
                    evidence_ids=[evidence_id],
                    limitations=["Synthetic planning fixture; not a scientific result."],
                )
            ],
            unit_of_observation="Dataset-specific observational unit established during planning.",
            unit_of_inference="Independent sampling unit identified before execution.",
            hierarchy_and_dependence=(
                "Preserve the documented nesting and dependence structure in estimation."
            ),
            analysis_strategy=[
                "Construct the variant-specific contrast from source-backed dataset bindings.",
                "Estimate the contrast with dependence-aware validation and sensitivity checks.",
            ],
            candidate_estimands=[
                "Variant-specific descriptive contrast at the documented unit of inference."
            ],
            validation_strategy=(
                "Use held-out or resampled checks appropriate to the documented dependence structure."
            ),
            split_strategy="Define leakage-safe splits before any full scientific execution.",
            diagnostics=["Check coverage, missingness, and stability across documented strata."],
            negative_controls=[
                "Use a scientifically irrelevant contrast where the fixture permits."
            ],
            positive_controls=[
                "Recover a documented structural signal before interpreting failure."
            ],
            alternative_explanations=[
                "Observed differences may reflect sampling or coverage imbalance.",
                "Observed differences may reflect an imperfect construct operationalization.",
            ],
            predicted_result_patterns=[
                invariant.positive_result_meaning,
                invariant.negative_result_meaning,
            ],
            claim_ceiling=ClaimLevel.DESCRIPTIVE,
            interpretation_limits=[
                "Planning evidence does not constitute a scientific result or execution authorization."
            ],
            resource_estimate="Bounded planning estimate; execution resources remain uncommitted.",
            unresolved_decisions=[],
            why_plan_serves_question=(
                f"The plan preserves {invariant.central_phenomenon} and the intended contrast "
                f"{invariant.target_contrast}."
            ),
            evidence_ids=[evidence_id],
        )
        entries.append(
            VariantAnalysisPlanEntry(
                variant_id=variant.variant_id,
                question_seed_id=variant.question_seed_id,
                analysis_plan=plan,
            )
        )
    return entries


def rejection(
    branch: QuestionFamilyBranch,
    *,
    message_id: str,
    evidence_id: str,
    provider_id: str,
    model_id: str,
    session_id: str,
) -> BranchRejectionMessage:
    payload = planner_message_base(
        branch,
        message_id=message_id,
        message_type="branch_rejection",
        scope="family",
        provider_id=provider_id,
        model_id=model_id,
        session_id=session_id,
    )
    payload.update(
        {
            "decision": BranchDecisionKind.REJECTED_INSUFFICIENT_EVIDENCE,
            "reason": (
                "A faithful plan would require dataset bindings absent from branch-local "
                "planning evidence."
            ),
            "blocking_evidence_ids": [evidence_id],
            "alternatives_for_future_data": [
                "revisit if future metadata exposes the required planning bindings"
            ],
            "variant_outcomes": variant_outcomes(
                branch,
                decision=BranchDecisionKind.REJECTED_INSUFFICIENT_EVIDENCE,
                evidence_id=evidence_id,
                summary=(
                    "Available planning evidence is insufficient to establish dataset fit for "
                    "this variant."
                ),
            ),
        }
    )
    return BranchRejectionMessage(**with_payload_digest(payload))


def human_escalation(
    branch: QuestionFamilyBranch,
    *,
    message_id: str,
    evidence_id: str,
    provider_id: str,
    model_id: str,
    session_id: str,
) -> HumanEscalationRequest:
    payload = planner_message_base(
        branch,
        message_id=message_id,
        message_type="human_escalation_request",
        scope="family",
        provider_id=provider_id,
        model_id=model_id,
        session_id=session_id,
    )
    payload.update(
        {
            "decision_needed": (
                "Choose which scientifically meaningful family interpretation should govern "
                "variant planning."
            ),
            "why_agents_cannot_resolve": (
                "Evidence leaves incompatible interpretations that both preserve parts of the "
                "family intent."
            ),
            "options": [
                "plan using the shared interpretation",
                "split interpretation by variant before planning",
            ],
            "consequences": [
                "shared interpretation keeps the family unified",
                "variant-local interpretation may require a material revision",
            ],
            "variant_outcomes": variant_outcomes(
                branch,
                decision=BranchDecisionKind.HUMAN_ESCALATION,
                evidence_id=evidence_id,
                summary="Evidence requires human scientific interpretation.",
            ),
        }
    )
    return HumanEscalationRequest(**with_payload_digest(payload))


def real_run_record_id(branch: QuestionFamilyBranch) -> str:
    """Non-synthetic run-record id for a real subprocess spawn (drops the ``synthetic-`` prefix).

    ``deterministic_id`` stamps ``synthetic-…`` on every id, which is honest for the in-process
    fakes but wrong for a real ``claude -p`` / ``codex exec`` run. A real host passes this id so a
    real run trace is not mislabeled synthetic; Fake/Synthetic keep the ``synthetic-`` id.
    """
    digest = stable_hash(
        {
            "branch_id": branch.branch_id,
            "question_family_id": branch.question_family_id,
            "label": "run-record",
        }
    )
    return f"coding-agent-run-record-{digest[:12]}"


def run_record(
    branch: QuestionFamilyBranch,
    handoff: DatasetPlannerHandoffManifest,
    *,
    run_id: str,
    status: CodingAgentRunStatus,
    transcript_path: Path,
    transcript_digest: str,
    planner_adapter: str,
    planner_identity: str,
    prompt_version: str = DATASET_PLANNER_PROMPT_VERSION,
    run_record_id: str | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    usage: CodingAgentRunUsage | None = None,
    planner_model_id: str = "",
    planner_reasoning_effort: str = "",
    planner_cli_version: str = "",
    planner_budget_policy: str = "",
    planner_timeout_seconds: int | None = None,
    source_tree_before_digest: str | None = None,
    source_tree_after_digest: str | None = None,
    workspace_manifest_before_digest: str | None = None,
    workspace_manifest_after_digest: str | None = None,
    attempt_count: int = 1,
    attempt_audit_digest: str = "",
    runner_warnings: list[str] | None = None,
    source_tree_mutation_detected: bool = False,
    blocked_actions_checked: list[str] | None = None,
) -> CodingAgentRunRecord:
    # Real subprocess runners witness the spawn, so they pass the actual wall-clock
    # start/end + captured token/USD usage; in-process runners (Synthetic / Manual) omit them and
    # the honest placeholder (now(); ended==started on success) is used, keeping their bytes stable.
    resolved_started_at = started_at if started_at is not None else datetime.now(UTC)
    if ended_at is not None:
        resolved_ended_at: datetime | None = ended_at
    else:
        resolved_ended_at = resolved_started_at if status == CodingAgentRunStatus.RETURNED else None
    # In-process runners (Synthetic / Manual) launch nothing, so the source tree is
    # trivially unchanged and the placeholder digest is honest. A real subprocess runner
    # measures the actual Maieusis-repo digest before/after the spawn and passes
    # it through here so the run trace records what was really observed.
    unchanged = stable_hash({"source_tree": "unchanged"})
    before_digest = source_tree_before_digest if source_tree_before_digest else unchanged
    after_digest = source_tree_after_digest if source_tree_after_digest else unchanged
    return CodingAgentRunRecord(
        run_record_id=run_record_id if run_record_id else deterministic_id(branch, "run-record"),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        planner_adapter=planner_adapter,
        planner_identity=planner_identity,
        prompt_version=prompt_version,
        packet_path=handoff.packet_path,
        task_path=handoff.task_path,
        handoff_digest=handoff.packet_digest,
        status=status,
        started_at=resolved_started_at,
        ended_at=resolved_ended_at,
        transcript_path=str(transcript_path),
        transcript_digest=transcript_digest,
        workspace_manifest_before_digest=workspace_manifest_before_digest or "",
        workspace_manifest_after_digest=workspace_manifest_after_digest or "",
        source_tree_before_digest=before_digest,
        source_tree_after_digest=after_digest,
        source_tree_mutation_detected=source_tree_mutation_detected,
        usage=usage,
        planner_model_id=planner_model_id,
        planner_reasoning_effort=planner_reasoning_effort,
        planner_cli_version=planner_cli_version,
        planner_budget_policy=planner_budget_policy,
        planner_timeout_seconds=planner_timeout_seconds,
        attempt_count=attempt_count,
        attempt_audit_digest=attempt_audit_digest,
        runner_warnings=runner_warnings or [],
        blocked_actions_checked=blocked_actions_checked
        or [
            "no live API call",
            "no live dataset access",
            "no downstream bridge artifact",
            "no execution artifact",
            "branch planner workspace writes only",
        ],
    )


def returned_bundle(
    branch: QuestionFamilyBranch,
    handoff: DatasetPlannerHandoffManifest,
    *,
    run_id: str,
    bundle_id: str,
    workspace: Path,
    run_record_path: Path,
    evidence_paths: list[Path],
    dialogue_paths: list[Path],
    plan_draft_paths: list[Path],
    rejection_paths: list[Path],
    host_repair_notes: list[str] | None = None,
    presentation_repair_ledger_path: Path | None = None,
    presentation_repair_raw_paths: list[Path] | None = None,
) -> PlannerReturnedArtifactBundle:
    return PlannerReturnedArtifactBundle(
        bundle_id=bundle_id,
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        planner_workspace=str(workspace),
        run_trace_path=str(run_record_path),
        evidence_paths=[str(path) for path in evidence_paths],
        dialogue_paths=[str(path) for path in dialogue_paths],
        plan_draft_paths=[str(path) for path in plan_draft_paths],
        rejection_paths=[str(path) for path in rejection_paths],
        validation_report_path=str(Path(handoff.packet_path).parent / "validation_report.yaml"),
        host_repair_notes=host_repair_notes or [],
        presentation_repair_ledger_path=(
            str(presentation_repair_ledger_path) if presentation_repair_ledger_path else ""
        ),
        presentation_repair_raw_paths=[str(path) for path in presentation_repair_raw_paths or []],
    )
