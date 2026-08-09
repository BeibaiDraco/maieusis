# Scanned PDFs

[Documentation home](INDEX.md) · [Manual setup](MANUAL_SETUP.md)

A scanned paper has pictures of pages instead of selectable text, so it cannot be read directly.
Fix this in three short steps: make a searchable copy with any OCR tool, write a small receipt
binding the two files, and drop all three in your papers inbox.

The original file always stays the paper's identity. The searchable copy is only used to read the
text, and it is accepted only when the receipt's checksums match both files exactly.

No OCR engine is bundled with Maieusis, and there is no Maieusis command that produces the
derivative or the receipt. That is deliberate: the derivative is made outside the product with
tools you choose, and it enters only through the receipt below. Writing the receipt is a few lines
of scripting in whatever language you prefer.

## 1. Make a searchable copy

Use any OCR tool you like. With the widely used `ocrmypdf`:

```bash
ocrmypdf scan.pdf scan.ocr.pdf
```

Name the copy `<original name>.ocr.pdf` and keep it next to the original.

## 2. Write the admission receipt

Create `scan.derivative.yaml` next to the PDF:

```yaml
schema_version: source_derivative_receipt/v1
original_filename: scan.pdf
original_sha256: <sha256 of scan.pdf>
original_page_count: 16
derived_filename: scan.ocr.pdf
derived_sha256: <sha256 of scan.ocr.pdf>
derived_page_count: 16
tool_label: ocrmypdf-16.4.1
page_map:
  - {original_page: 1, derived_page: 1}
  - {original_page: 2, derived_page: 2}
  # ... one entry per page
```

Every field is required. `page_map` must cover every page; when OCR preserves page order, as it
normally does, the mapping is one-to-one and easy to generate in a loop. If the page counts differ,
map the pages that correspond and leave out the ones that do not.

Both checksums are plain SHA-256 of the file bytes — `shasum -a 256 scan.pdf` on macOS, or
`sha256sum scan.pdf` on Linux.

## 3. Done

Keep all three files together in the inbox:

```text
papers/inbox/
  scan.pdf              # the original — stays the paper's identity
  scan.ocr.pdf          # the searchable copy — used only to read text
  scan.derivative.yaml  # the receipt binding the two
```

The next run reads the searchable copy while every record still points at the original file's
checksum. If either file changes after the receipt was written, that paper is skipped with a clear
reason and the other papers continue normally — rewrite the receipt to fix it.

## Bundled sources

If one PDF contains more than one article (for example a whole journal issue), declare which pages
are your article with a small companion file `scan.article_span.yaml`:

```yaml
schema_version: article_span/v1
page_start: 12
page_end: 27
reason: bundled_journal_issue
```

Pages outside the range are ignored entirely; the record keeps both the whole-file checksum and the
declared page range. This works on its own or together with a searchable copy.

---

[Documentation home](INDEX.md) · [Manual setup](MANUAL_SETUP.md)
