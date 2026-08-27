"""Offline materialization and redraw planning for the detailed presentation add-on."""

from __future__ import annotations

import os
import stat
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ...io import load_model
from ...provenance import sha256_file
from ...schemas.novelty_admission import FamilyNoveltyAdmission, VariantNoveltyAssessment
from ...schemas.planner_run import PlannerArtifactImportManifest
from ...schemas.planning_dialogue import (
    IndependentPlanReviewMessage,
    PlanDraftMessage,
    QuestionOwnerPlanReviewMessage,
)
from ...schemas.presentation import (
    PresentationAddonReceipt,
    PresentationAddonRecord,
    PresentationAddonState,
    PresentationArtifactKind,
    PresentationArtifactRecord,
    PresentationWarningCode,
    classify_presentation_warning,
    presentation_warning_sentence,
)
from ...schemas.question_family import (
    QuestionFamily,
    QuestionFamilyBatch,
    QuestionFamilyShortlistManifest,
)
from ...schemas.question_family_branch import QuestionFamilyInspectionEvidence
from ...schemas.question_pattern import QuestionPatternBankManifest, QuestionPatternCard
from ...schemas.question_scientist_context_v2 import QuestionScientistContextPayloadV2
from ...schemas.resume import (
    FamilyCompletionRecord,
    PresentationResumeDecision,
    PresentationResumeDecisionKind,
    PresentationResumeReason,
)
from ...schemas.run_manifest import ArtifactKind, RunManifest
from ..orchestration.run_envelope import (
    RunContext,
    atomic_write_model,
    load_run_manifest,
    validate_exact_artifact,
    write_run_manifest,
)
from ..orchestration.run_layout import RunPaths, read_stage_receipts
from .context_pages import (
    PatternSourceLink,
    RenderedPresentationPage,
    render_question_families_detailed,
    render_question_patterns_detailed,
)
from .family_page import (
    render_family_detailed_page,
    validate_family_detailed_page,
    variant_ids_are_ordered_subset,
)
from .privacy import extract_public_dois, validate_detailed_markdown

_ModelT = TypeVar("_ModelT", bound=BaseModel)


@dataclass(frozen=True, slots=True)
class FamilyPresentationSource:
    completion: FamilyCompletionRecord
    original_family: QuestionFamily
    family: QuestionFamily
    plan_draft: PlanDraftMessage | None
    owner_review: QuestionOwnerPlanReviewMessage | None
    independent_review: IndependentPlanReviewMessage | None
    inspection_evidence: tuple[QuestionFamilyInspectionEvidence, ...]


@dataclass(frozen=True, slots=True)
class PresentationSources:
    patterns: tuple[QuestionPatternCard, ...]
    pattern_links: tuple[PatternSourceLink, ...]
    question_batch: QuestionFamilyBatch | None
    shortlist: QuestionFamilyShortlistManifest | None
    question_context: QuestionScientistContextPayloadV2 | None
    novelty_admissions: tuple[FamilyNoveltyAdmission, ...]
    novelty_assessments: tuple[VariantNoveltyAssessment, ...]
    families: tuple[FamilyPresentationSource, ...]
    input_paths: tuple[Path, ...]
    expected_output_paths: tuple[str, ...]
    private_tokens: tuple[str, ...]
    public_dois: tuple[str, ...]

    @property
    def input_digests(self) -> dict[str, str]:
        if not self.input_paths:
            return {}
        root = _common_run_root(self.input_paths)
        return {path.relative_to(root).as_posix(): sha256_file(path) for path in self.input_paths}


