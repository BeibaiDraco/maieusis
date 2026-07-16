from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from ...io import dump_data, load_model
from ...provenance import stable_hash
from ...schemas.planning_dialogue import (
    BranchActorRole,
    PlanningMessage,
    PlanningMessageBase,
    PlanningMessageScope,
)
from ...schemas.question_branch import branch_event_payload_digest
from ...schemas.question_family import (
    QuestionFamilyIntentInvariant,
    QuestionFamilyShortlistManifest,
    QuestionFamilyVariantDistinctionAxis,
    ShortlistedQuestionFamily,
)
from ...schemas.question_family_branch import (
    QuestionFamilyBranch,
    QuestionFamilyBranchEvent,
    QuestionFamilyBranchEventPayload,
    QuestionFamilyBranchEventScope,
    QuestionFamilyBranchEventType,
    QuestionFamilyBranchState,
    QuestionFamilyInspectionEvidence,
    QuestionFamilyVariantIntentInvariant,
)
from ...schemas.question_seed import QuestionRevision, ScientificIntentInvariant
from .event_store import BranchEventStoreIdentity, FileBackedBranchEventStore


class QuestionFamilyBranchManagerConfig(BaseModel):
    max_dialogue_events: int = 6
    max_family_dialogue_rounds: int = 3
    max_variant_dialogue_rounds: int = 3
    max_material_revisions: int = 2


class DialogueRoundLimitReached(RuntimeError):
    """A planner tried to start another owner-dialogue round after its scoped cap.

    This is a resource boundary, not a scientific disposition.  Callers must stop
    owner dialogue and choose an ordinary plan/reject/escalate terminal from the
    evidence and answers already present on the branch.
    """


