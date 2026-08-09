from __future__ import annotations

import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from ...provenance import sha256_file, stable_hash
from ...schemas.paper_ingest import (
    BlockType,
    ParseCompletenessReport,
    ParsedPaper,
    ParsedPaperBlock,
    ParsedPaperPage,
    ParsedPaperSection,
    ParserKind,
)


class PdfParsingError(RuntimeError):
    pass


class PdfParsingProvider(ABC):
    parser_name: str
    parser_version: str
    parser_kind: ParserKind

    @abstractmethod
    def parse(self, pdf_path: Path, *, paper_id: str) -> ParsedPaper:
        raise NotImplementedError


class AutoPdfParsingProvider(PdfParsingProvider):
    """Try the best local parser first, then fall back to a deterministic text parser."""

    parser_name = "auto"
    parser_version = "v1"
    parser_kind = ParserKind.POPPLER_TEXT

    def __init__(self, *, prefer_docling: bool = True):
        self.prefer_docling = prefer_docling

    def parse(self, pdf_path: Path, *, paper_id: str) -> ParsedPaper:
        warnings: list[str] = []
        if self.prefer_docling:
            try:
                return DoclingPdfProvider().parse(pdf_path, paper_id=paper_id)
            except PdfParsingError as error:
                warnings.append(f"docling_unavailable_or_failed: {error}")
        parsed = PopplerTextPdfProvider().parse(pdf_path, paper_id=paper_id)
        parsed.warnings.extend(warnings)
        return parsed


class DoclingPdfProvider(PdfParsingProvider):
    """Docling adapter.

    Docling supplies richer document structure when installed. We still normalize through the
    Poppler page-text adapter for page-level evidence verification in this first version.

    OCR is opt-in (``do_ocr``, default off): docling's own library default runs full-page OCR on
    every page — catastrophically slow on ordinary text-layer PDFs. Pages without a text layer
    surface honestly through the parse-completeness report instead of being silently OCRed.
    """

    parser_name = "docling"
    parser_kind = ParserKind.DOCLING

    def __init__(self, *, config: dict[str, Any] | None = None, do_ocr: bool | None = None):
        self.config = config or {}
        self.do_ocr = bool(self.config.get("do_ocr", False)) if do_ocr is None else do_ocr
        self.parser_version = self._resolve_version()

    def parse(self, pdf_path: Path, *, paper_id: str) -> ParsedPaper:
        try:
            module = import_module("docling.document_converter")
            document_converter = cast(Any, module).DocumentConverter
        except ImportError as exc:
            raise PdfParsingError("Install optional PDF dependencies: uv sync --extra pdf") from exc

        try:
            converter_kwargs = docling_converter_kwargs(do_ocr=self.do_ocr)
        except Exception as exc:
            # Fail closed: never fall back to a bare converter whose library default is full-page
            # OCR. AutoPdfParsingProvider catches this and falls back to the Poppler text parser.
            raise PdfParsingError(f"Docling pipeline options unavailable: {exc}") from exc

        try:
            converter = document_converter(**converter_kwargs)
            result = converter.convert(str(pdf_path))
            document = result.document
            markdown = document.export_to_markdown()
        except Exception as exc:  # pragma: no cover - depends on optional external parser
            raise PdfParsingError(f"Docling failed to parse {pdf_path.name}: {exc}") from exc

        # Docling's OWN text, grouped by its OWN page attribution. Until 2026-08-04 this method
        # exported that markdown, used it ONLY to compute a hash for metadata, and returned the
        # POPPLER parse stamped `parser_kind = DOCLING` -- so a caller reading `parser_kind` saw
        # the better parser while every downstream stage read the worse text. Measured across the
        # 25-PDF climate corpus: poppler median hyphen-break density 1.30 per 1000 chars against
        # docling 0.03, cleaner on 20 of 25. On the older two-column papers poppler interleaves
        # three columns line by line and breaks words across them ("ves pene- / trate to
        # successively lower altitudes"), which is why citation markers could not be found and why
        # an extracted "sentence" was a fragment.
        #
        # The stated reason for discarding it -- "page-level evidence verification" -- was not a
        # real constraint: docling attributes every text item to a page (238 of 238 on
        # 11-baldwin-dunkerton-2001, pages 1-6). Grouping by that page number reproduces exactly the
        # one-block-per-page shape and the `{paper_id}-p{page:04d}` id scheme, so evidence spans,
        # block counts and every downstream resolution check are untouched and only the words change.
        by_page: dict[int, list[str]] = {}
        for item, _level in document.iterate_items():
            text = str(getattr(item, "text", "") or "").strip()
            if not text:
                continue
            provenance = getattr(item, "prov", None) or []
            page_no = getattr(provenance[0], "page_no", None) if provenance else None
            if page_no is None:
                continue
            by_page.setdefault(int(page_no), []).append(text)
        if not by_page:
            raise PdfParsingError(
                f"Docling parsed {pdf_path.name} but attributed no text to any page"
            )
        last_page = max(by_page)
        page_texts = ["\n".join(by_page.get(number, [])) for number in range(1, last_page + 1)]
        return _parsed_paper_from_pages(
            paper_id=paper_id,
            pdf_path=pdf_path,
            page_texts=page_texts,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            parser_kind=ParserKind.DOCLING,
            extra_metadata={
                "docling_markdown_sha256": stable_hash(markdown),
                "docling_config": self.config,
                "docling_do_ocr": self.do_ocr,
                **self.extra_metadata,
            }
            if hasattr(self, "extra_metadata")
            else {
                "docling_markdown_sha256": stable_hash(markdown),
                "docling_config": self.config,
                "docling_do_ocr": self.do_ocr,
            },
            expected_page_count=last_page,
        )

    @staticmethod
    def _resolve_version() -> str:
        try:
            from importlib.metadata import version

            return version("docling")
        except Exception:
            return "unknown"


