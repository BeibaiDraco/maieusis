"""COARSE durable resume for `maieusis run`.

`maieusis resume <run-id>` re-enters an existing ``runs/<id>/`` tree and finishes it: stages whose
StageReceipts prove completed-with-identical-inputs are REUSED (zero re-pay, zero re-spawn);
everything else re-runs. The design is deliberately coarse:

- **Stage-level** completion-skip on the front half (paper/dataset halves, stage C, stage D, the
  front layout), with per-stage input-digest + config/model-slice invalidation over an explicit
  static DAG. A stage without a COMPLETE receipt simply re-runs — no journal, no exactly-once.
- **Family-level** skip on the back half: a family whose driver-persisted
  ``FamilyCompletionRecord`` verifies (scientific-terminal status + intact artifacts + current
  shortlist binding) is fed to the orchestrator's ``completed_records`` seam; an incomplete family
  has its branch dir + layout dir deleted so the orchestrator recreates it FRESH. The orchestrator
  and branch manager are UNTOUCHED — re-entrancy is entirely driver-side.

Corruption fails closed: an artifact that exists behind a COMPLETE receipt/record but is missing or
digest-mismatched raises ``RunArtifactCorruptionError`` naming the artifact — never silent reuse,
never silent re-run. The reuse predicate recomputes every input digest from the real inputs with
the SAME functions the receipt writer used, so a hand-edited receipt can never skip payment.

The planner (``plan_resume``) is PURE: it reads receipts + artifacts and decides, constructing zero
providers and making zero paid calls. The decision set is persisted as a ``ResumeReceipt``
(``receipts/resume-<n>.yaml``) BEFORE any execution.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Iterator, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from yaml import YAMLError

from ...io import dump_data, load_model
from ...provenance import sha256_file, stable_hash
from ...schemas.front_half_authority import FrontHalfAuthorityCeiling
from ...schemas.gate_outcome import PromotionReceipt
from ...schemas.inferred_research_scope import ResolvedResearchScope
from ...schemas.maieusis_project_config import MaieusisProjectConfig
from ...schemas.multi_family_dossier import FamilyDossierStatus
from ...schemas.question_family import QuestionFamilyBatch, QuestionFamilyShortlistManifest
from ...schemas.question_pattern import QuestionFormationTrace, QuestionPatternCard
from ...schemas.question_scientist_context_v2 import QuestionScientistContextPayloadV2
from ...schemas.resume import (
    FamilyCompletionRecord,
    FamilyResumeDecision,
    FamilyResumeReason,
    PresentationResumeDecision,
    PresentationResumeDecisionKind,
    PresentationResumeReason,
    ResumeReceipt,
    StageResumeDecision,
    StageResumeDecisionKind,
    StageRunReason,
)
from ...schemas.run_outcome import DossierAxis, FamilyRunOutcome
from ...schemas.stage_d import StageDCandidateDisposition, StageDOutcomeRecord
from ...schemas.stage_receipt import FailureClass, StageReceipt, StageStatus
from ..agents.citation_importance_reviewer import CITATION_IMPORTANCE_REVIEWER_PROMPT_VERSION
from ..agents.formation_trace_reviewer import FORMATION_TRACE_REVIEWER_PROMPT_VERSION
from ..agents.paper_case_reviewer import PAPER_CASE_FIDELITY_REVIEWER_PROMPT_VERSION
from ..agents.pattern_reviewer import QUESTION_PATTERN_REVIEWER_PROMPT_VERSION
from ..paper_ingest.extraction import SOURCE_SPAN_PROMPT_VERSION
from ..paper_ingest.paperbank_gate import AcceptedPaperCase, PaperBankGateResult, PaperCaseDraft
from ..paper_patterns.citation_importance import (
    CITATION_IMPORTANCE_SELECTOR_PRODUCT_PROMPT_VERSION,
)
from ..paper_patterns.induction import QUESTION_PATTERN_INDUCER_PROMPT_VERSION
from ..paper_patterns.pattern_revision import (
    QUESTION_PATTERN_REVISER_PROMPT_VERSION,
    PatternRevisionHistory,
)
from ..paper_patterns.trace_drafting import QUESTION_FORMATION_TRACE_DRAFTER_PROMPT_VERSION
from .run_layout import RunPaths, assign_family_slugs, family_slug, read_stage_receipt

if TYPE_CHECKING:
    from ...schemas.topic_literature import TopicSourceTable
    from ..context.topic_evidence import R5TopicEvidenceSourceTable


# --- stage names + the explicit coarse DAG -------------
STAGE_PAPER_HALF = "paper_half"
STAGE_DATASET_HALF = "dataset_half"
STAGE_C = "stage_c"
STAGE_D = "stage_d"
STAGE_FRONT_LAYOUT = "front_layout"
STAGE_BACK_HALF = "back_half"

# Receipt config slices must change when a stage's deterministic semantics change, even if operator
# config and model routing do not. Otherwise an honest SCIENTIFIC_TERMINAL from old code is reusable
# forever and a launch-blocker fix cannot take effect on resume. Bump this explicit revision for every
# paper-half semantic change that can alter stage products or terminal disposition.
PAPER_HALF_IMPLEMENTATION_VERSION = "paper_half/v6"
STAGE_C_IMPLEMENTATION_VERSION = "stage_c/v1"
BACK_HALF_IMPLEMENTATION_VERSION = "back_half/v2"

STAGE_ORDER: tuple[str, ...] = (
    STAGE_PAPER_HALF,
    STAGE_DATASET_HALF,
    STAGE_C,
    STAGE_D,
    STAGE_FRONT_LAYOUT,
    STAGE_BACK_HALF,
)

#: Dataset scope consumes reviewed paper patterns; dataset half therefore follows paper half.
STAGE_UPSTREAM: dict[str, tuple[str, ...]] = {
    STAGE_PAPER_HALF: (),
    STAGE_DATASET_HALF: (STAGE_PAPER_HALF,),
    STAGE_C: (STAGE_PAPER_HALF, STAGE_DATASET_HALF),
    STAGE_D: (STAGE_C,),
    STAGE_FRONT_LAYOUT: (STAGE_D,),
    STAGE_BACK_HALF: (STAGE_D,),
}

#: Run-root-relative areas each stage EXCLUSIVELY owns: deleted before that stage re-runs so a
#: crash mid-stage (files written, receipt never written) can never mix with fresh outputs. The back
#: half is cleaned per family, not from this table.
STAGE_CLEAN_AREAS: dict[str, tuple[str, ...]] = {
    STAGE_PAPER_HALF: (
        # The run-envelope projections are written before their two-file trace pairs can be
        # re-indexed. Detach and remove the prior stage's copies first so a crash-safe rerun never
        # compares one freshly replaced member against the other member's old manifest digest.
        "artifacts/papers",
        "artifacts/patterns",
        "paperbank",
        "corpus/patterns",
        # The pattern-bank manifest sits at the corpus root (NOT under patterns/); a re-run that ends
        # all-unusable would otherwise leave a PREVIOUS run's manifest for stage C to read.
        "corpus/question_pattern_manifest.yaml",
        "stage_outputs/paper-half.yaml",
    ),
    STAGE_DATASET_HALF: (
        "corpus/context/dataset_narratives",
        "corpus/context/topic_evidence",
        "stage_outputs/dataset-half.yaml",
        "receipts/fulltext-enrichment.yaml",
    ),
    STAGE_C: ("corpus/research_intent.yaml", "corpus/context/question_scientist"),
    STAGE_D: ("corpus/question_families", "stage_outputs/stage-d.yaml"),
    # These are indexed stable projections. Their writers use adjacent replacement + os.replace, so
    # a failed rerender must leave the last valid current bytes visible.
    STAGE_FRONT_LAYOUT: (),
}

#: Receipt statuses the reuse predicate accepts: a completed stage OR an honest scientific end.
_REUSABLE_STATUSES = frozenset({StageStatus.COMPLETE, StageStatus.SCIENTIFIC_TERMINAL})

#: Explicit safe family terminals. Recoverable validation/provider warnings are reusable only when
#: their new-style completion records carry ``warning_class`` + ``terminal_rendered``; legacy records
#: remain RUN decisions so release-fix resumes can replace them.
SCIENTIFIC_TERMINAL_FAMILY_STATUSES: frozenset[FamilyDossierStatus] = frozenset(
    {
        FamilyDossierStatus.COMPLETED_DOSSIER_STACK,
        FamilyDossierStatus.PUBLIC_DOSSIER_REVISION_REQUIRED,
        FamilyDossierStatus.REJECTED,
        FamilyDossierStatus.HUMAN_ESCALATION,
        FamilyDossierStatus.REVISION_BUDGET_EXHAUSTED,
        FamilyDossierStatus.MATERIAL_REVISION_DEFERRED,
        FamilyDossierStatus.REVIEW_ESCALATED,
        FamilyDossierStatus.DEVELOPMENT_SURROGATE_PLAN,
        FamilyDossierStatus.DEVELOPMENT_SURROGATE_REJECT,
        FamilyDossierStatus.DEVELOPMENT_SURROGATE_ESCALATION,
        FamilyDossierStatus.AUTOMATED_PLAN,
        FamilyDossierStatus.AUTOMATED_REJECT,
        FamilyDossierStatus.AUTOMATED_ESCALATION,
        FamilyDossierStatus.FAILED_VALIDATION,
        FamilyDossierStatus.INFRASTRUCTURE_INCOMPLETE,
    }
)


class RunArtifactCorruptionError(RuntimeError):
    """An artifact behind a COMPLETE receipt/record is missing or digest-mismatched (fail closed)."""


class RunLockedError(RuntimeError):
    """Another live process holds the run lock."""


class StaleRunLockError(RuntimeError):
    """The run lock exists but its holder is dead — the user must clear it explicitly."""


class ScientificResumePreflightRequired(RuntimeError):
    """The locked re-plan found scientific work; CLI must preflight before retrying."""


# --- typed per-stage output summaries (rehydrated by the resume/layout/back-half paths) ------------
class PaperHalfStageOutput(BaseModel):
    """Everything the layout + back half need from the paper half, persisted at stage end."""

    model_config = ConfigDict(extra="forbid")

    gate_result: PaperBankGateResult
    accepted: list[AcceptedPaperCase] = Field(default_factory=list)
    traces: list[QuestionFormationTrace] = Field(default_factory=list)
    patterns: list[QuestionPatternCard] = Field(default_factory=list)
    pattern_revision_history: list[PatternRevisionHistory] = Field(default_factory=list)
    receipts: list[PromotionReceipt] = Field(default_factory=list)


class DatasetHalfStageOutput(BaseModel):
    """Everything the layout + back half need from the dataset half, persisted at stage end.

    The reviewed narrative + topic brief themselves live at their corpus paths (single source of
    truth); this file carries only the small non-corpus values.
    """

    model_config = ConfigDict(extra="forbid")

    receipts: list[PromotionReceipt] = Field(default_factory=list)
    lane_coverage: dict[str, int] = Field(default_factory=dict)
    source_count: int = 0
    scope: ResolvedResearchScope
    fulltext_counts: dict[str, int] = Field(default_factory=dict)
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED
    source_activity_path: str = ""


# --- shared digest computation (single source of truth for receipt WRITE and resume READ) ----------
def compute_paper_half_input_digests(
    config: MaieusisProjectConfig, drafts: Sequence[PaperCaseDraft] | None
) -> dict[str, str]:
    """Paper-half inputs: injected drafts when given, else the inbox PDFs (no paid ingestion needed).

    The PDF form is what `maieusis run`/`maieusis resume` record/recompute — resume can decide REUSE without
    re-paying extraction. Tests that inject drafts get stable per-draft digests instead.
    """
    if drafts is not None:
        return {f"draft:{draft.paper_id}": stable_hash(draft) for draft in drafts}
    inbox = Path(config.paperbank.inbox_dir)
    if not inbox.is_dir():
        return {}
    return {
        f"pdf:{pdf.name}": sha256_file(pdf) for pdf in sorted(inbox.glob("*.pdf")) if pdf.is_file()
    }


def compute_dataset_half_input_digests(config: MaieusisProjectConfig) -> dict[str, str]:
    """Dataset-half RAW inputs: the seed docs files.

    The topic source table is a DERIVED, refreshed-each-run input (the CLI retrieves it live over the
    network; timestamps make it non-reproducible), so it is deliberately NOT pinned — dataset-half
    re-runs are governed by its config slice (seed id/link, literature, research intent, mode) plus
    these docs digests. That mirrors production exactly: a CLI-retrieved table never pins a resume.
    """
    return {
        f"doc:{index}:{doc}": (sha256_file(doc) if doc.is_file() else "missing")
        for index, doc in enumerate(sorted(Path(p) for p in config.dataset.seed.docs))
    }


def upstream_output_digest(paths: RunPaths, upstream_stage: str) -> str:
    """The single 'upstream:<stage>' input value: a hash over the upstream receipt's output digests.

    Byte-identical upstream re-runs therefore still allow downstream REUSE (maximally honest AND
    cache-friendly). Missing upstream receipt → "missing" (never equal to a recorded hash).
    """
    receipt = read_stage_receipt(paths, upstream_stage)
    if receipt is None:
        return "missing"
    return stable_hash(dict(sorted(receipt.output_digests.items())))


def upstream_input_digests(paths: RunPaths, stage: str) -> dict[str, str]:
    return {
        f"upstream:{upstream}": upstream_output_digest(paths, upstream)
        for upstream in STAGE_UPSTREAM[stage]
    }


def _effective(config: MaieusisProjectConfig, configured: object) -> str:
    pm = config.effective_provider(configured)  # type: ignore[arg-type]
    return f"{pm.provider}:{pm.model or 'default'}"


def stage_model_versions(config: MaieusisProjectConfig, stage: str) -> dict[str, str]:
    """The EFFECTIVE provider:model per role a stage actually uses (R-A; demo↔standard flips show).

    Each front-half stage signs the exact configured roles that own its model calls. The back half
    uses owner + reviewer + the coding host.
    Stage C and the layout construct no providers.
    """
    models = config.models
    if stage == STAGE_PAPER_HALF:
        return {
            "extraction": _effective(config, config.paperbank.extraction),
            "pattern": _effective(config, models.effective_pattern),
            "reviewer": _effective(config, models.reviewer),
        }
    if stage == STAGE_DATASET_HALF:
        return {
            "narrator": _effective(config, models.narrator),
            "topic": _effective(config, models.topic),
            "reviewer": _effective(config, models.reviewer),
        }
    if stage == STAGE_D:
        return {
            "questioner": _effective(config, models.questioner),
            "reviewer": _effective(config, models.reviewer),
        }
    if stage == STAGE_BACK_HALF:
        versions = {
            "owner": _effective(config, models.owner),
            "reviewer": _effective(config, models.reviewer),
            "coding_host": models.coding_host.value,
            "coding_model": models.coding_model,
        }
        if models.coding_reasoning_effort is not None:
            versions["coding_reasoning_effort"] = models.coding_reasoning_effort.value
        return versions
    return {}


def stage_prompt_versions(stage: str) -> dict[str, str]:
    """Active prompt families whose bytes semantically own one coarse stage.

    The paper half is the only cross-run importable stage. Keeping every generator and independent
    reviewer prompt explicit in its receipt makes a prompt upgrade invalidate both resume and import
    before any provider is constructed.
    """
    if stage == STAGE_PAPER_HALF:
        return {
            "paper_case_extraction": SOURCE_SPAN_PROMPT_VERSION,
            "citation_importance_selection": (CITATION_IMPORTANCE_SELECTOR_PRODUCT_PROMPT_VERSION),
            "question_formation_trace": QUESTION_FORMATION_TRACE_DRAFTER_PROMPT_VERSION,
            "question_pattern_induction": QUESTION_PATTERN_INDUCER_PROMPT_VERSION,
            "question_pattern_revision": QUESTION_PATTERN_REVISER_PROMPT_VERSION,
            "paper_case_fidelity_review": PAPER_CASE_FIDELITY_REVIEWER_PROMPT_VERSION,
            "citation_importance_review": CITATION_IMPORTANCE_REVIEWER_PROMPT_VERSION,
            "formation_trace_review": FORMATION_TRACE_REVIEWER_PROMPT_VERSION,
            "question_pattern_review": QUESTION_PATTERN_REVIEWER_PROMPT_VERSION,
        }
    return {}


def stage_config_version(
    config: MaieusisProjectConfig,
    stage: str,
    *,
    family_count: int = 6,
    variants_per_family: int | None = None,
) -> str:
    """A stable hash of the stage's RELEVANT config slice.

    Neutral knobs (output_root, parallelism, timeouts) are deliberately excluded from every slice —
    changing them never invalidates a stage. A differing slice re-runs the stage (+ downstream).
    """
    mode = config.mode.value
    variants_per_family = (
        config.run.variants_per_family if variants_per_family is None else variants_per_family
    )
    slices: dict[str, object]
    if stage == STAGE_PAPER_HALF:
        paperbank = config.paperbank.model_dump(mode="json")
        # Filesystem locations are operational, not scientific identity. PDF filename+byte digests
        # are signed separately in ``input_digests``. The import source and its receipt SHA are
        # provenance for the reuse event, not part of the paper-half scientific configuration.
        paperbank.pop("inbox_dir", None)
        paperbank.pop("import_from_run", None)
        paperbank.pop("max_workers", None)  # parallelism is neutral
        slices = {
            "implementation_version": PAPER_HALF_IMPLEMENTATION_VERSION,
            "mode": mode,
            "paperbank": paperbank,
            "max_revise_rounds": config.run.max_revise_rounds,
        }
    elif stage == STAGE_DATASET_HALF:
        slices = {
            "mode": mode,
            "dataset_id": config.dataset.seed.dataset_id,
            "link": config.dataset.seed.link,
            "docs": [str(path) for path in config.dataset.seed.docs],
            "literature": config.literature.model_dump(mode="json"),
            "research_intent": config.research_intent.model_dump(mode="json"),
        }
    elif stage == STAGE_C:
        slices = {
            "implementation_version": STAGE_C_IMPLEMENTATION_VERSION,
            "research_intent": config.research_intent.model_dump(mode="json"),
            "dataset_id": config.dataset.seed.dataset_id,
        }
    elif stage == STAGE_D:
        slices = {
            "mode": mode,
            "novelty": config.novelty.model_dump(mode="json"),
            "family_count": family_count,
            "variants_per_family": variants_per_family,
        }
    elif stage == STAGE_FRONT_LAYOUT:
        # Everything resolved_inputs.md renders (mode/dataset/providers) — a pure-render slice.
        slices = {
            "mode": mode,
            "dataset_id": config.dataset.seed.dataset_id,
            "link_set": bool(config.dataset.seed.link),
            "owner_provider": config.models.owner.provider,
            "reviewer_provider": config.models.reviewer.provider,
            "coding_host": config.models.coding_host.value,
        }
    elif stage == STAGE_BACK_HALF:
        slices = {
            "implementation_version": BACK_HALF_IMPLEMENTATION_VERSION,
            "mode": mode,
            "max_revise_rounds": config.run.max_revise_rounds,
            "inspection_runtime": {
                key: value
                for key, value in config.dataset.inspection_runtime.model_dump(mode="json").items()
                if key not in {"max_turns", "timeout_seconds"}  # neutral limits
            },
            "allowed_inspection_resources": list(config.dataset.allowed_inspection_resources),
            "official_online_resources": list(config.dataset.official_online_resources),
        }
    else:
        raise ValueError(f"unknown stage {stage!r}")
    slices["allow_pro_model"] = config.models.allow_pro_model
    return stable_hash(slices)


# --- run-root-relative artifact digests -------------------------------------------------------------
def relative_output_digests(run_root: Path, paths: Sequence[Path]) -> dict[str, str]:
    """sha256 per output file, keyed by run-root-relative POSIX path (sorted, deterministic)."""
    digests: dict[str, str] = {}
    for path in paths:
        for file in sorted(path.rglob("*") if path.is_dir() else [path]):
            if file.is_file():
                digests[file.relative_to(run_root).as_posix()] = sha256_file(file)
    return dict(sorted(digests.items()))


def _verify_output_digests(
    run_root: Path, recorded: dict[str, str], *, owner_label: str
) -> list[str]:
    """DP-2 point 4: every recorded output must EXIST with a matching digest, else corruption."""
    verified: list[str] = []
    for rel, expected in recorded.items():
        file = run_root / rel
        if not file.is_file():
            raise RunArtifactCorruptionError(
                f"corruption in run {run_root.name!r}: {owner_label} recorded output {rel!r} "
                "is missing — refusing silent reuse or silent re-run; start a fresh run"
            )
        actual = sha256_file(file)
        if actual != expected:
            raise RunArtifactCorruptionError(
                f"corruption in run {run_root.name!r}: {owner_label} output {rel!r} digest "
                f"mismatch (expected sha256 {expected}, found {actual}) — refusing silent reuse "
                "or silent re-run; start a fresh run"
            )
        verified.append(rel)
    return verified


def _verify_stage_d_outcome_binding(paths: RunPaths) -> list[str]:
    """Verify retained bytes, type, context, and family lineage at the real reuse boundary."""
    outcome = load_model(paths.stage_output(STAGE_D), StageDOutcomeRecord)
    if not outcome.retained_batch_path:
        return []
    retained_path = paths.root / outcome.retained_batch_path
    try:
        root = paths.root.resolve(strict=True)
        resolved = retained_path.resolve(strict=True)
    except OSError as exc:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: Stage-D retained batch violates "
            "run-root confinement"
        ) from exc
    expected = root.joinpath(*Path(outcome.retained_batch_path).parts)
    if resolved != expected or not resolved.is_relative_to(root):
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: Stage-D retained batch violates "
            "run-root confinement (external or symlink alias)"
        )
    verified = _verify_output_digests(
        paths.root,
        {outcome.retained_batch_path: outcome.retained_batch_digest},
        owner_label="Stage-D retained batch",
    )
    try:
        batch = load_model(retained_path, QuestionFamilyBatch)
    except (OSError, ValueError, YAMLError) as exc:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: Stage-D retained batch is not a valid "
            "QuestionFamilyBatch"
        ) from exc
    try:
        payload = load_model(find_payload_path(paths), QuestionScientistContextPayloadV2)
    except (OSError, ValueError, YAMLError) as exc:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: persisted Stage-C context binding "
            "cannot be loaded for Stage-D reuse"
        ) from exc
    identities = {
        (batch.context_id, batch.context_digest),
        (outcome.context_id, outcome.context_digest),
        (payload.context_id, payload.context_digest),
    }
    if len(identities) != 1:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: persisted Stage-C context binding does not "
            "exactly match the Stage-D outcome and retained batch"
        )
    retained_ids = {
        candidate.question_family_id
        for candidate in outcome.processed_candidates
        if candidate.disposition == StageDCandidateDisposition.RETAINED
    }
    batch_ids = {family.question_family_id for family in batch.families}
    if batch_ids != retained_ids:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: Stage-D retained batch family lineage "
            "does not exactly match the outcome"
        )
    return verified


# --- run lock --------------------------------------------------------------------------------
def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def acquire_run_lock(run_root: Path, *, command: str) -> Iterator[None]:
    """OS-level exclusive lock on ``runs/<id>/`` held for the whole run/resume lifecycle.

    ``O_CREAT|O_EXCL`` + a pid record: a second concurrent process fails immediately; a lock whose
    holder is dead raises ``StaleRunLockError`` explaining how to clear it (no silent auto-break).
    """
    run_root.mkdir(parents=True, exist_ok=True)
    lock_path = run_root / ".maieusis-lock"
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        info: dict[str, object] = {}
        with suppress(OSError, ValueError):
            info = json.loads(lock_path.read_text(encoding="utf-8"))
        pid = int(str(info.get("pid", 0) or 0))
        started = str(info.get("started_at", "unknown"))
        holder = str(info.get("command", "unknown"))
        if pid and _pid_alive(pid):
            raise RunLockedError(
                f"run {run_root.name!r} is locked by running process {pid} "
                f"({holder!r}, started {started}) — wait for it to finish or stop it first"
            ) from None
        raise StaleRunLockError(
            f"run {run_root.name!r} has a stale lock from dead process {pid or 'unknown'} "
            f"({holder!r}, started {started}) — remove {lock_path} and re-run "
            f"'maieusis resume {run_root.name}'"
        ) from None
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "pid": os.getpid(),
                    "started_at": datetime.now(UTC).isoformat(),
                    "command": command,
                },
                handle,
            )
        yield
    finally:
        lock_path.unlink(missing_ok=True)


# --- family completion discovery -------------------------------------------------------------
def family_slug_map(manifest: QuestionFamilyShortlistManifest) -> dict[str, str]:
    """The DETERMINISTIC family-id → layout-slug map (sorted ids; identical at write and resume)."""
    all_ids = sorted(
        {sf.family.question_family_id for sf in manifest.shortlisted}
        | set(manifest.rejected_family_ids)
        | set(manifest.needs_revision_family_ids)
        | set(manifest.deferred_family_ids)
    )
    return assign_family_slugs(all_ids)


def discover_family_completions(
    paths: RunPaths, manifest: QuestionFamilyShortlistManifest
) -> tuple[list[FamilyCompletionRecord], list[FamilyResumeDecision]]:
    """Disk-discover each shortlisted family's completion state.

    Complete ⟺ the ``family_completion.yaml`` record parses, its status is an EXPLICIT scientific
    terminal (R-C), it binds to the CURRENT shortlist digest, and every listed artifact exists with
    a matching digest (mismatch/missing artifact behind a record → corruption, fail closed).
    A missing record or a non-terminal status → RUN (clean + recreate).
    """
    shortlist_digest = stable_hash(manifest)
    slugs = family_slug_map(manifest)
    completed: list[FamilyCompletionRecord] = []
    decisions: list[FamilyResumeDecision] = []
    for shortlisted in manifest.shortlisted:
        family_id = shortlisted.family.question_family_id
        slug = slugs[family_id]
        record_path = paths.family_completion(slug)
        if not record_path.is_file():
            decisions.append(
                FamilyResumeDecision(
                    question_family_id=family_id,
                    slug=slug,
                    decision=StageResumeDecisionKind.RUN,
                    reason=FamilyResumeReason.RECORD_MISSING,
                )
            )
            continue
        record = load_model(record_path, FamilyCompletionRecord)
        if record.shortlist_digest != shortlist_digest:
            decisions.append(
                FamilyResumeDecision(
                    question_family_id=family_id,
                    slug=slug,
                    decision=StageResumeDecisionKind.RUN,
                    reason=FamilyResumeReason.SHORTLIST_CHANGED,
                    status_on_disk=record.dossier_record.status.value,
                )
            )
            continue
        if record.dossier_record.status not in SCIENTIFIC_TERMINAL_FAMILY_STATUSES:
            decisions.append(
                FamilyResumeDecision(
                    question_family_id=family_id,
                    slug=slug,
                    decision=StageResumeDecisionKind.RUN,
                    reason=FamilyResumeReason.NON_TERMINAL_STATUS,
                    status_on_disk=record.dossier_record.status.value,
                )
            )
            continue
        if record.dossier_record.status in {
            FamilyDossierStatus.FAILED_VALIDATION,
            FamilyDossierStatus.INFRASTRUCTURE_INCOMPLETE,
        } and (
            record.family_run_outcome.warning_class is None
            or record.family_run_outcome.dossier_axis != DossierAxis.TERMINAL_RENDERED
        ):
            decisions.append(
                FamilyResumeDecision(
                    question_family_id=family_id,
                    slug=slug,
                    decision=StageResumeDecisionKind.RUN,
                    reason=FamilyResumeReason.NON_TERMINAL_STATUS,
                    status_on_disk=record.dossier_record.status.value,
                )
            )
            continue
        _verify_output_digests(
            paths.root, record.artifact_digests, owner_label=f"family {family_id!r} completion"
        )
        completed.append(record)
        decisions.append(
            FamilyResumeDecision(
                question_family_id=family_id,
                slug=slug,
                decision=StageResumeDecisionKind.REUSE,
                reason=FamilyResumeReason.TERMINAL_COMPLETE,
                status_on_disk=record.dossier_record.status.value,
            )
        )
    return completed, decisions


def inspect_persisted_family_processing(
    paths: RunPaths,
    manifest: QuestionFamilyShortlistManifest,
) -> tuple[list[FamilyRunOutcome], bool]:
    """Read every current family completion for run-state finalization.

    Recoverable warning completions are operational terminals and may be reused. Hard integrity,
    missing, corrupt, or non-terminal records remain incomplete. This helper keeps the finalizer
    consistent with the discovery predicate without relabeling warnings as accepted plans.
    """

    shortlist_digest = stable_hash(manifest)
    slugs = family_slug_map(manifest)
    outcomes: list[FamilyRunOutcome] = []
    infrastructure_incomplete = False
    for shortlisted in manifest.shortlisted:
        family_id = shortlisted.family.question_family_id
        record_path = paths.family_completion(slugs[family_id])
        if not record_path.is_file():
            infrastructure_incomplete = True
            continue
        try:
            record = load_model(record_path, FamilyCompletionRecord)
        except (OSError, ValueError, ValidationError, YAMLError):
            infrastructure_incomplete = True
            continue
        if record.shortlist_digest != shortlist_digest:
            infrastructure_incomplete = True
            continue
        outcome = record.family_run_outcome
        outcomes.append(outcome)
        if record.dossier_record.status not in SCIENTIFIC_TERMINAL_FAMILY_STATUSES:
            infrastructure_incomplete = True
        if outcome.failure_class is not None and outcome.failure_class != FailureClass.SCIENTIFIC:
            infrastructure_incomplete = True
    return outcomes, infrastructure_incomplete


# --- the pure resume planner --------------------------------------------------------
@dataclass
class ResumePlan:
    run_id: str
    stage_decisions: dict[str, StageResumeDecision]
    family_decisions: list[FamilyResumeDecision] = field(default_factory=list)
    completed_families: list[FamilyCompletionRecord] = field(default_factory=list)
    presentation_decision: PresentationResumeDecision = field(
        default_factory=lambda: PresentationResumeDecision(
            decision=PresentationResumeDecisionKind.RENDER,
            reason=PresentationResumeReason.NOT_RECORDED,
        )
    )

    @property
    def reused_stage_count(self) -> int:
        return sum(
            1 for d in self.stage_decisions.values() if d.decision == StageResumeDecisionKind.REUSE
        )

    @property
    def rerun_stage_count(self) -> int:
        return len(self.stage_decisions) - self.reused_stage_count

    @property
    def all_stages_reused(self) -> bool:
        return self.rerun_stage_count == 0

    @property
    def presentation_only(self) -> bool:
        return (
            self.all_stages_reused
            and self.presentation_decision.decision == PresentationResumeDecisionKind.RENDER
        )


@dataclass(frozen=True)
class ResumeExecutionResult:
    summary: Path
    plan: ResumePlan
    presentation_attempted: bool = False


def _run_decision(
    stage: str,
    reason: StageRunReason,
    *,
    receipt: StageReceipt | None,
    current_inputs: dict[str, str] | None = None,
    changed_keys: Sequence[str] = (),
) -> StageResumeDecision:
    return StageResumeDecision(
        stage_name=stage,
        decision=StageResumeDecisionKind.RUN,
        reason=reason,
        receipt_status=receipt.status.value if receipt else "missing",
        changed_input_keys=list(changed_keys),
        recorded_input_digests=dict(receipt.input_digests) if receipt else {},
        current_input_digests=dict(current_inputs or {}),
    )


def compute_current_input_digests(
    config: MaieusisProjectConfig,
    paths: RunPaths,
    stage: str,
    *,
    drafts: Sequence[PaperCaseDraft] | None = None,
    topic_source_table: object | None = None,
    topic_r5_source_table: object | None = None,
) -> dict[str, str]:
    """Recompute a stage's CURRENT input digests from the real inputs (never trusts the receipt)."""
    del topic_source_table, topic_r5_source_table  # derived tables are not pinned (see below)
    if stage == STAGE_PAPER_HALF:
        return compute_paper_half_input_digests(config, drafts)
    if stage == STAGE_DATASET_HALF:
        return {
            **compute_dataset_half_input_digests(config),
            **upstream_input_digests(paths, STAGE_DATASET_HALF),
        }
    return upstream_input_digests(paths, stage)