class QuestionFamilyBranchManager:
    def __init__(
        self,
        root: str | Path,
        *,
        run_id: str,
        config: QuestionFamilyBranchManagerConfig | None = None,
    ) -> None:
        self.root = Path(root)
        self.run_id = run_id
        self.config = config or QuestionFamilyBranchManagerConfig()

    def create_branch(
        self,
        shortlisted: ShortlistedQuestionFamily,
        *,
        context_id: str,
        owner_session_id: str | None = None,
        branch_id: str | None = None,
    ) -> QuestionFamilyBranch:
        family = shortlisted.family
        resolved_branch_id = branch_id or _branch_id(self.run_id, family.question_family_id)
        resolved_owner_session_id = owner_session_id or _owner_session_id(resolved_branch_id)
        family_invariant = _family_invariant(
            shortlisted=shortlisted,
            owner_session_id=resolved_owner_session_id,
        )
        family_invariant_digest = stable_hash(family_invariant.model_dump(mode="json"))
        variant_invariants = tuple(
            _variant_invariant(
                variant=variant,
                owner_session_id=resolved_owner_session_id,
                branch_id=resolved_branch_id,
            )
            for variant in family.variants
            if variant.variant_id in set(shortlisted.active_variant_ids)
        )
        event = _family_branch_event(
            event_id=_event_id(resolved_branch_id, "shortlist", 1),
            sequence=1,
            branch_id=resolved_branch_id,
            question_family_id=family.question_family_id,
            context_id=context_id,
            owner_session_id=resolved_owner_session_id,
            event_type=QuestionFamilyBranchEventType.SHORTLIST,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=family_invariant.invariant_id,
            family_intent_invariant_digest=family_invariant_digest,
        )
        branch = QuestionFamilyBranch(
            branch_id=resolved_branch_id,
            question_family_id=family.question_family_id,
            context_id=context_id,
            owner_session_id=resolved_owner_session_id,
            family_intent_invariant_id=family_invariant.invariant_id,
            family_intent_invariant_digest=family_invariant_digest,
            family_intent_invariant=family_invariant,
            active_variant_ids=tuple(shortlisted.active_variant_ids),
            variant_intent_invariants=variant_invariants,
            state=QuestionFamilyBranchState.SHORTLISTED,
            events=(event,),
        )
        store = self._store(branch)
        store.append(event)
        self._write_branch_snapshot(branch)
        return branch

    def load_branch(self, branch_id: str) -> QuestionFamilyBranch:
        branch_path = self._branch_path(branch_id)
        branch = load_model(branch_path, QuestionFamilyBranch)
        events = self._store(branch).load_events()
        state = _state_for_event_sequence(events)
        return QuestionFamilyBranch(
            **branch.model_dump(mode="python", exclude={"events", "state"}),
            events=tuple(events),
            state=state,
        )

    def start_planner(self, branch_id: str) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        event = _family_branch_event(
            event_id=_event_id(branch.branch_id, "planner-started", len(branch.events) + 1),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.PLANNER_STARTED,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
        )
        return self._append_event(
            branch, event, next_state=QuestionFamilyBranchState.PLANNER_INSPECTING
        )

    def record_family_context(self, branch_id: str, *, label: str) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        event = _family_branch_event(
            event_id=_event_id(branch.branch_id, label, len(branch.events) + 1),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.FAMILY_CONTEXT_RECORDED,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            planning_message_id=label,
        )
        return self._append_event(
            branch, event, next_state=QuestionFamilyBranchState.PLANNER_INSPECTING
        )

    def record_planner_handoff(
        self,
        branch_id: str,
        *,
        handoff_id: str,
        packet_digest: str,
    ) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        event = _family_branch_event(
            event_id=_event_id(branch.branch_id, handoff_id, len(branch.events) + 1),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.PLANNER_HANDOFF_PREPARED,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            artifact_id=handoff_id,
            artifact_digest=packet_digest,
        )
        return self._append_event(
            branch, event, next_state=QuestionFamilyBranchState.PLANNER_INSPECTING
        )

    def record_planning_message(
        self,
        branch_id: str,
        message: PlanningMessage,
        *,
        event_type: QuestionFamilyBranchEventType | None = None,
    ) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        _validate_message_identity(branch, message)
        if _is_dialogue_round_initiator(message) and _dialogue_round_limit_reached(
            branch, message, self.config
        ):
            raise DialogueRoundLimitReached(
                f"{message.scope.value} dialogue round limit reached; owner dialogue is closed "
                "for this scope, but the branch remains available for an evidence-backed "
                "plan, rejection, or genuine escalation"
            )
        resolved_event_type = event_type or _dialogue_event_type_for_message(message)
        event_scope = _event_scope_for_message(message)
        variant_id = message.variant_id if message.scope == PlanningMessageScope.VARIANT else ""
        event = _family_branch_event(
            event_id=_event_id(branch.branch_id, message.message_id, len(branch.events) + 1),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=resolved_event_type,
            scope=event_scope,
            actor_role=BranchActorRole(message.actor_role),
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            variant_id=variant_id,
            provider_id=message.provider_id,
            model_id=message.model_id,
            session_id=message.session_id,
            prompt_version=message.prompt_version,
            input_digest=message.input_digest,
            output_digest=message.output_digest,
            planning_message_id=message.message_id,
            planning_message_type=message.message_type,
            planning_message_digest=message.payload_digest,
        )
        return self._append_event(
            branch, event, next_state=QuestionFamilyBranchState.PLANNER_INSPECTING
        )

    def dialogue_round_limit_reached(
        self,
        branch_id: str,
        message: PlanningMessage,
    ) -> bool:
        """Return whether ``message`` would consume a forbidden dialogue round.

        Long-running coding-agent hosts use this read-only preflight so they can close
        owner dialogue without mutating scientific branch state or losing returned evidence.
        """

        branch = self.load_branch(branch_id)
        _validate_message_identity(branch, message)
        return _is_dialogue_round_initiator(message) and _dialogue_round_limit_reached(
            branch,
            message,
            self.config,
        )

    def record_inspection_evidence(
        self,
        branch_id: str,
        evidence: QuestionFamilyInspectionEvidence,
        *,
        provider_id: str,
        model_id: str,
        session_id: str,
        prompt_version: str,
        input_digest: str,
        output_digest: str,
    ) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        _validate_evidence_identity(branch, evidence)
        if evidence.evidence_id in {item.evidence_id for item in branch.inspection_evidence}:
            raise ValueError("inspection evidence_id already exists")
        evidence_digest = stable_hash(evidence.model_dump(mode="json"))
        event = _family_branch_event(
            event_id=_event_id(branch.branch_id, evidence.evidence_id, len(branch.events) + 1),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.INSPECTION_EVIDENCE_RECORDED,
            scope=evidence.scope,
            actor_role=BranchActorRole.DATASET_PLANNER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            variant_id=evidence.variant_id,
            provider_id=provider_id,
            model_id=model_id,
            session_id=session_id,
            prompt_version=prompt_version,
            input_digest=input_digest,
            output_digest=output_digest,
            evidence_id=evidence.evidence_id,
            artifact_id=evidence.evidence_id,
            artifact_digest=evidence_digest,
        )
        self._write_inspection_evidence(branch.branch_id, evidence)
        return self._append_event(
            branch,
            event,
            next_state=QuestionFamilyBranchState.PLANNER_INSPECTING,
            inspection_evidence=(*branch.inspection_evidence, evidence),
        )

    def record_question_revision(
        self,
        branch_id: str,
        *,
        variant_id: str,
        revision: QuestionRevision,
    ) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        if not revision.assessment.material_revision:
            return branch
        if not revision.owner_approved:
            raise ValueError("material revision requires owner approval")
        if (
            _material_revision_count(branch, variant_id=variant_id)
            >= self.config.max_material_revisions
        ):
            return self._request_escalation(branch, reason="material revision limit exceeded")
        event = _family_branch_event(
            event_id=_event_id(branch.branch_id, revision.revision_id, len(branch.events) + 1),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.VARIANT_MATERIAL_REVISION,
            scope=QuestionFamilyBranchEventScope.VARIANT,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            variant_id=variant_id,
            revision_id=revision.revision_id,
        )
        return self._append_event(
            branch, event, next_state=QuestionFamilyBranchState.PLANNER_INSPECTING
        )

    def record_closure_candidate(
        self,
        branch_id: str,
        *,
        closure_candidate_id: str,
        artifact_digest: str,
    ) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        event = _family_branch_event(
            event_id=_event_id(
                branch.branch_id,
                closure_candidate_id,
                len(branch.events) + 1,
            ),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.CLOSURE_CANDIDATE_CREATED,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            artifact_id=closure_candidate_id,
            artifact_digest=artifact_digest,
        )
        return self._append_event(branch, event, next_state=QuestionFamilyBranchState.HUMAN_REVIEW)

    def record_human_review_decision(
        self,
        branch_id: str,
        *,
        human_review_import_id: str,
        decision: str,
        artifact_digest: str,
    ) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        event_type, next_state = _human_review_event_and_state(decision)
        event = _family_branch_event(
            event_id=_event_id(
                branch.branch_id,
                human_review_import_id,
                len(branch.events) + 1,
            ),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=event_type,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.HUMAN_EXPERT,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            artifact_id=human_review_import_id,
            artifact_digest=artifact_digest,
        )
        return self._append_event(branch, event, next_state=next_state)

    def record_human_review_gate_correction(
        self,
        branch_id: str,
        *,
        correction_packet_id: str,
        artifact_digest: str,
    ) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        event = _family_branch_event(
            event_id=_event_id(
                branch.branch_id,
                correction_packet_id,
                len(branch.events) + 1,
            ),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.HUMAN_REVIEW_GATE_CORRECTED,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            artifact_id=correction_packet_id,
            artifact_digest=artifact_digest,
        )
        return self._append_event(branch, event, next_state=QuestionFamilyBranchState.HUMAN_REVIEW)

    def record_scientific_dossier_packet_prepared(
        self,
        branch_id: str,
        *,
        dossier_writing_packet_id: str,
        artifact_digest: str,
    ) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        event = _family_branch_event(
            event_id=_event_id(
                branch.branch_id,
                dossier_writing_packet_id,
                len(branch.events) + 1,
            ),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.SCIENTIFIC_DOSSIER_PACKET_PREPARED,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            artifact_id=dossier_writing_packet_id,
            artifact_digest=artifact_digest,
        )
        return self._append_event(branch, event, next_state=QuestionFamilyBranchState.HUMAN_REVIEW)

    def record_scientific_dossier_rendered(
        self,
        branch_id: str,
        *,
        dossier_markdown_artifact_id: str,
        artifact_digest: str,
        provider_id: str,
        model_id: str,
        session_id: str,
        prompt_version: str,
        input_digest: str,
        output_digest: str,
    ) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        event = _family_branch_event(
            event_id=_event_id(
                branch.branch_id,
                dossier_markdown_artifact_id,
                len(branch.events) + 1,
            ),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.SCIENTIFIC_DOSSIER_RENDERED,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            provider_id=provider_id,
            model_id=model_id,
            session_id=session_id,
            prompt_version=prompt_version,
            input_digest=input_digest,
            output_digest=output_digest,
            artifact_id=dossier_markdown_artifact_id,
            artifact_digest=artifact_digest,
        )
        return self._append_event(branch, event, next_state=QuestionFamilyBranchState.HUMAN_REVIEW)

    def record_end_user_scientific_dossier_rendered(
        self,
        branch_id: str,
        *,
        end_user_dossier_artifact_id: str,
        artifact_digest: str,
        provider_id: str,
        model_id: str,
        session_id: str,
        prompt_version: str,
        input_digest: str,
        output_digest: str,
    ) -> QuestionFamilyBranch:
        branch = self.load_branch(branch_id)
        event = _family_branch_event(
            event_id=_event_id(
                branch.branch_id,
                end_user_dossier_artifact_id,
                len(branch.events) + 1,
            ),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.END_USER_SCIENTIFIC_DOSSIER_RENDERED,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
            provider_id=provider_id,
            model_id=model_id,
            session_id=session_id,
            prompt_version=prompt_version,
            input_digest=input_digest,
            output_digest=output_digest,
            artifact_id=end_user_dossier_artifact_id,
            artifact_digest=artifact_digest,
        )
        return self._append_event(branch, event, next_state=QuestionFamilyBranchState.HUMAN_REVIEW)

    def _request_escalation(
        self, branch: QuestionFamilyBranch, *, reason: str
    ) -> QuestionFamilyBranch:
        event = _family_branch_event(
            event_id=_event_id(branch.branch_id, reason, len(branch.events) + 1),
            sequence=len(branch.events) + 1,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            event_type=QuestionFamilyBranchEventType.ESCALATION_REQUESTED,
            scope=QuestionFamilyBranchEventScope.FAMILY,
            actor_role=BranchActorRole.BRANCH_MANAGER,
            family_intent_invariant_id=branch.family_intent_invariant_id,
            family_intent_invariant_digest=branch.family_intent_invariant_digest,
        )
        return self._append_event(branch, event, next_state=QuestionFamilyBranchState.ESCALATED)

    def _append_event(
        self,
        branch: QuestionFamilyBranch,
        event: QuestionFamilyBranchEvent,
        *,
        next_state: QuestionFamilyBranchState,
        inspection_evidence: tuple[QuestionFamilyInspectionEvidence, ...] | None = None,
    ) -> QuestionFamilyBranch:
        updated = QuestionFamilyBranch(
            **branch.model_dump(mode="python", exclude={"events", "state", "inspection_evidence"}),
            events=(*branch.events, event),
            state=next_state,
            inspection_evidence=(
                inspection_evidence
                if inspection_evidence is not None
                else branch.inspection_evidence
            ),
        )
        self._store(branch).append(event)
        self._write_branch_snapshot(updated)
        return updated

    def _store(
        self, branch: QuestionFamilyBranch
    ) -> FileBackedBranchEventStore[QuestionFamilyBranchEvent]:
        return FileBackedBranchEventStore(
            self.root,
            identity=BranchEventStoreIdentity(
                run_id=self.run_id,
                branch_id=branch.branch_id,
                question_family_id=branch.question_family_id,
                context_id=branch.context_id,
                owner_session_id=branch.owner_session_id,
            ),
            event_model=QuestionFamilyBranchEvent,
        )

    def _write_branch_snapshot(self, branch: QuestionFamilyBranch) -> Path:
        return dump_data(branch, self._branch_path(branch.branch_id))

    def _write_inspection_evidence(
        self,
        branch_id: str,
        evidence: QuestionFamilyInspectionEvidence,
    ) -> Path:
        return dump_data(evidence, self._inspection_evidence_path(branch_id, evidence.evidence_id))

    def _branch_path(self, branch_id: str) -> Path:
        return self.root / self.run_id / "branches" / branch_id / "branch.yaml"

    def _inspection_evidence_path(self, branch_id: str, evidence_id: str) -> Path:
        return (
            self.root
            / self.run_id
            / "branches"
            / branch_id
            / "planner"
            / "evidence"
            / f"{evidence_id}.yaml"
        )


