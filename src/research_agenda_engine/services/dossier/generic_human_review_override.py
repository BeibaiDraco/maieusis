from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from ...io import dump_data, load_data, load_model
from ...provenance import stable_hash
from ...schemas.generic_dossier import (
    GenericEndUserDossierAuditSidecar,
    GenericEndUserDossierManifest,
    GenericEndUserDossierMarkdownArtifact,
)
from ...schemas.generic_family_outcome import GenericFamilyBranchOutcomePacket
from ...schemas.generic_human_review_override import (
    GenericHumanReviewOverrideCompletionStatus,
    GenericHumanReviewOverrideDecision,
    GenericHumanReviewOverrideImportResult,
    GenericHumanReviewOverrideTemplate,
)
from ...schemas.generic_review_authority import (
    GenericFamilyReviewDecisionPacket,
    GenericReviewDecisionValue,
)
from ...schemas.generic_scientific_source import DatasetGroundingLevel
from ...schemas.multi_family_dossier import FamilyDossierOutputRecord, ReviewAuthority
from ...schemas.question_family_branch import QuestionFamilyBranch
from ..orchestration import QuestionFamilyBranchManager
from .multi_family_coordinator import import_end_user_dossier_record

GENERIC_HUMAN_REVIEW_OVERRIDE_WORKSPACE = "generic_human_review_override"
_SourceIdentityRecord = FamilyDossierOutputRecord | GenericHumanReviewOverrideTemplate


@dataclass(frozen=True)
class _OverrideDecisionMapping:
    branch_decision: GenericHumanReviewOverrideDecision
    review_decision: GenericReviewDecisionValue
    human_review_imported: bool
    allows_dossier_generation: bool
    serious_mode_importable: bool


def emit_generic_human_review_override_template(
    *,
    output_root: str | Path,
    run_id: str,
    record: FamilyDossierOutputRecord,
    outcome_packet_path: str | Path,
    review_decision_path: str | Path,
    end_user_manifest_path: str | Path,
    family_title: str,
) -> Path:
    """Emit a blank, digest-prefilled generic human-review template for one dossier."""

    if record.human_review_authority != ReviewAuthority.AUTOMATED:
        raise ValueError("generic human review override templates require automated records")
    output_root = Path(output_root)
    workspace = _override_workspace(output_root, run_id=run_id, branch_id=record.branch_id)
    outcome_packet = load_model(outcome_packet_path, GenericFamilyBranchOutcomePacket)
    review_decision = load_model(review_decision_path, GenericFamilyReviewDecisionPacket)
    end_user_manifest = load_model(end_user_manifest_path, GenericEndUserDossierManifest)
    _validate_source_identity(record=record, outcome=outcome_packet, decision=review_decision)
    _validate_manifest_identity(record=record, manifest=end_user_manifest)

    template = GenericHumanReviewOverrideTemplate(
        template_id=f"generic-human-review-template-{record.question_family_id}",
        run_id=run_id,
        branch_id=record.branch_id,
        question_family_id=record.question_family_id,
        context_id=record.context_id,
        owner_session_id=record.owner_session_id,
        family_title=family_title,
        source_authority=review_decision.authority,
        source_dataset_grounding_level=review_decision.dataset_grounding_level,
        source_outcome_packet_id=outcome_packet.outcome_packet_id,
        source_review_decision_packet_id=review_decision.decision_packet_id,
        source_outcome_packet_path=str(outcome_packet_path),
        source_outcome_packet_digest=stable_hash(outcome_packet.model_dump(mode="json")),
        source_review_decision_path=str(review_decision_path),
        source_review_decision_digest=stable_hash(review_decision.model_dump(mode="json")),
        source_end_user_manifest_path=str(end_user_manifest_path),
        source_end_user_manifest_digest=stable_hash(end_user_manifest.model_dump(mode="json")),
        source_end_user_dossier_path=end_user_manifest.end_user_dossier_path,
        source_end_user_dossier_digest=_markdown_digest(end_user_manifest.end_user_dossier_path),
        source_end_user_artifact_path=end_user_manifest.end_user_dossier_artifact_path,
        source_end_user_artifact_digest=_model_file_digest(
            end_user_manifest.end_user_dossier_artifact_path,
            GenericEndUserDossierMarkdownArtifact,
        ),
        source_audit_sidecar_path=end_user_manifest.audit_sidecar_path,
        source_audit_sidecar_digest=_model_file_digest(
            end_user_manifest.audit_sidecar_path,
            GenericEndUserDossierAuditSidecar,
        ),
    )
    path = workspace / "human_review_decision_template.yaml"
    dump_data(template, path)
    return path


