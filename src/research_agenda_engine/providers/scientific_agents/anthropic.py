from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from ..capture import (
    capture_enabled,
    capture_paid_leaf,
    capture_paid_leaf_failure,
    capture_parse_failure,
    raw_response_body,
)
from ..models.base import (
    ANTHROPIC_MAX_OUTPUT_TOKENS,
    DEFAULT_EFFORT,
    DEFAULT_THINKING,
    partial_json_text,
    reasoning_request_kwargs,
)
from ..models.policy import ModelPolicyDecision, ensure_model_allowed
from .base import (
    ScientificAgentFailureKind,
    ScientificAgentInfrastructureError,
    ScientificAgentProvider,
    ScientificAgentSession,
    ScientificAgentSessionError,
    ScientificAgentSessionSnapshot,
    ScientificAgentTranscriptRecord,
    is_account_exhaustion_error,
    retry_on_transient,
    scientific_agent_payload_digest,
)

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R")


class _AnthropicGrammarCompilationTimeout(RuntimeError):
    """Secret-free marker for Anthropic's transient structured-output compiler timeout."""


def _is_anthropic_grammar_compilation_timeout(exc: BaseException) -> bool:
    return (
        int(getattr(exc, "status_code", 0) or 0) == 400
        and "grammar compilation timed out" in str(exc).lower()
    )


def _transient_anthropic_error_types() -> tuple[type[BaseException], ...]:
    """The Anthropic SDK's transient (retryable) error types, or () when the SDK is absent.

    An empty tuple means no retry (e.g. injected-fake-client unit tests) — identical to the
    pre-retry behavior. Generic 4xx validation errors (e.g. ``BadRequestError``) are deliberately
    excluded so they propagate immediately. Anthropic's exact structured-output grammar compiler
    timeout is handled separately below because it is a provider infrastructure failure despite
    its 400 status.
    """
    try:
        from anthropic import (
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            RateLimitError,
        )
    except Exception:
        return ()
    return (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)


def _anthropic_parse_with_bounded_retries(call: Callable[[], R]) -> R:
    """Preserve normal retries and retry the exact grammar-compiler timeout once.

    Anthropic sometimes reports a server-side structured-output grammar compilation timeout as a
    400. Retrying every 400 would hide schema/programming errors, so wrap only that exact status and
    message in a secret-free transient marker. The outer two-attempt budget means at most one extra
    provider call for this condition; repeated failure becomes infrastructure-incomplete.
    """

    def normal_retry_cycle() -> R:
        try:
            return retry_on_transient(
                call,
                transient=_transient_anthropic_error_types(),
            )
        except Exception as exc:
            if not _is_anthropic_grammar_compilation_timeout(exc):
                raise
            raise _AnthropicGrammarCompilationTimeout(
                "Anthropic structured-output grammar compilation timed out"
            ) from exc

    return retry_on_transient(
        normal_retry_cycle,
        transient=(_AnthropicGrammarCompilationTimeout,),
        max_attempts=2,
        base_delay=0,
    )


