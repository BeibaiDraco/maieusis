from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from ...io import load_data, load_model
from ...provenance import stable_hash
from ...schemas.planner_probe import ConstructProbeMap
from ...schemas.planner_run import (
    CodingAgentRunRecord,
    CodingAgentRunStatus,
    PlannerArtifactImportManifest,
    PlannerArtifactRepairLedger,
    PlannerReturnedArtifactBundle,
)
from ...schemas.question_family_branch import (
    QuestionFamilyBranch,
    QuestionFamilyBranchState,
    QuestionFamilyInspectionEvidence,
    inspection_evidence_identity_digest,
)
from ..orchestration import QuestionFamilyBranchManager
from .confined_workspace_io import (
    assert_confined_write_target,
    atomic_write_confined_model,
)
from .dataset_planner_packet import validate_planner_artifacts
from .evidence_claims import require_planner_evidence_unverified
from .planner_boundaries import assert_planner_boundary_safe
from .planner_failures import HardFamilyIntegrityViolation


def import_returned_planner_artifacts(
    branch_manager: QuestionFamilyBranchManager,
    bundle: PlannerReturnedArtifactBundle | dict[str, Any],
) -> PlannerArtifactImportManifest:
    resolved_bundle = (
        bundle
        if isinstance(bundle, PlannerReturnedArtifactBundle)
        else PlannerReturnedArtifactBundle.model_validate(bundle)
    )
    branch = branch_manager.load_branch(resolved_bundle.branch_id)
    _validate_bundle_identity(branch_manager, branch, resolved_bundle)
    expected_workspace = _bind_bundle_to_canonical_workspace(
        branch_manager,
        branch,
        resolved_bundle,
    )
    validation_report_path = _validation_report_path(resolved_bundle)
    manifest_path = Path(resolved_bundle.planner_workspace) / "artifact_import_manifest.yaml"
    # Both files are trusted-host products written after planner-controlled bytes exist.
    # Preflight both before any validation report or branch event is persisted so an
    # agent-planted alias cannot create a partial import transaction.
    assert_confined_write_target(
        workspace=expected_workspace,
        path=validation_report_path,
    )
    assert_confined_write_target(
        workspace=expected_workspace,
        path=manifest_path,
    )
    if not Path(resolved_bundle.run_trace_path).is_file():
        raise ValueError("planner returned artifact bundle is missing run trace")
    _validate_existing_paths(resolved_bundle)
    run_record = load_model(resolved_bundle.run_trace_path, CodingAgentRunRecord)
    _validate_run_record(branch, branch_manager.run_id, resolved_bundle, run_record)
    presentation_repair_ledger_digest = _validate_presentation_repair_audit(
        branch_manager,
        branch,
        resolved_bundle,
        expected_workspace=expected_workspace,
    )

    evidence_items = [
        load_model(path, QuestionFamilyInspectionEvidence)
        for path in resolved_bundle.evidence_paths
    ]
    if not evidence_items and resolved_bundle.plan_draft_paths:
        raise ValueError("a returned plan requires inspection evidence")
    _validate_evidence_items(branch, evidence_items)
    construct_probe_maps = [
        load_model(path, ConstructProbeMap) for path in resolved_bundle.construct_probe_map_paths
    ]
    _assert_output_payloads_planning_only(resolved_bundle)

    evidence_paths: list[str | Path] = list(resolved_bundle.evidence_paths)
    guarded_outputs = _guarded_output_payloads(resolved_bundle)
    report = validate_planner_artifacts(
        branch,
        run_id=branch_manager.run_id,
        evidence_paths=evidence_paths,
        construct_probe_map_paths=list(resolved_bundle.construct_probe_map_paths),
        planner_outputs=guarded_outputs,
        checked_paths=list(resolved_bundle.all_paths),
        planner_workspace=resolved_bundle.planner_workspace,
        require_typed_planner_outputs=True,
        # Evidence-only partial imports are a supported planning-state operation. Once any
        # dialogue/terminal output is returned, however, the bundle is a closure surface and must
        # contain exactly one typed terminal; a feasibility-only or conflicting surface fails.
        require_exactly_one_terminal=bool(guarded_outputs),
    )
    if resolved_bundle.host_repair_notes:
        report.warnings = list(
            dict.fromkeys([*report.warnings, *resolved_bundle.host_repair_notes])
        )
    atomic_write_confined_model(
        report,
        workspace=expected_workspace,
        path=validation_report_path,
    )
    if report.errors:
        raise ValueError("planner artifact import validation failed: " + "; ".join(report.errors))

    imported_event_ids: list[str] = []
    imported_evidence_ids: list[str] = []
    branch = branch_manager.load_branch(branch.branch_id)
    existing_evidence = {item.evidence_id: item for item in branch.inspection_evidence}
    for evidence in evidence_items:
        if evidence.evidence_id in existing_evidence:
            _assert_same_evidence(existing_evidence[evidence.evidence_id], evidence)
        else:
            updated = branch_manager.record_inspection_evidence(
                branch.branch_id,
                evidence,
                provider_id=run_record.planner_adapter,
                model_id=run_record.planner_identity,
                session_id=run_record.run_record_id,
                prompt_version=run_record.prompt_version,
                input_digest=run_record.handoff_digest,
                output_digest=run_record.transcript_digest
                or stable_hash(evidence.model_dump(mode="json")),
            )
            imported_event_ids.append(updated.events[-1].event_id)
            branch = updated
            existing_evidence[evidence.evidence_id] = evidence
        imported_evidence_ids.append(evidence.evidence_id)

    validation_report_digest = stable_hash(report.model_dump(mode="json"))
    manifest = PlannerArtifactImportManifest(
        import_id=f"planner-artifact-import-{stable_hash({'bundle': resolved_bundle.bundle_id, 'evidence': imported_evidence_ids})[:12]}",
        bundle_id=resolved_bundle.bundle_id,
        run_record_id=run_record.run_record_id,
        run_id=branch_manager.run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        evidence_ids=sorted(imported_evidence_ids),
        construct_probe_map_ids=sorted(
            probe_map.construct_probe_id for probe_map in construct_probe_maps
        ),
        imported_event_ids=imported_event_ids,
        # `artifact_paths`, deliberately NOT `all_paths`. The repair-audit files in the other half
        # of `all_paths` are described by their own schema as "private audit files, intentionally
        # excluded from ordinary artifact projection" (schemas/planner_run.py), and no supported
        # model type can parse them -- so listing them here guaranteed that any family needing a
        # lossless shape repair hit the hardest terminal in the system. Measured: 1 of 57 planner
        # branches produced a repair-audit directory, and it is the only hard-integrity terminal
        # in the live corpus, closed with nothing retained while both of its completed reviews sat
        # unread on disk. Their integrity is not weakened by this: the repair ledger is separately
        # hard-validated at import with per-record sha256 over both raw and canonical payloads,
        # and bound here by `presentation_repair_ledger_digest`.
        checked_paths=sorted(
            {
                str(Path(path))
                for path in (*resolved_bundle.artifact_paths, str(validation_report_path))
            }
        ),
        validation_report_digest=validation_report_digest,
        manifest_path=str(manifest_path),
        presentation_repair_ledger_digest=presentation_repair_ledger_digest,
    )
    atomic_write_confined_model(
        manifest,
        workspace=expected_workspace,
        path=manifest_path,
    )
    return manifest


