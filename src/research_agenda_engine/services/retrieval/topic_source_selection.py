"""Choose the kept topic corpus by reading the candidates, not by ranking them.

WHY THIS EXISTS, measured. Retrieval can only order records by topical relevance. The independent
topic-evidence reviewer judges the kept corpus against eight scientific dimensions. Those are
different questions, and the gap between them was expensive:

* Ranking by the catalogue's own relevance (2026-08-16) improved two legs -- ibl blocking terminals
  11/15 -> 6/15, nlb 14/15 -> 9/15 -- and made the third worse, climate 3/15 -> 5/15.
* The cause on climate was exact. The only retrieved paper bearing on `dataset_resource_reuse` was
  *A sudden stratospheric warming compendium*. Under relevance ranking it sits at position **52 of
  100** and is evicted; under the previous alphabetical tiebreak it survived by luck. The reviewer
  then failed the corpus for having no reuse evidence, `generic_lane_coverage` 4/15 -> 11/15.
* Raising the kept count cannot fix that: at rank 52 the record is out of any plausible cap.

So the selection has to read the records. This module asks a model to do that, under three rules
that keep it from becoming the failure modes this repository has already paid for:

1. **It selects; it never acquires.** Every returned identifier must already be in the pool. A model
   that could add a source would need the rights machinery a web hit cannot satisfy (hard rule 13);
   a model that could rewrite the query would reproduce the retraction of 2026-08-12, where an
   invented qualifier took "Rossby wave breaking" from 307 results to 0.
2. **It never sees a verdict.** It is asked once, before review, from the scope and the dimensions.
   It is not a loop, so it cannot optimise toward approval -- which would be searching for a pass
   rather than for coverage.
3. **Its output is counted.** The novelty web lane once shipped inert, producing 0 of 2740 priors
   while passing a conformance audit. `TopicSourceSelection.activity` records what this step did in
   terms a later reader can check against the corpus itself.

Failure is degradation, never a stop: any provider error, schema violation, or unknown identifier
falls back to the deterministic ranking with the reason recorded. A leg must not die because a
selection helper had a bad night.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...assets import resolve_asset
from ...providers.models.base import StructuredModelProvider
from ...schemas.topic_literature import TopicSourceRecord
from .generic_topic_lanes import GENERIC_REQUIRED_LANES

TOPIC_SOURCE_SELECTOR_PROMPT_VERSION = "topic_source_selector/v1"


def _load_prompt() -> str:
    return resolve_asset(
        Path("prompts") / Path(TOPIC_SOURCE_SELECTOR_PROMPT_VERSION).with_suffix(".md")
    ).read_text(encoding="utf-8")


class SelectedTopicSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    dimensions: list[str] = Field(default_factory=list)
    why: str = ""


class TopicSourceSelectorOutput(BaseModel):
    """What the model is allowed to say. It cannot add a record; it can only name one."""

    model_config = ConfigDict(extra="forbid")

    selected: list[SelectedTopicSource] = Field(default_factory=list)
    uncovered_dimensions: list[str] = Field(default_factory=list)
    selection_notes: str = ""


class TopicSourceSelectionActivity(BaseModel):
    """The countable record of what this step did. Absence of this is a dead lane.

    `kept_by_model` minus `kept_by_ranking_fallback` is the number a reader can check against the
    corpus, and `dimensions_served` is the thing the step exists to change -- a selection that
    returns the same records ranking would have returned has done nothing, and says so here.
    """

    model_config = ConfigDict(extra="forbid")

    status: str
    pool_size: int = 0
    target_size: int = 0
    kept_by_model: int = 0
    kept_by_ranking_fallback: int = 0
    rank_agreement: int = Field(
        default=0,
        description="records the model kept that deterministic ranking would also have kept",
    )
    dimensions_served: dict[str, int] = Field(default_factory=dict)
    uncovered_dimensions: list[str] = Field(default_factory=list)
    unknown_identifiers: list[str] = Field(default_factory=list)
    #: Every candidate this step did NOT keep, by id. The complement of a narrowing has no type
    #: anywhere else in this pipeline, so it gets no field, no writer, no digest and no gate -- and
    #: measured on six runs, the count of DISTINCT `topic-source-record-*` ids anywhere in the whole
    #: run tree equalled the KEPT count exactly, 6 of 6 (49, 49, 64, 60, 55, 47). Between 136 and
    #: 153 retrieved-and-paid-for candidates per run left no byte behind, so nobody could ask
    #: afterwards whether a particular record had been dropped. The module's own history records
    #: what that costs: the only `dataset_resource_reuse` record on the 2026-08-16 climate leg sat
    #: at rank 52, was evicted here, and the reviewer then failed the corpus for lacking reuse
    #: evidence.
    dropped_source_record_ids: list[str] = Field(default_factory=list)
    #: What the pool itself was narrowed from, before this step saw it. Without it the `pool_size`
    #: recorded here is itself an unlabelled truncation and reads as the whole harvest.
    distinct_after_dedupe: int = 0
    degraded_reason: str = ""
    prompt_version: str = TOPIC_SOURCE_SELECTOR_PROMPT_VERSION
    provider_id: str = ""
    model_id: str = ""


def _dropped_ids(pool: Sequence[TopicSourceRecord], kept: Sequence[TopicSourceRecord]) -> list[str]:
    """The complement, in pool order, proven to partition the pool.

    A plain function rather than a model validator: a new `@model_validator` adds a row to the
    protected `constraints.yaml` and turns an ordinary PR into one needing per-PR operator
    authorization, for no extra safety here -- every construction of this activity goes through
    one of the three return sites below, and each calls this.
    """

    kept_ids = {record.source_record_id for record in kept}
    dropped = [
        record.source_record_id for record in pool if record.source_record_id not in kept_ids
    ]
    unknown = sorted(kept_ids - {record.source_record_id for record in pool})
    if unknown:
        raise ValueError(f"selection kept records absent from its own pool: {unknown}")
    if len(dropped) + len(kept_ids) != len({record.source_record_id for record in pool}):
        raise ValueError("topic source selection does not partition its candidate pool")
    return dropped


class TopicSourceSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[TopicSourceRecord]
    activity: TopicSourceSelectionActivity


def _candidate_payload(records: Sequence[TopicSourceRecord]) -> list[dict[str, object]]:
    return [
        {
            "source_record_id": record.source_record_id,
            "title": record.title,
            "year": record.year,
            "venue": record.venue,
            "abstract": record.snippet,
            "abstract_absent": not record.snippet.strip(),
        }
        for record in records
    ]


def select_topic_sources(
    *,
    provider: StructuredModelProvider | None,
    candidates: Sequence[TopicSourceRecord],
    scope_terms: Sequence[str],
    topic_description: str = "",
    target_size: int = 20,
) -> TopicSourceSelection:
    """Keep at most ``target_size`` candidates, chosen for dimension coverage as well as relevance.

    ``candidates`` arrives in deterministic rank order, so the first ``target_size`` of it is exactly
    what the pipeline kept before this step existed. That slice is both the fallback and the
    comparison recorded in ``rank_agreement``.
    """
    ranked = list(candidates)
    fallback = ranked[:target_size]

    # `model_name`, not `model_id`. The sibling step recorded an empty model identity onto a live
    # artifact by reading an attribute the provider does not declare; `getattr` with a default hides
    # that, so the attribute name is the thing to get right, not the guard. Named arguments rather
    # than a `**dict`: the model's fields are not all `str`, and mypy cannot check the spread.
    identity_provider = "" if provider is None else getattr(provider, "provider_id", "")
    identity_model = "" if provider is None else getattr(provider, "model_name", "")

    def degraded(reason: str) -> TopicSourceSelection:
        return TopicSourceSelection(
            records=fallback,
            activity=TopicSourceSelectionActivity(
                status="degraded_to_ranking",
                pool_size=len(ranked),
                target_size=target_size,
                kept_by_ranking_fallback=len(fallback),
                dropped_source_record_ids=_dropped_ids(ranked, fallback),
                degraded_reason=reason,
                provider_id=identity_provider,
                model_id=identity_model,
            ),
        )

    if provider is None:
        return degraded("no selector provider configured")
    if len(ranked) <= target_size:
        return TopicSourceSelection(
            records=fallback,
            activity=TopicSourceSelectionActivity(
                status="pool_not_larger_than_target",
                pool_size=len(ranked),
                target_size=target_size,
                kept_by_ranking_fallback=len(fallback),
                dropped_source_record_ids=_dropped_ids(ranked, fallback),
                provider_id=identity_provider,
                model_id=identity_model,
            ),
        )

    payload = {
        "prompt_version": TOPIC_SOURCE_SELECTOR_PROMPT_VERSION,
        "scope_terms": list(scope_terms),
        "topic_description": topic_description,
        "required_dimensions": list(GENERIC_REQUIRED_LANES),
        "target_size": target_size,
        "candidates": _candidate_payload(ranked),
    }

    try:
        output = provider.generate_structured(
            system_prompt=_load_prompt(),
            user_prompt=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            output_model=TopicSourceSelectorOutput,
        )
    except Exception as exc:  # noqa: BLE001 - a helper must never end a leg
        return degraded(f"{type(exc).__name__}")
    by_id = {record.source_record_id: record for record in ranked}
    kept: list[TopicSourceRecord] = []
    unknown: list[str] = []
    dimensions: dict[str, int] = {}
    known_dimensions = set(GENERIC_REQUIRED_LANES)

    for item in output.selected[:target_size]:
        record = by_id.get(item.source_record_id)
        if record is None:
            # Not a suggestion to honour. The model may only name what it was shown, and a name it
            # invented is the one thing this step is structurally forbidden to produce.
            unknown.append(item.source_record_id)
            continue
        if any(existing.source_record_id == record.source_record_id for existing in kept):
            continue
        kept.append(record)
        for dimension in item.dimensions:
            if dimension in known_dimensions:
                dimensions[dimension] = dimensions.get(dimension, 0) + 1

    if not kept:
        return degraded("selector returned no usable identifier")

    # Fill from rank order only if the model kept fewer than the target AND did not say it was
    # deliberately keeping fewer. "Do not pad" is in the prompt; honouring a short honest corpus is
    # the point, so a shortfall the model explained is left short.
    # Counted BEFORE the padding below. `kept_by_model` names the records the model chose on
    # content; the loop that follows appends records it never saw a reason to keep. Counting the
    # padded list published "selected 20 of 200 candidates by content" for a selection that chose
    # eight -- and `kept_by_ranking_fallback`, the field a reader subtracts to recover the real
    # number, stayed at its default of zero on this path, so the arithmetic the docstring promises
    # returned the wrong answer rather than an obviously missing one.
    kept_by_the_model = len(kept)
    if len(kept) < target_size and not output.selection_notes.strip():
        for record in ranked:
            if len(kept) >= target_size:
                break
            if all(existing.source_record_id != record.source_record_id for existing in kept):
                kept.append(record)

    # Over the MODEL'S OWN picks, not the padded list. `fallback` is the top `target_size` of
    # `ranked` and the padding loop above fills from the top of `ranked`, so every padded record is
    # in `fallback_ids` by construction. Counting the padded list published "selected 8 of 200
    # candidates by content, 12 of which relevance ranking would also have kept" -- twelve of eight.
    # The number exists to say how much the model agreed with ranking; padding is not agreement.
    fallback_ids = {record.source_record_id for record in fallback}
    agreement = sum(
        1 for record in kept[:kept_by_the_model] if record.source_record_id in fallback_ids
    )

    return TopicSourceSelection(
        records=kept,
        activity=TopicSourceSelectionActivity(
            status="selected_by_model",
            pool_size=len(ranked),
            target_size=target_size,
            model_id=getattr(provider, "model_name", ""),
            kept_by_model=kept_by_the_model,
            kept_by_ranking_fallback=len(kept) - kept_by_the_model,
            dropped_source_record_ids=_dropped_ids(ranked, kept),
            rank_agreement=agreement,
            dimensions_served=dimensions,
            # The UNION of what the model admitted and what the kept records actually carry.
            # Reading only the model's own `uncovered_dimensions` let one free-form field decide a
            # published claim: an empty list printed "every required dimension has at least one
            # record" even when `dimensions_served` -- counted per record, right above -- showed a
            # required lane at zero. The two are independent model outputs and they disagree; the
            # counted one is the one a reader can check against the corpus, and records appended by
            # the rank-order padding below carry no dimension at all.
            uncovered_dimensions=sorted(
                {name for name in known_dimensions if not dimensions.get(name)}
                | {name for name in output.uncovered_dimensions if name in known_dimensions}
            ),
            unknown_identifiers=unknown,
            provider_id=provider.provider_id,
        ),
    )
