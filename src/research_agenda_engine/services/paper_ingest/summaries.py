"""Clean human-readable PaperBank summaries — diagnostic, NOT review-packs.

Each summary answers: what the system saw, what the automated gate judged, which sources it used, the
uncertainties, what the next stage used, and which input to adjust if unsatisfied. It is NOT a human
approval surface and never asserts a question is "novel". Machine ids / session ids / review-pack
fields stay in the audit artifacts, not here.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from ...schemas.paper_case import PaperCase
from .paperbank_gate import PaperBankGateResult


def _optional_section(title: str, entries: list[str]) -> list[str]:
    """A summary section rendered ONLY when it has content — absent fields are omitted cleanly."""
    if not any(entry for entry in entries):
        return []
    return [f"## {title}", "", *entries, ""]


def _contrast_entries(paper_case: PaperCase) -> list[str]:
    q = paper_case.scientific_question
    entries: list[str] = []
    if q.central_contrast:
        entries.append(q.central_contrast)
    if q.competing_explanations:
        if entries:
            entries.append("")
        entries.append("Competing explanations the paper weighed:")
        entries.extend(f"- {item}" for item in q.competing_explanations)
    if q.discriminating_observation:
        if entries:
            entries.append("")
        entries.append(f"What would tell them apart: {q.discriminating_observation}")
    return entries


def _background_entries(paper_case: PaperCase) -> list[str]:
    trace_claims = (
        paper_case.formation_trace.background_claims if paper_case.formation_trace else []
    )
    claims = [*paper_case.knowledge_state.motivating_claims, *trace_claims]
    return [f"- {claim}" for claim in claims if claim]


def _significance_entries(paper_case: PaperCase) -> list[str]:
    entries: list[str] = []
    if paper_case.formation_trace and paper_case.formation_trace.scientific_significance:
        entries.append(paper_case.formation_trace.scientific_significance)
    if paper_case.question_design.why_question_was_valuable:
        if entries:
            entries.append("")
        entries.append(paper_case.question_design.why_question_was_valuable)
    return entries


def render_paper_case_summary(paper_case: PaperCase) -> str:
    """Per-paper summary: what was extracted + how the automated gate judged it."""
    q = paper_case.scientific_question
    dataset = paper_case.dataset_description
    dataset_details: list[str] = []
    if dataset.population:
        dataset_details.append(f"- Population: {dataset.population}")
    if dataset.measurements:
        dataset_details.append(f"- Measurements: {', '.join(dataset.measurements)}")
    lines = [
        f"# Paper — {paper_case.citation or paper_case.paper_case_id}",
        "",
        f"- Review authority: `{paper_case.review.status.value}` (automated unless expert)",
        "",
        "## Question the system extracted",
        "",
        q.original_question or "_(not extracted)_",
        "",
        *_optional_section("The scientific contrast", _contrast_entries(paper_case)),
        *_optional_section("Background and motivation", _background_entries(paper_case)),
        *_optional_section("Why this question mattered", _significance_entries(paper_case)),
        "## What the dataset offered (as the paper used it)",
        "",
        dataset.task_or_design or dataset.dataset_name or "_(no dataset cue recorded)_",
        *(["", *dataset_details] if dataset_details else []),
        "",
        "## Key citations used in forming the question",
        "",
        *(f"- `{cwid}`" for cwid in paper_case.key_cited_work_ids),
    ]
    if not paper_case.key_cited_work_ids:
        lines.append("- _(none recorded)_")
    if paper_case.evidence_requests:
        lines.extend(
            [
                "",
                "## Open uncertainties (unmet evidence)",
                "",
                *(f"- {r}" for r in paper_case.evidence_requests),
            ]
        )
    lines.extend(
        [
            "",
            "## If this looks wrong",
            "",
            "Adjust the source PDF or its parse, then re-run — the gate re-judges from the paper.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_paperbank_overall_summary(result: PaperBankGateResult) -> str:
    """PaperBank-overall summary: the accepted set + honestly-listed exclusions + batch outcome."""
    lines = [
        "# PaperBank — automated review summary",
        "",
        f"- Batch outcome: `{result.batch_outcome.value}`",
        f"- Accepted (automated review passed): {len(result.accepted)}",
        f"- Excluded: {len(result.excluded)}",
        "",
        "## Accepted papers",
        "",
    ]
    lines.extend(
        f"- {a.paper_case.citation or a.paper_id} — `{a.paper_case.review.status.value}`"
        for a in result.accepted
    )
    if not result.accepted:
        lines.append(
            "- _(none — the batch produced no usable papers; downstream stages did not run)_"
        )
    lines.extend(["", "## Excluded papers (honestly listed)", ""])
    lines.extend(
        f"- {e.paper_id} — {e.reason}"
        + (f" (canonical: {e.canonical_paper_id})" if e.canonical_paper_id else "")
        + (f" — {e.detail}" if e.detail else "")
        for e in result.excluded
    )
    if not result.excluded:
        lines.append("- _(none)_")
    lines.extend(
        [
            "",
            "## If this looks wrong",
            "",
            "This is a diagnostic summary, not an approval. Add/replace PDFs or fix a parse and re-run; "
            "the automated gate re-judges each paper independently.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
