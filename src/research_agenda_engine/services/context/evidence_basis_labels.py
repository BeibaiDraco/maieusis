"""Canonical, cause-neutral honesty wording for the ``evidence_basis`` label (live-readiness).

R2 (cause-neutral): the system often does NOT know WHY full text is absent — it may not have been
attempted (demo / literature off), a fetch may have errored, or the source may be genuinely paywalled.
Never assert a specific cause on a user-facing surface. The enrichment ``StageReceipt`` carries the real
attempted / succeeded / failed-paywalled / failed-error breakdown; the honest surfaces point to it.

Single source of truth so every DP-2 surface reads consistently and stays cause-neutral.
"""

from __future__ import annotations

from collections.abc import Sequence

from ...schemas.question_scientist_context_v2 import (
    EvidenceBasis,
    OpenGapCard,
    ReviewedTopicClaimCard,
)
from ...schemas.scientific_context import TopicEvidenceClaimStatus

# The one cause-neutral phrase — never "paywalled", never a cause the system did not verify.
ABSTRACT_ONLY_PHRASE = "full text was not available to this system"

# The things the old vetoes covered: open gaps + STRONG claims (established/contested).
_STRONG_CLAIM_STATUSES = {
    TopicEvidenceClaimStatus.ESTABLISHED,
    TopicEvidenceClaimStatus.CONTESTED,
}


def abstract_only_gap_and_strong_claim_counts(
    open_gap_cards: Sequence[OpenGapCard],
    claim_cards: Sequence[ReviewedTopicClaimCard],
) -> tuple[int, int]:
    """(abstract_only, total) over open gaps + strong claims — the single count both surface 2 + 3 use."""
    items: list[OpenGapCard | ReviewedTopicClaimCard] = [
        *open_gap_cards,
        *(card for card in claim_cards if card.status in _STRONG_CLAIM_STATUSES),
    ]
    abstract_only = sum(1 for item in items if item.evidence_basis == EvidenceBasis.ABSTRACT_ONLY)
    return abstract_only, len(items)


def topic_evidence_basis_banner(abstract_only_count: int, total: int) -> str:
    """Header banner for ``topic_evidence_summary.md`` (surface 3). Empty when nothing is abstract-only."""
    if abstract_only_count <= 0:
        return ""
    return (
        f"> ⚠️ Evidence basis: {abstract_only_count} of {total} open gaps / strong claims rest on "
        f"ABSTRACT-ONLY literature ({ABSTRACT_ONLY_PHRASE}). These are literature-motivated, NOT "
        "fulltext-verified — see the fulltext-enrichment receipt for the per-route fetch breakdown."
    )


def family_evidence_basis_line(basis: EvidenceBasis) -> str:
    """Per-family basis line for ``question_families.md`` (surface 4)."""
    if basis == EvidenceBasis.ABSTRACT_ONLY:
        return (
            "- Evidence basis: **abstract-only** — this family's supporting literature is not "
            f"fulltext-verified ({ABSTRACT_ONLY_PHRASE})."
        )
    return "- Evidence basis: fulltext-backed."


def shortlist_evidence_basis_tag(basis: EvidenceBasis) -> str:
    """Inline tag appended to a shortlisted family line in ``shortlist.md`` (surface 5)."""
    return " (abstract-only basis)" if basis == EvidenceBasis.ABSTRACT_ONLY else ""


def dossier_evidence_basis_banner() -> str:
    """Top-of-dossier banner (surface 6), prepended by the driver exactly like the F1 banner."""
    return (
        "> ⚠️ Data basis: this family's open gap / key claims rest on ABSTRACT-ONLY literature "
        f"({ABSTRACT_ONLY_PHRASE}). The questions are literature-motivated but NOT fulltext-verified; "
        "a domain expert should confirm against primary sources.\n\n"
    )


def summary_evidence_basis_line(abstract_only_families: int, total_planning_families: int) -> str:
    """Aggregate line over families that reached planning, not final accepted dossiers."""
    if abstract_only_families <= 0:
        return ""
    return (
        f"Evidence basis: {abstract_only_families} of {total_planning_families} families that "
        "reached planning rest on abstract-only literature (see each dossier's Data basis banner)."
    )


def provenance_evidence_basis_note(abstract_only_count: int, total: int) -> str:
    """Cause-neutral, ID-free note for ``ContextProvenanceSummary.notes`` (surface 2 — the QS sees this)."""
    if abstract_only_count <= 0:
        return ""
    return (
        f"Evidence basis: {abstract_only_count} of {total} open gaps / strong claims rest on "
        f"abstract-only literature ({ABSTRACT_ONLY_PHRASE}); treat as literature-motivated, not "
        "fulltext-verified."
    )
