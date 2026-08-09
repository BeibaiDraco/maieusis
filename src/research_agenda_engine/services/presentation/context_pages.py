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

from ...schemas.novelty_admission import (
    FamilyNoveltyAdmission,
    NoveltyVariantDisposition,
    VariantNoveltyAssessment,
)
from ...schemas.presentation import PresentationWarningCode
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
from .privacy import extract_public_dois, remove_allowed_public_dois

_OMITTED = "Information omitted because it is not safe for a public presentation page."
_MISSING_SOURCE = "A reviewed source could not be resolved for public presentation."
_NOT_RECORDED = "None recorded."
_PATTERN_REFERENCE_LABEL = "a reviewed question pattern from this run's PatternBank"
_PAPER_CASE_REFERENCE_LABEL = "a reviewed source paper from this run's PaperBank"

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
    warnings: tuple[PresentationWarningCode, ...] = ()

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
        self._codes: list[PresentationWarningCode] = []

    def add(self, code: PresentationWarningCode) -> None:
        if code not in self._codes:
            self._codes.append(code)

    def freeze(self) -> tuple[PresentationWarningCode, ...]:
        return tuple(self._codes)


class _LiteratureResolver:
    def __init__(self, pack: TopicLiteratureContextPack | None, warnings: _Warnings) -> None:
        self._warnings = warnings
        self._sources: dict[str, ProposerSourceEvidenceCard] = {}
        self._items: dict[str, _LiteratureItem] = {}
        if pack is None:
            warnings.add(PresentationWarningCode.LITERATURE_CONTEXT_UNAVAILABLE)
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
            self._warnings.add(PresentationWarningCode.UNRESOLVED_LITERATURE_REFERENCE)
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
            self._warnings.add(PresentationWarningCode.UNRESOLVED_LITERATURE_REFERENCE)
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
                self._warnings.add(PresentationWarningCode.UNRESOLVED_LITERATURE_SOURCE)
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
                    self._warnings.add(PresentationWarningCode.UNSAFE_TYPED_SOURCE_URL_OMITTED)
            if citation not in citations:
                citations.append(citation)
        if citations:
            lines.append(f"  - Sources: {'; '.join(citations)}")
        elif item.source_record_ids:
            lines.append(f"  - Sources: {_MISSING_SOURCE}")
            self._warnings.add(PresentationWarningCode.UNRESOLVED_LITERATURE_SOURCE)
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
                warnings.add(PresentationWarningCode.CONFLICTING_PATTERN_SOURCE_LINK)
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
        warnings.add(PresentationWarningCode.NO_PATTERNS_AVAILABLE)

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
            warnings.add(PresentationWarningCode.INCOMPLETE_PATTERN_SOURCE_LINEAGE)
        if not edges:
            lines.append(f"- {_MISSING_SOURCE}")
            warnings.add(PresentationWarningCode.MISSING_PATTERN_SOURCE_LINK)
        for edge_index, edge in enumerate(edges, start=1):
            source_link = link_by_edge.get(edge)
            if (
                source_link is None
                or not _safe_relative_markdown_href(source_link.paper_href)
                or not _safe_relative_markdown_href(source_link.trace_href)
            ):
                lines.append(f"- Source {edge_index}: {_MISSING_SOURCE}")
                warnings.add(PresentationWarningCode.MISSING_PATTERN_SOURCE_LINK)
                continue
            paper_label = _safe_text(
                source_link.paper_label,
                warnings=warnings,
                forbidden_tokens=forbidden,
                allowed_public_dois=extract_public_dois(source_link.paper_label),
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


def _novelty_evidence_by_variant(
    assessments: Sequence[VariantNoveltyAssessment],
) -> dict[str, str]:
    """The reviewer's own sentence for a variant, plus the priors it actually compared against.

    A scientific "no" must carry its evidence -- shape (2) of the shepherd contract. The reader was
    told a question "duplicates prior work" and nothing more, while the rationale and the
    DOI-identified comparisons sat unread in the assessment file. Only what the reviewer WROTE is
    rendered; the host adds no interpretation of its own.
    """
    evidence: dict[str, str] = {}
    for assessment in assessments:
        parts: list[str] = []
        rationale = (assessment.rationale or "").strip()
        if rationale:
            parts.append(rationale)
        priors = [
            comparison.source_record_id
            for comparison in assessment.comparisons
            if getattr(comparison, "source_record_id", "")
        ]
        if priors:
            parts.append("Compared against: " + "; ".join(priors))
        for requirement in assessment.distinction_requirements:
            if requirement.strip():
                parts.append(f"To distinguish it: {requirement.strip()}")
        if parts:
            evidence[assessment.variant_id] = " ".join(parts)
    return evidence


def _novelty_disposition_by_variant(
    admissions: Sequence[FamilyNoveltyAdmission],
) -> dict[str, NoveltyVariantDisposition]:
    """Flatten the receipt-bound prior-art records into one variant → disposition lookup.

    Variant ids are unique per run, so a flat map is safe and keeps the caller from having to know
    which family owned which admission.
    """
    return {
        item.variant_id: item.disposition
        for admission in admissions
        for item in admission.variant_admissions
    }


def render_question_families_detailed(
    batch: QuestionFamilyBatch,
    *,
    shortlist: QuestionFamilyShortlistManifest | None,
    topic_literature: TopicLiteratureContextPack | None,
    novelty_admissions: Sequence[FamilyNoveltyAdmission] = (),
    novelty_assessments: Sequence[VariantNoveltyAssessment] = (),
) -> RenderedPresentationPage:
    """Render every proposed family/variant, including families not shortlisted for planning."""

    warnings = _Warnings()
    novelty_by_variant = _novelty_disposition_by_variant(novelty_admissions)
    novelty_evidence = _novelty_evidence_by_variant(novelty_assessments)
    resolver = _LiteratureResolver(topic_literature, warnings)
    shortlist_by_family = (
        {item.family.question_family_id: item for item in shortlist.shortlisted}
        if shortlist is not None
        else {}
    )
    rejected = set(shortlist.rejected_family_ids) if shortlist is not None else set()
    needs_revision = set(shortlist.needs_revision_family_ids) if shortlist is not None else set()
    deferred = set(shortlist.deferred_family_ids) if shortlist is not None else set()
    run_incomplete = set(shortlist.run_incomplete_family_ids) if shortlist is not None else set()
    if shortlist is None:
        warnings.add(PresentationWarningCode.SHORTLIST_UNAVAILABLE)

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
        family_labels = _unrenderable_reference_labels(family)
        family_disposition = _family_disposition(
            family,
            shortlist_by_family=shortlist_by_family,
            rejected=rejected,
            needs_revision=needs_revision,
            deferred=deferred,
            run_incomplete=run_incomplete,
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
                novelty_disposition=novelty_by_variant.get(variant.variant_id),
                novelty_evidence=novelty_evidence.get(variant.variant_id, ""),
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
            relevant_items = _resolved_literature(
                seed.relevant_literature_claims,
                resolver=resolver,
                replacements=family_labels,
            )
            if relevant_items:
                for item in relevant_items:
                    lines.extend(resolver.render(item, forbidden_tokens=variant_forbidden))
            else:
                lines.append(f"- {_MISSING_SOURCE}")
                if seed.relevant_literature_claims:
                    warnings.add(PresentationWarningCode.UNRESOLVED_LITERATURE_REFERENCE)

            lines.extend(["", "#### Closest known work", ""])
            closest_items = _resolved_literature(
                seed.closest_known_work,
                resolver=resolver,
                replacements=family_labels,
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


def _unrenderable_reference_labels(family: QuestionFamily) -> dict[str, str]:
    """Public stand-ins for the run-private ids a family may write inside scientific prose.

    Pattern ids and paper-case ids are private to the run, so they belong in the forbidden set and
    must never reach the page. They are also, measurably, written straight INTO the model's
    sentences: across 17 live batches, 87 ``closest_known_work`` / ``relevant_literature_claims``
    values carried a pattern id and 9 carried a paper-case id, most of them as the sentence's own
    subject ("qpat-regional-anomaly-driver-states-007 provides a precedent for objective state
    classification while preserving causal caveats.").

    Forbidding without substituting destroyed the whole sentence: 13 of the 18 "Closest known work"
    bullets on the only live run that ever built a PaperBank from scratch were the omission marker,
    and a further 15 bullets across three other runs were the unresolved-source marker because the
    model had written the bare id and nothing else.

    This page never receives the PatternBank or the PaperBank, so the reference cannot be rendered
    as a typed card. Naming its *kind* keeps the reviewer's sentence and its scientific meaning
    while the id itself still never appears -- degrade before strict construction, AGENTS.md rule
    11, and the same remedy as PR #109.
    """
    labels = {
        pattern_id: _PATTERN_REFERENCE_LABEL
        for pattern_id in family.source_pattern_ids
        if pattern_id
    }
    for variant in family.variants:
        for case_id in variant.seed.source_paper_case_ids:
            if case_id:
                labels[case_id] = _PAPER_CASE_REFERENCE_LABEL
    return labels


def _resolved_literature(
    values: Iterable[str],
    *,
    resolver: _LiteratureResolver,
    replacements: Mapping[str, str],
) -> tuple[_LiteratureItem, ...]:
    """Resolve model-written references, substituting the ids this page cannot render.

    Substitution runs BEFORE resolution so a private id never reaches the point where it can
    nullify the prose around it. Topic-literature ids are deliberately left intact: the resolver
    still resolves them to their reviewed typed card, which renders better than any stand-in.
    """
    items: list[_LiteratureItem] = []
    for value in values:
        stripped = value.strip()
        label = replacements.get(stripped)
        if label is not None:
            # The model wrote the bare id and nothing else; there is no sentence to preserve, so
            # state the kind of reference rather than reporting a resolution failure.
            items.append(_LiteratureItem(statement=f"{label[0].upper()}{label[1:]}."))
            continue
        substituted = _substitute_tokens(stripped, replacements)
        # The id is usually the sentence's own subject, so the stand-in usually lands at position
        # zero; the bullet is a standalone sentence and should read like one.
        if any(substituted.startswith(label) for label in set(replacements.values())):
            substituted = f"{substituted[0].upper()}{substituted[1:]}"
        items.extend(resolver.from_text(substituted))
    return _deduplicate_literature(items)


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
    run_incomplete: set[str],
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
    if family_id in run_incomplete:
        # The manifest has carried this bucket since #135 and nothing rendered it, so a family lost
        # to a provider fault fell through to "Disposition unavailable" -- or, worse, was written
        # into `deferred` upstream and read as a finding about the literature. The reader is told
        # what actually happened.
        return (
            "Not shortlisted — this family was not reviewed: the run could not complete its "
            "novelty review. This is an infrastructure limitation, not a scientific finding "
            "about the literature"
        )
    warnings.add(PresentationWarningCode.MISSING_SHORTLIST_DISPOSITION)
    return "Disposition unavailable"


_NOVELTY_FILTERED_DISPOSITIONS = {
    NoveltyVariantDisposition.REJECTED_DIRECT_RECAP: (
        "Not carried into planning — bounded prior-art review found a close prior that directly "
        "recaps this variant"
    ),
    NoveltyVariantDisposition.DEFERRED_CLOSE_PRIOR: (
        "Not carried into planning — deferred: a close prior sits near this variant and a "
        "distinguishing revision is required first"
    ),
    NoveltyVariantDisposition.DEFERRED_INSUFFICIENT_EVIDENCE: (
        "Not carried into planning — deferred: the bounded prior-art search did not return enough "
        "evidence to judge this variant"
    ),
    # #145 routed provider faults into their own disposition and stopped there: this table had no
    # entry, so such a variant fell past `filtered is None` to the missing-record branch and the
    # reader was told the run "recorded no decision" -- which is the opposite of the truth, since
    # #145's whole point is that the run DID record what happened. On the 2026-07-31 leg 2 of the
    # 3 delivered families carry one such variant each, so that false sentence would have printed
    # twice on the demo.
    NoveltyVariantDisposition.NOT_ASSESSED_INFRASTRUCTURE: (
        "Not carried into planning — this variant was never reviewed: the prior-art reviewer could "
        "not be reached. This is an infrastructure limitation, not a finding about the literature"
    ),
}
_NOVELTY_FILTERED_WITHOUT_RECORD = (
    "Not carried into planning — filtered before family review; this run kept no record of which "
    "prior-art finding decided it"
)


def _variant_disposition(
    *,
    family_disposition: str,
    variant: QuestionFamilyVariant,
    shortlisted_family: ShortlistedQuestionFamily | None,
    novelty_disposition: NoveltyVariantDisposition | None,
    warnings: _Warnings,
    novelty_evidence: str = "",
) -> str:
    """One variant's honest disposition, including the ones family review never saw.

    The `missing_variant_shortlist_disposition` case used to print "Not active; detailed disposition
    unavailable" and raise a warning. Both were wrong, and measuring the corpus settled why: 27
    variants across 14 of 16 live runs hit it, and in 27 of 27 the variant was absent from
    ``shortlisted_family.family.variants`` as well -- because that field is the novelty-ADMITTED
    family copy, so a variant filtered by bounded novelty admission was never carried into family
    review at all. Nothing was lost: no shortlist review decision for it was ever produced, and the
    shortlist reviewer has no per-variant slot in which to produce one.

    So the old behaviour treated a normal, expected outcome as an anomaly, which is what made almost
    every live run's presentation add-on read as degraded. Worse, the obvious "fix" -- minting a
    review decision in persistence -- would stamp the novelty judge's finding with the shortlist
    reviewer's identity, promoting unreviewed material past its authority (hard rule 12), and the
    schema would accept the forged record.

    The novelty judge DID decide, with provenance, and its record is receipt-bound in the same run.
    That record is the honest source, so its disposition is named here. The warning now fires only
    when something is genuinely unaccounted for: a variant family review should have decided on but
    did not, or a filtered variant with no prior-art record to explain it.
    """
    if shortlisted_family is None:
        return family_disposition
    if variant.variant_id in set(shortlisted_family.active_variant_ids):
        return "Active for planning"
    decisions = {
        decision.variant_id: decision.status
        for decision in shortlisted_family.review.variant_decisions
    }
    status = decisions.get(variant.variant_id)
    if status is not None:
        labels = {
            QuestionFamilyVariantReviewStatus.ACTIVE: "Active for planning",
            QuestionFamilyVariantReviewStatus.NEEDS_REVISION: "Not active — revision requested",
            QuestionFamilyVariantReviewStatus.REJECTED: "Not active — rejected by family review",
            QuestionFamilyVariantReviewStatus.DEFERRED: "Not active — deferred",
        }
        return labels[status]
    reviewed_variant_ids = {item.variant_id for item in shortlisted_family.family.variants}
    if variant.variant_id in reviewed_variant_ids:
        # Family review DID carry this variant and still recorded nothing for it. That is the only
        # genuinely anomalous shape, and it is what the warning should mean.
        warnings.add(PresentationWarningCode.MISSING_VARIANT_SHORTLIST_DISPOSITION)
        return "Not active; family review recorded no decision for this variant"
    filtered = _NOVELTY_FILTERED_DISPOSITIONS.get(novelty_disposition)  # type: ignore[arg-type]
    if filtered is not None:
        # The shepherd contract's shape (2) is "a scientific 'no' WITH its evidence". The label
        # alone told the reader their question duplicates prior work and stopped there, while the
        # reviewer's rationale and the DOI-identified priors it compared against sat unread in the
        # assessment file, already paid for. Appended verbatim -- the host adds no reading of its
        # own, and a variant whose assessment is missing keeps the bare label rather than a
        # fabricated justification.
        return f"{filtered}. {novelty_evidence}" if novelty_evidence else filtered
    # Filtered before family review, but nothing on disk says why -- including the case where the
    # prior-art record exists yet reports this variant as admitted, which would contradict its
    # absence from the active set.
    warnings.add(PresentationWarningCode.MISSING_VARIANT_SHORTLIST_DISPOSITION)
    return _NOVELTY_FILTERED_WITHOUT_RECORD


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
    allowed_public_dois: Iterable[str] = (),
    replacements: Mapping[str, str] | None = None,
) -> str:
    normalized = _substitute_tokens(" ".join(value.split()), replacements)
    if not normalized:
        return _NOT_RECORDED
    forbidden = [token.strip() for token in forbidden_tokens if token and token.strip()]
    token_checked_text = remove_allowed_public_dois(normalized, allowed_public_dois)
    unsafe = (
        _ABSOLUTE_PATH.search(normalized)
        or _SHA256.search(normalized)
        or _CREDENTIAL.search(normalized)
        or _PRIVATE_IDENTIFIER.search(normalized)
        or _PRIVATE_IDENTIFIER_TOKEN.search(normalized)
        or _RAW_PAYLOAD.search(normalized)
        or _RAW_URL.search(normalized)
        or _PDF_REFERENCE.search(normalized)
        or any(_contains_token(token_checked_text, token) for token in forbidden)
    )
    if unsafe:
        warnings.add(PresentationWarningCode.UNSAFE_PUBLIC_CONTENT_OMITTED)
        return _OMITTED
    escaped = html.escape(normalized, quote=False)
    return escaped.replace("\\", "\\\\").replace("`", "\\`").replace("[", "\\[").replace("]", "\\]")


def _substitute_tokens(value: str, replacements: Mapping[str, str] | None) -> str:
    """Replace whole-token occurrences, longest key first so a prefix never eats a longer id."""
    for token, replacement in sorted(
        (replacements or {}).items(), key=lambda item: len(item[0]), reverse=True
    ):
        value = re.sub(
            rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])",
            replacement,
            value,
        )
    return value


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
