from __future__ import annotations

import re
from typing import NamedTuple, TypedDict

from ...provenance import stable_hash
from ...schemas.cited_literature import (
    CitationContext,
    CitationContextRole,
    CitedWorkIdentifiers,
    CitedWorkRef,
    RawReferenceEntry,
    ReferenceResolutionStatus,
)
from ...schemas.paper_ingest import BlockType, ParsedPaper, ParsedPaperBlock

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
PMID_RE = re.compile(r"\bPMID[:\s]*(\d{5,12})\b", re.IGNORECASE)
PMCID_RE = re.compile(r"\bPMC(?:ID)?[:\s]*(PMC?\d{5,12})\b", re.IGNORECASE)
ARXIV_RE = re.compile(r"\barXiv[:\s]*([0-9]{4}\.[0-9]{4,5}(?:v\d+)?)\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
REFERENCE_HEADING_RE = re.compile(r"(?im)^\s*(references|bibliography|literature cited)\s*$")
NUMBERED_REF_RE = re.compile(r"^\s*(?:\[(\d{1,3})\]|(\d{1,3})[.)])\s+(.+)")
REFERENCE_START_RE = re.compile(r"(?:^|\s{3,})(?:\[(\d{1,3})\]|(\d{1,3})[.)])\s+")
BOILERPLATE_SECTION_PREFIXES = (
    "acknowledgements",
    "acknowledgments",
    "author contributions",
    "competing interests",
    "additional information",
    "publisher's note",
    "reviewer information",
    "reprints and permissions",
    "extended data is available",
    "supplementary information is available",
    "nature research",
    "nature portfolio",
    "reporting summary",
    "statistics",
    "data policy information",
    "materials & experimental systems",
)


class _ReferenceHints(TypedDict):
    title_hint: str
    author_hint: str
    year_hint: int | None
    doi_hint: str
    pmid_hint: str
    pmcid_hint: str
    arxiv_id_hint: str


class _ReferenceLine(NamedTuple):
    text: str
    block: ParsedPaperBlock | None


class _ReferenceCandidate(NamedTuple):
    raw_text: str
    block: ParsedPaperBlock | None
    reference_number: int | None


def extract_raw_references(parsed: ParsedPaper) -> list[RawReferenceEntry]:
    reference_blocks = _reference_blocks(parsed)
    primary_lines = _reference_lines(reference_blocks)
    if not primary_lines:
        primary_lines = _reference_lines_from_full_text(parsed)
    primary_entries = _split_reference_entries(primary_lines)
    tail_entries = _split_reference_entries(_tail_reference_lines(parsed))
    raw_entries = (
        tail_entries
        if len(primary_entries) < 10 and len(tail_entries) > len(primary_entries)
        else primary_entries
    )
    entries: list[RawReferenceEntry] = []
    for fallback_index, candidate in enumerate(raw_entries, start=1):
        hints = _reference_hints(candidate.raw_text)
        reference_index = candidate.reference_number or fallback_index
        raw_reference_id = f"{parsed.paper_id}.ref{reference_index:05d}"
        entries.append(
            RawReferenceEntry(
                raw_reference_id=raw_reference_id,
                source_paper_id=parsed.paper_id,
                reference_index=reference_index,
                raw_text=candidate.raw_text,
                source_block_id=candidate.block.block_id if candidate.block else "",
                source_span_id=candidate.block.block_id if candidate.block else raw_reference_id,
                section_title=candidate.block.section_title if candidate.block else "References",
                page_number=candidate.block.page_number if candidate.block else None,
                title_hint=hints["title_hint"],
                author_hint=hints["author_hint"],
                year_hint=hints["year_hint"],
                doi_hint=hints["doi_hint"],
                pmid_hint=hints["pmid_hint"],
                pmcid_hint=hints["pmcid_hint"],
                arxiv_id_hint=hints["arxiv_id_hint"],
            )
        )
    return entries


def build_unresolved_cited_works(entries: list[RawReferenceEntry]) -> list[CitedWorkRef]:
    works: list[CitedWorkRef] = []
    for entry in entries:
        cited_work_id = f"cw-{stable_hash(entry.raw_text)[:12]}"
        authors = _author_list(entry.author_hint)
        is_external = entry.source_block_id.startswith("external:")
        works.append(
            CitedWorkRef(
                cited_work_id=cited_work_id,
                raw_reference_id=entry.raw_reference_id,
                local_reference_index=entry.reference_index,
                raw_reference=entry.raw_text,
                title=entry.title_hint,
                authors=authors,
                year=entry.year_hint,
                identifiers=CitedWorkIdentifiers(
                    doi=entry.doi_hint,
                    pmid=entry.pmid_hint,
                    pmcid=entry.pmcid_hint,
                    arxiv_id=entry.arxiv_id_hint,
                ),
                resolution_status=(
                    ReferenceResolutionStatus.EXTERNAL_ONLY
                    if is_external
                    else ReferenceResolutionStatus.LOCAL_REFERENCE_EXTRACTED
                ),
                resolution_source=entry.source_block_id if is_external else "local_references",
                resolution_confidence=0.35 if is_external else 0.2,
            )
        )
    return works


def extract_citation_contexts(
    parsed: ParsedPaper, cited_works: list[CitedWorkRef]
) -> list[CitationContext]:
    body_blocks = [
        block
        for block in parsed.blocks
        if block.block_type != BlockType.REFERENCE
        and "reference" not in block.section_title.lower()
        and "bibliography" not in block.section_title.lower()
        and not _is_reference_cluster_block(block)
    ]
    if not body_blocks:
        body_blocks = [
            ParsedPaperBlock(
                block_id=f"{parsed.paper_id}.body",
                page_number=1,
                text=_body_text_before_references(parsed.full_text),
                block_type=BlockType.PAGE_TEXT,
                section_title="Body",
            )
        ]
    contexts: list[CitationContext] = []
    seen: set[tuple[str, str, str]] = set()
    for work in cited_works:
        patterns = _citation_patterns(work)
        if not patterns:
            continue
        for block in body_blocks:
            for pattern in patterns:
                for match in pattern.finditer(block.text):
                    sentence = _sentence_window(block.text, match.start(), match.end())
                    key = (work.cited_work_id, block.block_id, sentence)
                    if key in seen:
                        continue
                    seen.add(key)
                    context_id = f"cc-{stable_hash(key)[:12]}"
                    contexts.append(
                        CitationContext(
                            context_id=context_id,
                            cited_work_id=work.cited_work_id,
                            source_span_id=block.block_id,
                            page=block.page_number,
                            section=block.section_title,
                            local_context=sentence,
                            mention_text=match.group(0),
                            inferred_role=_infer_context_role(block.section_title, sentence),
                        )
                    )
    return contexts


def _reference_blocks(parsed: ParsedPaper) -> list[ParsedPaperBlock]:
    return [
        block
        for block in parsed.blocks
        if block.block_type == BlockType.REFERENCE
        or "reference" in block.section_title.lower()
        or "bibliography" in block.section_title.lower()
        or block.text.strip().lower().startswith(("references\n", "references "))
    ]


def _reference_lines(blocks: list[ParsedPaperBlock]) -> list[_ReferenceLine]:
    lines: list[_ReferenceLine] = []
    for block in blocks:
        text = re.sub(r"^\s*references\s*", "", block.text.strip(), flags=re.IGNORECASE)
        lines.extend(_expanded_reference_lines(text, block))
    return lines


def _reference_lines_from_full_text(
    parsed: ParsedPaper,
) -> list[_ReferenceLine]:
    match = REFERENCE_HEADING_RE.search(parsed.full_text)
    if not match:
        inline = re.search(r"\bReferences\b", parsed.full_text)
        if not inline:
            return []
        text = parsed.full_text[inline.end() :]
    else:
        text = parsed.full_text[match.end() :]
    return _expanded_reference_lines(text, None)


def _tail_reference_lines(parsed: ParsedPaper) -> list[_ReferenceLine]:
    if not parsed.blocks:
        return []
    lines: list[_ReferenceLine] = []
    for block in parsed.blocks:
        if _is_boilerplate_block(block):
            continue
        expanded = _expanded_reference_lines(block.text, block)
        if _numbered_reference_start_count(expanded) >= 2:
            lines.extend(_lines_from_first_numbered_reference(expanded))
    return lines


def _expanded_reference_lines(text: str, block: ParsedPaperBlock | None) -> list[_ReferenceLine]:
    lines: list[_ReferenceLine] = []
    for raw_line in text.splitlines():
        for chunk in _split_layout_columns(raw_line):
            cleaned = " ".join(chunk.split())
            if not cleaned:
                continue
            if _is_boilerplate_line(cleaned):
                continue
            lines.extend(_split_embedded_numbered_starts(cleaned, block))
    return lines


def _split_layout_columns(line: str) -> list[str]:
    return [part for part in re.split(r"\s{4,}", line.strip()) if part.strip()]


def _split_embedded_numbered_starts(
    line: str, block: ParsedPaperBlock | None
) -> list[_ReferenceLine]:
    matches = list(REFERENCE_START_RE.finditer(line))
    if len(matches) <= 1:
        return [_ReferenceLine(line, block)]
    parts: list[_ReferenceLine] = []
    for index, match in enumerate(matches):
        start = match.start()
        while start < len(line) and line[start].isspace():
            start += 1
        end = matches[index + 1].start() if index + 1 < len(matches) else len(line)
        part = line[start:end].strip()
        if part:
            parts.append(_ReferenceLine(part, block))
    return parts


def _split_reference_entries(
    lines_with_source: list[_ReferenceLine],
) -> list[_ReferenceCandidate]:
    entries: list[_ReferenceCandidate] = []
    current: list[str] = []
    current_block: ParsedPaperBlock | None = None
    current_number: int | None = None
    numbered = any(NUMBERED_REF_RE.match(line.text) for line in lines_with_source)
    for line_with_source in lines_with_source:
        line = line_with_source.text
        block = line_with_source.block
        match = NUMBERED_REF_RE.match(line)
        starts_new = bool(match) if numbered else _looks_like_reference_start(line)
        if starts_new and current:
            entries.append(
                _ReferenceCandidate(" ".join(current).strip(), current_block, current_number)
            )
            current = []
            current_block = block
            current_number = None
        if numbered and not current and not match:
            continue
        if match:
            current_number = int(match.group(1) or match.group(2) or "0") or None
            current.append(match.group(3).strip())
        else:
            current.append(line.strip())
        current_block = current_block or block
    if current:
        entries.append(
            _ReferenceCandidate(" ".join(current).strip(), current_block, current_number)
        )
    return [
        candidate
        for candidate in entries
        if len(candidate.raw_text) >= 20 and _looks_like_reference_text(candidate.raw_text)
    ]


def _looks_like_reference_start(line: str) -> bool:
    return bool(YEAR_RE.search(line)) and bool(re.match(r"^[A-Z][A-Za-z'`-]+", line))


def _looks_like_reference_text(text: str) -> bool:
    if not YEAR_RE.search(text):
        return False
    lowered = text.lower()
    if any(prefix in lowered[:80] for prefix in ["reporting summary", "data availability"]):
        return False
    return bool(
        re.search(
            r"\b(et al\.|j\.|journal|nature|science|neuron|neurosci|proc\.|doi|http)", lowered
        )
        or re.search(r"\(\d{4}\)", text)
    )


def _numbered_reference_start_count(lines: list[_ReferenceLine]) -> int:
    return sum(1 for line in lines if NUMBERED_REF_RE.match(line.text))


def _lines_from_first_numbered_reference(lines: list[_ReferenceLine]) -> list[_ReferenceLine]:
    for index, line in enumerate(lines):
        if NUMBERED_REF_RE.match(line.text):
            return lines[index:]
    return []


def _is_boilerplate_block(block: ParsedPaperBlock) -> bool:
    text = block.text.strip().lower()
    if not text:
        return True
    return text.startswith(
        ("nature research\nreporting summary", "nature portfolio\nreporting summary")
    )


def _is_reference_cluster_block(block: ParsedPaperBlock) -> bool:
    expanded = _expanded_reference_lines(block.text, block)
    return _numbered_reference_start_count(expanded) >= 2


def _is_boilerplate_line(line: str) -> bool:
    lowered = line.strip().lower()
    if not lowered:
        return True
    return any(lowered.startswith(prefix) for prefix in BOILERPLATE_SECTION_PREFIXES)


def _reference_hints(raw_text: str) -> _ReferenceHints:
    year_match = YEAR_RE.search(raw_text)
    doi_match = DOI_RE.search(raw_text)
    pmid_match = PMID_RE.search(raw_text)
    pmcid_match = PMCID_RE.search(raw_text)
    arxiv_match = ARXIV_RE.search(raw_text)
    return {
        "title_hint": _title_hint(raw_text),
        "author_hint": _author_hint(raw_text),
        "year_hint": int(year_match.group(0)) if year_match else None,
        "doi_hint": doi_match.group(0).rstrip(").,;") if doi_match else "",
        "pmid_hint": pmid_match.group(1) if pmid_match else "",
        "pmcid_hint": _normalize_pmcid(pmcid_match.group(1)) if pmcid_match else "",
        "arxiv_id_hint": arxiv_match.group(1) if arxiv_match else "",
    }


def _title_hint(raw_text: str) -> str:
    quoted = re.search(r"[\"“”](.{8,220})[\"“”]", raw_text)
    if quoted:
        return " ".join(quoted.group(1).split())
    cleaned = DOI_RE.sub("", raw_text)
    cleaned = PMID_RE.sub("", cleaned)
    cleaned = PMCID_RE.sub("", cleaned)
    cleaned = ARXIV_RE.sub("", cleaned)
    parts = [part.strip() for part in re.split(r"\.\s+", cleaned) if part.strip()]
    for part in parts[1:]:
        if YEAR_RE.fullmatch(part):
            continue
        if len(part) >= 8 and not re.fullmatch(r"[A-Z][A-Za-z'`-]+(,?\s+[A-Z]\.?)*", part):
            return part[:300]
    return ""


def _author_hint(raw_text: str) -> str:
    year_match = YEAR_RE.search(raw_text)
    prefix = raw_text[: year_match.start()] if year_match else raw_text.split(".", 1)[0]
    return " ".join(prefix.strip(" .").split())[:300]


def _author_list(author_hint: str) -> list[str]:
    if not author_hint:
        return []
    normalized = author_hint.replace(" and ", "; ")
    parts = [part.strip(" .,") for part in re.split(r";|,(?=\s+[A-Z][a-z]+)", normalized)]
    return [part for part in parts if part][:8]


def _normalize_pmcid(value: str) -> str:
    value = value.upper()
    return value if value.startswith("PMC") else f"PMC{value}"


def _body_text_before_references(text: str) -> str:
    match = REFERENCE_HEADING_RE.search(text)
    if match:
        return text[: match.start()]
    inline = re.search(r"\bReferences\b", text)
    return text[: inline.start()] if inline else text


def _citation_patterns(work: CitedWorkRef) -> list[re.Pattern[str]]:
    patterns: list[re.Pattern[str]] = []
    if work.local_reference_index is not None:
        index = str(work.local_reference_index)
        patterns.append(re.compile(rf"\[(?:[^\]]*,\s*)?{re.escape(index)}(?:\s*,[^\]]*)?\]"))
    if work.year and work.authors:
        surname = re.escape(work.authors[0].split()[0].strip(".,"))
        patterns.append(
            re.compile(rf"{surname}(?:\s+et\s+al\.)?(?:,|\s+\(|\s+)\s*{work.year}", re.IGNORECASE)
        )
    return patterns


def _sentence_window(text: str, start: int, end: int) -> str:
    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start))
    right_candidates = [pos for pos in [text.find(".", end), text.find("\n", end)] if pos != -1]
    right = min(right_candidates) if right_candidates else min(len(text), end + 260)
    sentence = text[left + 1 : right + 1].strip()
    return " ".join(sentence.split())


def _infer_context_role(section: str, sentence: str) -> CitationContextRole:
    text = f"{section} {sentence}".lower()
    if "dataset" in text or "data set" in text:
        return CitationContextRole.DATASET_PRECEDENT
    if "method" in text or "model" in text or "analysis" in text:
        return CitationContextRole.METHOD_PRECEDENT
    if "define" in text or "definition" in text or "construct" in text:
        return CitationContextRole.CONSTRUCT_DEFINITION
    if "however" in text or "unknown" in text or "remain" in text or "unresolved" in text:
        return CitationContextRole.UNRESOLVED_TENSION
    if "introduction" in text or "background" in text:
        return CitationContextRole.BACKGROUND
    return CitationContextRole.OTHER
