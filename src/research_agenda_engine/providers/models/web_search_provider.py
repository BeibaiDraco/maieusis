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

from pydantic import BaseModel, ValidationError

from ...provenance import stable_hash
from ...schemas.coarse_dataset_facts import WebSearchCitation
from ..capture import capture_enabled, capture_paid_leaf
from .anthropic_provider import AnthropicProvider, _anthropic_failure_kind
from .base import (
    DEFAULT_EFFORT,
    DEFAULT_THINKING,
    ModelConfigurationError,
    StructuredModelFailureKind,
    StructuredModelProviderError,
    reasoning_request_kwargs,
)
from .openai_provider import OpenAIProvider

T = TypeVar("T", bound=BaseModel)

_ANTHROPIC_DIRECT_WEB_SEARCH_TOOL = "web_search_20250305"
_DEFAULT_MAX_WEB_SEARCHES = 5
#: The fallback for a direct caller that passes no ceiling. Left at the historical value on
#: purpose: on the product path every config supplies its own `max_output_tokens`, so raising this
#: would change nothing a run does while adding a THIRD number for one quantity. What actually
#: bounds the lane is the schema cap, now `ANTHROPIC_MAX_OUTPUT_TOKENS` -- this provider is
#: `AnthropicWebSearchProvider` and its reply shares one budget with the thinking block exactly as
#: the gate reviewers do, whose 8192 truncated 5 of 408.
_DEFAULT_MAX_OUTPUT_TOKENS = 8192
# ``pause_turn`` is a server-side tool lifecycle event, not a general retry signal. One
# continuation lets Claude finish a long-running search while keeping the logical N-2 request
# finite and its tool-use reservation auditable.
_MAX_ANTHROPIC_PAUSE_TURN_CONTINUATIONS = 1


@dataclass(frozen=True)
class WebSearchProviderCapabilities:
    """Declared, auditable capability facts — never a guess from a requested knob."""

    provider_name: str
    tool_name: str = ""
    tool_version: str = ""
    enforces_hard_max_uses: bool = False
    reports_complete_action_trace: bool = False
    direct_only_tool_use: bool = False
    unsupported_reason: str = ""

    @property
    def supports_strict_novelty_grounding(self) -> bool:
        return (
            self.enforces_hard_max_uses
            and self.reports_complete_action_trace
            and self.direct_only_tool_use
        )


class WebSearchCapabilityError(ModelConfigurationError):
    """Raised before egress when a configured adapter cannot honor N-2's hard contract."""


class AnthropicWebSearchPauseTurnError(RuntimeError):
    """A bounded Anthropic web-search continuation could not complete honestly."""


@dataclass(frozen=True)
class WebSearchActionTrace:
    """A vendor-reported tool action.  Empty fields mean the vendor omitted them."""

    action_type: str
    query: str = ""
    provider_action_id: str = ""
    reported_result_count: int | None = None
    reported_filters: tuple[str, ...] | None = None


@dataclass(frozen=True)
class WebSearchSourceTrace:
    """Provider source metadata plus an explicitly labeled host binding; never page bodies."""

    url: str
    title: str = ""
    provider_source_id: str = ""
    provider_action_id: str = ""
    # An opaque host-generated binding for providers (currently Anthropic's real
    # ``web_search_result`` shape) that do not emit a source ID. This is deliberately separate
    # from ``provider_source_id``: it is not vendor telemetry and never claims to be.
    host_derived_source_binding_id: str = ""


@dataclass(frozen=True)
class WebSearchUsageTrace:
    """Actual values reported by the vendor; unknown values remain ``None``."""

    provider_reported_search_requests: int | None = None
    provider_reported_input_tokens: int | None = None
    provider_reported_output_tokens: int | None = None


