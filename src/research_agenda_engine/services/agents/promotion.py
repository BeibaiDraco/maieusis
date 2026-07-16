"""Promotion binding + receipt + product-grade gate.

A ``promote_*_to_ai_reviewed`` grants proposal authority; that trust boundary must not rest on
``decision == ACCEPT`` alone. ``assert_promotion_binding`` re-checks, fail-closed, that the outcome is
about THIS artifact and was earned by an independent reviewer:

  (a) ``outcome.gate_name`` is the gate this artifact type must have passed;
  (b) ``outcome.candidate_digest`` equals ``stable_hash(candidate)`` — the verdict is about this exact
      artifact, not a different one;
  (c) the reviewer is attributable AND its FAMILY is independent of a NON-EMPTY generator set;
  (d) the decision is a structurally-earned ``accept``.

``build_promotion_receipt`` runs that binding and returns a light ``PromotionReceipt``.
``assert_product_grade_promotion`` is the SEPARATE product-serious gate: it refuses a ``MOCK`` receipt.
Execution kind is recorded, never blocked at promotion — a mock promotion is fine for demo/tests, but a
``MOCK`` receipt can never pass the product-grade gate, so a mock-reviewed artifact is never a
product-serious ``AI_REVIEWED``.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from pydantic import BaseModel

from ...provenance import stable_hash
from ...schemas.gate_outcome import (
    GateDecision,
    GateOutcome,
    PromotionReceipt,
    ReviewerExecutionKind,
)
from .reviewer_base import assert_reviewer_provider_independent


def assert_promotion_binding(
    *, candidate: BaseModel, outcome: GateOutcome, expected_gate: str
) -> None:
    """Fail closed unless ``outcome`` is an earned, independent accept about THIS ``candidate``."""
    if outcome.gate_name != expected_gate:
        raise ValueError(
            f"cannot promote: outcome gate {outcome.gate_name!r} is not the expected "
            f"{expected_gate!r} gate — fail closed"
        )
    expected_digest = stable_hash(candidate)
    if outcome.candidate_digest != expected_digest:
        raise ValueError(
            "cannot promote: outcome candidate_digest does not match this artifact — the verdict is "
            "about a different candidate — fail closed"
        )
    if not [pid for pid in outcome.generator_provider_ids if pid]:
        raise ValueError(
            "cannot promote: outcome carries no generator identity to attest independence against — "
            "fail closed"
        )
    if not outcome.reviewer_provider_id.strip():
        raise ValueError("cannot promote: outcome carries no reviewer identity — fail closed")
    # Re-assert independence at the promotion trust boundary (family-normalized) — never rely on an
    # upstream invariant to grant proposal authority.
    assert_reviewer_provider_independent(
        outcome.reviewer_provider_id,
        outcome.generator_provider_ids,
        role_label=f"{expected_gate} promoter",
    )
    if outcome.decision != GateDecision.ACCEPT:
        raise ValueError(
            f"cannot promote: {expected_gate} gate returned {outcome.decision.value!r}, "
            "not accept — fail closed"
        )
    if not outcome.criterion_review_complete:
        raise ValueError(
            f"cannot promote: {expected_gate} criterion review is incomplete — fail closed"
        )


def build_promotion_receipt(
    *, candidate: BaseModel, outcome: GateOutcome, artifact_kind: str, expected_gate: str
) -> PromotionReceipt:
    """Bind (fail-closed) then emit the light promotion receipt."""
    assert_promotion_binding(candidate=candidate, outcome=outcome, expected_gate=expected_gate)
    return PromotionReceipt(
        artifact_kind=artifact_kind,
        candidate_digest=outcome.candidate_digest,
        expected_gate_name=expected_gate,
        review_record_digest=outcome.output_digest,
        earned_accept=True,
        reviewer_provider_id=outcome.reviewer_provider_id,
        reviewer_execution_kind=outcome.reviewer_execution_kind,
    )


def assert_product_grade_promotion(receipt: PromotionReceipt) -> None:
    """The product-serious gate: a mock-reviewed promotion is not product-grade authority.

    The promoter itself allows a mock reviewer (demo/tests). This gate — called on the STANDARD product
    load path — refuses anything but a LIVE_API receipt, so a mock promotion never becomes serious.
    """
    if receipt.reviewer_execution_kind != ReviewerExecutionKind.LIVE_API:
        raise ValueError(
            "product-serious promotion requires a LIVE_API reviewer; receipt is "
            f"{receipt.reviewer_execution_kind.value!r} (a mock/demo promotion is not product-grade)"
        )
