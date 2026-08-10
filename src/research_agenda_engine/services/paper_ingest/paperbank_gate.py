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
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...providers.models.base import StructuredModelFailureKind, StructuredModelProviderError
from ...providers.scientific_agents.base import (
    ScientificAgentFailureKind,
    ScientificAgentSessionError,
)
from ...schemas.cited_literature import (
    CitationSelectionStatus,
    PaperLocalLiteratureContext,
    literature_context_digest,
)
from ...schemas.gate_outcome import GateDecision, GateOutcome
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


def _failed_criteria(outcome: GateOutcome) -> set[str]:
    return {item.criterion for item in outcome.criterion_assessments if not item.passed}


def _redraft_for_fidelity_revise(case: PaperCase, outcome: GateOutcome) -> tuple[PaperCase, str]:
    """The one honest, deterministic repair available at this gate: drop the inline trace draft.

    Measured on the 2026-07-29 climate leg: 6 of 8 `revise` verdicts failed exactly
    ``supports_formation_trace``, on a field that ``promote_paper_case_to_ai_reviewed`` sets to None
    moments later and that the dedicated trace stage then regenerates. So the reviewer was refusing
    papers over a draft the pipeline discards. Removing that draft and asking again lets the reviewer
    judge the artifact that actually survives.

    This is host-side and deterministic: no model call, no prompt, no new construction seam. It does
    not overrule the reviewer — the re-review is a real, independent second verdict, and an accept
    earned there is promoted through the unchanged fail-closed path. A `revise` naming anything other
    than the trace has no deterministic repair here and is left alone, which keeps the round honest
    rather than performative.
    """
    if case.formation_trace is None:
        return case, ""
    if _FORMATION_TRACE_CRITERION not in _failed_criteria(outcome):
        return case, ""
    revised = case.model_copy(deep=True)
    revised.formation_trace = None
    return revised, (
        "Bounded fidelity revision round 1: dropped the inline formation_trace draft the review "
        f"faulted under {_FORMATION_TRACE_CRITERION}; the accepted path nulls that field and the "
        "trace stage drafts a fresh one, so the re-review judges the surviving case."
    )


def _fidelity_with_one_bounded_revision(
    draft: PaperCaseDraft,
    *,
    fidelity_review: FidelityReview,
    batch_context: PaperBankBatchContext,
    revision_notes: dict[str, list[str]],
) -> GateOutcome:
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
    return loop.final_outcome


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

    def _review_one(draft: PaperCaseDraft) -> tuple[GateOutcome | None, GateOutcome | None]:
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

    def _review_one_or_raise(draft: PaperCaseDraft) -> tuple[GateOutcome, GateOutcome | None]:
        assert draft.paper_case is not None and draft.literature is not None
        fidelity = _fidelity_with_one_bounded_revision(
            draft,
            fidelity_review=fidelity_review,
            batch_context=batch_context,
            revision_notes=revision_notes,
        )
        if fidelity.decision != GateDecision.ACCEPT:
            return fidelity, None
        # A paper with no key-citation selection (select_key_citations off, or zero cited works) has
        # nothing for the citation gate to review. Skip it honestly: the paper stands on its fidelity
        # accept and is flagged citation_skipped (D1) — never a bare raise, never silently
        # citation-verified. A non-SELECTED terminal selection also has no reviewable selection.
        if not _has_reviewable_selection(draft.literature):
            return fidelity, None
        return fidelity, citation_review(draft.paper_case, draft.literature)

    if max_workers <= 1 or len(canonical) <= 1:
        reviews = [_review_one(draft) for draft in canonical]
    else:
        with ThreadPoolExecutor(max_workers=min(max_workers, len(canonical))) as pool:
            reviews = list(pool.map(_review_one, canonical))

    accepted: list[AcceptedPaperCase] = []
    for draft, (fidelity, citation) in zip(canonical, reviews, strict=True):
        assert draft.paper_case is not None and draft.literature is not None
        if fidelity is None:
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
        if fidelity.decision != GateDecision.ACCEPT:
            # A `revise` that survived its one repaired re-review is reported as budget exhaustion,
            # carrying what the reviewer still asked for. A bare `fidelity_revise` read as "nobody
            # tried"; this says "we tried once and the reviewer still asked for these changes".
            if fidelity.decision == GateDecision.REVISE:
                reason = FIDELITY_REVISE_BUDGET_EXHAUSTED_REASON
                detail = "; ".join(
                    [
                        fidelity.rationale,
                        *(f"still required: {ask}" for ask in fidelity.required_changes),
                    ]
                )
            else:
                reason = f"fidelity_{fidelity.decision.value}"
                detail = fidelity.rationale
            excluded.append(ExcludedPaper(paper_id=draft.paper_id, reason=reason, detail=detail))
            continue
        citation_unpromoted = citation is None or (
            citation is not None and _citation_can_degrade_without_excluding_paper(citation)
        )
        if (
            citation is not None
            and citation.decision != GateDecision.ACCEPT
            and not citation_unpromoted
        ):
            excluded.append(
                ExcludedPaper(
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
