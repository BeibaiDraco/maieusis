from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...io import dump_data
from ...provenance import stable_hash
from ...schemas.question_pattern import (
    QuestionPatternBankEntry,
    QuestionPatternBankManifest,
    QuestionPatternCard,
    QuestionPatternHumanDecision,
    QuestionPatternReview,
    QuestionPatternReviewStatus,
)
from .formation_trace import FormationTraceRecord
from .induction import (
    QUESTION_PATTERN_INDUCER_PROMPT_VERSION,
    QuestionPatternInductionBatch,
    validate_pattern_abstraction,
)


class QuestionPatternReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: QuestionPatternCard
    source_records: list[FormationTraceRecord] = Field(default_factory=list)
    auto_flags: list[str] = Field(default_factory=list)


class QuestionPatternReviewPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: str
    prompt_version: str = QUESTION_PATTERN_INDUCER_PROMPT_VERSION
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    items: list[QuestionPatternReviewItem] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)


class QuestionPatternReviewDecisionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_batch_id: str
    pack_id: str
    expert_reviewer: str = ""
    decisions: list[QuestionPatternReview] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_duplicate_decisions(self) -> QuestionPatternReviewDecisionBatch:
        ids = [decision.pattern_id for decision in self.decisions]
        duplicates = sorted({pattern_id for pattern_id in ids if ids.count(pattern_id) > 1})
        if duplicates:
            raise ValueError(
                "QuestionPatternReviewDecisionBatch contains duplicate decisions: "
                + ", ".join(duplicates)
            )
        return self


class QuestionPatternReviewPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack: QuestionPatternReviewPack
    decision_template: QuestionPatternReviewDecisionBatch
    markdown: str


class QuestionPatternReviewImportResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: str
    accepted_patterns: list[QuestionPatternCard] = Field(default_factory=list)
    rejected_patterns: list[QuestionPatternCard] = Field(default_factory=list)
    unresolved_patterns: list[QuestionPatternCard] = Field(default_factory=list)
    unresolved_reviews: list[QuestionPatternReview] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def prepare_question_pattern_review(
    patterns: list[QuestionPatternCard],
    source_records: list[FormationTraceRecord],
) -> QuestionPatternReviewPreparation:
    record_by_case = {record.paper_case_id: record for record in source_records}
    items: list[QuestionPatternReviewItem] = []
    for pattern in patterns:
        records = [
            record_by_case[case_id]
            for case_id in pattern.source_case_ids
            if case_id in record_by_case
        ]
        items.append(
            QuestionPatternReviewItem(
                pattern=pattern,
                source_records=records,
                auto_flags=validate_pattern_abstraction(pattern, records or source_records),
            )
        )
    pack = QuestionPatternReviewPack(
        pack_id=f"question-pattern-review-{stable_hash([p.pattern_id for p in patterns])[:12]}",
        items=items,
        instructions=[
            "Review whether each pattern faithfully abstracts the cited paper traces.",
            "Mark expert_reviewed only when the pattern is transferable and scientifically useful.",
            "Leave draft when more evidence or rewriting is needed.",
        ],
    )
    decision_template = QuestionPatternReviewDecisionBatch(
        decision_batch_id=f"{pack.pack_id}-decisions-template",
        pack_id=pack.pack_id,
        decisions=[
            QuestionPatternReview(
                review_id=f"review-{item.pattern.pattern_id}",
                pattern_id=item.pattern.pattern_id,
            )
            for item in items
        ],
    )
    return QuestionPatternReviewPreparation(
        pack=pack,
        decision_template=decision_template,
        markdown=render_question_pattern_review_markdown(pack),
    )


