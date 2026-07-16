from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from ...io import dump_data, load_model
from ...provenance import stable_hash
from ...providers.scientific_agents import (
    ScientificAgentSessionSnapshot,
    ScientificAgentTranscriptRecord,
    scientific_agent_payload_digest,
)
from ...schemas.analysis_plan import AnalysisPlan
from ...schemas.dossier_closure import DossierClosureDiagnostic, DossierClosureOutcome
from ...schemas.generic_dossier import (
    GenericDossierCitationLedger,
    GenericDossierClaim,
    GenericDossierClaimScope,
    GenericDossierManifest,
    GenericDossierMarkdownArtifact,
    GenericDossierRenderManifest,
    GenericDossierSection,
    GenericDossierSourceRef,
    GenericDossierSourceType,
    GenericDossierWriterInput,
    GenericDossierWritingPacket,
    GenericEndUserDossierAuditBinding,
    GenericEndUserDossierAuditSidecar,
    GenericEndUserDossierManifest,
    GenericEndUserDossierMarkdownArtifact,
)
from ...schemas.generic_family_outcome import (
    GenericFamilyBranchOutcomePacket,
    GenericFamilyOutcomeKind,
    GenericVariantScientificOutcome,
    validate_generic_family_outcome_packet,
)
from ...schemas.generic_review_authority import (
    GenericFamilyReviewDecisionPacket,
    GenericReviewDecisionValue,
)
from ...schemas.generic_scientific_source import (
    DatasetGroundingLevel,
    QuestionFamilyScientificSourceSnapshot,
)
from ...schemas.multi_family_dossier import ReviewAuthority
from ...schemas.question_family_branch import (
    QuestionFamilyBranch,
    QuestionFamilyBranchEventType,
)
from ...schemas.stage_receipt import FailureClass
from ..orchestration import QuestionFamilyBranchManager
from .public_text_guard import find_public_markdown_jargon

GENERIC_SCIENTIFIC_DOSSIER_WORKSPACE = "generic_scientific_dossier"
GENERIC_SCIENTIFIC_DOSSIER_RENDERED_WORKSPACE = "generic_scientific_dossier_rendered"
GENERIC_END_USER_SCIENTIFIC_DOSSIER_WORKSPACE = "generic_end_user_scientific_dossier"
GENERIC_SOURCE_SNAPSHOT_FILENAME = "scientific_source_snapshot.yaml"
GENERIC_DOSSIER_WRITER_PROMPT_VERSION = "generic_dossier_writer/v1"
GENERIC_END_USER_DOSSIER_TRANSLATOR_PROMPT_VERSION = "generic_dossier_end_user_translator/v1"
GENERIC_DOSSIER_RENDERER_PROVIDER_ID = "local:generic-dossier-renderer"
GENERIC_DOSSIER_RENDERER_MODEL_ID = "deterministic-generic-dossier-renderer"
GENERIC_END_USER_TRANSLATOR_PROVIDER_ID = "local:generic-end-user-translator"
GENERIC_END_USER_TRANSLATOR_MODEL_ID = "deterministic-generic-end-user-translator"
DOSSIER_CLOSURE_DIAGNOSTIC_FILENAME = "dossier_closure_diagnostic.yaml"

_PLACEHOLDER_PUBLIC_PHRASES = (
    "this branch-local item",
    "remains separately reviewed",
    "development planning path",
    "preserves its sibling distinction",
    "generic dossier rendering",
)
_GENERIC_PUBLIC_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}


class GenericDossierPipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    branch_id: str
    question_family_id: str
    writing_workspace: str
    render_workspace: str
    end_user_workspace: str
    dossier_writing_packet_path: str
    citation_ledger_path: str
    dossier_skeleton_path: str
    writing_manifest_path: str
    machine_dossier_path: str
    machine_dossier_artifact_path: str
    render_manifest_path: str
    writer_session_snapshot_path: str
    end_user_dossier_path: str
    end_user_dossier_artifact_path: str
    audit_sidecar_path: str
    end_user_manifest_path: str
    translator_session_snapshot_path: str
    packet_prepared_event_id: str
    machine_rendered_event_id: str
    end_user_rendered_event_id: str


class DossierClosureError(ValueError):
    """Expected closure failure with an already-persisted typed diagnostic."""

    def __init__(self, message: str, *, diagnostic_path: Path) -> None:
        super().__init__(message)
        self.diagnostic_path = diagnostic_path


class PublicDossierRevisionRequired(DossierClosureError):
    """Accepted machine work exists, but its public rendering must be revised."""


class DossierProvenanceIntegrityFailure(DossierClosureError):
    """Strict dossier input bindings failed without repair or ID substitution."""


