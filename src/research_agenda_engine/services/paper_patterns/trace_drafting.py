from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...assets import resolve_asset
from ...io import dump_data, load_model
from ...provenance import stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas.paper_case import PaperCase
from ...schemas.question_pattern import (
    QuestionFormationEvidenceBinding,
    QuestionFormationEvidenceBindingRole,
    QuestionFormationLiteratureEvidence,
    QuestionFormationTrace,
    QuestionFormationTraceReviewStatus,
)
from ..retrieval.paper_case_index import PaperCaseIndex
from .literature_context import (
    PaperLocalLiteratureTraceContext,
    load_paper_local_literature_trace_context,
    validate_trace_literature_evidence,
)

QUESTION_FORMATION_TRACE_DRAFTER_PROMPT_VERSION = "question_formation_trace_drafter/v3"


class TraceDraftInsufficientEvidence(Exception):
    """The model produced a trace with no reconcilable evidence backing (after dropping every
    mis-transcribed reference). An HONEST per-artifact insufficiency — the driver drops the paper
    from pattern induction (E) instead of re-prompting the model or crashing the run."""


class FormationTraceDraftStatus(StrEnum):
    DRAFTED = "drafted"
    FAILED = "failed"


class FormationTraceDecisionStatus(StrEnum):
    DRAFT = "draft"
    EXPERT_REVIEWED = "expert_reviewed"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


class _TraceDraftModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trace_id: str = ""
    background_claims: list[str] = Field(default_factory=list)
    unresolved_gap: str = ""
    dataset_feature_noticed: str = ""
    opportunity_inference: str = ""
    resulting_question: str = ""
    expected_scientific_consequence: str = ""
    scientific_significance: str = ""
    transferable_reasoning_pattern: str = ""
    non_transferable_assumptions: list[str] = Field(default_factory=list)
    evidence_span_ids: list[str] = Field(default_factory=list)
    local_literature_context_id: str = ""
    local_literature_context_digest: str = ""
    key_cited_work_ids: list[str] = Field(default_factory=list)
    literature_evidence: list[QuestionFormationLiteratureEvidence] = Field(default_factory=list)
    evidence_bindings: list[QuestionFormationEvidenceBinding] = Field(default_factory=list)
    review_status: str = QuestionFormationTraceReviewStatus.DRAFT.value


class FormationTraceDraftArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: str
    paper_case_id: str
    prompt_version: str = QUESTION_FORMATION_TRACE_DRAFTER_PROMPT_VERSION
    provider_id: str = ""
    model_id: str = ""
    input_digest: str
    paper_case_digest: str
    local_literature_context_id: str
    local_literature_context_digest: str
    trace: QuestionFormationTrace
    auto_flags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_draft_links(self) -> FormationTraceDraftArtifact:
        if self.trace.review_status != QuestionFormationTraceReviewStatus.DRAFT:
            raise ValueError("FormationTraceDraftArtifact trace must remain draft")
        if self.trace.local_literature_context_id != self.local_literature_context_id:
            raise ValueError("draft trace local_literature_context_id mismatch")
        if self.trace.local_literature_context_digest != self.local_literature_context_digest:
            raise ValueError("draft trace local_literature_context_digest mismatch")
        return self


class FormationTraceDraftManifestItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_case_id: str
    status: FormationTraceDraftStatus
    draft_path: str = ""
    auto_flags: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class FormationTraceDraftManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_id: str
    prompt_version: str = QUESTION_FORMATION_TRACE_DRAFTER_PROMPT_VERSION
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    item_count: int = 0
    draft_count: int = 0
    failed_count: int = 0
    items: list[FormationTraceDraftManifestItem] = Field(default_factory=list)


class FormationTraceReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_case_id: str
    citation: str = ""
    original_question: str = ""
    draft: FormationTraceDraftArtifact
    local_literature: PaperLocalLiteratureTraceContext
    auto_flags: list[str] = Field(default_factory=list)


class FormationTraceReviewPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: str
    prompt_version: str = QUESTION_FORMATION_TRACE_DRAFTER_PROMPT_VERSION
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    items: list[FormationTraceReviewItem] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)


class FormationTraceReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: str
    paper_case_id: str
    status: FormationTraceDecisionStatus = FormationTraceDecisionStatus.DRAFT
    reviewer: str = ""
    required_changes: list[str] = Field(default_factory=list)
    notes: str = ""


class FormationTraceReviewDecisionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_batch_id: str
    pack_id: str
    decisions: list[FormationTraceReviewDecision] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_decisions(self) -> FormationTraceReviewDecisionBatch:
        decision_ids = [decision.decision_id for decision in self.decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("FormationTraceReviewDecisionBatch contains duplicate decision_id")
        paper_case_ids = [decision.paper_case_id for decision in self.decisions]
        if len(paper_case_ids) != len(set(paper_case_ids)):
            raise ValueError("FormationTraceReviewDecisionBatch contains duplicate paper_case_id")
        return self


class FormationTraceReviewImportResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_batch_id: str
    pack_id: str
    imported_count: int = 0
    skipped_count: int = 0
    imported_paper_case_ids: list[str] = Field(default_factory=list)
    skipped_paper_case_ids: list[str] = Field(default_factory=list)
    dry_run: bool = False


class FormationTraceReviewPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack: FormationTraceReviewPack
    decision_template: FormationTraceReviewDecisionBatch
    markdown: str


def draft_question_formation_trace(
    provider: StructuredModelProvider,
    *,
    paper_case: PaperCase,
    trace_context: PaperLocalLiteratureTraceContext,
    prompt_path: Path | None = None,
    max_prompt_chars: int = 300_000,
) -> FormationTraceDraftArtifact:
    prompt = (prompt_path or _default_prompt_path()).read_text(encoding="utf-8")
    payload = _draft_payload(paper_case=paper_case, trace_context=trace_context)
    user_prompt = json.dumps(payload, ensure_ascii=False, indent=2)
    if len(prompt) + len(user_prompt) > max_prompt_chars:
        raise ValueError("question formation trace draft prompt exceeded max_prompt_chars")
    input_digest = stable_hash({"system": prompt, "user": payload})
    # Deterministic host reconciliation (Strategy-1): _trace_from_model_output drops+flags every
    # mis-transcribed reference itself, so there is no model-retry. It raises only
    # TraceDraftInsufficientEvidence — a genuine no-usable-evidence signal the caller degrades on
    # (E), never a re-prompt.
    model_output = provider.generate_structured(
        system_prompt=prompt,
        user_prompt=user_prompt,
        output_model=_TraceDraftModelOutput,
    )
    trace, auto_flags = _trace_from_model_output(
        model_output=model_output,
        paper_case=paper_case,
        trace_context=trace_context,
    )
    return FormationTraceDraftArtifact(
        draft_id=f"formation-trace-draft-{paper_case.paper_case_id}-{input_digest[:12]}",
        paper_case_id=paper_case.paper_case_id,
        provider_id=provider.provider_name,
        model_id=provider.model_name,
        input_digest=input_digest,
        paper_case_digest=stable_hash(paper_case),
        local_literature_context_id=trace_context.local_literature_context_id,
        local_literature_context_digest=trace_context.local_literature_context_digest,
        trace=trace,
        auto_flags=auto_flags,
    )


def build_reviewed_formation_trace_drafts(
    *,
    provider: StructuredModelProvider,
    corpus_root: str | Path = "corpus",
    paper_ids: list[str] | None = None,
    write_review_pack: bool = False,
    max_prompt_chars: int = 300_000,
) -> FormationTraceDraftManifest:
    root = Path(corpus_root)
    drafts_dir = root / "formation_traces" / "drafts"
    cases = _reviewed_cases(root, paper_ids or [])
    items: list[FormationTraceDraftManifestItem] = []
    review_items: list[FormationTraceReviewItem] = []
    for paper_case in cases:
        try:
            trace_context = load_paper_local_literature_trace_context(
                paper_case=paper_case,
                corpus_root=root,
            )
            if trace_context is None:
                raise ValueError("missing paper-local literature trace context")
            draft = draft_question_formation_trace(
                provider,
                paper_case=paper_case,
                trace_context=trace_context,
                max_prompt_chars=max_prompt_chars,
            )
            draft_path = (
                drafts_dir / f"{paper_case.paper_case_id}.question_formation_trace_draft.yaml"
            )
            dump_data(draft, draft_path)
            items.append(
                FormationTraceDraftManifestItem(
                    paper_case_id=paper_case.paper_case_id,
                    status=FormationTraceDraftStatus.DRAFTED,
                    draft_path=str(draft_path),
                    auto_flags=draft.auto_flags,
                )
            )
            review_items.append(
                FormationTraceReviewItem(
                    paper_case_id=paper_case.paper_case_id,
                    citation=paper_case.citation,
                    original_question=paper_case.scientific_question.original_question,
                    draft=draft,
                    local_literature=trace_context,
                    auto_flags=draft.auto_flags,
                )
            )
        except Exception as exc:
            items.append(
                FormationTraceDraftManifestItem(
                    paper_case_id=paper_case.paper_case_id,
                    status=FormationTraceDraftStatus.FAILED,
                    errors=[str(exc)],
                )
            )
    manifest = FormationTraceDraftManifest(
        manifest_id=f"formation-trace-draft-{stable_hash([item.model_dump(mode='json') for item in items])[:12]}",
        item_count=len(items),
        draft_count=sum(1 for item in items if item.status == FormationTraceDraftStatus.DRAFTED),
        failed_count=sum(1 for item in items if item.status == FormationTraceDraftStatus.FAILED),
        items=items,
    )
    dump_data(manifest, root / "formation_traces" / "formation_trace_draft_manifest.yaml")
    if write_review_pack:
        preparation = prepare_formation_trace_review(review_items)
        write_formation_trace_review_outputs(
            preparation,
            root / "formation_traces" / "review",
        )
    return manifest


def rebuild_formation_trace_draft_manifest_from_sidecars(
    *,
    corpus_root: str | Path = "corpus",
    paper_ids: list[str] | None = None,
) -> FormationTraceDraftManifest:
    root = Path(corpus_root)
    items: list[FormationTraceDraftManifestItem] = []
    for paper_case in _reviewed_cases(root, paper_ids or []):
        draft_path = (
            root
            / "formation_traces"
            / "drafts"
            / f"{paper_case.paper_case_id}.question_formation_trace_draft.yaml"
        )
        if not draft_path.exists():
            items.append(
                FormationTraceDraftManifestItem(
                    paper_case_id=paper_case.paper_case_id,
                    status=FormationTraceDraftStatus.FAILED,
                    errors=[f"draft sidecar not found: {draft_path}"],
                )
            )
            continue
        try:
            draft = load_model(draft_path, FormationTraceDraftArtifact)
            if draft.paper_case_id != paper_case.paper_case_id:
                raise ValueError(
                    "draft sidecar paper_case_id mismatch: "
                    f"{draft.paper_case_id} != {paper_case.paper_case_id}"
                )
            items.append(
                FormationTraceDraftManifestItem(
                    paper_case_id=paper_case.paper_case_id,
                    status=FormationTraceDraftStatus.DRAFTED,
                    draft_path=str(draft_path),
                    auto_flags=draft.auto_flags,
                )
            )
        except Exception as exc:
            items.append(
                FormationTraceDraftManifestItem(
                    paper_case_id=paper_case.paper_case_id,
                    status=FormationTraceDraftStatus.FAILED,
                    errors=[str(exc)],
                )
            )
    manifest = FormationTraceDraftManifest(
        manifest_id=f"formation-trace-draft-{stable_hash([item.model_dump(mode='json') for item in items])[:12]}",
        item_count=len(items),
        draft_count=sum(1 for item in items if item.status == FormationTraceDraftStatus.DRAFTED),
        failed_count=sum(1 for item in items if item.status == FormationTraceDraftStatus.FAILED),
        items=items,
    )
    dump_data(manifest, root / "formation_traces" / "formation_trace_draft_manifest.yaml")
    return manifest


def prepare_formation_trace_review_from_sidecars(
    *,
    corpus_root: str | Path = "corpus",
    paper_ids: list[str] | None = None,
) -> FormationTraceReviewPreparation:
    root = Path(corpus_root)
    items: list[FormationTraceReviewItem] = []
    for paper_case in _reviewed_cases(root, paper_ids or []):
        draft_path = (
            root
            / "formation_traces"
            / "drafts"
            / f"{paper_case.paper_case_id}.question_formation_trace_draft.yaml"
        )
        if not draft_path.exists():
            raise ValueError(f"draft sidecar not found: {draft_path}")
        draft = load_model(draft_path, FormationTraceDraftArtifact)
        if draft.paper_case_id != paper_case.paper_case_id:
            raise ValueError(
                "draft sidecar paper_case_id mismatch: "
                f"{draft.paper_case_id} != {paper_case.paper_case_id}"
            )
        trace_context = load_paper_local_literature_trace_context(
            paper_case=paper_case,
            corpus_root=root,
        )
        if trace_context is None:
            raise ValueError(
                f"missing paper-local literature trace context: {paper_case.paper_case_id}"
            )
        if draft.local_literature_context_id != trace_context.local_literature_context_id:
            raise ValueError(
                f"draft local_literature_context_id mismatch: {paper_case.paper_case_id}"
            )
        if draft.local_literature_context_digest != trace_context.local_literature_context_digest:
            raise ValueError(
                f"draft local_literature_context_digest mismatch: {paper_case.paper_case_id}"
            )
        items.append(
            FormationTraceReviewItem(
                paper_case_id=paper_case.paper_case_id,
                citation=paper_case.citation,
                original_question=paper_case.scientific_question.original_question,
                draft=draft,
                local_literature=trace_context,
                auto_flags=draft.auto_flags,
            )
        )
    return prepare_formation_trace_review(items)


def prepare_formation_trace_review(
    items: list[FormationTraceReviewItem],
) -> FormationTraceReviewPreparation:
    pack = FormationTraceReviewPack(
        pack_id=f"formation-trace-review-{stable_hash([item.paper_case_id for item in items])[:12]}",
        items=items,
        instructions=[
            "Review whether each draft trace faithfully captures how the source paper formed its question.",
            "Drafts do not modify reviewed PaperCases and do not authorize QuestionSeeds.",
            "Use expert_reviewed only when the trace and cited literature roles are scientifically faithful.",
        ],
    )
    decision_template = FormationTraceReviewDecisionBatch(
        decision_batch_id=f"{pack.pack_id}-decisions-template",
        pack_id=pack.pack_id,
        decisions=[
            FormationTraceReviewDecision(
                decision_id=f"review-{item.paper_case_id}",
                paper_case_id=item.paper_case_id,
            )
            for item in items
        ],
    )
    return FormationTraceReviewPreparation(
        pack=pack,
        decision_template=decision_template,
        markdown=render_formation_trace_review_markdown(pack),
    )


def render_formation_trace_review_markdown(pack: FormationTraceReviewPack) -> str:
    lines = [
        f"# Formation Trace Review Pack: {pack.pack_id}",
        "",
        "Boundary: this pack is for expert review only. It does not write traces back to "
        "PaperCases, generate QuestionSeeds, or authorize AnalysisContracts.",
        "",
    ]
    for index, item in enumerate(pack.items, start=1):
        trace = item.draft.trace
        lines.extend(
            [
                f"## {index}. `{item.paper_case_id}`",
                "",
                f"- Citation: {item.citation or '[missing]'}",
                f"- Original question: {item.original_question or '[missing]'}",
                f"- Auto flags: {', '.join(item.auto_flags) or 'none'}",
                f"- Background: {' '.join(trace.background_claims)}",
                f"- Unresolved gap: {trace.unresolved_gap}",
                f"- Dataset feature noticed: {trace.dataset_feature_noticed}",
                f"- Opportunity inference: {trace.opportunity_inference}",
                f"- Resulting question: {trace.resulting_question}",
                f"- Consequence: {trace.expected_scientific_consequence}",
                f"- Scientific significance: {trace.scientific_significance}",
                f"- Transferable pattern: {trace.transferable_reasoning_pattern}",
                "",
                "### Selected Cited Works Used",
                "",
            ]
        )
        selected_by_id = {
            work.cited_work_id: work for work in item.local_literature.selected_cited_works
        }
        formation_roles_by_cited_work = _formation_roles_by_cited_work(trace)
        for evidence in trace.literature_evidence:
            work = selected_by_id.get(evidence.cited_work_id)
            title = work.title if work else "[missing selected work]"
            rank = work.selection_rank if work else evidence.selection_rank
            formation_roles = formation_roles_by_cited_work.get(evidence.cited_work_id, [])
            lines.extend(
                [
                    f"- `{evidence.cited_work_id}` rank {rank}: {title}",
                    f"  - Formation roles: {_format_roles(formation_roles)}",
                    f"  - Citation role hint: `{evidence.role.value}`",
                    f"  - Rationale: {evidence.rationale}",
                ]
            )
        lines.extend(["", "### Evidence Bindings", ""])
        for binding in trace.evidence_bindings:
            evidence_ids = (
                binding.source_span_ids + binding.cited_work_ids + binding.citation_context_ids
            )
            lines.extend(
                [
                    f"- `{binding.role.value}`: {binding.rationale}",
                    f"  - Evidence IDs: {', '.join(evidence_ids) or '[missing]'}",
                ]
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _formation_roles_by_cited_work(trace: QuestionFormationTrace) -> dict[str, list[str]]:
    roles_by_work: dict[str, set[str]] = {}
    for binding in trace.evidence_bindings:
        for cited_work_id in binding.cited_work_ids:
            roles_by_work.setdefault(cited_work_id, set()).add(binding.role.value)
    return {
        cited_work_id: sorted(roles)
        for cited_work_id, roles in sorted(roles_by_work.items(), key=lambda item: item[0])
    }


def _format_roles(roles: list[str]) -> str:
    return ", ".join(f"`{role}`" for role in roles) if roles else "[missing]"


def write_formation_trace_review_outputs(
    preparation: FormationTraceReviewPreparation,
    output_dir: str | Path,
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "pack": dump_data(preparation.pack, output / "formation_trace_review_pack.yaml"),
        "decision_template": dump_data(
            preparation.decision_template,
            output / "formation_trace_decisions.template.yaml",
        ),
        "markdown": output / "formation_trace_review.md",
    }
    paths["markdown"].write_text(preparation.markdown, encoding="utf-8")
    return paths


def import_formation_trace_review_decisions(
    *,
    decisions: FormationTraceReviewDecisionBatch,
    review_pack: FormationTraceReviewPack,
    corpus_root: str | Path = "corpus",
    dry_run: bool = False,
) -> FormationTraceReviewImportResult:
    if decisions.pack_id != review_pack.pack_id:
        raise ValueError("formation trace decision pack_id does not match review pack")
    pack_by_paper_id = {item.paper_case_id: item for item in review_pack.items}
    decision_paper_ids = {decision.paper_case_id for decision in decisions.decisions}
    if decision_paper_ids != set(pack_by_paper_id):
        missing = sorted(set(pack_by_paper_id) - decision_paper_ids)
        extra = sorted(decision_paper_ids - set(pack_by_paper_id))
        details = []
        if missing:
            details.append("missing decisions: " + ", ".join(missing))
        if extra:
            details.append("unknown decisions: " + ", ".join(extra))
        raise ValueError(
            "formation trace review decisions must match pack items: " + "; ".join(details)
        )

    root = Path(corpus_root)
    imported: list[str] = []
    skipped: list[str] = []
    for decision in decisions.decisions:
        if decision.status == FormationTraceDecisionStatus.DRAFT:
            raise ValueError(f"formation trace decision remains draft: {decision.paper_case_id}")
        if not decision.reviewer.strip():
            raise ValueError(
                f"formation trace decision requires reviewer: {decision.paper_case_id}"
            )
        item = pack_by_paper_id[decision.paper_case_id]
        if decision.status != FormationTraceDecisionStatus.EXPERT_REVIEWED:
            skipped.append(decision.paper_case_id)
            continue
        if decision.required_changes:
            raise ValueError(
                "expert_reviewed formation trace decision cannot have required_changes: "
                + decision.paper_case_id
            )
        case_path = root / "cases" / "reviewed" / f"{decision.paper_case_id}.paper_case.yaml"
        if not case_path.exists():
            raise ValueError(f"reviewed PaperCase file not found: {case_path}")
        paper_case = load_model(case_path, PaperCase)
        digest_case = (
            paper_case.model_copy(update={"formation_trace": None})
            if paper_case.formation_trace is not None
            else paper_case
        )
        if stable_hash(digest_case) != item.draft.paper_case_digest:
            raise ValueError(
                "reviewed PaperCase digest does not match formation trace draft: "
                + decision.paper_case_id
            )
        trace_context = load_paper_local_literature_trace_context(
            paper_case=digest_case,
            corpus_root=root,
        )
        if trace_context is None:
            raise ValueError(
                "missing paper-local literature trace context: " + decision.paper_case_id
            )
        if (
            trace_context.local_literature_context_digest
            != item.draft.local_literature_context_digest
        ):
            raise ValueError(
                "paper-local literature digest mismatch for draft import: " + decision.paper_case_id
            )
        closed_evidence_span_ids = list(
            dict.fromkeys(
                item.draft.trace.evidence_span_ids
                + [
                    source_span_id
                    for binding in item.draft.trace.evidence_bindings
                    for source_span_id in binding.source_span_ids
                ]
            )
        )
        trace = QuestionFormationTrace.model_validate(
            {
                **item.draft.trace.model_dump(mode="python"),
                "evidence_span_ids": closed_evidence_span_ids,
                "review_status": QuestionFormationTraceReviewStatus.EXPERT_REVIEWED,
            }
        )
        literature_issues = validate_trace_literature_evidence(
            trace=trace,
            trace_context=trace_context,
        )
        if literature_issues:
            raise ValueError(
                "formation trace literature evidence invalid for import: "
                + decision.paper_case_id
                + ": "
                + "; ".join(literature_issues)
            )
        updated_case = PaperCase.model_validate(
            {
                **paper_case.model_dump(mode="python"),
                "formation_trace": trace.model_dump(mode="python"),
            }
        )
        if not dry_run:
            dump_data(updated_case, case_path)
        imported.append(decision.paper_case_id)
    return FormationTraceReviewImportResult(
        decision_batch_id=decisions.decision_batch_id,
        pack_id=decisions.pack_id,
        imported_count=len(imported),
        skipped_count=len(skipped),
        imported_paper_case_ids=imported,
        skipped_paper_case_ids=skipped,
        dry_run=dry_run,
    )


def _trace_from_model_output(
    *,
    model_output: _TraceDraftModelOutput,
    paper_case: PaperCase,
    trace_context: PaperLocalLiteratureTraceContext,
) -> tuple[QuestionFormationTrace, list[str]]:
    auto_flags: list[str] = []
    valid_span_ids = {
        span.source_span_id for span in paper_case.evidence_spans if span.source_span_id
    }
    invalid_span_ids = sorted(set(model_output.evidence_span_ids) - valid_span_ids)
    if invalid_span_ids:
        auto_flags.append("invalid_evidence_span_ids_removed: " + ", ".join(invalid_span_ids))
    allowed_contexts_by_work = {
        work.cited_work_id: set(work.evidence_context_ids)
        for work in trace_context.selected_cited_works
    }
    selected_ids = set(trace_context.key_cited_work_ids)
    # A context whose citation-importance selection chose nothing is THINNER, not invalid. Every
    # literature requirement below is conditioned on this, mirroring the schema, which conditions
    # the same requirements on `local_literature_context_id` being claimed. Without this the three
    # sites below reduce a citation-free trace to zero literature evidence and then reject it FOR
    # having none -- a bar the paper can never clear because the drafter was handed nothing to
    # clear it with.
    citation_free_context = not trace_context.local_literature_context_id.strip()
    # Deterministic reconciliation (Strategy-1): a cited-work id the model mis-transcribed is DROPPED
    # and flagged, never re-prompted. literature_evidence entries citing a non-selected work are
    # dropped; binding cited-work ids are filtered to the selected set below.
    bad_cited_ids = sorted(
        {
            evidence.cited_work_id
            for evidence in model_output.literature_evidence
            if evidence.cited_work_id not in selected_ids
        }
    )
    if bad_cited_ids:
        auto_flags.append(
            "literature_evidence_non_selected_works_dropped: " + ", ".join(bad_cited_ids)
        )
    literature_evidence: list[QuestionFormationLiteratureEvidence] = []
    evidence_bindings: list[QuestionFormationEvidenceBinding] = []
    literature_binding_roles = {
        QuestionFormationEvidenceBindingRole.LITERATURE_GAP,
        QuestionFormationEvidenceBindingRole.THEORETICAL_TENSION,
        QuestionFormationEvidenceBindingRole.METHOD_OR_CONSTRUCT_PRECEDENT,
    }
    dataset_or_question_binding_roles = {
        QuestionFormationEvidenceBindingRole.DATASET_OPPORTUNITY,
        QuestionFormationEvidenceBindingRole.QUESTION_FORMING_MOVE,
    }
    all_allowed_context_ids = (
        set().union(*allowed_contexts_by_work.values()) if allowed_contexts_by_work else set()
    )
    for evidence in model_output.literature_evidence:
        if evidence.cited_work_id not in selected_ids:
            continue
        allowed_context_ids = allowed_contexts_by_work.get(evidence.cited_work_id, set())
        valid_context_ids = [
            context_id
            for context_id in evidence.evidence_context_ids
            if context_id in allowed_context_ids
        ]
        removed_context_ids = sorted(set(evidence.evidence_context_ids) - allowed_context_ids)
        if removed_context_ids:
            auto_flags.append(
                f"{evidence.cited_work_id}: invalid_citation_context_ids_removed: "
                + ", ".join(removed_context_ids)
            )
        literature_evidence.append(
            QuestionFormationLiteratureEvidence.model_validate(
                {
                    **evidence.model_dump(mode="python"),
                    "evidence_context_ids": valid_context_ids,
                }
            )
        )
    if not literature_evidence and not citation_free_context:
        raise TraceDraftInsufficientEvidence(
            "draft formation trace has no reconcilable literature_evidence"
        )
    for index, binding in enumerate(model_output.evidence_bindings, start=1):
        valid_cited_work_ids = [
            cited_work_id
            for cited_work_id in binding.cited_work_ids
            if cited_work_id in selected_ids
        ]
        removed_cited_work_ids = sorted(set(binding.cited_work_ids) - selected_ids)
        if removed_cited_work_ids:
            auto_flags.append(
                f"evidence_binding_{index}: non_selected_cited_work_ids_removed: "
                + ", ".join(removed_cited_work_ids)
            )
        valid_source_span_ids = [
            span_id for span_id in binding.source_span_ids if span_id in valid_span_ids
        ]
        removed_source_span_ids = sorted(set(binding.source_span_ids) - valid_span_ids)
        if removed_source_span_ids:
            auto_flags.append(
                f"evidence_binding_{index}: invalid_evidence_span_ids_removed: "
                + ", ".join(removed_source_span_ids)
            )
        binding_allowed_context_ids = (
            set().union(
                *[
                    allowed_contexts_by_work.get(cited_work_id, set())
                    for cited_work_id in valid_cited_work_ids
                ]
            )
            if valid_cited_work_ids
            else all_allowed_context_ids
        )
        valid_context_ids = [
            context_id
            for context_id in binding.citation_context_ids
            if context_id in binding_allowed_context_ids
        ]
        # Deterministic reconciliation: a cross-work / invalid citation context is DROPPED and
        # flagged (like span ids), never re-prompted.
        removed_context_ids = sorted(
            set(binding.citation_context_ids) - binding_allowed_context_ids
        )
        if removed_context_ids:
            auto_flags.append(
                f"evidence_binding_{index}: invalid_or_cross_work_citation_contexts_removed: "
                + ", ".join(removed_context_ids)
            )
        # Keep the schema's paper-local role boundary hard, but reconcile an ordinary model mistake
        # before strict construction. Literature-side roles need literature locators; dataset and
        # question roles need source spans. Do not invent a locator or reinterpret the role: drop the
        # unsupported binding, flag it, and let the existing no-evidence path degrade this paper if
        # no valid binding remains.
        if (
            binding.role in literature_binding_roles
            and not citation_free_context
            and not (valid_cited_work_ids or valid_context_ids)
        ):
            auto_flags.append(
                f"evidence_binding_{index}: dropped_literature_role_without_citation_evidence"
            )
            continue
        if binding.role in dataset_or_question_binding_roles and not valid_source_span_ids:
            auto_flags.append(f"evidence_binding_{index}: dropped_dataset_role_without_source_span")
            continue
        # A binding with no remaining evidence locator is dropped (the schema forbids an empty one).
        if not (valid_source_span_ids or valid_cited_work_ids or valid_context_ids):
            auto_flags.append(f"evidence_binding_{index}: dropped_no_resolvable_locator")
            continue
        evidence_bindings.append(
            QuestionFormationEvidenceBinding.model_validate(
                {
                    **binding.model_dump(mode="python"),
                    "cited_work_ids": valid_cited_work_ids,
                    "source_span_ids": valid_source_span_ids,
                    "citation_context_ids": valid_context_ids,
                }
            )
        )
    if not evidence_bindings:
        raise TraceDraftInsufficientEvidence(
            "draft formation trace has no reconcilable evidence_bindings"
        )
    # Consistency (schema invariant): every literature_evidence cited work must appear in a surviving
    # binding. After dropping mis-transcribed binding references, drop any literature_evidence whose
    # cited work is no longer covered by a binding (flag it); if that empties it, degrade honestly.
    binding_cited_ids = {
        cited_work_id for binding in evidence_bindings for cited_work_id in binding.cited_work_ids
    }
    covered_literature_evidence = [
        evidence for evidence in literature_evidence if evidence.cited_work_id in binding_cited_ids
    ]
    dropped_literature_ids = sorted(
        {
            evidence.cited_work_id
            for evidence in literature_evidence
            if evidence.cited_work_id not in binding_cited_ids
        }
    )
    if dropped_literature_ids:
        auto_flags.append(
            "literature_evidence_without_binding_dropped: " + ", ".join(dropped_literature_ids)
        )
    literature_evidence = covered_literature_evidence
    if not literature_evidence and not citation_free_context:
        raise TraceDraftInsufficientEvidence(
            "draft formation trace has no literature_evidence backed by an evidence_binding"
        )
    # D2(i): union the (already-valid) binding source_span_ids into the top-level evidence_span_ids —
    # mirror the human import path (this file's build_reviewed_formation_trace_drafts) so a trace whose
    # spans live only inside its bindings does not look span-empty to the downstream usability check.
    top_level_spans = list(
        dict.fromkeys(
            [span_id for span_id in model_output.evidence_span_ids if span_id in valid_span_ids]
            + [span_id for binding in evidence_bindings for span_id in binding.source_span_ids]
        )
    )
    trace = QuestionFormationTrace.model_validate(
        {
            **model_output.model_dump(mode="python"),
            "trace_id": model_output.trace_id
            or f"trace-draft-{paper_case.paper_case_id}-{stable_hash(model_output.model_dump(mode='json'))[:8]}",
            "evidence_span_ids": top_level_spans,
            "local_literature_context_id": trace_context.local_literature_context_id,
            "local_literature_context_digest": trace_context.local_literature_context_digest,
            "key_cited_work_ids": trace_context.key_cited_work_ids,
            "literature_evidence": literature_evidence,
            "evidence_bindings": evidence_bindings,
            "review_status": QuestionFormationTraceReviewStatus.DRAFT,
        }
    )
    literature_issues = validate_trace_literature_evidence(
        trace=trace,
        trace_context=trace_context,
    )
    if literature_issues:
        raise TraceDraftInsufficientEvidence("; ".join(literature_issues))
    return trace, auto_flags


def _draft_payload(
    *,
    paper_case: PaperCase,
    trace_context: PaperLocalLiteratureTraceContext,
) -> dict[str, Any]:
    allowed_contexts_by_work = {
        work.cited_work_id: work.evidence_context_ids for work in trace_context.selected_cited_works
    }
    instruction = "Draft one public QuestionFormationTrace for expert review."
    if not trace_context.local_literature_context_id.strip():
        # This paper's citation-importance selection chose nothing, so `allowed_cited_work_ids` is
        # empty. The prompt asks unconditionally for at least one literature-side binding, and
        # without this note a compliant model faces an instruction it has no allowed locator for --
        # it would either invent a cited-work id (rejected downstream) or omit the binding, and a
        # trace with no literature-side binding cannot be promoted past DRAFT
        # (question_pattern.py:181-184). Saying so in the PAYLOAD rather than the prompt keeps the
        # prompt a stable contract: this is a fact about one paper, not a change of task.
        instruction += (
            " No selected cited works are available for this paper, so cite none: leave"
            " literature_evidence empty and use no cited work or citation context IDs. Still"
            " provide at least one literature-side evidence binding, backed by allowed PaperCase"
            " source span IDs. Never invent an identifier to satisfy a field."
        )
    return {
        "prompt_version": QUESTION_FORMATION_TRACE_DRAFTER_PROMPT_VERSION,
        "instruction": instruction,
        "paper_case": paper_case.model_dump(
            mode="json",
            exclude={"formation_trace"},
        ),
        "selected_paper_local_literature": trace_context.model_dump(mode="json"),
        "allowed_cited_work_ids": trace_context.key_cited_work_ids,
        "allowed_context_ids_by_cited_work": allowed_contexts_by_work,
        "allowed_evidence_span_ids": [
            span.source_span_id for span in paper_case.evidence_spans if span.source_span_id
        ],
    }


def _reviewed_cases(root: Path, paper_ids: list[str]) -> list[PaperCase]:
    if paper_ids:
        return [
            load_model(root / "cases" / "reviewed" / f"{paper_id}.paper_case.yaml", PaperCase)
            for paper_id in paper_ids
        ]
    return PaperCaseIndex.from_corpus(root).cases


def _default_prompt_path() -> Path:
    return resolve_asset(
        Path("prompts") / Path(QUESTION_FORMATION_TRACE_DRAFTER_PROMPT_VERSION).with_suffix(".md")
    )
