"""Durable, bounded N-2 model-side web-grounding journal.

This module deliberately owns only the unsafe boundary around a model-side web call.  It creates
an immutable reservation *before* a provider can be constructed, turns the provider's reported
trace into a narrow quarantine receipt, and reuses that receipt on resume.  It does not decide
scientific novelty and it does not perform the deterministic DOI/title reconciliation; callers
hand the returned low-authority ``WebFoundPriorLead`` objects to that next step.

The in-memory draft types below are intentionally not persisted models.  They are the small,
typed intake surface that an adapter may build from a vendor response.  The persisted artifacts
are the strict public schemas in :mod:`research_agenda_engine.schemas.novelty_admission`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType

from ...io import load_model
from ...provenance import stable_hash
from ...providers.models.web_search_provider import require_strict_novelty_web_capability
from ...schemas._r5_firewall import assert_proposal_safe_payload
from ...schemas.external_evidence import assert_secret_free_persisted_value
from ...schemas.maieusis_project_config import NoveltyWebGroundingConfig
from ...schemas.novelty_admission import (
    NoveltyWebGroundingExclusion,
    NoveltyWebGroundingExclusionReason,
    NoveltyWebLeadRightsClass,
    NoveltyWebSearchAction,
    NoveltyWebSearchReceipt,
    NoveltyWebSearchReservation,
    NoveltyWebSearchSource,
    NoveltyWebToolUsage,
    WebFoundPriorLead,
    sanitize_novelty_web_locator,
)
from ..orchestration.run_envelope import atomic_write_model

_JOURNAL_DIRECTORY = "novelty-web"
_RESERVATIONS_DIRECTORY = "reservations"
_COMPLETED_DIRECTORY = "completed"
_MAX_SAFE_METADATA_CHARS = 500
_MAX_SAFE_PROVIDER_IDENTIFIER_CHARS = 200
_MAX_SAFE_ACTIONS = 8
# A source bound protects against a runaway or hostile provider response, but it has to be
# proportional to how many searches the reservation actually permits: one web search returns on the
# order of twenty results, so three of them routinely exceed any small fixed number. A fixed 64
# rejected roughly one real scout call in four across three datasets on 2026-07-24, discarding the
# whole paid call rather than the excess. See tests/test_upd2_web_source_cap.py for the measured
# distribution that pins this.
_MAX_SAFE_SOURCES_PER_SEARCH = 40
_MAX_SAFE_SOURCES_ABSOLUTE = 512


def _max_safe_sources_for(reserved_web_tool_uses: int) -> int:
    """The source ceiling for one reservation: proportional, positive, and absolutely bounded."""

    permitted = max(1, reserved_web_tool_uses)
    return min(_MAX_SAFE_SOURCES_ABSOLUTE, permitted * _MAX_SAFE_SOURCES_PER_SEARCH)


_VALID_SHA256_HEX = frozenset("0123456789abcdef")


class NoveltyWebGroundingStatus(StrEnum):
    """The only outcomes a caller may receive from one web-grounding attempt."""

    DISABLED = "disabled"
    COMPLETED = "completed"
    REPLAYED = "replayed"
    SPEND_EXHAUSTED = "spend_exhausted"
    UNCERTAIN_NO_RETRY = "uncertain_no_retry"


class NoveltyWebGroundingIntegrityError(ValueError):
    """Persisted journal bytes are contradictory, swapped, unsafe, or otherwise untrustworthy."""


class NoveltyWebQuarantineRejection(ValueError):
    """This host rejected a provider trace, with a message this module authored itself.

    Every message raised as this type is a constant written here, never provider text, so it is
    safe to record in a diagnostic. That distinction is the whole point of the type: a bare
    ``ValueError`` from a dependency might quote a response, and must stay unrecorded.
    """


@dataclass(frozen=True)
class NoveltyWebGroundingRequest:
    """Host-owned binding for one family/variant's bounded web scout call.

    The candidate itself never enters this durable journal.  ``candidate_input_digest`` is the
    digest of the already-redacted scout input, and ``request_digest`` is derived from the full
    stable identity below.  A revised N-1 candidate naturally has a new seed/variant digest, so it
    receives its own one permitted reservation.
    """

    run_id: str
    question_family_id: str
    variant_id: str
    question_seed_id: str
    question_digest: str
    candidate_input_digest: str
    prompt_version: str
    prompt_digest: str
    provider_id: str
    model_id: str
    config_digest: str
    # The redacted candidate projection is an in-memory prompt input only.  It is deliberately
    # excluded from equality, repr, request identity and persisted reservation/receipt artifacts;
    # ``candidate_input_digest`` is its sole durable representation.
    scout_packet: Mapping[str, object] = field(
        default_factory=dict,
        repr=False,
        compare=False,
        hash=False,
    )
    requested_search_cutoff: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "run_id",
            "question_family_id",
            "variant_id",
            "question_seed_id",
            "prompt_version",
            "provider_id",
            "model_id",
        ):
            value = getattr(self, field_name)
            if not _safe_identifier(value):
                raise ValueError(
                    f"novelty web request {field_name} must be a safe non-empty identifier"
                )
        for field_name in (
            "question_digest",
            "candidate_input_digest",
            "prompt_digest",
            "config_digest",
        ):
            _require_sha256(getattr(self, field_name), field_name=field_name)
        frozen_packet = _freeze_scout_packet(self.scout_packet)
        try:
            assert_secret_free_persisted_value(frozen_packet, path="novelty_web_scout_packet")
            assert_proposal_safe_payload(frozen_packet, context="novelty_web_scout_packet")
        except ValueError as exc:
            raise NoveltyWebQuarantineRejection(
                "novelty web scout packet crosses the proposal firewall"
            ) from exc
        if stable_hash(_thaw_scout_packet(frozen_packet)) != self.candidate_input_digest:
            raise NoveltyWebQuarantineRejection(
                "candidate_input_digest must bind the redacted scout packet exactly"
            )
        object.__setattr__(self, "scout_packet", frozen_packet)
        if self.requested_search_cutoff:
            try:
                object.__setattr__(
                    self,
                    "requested_search_cutoff",
                    _normalized_safe_metadata(self.requested_search_cutoff, max_chars=80),
                )
            except ValueError as exc:
                raise NoveltyWebQuarantineRejection(
                    "requested_search_cutoff must be bounded safe metadata"
                ) from exc

    @property
    def request_digest(self) -> str:
        """Stable identity used for the immutable reservation and replay binding."""

        return _request_digest(
            run_id=self.run_id,
            question_family_id=self.question_family_id,
            variant_id=self.variant_id,
            question_seed_id=self.question_seed_id,
            question_digest=self.question_digest,
            candidate_input_digest=self.candidate_input_digest,
            prompt_version=self.prompt_version,
            prompt_digest=self.prompt_digest,
            provider_id=self.provider_id,
            model_id=self.model_id,
            config_digest=self.config_digest,
            requested_search_cutoff=self.requested_search_cutoff,
        )

    @property
    def scout_packet_payload(self) -> dict[str, object]:
        """A fresh mutable projection for the adapter to serialize into the scout prompt."""

        return _thaw_scout_packet(self.scout_packet)


@dataclass(frozen=True)
class NoveltyWebActionDraft:
    """One provider-reported search action before host quarantine."""

    action_type: str
    query: str
    provider_action_id: str
    # ``None`` means the provider did not report a count.  The journal must not replace that with
    # a host-derived value because a receipt distinguishes unknown from provider-reported zero.
    reported_result_count: int | None
    # ``None`` means the vendor omitted filters; an empty tuple means it explicitly reported none.
    reported_filters: tuple[str, ...] | None = None


@dataclass(frozen=True)
class NoveltyWebSourceDraft:
    """One provider-reported source before host URL/title quarantine.

    ``host_derived_source_binding_id`` is an explicitly host-owned structural handle for a vendor
    source result that has no provider-issued source identifier.  It is only for the within-receipt
    URL binding; it carries no source authority and is never presented as provider telemetry.
    """

    locator: str
    title: str
    provider_source_id: str
    provider_action_id: str
    host_derived_source_binding_id: str = ""

    @property
    def source_binding_id(self) -> str:
        """Return the one permitted opaque source-binding handle, or an empty invalid handle."""

        if self.provider_source_id and self.host_derived_source_binding_id:
            return ""
        return self.provider_source_id or self.host_derived_source_binding_id


@dataclass(frozen=True)
class NoveltyWebLeadDraft:
    """A model-selected lead that must bind to a quarantined source by opaque handle.

    ``provider_quote`` is a deprecated intake-only compatibility field.  It comes from model
    structured output, not the vendor's action/source trace, so it is never promoted into a lead
    or receipt; the quarantine records a digest-only exclusion instead.
    """

    source_binding_id: str
    claimed_doi: str = ""
    claimed_venue: str = ""
    claimed_year: int | None = None
    provider_quote: str = field(default="", repr=False)


@dataclass(frozen=True)
class NoveltyWebUsageDraft:
    """Only vendor-reported counters; unknown values are represented as zero, never invented."""

    provider_reported_search_requests: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class NoveltyWebProviderTrace:
    """Narrow, typed provider output accepted by :class:`NoveltyWebGrounder`.

    An integration adapter owns prompt construction and structured-output parsing.  It must not
    place raw page content here.  The journal preserves only action and source metadata reported
    by the vendor.  Model-selected quote text is never provider trace material and is excluded.
    """

    provider_id: str
    model_id: str
    tool_name: str
    tool_version: str
    actions: tuple[NoveltyWebActionDraft, ...]
    sources: tuple[NoveltyWebSourceDraft, ...]
    lead_drafts: tuple[NoveltyWebLeadDraft, ...] = ()
    usage: NoveltyWebUsageDraft = NoveltyWebUsageDraft()
    # This is host-observed immediately after the provider returns.  It is the per-response
    # cutoff used by the durable receipt, rather than a stale Stage-D planning timestamp.
    completed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    # ``None`` preserves a vendor omission.  The host must not infer tool filters from the prompt.
    reported_filters: tuple[str, ...] | None = None


def _safe_failure_classification(exc: BaseException) -> str:
    """Classify a failed grounding call without quoting a single byte of provider output.

    An exception class name is host-side code identity and ``StructuredModelFailureKind`` is our
    own finite enum, so neither can carry web content into an artifact. Both are what separates an
    exhausted search ceiling from a rate limit, a timeout, or a shape fault.
    """

    kind = getattr(exc, "kind", None)
    kind_value = getattr(kind, "value", "")
    name = type(exc).__name__
    if isinstance(exc, NoveltyWebQuarantineRejection):
        # Safe by construction: this type is only ever raised with a message authored in this
        # module. Naming the rejected check is the difference between a diagnosable failure and
        # "some ValueError happened", which is where a whole live leg was lost.
        return f"{name}[{str(exc)[:200]}]"
    return f"{name}[{kind_value}]" if kind_value else name


@dataclass(frozen=True)
class NoveltyWebGroundingResult:
    """Safe result returned to N-1 after journal replay or a bounded fresh call."""

    status: NoveltyWebGroundingStatus
    reservation: NoveltyWebSearchReservation | None = None
    receipt: NoveltyWebSearchReceipt | None = None
    leads: tuple[WebFoundPriorLead, ...] = ()
    exclusions: tuple[NoveltyWebGroundingExclusion, ...] = ()
    reason: str = ""

    @property
    def can_continue_with_web_evidence(self) -> bool:
        return self.status in {
            NoveltyWebGroundingStatus.COMPLETED,
            NoveltyWebGroundingStatus.REPLAYED,
        }


@dataclass(frozen=True)
class NoveltyWebJournalPaths:
    """Exact immutable journal paths outside Stage-D's rerun-cleaned artifact roots."""

    root: Path

    @property
    def journal_root(self) -> Path:
        return self.root / "receipts" / _JOURNAL_DIRECTORY

    @property
    def reservations(self) -> Path:
        return self.journal_root / _RESERVATIONS_DIRECTORY

    @property
    def completed(self) -> Path:
        return self.journal_root / _COMPLETED_DIRECTORY

    @property
    def resolutions(self) -> Path:
        """Reserved sibling root for immutable DOI/title reconciliation artifacts.

        Resolution persistence is owned by the lead-resolution integration, but it must share the
        same non-Stage-D-cleaned journal root so a completed web call cannot be followed by an
        accidental repeat of deterministic reconciliation on resume.
        """

        return self.journal_root / "resolutions"

    def reservation_path(self, reservation_id: str) -> Path:
        return self.reservations / f"{reservation_id}.yaml"

    def completed_path(self, reservation_id: str) -> Path:
        return self.completed / f"{reservation_id}.yaml"

    def resolution_path(self, resolution_id: str) -> Path:
        return self.resolutions / f"{resolution_id}.yaml"


