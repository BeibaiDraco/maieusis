"""Promote + persist the narrator's fused narrative under AUTOMATED authority.

The narrator is specified for four coarse sources and wired for two of them (A documentation and D
user docs); see the `fusion` module docstring for what v0.1 actually feeds it.

Closes the gap where ``gather_and_fuse_dataset_narrative`` returned in-memory and the CLI only printed
it, so the Questioner context still read the legacy A-only reviewed narrative. Here the fused
``DatasetNarrative`` becomes the reviewed-narrative artifact the V2 context builder consumes
(``corpus/context/dataset_narratives/{dataset_id}.dataset_narrative.yaml``), with its verdict set by
the ALREADY-EXISTING independent-AI fidelity gate — the automated-default authority (see 4 model),
NOT a human import.

The status is *earned, not stamped*: ``promote_narrator_result_to_reviewed`` fails closed unless a
real fidelity review ran, returned ACCEPT, is provenance-bearing, and used a provider independent of
every generator. A missing review, a REJECT verdict, a REVISE that names something, or an
un-provenanced narrative all leave the narrative unpromoted → the V2 gate then refuses it (DRAFT is
not proposal-ready). The GF-2c adversarial fixture (a plausible-but-false narrative) drives REJECT
and fails closed through here.

The one deliberate exception is a REVISE that names NOTHING -- no required change, no unfaithful
claim, no over-precise finding, no hallucination, no failed criterion. Such a verdict used to be
run-fatal while carrying no actionable content; it is now promoted with an explicit warning in
``review_notes``. See ``_revise_that_names_nothing`` and ``revise_is_survivable``.

A revise that names something is a different case, and since 2026-08-12 it does not arrive here
first: ``narrative_revision.run_narrative_fidelity_repair_loop`` re-asks the narrator model for a
source-locked repair and returns it to the same independent gate, bounded by
``config.run.max_revise_rounds``. This module sees only what that loop finally produced, and its
answer to it is unchanged -- accept, or the survivable-revise exception, or fail closed.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ...io import dump_data
from ...provenance import stable_hash
from ...schemas.dataset_narrative import DatasetNarrative, DatasetNarrativeReviewStatus
from ..agents.dataset_narrative_reviewer import DatasetNarrativeFidelityDecision
from ..agents.promotion import assert_promoted_status_is_holdable
from ..agents.reviewer_base import assert_reviewer_provider_independent
from .fusion import source_locator
from .narrator import NarratorResult


class NarrativeFidelityNonAccept(ValueError):
    """The independent fidelity gate itself judged the narrative and did not accept it.

    The ONLY refusal in this module that is a statement about the SCIENCE. Every other refusal below
    is the host declining to grant authority because a piece of machinery is missing or inconsistent
    -- no review ran at all, the criterion sweep never finished, the reviewer shares a provider family
    with a generator, there is no generator identity to attest, the fused candidate carries no
    source_refs, or the stamped artifact cannot hold the status. In each of those the science was
    never judged, so recording them as a scientific verdict is the misfiling
    ``schemas/stage_receipt.py:22`` exists to forbid -- and it is not a cosmetic one:
    ``docs/public/SHEPHERD_MODE.md`` rule 3 forbids repairing past a scientific verdict and
    ``resume.py:233`` REUSES a scientific terminal instead of re-running it, so a host bug filed
    scientific is unrescuable by design.

    The caller therefore classifies on this TYPE, not on the review's decision word. Inferring it from
    the decision was wrong in both directions: a missing review defaulted to ``reject`` and read as a
    verdict nobody delivered, and a structural refusal that happened to follow a survivable ``revise``
    inherited that word and read as one too.
    """


def _revise_that_names_nothing(review: object) -> bool:
    """A `revise` verdict carrying no finding of any kind, and no failed criterion.

    CORRECTED 2026-08-03 against the raw capture of the call this docstring was written about.
    It said the reviewer "returned `revise` with every finding list empty". It did not. The capture
    (capture/ibl-rc2/scientific_agents.anthropic.session_send/0001-response.json) shows the model
    returned **accept**, all three criteria passing, every finding list empty, and a single
    `required_changes` item: "Consider reformatting the temporal_structure field ... for readability
    (not a fidelity blocker)". The HOST turned that into `revise`, because `accept_blocked` counted
    any non-empty `required_changes`. So this predicate could never fire on the leg it was built
    for -- it requires `decision == REVISE` and an empty `required_changes`, and neither held.
    The original reading came from the PERSISTED diagnostic, where `required_changes: []` is a
    schema default rather than an observation: evidence-discipline rule 10, committed by the fix.

    That downgrade is gone (see `dataset_narrative_reviewer.accept_blocked`), so the shape this
    predicate covers is now only what it literally says: a model-emitted `revise` naming nothing.
    Measured across every fidelity call in the capture archive, that shape has occurred **0 of 19**
    times. It is kept because it costs nothing and a reviewer may yet emit it, not because it has
    ever caught anything.

    When this was written there was no narrative revise loop anywhere in the project: `REVISE` had
    exactly one consumer, the fail-closed raise below, so it was operationally identical to
    `REJECT`. A reviewer wanting to say "accept, with a nit" had no word for it, and a reviewer
    naming a real but fixable defect had no repairer -- the second half of that is what
    `narrative_revision.py` now answers. Same shape as the plan reviewer's
    `missing_required_changes` (PR #107), one gate earlier and run-fatal instead of family-fatal.

    Deliberately narrow. `REJECT` stays fatal always; a `revise` that names ANY required change,
    unfaithful claim, over-precise finding, hallucination, or failed criterion stays fatal, because
    then the reviewer has identified something and the host must not overrule it. The gate's actual
    job -- unsupported claims, over-precision, trust mishandling -- is untouched.
    """

    if getattr(review, "decision", None) != DatasetNarrativeFidelityDecision.REVISE:
        return False
    named = (
        list(getattr(review, "required_changes", []) or [])
        + list(getattr(review, "unfaithful_claims", []) or [])
        + list(getattr(review, "too_precise_findings", []) or [])
        + list(getattr(review, "hallucination_findings", []) or [])
    )
    if named:
        return False
    if not getattr(review, "criterion_review_complete", False):
        return False
    assessments = list(getattr(review, "criterion_assessments", []) or [])
    # A criterion the reviewer marked failed IS a finding, whatever the lists say; and an empty
    # assessment list is not a clean bill of health, so it stays fatal too.
    return bool(assessments) and all(getattr(item, "passed", False) for item in assessments)


def revise_is_survivable(review: object) -> bool:
    """A ``revise`` the run may carry at draft authority instead of dying on.

    ``_revise_that_names_nothing`` requires an entirely empty finding set. Measured, that shape has
    occurred 0 of 19 times in the capture archive and 0 of 2 in the 2026-08-12 live legs, so in
    practice this gate had no survivable revise at all -- and when N2 was written it was the only
    front-half gate with no revise loop and no drafter to receive a repair. ``required_changes``
    therefore arrived at a gate structurally incapable of acting on it, and the run died over a
    repair nobody could make. (That is fixed: ``narrative_revision.py`` now repairs a revise that
    names something. This predicate keeps its job of deciding what may promote WITHOUT a repair, so
    that the loop never spends a model call on a verdict already survivable.)

    What killed two of five live legs on 2026-08-12 was a HOST field-map defect (fixed in N1): both
    reviewers passed every criterion, named zero unfaithful claims and zero hallucinations, and
    wrote a required change describing the mislabelling.
    ``prompts/dataset_narrative_fidelity_reviewer/v2.md`` tells the model to "return `revise`
    (fixable)" -- the word it is TOLD to use for something repairable.

    So a ``revise`` survives when the reviewer's own fidelity findings are empty and every criterion
    it assessed passed. What is genuinely a fidelity failure stays fatal: ``REJECT`` always, any
    unfaithful claim, any hallucination finding, any failed or unassessed criterion. Only
    ``required_changes`` and ``too_precise_findings`` -- a suggestion and a wording judgement, which
    AGENTS.md rule 11 keeps soft -- become a cap rather than a kill.
    """

    if getattr(review, "decision", None) != DatasetNarrativeFidelityDecision.REVISE:
        return False
    fidelity_findings = list(getattr(review, "unfaithful_claims", []) or []) + list(
        getattr(review, "hallucination_findings", []) or []
    )
    if fidelity_findings:
        return False
    if not getattr(review, "criterion_review_complete", False):
        return False
    assessments = list(getattr(review, "criterion_assessments", []) or [])
    return bool(assessments) and all(getattr(item, "passed", False) for item in assessments)


def promote_narrator_result_to_reviewed(result: NarratorResult) -> DatasetNarrative:
    """Earn ``AUTOMATED_REVIEWED`` from an accepted fidelity review, or raise (fail closed).

    Refuses to promote unless ALL hold: a review ran; its decision is ACCEPT, or a REVISE that
    names nothing at all (see ``_revise_that_names_nothing``); it carries real provenance; its
    provider is independent of every generator; and the fused candidate has source_refs. Exactly one
    of those refusals is a scientific verdict and it raises ``NarrativeFidelityNonAccept``; every
    other refusal raises a plain ``ValueError`` and means the machinery, not the science, is at
    fault. On success
    it returns a copy stamped with the automated verdict + the fused narrative's own provenance
    (fusion prompt marker, joined generator providers, source/input digests) plus a durable audit
    link to the review, and an explicit warning in ``review_notes`` when the verdict was not accept.
    """
    review = result.review
    if review is None:
        raise ValueError(
            "cannot promote DatasetNarrative: no independent fidelity review was run "
            "(the narrative gate has no automated authority to grant — fail closed)"
        )
    # N2 (2026-08-12): a `revise` whose criteria all passed and whose fidelity findings are empty
    # is carried at draft authority rather than ending the run. `_revise_that_names_nothing` stays
    # as the stricter historical shape; `revise_is_survivable` is the one that can actually fire.
    names_nothing = _revise_that_names_nothing(review)
    empty_revise = names_nothing or revise_is_survivable(review)
    if review.decision != DatasetNarrativeFidelityDecision.ACCEPT and not empty_revise:
        raise NarrativeFidelityNonAccept(
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
    if review.decision == DatasetNarrativeFidelityDecision.ACCEPT and review.required_changes:
        # An accept that carries suggestions is still an accept -- but the suggestions were paid
        # for and are the reviewer's own reading, so they travel with the artifact rather than
        # being dropped on the floor. Disclosure is what makes it safe to stop treating them as
        # fatal.
        narrative.review_notes += (
            " The gate accepted while suggesting "
            f"{len(review.required_changes)} non-blocking improvement(s); they are recorded on the "
            "persisted fidelity review in the reviewer's own wording and did not gate promotion."
        )
    if names_nothing:
        # Never a silent downgrade: the reader is told the verdict was not accept and that the
        # reviewer named nothing to repair, so they can judge the narrative themselves.
        narrative.review_notes += (
            " The gate returned revise while naming no required change, unfaithful claim, "
            "over-precise finding, hallucination, or failed criterion, so the narrative was "
            "promoted with this warning rather than ending the run; see the persisted fidelity "
            "review for the reviewer's own wording."
        )
    elif empty_revise:
        # The OTHER survivable shape, and it must not borrow the sentence above. N2 widened the
        # predicate to `revise_is_survivable`, which promotes a revise that DID name required
        # changes or over-precise findings as long as every criterion passed and no unfaithful
        # claim or hallucination was found -- exactly the two live legs it was written for. The
        # single note left behind then went on saying the reviewer named nothing, on artifacts
        # whose own persisted review lists what it named. That is an invented fact in a provenance
        # field, so each branch states only what actually happened.
        narrative.review_notes += (
            f" The gate returned revise while passing all {len(review.criterion_assessments)} "
            "criteria it assessed and naming no unfaithful claim and no hallucination; its "
            f"{len(review.required_changes)} required change(s) and "
            f"{len(review.too_precise_findings)} over-precise finding(s) are recorded on the "
            "persisted fidelity review in the reviewer's own wording, and the narrative was "
            "promoted with this warning rather than ending the run."
        )
    assert_promoted_status_is_holdable(narrative, expected_gate="dataset_narrative_fidelity")
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
