"""Atomic thin run envelope and deterministic user projection.

Only the lead orchestrator mutates this manifest. Family workers return results; the orchestrator
reconciles them serially. All indexed paths are exact host-provided candidates and are validated
without recursive discovery.
"""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from ...schemas.front_half_authority import FrontHalfCeilingReason
    from ...schemas.question_scientist_context_v2 import FrontHalfAuthorityCeiling
    from ...schemas.run_outcome import FamilyRunOutcome

import yaml
from pydantic import BaseModel, ValidationError
from yaml import YAMLError

from ...io import load_model
from ...provenance import sha256_bytes, sha256_file
from ...schemas.family_failure import sanitize_family_failure_text
from ...schemas.gate_outcome import GateDecision
from ...schemas.presentation import PresentationAddonRecord
from ...schemas.question_family import QuestionFamily
from ...schemas.run_manifest import (
    ArtifactAuthority,
    ArtifactKind,
    ArtifactProjectionState,
    ArtifactRecord,
    DiagnosticClass,
    DiagnosticRecord,
    FamilyDisposition,
    PaperDisposition,
    ProductProcessingState,
    RunManifest,
    RunProcessingState,
    RunStage,
    StageRecord,
)
from .run_layout import RunPaths

_STAGE_ORDER = (
    RunStage.PAPER_HALF,
    RunStage.DATASET_HALF,
    RunStage.STAGE_C,
    RunStage.STAGE_D,
    RunStage.FRONT_LAYOUT,
    RunStage.BACK_HALF,
)


@dataclass(frozen=True)
class RunContext:
    run_id: str
    paths: RunPaths


def fresh_run_id() -> str:
    return f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"


def initialize_run(output_root: str | Path, *, run_id: str | None = None) -> RunContext:
    """Allocate exactly one run and publish its manifest followed by README.

    If the output root itself cannot be created the filesystem exception is deliberately allowed to
    escape: no run-local ledger can be written yet. Once the run root exists, every caller can record
    later failures through :func:`record_run_failure`.
    """
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    resolved_id = run_id or fresh_run_id()
    run_root = root / resolved_id
    if run_root.exists() and any(run_root.iterdir()):
        raise ValueError(
            f"run_id {resolved_id!r} already exists at {run_root} and is non-empty; resume it instead"
        )
    run_root.mkdir(parents=True, exist_ok=True)
    context = RunContext(run_id=resolved_id, paths=RunPaths(root=run_root))
    manifest = RunManifest(
        run_id=resolved_id,
        stages=[StageRecord(stage=stage) for stage in _STAGE_ORDER],
        presentation_addon=PresentationAddonRecord(),
        next_action="Complete the zero-paid preflight before scientific processing begins.",
    )
    write_run_manifest(context.paths, manifest)
    return context


def load_run_manifest(paths: RunPaths, *, allow_missing_receipts: bool = False) -> RunManifest:
    manifest = _load_run_manifest_schema(paths)
    _validate_manifest_integrity(paths, manifest, allow_missing_receipts=allow_missing_receipts)
    return manifest


def _load_run_manifest_schema(paths: RunPaths) -> RunManifest:
    return load_model(paths.run_manifest, RunManifest)


def write_run_manifest(
    paths: RunPaths,
    manifest: RunManifest,
    *,
    before_readme_promote: Callable[[Path], None] | None = None,
    integrity_ignore_paths: set[str] | None = None,
) -> RunManifest:
    """Strictly validate and atomically publish manifest first, README second.

    ``integrity_ignore_paths`` is reserved for ``record_integrity_failure``: recording an
    already-diagnosed post-promotion mutation must not be blocked by the very mismatch it is
    reporting. Every other caller leaves it unset and keeps full validation.
    """
    now = datetime.now(UTC)
    if now < manifest.created_at:
        now = manifest.created_at
    candidate = manifest.model_copy(update={"updated_at": now})
    payload = yaml.safe_dump(
        candidate.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        allow_unicode=True,
    )
    # Validate the exact rendered bytes, not only the in-memory object.
    validated = RunManifest.model_validate(yaml.safe_load(payload))
    _validate_manifest_integrity(paths, validated, ignore_paths=integrity_ignore_paths)
    old_manifest = paths.run_manifest.read_bytes() if paths.run_manifest.is_file() else None
    old_readme = paths.readme.read_bytes() if paths.readme.is_file() else None
    _atomic_replace_bytes(paths.run_manifest, payload.encode("utf-8"))
    try:
        if before_readme_promote is not None:
            before_readme_promote(paths.readme)
        _atomic_replace_bytes(paths.readme, render_run_readme(validated).encode("utf-8"))
    except Exception:
        _restore_bytes(paths.run_manifest, old_manifest)
        _restore_bytes(paths.readme, old_readme)
        raise
    return validated


def atomic_write_model(path: str | Path, value: BaseModel) -> Path:
    """Render a strict model completely and atomically replace one adjacent YAML artifact."""
    target = Path(path)
    payload = yaml.safe_dump(
        value.model_dump(mode="json", exclude_none=True), sort_keys=False, allow_unicode=True
    ).encode("utf-8")
    # Re-validate the exact rendered representation through the model's concrete class.
    type(value).model_validate(yaml.safe_load(payload))
    _atomic_replace_bytes(target, payload)
    return target


def atomic_write_text(path: str | Path, text: str) -> Path:
    target = Path(path)
    payload = (text if text.endswith("\n") else text + "\n").encode("utf-8")
    _atomic_replace_bytes(target, payload)
    return target