def plan_resume(
    config: MaieusisProjectConfig,
    paths: RunPaths,
    *,
    drafts: Sequence[PaperCaseDraft] | None = None,
    topic_source_table: TopicSourceTable | None = None,
    topic_r5_source_table: R5TopicEvidenceSourceTable | None = None,
    family_count: int = 6,
    variants_per_family: int | None = None,
) -> ResumePlan:
    """PURE decision pass: per-stage REUSE/RUN + per-family decisions, zero execution.

    Walks the static DAG in order. Predicate (ALL must hold, else RUN): reusable receipt status ·
    identical recomputed input digests · identical config/model slices · every recorded output
    intact (else corruption, fail closed). A RUN stage marks its transitive downstream RUN.
    """
    variants_per_family = (
        config.run.variants_per_family if variants_per_family is None else variants_per_family
    )

    # Demo recomputes digests from the same deterministic demo inputs the fresh run recorded, so
    # `maieusis status` / `maieusis resume` see REUSE (else the injected-draft vs inbox-PDF digest differs).
    if config.is_demo and config.paperbank.import_from_run is None:
        from ...demo.generation import demo_paper_drafts, demo_topic_source_table

        if drafts is None:
            drafts = demo_paper_drafts()
        if topic_source_table is None:
            topic_source_table = demo_topic_source_table()

    decisions: dict[str, StageResumeDecision] = {}
    for stage in STAGE_ORDER:
        receipt = read_stage_receipt(paths, stage)
        ran_upstreams = [
            up
            for up in STAGE_UPSTREAM[stage]
            if decisions[up].decision == StageResumeDecisionKind.RUN
        ]
        if ran_upstreams:
            decisions[stage] = _run_decision(
                stage, StageRunReason.UPSTREAM_RAN, receipt=receipt, changed_keys=ran_upstreams
            )
            continue
        if receipt is None:
            decisions[stage] = _run_decision(stage, StageRunReason.MISSING_RECEIPT, receipt=None)
            continue
        if receipt.status not in _REUSABLE_STATUSES:
            decisions[stage] = _run_decision(
                stage, StageRunReason.RECEIPT_NOT_COMPLETE, receipt=receipt
            )
            continue
        expected_config = stage_config_version(
            config, stage, family_count=family_count, variants_per_family=variants_per_family
        )
        expected_models = stage_model_versions(config, stage)
        expected_prompts = stage_prompt_versions(stage)
        if (
            receipt.config_version != expected_config
            or receipt.model_versions != expected_models
            or receipt.prompt_versions != expected_prompts
        ):
            decisions[stage] = _run_decision(
                stage, StageRunReason.CONFIG_OR_MODEL_CHANGED, receipt=receipt
            )
            continue
        current = compute_current_input_digests(
            config,
            paths,
            stage,
            drafts=drafts,
            topic_source_table=topic_source_table,
            topic_r5_source_table=topic_r5_source_table,
        )
        if current != receipt.input_digests:
            changed = sorted(
                key
                for key in set(current) | set(receipt.input_digests)
                if current.get(key) != receipt.input_digests.get(key)
            )
            decisions[stage] = _run_decision(
                stage,
                StageRunReason.INPUT_DIGEST_CHANGED,
                receipt=receipt,
                current_inputs=current,
                changed_keys=changed,
            )
            continue
        verified = _verify_output_digests(
            paths.root, receipt.output_digests, owner_label=f"stage {stage!r}"
        )
        if stage == STAGE_D:
            for relative_path in _verify_stage_d_outcome_binding(paths):
                if relative_path not in verified:
                    verified.append(relative_path)
        decisions[stage] = StageResumeDecision(
            stage_name=stage,
            decision=StageResumeDecisionKind.REUSE,
            reason=StageRunReason.REUSE_VERIFIED,
            receipt_status=receipt.status.value,
            recorded_input_digests=dict(receipt.input_digests),
            current_input_digests=current,
            verified_output_paths=verified,
        )

    # Back-half family granularity: only meaningful when stage D is REUSED (same shortlist).
    family_decisions: list[FamilyResumeDecision] = []
    completed: list[FamilyCompletionRecord] = []
    if decisions[STAGE_D].decision == StageResumeDecisionKind.REUSE:
        manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
        back = decisions[STAGE_BACK_HALF]
        if back.reason == StageRunReason.CONFIG_OR_MODEL_CHANGED:
            # A family terminal is valid only under the back-half semantics/model/config that
            # produced it. In particular, increasing max_revise_rounds must re-enter an exhausted
            # family instead of silently reusing the old terminal and discarding the new budget.
            slugs = family_slug_map(manifest)
            family_decisions = [
                FamilyResumeDecision(
                    question_family_id=shortlisted.family.question_family_id,
                    slug=slugs[shortlisted.family.question_family_id],
                    decision=StageResumeDecisionKind.RUN,
                    reason=FamilyResumeReason.BACK_HALF_CHANGED,
                )
                for shortlisted in manifest.shortlisted
            ]
        else:
            completed, family_decisions = discover_family_completions(paths, manifest)
            incomplete = [d for d in family_decisions if d.decision == StageResumeDecisionKind.RUN]
            if back.decision == StageResumeDecisionKind.REUSE and incomplete:
                # The stage receipt verified but a family is incomplete → the stage re-runs with
                # the completed families skipped via completed_records (the family-level skip unit).
                decisions[STAGE_BACK_HALF] = _run_decision(
                    STAGE_BACK_HALF,
                    StageRunReason.INCOMPLETE_FAMILIES,
                    receipt=read_stage_receipt(paths, STAGE_BACK_HALF),
                    changed_keys=[d.question_family_id for d in incomplete],
                )
    else:
        # The shortlist itself re-runs → every family re-runs fresh (upstream invalidation).
        completed = []

    from ..presentation.materialize import plan_presentation_resume

    presentation_decision = plan_presentation_resume(
        paths,
        scientific_stage_will_run=any(
            decision.decision == StageResumeDecisionKind.RUN for decision in decisions.values()
        ),
    )
    return ResumePlan(
        run_id=paths.root.name,
        stage_decisions=decisions,
        family_decisions=family_decisions,
        completed_families=completed,
        presentation_decision=presentation_decision,
    )


