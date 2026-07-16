"""Deterministic, presentation-only views of PatternBank and QuestionFamily context.

These renderers consume already-validated typed artifacts.  They never call a model, change an
artifact's authority, or decide scientific acceptance.  The returned warning codes are deliberately
identifier-free so an orchestration layer may persist them without exposing private run metadata.
"""

from __future__ import annotations

import html
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from ...schemas.question_family import (
    QuestionFamily,
    QuestionFamilyBatch,
    QuestionFamilyShortlistManifest,
    QuestionFamilyVariant,
    QuestionFamilyVariantReviewStatus,
    ShortlistedQuestionFamily,
)
from ...schemas.question_pattern import QuestionPatternCard
from ...schemas.question_scientist_context_v2 import (
    ProposerSourceEvidenceCard,
    TopicLiteratureContextPack,
)

_OMITTED = "Information omitted because it is not safe for a public presentation page."
_MISSING_SOURCE = "A reviewed source could not be resolved for public presentation."
_NOT_RECORDED = "None recorded."

_ABSOLUTE_PATH = re.compile(
    r"(?:^|[\s(\[])"
    r"(?:/(?:Users|Volumes|private|tmp|var|home|root|opt|etc|mnt|workspace|data|srv)"
    r"(?:/|\b)|[A-Za-z]:[\\/])"
)
_SHA256 = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
_CREDENTIAL = re.compile(
    r"(?:\b(?:sk|ghp|github_pat)-?[A-Za-z0-9_]{12,}\b|"
    r"\b(?:api[_-]?key|authorization|bearer)\s*[:=]\s*\S+)",
    re.IGNORECASE,
)
_PRIVATE_IDENTIFIER = re.compile(
    r"\b(?:provider|session|request|thread|branch|event|evidence|claim|context)"
    r"(?:[_-]?id)?\s*[:=]\s*[A-Za-z0-9][A-Za-z0-9_.:-]*",
    re.IGNORECASE,
)
_PRIVATE_IDENTIFIER_TOKEN = re.compile(
    r"\b(?:provider|session|request|thread|branch|event|evidence|claim|context)"
    r"[_-]id[_-][A-Za-z0-9][A-Za-z0-9_.-]*\b",
    re.IGNORECASE,
)
_RAW_PAYLOAD = re.compile(
    r"[{'\"](?:provider|session|request|thread|branch|event|evidence|claim|context)"
    r"(?:_id)?['\"]\s*:",
    re.IGNORECASE,
)
_RAW_URL = re.compile(r"https?://\S+", re.IGNORECASE)
_PDF_REFERENCE = re.compile(r"(?:https?://\S+|\S+/\S*)\.pdf(?:\?\S*)?", re.IGNORECASE)
_IDENTIFIER_LIKE = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[-_:][A-Za-z0-9]+)+")
_INTERNAL_REFERENCE_PREFIXES = {
    "case",
    "claim",
    "clm",
    "context",
    "ctx",
    "evidence",
    "gap",
    "paper",
    "prior",
    "record",
    "source",
    "topic",
    "trace",
}
_EMBEDDED_INTERNAL_REFERENCE_PREFIXES = {"clm", "ctx", "qfamily", "qpattern", "qseed"}


@dataclass(frozen=True, slots=True)
class RenderedPresentationPage:
    """One candidate page plus identifier-free warning codes."""

    markdown: str
    warnings: tuple[str, ...] = ()

    @property
    def presentation_ready(self) -> bool:
        return not self.warnings


@dataclass(frozen=True, slots=True)
class PatternSourceLink:
    """Public-facing labels and run-relative links for one PatternCase/trace edge.

    The two IDs are lookup keys only.  Rendered prose uses the labels and relative links and never
    emits either key.
    """

    paper_case_id: str
    formation_trace_id: str
    paper_label: str
    paper_href: str
    trace_label: str
    trace_href: str


@dataclass(frozen=True, slots=True)
class _LiteratureItem:
    statement: str
    source_record_ids: tuple[str, ...] = ()
    reference_id: str = ""


