from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ...assets import resolve_asset
from ...io import dump_data
from ...provenance import sha256_file, stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas._r5_firewall import assert_proposal_safe_payload
from ...schemas.dataset_narrative import (
    DatasetNarrative,
    DatasetNarrativeReviewStatus,
    DatasetNarrativeScaleFact,
    DatasetNarrativeSourceRef,
    DatasetNarrativeSourceType,
)
from ..agents.promotion import assert_promoted_status_is_holdable
from .evidence_requests import (
    R5ContextEvidenceRequest,
    R5ContextEvidenceRequestKind,
)
from .review_gates import (
    ArtifactGateStatus,
    gate_dataset_narrative_review_item,
)

DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION = "dataset_narrative_extractor/v5"

DATASET_NARRATIVE_REQUIRED_EVIDENCE_FIELDS = [
    "scientific_purpose",
    "population",
    "task_or_design",
    "modalities",
    "broad_scale",
    "spatial_or_anatomical_coverage",
    "temporal_structure",
    "standardization",
    "hierarchical_structure",
    "broad_interventions",
    "major_variables",
    "reuse_opportunities",
    "known_high_level_limitations",
]


class ContextReviewStatus(StrEnum):
    DRAFT = "draft"
    NEEDS_REVISION = "needs_revision"
    EXPERT_REVIEWED = "expert_reviewed"
    REJECTED = "rejected"


class ProposalSourceExcerpt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_type: DatasetNarrativeSourceType
    title: str
    locator: str
    excerpt: str
    source_digest: str = ""
    section: str = ""
    page: int | None = Field(default=None, ge=1)
    excerpt_digest: str = ""
    snippet_kind: str = "source_excerpt"
    is_metadata_only: bool = False

    @field_validator("source_id", "locator", "excerpt")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ProposalSourceExcerpt core fields must be non-empty")
        return value

    @model_validator(mode="after")
    def enforce_proposal_safety(self) -> ProposalSourceExcerpt:
        if not self.excerpt_digest:
            self.excerpt_digest = stable_hash(
                {
                    "source_id": self.source_id,
                    "section": self.section,
                    "page": self.page,
                    "excerpt": self.excerpt,
                }
            )
        assert_proposal_safe_payload(
            self.model_dump(mode="python"), context="ProposalSourceExcerpt"
        )
        return self


class DatasetNarrativeSourcePacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    packet_id: str
    dataset_id: str
    source_excerpts: list[ProposalSourceExcerpt] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_packet_digest: str

    @field_validator("packet_id", "dataset_id", "source_packet_digest")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DatasetNarrativeSourcePacket identifiers must be non-empty")
        return value

    @model_validator(mode="after")
    def enforce_packet_safety(self) -> DatasetNarrativeSourcePacket:
        if not self.source_excerpts:
            raise ValueError("DatasetNarrativeSourcePacket requires source excerpts")
        assert_proposal_safe_payload(
            self.model_dump(mode="python"),
            context="DatasetNarrativeSourcePacket",
        )
        expected = dataset_source_packet_digest(
            {
                "dataset_id": self.dataset_id,
                "source_excerpts": [item.model_dump(mode="json") for item in self.source_excerpts],
            }
        )
        if self.source_packet_digest != expected:
            raise ValueError("source_packet_digest does not match source packet contents")
        return self


class DatasetSourceBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    section: str = ""
    page: int | None = None
    quote: str
    excerpt_digest: str = ""


class DatasetFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_id: str
    field: str
    claim_text: str
    source_bindings: list[DatasetSourceBinding] = Field(default_factory=list)
    support_status: str = "supported"
    proposal_safe: bool = True


class DatasetNarrativeFieldEvidenceOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    source_ids: list[str] = Field(default_factory=list)


class DatasetNarrativeModelOutput(BaseModel):
    """Provider-facing DatasetNarrative shape without free-form dict fields."""

    model_config = ConfigDict(extra="forbid")

    dataset_narrative_id: str
    dataset_id: str
    title: str
    scientific_purpose: str
    population: str
    task_or_design: str
    modalities: list[str] = Field(default_factory=list)
    broad_scale: str = ""
    spatial_or_anatomical_coverage: str = ""
    temporal_structure: str = ""
    standardization: str = ""
    hierarchical_structure: list[str] = Field(default_factory=list)
    broad_interventions: list[str] = Field(default_factory=list)
    major_variables: list[str] = Field(default_factory=list)
    reuse_opportunities: list[str] = Field(default_factory=list)
    known_high_level_limitations: list[str] = Field(default_factory=list)
    scale_facts: list[DatasetNarrativeScaleFact] = Field(default_factory=list)
    field_evidence_source_ids: list[DatasetNarrativeFieldEvidenceOutput] = Field(
        default_factory=list
    )
    source_refs: list[DatasetNarrativeSourceRef] = Field(default_factory=list)
    review_status: DatasetNarrativeReviewStatus = DatasetNarrativeReviewStatus.DRAFT


class DatasetNarrativeDraftBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundle_id: str
    dataset_id: str
    source_packet: DatasetNarrativeSourcePacket
    local_narrative: DatasetNarrative
    gpt_narrative: DatasetNarrative
    recommended_narrative: DatasetNarrative
    prompt_version: str = DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION
    provider_id: str = ""
    model_id: str = ""
    input_digest: str
    field_evidence_source_ids: dict[str, list[str]] = Field(default_factory=dict)
    dataset_facts: list[DatasetFact] = Field(default_factory=list)
    evidence_requests: list[R5ContextEvidenceRequest] = Field(default_factory=list)
    auto_flags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def force_draft_outputs(self) -> DatasetNarrativeDraftBundle:
        if self.prompt_version != DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION:
            raise ValueError("DatasetNarrative draft bundle uses stale prompt version")
        for narrative in [self.local_narrative, self.gpt_narrative, self.recommended_narrative]:
            if narrative.review_status != DatasetNarrativeReviewStatus.DRAFT:
                raise ValueError("DatasetNarrative draft bundle can only contain draft narratives")
            _validate_source_refs(narrative, self.source_packet)
            _validate_field_evidence_source_ids(narrative, self.source_packet)
            _validate_scale_fact_source_ids(narrative, self.source_packet)
        _validate_field_evidence_map(self.field_evidence_source_ids, self.source_packet)
        return self


class DatasetNarrativeReviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: str
    bundle_id: str
    dataset_id: str
    source_packet: DatasetNarrativeSourcePacket | None = None
    recommended_narrative: DatasetNarrative
    local_narrative: DatasetNarrative
    gpt_narrative: DatasetNarrative
    prompt_version: str = ""
    provider_id: str = ""
    model_id: str = ""
    input_digest: str = ""
    source_packet_digest: str = ""
    field_evidence_source_ids: dict[str, list[str]] = Field(default_factory=dict)
    dataset_facts: list[DatasetFact] = Field(default_factory=list)
    evidence_requests: list[R5ContextEvidenceRequest] = Field(default_factory=list)
    auto_flags: list[str] = Field(default_factory=list)


class DatasetNarrativeReviewPack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: str
    items: list[DatasetNarrativeReviewItem] = Field(default_factory=list)


class DatasetNarrativeReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: str
    dataset_id: str
    status: ContextReviewStatus = ContextReviewStatus.DRAFT
    reviewer: str = ""
    notes: str = ""
    required_changes: list[str] = Field(default_factory=list)
    evidence_request_waivers: list[str] = Field(default_factory=list)
    reviewed_at: datetime | None = None

    @model_validator(mode="after")
    def enforce_decision_metadata(self) -> DatasetNarrativeReviewDecision:
        if self.status == ContextReviewStatus.DRAFT:
            return self
        if not self.reviewer.strip():
            raise ValueError("non-draft DatasetNarrative review requires reviewer")
        if not self.notes.strip():
            raise ValueError("non-draft DatasetNarrative review requires notes")
        if self.status == ContextReviewStatus.EXPERT_REVIEWED and self.required_changes:
            raise ValueError("expert-reviewed DatasetNarrative cannot have required_changes")
        if self.status == ContextReviewStatus.NEEDS_REVISION and not self.required_changes:
            raise ValueError("needs_revision DatasetNarrative review requires required_changes")
        if self.reviewed_at is None:
            self.reviewed_at = datetime.now(UTC)
        return self


class DatasetNarrativeReviewDecisionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_batch_id: str
    pack_id: str
    expert_reviewer: str = ""
    decisions: list[DatasetNarrativeReviewDecision] = Field(default_factory=list)


class DatasetNarrativeImportResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted_narratives: list[DatasetNarrative] = Field(default_factory=list)
    rejected_dataset_ids: list[str] = Field(default_factory=list)
    unresolved_dataset_ids: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


def dataset_source_packet_digest(value: dict) -> str:
    return stable_hash(value)


def build_dataset_narrative_source_packet(
    *,
    dataset_id: str,
    source_excerpts: list[ProposalSourceExcerpt],
) -> DatasetNarrativeSourcePacket:
    payload = {
        "dataset_id": dataset_id,
        "source_excerpts": [item.model_dump(mode="json") for item in source_excerpts],
    }
    digest = dataset_source_packet_digest(payload)
    return DatasetNarrativeSourcePacket(
        packet_id=f"dataset-source-packet-{dataset_id}-{digest[:12]}",
        dataset_id=dataset_id,
        source_excerpts=source_excerpts,
        source_packet_digest=digest,
    )


def build_dataset_narrative_draft_bundle(
    *,
    provider: StructuredModelProvider,
    source_packet: DatasetNarrativeSourcePacket,
    max_prompt_chars: int = 250_000,
) -> DatasetNarrativeDraftBundle:
    """DEPRECATED: the legacy A-only single-model draft → human-review-pack path.

    The serious product path is now the fusing narrator
    (``services/narrative_sources/narrator.py``) → independent-AI fidelity gate →
    ``narrative_persistence.promote_narrator_result_to_reviewed`` (automated-default authority). This
    draft-bundle + review-pack surface is retained only as a compatibility/provenance surface for the
    older human-review flow; do not build new serious narratives on it.
    """
    user_packet = {
        "prompt_version": DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION,
        "dataset_id": source_packet.dataset_id,
        "allowed_source_ids": [item.source_id for item in source_packet.source_excerpts],
        "source_excerpts": [item.model_dump(mode="json") for item in source_packet.source_excerpts],
        "required_field_evidence": DATASET_NARRATIVE_REQUIRED_EVIDENCE_FIELDS,
        "required_scale_fact_topics": [
            "subjects or mice",
            "sessions if publicly source-backed",
            "trials if publicly source-backed",
            "probes or insertions",
            "neurons or units",
            "laboratories",
            "brain areas",
            "task structure",
            "behavior/video/movement measurements",
            "public access and hierarchy",
        ],
        "instructions": {
            "review_status": "draft",
            "proposal_stage": True,
            "field_level_evidence_required": True,
            "scale_facts_require_source_ids": True,
            "metadata_only_sources_cannot_support_substantive_fields": True,
            "do_not_include": [
                "exact columns",
                "table schemas",
                "joint coverage",
                "capability registry",
                "operator receipts",
                "QBench",
                "confirmation outcomes",
                "QuestionCard",
                "AnalysisContract",
            ],
        },
    }
    user_prompt = json.dumps(user_packet, sort_keys=True, ensure_ascii=False)
    if len(user_prompt) > max_prompt_chars:
        raise ValueError("dataset narrative source packet exceeds prompt budget")
    gpt_output = provider.generate_structured(
        system_prompt=_load_prompt(DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION),
        user_prompt=user_prompt,
        output_model=DatasetNarrativeModelOutput,
    )
    gpt_narrative = _dataset_narrative_from_model_output(gpt_output)
    gpt_narrative = _force_draft(gpt_narrative, source_packet)
    # GF-2c removed this draft bundle's old in-process dataset-specific "local narrative" track; the
    # deprecated bundle is now an A-source-only draft (the recommended narrative IS the extractor
    # draft). Source B is the generic agent path (unwired in v0.1), and the serious fusion + fidelity
    # gate is the new narrator. local_narrative mirrors the draft so the legacy bundle + human-review-pack
    # surface stays intact.
    recommended = gpt_narrative.model_copy(
        update={
            "dataset_narrative_id": f"dataset-narrative-recommended-{source_packet.dataset_id}"
        },
        deep=True,
    )
    # Generic packet-derived provenance formerly supplied by the deleted local track (all
    # dataset-agnostic): source refs for every packet excerpt + keyword-inferred field evidence,
    # unioned with the extractor's own refs/evidence so the human-review import stays supportable.
    merged_refs: dict[str, DatasetNarrativeSourceRef] = {}
    for ref in (
        *gpt_narrative.source_refs,
        *(_source_ref_from_excerpt(item) for item in source_packet.source_excerpts),
    ):
        existing = merged_refs.get(ref.source_id)
        if existing is None or (ref.reviewed and not existing.reviewed):
            merged_refs[ref.source_id] = ref  # prefer a reviewed ref over an unreviewed one
    recommended.source_refs = [merged_refs[key] for key in sorted(merged_refs)]
    inferred = _infer_field_evidence(source_packet)
    field_evidence: dict[str, list[str]] = {}
    for field in {*gpt_narrative.field_evidence_source_ids, *inferred}:
        merged = _dedupe_strings(
            [*gpt_narrative.field_evidence_source_ids.get(field, []), *inferred.get(field, [])]
        )
        if merged:
            field_evidence[field] = merged
    recommended.field_evidence_source_ids = field_evidence
    dataset_facts = extract_dataset_facts(
        recommended,
        source_packet=source_packet,
        field_evidence=field_evidence,
    )
    evidence_requests = build_dataset_context_evidence_requests(source_packet, field_evidence)
    input_digest = stable_hash(user_packet)
    return DatasetNarrativeDraftBundle(
        bundle_id=f"dataset-narrative-draft-{source_packet.dataset_id}-{input_digest[:12]}",
        dataset_id=source_packet.dataset_id,
        source_packet=source_packet,
        local_narrative=gpt_narrative,
        gpt_narrative=gpt_narrative,
        recommended_narrative=recommended,
        provider_id=provider.provider_id,
        model_id=getattr(provider, "model_name", ""),
        input_digest=input_digest,
        field_evidence_source_ids=field_evidence,
        dataset_facts=dataset_facts,
        evidence_requests=evidence_requests,
        auto_flags=_bundle_flags(gpt_narrative, gpt_narrative, source_packet),
    )


