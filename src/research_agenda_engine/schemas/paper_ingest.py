from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..provenance import stable_hash


class ParserKind(StrEnum):
    DOCLING = "docling"
    POPPLER_TEXT = "poppler_text"
    GROBID_TEI = "grobid_tei"
    FIXTURE = "fixture"


class PaperIngestStatus(StrEnum):
    DISCOVERED = "discovered"
    PARSED = "parsed"
    PARSE_INCOMPLETE = "parse_incomplete"
    TEXT_UNAVAILABLE = "text_unavailable"
    DEGRADED = "degraded"
    LOOKUP_FAILED = "lookup_failed"
    READY_FOR_EXTRACTION = "ready_for_extraction"
    EXTRACTED = "extracted"
    SPAN_VERIFIED = "span_verified"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"
    SKIPPED = "skipped"


class BlockType(StrEnum):
    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CAPTION = "caption"
    TABLE = "table"
    REFERENCE = "reference"
    PAGE_TEXT = "page_text"
    UNKNOWN = "unknown"


class LicenseClass(StrEnum):
    UNKNOWN = "unknown"
    METADATA_ONLY = "metadata_only"
    PERMISSIVE = "permissive"
    NON_COMMERCIAL = "non_commercial"
    RESTRICTED = "restricted"
    UNCLEAR = "unclear"


class ProcessedTextAvailability(StrEnum):
    NONE = "none"
    ABSTRACT = "abstract"
    PMC_BIOC = "pmc_bioc"
    PMC_JATS = "pmc_jats"
    ARXIV_SOURCE = "arxiv_source"
    S2ORC_RECORD = "s2orc_record"
    UNARXIVE_RECORD = "unarxive_record"


class SpanKind(StrEnum):
    UNKNOWN = "unknown"
    SECTION_PARAGRAPH = "section_paragraph"
    CHAR_OFFSET = "char_offset"
    PAGE_COORD = "page_coord"


class TextBBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(ge=1)
    x0: float
    y0: float
    x1: float
    y1: float

    @model_validator(mode="after")
    def validate_box(self) -> TextBBox:
        if self.x1 < self.x0 or self.y1 < self.y0:
            raise ValueError("bbox coordinates must be ordered")
        return self


class ParsedPaperPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_number: int = Field(ge=1)
    text: str = ""
    width: float | None = None
    height: float | None = None


class ParsedPaperBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block_id: str
    page_number: int = Field(ge=1)
    text: str = Field(min_length=1)
    block_type: BlockType = BlockType.PARAGRAPH
    section_title: str = ""
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    bbox: TextBBox | None = None
    source_path: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("block_id")
    @classmethod
    def validate_block_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("block_id cannot be empty")
        return value

    @model_validator(mode="after")
    def validate_char_span(self) -> ParsedPaperBlock:
        if (
            self.char_start is not None
            and self.char_end is not None
            and self.char_end < self.char_start
        ):
            raise ValueError("char_end must be greater than or equal to char_start")
        if self.bbox is not None and self.bbox.page != self.page_number:
            raise ValueError("bbox page must match block page_number")
        return self


class ParsedPaperSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str
    title: str
    level: int = Field(default=1, ge=1)
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    block_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_pages(self) -> ParsedPaperSection:
        if self.page_end < self.page_start:
            raise ValueError("page_end must be greater than or equal to page_start")
        return self


