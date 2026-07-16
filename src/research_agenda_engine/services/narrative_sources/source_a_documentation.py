"""Source A — documentation coarse facts from the seed link.

Deterministic, auditable: resolve the seed LINK to proposal-safe excerpts, run the active generic
``dataset_narrative_extractor/v4`` GPT extraction over them (only the GPT leg — NOT the full
``build_dataset_narrative_draft_bundle``, which drags in the dataset-specific local track that is
GF-2c's to delete), map the coarse story fields onto ``CoarseDocumentationFacts``, and pass it through the
shared host import firewall. ``seed.docs`` is never consumed here (reserved for GF-2c Source D).

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...assets import resolve_asset
from ...providers.models.base import StructuredModelProvider
from ...schemas.coarse_dataset_facts import CoarseDocumentationFacts
from ...schemas.dataset_seed import DatasetSeed
from ..context.dataset_narrative import (
    DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION,
    DATASET_NARRATIVE_REQUIRED_EVIDENCE_FIELDS,
    DatasetNarrativeModelOutput,
    DatasetNarrativeSourcePacket,
)
from .coarse_facts_import import import_coarse_facts
from .provider import GenericNarrativeSourceProvider, NarrativeSourceProvider

DOCUMENTATION_SOURCE_LOCATOR_SCHEME = "documentation-fetch"

# Dataset-agnostic scale-fact topics for the extractor prompt input (no dataset-specific wording).
_REQUIRED_SCALE_FACT_TOPICS = [
    "subjects or participants",
    "sessions or recordings if publicly stated",
    "trials or samples if publicly stated",
    "recording units, channels, or sensors",
    "measurement sites or regions",
    "task or experimental structure",
    "behavioral or auxiliary measurements",
    "public access mode and hierarchy",
]


def documentation_source_locator(dataset_id: str) -> str:
    return f"{DOCUMENTATION_SOURCE_LOCATOR_SCHEME}://{dataset_id}"


def build_documentation_coarse_facts(
    *,
    seed: DatasetSeed,
    provider: StructuredModelProvider,
    source_provider: NarrativeSourceProvider | None = None,
    max_prompt_chars: int = 250_000,
) -> CoarseDocumentationFacts:
    """Resolve the seed link, GPT-extract coarse facts, firewall them into ``CoarseDocumentationFacts``."""
    source_provider = source_provider or GenericNarrativeSourceProvider()
    packet = source_provider.build_source_packet(seed)
    raw, source_ref_ids = extract_coarse_story_from_packet(
        packet=packet,
        provider=provider,
        dataset_id=seed.dataset_id,
        max_prompt_chars=max_prompt_chars,
    )
    return import_coarse_facts(
        raw,
        CoarseDocumentationFacts,
        provenance={
            "dataset_id": seed.dataset_id,
            "source_locator": documentation_source_locator(seed.dataset_id),
            "provider_id": provider.provider_id,
            "model_id": getattr(provider, "model_name", ""),
            "source_ref_ids": source_ref_ids,
        },
        belt_context="documentation_coarse_facts(raw)",
    )


def extract_coarse_story_from_packet(
    *,
    packet: DatasetNarrativeSourcePacket,
    provider: StructuredModelProvider,
    dataset_id: str,
    max_prompt_chars: int = 250_000,
) -> tuple[dict[str, Any], list[str]]:
    """Run the v4 GPT extraction over a source packet + map to the coarse story dict.

    Shared by Source A (fetched documentation) and Source D (user-provided docs): both feed the same
    active generic extractor and coarse map; only the source of the packet + the provenance URI differ.
    Returns ``(coarse_story_raw_dict, source_ref_ids)``; the caller stamps provenance + firewalls.
    """
    user_packet = {
        "prompt_version": DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION,
        "dataset_id": dataset_id,
        "allowed_source_ids": [item.source_id for item in packet.source_excerpts],
        "source_excerpts": [item.model_dump(mode="json") for item in packet.source_excerpts],
        "required_field_evidence": DATASET_NARRATIVE_REQUIRED_EVIDENCE_FIELDS,
        "required_scale_fact_topics": _REQUIRED_SCALE_FACT_TOPICS,
        "instructions": {
            "review_status": "draft",
            "proposal_stage": True,
            "field_level_evidence_required": True,
            "scale_facts_require_source_ids": True,
            "metadata_only_sources_cannot_support_substantive_fields": True,
            "do_not_include": [
                "exact columns",
                "table schemas",
                "joint coverage",
                "capability registry",
                "operator receipts",
                "confirmation outcomes",
                "QuestionCard",
                "AnalysisContract",
            ],
        },
    }
    user_prompt = json.dumps(user_packet, sort_keys=True, ensure_ascii=False)
    if len(user_prompt) > max_prompt_chars:
        raise ValueError("coarse source packet exceeds prompt budget")
    output = provider.generate_structured(
        system_prompt=_load_extractor_prompt(),
        user_prompt=user_prompt,
        output_model=DatasetNarrativeModelOutput,
    )
    raw = _map_to_coarse(output, dataset_id=dataset_id)
    return raw, [item.source_id for item in packet.source_excerpts]


def _map_to_coarse(output: DatasetNarrativeModelOutput, *, dataset_id: str) -> dict[str, Any]:
    """Map the (heavier) narrative model output onto the coarse story fields (a strict subset)."""
    structure_parts = [output.temporal_structure, *output.hierarchical_structure]
    coarse_structure = "; ".join(part for part in structure_parts if str(part).strip())
    return {
        "dataset_id": dataset_id,
        "modalities": list(output.modalities),
        "broad_scale": output.broad_scale,
        "coarse_structure": coarse_structure,
        "task_or_design": output.task_or_design,
        "spatial_or_anatomical_coverage": output.spatial_or_anatomical_coverage,
        "standardization": output.standardization,
        "scientific_purpose": output.scientific_purpose,
        "population": output.population,
        "major_variables": list(output.major_variables),
        "reuse_opportunities": list(output.reuse_opportunities),
        "known_coarse_limitations": list(output.known_high_level_limitations),
        # v4 scale facts are already source-backed DatasetNarrativeScaleFacts; keep their source_ids.
        "scale_facts": [fact.model_dump(mode="json") for fact in output.scale_facts],
    }


def _load_extractor_prompt() -> str:
    path = Path("prompts") / Path(DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION).with_suffix(".md")
    return resolve_asset(path).read_text(encoding="utf-8")
