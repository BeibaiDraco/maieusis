"""Generic Source B: coarse, proposal-safe local-sample exploration.

Source B of the two-source dataset narrator: a generic coding agent explores a dataset's local
*sample* data and returns a COARSE, firewall-safe facts document (modality / coarse scale /
structure / task design / standardization / limitations) — never exact column names, table
schema, or exact row/trial/session/unit counts. It reuses the sandboxed spawn muscle (the
runners' ``explore()``), but is deliberately a lean sibling of the detailed planner path: no
branch, no owner/dialogue, no terminal plan/rejection — one coarse artifact.

Three defence layers keep the product coarse (agent-untrusted):

1. **Coarsen-by-contract (task text, here).** ``build_coarse_explore_task`` tells the agent to
   produce exactly one coarse facts YAML and forbids exact schema/columns/counts.
2. **Structural schema.** ``CoarseLocalDatasetFacts`` (``extra="forbid"``) has no columns/schema
   field, so exact schema has nowhere to go.
3. **Host-side import firewall (``collect_coarse_facts``, here).** The collecting host runs
   ``assert_proposal_safe_payload`` on the raw agent output *and* parses it through the strict
   schema, so any leak / extra key / malformed YAML fails closed. The agent is never trusted.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

import yaml
from pydantic import BaseModel, ConfigDict

from ...io import dump_data, load_data
from ...schemas.coarse_dataset_facts import CoarseExploreRunResult, CoarseLocalDatasetFacts
from ...services.narrative_sources.coarse_facts_import import import_coarse_facts
from ...services.planning.dataset_planner_packet import DatasetInspectionResources

COARSE_EXPLORE_PROMPT_VERSION = "coarse_sample_explorer/v1"
COARSE_EXPLORE_ARTIFACT_NAME = "coarse_facts.yaml"
COARSE_EXPLORE_TASK_NAME = "coarse_task.md"
COARSE_EXPLORE_HANDOFF_NAME = "coarse_handoff.yaml"
COARSE_SAMPLE_LOCATOR_SCHEME = "local-sample-exploration"

# Assertable contract clauses (the contract test pins these; keeping them constants means the
# forbidding wording cannot silently drift). All lowercase-"one" on purpose (the dataset-agnostic
# guard forbids the standalone uppercase acronym).
COARSE_TASK_SINGLE_ARTIFACT = "Write exactly one coarse facts YAML file"
COARSE_TASK_NO_EXACT_SCHEMA = (
    "NEVER report exact column or field names, table schemas, or exact "
    "row/trial/session/unit counts"
)
COARSE_TASK_NUMBERS_RULE = (
    "Report numbers only as coarse, order-of-magnitude or approximate scale facts"
)


def coarse_sample_locator(dataset_id: str) -> str:
    """The canonical Source-B provenance locator (also the A/B provenance tag GF-2c reuses)."""
    return f"{COARSE_SAMPLE_LOCATOR_SCHEME}://{dataset_id}"


class CoarseExploreHandoff(BaseModel):
    """Branch-free coarse handoff: the task text + the single declared output path."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    prompt_version: str = COARSE_EXPLORE_PROMPT_VERSION
    sample_locator: str
    task_text: str
    task_path: str
    artifact_path: str
    handoff_path: str


@runtime_checkable
class CoarseSampleExplorer(Protocol):
    """Launch half of the coarse path: run the coarse task, write one coarse facts artifact.

    Implemented by ``ClaudeCodeAgentRunner`` / ``CodexAgentRunner`` (``explore()``); both reuse
    their own ``external_readonly`` safety envelope.
    """

    runner_name: str

    def explore(
        self,
        *,
        task_text: str,
        workspace: Path,
        expected_artifact: Path,
        run_label: str = "",
    ) -> CoarseExploreRunResult: ...


def build_coarse_explore_task(
    *,
    dataset_id: str,
    workspace: str | Path,
    inspection_resources: DatasetInspectionResources,
) -> CoarseExploreHandoff:
    """Write the coarse-exploration ``task.md`` + a tiny handoff manifest (no branch)."""
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    locator = coarse_sample_locator(dataset_id)
    artifact_path = workspace / COARSE_EXPLORE_ARTIFACT_NAME
    task_text = _coarse_task_text(
        dataset_id=dataset_id,
        artifact_path=artifact_path,
        sample_locator=locator,
        inspection_resources=inspection_resources,
    )
    task_path = workspace / COARSE_EXPLORE_TASK_NAME
    task_path.write_text(task_text, encoding="utf-8")
    handoff = CoarseExploreHandoff(
        dataset_id=dataset_id,
        sample_locator=locator,
        task_text=task_text,
        task_path=str(task_path),
        artifact_path=str(artifact_path),
        handoff_path=str(workspace / COARSE_EXPLORE_HANDOFF_NAME),
    )
    dump_data(handoff.model_dump(mode="json"), workspace / COARSE_EXPLORE_HANDOFF_NAME)
    return handoff