class _Warnings:
    def __init__(self) -> None:
        self._codes: list[str] = []

    def add(self, code: str) -> None:
        if code not in self._codes:
            self._codes.append(code)

    def freeze(self) -> tuple[str, ...]:
        return tuple(self._codes)


class _LiteratureResolver:
    def __init__(self, pack: TopicLiteratureContextPack | None, warnings: _Warnings) -> None:
        self._warnings = warnings
        self._sources: dict[str, ProposerSourceEvidenceCard] = {}
        self._items: dict[str, _LiteratureItem] = {}
        if pack is None:
            warnings.add("literature_context_unavailable")
            return

        self._sources = {card.source_record_id: card for card in pack.source_cards}
        for claim_card in pack.claim_cards:
            self._items[claim_card.claim_id] = _LiteratureItem(
                statement=claim_card.statement,
                source_record_ids=tuple(claim_card.source_record_ids),
                reference_id=claim_card.claim_id,
            )
        for gap_card in pack.open_gap_cards:
            self._items[gap_card.gap_id] = _LiteratureItem(
                statement=f"{gap_card.statement} Why it remains open: {gap_card.why_live}",
                source_record_ids=tuple(gap_card.support_source_record_ids),
                reference_id=gap_card.gap_id,
            )
        for prior_card in pack.close_prior_cards:
            self._items[prior_card.close_prior_id] = _LiteratureItem(
                statement=f"{prior_card.statement} Relevance: {prior_card.implication}",
                source_record_ids=tuple(prior_card.source_record_ids),
                reference_id=prior_card.close_prior_id,
            )
        for limit_card in pack.method_limit_cards:
            self._items[limit_card.method_limit_id] = _LiteratureItem(
                statement=(
                    f"{limit_card.statement} Consequence for question development: "
                    f"{limit_card.consequence_for_question_generation}"
                ),
                source_record_ids=tuple(limit_card.source_record_ids),
                reference_id=limit_card.method_limit_id,
            )
        for source_card in pack.source_cards:
            self._items[source_card.source_record_id] = _LiteratureItem(
                statement=source_card.title,
                source_record_ids=(source_card.source_record_id,),
                reference_id=source_card.source_record_id,
            )

    @property
    def known_ids(self) -> frozenset[str]:
        return frozenset(self._items)

    def exact(self, reference: str) -> _LiteratureItem | None:
        item = self._items.get(reference.strip())
        if item is None:
            self._warnings.add("unresolved_literature_reference")
        return item

    def from_text(self, value: str) -> tuple[_LiteratureItem, ...]:
        stripped = value.strip()
        if not stripped:
            return ()
        exact = self._items.get(stripped)
        if exact is not None:
            return (exact,)

        mentioned = [
            (identifier, item)
            for identifier, item in self._items.items()
            if _contains_token(stripped, identifier)
        ]
        if mentioned:
            # The model sometimes embeds an internal claim ID in explanatory prose.  The detailed
            # page renders the reviewed typed card instead of echoing that mixed string.
            return _deduplicate_literature(item for _, item in mentioned)
        if _looks_like_internal_reference(stripped):
            self._warnings.add("unresolved_literature_reference")
            return ()
        return (_LiteratureItem(statement=stripped),)

    def render(self, item: _LiteratureItem, *, forbidden_tokens: Iterable[str]) -> list[str]:
        public_replacements = {identifier: "reviewed literature item" for identifier in self._items}
        statement = _safe_text(
            item.statement,
            warnings=self._warnings,
            forbidden_tokens=forbidden_tokens,
            replacements=public_replacements,
        )
        lines = [f"- {statement}"]
        citations: list[str] = []
        for source_index, source_id in enumerate(item.source_record_ids, start=1):
            source = self._sources.get(source_id)
            if source is None:
                self._warnings.add("unresolved_literature_source")
                continue
            citation_text = _without_exact_typed_url(source.citation, source.url)
            if not citation_text:
                citation_text = source.title or f"Reviewed source {source_index}"
            citation_replacements = {
                **public_replacements,
                source.source_record_id: f"reviewed source {source_index}",
            }
            citation = _safe_text(
                citation_text,
                warnings=self._warnings,
                forbidden_tokens=(*forbidden_tokens, source.source_record_id),
                replacements=citation_replacements,
            )
            if citation == _OMITTED:
                continue
            if source.url:
                if _is_safe_public_url(source.url):
                    citation = f"[{citation}]({source.url})"
                else:
                    self._warnings.add("unsafe_typed_source_url_omitted")
            if citation not in citations:
                citations.append(citation)
        if citations:
            lines.append(f"  - Sources: {'; '.join(citations)}")
        elif item.source_record_ids:
            lines.append(f"  - Sources: {_MISSING_SOURCE}")
            self._warnings.add("unresolved_literature_source")
        return lines