def extract_dataset_facts(
    narrative: DatasetNarrative,
    *,
    source_packet: DatasetNarrativeSourcePacket,
    field_evidence: dict[str, list[str]],
) -> list[DatasetFact]:
    source_by_id = {source.source_id: source for source in source_packet.source_excerpts}
    facts: list[DatasetFact] = []
    for field in DATASET_NARRATIVE_REQUIRED_EVIDENCE_FIELDS:
        claim_text = _dataset_field_claim_text(narrative, field)
        if not claim_text:
            continue
        bindings: list[DatasetSourceBinding] = []
        support_status = "unsupported"
        for source_id in field_evidence.get(field, []):
            source = source_by_id.get(source_id)
            if source is None:
                continue
            bindings.append(
                DatasetSourceBinding(
                    source_id=source.source_id,
                    section=source.section,
                    page=source.page,
                    quote=source.excerpt[:500],
                    excerpt_digest=source.excerpt_digest,
                )
            )
        if bindings:
            support_status = (
                "metadata_only"
                if all(source_by_id[binding.source_id].is_metadata_only for binding in bindings)
                else "supported"
            )
        facts.append(
            DatasetFact(
                fact_id=f"dataset-fact-{field}",
                field=field,
                claim_text=claim_text,
                source_bindings=bindings,
                support_status=support_status,
                proposal_safe=True,
            )
        )
    return facts


def _dataset_narrative_from_model_output(output: DatasetNarrativeModelOutput) -> DatasetNarrative:
    payload = output.model_dump(mode="python")
    payload["field_evidence_source_ids"] = {
        item.field: item.source_ids for item in output.field_evidence_source_ids
    }
    return DatasetNarrative(**payload)


def _dataset_field_claim_text(narrative: DatasetNarrative, field: str) -> str:
    value = getattr(narrative, field, "")
    if isinstance(value, list):
        return "; ".join(str(item) for item in value if str(item).strip())
    return str(value or "").strip()


def prepare_dataset_narrative_review(
    bundle: DatasetNarrativeDraftBundle,
) -> tuple[DatasetNarrativeReviewPack, DatasetNarrativeReviewDecisionBatch, str]:
    review_id = f"review-{bundle.bundle_id}"
    pack = DatasetNarrativeReviewPack(
        pack_id=f"dataset-narrative-review-{stable_hash(bundle)[:12]}",
        items=[
            DatasetNarrativeReviewItem(
                review_id=review_id,
                bundle_id=bundle.bundle_id,
                dataset_id=bundle.dataset_id,
                source_packet=bundle.source_packet,
                recommended_narrative=bundle.recommended_narrative,
                local_narrative=bundle.local_narrative,
                gpt_narrative=bundle.gpt_narrative,
                prompt_version=bundle.prompt_version,
                provider_id=bundle.provider_id,
                model_id=bundle.model_id,
                input_digest=bundle.input_digest,
                source_packet_digest=bundle.source_packet.source_packet_digest,
                field_evidence_source_ids=bundle.field_evidence_source_ids,
                dataset_facts=bundle.dataset_facts,
                evidence_requests=bundle.evidence_requests,
                auto_flags=bundle.auto_flags,
            )
        ],
    )
    decisions = DatasetNarrativeReviewDecisionBatch(
        decision_batch_id=f"{pack.pack_id}-decisions-template",
        pack_id=pack.pack_id,
        decisions=[
            DatasetNarrativeReviewDecision(
                review_id=review_id,
                dataset_id=bundle.dataset_id,
            )
        ],
    )
    return pack, decisions, render_dataset_narrative_review_markdown(pack)


