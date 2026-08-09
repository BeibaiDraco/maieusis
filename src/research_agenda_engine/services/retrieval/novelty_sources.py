"""Public scholarly-index adapters used only for proposal-stage prior recall.

Provider scores are diagnostic ranking signals.  They never decide novelty admission.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from ...provenance import stable_hash
from ..paper_ingest.external_lookup import ExternalLookupError, OpenAlexRequestCoordinator

JsonGetter = Callable[[str, dict[str, str]], dict[str, Any]]


@dataclass(frozen=True)
class NoveltySearchHit:
    provider_id: str
    source_record_id: str
    title: str
    abstract: str
    doi: str
    url: str
    year: int | None
    query_id: str
    response_digest: str
    retrieval_score: float


class NoveltyLeadResolutionMethod(StrEnum):
    """The one deterministic scholarly request allowed for a web-discovered lead."""

    DOI_SINGLE_ENTITY = "doi_single_entity"
    TITLE_RECONCILIATION = "title_reconciliation"
    NONE = "none"


class NoveltyLeadResolutionStatus(StrEnum):
    """Outcome of a bounded scholarly reconciliation attempt."""

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    ERROR = "error"
    INVALID_INPUT = "invalid_input"


@dataclass(frozen=True)
class NoveltyLeadResolutionResult:
    """A retrieval-layer result for translating a web lead into N-1 evidence.

    This deliberately is not a persisted novelty-web schema.  The admission service owns the
    receipt/lead artifact and translates this small, deterministic result into it.  ``hit`` is
    present only when Crossref returned an identity-safe canonical record.
    """

    provider_id: str
    method: NoveltyLeadResolutionMethod
    status: NoveltyLeadResolutionStatus
    response_digest: str | None = None
    hit: NoveltySearchHit | None = None
    error_class: str = ""


class CrossrefNoveltyLeadResolver:
    """One-shot Crossref reconciliation for an untrusted web-discovered prior lead.

    A claimed DOI is never treated as a search term: it gets exactly one direct ``/works/{doi}``
    request.  Only a lead with no DOI gets one ``query.title`` request, and the returned title must
    match the supplied title after conservative normalization.  Invalid input and request errors
    return typed outcomes; neither triggers a fallback request, retry, or loop.
    """

    provider_id = "crossref"

    def __init__(
        self,
        *,
        http_get_json: JsonGetter | None = None,
        email: str = "",
    ) -> None:
        self.http_get_json = http_get_json or _http_get_json
        self.email = email or os.getenv("CROSSREF_EMAIL", "")

    def resolve(
        self,
        *,
        query_id: str,
        claimed_doi: str = "",
        claimed_title: str = "",
    ) -> NoveltyLeadResolutionResult:
        """Resolve one lead with one Crossref request at most.

        The caller supplies a host-owned query id.  A non-empty but invalid DOI is an invalid
        DOI-path result, rather than an excuse to fall back to title matching.  That makes the
        path and request count auditable and prevents a malformed URL-like DOI from changing the
        authority claim of the lead.
        """

        if not isinstance(claimed_doi, str):
            return self._invalid(NoveltyLeadResolutionMethod.NONE, "invalid_claimed_doi")
        if not isinstance(claimed_title, str):
            return self._invalid(NoveltyLeadResolutionMethod.NONE, "invalid_claimed_title")
        method = (
            NoveltyLeadResolutionMethod.DOI_SINGLE_ENTITY
            if claimed_doi.strip()
            else NoveltyLeadResolutionMethod.TITLE_RECONCILIATION
        )
        if not _safe_resolution_query_id(query_id):
            return self._invalid(method, "invalid_query_id")

        if claimed_doi.strip():
            doi = _validated_claimed_doi(claimed_doi)
            if not doi:
                return self._invalid(method, "invalid_claimed_doi")
            return self._resolve_doi(query_id=query_id, doi=doi)

        title = _validated_claimed_title(claimed_title)
        if not title:
            return self._invalid(method, "invalid_claimed_title")
        return self._resolve_title(query_id=query_id, title=title)

    def _resolve_doi(self, *, query_id: str, doi: str) -> NoveltyLeadResolutionResult:
        method = NoveltyLeadResolutionMethod.DOI_SINGLE_ENTITY
        url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
        raw, response_digest, error_class = self._request(url)
        if raw is None or response_digest is None:
            return self._error(method, error_class)
        item = _crossref_message(raw)
        if item is None:
            return self._unresolved(method, response_digest)
        hit = _crossref_resolution_hit(
            item,
            query_id=query_id,
            response_digest=response_digest,
        )
        if hit is None or hit.doi != doi:
            return self._unresolved(method, response_digest)
        return NoveltyLeadResolutionResult(
            provider_id=self.provider_id,
            method=method,
            status=NoveltyLeadResolutionStatus.RESOLVED,
            response_digest=response_digest,
            hit=hit,
        )

    def _resolve_title(self, *, query_id: str, title: str) -> NoveltyLeadResolutionResult:
        method = NoveltyLeadResolutionMethod.TITLE_RECONCILIATION
        # The lead carries a search-result PAGE title; the index holds a bibliographic one. Query
        # and compare on the undecorated form -- the equality guard below is unchanged.
        title = _strip_page_chrome(title)
        params = {
            "query.title": title,
            "rows": "1",
            "select": "DOI,title,abstract,published,issued,URL",
        }
        if self.email:
            params["mailto"] = self.email
        url = f"https://api.crossref.org/works?{urllib.parse.urlencode(params)}"
        raw, response_digest, error_class = self._request(url)
        if raw is None or response_digest is None:
            return self._error(method, error_class)
        item = _crossref_first_item(raw)
        if item is None:
            return self._unresolved(method, response_digest)
        hit = _crossref_resolution_hit(
            item,
            query_id=query_id,
            response_digest=response_digest,
        )
        if hit is None or not _titles_match(title, hit.title):
            return self._unresolved(method, response_digest)
        return NoveltyLeadResolutionResult(
            provider_id=self.provider_id,
            method=method,
            status=NoveltyLeadResolutionStatus.RESOLVED,
            response_digest=response_digest,
            hit=hit,
        )

    def _request(self, url: str) -> tuple[dict[str, Any] | None, str | None, str]:
        try:
            raw = self.http_get_json(
                url,
                {"User-Agent": "maieusis/novelty-web-lead-resolution-v1"},
            )
            if not isinstance(raw, dict):
                raise ValueError("scholarly-index response must be a JSON object")
            return raw, stable_hash(raw), ""
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            # The caller persists only the class, never a possibly secret-bearing provider message.
            return None, None, type(exc).__name__

    def _invalid(
        self,
        method: NoveltyLeadResolutionMethod,
        error_class: str,
    ) -> NoveltyLeadResolutionResult:
        return NoveltyLeadResolutionResult(
            provider_id=self.provider_id,
            method=method,
            status=NoveltyLeadResolutionStatus.INVALID_INPUT,
            error_class=error_class,
        )

    def _unresolved(
        self,
        method: NoveltyLeadResolutionMethod,
        response_digest: str,
    ) -> NoveltyLeadResolutionResult:
        return NoveltyLeadResolutionResult(
            provider_id=self.provider_id,
            method=method,
            status=NoveltyLeadResolutionStatus.UNRESOLVED,
            response_digest=response_digest,
        )

    def _error(
        self,
        method: NoveltyLeadResolutionMethod,
        error_class: str,
    ) -> NoveltyLeadResolutionResult:
        return NoveltyLeadResolutionResult(
            provider_id=self.provider_id,
            method=method,
            status=NoveltyLeadResolutionStatus.ERROR,
            error_class=error_class,
        )


class NoveltySearchProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    def search(self, *, query_id: str, query: str) -> tuple[list[NoveltySearchHit], str]: ...


class OpenAlexNoveltySearchProvider:
    provider_id = "openalex"

    def __init__(
        self,
        *,
        http_get_json: JsonGetter | None = None,
        max_results: int = 8,
        email: str = "",
        api_key: str = "",
        request_coordinator: OpenAlexRequestCoordinator | None = None,
    ) -> None:
        self.http_get_json = http_get_json or _openalex_http_get_json
        self.max_results = max_results
        self.email = email or os.getenv("OPENALEX_EMAIL", "")
        self.api_key = api_key or os.getenv("OPENALEX_API_KEY", "")
        # CARD3-SAFETY: every OpenAlex call goes through the shared cached/limited/breaker-guarded
        # coordinator (the machinery built after the 2026-07-12 quota exhaustion). The product
        # factory supplies ONE coordinator per run so the quota breaker spans every family; a
        # default instance still enforces the limiter/breaker for direct construction.
        self.request_coordinator = request_coordinator or OpenAlexRequestCoordinator()

    def search(self, *, query_id: str, query: str) -> tuple[list[NoveltySearchHit], str]:
        params = {
            "search": query,
            "per-page": str(self.max_results),
            "select": (
                "id,display_name,publication_year,doi,primary_location,abstract_inverted_index,ids"
            ),
        }
        if self.email:
            params["mailto"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        raw = self.request_coordinator.get(
            f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}",
            {"User-Agent": "maieusis/novelty-admission-v2"},
            self.http_get_json,
        )
        response_digest = stable_hash(raw)
        query_tokens = _tokens(query)
        hits: list[NoveltySearchHit] = []
        for item in raw.get("results") or []:
            title = str(item.get("display_name") or item.get("title") or "").strip()
            if not title:
                continue
            abstract = _openalex_abstract(item.get("abstract_inverted_index"))
            ids = item.get("ids") or {}
            openalex_id = str(item.get("id") or ids.get("openalex") or "")
            doi = _normalize_doi(str(item.get("doi") or ids.get("doi") or ""))
            location = item.get("primary_location") or {}
            url = openalex_id or str(location.get("landing_page_url") or "")
            hits.append(
                NoveltySearchHit(
                    provider_id=self.provider_id,
                    source_record_id=openalex_id or f"openalex:{stable_hash(item)[:16]}",
                    title=title,
                    abstract=abstract[:4000],
                    doi=doi,
                    url=url,
                    year=_optional_int(item.get("publication_year")),
                    query_id=query_id,
                    response_digest=response_digest,
                    retrieval_score=_overlap(query_tokens, _tokens(f"{title} {abstract}")),
                )
            )
        return hits, response_digest


class CrossrefNoveltySearchProvider:
    provider_id = "crossref"

    def __init__(
        self,
        *,
        http_get_json: JsonGetter | None = None,
        max_results: int = 8,
        email: str = "",
    ) -> None:
        self.http_get_json = http_get_json or _http_get_json
        self.max_results = max_results
        self.email = email or os.getenv("CROSSREF_EMAIL", "")

    def search(self, *, query_id: str, query: str) -> tuple[list[NoveltySearchHit], str]:
        params = {
            "query": query,
            "rows": str(self.max_results),
            "select": "DOI,title,abstract,published,issued,URL,author",
        }
        if self.email:
            params["mailto"] = self.email
        raw = self.http_get_json(
            f"https://api.crossref.org/works?{urllib.parse.urlencode(params)}",
            {"User-Agent": "maieusis/novelty-admission-v2"},
        )
        response_digest = stable_hash(raw)
        query_tokens = _tokens(query)
        items = ((raw.get("message") or {}).get("items") or []) if isinstance(raw, dict) else []
        hits: list[NoveltySearchHit] = []
        for item in items:
            raw_titles = item.get("title") or []
            title = str(raw_titles[0] if raw_titles else "").strip()
            if not title:
                continue
            abstract = _strip_markup(str(item.get("abstract") or ""))[:4000]
            doi = _normalize_doi(str(item.get("DOI") or ""))
            source_id = f"https://doi.org/{doi}" if doi else f"crossref:{stable_hash(item)[:16]}"
            hits.append(
                NoveltySearchHit(
                    provider_id=self.provider_id,
                    source_record_id=source_id,
                    title=title,
                    abstract=abstract,
                    doi=doi,
                    url=str(item.get("URL") or source_id),
                    year=_crossref_year(item),
                    query_id=query_id,
                    response_digest=response_digest,
                    retrieval_score=_overlap(query_tokens, _tokens(f"{title} {abstract}")),
                )
            )
        return hits, response_digest


def sanitize_novelty_query(value: str, *, max_chars: int = 300) -> str:
    value = re.sub(r"[?*]", " ", value)
    value = re.sub(r"[/\\()[\]{}:;,_|+=<>\"'`~^]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= max_chars:
        return value
    return value[:max_chars].rsplit(" ", 1)[0].strip()


_CLAIMED_DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:a-z0-9]+$", re.IGNORECASE)


def _safe_resolution_query_id(value: str) -> bool:
    """Reject a malformed host-owned provenance key before it reaches an artifact."""

    return bool(
        isinstance(value, str)
        and value
        and len(value) <= 200
        and value.strip() == value
        and all(character.isprintable() and not character.isspace() for character in value)
    )


def _validated_claimed_doi(value: str) -> str:
    """Return a canonical DOI only when a web lead supplied a safe DOI-shaped identifier."""

    if (
        not isinstance(value, str)
        or len(value) > 300
        or any(not character.isprintable() for character in value)
    ):
        return ""
    normalized = value.strip()
    normalized = re.sub(r"^doi:\s*", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(
        r"^https?://(?:dx\.)?doi\.org/",
        "",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = normalized.strip().lower()
    if not _CLAIMED_DOI_RE.fullmatch(normalized):
        return ""
    return normalized


def _validated_claimed_title(value: str) -> str:
    """Keep a bounded, printable title for a single Crossref query-title request."""

    if (
        not isinstance(value, str)
        or len(value) > 500
        or any(not character.isprintable() for character in value)
    ):
        return ""
    title = re.sub(r"\s+", " ", value).strip()
    if not title or not any(character.isalnum() for character in title):
        return ""
    return title


def _crossref_message(raw: dict[str, Any]) -> dict[str, Any] | None:
    message = raw.get("message")
    return message if isinstance(message, dict) else None


def _crossref_first_item(raw: dict[str, Any]) -> dict[str, Any] | None:
    message = _crossref_message(raw)
    if message is None:
        return None
    items = message.get("items")
    if not isinstance(items, list) or not items:
        return None
    first = items[0]
    return first if isinstance(first, dict) else None


def _crossref_resolution_hit(
    item: dict[str, Any],
    *,
    query_id: str,
    response_digest: str,
) -> NoveltySearchHit | None:
    raw_titles = item.get("title")
    if not isinstance(raw_titles, list) or not raw_titles or not isinstance(raw_titles[0], str):
        return None
    title = raw_titles[0].strip()
    if not _validated_claimed_title(title):
        return None
    doi = _validated_claimed_doi(str(item.get("DOI") or ""))
    source_record_id = f"https://doi.org/{doi}" if doi else f"crossref:{stable_hash(item)[:16]}"
    abstract = _strip_markup(str(item.get("abstract") or ""))[:4000]
    return NoveltySearchHit(
        provider_id="crossref",
        source_record_id=source_record_id,
        title=title,
        abstract=abstract,
        doi=doi,
        # A DOI resolver gives us a durable canonical locator.  Do not retain Crossref's arbitrary
        # publisher URL as a substitute for a web page or full-text authority.
        url=f"https://doi.org/{doi}" if doi else "",
        year=_crossref_year(item),
        query_id=query_id,
        response_digest=response_digest,
        retrieval_score=1.0,
    )


#: Publisher and platform decoration a SEARCH-RESULT page title carries and a bibliographic title
#: never does. Each pattern below was taken from the 54 leads the 2026-07-31 climate leg discarded --
#: every one a real, on-topic paper, including "The Downward Influence of Stratospheric Sudden
#: Warmings", which scored a perfect token overlap in the packs that did survive.
_PAGE_CHROME_PREFIX = re.compile(
    r"^(?:WCD|ACP|AMT|ESD|GMD|TC|HESS|BG|NPG|OS|SE|EGUsphere|ESSD|CP)\s+-\s+",
    re.IGNORECASE,
)
_PAGE_CHROME_SUFFIX = re.compile(
    r"(?:"
    r"\s+\|\s+.*"  # publisher navigation: "... | Journal of Climate | AMS"
    r"|\s+in:\s+.*"  # "... in: Journal of the Atmospheric Sciences Volume 7..."
    r"|\s+-\s+(?:PMC|ADS|ScienceDirect|ORA|CentAUR|PubMed|arXiv|Semantic\s+Scholar)\b.*"
    r")$",
    re.IGNORECASE,
)
#: Below this, a stripped fragment is too generic to be a safe identity claim, so the lead is left
#: unresolved rather than risking a same-titled different work.
_MIN_STRIPPED_TITLE_CHARS = 20


def _strip_page_chrome(title: str) -> str:
    """A search-result page title reduced to the bibliographic title it decorates.

    The exact-match guard below is CORRECT and stays exact -- the defect was feeding it a page title
    and expecting equality. Chrome makes equality structurally impossible, so a correct guard became
    a blanket veto: 54 of 75 web leads (72%) were discarded on decoration, and the web lane is the
    one that works -- 90% of its priors carry a domain term against 26% of the deterministic lane.

    Monotone-safe by construction: stripping happens BEFORE an unchanged equality test, so
    over-stripping degrades to `unresolved` -- exactly today's behaviour -- and can never produce a
    false bind.
    """
    stripped = _PAGE_CHROME_SUFFIX.sub("", _PAGE_CHROME_PREFIX.sub("", title)).strip()
    if len(stripped) < _MIN_STRIPPED_TITLE_CHARS:
        return title
    return stripped


def _titles_match(claimed_title: str, canonical_title: str) -> bool:
    """Require an exact normalized title, never a semantic/ranking-based reconciliation."""

    return _title_match_key(claimed_title) == _title_match_key(canonical_title)


def _title_match_key(value: str) -> str:
    return " ".join(re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE))


def _http_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}") from exc
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("scholarly-index response must be a JSON object")
    return parsed


def _openalex_http_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    """OpenAlex getter with typed status codes so the coordinator's quota breaker can classify."""
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise ExternalLookupError(f"HTTP {exc.code}", status_code=exc.code) from exc
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("scholarly-index response must be a JSON object")
    return parsed


def _normalize_doi(value: str) -> str:
    return value.strip().lower().removeprefix("https://doi.org/").removeprefix("doi:")


def _openalex_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    positioned = [
        (int(position), word) for word, positions in index.items() for position in positions
    ]
    return " ".join(word for _, word in sorted(positioned))


def _strip_markup(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def _optional_int(value: object) -> int | None:
    if not isinstance(value, (str, int, float, bytes, bytearray)):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _crossref_year(item: dict[str, Any]) -> int | None:
    for key in ("published", "issued"):
        date_parts = (item.get(key) or {}).get("date-parts") or []
        if date_parts and date_parts[0]:
            return _optional_int(date_parts[0][0])
    return None


def _tokens(value: str) -> set[str]:
    stop = {"the", "and", "for", "with", "from", "that", "this", "does", "using"}
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.lower())
        if len(token) > 2 and token not in stop
    }


def _overlap(left: set[str], right: set[str]) -> float:
    if not left:
        return 0.0
    return round(len(left & right) / len(left), 4)
