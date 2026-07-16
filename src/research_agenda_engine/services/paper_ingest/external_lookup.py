from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ...provenance import stable_hash
from ...providers.capture import capture_paid_leaf
from ...schemas.cited_literature import RawReferenceEntry
from ...schemas.paper_ingest import (
    ExternalPaperIdentifiers,
    ExternalPaperMetadata,
    ExternalPaperRecord,
    LicenseClass,
    OpenAccessAssertion,
    PaperIdentityQuery,
    ProcessedTextAvailability,
    ProcessedTextFact,
    SpanKind,
)

JsonGetter = Callable[[str, dict[str, str]], dict[str, Any]]


class ExternalLookupError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class OpenAlexQuotaExhausted(ExternalLookupError):
    """The stage-scoped OpenAlex breaker is open after repeated exhausted 429s."""

    diagnostic = "provider_quota_exhausted"

    def __init__(self, *, report_diagnostic: bool = False) -> None:
        super().__init__(self.diagnostic, status_code=429)
        self.report_diagnostic = report_diagnostic


@dataclass(frozen=True)
class OpenAlexRequestStats:
    network_requests: int
    cache_hits: int
    negative_cache_hits: int
    quota_429s: int
    breaker_open: bool


class OpenAlexRequestCoordinator:
    """Stage-scoped cache, polite limiter, and quota breaker shared by OpenAlex providers."""

    def __init__(
        self,
        *,
        cache_dir: Path | None = None,
        min_interval_seconds: float = 0.0,
        negative_ttl_seconds: float = 24 * 60 * 60,
        quota_failure_threshold: int = 3,
        sleep: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        wall_time: Callable[[], float] = time.time,
    ) -> None:
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be non-negative")
        if negative_ttl_seconds <= 0:
            raise ValueError("negative_ttl_seconds must be positive")
        if quota_failure_threshold < 1:
            raise ValueError("quota_failure_threshold must be positive")
        self.cache_dir = cache_dir
        self.min_interval_seconds = min_interval_seconds
        self.negative_ttl_seconds = negative_ttl_seconds
        self.quota_failure_threshold = quota_failure_threshold
        self._sleep = sleep
        self._monotonic = monotonic
        self._wall_time = wall_time
        self._lock = threading.Lock()
        self._next_request_at = 0.0
        self._consecutive_quota_429s = 0
        self._breaker_open = False
        self._diagnostics: list[str] = []
        self._pending_diagnostics: list[str] = []
        self._network_requests = 0
        self._cache_hits = 0
        self._negative_cache_hits = 0
        self._quota_429s = 0

    @property
    def diagnostics(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._diagnostics)

    @property
    def stats(self) -> OpenAlexRequestStats:
        with self._lock:
            return OpenAlexRequestStats(
                network_requests=self._network_requests,
                cache_hits=self._cache_hits,
                negative_cache_hits=self._negative_cache_hits,
                quota_429s=self._quota_429s,
                breaker_open=self._breaker_open,
            )

    def take_diagnostics(self) -> tuple[str, ...]:
        """Consume diagnostics that have not yet been persisted at the stage boundary."""
        with self._lock:
            pending = tuple(self._pending_diagnostics)
            self._pending_diagnostics.clear()
            return pending

    def get(self, url: str, headers: dict[str, str], getter: JsonGetter) -> dict[str, Any]:
        cache_key = _openalex_cache_key(url)
        cached = self._read_cache(cache_key)
        if cached is not None:
            status, payload = cached
            with self._lock:
                if status == "not_found":
                    self._negative_cache_hits += 1
                else:
                    self._cache_hits += 1
            if status == "not_found":
                raise ExternalLookupError("OpenAlex record not found (cached)", status_code=404)
            return payload

        with self._lock:
            if self._breaker_open:
                raise OpenAlexQuotaExhausted()
            now = self._monotonic()
            delay = max(0.0, self._next_request_at - now)
            self._next_request_at = max(now, self._next_request_at) + self.min_interval_seconds
        if delay:
            self._sleep(delay)

        try:
            with self._lock:
                self._network_requests += 1
            payload = getter(url, headers)
        except ExternalLookupError as exc:
            if exc.status_code == 404:
                self._write_cache(cache_key, status="not_found", payload={})
            if exc.status_code == 429:
                self._record_quota_429()
            else:
                with self._lock:
                    self._consecutive_quota_429s = 0
            raise
        with self._lock:
            # A transient rate-429 that the HTTP layer retried successfully reaches this path and
            # therefore cannot trip the quota breaker.
            self._consecutive_quota_429s = 0
        self._write_cache(cache_key, status="ok", payload=payload)
        for alias in _openalex_cache_aliases(payload):
            if alias != cache_key:
                self._write_cache(alias, status="ok", payload=payload)
        return payload

    def _record_quota_429(self) -> None:
        report_diagnostic = False
        with self._lock:
            self._quota_429s += 1
            self._consecutive_quota_429s += 1
            if self._consecutive_quota_429s < self.quota_failure_threshold:
                return
            self._breaker_open = True
            if OpenAlexQuotaExhausted.diagnostic not in self._diagnostics:
                self._diagnostics.append(OpenAlexQuotaExhausted.diagnostic)
                self._pending_diagnostics.append(OpenAlexQuotaExhausted.diagnostic)
                report_diagnostic = True
        raise OpenAlexQuotaExhausted(report_diagnostic=report_diagnostic)

    def _read_cache(self, cache_key: str) -> tuple[str, dict[str, Any]] | None:
        path = self._cache_path(cache_key)
        if path is None:
            return None
        with self._lock:
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                return None
        if item.get("status") == "not_found":
            age = self._wall_time() - float(item.get("stored_at", 0.0))
            if age > self.negative_ttl_seconds:
                return None
        payload = item.get("payload")
        if item.get("schema_version") != 1 or not isinstance(payload, dict):
            return None
        status = str(item.get("status") or "")
        return (status, payload) if status in {"ok", "not_found"} else None

    def _write_cache(self, cache_key: str, *, status: str, payload: dict[str, Any]) -> None:
        path = self._cache_path(cache_key)
        if path is None:
            return
        item = {
            "schema_version": 1,
            "status": status,
            "stored_at": self._wall_time(),
            "payload": payload,
        }
        with self._lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(f".tmp-{os.getpid()}-{threading.get_ident()}")
            temporary.write_text(json.dumps(item, sort_keys=True), encoding="utf-8")
            temporary.replace(path)

    def _cache_path(self, cache_key: str) -> Path | None:
        if self.cache_dir is None:
            return None
        return self.cache_dir / f"{stable_hash(cache_key)}.json"