def import_dataset_narrative_review_decisions(
    *,
    pack: DatasetNarrativeReviewPack,
    decisions: DatasetNarrativeReviewDecisionBatch,
    require_complete: bool = True,
) -> DatasetNarrativeImportResult:
    by_review_id = {item.review_id: item for item in pack.items}
    decision_by_review_id = {decision.review_id: decision for decision in decisions.decisions}
    errors: list[str] = []
    accepted: list[DatasetNarrative] = []
    rejected: list[str] = []
    unresolved: list[str] = []
    if require_complete:
        missing = sorted(set(by_review_id) - set(decision_by_review_id))
        if missing:
            errors.append("Missing DatasetNarrative review decisions: " + ", ".join(missing))
    for review_id, item in by_review_id.items():
        decision = decision_by_review_id.get(review_id)
        if decision is None:
            unresolved.append(item.dataset_id)
            continue
        if decision.status == ContextReviewStatus.EXPERT_REVIEWED:
            import_errors = _dataset_narrative_serious_import_errors(item, decision)
            if import_errors:
                errors.extend(import_errors)
                unresolved.append(item.dataset_id)
                continue
            narrative = item.recommended_narrative.model_copy(deep=True)
            narrative.review_status = DatasetNarrativeReviewStatus.EXPERT_REVIEWED
            assert_promoted_status_is_holdable(
                narrative, expected_gate="dataset_narrative_expert_import"
            )
            narrative.dataset_narrative_id = f"dataset-narrative-{item.dataset_id}-expert-reviewed"
            narrative.field_evidence_source_ids = item.field_evidence_source_ids
            narrative.prompt_version = item.prompt_version
            narrative.provider_id = item.provider_id
            narrative.model_id = item.model_id
            narrative.input_digest = item.input_digest
            narrative.source_packet_digest = item.source_packet_digest
            narrative.dossier_digest = stable_hash(item)
            narrative.reviewed_at = decision.reviewed_at
            narrative.expert_reviewer = decision.reviewer
            narrative.review_notes = decision.notes
            accepted.append(narrative)
        elif decision.status == ContextReviewStatus.REJECTED:
            rejected.append(item.dataset_id)
        else:
            unresolved.append(item.dataset_id)
            if require_complete:
                errors.append(
                    f"DatasetNarrative decision for {item.dataset_id} remains {decision.status}"
                )
    return DatasetNarrativeImportResult(
        accepted_narratives=accepted,
        rejected_dataset_ids=rejected,
        unresolved_dataset_ids=unresolved,
        errors=errors,
    )


def write_dataset_narrative_review_outputs(
    bundle: DatasetNarrativeDraftBundle,
    *,
    corpus_root: str | Path = "corpus",
) -> dict[str, Path]:
    root = Path(corpus_root) / "context" / "dataset_narratives"
    source_path = dump_data(
        bundle.source_packet,
        root / "sources" / f"{bundle.dataset_id}.dataset_source_packet.yaml",
    )
    draft_path = dump_data(
        bundle, root / "drafts" / f"{bundle.dataset_id}.dataset_narrative_draft.yaml"
    )
    pack, decisions, markdown = prepare_dataset_narrative_review(bundle)
    review_root = root / "review"
    pack_path = dump_data(pack, review_root / "dataset_narrative_review_pack.yaml")
    template_path = dump_data(
        decisions,
        review_root / "dataset_narrative_decisions.template.yaml",
    )
    decision_path = dump_data(decisions, review_root / "dataset_narrative_decisions.yaml")
    markdown_path = review_root / "dataset_narrative_review.md"
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown, encoding="utf-8")
    dossier_markdown_path = review_root / "dataset_dossier_review.md"
    dossier_markdown_path.write_text(
        render_dataset_dossier_review_markdown(pack),
        encoding="utf-8",
    )
    return {
        "source_packet": source_path,
        "draft": draft_path,
        "review_pack": pack_path,
        "decision_template": template_path,
        "decisions": decision_path,
        "markdown": markdown_path,
        "dossier_markdown": dossier_markdown_path,
    }


def write_reviewed_dataset_narratives(
    narratives: list[DatasetNarrative],
    *,
    corpus_root: str | Path = "corpus",
) -> list[Path]:
    root = Path(corpus_root) / "context" / "dataset_narratives"
    return [
        dump_data(narrative, root / f"{narrative.dataset_id}.dataset_narrative.yaml")
        for narrative in narratives
    ]


def render_dataset_narrative_review_markdown(pack: DatasetNarrativeReviewPack) -> str:
    lines = [
        "# Dataset Narrative Review",
        "",
        (
            "Accept only if the recommended narrative is broad, source-backed, "
            "proposal-safe, and rich enough to support Question Scientist context."
        ),
        "",
    ]
    for item in pack.items:
        narrative = item.recommended_narrative
        excerpt_by_id = {
            excerpt.source_id: excerpt
            for excerpt in (item.source_packet.source_excerpts if item.source_packet else [])
        }
        lines.extend(
            [
                f"## {item.dataset_id}",
                "",
                f"- Review ID: `{item.review_id}`",
                f"- Prompt version: `{item.prompt_version or 'unknown'}`",
                f"- Auto flags: {', '.join(item.auto_flags) if item.auto_flags else 'none'}",
                "",
                "### Evidence Coverage",
                "",
                *[
                    _render_dataset_field_evidence(field, item, excerpt_by_id)
                    for field in DATASET_NARRATIVE_REQUIRED_EVIDENCE_FIELDS
                ],
                "",
                "### Recommended Narrative",
                "",
                f"- Title: {narrative.title}",
                f"- Scientific purpose: {narrative.scientific_purpose}",
                f"- Population: {narrative.population}",
                f"- Task/design: {narrative.task_or_design}",
                f"- Modalities: {', '.join(narrative.modalities)}",
                f"- Broad scale: {narrative.broad_scale}",
                f"- Spatial/anatomical coverage: {narrative.spatial_or_anatomical_coverage}",
                f"- Temporal structure: {narrative.temporal_structure}",
                f"- Standardization: {narrative.standardization}",
                f"- Hierarchical structure: {', '.join(narrative.hierarchical_structure)}",
                f"- Broad interventions: {', '.join(narrative.broad_interventions)}",
                f"- Major variables: {', '.join(narrative.major_variables)}",
                f"- Reuse opportunities: {'; '.join(narrative.reuse_opportunities)}",
                f"- High-level limitations: {'; '.join(narrative.known_high_level_limitations)}",
                "",
                "### Source-Backed Scale Facts",
                "",
                *_render_dataset_scale_fact_table(narrative.scale_facts, excerpt_by_id),
                "",
                "### Recommended Source Refs",
            ]
        )
        for ref in narrative.source_refs:
            section = f" ({ref.section})" if ref.section else ""
            quote = f" — {ref.quote_or_span[:220]}" if ref.quote_or_span else ""
            lines.append(f"- `{ref.source_id}` {ref.title or ref.locator}{section}{quote}")
        lines.extend(
            [
                "",
                "### Source Packet Appendix",
                "",
            ]
        )
        if item.source_packet is None:
            lines.append("- Source packet not embedded in this review pack.")
        else:
            lines.extend(
                _render_dataset_source_excerpt(excerpt)
                for excerpt in item.source_packet.source_excerpts
            )
        lines.append("")
    return "\n".join(lines)


