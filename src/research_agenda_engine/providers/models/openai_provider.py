from __future__ import annotations

import os
from typing import TypeVar, cast

from pydantic import BaseModel, ValidationError

from ..capture import (
    CaptureReceipt,
    capture_enabled,
    capture_paid_leaf,
    capture_parse_failure,
    raw_response_body,
)
from .base import (
    DEFAULT_EFFORT,
    DEFAULT_THINKING,
    ModelConfigurationError,
    StructuredModelFailureKind,
    StructuredModelProvider,
    StructuredModelProviderError,
    is_account_exhaustion_error,
    partial_json_text,
)
from .policy import ModelPolicyDecision, ensure_model_allowed

T = TypeVar("T", bound=BaseModel)


def _response_envelope(body: object) -> dict[str, object]:
    """A Responses-API postmortem's fields, read from the RAW body so every parse outcome has them.

    ``incomplete_details`` is the Responses-API counterpart of a ``max_tokens`` stop reason: it is
    how a reply cut at the ceiling identifies itself, and it was unreachable while capture recorded
    the parsed object.
    """
    fields = body if isinstance(body, dict) else {}
    output = fields.get("output")
    return {
        "status": fields.get("status"),
        "incomplete_details": fields.get("incomplete_details"),
        "output_item_types": [
            item.get("type") if isinstance(item, dict) else None
            for item in (output if isinstance(output, list) else [])
        ],
        "usage": fields.get("usage"),
        # The model's actual output; every other key here is a summary of it.
        "body": fields,
    }


def _validation_detail(exc: ValidationError, *, max_errors: int = 8, limit: int = 1200) -> str:
    """Summarize which fields rejected a structured response, for an internal diagnostic only.

    Without this, a strict-schema rejection surfaces as the bare kind ``structured_output_invalid``
    and there is no way to tell a truncated response from a genuinely malformed field. Values are
    excluded — the field path, error type, and message are what identify the defect.
    """

    parts = []
    for error in exc.errors()[:max_errors]:
        location = ".".join(str(item) for item in error.get("loc", ())) or "<root>"
        parts.append(f"{location}: {error.get('type', '?')} — {error.get('msg', '')}")
    remaining = max(0, len(exc.errors()) - max_errors)
    if remaining:
        parts.append(f"(+{remaining} more)")
    return "; ".join(parts)[:limit]


class OpenAIProvider(StructuredModelProvider):
    """OpenAI Responses API adapter using SDK-native Pydantic parsing."""

    provider_name = "openai"
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
        # Accepted and recorded on both adapters so a role's reasoning depth is one value in one
        # place. Only the Anthropic path puts it on the wire today: the Responses API expresses the
        # same idea as a differently-shaped, model-gated `reasoning` field, and guessing that mapping
        # without a live call to check would trade one unverified default for another -- which is the
        # defect this card exists to remove. The value still reaches the capture, so a run says what
        # each role was configured to do even where the adapter cannot yet honor it.
        self.thinking = thinking
        self.effort = effort
        resolved_model = model or os.getenv("OPENAI_MODEL")
        if not resolved_model:
            raise ModelConfigurationError("OpenAI model is not configured")
        self.policy_decision: ModelPolicyDecision = ensure_model_allowed(
            provider=self.provider_name,
            model=resolved_model,
            allow_pro_model=allow_pro_model,
        )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ModelConfigurationError("OpenAI provider dependency is unavailable") from exc

        self.model_name = resolved_model
        self._client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
    ) -> T:
        request_kwargs: dict[str, object] = {
            "model": self.model_name,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "text_format": output_model,
        }
        # Capture the wire body BEFORE the SDK post-parser runs. This adapter sat one step further
        # back than its Anthropic sibling: the hook was below BOTH the validation raise and the
        # `parsed is None` raise, so every failure shape wrote nothing, and a success recorded the
        # parsed object rather than the envelope -- no `status`, no `incomplete_details`, no `usage`.
        capturing = capture_enabled()
        receipt: CaptureReceipt | None = None
        try:
            if capturing:
                raw_response = self._client.responses.with_raw_response.parse(**request_kwargs)  # type: ignore[arg-type]
                receipt = capture_paid_leaf(
                    "models.openai.generate_structured",
                    request={
                        "model": self.model_name,
                        "system_prompt": system_prompt,
                        "user_prompt": user_prompt,
                        "output_model": output_model.__name__,
                        "thinking": self.thinking,
                        "effort": self.effort,
                    },
                    response=_response_envelope(raw_response_body(raw_response)),
                    model=self.model_name,
                )
                response = raw_response.parse()
            else:
                # Capture disabled: the original path, byte for byte.
                response = self._client.responses.parse(**request_kwargs)  # type: ignore[arg-type]
        except (TypeError, AssertionError):
            raise
        except ValidationError as exc:
            capture_parse_failure(receipt, exc)
            raise StructuredModelProviderError(
                StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=self.provider_id,
                detail=_validation_detail(exc),
                partial_output_text=partial_json_text(exc),
            ) from exc
        except Exception as exc:
            capture_parse_failure(receipt, exc)
            kind = _openai_failure_kind(exc)
            if kind is None:
                raise
            raise StructuredModelProviderError(kind, provider_id=self.provider_id) from exc
        parsed = response.output_parsed
        if parsed is None:
            raise StructuredModelProviderError(
                StructuredModelFailureKind.INVALID_RESPONSE,
                provider_id=self.provider_id,
                detail=f"status={getattr(response, 'status', None)!r}, no parsable output",
            )
        return cast(T, parsed)


def _openai_failure_kind(exc: Exception) -> StructuredModelFailureKind | None:
    # Billing is checked BEFORE the type name, and the order is the whole fix: OpenAI ships
    # `insufficient_quota` as a `RateLimitError`, so the name test below claims it first and reports
    # a throttle. An empty balance and a throttle call for opposite actions -- pay, versus wait --
    # and the run told the operator to wait.
    if is_account_exhaustion_error(exc):
        return StructuredModelFailureKind.ACCOUNT_EXHAUSTED
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
