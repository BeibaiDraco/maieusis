"""Coarse, proposal-safe dataset facts — the shared product of the two-source narrator.

The coarse ``DatasetNarrative`` is built from up to three feeds into a single shared coarse-facts
shape, distinguished only by a provenance URI:

- **Source A** (documentation fetch, ``documentation-fetch://``) — ``CoarseDocumentationFacts``;
- **Source B** (local-sample agent exploration, ``local-sample-exploration://``) — GF-2a's
  ``CoarseLocalDatasetFacts``;
- **Source C** (model self-research via web search, ``api-model-self-research://``) —
  ``CoarseModelResearchFacts``.

All three subclass ``CoarseDatasetFacts``, which holds the shared coarse CONTENT (the story fields
mirroring ``DatasetNarrative``, with every number quarantined inside the reused
``DatasetNarrativeScaleFact``) plus the proposal-safe firewall validator. There is no ``columns`` /
``table_schema`` / ``row_counts`` field and ``extra="forbid"`` rejects any the caller invents, so a
proposal-stage source has structurally nowhere to put an exact schema or an exact count; the model
validator additionally runs ``assert_proposal_safe_payload`` over the whole dump. Each subclass adds
only its own provenance, so GF-2c can attribute the merged content per source.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ._r5_firewall import assert_proposal_safe_payload
from .dataset_narrative import DatasetNarrativeScaleFact
from .planner_run import CodingAgentRunUsage


class CoarseDatasetFacts(BaseModel):
    """Shared coarse, firewall-safe CONTENT about a dataset (source-agnostic base).

    Mirrors the coarse story fields of ``DatasetNarrative``. Numbers live only in ``scale_facts``
    (reused ``DatasetNarrativeScaleFact``), which is itself coarse + source-backed + firewall-checked.
    Subclasses add their own source-specific provenance; the content + firewall live here so all three
    sources share exactly one coarse contract (this is the content GF-2c merges).
    """

    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    modalities: list[str] = Field(default_factory=list)
    broad_scale: str = ""
    coarse_structure: str = ""
    task_or_design: str = ""
    spatial_or_anatomical_coverage: str = ""
    standardization: str = ""
    # Added in GF-2c so all four sources can carry the full coarse story the fused DatasetNarrative
    # needs (its scientific_purpose is required). Optional (default "") → GF-2a/2b B stays compatible.
    scientific_purpose: str = ""
    population: str = ""
    major_variables: list[str] = Field(default_factory=list)
    reuse_opportunities: list[str] = Field(default_factory=list)
    known_coarse_limitations: list[str] = Field(default_factory=list)
    scale_facts: list[DatasetNarrativeScaleFact] = Field(default_factory=list)

    @field_validator("dataset_id", "task_or_design")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("CoarseDatasetFacts requires non-empty dataset_id and task_or_design")
        return value

    @model_validator(mode="after")
    def enforce_coarse_and_proposal_safe(self) -> CoarseDatasetFacts:
        if not self.modalities:
            raise ValueError("CoarseDatasetFacts requires at least one coarse modality")
        assert_proposal_safe_payload(self.model_dump(mode="python"), context=type(self).__name__)
        return self


class CoarseLocalDatasetFacts(CoarseDatasetFacts):
    """Source B: coarse facts read from a dataset's local sample by a sandboxed agent.

    Host-owned provenance (the exploring agent writes only the coarse scientific content; the
    collecting host stamps identity/digest).
    """

    sample_locator: str = ""
    explorer_adapter: str = ""
    explorer_identity: str = ""
    content_digest: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CoarseDocumentationFacts(CoarseDatasetFacts):
    """Source A: coarse facts extracted from documentation deterministically fetched via the seed link."""

    source_locator: str = ""  # documentation-fetch://<dataset_id>
    provider_id: str = ""
    model_id: str = ""
    source_ref_ids: list[str] = Field(default_factory=list)
    content_digest: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CoarseUserDescriptionFacts(CoarseDatasetFacts):
    """Source D: coarse facts extracted from the USER's own description docs.

    Highest trust of the four (the user is the domain expert on their own dataset), but STILL coarsened
    + firewalled before the Questioner — even detailed user text must not leak exact schema. Reuses
    Source A's extraction mechanism fed the user's docs instead of fetched documentation.
    """

    source_locator: str = ""  # user-provided-description://<dataset_id>
    provider_id: str = ""
    model_id: str = ""
    source_ref_ids: list[str] = Field(default_factory=list)
    content_digest: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WebSearchCitation(BaseModel):
    """A web source the model cited during Source-C self-research (provenance only)."""

    model_config = ConfigDict(extra="forbid")

    url: str = ""
    title: str = ""


class CoarseModelResearchFacts(CoarseDatasetFacts):
    """Source C: coarse facts a frontier model self-researched from the dataset name + link.

    Lowest trust of the three (may cite unverified web sources / hallucinate). It carries
    ``low_trust`` + the web-search ``citations`` for provenance; the structural firewall still
    fail-closes on exact schema/count leaks, and the semantic "too-precise / hallucinated" judgement
    is deferred to GF-2c's independent-AI fidelity gate.
    """

    source_locator: str = ""  # api-model-self-research://<provider>/<model>
    provider_id: str = ""
    model_id: str = ""
    web_search_citations: list[WebSearchCitation] = Field(default_factory=list)
    low_trust: bool = True
    content_digest: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CoarseScaleFactDraft(BaseModel):
    """A loose coarse scale fact a model/agent drafts (host stamps id + source-backing)."""

    model_config = ConfigDict(extra="forbid")

    quantity_kind: str = ""
    value_text: str = ""


class CoarseFactsModelOutput(BaseModel):
    """SDK-facing loose coarse output shape (Source C's structured-output target).

    A frontier model self-researches into this loose shape (coarse story fields + loose scale-fact
    drafts, no provenance / no scale-fact source ids); the host then stamps provenance and runs the
    shared import firewall to produce a strict ``CoarseModelResearchFacts``. This mirrors how the
    Source-B agent writes loose YAML that the host firewalls + stamps.
    """

    model_config = ConfigDict(extra="forbid")

    modalities: list[str] = Field(default_factory=list)
    broad_scale: str = ""
    coarse_structure: str = ""
    task_or_design: str = ""
    spatial_or_anatomical_coverage: str = ""
    standardization: str = ""
    major_variables: list[str] = Field(default_factory=list)
    known_coarse_limitations: list[str] = Field(default_factory=list)
    scale_facts: list[CoarseScaleFactDraft] = Field(default_factory=list)


class CoarseExploreRunResult(BaseModel):
    """What a runner's coarse ``explore()`` witnessed: the artifact + safety attestations.

    Parallel to ``AgentRunResult`` but for the branch-free coarse path: one coarse facts artifact
    instead of ``evidence[] + terminal plan/rejection``. The host stamps the coarse facts' provenance
    from this result; the transcript + digests are the audit trail.
    """

    model_config = ConfigDict(extra="forbid")

    artifact_path: str
    transcript_path: str
    explorer_adapter: str
    explorer_identity: str
    inspection_runtime: str = ""
    source_tree_before_digest: str = ""
    source_tree_after_digest: str = ""
    blocked_actions_checked: list[str] = Field(default_factory=list)
    usage: CodingAgentRunUsage | None = None

    @field_validator("artifact_path", "transcript_path", "explorer_adapter", "explorer_identity")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("CoarseExploreRunResult identity/path fields must be non-empty")
        return value
