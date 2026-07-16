from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .planning_dialogue import BranchActorRole
from .question_seed import QuestionRevision


class QuestionBranchState(StrEnum):
    PROPOSED = "proposed"
    SHORTLISTED = "shortlisted"
    PLANNER_INSPECTING = "planner_inspecting"
    AWAITING_OWNER_CLARIFICATION = "awaiting_owner_clarification"
    OPERATIONALIZATION_PROPOSED = "operationalization_proposed"
    PLAN_DRAFTED = "plan_drafted"
    OWNER_REVIEW = "owner_review"
    INDEPENDENT_REVIEW = "independent_review"
    HUMAN_REVIEW = "human_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    ARCHIVED = "archived"

    @property
    def is_terminal(self) -> bool:
        return self in {
            QuestionBranchState.ACCEPTED,
            QuestionBranchState.REJECTED,
            QuestionBranchState.ESCALATED,
            QuestionBranchState.ARCHIVED,
        }


class BranchTransitionEvent(StrEnum):
    SHORTLIST = "shortlist"
    PLANNER_STARTED = "planner_started"
    CLARIFICATION_REQUESTED = "clarification_requested"
    CLARIFICATION_RECEIVED = "clarification_received"
    OPERATIONALIZATION_PROPOSED = "operationalization_proposed"
    OPERATIONALIZATION_ACCEPTED = "operationalization_accepted"
    OPERATIONALIZATION_REVISED = "operationalization_revised"
    PLAN_DRAFTED = "plan_drafted"
    OWNER_REVIEW_STARTED = "owner_review_started"
    OWNER_REQUESTS_REVISION = "owner_requests_revision"
    OWNER_REJECTS = "owner_rejects"
    OWNER_ACCEPTS = "owner_accepts"
    REVIEWER_REQUESTS_REVISION = "reviewer_requests_revision"
    REVIEWER_REJECTS = "reviewer_rejects"
    REVIEWER_ACCEPTS = "reviewer_accepts"
    HUMAN_APPROVES = "human_approves"
    HUMAN_REQUESTS_REVISION = "human_requests_revision"
    HUMAN_REJECTS = "human_rejects"
    ESCALATION_REQUESTED = "escalation_requested"
    ARCHIVE = "archive"


class BranchRecordEvent(StrEnum):
    QUESTION_REVISION_RECORDED = "question_revision_recorded"
    DIALOGUE_ROUND_RECORDED = "dialogue_round_recorded"


class BranchEventPayloadSchema(StrEnum):
    BRANCH_TRANSITION = "branch_transition/v1"
    PLANNING_MESSAGE = "planning_message/v1"
    QUESTION_REVISION = "question_revision/v1"
    DIALOGUE_ROUND = "dialogue_round/v1"
    REVIEW_DECISION = "review_decision/v1"
    VALIDATED_PLAN_PACKAGE = "validated_plan_package/v1"


