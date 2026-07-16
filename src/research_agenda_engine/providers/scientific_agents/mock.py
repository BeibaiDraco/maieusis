from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from ...schemas.gate_outcome import ReviewerExecutionKind
from .base import (
    ScientificAgentFailureKind,
    ScientificAgentProvider,
    ScientificAgentSession,
    ScientificAgentSessionError,
    ScientificAgentSessionSnapshot,
    ScientificAgentTranscriptRecord,
    scientific_agent_payload_digest,
)

T = TypeVar("T", bound=BaseModel)


class MockScientificAgentProvider(ScientificAgentProvider):
    def __init__(
        self,
        *,
        responses: Iterable[BaseModel | dict[str, Any]] = (),
        usages: Iterable[dict[str, Any]] = (),
        provider_id: str = "mock:scientific-agent",
        model_id: str = "deterministic-scientific-agent",
    ) -> None:
        self._responses = list(responses)
        self._usages = list(usages)
        self._provider_id = provider_id
        self._model_id = model_id

    @property
    def provider_id(self) -> str:
        return self._provider_id

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
            raise ValueError("MockScientificAgentProvider requires branch/session/prompt identity")
        return MockScientificAgentSession(
            branch_id=branch_id,
            session_id=session_id,
            provider_id=self.provider_id,
            model_id=self.model_id,
            prompt_version=prompt_version,
            responses=self._responses,
            usages=self._usages,
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
        return MockScientificAgentSession(
            branch_id=snapshot.branch_id,
            session_id=snapshot.session_id,
            provider_id=snapshot.provider_id,
            model_id=snapshot.model_id,
            prompt_version=snapshot.prompt_version,
            responses=self._responses,
            usages=self._usages,
            transcript=snapshot.transcript,
            provider_session_id=snapshot.provider_session_id,
            provider_metadata=snapshot.provider_metadata,
        )


class MockScientificAgentSession(ScientificAgentSession):
    def __init__(
        self,
        *,
        branch_id: str,
        session_id: str,
        provider_id: str,
        model_id: str,
        prompt_version: str,
        responses: list[BaseModel | dict[str, Any]],
        usages: list[dict[str, Any]] | None = None,
        transcript: list[ScientificAgentTranscriptRecord] | None = None,
        provider_session_id: str = "",
        provider_metadata: dict[str, str] | None = None,
    ) -> None:
        self._branch_id = branch_id
        self._session_id = session_id
        self._provider_id = provider_id
        self._model_id = model_id
        self._prompt_version = prompt_version
        self._responses = list(responses)
        self._usages = list(usages or [])
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

    @property
    def execution_kind(self) -> ReviewerExecutionKind:
        return ReviewerExecutionKind.MOCK

    def send(self, payload: BaseModel, output_schema: type[T]) -> T:
        payload_branch_id = getattr(payload, "branch_id", None)
        if payload_branch_id is not None and payload_branch_id != self.branch_id:
            raise ValueError("ScientificAgent payload references another branch")
        sequence = len(self._transcript) + 1
        if self._responses:
            raw_response = self._responses.pop(0)
        else:
            raw_response = {
                "branch_id": self.branch_id,
                "message": f"mock response {sequence}",
            }
        response_payload = (
            raw_response.model_dump(mode="json")
            if isinstance(raw_response, BaseModel)
            else raw_response
        )
        try:
            output = output_schema.model_validate(response_payload)
        except (TypeError, AssertionError):
            raise
        except ValidationError as exc:
            raise ScientificAgentSessionError(
                ScientificAgentFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=self.provider_id,
                last_error=exc,
            ) from exc
        output_branch_id = getattr(output, "branch_id", None)
        # An empty branch claim is "no claim" (the caller code-stamps the branch on the
        # strict rebuild); only a non-empty claim of ANOTHER branch is a cross-branch leak.
        if output_branch_id and output_branch_id != self.branch_id:
            raise ValueError("ScientificAgent output references another branch")
        input_payload = payload.model_dump(mode="json")
        output_payload = output.model_dump(mode="json")
        usage = self._usages.pop(0) if self._usages else {}
        record = ScientificAgentTranscriptRecord(
            sequence=sequence,
            turn_id=f"{self.session_id}-turn-{sequence:03d}",
            branch_id=self.branch_id,
            session_id=self.session_id,
            provider_id=self.provider_id,
            model_id=self.model_id,
            prompt_version=self.prompt_version,
            input_schema=payload.__class__.__name__,
            input_payload=input_payload,
            input_digest=scientific_agent_payload_digest(input_payload),
            output_schema=output_schema.__name__,
            output_payload=output_payload,
            output_digest=scientific_agent_payload_digest(output_payload),
            provider_response_id=f"mock-response-{sequence:03d}",
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            total_tokens=usage.get("total_tokens"),
            cost_usd=usage.get("cost_usd"),
        )
        self._transcript.append(record)
        return output

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
