"""Evidence-bound proposal-stage novelty admission artifacts.

These schemas deliberately describe a bounded prior-art search.  They never certify global
novelty.  Deterministic code owns identity, search receipts, and admission invariants; a separate
model reviewer owns the scientific comparison recorded in ``VariantNoveltyAssessment``.
"""

from __future__ import annotations

import ipaddress
import re
from datetime import UTC, datetime
from enum import StrEnum
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..provenance import stable_hash
from .external_evidence import assert_secret_free_persisted_value, url_contains_sensitive_material
from .maieusis_project_config import NoveltyWebToolRateCard, novelty_web_tool_rate_micro_usd

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_EMBEDDED_HTTP_LOCATOR = re.compile(r"(?i)\bhttps?://[^\s<>\"']+")
_MAX_NOVELTY_WEB_QUOTE_CHARS = 2_000


def _require_sha256(value: str, *, field_name: str) -> str:
    normalized = value.strip().lower()
    if _SHA256_HEX.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must be sha256 hex")
    return normalized


def _novelty_web_host_is_unsafe(host: str) -> bool:
    normalized = host.strip().lower().rstrip(".")
    if not normalized or normalized == "localhost" or normalized.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(normalized)
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


def sanitize_novelty_web_locator(value: str) -> str:
    """Return a durable, non-sensitive HTTP locator with query and fragment removed.

    The caller may turn a validation failure into a typed quarantine exclusion, but it must never
    persist the unsafe original.  Ordinary tracking parameters are removed as well: a locator in a
    durable novelty receipt identifies a source, it is not a replayable request URL.
    """

    normalized = value.strip()
    if not normalized:
        return ""
    assert_secret_free_persisted_value(normalized, path="novelty_web_locator")
    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("novelty web locator must be an absolute HTTP(S) URL")
    if _novelty_web_host_is_unsafe(parsed.hostname or ""):
        raise ValueError("novelty web locator must not target a local or private host")
    if parsed.username or parsed.password or url_contains_sensitive_material(normalized):
        raise ValueError("novelty web locator must not contain credentials")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, "", ""))


def sanitize_novelty_web_quote(value: str) -> str:
    """Bound a provider-supplied quote and remove non-sensitive tracking locators from it.

    Quotes are metadata only, never page content.  Any credential-bearing locator raises before a
    quote could be persisted; the service records only its digest in a typed exclusion.
    """

    normalized = value.strip()
    if len(normalized) > _MAX_NOVELTY_WEB_QUOTE_CHARS:
        raise ValueError(
            f"novelty web quote exceeds {_MAX_NOVELTY_WEB_QUOTE_CHARS} character hard limit"
        )
    assert_secret_free_persisted_value(normalized, path="novelty_web_quote")
    return _EMBEDDED_HTTP_LOCATOR.sub(
        lambda match: sanitize_novelty_web_locator(match.group(0).rstrip(".,;:!?)]}")),
        normalized,
    )


class _NoveltyWebPersistedModel(BaseModel):
    """Strict base for durable N-2 web metadata with an early secret scan."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def refuse_secret_material(cls, value: object) -> object:
        assert_secret_free_persisted_value(value, path=cls.__name__)
        return value


class NoveltyQueryFocus(StrEnum):
    #: One domain term, alone. The four prose foci below joined 2-3 whole sentences into a 19-41
    #: word query; OpenAlex ANDs un-operatored words over FULLTEXT, so 6 of 8 such queries returned
    #: ZERO on the 2026-07-31 leg, and Crossref -- which ranks and never abstains -- answered the
    #: rest with whatever was nearest, including papers on torture, Ukrainian cultural heritage and
    #: portfolio credit models. Extracting the terms is a judgement and belongs to the reviewer
    #: model; the four names below are retained so existing artifacts still load.
    DOMAIN_TERM = "domain_term"
    QUESTION = "question"
    SCIENTIFIC_TENSION = "scientific_tension"
    DISTINCTION = "distinction"
    CONSEQUENCES = "consequences"


class NoveltyEvidenceBasis(StrEnum):
    TITLE_ONLY = "title_only"
    ABSTRACT = "abstract"
    FULLTEXT_EXCERPT = "fulltext_excerpt"


class NoveltyScholarlyIdentity(StrEnum):
    """Deterministic identity that can support a direct-recap rejection."""

    UNVERIFIED = "unverified"
    DOI = "doi"
    OPENALEX = "openalex"
    CROSSREF = "crossref"


class NoveltyEvidenceExclusionReason(StrEnum):
    """Why an untrusted candidate was withheld from the reviewer packet."""

    PROPOSAL_FIREWALL = "proposal_firewall"


class NoveltyProviderAttemptStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DISABLED = "disabled"


class NoveltyEvidenceLane(StrEnum):
    """Whether an attempt is one of N-1's scholarly lanes or N-2 discovery metadata."""

    DETERMINISTIC_SCHOLARLY = "deterministic_scholarly"
    WEB_DISCOVERY = "web_discovery"


class NoveltyPriorEvidenceOrigin(StrEnum):
    """Whether a canonical scholarly prior arrived through the ordinary or N-2 lead lane."""

    DETERMINISTIC = "deterministic"
    WEB_LEAD_RESOLVED = "web_lead_resolved"


class NoveltyWebLeadRightsClass(StrEnum):
    """Low-authority persistence class for model-side web discovery metadata.

    N-2 currently retains metadata only.  The quote-valued member remains for wire compatibility
    with an early additive draft, but strict receipt validation rejects it: a scout's structured
    output is model text, not a vendor-supplied source quotation.
    """

    METADATA_ONLY_UNVERIFIED = "metadata_only_unverified"
    PROVIDER_SUPPLIED_SHORT_QUOTE_UNVERIFIED = "provider_supplied_short_quote_unverified"