def import_generic_human_review_override_decision(
    *,
    run_root: str | Path,
    decision_path: str | Path,
    repository_root: str | Path = Path("."),
) -> GenericHumanReviewOverrideImportResult:
    """Import one edited generic human-review template as a typed branch event.

    The event is recorded before any completed-record import is attempted. If the dossier lacks
    serious dataset grounding, completion is blocked with a result artifact instead of raising an
    uncaught validation error.
    """

    run_root = Path(run_root)
    repository_root = Path(repository_root)
    raw = load_data(decision_path)
    if not isinstance(raw, dict):
        raise ValueError("malformed generic human review override decision file")
    template = GenericHumanReviewOverrideTemplate.model_validate(raw)
    branch_decision = _coerce_human_decision(template.human_decision)
    if not template.reviewer_name:
        raise ValueError("generic human review override requires reviewer_name")

    manager = QuestionFamilyBranchManager(run_root, run_id=template.run_id)
    branch = manager.load_branch(template.branch_id)
    _validate_template_branch_identity(template, branch)

    outcome = load_model(
        _resolve_path(template.source_outcome_packet_path, repository_root),
        GenericFamilyBranchOutcomePacket,
    )
    source_decision = load_model(
        _resolve_path(template.source_review_decision_path, repository_root),
        GenericFamilyReviewDecisionPacket,
    )
    manifest = load_model(
        _resolve_path(template.source_end_user_manifest_path, repository_root),
        GenericEndUserDossierManifest,
    )
    _validate_template_source_identity(template, outcome, source_decision, manifest)
    _verify_prefilled_digests(template, repository_root=repository_root)

    mapping = _map_human_override_decision(
        branch_decision, grounding=source_decision.dataset_grounding_level
    )
    import_workspace = _override_workspace(
        run_root, run_id=template.run_id, branch_id=template.branch_id
    )
    packet = _human_decision_packet(
        template=template,
        source_decision=source_decision,
        mapping=mapping,
    )
    packet_path = import_workspace / "human_review_decision_packet.yaml"
    dump_data(packet, packet_path)
    packet_digest = stable_hash(packet.model_dump(mode="json"))
    reloaded = manager.record_human_review_decision(
        template.branch_id,
        human_review_import_id=packet.decision_packet_id,
        decision=mapping.branch_decision.value,
        artifact_digest=packet_digest,
    )
    event = reloaded.events[-1]

    completion_status = GenericHumanReviewOverrideCompletionStatus.NON_ACCEPT_DECISION_RECORDED
    completion_blocker = ""
    completed_record_path = ""
    if mapping.branch_decision == GenericHumanReviewOverrideDecision.ACCEPT_FOR_DOSSIER:
        if not source_decision.dataset_grounding_level.supports_serious_dataset_grounding:
            completion_status = (
                GenericHumanReviewOverrideCompletionStatus.BLOCKED_INSUFFICIENT_GROUNDING
            )
            completion_blocker = (
                "Human review decision recorded, but completed dossier import requires sample or "
                "full-local dataset grounding."
            )
        else:
            try:
                completed = import_end_user_dossier_record(
                    repository_root=repository_root,
                    run_root=run_root,
                    manifest_path=template.source_end_user_manifest_path,
                    family_title=template.family_title,
                )
            except ValueError as exc:
                if "sample or full-local dataset grounding" not in str(exc):
                    raise
                completion_status = (
                    GenericHumanReviewOverrideCompletionStatus.BLOCKED_INSUFFICIENT_GROUNDING
                )
                completion_blocker = (
                    "Human review decision recorded, but completed dossier import requires sample "
                    "or full-local dataset grounding."
                )
            else:
                completed_record_path = str(import_workspace / "completed_family_record.yaml")
                dump_data(completed, completed_record_path)
                completion_status = (
                    GenericHumanReviewOverrideCompletionStatus.COMPLETED_RECORD_CREATED
                )

    result_path = import_workspace / "human_review_import_result.yaml"
    result = GenericHumanReviewOverrideImportResult(
        import_result_id=f"generic-human-review-import-{template.question_family_id}",
        import_result_path=str(result_path),
        run_id=template.run_id,
        branch_id=template.branch_id,
        question_family_id=template.question_family_id,
        human_review_decision_packet_path=str(packet_path),
        human_review_decision_packet_digest=packet_digest,
        human_review_event_recorded=True,
        human_review_event_id=event.event_id,
        human_review_event_sequence=event.sequence,
        branch_decision=mapping.branch_decision,
        review_decision_value=mapping.review_decision.value,
        dataset_grounding_level=source_decision.dataset_grounding_level,
        completion_status=completion_status,
        completion_blocker=completion_blocker,
        completed_record_path=completed_record_path,
    )
    dump_data(result, result_path)
    return result


def _override_workspace(output_root: Path, *, run_id: str, branch_id: str) -> Path:
    return (
        output_root
        / run_id
        / "branches"
        / branch_id
        / "planner"
        / GENERIC_HUMAN_REVIEW_OVERRIDE_WORKSPACE
    )