class ProcessedPaperLookupProvider(ABC):
    provider_name: str

    @abstractmethod
    def lookup(self, query: PaperIdentityQuery) -> ExternalPaperRecord:
        raise NotImplementedError


class SourceReferenceProvider(ABC):
    provider_name: str

    @abstractmethod
    def references_for_source(
        self, query: PaperIdentityQuery, *, source_paper_id: str
    ) -> list[RawReferenceEntry]:
        raise NotImplementedError


class NullProcessedPaperLookupProvider(ProcessedPaperLookupProvider):
    provider_name = "none"

    def lookup(self, query: PaperIdentityQuery) -> ExternalPaperRecord:
        return ExternalPaperRecord(
            paper_id=_paper_id_from_query(query),
            identifiers=ExternalPaperIdentifiers(
                doi=query.doi, pmid=query.pmid, pmcid=query.pmcid, arxiv_id=query.arxiv_id
            ),
            metadata=ExternalPaperMetadata(title=query.title),
        )


class CrossrefLookupProvider(ProcessedPaperLookupProvider):
    provider_name = "crossref"

    def __init__(
        self,
        *,
        mailto: str = "",
        http_get_json: JsonGetter | None = None,
        timeout_seconds: float = 20.0,
    ):
        self.mailto = mailto
        self.http_get_json = http_get_json or _timeout_json_getter(timeout_seconds)

    def lookup(self, query: PaperIdentityQuery) -> ExternalPaperRecord:
        if query.doi:
            quoted = urllib.parse.quote(query.doi, safe="")
            url = f"https://api.crossref.org/works/{quoted}"
        elif query.title:
            params = urllib.parse.urlencode({"query.title": query.title, "rows": "1"})
            url = f"https://api.crossref.org/works?{params}"
        else:
            return NullProcessedPaperLookupProvider().lookup(query)
        headers = _polite_headers(self.mailto)
        raw = self.http_get_json(url, headers)
        message = raw.get("message", {})
        if "items" in message:
            items = message.get("items") or []
            message = items[0] if items else {}
        record = ExternalPaperRecord(
            paper_id=_paper_id_from_query(query),
            identifiers=ExternalPaperIdentifiers(
                doi=_first_string(message.get("DOI")) or query.doi
            ),
            metadata=ExternalPaperMetadata(
                title=_first_string(message.get("title")) or query.title,
                authors=_crossref_authors(message),
                venue=_first_string(message.get("container-title")),
                year=_crossref_year(message),
                publisher=str(message.get("publisher") or ""),
                abstract=str(message.get("abstract") or ""),
            ),
            provider_records=[_provider_record(self.provider_name, url, raw)],
            response_hashes={self.provider_name: stable_hash(raw)},
        )
        for item in message.get("license") or []:
            url_value = str(item.get("URL") or "")
            record.open_access.append(
                OpenAccessAssertion(
                    is_open_access=None,
                    license_class=_license_class(url_value),
                    license_url=url_value,
                    source_url=url,
                    source=self.provider_name,
                    note="Crossref license metadata; not a full-text authorization by itself.",
                )
            )
        return record


