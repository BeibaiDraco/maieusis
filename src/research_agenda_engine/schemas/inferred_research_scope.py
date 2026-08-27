"""Typed research scope + open-mode inferred scope.

``ResearchIntent`` has three modes; this makes them real. ``ResolvedResearchScope`` is what topic
retrieval + the topic-evidence gate consume; for ``open`` mode it carries a typed
``InferredResearchScope`` derived from reviewed PatternBank + the coarse ``DatasetNarrative`` ONLY (the
open-mode firewall — see ``services/context/research_scope.py``). The original ``ResearchIntent`` is
always preserved separately; inference never masquerades as user input.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResearchScopeSourceMode(StrEnum):
    TOPIC_CONDITIONED = "topic_conditioned"
    SEED_QUESTION = "seed_question"
    OPEN_INFERRED = "open_inferred"


class InferredResearchScope(BaseModel):
    """Open-mode scope inferred from reviewed patterns + the coarse dataset narrative only."""

    model_config = ConfigDict(extra="forbid")

    scope_id: str
    scope_version: str = "inferred_research_scope/v1"
    inferred_topic_terms: list[str] = Field(default_factory=list)
    inferred_construct_families: list[str] = Field(default_factory=list)
    supporting_pattern_ids: list[str] = Field(default_factory=list)
    supporting_dataset_source_ids: list[str] = Field(default_factory=list)
    excluded_scope: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    # Provenance: how the scope was derived (deterministic marker or a generator identity).
    derivation: str = "deterministic_patterns_plus_coarse_narrative/v1"
    input_digest: str = ""
    output_digest: str = ""

    @field_validator("scope_id")
    @classmethod
    def require_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("InferredResearchScope scope_id must be non-empty")
        return value

    @field_validator("inferred_topic_terms", "supporting_pattern_ids")
    @classmethod
    def require_nonempty(cls, value: list[str]) -> list[str]:
        if not [item for item in value if item.strip()]:
            raise ValueError(
                "InferredResearchScope requires inferred_topic_terms and supporting_pattern_ids"
            )
        return value


class ResolvedResearchScope(BaseModel):
    """What retrieval + the topic-evidence gate consume; the original ResearchIntent is preserved."""

    model_config = ConfigDict(extra="forbid")

    source_mode: ResearchScopeSourceMode
    terms: list[str] = Field(default_factory=list)
    #: The names a paper REUSING this dataset would cite it by -- its release name, benchmark name,
    #: consortium, or accession. Deliberately NOT in `terms`: the deriver prompt rejects instrument,
    #: software and consortium names as scope terms because their literature is about the tool
    #: rather than a question anyone argues over, and that rule is right. But the reviewer requires
    #: source-backed evidence for the `dataset_resource_reuse` dimension, and no scope term is
    #: allowed to carry the only vocabulary that finds it -- so the dimension had no retrieval path
    #: at all and whatever reuse evidence appeared did so by luck. These terms feed that one lane.
    dataset_identity_terms: list[str] = Field(default_factory=list)
    construct_families: list[str] = Field(default_factory=list)
    seed_question: str = ""
    inferred_scope: InferredResearchScope | None = None
    original_intent_digest: str = ""

    @field_validator("terms")
    @classmethod
    def require_terms(cls, value: list[str]) -> list[str]:
        if not [item for item in value if item.strip()]:
            raise ValueError("ResolvedResearchScope requires at least one query term")
        return value
