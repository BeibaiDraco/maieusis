from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

from ...io import load_model
from ...provenance import stable_hash
from ...schemas.planner_probe import ConstructProbeMap
from ...schemas.planning_dialogue import (
    BranchRejectionMessage,
    DatasetFeasibilityFinding,
    HumanEscalationRequest,
    PlanDraftMessage,
    PlanningMessage,
    PlanRevisionContext,
)
from ...schemas.planning_policy import FullLocalDataPlanningPolicy
from ...schemas.question_family_branch import (
    QuestionFamilyBranch,
    QuestionFamilyBranchEventScope,
    QuestionFamilyBranchState,
    QuestionFamilyInspectionEvidence,
)
from .construct_probe_validation import validate_construct_probe_maps
from .direct_file_artifact_contract import DIRECT_FILE_FORBIDDEN_ENVELOPE_KEYS
from .evidence_claims import require_planner_evidence_unverified
from .guards import (
    FORBIDDEN_PLANNER_OUTPUT_TERMS as FORBIDDEN_PLANNER_OUTPUT_TERMS,
)
from .planner_boundaries import (
    find_planner_boundary_violations,
    planner_language_warnings,
)

DATASET_PLANNER_PROMPT_VERSION = "dataset_planner/v2"
DATASET_PLANNER_PACKET_VERSION = "dataset_planner_task_packet/v1"

SCIENTIFIC_DIALOGUE_TOOL_NAMES = (
    "branch_get_context",
    "branch_get_state",
    "branch_record_inspection_evidence",
    "branch_submit_clarification_request",
    "branch_ask_question_owner",
    "branch_submit_operationalization",
    "branch_submit_feasibility_finding",
    "branch_submit_plan_draft",
    "branch_submit_rejection",
    "branch_request_human_review",
)

_PLANNING_MESSAGE_ADAPTER: TypeAdapter[Any] = TypeAdapter(PlanningMessage)


class PlannerHandoffStatus(StrEnum):
    PREPARED = "prepared"
    RETURNED_VALID = "returned_valid"
    RETURNED_INVALID = "returned_invalid"


class PlannerPathPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    planner_workspace: str
    evidence_dir: str
    dialogue_dir: str
    plan_draft_path: str
    rejection_path: str
    validation_report_path: str

    @model_validator(mode="after")
    def validate_branch_local_paths(self) -> PlannerPathPolicy:
        paths = [
            self.planner_workspace,
            self.evidence_dir,
            self.dialogue_dir,
            self.plan_draft_path,
            self.rejection_path,
            self.validation_report_path,
        ]
        root = Path(self.planner_workspace).resolve()
        for value in paths:
            path = Path(value).resolve()
            if path != root and root not in path.parents:
                raise ValueError("planner output paths must remain under planner_workspace")
        return self


class PlannerPermissionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    write_policy: str
    allowed_inspection_modes: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    online_query_rules: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_planning_only_boundaries(self) -> PlannerPermissionPolicy:
        if "branch planning artifacts only" not in self.write_policy.lower():
            raise ValueError("planner write policy must be branch planning artifacts only")
        if not self.allowed_inspection_modes or not self.forbidden_actions:
            raise ValueError("planner permission policy requires allowed and forbidden actions")
        return self


class MetadataValueProbePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    authorized: bool = False
    semantic_alias_discovery_required: bool = True
    allowed_sources: list[str] = Field(default_factory=list)
    allowed_summaries: list[str] = Field(default_factory=list)
    forbidden_outputs: list[str] = Field(default_factory=list)
    redaction_required: bool = True

    @model_validator(mode="after")
    def validate_authorized_probe_scope(self) -> MetadataValueProbePolicy:
        if self.authorized:
            if not self.semantic_alias_discovery_required:
                raise ValueError(
                    "authorized metadata-value probe requires semantic alias discovery"
                )
            if not self.allowed_sources or not self.allowed_summaries or not self.forbidden_outputs:
                raise ValueError("authorized metadata-value probe requires explicit scope")
            if not self.redaction_required:
                raise ValueError("authorized metadata-value probe requires redaction")
        return self


class ScientificDialogueToolConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server_module: str
    run_id: str
    branch_id: str
    branch_token: str
    tools: list[str]

    @model_validator(mode="after")
    def require_known_tools(self) -> ScientificDialogueToolConfig:
        if set(self.tools) != set(SCIENTIFIC_DIALOGUE_TOOL_NAMES):
            raise ValueError("scientific dialogue tool config must include exactly known tools")
        return self


class DatasetInspectionResources(BaseModel):
    """Per-dataset planner inspection resources injected into a handoff packet.

    The packet fields (``allowed_inspection_resources`` / ``official_online_resources``) are
    generic; only their VALUES are dataset-coupled. This model carries those values as an
    injected input so the handoff backend hardcodes nothing dataset-specific. The generic
    default (``generic_inspection_resources``) carries no dataset names and no URLs; a
    dataset-specific caller passes its own set (e.g. ``providers.datasets.ibl_planning_resources``).
    """

    model_config = ConfigDict(extra="forbid")

    allowed_inspection_resources: list[str] = Field(default_factory=list)
    official_online_resources: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_allowed_resources(self) -> DatasetInspectionResources:
        if not self.allowed_inspection_resources:
            raise ValueError("dataset inspection resources require at least one allowed resource")
        return self


def generic_inspection_resources() -> DatasetInspectionResources:
    """Dataset-agnostic default: the dataset's own docs/schema/metadata/samples, no URLs."""
    return DatasetInspectionResources(
        allowed_inspection_resources=[
            "local dataset documentation",
            "dataset repository code",
            "schema and metadata files",
            "bounded sample data",
            "executor repository documentation and skills",
        ],
        official_online_resources=[],
    )


class DatasetPlannerTaskPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    packet_id: str
    packet_version: str = DATASET_PLANNER_PACKET_VERSION
    prompt_version: str = DATASET_PLANNER_PROMPT_VERSION
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_branch_event_count: int = Field(ge=1)
    active_variant_ids: list[str]
    family_intent_invariant: dict[str, Any]
    variant_intent_invariants: list[dict[str, Any]]
    scientific_dialogue: ScientificDialogueToolConfig
    output_paths: PlannerPathPolicy
    permission_policy: PlannerPermissionPolicy
    metadata_value_probe_policy: MetadataValueProbePolicy | None = None
    full_local_data_planning_policy: FullLocalDataPlanningPolicy | None = None
    # Bounded revise-loop: when present, this handoff is a re-plan round — the planner must
    # produce a revised plan draft that addresses the listed required_changes (see the role files).
    revision_context: PlanRevisionContext | None = None
    allowed_inspection_resources: list[str] = Field(default_factory=list)
    official_online_resources: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "packet_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DatasetPlannerTaskPacket identity fields must be non-empty")
        return value

    @model_validator(mode="after")
    def validate_family_variant_scope(self) -> DatasetPlannerTaskPacket:
        variant_ids = [
            str(item.get("variant_id", "")).strip() for item in self.variant_intent_invariants
        ]
        if sorted(variant_ids) != sorted(self.active_variant_ids):
            raise ValueError("planner packet variant invariants must match active variants")
        if self.scientific_dialogue.branch_id != self.branch_id:
            raise ValueError("planner packet dialogue config references another branch")
        if self.scientific_dialogue.run_id != self.run_id:
            raise ValueError("planner packet dialogue config references another run")
        if not self.allowed_inspection_resources or not self.expected_outputs:
            raise ValueError("planner packet requires inspection resources and expected outputs")
        return self


class DatasetPlannerHandoffManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    handoff_id: str
    status: PlannerHandoffStatus
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    packet_path: str
    task_path: str
    manifest_path: str
    packet_digest: str
    task_digest: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "handoff_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "packet_path",
        "task_path",
        "manifest_path",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DatasetPlannerHandoffManifest fields must be non-empty")
        return value

    @field_validator("packet_digest", "task_digest")
    @classmethod
    def require_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("handoff manifest digest fields must be sha256 hex")
        return value


class PlannerArtifactValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    run_id: str
    branch_id: str
    status: PlannerHandoffStatus
    evidence_ids: list[str] = Field(default_factory=list)
    checked_paths: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_report_status(self) -> PlannerArtifactValidationReport:
        if self.status == PlannerHandoffStatus.PREPARED:
            raise ValueError("artifact validation report cannot use prepared status")
        if self.status == PlannerHandoffStatus.RETURNED_VALID and self.errors:
            raise ValueError("returned_valid validation report cannot contain errors")
        if self.status == PlannerHandoffStatus.RETURNED_INVALID and not self.errors:
            raise ValueError("returned_invalid validation report requires errors")
        return self


def planner_packet_digest(packet: DatasetPlannerTaskPacket) -> str:
    return stable_hash(packet.model_dump(mode="json"))


def validate_planner_artifacts(
    branch: QuestionFamilyBranch,
    *,
    run_id: str,
    evidence_paths: list[str | Path] | None = None,
    construct_probe_map_paths: list[str | Path] | None = None,
    feasibility_findings: Sequence[DatasetFeasibilityFinding | dict[str, Any]] | None = None,
    construct_probe_maps: Sequence[ConstructProbeMap | dict[str, Any]] | None = None,
    planner_outputs: list[dict[str, Any]] | None = None,
    checked_paths: list[str | Path] | None = None,
    planner_workspace: str | Path | None = None,
    require_typed_planner_outputs: bool = False,
    require_exactly_one_terminal: bool = False,
    required_prompt_version: str | None = None,
) -> PlannerArtifactValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    evidence_items = list(branch.inspection_evidence)
    checked = [str(path) for path in checked_paths or []]

    for path in evidence_paths or []:
        checked.append(str(path))
        try:
            if planner_workspace is not None:
                _validate_path_under_workspace(path, planner_workspace)
            evidence = load_model(path, QuestionFamilyInspectionEvidence)
            _validate_evidence_for_branch(branch, evidence)
            require_planner_evidence_unverified(evidence)
            forbidden = _boundary_violations(evidence.model_dump(mode="json"))
            if forbidden:
                errors.append(
                    f"{path}: inspection evidence contains prohibited structured artifacts: "
                    + ", ".join(forbidden)
                )
            warnings.extend(
                f"{path}: advisory planner language: {item}"
                for item in planner_language_warnings(evidence.model_dump(mode="json"))
            )
            evidence_items.append(evidence)
        except Exception as exc:
            errors.append(f"{path}: {exc}")

    evidence_by_id: dict[str, QuestionFamilyInspectionEvidence] = {}
    for evidence in evidence_items:
        if evidence.evidence_id in evidence_by_id:
            if stable_hash(evidence_by_id[evidence.evidence_id].model_dump(mode="json")) != (
                stable_hash(evidence.model_dump(mode="json"))
            ):
                errors.append(
                    f"conflicting duplicate inspection evidence id: {evidence.evidence_id}"
                )
            continue
        evidence_by_id[evidence.evidence_id] = evidence

    for raw in feasibility_findings or []:
        try:
            finding = (
                raw
                if isinstance(raw, DatasetFeasibilityFinding)
                else DatasetFeasibilityFinding.model_validate(raw)
            )
            forbidden = _boundary_violations(finding.model_dump(mode="json"))
            if forbidden:
                errors.append(
                    "feasibility finding contains prohibited structured artifacts: "
                    + ", ".join(forbidden)
                )
            warnings.extend(
                "advisory feasibility language: " + item
                for item in planner_language_warnings(finding.model_dump(mode="json"))
            )
            _validate_finding_for_branch(branch, finding, evidence_by_id)
        except Exception as exc:
            errors.append(f"feasibility finding invalid: {exc}")

    if construct_probe_maps:
        errors.extend(
            validate_construct_probe_maps(
                branch,
                construct_probe_maps=construct_probe_maps,
                evidence_by_id=evidence_by_id,
            )
        )

    loaded_construct_probe_maps: list[ConstructProbeMap] = []
    for path in construct_probe_map_paths or []:
        checked.append(str(path))
        try:
            if planner_workspace is not None:
                _validate_path_under_workspace(path, planner_workspace)
            probe_map = load_model(path, ConstructProbeMap)
            loaded_construct_probe_maps.append(probe_map)
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    if loaded_construct_probe_maps:
        errors.extend(
            validate_construct_probe_maps(
                branch,
                construct_probe_maps=loaded_construct_probe_maps,
                evidence_by_id=evidence_by_id,
            )
        )

    typed_terminal_messages: list[
        PlanDraftMessage | BranchRejectionMessage | HumanEscalationRequest
    ] = []
    root_terminal_candidate_types: list[str] = []
    for output in planner_outputs or []:
        raw_message_type = output.get("message_type")
        if raw_message_type in {
            "plan_draft",
            "branch_rejection",
            "human_escalation_request",
        }:
            root_terminal_candidate_types.append(str(raw_message_type))
        forbidden = _boundary_violations(output)
        if forbidden:
            errors.append(
                "planner output contains prohibited structured artifacts: " + ", ".join(forbidden)
            )
        warnings.extend(
            "advisory planner language: " + item for item in planner_language_warnings(output)
        )
        if require_typed_planner_outputs:
            tool_envelope_keys = sorted(
                set(output).intersection(DIRECT_FILE_FORBIDDEN_ENVELOPE_KEYS)
            )
            if tool_envelope_keys:
                errors.append(
                    "planner output uses tool-call envelope keys: " + ", ".join(tool_envelope_keys)
                )
            try:
                message = _PLANNING_MESSAGE_ADAPTER.validate_python(output)
                if required_prompt_version and message.prompt_version != required_prompt_version:
                    raise ValueError(
                        "planner output prompt_version does not match active handoff: "
                        f"{message.prompt_version!r} != {required_prompt_version!r}"
                    )
                _validate_planning_message_for_branch(branch, message, evidence_by_id)
                if isinstance(
                    message,
                    (PlanDraftMessage, BranchRejectionMessage, HumanEscalationRequest),
                ):
                    typed_terminal_messages.append(message)
                if isinstance(message, PlanDraftMessage):
                    _validate_variant_analysis_plans_for_branch(
                        branch,
                        message,
                        evidence_by_id,
                        require_complete=True,
                    )
            except Exception as exc:
                errors.append(f"planner output invalid typed PlanningMessage: {exc}")

    if require_exactly_one_terminal and (
        len(root_terminal_candidate_types) != 1 or len(typed_terminal_messages) != 1
    ):
        terminal_types = [message.message_type for message in typed_terminal_messages]
        if len(root_terminal_candidate_types) == 1 and not typed_terminal_messages:
            errors.append(
                "planner output requires exactly one typed terminal "
                "(plan_draft, branch_rejection, or human_escalation_request); "
                "one root terminal candidate is present but invalid: "
                f"{root_terminal_candidate_types}; see the typed PlanningMessage validation "
                "error above"
            )
        else:
            errors.append(
                "planner output requires exactly one typed terminal "
                "(plan_draft, branch_rejection, or human_escalation_request); "
                f"observed {len(root_terminal_candidate_types)} root candidate(s): "
                f"{root_terminal_candidate_types}; {len(typed_terminal_messages)} passed typed "
                f"validation: {terminal_types}"
            )

    status = (
        PlannerHandoffStatus.RETURNED_INVALID if errors else PlannerHandoffStatus.RETURNED_VALID
    )
    return PlannerArtifactValidationReport(
        report_id=f"planner-validation-{stable_hash({'branch_id': branch.branch_id, 'errors': errors})[:12]}",
        run_id=run_id,
        branch_id=branch.branch_id,
        status=status,
        evidence_ids=sorted(evidence_by_id),
        checked_paths=checked,
        errors=errors,
        warnings=warnings,
    )


