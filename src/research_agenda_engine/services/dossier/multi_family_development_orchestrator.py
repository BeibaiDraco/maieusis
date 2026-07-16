from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

from pydantic import BaseModel, ConfigDict

from ...io import dump_data, load_data, load_model
from ...mcp import ScientificDialogueServer
from ...provenance import stable_hash
from ...providers.coding_agents import (
    CodingAgentHandoffBackend,
    CodingAgentPlannerHost,
    FakePlannerHost,
)
from ...providers.scientific_agents import (
    ScientificAgentInfrastructureError,
    ScientificAgentProvider,
    ScientificAgentSessionSnapshot,
    ScientificAgentTranscriptRecord,
    scientific_agent_payload_digest,
)
from ...schemas.analysis_plan import DatasetInspectionSourceType
from ...schemas.dossier_closure import DossierClosureDiagnostic, DossierClosureOutcome
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
    DatasetClaimStatus,
    DatasetGroundingLevel,
    QuestionFamilyScientificSourceSnapshot,
    QuestionFamilyScientificVariantSnapshot,
)
from ...schemas.multi_family_dossier import (
    FamilyDossierOutputRecord,
    FamilyDossierStatus,
    MultiFamilyCoordinationMode,
    MultiFamilyDossierManifest,
    ReviewAuthority,
)
from ...schemas.planner_run import (
    CodingAgentRunRecord,
    PlannerArtifactImportManifest,
    PlannerReturnedArtifactBundle,
)
from ...schemas.planning_dialogue import (
    BranchDecisionKind,
    BranchRejectionMessage,
    HumanEscalationRequest,
    IndependentPlanReviewMessage,
    PlanDraftMessage,
    PlanningMessage,
    PlanReviewDecisionValue,
    PlanRevisionContext,
    QuestionOwnerPlanReviewMessage,
)
from ...schemas.question_family import (
    QuestionFamily,
    QuestionFamilyShortlistManifest,
    ShortlistedQuestionFamily,
)
from ...schemas.question_family_branch import (
    QuestionFamilyBranch,
    QuestionFamilyBranchEventType,
    QuestionFamilyInspectionEvidence,
)
from ...schemas.stage_receipt import FailureClass
from ..orchestration import QuestionFamilyBranchManager
from ..planning.dataset_planner_packet import DatasetInspectionResources
from ..planning.planner_failures import (
    CodingAgentProviderUnavailable,
    HardFamilyIntegrityViolation,
)
from .development_review_dossier import (
    DEFAULT_REVIEW_GUIDANCE,
    DevelopmentMaterialRevisionDeferred,
    DevelopmentReviewEscalated,
    DevelopmentReviewRejected,
    DevelopmentRevisionBudgetExhausted,
    DevelopmentRevisionTerminal,
    run_development_review_and_dossier,
)
from .generic_family_dossier import (
    DOSSIER_CLOSURE_DIAGNOSTIC_FILENAME,
    GENERIC_END_USER_SCIENTIFIC_DOSSIER_WORKSPACE,
    GENERIC_SCIENTIFIC_DOSSIER_RENDERED_WORKSPACE,
    GENERIC_SCIENTIFIC_DOSSIER_WORKSPACE,
    DossierProvenanceIntegrityFailure,
    PublicDossierRevisionRequired,
    run_generic_development_dossier_pipeline,
)
from .generic_human_review_override import emit_generic_human_review_override_template
from .multi_family_coordinator import (
    build_multi_family_dossier_manifest,
    build_queued_family_record,
    render_aggregate_report,
    validate_aggregate_report_text,
    write_development_outcome_dossier,
    write_multi_family_outputs,
)

R5_M1H_DEFAULT_RUN_ID = "r5-m1h-true-parallel-family-dossier-development-run"
R5_M1H_DEVELOPMENT_WORKSPACE = "development_full_chain"


class PlannerRevisionTerminal(RuntimeError):
    """A revised planner bundle ended honestly with its own rejection/escalation artifact."""

    def __init__(
        self,
        *,
        outcome_kind: GenericFamilyOutcomeKind,
        message: BranchRejectionMessage | HumanEscalationRequest,
        bundle: PlannerReturnedArtifactBundle,
        revision_round: int,
    ) -> None:
        super().__init__(f"planner returned {outcome_kind.value} during revision round")
        self.outcome_kind = outcome_kind
        self.message = message
        self.bundle = bundle
        self.revision_round = revision_round


@dataclass(frozen=True)
class _CheckedArtifactFileSnapshot:
    relative_path: Path
    content: bytes
    sha256: str


@dataclass(frozen=True)
class _PlannerRevisionSurfaceSnapshot:
    root: Path
    workspace: Path
    recovery_root: Path
    directories: tuple[Path, ...]
    files: tuple[_CheckedArtifactFileSnapshot, ...]


def _tree_snapshot(root: Path) -> tuple[tuple[Path, ...], tuple[_CheckedArtifactFileSnapshot, ...]]:
    directories: list[Path] = []
    files: list[_CheckedArtifactFileSnapshot] = []

    def visit(directory: Path) -> None:
        with os.scandir(directory) as entries:
            for entry in sorted(entries, key=lambda item: item.name):
                path = Path(entry.path)
                relative = path.relative_to(root)
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISLNK(mode):
                    raise HardFamilyIntegrityViolation(
                        "planner revision baseline contains a symlink alias"
                    )
                if stat.S_ISDIR(mode):
                    directories.append(relative)
                    visit(path)
                    continue
                if not stat.S_ISREG(mode):
                    raise HardFamilyIntegrityViolation(
                        "planner revision baseline contains a non-regular filesystem entry"
                    )
                content = path.read_bytes()
                files.append(
                    _CheckedArtifactFileSnapshot(
                        relative_path=relative,
                        content=content,
                        sha256=hashlib.sha256(content).hexdigest(),
                    )
                )

    visit(root)
    return tuple(directories), tuple(files)


def _assert_confined_regular_path(*, root: Path, path: Path) -> None:
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise HardFamilyIntegrityViolation(
            "checked planner artifact cannot enter the revision transaction"
        )
    cursor = root
    for part in resolved.relative_to(root).parts:
        cursor /= part
        if cursor.is_symlink():
            raise HardFamilyIntegrityViolation(
                "checked planner artifact cannot enter the revision transaction"
            )


def _snapshot_checked_revision_surface(workspace: Path) -> _PlannerRevisionSurfaceSnapshot:
    """Freeze the complete branch surface before an in-place revision transaction."""

    lexical_workspace = workspace.absolute()
    if (
        lexical_workspace.is_symlink()
        or lexical_workspace.resolve(strict=True) != lexical_workspace
    ):
        raise HardFamilyIntegrityViolation("planner revision root is symlink-aliased")
    workspace = lexical_workspace
    root = workspace.parent
    if root.is_symlink() or root.resolve(strict=True) != root:
        raise HardFamilyIntegrityViolation("planner revision root is symlink-aliased")
    manifest_path = workspace / "artifact_import_manifest.yaml"
    manifest = load_model(manifest_path, PlannerArtifactImportManifest)
    for path in (*manifest.checked_paths, str(manifest_path)):
        _assert_confined_regular_path(root=workspace, path=Path(path))
    directories, files = _tree_snapshot(root)
    run_root = root.parent.parent if root.parent.name == "branches" else root.parent
    return _PlannerRevisionSurfaceSnapshot(
        root=root,
        workspace=workspace,
        recovery_root=(run_root / "private_diagnostics" / "planner_revision_recovery" / root.name),
        directories=directories,
        files=files,
    )


def _current_tree_entries(root: Path) -> list[tuple[Path, str, bytes | None, str | None]]:
    entries: list[tuple[Path, str, bytes | None, str | None]] = []

    def visit(directory: Path) -> None:
        with os.scandir(directory) as children:
            for entry in sorted(children, key=lambda item: item.name):
                path = Path(entry.path)
                relative = path.relative_to(root)
                mode = entry.stat(follow_symlinks=False).st_mode
                if stat.S_ISLNK(mode):
                    entries.append((relative, "symlink", None, os.readlink(path)))
                elif stat.S_ISDIR(mode):
                    entries.append((relative, "directory", None, None))
                    visit(path)
                elif stat.S_ISREG(mode):
                    entries.append((relative, "file", path.read_bytes(), None))
                else:
                    entries.append((relative, "special", None, None))

    visit(root)
    return entries


def _clear_tree_without_following_links(root: Path) -> None:
    def clear(directory: Path) -> None:
        with os.scandir(directory) as children:
            entries = list(children)
        for entry in entries:
            path = Path(entry.path)
            if entry.is_dir(follow_symlinks=False) and not entry.is_symlink():
                clear(path)
                os.rmdir(path)
            else:
                os.unlink(path)

    clear(root)


