from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TypeVar

from pydantic import BaseModel

from ...schemas.gate_outcome import ReviewerExecutionKind

T = TypeVar("T", bound=BaseModel)


class StructuredModelFailureKind(StrEnum):
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    SERVER_ERROR = "server_error"
    INVALID_RESPONSE = "invalid_response"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"


class StructuredModelProviderError(RuntimeError):
    """Finite, secret-free failure emitted by a structured model adapter."""

    def __init__(self, kind: StructuredModelFailureKind, *, provider_id: str):
        self.kind = kind
        self.provider_id = provider_id
        super().__init__(f"structured model provider failed: {kind.value}")


class ModelConfigurationError(ValueError):
    """A configured provider cannot be constructed without operator/config changes."""


class StructuredModelProvider(ABC):
    """Vendor-neutral interface for typed runtime model calls.

    Codex is the development/runtime shell in the intended workflow; this interface is
    for API model calls made by Maieusis itself.
    """

    provider_name: str
    model_name: str

    @property
    def provider_id(self) -> str:
        return f"{self.provider_name}:{self.model_name}"

    @property
    def execution_kind(self) -> ReviewerExecutionKind:
        """How this provider runs. Concrete default is a LIVE API; the mock provider overrides to MOCK.

        Type-side signal (see ``ReviewerExecutionKind``): a real provider inherits ``LIVE_API``; only
        ``MockModelProvider`` returns ``MOCK``. Used where a gate builds its outcome from a
        ``StructuredModelProvider`` reviewer (e.g. consolidation) so the outcome records execution kind.
        """
        return ReviewerExecutionKind.LIVE_API

    @abstractmethod
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
    ) -> T:
        raise NotImplementedError
