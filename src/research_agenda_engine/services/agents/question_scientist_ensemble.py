from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...io import dump_data, load_model
from ...provenance import stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas.question_scientist_context_v2 import QuestionScientistContextPayloadV2
from ...schemas.question_seed import (
    QuestionScientistEnsembleManifest,
    QuestionScientistProposerBranch,
    QuestionSeed,
    QuestionSeedBatch,
    QuestionSeedDuplicateCluster,
    QuestionSeedReviewDecision,
    QuestionSeedReviewDecisionBatch,
    QuestionSeedReviewItem,
    QuestionSeedReviewPack,
    QuestionSeedReviewStatus,
    QuestionSeedShortlistManifest,
    ShortlistedQuestionSeed,
)
from .question_scientist import (
    QUESTION_SCIENTIST_PROMPT_VERSION,
    generate_question_seed_batch,
    write_question_seed_batch,
)

LARGE_REVIEW_PACK_THRESHOLD = 24


class QuestionSeedReviewPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack: QuestionSeedReviewPack
    decision_template: QuestionSeedReviewDecisionBatch
    markdown: str


class QuestionSeedReviewImportResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shortlist: QuestionSeedShortlistManifest | None = None
    errors: list[str] = Field(default_factory=list)


def generate_question_seed_ensemble(
    *,
    provider: StructuredModelProvider,
    context_payload: QuestionScientistContextPayloadV2,
    branches: int = 3,
    seeds_per_branch: int = 8,
    corpus_root: str | Path = "corpus",
) -> QuestionScientistEnsembleManifest:
    if branches < 3:
        raise ValueError("R5-004B ensemble generation requires at least 3 proposer branches")
    if seeds_per_branch < 1 or seeds_per_branch > 20:
        raise ValueError("seeds_per_branch must be between 1 and 20")
    pattern_ids = [card.pattern_id for card in context_payload.paperbank_patterns.pattern_cards]
    branch_specs: list[tuple[str, list[str], list[str], str]] = []
    seen_subset_digests: set[str] = set()
    for branch_index in range(1, branches + 1):
        proposer_branch_id = f"qsc-proposer-{branch_index:03d}"
        selected_pattern_ids = _select_pattern_ids(pattern_ids, branch_index, branches)
        selected_source_case_ids = _selected_source_case_ids(context_payload, selected_pattern_ids)
        subset_digest = _context_subset_digest(
            context_digest=context_payload.context_digest,
            selected_pattern_ids=selected_pattern_ids,
            selected_source_case_ids=selected_source_case_ids,
        )
        if subset_digest in seen_subset_digests:
            raise ValueError(
                "Question Scientist ensemble contains duplicate scientific context subsets"
            )
        seen_subset_digests.add(subset_digest)
        branch_specs.append(
            (
                proposer_branch_id,
                selected_pattern_ids,
                selected_source_case_ids,
                subset_digest,
            )
        )
    proposer_branches: list[QuestionScientistProposerBranch] = []
    for (
        proposer_branch_id,
        selected_pattern_ids,
        selected_source_case_ids,
        subset_digest,
    ) in branch_specs:
        batch = generate_question_seed_batch(
            provider=provider,
            context_payload=context_payload,
            seed_count=seeds_per_branch,
            selected_pattern_ids=selected_pattern_ids,
            proposer_branch_id=proposer_branch_id,
            context_subset_digest=subset_digest,
        )
        batch = _rename_ensemble_seed_ids(batch, proposer_branch_id)
        batch_path = write_question_seed_batch(batch, corpus_root=corpus_root)
        proposer_branches.append(
            QuestionScientistProposerBranch(
                proposer_branch_id=proposer_branch_id,
                context_id=context_payload.context_id,
                context_digest=context_payload.context_digest,
                context_subset_digest=subset_digest,
                selected_pattern_ids=selected_pattern_ids,
                selected_source_paper_case_ids=selected_source_case_ids,
                seed_count_requested=seeds_per_branch,
                batch_id=batch.batch_id,
                batch_path=str(batch_path),
                origin_provider_id=batch.origin_provider_id,
                prompt_version=batch.prompt_version,
                input_digest=batch.input_digest,
            )
        )
    ensemble = QuestionScientistEnsembleManifest(
        ensemble_id=f"question-scientist-ensemble-{stable_hash([branch.model_dump(mode='json') for branch in proposer_branches])[:12]}",
        context_id=context_payload.context_id,
        context_digest=context_payload.context_digest,
        prompt_version=QUESTION_SCIENTIST_PROMPT_VERSION,
        proposer_branches=proposer_branches,
    )
    write_question_scientist_ensemble_manifest(ensemble, corpus_root=corpus_root)
    return ensemble


