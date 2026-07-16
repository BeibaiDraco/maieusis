"""Neutral research-intent types (product core).

The neutral research-intent types for the product core (extracted from the
retired ``schemas/question.py``; that legacy module was deleted in
5d-B). Import these from here.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..enums import ClaimLevel


class ResearchIntentMode(StrEnum):
    OPEN = "open"
    TOPIC_CONDITIONED = "topic_conditioned"
    SEED_QUESTION = "seed_question"


class NoveltyDistance(StrEnum):
    CONSERVATIVE = "conservative"
    ADJACENT = "adjacent"
    EXPLORATORY = "exploratory"


class ResearchIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: str = ""
    mode: ResearchIntentMode = ResearchIntentMode.OPEN
    topic_terms: list[str] = Field(default_factory=list)
    topic_description: str = ""
    seed_question: str = ""
    novelty_distance: NoveltyDistance = NoveltyDistance.ADJACENT
    include_concepts: list[str] = Field(default_factory=list)
    exclude_concepts: list[str] = Field(default_factory=list)
    preferred_epistemic_moves: list[str] = Field(default_factory=list)
    target_constructs: list[str] = Field(default_factory=list)
    preferred_claim_levels: list[ClaimLevel] = Field(default_factory=list)
    target_regions: list[str] = Field(default_factory=list)
    target_events: list[str] = Field(default_factory=list)
    budget: str = "prototype"
    constraints: list[str] = Field(default_factory=list)
    desired_question_families: list[str] = Field(default_factory=list)
    excluded_question_families: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_legacy_theme(self) -> ResearchIntent:
        if self.theme and not self.topic_terms:
            self.topic_terms = [self.theme]
        if self.mode == ResearchIntentMode.TOPIC_CONDITIONED and not self.topic_terms:
            raise ValueError("topic_conditioned intent requires topic_terms or legacy theme")
        if self.mode == ResearchIntentMode.SEED_QUESTION and not self.seed_question.strip():
            raise ValueError("seed_question intent requires seed_question")
        return self
