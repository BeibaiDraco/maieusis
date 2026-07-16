"""Generic seed-link retrieval for the documentation-side narrator.

Given one seed link, resolve it to a small set of proposal-safe ``ProposalSourceExcerpt``s via a
BOUNDED set of resolvers (not a universal scraper): a DANDI dandiset id, a DOI (Crossref), or a
direct URL / PDF. When a link yields only navigation noise or nothing, emit an honest
``is_metadata_only`` excerpt — never fabricate content. This module resolves the LINK only; the
seed's optional ``docs`` are reserved for GF-2c's Source D and are never parsed here.

The HTML/HTTP helpers here were generalized out of the old dataset-specific narrative provider. Every
network entry point is injectable so the mock suite runs with zero real HTTP.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import json
import re
import tempfile
import urllib.parse
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from ...schemas.dataset_narrative import DatasetNarrativeSourceType
from ..context.dataset_narrative import ProposalSourceExcerpt
from ..paper_ingest.parsing import PdfParsingError, PopplerTextPdfProvider

TextGetter = Callable[[str], str]
JsonGetter = Callable[[str], dict[str, Any]]
BytesGetter = Callable[[str], bytes]

LinkKind = Literal["dandi", "doi", "url"]

_USER_AGENT = "maieusis/0.1.0"
_DANDI_API = "https://api.dandiarchive.org/api"
_CROSSREF_API = "https://api.crossref.org/works"
_DANDI_ID_RE = re.compile(r"(?:dandi[:/]|dandiset/|dandisets/)\s*0*(\d{3,6})", re.IGNORECASE)
_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"'<>]+)", re.IGNORECASE)


# ---------------------------------------------------------------------------- real network entry points


def http_get_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read()
    return body.decode("utf-8", errors="replace") if isinstance(body, bytes) else str(body)


def http_get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    return data if isinstance(data, dict) else {"data": data}


def http_get_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return bytes(response.read())


# ---------------------------------------------------------------------------- HTML / text helpers


def html_to_text(value: str) -> str:
    main_match = re.search(
        r"<main\b[^>]*>(?P<body>.*?)</main>", value, flags=re.IGNORECASE | re.DOTALL
    )
    if main_match is None:
        main_match = re.search(
            r"<div\b[^>]*(?:role=[\"']main[\"']|class=[\"'][^\"']*(?:document|body|article)[^\"']*[\"'])[^>]*>(?P<body>.*?)</div>",
            value,
            flags=re.IGNORECASE | re.DOTALL,
        )
    if main_match is not None:
        value = main_match.group("body")
    for tag in ("script", "style", "nav", "aside", "footer"):
        value = re.sub(rf"<{tag}\b.*?</{tag}>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    cleaned = re.sub(r"\s+", " ", value).strip()
    for pattern in (
        r"previous next",
        r"table of contents",
        r"edit on github",
        r"search docs",
        r"copyright",
    ):
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def keyword_window(text: str, *, keywords: list[str], max_chars: int) -> str:
    normalized = text.lower()
    starts = [normalized.find(k.lower()) for k in keywords if normalized.find(k.lower()) >= 0]
    if not starts:
        return text[:max_chars].strip()
    start = max(0, min(starts) - max_chars // 4)
    return text[start : start + max_chars].strip()


def metadata_excerpt(title: str, url: str) -> str:
    return f"{title}. Public source URL used as proposal-stage dataset narrative evidence: {url}"


def _jats_abstract_to_text(abstract: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", abstract)).strip()


# ---------------------------------------------------------------------------- link-kind detection


def detect_link_kind(link: str) -> LinkKind:
    if _DANDI_ID_RE.search(link):
        return "dandi"
    if "doi.org/" in link.lower() or _DOI_RE.search(link):
        return "doi"
    return "url"


def _dandi_id(link: str) -> str | None:
    match = _DANDI_ID_RE.search(link)
    if not match:
        return None
    return match.group(1).zfill(6)


def _doi_from_link(link: str) -> str | None:
    match = _DOI_RE.search(link)
    return match.group(1).rstrip(".").rstrip("/") if match else None


# ---------------------------------------------------------------------------- resolvers (each defensive)


def resolve_dandi(
    link: str,
    *,
    dataset_id: str,
    http_get_json: JsonGetter = http_get_json,
    max_excerpt_chars: int = 1600,
    max_related_dois: int = 1,
    resolve_doi_fn: Callable[..., list[ProposalSourceExcerpt]] | None = None,
) -> list[ProposalSourceExcerpt]:
    dandi_id = _dandi_id(link)
    if dandi_id is None:
        return [_metadata_stub("DANDI dataset", link)]
    metadata = _fetch_dandi_metadata(dandi_id, http_get_json=http_get_json)
    if metadata is None:
        return [_metadata_stub(f"DANDI:{dandi_id}", link)]
    name = str(metadata.get("name", "") or "").strip()
    description = str(metadata.get("description", "") or "").strip()
    body = " ".join(part for part in (name, description) if part).strip()
    excerpts: list[ProposalSourceExcerpt] = []
    if body:
        excerpts.append(
            ProposalSourceExcerpt(
                source_id=f"dandi:{dandi_id}:metadata",
                source_type=DatasetNarrativeSourceType.DATASET_DOCUMENTATION,
                title=name or f"DANDI:{dandi_id}",
                locator=link,
                excerpt=body[:max_excerpt_chars],
                section="dandi_metadata",
                snippet_kind="dandi_metadata",
            )
        )
    else:
        excerpts.append(_metadata_stub(name or f"DANDI:{dandi_id}", link))
    # Bounded enrichment: resolve the first related-publication DOI when present.
    resolver = resolve_doi_fn or resolve_doi
    for doi in _dandi_related_dois(metadata)[:max_related_dois]:
        try:
            excerpts.extend(resolver(f"https://doi.org/{doi}", max_excerpt_chars=max_excerpt_chars))
        except Exception:
            continue
    return excerpts


def resolve_doi(
    link: str,
    *,
    http_get_json: JsonGetter = http_get_json,
    max_excerpt_chars: int = 1600,
) -> list[ProposalSourceExcerpt]:
    doi = _doi_from_link(link)
    if doi is None:
        return [_metadata_stub("DOI reference", link)]
    try:
        data = http_get_json(f"{_CROSSREF_API}/{urllib.parse.quote(doi, safe='')}")
    except Exception:
        return [_metadata_stub(f"DOI {doi}", link)]
    message = data.get("message", data) if isinstance(data, dict) else {}
    title_list = message.get("title") or []
    title = (title_list[0] if isinstance(title_list, list) and title_list else "").strip()
    container = message.get("container-title") or []
    container_title = (container[0] if isinstance(container, list) and container else "").strip()
    abstract = _jats_abstract_to_text(str(message.get("abstract", "") or ""))
    body = " ".join(part for part in (title, container_title, abstract) if part).strip()
    if not body:
        return [_metadata_stub(title or f"DOI {doi}", link)]
    return [
        ProposalSourceExcerpt(
            source_id=f"doi:{doi}",
            source_type=DatasetNarrativeSourceType.DATASET_PAPER,
            title=title or f"DOI {doi}",
            locator=f"https://doi.org/{doi}",
            excerpt=body[:max_excerpt_chars],
            section="crossref_metadata",
            snippet_kind="crossref_metadata",
        )
    ]


def resolve_url(
    link: str,
    *,
    http_get_text: TextGetter = http_get_text,
    http_get_bytes: BytesGetter = http_get_bytes,
    max_excerpt_chars: int = 1600,
) -> list[ProposalSourceExcerpt]:
    if link.lower().split("?")[0].endswith(".pdf"):
        return _resolve_pdf_url(
            link, http_get_bytes=http_get_bytes, max_excerpt_chars=max_excerpt_chars
        )
    try:
        text = html_to_text(http_get_text(link))
    except Exception:
        text = ""
    if not text:
        return [_metadata_stub("Dataset documentation page", link)]
    excerpt = (
        keyword_window(
            text,
            keywords=["dataset", "data", "recording", "task", "subject", "release", "public"],
            max_chars=max_excerpt_chars,
        )
        or text[:max_excerpt_chars]
    )
    return [
        ProposalSourceExcerpt(
            source_id=f"url:{_slug(link)}",
            source_type=DatasetNarrativeSourceType.DATASET_DOCUMENTATION,
            title="Dataset documentation page",
            locator=link,
            excerpt=excerpt,
            section="html_page",
            snippet_kind="html_excerpt",
        )
    ]


def resolve_seed_link(
    link: str,
    *,
    dataset_id: str,
    http_get_text: TextGetter = http_get_text,
    http_get_json: JsonGetter = http_get_json,
    http_get_bytes: BytesGetter = http_get_bytes,
    max_excerpt_chars: int = 1600,
) -> list[ProposalSourceExcerpt]:
    """Resolve one seed LINK to proposal-safe excerpts (never the seed's docs — those are Source D)."""
    kind = detect_link_kind(link)
    if kind == "dandi":
        return resolve_dandi(
            link,
            dataset_id=dataset_id,
            http_get_json=http_get_json,
            max_excerpt_chars=max_excerpt_chars,
        )
    if kind == "doi":
        return resolve_doi(link, http_get_json=http_get_json, max_excerpt_chars=max_excerpt_chars)
    return resolve_url(
        link,
        http_get_text=http_get_text,
        http_get_bytes=http_get_bytes,
        max_excerpt_chars=max_excerpt_chars,
    )


# ---------------------------------------------------------------------------- internals


def _fetch_dandi_metadata(dandi_id: str, *, http_get_json: JsonGetter) -> dict[str, Any] | None:
    try:
        dandiset = http_get_json(f"{_DANDI_API}/dandisets/{dandi_id}/")
    except Exception:
        return None
    version = ""
    published = dandiset.get("most_recent_published_version")
    if isinstance(published, dict):
        version = str(published.get("version", "") or "")
    if not version:
        draft = dandiset.get("draft_version")
        version = str(draft.get("version", "") if isinstance(draft, dict) else "draft") or "draft"
    try:
        payload = http_get_json(f"{_DANDI_API}/dandisets/{dandi_id}/versions/{version}/")
    except Exception:
        return None
    metadata = payload.get("metadata")
    return metadata if isinstance(metadata, dict) else payload


def _dandi_related_dois(metadata: dict[str, Any]) -> list[str]:
    dois: list[str] = []
    for resource in metadata.get("relatedResource", []) or []:
        if not isinstance(resource, dict):
            continue
        for value in (resource.get("identifier", ""), resource.get("url", "")):
            doi = _doi_from_link(str(value or ""))
            if doi and doi not in dois:
                dois.append(doi)
    return dois


def _resolve_pdf_url(
    link: str, *, http_get_bytes: BytesGetter, max_excerpt_chars: int
) -> list[ProposalSourceExcerpt]:
    try:
        data = http_get_bytes(link)
    except Exception:
        return [_metadata_stub("Dataset PDF", link)]
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "seed.pdf"
        pdf_path.write_bytes(data)
        try:
            parsed = PopplerTextPdfProvider().parse(pdf_path, paper_id="seed-pdf")
        except PdfParsingError:
            return [_metadata_stub("Dataset PDF", link)]
        text = " ".join(page.text for page in parsed.pages if page.text.strip())
    if not text.strip():
        return [_metadata_stub("Dataset PDF", link)]
    excerpt = (
        keyword_window(
            text,
            keywords=["abstract", "dataset", "data", "task", "recording"],
            max_chars=max_excerpt_chars,
        )
        or text[:max_excerpt_chars]
    )
    return [
        ProposalSourceExcerpt(
            source_id=f"pdf:{_slug(link)}",
            source_type=DatasetNarrativeSourceType.DATASET_PAPER,
            title="Dataset PDF",
            locator=link,
            excerpt=excerpt,
            section="pdf_text",
            snippet_kind="pdf_excerpt",
        )
    ]


def _metadata_stub(title: str, link: str) -> ProposalSourceExcerpt:
    return ProposalSourceExcerpt(
        source_id=f"metadata:{_slug(link)}",
        source_type=DatasetNarrativeSourceType.METADATA_SUMMARY,
        title=title or "Dataset reference",
        locator=link,
        excerpt=metadata_excerpt(title or "Dataset reference", link),
        section="metadata_only",
        snippet_kind="metadata_stub",
        is_metadata_only=True,
    )


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:48] or "link"