def _coerce_human_decision(value: object) -> GenericHumanReviewOverrideDecision:
    text = str(value).strip()
    if not text:
        raise ValueError("generic human review override requires human_decision")
    try:
        return GenericHumanReviewOverrideDecision(text)
    except ValueError as exc:
        raise ValueError(f"unsupported generic human review override decision: {text}") from exc


def _map_human_override_decision(
    decision: GenericHumanReviewOverrideDecision,
    *,
    grounding: DatasetGroundingLevel,
) -> _OverrideDecisionMapping:
    if decision == GenericHumanReviewOverrideDecision.ACCEPT_FOR_DOSSIER:
        if grounding.supports_serious_dataset_grounding:
            return _OverrideDecisionMapping(
                branch_decision=decision,
                review_decision=GenericReviewDecisionValue.ACCEPT_FOR_SERIOUS_DOSSIER,
                human_review_imported=True,
                allows_dossier_generation=True,
                serious_mode_importable=True,
            )
        return _OverrideDecisionMapping(
            branch_decision=decision,
            review_decision=GenericReviewDecisionValue.ACCEPT_FOR_DEVELOPMENT_DOSSIER,
            human_review_imported=True,
            allows_dossier_generation=True,
            serious_mode_importable=False,
        )
    if decision == GenericHumanReviewOverrideDecision.REVISION_REQUIRED:
        return _OverrideDecisionMapping(
            branch_decision=decision,
            review_decision=GenericReviewDecisionValue.REVISION_REQUIRED,
            human_review_imported=False,
            allows_dossier_generation=False,
            serious_mode_importable=False,
        )
    if decision == GenericHumanReviewOverrideDecision.REJECT:
        return _OverrideDecisionMapping(
            branch_decision=decision,
            review_decision=GenericReviewDecisionValue.REJECT,
            human_review_imported=False,
            allows_dossier_generation=False,
            serious_mode_importable=False,
        )
    return _OverrideDecisionMapping(
        branch_decision=decision,
        review_decision=GenericReviewDecisionValue.HUMAN_ESCALATION,
        human_review_imported=False,
        allows_dossier_generation=False,
        serious_mode_importable=False,
    )


def _human_decision_packet(
    *,
    template: GenericHumanReviewOverrideTemplate,
    source_decision: GenericFamilyReviewDecisionPacket,
    mapping: _OverrideDecisionMapping,
) -> GenericFamilyReviewDecisionPacket:
    input_digest = stable_hash(
        {
            "template_id": template.template_id,
            "source_review_decision_digest": template.source_review_decision_digest,
            "source_end_user_manifest_digest": template.source_end_user_manifest_digest,
        }
    )
    output_digest = stable_hash(
        {
            "human_decision": mapping.branch_decision.value,
            "reviewer_name": template.reviewer_name,
            "reviewer_notes": template.reviewer_notes,
            "required_changes": template.required_changes,
        }
    )
    return GenericFamilyReviewDecisionPacket(
        decision_packet_id=f"generic-human-review-decision-{stable_hash(output_digest)[:12]}",
        run_id=template.run_id,
        branch_id=template.branch_id,
        question_family_id=template.question_family_id,
        context_id=template.context_id,
        owner_session_id=template.owner_session_id,
        source_outcome_packet_id=template.source_outcome_packet_id,
        authority=ReviewAuthority.REAL_HUMAN_EXPERT,
        decision=mapping.review_decision,
        decision_summary=_decision_summary(template),
        reviewer_name=template.reviewer_name,
        input_digest=input_digest,
        output_digest=output_digest,
        dataset_grounding_level=source_decision.dataset_grounding_level,
        development_dossier_rendering_allowed=False,
        development_dossier_generation_allowed=False,
        human_review_imported=mapping.human_review_imported,
        allows_dossier_generation=mapping.allows_dossier_generation,
        serious_mode_importable=mapping.serious_mode_importable,
    )


def _decision_summary(template: GenericHumanReviewOverrideTemplate) -> str:
    parts = [
        f"Human override decision: {template.human_decision}.",
        f"Reviewer: {template.reviewer_name}.",
    ]
    if template.reviewer_notes:
        parts.append(f"Notes: {template.reviewer_notes}")
    if template.required_changes:
        parts.append("Required changes: " + "; ".join(template.required_changes))
    return " ".join(parts)


def _validate_template_branch_identity(
    template: GenericHumanReviewOverrideTemplate,
    branch: QuestionFamilyBranch,
) -> None:
    expected = {
        "branch_id": branch.branch_id,
        "question_family_id": branch.question_family_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
    }
    mismatched = [
        field
        for field, expected_value in expected.items()
        if getattr(template, field) != expected_value
    ]
    if mismatched:
        raise ValueError(
            "generic human review override references another " + ", ".join(mismatched)
        )


