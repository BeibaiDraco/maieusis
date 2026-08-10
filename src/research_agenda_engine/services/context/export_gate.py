from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ...schemas.question_scientist_context_v2 import (
    ContentAvailabilityClass,
    EvidenceExcerpt,
    ProposerSourceEvidenceCard,
    SourceEvidenceRole,
    SourceExportBlockReason,
    SourceExportStatus,
    SourceIntegrityClass,
    SourceQualityClass,
)
from .topic_evidence import (
    R5TopicSourceRecordEvidence,
    SourceEvidenceCard,
    TopicSourceSnippetKind,
    fulltext_rights_are_verified,
    rights_safe_source_text_and_kind,
)


@dataclass(frozen=True)
class SourceExportClassification:
    source_quality_class: SourceQualityClass
    content_availability_class: ContentAvailabilityClass
    integrity_class: SourceIntegrityClass
    export_status: SourceExportStatus
    block_reasons: tuple[SourceExportBlockReason, ...]
    warnings: tuple[str, ...]


def classify_topic_source_for_export(
    card: SourceEvidenceCard,
    *,
    r5_record: R5TopicSourceRecordEvidence | None = None,
) -> SourceExportClassification:
    content_availability = _content_availability_class(card, r5_record)
    quality_class = _source_quality_class(card, r5_record)
    integrity_class = _source_integrity_class(card, r5_record)
    block_reasons: list[SourceExportBlockReason] = []
    warnings: list[str] = []

    if not card.can_support_claims:
        if card.exclusion_reason == "off_topic":
            block_reasons.append(SourceExportBlockReason.OUT_OF_SCOPE_SOURCE)
        elif content_availability == ContentAvailabilityClass.TITLE_ONLY:
            block_reasons.append(SourceExportBlockReason.TITLE_ONLY_RECORD)
        elif content_availability == ContentAvailabilityClass.METADATA_ONLY:
            block_reasons.append(SourceExportBlockReason.METADATA_ONLY_RECORD)
        else:
            block_reasons.append(SourceExportBlockReason.EMPTY_EXCERPT)
    if integrity_class == SourceIntegrityClass.UNVERIFIABLE_CITATION:
        block_reasons.append(SourceExportBlockReason.UNVERIFIABLE_CITATION)
    if integrity_class == SourceIntegrityClass.RETRACTED:
        block_reasons.append(SourceExportBlockReason.RETRACTED_POSITIVE_EVIDENCE)
    if quality_class in {
        SourceQualityClass.NON_SCHOLARLY_NEWS_OR_BLOG,
        SourceQualityClass.VENDOR_MARKETING_OR_PRESS_RELEASE,
        SourceQualityClass.SOCIAL_MEDIA_OR_FORUM,
        SourceQualityClass.SUSPECTED_SPAM_OR_GENERATED_CONTENT,
    }:
        block_reasons.append(SourceExportBlockReason.NON_SCHOLARLY_SOURCE)
    if content_availability == ContentAvailabilityClass.ABSTRACT_ONLY:
        warnings.append("abstract_only_weak_context")
    if (
        r5_record is not None
        and r5_record.snippet_kind == TopicSourceSnippetKind.FULLTEXT_EXCERPT
        and not fulltext_rights_are_verified(r5_record)
    ):
        warnings.append("fulltext_rights_unverified")
    if quality_class in {
        SourceQualityClass.SCHOLARLY_PREPRINT,
        SourceQualityClass.EDITORIAL_COMMENTARY_OR_PERSPECTIVE,
        SourceQualityClass.DATASET_REGISTRY_OR_PROTOCOL,
        SourceQualityClass.UNCLASSIFIED_SOURCE,
    }:
        warnings.append(f"limited_evidence_role:{quality_class.value}")

    unique_reasons = tuple(dict.fromkeys(block_reasons))
    status = (
        SourceExportStatus.BLOCKED_FROM_QUESTION_SCIENTIST
        if unique_reasons
        else (SourceExportStatus.EXPORT_WITH_WARNING if warnings else SourceExportStatus.EXPORT)
    )
    return SourceExportClassification(
        source_quality_class=quality_class,
        content_availability_class=content_availability,
        integrity_class=integrity_class,
        export_status=status,
        block_reasons=unique_reasons,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def build_proposer_source_evidence_card(
    card: SourceEvidenceCard,
    *,
    r5_record: R5TopicSourceRecordEvidence | None = None,
    evidence_roles: list[SourceEvidenceRole] | None = None,
    support_claim_ids: list[str] | None = None,
    support_gap_ids: list[str] | None = None,
    support_close_prior_ids: list[str] | None = None,
    support_method_limit_ids: list[str] | None = None,
    max_excerpt_chars: int = 800,
    review_status: Literal["expert_reviewed", "ai_reviewed", "provisional"] = "expert_reviewed",
) -> ProposerSourceEvidenceCard:
    classification = classify_topic_source_for_export(card, r5_record=r5_record)
    text = _source_excerpt_text(card, r5_record, max_chars=max_excerpt_chars)
    excerpts: list[EvidenceExcerpt] = []
    if text and classification.export_status != SourceExportStatus.BLOCKED_FROM_QUESTION_SCIENTIST:
        excerpts.append(
            EvidenceExcerpt(
                excerpt_id=f"excerpt-{card.source_record_id}-001",
                source_record_id=card.source_record_id,
                text=text,
                char_count=len(text),
            )
        )
    quality_flags = [
        *card.quality_flags,
        *classification.warnings,
    ]
    return ProposerSourceEvidenceCard(
        source_record_id=card.source_record_id,
        title=card.title,
        citation=_citation_text(card, r5_record),
        year=card.year,
        venue="",
        doi=card.doi,
        url=card.url,
        source_quality_class=classification.source_quality_class,
        content_availability_class=classification.content_availability_class,
        integrity_class=classification.integrity_class,
        evidence_roles=evidence_roles or [SourceEvidenceRole.FIELD_STATE_BACKGROUND],
        review_status=review_status,
        export_status=classification.export_status,
        export_block_reasons=list(classification.block_reasons),
        excerpts=excerpts,
        support_claim_ids=support_claim_ids or [],
        support_gap_ids=support_gap_ids or [],
        support_close_prior_ids=support_close_prior_ids or [],
        support_method_limit_ids=support_method_limit_ids or [],
        quality_flags=quality_flags,
    )


def require_exportable_source_cards(cards: list[ProposerSourceEvidenceCard]) -> None:
    blocked = [
        card.source_record_id
        for card in cards
        if card.export_status == SourceExportStatus.BLOCKED_FROM_QUESTION_SCIENTIST
    ]
    if blocked:
        raise ValueError(
            "blocked source cards cannot enter Question Scientist context: " + ", ".join(blocked)
        )


def _content_availability_class(
    card: SourceEvidenceCard,
    r5_record: R5TopicSourceRecordEvidence | None,
) -> ContentAvailabilityClass:
    if card.exclusion_reason == "off_topic":
        return ContentAvailabilityClass.OUT_OF_SCOPE_RECORD
    snippet_kind = r5_record.snippet_kind if r5_record is not None else None
    if r5_record is not None and snippet_kind == TopicSourceSnippetKind.FULLTEXT_EXCERPT:
        if not fulltext_rights_are_verified(r5_record):
            _, fallback_kind = rights_safe_source_text_and_kind(r5_record)
            if fallback_kind in {
                TopicSourceSnippetKind.ABSTRACT,
                TopicSourceSnippetKind.PROVIDER_SNIPPET,
            }:
                return ContentAvailabilityClass.ABSTRACT_ONLY
            return ContentAvailabilityClass.METADATA_ONLY
        return ContentAvailabilityClass.FULL_TEXT_OR_SUFFICIENT_EXCERPT_AVAILABLE
    if snippet_kind in {TopicSourceSnippetKind.ABSTRACT, TopicSourceSnippetKind.PROVIDER_SNIPPET}:
        return ContentAvailabilityClass.ABSTRACT_ONLY
    if snippet_kind == TopicSourceSnippetKind.METADATA:
        return ContentAvailabilityClass.METADATA_ONLY
    if snippet_kind == TopicSourceSnippetKind.TITLE_ONLY:
        return ContentAvailabilityClass.TITLE_ONLY
    if card.abstract_or_excerpt.strip():
        return ContentAvailabilityClass.ABSTRACT_ONLY
    return ContentAvailabilityClass.TITLE_ONLY


def _source_quality_class(
    card: SourceEvidenceCard,
    r5_record: R5TopicSourceRecordEvidence | None,
) -> SourceQualityClass:
    text = " ".join([card.title, card.url, card.doi, " ".join(card.quality_flags)]).lower()
    if "retracted" in text:
        return SourceQualityClass.UNCLASSIFIED_SOURCE
    if "biorxiv" in text or "medrxiv" in text or card.doi.lower().startswith("10.1101"):
        return SourceQualityClass.SCHOLARLY_PREPRINT
    if any(token in text for token in ["figshare", "aws", "open data", "protocol"]):
        return SourceQualityClass.DATASET_REGISTRY_OR_PROTOCOL
    if any(token in text for token in ["review", "perspective", "commentary"]):
        return SourceQualityClass.EDITORIAL_COMMENTARY_OR_PERSPECTIVE
    # A DOI is an identifier, not peer review. Preprint servers and conference-abstract systems mint
    # them freely: every one of the four climate sources on the 2026-07-30 leg carries
    # `publication_types: ['posted-content']` and a `10.5194/egusphere-*` DOI -- two EGU preprints and
    # two EGU General Assembly ABSTRACTS -- and all four were exported to the Question Scientist as
    # `peer_reviewed_primary_study`. The correct signal was already on the same record and never
    # read. Crossref's own type is what decides; the DOI-only branch survives ONLY as an
    # unclassified fallback for a record that carries no type at all.
    pub_types = {
        value.strip().lower()
        for value in (r5_record.publication_types if r5_record is not None else [])
        if value.strip()
    }
    if pub_types & {"posted-content", "preprint"}:
        return SourceQualityClass.SCHOLARLY_PREPRINT
    if pub_types & {"journal-article", "article", "proceedings-article", "book-chapter"}:
        return SourceQualityClass.PEER_REVIEWED_PRIMARY_STUDY
    return SourceQualityClass.UNCLASSIFIED_SOURCE


def _source_integrity_class(
    card: SourceEvidenceCard,
    r5_record: R5TopicSourceRecordEvidence | None,
) -> SourceIntegrityClass:
    flags = " ".join(
        [
            *card.quality_flags,
            *(r5_record.source_quality_flags if r5_record is not None else []),
        ]
    ).lower()
    if "retracted" in flags:
        return SourceIntegrityClass.RETRACTED
    if "expression_of_concern" in flags or "concern" in flags:
        return SourceIntegrityClass.EXPRESSION_OF_CONCERN
    if "unverifiable" in flags:
        return SourceIntegrityClass.UNVERIFIABLE_CITATION
    if "red_flag" in flags:
        return SourceIntegrityClass.METHODOLOGICAL_RED_FLAG
    return SourceIntegrityClass.NORMAL


def _source_excerpt_text(
    card: SourceEvidenceCard,
    r5_record: R5TopicSourceRecordEvidence | None,
    *,
    max_chars: int,
) -> str:
    if (
        r5_record is not None
        and r5_record.snippet_kind == TopicSourceSnippetKind.FULLTEXT_EXCERPT
        and not fulltext_rights_are_verified(r5_record)
    ):
        fallback_text, _ = rights_safe_source_text_and_kind(r5_record)
        return fallback_text[:max_chars].strip()
    text = card.abstract_or_excerpt.strip()
    if not text and r5_record is not None:
        text = r5_record.abstract_or_snippet.strip()
    if not text:
        return ""
    return text[:max_chars].strip()


def _citation_text(
    card: SourceEvidenceCard,
    r5_record: R5TopicSourceRecordEvidence | None,
) -> str:
    year = card.year if card.year is not None else (r5_record.year if r5_record else None)
    suffix = f" ({year})" if year else ""
    identifiers = card.doi or card.pmid or card.openalex_id or card.semantic_scholar_id or card.url
    if identifiers:
        return f"{card.title}{suffix}; {identifiers}"
    return f"{card.title}{suffix}"
