"""Shared real planner host: Runner (launch) + Collect (read/validate/assemble).

``RealPlannerHost`` implements the ``CodingAgentPlannerHost`` protocol on top of a
pluggable ``AgentRunner``. It is the single, host-agnostic adapter that the
host wrappers (Codex / Claude Code) instantiate with a real
subprocess runner; the *Collect* half — read the workspace artifacts, validate
them, and assemble a ``PlannerReturnedArtifactBundle`` — is shared here so both
hosts return identical typed bundles regardless of how the agent was launched.

``run_planning`` reuses the proven contract: the shared
``run_record`` / ``returned_bundle`` builders, ``CodingAgentHandoffBackend``'s
``validate_returned_artifacts`` for the collect-time validation, and the caller's
existing ``import_returned_artifacts`` for the actual branch-event import. The
run trace is written by the host (it audits the launch), not by the in-sandbox
agent.

This module carries no dataset-specific names; it is enforced by the
dataset-agnostic guard.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from ...enums import ClaimLevel
from ...io import load_data
from ...provenance import stable_hash
from ...schemas.planner_run import (
    CodingAgentRunStatus,
    PlannerArtifactPresentationRepair,
    PlannerArtifactRepairLedger,
    PlannerReturnedArtifactBundle,
)
from ...schemas.planning_dialogue import DatasetFeasibilityFinding
from ...schemas.question_family_branch import QuestionFamilyBranch
from ...services.planning.confined_workspace_io import (
    assert_confined_write_target,
    atomic_write_confined_bytes,
    atomic_write_confined_model,
    atomic_write_confined_yaml_data,
)
from ...services.planning.dataset_planner_packet import (
    DATASET_PLANNER_PROMPT_VERSION,
    DatasetPlannerHandoffManifest,
)
from ...services.planning.planner_boundaries import assert_planner_boundary_safe
from ...services.planning.planner_bundle_builders import (
    real_run_record_id,
    restamp_provenance_digests,
    returned_bundle,
    run_record,
)
from ...services.planning.planner_failures import (
    HardFamilyIntegrityViolation,
    RecoverableFamilyTerminal,
)
from .agent_runner import AgentRunner, AgentRunResult
from .handoff import CodingAgentHandoffBackend

if TYPE_CHECKING:  # reserved collaborators forwarded to the runner
    from ...mcp import ScientificDialogueServer
    from ..scientific_agents import ScientificAgentProvider


@dataclass(frozen=True)
class _EnumPresentationAlias:
    alias_id: str
    target: str


_PRESENTATION_ENUM_ALIASES: dict[tuple[str, str], dict[str, _EnumPresentationAlias]] = {
    ("dataset_feasibility_finding", "status"): {
        "partial": _EnumPresentationAlias(
            alias_id="dataset_feasibility_finding.status.partial",
            target="partially_available",
        ),
        "available_with_constraints": _EnumPresentationAlias(
            alias_id="dataset_feasibility_finding.status.available_with_constraints",
            target="partially_available",
        ),
    }
}

_ANALYSIS_PLAN_PROSE_LIST_FIELDS = frozenset(
    {
        "analysis_strategy",
        "candidate_estimands",
        "diagnostics",
        "negative_controls",
        "positive_controls",
        "alternative_explanations",
        "predicted_result_patterns",
        "interpretation_limits",
        "required_new_skills",
        "unresolved_decisions",
    }
)
_CLAIM_LEVEL_VALUES = frozenset(level.value for level in ClaimLevel)
_CLAIM_CEILING_PROSE_ALIAS = (
    "plan_draft.analysis_plan.claim_ceiling_components.prose_degraded_to_notes"
)
_PROTECTED_SHAPE_TOKENS = frozenset(
    {
        "authority",
        "branch_id",
        "classification",
        "decision",
        "digest",
        "evidence_id",
        "model_id",
        "provider_id",
        "question_seed_id",
        "question_version_id",
        "scope",
        "session_id",
        "variant_id",
    }
)


@dataclass(frozen=True)
class _PresentationAliasUse:
    alias_id: str
    note: str


def _registered_presentation_alias_ids() -> tuple[str, ...]:
    enum_aliases = tuple(
        alias.alias_id
        for aliases in _PRESENTATION_ENUM_ALIASES.values()
        for alias in aliases.values()
    )
    prose_aliases = tuple(
        f"plan_draft.analysis_plan.{field_name}.{operation}"
        for field_name in sorted(_ANALYSIS_PLAN_PROSE_LIST_FIELDS)
        for operation in ("string_singleton", "single_key_string_mapping")
    )
    root_aliases = (
        "plan_draft.unresolved_decisions.string_singleton",
        _CLAIM_CEILING_PROSE_ALIAS,
    )
    return (*enum_aliases, *prose_aliases, *root_aliases)


_REGISTERED_PRESENTATION_ALIAS_IDS = _registered_presentation_alias_ids()
if len(_REGISTERED_PRESENTATION_ALIAS_IDS) != len(set(_REGISTERED_PRESENTATION_ALIAS_IDS)):
    raise RuntimeError("planner presentation aliases must be registered exactly once")


@dataclass(frozen=True)
class _PendingPresentationRepair:
    artifact_path: Path
    raw_snapshot_path: Path
    raw_digest: str
    aliases: tuple[str, ...]
    changes: tuple[str, ...]


class RealPlannerHost:
    """Runs one branch-local planning pass via a runner and collects a bundle."""

    def __init__(
        self,
        *,
        runner: AgentRunner,
        root: str | Path,
        adapter_name: str | None = None,
    ) -> None:
        self.runner = runner
        self.root = Path(root)
        self.adapter_name = adapter_name or runner.runner_name

    def run_planning(
        self,
        *,
        run_id: str,
        branch: QuestionFamilyBranch,
        handoff: DatasetPlannerHandoffManifest,
        owner_session: ScientificAgentProvider | None = None,
        dialogue_server: ScientificDialogueServer | None = None,
    ) -> PlannerReturnedArtifactBundle:
        backend = CodingAgentHandoffBackend(self.root, run_id=run_id)
        workspace = Path(handoff.packet_path).parent

        run_result = self.runner.run(
            run_id=run_id,
            branch=branch,
            handoff=handoff,
            workspace=workspace,
            owner_session=owner_session,
            dialogue_server=dialogue_server,
        )
        if run_result.status != CodingAgentRunStatus.RETURNED:
            raise RecoverableFamilyTerminal(
                f"agent runner did not return successfully: status={run_result.status.value}"
            )
        if run_result.source_tree_mutation_detected or (
            run_result.source_tree_before_digest
            and run_result.source_tree_after_digest
            and run_result.source_tree_before_digest != run_result.source_tree_after_digest
        ):
            raise HardFamilyIntegrityViolation(
                "coding-agent planner reported a Maieusis source-tree mutation"
            )

        # The host owns the run trace: it audits the launch (adapter identity,
        # transcript, source-tree unchanged). The in-sandbox agent owns only the
        # scientific artifacts under the workspace.
        # A real subprocess spawn reports actual timing (started_at set). Only then do we drop the
        # `synthetic-` run-record id and carry the real wall-clock + captured usage; in-process
        # runners (Synthetic / Manual) leave timing None and keep the synthetic id + placeholder.
        is_real_spawn = run_result.started_at is not None
        record = run_record(
            branch,
            handoff,
            run_id=run_id,
            status=CodingAgentRunStatus.RETURNED,
            transcript_path=Path(run_result.transcript_path),
            transcript_digest=run_result.transcript_digest,
            planner_adapter=self.adapter_name,
            planner_identity=run_result.planner_identity,
            run_record_id=real_run_record_id(branch) if is_real_spawn else None,
            started_at=run_result.started_at,
            ended_at=run_result.ended_at,
            usage=run_result.usage,
            planner_model_id=run_result.planner_model_id,
            planner_reasoning_effort=run_result.planner_reasoning_effort,
            planner_cli_version=run_result.planner_cli_version,
            planner_budget_policy=run_result.planner_budget_policy,
            planner_timeout_seconds=run_result.planner_timeout_seconds,
            # Empty for in-process runners (placeholder used); real for subprocess runners.
            source_tree_before_digest=run_result.source_tree_before_digest or None,
            source_tree_after_digest=run_result.source_tree_after_digest or None,
            workspace_manifest_before_digest=(run_result.workspace_manifest_before_digest or None),
            workspace_manifest_after_digest=(run_result.workspace_manifest_after_digest or None),
            attempt_count=run_result.attempt_count,
            attempt_audit_digest=run_result.attempt_audit_digest,
            runner_warnings=run_result.runner_warnings,
            source_tree_mutation_detected=run_result.source_tree_mutation_detected,
            blocked_actions_checked=run_result.blocked_actions_checked or None,
        )
        run_record_path = workspace / "run_record.yaml"
        atomic_write_confined_model(
            record,
            workspace=workspace,
            path=run_record_path,
        )

        return self._collect(
            backend=backend,
            branch=branch,
            handoff=handoff,
            run_id=run_id,
            workspace=workspace,
            run_record_path=run_record_path,
            run_result=run_result,
        )

    def _collect(
        self,
        *,
        backend: CodingAgentHandoffBackend,
        branch: QuestionFamilyBranch,
        handoff: DatasetPlannerHandoffManifest,
        run_id: str,
        workspace: Path,
        run_record_path: Path,
        run_result: AgentRunResult,
    ) -> PlannerReturnedArtifactBundle:
        """Read the workspace artifacts, validate them, and assemble the bundle."""
        # Validate EVERY returned coordinate before reading even the first payload.  Tolerant
        # presentation repair must never become a pre-confinement file read/write primitive.
        self._assert_workspace_and_authority_boundaries(run_result, workspace=workspace)
        pending_repairs = self._canonicalize_presentation_shapes(
            run_result,
            workspace=workspace,
        )
        run_result, classification_notes = self._reclassify_misplaced_feasibility_findings(
            run_result
        )
        # Option B: the host owns provenance. A spawned agent writes only
        # logical content (it has no code-execution tool to hash); the host recomputes
        # every sha256/stable_hash digest from that content before validation. Idempotent
        # for Synthetic / Manual artifacts (their builders already used these formulas).
        presentation_notes = [note for repair in pending_repairs for note in repair.changes]
        host_repair_notes = [
            *run_result.runner_warnings,
            *presentation_notes,
            *classification_notes,
            *self._restamp_provenance(run_result, workspace=workspace),
        ]
        repair_ledger_path, repair_raw_paths = self._persist_presentation_repair_ledger(
            pending_repairs,
            run_id=run_id,
            branch=branch,
            workspace=workspace,
        )

        evidence_paths: list[str | Path] = list(run_result.evidence_paths)
        construct_probe_map_paths: list[str | Path] = list(run_result.construct_probe_map_paths)
        report = backend.validate_returned_artifacts(
            branch.branch_id,
            evidence_paths=evidence_paths,
            construct_probe_map_paths=construct_probe_map_paths or None,
            planner_outputs=self._guarded_outputs(run_result),
            require_typed_planner_outputs=True,
            require_exactly_one_terminal=True,
            required_prompt_version=DATASET_PLANNER_PROMPT_VERSION,
        )
        if host_repair_notes:
            report.warnings = list(dict.fromkeys([*report.warnings, *host_repair_notes]))
            atomic_write_confined_model(
                report,
                workspace=workspace,
                path=workspace / "validation_report.yaml",
            )
        if report.errors:
            raise RecoverableFamilyTerminal(
                "real planner host collect validation failed: " + "; ".join(report.errors)
            )

        return returned_bundle(
            branch,
            handoff,
            run_id=run_id,
            bundle_id=self._bundle_id(branch, run_id),
            workspace=workspace,
            run_record_path=run_record_path,
            evidence_paths=[Path(path) for path in run_result.evidence_paths],
            dialogue_paths=[Path(path) for path in run_result.dialogue_paths],
            plan_draft_paths=[Path(path) for path in run_result.plan_draft_paths],
            rejection_paths=[Path(path) for path in run_result.rejection_paths],
            host_repair_notes=host_repair_notes,
            presentation_repair_ledger_path=repair_ledger_path,
            presentation_repair_raw_paths=repair_raw_paths,
        )

    def _canonicalize_presentation_shapes(
        self,
        run_result: AgentRunResult,
        *,
        workspace: Path,
    ) -> list[_PendingPresentationRepair]:
        """Apply only registered schema-aware presentation aliases, preserving raw bytes.

        This pass runs only after the complete returned path surface and raw structured-authority
        payloads have passed the hard boundary.  Registry keys include the exact message type and
        field, making the transformation deterministic and idempotent.  It never changes decisions,
        IDs, evidence, scope, authority, or any unregistered field.
        """

        pending: list[_PendingPresentationRepair] = []
        seen: set[str] = set()
        self._assert_safe_repair_audit_root(workspace)
        audit_root = workspace / "repair_audit" / "raw"
        for raw_path in self._returned_artifact_paths(run_result):
            path_key = str(raw_path)
            if path_key in seen:
                continue
            seen.add(path_key)
            path = Path(raw_path)
            data = self._load_agent_artifact(path)
            if not isinstance(data, dict):
                continue
            raw_bytes = path.read_bytes()
            alias_uses = _canonicalize_presentation_payload(data, artifact_name=path.name)
            if not alias_uses:
                continue
            aliases = tuple(alias.alias_id for alias in alias_uses)
            changes = tuple(alias.note for alias in alias_uses)
            raw_digest = hashlib.sha256(raw_bytes).hexdigest()
            raw_snapshot_path = audit_root / f"{raw_digest}.artifact"
            raw_snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            assert_confined_write_target(
                workspace=workspace,
                path=raw_snapshot_path,
            )
            if raw_snapshot_path.exists():
                if raw_snapshot_path.read_bytes() != raw_bytes:
                    raise HardFamilyIntegrityViolation(
                        "planner presentation repair raw snapshot digest collision"
                    )
            else:
                atomic_write_confined_bytes(
                    raw_bytes,
                    workspace=workspace,
                    path=raw_snapshot_path,
                )
            atomic_write_confined_yaml_data(
                data,
                workspace=workspace,
                path=path,
            )
            pending.append(
                _PendingPresentationRepair(
                    artifact_path=path,
                    raw_snapshot_path=raw_snapshot_path,
                    raw_digest=raw_digest,
                    aliases=aliases,
                    changes=changes,
                )
            )
        return pending

    @staticmethod
    def _assert_safe_repair_audit_root(workspace: Path) -> None:
        """Refuse agent-planted aliases before creating any host-owned repair audit path."""
        root = workspace.resolve(strict=True)
        cursor = workspace
        for component in ("repair_audit", "raw"):
            cursor /= component
            if cursor.is_symlink():
                raise HardFamilyIntegrityViolation(
                    "planner presentation repair audit path is symlink-aliased"
                )
            if cursor.exists():
                try:
                    resolved = cursor.resolve(strict=True)
                except OSError as exc:
                    raise HardFamilyIntegrityViolation(
                        "planner presentation repair audit path is unreadable"
                    ) from exc
                if resolved != root and root not in resolved.parents:
                    raise HardFamilyIntegrityViolation(
                        "planner presentation repair audit path escaped its branch workspace"
                    )
                if not resolved.is_dir():
                    raise HardFamilyIntegrityViolation(
                        "planner presentation repair audit path is not a directory"
                    )

    def _persist_presentation_repair_ledger(
        self,
        pending: list[_PendingPresentationRepair],
        *,
        run_id: str,
        branch: QuestionFamilyBranch,
        workspace: Path,
    ) -> tuple[Path | None, list[Path]]:
        if not pending:
            return None, []
        self._assert_safe_repair_audit_root(workspace)
        records = [
            PlannerArtifactPresentationRepair(
                repair_id=(
                    "planner-presentation-repair-"
                    + stable_hash(
                        {
                            "run_id": run_id,
                            "branch_id": branch.branch_id,
                            "artifact_path": str(repair.artifact_path),
                            "raw_digest": repair.raw_digest,
                            "changes": repair.changes,
                        }
                    )[:16]
                ),
                artifact_path=str(repair.artifact_path),
                raw_snapshot_path=str(repair.raw_snapshot_path),
                raw_digest=repair.raw_digest,
                canonical_digest=hashlib.sha256(repair.artifact_path.read_bytes()).hexdigest(),
                aliases=list(repair.aliases),
                changes=list(repair.changes),
            )
            for repair in pending
        ]
        ledger = PlannerArtifactRepairLedger(
            ledger_id=(
                "planner-presentation-repair-ledger-"
                + stable_hash(
                    {
                        "run_id": run_id,
                        "branch_id": branch.branch_id,
                        "records": [record.model_dump(mode="json") for record in records],
                    }
                )[:16]
            ),
            run_id=run_id,
            branch_id=branch.branch_id,
            planner_workspace=str(workspace),
            records=records,
        )
        ledger_path = workspace / "repair_audit" / "presentation_repair_ledger.yaml"
        atomic_write_confined_model(
            ledger,
            workspace=workspace,
            path=ledger_path,
        )
        raw_paths = list(dict.fromkeys(repair.raw_snapshot_path for repair in pending))
        return ledger_path, raw_paths

    def _reclassify_misplaced_feasibility_findings(
        self, run_result: AgentRunResult
    ) -> tuple[AgentRunResult, list[str]]:
        """Reclassify only strict feasibility messages misplaced under ``evidence/``.

        Coding agents occasionally follow the semantic word "evidence" instead of the packet's
        directory contract and write a valid ``DatasetFeasibilityFinding`` beside inspection
        evidence.  Discovery intentionally remains path-only because classifying dialogue there
        would confuse terminal-surface counting in subprocess runners.  Collect is the narrow safe
        repair point: a file moves between returned path lists only when its host-restamped payload
        strictly validates as the one allowed message type.  Near misses remain evidence and fail
        closed in the existing validator.
        """
        retained_evidence: list[str] = []
        dialogue_paths = list(run_result.dialogue_paths)
        dialogue_seen = set(dialogue_paths)
        notes: list[str] = []
        for path in run_result.evidence_paths:
            data = self._load_agent_artifact(path)
            if (
                not isinstance(data, dict)
                or data.get("message_type") != "dataset_feasibility_finding"
            ):
                retained_evidence.append(path)
                continue
            try:
                DatasetFeasibilityFinding.model_validate(restamp_provenance_digests(data))
            except ValueError:
                retained_evidence.append(path)
                continue
            if path not in dialogue_seen:
                dialogue_paths.append(path)
                dialogue_seen.add(path)
            notes.append(
                "host safe repair: reclassified schema-valid DatasetFeasibilityFinding "
                f"{Path(path).name} from evidence_paths to dialogue_paths; content and path "
                "retained unchanged"
            )
        if not notes:
            return run_result, []
        return (
            run_result.model_copy(
                update={
                    "evidence_paths": retained_evidence,
                    "dialogue_paths": dialogue_paths,
                }
            ),
            notes,
        )

    def _restamp_provenance(
        self,
        run_result: AgentRunResult,
        *,
        workspace: Path,
    ) -> list[str]:
        """Stamp code-owned provenance digests without repairing scientific state."""
        artifact_paths = (
            *run_result.evidence_paths,
            *run_result.dialogue_paths,
            *run_result.plan_draft_paths,
            *run_result.rejection_paths,
        )
        for path in artifact_paths:
            data = self._load_agent_artifact(path)
            if isinstance(data, dict):
                atomic_write_confined_yaml_data(
                    restamp_provenance_digests(data),
                    workspace=workspace,
                    path=Path(path),
                )
        return []

    def _guarded_outputs(self, run_result: AgentRunResult) -> list[Any]:
        return [
            self._load_agent_artifact(path)
            for path in (
                *run_result.dialogue_paths,
                *run_result.plan_draft_paths,
                *run_result.rejection_paths,
            )
        ]

    def _assert_workspace_and_authority_boundaries(
        self, run_result: AgentRunResult, *, workspace: Path
    ) -> None:
        """Validate the complete path surface before reading any returned artifact payload."""

        root = workspace.resolve(strict=True)
        lexical_root = Path(os.path.abspath(workspace))
        artifact_paths = self._returned_artifact_paths(run_result)

        # Pass 1 is metadata-only. Do not parse even a valid in-workspace file until every returned
        # coordinate has proved canonical, regular, non-symlinked, and branch-workspace confined.
        for raw_path in artifact_paths:
            path = Path(raw_path)
            lexical_path = Path(os.path.abspath(path))
            try:
                relative = lexical_path.relative_to(lexical_root)
                resolved = path.resolve(strict=True)
                metadata = path.lstat()
            except ValueError as exc:
                raise HardFamilyIntegrityViolation(
                    "coding-agent planner artifact escaped its branch workspace"
                ) from exc
            except OSError as exc:
                raise RecoverableFamilyTerminal(
                    f"planner returned a missing or unreadable artifact: {path.name}"
                ) from exc
            cursor = lexical_root
            has_symlink_component = False
            for component in relative.parts:
                cursor /= component
                if cursor.is_symlink():
                    has_symlink_component = True
                    break
            if (
                has_symlink_component
                or resolved == root
                or root not in resolved.parents
                or not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
            ):
                raise HardFamilyIntegrityViolation(
                    "coding-agent planner artifact escaped its branch workspace or is not a "
                    "single-link regular file"
                )

        # Pass 2 may now inspect content. Structured authority/result artifacts stay hard and are
        # checked on the exact raw payload before any tolerant presentation canonicalization.
        for raw_path in dict.fromkeys(artifact_paths):
            path = Path(raw_path)
            try:
                payload = self._load_agent_artifact(path)
            except ValueError as exc:
                raise RecoverableFamilyTerminal(str(exc)) from exc
            assert_planner_boundary_safe(payload, context="coding-agent planner artifact")

    @staticmethod
    def _returned_artifact_paths(run_result: AgentRunResult) -> tuple[str, ...]:
        return (
            *run_result.evidence_paths,
            *run_result.construct_probe_map_paths,
            *run_result.dialogue_paths,
            *run_result.plan_draft_paths,
            *run_result.rejection_paths,
        )

    @staticmethod
    def _load_agent_artifact(path: str | Path) -> Any:
        """Load an agent-written YAML artifact, failing closed on malformed YAML.

        A real coding agent can emit invalid YAML (e.g. an unquoted free-text value that
        contains a colon), so Collect must surface that as a clear fail-closed error naming the
        file, not a raw scanner traceback. The bundle is discarded either way.
        """
        try:
            return load_data(path)
        except yaml.YAMLError as exc:
            raise ValueError(
                f"planner wrote invalid YAML in {path} (fail-closed; quote free-text values or "
                f"use a block scalar): {exc}"
            ) from exc

    def _bundle_id(self, branch: QuestionFamilyBranch, run_id: str) -> str:
        digest = stable_hash(
            {
                "adapter_name": self.adapter_name,
                "run_id": run_id,
                "branch_id": branch.branch_id,
            }
        )
        return f"real-planner-{self.adapter_name}-{digest[:12]}"


def _canonicalize_presentation_payload(
    output: dict[str, Any], *, artifact_name: str
) -> list[_PresentationAliasUse]:
    """Apply exact schema/field aliases without changing any protected scientific state."""

    message_type = output.get("message_type")
    if not isinstance(message_type, str):
        return []
    alias_uses: list[_PresentationAliasUse] = []
    for (registered_type, field_name), aliases in _PRESENTATION_ENUM_ALIASES.items():
        if message_type != registered_type:
            continue
        source = output.get(field_name)
        alias = aliases.get(source) if isinstance(source, str) else None
        if alias is None:
            continue
        protected_before = stable_hash(
            {key: value for key, value in output.items() if key != field_name}
        )
        output[field_name] = alias.target
        protected_after = stable_hash(
            {key: value for key, value in output.items() if key != field_name}
        )
        if protected_after != protected_before:  # pragma: no cover - defensive invariant
            raise HardFamilyIntegrityViolation(
                "presentation canonicalization changed protected planner state"
            )
        if registered_type == "dataset_feasibility_finding" and field_name == "status":
            alias_uses.append(
                _PresentationAliasUse(
                    alias_id=alias.alias_id,
                    note=(
                        "host safe repair: DatasetFeasibilityFinding "
                        f"{artifact_name} conservatively normalized status {source} -> "
                        f"{alias.target}; coverage, limitations, impact, and evidence retained "
                        "unchanged"
                    ),
                )
            )
    if message_type == "plan_draft":
        alias_uses.extend(_canonicalize_plan_draft_prose_lists(output))
    alias_uses = _deduplicate_alias_uses(alias_uses)
    applied_alias_ids = [alias.alias_id for alias in alias_uses]
    if len(applied_alias_ids) != len(
        set(applied_alias_ids)
    ):  # pragma: no cover - registry/implementation invariant
        raise RuntimeError("planner presentation alias was applied more than once to one artifact")
    return alias_uses


def _deduplicate_alias_uses(
    alias_uses: list[_PresentationAliasUse],
) -> list[_PresentationAliasUse]:
    """Record one ledger alias per artifact while retaining every concrete occurrence note."""

    notes_by_alias: dict[str, list[str]] = {}
    for alias in alias_uses:
        notes = notes_by_alias.setdefault(alias.alias_id, [])
        if alias.note not in notes:
            notes.append(alias.note)
    return [
        _PresentationAliasUse(alias_id=alias_id, note="; ".join(notes))
        for alias_id, notes in notes_by_alias.items()
    ]


def _canonicalize_plan_draft_prose_lists(output: dict[str, Any]) -> list[_PresentationAliasUse]:
    """Canonicalize only exact prose-list fields in a typed family plan draft.

    A scalar string may stand for a one-item prose list. A YAML ``- label: explanation`` item may
    stand for the string ``"label: explanation"``. No identity, decision, authority, evidence,
    digest, scope, or unregistered field is touched.
    """

    alias_uses: list[_PresentationAliasUse] = []
    root_unresolved = output.get("unresolved_decisions")
    if isinstance(root_unresolved, str) and root_unresolved.strip():
        output["unresolved_decisions"] = [root_unresolved]
        alias_uses.append(
            _PresentationAliasUse(
                alias_id="plan_draft.unresolved_decisions.string_singleton",
                note=(
                    "host safe repair: plan_draft wrapped unresolved_decisions prose scalar as "
                    "a one-item list; text retained unchanged"
                ),
            )
        )

    entries = output.get("variant_analysis_plans")
    if not isinstance(entries, list):
        return alias_uses
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        variant_id = str(entry.get("variant_id") or "unknown-variant")
        plan = entry.get("analysis_plan")
        if not isinstance(plan, dict):
            continue
        claim_ceiling_alias = _degrade_claim_ceiling_component_prose(
            plan,
            variant_id=variant_id,
        )
        if claim_ceiling_alias is not None:
            alias_uses.append(claim_ceiling_alias)
        for field_name in sorted(_ANALYSIS_PLAN_PROSE_LIST_FIELDS):
            items = plan.get(field_name)
            if isinstance(items, str) and items.strip():
                plan[field_name] = [items]
                alias_uses.append(
                    _PresentationAliasUse(
                        alias_id=f"plan_draft.analysis_plan.{field_name}.string_singleton",
                        note=(
                            "host safe repair: plan_draft variant "
                            f"{variant_id} wrapped {field_name} prose scalar as a one-item list; "
                            "text retained unchanged"
                        ),
                    )
                )
                continue
            if not isinstance(items, list):
                continue
            repaired_indexes: list[int] = []
            for index, item in enumerate(items):
                if not isinstance(item, dict) or len(item) != 1:
                    continue
                key, value = next(iter(item.items()))
                if not isinstance(key, str) or not isinstance(value, str):
                    continue
                key = key.strip()
                value = value.strip()
                lowered_key = key.lower()
                if (
                    not key
                    or not value
                    or any(token in lowered_key for token in _PROTECTED_SHAPE_TOKENS)
                ):
                    continue
                items[index] = f"{key}: {value}"
                repaired_indexes.append(index)
            if repaired_indexes:
                alias_uses.append(
                    _PresentationAliasUse(
                        alias_id=(
                            f"plan_draft.analysis_plan.{field_name}.single_key_string_mapping"
                        ),
                        note=(
                            "host safe repair: plan_draft variant "
                            f"{variant_id} losslessly serialized single-key mapping item(s) in "
                            f"{field_name} at indexes "
                            + ", ".join(str(index) for index in repaired_indexes)
                        ),
                    )
                )
    return alias_uses


def _degrade_claim_ceiling_component_prose(
    plan: dict[str, Any],
    *,
    variant_id: str,
) -> _PresentationAliasUse | None:
    """Retain an exact all-prose component near-miss without inventing claim authority.

    ``claim_ceiling_components`` is a structured set of ``ClaimLevel`` values, not a prose field.
    A planner may nevertheless put explanatory limitations there.  When the primary ceiling is
    already exact and every component is unambiguously prose, degrade those strings to explicitly
    non-authoritative interpretation notes and leave the structured component set empty.  Mixed or
    malformed shapes remain untouched so strict typed validation rejects them.
    """

    primary = plan.get("claim_ceiling")
    components = plan.get("claim_ceiling_components")
    interpretation_limits = plan.get("interpretation_limits")
    if (
        not isinstance(primary, str)
        or primary not in _CLAIM_LEVEL_VALUES
        or not isinstance(components, list)
        or not components
        or not all(isinstance(item, str) and item.strip() for item in components)
        or any(item in _CLAIM_LEVEL_VALUES for item in components)
        or not isinstance(interpretation_limits, list)
        or not all(isinstance(item, str) for item in interpretation_limits)
    ):
        return None

    protected_before = stable_hash(
        {
            key: value
            for key, value in plan.items()
            if key not in {"claim_ceiling_components", "interpretation_limits"}
        }
    )
    retained_notes = [
        f"Untyped planner claim-ceiling note (non-authoritative): {item}" for item in components
    ]
    plan["claim_ceiling_components"] = []
    plan["interpretation_limits"] = [*interpretation_limits, *retained_notes]
    protected_after = stable_hash(
        {
            key: value
            for key, value in plan.items()
            if key not in {"claim_ceiling_components", "interpretation_limits"}
        }
    )
    if protected_after != protected_before:  # pragma: no cover - defensive invariant
        raise HardFamilyIntegrityViolation(
            "claim-ceiling presentation repair changed protected planner state"
        )
    return _PresentationAliasUse(
        alias_id=_CLAIM_CEILING_PROSE_ALIAS,
        note=(
            "host safe repair: plan_draft variant "
            f"{variant_id} retained explanatory claim_ceiling_components as explicitly "
            "non-authoritative interpretation_limits and cleared the malformed component set; "
            "primary claim ceiling and all protected planning state remained unchanged"
        ),
    )