def load_presentation_sources(paths: RunPaths) -> PresentationSources:
    """Load only typed, persisted products; never inspect provider payloads or invoke factories."""
    manifest = load_run_manifest(paths)
    source_paths: set[Path] = set()

    patterns, pattern_links = _load_pattern_sources(paths, manifest, source_paths)
    batch, shortlist, context = _load_question_sources(paths, source_paths)
    novelty_admissions = _load_novelty_admissions(paths, source_paths)
    novelty_assessments = _load_novelty_assessments(paths, source_paths)
    original_family_by_id: dict[str, QuestionFamily] = {}
    if batch is not None:
        original_family_by_id.update(
            (family.question_family_id, family) for family in batch.families
        )
    current_family_by_id = dict(original_family_by_id)
    if shortlist is not None:
        current_family_by_id.update(
            (item.family.question_family_id, item.family) for item in shortlist.shortlisted
        )
    family_sources = _load_family_sources(
        paths,
        original_family_by_id=original_family_by_id,
        current_family_by_id=current_family_by_id,
        source_paths=source_paths,
    )

    expected: list[str] = []
    if patterns:
        expected.append(paths.question_patterns_detailed.relative_to(paths.root).as_posix())
    if batch is not None:
        expected.append(paths.question_families_detailed.relative_to(paths.root).as_posix())
    expected.extend(
        paths.family_dossier_detailed(source.completion.slug).relative_to(paths.root).as_posix()
        for source in family_sources
    )
    _validate_scientific_source_bindings(paths, source_paths)
    return PresentationSources(
        patterns=patterns,
        pattern_links=pattern_links,
        question_batch=batch,
        shortlist=shortlist,
        question_context=context,
        novelty_admissions=novelty_admissions,
        novelty_assessments=novelty_assessments,
        families=family_sources,
        input_paths=tuple(sorted(source_paths)),
        expected_output_paths=tuple(expected),
        private_tokens=_presentation_private_tokens(
            patterns,
            batch,
            shortlist,
            context,
            family_sources,
        ),
        public_dois=tuple(
            dict.fromkeys(
                doi for link in pattern_links for doi in extract_public_dois(link.paper_label)
            )
        ),
    )


def plan_presentation_resume(
    paths: RunPaths, *, scientific_stage_will_run: bool
) -> PresentationResumeDecision:
    """Return a soft reuse/redraw decision after the six scientific decisions are known."""
    if scientific_stage_will_run:
        return PresentationResumeDecision(
            decision=PresentationResumeDecisionKind.RENDER,
            reason=PresentationResumeReason.SCIENTIFIC_STAGE_RAN,
        )
    manifest = load_run_manifest(paths)
    record = manifest.presentation_addon
    if record is None:
        return PresentationResumeDecision(
            decision=PresentationResumeDecisionKind.RENDER,
            reason=PresentationResumeReason.NOT_RECORDED,
        )
    if record.state != PresentationAddonState.PRODUCED:
        return PresentationResumeDecision(
            decision=PresentationResumeDecisionKind.RENDER,
            reason=PresentationResumeReason.NOT_PRODUCED,
        )
    sources = load_presentation_sources(paths)
    canonical_receipt_path = paths.presentation_receipt.relative_to(paths.root).as_posix()
    if record.receipt_path != canonical_receipt_path:
        return PresentationResumeDecision(
            decision=PresentationResumeDecisionKind.RENDER,
            reason=PresentationResumeReason.RECEIPT_UNAVAILABLE,
        )
    try:
        receipt_path = paths.root / record.receipt_path
        validate_exact_artifact(paths.root, receipt_path)
        receipt = load_model(receipt_path, PresentationAddonReceipt)
    except (OSError, ValueError):
        return PresentationResumeDecision(
            decision=PresentationResumeDecisionKind.RENDER,
            reason=PresentationResumeReason.RECEIPT_UNAVAILABLE,
        )
    if (
        receipt.run_id != paths.root.name
        or receipt.status != PresentationAddonState.PRODUCED
        or bool(receipt.warning.strip())
        or receipt.input_digests != sources.input_digests
        or receipt.expected_output_paths != list(sources.expected_output_paths)
    ):
        return PresentationResumeDecision(
            decision=PresentationResumeDecisionKind.RENDER,
            reason=PresentationResumeReason.SOURCE_CHANGED,
        )
    record_digests = {item.path: item.sha256 for item in record.outputs}
    if record_digests != receipt.output_digests:
        return PresentationResumeDecision(
            decision=PresentationResumeDecisionKind.RENDER,
            reason=PresentationResumeReason.OUTPUT_UNAVAILABLE,
        )
    verified: list[str] = []
    for relative_path, digest in receipt.output_digests.items():
        candidate = paths.root / relative_path
        try:
            validate_exact_artifact(paths.root, candidate)
            actual_digest = sha256_file(candidate)
        except (OSError, ValueError):
            return PresentationResumeDecision(
                decision=PresentationResumeDecisionKind.RENDER,
                reason=PresentationResumeReason.OUTPUT_UNAVAILABLE,
            )
        if actual_digest != digest:
            return PresentationResumeDecision(
                decision=PresentationResumeDecisionKind.RENDER,
                reason=PresentationResumeReason.OUTPUT_UNAVAILABLE,
            )
        verified.append(relative_path)
    return PresentationResumeDecision(
        decision=PresentationResumeDecisionKind.REUSE,
        reason=PresentationResumeReason.REUSE_VERIFIED,
        verified_output_paths=verified,
    )