def render_question_patterns_detailed(
    patterns: Sequence[QuestionPatternCard],
    *,
    source_links: Sequence[PatternSourceLink] = (),
) -> RenderedPresentationPage:
    """Render complete reviewed pattern content without changing the compact summary."""

    warnings = _Warnings()
    link_by_edge: dict[tuple[str, str], PatternSourceLink] = {}
    for link in source_links:
        key = (link.paper_case_id, link.formation_trace_id)
        if key in link_by_edge:
            existing = link_by_edge[key]
            if (existing.paper_href, existing.trace_href) != (link.paper_href, link.trace_href):
                warnings.add("conflicting_pattern_source_link")
            continue
        link_by_edge[key] = link

    lines = [
        "# Detailed question-formation patterns",
        "",
        (
            "These pages expand the compact PatternBank summary for scientific reading. They "
            "describe reviewed question-forming moves; they do not establish novelty, dataset "
            "feasibility, or a scientific result."
        ),
        "",
    ]
    if not patterns:
        lines.extend(["No reviewed question-formation patterns were available.", ""])
        warnings.add("no_patterns_available")

    for pattern_index, pattern in enumerate(patterns, start=1):
        forbidden = {
            pattern.pattern_id,
            *pattern.source_case_ids,
            *pattern.source_trace_ids,
        }
        replacements: dict[str, str] = {}
        for source_index, (case_id, trace_id) in enumerate(
            zip(pattern.source_case_ids, pattern.source_trace_ids, strict=False),
            start=1,
        ):
            replacements[case_id] = f"source paper {source_index}"
            replacements[trace_id] = f"formation trace {source_index}"

        def pattern_text(
            value: str,
            *,
            _forbidden: set[str] = forbidden,
            _replacements: dict[str, str] = replacements,
        ) -> str:
            return _safe_text(
                value,
                warnings=warnings,
                forbidden_tokens=_forbidden,
                replacements=_replacements,
            )

        def pattern_list(
            values: Sequence[str],
            *,
            _forbidden: set[str] = forbidden,
            _replacements: dict[str, str] = replacements,
        ) -> list[str]:
            return _render_text_list(
                values,
                warnings=warnings,
                forbidden_tokens=_forbidden,
                replacements=_replacements,
            )

        lines.extend(
            [
                f"## Pattern {pattern_index:03d}: {pattern_text(pattern.pattern_name)}",
                "",
                f"- Review authority: `{pattern.review_status.value}`",
                f"- Transfer scope: `{pattern.transfer_scope.value}`",
                "",
                "### Starting scientific state",
                "",
                *pattern_list(pattern.starting_scientific_state),
                "",
                "### Unresolved tension",
                "",
                pattern_text(pattern.unresolved_tension_pattern),
                "",
                "### Dataset cues",
                "",
                *pattern_list(pattern.dataset_cues),
                "",
                "### Question-forming move",
                "",
                pattern_text(pattern.question_formation_move),
                "",
                "### Scientific payoff",
                "",
                pattern_text(pattern.scientific_payoff),
                "",
                "### What different outcomes would mean",
                "",
                "- Positive: " + pattern_text(pattern.positive_result_consequence),
                "- Negative: " + pattern_text(pattern.negative_result_consequence),
                "",
                "### Common failure modes",
                "",
                *pattern_list(pattern.common_failure_modes),
                "",
                "### Details that should not be transferred",
                "",
                *pattern_list(pattern.non_transferable_details),
                "",
                "### Source PaperCases and formation traces",
                "",
            ]
        )
        edges = list(zip(pattern.source_case_ids, pattern.source_trace_ids, strict=False))
        if len(pattern.source_case_ids) != len(pattern.source_trace_ids):
            warnings.add("incomplete_pattern_source_lineage")
        if not edges:
            lines.append(f"- {_MISSING_SOURCE}")
            warnings.add("missing_pattern_source_link")
        for edge_index, edge in enumerate(edges, start=1):
            source_link = link_by_edge.get(edge)
            if (
                source_link is None
                or not _safe_relative_markdown_href(source_link.paper_href)
                or not _safe_relative_markdown_href(source_link.trace_href)
            ):
                lines.append(f"- Source {edge_index}: {_MISSING_SOURCE}")
                warnings.add("missing_pattern_source_link")
                continue
            paper_label = _safe_text(
                source_link.paper_label,
                warnings=warnings,
                forbidden_tokens=forbidden,
            )
            trace_label = _safe_text(
                source_link.trace_label,
                warnings=warnings,
                forbidden_tokens=forbidden,
            )
            lines.append(
                f"- Source {edge_index}: [{paper_label}]({source_link.paper_href}) · "
                f"[{trace_label}]({source_link.trace_href})"
            )
        lines.extend([""])

    return RenderedPresentationPage(
        markdown="\n".join(lines).rstrip() + "\n",
        warnings=warnings.freeze(),
    )


