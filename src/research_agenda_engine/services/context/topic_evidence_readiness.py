"""Shared deterministic topic-evidence readiness check.

A single function, called by BOTH the topic-evidence gate (as its host-side ``evidence_resolved``
pre-check) AND the V2 compiler (before it builds the TopicLiteratureContextPack). Sharing it is
what makes "an accepted brief always compiles" a real guarantee (not two copies that can drift): the
gate cannot earn-accept a brief that the compiler would then reject on a missing close-prior/open-gap
or an unresolved claim source.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from ...schemas.scientific_context import TopicEvidenceBrief, TopicEvidenceClaimStatus


def evaluate_topic_evidence_readiness(
    brief: TopicEvidenceBrief,
    *,
    source_record_ids: set[str],
    claim_supporting_record_ids: set[str],
) -> tuple[bool, list[str]]:
    """Return (ready, issues). The compile-critical checks the gate and the compiler both require.

    ``source_record_ids`` = every record id present in the source table; ``claim_supporting_record_ids``
    = the subset that may support a scientific claim (not title-only / metadata-only). Both are computed
    once by the caller from the source table and passed in, so this stays dependency-light.
    """
    issues: list[str] = []
    close_prior = [c for c in brief.claims if c.status == TopicEvidenceClaimStatus.ALREADY_ANSWERED]
    open_gap = [c for c in brief.claims if c.status == TopicEvidenceClaimStatus.OPEN_QUESTION]
    if not close_prior:
        issues.append("no close-prior/already-answered claim")
    if not open_gap:
        issues.append("no open-gap/open-question claim")
    for claim in brief.claims:
        for source_id in claim.source_record_ids:
            if source_id not in source_record_ids:
                issues.append(f"claim {claim.claim_id} cites unknown source {source_id}")
            elif source_id not in claim_supporting_record_ids:
                issues.append(
                    f"claim {claim.claim_id} cites a non-claim-supporting source {source_id}"
                )
    return (not issues, issues)