def render_dataset_dossier_review_markdown(pack: DatasetNarrativeReviewPack) -> str:
    lines = [
        "# Dataset Dossier Review",
        "",
        (
            "This is the main human-readable dataset review surface. It is intentionally "
            "less mechanical than the field evidence table, but every substantive fact "
            "must still be backed by source IDs or reviewer waiver."
        ),
        "",
        (
            "Proposal-safe inspiration is allowed here. Exact columns, joint coverage, "
            "capability registries, QBench, confirmation outcomes, QuestionCards, and "
            "AnalysisContracts remain planner/bridge-stage material and must not enter."
        ),
        "",
    ]
    for item in pack.items:
        narrative = item.recommended_narrative
        gate = gate_dataset_narrative_review_item(item)
        excerpt_by_id = {
            excerpt.source_id: excerpt
            for excerpt in (item.source_packet.source_excerpts if item.source_packet else [])
        }
        lines.extend(
            [
                f"## {item.dataset_id}",
                "",
                "## Artifact Status",
                "",
                f"**{gate.status.value.upper()}**",
                "",
                "### Blocking Reasons",
                "",
                *_render_dataset_gate_list(
                    gate.reasons,
                    empty="- No blocking reasons recorded.",
                ),
                "",
                "### Reviewer Action Checklist",
                "",
                *_render_dataset_gate_list(
                    gate.action_items,
                    empty="- No gate actions required.",
                ),
                "",
                f"- Review ID: `{item.review_id}`",
                f"- Prompt version: `{item.prompt_version or 'unknown'}`",
                f"- Provider/model: `{item.provider_id or 'unknown'}` / `{item.model_id or 'unknown'}`",
                f"- Source packet digest: `{item.source_packet_digest or 'missing'}`",
                f"- Auto flags: {', '.join(item.auto_flags) if item.auto_flags else 'none'}",
                "",
                "## Dataset Story",
                "",
                f"### Scientific purpose {_field_source_badge('scientific_purpose', item)}",
                "",
                narrative.scientific_purpose,
                "",
                f"### Release and public-access context {_field_source_badge('standardization', item)}",
                "",
                narrative.standardization,
                "",
                f"### Population {_field_source_badge('population', item)}",
                "",
                narrative.population,
                "",
                f"### Task structure {_field_source_badge('task_or_design', item)}",
                "",
                narrative.task_or_design,
                "",
                f"### Sensory, motor, and cognitive components {_field_source_badge('major_variables', item)}",
                "",
                "; ".join(narrative.major_variables) or "Not yet specified.",
                "",
                f"### Broad source-backed scale {_field_source_badge('broad_scale', item)}",
                "",
                narrative.broad_scale or "Not yet specified.",
                "",
                "### Scale and dataset structure facts",
                "",
                *_render_dataset_scale_fact_table(narrative.scale_facts, excerpt_by_id),
                "",
                f"### Recording modalities {_field_source_badge('modalities', item)}",
                "",
                ", ".join(narrative.modalities) or "Not yet specified.",
                "",
                f"### Anatomical scope {_field_source_badge('spatial_or_anatomical_coverage', item)}",
                "",
                narrative.spatial_or_anatomical_coverage or "Not yet specified.",
                "",
                f"### Temporal and trial structure {_field_source_badge('temporal_structure', item)}",
                "",
                narrative.temporal_structure or "Not yet specified.",
                "",
                f"### Reuse opportunities {_field_source_badge('reuse_opportunities', item)}",
                "",
                *_render_dataset_list(narrative.reuse_opportunities),
                "",
                f"### Known limitations {_field_source_badge('known_high_level_limitations', item)}",
                "",
                *_render_dataset_list(narrative.known_high_level_limitations),
                "",
                "## Proposal-Safe Inspiration vs Planner-Stage Feasibility",
                "",
                (
                    "This dossier may inspire broad question formation from source-backed "
                    "dataset descriptions. It does not certify exact variables, joins, "
                    "region coverage, sample sizes for a proposed contrast, executor skills, "
                    "or statistical feasibility. Those checks belong to isolated planning "
                    "branches after QuestionSeed generation."
                ),
                "",
                "## Evidence Requests",
                "",
                *_render_dataset_evidence_requests(item.evidence_requests),
                "",
                "## Dataset Fact Table",
                "",
                *_render_dataset_fact_table(item.dataset_facts),
                "",
                "## Field Evidence Index",
                "",
                *[
                    _render_dataset_field_evidence(field, item, excerpt_by_id)
                    for field in DATASET_NARRATIVE_REQUIRED_EVIDENCE_FIELDS
                ],
                "",
                "## Source Appendix",
                "",
            ]
        )
        if item.source_packet is None:
            lines.append("- Source packet not embedded in this review pack.")
        else:
            for excerpt in item.source_packet.source_excerpts:
                lines.extend(
                    [
                        f"### `{excerpt.source_id}`",
                        "",
                        f"- Title: {excerpt.title}",
                        f"- Type: {excerpt.source_type.value}",
                        f"- Section/page: {excerpt.section or 'unknown'}"
                        + (f", p. {excerpt.page}" if excerpt.page else ""),
                        f"- Metadata-only: {'yes' if excerpt.is_metadata_only else 'no'}",
                        "",
                        excerpt.excerpt.strip(),
                        "",
                    ]
                )
    return "\n".join(lines)