WebProviderFactory = Callable[[], object]
WebGroundingInvoker = Callable[[object, NoveltyWebGroundingRequest], NoveltyWebProviderTrace]


class NoveltyWebGrounder:
    """Own the no-silent-retry reservation, quarantine and receipt lifecycle.

    ``provider_factory`` is intentionally lazy.  The constructor itself cannot initialize a vendor
    client, and :meth:`ground` calls the factory only after the immutable reservation is visible and
    the permanent run-level web-tool reservation ceiling has been checked.
    """

    def __init__(
        self,
        *,
        run_root: str | Path,
        config: NoveltyWebGroundingConfig,
        provider_factory: WebProviderFactory,
        invoke: WebGroundingInvoker,
    ) -> None:
        self.paths = NoveltyWebJournalPaths(Path(run_root))
        self.config = config
        self._provider_factory = provider_factory
        self._invoke = invoke

    def ground(self, request: NoveltyWebGroundingRequest) -> NoveltyWebGroundingResult:
        """Return a replayed safe receipt or make exactly one newly reserved provider call.

        Any exception after a reservation is written leaves the reservation deliberately unmatched.
        A later invocation sees that durable ambiguity and returns ``uncertain_no_retry`` instead of
        constructing a provider or spending again.
        """

        if not self.config.enabled:
            return NoveltyWebGroundingResult(status=NoveltyWebGroundingStatus.DISABLED)
        self._validate_request_matches_config(request)

        snapshot = self._read_snapshot()
        matching_reservation = _find_exact_reservation(snapshot.reservations, request)
        same_candidate_reservations = _find_same_candidate_reservations(
            snapshot.reservations, request
        )
        receipts_by_reservation = {receipt.reservation_id: receipt for receipt in snapshot.receipts}

        if matching_reservation is not None:
            matching_receipt = receipts_by_reservation.get(matching_reservation.reservation_id)
            if matching_receipt is not None:
                self._validate_receipt_binding(matching_reservation, matching_receipt, request)
                return _replayed_result(matching_reservation, matching_receipt)

        # A previously issued call with no completed receipt is irreducibly ambiguous.  This guard
        # intentionally ignores changed prompt/config identity: changing a config cannot turn an
        # unknown billed call into permission to reissue it.
        dangling = [
            reservation
            for reservation in same_candidate_reservations
            if reservation.reservation_id not in receipts_by_reservation
        ]
        if dangling:
            return NoveltyWebGroundingResult(
                status=NoveltyWebGroundingStatus.UNCERTAIN_NO_RETRY,
                reservation=dangling[0],
                reason="unmatched_pre_call_reservation",
            )

        # A completed call for this exact candidate but a different prompt/config identity is also
        # not silently repeated inside one run.  ``-novelty-r1`` keeps its family/variant identity
        # but gets a new seed/question digest, so it is correctly a new bounded candidate instead.
        if same_candidate_reservations:
            completed = receipts_by_reservation.get(same_candidate_reservations[0].reservation_id)
            return NoveltyWebGroundingResult(
                status=NoveltyWebGroundingStatus.UNCERTAIN_NO_RETRY,
                reservation=same_candidate_reservations[0],
                receipt=completed,
                reason="existing_variant_web_identity_mismatch",
            )

        reservation = self._build_reservation(request)
        used = sum(item.reserved_tool_spend_micro_usd for item in snapshot.reservations)
        if used + reservation.reserved_tool_spend_micro_usd > (
            self.config.hard_run_tool_spend_ceiling_micro_usd
        ):
            return NoveltyWebGroundingResult(
                status=NoveltyWebGroundingStatus.SPEND_EXHAUSTED,
                reason="hard_web_tool_reservation_ceiling",
            )

        reservation_path = self.paths.reservation_path(reservation.reservation_id)
        if reservation_path.exists():
            existing = _load_reservation(reservation_path)
            if existing != reservation:
                raise NoveltyWebGroundingIntegrityError(
                    "reservation pathname is occupied by different immutable bytes"
                )
            return NoveltyWebGroundingResult(
                status=NoveltyWebGroundingStatus.UNCERTAIN_NO_RETRY,
                reservation=existing,
                reason="existing_pre_call_reservation",
            )
        atomic_write_model(reservation_path, reservation)

        try:
            provider = self._provider_factory()
            trace = self._invoke(provider, request)
            receipt = self._quarantine_trace(reservation, request, trace)
            completed_path = self.paths.completed_path(reservation.reservation_id)
            if completed_path.exists():
                # This should be unreachable in a serialized orchestrator.  It is still safer to
                # validate/replay durable bytes than overwrite them after a call.
                existing_receipt = _load_receipt(completed_path)
                self._validate_receipt_binding(reservation, existing_receipt, request)
                return _replayed_result(reservation, existing_receipt)
            atomic_write_model(completed_path, receipt)
        except NoveltyWebGroundingIntegrityError:
            raise
        except (AttributeError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
            # No raw provider exception or response text may leak into artifacts/diagnostics.  The
            # durable reservation itself is sufficient evidence for an honest no-retry terminal.
            #
            # The classification below is deliberately NOT provider text: an exception class name is
            # host-side code identity, and StructuredModelFailureKind is our own finite enum. Without
            # it every cause — an exhausted search ceiling, a rate limit, a timeout, a shape fault —
            # collapses into one indistinguishable string, which is how a six-in-ten failure rate
            # stayed undiagnosable through a whole live leg (2026-07-24).
            return NoveltyWebGroundingResult(
                status=NoveltyWebGroundingStatus.UNCERTAIN_NO_RETRY,
                reservation=reservation,
                reason=(
                    "reserved_call_did_not_publish_completed_receipt:"
                    f"{_safe_failure_classification(exc)}"
                ),
            )

        return NoveltyWebGroundingResult(
            status=NoveltyWebGroundingStatus.COMPLETED,
            reservation=reservation,
            receipt=receipt,
            leads=tuple(receipt.leads),
            exclusions=tuple(receipt.exclusions),
        )

    def _validate_request_matches_config(self, request: NoveltyWebGroundingRequest) -> None:
        # Provider factory/configuration accepts its conventional spelling, while the durable
        # request identity is deliberately canonicalized.  Compare the same canonical form so a
        # harmless ``Anthropic``/``anthropic`` spelling difference cannot strand a valid journal.
        expected_provider = self.config.scout.provider.strip().lower()
        expected_model = self.config.scout.model.strip()
        if request.provider_id != expected_provider or request.model_id != expected_model:
            raise ValueError(
                "novelty web request identity must match configured scout provider/model"
            )

    def _build_reservation(
        self, request: NoveltyWebGroundingRequest
    ) -> NoveltyWebSearchReservation:
        rate = self.config.web_tool_rate_micro_usd
        reserved_uses = self.config.max_searches_per_scout
        reservation_id = f"novelty-web-reservation-{request.request_digest[:20]}"
        return NoveltyWebSearchReservation(
            reservation_id=reservation_id,
            run_id=request.run_id,
            question_family_id=request.question_family_id,
            variant_id=request.variant_id,
            question_seed_id=request.question_seed_id,
            question_digest=request.question_digest,
            candidate_input_digest=request.candidate_input_digest,
            request_digest=request.request_digest,
            config_digest=request.config_digest,
            prompt_version=request.prompt_version,
            prompt_digest=request.prompt_digest,
            provider_id=request.provider_id,
            model_id=request.model_id,
            rate_card=self.config.rate_card,
            tool_rate_micro_usd=rate,
            reserved_web_tool_uses=reserved_uses,
            reserved_tool_spend_micro_usd=rate * reserved_uses,
            requested_search_cutoff=request.requested_search_cutoff,
        )

    def _read_snapshot(self) -> _JournalSnapshot:
        reservations = tuple(
            _load_reservation(path) for path in _journal_files(self.paths.reservations)
        )
        receipts = tuple(_load_receipt(path) for path in _journal_files(self.paths.completed))
        reservation_ids = {item.reservation_id for item in reservations}
        if len(reservation_ids) != len(reservations):
            raise NoveltyWebGroundingIntegrityError("duplicate novelty web reservation ids")
        if len({item.reservation_id for item in receipts}) != len(receipts):
            raise NoveltyWebGroundingIntegrityError("duplicate novelty web completed receipt ids")
        reservations_by_id = {item.reservation_id: item for item in reservations}
        for reservation in reservations:
            _validate_reservation_static(reservation)
        for receipt in receipts:
            matched_reservation = reservations_by_id.get(receipt.reservation_id)
            if matched_reservation is None:
                raise NoveltyWebGroundingIntegrityError(
                    "completed novelty web receipt has no matching reservation"
                )
            _validate_quarantined_receipt(receipt, reservation=matched_reservation)
        return _JournalSnapshot(reservations=reservations, receipts=receipts)

    def _quarantine_trace(
        self,
        reservation: NoveltyWebSearchReservation,
        request: NoveltyWebGroundingRequest,
        trace: NoveltyWebProviderTrace,
    ) -> NoveltyWebSearchReceipt:
        if trace.provider_id != request.provider_id or trace.model_id != request.model_id:
            raise NoveltyWebQuarantineRejection(
                "provider-reported identity does not match the reserved scout"
            )
        # The strict provider capability is a precondition of construction, but the completed
        # trace must independently attest the exact direct tool/version.  A merely printable tool
        # label cannot prove that the vendor-enforced ``max_uses`` control was actually active.
        capabilities = require_strict_novelty_web_capability(request.provider_id)
        try:
            tool_name = _normalized_safe_metadata(
                trace.tool_name, max_chars=_MAX_SAFE_PROVIDER_IDENTIFIER_CHARS
            )
            tool_version = _normalized_safe_metadata(
                trace.tool_version, max_chars=_MAX_SAFE_PROVIDER_IDENTIFIER_CHARS
            )
        except ValueError as exc:
            raise NoveltyWebQuarantineRejection(
                "provider reported unsafe web tool metadata"
            ) from exc
        if tool_name != capabilities.tool_name or tool_version != capabilities.tool_version:
            raise NoveltyWebQuarantineRejection(
                "provider trace does not attest the configured strict web tool"
            )
        if trace.completed_at.tzinfo is None:
            raise NoveltyWebQuarantineRejection(
                "provider trace completed_at must be timezone-aware"
            )
        reported_searches = trace.usage.provider_reported_search_requests
        if reported_searches is not None and reported_searches < 0:
            raise NoveltyWebQuarantineRejection(
                "provider-reported web search count cannot be negative"
            )
        if reported_searches is not None and reported_searches > reservation.reserved_web_tool_uses:
            raise NoveltyWebQuarantineRejection(
                "provider-reported web search count exceeded its hard reservation"
            )
        if len(trace.actions) > _MAX_SAFE_ACTIONS:
            raise NoveltyWebQuarantineRejection("provider reported too many web actions")
        if len(trace.sources) > _max_safe_sources_for(reservation.reserved_web_tool_uses):
            raise NoveltyWebQuarantineRejection("provider reported too many web sources")

        receipt_id = f"novelty-web-receipt-{reservation.reservation_id.removeprefix('novelty-web-reservation-')}"
        actions, action_by_provider_id = _quarantine_actions(trace.actions, receipt_id=receipt_id)
        if not actions:
            raise NoveltyWebQuarantineRejection("provider reported no safe searchable action trace")
        if len(actions) > reservation.reserved_web_tool_uses:
            raise NoveltyWebQuarantineRejection(
                "provider action trace exceeded its hard reservation"
            )
        if reported_searches is not None and reported_searches != len(actions):
            raise NoveltyWebQuarantineRejection(
                "provider action trace conflicts with reported web search usage"
            )
        sources, source_by_binding_id, exclusions = _quarantine_sources(
            trace.sources,
            receipt_id=receipt_id,
            action_by_provider_id=action_by_provider_id,
        )
        leads, lead_exclusions = _quarantine_leads(
            trace.lead_drafts,
            receipt_id=receipt_id,
            source_by_binding_id=source_by_binding_id,
            max_leads=self.config.max_leads_per_scout,
        )
        exclusions.extend(lead_exclusions)
        usage = NoveltyWebToolUsage(
            provider_reported_search_requests=_non_negative_or_none(
                trace.usage.provider_reported_search_requests,
                label="provider_reported_search_requests",
            ),
            provider_reported_input_tokens=_non_negative_or_none(
                trace.usage.input_tokens, label="input_tokens"
            ),
            provider_reported_output_tokens=_non_negative_or_none(
                trace.usage.output_tokens, label="output_tokens"
            ),
        )
        completed_at = trace.completed_at.astimezone(UTC)
        reported_filters = _safe_filters(trace.reported_filters)
        response_digest = _response_digest(
            provider_id=trace.provider_id,
            model_id=trace.model_id,
            tool_name=tool_name,
            tool_version=tool_version,
            actions=actions,
            sources=sources,
            leads=leads,
            exclusions=exclusions,
            usage=usage,
            reported_filters=reported_filters,
            completed_at=completed_at,
        )
        receipt = NoveltyWebSearchReceipt(
            receipt_id=receipt_id,
            reservation_id=reservation.reservation_id,
            run_id=reservation.run_id,
            question_family_id=reservation.question_family_id,
            variant_id=reservation.variant_id,
            question_seed_id=reservation.question_seed_id,
            question_digest=reservation.question_digest,
            candidate_input_digest=reservation.candidate_input_digest,
            request_digest=reservation.request_digest,
            config_digest=reservation.config_digest,
            prompt_version=reservation.prompt_version,
            prompt_digest=reservation.prompt_digest,
            provider_id=reservation.provider_id,
            model_id=reservation.model_id,
            rate_card=reservation.rate_card,
            tool_rate_micro_usd=reservation.tool_rate_micro_usd,
            reserved_web_tool_uses=reservation.reserved_web_tool_uses,
            tool_name=tool_name,
            tool_version=tool_version,
            requested_max_web_searches=reservation.reserved_web_tool_uses,
            search_cutoff=completed_at.date().isoformat(),
            requested_at=reservation.reserved_at,
            completed_at=completed_at,
            actions=actions,
            sources=sources,
            reported_filters=reported_filters,
            usage=usage,
            response_digest=response_digest,
            leads=leads,
            exclusions=exclusions,
        )
        _validate_quarantined_receipt(receipt, reservation=reservation, request=request)
        return receipt

    def _validate_receipt_binding(
        self,
        reservation: NoveltyWebSearchReservation,
        receipt: NoveltyWebSearchReceipt,
        request: NoveltyWebGroundingRequest,
    ) -> None:
        _validate_quarantined_receipt(receipt, reservation=reservation, request=request)


@dataclass(frozen=True)
class _JournalSnapshot:
    reservations: tuple[NoveltyWebSearchReservation, ...]
    receipts: tuple[NoveltyWebSearchReceipt, ...]


def _journal_files(directory: Path) -> Iterable[Path]:
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise NoveltyWebGroundingIntegrityError(
            "novelty web journal directory is not a real directory"
        )
    paths = tuple(sorted(directory.glob("*.yaml")))
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise NoveltyWebGroundingIntegrityError(
                "novelty web journal contains a non-regular file"
            )
    return paths


def _load_reservation(path: Path) -> NoveltyWebSearchReservation:
    try:
        reservation = load_model(path, NoveltyWebSearchReservation)
    except (OSError, TypeError, ValueError) as exc:
        raise NoveltyWebGroundingIntegrityError(
            "novelty web reservation cannot be replayed"
        ) from exc
    if path.stem != reservation.reservation_id:
        raise NoveltyWebGroundingIntegrityError(
            "reservation filename does not bind its reservation id"
        )
    return reservation


def _load_receipt(path: Path) -> NoveltyWebSearchReceipt:
    try:
        receipt = load_model(path, NoveltyWebSearchReceipt)
    except (OSError, TypeError, ValueError) as exc:
        raise NoveltyWebGroundingIntegrityError("novelty web receipt cannot be replayed") from exc
    if path.stem != receipt.reservation_id:
        raise NoveltyWebGroundingIntegrityError("receipt filename does not bind its reservation id")
    return receipt


def _find_exact_reservation(
    reservations: Iterable[NoveltyWebSearchReservation], request: NoveltyWebGroundingRequest
) -> NoveltyWebSearchReservation | None:
    expected = f"novelty-web-reservation-{request.request_digest[:20]}"
    matching = [item for item in reservations if item.reservation_id == expected]
    if len(matching) > 1:
        raise NoveltyWebGroundingIntegrityError("duplicate matching novelty web reservation")
    return matching[0] if matching else None


def _find_same_candidate_reservations(
    reservations: Iterable[NoveltyWebSearchReservation], request: NoveltyWebGroundingRequest
) -> list[NoveltyWebSearchReservation]:
    return [
        item
        for item in reservations
        if item.run_id == request.run_id
        and item.question_family_id == request.question_family_id
        and item.variant_id == request.variant_id
        and item.question_seed_id == request.question_seed_id
        and item.question_digest == request.question_digest
    ]


def _quarantine_actions(
    drafts: tuple[NoveltyWebActionDraft, ...], *, receipt_id: str
) -> tuple[list[NoveltyWebSearchAction], dict[str, str]]:
    actions: list[NoveltyWebSearchAction] = []
    action_by_provider_id: dict[str, str] = {}
    for index, draft in enumerate(drafts, start=1):
        if _canonical_direct_search_action(draft.action_type) is None:
            raise NoveltyWebQuarantineRejection("N-2 accepts only direct web search actions")
        if not _safe_identifier(draft.provider_action_id):
            raise NoveltyWebQuarantineRejection("provider action id is malformed")
        if draft.provider_action_id in action_by_provider_id:
            raise NoveltyWebQuarantineRejection("provider action ids must be unique")
        try:
            query = _normalized_safe_metadata(draft.query, max_chars=_MAX_SAFE_METADATA_CHARS)
        except ValueError as exc:
            raise NoveltyWebQuarantineRejection("provider search query is unsafe") from exc
        # This is ONE action's result count, so the per-search allowance is the right magnitude —
        # the run-level ceiling would be a far looser bound than this check intends.
        if draft.reported_result_count is not None and (
            draft.reported_result_count < 0
            or draft.reported_result_count > _MAX_SAFE_SOURCES_PER_SEARCH
        ):
            raise NoveltyWebQuarantineRejection("provider reported result count is out of bounds")
        action_id = f"web-action-{stable_hash({'receipt': receipt_id, 'provider_action_id': draft.provider_action_id, 'index': index})[:16]}"
        action = NoveltyWebSearchAction(
            action_id=action_id,
            action_type="search",
            query=query,
            provider_action_id=draft.provider_action_id,
            reported_result_count=draft.reported_result_count,
            reported_filters=_safe_filters(draft.reported_filters),
        )
        actions.append(action)
        action_by_provider_id[draft.provider_action_id] = action_id
    return actions, action_by_provider_id


def _quarantine_sources(
    drafts: tuple[NoveltyWebSourceDraft, ...],
    *,
    receipt_id: str,
    action_by_provider_id: dict[str, str],
) -> tuple[
    list[NoveltyWebSearchSource],
    dict[str, NoveltyWebSearchSource],
    list[NoveltyWebGroundingExclusion],
]:
    sources: list[NoveltyWebSearchSource] = []
    source_by_binding_id: dict[str, NoveltyWebSearchSource] = {}
    exclusions: list[NoveltyWebGroundingExclusion] = []
    for index, draft in enumerate(drafts, start=1):
        raw_digest = stable_hash(
            {
                "locator": draft.locator,
                "title": draft.title,
                "provider_source_id": draft.provider_source_id,
                "host_derived_source_binding_id": draft.host_derived_source_binding_id,
                "provider_action_id": draft.provider_action_id,
            }
        )
        source_binding_id = draft.source_binding_id
        if not _safe_identifier(source_binding_id):
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id,
                    reason="malformed_provider_metadata",
                    content_digest=raw_digest,
                )
            )
            continue
        if source_binding_id in source_by_binding_id:
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id,
                    reason="malformed_provider_metadata",
                    content_digest=raw_digest,
                )
            )
            continue
        action_id = action_by_provider_id.get(draft.provider_action_id)
        if action_id is None:
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id, reason="unbound_source", content_digest=raw_digest
                )
            )
            continue
        try:
            locator = sanitize_novelty_web_locator(draft.locator)
        except (TypeError, ValueError):
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id, reason="unsafe_locator", content_digest=raw_digest
                )
            )
            continue
        try:
            title = _normalized_safe_metadata(draft.title, max_chars=_MAX_SAFE_METADATA_CHARS)
        except ValueError:
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id, reason="proposal_firewall", content_digest=raw_digest
                )
            )
            continue
        source_id = f"web-source-{stable_hash({'receipt': receipt_id, 'source_binding_id': source_binding_id, 'locator': locator, 'title': title, 'index': index})[:16]}"
        source_digest = stable_hash(
            {
                "receipt_id": receipt_id,
                "source_id": source_id,
                "locator": locator,
                "title": title,
                "provider_source_id": draft.provider_source_id,
                "host_derived_source_binding_id": draft.host_derived_source_binding_id,
                "action_id": action_id,
            }
        )
        source = NoveltyWebSearchSource(
            source_id=source_id,
            source_digest=source_digest,
            locator=locator,
            title=title,
            provider_source_id=draft.provider_source_id,
            host_derived_source_binding_id=draft.host_derived_source_binding_id,
            action_id=action_id,
        )
        sources.append(source)
        source_by_binding_id[source_binding_id] = source
    return sources, source_by_binding_id, exclusions


