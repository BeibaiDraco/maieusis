"""Trust-ordered fusion of the coarse-facts feeds → one coarse ``DatasetNarrative``.

Deterministic, trust-ordered field merge of the coarse-facts feeds (D user docs > A documentation
> B local sample > C model self-research) into a single candidate ``DatasetNarrative``, with
field-level provenance recorded in ``field_evidence_source_ids`` (which source URI(s) contributed each
field). The merge is deterministic + auditable — the independent-AI fidelity gate only *judges* the
candidate, so a hallucinating model cannot invent the merge. Accepts any partial subset of sources.

WHAT IS ACTUALLY WIRED IN v0.1 (measured 2026-08-13 over 26 run artifacts on this machine, and this
module used to open by calling itself "four-source fusion", which was never true of any run):

- **D user docs** and **A documentation** are gathered by the product run driver whenever the seed
  supplies docs / a link, and are the only feeds any recorded run has ever fused.
- **B local sample** has no caller. ``gather_and_fuse_dataset_narrative`` accepts
  ``local_sample_facts``, and neither the run driver nor the dev CLI passes it, so no artifact in any
  run carries a ``local-sample-exploration://`` locator. The explorer module is real and kept.
- **C model self-research** is switched off in the driver, not by configuration: the executor's
  ``web_search_provider()`` returns ``None`` unconditionally, and 26 of 26 recorded runs file
  ``model_research: inactive`` in their ``source_activity.yaml``.

The trust order below therefore describes the merge rule, not four live feeds. Both absences are
now RECORDED per run (a ``local_sample`` row in ``DatasetSourceActivity`` and a narrator ``skipped``
note) rather than being visible only as a source that never appears.

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
    canonical_scale_fact_topic,
)

FUSION_VERSION = "dataset_narrative_fusion/v1"


class SourceKind(StrEnum):
    USER_DESCRIPTION = "user_description"  # D — user-provided-description:// (wired)
    DOCUMENTATION = "documentation"  # A — documentation-fetch:// (wired)
    LOCAL_SAMPLE = "local_sample"  # B — local-sample-exploration:// (no caller passes it in v0.1)
    MODEL_RESEARCH = "model_research"  # C — api-model-self-research:// (driver returns no provider)


# Trust order (highest first) IF a feed is present: D > A > B > C. In v0.1 only D and A are ever
# present, so this is the rule the merge would follow, not a description of four live inputs.
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
    ("hierarchical_structure", "hierarchical_structure"),
    ("broad_interventions", "broad_interventions"),
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

    # Scale facts are resolved BEFORE the list fields, because a limitation is superseded only by a
    # quantity a higher-trust source actually went on to state.
    scale_facts, scale_contributors = _resolve_scale_facts(present)
    if scale_contributors:
        field_evidence["scale_facts"] = scale_contributors

    item_evidence: dict[str, list[list[str]]] = {}
    for coarse_attr, narrative_attr in _LIST_FIELDS:
        merged, contributors, item_sources = _union_list(present, coarse_attr)
        values[narrative_attr] = merged
        if contributors:
            field_evidence[narrative_attr] = contributors
        if item_sources:
            item_evidence[narrative_attr] = item_sources

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
        # This construction lists every field by hand, so a _LIST_FIELDS entry alone reaches
        # `values` and `field_evidence` and then falls on the floor here. Adding the mapping without
        # this line was worse than not adding it: field_evidence_source_ids claimed the
        # documentation source backed a hierarchy while the field stayed empty, and the fidelity
        # reviewer -- correctly -- failed `faithful` on exactly that mismatch in two live legs.
        hierarchical_structure=values.get("hierarchical_structure", []),
        broad_interventions=values.get("broad_interventions", []),
        standardization=values.get("standardization", ""),
        major_variables=values.get("major_variables", []),
        reuse_opportunities=values.get("reuse_opportunities", []),
        known_high_level_limitations=values.get("known_high_level_limitations", []),
        scale_facts=scale_facts,
        field_evidence_source_ids=field_evidence,
        list_item_source_ids=item_evidence,
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


# A limitation that denies a quantity was STATED, not one that cautions about interpreting it. The
# distinction is the whole point: "counts are not stated" is superseded when a higher-trust source
# states them, while "the excerpt does not establish unit-quality equivalence" stays true and must
# survive. These are negations of a statement verb, a closed logical form -- not a synonym table.
def _union_list(
    present: Sequence[tuple[SourceKind, CoarseDatasetFacts]], attr: str
) -> tuple[list[str], list[str], list[list[str]]]:
    """Trust-ordered union of a list field, recording the contributing source PER ITEM.

    Per-ITEM provenance, not per-field. A field-level source list says only "these sources touched
    this field", and everything downstream stamped that whole list onto every item -- so a card
    authored by one source was delivered to the Question Scientist as jointly asserted by two,
    manufacturing corroboration that never happened.

    It is also what made a fused narrative read as self-contradictory. One source honestly recorded
    that ITS excerpts do not state unit counts while a higher-trust source supplied them; both are
    true of their own excerpts, and only the missing attribution made them read as one voice
    asserting a quantity and its absence at once. Scoping each statement to its source dissolves
    that without deleting anything, matching any vocabulary, or authoring any prose -- which is what
    two earlier deterministic attempts had to do, and why both were wrong.

    An identical sentence contributed by a second source is genuine corroboration, so that item
    carries both locators.
    """
    merged: list[str] = []
    item_sources: list[list[str]] = []
    index_of: dict[str, int] = {}
    contributors: list[str] = []
    for _kind, facts in present:  # already in trust order
        items = [str(item).strip() for item in getattr(facts, attr, []) if str(item).strip()]
        if not items:
            continue
        locator = source_locator(facts)
        if locator and locator not in contributors:
            contributors.append(locator)
        for item in items:
            key = item.lower()
            existing = index_of.get(key)
            if existing is not None:
                if locator and locator not in item_sources[existing]:
                    item_sources[existing].append(locator)
                continue
            index_of[key] = len(merged)
            merged.append(item)
            item_sources.append([locator] if locator else [])
    return merged, contributors, item_sources


def _resolve_scale_facts(
    present: Sequence[tuple[SourceKind, CoarseDatasetFacts]],
) -> tuple[list[Any], list[str]]:
    """Highest-trust source wins each quantity topic and keeps all of its facts for that topic.

    Cross-source RESOLUTION, matching ``_pick_scalar``, not a bag union. Every source is asked for
    the same ``SCALE_FACT_TOPICS``, so two sources describing one dataset describe the same
    quantities twice; a union keeps both restatements, and because they are independent model calls
    they can disagree. That is not hypothetical -- shipped narratives carried a ``142 total units in
    the training split`` fact beside a ``unit or electrode counts are not stated`` fact for the same
    topic, and exported both to the Question Scientist, because the old dedup key
    ``(quantity_kind, value_text)`` matched on neither half.

    Within a single source several facts may legitimately share a topic (a train count beside a test
    count), so multiplicity inside the winning source is preserved and only losing sources are
    dropped. A source that wins no topic is not credited as a contributor.
    """
    merged: list[Any] = []
    claimed: set[str] = set()
    feeds_by_topic: dict[str, set[str]] = {}
    contributors: list[str] = []
    for _kind, facts in present:  # already in trust order
        if not facts.scale_facts:
            continue
        locator = source_locator(facts)
        kept: list[Any] = []
        seen_here: set[tuple[str, str]] = set()
        for fact in facts.scale_facts:
            topic = canonical_scale_fact_topic(fact.quantity_kind)
            if topic in claimed:
                continue
            key = (topic, fact.value_text.strip().lower())
            if key in seen_here:
                continue
            seen_here.add(key)
            kept.append(fact)
        if not kept:
            continue
        for fact in kept:
            claimed.add(canonical_scale_fact_topic(fact.quantity_kind))
        merged.extend(kept)
        for fact in kept:
            feeds_by_topic.setdefault(canonical_scale_fact_topic(fact.quantity_kind), set()).add(
                locator
            )
        if locator and locator not in contributors:
            contributors.append(locator)
    assert_scale_facts_resolved_across_feeds(feeds_by_topic)
    return merged, contributors


def assert_scale_facts_resolved_across_feeds(feeds_by_topic: Mapping[str, set[str]]) -> None:
    """Post-condition: no quantity topic survives the merge from two different FEEDS.

    Checked here and not on ``DatasetNarrative`` because the model cannot express it.
    ``scale_facts[].source_ids`` holds EXCERPT ids: one feed citing two of its own excerpts looks
    like two sources, and two feeds that CORROBORATE one figure share citations, so excerpt ids
    separate neither case. A schema-level version of this guard rejected a legitimate single-source
    narrative and stopped this repository's own tracked ibl narrative from loading at all. Here the
    feed that contributed each kept fact is known, so the question is answerable.

    ``feeds_by_topic`` is accumulated from the facts actually KEPT. A first attempt at this
    post-condition re-derived its answer from the ownership map it was handed and could therefore
    never fail: a guard that restates how the code is written catches nothing.
    """

    unresolved = {topic: sorted(feeds) for topic, feeds in feeds_by_topic.items() if len(feeds) > 1}
    if unresolved:
        raise ValueError(
            "fused scale_facts leave a quantity topic claimed by two feeds: "
            + "; ".join(f"{topic}: {feeds}" for topic, feeds in sorted(unresolved.items()))
        )
