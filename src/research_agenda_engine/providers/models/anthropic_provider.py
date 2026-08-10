from __future__ import annotations

import os
from typing import Any, TypeVar, cast

from pydantic import BaseModel, ValidationError

from ..capture import (
    CaptureReceipt,
    capture_enabled,
    capture_paid_leaf,
    capture_parse_failure,
    raw_response_body,
)
from .base import (
    ANTHROPIC_MAX_OUTPUT_TOKENS,
    DEFAULT_EFFORT,
    DEFAULT_THINKING,
    ModelConfigurationError,
    StructuredModelFailureKind,
    StructuredModelProvider,
    StructuredModelProviderError,
    partial_json_text,
    reasoning_request_kwargs,
)
from .policy import ModelPolicyDecision, ensure_model_allowed

T = TypeVar("T", bound=BaseModel)

#: Re-exported under the historical private name so this module's call sites read unchanged.
#: The value, its measurement and the transport limit that bounds it live in `models/base.py`,
#: because the gate-reviewer adapter in another package must not drift from it.
_MAX_OUTPUT_TOKENS = ANTHROPIC_MAX_OUTPUT_TOKENS


def _response_envelope(body: object) -> dict[str, object]:
    """What a postmortem needs, read from the RAW body so it survives every parse outcome.

    #138 built this from the SDK's parsed message, which meant it could only be written once the
    parse had already succeeded -- the one situation where nobody needs it. Reading the wire body
    instead is what lets the same record exist on the validation branch.
    """
    fields = body if isinstance(body, dict) else {}
    content = fields.get("content")
    return {
        "stop_reason": fields.get("stop_reason"),
        "stop_sequence": fields.get("stop_sequence"),
        "content_block_types": [
            block.get("type") if isinstance(block, dict) else None
            for block in (content if isinstance(content, list) else [])
        ],
        "usage": fields.get("usage"),
        "max_tokens": _MAX_OUTPUT_TOKENS,
        # The model's actual output. Every other key here is a summary OF this one, and summaries
        # are what left the six failed novelty reviews of the 2026-07-31 leg undiagnosable.
        "body": fields,
    }


class AnthropicProvider(StructuredModelProvider):
    """Claude Messages API adapter using SDK-native Pydantic parsing."""

    provider_name = "anthropic"
    # Class-level so an adapter built with ``__new__`` (the shape several adapter tests use
    # to exercise error mapping without a client) still has a stated reasoning depth rather
    # than an AttributeError.
    thinking: str = DEFAULT_THINKING
    effort: str = DEFAULT_EFFORT

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        *,
        allow_pro_model: bool = False,
        thinking: str = DEFAULT_THINKING,
        effort: str = DEFAULT_EFFORT,
    ):
        self.thinking = thinking
        self.effort = effort
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
        # Reasoning depth is stated, not inherited. Sending no `thinking` field lets the vendor pick,
        # and on the 2026-07-31 leg it picked adaptive thinking for every role -- including the
        # novelty reviewer, whose refusals were generated inside that thinking (the refused replies
        # carry a thinking block and no text block; every reply that parsed carries a text block).
        # `effort` rides alongside because it is the knob that bounds the same reasoning.
        request_kwargs: dict[str, object] = {
            "model": self.model_name,
            "max_tokens": _MAX_OUTPUT_TOKENS,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "output_format": output_model,
            **reasoning_request_kwargs(self.thinking, self.effort),
        }
        # Capture the wire body BEFORE the SDK post-parser runs, so no parse outcome can lose it.
        # #138 moved the hook above the `parsed is None` raise and stopped there, but the SDK's own
        # ValidationError is raised from inside `messages.parse` -- above that hook -- so the
        # `structured_output_invalid` branch still wrote nothing. Reproducing the 2026-07-31 leg's
        # failing novelty reviews with MAIEUSIS_CAPTURE_DIR set created no capture directory at all.
        # The two `scientific_agents` adapters have always done it this way; these two never did.
        capturing = capture_enabled()
        receipt: CaptureReceipt | None = None
        # `Any` because the raw header makes `messages.parse` return the SDK's raw-response wrapper
        # rather than the `ParsedMessage` its signature promises; both branches then expose
        # `.parsed_output`, which is all this method reads.
        response: Any
        try:
            if capturing:
                # `messages.parse` has no generated `with_raw_response.parse` facade in the pinned
                # SDK; this is the header that facade sets, and `raw_response.parse()` then runs the
                # original post-parser unchanged.
                raw_response: Any = self._client.messages.parse(
                    **request_kwargs,  # type: ignore[arg-type]
                    extra_headers={"X-Stainless-Raw-Response": "true"},
                )
                receipt = capture_paid_leaf(
                    "models.anthropic.generate_structured",
                    request={
                        "model": self.model_name,
                        "system_prompt": system_prompt,
                        "user_prompt": user_prompt,
                        "output_model": output_model.__name__,
                        "max_tokens": _MAX_OUTPUT_TOKENS,
                        "thinking": self.thinking,
                        "effort": self.effort,
                    },
                    response=_response_envelope(raw_response_body(raw_response)),
                    model=self.model_name,
                )
                response = raw_response.parse()
            else:
                # Capture disabled: the original path, byte for byte, so CI never captures and a
                # normal run is unchanged.
                response = self._client.messages.parse(**request_kwargs)  # type: ignore[arg-type]
        except (TypeError, AssertionError):
            raise
        except ValidationError as exc:
            capture_parse_failure(receipt, exc)
            # `detail` is the one diagnostic field this error type exists to carry, and the sibling
            # OpenAI adapter already fills it. Truncation landing inside the JSON text (rather than
            # inside the thinking block) surfaces here rather than as a None parse, and there is no
            # response object in scope to read `stop_reason` from -- the field locations are the only
            # signal a caller gets, so discarding them left the two shapes indistinguishable.
            raise StructuredModelProviderError(
                StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=self.provider_id,
                detail="; ".join(
                    sorted(
                        {
                            f"{'.'.join(str(part) for part in item['loc'])}:{item['type']}"
                            for item in exc.errors()
                        }
                    )
                )[:400],
                partial_output_text=partial_json_text(exc),
            ) from exc
        except Exception as exc:
            capture_parse_failure(receipt, exc)
            kind = _anthropic_failure_kind(exc)
            if kind is None:
                raise
            raise StructuredModelProviderError(kind, provider_id=self.provider_id) from exc
        parsed = response.parsed_output
        if parsed is None:
            # `stop_reason` is already on the ParsedMessage; no raw-header work is needed to tell a
            # truncated reply from an empty one. Truncation inside the thinking block leaves a
            # message with no text block at all, which is why this arrives as a None parse rather
            # than as a validation error.
            if getattr(response, "stop_reason", None) == "max_tokens":
                raise StructuredModelProviderError(
                    StructuredModelFailureKind.OUTPUT_TRUNCATED,
                    provider_id=self.provider_id,
                    detail=f"reply cut at max_tokens={_MAX_OUTPUT_TOKENS}",
                )
            raise StructuredModelProviderError(
                StructuredModelFailureKind.INVALID_RESPONSE,
                provider_id=self.provider_id,
                detail=f"stop_reason={getattr(response, 'stop_reason', None)!r}, no parsable output",
            )
        return cast(T, parsed)


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
