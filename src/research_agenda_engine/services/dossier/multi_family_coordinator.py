from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import field_validator

from ...assets import resolve_asset
from ...config import load_runtime_env
from ...io import dump_data, load_data, load_model
from ...provenance import stable_hash
from ...providers.scientific_agents import (
    AnthropicScientificAgentProvider,
    OpenAIScientificAgentProvider,
    ScientificAgentProvider,
    ScientificAgentSessionSnapshot,
)
from ...schemas.family_failure import sanitize_family_failure_text
from ...schemas.generic_dossier import GenericEndUserDossierManifest
from ...schemas.generic_scientific_source import DatasetGroundingLevel
from ...schemas.multi_family_dossier import (
    DevelopmentModelSurrogateReview,
    DevelopmentSurrogateFamilyOutcomeArtifact,
    DevelopmentSurrogateFamilyOutcomeInput,
    DevelopmentSurrogateFamilyVariantInput,
    FamilyDossierOutputRecord,
    FamilyDossierStatus,
    FamilyOutcomeAuditSidecar,
    MultiFamilyCoordinationMode,
    MultiFamilyDossierManifest,
    ReviewAuthority,
)
from ...schemas.question_family import QuestionFamily, QuestionFamilyShortlistManifest
from ...schemas.question_family_branch import (
    QuestionFamilyBranch,
    QuestionFamilyBranchEvent,
    QuestionFamilyBranchEventType,
    QuestionFamilyInspectionEvidence,
)
from ...schemas.scientific_dossier import EndUserScientificDossierManifest
from ..orchestration import QuestionFamilyBranchManager
from ..planning.planner_boundaries import find_planner_boundary_violations

EndUserDossierManifest = EndUserScientificDossierManifest | GenericEndUserDossierManifest


class _DevelopmentSurrogateArtifactModelOutput(DevelopmentSurrogateFamilyOutcomeArtifact):
    """Generation-boundary mirror: artifact_id / branch_id / question_family_id are
    code-owned echo-ids tolerated when empty (the coordinator stamps them from the branch);
    decision_summary is genuine model content and remains fail-closed. NEVER persisted —
    the coordinator rebuilds the strict artifact, re-running every strict validator; the
    transcript output digest stays bound to this parsed payload (what the model said)."""

    artifact_id: str = ""
    branch_id: str = ""
    question_family_id: str = ""

    @field_validator("decision_summary")
    @classmethod
    def require_text(cls, value: str) -> str:
        # Same-name override: echo-ids dropped from the non-empty rule.
        value = value.strip()
        if not value:
            raise ValueError("development surrogate artifact fields must be non-empty")
        return value


R5_M1B_DEFAULT_RUN_ID = "r5-m1b-parallel-family-dossier-coordination"
DEVELOPMENT_OUTCOME_DOSSIER_WORKSPACE = "development_outcome_dossier"
DEVELOPMENT_FAMILY_OUTCOME_SURROGATE_PROMPT_VERSION = "development_family_outcome_surrogate/v1"

_SENSITIVE_REPORT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "credential",
        re.compile(
            r"\b(?:api[_ -]?key|authorization|bearer)\s*[:=]\s*\S+|"
            r"\bsk-[A-Za-z0-9_-]{12,}\b",
            re.I,
        ),
    ),
    (
        "provider request id",
        re.compile(
            r"\brequest[_ -]?id\s*[:=]\s*\S+|\breq_[A-Za-z0-9_-]+\b",
            re.I,
        ),
    ),
    (
        "local absolute path",
        re.compile(r"(?:^|\s)/(?:Users|private/tmp|tmp|var/folders)/\S+", re.I),
    ),
    (
        "serialized authority",
        re.compile(
            r"\b(?:execution_authorized|bridge_created|questioncard_created|"
            r"analysiscontract_created)\s*[:=]\s*(?:true|yes|1)\b",
            re.I,
        ),
    ),
    (
        "serialized result field",
        re.compile(
            r"\b(?:confirmation_outcomes?|confirmatory_results?|held[_ -]?out_results?)"
            r"\s*[:=]",
            re.I,
        ),
    ),
)

_PUBLIC_PLAN_TEXT_REDACTIONS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\breq_[A-Za-z0-9_-]+\b", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b", re.I),
    re.compile(r"\b(?:api[_ -]?key|authorization|bearer)\s*[:=]\s*\S+", re.I),
    re.compile(r"(?:^|\s)/(?:Users|private/tmp|tmp|var/folders)/\S+", re.I),
    re.compile(r"\bqfamily-branch-[A-Za-z0-9-]+\b", re.I),
    re.compile(r"\bqvariant-[A-Za-z0-9-]+\b", re.I),
    re.compile(r"\bqseed-[A-Za-z0-9-]+\b", re.I),
    re.compile(r"\b(?:analysis-plan|evidence|message|context)-[A-Za-z0-9-]+\b", re.I),
    re.compile(r"\b(?:owner|planner|reviewer)-session-[A-Za-z0-9-]+\b", re.I),
)

_PLAN_SCALAR_FIELDS: tuple[tuple[str, str], ...] = (
    ("refined_question", "Refined question"),
    ("population_and_scope", "Population and scope"),
    ("unit_of_observation", "Unit of observation"),
    ("unit_of_inference", "Unit of inference"),
    ("hierarchy_and_dependence", "Hierarchy and dependence"),
    ("validation_strategy", "Validation strategy"),
    ("split_strategy", "Split strategy"),
    ("claim_ceiling", "Planner-stated claim ceiling (not yet schema-validated)"),
    ("resource_estimate", "Resource estimate"),
    ("why_plan_serves_question", "Why this plan serves the question"),
)

_PLAN_LIST_FIELDS: tuple[tuple[str, str], ...] = (
    ("analysis_strategy", "Analysis strategy"),
    ("candidate_estimands", "Candidate estimands"),
    ("diagnostics", "Diagnostics"),
    ("negative_controls", "Negative controls"),
    ("positive_controls", "Positive controls"),
    ("alternative_explanations", "Alternative explanations"),
    ("predicted_result_patterns", "Predicted result patterns"),
    ("interpretation_limits", "Interpretation limits"),
    ("required_new_skills", "Required new skills"),
    ("unresolved_decisions", "Unresolved decisions"),
)


