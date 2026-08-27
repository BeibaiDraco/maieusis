"""Independent-AI fidelity gate for the fused coarse ``DatasetNarrative``.

Mirrors ``plan_reviewer.py``: a ``ScientificAgentProvider`` session judges a candidate fused
narrative against ALL FOUR source coarse-facts feeds (with their provenance URIs + trust ranks), and
returns a structured accept / revise / reject with per-criterion assessments. The reviewer must be an
INDEPENDENT provider/model from the generators (cross-provider), so a hallucinating generator cannot
also bless its own narrative.

``reject`` is an honest terminal. ``revise`` no longer is: since 2026-08-12 a repairable ``revise``
enters the bounded source-locked repair loop in ``narrative_sources/narrative_revision.py``, which
re-asks the narrator model to rewrite the prose it wrote and returns the redraft to THIS gate. The
old claim here -- "GF-2c runs no revise loop" -- was read as a statement that no loop was possible,
which was never true: fusion is deterministic but the content it fuses is model-written.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ...assets import resolve_asset
from ...providers.scientific_agents import (
    ScientificAgentProvider,
    ScientificAgentSession,
)
from ...schemas.coarse_dataset_facts import CoarseDatasetFacts
from ...schemas.dataset_narrative import DatasetNarrative
from ...schemas.gate_outcome import GateCriterionAssessment, GateCriterionAuditRecord
from ..narrative_sources.fusion import SourceKind, source_locator
from .gate_kernel import clean_required_changes, resolve_criterion_assessments
from .reviewer_base import (
    assert_reviewer_provider_independent,
    build_scientific_reviewer_provider_from_env,
)

DATASET_NARRATIVE_FIDELITY_REVIEWER_PROMPT_VERSION = "dataset_narrative_fidelity_reviewer/v2"

_TRUST_RANK: dict[SourceKind, int] = {
    SourceKind.USER_DESCRIPTION: 0,  # highest trust
    SourceKind.DOCUMENTATION: 1,
    SourceKind.LOCAL_SAMPLE: 2,
    SourceKind.MODEL_RESEARCH: 3,  # lowest trust
}


class DatasetNarrativeFidelityDecision(StrEnum):
    ACCEPT = "accept"
    REVISE = "revise"
    REJECT = "reject"


CANONICAL_FIDELITY_CRITERIA: tuple[str, ...] = ("faithful", "coarse", "trust_harmonized")


class FidelityCriterionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # The provider-facing shape remains tolerant of unknown labels so useful review content survives
    # parsing. The host then applies the shared deterministic criterion resolver: formatting-only
    # variants may canonicalize; unknown, missing, or conflicting labels cannot earn accept.
    criterion: str
    passed: bool
    notes: str = ""

    @field_validator("criterion")
    @classmethod
    def require_criterion(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("fidelity criterion must be non-empty")
        return value


class DatasetNarrativeFidelityReviewContent(BaseModel):
    """The reviewer's structured judgement (what the model returns)."""

    model_config = ConfigDict(extra="forbid")

    decision: DatasetNarrativeFidelityDecision
    rationale: str
    criterion_assessments: list[FidelityCriterionAssessment]
    required_changes: list[str] = Field(default_factory=list)
    unfaithful_claims: list[str] = Field(default_factory=list)
    too_precise_findings: list[str] = Field(default_factory=list)
    hallucination_findings: list[str] = Field(default_factory=list)


class FidelitySourceView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_kind: str
    source_locator: str
    trust_rank: int
    coarse_facts: dict[str, Any]


