"""Deterministic demo topic source table + topic evidence brief.

The config-reachable
``subscription_only_demo`` deterministic generation assets (public_optional). Demo mode is
an explicit mock + FakePlannerHost workflow demonstration — never a scientific-quality
claim (the demo banner and development_model_surrogate authority labels flow to every
output surface).
"""

from __future__ import annotations

from datetime import date

from research_agenda_engine.schemas.inferred_research_scope import (
    ResearchScopeSourceMode,
    ResolvedResearchScope,
)
from research_agenda_engine.schemas.scientific_context import (
    TopicEvidenceBrief,
    TopicEvidenceBriefReviewStatus,
    TopicEvidenceClaim,
    TopicEvidenceClaimOrigin,
    TopicEvidenceClaimStatus,
)
from research_agenda_engine.schemas.topic_literature import (
    TopicLensSourceFamily,
    TopicSourceRecord,
    TopicSourceTable,
)
from research_agenda_engine.services.retrieval.generic_topic_lanes import (
    build_generic_topic_evidence_query_plan,
)

_SOURCE_IDS = ["source-1", "source-2"]


def _generic_source_table() -> TopicSourceTable:
    """Two truthful provider/scope-term lineages with claim-supporting demo records."""
    scope = ResolvedResearchScope(
        source_mode=ResearchScopeSourceMode.OPEN_INFERRED, terms=["movement"]
    )
    plan = build_generic_topic_evidence_query_plan(
        scope,
        source_families=[TopicLensSourceFamily.OPENALEX, TopicLensSourceFamily.CROSSREF],
    )
    return TopicSourceTable(
        table_id="generic-source-table",
        query_plan_id=plan.plan_id,
        topic_terms=["movement"],
        max_records=20,
        records=[
            TopicSourceRecord(
                source_record_id=sid,
                source_family=query.source_family,
                query_ids=[query.query_id],
                title=f"Movement-related population geometry source {sid}",
                year=2024,
                url=f"https://example.org/{sid}",
                snippet="Substantive abstract text about movement and population geometry.",
                relevance_score=0.8,
                metadata_quality_score=0.8,
                source_payload_hash=f"h-{sid}",
            )
            for sid, query in zip(_SOURCE_IDS, plan.queries, strict=True)
        ],
    )


def _ready_gpt_brief() -> TopicEvidenceBrief:
    """A compile-ready topic brief citing the generic source table's ids (close-prior + open-gap)."""

    def _claim(cid: str, status: TopicEvidenceClaimStatus) -> TopicEvidenceClaim:
        return TopicEvidenceClaim(
            claim_id=cid,
            claim=f"Movement-related population geometry claim ({cid}).",
            status=status,
            source_refs=list(_SOURCE_IDS),
            source_record_ids=list(_SOURCE_IDS),
            origin=TopicEvidenceClaimOrigin.BOTH,
            synthesis_rationale="Reviewed from the supplied source records.",
            confidence=0.7,
        )

    return TopicEvidenceBrief(
        brief_id="gpt-topic-brief",
        topic_terms=["movement"],
        canonical_scope="Movement-related population geometry.",
        claims=[
            _claim("claim-open", TopicEvidenceClaimStatus.OPEN_QUESTION),
            _claim("claim-prior", TopicEvidenceClaimStatus.ALREADY_ANSWERED),
            _claim("claim-limit", TopicEvidenceClaimStatus.KNOWN_LIMITATION),
        ],
        nearest_dataset_reuse_work=["Related reuse work exists."],
        questions_already_answered=["Related geometry questions exist."],
        unresolved_tensions=["Movement can explain apparent decision signals."],
        knowledge_cutoff=date(2026, 6, 29),
        retrieval_manifest_digest="d" * 64,
        review_status=TopicEvidenceBriefReviewStatus.EXPERT_REVIEWED,
        prompt_version="topic_evidence_brief_synthesizer/v4",
        provider_id="openai:gpt-5.4",
        model_id="gpt-5.4",
        input_digest="a" * 64,
        source_table_digest="b" * 64,
    )