def build_dataset_context_evidence_requests(
    source_packet: DatasetNarrativeSourcePacket,
    field_evidence: dict[str, list[str]],
) -> list[R5ContextEvidenceRequest]:
    requests: list[R5ContextEvidenceRequest] = []
    source_by_id = {source.source_id: source for source in source_packet.source_excerpts}
    for field in DATASET_NARRATIVE_REQUIRED_EVIDENCE_FIELDS:
        source_ids = field_evidence.get(field, [])
        if not source_ids:
            requests.append(
                R5ContextEvidenceRequest(
                    request_id=f"dataset-evidence-request-{source_packet.dataset_id}-{field}",
                    kind=R5ContextEvidenceRequestKind.NEED_DATASET_DETAIL_FROM_PUBLIC_DOCS,
                    target_dataset_field=field,
                    description=(
                        "Need explicit source-backed public-document or dataset-paper evidence "
                        f"for DatasetNarrative field `{field}`."
                    ),
                    blocking=True,
                )
            )
            continue
        if all(
            source_by_id.get(source_id) and source_by_id[source_id].is_metadata_only
            for source_id in source_ids
        ):
            requests.append(
                R5ContextEvidenceRequest(
                    request_id=f"dataset-evidence-request-{source_packet.dataset_id}-{field}-metadata-only",
                    kind=R5ContextEvidenceRequestKind.NEED_DATASET_DETAIL_FROM_PUBLIC_DOCS,
                    target_dataset_field=field,
                    description=(
                        f"DatasetNarrative field `{field}` is supported only by metadata-only "
                        "sources; need substantive public-doc or paper excerpt evidence."
                    ),
                    blocking=True,
                )
            )
    return requests


def _field_source_badge(field: str, item: DatasetNarrativeReviewItem) -> str:
    source_ids = item.field_evidence_source_ids.get(field, [])
    if not source_ids:
        return "`sources: missing`"
    return "`sources: " + ", ".join(source_ids) + "`"


def _render_dataset_list(values: list[str]) -> list[str]:
    if not values:
        return ["- Not yet specified."]
    return [f"- {value}" for value in values]


def _render_dataset_evidence_requests(
    requests: list[R5ContextEvidenceRequest],
) -> list[str]:
    if not requests:
        return ["- No unresolved evidence requests."]
    lines: list[str] = []
    for request in requests:
        marker = "blocking" if request.blocking else "non-blocking"
        target = (
            request.target_dataset_field or request.target_lane or request.target_source_record_id
        )
        lines.append(
            f"- `{request.request_id}` [{request.kind.value}; {marker}; target `{target}`] "
            f"{request.description}"
        )
    return lines


def _render_dataset_fact_table(facts: list[DatasetFact]) -> list[str]:
    if not facts:
        return ["- No dataset facts extracted from field evidence."]
    lines = [
        "| Fact ID | Field | Claim | Support | Evidence quotes |",
        "|---|---|---|---|---|",
    ]
    for fact in facts:
        quotes = "<br>".join(
            f"`{binding.source_id}`"
            + (f" {binding.section}" if binding.section else "")
            + f": {_markdown_table_cell(binding.quote[:180])}"
            for binding in fact.source_bindings[:3]
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{fact.fact_id}`",
                    f"`{fact.field}`",
                    _markdown_table_cell(fact.claim_text[:220]),
                    fact.support_status,
                    quotes or "missing",
                ]
            )
            + " |"
        )
    return lines


def _render_dataset_scale_fact_table(
    scale_facts: list[DatasetNarrativeScaleFact],
    excerpt_by_id: dict[str, ProposalSourceExcerpt],
) -> list[str]:
    if not scale_facts:
        return ["- No source-backed scale facts extracted yet."]
    lines = [
        "| Fact ID | Kind | Value | Source support | Proposal status |",
        "|---|---|---|---|---|",
    ]
    for fact in scale_facts:
        sources = []
        for source_id in fact.source_ids:
            excerpt = excerpt_by_id.get(source_id)
            if excerpt is None:
                sources.append(f"`{source_id}`")
                continue
            location = excerpt.section or excerpt.locator
            if excerpt.page:
                location = f"{location}, p. {excerpt.page}" if location else f"p. {excerpt.page}"
            sources.append(f"`{source_id}` ({location})")
        status = "planner-stage only" if fact.planner_stage_only else "proposal-safe"
        if not fact.proposal_safe:
            status = "not proposal-safe"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{fact.scale_fact_id}`",
                    f"`{fact.quantity_kind}`",
                    _markdown_table_cell(fact.value_text),
                    "<br>".join(sources) or "missing",
                    status,
                ]
            )
            + " |"
        )
    return lines


def _markdown_table_cell(value: str) -> str:
    return " ".join(value.replace("|", "/").split())


def _render_dataset_gate_list(values: list[str], *, empty: str) -> list[str]:
    if not values:
        return [empty]
    return [f"- {value}" for value in values]


def _render_dataset_field_evidence(
    field: str,
    item: DatasetNarrativeReviewItem,
    excerpt_by_id: dict[str, ProposalSourceExcerpt],
) -> str:
    source_ids = item.field_evidence_source_ids.get(field, [])
    if not source_ids:
        return f"- `{field}`: MISSING"
    details = []
    for source_id in source_ids:
        excerpt = excerpt_by_id.get(source_id)
        if excerpt is None:
            details.append(f"`{source_id}`")
            continue
        location = excerpt.section or excerpt.locator
        if excerpt.page:
            location = f"{location}, p. {excerpt.page}" if location else f"p. {excerpt.page}"
        marker = "metadata-only" if excerpt.is_metadata_only else excerpt.snippet_kind
        details.append(f"`{source_id}` ({location}; {marker})")
    return f"- `{field}`: " + "; ".join(details)


