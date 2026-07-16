"""The `maieusis run` end-to-end driver.

One command runs the whole chain and produces the fixed ``runs/<id>/`` layout: per-included-family
end-user dossiers + a ``summary.md`` over ALL outcomes, ZERO human import.

Since 5c-1c every stage boundary emits a real ``StageReceipt`` (input digests, config/model slices,
output paths+digests) and persists a small typed stage-output summary, so `maieusis resume <run-id>`
(``orchestration/resume.py``) can REUSE completed-with-identical-inputs stages and re-run the rest.
The stage functions after stage D consume ONLY persisted artifacts (never in-memory carryover), so the
fresh path and the resume path execute identically. There is still no journal and no exactly-once: a
stage without a COMPLETE receipt simply re-runs.

Every provider/host/session is built ONLY through the ``StageExecutor`` seam (F6) — so the demo
zero-paid spy is clean (DP-7) and a fully-reused resume can prove ZERO provider constructions.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import functools
import os
import shutil
import threading
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic import TypeAdapter, ValidationError

from ...io import dump_data, load_data, load_model
from ...provenance import sha256_file, stable_hash
from ...providers.coding_agents.planner_host import CodingAgentPlannerHost
from ...providers.models.base import (
    ModelConfigurationError,
    StructuredModelFailureKind,
    StructuredModelProvider,
    StructuredModelProviderError,
)
from ...providers.models.factory import build_model_provider
from ...providers.models.web_search_provider import WebSearchModelProvider
from ...providers.scientific_agents import (
    ScientificAgentFailureKind,
    ScientificAgentInfrastructureError,
    ScientificAgentProvider,
    ScientificAgentSession,
    ScientificAgentSessionError,
)
from ...schemas.cited_literature import (
    CitationSelectionStatus,
    PaperLocalLiteratureContext,
    literature_context_digest,
)
from ...schemas.dataset_narrative import DatasetNarrative
from ...schemas.dataset_seed import DatasetSeed
from ...schemas.family_failure import (
    MAX_INTERNAL_FAMILY_FAILURE_TEXT,
    BackHalfFailureDiagnostic,
    BackHalfLineage,
    sanitize_family_failure_text,
)
from ...schemas.front_half_authority import FrontHalfAuthorityCeiling
from ...schemas.gate_outcome import (
    GateDecision,
    GateOutcome,
    PromotionReceipt,
    ReviewerExecutionKind,
)
from ...schemas.inferred_research_scope import ResolvedResearchScope
from ...schemas.maieusis_project_config import MaieusisProjectConfig
from ...schemas.multi_family_dossier import (
    DEVELOPMENT_SURROGATE_STATUSES,
    FamilyDossierStatus,
    ReviewAuthority,
)
from ...schemas.paper_case import PaperCase
from ...schemas.planner_run import CodingAgentRunRecord
from ...schemas.question_family import (
    QuestionFamily,
    QuestionFamilyBatch,
    QuestionFamilyShortlistManifest,
)
from ...schemas.question_pattern import (
    QuestionFormationTrace,
    QuestionPatternBankManifest,
    QuestionPatternCard,
)
from ...schemas.question_scientist_context_v2 import (
    EvidenceBasis,
    QuestionScientistContextPayloadV2,
)
from ...schemas.research_intent import ResearchIntent
from ...schemas.resume import FamilyCompletionRecord
from ...schemas.run_manifest import (
    ArtifactAuthority,
    ArtifactKind,
    ArtifactRecord,
    DiagnosticClass,
    FamilyDisposition,
    FamilyShortlistDisposition,
    PaperDisposition,
    PaperDispositionKind,
    ProductProcessingState,
    RunProcessingState,
    RunStage,
)
from ...schemas.run_outcome import (
    DossierAxis,
    FamilyRunOutcome,
    FamilyWarningClass,
    PlanningAxis,
    ReviewAxis,
    RunResult,
    RunTerminal,
    ShortlistAxis,
)
from ...schemas.scientific_context import TopicEvidenceBrief, TopicEvidenceClaimStatus
from ...schemas.shortlist_outcome import FamilyInclusionLabel, FamilyShortlistOutcome
from ...schemas.source_activity import (
    DatasetSourceActivity,
    SourceActivityItem,
    SourceActivityStatus,
)
from ...schemas.stage_d import (
    StageDCandidateDisposition,
    StageDFailureKind,
    StageDOutcomeRecord,
    StageDProcessedCandidate,
)
from ...schemas.stage_receipt import FailureClass, StageReceipt, StageStatus
from ...schemas.topic_literature import TopicSourceTable
from ...schemas.variant_novelty import VariantNoveltyResult
from ..agents.automated_shortlist import run_automated_family_shortlist
from ..agents.citation_importance_reviewer import (
    CITATION_IMPORTANCE_CRITERIA,
    CITATION_IMPORTANCE_REVIEWER_PROMPT_VERSION,
    load_citation_importance_reviewer_prompt,
    review_citation_importance,
)
from ..agents.dataset_narrative_reviewer import (
    DATASET_NARRATIVE_FIDELITY_REVIEWER_PROMPT_VERSION,
    load_dataset_narrative_fidelity_reviewer_prompt,
)
from ..agents.formation_trace_reviewer import (
    FORMATION_TRACE_CRITERIA,
    FORMATION_TRACE_REVIEWER_PROMPT_VERSION,
    load_formation_trace_reviewer_prompt,
    promote_formation_trace_to_ai_reviewed,
    review_formation_trace,
)
from ..agents.gate_diagnostics import (
    GateDiagnostic,
    build_gate_diagnostic,
    write_gate_diagnostic,
)
from ..agents.gate_kernel import run_gate_with_revise_loop
from ..agents.generation_boundaries import generation_boundary
from ..agents.paper_case_reviewer import (
    PAPER_CASE_FIDELITY_CRITERIA,
    PAPER_CASE_FIDELITY_REVIEWER_PROMPT_VERSION,
    PaperBankBatchContext,
    load_paper_case_fidelity_reviewer_prompt,
    review_paper_case_fidelity,
)
from ..agents.pattern_reviewer import (
    QUESTION_PATTERN_CRITERIA,
    QUESTION_PATTERN_REVIEWER_PROMPT_VERSION,
    load_question_pattern_reviewer_prompt,
    promote_pattern_to_ai_reviewed,
    review_question_pattern,
)
from ..agents.promotion import assert_product_grade_promotion, build_promotion_receipt
from ..agents.question_scientist_family import (
    NoValidFamilies,
    StageDPromptBudgetError,
    build_question_family_quality_report,
    build_question_family_user_packet,
    generate_question_family_batch,
    write_question_family_batch,
    write_question_family_quality_report,
)
from ..agents.shortlist_reviewer import (
    SHORTLIST_WORTHINESS_CRITERIA,
    SHORTLIST_WORTHINESS_REVIEWER_PROMPT_VERSION,
    load_shortlist_worthiness_reviewer_prompt,
)
from ..agents.topic_evidence_reviewer import (
    TOPIC_EVIDENCE_REVIEWER_PROMPT_VERSION,
    build_topic_evidence_gate_diagnostic,
    load_topic_evidence_reviewer_prompt,
    promote_topic_evidence_to_ai_reviewed,
    review_topic_evidence,
)
from ..context.evidence_basis_labels import (
    abstract_only_gap_and_strong_claim_counts,
    dossier_evidence_basis_banner,
    summary_evidence_basis_line,
    topic_evidence_basis_banner,
)
from ..context.question_scientist_export import QuestionScientistContextReadinessError
from ..context.research_scope import resolve_research_scope
from ..context.topic_evidence import (
    GENERIC_REQUIRED_LANES,
    TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION,
    R5TopicEvidenceSourceTable,
    build_r5_topic_source_table,
    build_topic_evidence_brief_draft_bundle,
    claim_supporting_source_ids,
)
from ..context.topic_evidence_readiness import evaluate_topic_evidence_readiness
from ..dossier.development_review_dossier import DevelopmentReviewNotAccepted
from ..narrative_sources.fusion import SourceKind
from ..narrative_sources.narrative_persistence import (
    persist_reviewed_narrator_result,
    promote_narrator_result_to_reviewed,
    reviewed_dataset_narrative_path,
)
from ..narrative_sources.narrator import NarratorResult, gather_and_fuse_dataset_narrative
from ..paper_ingest.paperbank_gate import (
    AcceptedPaperCase,
    PaperBankGateResult,
    PaperCaseDraft,
    _has_reviewable_selection,
    run_paperbank_then,
)
from ..paper_patterns.citation_importance import select_key_citations_product
from ..paper_patterns.formation_trace import FormationTraceRecord, collect_formation_trace_records
from ..paper_patterns.induction import NoInduciblePatterns, induce_question_patterns
from ..paper_patterns.literature_context import build_paper_local_literature_trace_context
from ..paper_patterns.pattern_revision import (
    PatternRevisionHistory,
    PatternRevisionRound,
    QuestionPatternRevisionError,
    revise_question_pattern,
)
from ..paper_patterns.review import write_question_pattern_bank
from ..paper_patterns.trace_drafting import (
    TraceDraftInsufficientEvidence,
    draft_question_formation_trace,
)
from ..planning.dataset_planner_packet import DatasetInspectionResources
from ..planning.planner_failures import HardFamilyIntegrityViolation
from ..retrieval.fulltext_fetch import (
    FulltextEnrichmentCounts,
    FulltextFetcher,
    NullFulltextFetcher,
    OpenAccessFulltextFetcher,
    enrich_records_with_fulltext,
)
from .front_half_persist import (
    build_shortlist_manifest,
    persist_reviewed_topic_evidence,
    persist_shortlist_manifest,
)
from .paperbank_import import PaperBankImportError, import_paperbank_from_run
from .resume import (
    STAGE_BACK_HALF,
    STAGE_C,
    STAGE_D,
    STAGE_DATASET_HALF,
    STAGE_FRONT_LAYOUT,
    STAGE_PAPER_HALF,
    DatasetHalfStageOutput,
    PaperHalfStageOutput,
    acquire_run_lock,
    compute_dataset_half_input_digests,
    compute_paper_half_input_digests,
    find_payload_path,
    find_shortlist_path,
    relative_output_digests,
    stage_config_version,
    stage_model_versions,
    stage_prompt_versions,
    upstream_input_digests,
)
from .run_envelope import (
    RunContext,
    _restore_bytes,
    add_diagnostic,
    atomic_write_model,
    atomic_write_text,
    authority_from_status,
    index_existing_artifact,
    initialize_run,
    load_run_manifest,
    promote_indexed_artifact,
    promote_model_artifact,
    promote_text_artifact,
    reconcile_family_inventory,
    record_run_failure,
    set_run_state,
    set_stage_state,
    upsert_family_disposition,
    upsert_paper_disposition,
    validate_exact_artifact,
    write_family_fallback,
    write_run_manifest,
)
from .run_envelope import (
    fresh_run_id as _envelope_fresh_run_id,
)
from .run_layout import (
    DEV_SURROGATE_DOSSIER_BANNER,
    PROVISIONAL_INSPIRATION_DOSSIER_BANNER,
    RunPaths,
    assign_family_slugs,
    family_slug,
    read_stage_receipt,
    render_question_families,
    render_shortlist,
    write_dataset_narrative,
    write_formation_trace,
    write_paper_case_view,
    write_paperbank_summary,
    write_question_families,
    write_question_patterns,
    write_research_scope_product,
    write_resolved_inputs,
    write_retrieval_summary,
    write_run_summary,
    write_run_terminal_summary,
    write_shortlist,
    write_stage_receipt,
    write_topic_evidence_summary,
)
from .runtime_factories import (
    build_inspection_resources,
    build_openalex_request_coordinator,
    build_owner_reviewer_providers,
    build_paper_lookup_providers,
    build_planner_host_factory,
    build_scientific_provider,
    build_source_reference_providers,
)

if TYPE_CHECKING:
    from ..dossier.multi_family_orchestrator import MultiFamilyFamilyResult


# --- the single injection seam (F6) ---------------------------------------------------------------
# Every front-half gate's ACTIVE reviewer prompt (family/version + loader). gate_session refuses an
# unregistered gate: a front-half gate reviewer must never run with an empty system prompt (that is
# exactly the live bug this map fixes — a promptless reviewer cannot know the required criteria keys,
# so every model-accept was structurally downgraded).
_FRONT_HALF_GATE_PROMPTS: dict[str, tuple[str, Callable[[], str]]] = {
    "paper_case_fidelity": (
        PAPER_CASE_FIDELITY_REVIEWER_PROMPT_VERSION,
        load_paper_case_fidelity_reviewer_prompt,
    ),
    "citation_importance": (
        CITATION_IMPORTANCE_REVIEWER_PROMPT_VERSION,
        load_citation_importance_reviewer_prompt,
    ),
    "formation_trace": (
        FORMATION_TRACE_REVIEWER_PROMPT_VERSION,
        load_formation_trace_reviewer_prompt,
    ),
    "question_pattern": (
        QUESTION_PATTERN_REVIEWER_PROMPT_VERSION,
        load_question_pattern_reviewer_prompt,
    ),
    "narrative_fidelity": (
        DATASET_NARRATIVE_FIDELITY_REVIEWER_PROMPT_VERSION,
        load_dataset_narrative_fidelity_reviewer_prompt,
    ),
    "topic_evidence": (
        TOPIC_EVIDENCE_REVIEWER_PROMPT_VERSION,
        load_topic_evidence_reviewer_prompt,
    ),
    "shortlist_worthiness": (
        SHORTLIST_WORTHINESS_REVIEWER_PROMPT_VERSION,
        load_shortlist_worthiness_reviewer_prompt,
    ),
}


class StageExecutor:
    """Builds every provider/session/host from the config. The ONLY place real providers are made.

    Standard mode builds real providers via the C2 factories; ``subscription_only_demo`` resolves every
    role to ``mock`` (``effective_provider``). Tests inject a subclass / mock so the demo zero-paid spy
    can assert real-provider construction == 0.
    """

    def __init__(self, config: MaieusisProjectConfig) -> None:
        self.config = config

    @property
    def is_demo(self) -> bool:
        return self.config.is_demo

    def generation_provider(self, role: str) -> StructuredModelProvider:
        """The front-half GENERATOR for one configured ROLE.

        Each role rides its OWN configured model — previously every generation call resolved
        ``models.owner`` while ``paperbank.extraction`` /
        ``models.{pattern,questioner,narrator,topic}``
        were read only by the preflight cost estimate, so a per-role model split was silently
        inert in real runs (same estimate-vs-driver divergence class as the ``max_families`` fix).
        """
        role_models = {
            "extraction": self.config.paperbank.extraction,
            "pattern": self.config.models.effective_pattern,
            "questioner": self.config.models.questioner,
            "narrator": self.config.models.narrator,
            "topic": self.config.models.topic,
        }
        if role not in role_models:
            raise ValueError(
                f"Unknown generation role {role!r}: expected one of {sorted(role_models)}"
            )
        pm = self.config.effective_provider(role_models[role])
        return build_model_provider(
            pm.provider.strip().lower(),
            model=pm.model or "",
            allow_pro_model=self.config.models.allow_pro_model,
        )

    def gate_session(
        self, *, gate_name: str, generator_provider_ids: Sequence[str]
    ) -> ScientificAgentSession:
        """A fresh cross-provider gate reviewer session (config reviewer ≠ generator family).

        The session's system prompt is the gate's ACTIVE reviewer prompt file. Previously every
        front-half gate reviewer was built with ``system_prompt=""`` (born that way in 5c-1b), so
        the live reviewer never saw its gate instructions or the required criteria keys — its
        criterion_assessments could not match them and the kernel structurally downgraded even a
        model-accept of a good artifact.
        """
        if gate_name not in _FRONT_HALF_GATE_PROMPTS:
            raise ValueError(
                f"Unknown front-half gate {gate_name!r}: no reviewer prompt is registered — "
                "a gate reviewer must never run with an empty system prompt"
            )
        prompt_version, load_prompt = _FRONT_HALF_GATE_PROMPTS[gate_name]
        pm = self.config.effective_provider(self.config.models.reviewer)
        provider: ScientificAgentProvider = build_scientific_provider(
            pm, system_prompt=load_prompt(), allow_pro_model=self.config.models.allow_pro_model
        )
        return provider.start_session(
            branch_id="front-half",
            session_id=f"{gate_name}-review",
            prompt_version=prompt_version,
        )

    def web_search_provider(self) -> WebSearchModelProvider | None:
        """The narrator Source-C (model web research) provider; None ⇒ Source C is skipped (V1: off)."""
        return None

    def fulltext_fetcher(self) -> FulltextFetcher:
        """The OA fulltext plus-on fetcher (config-gated): real OA routes on, else a no-op Null fetcher.

        Off when literature is off and in demo (literature is force-disabled there) — the real HTTP path
        is the operator's gated live step; tests inject a fake fetcher. It never gates a run.
        """
        literature = self.config.literature
        if literature.enabled and literature.fulltext_enrichment:
            return OpenAccessFulltextFetcher()
        return NullFulltextFetcher()

    def owner_reviewer_providers(
        self,
    ) -> tuple[ScientificAgentProvider, ScientificAgentProvider]:
        """The (owner, reviewer) API-agent providers for the back-half orchestrator (distinct)."""
        return build_owner_reviewer_providers(self.config)

    def planner_host_factory(self, run_root: Path) -> Callable[[str], CodingAgentPlannerHost]:
        """The per-family coding-agent host factory (real host standard / explicit Fake demo)."""
        return build_planner_host_factory(self.config, run_root=run_root)

    def inspection_resources(self) -> DatasetInspectionResources:
        return build_inspection_resources(self.config)


# --- captured provenance --------------------------------------------------------------------------
@dataclass
class PaperHalfResult:
    accepted: list[AcceptedPaperCase]
    gate_result: PaperBankGateResult
    reviewed_traces: list[QuestionFormationTrace]
    reviewed_patterns: list[QuestionPatternCard]
    pattern_revision_history: list[PatternRevisionHistory]
    receipts: list[PromotionReceipt]
    # Set only when pattern induction itself exhausted a bounded provider/validation recovery.
    # Zero patterns caused by honest scientific insufficiency leave this unset.
    pattern_generation_failure_class: FailureClass | None = None


def _capture_receipt(
    receipts: list[PromotionReceipt],
    *,
    candidate: PaperCase
    | PaperLocalLiteratureContext
    | QuestionFormationTrace
    | QuestionPatternCard,
    outcome: GateOutcome,
    artifact_kind: str,
    expected_gate: str,
) -> None:
    # F2: the front-half GateOutcomes ARE reachable — capture a PromotionReceipt so DP-5 can fire.
    receipts.append(
        build_promotion_receipt(
            candidate=candidate,
            outcome=outcome,
            artifact_kind=artifact_kind,
            expected_gate=expected_gate,
        )
    )


# A diagnostic label for the trace-DRAFT honest degrade (Deliverable E). It is NOT a reviewer gate
# (no gate_session, no reviewer prompt), so it is deliberately a constant rather than an inline
# ``gate_name="..."`` literal that the front-half gate-prompt source-sweep would treat as a gate.
_FORMATION_TRACE_DRAFT_DIAGNOSTIC = "formation_trace_draft"
# Diagnostic label for the induction honest-degrade (D3) — not a reviewer gate (no gate_session).
_QUESTION_PATTERN_INDUCTION_DIAGNOSTIC = "question_pattern_induction"
# Diagnostic label for the stage-D family-generation honest-degrade (D6).
_QUESTION_FAMILY_GENERATION_DIAGNOSTIC = "question_family_generation"
# Non-review diagnostic labels; constants keep the gate-prompt source sweep scoped to real gates.
_TOPIC_EVIDENCE_AVAILABILITY_DIAGNOSTIC = "topic_evidence_availability"
_TOPIC_EVIDENCE_PROVISIONAL_DIAGNOSTIC = "topic_evidence_provisional"
_QUESTION_FAMILY_RETRY_DIAGNOSTIC = "question_family_retry"
_PROVISIONAL_PLANNING_BOUNDARY_DIAGNOSTIC = "provisional_planning_boundary"
_STAGE_D_CURRENT_BATCH_ATTRIBUTE = "_maieusis_stage_d_current_batch_path"


def _diagnostics_dir(run_corpus: Path) -> Path:
    """``runs/<id>/diagnostics/`` — run_corpus is ``runs/<id>/corpus`` (RunLayout.corpus)."""
    return run_corpus.parent / "diagnostics"


def _record_non_accept_diagnostic(
    outcome: GateOutcome,
    required_criteria: Sequence[str],
    *,
    run_corpus: Path,
    artifact_label: str = "",
) -> Path | None:
    """Surface-only: on a non-accept front-half gate outcome, persist WHY under the run's
    diagnostics dir. Never changes the decision; a per-artifact filename keeps concurrent
    paper-half writes independent."""
    if outcome.is_accept:
        return None
    diagnostic = build_gate_diagnostic(outcome, required_criteria, artifact_label=artifact_label)
    return write_gate_diagnostic(diagnostic, _diagnostics_dir(run_corpus))


def run_paper_half(
    drafts: Sequence[PaperCaseDraft],
    *,
    executor: StageExecutor,
    run_corpus: Path,
    minimum_paper_count: int = 1,
    max_workers: int = 1,
    max_revise_rounds: int = 1,
    citation_prompt_char_budget: int = 120_000,
) -> PaperHalfResult:
    """Gate → traces → patterns → persist reviewed to the RUN-LOCAL corpus (F2 receipts captured).

    Drives the real 5a gates: PaperCase fidelity + citation (inside ``gate_paperbank``), formation-trace,
    and pattern — each earned + independent. Promoted patterns land in ``run_corpus`` for stage C.
    """
    receipts: list[PromotionReceipt] = []
    generator = executor.generation_provider("extraction")
    gen_ids = [generator.provider_id]
    _retry_unreviewable_citation_selections(
        drafts,
        generator=generator,
        max_prompt_chars=citation_prompt_char_budget,
    )

    # The gate invokes the review closures CONCURRENTLY when max_workers > 1, so gate receipts are
    # recorded into a lock-guarded per-paper bucket and flattened in draft order after the gate —
    # the persisted receipt sequence stays byte-identical to the serial path.
    gate_receipts: dict[int, list[PromotionReceipt]] = {}
    gate_receipts_lock = threading.Lock()

    def _bucket_gate_receipt(
        paper_case: PaperCase,
        *,
        candidate: PaperCase | PaperLocalLiteratureContext,
        outcome: GateOutcome,
        artifact_kind: str,
        expected_gate: str,
    ) -> None:
        # F2: the front-half GateOutcomes ARE reachable — capture a PromotionReceipt so DP-5 can fire.
        receipt = build_promotion_receipt(
            candidate=candidate,
            outcome=outcome,
            artifact_kind=artifact_kind,
            expected_gate=expected_gate,
        )
        with gate_receipts_lock:
            gate_receipts.setdefault(id(paper_case), []).append(receipt)

    def fidelity_review(
        paper_case: PaperCase,
        literature: PaperLocalLiteratureContext,
        batch: PaperBankBatchContext,
    ) -> GateOutcome:
        outcome = review_paper_case_fidelity(
            session=executor.gate_session(
                gate_name="paper_case_fidelity", generator_provider_ids=gen_ids
            ),
            paper_case=paper_case,
            literature=literature,
            batch_context=batch,
            generator_provider_ids=gen_ids,
        )
        if outcome.is_accept:
            _bucket_gate_receipt(
                paper_case,
                candidate=paper_case,
                outcome=outcome,
                artifact_kind="paper_case",
                expected_gate="paper_case_fidelity",
            )
        else:
            _record_non_accept_diagnostic(
                outcome,
                PAPER_CASE_FIDELITY_CRITERIA,
                run_corpus=run_corpus,
                artifact_label=paper_case.paper_case_id,
            )
        return outcome

    def citation_review(paper_case: PaperCase, literature: PaperLocalLiteratureContext):
        def _review_once(candidate: PaperLocalLiteratureContext) -> GateOutcome:
            return review_citation_importance(
                session=executor.gate_session(
                    gate_name="citation_importance", generator_provider_ids=gen_ids
                ),
                paper_case=paper_case,
                literature=candidate,
                generator_provider_ids=gen_ids,
            )

        outcome = _review_once(literature)
        # One bounded reselection is a cheap recovery for a stochastic selector that chose works
        # without usable context IDs. It is attempted only when the independent reviewer found hard
        # evidence closure unresolved; ordinary scientific revise/insufficient outcomes already
        # degrade honestly without excluding the PaperCase.
        if not outcome.is_accept and not outcome.evidence_resolved:
            reselected = select_key_citations_product(
                generator,
                paper_case=paper_case,
                literature_context=literature,
                max_prompt_chars=citation_prompt_char_budget,
            )
            if _has_reviewable_selection(reselected):
                literature.importance_selection = reselected.importance_selection
                # The bounded recovery call must not turn one already-honest citation rejection
                # into a whole-batch infrastructure failure. Preserve the first independently
                # bound outcome; the normal gate policy will exclude or degrade this paper.
                with suppress(ScientificAgentSessionError):
                    outcome = _review_once(literature)
        if outcome.is_accept:
            _bucket_gate_receipt(
                paper_case,
                candidate=literature,
                outcome=outcome,
                artifact_kind="citation_literature",
                expected_gate="citation_importance",
            )
        else:
            _record_non_accept_diagnostic(
                outcome,
                CITATION_IMPORTANCE_CRITERIA,
                run_corpus=run_corpus,
                artifact_label=paper_case.paper_case_id,
            )
        return outcome

    accepted_holder: list[AcceptedPaperCase] = []
    gate_result = run_paperbank_then(
        drafts,
        fidelity_review=fidelity_review,
        citation_review=citation_review,
        on_accepted=accepted_holder.extend,
        minimum_paper_count=minimum_paper_count,
        max_workers=max_workers,
    )
    for draft in drafts:
        if draft.paper_case is not None:
            receipts.extend(gate_receipts.get(id(draft.paper_case), []))
    _persist_paper_gate_products(
        drafts=drafts,
        accepted=accepted_holder,
        gate_result=gate_result,
        run_corpus=run_corpus,
        development_surrogate=any_mock_reviewer(receipts),
    )
    reviewed_patterns, reviewed_traces, pattern_revision_history, pattern_failure_class = (
        _traces_and_patterns(
            accepted_holder,
            executor=executor,
            generator=generator,
            receipts=receipts,
            run_corpus=run_corpus,
            max_revise_rounds=max_revise_rounds,
        )
        if gate_result.should_continue
        else ([], [], [], None)
    )
    if reviewed_patterns:
        manifest = write_question_pattern_bank(reviewed_patterns, corpus_root=run_corpus)
        _persist_pattern_products(
            reviewed_patterns,
            manifest=manifest,
            run_corpus=run_corpus,
            development_surrogate=any_mock_reviewer(receipts),
        )
    else:
        _persist_pattern_insufficiency(run_corpus)
    return PaperHalfResult(
        accepted=accepted_holder,
        gate_result=gate_result,
        reviewed_traces=reviewed_traces,
        reviewed_patterns=reviewed_patterns,
        pattern_revision_history=pattern_revision_history,
        receipts=receipts,
        pattern_generation_failure_class=pattern_failure_class,
    )


def _retry_unreviewable_citation_selections(
    drafts: Sequence[PaperCaseDraft],
    *,
    generator: StructuredModelProvider,
    max_prompt_chars: int,
) -> None:
    """Retry one stochastic empty/model-failed selection before any gate outcome is bound."""
    retryable = {
        CitationSelectionStatus.INSUFFICIENT_EVIDENCE,
        CitationSelectionStatus.MODEL_FAILED,
    }
    for draft in drafts:
        paper_case, literature = draft.paper_case, draft.literature
        selection = literature.importance_selection if literature is not None else None
        if (
            paper_case is None
            or literature is None
            or not literature.cited_works
            or selection is None
            or selection.selection_status not in retryable
        ):
            continue
        reselected = select_key_citations_product(
            generator,
            paper_case=paper_case,
            literature_context=literature,
            max_prompt_chars=max_prompt_chars,
        )
        if not _has_reviewable_selection(reselected):
            continue
        draft.literature = reselected
        draft.paper_case = paper_case.model_copy(
            update={
                "local_literature_context_id": reselected.context_id,
                "local_literature_context_digest": literature_context_digest(reselected),
                "key_cited_work_ids": list(
                    reselected.importance_selection.selected_cited_work_ids
                    if reselected.importance_selection is not None
                    else []
                ),
            }
        )


def _run_context_for_corpus(run_corpus: Path) -> RunContext | None:
    """Resolve the already initialized envelope for a run-local corpus, when present."""
    paths = RunPaths(root=run_corpus.parent)
    if not paths.run_manifest.is_file():
        return None
    context = RunContext(run_id=paths.root.name, paths=paths)
    load_run_manifest(paths)
    return context


def _persist_paper_gate_products(
    *,
    drafts: Sequence[PaperCaseDraft],
    accepted: Sequence[AcceptedPaperCase],
    gate_result: PaperBankGateResult,
    run_corpus: Path,
    development_surrogate: bool,
) -> None:
    context = _run_context_for_corpus(run_corpus)
    if context is None:
        return
    paths = context.paths
    accepted_cases = [item.paper_case for item in accepted]
    extracted_cases = [draft.paper_case for draft in drafts if draft.paper_case is not None]
    slugs = assign_family_slugs(case.paper_case_id for case in extracted_cases)
    accepted_by_input = {item.paper_id: item.paper_case for item in accepted}
    excluded_by_input = {item.paper_id: item for item in gate_result.excluded}

    for draft in drafts:
        accepted_case = accepted_by_input.get(draft.paper_id)
        if accepted_case is not None:
            slug = slugs[accepted_case.paper_case_id]
            typed_path = atomic_write_model(paths.paper_case_artifact(slug), accepted_case)
            authority = (
                ArtifactAuthority.PROVISIONAL
                if development_surrogate
                else authority_from_status(accepted_case.review.status)
            )
            index_existing_artifact(
                context,
                typed_path,
                kind=ArtifactKind.PAPER_CASE,
                processing_state=ProductProcessingState.PRODUCED,
                authority=authority,
                paper_id=accepted_case.paper_case_id,
            )
            view_path = write_paper_case_view(paths, paper_slug=slug, case=accepted_case)
            index_existing_artifact(
                context,
                view_path,
                kind=ArtifactKind.PAPER_CASE_VIEW,
                processing_state=ProductProcessingState.PRODUCED,
                authority=authority,
                paper_id=accepted_case.paper_case_id,
            )
            upsert_paper_disposition(
                context,
                PaperDisposition(
                    input_identity=draft.paper_id,
                    input_path=accepted_case.source_pdf,
                    paper_id=accepted_case.paper_case_id,
                    disposition=PaperDispositionKind.ACCEPTED,
                    paper_case_path=view_path.relative_to(paths.root).as_posix(),
                ),
            )
            continue

        excluded = excluded_by_input.get(draft.paper_id)
        reason = excluded.reason if excluded is not None else "no accepted PaperCase"
        retained_view = ""
        if draft.paper_case is not None:
            slug = slugs[draft.paper_case.paper_case_id]
            typed_path = atomic_write_model(paths.paper_case_artifact(slug), draft.paper_case)
            index_existing_artifact(
                context,
                typed_path,
                kind=ArtifactKind.PAPER_CASE,
                processing_state=ProductProcessingState.DEGRADED,
                authority=ArtifactAuthority.PROVISIONAL,
                paper_id=draft.paper_case.paper_case_id,
            )
            view_path = write_paper_case_view(paths, paper_slug=slug, case=draft.paper_case)
            index_existing_artifact(
                context,
                view_path,
                kind=ArtifactKind.PAPER_CASE_VIEW,
                processing_state=ProductProcessingState.DEGRADED,
                authority=ArtifactAuthority.PROVISIONAL,
                paper_id=draft.paper_case.paper_case_id,
            )
            retained_view = view_path.relative_to(paths.root).as_posix()
        disposition = (
            PaperDispositionKind.UNAVAILABLE
            if excluded is not None and excluded.reason == "unparseable"
            else PaperDispositionKind.NO_CASE
        )
        upsert_paper_disposition(
            context,
            PaperDisposition(
                input_identity=draft.paper_id,
                input_path=draft.paper_case.source_pdf if draft.paper_case is not None else "",
                paper_id=(
                    draft.paper_case.paper_case_id
                    if draft.paper_case is not None
                    else draft.paper_id
                ),
                disposition=disposition,
                reason=reason,
                paper_case_path=retained_view,
            ),
        )

    paperbank_summary = write_paperbank_summary(paths, gate_result)
    index_existing_artifact(
        context,
        paperbank_summary,
        kind=ArtifactKind.PAPER_CASE_VIEW,
        processing_state=(
            ProductProcessingState.PRODUCED if accepted_cases else ProductProcessingState.DEGRADED
        ),
        authority=(
            (
                ArtifactAuthority.PROVISIONAL
                if development_surrogate
                else ArtifactAuthority.AGENT_REVIEWED
            )
            if accepted_cases
            else ArtifactAuthority.UNKNOWN
        ),
        paper_id="paperbank-summary",
    )


def _persist_pattern_products(
    patterns: Sequence[QuestionPatternCard],
    *,
    manifest: QuestionPatternBankManifest,
    run_corpus: Path,
    development_surrogate: bool,
) -> None:
    context = _run_context_for_corpus(run_corpus)
    if context is None:
        return
    paths = context.paths
    authorities = [authority_from_status(pattern.review_status) for pattern in patterns]
    authority = (
        ArtifactAuthority.PROVISIONAL
        if development_surrogate
        else (
            ArtifactAuthority.VERIFIED
            if authorities and all(item == ArtifactAuthority.VERIFIED for item in authorities)
            else ArtifactAuthority.AGENT_REVIEWED
        )
    )
    stable_by_id: dict[str, Path] = {}
    for pattern in patterns:
        stable_by_id[pattern.pattern_id] = atomic_write_model(
            paths.question_pattern_artifact(pattern.pattern_id), pattern
        )
        index_existing_artifact(
            context,
            stable_by_id[pattern.pattern_id],
            kind=ArtifactKind.QUESTION_PATTERN,
            processing_state=ProductProcessingState.PRODUCED,
            authority=authority,
        )
    stable_entries = [
        entry.model_copy(
            update={
                "pattern_path": stable_by_id[entry.pattern_id].relative_to(paths.root).as_posix()
            }
        )
        for entry in manifest.entries
    ]
    stable_dir = paths.pattern_artifacts.relative_to(paths.root).as_posix()
    stable_manifest = manifest.model_copy(
        update={
            "extracted_patterns_dir": stable_dir,
            "reviewed_patterns_dir": stable_dir,
            "entries": stable_entries,
        }
    )
    manifest_path = atomic_write_model(paths.pattern_bank_artifact, stable_manifest)
    index_existing_artifact(
        context,
        manifest_path,
        kind=ArtifactKind.PATTERN_BANK,
        processing_state=ProductProcessingState.PRODUCED,
        authority=authority,
    )
    report_path = write_question_patterns(paths, patterns)
    index_existing_artifact(
        context,
        report_path,
        kind=ArtifactKind.PATTERN_REPORT,
        processing_state=ProductProcessingState.PRODUCED,
        authority=authority,
    )


def _persist_pattern_insufficiency(run_corpus: Path) -> None:
    context = _run_context_for_corpus(run_corpus)
    if context is None:
        return
    text = (
        "# Question-pattern insufficiency\n\n"
        "No reviewed question-formation pattern was available. Accepted PaperCases and reviewed "
        "formation traces remain visible, but question-family generation was not reached.\n"
    )
    stable_path = atomic_write_text(context.paths.pattern_insufficiency, text)
    index_existing_artifact(
        context,
        stable_path,
        kind=ArtifactKind.PATTERN_REPORT,
        processing_state=ProductProcessingState.DEGRADED,
        authority=ArtifactAuthority.UNKNOWN,
    )
    public_path = atomic_write_text(context.paths.question_patterns, text)
    index_existing_artifact(
        context,
        public_path,
        kind=ArtifactKind.PATTERN_REPORT,
        processing_state=ProductProcessingState.DEGRADED,
        authority=ArtifactAuthority.UNKNOWN,
    )
    add_diagnostic(
        context,
        diagnostic_class=DiagnosticClass.SCIENTIFIC,
        code="no_reviewed_question_patterns",
        public_message=(
            "No reviewed question-formation pattern survived; accepted upstream products remain available."
        ),
        internal_path=stable_path.relative_to(context.paths.root).as_posix(),
    )


def _persist_formation_trace_product(
    context: RunContext,
    *,
    paper_case: PaperCase,
    trace: QuestionFormationTrace,
    paper_slug: str,
    development_surrogate: bool,
) -> None:
    """Project one already-reviewed trace; shared by generation and receipt-bound import."""
    typed_trace = atomic_write_model(context.paths.formation_trace_artifact(paper_slug), trace)
    trace_view = write_formation_trace(context.paths, paper_slug=paper_slug, trace=trace)
    trace_authority = (
        ArtifactAuthority.PROVISIONAL
        if development_surrogate
        else authority_from_status(trace.review_status)
    )
    index_existing_artifact(
        context,
        typed_trace,
        kind=ArtifactKind.FORMATION_TRACE,
        processing_state=ProductProcessingState.PRODUCED,
        authority=trace_authority,
        paper_id=paper_case.paper_case_id,
    )
    index_existing_artifact(
        context,
        trace_view,
        kind=ArtifactKind.FORMATION_TRACE_VIEW,
        processing_state=ProductProcessingState.PRODUCED,
        authority=trace_authority,
        paper_id=paper_case.paper_case_id,
    )
    disposition = next(
        item
        for item in load_run_manifest(context.paths).papers
        if item.paper_id == paper_case.paper_case_id
    )
    disposition.formation_trace_path = trace_view.relative_to(context.paths.root).as_posix()
    upsert_paper_disposition(context, disposition)


def _project_imported_paper_half(
    context: RunContext, output: PaperHalfStageOutput
) -> PaperHalfResult:
    """Rebuild the target run's user projection from receipt-signed typed paper products."""
    accepted_by_input = {item.paper_id: item for item in output.accepted}
    drafts = [
        PaperCaseDraft(
            paper_id=item.paper_id,
            paper_case=item.paper_case,
            literature=item.literature,
        )
        for item in output.accepted
    ]
    drafts.extend(
        PaperCaseDraft(
            paper_id=item.paper_id,
            parseable=item.reason != "unparseable",
            parse_error=item.detail,
        )
        for item in output.gate_result.excluded
        if item.paper_id not in accepted_by_input
    )
    development_surrogate = any_mock_reviewer(output.receipts)
    _persist_paper_gate_products(
        drafts=drafts,
        accepted=output.accepted,
        gate_result=output.gate_result,
        run_corpus=context.paths.corpus,
        development_surrogate=development_surrogate,
    )

    paper_slugs = assign_family_slugs(item.paper_case.paper_case_id for item in output.accepted)
    for trace in output.traces:
        matches = [
            item
            for item in output.accepted
            if trace.local_literature_context_id
            and trace.local_literature_context_id == item.literature.context_id
        ]
        if len(matches) != 1:
            matches = [
                item
                for item in output.accepted
                if set(trace.evidence_span_ids).issubset(
                    {span.source_span_id for span in item.paper_case.evidence_spans}
                )
                and bool(trace.evidence_span_ids)
            ]
        if len(matches) != 1:
            raise PaperBankImportError(
                f"imported formation trace {trace.trace_id!r} does not resolve to exactly one PaperCase"
            )
        paper_case = matches[0].paper_case
        _persist_formation_trace_product(
            context,
            paper_case=paper_case,
            trace=trace,
            paper_slug=paper_slugs[paper_case.paper_case_id],
            development_surrogate=development_surrogate,
        )

    manifest = load_model(
        context.paths.corpus / "question_pattern_manifest.yaml", QuestionPatternBankManifest
    )
    _persist_pattern_products(
        output.patterns,
        manifest=manifest,
        run_corpus=context.paths.corpus,
        development_surrogate=development_surrogate,
    )
    return PaperHalfResult(
        accepted=output.accepted,
        gate_result=output.gate_result,
        reviewed_traces=output.traces,
        reviewed_patterns=output.patterns,
        pattern_revision_history=output.pattern_revision_history,
        receipts=output.receipts,
    )


