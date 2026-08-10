"""Config → runtime factories.

Turn a validated ``MaieusisProjectConfig`` into the runtime collaborators the driver + orchestrator need:
``DatasetInspectionResources`` built FROM THE CONFIG (never the legacy dataset-specific helper), a per-family
``planner_host_factory`` (real host in standard mode; an explicit ``FakePlannerHost`` in
subscription-only-demo — never a SILENT Fake), the owner/reviewer scientific providers (distinct), and
the per-variant ``VariantNoveltyConfig``. Demo mode resolves every API-agent provider to ``mock`` and
yields the Fake host, so a demo run makes ZERO paid model/agent calls.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from ...providers.coding_agents.claude_code_agent_runner import (
    CLAUDE_DATASET_ACCESS_ADD_DIR,
    CLAUDE_DATASET_ACCESS_EXTERNAL_READONLY,
    ClaudeCodeAgentRunner,
    probe_claude_cli_version,
)
from ...providers.coding_agents.claude_code_host import ClaudeCodePlannerHost
from ...providers.coding_agents.codex_agent_runner import (
    CODEX_DATASET_ACCESS_EXTERNAL_READONLY,
    CODEX_DATASET_ACCESS_SNAPSHOT_COPY,
    CodexAgentRunner,
)
from ...providers.coding_agents.codex_host import CodexPlannerHost
from ...providers.coding_agents.planner_host import CodingAgentPlannerHost, FakePlannerHost
from ...providers.scientific_agents import (
    AnthropicScientificAgentProvider,
    MockScientificAgentProvider,
    OpenAIScientificAgentProvider,
    ScientificAgentProvider,
)
from ...schemas.maieusis_project_config import (
    CodingHost,
    ConfigDatasetAccessMode,
    MaieusisProjectConfig,
    ProviderModel,
)
from ..agents.plan_reviewer import (
    build_plan_fidelity_reviewer_provider_from_env,
    load_plan_fidelity_reviewer_prompt,
)
from ..agents.question_owner import load_question_owner_prompt
from ..paper_ingest.external_lookup import (
    CrossrefLookupProvider,
    CrossrefSourceReferenceProvider,
    EuropePmcLookupProvider,
    NullProcessedPaperLookupProvider,
    OpenAlexLookupProvider,
    OpenAlexRequestCoordinator,
    OpenAlexSourceReferenceProvider,
    ProcessedPaperLookupProvider,
    SourceReferenceProvider,
)
from ..planning.dataset_planner_packet import DatasetInspectionResources
from ..retrieval.variant_novelty import VariantNoveltyConfig


def build_paper_lookup_providers(
    config: MaieusisProjectConfig,
    *,
    openalex_coordinator: OpenAlexRequestCoordinator | None = None,
) -> list[ProcessedPaperLookupProvider]:
    """The cited-work lookup stack for the PRODUCT ingest path (config-gated, no new secret).

    OpenAlex FIRST: the reference resolver keeps the first best-scoring record
    (``reference_resolution.py`` — strict ``>``), so on a DOI-match tie the abstract-bearing
    OpenAlex record wins over Crossref's (Crossref works usually carry NO abstract — the live
    308/308 ``resolved_record_has_no_abstract`` came from the reverse order). Crossref stays as
    the metadata fallback; a work absent from both remains honestly unavailable. Email/API-key
    handling lives in the providers (``OPENALEX_EMAIL`` / ``OPENALEX_API_KEY`` env; the same
    email doubles as the Crossref politeness mailto).
    """
    if not config.literature.enabled:
        return [NullProcessedPaperLookupProvider()]
    # config email wins; the providers themselves fall back to OPENALEX_EMAIL env when it is "".
    email = config.literature.openalex_email or os.getenv("OPENALEX_EMAIL", "")
    return [
        OpenAlexLookupProvider(email=email, request_coordinator=openalex_coordinator),
        CrossrefLookupProvider(mailto=email),
        EuropePmcLookupProvider(),
    ]


def build_source_reference_providers(
    config: MaieusisProjectConfig,
    *,
    openalex_coordinator: OpenAlexRequestCoordinator | None = None,
) -> list[SourceReferenceProvider]:
    """P1: the DOI-keyed whole-bibliography stack for the PRODUCT ingest path (config-gated).

    When a paper's PDF-parsed reference list is thinner than
    ``paperbank.min_local_reference_count``, these pull the paper's full reference list by DOI
    (bypassing imperfect PDF reference extraction) so cited-work resolution + abstracts are not
    starved. Crossref-source FIRST (one call returns the whole bibliography); OpenAlex-source second
    (its ``referenced_works`` walk is an N+1 fetch). Gated on ``paperbank.external_reference_fallback``
    AND ``literature.enabled``; empty when either is off (fallback disabled). No new secret — the same
    ``OPENALEX_EMAIL`` / ``OPENALEX_API_KEY`` env the abstract stack uses.
    """
    if not config.literature.enabled or not config.paperbank.external_reference_fallback:
        return []
    email = config.paperbank.openalex_email or os.getenv("OPENALEX_EMAIL", "")
    return [
        CrossrefSourceReferenceProvider(mailto=config.paperbank.crossref_mailto or email),
        OpenAlexSourceReferenceProvider(
            email=email,
            api_key=os.getenv("OPENALEX_API_KEY", ""),
            request_coordinator=openalex_coordinator,
        ),
    ]


def build_openalex_request_coordinator(config: MaieusisProjectConfig) -> OpenAlexRequestCoordinator:
    """Build one stage-scoped coordinator shared across all product OpenAlex request paths."""
    return OpenAlexRequestCoordinator(
        cache_dir=config.run.output_root / "ingest_corpus" / "lookup_cache" / "openalex",
        # Four requests/second across all paper workers stays below a polite "few requests/sec".
        min_interval_seconds=0.25,
        quota_failure_threshold=3,
    )


def build_inspection_resources(config: MaieusisProjectConfig) -> DatasetInspectionResources:
    """Build the planner inspection resources FROM THE CONFIG (never the legacy dataset-specific helper)."""
    configured_docs = [
        f"configured dataset description document: {Path(doc)}" for doc in config.dataset.seed.docs
    ]
    return DatasetInspectionResources(
        allowed_inspection_resources=[
            *config.dataset.allowed_inspection_resources,
            *configured_docs,
        ],
        official_online_resources=list(config.dataset.official_online_resources),
    )


def novelty_config_from(config: MaieusisProjectConfig) -> VariantNoveltyConfig:
    """Wire NoveltyConfig → the per-variant VariantNoveltyConfig (demo disables it via the fan-out)."""
    novelty = config.novelty
    return VariantNoveltyConfig(
        enabled=novelty.enabled,
        direct_recap_threshold=novelty.direct_recap_threshold,
        close_prior_threshold=novelty.close_prior_threshold,
        max_candidates=novelty.max_candidates,
    )


def build_planner_host_factory(
    config: MaieusisProjectConfig, *, run_root: str | Path
) -> Callable[[str], CodingAgentPlannerHost]:
    """Per-family host factory: real host from the config in standard mode; explicit Fake in demo.

    Demo mode yields ``FakePlannerHost`` (an explicit workflow-demo host that never spawns) — this is
    never a SILENT fallback (standard mode always builds the real ``coding_host``).
    """
    run_root = Path(run_root)
    if config.is_demo:

        def demo_factory(_family_id: str) -> CodingAgentPlannerHost:
            return FakePlannerHost(outcome="plan")

        return demo_factory

    runtime = config.dataset.inspection_runtime
    dataset_root = str(runtime.dataset_root) if runtime.dataset_root is not None else None
    inspection_python = runtime.inspection_python or None
    inspection_command = runtime.inspection_command or None
    inspection_pythonpath = runtime.inspection_pythonpath or None
    source_tree_root = runtime.source_tree_root

    external_readonly = runtime.dataset_access_mode == ConfigDatasetAccessMode.EXTERNAL_READONLY

    def factory(family_id: str) -> CodingAgentPlannerHost:
        launch_parent = run_root / f"launch-{family_id}"
        if config.models.coding_host == CodingHost.CLAUDE_CODE:
            claude_runner = ClaudeCodeAgentRunner(
                model=config.models.coding_model,
                effort=(
                    config.models.coding_reasoning_effort.value
                    if config.models.coding_reasoning_effort is not None
                    else None
                ),
                cli_version=probe_claude_cli_version(),
                dataset_root=dataset_root,
                dataset_access_mode=(
                    CLAUDE_DATASET_ACCESS_EXTERNAL_READONLY
                    if external_readonly
                    else CLAUDE_DATASET_ACCESS_ADD_DIR
                ),
                inspection_python=inspection_python,
                inspection_command=inspection_command,
                inspection_pythonpath=inspection_pythonpath,
                inspection_extra_env=dict(runtime.inspection_extra_env),
                source_tree_root=source_tree_root,
                max_turns=runtime.max_turns,
                timeout_seconds=runtime.timeout_seconds,
                launch_parent=launch_parent,
            )
            return ClaudeCodePlannerHost(root=run_root, runner=claude_runner)
        reasoning_effort = config.models.coding_reasoning_effort
        if reasoning_effort is None:  # defensive: ModelsConfig validation already requires this.
            raise ValueError("Codex coding_host requires coding_reasoning_effort")
        codex_runner = CodexAgentRunner(
            model=config.models.coding_model,
            reasoning_effort=reasoning_effort.value,
            dataset_root=dataset_root,
            dataset_access_mode=(
                CODEX_DATASET_ACCESS_EXTERNAL_READONLY
                if external_readonly
                else CODEX_DATASET_ACCESS_SNAPSHOT_COPY
            ),
            inspection_python=inspection_python,
            inspection_command=inspection_command,
            inspection_pythonpath=inspection_pythonpath,
            inspection_extra_env=dict(runtime.inspection_extra_env),
            source_tree_root=source_tree_root,
            timeout_seconds=runtime.timeout_seconds,
            launch_parent=launch_parent,
        )
        return CodexPlannerHost(root=run_root, runner=codex_runner)

    return factory


def build_scientific_provider(
    pm: ProviderModel,
    *,
    system_prompt: str,
    allow_pro_model: bool = False,
    mock_responses: Sequence[Any] = (),
) -> ScientificAgentProvider:
    """Build a scientific-agent provider from a config ProviderModel (mock stays paid-call-free)."""
    provider = pm.provider.strip().lower()
    if provider == "mock":
        return MockScientificAgentProvider(responses=list(mock_responses))
    if provider == "openai":
        return OpenAIScientificAgentProvider(
            model=pm.model or None,
            allow_pro_model=allow_pro_model,
            system_prompt=system_prompt,
            thinking=pm.thinking.value,
            effort=pm.effort.value,
        )
    if provider == "anthropic":
        return AnthropicScientificAgentProvider(
            model=pm.model or None,
            allow_pro_model=allow_pro_model,
            system_prompt=system_prompt,
            thinking=pm.thinking.value,
            effort=pm.effort.value,
        )
    raise ValueError(f"unsupported scientific provider: {provider!r}")


def build_owner_reviewer_providers(
    config: MaieusisProjectConfig,
    *,
    owner_mock_responses: Sequence[Any] = (),
    reviewer_mock_responses: Sequence[Any] = (),
) -> tuple[ScientificAgentProvider, ScientificAgentProvider]:
    """Build the (owner, reviewer) providers from the config (mock in demo). Distinct in standard mode."""
    owner_pm = config.effective_provider(config.models.owner)
    reviewer_pm = config.effective_provider(config.models.reviewer)
    owner = build_scientific_provider(
        owner_pm,
        system_prompt=load_question_owner_prompt(),
        allow_pro_model=config.models.allow_pro_model,
        mock_responses=owner_mock_responses,
    )
    if reviewer_pm.provider.strip().lower() == "mock":
        reviewer: ScientificAgentProvider = MockScientificAgentProvider(
            responses=list(reviewer_mock_responses), provider_id="mock:reviewer"
        )
    elif reviewer_pm.model.strip():
        # Config reviewer model is set → config WINS: build directly with that model + the plan-fidelity
        # reviewer prompt (env-only build_plan_fidelity_reviewer_provider_from_env would drop it).
        reviewer = build_scientific_provider(
            reviewer_pm,
            system_prompt=load_plan_fidelity_reviewer_prompt(),
            allow_pro_model=config.models.allow_pro_model,
        )
    else:
        # Empty config model → env fallback (MAIEUSIS_R5_REVIEWER_PROVIDER / <NAME>_MODEL).
        reviewer = build_plan_fidelity_reviewer_provider_from_env(
            provider=reviewer_pm.provider.strip().lower(),  # type: ignore[arg-type]
            allow_pro_model=config.models.allow_pro_model,
            thinking=reviewer_pm.thinking.value,
            effort=reviewer_pm.effort.value,
        )
    return owner, reviewer
