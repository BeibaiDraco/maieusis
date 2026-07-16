"""Fixed ``runs/<id>/`` public artifact layout.

The `maieusis run` driver produces a single deterministic tree per run (locked in
``docs/plans/2026-07-09-phase5-e2e-execution-plan.md``). This module owns the paths, the
dataset-agnostic family slug, and the thin render→write glue over the 5a summary renderers — so the
driver just hands it the stage artifacts. It writes files; it holds no run logic.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import os
import re
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ...io import dump_data, load_model
from ...schemas.dataset_narrative import DatasetNarrative
from ...schemas.family_failure import sanitize_family_failure_text
from ...schemas.front_half_authority import FrontHalfAuthorityCeiling
from ...schemas.inferred_research_scope import ResolvedResearchScope
from ...schemas.paper_case import PaperCase
from ...schemas.question_family import QuestionFamily
from ...schemas.question_pattern import QuestionFormationTrace, QuestionPatternCard
from ...schemas.question_scientist_context_v2 import EvidenceBasis
from ...schemas.research_intent import ResearchIntent
from ...schemas.run_outcome import DossierAxis, FamilyRunOutcome, RunTerminal
from ...schemas.scientific_context import TopicEvidenceBrief
from ...schemas.shortlist_outcome import FamilyInclusionLabel, FamilyShortlistOutcome
from ...schemas.stage_receipt import FailureClass, StageReceipt
from ..context.c_summaries import (
    render_dataset_narrative_human_view,
    render_question_family_human_view,
    render_shortlist_summary,
)
from ..context.research_scope import render_research_scope_summary
from ..context.topic_summaries import render_retrieval_summary, render_topic_evidence_summary
from ..dossier.multi_family_coordinator import validate_aggregate_report_text
from ..dossier.public_text_guard import find_public_markdown_jargon
from ..paper_ingest.summaries import (
    render_paper_case_summary,
    render_paperbank_overall_summary,
)
from ..paper_patterns.summaries import render_patternbank_summary

_SLUG_RE = re.compile(r"[^a-z0-9]+")

_PROVISIONAL_FRONT_HALF_BANNER = (
    "> **PROVISIONAL.** This source-bound inspiration has not earned verified authority."
)


def family_slug(identifier: str) -> str:
    """Dataset-agnostic slug: lowercase ASCII, non-alphanumerics collapsed to ``-``. No dataset tokens."""
    slug = _SLUG_RE.sub("-", identifier.strip().lower()).strip("-")
    return slug or "family"


def assign_family_slugs(identifiers: Iterable[str]) -> dict[str, str]:
    """Assign a UNIQUE directory slug per family id (deterministic collision suffix ``-2``, ``-3`` …)."""
    slugs: dict[str, str] = {}
    used: dict[str, int] = {}
    for identifier in identifiers:
        base = family_slug(identifier)
        count = used.get(base, 0) + 1
        used[base] = count
        slugs[identifier] = base if count == 1 else f"{base}-{count}"
    return slugs


@dataclass(frozen=True)
class RunPaths:
    """The fixed ``runs/<id>/`` tree. ``root`` is ``output_root/run_id``."""

    root: Path

    @property
    def summary(self) -> Path:
        return self.root / "summary.md"

    @property
    def readme(self) -> Path:
        return self.root / "README.md"

    @property
    def run_manifest(self) -> Path:
        return self.root / "run_manifest.yaml"

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    def paper_artifact_dir(self, slug: str) -> Path:
        return self.artifacts / "papers" / slug

    def paper_case_artifact(self, slug: str) -> Path:
        return self.paper_artifact_dir(slug) / "paper_case.yaml"

    def formation_trace_artifact(self, slug: str) -> Path:
        return self.paper_artifact_dir(slug) / "formation_trace.yaml"

    def formation_trace_view(self, slug: str) -> Path:
        return self.root / "paperbank" / "formation_traces" / f"{slug}.md"

    @property
    def pattern_artifacts(self) -> Path:
        return self.artifacts / "patterns"

    def question_pattern_artifact(self, pattern_id: str) -> Path:
        return self.pattern_artifacts / f"{family_slug(pattern_id)}.question_pattern.yaml"

    @property
    def pattern_bank_artifact(self) -> Path:
        return self.pattern_artifacts / "question_pattern_manifest.yaml"

    @property
    def pattern_insufficiency(self) -> Path:
        return self.pattern_artifacts / "insufficiency.md"

    @property
    def question_family_batch_artifact(self) -> Path:
        return self.artifacts / "question_family_batch.yaml"

    @property
    def shortlist_artifact(self) -> Path:
        return self.artifacts / "question_family_shortlist.yaml"

    @property
    def ingest_manifest_artifact(self) -> Path:
        return self.artifacts / "paper_ingest_manifest.yaml"

    @property
    def resolved_inputs(self) -> Path:
        return self.root / "inputs" / "resolved_inputs.md"

    @property
    def corpus(self) -> Path:
        return self.root / "corpus"

    @property
    def receipts(self) -> Path:
        return self.root / "receipts"

    @property
    def stage_outputs(self) -> Path:
        """Small typed per-stage output summaries (rehydrated by the 5c-1c resume path)."""
        return self.root / "stage_outputs"

    def stage_output(self, stage_name: str) -> Path:
        return self.stage_outputs / f"{family_slug(stage_name)}.yaml"

    @property
    def run_lock(self) -> Path:
        """The OS-level exclusive run lock (5c-1c DP-5); excluded from receipts/corruption checks."""
        return self.root / ".maieusis-lock"

    def family_completion(self, slug: str) -> Path:
        """The per-family durable completion record the resume planner discovers (5c-1c DP-4)."""
        return self.family_dir(slug) / "family_completion.yaml"

    def resume_receipt(self, index: int) -> Path:
        return self.receipts / f"resume-{index}.yaml"

    def paper_case(self, slug: str) -> Path:
        return self.root / "paperbank" / "papers" / f"{slug}.md"

    @property
    def paperbank_summary(self) -> Path:
        return self.root / "paperbank" / "paperbank_summary.md"

    @property
    def question_patterns(self) -> Path:
        return self.root / "paperbank" / "question_patterns.md"

    @property
    def question_patterns_detailed(self) -> Path:
        return self.root / "paperbank" / "question_patterns_detailed.md"

    @property
    def research_scope(self) -> Path:
        return self.root / "literature" / "research_scope.md"

    @property
    def retrieval_summary(self) -> Path:
        return self.root / "literature" / "retrieval_summary.md"

    @property
    def topic_evidence_summary(self) -> Path:
        return self.root / "literature" / "topic_evidence_summary.md"

    @property
    def dataset_narrative(self) -> Path:
        return self.root / "dataset" / "dataset_narrative.md"

    @property
    def question_families(self) -> Path:
        return self.root / "questions" / "question_families.md"

    @property
    def question_families_detailed(self) -> Path:
        return self.root / "questions" / "question_families_detailed.md"

    @property
    def shortlist(self) -> Path:
        return self.root / "questions" / "shortlist.md"

    def family_dir(self, slug: str) -> Path:
        return self.root / "families" / slug

    def family_dossier(self, slug: str) -> Path:
        return self.family_dir(slug) / "dossier.md"

    def family_dossier_detailed(self, slug: str) -> Path:
        return self.family_dir(slug) / "dossier_detailed.md"

    @property
    def presentation_receipt(self) -> Path:
        return self.root / "presentation" / "presentation_addon_receipt.yaml"

    def family_artifacts(self, slug: str) -> Path:
        return self.family_dir(slug) / "artifacts"


def _write(path: Path, text: str) -> Path:
    """Validate-complete text is promoted atomically; current bytes stay visible on write failure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (text if text.endswith("\n") else text + "\n").encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        Path(tmp_name).unlink(missing_ok=True)
    return path