class PopplerTextPdfProvider(PdfParsingProvider):
    parser_kind = ParserKind.POPPLER_TEXT

    def __init__(
        self,
        *,
        parser_name: str = "poppler_text",
        parser_version: str | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ):
        self.parser_name = parser_name
        self.parser_version = parser_version or _poppler_version()
        self.extra_metadata = extra_metadata or {}

    def parse(self, pdf_path: Path, *, paper_id: str) -> ParsedPaper:
        pdf_path = pdf_path.expanduser()
        if not pdf_path.exists():
            raise PdfParsingError(f"PDF not found: {pdf_path}")
        if shutil.which("pdftotext") is None:
            raise PdfParsingError("pdftotext is required for the fallback parser")

        text = _run_text_command(["pdftotext", "-layout", str(pdf_path), "-"])
        page_count = _pdf_page_count(pdf_path)
        raw_pages = text.split("\f")
        if raw_pages and not raw_pages[-1].strip():
            raw_pages = raw_pages[:-1]
        if page_count and len(raw_pages) < page_count:
            raw_pages.extend([""] * (page_count - len(raw_pages)))
        return _parsed_paper_from_pages(
            paper_id=paper_id,
            pdf_path=pdf_path,
            page_texts=raw_pages,
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            parser_kind=self.parser_kind,
            extra_metadata=self.extra_metadata,
            expected_page_count=page_count,
        )