def promote_model_artifact(
    context: RunContext,
    *,
    value: BaseModel,
    destination: str | Path,
    kind: ArtifactKind,
    processing_state: ProductProcessingState,
    authority: ArtifactAuthority,
    paper_id: str = "",
    family_id: str = "",
    source_context_digest: str = "",
    after_promote: Callable[[Path], None] | None = None,
    after_index: Callable[[Path], None] | None = None,
) -> Path:
    """Render a typed sibling candidate and promote bytes/index/callback as one rollback unit."""
    destination_path = Path(destination)
    candidate = _candidate_path(context, destination_path)
    try:
        atomic_write_model(candidate, value)
        if not promote_indexed_artifact(
            context,
            source=candidate,
            destination=destination_path,
            kind=kind,
            processing_state=processing_state,
            authority=authority,
            paper_id=paper_id,
            family_id=family_id,
            source_context_digest=source_context_digest,
            after_promote=after_promote,
            after_index=after_index,
        ):
            raise OSError(f"failed to promote current artifact {destination_path.name}")
        return destination_path
    finally:
        candidate.unlink(missing_ok=True)


def promote_text_artifact(
    context: RunContext,
    *,
    text: str,
    destination: str | Path,
    kind: ArtifactKind,
    processing_state: ProductProcessingState,
    authority: ArtifactAuthority,
    paper_id: str = "",
    family_id: str = "",
    source_context_digest: str = "",
    after_promote: Callable[[Path], None] | None = None,
    after_index: Callable[[Path], None] | None = None,
) -> Path:
    """Render a text sibling candidate and promote bytes/index/callback as one rollback unit."""
    destination_path = Path(destination)
    candidate = _candidate_path(context, destination_path)
    try:
        atomic_write_text(candidate, text)
        if not promote_indexed_artifact(
            context,
            source=candidate,
            destination=destination_path,
            kind=kind,
            processing_state=processing_state,
            authority=authority,
            paper_id=paper_id,
            family_id=family_id,
            source_context_digest=source_context_digest,
            after_promote=after_promote,
            after_index=after_index,
        ):
            raise OSError(f"failed to promote current artifact {destination_path.name}")
        return destination_path
    finally:
        candidate.unlink(missing_ok=True)


def _candidate_path(context: RunContext, destination: Path) -> Path:
    relative = destination.absolute().relative_to(context.paths.root.absolute()).as_posix()
    digest = hashlib.sha256(relative.encode()).hexdigest()[:12]
    suffix = destination.suffix or ".artifact"
    return context.paths.artifacts / ".candidates" / f"{digest}-{uuid4().hex}{suffix}"


def write_family_fallback(
    context: RunContext,
    *,
    family: QuestionFamily,
    disposition: FamilyDisposition,
    retained: list[ArtifactRecord] | None = None,
) -> Path:
    """Publish a scientific but non-fabricating fallback for a clean persisted family."""
    from ...schemas.multi_family_dossier import FamilyOutcomeAuditSidecar

    slug = _family_slug_for_manifest(context, family.question_family_id)
    path = context.paths.family_dossier(slug)
    records = retained or []
    lines = [
        f"# {family.title}",
        "",
        family.summary,
        "",
        "## Scientific tension",
        "",
        family.shared_scientific_tension,
        "",
        "## Question variants",
        "",
    ]
    for variant in family.variants:
        lines.extend(
            [
                f"### {variant.variant_role}",
                "",
                variant.seed.question,
                "",
                f"Why it matters: {variant.seed.why_scientifically_important}",
                "",
                f"Distinctive focus: {variant.distinct_from_siblings}",
                "",
                (f"Conditional dataset leverage: {variant.seed.dataset_leverage_hypothesis}"),
                "",
                f"Discriminating observation: {variant.seed.discriminating_observation}",
                "",
                "Competing explanations:",
                *[f"- {explanation}" for explanation in variant.seed.competing_explanations],
                "",
            ]
        )
    lines.extend(["## What the possible outcomes would mean", ""])
    for variant in family.variants:
        lines.extend(
            [
                f"### {variant.variant_role}",
                "",
                f"- Positive pattern: {variant.seed.positive_result_consequence}",
                f"- Negative pattern: {variant.seed.negative_result_consequence}",
                f"- Null or ambiguous pattern: {variant.seed.null_result_consequence}",
                "",
            ]
        )
    claim_status, evidence_note = _fallback_dataset_evidence_status(context, records)
    lines.extend(
        [
            "## Dataset evidence status",
            "",
            f"- Claim status: `{claim_status}`",
            f"- {evidence_note}",
            "- Dataset leverage statements above remain hypotheses unless a retained, host-bound source supports them.",
            "",
            "## Current disposition",
            "",
            f"- Shortlist: `{disposition.shortlist.value}`",
            f"- Planning: `{disposition.planning_state.value}`",
            f"- Closure: `{disposition.closure_state.value}`",
            f"- Authority: `{disposition.authority.value}`",
        ]
    )
    if disposition.reason:
        lines.append(f"- Status note: {disposition.reason}")
    lines.extend(["", "## Retained products", ""])
    if records:
        for record in sorted(records, key=lambda item: (item.kind.value, item.path)):
            relative_link = os.path.relpath(context.paths.root / record.path, path.parent)
            lines.append(
                f"- [{record.kind.value}]({Path(relative_link).as_posix()}) "
                f"— `{record.authority.value}`, digest `{record.sha256[:12]}`"
            )
    else:
        lines.append("- No validated downstream product is available.")
    terminal_audits = [
        context.paths.root / record.path
        for record in records
        if Path(record.path).name == "terminal_outcome_audit.yaml"
    ]
    terminal_details: list[str] = []
    if len(terminal_audits) == 1:
        try:
            terminal_audit = load_model(terminal_audits[0], FamilyOutcomeAuditSidecar)
        except (OSError, ValueError):
            terminal_audit = None
        if terminal_audit is not None and (
            terminal_audit.question_family_id == family.question_family_id
        ):
            terminal_details = list(terminal_audit.blockers)
    if terminal_details:
        lines.extend(["", "## Retained planning and review disposition", ""])
        lines.extend(f"- {detail}" for detail in terminal_details)
    retained_plan_projection = _retained_plan_projection(
        context,
        records,
        family_id=family.question_family_id,
    )
    if retained_plan_projection:
        lines.extend(["", retained_plan_projection])
    lines.extend(["", "## Limitations", ""])
    if any(record.kind == ArtifactKind.MACHINE_DOSSIER for record in records):
        lines.append(
            "A reviewed machine dossier was retained, but its normal public view is unavailable. "
            "This fallback does not change that artifact's authority or claims."
        )
    elif {"owner_plan_review.yaml", "independent_plan_review.yaml"} <= {
        Path(record.path).name for record in records if record.kind == ArtifactKind.PLAN
    }:
        lines.append(
            "Accepted planning and review artifacts were retained, but dossier closure failed "
            "before a public dossier could be produced."
        )
    elif terminal_details:
        lines.append(
            "A planning or review terminal was retained and summarized above. It is useful for "
            "inspection, but it does not carry accepted-plan authority."
        )
    else:
        lines.append("No acceptable plan or feasibility conclusion was produced for this family.")
    diagnostics = [
        item
        for item in load_run_manifest(context.paths).diagnostics
        if item.family_id == family.question_family_id
    ]
    if diagnostics:
        lines.extend(["", "## Diagnostics", ""])
        for diagnostic in diagnostics:
            link = ""
            if diagnostic.internal_path:
                target = context.paths.root / diagnostic.internal_path
                link = f" ([details]({Path(os.path.relpath(target, path.parent)).as_posix()}))"
            lines.append(
                f"- `{diagnostic.diagnostic_class.value}/{diagnostic.code}`: "
                f"{sanitize_family_failure_text(diagnostic.public_message)}{link}"
            )
    lines.extend(
        [
            "This page preserves the generated scientific question; it is not a scientific finding or downstream authorization.",
            "",
            "## Next action",
            "",
            "Inspect the run diagnostic and retained products before deciding whether to revise inputs or resume.",
            "",
        ]
    )
    # A fallback page is still useful for a hard-integrity terminal, but it must not soften the
    # authoritative FAILED closure state merely because the public reason was sanitized prose.
    if disposition.closure_state != ProductProcessingState.FAILED:
        disposition.closure_state = ProductProcessingState.DEGRADED
    disposition.dossier_path = path.relative_to(context.paths.root).as_posix()

    def _publish_disposition(_path: Path) -> None:
        upsert_family_disposition(context, disposition)

    promote_text_artifact(
        context,
        text="\n".join(lines),
        destination=path,
        kind=ArtifactKind.FAMILY_DOSSIER,
        processing_state=ProductProcessingState.DEGRADED,
        authority=disposition.authority,
        family_id=family.question_family_id,
        after_index=_publish_disposition,
    )
    return path