class OpenAlexLookupProvider(ProcessedPaperLookupProvider):
    provider_name = "openalex"

    def __init__(
        self,
        *,
        email: str = "",
        api_key: str = "",
        http_get_json: JsonGetter | None = None,
        timeout_seconds: float = 20.0,
        request_coordinator: OpenAlexRequestCoordinator | None = None,
    ):
        self.email = email or os.getenv("OPENALEX_EMAIL", "")
        self.api_key = api_key or os.getenv("OPENALEX_API_KEY", "")
        self.http_get_json = http_get_json or _timeout_json_getter(timeout_seconds)
        self.request_coordinator = request_coordinator or OpenAlexRequestCoordinator()

    def lookup(self, query: PaperIdentityQuery) -> ExternalPaperRecord:
        auth_params = {}
        if self.email:
            auth_params["mailto"] = self.email
        if self.api_key:
            auth_params["api_key"] = self.api_key
        if query.doi:
            base_url = (
                "https://api.openalex.org/works/https://doi.org/"
                f"{urllib.parse.quote(query.doi, safe='')}"
            )
            suffix = f"?{urllib.parse.urlencode(auth_params)}" if auth_params else ""
            url = f"{base_url}{suffix}"
        elif query.title:
            params = {"search": query.title, "per-page": "1", **auth_params}
            url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
        else:
            return NullProcessedPaperLookupProvider().lookup(query)
        headers = {"User-Agent": "maieusis/phase2"}
        raw = self.request_coordinator.get(url, headers, self.http_get_json)
        item = (raw.get("results") or [raw])[0] if isinstance(raw, dict) else {}
        ids = item.get("ids") or {}
        primary_location = item.get("primary_location") or {}
        open_access = item.get("open_access") or {}
        license_value = str(open_access.get("license") or primary_location.get("license") or "")
        record = ExternalPaperRecord(
            paper_id=_paper_id_from_query(query),
            identifiers=ExternalPaperIdentifiers(
                doi=_normalize_doi(ids.get("doi")) or query.doi,
                pmid=_extract_pubmed_id(ids.get("pmid")) or query.pmid,
                pmcid=_extract_pmcid(ids.get("pmcid")) or query.pmcid,
                openalex_id=str(item.get("id") or ""),
            ),
            metadata=ExternalPaperMetadata(
                title=str(item.get("title") or query.title),
                authors=[
                    str(authorship.get("author", {}).get("display_name") or "")
                    for authorship in item.get("authorships") or []
                    if authorship.get("author")
                ],
                venue=str(
                    (item.get("primary_location") or {}).get("source", {}).get("display_name") or ""
                ),
                year=item.get("publication_year"),
                abstract=_openalex_abstract(item.get("abstract_inverted_index")),
            ),
            open_access=[
                OpenAccessAssertion(
                    is_open_access=open_access.get("is_oa"),
                    license_class=_license_class(license_value),
                    license_url=license_value,
                    source_url=str(primary_location.get("landing_page_url") or ""),
                    source=self.provider_name,
                    note="OpenAlex OA metadata snapshot; PDF URLs are not persisted as authorization.",
                )
            ],
            processed_text=[
                ProcessedTextFact(
                    availability=ProcessedTextAvailability.ABSTRACT
                    if item.get("abstract_inverted_index")
                    else ProcessedTextAvailability.NONE,
                    source=self.provider_name,
                    source_record_id=str(item.get("id") or ""),
                    span_kind=SpanKind.UNKNOWN,
                    structure_level="abstract",
                    can_persist_full_text=False,
                )
            ],
            provider_records=[_provider_record(self.provider_name, url, raw)],
            response_hashes={self.provider_name: stable_hash(raw)},
        )
        return record


