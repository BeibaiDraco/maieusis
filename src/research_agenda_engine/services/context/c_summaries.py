"""C summaries — DatasetNarrative human-view (with sample-boundary honesty),
QuestionFamily human-view, and the shortlist. Clean diagnostic summaries, never "approved/serious/novel".

Sample-boundary honesty (item 4): the DatasetNarrative human-view states the sample's limits so the
dossier's "data basis & limitations" can surface them — the sample only proves what is IN the sample;
absence-in-sample is NOT absence-in-dataset; no joint-coverage is proven; and a gap the sample cannot
see is ``insufficient_sample_evidence``, never a false dataset mismatch.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Sequence

from ...schemas.dataset_narrative import DatasetNarrative
from ...schemas.question_family import QuestionFamily
from ...schemas.question_scientist_context_v2 import EvidenceBasis
from ...schemas.shortlist_outcome import FamilyInclusionLabel, FamilyShortlistOutcome
from ..narrative_sources.narrative_render import render_dataset_narrative_summary
from .evidence_basis_labels import family_evidence_basis_line, shortlist_evidence_basis_tag

SAMPLE_BOUNDARY_HONESTY = (
    "The local sample proves only what is present IN the sample. Absence of a feature in the sample is "
    "NOT absence in the full dataset; no joint-coverage across variables is proven; and a property the "
    "sample cannot resolve is recorded as insufficient_sample_evidence, never as a dataset mismatch."
)


def render_dataset_narrative_human_view(narrative: DatasetNarrative) -> str:
    """DatasetNarrative human-view = the 5a-0 summary + an explicit data-basis & limitations section."""
    base = render_dataset_narrative_summary(narrative).rstrip()
    lines = [
        base,
        "",
        "## Data basis & limitations",
        "",
        SAMPLE_BOUNDARY_HONESTY,
    ]
    if narrative.known_high_level_limitations:
        lines.extend(f"- {limit}" for limit in narrative.known_high_level_limitations)
    return "\n".join(lines).rstrip() + "\n"


def render_question_family_human_view(
    family: QuestionFamily, *, evidence_basis: EvidenceBasis | None = None
) -> str:
    """QuestionFamily human-view — the shared tension + its distinct variants (diagnostic).

    ``evidence_basis`` (DP-2 surface 4): the family's worst-case literature basis, surfaced honestly.
    """
    lines = [
        f"# Question family — {family.title}",
        "",
        f"- Shared scientific tension: {family.shared_scientific_tension}",
        f"- Summary: {family.summary}",
    ]
    if evidence_basis is not None:
        lines.append(family_evidence_basis_line(evidence_basis))
    lines.extend(["", "## Variants", ""])
    for variant in family.variants:
        lines.append(f"- **{variant.variant_role}** — {variant.seed.question}")
        lines.append(f"  - distinct from siblings: {variant.distinct_from_siblings}")
    lines.extend(
        [
            "",
            "## If this looks wrong",
            "",
            "This is a diagnostic summary, not an approval, and it does not claim any question is novel. "
            "Adjust the ResearchIntent or inputs and re-run.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_shortlist_summary(
    outcomes: Sequence[FamilyShortlistOutcome],
    *,
    basis_by_family: dict[str, EvidenceBasis] | None = None,
) -> str:
    """Shortlist summary covering ALL outcomes with honest, non-approval labels.

    ``basis_by_family`` (DP-2 surface 5): tags each included family with its literature basis honestly.
    """
    basis_by_family = basis_by_family or {}
    included = [o for o in outcomes if o.label == FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW]
    lines = [
        "# Shortlist (automated review)",
        "",
        (
            "- Shortlisted by automated worthiness review: "
            f"{len(included)} of {len(outcomes)} families"
        ),
        "",
        (
            "## Shortlisted families (passed automated worthiness review — suggested reading, "
            "not accepted planning dossiers)"
        ),
        "",
    ]
    lines.extend(
        f"- {o.question_family_id} — {len(o.active_variant_ids)} active variant(s)"
        + (
            "; bounded prior-art review found no direct recap in its recorded search scope "
            "as of its recorded search cutoff (no claim of novelty beyond that scope)"
            if o.novelty_admission_id
            else "; prior-art admission was not run"
        )
        + (
            shortlist_evidence_basis_tag(basis_by_family[o.question_family_id])
            if o.question_family_id in basis_by_family
            else ""
        )
        for o in included
    )
    if not included:
        lines.append("- _(none shortlisted)_")
    lines.extend(["", "## Not included (honestly listed)", ""])
    lines.extend(
        f"- {o.question_family_id} — `{o.label.value}`: {o.rationale}"
        for o in outcomes
        if o.label != FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW
    )
    if all(o.label == FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW for o in outcomes):
        lines.append("- _(none)_")
    lines.extend(
        [
            "",
            "## Note",
            "",
            "These labels are honest outcomes, not planning acceptances. `run_incomplete` is an infrastructure "
            "failure, not a scientific rejection. No question here is claimed to be novel. A "
            "bounded prior-art review is not a global priority or novelty certification.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