def _quarantine_leads(
    drafts: tuple[NoveltyWebLeadDraft, ...],
    *,
    receipt_id: str,
    source_by_binding_id: dict[str, NoveltyWebSearchSource],
    max_leads: int,
) -> tuple[list[WebFoundPriorLead], list[NoveltyWebGroundingExclusion]]:
    leads: list[WebFoundPriorLead] = []
    exclusions: list[NoveltyWebGroundingExclusion] = []
    used_source_ids: set[str] = set()
    for draft in drafts:
        raw_digest = stable_hash(
            {
                "source_binding_id": draft.source_binding_id,
                "claimed_doi": draft.claimed_doi,
                "claimed_venue": draft.claimed_venue,
                "claimed_year": draft.claimed_year,
                "provider_quote": draft.provider_quote,
            }
        )
        source = source_by_binding_id.get(draft.source_binding_id)
        if source is None:
            if draft.provider_quote:
                exclusions.append(
                    _exclusion(
                        receipt_id=receipt_id,
                        reason="model_generated_quote",
                        content_digest=stable_hash(
                            {
                                "schema": "novelty_web_model_quote_exclusion/v1",
                                "model_generated_quote": draft.provider_quote,
                            }
                        ),
                    )
                )
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id, reason="unbound_source", content_digest=raw_digest
                )
            )
            continue
        source_id = str(source.source_id)
        if draft.provider_quote:
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id,
                    source_id=source_id,
                    reason="model_generated_quote",
                    content_digest=stable_hash(
                        {
                            "schema": "novelty_web_model_quote_exclusion/v1",
                            "model_generated_quote": draft.provider_quote,
                        }
                    ),
                )
            )
        if source_id in used_source_ids or len(leads) >= max_leads:
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id,
                    source_id=source_id,
                    reason="malformed_provider_metadata",
                    content_digest=raw_digest,
                )
            )
            continue
        doi = _safe_doi(draft.claimed_doi)
        if draft.claimed_doi and not doi:
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id,
                    source_id=source_id,
                    reason="malformed_provider_metadata",
                    content_digest=raw_digest,
                )
            )
            continue
        try:
            venue = (
                _normalized_safe_metadata(draft.claimed_venue, max_chars=_MAX_SAFE_METADATA_CHARS)
                if draft.claimed_venue
                else ""
            )
        except ValueError:
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id,
                    source_id=source_id,
                    reason="proposal_firewall",
                    content_digest=raw_digest,
                )
            )
            continue
        if draft.claimed_year is not None and not (1000 <= draft.claimed_year <= 3000):
            exclusions.append(
                _exclusion(
                    receipt_id=receipt_id,
                    source_id=source_id,
                    reason="malformed_provider_metadata",
                    content_digest=raw_digest,
                )
            )
            continue
        source_digest = str(source.source_digest)
        lead_id = f"web-lead-{stable_hash({'receipt': receipt_id, 'source_id': source_id, 'source_digest': source_digest})[:16]}"
        lead = WebFoundPriorLead(
            lead_id=lead_id,
            receipt_id=receipt_id,
            source_id=source_id,
            locator=source.locator,
            title=source.title,
            claimed_doi=doi,
            claimed_venue=venue,
            claimed_year=draft.claimed_year,
            source_digest=source_digest,
        )
        leads.append(lead)
        used_source_ids.add(source_id)
    return leads, exclusions


