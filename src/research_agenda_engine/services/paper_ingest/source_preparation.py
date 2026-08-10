"""Source preparation: derivative admission and article-span isolation (UPD2-Card-5).

Two optional, fail-closed sidecars next to an inbox PDF change WHAT is parsed while the
ORIGINAL bytes stay the paper's identity:

- ``<stem>.derivative.yaml`` + ``<stem>.ocr.pdf`` (CLIM-02, Option B): an externally produced
  searchable derivative is admitted only through a verified ``SourceDerivativeReceipt``; the
  derived bytes are parsed for text but ``source_sha256`` remains the original's digest —
  the derived digest never launders identity. No OCR engine enters the dependency tree.
- ``<stem>.article_span.yaml`` (CLIM-03): a typed page span isolates ONE article from a
  bundled source; pages outside the span never enter the parsed artifact, and the span rides
  the metadata as source/article lineage.

Any mismatch (hash, filename, page count, out-of-range span) raises
``SourcePreparationError`` — the pipeline's per-paper isolation turns that into one failed
paper with a readable reason while safe siblings continue.
"""

from __future__ import annotations

from pathlib import Path

from ...io import load_model
from ...provenance import sha256_file, stable_hash
from ...schemas.paper_ingest import (
    ArticleSpanDeclaration,
    ParsedPaper,
    SourceDerivativeReceipt,
)
from .parsing import _build_sections_from_blocks


class SourcePreparationError(ValueError):
    """A sidecar exists but its bindings do not verify — fail closed for this paper only."""


def _sidecar(pdf_path: Path, suffix: str) -> Path:
    return pdf_path.parent / f"{pdf_path.stem}{suffix}"


def derived_companion_names(inbox_dir: Path) -> set[str]:
    """Names of ``*.ocr.pdf`` files declared by a derivative receipt — never standalone papers."""
    names: set[str] = set()
    for receipt_path in sorted(inbox_dir.glob("*.derivative.yaml")):
        try:
            receipt = load_model(receipt_path, SourceDerivativeReceipt)
        except (ValueError, TypeError, OSError):
            continue  # the owning paper fails closed at resolve time; selection stays inclusive
        names.add(receipt.derived_filename)
    return names


class PreparedSource:
    """Resolved preparation for one inbox PDF (internal, never persisted)."""

    def __init__(
        self,
        *,
        original_path: Path,
        parse_path: Path,
        receipt: SourceDerivativeReceipt | None = None,
        receipt_digest: str = "",
        article_span: ArticleSpanDeclaration | None = None,
    ) -> None:
        self.original_path = original_path
        self.parse_path = parse_path
        self.receipt = receipt
        self.receipt_digest = receipt_digest
        self.article_span = article_span

    @property
    def preparation_digest(self) -> str:
        """Cache-key contribution: any change to preparation inputs invalidates reuse."""
        if self.receipt is None and self.article_span is None:
            return ""
        return stable_hash(
            {
                "receipt": self.receipt.model_dump(mode="json") if self.receipt else None,
                "receipt_digest": self.receipt_digest,
                "article_span": (
                    self.article_span.model_dump(mode="json") if self.article_span else None
                ),
            }
        )


