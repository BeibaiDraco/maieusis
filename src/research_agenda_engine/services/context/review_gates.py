from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ...schemas.dataset_narrative import DatasetNarrative, DatasetNarrativeReviewStatus
from ...schemas.question_pattern import QuestionPatternCard
from ...schemas.review_authority import is_accepted_authority
from ...schemas.scientific_context import TopicEvidenceBrief


class ArtifactGateStatus(StrEnum):
    FIXTURE_NOT_FOR_REVIEW = "fixture_not_for_review"
    BLOCKED = "blocked"
    NEEDS_EVIDENCE = "needs_evidence"
    REVIEWABLE_DRAFT = "reviewable_draft"
    REVIEWED_ACCEPTED = "reviewed_accepted"
    REVIEWED_REJECTED = "reviewed_rejected"


class ArtifactGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ArtifactGateStatus
    reasons: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)

    @property
    def is_reviewable(self) -> bool:
        return self.status in {
            ArtifactGateStatus.REVIEWABLE_DRAFT,
            ArtifactGateStatus.REVIEWED_ACCEPTED,
        }


LEGACY_TOPIC_REGION_LANES = {
    "target_regions_cp_po_lp",
    "target_region_cp",
    "target_region_po",
    "target_region_lp",
}


def gate_topic_evidence_review_item(
    item: Any,
    *,
    waived_request_ids: set[str] | None = None,
) -> ArtifactGateResult:
    reasons: list[str] = []
    actions: list[str] = []
    waived_request_ids = waived_request_ids or set()
    fixture = _is_mock_provider(
        getattr(item, "provider_id", ""),
        getattr(item, "model_id", ""),
    )
    if fixture:
        reasons.append("provider is mock/deterministic fixture")
        actions.append("Regenerate topic evidence with an approved non-mock API provider.")

    blocking_requests = [
        request.request_id
        for request in getattr(item, "evidence_requests", [])
        if getattr(request, "blocking", False)
        and getattr(request, "request_id", "") not in waived_request_ids
    ]
    if blocking_requests:
        reasons.append("unresolved blocking evidence requests: " + ", ".join(blocking_requests))
        actions.append("Resolve or explicitly waive blocking evidence requests before import.")

    field_state = getattr(item, "field_state_draft", None)
    if field_state is None:
        reasons.append("missing TopicFieldStateDraft")
        actions.append("Regenerate field-state synthesis from curated evidence cards.")
    elif _contains_placeholder_text(field_state):
        reasons.append("field-state draft contains placeholder/mock text")
        actions.append("Regenerate field-state synthesis; placeholder output is not reviewable.")

    r5_source_table = getattr(item, "r5_source_table", None)
    if r5_source_table is None:
        reasons.append("missing R5 topic source table")
        actions.append("Rebuild topic source table with R5 lane protocol.")
    else:
        legacy_records = [
            record.source_record_id
            for record in getattr(r5_source_table, "records", [])
            if LEGACY_TOPIC_REGION_LANES & set(getattr(record, "lane_ids", []))
        ]
        if legacy_records:
            reasons.append("legacy target-region lane present: " + ", ".join(legacy_records[:8]))
            actions.append(
                "Regenerate sources with the active geometry/noise/circuit lane protocol."
            )

    card_by_id = {
        card.source_record_id: card for card in getattr(item, "source_evidence_cards", [])
    }
    off_topic_support = [
        card.source_record_id
        for card in card_by_id.values()
        if getattr(card, "can_support_claims", False)
        and "off_topic" in set(getattr(card, "quality_flags", []))
    ]
    if off_topic_support:
        reasons.append("off-topic records are claim-supporting: " + ", ".join(off_topic_support))
        actions.append("Exclude off-topic source records from synthesis packets.")

    bad_claim_sources: list[str] = []
    brief = getattr(item, "recommended_brief", None)
    for claim in getattr(brief, "claims", []) if brief is not None else []:
        for source_id in getattr(claim, "source_record_ids", []) or getattr(
            claim, "source_refs", []
        ):
            card = card_by_id.get(source_id)
            if card is not None and not getattr(card, "can_support_claims", False):
                bad_claim_sources.append(f"{claim.claim_id}:{source_id}")
    if bad_claim_sources:
        reasons.append(
            "claims cite title/metadata/diagnostic-only sources: " + ", ".join(bad_claim_sources)
        )
        actions.append("Remove unsupported claims or fetch usable abstracts/excerpts.")

    if reasons:
        status = (
            ArtifactGateStatus.FIXTURE_NOT_FOR_REVIEW if fixture else ArtifactGateStatus.BLOCKED
        )
        return ArtifactGateResult(
            status=status, reasons=_dedupe(reasons), action_items=_dedupe(actions)
        )
    return ArtifactGateResult(status=ArtifactGateStatus.REVIEWABLE_DRAFT)