def _retained_plan_projection(
    context: RunContext,
    records: list[ArtifactRecord],
    *,
    family_id: str,
) -> str:
    """Return the code-generated safe plan section from one retained warning dossier.

    The terminal source is already identity/digest checked before it enters the run manifest.  This
    helper additionally verifies its indexed digest and copies only the bounded section produced by
    ``write_development_outcome_dossier``; arbitrary raw planner Markdown is never discovered.
    """

    candidates = [
        record
        for record in records
        if record.family_id == family_id
        and record.kind == ArtifactKind.DIAGNOSTIC
        and Path(record.path).name == "terminal_outcome_source.md"
    ]
    if len(candidates) != 1:
        return ""
    record = candidates[0]
    source = context.paths.root / record.path
    try:
        validate_exact_artifact(context.paths.root, source)
        if sha256_file(source) != record.sha256:
            return ""
        text = source.read_text(encoding="utf-8")
    except (OSError, ValueError, UnicodeError):
        return ""
    start_marker = "## Safely retained planner draft"
    end_marker = "\n## Retained Outcome And Review Basis"
    start = text.find(start_marker)
    if start < 0:
        return ""
    end = text.find(end_marker, start)
    if end < 0:
        return ""
    return text[start:end].strip()


def _fallback_dataset_evidence_status(
    context: RunContext,
    records: list[ArtifactRecord],
) -> tuple[str, str]:
    """Summarize only validated evidence labels; never interpret planner-authored findings."""

    from ...schemas.generic_scientific_source import DatasetClaimStatus
    from ...schemas.question_family_branch import QuestionFamilyInspectionEvidence

    evidence_records = [
        record for record in records if record.kind == ArtifactKind.INSPECTION_EVIDENCE
    ]
    if not evidence_records:
        return "unknown", "No validated planner inspection evidence was retained."
    statuses: list[DatasetClaimStatus] = []
    for record in evidence_records:
        candidate = context.paths.root / record.path
        try:
            validate_exact_artifact(context.paths.root, candidate)
            evidence = load_model(candidate, QuestionFamilyInspectionEvidence)
        except (OSError, ValueError):
            continue
        statuses.append(evidence.dataset_claim_status)
    if statuses and all(status == DatasetClaimStatus.VERIFIED for status in statuses):
        return (
            "verified",
            "The retained evidence sources have host-owned byte bindings, but this fallback does not reinterpret their findings.",
        )
    return (
        "unverified",
        "Planner inspection records were retained, but their locators and digests do not by themselves prove the stated observations.",
    )


def _family_slug_for_manifest(context: RunContext, family_id: str) -> str:
    """Assign the stable collision-safe slug over the complete manifest family identity set."""
    from .run_layout import assign_family_slugs

    manifest = _load_run_manifest_schema(context.paths)
    ids = sorted({family_id, *(item.family_id for item in manifest.families)})
    return assign_family_slugs(ids)[family_id]


