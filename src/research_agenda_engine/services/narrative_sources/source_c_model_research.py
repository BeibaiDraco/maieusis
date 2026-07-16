"""Source C — model self-research coarse facts.

A frontier model is given only the dataset name + seed link and asked to WEB-SEARCH and return COARSE,
proposal-safe facts (no agent spawn — a templated web-search API call). It is the LOWEST-trust of the
three sources (it may cite unverified web sources or hallucinate), so its output carries
``low_trust=True`` + the web-search citations and passes through the SAME host import firewall as the
others (fail-closed on any exact schema/count leak). The semantic "too-precise / hallucinated"
judgement is deferred to GF-2c's fidelity gate.

Source C is OPTIONAL and degradable: if web search is unavailable the call raises and the caller lets
Source A carry the documentation side alone. A/C stay independent functions (no assembly here).

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from ...providers.models.web_search_provider import WebSearchModelProvider
from ...schemas.coarse_dataset_facts import CoarseFactsModelOutput, CoarseModelResearchFacts
from ...schemas.dataset_seed import DatasetSeed
from .coarse_facts_import import import_coarse_facts

MODEL_RESEARCH_LOCATOR_SCHEME = "api-model-self-research"
MODEL_RESEARCH_PROMPT_VERSION = "coarse_model_research/v1"

_SYSTEM_PROMPT = """You are a dataset research assistant for Maieusis, a multi-agent scientific
question-development system. Maieusis is assembling a COARSE, proposal-stage description of a dataset
that a Question Scientist will later use to inspire broad research questions. You are the
model-self-research source: use web search to learn about the named dataset, then return COARSE,
proposal-safe facts in the required schema.

Rules (a strict firewall rejects violations, so follow them exactly):
- Report only COARSE kinds and structure: recording/measurement modalities, order-of-magnitude or
  approximate scale, coarse hierarchy/temporal structure, the task or experimental design, coarse
  spatial/anatomical scope, standardization/packaging, broad variable families, and high-level
  limitations.
- NEVER report exact column or field names, table schemas, or exact row/trial/session/unit counts.
  Every number must be order-of-magnitude or approximate (for example 'tens of', 'order of a few
  hundred', 'roughly').
- Mark uncertainty explicitly in the relevant field when you are unsure; never invent specifics.
- Do not use execution/analysis vocabulary. Rely on and cite reputable web sources.
"""


def model_research_source_locator(provider_id: str) -> str:
    return f"{MODEL_RESEARCH_LOCATOR_SCHEME}://{provider_id.replace(':', '/')}"


def build_model_research_coarse_facts(
    *,
    seed: DatasetSeed,
    web_search_provider: WebSearchModelProvider,
    dataset_name: str = "",
    max_web_searches: int = 5,
) -> CoarseModelResearchFacts:
    """Web-search the named dataset, firewall the result into ``CoarseModelResearchFacts``.

    Raises if the web-search call fails; the caller (GF-2c) treats Source C as optional and falls back
    to Source A for the documentation side.
    """
    name = dataset_name.strip() or seed.dataset_id
    result = web_search_provider.research_structured(
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=(
            f"Research the dataset `{name}` (reference: {seed.link}). "
            "Return coarse, proposal-safe facts about it in the required schema."
        ),
        output_model=CoarseFactsModelOutput,
        max_web_searches=max_web_searches,
    )
    output = result.parsed
    locator = model_research_source_locator(result.provider_id)
    raw = {
        "dataset_id": seed.dataset_id,
        "modalities": list(output.modalities),
        "broad_scale": output.broad_scale,
        "coarse_structure": output.coarse_structure,
        "task_or_design": output.task_or_design,
        "spatial_or_anatomical_coverage": output.spatial_or_anatomical_coverage,
        "standardization": output.standardization,
        "major_variables": list(output.major_variables),
        "known_coarse_limitations": list(output.known_coarse_limitations),
        "scale_facts": [fact.model_dump() for fact in output.scale_facts],
    }
    return import_coarse_facts(
        raw,
        CoarseModelResearchFacts,
        provenance={
            "dataset_id": seed.dataset_id,
            "source_locator": locator,
            "provider_id": result.provider_id,
            "model_id": result.model_id,
            "web_search_citations": [citation.model_dump() for citation in result.citations],
            "low_trust": True,
        },
        scale_fact_source_ids=[locator],
        belt_context="model_research_coarse_facts(raw)",
    )