def _exclusion(
    *,
    receipt_id: str,
    reason: str,
    content_digest: str,
    source_id: str = "",
) -> NoveltyWebGroundingExclusion:
    return NoveltyWebGroundingExclusion(
        exclusion_id=f"web-exclusion-{stable_hash({'receipt': receipt_id, 'source_id': source_id, 'reason': reason, 'content_digest': content_digest})[:16]}",
        receipt_id=receipt_id,
        source_id=source_id,
        reason=NoveltyWebGroundingExclusionReason(reason),
        content_digest=content_digest,
    )


def _validate_quarantined_receipt(
    receipt: NoveltyWebSearchReceipt,
    *,
    reservation: NoveltyWebSearchReservation,
    request: NoveltyWebGroundingRequest | None = None,
) -> None:
    for field_name in (
        "run_id",
        "question_family_id",
        "variant_id",
        "question_seed_id",
        "question_digest",
        "candidate_input_digest",
        "request_digest",
        "config_digest",
        "prompt_version",
        "prompt_digest",
        "provider_id",
        "model_id",
        "rate_card",
        "tool_rate_micro_usd",
        "reserved_web_tool_uses",
    ):
        if getattr(receipt, field_name) != getattr(reservation, field_name):
            raise NoveltyWebGroundingIntegrityError(
                f"novelty web receipt does not match reservation field {field_name}"
            )
    if receipt.reservation_id != reservation.reservation_id:
        raise NoveltyWebGroundingIntegrityError("receipt does not bind its reservation")
    if request is not None and receipt.request_digest != request.request_digest:
        raise NoveltyWebGroundingIntegrityError("receipt does not match requested web identity")
    expected_receipt_id = (
        f"novelty-web-receipt-{reservation.reservation_id.removeprefix('novelty-web-reservation-')}"
    )
    if receipt.receipt_id != expected_receipt_id:
        raise NoveltyWebGroundingIntegrityError("receipt id does not match immutable reservation")
    try:
        capabilities = require_strict_novelty_web_capability(receipt.provider_id)
    except ValueError as exc:
        raise NoveltyWebGroundingIntegrityError(
            "receipt provider lacks strict web-search capability"
        ) from exc
    if (
        receipt.tool_name != capabilities.tool_name
        or receipt.tool_version != capabilities.tool_version
    ):
        raise NoveltyWebGroundingIntegrityError(
            "receipt does not attest the configured strict web tool"
        )
    _validate_receipt_action_usage_bounds(receipt)
    _require_sha256(receipt.response_digest, field_name="receipt response_digest")
    if receipt.response_digest != _response_digest_from_receipt(receipt):
        raise NoveltyWebGroundingIntegrityError("receipt response digest is not host-derived")
    if receipt.search_cutoff != receipt.completed_at.astimezone(UTC).date().isoformat():
        raise NoveltyWebGroundingIntegrityError(
            "receipt search cutoff is not response-time derived"
        )
    assert_secret_free_persisted_value(receipt, path="novelty_web_receipt")
    # The proposal firewall intentionally rejects artifact keys such as ``schema_version``.  Apply
    # it to every untrusted provider-derived string instead of the envelope model, so a valid typed
    # receipt is not mistaken for proposal context while replay still rechecks every raw surface.
    _validate_receipt_untrusted_strings(receipt)
    action_ids = {action.action_id for action in receipt.actions}
    if not action_ids or len(action_ids) != len(receipt.actions):
        raise NoveltyWebGroundingIntegrityError("receipt action inventory is empty or duplicated")
    source_ids = {source.source_id for source in receipt.sources}
    if len(source_ids) != len(receipt.sources):
        raise NoveltyWebGroundingIntegrityError("receipt source inventory contains duplicates")
    for source in receipt.sources:
        if source.action_id not in action_ids:
            raise NoveltyWebGroundingIntegrityError(
                "receipt source is not bound to a search action"
            )
        try:
            if sanitize_novelty_web_locator(source.locator) != source.locator:
                raise NoveltyWebGroundingIntegrityError("receipt stored an unsanitized web locator")
        except ValueError as exc:
            raise NoveltyWebGroundingIntegrityError("receipt contains unsafe web locator") from exc
    lead_ids = {lead.lead_id for lead in receipt.leads}
    if len(lead_ids) != len(receipt.leads):
        raise NoveltyWebGroundingIntegrityError("receipt contains duplicate web leads")
    for lead in receipt.leads:
        if lead.receipt_id != receipt.receipt_id or lead.source_id not in source_ids:
            raise NoveltyWebGroundingIntegrityError(
                "receipt lead does not bind to its source inventory"
            )
        source = next(source for source in receipt.sources if source.source_id == lead.source_id)
        if lead.locator != source.locator or lead.title != source.title:
            raise NoveltyWebGroundingIntegrityError(
                "receipt lead metadata does not match its source"
            )
        expected_source_digest = stable_hash(
            {
                "receipt_id": receipt.receipt_id,
                "source_id": source.source_id,
                "locator": source.locator,
                "title": source.title,
                "provider_source_id": source.provider_source_id,
                "host_derived_source_binding_id": source.host_derived_source_binding_id,
                "action_id": source.action_id,
            }
        )
        if lead.source_digest != expected_source_digest:
            raise NoveltyWebGroundingIntegrityError(
                "receipt lead source digest is not host-derived"
            )
    for exclusion in receipt.exclusions:
        if exclusion.receipt_id != receipt.receipt_id:
            raise NoveltyWebGroundingIntegrityError("receipt exclusion does not bind to receipt")
        if exclusion.source_id and exclusion.source_id not in source_ids:
            raise NoveltyWebGroundingIntegrityError(
                "receipt exclusion references an unknown source"
            )


