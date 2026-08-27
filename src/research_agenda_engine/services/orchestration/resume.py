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
from typing import TYPE_CHECKING, Literal, NoReturn, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from yaml import YAMLError, safe_dump

from ...io import dump_data, load_data, load_model
from ...provenance import semantic_hash, sha256_bytes, sha256_file, stable_hash
from ...providers.models.base import VENDOR_DEFAULT
from ...providers.models.policy import model_versions_accept
from ...schemas.derived_dataset_scope import DATASET_SCOPE_DERIVER_PROMPT_VERSION
from ...schemas.external_evidence import (
    ExternalEvidenceAttemptStatus,
    ExternalEvidenceBatchReceipt,
    LegacyExternalEvidenceDegradationReceipt,
    RetrievalOperation,
)
from ...schemas.front_half_authority import FrontHalfAuthorityCeiling, FrontHalfCeilingReason
from ...schemas.gate_outcome import PromotionReceipt
from ...schemas.inferred_research_scope import ResolvedResearchScope
from ...schemas.maieusis_project_config import MaieusisProjectConfig
from ...schemas.multi_family_dossier import FamilyDossierStatus
from ...schemas.novelty_admission import (
    NoveltyEvidencePack,
    NoveltyPriorEvidenceOrigin,
    NoveltyWebLeadResolution,
    NoveltyWebLeadResolutionReservation,
    NoveltyWebLeadResolutionStatus,
    NoveltyWebSearchReceipt,
    NoveltyWebSearchReservation,
    VariantNoveltyAssessment,
)
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
from ...schemas.run_outcome import DossierAxis, FamilyRunOutcome, RunTerminal
from ...schemas.stage_d import StageDCandidateDisposition, StageDOutcomeRecord
from ...schemas.stage_receipt import FailureClass, StageReceipt, StageStatus
from ..agents.citation_importance_reviewer import CITATION_IMPORTANCE_REVIEWER_PROMPT_VERSION
from ..agents.dataset_narrative_reviewer import (
    DATASET_NARRATIVE_FIDELITY_REVIEWER_PROMPT_VERSION,
)
from ..agents.formation_trace_reviewer import FORMATION_TRACE_REVIEWER_PROMPT_VERSION
from ..agents.novelty_admission import (
    NOVELTY_REVIEWER_PROMPT_VERSION,
    NOVELTY_REVISION_PROMPT_VERSION,
    NOVELTY_WEB_SCOUT_PROMPT_VERSION,
)
from ..agents.paper_case_reviewer import PAPER_CASE_FIDELITY_REVIEWER_PROMPT_VERSION
from ..agents.pattern_reviewer import QUESTION_PATTERN_REVIEWER_PROMPT_VERSION
from ..agents.topic_evidence_reviewer import TOPIC_EVIDENCE_REVIEWER_PROMPT_VERSION
from ..context.dataset_narrative import DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION
from ..context.topic_evidence import (
    TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION,
    TOPIC_FIELD_STATE_SYNTHESIZER_PROMPT_VERSION,
    R5TopicEvidenceSourceTable,
    R5TopicSourceRecordEvidence,
    TopicSourceAbstractStatus,
    TopicSourceSnippetKind,
    assess_fulltext_rights_degradation,
    fulltext_rights_are_verified,
)
from ..context.topic_evidence_revision import (
    TOPIC_EVIDENCE_BRIEF_REVISER_PROMPT_VERSION,
    TopicEvidenceRevisionHistory,
)
from ..context.topic_evidence_terminal_inquiry import (
    TOPIC_EVIDENCE_TERMINAL_INQUIRY_PROMPT_VERSION,
)
from ..narrative_sources.narrative_revision import DATASET_NARRATIVE_REVISER_PROMPT_VERSION
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
from ..retrieval.topic_source_selection import TOPIC_SOURCE_SELECTOR_PROMPT_VERSION
from .run_layout import (
    RunPaths,
    assign_family_slugs,
    family_slug,
    read_stage_receipt,
    write_run_terminal_summary,
    write_stage_receipt,
)

if TYPE_CHECKING:
    from ...schemas.topic_literature import TopicSourceTable
    from ..context.question_scientist_export import RightsSafeTopicSourceProjection


_N2Model = TypeVar("_N2Model", bound=BaseModel)


# --- stage names + the explicit coarse DAG -------------
STAGE_PAPER_HALF = "paper_half"
STAGE_DATASET_HALF = "dataset_half"
STAGE_C = "stage_c"
STAGE_D = "stage_d"
STAGE_FRONT_LAYOUT = "front_layout"
STAGE_BACK_HALF = "back_half"

# Receipt config slices must change when a stage's deterministic semantics change, even if operator
# config and model routing do not. Otherwise an honest SCIENTIFIC_TERMINAL from old code is reusable
# forever and a launch-blocker fix cannot take effect on resume. Bump the respective explicit
# revision for every paper- or dataset-half semantic change that can alter products or disposition.
PAPER_HALF_IMPLEMENTATION_VERSION = "paper_half/v9-identity-basis-and-round-labels"
DATASET_HALF_IMPLEMENTATION_VERSION = "dataset_half/v10-accounted-narrowing"
STAGE_C_IMPLEMENTATION_VERSION = "stage_c/v2-rights-safe-projection"
STAGE_D_IMPLEMENTATION_VERSION = "stage_d/v2-n2-web-grounding"
FRONT_LAYOUT_IMPLEMENTATION_VERSION = "front_layout/v2-novelty-admission-projection"
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
        # Current-attempt gate diagnostics are projections of this stage. Leaving a failed attempt
        # here caused a healthy resume to re-index the stale failure into its final README.
        "diagnostics/paper_case_fidelity",
        "diagnostics/paper_case_fidelity_accepted",
        "diagnostics/citation_importance",
        "diagnostics/citation_importance_accepted",
        "diagnostics/formation_trace_draft",
        "diagnostics/formation_trace",
        "diagnostics/formation_trace_accepted",
        "diagnostics/question_pattern_induction",
        "diagnostics/question_pattern",
        "diagnostics/question_pattern_accepted",
        # The pattern-bank manifest sits at the corpus root (NOT under patterns/); a re-run that ends
        # all-unusable would otherwise leave a PREVIOUS run's manifest for stage C to read.
        "corpus/question_pattern_manifest.yaml",
        "stage_outputs/paper-half.yaml",
    ),
    STAGE_DATASET_HALF: (
        "corpus/context/dataset_narratives",
        "corpus/context/topic_evidence",
        "stage_outputs/dataset-half.yaml",
        "stage_outputs/dataset-half-terminal.yaml",
        "receipts/fulltext-enrichment.yaml",
        "receipts/external-evidence",
    ),
    STAGE_C: (
        "corpus/research_intent.yaml",
        "corpus/context/question_scientist",
        "stage_outputs/stage-c-terminal.yaml",
    ),
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


_TOPIC_SOURCE_TABLE_RELATIVE_PATH = (
    "corpus/context/topic_evidence/sources/research_intent.topic_source_table.yaml"
)
_EXTERNAL_EVIDENCE_BATCH_RELATIVE_PATH = "receipts/external-evidence/fulltext-enrichment-batch.yaml"
_TOPIC_RIGHTS_DEGRADATION_RELATIVE_PATH = "receipts/external-evidence/topic-rights-degradation.yaml"
_LEGACY_RIGHTS_SIDECAR_DIGEST_PREFIX = "legacy_rights_sidecar_sha256:"
_EXTERNAL_EVIDENCE_TRANSPORT_STATUSES = frozenset(
    {
        ExternalEvidenceAttemptStatus.SUCCEEDED,
        ExternalEvidenceAttemptStatus.HTTP_ERROR,
        ExternalEvidenceAttemptStatus.STATUS_REJECTED,
        ExternalEvidenceAttemptStatus.FINAL_URL_REJECTED,
        ExternalEvidenceAttemptStatus.MEDIA_TYPE_REJECTED,
        ExternalEvidenceAttemptStatus.BODY_REJECTED,
        ExternalEvidenceAttemptStatus.FETCH_ERROR,
    }
)


class _LegacyV01TopicSourceRecord(BaseModel):
    """Exact pre-rights record surface retained by the climate validation run.

    This is intentionally not a permissive alias for the current record model. It names every
    field present on the retained artifact and forbids every later field, including the current
    rights, fallback, and provenance fields. It is consumed only by the bounded resume migration;
    normal ``R5TopicSourceRecordEvidence`` construction remains fail-closed.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_record_id: str
    lane_ids: list[str]
    query_ids: list[str]
    title: str
    year: int | None
    doi: str
    pmid: str
    openalex_id: str
    semantic_scholar_id: str
    url: str
    abstract_or_snippet: str
    abstract_status: Literal["available", "metadata_only"]
    snippet_kind: Literal["abstract", "fulltext_excerpt", "title_only"]
    ranking_features: dict[str, float]
    dedupe_key: str
    source_quality_flags: list[str]


class _LegacyV01TopicEvidenceSourceTable(BaseModel):
    """Exact table envelope paired with :class:`_LegacyV01TopicSourceRecord`."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    table_id: str
    query_plan_id: str
    protocol_version: Literal["r5_topic_evidence_lanes/v1"]
    records: list[_LegacyV01TopicSourceRecord]
    lane_coverage: dict[str, int]
    source_quality_flags: list[str]