def _traces_and_patterns(
    accepted: Sequence[AcceptedPaperCase],
    *,
    executor: StageExecutor,
    generator: StructuredModelProvider,
    receipts: list[PromotionReceipt],
    run_corpus: Path,
    max_revise_rounds: int,
) -> tuple[
    list[QuestionPatternCard],
    list[QuestionFormationTrace],
    list[PatternRevisionHistory],
    FailureClass | None,
]:
    # Fail closed if an active serious generator has no audited scope/normalization policy.
    generation_boundary("question_formation_trace_drafter/v3")
    generation_boundary("question_pattern_inducer/v3")
    generation_boundary("question_pattern_reviser/v1")
    gen_ids = [generator.provider_id]
    cases_with_traces: list[PaperCase] = []
    reviewed_traces: list[QuestionFormationTrace] = []
    trace_infrastructure_failures = 0
    paper_slugs = assign_family_slugs(item.paper_case.paper_case_id for item in accepted)
    context = _run_context_for_corpus(run_corpus)
    for item in accepted:
        paper_case, literature = item.paper_case, item.literature
        # D1(c): the trace path needs a SELECTED key-citation selection. A paper accepted on fidelity
        # alone (no selection) or whose selection reached an honest terminal (CONTEXT_TOO_LARGE /
        # MODEL_FAILED / INSUFFICIENT_EVIDENCE) is dropped from induction with a diagnostic — never a
        # bare ValueError from build_paper_local_literature_trace_context (which was OUTSIDE the try).
        if not _has_reviewable_selection(literature):
            selection = literature.importance_selection
            status = selection.selection_status.value if selection is not None else "none"
            write_gate_diagnostic(
                GateDiagnostic(
                    gate_name=_FORMATION_TRACE_DRAFT_DIAGNOSTIC,
                    artifact_label=paper_case.paper_case_id,
                    decision=GateDecision.INSUFFICIENT_EVIDENCE,
                    rationale=f"dropped from induction: key-citation selection status={status}",
                ),
                _diagnostics_dir(run_corpus),
            )
            continue
        try:
            trace_context = build_paper_local_literature_trace_context(
                paper_case=paper_case, literature_context=literature
            )
            draft = draft_question_formation_trace(
                generator, paper_case=paper_case, trace_context=trace_context
            )
        except TraceDraftInsufficientEvidence as exc:
            # E — honest per-artifact degrade: the model produced a trace with no reconcilable
            # evidence backing. Drop this paper from pattern induction with a diagnostic; never
            # crash the run (the paper stays an accepted PaperCase, it just yields no trace/pattern).
            write_gate_diagnostic(
                GateDiagnostic(
                    gate_name=_FORMATION_TRACE_DRAFT_DIAGNOSTIC,
                    artifact_label=paper_case.paper_case_id,
                    decision=GateDecision.INSUFFICIENT_EVIDENCE,
                    rationale=f"trace draft had no reconcilable evidence: {exc}",
                ),
                _diagnostics_dir(run_corpus),
            )
            continue
        except (StructuredModelProviderError, ScientificAgentSessionError, ValidationError) as exc:
            # A malformed/failed provider response is local to this paper. It is not a scientific
            # rejection and must not erase the other independently reviewable traces.
            write_gate_diagnostic(
                GateDiagnostic(
                    gate_name=_FORMATION_TRACE_DRAFT_DIAGNOSTIC,
                    artifact_label=paper_case.paper_case_id,
                    decision=GateDecision.INFRASTRUCTURE_FAILURE,
                    rationale=f"trace generation boundary failed for this paper: {exc}",
                ),
                _diagnostics_dir(run_corpus),
            )
            trace_infrastructure_failures += 1
            continue
        trace = draft.trace
        traced_case = paper_case.model_copy(update={"formation_trace": trace})
        try:
            outcome = review_formation_trace(
                session=executor.gate_session(
                    gate_name="formation_trace", generator_provider_ids=gen_ids
                ),
                trace=trace,
                paper_case=traced_case,
                literature=literature,
                generator_provider_ids=gen_ids,
            )
        except (StructuredModelProviderError, ScientificAgentSessionError, ValidationError) as exc:
            write_gate_diagnostic(
                GateDiagnostic(
                    gate_name="formation_trace",
                    artifact_label=paper_case.paper_case_id,
                    decision=GateDecision.INFRASTRUCTURE_FAILURE,
                    rationale=f"trace review boundary failed for this paper: {exc}",
                ),
                _diagnostics_dir(run_corpus),
            )
            trace_infrastructure_failures += 1
            continue
        if not outcome.is_accept:
            _record_non_accept_diagnostic(
                outcome,
                FORMATION_TRACE_CRITERIA,
                run_corpus=run_corpus,
                artifact_label=paper_case.paper_case_id,
            )
            continue
        promoted_trace = promote_formation_trace_to_ai_reviewed(trace, outcome)
        if context is not None:
            _persist_formation_trace_product(
                context,
                paper_case=paper_case,
                trace=promoted_trace,
                paper_slug=paper_slugs[paper_case.paper_case_id],
                development_surrogate=(
                    outcome.reviewer_execution_kind == ReviewerExecutionKind.MOCK
                ),
            )
        _capture_receipt(
            receipts,
            candidate=trace,
            outcome=outcome,
            artifact_kind="formation_trace",
            expected_gate="formation_trace",
        )
        cases_with_traces.append(paper_case.model_copy(update={"formation_trace": promoted_trace}))
        reviewed_traces.append(promoted_trace)

    all_records = collect_formation_trace_records(cases_with_traces, product_authority=True)
    # D2(ii): partition by graded usability BEFORE induction — a trace with zero evidence of any kind
    # is dropped with a per-paper diagnostic (the whole-batch require_usable_trace_records raise never
    # fires). A literature-only trace (graded-usable) survives.
    records = [record for record in all_records if record.is_usable]
    for record in all_records:
        if not record.is_usable:
            write_gate_diagnostic(
                GateDiagnostic(
                    gate_name=_FORMATION_TRACE_DRAFT_DIAGNOSTIC,
                    artifact_label=record.paper_case_id,
                    decision=GateDecision.INSUFFICIENT_EVIDENCE,
                    rationale="dropped from induction (no usable trace evidence): "
                    + "; ".join(record.evidence_issues),
                ),
                _diagnostics_dir(run_corpus),
            )
    if not records:
        return (
            [],
            reviewed_traces,
            [],
            FailureClass.PROVIDER_FAILURE if trace_infrastructure_failures else None,
        )
    # Pattern INDUCTION rides its independent pattern-role model, not the per-paper extraction or
    # Question Scientist model: it is
    # one batch call over all traces and its QuestionPatternBank shapes all downstream question
    # quality. The pattern-gate provenance names the induction provider.
    induction_generator = executor.generation_provider("pattern")
    induction_gen_ids = [induction_generator.provider_id]
    try:
        try:
            batch = induce_question_patterns(induction_generator, records)
        except (StructuredModelProviderError, ValidationError):
            # Exactly one fresh retry for a stochastic malformed batch. Both attempts remain inside
            # the same stage budget; no scientific content is repaired or invented by the host.
            batch = induce_question_patterns(induction_generator, records)
    except NoInduciblePatterns as exc:
        # D3→D4: every induced pattern was dropped (paraphrase/firewall). Return zero patterns with a
        # diagnostic; the paper half then emits an honest zero-patterns terminal (D4), not a crash.
        write_gate_diagnostic(
            GateDiagnostic(
                gate_name=_QUESTION_PATTERN_INDUCTION_DIAGNOSTIC,
                artifact_label="induction",
                decision=GateDecision.INSUFFICIENT_EVIDENCE,
                rationale=f"all induced patterns dropped: {exc}",
            ),
            _diagnostics_dir(run_corpus),
        )
        return [], reviewed_traces, [], None
    except (StructuredModelProviderError, ValidationError) as exc:
        write_gate_diagnostic(
            GateDiagnostic(
                gate_name=_QUESTION_PATTERN_INDUCTION_DIAGNOSTIC,
                artifact_label="induction",
                decision=GateDecision.INFRASTRUCTURE_FAILURE,
                rationale=f"pattern induction failed after one bounded retry: {exc}",
            ),
            _diagnostics_dir(run_corpus),
        )
        return [], reviewed_traces, [], FailureClass.PROVIDER_FAILURE
    known_case_ids = {r.paper_case_id for r in records}
    known_trace_ids = {r.formation_trace.trace_id for r in records}
    known_trace_case_edges = {
        (record.paper_case_id, record.formation_trace.trace_id) for record in records
    }
    reviewed: list[QuestionPatternCard] = []
    revision_history: list[PatternRevisionHistory] = []
    for pattern in batch.patterns:
        pattern_records = _records_for_pattern(pattern, records)
        source_questions = _pattern_source_questions(pattern_records)
        rounds: list[PatternRevisionRound] = []

        def _review(
            current: QuestionPatternCard,
            *,
            source_questions: list[dict[str, object]] = source_questions,
        ) -> GateOutcome:
            outcome = review_question_pattern(
                session=executor.gate_session(
                    gate_name="question_pattern", generator_provider_ids=induction_gen_ids
                ),
                pattern=current,
                known_case_ids=known_case_ids,
                known_trace_ids=known_trace_ids,
                known_trace_case_edges=known_trace_case_edges,
                source_paper_questions=source_questions,
                generator_provider_ids=induction_gen_ids,
                review_guidance="\n".join(
                    warning
                    for warning in batch.warnings
                    if current.pattern_id in warning or "advisory lexical overlap" in warning
                ),
            )
            if outcome.decision == GateDecision.REVISE and not outcome.evidence_resolved:
                return outcome.model_copy(
                    update={
                        "decision": GateDecision.REJECT,
                        "rationale": outcome.rationale
                        + " Host rejected revision because the claimed source closure is invalid.",
                    }
                )
            if outcome.decision == GateDecision.REVISE and not outcome.required_changes:
                return outcome.model_copy(
                    update={
                        "decision": GateDecision.INSUFFICIENT_EVIDENCE,
                        "rationale": outcome.rationale
                        + " Reviewer requested revision without actionable required_changes.",
                    }
                )
            return outcome

        def _redraft(
            current: QuestionPatternCard,
            outcome: GateOutcome,
            *,
            pattern_records: list[FormationTraceRecord] = pattern_records,
            rounds: list[PatternRevisionRound] = rounds,
        ) -> QuestionPatternCard:
            round_index = len(rounds) + 1
            _record_non_accept_diagnostic(
                outcome,
                QUESTION_PATTERN_CRITERIA,
                run_corpus=run_corpus,
                artifact_label=f"{current.pattern_id}.round-{round_index - 1}",
            )
            revised, revision_round = revise_question_pattern(
                induction_generator,
                pattern=current,
                source_records=pattern_records,
                review_outcome=outcome,
                round_index=round_index,
            )
            rounds.append(revision_round)
            return revised

        try:
            final_pattern, loop_result = run_gate_with_revise_loop(
                artifact=pattern,
                review=_review,
                redraft=_redraft,
                max_revise_rounds=max_revise_rounds,
            )
        except (
            QuestionPatternRevisionError,
            StructuredModelProviderError,
            ScientificAgentSessionError,
        ) as exc:
            write_gate_diagnostic(
                GateDiagnostic(
                    gate_name="question_pattern",
                    artifact_label=pattern.pattern_id,
                    decision=(
                        GateDecision.INFRASTRUCTURE_FAILURE
                        if isinstance(
                            exc,
                            (StructuredModelProviderError, ScientificAgentSessionError),
                        )
                        else GateDecision.REJECT
                    ),
                    rationale=f"bounded pattern revision could not produce a valid draft: {exc}",
                ),
                _diagnostics_dir(run_corpus),
            )
            continue
        outcome = loop_result.final_outcome
        if rounds:
            revision_history.append(
                PatternRevisionHistory(
                    pattern_id=pattern.pattern_id,
                    rounds=rounds,
                    final_outcome=outcome,
                    budget_exhausted=loop_result.budget_exhausted,
                )
            )
        if not outcome.is_accept:
            _record_non_accept_diagnostic(
                outcome,
                QUESTION_PATTERN_CRITERIA,
                run_corpus=run_corpus,
                artifact_label=(
                    f"{pattern.pattern_id}.revision-budget-exhausted"
                    if loop_result.budget_exhausted
                    else pattern.pattern_id
                ),
            )
            continue
        reviewed.append(promote_pattern_to_ai_reviewed(final_pattern, outcome))
        _capture_receipt(
            receipts,
            candidate=final_pattern,
            outcome=outcome,
            artifact_kind="question_pattern",
            expected_gate="question_pattern",
        )
    return reviewed, reviewed_traces, revision_history, None


def _records_for_pattern(
    pattern: QuestionPatternCard, records: Sequence[FormationTraceRecord]
) -> list[FormationTraceRecord]:
    """Return only the exact case↔trace edges claimed by one pattern, in declared order."""
    if len(pattern.source_case_ids) != len(pattern.source_trace_ids):
        # Unequal source arrays are legal on an unreviewed model draft but can never earn source
        # closure. Send an empty evidence packet to the reviewer so the hard evidence check rejects
        # only this pattern; ``zip(strict=True)`` here would crash the entire paper half first.
        return []
    by_edge = {
        (record.paper_case_id, record.formation_trace.trace_id): record for record in records
    }
    return [
        by_edge[edge]
        for edge in zip(pattern.source_case_ids, pattern.source_trace_ids, strict=True)
        if edge in by_edge
    ]


def _pattern_source_questions(
    records: Sequence[FormationTraceRecord],
) -> list[dict[str, object]]:
    """Reviewer packet with explicit IDs; never a six-question anonymous comparison pool."""
    return [
        {
            "paper_case_id": record.paper_case_id,
            "trace_id": record.formation_trace.trace_id,
            "original_question": record.original_question,
            "resulting_question": record.formation_trace.resulting_question,
            "epistemic_move": record.epistemic_move,
            "formation_trace": record.formation_trace.model_dump(mode="json"),
        }
        for record in records
    ]


_INFRA_DOSSIER_STATUS: dict[FamilyDossierStatus, FailureClass] = {
    FamilyDossierStatus.FAILED_VALIDATION: FailureClass.VALIDATION_FAILURE,
    FamilyDossierStatus.INFRASTRUCTURE_INCOMPLETE: FailureClass.PROVIDER_FAILURE,
    FamilyDossierStatus.QUEUED: FailureClass.PROVIDER_FAILURE,
    FamilyDossierStatus.BLOCKED: FailureClass.PROVIDER_FAILURE,
    FamilyDossierStatus.HARD_INTEGRITY_TERMINAL: FailureClass.VALIDATION_FAILURE,
}

_RECOVERABLE_FAMILY_WARNING: dict[FamilyDossierStatus, FamilyWarningClass] = {
    FamilyDossierStatus.FAILED_VALIDATION: FamilyWarningClass.VALIDATION,
    FamilyDossierStatus.INFRASTRUCTURE_INCOMPLETE: FamilyWarningClass.PROVIDER,
}