def _validate_receipt_action_usage_bounds(receipt: NoveltyWebSearchReceipt) -> None:
    """Recheck strict direct-search accounting independently of Pydantic receipt parsing.

    A receipt can be read through a future migration or constructed in memory without ordinary
    validation, so replay must independently enforce the reservation/request cap and the vendor's
    own counter.  When that counter is absent, the complete direct-action inventory remains the
    hard accounting source; omission cannot turn extra actions into permitted spend.
    """

    reserved = receipt.reserved_web_tool_uses
    requested = receipt.requested_max_web_searches
    if (
        not isinstance(reserved, int)
        or isinstance(reserved, bool)
        or reserved < 1
        or not isinstance(requested, int)
        or isinstance(requested, bool)
        or requested < 1
    ):
        raise NoveltyWebGroundingIntegrityError("receipt has invalid direct-search usage bounds")
    if requested > reserved:
        raise NoveltyWebGroundingIntegrityError(
            "receipt requested more searches than its reservation"
        )

    action_count = len(receipt.actions)
    if not action_count:
        raise NoveltyWebGroundingIntegrityError("receipt action inventory is empty")
    if action_count > reserved:
        raise NoveltyWebGroundingIntegrityError("receipt action inventory exceeds its reservation")
    if action_count > requested:
        raise NoveltyWebGroundingIntegrityError(
            "receipt action inventory exceeds its requested maximum"
        )
    for action in receipt.actions:
        if action.action_type != "search":
            raise NoveltyWebGroundingIntegrityError(
                "receipt contains a non-canonical direct search action"
            )

    usage = receipt.usage.provider_reported_search_requests
    if usage is None:
        return
    if not isinstance(usage, int) or isinstance(usage, bool) or usage < 0:
        raise NoveltyWebGroundingIntegrityError(
            "receipt has invalid provider-reported search usage"
        )
    if usage > reserved:
        raise NoveltyWebGroundingIntegrityError("receipt reported usage exceeds its reservation")
    if usage > requested:
        raise NoveltyWebGroundingIntegrityError(
            "receipt reported usage exceeds its requested maximum"
        )
    if usage != action_count:
        raise NoveltyWebGroundingIntegrityError(
            "receipt action inventory conflicts with reported tool usage"
        )


