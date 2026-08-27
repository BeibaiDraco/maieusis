from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ...provenance import stable_hash
from ...schemas.gate_outcome import ReviewerExecutionKind

# Re-exported: this lane's two adapters import it from here, and it is now shared with the
# generation lane so one predicate decides "the account is empty" for both.
from ..models.base import is_account_exhaustion_error as is_account_exhaustion_error

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R")


def _payload_dict(payload: BaseModel) -> dict[str, Any]:
    return payload.model_dump(mode="json")


def scientific_agent_payload_digest(payload: BaseModel | dict[str, Any]) -> str:
    if isinstance(payload, BaseModel):
        payload = _payload_dict(payload)
    return stable_hash(payload)


class ScientificAgentInfrastructureError(RuntimeError):
    """A bounded retry on a transient provider/API failure was exhausted.

    Distinct from a scientific failure: the owner/reviewer API was unreachable (rate limit /
    timeout / connection / server error), not that the plan is scientifically unsound. The
    orchestrator maps this to an ``infrastructure_incomplete`` terminal, never a scientific
    ``failed_validation`` — infrastructure must not masquerade as science.
    """

    def __init__(self, *, attempts: int, last_error: BaseException) -> None:
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"scientific agent API failed after {attempts} attempt(s): "
            f"{type(last_error).__name__}: {last_error}"
        )


class ScientificAgentFailureKind(StrEnum):
    ACCOUNT_EXHAUSTED = "account_exhausted"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    SERVER_ERROR = "server_error"
    INVALID_RESPONSE = "invalid_response"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    #: The reviewer ran out of room. Reply-shaped like the two above -- the provider answered and
    #: the answer was cut at the ceiling -- and NOT provider exhaustion, so it is contained per
    #: artifact. Its absence is why every measured gate truncation reached the run as
    #: `invalid_response`, indistinguishable from a garbled reply.
    OUTPUT_TRUNCATED = "output_truncated"


class ScientificAgentSessionError(ScientificAgentInfrastructureError):
    """Finite, secret-free expected failure at a scientific-agent session boundary."""

    def __init__(
        self,
        kind: ScientificAgentFailureKind,
        *,
        provider_id: str,
        attempts: int = 1,
        last_error: BaseException,
        partial_output_text: str = "",
    ) -> None:
        self.kind = kind
        self.provider_id = provider_id
        self.attempts = attempts
        self.last_error = last_error
        #: Whatever the model DID write before it was cut off. #139 gave the structured-model
        #: error this attribute and the session error never got one, so a gate reply carrying a
        #: complete `"decision"` field was discarded as unparseable. Kept off `str(self)` so a
        #: reply body never leaks into a log line.
        self.partial_output_text = partial_output_text
        RuntimeError.__init__(self, f"scientific agent session failed: {kind.value}")


