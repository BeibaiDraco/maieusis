from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from ...provenance import stable_hash
from .base import StructuredModelProvider

T = TypeVar("T", bound=BaseModel)


class CachedStructuredModelProvider(StructuredModelProvider):
    """Content-addressed cache around a provider for reproducible development."""

    def __init__(
        self, inner: StructuredModelProvider, cache_dir: str | Path = ".maieusis-cache/models"
    ):
        self.inner = inner
        self.cache_dir = Path(cache_dir)
        self.provider_name = f"cached-{inner.provider_name}"
        self.model_name = inner.model_name
        self.policy_decision = getattr(inner, "policy_decision", None)

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
    ) -> T:
        key = stable_hash(
            {
                "provider": self.inner.provider_id,
                "system": system_prompt,
                "user": user_prompt,
                "schema": output_model.model_json_schema(),
            }
        )
        path = self.cache_dir / self.inner.provider_name / self.inner.model_name / f"{key}.json"
        if path.exists():
            return output_model.model_validate_json(path.read_text(encoding="utf-8"))
        parsed = self.inner.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_model=output_model,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(parsed.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return parsed