@dataclass
class WebSearchResearchResult(Generic[T]):
    """A structured web result plus only the trace information the vendor actually reported."""

    parsed: T
    provider_id: str
    model_id: str
    citations: list[WebSearchCitation] = field(default_factory=list)
    actions: list[WebSearchActionTrace] = field(default_factory=list)
    sources: list[WebSearchSourceTrace] = field(default_factory=list)
    usage: WebSearchUsageTrace = field(default_factory=WebSearchUsageTrace)
    tool_name: str = ""
    tool_version: str = ""
    # This is host input, not vendor telemetry.  It makes an unenforceable OpenAI request visible
    # instead of silently dropping it; strict N-2 rejects that adapter before it can be used.
    requested_max_web_searches: int = _DEFAULT_MAX_WEB_SEARCHES


class WebSearchModelProvider(ABC):
    """Vendor-neutral interface for a typed model call that may use server-side web search."""

    provider_name: str
    model_name: str

    @property
    def provider_id(self) -> str:
        return f"{self.provider_name}:{self.model_name}"

    @property
    def capabilities(self) -> WebSearchProviderCapabilities:
        return web_search_provider_capabilities(self.provider_name)

    def require_strict_novelty_web_capability(self) -> WebSearchProviderCapabilities:
        return require_strict_novelty_web_capability(self)

    @abstractmethod
    def research_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
        max_web_searches: int = _DEFAULT_MAX_WEB_SEARCHES,
        max_output_tokens: int = _DEFAULT_MAX_OUTPUT_TOKENS,
    ) -> WebSearchResearchResult[T]:
        raise NotImplementedError