def render_question_families_detailed(
    batch: QuestionFamilyBatch,
    *,
    shortlist: QuestionFamilyShortlistManifest | None,
    topic_literature: TopicLiteratureContextPack | None,
) -> RenderedPresentationPage:
    """Render every proposed family/variant, including families not shortlisted for planning."""

    warnings = _Warnings()
    resolver = _LiteratureResolver(topic_literature, warnings)
    shortlist_by_family = (
        {item.family.question_family_id: item for item in shortlist.shortlisted}
        if shortlist is not None
        else {}
    )
    rejected = set(shortlist.rejected_family_ids) if shortlist is not None else set()
    needs_revision = set(shortlist.needs_revision_family_ids) if shortlist is not None else set()
    deferred = set(shortlist.deferred_family_ids) if shortlist is not None else set()
    if shortlist is None:
        warnings.add("shortlist_unavailable")

    lines = [
        "# Detailed Question Scientist families",
        "",
        (
            "This page preserves every proposed family and variant, including options that were not "
            "shortlisted for planning. Novelty and dataset leverage below are proposal-stage "
            "hypotheses, not verdicts or feasibility certifications."
        ),
        "",
        f"- Families proposed: {len(batch.families)}",
        f"- Authority ceiling: `{batch.authority_ceiling.value}`",
        "",
    ]
    for family_index, family in enumerate(batch.families, start=1):
        family_forbidden = _family_private_tokens(batch, family, resolver)
        family_disposition = _family_disposition(
            family,
            shortlist_by_family=shortlist_by_family,
            rejected=rejected,
            needs_revision=needs_revision,
            deferred=deferred,
            warnings=warnings,
        )
        lines.extend(
            [
                f"## Family {family_index:03d}: "
                f"{_safe_text(family.title, warnings=warnings, forbidden_tokens=family_forbidden)}",
                "",
                f"- Shortlist disposition: **{family_disposition}**",
                f"- Proposal review status: `{family.review_status.value}`",
                f"- Authority ceiling: `{family.authority_ceiling.value}`",
                "",
                "### Scientific background",
                "",
                _safe_text(
                    family.summary,
                    warnings=warnings,
                    forbidden_tokens=family_forbidden,
                ),
                "",
                "### Shared scientific tension",
                "",
                _safe_text(
                    family.shared_scientific_tension,
                    warnings=warnings,
                    forbidden_tokens=family_forbidden,
                ),
                "",
                "### Family structure",
                "",
                "- Semantic axes: "
                + _safe_inline_list(
                    family.semantic_axes,
                    warnings=warnings,
                    forbidden_tokens=family_forbidden,
                ),
                "- Distinctions that should not be merged: "
                + _safe_inline_list(
                    family.non_mergeable_distinctions,
                    warnings=warnings,
                    forbidden_tokens=family_forbidden,
                ),
                "- Proposal-stage uncertainties: "
                + _safe_inline_list(
                    family.proposal_stage_uncertainties,
                    warnings=warnings,
                    forbidden_tokens=family_forbidden,
                ),
                "- Dataset assumptions: "
                + _safe_inline_list(
                    family.assumptions_about_dataset,
                    warnings=warnings,
                    forbidden_tokens=family_forbidden,
                ),
                "",
                "### Reviewed literature context used by the family",
                "",
            ]
        )
        family_literature = _deduplicate_literature(
            item
            for reference in family.source_topic_claim_ids
            if (item := resolver.exact(reference)) is not None
        )
        if family_literature:
            for item in family_literature:
                lines.extend(resolver.render(item, forbidden_tokens=family_forbidden))
        elif family.source_topic_claim_ids:
            lines.append(f"- {_MISSING_SOURCE}")
        else:
            lines.append("- No family-level topic-literature claim was recorded.")

        selected = shortlist_by_family.get(family.question_family_id)
        for variant_index, variant in enumerate(family.variants, start=1):
            variant_forbidden = {*family_forbidden, variant.variant_id, variant.question_seed_id}
            disposition = _variant_disposition(
                family_disposition=family_disposition,
                variant=variant,
                shortlisted_family=selected,
                warnings=warnings,
            )
            seed = variant.seed
            lines.extend(
                [
                    "",
                    f"### Variant {family_index:03d}.{variant_index:03d}: "
                    f"{_safe_text(variant.variant_role, warnings=warnings, forbidden_tokens=variant_forbidden)}",
                    "",
                    f"- Shortlist disposition: **{disposition}**",
                    "- Distinction axes: "
                    + ", ".join(axis.value for axis in variant.distinction_axes),
                    "- Distinct from sibling variants: "
                    + _safe_text(
                        variant.distinct_from_siblings,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    "#### Question",
                    "",
                    _safe_text(
                        seed.question,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    "#### Scientific tension and why it matters",
                    "",
                    _safe_text(
                        seed.scientific_tension,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    _safe_text(
                        seed.why_scientifically_important,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    "#### Proposal-stage novelty hypothesis — not a verdict",
                    "",
                    _safe_text(
                        seed.novelty_hypothesis,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    "#### Relevant literature",
                    "",
                ]
            )
            relevant_items = _deduplicate_literature(
                item
                for value in seed.relevant_literature_claims
                for item in resolver.from_text(value)
            )
            if relevant_items:
                for item in relevant_items:
                    lines.extend(resolver.render(item, forbidden_tokens=variant_forbidden))
            else:
                lines.append(f"- {_MISSING_SOURCE}")
                if seed.relevant_literature_claims:
                    warnings.add("unresolved_literature_reference")

            lines.extend(["", "#### Closest known work", ""])
            closest_items = _deduplicate_literature(
                item for value in seed.closest_known_work for item in resolver.from_text(value)
            )
            if closest_items:
                for item in closest_items:
                    lines.extend(resolver.render(item, forbidden_tokens=variant_forbidden))
            else:
                lines.append(
                    f"- {_MISSING_SOURCE}" if seed.closest_known_work else f"- {_NOT_RECORDED}"
                )

            lines.extend(
                [
                    "",
                    "#### Dataset leverage hypothesis — not a feasibility certification",
                    "",
                    _safe_text(
                        seed.dataset_leverage_hypothesis,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    "#### Competing explanations",
                    "",
                    *_render_text_list(
                        seed.competing_explanations,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    "#### Discriminating observation",
                    "",
                    _safe_text(
                        seed.discriminating_observation,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    "#### What different outcomes would mean",
                    "",
                    "- Positive: "
                    + _safe_text(
                        seed.positive_result_consequence,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "- Negative: "
                    + _safe_text(
                        seed.negative_result_consequence,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "- Null: "
                    + _safe_text(
                        seed.null_result_consequence,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    "#### Ambiguities",
                    "",
                    *_render_text_list(
                        seed.ambiguous_constructs,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    "#### Planning challenges",
                    "",
                    *_render_text_list(
                        seed.likely_implementation_challenges,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                    "#### Dataset assumptions",
                    "",
                    *_render_text_list(
                        seed.assumptions_about_dataset,
                        warnings=warnings,
                        forbidden_tokens=variant_forbidden,
                    ),
                    "",
                ]
            )

    return RenderedPresentationPage(
        markdown="\n".join(lines).rstrip() + "\n",
        warnings=warnings.freeze(),
    )


def _family_private_tokens(
    batch: QuestionFamilyBatch,
    family: QuestionFamily,
    resolver: _LiteratureResolver,
) -> set[str]:
    return {
        batch.batch_id,
        batch.context_id,
        batch.context_digest,
        batch.input_digest,
        batch.origin_provider_id,
        batch.prompt_version,
        family.question_family_id,
        family.context_id,
        family.origin_provider_id,
        family.prompt_version,
        *family.source_pattern_ids,
        *family.source_topic_claim_ids,
        *family.source_topic_pack_ids,
        *family.source_dataset_context_ids,
        *family.source_family_ids,
        *resolver.known_ids,
        *(variant.variant_id for variant in family.variants),
        *(variant.question_seed_id for variant in family.variants),
        *(variant.seed.prompt_version for variant in family.variants),
        *(
            source_id
            for variant in family.variants
            for source_id in variant.seed.source_paper_case_ids
        ),
    }


def _family_disposition(
    family: QuestionFamily,
    *,
    shortlist_by_family: dict[str, ShortlistedQuestionFamily],
    rejected: set[str],
    needs_revision: set[str],
    deferred: set[str],
    warnings: _Warnings,
) -> str:
    family_id = family.question_family_id
    if family_id in shortlist_by_family:
        return "Shortlisted for planning; this is not scientific approval"
    if family_id in rejected:
        return "Not shortlisted — rejected by the configured family review"
    if family_id in needs_revision:
        return "Not shortlisted — revision requested"
    if family_id in deferred:
        return "Not shortlisted — deferred"
    warnings.add("missing_shortlist_disposition")
    return "Disposition unavailable"


def _variant_disposition(
    *,
    family_disposition: str,
    variant: QuestionFamilyVariant,
    shortlisted_family: ShortlistedQuestionFamily | None,
    warnings: _Warnings,
) -> str:
    if shortlisted_family is None:
        return family_disposition
    active_ids = set(shortlisted_family.active_variant_ids)
    if variant.variant_id in active_ids:
        return "Active for planning"
    decisions = {
        decision.variant_id: decision.status
        for decision in shortlisted_family.review.variant_decisions
    }
    status = decisions.get(variant.variant_id)
    if status is None:
        warnings.add("missing_variant_shortlist_disposition")
        return "Not active; detailed disposition unavailable"
    labels = {
        QuestionFamilyVariantReviewStatus.ACTIVE: "Active for planning",
        QuestionFamilyVariantReviewStatus.NEEDS_REVISION: "Not active — revision requested",
        QuestionFamilyVariantReviewStatus.REJECTED: "Not active — rejected by family review",
        QuestionFamilyVariantReviewStatus.DEFERRED: "Not active — deferred",
    }
    return labels[status]


def _render_text_list(
    values: Sequence[str],
    *,
    warnings: _Warnings,
    forbidden_tokens: Iterable[str],
    replacements: Mapping[str, str] | None = None,
) -> list[str]:
    if not values:
        return [f"- {_NOT_RECORDED}"]
    return [
        f"- {_safe_text(value, warnings=warnings, forbidden_tokens=forbidden_tokens, replacements=replacements)}"
        for value in values
    ]


def _safe_inline_list(
    values: Sequence[str],
    *,
    warnings: _Warnings,
    forbidden_tokens: Iterable[str],
) -> str:
    if not values:
        return _NOT_RECORDED
    return "; ".join(
        _safe_text(value, warnings=warnings, forbidden_tokens=forbidden_tokens) for value in values
    )


def _safe_text(
    value: str,
    *,
    warnings: _Warnings,
    forbidden_tokens: Iterable[str] = (),
    replacements: Mapping[str, str] | None = None,
) -> str:
    normalized = " ".join(value.split())
    if not normalized:
        return _NOT_RECORDED
    for token, replacement in sorted(
        (replacements or {}).items(), key=lambda item: len(item[0]), reverse=True
    ):
        normalized = re.sub(
            rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])",
            replacement,
            normalized,
        )
    forbidden = [token.strip() for token in forbidden_tokens if token and token.strip()]
    unsafe = (
        _ABSOLUTE_PATH.search(normalized)
        or _SHA256.search(normalized)
        or _CREDENTIAL.search(normalized)
        or _PRIVATE_IDENTIFIER.search(normalized)
        or _PRIVATE_IDENTIFIER_TOKEN.search(normalized)
        or _RAW_PAYLOAD.search(normalized)
        or _RAW_URL.search(normalized)
        or _PDF_REFERENCE.search(normalized)
        or any(_contains_token(normalized, token) for token in forbidden)
    )
    if unsafe:
        warnings.add("unsafe_public_content_omitted")
        return _OMITTED
    escaped = html.escape(normalized, quote=False)
    return escaped.replace("\\", "\\\\").replace("`", "\\`").replace("[", "\\[").replace("]", "\\]")


def _contains_token(text: str, token: str) -> bool:
    if not token:
        return False
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])", text) is not None


def _looks_like_internal_reference(value: str) -> bool:
    for match in _IDENTIFIER_LIKE.finditer(value):
        token = match.group(0)
        prefix = re.split(r"[-_:]", token, maxsplit=1)[0].lower()
        is_entire_value = match.start() == 0 and match.end() == len(value)
        if is_entire_value and (
            any(char.isdigit() for char in token) or prefix in _INTERNAL_REFERENCE_PREFIXES
        ):
            return True
        if prefix in _EMBEDDED_INTERNAL_REFERENCE_PREFIXES or (
            any(char.isdigit() for char in token) and prefix in _INTERNAL_REFERENCE_PREFIXES
        ):
            return True
    return False


def _safe_relative_markdown_href(value: str) -> bool:
    if not value or "\\" in value or "%" in value or "?" in value or "#" in value:
        return False
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", value):
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and path.parts[0] in {"papers", "formation_traces"}
        and path.suffix.lower() == ".md"
        and not any(part.startswith(".") for part in path.parts)
    )


def _is_safe_public_url(value: str) -> bool:
    if _ABSOLUTE_PATH.search(value) or _CREDENTIAL.search(value) or _SHA256.search(value):
        return False
    if re.search(r"[\s()<>`\"'\\]", value):
        return False
    parsed = urlsplit(value)
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
        and ".pdf" not in parsed.path.lower()
        and not re.search(
            r"(?:^|&)(?:format|type|download|file)=[^&]*pdf(?:&|$)",
            parsed.query,
            re.IGNORECASE,
        )
    )


def _deduplicate_literature(items: Iterable[_LiteratureItem]) -> tuple[_LiteratureItem, ...]:
    unique: list[_LiteratureItem] = []
    seen: set[tuple[str, tuple[str, ...], str]] = set()
    for item in items:
        key = (item.statement, item.source_record_ids, item.reference_id)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return tuple(unique)


def _without_exact_typed_url(citation: str, url: str) -> str:
    """Remove only the separately typed URL before rebuilding one safe Markdown link."""
    if not url:
        return citation.strip()
    stripped = citation.replace(url, " ")
    stripped = re.sub(r"\s*[,;|]\s*$", "", stripped.strip())
    return " ".join(stripped.split())