def create_branches_from_manifest(
    root: str | Path,
    *,
    run_id: str,
    manifest: QuestionFamilyShortlistManifest,
) -> list[QuestionFamilyBranch]:
    manager = QuestionFamilyBranchManager(root, run_id=run_id)
    return [
        manager.create_branch(shortlisted, context_id=manifest.context_id)
        for shortlisted in manifest.shortlisted
    ]


def _family_invariant(
    *,
    shortlisted: ShortlistedQuestionFamily,
    owner_session_id: str,
) -> QuestionFamilyIntentInvariant:
    family = shortlisted.family
    active_variant_by_id = {
        variant.variant_id: variant
        for variant in family.variants
        if variant.variant_id in set(shortlisted.active_variant_ids)
    }
    axes: list[QuestionFamilyVariantDistinctionAxis] = []
    for variant_id in shortlisted.active_variant_ids:
        for axis in active_variant_by_id[variant_id].distinction_axes:
            if axis not in axes:
                axes.append(axis)
    digest = stable_hash(
        {
            "question_family_id": family.question_family_id,
            "owner_session_id": owner_session_id,
            "active_variant_ids": shortlisted.active_variant_ids,
        }
    )
    return QuestionFamilyIntentInvariant(
        invariant_id=f"qfamily-invariant-{digest[:12]}",
        question_family_id=family.question_family_id,
        shared_phenomenon=family.title,
        shared_theoretical_tension=family.shared_scientific_tension,
        family_claim_boundary=family.summary,
        allowed_variant_axes=axes,
        forbidden_semantic_merges=family.non_mergeable_distinctions,
        owner_session_id=owner_session_id,
    )