class OpenAIWebSearchProvider(OpenAIProvider, WebSearchModelProvider):
    """OpenAI Responses web search for legacy Source-C use, not strict N-2 spending.

    The Responses API exposes useful action/source information, but it does not offer a documented
    server-enforced per-request maximum number of web searches.  ``capabilities`` says so plainly;
    callers must not reinterpret ``max_web_searches`` as a hard ceiling.
    """

    def research_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
        max_web_searches: int = _DEFAULT_MAX_WEB_SEARCHES,
        max_output_tokens: int = _DEFAULT_MAX_OUTPUT_TOKENS,
    ) -> WebSearchResearchResult[T]:
        _validate_request_bounds(
            max_web_searches=max_web_searches,
            max_output_tokens=max_output_tokens,
        )
        response = self._client.responses.parse(
            model=self.model_name,
            max_output_tokens=max_output_tokens,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=output_model,
            tools=[{"type": "web_search"}],
            # Ask for source inventory when the API provides it.  The result remains non-strict
            # because this API does not expose a vendor-enforced max-use control.
            include=["web_search_call.action.sources"],
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed structured output")
        return WebSearchResearchResult(
            parsed=parsed,
            provider_id=self.provider_id,
            model_id=self.model_name,
            citations=_openai_citations(response),
            actions=_openai_actions(response),
            sources=_openai_sources(response),
            usage=_openai_usage(response),
            tool_name="web_search",
            tool_version="responses_web_search",
            requested_max_web_searches=max_web_searches,
        )


class AnthropicWebSearchProvider(AnthropicProvider, WebSearchModelProvider):
    """Claude direct web-search server tool with a vendor-enforced ``max_uses`` bound."""

    def research_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
        max_web_searches: int = _DEFAULT_MAX_WEB_SEARCHES,
        max_output_tokens: int = _DEFAULT_MAX_OUTPUT_TOKENS,
    ) -> WebSearchResearchResult[T]:
        _validate_request_bounds(
            max_web_searches=max_web_searches,
            max_output_tokens=max_output_tokens,
        )
        # The SDK's message TypedDict union varies by version; retain the vendor-returned assistant
        # blocks verbatim for a pause continuation rather than coercing or serializing them.
        initial_messages: list[Any] = [{"role": "user", "content": user_prompt}]
        response = self._parse_web_search_response(
            model=self.model_name,
            max_tokens=max_output_tokens,
            system=system_prompt,
            messages=initial_messages,
            output_format=output_model,
            tools=_anthropic_web_search_tool(max_web_searches),
            **reasoning_request_kwargs(self.thinking, self.effort),
        )
        responses: list[Any] = [response]

        # Anthropic may pause a long server-side web-tool turn.  Continue exactly once with the
        # complete assistant content returned by the service (including opaque encrypted blocks),
        # held only in memory.  The next request receives *remaining* tool uses, never a reset of
        # the original ceiling.  A second pause is an honest finite failure, not an unbounded retry.
        for _continuation_index in range(_MAX_ANTHROPIC_PAUSE_TURN_CONTINUATIONS):
            if _anthropic_stop_reason(response) != "pause_turn":
                break
            _assert_anthropic_paused_response_is_auditable(response)
            _assert_anthropic_trace_within_web_cap(
                responses=responses,
                max_web_searches=max_web_searches,
            )
            remaining_uses = _remaining_anthropic_web_uses(
                responses=responses,
                max_web_searches=max_web_searches,
            )
            if remaining_uses < 1:
                # The ceiling is spent while the model is still mid-turn. Failing here discarded
                # both the searches already billed and the leads they found, which is the opposite
                # of what a bounded search should mean: spend the bound, then answer from what the
                # bound bought. Finish the turn with the tool withdrawn so the model must conclude
                # from the evidence it already gathered. It cannot search again — there is no tool.
                exhausted_content = _attr(response, "content", None)
                if not _as_mapping_sequence(exhausted_content):
                    raise AnthropicWebSearchPauseTurnError(
                        "Anthropic web search paused without assistant content to continue"
                    )
                response = self._parse_web_search_response(
                    model=self.model_name,
                    max_tokens=max_output_tokens,
                    system=system_prompt,
                    messages=[
                        *initial_messages,
                        {"role": "assistant", "content": exhausted_content},
                    ],
                    output_format=output_model,
                    # A continuation runs at the same depth as the turn it continues; inheriting a
                    # different one mid-trace would make the second half of one scout's evidence
                    # incomparable with the first.
                    **reasoning_request_kwargs(self.thinking, self.effort),
                )
                responses.append(response)
                break
            paused_content = _attr(response, "content", None)
            if not _as_mapping_sequence(paused_content):
                raise AnthropicWebSearchPauseTurnError(
                    "Anthropic web search paused without assistant content to continue"
                )
            response = self._parse_web_search_response(
                model=self.model_name,
                max_tokens=max_output_tokens,
                system=system_prompt,
                messages=[*initial_messages, {"role": "assistant", "content": paused_content}],
                output_format=output_model,
                tools=_anthropic_web_search_tool(remaining_uses),
                **reasoning_request_kwargs(self.thinking, self.effort),
            )
            responses.append(response)

        _assert_anthropic_trace_within_web_cap(
            responses=responses,
            max_web_searches=max_web_searches,
        )
        if _anthropic_stop_reason(response) == "pause_turn":
            raise AnthropicWebSearchPauseTurnError(
                "Anthropic web search remained paused after the bounded continuation"
            )
        parsed = response.parsed_output
        if parsed is None:
            raise RuntimeError("Anthropic returned no parsed structured output")
        if capture_enabled():
            # This seam had no capture at all, which is why a scout call rejected downstream left
            # nothing to inspect. The per-response breakdown is the diagnostic that matters: it
            # shows directly whether the vendor reports searches per response or cumulatively,
            # which decides whether summing across a pause continuation is even correct.
            capture_paid_leaf(
                "models.anthropic.web_search",
                request={
                    "model": self.model_name,
                    "max_web_searches": max_web_searches,
                    "max_output_tokens": max_output_tokens,
                    "output_model": output_model.__name__,
                },
                response={
                    "response_count": len(responses),
                    "per_response": [
                        {
                            "ordinal": ordinal,
                            "stop_reason": _anthropic_stop_reason(item),
                            "reported_web_search_requests": (
                                _anthropic_usage(item).provider_reported_search_requests
                            ),
                            "action_count": len(_anthropic_actions(item)),
                            "source_count": len(_anthropic_sources(item)),
                        }
                        for ordinal, item in enumerate(responses, start=1)
                    ],
                    "aggregated_reported_web_search_requests": (
                        _anthropic_usage_for_responses(responses).provider_reported_search_requests
                    ),
                    "aggregated_action_count": len(_anthropic_actions_for_responses(responses)),
                    "aggregated_source_count": len(_anthropic_sources_for_responses(responses)),
                },
                model=self.model_name,
            )
        return WebSearchResearchResult(
            parsed=parsed,
            provider_id=self.provider_id,
            model_id=self.model_name,
            citations=_anthropic_citations_for_responses(responses),
            actions=_anthropic_actions_for_responses(responses),
            sources=_anthropic_sources_for_responses(responses),
            usage=_anthropic_usage_for_responses(responses),
            tool_name="web_search",
            tool_version=_ANTHROPIC_DIRECT_WEB_SEARCH_TOOL,
            requested_max_web_searches=max_web_searches,
        )

    def _parse_web_search_response(self, **kwargs: Any) -> Any:
        """Normalize known Anthropic SDK failures without retaining vendor error text.

        N-2 writes its immutable pre-call reservation before this request, so a connection,
        timeout, authentication, or response-validation fault must become the ordinary typed
        provider failure that the grounder already degrades to its no-retry terminal.  Unknown
        programming errors intentionally escape for diagnosis rather than being misclassified as
        an uncertain provider outcome.
        """

        try:
            return self._client.messages.parse(**kwargs)
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