def materialize_detailed_presentation(context: RunContext) -> PresentationAddonRecord:
    """Strict add-on attempt; individual pages isolate failures and retain successful siblings."""
    if context.run_id != context.paths.root.name:
        raise ValueError("presentation context identity does not match its run root")
    started_at = datetime.now(UTC)
    sources = load_presentation_sources(context.paths)
    outputs: list[PresentationArtifactRecord] = []
    # The typed reasons, not a boolean. The previous version collected page LABELS, deduplicated
    # them, then used the list only for its truthiness and threw both the labels and the renderers'
    # typed codes away -- so fourteen of sixteen live runs persisted a byte-identical sentence that
    # named neither the page nor the cause, and told every reader to run a resume that could not fix
    # a content-level warning.
    warning_codes: list[PresentationWarningCode] = []
    #: One line per page that threw: its label and the exception class. Secret-free by
    #: construction -- no message, no provider text, no identifier.
    render_failures: list[str] = []

    def promote_page(
        *,
        label: str,
        kind: PresentationArtifactKind,
        destination: Path,
        render: Callable[[], str | RenderedPresentationPage],
        family_id: str = "",
        validator: Callable[[str], None] | None = None,
    ) -> None:
        try:
            rendered = render()
            if isinstance(rendered, RenderedPresentationPage):
                text = rendered.markdown
                warning_codes.extend(
                    classify_presentation_warning(code) for code in rendered.warnings
                )
            else:
                text = rendered
            _promote_presentation_text(
                root=context.paths.root,
                destination=destination,
                text=text,
                private_tokens=sources.private_tokens,
                allowed_public_dois=sources.public_dois,
                validator=validator,
            )
            outputs.append(
                PresentationArtifactRecord(
                    kind=kind,
                    path=destination.relative_to(context.paths.root).as_posix(),
                    sha256=sha256_file(destination),
                    family_id=family_id,
                )
            )
        except Exception as exc:  # noqa: BLE001 - page isolation is the add-on's public contract
            # A page that threw does not exist at all; that is a different fact from a page that
            # rendered with an unresolved entry, and it earns the opposite advice.
            warning_codes.append(PresentationWarningCode.PAGE_RENDER_FAILED)
            # WHICH page, and WHAT class of failure. Only the code was recorded until 2026-08-15,
            # and on the qualification set that cost a full investigation: three reading guides
            # were missing, the receipt said `page_render_failed` once, and finding out that two
            # were a redaction/validation disagreement and the third a meaningless variant-order
            # comparison took re-rendering every family by hand against the run's own artifacts.
            # The exception CLASS and the page label carry no provider text and no identifier, so
            # this stays inside the same privacy boundary the page itself is held to.
            render_failures.append(f"{label}: {type(exc).__name__}")

    if sources.patterns:
        promote_page(
            label="question-pattern page",
            kind=PresentationArtifactKind.QUESTION_PATTERNS_DETAILED,
            destination=context.paths.question_patterns_detailed,
            render=lambda: render_question_patterns_detailed(
                sources.patterns, source_links=sources.pattern_links
            ),
        )
    if sources.question_batch is not None:
        question_batch = sources.question_batch
        promote_page(
            label="question-family page",
            kind=PresentationArtifactKind.QUESTION_FAMILIES_DETAILED,
            destination=context.paths.question_families_detailed,
            render=lambda: render_question_families_detailed(
                question_batch,
                shortlist=sources.shortlist,
                topic_literature=(
                    sources.question_context.topic_literature
                    if sources.question_context is not None
                    else None
                ),
                novelty_admissions=sources.novelty_admissions,
                novelty_assessments=sources.novelty_assessments,
            ),
        )
    for family_source in sources.families:
        slug = family_source.completion.slug

        def render_family(source: FamilyPresentationSource = family_source) -> str:
            return render_family_detailed_page(
                completion=source.completion,
                original_family=source.original_family,
                family=source.family,
                plan_draft=source.plan_draft,
                owner_review=source.owner_review,
                independent_review=source.independent_review,
                inspection_evidence=source.inspection_evidence,
                # The renderer redacts against ONE family's own models; the promotion below
                # validates against the run-wide set. A token only the wide set knows therefore
                # survived redaction, failed validation, and was swallowed by the page-isolation
                # handler -- the family silently lost its reading guide, which is the residue PR
                # #109 did not close. Redaction and validation now share one set.
                extra_private_tokens=sources.private_tokens,
            )

        promote_page(
            label=f"family reading guide {len(outputs) + 1}",
            kind=PresentationArtifactKind.FAMILY_DOSSIER_DETAILED,
            destination=context.paths.family_dossier_detailed(slug),
            family_id=family_source.completion.question_family_id,
            render=render_family,
            validator=validate_family_detailed_page,
        )

    if len(outputs) != len(sources.expected_output_paths):
        warning_codes.append(PresentationWarningCode.EXPECTED_PAGE_MISSING)
    # Stable de-duplication keeps first-seen order without leaking an exception or a page identity.
    warning_codes = list(dict.fromkeys(warning_codes))
    # Derived, never hardcoded: the sentence cannot contradict the codes it came from, and a
    # WARNING state cannot exist without at least one code to explain it.
    warning = presentation_warning_sentence(warning_codes)
    state = PresentationAddonState.WARNING if warning_codes else PresentationAddonState.PRODUCED
    ended_at = datetime.now(UTC)
    output_digests = {item.path: item.sha256 for item in outputs}
    receipt = PresentationAddonReceipt(
        run_id=context.run_id,
        status=state,
        input_digests=sources.input_digests,
        expected_output_paths=list(sources.expected_output_paths),
        output_paths=list(output_digests),
        output_digests=output_digests,
        warning=warning,
        warning_codes=warning_codes,
        render_failures=render_failures,
        started_at=started_at,
        ended_at=ended_at,
    )
    _write_presentation_receipt(context.paths, receipt)
    record = PresentationAddonRecord(
        state=state,
        receipt_path=context.paths.presentation_receipt.relative_to(context.paths.root).as_posix(),
        outputs=outputs,
        warning=warning,
        warning_codes=warning_codes,
        render_failures=render_failures,
    )
    manifest = load_run_manifest(context.paths)
    manifest.presentation_addon = record
    write_run_manifest(context.paths, manifest)
    return record


