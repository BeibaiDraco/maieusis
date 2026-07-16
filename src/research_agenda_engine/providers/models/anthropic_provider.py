from __future__ import annotations

import os
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ..capture import capture_enabled, capture_paid_leaf
from .base import (
    ModelConfigurationError,
    StructuredModelFailureKind,
    StructuredModelProvider,
    StructuredModelProviderError,
)
from .policy import ModelPolicyDecision, ensure_model_allowed

T = TypeVar("T", bound=BaseModel)


class AnthropicProvider(StructuredModelProvider):
    """Claude Messages API adapter using SDK-native Pydantic parsing."""

    provider_name = "anthropic"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        *,
        allow_pro_model: bool = False,
    ):
        resolved_model = model or os.getenv("ANTHROPIC_MODEL")
        if not resolved_model:
            raise ModelConfigurationError("Anthropic model is not configured")
        self.policy_decision: ModelPolicyDecision = ensure_model_allowed(
            provider=self.provider_name,
            model=resolved_model,
            allow_pro_model=allow_pro_model,
        )
        try:
            import anthropic
        except ImportError as exc:
            raise ModelConfigurationError("Anthropic provider dependency is unavailable") from exc

        self.model_name = resolved_model
        self._client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
    ) -> T:
        try:
            response = self._client.messages.parse(
                model=self.model_name,
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                output_format=output_model,
            )
        except (TypeError, AssertionError):
            raise
        except ValidationError as exc:
            raise StructuredModelProviderError(
                StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=self.provider_id,
            ) from exc
        except Exception as exc:
            kind = _anthropic_failure_kind(exc)
            if kind is None:
                raise
            raise StructuredModelProviderError(kind, provider_id=self.provider_id) from exc
        parsed = response.parsed_output
        if parsed is None:
            raise StructuredModelProviderError(
                StructuredModelFailureKind.INVALID_RESPONSE,
                provider_id=self.provider_id,
            )
        if capture_enabled():  # guard so the response dump only runs when an operator opts in
            capture_paid_leaf(
                "models.anthropic.generate_structured",
                request={
                    "model": self.model_name,
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "output_model": output_model.__name__,
                },
                response=parsed.model_dump(mode="json"),
                model=self.model_name,
            )
        return parsed


def _anthropic_failure_kind(exc: Exception) -> StructuredModelFailureKind | None:
    name = type(exc).__name__
    if name in {"AuthenticationError", "PermissionDeniedError"}:
        return StructuredModelFailureKind.AUTHENTICATION
    if name == "RateLimitError":
        return StructuredModelFailureKind.RATE_LIMIT
    if name in {"APITimeoutError", "TimeoutError"}:
        return StructuredModelFailureKind.TIMEOUT
    if name in {"APIConnectionError", "ConnectionError"}:
        return StructuredModelFailureKind.CONNECTION
    if name == "InternalServerError" or (
        name == "APIStatusError" and int(getattr(exc, "status_code", 0) or 0) >= 500
    ):
        return StructuredModelFailureKind.SERVER_ERROR
    if name in {"APIResponseValidationError", "JSONDecodeError"}:
        return StructuredModelFailureKind.INVALID_RESPONSE
    return None