def _diagnostic_failure_class(status: FamilyDossierStatus) -> FailureClass:
    if status in {
        FamilyDossierStatus.PROVENANCE_INTEGRITY_TERMINAL,
        FamilyDossierStatus.HARD_INTEGRITY_TERMINAL,
    }:
        return FailureClass.VALIDATION_FAILURE
    return _INFRA_DOSSIER_STATUS.get(status, FailureClass.SCIENTIFIC)


def _public_family_terminal_reason(status: FamilyDossierStatus) -> str:
    """Fixed public wording; raw provider payloads and request IDs stay in private diagnostics."""
    if status == FamilyDossierStatus.INFRASTRUCTURE_INCOMPLETE:
        return (
            "A planning or review provider remained unavailable after bounded retries; a readable "
            "family dossier was retained with a provider warning."
        )
    if status == FamilyDossierStatus.FAILED_VALIDATION:
        return (
            "Returned planning material could not be fully validated; a readable family dossier "
            "was retained with a validation warning."
        )
    if status in {
        FamilyDossierStatus.PROVENANCE_INTEGRITY_TERMINAL,
        FamilyDossierStatus.HARD_INTEGRITY_TERMINAL,
    }:
        return (
            "A planning integrity boundary stopped untrusted artifact promotion; a safe family "
            "summary was retained."
        )
    return status.value


# Back-half status → (planning, review, dossier) for a family the shortlist INCLUDED. Recoverable
# family-local warnings are separate from hard/shared failure_class and still render a terminal dossier.
_SCIENTIFIC_DOSSIER_AXES: dict[
    FamilyDossierStatus, tuple[PlanningAxis, ReviewAxis, DossierAxis]
] = {
    FamilyDossierStatus.COMPLETED_DOSSIER_STACK: (
        PlanningAxis.PLAN,
        ReviewAxis.ACCEPT,
        DossierAxis.RENDERED,
    ),
    FamilyDossierStatus.AUTOMATED_PLAN: (
        PlanningAxis.PLAN,
        ReviewAxis.ACCEPT,
        DossierAxis.RENDERED,
    ),
    FamilyDossierStatus.DEVELOPMENT_SURROGATE_PLAN: (
        PlanningAxis.PLAN,
        ReviewAxis.ACCEPT,
        DossierAxis.RENDERED,
    ),
    FamilyDossierStatus.PUBLIC_DOSSIER_REVISION_REQUIRED: (
        PlanningAxis.PLAN,
        ReviewAxis.ACCEPT,
        DossierAxis.TERMINAL_RENDERED,
    ),
    FamilyDossierStatus.PROVENANCE_INTEGRITY_TERMINAL: (
        PlanningAxis.PLAN,
        ReviewAxis.ACCEPT,
        DossierAxis.TERMINAL_RENDERED,
    ),
    FamilyDossierStatus.REJECTED: (
        PlanningAxis.PLAN,
        ReviewAxis.REJECT,
        DossierAxis.TERMINAL_RENDERED,
    ),
    FamilyDossierStatus.AUTOMATED_REJECT: (
        PlanningAxis.PLAN,
        ReviewAxis.REJECT,
        DossierAxis.TERMINAL_RENDERED,
    ),
    FamilyDossierStatus.DEVELOPMENT_SURROGATE_REJECT: (
        PlanningAxis.PLAN,
        ReviewAxis.REJECT,
        DossierAxis.TERMINAL_RENDERED,
    ),
    FamilyDossierStatus.REVISION_BUDGET_EXHAUSTED: (
        PlanningAxis.BUDGET_EXHAUSTED,
        ReviewAxis.REVISION_TERMINAL,
        DossierAxis.TERMINAL_RENDERED,
    ),
    FamilyDossierStatus.MATERIAL_REVISION_DEFERRED: (
        PlanningAxis.MATERIAL_DEFERRED,
        ReviewAxis.REVISION_TERMINAL,
        DossierAxis.TERMINAL_RENDERED,
    ),
    FamilyDossierStatus.HUMAN_ESCALATION: (
        PlanningAxis.ESCALATION,
        ReviewAxis.NOT_RUN,
        DossierAxis.TERMINAL_RENDERED,
    ),
    FamilyDossierStatus.REVIEW_ESCALATED: (
        PlanningAxis.ESCALATION,
        ReviewAxis.HUMAN_ESCALATION,
        DossierAxis.TERMINAL_RENDERED,
    ),
    FamilyDossierStatus.AUTOMATED_ESCALATION: (
        PlanningAxis.ESCALATION,
        ReviewAxis.NOT_RUN,
        DossierAxis.TERMINAL_RENDERED,
    ),
    FamilyDossierStatus.DEVELOPMENT_SURROGATE_ESCALATION: (
        PlanningAxis.ESCALATION,
        ReviewAxis.NOT_RUN,
        DossierAxis.TERMINAL_RENDERED,
    ),
}


def family_outcome_from_dossier_status(
    question_family_id: str,
    *,
    status: FamilyDossierStatus,
    failed_stage_receipt_id: str = "",
    reason: str = "",
) -> FamilyRunOutcome:
    """Map an INCLUDED family's back-half ``FamilyDossierStatus`` → a derived ``FamilyRunOutcome``.

    Infra statuses (validation/incomplete/queued/blocked) become ``run_incomplete`` with an infrastructure
    ``failure_class`` pointing at the orchestrator receipt — NEVER a scientific rejection (DP-1).
    """
    if status in _RECOVERABLE_FAMILY_WARNING:
        return FamilyRunOutcome.derive(
            question_family_id=question_family_id,
            shortlist_axis=ShortlistAxis.INCLUDED,
            warning_class=_RECOVERABLE_FAMILY_WARNING[status],
            dossier_axis=DossierAxis.TERMINAL_RENDERED,
            reason=reason or f"back-half {status.value}",
        )
    if status == FamilyDossierStatus.HARD_INTEGRITY_TERMINAL:
        return FamilyRunOutcome.derive(
            question_family_id=question_family_id,
            shortlist_axis=ShortlistAxis.INCLUDED,
            failure_class=FailureClass.VALIDATION_FAILURE,
            failed_stage_receipt_id=failed_stage_receipt_id or STAGE_BACK_HALF,
            dossier_axis=DossierAxis.TERMINAL_RENDERED,
            reason=reason or status.value,
        )
    if status in _INFRA_DOSSIER_STATUS:
        return FamilyRunOutcome.derive(
            question_family_id=question_family_id,
            shortlist_axis=ShortlistAxis.INCLUDED,
            failure_class=_INFRA_DOSSIER_STATUS[status],
            failed_stage_receipt_id=failed_stage_receipt_id or STAGE_BACK_HALF,
            reason=reason or f"back-half {status.value}",
        )
    if status == FamilyDossierStatus.PROVENANCE_INTEGRITY_TERMINAL:
        planning, review, dossier = _SCIENTIFIC_DOSSIER_AXES[status]
        return FamilyRunOutcome.derive(
            question_family_id=question_family_id,
            shortlist_axis=ShortlistAxis.INCLUDED,
            planning_axis=planning,
            review_axis=review,
            dossier_axis=dossier,
            failure_class=FailureClass.VALIDATION_FAILURE,
            failed_stage_receipt_id=(failed_stage_receipt_id or STAGE_BACK_HALF),
            reason=reason or status.value,
        )
    planning, review, dossier = _SCIENTIFIC_DOSSIER_AXES[status]
    return FamilyRunOutcome.derive(
        question_family_id=question_family_id,
        shortlist_axis=ShortlistAxis.INCLUDED,
        planning_axis=planning,
        review_axis=review,
        dossier_axis=dossier,
        reason=reason or status.value,
    )


def non_included_family_outcome(
    question_family_id: str,
    *,
    shortlist_axis: ShortlistAxis,
    failed_stage_receipt_id: str = "",
    novelty_direct_recap: bool = False,
    reason: str = "",
) -> FamilyRunOutcome:
    """A family the shortlist did NOT include (rejected/deferred/run_incomplete bucket) — back half NOT_RUN."""
    failure_class = (
        FailureClass.PROVIDER_FAILURE if shortlist_axis == ShortlistAxis.RUN_INCOMPLETE else None
    )
    return FamilyRunOutcome.derive(
        question_family_id=question_family_id,
        shortlist_axis=shortlist_axis,
        failure_class=failure_class,
        failed_stage_receipt_id=failed_stage_receipt_id
        or (f"shortlist-{question_family_id}" if failure_class else ""),
        novelty_direct_recap=novelty_direct_recap,
        reason=reason,
    )


def is_development_surrogate(
    config: MaieusisProjectConfig,
    *,
    front_half_receipts: Sequence[PromotionReceipt],
    dossier_statuses: Sequence[FamilyDossierStatus] = (),
) -> bool:
    """F1: the run is dev-surrogate (never independently reviewed) if ANY reviewer ran mock.

    Signals: demo mode (all mock), any MOCK front-half receipt, or any development-surrogate dossier
    status from the back half. Standard with live reviewers ⇒ False.
    """
    if config.is_demo or any_mock_reviewer(front_half_receipts):
        return True
    return any(s in DEVELOPMENT_SURROGATE_STATUSES for s in dossier_statuses)


def run_stage_c(
    *,
    run_corpus: Path,
    intent_path: Path,
    dataset_id: str,
    provisional_inspiration: bool = False,
) -> Path:
    """Stage C: build + persist the V2 Question Scientist context from the RUN-LOCAL reviewed corpus.

    ``build_question_scientist_context_payload_v2`` runs ``assert_question_scientist_inputs_are_reviewed``
    internally — it MUST pass with ZERO human import (the run-local corpus carries only AI_REVIEWED /
    AUTOMATED_REVIEWED artifacts). Returns the written payload path.
    """
    from ..context.question_scientist_export import (
        build_question_scientist_context_payload_v2,
        write_question_scientist_context_payload_v2,
    )

    payload = build_question_scientist_context_payload_v2(
        corpus_root=run_corpus,
        intent_path=intent_path,
        dataset_id=dataset_id,
        provisional_inspiration=provisional_inspiration,
    )
    return write_question_scientist_context_payload_v2(payload, corpus_root=run_corpus)


# The gap/strong-claim sources the OA fulltext plus-on targets (what the old vetoes covered).
_FULLTEXT_TARGET_CLAIM_STATUSES = {
    TopicEvidenceClaimStatus.OPEN_QUESTION,
    TopicEvidenceClaimStatus.ESTABLISHED,
    TopicEvidenceClaimStatus.CONTESTED,
}


@dataclass
class DatasetHalfResult:
    receipts: list[PromotionReceipt]
    narrative: DatasetNarrative
    topic_brief: TopicEvidenceBrief
    lane_coverage: dict[str, int]
    source_count: int
    scope: ResolvedResearchScope
    fulltext_counts: FulltextEnrichmentCounts
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED
    source_activity_path: Path | None = None


def _scope_identity(scope: ResolvedResearchScope) -> tuple[str, str]:
    digest = stable_hash(scope)
    scope_id = (
        scope.inferred_scope.scope_id
        if scope.inferred_scope is not None
        else f"resolved-scope-{digest[:12]}"
    )
    return scope_id, digest


def _persist_early_dataset_products(
    *,
    run_corpus: Path,
    narrative: DatasetNarrative,
    intent: ResearchIntent,
    scope: ResolvedResearchScope | None = None,
) -> None:
    context = _run_context_for_corpus(run_corpus)
    if context is None:
        return
    narrative_path = write_dataset_narrative(context.paths, narrative)
    index_existing_artifact(
        context,
        narrative_path,
        kind=ArtifactKind.DATASET_NARRATIVE,
        processing_state=ProductProcessingState.PRODUCED,
        authority=authority_from_status(narrative.review_status),
    )
    if scope is not None:
        scope_path = write_research_scope_product(
            context.paths,
            intent=intent,
            scope=scope,
        )
        index_existing_artifact(
            context,
            scope_path,
            kind=ArtifactKind.RESEARCH_SCOPE,
            processing_state=ProductProcessingState.PRODUCED,
            authority=ArtifactAuthority.PROVISIONAL,
        )


def _persist_dataset_source_activity(
    *,
    config: MaieusisProjectConfig,
    run_corpus: Path,
    narrator_result: NarratorResult,
    narrative: DatasetNarrative,
    scope: ResolvedResearchScope,
    topic_table: R5TopicEvidenceSourceTable | None = None,
    topic_status: SourceActivityStatus = SourceActivityStatus.INACTIVE,
    topic_detail: str = "not assessed",
) -> Path:
    narrative_path = reviewed_dataset_narrative_path(narrative.dataset_id, corpus_root=run_corpus)
    run_root = run_corpus.parent
    narrative_relative = narrative_path.relative_to(run_root).as_posix()
    narrative_artifacts = [narrative_relative]
    narrative_digests = {narrative_relative: sha256_file(narrative_path)}
    docs = [Path(raw) for raw in config.dataset.seed.docs]
    digestable_docs = [path for path in docs if path.is_file()]
    doc_paths = [str(path) for path in digestable_docs]
    doc_digests = {str(path): sha256_file(path) for path in digestable_docs}
    documentation_produced = SourceKind.DOCUMENTATION in narrator_result.sources
    user_description_produced = SourceKind.USER_DESCRIPTION in narrator_result.sources
    documentation_status = (
        SourceActivityStatus.PRODUCED
        if documentation_produced
        else (
            SourceActivityStatus.FAILED
            if config.dataset.seed.link
            else SourceActivityStatus.INACTIVE
        )
    )
    user_description_status = (
        SourceActivityStatus.PRODUCED
        if user_description_produced
        else (SourceActivityStatus.FAILED if docs else SourceActivityStatus.INACTIVE)
    )
    source_items = [
        SourceActivityItem(
            source_id=SourceKind.DOCUMENTATION.value,
            status=documentation_status,
            input_paths=(
                [config.dataset.seed.link]
                if config.dataset.seed.link
                and documentation_status != SourceActivityStatus.INACTIVE
                else []
            ),
            input_digests=(
                {config.dataset.seed.link: stable_hash(config.dataset.seed.link)}
                if config.dataset.seed.link
                and documentation_status != SourceActivityStatus.INACTIVE
                else {}
            ),
            artifact_paths=narrative_artifacts if documentation_produced else [],
            artifact_digests=narrative_digests if documentation_produced else {},
            detail=narrator_result.skipped.get(
                SourceKind.DOCUMENTATION.value,
                "produced" if documentation_produced else "failed",
            ),
        ),
        SourceActivityItem(
            source_id=SourceKind.USER_DESCRIPTION.value,
            status=user_description_status,
            input_paths=(
                doc_paths if user_description_status != SourceActivityStatus.INACTIVE else []
            ),
            input_digests=(
                doc_digests if user_description_status != SourceActivityStatus.INACTIVE else {}
            ),
            artifact_paths=narrative_artifacts if user_description_produced else [],
            artifact_digests=narrative_digests if user_description_produced else {},
            detail=narrator_result.skipped.get(
                SourceKind.USER_DESCRIPTION.value,
                "configured user documentation" if docs else "inactive: no user docs supplied",
            ),
        ),
        SourceActivityItem(
            source_id=SourceKind.MODEL_RESEARCH.value,
            status=(
                SourceActivityStatus.PRODUCED
                if SourceKind.MODEL_RESEARCH in narrator_result.sources
                else SourceActivityStatus.INACTIVE
            ),
            artifact_paths=narrative_artifacts
            if SourceKind.MODEL_RESEARCH in narrator_result.sources
            else [],
            artifact_digests=narrative_digests
            if SourceKind.MODEL_RESEARCH in narrator_result.sources
            else {},
            detail=narrator_result.skipped.get(SourceKind.MODEL_RESEARCH.value, "produced"),
        ),
    ]
    topic_paths: list[str] = []
    topic_digests: dict[str, str] = {}
    if topic_table is not None and topic_status != SourceActivityStatus.INACTIVE:
        topic_path = (
            run_corpus
            / "context"
            / "topic_evidence"
            / "sources"
            / "research_intent.topic_source_table.yaml"
        )
        if topic_path.is_file():
            topic_relative = topic_path.relative_to(run_root).as_posix()
            topic_paths = [topic_relative]
            topic_digests = {topic_relative: sha256_file(topic_path)}
    source_items.append(
        SourceActivityItem(
            source_id="topic_literature",
            status=topic_status,
            artifact_paths=topic_paths,
            artifact_digests=topic_digests,
            detail=topic_detail,
        )
    )
    scope_id, scope_digest = _scope_identity(scope)
    supporting_count = (
        sum(1 for record in topic_table.records if record.can_support_claims)
        if topic_table is not None
        else 0
    )
    activity = DatasetSourceActivity(
        activity_id=f"dataset-source-activity-{stable_hash({'dataset': narrative.dataset_id, 'scope': scope_digest})[:12]}",
        dataset_id=narrative.dataset_id,
        scope_id=scope_id,
        scope_digest=scope_digest,
        sources=source_items,
        topic_record_count=len(topic_table.records) if topic_table is not None else 0,
        topic_claim_supporting_count=supporting_count,
        topic_lane_coverage=dict(topic_table.lane_coverage) if topic_table is not None else {},
    )
    path = run_corpus / "context" / "dataset_narratives" / "source_activity.yaml"
    context = _run_context_for_corpus(run_corpus)
    if context is not None:
        promote_model_artifact(
            context,
            value=activity,
            destination=path,
            kind=ArtifactKind.SOURCE_ACTIVITY,
            processing_state=(
                ProductProcessingState.PRODUCED
                if topic_status == SourceActivityStatus.PRODUCED
                else ProductProcessingState.DEGRADED
            ),
            authority=ArtifactAuthority.PROVISIONAL,
        )
    else:
        dump_data(activity, path)
    return path


def run_dataset_half(
    config: MaieusisProjectConfig,
    *,
    executor: StageExecutor,
    run_corpus: Path,
    intent: ResearchIntent,
    reviewed_patterns: Sequence[QuestionPatternCard] = (),
    scope: ResolvedResearchScope | None = None,
    topic_source_table: TopicSourceTable | None = None,
    topic_r5_source_table: R5TopicEvidenceSourceTable | None = None,
) -> DatasetHalfResult:
    """Dataset half: fuse+review the DatasetNarrative (Sources A/B/C/D) and the TopicEvidenceBrief.

    Both land AI/AUTOMATED-authority artifacts at the exact stage-C corpus paths, ZERO human import.
    The topic source table is INJECTED (generic-lane retrieval + web search happen upstream of this
    seam); the topic-evidence gate compares its generic ``required_lanes`` against the source table's
    own generic-lane coverage. ``topic_r5_source_table`` lets the retrieval layer supply an already
    fulltext-ENRICHED topic table (``build_r5_topic_source_table`` alone yields abstract-only records, which
    stage C rejects for open-gap support); it must cover the same source ids the brief cites. Returns the
    topic-evidence F2 receipt so DP-5 can refuse a mock-reviewed brief before the shortlist handoff.
    """
    # Narrator and topic evidence each ride their OWN configured role model.
    narrator_provider = executor.generation_provider("narrator")
    narrator_gen_ids = [narrator_provider.provider_id]
    topic_provider = executor.generation_provider("topic")
    topic_gen_ids = [topic_provider.provider_id]

    # Narrator: gather A (+ D/C/B when available) → fuse → independent fidelity gate → AUTOMATED persist.
    seed = DatasetSeed(
        dataset_id=config.dataset.seed.dataset_id,
        link=config.dataset.seed.link,
        docs=list(config.dataset.seed.docs),
    )
    narrator_result = gather_and_fuse_dataset_narrative(
        seed=seed,
        doc_provider=narrator_provider,
        web_search_provider=executor.web_search_provider(),
        reviewer_session=executor.gate_session(
            gate_name="narrative_fidelity", generator_provider_ids=narrator_gen_ids
        ),
    )
    # Q3: promote (fail-closed) INSIDE the try so a revise/reject verdict writes its diagnostic BEFORE
    # the raise. The old order persisted (which promotes internally) BEFORE the try, so on a non-accept
    # the raise fired first and the diagnostic-writing block below was dead. Persist only AFTER a
    # successful promote (the accept path); the re-raise then flows into the dataset-half terminal (Q2).
    try:
        narrative = promote_narrator_result_to_reviewed(narrator_result)
    except ValueError as exc:
        # Surface-only: the narrative gate stays fail-closed; persist WHY from its review content
        # (its reviewer uses accept/revise/reject — string-identical to GateDecision).
        review = narrator_result.review
        if review is not None:
            diagnostic = GateDiagnostic(
                gate_name="narrative_fidelity",
                decision=GateDecision(review.decision.value),
                rationale=review.rationale,
                failed_criteria=[a.criterion for a in review.criterion_assessments if not a.passed],
                returned_criteria=[a.criterion for a in review.criterion_assessments],
            )
            write_gate_diagnostic(diagnostic, _diagnostics_dir(run_corpus))
        raise ValueError(f"{exc} | narrative-fidelity gate diagnostics persisted") from exc
    persist_reviewed_narrator_result(narrator_result, corpus_root=run_corpus)
    _persist_early_dataset_products(
        run_corpus=run_corpus,
        narrative=narrative,
        intent=intent,
    )

    # Topic evidence: draft bundle → independent topic-evidence gate → AI_REVIEWED persist.
    resolved_scope = scope or resolve_research_scope(
        intent,
        reviewed_patterns=reviewed_patterns,
        dataset_narrative=narrative,
    )
    _persist_early_dataset_products(
        run_corpus=run_corpus,
        narrative=narrative,
        intent=intent,
        scope=resolved_scope,
    )
    source_activity_path = _persist_dataset_source_activity(
        config=config,
        run_corpus=run_corpus,
        narrator_result=narrator_result,
        narrative=narrative,
        scope=resolved_scope,
    )
    resolved_topic_source_table = topic_source_table or retrieve_topic_source_table(
        config, resolved_scope
    )
    bundle = build_topic_evidence_brief_draft_bundle(
        provider=topic_provider,
        intent=intent,
        source_table=resolved_topic_source_table,
        scope=resolved_scope,
    )
    r5_table = (
        topic_r5_source_table
        or bundle.r5_source_table
        or build_r5_topic_source_table(bundle.source_table)
    )
    # OA fulltext plus-on (never a gate): for the sources that support open gaps / strong claims, attempt
    # a legal OA excerpt. On success the record upgrades to FULLTEXT_EXCERPT (its evidence_basis then
    # reads fulltext_backed); on failure it stays abstract-only and the attempt is tallied. A fetch
    # failure is NEVER a run failure. Runs before the brief so the source_table_digest reflects it.
    target_source_ids = {
        source_id
        for claim in bundle.recommended_brief.claims
        if claim.status in _FULLTEXT_TARGET_CLAIM_STATUSES
        for source_id in (claim.source_record_ids or claim.source_refs)
    }
    enriched_records, fulltext_counts = enrich_records_with_fulltext(
        r5_table.records,
        fetcher=executor.fulltext_fetcher(),
        target_source_ids=target_source_ids,
    )
    r5_table = r5_table.model_copy(update={"records": enriched_records})
    # The bundle's recommended brief carries no provenance (it is attached on the human review-pack
    # path, which this AI-gate path bypasses); stamp the real generation provenance so stage C accepts.
    brief = bundle.recommended_brief.model_copy(
        update={
            "prompt_version": TOPIC_EVIDENCE_BRIEF_SYNTHESIZER_PROMPT_VERSION,
            "provider_id": topic_provider.provider_id,
            "model_id": getattr(topic_provider, "model_name", "") or topic_provider.provider_id,
            "input_digest": bundle.input_digest,
            "source_table_digest": stable_hash(r5_table),
        }
    )
    source_ids = {record.source_record_id for record in r5_table.records}
    topic_root = run_corpus / "context" / "topic_evidence"
    provisional_brief_path = dump_data(
        brief,
        topic_root / "research_intent.topic_evidence_brief.yaml",
    )
    source_table_path = dump_data(
        r5_table,
        topic_root / "sources" / "research_intent.topic_source_table.yaml",
    )
    # D5(a) + Q1: the gate must see the REAL claim-supporting classification (not a blanket True) AND
    # the SAME scope-driven off-topic view the compiler's blocked-source check uses, so a genuinely
    # weak OR off-scope brief earns an honest gate reject/revise (with diagnostic) at the dataset-half
    # boundary instead of a raw stage-C readiness/blocked-source crash after the spend.
    claim_supporting_ids = claim_supporting_source_ids(r5_table, resolved_scope)
    if not source_ids or not claim_supporting_ids:
        empty_harvest = not source_ids
        source_activity_path = _persist_dataset_source_activity(
            config=config,
            run_corpus=run_corpus,
            narrator_result=narrator_result,
            narrative=narrative,
            scope=resolved_scope,
            topic_table=r5_table,
            topic_status=(
                SourceActivityStatus.EMPTY if empty_harvest else SourceActivityStatus.PARTIAL
            ),
            topic_detail=(
                "no source-bound topic literature was available"
                if empty_harvest
                else "source-bound topic literature had no claim-supporting records"
            ),
        )
        diagnostic_path = write_gate_diagnostic(
            GateDiagnostic(
                gate_name=_TOPIC_EVIDENCE_AVAILABILITY_DIAGNOSTIC,
                decision=GateDecision.INSUFFICIENT_EVIDENCE,
                rationale="topic harvest contained no claim-supporting source-bound records",
            ),
            _diagnostics_dir(run_corpus),
        )
        context = _run_context_for_corpus(run_corpus)
        if context is not None:
            index_existing_artifact(
                context,
                provisional_brief_path,
                kind=ArtifactKind.TOPIC_EVIDENCE,
                processing_state=ProductProcessingState.DEGRADED,
                authority=ArtifactAuthority.PROVISIONAL,
            )
            index_existing_artifact(
                context,
                source_table_path,
                kind=ArtifactKind.TOPIC_EVIDENCE,
                processing_state=ProductProcessingState.DEGRADED,
                authority=ArtifactAuthority.PROVISIONAL,
            )
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.SCIENTIFIC,
                code="topic_evidence_empty",
                public_message="No source-bound topic literature was available for question development.",
                internal_path=diagnostic_path.relative_to(context.paths.root).as_posix(),
            )
        return DatasetHalfResult(
            receipts=[],
            narrative=narrative,
            topic_brief=brief,
            lane_coverage=dict(r5_table.lane_coverage),
            source_count=len(r5_table.records),
            scope=resolved_scope,
            fulltext_counts=fulltext_counts,
            authority_ceiling=FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION,
            source_activity_path=source_activity_path,
        )
    ready, readiness_issues = evaluate_topic_evidence_readiness(
        brief,
        source_record_ids=source_ids,
        claim_supporting_record_ids=claim_supporting_ids,
    )
    failed_lanes = [
        lane for lane in GENERIC_REQUIRED_LANES if r5_table.lane_coverage.get(lane, 0) == 0
    ]
    if not ready or failed_lanes:
        diagnostic_path = write_gate_diagnostic(
            GateDiagnostic(
                gate_name=_TOPIC_EVIDENCE_PROVISIONAL_DIAGNOSTIC,
                decision=GateDecision.INSUFFICIENT_EVIDENCE,
                rationale="; ".join(
                    [
                        *readiness_issues,
                        *(
                            ["partial generic-lane coverage: " + ", ".join(failed_lanes)]
                            if failed_lanes
                            else []
                        ),
                    ]
                ),
            ),
            _diagnostics_dir(run_corpus),
        )
        source_activity_path = _persist_dataset_source_activity(
            config=config,
            run_corpus=run_corpus,
            narrator_result=narrator_result,
            narrative=narrative,
            scope=resolved_scope,
            topic_table=r5_table,
            topic_status=SourceActivityStatus.PARTIAL,
            topic_detail="partial source-bound topic literature; provisional inspiration only",
        )
        context = _run_context_for_corpus(run_corpus)
        if context is not None:
            index_existing_artifact(
                context,
                provisional_brief_path,
                kind=ArtifactKind.TOPIC_EVIDENCE,
                processing_state=ProductProcessingState.DEGRADED,
                authority=ArtifactAuthority.PROVISIONAL,
            )
            index_existing_artifact(
                context,
                source_table_path,
                kind=ArtifactKind.TOPIC_EVIDENCE,
                processing_state=ProductProcessingState.DEGRADED,
                authority=ArtifactAuthority.PROVISIONAL,
            )
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.SCIENTIFIC,
                code="topic_evidence_provisional",
                public_message=(
                    "Partial topic literature is retained for provisional inspiration only."
                ),
                internal_path=diagnostic_path.relative_to(context.paths.root).as_posix(),
            )
        return DatasetHalfResult(
            receipts=[],
            narrative=narrative,
            topic_brief=brief,
            lane_coverage=dict(r5_table.lane_coverage),
            source_count=len(r5_table.records),
            scope=resolved_scope,
            fulltext_counts=fulltext_counts,
            authority_ceiling=FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION,
            source_activity_path=source_activity_path,
        )
    outcome = review_topic_evidence(
        session=executor.gate_session(
            gate_name="topic_evidence", generator_provider_ids=topic_gen_ids
        ),
        brief=brief,
        scope=resolved_scope,
        source_record_ids=source_ids,
        claim_supporting_record_ids=claim_supporting_ids,
        lane_coverage=r5_table.lane_coverage,
        research_intent=intent.model_dump(mode="json"),
        source_record_summaries=[
            {
                "source_record_id": record.source_record_id,
                "can_support_claims": record.can_support_claims,
            }
            for record in r5_table.records
        ],
        generator_provider_ids=topic_gen_ids,
    )
    try:
        promoted = promote_topic_evidence_to_ai_reviewed(
            brief, outcome
        )  # fail-closed on non-accept
    except ValueError as exc:
        # Surface-only: the gate stays fail-closed (assert_promotion_binding raised); persist WHY
        # (reviewer verdict + deterministic readiness + lane coverage) so a crashed run leaves a
        # trace, and re-raise with the same content in the message.
        diagnostic = build_topic_evidence_gate_diagnostic(
            outcome,
            brief,
            source_record_ids=source_ids,
            claim_supporting_record_ids=claim_supporting_ids,
            lane_coverage=r5_table.lane_coverage,
        )
        # run_corpus is runs/<id>/corpus (RunLayout.corpus) → runs/<id>/diagnostics/.
        diagnostic_path = run_corpus.parent / "diagnostics" / "topic_evidence_gate.yaml"
        dump_data(diagnostic, diagnostic_path)
        raise ValueError(
            f"{exc} | {diagnostic.summary_line()} | diagnostic persisted: {diagnostic_path}"
        ) from exc
    receipt = build_promotion_receipt(
        candidate=brief,
        outcome=outcome,
        artifact_kind="topic_evidence",
        expected_gate="topic_evidence",
    )
    persist_reviewed_topic_evidence(promoted, r5_table, corpus_root=run_corpus)
    source_activity_path = _persist_dataset_source_activity(
        config=config,
        run_corpus=run_corpus,
        narrator_result=narrator_result,
        narrative=narrative,
        scope=resolved_scope,
        topic_table=r5_table,
        topic_status=SourceActivityStatus.PRODUCED,
        topic_detail="reviewed topic literature produced",
    )
    return DatasetHalfResult(
        receipts=[receipt],
        narrative=narrative,
        topic_brief=promoted,
        lane_coverage=dict(r5_table.lane_coverage),
        source_count=len(r5_table.records),
        scope=resolved_scope,
        fulltext_counts=fulltext_counts,
        source_activity_path=source_activity_path,
    )