def try_materialize_detailed_presentation(
    context: RunContext,
) -> PresentationAddonRecord | None:
    """Best-effort fresh-run wrapper: add-on faults never escape into scientific finalization."""
    try:
        return materialize_detailed_presentation(context)
    except Exception:  # noqa: BLE001 - the wrapper must never alter scientific completion
        # Receipt/manifest failure can make even the warning pointer unavailable. The prior
        # scientific envelope remains authoritative and the next explicit resume can retry.
        return None


def _load_pattern_sources(
    paths: RunPaths, manifest: RunManifest, source_paths: set[Path]
) -> tuple[tuple[QuestionPatternCard, ...], tuple[PatternSourceLink, ...]]:
    canonical_manifest_path = paths.corpus / "question_pattern_manifest.yaml"
    if not canonical_manifest_path.is_file():
        return (), ()
    # The paper-half stage output is the receipt-owned typed source for PaperCases and formation
    # traces.  The stable ``artifacts/`` copies are manifest-indexed projections, not stage receipt
    # outputs, so consuming them here would create a second and weaker source-of-truth path.
    from ..orchestration.resume import PaperHalfStageOutput

    paper_output = _load_source(
        paths,
        paths.stage_output("paper_half"),
        PaperHalfStageOutput,
        source_paths,
    )
    bank = _load_source(paths, canonical_manifest_path, QuestionPatternBankManifest, source_paths)
    patterns = tuple(
        _load_source(paths, paths.root / entry.pattern_path, QuestionPatternCard, source_paths)
        for entry in bank.entries
    )
    case_records = {
        record.paper_id: record
        for record in manifest.artifacts
        if record.kind == ArtifactKind.PAPER_CASE and record.paper_id
    }
    trace_records = {
        record.paper_id: record
        for record in manifest.artifacts
        if record.kind == ArtifactKind.FORMATION_TRACE and record.paper_id
    }
    cases = {item.paper_case.paper_case_id: item.paper_case for item in paper_output.accepted}
    traces = {item.trace_id: item for item in paper_output.traces}
    links: list[PatternSourceLink] = []
    for pattern in patterns:
        for case_id, trace_id in zip(
            pattern.source_case_ids, pattern.source_trace_ids, strict=False
        ):
            case_record = case_records.get(case_id)
            trace_record = trace_records.get(case_id)
            if case_record is None or trace_record is None:
                continue
            case = cases.get(case_id)
            trace = traces.get(trace_id)
            if case is None or trace is None:
                continue
            slug = Path(case_record.path).parent.name
            paper_view = paths.paper_case(slug)
            trace_view = paths.formation_trace_view(slug)
            _require_existing_link_target(paths, paper_view)
            _require_existing_link_target(paths, trace_view)
            links.append(
                PatternSourceLink(
                    paper_case_id=case_id,
                    formation_trace_id=trace_id,
                    paper_label=case.citation or "Source PaperCase",
                    paper_href=f"papers/{slug}.md",
                    trace_label="Question-formation trace",
                    trace_href=f"formation_traces/{slug}.md",
                )
            )
    return patterns, tuple(links)