def _variant_invariant(
    *,
    variant,
    owner_session_id: str,
    branch_id: str,
) -> QuestionFamilyVariantIntentInvariant:
    seed = variant.seed
    digest = stable_hash(
        {
            "branch_id": branch_id,
            "variant_id": variant.variant_id,
            "question_seed_id": variant.question_seed_id,
        }
    )
    invariant = ScientificIntentInvariant(
        invariant_id=f"variant-invariant-{digest[:12]}",
        question_seed_id=variant.question_seed_id,
        central_phenomenon=seed.question,
        theoretical_tension=seed.scientific_tension,
        target_contrast=variant.distinct_from_siblings,
        intended_claim=seed.novelty_hypothesis,
        discriminating_observation=seed.discriminating_observation,
        population_scope="proposal-stage population scope; exact dataset scope is unresolved",
        positive_result_meaning=seed.positive_result_consequence,
        negative_result_meaning=seed.negative_result_consequence,
        allowed_refinements=seed.ambiguous_constructs + seed.likely_implementation_challenges,
        forbidden_semantic_changes=seed.competing_explanations,
        owner_session_id=owner_session_id,
    )
    return QuestionFamilyVariantIntentInvariant(
        variant_id=variant.variant_id,
        question_seed_id=variant.question_seed_id,
        invariant=invariant,
        distinction_axes=variant.distinction_axes,
    )


