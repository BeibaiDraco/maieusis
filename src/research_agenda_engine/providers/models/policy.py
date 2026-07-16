from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import StrEnum

from .base import ModelConfigurationError


class ModelTier(StrEnum):
    MOCK = "mock"
    STANDARD = "standard"
    PRO_EXPENSIVE = "pro_expensive"
    UNKNOWN = "unknown"


TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}
PRO_MODEL_IDS = {
    "claude-opus-4-8",
    "gpt-5.5",
    "gpt-5.5-pro",
    # gpt-5.6 family: sol is the expensive flagship and must stay behind the allow-pro gate;
    # gpt-5.6-terra / gpt-5.6-luna are standard-tier (the token heuristic already yields STANDARD).
    "gpt-5.6-sol",
}


@dataclass(frozen=True)
class ModelPolicyDecision:
    provider: str
    model: str
    tier: ModelTier
    authorized: bool
    authorization_source: str


def env_allows_pro_model() -> bool:
    return os.getenv("MAIEUSIS_ALLOW_PRO_MODEL", "").strip().lower() in TRUTHY_ENV_VALUES


def classify_model_id(model: str, *, provider: str = "") -> ModelTier:
    normalized = model.strip().lower()
    if not normalized:
        return ModelTier.UNKNOWN
    if provider.strip().lower() == "mock":
        return ModelTier.MOCK
    if normalized in PRO_MODEL_IDS:
        return ModelTier.PRO_EXPENSIVE
    tokens = [token for token in re.split(r"[^a-z0-9]+", normalized) if token]
    if (
        "opus" in tokens
        or "pro" in tokens
        or normalized.endswith("-pro")
        or normalized.endswith("_pro")
    ):
        return ModelTier.PRO_EXPENSIVE
    return ModelTier.STANDARD


def authorize_model(
    *,
    provider: str,
    model: str,
    allow_pro_model: bool = False,
) -> ModelPolicyDecision:
    tier = classify_model_id(model, provider=provider)
    env_allowed = env_allows_pro_model()
    authorized = tier != ModelTier.PRO_EXPENSIVE or allow_pro_model or env_allowed
    if allow_pro_model:
        source = "cli_flag"
    elif env_allowed:
        source = "env:MAIEUSIS_ALLOW_PRO_MODEL"
    elif tier == ModelTier.PRO_EXPENSIVE:
        source = "blocked"
    else:
        source = "not_required"
    return ModelPolicyDecision(
        provider=provider,
        model=model,
        tier=tier,
        authorized=authorized,
        authorization_source=source,
    )


def ensure_model_allowed(
    *,
    provider: str,
    model: str,
    allow_pro_model: bool = False,
) -> ModelPolicyDecision:
    decision = authorize_model(
        provider=provider,
        model=model,
        allow_pro_model=allow_pro_model,
    )
    if not decision.authorized:
        raise ModelConfigurationError(
            "Pro/expensive model calls are disabled by default. "
            f"Model '{model}' for provider '{provider}' requires explicit approval via "
            "--allow-pro-model or MAIEUSIS_ALLOW_PRO_MODEL=1."
        )
    return decision