def render_run_readme(manifest: RunManifest) -> str:
    lines = [
        f"# Run {manifest.run_id}",
        "",
        f"- State: `{manifest.run_state.value}`",
        f"- Last update: `{manifest.updated_at.isoformat()}`",
        "",
        "## Stages",
        "",
    ]
    for stage in manifest.stages:
        receipt = f" ([receipt]({stage.receipt_path}))" if stage.receipt_path else ""
        lines.append(f"- {stage.stage.value}: `{stage.processing_state.value}`{receipt}")
    lines.extend(["", "## Detailed presentation add-on", ""])
    presentation = manifest.presentation_addon
    if presentation is None:
        lines.append("- State: `not recorded` (legacy six-stage manifest)")
    else:
        receipt = f" ([receipt]({presentation.receipt_path}))" if presentation.receipt_path else ""
        lines.append(f"- State: `{presentation.state.value}`{receipt}")
        for output in presentation.outputs:
            label = output.kind.value.replace("_", " ")
            lines.append(f"- [{label}]({output.path})")
        if presentation.warning:
            lines.append(
                "- Presentation warning: " + sanitize_family_failure_text(presentation.warning)
            )
    lines.extend(["", "## Artifacts", ""])
    if manifest.artifacts:
        for artifact in manifest.artifacts:
            owner = artifact.family_id or artifact.paper_id
            owner_text = f" — {owner}" if owner else ""
            projection_text = (
                f" / `{artifact.projection_state.value}` for context "
                f"`{artifact.source_context_digest[:12]}`"
                if artifact.source_context_digest
                else ""
            )
            lines.append(
                f"- [{artifact.kind.value}]({artifact.path}) — `{artifact.processing_state.value}` / "
                f"`{artifact.authority.value}`{projection_text}{owner_text}"
            )
    else:
        lines.append("- No scientific artifacts have been produced yet.")
    lines.extend(["", "## Papers", ""])
    if manifest.papers:
        for paper in manifest.papers:
            reason = f" — {paper.reason}" if paper.reason else ""
            case = f" ([PaperCase]({paper.paper_case_path}))" if paper.paper_case_path else ""
            trace = (
                f" ([formation trace]({paper.formation_trace_path}))"
                if paper.formation_trace_path
                else ""
            )
            lines.append(
                f"- {paper.input_identity}: `{paper.disposition.value}`{case}{trace}{reason}"
            )
    else:
        lines.append("- Paper processing has not started.")
    lines.extend(["", "## Question families", ""])
    if manifest.families:
        for family in manifest.families:
            link = f" ([dossier]({family.dossier_path}))" if family.dossier_path else ""
            reason = f" — {family.reason}" if family.reason else ""
            lines.append(
                f"- {family.title or 'Question family'}: shortlist `{family.shortlist.value}`, "
                f"planning `{family.planning_state.value}`, closure `{family.closure_state.value}`, "
                f"authority `{family.authority.value}`{link}{reason}"
            )
    else:
        lines.append("- Question-family generation has not completed.")
    lines.extend(["", "## Diagnostics", ""])
    if manifest.diagnostics:
        for diagnostic in manifest.diagnostics:
            link = f" ([details]({diagnostic.internal_path}))" if diagnostic.internal_path else ""
            lines.append(
                f"- `{diagnostic.diagnostic_class.value}/{diagnostic.code}`: "
                f"{sanitize_family_failure_text(diagnostic.public_message)}{link}"
            )
    else:
        lines.append("- No diagnostics recorded.")
    lines.extend(["", "## Next action", "", manifest.next_action, ""])
    summaries = [
        artifact for artifact in manifest.artifacts if artifact.kind == ArtifactKind.SUMMARY
    ]
    if summaries:
        preferred = next(
            (artifact for artifact in summaries if artifact.path == "run_terminal.md"),
            summaries[-1],
        )
        lines.extend([f"The terminal [summary]({preferred.path}) is available.", ""])
    return "\n".join(lines)


def set_run_state(
    context: RunContext,
    state: RunProcessingState,
    *,
    next_action: str,
) -> RunManifest:
    manifest = load_run_manifest(context.paths)
    manifest.run_state = state
    manifest.next_action = next_action
    return write_run_manifest(context.paths, manifest)


def set_stage_state(
    context: RunContext,
    stage: RunStage,
    state: ProductProcessingState,
    *,
    receipt_path: str = "",
) -> RunManifest:
    manifest = load_run_manifest(context.paths)
    record = next(item for item in manifest.stages if item.stage == stage)
    record.processing_state = state
    if receipt_path:
        record.receipt_path = receipt_path
    return write_run_manifest(context.paths, manifest)


def upsert_paper_disposition(context: RunContext, disposition: PaperDisposition) -> RunManifest:
    manifest = load_run_manifest(context.paths)
    manifest.papers = [
        item for item in manifest.papers if item.input_identity != disposition.input_identity
    ]
    manifest.papers.append(disposition)
    manifest.papers.sort(key=lambda item: item.input_identity)
    return write_run_manifest(context.paths, manifest)


def upsert_family_disposition(context: RunContext, disposition: FamilyDisposition) -> RunManifest:
    manifest = load_run_manifest(context.paths)
    manifest.families = [
        item for item in manifest.families if item.family_id != disposition.family_id
    ]
    manifest.families.append(disposition)
    manifest.families.sort(key=lambda item: item.family_id)
    return write_run_manifest(context.paths, manifest)