class AnthropicScientificAgentProvider(ScientificAgentProvider):
    provider_name = "anthropic"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        *,
        allow_pro_model: bool = False,
        system_prompt: str = "",
        client: Any | None = None,
        thinking: str = DEFAULT_THINKING,
        effort: str = DEFAULT_EFFORT,
    ) -> None:
        # This is the seam where reasoning depth mattered most and was least visible: 105 of the
        # 107 claude-sonnet-5 replies on the 2026-07-31 leg carried a thinking block, all of it on
        # a vendor default nobody had chosen.
        self._thinking = thinking
        self._effort = effort
        resolved_model = model or os.getenv("ANTHROPIC_MODEL")
        if not resolved_model:
            raise ValueError("Set ANTHROPIC_MODEL or pass model=...")
        self.policy_decision: ModelPolicyDecision = ensure_model_allowed(
            provider=self.provider_name,
            model=resolved_model,
            allow_pro_model=allow_pro_model,
        )
        if client is None:
            try:
                import anthropic
            except ImportError as exc:
                raise RuntimeError(
                    "Install the optional dependency: uv sync --extra anthropic"
                ) from exc
            client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self._client = client
        self._model_id = resolved_model
        self._system_prompt = system_prompt

    @property
    def provider_id(self) -> str:
        return self.provider_name

    @property
    def model_id(self) -> str:
        return self._model_id

    def start_session(
        self,
        *,
        branch_id: str,
        session_id: str,
        prompt_version: str,
    ) -> ScientificAgentSession:
        if not branch_id.strip() or not session_id.strip() or not prompt_version.strip():
            raise ValueError("Anthropic scientific agent requires branch/session/prompt identity")
        return AnthropicScientificAgentSession(
            client=self._client,
            branch_id=branch_id,
            session_id=session_id,
            provider_id=self.provider_id,
            model_id=self.model_id,
            prompt_version=prompt_version,
            system_prompt=self._system_prompt,
            thinking=self._thinking,
            effort=self._effort,
        )

    def resume_session(
        self,
        snapshot: ScientificAgentSessionSnapshot,
        *,
        branch_id: str | None = None,
    ) -> ScientificAgentSession:
        if snapshot.provider_id != self.provider_id:
            raise ValueError("cannot resume snapshot from another provider")
        if snapshot.model_id != self.model_id:
            raise ValueError("cannot resume snapshot from another model")
        if branch_id is not None and branch_id != snapshot.branch_id:
            raise ValueError("cannot resume ScientificAgent session for another branch")
        return AnthropicScientificAgentSession(
            client=self._client,
            branch_id=snapshot.branch_id,
            session_id=snapshot.session_id,
            provider_id=snapshot.provider_id,
            model_id=snapshot.model_id,
            prompt_version=snapshot.prompt_version,
            system_prompt=self._system_prompt,
            transcript=snapshot.transcript,
            provider_session_id=snapshot.provider_session_id,
            provider_metadata=snapshot.provider_metadata,
            # Config is truth and the snapshot is provenance (hard rule 9), so a resumed session
            # keeps the provider's configured depth. Omitting these silently reverted every turn
            # after the first to the module default -- the same silent-default defect this field
            # exists to abolish, reintroduced one function below the fix.
            thinking=self._thinking,
            effort=self._effort,
        )