def _validate_reservation_static(reservation: NoveltyWebSearchReservation) -> None:
    expected_request_digest = _request_digest(
        run_id=reservation.run_id,
        question_family_id=reservation.question_family_id,
        variant_id=reservation.variant_id,
        question_seed_id=reservation.question_seed_id,
        question_digest=reservation.question_digest,
        candidate_input_digest=reservation.candidate_input_digest,
        prompt_version=reservation.prompt_version,
        prompt_digest=reservation.prompt_digest,
        provider_id=reservation.provider_id,
        model_id=reservation.model_id,
        config_digest=reservation.config_digest,
        requested_search_cutoff=reservation.requested_search_cutoff,
    )
    if reservation.request_digest != expected_request_digest:
        raise NoveltyWebGroundingIntegrityError("reservation request digest is not host-derived")
    expected_reservation_id = f"novelty-web-reservation-{reservation.request_digest[:20]}"
    if reservation.reservation_id != expected_reservation_id:
        raise NoveltyWebGroundingIntegrityError("reservation id is not host-derived")
    for value, label in (
        (reservation.run_id, "run_id"),
        (reservation.question_family_id, "question_family_id"),
        (reservation.variant_id, "variant_id"),
        (reservation.question_seed_id, "question_seed_id"),
        (reservation.prompt_version, "prompt_version"),
        (reservation.provider_id, "provider_id"),
        (reservation.model_id, "model_id"),
    ):
        _require_safe_persisted_identifier(value, label=label)
    if reservation.requested_search_cutoff:
        _require_safe_persisted_metadata(
            reservation.requested_search_cutoff,
            label="requested_search_cutoff",
        )