def collect_coarse_facts(
    *,
    workspace: str | Path,
    dataset_id: str,
    sample_locator: str = "",
    explorer_adapter: str = "",
    explorer_identity: str = "",
    artifact_name: str = COARSE_EXPLORE_ARTIFACT_NAME,
) -> CoarseLocalDatasetFacts:
    """Read the agent's coarse facts artifact + pass it through the shared host import firewall.

    Fail closed on a missing artifact, malformed YAML, a non-mapping payload, or any leak (the shared
    ``import_coarse_facts`` runs the belt firewall + strict reparse and stamps host-owned provenance;
    the local sample is B's single scale-fact source, so its URI is forced onto every scale fact).
    """
    workspace = Path(workspace)
    artifact_path = workspace / artifact_name
    if not artifact_path.exists():
        raise ValueError(f"coarse explore produced no coarse facts artifact at {artifact_path}")
    try:
        raw = load_data(artifact_path)
    except yaml.YAMLError as exc:
        raise ValueError(
            f"coarse explorer wrote invalid YAML in {artifact_path} (fail-closed; quote free-text "
            f"values or use a block scalar): {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise ValueError(f"coarse facts artifact must be a mapping, got {type(raw).__name__}")

    locator = sample_locator or coarse_sample_locator(dataset_id)
    return import_coarse_facts(
        raw,
        CoarseLocalDatasetFacts,
        provenance={
            "dataset_id": dataset_id,
            "sample_locator": locator,
            "explorer_adapter": explorer_adapter,
            "explorer_identity": explorer_identity,
        },
        scale_fact_source_ids=[locator],
    )


def explore_local_sample(
    *,
    runner: CoarseSampleExplorer,
    dataset_id: str,
    workspace: str | Path,
    inspection_resources: DatasetInspectionResources,
    run_label: str = "",
) -> CoarseLocalDatasetFacts:
    """Dual-host coarse driver: build task -> ``runner.explore()`` -> ``collect_coarse_facts``.

    ``runner`` is a ``ClaudeCodeAgentRunner`` or ``CodexAgentRunner`` configured for
    ``external_readonly`` access to the dataset's local sample.
    """
    workspace = Path(workspace)
    handoff = build_coarse_explore_task(
        dataset_id=dataset_id,
        workspace=workspace,
        inspection_resources=inspection_resources,
    )
    result = runner.explore(
        task_text=handoff.task_text,
        workspace=workspace,
        expected_artifact=Path(handoff.artifact_path),
        run_label=run_label or dataset_id,
    )
    return collect_coarse_facts(
        workspace=workspace,
        dataset_id=dataset_id,
        sample_locator=handoff.sample_locator,
        explorer_adapter=result.explorer_adapter,
        explorer_identity=result.explorer_identity,
    )


def _coarse_task_text(
    *,
    dataset_id: str,
    artifact_path: Path,
    sample_locator: str,
    inspection_resources: DatasetInspectionResources,
) -> str:
    allowed = "\n".join(f"- {item}" for item in inspection_resources.allowed_inspection_resources)
    online = inspection_resources.official_online_resources
    online_text = (
        "\n\nOfficial online reference(s) for this dataset (documentation/metadata only):\n"
        + "\n".join(f"- {url}" for url in online)
        if online
        else ""
    )
    return f"""# Maieusis Coarse Local-Sample Exploration Task (Source B)

You are a proposal-stage COARSE dataset explorer. This is NOT the detailed post-proposal
planner: you must stay COARSE. Your job is to read the dataset's local SAMPLE data read-only and
write a coarse, proposal-safe facts document that could help a scientist form broad questions —
without exposing exact structure.

Dataset id: `{dataset_id}`

Allowed inspection (local sample, read-only):
{allowed}{online_text}

Use the configured inspection runtime for bounded checks only (documentation, coarse shape, small
samples). Do NOT run a full or long-running analysis, do NOT search for effects or significance,
and do NOT load full raw-array surfaces.

## What to produce

{COARSE_TASK_SINGLE_ARTIFACT} at exactly this path:

`{artifact_path}`

It is a single YAML mapping with these coarse fields (all COARSE prose; omit what the sample does
not support):

- `dataset_id`: `{dataset_id}`
- `modalities`: list of coarse recording/measurement modalities (broad kinds, not field names)
- `broad_scale`: coarse magnitude prose (orders of magnitude / approximate ranges)
- `coarse_structure`: coarse hierarchy / temporal structure at a high level
- `task_or_design`: the experimental task or design, described broadly
- `spatial_or_anatomical_coverage`: coarse spatial / anatomical scope
- `standardization`: coarse packaging / standardization / access description
- `major_variables`: broad names of the major variable families (not exact fields)
- `known_coarse_limitations`: high-level caveats a proposal stage should keep in mind
- `scale_facts`: a list of coarse magnitude facts, each `{{quantity_kind, value_text}}` where
  `value_text` is an order-of-magnitude or approximate phrase (the host fills identity/source)

## Firewall (hard rules — violating any voids the whole run)

- {COARSE_TASK_NO_EXACT_SCHEMA}. Describe KINDS of things, not their exact identifiers.
- {COARSE_TASK_NUMBERS_RULE}. Use approximate phrasing (for example "tens of", "order of a few
  hundred", "roughly"), never an exact tally and never an `n_...=<number>` form.
- Do NOT emit a `columns`, `schema`, or `table_schema` field, or any exact per-record layout.
- Do NOT fill provenance/identity/digest fields; the trusted host stamps those. Provenance
  locator for this exploration is `{sample_locator}`.
- Do NOT use execution/analysis vocabulary anywhere (no "effect", "p-value", "significance",
  "confirmation set"), not even in a disclaimer.

Finish as soon as the single coarse facts YAML is written. Write nothing else outside the
workspace.
"""