def branch_event_payload_digest(payload: Mapping[str, Any]) -> str:
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class QuestionBranchEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    sequence: int = Field(ge=1)
    branch_id: str
    event_type: str
    actor_role: BranchActorRole
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    parent_event_id: str = ""
    payload_schema: BranchEventPayloadSchema
    payload_digest: str
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id", "branch_id", "event_type", "payload_digest")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionBranchEvent core fields must be non-empty")
        return value

    @field_validator("payload_digest")
    @classmethod
    def require_sha256_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("QuestionBranchEvent payload_digest must be a lowercase sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_payload_digest(self) -> QuestionBranchEvent:
        if self.payload_digest != branch_event_payload_digest(self.payload):
            raise ValueError("QuestionBranchEvent payload_digest does not match payload")
        if self.payload_schema in {
            BranchEventPayloadSchema.BRANCH_TRANSITION,
            BranchEventPayloadSchema.QUESTION_REVISION,
            BranchEventPayloadSchema.DIALOGUE_ROUND,
        }:
            missing = [
                field
                for field in [
                    "branch_id",
                    "question_seed_id",
                    "context_id",
                    "owner_session_id",
                    "event_type",
                    "scientific_intent_invariant_id",
                    "scientific_intent_invariant_digest",
                ]
                if field not in self.payload
            ]
            if missing:
                raise ValueError(
                    "branch transition event payload missing identity fields: " + ", ".join(missing)
                )
            if self.payload["branch_id"] != self.branch_id:
                raise ValueError("QuestionBranchEvent payload branch_id must match event")
            if self.payload["event_type"] != self.event_type:
                raise ValueError("QuestionBranchEvent payload event_type must match event")
        return self


class QuestionBranch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    branch_id: str
    question_seed_id: str
    context_id: str
    owner_session_id: str
    scientific_intent_invariant_id: str
    scientific_intent_invariant_digest: str
    initial_question_version_id: str
    current_question_version_id: str
    state: QuestionBranchState = QuestionBranchState.PROPOSED
    events: tuple[QuestionBranchEvent, ...] = Field(default_factory=tuple)
    material_revision_count: int = 0
    dialogue_round_count: int = 0
    max_material_revisions: int = 2
    max_dialogue_rounds: int = 6
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    LEGAL_TRANSITIONS: ClassVar[
        dict[QuestionBranchState, dict[BranchTransitionEvent, QuestionBranchState]]
    ] = {
        QuestionBranchState.PROPOSED: {
            BranchTransitionEvent.SHORTLIST: QuestionBranchState.SHORTLISTED,
            BranchTransitionEvent.ESCALATION_REQUESTED: QuestionBranchState.ESCALATED,
        },
        QuestionBranchState.SHORTLISTED: {
            BranchTransitionEvent.PLANNER_STARTED: QuestionBranchState.PLANNER_INSPECTING,
            BranchTransitionEvent.ESCALATION_REQUESTED: QuestionBranchState.ESCALATED,
        },
        QuestionBranchState.PLANNER_INSPECTING: {
            BranchTransitionEvent.CLARIFICATION_REQUESTED: (
                QuestionBranchState.AWAITING_OWNER_CLARIFICATION
            ),
            BranchTransitionEvent.OPERATIONALIZATION_PROPOSED: (
                QuestionBranchState.OPERATIONALIZATION_PROPOSED
            ),
            BranchTransitionEvent.PLAN_DRAFTED: QuestionBranchState.PLAN_DRAFTED,
            BranchTransitionEvent.ESCALATION_REQUESTED: QuestionBranchState.ESCALATED,
        },
        QuestionBranchState.AWAITING_OWNER_CLARIFICATION: {
            BranchTransitionEvent.CLARIFICATION_RECEIVED: QuestionBranchState.PLANNER_INSPECTING,
            BranchTransitionEvent.ESCALATION_REQUESTED: QuestionBranchState.ESCALATED,
        },
        QuestionBranchState.OPERATIONALIZATION_PROPOSED: {
            BranchTransitionEvent.OPERATIONALIZATION_ACCEPTED: (
                QuestionBranchState.PLANNER_INSPECTING
            ),
            BranchTransitionEvent.OPERATIONALIZATION_REVISED: (
                QuestionBranchState.PLANNER_INSPECTING
            ),
            BranchTransitionEvent.ESCALATION_REQUESTED: QuestionBranchState.ESCALATED,
        },
        QuestionBranchState.PLAN_DRAFTED: {
            BranchTransitionEvent.OWNER_REVIEW_STARTED: QuestionBranchState.OWNER_REVIEW,
            BranchTransitionEvent.ESCALATION_REQUESTED: QuestionBranchState.ESCALATED,
        },
        QuestionBranchState.OWNER_REVIEW: {
            BranchTransitionEvent.OWNER_REQUESTS_REVISION: (QuestionBranchState.PLANNER_INSPECTING),
            BranchTransitionEvent.OWNER_REJECTS: QuestionBranchState.REJECTED,
            BranchTransitionEvent.OWNER_ACCEPTS: QuestionBranchState.INDEPENDENT_REVIEW,
            BranchTransitionEvent.ESCALATION_REQUESTED: QuestionBranchState.ESCALATED,
        },
        QuestionBranchState.INDEPENDENT_REVIEW: {
            BranchTransitionEvent.REVIEWER_REQUESTS_REVISION: (
                QuestionBranchState.PLANNER_INSPECTING
            ),
            BranchTransitionEvent.REVIEWER_REJECTS: QuestionBranchState.REJECTED,
            BranchTransitionEvent.REVIEWER_ACCEPTS: QuestionBranchState.HUMAN_REVIEW,
            BranchTransitionEvent.ESCALATION_REQUESTED: QuestionBranchState.ESCALATED,
        },
        QuestionBranchState.HUMAN_REVIEW: {
            BranchTransitionEvent.HUMAN_APPROVES: QuestionBranchState.ACCEPTED,
            BranchTransitionEvent.HUMAN_REQUESTS_REVISION: QuestionBranchState.PLANNER_INSPECTING,
            BranchTransitionEvent.HUMAN_REJECTS: QuestionBranchState.REJECTED,
            BranchTransitionEvent.ESCALATION_REQUESTED: QuestionBranchState.ESCALATED,
        },
        QuestionBranchState.ACCEPTED: {
            BranchTransitionEvent.ARCHIVE: QuestionBranchState.ARCHIVED,
        },
        QuestionBranchState.REJECTED: {
            BranchTransitionEvent.ARCHIVE: QuestionBranchState.ARCHIVED,
        },
        QuestionBranchState.ESCALATED: {
            BranchTransitionEvent.ARCHIVE: QuestionBranchState.ARCHIVED,
        },
    }

    @field_validator(
        "branch_id",
        "question_seed_id",
        "context_id",
        "owner_session_id",
        "scientific_intent_invariant_id",
        "scientific_intent_invariant_digest",
        "initial_question_version_id",
        "current_question_version_id",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionBranch identity fields must be non-empty")
        return value

    @field_validator("scientific_intent_invariant_digest")
    @classmethod
    def require_sha256_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError(
                "QuestionBranch scientific_intent_invariant_digest must be a lowercase sha256 hex"
            )
        return value

    @model_validator(mode="after")
    def validate_event_scope(self) -> QuestionBranch:
        sequences = [event.sequence for event in self.events]
        if len(sequences) != len(set(sequences)):
            raise ValueError("QuestionBranch events contain duplicate sequence values")
        expected_sequences = list(range(1, len(self.events) + 1))
        if sorted(sequences) != expected_sequences:
            raise ValueError("QuestionBranch events must use contiguous sequence values")
        for event in self.events:
            if event.branch_id != self.branch_id:
                raise ValueError("QuestionBranch cannot contain event from another branch")
            required_payload_identity = {
                "branch_id": self.branch_id,
                "question_seed_id": self.question_seed_id,
                "context_id": self.context_id,
                "owner_session_id": self.owner_session_id,
                "scientific_intent_invariant_id": self.scientific_intent_invariant_id,
                "scientific_intent_invariant_digest": self.scientific_intent_invariant_digest,
            }
            missing = [key for key in required_payload_identity if key not in event.payload]
            if missing:
                raise ValueError(
                    "QuestionBranch event payload missing identity fields: " + ", ".join(missing)
                )
            mismatched_identity = [
                key
                for key, expected in required_payload_identity.items()
                if key in event.payload and event.payload[key] != expected
            ]
            if mismatched_identity:
                raise ValueError(
                    "QuestionBranch event payload references another "
                    + ", ".join(mismatched_identity)
                )
            found = _find_scope_mismatch(
                event.payload,
                branch_id=self.branch_id,
                question_seed_id=self.question_seed_id,
                context_id=self.context_id,
                owner_session_id=self.owner_session_id,
                scientific_intent_invariant_id=self.scientific_intent_invariant_id,
                scientific_intent_invariant_digest=self.scientific_intent_invariant_digest,
            )
            if found:
                raise ValueError(found)
        replayed_state = self._state_from_events(self.events)
        if replayed_state != self.state:
            raise ValueError("QuestionBranch state does not match replayed event history")
        replayed_material_revision_count = self._material_revision_count_from_events(self.events)
        if replayed_material_revision_count != self.material_revision_count:
            raise ValueError(
                "QuestionBranch material_revision_count does not match replayed event history"
            )
        replayed_dialogue_round_count = self._dialogue_round_count_from_events(self.events)
        if replayed_dialogue_round_count != self.dialogue_round_count:
            raise ValueError(
                "QuestionBranch dialogue_round_count does not match replayed event history"
            )
        replayed_question_version = self._question_version_from_events(self.events)
        expected_question_version = replayed_question_version or self.initial_question_version_id
        if expected_question_version != self.current_question_version_id:
            raise ValueError(
                "QuestionBranch current_question_version_id does not match replayed event history"
            )
        if (
            self.material_revision_count > self.max_material_revisions
            and self.state != QuestionBranchState.ESCALATED
        ):
            raise ValueError("material_revision_count above limit requires escalated state")
        if (
            self.dialogue_round_count > self.max_dialogue_rounds
            and self.state != QuestionBranchState.ESCALATED
        ):
            raise ValueError("dialogue_round_count above limit requires escalated state")
        return self

    @classmethod
    def _state_from_events(cls, events: tuple[QuestionBranchEvent, ...]) -> QuestionBranchState:
        state = QuestionBranchState.PROPOSED
        for event in sorted(events, key=lambda item: item.sequence):
            try:
                transition_event = BranchTransitionEvent(event.event_type)
            except ValueError:
                continue
            allowed = cls.LEGAL_TRANSITIONS.get(state, {})
            if transition_event not in allowed:
                raise ValueError(
                    "QuestionBranch event history contains illegal transition: "
                    f"{state} -> {transition_event}"
                )
            state = allowed[transition_event]
        return state

    @staticmethod
    def _material_revision_count_from_events(events: tuple[QuestionBranchEvent, ...]) -> int:
        return sum(
            int(bool(event.payload.get("material_revision")))
            for event in events
            if event.payload_schema == BranchEventPayloadSchema.QUESTION_REVISION
        )

    @staticmethod
    def _dialogue_round_count_from_events(events: tuple[QuestionBranchEvent, ...]) -> int:
        return sum(
            1 for event in events if event.payload_schema == BranchEventPayloadSchema.DIALOGUE_ROUND
        )

    @staticmethod
    def _question_version_from_events(events: tuple[QuestionBranchEvent, ...]) -> str | None:
        revision_versions = [
            event.payload.get("new_question_version_id")
            for event in sorted(events, key=lambda item: item.sequence)
            if event.payload_schema == BranchEventPayloadSchema.QUESTION_REVISION
        ]
        if not revision_versions:
            return None
        latest = revision_versions[-1]
        return latest if isinstance(latest, str) else None

    def transition(
        self, event_type: BranchTransitionEvent | str, *, event: QuestionBranchEvent
    ) -> QuestionBranch:
        normalized_event = BranchTransitionEvent(event_type)
        next_state = self.next_state(normalized_event)
        if event is None:
            raise ValueError("QuestionBranch transition requires an event")
        if event.event_type != normalized_event.value:
            raise ValueError("QuestionBranch transition event_type does not match requested event")
        if event.sequence != len(self.events) + 1:
            raise ValueError("QuestionBranch transition event sequence must be next contiguous")
        events = (*self.events, event)
        return QuestionBranch.model_validate(
            {
                **self.model_dump(mode="python", exclude={"events", "state"}),
                "state": next_state,
                "events": events,
            }
        )

    def next_state(self, event_type: BranchTransitionEvent | str) -> QuestionBranchState:
        normalized_event = BranchTransitionEvent(event_type)
        allowed = self.LEGAL_TRANSITIONS.get(self.state, {})
        if normalized_event not in allowed:
            raise ValueError(f"Illegal R5 branch transition: {self.state} -> {normalized_event}")
        return allowed[normalized_event]

    def record_question_revision(
        self,
        revision: QuestionRevision,
        *,
        revision_event: QuestionBranchEvent,
        escalation_event: QuestionBranchEvent | None = None,
    ) -> QuestionBranch:
        if revision.branch_id != self.branch_id:
            raise ValueError("QuestionRevision belongs to another branch")
        if revision_event.event_type != BranchRecordEvent.QUESTION_REVISION_RECORDED.value:
            raise ValueError("QuestionRevision record requires question_revision_recorded event")
        if revision_event.sequence != len(self.events) + 1:
            raise ValueError("QuestionRevision record event sequence must be next contiguous")
        if revision_event.payload_schema != BranchEventPayloadSchema.QUESTION_REVISION:
            raise ValueError("QuestionRevision record event requires question_revision/v1 payload")
        if revision_event.payload.get("revision_id") != revision.revision_id:
            raise ValueError("QuestionRevision record event revision_id mismatch")
        if (
            revision_event.payload.get("previous_question_version_id")
            != revision.previous_question_version_id
        ):
            raise ValueError("QuestionRevision record event previous_question_version_id mismatch")
        if (
            revision_event.payload.get("new_question_version_id")
            != revision.new_question_version_id
        ):
            raise ValueError("QuestionRevision record event new_question_version_id mismatch")
        if revision.previous_question_version_id != self.current_question_version_id:
            raise ValueError("QuestionRevision previous_question_version_id must match branch")
        if revision_event.payload.get("material_revision") != revision.assessment.material_revision:
            raise ValueError("QuestionRevision record event material_revision mismatch")
        material_count = self.material_revision_count + int(revision.assessment.material_revision)
        limit_exceeded = material_count > self.max_material_revisions
        if limit_exceeded and escalation_event is None:
            raise ValueError("material revision limit requires escalation event")
        if not limit_exceeded and escalation_event is not None:
            raise ValueError(
                "escalation event is only allowed when material revision limit is exceeded"
            )
        new_events = (*self.events, revision_event)
        if escalation_event is not None:
            if escalation_event.event_type != BranchTransitionEvent.ESCALATION_REQUESTED.value:
                raise ValueError("QuestionRevision escalation event must be escalation_requested")
            if escalation_event.sequence != len(new_events) + 1:
                raise ValueError(
                    "QuestionRevision escalation event sequence must be next contiguous"
                )
            return QuestionBranch.model_validate(
                {
                    **self.model_dump(
                        mode="python",
                        exclude={
                            "current_question_version_id",
                            "material_revision_count",
                            "state",
                            "events",
                        },
                    ),
                    "current_question_version_id": revision.new_question_version_id,
                    "material_revision_count": material_count,
                    "state": QuestionBranchState.ESCALATED,
                    "events": (*new_events, escalation_event),
                }
            )
        updated = QuestionBranch.model_validate(
            {
                **self.model_dump(
                    mode="python",
                    exclude={
                        "current_question_version_id",
                        "material_revision_count",
                        "events",
                    },
                ),
                "current_question_version_id": revision.new_question_version_id,
                "material_revision_count": material_count,
                "events": new_events,
            }
        )
        return updated

    def record_dialogue_round(
        self,
        *,
        dialogue_event: QuestionBranchEvent,
        escalation_event: QuestionBranchEvent | None = None,
    ) -> QuestionBranch:
        if dialogue_event.event_type != BranchRecordEvent.DIALOGUE_ROUND_RECORDED.value:
            raise ValueError("Dialogue round record requires dialogue_round_recorded event")
        if dialogue_event.sequence != len(self.events) + 1:
            raise ValueError("Dialogue round record event sequence must be next contiguous")
        if dialogue_event.payload_schema != BranchEventPayloadSchema.DIALOGUE_ROUND:
            raise ValueError("Dialogue round record event requires dialogue_round/v1 payload")
        round_count = self.dialogue_round_count + 1
        if dialogue_event.payload.get("dialogue_round_count") != round_count:
            raise ValueError("Dialogue round record event dialogue_round_count mismatch")
        limit_exceeded = round_count > self.max_dialogue_rounds
        if limit_exceeded and escalation_event is None:
            raise ValueError("dialogue round limit requires escalation event")
        if not limit_exceeded and escalation_event is not None:
            raise ValueError(
                "escalation event is only allowed when dialogue round limit is exceeded"
            )
        new_events = (*self.events, dialogue_event)
        if escalation_event is not None:
            if escalation_event.event_type != BranchTransitionEvent.ESCALATION_REQUESTED.value:
                raise ValueError("Dialogue round escalation event must be escalation_requested")
            if escalation_event.sequence != len(new_events) + 1:
                raise ValueError("Dialogue round escalation event sequence must be next contiguous")
            return QuestionBranch.model_validate(
                {
                    **self.model_dump(
                        mode="python",
                        exclude={"dialogue_round_count", "state", "events"},
                    ),
                    "dialogue_round_count": round_count,
                    "state": QuestionBranchState.ESCALATED,
                    "events": (*new_events, escalation_event),
                }
            )
        updated = QuestionBranch.model_validate(
            {
                **self.model_dump(mode="python", exclude={"dialogue_round_count", "events"}),
                "dialogue_round_count": round_count,
                "events": new_events,
            }
        )
        return updated


def _find_scope_mismatch(
    value: Any,
    *,
    branch_id: str,
    question_seed_id: str,
    context_id: str,
    owner_session_id: str,
    scientific_intent_invariant_id: str,
    scientific_intent_invariant_digest: str,
) -> str:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key == "branch_id" and nested != branch_id:
                return "QuestionBranch event payload references another branch_id"
            if key == "question_seed_id" and nested != question_seed_id:
                return "QuestionBranch event payload references another question_seed_id"
            if key == "context_id" and nested != context_id:
                return "QuestionBranch event payload references another context_id"
            if key == "owner_session_id" and nested != owner_session_id:
                return "QuestionBranch event payload references another owner_session_id"
            if key == "scientific_intent_invariant_id" and nested != scientific_intent_invariant_id:
                return (
                    "QuestionBranch event payload references another scientific_intent_invariant_id"
                )
            if (
                key == "scientific_intent_invariant_digest"
                and nested != scientific_intent_invariant_digest
            ):
                return (
                    "QuestionBranch event payload references another "
                    "scientific_intent_invariant_digest"
                )
            found = _find_scope_mismatch(
                nested,
                branch_id=branch_id,
                question_seed_id=question_seed_id,
                context_id=context_id,
                owner_session_id=owner_session_id,
                scientific_intent_invariant_id=scientific_intent_invariant_id,
                scientific_intent_invariant_digest=scientific_intent_invariant_digest,
            )
            if found:
                return found
    elif isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for item in value:
            found = _find_scope_mismatch(
                item,
                branch_id=branch_id,
                question_seed_id=question_seed_id,
                context_id=context_id,
                owner_session_id=owner_session_id,
                scientific_intent_invariant_id=scientific_intent_invariant_id,
                scientific_intent_invariant_digest=scientific_intent_invariant_digest,
            )
            if found:
                return found
    return ""