def assert_front_half_product_grade(receipts: Sequence[PromotionReceipt]) -> None:
    """DP-5: Standard refuses a mock-reviewed front-half artifact before the shortlist→orchestrator handoff."""
    for receipt in receipts:
        assert_product_grade_promotion(receipt)


def novelty_not_assessed(
    family: QuestionFamily, active_ids: Sequence[str]
) -> list[VariantNoveltyResult]:
    """Default product result when no nearest-prior search ran: explicitly not assessed."""
    from ...schemas.variant_novelty import VariantNoveltyStatus

    seed_by_variant = {v.variant_id: v.question_seed_id for v in family.variants}
    return [
        VariantNoveltyResult(
            variant_id=variant_id,
            question_seed_id=seed_by_variant.get(variant_id, ""),
            status=VariantNoveltyStatus.NOT_ASSESSED,
            rationale="Novelty was not assessed because no search ran.",
            retrieval_enabled=False,
        )
        for variant_id in active_ids
    ]


def _initialize_family_products(context: RunContext, batch: QuestionFamilyBatch) -> None:
    """Index the complete clean batch and give every family an immediate fallback product."""
    family_ids = {family.question_family_id for family in batch.families}
    existing = {item.family_id: item for item in load_run_manifest(context.paths).families}

    def _reconcile(_path: Path) -> None:
        reconcile_family_inventory(context, current_family_ids=family_ids)

    promote_model_artifact(
        context,
        value=batch,
        destination=context.paths.question_family_batch_artifact,
        kind=ArtifactKind.QUESTION_FAMILY_BATCH,
        processing_state=ProductProcessingState.PRODUCED,
        authority=ArtifactAuthority.PROVISIONAL,
        source_context_digest=batch.context_digest,
        after_index=_reconcile,
    )
    for family in batch.families:
        if family.question_family_id in existing:
            continue
        upsert_family_disposition(
            context,
            FamilyDisposition(
                family_id=family.question_family_id,
                title=family.title,
                authority=(
                    ArtifactAuthority.PROVISIONAL
                    if batch.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
                    else authority_from_status(family.review_status)
                ),
                reason="Awaiting automated shortlist review.",
            ),
        )
    for family in batch.families:
        if family.question_family_id in existing:
            continue
        disposition = next(
            item
            for item in load_run_manifest(context.paths).families
            if item.family_id == family.question_family_id
        )
        write_family_fallback(context, family=family, disposition=disposition)
    # Publish the aggregate view only after every newly persisted family has a manifest row and
    # immediate fallback. If this projection fails, the strict batch remains honestly usable and
    # no family disappears from the run inventory merely because a derived Markdown view failed.
    promote_text_artifact(
        context,
        text=render_question_families(
            batch.families,
            authority_ceiling=batch.authority_ceiling,
            planning_eligible=True,
        ),
        destination=context.paths.question_families,
        kind=ArtifactKind.QUESTION_FAMILIES_VIEW,
        processing_state=ProductProcessingState.PRODUCED,
        authority=ArtifactAuthority.PROVISIONAL,
        source_context_digest=batch.context_digest,
    )


def _family_shortlist_disposition(outcome: FamilyShortlistOutcome) -> FamilyShortlistDisposition:
    if outcome.is_included:
        return FamilyShortlistDisposition.SHORTLISTED
    if outcome.label == FamilyInclusionLabel.REJECTED_SCIENTIFIC:
        return FamilyShortlistDisposition.REJECTED
    if outcome.label in {
        FamilyInclusionLabel.DEFERRED_MATERIAL_REVISION,
        FamilyInclusionLabel.REVISION_BUDGET_EXHAUSTED,
    }:
        return FamilyShortlistDisposition.NEEDS_REVISION
    return FamilyShortlistDisposition.DEFERRED


def _project_shortlist_products(
    context: RunContext,
    *,
    batch: QuestionFamilyBatch,
    outcomes: Sequence[FamilyShortlistOutcome],
    shortlist_path: Path,
    development_surrogate: bool,
) -> None:
    by_id = {outcome.question_family_id: outcome for outcome in outcomes}
    shortlist_authority = (
        ArtifactAuthority.PROVISIONAL
        if development_surrogate
        or batch.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
        else ArtifactAuthority.AGENT_REVIEWED
    )
    shortlist = load_model(shortlist_path, QuestionFamilyShortlistManifest)
    promote_model_artifact(
        context,
        value=shortlist,
        destination=context.paths.shortlist_artifact,
        kind=ArtifactKind.SHORTLIST,
        processing_state=ProductProcessingState.PRODUCED,
        authority=shortlist_authority,
        source_context_digest=shortlist.context_digest,
    )
    for family in batch.families:
        outcome = by_id[family.question_family_id]
        disposition = next(
            item
            for item in load_run_manifest(context.paths).families
            if item.family_id == family.question_family_id
        )
        disposition.shortlist = _family_shortlist_disposition(outcome)
        disposition.reason = f"Automated shortlist disposition: {outcome.label.value}."
        current_dossier = next(
            (
                item
                for item in load_run_manifest(context.paths).artifacts
                if item.family_id == family.question_family_id
                and item.kind == ArtifactKind.FAMILY_DOSSIER
            ),
            None,
        )
        if not outcome.is_included or (
            current_dossier is None
            or current_dossier.processing_state != ProductProcessingState.PRODUCED
        ):
            write_family_fallback(context, family=family, disposition=disposition)
        else:
            upsert_family_disposition(context, disposition)
    promote_text_artifact(
        context,
        text=render_shortlist(
            outcomes,
            authority_ceiling=shortlist.authority_ceiling,
            planning_eligible=shortlist.planning_eligible,
        ),
        destination=context.paths.shortlist,
        kind=ArtifactKind.SHORTLIST_VIEW,
        processing_state=ProductProcessingState.PRODUCED,
        authority=shortlist_authority,
        source_context_digest=shortlist.context_digest,
    )


def run_stage_d(
    payload_path: Path,
    *,
    executor: StageExecutor,
    run_corpus: Path,
    novelty_fn: Callable[[QuestionFamily, Sequence[str]], list[VariantNoveltyResult]] = (
        novelty_not_assessed
    ),
    family_count: int = 6,
    variants_per_family: int = 3,
) -> Path:
    """D: generate families → per-active-variant novelty → shortlist gate → persist the manifest.

    ``novelty_fn`` computes the per-variant nearest-prior results (DEC-2; the driver passes a config-gated
    retrieval, Standard-on/demo-off). Persists to the RUN-LOCAL corpus (the orchestrator loads it).
    """
    payload = load_model(payload_path, QuestionScientistContextPayloadV2)
    generator = executor.generation_provider("questioner")
    gen_ids = [generator.provider_id]
    retry_failures: list[str] = []
    context = _run_context_for_corpus(run_corpus)

    def _persist_valid_batch(valid_batch: QuestionFamilyBatch) -> None:
        write_question_family_batch(valid_batch, corpus_root=run_corpus)
        if context is not None:
            _initialize_family_products(context, valid_batch)

    def _family_dropped(family_id: str, reasons: list[str]) -> None:
        # D6: a family dropped for a quality blocker (or an under-count shape note) is recorded, never
        # silently lost — it never reaches the shortlist.
        diagnostic_path = write_gate_diagnostic(
            GateDiagnostic(
                gate_name=_QUESTION_FAMILY_GENERATION_DIAGNOSTIC,
                artifact_label=family_id,
                decision=GateDecision.REJECT if family_id != "shape" else GateDecision.REVISE,
                rationale="dropped from shortlist: " + "; ".join(reasons),
            ),
            _diagnostics_dir(run_corpus),
        )
        context = _run_context_for_corpus(run_corpus)
        if context is not None:
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.SCIENTIFIC,
                code="family_candidate_dropped",
                public_message="A generated family candidate failed strict quality validation.",
                internal_path=diagnostic_path.relative_to(context.paths.root).as_posix(),
            )

    def _retry_failed(kind: str) -> None:
        retry_failures.append(kind)
        diagnostic_path = write_gate_diagnostic(
            GateDiagnostic(
                gate_name=_QUESTION_FAMILY_RETRY_DIAGNOSTIC,
                decision=GateDecision.INFRASTRUCTURE_FAILURE,
                rationale=f"optional count-target retry failed: {kind}; first valid batch retained",
            ),
            _diagnostics_dir(run_corpus),
        )
        context = _run_context_for_corpus(run_corpus)
        if context is not None:
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.INFRASTRUCTURE,
                code="question_family_retry_failed",
                public_message=(
                    "An optional family-count retry failed; the first valid family batch was retained."
                ),
                internal_path=diagnostic_path.relative_to(context.paths.root).as_posix(),
            )

    batch = generate_question_family_batch(
        provider=generator,
        context_payload=payload,
        family_count=family_count,
        variants_per_family=variants_per_family,
        on_family_dropped=_family_dropped,
        on_retry_failed=_retry_failed,
        on_valid_batch=_persist_valid_batch,
    )
    # Required ordering: the clean strict batch is durable before ANY novelty/shortlist call.
    batch_path = write_question_family_batch(batch, corpus_root=run_corpus)
    user_packet = build_question_family_user_packet(
        payload,
        family_count=family_count,
        variants_per_family=variants_per_family,
        provider_id=generator.provider_id,
    )
    quality_report = build_question_family_quality_report(
        batch,
        allowed_pattern_ids=user_packet["allowed_pattern_ids"],
        allowed_topic_claim_ids=user_packet["allowed_topic_claim_ids"],
        allowed_topic_pack_ids=user_packet.get("allowed_topic_pack_ids"),
        allowed_dataset_context_ids=user_packet["allowed_dataset_context_ids"],
    )
    write_question_family_quality_report(quality_report, corpus_root=run_corpus)
    if context is not None:
        _initialize_family_products(context, batch)
    results: list[tuple[FamilyShortlistOutcome, QuestionFamily | None]] = []

    def _shortlist_diagnostic(outcome: GateOutcome, family_id: str) -> None:
        diagnostic_path = _record_non_accept_diagnostic(
            outcome,
            SHORTLIST_WORTHINESS_CRITERIA,
            run_corpus=run_corpus,
            artifact_label=family_id,
        )
        if context is not None and diagnostic_path is not None:
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.SCIENTIFIC,
                code="shortlist_family_not_accepted",
                public_message="The automated shortlist review did not include this family.",
                internal_path=diagnostic_path.relative_to(context.paths.root).as_posix(),
                family_id=family_id,
            )

    for family in batch.families:
        active_ids = [variant.variant_id for variant in family.variants]
        family_warnings = [
            warning.message
            for warning in quality_report.warnings
            if not warning.question_family_id
            or warning.question_family_id == family.question_family_id
        ]
        try:
            result = run_automated_family_shortlist(
                family,
                session=executor.gate_session(
                    gate_name="shortlist_worthiness", generator_provider_ids=gen_ids
                ),
                active_variant_ids=active_ids,
                novelty_results=novelty_fn(family, active_ids),
                generator_provider_ids=gen_ids,
                review_guidance=(
                    "Mechanical quality findings are advisory review inputs: "
                    + "; ".join(family_warnings)
                    if family_warnings
                    else ""
                ),
                on_gate_outcome=functools.partial(
                    _shortlist_diagnostic, family_id=family.question_family_id
                ),
            )
        except (
            StructuredModelProviderError,
            ModelConfigurationError,
            ScientificAgentInfrastructureError,
        ) as exc:
            setattr(
                exc,
                _STAGE_D_CURRENT_BATCH_ATTRIBUTE,
                batch_path.relative_to(run_corpus.parent).as_posix(),
            )
            raise
        results.append(result)
    manifest = build_shortlist_manifest(
        results,
        batch_id=batch.batch_id,
        context_id=payload.context_id,
        context_digest=payload.context_digest,
        authority_ceiling=batch.authority_ceiling,
    )
    shortlist_path = persist_shortlist_manifest(manifest, corpus_root=run_corpus)
    if context is not None:
        _project_shortlist_products(
            context,
            batch=batch,
            outcomes=[outcome for outcome, _family in results],
            shortlist_path=shortlist_path,
            development_surrogate=generator.provider_id.startswith("mock"),
        )
    outcome_path = run_corpus.parent / "stage_outputs" / "stage-d.yaml"
    prior_diagnostics = [
        path.relative_to(run_corpus.parent).as_posix()
        for path in sorted(_diagnostics_dir(run_corpus).glob("stage_d_terminal*.yaml"))
    ]
    dump_data(
        StageDOutcomeRecord(
            outcome_id=f"stage-d-outcome-{payload.context_digest[:12]}",
            context_id=payload.context_id,
            context_digest=payload.context_digest,
            stage_status=StageStatus.COMPLETE,
            processed_candidates=[
                StageDProcessedCandidate(
                    question_family_id=family.question_family_id,
                    disposition=StageDCandidateDisposition.RETAINED,
                )
                for family in batch.families
            ],
            retained_batch_path=batch_path.relative_to(run_corpus.parent).as_posix(),
            retained_batch_digest=sha256_file(batch_path),
            superseded_diagnostic_paths=prior_diagnostics,
        ),
        outcome_path,
    )
    return shortlist_path


# --- stage-boundary execution (5c-1c): each stage emits a REAL receipt + persists its outputs ------
def _emit_stage_receipt(
    paths: RunPaths,
    config: MaieusisProjectConfig,
    stage: str,
    *,
    input_digests: dict[str, str],
    output_paths: Sequence[Path],
    family_count: int = 6,
    variants_per_family: int = 3,
    status: StageStatus = StageStatus.COMPLETE,
    failure_class: FailureClass | None = None,
    detail: str = "",
) -> StageReceipt:
    """Write the stage's receipt: input digests + config/model slices + output digests.

    Defaults to a COMPLETE receipt; ``status``/``failure_class``/``detail`` let a stage record an
    honest terminal (e.g. a SCIENTIFIC_TERMINAL paper half that accepted zero papers) instead of
    reporting COMPLETE and letting a downstream stage crash. ``summary.md`` and resume receipts are
    never listed here — they are regenerated projections.
    """
    output_digests = relative_output_digests(paths.root, output_paths)
    receipt = StageReceipt(
        stage_name=stage,
        status=status,
        input_digests=dict(sorted(input_digests.items())),
        config_version=stage_config_version(
            config, stage, family_count=family_count, variants_per_family=variants_per_family
        ),
        prompt_versions=stage_prompt_versions(stage),
        model_versions=stage_model_versions(config, stage),
        output_paths=sorted(output_digests),
        output_digests=output_digests,
        failure_class=failure_class,
        detail=detail,
        ended_at=datetime.now(UTC),
    )
    receipt_path = write_stage_receipt(paths, receipt)
    if paths.run_manifest.is_file() and stage in {item.value for item in RunStage}:
        state = {
            StageStatus.COMPLETE: ProductProcessingState.PRODUCED,
            StageStatus.SCIENTIFIC_TERMINAL: ProductProcessingState.DEGRADED,
            StageStatus.INFRASTRUCTURE_FAILED: ProductProcessingState.FAILED,
            StageStatus.EXTERNAL_CALL_UNCERTAIN: ProductProcessingState.FAILED,
        }.get(status, ProductProcessingState.NOT_REACHED)
        set_stage_state(
            RunContext(run_id=paths.root.name, paths=paths),
            RunStage(stage),
            state,
            receipt_path=receipt_path.relative_to(paths.root).as_posix(),
        )
    return receipt


def exec_stage_paper_half(
    config: MaieusisProjectConfig,
    executor: StageExecutor,
    paths: RunPaths,
    drafts: Sequence[PaperCaseDraft],
    *,
    input_digests: dict[str, str] | None = None,
) -> PaperHalfResult:
    """Stage A boundary: run the paper half, persist its typed stage output, emit the receipt.

    ``input_digests`` lets the CLI path record the inbox-PDF digests (recomputable on resume WITHOUT
    re-paying ingestion); the injected-drafts path records per-draft digests.
    """
    result = run_paper_half(
        drafts,
        executor=executor,
        run_corpus=paths.corpus,
        max_workers=config.paperbank.max_workers,
        max_revise_rounds=config.run.max_revise_rounds,
        citation_prompt_char_budget=config.paperbank.citation_prompt_char_budget,
    )
    stage_output_path = dump_data(
        PaperHalfStageOutput(
            gate_result=result.gate_result,
            accepted=result.accepted,
            traces=result.reviewed_traces,
            patterns=result.reviewed_patterns,
            pattern_revision_history=result.pattern_revision_history,
            receipts=result.receipts,
        ),
        paths.stage_output(STAGE_PAPER_HALF),
    )
    # Honest terminal: zero accepted papers ⇒ no patterns ⇒ nothing downstream can develop. Record a
    # SCIENTIFIC_TERMINAL receipt (not COMPLETE) so the run stops honestly instead of crashing stage C
    # on the missing pattern manifest.
    if _paper_half_is_terminal(result):
        if result.pattern_generation_failure_class is not None:
            status = StageStatus.INFRASTRUCTURE_FAILED
            failure_class = result.pattern_generation_failure_class
        else:
            status = StageStatus.SCIENTIFIC_TERMINAL
            failure_class = FailureClass.SCIENTIFIC
        detail = _paper_half_terminal_detail(result)
    else:
        status, failure_class, detail = StageStatus.COMPLETE, None, ""
    _emit_stage_receipt(
        paths,
        config,
        STAGE_PAPER_HALF,
        input_digests=(
            input_digests
            if input_digests is not None
            else compute_paper_half_input_digests(config, drafts)
        ),
        output_paths=[
            paths.corpus / "patterns",
            paths.corpus / "question_pattern_manifest.yaml",
            stage_output_path,
        ],
        status=status,
        failure_class=failure_class,
        detail=detail,
    )
    return result


def _paper_half_is_terminal(result: PaperHalfResult) -> bool:
    """The paper half is a scientific terminal when it accepted ZERO papers OR it accepted papers but
    induced ZERO usable patterns (D4). Either way there is nothing for the downstream stages to build
    on — an honest terminal, not a stage-C crash on the missing pattern manifest."""
    return not result.gate_result.should_continue or not result.reviewed_patterns


def _paper_half_terminal_detail(result: PaperHalfResult) -> str:
    """A cause-neutral one-liner: zero accepted papers, or accepted papers but zero usable patterns."""
    excluded = result.gate_result.excluded
    total = len(result.gate_result.accepted) + len(excluded)
    if not result.gate_result.should_continue:
        reasons = sorted({f"{item.paper_id}:{item.reason}" for item in excluded})
        summary = (
            f"paper half accepted 0 of {total} papers ({result.gate_result.batch_outcome.value})"
        )
        return f"{summary}: {'; '.join(reasons)}" if reasons else summary
    detail = (
        f"paper half accepted {len(result.gate_result.accepted)} of {total} papers but induced 0 "
        "usable question patterns"
    )
    if result.pattern_generation_failure_class is not None:
        return detail + " because pattern generation exhausted its bounded provider recovery"
    return detail


def exec_stage_dataset_half(
    config: MaieusisProjectConfig,
    executor: StageExecutor,
    paths: RunPaths,
    *,
    topic_source_table: TopicSourceTable | None = None,
    topic_r5_source_table: R5TopicEvidenceSourceTable | None = None,
) -> DatasetHalfResult:
    """Stage B boundary: run the dataset half, persist its typed stage output, emit the receipt."""
    paper_output = load_model(paths.stage_output(STAGE_PAPER_HALF), PaperHalfStageOutput)
    result = run_dataset_half(
        config,
        executor=executor,
        run_corpus=paths.corpus,
        intent=config.research_intent,
        reviewed_patterns=paper_output.patterns,
        topic_source_table=topic_source_table,
        topic_r5_source_table=topic_r5_source_table,
    )
    # DP-5 (PR #25): the honest OA fulltext-enrichment tally (informational; not a DAG stage).
    counts = result.fulltext_counts.as_dict()
    write_stage_receipt(
        paths,
        StageReceipt(
            stage_name="fulltext_enrichment",
            status=StageStatus.COMPLETE,
            detail="OA fulltext plus-on: "
            + "; ".join(f"{key}={value}" for key, value in counts.items()),
        ),
    )
    stage_output_path = dump_data(
        DatasetHalfStageOutput(
            receipts=result.receipts,
            lane_coverage=dict(result.lane_coverage),
            source_count=result.source_count,
            scope=result.scope,
            fulltext_counts={key: int(value) for key, value in counts.items()},
            authority_ceiling=result.authority_ceiling,
            source_activity_path=(
                result.source_activity_path.relative_to(paths.root).as_posix()
                if result.source_activity_path is not None
                else ""
            ),
        ),
        paths.stage_output(STAGE_DATASET_HALF),
    )
    if paths.run_manifest.is_file():
        context = RunContext(run_id=paths.root.name, paths=paths)
        research_scope_path = write_research_scope_product(
            paths, intent=config.research_intent, scope=result.scope
        )
        index_existing_artifact(
            context,
            research_scope_path,
            kind=ArtifactKind.RESEARCH_SCOPE,
            processing_state=ProductProcessingState.PRODUCED,
            authority=ArtifactAuthority.PROVISIONAL,
        )
        retrieval_path = write_retrieval_summary(
            paths,
            topic_terms=list(result.scope.terms),
            lane_coverage=result.lane_coverage,
            source_count=result.source_count,
        )
        index_existing_artifact(
            context,
            retrieval_path,
            kind=ArtifactKind.RETRIEVAL_SUMMARY,
            processing_state=ProductProcessingState.PRODUCED,
            authority=ArtifactAuthority.PROVISIONAL,
        )
        topic_path = write_topic_evidence_summary(paths, result.topic_brief)
        index_existing_artifact(
            context,
            topic_path,
            kind=ArtifactKind.TOPIC_EVIDENCE,
            processing_state=ProductProcessingState.PRODUCED,
            authority=(
                ArtifactAuthority.PROVISIONAL
                if config.is_demo
                else authority_from_status(result.topic_brief.review_status)
            ),
        )
        narrative_path = write_dataset_narrative(paths, result.narrative)
        index_existing_artifact(
            context,
            narrative_path,
            kind=ArtifactKind.DATASET_NARRATIVE,
            processing_state=ProductProcessingState.PRODUCED,
            authority=(
                ArtifactAuthority.PROVISIONAL
                if config.is_demo
                else authority_from_status(result.narrative.review_status)
            ),
        )
    _emit_stage_receipt(
        paths,
        config,
        STAGE_DATASET_HALF,
        input_digests={
            **compute_dataset_half_input_digests(config),
            **upstream_input_digests(paths, STAGE_DATASET_HALF),
        },
        output_paths=[
            paths.corpus / "context" / "dataset_narratives",
            paths.corpus / "context" / "topic_evidence",
            stage_output_path,
        ],
    )
    return result


def exec_stage_c(config: MaieusisProjectConfig, paths: RunPaths) -> Path:
    """Stage C boundary: write the intent, build+persist the V2 context, emit the receipt."""
    intent_path = dump_data(config.research_intent, paths.corpus / "research_intent.yaml")
    dataset_output = load_model(paths.stage_output(STAGE_DATASET_HALF), DatasetHalfStageOutput)
    payload_path = run_stage_c(
        run_corpus=paths.corpus,
        intent_path=intent_path,
        dataset_id=config.dataset.seed.dataset_id,
        provisional_inspiration=(
            dataset_output.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
        ),
    )
    if paths.run_manifest.is_file():
        index_existing_artifact(
            RunContext(run_id=paths.root.name, paths=paths),
            payload_path,
            kind=ArtifactKind.CONTEXT_PAYLOAD,
            processing_state=ProductProcessingState.PRODUCED,
            authority=(
                ArtifactAuthority.PROVISIONAL
                if config.is_demo
                or dataset_output.authority_ceiling
                == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
                else ArtifactAuthority.AGENT_REVIEWED
            ),
        )
    _emit_stage_receipt(
        paths,
        config,
        STAGE_C,
        input_digests=upstream_input_digests(paths, STAGE_C),
        output_paths=[intent_path, payload_path],
    )
    return payload_path