def gate_dataset_narrative_review_item(
    item: Any,
    *,
    waived_request_ids: set[str] | None = None,
) -> ArtifactGateResult:
    reasons: list[str] = []
    actions: list[str] = []
    waived_request_ids = waived_request_ids or set()
    fixture = _is_mock_provider(
        getattr(item, "provider_id", ""),
        getattr(item, "model_id", ""),
    )
    if fixture:
        reasons.append("provider is mock/deterministic fixture")
        actions.append("Regenerate dataset narrative with an approved non-mock API provider.")

    blocking_requests = [
        request.request_id
        for request in getattr(item, "evidence_requests", [])
        if getattr(request, "blocking", False)
        and getattr(request, "request_id", "") not in waived_request_ids
    ]
    if blocking_requests:
        reasons.append("unresolved blocking evidence requests: " + ", ".join(blocking_requests))
        actions.append("Resolve or explicitly waive blocking evidence requests before import.")

    source_packet = getattr(item, "source_packet", None)
    source_by_id = {
        source.source_id: source
        for source in (getattr(source_packet, "source_excerpts", []) if source_packet else [])
    }
    field_evidence = getattr(item, "field_evidence_source_ids", {}) or {}
    missing_fields = [
        field for field in _dataset_required_fields() if not field_evidence.get(field)
    ]
    if missing_fields:
        reasons.append("dataset fields lack evidence: " + ", ".join(missing_fields))
        actions.append("Add explicit field-level evidence or reviewer waivers.")

    metadata_only_fields = []
    for field, source_ids in field_evidence.items():
        if source_ids and all(
            getattr(source_by_id.get(source_id), "is_metadata_only", False)
            for source_id in source_ids
            if source_by_id.get(source_id) is not None
        ):
            metadata_only_fields.append(field)
    if metadata_only_fields:
        reasons.append(
            "metadata-only evidence supports substantive fields: "
            + ", ".join(sorted(metadata_only_fields))
        )
        actions.append("Use dataset-paper or official-doc body excerpts for substantive fields.")

    legacy_keyword_windows = [
        source.source_id
        for source in source_by_id.values()
        if getattr(source, "snippet_kind", "") == "pdf_section_window"
    ]
    if legacy_keyword_windows:
        reasons.append(
            "legacy PDF keyword windows used as section evidence: "
            + ", ".join(legacy_keyword_windows[:8])
        )
        actions.append("Regenerate source packet with section-aware PDF extraction.")

    # A former dataset-specific "widefield modality unsupported by the target dataset"
    # heuristic was removed here: it hardcoded one dataset's modality/source vocabulary and has no
    # place in a dataset-agnostic product. The narrative-vs-dataset-mismatch / unsupported-modality
    # firewall responsibility now lives on the product path in the independent-AI DatasetNarrative
    # fidelity gate (services/agents/dataset_narrative_reviewer.py: faithful/trust_harmonized criteria
    # + hallucination/unfaithful findings), backed by deterministic provenance-tracked fusion (a
    # modality only enters the fused narrative if a source contributed it). This legacy A-only
    # review-item gate no longer carries a dataset-specific modality check.

    if reasons:
        status = (
            ArtifactGateStatus.FIXTURE_NOT_FOR_REVIEW if fixture else ArtifactGateStatus.BLOCKED
        )
        return ArtifactGateResult(
            status=status, reasons=_dedupe(reasons), action_items=_dedupe(actions)
        )
    return ArtifactGateResult(status=ArtifactGateStatus.REVIEWABLE_DRAFT)


