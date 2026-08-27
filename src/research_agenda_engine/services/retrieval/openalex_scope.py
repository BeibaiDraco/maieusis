"""The user's own research field, as OpenAlex identifies it, and what it does to a lane's pool.

Topic retrieval sends each of the user's terms to OpenAlex as an exact title-and-abstract phrase.
That phrase has no field, so `dynamical systems models` returned engineering, decision science and
developmental psychology, and on 2026-08-12 the topic-evidence reviewer ended a run over three
developmental-psychology papers it had been asked to read as neuroscience. Naming the field the
literature lives in removes that class of contamination structurally: `primary_topic.field.id` is
OpenAlex's own classification of a work, not a word match, so filtering on it is not a lexical
relevance gate (AGENTS.md hard rule 11).

Two things live here, and they share one filter builder on purpose. `resolve_openalex_field_id`
turns the user's words into the identity the works endpoint wants, and `probe_topic_term_pools`
asks, before a run is paid for, how many works each term actually has once that filter is on. The
probe measures the request the harvester will issue, so a shared builder is what makes the answer
about the run rather than about a request that resembles it.

The field taxonomy is fetched live rather than written down here. A table of the twenty-six field
names would be a table of domains inside a repository whose fifth hard rule is that new code
survives a dataset swap, and it would silently rot the day OpenAlex revises its taxonomy. Asking
the provider for its own list costs one free metadata request and cannot drift.

Matching is exact on the display name, case- and whitespace-insensitive, and nothing else. There is
no fuzzy fallback on purpose: a wrong field filter empties a lane, and an empty lane is worse than
the over-retrieval this exists to reduce. Every failure — no name, a name that is not one of the
twenty-six, an unreachable endpoint, a malformed reply — returns the empty string, and the caller
then builds exactly the request it built before this module existed.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

import time
import urllib.parse
from collections.abc import Callable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from .literature_prior_search import _http_get_json

#: All twenty-six fields fit in one page; ``per-page`` is stated so the default page size can never
#: silently truncate the taxonomy and turn a valid field name into an unresolvable one.
OPENALEX_FIELDS_URL = "https://api.openalex.org/fields?per-page=50"
OPENALEX_WORKS_URL = "https://api.openalex.org/works"

#: OpenAlex's own topical classification of a work. Structural provider metadata, not word matching.
OPENALEX_FIELD_FILTER_KEY = "primary_topic.field.id"

#: Seconds between consecutive probe requests. OpenAlex answers a rapid repeat of the same shape
#: with a zero count rather than an error, which would read here as a term with no literature and
#: refuse a run that is perfectly fine. Measured pacing, not a guess at a published limit.
_PROBE_MIN_INTERVAL_SECONDS = 1.0

JsonGetter = Callable[[str, dict[str, str]], dict[str, object]]
Sleeper = Callable[[float], None]

#: Everything a failed lookup or count can raise out of the default getter. ``urllib.error.URLError``
#: is an ``OSError``; ``json.JSONDecodeError`` is a ``ValueError``; and ``_http_get_json`` re-raises
#: a non-2xx response as ``RuntimeError``, which is the case that matters most here — a 429 from a
#: shared quota must degrade this to "not measured", never take down a preflight or a run.
_LOOKUP_FAILURES = (OSError, ValueError, RuntimeError)


class TopicTermPool(BaseModel):
    """How many works one term has, under the request this run will issue and without its filter.

    Both counts, because one of them alone cannot answer the question the check is asked. A term
    below quota is either a term the field starved or a term with thin literature anywhere, and only
    the second number tells them apart -- measured 2026-08-12, `weather regime transitions` has 30
    works unfiltered and 6 under `Earth and Planetary Sciences` (the field took them), while `neural
    co-variability` has 3 either way (nothing took them; there are three).
    """

    model_config = ConfigDict(extra="forbid")

    term: str
    #: Works matching the exact phrase under the applied filter. ``-1`` when the count could not be
    #: measured at all, which is a statement about the probe and never about the term.
    pool: int = -1
    measured: bool = False
    #: The same count with no field condition. Equal to ``pool`` when no field was applied, in which
    #: case it is the same single request rather than a second one.
    unfiltered_pool: int = -1
    unfiltered_measured: bool = False


class TopicTermPoolReport(BaseModel):
    """What the free pool probe found: the field it applied, and the pool behind each term."""

    model_config = ConfigDict(extra="forbid")

    #: The field the user named, in the user's own words.
    research_field: str = ""
    #: OpenAlex's identity for it, or empty when the name did not resolve or could not be looked up.
    #: Empty means the counts below are unfiltered, which is exactly what the run would then issue.
    openalex_field_id: str = ""
    pools: list[TopicTermPool] = Field(default_factory=list)

    def field_starved(self, required: int) -> list[TopicTermPool]:
        """Terms the FIELD dropped below quota: enough literature exists, this field cannot see it.

        The only condition that justifies refusing a run, because it is the only one the user can
        act on -- a different field name recovers the literature. Both counts must be measured;
        attributing a shortfall to the field on an unmeasured comparison would be a guess.
        """

        return [
            pool
            for pool in self.pools
            if pool.measured
            and pool.pool < required
            and pool.unfiltered_measured
            and pool.unfiltered_pool >= required
        ]

    def thin(self, required: int) -> list[TopicTermPool]:
        """Terms below quota that the field did not cause. Worth saying; never worth refusing over."""

        starved = {pool.term for pool in self.field_starved(required)}
        return [
            pool
            for pool in self.pools
            if pool.measured and pool.pool < required and pool.term not in starved
        ]

    def unmeasured(self) -> list[TopicTermPool]:
        return [pool for pool in self.pools if not pool.measured]


def normalize_field_text(value: str) -> str:
    """Collapse whitespace and case so a user's field name can be compared with a display name."""

    return " ".join(value.split()).casefold()


