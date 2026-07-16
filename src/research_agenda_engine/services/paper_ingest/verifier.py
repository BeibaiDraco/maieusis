from __future__ import annotations

import re
import unicodedata

from ...schemas.paper_case import EvidenceSpan, PaperCase
from ...schemas.paper_ingest import EvidenceSpanVerification, PaperSourceSpan, ParsedPaper


class EvidenceSpanVerifier:
    def verify_paper_case(
        self,
        paper_case: PaperCase,
        parsed: ParsedPaper,
        source_spans: list[PaperSourceSpan] | None = None,
        require_source_spans: bool = False,
    ) -> list[EvidenceSpanVerification]:
        source_span_by_id = {span.span_id: span for span in source_spans or []}
        return [
            self.verify_span(
                span,
                parsed,
                source_span_by_id=source_span_by_id,
                require_source_span=require_source_spans,
            )
            for span in paper_case.evidence_spans
        ]

    def suggested_page_repair(self, span: EvidenceSpan, parsed: ParsedPaper) -> int | None:
        """Return a single deterministic page repair for a wrong-page span."""

        candidates = _candidate_pages(
            parsed,
            span.page,
            span.quote_or_span,
            accepted_notes={
                "exact_normalized_page_match",
                "exact_candidate_page_match",
                "quoted_segments_page_match",
                "ellipsis_segment_page_match",
            },
        )
        return candidates[0] if len(candidates) == 1 else None

    def verify_span(
        self,
        span: EvidenceSpan,
        parsed: ParsedPaper,
        *,
        source_span_by_id: dict[str, PaperSourceSpan] | None = None,
        require_source_span: bool = False,
    ) -> EvidenceSpanVerification:
        if span.source_span_id:
            return _verify_parser_owned_span(span, source_span_by_id or {})
        if require_source_span:
            return _failed(
                span,
                "missing_source_span_id",
                "Evidence span must cite a parser-owned source_span_id in source_span mode.",
            )
        if span.page < 1:
            return _failed(span, "invalid_page", "Evidence page must be one-based.")
        page = next((item for item in parsed.pages if item.page_number == span.page), None)
        if page is None:
            return _failed(span, "page_not_found", "Evidence page is not in parsed paper.")
        quote = span.quote_or_span.strip()
        if not quote:
            return _failed(span, "empty_quote", "Evidence quote is empty.")

        match_note = _quote_match_note(page.text, quote)
        if match_note:
            block = _matching_block(parsed, span.page, quote)
            return EvidenceSpanVerification(
                field=span.field,
                page=span.page,
                verified=True,
                matched_block_id=block or "",
                note=match_note,
            )
        candidate_pages = _candidate_pages(parsed, span.page, quote)
        note = "Evidence quote was not found on the claimed page."
        if candidate_pages:
            pages = ", ".join(str(page_number) for page_number in candidate_pages[:5])
            note = f"{note} The same quote appears on page(s): {pages}."
        return _failed(span, "quote_not_found", note)


def _failed(span: EvidenceSpan, code: str, note: str) -> EvidenceSpanVerification:
    return EvidenceSpanVerification(
        field=span.field,
        page=max(1, span.page),
        verified=False,
        issue_code=code,
        note=note,
    )


def _verify_parser_owned_span(
    span: EvidenceSpan, source_span_by_id: dict[str, PaperSourceSpan]
) -> EvidenceSpanVerification:
    source_span = source_span_by_id.get(span.source_span_id)
    if source_span is None:
        return _failed(
            span,
            "invalid_source_span_id",
            f"Parser-owned source span was not found: {span.source_span_id}",
        )
    if span.source_text_version and span.source_text_version != source_span.source_text_version:
        return _failed(
            span,
            "source_text_version_mismatch",
            "Evidence span source_text_version does not match parser-owned source span.",
        )
    if span.page != source_span.page:
        return _failed(
            span,
            "source_span_page_mismatch",
            "Evidence page does not match parser-owned source span page.",
        )
    start = span.char_start if span.char_start is not None else 0
    end = span.char_end if span.char_end is not None else len(source_span.text_exact)
    if start < 0 or end < start or end > len(source_span.text_exact):
        return _failed(
            span,
            "source_span_offset_out_of_bounds",
            "Evidence char_start/char_end are outside parser-owned source span text.",
        )
    expected = source_span.text_exact[start:end]
    if not expected:
        return _failed(span, "empty_source_span_slice", "Evidence source span slice is empty.")
    if span.quote_or_span != expected:
        return _failed(
            span,
            "source_span_quote_mismatch",
            "Evidence quote does not exactly match the parser-owned source span slice.",
        )
    return EvidenceSpanVerification(
        field=span.field,
        page=span.page,
        verified=True,
        matched_block_id=source_span.span_id,
        note="source_span_exact_match",
    )