def render_question_pattern_review_markdown(pack: QuestionPatternReviewPack) -> str:
    lines = [
        f"# Question Pattern Review Pack: {pack.pack_id}",
        "",
        "Boundary: this pack supports expert review only. It does not approve patterns, "
        "generate QuestionSeeds, or authorize AnalysisContracts.",
        "",
    ]
    for index, item in enumerate(pack.items, start=1):
        pattern = item.pattern
        lines.extend(
            [
                f"## {index}. {pattern.pattern_name}",
                "",
                f"- Pattern ID: `{pattern.pattern_id}`",
                f"- Transfer scope: `{pattern.transfer_scope.value}`",
                f"- Source cases: {', '.join(pattern.source_case_ids) or 'none'}",
                f"- Source traces: {', '.join(pattern.source_trace_ids) or 'none'}",
                f"- Starting scientific state: {'; '.join(pattern.starting_scientific_state) or '[missing]'}",
                f"- Unresolved tension pattern: {pattern.unresolved_tension_pattern}",
                f"- Dataset cues: {'; '.join(pattern.dataset_cues) or '[missing]'}",
                f"- Formation move: {pattern.question_formation_move}",
                f"- Scientific payoff: {pattern.scientific_payoff}",
                f"- Positive consequence: {pattern.positive_result_consequence}",
                f"- Negative consequence: {pattern.negative_result_consequence}",
                f"- Common failure modes: {'; '.join(pattern.common_failure_modes) or '[missing]'}",
                f"- Non-transferable details: {'; '.join(pattern.non_transferable_details) or '[missing]'}",
                f"- Auto flags: {', '.join(item.auto_flags) or 'none'}",
                "",
            ]
        )
        for record in item.source_records:
            trace = record.formation_trace
            lines.extend(
                [
                    f"### Source `{record.paper_case_id}`",
                    "",
                    f"- Citation: {record.citation or '[missing]'}",
                    f"- Original question: {record.original_question or '[missing]'}",
                    f"- Background: {' '.join(trace.background_claims)}",
                    f"- Unresolved gap: {trace.unresolved_gap}",
                    f"- Dataset feature noticed: {trace.dataset_feature_noticed}",
                    f"- Opportunity inference: {trace.opportunity_inference}",
                    f"- Resulting question: {trace.resulting_question}",
                    f"- Consequence: {trace.expected_scientific_consequence}",
                    f"- Scientific significance: {trace.scientific_significance}",
                    f"- Trace move: {trace.transferable_reasoning_pattern}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def import_question_pattern_reviews(
    *,
    pack: QuestionPatternReviewPack,
    decisions: QuestionPatternReviewDecisionBatch,
    require_complete: bool = False,
) -> QuestionPatternReviewImportResult:
    if decisions.pack_id != pack.pack_id:
        raise ValueError("QuestionPatternReviewDecisionBatch pack_id does not match review pack")
    item_by_pattern = {item.pattern.pattern_id: item for item in pack.items}
    decision_pattern_ids = {decision.pattern_id for decision in decisions.decisions}
    result = QuestionPatternReviewImportResult(pack_id=pack.pack_id)
    if require_complete:
        missing = sorted(set(item_by_pattern) - decision_pattern_ids)
        if missing:
            result.errors.append("Missing pattern review decisions: " + ", ".join(missing))
    for decision in decisions.decisions:
        item = item_by_pattern.get(decision.pattern_id)
        if item is None:
            result.errors.append(f"Decision references unknown pattern: {decision.pattern_id}")
            continue
        # Validate the human decision against the human-only enum. An ``ai_reviewed`` (or any other
        # non-human) status ERRORS here — it is NEVER laundered into EXPERT_REVIEWED. AI authority can
        # only be granted by the automated gate's promoter, never through this human import path.
        try:
            human_decision = QuestionPatternHumanDecision(decision.status.value)
        except ValueError:
            result.errors.append(
                f"{decision.pattern_id}: {decision.status.value!r} is not a valid human review "
                "decision (ai_reviewed is set only by the automated gate, never the human importer)"
            )
            continue
        if human_decision in {
            QuestionPatternHumanDecision.DRAFT,
            QuestionPatternHumanDecision.NEEDS_REVISION,
        }:
            result.unresolved_reviews.append(decision)
            result.unresolved_patterns.append(
                QuestionPatternCard.model_validate(
                    {
                        **item.pattern.model_dump(mode="python"),
                        "review_status": QuestionPatternReviewStatus(human_decision.value),
                    }
                )
            )
            continue
        if human_decision == QuestionPatternHumanDecision.REJECTED:
            result.rejected_patterns.append(
                QuestionPatternCard.model_validate(
                    {
                        **item.pattern.model_dump(mode="python"),
                        "review_status": QuestionPatternReviewStatus.REJECTED,
                    }
                )
            )
            continue
        try:  # human_decision == ACCEPT → EXPERT_REVIEWED (the only human accept)
            result.accepted_patterns.append(
                QuestionPatternCard.model_validate(
                    {
                        **item.pattern.model_dump(mode="python"),
                        "review_status": QuestionPatternReviewStatus.EXPERT_REVIEWED,
                    }
                )
            )
        except ValueError as exc:
            result.errors.append(f"{decision.pattern_id}: {exc}")
    if require_complete and result.unresolved_reviews:
        result.errors.append(
            "Pattern review import requires final decisions for all patterns: "
            + ", ".join(review.pattern_id for review in result.unresolved_reviews)
        )
    return result


def write_question_pattern_review_outputs(
    preparation: QuestionPatternReviewPreparation,
    output_dir: str | Path,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "pack": dump_data(preparation.pack, output / "question_pattern_review_pack.yaml"),
        "decision_template": dump_data(
            preparation.decision_template,
            output / "question_pattern_decisions.template.yaml",
        ),
        "decision_file": dump_data(
            preparation.decision_template,
            output / "question_pattern_decisions.yaml",
        ),
        "markdown": output / "question_pattern_review.md",
    }
    paths["markdown"].write_text(preparation.markdown, encoding="utf-8")
    return paths


def write_question_pattern_induction_outputs(
    batch: QuestionPatternInductionBatch,
    *,
    corpus_root: str | Path = "corpus",
) -> dict[str, Path]:
    root = Path(corpus_root)
    induction_dir = root / "patterns" / "induction"
    induction_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "batch": dump_data(
            batch,
            induction_dir / "question_pattern_induction_batch.yaml",
        )
    }
    write_question_pattern_bank(batch.patterns, corpus_root=root)
    paths["manifest"] = root / "question_pattern_manifest.yaml"
    return paths


