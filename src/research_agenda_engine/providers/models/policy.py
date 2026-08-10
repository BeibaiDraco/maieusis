from __future__ import annotations

import os
import re
from collections.abc import Mapping
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


# Declared model supersession, operator-directed 2026-07-25: the API reviewer/judge/scout role
# moves from ``claude-opus-4-8`` to ``claude-sonnet-5``, and artifacts the retired model already
# produced stay reusable under the successor. The relation is DIRECTIONAL — an artifact made by the
# retired model is acceptable where its successor is configured, never the reverse — and it never
# rewrites provenance: a receipt keeps naming the model that actually produced it, so a reader can
# always see that a reused artifact predates the switch.
SUPERSEDED_BY: dict[str, str] = {
    "claude-opus-4-8": "claude-sonnet-5",
}


def model_identity_accepts(*, recorded: str, expected: str) -> bool:
    """True when an artifact recorded as ``recorded`` may be reused under ``expected``.

    ``recorded`` and ``expected`` are ``provider:model`` identities as written into receipts.
    """

    if recorded == expected:
        return True
    recorded_provider, _, recorded_model = recorded.partition(":")
    expected_provider, _, expected_model = expected.partition(":")
    if recorded_provider != expected_provider:
        return False
    return SUPERSEDED_BY.get(recorded_model) == expected_model


def model_versions_accept(recorded: Mapping[str, str], expected: Mapping[str, str]) -> bool:
    """Role-by-role reuse check that honors declared supersession.

    Equality is still required for every role; supersession only widens what counts as equal for
    a role whose retired model has a declared successor. A missing or extra role is a mismatch,
    exactly as a dict comparison would treat it.
    """

    if set(recorded) != set(expected):
        return False
    return all(
        model_identity_accepts(recorded=recorded[role], expected=expected[role])
        for role in expected
    )


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