def reconcile_family_inventory(context: RunContext, *, current_family_ids: set[str]) -> RunManifest:
    """Remove prior Stage-D family rows and owned artifacts that are absent from the new batch."""
    manifest = load_run_manifest(context.paths)
    manifest.families = [item for item in manifest.families if item.family_id in current_family_ids]
    manifest.artifacts = [
        item
        for item in manifest.artifacts
        if not item.family_id or item.family_id in current_family_ids
    ]
    return write_run_manifest(context.paths, manifest)


def add_diagnostic(
    context: RunContext,
    *,
    diagnostic_class: DiagnosticClass,
    code: str,
    public_message: str,
    internal_path: str = "",
    paper_id: str = "",
    family_id: str = "",
) -> DiagnosticRecord:
    manifest = load_run_manifest(context.paths)
    digest = hashlib.sha256(
        f"{context.run_id}:{len(manifest.diagnostics)}:{diagnostic_class}:{code}".encode()
    ).hexdigest()[:12]
    record = DiagnosticRecord(
        diagnostic_id=f"diagnostic-{digest}",
        diagnostic_class=diagnostic_class,
        code=code,
        public_message=public_message,
        internal_path=internal_path,
        paper_id=paper_id,
        family_id=family_id,
    )
    manifest.diagnostics.append(record)
    write_run_manifest(context.paths, manifest)
    return record


def retire_current_run_diagnostics(context: RunContext, *, codes: Sequence[str]) -> RunManifest:
    """Retire superseded generic run-level diagnostics from the current reader projection.

    Resume receipts and paid-leaf captures retain the historical attempt. This helper removes only
    exact, caller-supplied generic codes after a later execution reached a new durable state; it
    cannot clear integrity, scientific, paper, or family diagnostics by broad class matching.
    """

    selected = set(codes)
    manifest = load_run_manifest(context.paths)
    retained_diagnostics = [
        diagnostic
        for diagnostic in manifest.diagnostics
        if not (
            diagnostic.code in selected
            and not diagnostic.paper_id
            and not diagnostic.family_id
            and not diagnostic.internal_path
        )
    ]
    retired = len(retained_diagnostics) != len(manifest.diagnostics)
    manifest.diagnostics = retained_diagnostics
    if retired:
        manifest.artifacts = [
            artifact
            for artifact in manifest.artifacts
            if artifact.path != context.paths.interruption_summary.name
        ]
    persisted = write_run_manifest(context.paths, manifest)
    if retired:
        context.paths.interruption_summary.unlink(missing_ok=True)
    return persisted


def record_run_failure(
    context: RunContext,
    *,
    code: str,
    diagnostic_class: DiagnosticClass = DiagnosticClass.PROGRAMMER_FAULT,
    public_message: str = "The run stopped before it could complete; earlier products remain available.",
    failed: bool = True,
) -> RunManifest:
    add_diagnostic(
        context,
        diagnostic_class=diagnostic_class,
        code=code,
        public_message=public_message,
    )
    manifest = set_run_state(
        context,
        RunProcessingState.FAILED if failed else RunProcessingState.INCOMPLETE,
        next_action="Inspect the diagnostics and retained products, correct the cause, then resume.",
    )
    from .run_layout import write_run_interruption_summary

    terminal_path = write_run_interruption_summary(
        context.paths,
        manifest,
        diagnostic_class=diagnostic_class,
        code=code,
        public_message=public_message,
        resume_valid=True,
    )
    if not index_existing_artifact(
        context,
        terminal_path,
        kind=ArtifactKind.SUMMARY,
        processing_state=ProductProcessingState.DEGRADED,
        authority=ArtifactAuthority.UNKNOWN,
    ):
        raise OSError("run interruption terminal could not be indexed")
    return load_run_manifest(context.paths)


def record_integrity_failure(
    context: RunContext,
    *,
    mismatched_paths: Sequence[str],
    code: str = "indexed_artifact_integrity_mismatch",
) -> RunManifest:
    """CLIM-13: persist an honest INTEGRITY terminal for post-promotion artifact mutations.

    The mutated bytes never regain authority (their records keep the promoted digest and every
    trusting read still fails closed); this only makes the failure RECORDABLE — a FAILED run
    state plus one sanitized INTEGRITY diagnostic per mutated run-relative path — so no run ever
    again needs an off-product manual reindex just to report its own integrity violation.
    Idempotent: an already-recorded (code, path) pair is not duplicated. Sibling artifact,
    family, and diagnostic records are left untouched and stay visible.
    """
    if not mismatched_paths:
        raise ValueError("record_integrity_failure requires at least one mismatched path")
    ignore = set(mismatched_paths)
    manifest = _load_run_manifest_schema(context.paths)
    _validate_manifest_integrity(context.paths, manifest, ignore_paths=ignore)
    already = {
        (record.code, record.internal_path)
        for record in manifest.diagnostics
        if record.diagnostic_class == DiagnosticClass.INTEGRITY
    }
    for relative in mismatched_paths:
        if (code, relative) in already:
            continue
        digest = hashlib.sha256(
            f"{context.run_id}:{len(manifest.diagnostics)}:{DiagnosticClass.INTEGRITY}:{code}".encode()
        ).hexdigest()[:12]
        manifest.diagnostics.append(
            DiagnosticRecord(
                diagnostic_id=f"diagnostic-{digest}",
                diagnostic_class=DiagnosticClass.INTEGRITY,
                code=code,
                public_message=(
                    f"An indexed artifact was mutated after promotion: {relative}. The run is "
                    "honestly failed; the mutated bytes hold no authority, and retained sibling "
                    "products remain readable."
                ),
                internal_path=relative,
            )
        )
    manifest.run_state = RunProcessingState.FAILED
    manifest.next_action = (
        "Inspect the integrity diagnostics; restore the artifact from its authoritative source "
        "or close the run. Mutated bytes are never re-promoted."
    )
    from .run_layout import write_run_interruption_summary

    terminal_path = write_run_interruption_summary(
        context.paths,
        manifest,
        diagnostic_class=DiagnosticClass.INTEGRITY,
        code=code,
        public_message=(
            "Artifact integrity validation stopped this run. Mutated bytes hold no authority; "
            "retained sibling products remain visible."
        ),
        resume_valid=False,
    )
    relative = terminal_path.relative_to(context.paths.root).as_posix()
    digest = sha256_file(terminal_path)
    identity = f"{ArtifactKind.SUMMARY.value}:{relative}::"
    manifest.artifacts = [item for item in manifest.artifacts if item.path != relative]
    manifest.artifacts.append(
        ArtifactRecord(
            artifact_id=f"artifact-{hashlib.sha256(identity.encode()).hexdigest()[:12]}",
            kind=ArtifactKind.SUMMARY,
            path=relative,
            sha256=digest,
            processing_state=ProductProcessingState.DEGRADED,
            authority=ArtifactAuthority.UNKNOWN,
        )
    )
    manifest.artifacts.sort(key=lambda item: (item.kind.value, item.family_id, item.paper_id))
    ignore.discard(relative)
    return write_run_manifest(context.paths, manifest, integrity_ignore_paths=ignore)