def _render_dataset_source_excerpt(excerpt: ProposalSourceExcerpt) -> str:
    page = f", p. {excerpt.page}" if excerpt.page else ""
    metadata = "yes" if excerpt.is_metadata_only else "no"
    lines = [
        f"#### `{excerpt.source_id}`",
        "",
        f"- Title: {excerpt.title}",
        f"- Type: {excerpt.source_type.value}",
        f"- Locator: {excerpt.locator}",
        f"- Section/page: {excerpt.section or 'unknown'}{page}",
        f"- Snippet kind: {excerpt.snippet_kind}",
        f"- Metadata-only: {metadata}",
        f"- Excerpt digest: `{excerpt.excerpt_digest}`",
        "",
        excerpt.excerpt.strip(),
        "",
    ]
    return "\n".join(lines)


def _force_draft(
    narrative: DatasetNarrative,
    source_packet: DatasetNarrativeSourcePacket,
) -> DatasetNarrative:
    narrative = narrative.model_copy(
        update={
            "dataset_id": source_packet.dataset_id,
            "review_status": DatasetNarrativeReviewStatus.DRAFT,
        },
        deep=True,
    )
    if not narrative.field_evidence_source_ids:
        narrative.field_evidence_source_ids = _infer_field_evidence_from_refs(
            narrative, source_packet
        )
    _validate_source_refs(narrative, source_packet)
    _validate_field_evidence_source_ids(narrative, source_packet)
    _validate_scale_fact_source_ids(narrative, source_packet)
    return narrative


def _validate_source_refs(
    narrative: DatasetNarrative,
    source_packet: DatasetNarrativeSourcePacket,
) -> None:
    allowed = {item.source_id for item in source_packet.source_excerpts}
    unknown = sorted(ref.source_id for ref in narrative.source_refs if ref.source_id not in allowed)
    if unknown:
        raise ValueError("DatasetNarrative cites unknown source IDs: " + ", ".join(unknown))


def _validate_field_evidence_source_ids(
    narrative: DatasetNarrative,
    source_packet: DatasetNarrativeSourcePacket,
) -> None:
    _validate_field_evidence_map(narrative.field_evidence_source_ids, source_packet)


def _validate_scale_fact_source_ids(
    narrative: DatasetNarrative,
    source_packet: DatasetNarrativeSourcePacket,
) -> None:
    allowed = {item.source_id for item in source_packet.source_excerpts}
    unknown = sorted(
        {
            source_id
            for fact in narrative.scale_facts
            for source_id in fact.source_ids
            if source_id not in allowed
        }
    )
    if unknown:
        raise ValueError(
            "DatasetNarrative scale facts cite unknown source IDs: " + ", ".join(unknown)
        )


def _validate_field_evidence_map(
    field_evidence: dict[str, list[str]],
    source_packet: DatasetNarrativeSourcePacket,
) -> None:
    allowed = {item.source_id for item in source_packet.source_excerpts}
    unknown = sorted(
        {
            source_id
            for source_ids in field_evidence.values()
            for source_id in source_ids
            if source_id not in allowed
        }
    )
    if unknown:
        raise ValueError(
            "DatasetNarrative field evidence cites unknown source IDs: " + ", ".join(unknown)
        )


def _source_ref_from_excerpt(excerpt: ProposalSourceExcerpt) -> DatasetNarrativeSourceRef:
    return DatasetNarrativeSourceRef(
        source_id=excerpt.source_id,
        source_type=excerpt.source_type,
        locator=excerpt.locator,
        title=excerpt.title,
        section=excerpt.section,
        page=excerpt.page,
        quote_or_span=excerpt.excerpt[:400],
        source_digest=excerpt.source_digest or excerpt.excerpt_digest,
        reviewed=not excerpt.is_metadata_only,
    )


def _infer_field_evidence(source_packet: DatasetNarrativeSourcePacket) -> dict[str, list[str]]:
    substantive = [item for item in source_packet.source_excerpts if not item.is_metadata_only]
    if not substantive:
        return {}
    text_by_source = {
        item.source_id: " ".join([item.section, item.title, item.excerpt]).lower()
        for item in substantive
    }
    field_keywords = {
        "scientific_purpose": ["purpose", "resource", "understand", "brain-wide", "map"],
        "population": ["mouse", "mice", "animal", "subject"],
        "task_or_design": ["task", "decision", "stimulus", "choice", "feedback", "behavior"],
        "modalities": ["neuropixels", "electrophysiology", "recording", "widefield"],
        "broad_scale": ["multi", "large", "brain-wide", "laborator", "standard"],
        "spatial_or_anatomical_coverage": ["brain", "atlas", "area", "region", "anatom"],
        "temporal_structure": ["trial", "event", "time", "session"],
        "standardization": ["standard", "protocol", "public", "release", "one"],
        "hierarchical_structure": ["subject", "session", "probe", "region", "lab"],
        "broad_interventions": ["stimulus", "feedback", "choice", "contrast"],
        "major_variables": ["neural", "stimulus", "choice", "movement", "feedback"],
        "reuse_opportunities": ["reuse", "public", "resource", "available", "analysis"],
        "known_high_level_limitations": ["limitation", "caveat", "subset", "later", "available"],
    }
    evidence: dict[str, list[str]] = {}
    for field, keywords in field_keywords.items():
        matched = [
            source_id
            for source_id, text in text_by_source.items()
            if any(keyword in text for keyword in keywords)
        ]
        if matched:
            evidence[field] = matched[:4]
    return evidence


def _infer_field_evidence_from_refs(
    narrative: DatasetNarrative,
    source_packet: DatasetNarrativeSourcePacket,
) -> dict[str, list[str]]:
    return _infer_field_evidence(source_packet)