def _family_branch_event(
    *,
    event_id: str,
    sequence: int,
    branch_id: str,
    question_family_id: str,
    context_id: str,
    owner_session_id: str,
    event_type: QuestionFamilyBranchEventType,
    scope: QuestionFamilyBranchEventScope,
    actor_role: BranchActorRole,
    family_intent_invariant_id: str,
    family_intent_invariant_digest: str,
    variant_id: str = "",
    provider_id: str = "",
    model_id: str = "",
    session_id: str = "",
    prompt_version: str = "",
    input_digest: str = "",
    output_digest: str = "",
    planning_message_id: str = "",
    planning_message_type: str = "",
    planning_message_digest: str = "",
    revision_id: str = "",
    evidence_id: str = "",
    artifact_id: str = "",
    artifact_digest: str = "",
) -> QuestionFamilyBranchEvent:
    payload = QuestionFamilyBranchEventPayload(
        branch_id=branch_id,
        question_family_id=question_family_id,
        context_id=context_id,
        owner_session_id=owner_session_id,
        event_type=event_type,
        scope=scope,
        family_intent_invariant_id=family_intent_invariant_id,
        family_intent_invariant_digest=family_intent_invariant_digest,
        variant_id=variant_id,
        provider_id=provider_id,
        model_id=model_id,
        session_id=session_id,
        prompt_version=prompt_version,
        input_digest=input_digest,
        output_digest=output_digest,
        planning_message_id=planning_message_id,
        planning_message_type=planning_message_type,
        planning_message_digest=planning_message_digest,
        revision_id=revision_id,
        evidence_id=evidence_id,
        artifact_id=artifact_id,
        artifact_digest=artifact_digest,
    )
    payload_dict = payload.model_dump(mode="json", exclude_defaults=True)
    return QuestionFamilyBranchEvent(
        event_id=event_id,
        branch_id=branch_id,
        question_family_id=question_family_id,
        context_id=context_id,
        owner_session_id=owner_session_id,
        event_type=event_type,
        scope=scope,
        variant_id=variant_id,
        actor_role=actor_role,
        sequence=sequence,
        payload=payload,
        payload_digest=branch_event_payload_digest(payload_dict),
    )