# --- artifact discovery helpers (deterministic rehydration paths) -----------------------------------
def find_payload_path(paths: RunPaths) -> Path:
    """The single persisted V2 context payload (its filename embeds the context id)."""
    candidates = sorted(
        (paths.corpus / "context" / "question_scientist").glob(
            "*.question_scientist_context_v2.yaml"
        )
    )
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one V2 context payload under {paths.corpus}, found {len(candidates)}"
        )
    return candidates[0]


def find_shortlist_path(paths: RunPaths) -> Path:
    return (
        paths.corpus / "question_families" / "reviewed" / "question_family_shortlist_manifest.yaml"
    )


# --- clean steps -------------------------------------------------------------------------------
def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def clean_stage_for_rerun(paths: RunPaths, stage: str) -> None:
    """Delete the areas a RUN stage exclusively owns + its receipt (re-run-safe on a dirty dir)."""
    if stage == STAGE_BACK_HALF:
        raise ValueError("the back half is cleaned per family (clean_back_half_for_rerun)")
    _clear_manifest_stage_receipt(paths, stage, removed_roots=STAGE_CLEAN_AREAS[stage])
    for rel in STAGE_CLEAN_AREAS[stage]:
        _remove(paths.root / rel)
    _remove(paths.receipts / f"{_receipt_file_name(stage)}")


