"""Clean human-readable PatternBank summary — diagnostic, NOT a review-pack.

Answers what patterns were induced + accepted, which authority, and how to adjust. Not an approval
surface; never asserts novelty. This module carries no dataset-specific names; it is enforced by the
dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Sequence

from ...schemas.question_pattern import QuestionPatternCard


def render_patternbank_summary(patterns: Sequence[QuestionPatternCard]) -> str:
    """PatternBank summary: the accepted question-forming moves + their authority + sources."""
    lines = [
        "# PatternBank — automated review summary",
        "",
        f"- Reviewed question patterns: {len(patterns)}",
        "",
        "## Patterns (reusable question-forming moves)",
        "",
    ]
    for pattern in patterns:
        lines.append(
            f"- **{pattern.pattern_name}** — `{pattern.review_status.value}`, "
            f"{pattern.transfer_scope.value}, from {len(set(pattern.source_case_ids))} source paper(s)"
        )
        if pattern.question_formation_move:
            lines.append(f"  - move: {pattern.question_formation_move}")
    if not patterns:
        lines.append("- _(no reviewed patterns; the run stops before question generation)_")
    lines.extend(
        [
            "",
            "## If this looks wrong",
            "",
            "This is a diagnostic summary, not an approval. Adjust the PaperBank inputs and re-run; "
            "patterns are re-induced and re-reviewed from the accepted formation traces.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
