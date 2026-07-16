from __future__ import annotations

from pathlib import Path
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel, ConfigDict, field_validator

from ...io import dump_data, load_model

T = TypeVar("T", bound=BaseModel)


def _event_sequence(event: BaseModel) -> int:
    return int(cast(Any, event).sequence)


def _event_id(event: BaseModel) -> str:
    return str(cast(Any, event).event_id)


class BranchEventStoreIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    branch_id: str
    context_id: str = ""
    owner_session_id: str = ""
    question_family_id: str = ""
    question_seed_id: str = ""

    @field_validator("run_id", "branch_id")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("BranchEventStoreIdentity requires run_id and branch_id")
        return value


class FileBackedBranchEventStore(Generic[T]):
    def __init__(
        self,
        root: str | Path,
        *,
        identity: BranchEventStoreIdentity,
        event_model: type[T],
    ) -> None:
        self.root = Path(root)
        self.identity = identity
        self.event_model = event_model

    @property
    def branch_root(self) -> Path:
        return self.root / self.identity.run_id / "branches" / self.identity.branch_id

    @property
    def events_dir(self) -> Path:
        return self.branch_root / "events"

    def append(self, event: T) -> Path:
        self._verify_event_identity(event)
        events: list[T] = self.load_events()
        expected_sequence = len(events) + 1
        if _event_sequence(event) != expected_sequence:
            raise ValueError("event sequence must be next contiguous value")
        event_ids = {_event_id(existing) for existing in events}
        if _event_id(event) in event_ids:
            raise ValueError("event_id already exists in branch event store")
        path = self._event_path(event)
        if path.exists():
            raise ValueError("event file already exists")
        self.events_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f".{path.stem}.tmp.yaml")
        dump_data(event, tmp_path)
        tmp_path.replace(path)
        return path

    def load_events(self) -> list[T]:
        if not self.events_dir.exists():
            return []
        paths = sorted(
            path
            for path in self.events_dir.glob("*.yaml")
            if not path.name.startswith(".") and not path.name.endswith(".tmp")
        )
        events = [load_model(path, self.event_model) for path in paths]
        self._verify_event_sequence(events)
        for event in events:
            self._verify_event_identity(event)
        return events

    def _event_path(self, event: T) -> Path:
        sequence = _event_sequence(event)
        event_id = _event_id(event)
        safe_event_id = "".join(
            char if char.isalnum() or char in "-_" else "_" for char in event_id
        )
        return self.events_dir / f"{sequence:06d}-{safe_event_id}.yaml"

    def _verify_event_sequence(self, events: list[T]) -> None:
        sequences = [_event_sequence(event) for event in events]
        if sequences != list(range(1, len(sequences) + 1)):
            raise ValueError("branch event store events must be contiguous")
        event_ids = [_event_id(event) for event in events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("branch event store contains duplicate event IDs")

    def _verify_event_identity(self, event: T) -> None:
        for field_name, expected in self.identity.model_dump(mode="python").items():
            if not expected or not hasattr(event, field_name):
                continue
            if getattr(event, field_name) != expected:
                raise ValueError(f"event references another {field_name}")