def _parsed_paper_from_pages(
    *,
    paper_id: str,
    pdf_path: Path,
    page_texts: list[str],
    parser_name: str,
    parser_version: str,
    parser_kind: ParserKind,
    extra_metadata: dict[str, Any],
    expected_page_count: int,
) -> ParsedPaper:
    """Build the ParsedPaper both parsers return, so their SHAPE cannot drift.

    Extracted rather than duplicated because the docling parser exists to change the TEXT and
    nothing else. Block granularity stays one block per page and `block_id` stays
    ``{paper_id}-p{page:04d}`` -- which is what an evidence span points at, so a re-parse with a
    better parser leaves every downstream id scheme, block count and resolution check untouched
    and only the words improve.
    """
    pages = [
        ParsedPaperPage(page_number=index + 1, text=(text or "").strip())
        for index, text in enumerate(page_texts)
    ]
    if not pages and expected_page_count:
        pages = [ParsedPaperPage(page_number=n + 1, text="") for n in range(expected_page_count)]
    blocks = [
        ParsedPaperBlock(
            block_id=f"{paper_id}-p{page.page_number:04d}",
            page_number=page.page_number,
            text=page.text or " ",
            block_type=BlockType.PAGE_TEXT,
            section_title=_guess_page_section(page.text),
            source_path=pdf_path.as_posix(),
        )
        for page in pages
        if page.text.strip()
    ]
    return ParsedPaper(
        paper_id=paper_id,
        source_pdf=pdf_path.as_posix(),
        source_sha256=sha256_file(pdf_path),
        parser_name=parser_name,
        parser_version=parser_version,
        parser_kind=parser_kind,
        parser_config_hash=stable_hash(
            {"parser": parser_name, "version": parser_version, "metadata": extra_metadata}
        ),
        pages=pages,
        sections=_build_sections_from_blocks(blocks),
        blocks=blocks,
        metadata={
            "expected_page_count": expected_page_count,
            "source_filename": pdf_path.name,
            **extra_metadata,
        },
    )


def docling_converter_kwargs(*, do_ocr: bool) -> dict[str, Any]:
    """Explicit docling converter options — OCR only when asked for, never by library default."""
    converter_module = import_module("docling.document_converter")
    base_models = import_module("docling.datamodel.base_models")
    pipeline_options_module = import_module("docling.datamodel.pipeline_options")
    options = cast(Any, pipeline_options_module).PdfPipelineOptions(do_ocr=do_ocr)
    pdf_format = cast(Any, converter_module).PdfFormatOption(pipeline_options=options)
    return {"format_options": {cast(Any, base_models).InputFormat.PDF: pdf_format}}


def build_pdf_parser(name: str) -> PdfParsingProvider:
    """Resolve a configured ``paperbank.parser`` name to a provider — the ONLY name→parser map.

    ``poppler_text`` (the product default) selects the deterministic Poppler text-layer parser and
    never touches docling/OCR.
    """
    normalized = name.strip().lower()
    if normalized == "auto":
        return AutoPdfParsingProvider()
    if normalized == "docling":
        return DoclingPdfProvider()
    if normalized in {"poppler", "poppler_text"}:
        return PopplerTextPdfProvider()
    raise ValueError(f"Unknown PDF parser {name!r}: expected auto, docling, or poppler_text")


def build_completeness_report(
    parsed: ParsedPaper,
    *,
    min_page_coverage: float = 0.8,
    min_total_chars: int = 1000,
) -> ParseCompletenessReport:
    expected = int(parsed.metadata.get("expected_page_count") or len(parsed.pages))
    parsed_count = len(parsed.pages)
    pages_with_text = sum(1 for page in parsed.pages if page.text.strip())
    denominator = expected or parsed_count or 1
    page_coverage = min(1.0, pages_with_text / denominator)
    total_chars = parsed.total_text_chars
    titles = [section.title for section in parsed.sections]
    title_lc = " ".join(titles).lower()
    weak_sections: list[str] = []
    if "abstract" not in title_lc and not _contains_heading(parsed.full_text, "abstract"):
        weak_sections.append("abstract_not_detected")
    if not any(label in title_lc for label in ["method", "materials"]) and not _contains_heading(
        parsed.full_text, "method"
    ):
        weak_sections.append("methods_not_detected")
    if "reference" not in title_lc and not _contains_heading(parsed.full_text, "references"):
        weak_sections.append("references_not_detected")

    risks: list[str] = []
    if expected and parsed_count != expected:
        risks.append("page_count_mismatch")
    if page_coverage < min_page_coverage:
        risks.append("low_page_text_coverage")
    if total_chars < min_total_chars:
        risks.append("too_little_extracted_text")
    if not parsed.blocks:
        risks.append("no_text_blocks")
    is_complete = (
        not any(
            risk in risks
            for risk in [
                "page_count_mismatch",
                "low_page_text_coverage",
                "too_little_extracted_text",
                "no_text_blocks",
            ]
        )
        and not weak_sections
    )
    return ParseCompletenessReport(
        paper_id=parsed.paper_id,
        source_sha256=parsed.source_sha256,
        parser_name=parsed.parser_name,
        expected_page_count=expected,
        parsed_page_count=parsed_count,
        pages_with_text=pages_with_text,
        page_coverage=page_coverage,
        total_text_chars=total_chars,
        section_titles=titles,
        missing_or_weak_sections=weak_sections,
        risks=risks,
        is_complete=is_complete,
    )