def _validate_evidence_for_branch(
    branch: QuestionFamilyBranch,
    evidence: QuestionFamilyInspectionEvidence,
) -> None:
    if branch.state != QuestionFamilyBranchState.PLANNER_INSPECTING:
        raise ValueError("planner evidence requires planner_started branch state")
    if evidence.branch_id != branch.branch_id:
        raise ValueError("inspection evidence references another branch")
    if evidence.question_family_id != branch.question_family_id:
        raise ValueError("inspection evidence references another family")
    if (
        evidence.scope == QuestionFamilyBranchEventScope.VARIANT
        and evidence.variant_id not in branch.active_variant_ids
    ):
        raise ValueError("inspection evidence references inactive variant")


def _validate_finding_for_branch(
    branch: QuestionFamilyBranch,
    finding: DatasetFeasibilityFinding,
    evidence_by_id: dict[str, QuestionFamilyInspectionEvidence],
) -> None:
    if finding.branch_id != branch.branch_id:
        raise ValueError("feasibility finding references another branch")
    if finding.context_id != branch.context_id:
        raise ValueError("feasibility finding references another context")
    if finding.owner_session_id != branch.owner_session_id:
        raise ValueError("feasibility finding references another owner session")
    _validate_variant_message_identity(branch, finding.variant_id, finding.question_seed_id)
    unsupported = [
        evidence_id
        for evidence_id in finding.evidence_ids
        if evidence_id not in evidence_by_id
        or not evidence_by_id[evidence_id].can_support_variant(finding.variant_id)
    ]
    if unsupported:
        raise ValueError(
            "feasibility finding references unsupported evidence: " + ", ".join(unsupported)
        )