class MockWebSearchModelProvider(WebSearchModelProvider):
    """Deterministic web-search provider for tests: supplied trace fixtures, no API."""

    provider_name = "mock"
    model_name = "web-search-fixture"

    def __init__(
        self,
        *,
        factory: Any,
        citations: Sequence[WebSearchCitation] | None = None,
        actions: Sequence[WebSearchActionTrace] | None = None,
        sources: Sequence[WebSearchSourceTrace] | None = None,
        usage: WebSearchUsageTrace | None = None,
        tool_name: str = "mock_web_search",
        tool_version: str = "fixture",
    ) -> None:
        self.factory = factory
        self._citations = list(citations or [])
        self._actions = list(actions or [])
        self._sources = list(sources or [])
        self._usage = usage or WebSearchUsageTrace()
        self._tool_name = tool_name
        self._tool_version = tool_version

    def research_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
        max_web_searches: int = _DEFAULT_MAX_WEB_SEARCHES,
        max_output_tokens: int = _DEFAULT_MAX_OUTPUT_TOKENS,
    ) -> WebSearchResearchResult[T]:
        _validate_request_bounds(
            max_web_searches=max_web_searches,
            max_output_tokens=max_output_tokens,
        )
        value = self.factory(output_model, system_prompt, user_prompt)
        parsed = output_model.model_validate(value)
        return WebSearchResearchResult(
            parsed=parsed,
            provider_id=self.provider_id,
            model_id=self.model_name,
            citations=list(self._citations),
            actions=list(self._actions),
            sources=list(self._sources),
            usage=self._usage,
            tool_name=self._tool_name,
            tool_version=self._tool_version,
            requested_max_web_searches=max_web_searches,
        )


def web_search_provider_capabilities(provider_name: str) -> WebSearchProviderCapabilities:
    """Return the known contract for an adapter without constructing it or making egress."""

    normalized = provider_name.strip().lower()
    if normalized == "anthropic":
        return WebSearchProviderCapabilities(
            provider_name="anthropic",
            tool_name="web_search",
            tool_version=_ANTHROPIC_DIRECT_WEB_SEARCH_TOOL,
            enforces_hard_max_uses=True,
            reports_complete_action_trace=True,
            direct_only_tool_use=True,
        )
    if normalized == "openai":
        return WebSearchProviderCapabilities(
            provider_name="openai",
            tool_name="web_search",
            tool_version="responses_web_search",
            unsupported_reason=(
                "OpenAI web search does not expose a documented vendor-enforced per-request "
                "maximum use bound for strict N-2 web-tool reservations"
            ),
        )
    if normalized == "mock":
        return WebSearchProviderCapabilities(
            provider_name="mock",
            unsupported_reason="mock web search is a test seam, not an operational N-2 provider",
        )
    return WebSearchProviderCapabilities(
        provider_name=normalized or "<empty>",
        unsupported_reason=f"unknown web-search provider: {provider_name}",
    )


