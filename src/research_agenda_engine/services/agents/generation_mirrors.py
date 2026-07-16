"""Generation-boundary mirrors for model-structured outputs.

THE RULE: a model must never be asked to produce a code-derived field (digests, code-owned
ids, provenance identifiers), and a run must never crash because an honest model left one
empty. Real providers parse model JSON directly into the output model, so strict-schema
validators run inside ``generate_structured`` — before any force/stamp function can repair
the payload. These mirrors are strict-schema subclasses that tolerate empty code-level
fields at the generation boundary only.

Echo-id fields (``context_id`` / ``origin_provider_id`` / ``prompt_version`` and kin) stay
in the model-facing JSON schema because the active prompt families explicitly instruct
copying them; fully un-asking them requires prompt-family version bumps and is a recorded
follow-up. The code stamps them unconditionally regardless of what the model echoed.

A mirror instance is NEVER persisted: every caller rebuilds the strict parent via
``StrictModel.model_validate({**mirror.model_dump(mode="python"), **code_stamps})`` so the
strict validators re-run with the stamped values. A persisted artifact with an empty
code-level field is still rejected by the untouched parent schema.
"""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from ...schemas._r5_firewall import assert_proposal_safe_payload
from ...schemas.question_family import (
    QuestionFamily,
    QuestionFamilyConsolidationFinding,
    QuestionFamilyVariant,
)
from ...schemas.question_seed import QuestionSeed


class QuestionSeedModelOutput(QuestionSeed):
    """QuestionSeed generation mirror: echo-ids and the model-assigned seed id are tolerated
    when empty (the force functions stamp echo-ids unconditionally and default empty seed
    ids deterministically); the scientific-content fields remain fail-closed."""

    question_seed_id: str = ""
    context_id: str = ""
    origin_provider_id: str = ""
    prompt_version: str = ""

    @field_validator(
        "question",
        "scientific_tension",
        "why_scientifically_important",
        "novelty_hypothesis",
        "dataset_leverage_hypothesis",
        "discriminating_observation",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        # Same-name override of QuestionSeed.require_text: drops only the code-level ids
        # from the non-empty rule; genuine scientific content still fails closed.
        value = value.strip()
        if not value:
            raise ValueError("QuestionSeed core fields must be non-empty")
        return value


class QuestionFamilyVariantModelOutput(QuestionFamilyVariant):
    """QuestionFamilyVariant generation mirror: the nested seed is the relaxed mirror and
    the seed cross-reference id may be empty (stamped by the force functions)."""

    question_seed_id: str = ""
    seed: QuestionSeedModelOutput

    @field_validator("variant_id", "variant_role", "distinct_from_siblings")
    @classmethod
    def require_text(cls, value: str) -> str:
        # Same-name override: question_seed_id dropped from the non-empty rule.
        value = value.strip()
        if not value:
            raise ValueError("QuestionFamilyVariant text fields must be non-empty")
        return value


class QuestionFamilyModelOutput(QuestionFamily):
    """QuestionFamily generation mirror: echo-ids tolerated when empty and their
    family/variant consistency checks deferred to the strict rebuild (the force functions
    stamp one value everywhere, then QuestionFamily.model_validate re-runs the full parent
    validator)."""

    variants: list[QuestionFamilyVariantModelOutput] = Field(  # type: ignore[assignment]
        default_factory=list
    )
    context_id: str = ""
    origin_provider_id: str = ""
    prompt_version: str = ""

    @field_validator("question_family_id", "title", "summary", "shared_scientific_tension")
    @classmethod
    def require_text(cls, value: str) -> str:
        # Same-name override: echo-ids dropped from the non-empty rule.
        value = value.strip()
        if not value:
            raise ValueError("QuestionFamily core text fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_family(self) -> QuestionFamilyModelOutput:
        # Same-name override of QuestionFamily.validate_family: keeps every content check,
        # drops the echo-id consistency checks, and duplicate-checks only non-empty seed
        # ids (empty ones receive deterministic ids in the force functions). Keep the
        # content checks in sync with the parent validator.
        if not self.variants:
            raise ValueError("QuestionFamily requires variants")
        variant_ids = [variant.variant_id for variant in self.variants]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("QuestionFamily contains duplicate variant_id values")
        seed_ids = [
            variant.seed.question_seed_id
            for variant in self.variants
            if variant.seed.question_seed_id
        ]
        if len(seed_ids) != len(set(seed_ids)):
            raise ValueError("QuestionFamily contains duplicate question_seed_id values")
        if len(self.variants) > 1 and not self.non_mergeable_distinctions:
            raise ValueError("multi-variant QuestionFamily requires non_mergeable_distinctions")
        if len(self.source_family_ids) != len(set(self.source_family_ids)):
            raise ValueError("QuestionFamily source_family_ids must be unique")
        if not self.source_pattern_ids:
            variant_pattern_ids = {
                pattern_id
                for variant in self.variants
                for pattern_id in variant.seed.source_pattern_ids
            }
            if not variant_pattern_ids:
                raise ValueError("QuestionFamily requires source_pattern_ids")
            self.source_pattern_ids = sorted(variant_pattern_ids)
        assert_proposal_safe_payload(self.model_dump(mode="python"), context="QuestionFamily")
        return self


class ConsolidationFindingModelOutput(QuestionFamilyConsolidationFinding):
    """Consolidation-finding generation mirror: finding_id is code-owned (the review-report
    builder re-stamps it deterministically) and tolerated when empty; the finding message
    remains fail-closed."""

    finding_id: str = ""

    @model_validator(mode="after")
    def validate_finding(self) -> ConsolidationFindingModelOutput:
        # Same-name override: finding_id dropped from the non-empty rule.
        if not self.message.strip():
            raise ValueError("consolidation finding requires message")
        return self