def assert_question_scientist_inputs_are_reviewed(
    *,
    paperbank_question_patterns: list[QuestionPatternCard],
    topic_literature_brief: TopicEvidenceBrief,
    dataset_narrative: DatasetNarrative,
    allow_provisional_topic: bool = False,
) -> None:
    if not paperbank_question_patterns:
        raise ValueError("Question Scientist context requires reviewed PaperBank patterns")
    # Accept either honest authority (AI_REVIEWED or EXPERT_REVIEWED) for patterns; is_proposal_ready
    # already routes through review_authority.is_accepted_authority. The TopicEvidenceBrief branch below
    # stays EXPERT-only until 5a-1b inverts the topic-evidence gate.
    unreviewed_patterns = [
        pattern.pattern_id
        for pattern in paperbank_question_patterns
        if not is_accepted_authority(pattern.review_status) or not pattern.is_proposal_ready
    ]
    if unreviewed_patterns:
        raise ValueError(
            "Question Scientist context requires reviewed accepted PatternBank entries: "
            + ", ".join(unreviewed_patterns)
        )
    # The topic-evidence gate is inverted — accept EITHER the automated independent-AI
    # verdict (AI_REVIEWED) OR the optional post-hoc human review (EXPERT_REVIEWED); still refuse
    # DRAFT / SOURCE_REVIEWED (not fidelity-gated).
    if not allow_provisional_topic and not is_accepted_authority(
        topic_literature_brief.review_status
    ):
        raise ValueError("Question Scientist context requires reviewed accepted TopicEvidenceBrief")
    if not (
        topic_literature_brief.prompt_version
        and topic_literature_brief.provider_id
        and topic_literature_brief.input_digest
        and topic_literature_brief.source_table_digest
    ):
        raise ValueError(
            "Question Scientist context requires provenance-bearing TopicEvidenceBrief"
        )
    # The narrative gate (born inverted) accepts EITHER the automated independent-AI
    # fidelity verdict (the default authority) OR the optional post-hoc human review. It still refuses
    # DRAFT / SOURCE_VERIFIED (not fidelity-reviewed) and anything else, so an un-gated or
    # gate-rejected narrative fails closed. The provenance-bearing check below is unchanged. NOTE: the
    # TopicEvidenceBrief branch above stays EXPERT_REVIEWED-only — 5a-1 inverts the topic-evidence gate.
    if dataset_narrative.review_status not in {
        DatasetNarrativeReviewStatus.AUTOMATED_REVIEWED,
        DatasetNarrativeReviewStatus.EXPERT_REVIEWED,
    }:
        raise ValueError("Question Scientist context requires reviewed accepted DatasetNarrative")
    if not (
        dataset_narrative.prompt_version
        and dataset_narrative.provider_id
        and dataset_narrative.input_digest
        and dataset_narrative.source_packet_digest
    ):
        raise ValueError("Question Scientist context requires provenance-bearing DatasetNarrative")


def _is_mock_provider(provider_id: str, model_id: str) -> bool:
    text = f"{provider_id} {model_id}".lower()
    return "mock" in text or "deterministic-fixture" in text


def _contains_placeholder_text(value: Any) -> bool:
    dumped = str(value.model_dump(mode="json") if hasattr(value, "model_dump") else value)
    lowered = dumped.lower()
    return "mock field-state synthesis placeholder" in lowered or "placeholder" in lowered


def _dataset_required_fields() -> list[str]:
    return [
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


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output