def _validate_bundle_identity(
    branch_manager: QuestionFamilyBranchManager,
    branch: QuestionFamilyBranch,
    bundle: PlannerReturnedArtifactBundle,
) -> None:
    if branch.state != QuestionFamilyBranchState.PLANNER_INSPECTING:
        raise HardFamilyIntegrityViolation(
            "planner artifact import requires the branch-local planner_started state"
        )
    expected = {
        "run_id": branch_manager.run_id,
        "branch_id": branch.branch_id,
        "question_family_id": branch.question_family_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
    }
    mismatched = [
        field
        for field, expected_value in expected.items()
        if getattr(bundle, field) != expected_value
    ]
    if mismatched:
        raise HardFamilyIntegrityViolation(
            "planner returned artifact bundle references another " + ", ".join(mismatched)
        )


def _bind_bundle_to_canonical_workspace(
    branch_manager: QuestionFamilyBranchManager,
    branch: QuestionFamilyBranch,
    bundle: PlannerReturnedArtifactBundle,
) -> Path:
    """Bind the self-described bundle root before opening any returned artifact."""

    expected = (
        branch_manager.root / branch_manager.run_id / "branches" / branch.branch_id / "planner"
    )
    expected_resolved = expected.resolve(strict=False)
    supplied = Path(bundle.planner_workspace)
    if supplied.resolve(strict=False) != expected_resolved or supplied.is_symlink():
        raise HardFamilyIntegrityViolation(
            "planner returned artifact bundle uses a non-canonical branch workspace"
        )

    lexical_root = Path(os.path.abspath(expected))
    for raw_path in bundle.all_paths:
        path = Path(raw_path)
        lexical_path = Path(os.path.abspath(path))
        try:
            relative = lexical_path.relative_to(lexical_root)
        except ValueError as exc:
            raise HardFamilyIntegrityViolation(
                "planner returned artifact escaped the canonical branch workspace"
            ) from exc
        resolved = path.resolve(strict=False)
        if resolved != expected_resolved and expected_resolved not in resolved.parents:
            raise HardFamilyIntegrityViolation(
                "planner returned artifact escaped the canonical branch workspace"
            )
        cursor = lexical_root
        for component in relative.parts:
            cursor /= component
            if cursor.is_symlink():
                raise HardFamilyIntegrityViolation(
                    "planner returned artifact path contains a symlink"
                )
    return expected_resolved


