from __future__ import annotations

import json
import os
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from ..capture import (
    capture_enabled,
    capture_paid_leaf,
    capture_paid_leaf_failure,
    capture_parse_failure,
    raw_response_body,
)
from ..models.base import DEFAULT_EFFORT, DEFAULT_THINKING
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


def _transient_openai_error_types() -> tuple[type[BaseException], ...]:
    """The OpenAI SDK's transient (retryable) error types, or () when the SDK is absent.

    An empty tuple means no retry (e.g. injected-fake-client unit tests) — identical to the
    pre-retry behavior. 4xx validation errors (e.g. ``BadRequestError``) are deliberately
    excluded so they propagate immediately.
    """
    try:
        from openai import (
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            RateLimitError,
        )
    except Exception:
        return ()
    return (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)


class OpenAIScientificAgentProvider(ScientificAgentProvider):
    provider_name = "openai"

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
        # Carried and recorded so a role's reasoning depth is one value across both hosts. The
        # Responses API expresses it differently and gates it by model, so this adapter states the
        # value rather than guessing a wire mapping it cannot verify here.
        self._thinking = thinking
        self._effort = effort
        resolved_model = model or os.getenv("OPENAI_MODEL")
        if not resolved_model:
            raise ValueError("Set OPENAI_MODEL or pass model=...")
        self.policy_decision: ModelPolicyDecision = ensure_model_allowed(
            provider=self.provider_name,
            model=resolved_model,
            allow_pro_model=allow_pro_model,
        )
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise RuntimeError(
                    "Install the optional dependency: uv sync --extra openai"
                ) from exc
            client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
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
            raise ValueError("OpenAI scientific agent requires branch/session/prompt identity")
        return OpenAIScientificAgentSession(
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
        return OpenAIScientificAgentSession(
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
            # Same reason as the Anthropic lane: a resumed session keeps the provider's configured
            # depth rather than silently reverting to the module default.
            thinking=self._thinking,
            effort=self._effort,
        )


class OpenAIScientificAgentSession(ScientificAgentSession):
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
            "input": [
                {"role": "system", "content": self._system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(payload_json, sort_keys=True, default=str),
                },
            ],
            "text_format": output_schema,
        }
        # Bounded retry+backoff on transient API failures (429/timeout/connection/5xx). On
        # exhaustion this raises ScientificAgentInfrastructureError, which the orchestrator maps
        # to an infrastructure_incomplete terminal (never a scientific failed_validation).
        capturing = capture_enabled()
        capture_request: dict[str, Any] | None = None
        try:
            if capturing:
                capture_request = self._capture_request(payload, output_schema, request_kwargs)
                raw_response = retry_on_transient(
                    lambda: self._client.responses.with_raw_response.parse(**request_kwargs),
                    transient=_transient_openai_error_types(),
                )
                receipt = capture_paid_leaf(
                    "scientific_agents.openai.session_send",
                    request=capture_request,
                    response=raw_response_body(raw_response),
                    model=self.model_id,
                )
            else:
                # Preserve the original SDK parse path byte-for-byte when capture is disabled.
                response = retry_on_transient(
                    lambda: self._client.responses.parse(**request_kwargs),
                    transient=_transient_openai_error_types(),
                )
                receipt = None
        except ScientificAgentInfrastructureError as exc:
            kind = _openai_session_failure_kind(exc.last_error)
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
            kind = _openai_session_failure_kind(exc)
            self._capture_failed_send(capture_request, exc, kind=kind)
            if kind is None:
                raise
            raise ScientificAgentSessionError(
                kind, provider_id=self.provider_id, last_error=exc
            ) from exc
        try:
            if capturing:
                response = raw_response.parse()
            parsed = response.output_parsed
            if parsed is None:
                raise ScientificAgentSessionError(
                    ScientificAgentFailureKind.INVALID_RESPONSE,
                    provider_id=self.provider_id,
                    last_error=ValueError("parsed structured output missing"),
                )
            output = output_schema.model_validate(parsed)
        except ValidationError as exc:
            capture_parse_failure(receipt, exc)
            raise ScientificAgentSessionError(
                ScientificAgentFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=self.provider_id,
                last_error=exc,
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
            input_tokens=getattr(response_usage, "input_tokens", None),
            output_tokens=getattr(response_usage, "output_tokens", None),
            total_tokens=getattr(response_usage, "total_tokens", None),
        )
        self._transcript.append(record)
        return output

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
            # Recorded beside the wire rather than inside it: this adapter carries the configured
            # reasoning depth but does not send it, because the Responses API expresses the same
            # idea as a differently-shaped, model-gated field. Keeping it in the capture is what
            # makes "carried and recorded" true -- without this the value was dead state and the
            # claim was false.
            "configured_reasoning_depth": {
                "thinking": self._thinking,
                "effort": self._effort,
                "sent_on_wire": False,
            },
        }

    def _capture_failed_send(
        self,
        request: dict[str, Any] | None,
        error: BaseException,
        *,
        kind: ScientificAgentFailureKind | None,
        attempts: int = 1,
    ) -> None:
        if request is None:
            return
        capture_paid_leaf_failure(
            "scientific_agents.openai.session_send",
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


def _openai_session_failure_kind(exc: BaseException) -> ScientificAgentFailureKind | None:
    if is_account_exhaustion_error(exc):
        return ScientificAgentFailureKind.ACCOUNT_EXHAUSTED
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
