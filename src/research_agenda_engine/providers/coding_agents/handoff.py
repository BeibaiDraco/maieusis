from __future__ import annotations

from pathlib import Path
from typing import Any

from ...assets import resolve_asset
from ...io import dump_data
from ...mcp import scientific_dialogue_branch_token
from ...provenance import stable_hash
from ...schemas.planner_run import (
    PlannerArtifactImportManifest,
    PlannerReturnedArtifactBundle,
)
from ...schemas.planning_dialogue import PlanRevisionContext
from ...schemas.question_family_branch import QuestionFamilyBranchState
from ...services.orchestration import QuestionFamilyBranchManager
from ...services.planning.confined_workspace_io import atomic_write_confined_model
from ...services.planning.dataset_planner_packet import (
    DATASET_PLANNER_PROMPT_VERSION,
    SCIENTIFIC_DIALOGUE_TOOL_NAMES,
    DatasetInspectionResources,
    DatasetPlannerHandoffManifest,
    DatasetPlannerTaskPacket,
    MetadataValueProbePolicy,
    PlannerArtifactValidationReport,
    PlannerHandoffStatus,
    PlannerPathPolicy,
    PlannerPermissionPolicy,
    ScientificDialogueToolConfig,
    generic_inspection_resources,
    planner_packet_digest,
    validate_planner_artifacts,
)
from ...services.planning.planner_artifact_import import import_returned_planner_artifacts


class CodingAgentHandoffBackend:
    """Prepare branch-local planner handoff artifacts without launching an agent."""

    def __init__(
        self,
        root: str | Path,
        *,
        run_id: str,
        branch_manager: QuestionFamilyBranchManager | None = None,
        inspection_resources: DatasetInspectionResources | None = None,
    ) -> None:
        self.root = Path(root)
        self.run_id = run_id
        self.branch_manager = branch_manager or QuestionFamilyBranchManager(
            self.root,
            run_id=run_id,
        )
        # Per-dataset injected input. The handoff hardcodes nothing dataset-specific: the default is
        # the dataset-agnostic generic set (docs/schema/metadata/samples, no URLs); a dataset-specific
        # caller (e.g. providers.datasets.ibl_planning_resources) passes its own resources.
        self._inspection_resources = inspection_resources or generic_inspection_resources()

    def prepare_handoff(
        self,
        branch_id: str,
        *,
        metadata_value_probe_policy: MetadataValueProbePolicy | None = None,
        revision_context: PlanRevisionContext | None = None,
    ) -> DatasetPlannerHandoffManifest:
        branch = self.branch_manager.load_branch(branch_id)
        if branch.state != QuestionFamilyBranchState.PLANNER_INSPECTING:
            raise ValueError("dataset planner handoff requires planner_started branch state")

        planner_dir = self._planner_dir(branch.branch_id)
        paths = PlannerPathPolicy(
            planner_workspace=str(planner_dir),
            evidence_dir=str(planner_dir / "evidence"),
            dialogue_dir=str(planner_dir / "dialogue"),
            plan_draft_path=str(planner_dir / "plan_draft.yaml"),
            rejection_path=str(planner_dir / "rejection.yaml"),
            validation_report_path=str(planner_dir / "validation_report.yaml"),
        )
        handoff_id = _handoff_id(
            run_id=self.run_id,
            branch_id=branch.branch_id,
            source_branch_event_count=len(branch.events),
        )
        packet = DatasetPlannerTaskPacket(
            packet_id=f"dataset-planner-packet-{handoff_id[-12:]}",
            run_id=self.run_id,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            source_branch_event_count=len(branch.events),
            active_variant_ids=list(branch.active_variant_ids),
            family_intent_invariant=branch.family_intent_invariant.model_dump(mode="json"),
            variant_intent_invariants=[
                invariant.model_dump(mode="json") for invariant in branch.variant_intent_invariants
            ],
            scientific_dialogue=ScientificDialogueToolConfig(
                server_module="research_agenda_engine.mcp.scientific_dialogue_server:build_server",
                run_id=self.run_id,
                branch_id=branch.branch_id,
                branch_token=scientific_dialogue_branch_token(branch, run_id=self.run_id),
                tools=list(SCIENTIFIC_DIALOGUE_TOOL_NAMES),
            ),
            output_paths=paths,
            permission_policy=_permission_policy(),
            metadata_value_probe_policy=metadata_value_probe_policy,
            revision_context=revision_context,
            allowed_inspection_resources=list(
                self._inspection_resources.allowed_inspection_resources
            ),
            official_online_resources=list(self._inspection_resources.official_online_resources),
            expected_outputs=[
                "QuestionFamilyInspectionEvidence YAML written under the packet evidence_dir",
                "clarification or operationalization messages when needed",
                "DatasetFeasibilityFinding messages with existing evidence IDs",
                "PlanDraftMessage or BranchRejectionMessage",
            ],
        )
        packet_digest = planner_packet_digest(packet)
        task_text = _task_text(packet)
        task_digest = stable_hash({"task": task_text})

        packet_path = planner_dir / "handoff_packet.yaml"
        task_path = planner_dir / "task.md"
        manifest_path = planner_dir / "handoff_manifest.yaml"
        dump_data(packet, packet_path)
        task_path.parent.mkdir(parents=True, exist_ok=True)
        task_path.write_text(task_text, encoding="utf-8")

        manifest = DatasetPlannerHandoffManifest(
            handoff_id=handoff_id,
            status=PlannerHandoffStatus.PREPARED,
            run_id=self.run_id,
            branch_id=branch.branch_id,
            question_family_id=branch.question_family_id,
            context_id=branch.context_id,
            owner_session_id=branch.owner_session_id,
            packet_path=str(packet_path),
            task_path=str(task_path),
            manifest_path=str(manifest_path),
            packet_digest=packet_digest,
            task_digest=task_digest,
        )
        dump_data(manifest, manifest_path)
        self.branch_manager.record_planner_handoff(
            branch.branch_id,
            handoff_id=handoff_id,
            packet_digest=packet_digest,
        )
        return manifest

    def validate_returned_artifacts(
        self,
        branch_id: str,
        *,
        evidence_paths: list[str | Path] | None = None,
        construct_probe_map_paths: list[str | Path] | None = None,
        feasibility_findings: list[dict[str, Any]] | None = None,
        construct_probe_maps: list[dict[str, Any]] | None = None,
        planner_outputs: list[dict[str, Any]] | None = None,
        require_typed_planner_outputs: bool = False,
        require_exactly_one_terminal: bool = False,
        required_prompt_version: str | None = None,
    ) -> PlannerArtifactValidationReport:
        branch = self.branch_manager.load_branch(branch_id)
        report = validate_planner_artifacts(
            branch,
            run_id=self.run_id,
            evidence_paths=evidence_paths,
            construct_probe_map_paths=construct_probe_map_paths,
            feasibility_findings=feasibility_findings,
            construct_probe_maps=construct_probe_maps,
            planner_outputs=planner_outputs,
            planner_workspace=self._planner_dir(branch.branch_id),
            require_typed_planner_outputs=require_typed_planner_outputs,
            require_exactly_one_terminal=require_exactly_one_terminal,
            required_prompt_version=required_prompt_version,
        )
        workspace = self._planner_dir(branch.branch_id)
        atomic_write_confined_model(
            report,
            workspace=workspace,
            path=workspace / "validation_report.yaml",
        )
        return report

    def import_returned_artifacts(
        self,
        bundle: PlannerReturnedArtifactBundle | dict[str, Any],
    ) -> PlannerArtifactImportManifest:
        return import_returned_planner_artifacts(self.branch_manager, bundle)

    def _planner_dir(self, branch_id: str) -> Path:
        return self.root / self.run_id / "branches" / branch_id / "planner"


