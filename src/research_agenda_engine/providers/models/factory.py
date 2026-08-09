from __future__ import annotations

from .anthropic_provider import AnthropicProvider
from .base import (
    DEFAULT_EFFORT,
    DEFAULT_THINKING,
    ModelConfigurationError,
    StructuredModelProvider,
)
from .cached import CachedStructuredModelProvider
from .mock import MockStructuredModelProvider
from .openai_provider import OpenAIProvider


def build_model_provider(
    provider: str,
    *,
    model: str = "",
    cache: bool = True,
    allow_pro_model: bool = False,
    thinking: str = DEFAULT_THINKING,
    effort: str = DEFAULT_EFFORT,
) -> StructuredModelProvider:
    """Build a role's provider. ``thinking`` and ``effort`` default to the vendor behaviour the
    2026-07-31 leg ran on, so an unchanged caller keeps its baseline while the value stops being
    invisible."""
    normalized = provider.strip().lower()
    if normalized == "openai":
        inner: StructuredModelProvider = OpenAIProvider(
            model=model or None,
            allow_pro_model=allow_pro_model,
            thinking=thinking,
            effort=effort,
        )
    elif normalized == "anthropic":
        inner = AnthropicProvider(
            model=model or None,
            allow_pro_model=allow_pro_model,
            thinking=thinking,
            effort=effort,
        )
    elif normalized == "mock":
        inner = MockStructuredModelProvider()
    else:
        raise ModelConfigurationError(f"Unknown model provider: {provider}")
    return CachedStructuredModelProvider(inner) if cache and normalized != "mock" else inner