def exec_stage_d(
    config: MaieusisProjectConfig,
    executor: StageExecutor,
    paths: RunPaths,
    *,
    family_count: int = 6,
    variants_per_family: int = 3,
) -> Path:
    """Stage D boundary: families → novelty → shortlist gate → manifest, then the receipt."""
    shortlist_path = run_stage_d(
        find_payload_path(paths),
        executor=executor,
        run_corpus=paths.corpus,
        family_count=family_count,
        variants_per_family=variants_per_family,
    )
    _emit_stage_receipt(
        paths,
        config,
        STAGE_D,
        input_digests=upstream_input_digests(paths, STAGE_D),
        output_paths=[paths.corpus / "question_families", paths.stage_output(STAGE_D)],
        family_count=family_count,
        variants_per_family=variants_per_family,
    )
    return shortlist_path


def exec_front_layout(config: MaieusisProjectConfig, paths: RunPaths) -> None:
    """Front-half human-view layout from PERSISTED artifacts ONLY (identical fresh and resumed)."""
    paper_out = load_model(paths.stage_output(STAGE_PAPER_HALF), PaperHalfStageOutput)
    dataset_out = load_model(paths.stage_output(STAGE_DATASET_HALF), DatasetHalfStageOutput)
    payload = load_model(find_payload_path(paths), QuestionScientistContextPayloadV2)
    batch = load_model(paths.question_family_batch_artifact, QuestionFamilyBatch)
    manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
    narrative = load_model(
        reviewed_dataset_narrative_path(config.dataset.seed.dataset_id, corpus_root=paths.corpus),
        DatasetNarrative,
    )
    topic_brief = load_model(
        paths.corpus / "context" / "topic_evidence" / "research_intent.topic_evidence_brief.yaml",
        TopicEvidenceBrief,
    )
    basis_by_family = evidence_basis_by_family(payload, batch.families)
    context = (
        RunContext(run_id=paths.root.name, paths=paths) if paths.run_manifest.is_file() else None
    )
    projection_paths = (
        RunPaths(root=paths.artifacts / ".front-layout-candidates")
        if context is not None
        else paths
    )
    written: list[Path] = []

    def _index(
        source: Path,
        *,
        destination: Path,
        kind: ArtifactKind,
        authority: ArtifactAuthority,
        paper_id: str = "",
    ) -> None:
        if context is not None:
            if not promote_indexed_artifact(
                context,
                source=source,
                destination=destination,
                kind=kind,
                processing_state=ProductProcessingState.PRODUCED,
                authority=authority,
                paper_id=paper_id,
                source_context_digest=payload.context_digest,
            ):
                raise OSError(f"front-layout projection failed: {destination.name}")
            source.unlink(missing_ok=True)
        written.append(destination)

    _index(
        write_resolved_inputs(projection_paths, config),
        destination=paths.resolved_inputs,
        kind=ArtifactKind.RESOLVED_INPUTS,
        authority=ArtifactAuthority.UNKNOWN,
    )
    accepted_cases = [accepted.paper_case for accepted in paper_out.accepted]
    paper_slugs = assign_family_slugs(case.paper_case_id for case in accepted_cases)
    for case in accepted_cases:
        _index(
            write_paper_case_view(
                projection_paths, paper_slug=paper_slugs[case.paper_case_id], case=case
            ),
            destination=paths.paper_case(paper_slugs[case.paper_case_id]),
            kind=ArtifactKind.PAPER_CASE_VIEW,
            authority=(
                ArtifactAuthority.PROVISIONAL
                if config.is_demo
                else authority_from_status(case.review.status)
            ),
            paper_id=case.paper_case_id,
        )
    _index(
        write_paperbank_summary(projection_paths, paper_out.gate_result),
        destination=paths.paperbank_summary,
        kind=ArtifactKind.PAPER_CASE_VIEW,
        authority=(
            ArtifactAuthority.PROVISIONAL if config.is_demo else ArtifactAuthority.AGENT_REVIEWED
        ),
        paper_id="paperbank-summary",
    )
    _index(
        write_question_patterns(projection_paths, paper_out.patterns),
        destination=paths.question_patterns,
        kind=ArtifactKind.PATTERN_REPORT,
        authority=(
            ArtifactAuthority.PROVISIONAL if config.is_demo else ArtifactAuthority.AGENT_REVIEWED
        ),
    )
    _index(
        write_research_scope_product(
            projection_paths, intent=config.research_intent, scope=dataset_out.scope
        ),
        destination=paths.research_scope,
        kind=ArtifactKind.RESEARCH_SCOPE,
        authority=ArtifactAuthority.PROVISIONAL,
    )
    _index(
        write_retrieval_summary(
            projection_paths,
            topic_terms=list(dataset_out.scope.terms),
            lane_coverage=dataset_out.lane_coverage,
            source_count=dataset_out.source_count,
        ),
        destination=paths.retrieval_summary,
        kind=ArtifactKind.RETRIEVAL_SUMMARY,
        authority=ArtifactAuthority.PROVISIONAL,
    )
    _index(
        write_topic_evidence_summary(
            projection_paths, topic_brief, evidence_basis_banner=_topic_basis_banner(payload)
        ),
        destination=paths.topic_evidence_summary,
        kind=ArtifactKind.TOPIC_EVIDENCE,
        authority=(
            ArtifactAuthority.PROVISIONAL
            if config.is_demo
            else authority_from_status(topic_brief.review_status)
        ),
    )
    _index(
        write_dataset_narrative(projection_paths, narrative),
        destination=paths.dataset_narrative,
        kind=ArtifactKind.DATASET_NARRATIVE,
        authority=(
            ArtifactAuthority.PROVISIONAL
            if config.is_demo
            else authority_from_status(narrative.review_status)
        ),
    )
    _index(
        write_question_families(
            projection_paths,
            families=batch.families,
            basis_by_family=basis_by_family,
            authority_ceiling=batch.authority_ceiling,
            planning_eligible=manifest.planning_eligible,
        ),
        destination=paths.question_families,
        kind=ArtifactKind.QUESTION_FAMILIES_VIEW,
        authority=ArtifactAuthority.PROVISIONAL,
    )
    _index(
        write_shortlist(
            projection_paths,
            outcomes=_shortlist_outcomes_from_manifest(manifest),
            basis_by_family=basis_by_family,
            authority_ceiling=manifest.authority_ceiling,
            planning_eligible=manifest.planning_eligible,
        ),
        destination=paths.shortlist,
        kind=ArtifactKind.SHORTLIST_VIEW,
        authority=(
            ArtifactAuthority.PROVISIONAL
            if config.is_demo
            or manifest.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
            else ArtifactAuthority.AGENT_REVIEWED
        ),
    )
    _emit_stage_receipt(
        paths,
        config,
        STAGE_FRONT_LAYOUT,
        input_digests=upstream_input_digests(paths, STAGE_FRONT_LAYOUT),
        output_paths=written,
    )


def exec_back_half(
    config: MaieusisProjectConfig,
    executor: StageExecutor,
    paths: RunPaths,
    run_id: str,
    *,
    completed: Sequence[FamilyCompletionRecord] = (),
    resume_note: str = "",
) -> RunResult:
    """Back-half boundary: rehydrate front receipts, refuse mock-in-Standard, run, emit the receipt.

    DP-5 + R-B: ``assert_front_half_product_grade`` fires from the REHYDRATED stage outputs on BOTH
    the fresh and the resume path — a mock-reviewed front half in Standard is refused before any
    back-half spend. Demo mode is the honest downgrade path instead (F1).
    """
    try:
        paper_out = load_model(paths.stage_output(STAGE_PAPER_HALF), PaperHalfStageOutput)
        dataset_out = load_model(paths.stage_output(STAGE_DATASET_HALF), DatasetHalfStageOutput)
    except (ValueError, ValidationError, OSError) as exc:
        return _back_half_run_terminal(
            config,
            paths,
            run_id,
            exc,
            completed=completed,
            resume_note=resume_note,
        )

    front_receipts = [*paper_out.receipts, *dataset_out.receipts]
    # This is a product trust-boundary refusal, not imperfect external content. It must remain a
    # loud gate failure and never be relabeled as an infrastructure/scientific terminal.
    if not config.is_demo:
        assert_front_half_product_grade(front_receipts)

    try:
        payload = load_model(find_payload_path(paths), QuestionScientistContextPayloadV2)
        manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
        basis_by_family = evidence_basis_by_family(
            payload, [sf.family for sf in manifest.shortlisted]
        )
        result = run_back_half(
            config,
            executor=executor,
            run_root=paths.root,
            run_id=run_id,
            shortlist_path=find_shortlist_path(paths),
            front_half_receipts=front_receipts,
            basis_by_family=basis_by_family,
            completed=completed,
            resume_note=resume_note,
        )
        hard_family_failure = next(
            (
                outcome.failure_class
                for outcome in result.family_outcomes
                if outcome.failure_class is not None
                and outcome.failure_class != FailureClass.SCIENTIFIC
            ),
            None,
        )
        _emit_stage_receipt(
            paths,
            config,
            STAGE_BACK_HALF,
            input_digests=upstream_input_digests(paths, STAGE_BACK_HALF),
            output_paths=[
                paths.root / "families",
                paths.root / run_id / "aggregate_dossier_coordination",
            ],
            status=(
                StageStatus.INFRASTRUCTURE_FAILED
                if hard_family_failure is not None
                else StageStatus.COMPLETE
            ),
            failure_class=hard_family_failure,
            detail=(
                "A family integrity boundary stopped untrusted artifact promotion; safe sibling "
                "and family summaries were retained."
                if hard_family_failure is not None
                else ""
            ),
        )
        return result
    except (
        DevelopmentReviewNotAccepted,
        ScientificAgentInfrastructureError,
        ValueError,
        ValidationError,
        OSError,
    ) as exc:
        # A sibling may have reached a durable terminal during this attempt before a later shared
        # failure. Re-discover strict completion records now so the terminal result and summary do
        # not erase already-usable dossiers. This lazy import avoids the end_to_end↔resume import
        # cycle during module initialization.
        discovered = list(completed)
        try:
            from .resume import discover_family_completions

            current_manifest = load_model(
                find_shortlist_path(paths), QuestionFamilyShortlistManifest
            )
            current_completed, _ = discover_family_completions(paths, current_manifest)
            by_family = {record.question_family_id: record for record in discovered}
            by_family.update({record.question_family_id: record for record in current_completed})
            discovered = list(by_family.values())
        except (FileNotFoundError, ValueError, ValidationError, OSError):
            pass
        return _back_half_run_terminal(
            config,
            paths,
            run_id,
            exc,
            completed=discovered,
            resume_note=resume_note,
        )


_SHORTLIST_BUCKET_AXIS = {
    "rejected": ShortlistAxis.REJECTED_SCIENTIFIC,
    "needs_revision": ShortlistAxis.DEFERRED_MATERIAL_REVISION,
    "deferred": ShortlistAxis.DEFERRED_INSUFFICIENT_EVIDENCE,
}


def _back_half_lineage(paths: RunPaths, run_id: str) -> BackHalfLineage:
    """Prove generation + planner processing from strict artifacts, never path existence alone."""
    family_ids: list[str] = []
    try:
        manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
        family_ids = [item.family.question_family_id for item in manifest.shortlisted]
    except (FileNotFoundError, ValueError, ValidationError, OSError):
        pass

    roots = [paths.root / run_id, paths.root]
    candidates = sorted({path for root in roots for path in root.rglob("run_record.yaml")})
    processed_family_ids: set[str] = set()
    valid_paths: list[str] = []
    for path in candidates:
        try:
            record = load_model(path, CodingAgentRunRecord)
        except (FileNotFoundError, ValueError, ValidationError, OSError):
            continue
        if record.question_family_id not in family_ids:
            continue
        processed_family_ids.add(record.question_family_id)
        try:
            valid_paths.append(path.relative_to(paths.root).as_posix())
        except ValueError:
            valid_paths.append(path.as_posix())
    family_set = set(family_ids)
    return BackHalfLineage(
        families_generated=bool(family_ids),
        family_ids=family_ids,
        planners_ran=bool(family_set) and family_set.issubset(processed_family_ids),
        processed_family_ids=sorted(processed_family_ids),
        planner_run_record_paths=valid_paths,
    )


def _back_half_failure_class(exc: Exception, lineage: BackHalfLineage) -> FailureClass:
    """Classify from cause AND lineage; starvation can never masquerade as scientific."""
    if isinstance(exc, ScientificAgentInfrastructureError):
        return FailureClass.PROVIDER_FAILURE
    if isinstance(exc, PermissionError):
        return FailureClass.SANDBOX_FAILURE
    if isinstance(exc, ValidationError):
        return FailureClass.SCHEMA_ERROR
    if isinstance(exc, OSError):
        return FailureClass.EXTERNAL_CALL_UNCERTAIN
    if isinstance(exc, DevelopmentReviewNotAccepted) and lineage.planners_ran:
        return FailureClass.SCIENTIFIC
    return FailureClass.VALIDATION_FAILURE


def _persist_family_failure_diagnostic(
    paths: RunPaths,
    *,
    run_id: str,
    question_family_id: str,
    raw_text: str,
    sanitized_text: str,
    failure_class: FailureClass,
) -> Path:
    code: Literal["family_failure_recorded", "family_failure_text_sanitized"] = (
        "family_failure_text_sanitized"
        if " ".join(raw_text.split()) != sanitized_text
        else "family_failure_recorded"
    )
    diagnostic = BackHalfFailureDiagnostic(
        diagnostic_id=f"back-half-family-{family_slug(question_family_id)}",
        code=code,
        scope="family",
        question_family_id=question_family_id,
        failure_class=failure_class,
        exception_type="FamilyFailure",
        raw_text=raw_text[:MAX_INTERNAL_FAMILY_FAILURE_TEXT],
        sanitized_text=sanitized_text,
        lineage=_back_half_lineage(paths, run_id),
    )
    return dump_data(
        diagnostic,
        paths.root / "diagnostics" / "back_half_family" / f"{family_slug(question_family_id)}.yaml",
    )


def _clear_current_family_incomplete_diagnostic(
    paths: RunPaths,
    *,
    question_family_id: str,
) -> None:
    """Retire only the stale current-state index; keep the historical diagnostic file."""
    manifest = load_run_manifest(paths)
    retained = [
        diagnostic
        for diagnostic in manifest.diagnostics
        if not (
            diagnostic.code == "family_development_incomplete"
            and diagnostic.family_id == question_family_id
        )
    ]
    if len(retained) != len(manifest.diagnostics):
        manifest.diagnostics = retained
        write_run_manifest(paths, manifest)


def _back_half_public_terminal_reason(failure_class: FailureClass) -> str:
    if failure_class == FailureClass.SCIENTIFIC:
        return (
            "Question-family planning was completed but the scientific review did not support "
            "continuing; see the run diagnostics for details."
        )
    return (
        "Question-family development could not be completed because a required service or input "
        "was unavailable; see the run diagnostics for details."
    )


def _back_half_terminal_outcomes(
    manifest: QuestionFamilyShortlistManifest,
    *,
    failure_class: FailureClass,
    reason: str,
    completed: Sequence[FamilyCompletionRecord],
) -> list[FamilyRunOutcome]:
    completed_by_id = {record.question_family_id: record for record in completed}
    outcomes: list[FamilyRunOutcome] = []
    for shortlisted in manifest.shortlisted:
        family_id = shortlisted.family.question_family_id
        if family_id in completed_by_id:
            outcomes.append(completed_by_id[family_id].family_run_outcome)
        elif failure_class == FailureClass.SCIENTIFIC:
            # Run-level processing does not prove a scientific rejection for every sibling.
            outcomes.append(
                FamilyRunOutcome.derive(
                    question_family_id=family_id,
                    shortlist_axis=ShortlistAxis.INCLUDED,
                    planning_axis=PlanningAxis.ESCALATION,
                    reason=reason,
                )
            )
        else:
            outcomes.append(
                FamilyRunOutcome.derive(
                    question_family_id=family_id,
                    shortlist_axis=ShortlistAxis.INCLUDED,
                    failure_class=failure_class,
                    failed_stage_receipt_id=STAGE_BACK_HALF,
                    reason=reason,
                )
            )
    for bucket, axis in _SHORTLIST_BUCKET_AXIS.items():
        outcomes.extend(
            non_included_family_outcome(family_id, shortlist_axis=axis)
            for family_id in getattr(manifest, f"{bucket}_family_ids")
        )
    return outcomes


def _back_half_run_terminal(
    config: MaieusisProjectConfig,
    paths: RunPaths,
    run_id: str,
    exc: Exception,
    *,
    completed: Sequence[FamilyCompletionRecord],
    resume_note: str,
) -> RunResult:
    """Persist a typed run terminal + diagnostic and always leave an honest summary projection."""
    lineage = _back_half_lineage(paths, run_id)
    failure_class = _back_half_failure_class(exc, lineage)
    reason = _back_half_public_terminal_reason(failure_class)
    diagnostic = BackHalfFailureDiagnostic(
        diagnostic_id="back-half-terminal",
        code="back_half_terminal",
        scope="run",
        failure_class=failure_class,
        exception_type=type(exc).__name__,
        raw_text=str(exc)[:MAX_INTERNAL_FAMILY_FAILURE_TEXT],
        sanitized_text=reason,
        lineage=lineage,
    )
    diagnostic_path = dump_data(diagnostic, paths.root / "diagnostics" / "back_half_terminal.yaml")
    status = (
        StageStatus.SCIENTIFIC_TERMINAL
        if failure_class == FailureClass.SCIENTIFIC
        else StageStatus.INFRASTRUCTURE_FAILED
    )
    try:
        input_digests = upstream_input_digests(paths, STAGE_BACK_HALF)
    except (FileNotFoundError, ValueError, ValidationError, OSError):
        input_digests = {}
    _emit_stage_receipt(
        paths,
        config,
        STAGE_BACK_HALF,
        input_digests=input_digests,
        output_paths=[diagnostic_path],
        status=status,
        failure_class=failure_class,
        detail=reason,
    )
    terminal = RunTerminal(
        failed_stage=STAGE_BACK_HALF,
        failed_stage_receipt_id=STAGE_BACK_HALF,
        failure_class=failure_class,
        reason=reason,
    )
    try:
        manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
    except (FileNotFoundError, ValueError, ValidationError, OSError):
        write_run_terminal_summary(paths, terminal, resume_note=resume_note)
        outcomes: list[FamilyRunOutcome] = []
    else:
        outcomes = _back_half_terminal_outcomes(
            manifest,
            failure_class=failure_class,
            reason=reason,
            completed=completed,
        )
        if paths.run_manifest.is_file() and paths.question_family_batch_artifact.is_file():
            context = RunContext(run_id=run_id, paths=paths)
            add_diagnostic(
                context,
                diagnostic_class=(
                    DiagnosticClass.SCIENTIFIC
                    if failure_class == FailureClass.SCIENTIFIC
                    else DiagnosticClass.INFRASTRUCTURE
                ),
                code="back_half_terminal",
                public_message=reason,
                internal_path=diagnostic_path.relative_to(paths.root).as_posix(),
            )
            batch = load_model(paths.question_family_batch_artifact, QuestionFamilyBatch)
            family_by_id = {family.question_family_id: family for family in batch.families}
            for outcome in outcomes:
                family = family_by_id.get(outcome.question_family_id)
                if family is None:
                    continue
                if outcome.failure_class is not None:
                    add_diagnostic(
                        context,
                        diagnostic_class=(
                            DiagnosticClass.SCIENTIFIC
                            if outcome.failure_class == FailureClass.SCIENTIFIC
                            else DiagnosticClass.INFRASTRUCTURE
                        ),
                        code="family_back_half_terminal",
                        public_message=reason,
                        internal_path=diagnostic_path.relative_to(paths.root).as_posix(),
                        family_id=family.question_family_id,
                    )
                retained = [
                    item
                    for item in load_run_manifest(paths).artifacts
                    if item.family_id == family.question_family_id
                    and item.kind != ArtifactKind.FAMILY_DOSSIER
                ]
                disposition = _update_family_closure_disposition(
                    context, family=family, outcome=outcome
                )
                current = next(
                    (
                        item
                        for item in load_run_manifest(paths).artifacts
                        if item.family_id == family.question_family_id
                        and item.kind == ArtifactKind.FAMILY_DOSSIER
                        and item.processing_state == ProductProcessingState.PRODUCED
                    ),
                    None,
                )
                if current is None:
                    write_family_fallback(
                        context,
                        family=family,
                        disposition=disposition,
                        retained=retained,
                    )
                else:
                    disposition.dossier_path = current.path
                    upsert_family_disposition(context, disposition)
        write_run_summary(
            paths,
            outcomes,
            development_surrogate=config.is_demo,
            resume_note=resume_note,
            all_family_processing_finished=False,
        )
    return RunResult(
        run_id=run_id,
        family_outcomes=outcomes,
        run_terminal=terminal,
        development_surrogate=config.is_demo,
    )


def run_back_half(
    config: MaieusisProjectConfig,
    *,
    executor: StageExecutor,
    run_root: Path,
    run_id: str,
    shortlist_path: Path,
    front_half_receipts: Sequence[PromotionReceipt] = (),
    basis_by_family: dict[str, EvidenceBasis] | None = None,
    completed: Sequence[FamilyCompletionRecord] = (),
    resume_note: str = "",
) -> RunResult:
    """D→F/G: run the orchestrator over the shortlist, map every family → a derived FamilyRunOutcome.

    Per-family isolation is the orchestrator's (each branch is independent); a family's back-half infra
    stop → ``run_incomplete`` (DP-1), a scientific terminal → its honest label. Non-shortlisted families
    keep their shortlist bucket. F1: the run is downgraded to development_model_surrogate if any reviewer
    ran mock.

    5c-1c: ``completed`` families (disk-verified terminal ``FamilyCompletionRecord``s) are fed to the
    orchestrator's ``completed_records`` seam — zero branch creation, zero spawn for them — and their
    persisted outcomes are merged back in. When EVERY shortlisted family is completed, the orchestrator
    (and the owner/reviewer providers) are not touched at all.
    """
    from ..dossier.multi_family_orchestrator import run_multi_family_orchestrator

    manifest = load_model(shortlist_path, QuestionFamilyShortlistManifest)
    shortlisted_ids = [sf.family.question_family_id for sf in manifest.shortlisted]
    completed_by_id = {
        record.question_family_id: record
        for record in completed
        if record.question_family_id in set(shortlisted_ids)
    }
    to_run = [fid for fid in shortlisted_ids if fid not in completed_by_id]

    outcomes: list[FamilyRunOutcome] = [
        record.family_run_outcome for record in completed_by_id.values()
    ]
    dossier_statuses = [record.dossier_record.status for record in completed_by_id.values()]
    family_results: list[MultiFamilyFamilyResult] = []
    if to_run:
        owner_provider, reviewer_provider = executor.owner_reviewer_providers()
        result = run_multi_family_orchestrator(
            output_root=run_root,
            run_id=run_id,
            target_family_ids=to_run,
            shortlist_path=shortlist_path,
            planner_host_factory=executor.planner_host_factory(run_root),
            owner_provider=owner_provider,
            reviewer_provider=reviewer_provider,
            inspection_resources=executor.inspection_resources(),
            review_authority=ReviewAuthority.AUTOMATED,
            completed_records=[record.dossier_record for record in completed_by_id.values()],
            # Honor the operator's back-half config: these were previously NOT passed, so the
            # orchestrator ran its own defaults (max_revise_rounds=4 vs the config default 2 — a
            # silent live cost overrun vs the preflight estimate; the back-half receipt slice
            # already records max_revise_rounds, so no receipt change is needed here).
            max_parallel_family_workers=config.run.max_parallel_family_workers,
            max_revise_rounds=config.run.max_revise_rounds,
        )
        family_results = list(result.family_results)
        for family_result in result.family_results:
            dossier_statuses.append(family_result.status)
            raw_reason = family_result.error or family_result.status.value
            safe_reason = (
                _public_family_terminal_reason(family_result.status)
                if family_result.error
                else sanitize_family_failure_text(raw_reason)
            )
            if family_result.error:
                diagnostic_path = _persist_family_failure_diagnostic(
                    RunPaths(root=run_root),
                    run_id=run_id,
                    question_family_id=family_result.question_family_id,
                    raw_text=family_result.error,
                    sanitized_text=safe_reason,
                    failure_class=_diagnostic_failure_class(family_result.status),
                )
                envelope_paths = RunPaths(root=run_root)
                if envelope_paths.run_manifest.is_file():
                    add_diagnostic(
                        RunContext(run_id=run_id, paths=envelope_paths),
                        diagnostic_class=(
                            DiagnosticClass.SCIENTIFIC
                            if _diagnostic_failure_class(family_result.status)
                            == FailureClass.SCIENTIFIC
                            else DiagnosticClass.INFRASTRUCTURE
                        ),
                        code="family_development_incomplete",
                        public_message=safe_reason,
                        internal_path=diagnostic_path.relative_to(run_root).as_posix(),
                        family_id=family_result.question_family_id,
                    )
            outcomes.append(
                family_outcome_from_dossier_status(
                    family_result.question_family_id,
                    status=family_result.status,
                    reason=safe_reason,
                )
            )

    # Non-shortlisted families keep their honest shortlist bucket (back half NOT_RUN).
    for bucket, axis in _SHORTLIST_BUCKET_AXIS.items():
        for family_id in getattr(manifest, f"{bucket}_family_ids"):
            outcomes.append(non_included_family_outcome(family_id, shortlist_axis=axis))

    run_result = RunResult(
        run_id=run_id,
        family_outcomes=outcomes,
        development_surrogate=is_development_surrogate(
            config,
            front_half_receipts=front_half_receipts,
            dossier_statuses=dossier_statuses,
        ),
    )
    run_result.family_outcomes = _write_back_half_layout(
        RunPaths(root=run_root),
        outcomes=outcomes,
        family_results=family_results,
        development_surrogate=run_result.development_surrogate,
        authority_ceiling=manifest.authority_ceiling,
        basis_by_family=basis_by_family or {},
        run_id=run_id,
        shortlist_digest=stable_hash(manifest),
        reused_included_ids=frozenset(completed_by_id),
        resume_note=resume_note,
    )
    return run_result


def _find_artifact(artifact_paths: Sequence[str], suffix: str) -> Path | None:
    for raw in artifact_paths:
        path = Path(raw)
        if path.name == suffix and path.exists():
            return path
    return None


def _family_completion_record(
    paths: RunPaths,
    *,
    run_id: str,
    shortlist_digest: str,
    slug: str,
    family_result: MultiFamilyFamilyResult,
    outcome: FamilyRunOutcome,
) -> FamilyCompletionRecord:
    """Build one family's durable completion record over the artifacts that exist under the run root."""
    record = family_result.record
    candidates = [paths.family_dir(slug) / "dossier.md", paths.family_dir(slug) / "audit.yaml"]
    if family_result.status in {
        FamilyDossierStatus.PUBLIC_DOSSIER_REVISION_REQUIRED,
        FamilyDossierStatus.PROVENANCE_INTEGRITY_TERMINAL,
    }:
        closure_relative = paths.family_artifacts(slug).relative_to(paths.root) / "dossier_closure"
        stable_names = {
            "diagnostic.yaml",
            "source_outcome_packet.yaml",
            "source_review_decision.yaml",
            "scientific_source_snapshot.yaml",
        }
        if family_result.status == FamilyDossierStatus.PUBLIC_DOSSIER_REVISION_REQUIRED:
            stable_names.update(
                {
                    "machine_dossier.md",
                    "machine_dossier_artifact.yaml",
                    "machine_render_manifest.yaml",
                }
            )
        expected_paths = {(closure_relative / name).as_posix() for name in stable_names}
        indexed_paths = {
            item.path
            for item in load_run_manifest(paths).artifacts
            if item.family_id == family_result.question_family_id
            and item.path.startswith(closure_relative.as_posix() + "/")
        }
        if indexed_paths != expected_paths:
            raise ValueError("typed dossier closure stable projection is incomplete")
        candidates.extend(paths.root / relative for relative in sorted(expected_paths))
    for raw in (record.outcome_markdown_path, record.outcome_audit_path):
        if raw:
            candidates.append(Path(raw))
    files = [
        candidate
        for candidate in candidates
        if candidate.is_file() and candidate.is_relative_to(paths.root)
    ]
    return FamilyCompletionRecord(
        run_id=run_id,
        question_family_id=family_result.question_family_id,
        slug=slug,
        shortlist_digest=shortlist_digest,
        dossier_record=record,
        family_run_outcome=outcome,
        artifact_digests=relative_output_digests(paths.root, files),
    )