def _validate_planning_message_for_branch(
    branch: QuestionFamilyBranch,
    message: PlanningMessage,
    evidence_by_id: dict[str, QuestionFamilyInspectionEvidence],
) -> None:
    if message.branch_id != branch.branch_id:
        raise ValueError("planning message references another branch")
    if message.context_id != branch.context_id:
        raise ValueError("planning message references another context")
    if message.owner_session_id != branch.owner_session_id:
        raise ValueError("planning message references another owner session")
    if message.scope == "variant":
        _validate_variant_message_identity(branch, message.variant_id, message.question_seed_id)

    direct_evidence_ids: list[str] = []
    for field_name in ("evidence_ids", "blocking_evidence_ids"):
        direct_evidence_ids.extend(getattr(message, field_name, []))
    if direct_evidence_ids:
        variant_id = message.variant_id if message.scope == "variant" else ""
        _validate_message_evidence_refs(
            direct_evidence_ids,
            evidence_by_id,
            variant_id=variant_id,
            context=f"planning message {message.message_id}",
        )

    # Review messages carry evidence inside typed criterion/change assessments as well as at the
    # top level. Every nested reference remains branch-local; prose reconciliation cannot launder a
    # foreign evidence ID into the durable issue ledger.
    nested_evidence_groups = [
        ("classified change", item.evidence_ids)
        for item in getattr(message, "classified_required_changes", [])
    ]
    nested_evidence_groups.extend(
        ("owner change assessment", item.evidence_ids)
        for item in getattr(message, "owner_change_assessments", [])
    )
    nested_evidence_groups.extend(
        ("criterion assessment", item.evidence_ids)
        for item in getattr(message, "criterion_assessments", [])
    )
    for label, evidence_ids in nested_evidence_groups:
        _validate_message_evidence_refs(
            evidence_ids,
            evidence_by_id,
            variant_id=message.variant_id if message.scope == "variant" else "",
            context=f"planning message {message.message_id} {label}",
        )

    for outcome in getattr(message, "variant_outcomes", []):
        _validate_variant_message_identity(branch, outcome.variant_id, outcome.question_seed_id)
        if (
            isinstance(message, PlanDraftMessage)
            and outcome.decision.is_accepted
            and not outcome.evidence_ids
        ):
            raise ValueError(
                "accepted plan variant requires branch-local evidence: " + outcome.variant_id
            )
        _validate_message_evidence_refs(
            outcome.evidence_ids,
            evidence_by_id,
            variant_id=outcome.variant_id,
            context=f"variant outcome {outcome.variant_id}",
        )

    if isinstance(message, PlanDraftMessage) and message.variant_analysis_plans:
        _validate_variant_analysis_plans_for_branch(
            branch,
            message,
            evidence_by_id,
            require_complete=False,
        )