class AnthropicScientificAgentSession(ScientificAgentSession):
    def __init__(
        self,
        *,
        client: Any,
        branch_id: str,
        session_id: str,
        provider_id: str,
        model_id: str,
        prompt_version: str,
        system_prompt: str,
        transcript: list[ScientificAgentTranscriptRecord] | None = None,
        provider_session_id: str = "",
        provider_metadata: dict[str, str] | None = None,
        thinking: str = DEFAULT_THINKING,
        effort: str = DEFAULT_EFFORT,
    ) -> None:
        self._thinking = thinking
        self._effort = effort
        self._client = client
        self._branch_id = branch_id
        self._session_id = session_id
        self._provider_id = provider_id
        self._model_id = model_id
        self._prompt_version = prompt_version
        self._system_prompt = system_prompt
        self._transcript = list(transcript or [])
        self._provider_session_id = provider_session_id
        self._provider_metadata = dict(provider_metadata or {})

    @property
    def branch_id(self) -> str:
        return self._branch_id

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def prompt_version(self) -> str:
        return self._prompt_version

    def send(self, payload: BaseModel, output_schema: type[T]) -> T:
        payload_branch_id = getattr(payload, "branch_id", None)
        if payload_branch_id is not None and payload_branch_id != self.branch_id:
            raise ValueError("ScientificAgent payload references another branch")
        payload_json = payload.model_dump(mode="json")
        request_kwargs: dict[str, Any] = {
            "model": self.model_id,
            "max_tokens": ANTHROPIC_MAX_OUTPUT_TOKENS,
            "system": self._system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(payload_json, sort_keys=True, default=str),
                }
            ],
            "output_format": output_schema,
            **reasoning_request_kwargs(self._thinking, self._effort),
        }
        # Bounded retry+backoff on transient API failures (429/timeout/connection/5xx). On
        # exhaustion this raises ScientificAgentInfrastructureError, which the orchestrator maps
        # to an infrastructure_incomplete terminal (never a scientific failed_validation).
        capturing = capture_enabled()
        fallback_output: T | None = None
        capture_request: dict[str, Any] | None = None
        try:
            if capturing:
                # Anthropic's `messages.parse` has no generated `with_raw_response.parse` facade in the
                # pinned SDK. This is the same raw-response header used by that SDK's generated facade;
                # calling `raw_response.parse()` then executes its original post-parser unchanged.
                raw_request_kwargs = {
                    **request_kwargs,
                    "extra_headers": {"X-Stainless-Raw-Response": "true"},
                }
                capture_request = self._capture_request(payload, output_schema, raw_request_kwargs)
                raw_response = _anthropic_parse_with_bounded_retries(
                    lambda: self._client.messages.parse(**raw_request_kwargs)
                )
                receipt = capture_paid_leaf(
                    "scientific_agents.anthropic.session_send",
                    request=capture_request,
                    response=raw_response_body(raw_response),
                    model=self.model_id,
                )
            else:
                # Preserve the original SDK parse path byte-for-byte when capture is disabled.
                response = _anthropic_parse_with_bounded_retries(
                    lambda: self._client.messages.parse(**request_kwargs)
                )
                receipt = None
        except ScientificAgentInfrastructureError as exc:
            if isinstance(exc.last_error, _AnthropicGrammarCompilationTimeout):
                response, fallback_output, receipt = self._send_strict_json_fallback(
                    payload=payload,
                    payload_json=payload_json,
                    output_schema=output_schema,
                    capturing=capturing,
                )
                self._provider_metadata["structured_output_recovery"] = (
                    "strict_json_after_grammar_compilation_timeout"
                )
            else:
                kind = _anthropic_session_failure_kind(exc.last_error)
                self._capture_failed_send(
                    capture_request,
                    exc.last_error,
                    kind=kind,
                    attempts=exc.attempts,
                )
                if kind is None:
                    raise
                raise ScientificAgentSessionError(
                    kind,
                    provider_id=self.provider_id,
                    attempts=exc.attempts,
                    last_error=exc.last_error,
                ) from exc
        except ValidationError as exc:
            self._capture_failed_send(
                capture_request,
                exc,
                kind=ScientificAgentFailureKind.STRUCTURED_OUTPUT_INVALID,
            )
            raise ScientificAgentSessionError(
                ScientificAgentFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=self.provider_id,
                last_error=exc,
            ) from exc
        except (TypeError, AssertionError) as exc:
            self._capture_failed_send(capture_request, exc, kind=None)
            raise
        except Exception as exc:
            kind = _anthropic_session_failure_kind(exc)
            self._capture_failed_send(capture_request, exc, kind=kind)
            if kind is None:
                raise
            raise ScientificAgentSessionError(
                kind, provider_id=self.provider_id, last_error=exc
            ) from exc
        try:
            if fallback_output is not None:
                output = fallback_output
            else:
                if capturing:
                    response = raw_response.parse()
                # A reply that ran out of room is not a malformed reply, and the response has
                # said so all along -- nothing read it. This branch catches the shape with NO text
                # block at all (2 of the 5 measured truncations): `parsed_output` is None and they
                # landed in INVALID_RESPONSE, the same bucket as a garbled answer. The other 3
                # carry a text block cut mid-JSON, which the SDK's post-parser rejects one line
                # above -- they are named in the ValidationError handler below, which is the only
                # place they can be reached.
                if getattr(response, "stop_reason", None) == "max_tokens":
                    raise ScientificAgentSessionError(
                        ScientificAgentFailureKind.OUTPUT_TRUNCATED,
                        provider_id=self.provider_id,
                        last_error=ValueError(
                            "reply stopped at the "
                            f"{ANTHROPIC_MAX_OUTPUT_TOKENS}-token output ceiling"
                        ),
                    )
                parsed = response.parsed_output
                if parsed is None:
                    raise ScientificAgentSessionError(
                        ScientificAgentFailureKind.INVALID_RESPONSE,
                        provider_id=self.provider_id,
                        last_error=ValueError("parsed structured output missing"),
                    )
                output = output_schema.model_validate(parsed)
        except ValidationError as exc:
            capture_parse_failure(receipt, exc)
            # 3 of the 5 measured truncations land HERE, not in the branch above: their reply
            # carries a text block cut mid-JSON, so the SDK's post-parser raises before any
            # `stop_reason` can be read off a parsed message. All three open with a COMPLETE
            # `"decision"` field -- `{"decision":"accept",...` twice and `{"decision":"revise",...`
            # once -- so calling them "structured output invalid" both misnames the cause and
            # throws away a verdict the run already paid for.
            #
            # `raw_response` is still in scope on the capturing path (which is the path a live leg
            # takes: launch.sh exports MAIEUSIS_CAPTURE_DIR), and its RAW body carries the
            # stop_reason the parsed message never got to expose. Without capture there is no
            # response object at all -- `messages.parse` raised inside the retry helper -- so the
            # kind stays honest at STRUCTURED_OUTPUT_INVALID rather than guessing from the bytes.
            truncated = False
            if capturing:
                body = raw_response_body(raw_response)
                truncated = bool(isinstance(body, dict) and body.get("stop_reason") == "max_tokens")
            raise ScientificAgentSessionError(
                ScientificAgentFailureKind.OUTPUT_TRUNCATED
                if truncated
                else ScientificAgentFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=self.provider_id,
                last_error=exc,
                partial_output_text=partial_json_text(exc),
            ) from exc
        except Exception as exc:
            capture_parse_failure(receipt, exc)
            raise
        output_branch_id = getattr(output, "branch_id", None)
        # An empty branch claim is "no claim" (the caller code-stamps the branch on the
        # strict rebuild); only a non-empty claim of ANOTHER branch is a cross-branch leak.
        if output_branch_id and output_branch_id != self.branch_id:
            raise ValueError("ScientificAgent output references another branch")
        response_id = str(getattr(response, "id", "") or "")
        if response_id:
            self._provider_session_id = response_id
        response_usage = getattr(response, "usage", None)
        usage_input = getattr(response_usage, "input_tokens", None)
        usage_output = getattr(response_usage, "output_tokens", None)
        usage_total: int | None = None
        if usage_input is not None or usage_output is not None:
            usage_total = int(usage_input or 0) + int(usage_output or 0)
        output_payload = output.model_dump(mode="json")
        sequence = len(self._transcript) + 1
        record = ScientificAgentTranscriptRecord(
            sequence=sequence,
            turn_id=f"{self.session_id}-turn-{sequence:03d}",
            branch_id=self.branch_id,
            session_id=self.session_id,
            provider_id=self.provider_id,
            model_id=self.model_id,
            prompt_version=self.prompt_version,
            input_schema=payload.__class__.__name__,
            input_payload=payload_json,
            input_digest=scientific_agent_payload_digest(payload_json),
            output_schema=output_schema.__name__,
            output_payload=output_payload,
            output_digest=scientific_agent_payload_digest(output_payload),
            provider_response_id=response_id,
            input_tokens=usage_input,
            output_tokens=usage_output,
            total_tokens=usage_total,
        )
        self._transcript.append(record)
        return output

    def _send_strict_json_fallback(
        self,
        *,
        payload: BaseModel,
        payload_json: dict[str, Any],
        output_schema: type[T],
        capturing: bool,
    ) -> tuple[Any, T, Any]:
        """Bypass only Anthropic's unavailable grammar compiler; keep strict local validation.

        This is a single, non-retrying recovery call after both structured-output attempts failed
        with Anthropic's exact grammar-compilation timeout. It uses the same model and scientific
        prompt, accepts only a bare JSON object, and rebuilds the original Pydantic output schema.
        It is not a prose repair path and does not relax any scientific or authority field.
        """
        fallback_system = (
            f"{self._system_prompt}\n\n"
            "TRANSPORT RECOVERY: The provider's structured-output grammar compiler was unavailable. "
            "Return exactly one JSON object matching required_output_schema. Do not use Markdown "
            "fences, commentary, or text before or after the JSON object."
        )
        fallback_payload = {
            "scientific_input": payload_json,
            "required_output_schema": output_schema.model_json_schema(),
        }
        request_kwargs: dict[str, Any] = {
            "model": self.model_id,
            "max_tokens": ANTHROPIC_MAX_OUTPUT_TOKENS,
            "system": fallback_system,
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(fallback_payload, sort_keys=True, default=str),
                }
            ],
            # The recovery call keeps the session's stated reasoning depth. Letting it fall back to
            # the vendor default would make the retry differ from the attempt it is recovering.
            **reasoning_request_kwargs(self._thinking, self._effort),
        }
        receipt = None
        capture_request: dict[str, Any] | None = None
        try:
            if capturing:
                raw_request_kwargs = {
                    **request_kwargs,
                    "extra_headers": {"X-Stainless-Raw-Response": "true"},
                }
                capture_request = self._capture_request(payload, output_schema, raw_request_kwargs)
                raw_response = self._client.messages.create(**raw_request_kwargs)
                receipt = capture_paid_leaf(
                    "scientific_agents.anthropic.session_send_strict_json_recovery",
                    request=capture_request,
                    response=raw_response_body(raw_response),
                    model=self.model_id,
                )
                response = raw_response.parse()
            else:
                response = self._client.messages.create(**request_kwargs)
        except (TypeError, AssertionError) as exc:
            self._capture_failed_send(
                capture_request,
                exc,
                kind=None,
                seam="scientific_agents.anthropic.session_send_strict_json_recovery",
            )
            raise
        except Exception as exc:
            kind = _anthropic_session_failure_kind(exc)
            self._capture_failed_send(
                capture_request,
                exc,
                kind=kind,
                seam="scientific_agents.anthropic.session_send_strict_json_recovery",
            )
            if kind is None:
                raise
            raise ScientificAgentSessionError(
                kind,
                provider_id=self.provider_id,
                attempts=1,
                last_error=exc,
            ) from exc

        try:
            content = getattr(response, "content", None)
            if not isinstance(content, list):
                raise ValueError("Anthropic JSON recovery response has no content list")
            text_parts: list[str] = []
            for block in content:
                text = (
                    block.get("text") if isinstance(block, dict) else getattr(block, "text", None)
                )
                if isinstance(text, str):
                    text_parts.append(text)
            raw_text = "".join(text_parts).strip()
            decoded = json.loads(raw_text)
            if not isinstance(decoded, dict):
                raise ValueError("Anthropic JSON recovery response is not one JSON object")
            output = output_schema.model_validate(decoded)
        except ValidationError as exc:
            capture_parse_failure(receipt, exc)
            raise ScientificAgentSessionError(
                ScientificAgentFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=self.provider_id,
                attempts=1,
                last_error=exc,
            ) from exc
        except (json.JSONDecodeError, ValueError) as exc:
            capture_parse_failure(receipt, exc)
            raise ScientificAgentSessionError(
                ScientificAgentFailureKind.INVALID_RESPONSE,
                provider_id=self.provider_id,
                attempts=1,
                last_error=exc,
            ) from exc
        return response, output, receipt

    def _capture_request(
        self,
        payload: BaseModel,
        output_schema: type[BaseModel],
        request_kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "provider": self.provider_id,
            "model": self.model_id,
            "branch_id": self.branch_id,
            "session_id": self.session_id,
            "prompt_version": self.prompt_version,
            "input_schema": payload.__class__.__name__,
            "output_schema": output_schema.__name__,
            "wire": request_kwargs,
        }

    def _capture_failed_send(
        self,
        request: dict[str, Any] | None,
        error: BaseException,
        *,
        kind: ScientificAgentFailureKind | None,
        attempts: int = 1,
        seam: str = "scientific_agents.anthropic.session_send",
    ) -> None:
        if request is None:
            return
        capture_paid_leaf_failure(
            seam,
            request=request,
            error=error,
            provider=self.provider_id,
            model=self.model_id,
            failure_kind=kind.value if kind is not None else "unclassified",
            attempts=attempts,
        )

    def snapshot(self) -> ScientificAgentSessionSnapshot:
        return ScientificAgentSessionSnapshot(
            branch_id=self.branch_id,
            session_id=self.session_id,
            provider_id=self.provider_id,
            model_id=self.model_id,
            prompt_version=self.prompt_version,
            provider_session_id=self._provider_session_id,
            provider_metadata=self._provider_metadata,
            transcript=self._transcript,
        )


def _anthropic_session_failure_kind(exc: BaseException) -> ScientificAgentFailureKind | None:
    if is_account_exhaustion_error(exc):
        return ScientificAgentFailureKind.ACCOUNT_EXHAUSTED
    if isinstance(exc, _AnthropicGrammarCompilationTimeout):
        return ScientificAgentFailureKind.SERVER_ERROR
    name = type(exc).__name__
    if name in {"AuthenticationError", "PermissionDeniedError"}:
        return ScientificAgentFailureKind.AUTHENTICATION
    if name == "RateLimitError":
        return ScientificAgentFailureKind.RATE_LIMIT
    if name in {"APITimeoutError", "TimeoutError"}:
        return ScientificAgentFailureKind.TIMEOUT
    if name in {"APIConnectionError", "ConnectionError"}:
        return ScientificAgentFailureKind.CONNECTION
    if name == "InternalServerError" or int(getattr(exc, "status_code", 0) or 0) >= 500:
        return ScientificAgentFailureKind.SERVER_ERROR
    if name in {"APIResponseValidationError", "JSONDecodeError"}:
        return ScientificAgentFailureKind.INVALID_RESPONSE
    return None