def record_detected_integrity_failure(paths: RunPaths) -> list[str]:
    """Detection-site helper: persist the honest INTEGRITY terminal for a mutated run.

    Called from except-branches after a trusting read raised. Returns the mismatched
    run-relative paths (empty when the failure was something other than an artifact
    mutation, in which case nothing is recorded and the caller re-raises its original
    error). Never raises on the recording path itself beyond genuinely unreadable state.
    """
    mismatched = collect_integrity_mismatches(paths)
    if mismatched:
        record_integrity_failure(
            RunContext(run_id=paths.root.name, paths=paths), mismatched_paths=mismatched
        )
    return mismatched


def index_gate_diagnostics(context: RunContext) -> int:
    """Index actionable gate diagnostics into the run manifest. Returns the indexed count.

    The gates are good at WRITING per-artifact diagnostics and were blind at SURFACING them.
    Measured on the 2026-07-30 climate leg: 24 artifacts did not reach the reader (2 papers, 12
    formation traces, 1 pattern, 7 variants, 2 families), 29 gate diagnostics sat on disk, and the
    manifest indexed exactly ONE of them -- a run-level note about none of the 24. Since
    ``maieusis status`` and ``README.md`` read the manifest, a shepherd inspecting the run saw a
    clean ``run_state: complete`` that had lost 24 artifacts, and its bounded repair budget had
    nothing to aim at. A loss the shepherd cannot see is one it cannot back up.

    Indexing here rather than inside ``write_gate_diagnostic`` is deliberate: that function receives
    a directory, not a ``RunContext``, and threading context through all of its call sites would let
    a future call site forget. Walking the directory once at closeout cannot miss one.

    Earned accepts remain on disk as audit evidence, but are intentionally absent from the reader
    manifest: a successful run can contain hundreds of them, and a wall of passes hides the losses
    the shepherd must act on. The reader-facing ``public_message`` names each non-accept gate and
    outcome only; the rationale stays behind ``internal_path``, which is what the shepherd opens.
    """
    from ..agents.gate_diagnostics import GateDiagnostic

    diagnostics_dir = context.paths.root / "diagnostics"
    if not diagnostics_dir.is_dir():
        return 0
    manifest = load_run_manifest(context.paths)
    already = {record.internal_path for record in manifest.diagnostics if record.internal_path}
    indexed = 0
    for path in sorted(diagnostics_dir.rglob("*.yaml")):
        relative = path.relative_to(context.paths.root).as_posix()
        if relative in already:
            continue
        try:
            diagnostic = load_model(path, GateDiagnostic)
        except (OSError, ValueError, ValidationError, YAMLError):
            # A run-level note that is not a GateDiagnostic, or an unreadable file. Skipping it is
            # correct -- this indexer must never be the thing that ends a run at closeout.
            continue
        if diagnostic.decision == GateDecision.ACCEPT:
            continue
        infrastructure = diagnostic.decision == GateDecision.INFRASTRUCTURE_FAILURE
        add_diagnostic(
            context,
            diagnostic_class=(
                DiagnosticClass.INFRASTRUCTURE if infrastructure else DiagnosticClass.SCIENTIFIC
            ),
            code=f"gate_{diagnostic.gate_name}_{diagnostic.decision.value}",
            public_message=(
                f"The {diagnostic.gate_name.replace('_', ' ')} gate recorded "
                f"'{diagnostic.decision.value}'"
                + (f" for {diagnostic.artifact_label}." if diagnostic.artifact_label else ".")
            ),
            internal_path=relative,
        )
        indexed += 1
    return indexed


def seal_run_summary(
    context: RunContext,
    outcomes: Sequence[FamilyRunOutcome],
    *,
    development_surrogate: bool,
    authority_ceiling: FrontHalfAuthorityCeiling | None = None,
    ceiling_reason: FrontHalfCeilingReason | None = None,
    evidence_basis_line: str = "",
    resume_note: str = "",
    all_family_processing_finished: bool = True,
    processing_state: ProductProcessingState = ProductProcessingState.PRODUCED,
    authority: ArtifactAuthority = ArtifactAuthority.AGENT_REVIEWED,
) -> Path:
    """CLIM-13 ordered closeout checkpoint: finalize summary bytes, THEN promote, as one step.

    Every banner/basis/resume line is an INPUT to the render — nothing may write ``summary.md``
    after this returns; the index promotion is the last write touching it. Re-sealing is the
    legal crash recovery for a crash between the write and the promotion: it atomically rewrites
    and re-promotes, keeping exactly one SUMMARY record at the stable path.
    """
    from .run_layout import write_run_summary

    # Before the summary is rendered and promoted, so the closeout the reader receives is backed by
    # an index the shepherd can actually follow.
    index_gate_diagnostics(context)
    kwargs: dict[str, object] = {}
    if authority_ceiling is not None:
        kwargs["authority_ceiling"] = authority_ceiling
    summary_path = write_run_summary(
        context.paths,
        outcomes,
        development_surrogate=development_surrogate,
        ceiling_reason=ceiling_reason,
        evidence_basis_line=evidence_basis_line,
        resume_note=resume_note,
        all_family_processing_finished=all_family_processing_finished,
        **kwargs,  # type: ignore[arg-type]
    )
    if not index_existing_artifact(
        context,
        summary_path,
        kind=ArtifactKind.SUMMARY,
        processing_state=processing_state,
        authority=authority,
    ):
        raise ValueError("summary promotion failed run-boundary integrity validation")
    return summary_path