def resolve_source_preparation(pdf_path: Path) -> PreparedSource:
    """Read and VERIFY the optional sidecars for one inbox PDF (fail-closed)."""

    parse_path = pdf_path
    receipt: SourceDerivativeReceipt | None = None
    receipt_digest = ""
    receipt_path = _sidecar(pdf_path, ".derivative.yaml")
    if receipt_path.exists():
        try:
            receipt = load_model(receipt_path, SourceDerivativeReceipt)
        except Exception as exc:
            raise SourcePreparationError(f"invalid derivative receipt: {exc}") from exc
        if receipt.original_filename != pdf_path.name:
            raise SourcePreparationError(
                "derivative receipt original_filename does not name this PDF"
            )
        original_sha = sha256_file(pdf_path)
        if original_sha != receipt.original_sha256:
            raise SourcePreparationError(
                "original PDF bytes do not match the derivative receipt original_sha256"
            )
        derived_path = pdf_path.parent / receipt.derived_filename
        if not derived_path.exists():
            raise SourcePreparationError(
                f"derived file named by the receipt is missing: {receipt.derived_filename}"
            )
        derived_sha = sha256_file(derived_path)
        if derived_sha != receipt.derived_sha256:
            raise SourcePreparationError(
                "derived file bytes do not match the derivative receipt derived_sha256"
            )
        receipt_digest = stable_hash(receipt.model_dump(mode="json"))
        parse_path = derived_path

    article_span: ArticleSpanDeclaration | None = None
    span_path = _sidecar(pdf_path, ".article_span.yaml")
    if span_path.exists():
        try:
            article_span = load_model(span_path, ArticleSpanDeclaration)
        except Exception as exc:
            raise SourcePreparationError(f"invalid article-span declaration: {exc}") from exc

    return PreparedSource(
        original_path=pdf_path,
        parse_path=parse_path,
        receipt=receipt,
        receipt_digest=receipt_digest,
        article_span=article_span,
    )


def apply_source_preparation(parsed: ParsedPaper, preparation: PreparedSource) -> ParsedPaper:
    """Re-bind identity to the original bytes and isolate the declared article span."""

    if preparation.receipt is None and preparation.article_span is None:
        return parsed

    data = parsed.model_dump(mode="python")
    metadata = dict(data["metadata"])
    warnings = list(data["warnings"])

    if preparation.receipt is not None:
        receipt = preparation.receipt
        expected = metadata.get("expected_page_count")
        if expected not in (None, 0) and expected != receipt.derived_page_count:
            raise SourcePreparationError(
                "derived file page count does not match the derivative receipt"
            )
        # Identity retention: the ORIGINAL bytes stay the paper's identity; the derived digest
        # is recorded alongside and never becomes source_sha256.
        data["source_pdf"] = preparation.original_path.as_posix()
        data["source_sha256"] = receipt.original_sha256
        metadata["source_filename"] = preparation.original_path.name
        metadata["derived_pdf"] = receipt.derived_filename
        metadata["derived_sha256"] = receipt.derived_sha256
        metadata["derivative_receipt_digest"] = preparation.receipt_digest
        metadata["derivative_tool_label"] = receipt.tool_label
        metadata["original_page_count"] = receipt.original_page_count
        warnings.append(f"derivative_admitted:{receipt.tool_label}")

    if preparation.article_span is not None:
        span = preparation.article_span
        available = max((page["page_number"] for page in data["pages"]), default=0)
        if span.page_end > available:
            raise SourcePreparationError(
                f"article span {span.page_start}-{span.page_end} exceeds the "
                f"{available}-page source"
            )
        pages = [
            page
            for page in data["pages"]
            if span.page_start <= page["page_number"] <= span.page_end
        ]
        blocks = [
            block
            for block in data["blocks"]
            if span.page_start <= block["page_number"] <= span.page_end
        ]
        data["pages"] = pages
        data["blocks"] = blocks
        data["sections"] = [
            section.model_dump(mode="python")
            for section in _build_sections_from_blocks(
                [
                    parsed_block
                    for parsed_block in parsed.blocks
                    if span.page_start <= parsed_block.page_number <= span.page_end
                ]
            )
        ]
        metadata["source_page_count"] = metadata.get("expected_page_count")
        metadata["expected_page_count"] = span.page_end - span.page_start + 1
        metadata["article_page_start"] = span.page_start
        metadata["article_page_end"] = span.page_end
        metadata["article_span_reason"] = span.reason
        warnings.append(f"article_span_isolated:{span.page_start}-{span.page_end}")

    data["metadata"] = metadata
    data["warnings"] = warnings
    return ParsedPaper.model_validate(data)