def openalex_auth_suffix(*, openalex_email: str = "", openalex_api_key: str = "") -> str:
    """Credential query-string suffix, or empty. NEVER include this in a persisted URL."""

    auth = {
        key: value
        for key, value in (("mailto", openalex_email), ("api_key", openalex_api_key))
        if value
    }
    return f"&{urllib.parse.urlencode(auth)}" if auth else ""


def openalex_works_filter(query_text: str, filters: Mapping[str, str]) -> str:
    """The single ``filter`` parameter value: the exact phrase, plus whatever else was asked for.

    OpenAlex ANDs comma-separated conditions inside one ``filter``, so a structural condition rides
    the SAME request: no extra call and no extra cost. An empty ``filters`` reproduces the
    single-condition request byte for byte, which is what makes an unnamed field a true no-op.
    """

    parts = [f'title_and_abstract.search:"{query_text}"']
    parts.extend(f"{key}:{value}" for key, value in sorted(filters.items()) if key and value)
    return ",".join(parts)


def resolve_openalex_field_id(
    research_field: str,
    *,
    http_get_json: JsonGetter,
    openalex_email: str = "",
    openalex_api_key: str = "",
) -> str:
    """Return ``fields/<n>`` for an exactly-named OpenAlex field, or ``""`` to retrieve unfiltered."""

    wanted = normalize_field_text(research_field)
    if not wanted:
        return ""
    try:
        payload = http_get_json(
            OPENALEX_FIELDS_URL
            + openalex_auth_suffix(
                openalex_email=openalex_email, openalex_api_key=openalex_api_key
            ),
            {},
        )
    except _LOOKUP_FAILURES:
        # The field filter is an improvement to a request that already works without it, so a
        # taxonomy lookup that did not come back must never be able to stop a run.
        return ""
    if not isinstance(payload, dict):
        return ""
    results = payload.get("results")
    if not isinstance(results, list):
        return ""
    for item in results:
        if not isinstance(item, dict):
            continue
        if normalize_field_text(str(item.get("display_name") or "")) != wanted:
            continue
        return _field_identity(str(item.get("id") or ""))
    return ""