def require_strict_novelty_web_capability(
    provider: str | WebSearchModelProvider,
) -> WebSearchProviderCapabilities:
    """Fail closed unless the adapter can enforce and audit N-2's request ceiling."""

    capabilities = (
        web_search_provider_capabilities(provider)
        if isinstance(provider, str)
        else provider.capabilities
    )
    if not capabilities.supports_strict_novelty_grounding:
        reason = capabilities.unsupported_reason or "missing strict N-2 web-search capability"
        raise WebSearchCapabilityError(
            f"web provider {capabilities.provider_name!r} cannot run strict novelty grounding: {reason}"
        )
    return capabilities


def build_novelty_web_search_provider(
    provider: str,
    *,
    model: str = "",
    allow_pro_model: bool = False,
    thinking: str = DEFAULT_THINKING,
    effort: str = DEFAULT_EFFORT,
) -> WebSearchModelProvider:
    """Build the uncached, novelty-specific web seam after capability validation.

    This deliberately does not reuse the Source-C dataset-narrative wiring or the regular cached
    model factory.  A strict N-2 scout must expose the tool-use bound and complete receipt trace
    before its client is constructed.
    """

    normalized = provider.strip().lower()
    require_strict_novelty_web_capability(normalized)
    if normalized == "anthropic":
        return AnthropicWebSearchProvider(
            model=model or None,
            allow_pro_model=allow_pro_model,
            thinking=thinking,
            effort=effort,
        )
    # The capability guard above makes every other current branch unreachable.  Keeping a finite
    # error rather than a fallback prevents a future adapter from quietly becoming operational.
    raise WebSearchCapabilityError(
        f"web provider {provider!r} has no strict novelty factory implementation"
    )


def _validate_request_bounds(*, max_web_searches: int, max_output_tokens: int) -> None:
    if isinstance(max_web_searches, bool) or max_web_searches < 1:
        raise ValueError("max_web_searches must be a positive integer")
    if isinstance(max_output_tokens, bool) or max_output_tokens < 1:
        raise ValueError("max_output_tokens must be a positive integer")


def _anthropic_web_search_tool(max_uses: int) -> list[Any]:
    """Build the documented direct-only server-tool shape for one bounded API request."""

    # Typed loosely: the vendor SDK's server-tool TypedDict union varies by version, so we build
    # the documented direct-only web-search shape as a plain dict and let the SDK validate it at
    # runtime. The 2025-03 direct tool deliberately avoids later dynamic tool/code callers.
    return [
        {
            "type": _ANTHROPIC_DIRECT_WEB_SEARCH_TOOL,
            "name": "web_search",
            "max_uses": max_uses,
        }
    ]


def _anthropic_stop_reason(response: Any) -> str:
    return _as_text(_attr(response, "stop_reason", ""))


def _anthropic_actions_for_responses(responses: Sequence[Any]) -> list[WebSearchActionTrace]:
    return [action for response in responses for action in _anthropic_actions(response)]


def _anthropic_sources_for_responses(responses: Sequence[Any]) -> list[WebSearchSourceTrace]:
    return [
        source
        for response_ordinal, response in enumerate(responses, start=1)
        for source in _anthropic_sources(response, response_ordinal=response_ordinal)
    ]


def _anthropic_citations_for_responses(responses: Sequence[Any]) -> list[WebSearchCitation]:
    return _dedupe_citations(
        [citation for response in responses for citation in _anthropic_citations(response)]
    )