def _validate_run_record(
    branch: QuestionFamilyBranch,
    run_id: str,
    bundle: PlannerReturnedArtifactBundle,
    run_record: CodingAgentRunRecord,
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
        raise HardFamilyIntegrityViolation(
            "planner run record references another " + ", ".join(mismatched)
        )
    if run_record.status != CodingAgentRunStatus.RETURNED:
        raise ValueError("planner run record must have returned status")
    if run_record.source_tree_mutation_detected:
        raise HardFamilyIntegrityViolation("planner run record reports source-tree mutation")
    if (
        run_record.source_tree_before_digest
        and run_record.source_tree_after_digest
        and run_record.source_tree_before_digest != run_record.source_tree_after_digest
    ):
        raise HardFamilyIntegrityViolation("planner run record source-tree digest changed")


def _validate_existing_paths(bundle: PlannerReturnedArtifactBundle) -> None:
    missing = [
        path
        for path in (
            bundle.run_trace_path,
            *bundle.evidence_paths,
            *bundle.construct_probe_map_paths,
            *bundle.dialogue_paths,
            *bundle.plan_draft_paths,
            *bundle.rejection_paths,
            *bundle.repair_audit_paths,
        )
        if not Path(path).is_file()
    ]
    if missing:
        raise ValueError(
            "planner returned artifact bundle references missing paths: " + ", ".join(missing)
        )


def _validate_presentation_repair_audit(
    branch_manager: QuestionFamilyBranchManager,
    branch: QuestionFamilyBranch,
    bundle: PlannerReturnedArtifactBundle,
    *,
    expected_workspace: Path,
) -> str:
    ledger_path = bundle.presentation_repair_ledger_path
    raw_paths = set(bundle.presentation_repair_raw_paths)
    if not ledger_path:
        if raw_paths:
            raise HardFamilyIntegrityViolation(
                "planner presentation repair snapshots lack a typed repair ledger"
            )
        return ""

    ledger = load_model(ledger_path, PlannerArtifactRepairLedger)
    if (
        ledger.run_id != branch_manager.run_id
        or ledger.branch_id != branch.branch_id
        or Path(ledger.planner_workspace).resolve(strict=False) != expected_workspace
    ):
        raise HardFamilyIntegrityViolation(
            "planner presentation repair ledger identity or workspace mismatch"
        )
    returned_payload_paths = {
        *bundle.evidence_paths,
        *bundle.construct_probe_map_paths,
        *bundle.dialogue_paths,
        *bundle.plan_draft_paths,
        *bundle.rejection_paths,
    }
    ledger_raw_paths = {record.raw_snapshot_path for record in ledger.records}
    if ledger_raw_paths != raw_paths:
        raise HardFamilyIntegrityViolation(
            "planner presentation repair ledger does not cover exactly its raw snapshots"
        )
    for record in ledger.records:
        if record.artifact_path not in returned_payload_paths:
            raise HardFamilyIntegrityViolation(
                "planner presentation repair ledger references an unreturned artifact"
            )
        raw_digest = hashlib.sha256(Path(record.raw_snapshot_path).read_bytes()).hexdigest()
        canonical_digest = hashlib.sha256(Path(record.artifact_path).read_bytes()).hexdigest()
        if raw_digest != record.raw_digest or canonical_digest != record.canonical_digest:
            raise HardFamilyIntegrityViolation("planner presentation repair ledger digest mismatch")
    return hashlib.sha256(Path(ledger_path).read_bytes()).hexdigest()


def _validate_evidence_items(
    branch: QuestionFamilyBranch,
    evidence_items: list[QuestionFamilyInspectionEvidence],
) -> None:
    seen: set[str] = set()
    for evidence in evidence_items:
        if evidence.evidence_id in seen:
            raise ValueError("planner artifact import contains duplicate evidence_id")
        seen.add(evidence.evidence_id)
        if evidence.branch_id != branch.branch_id:
            raise HardFamilyIntegrityViolation("inspection evidence references another branch")
        if evidence.question_family_id != branch.question_family_id:
            raise HardFamilyIntegrityViolation("inspection evidence references another family")
        require_planner_evidence_unverified(evidence)
        assert_planner_boundary_safe(
            evidence.model_dump(mode="json"),
            context="inspection evidence",
        )


def _assert_output_payloads_planning_only(bundle: PlannerReturnedArtifactBundle) -> None:
    for payload in _guarded_output_payloads(bundle):
        assert_planner_boundary_safe(payload, context="planner returned artifact")


def _guarded_output_payloads(bundle: PlannerReturnedArtifactBundle) -> list[Any]:
    return [
        _load_guard_payload(path)
        for path in (
            *bundle.dialogue_paths,
            *bundle.plan_draft_paths,
            *bundle.rejection_paths,
        )
    ]


def _load_guard_payload(path: str) -> Any:
    resolved = Path(path)
    if resolved.suffix.lower() in {".yaml", ".yml", ".json"}:
        return load_data(resolved)
    return resolved.read_text(encoding="utf-8")


def _validation_report_path(bundle: PlannerReturnedArtifactBundle) -> Path:
    if bundle.validation_report_path:
        return Path(bundle.validation_report_path)
    return Path(bundle.planner_workspace) / "validation_report.yaml"


def _assert_same_evidence(
    existing: QuestionFamilyInspectionEvidence,
    returned: QuestionFamilyInspectionEvidence,
) -> None:
    """A replan returning evidence the branch already holds must return the SAME evidence.

    Compared by identity digest rather than by full model dump, for the reason spelled out in
    `inspection_evidence_identity_digest`: on a replan the returned record is a re-read of the
    planner's own file, which omits `created_at`, so the field is stamped at load time and can never
    equal the stored copy. This check raises `HardFamilyIntegrityViolation` -- a burn-class terminal
    -- and it had exactly the same timestamp defect as the collect-side check. It has never fired
    only because collect refused first.
    """
    if inspection_evidence_identity_digest(existing) != inspection_evidence_identity_digest(
        returned
    ):
        raise HardFamilyIntegrityViolation(
            "returned evidence differs from already recorded branch evidence"
        )