def _receipt_file_name(stage: str) -> str:
    return f"{family_slug(stage)}.yaml"


def _clear_manifest_stage_receipt(
    paths: RunPaths, stage: str, *, removed_roots: Sequence[str] = ()
) -> None:
    """Detach current pointers before resume removes their owned files."""
    if not paths.run_manifest.is_file():
        return
    from ...schemas.run_manifest import (
        PaperDispositionKind,
        ProductProcessingState,
        RunStage,
    )
    from .run_envelope import (
        _load_run_manifest_schema,
        _validate_manifest_integrity,
        write_run_manifest,
    )

    prefixes = tuple(root.rstrip("/") for root in removed_roots)

    def is_removed(path: str) -> bool:
        return bool(path) and any(
            path == prefix or path.startswith(prefix + "/") for prefix in prefixes
        )

    # A previous attempt may have crashed after atomically replacing one stage-owned file but
    # before refreshing its manifest record. Validate everything EXCEPT the paths this cleanup is
    # about to detach; corruption anywhere else remains a hard failure.
    manifest = _load_run_manifest_schema(paths)
    ignored_paths = {artifact.path for artifact in manifest.artifacts if is_removed(artifact.path)}
    ignored_paths.update(
        path
        for paper in manifest.papers
        for path in (paper.paper_case_path, paper.formation_trace_path)
        if is_removed(path)
    )
    ignored_paths.update(
        diagnostic.internal_path
        for diagnostic in manifest.diagnostics
        if is_removed(diagnostic.internal_path)
    )
    _validate_manifest_integrity(paths, manifest, ignore_paths=ignored_paths)

    stage_record = next(item for item in manifest.stages if item.stage == RunStage(stage))
    stage_record.receipt_path = ""
    stage_record.processing_state = ProductProcessingState.NOT_REACHED
    if prefixes:
        manifest.artifacts = [
            artifact for artifact in manifest.artifacts if not is_removed(artifact.path)
        ]
        manifest.diagnostics = [
            diagnostic
            for diagnostic in manifest.diagnostics
            if not is_removed(diagnostic.internal_path)
        ]
    if stage == STAGE_PAPER_HALF:
        for paper in manifest.papers:
            paper.disposition = PaperDispositionKind.PENDING
            paper.reason = ""
            paper.paper_case_path = ""
            paper.formation_trace_path = ""
    write_run_manifest(paths, manifest)