def _validated_fixed_family_artifacts(
    paths: RunPaths,
    *,
    context: RunContext,
    family_id: str,
    branch_id: str,
    slug: str,
    development_surrogate: bool,
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED,
    closure_status: FamilyDossierStatus | None = None,
) -> tuple[list[ArtifactRecord], Path | None, Path | None]:
    """Project only fixed, strict branch artifacts; never inspect arbitrary returned path strings."""
    from ...schemas.dossier_closure import DossierClosureDiagnostic, DossierClosureOutcome
    from ...schemas.generic_dossier import (
        GenericDossierRenderManifest,
        GenericEndUserDossierAuditSidecar,
        GenericEndUserDossierManifest,
    )
    from ...schemas.multi_family_dossier import FamilyOutcomeAuditSidecar
    from ...schemas.planner_probe import ConstructProbeMap
    from ...schemas.planner_run import (
        CodingAgentRunRecord,
        PlannerArtifactImportManifest,
    )
    from ...schemas.planning_dialogue import (
        BranchRejectionMessage,
        HumanEscalationRequest,
        IndependentPlanReviewMessage,
        PlanDraftMessage,
        PlanningMessage,
        QuestionOwnerPlanReviewMessage,
    )
    from ...schemas.question_family_branch import QuestionFamilyInspectionEvidence
    from ..planning.dataset_planner_packet import (
        DatasetPlannerHandoffManifest,
        PlannerArtifactValidationReport,
    )

    branch_planner = paths.root / (context.run_id) / "branches" / branch_id / "planner"
    destination_root = paths.family_artifacts(slug)
    reviewed_authority = (
        ArtifactAuthority.PROVISIONAL
        if development_surrogate
        or authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
        else ArtifactAuthority.AGENT_REVIEWED
    )
    handoff_source = branch_planner / "handoff_manifest.yaml"
    recoverable_terminal_statuses = {
        FamilyDossierStatus.FAILED_VALIDATION,
        FamilyDossierStatus.INFRASTRUCTURE_INCOMPLETE,
    }
    # A planner/provider may fail before a handoff exists. That is precisely the recoverable case
    # served by the typed outcome dossier; demanding a missing handoff here would incorrectly
    # upgrade an ordinary warning into a hard integrity terminal. Validate the outcome pair against
    # the trusted run/branch/family identities and return it as the sole retained back-half product.
    if closure_status in recoverable_terminal_statuses and not handoff_source.is_file():
        terminal_workspace = branch_planner / "development_outcome_dossier"
        terminal_markdown_source = terminal_workspace / "outcome.md"
        terminal_audit_source = terminal_workspace / "outcome_audit.yaml"
        try:
            validate_exact_artifact(paths.root, terminal_markdown_source)
            validate_exact_artifact(paths.root, terminal_audit_source)
            terminal_audit = load_model(terminal_audit_source, FamilyOutcomeAuditSidecar)
            if (
                terminal_audit.run_id != context.run_id
                or terminal_audit.branch_id != branch_id
                or terminal_audit.question_family_id != family_id
                or terminal_audit.status != closure_status
                or Path(terminal_audit.outcome_markdown_path).absolute()
                != terminal_markdown_source.absolute()
                or stable_hash(terminal_markdown_source.read_text(encoding="utf-8"))
                != terminal_audit.outcome_markdown_digest
            ):
                raise ValueError("terminal outcome dossier binding mismatch")
        except (OSError, ValueError, ValidationError) as exc:
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.INTEGRITY,
                code="terminal_outcome_rejected",
                public_message=(
                    "A terminal planning outcome failed strict identity or digest validation."
                ),
                family_id=family_id,
            )
            raise HardFamilyIntegrityViolation(
                "terminal outcome failed strict identity or digest validation"
            ) from exc
        promote_indexed_artifact(
            context,
            source=terminal_markdown_source,
            destination=destination_root / "terminal_outcome_source.md",
            kind=ArtifactKind.DIAGNOSTIC,
            processing_state=ProductProcessingState.DEGRADED,
            authority=ArtifactAuthority.PROVISIONAL,
            family_id=family_id,
        )
        promote_indexed_artifact(
            context,
            source=terminal_audit_source,
            destination=destination_root / "terminal_outcome_audit.yaml",
            kind=ArtifactKind.AUDIT_SIDECAR,
            processing_state=ProductProcessingState.DEGRADED,
            authority=ArtifactAuthority.PROVISIONAL,
            family_id=family_id,
        )
        retained = [
            item
            for item in load_run_manifest(paths).artifacts
            if item.family_id == family_id and item.kind != ArtifactKind.FAMILY_DOSSIER
        ]
        return retained, None, None
    try:
        validate_exact_artifact(paths.root, handoff_source)
        handoff = load_model(handoff_source, DatasetPlannerHandoffManifest)
        if (
            handoff.run_id != context.run_id
            or handoff.branch_id != branch_id
            or handoff.question_family_id != family_id
            or Path(handoff.manifest_path).absolute() != handoff_source.absolute()
        ):
            raise ValueError("planner handoff identity mismatch")
    except (OSError, ValueError, ValidationError) as exc:
        add_diagnostic(
            context,
            diagnostic_class=DiagnosticClass.INTEGRITY,
            code="planner_handoff_rejected",
            public_message="The planner handoff failed strict run and branch identity validation.",
            family_id=family_id,
        )
        raise HardFamilyIntegrityViolation(
            "planner handoff failed strict run and branch identity validation"
        ) from exc

    expected_identity = {
        "run_id": handoff.run_id,
        "branch_id": handoff.branch_id,
        "question_family_id": handoff.question_family_id,
        "context_id": handoff.context_id,
        "owner_session_id": handoff.owner_session_id,
    }

    def _validate_identity(model: object) -> None:
        for key, expected in expected_identity.items():
            if hasattr(model, key) and getattr(model, key) != expected:
                raise ValueError(f"{key} identity mismatch")

    if not promote_indexed_artifact(
        context,
        source=handoff_source,
        destination=destination_root / "handoff_manifest.yaml",
        kind=ArtifactKind.PLANNER_HANDOFF,
        processing_state=ProductProcessingState.PRODUCED,
        authority=ArtifactAuthority.UNKNOWN,
        family_id=family_id,
    ):
        return ([], None, None)

    import_source = branch_planner / "artifact_import_manifest.yaml"
    import_manifest: PlannerArtifactImportManifest | None = None
    if import_source.is_file():
        try:
            validate_exact_artifact(paths.root, import_source)
            import_manifest = load_model(import_source, PlannerArtifactImportManifest)
            _validate_identity(import_manifest)
            if Path(import_manifest.manifest_path).absolute() != import_source.absolute():
                raise ValueError("planner import manifest path mismatch")
        except (OSError, ValueError, ValidationError) as exc:
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.INTEGRITY,
                code="planner_import_manifest_rejected",
                public_message="The planner import manifest failed strict identity validation.",
                family_id=family_id,
            )
            raise HardFamilyIntegrityViolation(
                "planner import manifest failed strict identity validation"
            ) from exc
        else:
            if not promote_indexed_artifact(
                context,
                source=import_source,
                destination=destination_root / "artifact_import_manifest.yaml",
                kind=ArtifactKind.PLANNER_IMPORT_MANIFEST,
                processing_state=ProductProcessingState.PRODUCED,
                authority=ArtifactAuthority.UNKNOWN,
                family_id=family_id,
            ):
                import_manifest = None

    projected_specs: list[tuple[Path, str, type[object], ArtifactKind, ArtifactAuthority]] = [
        (
            branch_planner / "development_review" / "owner_plan_review.yaml",
            "owner_plan_review.yaml",
            QuestionOwnerPlanReviewMessage,
            ArtifactKind.PLAN,
            reviewed_authority,
        ),
        (
            branch_planner / "development_review" / "independent_plan_review.yaml",
            "independent_plan_review.yaml",
            IndependentPlanReviewMessage,
            ArtifactKind.PLAN,
            reviewed_authority,
        ),
    ]
    for source, name, model_type, kind, authority in projected_specs:
        if not source.is_file():
            continue
        try:
            validate_exact_artifact(paths.root, source)
            model = load_model(source, model_type)  # type: ignore[type-var]
            _validate_identity(model)
        except (OSError, ValueError, ValidationError) as exc:
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.INTEGRITY,
                code="fixed_branch_artifact_rejected",
                public_message=(
                    "A fixed branch artifact failed strict identity validation and was not retained."
                ),
                family_id=family_id,
            )
            raise HardFamilyIntegrityViolation(
                "fixed branch artifact failed strict identity validation"
            ) from exc
        promote_indexed_artifact(
            context,
            source=source,
            destination=destination_root / name,
            kind=kind,
            processing_state=ProductProcessingState.PRODUCED,
            authority=authority,
            family_id=family_id,
        )

    closure_candidates = (
        (
            DossierClosureOutcome.PROVENANCE_INTEGRITY_TERMINAL,
            branch_planner / "generic_scientific_dossier" / "dossier_closure_diagnostic.yaml",
        ),
        (
            DossierClosureOutcome.PUBLIC_DOSSIER_REVISION_REQUIRED,
            branch_planner
            / "generic_end_user_scientific_dossier"
            / "dossier_closure_diagnostic.yaml",
        ),
    )
    closure_statuses = {
        FamilyDossierStatus.PUBLIC_DOSSIER_REVISION_REQUIRED,
        FamilyDossierStatus.PROVENANCE_INTEGRITY_TERMINAL,
    }
    closure_code_by_status: dict[FamilyDossierStatus, DossierClosureOutcome] = {
        FamilyDossierStatus.PUBLIC_DOSSIER_REVISION_REQUIRED: (
            DossierClosureOutcome.PUBLIC_DOSSIER_REVISION_REQUIRED
        ),
        FamilyDossierStatus.PROVENANCE_INTEGRITY_TERMINAL: (
            DossierClosureOutcome.PROVENANCE_INTEGRITY_TERMINAL
        ),
    }
    expected_closure_code = (
        closure_code_by_status[closure_status] if closure_status in closure_statuses else None
    )
    present_closures = [
        item
        for item in closure_candidates
        if (expected_closure_code is None or item[0] == expected_closure_code)
        and (item[1].exists() or item[1].is_symlink())
    ]
    if closure_status is not None and closure_status not in closure_statuses:
        present_closures = []
    if len(present_closures) > 1:
        add_diagnostic(
            context,
            diagnostic_class=DiagnosticClass.INTEGRITY,
            code="dossier_closure_rejected",
            public_message="Conflicting dossier-closure diagnostics were not retained.",
            family_id=family_id,
        )
        if closure_status in closure_statuses:
            raise ValueError("conflicting typed dossier closure diagnostics")
    elif closure_status in closure_statuses and not present_closures:
        raise ValueError("typed dossier closure diagnostic is missing")
    elif present_closures:
        expected_code, diagnostic_source = present_closures[0]
        writing_root = branch_planner / "generic_scientific_dossier"
        fixed_retained: dict[Path, str] = {
            writing_root / "source_outcome_packet.yaml": "source_outcome_packet.yaml",
            writing_root / "source_review_decision.yaml": "source_review_decision.yaml",
            writing_root / "scientific_source_snapshot.yaml": "scientific_source_snapshot.yaml",
        }
        expected_omitted: set[Path] = set()
        if expected_code == DossierClosureOutcome.PUBLIC_DOSSIER_REVISION_REQUIRED:
            machine_root = branch_planner / "generic_scientific_dossier_rendered"
            fixed_retained.update(
                {
                    machine_root / "scientific_dossier.md": "machine_dossier.md",
                    machine_root
                    / "scientific_dossier_artifact.yaml": "machine_dossier_artifact.yaml",
                    machine_root / "manifest.yaml": "machine_render_manifest.yaml",
                }
            )
            public_root = branch_planner / "generic_end_user_scientific_dossier"
            expected_omitted = {
                public_root / "end_user_dossier.md",
                public_root / "end_user_dossier_artifact.yaml",
                public_root / "end_user_dossier_audit.yaml",
                public_root / "manifest.yaml",
            }
        try:
            validate_exact_artifact(paths.root, diagnostic_source)
            diagnostic = load_model(diagnostic_source, DossierClosureDiagnostic)
            if (
                diagnostic.code != expected_code
                or diagnostic.run_id != context.run_id
                or diagnostic.branch_id != branch_id
                or diagnostic.question_family_id != family_id
                or {Path(raw) for raw in diagnostic.retained_artifact_paths} != set(fixed_retained)
                or {Path(raw) for raw in diagnostic.omitted_public_artifact_paths}
                != expected_omitted
            ):
                raise ValueError("dossier closure diagnostic binding mismatch")
            for source in fixed_retained:
                validate_exact_artifact(paths.root, source)
            if any(path.exists() or path.is_symlink() for path in expected_omitted):
                raise ValueError("an omitted public dossier artifact already exists")
        except (OSError, ValueError, ValidationError) as exc:
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.INTEGRITY,
                code="dossier_closure_rejected",
                public_message=(
                    "A dossier-closure diagnostic failed strict identity or path validation."
                ),
                family_id=family_id,
            )
            if closure_status in closure_statuses:
                raise ValueError("typed dossier closure diagnostic failed validation") from exc
        else:
            closure_root = destination_root / "dossier_closure"
            projected_sources = {
                closure_root / "diagnostic.yaml": diagnostic_source,
                **{
                    closure_root / stable_name: source
                    for source, stable_name in fixed_retained.items()
                },
            }
            closure_prefix = (closure_root.relative_to(paths.root)).as_posix()
            previous_manifest = load_run_manifest(paths)
            previous_closure_records = [
                item.model_copy(deep=True)
                for item in previous_manifest.artifacts
                if item.family_id == family_id and item.path.startswith(closure_prefix + "/")
            ]
            previous_destination_bytes: dict[Path, bytes | None] = {}
            for destination in projected_sources:
                if destination.exists() or destination.is_symlink():
                    validate_exact_artifact(paths.root, destination)
                    previous_destination_bytes[destination] = destination.read_bytes()
                else:
                    previous_destination_bytes[destination] = None
            previous_manifest_bytes = paths.run_manifest.read_bytes()
            previous_readme_bytes = paths.readme.read_bytes()
            try:
                if not promote_indexed_artifact(
                    context,
                    source=diagnostic_source,
                    destination=closure_root / "diagnostic.yaml",
                    kind=ArtifactKind.DIAGNOSTIC,
                    processing_state=ProductProcessingState.FAILED,
                    authority=ArtifactAuthority.UNKNOWN,
                    family_id=family_id,
                ):
                    raise ValueError("typed dossier closure diagnostic promotion failed")
                for source, stable_name in fixed_retained.items():
                    if not promote_indexed_artifact(
                        context,
                        source=source,
                        destination=closure_root / stable_name,
                        kind=ArtifactKind.DIAGNOSTIC,
                        processing_state=ProductProcessingState.FAILED,
                        authority=ArtifactAuthority.UNKNOWN,
                        family_id=family_id,
                    ):
                        raise ValueError("typed dossier closure retained-input promotion failed")
                expected_projection = {
                    destination.relative_to(paths.root).as_posix(): sha256_file(source)
                    for destination, source in projected_sources.items()
                }
                current_manifest = load_run_manifest(paths)
                indexed_projection = {
                    item.path: item.sha256
                    for item in current_manifest.artifacts
                    if item.family_id == family_id and item.path in expected_projection
                }
                if indexed_projection != expected_projection:
                    raise ValueError("typed dossier closure projection digest mismatch")
                retained_manifest_artifacts = [
                    item
                    for item in current_manifest.artifacts
                    if not (
                        item.family_id == family_id
                        and item.path.startswith(closure_prefix + "/")
                        and item.path not in expected_projection
                    )
                ]
                if retained_manifest_artifacts != current_manifest.artifacts:
                    current_manifest.artifacts = retained_manifest_artifacts
                    write_run_manifest(paths, current_manifest)
            except (OSError, ValueError, ValidationError) as exc:
                for destination, payload in previous_destination_bytes.items():
                    _restore_bytes(destination, payload)
                _restore_bytes(paths.run_manifest, previous_manifest_bytes)
                _restore_bytes(paths.readme, previous_readme_bytes)
                restored_manifest = load_run_manifest(paths)
                restored_closure_records = [
                    item
                    for item in restored_manifest.artifacts
                    if item.family_id == family_id and item.path.startswith(closure_prefix + "/")
                ]
                if restored_closure_records != previous_closure_records:
                    raise RuntimeError(
                        "typed dossier closure prior generation could not be restored"
                    ) from exc
                add_diagnostic(
                    context,
                    diagnostic_class=DiagnosticClass.INTEGRITY,
                    code="dossier_closure_projection_incomplete",
                    public_message=(
                        "The typed dossier-closure diagnostic could not be projected completely."
                    ),
                    family_id=family_id,
                )
                raise ValueError("typed dossier closure stable projection is incomplete") from exc

    if import_manifest is not None:
        known_sources = {source.absolute() for source, *_rest in projected_specs}
        known_sources.update({handoff_source.absolute(), import_source.absolute()})
        supported_imports: tuple[tuple[type[object], ArtifactKind, ArtifactAuthority], ...] = (
            (CodingAgentRunRecord, ArtifactKind.PLANNER_RUN_RECORD, ArtifactAuthority.UNKNOWN),
            (
                QuestionFamilyInspectionEvidence,
                ArtifactKind.INSPECTION_EVIDENCE,
                ArtifactAuthority.PROVISIONAL,
            ),
            (ConstructProbeMap, ArtifactKind.INSPECTION_EVIDENCE, ArtifactAuthority.PROVISIONAL),
            (
                PlannerArtifactValidationReport,
                ArtifactKind.PLANNER_VALIDATION_REPORT,
                ArtifactAuthority.UNKNOWN,
            ),
            (PlanDraftMessage, ArtifactKind.PLAN, ArtifactAuthority.PROVISIONAL),
            (BranchRejectionMessage, ArtifactKind.REJECTION, ArtifactAuthority.PROVISIONAL),
            (HumanEscalationRequest, ArtifactKind.ESCALATION, ArtifactAuthority.PROVISIONAL),
        )
        for raw_path in import_manifest.checked_paths:
            source = Path(raw_path)
            if source.absolute() in known_sources:
                continue
            try:
                if (
                    not source.is_file()
                    or source.is_symlink()
                    or not source.resolve().is_relative_to(branch_planner.resolve())
                ):
                    raise ValueError("checked planner path escaped its workspace")
                validate_exact_artifact(paths.root, source)
                imported_model: object | None = None
                imported_kind: ArtifactKind | None = None
                imported_authority = ArtifactAuthority.UNKNOWN
                for model_type, kind, authority in supported_imports:
                    try:
                        imported_model = load_model(source, model_type)  # type: ignore[type-var]
                    except (ValueError, ValidationError):
                        continue
                    imported_kind = kind
                    imported_authority = authority
                    break
                if imported_model is None:
                    try:
                        imported_model = TypeAdapter(PlanningMessage).validate_python(
                            load_data(source)
                        )
                    except (ValueError, ValidationError):
                        imported_model = None
                    else:
                        imported_kind = ArtifactKind.DIALOGUE
                        imported_authority = ArtifactAuthority.PROVISIONAL
                if imported_model is None or imported_kind is None:
                    raise ValueError("unsupported checked planner artifact type")
                _validate_identity(imported_model)
                if isinstance(imported_model, QuestionFamilyInspectionEvidence) and (
                    imported_model.evidence_id not in import_manifest.evidence_ids
                ):
                    raise ValueError("inspection evidence was not imported")
                if isinstance(imported_model, ConstructProbeMap) and (
                    imported_model.construct_probe_id not in import_manifest.construct_probe_map_ids
                ):
                    raise ValueError("construct probe map was not imported")
                if isinstance(imported_model, PlannerArtifactValidationReport) and (
                    stable_hash(imported_model.model_dump(mode="json"))
                    != import_manifest.validation_report_digest
                ):
                    raise ValueError("planner validation report digest mismatch")
                relative = source.absolute().relative_to(branch_planner.absolute()).as_posix()
                safe_name = f"{stable_hash(relative)[:10]}-{source.name}"
                if not promote_indexed_artifact(
                    context,
                    source=source,
                    destination=destination_root / "imported" / safe_name,
                    kind=imported_kind,
                    processing_state=ProductProcessingState.PRODUCED,
                    authority=imported_authority,
                    family_id=family_id,
                ):
                    raise ValueError("checked planner artifact promotion failed")
            except (OSError, ValueError, ValidationError) as exc:
                add_diagnostic(
                    context,
                    diagnostic_class=DiagnosticClass.INTEGRITY,
                    code="checked_planner_artifact_rejected",
                    public_message=(
                        "A planner artifact listed by the strict import manifest failed validation."
                    ),
                    family_id=family_id,
                )
                raise HardFamilyIntegrityViolation(
                    "checked planner artifact failed strict identity validation"
                ) from exc

    # A reject/revise/provider-warning family owns a typed user-readable outcome pair. Validate its
    # identity and digest, then retain it as a degraded source so the public fallback can include the
    # actual review disposition instead of claiming that no useful planning work exists.
    terminal_workspace = branch_planner / "development_outcome_dossier"
    terminal_markdown_source = terminal_workspace / "outcome.md"
    terminal_audit_source = terminal_workspace / "outcome_audit.yaml"
    if terminal_markdown_source.exists() or terminal_audit_source.exists():
        try:
            validate_exact_artifact(paths.root, terminal_markdown_source)
            validate_exact_artifact(paths.root, terminal_audit_source)
            terminal_audit = load_model(terminal_audit_source, FamilyOutcomeAuditSidecar)
            _validate_identity(terminal_audit)
            if (
                closure_status is None
                or terminal_audit.status != closure_status
                or Path(terminal_audit.outcome_markdown_path).absolute()
                != terminal_markdown_source.absolute()
                or stable_hash(terminal_markdown_source.read_text(encoding="utf-8"))
                != terminal_audit.outcome_markdown_digest
            ):
                raise ValueError("terminal outcome dossier binding mismatch")
        except (OSError, ValueError, ValidationError) as exc:
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.INTEGRITY,
                code="terminal_outcome_rejected",
                public_message=(
                    "A terminal planning outcome failed strict identity or digest validation."
                ),
                family_id=family_id,
            )
            raise HardFamilyIntegrityViolation(
                "machine dossier failed strict identity or digest validation"
            ) from exc
        else:
            promote_indexed_artifact(
                context,
                source=terminal_markdown_source,
                destination=destination_root / "terminal_outcome_source.md",
                kind=ArtifactKind.DIAGNOSTIC,
                processing_state=ProductProcessingState.DEGRADED,
                authority=ArtifactAuthority.PROVISIONAL,
                family_id=family_id,
            )
            promote_indexed_artifact(
                context,
                source=terminal_audit_source,
                destination=destination_root / "terminal_outcome_audit.yaml",
                kind=ArtifactKind.AUDIT_SIDECAR,
                processing_state=ProductProcessingState.DEGRADED,
                authority=ArtifactAuthority.PROVISIONAL,
                family_id=family_id,
            )

    machine_path: Path | None = None
    machine_workspace = branch_planner / "generic_scientific_dossier_rendered"
    machine_manifest_path = machine_workspace / "manifest.yaml"
    if machine_manifest_path.is_file():
        try:
            validate_exact_artifact(paths.root, machine_manifest_path)
            machine_manifest = load_model(machine_manifest_path, GenericDossierRenderManifest)
            expected_machine = machine_workspace / "scientific_dossier.md"
            validate_exact_artifact(paths.root, expected_machine)
            if (
                machine_manifest.run_id != context.run_id
                or machine_manifest.branch_id != branch_id
                or machine_manifest.question_family_id != family_id
                or machine_manifest.context_id != handoff.context_id
                or machine_manifest.owner_session_id != handoff.owner_session_id
                or Path(machine_manifest.dossier_markdown_path).absolute()
                != expected_machine.absolute()
                or stable_hash(expected_machine.read_text(encoding="utf-8"))
                != machine_manifest.dossier_markdown_digest
            ):
                raise ValueError("machine dossier manifest binding mismatch")
        except (OSError, ValueError, ValidationError) as exc:
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.INTEGRITY,
                code="machine_dossier_rejected",
                public_message="A machine dossier failed strict identity or digest validation.",
                family_id=family_id,
            )
            raise HardFamilyIntegrityViolation(
                "public dossier failed strict identity or digest validation"
            ) from exc
        else:
            machine_path = destination_root / "machine_dossier.md"
            promote_indexed_artifact(
                context,
                source=expected_machine,
                destination=machine_path,
                kind=ArtifactKind.MACHINE_DOSSIER,
                processing_state=ProductProcessingState.PRODUCED,
                authority=reviewed_authority,
                family_id=family_id,
            )
            promote_indexed_artifact(
                context,
                source=machine_manifest_path,
                destination=destination_root / "machine_render_manifest.yaml",
                kind=ArtifactKind.MACHINE_DOSSIER,
                processing_state=ProductProcessingState.PRODUCED,
                authority=reviewed_authority,
                family_id=family_id,
            )

    public_path: Path | None = None
    audit_path: Path | None = None
    public_workspace = branch_planner / "generic_end_user_scientific_dossier"
    public_manifest_path = public_workspace / "manifest.yaml"
    if public_manifest_path.is_file():
        try:
            validate_exact_artifact(paths.root, public_manifest_path)
            public_manifest = load_model(public_manifest_path, GenericEndUserDossierManifest)
            expected_public = public_workspace / "end_user_dossier.md"
            expected_audit = public_workspace / "end_user_dossier_audit.yaml"
            validate_exact_artifact(paths.root, expected_public)
            validate_exact_artifact(paths.root, expected_audit)
            audit = load_model(expected_audit, GenericEndUserDossierAuditSidecar)
            if (
                public_manifest.run_id != context.run_id
                or public_manifest.branch_id != branch_id
                or public_manifest.question_family_id != family_id
                or public_manifest.context_id != handoff.context_id
                or public_manifest.owner_session_id != handoff.owner_session_id
                or audit.run_id != context.run_id
                or audit.branch_id != branch_id
                or audit.question_family_id != family_id
                or audit.context_id != handoff.context_id
                or audit.owner_session_id != handoff.owner_session_id
                or Path(public_manifest.end_user_dossier_path).absolute()
                != expected_public.absolute()
                or Path(public_manifest.audit_sidecar_path).absolute() != expected_audit.absolute()
                or stable_hash(expected_public.read_text(encoding="utf-8"))
                != public_manifest.end_user_dossier_digest
                or stable_hash(audit.model_dump(mode="json"))
                != public_manifest.audit_sidecar_digest
            ):
                raise ValueError("public dossier manifest binding mismatch")
        except (OSError, ValueError, ValidationError) as exc:
            add_diagnostic(
                context,
                diagnostic_class=DiagnosticClass.INTEGRITY,
                code="public_dossier_rejected",
                public_message="A public dossier failed strict identity or digest validation.",
                family_id=family_id,
            )
            raise HardFamilyIntegrityViolation(
                "public dossier failed strict identity or digest validation"
            ) from exc
        else:
            audit_path = destination_root / "end_user_dossier_audit.yaml"
            audit_promoted = promote_indexed_artifact(
                context,
                source=expected_audit,
                destination=audit_path,
                kind=ArtifactKind.AUDIT_SIDECAR,
                processing_state=ProductProcessingState.PRODUCED,
                authority=reviewed_authority,
                family_id=family_id,
            )
            if audit_promoted:
                stable_public = destination_root / "end_user_dossier.md"
                if promote_indexed_artifact(
                    context,
                    source=expected_public,
                    destination=stable_public,
                    kind=ArtifactKind.PUBLIC_DOSSIER_SOURCE,
                    processing_state=ProductProcessingState.PRODUCED,
                    authority=reviewed_authority,
                    family_id=family_id,
                ):
                    public_path = stable_public
                else:
                    audit_path = None
            else:
                audit_path = None

    retained = [
        item
        for item in load_run_manifest(paths).artifacts
        if item.family_id == family_id and item.kind != ArtifactKind.FAMILY_DOSSIER
    ]
    return retained, public_path, audit_path


