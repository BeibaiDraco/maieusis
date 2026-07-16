"""Unified front-half gate vocabulary + earned-outcome schema.

This is the GO-FORWARD result vocabulary for every front-half quality gate (PaperCase fidelity,
citation-importance, formation-trace, pattern, and — in 5a-1b — topic-evidence). Relationship to the
two pre-existing decision vocabs (NOT migrated this slice, to avoid churn on merged code):

  * ``DatasetNarrativeFidelityDecision`` (5a-0, ``services/agents/dataset_narrative_reviewer.py``):
    accept / revise / reject — the narrative fidelity gate keeps its own 3-value vocab.
  * ``GenericReviewDecisionValue`` (``schemas/generic_review_authority.py``): the downstream
    dossier-authority axis (accept_for_*_dossier / revision_required / reject / human_escalation).

``GateDecision`` adds the two honest terminals those lack at the front half: ``insufficient_evidence``
(scientific evidence too thin to judge — NOT a reject) and ``infrastructure_failure`` (host-side
API/timeout/parser/validation error — NEVER a scientific rejection).

``accept`` is EARNED, not the model's say-so: ``GateReviewContent`` is what the reviewer model returns;
``GateOutcome`` is the structurally-derived verdict (see ``services/agents/gate_kernel.py``).

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class GateDecision(StrEnum):
    ACCEPT = "accept"
    REVISE = "revise"
    REJECT = "reject"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"


class GateModelDecision(StrEnum):
    """The reviewer MODEL's say-so vocabulary — deliberately WITHOUT ``infrastructure_failure``.

    Infrastructure failure is a host-only classification (a provider/timeout/parser/validation error);
    ``resolve_gate_outcome`` sets it from the host ``infrastructure_error`` flag. Excluding it here means
    a reviewer model can never *claim* an infra failure to dodge a scientific verdict. Values are a
    subset of ``GateDecision`` (same strings), so mapping to the final ``GateDecision`` is by value.
    """

    ACCEPT = "accept"
    REVISE = "revise"
    REJECT = "reject"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ReviewerExecutionKind(StrEnum):
    """How the reviewer that produced a verdict actually ran.

    ``LIVE_API`` is a real frontier-model call; ``MOCK`` is a fixture/demo reviewer. This is NOT an
    unforgeable language-level guarantee — it is a recorded signal set type-side by the concrete
    session/provider. The product-serious guarantee is the controlled factory (Standard builds only
    live reviewers) + ``assert_product_grade_promotion`` refusing a ``MOCK`` promotion receipt.
    """

    LIVE_API = "live_api"
    MOCK = "mock"


class GateCriterionAuditStatus(StrEnum):
    """Host-side disposition of one raw reviewer criterion label.

    This audit vocabulary is deliberately about presentation/coverage, not scientific meaning. The
    host may normalize case, surrounding whitespace, spaces, and hyphens, but it never guesses that
    an unknown paraphrase means one of the required criteria.
    """

    MATCHED = "matched"
    UNKNOWN = "unknown"
    DUPLICATE_CONSISTENT = "duplicate_consistent"
    DUPLICATE_CONFLICT = "duplicate_conflict"


class GateCriterionAuditRecord(BaseModel):
    """Raw-to-canonical record for one model-returned criterion assessment."""

    model_config = ConfigDict(extra="forbid")

    raw_criterion: str
    normalized_criterion: str
    # Empty only when the normalized label is not one of the host-required canonical criteria.
    canonical_criterion: str = ""
    passed: bool
    notes: str = ""
    status: GateCriterionAuditStatus


class GateCriterionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criterion: str
    passed: bool
    notes: str = ""


class GateReviewContent(BaseModel):
    """What the reviewer model returns — its say-so, NOT the final verdict.

    The reviewer may return ``accept`` here; the kernel re-derives the real outcome from the criteria,
    findings, evidence resolution, and required_changes. A model-supplied ``accept`` with a failed
    criterion is downgraded, never trusted. ``decision`` uses ``GateModelDecision`` — the model cannot
    emit ``infrastructure_failure`` (host-only).
    """

    model_config = ConfigDict(extra="forbid")

    decision: GateModelDecision
    rationale: str = ""
    criterion_assessments: list[GateCriterionAssessment] = Field(default_factory=list)
    required_changes: list[str] = Field(default_factory=list)
    blocker_findings: list[str] = Field(default_factory=list)
    hallucination_findings: list[str] = Field(default_factory=list)


class GateOutcome(BaseModel):
    """The structurally-derived verdict (earned) + reviewer provenance (independent-AI authority).

    The three binding fields (``candidate_digest`` / ``generator_provider_ids`` /
    ``reviewer_execution_kind``) are REQUIRED: a promoter binds the outcome to THIS artifact, re-asserts
    reviewer independence, and records execution kind at the trust boundary, so an unpopulated outcome
    cannot exist and a promoter cannot silently skip the binding.
    """

    model_config = ConfigDict(extra="forbid")

    gate_name: str
    decision: GateDecision
    # Digest of the SPECIFIC candidate artifact this verdict is about (binds outcome→artifact).
    candidate_digest: str
    # The generator provider ids the reviewer had to be independent of (re-asserted at promotion).
    generator_provider_ids: list[str]
    # How the reviewer ran (live_api vs mock) — recorded for the promotion receipt / product-grade gate.
    reviewer_execution_kind: ReviewerExecutionKind
    rationale: str = ""
    criterion_assessments: list[GateCriterionAssessment] = Field(default_factory=list)
    # Host-built raw→canonical audit. ``criterion_assessments`` above is the canonical, deduplicated
    # view used for authority; this ledger preserves every raw reviewer item, including unknown and
    # conflicting duplicates.
    criterion_audit: list[GateCriterionAuditRecord] = Field(default_factory=list)
    criterion_review_complete: bool = True
    required_changes: list[str] = Field(default_factory=list)
    blocker_findings: list[str] = Field(default_factory=list)
    hallucination_findings: list[str] = Field(default_factory=list)
    # Set when the model claimed ``accept`` but the kernel downgraded it (a false accept was blocked).
    downgraded_from: GateDecision | None = None
    evidence_resolved: bool = True
    # Reviewer provenance — the independent-AI authority that produced this verdict.
    reviewer_provider_id: str = ""
    reviewer_model_id: str = ""
    reviewer_session_id: str = ""
    input_digest: str = ""
    output_digest: str = ""

    @property
    def is_accept(self) -> bool:
        return self.decision == GateDecision.ACCEPT


class PromotionReceipt(BaseModel):
    """A light record that an AI promotion BOUND its outcome to the artifact — not the maximal review.

    Emitted by every ``promote_*_to_ai_reviewed`` on success. It captures exactly what makes the
    promotion trustworthy: the candidate it is about, the reviewer's output turn it rests on, the gate
    it had to pass, that ``accept`` was structurally earned, and how the reviewer ran. It is enough to
    audit + to gate product-serious loads (``assert_product_grade_promotion``); it is NOT the reviewer's
    full transcript/record.
    """

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str
    candidate_digest: str
    expected_gate_name: str
    review_record_digest: str
    earned_accept: bool
    reviewer_provider_id: str
    reviewer_execution_kind: ReviewerExecutionKind
    promoted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GateLoopResult(BaseModel):
    """Result of a bounded revise-loop: the final earned outcome + whether the budget was exhausted."""

    model_config = ConfigDict(extra="forbid")

    final_outcome: GateOutcome
    rounds_used: int = Field(ge=0)
    budget_exhausted: bool = False