class NoveltyWebGroundingExclusionReason(StrEnum):
    """Why untrusted model-side web material did not enter a durable lead."""

    UNSAFE_LOCATOR = "unsafe_locator"
    UNSAFE_QUOTE = "unsafe_quote"
    PROPOSAL_FIREWALL = "proposal_firewall"
    MALFORMED_PROVIDER_METADATA = "malformed_provider_metadata"
    UNBOUND_SOURCE = "unbound_source"
    MODEL_GENERATED_QUOTE = "model_generated_quote"


class NoveltyWebLeadResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    UNAVAILABLE = "unavailable"
    INVALID_INPUT = "invalid_input"
    ERROR = "error"


class NoveltyWebLeadResolutionMethod(StrEnum):
    DOI_SINGLE_ENTITY = "doi_single_entity"
    TITLE_RECONCILIATION = "title_reconciliation"
    NOT_ATTEMPTED = "not_attempted"


class NoveltyVerdict(StrEnum):
    DIRECT_RECAP = "direct_recap"
    CLOSE_PRIOR_REVISION_REQUIRED = "close_prior_revision_required"
    NO_DIRECT_RECAP_FOUND_IN_SCOPE = "no_direct_recap_found_in_scope"
    INSUFFICIENT_SEARCH_EVIDENCE = "insufficient_search_evidence"


class NoveltyVariantDisposition(StrEnum):
    ADMITTED = "admitted"
    REJECTED_DIRECT_RECAP = "rejected_direct_recap"
    DEFERRED_CLOSE_PRIOR = "deferred_close_prior"
    DEFERRED_INSUFFICIENT_EVIDENCE = "deferred_insufficient_evidence"
    #: The reviewer never answered usably. Distinct from DEFERRED_INSUFFICIENT_EVIDENCE, which is a
    #: finding ABOUT THE LITERATURE: across all 23 runs, 97% of non-scientific losses reached the
    #: reader wearing a scientific label, and only 9 of 51 `insufficient_search_evidence` verdicts
    #: were genuine search insufficiency.
    NOT_ASSESSED_INFRASTRUCTURE = "not_assessed_infrastructure"