def index_existing_artifact(
    context: RunContext,
    path: str | Path,
    *,
    kind: ArtifactKind,
    processing_state: ProductProcessingState,
    authority: ArtifactAuthority,
    paper_id: str = "",
    family_id: str = "",
    source_context_digest: str = "",
    expected_sha256: str = "",
) -> bool:
    candidate = Path(path)
    try:
        relative = _validate_index_candidate(context.paths.root, candidate)
        digest = sha256_file(candidate)
        if expected_sha256 and digest != expected_sha256:
            raise ValueError("artifact digest does not match the expected host digest")
    except (OSError, ValueError):
        add_diagnostic(
            context,
            diagnostic_class=DiagnosticClass.INTEGRITY,
            code="artifact_index_rejected",
            public_message="A candidate artifact failed run-boundary integrity validation and was not indexed.",
        )
        return False

    manifest = _load_run_manifest_schema(context.paths)
    _validate_manifest_integrity(context.paths, manifest, ignore_paths={relative})
    identity = f"{kind.value}:{relative}:{paper_id}:{family_id}"
    artifact_id = f"artifact-{hashlib.sha256(identity.encode()).hexdigest()[:12]}"
    record = ArtifactRecord(
        artifact_id=artifact_id,
        kind=kind,
        path=relative,
        sha256=digest,
        processing_state=processing_state,
        authority=authority,
        source_context_digest=source_context_digest,
        paper_id=paper_id,
        family_id=family_id,
    )
    # The normalized stable path is the logical current pointer. This permits several retained PLAN
    # products for one family (draft + reviews) while a replacement at the same path removes stale
    # metadata exactly once.
    manifest.artifacts = [item for item in manifest.artifacts if item.path != relative]
    manifest.artifacts.append(record)
    manifest.artifacts.sort(key=lambda item: (item.kind.value, item.family_id, item.paper_id))
    write_run_manifest(context.paths, manifest)
    return True


def promote_indexed_artifact(
    context: RunContext,
    *,
    source: str | Path,
    destination: str | Path,
    kind: ArtifactKind,
    processing_state: ProductProcessingState,
    authority: ArtifactAuthority,
    paper_id: str = "",
    family_id: str = "",
    source_context_digest: str = "",
    expected_sha256: str = "",
    before_promote: Callable[[Path], None] | None = None,
    after_promote: Callable[[Path], None] | None = None,
    after_index: Callable[[Path], None] | None = None,
) -> bool:
    """Write a validated sibling replacement and promote it without deleting current first."""
    source_path = Path(source)
    destination_path = Path(destination)
    tmp_path: Path | None = None
    promoted = False
    old_destination = destination_path.read_bytes() if destination_path.is_file() else None
    old_manifest = context.paths.run_manifest.read_bytes()
    old_readme = context.paths.readme.read_bytes()
    try:
        load_run_manifest(context.paths)
        _validate_index_candidate(context.paths.root, source_path)
        source_stat = source_path.lstat()
        if source_path.is_symlink() or not stat.S_ISREG(source_stat.st_mode):
            raise ValueError("replacement source must be a non-symlink regular file")
        payload = source_path.read_bytes()
        digest = sha256_bytes(payload)
        if expected_sha256 and digest != expected_sha256:
            raise ValueError("replacement source digest mismatch")
        _validate_destination(context.paths.root, destination_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=destination_path.parent, prefix=f".{destination_path.name}.", suffix=".tmp"
        )
        tmp_path = Path(tmp_name)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if sha256_file(tmp_path) != digest:
            raise ValueError("replacement bytes changed before promotion")
        if before_promote is not None:
            before_promote(tmp_path)
        os.replace(tmp_path, destination_path)
        tmp_path = None
        promoted = True
        if after_promote is not None:
            after_promote(destination_path)
        indexed = index_existing_artifact(
            context,
            destination_path,
            kind=kind,
            processing_state=processing_state,
            authority=authority,
            paper_id=paper_id,
            family_id=family_id,
            source_context_digest=source_context_digest,
            expected_sha256=digest,
        )
        if not indexed:
            raise ValueError("replacement could not be indexed")
        if after_index is not None:
            after_index(destination_path)
        return True
    except Exception as exc:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        if promoted:
            _restore_bytes(destination_path, old_destination)
            _restore_bytes(context.paths.run_manifest, old_manifest)
            _restore_bytes(context.paths.readme, old_readme)
        add_diagnostic(
            context,
            diagnostic_class=DiagnosticClass.INTEGRITY,
            code="artifact_promotion_failed",
            public_message="A replacement artifact did not validate; the previous current product was retained.",
            family_id=family_id,
            paper_id=paper_id,
        )
        _mark_cross_context_projection_stale(
            context,
            destination=destination_path,
            attempted_context_digest=source_context_digest,
        )
        if isinstance(exc, (OSError, ValueError)):
            return False
        raise