def _load_question_sources(
    paths: RunPaths, source_paths: set[Path]
) -> tuple[
    QuestionFamilyBatch | None,
    QuestionFamilyShortlistManifest | None,
    QuestionScientistContextPayloadV2 | None,
]:
    batch_candidates = sorted(
        (paths.corpus / "question_families").glob("*.question_family_batch.yaml")
    )
    if len(batch_candidates) > 1:
        raise ValueError("multiple canonical Question Scientist batches are not presentation-safe")
    batch = (
        _load_source(paths, batch_candidates[0], QuestionFamilyBatch, source_paths)
        if batch_candidates
        else None
    )
    canonical_shortlist = (
        paths.corpus / "question_families" / "reviewed" / "question_family_shortlist_manifest.yaml"
    )
    shortlist = (
        _load_source(paths, canonical_shortlist, QuestionFamilyShortlistManifest, source_paths)
        if canonical_shortlist.is_file()
        else None
    )
    payload_candidates = sorted(
        (paths.corpus / "context" / "question_scientist").glob(
            "*.question_scientist_context_v2.yaml"
        )
    )
    if len(payload_candidates) > 1:
        raise ValueError("multiple typed question context payloads are not presentation-safe")
    context = (
        _load_source(paths, payload_candidates[0], QuestionScientistContextPayloadV2, source_paths)
        if payload_candidates
        else None
    )
    return batch, shortlist, context