@dataclass(frozen=True)
class _TopicSourceRightsMigrationView:
    """Rights partitions plus a safe in-memory projection over immutable source bytes."""

    safe_source_table: R5TopicEvidenceSourceTable
    degraded_source_record_ids: tuple[str, ...]
    abstract_fallback_source_record_ids: tuple[str, ...]
    metadata_only_source_record_ids: tuple[str, ...]
    legacy_v0_1_shape: bool = False


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
    topic_revision_history: TopicEvidenceRevisionHistory | None = None
    lane_coverage: dict[str, int] = Field(default_factory=dict)
    source_count: int = 0
    #: The candidate pool the kept sources were selected FROM. Carried here because only the stage
    #: that ran the selector knows it, and a resume rewrites the reader's retrieval summary: without
    #: this a resumed run would DOWNGRADE a summary that named the real pool to one that says the
    #: pool was not recorded. Zero means genuinely unknown -- an injected table, or a run from
    #: before this field existed -- and renders as "not recorded", never as the kept count.
    retrieved_count: int = 0
    scope: ResolvedResearchScope
    fulltext_counts: dict[str, int] = Field(default_factory=dict)
    external_evidence_batch_receipt_path: str = ""
    external_evidence_batch_receipt_digest: str = ""
    rights_degradation_receipt_path: str = ""
    rights_degradation_receipt_digest: str = ""
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED
    source_activity_path: str = ""
    # Why the ceiling was applied.  The ceiling alone cannot distinguish a brief that never reached
    # a reviewer from one that was reviewed and re-adjudicated and still found short, and every
    # reader-facing surface that says "unreviewed" is wrong about the second.  Absent on runs that
    # predate the field: consumers that need the distinction must fail closed on ``None``, never
    # read it as "verified".
    ceiling_reason: FrontHalfCeilingReason | None = None
    ceiling_residual_dimensions: list[str] = Field(default_factory=list)
    ceiling_reason_detail: str = ""


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
    digests = {
        f"pdf:{pdf.name}": sha256_file(pdf) for pdf in sorted(inbox.glob("*.pdf")) if pdf.is_file()
    }
    # Source-preparation sidecars (derivative receipts, article spans) are inputs too: a changed
    # sidecar must invalidate reuse exactly like changed PDF bytes. Absent sidecars leave every
    # pre-existing digest map byte-identical.
    for pattern in ("*.derivative.yaml", "*.article_span.yaml"):
        digests.update(
            {
                f"sidecar:{sidecar.name}": sha256_file(sidecar)
                for sidecar in sorted(inbox.glob(pattern))
                if sidecar.is_file()
            }
        )
    return digests


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

    CLIM-10: hashes the TIMESTAMP-FREE semantic output digests, so a scientifically identical
    upstream re-run (differing only by provenance timestamps embedded in its artifacts) yields the
    same value and downstream REUSES — the honest, cache-friendly behavior the docstring always
    promised. Pre-CLIM-10 receipts have no semantic digests and fall back to the raw byte digests
    (unchanged behavior). Missing upstream receipt → "missing" (never equal to a recorded hash).
    """
    receipt = read_stage_receipt(paths, upstream_stage)
    if receipt is None:
        return "missing"
    reuse_digests = receipt.semantic_output_digests or receipt.output_digests
    return stable_hash(dict(sorted(reuse_digests.items())))


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
        versions = {
            "questioner": _effective(config, models.questioner),
            "reviewer": _effective(config, models.reviewer),
            "novelty_reviewer": _effective(config, models.novelty_reviewer or models.reviewer),
        }
        if config.novelty.web_grounding.enabled and not config.is_demo:
            versions["novelty_web_scout"] = _effective(config, config.novelty.web_grounding.scout)
        return versions
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


def stage_prompt_versions(
    stage: str,
    *,
    config: MaieusisProjectConfig | None = None,
) -> dict[str, str]:
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
    if stage == STAGE_DATASET_HALF:
        return {
            "dataset_narrative_extraction": DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION,
            "dataset_narrative_review": DATASET_NARRATIVE_FIDELITY_REVIEWER_PROMPT_VERSION,
            # The bounded narrative repair loop is a real generator on this stage, so an upgrade to
            # its prompt must invalidate a resume exactly as the topic reviser's does. The dataset
            # half is not cross-run importable, so this key moves resume reuse only.
            "dataset_narrative_revision": DATASET_NARRATIVE_REVISER_PROMPT_VERSION,
            # The scope deriver decides which literature this stage retrieves at all, so a prompt
            # upgrade must invalidate a resume: reusing a dataset half derived under an older
            # deriver would silently keep a corpus the current product would not have searched.
            "dataset_scope_derivation": DATASET_SCOPE_DERIVER_PROMPT_VERSION,
            "topic_source_selection": TOPIC_SOURCE_SELECTOR_PROMPT_VERSION,
            "topic_field_state_synthesis": TOPIC_FIELD_STATE_SYNTHESIZER_PROMPT_VERSION,
            "topic_evidence_synthesis": TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION,
            "topic_evidence_revision": TOPIC_EVIDENCE_BRIEF_REVISER_PROMPT_VERSION,
            "topic_evidence_terminal_inquiry": TOPIC_EVIDENCE_TERMINAL_INQUIRY_PROMPT_VERSION,
            "topic_evidence_review": TOPIC_EVIDENCE_REVIEWER_PROMPT_VERSION,
        }
    if stage == STAGE_D:
        versions = {
            "novelty_review": NOVELTY_REVIEWER_PROMPT_VERSION,
            "novelty_revision": NOVELTY_REVISION_PROMPT_VERSION,
        }
        if config is not None and config.novelty.web_grounding.enabled and not config.is_demo:
            versions["novelty_web_scout"] = NOVELTY_WEB_SCOUT_PROMPT_VERSION
        return versions
    return {}


def _dataset_half_config_slice(
    config: MaieusisProjectConfig,
    *,
    include_rights_implementation_version: bool,
) -> dict[str, object]:
    """Return the exact dataset-half config slice for current or frozen-v0.1 semantics.

    Public v0.1 receipts predate an explicit dataset-half implementation revision.  The
    compatibility migrator must recognize that exact historical hash without treating an
    arbitrary config mismatch as eligible for a no-call migration.
    """

    literature = config.literature.model_dump(mode="json")
    _drop_unnamed_research_field(literature)
    payload: dict[str, object] = {
        "mode": config.mode.value,
        "dataset_id": config.dataset.seed.dataset_id,
        "link": config.dataset.seed.link,
        "docs": [str(path) for path in config.dataset.seed.docs],
        "literature": literature,
        "research_intent": config.research_intent.model_dump(mode="json"),
    }
    if include_rights_implementation_version:
        payload = {
            "implementation_version": DATASET_HALF_IMPLEMENTATION_VERSION,
            "max_revise_rounds": config.run.max_revise_rounds,
            **payload,
        }
    payload["allow_pro_model"] = config.models.allow_pro_model
    return payload


def legacy_dataset_half_config_version(config: MaieusisProjectConfig) -> str:
    """Frozen v0.1 dataset-half config hash (before the rights implementation version existed)."""

    return stable_hash(
        _dataset_half_config_slice(config, include_rights_implementation_version=False)
    )


def _drop_unnamed_research_field(dumped: object) -> None:
    """Strip an unnamed research field from a dumped LiteratureConfig.

    A run that names no field sends the same requests it sent before the field existed, so its
    dataset half is unchanged and its receipt must stay reusable -- the same rule
    ``_drop_vendor_default_reasoning`` enforces for reasoning depth, and for the same reason: this
    slice dumps ``config.literature`` wholesale, so a new key at its default would otherwise move
    the dataset-half config hash of every existing run and make a resume re-pay narrative fusion,
    retrieval, synthesis, and review to arrive at identical bytes.

    A field that WAS named is scientific configuration and stays in the digest. That is correct: it
    changes what literature the run acquires.
    """
    if not isinstance(dumped, dict):
        return
    if not str(dumped.get("research_field") or "").strip():
        dumped.pop("research_field", None)


def _drop_vendor_default_reasoning(dumped: object) -> None:
    """Strip reasoning depth from a dumped ProviderModel when it is the vendor default.

    A run configured at the vendor default sends exactly what runs sent before this field existed,
    so its scientific configuration is unchanged and its receipt must stay reusable. Leaving the
    keys in moved the ``paper_half`` and ``stage_d`` digests on EVERY pre-existing run: a resume
    re-paid the whole pipeline from 25-PDF extraction onward, and the cross-run PaperBank import --
    which uses this same predicate as a HARD gate -- failed at preflight.

    A depth that was actually CHOSEN is scientific configuration and stays in the digest, so setting
    one still invalidates reuse. That is correct: it changes what the models do.
    """
    if not isinstance(dumped, dict):
        return
    for key in ("thinking", "effort"):
        if dumped.get(key) == VENDOR_DEFAULT:
            dumped.pop(key, None)


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
        _drop_vendor_default_reasoning(paperbank.get("extraction", {}))
        slices = {
            "implementation_version": PAPER_HALF_IMPLEMENTATION_VERSION,
            "mode": mode,
            "paperbank": paperbank,
            "max_revise_rounds": config.run.max_revise_rounds,
        }
    elif stage == STAGE_DATASET_HALF:
        # This helper already includes the shared allow_pro_model field so it can also reproduce
        # the exact frozen v0.1 slice for the bounded rights-only compatibility migration.
        return stable_hash(
            _dataset_half_config_slice(config, include_rights_implementation_version=True)
        )
    elif stage == STAGE_C:
        slices = {
            "implementation_version": STAGE_C_IMPLEMENTATION_VERSION,
            "research_intent": config.research_intent.model_dump(mode="json"),
            "dataset_id": config.dataset.seed.dataset_id,
        }
    elif stage == STAGE_D:
        novelty = config.novelty.model_dump(mode="json")
        _drop_vendor_default_reasoning((novelty.get("web_grounding") or {}).get("scout", {}))
        slices = {
            "implementation_version": STAGE_D_IMPLEMENTATION_VERSION,
            "mode": mode,
            "novelty": novelty,
            "family_count": family_count,
            "variants_per_family": variants_per_family,
        }
    elif stage == STAGE_FRONT_LAYOUT:
        # Everything the human views render (mode/dataset/providers) — a pure-render slice. The
        # renderer itself is an input too: without the implementation version here, a corrected
        # projection could never reach a resumed run, and the only alternative would be deleting a
        # receipt by hand (never permitted). Bump it whenever a human-view projection changes.
        slices = {
            "implementation_version": FRONT_LAYOUT_IMPLEMENTATION_VERSION,
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


def _semantic_file_digest(file: Path) -> str:
    """Timestamp-free semantic digest of one output artifact (CLIM-10).

    Loadable YAML/JSON artifacts are hashed with provenance-timestamp keys stripped so a re-run
    that changed only timestamps compares equal; anything that will not parse as a mapping/list
    (opaque bytes, markdown) falls back to its byte digest — conservative: it gates as before.
    """
    try:
        loaded = load_data(file)
    except (OSError, ValueError, yaml.YAMLError):
        # Unreadable or non-YAML/JSON output → byte digest (conservative: gates as before).
        return sha256_file(file)
    if not isinstance(loaded, (dict, list)):
        return sha256_file(file)
    return semantic_hash(loaded)


def relative_semantic_output_digests(run_root: Path, paths: Sequence[Path]) -> dict[str, str]:
    """Per-output timestamp-free semantic digests, keyed like ``relative_output_digests``."""
    digests: dict[str, str] = {}
    for path in paths:
        for file in sorted(path.rglob("*") if path.is_dir() else [path]):
            if file.is_file():
                digests[file.relative_to(run_root).as_posix()] = _semantic_file_digest(file)
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


def _topic_source_table_path(paths: RunPaths) -> Path:
    return paths.root / _TOPIC_SOURCE_TABLE_RELATIVE_PATH


def _topic_rights_degradation_path(paths: RunPaths) -> Path:
    return paths.root / _TOPIC_RIGHTS_DEGRADATION_RELATIVE_PATH


_LEGACY_V01_REPAIR_FLAG = "public_fulltext_excerpt_repair:v2_export_gate"
_LEGACY_V01_REPAIR_FEATURE = "public_fulltext_excerpt_repair"
_LEGACY_V01_LOOKUP_REPAIR_FLAG = "public_lookup_repair_from_secondary_pointer"
_LEGACY_V01_LOOKUP_REPAIR_FEATURE = "public_lookup_repair"
_LEGACY_V01_BASE_RANKING_FEATURES = frozenset(
    {"relevance_score", "metadata_quality_score", "cited_by_count", "lane_count"}
)


def _current_topic_rights_migration_view(
    source_table: R5TopicEvidenceSourceTable,
) -> _TopicSourceRightsMigrationView:
    assessment = assess_fulltext_rights_degradation(source_table)
    return _TopicSourceRightsMigrationView(
        safe_source_table=source_table,
        degraded_source_record_ids=tuple(assessment.degraded_source_record_ids),
        abstract_fallback_source_record_ids=tuple(assessment.abstract_fallback_source_record_ids),
        metadata_only_source_record_ids=tuple(assessment.metadata_only_source_record_ids),
    )


def _legacy_v01_topic_rights_migration_view(
    payload: object,
) -> _TopicSourceRightsMigrationView:
    """Validate one exact historical shape and derive a non-persisted safe projection.

    The retained climate-run table predates ``fulltext_provenance``. Its five repaired excerpt
    rows can be recognized by a pair of exact v0.1 repair markers, but those markers never prove
    access rights. Their fetched passage is therefore removed in the safe projection. Independently
    retained abstract rows remain available; no text is guessed to be an abstract fallback for a
    repaired excerpt row.
    """

    legacy = _LegacyV01TopicEvidenceSourceTable.model_validate(payload)
    if not legacy.table_id.startswith(
        "r5-topic-source-table-"
    ) or not legacy.query_plan_id.startswith("r5-topic-evidence-plan-"):
        raise ValueError("legacy v0.1 topic table identifiers do not match the frozen shape")
    record_ids = [record.source_record_id for record in legacy.records]
    if not record_ids or len(record_ids) != len(set(record_ids)):
        raise ValueError("legacy v0.1 topic table requires unique records")
    computed_lane_coverage: dict[str, int] = {}
    safe_records: list[R5TopicSourceRecordEvidence] = []
    degraded_ids: list[str] = []
    for record in legacy.records:
        if (
            not record.source_record_id.startswith("topic-source-record-")
            or not record.lane_ids
            or not record.query_ids
            or not all(query_id.startswith("r5-topic-") for query_id in record.query_ids)
            or not record.title.strip()
            or not record.url.strip()
            or not record.dedupe_key.strip()
        ):
            raise ValueError("legacy v0.1 topic record identity does not match the frozen shape")
        for lane_id in record.lane_ids:
            computed_lane_coverage[lane_id] = computed_lane_coverage.get(lane_id, 0) + 1
        feature_keys = frozenset(record.ranking_features)
        allowed_features = _LEGACY_V01_BASE_RANKING_FEATURES | {
            _LEGACY_V01_REPAIR_FEATURE,
            _LEGACY_V01_LOOKUP_REPAIR_FEATURE,
        }
        if not _LEGACY_V01_BASE_RANKING_FEATURES.issubset(
            feature_keys
        ) or not feature_keys.issubset(allowed_features):
            raise ValueError("legacy v0.1 ranking features do not match the frozen shape")
        is_repaired_fulltext = record.snippet_kind == "fulltext_excerpt"
        is_lookup_repaired_abstract = (
            _LEGACY_V01_LOOKUP_REPAIR_FEATURE in feature_keys
            or _LEGACY_V01_LOOKUP_REPAIR_FLAG in record.source_quality_flags
        )
        if is_repaired_fulltext:
            if (
                record.abstract_status != "available"
                or feature_keys != _LEGACY_V01_BASE_RANKING_FEATURES | {_LEGACY_V01_REPAIR_FEATURE}
                or record.ranking_features[_LEGACY_V01_REPAIR_FEATURE] != 1.0
                or record.source_quality_flags != [_LEGACY_V01_REPAIR_FLAG]
            ):
                raise ValueError(
                    "legacy no-provenance fulltext lacks the exact frozen repair markers"
                )
        elif is_lookup_repaired_abstract:
            if (
                record.snippet_kind != "abstract"
                or record.abstract_status != "available"
                or feature_keys
                != _LEGACY_V01_BASE_RANKING_FEATURES | {_LEGACY_V01_LOOKUP_REPAIR_FEATURE}
                or record.ranking_features.get(_LEGACY_V01_LOOKUP_REPAIR_FEATURE) != 1.0
                or record.source_quality_flags != [_LEGACY_V01_LOOKUP_REPAIR_FLAG]
            ):
                raise ValueError("legacy public-lookup repair does not match the frozen shape")
        elif (
            _LEGACY_V01_REPAIR_FEATURE in feature_keys
            or _LEGACY_V01_REPAIR_FLAG in record.source_quality_flags
        ):
            raise ValueError("legacy repair markers are valid only on a fulltext excerpt")
        elif feature_keys != _LEGACY_V01_BASE_RANKING_FEATURES:
            raise ValueError("legacy ranking features contain an unpaired repair marker")
        elif record.snippet_kind == "abstract" and record.abstract_status != "available":
            raise ValueError("legacy abstract rows must have available status")
        elif record.snippet_kind == "title_only" and record.abstract_status != "metadata_only":
            raise ValueError("legacy title-only rows must have metadata-only status")

        safe_payload = record.model_dump(mode="python")
        if is_repaired_fulltext:
            degraded_ids.append(record.source_record_id)
            safe_payload.update(
                {
                    "abstract_or_snippet": "",
                    "abstract_status": TopicSourceAbstractStatus.METADATA_ONLY,
                    "snippet_kind": TopicSourceSnippetKind.METADATA,
                    "source_quality_flags": [
                        *record.source_quality_flags,
                        "fulltext_rights_unverified",
                        "legacy_fulltext_removed_from_safe_projection",
                    ],
                }
            )
        safe_records.append(R5TopicSourceRecordEvidence.model_validate(safe_payload))
    if not degraded_ids:
        raise ValueError("legacy v0.1 compatibility requires a repaired no-provenance excerpt")
    if computed_lane_coverage != legacy.lane_coverage:
        raise ValueError("legacy v0.1 lane coverage does not match its records")
    return _TopicSourceRightsMigrationView(
        safe_source_table=R5TopicEvidenceSourceTable(
            table_id=legacy.table_id,
            query_plan_id=legacy.query_plan_id,
            protocol_version=legacy.protocol_version,
            records=safe_records,
            lane_coverage=dict(legacy.lane_coverage),
            source_quality_flags=[
                *legacy.source_quality_flags,
                "legacy_v0_1_rights_safe_projection",
            ],
        ),
        degraded_source_record_ids=tuple(sorted(degraded_ids)),
        abstract_fallback_source_record_ids=(),
        metadata_only_source_record_ids=tuple(sorted(degraded_ids)),
        legacy_v0_1_shape=True,
    )


def _build_topic_rights_degradation_receipt(
    paths: RunPaths,
    source_table: _TopicSourceRightsMigrationView,
    *,
    created_at: datetime | None = None,
) -> LegacyExternalEvidenceDegradationReceipt | None:
    """Build the canonical sidecar over immutable source-table bytes, without writing either."""

    if not source_table.degraded_source_record_ids:
        return None
    source_path = _confined_external_evidence_path(
        paths,
        _TOPIC_SOURCE_TABLE_RELATIVE_PATH,
        owner_label="topic source table for rights degradation",
    )
    source_digest = sha256_file(source_path)
    identity = {
        "source_path": _TOPIC_SOURCE_TABLE_RELATIVE_PATH,
        "source_digest": source_digest,
        "affected_source_ids": source_table.degraded_source_record_ids,
    }
    values: dict[str, object] = {
        "receipt_id": f"legacy-external-evidence-{stable_hash(identity)[:16]}",
        "original_artifact_path": _TOPIC_SOURCE_TABLE_RELATIVE_PATH,
        "original_artifact_digest": source_digest,
        "affected_source_ids": source_table.degraded_source_record_ids,
        "abstract_fallback_source_ids": source_table.abstract_fallback_source_record_ids,
        "metadata_only_source_ids": source_table.metadata_only_source_record_ids,
    }
    if created_at is not None:
        values["created_at"] = created_at
    return LegacyExternalEvidenceDegradationReceipt.model_validate(values)


def _load_topic_source_table_for_rights_migration(
    paths: RunPaths,
) -> _TopicSourceRightsMigrationView:
    try:
        source_path = _confined_external_evidence_path(
            paths,
            _TOPIC_SOURCE_TABLE_RELATIVE_PATH,
            owner_label="topic source table for rights migration",
        )
        payload = load_data(source_path)
        try:
            current = R5TopicEvidenceSourceTable.model_validate(payload)
        except ValidationError:
            return _legacy_v01_topic_rights_migration_view(payload)
        return _current_topic_rights_migration_view(current)
    except (OSError, ValueError, ValidationError, YAMLError) as exc:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: legacy topic source table is missing, "
            "aliased, or invalid; refusing rights migration/reuse"
        ) from exc


def _legacy_rights_sidecar_markers(dataset_receipt: StageReceipt | None) -> list[str]:
    return [
        line.removeprefix(_LEGACY_RIGHTS_SIDECAR_DIGEST_PREFIX).strip()
        for line in (dataset_receipt.detail.splitlines() if dataset_receipt else [])
        if line.startswith(_LEGACY_RIGHTS_SIDECAR_DIGEST_PREFIX)
    ]


def _confined_external_evidence_path(
    paths: RunPaths,
    relative_path: str,
    *,
    owner_label: str,
) -> Path:
    """Resolve one persisted pointer without accepting absolute, parent, or symlink aliases."""

    candidate = Path(relative_path)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: {owner_label} violates run-root confinement"
        )
    try:
        root = paths.root.resolve(strict=True)
        pointed = paths.root / candidate
        resolved = pointed.resolve(strict=True)
    except OSError as exc:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: {owner_label} is missing or violates "
            "run-root confinement"
        ) from exc
    expected = root.joinpath(*candidate.parts)
    if (
        resolved != expected
        or not resolved.is_relative_to(root)
        or not resolved.is_file()
        or pointed.is_symlink()
    ):
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: {owner_label} violates run-root confinement "
            "(external or symlink alias)"
        )
    return resolved


def _confined_external_evidence_write_path(
    paths: RunPaths,
    relative_path: str,
    *,
    owner_label: str,
) -> Path:
    """Prepare one run-local write target without following symlinked ancestors.

    The destination may not exist yet, so the read-side helper cannot be reused directly.
    Every existing ancestor is checked before the next directory is created; the final
    destination must either be absent or be the exact regular file inside the resolved run root.
    """

    candidate = Path(relative_path)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: {owner_label} violates run-root confinement"
        )
    try:
        root = paths.root.resolve(strict=True)
        current = paths.root
        for part in candidate.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise ValueError("symlinked ancestor")
            if current.exists():
                if not current.is_dir():
                    raise ValueError("non-directory ancestor")
            else:
                current.mkdir()
            expected_current = root.joinpath(*current.relative_to(paths.root).parts)
            if current.resolve(strict=True) != expected_current:
                raise ValueError("aliased ancestor")
        destination = paths.root / candidate
        expected_destination = root.joinpath(*candidate.parts)
        if destination.is_symlink():
            raise ValueError("symlinked destination")
        if destination.exists():
            if (
                destination.resolve(strict=True) != expected_destination
                or not destination.is_file()
            ):
                raise ValueError("aliased or non-file destination")
        elif destination.parent.resolve(strict=True) != expected_destination.parent:
            raise ValueError("aliased destination parent")
    except (OSError, ValueError) as exc:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: {owner_label} violates run-root confinement "
            "(external or symlink alias)"
        ) from exc
    return destination


def _reconstructed_external_evidence_input_digest(
    source_table: R5TopicEvidenceSourceTable,
    batch: ExternalEvidenceBatchReceipt,
) -> str:
    """Recreate the pre-enrichment table that the fresh batch receipt signed.

    A successful enrichment replaces the displayed abstract/provider snippet with the bounded
    excerpt and retains the former text in explicit fallback fields.  Reversing only those
    successful, attempt-bound changes lets resume compare the batch's input digest with the real
    persisted output without discarding lawful lower-authority text.
    """

    attempts = {attempt.source_record_id: attempt for attempt in batch.attempts}
    reconstructed: list[dict[str, object]] = []
    for record in source_table.records:
        attempt = attempts.get(record.source_record_id)
        if attempt is None or attempt.status != ExternalEvidenceAttemptStatus.SUCCEEDED:
            reconstructed.append(record.model_dump(mode="json"))
            continue
        provenance = record.fulltext_provenance
        if (
            provenance is None
            or provenance.retrieval_attempt != attempt
            or not fulltext_rights_are_verified(record)
            or not record.fulltext_fallback_abstract_or_snippet.strip()
            or record.fulltext_fallback_snippet_kind is None
        ):
            raise RunArtifactCorruptionError(
                "external-evidence success is not exactly bound to the persisted source/fulltext "
                f"provenance for {record.source_record_id!r}"
            )
        reconstructed.append(
            record.model_copy(
                update={
                    "abstract_or_snippet": record.fulltext_fallback_abstract_or_snippet,
                    "snippet_kind": record.fulltext_fallback_snippet_kind,
                    "fulltext_fallback_abstract_or_snippet": "",
                    "fulltext_fallback_snippet_kind": None,
                    "fulltext_provenance": None,
                }
            ).model_dump(mode="json")
        )
    return stable_hash(reconstructed)


def validate_external_evidence_batch_binding(
    paths: RunPaths,
    *,
    dataset_output: DatasetHalfStageOutput,
    dataset_receipt: StageReceipt,
) -> list[str]:
    """Verify a fresh dataset-half batch against its table and both receipt layers.

    Migrated v0.1 outputs are the sole no-batch compatibility shape: they retain their historical
    DatasetHalfStageOutput bytes and carry one exact rights-degradation marker instead.  Every fresh
    Card-1 output must provide the canonical pointer/digest pair and a typed receipt whose complete
    target accounting closes against the persisted topic table.
    """

    pointer = dataset_output.external_evidence_batch_receipt_path
    pointer_digest = dataset_output.external_evidence_batch_receipt_digest
    markers = _legacy_rights_sidecar_markers(dataset_receipt)
    if bool(pointer) != bool(pointer_digest):
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: incomplete dataset-half external-evidence "
            "batch pointer/digest pair"
        )
    if not pointer:
        if len(markers) == 1 and markers[0]:
            return []
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: current dataset-half output lacks its "
            "external-evidence batch receipt"
        )
    if markers:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: fresh external-evidence batch conflicts "
            "with a legacy rights-migration marker"
        )
    if pointer != _EXTERNAL_EVIDENCE_BATCH_RELATIVE_PATH:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: dataset-half external-evidence batch pointer "
            "is not the canonical run-local path"
        )
    batch_path = _confined_external_evidence_path(
        paths,
        pointer,
        owner_label="dataset-half external-evidence batch receipt",
    )
    try:
        batch = load_model(batch_path, ExternalEvidenceBatchReceipt)
    except (OSError, ValueError, ValidationError, YAMLError) as exc:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: dataset-half external-evidence batch is "
            "not a valid typed receipt"
        ) from exc
    raw_digest = sha256_file(batch_path)
    canonical_digest = sha256_bytes(
        safe_dump(
            batch.model_dump(mode="json", exclude_none=True),
            sort_keys=False,
            allow_unicode=True,
        ).encode("utf-8")
    )
    if pointer_digest != raw_digest or raw_digest != canonical_digest:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: dataset-half external-evidence batch digest "
            "does not match its canonical typed bytes"
        )
    if (
        dataset_receipt.output_paths.count(pointer) != 1
        or dataset_receipt.output_digests.get(pointer) != pointer_digest
    ):
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: outer dataset-half StageReceipt does not "
            "bind the exact external-evidence batch"
        )
    if batch.operation != RetrievalOperation.TOPIC_FULLTEXT_EXCERPT:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: dataset-half batch records the wrong "
            "retrieval operation"
        )
    expected_receipt_id = (
        "external-evidence-batch-"
        + stable_hash(
            {
                "attempts": batch.attempts_digest,
                "input": batch.input_table_digest,
                "targets": sorted(batch.declared_target_ids),
            }
        )[:16]
    )
    if batch.receipt_id != expected_receipt_id:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: external-evidence batch receipt identity "
            "does not match its bound contents"
        )

    source_table = _load_topic_source_table_for_rights_migration(paths).safe_source_table
    source_ids = [record.source_record_id for record in source_table.records]
    if len(source_ids) != len(set(source_ids)):
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: persisted topic source table contains "
            "duplicate source_record_id values"
        )
    record_by_id = {record.source_record_id: record for record in source_table.records}
    batch_attempt_ids = {attempt.attempt_id for attempt in batch.attempts}
    for attempt in batch.attempts:
        record = record_by_id.get(attempt.source_record_id)
        if record is None:
            if attempt.status != ExternalEvidenceAttemptStatus.TARGET_NOT_FOUND:
                raise RunArtifactCorruptionError(
                    f"corruption in run {paths.root.name!r}: external-evidence target "
                    f"{attempt.source_record_id!r} is absent without TARGET_NOT_FOUND accounting"
                )
            continue
        if attempt.status == ExternalEvidenceAttemptStatus.TARGET_NOT_FOUND:
            raise RunArtifactCorruptionError(
                f"corruption in run {paths.root.name!r}: external-evidence target "
                f"{attempt.source_record_id!r} is present but recorded TARGET_NOT_FOUND"
            )
        if attempt.status == ExternalEvidenceAttemptStatus.SUCCEEDED:
            provenance = record.fulltext_provenance
            if (
                provenance is None
                or provenance.retrieval_attempt != attempt
                or not fulltext_rights_are_verified(record)
            ):
                raise RunArtifactCorruptionError(
                    f"corruption in run {paths.root.name!r}: successful external-evidence "
                    f"attempt for {attempt.source_record_id!r} does not match fulltext provenance"
                )
        elif attempt.status == ExternalEvidenceAttemptStatus.SKIPPED_ALREADY_FULLTEXT and (
            record.fulltext_provenance is None
        ):
            raise RunArtifactCorruptionError(
                f"corruption in run {paths.root.name!r}: SKIPPED_ALREADY_FULLTEXT target "
                f"{attempt.source_record_id!r} has no persisted fulltext provenance"
            )
    for record in source_table.records:
        provenance = record.fulltext_provenance
        if (
            provenance is not None
            and provenance.retrieval_attempt is not None
            and provenance.retrieval_attempt.attempt_id in batch_attempt_ids
        ):
            matching = next(
                attempt
                for attempt in batch.attempts
                if attempt.attempt_id == provenance.retrieval_attempt.attempt_id
            )
            if matching.status != ExternalEvidenceAttemptStatus.SUCCEEDED or matching != (
                provenance.retrieval_attempt
            ):
                raise RunArtifactCorruptionError(
                    f"corruption in run {paths.root.name!r}: persisted fulltext provenance for "
                    f"{record.source_record_id!r} conflicts with its batch attempt"
                )
    reconstructed_input_digest = _reconstructed_external_evidence_input_digest(source_table, batch)
    if reconstructed_input_digest != batch.input_table_digest:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: external-evidence batch input digest does "
            "not reconcile with the persisted topic source table"
        )

    external_stage_receipt = read_stage_receipt(paths, "fulltext_enrichment")
    if (
        external_stage_receipt is None
        or external_stage_receipt.status != StageStatus.COMPLETE
        or external_stage_receipt.output_paths != [pointer]
        or external_stage_receipt.output_digests != {pointer: pointer_digest}
    ):
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: fulltext-enrichment StageReceipt does not "
            "bind the exact external-evidence batch"
        )
    expected_external_call_ids = sorted(
        attempt.attempt_id
        for attempt in batch.attempts
        if attempt.status in _EXTERNAL_EVIDENCE_TRANSPORT_STATUSES
    )
    if (
        len(external_stage_receipt.external_call_ids)
        != len(set(external_stage_receipt.external_call_ids))
        or sorted(external_stage_receipt.external_call_ids) != expected_external_call_ids
    ):
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: fulltext-enrichment external_call_ids do "
            "not match attempts that reached transport"
        )
    return [pointer]


def validate_topic_rights_degradation_binding(
    paths: RunPaths,
    *,
    dataset_output: DatasetHalfStageOutput | None = None,
    dataset_receipt: StageReceipt | None = None,
) -> list[str]:
    """Consume and verify the canonical rights sidecar at the dataset-half reuse boundary.

    A sidecar is mandatory exactly when the immutable table contains v0.1-style unverified
    full-text records.  Its raw-file SHA, affected IDs, and abstract-vs-metadata partitions are
    recomputed from the real table.  Missing, mutated, orphaned, or source-substituted sidecars are
    corruption, never a reason to silently restore the old full-text authority or rerun providers.
    """

    source_table = _load_topic_source_table_for_rights_migration(paths)
    expected_without_time = _build_topic_rights_degradation_receipt(paths, source_table)
    sidecar_path = _topic_rights_degradation_path(paths)
    if expected_without_time is None:
        if sidecar_path.exists() or sidecar_path.is_symlink():
            raise RunArtifactCorruptionError(
                f"corruption in run {paths.root.name!r}: an orphaned topic rights-degradation "
                "sidecar exists for a source table with no degraded records"
            )
        if dataset_output is not None and (
            dataset_output.rights_degradation_receipt_path
            or dataset_output.rights_degradation_receipt_digest
        ):
            raise RunArtifactCorruptionError(
                f"corruption in run {paths.root.name!r}: dataset-half points to a rights "
                "degradation sidecar that is not warranted by its source table"
            )
        if dataset_receipt is not None and any(
            line.startswith(_LEGACY_RIGHTS_SIDECAR_DIGEST_PREFIX)
            for line in dataset_receipt.detail.splitlines()
        ):
            raise RunArtifactCorruptionError(
                f"corruption in run {paths.root.name!r}: dataset receipt claims a legacy rights "
                "sidecar for a source table with no degraded records"
            )
        return []

    try:
        sidecar_path = _confined_external_evidence_path(
            paths,
            _TOPIC_RIGHTS_DEGRADATION_RELATIVE_PATH,
            owner_label="topic rights-degradation sidecar",
        )
        persisted = load_model(sidecar_path, LegacyExternalEvidenceDegradationReceipt)
    except (OSError, ValueError, ValidationError, YAMLError) as exc:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: required topic rights-degradation sidecar "
            "is missing, aliased, or invalid; refusing reuse"
        ) from exc
    expected = _build_topic_rights_degradation_receipt(
        paths,
        source_table,
        created_at=persisted.created_at,
    )
    if expected is None or persisted != expected:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: topic rights-degradation sidecar does not "
            "match the immutable source bytes and recomputed authority partitions"
        )
    sidecar_digest = sha256_file(sidecar_path)
    canonical_bytes = safe_dump(
        persisted.model_dump(mode="json", exclude_none=True),
        sort_keys=False,
        allow_unicode=True,
    ).encode("utf-8")
    if sidecar_digest != sha256_bytes(canonical_bytes):
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: topic rights-degradation sidecar bytes "
            "were changed or produced by an unknown serializer"
        )
    if dataset_output is not None:
        pointer = dataset_output.rights_degradation_receipt_path
        pointer_digest = dataset_output.rights_degradation_receipt_digest
        if bool(pointer) != bool(pointer_digest):
            raise RunArtifactCorruptionError(
                f"corruption in run {paths.root.name!r}: incomplete dataset-half rights sidecar "
                "pointer/digest pair"
            )
        # Fresh Card-1 runs bind the sidecar in DatasetHalfStageOutput.  A migrated v0.1 output is
        # intentionally byte-preserved and therefore has neither field; the recomputed canonical
        # binding above is its compatibility authority record.
        if pointer and (
            pointer != _TOPIC_RIGHTS_DEGRADATION_RELATIVE_PATH or pointer_digest != sidecar_digest
        ):
            raise RunArtifactCorruptionError(
                f"corruption in run {paths.root.name!r}: dataset-half rights sidecar pointer or "
                "digest does not match the canonical degradation receipt"
            )
        if not pointer:
            markers = [
                line.removeprefix(_LEGACY_RIGHTS_SIDECAR_DIGEST_PREFIX).strip()
                for line in (dataset_receipt.detail.splitlines() if dataset_receipt else [])
                if line.startswith(_LEGACY_RIGHTS_SIDECAR_DIGEST_PREFIX)
            ]
            if markers != [sidecar_digest]:
                raise RunArtifactCorruptionError(
                    f"corruption in run {paths.root.name!r}: byte-preserved legacy dataset-half "
                    "output lacks the exact typed sidecar digest binding"
                )
    return [_TOPIC_RIGHTS_DEGRADATION_RELATIVE_PATH]


def _validated_legacy_stage_c_source_projection(
    paths: RunPaths,
    *,
    dataset_output: DatasetHalfStageOutput,
    dataset_receipt: StageReceipt,
) -> RightsSafeTopicSourceProjection | None:
    """Return the legacy Stage-C projection only after validating both receipt layers.

    Current-schema tables continue through Stage C's ordinary strict loader.  The exceptional
    projection exists solely for an exact no-provenance v0.1 table whose immutable bytes, degraded
    source partition, sidecar, and migrated dataset receipt all reconcile.
    """

    verified_paths = validate_topic_rights_degradation_binding(
        paths,
        dataset_output=dataset_output,
        dataset_receipt=dataset_receipt,
    )
    view = _load_topic_source_table_for_rights_migration(paths)
    if not view.legacy_v0_1_shape:
        return None
    if verified_paths != [_TOPIC_RIGHTS_DEGRADATION_RELATIVE_PATH]:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: legacy Stage-C projection lacks its "
            "validated rights-degradation sidecar"
        )
    from ..context.question_scientist_export import RightsSafeTopicSourceProjection

    return RightsSafeTopicSourceProjection(
        source_table=view.safe_source_table,
        original_semantic_digest=stable_hash(load_data(_topic_source_table_path(paths))),
        excluded_source_record_ids=view.degraded_source_record_ids,
    )


def persist_topic_rights_degradation_receipt(paths: RunPaths) -> Path | None:
    """Persist or validate the canonical non-mutating topic-rights sidecar."""

    source_path = _confined_external_evidence_path(
        paths,
        _TOPIC_SOURCE_TABLE_RELATIVE_PATH,
        owner_label="topic source table for rights migration",
    )
    original_bytes = source_path.read_bytes()
    source_table = _load_topic_source_table_for_rights_migration(paths)
    receipt = _build_topic_rights_degradation_receipt(paths, source_table)
    if receipt is None:
        return None
    sidecar_path = _confined_external_evidence_write_path(
        paths,
        _TOPIC_RIGHTS_DEGRADATION_RELATIVE_PATH,
        owner_label="topic rights-degradation sidecar write",
    )
    if sidecar_path.exists():
        validate_topic_rights_degradation_binding(paths)
    else:
        dump_data(receipt, sidecar_path)
        validate_topic_rights_degradation_binding(paths)
    if source_path.read_bytes() != original_bytes:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: persisting the rights sidecar changed "
            "immutable source-table bytes"
        )
    return sidecar_path


def migrate_legacy_dataset_half_rights(
    config: MaieusisProjectConfig,
    paths: RunPaths,
) -> Path | None:
    """Perform the one bounded, provider-free v0.1 rights migration under the run lock.

    Eligibility is deliberately exact: frozen legacy config hash, current real inputs, matching
    model/prompt identity, intact recorded outputs, and at least one known-unverified FULLTEXT record.
    Only the typed sidecar and dataset receipt's semantic config marker are written.  Source tables,
    Stage-C/D products, family artifacts, and all scientific bytes remain unchanged.
    """

    receipt = read_stage_receipt(paths, STAGE_DATASET_HALF)
    if receipt is None or receipt.status not in _REUSABLE_STATUSES:
        return None
    if receipt.config_version != legacy_dataset_half_config_version(config):
        return None
    if not model_versions_accept(
        receipt.model_versions, stage_model_versions(config, STAGE_DATASET_HALF)
    ) or receipt.prompt_versions != stage_prompt_versions(STAGE_DATASET_HALF):
        return None
    current_inputs = compute_current_input_digests(config, paths, STAGE_DATASET_HALF)
    if receipt.input_digests != current_inputs:
        return None
    _verify_output_digests(
        paths.root,
        receipt.output_digests,
        owner_label="legacy dataset-half rights migration",
    )
    dataset_output = load_model(paths.stage_output(STAGE_DATASET_HALF), DatasetHalfStageOutput)
    if (
        dataset_output.rights_degradation_receipt_path
        or dataset_output.rights_degradation_receipt_digest
    ):
        # A supposedly frozen v0.1 output cannot already contain Card-1-only pointer fields.
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: legacy dataset-half output contains a "
            "partial or anachronistic rights sidecar pointer"
        )
    source_table = _load_topic_source_table_for_rights_migration(paths)
    if _build_topic_rights_degradation_receipt(paths, source_table) is None:
        # The rights semantic revision may still require a normal dataset-half rerun; the special
        # no-call path exists only for the known-wrong authority shape it can safely lower.
        return None
    sidecar_path = persist_topic_rights_degradation_receipt(paths)
    if sidecar_path is None:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: eligible rights migration did not persist "
            "its required sidecar"
        )
    sidecar_digest = sha256_file(sidecar_path)
    detail_lines = receipt.detail.splitlines()
    old_markers = [
        line for line in detail_lines if line.startswith(_LEGACY_RIGHTS_SIDECAR_DIGEST_PREFIX)
    ]
    if old_markers:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: frozen legacy dataset receipt already "
            "contains an unexpected rights-sidecar digest marker"
        )
    migrated_detail = "\n".join(
        [
            *detail_lines,
            f"{_LEGACY_RIGHTS_SIDECAR_DIGEST_PREFIX}{sidecar_digest}",
        ]
    ).strip()
    migrated_output_digests = {
        **receipt.output_digests,
        _TOPIC_RIGHTS_DEGRADATION_RELATIVE_PATH: sidecar_digest,
    }
    write_stage_receipt(
        paths,
        receipt.model_copy(
            update={
                "config_version": stage_config_version(config, STAGE_DATASET_HALF),
                "detail": migrated_detail,
                "output_paths": sorted(migrated_output_digests),
                "output_digests": dict(sorted(migrated_output_digests.items())),
            }
        ),
    )
    return sidecar_path


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


_NOVELTY_WEB_JOURNAL_RELATIVE_ROOT = Path("receipts") / "novelty-web"


def _verify_stage_d_novelty_web_bindings(paths: RunPaths) -> list[str]:
    """Verify N-2's retained journal without constructing a provider or re-searching.

    Stage D deliberately retains this small receipt tree across ordinary corpus cleanup.  Reuse is
    safe only when every persisted web reference binds its family/variant/question and every
    resolved canonical record exactly matches its one bounded Crossref reconciliation snapshot.
    This verifier is read-only: a missing, swapped, malformed, or symlinked artifact is corruption,
    never permission to make another web request.
    """

    reservations = _load_novelty_web_models(paths, "reservations", NoveltyWebSearchReservation)
    completed = _load_novelty_web_models(paths, "completed", NoveltyWebSearchReceipt)
    resolution_reservations = _load_novelty_web_models(
        paths, "resolution-reservations", NoveltyWebLeadResolutionReservation
    )
    resolutions = _load_novelty_web_models(paths, "resolutions", NoveltyWebLeadResolution)

    reservations_by_id = {item.reservation_id: item for _path, item in reservations}
    receipts_by_id = {item.receipt_id: item for _path, item in completed}
    resolution_reservations_by_id = {
        item.reservation_id: item for _path, item in resolution_reservations
    }
    resolution_reservations_by_resolution_id = {
        item.resolution_id: item for _path, item in resolution_reservations
    }
    resolutions_by_id = {item.resolution_id: item for _path, item in resolutions}
    if len(reservations_by_id) != len(reservations):
        _n2_corruption(paths, "duplicate novelty-web reservation identities")
    if len(receipts_by_id) != len(completed):
        _n2_corruption(paths, "duplicate novelty-web completed receipt identities")
    if len(resolution_reservations_by_id) != len(resolution_reservations):
        _n2_corruption(paths, "duplicate novelty-web reconciliation reservation identities")
    if len(resolution_reservations_by_resolution_id) != len(resolution_reservations):
        _n2_corruption(paths, "multiple reconciliation reservations target one web lead")
    if len(resolutions_by_id) != len(resolutions):
        _n2_corruption(paths, "duplicate novelty-web resolution identities")

    for completed_path, receipt in completed:
        if completed_path.stem != receipt.reservation_id:
            _n2_corruption(
                paths, "novelty-web completed receipt filename does not bind reservation"
            )
        reservation = reservations_by_id.get(receipt.reservation_id)
        if reservation is None:
            _n2_corruption(paths, "novelty-web completed receipt has no pre-call reservation")
        _verify_novelty_web_receipt_reservation_pair(paths, receipt, reservation)

    for reservation_path, reservation_entry in resolution_reservations:
        if reservation_path.stem != reservation_entry.reservation_id:
            _n2_corruption(
                paths,
                "novelty-web reconciliation reservation filename does not bind its identity",
            )
        bound_receipt = receipts_by_id.get(reservation_entry.receipt_id)
        if bound_receipt is None:
            _n2_corruption(
                paths,
                "novelty-web reconciliation reservation has no completed search receipt",
            )
        if reservation_entry.lead_id not in {lead.lead_id for lead in bound_receipt.leads}:
            _n2_corruption(
                paths,
                "novelty-web reconciliation reservation references a lead outside its receipt",
            )

    for resolution_path, resolution in resolutions:
        if resolution_path.stem != resolution.resolution_id:
            _n2_corruption(paths, "novelty-web resolution filename does not bind its identity")
        bound_receipt = receipts_by_id.get(resolution.receipt_id)
        if bound_receipt is None:
            _n2_corruption(paths, "novelty-web resolution has no completed search receipt")
        if resolution.lead_id not in {lead.lead_id for lead in bound_receipt.leads}:
            _n2_corruption(paths, "novelty-web resolution references a lead outside its receipt")
        reconciliation_reservation = resolution_reservations_by_resolution_id.get(
            resolution.resolution_id
        )
        if reconciliation_reservation is None:
            _n2_corruption(
                paths, "novelty-web resolution has no pre-call reconciliation reservation"
            )
        if (
            reconciliation_reservation.receipt_id != resolution.receipt_id
            or reconciliation_reservation.lead_id != resolution.lead_id
        ):
            _n2_corruption(
                paths, "novelty-web resolution does not bind its reconciliation reservation"
            )
        if resolution.status != NoveltyWebLeadResolutionStatus.UNAVAILABLE and (
            reconciliation_reservation.method != resolution.method
            or reconciliation_reservation.deterministic_provider_id
            != resolution.deterministic_provider_id
            or reconciliation_reservation.deterministic_query_digest
            != resolution.deterministic_query_digest
        ):
            _n2_corruption(
                paths,
                "novelty-web resolution route does not match its pre-call reconciliation reservation",
            )

    evidence_packs = _load_stage_d_novelty_models(paths, "evidence", NoveltyEvidencePack)
    evidence_by_id = {item.evidence_pack_id: item for _path, item in evidence_packs}
    if len(evidence_by_id) != len(evidence_packs):
        _n2_corruption(paths, "duplicate Stage-D novelty evidence-pack identities")
    for _path, evidence in evidence_packs:
        _verify_novelty_web_evidence_pack(
            paths,
            evidence,
            receipts_by_id=receipts_by_id,
            resolutions_by_id=resolutions_by_id,
        )

    assessments = _load_stage_d_novelty_models(paths, "assessments", VariantNoveltyAssessment)
    for _path, assessment in assessments:
        bound_evidence = evidence_by_id.get(assessment.evidence_pack_id)
        if bound_evidence is None:
            _n2_corruption(paths, "novelty assessment refers to a missing evidence pack")
        if set(assessment.web_receipt_ids) != set(bound_evidence.web_receipt_ids) or set(
            assessment.web_resolution_ids
        ) != set(bound_evidence.web_resolution_ids):
            _n2_corruption(
                paths,
                "novelty assessment web receipt/resolution links do not match its evidence pack",
            )

    return sorted(
        [
            path.relative_to(paths.root).as_posix()
            for path, _item in [
                *reservations,
                *completed,
                *resolution_reservations,
                *resolutions,
            ]
        ]
    )


def _load_novelty_web_models(
    paths: RunPaths,
    subdirectory: str,
    model_type: type[_N2Model],
) -> list[tuple[Path, _N2Model]]:
    """Load every controlled N-2 journal YAML only from a confined regular-file directory."""

    directory = _novelty_web_confined_directory(paths, subdirectory)
    if directory is None:
        return []
    loaded: list[tuple[Path, _N2Model]] = []
    for candidate in sorted(directory.iterdir()):
        if candidate.suffix != ".yaml" or candidate.is_symlink() or not candidate.is_file():
            _n2_corruption(paths, "novelty-web journal contains a non-regular YAML artifact")
        try:
            resolved = candidate.resolve(strict=True)
            if not resolved.is_relative_to(directory):
                _n2_corruption(paths, "novelty-web journal artifact escapes its directory")
            model = load_model(candidate, model_type)
        except (OSError, ValueError, ValidationError, YAMLError) as exc:
            raise RunArtifactCorruptionError(
                f"corruption in run {paths.root.name!r}: novelty-web {subdirectory} artifact "
                "is not a valid typed receipt"
            ) from exc
        loaded.append((candidate, model))
    return loaded


def _load_stage_d_novelty_models(
    paths: RunPaths,
    leaf_directory: str,
    model_type: type[_N2Model],
) -> list[tuple[Path, _N2Model]]:
    """Read normal Stage-D novelty outputs while refusing symlink traversal outside the run."""

    root = paths.corpus / "question_families" / "novelty"
    if not root.exists():
        return []
    if root.is_symlink() or not root.is_dir():
        _n2_corruption(paths, "Stage-D novelty output root is not a real directory")
    run_root = paths.root.resolve(strict=True)
    loaded: list[tuple[Path, _N2Model]] = []
    for candidate in sorted(root.rglob(f"{leaf_directory}/*.yaml")):
        if candidate.is_symlink() or not candidate.is_file():
            _n2_corruption(paths, "Stage-D novelty output contains a non-regular artifact")
        try:
            resolved = candidate.resolve(strict=True)
            if not resolved.is_relative_to(run_root):
                _n2_corruption(paths, "Stage-D novelty artifact escapes the run root")
            model = load_model(candidate, model_type)
        except (OSError, ValueError, ValidationError, YAMLError) as exc:
            raise RunArtifactCorruptionError(
                f"corruption in run {paths.root.name!r}: Stage-D novelty {leaf_directory} "
                "artifact is not a valid typed model"
            ) from exc
        loaded.append((candidate, model))
    return loaded


def _novelty_web_confined_directory(paths: RunPaths, subdirectory: str) -> Path | None:
    if Path(subdirectory).name != subdirectory:
        _n2_corruption(paths, "invalid novelty-web journal directory identifier")
    directory = paths.root / _NOVELTY_WEB_JOURNAL_RELATIVE_ROOT / subdirectory
    if not directory.exists():
        return None
    if directory.is_symlink() or not directory.is_dir():
        _n2_corruption(paths, "novelty-web journal directory is not a real directory")
    try:
        run_root = paths.root.resolve(strict=True)
        resolved = directory.resolve(strict=True)
    except OSError as exc:
        raise RunArtifactCorruptionError(
            f"corruption in run {paths.root.name!r}: novelty-web journal directory cannot be read"
        ) from exc
    if not resolved.is_relative_to(run_root):
        _n2_corruption(paths, "novelty-web journal directory escapes the run root")
    return resolved


def _verify_novelty_web_receipt_reservation_pair(
    paths: RunPaths,
    receipt: NoveltyWebSearchReceipt,
    reservation: NoveltyWebSearchReservation,
) -> None:
    fields = (
        "run_id",
        "question_family_id",
        "variant_id",
        "question_seed_id",
        "question_digest",
        "candidate_input_digest",
        "request_digest",
        "config_digest",
        "prompt_version",
        "prompt_digest",
        "provider_id",
        "model_id",
        "rate_card",
        "tool_rate_micro_usd",
        "reserved_web_tool_uses",
    )
    if any(getattr(receipt, field) != getattr(reservation, field) for field in fields):
        _n2_corruption(paths, "novelty-web receipt does not match its immutable reservation")
    if receipt.requested_at != reservation.reserved_at:
        _n2_corruption(paths, "novelty-web receipt request time does not match its reservation")


def _verify_novelty_web_evidence_pack(
    paths: RunPaths,
    evidence: NoveltyEvidencePack,
    *,
    receipts_by_id: dict[str, NoveltyWebSearchReceipt],
    resolutions_by_id: dict[str, NoveltyWebLeadResolution],
) -> None:
    for receipt_id in evidence.web_receipt_ids:
        receipt = receipts_by_id.get(receipt_id)
        if receipt is None:
            _n2_corruption(paths, "novelty evidence pack refers to a missing web receipt")
        if (
            receipt.question_family_id != evidence.question_family_id
            or receipt.variant_id != evidence.variant_id
            or receipt.question_seed_id != evidence.question_seed_id
            or receipt.question_digest != evidence.question_digest
        ):
            _n2_corruption(
                paths, "novelty web receipt is swapped across family, variant, or question"
            )
    for resolution_id in evidence.web_resolution_ids:
        resolution = resolutions_by_id.get(resolution_id)
        if resolution is None:
            _n2_corruption(paths, "novelty evidence pack refers to a missing web resolution")
        if resolution.receipt_id not in evidence.web_receipt_ids:
            _n2_corruption(
                paths, "novelty web resolution is not bound to the evidence-pack receipt"
            )
    for prior in evidence.priors:
        if prior.evidence_origin != NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED:
            continue
        if (
            prior.web_receipt_id not in evidence.web_receipt_ids
            or prior.web_resolution_id not in evidence.web_resolution_ids
        ):
            _n2_corruption(paths, "web-resolved prior has no evidence-pack receipt chain")
        resolution = resolutions_by_id.get(prior.web_resolution_id)
        if (
            resolution is None
            or resolution.canonical_prior is None
            or resolution.canonical_prior.model_dump(mode="json") != prior.model_dump(mode="json")
        ):
            _n2_corruption(
                paths, "web-resolved prior does not match its immutable resolution snapshot"
            )


def _n2_corruption(paths: RunPaths, detail: str) -> NoReturn:
    raise RunArtifactCorruptionError(f"corruption in run {paths.root.name!r}: {detail}")


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
def shortlist_context_digest(manifest: QuestionFamilyShortlistManifest) -> str:
    """The shared proposal context every family in a batch was planned against.

    Deliberately NOT a hash of the whole manifest. Which siblings were shortlisted beside a family
    does not change what that family's plan means, and treating it as if it did is what made a
    transient connection drop unrecoverable on 2026-08-14: rescuing one family would have
    invalidated four accepted plans and a reject that were already earned and paid for.
    """

    return stable_hash(
        {
            "shortlist_id": manifest.shortlist_id,
            "pack_id": manifest.pack_id,
            "context_id": manifest.context_id,
            "context_digest": manifest.context_digest,
            "authority_ceiling": str(getattr(manifest.authority_ceiling, "value", "")),
        }
    )


def shortlist_entry_digest(manifest: QuestionFamilyShortlistManifest, family_id: str) -> str:
    """A digest over ONE family's shortlist entry, or its bucket when it is not shortlisted.

    A family whose own entry changed must still lose its terminal — the narrower binding is not a
    free pass. A family that has no entry (it sits in `run_incomplete`, say) digests its bucket, so
    moving between buckets invalidates it exactly as a content change would.
    """

    for shortlisted in manifest.shortlisted:
        if shortlisted.family.question_family_id == family_id:
            return stable_hash(shortlisted.model_dump(mode="json"))
    for bucket, ids in (
        ("rejected", manifest.rejected_family_ids),
        ("needs_revision", manifest.needs_revision_family_ids),
        ("deferred", manifest.deferred_family_ids),
        ("run_incomplete", manifest.run_incomplete_family_ids),
    ):
        if family_id in ids:
            return stable_hash({"bucket": bucket, "question_family_id": family_id})
    return stable_hash({"bucket": "absent", "question_family_id": family_id})


def family_slug_map(manifest: QuestionFamilyShortlistManifest) -> dict[str, str]:
    """The DETERMINISTIC family-id → layout-slug map (sorted ids; identical at write and resume)."""
    all_ids = sorted(
        {sf.family.question_family_id for sf in manifest.shortlisted}
        | set(manifest.rejected_family_ids)
        | set(manifest.needs_revision_family_ids)
        | set(manifest.deferred_family_ids)
        | set(manifest.run_incomplete_family_ids)
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
    context_digest = shortlist_context_digest(manifest)
    slugs = family_slug_map(manifest)
    completed: list[FamilyCompletionRecord] = []
    decisions: list[FamilyResumeDecision] = []
    # The `run_incomplete` bucket is visited too. It holds families whose shortlist review was
    # stopped by an infrastructure fault -- nothing scientific was decided about them -- and before
    # 2026-08-14 this loop read `manifest.shortlisted` alone, so they were unreachable by any resume
    # and one dropped connection cost a family permanently. They have no completion record, so they
    # fall through to RECORD_MISSING below and are re-reviewed.
    family_ids = [sf.family.question_family_id for sf in manifest.shortlisted] + [
        family_id
        for family_id in manifest.run_incomplete_family_ids
        if family_id not in {sf.family.question_family_id for sf in manifest.shortlisted}
    ]
    for family_id in family_ids:
        slug = slugs[family_id]
        entry_digest = shortlist_entry_digest(manifest, family_id)
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
        try:
            record = load_model(record_path, FamilyCompletionRecord)
        except (OSError, ValueError, ValidationError, YAMLError):
            # A record this reader cannot parse is not a reusable terminal, and it must not stop the
            # resume either. Splitting `shortlist_digest` into a context digest and an entry digest
            # made every record written before that change unreadable, and without this branch the
            # first resume over such a run died inside `load_model` instead of re-running the
            # family. Caught against a real leg's artifacts; the unit fixtures all carried new
            # records and saw nothing.
            decisions.append(
                FamilyResumeDecision(
                    question_family_id=family_id,
                    slug=slug,
                    decision=StageResumeDecisionKind.RUN,
                    reason=FamilyResumeReason.RECORD_MISSING,
                )
            )
            continue
        if (
            record.shortlist_context_digest != context_digest
            or record.shortlist_entry_digest != entry_digest
        ):
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

    context_digest = shortlist_context_digest(manifest)
    slugs = family_slug_map(manifest)
    outcomes: list[FamilyRunOutcome] = []
    infrastructure_incomplete = False
    # `run_incomplete` families are counted here too: a family the shortlist gate could not review
    # is precisely an infrastructure-incomplete run, and reading only `shortlisted` let the
    # finalizer miss the one family that made the run incomplete in the first place.
    shortlisted_ids = {sf.family.question_family_id for sf in manifest.shortlisted}
    for family_id in [sf.family.question_family_id for sf in manifest.shortlisted] + [
        fid for fid in manifest.run_incomplete_family_ids if fid not in shortlisted_ids
    ]:
        record_path = paths.family_completion(slugs[family_id])
        if not record_path.is_file():
            infrastructure_incomplete = True
            continue
        try:
            record = load_model(record_path, FamilyCompletionRecord)
        except (OSError, ValueError, ValidationError, YAMLError):
            infrastructure_incomplete = True
            continue
        if record.shortlist_context_digest != context_digest or (
            record.shortlist_entry_digest != shortlist_entry_digest(manifest, family_id)
        ):
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
        return sum(
            1 for d in self.stage_decisions.values() if d.decision == StageResumeDecisionKind.RUN
        )

    @property
    def terminal_not_applicable_count(self) -> int:
        return sum(
            1
            for d in self.stage_decisions.values()
            if d.decision == StageResumeDecisionKind.TERMINAL_NOT_APPLICABLE
        )

    @property
    def reused_scientific_terminal_stage(self) -> str | None:
        return next(
            (
                stage
                for stage in STAGE_ORDER
                if self.stage_decisions[stage].decision == StageResumeDecisionKind.REUSE
                and self.stage_decisions[stage].receipt_status
                == StageStatus.SCIENTIFIC_TERMINAL.value
            ),
            None,
        )

    @property
    def all_stages_reused(self) -> bool:
        """No stage will execute; terminal-barrier stages may be explicitly not applicable."""
        return self.rerun_stage_count == 0

    @property
    def presentation_only(self) -> bool:
        return (
            self.all_stages_reused
            and self.reused_scientific_terminal_stage is None
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


def _terminal_not_applicable_decision(
    stage: str,
    *,
    receipt: StageReceipt | None,
    terminal_upstreams: Sequence[str],
) -> StageResumeDecision:
    return StageResumeDecision(
        stage_name=stage,
        decision=StageResumeDecisionKind.TERMINAL_NOT_APPLICABLE,
        reason=StageRunReason.UPSTREAM_SCIENTIFIC_TERMINAL,
        receipt_status=receipt.status.value if receipt else "missing",
        changed_input_keys=list(terminal_upstreams),
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
        terminal_upstreams = [
            upstream
            for upstream in STAGE_UPSTREAM[stage]
            if decisions[upstream].decision == StageResumeDecisionKind.TERMINAL_NOT_APPLICABLE
            or (
                decisions[upstream].decision == StageResumeDecisionKind.REUSE
                and decisions[upstream].receipt_status == StageStatus.SCIENTIFIC_TERMINAL.value
            )
        ]
        if terminal_upstreams:
            decisions[stage] = _terminal_not_applicable_decision(
                stage,
                receipt=receipt,
                terminal_upstreams=terminal_upstreams,
            )
            continue
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
        expected_prompts = stage_prompt_versions(stage, config=config)
        if (
            receipt.config_version != expected_config
            or not model_versions_accept(receipt.model_versions, expected_models)
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
        if stage == STAGE_DATASET_HALF and receipt.status == StageStatus.COMPLETE:
            dataset_output = load_model(
                paths.stage_output(STAGE_DATASET_HALF), DatasetHalfStageOutput
            )
            for relative_path in validate_external_evidence_batch_binding(
                paths,
                dataset_output=dataset_output,
                dataset_receipt=receipt,
            ):
                if relative_path not in verified:
                    verified.append(relative_path)
            for relative_path in validate_topic_rights_degradation_binding(
                paths,
                dataset_output=dataset_output,
                dataset_receipt=receipt,
            ):
                if relative_path not in verified:
                    verified.append(relative_path)
        if stage == STAGE_D:
            for relative_path in _verify_stage_d_outcome_binding(paths):
                if relative_path not in verified:
                    verified.append(relative_path)
            for relative_path in _verify_stage_d_novelty_web_bindings(paths):
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
        manifest.diagnostics = [
            diagnostic
            for diagnostic in manifest.diagnostics
            if diagnostic.code not in {"paper_half_terminal", "no_reviewed_question_patterns"}
        ]
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
    note = (
        f"This run was resumed: {plan.reused_stage_count} stage(s) reused, "
        f"{plan.rerun_stage_count} stage(s) re-run."
    )
    if plan.terminal_not_applicable_count:
        note += (
            f" {plan.terminal_not_applicable_count} downstream stage(s) were not applicable "
            "after a reused scientific terminal."
        )
    return note


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
    from ...providers.scientific_agents import (
        ScientificAgentInfrastructureError,
        ScientificAgentSessionError,
    )
    from ..agents.question_scientist_family import NoValidFamilies, StageDPromptBudgetError
    from .end_to_end import (
        DatasetContextTerminalError,
        QuestionScientistContextReadinessError,
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
        maybe_terminalize_stage_receipt,
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
        # Card-1 compatibility: an exact v0.1 false-OA dataset half can be made safe without
        # deleting its source table or constructing any provider.  The bounded migration writes
        # only a typed authority-degradation sidecar and advances the dataset receipt's semantic
        # marker; plan_resume then consumes and verifies that sidecar like every current receipt.
        migrate_legacy_dataset_half_rights(config, paths)
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

        reused_terminal_stage = plan.reused_scientific_terminal_stage
        if reused_terminal_stage is not None:
            terminal_receipt = read_stage_receipt(paths, reused_terminal_stage)
            if (
                terminal_receipt is None
                or terminal_receipt.status != StageStatus.SCIENTIFIC_TERMINAL
                or terminal_receipt.failure_class != FailureClass.SCIENTIFIC
            ):
                raise RunArtifactCorruptionError(
                    "resume plan named a scientific terminal without its bound scientific receipt"
                )
            write_run_terminal_summary(
                paths,
                RunTerminal(
                    failed_stage=reused_terminal_stage,
                    failed_stage_receipt_id=reused_terminal_stage,
                    failure_class=FailureClass.SCIENTIFIC,
                    reason=terminal_receipt.detail,
                ),
                resume_note=note,
            )
            return ResumeExecutionResult(summary=paths.summary, plan=plan)

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

        stage_c_source_projection: RightsSafeTopicSourceProjection | None = None
        if must_run(STAGE_C) and not must_run(STAGE_DATASET_HALF):
            dataset_receipt = read_stage_receipt(paths, STAGE_DATASET_HALF)
            if dataset_receipt is None or dataset_receipt.status != StageStatus.COMPLETE:
                raise RunArtifactCorruptionError(
                    f"corruption in run {paths.root.name!r}: Stage C cannot reuse a missing or "
                    "non-complete dataset-half receipt"
                )
            dataset_output = load_model(
                paths.stage_output(STAGE_DATASET_HALF), DatasetHalfStageOutput
            )
            stage_c_source_projection = _validated_legacy_stage_c_source_projection(
                paths,
                dataset_output=dataset_output,
                dataset_receipt=dataset_receipt,
            )

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
                        resume=True,
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
        terminal_result = maybe_terminalize_stage_receipt(
            paths,
            run_id=run_id,
            stage=STAGE_PAPER_HALF,
            resume_note=note,
        )
        if terminal_result is not None:
            return ResumeExecutionResult(summary=paths.summary, plan=plan)
        # Mirror the fresh-run typed terminal on resume: scientific non-accept stays scientific;
        # provider/schema/config failures stay infrastructure. Both stop before downstream stages.
        if must_run(STAGE_DATASET_HALF):
            try:
                exec_stage_dataset_half(
                    config,
                    resolved_executor,  # type: ignore[arg-type]
                    paths,
                    topic_source_table=topic_source_table,
                    topic_r5_source_table=topic_r5_source_table,
                )
            except (
                DatasetContextTerminalError,
                ModelConfigurationError,
                ScientificAgentInfrastructureError,
                ScientificAgentSessionError,
                StructuredModelProviderError,
                ValueError,
                ValidationError,
            ) as exc:
                _dataset_context_run_terminal(
                    config, paths, run_id, exc, stage=STAGE_DATASET_HALF, resume_note=note
                )
                return ResumeExecutionResult(summary=paths.summary, plan=plan)
        if must_run(STAGE_C):
            try:
                exec_stage_c(
                    config,
                    paths,
                    rights_safe_topic_source_projection=stage_c_source_projection,
                )
            except QuestionScientistContextReadinessError as exc:
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
                ScientificAgentSessionError,
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
    from ...providers.models.base import StructuredModelProviderError
    from ...providers.scientific_agents import (
        ScientificAgentInfrastructureError,
        ScientificAgentSessionError,
    )
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
        retire_current_run_diagnostics,
        set_run_state,
    )

    paths = RunPaths(root=Path(config.run.output_root) / run_id)
    if not paths.root.is_dir() or not any(paths.root.iterdir()):
        raise ValueError(
            f"run {run_id!r} not found at {paths.root} — nothing to resume (start with 'maieusis run')"
        )
    try:
        manifest = load_run_manifest(paths, allow_missing_receipts=True)
    except ValueError as exc:
        # CLIM-13: a post-promotion artifact mutation must be REJECTED honestly — persist the
        # INTEGRITY terminal (FAILED state + sanitized diagnostics) instead of dying with a bare
        # traceback that only a manual off-product reindex could clear. Mutated bytes never
        # regain authority; resume refuses to proceed.
        from .run_envelope import record_detected_integrity_failure

        mismatched = record_detected_integrity_failure(paths)
        if not mismatched:
            raise
        raise ValueError(
            "resume refused: indexed artifacts were mutated after promotion "
            f"({', '.join(mismatched)}); the run is recorded as an honest INTEGRITY failure and "
            "the mutated bytes hold no authority"
        ) from exc
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
    except Exception as exc:
        provider_failure = isinstance(
            exc,
            (
                ScientificAgentInfrastructureError,
                ScientificAgentSessionError,
                StructuredModelProviderError,
            ),
        )
        kind = getattr(getattr(exc, "kind", None), "value", "")
        record_run_failure(
            context,
            code=(
                f"provider_{kind}"
                if provider_failure and kind
                else ("provider_infrastructure_failure" if provider_failure else "resume_exception")
            ),
            diagnostic_class=(
                DiagnosticClass.INFRASTRUCTURE
                if provider_failure
                else DiagnosticClass.PROGRAMMER_FAULT
            ),
            public_message=(
                "A required provider could not complete resume; previous validated products remain current."
                if provider_failure
                else "Resume stopped before replacement completed; previous validated products remain current."
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
    # The resumed summary may replace an indexed presentation artifact. Refresh that index before
    # loading the manifest to retire stale run-level failures, otherwise integrity validation sees
    # the intentionally replaced summary bytes as corruption.
    retire_current_run_diagnostics(
        context,
        codes=(
            "run_exception",
            "resume_exception",
            "provider_infrastructure_failure",
            "provider_account_exhausted",
            "provider_authentication",
            "provider_rate_limit",
            "provider_timeout",
            "provider_connection",
            "provider_server_error",
        ),
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
    shared_scientific_terminal = False
    shared_incomplete = False
    shared_projection_degraded = False
    for stage in post_run.stages:
        if stage.processing_state == ProductProcessingState.DEGRADED:
            shared_projection_degraded = True
            receipt = read_stage_receipt(paths, stage.stage.value)
            if receipt is not None and receipt.status == StageStatus.SCIENTIFIC_TERMINAL:
                shared_scientific_terminal = True
            else:
                shared_incomplete = True
        elif stage.processing_state == ProductProcessingState.FAILED:
            shared_incomplete = True
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
    if summary.is_file() and (shared_projection_degraded or family_projection_degraded):
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
            "Read the shared scientific-terminal summary and its linked diagnostics; no "
            "downstream dossier stage was applicable."
            if shared_scientific_terminal and not infrastructure_incomplete
            else (
                "Read the available family dossiers and terminal summary; inspect any degraded "
                "family separately."
                if family_projection_degraded
                else "Read the family dossiers and terminal summary; downstream authorization "
                "remains separate."
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
        shortlist_reason_by_family,
    )
    from .run_layout import write_run_summary

    manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
    completed, _ = discover_family_completions(paths, manifest)
    outcomes = [record.family_run_outcome for record in completed]
    # A resumed run must render the same reason a fresh run does, or `resume` would silently strip
    # it back out of summary.md — the third call site, and the one easiest to miss.
    non_included_reasons = shortlist_reason_by_family(paths)
    for bucket, axis in _SHORTLIST_BUCKET_AXIS.items():
        for family_id in getattr(manifest, f"{bucket}_family_ids"):
            outcomes.append(
                non_included_family_outcome(
                    family_id,
                    shortlist_axis=axis,
                    reason=non_included_reasons.get(family_id, ""),
                )
            )

    paper_out = load_model(paths.stage_output(STAGE_PAPER_HALF), PaperHalfStageOutput)
    dataset_out = load_model(paths.stage_output(STAGE_DATASET_HALF), DatasetHalfStageOutput)
    development_surrogate = is_development_surrogate(
        config,
        front_half_receipts=[*paper_out.receipts, *dataset_out.receipts],
        dossier_statuses=[record.dossier_record.status for record in completed],
    )
    payload = load_model(find_payload_path(paths), QuestionScientistContextPayloadV2)
    basis_by_family = evidence_basis_by_family(payload, [sf.family for sf in manifest.shortlisted])
    planning_family_ids = {record.question_family_id for record in completed}
    abstract_only = sum(
        1
        for family_id in planning_family_ids
        if basis_by_family.get(family_id) == EvidenceBasis.ABSTRACT_ONLY
    )
    return write_run_summary(
        paths,
        outcomes,
        development_surrogate=development_surrogate,
        authority_ceiling=manifest.authority_ceiling,
        # A resumed run must render the same banner a fresh run does. The manifest carries the
        # ceiling but not its reason; the dataset half already loaded above carries the reason.
        ceiling_reason=dataset_out.ceiling_reason,
        evidence_basis_line=summary_evidence_basis_line(abstract_only, len(planning_family_ids)),
        resume_note=resume_note,
    )