def _handoff_id(*, run_id: str, branch_id: str, source_branch_event_count: int) -> str:
    digest = stable_hash(
        {
            "run_id": run_id,
            "branch_id": branch_id,
            "source_branch_event_count": source_branch_event_count,
        }
    )
    return f"planner-handoff-{digest[:12]}"


def _permission_policy() -> PlannerPermissionPolicy:
    return PlannerPermissionPolicy(
        write_policy="Write branch planning artifacts only under the planner workspace.",
        allowed_inspection_modes=[
            "documentation inspection",
            "schema inspection",
            "metadata query",
            "bounded sample inspection",
            "repository code inspection",
            "executor skill documentation inspection",
            "tiny structural or synthetic probes",
        ],
        forbidden_actions=[
            "edit Maieusis source files",
            "modify dataset files",
            "run the full scientific pipeline",
            "search for effects or optimize target outcomes",
            "access held-out outcome data",
            "create downstream bridge or execution artifacts",
            "silently change scientific intent",
        ],
        online_query_rules=[
            "Use official documentation and metadata endpoints only.",
            "Record URL or endpoint, access time, query digest, result digest, and limits.",
            "Mark online evidence as planning_only and confirmation-firewall checked.",
        ],
    )


def _task_text(packet: DatasetPlannerTaskPacket) -> str:
    active_prompt = resolve_asset(
        Path("prompts") / f"{DATASET_PLANNER_PROMPT_VERSION}.md"
    ).read_text(encoding="utf-8")
    revision_text = ""
    if packet.revision_context is not None:
        rc = packet.revision_context
        change_lines = "\n".join(f"  - {change}" for change in rc.required_changes)
        revision_text = f"""
REVISION ROUND {rc.revision_round} — this is a bounded re-plan, not a fresh plan.

An earlier plan draft (`{rc.prior_plan_draft_message_id}`, analysis plan
`{rc.prior_analysis_plan_id}`) was reviewed and the owner and/or the independent
reviewer asked for revision. Read your prior plan draft and produce a REVISED
plan draft that directly ADDRESSES each required change below, while preserving
the scientific intent and the distinctions between sibling variants:

{change_lines}

Do not collapse sibling variants into one pipeline. If addressing a change would
require altering the central question, phenomenon, target contrast, claim level,
population scope, or discriminating observation (a MATERIAL revision), do NOT
silently do it — say so in your planner assessment instead.
"""
    metadata_probe_text = ""
    if packet.metadata_value_probe_policy and packet.metadata_value_probe_policy.authorized:
        policy = packet.metadata_value_probe_policy
        metadata_probe_text = f"""
Authorized bounded schema/metadata-value probe:

- Semantic alias discovery is required. Keyword absence is not evidence of
  construct absence when dataset aliases or plausible proxies exist.
- Use observed dataset terminology and provide a mapping rationale for every
  construct-to-field relationship.
- Allowed sources: {", ".join(policy.allowed_sources)}
- Allowed summaries: {", ".join(policy.allowed_summaries)}
- Forbidden persisted outputs: {", ".join(policy.forbidden_outputs)}
- Persist `ConstructProbeMap` records with evidence IDs, match class,
  uncertainty, and owner_review_needed. `plausible_proxy` and `ambiguous`
  mappings require owner review or human escalation before plan acceptance.
"""
    return f"""{active_prompt}

# Branch-Specific Maieusis Dataset Planner Task

You are the dataset-planning coding agent for one isolated QuestionFamilyBranch.
Use the branch-local packet at:

`{packet.output_paths.planner_workspace}/handoff_packet.yaml`

Work only under:

`{packet.output_paths.planner_workspace}`

Branch identity:

- run_id: `{packet.run_id}`
- branch_id: `{packet.branch_id}`
- question_family_id: `{packet.question_family_id}`
- context_id: `{packet.context_id}`
- owner_session_id: `{packet.owner_session_id}`
- active_variant_ids: `{", ".join(packet.active_variant_ids)}`

Use only the actively exposed scientific-dialogue tools for reading branch state
and asking the Question Owner. Write every inspected dataset or executor-doc
claim as `QuestionFamilyInspectionEvidence` YAML under the packet evidence
directory before referring to that claim in a feasibility finding. The trusted
host, not you, writes the CodingAgentRunRecord and returned bundle.

Every dataset assertion must be backed by branch-local
QuestionFamilyInspectionEvidence. Evidence may be family-scoped or scoped to one
active variant. A variant may not use evidence scoped to a sibling variant.
The evidence directory accepts ONLY `QuestionFamilyInspectionEvidence` files.
Write every `DatasetFeasibilityFinding` PlanningMessage under the dialogue
directory, never under the evidence directory; a feasibility finding is not the
single terminal artifact and does not replace the root plan/rejection/escalation.
Every typed planning message must carry explicit `scope`. Use `scope="family"`
only for shared clarification or aggregate family plan/reject/escalation
messages. Operationalization proposals and feasibility findings must be
`scope="variant"` with an active `variant_id` and matching `question_seed_id`.
If a scientific-dialogue tool returns `dialogue_round_limit_reached=true`, do
not retry or continue owner dialogue in that scope. This is a resource cap, not
a scientific verdict. Preserve the evidence and answers already produced, then
write exactly one root terminal artifact: `plan_draft.yaml` when that record
supports a plan (list unresolved decisions explicitly), `rejection.yaml` when
the dataset cannot support any sound variant, or `escalation.yaml` only when a
genuinely unresolved scientific decision requires escalation.
{metadata_probe_text}
{revision_text}

This is a planning-only handoff. Do not edit source or dataset files, run a full
analysis, inspect held-out outcomes, optimize for effects, or write downstream
bridge/execution artifacts. If the dataset cannot support one variant without
changing the scientific intent, reject that variant honestly inside a family
`plan_draft` while preserving any supported sibling variant. Write a root
`rejection.yaml` only when no active variant is accepted or
`accepted_requires_new_skill`; never reject the whole family solely because one
sibling is unsupported. Every accepted variant must cite branch-local evidence
that is valid for that variant.
Evidence must close transitively at all three levels: every data-source evidence
ID must also appear in its AnalysisPlan evidence ledger, and every AnalysisPlan
evidence ID must appear in the matching variant outcome ledger. Never borrow a
sibling variant's evidence or mechanically promote it to family scope.

Expected outputs:

- `QuestionFamilyInspectionEvidence` YAML files only in `{packet.output_paths.evidence_dir}`
- `DatasetFeasibilityFinding` PlanningMessage YAML files only in
  `{packet.output_paths.dialogue_dir}` when needed
- exactly one plan draft, rejection, or human-escalation artifact at the
  packet-specified root path
"""
