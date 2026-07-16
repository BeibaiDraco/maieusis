from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ...io import load_model
from ...schemas.question_pattern import (
    QuestionPatternBankManifest,
    QuestionPatternCard,
)
from ...schemas.review_authority import is_accepted_authority


@dataclass(frozen=True)
class QuestionPatternRetrievalHit:
    pattern: QuestionPatternCard
    score: float
    rationale: str


class QuestionPatternBank:
    def __init__(self, patterns: list[QuestionPatternCard]):
        self.patterns = patterns

    @classmethod
    def from_corpus(
        cls,
        corpus_root: str | Path = "corpus",
        *,
        serious_mode: bool = True,
    ) -> QuestionPatternBank:
        root = Path(corpus_root)
        manifest = load_model(root / "question_pattern_manifest.yaml", QuestionPatternBankManifest)
        patterns: list[QuestionPatternCard] = []
        for entry in manifest.entries:
            # Accept either honest authority (AI_REVIEWED or EXPERT_REVIEWED); see review_authority.py.
            if serious_mode and not is_accepted_authority(entry.status):
                continue
            pattern = load_model(
                _resolve_pattern_path(root, entry.pattern_path), QuestionPatternCard
            )
            if serious_mode and not pattern.is_proposal_ready:
                continue
            patterns.append(pattern)
        if serious_mode and not patterns:
            raise ValueError(
                "serious QuestionPatternBank retrieval requires at least one "
                "expert-reviewed proposal-ready pattern"
            )
        return cls(patterns)

    def retrieve(
        self,
        query_terms: list[str],
        *,
        limit: int = 8,
        serious_mode: bool = True,
    ) -> list[QuestionPatternRetrievalHit]:
        candidates = [
            pattern
            for pattern in self.patterns
            if not serious_mode or is_accepted_authority(pattern.review_status)
        ]
        scored = [
            QuestionPatternRetrievalHit(
                pattern=pattern,
                score=_score_pattern(pattern, query_terms),
                rationale="Lexical overlap over reviewed question-pattern fields.",
            )
            for pattern in candidates
        ]
        return sorted(scored, key=lambda hit: (-hit.score, hit.pattern.pattern_id))[:limit]


def _resolve_pattern_path(corpus_root: Path, pattern_path: str) -> Path:
    path = Path(pattern_path)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == corpus_root.name:
        return corpus_root.parent / path
    return corpus_root / path


def _score_pattern(pattern: QuestionPatternCard, query_terms: list[str]) -> float:
    query_tokens = _tokens(" ".join(query_terms))
    if not query_tokens:
        return 0.5
    pattern_tokens = _tokens(
        " ".join(
            [
                pattern.pattern_name,
                " ".join(pattern.starting_scientific_state),
                pattern.unresolved_tension_pattern,
                " ".join(pattern.dataset_cues),
                pattern.question_formation_move,
                pattern.scientific_payoff,
            ]
        )
    )
    return round(len(query_tokens & pattern_tokens) / len(query_tokens), 4)


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in {"the", "and", "for", "with", "from"}
    }
