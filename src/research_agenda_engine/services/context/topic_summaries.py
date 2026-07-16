"""Clean human-readable topic summaries — diagnostic, NOT review-packs.

``research_scope.md`` is rendered by ``research_scope.render_research_scope_summary``; here are the
retrieval + topic-evidence summaries. Each answers: what the system retrieved/judged, which sources,
the uncertainties, and which input to adjust — never an approval surface, never asserts novelty.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from ...schemas.scientific_context import TopicEvidenceBrief, TopicEvidenceClaimStatus


def render_retrieval_summary(
    *, topic_terms: list[str], lane_coverage: dict[str, int], source_count: int
) -> str:
    """Diagnostic summary of what literature retrieval found (lanes, source counts)."""
    lines = [
        "# Literature retrieval",
        "",
        f"- Query terms: {', '.join(topic_terms) or '(none)'}",
        f"- Sources retrieved: {source_count}",
        "",
        "## Lane coverage",
        "",
        *(f"- {lane}: {count} source(s)" for lane, count in sorted(lane_coverage.items())),
    ]
    thin = [lane for lane, count in lane_coverage.items() if count == 0]
    if thin:
        lines.extend(["", "## Thin lanes (no sources found)", "", *(f"- {lane}" for lane in thin)])
    lines.extend(
        [
            "",
            "## If this looks wrong",
            "",
            "Adjust the ResearchIntent (topic / seed question) or add a lit-search provider, then re-run.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_topic_evidence_summary(
    brief: TopicEvidenceBrief, *, evidence_basis_banner: str = ""
) -> str:
    """Diagnostic summary of the reviewed TopicEvidenceBrief (scope, close-priors, open gaps).

    ``evidence_basis_banner`` (DP-2 surface 3): an honest, cause-neutral header when any open gap / strong
    claim rests on abstract-only literature — surfaced loudly, never a veto.
    """
    close_prior = [c for c in brief.claims if c.status == TopicEvidenceClaimStatus.ALREADY_ANSWERED]
    open_gap = [c for c in brief.claims if c.status == TopicEvidenceClaimStatus.OPEN_QUESTION]
    lines = ["# Topic evidence", ""]
    if evidence_basis_banner:
        lines.extend([evidence_basis_banner, ""])
    lines.extend(
        [
            f"- Review authority: `{brief.review_status.value}` (automated unless expert)",
            f"- Scope: {brief.canonical_scope}",
            "",
            "## Close priors (already answered — avoid redundant questions)",
            "",
            *(f"- {c.claim}" for c in close_prior),
        ]
    )
    if not close_prior:
        lines.append("- _(none recorded)_")
    lines.extend(["", "## Open gaps (still open — NOT a novelty claim)", ""])
    lines.extend(f"- {c.claim}" for c in open_gap)
    if not open_gap:
        lines.append("- _(none recorded)_")
    if brief.unresolved_tensions:
        lines.extend(
            ["", "## Unresolved tensions", "", *(f"- {t}" for t in brief.unresolved_tensions)]
        )
    lines.extend(
        [
            "",
            "## If this looks wrong",
            "",
            "This is a diagnostic summary, not an approval, and it does not claim any question is novel. "
            "Adjust the ResearchIntent or sources and re-run.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
