from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from ...schemas.gate_outcome import ReviewerExecutionKind
from .base import StructuredModelProvider

T = TypeVar("T", bound=BaseModel)


class MockModelProvider(StructuredModelProvider):
    provider_name = "mock"
    model_name = "deterministic-fixture"

    def __init__(self, factory: Callable[[type[BaseModel], str, str], Any] | None = None):
        self.factory = factory

    @property
    def execution_kind(self) -> ReviewerExecutionKind:
        return ReviewerExecutionKind.MOCK

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
    ) -> T:
        if self.factory is None:
            raise RuntimeError(
                "MockModelProvider needs a factory for this call. The offline demo uses "
                "template generation and does not call a model."
            )
        value = self.factory(output_model, system_prompt, user_prompt)
        return output_model.model_validate(value)


MockStructuredModelProvider = MockModelProvider