def orchestrator_tree(paths: RunPaths, run_id: str) -> Path:
    """The orchestrator's own tree: it receives ``output_root=run_root`` and nests under run_id."""
    return paths.root / run_id


def _branch_dir_for_family(paths: RunPaths, run_id: str, question_family_id: str) -> Path:
    # The branch manager's deterministic branch-id contract (READ-ONLY reuse of the private helper;
    # the kickoff pins re-entrancy on exactly this determinism — branch_manager itself is untouched).
    from .branch_manager import _branch_id

    return orchestrator_tree(paths, run_id) / "branches" / _branch_id(run_id, question_family_id)


def clean_back_half_for_rerun(
    paths: RunPaths,
    run_id: str,
    *,
    rerun_family_ids: Sequence[str],
    slugs: dict[str, str],
    wholesale: bool,
) -> None:
    """DP-4 cleaning: per-incomplete-family branch+layout dirs, or wholesale when the shortlist ran.

    Internal branch scratch may be removed for re-entry. Stable ``families/<slug>/`` projections are
    never deleted before a replacement validates; their writers promote adjacent replacements.
    """
    _clear_manifest_stage_receipt(paths, STAGE_BACK_HALF)
    if wholesale:
        _remove(orchestrator_tree(paths, run_id))
    else:
        for family_id in rerun_family_ids:
            _remove(_branch_dir_for_family(paths, run_id, family_id))
        _remove(orchestrator_tree(paths, run_id) / "aggregate_dossier_coordination")
    _remove(paths.receipts / _receipt_file_name(STAGE_BACK_HALF))


