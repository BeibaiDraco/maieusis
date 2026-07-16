"""Generic dataset-seed narrative source provider.

Replaces the hand-coded dataset-specific narrative provider: given ANY ``DatasetSeed`` (a ``dataset_id`` + one
``link``), resolve the link to proposal-safe excerpts and assemble the existing
``DatasetNarrativeSourcePacket``. The link is the only input consumed here; ``seed.docs`` is reserved
for GF-2c's Source D. Every network entry point is injectable so the mock suite runs with zero HTTP.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ...schemas.dataset_seed import DatasetSeed
from ..context.dataset_narrative import (
    DatasetNarrativeSourcePacket,
    build_dataset_narrative_source_packet,
)
from ..retrieval.dataset_seed_retrieval import (
    BytesGetter,
    JsonGetter,
    TextGetter,
    http_get_bytes,
    http_get_json,
    http_get_text,
    resolve_seed_link,
)


@runtime_checkable
class NarrativeSourceProvider(Protocol):
    """Builds a proposal-safe source packet from a dataset seed."""

    provider_id: str

    def build_source_packet(self, seed: DatasetSeed) -> DatasetNarrativeSourcePacket: ...


class GenericNarrativeSourceProvider:
    """Resolve a seed's LINK to excerpts, then assemble a ``DatasetNarrativeSourcePacket``."""

    provider_id = "generic_narrative_sources/v1"

    def __init__(
        self,
        *,
        http_get_text: TextGetter = http_get_text,
        http_get_json: JsonGetter = http_get_json,
        http_get_bytes: BytesGetter = http_get_bytes,
        max_excerpt_chars: int = 1600,
    ) -> None:
        self.http_get_text = http_get_text
        self.http_get_json = http_get_json
        self.http_get_bytes = http_get_bytes
        self.max_excerpt_chars = max_excerpt_chars

    def build_source_packet(self, seed: DatasetSeed) -> DatasetNarrativeSourcePacket:
        excerpts = resolve_seed_link(
            seed.link,
            dataset_id=seed.dataset_id,
            http_get_text=self.http_get_text,
            http_get_json=self.http_get_json,
            http_get_bytes=self.http_get_bytes,
            max_excerpt_chars=self.max_excerpt_chars,
        )
        return build_dataset_narrative_source_packet(
            dataset_id=seed.dataset_id,
            source_excerpts=excerpts,
        )