def _anthropic_usage_for_responses(responses: Sequence[Any]) -> WebSearchUsageTrace:
    usages = [_anthropic_usage(response) for response in responses]
    return WebSearchUsageTrace(
        provider_reported_search_requests=_sum_reported_usage(
            [usage.provider_reported_search_requests for usage in usages]
        ),
        provider_reported_input_tokens=_sum_reported_usage(
            [usage.provider_reported_input_tokens for usage in usages]
        ),
        provider_reported_output_tokens=_sum_reported_usage(
            [usage.provider_reported_output_tokens for usage in usages]
        ),
    )


def _sum_reported_usage(values: Sequence[int | None]) -> int | None:
    reported_values = [value for value in values if value is not None]
    return sum(reported_values) if reported_values else None


def _assert_anthropic_trace_within_web_cap(
    *, responses: Sequence[Any], max_web_searches: int
) -> None:
    action_count = len(_anthropic_actions_for_responses(responses))
    reported_search_requests = _anthropic_usage_for_responses(
        responses
    ).provider_reported_search_requests
    if action_count > max_web_searches:
        raise AnthropicWebSearchPauseTurnError(
            "Anthropic reported more web-search actions than the configured web-search ceiling"
        )
    if reported_search_requests is not None and reported_search_requests > max_web_searches:
        raise AnthropicWebSearchPauseTurnError(
            "Anthropic reported more web-search requests than the configured web-search ceiling"
        )


def _assert_anthropic_paused_response_is_auditable(response: Any) -> None:
    """Refuse to continue when the paused turn cannot prove its web-tool use count.

    A missing action trace is not equivalent to zero searches.  Continuing with the full allowance
    in that case could let an unobserved first request consume web-tool uses beyond the durable
    N-2 reservation.  An explicit vendor-reported zero remains a valid, auditable observation.
    """

    if (
        not _anthropic_actions(response)
        and _anthropic_usage(response).provider_reported_search_requests is None
    ):
        raise AnthropicWebSearchPauseTurnError(
            "Anthropic web search paused without an auditable action or vendor usage trace"
        )


def _remaining_anthropic_web_uses(*, responses: Sequence[Any], max_web_searches: int) -> int:
    action_count = len(_anthropic_actions_for_responses(responses))
    reported_search_requests = _anthropic_usage_for_responses(
        responses
    ).provider_reported_search_requests
    observed_uses = max(action_count, reported_search_requests or 0)
    return max_web_searches - observed_uses