def _validate_variant_analysis_plans_for_branch(
    branch: QuestionFamilyBranch,
    message: PlanDraftMessage,
    evidence_by_id: dict[str, QuestionFamilyInspectionEvidence],
    *,
    require_complete: bool,
) -> None:
    """Validate detailed accepted-variant plans at the serious direct-file boundary."""

    accepted = {
        outcome.variant_id: outcome
        for outcome in message.variant_outcomes
        if outcome.decision.is_accepted
    }
    details = {entry.variant_id: entry for entry in message.variant_analysis_plans}
    if require_complete and set(details) != set(accepted):
        missing = sorted(set(accepted) - set(details))
        unexpected = sorted(set(details) - set(accepted))
        parts = []
        if missing:
            parts.append("missing accepted variants: " + ", ".join(missing))
        if unexpected:
            parts.append("unexpected variants: " + ", ".join(unexpected))
        raise ValueError(
            "serious direct-file plan requires one detailed AnalysisPlan per accepted variant"
            + ("; " + "; ".join(parts) if parts else "")
        )

    invariant_by_variant = {
        invariant.variant_id: invariant for invariant in branch.variant_intent_invariants
    }
    plan_ids: set[str] = set()
    for variant_id, detail in details.items():
        outcome = accepted.get(variant_id)
        invariant = invariant_by_variant.get(variant_id)
        if outcome is None or invariant is None:
            raise ValueError("detailed AnalysisPlan references a non-accepted branch variant")
        if detail.question_seed_id != outcome.question_seed_id:
            raise ValueError("detailed AnalysisPlan variant/question-seed identity mismatch")
        plan = detail.analysis_plan
        if plan.analysis_plan_id in plan_ids:
            raise ValueError("detailed AnalysisPlan IDs must be unique within a family plan")
        plan_ids.add(plan.analysis_plan_id)
        if plan.branch_id != branch.branch_id:
            raise ValueError("detailed AnalysisPlan references another branch")
        if plan.question_version_id != invariant.question_seed_id:
            raise ValueError(
                "detailed AnalysisPlan question_version_id must match the active question seed"
            )
        if plan.scientific_intent_invariant_id != invariant.invariant.invariant_id:
            raise ValueError("detailed AnalysisPlan references another scientific intent invariant")
        if not set(plan.evidence_ids).issubset(outcome.evidence_ids):
            raise ValueError(
                "detailed AnalysisPlan evidence must be declared by its variant outcome"
            )
        _validate_message_evidence_refs(
            plan.evidence_ids,
            evidence_by_id,
            variant_id=variant_id,
            context=f"detailed AnalysisPlan {plan.analysis_plan_id}",
        )
        for source in plan.data_sources:
            if source.branch_id != branch.branch_id:
                raise ValueError("detailed AnalysisPlan data source references another branch")
            if not set(source.evidence_ids).issubset(plan.evidence_ids):
                raise ValueError(
                    "detailed AnalysisPlan data-source evidence is absent from the plan ledger"
                )
            _validate_message_evidence_refs(
                source.evidence_ids,
                evidence_by_id,
                variant_id=variant_id,
                context=f"detailed AnalysisPlan data source {source.data_source_id}",
            )


def _validate_message_evidence_refs(
    evidence_ids: list[str],
    evidence_by_id: dict[str, QuestionFamilyInspectionEvidence],
    *,
    variant_id: str,
    context: str,
) -> None:
    unsupported = [
        evidence_id
        for evidence_id in evidence_ids
        if evidence_id not in evidence_by_id
        or (variant_id and not evidence_by_id[evidence_id].can_support_variant(variant_id))
    ]
    if unsupported:
        raise ValueError(f"{context} references unsupported evidence: " + ", ".join(unsupported))


def _validate_variant_message_identity(
    branch: QuestionFamilyBranch,
    variant_id: str,
    question_seed_id: str,
) -> None:
    matches = [
        invariant
        for invariant in branch.variant_intent_invariants
        if invariant.variant_id == variant_id
    ]
    if len(matches) != 1:
        raise ValueError("message does not reference exactly one active branch variant")
    if matches[0].question_seed_id != question_seed_id:
        raise ValueError("message variant_id/question_seed_id mismatch")


def _validate_path_under_workspace(path: str | Path, planner_workspace: str | Path) -> None:
    root = Path(planner_workspace).resolve()
    resolved = Path(path).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("planner artifact path must remain under planner_workspace")


def _boundary_violations(value: Any) -> list[str]:
    return find_planner_boundary_violations(value)
