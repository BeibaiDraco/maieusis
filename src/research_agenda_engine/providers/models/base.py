from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ...schemas.gate_outcome import ReviewerExecutionKind

T = TypeVar("T", bound=BaseModel)

#: What the adapters sent before reasoning depth was configurable: nothing. Both vendors then
#: applied their own default, so every role in the product ran on a reasoning setting nobody in
#: this repository had chosen.
#:
#: The default is that same state NAMED rather than replaced, because no single value can restate
#: it: omitting `thinking` runs adaptive on claude-sonnet-5 and NO thinking on claude-opus-4-8
#: (249 of 489 sonnet-5 replies in the capture archive carry a thinking block, against 0 of 204 on
#: opus-4-8). Defaulting to a named value would therefore have switched thinking ON for every
#: opus-4-8 role -- including the reviewer frozen by the published v0.1.0 pair contract.
VENDOR_DEFAULT = "vendor_default"
DEFAULT_THINKING = VENDOR_DEFAULT
DEFAULT_EFFORT = VENDOR_DEFAULT

#: Output ceiling for one Anthropic reply, shared by the structured-model adapter and the
#: scientific-agent (gate reviewer) adapter. It lives here because those are two different
#: packages that must not drift: the old 8_192 was NAMED in `anthropic_provider` — with a comment
#: explaining that naming it is what makes a raised ceiling falsifiable — and INLINED twice in
#: `scientific_agents/anthropic`, which is the path where every measured truncation happened.
#:
#: On models with server-side adaptive thinking this single budget is SHARED with the thinking
#: block, so the answer gets whatever the thinking leaves. Measured across the live capture
#: archive: 5 of 408 Anthropic gate turns stopped at `max_tokens`. Every one carries a thinking
#: block whose TEXT is empty and whose signature runs 26,356-31,172 characters -- the reasoning
#: alone consumed the budget. Three of the five still managed a partial answer before the cut
#: (4,172 / 1,661 / 4,087 characters, each opening with a COMPLETE `"decision"` field); the other
#: two produced no text block at all. They are not correlated with input size (a 46 kB request
#: truncated while a 284 kB one did not), and all five were `claude-sonnet-5`, which is
#: `models.reviewer` on the climate profile.
#:
#: 21_000 is chosen, not guessed. Successful gate replies spend up to 29,582 characters of
#: thinking + signature + answer (median 7,804, p90 18,595), so the old ceiling sat inside the
#: live distribution's tail rather than beyond it. 21_000 clears the observed maximum with room
#: and is the largest value the SDK accepts on the NON-STREAMING path: probed against the live
#: API, 21,250 is accepted and 21,500 raises "Streaming is required for operations that may take
#: longer than 10 minutes". Going higher is not a constant change, it is a transport change.
#:
#: Raising a ceiling costs nothing by itself — `max_tokens` is a cap, not an order, and billing
#: follows the tokens actually produced.
ANTHROPIC_MAX_OUTPUT_TOKENS = 21_000


def reasoning_request_kwargs(thinking: str, effort: str) -> dict[str, object]:
    """The request keys a stated reasoning depth adds -- and NOTHING when it is the vendor default.

    Omission is the point: a key carrying the vendor's own default is still a key that was not on
    the wire before, and `output_config` is the same object that carries the structured-output
    format. Returning an empty dict keeps a default-configured run byte-identical to the runs that
    came before this field existed.
    """
    kwargs: dict[str, object] = {}
    if thinking != VENDOR_DEFAULT:
        kwargs["thinking"] = {"type": thinking}
    if effort != VENDOR_DEFAULT:
        kwargs["output_config"] = {"effort": effort}
    return kwargs


class StructuredModelFailureKind(StrEnum):
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    SERVER_ERROR = "server_error"
    INVALID_RESPONSE = "invalid_response"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    # The reply was cut at the output ceiling. Distinct from the two above because it is the one
    # reply shape a bounded retry CANNOT fix by replaying: the packet is unchanged, the ceiling is
    # unchanged, so an identical request truncates identically. Six novelty reviews died this way on
    # the 2026-07-31 leg and were retried three times each -- 18 fully-billed calls that could not
    # have succeeded. A caller that can see this kind can raise the ceiling instead of replaying.
    OUTPUT_TRUNCATED = "output_truncated"


def partial_json_text(exc: ValidationError) -> str:
    """The model's own output when a reply was cut mid-JSON, and "" otherwise.

    The SDKs parse structured output with ``TypeAdapter(output_format).validate_json(text)``, so a
    truncated body raises a single ``json_invalid`` error whose ``input`` IS the whole raw text. The
    bytes the vendor billed for are therefore already inside the exception -- no raw-response header
    and no capture directory needed, which is what keeps this off the paid request path entirely.

    Only ``json_invalid`` qualifies. Every other error type means the JSON parsed and the CONTENT was
    rejected: a complete reply the schema refused, with nothing to salvage and no truncation to
    repair.
    """
    errors = exc.errors()
    if len(errors) != 1 or errors[0].get("type") != "json_invalid":
        return ""
    raw = errors[0].get("input")
    return raw if isinstance(raw, str) else ""


class StructuredModelProviderError(RuntimeError):
    """Finite, secret-free failure emitted by a structured model adapter."""

    def __init__(
        self,
        kind: StructuredModelFailureKind,
        *,
        provider_id: str,
        detail: str = "",
        partial_output_text: str = "",
    ):
        self.kind = kind
        self.provider_id = provider_id
        # The reply the vendor cut off, preserved verbatim and NOT interpreted here. A cut-off
        # novelty review holds a complete verdict and rationale -- the 2026-07-31 leg threw away
        # 4,660 billed output tokens of correct science because this attribute did not exist. The
        # adapter is vendor-neutral and serves eight roles with eight authority regimes, so deciding
        # what a partial reply MEANS belongs to the caller that knows its schema. Kept off
        # ``str(self)`` for the same reason as ``detail``.
        self.partial_output_text = partial_output_text
        # ``detail`` carries WHICH field rejected the response, so a validation failure is
        # diagnosable at all. It is deliberately kept OFF ``str(self)``: the message is the
        # secret-free surface this class promises, while the detail quotes provider output and
        # belongs only in an internal diagnostic that already handles model-authored text.
        self.detail = detail
        super().__init__(f"structured model provider failed: {kind.value}")


class ModelConfigurationError(ValueError):
    """A configured provider cannot be constructed without operator/config changes."""


class StructuredModelProvider(ABC):
    """Vendor-neutral interface for typed runtime model calls.

    Codex is the development/runtime shell in the intended workflow; this interface is
    for API model calls made by Maieusis itself.
    """

    provider_name: str
    model_name: str

    @property
    def provider_id(self) -> str:
        return f"{self.provider_name}:{self.model_name}"

    @property
    def execution_kind(self) -> ReviewerExecutionKind:
        """How this provider runs. Concrete default is a LIVE API; the mock provider overrides to MOCK.

        Type-side signal (see ``ReviewerExecutionKind``): a real provider inherits ``LIVE_API``; only
        ``MockModelProvider`` returns ``MOCK``. Used where a gate builds its outcome from a
        ``StructuredModelProvider`` reviewer (e.g. consolidation) so the outcome records execution kind.
        """
        return ReviewerExecutionKind.LIVE_API

    @abstractmethod
    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_model: type[T],
    ) -> T:
        raise NotImplementedError