class DatasetNarrativeFidelityTurnInput(BaseModel):
    """Reviewer input: the candidate narrative + ALL sources with provenance + trust (commander)."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    candidate_narrative: dict[str, Any]
    field_evidence_source_ids: dict[str, list[str]]
    sources: list[FidelitySourceView]
    required_criteria: list[str] = Field(default_factory=list)
    review_guidance: str = ""


class DatasetNarrativeFidelityReview(BaseModel):
    """The recorded review (content + provenance/independence audit)."""

    model_config = ConfigDict(extra="forbid")

    review_id: str
    dataset_id: str
    prompt_version: str
    provider_id: str
    model_id: str
    session_id: str
    input_digest: str
    output_digest: str
    generator_provider_ids: list[str]
    decision: DatasetNarrativeFidelityDecision
    downgraded_from: DatasetNarrativeFidelityDecision | None = None
    rationale: str
    criterion_assessments: list[FidelityCriterionAssessment]
    criterion_audit: list[GateCriterionAuditRecord] = Field(default_factory=list)
    criterion_review_complete: bool = True
    required_changes: list[str] = Field(default_factory=list)
    unfaithful_claims: list[str] = Field(default_factory=list)
    too_precise_findings: list[str] = Field(default_factory=list)
    hallucination_findings: list[str] = Field(default_factory=list)


def load_dataset_narrative_fidelity_reviewer_prompt(
    prompt_version: str = DATASET_NARRATIVE_FIDELITY_REVIEWER_PROMPT_VERSION,
) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def build_dataset_narrative_fidelity_reviewer_provider_from_env(
    *,
    provider: Literal["openai", "anthropic"] | None = None,
    allow_pro_model: bool = False,
    project_root: str | Path | None = None,
) -> ScientificAgentProvider:
    """Build a live independent narrative fidelity reviewer provider from runtime env files."""
    return build_scientific_reviewer_provider_from_env(
        system_prompt_loader=load_dataset_narrative_fidelity_reviewer_prompt,
        credential_fallback=("anthropic", "openai"),
        unsupported_provider_label="narrative fidelity reviewer",
        provider=provider,
        allow_pro_model=allow_pro_model,
        project_root=project_root,
    )


def review_dataset_narrative_fidelity(
    *,
    session: ScientificAgentSession,
    dataset_id: str,
    candidate: DatasetNarrative,
    sources: Mapping[SourceKind, CoarseDatasetFacts | None],
    generator_provider_ids: Sequence[str],
    review_guidance: str = "",
) -> DatasetNarrativeFidelityReview:
    """Run the independent fidelity gate over the candidate + every source that was actually present.

    "All four sources" was never true of a run: v0.1 wires A and D only (`fusion` module docstring).
    The reviewer sees the feeds in ``sources``, so it judges what the fuser really merged.
    """
    source_views = [
        FidelitySourceView(
            source_kind=kind.value,
            source_locator=source_locator(facts),
            trust_rank=_TRUST_RANK[kind],
            coarse_facts=facts.model_dump(mode="json"),
        )
        for kind in SourceKind
        if (facts := sources.get(kind)) is not None
    ]
    if not source_views:
        raise ValueError("fidelity review requires at least one source")

    turn_input = DatasetNarrativeFidelityTurnInput(
        dataset_id=dataset_id,
        candidate_narrative=candidate.model_dump(mode="json"),
        field_evidence_source_ids=candidate.field_evidence_source_ids,
        sources=source_views,
        required_criteria=list(CANONICAL_FIDELITY_CRITERIA),
        review_guidance=review_guidance,
    )
    content = session.send(turn_input, DatasetNarrativeFidelityReviewContent)
    record = session.snapshot().transcript[-1]
    assert_reviewer_provider_independent(
        record.provider_id,
        generator_provider_ids,
        role_label="narrative fidelity reviewer",
    )
    criterion_resolution = resolve_criterion_assessments(
        [
            GateCriterionAssessment(
                criterion=item.criterion,
                passed=item.passed,
                notes=item.notes,
            )
            for item in content.criterion_assessments
        ],
        CANONICAL_FIDELITY_CRITERIA,
    )
    criterion_assessments = [
        FidelityCriterionAssessment(
            criterion=item.criterion,
            passed=item.passed,
            notes=item.notes,
        )
        for item in criterion_resolution.canonical_assessments
    ]
    required_changes = clean_required_changes(content.required_changes)
    unfaithful = bool(content.unfaithful_claims or content.hallucination_findings)
    # `required_changes` is deliberately NOT here. It was, and on the live corpus that single
    # disjunct is the only thing this gate has ever done: across 19 runs the reviewer returned
    # `accept` 19/19 with all three criteria passing, and the one run that also carried a
    # required_change -- "Consider reformatting the temporal_structure field ... for readability
    # (not a fidelity blocker)", the reviewer's own words -- was downgraded to `revise`, refused by
    # the promoter, and reached the user as "this run did not have enough usable evidence", outcome
    # class `scientific`, with an instruction to go change the papers and the dataset. Both were
    # fine. A suggestion is not a finding, and a gate that cannot tell them apart is a coin flip on
    # a whole paid run.
    #
    # Everything that IS a finding still blocks: a missing, failed, unknown or conflicting
    # criterion, an unfaithful claim, an over-precise claim, a hallucination. The gate's actual job
    # -- unsupported claims, over-precision, trust mishandling -- is untouched. What changed is that
    # the reviewer may now say "accept, and here is a nit" and be believed on the accept.
    accept_blocked = bool(
        criterion_resolution.missing
        or criterion_resolution.failed
        or criterion_resolution.unknown
        or criterion_resolution.conflicts
        or unfaithful
        or content.too_precise_findings
    )
    decision = content.decision
    downgraded_from = None
    if decision == DatasetNarrativeFidelityDecision.ACCEPT and accept_blocked:
        downgraded_from = DatasetNarrativeFidelityDecision.ACCEPT
        decision = (
            DatasetNarrativeFidelityDecision.REJECT
            if unfaithful
            else DatasetNarrativeFidelityDecision.REVISE
        )
        if not required_changes:
            required_changes = [
                *[
                    f"criterion not satisfied: {name}"
                    for name in (*criterion_resolution.missing, *criterion_resolution.failed)
                ],
                *[f"unknown criterion returned: {name!r}" for name in criterion_resolution.unknown],
                *[
                    f"conflicting duplicate criterion assessments: {name}"
                    for name in criterion_resolution.conflicts
                ],
                *[f"unfaithful claim: {finding}" for finding in content.unfaithful_claims],
                *[f"claim is too precise: {finding}" for finding in content.too_precise_findings],
                *[
                    f"hallucination finding: {finding}"
                    for finding in content.hallucination_findings
                ],
            ]
    return DatasetNarrativeFidelityReview(
        review_id=f"dataset-narrative-fidelity-{dataset_id}-{record.output_digest[:12]}",
        dataset_id=dataset_id,
        prompt_version=record.prompt_version,
        provider_id=record.provider_id,
        model_id=record.model_id,
        session_id=record.session_id,
        input_digest=record.input_digest,
        output_digest=record.output_digest,
        generator_provider_ids=sorted({pid for pid in generator_provider_ids if pid}),
        decision=decision,
        downgraded_from=downgraded_from,
        rationale=content.rationale,
        criterion_assessments=criterion_assessments,
        criterion_audit=list(criterion_resolution.audit),
        criterion_review_complete=not (
            criterion_resolution.missing
            or criterion_resolution.unknown
            or criterion_resolution.conflicts
        ),
        required_changes=required_changes,
        unfaithful_claims=list(content.unfaithful_claims),
        too_precise_findings=list(content.too_precise_findings),
        hallucination_findings=list(content.hallucination_findings),
    )