def load_development_family_outcome_surrogate_prompt(
    prompt_version: str = DEVELOPMENT_FAMILY_OUTCOME_SURROGATE_PROMPT_VERSION,
) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def build_development_family_outcome_surrogate_provider_from_env(
    *,
    provider: Literal["openai", "anthropic"] | None = None,
    allow_pro_model: bool = False,
    project_root: str | Path | None = None,
) -> ScientificAgentProvider:
    """Build a live development-only family outcome surrogate provider."""

    load_runtime_env(project_root=Path(project_root) if project_root is not None else Path.cwd())
    env_provider = os.getenv("MAIEUSIS_R5_DEVELOPMENT_SURROGATE_PROVIDER")
    provider_name = (provider if provider is not None else env_provider or "").strip().lower()
    if not provider_name:
        if os.getenv("OPENAI_API_KEY"):
            provider_name = "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            provider_name = "anthropic"
        else:
            raise ValueError(
                "Set MAIEUSIS_R5_DEVELOPMENT_SURROGATE_PROVIDER plus provider credentials/model, "
                "or set OPENAI_API_KEY/OPENAI_MODEL or ANTHROPIC_API_KEY/ANTHROPIC_MODEL."
            )

    system_prompt = load_development_family_outcome_surrogate_prompt()
    if provider_name == "openai":
        model = (
            os.getenv("MAIEUSIS_R5_DEVELOPMENT_SURROGATE_MODEL")
            or os.getenv("MAIEUSIS_R5_DEVELOPMENT_SURROGATE_OPENAI_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-5.4"
        )
        return OpenAIScientificAgentProvider(
            model=model,
            allow_pro_model=allow_pro_model,
            system_prompt=system_prompt,
        )
    if provider_name == "anthropic":
        model = (
            os.getenv("MAIEUSIS_R5_DEVELOPMENT_SURROGATE_MODEL")
            or os.getenv("MAIEUSIS_R5_DEVELOPMENT_SURROGATE_ANTHROPIC_MODEL")
            or os.getenv("ANTHROPIC_MODEL")
            or "claude-opus-4-8"
        )
        return AnthropicScientificAgentProvider(
            model=model,
            allow_pro_model=allow_pro_model,
            system_prompt=system_prompt,
        )
    raise ValueError(f"Unsupported R5 development surrogate provider: {provider_name}")


def import_end_user_dossier_record(
    *,
    repository_root: str | Path,
    run_root: str | Path,
    manifest_path: str | Path,
    family_title: str,
) -> FamilyDossierOutputRecord:
    """Import an existing branch-local end-user dossier manifest as one aggregate record."""

    repository_root = Path(repository_root)
    run_root = Path(run_root)
    manifest_path = _resolve_path(manifest_path, repository_root=repository_root)
    end_user_manifest = _load_end_user_manifest(manifest_path)
    manager = QuestionFamilyBranchManager(run_root, run_id=end_user_manifest.run_id)
    branch = manager.load_branch(end_user_manifest.branch_id)
    _validate_manifest_identity(branch, end_user_manifest)
    _validate_manifest_files(repository_root, end_user_manifest)
    _validate_branch_local_paths(end_user_manifest)
    dossier_event = _find_end_user_dossier_event(branch, end_user_manifest)
    human_gate_event = _latest_human_review_gate_event(branch)
    human_review_authority = _human_review_authority_for_gate(human_gate_event)
    if human_review_authority != ReviewAuthority.REAL_HUMAN_EXPERT:
        raise ValueError("completed dossier import requires current real human review gate")
    return FamilyDossierOutputRecord(
        record_id=_record_id(end_user_manifest.question_family_id, end_user_manifest.branch_id),
        question_family_id=end_user_manifest.question_family_id,
        branch_id=end_user_manifest.branch_id,
        context_id=end_user_manifest.context_id,
        owner_session_id=end_user_manifest.owner_session_id,
        family_title=family_title,
        variant_ids=list(branch.active_variant_ids),
        status=FamilyDossierStatus.COMPLETED_DOSSIER_STACK,
        branch_state=branch.state,
        branch_event_count=len(branch.events),
        # The imported manifest and current human gate are matched to replayed branch events above.
        replay_verified=True,
        branch_event_id=end_user_manifest.branch_event_id,
        branch_event_sequence=dossier_event.sequence,
        human_review_gate_event_id=human_gate_event.event_id if human_gate_event else "",
        human_review_gate_event_sequence=human_gate_event.sequence if human_gate_event else None,
        human_review_gate_artifact_id=human_gate_event.payload.artifact_id
        if human_gate_event
        else "",
        human_review_gate_artifact_digest=human_gate_event.payload.artifact_digest
        if human_gate_event
        else "",
        end_user_dossier_manifest_id=end_user_manifest.end_user_dossier_manifest_id,
        end_user_dossier_manifest_path=_display_path(manifest_path, repository_root),
        end_user_dossier_path=end_user_manifest.end_user_dossier_path,
        end_user_dossier_digest=end_user_manifest.end_user_dossier_digest,
        end_user_dossier_artifact_path=end_user_manifest.end_user_dossier_artifact_path,
        end_user_dossier_artifact_digest=end_user_manifest.end_user_dossier_artifact_digest,
        audit_sidecar_path=end_user_manifest.audit_sidecar_path,
        audit_sidecar_digest=end_user_manifest.audit_sidecar_digest,
        provider_id=end_user_manifest.provider_id,
        model_id=end_user_manifest.model_id,
        prompt_version=end_user_manifest.prompt_version,
        session_id=end_user_manifest.session_id,
        input_digest=end_user_manifest.input_digest,
        output_digest=end_user_manifest.output_digest,
        human_review_authority=human_review_authority,
        human_review_status="accepted_for_dossier",
        dataset_grounding_level=_infer_completed_dataset_grounding_level(branch),
        human_review_imported=human_review_authority == ReviewAuthority.REAL_HUMAN_EXPERT,
        allows_dossier_generation=human_review_authority == ReviewAuthority.REAL_HUMAN_EXPERT,
        final_dossier_created=getattr(end_user_manifest, "final_dossier_created", True),
        planning_only=end_user_manifest.planning_only,
        non_terminal=end_user_manifest.non_terminal,
        contract_eligible=end_user_manifest.contract_eligible,
        execution_authorized=end_user_manifest.execution_authorized,
        bridge_created=end_user_manifest.bridge_created,
        questioncard_created=end_user_manifest.questioncard_created,
        analysiscontract_created=end_user_manifest.analysiscontract_created,
        result_values_persisted=end_user_manifest.result_values_persisted,
    )


def _infer_completed_dataset_grounding_level(
    branch: QuestionFamilyBranch,
) -> DatasetGroundingLevel:
    """Infer the strongest completed-record planning evidence level from branch history."""

    provenance_text = " ".join(
        [
            *(event.payload.provider_id for event in branch.events),
            *(event.payload.model_id for event in branch.events),
            *(event.payload.session_id for event in branch.events),
            *(event.payload.prompt_version for event in branch.events),
            *(event.payload.planning_message_type for event in branch.events),
            *(event.payload.evidence_id for event in branch.events),
            *(event.payload.artifact_id for event in branch.events),
            *(evidence.evidence_id for evidence in branch.inspection_evidence),
            *(evidence.source_locator for evidence in branch.inspection_evidence),
            *(evidence.inspection_method for evidence in branch.inspection_evidence),
            *(evidence.finding for evidence in branch.inspection_evidence),
        ]
    ).lower()
    if "full-local" in provenance_text or "full_local_structural" in provenance_text:
        return DatasetGroundingLevel.FULL_LOCAL_STRUCTURAL_AVAILABLE
    if "sample" in provenance_text:
        return DatasetGroundingLevel.SAMPLE_INSPECTED
    if "schema" in provenance_text or "metadata" in provenance_text:
        return DatasetGroundingLevel.SCHEMA_METADATA_INSPECTED
    return DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY


def _load_end_user_manifest(manifest_path: Path) -> EndUserDossierManifest:
    try:
        return load_model(manifest_path, EndUserScientificDossierManifest)
    except Exception:
        return load_model(manifest_path, GenericEndUserDossierManifest)


def build_queued_family_record(
    *,
    branch: QuestionFamilyBranch,
    family_title: str,
    status: FamilyDossierStatus = FamilyDossierStatus.QUEUED,
    blockers: Iterable[str] = (),
    outcome_markdown_path: str = "",
    outcome_audit_path: str = "",
    human_review_authority: ReviewAuthority = ReviewAuthority.MISSING,
) -> FamilyDossierOutputRecord:
    if status == FamilyDossierStatus.COMPLETED_DOSSIER_STACK:
        raise ValueError("queued family helper cannot create completed records")
    return FamilyDossierOutputRecord(
        record_id=_record_id(branch.question_family_id, branch.branch_id),
        question_family_id=branch.question_family_id,
        branch_id=branch.branch_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        family_title=family_title,
        variant_ids=list(branch.active_variant_ids),
        status=status,
        branch_state=branch.state,
        branch_event_count=len(branch.events),
        replay_verified=True,
        blockers=list(blockers),
        outcome_markdown_path=outcome_markdown_path,
        outcome_audit_path=outcome_audit_path,
        human_review_authority=human_review_authority,
    )


def write_development_outcome_dossier(
    *,
    output_root: str | Path,
    run_id: str,
    branch: QuestionFamilyBranch,
    family_title: str,
    status: FamilyDossierStatus,
    blockers: Iterable[str],
    human_review_authority: ReviewAuthority = ReviewAuthority.MISSING,
) -> FamilyDossierOutputRecord:
    if status == FamilyDossierStatus.COMPLETED_DOSSIER_STACK:
        raise ValueError("development outcome writer cannot create completed dossier records")
    if human_review_authority == ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE:
        raise ValueError(
            "use write_development_model_surrogate_outcome_dossier for surrogate authority"
        )
    blocker_list = [
        sanitize_family_failure_text(blocker.strip()) for blocker in blockers if blocker.strip()
    ]
    if not blocker_list:
        raise ValueError("development outcome dossier requires blockers")
    workspace = (
        Path(output_root)
        / run_id
        / "branches"
        / branch.branch_id
        / "planner"
        / DEVELOPMENT_OUTCOME_DOSSIER_WORKSPACE
    )
    workspace.mkdir(parents=True, exist_ok=True)
    outcome_path = workspace / "outcome.md"
    audit_path = workspace / "outcome_audit.yaml"
    retained_plan_lines = _safe_retained_plan_markdown(
        output_root=Path(output_root),
        run_id=run_id,
        branch=branch,
    )
    markdown = _render_development_outcome_markdown(
        branch=branch,
        family_title=family_title,
        status=status,
        blockers=blocker_list,
        retained_plan_lines=retained_plan_lines,
    )
    outcome_path.write_text(markdown, encoding="utf-8")
    audit_sidecar = FamilyOutcomeAuditSidecar(
        audit_sidecar_id=_outcome_sidecar_id(branch.question_family_id, branch.branch_id),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        status=status,
        outcome_markdown_path=outcome_path.as_posix(),
        outcome_markdown_digest=stable_hash(markdown),
        blockers=blocker_list,
        human_review_authority=human_review_authority,
    )
    dump_data(audit_sidecar, audit_path)
    return build_queued_family_record(
        branch=branch,
        family_title=family_title,
        status=status,
        blockers=blocker_list,
        outcome_markdown_path=outcome_path.as_posix(),
        outcome_audit_path=audit_path.as_posix(),
        human_review_authority=human_review_authority,
    )


def write_development_model_surrogate_outcome_dossier(
    *,
    output_root: str | Path,
    run_id: str,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    blockers: Iterable[str],
    surrogate_provider: ScientificAgentProvider,
) -> FamilyDossierOutputRecord:
    """Write a branch-local development-only model surrogate outcome dossier."""

    if family.question_family_id != branch.question_family_id:
        raise ValueError("development surrogate family does not match branch")
    if family.context_id != branch.context_id:
        raise ValueError("development surrogate family does not match branch context")
    blocker_list = [blocker.strip() for blocker in blockers if blocker.strip()]
    if not blocker_list:
        raise ValueError("development surrogate outcome dossier requires blockers")

    workspace = (
        Path(output_root)
        / run_id
        / "branches"
        / branch.branch_id
        / "planner"
        / DEVELOPMENT_OUTCOME_DOSSIER_WORKSPACE
    )
    workspace.mkdir(parents=True, exist_ok=True)

    surrogate_input = _build_development_surrogate_input(
        run_id=run_id,
        branch=branch,
        family=family,
        blockers=blocker_list,
    )
    session_id = _development_surrogate_session_id(
        run_id=run_id,
        branch=branch,
        provider=surrogate_provider,
    )
    session = surrogate_provider.start_session(
        branch_id=branch.branch_id,
        session_id=session_id,
        prompt_version=DEVELOPMENT_FAMILY_OUTCOME_SURROGATE_PROMPT_VERSION,
    )
    model_artifact = session.send(surrogate_input, _DevelopmentSurrogateArtifactModelOutput)
    # A non-empty echo of another family stays an honest drift failure; an empty echo is
    # "no claim" and receives the code-owned value in the strict rebuild below.
    if (
        model_artifact.question_family_id
        and model_artifact.question_family_id != branch.question_family_id
    ):
        raise ValueError("development surrogate output references another family")
    artifact = DevelopmentSurrogateFamilyOutcomeArtifact.model_validate(
        {
            **model_artifact.model_dump(mode="python"),
            "artifact_id": model_artifact.artifact_id.strip()
            or f"development-family-outcome-{branch.branch_id}",
            "branch_id": branch.branch_id,
            "question_family_id": branch.question_family_id,
        }
    )
    _validate_development_surrogate_text_fields(artifact)

    session_snapshot = session.snapshot()
    if not session_snapshot.transcript:
        raise ValueError("development surrogate session returned no transcript")
    transcript_record = session_snapshot.transcript[-1]
    if transcript_record.input_digest != stable_hash(surrogate_input.model_dump(mode="json")):
        raise ValueError("development surrogate transcript input digest mismatch")
    # DP-6: the transcript output digest binds what the MODEL said (the parsed mirror);
    # the persisted-artifact digest below binds the code-stamped strict rebuild.
    if transcript_record.output_digest != stable_hash(model_artifact.model_dump(mode="json")):
        raise ValueError("development surrogate transcript output digest mismatch")

    input_path = workspace / "surrogate_input.yaml"
    markdown_path = workspace / "outcome.md"
    artifact_path = workspace / "surrogate_artifact.yaml"
    snapshot_path = workspace / "surrogate_session_snapshot.yaml"
    audit_path = workspace / "outcome_audit.yaml"

    dump_data(surrogate_input, input_path)
    markdown_path.write_text(artifact.public_markdown, encoding="utf-8")
    dump_data(artifact, artifact_path)
    dump_data(session_snapshot, snapshot_path)

    input_digest = stable_hash(surrogate_input.model_dump(mode="json"))
    markdown_digest = stable_hash(artifact.public_markdown)
    artifact_digest = stable_hash(artifact.model_dump(mode="json"))
    snapshot_digest = stable_hash(session_snapshot.model_dump(mode="json"))

    surrogate_review = DevelopmentModelSurrogateReview(
        provider_id=transcript_record.provider_id,
        model_id=transcript_record.model_id,
        prompt_version=transcript_record.prompt_version,
        session_id=transcript_record.session_id,
        input_digest=transcript_record.input_digest,
        output_digest=transcript_record.output_digest,
        decision_summary=artifact.decision_summary,
    )
    audit_sidecar = FamilyOutcomeAuditSidecar(
        audit_sidecar_id=_outcome_sidecar_id(branch.question_family_id, branch.branch_id),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        status=artifact.outcome_status,
        outcome_markdown_path=markdown_path.as_posix(),
        outcome_markdown_digest=markdown_digest,
        blockers=artifact.blockers,
        human_review_authority=ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE,
        development_surrogate_review=surrogate_review,
        development_surrogate_input_path=input_path.as_posix(),
        development_surrogate_artifact_path=artifact_path.as_posix(),
        development_surrogate_session_snapshot_path=snapshot_path.as_posix(),
        development_surrogate_input_digest=input_digest,
        development_surrogate_artifact_digest=artifact_digest,
        development_surrogate_session_snapshot_digest=snapshot_digest,
    )
    dump_data(audit_sidecar, audit_path)

    return FamilyDossierOutputRecord(
        record_id=_record_id(branch.question_family_id, branch.branch_id),
        question_family_id=branch.question_family_id,
        branch_id=branch.branch_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        family_title=family.title,
        variant_ids=list(branch.active_variant_ids),
        status=artifact.outcome_status,
        branch_state=branch.state,
        branch_event_count=len(branch.events),
        replay_verified=False,
        provider_id=transcript_record.provider_id,
        model_id=transcript_record.model_id,
        prompt_version=transcript_record.prompt_version,
        session_id=transcript_record.session_id,
        input_digest=transcript_record.input_digest,
        output_digest=transcript_record.output_digest,
        human_review_authority=ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE,
        blockers=artifact.blockers,
        development_surrogate_review=surrogate_review,
        outcome_markdown_path=markdown_path.as_posix(),
        outcome_audit_path=audit_path.as_posix(),
        development_surrogate_input_path=input_path.as_posix(),
        development_surrogate_artifact_path=artifact_path.as_posix(),
        development_surrogate_session_snapshot_path=snapshot_path.as_posix(),
        development_surrogate_input_digest=input_digest,
        development_surrogate_artifact_digest=artifact_digest,
        development_surrogate_session_snapshot_digest=snapshot_digest,
    )


def build_multi_family_dossier_manifest(
    *,
    run_id: str,
    shortlist: QuestionFamilyShortlistManifest,
    records: list[FamilyDossierOutputRecord],
    coordination_mode: MultiFamilyCoordinationMode,
    max_parallel_family_workers: int = 2,
    aggregate_report_path: str = "",
    parallel_run_report_path: str = "",
) -> MultiFamilyDossierManifest:
    return MultiFamilyDossierManifest(
        aggregate_manifest_id=_aggregate_manifest_id(run_id, records),
        run_id=run_id,
        shortlist_id=shortlist.shortlist_id,
        context_id=shortlist.context_id,
        coordination_mode=coordination_mode,
        max_parallel_family_workers=max_parallel_family_workers,
        shortlisted_family_ids=[
            shortlisted.family.question_family_id for shortlisted in shortlist.shortlisted
        ],
        records=records,
        aggregate_report_path=aggregate_report_path,
        parallel_run_report_path=parallel_run_report_path,
    )


def render_aggregate_report(manifest: MultiFamilyDossierManifest) -> str:
    lines = [
        "# R5 Parallel Family Dossier Status",
        "",
        "This report is a planning-only coordination view. It summarizes branch-local "
        "dossier status without authorizing downstream operational conversion.",
        "",
        f"- Run: `{manifest.run_id}`",
        f"- Shortlist: `{manifest.shortlist_id}`",
        f"- Context: `{manifest.context_id}`",
        f"- Coordination mode: `{manifest.coordination_mode.value}`",
        f"- Max parallel family workers: `{manifest.max_parallel_family_workers}`",
        f"- Families: `{len(manifest.records)}`",
        f"- Completed dossier stacks: `{manifest.completed_family_count}`",
        f"- Non-completed / development outcomes: "
        f"`{len(manifest.records) - manifest.completed_family_count}`",
        "",
        "Surrogate authority never imports human review and never unlocks serious dossier "
        "authority, downstream operational conversion, or scientific finding claims.",
        "",
        "| Family | Status | Authority | Human Review | Dataset Grounding | Public Markdown | Audit Sidecar | Blockers |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for record in manifest.records:
        public_path = _aggregate_report_artifact_path(
            record.end_user_dossier_path or record.outcome_markdown_path or "",
            run_id=manifest.run_id,
        )
        audit_path = _aggregate_report_artifact_path(
            record.audit_sidecar_path or record.outcome_audit_path or "",
            run_id=manifest.run_id,
        )
        blockers = (
            "; ".join(sanitize_family_failure_text(blocker) for blocker in record.blockers)
            if record.blockers
            else ""
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{record.question_family_id}`",
                    f"`{record.status.value}`",
                    f"`{record.human_review_authority.value}`",
                    f"`{record.human_review_status}`",
                    f"`{record.dataset_grounding_level.value}`",
                    _markdown_cell(public_path),
                    _markdown_cell(audit_path),
                    _markdown_cell(blockers),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "All entries remain non-terminal R5 planning artifacts. Downstream operational "
            "conversion surfaces remain inactive.",
        ]
    )
    report = "\n".join(lines) + "\n"
    errors = validate_aggregate_report_text(report)
    if errors:
        raise ValueError("aggregate report contains forbidden terms: " + "; ".join(errors))
    return report


def render_parallel_run_report(
    manifest: MultiFamilyDossierManifest,
    *,
    started_at: datetime,
    finished_at: datetime,
    subagent_count: int,
    api_agent_count: int,
    notes: Iterable[str] = (),
) -> str:
    elapsed = max(0.0, (finished_at - started_at).total_seconds())
    lines = [
        "# R5-M1B Parallel Implementation And Run Report",
        "",
        f"- Started at: `{started_at.isoformat()}`",
        f"- Finished at: `{finished_at.isoformat()}`",
        f"- Elapsed seconds: `{elapsed:.1f}`",
        f"- Subagents used: `{subagent_count}`",
        f"- API agents used: `{api_agent_count}`",
        f"- Max parallel family workers: `{manifest.max_parallel_family_workers}`",
        f"- Coordination mode: `{manifest.coordination_mode.value}`",
        "",
        "## Queue Strategy",
        "",
        "Families are represented as independent branch-local records. Completed R5-010D "
        "outputs are imported read-only; unfinished families remain queued or blocked "
        "until their own isolated owner, planner, review, and dossier artifacts exist.",
        "",
        "Development-model surrogate records are development testing artifacts only. They do "
        "not import human review, unlock dossier generation, or create scientific findings.",
        "",
        "## Family Batches",
        "",
    ]
    for index, record in enumerate(manifest.records, start=1):
        lines.append(
            f"{index}. `{record.question_family_id}`: `{record.status.value}` on "
            f"`{record.branch_id}` with `{record.human_review_authority.value}` authority."
        )
    note_list = [note.strip() for note in notes if note.strip()]
    if note_list:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in note_list)
    lines.extend(
        [
            "",
            "## Boundary Status",
            "",
            "The run remains planning-only and non-terminal. It does not authorize "
            "downstream operational conversion or scientific findings.",
        ]
    )
    report = "\n".join(lines) + "\n"
    errors = validate_aggregate_report_text(report)
    if errors:
        raise ValueError("parallel run report contains forbidden terms: " + "; ".join(errors))
    return report


def write_multi_family_outputs(
    *,
    output_root: str | Path,
    manifest: MultiFamilyDossierManifest,
    aggregate_report_markdown: str,
    parallel_run_report_markdown: str,
) -> tuple[Path, Path, Path]:
    output_root = Path(output_root)
    workspace = output_root / manifest.run_id / "aggregate_dossier_coordination"
    manifest_path = workspace / "multi_family_dossier_manifest.yaml"
    aggregate_report_path = workspace / "aggregate_family_dossier_report.md"
    parallel_report_path = workspace / "parallel_implementation_run_report.md"
    dump_data(manifest, manifest_path)
    aggregate_report_path.parent.mkdir(parents=True, exist_ok=True)
    aggregate_report_path.write_text(aggregate_report_markdown, encoding="utf-8")
    parallel_report_path.write_text(parallel_run_report_markdown, encoding="utf-8")
    return manifest_path, aggregate_report_path, parallel_report_path


def validate_aggregate_report_text(text: str) -> list[str]:
    """Find concrete secrets or serialized authority claims in a public report.

    Scientific and planning vocabulary is intentionally unrestricted here.  Typed records enforce
    the R5-011/confirmation/authority boundaries; prose words such as ``execution``, ``p-value``,
    ``effect size``, ``significant``, and ``model result`` cannot create authority.
    """

    return [label for label, pattern in _SENSITIVE_REPORT_PATTERNS if pattern.search(text)]


def family_title_by_id(shortlist: QuestionFamilyShortlistManifest) -> dict[str, str]:
    return {
        shortlisted.family.question_family_id: shortlisted.family.title
        for shortlisted in shortlist.shortlisted
    }


def family_by_id(shortlist: QuestionFamilyShortlistManifest) -> dict[str, QuestionFamily]:
    return {
        shortlisted.family.question_family_id: shortlisted.family
        for shortlisted in shortlist.shortlisted
    }


def _validate_development_surrogate_text_fields(
    artifact: DevelopmentSurrogateFamilyOutcomeArtifact,
) -> None:
    text_fields = {
        "markdown": artifact.public_markdown,
        "decision_summary": artifact.decision_summary,
        "blockers": " ".join(artifact.blockers),
    }
    failures = {
        name: validate_aggregate_report_text(text)
        for name, text in text_fields.items()
        if validate_aggregate_report_text(text)
    }
    if failures:
        detail = "; ".join(
            f"{name}: {', '.join(errors)}" for name, errors in sorted(failures.items())
        )
        raise ValueError("development surrogate outcome contains forbidden terms: " + detail)


def _build_development_surrogate_input(
    *,
    run_id: str,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    blockers: list[str],
) -> DevelopmentSurrogateFamilyOutcomeInput:
    variants_by_id = {variant.variant_id: variant for variant in family.variants}
    missing = sorted(set(branch.active_variant_ids) - set(variants_by_id))
    if missing:
        raise ValueError("branch active variants missing from family: " + ", ".join(missing))
    active_variants = [
        DevelopmentSurrogateFamilyVariantInput(
            variant_id=variant.variant_id,
            question_seed_id=variant.question_seed_id,
            question=variant.seed.question,
            variant_role=variant.variant_role,
            distinction_axes=[axis.value for axis in variant.distinction_axes],
            distinct_from_siblings=variant.distinct_from_siblings,
        )
        for variant_id in branch.active_variant_ids
        for variant in [variants_by_id[variant_id]]
    ]
    return DevelopmentSurrogateFamilyOutcomeInput(
        input_packet_id=_development_surrogate_input_id(branch=branch, run_id=run_id),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        family_title=family.title,
        family_summary=family.summary,
        shared_scientific_tension=family.shared_scientific_tension,
        branch_state=branch.state,
        active_variants=active_variants,
        current_blockers=blockers,
        prompt_requirements=[
            "Return a development-only plan, reject, or escalation dossier.",
            "Preserve family and variant distinctions without merging sibling variants.",
            "Mark surrogate authority as development_model_surrogate and development_testing_only.",
            "Do not claim human approval, final closure, operational conversion, or findings.",
        ],
        forbidden_outputs=[
            "QuestionCard",
            "AnalysisContract",
            "bridge artifact",
            "scientific analysis run",
            "confirmation outcome",
            "p-value or significance claim",
            "effect estimate or decoder/model result",
        ],
    )


def _validate_manifest_identity(
    branch: QuestionFamilyBranch,
    manifest: EndUserDossierManifest,
) -> None:
    if manifest.branch_id != branch.branch_id:
        raise ValueError("end-user dossier manifest references another branch")
    if manifest.question_family_id != branch.question_family_id:
        raise ValueError("end-user dossier manifest references another family")
    if manifest.context_id != branch.context_id:
        raise ValueError("end-user dossier manifest references another context")
    if manifest.owner_session_id != branch.owner_session_id:
        raise ValueError("end-user dossier manifest references another owner session")


def _validate_manifest_files(
    repository_root: Path,
    manifest: EndUserDossierManifest,
) -> None:
    expected = {
        manifest.translator_input_path: manifest.translator_input_digest,
        manifest.end_user_dossier_artifact_path: manifest.end_user_dossier_artifact_digest,
        manifest.audit_sidecar_path: manifest.audit_sidecar_digest,
        manifest.translator_session_snapshot_path: manifest.translator_session_snapshot_digest,
    }
    mismatches = []
    for path_text, expected_digest in expected.items():
        path = _resolve_path(path_text, repository_root=repository_root)
        if not path.exists():
            mismatches.append(f"{path_text} missing")
            continue
        actual_digest = stable_hash(load_data(path))
        if (
            isinstance(manifest, GenericEndUserDossierManifest)
            and path_text == manifest.translator_session_snapshot_path
        ):
            actual_digest = stable_hash(
                load_model(path, ScientificAgentSessionSnapshot).model_dump(mode="json")
            )
        if actual_digest != expected_digest:
            mismatches.append(f"{path_text} digest mismatch")
    markdown_path = _resolve_path(manifest.end_user_dossier_path, repository_root=repository_root)
    if not markdown_path.exists():
        mismatches.append(f"{manifest.end_user_dossier_path} missing")
    elif stable_hash(markdown_path.read_text(encoding="utf-8")) != manifest.end_user_dossier_digest:
        mismatches.append(f"{manifest.end_user_dossier_path} digest mismatch")
    if mismatches:
        raise ValueError(
            "end-user dossier manifest file validation failed: " + "; ".join(mismatches)
        )


def _validate_branch_local_paths(manifest: EndUserDossierManifest) -> None:
    marker = f"/branches/{manifest.branch_id}/planner/"
    path_fields = {
        "translator_input_path": manifest.translator_input_path,
        "end_user_dossier_path": manifest.end_user_dossier_path,
        "end_user_dossier_artifact_path": manifest.end_user_dossier_artifact_path,
        "audit_sidecar_path": manifest.audit_sidecar_path,
        "translator_session_snapshot_path": manifest.translator_session_snapshot_path,
    }
    leaked = [
        field_name
        for field_name, path_text in path_fields.items()
        if marker not in "/" + Path(path_text).as_posix()
    ]
    if leaked:
        raise ValueError("end-user dossier paths are not branch-local: " + ", ".join(leaked))


def _find_end_user_dossier_event(
    branch: QuestionFamilyBranch,
    manifest: EndUserDossierManifest,
) -> QuestionFamilyBranchEvent:
    matches = [
        event
        for event in branch.events
        if event.event_type == QuestionFamilyBranchEventType.END_USER_SCIENTIFIC_DOSSIER_RENDERED
        and event.event_id == manifest.branch_event_id
    ]
    if len(matches) != 1:
        raise ValueError("branch replay does not contain exactly one end-user dossier event")
    event = matches[0]
    if event.payload.artifact_digest != manifest.end_user_dossier_artifact_digest:
        raise ValueError("branch replay end-user dossier artifact digest mismatch")
    if event.payload.provider_id != manifest.provider_id:
        raise ValueError("branch replay end-user dossier provider mismatch")
    if event.payload.model_id != manifest.model_id:
        raise ValueError("branch replay end-user dossier model mismatch")
    if event.payload.session_id != manifest.session_id:
        raise ValueError("branch replay end-user dossier session mismatch")
    if event.payload.prompt_version != manifest.prompt_version:
        raise ValueError("branch replay end-user dossier prompt mismatch")
    if event.payload.input_digest != manifest.input_digest:
        raise ValueError("branch replay end-user dossier input digest mismatch")
    if event.payload.output_digest != manifest.output_digest:
        raise ValueError("branch replay end-user dossier output digest mismatch")
    return event


def _latest_human_review_gate_event(
    branch: QuestionFamilyBranch,
) -> QuestionFamilyBranchEvent | None:
    gate_event_types = {
        QuestionFamilyBranchEventType.HUMAN_REVIEW_ACCEPTED_FOR_DOSSIER,
        QuestionFamilyBranchEventType.HUMAN_REVIEW_REVISION_REQUESTED,
        QuestionFamilyBranchEventType.HUMAN_REVIEW_REJECTED,
        QuestionFamilyBranchEventType.HUMAN_REVIEW_ESCALATION_REQUESTED,
        QuestionFamilyBranchEventType.HUMAN_REVIEW_GATE_CORRECTED,
    }
    gate_events = [event for event in branch.events if event.event_type in gate_event_types]
    if not gate_events:
        return None
    return max(gate_events, key=lambda event: event.sequence)


def _human_review_authority_for_gate(
    event: QuestionFamilyBranchEvent | None,
) -> ReviewAuthority:
    if event is None:
        return ReviewAuthority.MISSING
    if (
        event.event_type == QuestionFamilyBranchEventType.HUMAN_REVIEW_ACCEPTED_FOR_DOSSIER
        and event.actor_role.value == "human_expert"
    ):
        return ReviewAuthority.REAL_HUMAN_EXPERT
    return ReviewAuthority.UNKNOWN


def _record_id(question_family_id: str, branch_id: str) -> str:
    digest = stable_hash({"question_family_id": question_family_id, "branch_id": branch_id})
    return f"family-dossier-record-{digest[:12]}"


def _aggregate_manifest_id(run_id: str, records: list[FamilyDossierOutputRecord]) -> str:
    digest = stable_hash(
        {
            "run_id": run_id,
            "records": [
                {
                    "question_family_id": record.question_family_id,
                    "branch_id": record.branch_id,
                    "status": record.status.value,
                }
                for record in records
            ],
        }
    )
    return f"multi-family-dossier-manifest-{digest[:12]}"


def _outcome_sidecar_id(question_family_id: str, branch_id: str) -> str:
    digest = stable_hash({"question_family_id": question_family_id, "branch_id": branch_id})
    return f"family-outcome-audit-sidecar-{digest[:12]}"


def _development_surrogate_input_id(*, branch: QuestionFamilyBranch, run_id: str) -> str:
    digest = stable_hash(
        {
            "run_id": run_id,
            "branch_id": branch.branch_id,
            "question_family_id": branch.question_family_id,
            "prompt_version": DEVELOPMENT_FAMILY_OUTCOME_SURROGATE_PROMPT_VERSION,
        }
    )
    return f"development-surrogate-family-outcome-input-{digest[:12]}"


def _development_surrogate_session_id(
    *,
    run_id: str,
    branch: QuestionFamilyBranch,
    provider: ScientificAgentProvider,
) -> str:
    digest = stable_hash(
        {
            "run_id": run_id,
            "branch_id": branch.branch_id,
            "question_family_id": branch.question_family_id,
            "provider_id": provider.provider_id,
            "model_id": provider.model_id,
            "prompt_version": DEVELOPMENT_FAMILY_OUTCOME_SURROGATE_PROMPT_VERSION,
        }
    )
    return f"development-surrogate-session-{digest[:12]}"


def _render_development_outcome_markdown(
    *,
    branch: QuestionFamilyBranch,
    family_title: str,
    status: FamilyDossierStatus,
    blockers: list[str],
    retained_plan_lines: list[str],
) -> str:
    lines = [
        f"# {family_title}",
        "",
        f"Family status: `{status.value}`",
        "",
        "This is a user-readable planning outcome dossier. It preserves the useful scientific "
        "work and the configured review disposition even though this family did not receive "
        "accepted-plan authority.",
        "",
        "## Branch Scope",
        "",
        f"- Active variants: `{len(branch.active_variant_ids)}`",
        f"- Branch state: `{branch.state.value}`",
        "",
    ]
    lines.extend(retained_plan_lines)
    lines.extend(["## Retained Outcome And Review Basis", ""])
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This dossier is a terminal planning record, not an accepted analysis plan. It does "
            "not open any downstream analysis or compatibility path, or convert the family into "
            "operational material.",
        ]
    )
    # This note intentionally preserves reviewer and planner language such as candidate p-values,
    # effect sizes, or model diagnostics. Those are planning terms, not result claims. Authority is
    # enforced by the typed record/status and fixed boundary text above; a broad lexical veto here
    # would erase exactly the useful terminal work this artifact exists to retain.
    return "\n".join(lines) + "\n"


def _safe_retained_plan_markdown(
    *,
    output_root: Path,
    run_id: str,
    branch: QuestionFamilyBranch,
) -> list[str]:
    """Project scientific fields from one invalid-but-identity-safe root plan.

    The source remains an untrusted, non-imported planner artifact.  This projection reads only the
    fixed root ``plan_draft.yaml`` path, requires branch/context/owner/variant identity, rejects any
    structured authority/result boundary, drops provenance IDs, and renders an allowlist of
    scientific plan fields.  It never changes the warning status or grants accepted-plan authority.
    """

    planner_root = output_root / run_id / "branches" / branch.branch_id / "planner"
    source = planner_root / "plan_draft.yaml"
    try:
        source_stat = source.lstat()
        if source.is_symlink() or not source.is_file() or source_stat.st_size <= 0:
            return []
        if not source.resolve().is_relative_to(planner_root.resolve()):
            return []
        raw = load_data(source)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError):
        return []
    if not isinstance(raw, Mapping):
        return []
    expected_identity = {
        "message_type": "plan_draft",
        "branch_id": branch.branch_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
        "scope": "family",
    }
    if any(raw.get(key) != expected for key, expected in expected_identity.items()):
        return []
    if find_planner_boundary_violations(raw):
        return []

    expected_variant_identity = {
        invariant.variant_id: (invariant.question_seed_id, invariant.invariant.invariant_id)
        for invariant in branch.variant_intent_invariants
    }
    evidence_by_id = {evidence.evidence_id: evidence for evidence in branch.inspection_evidence}
    raw_outcomes = raw.get("variant_outcomes")
    raw_plans = raw.get("variant_analysis_plans")
    if not isinstance(raw_outcomes, list) or not isinstance(raw_plans, list):
        return []
    outcomes_by_variant: dict[str, Mapping[str, object]] = {}
    for item in raw_outcomes:
        if not isinstance(item, Mapping):
            return []
        variant_id = item.get("variant_id")
        seed_id = item.get("question_seed_id")
        if (
            not isinstance(variant_id, str)
            or expected_variant_identity.get(variant_id, (None, None))[0] != seed_id
            or variant_id in outcomes_by_variant
            or not _evidence_ids_support_variant(
                item.get("evidence_ids"),
                variant_id=variant_id,
                evidence_by_id=evidence_by_id,
            )
        ):
            return []
        outcomes_by_variant[variant_id] = item
    if set(outcomes_by_variant) != set(expected_variant_identity):
        return []
    accepted_variant_ids = {
        variant_id
        for variant_id, outcome in outcomes_by_variant.items()
        if outcome.get("decision") in {"accepted", "accepted_requires_new_skill"}
    }
    known_decisions = {
        "pending",
        "accepted",
        "accepted_requires_new_skill",
        "rejected_dataset_mismatch",
        "rejected_operationalization_failure",
        "rejected_scientific_drift",
        "rejected_insufficient_evidence",
        "rejected_low_scientific_value",
        "human_escalation",
    }
    if any(
        outcome.get("decision") not in known_decisions for outcome in outcomes_by_variant.values()
    ):
        return []

    plans_by_variant: dict[str, Mapping[str, object]] = {}
    for item in raw_plans:
        if not isinstance(item, Mapping):
            return []
        variant_id = item.get("variant_id")
        seed_id = item.get("question_seed_id")
        plan = item.get("analysis_plan")
        if (
            not isinstance(variant_id, str)
            or expected_variant_identity.get(variant_id, (None, None))[0] != seed_id
            or variant_id in plans_by_variant
            or not isinstance(plan, Mapping)
            or plan.get("branch_id") != branch.branch_id
            or plan.get("question_version_id") != seed_id
            or plan.get("scientific_intent_invariant_id")
            != expected_variant_identity.get(variant_id, (None, None))[1]
            or plan.get("contains_executable_code") is not False
            or not _evidence_ids_support_variant(
                plan.get("evidence_ids"),
                variant_id=variant_id,
                evidence_by_id=evidence_by_id,
            )
            or not _plan_data_source_identity_is_safe(
                plan.get("data_sources"),
                branch_id=branch.branch_id,
                variant_id=variant_id,
                evidence_by_id=evidence_by_id,
            )
        ):
            return []
        plans_by_variant[variant_id] = plan
    if set(plans_by_variant) != accepted_variant_ids:
        return []

    lines = [
        "## Safely retained planner draft",
        "",
        "The planner returned a complete-looking draft, but it did not pass strict typed "
        "validation and has not received scientific review. The scientific content below is a "
        "sanitized inspection copy: provenance identifiers are omitted, and no accepted-plan "
        "authority is implied.",
        "",
    ]
    summary = _public_plan_text(raw.get("summary"))
    if summary:
        lines.extend(["### Family summary", "", summary, ""])
    assessment = _public_plan_text(raw.get("planner_assessment"))
    if assessment:
        lines.extend([f"- Planner assessment label: `{assessment}`", ""])

    for index, invariant in enumerate(branch.variant_intent_invariants, start=1):
        outcome = outcomes_by_variant[invariant.variant_id]
        lines.extend([f"### Variant {index}", ""])
        decision = _public_plan_text(outcome.get("decision"))
        outcome_summary = _public_plan_text(outcome.get("summary"))
        if decision:
            lines.append(f"- Planner-stated disposition: `{decision}`")
        if outcome_summary:
            lines.append(f"- Planner summary: {outcome_summary}")
        if decision or outcome_summary:
            lines.append("")
        plan = plans_by_variant.get(invariant.variant_id)
        if plan is None:
            lines.extend(
                [
                    "No analysis plan was supplied for this non-accepted planner disposition.",
                    "",
                ]
            )
        else:
            _append_plan_scalars(lines, plan)
            _append_plan_data_sources(lines, plan.get("data_sources"))
            _append_plan_lists(lines, plan)
    return lines


def _evidence_ids_support_variant(
    raw_ids: object,
    *,
    variant_id: str,
    evidence_by_id: Mapping[str, QuestionFamilyInspectionEvidence],
) -> bool:
    if not isinstance(raw_ids, list) or not raw_ids:
        return False
    for evidence_id in raw_ids:
        if not isinstance(evidence_id, str):
            return False
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None or not evidence.can_support_variant(variant_id):
            return False
    return True


def _plan_data_source_identity_is_safe(
    raw_sources: object,
    *,
    branch_id: str,
    variant_id: str,
    evidence_by_id: Mapping[str, QuestionFamilyInspectionEvidence],
) -> bool:
    if not isinstance(raw_sources, list):
        return False
    for source in raw_sources:
        if not isinstance(source, Mapping) or source.get("branch_id") != branch_id:
            return False
        required_variables = source.get("required_variables")
        if required_variables and not _evidence_ids_support_variant(
            source.get("evidence_ids"),
            variant_id=variant_id,
            evidence_by_id=evidence_by_id,
        ):
            return False
    return True


def _append_plan_scalars(lines: list[str], plan: Mapping[str, object]) -> None:
    for field_name, label in _PLAN_SCALAR_FIELDS:
        text = _public_plan_text(plan.get(field_name))
        if text:
            lines.extend([f"#### {label}", "", text, ""])


def _append_plan_data_sources(lines: list[str], raw_sources: object) -> None:
    if not isinstance(raw_sources, list):
        return
    rendered: list[list[str]] = []
    for raw_source in raw_sources:
        if not isinstance(raw_source, Mapping):
            continue
        source_lines: list[str] = []
        description = _public_plan_text(raw_source.get("description"))
        grain = _public_plan_text(raw_source.get("expected_grain"))
        if description:
            source_lines.append(description)
        if grain:
            source_lines.append(f"Expected grain: {grain}")
        variables = _public_plan_list(raw_source.get("required_variables"))
        if variables:
            source_lines.append("Required variables: " + "; ".join(variables))
        limitations = _public_plan_list(raw_source.get("limitations"))
        if limitations:
            source_lines.append("Limitations: " + "; ".join(limitations))
        if source_lines:
            rendered.append(source_lines)
    if not rendered:
        return
    lines.extend(["#### Data sources", ""])
    for index, source_lines in enumerate(rendered, start=1):
        lines.append(f"{index}. " + source_lines[0])
        lines.extend(f"   - {item}" for item in source_lines[1:])
    lines.append("")


def _append_plan_lists(lines: list[str], plan: Mapping[str, object]) -> None:
    for field_name, label in _PLAN_LIST_FIELDS:
        items = _public_plan_list(plan.get(field_name))
        if not items:
            continue
        lines.extend([f"#### {label}", ""])
        lines.extend(f"- {item}" for item in items)
        lines.append("")


def _public_plan_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    rendered: list[str] = []
    for item in value:
        text = _public_plan_text(item)
        if text:
            rendered.append(text)
    return rendered


def _public_plan_text(value: object) -> str:
    if isinstance(value, str):
        text = " ".join(value.split())
    elif isinstance(value, Mapping) and len(value) == 1:
        key, nested = next(iter(value.items()))
        if not isinstance(key, str) or not isinstance(nested, str):
            return ""
        text = f"{' '.join(key.split())}: {' '.join(nested.split())}"
    else:
        return ""
    for pattern in _PUBLIC_PLAN_TEXT_REDACTIONS:
        text = pattern.sub(" [internal reference omitted]", text)
    return " ".join(text.split()).replace("|", "\\|")


def _resolve_path(path: str | Path, *, repository_root: Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return repository_root / path


def _display_path(path: str | Path, repository_root: Path) -> str:
    path = Path(path)
    try:
        return path.relative_to(repository_root).as_posix()
    except ValueError:
        return path.as_posix()


def _aggregate_report_artifact_path(value: str, *, run_id: str) -> str:
    """Render an artifact location without exposing the host's absolute run root.

    Aggregate reports live at ``<output>/<run_id>/aggregate_dossier_coordination``.  Records may
    legitimately retain absolute audit paths, so project them back to a report-relative location
    beginning after the outer run-id component.  An unexpected absolute path outside that run is
    reduced to its filename; the report remains useful without publishing host topology.
    """

    if not value:
        return ""
    path = Path(value)
    if not path.is_absolute():
        return path.as_posix()
    parts = path.parts
    try:
        run_index = parts.index(run_id)
    except ValueError:
        return path.name
    suffix = Path(*parts[run_index + 1 :]).as_posix()
    return f"../{suffix}" if suffix and suffix != "." else path.name


def _markdown_cell(value: str) -> str:
    value = value.replace("|", "\\|")
    return value