def _load_family_sources(
    paths: RunPaths,
    *,
    original_family_by_id: dict[str, QuestionFamily],
    current_family_by_id: dict[str, QuestionFamily],
    source_paths: set[Path],
) -> tuple[FamilyPresentationSource, ...]:
    sources: list[FamilyPresentationSource] = []
    for completion_path in sorted(paths.root.glob("families/*/family_completion.yaml")):
        completion = _load_source(paths, completion_path, FamilyCompletionRecord, source_paths)
        if completion.run_id != paths.root.name:
            raise ValueError("family completion belongs to a different run")
        if completion.slug != completion_path.parent.name:
            raise ValueError("family completion slug differs from its run directory")
        original_family = original_family_by_id.get(completion.question_family_id)
        family = current_family_by_id.get(completion.question_family_id)
        if original_family is None:
            raise ValueError(
                "a completed family is absent from the original Question Scientist batch"
            )
        if family is None:
            raise ValueError("a completed family is absent from the typed Question Scientist batch")
        if not variant_ids_are_ordered_subset(
            [variant.variant_id for variant in original_family.variants],
            [variant.variant_id for variant in family.variants],
        ):
            raise ValueError(
                "post-novelty family variants are not an ordered subset of the original family"
            )
        artifact_dir = paths.family_artifacts(completion.slug)
        imported_dir = artifact_dir / "imported"
        plan_path = _single_optional(sorted(imported_dir.glob("*-plan_draft.yaml")))
        owner_path = artifact_dir / "owner_plan_review.yaml"
        independent_path = artifact_dir / "independent_plan_review.yaml"
        plan = (
            _load_source(paths, plan_path, PlanDraftMessage, source_paths)
            if plan_path is not None
            else None
        )
        owner = (
            _load_source(paths, owner_path, QuestionOwnerPlanReviewMessage, source_paths)
            if owner_path.is_file()
            else None
        )
        independent = (
            _load_source(paths, independent_path, IndependentPlanReviewMessage, source_paths)
            if independent_path.is_file()
            else None
        )
        evidence = _load_family_inspection_evidence(
            paths, artifact_dir=artifact_dir, imported_dir=imported_dir, source_paths=source_paths
        )
        _require_existing_link_target(paths, paths.family_dossier(completion.slug))
        sources.append(
            FamilyPresentationSource(
                completion=completion,
                original_family=original_family,
                family=family,
                plan_draft=plan,
                owner_review=owner,
                independent_review=independent,
                inspection_evidence=evidence,
            )
        )
    return tuple(sources)


def _load_family_inspection_evidence(
    paths: RunPaths,
    *,
    artifact_dir: Path,
    imported_dir: Path,
    source_paths: set[Path],
) -> tuple[QuestionFamilyInspectionEvidence, ...]:
    """Discover typed inspection evidence BY TYPE, and check the result against the import manifest.

    This used to be ``imported_dir.glob("*-evidence-*.yaml")``. Nothing ever prescribed that name:
    the handoff contract gives the planner a DIRECTORY, the literal ``-evidence-`` appears exactly
    once in all of ``src/``, and every other consumer keys on ``evidence_id``. The planner writes
    ``<digest>-ev-<slug>.yaml``, so the glob matched **none** of them for whole families.

    Measured across every family in every retained run: the import manifests declare **262**
    evidence records, discovery by type finds **262** with zero mismatches, and the glob found
    **207** -- 55 lost, 21%, with **nine families (12.9%) loading zero of their own evidence**.
    A family that loaded zero then printed "No safely resolved, typed inspection statement was
    available for this view" onto a delivered scientific reading guide while five to seven
    receipt-bound statements sat in its own directory: 16 of the 17 occurrences of that sentence
    corpus-wide were false.

    The receipt could not catch it, because ``expected_output_paths`` is derived from the same glob
    output -- so ``EXPECTED_PAGE_MISSING`` was structurally unable to fire and d3p5:nlb recorded
    ``status: produced, warning: '', warning_codes: []`` over six blank families.

    Hence the assertion, and not merely the wider discovery: the manifest is the independent record
    of what was imported, so a page can be required to account for all of it. **A page may not
    assert an absence it did not verify against a manifest.**
    """

    manifest_path = artifact_dir / "artifact_import_manifest.yaml"
    if not manifest_path.is_file():
        # No planner artifact import ran for this family; there is nothing to account against and
        # an empty inspection section is the honest rendering.
        return ()
    manifest = _load_source(paths, manifest_path, PlannerArtifactImportManifest, source_paths)
    discovered: dict[str, Path] = {}
    for path in sorted(imported_dir.glob("*.yaml")):
        if path == manifest_path:
            continue
        try:
            probe = load_model(path, QuestionFamilyInspectionEvidence)
        except ValidationError:
            # The directory also holds the plan draft, run record and validation report. Failing to
            # validate as inspection evidence is the ordinary case here, not an error -- and it is
            # the ONLY failure swallowed: an unreadable or malformed file still raises, because a
            # file this loader could not read is exactly the case the manifest check exists to
            # catch, and swallowing it would restore the silence being removed.
            continue
        discovered[probe.evidence_id] = path
    declared = list(dict.fromkeys(manifest.evidence_ids))
    missing = [evidence_id for evidence_id in declared if evidence_id not in discovered]
    undeclared = sorted(set(discovered) - set(declared))
    if missing or undeclared:
        raise ValueError(
            "family inspection evidence does not account for its import manifest "
            f"({manifest_path}): declared-but-absent={missing}, present-but-undeclared={undeclared}"
        )
    return tuple(
        _load_source(paths, discovered[evidence_id], QuestionFamilyInspectionEvidence, source_paths)
        for evidence_id in declared
    )