def preserve_branch_products_before_cleanup(
    config: MaieusisProjectConfig,
    paths: RunPaths,
    *,
    run_id: str,
    family_ids: Sequence[str],
) -> None:
    """Promote validated branch-local products before resume removes planner scratch."""
    if not paths.question_family_batch_artifact.is_file():
        return
    batch = load_model(paths.question_family_batch_artifact, QuestionFamilyBatch)
    family_by_id = {family.question_family_id: family for family in batch.families}
    slugs = assign_family_slugs(family_by_id)
    context = RunContext(run_id=run_id, paths=paths)
    for family_id in family_ids:
        family = family_by_id.get(family_id)
        if family is None:
            continue
        branch_id = f"qfamily-branch-{stable_hash({'run_id': run_id, 'family': family_id})[:12]}"
        handoff = paths.root / run_id / "branches" / branch_id / "planner" / "handoff_manifest.yaml"
        if not handoff.is_file():
            continue
        retained, public_source, audit = _validated_fixed_family_artifacts(
            paths,
            context=context,
            family_id=family_id,
            branch_id=branch_id,
            slug=slugs[family_id],
            development_surrogate=config.is_demo,
            authority_ceiling=batch.authority_ceiling,
        )
        disposition = next(
            item for item in load_run_manifest(paths).families if item.family_id == family_id
        )
        if public_source is not None and audit is not None:
            text = public_source.read_text(encoding="utf-8")
            authority = (
                ArtifactAuthority.PROVISIONAL
                if config.is_demo
                or batch.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
                else ArtifactAuthority.AGENT_REVIEWED
            )
            if (
                batch.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
                and not text.startswith(PROVISIONAL_INSPIRATION_DOSSIER_BANNER)
            ):
                text = PROVISIONAL_INSPIRATION_DOSSIER_BANNER + text
            if config.is_demo and not text.startswith(DEV_SURROGATE_DOSSIER_BANNER):
                text = DEV_SURROGATE_DOSSIER_BANNER + text
            disposition.closure_state = ProductProcessingState.PRODUCED
            disposition.authority = authority
            disposition.dossier_path = (
                paths.family_dossier(slugs[family_id]).relative_to(paths.root).as_posix()
            )

            def _publish_disposition(_path: Path, current: FamilyDisposition = disposition) -> None:
                upsert_family_disposition(context, current)

            promote_text_artifact(
                context,
                text=text,
                destination=paths.family_dossier(slugs[family_id]),
                kind=ArtifactKind.FAMILY_DOSSIER,
                processing_state=ProductProcessingState.PRODUCED,
                authority=authority,
                family_id=family_id,
                after_index=_publish_disposition,
            )
        elif retained:
            current = next(
                (
                    item
                    for item in load_run_manifest(paths).artifacts
                    if item.family_id == family_id
                    and item.kind == ArtifactKind.FAMILY_DOSSIER
                    and item.processing_state == ProductProcessingState.PRODUCED
                ),
                None,
            )
            if current is None:
                write_family_fallback(
                    context,
                    family=family,
                    disposition=disposition,
                    retained=retained,
                )


def _update_family_closure_disposition(
    context: RunContext,
    *,
    family: QuestionFamily,
    outcome: FamilyRunOutcome,
) -> FamilyDisposition:
    disposition = next(
        item
        for item in load_run_manifest(context.paths).families
        if item.family_id == family.question_family_id
    )
    disposition.planning_state = (
        ProductProcessingState.NOT_REACHED
        if outcome.planning_axis == PlanningAxis.NOT_RUN
        else (
            ProductProcessingState.PRODUCED
            if outcome.planning_axis == PlanningAxis.PLAN
            else (
                ProductProcessingState.FAILED
                if outcome.failure_class is not None
                and outcome.failure_class != FailureClass.SCIENTIFIC
                else ProductProcessingState.PRODUCED
            )
        )
    )
    disposition.closure_state = (
        ProductProcessingState.PRODUCED
        if outcome.dossier_axis == DossierAxis.RENDERED
        else (
            ProductProcessingState.FAILED
            if (
                outcome.failure_class is not None
                and outcome.failure_class != FailureClass.SCIENTIFIC
            )
            or outcome.dossier_axis == DossierAxis.RENDER_FAILURE
            else ProductProcessingState.DEGRADED
        )
    )
    disposition.reason = sanitize_family_failure_text(
        outcome.reason or outcome.public_summary_label.value
    )
    return disposition


def _deindex_stale_family_closure(paths: RunPaths, *, family_id: str, slug: str) -> None:
    """Retire old closure current-pointers only after a replacement family view exists."""
    closure_root = paths.family_artifacts(slug) / "dossier_closure"
    closure_prefix = closure_root.relative_to(paths.root).as_posix()
    manifest = load_run_manifest(paths)
    retained = [
        item
        for item in manifest.artifacts
        if not (item.family_id == family_id and item.path.startswith(closure_prefix + "/"))
    ]
    if retained != manifest.artifacts:
        manifest.artifacts = retained
        write_run_manifest(paths, manifest)
    try:
        run_root = paths.root.absolute()
        controlled_closure = closure_root.absolute()
        if not controlled_closure.is_relative_to(run_root):
            return
        ancestor = controlled_closure.parent
        while ancestor != run_root:
            if ancestor.is_symlink():
                return
            parent = ancestor.parent
            if parent == ancestor:
                return
            ancestor = parent
        if not controlled_closure.parent.resolve(strict=True).is_relative_to(
            run_root.resolve(strict=True)
        ):
            return
        if controlled_closure.is_symlink():
            controlled_closure.unlink()
        elif controlled_closure.is_dir():
            shutil.rmtree(controlled_closure)
    except (OSError, RuntimeError):
        # The manifest is authoritative.  Cleanup debris must not turn a valid
        # replacement family view into a failed run.
        pass


def _write_back_half_layout(
    paths: RunPaths,
    *,
    outcomes: Sequence[FamilyRunOutcome],
    family_results: Sequence[MultiFamilyFamilyResult],
    development_surrogate: bool,
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED,
    basis_by_family: dict[str, EvidenceBasis] | None = None,
    run_id: str = "",
    shortlist_digest: str = "",
    reused_included_ids: frozenset[str] = frozenset(),
    resume_note: str = "",
) -> list[FamilyRunOutcome]:
    """Copy each rendered end-user dossier → families/<slug>/ (with the F1 + basis banners) + summary LAST.

    5c-1c: slugs are assigned over SORTED family ids (deterministic across runs and resumes), each
    orchestrated family gets a durable ``family_completion.yaml`` (written AFTER its dossier copy so
    the digests cover it), and reused families' dirs are left untouched.
    """
    basis_by_family = basis_by_family or {}
    slugs = assign_family_slugs(sorted(o.question_family_id for o in outcomes))
    effective_outcomes = list(outcomes)
    outcome_by_id = {o.question_family_id: o for o in effective_outcomes}
    context = (
        RunContext(run_id=run_id or paths.root.name, paths=paths)
        if paths.run_manifest.is_file()
        else None
    )
    family_by_id: dict[str, QuestionFamily] = {}
    if context is not None:
        batch = load_model(paths.question_family_batch_artifact, QuestionFamilyBatch)
        family_by_id = {family.question_family_id: family for family in batch.families}
    for family_result in family_results:
        family_id = family_result.question_family_id
        artifact_paths = list(family_result.artifact_paths)
        slug = slugs.get(family_id, family_slug(family_id))
        dossier_src: Path | None = None
        retained: list[ArtifactRecord] = []
        disposition: FamilyDisposition | None = None
        family_pointer_materialized = False
        projection_hard = False
        if context is not None and family_id in family_by_id:
            try:
                retained, dossier_src, _audit = _validated_fixed_family_artifacts(
                    paths,
                    context=context,
                    family_id=family_id,
                    branch_id=family_result.branch_id,
                    slug=slug,
                    development_surrogate=development_surrogate,
                    authority_ceiling=authority_ceiling,
                    closure_status=family_result.status,
                )
            except HardFamilyIntegrityViolation:
                projection_hard = True
                retained = []
                dossier_src = None
                add_diagnostic(
                    context,
                    diagnostic_class=DiagnosticClass.INTEGRITY,
                    code="family_projection_integrity_terminal",
                    public_message=(
                        "A family artifact failed an integrity boundary and was not promoted."
                    ),
                    family_id=family_id,
                )
                hard_outcome = FamilyRunOutcome.derive(
                    question_family_id=family_id,
                    shortlist_axis=ShortlistAxis.INCLUDED,
                    failure_class=FailureClass.VALIDATION_FAILURE,
                    failed_stage_receipt_id=STAGE_BACK_HALF,
                    dossier_axis=DossierAxis.TERMINAL_RENDERED,
                    reason=FamilyDossierStatus.HARD_INTEGRITY_TERMINAL.value,
                )
                outcome_by_id[family_id] = hard_outcome
                effective_outcomes = [
                    hard_outcome if item.question_family_id == family_id else item
                    for item in effective_outcomes
                ]
            disposition = _update_family_closure_disposition(
                context,
                family=family_by_id[family_id],
                outcome=outcome_by_id[family_id],
            )
        else:
            dossier_src = _find_artifact(artifact_paths, "end_user_dossier.md")
        if family_id and dossier_src:
            dest = paths.family_dir(slug)
            dest.mkdir(parents=True, exist_ok=True)
            text = dossier_src.read_text(encoding="utf-8")
            # DP-2 surface 6: prepend the honest data-basis banner for an abstract-only family, exactly
            # the same driver-side mechanism as the F1 banner (orchestrator untouched). Basis banner
            # first so the F1 authority banner stays at the very top when both apply.
            if basis_by_family.get(family_id) == EvidenceBasis.ABSTRACT_ONLY:
                text = dossier_evidence_basis_banner() + text
            if development_surrogate:
                text = DEV_SURROGATE_DOSSIER_BANNER + text
            if authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION:
                text = PROVISIONAL_INSPIRATION_DOSSIER_BANNER + text
            candidate_path = atomic_write_text(
                paths.family_artifacts(slug) / "public_dossier_candidate.md", text
            )
            if context is not None:
                public_authority = (
                    ArtifactAuthority.PROVISIONAL
                    if development_surrogate
                    or authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
                    else ArtifactAuthority.AGENT_REVIEWED
                )
                promoted = promote_indexed_artifact(
                    context,
                    source=candidate_path,
                    destination=dest / "dossier.md",
                    kind=ArtifactKind.FAMILY_DOSSIER,
                    processing_state=ProductProcessingState.PRODUCED,
                    authority=public_authority,
                    family_id=family_id,
                )
                candidate_path.unlink(missing_ok=True)
                if promoted and disposition is not None:
                    family_pointer_materialized = True
                    disposition.closure_state = ProductProcessingState.PRODUCED
                    disposition.dossier_path = (
                        (dest / "dossier.md").relative_to(paths.root).as_posix()
                    )
                    disposition.authority = public_authority
                    upsert_family_disposition(context, disposition)
                elif disposition is not None:
                    current = next(
                        (
                            item
                            for item in load_run_manifest(paths).artifacts
                            if item.family_id == family_id
                            and item.kind == ArtifactKind.FAMILY_DOSSIER
                            and item.processing_state == ProductProcessingState.PRODUCED
                        ),
                        None,
                    )
                    if current is None:
                        write_family_fallback(
                            context,
                            family=family_by_id[family_id],
                            disposition=disposition,
                            retained=retained,
                        )
                        family_pointer_materialized = True
                    else:
                        disposition.dossier_path = current.path
                        upsert_family_disposition(context, disposition)
            else:
                atomic_write_text(dest / "dossier.md", text)
                candidate_path.unlink(missing_ok=True)
            audit_src = (
                None
                if context is not None
                else _find_artifact(artifact_paths, "end_user_dossier_audit.yaml")
            )
            if audit_src is not None:
                (dest / "audit.yaml").write_text(
                    audit_src.read_text(encoding="utf-8"), encoding="utf-8"
                )
        elif context is not None and disposition is not None:
            current = next(
                (
                    item
                    for item in load_run_manifest(paths).artifacts
                    if item.family_id == family_id
                    and item.kind == ArtifactKind.FAMILY_DOSSIER
                    and item.processing_state == ProductProcessingState.PRODUCED
                ),
                None,
            )
            if current is None:
                write_family_fallback(
                    context,
                    family=family_by_id[family_id],
                    disposition=disposition,
                    retained=retained,
                )
                family_pointer_materialized = True
            else:
                disposition.dossier_path = current.path
                upsert_family_disposition(context, disposition)
        if (
            context is not None
            and family_pointer_materialized
            and family_result.status
            not in {
                FamilyDossierStatus.PUBLIC_DOSSIER_REVISION_REQUIRED,
                FamilyDossierStatus.PROVENANCE_INTEGRITY_TERMINAL,
            }
        ):
            _deindex_stale_family_closure(paths, family_id=family_id, slug=slug)
        if family_id and family_id in outcome_by_id and not projection_hard:
            record = _family_completion_record(
                paths,
                run_id=run_id or paths.root.name,
                shortlist_digest=shortlist_digest,
                slug=slug,
                family_result=family_result,
                outcome=outcome_by_id[family_id],
            )
            dump_data(record, paths.family_completion(slug))
            if not family_result.error and paths.run_manifest.is_file():
                _clear_current_family_incomplete_diagnostic(
                    paths,
                    question_family_id=family_id,
                )
    # DP-2 surface 7: aggregate basis line over INCLUDED families (freshly orchestrated + reused).
    included_ids = {fr.question_family_id for fr in family_results} | set(reused_included_ids)
    included_ids.discard("")
    abstract_only_families = sum(
        1
        for family_id in included_ids
        if basis_by_family.get(family_id) == EvidenceBasis.ABSTRACT_ONLY
    )
    basis_line = summary_evidence_basis_line(abstract_only_families, len(included_ids))
    # summary.md is written ATOMICALLY + LAST (after every family reached a terminal + dossiers landed).
    summary_path = write_run_summary(
        paths,
        effective_outcomes,
        development_surrogate=development_surrogate,
        authority_ceiling=authority_ceiling,
        evidence_basis_line=basis_line,
        resume_note=resume_note,
    )
    if context is not None:
        degraded = any(
            (outcome.failure_class is not None and outcome.failure_class != FailureClass.SCIENTIFIC)
            or outcome.warning_class is not None
            or outcome.dossier_axis == DossierAxis.TERMINAL_RENDERED
            or outcome.dossier_axis == DossierAxis.RENDER_FAILURE
            for outcome in effective_outcomes
        )
        index_existing_artifact(
            context,
            summary_path,
            kind=ArtifactKind.SUMMARY,
            processing_state=(
                ProductProcessingState.DEGRADED if degraded else ProductProcessingState.PRODUCED
            ),
            authority=(
                ArtifactAuthority.PROVISIONAL
                if development_surrogate
                or authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
                else ArtifactAuthority.AGENT_REVIEWED
            ),
        )
    return effective_outcomes


# --- the composed A→G run -------------------------------------------------------------------------
def _shortlist_outcomes_from_manifest(
    manifest: QuestionFamilyShortlistManifest,
) -> list[FamilyShortlistOutcome]:
    """Reconstruct the per-family shortlist outcomes for the questions/ human view from the manifest.

    The authoritative outcome record is ``summary.md`` (DP-3) + the persisted branch state; this is the
    honest questions-layout projection (bucket → label), not a second source of truth.
    """
    outcomes = [
        FamilyShortlistOutcome(
            question_family_id=sf.family.question_family_id,
            label=FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW,
            gate_decision="accept",
            active_variant_ids=list(sf.active_variant_ids),
        )
        for sf in manifest.shortlisted
    ]
    for fid in manifest.rejected_family_ids:
        outcomes.append(
            FamilyShortlistOutcome(
                question_family_id=fid,
                label=FamilyInclusionLabel.REJECTED_SCIENTIFIC,
                gate_decision="reject",
            )
        )
    for fid in manifest.needs_revision_family_ids:
        outcomes.append(
            FamilyShortlistOutcome(
                question_family_id=fid,
                label=FamilyInclusionLabel.DEFERRED_MATERIAL_REVISION,
                gate_decision="revise",
            )
        )
    for fid in manifest.deferred_family_ids:
        outcomes.append(
            FamilyShortlistOutcome(
                question_family_id=fid,
                label=FamilyInclusionLabel.DEFERRED_INSUFFICIENT_EVIDENCE,
                gate_decision="defer",
            )
        )
    return outcomes


# --- evidence-basis propagation ---
def evidence_basis_by_family(
    payload: QuestionScientistContextPayloadV2, families: Sequence[QuestionFamily]
) -> dict[str, EvidenceBasis]:
    """Worst-case family basis: abstract_only if ANY supporting topic claim is abstract-only.

    Derived from the pack's per-claim ``evidence_basis`` (the single source of truth); a family whose
    referenced claims are unknown is treated conservatively as abstract_only — never falsely fulltext.
    """
    basis_by_claim = {
        card.claim_id: card.evidence_basis for card in payload.topic_literature.claim_cards
    }
    result: dict[str, EvidenceBasis] = {}
    for family in families:
        referenced = [
            basis_by_claim[claim_id]
            for claim_id in family.source_topic_claim_ids
            if claim_id in basis_by_claim
        ]
        if not referenced or any(basis == EvidenceBasis.ABSTRACT_ONLY for basis in referenced):
            result[family.question_family_id] = EvidenceBasis.ABSTRACT_ONLY
        else:
            result[family.question_family_id] = EvidenceBasis.FULLTEXT_BACKED
    return result


def _topic_basis_banner(payload: QuestionScientistContextPayloadV2) -> str:
    abstract_only, total = abstract_only_gap_and_strong_claim_counts(
        payload.topic_literature.open_gap_cards, payload.topic_literature.claim_cards
    )
    return topic_evidence_basis_banner(abstract_only, total)


def run_end_to_end(
    config: MaieusisProjectConfig,
    *,
    drafts: Sequence[PaperCaseDraft],
    executor: StageExecutor,
    topic_source_table: TopicSourceTable | None = None,
    topic_r5_source_table: R5TopicEvidenceSourceTable | None = None,
    family_count: int = 6,
    variants_per_family: int = 3,
    paper_input_digests: dict[str, str] | None = None,
    run_context: RunContext | None = None,
) -> RunResult:
    """Initialize one visible envelope, execute the chain, and preserve it on every Exception."""
    context = run_context or initialize_run(config.run.output_root)
    if load_run_manifest(context.paths).run_state == RunProcessingState.INITIALIZED:
        set_run_state(
            context,
            RunProcessingState.RUNNING,
            next_action="Scientific processing is running; inspect retained products here.",
        )
    try:
        result = _run_end_to_end_initialized(
            config,
            drafts=drafts,
            executor=executor,
            topic_source_table=topic_source_table,
            topic_r5_source_table=topic_r5_source_table,
            family_count=family_count,
            variants_per_family=variants_per_family,
            paper_input_digests=paper_input_digests,
            run_context=context,
        )
    except Exception:
        if load_run_manifest(context.paths).run_state not in {
            RunProcessingState.FAILED,
            RunProcessingState.INCOMPLETE,
        }:
            record_run_failure(context, code="run_exception")
        raise
    _finalize_run_envelope(context, result)
    # Presentation is a redrawable default add-on. Scientific state and all six receipts are fixed
    # before this best-effort call, and any add-on fault is intentionally non-propagating.
    from ..presentation.materialize import try_materialize_detailed_presentation

    try_materialize_detailed_presentation(context)
    return result