def retry_on_transient(
    call: Callable[[], R],
    *,
    transient: tuple[type[BaseException], ...],
    max_attempts: int = 3,
    base_delay: float = 0.5,
    sleep: Callable[[float], None] = time.sleep,
) -> R:
    """Call ``call`` with bounded exponential-backoff retry on transient errors.

    Retries only when the raised exception is an instance of ``transient`` (e.g. the SDK's
    rate-limit / timeout / connection / server-error types). Any other exception — a 4xx
    validation error, a programming bug — propagates immediately: it is never retried and never
    reclassified as infrastructure. On exhaustion raises ``ScientificAgentInfrastructureError``
    carrying the attempt count and last error. ``sleep`` is injectable so tests run instantly.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    last_error: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return call()
        except transient as exc:
            last_error = exc
            if attempt >= max_attempts:
                break
            sleep(base_delay * (2 ** (attempt - 1)))
    assert last_error is not None
    raise ScientificAgentInfrastructureError(attempts=max_attempts, last_error=last_error)


class ScientificAgentTranscriptRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sequence: int = Field(ge=1)
    turn_id: str
    branch_id: str
    session_id: str
    provider_id: str
    model_id: str
    prompt_version: str
    input_schema: str
    input_payload: dict[str, Any]
    input_digest: str
    output_schema: str
    output_payload: dict[str, Any]
    output_digest: str
    provider_response_id: str = ""
    # Per-call token/cost usage (optional). Populated from the SDK response by the real openai /
    # anthropic sessions; the mock session stamps injected mock numbers. ``cost_usd`` stays None for
    # review calls (the SDKs report tokens, not USD).
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "turn_id",
        "branch_id",
        "session_id",
        "provider_id",
        "model_id",
        "prompt_version",
        "input_schema",
        "input_digest",
        "output_schema",
        "output_digest",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ScientificAgent transcript fields must be non-empty")
        return value

    @field_validator("input_digest", "output_digest")
    @classmethod
    def require_sha256_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("ScientificAgent transcript digest must be sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_payload_digests(self) -> ScientificAgentTranscriptRecord:
        if self.input_digest != scientific_agent_payload_digest(self.input_payload):
            raise ValueError("ScientificAgent transcript input_digest does not match payload")
        if self.output_digest != scientific_agent_payload_digest(self.output_payload):
            raise ValueError("ScientificAgent transcript output_digest does not match payload")
        return self


class ScientificAgentSessionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    branch_id: str
    session_id: str
    provider_id: str
    model_id: str
    prompt_version: str
    provider_session_id: str = ""
    provider_metadata: dict[str, str] = Field(default_factory=dict)
    transcript: list[ScientificAgentTranscriptRecord] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("branch_id", "session_id", "provider_id", "model_id", "prompt_version")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ScientificAgentSessionSnapshot identity fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_transcript(self) -> ScientificAgentSessionSnapshot:
        sequences = [record.sequence for record in self.transcript]
        if sequences != list(range(1, len(sequences) + 1)):
            raise ValueError("ScientificAgentSessionSnapshot transcript must be contiguous")
        turn_ids = [record.turn_id for record in self.transcript]
        if len(turn_ids) != len(set(turn_ids)):
            raise ValueError("ScientificAgentSessionSnapshot transcript turn IDs must be unique")
        for record in self.transcript:
            if record.branch_id != self.branch_id:
                raise ValueError("ScientificAgentSessionSnapshot contains another branch")
            if record.session_id != self.session_id:
                raise ValueError("ScientificAgentSessionSnapshot contains another session")
            if record.provider_id != self.provider_id:
                raise ValueError("ScientificAgentSessionSnapshot contains another provider")
            if record.model_id != self.model_id:
                raise ValueError("ScientificAgentSessionSnapshot contains another model")
            if record.prompt_version != self.prompt_version:
                raise ValueError("ScientificAgentSessionSnapshot contains another prompt")
        return self


class ScientificAgentSession(ABC):
    @property
    @abstractmethod
    def branch_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def session_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def provider_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def model_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def prompt_version(self) -> str:
        raise NotImplementedError

    @property
    def execution_kind(self) -> ReviewerExecutionKind:
        """How this session runs. Concrete default is a LIVE API; the mock session overrides to MOCK.

        Type-side (not a forgeable string): a real openai/anthropic session inherits ``LIVE_API``; only
        ``MockScientificAgentSession`` returns ``MOCK``. Consumed by the gate kernel to stamp the
        outcome + promotion receipt so a mock-reviewed artifact fails the product-grade gate.
        """
        return ReviewerExecutionKind.LIVE_API

    @abstractmethod
    def send(self, payload: BaseModel, output_schema: type[T]) -> T:
        raise NotImplementedError

    @abstractmethod
    def snapshot(self) -> ScientificAgentSessionSnapshot:
        raise NotImplementedError


class ScientificAgentProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def model_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def start_session(
        self,
        *,
        branch_id: str,
        session_id: str,
        prompt_version: str,
    ) -> ScientificAgentSession:
        raise NotImplementedError

    @abstractmethod
    def resume_session(
        self,
        snapshot: ScientificAgentSessionSnapshot,
        *,
        branch_id: str | None = None,
    ) -> ScientificAgentSession:
        raise NotImplementedError
