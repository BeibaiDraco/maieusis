"""Bounded, source-locked repair of an independently reviewed ``DatasetNarrative``.

The dataset-narrative fidelity gate was the only front-half gate with no revise loop:
``dataset_narrative_reviewer.py`` said so outright, and a ``revise`` naming a failed criterion ended
the run at ``promote_narrator_result_to_reviewed`` before any research question existed. Measured
across twenty live legs on 2026-08-12, three died there, all on ``failed_criteria: ['faithful']``.

The standing objection was that the narrative is fused deterministically (``fusion.py``), so no
generator exists to receive a repair. That reasoning is incomplete. Fusion is deterministic but the
CONTENT it fuses is model-written: the field that killed leg 23,
``spatial_or_anatomical_coverage``, comes from ``DatasetNarrativeModelOutput`` through
``source_a_documentation._map_to_coarse`` and lands unchanged on the narrative through
``fusion._SCALAR_FIELDS``. A model wrote the sentence, so a model can rewrite it.

The shape is the topic-evidence precedent (``context/topic_evidence_revision.py``): the reviewer's
own finding travels to a source-locked reviser, the redraft is persisted before anything else can
fail, and it goes back to the SAME independent gate. Nothing here promotes anything; promotion
still requires the gate to accept.

Two host locks make the repair safe, and both are refusals rather than silent sanitizations:

* **Evidence is host-owned.** ``scale_facts``, ``source_refs`` and ``field_evidence_source_ids`` are
  not in the reviser's output model at all — they are carried across from the reviewed candidate.
  A repair may reword the narrative; it may never alter what the narrative is evidenced by.
* **A disclaimer may not be laundered.** Leg 23's contradiction had two resolutions: soften the
  coverage claim, or delete the limitation that exposed it. The second satisfies the reviewer and
  looks identical to success from the outside. So every entry of ``known_high_level_limitations``
  present before a repair must survive it; new entries are welcome.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...assets import resolve_asset
from ...io import dump_data
from ...provenance import sha256_file, stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas.coarse_dataset_facts import CoarseDatasetFacts
from ...schemas.dataset_narrative import DatasetNarrative
from ..agents.dataset_narrative_reviewer import (
    DatasetNarrativeFidelityDecision,
    DatasetNarrativeFidelityReview,
)
from .fusion import SourceKind, source_locator
from .narrative_persistence import revise_is_survivable
from .narrator import NarratorResult

DATASET_NARRATIVE_REVISER_PROMPT_VERSION = "dataset_narrative_reviser/v1"

#: Trust rank per source kind, mirrored from the reviewer so the reviser reads the same ordering.
_TRUST_RANK: dict[SourceKind, int] = {
    SourceKind.USER_DESCRIPTION: 0,
    SourceKind.DOCUMENTATION: 1,
    SourceKind.LOCAL_SAMPLE: 2,
    SourceKind.MODEL_RESEARCH: 3,
}

#: The narrative fields a repair may rewrite. Everything absent from this tuple is carried verbatim
#: from the reviewed candidate, because it is either evidence or host-owned identity/provenance.
REVISABLE_NARRATIVE_FIELDS: tuple[str, ...] = (
    "title",
    "scientific_purpose",
    "population",
    "task_or_design",
    "broad_scale",
    "spatial_or_anatomical_coverage",
    "temporal_structure",
    "standardization",
    "modalities",
    "hierarchical_structure",
    "broad_interventions",
    "major_variables",
    "reuse_opportunities",
    "known_high_level_limitations",
)

#: What a repair must never move. The first three are the narrative's evidence; the rest are the
#: identity and authority the host alone may stamp.
EVIDENCE_LOCKED_NARRATIVE_FIELDS: tuple[str, ...] = (
    "scale_facts",
    "source_refs",
    "field_evidence_source_ids",
    "dataset_narrative_id",
    "dataset_id",
    "review_status",
    "prompt_version",
    "provider_id",
    "model_id",
    "input_digest",
    "source_packet_digest",
    "dossier_digest",
    "reviewed_at",
    "expert_reviewer",
    "review_notes",
)


class NarrativeRevisionError(ValueError):
    """A narrative repair crossed its evidence, disclaimer, or proposal boundary."""


class NarrativeDisclaimerLaunderingError(NarrativeRevisionError):
    """The repair answered the reviewer by deleting a limitation instead of softening a claim.

    The single most dangerous outcome this loop can produce, because it is indistinguishable from a
    real repair at the gate: the reviewer's finding was a CONTRADICTION between a confident claim and
    the narrative's own ``known_high_level_limitations``, and dropping either side resolves it. One
    of those two is honest.
    """


class _DatasetNarrativeRevisionOutput(BaseModel):
    """What the reviser model returns — the revisable prose only.

    Deliberately does NOT declare ``scale_facts``, ``source_refs`` or ``field_evidence_source_ids``.
    That absence is the evidence lock: there is no field for the model to put invented evidence in,
    so the lock cannot be forgotten at a call site the way a post-hoc comparison can.
    """

    model_config = ConfigDict(extra="forbid")

    title: str
    scientific_purpose: str
    population: str
    task_or_design: str
    broad_scale: str = ""
    spatial_or_anatomical_coverage: str = ""
    temporal_structure: str = ""
    standardization: str = ""
    modalities: list[str] = Field(default_factory=list)
    hierarchical_structure: list[str] = Field(default_factory=list)
    broad_interventions: list[str] = Field(default_factory=list)
    major_variables: list[str] = Field(default_factory=list)
    reuse_opportunities: list[str] = Field(default_factory=list)
    known_high_level_limitations: list[str] = Field(default_factory=list)
    change_notes: list[str] = Field(default_factory=list)


class DatasetNarrativeRevisionRound(BaseModel):
    """Typed provenance for one source-locked redraft between two independent fidelity reviews."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    round_index: int = Field(ge=1)
    prompt_version: str = DATASET_NARRATIVE_REVISER_PROMPT_VERSION
    candidate_digest_before: str
    reviewer_review: DatasetNarrativeFidelityReview
    revision_input_digest: str
    generator_provider_id: str
    generator_model_id: str
    revised_candidate_digest: str
    revised_candidate_path: str
    revised_candidate_sha256: str
    changed_fields: list[str] = Field(default_factory=list)
    change_notes: list[str] = Field(default_factory=list)
    limitations_before: int = 0
    limitations_after: int = 0