def write_question_scientist_ensemble_manifest(
    manifest: QuestionScientistEnsembleManifest,
    *,
    corpus_root: str | Path = "corpus",
) -> Path:
    root = Path(corpus_root) / "question_seeds" / "ensemble"
    return dump_data(manifest, root / f"{manifest.ensemble_id}.question_scientist_ensemble.yaml")


def load_question_seed_batches_from_ensemble(
    manifest: QuestionScientistEnsembleManifest,
) -> list[QuestionSeedBatch]:
    return [
        load_model(Path(branch.batch_path), QuestionSeedBatch)
        for branch in manifest.proposer_branches
    ]


def prepare_question_seed_review(
    *,
    batches: list[QuestionSeedBatch],
    ensemble_manifest: QuestionScientistEnsembleManifest | None = None,
) -> QuestionSeedReviewPreparation:
    if not batches:
        raise ValueError("QuestionSeed review pack requires at least one batch")
    context_ids = {batch.context_id for batch in batches}
    context_digests = {batch.context_digest for batch in batches}
    if len(context_ids) != 1 or len(context_digests) != 1:
        raise ValueError("QuestionSeed review batches must share context_id and context_digest")
    source_batch_ids = [batch.batch_id for batch in batches]
    branch_by_batch = (
        {
            branch.batch_id: branch.proposer_branch_id
            for branch in ensemble_manifest.proposer_branches
        }
        if ensemble_manifest
        else {}
    )
    seeds: list[tuple[QuestionSeed, str, str]] = []
    for batch in batches:
        for seed in batch.seeds:
            seeds.append((seed, batch.batch_id, branch_by_batch.get(batch.batch_id, "")))
    duplicate_clusters, auto_flags = cluster_question_seeds([seed for seed, _, _ in seeds])
    items = [
        QuestionSeedReviewItem(
            review_item_id=f"review-candidate-{index:03d}",
            seed=seed,
            source_batch_id=batch_id,
            proposer_branch_id=branch_id,
            duplicate_cluster_id=_cluster_id_for_seed(seed.question_seed_id, duplicate_clusters),
            duplicate_seed_ids=_duplicate_seed_ids(seed.question_seed_id, duplicate_clusters),
            auto_flags=auto_flags.get(seed.question_seed_id, []),
        )
        for index, (seed, batch_id, branch_id) in enumerate(seeds, start=1)
    ]
    pack = QuestionSeedReviewPack(
        pack_id=f"question-seed-review-{stable_hash([item.seed.model_dump(mode='json') for item in items])[:12]}",
        context_id=next(iter(context_ids)),
        context_digest=next(iter(context_digests)),
        source_batch_ids=source_batch_ids,
        source_ensemble_id=ensemble_manifest.ensemble_id if ensemble_manifest else "",
        duplicate_clusters=duplicate_clusters,
        items=items,
        instructions=[
            "Review scientific value, novelty, and whether the seed is worth dataset-planning.",
            "Shortlisting does not certify feasibility and does not create a QuestionBranch.",
            "Reject generic decoding benchmarks, pure method benchmarks, or seeds with weak scientific consequences.",
        ],
    )
    decisions = QuestionSeedReviewDecisionBatch(
        decision_batch_id=f"{pack.pack_id}-decisions-template",
        pack_id=pack.pack_id,
        decisions=[
            QuestionSeedReviewDecision(
                review_item_id=item.review_item_id,
                question_seed_id=item.seed.question_seed_id,
            )
            for item in items
        ],
    )
    return QuestionSeedReviewPreparation(
        pack=pack,
        decision_template=decisions,
        markdown=render_question_seed_review_markdown(pack),
    )