def _as_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _as_nonnegative_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _as_mapping_sequence(value: object) -> list[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return []


def _as_filter_trace(value: object) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return (value,)
    values = _as_mapping_sequence(value)
    return tuple(item for item in values if isinstance(item, str))


def _openai_actions(response: Any) -> list[WebSearchActionTrace]:
    actions: list[WebSearchActionTrace] = []
    for item in _as_mapping_sequence(_attr(response, "output", [])):
        if _as_text(_attr(item, "type")) != "web_search_call":
            continue
        action = _attr(item, "action", {})
        action_type = _as_text(_attr(action, "type")) or "web_search_call"
        actions.append(
            WebSearchActionTrace(
                action_type=action_type,
                query=_as_text(_attr(action, "query")),
                provider_action_id=_as_text(_attr(item, "id")),
                reported_result_count=_as_nonnegative_int(_attr(action, "result_count", None)),
                reported_filters=_as_filter_trace(_attr(action, "filters", None)),
            )
        )
    return actions


def _openai_sources(response: Any) -> list[WebSearchSourceTrace]:
    sources: list[WebSearchSourceTrace] = []
    for item in _as_mapping_sequence(_attr(response, "output", [])):
        if _as_text(_attr(item, "type")) != "web_search_call":
            continue
        action = _attr(item, "action", {})
        action_id = _as_text(_attr(item, "id"))
        for source in _as_mapping_sequence(_attr(action, "sources", [])):
            url = _as_text(_attr(source, "url"))
            if not url:
                continue
            sources.append(
                WebSearchSourceTrace(
                    url=url,
                    title=_as_text(_attr(source, "title")),
                    provider_source_id=(
                        _as_text(_attr(source, "id")) or _as_text(_attr(source, "source_id"))
                    ),
                    provider_action_id=action_id,
                )
            )
    return sources


def _openai_usage(response: Any) -> WebSearchUsageTrace:
    usage = _attr(response, "usage", {})
    return WebSearchUsageTrace(
        provider_reported_input_tokens=_as_nonnegative_int(_attr(usage, "input_tokens", None)),
        provider_reported_output_tokens=_as_nonnegative_int(_attr(usage, "output_tokens", None)),
    )


def _anthropic_actions(response: Any) -> list[WebSearchActionTrace]:
    actions: list[WebSearchActionTrace] = []
    for block in _as_mapping_sequence(_attr(response, "content", [])):
        if _as_text(_attr(block, "type")) != "server_tool_use":
            continue
        if _as_text(_attr(block, "name")) != "web_search":
            continue
        tool_input = _attr(block, "input", {})
        actions.append(
            WebSearchActionTrace(
                action_type=_as_text(_attr(block, "name")),
                query=_as_text(_attr(tool_input, "query")),
                provider_action_id=_as_text(_attr(block, "id")),
                reported_filters=_as_filter_trace(_attr(tool_input, "filters", None)),
            )
        )
    return actions


def _anthropic_sources(response: Any, *, response_ordinal: int = 1) -> list[WebSearchSourceTrace]:
    sources: list[WebSearchSourceTrace] = []
    result_ordinal_by_action_id: dict[str, int] = {}
    for block in _as_mapping_sequence(_attr(response, "content", [])):
        if _as_text(_attr(block, "type")) != "web_search_tool_result":
            continue
        action_id = _as_text(_attr(block, "tool_use_id"))
        for result in _as_mapping_sequence(_attr(block, "content", [])):
            result_type = _as_text(_attr(result, "type"))
            if result_type and result_type != "web_search_result":
                continue
            url = _as_text(_attr(result, "url"))
            if not url:
                continue
            title = _as_text(_attr(result, "title"))
            provider_source_id = _as_text(_attr(result, "id")) or _as_text(
                _attr(result, "source_id")
            )
            result_ordinal = result_ordinal_by_action_id.get(action_id, 0) + 1
            result_ordinal_by_action_id[action_id] = result_ordinal
            sources.append(
                WebSearchSourceTrace(
                    url=url,
                    title=title,
                    provider_source_id=provider_source_id,
                    provider_action_id=action_id,
                    host_derived_source_binding_id=(
                        ""
                        if provider_source_id
                        else _anthropic_host_derived_source_binding_id(
                            response_ordinal=response_ordinal,
                            provider_action_id=action_id,
                            result_ordinal=result_ordinal,
                        )
                    ),
                )
            )
    return sources


def _anthropic_host_derived_source_binding_id(
    *, response_ordinal: int, provider_action_id: str, result_ordinal: int
) -> str:
    """Return an opaque host binding without hashing raw web metadata.

    Anthropic's documented ``web_search_result`` block has a URL/title but no vendor source ID.
    The result's position within the vendor action trace is enough to bind it deterministically;
    keeping raw URLs and titles out of this identity avoids turning unsafe locator material into a
    persisted host identifier.
    """

    return "host-src-" + stable_hash(
        {
            "schema": "anthropic_web_search_source_binding/v1",
            "tool_name": "web_search",
            "tool_version": _ANTHROPIC_DIRECT_WEB_SEARCH_TOOL,
            "response_ordinal": response_ordinal,
            "provider_action_id": provider_action_id,
            "result_ordinal": result_ordinal,
        }
    )


def _anthropic_usage(response: Any) -> WebSearchUsageTrace:
    usage = _attr(response, "usage", {})
    server_tool_use = _attr(usage, "server_tool_use", {})
    return WebSearchUsageTrace(
        provider_reported_search_requests=_as_nonnegative_int(
            _attr(server_tool_use, "web_search_requests", None)
        ),
        provider_reported_input_tokens=_as_nonnegative_int(_attr(usage, "input_tokens", None)),
        provider_reported_output_tokens=_as_nonnegative_int(_attr(usage, "output_tokens", None)),
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