class EuropePmcLookupProvider(ProcessedPaperLookupProvider):
    """P2: Europe PMC abstract lookup (keyless public REST). A strong biomed/PMC abstract source that
    complements OpenAlex (abstract_inverted_index gaps) and Crossref (usually no abstract). Mirrors
    ``OpenAlexLookupProvider``; the abstract-backfill (``reference_resolution``) adopts whichever
    provider actually returned a non-empty abstract, so cascade order is not load-bearing for it."""

    provider_name = "europepmc"

    def __init__(
        self,
        *,
        http_get_json: JsonGetter | None = None,
        timeout_seconds: float = 20.0,
    ):
        self.http_get_json = http_get_json or _timeout_json_getter(timeout_seconds)

    def lookup(self, query: PaperIdentityQuery) -> ExternalPaperRecord:
        if query.doi:
            term = f'DOI:"{query.doi}"'
        elif query.title:
            term = f'TITLE:"{query.title}"'
        else:
            return NullProcessedPaperLookupProvider().lookup(query)
        params = {"query": term, "format": "json", "resultType": "core", "pageSize": "1"}
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode(
            params
        )
        headers = {"User-Agent": "maieusis/phase2"}
        raw = self.http_get_json(url, headers)
        results = (
            ((raw.get("resultList") or {}).get("result") or []) if isinstance(raw, dict) else []
        )
        item = results[0] if results else {}
        abstract = str(item.get("abstractText") or "").strip()
        is_open_access = str(item.get("isOpenAccess") or "").upper() == "Y"
        license_value = str(item.get("license") or "")
        return ExternalPaperRecord(
            paper_id=_paper_id_from_query(query),
            identifiers=ExternalPaperIdentifiers(
                doi=_normalize_doi(item.get("doi")) or query.doi,
                pmid=str(item.get("pmid") or "") or query.pmid,
                pmcid=str(item.get("pmcid") or "") or query.pmcid,
            ),
            metadata=ExternalPaperMetadata(
                title=str(item.get("title") or query.title),
                authors=[
                    name.strip()
                    for name in str(item.get("authorString") or "").split(",")
                    if name.strip()
                ],
                venue=str(item.get("journalTitle") or ""),
                year=int(item["pubYear"]) if str(item.get("pubYear") or "").isdigit() else None,
                abstract=abstract,
            ),
            open_access=[
                OpenAccessAssertion(
                    is_open_access=is_open_access,
                    license_class=_license_class(license_value),
                    license_url=license_value,
                    source_url="",
                    source=self.provider_name,
                    note="Europe PMC metadata snapshot; PDF URLs are not persisted as authorization.",
                )
            ],
            processed_text=[
                ProcessedTextFact(
                    availability=ProcessedTextAvailability.ABSTRACT
                    if abstract
                    else ProcessedTextAvailability.NONE,
                    source=self.provider_name,
                    source_record_id=str(item.get("id") or ""),
                    span_kind=SpanKind.UNKNOWN,
                    structure_level="abstract",
                    can_persist_full_text=False,
                )
            ],
            provider_records=[_provider_record(self.provider_name, url, raw)],
            response_hashes={self.provider_name: stable_hash(raw)},
        )


class CrossrefSourceReferenceProvider(SourceReferenceProvider):
    provider_name = "crossref_source_references"

    def __init__(
        self,
        *,
        mailto: str = "",
        http_get_json: JsonGetter | None = None,
        timeout_seconds: float = 20.0,
    ):
        self.mailto = mailto
        self.http_get_json = http_get_json or _timeout_json_getter(timeout_seconds)

    def references_for_source(
        self, query: PaperIdentityQuery, *, source_paper_id: str
    ) -> list[RawReferenceEntry]:
        url = _crossref_work_url(query)
        if not url:
            return []
        raw = self.http_get_json(url, _polite_headers(self.mailto))
        message = raw.get("message", {})
        if "items" in message:
            items = message.get("items") or []
            message = items[0] if items else {}
        entries: list[RawReferenceEntry] = []
        for fallback_index, item in enumerate(message.get("reference") or [], start=1):
            raw_text = _crossref_reference_text(item)
            if not raw_text:
                continue
            reference_index = _reference_key_number(item.get("key")) or fallback_index
            doi = _normalize_doi(item.get("DOI"))
            title = _first_string(item.get("article-title"))
            author = str(item.get("author") or "")
            year = _safe_year(item.get("year"))
            raw_reference_id = f"{source_paper_id}.crossref_ref{reference_index:05d}"
            entries.append(
                RawReferenceEntry(
                    raw_reference_id=raw_reference_id,
                    source_paper_id=source_paper_id,
                    reference_index=reference_index,
                    raw_text=raw_text,
                    source_block_id=f"external:{self.provider_name}",
                    source_span_id=f"external:{self.provider_name}:{stable_hash(raw_text)[:12]}",
                    section_title="external_reference_metadata",
                    title_hint=title,
                    author_hint=author,
                    year_hint=year,
                    doi_hint=doi,
                )
            )
        return entries