def write_question_seed_review_outputs(
    preparation: QuestionSeedReviewPreparation,
    *,
    corpus_root: str | Path = "corpus",
) -> dict[str, Path]:
    root = Path(corpus_root) / "question_seeds" / "review"
    pack_path = dump_data(preparation.pack, root / "question_seed_review_pack.yaml")
    template_path = dump_data(
        preparation.decision_template,
        root / "question_seed_decisions.template.yaml",
    )
    decision_path = dump_data(
        preparation.decision_template,
        root / "question_seed_decisions.yaml",
    )
    markdown_path = root / "question_seed_review.md"
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(preparation.markdown, encoding="utf-8")
    return {
        "review_pack": pack_path,
        "decision_template": template_path,
        "decisions": decision_path,
        "markdown": markdown_path,
    }


def import_question_seed_reviews(
    *,
    pack: QuestionSeedReviewPack,
    decisions: QuestionSeedReviewDecisionBatch,
    require_complete: bool = True,
) -> QuestionSeedReviewImportResult:
    errors: list[str] = []
    if decisions.pack_id != pack.pack_id:
        raise ValueError("QuestionSeedReviewDecisionBatch pack_id does not match review pack")
    item_by_seed = {item.seed.question_seed_id: item for item in pack.items}
    decision_by_seed = {decision.question_seed_id: decision for decision in decisions.decisions}
    unknown = sorted(set(decision_by_seed) - set(item_by_seed))
    if unknown:
        errors.append("QuestionSeed decisions reference unknown seed IDs: " + ", ".join(unknown))
    if require_complete:
        missing = sorted(set(item_by_seed) - set(decision_by_seed))
        if missing:
            errors.append("Missing QuestionSeed review decisions: " + ", ".join(missing))
    shortlisted: list[ShortlistedQuestionSeed] = []
    rejected: list[str] = []
    needs_revision: list[str] = []
    deferred: list[str] = []
    for seed_id, item in item_by_seed.items():
        decision = decision_by_seed.get(seed_id)
        if decision is None:
            continue
        if not decision.reviewer.strip() or not decision.notes.strip():
            errors.append(f"{seed_id}: QuestionSeed decision is unreviewed")
            continue
        if decision.review_item_id != item.review_item_id:
            errors.append(f"{seed_id}: decision review_item_id does not match review pack")
            continue
        if decision.status == QuestionSeedReviewStatus.SHORTLISTED:
            shortlisted.append(
                ShortlistedQuestionSeed(
                    seed=item.seed,
                    review=decision,
                    duplicate_cluster_id=item.duplicate_cluster_id,
                    source_batch_id=item.source_batch_id,
                )
            )
        elif decision.status == QuestionSeedReviewStatus.REJECTED:
            rejected.append(seed_id)
        elif decision.status == QuestionSeedReviewStatus.NEEDS_REVISION:
            needs_revision.append(seed_id)
        else:
            deferred.append(seed_id)
    if errors:
        return QuestionSeedReviewImportResult(errors=errors)
    shortlist = QuestionSeedShortlistManifest(
        shortlist_id=f"question-seed-shortlist-{stable_hash({'pack': pack.pack_id, 'decisions': decisions.model_dump(mode='json')})[:12]}",
        pack_id=pack.pack_id,
        context_id=pack.context_id,
        context_digest=pack.context_digest,
        shortlisted=shortlisted,
        rejected_seed_ids=rejected,
        needs_revision_seed_ids=needs_revision,
        deferred_seed_ids=deferred,
    )
    return QuestionSeedReviewImportResult(shortlist=shortlist)


def write_question_seed_shortlist(
    shortlist: QuestionSeedShortlistManifest,
    *,
    corpus_root: str | Path = "corpus",
) -> Path:
    root = Path(corpus_root) / "question_seeds" / "reviewed"
    return dump_data(shortlist, root / "question_seed_shortlist_manifest.yaml")


