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

from pydantic import BaseModel, ConfigDict, Field

from ...schemas.cited_literature import (
    CitationSelectionStatus,
    PaperLocalLiteratureContext,
    literature_context_digest,
)
from ...schemas.gate_outcome import GateDecision, GateOutcome
from ...schemas.paper_case import PaperCase
from ..agents.citation_importance_reviewer import promote_literature_to_ai_reviewed
from ..agents.paper_case_reviewer import (
    PaperBankBatchContext,
    cited_abstract_basis_note,
    promote_paper_case_to_ai_reviewed,
)

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
                    paper_id=draft.paper_id, reason="unparseable", detail=draft.parse_error
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
    def _review_one(draft: PaperCaseDraft) -> tuple[GateOutcome, GateOutcome | None]:
        assert draft.paper_case is not None and draft.literature is not None
        fidelity = fidelity_review(draft.paper_case, draft.literature, batch_context)
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
        if fidelity.decision != GateDecision.ACCEPT:
            excluded.append(
                ExcludedPaper(
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
            excluded.append(
                ExcludedPaper(
                    paper_id=draft.paper_id,
                    reason=f"citation_{citation.decision.value}",
                    detail=citation.rationale,
                )
            )
            continue
        promoted_case = promote_paper_case_to_ai_reviewed(
            draft.paper_case,
            fidelity,
            cited_abstract_basis=cited_abstract_basis_note(draft.literature),
        )
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