class OpenAlexSourceReferenceProvider(SourceReferenceProvider):
    provider_name = "openalex_source_references"

    def __init__(
        self,
        *,
        email: str = "",
        api_key: str = "",
        http_get_json: JsonGetter | None = None,
        timeout_seconds: float = 20.0,
        inter_call_delay_seconds: float = 0.0,
        request_coordinator: OpenAlexRequestCoordinator | None = None,
    ):
        self.email = email or os.getenv("OPENALEX_EMAIL", "")
        self.api_key = api_key or os.getenv("OPENALEX_API_KEY", "")
        self.http_get_json = http_get_json or _timeout_json_getter(timeout_seconds)
        # Compatibility constructor leaf: when no shared coordinator is supplied it becomes this
        # provider's minimum interval. The product factory supplies one coordinator across workers.
        self.inter_call_delay_seconds = inter_call_delay_seconds
        self.request_coordinator = request_coordinator or OpenAlexRequestCoordinator(
            min_interval_seconds=inter_call_delay_seconds
        )

    def references_for_source(
        self, query: PaperIdentityQuery, *, source_paper_id: str
    ) -> list[RawReferenceEntry]:
        item = self._source_item(query)
        referenced_works = item.get("referenced_works") or []
        entries: list[RawReferenceEntry] = []
        for index, work_url in enumerate(referenced_works, start=1):
            try:
                cited = self.request_coordinator.get(
                    self._with_auth_params(str(work_url)),
                    _openalex_headers(),
                    self.http_get_json,
                )
            except OpenAlexQuotaExhausted:
                break
            except Exception:
                continue
            raw_text = _openalex_reference_text(cited)
            if not raw_text:
                continue
            ids = cited.get("ids") or {}
            raw_reference_id = f"{source_paper_id}.openalex_ref{index:05d}"
            entries.append(
                RawReferenceEntry(
                    raw_reference_id=raw_reference_id,
                    source_paper_id=source_paper_id,
                    reference_index=index,
                    raw_text=raw_text,
                    source_block_id=f"external:{self.provider_name}",
                    source_span_id=f"external:{self.provider_name}:{stable_hash(raw_text)[:12]}",
                    section_title="external_reference_metadata",
                    title_hint=str(cited.get("title") or ""),
                    author_hint=", ".join(
                        str(authorship.get("author", {}).get("display_name") or "")
                        for authorship in cited.get("authorships") or []
                        if authorship.get("author")
                    ),
                    year_hint=cited.get("publication_year"),
                    doi_hint=_normalize_doi(ids.get("doi")),
                    pmid_hint=_extract_pubmed_id(ids.get("pmid")),
                    pmcid_hint=_extract_pmcid(ids.get("pmcid")),
                )
            )
        return entries

    def _source_item(self, query: PaperIdentityQuery) -> dict[str, Any]:
        auth_params = self._auth_params()
        if query.doi:
            base_url = (
                "https://api.openalex.org/works/https://doi.org/"
                f"{urllib.parse.quote(query.doi, safe='')}"
            )
            suffix = f"?{urllib.parse.urlencode(auth_params)}" if auth_params else ""
            url = f"{base_url}{suffix}"
        elif query.title:
            params = {"search": query.title, "per-page": "1", **auth_params}
            url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
        else:
            return {}
        raw = self.request_coordinator.get(url, _openalex_headers(), self.http_get_json)
        results = raw.get("results")
        if isinstance(results, list) and results and isinstance(results[0], dict):
            return results[0]
        return raw

    def _auth_params(self) -> dict[str, str]:
        auth_params: dict[str, str] = {}
        if self.email:
            auth_params["mailto"] = self.email
        if self.api_key:
            auth_params["api_key"] = self.api_key
        return auth_params

    def _with_auth_params(self, url: str) -> str:
        params = self._auth_params()
        if not params:
            return url
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{urllib.parse.urlencode(params)}"


class PmcBiocLookupProvider(ProcessedPaperLookupProvider):
    provider_name = "pmc_bioc"

    def __init__(self, *, http_get_json: JsonGetter | None = None):
        self.http_get_json = http_get_json or _http_get_json

    def lookup(self, query: PaperIdentityQuery) -> ExternalPaperRecord:
        if not query.pmcid:
            return NullProcessedPaperLookupProvider().lookup(query)
        pmcid = query.pmcid.upper().removeprefix("PMC")
        url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/PMC{pmcid}/unicode"
        raw = self.http_get_json(url, {"User-Agent": "maieusis/phase2"})
        documents = raw.get("documents") or []
        passages = documents[0].get("passages") if documents else []
        title = ""
        abstract_parts: list[str] = []
        for passage in passages or []:
            infons = passage.get("infons") or {}
            section_type = str(infons.get("section_type") or infons.get("type") or "").lower()
            text = str(passage.get("text") or "")
            if section_type == "title" and not title:
                title = text
            elif section_type == "abstract":
                abstract_parts.append(text)
        return ExternalPaperRecord(
            paper_id=_paper_id_from_query(query),
            identifiers=ExternalPaperIdentifiers(
                pmcid=f"PMC{pmcid}", doi=query.doi, pmid=query.pmid
            ),
            metadata=ExternalPaperMetadata(
                title=title or query.title, abstract="\n".join(abstract_parts)
            ),
            processed_text=[
                ProcessedTextFact(
                    availability=ProcessedTextAvailability.PMC_BIOC,
                    source=self.provider_name,
                    source_record_id=f"PMC{pmcid}",
                    span_kind=SpanKind.CHAR_OFFSET,
                    structure_level="passage",
                    references_available=True,
                    citation_contexts_available=False,
                    content_hash=stable_hash(raw),
                    can_persist_full_text=True,
                    note="Persistence still depends on article-level PMC OA license.",
                )
            ],
            provider_records=[_provider_record(self.provider_name, url, raw)],
            response_hashes={self.provider_name: stable_hash(raw)},
        )