def _run_end_to_end_initialized(
    config: MaieusisProjectConfig,
    *,
    drafts: Sequence[PaperCaseDraft],
    executor: StageExecutor,
    topic_source_table: TopicSourceTable | None = None,
    topic_r5_source_table: R5TopicEvidenceSourceTable | None = None,
    family_count: int = 6,
    variants_per_family: int = 3,
    paper_input_digests: dict[str, str] | None = None,
    run_context: RunContext,
) -> RunResult:
    """`maieusis run`: the whole chain ONCE (fresh run_id) → the fixed ``runs/<id>/`` layout.

    A→G: paper half (gate→traces→patterns) with the dataset half (narrator + topic) → stage C (V2
    context) → stage D (families→shortlist) → front-half layout → back half (orchestrator→dossiers +
    ``summary.md``). ZERO human import throughout; the run ends at planning dossiers (R5-011 stays
    blocked). Guards: a dataset link is required, and a populated run_id fails cleanly (resume it with
    `maieusis resume`). Every provider/host/session is built ONLY through ``executor`` (F6). Each stage
    boundary emits a StageReceipt; ``paper_input_digests`` lets the CLI path record the raw inbox-PDF
    digests so a resume can decide REUSE without re-paying ingestion.
    """
    assert_dataset_link_present(config)
    run_id = run_context.run_id
    run_root = run_context.paths.root
    paths = run_context.paths

    with acquire_run_lock(run_root, command="maieusis run"):
        # A/B: front half — paper (gate→traces→patterns) with dataset (narrator + topic) → corpus.
        if config.paperbank.import_from_run is None:
            paper_result = exec_stage_paper_half(
                config, executor, paths, drafts, input_digests=paper_input_digests
            )
        else:
            paper_result = _project_imported_paper_half(
                run_context, import_paperbank_from_run(config, run_context)
            )
        # Honest run terminal: zero accepted papers OR zero usable patterns ⇒ nothing to develop.
        # Stop with a scientific run terminal + summary.md, never crash stage C on the missing manifest.
        if _paper_half_is_terminal(paper_result):
            return _paper_half_run_terminal(paths, run_id, paper_result)
        # Q2: the dataset half + stage C are the only front-half stages without an honest terminal.
        # A narrative/topic/compile fail-closed verdict (narrator or topic reject/revise, readiness
        # failed, blocked source, empty/thin table, unreadable user doc, or an unparseable gate review)
        # is a ValueError/ValidationError — convert it to a persisted SCIENTIFIC_TERMINAL + summary.md
        # instead of an uncaught traceback. The gate DECISION stays fail-closed; only the shape changes.
        # A genuine code/infrastructure bug (other exception types) still surfaces as a real traceback.
        try:
            exec_stage_dataset_half(
                config,
                executor,
                paths,
                topic_source_table=topic_source_table,
                topic_r5_source_table=topic_r5_source_table,
            )
        except (ValueError, ValidationError) as exc:
            return _dataset_context_run_terminal(
                config, paths, run_id, exc, stage=STAGE_DATASET_HALF
            )
        # C: research intent + V2 context (ZERO human import) → D: families → shortlist manifest.
        # Only the compiler's typed SCIENTIFIC readiness verdict belongs in the scientific-terminal
        # path. Pydantic/compiler/provenance/identity invariants are product failures and must reach
        # the outer run envelope as incomplete rather than masquerading as scientific insufficiency.
        try:
            exec_stage_c(config, paths)
        except QuestionScientistContextReadinessError as exc:
            return _dataset_context_run_terminal(config, paths, run_id, exc, stage=STAGE_C)
        try:
            exec_stage_d(
                config,
                executor,
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
            return _stage_d_run_terminal(config, paths, run_id, exc)
        # Front-half human-view layout (persisted artifacts only — identical fresh and resumed).
        exec_front_layout(config, paths)
        manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
        if not manifest.planning_eligible:
            return _planning_ineligible_run_terminal(config, paths, run_id)
        # G: back half — orchestrator over the shortlist → dossiers + summary.md (written LAST).
        return exec_back_half(config, executor, paths, run_id)


def _finalize_run_envelope(context: RunContext, result: RunResult) -> None:
    projection_degraded = result.run_terminal is not None or any(
        (outcome.failure_class is not None and outcome.failure_class != FailureClass.SCIENTIFIC)
        or outcome.warning_class is not None
        or outcome.dossier_axis == DossierAxis.TERMINAL_RENDERED
        or outcome.dossier_axis == DossierAxis.RENDER_FAILURE
        for outcome in result.family_outcomes
    )
    infrastructure_incomplete = (
        result.run_terminal is not None
        and result.run_terminal.failure_class != FailureClass.SCIENTIFIC
    ) or any(
        outcome.failure_class is not None and outcome.failure_class != FailureClass.SCIENTIFIC
        for outcome in result.family_outcomes
    )
    accepted_count = sum(
        outcome.dossier_axis == DossierAxis.RENDERED for outcome in result.family_outcomes
    )
    authority_ceiling = FrontHalfAuthorityCeiling.VERIFIED
    shortlist_path = find_shortlist_path(context.paths)
    if shortlist_path.is_file():
        authority_ceiling = load_model(
            shortlist_path, QuestionFamilyShortlistManifest
        ).authority_ceiling
    if context.paths.summary.is_file():
        index_existing_artifact(
            context,
            context.paths.summary,
            kind=ArtifactKind.SUMMARY,
            processing_state=(
                ProductProcessingState.DEGRADED
                if projection_degraded
                else ProductProcessingState.PRODUCED
            ),
            authority=(
                ArtifactAuthority.PROVISIONAL
                if result.development_surrogate
                or authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
                else ArtifactAuthority.AGENT_REVIEWED
            ),
        )
    if infrastructure_incomplete:
        set_run_state(
            context,
            RunProcessingState.INCOMPLETE,
            next_action=(
                "Shared or family infrastructure processing is incomplete; read any retained "
                "family dossiers, inspect diagnostics, then resume after correcting the failure."
            ),
        )
    else:
        set_run_state(
            context,
            RunProcessingState.COMPLETE,
            next_action=(
                "Review every family dossier and hidden audit artifact; warning and scientific "
                "terminal dossiers remain useful without accepted-plan authority."
                if projection_degraded
                else (
                    "Review the family dossiers and hidden audit artifacts."
                    if accepted_count
                    else "All families reached honest scientific terminals; inspect their retained "
                    "plans, outcome dossiers, and review diagnostics before revising inputs."
                )
            ),
        )


def _dataset_context_run_terminal(
    config: MaieusisProjectConfig,
    paths: RunPaths,
    run_id: str,
    exc: Exception,
    *,
    stage: str,
    resume_note: str = "",
) -> RunResult:
    """Honest run-level SCIENTIFIC terminal for a dataset-half / stage-C fail-closed verdict (Q2).

    The narrator/topic gates and the stage-C compiler stay fail-closed — a rejected narrative or brief
    must NOT proceed to families. This only turns the resulting ValueError/ValidationError into a
    persisted SCIENTIFIC_TERMINAL receipt + a run-terminal summary.md (never a bare traceback), so the
    run reports an honest scientific stop. Mirrors ``_stage_d_run_terminal`` / ``_paper_half_run_terminal``.

    The raw exception can carry model/gate content (a topic brief or compile error may mention firewalled
    terms like ``execution`` / ``p-value``), so it goes to an INTERNAL diagnostic only. The receipt
    detail + run-terminal summary use a cause-neutral, public-text-guard-safe reason — the receipt
    detail is re-surfaced as the public reason on resume, so it too must be clean.
    """
    diagnostic_path = write_gate_diagnostic(
        GateDiagnostic(
            gate_name=f"{stage}_terminal",
            decision=GateDecision.REJECT,
            rationale=str(exc)[:2000],
        ),
        _diagnostics_dir(paths.corpus),
    )
    if paths.run_manifest.is_file():
        add_diagnostic(
            RunContext(run_id=run_id, paths=paths),
            diagnostic_class=DiagnosticClass.SCIENTIFIC,
            code=f"{stage}_terminal",
            public_message="A shared scientific context stage ended without usable downstream input.",
            internal_path=diagnostic_path.relative_to(paths.root).as_posix(),
        )
    reason = _public_scientific_terminal_reason(stage)
    retained_candidates = [
        paths.corpus / "context" / "dataset_narratives",
        paths.corpus / "context" / "topic_evidence",
        paths.dataset_narrative,
        paths.research_scope,
        paths.retrieval_summary,
        _diagnostics_dir(paths.corpus),
        paths.stage_output(STAGE_DATASET_HALF),
        paths.corpus / "research_intent.yaml",
    ]
    retained_paths = [path for path in retained_candidates if path.exists() or path.is_symlink()]
    input_digests = upstream_input_digests(paths, stage)
    if stage == STAGE_DATASET_HALF:
        input_digests = {
            **compute_dataset_half_input_digests(config),
            **input_digests,
        }
    _emit_stage_receipt(
        paths,
        config,
        stage,
        input_digests=input_digests,
        output_paths=retained_paths,
        status=StageStatus.SCIENTIFIC_TERMINAL,
        failure_class=FailureClass.SCIENTIFIC,
        detail=reason,
    )
    terminal = RunTerminal(
        failed_stage=stage,
        failed_stage_receipt_id=stage,
        failure_class=FailureClass.SCIENTIFIC,
        reason=reason,
    )
    write_run_terminal_summary(paths, terminal, resume_note=resume_note)
    return RunResult(run_id=run_id, run_terminal=terminal)


def _public_scientific_terminal_reason(stage: str) -> str:
    """A cause-neutral, public-text-guard-safe run-terminal reason for a front-half scientific stop.
    Never embeds raw model/gate text (which can contain firewalled terms); the technical cause lives in
    the run diagnostics."""
    what = {
        STAGE_DATASET_HALF: "the dataset narrative and topic literature evidence",
        STAGE_C: "the research question context",
    }.get(stage, "the run inputs")
    return (
        f"this run did not have enough usable evidence in {what} to develop any question, so no "
        "question families were produced; see the run diagnostics for details"
    )


def _stage_d_run_terminal(
    config: MaieusisProjectConfig,
    paths: RunPaths,
    run_id: str,
    exc: Exception,
    *,
    resume_note: str = "",
) -> RunResult:
    """Persist one finite Stage-D scientific or infrastructure terminal."""
    failure_kind, failure_class, status = _classify_stage_d_failure(exc)
    scientific = failure_kind == StageDFailureKind.ALL_QUALITY_DROPPED
    diagnostic_path = write_gate_diagnostic(
        GateDiagnostic(
            gate_name=_next_stage_d_terminal_gate_name(_diagnostics_dir(paths.corpus)),
            decision=(GateDecision.REJECT if scientific else GateDecision.INFRASTRUCTURE_FAILURE),
            rationale=str(exc)[:2000],
        ),
        _diagnostics_dir(paths.corpus),
    )
    payload = load_model(find_payload_path(paths), QuestionScientistContextPayloadV2)
    if isinstance(exc, NoValidFamilies):
        retained_batch = None
        processed = exc.processed_candidates
    else:
        carried_path = getattr(exc, _STAGE_D_CURRENT_BATCH_ATTRIBUTE, "")
        retained_batch = (
            paths.root / carried_path
            if isinstance(carried_path, str) and carried_path
            else paths.question_family_batch_artifact
        )
        retained = (
            load_model(retained_batch, QuestionFamilyBatch) if retained_batch.is_file() else None
        )
        if retained is None or (retained.context_id, retained.context_digest) != (
            payload.context_id,
            payload.context_digest,
        ):
            retained_batch = None
            processed = []
        else:
            processed = [
                StageDProcessedCandidate(
                    question_family_id=family.question_family_id,
                    disposition=StageDCandidateDisposition.RETAINED,
                )
                for family in retained.families
            ]
    if retained_batch is not None and not processed:
        retained_batch = None
    outcome_path = dump_data(
        StageDOutcomeRecord(
            outcome_id=f"stage-d-outcome-{payload.context_digest[:12]}",
            context_id=payload.context_id,
            context_digest=payload.context_digest,
            stage_status=status,
            failure_class=failure_class,
            failure_kind=failure_kind,
            processed_candidates=processed,
            retained_batch_path=(
                retained_batch.relative_to(paths.root).as_posix() if retained_batch else ""
            ),
            retained_batch_digest=sha256_file(retained_batch) if retained_batch else "",
        ),
        paths.stage_output(STAGE_D),
    )
    if paths.run_manifest.is_file():
        add_diagnostic(
            RunContext(run_id=run_id, paths=paths),
            diagnostic_class=(
                DiagnosticClass.SCIENTIFIC if scientific else DiagnosticClass.INFRASTRUCTURE
            ),
            code="stage_d_terminal",
            public_message=(
                "No generated question family passed strict quality validation."
                if scientific
                else "Question-family generation stopped because its configured model service was unavailable."
            ),
            internal_path=diagnostic_path.relative_to(paths.root).as_posix(),
        )
    reason = (
        (
            "this run produced no valid question families after every real candidate was processed "
            "by the quality gate; see the run diagnostics for details"
        )
        if scientific
        else (
            "question-family generation could not complete because its configured model service "
            "was unavailable; earlier products remain available and the run can be resumed"
        )
    )
    retained_outputs = [
        path
        for path in [paths.corpus / "question_families", diagnostic_path, outcome_path]
        if path.exists()
    ]
    _emit_stage_receipt(
        paths,
        config,
        STAGE_D,
        input_digests=upstream_input_digests(paths, STAGE_D),
        output_paths=retained_outputs,
        status=status,
        failure_class=failure_class,
        detail=reason,
    )
    terminal = RunTerminal(
        failed_stage=STAGE_D,
        failed_stage_receipt_id=STAGE_D,
        failure_class=failure_class,
        reason=reason,
    )
    write_run_terminal_summary(paths, terminal, resume_note=resume_note)
    return RunResult(run_id=run_id, run_terminal=terminal)


def _classify_stage_d_failure(
    exc: Exception,
) -> tuple[StageDFailureKind, FailureClass, StageStatus]:
    if isinstance(exc, NoValidFamilies):
        return (
            StageDFailureKind.ALL_QUALITY_DROPPED,
            FailureClass.SCIENTIFIC,
            StageStatus.SCIENTIFIC_TERMINAL,
        )
    if isinstance(exc, StageDPromptBudgetError):
        return (
            StageDFailureKind.PROMPT_BUDGET,
            FailureClass.PROMPT_BUDGET,
            StageStatus.INFRASTRUCTURE_FAILED,
        )
    if isinstance(exc, ModelConfigurationError):
        return (
            StageDFailureKind.CONFIGURATION_UNAVAILABLE,
            FailureClass.VALIDATION_FAILURE,
            StageStatus.INFRASTRUCTURE_FAILED,
        )
    if isinstance(exc, StructuredModelProviderError):
        structured_mapping = {
            StructuredModelFailureKind.AUTHENTICATION: StageDFailureKind.PROVIDER_AUTHENTICATION,
            StructuredModelFailureKind.RATE_LIMIT: StageDFailureKind.PROVIDER_RATE_LIMIT,
            StructuredModelFailureKind.TIMEOUT: StageDFailureKind.PROVIDER_TIMEOUT,
            StructuredModelFailureKind.CONNECTION: StageDFailureKind.PROVIDER_CONNECTION,
            StructuredModelFailureKind.SERVER_ERROR: StageDFailureKind.PROVIDER_SERVER_ERROR,
            StructuredModelFailureKind.INVALID_RESPONSE: StageDFailureKind.PROVIDER_INVALID_RESPONSE,
            StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID: (
                StageDFailureKind.STRUCTURED_OUTPUT_INVALID
            ),
        }
        failure_class = (
            FailureClass.SCHEMA_ERROR
            if exc.kind == StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID
            else FailureClass.PROVIDER_FAILURE
        )
        status = (
            StageStatus.EXTERNAL_CALL_UNCERTAIN
            if exc.kind == StructuredModelFailureKind.TIMEOUT
            else StageStatus.INFRASTRUCTURE_FAILED
        )
        return structured_mapping[exc.kind], failure_class, status
    if isinstance(exc, ScientificAgentSessionError):
        scientific_mapping = {
            ScientificAgentFailureKind.AUTHENTICATION: StageDFailureKind.PROVIDER_AUTHENTICATION,
            ScientificAgentFailureKind.RATE_LIMIT: StageDFailureKind.PROVIDER_RATE_LIMIT,
            ScientificAgentFailureKind.TIMEOUT: StageDFailureKind.PROVIDER_TIMEOUT,
            ScientificAgentFailureKind.CONNECTION: StageDFailureKind.PROVIDER_CONNECTION,
            ScientificAgentFailureKind.SERVER_ERROR: StageDFailureKind.PROVIDER_SERVER_ERROR,
            ScientificAgentFailureKind.INVALID_RESPONSE: StageDFailureKind.PROVIDER_INVALID_RESPONSE,
            ScientificAgentFailureKind.STRUCTURED_OUTPUT_INVALID: (
                StageDFailureKind.STRUCTURED_OUTPUT_INVALID
            ),
        }
        failure_class = (
            FailureClass.SCHEMA_ERROR
            if exc.kind == ScientificAgentFailureKind.STRUCTURED_OUTPUT_INVALID
            else FailureClass.PROVIDER_FAILURE
        )
        status = (
            StageStatus.EXTERNAL_CALL_UNCERTAIN
            if exc.kind == ScientificAgentFailureKind.TIMEOUT
            else StageStatus.INFRASTRUCTURE_FAILED
        )
        return scientific_mapping[exc.kind], failure_class, status
    if isinstance(exc, ScientificAgentInfrastructureError):
        return (
            StageDFailureKind.REVIEWER_PROVIDER_FAILURE,
            FailureClass.PROVIDER_FAILURE,
            StageStatus.INFRASTRUCTURE_FAILED,
        )
    raise TypeError(f"unsupported Stage-D expected failure type: {type(exc).__name__}")


def _next_stage_d_terminal_gate_name(diagnostics_dir: Path) -> str:
    base = f"{STAGE_D}_terminal"
    if not (diagnostics_dir / f"{base}.yaml").exists():
        return base
    index = 1
    while (diagnostics_dir / f"{base}-{index:03d}.yaml").exists():
        index += 1
    return f"{base}-{index:03d}"


def _planning_ineligible_run_terminal(
    config: MaieusisProjectConfig,
    paths: RunPaths,
    run_id: str,
    *,
    resume_note: str = "",
) -> RunResult:
    manifest = load_model(find_shortlist_path(paths), QuestionFamilyShortlistManifest)
    if (
        manifest.authority_ceiling != FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
        or manifest.planning_eligible
    ):
        raise ValueError("planning-ineligible terminal requires a provisional shortlist")
    diagnostic_path = write_gate_diagnostic(
        GateDiagnostic(
            gate_name=_PROVISIONAL_PLANNING_BOUNDARY_DIAGNOSTIC,
            decision=GateDecision.INSUFFICIENT_EVIDENCE,
            rationale=(
                "provisional_inspiration authority cannot enter the verified planning route"
            ),
        ),
        _diagnostics_dir(paths.corpus),
    )
    if paths.run_manifest.is_file():
        add_diagnostic(
            RunContext(run_id=run_id, paths=paths),
            diagnostic_class=DiagnosticClass.SCIENTIFIC,
            code="provisional_planning_ineligible",
            public_message=(
                "Provisional question families remain visible but cannot enter planning yet."
            ),
            internal_path=diagnostic_path.relative_to(paths.root).as_posix(),
        )
    reason = (
        "question families were retained as provisional inspiration and are not eligible for the "
        "current verified planning route; review the visible families and evidence limitations"
    )
    outputs = [
        path
        for path in [
            find_shortlist_path(paths),
            paths.question_family_batch_artifact,
            paths.question_families,
            paths.shortlist,
            diagnostic_path,
        ]
        if path.exists()
    ]
    _emit_stage_receipt(
        paths,
        config,
        STAGE_BACK_HALF,
        input_digests=upstream_input_digests(paths, STAGE_BACK_HALF),
        output_paths=outputs,
        status=StageStatus.SCIENTIFIC_TERMINAL,
        failure_class=FailureClass.SCIENTIFIC,
        detail=reason,
    )
    terminal = RunTerminal(
        failed_stage=STAGE_BACK_HALF,
        failed_stage_receipt_id=STAGE_BACK_HALF,
        failure_class=FailureClass.SCIENTIFIC,
        reason=reason,
    )
    write_run_terminal_summary(paths, terminal, resume_note=resume_note)
    return RunResult(run_id=run_id, run_terminal=terminal)


def _paper_half_run_terminal(
    paths: RunPaths, run_id: str, paper_result: PaperHalfResult
) -> RunResult:
    """Build + persist the honest run-level SCIENTIFIC terminal for a zero-accepted paper half."""
    if paths.run_manifest.is_file():
        add_diagnostic(
            RunContext(run_id=run_id, paths=paths),
            diagnostic_class=DiagnosticClass.SCIENTIFIC,
            code="paper_half_terminal",
            public_message="The paper stage produced no usable reviewed question pattern.",
        )
    terminal = RunTerminal(
        failed_stage=STAGE_PAPER_HALF,
        failed_stage_receipt_id=STAGE_PAPER_HALF,
        failure_class=FailureClass.SCIENTIFIC,
        reason=_paper_half_terminal_detail(paper_result),
    )
    write_run_terminal_summary(paths, terminal)
    return RunResult(run_id=run_id, run_terminal=terminal)


def maybe_write_paper_half_terminal_summary(
    paths: RunPaths, *, resume_note: str = ""
) -> Path | None:
    """If the persisted paper-half receipt is a SCIENTIFIC_TERMINAL (zero accepted papers), write the
    run-terminal summary from the receipt's recorded reason and return it — else None. Lets the resume
    path report the same honest terminal (instead of crashing stage C) whether the receipt was reused
    or freshly re-run."""
    receipt = read_stage_receipt(paths, STAGE_PAPER_HALF)
    if receipt is None or receipt.status != StageStatus.SCIENTIFIC_TERMINAL:
        return None
    terminal = RunTerminal(
        failed_stage=STAGE_PAPER_HALF,
        failed_stage_receipt_id=STAGE_PAPER_HALF,
        failure_class=FailureClass.SCIENTIFIC,
        reason=receipt.detail,
    )
    return write_run_terminal_summary(paths, terminal, resume_note=resume_note)


# --- CLI orchestration entrypoint -----------------------------------------------------------------
def retrieve_topic_source_table(
    config: MaieusisProjectConfig, scope: ResolvedResearchScope
) -> TopicSourceTable:
    """LIVE generic topic retrieval for the research intent (external HTTP — the user's gated step).

    Domain-neutral: the query lanes come from ``generic_topic_lanes`` and the scope's OWN terms.

    The opt-in paid Elicit source is threaded here (the ONLY driver seam; both ``maieusis run`` and
    ``maieusis resume`` call this): ``config.literature.source_profile`` selects the source families and
    ``ELICIT_API_KEY`` (env-only, NEVER persisted) unlocks Elicit for the ``auto`` profile. Default
    ``public`` ⇒ no Elicit lane and no spend. The harvester itself already reads ``ELICIT_API_KEY`` from
    the env, so the key is not passed to it (and never lands in a config, receipt, or artifact).
    """
    from ..retrieval.generic_topic_lanes import build_generic_topic_evidence_query_plan
    from ..retrieval.topic_sources import TopicSourceHarvester

    plan = build_generic_topic_evidence_query_plan(
        scope,
        source_profile=config.literature.source_profile,
        elicit_api_key=os.getenv("ELICIT_API_KEY", ""),
    )
    return TopicSourceHarvester(max_records=20).harvest(plan)


def ingest_paper_drafts(
    config: MaieusisProjectConfig,
    executor: StageExecutor,
    *,
    run_context: RunContext | None = None,
) -> list[PaperCaseDraft]:
    """LIVE paper ingestion: extract each inbox PDF → a pre-gate ``PaperCaseDraft`` (paid extraction).

    Runs the real ``PaperIngestPipeline`` over ``paperbank.inbox_dir`` then loads each written PaperCase +
    local-literature sidecar into a draft (``run_paper_half`` re-gates them). Paid/parser work — the
    user's gated step; the CLI wiring itself is exercised by tests that inject drafts directly.
    """
    from ..paper_ingest.pipeline import PaperIngestPipeline, PaperIngestPipelineConfig

    provider = executor.generation_provider("extraction")
    corpus_root = config.run.output_root / "ingest_corpus"
    openalex_coordinator = build_openalex_request_coordinator(config)
    pipeline = PaperIngestPipeline(
        model_provider=provider,
        # Real cited-work lookup (config-gated): previously the product path passed NO providers,
        # so references resolved against the Null provider and no abstract was ever fetched —
        # the estimate-vs-driver wiring class again. OpenAlex-first for abstract-bearing records.
        lookup_providers=build_paper_lookup_providers(
            config, openalex_coordinator=openalex_coordinator
        ),
        # P1: DOI-keyed whole-bibliography fallback — when PDF reference parsing is thin, pull the
        # paper's full reference list so cited-work resolution + abstracts are not starved. Config-gated.
        source_reference_providers=build_source_reference_providers(
            config, openalex_coordinator=openalex_coordinator
        ),
        config=PaperIngestPipelineConfig(
            inbox_dir=config.paperbank.inbox_dir,
            output_root=corpus_root,
            # Honor the operator's parser + parallelism config: the pipeline-dataclass defaults
            # ("auto" parser, 1 worker) silently overrode paperbank.parser / paperbank.max_workers
            # in real runs — the docling full-page-OCR live-run bug lived exactly here.
            parser_name=config.paperbank.parser,
            max_workers=config.paperbank.max_workers,
            provider_name=provider.provider_id,
            model_name=getattr(provider, "model_name", ""),
            external_lookup=config.literature.enabled,
            # Honor the operator's cited-literature + key-citation-selection config. These were
            # OMITTED before, so the pipeline used its dataclass defaults (select_key_citations=False)
            # even though PaperBankConfig defaults them True — importance_selection was never built,
            # which crashed the downstream citation gate + trace context (the wiring class again).
            cited_literature=config.paperbank.cited_literature,
            select_key_citations=config.paperbank.select_key_citations,
            citation_prompt_char_budget=config.paperbank.citation_prompt_char_budget,
            min_local_reference_count=config.paperbank.min_local_reference_count,
            # source_span is REQUIRED downstream (the traces reference parser-owned source_span_ids);
            # it is deliberately hardcoded, not read from config.paperbank.evidence_mode.
            evidence_mode="source_span",
        ),
    )
    manifest = pipeline.run(all_papers=True)
    if run_context is not None:
        ingest_manifest_path = atomic_write_model(
            run_context.paths.ingest_manifest_artifact, manifest
        )
        index_existing_artifact(
            run_context,
            ingest_manifest_path,
            kind=ArtifactKind.INGEST_MANIFEST,
            processing_state=ProductProcessingState.PRODUCED,
            authority=ArtifactAuthority.UNKNOWN,
        )
        for item in manifest.items:
            upsert_paper_disposition(
                run_context,
                PaperDisposition(
                    input_identity=item.paper_id,
                    input_path=str(Path(manifest.inbox_dir) / item.filename),
                    paper_id=item.paper_id,
                    disposition=(
                        PaperDispositionKind.PENDING
                        if item.paper_case_artifact
                        else PaperDispositionKind.UNAVAILABLE
                    ),
                    reason="" if item.paper_case_artifact else "no extracted PaperCase",
                ),
            )
    drafts: list[PaperCaseDraft] = []
    for item in manifest.items:
        if not item.paper_case_artifact:
            drafts.append(
                PaperCaseDraft(paper_id=item.paper_id, parseable=False, parse_error="not_extracted")
            )
            continue
        case = load_model(Path(item.paper_case_artifact), PaperCase)
        if item.local_literature_artifact:
            literature = load_model(
                Path(item.local_literature_artifact), PaperLocalLiteratureContext
            )
        else:
            # Honest degrade, not a crash: with paperbank.cited_literature AND select_key_citations
            # both disabled the pipeline never writes the literature sidecar, and the manifest
            # records exactly which artifacts exist (symmetric with the paper_case_artifact check
            # above — the old unconditional path load raised FileNotFoundError here). Synthesize an
            # EMPTY literature context so the paper still enters the gate and stands on fidelity
            # alone (the selection-less path); the warning surfaces the config-gated degrade.
            literature = PaperLocalLiteratureContext(
                context_id=f"pll-{case.paper_case_id}-disabled",
                paper_case_id=case.paper_case_id,
                source_paper_id=item.paper_id,
                source_sha256=case.source_sha256,
                warnings=[
                    "cited-literature collection disabled by config; paper gated on fidelity alone"
                ],
            )
        drafts.append(
            PaperCaseDraft(paper_id=item.paper_id, paper_case=case, literature=literature)
        )
    return drafts


def effective_family_count(config: MaieusisProjectConfig, family_count: int) -> int:
    """Resolve generation to the smaller of the product cap and an injected fixture ceiling."""
    return min(config.run.max_families, family_count)


def effective_variants_per_family(
    config: MaieusisProjectConfig, variants_per_family: int | None
) -> int:
    """Use the public config unless an internal/test driver explicitly supplies the count."""
    return config.run.variants_per_family if variants_per_family is None else variants_per_family


def execute_run_from_config(
    config: MaieusisProjectConfig,
    *,
    run_context: RunContext | None = None,
    executor: StageExecutor | None = None,
    drafts: Sequence[PaperCaseDraft] | None = None,
    topic_source_table: TopicSourceTable | None = None,
    topic_r5_source_table: R5TopicEvidenceSourceTable | None = None,
    family_count: int = 6,
    variants_per_family: int | None = None,
) -> Path:
    """The `maieusis run` core: resolve executor + inputs → run the whole chain → return the summary.md path.

    ``executor`` defaults to a real ``StageExecutor(config)``; ``drafts`` and ``topic_source_table``
    default to the LIVE ingestion + retrieval helpers (paid/external — the user's gated step). Tests
    inject all three so the full A→G wiring is exercised with ZERO paid calls / zero spawns. Real live
    runs additionally need topic FULLTEXT enrichment (pass ``topic_r5_source_table``); without it stage C
    rejects abstract-only open-gap support — the one remaining generic gap (tracked in the 5c-1b tail).

    ``run.max_families`` caps how many families are generated and ``run.variants_per_family`` sets
    the requested family shape (so the run costs what ``check`` estimated). Explicit function
    arguments remain an internal/test injection seam.
    """
    context = run_context or initialize_run(config.run.output_root)
    if load_run_manifest(context.paths).run_state == RunProcessingState.INITIALIZED:
        set_run_state(
            context,
            RunProcessingState.RUNNING,
            next_action="Scientific processing is running; inspect retained products here.",
        )
    family_count = effective_family_count(config, family_count)
    variants_per_family = effective_variants_per_family(config, variants_per_family)
    # subscription_only_demo resolves the executor + inputs to the deterministic demo assets
    # (public_optional) so `maieusis run` completes config-reachably with ZERO paid calls / spawns —
    # an explicit mock + FakePlannerHost demonstration, never a scientific-quality claim.
    try:
        if config.is_demo and config.paperbank.import_from_run is None:
            from ...demo.generation import resolve_demo_run_inputs

            executor, drafts, topic_source_table = resolve_demo_run_inputs(
                config, executor=executor, drafts=drafts, topic_source_table=topic_source_table
            )

        executor = executor or StageExecutor(config)
        # When THIS function resolves the papers (paid ingestion), the paper-half receipt must record the
        # RAW inbox-PDF digests (not the extracted drafts) so a resume can recompute them WITHOUT
        # re-paying extraction. Injected drafts keep the default per-draft digests.
        paper_input_digests: dict[str, str] | None
        resolved_drafts: list[PaperCaseDraft]
        if config.paperbank.import_from_run is not None:
            if drafts is not None:
                raise ValueError(
                    "paperbank.import_from_run cannot be combined with injected paper drafts"
                )
            paper_input_digests = compute_paper_half_input_digests(config, None)
            resolved_drafts = []
        else:
            paper_input_digests = (
                compute_paper_half_input_digests(config, None) if drafts is None else None
            )
            resolved_drafts = (
                list(drafts)
                if drafts is not None
                else ingest_paper_drafts(config, executor, run_context=context)
            )
        run_end_to_end(
            config,
            drafts=resolved_drafts,
            executor=executor,
            topic_source_table=topic_source_table,
            topic_r5_source_table=topic_r5_source_table,
            family_count=family_count,
            variants_per_family=variants_per_family,
            paper_input_digests=paper_input_digests,
            run_context=context,
        )
        return context.paths.summary
    except Exception:
        if load_run_manifest(context.paths).run_state not in {
            RunProcessingState.FAILED,
            RunProcessingState.INCOMPLETE,
        }:
            record_run_failure(
                context,
                code="execute_run_exception",
                diagnostic_class=DiagnosticClass.PROGRAMMER_FAULT,
            )
        raise


# --- run entry guards ------------------------------------------------------------------------
def fresh_run_id() -> str:
    """A fresh run id per `maieusis run` (timestamp + short uuid); `maieusis resume` re-enters an existing one."""
    return _envelope_fresh_run_id()


def assert_run_id_available(output_root: Path, run_id: str) -> None:
    """Fail CLEANLY if ``runs/<run_id>/`` already exists non-empty — resume it instead of overwriting."""
    run_root = output_root / run_id
    if run_root.exists() and any(run_root.iterdir()):
        raise ValueError(
            f"run_id {run_id!r} already exists at {run_root} and is non-empty; "
            f"use 'maieusis resume {run_id}' to resume it, or start a fresh run"
        )


def assert_dataset_link_present(config: MaieusisProjectConfig) -> None:
    """Compatibility-named guard: require Source A or readable Source D input.

    Every configured description path is an explicit input. Missing, non-file, or empty entries are
    rejected here instead of being silently omitted by the narrator.
    """
    docs = [Path(path) for path in config.dataset.seed.docs]
    unreadable: list[Path] = []
    for doc in docs:
        try:
            if not doc.is_file() or doc.stat().st_size <= 0:
                unreadable.append(doc)
        except OSError:
            unreadable.append(doc)
    if unreadable:
        rendered = ", ".join(str(path) for path in unreadable)
        raise ValueError(f"dataset description docs are missing, unreadable, or empty: {rendered}")
    if not config.dataset.seed.link.strip() and not docs:
        raise ValueError(
            "dataset seed requires a link or at least one readable non-empty description doc"
        )


def any_mock_reviewer(receipts: Sequence[PromotionReceipt]) -> bool:
    """F1 signal: True if any captured receipt shows a MOCK reviewer (⇒ downgrade to dev-surrogate)."""
    return any(r.reviewer_execution_kind == ReviewerExecutionKind.MOCK for r in receipts)
