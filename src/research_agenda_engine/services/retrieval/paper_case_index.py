from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

from ...io import load_model
from ...schemas.paper_case import PaperCase, PaperCorpusManifest, PaperType
from ...schemas.review_authority import is_accepted_authority
from ...schemas.topic_literature import (
    PaperCaseRetrievalHit,
    PaperCaseRetrievalQuery,
    PaperCaseRetrievalResult,
)


@dataclass(frozen=True)
class PaperCaseCorpusIssue:
    code: str
    message: str


class PaperCaseIndex:
    """Reviewed PaperCase index used by Phase-2 proposers."""

    def __init__(self, cases: list[PaperCase]):
        self.cases = cases

    @classmethod
    def from_corpus(cls, corpus_root: str | Path = "corpus") -> PaperCaseIndex:
        root = Path(corpus_root)
        manifest = load_model(root / "corpus_manifest.yaml", PaperCorpusManifest)
        cases: list[PaperCase] = []
        for entry in manifest.entries:
            # Accept either honest authority (AI_REVIEWED or EXPERT_REVIEWED); see review_authority.py.
            if not is_accepted_authority(entry.status):
                continue
            case_path = Path(entry.case_path)
            if not case_path.is_absolute():
                case_path = root.parent / case_path
            paper_case = load_model(case_path, PaperCase)
            if not is_accepted_authority(paper_case.review.status):
                raise ValueError(f"Manifest reviewed entry is not accepted-authority: {case_path}")
            if paper_case.evidence_requests:
                raise ValueError(f"Reviewed PaperCase still has evidence_requests: {case_path}")
            cases.append(paper_case)
        return cls(cases)

    def by_id(self, paper_case_id: str) -> PaperCase:
        for case in self.cases:
            if case.paper_case_id == paper_case_id:
                return case
        raise KeyError(paper_case_id)


class PaperCaseRetriever:
    def __init__(self, index: PaperCaseIndex):
        self.index = index

    def retrieve(self, query: PaperCaseRetrievalQuery) -> PaperCaseRetrievalResult:
        excluded = set(query.exclude_paper_case_ids)
        allowed_types = set(query.paper_types)
        candidates = [
            case
            for case in self.index.cases
            if case.paper_case_id not in excluded
            and (not allowed_types or case.paper_type in allowed_types)
        ]
        scored = [
            _score_case(
                case,
                topic_terms=query.topic_terms,
                epistemic_moves=query.epistemic_moves,
            )
            for case in candidates
        ]
        selected: list[PaperCaseRetrievalHit] = []
        seen_types: set[PaperType] = set()
        for case, hit in sorted(scored, key=lambda item: (-item[1].score, item[0].paper_case_id)):
            if case.paper_type not in seen_types:
                hit.diversity_bonus = 0.1
                hit.score += hit.diversity_bonus
            selected.append(hit)
            seen_types.add(case.paper_type)
            if len(selected) >= query.limit:
                break
        selected.sort(key=lambda item: (-item.score, item.paper_case_id))
        return PaperCaseRetrievalResult(
            query=query,
            hits=selected,
            reviewed_case_count=len(self.index.cases),
        )


def validate_paper_case_corpus(corpus_root: str | Path = "corpus") -> list[PaperCaseCorpusIssue]:
    root = Path(corpus_root)
    manifest = load_model(root / "corpus_manifest.yaml", PaperCorpusManifest)
    reviewed_dir = root / "cases" / "reviewed"
    reviewed_paths = sorted(reviewed_dir.glob("*.paper_case.yaml"))
    reviewed_cases = [load_model(path, PaperCase) for path in reviewed_paths]
    manifest_by_id = {entry.paper_id: entry for entry in manifest.entries}
    registry_ids = _registry_ids(root / "paper_registry.csv")
    issues: list[PaperCaseCorpusIssue] = []

    for case in reviewed_cases:
        entry = manifest_by_id.get(case.paper_case_id)
        if entry is None:
            issues.append(
                PaperCaseCorpusIssue(
                    code="reviewed_case_missing_manifest_entry",
                    message=f"{case.paper_case_id} is reviewed but absent from corpus manifest.",
                )
            )
        elif not is_accepted_authority(entry.status):
            issues.append(
                PaperCaseCorpusIssue(
                    code="manifest_status_not_accepted_authority",
                    message=f"{case.paper_case_id} manifest status is {entry.status}.",
                )
            )
        if case.paper_case_id not in registry_ids:
            issues.append(
                PaperCaseCorpusIssue(
                    code="reviewed_case_missing_registry_row",
                    message=f"{case.paper_case_id} is reviewed but absent from registry.",
                )
            )
        if not is_accepted_authority(case.review.status):
            issues.append(
                PaperCaseCorpusIssue(
                    code="reviewed_artifact_status_mismatch",
                    message=f"{case.paper_case_id} reviewed artifact is {case.review.status}.",
                )
            )
        if case.evidence_requests:
            issues.append(
                PaperCaseCorpusIssue(
                    code="reviewed_case_has_evidence_requests",
                    message=f"{case.paper_case_id} still has evidence_requests.",
                )
            )

    reviewed_ids = {case.paper_case_id for case in reviewed_cases}
    for entry in manifest.entries:
        if is_accepted_authority(entry.status) and entry.paper_id not in reviewed_ids:
            issues.append(
                PaperCaseCorpusIssue(
                    code="manifest_reviewed_entry_missing_artifact",
                    message=f"{entry.paper_id} is reviewed in manifest but has no artifact.",
                )
            )
    return issues


def _score_case(
    case: PaperCase, *, topic_terms: list[str], epistemic_moves: list[str]
) -> tuple[PaperCase, PaperCaseRetrievalHit]:
    topic_tokens = _tokens(" ".join(topic_terms))
    move_tokens = _tokens(" ".join(epistemic_moves))
    topic_text = " ".join(
        [
            " ".join(case.topic_tags),
            case.dataset_description.dataset_name,
            case.dataset_description.population,
            " ".join(case.dataset_description.modalities),
            case.knowledge_state.unresolved_tension,
            case.scientific_question.original_question,
        ]
    )
    design_text = " ".join(
        [
            case.dataset_description.task_or_design,
            " ".join(case.dataset_description.measurements),
            " ".join(case.dataset_description.relevant_affordances),
            case.question_design.why_dataset_can_answer,
        ]
    )
    move_text = " ".join(
        [
            case.question_design.epistemic_move,
            case.question_design.novelty_relative_to_parent_dataset,
            " ".join(case.question_design.non_transferable_details),
        ]
    )
    topic_score = _overlap_score(topic_tokens, _tokens(topic_text))
    design_score = _overlap_score(topic_tokens, _tokens(design_text)) * 0.6
    move_score = _overlap_score(move_tokens, _tokens(move_text))
    base = topic_score + design_score + move_score
    if not topic_tokens and not move_tokens:
        base = 0.5
    return (
        case,
        PaperCaseRetrievalHit(
            paper_case_id=case.paper_case_id,
            paper_type=case.paper_type,
            score=round(base, 4),
            topic_score=round(topic_score, 4),
            design_score=round(design_score, 4),
            epistemic_move_score=round(move_score, 4),
            rationale="Lexical overlap over reviewed PaperCase topic, design, and epistemic move fields.",
        ),
    )


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in {"the", "and", "for", "with", "from"}
    }


def _overlap_score(query_tokens: set[str], document_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0
    return len(query_tokens & document_tokens) / len(query_tokens)


def _registry_ids(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["paper_id"] for row in csv.DictReader(handle)}