def _load_source(
    paths: RunPaths, path: Path, model: type[_ModelT], source_paths: set[Path]
) -> _ModelT:
    validate_exact_artifact(paths.root, path)
    value = load_model(path, model)
    source_paths.add(path)
    return value


def _require_existing_link_target(paths: RunPaths, path: Path) -> None:
    """Validate a navigation target without treating unread Markdown as a rendering input."""
    validate_exact_artifact(paths.root, path)


def _single_optional(paths: Sequence[Path]) -> Path | None:
    if len(paths) > 1:
        raise ValueError("multiple typed plan drafts are not presentation-safe")
    return paths[0] if paths else None


def _common_run_root(paths: Sequence[Path]) -> Path:
    # Every source has already passed exact run-root containment. The stable root is the ancestor
    # immediately above the first public top-level run directory component.
    first = paths[0]
    for ancestor in first.parents:
        if (ancestor / "run_manifest.yaml").is_file():
            return ancestor
    raise ValueError("presentation source paths are not inside a run envelope")


def _receipt_bound_digests(paths: RunPaths) -> dict[str, str]:
    """Run-relative path → digest for every output a six-stage receipt signed."""
    bound: dict[str, str] = {}
    for receipt in read_stage_receipts(paths):
        for relative_path, digest in receipt.output_digests.items():
            prior = bound.get(relative_path)
            if prior is not None and prior != digest:
                raise ValueError("scientific stage receipts disagree about one source digest")
            bound[relative_path] = digest
    return bound


def _load_novelty_admissions(
    paths: RunPaths, source_paths: set[Path]
) -> tuple[FamilyNoveltyAdmission, ...]:
    """The receipt-bound prior-art records that explain a filtered variant's disposition.

    Only records a six-stage receipt actually signed are consumed. An unsigned file is skipped
    rather than loaded, which keeps the add-on's "never consume an unbound scientific source"
    contract intact AND stops a run whose Stage D predates this binding from losing every detailed
    page to a strict-construction failure. A skipped record simply leaves its variant with the
    honest no-record sentence.
    """
    bound = _receipt_bound_digests(paths)
    admissions: list[FamilyNoveltyAdmission] = []
    root = paths.corpus / "question_families" / "novelty"
    for candidate in sorted(root.glob("*/*.family_novelty_admission.yaml")):
        relative = candidate.relative_to(paths.root).as_posix()
        if relative not in bound:
            continue
        admissions.append(_load_source(paths, candidate, FamilyNoveltyAdmission, source_paths))
    return tuple(admissions)


def _load_novelty_assessments(
    paths: RunPaths, source_paths: set[Path]
) -> tuple[VariantNoveltyAssessment, ...]:
    """The reviewer's OWN words for each variant, and the priors it actually compared against.

    A scientific "no" has to carry its evidence -- that is shape (2) of the shepherd contract. The
    disposition alone told a reader their question "duplicates prior work" and stopped there, while
    the rationale and the DOI-identified comparisons sat in the assessment file next door, paid for
    and unread. Loaded under the same receipt binding as the admissions: an unsigned record is
    skipped rather than consumed, so an older run simply keeps the bare disposition.
    """
    bound = _receipt_bound_digests(paths)
    assessments: list[VariantNoveltyAssessment] = []
    root = paths.corpus / "question_families" / "novelty"
    for candidate in sorted(root.glob("*/assessments/novelty-assessment-*.yaml")):
        relative = candidate.relative_to(paths.root).as_posix()
        if relative not in bound:
            continue
        assessments.append(_load_source(paths, candidate, VariantNoveltyAssessment, source_paths))
    return tuple(assessments)


def _validate_scientific_source_bindings(paths: RunPaths, source_paths: set[Path]) -> None:
    """Every consumed typed/source file must already be signed by a six-stage receipt."""
    bound = _receipt_bound_digests(paths)
    for source_path in source_paths:
        relative = source_path.relative_to(paths.root).as_posix()
        expected = bound.get(relative)
        if expected is None:
            raise ValueError("presentation attempted to consume an unbound scientific source")
        if sha256_file(source_path) != expected:
            raise ValueError("scientific source digest differs from its stage receipt")