def write_stage_receipt(paths: RunPaths, receipt: StageReceipt) -> Path:
    """Persist a stage boundary's ``StageReceipt`` to ``runs/<id>/receipts/<stage>.yaml`` (provenance)."""
    return dump_data(receipt, paths.receipts / f"{family_slug(receipt.stage_name)}.yaml")


def read_stage_receipts(paths: RunPaths) -> list[StageReceipt]:
    """Load every persisted stage receipt (sorted by file name).

    Skips ``resume-*.yaml`` (those are ``ResumeReceipt`` decision records, a different schema). Since
    5c-1c these receipts feed the digest-verified resume read path — the reuse predicate recomputes
    every input digest from the real inputs, so a hand-edited receipt can never skip payment.
    """
    if not paths.receipts.exists():
        return []
    return [
        load_model(path, StageReceipt)
        for path in sorted(paths.receipts.glob("*.yaml"))
        if not path.name.startswith("resume-")
    ]


def read_stage_receipt(paths: RunPaths, stage_name: str) -> StageReceipt | None:
    """Load one stage's receipt by stage name, or None when the stage has no receipt yet."""
    path = paths.receipts / f"{family_slug(stage_name)}.yaml"
    if not path.exists():
        return None
    return load_model(path, StageReceipt)


def render_resolved_inputs(config: object) -> str:
    """A clean, dataset-agnostic view of the resolved run inputs (the only NEW renderer in CP-A)."""
    dataset = getattr(config, "dataset", None)
    seed = getattr(dataset, "seed", None)
    models = getattr(config, "models", None)
    mode = getattr(getattr(config, "mode", None), "value", str(getattr(config, "mode", "")))
    lines = [
        "# Resolved run inputs",
        "",
        f"- Product mode: `{mode}`",
        f"- Dataset id: `{getattr(seed, 'dataset_id', '')}`",
        f"- Dataset link: {'set' if getattr(seed, 'link', '') else '(none)'}",
        f"- Owner provider: `{getattr(getattr(models, 'owner', None), 'provider', '')}`",
        f"- Reviewer provider: `{getattr(getattr(models, 'reviewer', None), 'provider', '')}`",
        f"- Coding host: `{getattr(getattr(models, 'coding_host', None), 'value', '')}`",
        "",
        "## If this looks wrong",
        "",
        "Edit `maieusis.yaml` (dataset link/sample, providers, research interest) and re-run.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_resolved_inputs(paths: RunPaths, config: object) -> Path:
    return _write(paths.resolved_inputs, render_resolved_inputs(config))


def write_paperbank(
    paths: RunPaths,
    *,
    paperbank_result: object,
    accepted_paper_cases: Sequence[PaperCase],
    patterns: Sequence[QuestionPatternCard],
) -> dict[str, Path]:
    written: dict[str, Path] = {}
    slugs = assign_family_slugs(case.paper_case_id for case in accepted_paper_cases)
    for case in accepted_paper_cases:
        written[case.paper_case_id] = write_paper_case_view(
            paths, paper_slug=slugs[case.paper_case_id], case=case
        )
    written["paperbank_summary"] = write_paperbank_summary(paths, paperbank_result)
    written["question_patterns"] = write_question_patterns(paths, patterns)
    return written


def write_paper_case_view(paths: RunPaths, *, paper_slug: str, case: PaperCase) -> Path:
    return _write(paths.paper_case(paper_slug), render_paper_case_summary(case))


def write_paperbank_summary(paths: RunPaths, paperbank_result: object) -> Path:
    return _write(
        paths.paperbank_summary,
        render_paperbank_overall_summary(paperbank_result),  # type: ignore[arg-type]
    )


def write_question_patterns(paths: RunPaths, patterns: Sequence[QuestionPatternCard]) -> Path:
    return _write(paths.question_patterns, render_patternbank_summary(patterns))


def render_formation_trace(trace: QuestionFormationTrace) -> str:
    lines = [
        "# Question-formation trace",
        "",
        f"- Review status: `{trace.review_status.value}`",
        "",
        "## Starting background",
        "",
        *[f"- {claim}" for claim in trace.background_claims],
        "",
        "## Unresolved gap",
        "",
        trace.unresolved_gap,
        "",
        "## Dataset opportunity",
        "",
        trace.dataset_feature_noticed,
        "",
        trace.opportunity_inference,
        "",
        "## Resulting question",
        "",
        trace.resulting_question,
        "",
        "## Scientific consequence",
        "",
        trace.expected_scientific_consequence,
        "",
        trace.scientific_significance,
        "",
    ]
    return "\n".join(lines)


def write_formation_trace(
    paths: RunPaths, *, paper_slug: str, trace: QuestionFormationTrace
) -> Path:
    return _write(paths.formation_trace_view(paper_slug), render_formation_trace(trace))


def write_literature_and_dataset(
    paths: RunPaths,
    *,
    intent: ResearchIntent,
    scope: ResolvedResearchScope | None,
    topic_terms: list[str],
    lane_coverage: dict[str, int],
    source_count: int,
    topic_brief: TopicEvidenceBrief,
    narrative: DatasetNarrative,
    evidence_basis_banner: str = "",
) -> dict[str, Path]:
    # F4: an open-mode run derived a scope → render it; otherwise render the explicit intent honestly,
    # never a fake/empty scope.
    return {
        "research_scope": write_research_scope_product(paths, intent=intent, scope=scope),
        "retrieval_summary": write_retrieval_summary(
            paths,
            topic_terms=topic_terms,
            lane_coverage=lane_coverage,
            source_count=source_count,
        ),
        "topic_evidence_summary": write_topic_evidence_summary(
            paths, topic_brief, evidence_basis_banner=evidence_basis_banner
        ),
        "dataset_narrative": write_dataset_narrative(paths, narrative),
    }


def write_research_scope(paths: RunPaths, text: str) -> Path:
    return _write(paths.research_scope, text)


def write_research_scope_product(
    paths: RunPaths, *, intent: ResearchIntent, scope: ResolvedResearchScope | None
) -> Path:
    text = (
        render_research_scope_summary(scope) if scope is not None else _render_intent_scope(intent)
    )
    return write_research_scope(paths, text)


def write_retrieval_summary(
    paths: RunPaths,
    *,
    topic_terms: list[str],
    lane_coverage: dict[str, int],
    source_count: int,
) -> Path:
    return _write(
        paths.retrieval_summary,
        render_retrieval_summary(
            topic_terms=topic_terms, lane_coverage=lane_coverage, source_count=source_count
        ),
    )


def write_topic_evidence_summary(
    paths: RunPaths, topic_brief: TopicEvidenceBrief, *, evidence_basis_banner: str = ""
) -> Path:
    return _write(
        paths.topic_evidence_summary,
        render_topic_evidence_summary(topic_brief, evidence_basis_banner=evidence_basis_banner),
    )


def write_dataset_narrative(paths: RunPaths, narrative: DatasetNarrative) -> Path:
    return _write(paths.dataset_narrative, render_dataset_narrative_human_view(narrative))


def _render_intent_scope(intent: ResearchIntent) -> str:
    mode = getattr(getattr(intent, "mode", None), "value", str(getattr(intent, "mode", "")))
    terms = list(
        getattr(intent, "topic_terms", []) or getattr(intent, "target_constructs", []) or []
    )
    lines = [
        "# Research intent",
        "",
        f"- Mode: `{mode}`",
        f"- Terms: {', '.join(terms) or '(none)'}",
        "",
        "This run used an explicit research interest (not an inferred open-mode scope).",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_questions(
    paths: RunPaths,
    *,
    families: Sequence[QuestionFamily],
    shortlist_outcomes: Sequence[FamilyShortlistOutcome],
    basis_by_family: dict[str, EvidenceBasis] | None = None,
    authority_ceiling: FrontHalfAuthorityCeiling | None = None,
    planning_eligible: bool = True,
) -> dict[str, Path]:
    basis_by_family = basis_by_family or {}
    return {
        "question_families": write_question_families(
            paths,
            families=families,
            basis_by_family=basis_by_family,
            authority_ceiling=authority_ceiling,
            planning_eligible=planning_eligible,
        ),
        "shortlist": write_shortlist(
            paths,
            outcomes=shortlist_outcomes,
            basis_by_family=basis_by_family,
            authority_ceiling=authority_ceiling,
            planning_eligible=planning_eligible,
        ),
    }


def write_question_families(
    paths: RunPaths,
    *,
    families: Sequence[QuestionFamily],
    basis_by_family: dict[str, EvidenceBasis] | None = None,
    authority_ceiling: FrontHalfAuthorityCeiling | None = None,
    planning_eligible: bool = True,
) -> Path:
    return _write(
        paths.question_families,
        render_question_families(
            families,
            basis_by_family=basis_by_family,
            authority_ceiling=authority_ceiling,
            planning_eligible=planning_eligible,
        ),
    )


def render_question_families(
    families: Sequence[QuestionFamily],
    *,
    basis_by_family: dict[str, EvidenceBasis] | None = None,
    authority_ceiling: FrontHalfAuthorityCeiling | None = None,
    planning_eligible: bool = True,
) -> str:
    basis_by_family = basis_by_family or {}
    rendered = (
        "\n\n---\n\n".join(
            render_question_family_human_view(
                family, evidence_basis=basis_by_family.get(family.question_family_id)
            )
            for family in families
        )
        or "# Question families\n\n(none)\n"
    )
    return _with_front_half_authority_banner(
        rendered,
        authority_ceiling=authority_ceiling,
        planning_eligible=planning_eligible,
    )


def write_shortlist(
    paths: RunPaths,
    *,
    outcomes: Sequence[FamilyShortlistOutcome],
    basis_by_family: dict[str, EvidenceBasis] | None = None,
    authority_ceiling: FrontHalfAuthorityCeiling | None = None,
    planning_eligible: bool = True,
) -> Path:
    return _write(
        paths.shortlist,
        render_shortlist(
            outcomes,
            basis_by_family=basis_by_family,
            authority_ceiling=authority_ceiling,
            planning_eligible=planning_eligible,
        ),
    )


def render_shortlist(
    outcomes: Sequence[FamilyShortlistOutcome],
    *,
    basis_by_family: dict[str, EvidenceBasis] | None = None,
    authority_ceiling: FrontHalfAuthorityCeiling | None = None,
    planning_eligible: bool = True,
) -> str:
    return _with_front_half_authority_banner(
        render_shortlist_summary(outcomes, basis_by_family=basis_by_family or {}),
        authority_ceiling=authority_ceiling,
        planning_eligible=planning_eligible,
    )


def _with_front_half_authority_banner(
    rendered: str,
    *,
    authority_ceiling: FrontHalfAuthorityCeiling | None,
    planning_eligible: bool,
) -> str:
    if authority_ceiling != FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION:
        return rendered
    banner = _PROVISIONAL_FRONT_HALF_BANNER
    if planning_eligible:
        banner += (
            " Planning continues through the ordinary route, but every downstream plan and dossier "
            "remains provisional until the inputs are independently reviewed."
        )
    else:
        banner += " This historical manifest is planning-ineligible."
    return f"{banner}\n\n{rendered}"


# --- summary.md over ALL outcomes ----------------------------------------------------------
# Honest, NON-approval headings per public label — deliberately forbidden-term-safe (no "approved",
# no "novel", no "significant"/"effect"/"execution"/"result-claim" phrasing).
_LABEL_HEADINGS: dict[FamilyInclusionLabel, str] = {
    FamilyInclusionLabel.INCLUDED_BY_AUTOMATED_REVIEW: (
        "Included (the automated review passed this — suggested reading)"
    ),
    FamilyInclusionLabel.REJECTED_SCIENTIFIC: "Not included (scientifically rejected)",
    FamilyInclusionLabel.DIRECT_RECAP: "Not included (a close prior already covers this)",
    FamilyInclusionLabel.DEFERRED_INSUFFICIENT_EVIDENCE: "Deferred (insufficient evidence)",
    FamilyInclusionLabel.DEFERRED_MATERIAL_REVISION: "Deferred (needs material revision)",
    FamilyInclusionLabel.REVISION_BUDGET_EXHAUSTED: (
        "Deferred (automated revision budget exhausted)"
    ),
    FamilyInclusionLabel.PUBLIC_DOSSIER_REVISION_REQUIRED: (
        "Public dossier revision required (accepted planning retained)"
    ),
    FamilyInclusionLabel.COMPLETED_WITH_WARNINGS: (
        "Completed with a family-level warning (a readable dossier was retained)"
    ),
    FamilyInclusionLabel.RUN_INCOMPLETE: (
        "Run incomplete (an infrastructure issue — NOT a scientific rejection)"
    ),
}

_DEV_SURROGATE_BANNER = (
    "> ⚠️ Subscription-only fallback: independent review incomplete; workflow demo only. These outputs "
    "carry `development_model_surrogate` authority and were NOT independently reviewed."
)
# Prepended to every public dossier.md when the run was downgraded (F1) — no dossier can read as
# independently reviewed when a reviewer ran mock.
DEV_SURROGATE_DOSSIER_BANNER = _DEV_SURROGATE_BANNER + "\n\n"

_PROVISIONAL_INSPIRATION_DOSSIER_BANNER = (
    "> ⚠️ Provisional inspiration: planning continued from source-bound but not independently "
    "reviewed inputs. Dataset claims remain conditional or unverified, and this dossier cannot "
    "be elevated above provisional authority without independent review."
)
PROVISIONAL_INSPIRATION_DOSSIER_BANNER = _PROVISIONAL_INSPIRATION_DOSSIER_BANNER + "\n\n"


def render_run_summary(
    outcomes: Sequence[FamilyRunOutcome],
    *,
    development_surrogate: bool,
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED,
    evidence_basis_line: str = "",
    resume_note: str = "",
    all_family_processing_finished: bool = True,
) -> str:
    """Render ``summary.md`` over ALL family outcomes with honest, non-approval labels.

    ``evidence_basis_line`` (DP-2 surface 7): an honest aggregate when some included families rest on
    abstract-only literature — a loud, cause-neutral flag, never a veto. ``resume_note`` (5c-1c): the
    honest, cause-neutral statement that the run was resumed (N stages reused / M re-run).
    """
    lines = ["# Run summary", ""]
    if development_surrogate:
        lines.extend([_DEV_SURROGATE_BANNER, ""])
    if authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION:
        lines.extend([_PROVISIONAL_INSPIRATION_DOSSIER_BANNER, ""])
    lines.append(f"{len(outcomes)} question family/families reached a terminal outcome.")
    accepted_count = sum(outcome.dossier_axis == DossierAxis.RENDERED for outcome in outcomes)
    hard_incomplete = any(
        outcome.failure_class is not None and outcome.failure_class != FailureClass.SCIENTIFIC
        for outcome in outcomes
    )
    warning_count = sum(outcome.warning_class is not None for outcome in outcomes)
    if not all_family_processing_finished or hard_incomplete:
        lines.append(
            "Overall processing outcome: incomplete — one or more shared or family infrastructure "
            "steps did not finish cleanly."
        )
        if accepted_count:
            lines.append(
                f"{accepted_count} accepted family dossier(s) completed before the stop and remain "
                "available to read."
            )
    elif warning_count:
        lines.append(
            "Overall processing outcome: complete with warnings — every family reached a safe, "
            "user-readable terminal outcome."
        )
        lines.append(
            f"Family warnings: {warning_count}. These families did not gain accepted-plan authority; "
            "their dossiers preserve the question, retained work, and next steps."
        )
        if accepted_count:
            lines.append(
                f"Accepted outputs: {accepted_count} family dossier(s) completed the configured "
                "planning review and are available to read."
            )
    elif accepted_count:
        lines.append(
            "Overall processing outcome: complete — all family attempts reached a terminal outcome."
        )
        lines.append(
            f"Accepted outputs: {accepted_count} family dossier(s) completed the configured "
            "planning review and are available to read."
        )
    else:
        lines.append(
            "Overall processing outcome: complete — all family attempts reached an honest terminal "
            "outcome; none produced a dossier accepted by the configured planning review."
        )
    if resume_note:
        lines.append(resume_note)
    if evidence_basis_line:
        lines.append(evidence_basis_line)
    lines.append("")
    for label, heading in _LABEL_HEADINGS.items():
        bucket = [o for o in outcomes if o.public_summary_label == label]
        if not bucket:
            continue
        lines.extend([f"## {heading}", "", f"- Label: `{label.value}`", ""])
        for outcome in bucket:
            reason = f" — {outcome.reason}" if outcome.reason else ""
            lines.append(f"- `{outcome.question_family_id}`{reason}")
        lines.append("")
    lines.extend(
        [
            "## If this looks wrong",
            "",
            "Adjust `maieusis.yaml` (papers, dataset link/sample, research interest, providers) and re-run.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_run_terminal_summary(terminal: RunTerminal, *, resume_note: str = "") -> str:
    """Render ``summary.md`` for a RUN-LEVEL terminal — a shared front-half failure with NO families.

    Honest and cause-neutral: it names the stage that ended the run and the reason, and points the
    user at the config knobs, instead of a crash or a bare 'fail closed'.
    """
    kind = (
        "did not have enough usable evidence to develop any question"
        if terminal.failure_class == FailureClass.SCIENTIFIC
        else "could not complete a shared setup stage"
    )
    lines = ["# Run summary", "", f"This run {kind}, so no question families were produced.", ""]
    if resume_note:
        lines.extend([resume_note, ""])
    lines.extend(
        [
            f"- Stage: `{terminal.failed_stage}`",
            f"- Outcome class: `{terminal.failure_class.value}`",
        ]
    )
    if terminal.reason:
        lines.append(f"- Reason: {terminal.reason}")
    lines.extend(
        [
            "",
            "## If this looks wrong",
            "",
            "Adjust `maieusis.yaml` (papers, dataset link/sample, research interest, providers) and re-run.",
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_run_terminal_summary(
    paths: RunPaths, terminal: RunTerminal, *, resume_note: str = ""
) -> Path:
    """Validate (forbidden-term + jargon) then write the run-terminal ``summary.md`` ATOMICALLY."""
    text = render_run_terminal_summary(terminal, resume_note=resume_note)
    forbidden = validate_aggregate_report_text(text)
    if forbidden:
        raise ValueError("run summary contains forbidden terms: " + ", ".join(forbidden))
    jargon = find_public_markdown_jargon(text)
    if jargon:
        raise ValueError("run summary contains internal jargon: " + ", ".join(jargon))
    paths.summary.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=paths.summary.parent, suffix=".md.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_name, paths.summary)
    finally:
        Path(tmp_name).unlink(missing_ok=True)
    return paths.summary


def write_run_summary(
    paths: RunPaths,
    outcomes: Sequence[FamilyRunOutcome],
    *,
    development_surrogate: bool,
    authority_ceiling: FrontHalfAuthorityCeiling = FrontHalfAuthorityCeiling.VERIFIED,
    evidence_basis_line: str = "",
    resume_note: str = "",
    all_family_processing_finished: bool = True,
) -> Path:
    """Validate (forbidden-term) then write ``summary.md`` ATOMICALLY (temp + os.replace) — LAST.

    Normal callers write only after every family reached a terminal. A shared back-half terminal passes
    ``all_family_processing_finished=False`` so retained completed siblings remain visible without the
    partial run reading as successful. A resumed run regenerates this projection with ``resume_note``.
    """
    # Defense in depth for outcomes constructed outside the main driver. Sanitization removes only
    # internal identifiers, credentials, local paths, and serialized authority/result fields; it
    # deliberately preserves ordinary scientific prose. Applying it to every reason prevents one
    # family's dirty presentation text from turning final cohort rendering into a shared failure.
    safe_outcomes = [
        outcome.model_copy(update={"reason": sanitize_family_failure_text(outcome.reason)})
        if outcome.reason
        else outcome
        for outcome in outcomes
    ]
    text = render_run_summary(
        safe_outcomes,
        development_surrogate=development_surrogate,
        authority_ceiling=authority_ceiling,
        evidence_basis_line=evidence_basis_line,
        resume_note=resume_note,
        all_family_processing_finished=all_family_processing_finished,
    )
    forbidden = validate_aggregate_report_text(text)
    if forbidden:
        raise ValueError("run summary contains forbidden terms: " + ", ".join(forbidden))
    jargon = find_public_markdown_jargon(text)
    if jargon:
        raise ValueError("run summary contains internal jargon: " + ", ".join(jargon))
    paths.summary.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=paths.summary.parent, suffix=".md.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_name, paths.summary)
    finally:
        Path(tmp_name).unlink(missing_ok=True)
    return paths.summary
