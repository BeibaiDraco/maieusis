"""PaperBank batch gate — deterministic Stage 0 + per-paper AI Stage 1.

Consumes the per-PDF extraction drafts and produces the AI-reviewed accepted PaperBank:

* **Stage 0 (deterministic, before any gate model call):** drop unparseable papers (isolated, one bad
  PDF never aborts the batch); collapse duplicate PDFs by source SHA-256 to one canonical; record every
  exclusion.
* **Stage 1 (per-paper, independent):** PaperCase fidelity gate → citation-importance gate. An earned
  PaperCase fidelity accept keeps the paper usable. Citation accept promotes the literature sidecar;
  an honest non-blocking revise/insufficient outcome keeps that sidecar unpromoted and visible as a
  warning. Citation identity/evidence failure, blocker/hallucination, reject, or infrastructure failure
  still excludes the paper.

**All-unusable-stop:** if no paper is accepted, ``batch_outcome = all_papers_unusable`` and the caller
must not run the expensive downstream (formation traces, pattern induction). ``run_paperbank_then``
enforces that structurally: the ``on_accepted`` continuation is invoked ONLY when the batch produced at
least one accepted paper — proven by injected spies (call-count 0 on all-unusable).

The review steps are injected callables so the batch logic is testable with mock reviewers and no paid
API. This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...providers.models.base import StructuredModelFailureKind, StructuredModelProviderError
from ...providers.scientific_agents.base import (
    ScientificAgentFailureKind,
    ScientificAgentSessionError,
)
from ...schemas.cited_literature import (
    CitationSelectionPolicy,
    CitationSelectionStatus,
    PaperLocalLiteratureContext,
    literature_context_digest,
)
from ...schemas.gate_outcome import GateDecision, GateLoopResult, GateOutcome
from ...schemas.paper_case import PaperCase
from ...schemas.stage_receipt import FailureClass
from ..agents.citation_importance_reviewer import promote_literature_to_ai_reviewed
from ..agents.gate_kernel import run_gate_with_revise_loop
from ..agents.paper_case_reviewer import (
    PaperBankBatchContext,
    cited_abstract_basis_note,
    promote_paper_case_to_ai_reviewed,
)
from ..agents.promotion import PromotedStatusNotHoldableError

# NOTE: with max_workers > 1 the gate invokes these callables CONCURRENTLY (one worker per draft);
# injected implementations must be thread-safe.
FidelityReview = Callable[
    [PaperCase, PaperLocalLiteratureContext, PaperBankBatchContext], GateOutcome
]
CitationReview = Callable[[PaperCase, PaperLocalLiteratureContext], GateOutcome]


class PaperBankBatchOutcome(StrEnum):
    ACCEPTED = "accepted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    ALL_PAPERS_UNUSABLE = "all_papers_unusable"


class PaperCaseDraft(BaseModel):
    """One per-PDF extraction draft handed to the gate (parseable or not)."""

    model_config = ConfigDict(extra="forbid")

    paper_id: str
    parseable: bool = True
    paper_case: PaperCase | None = None
    literature: PaperLocalLiteratureContext | None = None
    parse_error: str = ""
    failure_class: FailureClass | None = None


class AcceptedPaperCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    paper_case: PaperCase  # AI_REVIEWED
    literature: PaperLocalLiteratureContext  # AI_REVIEWED


class ExcludedPaper(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    reason: str
    detail: str = ""
    canonical_paper_id: str = ""
    failure_class: FailureClass | None = None


class PaperBankGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_outcome: PaperBankBatchOutcome
    accepted: list[AcceptedPaperCase] = Field(default_factory=list)
    excluded: list[ExcludedPaper] = Field(default_factory=list)

    @property
    def should_continue(self) -> bool:
        """True only when at least one paper was accepted — the all-unusable-stop predicate."""
        return bool(self.accepted)


def _has_reviewable_selection(literature: PaperLocalLiteratureContext) -> bool:
    """A citation gate needs a SELECTED key-citation selection. None (no cited works /
    select_key_citations off) or a non-SELECTED terminal (CONTEXT_TOO_LARGE / MODEL_FAILED /
    INSUFFICIENT_EVIDENCE) has nothing reviewable — the citation gate is skipped honestly."""
    selection = literature.importance_selection
    return selection is not None and selection.selection_status == CitationSelectionStatus.SELECTED


def _citation_can_degrade_without_excluding_paper(outcome: GateOutcome) -> bool:
    """True when citation quality is incomplete but its hard identity/evidence closure is intact.

    The citation sidecar does not earn promotion in this path. The fidelity-reviewed PaperCase may
    still proceed to formation-trace review, which independently judges whether the cited literature
    actually supports the trace. Unknown IDs, unresolved evidence, blockers, and hallucinations never
    enter this degraded path.
    """
    return (
        outcome.decision in {GateDecision.REVISE, GateDecision.INSUFFICIENT_EVIDENCE}
        and outcome.evidence_resolved
        and not outcome.blocker_findings
        and not outcome.hallucination_findings
    )


#: Suffix on every ExcludedPaper.reason produced by a CONTAINED gate failure, so a caller can tell
#: a batch emptied by unusable replies from a batch a reviewer actually judged.
GATE_INFRASTRUCTURE_REASON_SUFFIX = "_infrastructure_failure"

#: The fidelity criterion that judges the case's inline formation-trace draft.
_FORMATION_TRACE_CRITERION = "supports_formation_trace"

#: Exactly one revise round for the fidelity gate, deliberately NOT `config.run.max_revise_rounds`
#: (the climate profile sets 2, the example profile 3). Operator direction 2026-07-29: a revise must
#: cause a real revision, and at most one round.
FIDELITY_MAX_REVISE_ROUNDS = 1

#: Reason recorded when the one round ran and the reviewer still asked for changes. Distinct from a
#: bare `fidelity_revise` so a reader can tell "nobody tried" from "we tried once and it still asked".
FIDELITY_REVISE_BUDGET_EXHAUSTED_REASON = "fidelity_revise_budget_exhausted"

#: Reason recorded when the reviewer asked for a change this host has no deterministic repair for,
#: so no round was spent and no second review was paid for. Before this existed, the loop re-reviewed
#: a byte-identical artifact and filed the result as budget exhaustion — a paid call and a false
#: record. Measured across the live corpus: 11 of 20 fidelity `revise` verdicts name nothing this
#: gate can repair.
FIDELITY_REVISE_NO_REPAIR_REASON = "fidelity_revise_no_repair_available"

#: Same pair, one gate later. Before this card the citation gate had NO revise loop at all: 11
#: `citation_revise` and 3 `citation_insufficient_evidence` exclusions across the live corpus, every
#: one a paper a reviewer explicitly declined to reject.
CITATION_MAX_REVISE_ROUNDS = 1
CITATION_REVISE_BUDGET_EXHAUSTED_REASON = "citation_revise_budget_exhausted"
CITATION_REVISE_NO_REPAIR_REASON = "citation_revise_no_repair_available"

#: Every paper exclusion in this module that is NOT a reviewer's final verdict, and the class that
#: says so. A reject / insufficient_evidence keeps `failure_class=None`, which
#: `_paper_half_terminal_cause` reads as science. Operator ruling 2026-08-12: budget exhaustion must
#: not be equivalent to rejection anywhere, and `schemas/stage_receipt.py` already agreed — a
#: reviewer that asked for a change and never gave a final verdict has not judged the science.
_NON_SCIENTIFIC_EXCLUSION_CLASSES: dict[str, FailureClass] = {
    FIDELITY_REVISE_BUDGET_EXHAUSTED_REASON: FailureClass.PROMPT_BUDGET,
    CITATION_REVISE_BUDGET_EXHAUSTED_REASON: FailureClass.PROMPT_BUDGET,
    FIDELITY_REVISE_NO_REPAIR_REASON: FailureClass.VALIDATION_FAILURE,
    CITATION_REVISE_NO_REPAIR_REASON: FailureClass.VALIDATION_FAILURE,
}


def _failed_criteria(outcome: GateOutcome) -> set[str]:
    return {item.criterion for item in outcome.criterion_assessments if not item.passed}


def _publication_date_is_impossible(case: PaperCase) -> bool:
    """True when the recorded publication date could not be supported by any source, ever.

    Purely a host predicate against the run's own clock — no prose parsing, no inference about what
    the right date would be. `20-shaw-miyawaki-2024` carried ``publication_date: '3000-11-30'`` in
    the published climate demo while its own evidence span reads "Published online: 30 November
    2023"; that was the reviewer's ONLY finding, against a rationale recording that the question,
    the dataset cue, all fifteen key citations and the trace were faithful.
    """
    return case.publication_date is not None and case.publication_date > datetime.now(UTC).date()


def _redraft_for_fidelity_revise(case: PaperCase, outcome: GateOutcome) -> tuple[PaperCase, str]:
    """The honest, deterministic repairs available at this gate. No model call, no invention.

    (1) Drop the inline trace draft. Measured on the 2026-07-29 climate leg: 6 of 8 `revise`
    verdicts failed exactly ``supports_formation_trace``, on a field that
    ``promote_paper_case_to_ai_reviewed`` sets to None moments later and that the dedicated trace
    stage then regenerates. So the reviewer was refusing papers over a draft the pipeline discards.

    (2) Clear an impossible ``publication_date``. The field is ``date | None`` and is not one of
    ``missing_required_scientific_fields``, so clearing it costs the case nothing it needs to hold
    reviewed authority. The host deliberately does NOT try to derive the right date from the paper's
    evidence spans: reading "Published online: 30 November 2023" out of prose is inference, and this
    gate does not infer. It removes a claim it can prove no source supports and asks again.

    This is host-side and deterministic: no model call, no prompt, no new construction seam. It does
    not overrule the reviewer — the re-review is a real, independent second verdict, and an accept
    earned there is promoted through the unchanged fail-closed path. A `revise` naming anything else
    still has no repair here and the case is returned untouched, which
    ``run_gate_with_revise_loop`` now detects instead of paying for an identical second review.
    """
    revised = case
    notes: list[str] = []
    if revised.formation_trace is not None and _FORMATION_TRACE_CRITERION in _failed_criteria(
        outcome
    ):
        revised = revised.model_copy(deep=True)
        revised.formation_trace = None
        notes.append(
            "Bounded fidelity revision round 1: dropped the inline formation_trace draft the review "
            f"faulted under {_FORMATION_TRACE_CRITERION}; the accepted path nulls that field and the "
            "trace stage drafts a fresh one, so the re-review judges the surviving case."
        )
    impossible = revised.publication_date
    if impossible is not None and _publication_date_is_impossible(revised):
        revised = revised.model_copy(update={"publication_date": None}, deep=True)
        notes.append(
            f"Bounded fidelity revision round 1: cleared publication_date {impossible.isoformat()}, "
            "which postdates this run and so cannot be supported by any source. The host does not "
            "infer the correct date from the paper's prose; the field is optional and the case's "
            "scientific content is untouched."
        )
    return revised, " ".join(notes)


def _fidelity_with_one_bounded_revision(
    draft: PaperCaseDraft,
    *,
    fidelity_review: FidelityReview,
    batch_context: PaperBankBatchContext,
    revision_notes: dict[str, list[str]],
) -> GateLoopResult:
    """Review the case; on `revise`, repair once deterministically and re-review.

    Before this, `revise` was operationally identical to `reject` — the gate excluded on ANY
    non-ACCEPT decision and no revise loop existed, so a verdict that asks for a change was heard as
    "discard". That cost 8 of 20 papers on the 2026-07-29 climate leg. Same shape as #107/#108, one
    gate earlier.

    Replaces ``draft.paper_case`` when a repair is applied, so the promotion phase promotes the
    artifact that was actually re-reviewed and never a stale draft. The repair note is handed back
    through ``revision_notes`` rather than written onto the case here: ``assert_promotion_binding``
    compares ``outcome.candidate_digest`` against ``stable_hash(case)``, so touching the case after
    its verdict was computed would break its own promotion. The note is appended after promotion,
    exactly where the citation-degrade limitation already is.
    """
    assert draft.paper_case is not None and draft.literature is not None
    literature = draft.literature
    notes: list[str] = []

    def _review(case: PaperCase) -> GateOutcome:
        return fidelity_review(case, literature, batch_context)

    def _redraft(case: PaperCase, outcome: GateOutcome) -> PaperCase:
        revised, note = _redraft_for_fidelity_revise(case, outcome)
        if note:
            notes.append(note)
        return revised

    case, loop = run_gate_with_revise_loop(
        artifact=draft.paper_case,
        review=_review,
        redraft=_redraft,
        max_revise_rounds=FIDELITY_MAX_REVISE_ROUNDS,
    )
    if notes:
        revision_notes.setdefault(draft.paper_id, []).extend(notes)
    draft.paper_case = case
    return loop


def _redraft_for_citation_revise(
    literature: PaperLocalLiteratureContext, outcome: GateOutcome
) -> tuple[PaperLocalLiteratureContext, str]:
    """Drop selected works whose participation the HOST itself can see is unevidenced.

    The one repair available here without reading the reviewer's prose. A selection item that
    carries no ``evidence_context_ids`` AND has no citation context of its own anywhere in the
    packet asserts a rank and a role over nothing: the schema's own
    ``central/supporting citation selection requires evidence context ids`` rule does not catch it,
    because that rule only fires when contexts for the work exist. It is exactly what cost the
    published climate demo ``18-thackeray-et-al-2022``, whose blocker reads that ``cw-1c5f62581c46``
    is "selected with a supporting rank/role ... yet has no evidence_context_ids and no
    corresponding citation_contexts entry anywhere in the input".

    Deterministic and host-checkable: no author-year matching, no prose parsing, nothing invented.
    The dropped item leaves the sidecar smaller and honest, and the re-review is a real independent
    second verdict on it. Every other citation finding — a context attached to the wrong work, an
    abstract-honesty mismatch — has no host repair and returns the literature untouched, which the
    kernel now detects rather than paying for an identical second review.
    """
    selection = literature.importance_selection
    if selection is None:
        return literature, ""
    if selection.selection_policy != CitationSelectionPolicy.EVIDENCE_DRIVEN:
        # A legacy FIXED_COUNT selection is size-locked to its input: fewer than ten cited works
        # must ALL be selected, and ten or more must select between ten and fifteen
        # (`schemas/cited_literature.py:265-280`). Shrinking one is not the host's to do, so this
        # repair is simply unavailable there and the kernel records that rather than producing an
        # artifact that would die at promotion. The product selector emits EVIDENCE_DRIVEN.
        return literature, ""
    evidenced_work_ids = {context.cited_work_id for context in literature.citation_contexts}
    unevidenced = [
        item.cited_work_id
        for item in selection.items
        if not item.evidence_context_ids and item.cited_work_id not in evidenced_work_ids
    ]
    if not unevidenced:
        return literature, ""
    dropped = set(unevidenced)
    kept = [item for item in selection.items if item.cited_work_id not in dropped]
    if not kept:
        # An evidence-driven selection must keep at least one work; a selection where NOTHING is
        # evidenced is not a repair case, it is the reviewer's finding standing.
        return literature, ""
    # Ranks must stay contiguous from 1 (`cited_literature.py:254-256`). Renumbering the survivors
    # in their existing order preserves the model's relative ordering exactly and invents nothing.
    kept_items = [
        item.model_copy(update={"rank": position}) for position, item in enumerate(kept, start=1)
    ]
    revised_selection = selection.model_copy(
        update={
            "items": kept_items,
            # `selected_cited_work_ids` must match item order, not merely membership.
            "selected_cited_work_ids": [item.cited_work_id for item in kept_items],
            "selection_size_actual": len(kept_items),
        },
        deep=True,
    )
    revised = literature.model_copy(update={"importance_selection": revised_selection}, deep=True)
    return revised, (
        "Bounded citation revision round 1: dropped "
        f"{len(unevidenced)} selected work(s) with no citation context anywhere in the packet "
        f"({', '.join(sorted(dropped))}); their rank and role rested on nothing the reviewer or the "
        "host could check. Surviving works keep their relative order and are renumbered from 1; no "
        "other selection was touched."
    )


def _citation_with_one_bounded_revision(
    draft: PaperCaseDraft,
    *,
    citation_review: CitationReview,
    revision_notes: dict[str, list[str]],
) -> GateLoopResult:
    """Review the citation sidecar; on `revise`, repair once deterministically and re-review.

    This gate had NO revise loop. A non-degradable `revise` excluded the whole paper with zero
    rounds — 11 `citation_revise` exclusions across the live corpus, on eight distinct papers, every
    one of them a paper whose reviewer wrote out why revision rather than rejection was the right
    call. `citation_reject` is untouched and still drops the paper on sight.

    Mutates ``draft.literature`` when a repair applies, so promotion binds to the artifact that was
    actually re-reviewed; ``_sync_case_literature_link`` then re-binds the case's stored digest to
    it on both the promoted and the unpromoted path.
    """
    assert draft.paper_case is not None and draft.literature is not None
    paper_case = draft.paper_case
    notes: list[str] = []

    def _review(literature: PaperLocalLiteratureContext) -> GateOutcome:
        return citation_review(paper_case, literature)

    def _redraft(
        literature: PaperLocalLiteratureContext, outcome: GateOutcome
    ) -> PaperLocalLiteratureContext:
        revised, note = _redraft_for_citation_revise(literature, outcome)
        if note:
            notes.append(note)
        return revised

    literature, loop = run_gate_with_revise_loop(
        artifact=draft.literature,
        review=_review,
        redraft=_redraft,
        max_revise_rounds=CITATION_MAX_REVISE_ROUNDS,
    )
    if notes:
        revision_notes.setdefault(draft.paper_id, []).extend(notes)
    draft.literature = literature
    return loop


def _revise_loop_exclusion(
    *,
    paper_id: str,
    gate: str,
    loop: GateLoopResult,
) -> ExcludedPaper | None:
    """The honest non-verdict terminal for a `revise` this gate could not clear, or None.

    Names WHICH of the two happened, and carries a non-scientific class either way. Neither is the
    reviewer's final judgement on the science: one is a budget that ran out, the other is a repair
    the host does not have.
    """
    outcome = loop.final_outcome
    if outcome.decision != GateDecision.REVISE:
        return None
    if loop.redraft_unavailable:
        reason = f"{gate}_revise_no_repair_available"
        lead = (
            "the reviewer asked for a change this host has no deterministic repair for, so no "
            "revision round was spent"
        )
    elif loop.budget_exhausted:
        reason = f"{gate}_revise_budget_exhausted"
        lead = "the bounded revision round ran and the reviewer still asked for changes"
    else:
        return None
    detail = "; ".join(
        [lead, outcome.rationale, *(f"still required: {ask}" for ask in outcome.required_changes)]
    )
    return ExcludedPaper(
        paper_id=paper_id,
        reason=reason,
        detail=detail,
        failure_class=_NON_SCIENTIFIC_EXCLUSION_CLASSES[reason],
    )


_LOCAL_AGENT_KINDS = frozenset(
    {
        ScientificAgentFailureKind.INVALID_RESPONSE,
        ScientificAgentFailureKind.STRUCTURED_OUTPUT_INVALID,
        # Same reasoning that added OUTPUT_TRUNCATED to `_LOCAL_MODEL_KINDS` below: the reviewer
        # ANSWERED and the answer was cut at the ceiling. Omitting it here would make one truncated
        # gate reply read as shared provider exhaustion and abort every sibling paper -- the #114
        # defect, re-entered through the door #144 closed on the other adapter.
        ScientificAgentFailureKind.OUTPUT_TRUNCATED,
    }
)
_LOCAL_MODEL_KINDS = frozenset(
    {
        StructuredModelFailureKind.INVALID_RESPONSE,
        StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID,
        # Reply-shaped like the two above: the reviewer ANSWERED and the answer was cut at the
        # ceiling. Omitting it made one truncated paper reply read as shared provider exhaustion and
        # abort every sibling -- the #114 defect shape, on a kind that did not exist when this set
        # was written.
        StructuredModelFailureKind.OUTPUT_TRUNCATED,
    }
)


def _is_containable_gate_failure(exc: BaseException) -> bool:
    """Reply-shaped (the reviewer ANSWERED unusably) is contained; provider exhaustion is not.

    Containing a retry-exhausted rate limit, timeout, connection or auth failure would record an
    outage as a per-paper scientific exclusion -- infrastructure masquerading as a judged
    PaperBank, which is the defect this project keeps removing. Those are shared: the next sibling
    fails identically, so they stay whole-run and fail closed (AGENTS.md rule 12). Every hard
    boundary -- promotion binding, reviewer independence, branch identity -- raises a bare
    ValueError or AssertionError and is deliberately absent from this predicate.
    """

    if isinstance(exc, ValidationError):
        return True
    if isinstance(exc, ScientificAgentSessionError):
        return exc.kind in _LOCAL_AGENT_KINDS
    if isinstance(exc, StructuredModelProviderError):
        return exc.kind in _LOCAL_MODEL_KINDS
    return False


def _contained_failure_detail(exc: BaseException) -> str:
    """Secret-free, bounded detail for a persisted, user-visible exclusion record.

    The two provider error types keep provider output off ``__str__`` by construction. A pydantic
    ValidationError does not -- it quotes the offending input -- so it is reduced to a field count.
    """

    if isinstance(exc, ValidationError):
        return (
            "the reviewer reply failed strict validation "
            f"({exc.error_count()} field error(s)); the paper was not judged"
        )
    return f"{type(exc).__name__}: {exc}"


def gate_paperbank(
    drafts: Sequence[PaperCaseDraft],
    *,
    fidelity_review: FidelityReview,
    citation_review: CitationReview,
    minimum_paper_count: int = 1,
    max_workers: int = 1,
) -> PaperBankGateResult:
    """Run Stage 0 (deterministic) + Stage 1 (per-paper AI gates) over the extraction drafts.

    ``max_workers > 1`` reviews the canonical drafts concurrently (Stage 1 papers are independent);
    the decision/promotion phase stays serial in draft order, so decisions, ``accepted``/``excluded``
    contents and ordering are identical to the serial path by construction.
    """
    excluded: list[ExcludedPaper] = []

    # --- Stage 0: unparseable isolation + SHA-256 dedup ------------------------------------------
    canonical: list[PaperCaseDraft] = []
    seen_sha: dict[str, str] = {}
    for draft in drafts:
        if not draft.parseable or draft.paper_case is None or draft.literature is None:
            excluded.append(
                ExcludedPaper(
                    paper_id=draft.paper_id,
                    reason="unparseable",
                    detail=draft.parse_error,
                    failure_class=draft.failure_class,
                )
            )
            continue
        sha = draft.paper_case.source_sha256
        if sha and sha in seen_sha:
            excluded.append(
                ExcludedPaper(
                    paper_id=draft.paper_id,
                    reason="duplicate_pdf",
                    canonical_paper_id=seen_sha[sha],
                )
            )
            continue
        if sha:
            seen_sha[sha] = draft.paper_id
        canonical.append(draft)

    if not canonical:
        return PaperBankGateResult(
            batch_outcome=PaperBankBatchOutcome.ALL_PAPERS_UNUSABLE, excluded=excluded
        )

    batch_context = PaperBankBatchContext(
        paperbank_paper_count=len(canonical),
        distinct_paper_types=len({d.paper_case.paper_type for d in canonical if d.paper_case}),
        minimum_paper_count=minimum_paper_count,
    )

    # --- Stage 1: per-paper fidelity → citation gates (independent) ------------------------------
    contained: dict[str, str] = {}
    revision_notes: dict[str, list[str]] = {}

    def _review_one(draft: PaperCaseDraft) -> tuple[GateLoopResult | None, GateLoopResult | None]:
        """One paper's gates, contained.

        Containment lives INSIDE this function on purpose: `list(pool.map(...))` re-raises at
        iteration and discards every sibling's already-paid verdict, so wrapping the pool would
        not save them. Before this, one unusable reply aborted the whole batch and
        `exec_stage_paper_half` -- which has no try/except -- wrote not even a StageReceipt: a bare
        traceback, zero artifacts, zero dossiers. That is the worst outcome available to a user
        building their first PaperBank.
        """
        assert draft.paper_case is not None and draft.literature is not None
        try:
            return _review_one_or_raise(draft)
        except (
            ValidationError,
            ScientificAgentSessionError,
            StructuredModelProviderError,
        ) as exc:
            # Concrete types, never a broad except: a hard boundary -- promotion binding, reviewer
            # independence, branch identity -- raises a bare ValueError or AssertionError and must
            # keep escaping. The kind filter then separates a reply we cannot use from a provider
            # we exhausted.
            if not _is_containable_gate_failure(exc):
                raise
            contained[draft.paper_id] = _contained_failure_detail(exc)
            return None, None

    def _review_one_or_raise(draft: PaperCaseDraft) -> tuple[GateLoopResult, GateLoopResult | None]:
        assert draft.paper_case is not None and draft.literature is not None
        fidelity = _fidelity_with_one_bounded_revision(
            draft,
            fidelity_review=fidelity_review,
            batch_context=batch_context,
            revision_notes=revision_notes,
        )
        if fidelity.final_outcome.decision != GateDecision.ACCEPT:
            return fidelity, None
        # A paper with no key-citation selection (select_key_citations off, or zero cited works) has
        # nothing for the citation gate to review. Skip it honestly: the paper stands on its fidelity
        # accept and is flagged citation_skipped (D1) — never a bare raise, never silently
        # citation-verified. A non-SELECTED terminal selection also has no reviewable selection.
        if not _has_reviewable_selection(draft.literature):
            return fidelity, None
        return fidelity, _citation_with_one_bounded_revision(
            draft,
            citation_review=citation_review,
            revision_notes=revision_notes,
        )

    if max_workers <= 1 or len(canonical) <= 1:
        reviews = [_review_one(draft) for draft in canonical]
    else:
        with ThreadPoolExecutor(max_workers=min(max_workers, len(canonical))) as pool:
            reviews = list(pool.map(_review_one, canonical))

    accepted: list[AcceptedPaperCase] = []
    for draft, (fidelity_loop, citation_loop) in zip(canonical, reviews, strict=True):
        assert draft.paper_case is not None and draft.literature is not None
        if fidelity_loop is None:
            # Contained: this paper was never judged. Recorded as an infrastructure exclusion so it
            # can never be read as a scientific verdict on the paper.
            excluded.append(
                ExcludedPaper(
                    paper_id=draft.paper_id,
                    reason=f"gate{GATE_INFRASTRUCTURE_REASON_SUFFIX}",
                    detail=contained.get(draft.paper_id, "the reviewer returned no usable verdict"),
                    failure_class=FailureClass.SCHEMA_ERROR,
                )
            )
            continue
        fidelity = fidelity_loop.final_outcome
        citation = citation_loop.final_outcome if citation_loop is not None else None
        if fidelity.decision != GateDecision.ACCEPT:
            # A `revise` the loop could not clear names WHICH of the two things happened and carries
            # a non-scientific class; a reject / insufficient_evidence is the reviewer's own final
            # verdict and keeps `failure_class=None`, which downstream reads as science.
            non_verdict = _revise_loop_exclusion(
                paper_id=draft.paper_id, gate="fidelity", loop=fidelity_loop
            )
            excluded.append(
                non_verdict
                if non_verdict is not None
                else ExcludedPaper(
                    paper_id=draft.paper_id,
                    reason=f"fidelity_{fidelity.decision.value}",
                    detail=fidelity.rationale,
                )
            )
            continue
        citation_unpromoted = citation is None or (
            citation is not None and _citation_can_degrade_without_excluding_paper(citation)
        )
        if (
            citation is not None
            and citation.decision != GateDecision.ACCEPT
            and not citation_unpromoted
        ):
            assert citation_loop is not None
            non_verdict = _revise_loop_exclusion(
                paper_id=draft.paper_id, gate="citation", loop=citation_loop
            )
            excluded.append(
                non_verdict
                if non_verdict is not None
                else ExcludedPaper(
                    paper_id=draft.paper_id,
                    reason=f"citation_{citation.decision.value}",
                    detail=citation.rationale,
                )
            )
            continue
        try:
            promoted_case = promote_paper_case_to_ai_reviewed(
                draft.paper_case,
                fidelity,
                cited_abstract_basis=cited_abstract_basis_note(draft.literature),
            )
        except PromotedStatusNotHoldableError as exc:
            # The highest-traffic promoter, and it had the same gap: `PaperCase.validate_reviewed_fields`
            # gates on `review.status`, and constructing the inner `PaperCaseReview` does not re-run the
            # outer rule. One paper that cannot hold reviewed authority is excluded honestly; its
            # siblings keep their already-paid verdicts.
            excluded.append(
                ExcludedPaper(
                    paper_id=draft.paper_id,
                    reason="fidelity_unholdable_reviewed_status",
                    detail=str(exc),
                )
            )
            continue
        # After promotion validated the digest binding, never before: a bounded revision round is
        # part of this paper's honest history and the reader is entitled to see it.
        promoted_case.review.corrections.extend(revision_notes.get(draft.paper_id, []))
        if citation_unpromoted:
            # Stands on fidelity alone: keep the literature at its extractor review status (no citation
            # promotion), record the honest limitation on the case review, and keep the pre-review link.
            limitation = (
                "citation gate skipped: no key-citation selection"
                if citation is None
                else f"citation gate {citation.decision.value}: {citation.rationale}"
            )
            promoted_case = _sync_case_literature_link(promoted_case, draft.literature)
            promoted_case.review.corrections.append(
                f"{limitation} (paper stands on fidelity; literature remains unpromoted)"
            )
            accepted.append(
                AcceptedPaperCase(
                    paper_id=draft.paper_id,
                    paper_case=promoted_case,
                    literature=draft.literature,
                )
            )
            continue
        assert citation is not None  # not skipped and fidelity accepted ⇒ a real citation outcome
        promoted_literature = promote_literature_to_ai_reviewed(draft.literature, citation)
        # Re-sync the case's literature-sidecar linkage to the PROMOTED literature. Promotion flips
        # review_status (which the digest covers), so a case built over the pre-review literature would
        # otherwise carry a stale digest and fail the downstream case↔literature link check when the
        # formation-trace context is built.
        promoted_case = _sync_case_literature_link(promoted_case, promoted_literature)
        accepted.append(
            AcceptedPaperCase(
                paper_id=draft.paper_id,
                paper_case=promoted_case,
                literature=promoted_literature,
            )
        )

    if not accepted:
        outcome = PaperBankBatchOutcome.ALL_PAPERS_UNUSABLE
    elif len(accepted) < minimum_paper_count:
        outcome = PaperBankBatchOutcome.INSUFFICIENT_EVIDENCE
    else:
        outcome = PaperBankBatchOutcome.ACCEPTED
    return PaperBankGateResult(batch_outcome=outcome, accepted=accepted, excluded=excluded)


def _sync_case_literature_link(
    paper_case: PaperCase, literature: PaperLocalLiteratureContext
) -> PaperCase:
    """Bind a promoted/fidelity-only case to the exact selection that proceeds downstream."""
    if not paper_case.local_literature_context_id:
        return paper_case
    selection = literature.importance_selection
    return paper_case.model_copy(
        update={
            "local_literature_context_id": literature.context_id,
            "local_literature_context_digest": literature_context_digest(literature),
            "key_cited_work_ids": list(
                selection.selected_cited_work_ids if selection is not None else []
            ),
        }
    )


def run_paperbank_then(
    drafts: Sequence[PaperCaseDraft],
    *,
    fidelity_review: FidelityReview,
    citation_review: CitationReview,
    on_accepted: Callable[[list[AcceptedPaperCase]], None],
    minimum_paper_count: int = 1,
    max_workers: int = 1,
) -> PaperBankGateResult:
    """Gate the PaperBank, then run ``on_accepted`` ONLY if at least one paper was accepted.

    This is the structural all-unusable-stop: the expensive downstream (``on_accepted``) is never
    reached when the gate produced zero accepted papers.
    """
    result = gate_paperbank(
        drafts,
        fidelity_review=fidelity_review,
        citation_review=citation_review,
        minimum_paper_count=minimum_paper_count,
        max_workers=max_workers,
    )
    if result.should_continue:
        on_accepted(result.accepted)
    return result
