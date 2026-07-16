from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from pydantic import BaseModel


def _event_sequence(event: BaseModel) -> int:
    return int(cast(Any, event).sequence)


def _event_id(event: BaseModel) -> str:
    return str(cast(Any, event).event_id)


def latest_event_sequence(events: Sequence[BaseModel]) -> int:
    if not events:
        return 0
    verify_contiguous_events(events)
    return _event_sequence(events[-1])


def verify_contiguous_events(events: Sequence[BaseModel]) -> None:
    sequences = [_event_sequence(event) for event in events]
    if sequences != list(range(1, len(sequences) + 1)):
        raise ValueError("events must be contiguous")
    event_ids = [_event_id(event) for event in events]
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("events contain duplicate event IDs")