def merge_external_records(
    paper_id: str, records: list[ExternalPaperRecord]
) -> ExternalPaperRecord:
    merged = ExternalPaperRecord(paper_id=paper_id)
    for record in records:
        merged.identifiers = ExternalPaperIdentifiers(
            doi=merged.identifiers.doi or record.identifiers.doi,
            pmid=merged.identifiers.pmid or record.identifiers.pmid,
            pmcid=merged.identifiers.pmcid or record.identifiers.pmcid,
            openalex_id=merged.identifiers.openalex_id or record.identifiers.openalex_id,
            semantic_scholar_id=(
                merged.identifiers.semantic_scholar_id or record.identifiers.semantic_scholar_id
            ),
            arxiv_id=merged.identifiers.arxiv_id or record.identifiers.arxiv_id,
        )
        merged.metadata = ExternalPaperMetadata(
            title=merged.metadata.title or record.metadata.title,
            authors=merged.metadata.authors or record.metadata.authors,
            venue=merged.metadata.venue or record.metadata.venue,
            year=merged.metadata.year or record.metadata.year,
            publisher=merged.metadata.publisher or record.metadata.publisher,
            abstract=merged.metadata.abstract or record.metadata.abstract,
        )
        merged.open_access.extend(record.open_access)
        merged.processed_text.extend(record.processed_text)
        merged.provider_records.extend(record.provider_records)
        merged.warnings.extend(record.warnings)
        merged.response_hashes.update(record.response_hashes)
    return merged


def _timeout_json_getter(timeout_seconds: float) -> JsonGetter:
    def get(url: str, headers: dict[str, str]) -> dict[str, Any]:
        return _http_get_json(url, headers, timeout_seconds=timeout_seconds)

    return get


def _http_get_json(
    url: str,
    headers: dict[str, str],
    *,
    timeout_seconds: float = 20.0,
    max_retries: int | None = None,
) -> dict[str, Any]:
    retry_limit = _MAX_HTTP_RETRIES if max_retries is None else max_retries
    request = urllib.request.Request(url, headers=headers)
    attempt = 0
    parsed: Any = None
    while True:
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                payload = response.read().decode("utf-8")
            # Y3: parse INSIDE the try so a non-JSON body (a 200 with an HTML error page, a truncated
            # stream) becomes the SAME uniform ExternalLookupError that callers already catch — instead
            # of a raw json.JSONDecodeError leaking out and reading as a code bug / crashing an outer path.
            parsed = json.loads(payload)
            break
        except urllib.error.HTTPError as exc:
            # Blocker #3: OpenAlex/Crossref rate-limiting (429; 503 = transient overload) under the
            # whole-corpus burst was starving the cited-literature build → no key-citation selection →
            # accepted papers dropped from induction → 0 usable patterns. Retry with backoff honoring the
            # server's Retry-After, then fail HONESTLY as the uniform ExternalLookupError. Not a silent
            # swallow: an exhausted-retry 429 still surfaces (and Y1(a) records it per paper).
            if exc.code in (429, 503) and attempt < retry_limit:
                time.sleep(_retry_after_seconds(exc) or min(2.0**attempt, 30.0))
                attempt += 1
                continue
            raise ExternalLookupError(
                f"External lookup failed for {_safe_endpoint(url)}: HTTP {exc.code}",
                status_code=exc.code,
            ) from exc
        except Exception as exc:
            raise ExternalLookupError(
                f"External lookup failed for {_safe_endpoint(url)}: {exc}"
            ) from exc
    if not isinstance(parsed, dict):
        raise ExternalLookupError(f"Expected JSON object from {_safe_endpoint(url)}")
    capture_paid_leaf(
        "external_lookup.http_get_json",
        request={"url": url, "headers": headers},
        response=parsed,
    )
    return parsed