class _DossierInputMismatch(ValueError):
    def __init__(
        self,
        message: str,
        *,
        errors: list[str],
        observed: dict[str, str] | None = None,
        expected: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.errors = errors
        self.observed = observed or {}
        self.expected = expected or {}


def run_generic_development_dossier_pipeline(
    *,
    output_root: str | Path,
    run_id: str,
    branch_id: str,
    outcome_packet: GenericFamilyBranchOutcomePacket | dict[str, object],
    review_decision: GenericFamilyReviewDecisionPacket | dict[str, object],
    source_snapshot: QuestionFamilyScientificSourceSnapshot | dict[str, object],
    family_title: str,
    family_summary: str,
) -> GenericDossierPipelineResult:
    """Render a generic development-mode A/B/D dossier stack for one family branch."""

    packet_result = prepare_generic_dossier_writing_packet(
        output_root=output_root,
        run_id=run_id,
        branch_id=branch_id,
        outcome_packet=outcome_packet,
        review_decision=review_decision,
        source_snapshot=source_snapshot,
        family_title=family_title,
        family_summary=family_summary,
    )
    render_result = render_generic_machine_dossier(
        output_root=output_root,
        run_id=run_id,
        branch_id=branch_id,
        writing_manifest_path=packet_result.writing_manifest_path,
    )
    end_user_result = render_generic_end_user_dossier(
        output_root=output_root,
        run_id=run_id,
        branch_id=branch_id,
        render_manifest_path=render_result.render_manifest_path,
    )
    return GenericDossierPipelineResult(
        run_id=run_id,
        branch_id=branch_id,
        question_family_id=packet_result.question_family_id,
        writing_workspace=packet_result.writing_workspace,
        render_workspace=render_result.render_workspace,
        end_user_workspace=end_user_result.end_user_workspace,
        dossier_writing_packet_path=packet_result.dossier_writing_packet_path,
        citation_ledger_path=packet_result.citation_ledger_path,
        dossier_skeleton_path=packet_result.dossier_skeleton_path,
        writing_manifest_path=packet_result.writing_manifest_path,
        machine_dossier_path=render_result.machine_dossier_path,
        machine_dossier_artifact_path=render_result.machine_dossier_artifact_path,
        render_manifest_path=render_result.render_manifest_path,
        writer_session_snapshot_path=render_result.writer_session_snapshot_path,
        end_user_dossier_path=end_user_result.end_user_dossier_path,
        end_user_dossier_artifact_path=end_user_result.end_user_dossier_artifact_path,
        audit_sidecar_path=end_user_result.audit_sidecar_path,
        end_user_manifest_path=end_user_result.end_user_manifest_path,
        translator_session_snapshot_path=end_user_result.translator_session_snapshot_path,
        packet_prepared_event_id=packet_result.packet_prepared_event_id,
        machine_rendered_event_id=render_result.machine_rendered_event_id,
        end_user_rendered_event_id=end_user_result.end_user_rendered_event_id,
    )


class GenericDossierPacketResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    branch_id: str
    question_family_id: str
    writing_workspace: str
    dossier_writing_packet_path: str
    citation_ledger_path: str
    dossier_skeleton_path: str
    writing_manifest_path: str
    packet_prepared_event_id: str


def prepare_generic_dossier_writing_packet(
    *,
    output_root: str | Path,
    run_id: str,
    branch_id: str,
    outcome_packet: GenericFamilyBranchOutcomePacket | dict[str, object],
    review_decision: GenericFamilyReviewDecisionPacket | dict[str, object],
    source_snapshot: QuestionFamilyScientificSourceSnapshot | dict[str, object],
    family_title: str,
    family_summary: str,
) -> GenericDossierPacketResult:
    manager = QuestionFamilyBranchManager(output_root, run_id=run_id)
    branch = manager.load_branch(branch_id)
    workspace = _workspace(
        output_root,
        run_id=run_id,
        branch_id=branch_id,
        name=GENERIC_SCIENTIFIC_DOSSIER_WORKSPACE,
    )
    workspace.mkdir(parents=True, exist_ok=True)
    # Keep the caller's exact input before strict construction. A foreign binding must remain
    # inspectable and must never be normalized into an apparently valid branch-local packet.
    dump_data(_jsonable_external_input(outcome_packet), workspace / "source_outcome_packet.yaml")
    dump_data(_jsonable_external_input(review_decision), workspace / "source_review_decision.yaml")
    dump_data(
        _jsonable_external_input(source_snapshot), workspace / GENERIC_SOURCE_SNAPSHOT_FILENAME
    )
    try:
        outcome = (
            outcome_packet
            if isinstance(outcome_packet, GenericFamilyBranchOutcomePacket)
            else GenericFamilyBranchOutcomePacket.model_validate(outcome_packet)
        )
        decision = (
            review_decision
            if isinstance(review_decision, GenericFamilyReviewDecisionPacket)
            else GenericFamilyReviewDecisionPacket.model_validate(review_decision)
        )
        snapshot = _coerce_source_snapshot(source_snapshot)
        _validate_dossier_provenance(
            branch,
            outcome=outcome,
            decision=decision,
            source_snapshot=snapshot,
        )
        # A schema-valid scientific non-accept remains the ordinary pre-existing disposition.
        # Only an accepted decision crosses into the typed authority-integrity boundary.
        _validate_dossier_decision(decision)
        _validate_dossier_authority(decision)
    except (ValidationError, _DossierInputMismatch) as exc:
        errors = exc.errors if isinstance(exc, _DossierInputMismatch) else ["schema_validation"]
        observed = exc.observed if isinstance(exc, _DossierInputMismatch) else {}
        expected = exc.expected if isinstance(exc, _DossierInputMismatch) else {}
        diagnostic_path = _persist_dossier_closure_diagnostic(
            workspace,
            DossierClosureDiagnostic(
                diagnostic_id=f"dossier-provenance-{branch.branch_id}",
                code=DossierClosureOutcome.PROVENANCE_INTEGRITY_TERMINAL,
                run_id=run_id,
                branch_id=branch.branch_id,
                question_family_id=branch.question_family_id,
                failure_class=FailureClass.VALIDATION_FAILURE,
                reason=(
                    "Dossier input provenance failed strict identity, digest, or grounding "
                    "validation."
                ),
                errors=errors,
                retained_artifact_paths=_accepted_input_paths(workspace),
                observed_bindings=observed,
                expected_bindings=expected,
            ),
        )
        raise DossierProvenanceIntegrityFailure(
            "dossier input provenance validation failed", diagnostic_path=diagnostic_path
        ) from exc
    source_outcome_path = workspace / "source_outcome_packet.yaml"
    source_review_path = workspace / "source_review_decision.yaml"
    source_snapshot_path = workspace / GENERIC_SOURCE_SNAPSHOT_FILENAME
    dump_data(outcome, source_outcome_path)
    dump_data(decision, source_review_path)
    dump_data(snapshot, source_snapshot_path)

    source_outcome_digest = stable_hash(outcome.model_dump(mode="json"))
    source_review_digest = stable_hash(decision.model_dump(mode="json"))
    source_snapshot_digest = stable_hash(snapshot.model_dump(mode="json"))
    branch_path = Path(output_root) / run_id / "branches" / branch_id / "branch.yaml"
    branch_digest = stable_hash(branch.model_dump(mode="json"))

    evidence_by_id = {evidence.evidence_id: evidence for evidence in branch.inspection_evidence}
    sources = [
        GenericDossierSourceRef(
            source_id="branch_state",
            source_type=GenericDossierSourceType.BRANCH_STATE,
            artifact_id=branch.branch_id,
            artifact_path=str(branch_path),
            artifact_digest=branch_digest,
            contribution="Replayable branch state used to bind this dossier to one family branch.",
        ),
        GenericDossierSourceRef(
            source_id=snapshot.source_snapshot_id,
            source_type=GenericDossierSourceType.SCIENTIFIC_SOURCE_SNAPSHOT,
            artifact_id=snapshot.source_snapshot_id,
            artifact_path=str(source_snapshot_path),
            artifact_digest=source_snapshot_digest,
            contribution="Branch-local scientific source snapshot used for public dossier content.",
        ),
        GenericDossierSourceRef(
            source_id=outcome.outcome_packet_id,
            source_type=GenericDossierSourceType.FAMILY_OUTCOME,
            artifact_id=outcome.outcome_packet_id,
            artifact_path=str(source_outcome_path),
            artifact_digest=source_outcome_digest,
            contribution="Generic plan/reject/escalation outcome for this family.",
        ),
        GenericDossierSourceRef(
            source_id=decision.decision_packet_id,
            source_type=GenericDossierSourceType.REVIEW_DECISION,
            artifact_id=decision.decision_packet_id,
            artifact_path=str(source_review_path),
            artifact_digest=source_review_digest,
            contribution="Development bounded-decision gate for dossier rendering.",
        ),
    ]
    for evidence in branch.inspection_evidence:
        sources.append(
            GenericDossierSourceRef(
                source_id=evidence.evidence_id,
                source_type=GenericDossierSourceType.PLANNER_EVIDENCE,
                artifact_id=evidence.evidence_id,
                artifact_path=str(
                    Path(output_root)
                    / run_id
                    / "branches"
                    / branch_id
                    / "planner"
                    / "evidence"
                    / f"{evidence.evidence_id}.yaml"
                ),
                artifact_digest=stable_hash(evidence.model_dump(mode="json")),
                contribution=evidence.finding,
            )
        )
    allowed_citation_ids = sorted({source.source_id for source in sources} | set(evidence_by_id))
    ledger = GenericDossierCitationLedger(
        citation_ledger_id=_dossier_id("generic-dossier-citation-ledger", branch, run_id),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        sources=sources,
        evidence_ids=sorted(evidence_by_id),
        allowed_citation_ids=allowed_citation_ids,
    )
    packet = _build_writing_packet(
        branch=branch,
        run_id=run_id,
        family_title=family_title,
        family_summary=family_summary,
        outcome=outcome,
        decision=decision,
        source_snapshot=snapshot,
        ledger=ledger,
        workspace=workspace,
    )
    packet_errors = validate_generic_writing_packet_quality(packet)
    if packet_errors:
        raise ValueError(
            "generic dossier writing packet failed quality validation: " + "; ".join(packet_errors)
        )
    skeleton = _render_skeleton(packet)

    ledger_path = workspace / "citation_ledger.yaml"
    packet_path = workspace / "dossier_writing_packet.yaml"
    skeleton_path = workspace / "dossier_skeleton.md"
    dump_data(ledger, ledger_path)
    dump_data(packet, packet_path)
    skeleton_path.write_text(skeleton, encoding="utf-8")

    packet_digest = stable_hash(packet.model_dump(mode="json"))
    ledger_digest = stable_hash(ledger.model_dump(mode="json"))
    skeleton_digest = stable_hash(skeleton)
    branch = manager.record_scientific_dossier_packet_prepared(
        branch.branch_id,
        dossier_writing_packet_id=packet.dossier_writing_packet_id,
        artifact_digest=packet_digest,
    )
    event = branch.events[-1]
    if event.event_type != QuestionFamilyBranchEventType.SCIENTIFIC_DOSSIER_PACKET_PREPARED:
        raise ValueError("generic dossier packet failed to record branch event")

    manifest = GenericDossierManifest(
        dossier_manifest_id=_dossier_id("generic-dossier-manifest", branch, run_id),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        dossier_writing_packet_id=packet.dossier_writing_packet_id,
        citation_ledger_id=ledger.citation_ledger_id,
        dossier_writing_packet_path=str(packet_path),
        dossier_writing_packet_digest=packet_digest,
        citation_ledger_path=str(ledger_path),
        citation_ledger_digest=ledger_digest,
        dossier_skeleton_path=str(skeleton_path),
        dossier_skeleton_digest=skeleton_digest,
        source_packet_ids=[
            snapshot.source_snapshot_id,
            outcome.outcome_packet_id,
            decision.decision_packet_id,
        ],
        source_packet_digests={
            snapshot.source_snapshot_id: source_snapshot_digest,
            outcome.outcome_packet_id: source_outcome_digest,
            decision.decision_packet_id: source_review_digest,
        },
        branch_event_id=event.event_id,
    )
    manifest_path = workspace / "manifest.yaml"
    dump_data(manifest, manifest_path)
    return GenericDossierPacketResult(
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        writing_workspace=str(workspace),
        dossier_writing_packet_path=str(packet_path),
        citation_ledger_path=str(ledger_path),
        dossier_skeleton_path=str(skeleton_path),
        writing_manifest_path=str(manifest_path),
        packet_prepared_event_id=event.event_id,
    )


class GenericDossierMachineRenderResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    branch_id: str
    question_family_id: str
    render_workspace: str
    machine_dossier_path: str
    machine_dossier_artifact_path: str
    render_manifest_path: str
    writer_session_snapshot_path: str
    machine_rendered_event_id: str


def render_generic_machine_dossier(
    *,
    output_root: str | Path,
    run_id: str,
    branch_id: str,
    writing_manifest_path: str | Path,
) -> GenericDossierMachineRenderResult:
    manager = QuestionFamilyBranchManager(output_root, run_id=run_id)
    branch = manager.load_branch(branch_id)
    writing_manifest = load_model(writing_manifest_path, GenericDossierManifest)
    packet = load_model(writing_manifest.dossier_writing_packet_path, GenericDossierWritingPacket)
    ledger = load_model(writing_manifest.citation_ledger_path, GenericDossierCitationLedger)
    skeleton = Path(writing_manifest.dossier_skeleton_path).read_text(encoding="utf-8")
    workspace = _workspace(
        output_root,
        run_id=run_id,
        branch_id=branch_id,
        name=GENERIC_SCIENTIFIC_DOSSIER_RENDERED_WORKSPACE,
    )
    workspace.mkdir(parents=True, exist_ok=True)

    expected_artifact_id = _dossier_id("generic-machine-dossier-markdown", branch, run_id)
    writer_input = GenericDossierWriterInput(
        writer_input_id=_dossier_id("generic-dossier-writer-input", branch, run_id),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_dossier_writing_packet_id=packet.dossier_writing_packet_id,
        source_citation_ledger_id=ledger.citation_ledger_id,
        source_manifest_id=writing_manifest.dossier_manifest_id,
        expected_dossier_markdown_artifact_id=expected_artifact_id,
        allowed_citation_ids=ledger.allowed_citation_ids,
        evidence_ids=ledger.evidence_ids,
        required_section_ids=[section.section_id for section in packet.sections],
        claim_ids=[claim.claim_id for claim in packet.claims],
        dossier_writing_packet=packet.model_dump(mode="json"),
        citation_ledger=ledger.model_dump(mode="json"),
        source_manifest=writing_manifest.model_dump(mode="json"),
        dossier_skeleton_markdown=skeleton,
        instructions_summary=(
            "Render a machine/audit planning dossier. Keep internal IDs and citation audit "
            "visible here; the end-user translation will redact them."
        ),
    )
    markdown_artifact = GenericDossierMarkdownArtifact(
        dossier_markdown_artifact_id=expected_artifact_id,
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_dossier_writing_packet_id=packet.dossier_writing_packet_id,
        source_citation_ledger_id=ledger.citation_ledger_id,
        source_manifest_id=writing_manifest.dossier_manifest_id,
        title=packet.question_title,
        markdown=_render_machine_markdown(packet=packet, ledger=ledger),
        section_ids=[section.section_id for section in packet.sections],
        claim_ids=[claim.claim_id for claim in packet.claims],
        cited_source_ids=[source.source_id for source in ledger.sources],
        cited_evidence_ids=ledger.evidence_ids,
        writer_limitations=packet.remaining_human_decisions,
        citation_audit_summary="Every machine claim cites ledger sources or evidence IDs.",
    )
    session_id = _dossier_id("generic-dossier-writer-session", branch, run_id)
    snapshot = _session_snapshot(
        branch_id=branch.branch_id,
        session_id=session_id,
        provider_id=GENERIC_DOSSIER_RENDERER_PROVIDER_ID,
        model_id=GENERIC_DOSSIER_RENDERER_MODEL_ID,
        prompt_version=GENERIC_DOSSIER_WRITER_PROMPT_VERSION,
        input_payload=writer_input,
        output_payload=markdown_artifact,
        output_schema=GenericDossierMarkdownArtifact,
    )
    record = snapshot.transcript[-1]

    writer_input_path = workspace / "writer_input.yaml"
    markdown_path = workspace / "scientific_dossier.md"
    artifact_path = workspace / "scientific_dossier_artifact.yaml"
    snapshot_path = workspace / "writer_session_snapshot.yaml"
    dump_data(writer_input, writer_input_path)
    markdown_path.write_text(markdown_artifact.markdown, encoding="utf-8")
    dump_data(markdown_artifact, artifact_path)
    dump_data(snapshot, snapshot_path)

    writer_input_digest = stable_hash(writer_input.model_dump(mode="json"))
    markdown_digest = stable_hash(markdown_artifact.markdown)
    artifact_digest = stable_hash(markdown_artifact.model_dump(mode="json"))
    snapshot_digest = stable_hash(snapshot.model_dump(mode="json"))
    branch = manager.record_scientific_dossier_rendered(
        branch.branch_id,
        dossier_markdown_artifact_id=markdown_artifact.dossier_markdown_artifact_id,
        artifact_digest=artifact_digest,
        provider_id=record.provider_id,
        model_id=record.model_id,
        session_id=record.session_id,
        prompt_version=record.prompt_version,
        input_digest=record.input_digest,
        output_digest=record.output_digest,
    )
    event = branch.events[-1]
    if event.event_type != QuestionFamilyBranchEventType.SCIENTIFIC_DOSSIER_RENDERED:
        raise ValueError("generic machine dossier failed to record branch event")
    render_manifest = GenericDossierRenderManifest(
        rendered_dossier_manifest_id=_dossier_id("generic-dossier-render-manifest", branch, run_id),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_dossier_manifest_id=writing_manifest.dossier_manifest_id,
        source_dossier_writing_packet_id=packet.dossier_writing_packet_id,
        source_citation_ledger_id=ledger.citation_ledger_id,
        writer_input_path=str(writer_input_path),
        writer_input_digest=writer_input_digest,
        dossier_markdown_path=str(markdown_path),
        dossier_markdown_digest=markdown_digest,
        dossier_markdown_artifact_path=str(artifact_path),
        dossier_markdown_artifact_digest=artifact_digest,
        writer_session_snapshot_path=str(snapshot_path),
        writer_session_snapshot_digest=snapshot_digest,
        provider_id=record.provider_id,
        model_id=record.model_id,
        prompt_version=record.prompt_version,
        session_id=record.session_id,
        input_digest=record.input_digest,
        output_digest=record.output_digest,
        branch_event_id=event.event_id,
    )
    manifest_path = workspace / "manifest.yaml"
    dump_data(render_manifest, manifest_path)
    return GenericDossierMachineRenderResult(
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        render_workspace=str(workspace),
        machine_dossier_path=str(markdown_path),
        machine_dossier_artifact_path=str(artifact_path),
        render_manifest_path=str(manifest_path),
        writer_session_snapshot_path=str(snapshot_path),
        machine_rendered_event_id=event.event_id,
    )


class GenericEndUserDossierResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    branch_id: str
    question_family_id: str
    end_user_workspace: str
    end_user_dossier_path: str
    end_user_dossier_artifact_path: str
    audit_sidecar_path: str
    end_user_manifest_path: str
    translator_session_snapshot_path: str
    end_user_rendered_event_id: str


def render_generic_end_user_dossier(
    *,
    output_root: str | Path,
    run_id: str,
    branch_id: str,
    render_manifest_path: str | Path,
) -> GenericEndUserDossierResult:
    manager = QuestionFamilyBranchManager(output_root, run_id=run_id)
    branch = manager.load_branch(branch_id)
    render_manifest = load_model(render_manifest_path, GenericDossierRenderManifest)
    machine_artifact = load_model(
        render_manifest.dossier_markdown_artifact_path,
        GenericDossierMarkdownArtifact,
    )
    writing_workspace = _workspace(
        output_root,
        run_id=run_id,
        branch_id=branch_id,
        name=GENERIC_SCIENTIFIC_DOSSIER_WORKSPACE,
    )
    packet = load_model(
        writing_workspace / "dossier_writing_packet.yaml",
        GenericDossierWritingPacket,
    )
    outcome = load_model(
        writing_workspace / "source_outcome_packet.yaml",
        GenericFamilyBranchOutcomePacket,
    )
    source_snapshot = load_model(
        writing_workspace / GENERIC_SOURCE_SNAPSHOT_FILENAME,
        QuestionFamilyScientificSourceSnapshot,
    )
    ledger = load_model(
        writing_workspace / "citation_ledger.yaml",
        GenericDossierCitationLedger,
    )
    workspace = _workspace(
        output_root,
        run_id=run_id,
        branch_id=branch_id,
        name=GENERIC_END_USER_SCIENTIFIC_DOSSIER_WORKSPACE,
    )
    workspace.mkdir(parents=True, exist_ok=True)

    redacted_internal_ids = _redacted_ids(
        branch=branch,
        packet=packet,
        ledger=ledger,
        render_manifest=render_manifest,
        machine_artifact=machine_artifact,
        outcome=outcome,
    )
    public_markdown = _render_public_markdown(
        packet,
        source_snapshot=source_snapshot,
        redacted_internal_ids=redacted_internal_ids,
    )
    quality_errors = validate_generic_public_dossier_quality(
        public_markdown,
        source_snapshot=source_snapshot,
    )
    if quality_errors:
        omitted_paths = [
            str(workspace / "end_user_dossier.md"),
            str(workspace / "end_user_dossier_artifact.yaml"),
            str(workspace / "end_user_dossier_audit.yaml"),
            str(workspace / "manifest.yaml"),
        ]
        writing_workspace = _workspace(
            output_root,
            run_id=run_id,
            branch_id=branch_id,
            name=GENERIC_SCIENTIFIC_DOSSIER_WORKSPACE,
        )
        diagnostic_path = _persist_dossier_closure_diagnostic(
            workspace,
            DossierClosureDiagnostic(
                diagnostic_id=f"public-dossier-revision-{branch.branch_id}",
                code=DossierClosureOutcome.PUBLIC_DOSSIER_REVISION_REQUIRED,
                run_id=run_id,
                branch_id=branch.branch_id,
                question_family_id=branch.question_family_id,
                reason=(
                    "The accepted machine dossier requires public-text revision before publication."
                ),
                errors=quality_errors,
                retained_artifact_paths=[
                    render_manifest.dossier_markdown_path,
                    render_manifest.dossier_markdown_artifact_path,
                    str(Path(render_manifest_path)),
                    str(writing_workspace / "source_outcome_packet.yaml"),
                    str(writing_workspace / "source_review_decision.yaml"),
                    str(writing_workspace / GENERIC_SOURCE_SNAPSHOT_FILENAME),
                ],
                omitted_public_artifact_paths=omitted_paths,
            ),
        )
        raise PublicDossierRevisionRequired(
            "generic public dossier failed quality validation", diagnostic_path=diagnostic_path
        )

    public_artifact = GenericEndUserDossierMarkdownArtifact(
        end_user_dossier_artifact_id=_dossier_id("generic-end-user-dossier", branch, run_id),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_dossier_markdown_artifact_id=machine_artifact.dossier_markdown_artifact_id,
        source_render_manifest_id=render_manifest.rendered_dossier_manifest_id,
        title=packet.question_title,
        markdown=public_markdown,
        section_titles=[section.title for section in packet.sections],
        public_limitations=packet.remaining_human_decisions,
        visible_authority_statement=_public_authority_statement(packet.review_authority),
        redacted_internal_ids=redacted_internal_ids,
        cited_public_binding_labels=[
            f"Audit binding {index}" for index, _claim in enumerate(packet.claims, start=1)
        ],
    )
    translator_input: dict[str, object] = {
        "source_render_manifest_id": render_manifest.rendered_dossier_manifest_id,
        "source_dossier_markdown_artifact_id": machine_artifact.dossier_markdown_artifact_id,
        "redaction_policy": "Hide internal claim/source/evidence/run/branch IDs in public Markdown.",
        "redacted_internal_ids": redacted_internal_ids,
    }
    audit_sidecar = _build_audit_sidecar(
        branch=branch,
        run_id=run_id,
        packet=packet,
        ledger=ledger,
        render_manifest=render_manifest,
        machine_artifact=machine_artifact,
        public_artifact=public_artifact,
        translator_input=translator_input,
    )
    session_id = _dossier_id("generic-end-user-translator-session", branch, run_id)
    snapshot = _session_snapshot_from_dict(
        branch_id=branch.branch_id,
        session_id=session_id,
        provider_id=GENERIC_END_USER_TRANSLATOR_PROVIDER_ID,
        model_id=GENERIC_END_USER_TRANSLATOR_MODEL_ID,
        prompt_version=GENERIC_END_USER_DOSSIER_TRANSLATOR_PROMPT_VERSION,
        input_payload=translator_input,
        output_payload=public_artifact,
        output_schema=GenericEndUserDossierMarkdownArtifact,
    )
    record = snapshot.transcript[-1]

    translator_input_path = workspace / "translator_input.yaml"
    markdown_path = workspace / "end_user_dossier.md"
    artifact_path = workspace / "end_user_dossier_artifact.yaml"
    audit_sidecar_path = workspace / "end_user_dossier_audit.yaml"
    snapshot_path = workspace / "translator_session_snapshot.yaml"
    dump_data(translator_input, translator_input_path)
    markdown_path.write_text(public_artifact.markdown, encoding="utf-8")
    dump_data(public_artifact, artifact_path)
    dump_data(audit_sidecar, audit_sidecar_path)
    dump_data(snapshot, snapshot_path)

    translator_input_digest = stable_hash(translator_input)
    markdown_digest = stable_hash(public_artifact.markdown)
    artifact_digest = stable_hash(public_artifact.model_dump(mode="json"))
    audit_sidecar_digest = stable_hash(audit_sidecar.model_dump(mode="json"))
    snapshot_digest = stable_hash(snapshot.model_dump(mode="json"))
    branch = manager.record_end_user_scientific_dossier_rendered(
        branch.branch_id,
        end_user_dossier_artifact_id=public_artifact.end_user_dossier_artifact_id,
        artifact_digest=artifact_digest,
        provider_id=record.provider_id,
        model_id=record.model_id,
        session_id=record.session_id,
        prompt_version=record.prompt_version,
        input_digest=record.input_digest,
        output_digest=record.output_digest,
    )
    event = branch.events[-1]
    if event.event_type != QuestionFamilyBranchEventType.END_USER_SCIENTIFIC_DOSSIER_RENDERED:
        raise ValueError("generic end-user dossier failed to record branch event")
    manifest = GenericEndUserDossierManifest(
        end_user_dossier_manifest_id=_dossier_id(
            "generic-end-user-dossier-manifest", branch, run_id
        ),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_render_manifest_id=render_manifest.rendered_dossier_manifest_id,
        source_dossier_markdown_artifact_id=machine_artifact.dossier_markdown_artifact_id,
        source_dossier_writing_packet_id=packet.dossier_writing_packet_id,
        source_citation_ledger_id=packet.citation_ledger_id,
        translator_input_path=str(translator_input_path),
        translator_input_digest=translator_input_digest,
        end_user_dossier_path=str(markdown_path),
        end_user_dossier_digest=markdown_digest,
        end_user_dossier_artifact_path=str(artifact_path),
        end_user_dossier_artifact_digest=artifact_digest,
        audit_sidecar_path=str(audit_sidecar_path),
        audit_sidecar_digest=audit_sidecar_digest,
        translator_session_snapshot_path=str(snapshot_path),
        translator_session_snapshot_digest=snapshot_digest,
        provider_id=record.provider_id,
        model_id=record.model_id,
        prompt_version=record.prompt_version,
        session_id=record.session_id,
        input_digest=record.input_digest,
        output_digest=record.output_digest,
        branch_event_id=event.event_id,
    )
    manifest_path = workspace / "manifest.yaml"
    dump_data(manifest, manifest_path)
    return GenericEndUserDossierResult(
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        end_user_workspace=str(workspace),
        end_user_dossier_path=str(markdown_path),
        end_user_dossier_artifact_path=str(artifact_path),
        audit_sidecar_path=str(audit_sidecar_path),
        end_user_manifest_path=str(manifest_path),
        translator_session_snapshot_path=str(snapshot_path),
        end_user_rendered_event_id=event.event_id,
    )


def _validate_dossier_provenance(
    branch: QuestionFamilyBranch,
    *,
    outcome: GenericFamilyBranchOutcomePacket,
    decision: GenericFamilyReviewDecisionPacket,
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
) -> None:
    snapshot_identity = {
        "branch_id": branch.branch_id,
        "question_family_id": branch.question_family_id,
        "context_id": branch.context_id,
    }
    snapshot_mismatches = [
        field
        for field, expected in snapshot_identity.items()
        if getattr(source_snapshot, field) != expected
    ]
    if snapshot_mismatches:
        raise _DossierInputMismatch(
            "generic dossier source snapshot references another " + ", ".join(snapshot_mismatches),
            errors=["source_snapshot_identity:" + field for field in snapshot_mismatches],
            observed={field: str(getattr(source_snapshot, field)) for field in snapshot_mismatches},
            expected={field: str(snapshot_identity[field]) for field in snapshot_mismatches},
        )
    snapshot_digest = stable_hash(source_snapshot.model_dump(mode="json"))
    if outcome.source_snapshot_id != source_snapshot.source_snapshot_id:
        raise _DossierInputMismatch(
            "generic dossier outcome source snapshot mismatch",
            errors=["outcome_source_snapshot_id_mismatch"],
            observed={"source_snapshot_id": outcome.source_snapshot_id},
            expected={"source_snapshot_id": source_snapshot.source_snapshot_id},
        )
    if outcome.source_snapshot_digest != snapshot_digest:
        raise _DossierInputMismatch(
            "generic dossier outcome source snapshot digest mismatch",
            errors=["outcome_source_snapshot_digest_mismatch"],
            observed={"source_snapshot_digest": outcome.source_snapshot_digest},
            expected={"source_snapshot_digest": snapshot_digest},
        )
    if decision.dataset_grounding_level != outcome.dataset_grounding_level:
        raise _DossierInputMismatch(
            "generic review decision dataset grounding level mismatch",
            errors=["review_outcome_grounding_mismatch"],
            observed={"decision_grounding": decision.dataset_grounding_level.value},
            expected={"outcome_grounding": outcome.dataset_grounding_level.value},
        )
    if decision.dataset_claim_status != outcome.dataset_claim_status:
        raise _DossierInputMismatch(
            "generic review decision dataset claim status mismatch",
            errors=["review_outcome_dataset_claim_status_mismatch"],
            observed={"decision_claim_status": decision.dataset_claim_status.value},
            expected={"outcome_claim_status": outcome.dataset_claim_status.value},
        )
    errors = validate_generic_family_outcome_packet(
        branch,
        packet=outcome,
        evidence_by_id={evidence.evidence_id: evidence for evidence in branch.inspection_evidence},
    )
    if errors:
        raise _DossierInputMismatch(
            "generic dossier outcome packet is invalid",
            errors=["outcome_packet:" + error for error in errors],
        )
    identity = {
        "branch_id": branch.branch_id,
        "question_family_id": branch.question_family_id,
        "context_id": branch.context_id,
        "owner_session_id": branch.owner_session_id,
    }
    mismatched = [
        field for field, expected in identity.items() if getattr(decision, field) != expected
    ]
    if mismatched:
        raise _DossierInputMismatch(
            "generic review decision references another " + ", ".join(mismatched),
            errors=["review_decision_identity:" + field for field in mismatched],
            observed={field: str(getattr(decision, field)) for field in mismatched},
            expected={field: str(identity[field]) for field in mismatched},
        )
    if decision.source_outcome_packet_id != outcome.outcome_packet_id:
        raise _DossierInputMismatch(
            "generic review decision source outcome packet mismatch",
            errors=["review_source_outcome_packet_id_mismatch"],
            observed={"source_outcome_packet_id": decision.source_outcome_packet_id},
            expected={"source_outcome_packet_id": outcome.outcome_packet_id},
        )


def _validate_dossier_decision(decision: GenericFamilyReviewDecisionPacket) -> None:
    if decision.decision not in {
        GenericReviewDecisionValue.ACCEPT_FOR_DEVELOPMENT_DOSSIER,
        GenericReviewDecisionValue.ACCEPT_FOR_SERIOUS_DOSSIER,
    }:
        raise ValueError("generic dossier rendering requires an accepted review decision")


def _validate_dossier_authority(decision: GenericFamilyReviewDecisionPacket) -> None:
    if decision.authority in {
        ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE,
        ReviewAuthority.AUTOMATED,
    }:
        if not decision.development_dossier_rendering_allowed:
            raise _DossierInputMismatch(
                "automated decision must allow development dossier rendering",
                errors=["review_authority_render_permission_mismatch"],
                observed={"development_dossier_rendering_allowed": "false"},
                expected={"development_dossier_rendering_allowed": "true"},
            )
    elif decision.authority == ReviewAuthority.REAL_HUMAN_EXPERT:
        if not decision.allows_dossier_generation or not decision.human_review_imported:
            raise _DossierInputMismatch(
                "real human decision must allow dossier generation",
                errors=["review_authority_human_import_mismatch"],
                observed={
                    "allows_dossier_generation": str(decision.allows_dossier_generation).lower(),
                    "human_review_imported": str(decision.human_review_imported).lower(),
                },
                expected={
                    "allows_dossier_generation": "true",
                    "human_review_imported": "true",
                },
            )
    else:
        raise _DossierInputMismatch(
            "generic dossier rendering requires a review authority",
            errors=["review_authority_missing_or_unsupported"],
            observed={"review_authority": decision.authority.value},
            expected={"review_authority": "automated_or_real_human_expert"},
        )


def _accepted_input_paths(workspace: Path) -> list[str]:
    return [
        str(workspace / "source_outcome_packet.yaml"),
        str(workspace / "source_review_decision.yaml"),
        str(workspace / GENERIC_SOURCE_SNAPSHOT_FILENAME),
    ]


def _jsonable_external_input(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    return TypeAdapter(object).dump_python(value, mode="json")


def _persist_dossier_closure_diagnostic(
    workspace: Path,
    diagnostic: DossierClosureDiagnostic,
) -> Path:
    return dump_data(diagnostic, workspace / DOSSIER_CLOSURE_DIAGNOSTIC_FILENAME)


def _build_writing_packet(
    *,
    branch: QuestionFamilyBranch,
    run_id: str,
    family_title: str,
    family_summary: str,
    outcome: GenericFamilyBranchOutcomePacket,
    decision: GenericFamilyReviewDecisionPacket,
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
    ledger: GenericDossierCitationLedger,
    workspace: Path,
) -> GenericDossierWritingPacket:
    scientific_by_variant = {
        entry.variant_id: entry for entry in outcome.variant_scientific_outcomes
    }
    plan_by_variant = {
        entry.variant_id: entry.analysis_plan for entry in outcome.variant_analysis_plans
    }
    variant_claims = []
    variant_plan_claims = []
    variant_disposition_claims = []
    for entry in outcome.variant_outcomes:
        scientific = scientific_by_variant[entry.variant_id]
        variant_claims.append(
            GenericDossierClaim(
                claim_id=f"claim-{entry.variant_id}-outcome",
                scope=GenericDossierClaimScope.VARIANT,
                variant_id=entry.variant_id,
                text=_variant_claim_text(scientific),
                citation_ids=sorted(
                    set(entry.evidence_ids)
                    | {outcome.outcome_packet_id, source_snapshot.source_snapshot_id}
                ),
            )
        )
        if outcome.outcome_kind == GenericFamilyOutcomeKind.PLAN and entry.decision.is_accepted:
            detailed_plan = plan_by_variant.get(entry.variant_id)
            variant_plan_claims.append(
                GenericDossierClaim(
                    claim_id=f"claim-{entry.variant_id}-plan",
                    scope=GenericDossierClaimScope.VARIANT,
                    variant_id=entry.variant_id,
                    text=_variant_plan_text(entry.summary, detailed_plan),
                    citation_ids=sorted(
                        set(entry.evidence_ids)
                        | (set(detailed_plan.evidence_ids) if detailed_plan is not None else set())
                        | {outcome.outcome_packet_id}
                    ),
                )
            )
        elif outcome.outcome_kind == GenericFamilyOutcomeKind.PLAN:
            disposition = entry.decision.value.replace("_", " ").capitalize()
            variant_disposition_claims.append(
                GenericDossierClaim(
                    claim_id=f"claim-{entry.variant_id}-disposition",
                    scope=GenericDossierClaimScope.VARIANT,
                    variant_id=entry.variant_id,
                    text=f"{disposition}. {entry.summary}",
                    citation_ids=sorted(set(entry.evidence_ids) | {outcome.outcome_packet_id}),
                )
            )
    if outcome.outcome_kind == GenericFamilyOutcomeKind.PLAN:
        variant_section_title = (
            "Variant Outcomes And Plans" if variant_disposition_claims else "Variant Plans"
        )
    else:
        variant_section_title = "Variant Outcomes"
    claims = [
        GenericDossierClaim(
            claim_id="claim-family-question",
            scope=GenericDossierClaimScope.FAMILY,
            text=source_snapshot.family_summary,
            citation_ids=[source_snapshot.source_snapshot_id, outcome.outcome_packet_id],
        ),
        GenericDossierClaim(
            claim_id="claim-scientific-motivation",
            scope=GenericDossierClaimScope.FAMILY,
            text=source_snapshot.shared_scientific_tension,
            citation_ids=[source_snapshot.source_snapshot_id, outcome.outcome_packet_id],
        ),
        GenericDossierClaim(
            claim_id="claim-dataset-leverage",
            scope=GenericDossierClaimScope.FEASIBILITY,
            text=(
                f"Dataset claim status is {outcome.dataset_claim_status.value}; observed-depth "
                f"label is {outcome.dataset_grounding_level.value}. Dataset leverage remains a "
                "planning hypothesis: "
                f"{_join_sentences(v.dataset_leverage_hypothesis for v in source_snapshot.variants)} "
                "No scientific-result generation was performed."
            ),
            citation_ids=sorted(set(ledger.evidence_ids) | {source_snapshot.source_snapshot_id}),
        ),
        *variant_claims,
        *variant_plan_claims,
        *variant_disposition_claims,
        GenericDossierClaim(
            claim_id="claim-competing-explanations",
            scope=GenericDossierClaimScope.METHOD,
            text=_competing_explanation_text(outcome.variant_scientific_outcomes),
            citation_ids=[source_snapshot.source_snapshot_id, outcome.outcome_packet_id],
        ),
        GenericDossierClaim(
            claim_id="claim-outcome-meanings",
            scope=GenericDossierClaimScope.METHOD,
            text=_outcome_meanings_text(outcome.variant_scientific_outcomes),
            citation_ids=[source_snapshot.source_snapshot_id, outcome.outcome_packet_id],
        ),
        GenericDossierClaim(
            claim_id="claim-limitations",
            scope=GenericDossierClaimScope.LIMITATION,
            text=_planning_status_text(outcome=outcome, decision=decision),
            citation_ids=[decision.decision_packet_id],
        ),
        GenericDossierClaim(
            claim_id="claim-authority",
            scope=GenericDossierClaimScope.PROVENANCE,
            text=(
                f"Review authority is {decision.authority.value}; human review status is "
                f"{_human_review_status(decision)}."
            ),
            citation_ids=[decision.decision_packet_id],
        ),
        GenericDossierClaim(
            claim_id="claim-provenance",
            scope=GenericDossierClaimScope.PROVENANCE,
            text="The dossier is bound to branch-local replayable state and review provenance.",
            citation_ids=[
                "branch_state",
                source_snapshot.source_snapshot_id,
                outcome.outcome_packet_id,
                decision.decision_packet_id,
            ],
        ),
    ]
    sections = [
        GenericDossierSection(
            section_id="question_family",
            title="Question Family",
            purpose="Identify the family and intent boundary.",
            claim_ids=["claim-family-question"],
        ),
        GenericDossierSection(
            section_id="scientific_motivation",
            title="Scientific Motivation",
            purpose="Explain why the family remains scientifically consequential.",
            claim_ids=["claim-scientific-motivation"],
        ),
        GenericDossierSection(
            section_id="dataset_leverage",
            title="Dataset Leverage",
            purpose="Explain branch-local evidence support.",
            claim_ids=["claim-dataset-leverage"],
        ),
        GenericDossierSection(
            section_id="variant_plans",
            title=variant_section_title,
            purpose="Keep sibling variants distinct.",
            claim_ids=[
                claim_id
                for scientific_claim in variant_claims
                for claim_id in (
                    scientific_claim.claim_id,
                    *[
                        plan_claim.claim_id
                        for plan_claim in variant_plan_claims
                        if plan_claim.variant_id == scientific_claim.variant_id
                    ],
                    *[
                        disposition_claim.claim_id
                        for disposition_claim in variant_disposition_claims
                        if disposition_claim.variant_id == scientific_claim.variant_id
                    ],
                )
            ],
        ),
        GenericDossierSection(
            section_id="competing_explanations",
            title="Competing Explanations And Controls",
            purpose="State alternatives that the plan must keep visible.",
            claim_ids=["claim-competing-explanations"],
        ),
        GenericDossierSection(
            section_id="outcome_meanings",
            title="Outcome Meanings",
            purpose="Explain how positive, negative, and mixed outcomes would be interpreted.",
            claim_ids=["claim-outcome-meanings"],
        ),
        GenericDossierSection(
            section_id="limitations",
            title="Limitations",
            purpose="State development-mode and no-bridge limits.",
            claim_ids=["claim-limitations"],
        ),
        GenericDossierSection(
            section_id="authority",
            title="Authority And Next Decisions",
            purpose="State authority and human-review boundaries.",
            claim_ids=["claim-authority"],
        ),
        GenericDossierSection(
            section_id="provenance",
            title="Provenance",
            purpose="Record audit chain references.",
            claim_ids=["claim-provenance"],
        ),
    ]
    return GenericDossierWritingPacket(
        dossier_writing_packet_id=_dossier_id("generic-dossier-writing-packet", branch, run_id),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_snapshot_id=source_snapshot.source_snapshot_id,
        source_snapshot_digest=stable_hash(source_snapshot.model_dump(mode="json")),
        dataset_grounding_level=outcome.dataset_grounding_level,
        dataset_claim_status=outcome.dataset_claim_status,
        human_review_status=_human_review_status(decision),
        source_outcome_packet_id=outcome.outcome_packet_id,
        source_review_decision_packet_id=decision.decision_packet_id,
        review_authority=decision.authority,
        review_decision=decision.decision,
        outcome_kind=outcome.outcome_kind,
        branch_decision=outcome.decision,
        citation_ledger_id=ledger.citation_ledger_id,
        allowed_citation_ids=ledger.allowed_citation_ids,
        evidence_ids=ledger.evidence_ids,
        question_title=family_title,
        question_statement=branch.family_intent_invariant.shared_phenomenon,
        family_intent_summary=family_summary,
        claim_ceiling=[
            "Planning dossier only.",
            "No scientific result is claimed.",
            "No R5-011 bridge, QuestionCard, AnalysisContract, handoff, or execution is created.",
        ],
        remaining_human_decisions=[
            "Optional post-hoc human review may be imported through the generic file template.",
            "Separate explicit bridge approval is required before any R5-011 downstream artifact.",
        ],
        sections=sections,
        claims=claims,
        dossier_skeleton_path=str(workspace / "dossier_skeleton.md"),
        citation_ledger_path=str(workspace / "citation_ledger.yaml"),
    )


def _coerce_source_snapshot(
    source_snapshot: QuestionFamilyScientificSourceSnapshot | dict[str, object],
) -> QuestionFamilyScientificSourceSnapshot:
    if isinstance(source_snapshot, QuestionFamilyScientificSourceSnapshot):
        return source_snapshot
    return QuestionFamilyScientificSourceSnapshot.model_validate(source_snapshot)


def _variant_claim_text(scientific: GenericVariantScientificOutcome) -> str:
    return (
        f"{scientific.variant_role}: {scientific.scientific_question} "
        f"The preserved contrast is {scientific.scientific_contrast}. "
        f"The discriminating observation is {scientific.discriminating_observation}. "
        f"Current dataset leverage status: {scientific.dataset_leverage_status}"
    )


def _variant_plan_text(summary: str, plan: AnalysisPlan | None) -> str:
    """Render a public, inspectable plan description while preserving legacy summaries."""

    if plan is None:
        return summary
    components = [
        summary,
        f"Refined question: {plan.refined_question}",
        f"Population and scope: {plan.population_and_scope}",
        "Data sources: " + _plan_data_source_text(plan),
        f"Unit of observation: {plan.unit_of_observation}",
        f"Unit of inference: {plan.unit_of_inference}",
        f"Hierarchy and dependence: {plan.hierarchy_and_dependence}",
        "Analysis strategy: " + _join_sentences(plan.analysis_strategy),
        "Candidate estimands: " + _join_sentences(plan.candidate_estimands),
        f"Validation strategy: {plan.validation_strategy}",
        f"Split strategy: {plan.split_strategy}",
        "Diagnostics: " + _join_sentences(plan.diagnostics),
        "Negative controls: " + _join_sentences(plan.negative_controls),
        "Positive controls: " + _join_sentences(plan.positive_controls),
        "Alternative explanations: " + _join_sentences(plan.alternative_explanations),
        "Predicted result patterns: " + _join_sentences(plan.predicted_result_patterns),
        _render_claim_ceiling(plan),
        "Interpretation limits: " + _join_sentences(plan.interpretation_limits),
        f"Resource estimate: {plan.resource_estimate}",
        f"Why this serves the question: {plan.why_plan_serves_question}",
    ]
    if plan.required_new_skills:
        components.append("Required new skills: " + _join_sentences(plan.required_new_skills))
    if plan.unresolved_decisions:
        components.append(
            "Unresolved planning decisions: " + _join_sentences(plan.unresolved_decisions)
        )
    return " ".join(component.strip() for component in components if component.strip())


def _render_claim_ceiling(plan: AnalysisPlan) -> str:
    if not plan.claim_ceiling_components:
        return f"Claim ceiling: {plan.claim_ceiling.value}"
    components = ", ".join(level.value for level in plan.claim_ceiling_components)
    return f"Claim ceiling: {plan.claim_ceiling.value} (preserved modes: {components})"


def _plan_data_source_text(plan: AnalysisPlan) -> str:
    if not plan.data_sources:
        return "No source-backed data source was available."
    rendered = []
    for source in plan.data_sources:
        details = [source.description, f"Expected grain: {source.expected_grain}"]
        if source.required_variables:
            details.append("Required variables: " + ", ".join(source.required_variables))
        if source.limitations:
            details.append("Limitations: " + _join_sentences(source.limitations))
        rendered.append("; ".join(details))
    return " ".join(item if item.endswith(".") else item + "." for item in rendered)


def _competing_explanation_text(
    variant_outcomes: list[GenericVariantScientificOutcome],
) -> str:
    explanations = []
    for outcome in variant_outcomes:
        explanations.extend(outcome.competing_explanations)
    return "Competing explanations that must remain visible: " + _join_sentences(
        dict.fromkeys(explanations)
    )


def _outcome_meanings_text(
    variant_outcomes: list[GenericVariantScientificOutcome],
) -> str:
    meanings = []
    for outcome in variant_outcomes:
        meanings.extend(outcome.outcome_meanings)
    return "Possible outcome meanings: " + _join_sentences(dict.fromkeys(meanings))


def _join_sentences(items: Iterable[object]) -> str:
    values = [str(item).strip() for item in items if str(item).strip()]
    if not values:
        return "No source-backed statement was available."
    return " ".join(item if item.endswith(".") else item + "." for item in values)


def _human_review_status(decision: GenericFamilyReviewDecisionPacket) -> str:
    if decision.human_review_imported and decision.allows_dossier_generation:
        return "accepted_for_dossier"
    if decision.authority == ReviewAuthority.AUTOMATED:
        return "human_review_optional_not_imported"
    if decision.authority == ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE:
        return "awaiting_real_human_review"
    return "not_imported"


def _planning_status_text(
    *,
    outcome: GenericFamilyBranchOutcomePacket,
    decision: GenericFamilyReviewDecisionPacket,
) -> str:
    if decision.authority == ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE:
        return (
            "This development model-surrogate dossier is not an independently accepted planning "
            "outcome. Optional post-hoc human review may be imported later. It remains "
            "planning-only and does not authorize a downstream bridge or execution or claim "
            "scientific results."
        )
    outcome_label = {
        GenericFamilyOutcomeKind.PLAN: "accepted plan",
        GenericFamilyOutcomeKind.REJECTION: "scientific rejection",
        GenericFamilyOutcomeKind.HUMAN_ESCALATION: "automated escalation terminal",
    }[outcome.outcome_kind]
    authority_label = (
        "automated independent"
        if decision.authority == ReviewAuthority.AUTOMATED
        else decision.authority.value.replace("_", " ")
    )
    return (
        f"This {outcome_label} is a completed planning outcome under "
        f"{authority_label} review. Optional post-hoc human review may "
        "be imported later. It remains planning-only and does not authorize a downstream bridge "
        "or execution or claim scientific results."
    )


def _render_skeleton(packet: GenericDossierWritingPacket) -> str:
    lines = [f"# {packet.question_title}", ""]
    for section in packet.sections:
        lines.extend([f"## {section.title}", "", f"Purpose: {section.purpose}", ""])
        for claim_id in section.claim_ids:
            lines.append(f"- [{claim_id}]")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _render_machine_markdown(
    *,
    packet: GenericDossierWritingPacket,
    ledger: GenericDossierCitationLedger,
) -> str:
    claim_by_id = {claim.claim_id: claim for claim in packet.claims}
    lines = [
        f"# {packet.question_title}",
        "",
        f"Run: `{packet.run_id}`",
        f"Branch: `{packet.branch_id}`",
        f"Family: `{packet.question_family_id}`",
        f"Authority: `{packet.review_authority.value}`",
        f"Outcome: `{packet.outcome_kind.value}` / `{packet.branch_decision.value}`",
        f"Dataset claim status: `{packet.dataset_claim_status.value}`",
        "",
    ]
    for section in packet.sections:
        lines.extend([f"## {section.title}", ""])
        for claim_id in section.claim_ids:
            claim = claim_by_id[claim_id]
            citations = ", ".join(f"`{citation_id}`" for citation_id in claim.citation_ids)
            lines.append(f"- `{claim.claim_id}` {claim.text} Citations: {citations}.")
        lines.append("")
    lines.extend(
        [
            "## Citation Ledger",
            "",
            f"Allowed citation IDs: {', '.join(f'`{item}`' for item in ledger.allowed_citation_ids)}",
            "",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _render_public_markdown(
    packet: GenericDossierWritingPacket,
    *,
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
    redacted_internal_ids: list[str],
) -> str:
    outcome_label = {
        GenericFamilyOutcomeKind.PLAN: "development planning dossier",
        GenericFamilyOutcomeKind.REJECTION: "development rejection dossier",
        GenericFamilyOutcomeKind.HUMAN_ESCALATION: "development escalation dossier",
    }[packet.outcome_kind]
    lines = [
        f"# {packet.question_title}",
        "",
        f"This is a {outcome_label}. It is planning-only and does not report scientific results.",
        f"Dataset grounding level: `{packet.dataset_grounding_level.value}`.",
        f"Dataset claim status: `{packet.dataset_claim_status.value}`.",
        "",
        "## Question Family",
        "",
        _redact_text(_claim_text(packet, "claim-family-question"), redacted_internal_ids),
        "",
        "## Scientific Motivation",
        "",
        _redact_text(_claim_text(packet, "claim-scientific-motivation"), redacted_internal_ids),
        "",
        "## Dataset Leverage",
        "",
        _redact_text(_claim_text(packet, "claim-dataset-leverage"), redacted_internal_ids),
        "",
        "## " + _variant_section_title(packet),
        "",
    ]
    plan_claims = {
        claim.variant_id: claim
        for claim in packet.claims
        if claim.scope == GenericDossierClaimScope.VARIANT and claim.claim_id.endswith("-plan")
    }
    disposition_claims = {
        claim.variant_id: claim
        for claim in packet.claims
        if claim.scope == GenericDossierClaimScope.VARIANT
        and claim.claim_id.endswith("-disposition")
    }
    for index, variant in enumerate(source_snapshot.variants, start=1):
        lines.extend(
            [
                f"- Variant {index} ({_redact_text(variant.variant_role, redacted_internal_ids)}): "
                f"{_redact_text(variant.question, redacted_internal_ids)}",
                "  - Distinguishing test: "
                + _redact_text(
                    f"{variant.distinct_from_siblings} The discriminating observation is "
                    f"{variant.discriminating_observation}",
                    redacted_internal_ids,
                ),
            ]
        )
        if plan_claim := plan_claims.get(variant.variant_id):
            lines.append(
                "  - Planned analysis: " + _redact_text(plan_claim.text, redacted_internal_ids)
            )
        elif disposition_claim := disposition_claims.get(variant.variant_id):
            lines.append(
                "  - Planning disposition: "
                + _redact_text(disposition_claim.text, redacted_internal_ids)
            )
        lines.append(
            "  - What would support or weaken it: "
            + _redact_text(
                _join_sentences(
                    [
                        variant.positive_result_consequence,
                        variant.negative_result_consequence,
                        variant.null_result_consequence,
                    ]
                ),
                redacted_internal_ids,
            )
        )
    lines.extend(
        [
            "",
            "## Competing Explanations And Controls",
            "",
            _redact_text(
                _claim_text(packet, "claim-competing-explanations"), redacted_internal_ids
            ),
            "",
            "## Outcome Meanings",
            "",
            _redact_text(_claim_text(packet, "claim-outcome-meanings"), redacted_internal_ids),
            "",
            "## Planning Status and Limits",
            "",
            _redact_text(_claim_text(packet, "claim-limitations"), redacted_internal_ids),
            "",
            f"- Dataset statements are labeled `{packet.dataset_claim_status.value}`; planner-authored "
            "locators or digests alone do not verify an observation.",
            f"- Dataset grounding here reached {_public_grounding_phrase(packet.dataset_grounding_level)}; "
            "it includes no scientific-result values or execution outputs.",
            "- A separate bridge approval is still required before downstream execution artifacts.",
            "",
        ]
    )
    return "\n".join(lines).strip() + "\n"


_PUBLIC_GROUNDING_PHRASE: dict[DatasetGroundingLevel, str] = {
    DatasetGroundingLevel.UNKNOWN: "an unknown inspection depth",
    DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY: (
        "repository documentation and inventory only (no schema, sample, or structural inspection)"
    ),
    DatasetGroundingLevel.SCHEMA_METADATA_INSPECTED: "dataset schema and metadata inspection",
    DatasetGroundingLevel.SAMPLE_INSPECTED: "bounded inspection of dataset samples",
    DatasetGroundingLevel.FULL_LOCAL_STRUCTURAL_AVAILABLE: (
        "full local structural availability of the dataset"
    ),
}


def _public_grounding_phrase(grounding: DatasetGroundingLevel) -> str:
    """Human-readable clause for the derived dataset-grounding level (public dossier)."""
    return _PUBLIC_GROUNDING_PHRASE.get(
        grounding, _PUBLIC_GROUNDING_PHRASE[DatasetGroundingLevel.DOCUMENTATION_INVENTORY_ONLY]
    )


def _public_authority_statement(authority: ReviewAuthority) -> str:
    if authority == ReviewAuthority.REAL_HUMAN_EXPERT:
        return "This dossier was authorized by a real human expert review import."
    if authority == ReviewAuthority.AUTOMATED:
        return (
            "This dossier was authorized by automated independent review; no human review has "
            "been imported."
        )
    if authority == ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE:
        return (
            "This dossier was authorized only by a development model-surrogate review and "
            "cannot stand in for real human expert approval."
        )
    return "This dossier has no serious review authority."


def _claim_text(packet: GenericDossierWritingPacket, claim_id: str) -> str:
    for claim in packet.claims:
        if claim.claim_id == claim_id:
            return claim.text
    raise ValueError("generic public renderer missing claim: " + claim_id)


def _section_id_for_claim(packet: GenericDossierWritingPacket, claim_id: str) -> str:
    for section in packet.sections:
        if claim_id in section.claim_ids:
            return section.section_id
    return ""


def _variant_section_title(packet: GenericDossierWritingPacket) -> str:
    for section in packet.sections:
        if section.section_id == "variant_plans":
            return section.title
    raise ValueError("generic public renderer missing variant section")


def _is_variant_planning_outcome_claim(claim: GenericDossierClaim) -> bool:
    return claim.claim_id.endswith(("-plan", "-disposition"))


def _source_snapshot_paths_for_claim(claim: GenericDossierClaim) -> list[str]:
    if _is_variant_planning_outcome_claim(claim):
        return []
    if claim.scope == GenericDossierClaimScope.VARIANT and claim.variant_id:
        return [
            f"variants[{claim.variant_id}].question",
            f"variants[{claim.variant_id}].variant_role",
            f"variants[{claim.variant_id}].distinct_from_siblings",
            f"variants[{claim.variant_id}].discriminating_observation",
            f"variants[{claim.variant_id}].dataset_leverage_hypothesis",
            f"variants[{claim.variant_id}].positive_result_consequence",
            f"variants[{claim.variant_id}].negative_result_consequence",
            f"variants[{claim.variant_id}].null_result_consequence",
        ]
    if claim.claim_id == "claim-family-question":
        return ["family_summary"]
    if claim.claim_id == "claim-scientific-motivation":
        return ["shared_scientific_tension"]
    if claim.claim_id == "claim-dataset-leverage":
        return ["variants[].dataset_leverage_hypothesis"]
    if claim.claim_id == "claim-competing-explanations":
        return ["variants[].competing_explanations"]
    if claim.claim_id == "claim-outcome-meanings":
        return [
            "variants[].positive_result_consequence",
            "variants[].negative_result_consequence",
            "variants[].null_result_consequence",
        ]
    return []


def _redact_text(text: str, redacted_internal_ids: list[str]) -> str:
    redacted = text
    for token in sorted(redacted_internal_ids, key=len, reverse=True):
        redacted = redacted.replace(token, "an internal audit identifier")
    return redacted


def validate_generic_public_dossier_quality(
    markdown: str,
    *,
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
) -> list[str]:
    errors: list[str] = []
    for internal_id in [
        source_snapshot.branch_id,
        source_snapshot.question_family_id,
        source_snapshot.source_snapshot_id,
        *[variant.variant_id for variant in source_snapshot.variants],
    ]:
        if internal_id and internal_id in markdown:
            errors.append("public dossier leaked internal ID: " + internal_id)
    for label in find_public_markdown_jargon(markdown):
        errors.append("public dossier contains internal jargon: " + label)

    variant_blocks = _public_variant_blocks(markdown)
    if len(variant_blocks) != len(source_snapshot.variants):
        errors.append(
            "public dossier variant block count mismatch: "
            f"{len(variant_blocks)} != {len(source_snapshot.variants)}"
        )
        return errors

    normalized_blocks = []
    for block in variant_blocks:
        block_tokens = _meaningful_tokens(block)
        normalized_blocks.append(" ".join(sorted(block_tokens)))
    if len(normalized_blocks) != len(set(normalized_blocks)):
        errors.append("public dossier repeats identical variant blocks")
    return errors


def validate_generic_writing_packet_quality(packet: GenericDossierWritingPacket) -> list[str]:
    """Return only identity/coverage blockers; prose quality is advisory in Phase 6-P."""

    return []


def generic_public_dossier_quality_warnings(
    markdown: str,
    *,
    source_snapshot: QuestionFamilyScientificSourceSnapshot,
) -> list[str]:
    warnings: list[str] = []
    lower = markdown.lower()
    for phrase in _PLACEHOLDER_PUBLIC_PHRASES:
        if phrase in lower:
            warnings.append("placeholder public dossier text: " + phrase)
    variant_blocks = _public_variant_blocks(markdown)
    for block, variant in zip(variant_blocks, source_snapshot.variants, strict=False):
        block_tokens = _meaningful_tokens(block)
        source_tokens = _meaningful_tokens(
            " ".join(
                [
                    variant.question,
                    variant.variant_role,
                    variant.distinct_from_siblings,
                    variant.discriminating_observation,
                ]
            )
        )
        if len(block_tokens) < 14:
            warnings.append(f"variant public block is too thin: {variant.variant_id}")
        if len(block_tokens & source_tokens) < 4:
            warnings.append(
                "variant public block lacks source semantic overlap: " + variant.variant_id
            )
    return warnings


def generic_writing_packet_quality_warnings(
    packet: GenericDossierWritingPacket,
) -> list[str]:
    warnings: list[str] = []
    for claim in packet.claims:
        lower = claim.text.lower()
        for phrase in _PLACEHOLDER_PUBLIC_PHRASES:
            if phrase in lower:
                warnings.append("placeholder claim text: " + claim.claim_id)
        if claim.scope == GenericDossierClaimScope.VARIANT:
            cleaned = claim.text.replace(claim.variant_id, "")
            if len(_meaningful_tokens(cleaned)) < 10:
                warnings.append("variant claim is too thin: " + claim.claim_id)
    return warnings


def _public_variant_blocks(markdown: str) -> list[str]:
    return [
        line.removeprefix("- ").strip()
        for line in markdown.splitlines()
        if line.startswith("- Variant ")
    ]


def _meaningful_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z][a-z0-9]+", text.lower())
        if token not in _GENERIC_PUBLIC_STOPWORDS
        and not token.startswith("cfam")
        and token not in {"variant", "internal", "audit", "identifier"}
    }


def _build_audit_sidecar(
    *,
    branch: QuestionFamilyBranch,
    run_id: str,
    packet: GenericDossierWritingPacket,
    ledger: GenericDossierCitationLedger,
    render_manifest: GenericDossierRenderManifest,
    machine_artifact: GenericDossierMarkdownArtifact,
    public_artifact: GenericEndUserDossierMarkdownArtifact,
    translator_input: dict[str, object],
) -> GenericEndUserDossierAuditSidecar:
    source_paths = [source.artifact_path for source in ledger.sources]
    source_digests = [source.artifact_digest for source in ledger.sources]
    source_by_id = {source.source_id: source for source in ledger.sources}
    bindings = []
    for index, claim in enumerate(packet.claims, start=1):
        claim_sources = [
            source_by_id[source_id] for source_id in claim.citation_ids if source_id in source_by_id
        ]
        paths = [source.artifact_path for source in claim_sources] or source_paths
        digests = [source.artifact_digest for source in claim_sources] or source_digests
        evidence_ids = [item for item in claim.citation_ids if item in set(ledger.evidence_ids)]
        if not evidence_ids and not _is_variant_planning_outcome_claim(claim):
            evidence_ids = ledger.evidence_ids
        bindings.append(
            GenericEndUserDossierAuditBinding(
                public_label=f"Audit binding {index}",
                public_section_id=_section_id_for_claim(packet, claim.claim_id),
                public_text_digest=stable_hash(claim.text),
                internal_claim_ids=[claim.claim_id],
                internal_source_ids=claim.citation_ids,
                internal_evidence_ids=evidence_ids,
                source_artifact_paths=paths,
                source_artifact_digests=digests,
                source_snapshot_field_paths=_source_snapshot_paths_for_claim(claim),
            )
        )
    return GenericEndUserDossierAuditSidecar(
        audit_sidecar_id=_dossier_id("generic-end-user-dossier-audit", branch, run_id),
        run_id=run_id,
        branch_id=branch.branch_id,
        question_family_id=branch.question_family_id,
        context_id=branch.context_id,
        owner_session_id=branch.owner_session_id,
        source_dossier_markdown_artifact_id=machine_artifact.dossier_markdown_artifact_id,
        source_render_manifest_id=render_manifest.rendered_dossier_manifest_id,
        source_outcome_packet_id=packet.source_outcome_packet_id,
        source_review_decision_packet_id=packet.source_review_decision_packet_id,
        authority=packet.review_authority,
        provider_id=GENERIC_END_USER_TRANSLATOR_PROVIDER_ID,
        model_id=GENERIC_END_USER_TRANSLATOR_MODEL_ID,
        prompt_version=GENERIC_END_USER_DOSSIER_TRANSLATOR_PROMPT_VERSION,
        session_id=_dossier_id("generic-end-user-translator-session", branch, run_id),
        input_digest=stable_hash(translator_input),
        output_digest=stable_hash(public_artifact.model_dump(mode="json")),
        branch_event_ids=[
            event.event_id
            for event in branch.events
            if event.event_type
            in {
                QuestionFamilyBranchEventType.SCIENTIFIC_DOSSIER_PACKET_PREPARED,
                QuestionFamilyBranchEventType.SCIENTIFIC_DOSSIER_RENDERED,
            }
        ],
        redacted_internal_ids=public_artifact.redacted_internal_ids,
        bindings=bindings,
    )


def _session_snapshot(
    *,
    branch_id: str,
    session_id: str,
    provider_id: str,
    model_id: str,
    prompt_version: str,
    input_payload: BaseModel,
    output_payload: BaseModel,
    output_schema: type[BaseModel],
) -> ScientificAgentSessionSnapshot:
    return _session_snapshot_from_dict(
        branch_id=branch_id,
        session_id=session_id,
        provider_id=provider_id,
        model_id=model_id,
        prompt_version=prompt_version,
        input_payload=input_payload.model_dump(mode="json"),
        output_payload=output_payload,
        output_schema=output_schema,
    )


def _session_snapshot_from_dict(
    *,
    branch_id: str,
    session_id: str,
    provider_id: str,
    model_id: str,
    prompt_version: str,
    input_payload: dict[str, object],
    output_payload: BaseModel,
    output_schema: type[BaseModel],
) -> ScientificAgentSessionSnapshot:
    output_dict = output_payload.model_dump(mode="json")
    input_digest = scientific_agent_payload_digest(input_payload)
    output_digest = scientific_agent_payload_digest(output_dict)
    record = ScientificAgentTranscriptRecord(
        sequence=1,
        turn_id=stable_hash(
            {
                "branch_id": branch_id,
                "session_id": session_id,
                "prompt_version": prompt_version,
            }
        )[:16],
        branch_id=branch_id,
        session_id=session_id,
        provider_id=provider_id,
        model_id=model_id,
        prompt_version=prompt_version,
        input_schema="dict",
        input_payload=input_payload,
        input_digest=input_digest,
        output_schema=output_schema.__name__,
        output_payload=output_dict,
        output_digest=output_digest,
        provider_response_id="local-deterministic",
        created_at=datetime.now(UTC),
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


def _redacted_ids(
    *,
    branch: QuestionFamilyBranch,
    packet: GenericDossierWritingPacket,
    ledger: GenericDossierCitationLedger,
    render_manifest: GenericDossierRenderManifest,
    machine_artifact: GenericDossierMarkdownArtifact,
    outcome: GenericFamilyBranchOutcomePacket,
) -> list[str]:
    ids = {
        packet.run_id,
        branch.branch_id,
        branch.question_family_id,
        branch.context_id,
        branch.owner_session_id,
        packet.dossier_writing_packet_id,
        packet.citation_ledger_id,
        packet.source_outcome_packet_id,
        packet.source_review_decision_packet_id,
        render_manifest.rendered_dossier_manifest_id,
        machine_artifact.dossier_markdown_artifact_id,
        outcome.accepted_plan_draft_message_id,
        outcome.accepted_plan_draft_packet_id,
        outcome.owner_plan_review_message_id,
        outcome.independent_plan_review_message_id,
        outcome.rejection_message_id,
        outcome.escalation_message_id,
        *outcome.source_message_ids,
        *packet.allowed_citation_ids,
        *packet.evidence_ids,
        *(claim.claim_id for claim in packet.claims),
        *(event.event_id for event in branch.events),
        *(variant_id for variant_id in branch.active_variant_ids),
    }
    return sorted(item for item in ids if item)


def _workspace(output_root: str | Path, *, run_id: str, branch_id: str, name: str) -> Path:
    return Path(output_root) / run_id / "branches" / branch_id / "planner" / name


def _dossier_id(prefix: str, branch: QuestionFamilyBranch, run_id: str) -> str:
    digest = stable_hash(
        {
            "prefix": prefix,
            "run_id": run_id,
            "branch_id": branch.branch_id,
            "family_id": branch.question_family_id,
        }
    )
    return f"{prefix}-{digest[:12]}"
