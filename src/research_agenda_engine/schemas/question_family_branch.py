from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..provenance import stable_hash
from .analysis_plan import DatasetInspectionSourceType
from .generic_scientific_source import DatasetClaimStatus
from .planning_dialogue import BranchActorRole, BranchDecisionKind
from .question_branch import branch_event_payload_digest
from .question_family import (
    QuestionFamilyClosurePackage,
    QuestionFamilyIntentInvariant,
    QuestionFamilyVariantDistinctionAxis,
)
from .question_seed import ScientificIntentInvariant


class QuestionFamilyBranchState(StrEnum):
    PROPOSED = "proposed"
    SHORTLISTED = "shortlisted"
    PLANNER_INSPECTING = "planner_inspecting"
    OWNER_REVIEW = "owner_review"
    INDEPENDENT_REVIEW = "independent_review"
    HUMAN_REVIEW = "human_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    ARCHIVED = "archived"


class QuestionFamilyBranchEventScope(StrEnum):
    FAMILY = "family"
    VARIANT = "variant"


class QuestionFamilyBranchEventType(StrEnum):
    SHORTLIST = "shortlist"
    PLANNER_STARTED = "planner_started"
    FAMILY_CONTEXT_RECORDED = "family_context_recorded"
    PLANNER_HANDOFF_PREPARED = "planner_handoff_prepared"
    FAMILY_DIALOGUE_RECORDED = "family_dialogue_recorded"
    VARIANT_DIALOGUE_RECORDED = "variant_dialogue_recorded"
    VARIANT_EVIDENCE_RECORDED = "variant_evidence_recorded"
    INSPECTION_EVIDENCE_RECORDED = "inspection_evidence_recorded"
    VARIANT_MATERIAL_REVISION = "variant_material_revision"
    CLOSURE_CANDIDATE_CREATED = "closure_candidate_created"
    HUMAN_REVIEW_ACCEPTED_FOR_DOSSIER = "human_review_accepted_for_dossier"
    HUMAN_REVIEW_REVISION_REQUESTED = "human_review_revision_requested"
    HUMAN_REVIEW_REJECTED = "human_review_rejected"
    HUMAN_REVIEW_ESCALATION_REQUESTED = "human_review_escalation_requested"
    HUMAN_REVIEW_GATE_CORRECTED = "human_review_gate_corrected"
    SCIENTIFIC_DOSSIER_PACKET_PREPARED = "scientific_dossier_packet_prepared"
    SCIENTIFIC_DOSSIER_RENDERED = "scientific_dossier_rendered"
    END_USER_SCIENTIFIC_DOSSIER_RENDERED = "end_user_scientific_dossier_rendered"
    CLOSURE_RECORDED = "closure_recorded"
    ESCALATION_REQUESTED = "escalation_requested"
    ARCHIVE = "archive"


class QuestionFamilyVariantIntentInvariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    invariant: ScientificIntentInvariant
    distinction_axes: list[QuestionFamilyVariantDistinctionAxis] = Field(default_factory=list)

    @field_validator("variant_id", "question_seed_id")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("variant intent invariant identity fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_variant_invariant(self) -> QuestionFamilyVariantIntentInvariant:
        if self.question_seed_id != self.invariant.question_seed_id:
            raise ValueError(
                "variant intent invariant question_seed_id must match nested invariant"
            )
        if not self.distinction_axes:
            raise ValueError("variant intent invariant requires distinction_axes")
        return self


class QuestionFamilyBranchEventPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    event_type: QuestionFamilyBranchEventType
    scope: QuestionFamilyBranchEventScope
    family_intent_invariant_id: str
    family_intent_invariant_digest: str
    variant_id: str = ""
    provider_id: str = ""
    model_id: str = ""
    session_id: str = ""
    prompt_version: str = ""
    input_digest: str = ""
    output_digest: str = ""
    planning_message_id: str = ""
    planning_message_type: str = ""
    planning_message_digest: str = ""
    revision_id: str = ""
    evidence_id: str = ""
    artifact_id: str = ""
    artifact_digest: str = ""

    @field_validator(
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "family_intent_invariant_id",
        "family_intent_invariant_digest",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionFamilyBranchEvent payload identity fields must be non-empty")
        return value

    @field_validator(
        "family_intent_invariant_digest",
        "input_digest",
        "output_digest",
        "planning_message_digest",
        "artifact_digest",
    )
    @classmethod
    def validate_optional_digest(cls, value: str) -> str:
        if value and (len(value) != 64 or any(char not in "0123456789abcdef" for char in value)):
            raise ValueError("QuestionFamilyBranchEvent payload digest fields must be sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_payload_scope(self) -> QuestionFamilyBranchEventPayload:
        if self.scope == QuestionFamilyBranchEventScope.VARIANT and not self.variant_id.strip():
            raise ValueError("variant-scoped family branch event payload requires variant_id")
        if self.scope == QuestionFamilyBranchEventScope.FAMILY and self.variant_id.strip():
            raise ValueError("family-scoped family branch event payload cannot carry variant_id")
        return self


class QuestionFamilyBranchEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    event_type: QuestionFamilyBranchEventType
    scope: QuestionFamilyBranchEventScope
    variant_id: str = ""
    actor_role: BranchActorRole
    sequence: int = Field(ge=1)
    payload: QuestionFamilyBranchEventPayload
    payload_digest: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "event_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "payload_digest",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionFamilyBranchEvent identity fields must be non-empty")
        return value

    @field_validator("payload_digest")
    @classmethod
    def require_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("QuestionFamilyBranchEvent payload_digest must be sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_scope_and_identity(self) -> QuestionFamilyBranchEvent:
        payload_dict = self.payload.model_dump(mode="json", exclude_defaults=True)
        if self.payload_digest != branch_event_payload_digest(payload_dict):
            raise ValueError("QuestionFamilyBranchEvent payload_digest does not match payload")
        if self.scope == QuestionFamilyBranchEventScope.VARIANT and not self.variant_id.strip():
            raise ValueError("variant-scoped family branch event requires variant_id")
        if self.scope == QuestionFamilyBranchEventScope.FAMILY and self.variant_id.strip():
            raise ValueError("family-scoped branch event cannot carry variant_id")
        expected = {
            "branch_id": self.branch_id,
            "question_family_id": self.question_family_id,
            "context_id": self.context_id,
            "owner_session_id": self.owner_session_id,
            "event_type": self.event_type,
            "scope": self.scope,
        }
        if self.scope == QuestionFamilyBranchEventScope.VARIANT:
            expected["variant_id"] = self.variant_id
        mismatched = [key for key, value in expected.items() if getattr(self.payload, key) != value]
        if mismatched:
            raise ValueError(
                "QuestionFamilyBranchEvent payload references another " + ", ".join(mismatched)
            )
        if self.actor_role not in {BranchActorRole.BRANCH_MANAGER, BranchActorRole.HUMAN_EXPERT}:
            required_agent_fields = {
                "provider_id": self.payload.provider_id,
                "model_id": self.payload.model_id,
                "session_id": self.payload.session_id,
                "prompt_version": self.payload.prompt_version,
                "input_digest": self.payload.input_digest,
                "output_digest": self.payload.output_digest,
            }
            missing_agent_fields = [
                key for key, value in required_agent_fields.items() if not value.strip()
            ]
            if missing_agent_fields:
                raise ValueError(
                    "agent-originated family branch event missing provenance: "
                    + ", ".join(missing_agent_fields)
                )
        return self


class QuestionFamilyInspectionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    branch_id: str
    question_family_id: str
    scope: QuestionFamilyBranchEventScope
    variant_id: str = ""
    source_type: DatasetInspectionSourceType
    source_locator: str
    source_digest: str
    inspection_method: str
    finding: str
    limitations: list[str] = Field(default_factory=list)
    created_by: str
    query_or_command_digest: str = ""
    result_digest: str = ""
    dataset_claim_status: DatasetClaimStatus = DatasetClaimStatus.UNVERIFIED
    host_binding_digest: str = ""
    row_limit: int | None = Field(default=None, ge=0)
    sample_limit: int | None = Field(default=None, ge=0)
    online_source_accessed_at: datetime | None = None
    planning_only: bool = True
    confirmation_firewall_checked: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_evidence_scope(self) -> QuestionFamilyInspectionEvidence:
        if not self.evidence_id.strip():
            raise ValueError("QuestionFamilyInspectionEvidence requires evidence_id")
        if not self.branch_id.strip() or not self.question_family_id.strip():
            raise ValueError("QuestionFamilyInspectionEvidence requires branch/family identity")
        if len(self.source_digest) != 64 or any(
            char not in "0123456789abcdef" for char in self.source_digest
        ):
            raise ValueError("QuestionFamilyInspectionEvidence source_digest must be sha256 hex")
        for field_name, digest in {
            "query_or_command_digest": self.query_or_command_digest,
            "result_digest": self.result_digest,
            "host_binding_digest": self.host_binding_digest,
        }.items():
            if digest and (
                len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest)
            ):
                raise ValueError(
                    f"QuestionFamilyInspectionEvidence {field_name} must be sha256 hex"
                )
        if self.dataset_claim_status == DatasetClaimStatus.VERIFIED:
            if not self.host_binding_digest:
                raise ValueError("verified inspection evidence requires host_binding_digest")
        elif self.host_binding_digest:
            raise ValueError("only verified inspection evidence may carry host_binding_digest")
        if self.scope == QuestionFamilyBranchEventScope.VARIANT and not self.variant_id.strip():
            raise ValueError("variant-scoped family evidence requires variant_id")
        if self.scope == QuestionFamilyBranchEventScope.FAMILY and self.variant_id.strip():
            raise ValueError("family-scoped evidence cannot carry variant_id")
        is_online = self.source_locator.startswith(("http://", "https://"))
        if is_online:
            missing = []
            if self.online_source_accessed_at is None:
                missing.append("online_source_accessed_at")
            if not self.query_or_command_digest:
                missing.append("query_or_command_digest")
            if not self.result_digest:
                missing.append("result_digest")
            if missing:
                raise ValueError(
                    "online QuestionFamilyInspectionEvidence requires " + ", ".join(missing)
                )
        if not self.planning_only:
            raise ValueError("QuestionFamilyInspectionEvidence must remain planning_only")
        if not self.confirmation_firewall_checked:
            raise ValueError(
                "QuestionFamilyInspectionEvidence requires confirmation_firewall_checked"
            )
        return self

    def can_support_variant(self, variant_id: str) -> bool:
        if self.scope == QuestionFamilyBranchEventScope.FAMILY:
            return True
        return self.variant_id == variant_id


#: Fields excluded from an inspection evidence record's IDENTITY, because the host stamps them and a
#: re-read of the same planner file cannot reproduce them.
_EVIDENCE_IDENTITY_EXCLUDED_FIELDS: frozenset[str] = frozenset({"created_at"})


def inspection_evidence_identity_digest(evidence: QuestionFamilyInspectionEvidence) -> str:
    """Canonical "is this the same evidence?" digest — everything scientific, minus ``created_at``.

    A replan re-reads the planner's own evidence files while the branch already holds the copies
    round 0 recorded, so the same evidence is loaded twice and compared. ``created_at`` carries
    ``default_factory=datetime.now``, and the planner-authored file omits the field, so the second
    reading stamps LOAD time: on the three families this killed, the round-0 copies read
    ``2026-08-12T01:13:47Z`` and the re-reads of the very same files read ``2026-08-13T00:46:10Z``.
    Measured across all ten conflicting ids in those three branches, ``created_at`` was the ONLY
    differing field — no finding, source digest, method or limitation differed anywhere.

    So a full-model comparison answers a question nobody asked. This answers the real one: two
    records share an id and describe the same inspection. Every scientific and provenance field
    stays in the digest, so a planner that changes a finding, a source digest or a limitation under
    an id it already used is still a conflict, and still fails closed.
    """
    return stable_hash(
        evidence.model_dump(mode="json", exclude=set(_EVIDENCE_IDENTITY_EXCLUDED_FIELDS))
    )


class QuestionFamilyBranch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    family_intent_invariant_id: str
    family_intent_invariant_digest: str
    family_intent_invariant: QuestionFamilyIntentInvariant
    active_variant_ids: tuple[str, ...] = Field(default_factory=tuple)
    variant_intent_invariants: tuple[QuestionFamilyVariantIntentInvariant, ...] = Field(
        default_factory=tuple
    )
    state: QuestionFamilyBranchState = QuestionFamilyBranchState.PROPOSED
    events: tuple[QuestionFamilyBranchEvent, ...] = Field(default_factory=tuple)
    inspection_evidence: tuple[QuestionFamilyInspectionEvidence, ...] = Field(default_factory=tuple)
    closure: QuestionFamilyClosurePackage | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "family_intent_invariant_id",
        "family_intent_invariant_digest",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("QuestionFamilyBranch identity fields must be non-empty")
        return value

    @field_validator("family_intent_invariant_digest")
    @classmethod
    def require_sha256_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("QuestionFamilyBranch invariant digest must be sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_family_branch(self) -> QuestionFamilyBranch:
        if len(self.active_variant_ids) != len(set(self.active_variant_ids)):
            raise ValueError("QuestionFamilyBranch contains duplicate active_variant_ids")
        if not self.active_variant_ids:
            raise ValueError("QuestionFamilyBranch requires active_variant_ids")
        if self.family_intent_invariant_id != self.family_intent_invariant.invariant_id:
            raise ValueError("family invariant ID does not match nested invariant")
        if self.family_intent_invariant.question_family_id != self.question_family_id:
            raise ValueError("family invariant references another question_family_id")
        if self.family_intent_invariant.owner_session_id != self.owner_session_id:
            raise ValueError("family invariant references another owner_session_id")
        expected_family_digest = stable_hash(self.family_intent_invariant.model_dump(mode="json"))
        if self.family_intent_invariant_digest != expected_family_digest:
            raise ValueError("family invariant digest does not match nested invariant")
        variant_ids = [
            variant_invariant.variant_id for variant_invariant in self.variant_intent_invariants
        ]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValueError("QuestionFamilyBranch contains duplicate variant invariants")
        missing_variant_invariants = sorted(set(self.active_variant_ids) - set(variant_ids))
        if missing_variant_invariants:
            raise ValueError(
                "QuestionFamilyBranch missing variant invariants: "
                + ", ".join(missing_variant_invariants)
            )
        extra_variant_invariants = sorted(set(variant_ids) - set(self.active_variant_ids))
        if extra_variant_invariants:
            raise ValueError(
                "QuestionFamilyBranch contains non-active variant invariants: "
                + ", ".join(extra_variant_invariants)
            )
        for variant_invariant in self.variant_intent_invariants:
            if variant_invariant.invariant.owner_session_id != self.owner_session_id:
                raise ValueError("variant invariant references another owner_session_id")
        sequences = [event.sequence for event in self.events]
        if sequences != list(range(1, len(sequences) + 1)):
            raise ValueError("QuestionFamilyBranch events must use contiguous sequences")
        for event in self.events:
            if event.branch_id != self.branch_id:
                raise ValueError("QuestionFamilyBranch contains event from another branch")
            if event.question_family_id != self.question_family_id:
                raise ValueError("QuestionFamilyBranch contains event from another family")
            if event.context_id != self.context_id:
                raise ValueError("QuestionFamilyBranch contains event from another context")
            if event.owner_session_id != self.owner_session_id:
                raise ValueError("QuestionFamilyBranch contains event from another owner session")
            if (
                event.scope == QuestionFamilyBranchEventScope.VARIANT
                and event.variant_id not in self.active_variant_ids
            ):
                raise ValueError("QuestionFamilyBranch event references inactive variant")
            if event.payload.family_intent_invariant_id != self.family_intent_invariant_id:
                raise ValueError("QuestionFamilyBranch event references another family invariant")
            if event.payload.family_intent_invariant_digest != self.family_intent_invariant_digest:
                raise ValueError("QuestionFamilyBranch event references another invariant digest")
        evidence_by_id = {evidence.evidence_id: evidence for evidence in self.inspection_evidence}
        if len(evidence_by_id) != len(self.inspection_evidence):
            raise ValueError("QuestionFamilyBranch contains duplicate inspection evidence IDs")
        for evidence in self.inspection_evidence:
            if evidence.branch_id != self.branch_id:
                raise ValueError("QuestionFamilyBranch contains evidence from another branch")
            if evidence.question_family_id != self.question_family_id:
                raise ValueError("QuestionFamilyBranch contains evidence from another family")
            if (
                evidence.scope == QuestionFamilyBranchEventScope.VARIANT
                and evidence.variant_id not in self.active_variant_ids
            ):
                raise ValueError("QuestionFamilyBranch evidence references inactive variant")
        derived_state = self._derive_state_from_events()
        if self.state != derived_state:
            raise ValueError(
                "QuestionFamilyBranch state must be derived from events; expected "
                + derived_state.value
            )
        has_closure_event = any(
            event.event_type == QuestionFamilyBranchEventType.CLOSURE_RECORDED
            for event in self.events
        )
        if has_closure_event and self.closure is None:
            raise ValueError("QuestionFamilyBranch closure event requires closure package")
        if self.closure is not None and not has_closure_event:
            raise ValueError("QuestionFamilyBranch closure package requires closure event")
        if self.closure is not None:
            if self.closure.branch_id != self.branch_id:
                raise ValueError("QuestionFamilyBranch closure references another branch")
            if self.closure.question_family_id != self.question_family_id:
                raise ValueError("QuestionFamilyBranch closure references another family")
            if set(self.closure.active_variant_ids) != set(self.active_variant_ids):
                raise ValueError("QuestionFamilyBranch closure active variants mismatch")
            revised_variant_ids = {
                event.variant_id
                for event in self.events
                if event.event_type == QuestionFamilyBranchEventType.VARIANT_MATERIAL_REVISION
            }
            missing_rechecks = sorted(
                closure.variant_id
                for closure in self.closure.variant_closures
                if closure.variant_id in revised_variant_ids
                and not closure.novelty_recheck_required
            )
            if missing_rechecks:
                raise ValueError(
                    "materially revised family variants require novelty recheck: "
                    + ", ".join(missing_rechecks)
                )
            incomplete_accepted_rechecks = sorted(
                closure.variant_id
                for closure in self.closure.variant_closures
                if closure.variant_id in revised_variant_ids
                and closure.decision.is_accepted
                and (
                    not closure.novelty_recheck_completed
                    or not closure.novelty_recheck_artifact_ids
                )
            )
            if incomplete_accepted_rechecks:
                raise ValueError(
                    "accepted materially revised variants require completed novelty recheck: "
                    + ", ".join(incomplete_accepted_rechecks)
                )
            unsupported_evidence = sorted(
                closure.variant_id
                for closure in self.closure.variant_closures
                if closure.decision.is_accepted
                for evidence_id in closure.evidence_ids
                if evidence_id not in evidence_by_id
                or not evidence_by_id[evidence_id].can_support_variant(closure.variant_id)
            )
            if unsupported_evidence:
                raise ValueError(
                    "accepted variant closures require branch-local support evidence: "
                    + ", ".join(unsupported_evidence)
                )
        return self

    def _derive_state_from_events(self) -> QuestionFamilyBranchState:
        state = QuestionFamilyBranchState.PROPOSED
        for event in self.events:
            if state in {
                QuestionFamilyBranchState.ACCEPTED,
                QuestionFamilyBranchState.REJECTED,
                QuestionFamilyBranchState.ESCALATED,
                QuestionFamilyBranchState.ARCHIVED,
            }:
                if event.event_type == QuestionFamilyBranchEventType.ARCHIVE and (
                    state != QuestionFamilyBranchState.ARCHIVED
                ):
                    state = QuestionFamilyBranchState.ARCHIVED
                    continue
                raise ValueError("QuestionFamilyBranch terminal state cannot accept more events")
            if event.event_type == QuestionFamilyBranchEventType.SHORTLIST:
                if state != QuestionFamilyBranchState.PROPOSED:
                    raise ValueError("QuestionFamilyBranch illegal shortlist transition")
                state = QuestionFamilyBranchState.SHORTLISTED
            elif event.event_type == QuestionFamilyBranchEventType.PLANNER_STARTED:
                if state != QuestionFamilyBranchState.SHORTLISTED:
                    raise ValueError("QuestionFamilyBranch illegal planner_started transition")
                state = QuestionFamilyBranchState.PLANNER_INSPECTING
            elif event.event_type in {
                QuestionFamilyBranchEventType.FAMILY_CONTEXT_RECORDED,
                QuestionFamilyBranchEventType.PLANNER_HANDOFF_PREPARED,
                QuestionFamilyBranchEventType.FAMILY_DIALOGUE_RECORDED,
                QuestionFamilyBranchEventType.VARIANT_DIALOGUE_RECORDED,
                QuestionFamilyBranchEventType.VARIANT_EVIDENCE_RECORDED,
                QuestionFamilyBranchEventType.INSPECTION_EVIDENCE_RECORDED,
                QuestionFamilyBranchEventType.VARIANT_MATERIAL_REVISION,
            }:
                if state == QuestionFamilyBranchState.HUMAN_REVIEW and (
                    event.event_type == QuestionFamilyBranchEventType.FAMILY_DIALOGUE_RECORDED
                    and event.payload.planning_message_type
                    == "family_method_specification_proposal"
                ):
                    state = QuestionFamilyBranchState.PLANNER_INSPECTING
                    continue
                if state != QuestionFamilyBranchState.PLANNER_INSPECTING:
                    raise ValueError(
                        "QuestionFamilyBranch planning records require planner_started"
                    )
            elif event.event_type == QuestionFamilyBranchEventType.CLOSURE_CANDIDATE_CREATED:
                if state != QuestionFamilyBranchState.PLANNER_INSPECTING:
                    raise ValueError(
                        "QuestionFamilyBranch closure candidate requires planner_started"
                    )
                if self.closure is not None:
                    raise ValueError(
                        "QuestionFamilyBranch closure candidate cannot carry final closure"
                    )
                state = QuestionFamilyBranchState.HUMAN_REVIEW
            elif event.event_type == (
                QuestionFamilyBranchEventType.HUMAN_REVIEW_ACCEPTED_FOR_DOSSIER
            ):
                if state not in {
                    QuestionFamilyBranchState.HUMAN_REVIEW,
                    QuestionFamilyBranchState.PLANNER_INSPECTING,
                }:
                    raise ValueError("QuestionFamilyBranch human review import requires review")
                state = QuestionFamilyBranchState.HUMAN_REVIEW
            elif event.event_type == QuestionFamilyBranchEventType.HUMAN_REVIEW_REVISION_REQUESTED:
                if state not in {
                    QuestionFamilyBranchState.HUMAN_REVIEW,
                    QuestionFamilyBranchState.PLANNER_INSPECTING,
                }:
                    raise ValueError("QuestionFamilyBranch human review revision requires review")
                state = QuestionFamilyBranchState.PLANNER_INSPECTING
            elif event.event_type == QuestionFamilyBranchEventType.HUMAN_REVIEW_REJECTED:
                if state not in {
                    QuestionFamilyBranchState.HUMAN_REVIEW,
                    QuestionFamilyBranchState.PLANNER_INSPECTING,
                }:
                    raise ValueError("QuestionFamilyBranch human review rejection requires review")
                state = QuestionFamilyBranchState.REJECTED
            elif event.event_type == (
                QuestionFamilyBranchEventType.HUMAN_REVIEW_ESCALATION_REQUESTED
            ):
                if state not in {
                    QuestionFamilyBranchState.HUMAN_REVIEW,
                    QuestionFamilyBranchState.PLANNER_INSPECTING,
                }:
                    raise ValueError("QuestionFamilyBranch human review escalation requires review")
                state = QuestionFamilyBranchState.ESCALATED
            elif event.event_type == (
                QuestionFamilyBranchEventType.SCIENTIFIC_DOSSIER_PACKET_PREPARED
            ):
                if state != QuestionFamilyBranchState.HUMAN_REVIEW and not (
                    state == QuestionFamilyBranchState.PLANNER_INSPECTING
                    and event.payload.artifact_id.startswith("generic-dossier-writing-packet-")
                ):
                    raise ValueError(
                        "QuestionFamilyBranch dossier packet preparation requires human review"
                    )
                if self.closure is not None:
                    raise ValueError(
                        "QuestionFamilyBranch dossier packet preparation cannot carry closure"
                    )
                state = QuestionFamilyBranchState.HUMAN_REVIEW
            elif event.event_type == QuestionFamilyBranchEventType.SCIENTIFIC_DOSSIER_RENDERED:
                if state != QuestionFamilyBranchState.HUMAN_REVIEW:
                    raise ValueError("QuestionFamilyBranch dossier rendering requires human review")
                if self.closure is not None:
                    raise ValueError("QuestionFamilyBranch dossier rendering cannot carry closure")
                state = QuestionFamilyBranchState.HUMAN_REVIEW
            elif event.event_type == (
                QuestionFamilyBranchEventType.END_USER_SCIENTIFIC_DOSSIER_RENDERED
            ):
                if state != QuestionFamilyBranchState.HUMAN_REVIEW:
                    raise ValueError(
                        "QuestionFamilyBranch end-user dossier rendering requires human review"
                    )
                if self.closure is not None:
                    raise ValueError(
                        "QuestionFamilyBranch end-user dossier rendering cannot carry closure"
                    )
                state = QuestionFamilyBranchState.HUMAN_REVIEW
            elif event.event_type == QuestionFamilyBranchEventType.ESCALATION_REQUESTED:
                state = QuestionFamilyBranchState.ESCALATED
            elif event.event_type == QuestionFamilyBranchEventType.ARCHIVE:
                state = QuestionFamilyBranchState.ARCHIVED
            elif event.event_type == QuestionFamilyBranchEventType.CLOSURE_RECORDED:
                if state not in {
                    QuestionFamilyBranchState.PLANNER_INSPECTING,
                    QuestionFamilyBranchState.HUMAN_REVIEW,
                }:
                    raise ValueError("QuestionFamilyBranch closure requires planner_started")
                if self.closure is None:
                    raise ValueError("QuestionFamilyBranch closure event requires closure package")
                state = self._derive_terminal_state_from_closure()
        return state

    def _derive_terminal_state_from_closure(self) -> QuestionFamilyBranchState:
        if self.closure is None:
            raise ValueError("QuestionFamilyBranch closure package is required")
        decisions = [closure.decision for closure in self.closure.variant_closures]
        if any(decision == BranchDecisionKind.HUMAN_ESCALATION for decision in decisions):
            return QuestionFamilyBranchState.ESCALATED
        if any(decision.is_accepted for decision in decisions):
            return QuestionFamilyBranchState.ACCEPTED
        return QuestionFamilyBranchState.REJECTED