# --- resume receipt persistence -----------------------------------------------------------------------
def persist_resume_receipt(paths: RunPaths, plan: ResumePlan, config_digest: str) -> Path:
    index = 1 + sum(1 for _ in paths.receipts.glob("resume-*.yaml"))
    receipt = ResumeReceipt(
        run_id=plan.run_id,
        resume_index=index,
        config_digest=config_digest,
        stage_decisions=[plan.stage_decisions[stage] for stage in STAGE_ORDER],
        family_decisions=list(plan.family_decisions),
        presentation_decision=plan.presentation_decision,
    )
    return dump_data(receipt, paths.resume_receipt(index))


def resume_note_for(plan: ResumePlan) -> str:
    return (
        f"This run was resumed: {plan.reused_stage_count} stage(s) reused, "
        f"{plan.rerun_stage_count} stage(s) re-run."
    )


# --- the resume driver ---------------------------------------------------------------------------------
def _execute_resume_initialized(
    config: MaieusisProjectConfig,
    run_id: str,
    *,
    executor: object | None = None,
    drafts: Sequence[PaperCaseDraft] | None = None,
    topic_source_table: TopicSourceTable | None = None,
    topic_r5_source_table: R5TopicEvidenceSourceTable | None = None,
    family_count: int = 6,
    variants_per_family: int | None = None,
    scientific_preflight_complete: bool = True,
) -> ResumeExecutionResult:
    """`maieusis resume`: plan (pure) → persist the decision set → clean → execute only what must RUN.

    A fully-reused resume constructs ZERO providers and spawns nothing — it only regenerates
    ``summary.md`` (with the honest resume note). Paid input resolution (PDF ingestion, topic
    retrieval) happens ONLY when the owning stage actually re-runs.
    """
    from ...providers.models.base import ModelConfigurationError, StructuredModelProviderError
    from ...providers.scientific_agents import ScientificAgentInfrastructureError
    from ..agents.question_scientist_family import NoValidFamilies, StageDPromptBudgetError
    from .end_to_end import (
        StageExecutor,
        _dataset_context_run_terminal,
        _planning_ineligible_run_terminal,
        _project_imported_paper_half,
        _stage_d_run_terminal,
        effective_family_count,
        effective_variants_per_family,
        exec_back_half,
        exec_front_layout,
        exec_stage_c,
        exec_stage_d,
        exec_stage_dataset_half,
        exec_stage_paper_half,
        ingest_paper_drafts,
        maybe_write_paper_half_terminal_summary,
        preserve_branch_products_before_cleanup,
    )
    from .paperbank_import import import_paperbank_from_run

    # Bind resume to the SAME family cap the fresh run used (run.max_families) so the recomputed stage-D
    # config digest matches — otherwise a capped run would falsely re-RUN (and re-pay) stage D on resume.
    family_count = effective_family_count(config, family_count)
    variants_per_family = effective_variants_per_family(config, variants_per_family)

    # Demo resolves the executor + drafts + topic table to the same deterministic demo assets the
    # fresh run used, so the recomputed digests match and a completed demo run resumes all-REUSE.
    if config.is_demo and config.paperbank.import_from_run is None:
        from ...demo.generation import demo_paper_drafts, demo_topic_source_table

        if drafts is None:
            drafts = demo_paper_drafts()
        if topic_source_table is None:
            topic_source_table = demo_topic_source_table()

    run_root = Path(config.run.output_root) / run_id
    if not run_root.is_dir() or not any(run_root.iterdir()):
        raise ValueError(
            f"run {run_id!r} not found at {run_root} — nothing to resume (start with 'maieusis run')"
        )
    paths = RunPaths(root=run_root)
    with acquire_run_lock(run_root, command="maieusis resume"):
        plan = plan_resume(
            config,
            paths,
            drafts=drafts,
            topic_source_table=topic_source_table,
            topic_r5_source_table=topic_r5_source_table,
            family_count=family_count,
            variants_per_family=variants_per_family,
        )
        if not plan.all_stages_reused and not scientific_preflight_complete:
            raise ScientificResumePreflightRequired(
                "one or more scientific stages require execution after the locked re-plan"
            )

        if not plan.all_stages_reused:
            from ...schemas.run_manifest import ProductProcessingState, RunProcessingState
            from .run_envelope import (
                RunContext,
                load_run_manifest,
                set_run_state,
                write_run_manifest,
            )

            current_manifest = load_run_manifest(paths, allow_missing_receipts=True)
            missing_link = False
            for stage_record in current_manifest.stages:
                if (
                    stage_record.receipt_path
                    and not (paths.root / stage_record.receipt_path).is_file()
                ):
                    stage_record.receipt_path = ""
                    stage_record.processing_state = ProductProcessingState.NOT_REACHED
                    missing_link = True
            if missing_link:
                write_run_manifest(paths, current_manifest)
        persist_resume_receipt(paths, plan, stable_hash(config.model_dump(mode="json")))
        note = resume_note_for(plan)

        if not plan.all_stages_reused:
            set_run_state(
                RunContext(run_id=run_id, paths=paths),
                RunProcessingState.RUNNING,
                next_action=(
                    "Resume is running; previous validated products remain current until replaced."
                ),
            )

        if plan.presentation_only:
            from ..presentation.materialize import try_materialize_detailed_presentation
            from .run_envelope import RunContext

            try_materialize_detailed_presentation(RunContext(run_id=run_id, paths=paths))
            return ResumeExecutionResult(
                summary=paths.summary,
                plan=plan,
                presentation_attempted=True,
            )

        if plan.all_stages_reused:
            manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
            if not manifest.planning_eligible:
                _planning_ineligible_run_terminal(
                    config, paths, run_id, resume_note=resume_note_for(plan)
                )
                return ResumeExecutionResult(summary=paths.summary, plan=plan)
            regenerate_summary_from_disk(config, paths, resume_note=note)
            return ResumeExecutionResult(summary=paths.summary, plan=plan)

        decisions = plan.stage_decisions

        def must_run(stage: str) -> bool:
            return decisions[stage].decision == StageResumeDecisionKind.RUN

        # DP-6: clean every RUN stage BEFORE executing anything (re-run-safe on dirty dirs).
        for stage in STAGE_ORDER[:-1]:
            if must_run(stage):
                clean_stage_for_rerun(paths, stage)
        if must_run(STAGE_BACK_HALF):
            wholesale = not plan.family_decisions  # stage D re-ran → no per-family granularity
            rerun_family_ids = [
                d.question_family_id
                for d in plan.family_decisions
                if d.decision == StageResumeDecisionKind.RUN
            ]
            if wholesale:
                from .run_envelope import load_run_manifest

                rerun_family_ids = [
                    family.family_id for family in load_run_manifest(paths).families
                ]
            preserve_branch_products_before_cleanup(
                config,
                paths,
                run_id=run_id,
                family_ids=rerun_family_ids,
            )
            manifest_slugs: dict[str, str] = {}
            if not wholesale:
                manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
                manifest_slugs = family_slug_map(manifest)
            clean_back_half_for_rerun(
                paths,
                run_id,
                rerun_family_ids=rerun_family_ids,
                slugs=manifest_slugs,
                wholesale=wholesale,
            )

        if config.is_demo and config.paperbank.import_from_run is None:
            from ...demo.generation import resolve_demo_run_inputs

            executor, drafts, topic_source_table = resolve_demo_run_inputs(
                config,
                executor=executor,
                drafts=drafts,
                topic_source_table=topic_source_table,
            )
        resolved_executor = executor if executor is not None else StageExecutor(config)
        if must_run(STAGE_PAPER_HALF):
            from .run_envelope import RunContext

            run_context = RunContext(run_id=run_id, paths=paths)
            if config.paperbank.import_from_run is not None:
                if drafts is not None:
                    raise ValueError(
                        "paperbank.import_from_run cannot be combined with injected paper drafts"
                    )
                _project_imported_paper_half(
                    run_context, import_paperbank_from_run(config, run_context)
                )
            else:
                resolved_drafts = (
                    list(drafts)
                    if drafts is not None
                    else ingest_paper_drafts(
                        config,
                        resolved_executor,  # type: ignore[arg-type]
                        run_context=run_context,
                    )
                )
                exec_stage_paper_half(
                    config,
                    resolved_executor,  # type: ignore[arg-type]
                    paths,
                    resolved_drafts,
                    input_digests=compute_paper_half_input_digests(config, drafts),
                )
        # Honest run terminal: a zero-accepted paper half (freshly re-run OR a reused
        # SCIENTIFIC_TERMINAL receipt) stops the resume here with the run-terminal summary — never a
        # stage-C crash on the missing pattern manifest.
        terminal_summary = maybe_write_paper_half_terminal_summary(paths, resume_note=note)
        if terminal_summary is not None:
            return ResumeExecutionResult(summary=terminal_summary, plan=plan)
        # Q2: mirror the fresh-run honest terminal on resume — a dataset-half / stage-C fail-closed
        # verdict writes a SCIENTIFIC_TERMINAL receipt + summary.md and stops, never a bare traceback.
        if must_run(STAGE_DATASET_HALF):
            try:
                exec_stage_dataset_half(
                    config,
                    resolved_executor,  # type: ignore[arg-type]
                    paths,
                    topic_source_table=topic_source_table,
                    topic_r5_source_table=topic_r5_source_table,
                )
            except (ValueError, ValidationError) as exc:
                _dataset_context_run_terminal(
                    config, paths, run_id, exc, stage=STAGE_DATASET_HALF, resume_note=note
                )
                return ResumeExecutionResult(summary=paths.summary, plan=plan)
        if must_run(STAGE_C):
            try:
                exec_stage_c(config, paths)
            except (ValueError, ValidationError) as exc:
                _dataset_context_run_terminal(
                    config, paths, run_id, exc, stage=STAGE_C, resume_note=note
                )
                return ResumeExecutionResult(summary=paths.summary, plan=plan)
        if must_run(STAGE_D):
            try:
                exec_stage_d(
                    config,
                    resolved_executor,  # type: ignore[arg-type]
                    paths,
                    family_count=family_count,
                    variants_per_family=variants_per_family,
                )
            except (
                NoValidFamilies,
                StageDPromptBudgetError,
                StructuredModelProviderError,
                ModelConfigurationError,
                ScientificAgentInfrastructureError,
            ) as exc:
                _stage_d_run_terminal(config, paths, run_id, exc, resume_note=note)
                return ResumeExecutionResult(summary=paths.summary, plan=plan)
        if must_run(STAGE_FRONT_LAYOUT):
            exec_front_layout(config, paths)
        manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
        if not manifest.planning_eligible:
            _planning_ineligible_run_terminal(config, paths, run_id, resume_note=note)
            return ResumeExecutionResult(summary=paths.summary, plan=plan)
        if must_run(STAGE_BACK_HALF):
            exec_back_half(
                config,
                resolved_executor,  # type: ignore[arg-type]
                paths,
                run_id,
                completed=plan.completed_families,
                resume_note=note,
            )
        else:
            # e.g. only the layout re-ran — the back half is intact; just restate the summary.
            regenerate_summary_from_disk(config, paths, resume_note=note)
        return ResumeExecutionResult(summary=paths.summary, plan=plan)