def _human_review_event_and_state(
    decision: str,
) -> tuple[QuestionFamilyBranchEventType, QuestionFamilyBranchState]:
    if decision in {"accept_for_dossier", "accept_with_minor_comments"}:
        return (
            QuestionFamilyBranchEventType.HUMAN_REVIEW_ACCEPTED_FOR_DOSSIER,
            QuestionFamilyBranchState.HUMAN_REVIEW,
        )
    if decision == "revision_required":
        return (
            QuestionFamilyBranchEventType.HUMAN_REVIEW_REVISION_REQUESTED,
            QuestionFamilyBranchState.PLANNER_INSPECTING,
        )
    if decision == "reject":
        return (
            QuestionFamilyBranchEventType.HUMAN_REVIEW_REJECTED,
            QuestionFamilyBranchState.REJECTED,
        )
    if decision == "human_escalation":
        return (
            QuestionFamilyBranchEventType.HUMAN_REVIEW_ESCALATION_REQUESTED,
            QuestionFamilyBranchState.ESCALATED,
        )
    raise ValueError(f"unsupported human review decision: {decision}")


def _state_for_event_sequence(
    events: list[QuestionFamilyBranchEvent],
) -> QuestionFamilyBranchState:
    if not events:
        return QuestionFamilyBranchState.PROPOSED
    last = events[-1].event_type
    if last == QuestionFamilyBranchEventType.SHORTLIST:
        return QuestionFamilyBranchState.SHORTLISTED
    if last == QuestionFamilyBranchEventType.ESCALATION_REQUESTED:
        return QuestionFamilyBranchState.ESCALATED
    if last == QuestionFamilyBranchEventType.ARCHIVE:
        return QuestionFamilyBranchState.ARCHIVED
    if last == QuestionFamilyBranchEventType.CLOSURE_CANDIDATE_CREATED:
        return QuestionFamilyBranchState.HUMAN_REVIEW
    if last == QuestionFamilyBranchEventType.HUMAN_REVIEW_ACCEPTED_FOR_DOSSIER:
        return QuestionFamilyBranchState.HUMAN_REVIEW
    if last == QuestionFamilyBranchEventType.HUMAN_REVIEW_REVISION_REQUESTED:
        return QuestionFamilyBranchState.PLANNER_INSPECTING
    if last == QuestionFamilyBranchEventType.HUMAN_REVIEW_REJECTED:
        return QuestionFamilyBranchState.REJECTED
    if last == QuestionFamilyBranchEventType.HUMAN_REVIEW_ESCALATION_REQUESTED:
        return QuestionFamilyBranchState.ESCALATED
    if last == QuestionFamilyBranchEventType.HUMAN_REVIEW_GATE_CORRECTED:
        return QuestionFamilyBranchState.HUMAN_REVIEW
    if last == QuestionFamilyBranchEventType.SCIENTIFIC_DOSSIER_PACKET_PREPARED:
        return QuestionFamilyBranchState.HUMAN_REVIEW
    if last == QuestionFamilyBranchEventType.SCIENTIFIC_DOSSIER_RENDERED:
        return QuestionFamilyBranchState.HUMAN_REVIEW
    if last == QuestionFamilyBranchEventType.END_USER_SCIENTIFIC_DOSSIER_RENDERED:
        return QuestionFamilyBranchState.HUMAN_REVIEW
    return QuestionFamilyBranchState.PLANNER_INSPECTING


def _branch_id(run_id: str, question_family_id: str) -> str:
    return f"qfamily-branch-{stable_hash({'run_id': run_id, 'family': question_family_id})[:12]}"


def _owner_session_id(branch_id: str) -> str:
    return f"owner-session-{stable_hash({'branch_id': branch_id})[:12]}"


def _event_id(branch_id: str, label: str, sequence: int) -> str:
    return f"event-{stable_hash({'branch_id': branch_id, 'label': label, 'seq': sequence})[:12]}"