def _mark_cross_context_projection_stale(
    context: RunContext,
    *,
    destination: Path,
    attempted_context_digest: str,
) -> None:
    """Keep the old current bytes, but do not relabel them as output of a new context."""
    if not attempted_context_digest:
        return
    relative = destination.absolute().relative_to(context.paths.root.absolute()).as_posix()
    manifest = _load_run_manifest_schema(context.paths)
    changed = False
    for artifact in manifest.artifacts:
        if (
            artifact.path == relative
            and artifact.source_context_digest
            and artifact.source_context_digest != attempted_context_digest
            and artifact.projection_state == ArtifactProjectionState.CURRENT
        ):
            artifact.projection_state = ArtifactProjectionState.STALE
            changed = True
    if changed:
        write_run_manifest(context.paths, manifest)


def _atomic_replace_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def _restore_bytes(path: Path, payload: bytes | None) -> None:
    if payload is None:
        path.unlink(missing_ok=True)
    else:
        _atomic_replace_bytes(path, payload)


def _validate_index_candidate(root: Path, candidate: Path) -> str:
    root_abs = root.absolute()
    candidate_abs = candidate.absolute()
    if not candidate_abs.is_relative_to(root_abs):
        raise ValueError("artifact candidate escapes the run root")
    relative_path = candidate_abs.relative_to(root_abs)
    current = root_abs
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("artifact candidate includes a symlink")
    file_stat = candidate_abs.lstat()
    if not stat.S_ISREG(file_stat.st_mode):
        raise ValueError("artifact candidate is not a regular file")
    return relative_path.as_posix()


def _validate_destination(root: Path, destination: Path) -> None:
    root_abs = root.absolute()
    destination_abs = destination.absolute()
    if not destination_abs.is_relative_to(root_abs):
        raise ValueError("artifact destination escapes the run root")
    current = root_abs
    for part in destination_abs.relative_to(root_abs).parts[:-1]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError("artifact destination parent is a symlink")


def _artifact_integrity_mismatches(
    paths: RunPaths, manifest: RunManifest, *, ignore_paths: set[str] | None = None
) -> list[str]:
    """Every indexed artifact whose bytes no longer match its promoted record (run-relative)."""
    ignored = ignore_paths or set()
    mismatched: list[str] = []
    for artifact in manifest.artifacts:
        if artifact.path in ignored:
            continue
        candidate = paths.root / artifact.path
        try:
            relative = _validate_index_candidate(paths.root, candidate)
            ok = relative == artifact.path and sha256_file(candidate) == artifact.sha256
        except (OSError, ValueError):
            ok = False
        if not ok:
            mismatched.append(artifact.path)
    return mismatched


def collect_integrity_mismatches(paths: RunPaths) -> list[str]:
    """CLIM-13: enumerate post-promotion artifact mutations WITHOUT raising.

    The trusting readers (``load_run_manifest`` / ``write_run_manifest``) stay hard and
    fail-closed; this collector exists so a detection site can turn the hard signal into a
    persisted honest INTEGRITY terminal via ``record_integrity_failure`` instead of dying
    inside its own failure-reporting path (the climate trap that forced a manual reindex).
    """
    return _artifact_integrity_mismatches(paths, _load_run_manifest_schema(paths))


def _validate_manifest_integrity(
    paths: RunPaths,
    manifest: RunManifest,
    *,
    ignore_paths: set[str] | None = None,
    allow_missing_receipts: bool = False,
) -> None:
    """Revalidate every current pointer before status or mutation trusts the manifest."""
    if manifest.run_id != paths.root.name:
        raise ValueError("run manifest identity does not match its run root")
    ignored = ignore_paths or set()
    for artifact in manifest.artifacts:
        if artifact.path in ignored:
            continue
        candidate = paths.root / artifact.path
        relative = _validate_index_candidate(paths.root, candidate)
        if relative != artifact.path or sha256_file(candidate) != artifact.sha256:
            raise ValueError(f"indexed artifact integrity mismatch: {artifact.path}")
    linked_paths = {
        *(
            path
            for paper in manifest.papers
            for path in (paper.paper_case_path, paper.formation_trace_path)
            if path
        ),
        *(family.dossier_path for family in manifest.families if family.dossier_path),
        *(
            diagnostic.internal_path
            for diagnostic in manifest.diagnostics
            if diagnostic.internal_path
        ),
    }
    for relative in linked_paths - ignored:
        if _validate_index_candidate(paths.root, paths.root / relative) != relative:
            raise ValueError(f"linked manifest path integrity mismatch: {relative}")
    for stage in manifest.stages:
        if not stage.receipt_path or stage.receipt_path in ignored:
            continue
        try:
            relative = _validate_index_candidate(paths.root, paths.root / stage.receipt_path)
        except FileNotFoundError:
            if allow_missing_receipts:
                continue
            raise
        if relative != stage.receipt_path:
            raise ValueError(f"stage receipt path integrity mismatch: {stage.receipt_path}")


def validate_exact_artifact(root: str | Path, candidate: str | Path) -> str:
    """Validate an exact candidate before any schema load/read follows its path."""
    return _validate_index_candidate(Path(root), Path(candidate))


def authority_from_status(value: object) -> ArtifactAuthority:
    text = getattr(value, "value", value)
    normalized = str(text).strip().lower()
    if "expert_reviewed" in normalized or "human_reviewed" in normalized:
        return ArtifactAuthority.VERIFIED
    if "ai_reviewed" in normalized or "automated" in normalized or "agent_reviewed" in normalized:
        return ArtifactAuthority.AGENT_REVIEWED
    if normalized and normalized not in {"unknown", "none"}:
        return ArtifactAuthority.PROVISIONAL
    return ArtifactAuthority.UNKNOWN