_MAX_HTTP_RETRIES = 5


def probe_openalex_quota(
    *,
    email: str = "",
    api_key: str = "",
    http_get_json: JsonGetter | None = None,
) -> None:
    """Issue one cheap filter-class request; raise a structured 429 without retrying it."""
    params = {
        "filter": "has_doi:true",
        "per-page": "1",
        "select": "id",
    }
    resolved_email = email or os.getenv("OPENALEX_EMAIL", "")
    resolved_api_key = api_key or os.getenv("OPENALEX_API_KEY", "")
    if resolved_email:
        params["mailto"] = resolved_email
    if resolved_api_key:
        params["api_key"] = resolved_api_key
    url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
    getter = http_get_json or (
        lambda request_url, headers: _http_get_json(request_url, headers, max_retries=0)
    )
    getter(url, _openalex_headers())


def collect_openalex_diagnostics(*provider_groups: Sequence[object]) -> list[str]:
    """Return one copy of every stage-level coordinator diagnostic."""
    diagnostics: list[str] = []
    seen_coordinators: set[int] = set()
    for providers in provider_groups:
        for provider in providers:
            coordinator = getattr(provider, "request_coordinator", None)
            if not isinstance(coordinator, OpenAlexRequestCoordinator):
                continue
            identity = id(coordinator)
            if identity in seen_coordinators:
                continue
            seen_coordinators.add(identity)
            for diagnostic in coordinator.take_diagnostics():
                if diagnostic not in diagnostics:
                    diagnostics.append(diagnostic)
    return diagnostics


def collect_openalex_request_stats(
    *provider_groups: Sequence[object],
) -> OpenAlexRequestStats | None:
    """Aggregate shared-coordinator counters once each for persisted spend diagnostics."""
    coordinators: list[OpenAlexRequestCoordinator] = []
    seen: set[int] = set()
    for providers in provider_groups:
        for provider in providers:
            coordinator = getattr(provider, "request_coordinator", None)
            if isinstance(coordinator, OpenAlexRequestCoordinator) and id(coordinator) not in seen:
                seen.add(id(coordinator))
                coordinators.append(coordinator)
    if not coordinators:
        return None
    snapshots = [coordinator.stats for coordinator in coordinators]
    return OpenAlexRequestStats(
        network_requests=sum(item.network_requests for item in snapshots),
        cache_hits=sum(item.cache_hits for item in snapshots),
        negative_cache_hits=sum(item.negative_cache_hits for item in snapshots),
        quota_429s=sum(item.quota_429s for item in snapshots),
        breaker_open=any(item.breaker_open for item in snapshots),
    )


def _openalex_cache_key(url: str) -> str:
    """Normalize a request without retaining auth parameters or secret-bearing URLs."""
    parsed = urllib.parse.urlparse(url)
    path = urllib.parse.unquote(parsed.path).rstrip("/")
    doi_marker = "/works/https://doi.org/"
    if doi_marker in path:
        return f"doi:{_normalize_doi(path.split(doi_marker, 1)[1]).lower()}"
    if path.startswith("/W") or "/works/W" in path:
        return f"openalex:{path.rsplit('/', 1)[-1].lower()}"
    query = urllib.parse.parse_qs(parsed.query)
    if query.get("search"):
        normalized = re.sub(r"\s+", " ", query["search"][0].strip().lower())
        return f"search:{normalized}"
    safe_query = {
        key: sorted(values)
        for key, values in query.items()
        if key.lower() not in {"api_key", "mailto"}
    }
    return f"request:{path.lower()}:{stable_hash(safe_query)}"


def _openalex_cache_aliases(payload: dict[str, Any]) -> set[str]:
    item: Any = payload
    results = payload.get("results")
    # Search responses are wrappers while direct work responses are bare records. Do not alias a
    # wrapper under a direct-work key: callers intentionally consume those two shapes differently.
    if isinstance(results, list):
        return set()
    if not isinstance(item, dict):
        return set()
    aliases: set[str] = set()
    openalex_id = str(item.get("id") or "")
    if openalex_id:
        aliases.add(f"openalex:{openalex_id.rstrip('/').rsplit('/', 1)[-1].lower()}")
    doi = _normalize_doi((item.get("ids") or {}).get("doi")).lower()
    if doi:
        aliases.add(f"doi:{doi}")
    return aliases


def _safe_endpoint(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    safe_pairs = [
        (key, value)
        for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in {"api_key", "mailto"}
    ]
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(safe_pairs), "")
    )


