"""Human-readable summary of the narrator's fused ``DatasetNarrative``.

The GF-2c narrator produced no renderer — only in-memory objects. This is the clean, Questioner's-view
*summary* (D3-style: not a review-pack) that doubles as transparency and a Phase-4 optional-override
surface: if the auto-generated narrative looks wrong, a human reads this to see what the Questioner
will be told about the dataset, and how it was gated.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from ...schemas.dataset_narrative import DatasetNarrative
from .narrator import NarratorResult


def render_dataset_narrative_summary(narrative: DatasetNarrative) -> str:
    """Render a coarse, proposal-stage DatasetNarrative as a clean human-readable Markdown summary."""
    lines: list[str] = [
        f"# Dataset Narrative — {narrative.title}",
        "",
        f"- Dataset: `{narrative.dataset_id}`",
        f"- Review status: `{narrative.review_status.value}`",
        "",
        "## Scientific purpose",
        "",
        narrative.scientific_purpose or "_(not stated)_",
        "",
    ]
    _section(lines, "Population", narrative.population)
    _section(lines, "Task / design", narrative.task_or_design)
    _section(lines, "Recording modalities", "; ".join(narrative.modalities))
    _section(lines, "Broad scale", narrative.broad_scale)
    _section(lines, "Anatomical / spatial coverage", narrative.spatial_or_anatomical_coverage)
    _section(lines, "Temporal / trial structure", narrative.temporal_structure)
    _section(lines, "Standardization", narrative.standardization)
    _bullets(lines, "Major variables", narrative.major_variables)
    _bullets(lines, "Reuse opportunities", narrative.reuse_opportunities)
    _bullets(lines, "Known high-level limitations", narrative.known_high_level_limitations)
    if narrative.scale_facts:
        lines.extend(["## Coarse scale facts", ""])
        lines.extend(f"- {fact.quantity_kind}: {fact.value_text}" for fact in narrative.scale_facts)
        lines.append("")
    lines.extend(["## Provenance", ""])
    lines.append(f"- Fusion prompt marker: `{narrative.prompt_version}`")
    lines.append(f"- Generator provider(s): `{narrative.provider_id or '(none)'}`")
    lines.append(f"- Source feeds fused: {len(narrative.source_refs)}")
    if narrative.review_notes:
        lines.extend(["", "## Review authority", "", narrative.review_notes])
    return "\n".join(lines).rstrip() + "\n"


def render_narrator_result_summary(result: NarratorResult) -> str:
    """Render the fused candidate + which sources fed it + the fidelity verdict (pre-persistence view)."""
    narrative = result.candidate
    lines = [render_dataset_narrative_summary(narrative).rstrip(), "", "## Narrator run", ""]
    lines.append(f"- Sources fused: {', '.join(sorted(kind.value for kind in result.sources))}")
    if result.skipped:
        lines.append(f"- Skipped sources: {result.skipped}")
    if result.review is not None:
        lines.append(f"- Independent fidelity gate: **{result.review.decision.value}**")
        if result.review.rationale:
            lines.append(f"- Rationale: {result.review.rationale}")
    else:
        lines.append("- Independent fidelity gate: not run (narrative is not proposal-ready)")
    return "\n".join(lines).rstrip() + "\n"


def _section(lines: list[str], heading: str, text: str) -> None:
    if text.strip():
        lines.extend([f"## {heading}", "", text.strip(), ""])


def _bullets(lines: list[str], heading: str, items: list[str]) -> None:
    values = [item.strip() for item in items if item.strip()]
    if values:
        lines.extend([f"## {heading}", ""])
        lines.extend(f"- {value}" for value in values)
        lines.append("")
