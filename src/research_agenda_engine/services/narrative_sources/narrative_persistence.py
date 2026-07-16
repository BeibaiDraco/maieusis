"""Promote + persist the four-source narrator's fused narrative under AUTOMATED authority.

Closes the gap where ``gather_and_fuse_dataset_narrative`` returned in-memory and the CLI only printed
it, so the Questioner context still read the legacy A-only reviewed narrative. Here the fused
``DatasetNarrative`` becomes the reviewed-narrative artifact the V2 context builder consumes
(``corpus/context/dataset_narratives/{dataset_id}.dataset_narrative.yaml``), with its verdict set by
the ALREADY-EXISTING independent-AI fidelity gate — the automated-default authority (see 4 model),
NOT a human import.

The status is *earned, not stamped*: ``promote_narrator_result_to_reviewed`` fails closed unless a
real fidelity review ran, returned ACCEPT, is provenance-bearing, and used a provider independent of
every generator. A missing review, a REVISE/REJECT verdict, or an un-provenanced narrative all leave
the narrative unpromoted → the V2 gate then refuses it (DRAFT is not proposal-ready). The GF-2c
adversarial fixture (a plausible-but-false narrative) drives REJECT and fails closed through here.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ...io import dump_data
from ...provenance import stable_hash
from ...schemas.dataset_narrative import DatasetNarrative, DatasetNarrativeReviewStatus
from ..agents.dataset_narrative_reviewer import DatasetNarrativeFidelityDecision
from ..agents.reviewer_base import assert_reviewer_provider_independent
from .fusion import source_locator
from .narrator import NarratorResult


def promote_narrator_result_to_reviewed(result: NarratorResult) -> DatasetNarrative:
    """Earn ``AUTOMATED_REVIEWED`` from an accepted fidelity review, or raise (fail closed).

    Refuses to promote unless ALL hold: a review ran, its decision is ACCEPT, it carries real
    provenance, its provider is independent of every generator, and the fused candidate has
    source_refs. On success it returns a copy stamped with the automated verdict + the fused
    narrative's own provenance (fusion prompt marker, joined generator providers, source/input
    digests) plus a durable audit link to the review.
    """
    review = result.review
    if review is None:
        raise ValueError(
            "cannot promote DatasetNarrative: no independent fidelity review was run "
            "(the narrative gate has no automated authority to grant — fail closed)"
        )
    if review.decision != DatasetNarrativeFidelityDecision.ACCEPT:
        raise ValueError(
            "cannot promote DatasetNarrative: independent fidelity gate returned "
            f"{review.decision.value!r}, not accept — fail closed"
        )
    if not review.criterion_review_complete:
        raise ValueError(
            "cannot promote DatasetNarrative: criterion review is incomplete — fail closed"
        )
    # Defensive re-assert: the review was already built with this check, but promotion is the
    # trust boundary that grants proposal authority, so it must not depend on an upstream invariant.
    assert_reviewer_provider_independent(
        review.provider_id,
        review.generator_provider_ids,
        role_label="narrative fidelity reviewer",
    )
    generator_provider_id = "+".join(review.generator_provider_ids)
    if not generator_provider_id:
        raise ValueError(
            "cannot promote DatasetNarrative: no generator provider identity to attest — fail closed"
        )
    candidate = result.candidate
    if not candidate.source_refs:
        raise ValueError(
            "cannot promote DatasetNarrative: fused candidate has no source_refs — fail closed"
        )

    narrative = candidate.model_copy(deep=True)
    narrative.review_status = DatasetNarrativeReviewStatus.AUTOMATED_REVIEWED
    narrative.dataset_narrative_id = f"dataset-narrative-{narrative.dataset_id}-automated-reviewed"
    # Fusion is deterministic and has no LLM prompt; candidate.prompt_version already carries the
    # non-prompt fusion marker (dataset_narrative_fusion/v1). Keep it; the review authority is
    # recorded separately below (dossier_digest + review_notes) for a durable audit link.
    narrative.provider_id = generator_provider_id
    narrative.source_packet_digest = stable_hash(
        {source_locator(facts): facts.model_dump(mode="json") for facts in result.sources.values()}
    )
    narrative.input_digest = review.input_digest
    narrative.dossier_digest = review.output_digest
    narrative.reviewed_at = datetime.now(UTC)
    # Not a human review — leave expert_reviewer empty and record the automated authority in the notes.
    narrative.expert_reviewer = ""
    narrative.review_notes = (
        f"Automated independent-AI fidelity gate {review.prompt_version} "
        f"(provider {review.provider_id}, model {review.model_id}, session {review.session_id}) "
        f"returned {review.decision.value}; reviewer independent of generators "
        f"{review.generator_provider_ids}."
    )
    return narrative


def reviewed_dataset_narrative_path(dataset_id: str, *, corpus_root: str | Path = "corpus") -> Path:
    """The singleton reviewed-narrative artifact path the V2 context builder reads."""
    return (
        Path(corpus_root)
        / "context"
        / "dataset_narratives"
        / f"{dataset_id}.dataset_narrative.yaml"
    )


def persist_reviewed_narrator_result(
    result: NarratorResult,
    *,
    corpus_root: str | Path = "corpus",
) -> Path:
    """Promote (fail-closed) then write the reviewed narrative to the singleton context path."""
    narrative = promote_narrator_result_to_reviewed(result)
    return dump_data(
        narrative, reviewed_dataset_narrative_path(narrative.dataset_id, corpus_root=corpus_root)
    )
