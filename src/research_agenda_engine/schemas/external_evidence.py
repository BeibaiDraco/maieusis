"""Typed rights and retrieval receipts for externally fetched scientific text.

Bibliographic URLs are not evidence that text is open access.  These types keep the
provider assertion, the asserted content URL, and the observed HTTP response bound
together so downstream code can distinguish verified short-excerpt authority from a
legacy or merely discoverable landing page.
"""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from html import unescape
from typing import Any
from urllib.parse import parse_qsl, urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..provenance import stable_hash

_ALWAYS_SENSITIVE_QUERY_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "client_secret",
        "credential",
        "password",
        "refresh_token",
        "token",
    }
)
_CONTEXTUAL_SENSITIVE_QUERY_KEYS = frozenset({"auth", "key", "sig", "signature"})
_SAFE_SECRET_PLACEHOLDERS = frozenset(
    {"", "none", "not-set", "redacted", "unset", "<redacted>", "[redacted]"}
)
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(?:authorization|proxy-authorization|x-api-key|api[_-]?key|"
    r"access[_-]?token|refresh[_-]?token|client[_-]?secret|password)"
    r"\s*[:=]\s*([^\s,;]+)"
)
_BEARER_SECRET = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")
_OPENAI_STYLE_SECRET = re.compile(r"(?i)\bsk-[A-Za-z0-9_-]{8,}")
_PRIVATE_KEY_MARKER = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
_EMBEDDED_HTTP_LOCATOR = re.compile(r"""(?i)\bhttps?://[^\s<>"']+""")
_PERSISTED_SECRET_FIELD_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "authorization",
        "client_secret",
        "cookie",
        "password",
        "proxy_authorization",
        "refresh_token",
        "set_cookie",
        "token",
        "x_api_key",
        "x_amz_credential",
        "x_amz_security_token",
        "x_amz_signature",
        "x_goog_credential",
        "x_goog_signature",
    }
)
_BLOCKED_EXTERNAL_URL_MARKERS = (
    "/login",
    "/paywall",
    "/purchase",
    "/signin",
    "/subscribe",
)
_SAFE_EXTERNAL_TEXT_MEDIA_TYPES = frozenset(
    {
        "application/xhtml+xml",
        "application/xml",
        "text/html",
        "text/plain",
        "text/xml",
    }
)


def _looks_like_secret_value(value: str) -> bool:
    stripped = value.strip()
    if stripped.lower() in _SAFE_SECRET_PLACEHOLDERS:
        return False
    if _OPENAI_STYLE_SECRET.search(stripped) or _BEARER_SECRET.search(stripped):
        return True
    # Contextual URL fields such as ``key=figure-1`` are valid scientific
    # locators.  Only long/high-entropy-looking values are treated as credentials.
    return (
        len(stripped) >= 16
        and bool(re.search(r"[A-Za-z]", stripped))
        and bool(re.search(r"[0-9._~+/=-]", stripped))
    )


def url_contains_sensitive_material(value: str) -> bool:
    """Return whether an HTTP locator contains credentials or secret query material.

    Generic short query fields remain usable (for example ``?key=figure-1``); the
    scanner rejects strong credential names and high-entropy contextual values.
    """

    # Provider abstracts and snippets commonly HTML-escape query separators.  Parse the
    # decoded locator so ``&amp;X-Amz-Signature=...`` and numeric entity variants cannot
    # turn a signed URL into an apparently ordinary bibliographic link.  Decoding is
    # detection-only: callers retain or redact the original prose bytes.
    parsed = urlparse(unescape(value))
    if parsed.username or parsed.password:
        return True
    query_items = [
        *parse_qsl(parsed.query, keep_blank_values=True),
        *parse_qsl(parsed.fragment, keep_blank_values=True),
    ]
    for key, item_value in query_items:
        normalized = key.strip().lower().replace("-", "_")
        cloud_secret = normalized in {
            "x_amz_credential",
            "x_amz_security_token",
            "x_amz_signature",
            "x_goog_credential",
            "x_goog_signature",
        }
        if normalized in _ALWAYS_SENSITIVE_QUERY_KEYS or cloud_secret:
            if item_value.strip().lower() not in _SAFE_SECRET_PLACEHOLDERS:
                return True
        elif normalized in _CONTEXTUAL_SENSITIVE_QUERY_KEYS and _looks_like_secret_value(
            item_value
        ):
            return True
    return False


