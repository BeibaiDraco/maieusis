"""Shared base for independent-AI reviewers.

Factors the env→provider resolution + the two independence primitives that were copy-pasted across
``dataset_narrative_reviewer.py`` and ``plan_reviewer.py`` into one reusable surface over
``providers/scientific_agents/base.py``. The front-half quality gates
(formation-trace / pattern / topic-evidence / consolidation / shortlist) extend this base rather
than re-copying the resolver.

Two distinct independence checks live here because the two reviewers protect independence
differently: the narrative fidelity reviewer must use a *provider* distinct from every source
generator (``assert_reviewer_provider_independent``), while the plan reviewer must use a *session*
distinct from the owner's review session (``assert_reviewer_session_independent``). Both are exposed;
each reviewer uses the one that matches its trust boundary.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

from ...config import load_runtime_env
from ...providers.models.base import DEFAULT_EFFORT, DEFAULT_THINKING
from ...providers.scientific_agents import (
    AnthropicScientificAgentProvider,
    OpenAIScientificAgentProvider,
    ScientificAgentProvider,
)

MAIEUSIS_R5_REVIEWER_PROVIDER_ENV = "MAIEUSIS_R5_REVIEWER_PROVIDER"


def build_scientific_reviewer_provider_from_env(
    *,
    system_prompt_loader: Callable[[], str],
    credential_fallback: Sequence[str],
    unsupported_provider_label: str,
    provider: Literal["openai", "anthropic"] | None = None,
    allow_pro_model: bool = False,
    project_root: str | Path | None = None,
    thinking: str = DEFAULT_THINKING,
    effort: str = DEFAULT_EFFORT,
) -> ScientificAgentProvider:
    """Resolve a live independent reviewer provider from runtime env files.

    ``provider`` (explicit) wins; else ``MAIEUSIS_R5_REVIEWER_PROVIDER``; else the first entry in
    ``credential_fallback`` whose ``<NAME>_API_KEY`` + ``<NAME>_MODEL`` are both set. The system
    prompt is loaded only *after* the provider resolves (a missing prompt never masks a missing
    credential), so each reviewer's prior behavior is preserved byte-for-byte.
    """
    load_runtime_env(project_root=Path(project_root) if project_root is not None else Path.cwd())
    env_provider = os.getenv(MAIEUSIS_R5_REVIEWER_PROVIDER_ENV)
    provider_name = (provider if provider is not None else env_provider or "").strip().lower()
    if not provider_name:
        for name in credential_fallback:
            if os.getenv(f"{name.upper()}_API_KEY") and os.getenv(f"{name.upper()}_MODEL"):
                provider_name = name
                break
        else:
            pairs = " or ".join(
                f"{name.upper()}_API_KEY/{name.upper()}_MODEL" for name in credential_fallback
            )
            raise ValueError(
                f"Set {MAIEUSIS_R5_REVIEWER_PROVIDER_ENV} plus provider credentials/model, or set "
                f"{pairs}."
            )
    system_prompt = system_prompt_loader()
    if provider_name == "openai":
        return OpenAIScientificAgentProvider(
            allow_pro_model=allow_pro_model,
            system_prompt=system_prompt,
            thinking=thinking,
            effort=effort,
        )
    if provider_name == "anthropic":
        return AnthropicScientificAgentProvider(
            allow_pro_model=allow_pro_model,
            system_prompt=system_prompt,
            thinking=thinking,
            effort=effort,
        )
    raise ValueError(f"Unsupported {unsupported_provider_label} provider: {provider_name}")


# Wrapper prefixes an inner provider id can accrete (e.g. the cache wrapper names itself
# ``cached-<inner>``). Unwrapped recursively so ``cached-openai:gpt-5.5`` resolves to the ``openai``
# family — a cached reviewer is NOT independent of an ``openai`` generator.
_PROVIDER_WRAPPER_PREFIXES: tuple[str, ...] = ("cached-",)
# Provider names that denote the same underlying family.
_PROVIDER_FAMILY_ALIASES: dict[str, str] = {"deterministic-fixture": "mock"}


def provider_family(provider_id: str) -> str:
    """Normalize a provider id/name to its FAMILY (``openai`` / ``anthropic`` / ``mock`` / …).

    Drops the ``model`` half of a ``provider:model`` id, recursively strips wrapper prefixes, and maps
    known aliases. Comparing families (not full id strings) is what makes ``openai:gpt-5.4`` and
    ``cached-openai:gpt-5.5`` correctly NON-independent. An unknown provider maps to its own unwrapped
    name, so two distinct unknowns still compare as independent.
    """
    name = provider_id.split(":", 1)[0].strip().lower()
    changed = True
    while changed:
        changed = False
        for prefix in _PROVIDER_WRAPPER_PREFIXES:
            if name.startswith(prefix):
                name = name[len(prefix) :]
                changed = True
    return _PROVIDER_FAMILY_ALIASES.get(name, name)


def assert_reviewer_provider_independent(
    reviewer_provider_id: str,
    generator_provider_ids: Sequence[str],
    *,
    role_label: str = "reviewer",
) -> None:
    """Fail if the reviewer's provider FAMILY also generated one of the inputs it is judging.

    Family-normalized + wrapper-unwrapped so a cache/wrapper alias cannot smuggle a same-family reviewer
    past the independence rule.
    """
    reviewer = provider_family(reviewer_provider_id)
    generators = {provider_family(pid) for pid in generator_provider_ids if pid}
    if reviewer in generators:
        raise ValueError(
            f"{role_label} must be independent of the generators "
            f"(reviewer provider {reviewer_provider_id!r} resolves to family {reviewer!r}, "
            "which also generated a source)"
        )


def assert_reviewer_session_independent(
    reviewer_session_id: str,
    other_session_id: str,
    *,
    role_label: str = "independent reviewer",
    other_label: str = "owner review",
) -> None:
    """Fail if the reviewer session is the same session as the one it must be independent of."""
    if reviewer_session_id == other_session_id:
        raise ValueError(f"{role_label} session must differ from {other_label} session")