def probe_topic_term_pools(
    terms: Sequence[str],
    *,
    research_field: str = "",
    http_get_json: JsonGetter | None = None,
    openalex_email: str = "",
    openalex_api_key: str = "",
    sleep: Sleeper = time.sleep,
    min_interval_seconds: float = _PROBE_MIN_INTERVAL_SECONDS,
) -> TopicTermPoolReport:
    """Count the works each term has, with the run's filter and without it. Free, and never raises.

    A term whose pool cannot fill the lane's quota is reported ``measured`` with its real count; a
    term the probe could not reach at all is reported unmeasured, and the caller must treat those
    two as different things. Conflating them would turn an unreachable OpenAlex into a refusal to
    start, which is the one failure mode this check is forbidden to have.

    The unfiltered count is a second request only when a field actually resolved. With no field the
    two counts are the same measurement, so asking twice would double the traffic to learn nothing.
    """

    getter = http_get_json or _http_get_json
    field_id = (
        resolve_openalex_field_id(
            research_field,
            http_get_json=getter,
            openalex_email=openalex_email,
            openalex_api_key=openalex_api_key,
        )
        if research_field.strip()
        else ""
    )
    issued = 0

    def paced_count(term: str, field: str) -> int | None:
        # Pacing sits on the REQUEST, not on the term: with a field resolved each term issues two,
        # and OpenAlex answers an unpaced repeat with a zero rather than an error -- which would
        # read here as a term with no literature and refuse a run that is perfectly fine.
        nonlocal issued
        if issued:
            sleep(min_interval_seconds)
        issued += 1
        return _count_one(
            term,
            http_get_json=getter,
            openalex_field_id=field,
            openalex_email=openalex_email,
            openalex_api_key=openalex_api_key,
        )

    pools: list[TopicTermPool] = []
    for term in terms:
        filtered = paced_count(term, field_id)
        unfiltered = paced_count(term, "") if field_id else filtered
        pools.append(
            TopicTermPool(
                term=term,
                pool=filtered if filtered is not None else -1,
                measured=filtered is not None,
                unfiltered_pool=unfiltered if unfiltered is not None else -1,
                unfiltered_measured=unfiltered is not None,
            )
        )
    return TopicTermPoolReport(
        research_field=" ".join(research_field.split()),
        openalex_field_id=field_id,
        pools=pools,
    )


def _count_one(
    term: str,
    *,
    http_get_json: JsonGetter,
    openalex_field_id: str,
    openalex_email: str,
    openalex_api_key: str,
) -> int | None:
    """Works matching this exact phrase under this filter, or ``None`` when it could not be asked."""
    filters = {OPENALEX_FIELD_FILTER_KEY: openalex_field_id} if openalex_field_id.strip() else {}
    params = urllib.parse.urlencode(
        {"filter": openalex_works_filter(term, filters), "per-page": "1"}
    )
    url = f"{OPENALEX_WORKS_URL}?{params}" + openalex_auth_suffix(
        openalex_email=openalex_email, openalex_api_key=openalex_api_key
    )
    try:
        payload = http_get_json(url, {})
    except _LOOKUP_FAILURES:
        return None
    if not isinstance(payload, dict):
        return None
    meta = payload.get("meta")
    if not isinstance(meta, dict):
        return None
    count = meta.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return None
    return count


def _field_identity(entity_url: str) -> str:
    """``https://openalex.org/fields/28`` → ``fields/28``; anything else → ``""``."""

    marker = "/fields/"
    if marker not in entity_url:
        return ""
    suffix = entity_url.rsplit(marker, 1)[1].strip("/")
    if not suffix or not suffix.isdigit():
        return ""
    return f"fields/{suffix}"
