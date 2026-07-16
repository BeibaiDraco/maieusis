from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...assets import resolve_asset
from ...io import dump_data
from ...provenance import stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas.question_scientist_context_v2 import QuestionScientistContextPayloadV2
from ...schemas.question_seed import QuestionSeed, QuestionSeedBatch
from .generation_mirrors import QuestionSeedModelOutput

QUESTION_SCIENTIST_PROMPT_VERSION = "question_scientist/v1"


class _QuestionScientistModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seeds: list[QuestionSeedModelOutput] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_seed_candidates(self) -> _QuestionScientistModelOutput:
        if not self.seeds:
            raise ValueError("Question Scientist output requires at least one seed")
        return self


def generate_question_seed_batch(
    *,
    provider: StructuredModelProvider,
    context_payload: QuestionScientistContextPayloadV2,
    seed_count: int = 12,
    max_prompt_chars: int = 300_000,
    selected_pattern_ids: list[str] | None = None,
    proposer_branch_id: str = "",
    context_subset_digest: str = "",
) -> QuestionSeedBatch:
    if seed_count < 1 or seed_count > 20:
        raise ValueError("seed_count must be between 1 and 20")
    user_packet = build_question_scientist_user_packet(
        context_payload,
        seed_count=seed_count,
        provider_id=provider.provider_id,
        selected_pattern_ids=selected_pattern_ids,
        proposer_branch_id=proposer_branch_id,
        context_subset_digest=context_subset_digest,
    )
    user_prompt = json.dumps(user_packet, sort_keys=True, ensure_ascii=False)
    if len(user_prompt) > max_prompt_chars:
        raise ValueError("Question Scientist context packet exceeds prompt budget")
    output = provider.generate_structured(
        system_prompt=_load_prompt(QUESTION_SCIENTIST_PROMPT_VERSION),
        user_prompt=user_prompt,
        output_model=_QuestionScientistModelOutput,
    )
    input_digest = stable_hash(user_packet)
    return _force_question_seed_batch(
        output,
        context_payload=context_payload,
        provider_id=provider.provider_id,
        input_digest=input_digest,
    )


def build_question_scientist_user_packet(
    context_payload: QuestionScientistContextPayloadV2,
    *,
    seed_count: int,
    provider_id: str,
    selected_pattern_ids: list[str] | None = None,
    proposer_branch_id: str = "",
    context_subset_digest: str = "",
) -> dict:
    context_payload_dict = context_payload.model_dump(mode="json")
    all_pattern_cards = context_payload.paperbank_patterns.pattern_cards
    selected_pattern_ids = selected_pattern_ids or [card.pattern_id for card in all_pattern_cards]
    selected_pattern_set = set(selected_pattern_ids)
    selected_pattern_cards = [
        card for card in all_pattern_cards if card.pattern_id in selected_pattern_set
    ]
    if not selected_pattern_cards:
        raise ValueError("Question Scientist proposer branch selected no pattern cards")
    pattern_ids = [card.pattern_id for card in selected_pattern_cards]
    context_payload_dict["paperbank_patterns"] = {
        **context_payload_dict["paperbank_patterns"],
        "pattern_cards": [card.model_dump(mode="json") for card in selected_pattern_cards],
    }
    topic_claim_ids = [claim.claim_id for claim in context_payload.topic_literature.claim_cards]
    topic_source_record_ids = [
        source.source_record_id for source in context_payload.topic_literature.source_cards
    ]
    instructions: dict[str, Any] = {
        "return_only": "QuestionSeedBatch.seeds payload via structured output",
        "do_not_generate_question_cards": True,
        "do_not_generate_analysis_contracts": True,
        "do_not_claim_feasibility": True,
        "exact_schema_or_column_details_forbidden": True,
        "positive_negative_null_consequences_required": True,
    }
    if proposer_branch_id:
        instructions["respect_proposer_branch_pattern_subset"] = True
    packet = {
        "prompt_version": QUESTION_SCIENTIST_PROMPT_VERSION,
        "context_id": context_payload.context_id,
        "context_digest": context_payload.context_digest,
        "proposer_branch_id": proposer_branch_id,
        "context_subset_digest": context_subset_digest,
        "origin_provider_id": provider_id,
        "seed_count_requested": seed_count,
        "allowed_pattern_ids": pattern_ids,
        "allowed_topic_claim_ids": topic_claim_ids,
        "allowed_topic_source_record_ids": topic_source_record_ids,
        "context_payload": context_payload_dict,
        "instructions": instructions,
    }
    return packet


def write_question_seed_batch(
    batch: QuestionSeedBatch,
    *,
    corpus_root: str | Path = "corpus",
) -> Path:
    root = Path(corpus_root) / "question_seeds"
    return dump_data(batch, root / f"{batch.batch_id}.question_seed_batch.yaml")


def _force_question_seed_batch(
    output: _QuestionScientistModelOutput,
    *,
    context_payload: QuestionScientistContextPayloadV2,
    provider_id: str,
    input_digest: str,
) -> QuestionSeedBatch:
    seeds: list[QuestionSeed] = []
    seen_ids: set[str] = set()
    for index, seed in enumerate(output.seeds, start=1):
        seed_id = seed.question_seed_id.strip() or f"qseed-{index:03d}"
        if seed_id in seen_ids:
            seed_id = f"qseed-{index:03d}"
        seen_ids.add(seed_id)
        # Rebuild as the strict QuestionSeed (not model_copy): the strict validators re-run
        # with the code-stamped values, so a mirror instance can never leak downstream.
        seeds.append(
            QuestionSeed.model_validate(
                {
                    **seed.model_dump(mode="python"),
                    "question_seed_id": seed_id,
                    "context_id": context_payload.context_id,
                    "origin_provider_id": provider_id,
                    "prompt_version": QUESTION_SCIENTIST_PROMPT_VERSION,
                }
            )
        )
    batch_payload = {
        "batch_id": f"question-seed-batch-{stable_hash({'context': context_payload.context_digest, 'input': input_digest, 'seeds': [seed.model_dump(mode='json') for seed in seeds]})[:12]}",
        "context_id": context_payload.context_id,
        "context_digest": context_payload.context_digest,
        "input_digest": input_digest,
        "seeds": seeds,
        "origin_provider_id": provider_id,
        "prompt_version": QUESTION_SCIENTIST_PROMPT_VERSION,
    }
    return QuestionSeedBatch.model_validate(batch_payload)


def _load_prompt(prompt_version: str) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")