def _embedded_http_locators(value: str) -> list[str]:
    """Extract prose-embedded HTTP locators for credential scanning.

    Common sentence punctuation is excluded from the parsed locator. This is not a general URL
    parser; it is a deliberately broad credential-leak detector over provider prose.
    """

    return [match.group(0).rstrip(".,;:!?)]}") for match in _EMBEDDED_HTTP_LOCATOR.finditer(value)]


def redact_sensitive_urls_from_text(value: str) -> str:
    """Remove only credential-bearing embedded URLs while retaining surrounding prose."""

    return _EMBEDDED_HTTP_LOCATOR.sub(
        lambda match: (
            "[credential-bearing URL removed]"
            if url_contains_sensitive_material(match.group(0).rstrip(".,;:!?)]}"))
            else match.group(0)
        ),
        value,
    )


def assert_secret_free_persisted_value(value: Any, *, path: str = "root") -> None:
    """Recursively reject high-confidence secrets from a persisted typed payload.

    This deliberately does not reject ordinary DOIs, PMIDs, hashes, query locators,
    or prose merely mentioning authentication.  It rejects credential-bearing URLs,
    authorization assignments, bearer/API tokens, and private keys at any depth.
    """

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="python")
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = str(key).strip().lower().replace("-", "_")
            if normalized_key == "credential_env_names":
                names = child if isinstance(child, Sequence) else []
                if isinstance(names, (str, bytes, bytearray)) or any(
                    not isinstance(name, str) or re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", name) is None
                    for name in names
                ):
                    raise ValueError(
                        f"persisted external-evidence field {path}.{key} must contain "
                        "environment-variable names only"
                    )
            elif normalized_key in _PERSISTED_SECRET_FIELD_KEYS:
                rendered = str(child).strip().lower()
                if rendered not in _SAFE_SECRET_PLACEHOLDERS:
                    raise ValueError(
                        f"persisted external-evidence field {path}.{key} contains "
                        "credential material"
                    )
            assert_secret_free_persisted_value(child, path=f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            assert_secret_free_persisted_value(child, path=f"{path}[{index}]")
        return
    if not isinstance(value, str):
        return
    stripped = value.strip()
    if any(url_contains_sensitive_material(url) for url in _embedded_http_locators(stripped)):
        raise ValueError(f"persisted external-evidence field {path} contains credentials")
    assignment = _SECRET_ASSIGNMENT.search(stripped)
    if assignment and assignment.group(1).strip().lower() not in _SAFE_SECRET_PLACEHOLDERS:
        raise ValueError(f"persisted external-evidence field {path} contains credential material")
    if (
        _BEARER_SECRET.search(stripped)
        or _OPENAI_STYLE_SECRET.search(stripped)
        or _PRIVATE_KEY_MARKER.search(stripped)
    ):
        raise ValueError(f"persisted external-evidence field {path} contains credential material")


class _SecretRefusingModel(BaseModel):
    """Pydantic base that scans raw nested input before it can be persisted."""

    @model_validator(mode="before")
    @classmethod
    def recursively_refuse_secrets(cls, value: Any) -> Any:
        assert_secret_free_persisted_value(value, path=cls.__name__)
        return value


class ExternalEvidenceProvider(StrEnum):
    OPENALEX = "openalex"
    ARXIV = "arxiv"
    BIORXIV = "biorxiv"
    MEDRXIV = "medrxiv"
    PMC = "pmc"
    UNPAYWALL = "unpaywall"
    LEGACY = "legacy"


class ExternalEvidenceUrlRole(StrEnum):
    BIBLIOGRAPHIC_LANDING = "bibliographic_landing"
    PROVIDER_ASSERTED_OA = "provider_asserted_oa"
    REPOSITORY_FULLTEXT = "repository_fulltext"


class ExternalEvidenceAccessStatus(StrEnum):
    OPEN_ACCESS = "open_access"
    RIGHTS_UNVERIFIED = "rights_unverified"
    RESTRICTED = "restricted"


class ExcerptPersistencePermission(StrEnum):
    SHORT_EXCERPT_ALLOWED = "short_excerpt_allowed"
    UNKNOWN = "unknown"
    PROHIBITED = "prohibited"


class ExternalEvidenceAttemptStatus(StrEnum):
    SUCCEEDED = "succeeded"
    NO_ELIGIBLE_ASSERTION = "no_eligible_assertion"
    HTTP_ERROR = "http_error"
    STATUS_REJECTED = "status_rejected"
    FINAL_URL_REJECTED = "final_url_rejected"
    MEDIA_TYPE_REJECTED = "media_type_rejected"
    BODY_REJECTED = "body_rejected"
    RIGHTS_REJECTED = "rights_rejected"
    FETCH_ERROR = "fetch_error"
    SKIPPED_ALREADY_FULLTEXT = "skipped_already_fulltext"
    SKIPPED_CANNOT_SUPPORT = "skipped_cannot_support"
    TARGET_NOT_FOUND = "target_not_found"


class ExternalEvidenceRedirectDecision(StrEnum):
    NOT_OBSERVED = "not_observed"
    NO_REDIRECT = "no_redirect"
    SAME_HOST = "same_host"
    SAFE_SUBDOMAIN = "safe_subdomain"
    REJECTED_CROSS_SITE = "rejected_cross_site"
    REJECTED_UNSAFE_HOST = "rejected_unsafe_host"
    REJECTED_HTTPS_DOWNGRADE = "rejected_https_downgrade"
    REJECTED_CREDENTIALS = "rejected_credentials"


def assess_external_evidence_redirect(
    requested_url: str,
    final_url: str,
) -> ExternalEvidenceRedirectDecision:
    """Classify a requested/final URL pair without contacting either host."""

    requested = urlparse(requested_url)
    final = urlparse(final_url)
    if requested.scheme not in {"http", "https"} or final.scheme not in {"http", "https"}:
        return ExternalEvidenceRedirectDecision.REJECTED_UNSAFE_HOST
    if not requested.netloc or not final.netloc:
        return ExternalEvidenceRedirectDecision.REJECTED_UNSAFE_HOST
    if url_contains_sensitive_material(requested_url) or url_contains_sensitive_material(final_url):
        return ExternalEvidenceRedirectDecision.REJECTED_CREDENTIALS
    requested_host = (requested.hostname or "").lower().rstrip(".")
    final_host = (final.hostname or "").lower().rstrip(".")
    if _host_is_unsafe(requested_host) or _host_is_unsafe(final_host):
        return ExternalEvidenceRedirectDecision.REJECTED_UNSAFE_HOST
    if requested.scheme == "https" and final.scheme != "https":
        return ExternalEvidenceRedirectDecision.REJECTED_HTTPS_DOWNGRADE
    lowered = f"{final.netloc}{final.path}".lower()
    if any(marker in lowered for marker in _BLOCKED_EXTERNAL_URL_MARKERS):
        return ExternalEvidenceRedirectDecision.REJECTED_UNSAFE_HOST
    if requested_url == final_url:
        return ExternalEvidenceRedirectDecision.NO_REDIRECT
    if requested_host == final_host:
        return ExternalEvidenceRedirectDecision.SAME_HOST
    if requested_host.endswith(f".{final_host}") or final_host.endswith(f".{requested_host}"):
        return ExternalEvidenceRedirectDecision.SAFE_SUBDOMAIN
    return ExternalEvidenceRedirectDecision.REJECTED_CROSS_SITE


class ExternalEvidenceAuthority(StrEnum):
    FULLTEXT_BACKED = "fulltext_backed"
    RIGHTS_UNVERIFIED = "rights_unverified"


class RetrievalOperation(StrEnum):
    """External retrieval capability, separated by scientific input family."""

    PAPER_METADATA = "paper.metadata"
    PAPER_ABSTRACT = "paper.abstract"
    PAPER_FULLTEXT_EXCERPT = "paper.fulltext_excerpt"
    TOPIC_LITERATURE_SEARCH = "topic.literature_search"
    TOPIC_FULLTEXT_EXCERPT = "topic.fulltext_excerpt"
    DATASET_METADATA = "dataset.metadata"
    DATASET_SAMPLE = "dataset.sample"


class RetrievalProviderDescriptor(_SecretRefusingModel):
    """Secret-free, typed description of one external retrieval provider."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider_id: str
    provider_name: str
    provider_version: str = ""
    base_urls: list[str] = Field(default_factory=list)
    supported_operations: list[RetrievalOperation]
    credential_env_names: list[str] = Field(default_factory=list)

    @field_validator("provider_id", "provider_name")
    @classmethod
    def require_provider_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("retrieval provider identity must be non-empty")
        return value

    @field_validator("base_urls")
    @classmethod
    def validate_provider_base_urls(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("retrieval provider base URLs must be unique")
        for value in values:
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("retrieval provider base URLs must be absolute HTTP(S) URLs")
            if url_contains_sensitive_material(value) or _host_is_unsafe(parsed.hostname or ""):
                raise ValueError(
                    "retrieval provider URLs must not contain credentials or unsafe hosts"
                )
        return values

    @field_validator("credential_env_names")
    @classmethod
    def require_names_not_secret_values(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("credential environment names must be unique")
        for value in values:
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{1,63}", value):
                raise ValueError(
                    "credential_env_names accepts environment-variable names only, never values"
                )
        return values

    @model_validator(mode="after")
    def require_operations(self) -> RetrievalProviderDescriptor:
        if not self.supported_operations:
            raise ValueError("retrieval provider must declare at least one operation")
        if len(self.supported_operations) != len(set(self.supported_operations)):
            raise ValueError("retrieval provider operations must be unique")
        return self

    @property
    def semantic_digest(self) -> str:
        return stable_hash(self.model_dump(mode="json"))


class RetrievalPolicy(_SecretRefusingModel):
    """Fail-closed external retrieval policy; never carries credential values."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: str
    allowed_operations: list[RetrievalOperation]
    network_enabled: bool = True
    paid_providers_enabled: bool = False
    require_explicit_fulltext_rights: bool = True
    persist_full_documents: bool = False
    max_persisted_excerpt_chars: int = Field(default=1500, ge=1, le=1500)
    credential_env_names: list[str] = Field(default_factory=list)
    provider_precedence: dict[RetrievalOperation, list[str]] = Field(default_factory=dict)

    @field_validator("policy_id")
    @classmethod
    def require_policy_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("retrieval policy_id must be non-empty")
        return value

    @field_validator("credential_env_names")
    @classmethod
    def validate_policy_credential_names(cls, values: list[str]) -> list[str]:
        # Reuse the descriptor's deliberately narrow secret-safe syntax.
        return RetrievalProviderDescriptor.require_names_not_secret_values(values)

    @model_validator(mode="after")
    def enforce_fulltext_firewall(self) -> RetrievalPolicy:
        if len(self.allowed_operations) != len(set(self.allowed_operations)):
            raise ValueError("retrieval policy operations must be unique")
        fulltext = {
            RetrievalOperation.PAPER_FULLTEXT_EXCERPT,
            RetrievalOperation.TOPIC_FULLTEXT_EXCERPT,
        }
        if (
            fulltext.intersection(self.allowed_operations)
            and not self.require_explicit_fulltext_rights
        ):
            raise ValueError("fulltext retrieval must require explicit rights assertions")
        if self.persist_full_documents:
            raise ValueError("Maieusis retrieval policy may not persist full external documents")
        if not self.network_enabled and self.paid_providers_enabled:
            raise ValueError(
                "paid providers cannot be enabled when retrieval network access is off"
            )
        for operation, providers in self.provider_precedence.items():
            if operation not in self.allowed_operations:
                raise ValueError("provider precedence may reference only allowed operations")
            normalized = [provider.strip() for provider in providers]
            if any(not provider for provider in normalized):
                raise ValueError("provider precedence identities must be non-empty")
            if len(normalized) != len(set(normalized)):
                raise ValueError("provider precedence identities must be unique per operation")
        return self

    @property
    def semantic_digest(self) -> str:
        return stable_hash(self.model_dump(mode="json"))


class DeterministicRetrievalFixture(_SecretRefusingModel):
    """Small secret-safe payload for hermetic operation/provider adapter tests."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_id: str
    provider_id: str
    operation: RetrievalOperation
    locator: str
    payload: dict[str, Any]
    payload_digest: str

    @field_validator("fixture_id", "provider_id", "locator", "payload_digest")
    @classmethod
    def require_fixture_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("retrieval fixtures require provider, locator, and digest identity")
        return value

    @model_validator(mode="after")
    def bind_fixture_payload(self) -> DeterministicRetrievalFixture:
        if self.payload_digest != stable_hash(self.payload):
            raise ValueError("retrieval fixture payload_digest does not match payload")
        return self


_OA_ASSERTION_PROVIDERS = {
    ExternalEvidenceProvider.OPENALEX,
    ExternalEvidenceProvider.ARXIV,
    ExternalEvidenceProvider.BIORXIV,
    ExternalEvidenceProvider.MEDRXIV,
    ExternalEvidenceProvider.PMC,
    ExternalEvidenceProvider.UNPAYWALL,
}


class ExternalEvidenceRightsAssertion(_SecretRefusingModel):
    """A provider statement about one exact external content URL.

    ``source_payload_hash`` binds the assertion to the provider response or repository
    identity from which it was derived.  A generic landing URL cannot become eligible
    merely by being copied into this model: all authority fields must agree.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    assertion_id: str
    provider: ExternalEvidenceProvider
    provider_record_id: str = ""
    bibliographic_locator: str
    asserted_url: str
    url_role: ExternalEvidenceUrlRole
    access_status: ExternalEvidenceAccessStatus
    license_id: str = ""
    persistence_permission: ExcerptPersistencePermission
    assertion_source_url: str = ""
    source_payload_hash: str
    asserted_at: datetime | None = None

    @field_validator(
        "assertion_id",
        "bibliographic_locator",
        "asserted_url",
        "source_payload_hash",
    )
    @classmethod
    def require_bound_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("external-evidence rights assertions require source-bound fields")
        return value

    @field_validator("asserted_url", "assertion_source_url")
    @classmethod
    def require_http_url_when_present(cls, value: str) -> str:
        value = value.strip()
        if not value:
            return value
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("external-evidence URLs must be absolute HTTP(S) URLs")
        if url_contains_sensitive_material(value) or _host_is_unsafe(parsed.hostname or ""):
            raise ValueError("external-evidence URLs must not contain credentials or unsafe hosts")
        return value

    @model_validator(mode="after")
    def prevent_landing_page_authority(self) -> ExternalEvidenceRightsAssertion:
        if self.url_role == ExternalEvidenceUrlRole.BIBLIOGRAPHIC_LANDING:
            if self.access_status == ExternalEvidenceAccessStatus.OPEN_ACCESS:
                raise ValueError("a bibliographic landing URL cannot assert open-access authority")
            if self.persistence_permission == ExcerptPersistencePermission.SHORT_EXCERPT_ALLOWED:
                raise ValueError("a bibliographic landing URL cannot authorize excerpt persistence")
        return self

    @property
    def authorizes_short_excerpt(self) -> bool:
        return (
            self.provider in _OA_ASSERTION_PROVIDERS
            and self.url_role
            in {
                ExternalEvidenceUrlRole.PROVIDER_ASSERTED_OA,
                ExternalEvidenceUrlRole.REPOSITORY_FULLTEXT,
            }
            and self.access_status == ExternalEvidenceAccessStatus.OPEN_ACCESS
            and self.persistence_permission == ExcerptPersistencePermission.SHORT_EXCERPT_ALLOWED
            and bool(self.source_payload_hash)
        )


class ExternalEvidenceFetchAttempt(_SecretRefusingModel):
    """One durable retrieval attempt, including negative and rejected outcomes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    attempt_id: str
    source_record_id: str
    operation: RetrievalOperation
    transport_descriptor: RetrievalProviderDescriptor
    transport_descriptor_id: str
    transport_descriptor_version: str
    transport_descriptor_digest: str
    retrieval_policy: RetrievalPolicy
    retrieval_policy_id: str
    retrieval_policy_digest: str
    semantic_request_digest: str
    assertion_id: str = ""
    rights_assertion_digest: str = ""
    provider: ExternalEvidenceProvider | None = None
    requested_url: str = ""
    final_url: str = ""
    status: ExternalEvidenceAttemptStatus
    http_status: int | None = None
    media_type: str = ""
    redirect_decision: ExternalEvidenceRedirectDecision = (
        ExternalEvidenceRedirectDecision.NOT_OBSERVED
    )
    response_body_digest: str = ""
    response_bytes: int = Field(default=0, ge=0)
    excerpt_digest: str = ""
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    detail: str = Field(default="", max_length=240)

    @field_validator("attempt_id", "source_record_id")
    @classmethod
    def require_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("external-evidence attempts require stable identities")
        return value

    @field_validator(
        "transport_descriptor_id",
        "transport_descriptor_version",
        "transport_descriptor_digest",
        "retrieval_policy_id",
        "retrieval_policy_digest",
        "semantic_request_digest",
    )
    @classmethod
    def require_retrieval_binding(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("external-evidence attempts require transport and policy bindings")
        return value

    @field_validator("requested_url", "final_url")
    @classmethod
    def refuse_sensitive_attempt_urls(cls, value: str) -> str:
        if value:
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("external-evidence attempt URLs must be absolute HTTP(S) URLs")
            if url_contains_sensitive_material(value):
                raise ValueError("external-evidence attempt URLs must not persist credentials")
        return value

    @model_validator(mode="after")
    def successful_attempt_is_complete(self) -> ExternalEvidenceFetchAttempt:
        if (
            self.transport_descriptor_id != self.transport_descriptor.provider_id
            or self.transport_descriptor_version != self.transport_descriptor.provider_version
            or self.transport_descriptor_digest != self.transport_descriptor.semantic_digest
        ):
            raise ValueError("external-evidence attempt transport descriptor binding mismatch")
        if (
            self.retrieval_policy_id != self.retrieval_policy.policy_id
            or self.retrieval_policy_digest != self.retrieval_policy.semantic_digest
        ):
            raise ValueError("external-evidence attempt retrieval policy binding mismatch")
        if self.operation not in self.transport_descriptor.supported_operations:
            raise ValueError("external-evidence attempt operation is unsupported by transport")
        if self.operation not in self.retrieval_policy.allowed_operations:
            raise ValueError("external-evidence attempt operation is disabled by policy")
        expected_request_digest = stable_hash(
            {
                "operation": self.operation.value,
                "source_record_id": self.source_record_id,
                "assertion_id": self.assertion_id,
                "requested_url": self.requested_url,
            }
        )
        if self.semantic_request_digest != expected_request_digest:
            raise ValueError("external-evidence semantic_request_digest does not match request")
        assertion_parts = (
            bool(self.assertion_id),
            self.provider is not None,
            bool(self.rights_assertion_digest),
        )
        if len(set(assertion_parts)) != 1:
            raise ValueError(
                "external-evidence assertion ID, provider, and assertion digest must be paired"
            )
        fulltext_operations = {
            RetrievalOperation.PAPER_FULLTEXT_EXCERPT,
            RetrievalOperation.TOPIC_FULLTEXT_EXCERPT,
        }
        if self.excerpt_digest and self.operation not in fulltext_operations:
            raise ValueError("only a full-text-excerpt operation may retain an excerpt digest")
        if self.status == ExternalEvidenceAttemptStatus.SUCCEEDED:
            missing = [
                name
                for name, value in (
                    ("assertion_id", self.assertion_id),
                    ("provider", self.provider),
                    ("requested_url", self.requested_url),
                    ("final_url", self.final_url),
                    ("media_type", self.media_type),
                    ("redirect_decision", self.redirect_decision),
                    ("response_body_digest", self.response_body_digest),
                    ("excerpt_digest", self.excerpt_digest),
                )
                if not value
            ]
            allowed_redirects = {
                ExternalEvidenceRedirectDecision.NO_REDIRECT,
                ExternalEvidenceRedirectDecision.SAME_HOST,
                ExternalEvidenceRedirectDecision.SAFE_SUBDOMAIN,
            }
            if (
                missing
                or self.http_status != 200
                or self.response_bytes <= 0
                or self.redirect_decision not in allowed_redirects
            ):
                raise ValueError(
                    "successful external-evidence attempt lacks response provenance: "
                    + ", ".join(missing)
                )
            expected_redirect = assess_external_evidence_redirect(
                self.requested_url, self.final_url
            )
            if self.redirect_decision != expected_redirect:
                raise ValueError(
                    "successful external-evidence redirect decision does not match safe URLs"
                )
            normalized_media_type = self.media_type.split(";", 1)[0].strip().lower()
            if normalized_media_type not in _SAFE_EXTERNAL_TEXT_MEDIA_TYPES:
                raise ValueError(
                    "successful external-evidence attempt has unsupported persisted media type"
                )
        return self


def _host_is_unsafe(host: str) -> bool:
    lowered = host.strip().lower().rstrip(".")
    if not lowered or lowered == "localhost" or lowered.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(lowered)
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


class ExternalEvidenceBatchReceipt(_SecretRefusingModel):
    """Digest-bound accounting for every attempted external-text target in a batch."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str
    operation: RetrievalOperation
    transport_descriptor: RetrievalProviderDescriptor
    transport_descriptor_id: str
    transport_descriptor_version: str
    transport_descriptor_digest: str
    retrieval_policy: RetrievalPolicy
    retrieval_policy_id: str
    retrieval_policy_digest: str
    input_table_digest: str
    declared_target_ids: list[str] = Field(default_factory=list)
    attempts: list[ExternalEvidenceFetchAttempt] = Field(default_factory=list)
    attempted_source_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    attempts_digest: str
    semantic_content_digest: str

    @field_validator(
        "receipt_id",
        "transport_descriptor_id",
        "transport_descriptor_version",
        "transport_descriptor_digest",
        "retrieval_policy_id",
        "retrieval_policy_digest",
        "input_table_digest",
    )
    @classmethod
    def require_batch_binding(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(
                "external-evidence batches require input, transport, and policy bindings"
            )
        return value

    @model_validator(mode="after")
    def bind_attempts_and_targets(self) -> ExternalEvidenceBatchReceipt:
        if (
            self.transport_descriptor_id != self.transport_descriptor.provider_id
            or self.transport_descriptor_version != self.transport_descriptor.provider_version
            or self.transport_descriptor_digest != self.transport_descriptor.semantic_digest
        ):
            raise ValueError("external-evidence batch transport descriptor binding mismatch")
        if (
            self.retrieval_policy_id != self.retrieval_policy.policy_id
            or self.retrieval_policy_digest != self.retrieval_policy.semantic_digest
        ):
            raise ValueError("external-evidence batch retrieval policy binding mismatch")
        if self.operation not in self.transport_descriptor.supported_operations:
            raise ValueError("external-evidence batch operation is unsupported by transport")
        if self.operation not in self.retrieval_policy.allowed_operations:
            raise ValueError("external-evidence batch operation is disabled by policy")
        payload = [attempt.model_dump(mode="json") for attempt in self.attempts]
        if self.attempts_digest != stable_hash(payload):
            raise ValueError("external-evidence batch attempts_digest does not match attempts")
        semantic_payload = _batch_semantic_payload(
            attempts=self.attempts,
            operation=self.operation,
            transport_descriptor_id=self.transport_descriptor_id,
            transport_descriptor_version=self.transport_descriptor_version,
            transport_descriptor_digest=self.transport_descriptor_digest,
            retrieval_policy_id=self.retrieval_policy_id,
            retrieval_policy_digest=self.retrieval_policy_digest,
            input_table_digest=self.input_table_digest,
            declared_target_ids=self.declared_target_ids,
        )
        if self.semantic_content_digest != stable_hash(semantic_payload):
            raise ValueError(
                "external-evidence batch semantic_content_digest does not match attempts"
            )
        attempt_ids = [attempt.attempt_id for attempt in self.attempts]
        if len(attempt_ids) != len(set(attempt_ids)):
            raise ValueError("external-evidence batch attempt IDs must be unique")
        observed = [attempt.source_record_id for attempt in self.attempts]
        if len(observed) != len(set(observed)):
            raise ValueError("external-evidence batch requires exactly one attempt per source")
        if len(self.attempted_source_ids) != len(set(self.attempted_source_ids)):
            raise ValueError("external-evidence batch target IDs must be unique")
        if len(self.declared_target_ids) != len(set(self.declared_target_ids)):
            raise ValueError("external-evidence batch declared target IDs must be unique")
        if sorted(self.declared_target_ids) != sorted(self.attempted_source_ids):
            raise ValueError("external-evidence batch declared targets do not match accounting")
        if sorted(self.attempted_source_ids) != sorted(observed):
            raise ValueError("external-evidence batch target accounting does not match attempts")
        for attempt in self.attempts:
            bindings = (
                attempt.operation == self.operation,
                attempt.transport_descriptor == self.transport_descriptor,
                attempt.transport_descriptor_id == self.transport_descriptor_id,
                attempt.transport_descriptor_version == self.transport_descriptor_version,
                attempt.transport_descriptor_digest == self.transport_descriptor_digest,
                attempt.retrieval_policy == self.retrieval_policy,
                attempt.retrieval_policy_id == self.retrieval_policy_id,
                attempt.retrieval_policy_digest == self.retrieval_policy_digest,
            )
            if not all(bindings):
                raise ValueError("external-evidence batch attempt binding mismatch")
        return self

    @property
    def outcome_counts(self) -> dict[str, int]:
        return {
            status.value: sum(attempt.status == status for attempt in self.attempts)
            for status in ExternalEvidenceAttemptStatus
        }


class LegacyExternalEvidenceDegradationReceipt(_SecretRefusingModel):
    """Audit-only authority downgrade for immutable v0.1 evidence artifacts.

    The original artifact is not rewritten and no provider is contacted.  Consumers
    persist this sidecar and apply the lower authority when loading the old bytes.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str
    migration_version: str = "external_evidence_rights/v1"
    original_artifact_path: str
    original_artifact_digest: str
    affected_source_ids: list[str]
    abstract_fallback_source_ids: list[str] = Field(default_factory=list)
    metadata_only_source_ids: list[str] = Field(default_factory=list)
    from_authority: ExternalEvidenceAuthority = ExternalEvidenceAuthority.FULLTEXT_BACKED
    to_authority: ExternalEvidenceAuthority = ExternalEvidenceAuthority.RIGHTS_UNVERIFIED
    original_artifact_rewritten: bool = False
    provider_calls_made: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "receipt_id",
        "original_artifact_path",
        "original_artifact_digest",
    )
    @classmethod
    def require_migration_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("legacy external-evidence degradation requires artifact identity")
        return value

    @model_validator(mode="after")
    def enforce_non_mutating_degradation(self) -> LegacyExternalEvidenceDegradationReceipt:
        if not self.affected_source_ids:
            raise ValueError("legacy external-evidence degradation requires affected source IDs")
        if len(self.affected_source_ids) != len(set(self.affected_source_ids)):
            raise ValueError("legacy external-evidence affected source IDs must be unique")
        fallback = set(self.abstract_fallback_source_ids)
        metadata_only = set(self.metadata_only_source_ids)
        if fallback.intersection(metadata_only):
            raise ValueError("legacy rights-degradation authority partitions must not overlap")
        if fallback.union(metadata_only) != set(self.affected_source_ids):
            raise ValueError(
                "legacy rights-degradation authority partitions must exactly cover affected sources"
            )
        if (
            self.from_authority != ExternalEvidenceAuthority.FULLTEXT_BACKED
            or self.to_authority != ExternalEvidenceAuthority.RIGHTS_UNVERIFIED
        ):
            raise ValueError(
                "legacy external-evidence degradation permits only FULLTEXT_BACKED to "
                "RIGHTS_UNVERIFIED"
            )
        if self.original_artifact_rewritten or self.provider_calls_made:
            raise ValueError(
                "legacy external-evidence degradation must not rewrite bytes or call providers"
            )
        return self


def build_external_evidence_batch_receipt(
    attempts: list[ExternalEvidenceFetchAttempt],
    *,
    operation: RetrievalOperation,
    transport_descriptor: RetrievalProviderDescriptor,
    retrieval_policy: RetrievalPolicy,
    input_table_digest: str,
    declared_target_ids: Sequence[str],
    created_at: datetime | None = None,
) -> ExternalEvidenceBatchReceipt:
    timestamp = created_at or datetime.now(UTC)
    ordered_attempts = sorted(attempts, key=lambda attempt: attempt.source_record_id)
    ordered_targets = sorted(set(declared_target_ids))
    payload = [attempt.model_dump(mode="json") for attempt in ordered_attempts]
    digest = stable_hash(payload)
    return ExternalEvidenceBatchReceipt(
        receipt_id=(
            "external-evidence-batch-"
            f"{stable_hash({'attempts': digest, 'input': input_table_digest, 'targets': ordered_targets})[:16]}"
        ),
        operation=operation,
        transport_descriptor_id=transport_descriptor.provider_id,
        transport_descriptor=transport_descriptor,
        transport_descriptor_version=transport_descriptor.provider_version,
        transport_descriptor_digest=transport_descriptor.semantic_digest,
        retrieval_policy_id=retrieval_policy.policy_id,
        retrieval_policy=retrieval_policy,
        retrieval_policy_digest=retrieval_policy.semantic_digest,
        input_table_digest=input_table_digest,
        declared_target_ids=ordered_targets,
        attempts=ordered_attempts,
        attempted_source_ids=ordered_targets,
        created_at=timestamp,
        attempts_digest=digest,
        semantic_content_digest=stable_hash(
            _batch_semantic_payload(
                attempts=ordered_attempts,
                operation=operation,
                transport_descriptor_id=transport_descriptor.provider_id,
                transport_descriptor_version=transport_descriptor.provider_version,
                transport_descriptor_digest=transport_descriptor.semantic_digest,
                retrieval_policy_id=retrieval_policy.policy_id,
                retrieval_policy_digest=retrieval_policy.semantic_digest,
                input_table_digest=input_table_digest,
                declared_target_ids=ordered_targets,
            )
        ),
    )


def _attempt_semantic_payload(attempt: ExternalEvidenceFetchAttempt) -> dict[str, object]:
    """Timestamp/attempt-ID-free result identity for cache and replay comparison."""

    payload = attempt.model_dump(mode="json")
    payload.pop("attempt_id", None)
    payload.pop("retrieved_at", None)
    return payload


def _batch_semantic_payload(
    *,
    attempts: Sequence[ExternalEvidenceFetchAttempt],
    operation: RetrievalOperation,
    transport_descriptor_id: str,
    transport_descriptor_version: str,
    transport_descriptor_digest: str,
    retrieval_policy_id: str,
    retrieval_policy_digest: str,
    input_table_digest: str,
    declared_target_ids: Sequence[str],
) -> dict[str, object]:
    return {
        "operation": operation.value,
        "transport_descriptor_id": transport_descriptor_id,
        "transport_descriptor_version": transport_descriptor_version,
        "transport_descriptor_digest": transport_descriptor_digest,
        "retrieval_policy_id": retrieval_policy_id,
        "retrieval_policy_digest": retrieval_policy_digest,
        "input_table_digest": input_table_digest,
        "declared_target_ids": sorted(declared_target_ids),
        "attempts": [_attempt_semantic_payload(attempt) for attempt in attempts],
    }