def _request_digest(
    *,
    run_id: str,
    question_family_id: str,
    variant_id: str,
    question_seed_id: str,
    question_digest: str,
    candidate_input_digest: str,
    prompt_version: str,
    prompt_digest: str,
    provider_id: str,
    model_id: str,
    config_digest: str,
    requested_search_cutoff: str,
) -> str:
    return stable_hash(
        {
            "schema": "novelty_web_grounding_request/v1",
            "run_id": run_id,
            "question_family_id": question_family_id,
            "variant_id": variant_id,
            "question_seed_id": question_seed_id,
            "question_digest": question_digest,
            "candidate_input_digest": candidate_input_digest,
            "prompt_version": prompt_version,
            "prompt_digest": prompt_digest,
            "provider_id": provider_id,
            "model_id": model_id,
            "config_digest": config_digest,
            "requested_search_cutoff": requested_search_cutoff,
        }
    )


def _response_digest(
    *,
    provider_id: str,
    model_id: str,
    tool_name: str,
    tool_version: str,
    actions: list[NoveltyWebSearchAction],
    sources: list[NoveltyWebSearchSource],
    leads: list[WebFoundPriorLead],
    exclusions: list[NoveltyWebGroundingExclusion],
    usage: NoveltyWebToolUsage,
    reported_filters: list[str] | None,
    completed_at: datetime,
) -> str:
    return stable_hash(
        {
            "provider_id": provider_id,
            "model_id": model_id,
            "tool_name": tool_name,
            "tool_version": tool_version,
            "actions": [action.model_dump(mode="json") for action in actions],
            "sources": [source.model_dump(mode="json") for source in sources],
            "leads": [lead.model_dump(mode="json") for lead in leads],
            "exclusions": [item.model_dump(mode="json") for item in exclusions],
            "usage": usage.model_dump(mode="json"),
            "reported_filters": reported_filters,
            "completed_at": completed_at.astimezone(UTC).isoformat(),
        }
    )


def _response_digest_from_receipt(receipt: NoveltyWebSearchReceipt) -> str:
    return _response_digest(
        provider_id=receipt.provider_id,
        model_id=receipt.model_id,
        tool_name=receipt.tool_name,
        tool_version=receipt.tool_version,
        actions=receipt.actions,
        sources=receipt.sources,
        leads=receipt.leads,
        exclusions=receipt.exclusions,
        usage=receipt.usage,
        reported_filters=receipt.reported_filters,
        completed_at=receipt.completed_at,
    )