def write_question_pattern_bank(
    patterns: list[QuestionPatternCard],
    *,
    corpus_root: str | Path = "corpus",
) -> QuestionPatternBankManifest:
    root = Path(corpus_root)
    extracted_dir = root / "patterns" / "extracted"
    reviewed_dir = root / "patterns" / "reviewed"
    extracted_dir.mkdir(parents=True, exist_ok=True)
    reviewed_dir.mkdir(parents=True, exist_ok=True)
    entries: list[QuestionPatternBankEntry] = []
    for pattern in patterns:
        target_dir = reviewed_dir if pattern.is_proposal_ready else extracted_dir
        path = target_dir / f"{pattern.pattern_id}.question_pattern.yaml"
        dump_data(pattern, path)
        relative_path = Path(root.name) / path.relative_to(root)
        entries.append(
            QuestionPatternBankEntry(
                pattern_id=pattern.pattern_id,
                pattern_path=relative_path.as_posix(),
                status=pattern.review_status,
                transfer_scope=pattern.transfer_scope,
                source_case_ids=pattern.source_case_ids,
                source_trace_ids=pattern.source_trace_ids,
                pattern_digest=stable_hash(pattern),
            )
        )
    manifest = QuestionPatternBankManifest(entries=entries)
    dump_data(manifest, root / "question_pattern_manifest.yaml")
    return manifest