def _matching_block(
    parsed: ParsedPaper,
    page: int,
    quote: str,
) -> str | None:
    for block in parsed.blocks:
        if block.page_number != page:
            continue
        if _quote_match_note(block.text, quote):
            return block.block_id
    return None


def _candidate_pages(
    parsed: ParsedPaper,
    claimed_page: int,
    quote: str,
    *,
    accepted_notes: set[str] | None = None,
) -> list[int]:
    return [
        page.page_number
        for page in parsed.pages
        if page.page_number != claimed_page
        and (note := _quote_match_note(page.text, quote))
        and (accepted_notes is None or note in accepted_notes)
    ]


def _quote_match_note(text: str, quote: str) -> str:
    page_text = _normalize_text(text)
    normalized_quote = _normalize_text(quote)
    if normalized_quote and normalized_quote in page_text:
        return "exact_normalized_page_match"
    quoted_parts = _quoted_parts(quote)
    if len(quoted_parts) > 1:
        if _ordered_segments_match(page_text, [_normalize_text(part) for part in quoted_parts]):
            return "quoted_segments_page_match"
        return ""
    for candidate in _quote_candidates(quote):
        normalized_candidate = _normalize_text(candidate)
        if normalized_candidate and normalized_candidate in page_text:
            return "exact_candidate_page_match"
        if _fuzzy_contains(page_text, normalized_candidate):
            return "fuzzy_candidate_page_match"
    if _ellipsis_segments_match(page_text, normalized_quote):
        return "ellipsis_segment_page_match"
    if _fuzzy_contains(page_text, normalized_quote):
        return "fuzzy_page_match"
    return ""


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    replacements = {
        "\u00a0": " ",
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2212": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\ufb00": "ff",
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    normalized = normalized.strip().strip("\"'")
    normalized = re.sub(r"-\s+", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip().lower()


def _quote_candidates(quote: str) -> list[str]:
    candidates: list[str] = []
    normalized = quote.strip()
    quoted_parts = _quoted_parts(normalized)
    if len(quoted_parts) == 1:
        candidates.extend(quoted_parts)
    if ":" in normalized:
        prefix, suffix = normalized.split(":", 1)
        if 0 < len(prefix.split()) <= 8 and len(suffix.split()) >= 4:
            candidates.append(suffix.strip())
    candidates.append(normalized.strip().strip("\"'"))
    seen: set[str] = set()
    unique: list[str] = []
    for candidate in candidates:
        key = _normalize_text(candidate)
        if key and key not in seen:
            unique.append(candidate)
            seen.add(key)
    return unique


def _quoted_parts(quote: str) -> list[str]:
    return [
        match_part.strip()
        for match in re.findall(r'"([^"]+)"|“([^”]+)”', quote)
        for match_part in match
        if match_part.strip()
    ]


def _ellipsis_segments_match(text: str, quote: str) -> bool:
    if "..." not in quote and "…" not in quote:
        return False
    segments = [
        segment.strip() for segment in re.split(r"(?:\.\.\.|…)", quote) if len(segment.split()) >= 4
    ]
    if len(segments) < 2:
        return False
    return _ordered_segments_match(text, segments)


def _ordered_segments_match(text: str, segments: list[str]) -> bool:
    substantial_segments = [segment for segment in segments if len(segment.split()) >= 4]
    if len(substantial_segments) < 2:
        return False
    cursor = 0
    for segment in substantial_segments:
        index = text.find(segment, cursor)
        if index < 0:
            return False
        cursor = index + len(segment)
    return True


def _fuzzy_contains(text: str, quote: str) -> bool:
    if len(quote) < 25:
        return False
    quote_tokens = quote.split()
    if len(quote_tokens) < 5:
        return False
    window = max(4, int(len(quote_tokens) * 0.7))
    for index in range(0, len(quote_tokens) - window + 1):
        excerpt = " ".join(quote_tokens[index : index + window])
        if excerpt in text:
            return True
    return False
