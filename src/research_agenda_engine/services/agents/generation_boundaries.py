"""Auditable failure-scope and normalization policy for serious generation boundaries.

This registry is descriptive authority used by tests and release audits.  It prevents a new active
generator from silently inheriting whole-run failure semantics or an undocumented prose repair.
Runtime adapters still implement the listed behavior at their concrete typed boundary.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class GenerationFailureScope(StrEnum):
    ARTIFACT = "artifact"
    BATCH = "batch"
    STAGE = "stage"
    FAMILY = "family"
    VARIANT = "variant"


class GenerationBoundaryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    prompt_version: str
    failure_scope: GenerationFailureScope
    bounded_retries: int = 0
    host_owned_fields: tuple[str, ...] = ()
    safe_normalizations: tuple[str, ...] = ()
    hard_boundaries: tuple[str, ...] = (
        "identity",
        "evidence_scope",
        "authority",
        "confirmation_firewall",
        "filesystem_scope",
    )


_HOST_IDS = ("artifact_id", "parent_ids", "prompt_version", "input_digest")


SERIOUS_GENERATION_BOUNDARIES: dict[str, GenerationBoundaryPolicy] = {
    policy.prompt_version: policy
    for policy in (
        GenerationBoundaryPolicy(
            prompt_version="paper_case_extractor/v8",
            failure_scope=GenerationFailureScope.ARTIFACT,
            bounded_retries=1,
            host_owned_fields=_HOST_IDS,
        ),
        GenerationBoundaryPolicy(
            prompt_version="citation_importance_selector/v3",
            failure_scope=GenerationFailureScope.ARTIFACT,
            bounded_retries=1,
            host_owned_fields=_HOST_IDS,
        ),
        GenerationBoundaryPolicy(
            prompt_version="question_formation_trace_drafter/v3",
            failure_scope=GenerationFailureScope.ARTIFACT,
            host_owned_fields=_HOST_IDS,
        ),
        GenerationBoundaryPolicy(
            prompt_version="question_pattern_inducer/v3",
            failure_scope=GenerationFailureScope.BATCH,
            bounded_retries=1,
            host_owned_fields=_HOST_IDS,
        ),
        GenerationBoundaryPolicy(
            prompt_version="question_pattern_reviser/v1",
            failure_scope=GenerationFailureScope.ARTIFACT,
            host_owned_fields=_HOST_IDS,
        ),
        GenerationBoundaryPolicy(
            prompt_version="dataset_narrative_extractor/v5",
            failure_scope=GenerationFailureScope.STAGE,
            host_owned_fields=_HOST_IDS,
        ),
        GenerationBoundaryPolicy(
            prompt_version="dataset_narrative_reviser/v1",
            failure_scope=GenerationFailureScope.STAGE,
            host_owned_fields=(
                "scale_facts",
                "source_refs",
                "field_evidence_source_ids",
                "dataset_narrative_id",
                "dataset_id",
                "review_status",
                "prompt_version",
                "provider_id",
                "model_id",
                "input_digest",
                "source_packet_digest",
                "dossier_digest",
                "reviewed_at",
                "expert_reviewer",
                "review_notes",
            ),
        ),
        GenerationBoundaryPolicy(
            # Degrades rather than fails: a scope the model could not write falls back to
            # deterministic keyword extraction over the same narrative, so no retry is bought here.
            # SCOPE, not ARTIFACT: the derived scope decides what literature the whole dataset half
            # searches, so a wrong one is not a bad artifact, it is a bad stage.
            prompt_version="dataset_scope_deriver/v2",
            failure_scope=GenerationFailureScope.STAGE,
            bounded_retries=0,
            host_owned_fields=(
                "scope_id",
                "prompt_version",
                "provider_id",
                "model_id",
                "input_digest",
                "output_digest",
                "status",
            ),
        ),
        GenerationBoundaryPolicy(
            # Registered 2026-08-17: this generator shipped without a boundary and nothing noticed,
            # because the registry is a declaration and an unregistered generator is only caught
            # where `generation_boundary` is called. `test_every_service_prompt_version_is_bounded`
            # now catches it from the service constants instead.
            prompt_version="topic_source_selector/v1",
            failure_scope=GenerationFailureScope.STAGE,
            bounded_retries=0,
            host_owned_fields=("source_record_id",),
        ),
        GenerationBoundaryPolicy(
            prompt_version="topic_evidence_brief_synthesizer/v7",
            failure_scope=GenerationFailureScope.STAGE,
            bounded_retries=1,
            host_owned_fields=_HOST_IDS,
        ),
        GenerationBoundaryPolicy(
            prompt_version="topic_evidence_brief_reviser/v1",
            failure_scope=GenerationFailureScope.STAGE,
            host_owned_fields=(
                "brief_id",
                "topic_terms",
                "canonical_scope",
                "knowledge_cutoff",
                "retrieval_manifest_digest",
                "review_status",
                "prompt_version",
                "provider_id",
                "model_id",
                "input_digest",
                "source_table_digest",
                "field_state_digest",
                "reviewed_at",
                "expert_reviewer",
                "review_notes",
            ),
        ),
        GenerationBoundaryPolicy(
            prompt_version="topic_evidence_terminal_inquiry/v1",
            failure_scope=GenerationFailureScope.STAGE,
            host_owned_fields=(
                "original_outcome",
                "allowed_source_record_ids",
                "eligible_source_record_ids",
                "prompt_version",
                "input_digest",
                "provider_id",
                "model_id",
                "output_digest",
            ),
        ),
        GenerationBoundaryPolicy(
            prompt_version="topic_field_state_synthesizer/v3",
            failure_scope=GenerationFailureScope.STAGE,
            host_owned_fields=_HOST_IDS,
        ),
        GenerationBoundaryPolicy(
            prompt_version="question_scientist/v2",
            failure_scope=GenerationFailureScope.FAMILY,
            bounded_retries=1,
            host_owned_fields=("batch_id", "question_family_id", "variant_id"),
        ),
        GenerationBoundaryPolicy(
            prompt_version="question_owner/v3",
            failure_scope=GenerationFailureScope.VARIANT,
            host_owned_fields=("branch_id", "question_family_id", "variant_id", "message_id"),
        ),
        GenerationBoundaryPolicy(
            prompt_version="dataset_planner/v2",
            failure_scope=GenerationFailureScope.VARIANT,
            bounded_retries=1,
            host_owned_fields=("branch_id", "question_family_id", "variant_id"),
            safe_normalizations=(
                "registered field alias",
                "single-key prose mapping to prose string",
                "whole-field prose string to singleton prose list",
                "all-prose claim-ceiling components degraded to non-authoritative notes",
            ),
        ),
    )
}


def generation_boundary(prompt_version: str) -> GenerationBoundaryPolicy:
    """Return the explicit serious-use boundary or fail closed for an unregistered generator."""
    try:
        return SERIOUS_GENERATION_BOUNDARIES[prompt_version]
    except KeyError as exc:
        raise ValueError(f"unregistered serious generation boundary: {prompt_version}") from exc