def _material_revision_count(branch: QuestionFamilyBranch, *, variant_id: str) -> int:
    return sum(
        event.event_type == QuestionFamilyBranchEventType.VARIANT_MATERIAL_REVISION
        and event.variant_id == variant_id
        for event in branch.events
    )


def _validate_message_identity(branch: QuestionFamilyBranch, message: PlanningMessageBase) -> None:
    if message.branch_id != branch.branch_id:
        raise ValueError("planning message references another branch")
    if message.context_id != branch.context_id:
        raise ValueError("planning message references another context")
    if message.owner_session_id != branch.owner_session_id:
        raise ValueError("planning message references another owner session")
    if message.scope == PlanningMessageScope.FAMILY:
        if message.variant_id or message.question_seed_id:
            raise ValueError("family-scoped planning message cannot reference a variant")
        return
    expected_seed_id = _question_seed_id_for_variant(branch, message.variant_id)
    if message.question_seed_id != expected_seed_id:
        raise ValueError("planning message variant_id/question_seed_id mismatch")


def _validate_evidence_identity(
    branch: QuestionFamilyBranch,
    evidence: QuestionFamilyInspectionEvidence,
) -> None:
    if evidence.branch_id != branch.branch_id:
        raise ValueError("inspection evidence references another branch")
    if evidence.question_family_id != branch.question_family_id:
        raise ValueError("inspection evidence references another family")
    if (
        evidence.scope == QuestionFamilyBranchEventScope.VARIANT
        and evidence.variant_id not in branch.active_variant_ids
    ):
        raise ValueError("inspection evidence references inactive variant")


def _question_seed_id_for_variant(branch: QuestionFamilyBranch, variant_id: str) -> str:
    matches = [
        invariant.question_seed_id
        for invariant in branch.variant_intent_invariants
        if invariant.variant_id == variant_id
    ]
    if len(matches) != 1:
        raise ValueError("planning message does not reference exactly one active branch variant")
    return matches[0]


def _event_scope_for_message(message: PlanningMessageBase) -> QuestionFamilyBranchEventScope:
    if message.scope == PlanningMessageScope.FAMILY:
        return QuestionFamilyBranchEventScope.FAMILY
    return QuestionFamilyBranchEventScope.VARIANT


def _dialogue_event_type_for_message(
    message: PlanningMessageBase,
) -> QuestionFamilyBranchEventType:
    if message.scope == PlanningMessageScope.FAMILY:
        return QuestionFamilyBranchEventType.FAMILY_DIALOGUE_RECORDED
    return QuestionFamilyBranchEventType.VARIANT_DIALOGUE_RECORDED


_DIALOGUE_ROUND_INITIATOR_TYPES = frozenset(
    {
        "clarification_request",
        "operationalization_proposal",
        "family_operationalization_revision_proposal",
    }
)


def _is_dialogue_round_initiator(message: PlanningMessageBase) -> bool:
    return (
        message.actor_role == BranchActorRole.DATASET_PLANNER
        and message.message_type in _DIALOGUE_ROUND_INITIATOR_TYPES
    )


def _dialogue_round_limit_reached(
    branch: QuestionFamilyBranch,
    message: PlanningMessageBase,
    config: QuestionFamilyBranchManagerConfig,
) -> bool:
    if message.scope == PlanningMessageScope.FAMILY:
        return (
            _dialogue_round_count(branch, scope=PlanningMessageScope.FAMILY)
            >= config.max_family_dialogue_rounds
        )
    return (
        _dialogue_round_count(
            branch,
            scope=PlanningMessageScope.VARIANT,
            variant_id=message.variant_id,
        )
        >= config.max_variant_dialogue_rounds
    )


def _dialogue_round_count(
    branch: QuestionFamilyBranch,
    *,
    scope: PlanningMessageScope,
    variant_id: str = "",
) -> int:
    expected_event_type = (
        QuestionFamilyBranchEventType.FAMILY_DIALOGUE_RECORDED
        if scope == PlanningMessageScope.FAMILY
        else QuestionFamilyBranchEventType.VARIANT_DIALOGUE_RECORDED
    )
    return sum(
        event.event_type == expected_event_type
        and (scope == PlanningMessageScope.FAMILY or event.variant_id == variant_id)
        and event.actor_role == BranchActorRole.DATASET_PLANNER
        and event.payload.planning_message_type in _DIALOGUE_ROUND_INITIATOR_TYPES
        for event in branch.events
    )
