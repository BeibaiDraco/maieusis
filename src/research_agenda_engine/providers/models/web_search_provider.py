"""Web-search-capable structured model providers.

The base ``StructuredModelProvider`` makes a one-shot typed call with no tools. Source C needs the
model to WEB-SEARCH and return structured output in one call, so this adds a ``WebSearchModelProvider``
interface + vendor variants that subclass the existing providers (reusing their key + model-policy
handling — so no API key ever enters a prompt/log/persisted artifact) and turn on the vendor's
server-side web-search tool. The dataset name/link arrive only in the ``user_prompt``; nothing here
is bound to a dataset. The base ``StructuredModelProvider`` and the existing providers are untouched.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from ...schemas.coarse_dataset_facts import WebSearchCitation
from .anthropic_provider import AnthropicProvider
from .openai_provider import OpenAIProvider

T = TypeVar("T", bound=BaseModel)

_ANTHROPIC_WEB_SEARCH_TOOL = "web_search_20260209"
_DEFAULT_MAX_WEB_SEARCHES = 5


@dataclass
class WebSearchResearchResult(Generic[T]):
    """A structured model output produced with web search, plus the sources the model cited."""

    parsed: T
    provider_id: str
    model_id: str
    citations: list[WebSearchCitation] = field(default_factory=list)


class WebSearchModelProvider(ABC):
    """Vendor-neutral interface for a typed model call that may use server-side web search."""

    provider_name: str
    model_name: str

    @property
    def provider_id(self) -> str:
        return f"{self.provider_name}:{self.model_name}"

    @abstractmethod
    def research_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
        max_web_searches: int = _DEFAULT_MAX_WEB_SEARCHES,
    ) -> WebSearchResearchResult[T]:
        raise NotImplementedError


class OpenAIWebSearchProvider(OpenAIProvider, WebSearchModelProvider):
    """OpenAI Responses API with the ``web_search`` tool + SDK-native structured parsing."""

    def research_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
        max_web_searches: int = _DEFAULT_MAX_WEB_SEARCHES,
    ) -> WebSearchResearchResult[T]:
        del max_web_searches  # OpenAI bounds tool use internally; kept for interface symmetry
        response = self._client.responses.parse(
            model=self.model_name,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=output_model,
            tools=[{"type": "web_search"}],
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed structured output")
        return WebSearchResearchResult(
            parsed=parsed,
            provider_id=self.provider_id,
            model_id=self.model_name,
            citations=_openai_citations(response),
        )


class AnthropicWebSearchProvider(AnthropicProvider, WebSearchModelProvider):
    """Claude Messages API with the ``web_search`` server tool + SDK-native structured parsing."""

    def research_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
        max_web_searches: int = _DEFAULT_MAX_WEB_SEARCHES,
    ) -> WebSearchResearchResult[T]:
        # Typed loosely: the vendor SDK's server-tool TypedDict union varies by version, so we build
        # the documented web-search tool shape as a plain dict and let the SDK validate it at runtime.
        web_search_tool: list[Any] = [
            {"type": _ANTHROPIC_WEB_SEARCH_TOOL, "name": "web_search", "max_uses": max_web_searches}
        ]
        response = self._client.messages.parse(
            model=self.model_name,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            output_format=output_model,
            tools=web_search_tool,
        )
        parsed = response.parsed_output
        if parsed is None:
            raise RuntimeError("Anthropic returned no parsed structured output")
        return WebSearchResearchResult(
            parsed=parsed,
            provider_id=self.provider_id,
            model_id=self.model_name,
            citations=_anthropic_citations(response),
        )


class MockWebSearchModelProvider(WebSearchModelProvider):
    """Deterministic web-search provider for tests: canned parsed output + citations, no API."""

    provider_name = "mock"
    model_name = "web-search-fixture"

    def __init__(
        self,
        *,
        factory: Any,
        citations: Sequence[WebSearchCitation] | None = None,
    ) -> None:
        self.factory = factory
        self._citations = list(citations or [])

    def research_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
        max_web_searches: int = _DEFAULT_MAX_WEB_SEARCHES,
    ) -> WebSearchResearchResult[T]:
        del max_web_searches
        value = self.factory(output_model, system_prompt, user_prompt)
        parsed = output_model.model_validate(value)
        return WebSearchResearchResult(
            parsed=parsed,
            provider_id=self.provider_id,
            model_id=self.model_name,
            citations=list(self._citations),
        )


def _openai_citations(response: Any) -> list[WebSearchCitation]:
    """Extract url citations from an OpenAI Responses object (defensive; best-effort provenance)."""
    citations: list[WebSearchCitation] = []
    for item in getattr(response, "output", []) or []:
        for block in getattr(item, "content", []) or []:
            for annotation in getattr(block, "annotations", []) or []:
                url = _attr(annotation, "url")
                if url:
                    citations.append(WebSearchCitation(url=url, title=_attr(annotation, "title")))
    return _dedupe_citations(citations)


def _anthropic_citations(response: Any) -> list[WebSearchCitation]:
    """Extract url citations from a Claude response's web_search_tool_result blocks (defensive)."""
    citations: list[WebSearchCitation] = []
    for block in getattr(response, "content", []) or []:
        if _attr(block, "type") != "web_search_tool_result":
            continue
        for result in _attr(block, "content", []) or []:
            url = _attr(result, "url")
            if url:
                citations.append(WebSearchCitation(url=url, title=_attr(result, "title")))
    return _dedupe_citations(citations)


def _attr(obj: Any, name: str, default: Any = "") -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _dedupe_citations(citations: list[WebSearchCitation]) -> list[WebSearchCitation]:
    seen: set[str] = set()
    out: list[WebSearchCitation] = []
    for citation in citations:
        if citation.url and citation.url not in seen:
            seen.add(citation.url)
            out.append(citation)
    return out
