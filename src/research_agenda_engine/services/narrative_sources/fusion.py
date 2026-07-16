"""Four-source fusion → one coarse ``DatasetNarrative``.

Deterministic, trust-ordered field merge of the four coarse-facts feeds (D user docs > A documentation
> B local sample > C model self-research) into a single candidate ``DatasetNarrative``, with
field-level provenance recorded in ``field_evidence_source_ids`` (which source URI(s) contributed each
field). The merge is deterministic + auditable — the independent-AI fidelity gate only *judges* the
candidate, so a hallucinating model cannot invent the merge. Accepts any partial subset of sources.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from ...schemas.coarse_dataset_facts import CoarseDatasetFacts
from ...schemas.dataset_narrative import (
    DatasetNarrative,
    DatasetNarrativeReviewStatus,
    DatasetNarrativeSourceRef,
    DatasetNarrativeSourceType,
)

FUSION_VERSION = "dataset_narrative_fusion/v1"


class SourceKind(StrEnum):
    USER_DESCRIPTION = "user_description"  # D — user-provided-description://
    DOCUMENTATION = "documentation"  # A — documentation-fetch://
    LOCAL_SAMPLE = "local_sample"  # B — local-sample-exploration://
    MODEL_RESEARCH = "model_research"  # C — api-model-self-research://


# Trust order (highest first): D > A > B > C.
_TRUST_ORDER: tuple[SourceKind, ...] = (
    SourceKind.USER_DESCRIPTION,
    SourceKind.DOCUMENTATION,
    SourceKind.LOCAL_SAMPLE,
    SourceKind.MODEL_RESEARCH,
)

_SOURCE_TYPE: dict[SourceKind, DatasetNarrativeSourceType] = {
    SourceKind.USER_DESCRIPTION: DatasetNarrativeSourceType.EXPERT_NOTE,
    SourceKind.DOCUMENTATION: DatasetNarrativeSourceType.DATASET_DOCUMENTATION,
    SourceKind.LOCAL_SAMPLE: DatasetNarrativeSourceType.METADATA_SUMMARY,
    SourceKind.MODEL_RESEARCH: DatasetNarrativeSourceType.METADATA_SUMMARY,
}

# Coarse scalar/list fields → DatasetNarrative field names.
_SCALAR_FIELDS: tuple[tuple[str, str], ...] = (
    ("broad_scale", "broad_scale"),
    ("task_or_design", "task_or_design"),
    ("spatial_or_anatomical_coverage", "spatial_or_anatomical_coverage"),
    ("standardization", "standardization"),
    ("scientific_purpose", "scientific_purpose"),
    ("population", "population"),
    ("coarse_structure", "temporal_structure"),
)
_LIST_FIELDS: tuple[tuple[str, str], ...] = (
    ("modalities", "modalities"),
    ("major_variables", "major_variables"),
    ("reuse_opportunities", "reuse_opportunities"),
    ("known_coarse_limitations", "known_high_level_limitations"),
)


def source_locator(facts: CoarseDatasetFacts) -> str:
    """The provenance URI of a coarse-facts feed (B uses ``sample_locator``; A/C/D ``source_locator``)."""
    return str(getattr(facts, "source_locator", "") or getattr(facts, "sample_locator", ""))


def fuse_coarse_dataset_narrative(
    sources: Mapping[SourceKind, CoarseDatasetFacts | None],
    *,
    dataset_id: str,
) -> DatasetNarrative:
    """Fuse the present coarse-facts feeds into one candidate (DRAFT) ``DatasetNarrative``."""
    present: list[tuple[SourceKind, CoarseDatasetFacts]] = []
    for kind in _TRUST_ORDER:  # highest trust first
        facts = sources.get(kind)
        if facts is not None:
            present.append((kind, facts))
    if not present:
        raise ValueError("fuse_coarse_dataset_narrative requires at least one source")

    field_evidence: dict[str, list[str]] = {}
    values: dict[str, Any] = {}

    for coarse_attr, narrative_attr in _SCALAR_FIELDS:
        winner, contributors = _pick_scalar(present, coarse_attr)
        values[narrative_attr] = winner
        if contributors:
            field_evidence[narrative_attr] = contributors

    for coarse_attr, narrative_attr in _LIST_FIELDS:
        merged, contributors = _union_list(present, coarse_attr)
        values[narrative_attr] = merged
        if contributors:
            field_evidence[narrative_attr] = contributors

    scale_facts, scale_contributors = _union_scale_facts(present)
    if scale_contributors:
        field_evidence["scale_facts"] = scale_contributors

    scientific_purpose = values.get("scientific_purpose") or (
        f"A proposal-stage coarse description of the {dataset_id} dataset, fused from "
        f"{len(present)} source(s)."
    )

    source_refs = [
        DatasetNarrativeSourceRef(
            source_id=source_locator(facts),
            source_type=_SOURCE_TYPE[kind],
            locator=source_locator(facts),
            title=f"{kind.value} coarse facts",
            reviewed=False,
        )
        for kind, facts in present
        if source_locator(facts)
    ]

    return DatasetNarrative(
        dataset_narrative_id=f"dataset-narrative-fused-{dataset_id}",
        dataset_id=dataset_id,
        title=f"{dataset_id} coarse proposal-stage dataset narrative",
        scientific_purpose=scientific_purpose,
        population=values.get("population", ""),
        task_or_design=values.get("task_or_design", ""),
        modalities=values.get("modalities", []),
        broad_scale=values.get("broad_scale", ""),
        spatial_or_anatomical_coverage=values.get("spatial_or_anatomical_coverage", ""),
        temporal_structure=values.get("temporal_structure", ""),
        standardization=values.get("standardization", ""),
        major_variables=values.get("major_variables", []),
        reuse_opportunities=values.get("reuse_opportunities", []),
        known_high_level_limitations=values.get("known_high_level_limitations", []),
        scale_facts=scale_facts,
        field_evidence_source_ids=field_evidence,
        source_refs=source_refs,
        review_status=DatasetNarrativeReviewStatus.DRAFT,
        prompt_version=FUSION_VERSION,
    )


def _pick_scalar(
    present: Sequence[tuple[SourceKind, CoarseDatasetFacts]], attr: str
) -> tuple[str, list[str]]:
    """Highest-trust non-empty scalar wins; every contributing source URI is recorded for provenance."""
    winner = ""
    contributors: list[str] = []
    for _kind, facts in present:  # already in trust order
        value = str(getattr(facts, attr, "") or "").strip()
        if not value:
            continue
        if not winner:
            winner = value
        locator = source_locator(facts)
        if locator and locator not in contributors:
            contributors.append(locator)
    return winner, contributors


def _union_list(
    present: Sequence[tuple[SourceKind, CoarseDatasetFacts]], attr: str
) -> tuple[list[str], list[str]]:
    """Trust-ordered union of a list field; contributing source URIs recorded for provenance."""
    merged: list[str] = []
    seen: set[str] = set()
    contributors: list[str] = []
    for _kind, facts in present:
        items = [str(item).strip() for item in getattr(facts, attr, []) if str(item).strip()]
        if not items:
            continue
        locator = source_locator(facts)
        if locator and locator not in contributors:
            contributors.append(locator)
        for item in items:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                merged.append(item)
    return merged, contributors


def _union_scale_facts(
    present: Sequence[tuple[SourceKind, CoarseDatasetFacts]],
) -> tuple[list[Any], list[str]]:
    """Union of all sources' coarse scale facts (each keeps its own source_ids), deduped by content."""
    merged: list[Any] = []
    seen: set[tuple[str, str]] = set()
    contributors: list[str] = []
    for _kind, facts in present:
        if not facts.scale_facts:
            continue
        locator = source_locator(facts)
        if locator and locator not in contributors:
            contributors.append(locator)
        for fact in facts.scale_facts:
            key = (fact.quantity_kind.lower(), fact.value_text.lower())
            if key not in seen:
                seen.add(key)
                merged.append(fact)
    return merged, contributors