def render_question_seed_review_markdown(pack: QuestionSeedReviewPack) -> str:
    label_by_seed_id = {
        item.seed.question_seed_id: _candidate_label(index)
        for index, item in enumerate(pack.items, start=1)
    }
    representative_seed_ids = _representative_seed_ids(pack)
    lines = [
        f"# QuestionSeed Review Pack: {pack.pack_id}",
        "",
        "Boundary: this pack supports human scientific shortlisting only. It does not "
        "certify dataset feasibility, create QuestionBranches, generate QuestionCards, "
        "or authorize AnalysisContracts/execution.",
        "",
        f"- Context ID: `{pack.context_id}`",
        f"- Source batches: {', '.join(pack.source_batch_ids)}",
        f"- Raw QuestionSeeds: {len(pack.items)}",
        f"- Representative review candidates: {len(representative_seed_ids)}",
        f"- Duplicate clusters: {len(pack.duplicate_clusters)}",
        "",
    ]
    if len(pack.items) > LARGE_REVIEW_PACK_THRESHOLD:
        lines.extend(
            [
                "**Large review pack:** prioritize representative candidates and use duplicate "
                "cluster notes to avoid spending equal attention on near-identical proposals. "
                "The YAML review pack retains every raw QuestionSeed and full provenance.",
                "",
            ]
        )
    lines.extend(
        [
            "## Review Instructions",
            "",
            *[f"- {instruction}" for instruction in pack.instructions],
            "",
        ]
    )
    if pack.duplicate_clusters:
        lines.extend(["## Duplicate Cluster Guide", ""])
        for cluster in pack.duplicate_clusters:
            representative = label_by_seed_id.get(
                cluster.representative_seed_id,
                cluster.representative_seed_id,
            )
            siblings = [
                label_by_seed_id.get(seed_id, seed_id)
                for seed_id in cluster.seed_ids
                if seed_id != cluster.representative_seed_id
            ]
            lines.append(
                f"- `{cluster.cluster_id}`: representative {representative}; "
                f"sibling candidates {', '.join(siblings) or 'none'}. {cluster.rationale}"
            )
        lines.append("")
    for index, item in enumerate(pack.items, start=1):
        seed = item.seed
        candidate_label = label_by_seed_id[seed.question_seed_id]
        duplicate_labels = [
            label_by_seed_id.get(seed_id, seed_id) for seed_id in item.duplicate_seed_ids
        ]
        auto_flags = [_blind_seed_id_references(flag, label_by_seed_id) for flag in item.auto_flags]
        review_role = (
            "representative"
            if seed.question_seed_id in representative_seed_ids
            else "duplicate sibling"
        )
        lines.extend(
            [
                f"## {index}. {candidate_label}",
                "",
                f"- Review item ID: `{item.review_item_id}`",
                f"- Review role: {review_role}",
                f"- Duplicate cluster: `{item.duplicate_cluster_id or 'none'}`",
                f"- Duplicate candidates: {', '.join(duplicate_labels) or 'none'}",
                f"- Auto flags: {'; '.join(auto_flags) or 'none'}",
                "",
                "### Question",
                "",
                seed.question,
                "",
                "### Scientific Tension",
                "",
                seed.scientific_tension,
                "",
                "### Why It Matters",
                "",
                seed.why_scientifically_important,
                "",
                "### Novelty And Closest Known Work",
                "",
                f"- Novelty hypothesis: {seed.novelty_hypothesis}",
                f"- Closest known work: {', '.join(seed.closest_known_work) or 'none listed'}",
                "",
                "### Dataset Leverage Hypothesis",
                "",
                seed.dataset_leverage_hypothesis,
                "",
                "### Competing Explanations",
                "",
                *[f"- {value}" for value in seed.competing_explanations],
                "",
                "### Discriminating Observation",
                "",
                seed.discriminating_observation,
                "",
                "### Outcome Meanings",
                "",
                f"- Positive: {seed.positive_result_consequence}",
                f"- Negative: {seed.negative_result_consequence}",
                f"- Null: {seed.null_result_consequence}",
                "",
                "### Ambiguities, Assumptions, And Planning Challenges",
                "",
                f"- Ambiguous constructs: {'; '.join(seed.ambiguous_constructs) or 'none listed'}",
                f"- Dataset assumptions: {'; '.join(seed.assumptions_about_dataset) or 'none listed'}",
                f"- Implementation challenges: {'; '.join(seed.likely_implementation_challenges) or 'none listed'}",
                "",
                "### Source Lineage",
                "",
                f"- Source pattern IDs: {', '.join(seed.source_pattern_ids) or 'none'}",
                f"- Source paper case IDs: {', '.join(seed.source_paper_case_ids) or 'none'}",
                f"- Relevant literature claims: {'; '.join(seed.relevant_literature_claims) or 'none listed'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def cluster_question_seeds(
    seeds: list[QuestionSeed],
) -> tuple[list[QuestionSeedDuplicateCluster], dict[str, list[str]]]:
    parent = {seed.question_seed_id: seed.question_seed_id for seed in seeds}
    auto_flags: dict[str, list[str]] = {seed.question_seed_id: [] for seed in seeds}

    def find(seed_id: str) -> str:
        while parent[seed_id] != seed_id:
            parent[seed_id] = parent[parent[seed_id]]
            seed_id = parent[seed_id]
        return seed_id

    def union(left: str, right: str) -> None:
        parent[find(right)] = find(left)

    for index, left in enumerate(seeds):
        for right in seeds[index + 1 :]:
            question_sim = _jaccard(_tokens(left.question), _tokens(right.question))
            tension_sim = _jaccard(
                _tokens(left.scientific_tension + " " + left.discriminating_observation),
                _tokens(right.scientific_tension + " " + right.discriminating_observation),
            )
            combined_sim = _jaccard(_seed_tokens(left), _seed_tokens(right))
            phrase_sim = _jaccard(_phrase_tokens(left), _phrase_tokens(right))
            source_overlap = bool(set(left.source_pattern_ids) & set(right.source_pattern_ids))
            if (
                (combined_sim >= 0.62 and tension_sim >= 0.50)
                or (question_sim >= 0.78 and tension_sim >= 0.45)
                or (source_overlap and question_sim >= 0.82 and tension_sim >= 0.40)
                or (
                    phrase_sim >= 0.36
                    and tension_sim >= 0.28
                    and (source_overlap or question_sim >= 0.38)
                )
                or (
                    source_overlap
                    and combined_sim >= 0.30
                    and tension_sim >= 0.26
                    and question_sim >= 0.25
                )
            ):
                union(left.question_seed_id, right.question_seed_id)
            elif question_sim >= 0.65 and tension_sim < 0.35:
                flag = (
                    "near wording overlap with a different scientific tension; "
                    "kept separate for review"
                )
                auto_flags[left.question_seed_id].append(f"{right.question_seed_id}: {flag}")
                auto_flags[right.question_seed_id].append(f"{left.question_seed_id}: {flag}")
    grouped: dict[str, list[str]] = {}
    for seed in seeds:
        grouped.setdefault(find(seed.question_seed_id), []).append(seed.question_seed_id)
    clusters = [
        QuestionSeedDuplicateCluster(
            cluster_id=f"dup-cluster-{stable_hash(seed_ids)[:8]}",
            seed_ids=seed_ids,
            representative_seed_id=seed_ids[0],
            rationale="Source-aware lexical/tension overlap suggests these seeds may represent the same scientific proposal.",
        )
        for seed_ids in grouped.values()
        if len(seed_ids) > 1
    ]
    return clusters, auto_flags


def _select_pattern_ids(pattern_ids: list[str], branch_index: int, branches: int) -> list[str]:
    if not pattern_ids:
        raise ValueError("Question Scientist ensemble requires reviewed pattern IDs")
    if len(pattern_ids) == 1:
        return pattern_ids
    window = max(2, min(len(pattern_ids), (len(pattern_ids) + 1) // 2))
    offset = (branch_index - 1) % len(pattern_ids)
    rotated = pattern_ids[offset:] + pattern_ids[:offset]
    return rotated[:window]


def _context_subset_digest(
    *,
    context_digest: str,
    selected_pattern_ids: list[str],
    selected_source_case_ids: list[str],
) -> str:
    return stable_hash(
        {
            "context_digest": context_digest,
            "selected_pattern_ids": selected_pattern_ids,
            "selected_source_paper_case_ids": selected_source_case_ids,
        }
    )


def _selected_source_case_ids(
    context_payload: QuestionScientistContextPayloadV2,
    selected_pattern_ids: list[str],
) -> list[str]:
    selected = set(selected_pattern_ids)
    case_ids: set[str] = set()
    for card in context_payload.paperbank_patterns.pattern_cards:
        if card.pattern_id not in selected:
            continue
        for trace in card.formation_trace_summaries:
            case_ids.add(trace.source_paper_case_id)
    return sorted(case_ids)


def _rename_ensemble_seed_ids(
    batch: QuestionSeedBatch,
    proposer_branch_id: str,
) -> QuestionSeedBatch:
    renamed = [
        seed.model_copy(
            update={
                "question_seed_id": f"qseed-{proposer_branch_id.removeprefix('qsc-proposer-')}-{index:03d}"
            }
        )
        for index, seed in enumerate(batch.seeds, start=1)
    ]
    payload = batch.model_dump(mode="python")
    payload["seeds"] = renamed
    payload["batch_id"] = (
        "question-seed-batch-"
        + stable_hash(
            {
                "context_digest": batch.context_digest,
                "input_digest": batch.input_digest,
                "proposer_branch_id": proposer_branch_id,
                "seeds": [seed.model_dump(mode="json") for seed in renamed],
            }
        )[:12]
    )
    return QuestionSeedBatch.model_validate(payload)


def _candidate_label(index: int) -> str:
    return f"Candidate {index:03d}"


def _representative_seed_ids(pack: QuestionSeedReviewPack) -> set[str]:
    clustered_seed_ids = {
        seed_id for cluster in pack.duplicate_clusters for seed_id in cluster.seed_ids
    }
    representative_ids = {cluster.representative_seed_id for cluster in pack.duplicate_clusters}
    unclustered_ids = {
        item.seed.question_seed_id
        for item in pack.items
        if item.seed.question_seed_id not in clustered_seed_ids
    }
    return representative_ids | unclustered_ids


def _blind_seed_id_references(text: str, label_by_seed_id: dict[str, str]) -> str:
    blind_text = text
    for seed_id, label in sorted(label_by_seed_id.items(), key=lambda item: -len(item[0])):
        blind_text = blind_text.replace(seed_id, label)
    return blind_text


def _cluster_id_for_seed(
    seed_id: str,
    clusters: list[QuestionSeedDuplicateCluster],
) -> str:
    for cluster in clusters:
        if seed_id in cluster.seed_ids:
            return cluster.cluster_id
    return ""


def _duplicate_seed_ids(
    seed_id: str,
    clusters: list[QuestionSeedDuplicateCluster],
) -> list[str]:
    for cluster in clusters:
        if seed_id in cluster.seed_ids:
            return [other for other in cluster.seed_ids if other != seed_id]
    return []


def _seed_tokens(seed: QuestionSeed) -> set[str]:
    return _tokens(
        " ".join(
            [
                seed.question,
                seed.scientific_tension,
                seed.novelty_hypothesis,
                seed.discriminating_observation,
                " ".join(seed.competing_explanations),
            ]
        )
    )


def _phrase_tokens(seed: QuestionSeed) -> set[str]:
    tokens = list(
        _ordered_tokens(
            " ".join(
                [
                    seed.question,
                    seed.scientific_tension,
                    seed.discriminating_observation,
                ]
            )
        )
    )
    bigrams = {" ".join(tokens[index : index + 2]) for index in range(len(tokens) - 1)}
    trigrams = {" ".join(tokens[index : index + 3]) for index in range(len(tokens) - 2)}
    return bigrams | trigrams


def _tokens(text: str) -> set[str]:
    return set(_ordered_tokens(text))


def _ordered_tokens(text: str) -> list[str]:
    stop = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "into",
        "does",
        "are",
        "their",
        "through",
    }
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in stop
    ]


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)
