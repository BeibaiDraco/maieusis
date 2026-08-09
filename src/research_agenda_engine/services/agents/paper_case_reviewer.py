"""Independent-AI PaperCase fidelity gate — the upstream pollution entry.

Verifies structurally (dataset-agnostic — no neuroscience assumptions) that an extracted PaperCase is
faithful to its source paper before it can support a formation trace: the paper's real scientific
question was extracted, the dataset cue came from the paper, the key citations really participated in
question formation, a missing abstract is honestly recorded, and the case suffices to support a
formation trace. Mirrors ``dataset_narrative_reviewer.py`` and runs on the 5a-1 gate kernel
(cross-provider reviewer, structurally earned accept). Deterministic evidence pre-checks (do the
key_cited_work_ids resolve? do the referenced spans exist?) are host-side; the model cannot assert
evidence closure.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ...assets import resolve_asset
from ...providers.scientific_agents import ScientificAgentProvider, ScientificAgentSession
from ...schemas.cited_literature import AbstractRetrievalStatus, PaperLocalLiteratureContext
from ...schemas.gate_outcome import GateOutcome
from ...schemas.paper_case import PaperCase, PaperCaseReview, PaperCaseReviewStatus
from ..context.evidence_basis_labels import ABSTRACT_ONLY_PHRASE
from .gate_kernel import run_structured_gate_review
from .promotion import assert_promoted_status_is_holdable, assert_promotion_binding
from .reviewer_base import build_scientific_reviewer_provider_from_env

PAPER_CASE_FIDELITY_REVIEWER_PROMPT_VERSION = "paper_case_fidelity_reviewer/v3"
PAPER_CASE_FIDELITY_GATE = "paper_case_fidelity"

# Structural fidelity criteria — all dataset-agnostic (no domain vocabulary).
PAPER_CASE_FIDELITY_CRITERIA: tuple[str, ...] = (
    "question_extracted_faithfully",
    "dataset_cue_from_paper",
    "key_citations_participated",
    "citation_context_matches",
    "missing_abstract_recorded",
    "supports_formation_trace",
)


class PaperBankBatchContext(BaseModel):
    """Batch-level context handed to the fidelity reviewer as hard context (min count + diversity)."""

    model_config = ConfigDict(extra="forbid")

    paperbank_paper_count: int = Field(ge=0)
    distinct_paper_types: int = Field(ge=0)
    minimum_paper_count: int = Field(ge=1, default=1)


class PaperCaseFidelityTurnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_case: dict[str, Any]
    cited_works: list[dict[str, Any]]
    citation_contexts: list[dict[str, Any]]
    importance_selection: dict[str, Any] | None
    batch_context: PaperBankBatchContext
    review_guidance: str = ""


def load_paper_case_fidelity_reviewer_prompt(
    prompt_version: str = PAPER_CASE_FIDELITY_REVIEWER_PROMPT_VERSION,
) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def build_paper_case_fidelity_reviewer_provider_from_env(
    *,
    provider: Literal["openai", "anthropic"] | None = None,
    allow_pro_model: bool = False,
    project_root: str | Path | None = None,
) -> ScientificAgentProvider:
    """Build a live independent PaperCase fidelity reviewer provider from runtime env files."""
    return build_scientific_reviewer_provider_from_env(
        system_prompt_loader=load_paper_case_fidelity_reviewer_prompt,
        credential_fallback=("anthropic", "openai"),
        unsupported_provider_label="PaperCase fidelity reviewer",
        provider=provider,
        allow_pro_model=allow_pro_model,
        project_root=project_root,
    )


def _evidence_resolved(paper_case: PaperCase, literature: PaperLocalLiteratureContext) -> bool:
    """Host-side hard identity closure for every locator carried by the PaperCase.

    This includes the inline formation trace: even though accepted cases later receive a newly drafted
    trace, a candidate carrying invented source/span/citation locators cannot cross this hard boundary.
    ``selected ⊆ input`` is already enforced at CitationImportanceSelection construction.
    """
    cited_ids = {work.cited_work_id for work in literature.cited_works}
    if not set(paper_case.key_cited_work_ids) <= cited_ids:
        return False
    trace = paper_case.formation_trace
    if trace is None:
        return True
    span_ids = {span.source_span_id for span in paper_case.evidence_spans if span.source_span_id}
    context_ids = {context.context_id for context in literature.citation_contexts}
    if not set(trace.evidence_span_ids) <= span_ids:
        return False
    if not set(trace.key_cited_work_ids) <= cited_ids:
        return False
    if not {item.cited_work_id for item in trace.literature_evidence} <= cited_ids:
        return False
    return all(
        set(binding.source_span_ids) <= span_ids
        and set(binding.cited_work_ids) <= cited_ids
        and set(binding.citation_context_ids) <= context_ids
        for binding in trace.evidence_bindings
    )


def cited_abstract_availability(literature: PaperLocalLiteratureContext) -> tuple[int, int]:
    """(unavailable, total) cited-work abstract counts — the veto→label input (PR #25 class)."""
    total = len(literature.cited_works)
    unavailable = sum(
        1
        for work in literature.cited_works
        if work.abstract_status == AbstractRetrievalStatus.UNAVAILABLE
    )
    return unavailable, total


def cited_abstract_review_guidance(literature: PaperLocalLiteratureContext) -> str:
    """Deterministic belt: a faithful case whose cited abstracts are genuinely unavailable to this
    system must NOT be hard-rejected on the citation criteria. Present only when some are missing;
    fabrication/faithfulness/cue-import checks are explicitly kept strict."""
    unavailable, total = cited_abstract_availability(literature)
    if not unavailable:
        return ""
    return (
        f"Cited-work abstracts: {unavailable} of {total} cited works have no abstract "
        f"available to this system. Judge key_citations_participated and citation_context_matches "
        f"from the paper's OWN citation contexts and reference metadata; genuine unavailability is a "
        f"recorded limitation under missing_abstract_recorded, NOT a failure of those criteria and "
        f"NOT grounds for reject. A fabricated question, an imported dataset cue, or a key citation "
        f"drawn from an unrelated passage still fails."
    )


def cited_abstract_basis_note(literature: PaperLocalLiteratureContext) -> str:
    """The honest, cause-neutral label stamped on an accepted case when abstracts were unavailable."""
    unavailable, total = cited_abstract_availability(literature)
    if not unavailable:
        return ""
    return f"Cited-abstract basis: {unavailable} of {total} cited works — {ABSTRACT_ONLY_PHRASE}."


def review_paper_case_fidelity(
    *,
    session: ScientificAgentSession,
    paper_case: PaperCase,
    literature: PaperLocalLiteratureContext,
    batch_context: PaperBankBatchContext,
    generator_provider_ids: Sequence[str],
    review_guidance: str = "",
) -> GateOutcome:
    """Run the independent PaperCase fidelity gate; returns a structurally-earned GateOutcome."""
    selection = literature.importance_selection
    merged_guidance = "\n".join(
        line for line in [cited_abstract_review_guidance(literature), review_guidance] if line
    )
    turn_input = PaperCaseFidelityTurnInput(
        paper_case=paper_case.model_dump(mode="json"),
        cited_works=[work.model_dump(mode="json") for work in literature.cited_works],
        citation_contexts=[ctx.model_dump(mode="json") for ctx in literature.citation_contexts],
        importance_selection=selection.model_dump(mode="json") if selection is not None else None,
        batch_context=batch_context,
        review_guidance=merged_guidance,
    )
    return run_structured_gate_review(
        session=session,
        turn_input=turn_input,
        candidate=paper_case,
        gate_name=PAPER_CASE_FIDELITY_GATE,
        required_criteria=PAPER_CASE_FIDELITY_CRITERIA,
        evidence_resolved=_evidence_resolved(paper_case, literature),
        generator_provider_ids=generator_provider_ids,
    )


def promote_paper_case_to_ai_reviewed(
    paper_case: PaperCase, outcome: GateOutcome, *, cited_abstract_basis: str = ""
) -> PaperCase:
    """Stamp ``AI_REVIEWED`` on a fidelity-accepted PaperCase, or raise (fail closed).

    The outcome is BOUND to this PaperCase (expected gate + candidate digest + independent reviewer +
    earned accept). The status is set via the AI promoter ONLY — never the human importer — so an AI
    verdict can never masquerade as ``EXPERT_REVIEWED``. ``cited_abstract_basis`` (from
    ``cited_abstract_basis_note``) is an honest label recorded when some cited abstracts were
    unavailable to this system — the accept stands on the paper's own structure, and the label says so.
    """
    assert_promotion_binding(
        candidate=paper_case, outcome=outcome, expected_gate=PAPER_CASE_FIDELITY_GATE
    )
    promoted = paper_case.model_copy(deep=True)
    # The inline formation_trace is replaced after the candidate has crossed the fidelity gate. Its
    # locators were nevertheless checked by `_evidence_resolved`; clearing it here prevents the
    # temporary draft from becoming the authoritative post-review formation trace.
    promoted.formation_trace = None
    note = (
        f"Independent-AI PaperCase fidelity gate {PAPER_CASE_FIDELITY_REVIEWER_PROMPT_VERSION} "
        f"(model {outcome.reviewer_model_id}, session {outcome.reviewer_session_id}) accepted; "
        f"reviewer independent of generators."
    )
    if cited_abstract_basis:
        note = f"{note} {cited_abstract_basis}"
    # An improvement the reviewer named while accepting must reach a READER, not just the audit trail.
    # `render_paper_case_summary` prints `evidence_requests` under "Open uncertainties" and prints
    # neither `review.note` nor `review.corrections`, so the note alone would be invisible — which is
    # how the citation-degrade limitation has been invisible all along.
    for ask in outcome.required_changes:
        request = f"ReviewerNote[accepted_with_improvement]: {ask}"
        if request not in promoted.evidence_requests:
            promoted.evidence_requests.append(request)
    promoted.review = PaperCaseReview(
        status=PaperCaseReviewStatus.AI_REVIEWED,
        previous_status=paper_case.review.status,
        reviewer=f"ai:{outcome.reviewer_provider_id}",
        reviewed_at=datetime.now(UTC),
        corrections=list(paper_case.review.corrections),
        note=note,
    )
    # `PaperCase.validate_reviewed_fields` gates on `review.status`, and constructing the inner
    # `PaperCaseReview` does not re-run the outer rule -- so this stamp can mint an unholdable
    # status exactly like the trace promoter did.
    assert_promoted_status_is_holdable(promoted, expected_gate=PAPER_CASE_FIDELITY_GATE)
    return promoted