def _run_text_command(args: list[str]) -> str:
    completed = subprocess.run(args, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise PdfParsingError(completed.stderr.strip() or f"Command failed: {' '.join(args)}")
    return completed.stdout


def _pdf_page_count(pdf_path: Path) -> int:
    if shutil.which("pdfinfo") is None:
        return 0
    completed = subprocess.run(
        ["pdfinfo", str(pdf_path)], check=False, capture_output=True, text=True
    )
    if completed.returncode != 0:
        return 0
    match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, flags=re.MULTILINE)
    return int(match.group(1)) if match else 0


def _poppler_version() -> str:
    if shutil.which("pdftotext") is None:
        return "missing"
    completed = subprocess.run(["pdftotext", "-v"], check=False, capture_output=True, text=True)
    version_text = completed.stderr.strip() or completed.stdout.strip() or "unknown"
    return version_text.splitlines()[0]


def _guess_page_section(text: str) -> str:
    for line in text.splitlines()[:40]:
        cleaned = line.strip()
        if not cleaned:
            continue
        lower = cleaned.lower().strip(" .:")
        if lower in {
            "abstract",
            "introduction",
            "methods",
            "materials and methods",
            "results",
            "discussion",
            "references",
        }:
            return cleaned
    return "full_text"


def _build_sections_from_blocks(blocks: list[ParsedPaperBlock]) -> list[ParsedPaperSection]:
    if not blocks:
        return []
    sections: list[ParsedPaperSection] = []
    current_title = blocks[0].section_title or "full_text"
    current_ids: list[str] = []
    page_start = blocks[0].page_number
    for block in blocks:
        title = block.section_title or current_title
        if title != current_title and current_ids:
            sections.append(
                ParsedPaperSection(
                    section_id=f"sec-{len(sections) + 1:03d}",
                    title=current_title,
                    page_start=page_start,
                    page_end=blocks_by_id(blocks, current_ids[-1]).page_number,
                    block_ids=current_ids,
                )
            )
            current_title = title
            current_ids = []
            page_start = block.page_number
        current_ids.append(block.block_id)
    if current_ids:
        sections.append(
            ParsedPaperSection(
                section_id=f"sec-{len(sections) + 1:03d}",
                title=current_title,
                page_start=page_start,
                page_end=blocks_by_id(blocks, current_ids[-1]).page_number,
                block_ids=current_ids,
            )
        )
    return sections


def blocks_by_id(blocks: list[ParsedPaperBlock], block_id: str) -> ParsedPaperBlock:
    for block in blocks:
        if block.block_id == block_id:
            return block
    raise KeyError(block_id)


def _contains_heading(text: str, heading: str) -> bool:
    pattern = rf"(?im)^\s*(\d+\.?\s*)?{re.escape(heading)}s?\s*$"
    return re.search(pattern, text) is not None