class NoveltyWebSearchAction(_NoveltyWebPersistedModel):
    """One server-reported search action, with no invented query or result fields."""

    action_id: str
    action_type: str
    query: str = Field(default="", max_length=2_000)
    provider_action_id: str = Field(default="", max_length=512)
    reported_result_count: int | None = Field(default=None, ge=0)
    # ``None`` means the vendor did not report filters; ``[]`` means it explicitly reported none.
    reported_filters: list[str] | None = None

    @field_validator("action_id")
    @classmethod
    def require_identity(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("novelty web action identity fields must be non-empty")
        return normalized

    @field_validator("action_type")
    @classmethod
    def require_direct_search_action(cls, value: str) -> str:
        if value.strip().lower() != "search":
            raise ValueError("novelty web receipt actions must be canonical direct searches")
        return "search"


class NoveltyWebSearchSource(_NoveltyWebPersistedModel):
    """A quarantined source bound to a search action (metadata only).

    Some strict adapters report an opaque source ID.  Anthropic's documented basic web-search
    result shape does not, so the host may instead retain a separately labelled structural binding
    ID.  The latter is never vendor telemetry and cannot be mistaken for a scholarly identity.
    """

    source_id: str
    source_digest: str
    locator: str = ""
    title: str = Field(default="", max_length=1_000)
    provider_source_id: str = Field(default="", max_length=512)
    host_derived_source_binding_id: str = Field(default="", max_length=512)
    action_id: str = Field(default="", max_length=512)

    @field_validator("source_id")
    @classmethod
    def require_source_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("novelty web source requires a source_id")
        return normalized

    @field_validator("source_digest")
    @classmethod
    def require_source_digest(cls, value: str) -> str:
        return _require_sha256(value, field_name="novelty web source_digest")

    @field_validator("locator")
    @classmethod
    def sanitize_locator(cls, value: str) -> str:
        return sanitize_novelty_web_locator(value)

    @model_validator(mode="after")
    def require_source_binding_identity(self) -> NoveltyWebSearchSource:
        has_provider_id = bool(self.provider_source_id.strip())
        has_host_binding = bool(self.host_derived_source_binding_id.strip())
        if has_provider_id == has_host_binding:
            raise ValueError(
                "novelty web source requires exactly one provider or host-derived binding identity"
            )
        return self


class NoveltyWebGroundingExclusion(_NoveltyWebPersistedModel):
    """Digest-only quarantine outcome for unsafe or unbound model-side web material."""

    exclusion_id: str
    reason: NoveltyWebGroundingExclusionReason
    content_digest: str
    receipt_id: str = ""
    source_id: str = ""

    @field_validator("exclusion_id")
    @classmethod
    def require_exclusion_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("novelty web exclusion requires an exclusion_id")
        return normalized

    @field_validator("content_digest")
    @classmethod
    def require_content_digest(cls, value: str) -> str:
        return _require_sha256(value, field_name="novelty web exclusion content_digest")


class WebFoundPriorLead(_NoveltyWebPersistedModel):
    """Quarantined discovery metadata; never standalone scientific prior evidence."""

    schema_version: str = "web_found_prior_lead/v1"
    lead_id: str
    receipt_id: str
    source_id: str
    source_digest: str
    locator: str = ""
    title: str = Field(default="", max_length=1_000)
    claimed_doi: str = Field(default="", max_length=512)
    claimed_venue: str = Field(default="", max_length=512)
    claimed_year: int | None = Field(default=None, ge=1_000, le=3_000)
    # Retain the field as an in-process compatibility shim only.  It is always excluded from a
    # durable model dump and non-empty values fail closed: model structured output cannot be
    # relabelled as a provider-supplied quotation.
    provider_quote: str = Field(default="", exclude=True, repr=False)
    rights_class: NoveltyWebLeadRightsClass = NoveltyWebLeadRightsClass.METADATA_ONLY_UNVERIFIED

    @field_validator("lead_id", "receipt_id", "source_id")
    @classmethod
    def require_lead_identity(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("novelty web lead identity fields must be non-empty")
        return normalized

    @field_validator("source_digest")
    @classmethod
    def require_lead_source_digest(cls, value: str) -> str:
        return _require_sha256(value, field_name="novelty web lead source_digest")

    @field_validator("locator")
    @classmethod
    def sanitize_lead_locator(cls, value: str) -> str:
        return sanitize_novelty_web_locator(value)

    @field_validator("provider_quote")
    @classmethod
    def refuse_model_generated_quote(cls, value: str) -> str:
        if value.strip():
            raise ValueError("model-generated novelty web quotes must be excluded, not persisted")
        return ""

    @model_validator(mode="after")
    def validate_low_authority_lead(self) -> WebFoundPriorLead:
        if not (self.locator or self.title.strip() or self.claimed_doi.strip()):
            raise ValueError("novelty web lead requires a locator, title, or claimed DOI")
        if self.rights_class != NoveltyWebLeadRightsClass.METADATA_ONLY_UNVERIFIED:
            raise ValueError("novelty web leads retain metadata only; quotes cannot be persisted")
        return self


class NoveltyWebToolUsage(_NoveltyWebPersistedModel):
    """Only vendor-reported usage values; unknown values remain absent rather than estimated."""

    provider_reported_search_requests: int | None = Field(default=None, ge=0)
    provider_reported_input_tokens: int | None = Field(default=None, ge=0)
    provider_reported_output_tokens: int | None = Field(default=None, ge=0)


class NoveltyWebSearchReservation(_NoveltyWebPersistedModel):
    """Immutable pre-call spend reservation written before a model-side web request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "novelty_web_search_reservation/v1"
    reservation_id: str
    run_id: str
    question_family_id: str
    variant_id: str
    question_seed_id: str
    question_digest: str
    candidate_input_digest: str
    request_digest: str
    config_digest: str
    prompt_version: str
    prompt_digest: str
    provider_id: str
    model_id: str
    rate_card: NoveltyWebToolRateCard
    tool_rate_micro_usd: int = Field(ge=1)
    reserved_web_tool_uses: int = Field(ge=1)
    reserved_tool_spend_micro_usd: int = Field(ge=0)
    requested_search_cutoff: str = ""
    reserved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "reservation_id",
        "run_id",
        "question_family_id",
        "variant_id",
        "question_seed_id",
        "prompt_version",
        "provider_id",
        "model_id",
    )
    @classmethod
    def require_reservation_identity(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("novelty web reservation identity fields must be non-empty")
        return normalized

    @field_validator(
        "question_digest",
        "candidate_input_digest",
        "request_digest",
        "config_digest",
        "prompt_digest",
    )
    @classmethod
    def require_reservation_digest(cls, value: str) -> str:
        return _require_sha256(value, field_name="novelty web reservation digest")

    @model_validator(mode="after")
    def validate_reservation_cost(self) -> NoveltyWebSearchReservation:
        expected_rate = novelty_web_tool_rate_micro_usd(self.rate_card)
        if self.tool_rate_micro_usd != expected_rate:
            raise ValueError("novelty web reservation rate does not match its fixed rate card")
        expected_spend = self.tool_rate_micro_usd * self.reserved_web_tool_uses
        if self.reserved_tool_spend_micro_usd != expected_spend:
            raise ValueError("novelty web reservation spend must equal rate times reserved uses")
        return self


class NoveltyWebSearchReceipt(_NoveltyWebPersistedModel):
    """Immutable, self-contained record of a completed bounded model-side web search."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "novelty_web_search_receipt/v1"
    receipt_id: str
    reservation_id: str
    run_id: str
    question_family_id: str
    variant_id: str
    question_seed_id: str
    question_digest: str
    candidate_input_digest: str
    request_digest: str
    config_digest: str
    prompt_version: str
    prompt_digest: str
    provider_id: str
    model_id: str
    rate_card: NoveltyWebToolRateCard
    tool_rate_micro_usd: int = Field(ge=1)
    reserved_web_tool_uses: int = Field(ge=1)
    tool_name: str
    tool_version: str
    requested_max_web_searches: int = Field(ge=1)
    search_cutoff: str
    requested_at: datetime
    completed_at: datetime
    actions: list[NoveltyWebSearchAction] = Field(default_factory=list, max_length=64)
    sources: list[NoveltyWebSearchSource] = Field(default_factory=list, max_length=128)
    # ``None`` is an honest "vendor omitted it" state; an empty list is a provider-reported empty
    # filter set.  The host must not infer a filter from its own prompt or configuration.
    reported_filters: list[str] | None = None
    usage: NoveltyWebToolUsage = Field(default_factory=NoveltyWebToolUsage)
    response_digest: str
    leads: list[WebFoundPriorLead] = Field(default_factory=list, max_length=8)
    exclusions: list[NoveltyWebGroundingExclusion] = Field(default_factory=list, max_length=128)

    @field_validator(
        "receipt_id",
        "reservation_id",
        "run_id",
        "question_family_id",
        "variant_id",
        "question_seed_id",
        "prompt_version",
        "provider_id",
        "model_id",
        "tool_name",
        "tool_version",
        "search_cutoff",
    )
    @classmethod
    def require_receipt_identity(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("novelty web receipt identity fields must be non-empty")
        return normalized

    @field_validator(
        "question_digest",
        "candidate_input_digest",
        "request_digest",
        "config_digest",
        "prompt_digest",
        "response_digest",
    )
    @classmethod
    def require_receipt_digest(cls, value: str) -> str:
        return _require_sha256(value, field_name="novelty web receipt digest")

    @model_validator(mode="after")
    def validate_completed_receipt(self) -> NoveltyWebSearchReceipt:
        if self.tool_rate_micro_usd != novelty_web_tool_rate_micro_usd(self.rate_card):
            raise ValueError("novelty web receipt rate does not match its fixed rate card")
        if self.requested_max_web_searches > self.reserved_web_tool_uses:
            raise ValueError("novelty web receipt requested more searches than its reservation")
        action_count = len(self.actions)
        if not action_count:
            raise ValueError("completed novelty web receipt requires a direct search action trace")
        if action_count > self.reserved_web_tool_uses:
            raise ValueError("novelty web receipt action count exceeds its reservation")
        if action_count > self.requested_max_web_searches:
            raise ValueError("novelty web receipt action count exceeds its requested maximum")
        usage = self.usage.provider_reported_search_requests
        if usage is not None:
            if usage > self.reserved_web_tool_uses:
                raise ValueError("novelty web receipt usage exceeds its reservation")
            if usage > self.requested_max_web_searches:
                raise ValueError("novelty web receipt usage exceeds its requested maximum")
            if usage != action_count:
                raise ValueError(
                    "novelty web receipt action trace conflicts with reported tool usage"
                )
        # ``requested_at`` is host time while a vendor may report/echo a differently clocked
        # completion timestamp.  The journal records its host-observed response cutoff; a schema
        # must not turn harmless clock skew into an uncertain, permanently unrepeatable call.

        action_ids = [action.action_id for action in self.actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("novelty web receipt contains duplicate action ids")
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("novelty web receipt contains duplicate source ids")
        source_by_id = {source.source_id: source for source in self.sources}
        for source in self.sources:
            if source.action_id and source.action_id not in action_ids:
                raise ValueError("novelty web source references an unknown action")
        lead_ids = [lead.lead_id for lead in self.leads]
        if len(lead_ids) != len(set(lead_ids)):
            raise ValueError("novelty web receipt contains duplicate lead ids")
        for lead in self.leads:
            if lead.receipt_id != self.receipt_id:
                raise ValueError("novelty web lead must bind to its containing receipt")
            bound_source = source_by_id.get(lead.source_id)
            if bound_source is None:
                raise ValueError("novelty web lead references an unknown receipt source")
            if lead.source_digest != bound_source.source_digest:
                raise ValueError("novelty web lead source digest does not match receipt source")
            if lead.locator and bound_source.locator and lead.locator != bound_source.locator:
                raise ValueError("novelty web lead locator does not match receipt source")
        exclusion_ids = [exclusion.exclusion_id for exclusion in self.exclusions]
        if len(exclusion_ids) != len(set(exclusion_ids)):
            raise ValueError("novelty web receipt contains duplicate exclusion ids")
        for exclusion in self.exclusions:
            if exclusion.receipt_id and exclusion.receipt_id != self.receipt_id:
                raise ValueError("novelty web exclusion must bind to its containing receipt")
            if exclusion.source_id and exclusion.source_id not in source_by_id:
                raise ValueError("novelty web exclusion references an unknown receipt source")
        return self


class NoveltyWebLeadResolution(_NoveltyWebPersistedModel):
    """One bounded deterministic DOI/title reconciliation for one quarantined web lead."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "novelty_web_lead_resolution/v1"
    resolution_id: str
    receipt_id: str
    lead_id: str
    status: NoveltyWebLeadResolutionStatus
    method: NoveltyWebLeadResolutionMethod
    canonical_source_record_id: str = ""
    canonical_prior: NoveltyPriorRecord | None = None
    canonical_prior_snapshot_digest: str = ""
    deterministic_provider_id: str = ""
    deterministic_query_digest: str = ""
    deterministic_response_digest: str = ""
    # A finite exception/validation class only; never raw provider text or a URL.
    failure_class: str = Field(default="", max_length=128)
    rationale: str = Field(default="", max_length=2_000)
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("resolution_id", "receipt_id", "lead_id")
    @classmethod
    def require_resolution_identity(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("novelty web lead resolution identity fields must be non-empty")
        return normalized

    @field_validator(
        "canonical_prior_snapshot_digest",
        "deterministic_query_digest",
        "deterministic_response_digest",
    )
    @classmethod
    def validate_optional_resolution_digest(cls, value: str) -> str:
        normalized = value.strip().lower()
        return "" if not normalized else _require_sha256(normalized, field_name="resolution digest")

    @field_validator("failure_class")
    @classmethod
    def validate_failure_class(cls, value: str) -> str:
        normalized = value.strip()
        if normalized and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,127}", normalized) is None:
            raise ValueError("web lead resolution failure_class must be a finite safe identifier")
        return normalized

    @model_validator(mode="after")
    def validate_resolution_authority(self) -> NoveltyWebLeadResolution:
        attempted = self.method != NoveltyWebLeadResolutionMethod.NOT_ATTEMPTED
        if self.status == NoveltyWebLeadResolutionStatus.RESOLVED:
            if (
                not attempted
                or not self.canonical_source_record_id.strip()
                or self.canonical_prior is None
                or not self.canonical_prior_snapshot_digest
            ):
                raise ValueError(
                    "resolved web lead requires a reconciliation method and canonical prior snapshot"
                )
            if self.canonical_prior.source_record_id != self.canonical_source_record_id:
                raise ValueError(
                    "resolved web lead canonical record id must match its prior snapshot"
                )
            if self.canonical_prior_snapshot_digest != stable_hash(
                self.canonical_prior.model_dump(mode="json")
            ):
                raise ValueError("resolved web lead canonical prior snapshot digest does not match")
            if self.canonical_prior.evidence_origin != NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED:
                raise ValueError("resolved web lead prior snapshot must carry web-lead provenance")
            if (
                self.canonical_prior.web_receipt_id != self.receipt_id
                or self.canonical_prior.web_lead_id != self.lead_id
                or self.canonical_prior.web_resolution_id != self.resolution_id
            ):
                raise ValueError(
                    "resolved web lead prior snapshot provenance does not bind resolution"
                )
        elif (
            self.canonical_source_record_id
            or self.canonical_prior is not None
            or self.canonical_prior_snapshot_digest
        ):
            raise ValueError("unresolved web lead must not claim a canonical scholarly record")
        if self.status in {
            NoveltyWebLeadResolutionStatus.RESOLVED,
            NoveltyWebLeadResolutionStatus.UNRESOLVED,
        }:
            if not attempted:
                raise ValueError("completed web lead reconciliation requires an attempted method")
            if not self.deterministic_provider_id.strip():
                raise ValueError(
                    "attempted web lead reconciliation requires a deterministic provider"
                )
            if not self.deterministic_query_digest or not self.deterministic_response_digest:
                raise ValueError(
                    "attempted web lead reconciliation requires request/response digests"
                )
            if self.failure_class:
                raise ValueError(
                    "successful reconciliation terminal must not carry a failure class"
                )
        elif self.status == NoveltyWebLeadResolutionStatus.ERROR:
            if not attempted or not self.deterministic_provider_id.strip():
                raise ValueError("resolution error requires an attempted deterministic provider")
            if not self.deterministic_query_digest:
                raise ValueError("resolution error requires the deterministic request digest")
            if not self.failure_class.strip():
                raise ValueError("resolution error requires a finite failure class")
        elif self.status == NoveltyWebLeadResolutionStatus.INVALID_INPUT:
            if not attempted:
                raise ValueError(
                    "invalid web lead input must record its selected reconciliation route"
                )
            if not self.deterministic_provider_id.strip() or not self.deterministic_query_digest:
                raise ValueError("invalid web lead input requires deterministic route identity")
            if not self.failure_class.strip():
                raise ValueError("invalid web lead input requires a finite failure class")
            if self.deterministic_response_digest:
                raise ValueError("invalid web lead input must not claim a provider response")
        elif self.status == NoveltyWebLeadResolutionStatus.UNAVAILABLE:
            if attempted:
                raise ValueError("unavailable web lead must not claim a reconciliation attempt")
            if (
                self.deterministic_provider_id
                or self.deterministic_query_digest
                or self.deterministic_response_digest
            ):
                raise ValueError(
                    "unavailable web lead must not carry deterministic query/response data"
                )
        else:  # defensive finite enum exhaustiveness
            raise ValueError("unsupported web lead resolution status")
        return self


class NoveltyWebLeadResolutionReservation(_NoveltyWebPersistedModel):
    """Immutable pre-call reservation for one deterministic scholarly reconciliation.

    A web lead may make at most one DOI or title lookup.  This record is deliberately separate
    from the model-side search reservation: the web tool has a fee cap, while the reconciliation
    has an exactly-once/replay boundary.  If a process stops after this reservation and before its
    terminal resolution is durably written, a later run must close the lead unavailable rather
    than make the request again.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "novelty_web_lead_resolution_reservation/v1"
    reservation_id: str
    resolution_id: str
    receipt_id: str
    lead_id: str
    method: NoveltyWebLeadResolutionMethod
    deterministic_provider_id: str
    deterministic_query_digest: str
    reserved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "reservation_id",
        "resolution_id",
        "receipt_id",
        "lead_id",
        "deterministic_provider_id",
    )
    @classmethod
    def require_resolution_reservation_identity(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(
                "web lead reconciliation reservation identity fields must be non-empty"
            )
        return normalized

    @field_validator("deterministic_query_digest")
    @classmethod
    def require_resolution_reservation_digest(cls, value: str) -> str:
        return _require_sha256(value, field_name="web lead reconciliation reservation digest")

    @model_validator(mode="after")
    def require_selected_reconciliation_method(self) -> NoveltyWebLeadResolutionReservation:
        if self.method == NoveltyWebLeadResolutionMethod.NOT_ATTEMPTED:
            raise ValueError(
                "web lead reconciliation reservation requires a selected lookup method"
            )
        return self


class NoveltySearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_id: str
    focus: NoveltyQueryFocus
    query: str
    query_digest: str

    @field_validator("query_id", "query")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("novelty search query fields must be non-empty")
        return value

    @field_validator("query_digest")
    @classmethod
    def require_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("query_digest must be sha256 hex")
        return value


class NoveltySearchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "novelty_search_plan/v1"
    search_plan_id: str
    question_family_id: str
    variant_id: str
    question_seed_id: str
    question_digest: str
    search_cutoff: str
    required_provider_lanes: list[str] = Field(default_factory=list)
    queries: list[NoveltySearchQuery] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_plan(self) -> NoveltySearchPlan:
        if len(self.required_provider_lanes) < 2:
            raise ValueError("serious novelty search requires at least two provider lanes")
        if len(self.required_provider_lanes) != len(set(self.required_provider_lanes)):
            raise ValueError("novelty provider lanes must be unique")
        if len(self.queries) < 3:
            raise ValueError("novelty search plan requires at least three query formulations")
        if len({query.query_id for query in self.queries}) != len(self.queries):
            raise ValueError("novelty search query ids must be unique")
        return self


class NoveltyProviderAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_id: str
    status: NoveltyProviderAttemptStatus
    lane: NoveltyEvidenceLane = NoveltyEvidenceLane.DETERMINISTIC_SCHOLARLY
    query_ids: list[str] = Field(default_factory=list)
    response_digests: dict[str, str] = Field(default_factory=dict)
    candidate_count: int = Field(default=0, ge=0)
    error_class: str = ""


class NoveltyPriorRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    title: str
    year: int | None = None
    doi: str = ""
    url: str = ""
    providers: list[str] = Field(default_factory=list)
    query_ids: list[str] = Field(default_factory=list)
    evidence_basis: NoveltyEvidenceBasis
    scholarly_identity: NoveltyScholarlyIdentity
    abstract_or_excerpt: str = ""
    evidence_digest: str
    retrieval_scores: dict[str, float] = Field(default_factory=dict)
    #: Why this record holds its slot.  ``retrieval_scores`` is a token-overlap number that
    #: saturates -- 458 of the 505 provider scores in run 20260806T190138Z-2249f35e were exactly
    #: 1.0 -- so on its own it decided nothing and the list fell back to alphabetical order.  These
    #: two record the ranked judgement the indexes themselves made: ``provider_best_rank`` is the
    #: best (lowest) page position this record reached on any of the variant's queries per
    #: provider, and ``rank_fusion_score`` is the reciprocal-rank sum across every query/provider
    #: page that returned it, which is what the ordering actually breaks ties on.
    provider_best_rank: dict[str, int] = Field(default_factory=dict)
    rank_fusion_score: float = 0.0
    # Default retains every N-1 artifact.  A web-discovered source only gains this record shape
    # after one deterministic reconciliation, and carries the immutable receipt/lead/resolution
    # chain needed for offline replay.
    evidence_origin: NoveltyPriorEvidenceOrigin = NoveltyPriorEvidenceOrigin.DETERMINISTIC
    web_receipt_id: str = ""
    web_lead_id: str = ""
    web_resolution_id: str = ""

    @model_validator(mode="after")
    def validate_record(self) -> NoveltyPriorRecord:
        if not self.source_record_id.strip() or not self.title.strip():
            raise ValueError("novelty prior records require identity and title")
        if len(self.evidence_digest) != 64:
            raise ValueError("novelty prior evidence_digest must be sha256 hex")
        if self.evidence_basis != NoveltyEvidenceBasis.TITLE_ONLY and not self.abstract_or_excerpt:
            raise ValueError("content-bearing novelty prior requires an abstract or excerpt")
        if not self.providers or not self.query_ids:
            raise ValueError("novelty prior records require provider and query provenance")
        web_links = (self.web_receipt_id, self.web_lead_id, self.web_resolution_id)
        if self.evidence_origin == NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED:
            if not all(value.strip() for value in web_links):
                raise ValueError(
                    "web-resolved novelty prior requires receipt, lead, and resolution links"
                )
        elif any(value.strip() for value in web_links):
            raise ValueError("deterministic novelty prior must not carry web-lead links")
        return self


class NoveltyEvidenceExclusion(BaseModel):
    """A secret-free record of untrusted prior text withheld before model review."""

    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    reason: NoveltyEvidenceExclusionReason
    content_digest: str

    @field_validator("source_record_id")
    @classmethod
    def require_source_record_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("novelty evidence exclusion requires a source_record_id")
        return value

    @field_validator("content_digest")
    @classmethod
    def require_content_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("novelty evidence exclusion content_digest must be sha256 hex")
        return value


class NoveltyEvidencePack(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "novelty_evidence_pack/v1"
    evidence_pack_id: str
    search_plan_id: str
    question_family_id: str
    variant_id: str
    question_seed_id: str
    question_digest: str
    search_cutoff: str
    provider_attempts: list[NoveltyProviderAttempt] = Field(default_factory=list)
    priors: list[NoveltyPriorRecord] = Field(default_factory=list)
    exclusions: list[NoveltyEvidenceExclusion] = Field(default_factory=list)
    # The immutable N-2 receipt is the source of web leads/exclusions.  Keep compact links here so
    # the existing evidence pack can be replayed without duplicating untrusted web metadata.
    web_receipt_ids: list[str] = Field(default_factory=list)
    web_resolution_ids: list[str] = Field(default_factory=list)
    web_exclusion_ids: list[str] = Field(default_factory=list)
    evidence_adequate_for_review: bool = False
    insufficiency_reasons: list[str] = Field(default_factory=list)
    # A bounded, host-authored note that narrows what this pack covers WITHOUT deciding that it is
    # inadequate. The supplementary web-discovery lane belongs here, not in
    # ``insufficiency_reasons``: a lane that ran and resolved nothing used to yield an adequate
    # pack while a lane that crashed and resolved nothing yielded an inadequate one, on
    # byte-identical reviewer-visible evidence -- so the old placement let an infrastructure
    # condition make the scientific call. Measured over the live corpus, that placement left the
    # judge uninvoked on 29 of 137 variants, every one of which had two successful scholarly
    # lanes, 20 priors, and 3-14 abstract-bearing priors.
    scope_caveats: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_evidence(self) -> NoveltyEvidencePack:
        providers = [attempt.provider_id for attempt in self.provider_attempts]
        if len(providers) != len(set(providers)):
            raise ValueError("novelty evidence pack contains duplicate provider attempts")
        excluded_source_ids = [item.source_record_id for item in self.exclusions]
        if len(excluded_source_ids) != len(set(excluded_source_ids)):
            raise ValueError("novelty evidence pack contains duplicate excluded source ids")
        if len(self.web_receipt_ids) != len(set(self.web_receipt_ids)):
            raise ValueError("novelty evidence pack contains duplicate web receipt ids")
        if len(self.web_resolution_ids) != len(set(self.web_resolution_ids)):
            raise ValueError("novelty evidence pack contains duplicate web resolution ids")
        if len(self.web_exclusion_ids) != len(set(self.web_exclusion_ids)):
            raise ValueError("novelty evidence pack contains duplicate web exclusion ids")
        prior_source_ids = {prior.source_record_id for prior in self.priors}
        if prior_source_ids.intersection(excluded_source_ids):
            raise ValueError("a novelty prior cannot be both reviewed and excluded")
        if self.evidence_adequate_for_review:
            successful = {
                attempt.provider_id
                for attempt in self.provider_attempts
                if (
                    attempt.status == NoveltyProviderAttemptStatus.SUCCEEDED
                    and attempt.lane == NoveltyEvidenceLane.DETERMINISTIC_SCHOLARLY
                )
            }
            resolved_web_priors = [
                prior
                for prior in self.priors
                if prior.evidence_origin == NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED
            ]
            for prior in resolved_web_priors:
                if (
                    prior.web_receipt_id not in self.web_receipt_ids
                    or prior.web_resolution_id not in self.web_resolution_ids
                ):
                    raise ValueError(
                        "web-resolved novelty prior must link to this pack's receipt and resolution"
                    )
            # D8 permits exactly one deterministically unavailable lane to be replaced by one
            # resolved (not raw/unresolved) web lead.  Two web leads may never substitute for both
            # ordinary scholarly lanes.
            regular_two_lane = len(successful) >= 2
            one_lane_plus_resolved_web = len(successful) == 1 and bool(resolved_web_priors)
            if not (regular_two_lane or one_lane_plus_resolved_web):
                raise ValueError(
                    "adequate novelty evidence requires two successful lanes or one lane plus "
                    "a resolved web canonical prior"
                )
            if not any(
                prior.evidence_basis != NoveltyEvidenceBasis.TITLE_ONLY for prior in self.priors
            ):
                raise ValueError("adequate novelty evidence requires content-bearing prior records")
            if self.insufficiency_reasons:
                raise ValueError("adequate novelty evidence cannot carry insufficiency reasons")
        elif not self.insufficiency_reasons:
            raise ValueError("inadequate novelty evidence requires explicit reasons")
        return self


class NoveltyCitationBinding(BaseModel):
    """The exact persisted prior bytes a reviewer comparison relies on."""

    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    evidence_digest: str

    @field_validator("source_record_id")
    @classmethod
    def require_source_record_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("novelty citation binding requires a source_record_id")
        return value

    @field_validator("evidence_digest")
    @classmethod
    def require_evidence_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("novelty citation binding evidence_digest must be sha256 hex")
        return value


class NoveltyPriorComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_record_id: str
    citation_binding: NoveltyCitationBinding
    central_phenomenon_overlap: str
    theoretical_tension_overlap: str
    target_contrast_overlap: str
    discriminating_observation_overlap: str
    outcome_meaning_overlap: str
    substantive_delta: str
    directly_answers_question: bool = False

    @model_validator(mode="after")
    def validate_citation_binding(self) -> NoveltyPriorComparison:
        if self.citation_binding.source_record_id != self.source_record_id:
            raise ValueError("novelty comparison citation binding must match its source_record_id")
        return self


# D6 bounds on the judge free-text that reaches the questioner's revision prompt.
NOVELTY_RATIONALE_MAX_CHARS = 4_000
NOVELTY_DISTINCTION_MAX_ITEMS = 12
NOVELTY_DISTINCTION_ITEM_MAX_CHARS = 500


class NoveltyReplyCompleteness(StrEnum):
    """How much of the reviewer's reply survived, as a HOST observation about the transport.

    Deliberately NOT a `NoveltyVerdict` member. `NoveltyReviewModelOutput.verdict` is typed
    `NoveltyVerdict`, so anything added there becomes a value the reviewer can SELECT -- and
    `gate_outcome.py` already documents why that is wrong, omitting `infrastructure_failure` from
    `GateModelDecision` so a reviewer model can never claim an infra failure to dodge a scientific
    verdict. The novelty vocabulary stays purely scientific; completeness lives here, where the model
    never sees it.
    """

    #: The reviewer answered in full.
    COMPLETE = "complete"
    #: The reply was cut mid-JSON and a whole-field prefix was recovered. On the 2026-07-31 leg a
    #: biosecurity classifier fired on stratospheric wave-forcing reasoning and cut replies off
    #: after the verdict and rationale were already written; the run discarded 4,660 billed output
    #: tokens of correct science and filed it as thin literature.
    SALVAGED_PREFIX = "salvaged_prefix"
    #: Nothing usable arrived. NOT a scientific finding about the literature.
    NOT_REVIEWED = "not_reviewed"


class NoveltyReviewSalvage(BaseModel):
    """What a cut-off reply yielded, recorded whether or not it was acted on.

    Rule 12 says preserve useful partials, so a recovered rejection is kept as evidence for a retry,
    for shepherd mode, and for a human -- but ``adopted`` stays false and nothing downstream reads
    the verdict from here. Only a digest of the reply is stored, never its text: the raw bytes are
    model-authored prose and belong in the operator-gated capture, not in a persisted artifact.
    """

    model_config = ConfigDict(extra="forbid")

    recovered_verdict: NoveltyVerdict
    adopted: bool
    received_fields: list[str] = Field(default_factory=list)
    truncated_field: str = ""
    reply_sha256: str = ""
    reply_chars: int = Field(default=0, ge=0)


class VariantNoveltyAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "variant_novelty_assessment/v2"
    assessment_id: str
    question_family_id: str
    variant_id: str
    question_seed_id: str
    question_digest: str
    evidence_pack_id: str
    evidence_pack_digest: str
    verdict: NoveltyVerdict
    evidence_adequate: bool
    # D6 hard ceilings: this judge free-text reaches the questioner's revision prompt, so it is
    # a bounded injection surface. The live path truncates to these caps before construction
    # (degrade, never crash); the caps also reject a hand-forged over-long artifact at load.
    rationale: str = Field(max_length=NOVELTY_RATIONALE_MAX_CHARS)
    comparisons: list[NoveltyPriorComparison] = Field(default_factory=list)
    distinction_requirements: list[str] = Field(
        default_factory=list, max_length=NOVELTY_DISTINCTION_MAX_ITEMS
    )
    reviewer_provider_id: str
    reviewer_prompt_version: str
    reviewer_input_digest: str
    search_cutoff: str
    # Additive receipt links keep the reviewer judgment auditably tied to the N-2 discovery path.
    web_receipt_ids: list[str] = Field(default_factory=list)
    web_resolution_ids: list[str] = Field(default_factory=list)
    # Host observations about the transport, defaulted so every existing artifact loads unchanged.
    reply_completeness: NoveltyReplyCompleteness = NoveltyReplyCompleteness.COMPLETE
    salvage: NoveltyReviewSalvage | None = None

    @field_validator("distinction_requirements")
    @classmethod
    def _bound_distinction_items(cls, value: list[str]) -> list[str]:
        for item in value:
            if len(item) > NOVELTY_DISTINCTION_ITEM_MAX_CHARS:
                raise ValueError(
                    "novelty distinction requirement exceeds the per-item character bound"
                )
        return value

    @model_validator(mode="after")
    def validate_assessment(self) -> VariantNoveltyAssessment:
        # The authority line, enforced at LOAD as well as at construction so a hand-forged artifact
        # cannot smuggle a salvaged rejection past it. A salvaged verdict may be adopted only in the
        # direction that closes nothing: an admit is non-terminal and still faces the shortlist, the
        # owner/planner dialogue, and the independent plan reviewer, so a wrong salvage costs one
        # visible wasted branch. A rejection is terminal and unreviewable -- deleting a question on a
        # comparison table a classifier cut off is not recoverable and not auditable.
        if self.salvage is not None and self.salvage.adopted:
            if self.reply_completeness is not NoveltyReplyCompleteness.SALVAGED_PREFIX:
                raise ValueError("an adopted salvage must be recorded as a salvaged prefix")
            if self.salvage.recovered_verdict is not NoveltyVerdict.NO_DIRECT_RECAP_FOUND_IN_SCOPE:
                raise ValueError(
                    "a salvaged verdict may never remove a variant: only "
                    "no_direct_recap_found_in_scope may be adopted"
                )
            if self.verdict is not self.salvage.recovered_verdict:
                raise ValueError("an adopted salvage must be the assessment's own verdict")
        if len(self.web_receipt_ids) != len(set(self.web_receipt_ids)):
            raise ValueError("novelty assessment contains duplicate web receipt ids")
        if len(self.web_resolution_ids) != len(set(self.web_resolution_ids)):
            raise ValueError("novelty assessment contains duplicate web resolution ids")
        if self.verdict == NoveltyVerdict.INSUFFICIENT_SEARCH_EVIDENCE:
            if self.evidence_adequate:
                raise ValueError("insufficient novelty assessment cannot claim adequate evidence")
        elif not self.evidence_adequate:
            raise ValueError("scientific novelty verdicts require adequate evidence")
        if (
            self.verdict
            in {
                NoveltyVerdict.DIRECT_RECAP,
                NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED,
            }
            and not self.comparisons
        ):
            raise ValueError("recap/close-prior verdicts require source-bound comparisons")
        if self.verdict == NoveltyVerdict.DIRECT_RECAP and not any(
            comparison.directly_answers_question for comparison in self.comparisons
        ):
            raise ValueError("direct-recap verdict requires a comparison that directly answers")
        if (
            self.verdict == NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED
            and not self.distinction_requirements
        ):
            raise ValueError("close-prior verdict requires distinction requirements")
        if (
            self.verdict != NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED
            and self.distinction_requirements
        ):
            raise ValueError("distinction requirements belong only to close-prior verdicts")
        return self

    @property
    def is_admitted(self) -> bool:
        return self.verdict == NoveltyVerdict.NO_DIRECT_RECAP_FOUND_IN_SCOPE


class NoveltyRevisionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "novelty_revision_record/v1"
    revision_id: str
    question_family_id: str
    original_variant_id: str
    revised_variant_id: str
    original_question_seed_id: str
    revised_question_seed_id: str
    original_question_digest: str
    revised_question_digest: str
    source_assessment_id: str
    requirements: list[str] = Field(default_factory=list)
    cited_prior_record_ids: list[str] = Field(default_factory=list)
    intent_preservation_rationale: str
    revision_provider_id: str
    revision_prompt_version: str
    revision_input_digest: str
    recheck_assessment_id: str = ""
    novelty_recheck_completed: bool = False

    @model_validator(mode="after")
    def validate_recheck(self) -> NoveltyRevisionRecord:
        if not self.cited_prior_record_ids:
            raise ValueError("novelty revision requires cited prior record ids")
        if len(self.cited_prior_record_ids) != len(set(self.cited_prior_record_ids)):
            raise ValueError("novelty revision cited prior record ids must be unique")
        if self.novelty_recheck_completed != bool(self.recheck_assessment_id):
            raise ValueError("novelty revision recheck status must match its assessment id")
        return self


class NoveltyInfrastructureDeferralGroup(BaseModel):
    """One shared infrastructure cause and the families it deferred (D8)."""

    model_config = ConfigDict(extra="forbid")

    failure_class: str
    family_ids: list[str] = Field(min_length=1)


class NoveltyInfrastructureDeferralCollapse(BaseModel):
    """Run-level aggregation of per-family novelty infrastructure deferrals (D8).

    Each family still closes with its own honest insufficient-evidence terminal; this record
    collapses the identical-cause deferrals into one run-level view so an auditor sees "N families
    deferred by cause X" once instead of N scattered identical rationales. It never re-labels any
    family and carries only the exception CLASS (never raw provider/reviewer text).
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "novelty_infrastructure_deferral_collapse/v1"
    groups: list[NoveltyInfrastructureDeferralGroup] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate(self) -> NoveltyInfrastructureDeferralCollapse:
        classes = [group.failure_class for group in self.groups]
        if len(classes) != len(set(classes)):
            raise ValueError("deferral collapse must group each failure class exactly once")
        return self


class NoveltyVariantAdmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variant_id: str
    question_seed_id: str
    assessment_id: str
    disposition: NoveltyVariantDisposition
    revision_id: str = ""


class FamilyNoveltyAdmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "family_novelty_admission/v1"
    admission_id: str
    question_family_id: str
    source_family_digest: str
    admitted_family_digest: str = ""
    active_variant_ids: list[str] = Field(default_factory=list)
    variant_admissions: list[NoveltyVariantAdmission] = Field(default_factory=list)
    family_coherent_after_filtering: bool = False
    rationale: str

    @model_validator(mode="after")
    def validate_admission(self) -> FamilyNoveltyAdmission:
        admitted = [
            item.variant_id
            for item in self.variant_admissions
            if item.disposition == NoveltyVariantDisposition.ADMITTED
        ]
        if admitted != self.active_variant_ids:
            raise ValueError("family novelty active ids must equal admitted variant dispositions")
        if bool(self.active_variant_ids) != self.family_coherent_after_filtering:
            raise ValueError("family novelty coherence must match whether admitted variants remain")
        if self.active_variant_ids and not self.admitted_family_digest:
            raise ValueError("admitted family requires an admitted_family_digest")
        return self


# ``NoveltyWebLeadResolution`` deliberately appears before ``NoveltyPriorRecord`` so the compact
# web artifacts are grouped together.  Resolve its forward reference after all N-1 types exist.
NoveltyWebLeadResolution.model_rebuild()