class DatasetNarrativeRevisionHistory(BaseModel):
    """The complete bounded repair/re-review disposition for one dataset narrative."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    rounds: list[DatasetNarrativeRevisionRound] = Field(default_factory=list)
    final_decision: DatasetNarrativeFidelityDecision
    final_rationale: str = ""
    budget_exhausted: bool = False
    repair_refused: str = ""


def _normalized(value: str) -> str:
    """Whitespace-folded, case-folded text — the mechanical normalization AGENTS.md rule 11 allows."""
    return " ".join(str(value).split()).casefold()


def assert_limitations_not_laundered(before: Sequence[str], after: Sequence[str]) -> None:
    """Refuse a repair that removed a stated limitation. THE honesty guard for this loop.

    Verbatim survival (modulo whitespace and case) rather than a similarity judgement, because the
    thing being protected is not phrasing: it is whether a disclaimer the reader was given still
    exists. A reviser is told plainly to copy the list through and edit the claim instead, so the
    only revision this rejects is one that did the other thing.

    Additions pass. A repair that discovers a further honest limit while softening a claim is doing
    exactly what it should.
    """

    kept = {_normalized(item) for item in after}
    dropped = [str(item) for item in before if _normalized(item) not in kept]
    if dropped:
        raise NarrativeDisclaimerLaunderingError(
            "narrative repair dropped "
            f"{len(dropped)} stated limitation(s) instead of softening the claim they contradict: "
            + " | ".join(dropped)
        )


def assert_revision_preserved_evidence(
    candidate: DatasetNarrative, revised: DatasetNarrative
) -> None:
    """Refuse a repair whose evidence or host-owned identity differs from the reviewed candidate.

    Redundant with the reviser's output model today, which declares none of these fields. Kept as a
    defensive re-assert at the trust boundary, exactly as ``promote_narrator_result_to_reviewed``
    re-asserts reviewer independence: a later widening of the output model, or a second caller that
    builds the revised narrative some other way, must not be able to move evidence silently.
    """

    moved = [
        name
        for name in EVIDENCE_LOCKED_NARRATIVE_FIELDS
        if getattr(revised, name) != getattr(candidate, name)
    ]
    if moved:
        raise NarrativeRevisionError(
            "narrative repair changed host-owned evidence or identity fields: " + ", ".join(moved)
        )


def is_repairable_revise(review: DatasetNarrativeFidelityReview | None) -> bool:
    """A verdict this loop should spend a model call on.

    ``reject`` is the reviewer's own word for a narrative that is fundamentally unfaithful or
    uncoarsenable (``prompts/dataset_narrative_fidelity_reviewer/v2.md``), so it is never repaired.
    A ``revise`` that is already survivable under N2 needs no repair either -- it promotes with a
    warning -- and paying for a redraft of it would be worse than the defect this loop fixes.
    Everything else the reviewer called ``revise`` is, by that prompt's own definition, fixable.
    """

    if review is None or review.decision != DatasetNarrativeFidelityDecision.REVISE:
        return False
    return not revise_is_survivable(review)


def narrative_repair_review_guidance(
    *, round_index: int, previous: DatasetNarrativeFidelityReview
) -> str:
    """What the re-review is told about the repair it is judging.

    Carries the previous reviewer's own findings back to it, and — the part that matters — states
    the host lock, so the gate does not reward a candidate that resolved a contradiction by
    deleting the disclaimer. It could not have: the host would have refused it.
    """

    named = [
        *(f"required change: {item}" for item in previous.required_changes),
        *(f"unfaithful claim: {item}" for item in previous.unfaithful_claims),
        *(f"too precise: {item}" for item in previous.too_precise_findings),
        *(f"hallucination: {item}" for item in previous.hallucination_findings),
        *(
            f"failed criterion: {item.criterion}"
            for item in previous.criterion_assessments
            if not item.passed
        ),
    ]
    findings = "; ".join(named) if named else "no itemized finding beyond the rationale"
    return (
        f"This candidate is round {round_index} of a bounded source-locked repair. The previous "
        f"independent review returned {previous.decision.value} and named: {findings}. Its "
        f"rationale was: {previous.rationale} Judge the revised candidate on its own merits against "
        "the sources, and say whether those findings are now resolved. The repair could only "
        "rewrite narrative prose: scale facts, source refs and field-level evidence were carried "
        "over by the host unchanged, and every previously stated limitation was required to survive "
        "verbatim, so a contradiction cannot have been resolved by deleting a disclaimer."
    )


def _load_reviser_prompt(prompt_path: Path | None = None) -> str:
    path = prompt_path or resolve_asset(
        Path("prompts") / Path(DATASET_NARRATIVE_REVISER_PROMPT_VERSION).with_suffix(".md")
    )
    return path.read_text(encoding="utf-8")


def _realigned_item_sources(
    candidate: DatasetNarrative, updates: Mapping[str, object]
) -> dict[str, list[list[str]]]:
    """Carry per-item provenance across a repair that may reorder, drop or add list entries.

    The reviser is allowed to add a limitation and to reword one, so an index-aligned map built
    before the repair does not describe the list after it. A surviving sentence keeps the source
    that authored it, matched on its own text; a sentence the reviser introduced carries the
    field-level list, because the reviser writes only from the sources it was shown. Dropping the
    map instead would be worse: it would silently restore the field-level stamp that made a card
    look jointly asserted by sources that never said it.
    """

    realigned: dict[str, list[list[str]]] = {}
    for name, per_item in candidate.list_item_source_ids.items():
        before = getattr(candidate, name, None)
        after = updates.get(name, before)
        if not isinstance(before, list) or not isinstance(after, list):
            continue
        known = {
            str(text).strip().lower(): list(sources)
            for text, sources in zip(before, per_item, strict=False)
        }
        field_level = list(candidate.field_evidence_source_ids.get(name, []))
        realigned[name] = [known.get(str(item).strip().lower(), field_level) for item in after]
    return realigned


def revise_dataset_narrative(
    provider: StructuredModelProvider,
    *,
    candidate: DatasetNarrative,
    sources: Mapping[SourceKind, CoarseDatasetFacts],
    review: DatasetNarrativeFidelityReview,
    round_index: int,
    revision_output_path: Path,
    revision_output_reference: str,
    prompt_path: Path | None = None,
    max_prompt_chars: int = 250_000,
) -> tuple[DatasetNarrative, DatasetNarrativeRevisionRound]:
    """One source-locked repair of a reviewed narrative, persisted before it is re-reviewed."""

    if not is_repairable_revise(review):
        raise NarrativeRevisionError(
            f"narrative repair requires a repairable revise verdict, got {review.decision.value!r}"
        )
    if not sources:
        raise NarrativeRevisionError("narrative repair requires at least one source")

    payload = {
        "prompt_version": DATASET_NARRATIVE_REVISER_PROMPT_VERSION,
        "round_index": round_index,
        "dataset_id": candidate.dataset_id,
        "candidate_narrative": candidate.model_dump(mode="json"),
        "field_evidence_source_ids": candidate.field_evidence_source_ids,
        "sources": [
            {
                "source_kind": kind.value,
                "source_locator": source_locator(facts),
                "trust_rank": _TRUST_RANK[kind],
                "coarse_facts": facts.model_dump(mode="json"),
            }
            for kind in SourceKind
            if (facts := sources.get(kind)) is not None
        ],
        "review_feedback": {
            "decision": review.decision.value,
            "rationale": review.rationale,
            "criterion_assessments": [
                item.model_dump(mode="json") for item in review.criterion_assessments
            ],
            "criterion_audit": [item.model_dump(mode="json") for item in review.criterion_audit],
            "required_changes": list(review.required_changes),
            "unfaithful_claims": list(review.unfaithful_claims),
            "too_precise_findings": list(review.too_precise_findings),
            "hallucination_findings": list(review.hallucination_findings),
        },
        "host_owned_fields": list(EVIDENCE_LOCKED_NARRATIVE_FIELDS),
        "repair_rules": {
            "limitations_must_survive_verbatim": True,
            "may_add_limitations": True,
            "evidence_is_host_owned": True,
            "claims_must_be_supported_by_a_listed_source": True,
        },
    }
    user_prompt = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if len(user_prompt) > max_prompt_chars:
        raise NarrativeRevisionError("narrative repair packet exceeds prompt budget")
    input_digest = stable_hash(payload)

    generated = provider.generate_structured(
        system_prompt=_load_reviser_prompt(prompt_path),
        user_prompt=user_prompt,
        output_model=_DatasetNarrativeRevisionOutput,
    )

    updates = {name: getattr(generated, name) for name in REVISABLE_NARRATIVE_FIELDS}
    updates["list_item_source_ids"] = _realigned_item_sources(candidate, updates)
    try:
        revised = DatasetNarrative.model_validate(
            {**candidate.model_dump(mode="python"), **updates}
        )
    except ValueError as exc:
        raise NarrativeRevisionError(f"narrative repair failed strict validation: {exc}") from exc

    # Order matters: the laundering check runs on the model's own list, before anything downstream
    # can normalize it into looking compliant.
    assert_limitations_not_laundered(
        candidate.known_high_level_limitations, revised.known_high_level_limitations
    )
    assert_revision_preserved_evidence(candidate, revised)

    changed = [
        name
        for name in REVISABLE_NARRATIVE_FIELDS
        if getattr(revised, name) != getattr(candidate, name)
    ]
    if not changed:
        # A repair that changed nothing would burn the remaining budget re-reviewing the same bytes
        # and end at the same verdict. Refuse it here so the run records why instead of stalling.
        raise NarrativeRevisionError("narrative repair returned the reviewed candidate unchanged")

    dump_data(revised, revision_output_path)
    return revised, DatasetNarrativeRevisionRound(
        dataset_id=candidate.dataset_id,
        round_index=round_index,
        candidate_digest_before=stable_hash(candidate),
        reviewer_review=review,
        revision_input_digest=input_digest,
        generator_provider_id=provider.provider_id,
        generator_model_id=getattr(provider, "model_name", "") or provider.provider_id,
        revised_candidate_digest=stable_hash(revised),
        revised_candidate_path=revision_output_reference,
        revised_candidate_sha256=sha256_file(revision_output_path),
        changed_fields=changed,
        change_notes=list(generated.change_notes),
        limitations_before=len(candidate.known_high_level_limitations),
        limitations_after=len(revised.known_high_level_limitations),
    )


@dataclass
class NarrativeRepairLoopResult:
    """The narrator result the promoter should judge, plus how it got there."""

    result: NarratorResult
    rounds: list[DatasetNarrativeRevisionRound] = field(default_factory=list)
    budget_exhausted: bool = False
    repair_refused: str = ""

    def history(self) -> DatasetNarrativeRevisionHistory:
        review = self.result.review
        return DatasetNarrativeRevisionHistory(
            dataset_id=self.result.candidate.dataset_id,
            rounds=list(self.rounds),
            final_decision=(
                review.decision if review is not None else DatasetNarrativeFidelityDecision.REJECT
            ),
            final_rationale=review.rationale if review is not None else "",
            budget_exhausted=self.budget_exhausted,
            repair_refused=self.repair_refused,
        )


def run_narrative_fidelity_repair_loop(
    *,
    initial: NarratorResult,
    redraft: Callable[
        [DatasetNarrative, DatasetNarrativeFidelityReview, int],
        tuple[DatasetNarrative, DatasetNarrativeRevisionRound],
    ],
    review: Callable[[DatasetNarrative], DatasetNarrativeFidelityReview],
    max_revise_rounds: int,
) -> NarrativeRepairLoopResult:
    """Repair-and-re-review a fused narrative while the gate keeps saying ``revise``, bounded.

    Mirrors ``gate_kernel.run_gate_with_revise_loop``'s contract — bounded rounds, an honest
    ``budget_exhausted`` flag, and no rewriting of the reviewer's final word — but reads the
    narrative gate's own ``DatasetNarrativeFidelityReview`` rather than a ``GateOutcome``, so a
    survivable ``revise`` (N2) can end the loop without being relabelled as an accept it never was.

    A host refusal of a redraft (a laundered disclaimer, moved evidence, a no-op repair) stops the
    loop and is reported in ``repair_refused``. It is never also a budget exhaustion, and that falls
    out of the loop condition rather than being asserted: a refusal can only happen on an iteration
    the guard already let start, so ``len(rounds) < max_revise_rounds`` held when it did. An extra
    ``not refused`` term was written here first and removed -- it could not be made to fail under
    mutation, and AGENTS.md rule 8 says a guard that cannot fail is not a guard.
    """

    if max_revise_rounds < 0:
        raise ValueError("max_revise_rounds must be >= 0")

    current = initial
    rounds: list[DatasetNarrativeRevisionRound] = []
    refused = ""
    while is_repairable_revise(current.review) and len(rounds) < max_revise_rounds:
        assert current.review is not None  # narrowed by is_repairable_revise
        try:
            revised, round_record = redraft(current.candidate, current.review, len(rounds) + 1)
        except NarrativeRevisionError as exc:
            refused = f"{type(exc).__name__}: {exc}"
            break
        rounds.append(round_record)
        current = NarratorResult(
            candidate=revised,
            sources=dict(current.sources),
            review=review(revised),
            skipped=dict(current.skipped),
        )

    return NarrativeRepairLoopResult(
        result=current,
        rounds=rounds,
        budget_exhausted=(
            is_repairable_revise(current.review) and len(rounds) >= max_revise_rounds
        ),
        repair_refused=refused,
    )