def _retry_after_seconds(exc: urllib.error.HTTPError) -> float | None:
    """Parse a numeric ``Retry-After`` (seconds) header, capped, so we honor the server's own backoff."""
    raw = exc.headers.get("Retry-After") if exc.headers else None
    if not raw:
        return None
    try:
        return min(float(raw), 60.0)
    except ValueError:
        return None


def _polite_headers(mailto: str) -> dict[str, str]:
    value = "maieusis/phase2"
    if mailto:
        value = f"{value} (mailto:{mailto})"
    return {"User-Agent": value}


def _openalex_headers() -> dict[str, str]:
    return {"User-Agent": "maieusis/phase2"}


def _crossref_work_url(query: PaperIdentityQuery) -> str:
    if query.doi:
        quoted = urllib.parse.quote(query.doi, safe="")
        return f"https://api.crossref.org/works/{quoted}"
    if query.title:
        params = urllib.parse.urlencode({"query.title": query.title, "rows": "1"})
        return f"https://api.crossref.org/works?{params}"
    return ""


def _paper_id_from_query(query: PaperIdentityQuery) -> str:
    if query.source_pdf:
        return query.source_pdf.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    if query.doi:
        return query.doi.replace("/", "-").replace(".", "-")
    return "external-paper"


def _provider_record(provider: str, endpoint: str, raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": provider,
        "endpoint": _safe_endpoint(endpoint),
        "retrieved_at": datetime.now(UTC).isoformat(),
        "response_hash": stable_hash(raw),
    }


def _first_string(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def _crossref_authors(message: dict[str, Any]) -> list[str]:
    authors = []
    for author in message.get("author") or []:
        parts = [str(author.get("given") or ""), str(author.get("family") or "")]
        name = " ".join(part for part in parts if part).strip()
        if name:
            authors.append(name)
    return authors


def _crossref_year(message: dict[str, Any]) -> int | None:
    for key in ["published-print", "published-online", "published", "issued"]:
        date_parts = (message.get(key) or {}).get("date-parts") or []
        if date_parts and date_parts[0]:
            return int(date_parts[0][0])
    return None


def _crossref_reference_text(item: dict[str, Any]) -> str:
    unstructured = str(item.get("unstructured") or "").strip()
    if unstructured:
        return " ".join(unstructured.split())
    parts = [
        str(item.get("author") or ""),
        _first_string(item.get("article-title")),
        _first_string(item.get("journal-title")),
        str(item.get("year") or ""),
        _normalize_doi(item.get("DOI")),
    ]
    return ". ".join(part.strip(" .") for part in parts if part and part.strip(" ."))


def _openalex_reference_text(item: dict[str, Any]) -> str:
    authors = [
        str(authorship.get("author", {}).get("display_name") or "")
        for authorship in item.get("authorships") or []
        if authorship.get("author")
    ]
    venue = str((item.get("primary_location") or {}).get("source", {}).get("display_name") or "")
    ids = item.get("ids") or {}
    parts = [
        ", ".join(author for author in authors if author),
        str(item.get("title") or ""),
        venue,
        str(item.get("publication_year") or ""),
        _normalize_doi(ids.get("doi")),
    ]
    return ". ".join(part.strip(" .") for part in parts if part and part.strip(" ."))


def _reference_key_number(value: Any) -> int | None:
    match = re.search(r"\d+", str(value or ""))
    return int(match.group(0)) if match else None


def _safe_year(value: Any) -> int | None:
    try:
        year = int(str(value))
    except (TypeError, ValueError):
        return None
    return year if 1800 <= year <= 2200 else None


def _license_class(value: str) -> LicenseClass:
    normalized = value.lower()
    if not normalized:
        return LicenseClass.UNKNOWN
    if "creativecommons.org/licenses/by/" in normalized or "cc-by" in normalized:
        return LicenseClass.PERMISSIVE
    if "noncommercial" in normalized or "by-nc" in normalized:
        return LicenseClass.NON_COMMERCIAL
    if "restricted" in normalized or "elsevier" in normalized:
        return LicenseClass.RESTRICTED
    return LicenseClass.UNCLEAR


def _normalize_doi(value: Any) -> str:
    text = str(value or "")
    return text.removeprefix("https://doi.org/").removeprefix("http://doi.org/")


def _extract_pubmed_id(value: Any) -> str:
    text = str(value or "")
    return text.rsplit("/", 1)[-1] if text else ""


def _extract_pmcid(value: Any) -> str:
    text = str(value or "")
    return text.rsplit("/", 1)[-1].upper() if text else ""


def _openalex_abstract(index: dict[str, list[int]] | None) -> str:
    if not index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, offsets in index.items():
        positions.extend((int(offset), word) for offset in offsets)
    return " ".join(word for _, word in sorted(positions))