def execute_resume_from_config(
    config: MaieusisProjectConfig,
    run_id: str,
    *,
    executor: object | None = None,
    drafts: Sequence[PaperCaseDraft] | None = None,
    topic_source_table: TopicSourceTable | None = None,
    topic_r5_source_table: R5TopicEvidenceSourceTable | None = None,
    family_count: int = 6,
    variants_per_family: int | None = None,
    scientific_preflight_complete: bool = True,
) -> Path:
    """Resume one existing envelope and preserve its last valid projections on failure."""
    from ...schemas.run_manifest import (
        ArtifactAuthority,
        ArtifactKind,
        DiagnosticClass,
        ProductProcessingState,
        RunProcessingState,
    )
    from .run_envelope import (
        RunContext,
        index_existing_artifact,
        load_run_manifest,
        record_run_failure,
        set_run_state,
    )

    paths = RunPaths(root=Path(config.run.output_root) / run_id)
    if not paths.root.is_dir() or not any(paths.root.iterdir()):
        raise ValueError(
            f"run {run_id!r} not found at {paths.root} — nothing to resume (start with 'maieusis run')"
        )
    manifest = load_run_manifest(paths, allow_missing_receipts=True)
    if manifest.run_id != run_id:
        raise ValueError("run manifest identity does not match the requested run")
    context = RunContext(run_id=run_id, paths=paths)
    try:
        execution = _execute_resume_initialized(
            config,
            run_id,
            executor=executor,
            drafts=drafts,
            topic_source_table=topic_source_table,
            topic_r5_source_table=topic_r5_source_table,
            family_count=family_count,
            variants_per_family=variants_per_family,
            scientific_preflight_complete=scientific_preflight_complete,
        )
    except ScientificResumePreflightRequired:
        raise
    except Exception:
        record_run_failure(
            context,
            code="resume_exception",
            diagnostic_class=DiagnosticClass.PROGRAMMER_FAULT,
            public_message=(
                "Resume stopped before replacement completed; previous validated products remain current."
            ),
            failed=False,
        )
        raise
    summary = execution.summary
    if execution.plan.presentation_only:
        return summary
    if summary.is_file():
        index_existing_artifact(
            context,
            summary,
            kind=ArtifactKind.SUMMARY,
            processing_state=ProductProcessingState.PRODUCED,
            authority=ArtifactAuthority.PROVISIONAL,
        )
    post_run = load_run_manifest(paths)
    family_outcomes: list[FamilyRunOutcome] = []
    family_processing_incomplete = False
    shortlist_path = find_shortlist_path(paths)
    if shortlist_path.is_file():
        shortlist = load_model(shortlist_path, QuestionFamilyShortlistManifest)
        family_outcomes, family_processing_incomplete = inspect_persisted_family_processing(
            paths, shortlist
        )
    shared_incomplete = any(
        stage.processing_state in {ProductProcessingState.DEGRADED, ProductProcessingState.FAILED}
        for stage in post_run.stages
    )
    family_projection_degraded = any(
        family.closure_state in {ProductProcessingState.DEGRADED, ProductProcessingState.FAILED}
        for family in post_run.families
    )
    infrastructure_incomplete = (
        shared_incomplete
        or family_processing_incomplete
        or any(
            outcome.failure_class is not None and outcome.failure_class != FailureClass.SCIENTIFIC
            for outcome in family_outcomes
        )
    )
    accepted_count = sum(
        outcome.dossier_axis == DossierAxis.RENDERED for outcome in family_outcomes
    )
    if summary.is_file() and (shared_incomplete or family_projection_degraded):
        index_existing_artifact(
            context,
            summary,
            kind=ArtifactKind.SUMMARY,
            processing_state=ProductProcessingState.DEGRADED,
            authority=ArtifactAuthority.PROVISIONAL,
        )
    set_run_state(
        context,
        RunProcessingState.INCOMPLETE if infrastructure_incomplete else RunProcessingState.COMPLETE,
        next_action=(
            (
                "Read the available family dossiers and terminal summary; inspect any degraded "
                "family separately."
                if family_projection_degraded
                else (
                    "Read the family dossiers and terminal summary; downstream authorization "
                    "remains separate."
                )
            )
            if not infrastructure_incomplete and accepted_count
            else (
                "Shared or family infrastructure processing is incomplete; read any retained "
                "family dossiers, inspect diagnostics, then resume after correcting the failure."
                if infrastructure_incomplete
                else "All families reached honest scientific terminals; inspect their retained "
                "plans, outcome dossiers, and review diagnostics before revising inputs."
            )
        ),
    )
    if not execution.plan.all_stages_reused:
        from ..presentation.materialize import try_materialize_detailed_presentation

        try_materialize_detailed_presentation(context)
    return summary