def _promote_presentation_text(
    *,
    root: Path,
    destination: Path,
    text: str,
    private_tokens: Sequence[str],
    allowed_public_dois: Sequence[str],
    validator: Callable[[str], None] | None,
) -> None:
    root = root.absolute()
    destination = destination.absolute()
    if not destination.is_relative_to(root):
        raise ValueError("presentation destination escapes the run root")
    _assert_safe_presentation_destination(root, destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = (text if text.endswith("\n") else text + "\n").encode("utf-8")
    fd, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".candidate",
    )
    candidate = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        candidate_stat = candidate.lstat()
        if not stat.S_ISREG(candidate_stat.st_mode):
            raise ValueError("presentation candidate is not a regular file")
        candidate_text = candidate.read_text(encoding="utf-8")
        validate_detailed_markdown(
            candidate_text,
            private_tokens=private_tokens,
            allowed_public_dois=allowed_public_dois,
        )
        if validator is not None:
            validator(candidate_text)
        os.replace(candidate, destination)
    finally:
        candidate.unlink(missing_ok=True)


def _write_presentation_receipt(paths: RunPaths, receipt: PresentationAddonReceipt) -> None:
    """Publish the soft receipt only after applying the add-on's run-root/symlink boundary."""
    root = paths.root.absolute()
    destination = paths.presentation_receipt.absolute()
    _assert_safe_presentation_destination(root, destination)
    atomic_write_model(destination, receipt)


def _assert_safe_presentation_destination(root: Path, destination: Path) -> None:
    if not destination.is_relative_to(root):
        raise ValueError("presentation destination escapes the run root")
    current = root
    if current.is_symlink():
        raise ValueError("presentation run root cannot be a symlink")
    for part in destination.relative_to(root).parts:
        current = current / part
        # ``is_symlink`` also catches a dangling symlink; ``exists()`` would not.
        if current.is_symlink():
            raise ValueError("presentation destination contains a symlink")


#: Field names whose values are PUBLIC vocabulary, not identifiers this run minted.
#:
#: The `_id` suffix is a proxy for "this is private", and on 2026-07-28 the fault-injection harness
#: showed the proxy firing on public facts: 19 of a live run's 304 "private" tokens were ordinary
#: prose, among them `anthropic`, `openai`, `crossref`, `openalex` (vendor names, published in every
#: dossier's provenance) and `open_gaps`, `background_core_constructs` (topic-literature lane
#: categories, a fixed vocabulary). Each of these fields carries a closed vocabulary that exists
#: before any run and is identical across runs -- the opposite of a run-scoped identifier.
#:
#: This matters because the redaction pass and the validation pass must share one set: widening
#: redaction to cover a set containing "anthropic" would replace the word wherever a reviewer wrote
#: it, mangling the prose the page exists to carry.
_PUBLIC_VOCABULARY_FIELDS = frozenset({"lane_id", "lane_ids", "provider_id", "source_id"})


def _presentation_private_tokens(*values: object) -> tuple[str, ...]:
    """Collect exact typed identifiers; ordinary scientific compounds are never guessed as IDs."""
    tokens: set[str] = set()

    def collect(value: object, *, identifier_field: bool = False) -> None:
        if isinstance(value, BaseModel):
            collect(value.model_dump(mode="python"))
            return
        if is_dataclass(value) and not isinstance(value, type):
            for field in fields(value):
                collect(getattr(value, field.name))
            return
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key)
                collect(
                    item,
                    identifier_field=(
                        key_text not in _PUBLIC_VOCABULARY_FIELDS
                        and (
                            key_text == "id"
                            or key_text.endswith("_id")
                            or key_text.endswith("_ids")
                        )
                    ),
                )
            return
        if isinstance(value, (list, tuple, set, frozenset)):
            for item in value:
                collect(item, identifier_field=identifier_field)
            return
        if identifier_field and isinstance(value, str) and len(value.strip()) >= 6:
            tokens.add(value.strip())

    for value in values:
        collect(value)
    return tuple(sorted(tokens))