def _restore_snapshot_files(snapshot: _PlannerRevisionSurfaceSnapshot) -> None:
    for relative in sorted(snapshot.directories, key=lambda path: len(path.parts)):
        (snapshot.root / relative).mkdir()
    for item in snapshot.files:
        path = snapshot.root / item.relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.restore-{item.sha256[:12]}")
        temporary.write_bytes(item.content)
        os.replace(temporary, path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != item.sha256:
            raise HardFamilyIntegrityViolation(
                "failed revision could not restore a checked branch artifact"
            )


def _restore_failed_revision_surface(
    snapshot: _PlannerRevisionSurfaceSnapshot,
    *,
    revision_round: int,
    provider_unavailable: bool,
) -> Path:
    """Quarantine failed revision bytes and restore the last imported surface exactly."""

    if (
        snapshot.root.is_symlink()
        or not snapshot.root.is_dir()
        or snapshot.root.resolve(strict=True) != snapshot.root
    ):
        raise HardFamilyIntegrityViolation("revision transaction root is no longer confined")
    audit_root = snapshot.recovery_root
    audit_base = audit_root.parents[2]
    if audit_base.is_symlink() or audit_base.resolve(strict=True) != audit_base:
        raise HardFamilyIntegrityViolation("revision recovery audit base is symlink-aliased")
    cursor = audit_base
    for part in audit_root.relative_to(audit_base).parts:
        cursor /= part
        if cursor.exists() or cursor.is_symlink():
            if cursor.is_symlink() or not cursor.is_dir():
                raise HardFamilyIntegrityViolation(
                    "revision recovery audit path is symlink-aliased"
                )
        else:
            cursor.mkdir()
    if not audit_root.resolve(strict=True).is_relative_to(audit_base):
        raise HardFamilyIntegrityViolation("revision recovery audit root escaped its branch")
    round_root = audit_root / f"round-{revision_round}"
    if round_root.exists() or round_root.is_symlink():
        raise HardFamilyIntegrityViolation("revision recovery round already exists or is aliased")
    round_root.mkdir()

    candidate_records: list[dict[str, str]] = []
    restored_records: list[dict[str, str]] = []
    unsafe_entries: list[str] = []
    baseline = {item.relative_path: item for item in snapshot.files}
    baseline_directories = set(snapshot.directories)
    for index, (relative_path, kind, content, target) in enumerate(
        _current_tree_entries(snapshot.root)
    ):
        prior = baseline.get(relative_path)
        current_digest = hashlib.sha256(content).hexdigest() if content is not None else ""
        if kind == "file" and prior is not None and current_digest == prior.sha256:
            continue
        if kind == "directory" and relative_path in baseline_directories:
            continue
        record = {"path": relative_path.as_posix(), "entry_type": kind}
        if content is not None:
            candidate_path = round_root / (
                f"{index:04d}-"
                + hashlib.sha256(relative_path.as_posix().encode("utf-8")).hexdigest()[:12]
                + ".candidate"
            )
            candidate_path.write_bytes(content)
            record["candidate_sha256"] = current_digest
            record["candidate_snapshot"] = str(candidate_path)
        if target is not None:
            record["symlink_target"] = target
        if kind in {"symlink", "special"}:
            unsafe_entries.append(relative_path.as_posix())
        candidate_records.append(record)

    _clear_tree_without_following_links(snapshot.root)
    _restore_snapshot_files(snapshot)
    for item in snapshot.files:
        restored_records.append(
            {
                "path": item.relative_path.as_posix(),
                "restored_sha256": item.sha256,
            }
        )

    audit_path = round_root / "recovery_audit.yaml"
    dump_data(
        {
            "schema_version": "planner_revision_recovery/v1",
            "revision_round": revision_round,
            "provider_unavailable": provider_unavailable,
            "candidate_files": candidate_records,
            "restored_files": restored_records,
            "unsafe_entries": unsafe_entries,
            "authority_granted": False,
        },
        audit_path,
    )
    if unsafe_entries:
        raise HardFamilyIntegrityViolation(
            "failed revision introduced an unsafe filesystem entry; prior branch surface restored"
        )
    return audit_path


# Dataset grounding is DERIVED from the coding-agent run's returned evidence, never
# hardcoded or caller-asserted. Each `QuestionFamilyInspectionEvidence.source_type` maps
# CONSERVATIVELY to a grounding tier; the family grounding is the deepest tier any imported evidence
# supports, so it can never exceed the inspection depth the agent actually reached. No source_type
# maps to FULL_LOCAL_STRUCTURAL_AVAILABLE — that tier is never claimed from a single evidence
# source_type (the honest floor).
_SOURCE_TYPE_GROUNDING: dict[DatasetInspectionSourceType, DatasetGroundingLevel] = {
    DatasetInspectionSourceType.DOCUMENTATION: DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY,
    DatasetInspectionSourceType.REPOSITORY_CODE: DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY,
    DatasetInspectionSourceType.EXECUTOR_SKILL: DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY,
    DatasetInspectionSourceType.SYNTHETIC_PROBE: DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY,
    DatasetInspectionSourceType.SCHEMA: DatasetGroundingLevel.SCHEMA_METADATA_INSPECTED,
    DatasetInspectionSourceType.METADATA_QUERY: DatasetGroundingLevel.SCHEMA_METADATA_INSPECTED,
    DatasetInspectionSourceType.SAMPLE_INSPECTION: DatasetGroundingLevel.SAMPLE_INSPECTED,
}

# Grounding tiers, lowest -> highest, for taking the max over a set of evidence records.
_GROUNDING_ORDER: tuple[DatasetGroundingLevel, ...] = (
    DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY,
    DatasetGroundingLevel.SCHEMA_METADATA_INSPECTED,
    DatasetGroundingLevel.SAMPLE_INSPECTED,
    DatasetGroundingLevel.FULL_LOCAL_STRUCTURAL_AVAILABLE,
)


def derive_dataset_grounding_level(
    evidence: Iterable[QuestionFamilyInspectionEvidence],
) -> DatasetGroundingLevel:
    """Honestly derive the family dataset-grounding level from the coding agent's returned evidence.

    The level is the deepest tier any evidence record's ``source_type`` supports (documentation ->
    schema/metadata -> sample). Unknown or synthetic source types floor to
    ``DOCUMENTATION_INVENTORY_ONLY``; with no evidence, the floor is returned. The result can never
    exceed the inspection depth the agent actually reached (the honest ceiling), so a ``FakePlannerHost``
    ``synthetic_probe`` run stays ``documentation_inventory_only`` and a real run that only read schema
    reports ``schema_metadata_inspected`` (not a caller-asserted ``sample_inspected``).
    """
    level = DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY
    for record in evidence:
        mapped = _SOURCE_TYPE_GROUNDING.get(
            record.source_type, DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY
        )
        if _GROUNDING_ORDER.index(mapped) > _GROUNDING_ORDER.index(level):
            level = mapped
    return level


class MultiFamilyDevelopmentFamilyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_family_id: str
    branch_id: str
    status: FamilyDossierStatus
    record: FamilyDossierOutputRecord
    artifact_paths: list[str]
    api_attempts: int = 0
    api_successes: int = 0
    api_failures: int = 0
    # Two-sided cost (optional; None where a family reported nothing). ``spawn_*`` is the coding-agent
    # planner spawn cost (from the run record), ``review_*`` is the owner + independent review cost
    # (summed across revise rounds). USD is present only where the source reported it (Claude spawn).
    spawn_cost_usd: float | None = None
    spawn_total_tokens: int | None = None
    review_cost_usd: float | None = None
    review_total_tokens: int | None = None
    error: str = ""


class MultiFamilyDevelopmentRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    manifest_path: str
    aggregate_report_path: str
    parallel_run_report_path: str
    family_results: list[MultiFamilyDevelopmentFamilyResult]
    max_parallel_family_workers: int
    elapsed_seconds: float
    api_attempts: int
    api_successes: int
    api_failures: int
    # Whole-run cost = sum of every family's spawn + review cost/tokens (None if none reported).
    total_cost_usd: float | None = None
    total_tokens: int | None = None


def run_multi_family_development_orchestrator(
    *,
    output_root: str | Path,
    target_family_ids: Iterable[str],
    shortlist_path: str | Path = Path(
        "corpus/question_families/reviewed/question_family_shortlist_manifest.yaml"
    ),
    run_id: str = R5_M1H_DEFAULT_RUN_ID,
    planner_host: CodingAgentPlannerHost | None = None,
    planner_host_factory: Callable[[str], CodingAgentPlannerHost] | None = None,
    owner_provider: ScientificAgentProvider | None = None,
    reviewer_provider: ScientificAgentProvider | None = None,
    completed_records: Iterable[FamilyDossierOutputRecord] = (),
    max_parallel_family_workers: int = 2,
    max_revise_rounds: int = 4,
    inspection_resources: DatasetInspectionResources | None = None,
    subagents_used: int = 0,
    api_agents_used: int = 0,
    review_authority: ReviewAuthority = ReviewAuthority.AUTOMATED,
) -> MultiFamilyDevelopmentRunResult:
    if max_parallel_family_workers < 1:
        raise ValueError("max_parallel_family_workers must be >= 1")
    if max_revise_rounds < 0:
        raise ValueError("max_revise_rounds must be >= 0")
    if review_authority != ReviewAuthority.AUTOMATED:
        raise ValueError("Phase 4 development orchestrator emits automated authority only")
    # Injected real review is the ONLY plan path (the deterministic review stub was removedubs and
    # the `real_review_flow` coexistence switch). Every PLAN family runs the typed owner +
    # independent plan review (`run_development_review_and_dossier`) — mock providers in CI/unit,
    # real providers live — under automated authority (no human review imported). Grounding is
    # derived from the run's evidence, not caller-asserted.
    if owner_provider is None or reviewer_provider is None:
        raise ValueError(
            "run_multi_family_development_orchestrator requires both owner_provider and "
            "reviewer_provider (injected real review is the only plan path)"
        )
    # Per-family host provisioning. `planner_host_factory` builds a FRESH host/runner per
    # family so concurrent families share NO runner state — critically, each family snapshots its own
    # lead config-home for the breach tripwire, so one family's real breach fails only that family
    # (not every in-flight sibling). The shared `planner_host` path stays for CI/mock (FakePlannerHost
    # is stateless, safe to share). Exactly one of the two may be supplied.
    if planner_host is not None and planner_host_factory is not None:
        raise ValueError("pass either planner_host or planner_host_factory, not both")
    shared_host: CodingAgentPlannerHost | None = planner_host
    if planner_host_factory is None:
        shared_host = shared_host or FakePlannerHost(outcome="plan")
    started = datetime.now(UTC)
    monotonic_started = monotonic()
    output_root = Path(output_root)
    shortlist = load_model(shortlist_path, QuestionFamilyShortlistManifest)
    target_ids = tuple(
        dict.fromkeys(family_id.strip() for family_id in target_family_ids if family_id.strip())
    )
    completed_by_family = {record.question_family_id: record for record in completed_records}
    shortlisted_by_id = {item.family.question_family_id: item for item in shortlist.shortlisted}
    missing_targets = sorted(set(target_ids) - set(shortlisted_by_id))
    if missing_targets:
        raise ValueError("target families missing from shortlist: " + ", ".join(missing_targets))

    branch_manager = QuestionFamilyBranchManager(output_root, run_id=run_id)
    branches_by_family = {
        family_id: _create_branch(branch_manager, shortlisted)
        for family_id, shortlisted in shortlisted_by_id.items()
        if family_id not in completed_by_family
    }

    def _host_for_family(family_id: str) -> CodingAgentPlannerHost:
        if planner_host_factory is not None:
            return planner_host_factory(family_id)
        assert shared_host is not None  # guaranteed when no factory is supplied
        return shared_host

    family_results: list[MultiFamilyDevelopmentFamilyResult] = []
    worker_count = min(max_parallel_family_workers, max(1, len(target_ids)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(
                _run_one_family_with_factory,
                output_root=output_root,
                run_id=run_id,
                branch=branches_by_family[family_id],
                family=shortlisted_by_id[family_id].family,
                host_factory=_host_for_family,
                owner_provider=owner_provider,
                reviewer_provider=reviewer_provider,
                max_revise_rounds=max_revise_rounds,
                inspection_resources=inspection_resources,
                review_authority=review_authority,
            ): family_id
            for family_id in target_ids
            if family_id not in completed_by_family
        }
        for future in as_completed(futures):
            family_results.append(future.result())

    records_by_family: dict[str, FamilyDossierOutputRecord] = dict(completed_by_family)
    records_by_family.update(
        {result.question_family_id: result.record for result in family_results}
    )
    for family_id, branch in branches_by_family.items():
        if family_id in records_by_family:
            continue
        records_by_family[family_id] = build_queued_family_record(
            branch=branch,
            family_title=shortlisted_by_id[family_id].family.title,
            blockers=["Not targeted in this development full-chain run."],
        )
    ordered_records = [
        records_by_family[shortlisted.family.question_family_id]
        for shortlisted in shortlist.shortlisted
    ]

    aggregate_workspace = output_root / run_id / "aggregate_dossier_coordination"
    aggregate_report_path = aggregate_workspace / "aggregate_family_dossier_report.md"
    parallel_report_path = aggregate_workspace / "parallel_implementation_run_report.md"
    manifest = build_multi_family_dossier_manifest(
        run_id=run_id,
        shortlist=shortlist,
        records=ordered_records,
        coordination_mode=MultiFamilyCoordinationMode.DEVELOPMENT_RUN,
        max_parallel_family_workers=max_parallel_family_workers,
        aggregate_report_path=str(aggregate_report_path),
        parallel_run_report_path=str(parallel_report_path),
    )
    aggregate_report = render_aggregate_report(manifest)
    finished = datetime.now(UTC)
    api_attempts = sum(result.api_attempts for result in family_results)
    api_successes = sum(result.api_successes for result in family_results)
    api_failures = sum(result.api_failures for result in family_results)
    parallel_report = render_development_parallel_run_report(
        manifest,
        family_results=sorted(family_results, key=lambda item: item.question_family_id),
        started_at=started,
        finished_at=finished,
        subagents_used=subagents_used,
        api_agents_used=api_agents_used,
        api_attempts=api_attempts,
        api_successes=api_successes,
        api_failures=api_failures,
    )
    manifest_path, aggregate_report_path, parallel_report_path = write_multi_family_outputs(
        output_root=output_root,
        manifest=manifest,
        aggregate_report_markdown=aggregate_report,
        parallel_run_report_markdown=parallel_report,
    )
    total_cost_usd, total_tokens = _aggregate_run_cost(family_results)
    return MultiFamilyDevelopmentRunResult(
        run_id=run_id,
        manifest_path=str(manifest_path),
        aggregate_report_path=str(aggregate_report_path),
        parallel_run_report_path=str(parallel_report_path),
        family_results=sorted(family_results, key=lambda item: item.question_family_id),
        max_parallel_family_workers=max_parallel_family_workers,
        elapsed_seconds=monotonic() - monotonic_started,
        api_attempts=api_attempts,
        api_successes=api_successes,
        api_failures=api_failures,
        total_cost_usd=total_cost_usd,
        total_tokens=total_tokens,
    )


def _aggregate_run_cost(
    family_results: list[MultiFamilyDevelopmentFamilyResult],
) -> tuple[float | None, int | None]:
    """Sum spawn + review cost/tokens across families (spawn + owner/reviewer review).

    A total is None only when NO family reported that figure; otherwise present figures are summed
    (a family that reported nothing contributes 0), so a mixed run still reports a visible total.
    """
    cost_total = 0.0
    token_total = 0
    has_cost = False
    has_tokens = False
    for result in family_results:
        for cost in (result.spawn_cost_usd, result.review_cost_usd):
            if cost is not None:
                cost_total += cost
                has_cost = True
        for tokens in (result.spawn_total_tokens, result.review_total_tokens):
            if tokens is not None:
                token_total += tokens
                has_tokens = True
    return (cost_total if has_cost else None, token_total if has_tokens else None)


def _bundle_spawn_usage(bundle: PlannerReturnedArtifactBundle) -> tuple[float | None, int | None]:
    """Read spawn cost/tokens from the run record the host wrote at the bundle's run trace path."""
    try:
        record = load_model(bundle.run_trace_path, CodingAgentRunRecord)
    except Exception:
        return (None, None)
    if record.usage is None:
        return (None, None)
    return (record.usage.cost_usd, record.usage.total_tokens)


def render_development_parallel_run_report(
    manifest: MultiFamilyDossierManifest,
    *,
    family_results: list[MultiFamilyDevelopmentFamilyResult],
    started_at: datetime,
    finished_at: datetime,
    subagents_used: int,
    api_agents_used: int,
    api_attempts: int,
    api_successes: int,
    api_failures: int,
    tests_run: Iterable[str] = (),
) -> str:
    elapsed = max(0.0, (finished_at - started_at).total_seconds())
    lines = [
        "# R5-M1H Parallel Development Run Report",
        "",
        f"- Started at: `{started_at.isoformat()}`",
        f"- Finished at: `{finished_at.isoformat()}`",
        f"- Elapsed seconds: `{elapsed:.1f}`",
        f"- Subagents used: `{subagents_used}`",
        f"- API agents used: `{api_agents_used}`",
        f"- API attempts: `{api_attempts}`",
        f"- API successes: `{api_successes}`",
        f"- API failures: `{api_failures}`",
        f"- Max parallel family workers: `{manifest.max_parallel_family_workers}`",
        f"- Coordination mode: `{manifest.coordination_mode.value}`",
        "",
        "## Family Status",
        "",
    ]
    result_by_family = {result.question_family_id: result for result in family_results}
    for record in manifest.records:
        lines.append(
            f"- `{record.question_family_id}`: `{record.status.value}` on `{record.branch_id}` "
            f"with `{record.human_review_authority.value}` authority, "
            f"`{record.human_review_status}` human-review status, and "
            f"`{record.dataset_grounding_level.value}` dataset grounding."
        )
        if record.provider_id:
            lines.append(
                "  Provenance: "
                f"`{record.provider_id}` / `{record.model_id}` / "
                f"`{record.prompt_version}` / `{record.session_id}`."
            )
        paths = [
            record.end_user_dossier_manifest_path,
            record.end_user_dossier_path,
            record.audit_sidecar_path,
            record.outcome_markdown_path,
            record.outcome_audit_path,
            record.development_surrogate_artifact_path,
            record.development_surrogate_session_snapshot_path,
        ]
        for path in [path for path in paths if path]:
            lines.append(f"  Artifact: `{path}`")
        family_result = result_by_family.get(record.question_family_id)
        if family_result is not None:
            for path in family_result.artifact_paths:
                if path not in paths:
                    lines.append(f"  Artifact: `{path}`")
    test_list = [test.strip() for test in tests_run if test.strip()]
    if test_list:
        lines.extend(["", "## Tests Run", ""])
        lines.extend(f"- {test}" for test in test_list)
    lines.extend(
        [
            "",
            "## Remaining Limits",
            "",
            "- Automated families have no human review imported; optional file review can promote one family.",
            "- No downstream run artifact is authorized by this report.",
            "",
            "## Boundary Status",
            "",
            "R5-011 remains blocked.",
            "All records are planning-only and non-terminal.",
        ]
    )
    report = "\n".join(lines) + "\n"
    errors = validate_aggregate_report_text(report)
    if errors:
        raise ValueError(
            "development parallel run report contains forbidden terms: " + "; ".join(errors)
        )
    return report


def _run_one_family_with_factory(
    *,
    output_root: Path,
    run_id: str,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    host_factory: Callable[[str], CodingAgentPlannerHost],
    owner_provider: ScientificAgentProvider | None = None,
    reviewer_provider: ScientificAgentProvider | None = None,
    max_revise_rounds: int = 4,
    inspection_resources: DatasetInspectionResources | None = None,
    review_authority: ReviewAuthority = ReviewAuthority.AUTOMATED,
) -> MultiFamilyDevelopmentFamilyResult:
    """Construct the per-family host inside the worker isolation boundary."""
    try:
        host = host_factory(branch.question_family_id)
        return _run_one_family(
            output_root=output_root,
            run_id=run_id,
            branch=branch,
            family=family,
            host=host,
            owner_provider=owner_provider,
            reviewer_provider=reviewer_provider,
            max_revise_rounds=max_revise_rounds,
            inspection_resources=inspection_resources,
            review_authority=review_authority,
        )
    except HardFamilyIntegrityViolation as exc:
        return _hard_integrity_family_result(
            output_root=output_root,
            run_id=run_id,
            branch=branch,
            family=family,
            exc=exc,
        )
    except Exception as exc:
        return _recoverable_family_terminal_result(
            output_root=output_root,
            run_id=run_id,
            branch=branch,
            family=family,
            status=FamilyDossierStatus.INFRASTRUCTURE_INCOMPLETE,
            public_blocker=(
                "The coding-agent planner could not be started. The scientific question remains "
                "available, and this family closed with a provider warning."
            ),
            exc=exc,
        )


def _run_one_family(
    *,
    output_root: Path,
    run_id: str,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    host: CodingAgentPlannerHost,
    owner_provider: ScientificAgentProvider | None = None,
    reviewer_provider: ScientificAgentProvider | None = None,
    max_revise_rounds: int = 4,
    inspection_resources: DatasetInspectionResources | None = None,
    review_authority: ReviewAuthority = ReviewAuthority.AUTOMATED,
) -> MultiFamilyDevelopmentFamilyResult:
    try:
        return _run_one_family_or_raise(
            output_root=output_root,
            run_id=run_id,
            branch=branch,
            family=family,
            host=host,
            owner_provider=owner_provider,
            reviewer_provider=reviewer_provider,
            max_revise_rounds=max_revise_rounds,
            inspection_resources=inspection_resources,
            review_authority=review_authority,
        )
    except ScientificAgentInfrastructureError as exc:
        # A bounded retry on a transient owner/reviewer API failure (429/5xx/timeout) was
        # exhausted. This is an INFRASTRUCTURE terminal, not a scientific failure — it must never
        # masquerade as failed_validation (AGENTS.md #10 fail honestly). A human MAY re-run; the
        # persisted status is honest. Cleanup mirrors the FAILED_VALIDATION handler below.
        try:
            reloaded = QuestionFamilyBranchManager(output_root, run_id=run_id).load_branch(
                branch.branch_id
            )
        except Exception:
            reloaded = branch
        return _recoverable_family_terminal_result(
            output_root=output_root,
            run_id=run_id,
            branch=reloaded,
            family=family,
            status=FamilyDossierStatus.INFRASTRUCTURE_INCOMPLETE,
            public_blocker=(
                "The Question Owner or independent reviewer remained unavailable after bounded "
                "retries. Retained planning material is shown with a provider warning."
            ),
            exc=exc,
            api_failures=1,
        )
    except CodingAgentProviderUnavailable as exc:
        try:
            reloaded = QuestionFamilyBranchManager(output_root, run_id=run_id).load_branch(
                branch.branch_id
            )
        except Exception:
            reloaded = branch
        return _recoverable_family_terminal_result(
            output_root=output_root,
            run_id=run_id,
            branch=reloaded,
            family=family,
            status=FamilyDossierStatus.INFRASTRUCTURE_INCOMPLETE,
            public_blocker=(
                "The coding-agent provider became unavailable during bounded planning. Retained "
                "planning material is shown with a provider warning."
            ),
            exc=exc,
            api_failures=1,
        )
    except PublicDossierRevisionRequired as exc:
        return _dossier_closure_family_result(
            output_root=output_root,
            run_id=run_id,
            branch=branch,
            family=family,
            exc=exc,
            expected_code=DossierClosureOutcome.PUBLIC_DOSSIER_REVISION_REQUIRED,
            status=FamilyDossierStatus.PUBLIC_DOSSIER_REVISION_REQUIRED,
        )
    except DossierProvenanceIntegrityFailure as exc:
        return _dossier_closure_family_result(
            output_root=output_root,
            run_id=run_id,
            branch=branch,
            family=family,
            exc=exc,
            expected_code=DossierClosureOutcome.PROVENANCE_INTEGRITY_TERMINAL,
            status=FamilyDossierStatus.PROVENANCE_INTEGRITY_TERMINAL,
        )
    except HardFamilyIntegrityViolation:
        raise
    except Exception as exc:
        # Shape/availability failures close only this family with a readable warning dossier.
        return _recoverable_family_terminal_result(
            output_root=output_root,
            run_id=run_id,
            branch=branch,
            family=family,
            status=FamilyDossierStatus.FAILED_VALIDATION,
            public_blocker=(
                "The returned planning material could not be fully validated. The scientific "
                "question and any safely retained products remain available with a validation warning."
            ),
            exc=exc,
        )


def _dossier_closure_family_result(
    *,
    output_root: Path,
    run_id: str,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    exc: PublicDossierRevisionRequired | DossierProvenanceIntegrityFailure,
    expected_code: DossierClosureOutcome,
    status: FamilyDossierStatus,
) -> MultiFamilyDevelopmentFamilyResult:
    """Validate one exact closure diagnostic before preserving accepted upstream authority."""
    try:
        planner_root = output_root / run_id / "branches" / branch.branch_id / "planner"
        workspace_name = (
            GENERIC_END_USER_SCIENTIFIC_DOSSIER_WORKSPACE
            if expected_code == DossierClosureOutcome.PUBLIC_DOSSIER_REVISION_REQUIRED
            else GENERIC_SCIENTIFIC_DOSSIER_WORKSPACE
        )
        expected_diagnostic = planner_root / workspace_name / DOSSIER_CLOSURE_DIAGNOSTIC_FILENAME
        if exc.diagnostic_path.absolute() != expected_diagnostic.absolute():
            raise ValueError("dossier closure diagnostic coordinate mismatch")
        _require_regular_confined_file(expected_diagnostic, root=planner_root)
        diagnostic = load_model(expected_diagnostic, DossierClosureDiagnostic)
        if (
            diagnostic.code != expected_code
            or diagnostic.run_id != run_id
            or diagnostic.branch_id != branch.branch_id
            or diagnostic.question_family_id != branch.question_family_id
            or (
                expected_code == DossierClosureOutcome.PROVENANCE_INTEGRITY_TERMINAL
                and diagnostic.failure_class != FailureClass.VALIDATION_FAILURE
            )
        ):
            raise ValueError("dossier closure diagnostic identity mismatch")

        writing_root = planner_root / GENERIC_SCIENTIFIC_DOSSIER_WORKSPACE
        allowed_retained = {
            writing_root / "source_outcome_packet.yaml",
            writing_root / "source_review_decision.yaml",
            writing_root / "scientific_source_snapshot.yaml",
        }
        expected_omitted: set[Path] = set()
        if expected_code == DossierClosureOutcome.PUBLIC_DOSSIER_REVISION_REQUIRED:
            machine_root = planner_root / GENERIC_SCIENTIFIC_DOSSIER_RENDERED_WORKSPACE
            allowed_retained.update(
                {
                    machine_root / "scientific_dossier.md",
                    machine_root / "scientific_dossier_artifact.yaml",
                    machine_root / "manifest.yaml",
                }
            )
            public_root = planner_root / GENERIC_END_USER_SCIENTIFIC_DOSSIER_WORKSPACE
            expected_omitted = {
                public_root / "end_user_dossier.md",
                public_root / "end_user_dossier_artifact.yaml",
                public_root / "end_user_dossier_audit.yaml",
                public_root / "manifest.yaml",
            }
        retained = {Path(raw) for raw in diagnostic.retained_artifact_paths}
        omitted = {Path(raw) for raw in diagnostic.omitted_public_artifact_paths}
        if retained != allowed_retained or omitted != expected_omitted:
            raise ValueError("dossier closure path allowlist mismatch")
        for path in retained:
            _require_regular_confined_file(path, root=planner_root)
        for path in omitted:
            if path.exists() or path.is_symlink():
                raise ValueError("an omitted public dossier artifact already exists")

        review_root = planner_root / "development_review"
        owner_path = review_root / "owner_plan_review.yaml"
        independent_path = review_root / "independent_plan_review.yaml"
        for review_path in (owner_path, independent_path):
            _require_regular_confined_file(review_path, root=planner_root)
        owner_review = load_model(owner_path, QuestionOwnerPlanReviewMessage)
        independent_review = load_model(independent_path, IndependentPlanReviewMessage)
        for review in (owner_review, independent_review):
            if (
                review.branch_id != branch.branch_id
                or review.context_id != branch.context_id
                or review.owner_session_id != branch.owner_session_id
                or review.decision != PlanReviewDecisionValue.ACCEPT
                or {item.variant_id for item in review.variant_outcomes}
                != set(branch.active_variant_ids)
            ):
                raise ValueError("dossier closure lacks bound accepted review records")
        reloaded = QuestionFamilyBranchManager(output_root, run_id=run_id).load_branch(
            branch.branch_id
        )
        if (
            owner_review.plan_draft_message_id != independent_review.plan_draft_message_id
            or owner_review.plan_draft_packet_id != independent_review.plan_draft_packet_id
            or owner_review.analysis_plan_id != independent_review.analysis_plan_id
            or independent_review.owner_plan_review_message_id != owner_review.message_id
        ):
            raise ValueError("dossier closure accepted review pair is not cross-bound")
        for review in (owner_review, independent_review):
            if not any(
                event.event_type == QuestionFamilyBranchEventType.FAMILY_DIALOGUE_RECORDED
                and event.payload.planning_message_id == review.message_id
                and event.payload.planning_message_type == review.message_type
                and event.payload.planning_message_digest == review.payload_digest
                for event in reloaded.events
            ):
                raise ValueError(
                    "dossier closure accepted review was not imported into branch replay"
                )
        reason = expected_code.value
        record = build_queued_family_record(
            branch=reloaded,
            family_title=family.title,
            status=status,
            blockers=[reason],
        )
        return MultiFamilyDevelopmentFamilyResult(
            question_family_id=branch.question_family_id,
            branch_id=branch.branch_id,
            status=status,
            record=record,
            artifact_paths=[str(expected_diagnostic), *sorted(str(path) for path in retained)],
            error=reason,
        )
    except Exception as validation_exc:
        return _hard_integrity_family_result(
            output_root=output_root,
            run_id=run_id,
            branch=branch,
            family=family,
            exc=validation_exc,
        )


def _require_regular_confined_file(path: Path, *, root: Path) -> None:
    file_stat = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(file_stat.st_mode):
        raise ValueError("dossier closure artifact must be a regular non-symlink file")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("dossier closure artifact escaped its branch workspace")


def _generic_failed_validation_result(
    *,
    output_root: Path,
    run_id: str,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    exc: Exception,
) -> MultiFamilyDevelopmentFamilyResult:
    return _recoverable_family_terminal_result(
        output_root=output_root,
        run_id=run_id,
        branch=branch,
        family=family,
        status=FamilyDossierStatus.FAILED_VALIDATION,
        public_blocker=(
            "The returned planning material could not be fully validated. The scientific question "
            "remains available with a validation warning."
        ),
        exc=exc,
    )


def _recoverable_family_terminal_result(
    *,
    output_root: Path,
    run_id: str,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    status: FamilyDossierStatus,
    public_blocker: str,
    exc: Exception,
    api_failures: int = 0,
) -> MultiFamilyDevelopmentFamilyResult:
    """Write a digest-bound, public-safe terminal dossier for one recoverable family warning."""
    try:
        reloaded = QuestionFamilyBranchManager(output_root, run_id=run_id).load_branch(
            branch.branch_id
        )
    except Exception:
        reloaded = branch
    try:
        record = write_development_outcome_dossier(
            output_root=output_root,
            run_id=run_id,
            branch=reloaded,
            family_title=family.title,
            status=status,
            blockers=[public_blocker],
        )
    except Exception:
        # Last-resort sibling isolation: the envelope layer can still render a safe family fallback
        # from the trusted front-half family if this richer outcome writer is unavailable.
        record = build_queued_family_record(
            branch=reloaded,
            family_title=family.title,
            status=status,
            blockers=[public_blocker],
        )
    return MultiFamilyDevelopmentFamilyResult(
        question_family_id=branch.question_family_id,
        branch_id=branch.branch_id,
        status=status,
        record=record,
        artifact_paths=[
            path for path in (record.outcome_markdown_path, record.outcome_audit_path) if path
        ],
        error=str(exc),
        api_failures=api_failures,
    )


def _hard_integrity_family_result(
    *,
    output_root: Path,
    run_id: str,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    exc: Exception,
) -> MultiFamilyDevelopmentFamilyResult:
    """Close one unsafe family without promoting planner-authored content or stopping siblings."""
    try:
        reloaded = QuestionFamilyBranchManager(output_root, run_id=run_id).load_branch(
            branch.branch_id
        )
    except Exception:
        reloaded = branch
    record = build_queued_family_record(
        branch=reloaded,
        family_title=family.title,
        status=FamilyDossierStatus.HARD_INTEGRITY_TERMINAL,
        blockers=[
            "A planning integrity or isolation boundary stopped downstream artifact promotion. "
            "The original scientific question remains visible for inspection."
        ],
    )
    return MultiFamilyDevelopmentFamilyResult(
        question_family_id=branch.question_family_id,
        branch_id=branch.branch_id,
        status=FamilyDossierStatus.HARD_INTEGRITY_TERMINAL,
        record=record,
        artifact_paths=[],
        error=str(exc),
    )


def _run_one_family_or_raise(
    *,
    output_root: Path,
    run_id: str,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    host: CodingAgentPlannerHost,
    owner_provider: ScientificAgentProvider | None = None,
    reviewer_provider: ScientificAgentProvider | None = None,
    max_revise_rounds: int = 4,
    inspection_resources: DatasetInspectionResources | None = None,
    review_authority: ReviewAuthority = ReviewAuthority.AUTOMATED,
) -> MultiFamilyDevelopmentFamilyResult:
    branch_manager = QuestionFamilyBranchManager(output_root, run_id=run_id)
    backend = CodingAgentHandoffBackend(
        output_root,
        run_id=run_id,
        branch_manager=branch_manager,
        inspection_resources=inspection_resources,
    )
    branch = branch_manager.start_planner(branch.branch_id)
    workspace = _development_workspace(output_root, run_id=run_id, branch_id=branch.branch_id)
    workspace.mkdir(parents=True, exist_ok=True)

    source_snapshot = _scientific_source_snapshot(branch=branch, family=family, run_id=run_id)
    source_snapshot_path = workspace / "scientific_source_snapshot.yaml"
    dump_data(source_snapshot, source_snapshot_path)
    source_snapshot_digest = stable_hash(source_snapshot.model_dump(mode="json"))

    # Feasibility runs through the coding-agent planner-host seam: prepare a
    # branch-local handoff, let the host inspect and return a typed bundle, then
    # import that bundle as replayable branch evidence. The host decides the real
    # outcome (plan / rejection / escalation); the orchestrator no longer hardcodes
    # an accepted plan.
    handoff = backend.prepare_handoff(branch.branch_id)
    # A per-family branch-scoped dialogue server lets the spawned agent ask the Question Owner
    # mid-inspection over localhost (the owner API key stays in this process, inside
    # `owner_provider`, and never enters the agent sandbox). A real host self-hosts it;
    # `FakePlannerHost` ignores it. Built for every family (providers are required at entry).
    dialogue_server = ScientificDialogueServer(
        output_root, run_id=run_id, owner_provider=owner_provider
    )
    bundle = host.run_planning(
        run_id=run_id,
        branch=branch_manager.load_branch(branch.branch_id),
        handoff=handoff,
        dialogue_server=dialogue_server,
    )
    import_manifest = backend.import_returned_artifacts(bundle)
    # Spawn cost/tokens from the run record the host wrote (real runs only; None for fakes). Revise
    # rounds re-spawn and overwrite the run record, so this is the primary spawn's cost; review cost
    # (below) sums across all rounds.
    spawn_cost_usd, spawn_total_tokens = _bundle_spawn_usage(bundle)
    branch = branch_manager.load_branch(branch.branch_id)
    outcome_kind = _bundle_outcome_kind(bundle)
    planner_message = _load_planner_message(bundle, outcome_kind)
    imported_evidence = _imported_evidence_records(branch, import_manifest)
    if outcome_kind == GenericFamilyOutcomeKind.PLAN:
        outcome_evidence = imported_evidence
        grounding = derive_dataset_grounding_level(outcome_evidence)
    else:
        outcome_evidence = _terminal_evidence_records(planner_message, imported_evidence)
    if outcome_kind != GenericFamilyOutcomeKind.PLAN and not outcome_evidence:
        grounding = DatasetGroundingLevel.UNKNOWN
    elif outcome_kind != GenericFamilyOutcomeKind.PLAN:
        # Grounding is DERIVED from the evidence the host actually returned + imported:
        # never hardcoded, never caller-asserted, and never deeper than the agent truly inspected.
        grounding = derive_dataset_grounding_level(outcome_evidence)
    branch = branch_manager.record_planning_message(branch.branch_id, planner_message)

    # PLAN: injected real (mock in CI, real live) owner + independent review is the ONLY plan path.
    # Delegate the reviews + bounded revise-loop + honesty gate + outcome/decision + dossier to the
    # proven downstream (`run_development_review_and_dossier`), then map its result into the
    # family record (keeping the imported evidence-id / replay binding + the derived grounding). A
    # non-material `revise` re-spawns the planner; every other non-accept outcome raises a
    # distinct honest terminal that maps to its own no-dossier status.
    if outcome_kind == GenericFamilyOutcomeKind.PLAN:
        assert isinstance(planner_message, PlanDraftMessage)
        assert owner_provider is not None and reviewer_provider is not None
        return _run_plan_family_with_real_review(
            output_root=output_root,
            run_id=run_id,
            branch=branch,
            family=family,
            plan_draft=planner_message,
            owner_provider=owner_provider,
            reviewer_provider=reviewer_provider,
            dataset_grounding_level=grounding,
            source_snapshot=source_snapshot,
            source_snapshot_path=source_snapshot_path,
            handoff_manifest_path=handoff.manifest_path,
            workspace=workspace,
            branch_manager=branch_manager,
            host=host,
            backend=backend,
            dialogue_server=dialogue_server,
            max_revise_rounds=max_revise_rounds,
            spawn_cost_usd=spawn_cost_usd,
            spawn_total_tokens=spawn_total_tokens,
            review_authority=review_authority,
        )

    # REJECTION / ESCALATION terminal path (no review needed).
    dialogue_path = workspace / "planner_terminal_dialogue.yaml"
    dump_data([planner_message], dialogue_path)
    dialogue_artifact_paths = [str(dialogue_path)]
    if outcome_kind == GenericFamilyOutcomeKind.REJECTION:
        assert isinstance(planner_message, BranchRejectionMessage)
        outcome = _rejection_outcome_packet(
            branch=branch,
            family=family,
            rejection=planner_message,
            evidence=outcome_evidence,
            source_snapshot=source_snapshot,
            source_snapshot_digest=source_snapshot_digest,
            run_id=run_id,
            grounding=grounding,
        )
        status = FamilyDossierStatus.AUTOMATED_REJECT
    else:
        assert isinstance(planner_message, HumanEscalationRequest)
        outcome = _escalation_outcome_packet(
            branch=branch,
            family=family,
            escalation=planner_message,
            evidence=outcome_evidence,
            source_snapshot=source_snapshot,
            source_snapshot_digest=source_snapshot_digest,
            run_id=run_id,
            grounding=grounding,
        )
        status = FamilyDossierStatus.AUTOMATED_ESCALATION
    review_input = _development_review_input(
        branch=branch,
        family=family,
        outcome=outcome,
        source_snapshot=source_snapshot,
        run_id=run_id,
        review_authority=review_authority,
    )
    review_input_digest = stable_hash(review_input)
    review_output_digest = _digest(f"{family.question_family_id}:automated-output")
    decision = _development_decision_packet(
        branch=branch,
        outcome=outcome,
        run_id=run_id,
        input_digest=review_input_digest,
        output_digest=review_output_digest,
        dataset_grounding_level=grounding,
        review_authority=review_authority,
    )
    decision_path = workspace / "automated_review_decision.yaml"
    review_input_path = workspace / "automated_review_input.yaml"
    review_snapshot_path = workspace / "automated_review_session_snapshot.yaml"
    outcome_packet_path = workspace / "generic_family_outcome_packet.yaml"
    dump_data(outcome, outcome_packet_path)
    dump_data(review_input, review_input_path)
    dump_data(decision, decision_path)
    dump_data(
        _snapshot_from_payloads(
            branch_id=branch.branch_id,
            session_id=decision.session_id,
            provider_id=decision.provider_id,
            model_id=decision.model_id,
            prompt_version=decision.prompt_version,
            input_payload=review_input,
            output_payload=decision.model_dump(mode="json"),
            output_schema="GenericFamilyReviewDecisionPacket",
        ),
        review_snapshot_path,
    )

    dossier_result = run_generic_development_dossier_pipeline(
        output_root=output_root,
        run_id=run_id,
        branch_id=branch.branch_id,
        outcome_packet=outcome,
        review_decision=decision,
        source_snapshot=source_snapshot,
        family_title=family.title,
        family_summary=family.summary,
    )
    reloaded = branch_manager.load_branch(branch.branch_id)
    dossier_event = next(
        event
        for event in reloaded.events
        if event.event_id == dossier_result.end_user_rendered_event_id
    )
    record = FamilyDossierOutputRecord(
        record_id=_record_id(branch.question_family_id, branch.branch_id),
        question_family_id=branch.question_family_id,
        branch_id=branch.branch_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        family_title=family.title,
        variant_ids=list(branch.active_variant_ids),
        status=status,
        rejection_reason=(
            outcome.decision if outcome.outcome_kind == GenericFamilyOutcomeKind.REJECTION else None
        ),
        branch_state=reloaded.state,
        branch_event_count=len(reloaded.events),
        replay_verified=True,
        branch_event_id=dossier_event.event_id,
        branch_event_sequence=dossier_event.sequence,
        provider_id=decision.provider_id,
        model_id=decision.model_id,
        prompt_version=decision.prompt_version,
        session_id=decision.session_id,
        input_digest=decision.input_digest,
        output_digest=decision.output_digest,
        human_review_authority=review_authority,
        human_review_status="human_review_optional_not_imported",
        dataset_grounding_level=decision.dataset_grounding_level,
        blockers=[
            "Automated dossier only; human review is optional and not imported.",
            f"Dataset grounding level is {decision.dataset_grounding_level.value}; serious dataset grounding remains unimported.",
            "Downstream compatibility remains unavailable pending explicit authorization.",
        ],
        outcome_markdown_path=dossier_result.end_user_dossier_path,
        outcome_audit_path=dossier_result.audit_sidecar_path,
    )
    override_template_path = emit_generic_human_review_override_template(
        output_root=output_root,
        run_id=run_id,
        record=record,
        outcome_packet_path=outcome_packet_path,
        review_decision_path=decision_path,
        end_user_manifest_path=dossier_result.end_user_manifest_path,
        family_title=family.title,
    )
    artifact_paths = [
        str(source_snapshot_path),
        handoff.manifest_path,
        *dialogue_artifact_paths,
        str(outcome_packet_path),
        str(review_input_path),
        str(decision_path),
        str(review_snapshot_path),
        dossier_result.machine_dossier_path,
        dossier_result.end_user_dossier_path,
        dossier_result.audit_sidecar_path,
        dossier_result.end_user_manifest_path,
        str(override_template_path),
    ]
    return MultiFamilyDevelopmentFamilyResult(
        question_family_id=branch.question_family_id,
        branch_id=branch.branch_id,
        status=status,
        record=record,
        artifact_paths=artifact_paths,
        spawn_cost_usd=spawn_cost_usd,
        spawn_total_tokens=spawn_total_tokens,
    )


def _run_plan_family_with_real_review(
    *,
    output_root: Path,
    run_id: str,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    plan_draft: PlanDraftMessage,
    owner_provider: ScientificAgentProvider,
    reviewer_provider: ScientificAgentProvider,
    dataset_grounding_level: DatasetGroundingLevel,
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
    source_snapshot_path: Path,
    handoff_manifest_path: str,
    workspace: Path,
    branch_manager: QuestionFamilyBranchManager,
    host: CodingAgentPlannerHost,
    backend: CodingAgentHandoffBackend,
    dialogue_server: ScientificDialogueServer,
    max_revise_rounds: int,
    spawn_cost_usd: float | None = None,
    spawn_total_tokens: int | None = None,
    review_authority: ReviewAuthority = ReviewAuthority.AUTOMATED,
) -> MultiFamilyDevelopmentFamilyResult:
    """Drive one PLAN family through the real review + dossier downstream.

    Reuses ``run_development_review_and_dossier`` (real owner + independent review, honesty gate,
    generic outcome/decision packets, translated dossier + audit sidecar), now with a bounded
    revise-loop: on a non-material ``revise`` the ``replan`` closure re-spawns THIS family's planner
    with a revision handoff (prior plan + union of required changes), imports + records the revised
    plan, and the loop re-reviews it (up to ``max_revise_rounds`` rounds). Both-accept -> the accepted
    dossier record below. Every other non-accept outcome raises a distinct honest terminal
    (reject / escalate / material-deferred / budget-exhausted) that maps to its own no-dossier record.
    """

    def _replan(*, revision_context: PlanRevisionContext) -> PlanDraftMessage:
        # Re-spawn THIS family's planner with the revision handoff, import + record the revised plan.
        revision_handoff = backend.prepare_handoff(
            branch.branch_id, revision_context=revision_context
        )
        planner_workspace = Path(revision_handoff.packet_path).parent
        prior_surface = _snapshot_checked_revision_surface(planner_workspace)
        try:
            revised_bundle = host.run_planning(
                run_id=run_id,
                branch=branch_manager.load_branch(branch.branch_id),
                handoff=revision_handoff,
                dialogue_server=dialogue_server,
            )
            backend.import_returned_artifacts(revised_bundle)
            revised_kind = _bundle_outcome_kind(revised_bundle)
            revised_message = _load_planner_message(revised_bundle, revised_kind)
            branch_manager.record_planning_message(branch.branch_id, revised_message)
        except Exception as exc:
            audit_path = _restore_failed_revision_surface(
                prior_surface,
                revision_round=revision_context.revision_round,
                provider_unavailable=isinstance(exc, CodingAgentProviderUnavailable),
            )
            if isinstance(exc, CodingAgentProviderUnavailable):
                raise CodingAgentProviderUnavailable(
                    f"{exc}; prior imported planner surface restored; recovery_audit={audit_path}"
                ) from exc
            raise
        if revised_kind != GenericFamilyOutcomeKind.PLAN:
            # Preserve the planner-authored terminal instead of replacing it with a synthetic
            # review exception. Evidence was imported while the branch was still inspectable; the
            # typed terminal message now joins branch replay before the family closes.
            assert isinstance(revised_message, (BranchRejectionMessage, HumanEscalationRequest))
            raise PlannerRevisionTerminal(
                outcome_kind=revised_kind,
                message=revised_message,
                bundle=revised_bundle,
                revision_round=revision_context.revision_round,
            )
        assert isinstance(revised_message, PlanDraftMessage)
        return revised_message

    try:
        result = run_development_review_and_dossier(
            output_root=output_root,
            run_id=run_id,
            branch_id=branch.branch_id,
            family=family,
            plan_draft=plan_draft,
            owner_provider=owner_provider,
            reviewer_provider=reviewer_provider,
            dataset_grounding_level=dataset_grounding_level,
            replan=_replan,
            max_revise_rounds=max_revise_rounds,
            review_guidance=DEFAULT_REVIEW_GUIDANCE,
            review_authority=review_authority,
        )
    except PlannerRevisionTerminal as exc:
        return _planner_revision_terminal_result(
            output_root=output_root,
            run_id=run_id,
            terminal=exc,
            branch=branch,
            family=family,
            source_snapshot_path=source_snapshot_path,
            handoff_manifest_path=handoff_manifest_path,
            branch_manager=branch_manager,
        )
    except DevelopmentMaterialRevisionDeferred as exc:
        return _revise_loop_terminal_result(
            output_root=output_root,
            run_id=run_id,
            status=FamilyDossierStatus.MATERIAL_REVISION_DEFERRED,
            exc=exc,
            branch=branch,
            family=family,
            source_snapshot_path=source_snapshot_path,
            handoff_manifest_path=handoff_manifest_path,
            branch_manager=branch_manager,
        )
    except DevelopmentRevisionBudgetExhausted as exc:
        return _revise_loop_terminal_result(
            output_root=output_root,
            run_id=run_id,
            status=FamilyDossierStatus.REVISION_BUDGET_EXHAUSTED,
            exc=exc,
            branch=branch,
            family=family,
            source_snapshot_path=source_snapshot_path,
            handoff_manifest_path=handoff_manifest_path,
            branch_manager=branch_manager,
        )
    except DevelopmentReviewRejected as exc:
        return _revise_loop_terminal_result(
            output_root=output_root,
            run_id=run_id,
            status=FamilyDossierStatus.REJECTED,
            exc=exc,
            branch=branch,
            family=family,
            source_snapshot_path=source_snapshot_path,
            handoff_manifest_path=handoff_manifest_path,
            branch_manager=branch_manager,
        )
    except DevelopmentReviewEscalated as exc:
        return _revise_loop_terminal_result(
            output_root=output_root,
            run_id=run_id,
            status=FamilyDossierStatus.REVIEW_ESCALATED,
            exc=exc,
            branch=branch,
            family=family,
            source_snapshot_path=source_snapshot_path,
            handoff_manifest_path=handoff_manifest_path,
            branch_manager=branch_manager,
        )
    decision = load_model(result.review_decision_path, GenericFamilyReviewDecisionPacket)
    outcome = load_model(result.outcome_packet_path, GenericFamilyBranchOutcomePacket)

    # The FamilyDossierOutputRecord stores record-level review provenance. Keep a compact automated
    # review-input + snapshot artifact for audit, without cloning the legacy surrogate provenance
    # object.
    review_input = _development_review_input(
        branch=branch,
        family=family,
        outcome=outcome,
        source_snapshot=source_snapshot,
        run_id=run_id,
        review_authority=review_authority,
    )
    review_snapshot = _snapshot_from_payloads(
        branch_id=branch.branch_id,
        session_id=decision.session_id,
        provider_id=decision.provider_id,
        model_id=decision.model_id,
        prompt_version=decision.prompt_version,
        input_payload=review_input,
        output_payload=decision.model_dump(mode="json"),
        output_schema="GenericFamilyReviewDecisionPacket",
    )
    review_input_path = workspace / "automated_review_input.yaml"
    review_snapshot_path = workspace / "automated_review_session_snapshot.yaml"
    dump_data(review_input, review_input_path)
    dump_data(review_snapshot, review_snapshot_path)

    # Replay binding: reload the branch and locate the end-user dossier render event the 2e
    # downstream recorded (same replay proof the deterministic path stamps).
    reloaded = branch_manager.load_branch(branch.branch_id)
    dossier_event = next(
        event for event in reloaded.events if event.event_id == result.end_user_rendered_event_id
    )
    record = FamilyDossierOutputRecord(
        record_id=_record_id(branch.question_family_id, branch.branch_id),
        question_family_id=branch.question_family_id,
        branch_id=branch.branch_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        family_title=family.title,
        variant_ids=list(branch.active_variant_ids),
        status=FamilyDossierStatus.AUTOMATED_PLAN,
        branch_state=reloaded.state,
        branch_event_count=len(reloaded.events),
        replay_verified=True,
        branch_event_id=dossier_event.event_id,
        branch_event_sequence=dossier_event.sequence,
        provider_id=decision.provider_id,
        model_id=decision.model_id,
        prompt_version=decision.prompt_version,
        session_id=decision.session_id,
        input_digest=decision.input_digest,
        output_digest=decision.output_digest,
        human_review_authority=review_authority,
        human_review_status="human_review_optional_not_imported",
        dataset_grounding_level=decision.dataset_grounding_level,
        blockers=[
            "Automated dossier only; human review is optional and not imported.",
            f"Dataset grounding level is {decision.dataset_grounding_level.value}; "
            "serious dataset grounding remains unimported.",
            "Downstream compatibility remains unavailable pending explicit authorization.",
        ],
        outcome_markdown_path=result.end_user_dossier_path,
        outcome_audit_path=result.audit_sidecar_path,
    )
    override_template_path = emit_generic_human_review_override_template(
        output_root=output_root,
        run_id=run_id,
        record=record,
        outcome_packet_path=result.outcome_packet_path,
        review_decision_path=result.review_decision_path,
        end_user_manifest_path=result.end_user_manifest_path,
        family_title=family.title,
    )
    artifact_paths = [
        str(source_snapshot_path),
        handoff_manifest_path,
        result.owner_review_path,
        result.independent_review_path,
        result.outcome_packet_path,
        str(review_input_path),
        result.review_decision_path,
        str(review_snapshot_path),
        result.machine_dossier_path,
        result.end_user_dossier_path,
        result.audit_sidecar_path,
        result.end_user_manifest_path,
        str(override_template_path),
    ]
    # Two paid reviews per review round (owner + independent); the accepted round plus each revise
    # round that preceded it (result.revise_rounds_used) all ran real reviews.
    review_api_calls = 2 * (result.revise_rounds_used + 1)
    return MultiFamilyDevelopmentFamilyResult(
        question_family_id=branch.question_family_id,
        branch_id=branch.branch_id,
        status=FamilyDossierStatus.AUTOMATED_PLAN,
        record=record,
        artifact_paths=artifact_paths,
        api_attempts=review_api_calls,
        api_successes=review_api_calls,
        spawn_cost_usd=spawn_cost_usd,
        spawn_total_tokens=spawn_total_tokens,
        review_cost_usd=result.review_cost_usd,
        review_total_tokens=result.review_total_tokens,
    )


def _planner_revision_terminal_result(
    *,
    output_root: Path,
    run_id: str,
    terminal: PlannerRevisionTerminal,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    source_snapshot_path: Path,
    handoff_manifest_path: str,
    branch_manager: QuestionFamilyBranchManager,
) -> MultiFamilyDevelopmentFamilyResult:
    """Retain a real planner rejection/escalation returned by a review-requested replan."""
    reloaded = branch_manager.load_branch(branch.branch_id)
    message = terminal.message
    if isinstance(message, BranchRejectionMessage):
        status = FamilyDossierStatus.REJECTED
        details = [
            f"The revised planner rejected further planning: {message.reason}",
            *(
                ["Future-data alternatives: " + "; ".join(message.alternatives_for_future_data)]
                if message.alternatives_for_future_data
                else []
            ),
        ]
    else:
        status = FamilyDossierStatus.HUMAN_ESCALATION
        details = [
            f"The revised planner reached an honest optional escalation: {message.decision_needed}",
            f"Why the automated agents could not resolve it: {message.why_agents_cannot_resolve}",
        ]
    details.extend(
        f"Variant {entry.variant_id}: {entry.decision.value} — {entry.summary}"
        for entry in message.variant_outcomes
    )
    details.extend(
        [
            f"The planner terminal was returned during revision round {terminal.revision_round}.",
            "The terminal message and imported evidence remain bound to branch replay.",
            "Downstream compatibility remains unavailable pending explicit authorization.",
        ]
    )
    record = write_development_outcome_dossier(
        output_root=output_root,
        run_id=run_id,
        branch=reloaded,
        family_title=family.title,
        status=status,
        blockers=details,
    )
    artifacts = [
        str(source_snapshot_path),
        handoff_manifest_path,
        *terminal.bundle.artifact_paths,
        record.outcome_markdown_path,
        record.outcome_audit_path,
    ]
    # Only the review rounds completed before this replan incurred owner+independent review calls.
    review_api_calls = 2 * terminal.revision_round
    return MultiFamilyDevelopmentFamilyResult(
        question_family_id=branch.question_family_id,
        branch_id=branch.branch_id,
        status=status,
        record=record,
        artifact_paths=list(dict.fromkeys(artifacts)),
        api_attempts=review_api_calls,
        api_successes=review_api_calls,
    )


def _revise_loop_terminal_result(
    *,
    output_root: Path,
    run_id: str,
    status: FamilyDossierStatus,
    exc: DevelopmentRevisionTerminal,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    source_snapshot_path: Path,
    handoff_manifest_path: str,
    branch_manager: QuestionFamilyBranchManager,
) -> MultiFamilyDevelopmentFamilyResult:
    """Build an honest user-readable dossier for a bounded review-loop terminal.

    The artifact is deliberately not an accepted-plan dossier.  It preserves the latest plan and
    both review dispositions so a scientifically useful, repairable product is not replaced by a
    generic fallback merely because automated acceptance was not reached.
    """
    reloaded = branch_manager.load_branch(branch.branch_id)
    blockers, retained_review_paths = _retained_review_terminal_details(status, exc)
    record = write_development_outcome_dossier(
        output_root=output_root,
        run_id=run_id,
        branch=reloaded,
        family_title=family.title,
        status=status,
        blockers=blockers,
        # This field names imported HUMAN-review authority. The automated owner/reviewer
        # provenance remains in the retained typed review artifacts rather than being mislabeled
        # as a human gate.
        human_review_authority=ReviewAuthority.MISSING,
    )
    review_rounds = exc.rounds_used + 1
    review_api_calls = 2 * review_rounds
    artifact_paths = [
        str(source_snapshot_path),
        handoff_manifest_path,
        *retained_review_paths,
        record.outcome_markdown_path,
        record.outcome_audit_path,
    ]
    return MultiFamilyDevelopmentFamilyResult(
        question_family_id=branch.question_family_id,
        branch_id=branch.branch_id,
        status=status,
        record=record,
        artifact_paths=artifact_paths,
        api_attempts=review_api_calls,
        api_successes=review_api_calls,
        # This is an expected scientific terminal, not an infrastructure error. The typed status,
        # retained plan, and reviews carry the disposition without an "incomplete" diagnostic.
        error="",
    )


def _retained_review_terminal_details(
    status: FamilyDossierStatus,
    exc: DevelopmentRevisionTerminal,
) -> tuple[list[str], list[str]]:
    """Return public-safe retained plan/review details plus their authoritative file paths."""
    blockers = _revise_loop_blockers(status, exc)
    retained_paths: list[str] = []
    for path in (exc.owner_review_path, exc.independent_review_path):
        if path and Path(path).is_file():
            retained_paths.append(path)

    review_root = (
        Path(exc.owner_review_path).parent
        if exc.owner_review_path
        else (Path(exc.independent_review_path).parent if exc.independent_review_path else None)
    )
    if review_root is not None:
        plan_path = review_root / f"round_{exc.rounds_used}" / "plan_draft.yaml"
        if plan_path.is_file():
            plan = load_model(plan_path, PlanDraftMessage)
            retained_paths.append(str(plan_path))
            blockers.append(f"Retained plan summary: {plan.summary}")
            blockers.extend(
                f"Variant {entry.variant_id}: {entry.decision.value} — {entry.summary}"
                for entry in plan.variant_outcomes
            )
    if exc.owner_review_path and Path(exc.owner_review_path).is_file():
        owner_review = load_model(exc.owner_review_path, QuestionOwnerPlanReviewMessage)
        blockers.append(f"Question Owner: {owner_review.decision.value} — {owner_review.rationale}")
    if exc.independent_review_path and Path(exc.independent_review_path).is_file():
        independent_review = load_model(exc.independent_review_path, IndependentPlanReviewMessage)
        blockers.append(
            "Independent reviewer: "
            f"{independent_review.decision.value} — {independent_review.rationale}"
        )
    return blockers, list(dict.fromkeys(retained_paths))


def _revise_loop_blockers(
    status: FamilyDossierStatus, exc: DevelopmentRevisionTerminal
) -> list[str]:
    """Honest disposition lines for a revise-loop terminal; none is a mandatory human handoff."""
    blockers = [
        "Automated review did not grant accepted-plan authority; the plan and reviews are retained.",
        f"Owner review decision: {exc.owner_decision}; independent review decision: "
        f"{exc.independent_decision}.",
        f"Bounded revise-loop rounds used: {exc.rounds_used}.",
    ]
    if status == FamilyDossierStatus.REVISION_BUDGET_EXHAUSTED:
        blockers.append(
            "The per-family revise-round budget was reached without acceptance (honest terminal)."
        )
    elif status == FamilyDossierStatus.MATERIAL_REVISION_DEFERRED:
        blockers.append(
            "A material revision was detected; it is deferred pending renewed literature and a "
            "novelty recheck (Phase 5a) — not auto-completed and not a mandatory human handoff."
        )
        if isinstance(exc, DevelopmentMaterialRevisionDeferred) and exc.novelty_recheck_required:
            blockers.append(
                "A novelty recheck is required before this material revision may proceed."
            )
    elif status == FamilyDossierStatus.REVIEW_ESCALATED:
        blockers.append(
            "A reviewer returned human_review (escalate) — a rare honest terminal, human-optional, "
            "not a mandatory handoff."
        )
    elif status == FamilyDossierStatus.REJECTED:
        blockers.append("A reviewer rejected the plan (honest terminal).")
    if exc.required_changes:
        blockers.append("Requested changes: " + "; ".join(exc.required_changes))
    blockers.append("Downstream compatibility remains unavailable pending explicit authorization.")
    return blockers


def _create_branch(
    branch_manager: QuestionFamilyBranchManager,
    shortlisted: ShortlistedQuestionFamily,
) -> QuestionFamilyBranch:
    return branch_manager.create_branch(shortlisted, context_id=shortlisted.family.context_id)


def _scientific_source_snapshot(
    *,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    run_id: str,
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


def _imported_evidence_records(
    branch: QuestionFamilyBranch,
    import_manifest: PlannerArtifactImportManifest,
) -> list[QuestionFamilyInspectionEvidence]:
    """All inspection-evidence records the planner bundle imported (family + variant scope).

    Grounding derives from ALL of them: a variant-scoped sample inspection still means the dataset
    was sampled during this branch's planning.
    """
    imported = set(import_manifest.evidence_ids)
    return [evidence for evidence in branch.inspection_evidence if evidence.evidence_id in imported]


def _terminal_evidence_records(
    message: PlanningMessage,
    imported_evidence: list[QuestionFamilyInspectionEvidence],
) -> list[QuestionFamilyInspectionEvidence]:
    """Return the imported evidence actually cited by a rejection/escalation terminal.

    Terminal conclusions may be variant-only or may honestly cite no evidence. Keep the
    message's ordered evidence union rather than inventing a family-scoped anchor or attaching
    unrelated evidence that happened to be returned in the same planner bundle.
    """
    referenced_ids: list[str] = []
    for evidence_id in getattr(message, "blocking_evidence_ids", []):
        if evidence_id and evidence_id not in referenced_ids:
            referenced_ids.append(evidence_id)
    for outcome in getattr(message, "variant_outcomes", []):
        for evidence_id in outcome.evidence_ids:
            if evidence_id and evidence_id not in referenced_ids:
                referenced_ids.append(evidence_id)
    by_id = {evidence.evidence_id: evidence for evidence in imported_evidence}
    return [by_id[evidence_id] for evidence_id in referenced_ids if evidence_id in by_id]


def _bundle_outcome_kind(bundle: PlannerReturnedArtifactBundle) -> GenericFamilyOutcomeKind:
    if bundle.plan_draft_paths:
        return GenericFamilyOutcomeKind.PLAN
    if bundle.rejection_paths:
        return GenericFamilyOutcomeKind.REJECTION
    return GenericFamilyOutcomeKind.HUMAN_ESCALATION


def _load_planner_message(
    bundle: PlannerReturnedArtifactBundle,
    outcome_kind: GenericFamilyOutcomeKind,
) -> PlanningMessage:
    if outcome_kind == GenericFamilyOutcomeKind.PLAN:
        return load_model(bundle.plan_draft_paths[0], PlanDraftMessage)
    if outcome_kind == GenericFamilyOutcomeKind.REJECTION:
        return load_model(bundle.rejection_paths[0], BranchRejectionMessage)
    return _load_unique_human_escalation(bundle)


def _load_unique_human_escalation(
    bundle: PlannerReturnedArtifactBundle,
) -> HumanEscalationRequest:
    """Select the one typed escalation terminal without relying on dialogue path order.

    ``dialogue_paths`` may also contain valid non-terminal feasibility findings.  Real coding
    agents commonly write those before the root-level ``escalation.yaml``, so positional selection
    can misclassify a scientifically honest terminal as failed validation.  Message type identifies
    candidates; the full strict schema remains authoritative and zero/multiple terminals fail
    closed.
    """
    candidate_paths: list[str] = []
    for path in bundle.dialogue_paths:
        payload = load_data(path)
        if not isinstance(payload, dict) or payload.get("message_type") != (
            "human_escalation_request"
        ):
            continue
        candidate_paths.append(path)
    if len(candidate_paths) != 1:
        raise ValueError(
            "human_escalation outcome requires exactly one strict "
            f"HumanEscalationRequest terminal; found {len(candidate_paths)}"
        )
    return load_model(candidate_paths[0], HumanEscalationRequest)


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
            f"Development source snapshot preserves the dataset leverage hypothesis: "
            f"{variant.dataset_leverage_hypothesis} Actual grounding is "
            f"{grounding.value}."
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
            "Human review is optional and has not been imported.",
            "Real dataset-planner inspection remains required before serious dataset grounding.",
        ],
    )


def _rejection_outcome_packet(
    *,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    rejection: BranchRejectionMessage,
    evidence: list[QuestionFamilyInspectionEvidence],
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
    source_snapshot_digest: str,
    run_id: str,
    grounding: DatasetGroundingLevel,
) -> GenericFamilyBranchOutcomePacket:
    return GenericFamilyBranchOutcomePacket(
        outcome_packet_id=f"generic-family-outcome-rejection-{family.question_family_id}",
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_snapshot_id=source_snapshot.source_snapshot_id,
        source_snapshot_digest=source_snapshot_digest,
        dataset_grounding_level=grounding,
        dataset_claim_status=(
            DatasetClaimStatus.UNVERIFIED if evidence else DatasetClaimStatus.UNKNOWN
        ),
        outcome_kind=GenericFamilyOutcomeKind.REJECTION,
        # Preserve the planner's real rejection subtype (dataset_mismatch /
        # operationalization_failure / scientific_drift / insufficient_evidence /
        # low_scientific_value) instead of flattening every rejection to dataset_mismatch.
        decision=rejection.decision,
        summary=(
            f"Development-mode {rejection.decision.value} rejection for {family.title}. "
            "It supports a development rejection dossier only."
        ),
        family_scientific_summary=(
            f"{source_snapshot.family_summary} The shared tension is "
            f"{source_snapshot.shared_scientific_tension}"
        ),
        source_message_ids=[rejection.message_id],
        evidence_ids=[record.evidence_id for record in evidence],
        # Preserve the planner's per-variant rejection subtype, rationale, and scoped
        # evidence. A family terminal does not authorize flattening every sibling onto
        # the first family-scoped record.
        variant_outcomes=list(rejection.variant_outcomes),
        variant_scientific_outcomes=[
            _variant_scientific_outcome(variant, grounding=grounding)
            for variant in source_snapshot.variants
        ],
        rejection_message_id=rejection.message_id,
        limitations=[
            "Development-mode only.",
            f"Dataset grounding level: {grounding.value}.",
            "Human review is optional and has not been imported.",
        ],
    )


def _escalation_outcome_packet(
    *,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    escalation: HumanEscalationRequest,
    evidence: list[QuestionFamilyInspectionEvidence],
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
    source_snapshot_digest: str,
    run_id: str,
    grounding: DatasetGroundingLevel,
) -> GenericFamilyBranchOutcomePacket:
    return GenericFamilyBranchOutcomePacket(
        outcome_packet_id=f"generic-family-outcome-escalation-{family.question_family_id}",
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_snapshot_id=source_snapshot.source_snapshot_id,
        source_snapshot_digest=source_snapshot_digest,
        dataset_grounding_level=grounding,
        dataset_claim_status=(
            DatasetClaimStatus.UNVERIFIED if evidence else DatasetClaimStatus.UNKNOWN
        ),
        outcome_kind=GenericFamilyOutcomeKind.HUMAN_ESCALATION,
        decision=BranchDecisionKind.HUMAN_ESCALATION,
        summary=(
            f"Development-mode human-escalation outcome for {family.title}. "
            "It supports a development escalation dossier only."
        ),
        family_scientific_summary=(
            f"{source_snapshot.family_summary} The shared tension is "
            f"{source_snapshot.shared_scientific_tension}"
        ),
        source_message_ids=[escalation.message_id],
        evidence_ids=[record.evidence_id for record in evidence],
        variant_outcomes=list(escalation.variant_outcomes),
        variant_scientific_outcomes=[
            _variant_scientific_outcome(variant, grounding=grounding)
            for variant in source_snapshot.variants
        ],
        escalation_message_id=escalation.message_id,
        limitations=[
            "Development-mode only.",
            f"Dataset grounding level: {grounding.value}.",
            "Human review is optional and has not been imported.",
        ],
    )


def _development_review_input(
    *,
    branch: QuestionFamilyBranch,
    family: QuestionFamily,
    outcome: GenericFamilyBranchOutcomePacket,
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
    run_id: str,
    review_authority: ReviewAuthority,
) -> dict[str, object]:
    return {
        "run_id": run_id,
        "branch_id": branch.branch_id,
        "question_family_id": family.question_family_id,
        "source_outcome_packet_id": outcome.outcome_packet_id,
        "source_snapshot_id": source_snapshot.source_snapshot_id,
        "dataset_grounding_level": outcome.dataset_grounding_level.value,
        "review_mode": review_authority.value,
        "requested_decision": "accept_for_development_dossier",
        "r5_011_blocked": True,
    }


def _development_decision_packet(
    *,
    branch: QuestionFamilyBranch,
    outcome: GenericFamilyBranchOutcomePacket,
    run_id: str,
    input_digest: str,
    output_digest: str,
    dataset_grounding_level: DatasetGroundingLevel,
    review_authority: ReviewAuthority,
) -> GenericFamilyReviewDecisionPacket:
    return GenericFamilyReviewDecisionPacket(
        decision_packet_id=f"generic-development-review-decision-{branch.question_family_id}",
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_outcome_packet_id=outcome.outcome_packet_id,
        authority=review_authority,
        decision=GenericReviewDecisionValue.ACCEPT_FOR_DEVELOPMENT_DOSSIER,
        decision_summary="Automated review allows a development dossier only.",
        provider_id="local:automated-review",
        model_id="deterministic-automated-review",
        prompt_version="development_family_review/v1",
        session_id=f"automated-review-session-{branch.question_family_id}",
        input_digest=input_digest,
        output_digest=output_digest,
        dataset_grounding_level=dataset_grounding_level,
        dataset_claim_status=outcome.dataset_claim_status,
        development_dossier_rendering_allowed=True,
        development_dossier_generation_allowed=True,
    )


def _snapshot_from_payloads(
    *,
    branch_id: str,
    session_id: str,
    provider_id: str,
    model_id: str,
    prompt_version: str,
    input_payload: dict[str, object],
    output_payload: dict[str, object],
    output_schema: str,
) -> ScientificAgentSessionSnapshot:
    record = ScientificAgentTranscriptRecord(
        sequence=1,
        turn_id=_digest(f"{branch_id}:{session_id}:{prompt_version}")[:16],
        branch_id=branch_id,
        session_id=session_id,
        provider_id=provider_id,
        model_id=model_id,
        prompt_version=prompt_version,
        input_schema="dict",
        input_payload=input_payload,
        input_digest=scientific_agent_payload_digest(input_payload),
        output_schema=output_schema,
        output_payload=output_payload,
        output_digest=scientific_agent_payload_digest(output_payload),
        provider_response_id="local-deterministic",
    )
    return ScientificAgentSessionSnapshot(
        branch_id=branch_id,
        session_id=session_id,
        provider_id=provider_id,
        model_id=model_id,
        prompt_version=prompt_version,
        provider_session_id=session_id,
        provider_metadata={"provider": "local_deterministic"},
        transcript=[record],
    )


def _development_workspace(output_root: Path, *, run_id: str, branch_id: str) -> Path:
    return output_root / run_id / "branches" / branch_id / "planner" / R5_M1H_DEVELOPMENT_WORKSPACE


def _record_id(question_family_id: str, branch_id: str) -> str:
    digest = stable_hash({"question_family_id": question_family_id, "branch_id": branch_id})
    return f"family-dossier-record-{digest[:12]}"


def _digest(label: str) -> str:
    return stable_hash({"label": label})
