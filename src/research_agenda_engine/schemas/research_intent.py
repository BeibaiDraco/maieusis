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


class ScopeDerivationMode(StrEnum):
    """Who decides which literature this run searches for.

    Added 2026-08-17 after two release configs were found searching the same eight generic terms for
    two unrelated datasets, with both candidate pools exhausted and the dimensions the independent
    reviewer grades on absent from the corpus. See
    ``schemas/derived_dataset_scope.py`` for the measurement.

    ``never`` turns off the MODEL, not derivation: an ``open``-mode run with no declared terms still
    falls back to deterministic keyword extraction from the same narrative. The only way to search
    exactly what you wrote is to write it.
    """

    #: Declared terms win outright and no model is asked. Only a mode with nothing declared -- that
    #: is, ``open`` -- reaches the deriver. This is the default because it leaves every existing
    #: config's retrieval byte-identical and costs it nothing.
    AUTO = "auto"
    #: Declared terms are kept, in order and unrewritten, and the deriver's terms are appended. For
    #: the case that produced this feature: a user who knows three terms and wants the rest filled.
    AUGMENT = "augment"
    #: No model call on this path, ever.
    NEVER = "never"


class ResearchIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: str = ""
    mode: ResearchIntentMode = ResearchIntentMode.OPEN
    topic_terms: list[str] = Field(default_factory=list)
    topic_description: str = ""
    seed_question: str = ""
    novelty_distance: NoveltyDistance = NoveltyDistance.ADJACENT
    scope_derivation: ScopeDerivationMode = ScopeDerivationMode.AUTO
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