def _dataset_narrative_serious_import_errors(
    item: DatasetNarrativeReviewItem,
    decision: DatasetNarrativeReviewDecision,
) -> list[str]:
    errors: list[str] = []
    if item.prompt_version != DATASET_NARRATIVE_EXTRACTOR_PROMPT_VERSION:
        errors.append(
            "DatasetNarrative review pack uses stale prompt version: "
            f"{item.prompt_version or 'unknown'}"
        )
    gate = gate_dataset_narrative_review_item(
        item,
        waived_request_ids=set(decision.evidence_request_waivers),
    )
    if gate.status in {ArtifactGateStatus.BLOCKED, ArtifactGateStatus.FIXTURE_NOT_FOR_REVIEW}:
        errors.append(
            "DatasetNarrative review item is not serious-importable: "
            f"{gate.status.value}; " + "; ".join(gate.reasons)
        )
    if item.provider_id.startswith("mock:"):
        errors.append("DatasetNarrative serious import cannot accept mock-provider output")
    if not item.input_digest:
        errors.append("DatasetNarrative serious import requires input_digest")
    if not item.source_packet_digest:
        errors.append("DatasetNarrative serious import requires source_packet_digest")
    waived = set(decision.evidence_request_waivers)
    unresolved_blocking = [
        request.request_id
        for request in item.evidence_requests
        if request.blocking and request.request_id not in waived
    ]
    if unresolved_blocking:
        errors.append(
            "DatasetNarrative has unresolved blocking evidence requests: "
            + ", ".join(unresolved_blocking)
        )
    source_by_id = {ref.source_id: ref for ref in item.recommended_narrative.source_refs}
    if not source_by_id:
        errors.append("DatasetNarrative expert import requires source refs")
    for field in DATASET_NARRATIVE_REQUIRED_EVIDENCE_FIELDS:
        source_ids = item.field_evidence_source_ids.get(field) or []
        if not source_ids:
            errors.append(f"DatasetNarrative field lacks evidence: {field}")
            continue
        missing = [source_id for source_id in source_ids if source_id not in source_by_id]
        if missing:
            errors.append(
                f"DatasetNarrative field {field} cites sources not present in source_refs: "
                + ", ".join(missing)
            )
        unreviewed = []
        for source_id in source_ids:
            ref = source_by_id.get(source_id)
            if ref is not None and not ref.reviewed:
                unreviewed.append(source_id)
        if unreviewed:
            errors.append(
                f"DatasetNarrative field {field} is supported only by unreviewed/metadata evidence: "
                + ", ".join(unreviewed)
            )
    if not item.recommended_narrative.scale_facts:
        errors.append("DatasetNarrative expert import requires source-backed scale_facts")
    source_packet_by_id = {
        excerpt.source_id: excerpt
        for excerpt in (item.source_packet.source_excerpts if item.source_packet else [])
    }
    for fact in item.recommended_narrative.scale_facts:
        if fact.planner_stage_only or not fact.proposal_safe:
            errors.append(f"DatasetNarrative scale fact is not proposal-safe: {fact.scale_fact_id}")
        if not fact.source_ids:
            errors.append(f"DatasetNarrative scale fact lacks source IDs: {fact.scale_fact_id}")
            continue
        missing = [source_id for source_id in fact.source_ids if source_id not in source_by_id]
        if missing:
            errors.append(
                f"DatasetNarrative scale fact {fact.scale_fact_id} cites sources not present "
                "in source_refs: " + ", ".join(missing)
            )
        metadata_only = [
            source_id
            for source_id in fact.source_ids
            if source_packet_by_id.get(source_id) is not None
            and source_packet_by_id[source_id].is_metadata_only
        ]
        if metadata_only:
            errors.append(
                f"DatasetNarrative scale fact {fact.scale_fact_id} uses metadata-only support: "
                + ", ".join(metadata_only)
            )
    return errors


def _bundle_flags(
    local_narrative: DatasetNarrative,
    gpt_narrative: DatasetNarrative,
    source_packet: DatasetNarrativeSourcePacket,
) -> list[str]:
    flags: list[str] = []
    if not gpt_narrative.source_refs:
        flags.append("gpt_narrative_missing_source_refs")
    if len(gpt_narrative.source_refs) < min(2, len(source_packet.source_excerpts)):
        flags.append("gpt_narrative_uses_few_sources")
    if not local_narrative.known_high_level_limitations:
        flags.append("local_narrative_missing_limitations")
    metadata_only = [
        item.source_id for item in source_packet.source_excerpts if item.is_metadata_only
    ]
    if metadata_only:
        flags.append("metadata_only_sources_present:" + ",".join(metadata_only))
    missing_fields = [
        field
        for field in DATASET_NARRATIVE_REQUIRED_EVIDENCE_FIELDS
        if not local_narrative.field_evidence_source_ids.get(field)
        and not gpt_narrative.field_evidence_source_ids.get(field)
    ]
    if missing_fields:
        flags.append("field_evidence_missing:" + ",".join(missing_fields))
    if not local_narrative.scale_facts and not gpt_narrative.scale_facts:
        flags.append("scale_facts_missing")
    nature_excerpts = [
        item
        for item in source_packet.source_excerpts
        if item.source_id.startswith("paper:ibl-brain-wide-map-2025") and not item.is_metadata_only
    ]
    if len(nature_excerpts) < 3:
        flags.append("few_substantive_nature_paper_excerpts")
    return flags


def _load_prompt(prompt_version: str) -> str:
    return resolve_asset(Path("prompts") / Path(prompt_version).with_suffix(".md")).read_text(
        encoding="utf-8"
    )


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output


def source_excerpt_from_file(
    *,
    source_id: str,
    source_type: DatasetNarrativeSourceType,
    title: str,
    locator: str,
    path: Path,
    excerpt: str,
) -> ProposalSourceExcerpt:
    return ProposalSourceExcerpt(
        source_id=source_id,
        source_type=source_type,
        title=title,
        locator=locator,
        excerpt=excerpt,
        source_digest=sha256_file(path) if path.exists() else stable_hash(excerpt),
    )
