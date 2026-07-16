"""Shared host-side import firewall for coarse dataset facts (all sources; agent/model untrusted).

Factored out of GF-2a's ``collect_coarse_facts`` so every source (A documentation, B local sample,
C model self-research) passes the SAME belt-and-suspenders gate:

1. **Belt** — ``assert_proposal_safe_payload`` on the raw source dict before it is trusted/reshaped;
2. **Provenance stamping** — the host owns source-locator / provider / identity fields, and (for
   loose sources B/C) forces every coarse scale fact to be single-source-backed;
3. **Suspenders** — a strict reparse through the target ``CoarseDatasetFacts`` subclass, which re-runs
   the firewall + ``extra="forbid"`` + the reused scale-fact validators.

Any leak, extra key, or malformed value fails closed. The semantic "too-precise / hallucinated"
judgement is out of scope here (GF-2c's fidelity gate).

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from typing import Any, TypeVar

from ...provenance import stable_hash
from ...schemas._r5_firewall import assert_proposal_safe_payload
from ...schemas.coarse_dataset_facts import CoarseDatasetFacts

T = TypeVar("T", bound=CoarseDatasetFacts)


def import_coarse_facts(
    raw: dict[str, Any],
    model_cls: type[T],
    *,
    provenance: dict[str, Any],
    scale_fact_source_ids: list[str] | None = None,
    belt_context: str = "coarse_facts(raw)",
) -> T:
    """Firewall + stamp a raw source dict into a strict coarse-facts model. Fail closed on any leak.

    ``provenance`` overwrites host-owned fields (dataset_id + source-locator/provider/identity).
    ``scale_fact_source_ids`` (B/C) forces every scale fact to be backed by that single source URI and
    synthesizes ids for loose ``{quantity_kind, value_text}`` facts; ``None`` (A) keeps the source's
    own scale-fact ``source_ids`` (e.g. documentation excerpt refs).
    """
    if not isinstance(raw, dict):
        raise ValueError(f"coarse facts payload must be a mapping, got {type(raw).__name__}")
    # Belt: scan the raw source content before it is trusted or reshaped.
    assert_proposal_safe_payload(raw, context=belt_context)

    normalized: dict[str, Any] = dict(raw)
    normalized.update(provenance)
    normalized.pop("content_digest", None)  # host-owned
    normalized.pop("created_at", None)  # host time
    if scale_fact_source_ids is not None:
        normalized["scale_facts"] = [
            _normalize_scale_fact(item, source_ids=scale_fact_source_ids, index=index)
            for index, item in enumerate(raw.get("scale_facts") or [])
        ]

    # Suspenders: the strict schema re-runs the firewall + extra="forbid" + scale-fact validators.
    facts = model_cls.model_validate(normalized)
    return facts.model_copy(update={"content_digest": _content_digest(facts)})


def _normalize_scale_fact(item: Any, *, source_ids: list[str], index: int) -> dict[str, Any]:
    """Force a coarse scale fact to be source-backed + strip any leaky extra keys the source added.

    The host owns scale-fact identity + source-backing. Only the source's ``quantity_kind`` /
    ``value_text`` (and an optional quote) survive; everything else is host-set so a leaky extra key
    on a scale fact cannot reach the strict schema.
    """
    if not isinstance(item, dict):
        raise ValueError("coarse scale_fact must be a mapping")
    quantity_kind = str(item.get("quantity_kind", "")).strip()
    value_text = str(item.get("value_text", "")).strip()
    scale_fact_id = str(item.get("scale_fact_id", "")).strip() or (
        f"coarse-scale-{index}-{stable_hash({'q': quantity_kind, 'v': value_text})[:8]}"
    )
    return {
        "scale_fact_id": scale_fact_id,
        "quantity_kind": quantity_kind,
        "value_text": value_text,
        "source_ids": list(source_ids),
        "quote_or_span": str(item.get("quote_or_span", "")),
        "proposal_safe": True,
        "planner_stage_only": False,
    }


def _content_digest(facts: CoarseDatasetFacts) -> str:
    """Digest only the shared coarse CONTENT (not provenance), so it is comparable across sources."""
    dump = facts.model_dump(mode="json")
    content = {field: dump.get(field) for field in CoarseDatasetFacts.model_fields}
    return stable_hash(content)
