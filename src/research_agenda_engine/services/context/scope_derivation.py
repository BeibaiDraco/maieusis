"""Ask a model which literature this dataset's field is, by showing it the dataset and nothing else.

WHY THIS EXISTS is recorded in ``schemas/derived_dataset_scope.py`` -- two release configs searching
byte-identical generic terms for two unrelated datasets, both candidate pools exhausted, and the
dimensions the independent reviewer grades on missing from the corpus because no query ever asked
for them.

Three rules keep this from becoming failures this repository has already paid for.

1. **It reads the dataset, and only the dataset.** The payload is built from an explicit allowlist of
   ``DatasetNarrative`` scope fields (``NARRATIVE_SCOPE_FIELDS``), so review status, reviewer notes,
   digests and generator identity cannot reach the model even as the narrative grows new fields. It
   never sees a gate criterion, a verdict, a ``required_changes`` entry or an authority ceiling: it
   is asked once, before any literature exists and long before any review, so it is not a loop and
   cannot optimise toward approval. It is shown the eight semantic dimensions a corpus is later read
   along -- an operator ruling of 2026-08-17, on the precedent that
   ``prompts/topic_source_selector/v1.md`` already shows the corpus selector the same list, and on
   the measurement that a term set naming no controversy and no reuse is exactly what failed.

2. **Its output is counted, and every term is checked against reality.** Each proposed term is
   measured against the same scholarly index the run will search. A term with a literature of zero
   is dropped and said so; a term the probe could not reach is KEPT and recorded as unmeasured,
   because conflating "no literature" with "no answer from the index" would discard good terms on
   the strength of a failed HTTP request. ``deterministic_overlap`` records how much of this a
   keyword extractor would have produced anyway -- a derivation that changed nothing says so.

3. **Failure degrades, never stops.** Any provider error, schema violation, or empty result falls
   back to ``deterministic_narrative_terms`` -- the same function open mode uses when no model runs
   -- with the exception CLASS NAME recorded and the provider's message deliberately discarded,
   because provider text can carry signed URLs and account identifiers (hard rule 13). A leg must
   not die because a scope helper had a bad night. The one case that is not recoverable is a
   narrative so thin that neither lane yields a single term; that is a scientific terminal, and the
   caller raises rather than searching for nothing.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...assets import resolve_asset
from ...provenance import stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas.dataset_narrative import DatasetNarrative
from ...schemas.derived_dataset_scope import (
    DATASET_SCOPE_DERIVER_PROMPT_VERSION,
    TERM_POOL_UNMEASURED,
    DerivedDatasetScope,
    DerivedScopeStatus,
    DerivedScopeTerm,
)
from ...schemas.research_intent import ResearchIntent, ResearchIntentMode, ScopeDerivationMode
from ..retrieval.generic_topic_lanes import GENERIC_REQUIRED_LANES
from ..retrieval.openalex_scope import TopicTermPoolReport, probe_topic_term_pools
from .research_scope import config_declared_scope_terms, deterministic_narrative_terms

#: Declared here rather than imported from `services.preflight`: preflight imports this module's
#: siblings, and a context module reaching back into preflight would invert the dependency.
TopicTermPoolProbe = Callable[..., TopicTermPoolReport]

#: The narrative fields the deriver is allowed to see, named explicitly rather than by exclusion.
#: An allowlist survives the narrative gaining a field; a denylist silently leaks the next one.
NARRATIVE_SCOPE_FIELDS = (
    "scientific_purpose",
    "population",
    "broad_interventions",
    "broad_scale",
    "scale_facts",
    "hierarchical_structure",
    "modalities",
    "major_variables",
    "reuse_opportunities",
    "known_high_level_limitations",
)

#: The band the prompt asks for. Below the floor the candidate pool measurably ran dry on two legs;
#: above the ceiling the scope spans more than one literature review can honestly serve, which is
#: how a hand-written sixteen-term list started failing `scope_fidelity`.
DERIVED_TERM_FLOOR = 12
DERIVED_TERM_CEILING = 18
# The word-count band a usable search phrase falls in. The deriver prompt asks a model for two or
# three words and accepts four when the field genuinely uses them; the degrade path applies the same
# shape to keyword extraction's output.
DERIVED_TERM_BAND = (2, 4)


class DerivedScopeTermProposal(BaseModel):
    """What the model may say about one term. It may not name an id, a version or a digest."""

    model_config = ConfigDict(extra="forbid")

    term: str
    why: str = ""
    dataset_basis: list[str] = Field(default_factory=list)


class DatasetScopeDeriverOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    terms: list[DerivedScopeTermProposal] = Field(default_factory=list)
    dataset_identity_terms: list[str] = Field(default_factory=list)
    construct_families: list[str] = Field(default_factory=list)
    derivation_notes: str = ""


def _load_prompt() -> str:
    return resolve_asset(
        Path("prompts") / Path(DATASET_SCOPE_DERIVER_PROMPT_VERSION).with_suffix(".md")
    ).read_text(encoding="utf-8")


def _narrative_payload(narrative: DatasetNarrative) -> dict[str, object]:
    return {field: getattr(narrative, field) for field in NARRATIVE_SCOPE_FIELDS}


def _dedupe(values: Sequence[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = value.strip()
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def scope_derivation_applies(intent: ResearchIntent) -> bool:
    """Whether a model would be asked at all, decided from the intent alone.

    Kept separate from the derivation so a caller can answer "will this run spend a model call on
    scope?" without building a payload, and so the answer is one expression rather than a condition
    repeated at the call site and in the tests that guard it.
    """

    if intent.scope_derivation == ScopeDerivationMode.NEVER:
        return False
    if intent.scope_derivation == ScopeDerivationMode.AUGMENT:
        return True
    # AUTO: the declared terms win outright wherever there are any, which is every mode but `open`.
    return intent.mode == ResearchIntentMode.OPEN and not config_declared_scope_terms(intent)


def _inactive(
    narrative: DatasetNarrative, status: DerivedScopeStatus, deterministic: Sequence[str]
) -> DerivedDatasetScope:
    return DerivedDatasetScope(
        scope_id=f"derived-scope-{narrative.dataset_id}",
        status=status,
        dataset_id=narrative.dataset_id,
        narrative_id=narrative.dataset_narrative_id,
        deterministic_terms=list(deterministic),
    )


def _degraded_term_rank(term: str) -> tuple[int, int]:
    """Sort key for the degrade path: the phrase band first, then everything else by length.

    `DERIVED_TERM_BAND` is the shape the deriver prompt asks a model for ("prefer two or three
    words"), and it is also what the narrative's own curated fields already contain. Ranking by it
    keeps the phrases when the model cannot be reached.
    """

    words = len(term.split())
    low, high = DERIVED_TERM_BAND
    return (0 if low <= words <= high else 1, words)


def derive_dataset_scope(
    *,
    provider: StructuredModelProvider | None,
    narrative: DatasetNarrative,
    intent: ResearchIntent,
    research_field: str = "",
    openalex_email: str = "",
    openalex_api_key: str = "",
    pool_probe: TopicTermPoolProbe = probe_topic_term_pools,
    literature_enabled: bool = True,
) -> DerivedDatasetScope:
    """Derive this run's default search terms from the dataset's reviewed narrative.

    Always returns a record, including for the runs where no model was asked: a step that files
    nothing when it does nothing is indistinguishable from a step that shipped inert, and this
    repository has already published a feature that passed a conformance audit while producing zero
    output on 26 of 26 runs.
    """

    deterministic = deterministic_narrative_terms(narrative)
    narrative_digest = stable_hash(_narrative_payload(narrative))

    if not literature_enabled:
        return _inactive(narrative, DerivedScopeStatus.LITERATURE_DISABLED, deterministic)
    if intent.scope_derivation == ScopeDerivationMode.NEVER:
        return _inactive(narrative, DerivedScopeStatus.DISABLED_BY_CONFIG, deterministic)
    if not scope_derivation_applies(intent):
        return _inactive(narrative, DerivedScopeStatus.USER_DECLARED_SCOPE, deterministic)

    payload = {
        "prompt_version": DATASET_SCOPE_DERIVER_PROMPT_VERSION,
        "dataset": _narrative_payload(narrative),
        "semantic_dimensions": list(GENERIC_REQUIRED_LANES),
        "term_band": {"minimum": DERIVED_TERM_FLOOR, "maximum": DERIVED_TERM_CEILING},
        # Shown so the deriver does not spend its budget restating terms the user already wrote.
        # Empty in every mode but AUGMENT.
        "already_declared_by_user": config_declared_scope_terms(intent),
    }
    input_digest = stable_hash(payload)

    def degraded(reason: str, rationales: Sequence[DerivedScopeTerm] = ()) -> DerivedDatasetScope:
        # The SAME ceiling the model path obeys. Without it the fallback was uncapped: measured
        # 2026-08-18 against the live ibl narrative with a provider that raises, the degraded scope
        # carried 42 terms and `augment` resolved to 43 -- against 18 on the success path -- five of
        # them sentence-length phrases ("Mouse pose and movement information from video and
        # DeepLabCut analysis") that retrieve nothing under exact-phrase matching. A degradation is
        # supposed to be a smaller, honest scope, not a wider unmeasured one, and term count is the
        # variable this card measured `scope_fidelity` collapsing on: 15 terms failed it 0/15, 22
        # failed it 13/14. One transient provider error would have done that to a paid leg.
        #
        # THE BAND, not an end of the list. Deterministic extraction returns two populations mixed
        # together: the narrative's curated field values, which are two-to-four-word phrases a
        # scholar would type, and single words from keyword extraction over the reuse prose.
        # Measured 2026-08-18 on the retained neuroscience narrative: 84 terms, 67 single words. Taking
        # the shortest filled all eighteen slots with single words -- `across`, `broad`, `develop`,
        # `new`, `scientific` -- and discarded `neural activity`, `brain area identity` and
        # `visual stimulus features`. Under exact-phrase matching that is worse than the uncapped
        # list it replaced, which at least contained the phrases. Taking the longest keeps the
        # whole-sentence entries, which retrieve nothing. So: two-to-four words first, then whatever
        # is left, shortest first, so a short honest scope tops up with words rather than sentences.
        capped = sorted(deterministic, key=_degraded_term_rank)[:DERIVED_TERM_CEILING]
        return DerivedDatasetScope(
            scope_id=f"derived-scope-{narrative.dataset_id}",
            status=DerivedScopeStatus.DEGRADED_TO_DETERMINISTIC,
            terms=capped,
            construct_families=_dedupe(narrative.major_variables),
            # Kept even though none of them survived. Measured 2026-08-17: the first live derivation
            # degraded with "every derived term has an empty literature", and because the proposals
            # were discarded there was no way to see WHICH phrases the model had written or why the
            # index refused them -- the diagnosis had to be re-bought. A degradation that throws
            # away its own evidence makes the next one just as expensive.
            term_rationales=list(rationales),
            dataset_id=narrative.dataset_id,
            narrative_id=narrative.dataset_narrative_id,
            narrative_digest=narrative_digest,
            # The full extraction is retained so a reader can see what the cap dropped.
            deterministic_terms=list(deterministic),
            deterministic_overlap=len(capped),
            input_digest=input_digest,
            output_digest=stable_hash({"terms": capped}),
            degraded_reason=reason,
            provider_id=provider.provider_id if provider is not None else "",
            # The model whose call was paid for and failed. `provider_id` was recorded here and
            # `model_id` was not, so a degradation named the vendor and not the model -- and the
            # model is what an operator changes. Measured 2026-08-19 by injecting one provider error
            # into a live dataset half: `status: degraded_to_deterministic`, `provider_id` set,
            # `model_id: ''`. The sibling selection record carried the same asymmetry and was
            # repaired an hour earlier; this one was not checked at the same time, which is the
            # instance-not-class mistake this card exists to stop repeating.
            model_id=getattr(provider, "model_name", "") if provider is not None else "",
        )

    if provider is None:
        return degraded("no scope deriver provider configured")

    try:
        output = provider.generate_structured(
            system_prompt=_load_prompt(),
            user_prompt=json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
            output_model=DatasetScopeDeriverOutput,
        )
    except Exception as exc:  # noqa: BLE001 - a scope helper must never end a leg
        # CLASS NAME ONLY: a provider message can carry a signed URL or an account identifier, and
        # those must not reach an artifact (hard rule 13).
        return degraded(type(exc).__name__)

    proposed = _dedupe([item.term for item in output.terms])[:DERIVED_TERM_CEILING]
    if not proposed:
        return degraded("deriver returned no usable term")

    report = _measure_pools(
        proposed,
        probe=pool_probe,
        research_field=research_field,
        openalex_email=openalex_email,
        openalex_api_key=openalex_api_key,
    )
    pools = {pool.term: pool for pool in report.pools} if report is not None else {}

    rationales: list[DerivedScopeTerm] = []
    kept: list[str] = []
    by_term = {item.term.strip().lower(): item for item in output.terms}
    for term in proposed:
        source = by_term.get(term.lower())
        pool = pools.get(term)
        # An unmeasured term is KEPT. Only a term the index positively reports as empty is dropped,
        # and only then is the drop attributable to the term rather than to the probe.
        measured_empty = pool is not None and pool.measured and pool.pool == 0
        rationales.append(
            DerivedScopeTerm(
                term=term,
                why=(source.why if source is not None else ""),
                dataset_basis=list(source.dataset_basis) if source is not None else [],
                kept=not measured_empty,
                pool=(pool.pool if pool is not None and pool.measured else TERM_POOL_UNMEASURED),
                dropped_reason=(
                    "no works match this phrase in the index" if measured_empty else ""
                ),
            )
        )
        if not measured_empty:
            kept.append(term)

    if not kept:
        return degraded("every derived term has an empty literature", rationales)

    deterministic_lower = {value.lower() for value in deterministic}
    return DerivedDatasetScope(
        scope_id=f"derived-scope-{narrative.dataset_id}",
        status=DerivedScopeStatus.DERIVED_BY_MODEL,
        terms=kept,
        construct_families=_dedupe(output.construct_families),
        term_rationales=rationales,
        derivation_notes=output.derivation_notes,
        dataset_id=narrative.dataset_id,
        narrative_id=narrative.dataset_narrative_id,
        narrative_digest=narrative_digest,
        deterministic_terms=list(deterministic),
        deterministic_overlap=sum(1 for term in kept if term.lower() in deterministic_lower),
        provider_id=provider.provider_id,
        # `model_name`, not `model_id`: the provider protocol names it `model_name`
        # (`providers/models/cached.py:24`, and every sibling step reads it that way --
        # `services/context/topic_evidence.py:739,787,799`). Reading the wrong attribute through
        # `getattr(..., "")` recorded an EMPTY model identity on a live artifact without raising,
        # which is the shape of defect that survives every test and is only visible in the output.
        # Caught 2026-08-18 by reading the artifact a live `run_dataset_half` actually wrote.
        model_id=getattr(provider, "model_name", ""),
        dataset_identity_terms=_dedupe(output.dataset_identity_terms),
        input_digest=input_digest,
        output_digest=stable_hash(
            {"terms": kept, "construct_families": _dedupe(output.construct_families)}
        ),
    )


def _measure_pools(
    terms: Sequence[str],
    *,
    probe: TopicTermPoolProbe,
    research_field: str,
    openalex_email: str,
    openalex_api_key: str,
) -> TopicTermPoolReport | None:
    """Count each term's literature, and treat any failure here as "not measured", never as zero."""

    try:
        return probe(
            terms,
            research_field=research_field,
            openalex_email=openalex_email,
            openalex_api_key=openalex_api_key,
        )
    except Exception:  # noqa: BLE001 - a free check must never become a reason a run cannot start
        return None