class ParsedPaper(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    source_pdf: str
    source_sha256: str
    parser_name: str
    parser_version: str
    parser_kind: ParserKind
    parser_config_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    pages: list[ParsedPaperPage] = Field(default_factory=list)
    sections: list[ParsedPaperSection] = Field(default_factory=list)
    blocks: list[ParsedPaperBlock] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("paper_id", "source_sha256", "parser_name", "parser_version")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value cannot be empty")
        return value

    @model_validator(mode="after")
    def validate_references(self) -> ParsedPaper:
        page_numbers = {page.page_number for page in self.pages}
        block_ids = {block.block_id for block in self.blocks}
        if len(block_ids) != len(self.blocks):
            raise ValueError("block_id values must be unique")
        for block in self.blocks:
            if page_numbers and block.page_number not in page_numbers:
                raise ValueError(f"block {block.block_id} references unknown page")
        for section in self.sections:
            missing = set(section.block_ids) - block_ids
            if missing:
                raise ValueError(f"section {section.section_id} references unknown block ids")
        return self

    @property
    def total_text_chars(self) -> int:
        return sum(len(page.text) for page in self.pages)

    @property
    def full_text(self) -> str:
        return "\n\n".join(
            page.text for page in sorted(self.pages, key=lambda item: item.page_number)
        )


class ParseCompletenessReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    source_sha256: str
    parser_name: str
    expected_page_count: int = Field(ge=0)
    parsed_page_count: int = Field(ge=0)
    pages_with_text: int = Field(ge=0)
    page_coverage: float = Field(ge=0.0, le=1.0)
    total_text_chars: int = Field(ge=0)
    section_titles: list[str] = Field(default_factory=list)
    missing_or_weak_sections: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    is_complete: bool


class ExternalPaperIdentifiers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    openalex_id: str = ""
    semantic_scholar_id: str = ""
    arxiv_id: str = ""


class ExternalPaperMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = ""
    authors: list[str] = Field(default_factory=list)
    venue: str = ""
    year: int | None = None
    publisher: str = ""
    abstract: str = ""


class OpenAccessAssertion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_open_access: bool | None = None
    license_class: LicenseClass = LicenseClass.UNKNOWN
    license_url: str = ""
    source_url: str = ""
    source: str = ""
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    note: str = ""


class ProcessedTextFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    availability: ProcessedTextAvailability = ProcessedTextAvailability.NONE
    source: str = ""
    source_record_id: str = ""
    span_kind: SpanKind = SpanKind.UNKNOWN
    structure_level: str = ""
    references_available: bool = False
    citation_contexts_available: bool = False
    content_hash: str = ""
    can_persist_full_text: bool = False
    note: str = ""


class ExternalPaperRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    identifiers: ExternalPaperIdentifiers = Field(default_factory=ExternalPaperIdentifiers)
    metadata: ExternalPaperMetadata = Field(default_factory=ExternalPaperMetadata)
    open_access: list[OpenAccessAssertion] = Field(default_factory=list)
    processed_text: list[ProcessedTextFact] = Field(default_factory=list)
    provider_records: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    response_hashes: dict[str, str] = Field(default_factory=dict)


class PaperIdentityQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    arxiv_id: str = ""
    title: str = ""
    source_pdf: str = ""
    source_sha256: str = ""


class PaperSourceChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    page_number: int = Field(ge=1)
    section_title: str = ""
    text: str = Field(min_length=1)
    token_estimate: int = Field(default=0, ge=0)


class PaperSourceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    span_id: str
    paper_id: str
    page: int = Field(ge=1)
    section_title: str = ""
    text_exact: str = Field(min_length=1)
    source_text_version: str
    text_norm_hash: str
    bbox: TextBBox | None = None
    column_index: int | None = Field(default=None, ge=0)
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)

    @field_validator("span_id", "paper_id", "source_text_version", "text_norm_hash")
    @classmethod
    def validate_non_empty_span_field(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PaperSourceSpan identifiers and hashes cannot be empty")
        return value

    @model_validator(mode="after")
    def validate_char_span(self) -> PaperSourceSpan:
        if (
            self.char_start is not None
            and self.char_end is not None
            and self.char_end < self.char_start
        ):
            raise ValueError("char_end must be greater than or equal to char_start")
        return self


class PaperExtractionWindow(BaseModel):
    """One deterministic bounded model call over parser-owned source spans."""

    model_config = ConfigDict(extra="forbid")

    window_id: str
    source_span_ids: list[str] = Field(min_length=1)
    context_char_count: int = Field(ge=1)
    input_digest: str
    output_digest: str

    @field_validator("window_id")
    @classmethod
    def require_window_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("PaperExtractionWindow identity fields cannot be empty")
        return value

    @field_validator("input_digest", "output_digest")
    @classmethod
    def require_sha256_digest(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("PaperExtractionWindow digests must be sha256 hex")
        return value

    @model_validator(mode="after")
    def require_unique_span_ids(self) -> PaperExtractionWindow:
        if len(self.source_span_ids) != len(set(self.source_span_ids)):
            raise ValueError("PaperExtractionWindow source_span_ids must be unique")
        return self


class PaperExtractionSourcePacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    packet_id: str
    paper_id: str
    source_filename: str = ""
    source_sha256: str
    parser_name: str
    parser_config_hash: str
    completeness: ParseCompletenessReport
    external_record: ExternalPaperRecord | None = None
    chunks: list[PaperSourceChunk] = Field(default_factory=list)
    source_spans: list[PaperSourceSpan] = Field(default_factory=list)
    extraction_windows: list[PaperExtractionWindow] = Field(default_factory=list)
    full_context_provided: bool
    context_char_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_source_and_window_closure(self) -> PaperExtractionSourcePacket:
        if self.completeness.paper_id != self.paper_id:
            raise ValueError("source packet completeness paper_id must match packet paper_id")
        if self.completeness.source_sha256 != self.source_sha256:
            raise ValueError("source packet completeness digest must match packet source_sha256")

        span_ids = [span.span_id for span in self.source_spans]
        if len(span_ids) != len(set(span_ids)):
            raise ValueError("source packet source span ids must be unique")
        if any(span.paper_id != self.paper_id for span in self.source_spans):
            raise ValueError("source packet spans must belong to packet paper_id")

        if not self.extraction_windows:
            return self
        window_ids = [window.window_id for window in self.extraction_windows]
        if len(window_ids) != len(set(window_ids)):
            raise ValueError("source packet extraction window ids must be unique")
        covered_ids = [
            span_id for window in self.extraction_windows for span_id in window.source_span_ids
        ]
        if len(covered_ids) != len(set(covered_ids)):
            raise ValueError("source packet extraction windows must not overlap")
        if set(covered_ids) != set(span_ids):
            raise ValueError("source packet extraction windows must exactly cover source spans")
        span_by_id = {span.span_id: span for span in self.source_spans}
        for window in self.extraction_windows:
            window_spans = [span_by_id[span_id] for span_id in window.source_span_ids]
            expected_char_count = sum(len(span.text_exact) for span in window_spans)
            if window.context_char_count != expected_char_count:
                raise ValueError("extraction window context count must match its source spans")
            canonical_window = self.model_copy(
                update={
                    "packet_id": window.window_id,
                    "source_spans": window_spans,
                    "extraction_windows": [],
                    "full_context_provided": True,
                    "context_char_count": expected_char_count,
                },
                deep=True,
            )
            if stable_hash(canonical_window) != window.input_digest:
                raise ValueError("extraction window digest must match canonical window input")
        return self


class EvidenceSpanVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    page: int = Field(ge=1)
    verified: bool
    matched_block_id: str = ""
    issue_code: str = ""
    note: str = ""


class PaperIngestItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    filename: str
    source_sha256: str = ""
    status: PaperIngestStatus = PaperIngestStatus.DISCOVERED
    parsed_artifact: str = ""
    completeness_artifact: str = ""
    external_artifact: str = ""
    source_packet_artifact: str = ""
    paper_case_artifact: str = ""
    local_literature_artifact: str = ""
    review_artifact: str = ""
    cache_key: str = ""
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class PaperIngestRunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    inbox_dir: str
    output_root: str
    parser: str
    provider: str = ""
    model: str = ""
    parse_only: bool = False
    external_lookup: bool = False
    max_workers: int = Field(default=1, ge=1)
    configuration: dict[str, Any] = Field(default_factory=dict)
    items: list[PaperIngestItem] = Field(default_factory=list)

    def status_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.items:
            counts[item.status.value] = counts.get(item.status.value, 0) + 1
        return counts


def paper_id_from_filename(path: str | Path) -> str:
    stem = Path(path).stem.lower()
    cleaned = []
    previous_dash = False
    for char in stem:
        if char.isalnum():
            cleaned.append(char)
            previous_dash = False
        elif not previous_dash:
            cleaned.append("-")
            previous_dash = True
    return "".join(cleaned).strip("-") or "paper"