def _replayed_result(
    reservation: NoveltyWebSearchReservation, receipt: NoveltyWebSearchReceipt
) -> NoveltyWebGroundingResult:
    return NoveltyWebGroundingResult(
        status=NoveltyWebGroundingStatus.REPLAYED,
        reservation=reservation,
        receipt=receipt,
        leads=tuple(receipt.leads),
        exclusions=tuple(receipt.exclusions),
    )


def _safe_identifier(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip()
    if not normalized or len(normalized) > _MAX_SAFE_PROVIDER_IDENTIFIER_CHARS:
        return False
    if normalized != value or any(
        not character.isprintable() or character.isspace() for character in value
    ):
        return False
    try:
        assert_secret_free_persisted_value(value, path="novelty_web_identifier")
        assert_proposal_safe_payload(value, context="novelty_web_identifier")
    except ValueError:
        return False
    return True


def _safe_metadata(value: object, *, max_chars: int) -> bool:
    try:
        _normalized_safe_metadata(value, max_chars=max_chars)
    except ValueError:
        return False
    return True


def _normalized_safe_metadata(value: object, *, max_chars: int) -> str:
    if not isinstance(value, str):
        raise NoveltyWebQuarantineRejection("metadata must be text")
    normalized = " ".join(value.split())
    if (
        not normalized
        or len(normalized) > max_chars
        or any(not char.isprintable() for char in normalized)
    ):
        raise NoveltyWebQuarantineRejection("metadata is not bounded printable text")
    try:
        assert_secret_free_persisted_value(normalized, path="novelty_web_metadata")
        assert_proposal_safe_payload(normalized, context="novelty_web_metadata")
    except ValueError as exc:
        raise NoveltyWebQuarantineRejection("metadata crosses a trust boundary") from exc
    return normalized


def _safe_doi(value: object) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.strip().lower()
    if not normalized:
        return ""
    if len(normalized) > 300 or not normalized.startswith("10.") or "/" not in normalized:
        return ""
    if any(not character.isprintable() or character.isspace() for character in normalized):
        return ""
    try:
        assert_secret_free_persisted_value(normalized, path="novelty_web_claimed_doi")
        assert_proposal_safe_payload(normalized, context="novelty_web_claimed_doi")
    except ValueError:
        return ""
    return normalized


def _canonical_direct_search_action(value: object) -> str | None:
    """Map only documented direct-tool aliases to N-2's one canonical action kind."""

    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    return "search" if normalized in {"search", "web_search"} else None


def _validate_receipt_untrusted_strings(receipt: NoveltyWebSearchReceipt) -> None:
    _require_safe_persisted_metadata(receipt.tool_name, label="tool_name")
    _require_safe_persisted_metadata(receipt.tool_version, label="tool_version")
    _validate_persisted_filters(receipt.reported_filters, label="reported_filters")
    for action in receipt.actions:
        _require_safe_persisted_metadata(action.action_type, label="action_type")
        _require_safe_persisted_identifier(action.action_id, label="action_id")
        if action.provider_action_id:
            _require_safe_persisted_identifier(
                action.provider_action_id, label="provider_action_id"
            )
        if action.query:
            _require_safe_persisted_metadata(action.query, label="action_query")
        _validate_persisted_filters(action.reported_filters, label="action_filters")
    for source in receipt.sources:
        _require_safe_persisted_identifier(source.source_id, label="source_id")
        if bool(source.provider_source_id) == bool(source.host_derived_source_binding_id):
            raise NoveltyWebGroundingIntegrityError(
                "receipt source must have exactly one provider or host-derived binding identity"
            )
        if source.provider_source_id:
            _require_safe_persisted_identifier(
                source.provider_source_id, label="provider_source_id"
            )
        if source.host_derived_source_binding_id:
            _require_safe_persisted_identifier(
                source.host_derived_source_binding_id,
                label="host_derived_source_binding_id",
            )
        if source.title:
            _require_safe_persisted_metadata(source.title, label="source_title")
    for lead in receipt.leads:
        _require_safe_persisted_identifier(lead.lead_id, label="lead_id")
        if lead.provider_quote:
            raise NoveltyWebGroundingIntegrityError("receipt retains a model-generated quote")
        if lead.rights_class != NoveltyWebLeadRightsClass.METADATA_ONLY_UNVERIFIED:
            raise NoveltyWebGroundingIntegrityError("receipt assigns unsupported quote rights")
        if lead.title:
            _require_safe_persisted_metadata(lead.title, label="lead_title")
        if lead.claimed_doi:
            _require_safe_persisted_metadata(lead.claimed_doi, label="lead_doi")
        if lead.claimed_venue:
            _require_safe_persisted_metadata(lead.claimed_venue, label="lead_venue")


def _validate_persisted_filters(value: list[str] | None, *, label: str) -> None:
    if value is None:
        return
    for item in value:
        _require_safe_persisted_metadata(item, label=label)


def _require_safe_persisted_metadata(value: object, *, label: str) -> None:
    if not _safe_metadata(value, max_chars=_MAX_SAFE_METADATA_CHARS):
        raise NoveltyWebGroundingIntegrityError(f"receipt contains unsafe {label}")


def _require_safe_persisted_identifier(value: object, *, label: str) -> None:
    if not _safe_identifier(value):
        raise NoveltyWebGroundingIntegrityError(f"receipt contains unsafe {label}")


def _require_sha256(value: object, *, field_name: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in _VALID_SHA256_HEX for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase sha256 hex")


def _non_negative_or_none(value: object, *, label: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer or None")
    return value


def _safe_filters(value: tuple[str, ...] | None) -> list[str] | None:
    if value is None:
        return None
    cleaned: list[str] = []
    for item in value:
        try:
            cleaned.append(_normalized_safe_metadata(item, max_chars=_MAX_SAFE_METADATA_CHARS))
        except ValueError as exc:
            raise NoveltyWebQuarantineRejection("provider reported an unsafe web filter") from exc
    return cleaned


def _freeze_scout_packet(value: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise NoveltyWebQuarantineRejection("scout_packet must be a mapping")
    frozen = _freeze_scout_value(value)
    if not isinstance(frozen, Mapping):  # Defensive narrowing for the recursive helper.
        raise NoveltyWebQuarantineRejection("scout_packet must remain a mapping")
    return frozen


def _freeze_scout_value(value: object) -> object:
    """Make a JSON-shaped packet immutable before handing it to the provider adapter."""

    if isinstance(value, Mapping):
        frozen: dict[str, object] = {}
        for key, child in value.items():
            if not isinstance(key, str) or not _safe_identifier(key):
                raise NoveltyWebQuarantineRejection("scout packet keys must be safe identifiers")
            frozen[key] = _freeze_scout_value(child)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_scout_value(child) for child in value)
    if value is None or isinstance(value, str | int | float | bool):
        return value
    raise NoveltyWebQuarantineRejection("scout packet must contain only JSON-shaped values")


def _thaw_scout_packet(value: Mapping[str, object]) -> dict[str, object]:
    thawed = _thaw_scout_value(value)
    if not isinstance(thawed, dict):  # Defensive narrowing for the recursive helper.
        raise NoveltyWebQuarantineRejection("scout packet must remain a mapping")
    return thawed


def _thaw_scout_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _thaw_scout_value(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_thaw_scout_value(child) for child in value]
    return value
