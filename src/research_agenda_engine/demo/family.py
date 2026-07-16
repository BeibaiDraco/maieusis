"""Deterministic demo question-family generation payload.

The config-reachable
``subscription_only_demo`` deterministic generation assets (public_optional). Demo mode is
an explicit mock + FakePlannerHost workflow demonstration — never a scientific-quality
claim (the demo banner and development_model_surrogate authority labels flow to every
output surface).
"""

from __future__ import annotations

import json


def _seed_payload(packet: dict, index: int) -> dict:
    return {
        "question_seed_id": f"qseed-{index:03d}",
        "question": (
            "Does representational geometry separate task variables from shared "
            "behavioral-state structure across brain areas?"
        ),
        "scientific_tension": (
            "Population geometry may reflect task coding or shared movement/state structure."
        ),
        "why_scientifically_important": (
            "The contrast clarifies whether geometry is a coding object or a state confound."
        ),
        "relevant_literature_claims": ["claim-open"],
        "novelty_hypothesis": (
            "The seed focuses on discriminating geometry interpretations rather than decoding score."
        ),
        "closest_known_work": ["claim-prior"],
        "dataset_leverage_hypothesis": (
            "The reviewed dataset context describes broad task-aligned neural and behavioral data."
        ),
        "competing_explanations": [
            "task variables define reusable representational geometry",
            "shared behavioral state explains most apparent geometry",
        ],
        "discriminating_observation": (
            "A geometry contrast separates task-aligned structure from state-linked structure."
        ),
        "positive_result_consequence": "Supports a task-geometry interpretation.",
        "negative_result_consequence": "Supports a state/confound interpretation.",
        "null_result_consequence": (
            "Suggests this dataset may not distinguish the geometry interpretations."
        ),
        "ambiguous_constructs": ["representational geometry", "behavioral state"],
        "likely_implementation_challenges": [
            "A later planner must define geometry and state controls."
        ],
        "assumptions_about_dataset": [
            "The broad dataset narrative implies relevant neural and behavioral measurements."
        ],
        "source_pattern_ids": [packet["allowed_pattern_ids"][0]],
        "source_paper_case_ids": [],
        "context_id": packet["context_id"],
        "origin_provider_id": packet["origin_provider_id"],
        "prompt_version": packet["prompt_version"],
    }


_VARIANT_TEMPLATES = [
    (
        "task-versus-state contrast",
        ["target_contrast", "discriminating_observation"],
        "Does representational geometry preserve task coding after behavioral-state controls?",
    ),
    (
        "cross-area outcome-meaning contrast",
        ["outcome_meaning", "population_scope"],
        "Does cross-area geometry reveal shared coding or region-local state structure?",
    ),
    (
        "claim-level discrimination contrast",
        ["claim_level", "theoretical_tension"],
        "Does the geometry contrast hold across task epochs or collapse to a single window?",
    ),
]


def _family_factory(output_model, _system_prompt: str, user_prompt: str):
    # Honor the requested family/variant counts (the packet carries them) so the demo satisfies
    # whatever `maieusis run` asked for — a fixed template replicated per family.
    packet = json.loads(user_prompt)
    family_count = int(packet.get("family_count_requested", 1))
    variants_per_family = int(packet.get("variants_per_family_requested", 2))
    families = []
    for fam in range(family_count):
        variants = []
        for v in range(variants_per_family):
            role, axes, question = _VARIANT_TEMPLATES[v % len(_VARIANT_TEMPLATES)]
            variants.append(
                _variant_payload(
                    packet,
                    fam * variants_per_family + v + 1,
                    role=role,
                    axes=axes,
                    question=question,
                )
            )
        families.append(_family_payload(packet, variants=variants, family_index=fam))
    return output_model.model_validate({"families": families})


def _family_payload(
    packet: dict,
    *,
    variants: list[dict] | None = None,
    family_index: int = 0,
    **overrides,
) -> dict:
    payload = {
        "question_family_id": f"qfamily-{family_index + 1:03d}",
        "title": "Task geometry versus behavioral state",
        "summary": "A family asking whether neural geometry reflects task coding or state.",
        "shared_scientific_tension": (
            "Population geometry may express task variables, or it may mostly reflect "
            "shared behavioral state and movement structure."
        ),
        "variants": variants
        or [
            _variant_payload(
                packet,
                1,
                role="within-area state-control contrast",
                axes=["target_contrast", "discriminating_observation"],
                question=(
                    "Does population geometry preserve task coding after explicit "
                    "movement-state controls?"
                ),
            ),
            _variant_payload(
                packet,
                2,
                role="cross-area outcome-meaning contrast",
                axes=["outcome_meaning", "population_scope"],
                question=(
                    "Do cross-area geometry alignments imply shared task structure "
                    "or region-local behavioral state?"
                ),
            ),
        ],
        "semantic_axes": ["target contrast", "outcome meaning"],
        "non_mergeable_distinctions": [
            "One variant tests state control within a geometry, while another asks whether cross-area sharing changes the interpretation."
        ],
        "source_pattern_ids": [packet["allowed_pattern_ids"][0]],
        "source_topic_claim_ids": packet["allowed_topic_claim_ids"][:1],
        "source_dataset_context_ids": [packet["allowed_dataset_context_ids"][0]],
        "proposal_stage_uncertainties": [
            "A later planner must decide how to operationalize geometry and state."
        ],
        "assumptions_about_dataset": [
            "The reviewed dataset narrative suggests neural and behavioral measurements are relevant."
        ],
        "context_id": packet["context_id"],
        "origin_provider_id": packet["origin_provider_id"],
        "prompt_version": packet["prompt_version"],
    }
    payload.update(overrides)
    return payload


def _variant_payload(
    packet: dict,
    index: int,
    *,
    role: str | None = None,
    axes: list[str] | None = None,
    question: str | None = None,
    distinct_from_siblings: str | None = None,
    branch_eligible: bool = True,
) -> dict:
    seed = _seed_payload(packet, index)
    seed["question_seed_id"] = f"qseed-family-{index:03d}"
    seed["question"] = question or (
        "Does representational geometry separate task variables from movement-linked "
        f"behavioral state in family variant {index}?"
    )
    seed["scientific_tension"] = (
        "Population geometry may reveal task coding, but it may instead reflect "
        f"variant-specific behavioral state structure {index}."
    )
    seed["discriminating_observation"] = (
        "The decisive observation is whether the proposed geometry contrast survives "
        f"the sibling-specific control logic {index}."
    )
    return {
        "variant_id": f"qvariant-{index:03d}",
        "question_seed_id": seed["question_seed_id"],
        "seed": seed,
        "variant_role": role or f"variant role {index}",
        "distinction_axes": axes or ["target_contrast"],
        "distinct_from_siblings": distinct_from_siblings
        or (
            "This variant changes the scientific contrast and outcome meaning relative "
            "to its sibling, not just the wording."
        ),
        "branch_eligible": branch_eligible,
    }
