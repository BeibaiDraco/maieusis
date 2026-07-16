from __future__ import annotations

from .anthropic_provider import AnthropicProvider
from .base import ModelConfigurationError, StructuredModelProvider
from .cached import CachedStructuredModelProvider
from .mock import MockStructuredModelProvider
from .openai_provider import OpenAIProvider


def build_model_provider(
    provider: str,
    *,
    model: str = "",
    cache: bool = True,
    allow_pro_model: bool = False,
) -> StructuredModelProvider:
    normalized = provider.strip().lower()
    if normalized == "openai":
        inner: StructuredModelProvider = OpenAIProvider(
            model=model or None,
            allow_pro_model=allow_pro_model,
        )
    elif normalized == "anthropic":
        inner = AnthropicProvider(model=model or None, allow_pro_model=allow_pro_model)
    elif normalized == "mock":
        inner = MockStructuredModelProvider()
    else:
        raise ModelConfigurationError(f"Unknown model provider: {provider}")
    return CachedStructuredModelProvider(inner) if cache and normalized != "mock" else inner
