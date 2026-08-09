"""Front-half gate → persist adapters.

The 5a automated gates return in-memory results; this module persists their review-stamped artifacts to
the exact corpus paths the next stage loads, so the automated front half chains with NO human import.

The load-bearing seam is the SHORTLIST synthesis (DP#1): ``run_automated_family_shortlist`` returns
per-family ``FamilyShortlistOutcome`` (honest labels) + an ``AI_REVIEWED`` reviewed family; here that is
turned into a VALID ``QuestionFamilyShortlistManifest`` (a SHORTLISTED ``QuestionFamilyReviewDecision``
whose ACTIVE variant set exactly equals the shortlist's active_variant_ids, with ``scientific_value_notes``
populated) — AI authority, never a faked human decision.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ...io import dump_data
from ...schemas.front_half_authority import FrontHalfAuthorityCeiling
from ...schemas.question_family import (
    QuestionFamily,
    QuestionFamilyReviewDecision,
    QuestionFamilyReviewStatus,
    QuestionFamilyShortlistManifest,
    QuestionFamilyVariantReviewDecision,
    QuestionFamilyVariantReviewStatus,
    ShortlistedQuestionFamily,
)
from ...schemas.scientific_context import TopicEvidenceBrief
from ...schemas.shortlist_outcome import (
    FamilyInclusionLabel,
    FamilyShortlistOutcome,
    VariantShortlistDisposition,
)
from ..agents.question_scientist_family import write_question_family_shortlist
from ..context.topic_evidence import R5TopicEvidenceSourceTable

# Variant dispositions that remain in the shortlist (FLAGGED_DIRECT_RECAP is kept-but-flagged — G-A).
_ACTIVE_DISPOSITIONS = frozenset(
    {VariantShortlistDisposition.ACTIVE, VariantShortlistDisposition.FLAGGED_DIRECT_RECAP}
)

ShortlistResult = tuple[FamilyShortlistOutcome, QuestionFamily | None]


def _shortlisted_family(
    outcome: FamilyShortlistOutcome, reviewed_family: QuestionFamily, *, batch_id: str
) -> ShortlistedQuestionFamily:
    active_vos = [vo for vo in outcome.variant_outcomes if vo.disposition in _ACTIVE_DISPOSITIONS]
    active_ids = [vo.variant_id for vo in active_vos]
    seed_by_variant = {v.variant_id: v.question_seed_id for v in reviewed_family.variants}
    variant_decisions = [
        QuestionFamilyVariantReviewDecision(
            variant_id=vo.variant_id,
            question_seed_id=seed_by_variant[vo.variant_id],
            status=QuestionFamilyVariantReviewStatus.ACTIVE,
            notes=(
                vo.rationale.strip()
                or f"Kept active by the automated shortlist (novelty: {vo.novelty_status.value})."
            ),
        )
        for vo in active_vos
    ]
    notes = outcome.rationale.strip() or "Included by the automated shortlist-worthiness gate."
    review = QuestionFamilyReviewDecision(
        review_item_id=f"auto-review-{outcome.question_family_id}",
        question_family_id=outcome.question_family_id,
        status=QuestionFamilyReviewStatus.SHORTLISTED,
        reviewer="ai:automated-shortlist",  # AI authority — never a human reviewer
        notes=notes,
        scientific_value_notes=notes,  # F4: SHORTLISTED decisions require scientific_value_notes
        variant_decisions=variant_decisions,
    )
    return ShortlistedQuestionFamily(
        family=reviewed_family,
        review=review,
        active_variant_ids=active_ids,
        source_batch_id=batch_id,
        novelty_admission_id=outcome.novelty_admission_id,
        novelty_assessment_ids={
            item.variant_id: item.novelty_assessment_id
            for item in active_vos
            if item.novelty_assessment_id
        },
    )


def build_shortlist_manifest(
    results: Sequence[ShortlistResult],
    *,
    batch_id: str,
    context_id: str,
    context_digest: str,
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED,
) -> QuestionFamilyShortlistManifest:
    """Synthesize a valid shortlist manifest from the automated per-family outcomes (DP#1)."""
    shortlisted: list[ShortlistedQuestionFamily] = []
    rejected: list[str] = []
    needs_revision: list[str] = []
    deferred: list[str] = []
    run_incomplete: list[str] = []
    for outcome, reviewed_family in results:
        label = outcome.label
        if label == FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW:
            if reviewed_family is None:
                raise ValueError(
                    f"included family {outcome.question_family_id} has no AI_REVIEWED family"
                )
            shortlisted.append(_shortlisted_family(outcome, reviewed_family, batch_id=batch_id))
        elif label == FamilyInclusionLabel.REJECTED_SCIENTIFIC:
            rejected.append(outcome.question_family_id)
        elif label == FamilyInclusionLabel.DEFERRED_MATERIAL_REVISION:
            needs_revision.append(outcome.question_family_id)
        elif label == FamilyInclusionLabel.RUN_INCOMPLETE:
            # Its own bucket since 2026-07-31. It used to share `deferred`, and the axis map turned
            # the shared bucket into DEFERRED_INSUFFICIENT_EVIDENCE — so an API failure reached the
            # reader as "not enough usable evidence", the exact mislabelling that put 97% of
            # non-scientific losses behind a scientific sentence.
            run_incomplete.append(outcome.question_family_id)
        else:
            deferred.append(outcome.question_family_id)
    return QuestionFamilyShortlistManifest(
        shortlist_id=f"automated-shortlist-{batch_id}",
        pack_id=f"automated-pack-{batch_id}",
        context_id=context_id,
        context_digest=context_digest,
        shortlisted=shortlisted,
        rejected_family_ids=rejected,
        needs_revision_family_ids=needs_revision,
        deferred_family_ids=deferred,
        run_incomplete_family_ids=run_incomplete,
        authority_ceiling=authority_ceiling,
        # Phase 6-P sends both authority modes through the same planner route. The authority
        # ceiling is carried separately and must never be inferred from route eligibility.
        planning_eligible=True,
    )


def persist_shortlist_manifest(
    manifest: QuestionFamilyShortlistManifest, *, corpus_root: str | Path = "corpus"
) -> Path:
    """Write the manifest to corpus/question_families/reviewed/ (the path the orchestrator loads)."""
    return write_question_family_shortlist(manifest, corpus_root=corpus_root)


def persist_reviewed_topic_evidence(
    brief: TopicEvidenceBrief,
    source_table: R5TopicEvidenceSourceTable,
    *,
    corpus_root: str | Path = "corpus",
) -> tuple[Path, Path]:
    """Co-write the reviewed topic brief + its source table to the exact stage-C topic-evidence paths.

    The V2 context builder loads BOTH the reviewed ``TopicEvidenceBrief`` and the
    ``R5TopicEvidenceSourceTable`` (product code splits their writers across two functions); landing
    them together here means stage C never fails on a present-brief-but-missing-source-table. The brief
    must already carry an accepted authority (the driver promotes it through the topic-evidence gate).
    """
    root = Path(corpus_root) / "context" / "topic_evidence"
    brief_path = dump_data(brief, root / "research_intent.topic_evidence_brief.yaml")
    source_path = dump_data(
        source_table, root / "sources" / "research_intent.topic_source_table.yaml"
    )
    return brief_path, source_path