def _validate_template_source_identity(
    template: GenericHumanReviewOverrideTemplate,
    outcome: GenericFamilyBranchOutcomePacket,
    decision: GenericFamilyReviewDecisionPacket,
    manifest: GenericEndUserDossierManifest,
) -> None:
    _validate_source_identity(record=template, outcome=outcome, decision=decision)
    _validate_manifest_identity(record=template, manifest=manifest)
    if decision.authority != ReviewAuthority.AUTOMATED:
        raise ValueError("generic human review override source decision must be automated")
    if decision.human_review_imported or decision.allows_dossier_generation:
        raise ValueError("generic human review override source decision already imports review")
    if decision.decision == GenericReviewDecisionValue.ACCEPT_FOR_SERIOUS_DOSSIER:
        raise ValueError("generic human review override source decision cannot already be serious")
    if template.source_outcome_packet_id != outcome.outcome_packet_id:
        raise ValueError("generic human review override outcome packet mismatch")
    if template.source_review_decision_packet_id != decision.decision_packet_id:
        raise ValueError("generic human review override decision packet mismatch")


def _validate_source_identity(
    *,
    record: _SourceIdentityRecord,
    outcome: GenericFamilyBranchOutcomePacket,
    decision: GenericFamilyReviewDecisionPacket,
) -> None:
    expected = {
        "branch_id": record.branch_id,
        "question_family_id": record.question_family_id,
        "context_id": record.context_id,
        "owner_session_id": record.owner_session_id,
    }
    mismatched = [
        field
        for field, expected_value in expected.items()
        if getattr(outcome, field) != expected_value or getattr(decision, field) != expected_value
    ]
    if mismatched:
        raise ValueError(
            "generic human review override source references another " + ", ".join(mismatched)
        )
    if decision.source_outcome_packet_id != outcome.outcome_packet_id:
        raise ValueError("generic human review override source outcome mismatch")


def _validate_manifest_identity(
    *,
    record: _SourceIdentityRecord,
    manifest: GenericEndUserDossierManifest,
) -> None:
    run_id = (
        record.run_id if isinstance(record, GenericHumanReviewOverrideTemplate) else manifest.run_id
    )
    expected = {
        "run_id": run_id,
        "branch_id": record.branch_id,
        "question_family_id": record.question_family_id,
        "context_id": record.context_id,
        "owner_session_id": record.owner_session_id,
    }
    mismatched = [
        field
        for field, expected_value in expected.items()
        if getattr(manifest, field) != expected_value
    ]
    if mismatched:
        raise ValueError(
            "generic human review override manifest references another " + ", ".join(mismatched)
        )


def _verify_prefilled_digests(
    template: GenericHumanReviewOverrideTemplate,
    *,
    repository_root: Path,
) -> None:
    checks = {
        "source_outcome_packet_digest": stable_hash(
            load_model(
                _resolve_path(template.source_outcome_packet_path, repository_root),
                GenericFamilyBranchOutcomePacket,
            ).model_dump(mode="json")
        ),
        "source_review_decision_digest": stable_hash(
            load_model(
                _resolve_path(template.source_review_decision_path, repository_root),
                GenericFamilyReviewDecisionPacket,
            ).model_dump(mode="json")
        ),
        "source_end_user_manifest_digest": stable_hash(
            load_model(
                _resolve_path(template.source_end_user_manifest_path, repository_root),
                GenericEndUserDossierManifest,
            ).model_dump(mode="json")
        ),
        "source_end_user_dossier_digest": _markdown_digest(
            _resolve_path(template.source_end_user_dossier_path, repository_root)
        ),
        "source_end_user_artifact_digest": _model_file_digest(
            _resolve_path(template.source_end_user_artifact_path, repository_root),
            GenericEndUserDossierMarkdownArtifact,
        ),
        "source_audit_sidecar_digest": _model_file_digest(
            _resolve_path(template.source_audit_sidecar_path, repository_root),
            GenericEndUserDossierAuditSidecar,
        ),
    }
    mismatched = [field for field, actual in checks.items() if getattr(template, field) != actual]
    if mismatched:
        raise ValueError(
            "generic human review override artifact digest mismatch: " + ", ".join(mismatched)
        )


def _resolve_path(path: str | Path, repository_root: Path) -> Path:
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved
    return repository_root / resolved


def _markdown_digest(path: str | Path) -> str:
    return stable_hash(Path(path).read_text(encoding="utf-8"))


def _model_file_digest(path: str | Path, model_type: type[BaseModel]) -> str:
    model: BaseModel = load_model(path, model_type)
    return stable_hash(model.model_dump(mode="json"))
