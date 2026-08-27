"""Rights-aware, quote-bounded external full-text enrichment.

Only a source-bound provider/repository assertion can authorize a fetch.  The
observed final URL, HTTP status, media type, body digest, and excerpt digest are
retained in a typed attempt receipt.  A generic bibliographic landing URL is never
an OA assertion.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html import unescape
from typing import Any, Protocol
from urllib.parse import urljoin, urlparse

from ...provenance import stable_hash
from ...schemas.external_evidence import (
    DeterministicRetrievalFixture,
    ExternalEvidenceAttemptStatus,
    ExternalEvidenceBatchReceipt,
    ExternalEvidenceFetchAttempt,
    ExternalEvidenceProvider,
    ExternalEvidenceRedirectDecision,
    ExternalEvidenceRightsAssertion,
    RetrievalOperation,
    RetrievalPolicy,
    RetrievalProviderDescriptor,
    assess_external_evidence_redirect,
    build_external_evidence_batch_receipt,
    url_contains_sensitive_material,
)
from ...schemas.fulltext_excerpt import (
    MAX_FULLTEXT_EXCERPT_CHARS,
    FulltextExcerpt,
    OaRoute,
    build_fulltext_excerpt,
)
from ..context.topic_evidence import (
    R5TopicSourceRecordEvidence,
    TopicSourceAbstractStatus,
    TopicSourceSnippetKind,
)

MAX_FETCH_RESPONSE_BYTES = 64_000
_TEXT_MEDIA_TYPES = {
    "text/plain",
    "text/html",
    "text/xml",
    "application/xml",
    "application/xhtml+xml",
}
_BLOCKED_PAGE_MARKERS = (
    "access denied",
    "institutional access",
    "log in to access",
    "login to access",
    "purchase access",
    "sign in to access",
    "subscribe to read",
    "verify you are human",
)
_NAVIGATION_TEXT_MARKERS = frozenset(
    {
        "contact",
        "cookie",
        "home",
        "login",
        "menu",
        "next",
        "previous",
        "privacy",
        "search",
        "signin",
    }
)
_MIN_STRUCTURED_SUBSTANTIVE_CHARS = 48
_MIN_UNSTRUCTURED_SUBSTANTIVE_CHARS = 120
OA_FULLTEXT_TRANSPORT_DESCRIPTOR = RetrievalProviderDescriptor(
    provider_id="maieusis-oa-http",
    provider_name="Maieusis rights-aware OA HTTP adapter",
    provider_version="2",
    supported_operations=[RetrievalOperation.TOPIC_FULLTEXT_EXCERPT],
)
OA_FULLTEXT_RETRIEVAL_POLICY = RetrievalPolicy(
    policy_id="topic-oa-short-excerpt/v1",
    allowed_operations=[RetrievalOperation.TOPIC_FULLTEXT_EXCERPT],
    provider_precedence={
        RetrievalOperation.TOPIC_FULLTEXT_EXCERPT: [
            ExternalEvidenceProvider.PMC.value,
            ExternalEvidenceProvider.ARXIV.value,
            ExternalEvidenceProvider.BIORXIV.value,
            ExternalEvidenceProvider.MEDRXIV.value,
            ExternalEvidenceProvider.UNPAYWALL.value,
            ExternalEvidenceProvider.OPENALEX.value,
        ]
    },
)

_OA_PROVIDER_PRECEDENCE = {
    provider: index
    for index, provider in enumerate(
        OA_FULLTEXT_RETRIEVAL_POLICY.provider_precedence[RetrievalOperation.TOPIC_FULLTEXT_EXCERPT]
    )
}


class FulltextFetcher(Protocol):
    """Fetch a verified short excerpt, or ``None`` when no eligible text exists."""

    def fetch(self, record: R5TopicSourceRecordEvidence) -> FulltextExcerpt | None: ...


class NullFulltextFetcher:
    def fetch(self, record: R5TopicSourceRecordEvidence) -> FulltextExcerpt | None:
        return None


@dataclass(frozen=True)
class ExternalEvidenceHttpResponse:
    """Transport-neutral HTTP response surface used by the live fetcher and tests."""

    status_code: int
    final_url: str
    media_type: str
    body: bytes


class DeterministicFakeRetrievalAdapter:
    """Hermetic adapter with operation-specific, secret-scanned fixtures.

    This is intentionally small: it proves paper/topic/dataset routing and provider
    precedence without pretending to be the later provider-neutral retrieval stack.
    """

    def __init__(
        self,
        *,
        descriptor: RetrievalProviderDescriptor,
        fixtures: Sequence[DeterministicRetrievalFixture],
    ) -> None:
        self.descriptor = descriptor
        self.calls: list[tuple[RetrievalOperation, str]] = []
        keyed: dict[tuple[RetrievalOperation, str], DeterministicRetrievalFixture] = {}
        for fixture in fixtures:
            if fixture.provider_id != descriptor.provider_id:
                raise ValueError("fake retrieval fixture provider does not match its adapter")
            if fixture.operation not in descriptor.supported_operations:
                raise ValueError("fake retrieval fixture operation is unsupported by its adapter")
            key = (fixture.operation, fixture.locator)
            if key in keyed:
                raise ValueError("fake retrieval fixtures must be unique per operation and locator")
            keyed[key] = fixture
        self._fixtures = keyed

    def retrieve(
        self,
        operation: RetrievalOperation,
        locator: str,
    ) -> DeterministicRetrievalFixture | None:
        if operation not in self.descriptor.supported_operations:
            raise ValueError("retrieval operation is not supported by this fake adapter")
        self.calls.append((operation, locator))
        return self._fixtures.get((operation, locator))


def retrieve_from_fake_adapters(
    adapters: Sequence[DeterministicFakeRetrievalAdapter],
    *,
    policy: RetrievalPolicy,
    operation: RetrievalOperation,
    locator: str,
) -> DeterministicRetrievalFixture | None:
    """Resolve a fixture in deterministic configured-provider order."""

    if operation not in policy.allowed_operations:
        raise ValueError("retrieval operation is disabled by policy")
    precedence = {
        provider_id: index
        for index, provider_id in enumerate(policy.provider_precedence.get(operation, []))
    }
    ordered = sorted(
        adapters,
        key=lambda adapter: (
            precedence.get(adapter.descriptor.provider_id, len(precedence)),
            adapter.descriptor.provider_id,
            adapter.descriptor.provider_version,
        ),
    )
    for adapter in ordered:
        if operation not in adapter.descriptor.supported_operations:
            continue
        fixture = adapter.retrieve(operation, locator)
        if fixture is not None:
            return fixture
    return None


@dataclass(frozen=True)
class FulltextFetchResult:
    excerpt: FulltextExcerpt | None
    attempt: ExternalEvidenceFetchAttempt


@dataclass
class FulltextEnrichmentCounts:
    """Back-compatible counters plus typed per-attempt accounting."""

    attempted: int = 0
    succeeded: int = 0
    failed_no_oa: int = 0
    failed_error: int = 0
    attempt_receipts: list[ExternalEvidenceFetchAttempt] = field(default_factory=list)
    operation: RetrievalOperation = RetrievalOperation.TOPIC_FULLTEXT_EXCERPT
    transport_descriptor: RetrievalProviderDescriptor = OA_FULLTEXT_TRANSPORT_DESCRIPTOR
    retrieval_policy: RetrievalPolicy = OA_FULLTEXT_RETRIEVAL_POLICY
    input_table_digest: str = ""
    declared_target_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, int]:
        # Keep the v0.1 orchestration receipt shape stable; the typed batch is separate.
        return {
            "attempted": self.attempted,
            "succeeded": self.succeeded,
            "failed_no_oa": self.failed_no_oa,
            "failed_error": self.failed_error,
        }

    def outcome_note(self, *, requested: bool) -> str:
        """The honest sentence about what this batch actually grounded; empty when it grounded some.

        Measured on 2026-08-13 over the live corpus on this machine: 24 of 24 legs carrying counts
        attempted at least one full-text target and NONE ever succeeded (113 attempts, 0 successes;
        per-attempt statuses across the same 24 batch receipts were no_eligible_assertion 59,
        rights_rejected 41, http_error 9, media_type_rejected 4 — the word `succeeded` does not
        appear once). The config knob now defaults off, but a reader of a receipt should not have to
        infer the outcome from four counters either way.

        ``requested`` is the run's own ``literature.enabled and literature.fulltext_enrichment``. It
        is not optional politeness: with the lane off the driver still tallies eligible TARGETS
        against a null fetcher, so ``attempted`` is non-zero on a run that issued no fetch at all,
        and a warning phrased as "attempted N and enriched none" would itself be the kind of false
        claim this card exists to remove.
        """
        if self.succeeded > 0:
            return ""
        if not requested:
            return (
                "full-text enrichment was not requested (literature.fulltext_enrichment is off); "
                "this run's topic evidence is abstract-only"
            )
        if self.attempted <= 0:
            return ""
        return (
            f"WARNING: full-text enrichment attempted {self.attempted} target(s) and enriched none; "
            "this run's topic evidence is abstract-only"
        )

    def build_batch_receipt(self) -> ExternalEvidenceBatchReceipt:
        return build_external_evidence_batch_receipt(
            self.attempt_receipts,
            operation=self.operation,
            transport_descriptor=self.transport_descriptor,
            retrieval_policy=self.retrieval_policy,
            input_table_digest=self.input_table_digest,
            declared_target_ids=self.declared_target_ids,
        )


def enrich_records_with_fulltext(
    records: Sequence[R5TopicSourceRecordEvidence],
    *,
    fetcher: FulltextFetcher,
    target_source_ids: Iterable[str],
) -> tuple[list[R5TopicSourceRecordEvidence], FulltextEnrichmentCounts]:
    """Enrich eligible target records and retain one typed receipt per attempted target.

    The public return remains a two-tuple for orchestration compatibility.  Receipt
    fields are available as ``counts.attempt_receipts`` and
    ``counts.build_batch_receipt()``.  Legacy excerpts remain readable but are not
    promoted because they lack verified rights/response provenance.
    """

    targets = {str(source_id).strip() for source_id in target_source_ids if str(source_id).strip()}
    descriptor = getattr(fetcher, "descriptor", OA_FULLTEXT_TRANSPORT_DESCRIPTOR)
    policy = getattr(fetcher, "policy", OA_FULLTEXT_RETRIEVAL_POLICY)
    if not isinstance(descriptor, RetrievalProviderDescriptor) or not isinstance(
        policy, RetrievalPolicy
    ):
        raise TypeError(
            "full-text fetcher descriptor and policy must use typed retrieval contracts"
        )
    input_table_digest = stable_hash([record.model_dump(mode="json") for record in records])
    counts = FulltextEnrichmentCounts(
        attempted=len(targets),
        transport_descriptor=descriptor,
        retrieval_policy=policy,
        input_table_digest=input_table_digest,
        declared_target_ids=sorted(targets),
    )
    enriched: list[R5TopicSourceRecordEvidence] = []
    processed_targets: set[str] = set()
    for record in records:
        source_id = record.source_record_id
        if source_id not in targets or source_id in processed_targets:
            enriched.append(record)
            continue
        processed_targets.add(source_id)
        if record.snippet_kind == TopicSourceSnippetKind.FULLTEXT_EXCERPT:
            counts.attempt_receipts.append(
                _attempt(
                    record,
                    status=ExternalEvidenceAttemptStatus.SKIPPED_ALREADY_FULLTEXT,
                    descriptor=descriptor,
                    policy=policy,
                    detail="target already carries a full-text excerpt",
                )
            )
            enriched.append(record)
            continue
        if not record.can_support_claims:
            counts.attempt_receipts.append(
                _attempt(
                    record,
                    status=ExternalEvidenceAttemptStatus.SKIPPED_CANNOT_SUPPORT,
                    descriptor=descriptor,
                    policy=policy,
                    detail="target cannot support scientific claims",
                )
            )
            enriched.append(record)
            continue
        try:
            fetch_with_receipt = getattr(fetcher, "fetch_with_receipt", None)
            if callable(fetch_with_receipt):
                result = fetch_with_receipt(record)
            else:
                excerpt = fetcher.fetch(record)
                result = _compatibility_fetch_result(record, excerpt)
        except Exception as exc:  # an external failure never becomes a scientific rejection
            result = FulltextFetchResult(
                excerpt=None,
                attempt=_attempt(
                    record,
                    status=ExternalEvidenceAttemptStatus.FETCH_ERROR,
                    descriptor=descriptor,
                    policy=policy,
                    detail=f"fetcher raised {type(exc).__name__}",
                ),
            )
        if result.excerpt is not None and (
            not _excerpt_is_bound_to_record(record, result.excerpt)
            or result.excerpt.retrieval_attempt != result.attempt
        ):
            result = FulltextFetchResult(
                excerpt=None,
                attempt=_attempt(
                    record,
                    status=ExternalEvidenceAttemptStatus.RIGHTS_REJECTED,
                    descriptor=descriptor,
                    policy=policy,
                    detail=(
                        "fetcher excerpt and returned attempt were not exactly bound to "
                        "the record's rights assertion"
                    ),
                ),
            )
        if (
            result.excerpt is None
            and result.attempt.status == ExternalEvidenceAttemptStatus.SUCCEEDED
        ):
            result = FulltextFetchResult(
                excerpt=None,
                attempt=_attempt(
                    record,
                    status=ExternalEvidenceAttemptStatus.RIGHTS_REJECTED,
                    descriptor=descriptor,
                    policy=policy,
                    detail="fetcher reported success without a bound excerpt",
                ),
            )
        if not _attempt_matches_adapter(
            result.attempt,
            source_record_id=source_id,
            descriptor=descriptor,
            policy=policy,
        ):
            result = FulltextFetchResult(
                excerpt=None,
                attempt=_attempt(
                    record,
                    status=ExternalEvidenceAttemptStatus.RIGHTS_REJECTED,
                    descriptor=descriptor,
                    policy=policy,
                    detail="fetcher attempt transport or policy binding mismatch",
                ),
            )
        counts.attempt_receipts.append(result.attempt)
        if result.excerpt is None:
            if result.attempt.status in {
                ExternalEvidenceAttemptStatus.NO_ELIGIBLE_ASSERTION,
                ExternalEvidenceAttemptStatus.RIGHTS_REJECTED,
            }:
                counts.failed_no_oa += 1
            else:
                counts.failed_error += 1
            enriched.append(record)
            continue
        if not result.excerpt.has_verified_rights:
            # Defensive: a custom provider cannot promote a v0.1 rights-unverified object.
            counts.failed_no_oa += 1
            enriched.append(record)
            continue
        counts.succeeded += 1
        enriched.append(
            R5TopicSourceRecordEvidence.model_validate(
                {
                    **record.model_dump(mode="python"),
                    "snippet_kind": TopicSourceSnippetKind.FULLTEXT_EXCERPT.value,
                    "abstract_or_snippet": result.excerpt.excerpt,
                    "abstract_status": TopicSourceAbstractStatus.AVAILABLE.value,
                    "fulltext_fallback_abstract_or_snippet": record.abstract_or_snippet,
                    "fulltext_fallback_snippet_kind": record.snippet_kind.value,
                    "fulltext_provenance": result.excerpt.model_dump(mode="python"),
                }
            )
        )
    for missing_source_id in sorted(targets - processed_targets):
        counts.attempt_receipts.append(
            _attempt_for_source_id(
                missing_source_id,
                status=ExternalEvidenceAttemptStatus.TARGET_NOT_FOUND,
                descriptor=descriptor,
                policy=policy,
                detail="declared full-text target is absent from the input table",
            )
        )
    return enriched, counts


def _excerpt_is_bound_to_record(
    record: R5TopicSourceRecordEvidence,
    excerpt: FulltextExcerpt,
) -> bool:
    assertion = excerpt.rights_assertion
    attempt = excerpt.retrieval_attempt
    if assertion is None or attempt is None or attempt.source_record_id != record.source_record_id:
        return False
    return any(item == assertion for item in record.fulltext_rights_assertions)


def _compatibility_fetch_result(
    record: R5TopicSourceRecordEvidence,
    excerpt: FulltextExcerpt | None,
) -> FulltextFetchResult:
    if excerpt is None:
        return FulltextFetchResult(
            excerpt=None,
            attempt=_attempt(record, status=ExternalEvidenceAttemptStatus.NO_ELIGIBLE_ASSERTION),
        )
    if not excerpt.has_verified_rights:
        return FulltextFetchResult(
            excerpt=None,
            attempt=_attempt(
                record,
                status=ExternalEvidenceAttemptStatus.RIGHTS_REJECTED,
                detail="custom fetcher returned a legacy rights-unverified excerpt",
            ),
        )
    assert excerpt.retrieval_attempt is not None
    return FulltextFetchResult(excerpt=excerpt, attempt=excerpt.retrieval_attempt)


def _record_assertions(record: Any) -> list[ExternalEvidenceRightsAssertion]:
    raw = getattr(record, "fulltext_rights_assertions", []) or []
    assertions: list[ExternalEvidenceRightsAssertion] = []
    for item in raw:
        try:
            assertion = (
                item
                if isinstance(item, ExternalEvidenceRightsAssertion)
                else ExternalEvidenceRightsAssertion.model_validate(item)
            )
        except (TypeError, ValueError) as exc:
            raise _InvalidRightsAssertions from exc
        if _assertion_matches_record(assertion, record):
            assertions.append(assertion)
    decisions: dict[tuple[str, str, str], tuple[str, str, str, str]] = {}
    for assertion in assertions:
        subject = (
            assertion.provider.value,
            assertion.bibliographic_locator.lower(),
            assertion.asserted_url.lower(),
        )
        decision = (
            assertion.url_role.value,
            assertion.access_status.value,
            assertion.persistence_permission.value,
            assertion.license_id.lower(),
        )
        prior = decisions.setdefault(subject, decision)
        if prior != decision:
            raise _ConflictingRightsAssertions
    eligible = [assertion for assertion in assertions if assertion.authorizes_short_excerpt]
    if eligible:
        return eligible
    if assertions:
        raise _RightsAssertionRefused
    return []


def _assertion_matches_record(assertion: ExternalEvidenceRightsAssertion, record: Any) -> bool:
    locators = {
        _normalized_bibliographic_locator(str(getattr(record, name, "") or ""))
        for name in (
            "source_record_id",
            "source_locator",
            "doi",
            "pmid",
            "pmcid",
            "openalex_id",
            "semantic_scholar_id",
        )
    }
    locators.discard("")
    subject = _normalized_bibliographic_locator(assertion.bibliographic_locator)
    return subject in locators


def _normalized_bibliographic_locator(value: str) -> str:
    normalized = value.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if normalized.startswith(prefix):
            return normalized.removeprefix(prefix).strip()
    return normalized


class _ConflictingRightsAssertions(ValueError):
    pass


class _InvalidRightsAssertions(ValueError):
    pass


class _RightsAssertionRefused(ValueError):
    pass


def _oa_target(
    record: R5TopicSourceRecordEvidence,
) -> tuple[str, OaRoute, ExternalEvidenceRightsAssertion] | None:
    """Return only an explicit, source-matching OA/repository assertion."""

    assertions = _record_assertions(record)
    if not assertions:
        return None
    assertion = sorted(
        assertions,
        key=lambda item: (
            _OA_PROVIDER_PRECEDENCE.get(item.provider.value, len(_OA_PROVIDER_PRECEDENCE)),
            item.provider.value,
            item.assertion_id,
        ),
    )[0]
    route = {
        ExternalEvidenceProvider.OPENALEX: OaRoute.OPENALEX_OA_LOCATION,
        ExternalEvidenceProvider.ARXIV: OaRoute.ARXIV,
        ExternalEvidenceProvider.BIORXIV: OaRoute.ARXIV,
        ExternalEvidenceProvider.MEDRXIV: OaRoute.ARXIV,
        ExternalEvidenceProvider.PMC: OaRoute.PMC_OA,
        ExternalEvidenceProvider.UNPAYWALL: OaRoute.UNPAYWALL,
    }[assertion.provider]
    return assertion.asserted_url, route, assertion


class OpenAccessFulltextFetcher:
    """Live OA fetcher with typed rights and observed-response validation."""

    def __init__(
        self,
        *,
        http_get_response: Callable[[str], ExternalEvidenceHttpResponse] | None = None,
        # Kept as a narrow injection alias for v0.1 tests. A string is interpreted as
        # an observed 200 text/plain response at the requested URL, never as rights.
        http_get_text: Callable[[str], str | None] | None = None,
        license_label: str = "",
        policy: RetrievalPolicy | None = None,
    ) -> None:
        self.descriptor = OA_FULLTEXT_TRANSPORT_DESCRIPTOR
        self.policy = policy or OA_FULLTEXT_RETRIEVAL_POLICY
        self._http_get_response = http_get_response or _default_http_get_response
        self._http_get_text = http_get_text
        self._legacy_license_label = license_label
        self.last_attempt: ExternalEvidenceFetchAttempt | None = None

    def fetch(self, record: R5TopicSourceRecordEvidence) -> FulltextExcerpt | None:
        result = self.fetch_with_receipt(record)
        return result.excerpt

    def fetch_with_receipt(self, record: R5TopicSourceRecordEvidence) -> FulltextFetchResult:
        if (
            not self.policy.network_enabled
            or RetrievalOperation.TOPIC_FULLTEXT_EXCERPT not in self.policy.allowed_operations
        ):
            return self._finish(
                None,
                _attempt(
                    record,
                    status=ExternalEvidenceAttemptStatus.RIGHTS_REJECTED,
                    descriptor=self.descriptor,
                    policy=self.policy,
                    detail="retrieval policy disables topic full-text excerpts",
                ),
            )
        try:
            target = _oa_target(record)
        except (
            _ConflictingRightsAssertions,
            _InvalidRightsAssertions,
            _RightsAssertionRefused,
        ) as exc:
            return self._finish(
                None,
                _attempt(
                    record,
                    status=ExternalEvidenceAttemptStatus.RIGHTS_REJECTED,
                    descriptor=self.descriptor,
                    policy=self.policy,
                    detail=(
                        "conflicting source-bound rights assertions"
                        if isinstance(exc, _ConflictingRightsAssertions)
                        else (
                            "source-bound rights assertion does not authorize persistence"
                            if isinstance(exc, _RightsAssertionRefused)
                            else "invalid source-bound rights assertion"
                        )
                    ),
                ),
            )
        if target is None:
            return self._finish(
                None,
                _attempt(
                    record,
                    status=ExternalEvidenceAttemptStatus.NO_ELIGIBLE_ASSERTION,
                    descriptor=self.descriptor,
                    policy=self.policy,
                ),
            )
        requested_url, route, assertion = target
        retrieved_at = datetime.now(UTC)
        request_decision = _assess_final_url(requested_url, requested_url)
        if request_decision != ExternalEvidenceRedirectDecision.NO_REDIRECT:
            return self._finish(
                None,
                _attempt(
                    record,
                    assertion=assertion,
                    status=ExternalEvidenceAttemptStatus.RIGHTS_REJECTED,
                    requested_url=requested_url,
                    redirect_decision=request_decision,
                    retrieved_at=retrieved_at,
                    descriptor=self.descriptor,
                    policy=self.policy,
                    detail="asserted URL host is not safe for external retrieval",
                ),
            )
        try:
            response = self._get_response(requested_url)
        except Exception as exc:
            return self._finish(
                None,
                _attempt(
                    record,
                    assertion=assertion,
                    status=ExternalEvidenceAttemptStatus.HTTP_ERROR,
                    requested_url=requested_url,
                    retrieved_at=retrieved_at,
                    descriptor=self.descriptor,
                    policy=self.policy,
                    detail=f"HTTP transport raised {type(exc).__name__}",
                ),
            )
        redirect_decision = _assess_final_url(requested_url, response.final_url)

        def observed_attempt(
            status: ExternalEvidenceAttemptStatus,
            *,
            excerpt_digest: str = "",
        ) -> ExternalEvidenceFetchAttempt:
            return _attempt(
                record,
                status=status,
                assertion=assertion,
                requested_url=requested_url,
                final_url=response.final_url,
                http_status=response.status_code,
                media_type=_normalized_media_type(response.media_type),
                redirect_decision=redirect_decision,
                response_body_digest=stable_hash(response.body),
                response_bytes=len(response.body),
                excerpt_digest=excerpt_digest,
                retrieved_at=retrieved_at,
                descriptor=self.descriptor,
                policy=self.policy,
            )

        if response.status_code != 200:
            return self._finish(
                None,
                observed_attempt(ExternalEvidenceAttemptStatus.STATUS_REJECTED),
            )
        if redirect_decision not in {
            ExternalEvidenceRedirectDecision.NO_REDIRECT,
            ExternalEvidenceRedirectDecision.SAME_HOST,
            ExternalEvidenceRedirectDecision.SAFE_SUBDOMAIN,
        }:
            return self._finish(
                None,
                observed_attempt(ExternalEvidenceAttemptStatus.FINAL_URL_REJECTED),
            )
        media_type = _normalized_media_type(response.media_type)
        if media_type not in _TEXT_MEDIA_TYPES:
            return self._finish(
                None,
                observed_attempt(ExternalEvidenceAttemptStatus.MEDIA_TYPE_REJECTED),
            )
        text = _validated_response_text(response.body, media_type=media_type)
        if text is None:
            return self._finish(
                None,
                observed_attempt(ExternalEvidenceAttemptStatus.BODY_REJECTED),
            )
        bounded = text[:MAX_FULLTEXT_EXCERPT_CHARS]
        excerpt_digest = stable_hash(bounded)
        attempt = observed_attempt(
            ExternalEvidenceAttemptStatus.SUCCEEDED,
            excerpt_digest=excerpt_digest,
        )
        excerpt = build_fulltext_excerpt(
            excerpt=bounded,
            source_url=response.final_url,
            oa_route=route,
            license=assertion.license_id,
            retrieved_at=retrieved_at,
            rights_assertion=assertion,
            retrieval_attempt=attempt,
        )
        return self._finish(excerpt, attempt)

    def _get_response(self, requested_url: str) -> ExternalEvidenceHttpResponse:
        if self._http_get_text is not None:
            text = self._http_get_text(requested_url)
            return ExternalEvidenceHttpResponse(
                status_code=200,
                final_url=requested_url,
                media_type="text/plain",
                body=(text or "").encode("utf-8"),
            )
        return self._http_get_response(requested_url)

    def _finish(
        self,
        excerpt: FulltextExcerpt | None,
        attempt: ExternalEvidenceFetchAttempt,
    ) -> FulltextFetchResult:
        self.last_attempt = attempt
        return FulltextFetchResult(excerpt=excerpt, attempt=attempt)


def _attempt(
    record: Any,
    *,
    status: ExternalEvidenceAttemptStatus,
    assertion: ExternalEvidenceRightsAssertion | None = None,
    requested_url: str = "",
    final_url: str = "",
    http_status: int | None = None,
    media_type: str = "",
    redirect_decision: ExternalEvidenceRedirectDecision = (
        ExternalEvidenceRedirectDecision.NOT_OBSERVED
    ),
    response_body_digest: str = "",
    response_bytes: int = 0,
    excerpt_digest: str = "",
    retrieved_at: datetime | None = None,
    detail: str = "",
    descriptor: RetrievalProviderDescriptor = OA_FULLTEXT_TRANSPORT_DESCRIPTOR,
    policy: RetrievalPolicy = OA_FULLTEXT_RETRIEVAL_POLICY,
) -> ExternalEvidenceFetchAttempt:
    source_record_id = str(getattr(record, "source_record_id", "") or "unknown-source")
    return _attempt_for_source_id(
        source_record_id,
        status=status,
        assertion=assertion,
        requested_url=requested_url,
        final_url=final_url,
        http_status=http_status,
        media_type=media_type,
        redirect_decision=redirect_decision,
        response_body_digest=response_body_digest,
        response_bytes=response_bytes,
        excerpt_digest=excerpt_digest,
        retrieved_at=retrieved_at,
        detail=detail,
        descriptor=descriptor,
        policy=policy,
    )


def _attempt_for_source_id(
    source_record_id: str,
    *,
    status: ExternalEvidenceAttemptStatus,
    assertion: ExternalEvidenceRightsAssertion | None = None,
    requested_url: str = "",
    final_url: str = "",
    http_status: int | None = None,
    media_type: str = "",
    redirect_decision: ExternalEvidenceRedirectDecision = (
        ExternalEvidenceRedirectDecision.NOT_OBSERVED
    ),
    response_body_digest: str = "",
    response_bytes: int = 0,
    excerpt_digest: str = "",
    retrieved_at: datetime | None = None,
    detail: str = "",
    descriptor: RetrievalProviderDescriptor = OA_FULLTEXT_TRANSPORT_DESCRIPTOR,
    policy: RetrievalPolicy = OA_FULLTEXT_RETRIEVAL_POLICY,
) -> ExternalEvidenceFetchAttempt:
    timestamp = retrieved_at or datetime.now(UTC)
    sanitized_requested_url = _sanitize_receipt_url(requested_url)
    identity = {
        "source_record_id": source_record_id,
        "assertion_id": assertion.assertion_id if assertion else "",
        "requested_url": sanitized_requested_url,
        "retrieved_at": timestamp.isoformat(),
        "status": status.value,
    }
    semantic_request_digest = stable_hash(
        {
            "operation": RetrievalOperation.TOPIC_FULLTEXT_EXCERPT.value,
            "source_record_id": source_record_id,
            "assertion_id": assertion.assertion_id if assertion else "",
            "requested_url": sanitized_requested_url,
        }
    )
    return ExternalEvidenceFetchAttempt(
        attempt_id=f"external-evidence-attempt-{stable_hash(identity)[:16]}",
        source_record_id=source_record_id,
        operation=RetrievalOperation.TOPIC_FULLTEXT_EXCERPT,
        transport_descriptor=descriptor,
        transport_descriptor_id=descriptor.provider_id,
        transport_descriptor_version=descriptor.provider_version,
        transport_descriptor_digest=descriptor.semantic_digest,
        retrieval_policy=policy,
        retrieval_policy_id=policy.policy_id,
        retrieval_policy_digest=policy.semantic_digest,
        semantic_request_digest=semantic_request_digest,
        assertion_id=assertion.assertion_id if assertion else "",
        rights_assertion_digest=(
            stable_hash(assertion.model_dump(mode="json")) if assertion else ""
        ),
        provider=assertion.provider if assertion else None,
        requested_url=sanitized_requested_url,
        final_url=_sanitize_receipt_url(final_url),
        status=status,
        http_status=http_status,
        media_type=media_type,
        redirect_decision=redirect_decision,
        response_body_digest=response_body_digest,
        response_bytes=response_bytes,
        excerpt_digest=excerpt_digest,
        retrieved_at=timestamp,
        detail=detail,
    )


def _attempt_matches_adapter(
    attempt: ExternalEvidenceFetchAttempt,
    *,
    source_record_id: str,
    descriptor: RetrievalProviderDescriptor,
    policy: RetrievalPolicy,
) -> bool:
    return all(
        (
            attempt.source_record_id == source_record_id,
            attempt.operation == RetrievalOperation.TOPIC_FULLTEXT_EXCERPT,
            attempt.transport_descriptor == descriptor,
            attempt.transport_descriptor_id == descriptor.provider_id,
            attempt.transport_descriptor_version == descriptor.provider_version,
            attempt.transport_descriptor_digest == descriptor.semantic_digest,
            attempt.retrieval_policy == policy,
            attempt.retrieval_policy_id == policy.policy_id,
            attempt.retrieval_policy_digest == policy.semantic_digest,
        )
    )


def _normalized_media_type(value: str) -> str:
    return value.split(";", 1)[0].strip().lower()


def _assess_final_url(
    requested_url: str,
    final_url: str,
) -> ExternalEvidenceRedirectDecision:
    return assess_external_evidence_redirect(requested_url, final_url)


def _url_has_sensitive_material(value: str) -> bool:
    return url_contains_sensitive_material(value)


def _sanitize_receipt_url(value: str) -> str:
    """Remove credentials/sensitive query data before any URL enters a durable receipt."""

    if not value or not _url_has_sensitive_material(value):
        return value
    parsed = urlparse(value)
    host = parsed.hostname or "redacted.invalid"
    rendered_host = f"[{host}]" if ":" in host else host
    try:
        port = parsed.port
    except ValueError:
        port = None
    netloc = f"{rendered_host}:{port}" if port is not None else rendered_host
    return parsed._replace(netloc=netloc, query="", fragment="").geturl()


def _host_is_unsafe(host: str) -> bool:
    if not host or host == "localhost" or host.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_reserved,
            address.is_unspecified,
            address.is_multicast,
        )
    )


def _validate_public_network_target(url: str) -> None:
    """Resolve and reject non-public HTTP targets before opening a connection."""

    if _assess_final_url(url, url) != ExternalEvidenceRedirectDecision.NO_REDIRECT:
        raise urllib.error.URLError("external retrieval target is unsafe")
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise urllib.error.URLError(
            "external retrieval target could not be safely resolved"
        ) from exc
    if not addresses:
        raise urllib.error.URLError("external retrieval target has no resolved address")
    for address in addresses:
        sockaddr = address[4]
        if not sockaddr or _host_is_unsafe(str(sockaddr[0])):
            raise urllib.error.URLError(
                "external retrieval target resolves to a non-public address"
            )


class _SafeExternalRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Validate every redirect destination before urllib follows it."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        resolved_url = urljoin(req.full_url, newurl)
        decision = _assess_final_url(req.full_url, resolved_url)
        if decision not in {
            ExternalEvidenceRedirectDecision.SAME_HOST,
            ExternalEvidenceRedirectDecision.SAFE_SUBDOMAIN,
        }:
            raise urllib.error.HTTPError(
                req.full_url,
                code,
                f"external redirect rejected: {decision.value}",
                headers,
                fp,
            )
        _validate_public_network_target(resolved_url)
        return super().redirect_request(req, fp, code, msg, headers, resolved_url)


def _validated_response_text(body: bytes, *, media_type: str) -> str | None:
    if not body or len(body) > MAX_FETCH_RESPONSE_BYTES:
        return None
    decoded = body.decode("utf-8", errors="replace")
    visible = decoded
    has_scientific_container = False
    if media_type in {"text/html", "application/xhtml+xml", "text/xml", "application/xml"}:
        visible = re.sub(
            r"(?is)<(script|style|nav|header|footer|aside|form)[^>]*>.*?</\1>",
            " ",
            visible,
        )
        content_blocks = re.findall(
            r"(?is)<(?:article|main|abstract)(?:\s[^>]*)?>(.*?)</(?:article|main|abstract)>",
            visible,
        )
        if content_blocks:
            has_scientific_container = True
            visible = " ".join(content_blocks)
        visible = re.sub(r"(?s)<[^>]+>", " ", visible)
        visible = unescape(visible)
    visible = " ".join(visible.split()).strip()
    probe = visible[:2500].lower()
    if any(marker in probe for marker in _BLOCKED_PAGE_MARKERS):
        return None
    latin_words = [word.lower() for word in re.findall(r"[A-Za-z]{2,}", visible)]
    navigation_markers = sum(word in _NAVIGATION_TEXT_MARKERS for word in latin_words)
    if latin_words and navigation_markers * 2 >= len(latin_words) and not has_scientific_container:
        return None
    # Language-neutral content floor: ``str.isalpha`` counts Unicode scripts,
    # including CJK, without requiring English scientific vocabulary. Structured
    # article containers earn a lower floor; unstructured text must supply a real
    # paragraph rather than a short navigation or publisher-chrome fragment.
    substantive_chars = sum(character.isalpha() for character in visible)
    minimum = (
        _MIN_STRUCTURED_SUBSTANTIVE_CHARS
        if has_scientific_container
        else _MIN_UNSTRUCTURED_SUBSTANTIVE_CHARS
    )
    if substantive_chars < minimum:
        return None
    return visible


def _default_http_get_response(
    url: str,
) -> ExternalEvidenceHttpResponse:  # pragma: no cover - live-only network path
    _validate_public_network_target(url)
    request = urllib.request.Request(url, headers={"User-Agent": "maieusis-oa-fulltext/2.0"})
    opener = urllib.request.build_opener(_SafeExternalRedirectHandler())
    with opener.open(request, timeout=30) as response:
        raw: bytes = response.read(MAX_FETCH_RESPONSE_BYTES + 1)
        status = int(getattr(response, "status", 200))
        final_url = str(response.geturl())
        media_type = str(response.headers.get("Content-Type") or "")
    return ExternalEvidenceHttpResponse(
        status_code=status,
        final_url=final_url,
        media_type=media_type,
        body=raw,
    )


# Kept as a private compatibility alias for code that imported the old helper.
def _default_http_get_text(url: str) -> str | None:  # pragma: no cover - live-only network path
    response = _default_http_get_response(url)
    return _validated_response_text(
        response.body, media_type=_normalized_media_type(response.media_type)
    )