def regenerate_summary_from_disk(
    config: MaieusisProjectConfig, paths: RunPaths, *, resume_note: str
) -> Path:
    """Rebuild ``summary.md`` purely from persisted state (completion records + manifest buckets)."""
    from ...schemas.question_scientist_context_v2 import (
        EvidenceBasis,
        QuestionScientistContextPayloadV2,
    )
    from ..context.evidence_basis_labels import summary_evidence_basis_line
    from .end_to_end import (
        _SHORTLIST_BUCKET_AXIS,  # the single bucket→axis map
        evidence_basis_by_family,
        is_development_surrogate,
        non_included_family_outcome,
    )
    from .run_layout import write_run_summary

    manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
    completed, _ = discover_family_completions(paths, manifest)
    outcomes = [record.family_run_outcome for record in completed]
    for bucket, axis in _SHORTLIST_BUCKET_AXIS.items():
        for family_id in getattr(manifest, f"{bucket}_family_ids"):
            outcomes.append(non_included_family_outcome(family_id, shortlist_axis=axis))

    paper_out = load_model(paths.stage_output(STAGE_PAPER_HALF), PaperHalfStageOutput)
    dataset_out = load_model(paths.stage_output(STAGE_DATASET_HALF), DatasetHalfStageOutput)
    development_surrogate = is_development_surrogate(
        config,
        front_half_receipts=[*paper_out.receipts, *dataset_out.receipts],
        dossier_statuses=[record.dossier_record.status for record in completed],
    )
    payload = load_model(find_payload_path(paths), QuestionScientistContextPayloadV2)
    basis_by_family = evidence_basis_by_family(payload, [sf.family for sf in manifest.shortlisted])
    included_ids = {record.question_family_id for record in completed}
    abstract_only = sum(
        1
        for family_id in included_ids
        if basis_by_family.get(family_id) == EvidenceBasis.ABSTRACT_ONLY
    )
    return write_run_summary(
        paths,
        outcomes,
        development_surrogate=development_surrogate,
        authority_ceiling=manifest.authority_ceiling,
        evidence_basis_line=summary_evidence_basis_line(abstract_only, len(included_ids)),
        resume_note=resume_note,
    )
