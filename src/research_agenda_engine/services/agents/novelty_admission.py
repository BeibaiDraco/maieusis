"""Evidence-driven, model-reviewed novelty admission before shortlist and planning."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ...assets import resolve_asset
from ...io import load_model
from ...provenance import stable_hash
from ...providers.models.base import (
    ModelConfigurationError,
    StructuredModelFailureKind,
    StructuredModelProvider,
    StructuredModelProviderError,
)
from ...providers.models.web_search_provider import (
    WebSearchModelProvider,
    WebSearchResearchResult,
)
from ...schemas._r5_firewall import assert_proposal_safe_payload
from ...schemas.external_evidence import assert_secret_free_persisted_value
from ...schemas.novelty_admission import (
    NOVELTY_DISTINCTION_ITEM_MAX_CHARS,
    NOVELTY_DISTINCTION_MAX_ITEMS,
    NOVELTY_RATIONALE_MAX_CHARS,
    FamilyNoveltyAdmission,
    NoveltyEvidenceBasis,
    NoveltyEvidenceExclusion,
    NoveltyEvidenceExclusionReason,
    NoveltyEvidenceLane,
    NoveltyEvidencePack,
    NoveltyPriorComparison,
    NoveltyPriorEvidenceOrigin,
    NoveltyPriorRecord,
    NoveltyProviderAttempt,
    NoveltyProviderAttemptStatus,
    NoveltyQueryFocus,
    NoveltyReplyCompleteness,
    NoveltyReviewSalvage,
    NoveltyRevisionRecord,
    NoveltyScholarlyIdentity,
    NoveltySearchPlan,
    NoveltySearchQuery,
    NoveltyVariantAdmission,
    NoveltyVariantDisposition,
    NoveltyVerdict,
    NoveltyWebLeadResolution,
    NoveltyWebLeadResolutionMethod,
    NoveltyWebLeadResolutionReservation,
    NoveltyWebLeadResolutionStatus,
    VariantNoveltyAssessment,
    WebFoundPriorLead,
    sanitize_novelty_web_locator,
)
from ...schemas.question_family import (
    QuestionFamily,
    QuestionFamilyVariant,
    QuestionFamilyVariantDistinctionAxis,
)
from ...schemas.question_seed import QuestionSeed
from ...schemas.variant_novelty import (
    NearestPriorCandidate,
    VariantNoveltyResult,
    VariantNoveltyStatus,
)
from ..orchestration.run_envelope import atomic_write_model
from ..retrieval.novelty_sources import (
    CrossrefNoveltyLeadResolver,
    NoveltyLeadResolutionResult,
    NoveltySearchHit,
    NoveltySearchProvider,
    sanitize_novelty_query,
)
from ..retrieval.novelty_sources import (
    NoveltyLeadResolutionMethod as RetrievalLeadResolutionMethod,
)
from ..retrieval.novelty_sources import (
    NoveltyLeadResolutionStatus as RetrievalLeadResolutionStatus,
)
from .generation_mirrors import QuestionSeedModelOutput
from .novelty_web_grounding import (
    NoveltyWebActionDraft,
    NoveltyWebGrounder,
    NoveltyWebGroundingRequest,
    NoveltyWebGroundingResult,
    NoveltyWebLeadDraft,
    NoveltyWebProviderTrace,
    NoveltyWebSourceDraft,
    NoveltyWebUsageDraft,
)

NOVELTY_REVIEWER_PROMPT_VERSION = "novelty_reviewer/v3"
NOVELTY_REVISION_PROMPT_VERSION = "novelty_revision/v2"
# A schema-invalid reviewer reply is replayed within this budget before the variant is deferred.
# Mirrors STRUCTURED_OUTPUT_MAX_ATTEMPTS in the paper extractor: a malformed reply is not evidence
# about the question, and one of them used to cost a variant outright.
NOVELTY_REVIEW_MAX_ATTEMPTS = 3

NOVELTY_WEB_SCOUT_PROMPT_VERSION = "novelty_web_scout/v1"


class NoveltyVariantRejection(ValueError):
    """This host rejected one variant's model reply, with a message this module authored.

    Follows the ``NoveltyWebQuarantineRejection`` template: every message raised as this type is a
    constant written here, never provider text, so it is safe to record. The type is what lets the
    per-variant handler tell "the model answered in a shape we refuse" apart from a host invariant
    or a configuration error, which must stay hard and uncaught.
    """


class NoveltyReviewModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: NoveltyVerdict
    evidence_adequate: bool
    rationale: str
    comparisons: list[NoveltyPriorComparison] = Field(default_factory=list)
    distinction_requirements: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scientific_verdict(self) -> NoveltyReviewModelOutput:
        if self.verdict == NoveltyVerdict.INSUFFICIENT_SEARCH_EVIDENCE:
            if self.evidence_adequate:
                raise ValueError("insufficient novelty verdict cannot claim adequate evidence")
        elif not self.evidence_adequate:
            raise ValueError("scientific novelty verdict requires adequate evidence")
        if (
            self.verdict
            in {
                NoveltyVerdict.DIRECT_RECAP,
                NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED,
            }
            and not self.comparisons
        ):
            raise ValueError("recap/close-prior verdict requires comparisons")
        if self.verdict == NoveltyVerdict.DIRECT_RECAP and not any(
            comparison.directly_answers_question for comparison in self.comparisons
        ):
            raise ValueError("direct-recap verdict requires a comparison that directly answers")
        if (
            self.verdict == NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED
            and not self.distinction_requirements
        ):
            raise ValueError("close-prior verdict requires distinction requirements")
        return self


class NoveltyRevisionModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # The provider owns scientific content; code-owned ids/provenance are stamped below before the
    # strict QuestionSeed is constructed and persisted.
    revised_seed: QuestionSeedModelOutput
    variant_role: str
    # The enum, not `list[str]`: the generation mirror QuestionFamilyVariantModelOutput inherits
    # this constraint from QuestionFamilyVariant, so the provider's own JSON schema enforces it
    # there and every generated variant is valid. Hand-rolling it as free text here meant nothing
    # constrained the revision, and on 2026-07-26 a model that answered "population scope" instead
    # of "population_scope" killed a whole question family at strict construction.
    distinction_axes: list[QuestionFamilyVariantDistinctionAxis]
    distinct_from_siblings: str
    intent_preservation_rationale: str
    cited_prior_record_ids: list[str] = Field(default_factory=list)


class NoveltyWebScoutLeadModelOutput(BaseModel):
    """A low-authority model selection that still has to bind to a tool-reported source.

    The web scout cannot provide canonical scholarly evidence.  It only identifies a returned
    source URL and optional bibliographic metadata that the host will quarantine, then reconcile
    through one deterministic Crossref lookup.  It never returns a quote: the structured response
    is model-authored, while N-2 may retain only metadata actually reported by the web tool.
    """

    model_config = ConfigDict(extra="forbid")

    source_url: str
    claimed_doi: str = ""
    claimed_venue: str = ""
    claimed_year: int | None = None


class NoveltyWebScoutModelOutput(BaseModel):
    """Strict response shape for the independent, bounded web scout prompt."""

    model_config = ConfigDict(extra="forbid")

    leads: list[NoveltyWebScoutLeadModelOutput] = Field(default_factory=list, max_length=8)


class NoveltyWebLeadResolver(Protocol):
    """The one-shot deterministic resolver seam used by N-2 and hermetic tests."""

    provider_id: str

    def resolve(
        self,
        *,
        query_id: str,
        claimed_doi: str = "",
        claimed_title: str = "",
    ) -> NoveltyLeadResolutionResult: ...


@dataclass(frozen=True)
class FamilyNoveltyAdmissionResult:
    admitted_family: QuestionFamily | None
    admission: FamilyNoveltyAdmission
    search_plans: tuple[NoveltySearchPlan, ...]
    evidence_packs: tuple[NoveltyEvidencePack, ...]
    assessments: tuple[VariantNoveltyAssessment, ...]
    revisions: tuple[NoveltyRevisionRecord, ...]
    legacy_results: tuple[VariantNoveltyResult, ...]


def _truncate(text: str, limit: int) -> str:
    """Bound judge free-text to a character ceiling with a visible truncation marker (D6)."""
    if len(text) <= limit:
        return text
    marker = " …[truncated]"
    return text[: max(0, limit - len(marker))] + marker


def build_novelty_web_scout_packet(variant: QuestionFamilyVariant) -> dict[str, object]:
    """Project the minimum safe candidate material into the independent N-2 scout.

    This is intentionally narrower than both the Question Scientist packet and the N-1 judge
    packet.  In particular, it excludes self-assessed novelty, sibling distinctions, dataset
    leverage, feasibility, deterministic novelty hits, and every confirmation/result surface.
    The durable journal stores only this packet's digest, never these strings.
    """

    seed = variant.seed
    packet: dict[str, object] = {
        "candidate_question": {
            "question": seed.question,
            "scientific_tension": seed.scientific_tension,
            "why_scientifically_important": seed.why_scientifically_important,
            "discriminating_observation": seed.discriminating_observation,
            "positive_result_consequence": seed.positive_result_consequence,
            "negative_result_consequence": seed.negative_result_consequence,
            "null_result_consequence": seed.null_result_consequence,
        },
        "instructions": {
            "task": "discover_possible_prior_work_leads_only",
            "no_novelty_verdict": True,
            "no_feasibility_or_execution_claim": True,
            "source_url_must_bind_to_tool_result": True,
            "canonical_scholarly_resolution_is_host_owned": True,
        },
    }
    assert_proposal_safe_payload(packet, context="novelty web scout packet")
    return packet


def invoke_novelty_web_scout(
    provider: object,
    request: NoveltyWebGroundingRequest,
    *,
    max_web_searches: int,
    max_output_tokens: int,
) -> NoveltyWebProviderTrace:
    """Call the strict web adapter and translate only vendor-reported trace into the journal.

    The model's selected source URL is matched against the server tool's own source inventory in
    memory.  No model URL or title becomes durable until ``NoveltyWebGrounder`` performs its
    secret scan, locator stripping, and proposal firewall quarantine.  Quotes are deliberately
    not accepted from the model response because they are not vendor-reported tool telemetry.
    """

    if not isinstance(provider, WebSearchModelProvider):
        raise TypeError("N-2 novelty web scout requires a WebSearchModelProvider")
    if provider.provider_name != request.provider_id or provider.model_name != request.model_id:
        raise ValueError("constructed novelty web scout identity does not match its reservation")
    result: WebSearchResearchResult[NoveltyWebScoutModelOutput] = provider.research_structured(
        system_prompt=_load_prompt(NOVELTY_WEB_SCOUT_PROMPT_VERSION),
        user_prompt=json.dumps(request.scout_packet_payload, sort_keys=True, ensure_ascii=False),
        output_model=NoveltyWebScoutModelOutput,
        max_web_searches=max_web_searches,
        max_output_tokens=max_output_tokens,
    )
    if result.model_id != request.model_id:
        raise ValueError("novelty web scout response model does not match its reservation")

    source_locator_to_ids: dict[str, list[str]] = {}
    source_drafts: list[NoveltyWebSourceDraft] = []
    for source in result.sources:
        source_binding_id = source.provider_source_id or source.host_derived_source_binding_id
        source_drafts.append(
            NoveltyWebSourceDraft(
                locator=source.url,
                title=source.title,
                provider_source_id=source.provider_source_id,
                provider_action_id=source.provider_action_id,
                host_derived_source_binding_id=source.host_derived_source_binding_id,
            )
        )
        # Matching is ephemeral and intentionally conservative.  A malformed or signed model URL
        # cannot accidentally bind to a safe source; the journal will retain only a digest-only
        # exclusion when it sees the associated raw draft.
        try:
            safe_locator = sanitize_novelty_web_locator(source.url)
        except (TypeError, ValueError):
            continue
        if source_binding_id:
            source_locator_to_ids.setdefault(safe_locator, []).append(source_binding_id)

    lead_drafts: list[NoveltyWebLeadDraft] = []
    for lead in result.parsed.leads:
        source_binding_id = ""
        try:
            safe_locator = sanitize_novelty_web_locator(lead.source_url)
            matches = source_locator_to_ids.get(safe_locator, [])
            # Ambiguous duplicate source URLs do not get a guessed identity.  The journal records
            # a typed unbound-source exclusion instead of letting the model select a source.
            if len(matches) == 1:
                source_binding_id = matches[0]
        except (TypeError, ValueError):
            pass
        lead_drafts.append(
            NoveltyWebLeadDraft(
                source_binding_id=source_binding_id,
                claimed_doi=lead.claimed_doi,
                claimed_venue=lead.claimed_venue,
                claimed_year=lead.claimed_year,
            )
        )

    return NoveltyWebProviderTrace(
        # The journal binds the configured vendor/model separately from the adapter's richer
        # ``provider_id`` rendering (usually ``vendor:model``), so no adapter formatting leaks
        # into immutable request identity.
        provider_id=request.provider_id,
        model_id=request.model_id,
        tool_name=result.tool_name,
        tool_version=result.tool_version,
        actions=tuple(
            NoveltyWebActionDraft(
                action_type=action.action_type,
                query=action.query,
                provider_action_id=action.provider_action_id,
                reported_result_count=action.reported_result_count,
                reported_filters=action.reported_filters,
            )
            for action in result.actions
        ),
        sources=tuple(source_drafts),
        lead_drafts=tuple(lead_drafts),
        usage=NoveltyWebUsageDraft(
            provider_reported_search_requests=(result.usage.provider_reported_search_requests),
            input_tokens=result.usage.provider_reported_input_tokens,
            output_tokens=result.usage.provider_reported_output_tokens,
        ),
    )


def _build_novelty_web_grounding_request(
    family: QuestionFamily,
    variant: QuestionFamilyVariant,
    *,
    web_grounder: NoveltyWebGrounder,
    search_cutoff: str,
) -> NoveltyWebGroundingRequest:
    packet = build_novelty_web_scout_packet(variant)
    config = web_grounder.config
    prompt = _load_prompt(NOVELTY_WEB_SCOUT_PROMPT_VERSION)
    return NoveltyWebGroundingRequest(
        run_id=web_grounder.paths.root.name,
        question_family_id=family.question_family_id,
        variant_id=variant.variant_id,
        question_seed_id=variant.question_seed_id,
        question_digest=stable_hash(variant.seed),
        candidate_input_digest=stable_hash(packet),
        prompt_version=NOVELTY_WEB_SCOUT_PROMPT_VERSION,
        prompt_digest=stable_hash(prompt),
        provider_id=config.scout.provider.strip().lower(),
        model_id=config.scout.model.strip(),
        config_digest=stable_hash(config.model_dump(mode="json")),
        scout_packet=packet,
        requested_search_cutoff=search_cutoff,
    )


def _resolve_novelty_web_leads(
    grounding: NoveltyWebGroundingResult,
    *,
    web_grounder: NoveltyWebGrounder,
    resolver: NoveltyWebLeadResolver,
) -> tuple[tuple[NoveltyPriorRecord, ...], tuple[NoveltyWebLeadResolution, ...]]:
    """Resolve each quarantined web lead once, then replay immutable canonical snapshots.

    The resolution artifact lives beside the immutable web-call receipt rather than inside the
    Stage-D-cleaned corpus.  A resume therefore reads the exact prior snapshot that informed the
    reviewer; it never needs to call Crossref merely to rebuild a previous evidence pack.
    """

    receipt = grounding.receipt
    if receipt is None:
        raise ValueError("completed novelty web grounding must include a receipt")
    records: list[NoveltyPriorRecord] = []
    resolutions: list[NoveltyWebLeadResolution] = []
    for lead in receipt.leads:
        resolution = _load_or_resolve_novelty_web_lead(
            receipt_id=receipt.receipt_id,
            lead=lead,
            web_grounder=web_grounder,
            resolver=resolver,
        )
        resolutions.append(resolution)
        if resolution.status == NoveltyWebLeadResolutionStatus.RESOLVED:
            if resolution.canonical_prior is None:
                raise ValueError(
                    "resolved novelty web lead is missing its canonical prior snapshot"
                )
            records.append(resolution.canonical_prior)
    return tuple(records), tuple(resolutions)


def _load_or_resolve_novelty_web_lead(
    *,
    receipt_id: str,
    lead: WebFoundPriorLead,
    web_grounder: NoveltyWebGrounder,
    resolver: NoveltyWebLeadResolver,
) -> NoveltyWebLeadResolution:
    """Persist one terminal DOI/title reconciliation, never silently re-query a stored result.

    Unlike ordinary Stage-D output, the lookup itself has an immutable pre-call reservation.  A
    search receipt alone is insufficient: a crash between ``resolver.resolve`` and the resolution
    write would otherwise turn a supposedly one-shot Crossref request into a repeat on resume.
    """

    method = (
        NoveltyWebLeadResolutionMethod.DOI_SINGLE_ENTITY
        if lead.claimed_doi.strip()
        else NoveltyWebLeadResolutionMethod.TITLE_RECONCILIATION
    )
    deterministic_query_digest = stable_hash(
        {
            "schema": "novelty_web_lead_reconciliation_request/v1",
            "receipt_id": receipt_id,
            "lead_id": lead.lead_id,
            "method": method.value,
            "claimed_doi": lead.claimed_doi,
            "title": lead.title,
            "deterministic_provider": resolver.provider_id,
        }
    )
    resolution_id = (
        "novelty-web-resolution-"
        f"{stable_hash({'receipt_id': receipt_id, 'lead_id': lead.lead_id, 'request': deterministic_query_digest})[:20]}"
    )
    path = web_grounder.paths.resolution_path(resolution_id)
    if path.exists():
        if path.is_symlink() or not path.is_file():
            raise ValueError("novelty web lead resolution path is not a regular file")
        persisted = load_model(path, NoveltyWebLeadResolution)
        _validate_novelty_web_resolution_binding(
            persisted,
            resolution_id=resolution_id,
            receipt_id=receipt_id,
            lead=lead,
            deterministic_query_digest=deterministic_query_digest,
        )
        return persisted

    reservation = _build_novelty_web_lead_resolution_reservation(
        resolution_id=resolution_id,
        receipt_id=receipt_id,
        lead=lead,
        method=method,
        deterministic_provider_id=resolver.provider_id,
        deterministic_query_digest=deterministic_query_digest,
    )
    reservation_path = _novelty_web_lead_resolution_reservation_path(
        web_grounder, reservation.reservation_id
    )
    if reservation_path.exists():
        if reservation_path.is_symlink() or not reservation_path.is_file():
            raise ValueError(
                "novelty web lead reconciliation reservation path is not a regular file"
            )
        persisted_reservation = load_model(reservation_path, NoveltyWebLeadResolutionReservation)
        _validate_novelty_web_lead_resolution_reservation(
            persisted_reservation,
            expected=reservation,
        )
        # This reservation was written before a prior attempt, but no terminal resolution is
        # present.  Its outcome is unknowable, so close it advisory-only without a second
        # deterministic-provider request.
        unavailable = _unavailable_novelty_web_lead_resolution(
            resolution_id=resolution_id,
            receipt_id=receipt_id,
            lead=lead,
        )
        atomic_write_model(path, unavailable)
        return unavailable

    atomic_write_model(reservation_path, reservation)
    retrieval_query_id = f"{resolution_id}-query"
    try:
        outcome = resolver.resolve(
            query_id=retrieval_query_id,
            claimed_doi=lead.claimed_doi,
            claimed_title=lead.title,
        )
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        outcome = NoveltyLeadResolutionResult(
            provider_id=resolver.provider_id,
            method=(
                RetrievalLeadResolutionMethod.DOI_SINGLE_ENTITY
                if method == NoveltyWebLeadResolutionMethod.DOI_SINGLE_ENTITY
                else RetrievalLeadResolutionMethod.TITLE_RECONCILIATION
            ),
            status=RetrievalLeadResolutionStatus.ERROR,
            error_class=type(exc).__name__,
        )
    outcome = _validate_novelty_web_lead_resolution_outcome(
        outcome,
        reservation=reservation,
        retrieval_query_id=retrieval_query_id,
    )
    resolution = _build_novelty_web_lead_resolution(
        resolution_id=resolution_id,
        receipt_id=receipt_id,
        lead=lead,
        deterministic_query_digest=deterministic_query_digest,
        retrieval_query_id=retrieval_query_id,
        outcome=outcome,
    )
    # Atomic replace is intentionally only used for a path that did not exist at the check above.
    # A normal single Stage-D process therefore never rewrites an immutable completed resolution;
    # a concurrent/tampered path becomes a validation failure rather than silently replacing bytes.
    if path.exists():
        raise ValueError("novelty web lead resolution appeared during deterministic reconciliation")
    atomic_write_model(path, resolution)
    return resolution


def _novelty_web_lead_resolution_reservation_path(
    web_grounder: NoveltyWebGrounder, reservation_id: str
) -> Path:
    """Locate a reconciliation reservation outside ordinary Stage-D cleanup roots."""

    return web_grounder.paths.journal_root / "resolution-reservations" / f"{reservation_id}.yaml"


def _build_novelty_web_lead_resolution_reservation(
    *,
    resolution_id: str,
    receipt_id: str,
    lead: WebFoundPriorLead,
    method: NoveltyWebLeadResolutionMethod,
    deterministic_provider_id: str,
    deterministic_query_digest: str,
) -> NoveltyWebLeadResolutionReservation:
    """Build the exact one-shot reconciliation identity before the resolver is callable."""

    reservation_payload = {
        "schema": "novelty_web_lead_resolution_reservation/v1",
        "resolution_id": resolution_id,
        "receipt_id": receipt_id,
        "lead_id": lead.lead_id,
        "method": method.value,
        "deterministic_provider_id": deterministic_provider_id,
        "deterministic_query_digest": deterministic_query_digest,
    }
    return NoveltyWebLeadResolutionReservation(
        reservation_id=(
            f"novelty-web-resolution-reservation-{stable_hash(reservation_payload)[:20]}"
        ),
        resolution_id=resolution_id,
        receipt_id=receipt_id,
        lead_id=lead.lead_id,
        method=method,
        deterministic_provider_id=deterministic_provider_id,
        deterministic_query_digest=deterministic_query_digest,
    )


def _validate_novelty_web_lead_resolution_reservation(
    persisted: NoveltyWebLeadResolutionReservation,
    *,
    expected: NoveltyWebLeadResolutionReservation,
) -> None:
    """Reject substituted reconciliation reservations before treating them as no-retry state."""

    if persisted.model_dump(mode="json", exclude={"reserved_at"}) != expected.model_dump(
        mode="json", exclude={"reserved_at"}
    ):
        raise ValueError("persisted novelty web reconciliation reservation does not bind its lead")


def _unavailable_novelty_web_lead_resolution(
    *,
    resolution_id: str,
    receipt_id: str,
    lead: WebFoundPriorLead,
) -> NoveltyWebLeadResolution:
    """Close a dangling pre-call reconciliation reservation without claiming its outcome."""

    return NoveltyWebLeadResolution(
        resolution_id=resolution_id,
        receipt_id=receipt_id,
        lead_id=lead.lead_id,
        method=NoveltyWebLeadResolutionMethod.NOT_ATTEMPTED,
        status=NoveltyWebLeadResolutionStatus.UNAVAILABLE,
        rationale=(
            "an earlier deterministic reconciliation reservation was left unmatched; "
            "this lead remains advisory and was not retried"
        ),
    )


def _validate_novelty_web_lead_resolution_outcome(
    outcome: NoveltyLeadResolutionResult,
    *,
    reservation: NoveltyWebLeadResolutionReservation,
    retrieval_query_id: str,
) -> NoveltyLeadResolutionResult:
    """Fail closed unless a resolved hit binds its reserved provider, request, and response."""

    expected_method = {
        NoveltyWebLeadResolutionMethod.DOI_SINGLE_ENTITY: (
            RetrievalLeadResolutionMethod.DOI_SINGLE_ENTITY
        ),
        NoveltyWebLeadResolutionMethod.TITLE_RECONCILIATION: (
            RetrievalLeadResolutionMethod.TITLE_RECONCILIATION
        ),
    }[reservation.method]
    if (
        outcome.provider_id != reservation.deterministic_provider_id
        or outcome.method != expected_method
    ):
        return _resolver_resolution_error(
            reservation=reservation,
            method=expected_method,
            error_class="ResolverIdentityMismatch",
        )
    if outcome.status == RetrievalLeadResolutionStatus.RESOLVED:
        hit = outcome.hit
        if (
            hit is None
            or hit.provider_id != outcome.provider_id
            or hit.provider_id != reservation.deterministic_provider_id
            or hit.query_id != retrieval_query_id
            or hit.response_digest != outcome.response_digest
        ):
            return _resolver_resolution_error(
                reservation=reservation,
                method=expected_method,
                error_class="ResolverProvenanceMismatch",
            )
    return outcome


def _resolver_resolution_error(
    *,
    reservation: NoveltyWebLeadResolutionReservation,
    method: RetrievalLeadResolutionMethod,
    error_class: str,
) -> NoveltyLeadResolutionResult:
    """Close an untrusted resolver response without preserving disputed response material."""

    return NoveltyLeadResolutionResult(
        provider_id=reservation.deterministic_provider_id,
        method=method,
        status=RetrievalLeadResolutionStatus.ERROR,
        error_class=error_class,
    )


def _build_novelty_web_lead_resolution(
    *,
    resolution_id: str,
    receipt_id: str,
    lead: WebFoundPriorLead,
    deterministic_query_digest: str,
    retrieval_query_id: str,
    outcome: NoveltyLeadResolutionResult,
) -> NoveltyWebLeadResolution:
    """Convert one bounded resolver result into a self-contained, replayable terminal artifact."""

    method = _schema_resolution_method(outcome.method)
    if outcome.status == RetrievalLeadResolutionStatus.RESOLVED and outcome.hit is not None:
        try:
            canonical = _canonical_web_resolved_prior(
                outcome.hit,
                receipt_id=receipt_id,
                lead=lead,
                resolution_id=resolution_id,
                retrieval_query_id=retrieval_query_id,
            )
        except ValueError:
            # The reconciliation response arrived, but its candidate text cannot safely cross into
            # proposal context.  Preserve the response digest and close this lead advisory-only.
            return NoveltyWebLeadResolution(
                resolution_id=resolution_id,
                receipt_id=receipt_id,
                lead_id=lead.lead_id,
                method=method,
                deterministic_provider_id=outcome.provider_id,
                deterministic_query_digest=deterministic_query_digest,
                status=NoveltyWebLeadResolutionStatus.UNRESOLVED,
                deterministic_response_digest=outcome.response_digest or "",
                rationale="resolved scholarly candidate failed proposal-safety quarantine",
            )
        return NoveltyWebLeadResolution(
            resolution_id=resolution_id,
            receipt_id=receipt_id,
            lead_id=lead.lead_id,
            method=method,
            deterministic_provider_id=outcome.provider_id,
            deterministic_query_digest=deterministic_query_digest,
            status=NoveltyWebLeadResolutionStatus.RESOLVED,
            canonical_source_record_id=canonical.source_record_id,
            canonical_prior=canonical,
            canonical_prior_snapshot_digest=stable_hash(canonical.model_dump(mode="json")),
            deterministic_response_digest=outcome.response_digest or "",
            rationale="one bounded Crossref reconciliation resolved a canonical scholarly record",
        )
    if outcome.status == RetrievalLeadResolutionStatus.UNRESOLVED:
        return NoveltyWebLeadResolution(
            resolution_id=resolution_id,
            receipt_id=receipt_id,
            lead_id=lead.lead_id,
            method=method,
            deterministic_provider_id=outcome.provider_id,
            deterministic_query_digest=deterministic_query_digest,
            status=NoveltyWebLeadResolutionStatus.UNRESOLVED,
            deterministic_response_digest=outcome.response_digest or "",
            rationale="one bounded Crossref reconciliation found no canonical scholarly match",
        )
    if outcome.status == RetrievalLeadResolutionStatus.ERROR:
        return NoveltyWebLeadResolution(
            resolution_id=resolution_id,
            receipt_id=receipt_id,
            lead_id=lead.lead_id,
            method=method,
            deterministic_provider_id=outcome.provider_id,
            deterministic_query_digest=deterministic_query_digest,
            status=NoveltyWebLeadResolutionStatus.ERROR,
            failure_class=outcome.error_class or "ResolverError",
            rationale="deterministic scholarly reconciliation failed without a durable response",
        )
    if outcome.status == RetrievalLeadResolutionStatus.INVALID_INPUT:
        return NoveltyWebLeadResolution(
            resolution_id=resolution_id,
            receipt_id=receipt_id,
            lead_id=lead.lead_id,
            method=method,
            deterministic_provider_id=outcome.provider_id,
            deterministic_query_digest=deterministic_query_digest,
            status=NoveltyWebLeadResolutionStatus.INVALID_INPUT,
            failure_class=outcome.error_class or "InvalidLeadInput",
            rationale="web lead could not form a safe bounded scholarly reconciliation request",
        )
    raise ValueError("unknown novelty web lead resolution status")


def _schema_resolution_method(
    method: RetrievalLeadResolutionMethod,
) -> NoveltyWebLeadResolutionMethod:
    return {
        RetrievalLeadResolutionMethod.DOI_SINGLE_ENTITY: (
            NoveltyWebLeadResolutionMethod.DOI_SINGLE_ENTITY
        ),
        RetrievalLeadResolutionMethod.TITLE_RECONCILIATION: (
            NoveltyWebLeadResolutionMethod.TITLE_RECONCILIATION
        ),
        RetrievalLeadResolutionMethod.NONE: NoveltyWebLeadResolutionMethod.NOT_ATTEMPTED,
    }[method]


def _canonical_web_resolved_prior(
    hit: NoveltySearchHit,
    *,
    receipt_id: str,
    lead: WebFoundPriorLead,
    resolution_id: str,
    retrieval_query_id: str,
) -> NoveltyPriorRecord:
    """Create a canonical scholarly record without promoting web metadata itself to evidence."""

    assert_secret_free_persisted_value(
        {
            "source_record_id": hit.source_record_id,
            "title": hit.title,
            "abstract_or_excerpt": hit.abstract,
            "doi": hit.doi,
            "provider_id": hit.provider_id,
            "query_id": hit.query_id,
        },
        path="resolved_novelty_web_prior",
    )
    assert_proposal_safe_payload(
        {
            "source_record_id": hit.source_record_id,
            "title": hit.title,
            "abstract_or_excerpt": hit.abstract,
            "doi": hit.doi,
            "provider_id": hit.provider_id,
            "query_id": hit.query_id,
        },
        context="resolved novelty web prior",
    )
    abstract = hit.abstract.strip()
    basis = NoveltyEvidenceBasis.ABSTRACT if abstract else NoveltyEvidenceBasis.TITLE_ONLY
    doi = hit.doi.strip().lower()
    source_record_id = f"https://doi.org/{doi}" if doi else hit.source_record_id
    if not source_record_id.strip():
        raise ValueError("web resolution did not supply a canonical scholarly identity")
    scholarly_identity = NoveltyScholarlyIdentity.DOI if doi else NoveltyScholarlyIdentity.CROSSREF
    payload: dict[str, object] = {
        "source_record_id": source_record_id,
        "title": hit.title,
        "year": hit.year,
        "doi": doi,
        # Crossref landing URLs can contain untrusted query strings.  The host retains only the
        # DOI URL it constructed from the canonical identifier.
        "url": source_record_id if doi else "",
        "providers": [hit.provider_id],
        "query_ids": [retrieval_query_id],
        "evidence_basis": basis.value,
        "scholarly_identity": scholarly_identity.value,
        "abstract_or_excerpt": abstract,
        "evidence_origin": NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED.value,
        "web_receipt_id": receipt_id,
        "web_lead_id": lead.lead_id,
        "web_resolution_id": resolution_id,
    }
    return NoveltyPriorRecord.model_validate(
        {
            **payload,
            "evidence_digest": stable_hash(payload),
            "retrieval_scores": {hit.provider_id: hit.retrieval_score},
        }
    )


def _validate_novelty_web_resolution_binding(
    resolution: NoveltyWebLeadResolution,
    *,
    resolution_id: str,
    receipt_id: str,
    lead: WebFoundPriorLead,
    deterministic_query_digest: str,
) -> None:
    if (
        resolution.resolution_id != resolution_id
        or resolution.receipt_id != receipt_id
        or resolution.lead_id != lead.lead_id
    ):
        raise ValueError("persisted novelty web lead resolution does not bind its current lead")
    if (
        resolution.status != NoveltyWebLeadResolutionStatus.UNAVAILABLE
        and resolution.deterministic_query_digest != deterministic_query_digest
    ):
        raise ValueError(
            "persisted novelty web lead resolution route does not bind its current lead"
        )
    if resolution.status == NoveltyWebLeadResolutionStatus.RESOLVED:
        prior = resolution.canonical_prior
        if prior is None or (
            prior.web_receipt_id != receipt_id
            or prior.web_lead_id != lead.lead_id
            or prior.web_resolution_id != resolution_id
        ):
            raise ValueError("persisted resolved novelty web prior has broken provenance links")


NOVELTY_SEARCH_TERM_PROMPT_VERSION = "novelty_search_terms/v1"
#: A handful is enough: each term is its own query, and they are unioned. More terms buy breadth at
#: linear cost; the pack is capped downstream anyway.
NOVELTY_SEARCH_TERM_MAX = 6


class NoveltySearchTermsModelOutput(BaseModel):
    """The reviewer's own reading of what to look for."""

    model_config = ConfigDict(extra="forbid")

    terms: list[str] = Field(default_factory=list, max_length=NOVELTY_SEARCH_TERM_MAX)


def build_novelty_search_terms(
    variant: QuestionFamilyVariant,
    *,
    provider: StructuredModelProvider,
) -> list[str]:
    """Domain terms for one variant, or an empty list.

    Extracting search terms from a scientific question is a judgement about a field, so it belongs
    to a model rather than to a regular expression -- a hand-written extractor here would be exactly
    the kind of deterministic word-game this project keeps removing. An empty return is a normal
    outcome and the caller falls back to the run's declared scope terms.
    """
    seed = variant.seed
    packet = {
        "question": seed.question,
        "scientific_tension": seed.scientific_tension,
        "discriminating_observation": seed.discriminating_observation,
    }
    try:
        output = provider.generate_structured(
            system_prompt=_load_prompt(NOVELTY_SEARCH_TERM_PROMPT_VERSION),
            user_prompt=json.dumps(packet, sort_keys=True, ensure_ascii=False),
            output_model=NoveltySearchTermsModelOutput,
        )
    except StructuredModelProviderError:
        # Never fatal: the deterministic scope terms are the backstop, and a novelty pack built from
        # them is still real domain literature.
        return []
    seen: set[str] = set()
    terms: list[str] = []
    for term in output.terms:
        cleaned = sanitize_novelty_query(term).strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            terms.append(cleaned)
    return terms[:NOVELTY_SEARCH_TERM_MAX]


def build_novelty_search_plan(
    family: QuestionFamily,
    variant: QuestionFamilyVariant,
    *,
    provider_ids: list[str],
    search_cutoff: str,
    search_terms: Sequence[str] = (),
    fallback_terms: Sequence[str] = (),
) -> NoveltySearchPlan:
    """One domain term per query. The focus is a LABEL and never enters the query string.

    The four prose foci this replaces joined whole sentences -- question, tension + shared tension,
    distinction + hypothesis + observation, the three consequence clauses -- into 19-41 word
    queries. OpenAlex ANDs un-operatored words over FULLTEXT, so on the 2026-07-31 leg 6 of 8 such
    queries returned ZERO, and Crossref, which ranks by relevance and never abstains, answered the
    remainder with the nearest thing it had: papers on torture, Ukrainian cultural heritage and
    portfolio credit models reached a stratospheric-dynamics novelty pack. The same packs' best
    priors -- three perfect-overlap papers on eddy-annular-mode feedback -- came in on the one lane
    that was not prose.

    Terms come from the reviewer model (extracting them from a scientific question is a judgement,
    not string processing), and `fallback_terms` -- the run's own declared scope terms -- back that
    up when the model returns nothing. This is the project's standing shape: the agent judges, the
    deterministic path only catches.
    """
    seed = variant.seed
    terms = [term.strip() for term in search_terms if term.strip()]
    if not terms:
        terms = [term.strip() for term in fallback_terms if term.strip()]
    raw = [(NoveltyQueryFocus.DOMAIN_TERM, term) for term in terms]
    queries: list[NoveltySearchQuery] = []
    for index, (focus, value) in enumerate(raw, start=1):
        query = sanitize_novelty_query(value)
        query_id = f"{variant.variant_id}-{focus.value}-{index}"
        queries.append(
            NoveltySearchQuery(
                query_id=query_id,
                focus=focus,
                query=query,
                query_digest=stable_hash({"query_id": query_id, "query": query}),
            )
        )
    question_digest = stable_hash(seed)
    return NoveltySearchPlan(
        search_plan_id=f"novelty-search-{stable_hash({'variant': variant.variant_id, 'question': question_digest, 'queries': [query.query_digest for query in queries], 'providers': provider_ids, 'cutoff': search_cutoff})[:16]}",
        question_family_id=family.question_family_id,
        variant_id=variant.variant_id,
        question_seed_id=variant.question_seed_id,
        question_digest=question_digest,
        search_cutoff=search_cutoff,
        required_provider_lanes=provider_ids,
        queries=queries,
    )


def retrieve_novelty_evidence(
    plan: NoveltySearchPlan,
    *,
    providers: list[NoveltySearchProvider],
    max_priors: int = 20,
    web_resolved_priors: tuple[NoveltyPriorRecord, ...] = (),
    web_receipt_ids: tuple[str, ...] = (),
    web_resolution_ids: tuple[str, ...] = (),
    web_exclusion_ids: tuple[str, ...] = (),
    web_provider_attempt: NoveltyProviderAttempt | None = None,
    web_grounding_insufficiency_reason: str = "",
) -> NoveltyEvidencePack:
    hits: list[NoveltySearchHit] = []
    attempts: list[NoveltyProviderAttempt] = []
    providers_by_id = {provider.provider_id: provider for provider in providers}
    for provider_id in plan.required_provider_lanes:
        provider = providers_by_id.get(provider_id)
        if provider is None:
            attempts.append(
                NoveltyProviderAttempt(
                    provider_id=provider_id,
                    status=NoveltyProviderAttemptStatus.DISABLED,
                    error_class="provider_not_configured",
                )
            )
            continue
        response_digests: dict[str, str] = {}
        provider_hits: list[NoveltySearchHit] = []
        failed = False
        error_class = ""
        for query in plan.queries:
            try:
                query_hits, response_digest = provider.search(
                    query_id=query.query_id,
                    query=query.query,
                )
                response_digests[query.query_id] = response_digest
                provider_hits.extend(query_hits)
            except (
                OSError,
                RuntimeError,
                TypeError,
                ValueError,
            ) as exc:  # provider boundary; persist class, never raw secret-bearing text
                failed = True
                error_class = type(exc).__name__
        hits.extend(provider_hits)
        attempts.append(
            NoveltyProviderAttempt(
                provider_id=provider_id,
                status=(
                    NoveltyProviderAttemptStatus.FAILED
                    if failed and not response_digests
                    else NoveltyProviderAttemptStatus.SUCCEEDED
                ),
                query_ids=[query.query_id for query in plan.queries],
                response_digests=response_digests,
                candidate_count=len(provider_hits),
                error_class=error_class,
            )
        )

    priors, exclusions = _canonicalize_hits(hits)
    # Web-discovered material may enter the scholarly pack only through an immutable canonical
    # snapshot created by the one-shot resolver.  Raw leads, page locators and short quotes stay
    # solely in the low-authority receipt and never reach this function's reviewer-facing priors.
    deterministic_source_ids = {prior.source_record_id for prior in priors}
    admitted_web: list[NoveltyPriorRecord] = []
    for prior in web_resolved_priors:
        if prior.evidence_origin != NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED:
            raise ValueError("N-2 web evidence must be a resolved canonical prior record")
        if (
            prior.web_receipt_id not in web_receipt_ids
            or prior.web_resolution_id not in web_resolution_ids
        ):
            raise ValueError("N-2 web prior is not linked to this evidence pack's receipt chain")
        # A normal two-lane retrieval may find the exact same scholarly record.  Keep that
        # ordinary record rather than inserting duplicate source IDs into the model packet; this
        # conservative choice simply means duplicate web corroboration cannot replace a failed
        # lane on its own.
        if prior.source_record_id not in deterministic_source_ids:
            admitted_web.append(prior)
            deterministic_source_ids.add(prior.source_record_id)
    # Reserve the web lane's slots BEFORE truncating.  Appending first and cutting afterwards
    # silently deleted the entire discovery lane on every live run through 2026-07-26: the
    # deterministic list is always longer than ``max_priors`` after dedup, so the appended web
    # priors sat past the cut every single time — 2740 priors across 137 packs, none of them
    # web-origin, while the packs still advertised a non-empty ``web_resolution_ids``.  The web
    # reservation is itself capped at half the pack so neither lane can starve the other.
    web_budget = min(len(admitted_web), max(max_priors // 2, 1))
    reserved_web = admitted_web[:web_budget]
    priors = [*priors[: max(max_priors - len(reserved_web), 0)], *reserved_web]
    if admitted_web and not any(
        prior.evidence_origin == NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED for prior in priors
    ):  # pragma: no cover - guarded by construction above; a regression tripwire, not a branch
        raise ValueError(
            "N-2 web priors survived deduplication but none reached the reviewer-facing pack"
        )
    if web_provider_attempt is not None:
        if web_provider_attempt.lane != NoveltyEvidenceLane.WEB_DISCOVERY:
            raise ValueError("N-2 web provider attempt must carry the web-discovery lane")
        attempts.append(web_provider_attempt)
    successful = {
        attempt.provider_id
        for attempt in attempts
        if (
            attempt.status == NoveltyProviderAttemptStatus.SUCCEEDED
            and attempt.lane == NoveltyEvidenceLane.DETERMINISTIC_SCHOLARLY
        )
    }
    resolved_web_in_pack = [
        prior
        for prior in priors
        if prior.evidence_origin == NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED
    ]
    insufficiency: list[str] = []
    if not (len(successful) >= 2 or (len(successful) == 1 and resolved_web_in_pack)):
        insufficiency.append("fewer than two scholarly-index provider lanes completed")
    if not any(prior.evidence_basis != NoveltyEvidenceBasis.TITLE_ONLY for prior in priors):
        insufficiency.append("no abstract- or excerpt-bearing prior record was retrieved")
    # A scope caveat, not an insufficiency. The two floors above are the real ones -- fewer than
    # two scholarly lanes, or no content-bearing prior -- and they still hold. The supplementary
    # web lane failing to complete narrows what the judge can claim to have searched; it does not
    # make the judge unable to read the twenty scholarly priors in front of it. The detailed
    # host-side classification stays in the provider attempt and the durable receipt, which is
    # where it is already diagnosable; only this bounded sentence reaches the reviewer packet.
    scope_caveats: list[str] = []
    if web_grounding_insufficiency_reason:
        scope_caveats.append(
            "the supplementary web-discovery lane did not complete for this variant, so the "
            "recorded search scope is the scholarly lanes only"
        )
    adequate = not insufficiency
    pack_payload: dict[str, Any] = {
        "search_plan_id": plan.search_plan_id,
        "question_family_id": plan.question_family_id,
        "variant_id": plan.variant_id,
        "question_seed_id": plan.question_seed_id,
        "question_digest": plan.question_digest,
        "search_cutoff": plan.search_cutoff,
        "provider_attempts": [attempt.model_dump(mode="json") for attempt in attempts],
        "priors": [prior.model_dump(mode="json") for prior in priors],
        "exclusions": [exclusion.model_dump(mode="json") for exclusion in exclusions],
        "web_receipt_ids": sorted(set(web_receipt_ids)),
        "web_resolution_ids": sorted(set(web_resolution_ids)),
        "web_exclusion_ids": sorted(set(web_exclusion_ids)),
    }
    return NoveltyEvidencePack(
        evidence_pack_id=f"novelty-evidence-{stable_hash(pack_payload)[:16]}",
        **pack_payload,
        evidence_adequate_for_review=adequate,
        insufficiency_reasons=insufficiency,
        scope_caveats=scope_caveats,
    )


def _longest_complete_object_prefix(text: str) -> str | None:
    """The longest prefix of a cut-off JSON object that is itself a complete object.

    One pass tracking string and escape state so a comma or brace inside `rationale` prose is never
    mistaken for structure. Cuts at the last TOP-LEVEL comma and appends exactly one `}` -- the only
    byte this repository ever authors into a model's reply. A key/value pair still being written is
    dropped whole, never completed, and an array still open is dropped entirely rather than closed
    early: half a comparison table is not evidence.
    """
    if not text.startswith("{"):
        return None
    depth = 0
    in_string = False
    escaped = False
    last_top_level_comma = -1
    for index, char in enumerate(text):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = in_string
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
        elif char == "," and depth == 1:
            last_top_level_comma = index
    if last_top_level_comma < 0:
        return None
    return text[:last_top_level_comma] + "}"


def _salvage_truncated_review(exc: StructuredModelProviderError) -> NoveltyReviewModelOutput | None:
    """The science a cut-off reply already paid for, or None.

    The repaired prefix is handed to the UNMODIFIED ``NoveltyReviewModelOutput``, whose validator
    already encodes which verdict needs which evidence: `direct_recap` and
    `close_prior_revision_required` require comparisons, `direct_recap` additionally requires one
    that directly answers the question, `close_prior` requires distinction requirements. So if the
    recovered prefix validates, the verdict's own evidentiary requirement was met by bytes that
    actually arrived. Nothing is inferred, defaulted in, or completed.
    """
    if not exc.partial_output_text:
        return None
    repaired = _longest_complete_object_prefix(exc.partial_output_text)
    if repaired is None:
        return None
    try:
        recovered = json.loads(repaired)
    except json.JSONDecodeError:  # pragma: no cover - the repair only ever emits parseable objects
        return None
    if not isinstance(recovered, dict):  # pragma: no cover - the repair only ever emits objects
        return None
    try:
        # Explicit kwargs, not a validate-from-JSON call: the latter is a registered construction
        # seam and would turn this into a control-plane change. The two list fields fall back to the
        # schema's OWN defaults when the cut landed before they started -- which cannot smuggle a
        # rejection through, because the unmodified validator still requires comparisons for
        # `direct_recap` and `close_prior_revision_required`.
        return NoveltyReviewModelOutput(
            verdict=recovered["verdict"],
            evidence_adequate=recovered["evidence_adequate"],
            rationale=recovered["rationale"],
            comparisons=recovered.get("comparisons", []),
            distinction_requirements=recovered.get("distinction_requirements", []),
        )
    except (KeyError, ValidationError):
        return None


def review_variant_novelty(
    variant: QuestionFamilyVariant,
    evidence: NoveltyEvidencePack,
    *,
    reviewer: StructuredModelProvider,
) -> VariantNoveltyAssessment:
    if stable_hash(variant.seed) != evidence.question_digest:
        raise ValueError("novelty evidence does not bind the active variant question")
    evidence_digest = stable_hash(evidence)
    packet = _build_reviewer_packet(variant, evidence)
    input_digest = stable_hash(packet)
    if not evidence.evidence_adequate_for_review:
        return VariantNoveltyAssessment(
            assessment_id=f"novelty-assessment-{stable_hash({'evidence': evidence_digest, 'verdict': 'insufficient'})[:16]}",
            question_family_id=evidence.question_family_id,
            variant_id=variant.variant_id,
            question_seed_id=variant.question_seed_id,
            question_digest=evidence.question_digest,
            evidence_pack_id=evidence.evidence_pack_id,
            evidence_pack_digest=evidence_digest,
            verdict=NoveltyVerdict.INSUFFICIENT_SEARCH_EVIDENCE,
            evidence_adequate=False,
            rationale="; ".join(evidence.insufficiency_reasons),
            reviewer_provider_id="not_invoked:insufficient_evidence",
            reviewer_prompt_version=NOVELTY_REVIEWER_PROMPT_VERSION,
            reviewer_input_digest=input_digest,
            search_cutoff=evidence.search_cutoff,
            web_receipt_ids=evidence.web_receipt_ids,
            web_resolution_ids=evidence.web_resolution_ids,
        )
    if reviewer.provider_id == variant.seed.origin_provider_id:
        raise ValueError("novelty reviewer must not be the exact Question Scientist model identity")
    output = None
    salvaged: NoveltyReviewModelOutput | None = None
    salvage: NoveltyReviewSalvage | None = None
    for attempt in range(1, NOVELTY_REVIEW_MAX_ATTEMPTS + 1):
        try:
            output = reviewer.generate_structured(
                system_prompt=_load_prompt(NOVELTY_REVIEWER_PROMPT_VERSION),
                user_prompt=json.dumps(packet, sort_keys=True, ensure_ascii=False),
                output_model=NoveltyReviewModelOutput,
            )
            break
        except StructuredModelProviderError as exc:
            # A schema-invalid reply says nothing about the question under review, yet one such
            # reply used to defer the variant outright — the same reply-shape-as-verdict mistake the
            # paper extractor already avoids (services/paper_ingest/extraction.py). Replay the
            # identical packet within one clear budget; every other failure kind, and the final
            # invalid reply, still fail closed with the provider's own error.
            # An EMPTY reply says even less about the question than a schema-invalid one, and the
            # comment above already names the principle it violates. It was excluded only because
            # the provider reports it under a different kind: `AnthropicStructuredModelProvider`
            # raises INVALID_RESPONSE when `parsed_output` is None. That gap deferred 3 variants on
            # the 2026-07-30 leg and 4 on the leg before, where it took BOTH variants of one family
            # and closed it outright. Same budget, same identical packet, same fail-closed ending.
            # Keep the first recoverable reply. A classifier that cuts a reply off after the
            # verdict and rationale are written has already been paid for; discarding those bytes is
            # what filed a real `no_direct_recap_found_in_scope` as thin literature on the
            # 2026-07-31 leg and closed a family that belonged in the run.
            if salvaged is None:
                salvaged = _salvage_truncated_review(exc)
                if salvaged is not None:
                    salvage = NoveltyReviewSalvage(
                        recovered_verdict=salvaged.verdict,
                        adopted=(salvaged.verdict is NoveltyVerdict.NO_DIRECT_RECAP_FOUND_IN_SCOPE),
                        received_fields=sorted(salvaged.model_fields_set),
                        # A digest, never the prose: the raw reply is model-authored text and
                        # belongs in the operator-gated capture, not in a persisted artifact.
                        reply_sha256=hashlib.sha256(
                            exc.partial_output_text.encode("utf-8")
                        ).hexdigest(),
                        reply_chars=len(exc.partial_output_text),
                    )
            if (
                exc.kind
                not in {
                    StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID,
                    StructuredModelFailureKind.INVALID_RESPONSE,
                }
                or attempt >= NOVELTY_REVIEW_MAX_ATTEMPTS
            ):
                # Salvage is the LAST resort, never a substitute for the retry: the budget is
                # unchanged and a complete reply always wins. Only an admit may be adopted -- a
                # salvaged rejection is recorded by the caller and never acted on, because a
                # rejection is terminal while an admit still faces three further gates.
                if (
                    salvaged is not None
                    and salvaged.verdict is NoveltyVerdict.NO_DIRECT_RECAP_FOUND_IN_SCOPE
                ):
                    output = salvaged
                    break
                raise
    if output is None:  # pragma: no cover - the loop either binds output or raises
        raise RuntimeError("novelty reviewer returned no structured output")
    try:
        assert_proposal_safe_payload(
            output.model_dump(mode="json"), context="novelty reviewer output"
        )
    except ValueError:
        return _insufficient_assessment(
            variant,
            evidence,
            reviewer_provider_id=reviewer.provider_id,
            reviewer_input_digest=input_digest,
            rationale=(
                "Novelty reviewer output crossed the proposal-safety boundary; deferred rather "
                "than persisting untrusted comparison text."
            ),
        )
    prior_by_source = {prior.source_record_id: prior for prior in evidence.priors}
    allowed_sources = set(prior_by_source)
    cited_sources = {comparison.source_record_id for comparison in output.comparisons}
    # Typed, not bare: these two judge a model REPLY, so they close one variant honestly. The
    # binding and identity checks above are host invariants and stay hard.
    if not cited_sources <= allowed_sources:
        raise NoveltyVariantRejection("novelty reviewer cited a source outside its evidence pack")
    for comparison in output.comparisons:
        prior = prior_by_source[comparison.source_record_id]
        if comparison.citation_binding.evidence_digest != prior.evidence_digest:
            raise NoveltyVariantRejection(
                "novelty reviewer citation binding does not match persisted evidence"
            )
    if output.verdict == NoveltyVerdict.DIRECT_RECAP and not _direct_recap_is_corroborated(
        output=output,
        prior_by_source=prior_by_source,
    ):
        return _insufficient_assessment(
            variant,
            evidence,
            reviewer_provider_id=reviewer.provider_id,
            reviewer_input_digest=input_digest,
            rationale=(
                "A possible direct recap lacked a cited, content-bearing prior with "
                "scholarly corroboration; deferred rather than rejected."
            ),
        )
    if (
        output.verdict == NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED
        and not _close_prior_has_sufficient_authority(
            output=output,
            prior_by_source=prior_by_source,
        )
    ):
        return _insufficient_assessment(
            variant,
            evidence,
            reviewer_provider_id=reviewer.provider_id,
            reviewer_input_digest=input_digest,
            rationale=(
                "A possible close-prior judgment cited a title-only canonical record resolved "
                "from a web lead; deferred rather than requiring a substantive revision."
            ),
        )
    reviewer_fields = output.model_dump(mode="python")
    # D6: truncate the judge free-text that will reach the questioner's revision prompt to its
    # hard ceilings BEFORE strict construction — degrade, never crash a family on a verbose judge.
    reviewer_fields["rationale"] = _truncate(
        reviewer_fields.get("rationale", ""), NOVELTY_RATIONALE_MAX_CHARS
    )
    reviewer_fields["distinction_requirements"] = [
        _truncate(item, NOVELTY_DISTINCTION_ITEM_MAX_CHARS)
        for item in reviewer_fields.get("distinction_requirements", [])[
            :NOVELTY_DISTINCTION_MAX_ITEMS
        ]
    ]
    if output.verdict != NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED:
        # Same repair discipline, one field over: `VariantNoveltyAssessment` rejects distinction
        # requirements on any non-close-prior verdict, and that rule exists NOWHERE the reviewer can
        # see it -- not in `NoveltyReviewModelOutput`, which the provider validates against, and not
        # in `prompts/novelty_reviewer/v3` (grep returns nothing). So a reviewer that finds no prior
        # recapping the question, says ADMIT, and helpfully attaches a few distinctions had its
        # entire source-bound verdict destroyed at strict construction -- past the retry loop, so
        # with zero retries -- and relabeled `insufficient_search_evidence`. That fired 3 times on
        # the 2026-07-30 leg, taking both variants of one family and therefore a whole dossier.
        # On a non-close-prior verdict these asks bind nothing and drive no revision, so dropping
        # them costs no science. The unstated rule must not outrank the reviewer's judgement.
        reviewer_fields["distinction_requirements"] = []
    payload = {
        "question_family_id": evidence.question_family_id,
        "variant_id": variant.variant_id,
        "question_seed_id": variant.question_seed_id,
        "question_digest": evidence.question_digest,
        "evidence_pack_id": evidence.evidence_pack_id,
        "evidence_pack_digest": stable_hash(evidence),
        **reviewer_fields,
        "reviewer_provider_id": reviewer.provider_id,
        "reviewer_prompt_version": NOVELTY_REVIEWER_PROMPT_VERSION,
        "reviewer_input_digest": input_digest,
        "search_cutoff": evidence.search_cutoff,
        "web_receipt_ids": evidence.web_receipt_ids,
        "web_resolution_ids": evidence.web_resolution_ids,
    }
    if salvage is not None:
        # Added only when a salvage actually happened, so a complete review keeps a byte-identical
        # assessment_id and no existing artifact shifts.
        payload["reply_completeness"] = NoveltyReplyCompleteness.SALVAGED_PREFIX
        payload["salvage"] = salvage
    return VariantNoveltyAssessment(
        assessment_id=f"novelty-assessment-{stable_hash(payload)[:16]}", **payload
    )


def _build_reviewer_packet(
    variant: QuestionFamilyVariant,
    evidence: NoveltyEvidencePack,
) -> dict[str, Any]:
    """Project only judge-relevant, source-bound text into the independent review packet."""

    seed = variant.seed
    packet = {
        "candidate_question": {
            "variant_id": variant.variant_id,
            "question_seed_id": variant.question_seed_id,
            "question": seed.question,
            "scientific_tension": seed.scientific_tension,
            "why_scientifically_important": seed.why_scientifically_important,
            "discriminating_observation": seed.discriminating_observation,
            "positive_result_consequence": seed.positive_result_consequence,
            "negative_result_consequence": seed.negative_result_consequence,
            "null_result_consequence": seed.null_result_consequence,
        },
        "evidence_pack": {
            "evidence_pack_id": evidence.evidence_pack_id,
            "search_cutoff": evidence.search_cutoff,
            "priors": [
                {
                    "source_record_id": prior.source_record_id,
                    "title": prior.title,
                    "year": prior.year,
                    "doi": prior.doi,
                    "scholarly_identity": prior.scholarly_identity.value,
                    "evidence_basis": prior.evidence_basis.value,
                    "abstract_or_excerpt": prior.abstract_or_excerpt,
                    "evidence_digest": prior.evidence_digest,
                    "evidence_origin": (
                        "resolved_web_lead"
                        if prior.evidence_origin == NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED
                        else "deterministic_scholarly_index"
                    ),
                    "web_provenance": (
                        {
                            "receipt_id": prior.web_receipt_id,
                            "resolution_id": prior.web_resolution_id,
                        }
                        if prior.evidence_origin == NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED
                        else None
                    ),
                }
                for prior in evidence.priors
            ],
            "web_receipt_ids": evidence.web_receipt_ids,
            "web_resolution_ids": evidence.web_resolution_ids,
        },
        "instructions": {
            "bounded_search_not_global_novelty": True,
            "scope_caveats": list(evidence.scope_caveats),
            "similarity_scores_are_recall_only": True,
            "cite_only_source_record_ids_in_pack": True,
            "direct_recap_requires_scholarly_corroboration": True,
        },
    }
    assert_proposal_safe_payload(packet, context="novelty reviewer packet")
    return packet


def _direct_recap_is_corroborated(
    *,
    output: NoveltyReviewModelOutput,
    prior_by_source: dict[str, NoveltyPriorRecord],
) -> bool:
    """A model's direct-recap opinion becomes rejection-eligible only with scholarly evidence."""

    return any(
        comparison.directly_answers_question
        and (prior := prior_by_source[comparison.source_record_id]).evidence_basis
        != NoveltyEvidenceBasis.TITLE_ONLY
        and prior.scholarly_identity != NoveltyScholarlyIdentity.UNVERIFIED
        and prior.evidence_origin
        in {
            NoveltyPriorEvidenceOrigin.DETERMINISTIC,
            NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED,
        }
        for comparison in output.comparisons
    )


def _close_prior_has_sufficient_authority(
    *,
    output: NoveltyReviewModelOutput,
    prior_by_source: dict[str, NoveltyPriorRecord],
) -> bool:
    """Prevent an N-2 title-only lead from being used in the sole revision pass.

    N-1 historically permits its ordinary scholarly records through the close-prior route, even
    when their available content is thin.  Keep that path unchanged.  N-2 adds a lower-authority
    discovery origin, so a Crossref-resolved record with only a title cannot contribute to the
    one permitted substantive rewrite.  We reject the whole close-prior result if it cites such a
    record: otherwise a reviewer could pair it with an ordinary N-1 comparison while still using
    the title-only web lead to compel the revision.  Ordinary N-1 title-only comparisons remain
    unchanged.
    """

    return not any(
        (prior := prior_by_source[comparison.source_record_id]).evidence_origin
        == NoveltyPriorEvidenceOrigin.WEB_LEAD_RESOLVED
        and prior.evidence_basis == NoveltyEvidenceBasis.TITLE_ONLY
        for comparison in output.comparisons
    )


def _insufficient_assessment(
    variant: QuestionFamilyVariant,
    evidence: NoveltyEvidencePack,
    *,
    reviewer_provider_id: str,
    reviewer_input_digest: str,
    rationale: str,
) -> VariantNoveltyAssessment:
    """Persist an honest non-rejection when a strict authority condition is not met."""

    evidence_digest = stable_hash(evidence)
    payload = {
        "variant": variant.variant_id,
        "question": evidence.question_digest,
        "evidence": evidence_digest,
        "provider": reviewer_provider_id,
        "input": reviewer_input_digest,
        "rationale": rationale,
    }
    return VariantNoveltyAssessment(
        assessment_id=f"novelty-assessment-{stable_hash(payload)[:16]}",
        question_family_id=evidence.question_family_id,
        variant_id=variant.variant_id,
        question_seed_id=variant.question_seed_id,
        question_digest=evidence.question_digest,
        evidence_pack_id=evidence.evidence_pack_id,
        evidence_pack_digest=evidence_digest,
        verdict=NoveltyVerdict.INSUFFICIENT_SEARCH_EVIDENCE,
        evidence_adequate=False,
        rationale=rationale,
        reviewer_provider_id=reviewer_provider_id,
        reviewer_prompt_version=NOVELTY_REVIEWER_PROMPT_VERSION,
        reviewer_input_digest=reviewer_input_digest,
        search_cutoff=evidence.search_cutoff,
        web_receipt_ids=evidence.web_receipt_ids,
        web_resolution_ids=evidence.web_resolution_ids,
    )


def revise_variant_for_novelty(
    family: QuestionFamily,
    variant: QuestionFamilyVariant,
    assessment: VariantNoveltyAssessment,
    evidence: NoveltyEvidencePack,
    *,
    revision_provider: StructuredModelProvider,
) -> tuple[QuestionFamilyVariant, NoveltyRevisionRecord]:
    if assessment.verdict != NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED:
        raise ValueError("novelty revision is allowed only for close-prior verdicts")
    packet = {
        "family": family.model_dump(mode="json"),
        "variant": variant.model_dump(mode="json"),
        "assessment": assessment.model_dump(mode="json"),
        "closest_priors": [prior.model_dump(mode="json") for prior in evidence.priors],
        "instructions": {
            "preserve_family_scientific_intent": True,
            "satisfy_every_distinction_requirement": True,
            "do_not_claim_global_novelty": True,
            "do_not_add_dataset_schema_or_feasibility_facts": True,
        },
    }
    input_digest = stable_hash(packet)
    output = revision_provider.generate_structured(
        system_prompt=_load_prompt(NOVELTY_REVISION_PROMPT_VERSION),
        user_prompt=json.dumps(packet, sort_keys=True, ensure_ascii=False),
        output_model=NoveltyRevisionModelOutput,
    )
    assert_proposal_safe_payload(output.model_dump(mode="json"), context="novelty revision output")
    allowed_cited_prior_ids = {comparison.source_record_id for comparison in assessment.comparisons}
    cited_prior_record_ids = sorted(set(output.cited_prior_record_ids))
    if not cited_prior_record_ids or not set(cited_prior_record_ids) <= allowed_cited_prior_ids:
        raise NoveltyVariantRejection(
            "novelty revision must cite only prior records bound by its assessment"
        )
    revised_seed_id = f"{variant.question_seed_id}-novelty-r1"
    revised_seed = QuestionSeed.model_validate(
        {
            **output.revised_seed.model_dump(mode="python"),
            "question_seed_id": revised_seed_id,
            "context_id": variant.seed.context_id,
            "origin_provider_id": variant.seed.origin_provider_id,
            "prompt_version": variant.seed.prompt_version,
            "source_pattern_ids": variant.seed.source_pattern_ids,
            "source_paper_case_ids": variant.seed.source_paper_case_ids,
        }
    )
    revised_variant = QuestionFamilyVariant.model_validate(
        {
            **variant.model_dump(mode="python"),
            "question_seed_id": revised_seed_id,
            "seed": revised_seed,
            "variant_role": output.variant_role,
            "distinction_axes": output.distinction_axes,
            "distinct_from_siblings": output.distinct_from_siblings,
            "source_variant_ids": sorted(set([*variant.source_variant_ids, variant.variant_id])),
        }
    )
    original_digest = stable_hash(variant.seed)
    revised_digest = stable_hash(revised_seed)
    if original_digest == revised_digest:
        raise NoveltyVariantRejection("novelty revision did not change the scientific question")
    revision_payload = {
        "question_family_id": family.question_family_id,
        "original_variant_id": variant.variant_id,
        "revised_variant_id": revised_variant.variant_id,
        "original_question_seed_id": variant.question_seed_id,
        "revised_question_seed_id": revised_seed_id,
        "original_question_digest": original_digest,
        "revised_question_digest": revised_digest,
        "source_assessment_id": assessment.assessment_id,
        "requirements": assessment.distinction_requirements,
        "cited_prior_record_ids": cited_prior_record_ids,
        "intent_preservation_rationale": output.intent_preservation_rationale,
        "revision_provider_id": revision_provider.provider_id,
        "revision_prompt_version": NOVELTY_REVISION_PROMPT_VERSION,
        "revision_input_digest": input_digest,
    }
    return revised_variant, NoveltyRevisionRecord.model_validate(
        {
            "revision_id": f"novelty-revision-{stable_hash(revision_payload)[:16]}",
            **revision_payload,
        }
    )


def run_family_novelty_admission(
    family: QuestionFamily,
    *,
    providers: list[NoveltySearchProvider],
    reviewer: StructuredModelProvider,
    revision_provider: StructuredModelProvider,
    search_cutoff: str | None = None,
    web_grounder: NoveltyWebGrounder | None = None,
    web_lead_resolver: NoveltyWebLeadResolver | None = None,
    fallback_terms: Sequence[str] = (),
) -> FamilyNoveltyAdmissionResult:
    if web_grounder is None and web_lead_resolver is not None:
        raise ValueError("a novelty web lead resolver requires an enabled web grounder")
    if web_grounder is not None and web_lead_resolver is None:
        web_lead_resolver = CrossrefNoveltyLeadResolver()
    cutoff = search_cutoff or datetime.now(UTC).date().isoformat()
    plans: list[NoveltySearchPlan] = []
    packs: list[NoveltyEvidencePack] = []
    assessments: list[VariantNoveltyAssessment] = []
    revisions: list[NoveltyRevisionRecord] = []
    legacy: list[VariantNoveltyResult] = []
    admissions: list[NoveltyVariantAdmission] = []
    admitted_variants: list[QuestionFamilyVariant] = []

    for original in family.variants:
        variant = original
        plan, pack, assessment = _assess_once(
            family,
            variant,
            providers=providers,
            reviewer=reviewer,
            search_cutoff=cutoff,
            web_grounder=web_grounder,
            web_lead_resolver=web_lead_resolver,
            fallback_terms=fallback_terms,
        )
        plans.append(plan)
        packs.append(pack)
        assessments.append(assessment)
        revision_id = ""
        if assessment.verdict == NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED:
            try:
                variant, revision = revise_variant_for_novelty(
                    family,
                    variant,
                    assessment,
                    pack,
                    revision_provider=revision_provider,
                )
            except (
                StructuredModelProviderError,
                ModelConfigurationError,
                NoveltyVariantRejection,
                ValidationError,
            ) as exc:
                # ValidationError and NoveltyVariantRejection joined this handler on 2026-07-26:
                # a revision reply carrying "population scope" instead of "population_scope" raised
                # ValidationError out of the whole per-variant loop, and end_to_end closed the
                # ENTIRE family as deferred_insufficient_evidence. Family qfamily-004 lost its
                # innocent second variant that way, unsearched and unassessed. One variant's reply
                # shape must never decide its sibling's fate.
                assessment = _provider_unavailable_assessment(
                    variant,
                    pack,
                    provider_id=getattr(exc, "provider_id", revision_provider.provider_id),
                    failure_class=_variant_failure_classification(exc),
                )
                assessments.append(assessment)
                revision = None
            if revision is None:
                disposition = _disposition(assessment)
                admissions.append(
                    NoveltyVariantAdmission(
                        variant_id=variant.variant_id,
                        question_seed_id=variant.question_seed_id,
                        assessment_id=assessment.assessment_id,
                        disposition=disposition,
                    )
                )
                legacy.append(_legacy_projection(variant, assessment, pack))
                continue
            plan, pack, assessment = _assess_once(
                family,
                variant,
                providers=providers,
                reviewer=reviewer,
                search_cutoff=cutoff,
                web_grounder=web_grounder,
                web_lead_resolver=web_lead_resolver,
            )
            plans.append(plan)
            packs.append(pack)
            assessments.append(assessment)
            revision = _complete_novelty_revision_recheck(revision, assessment)
            revisions.append(revision)
            revision_id = revision.revision_id

        disposition = _disposition(assessment)
        if disposition == NoveltyVariantDisposition.ADMITTED:
            admitted_variants.append(variant)
        admissions.append(
            NoveltyVariantAdmission(
                variant_id=variant.variant_id,
                question_seed_id=variant.question_seed_id,
                assessment_id=assessment.assessment_id,
                disposition=disposition,
                revision_id=revision_id,
            )
        )
        legacy.append(_legacy_projection(variant, assessment, pack))

    admitted_family = (
        family.model_copy(update={"variants": admitted_variants}, deep=True)
        if admitted_variants
        else None
    )
    if admitted_family is not None:
        admitted_family = QuestionFamily.model_validate(admitted_family.model_dump(mode="python"))
    source_digest = stable_hash(family)
    admitted_digest = stable_hash(admitted_family) if admitted_family is not None else ""
    active_ids = [variant.variant_id for variant in admitted_variants]
    admission_payload = {
        "question_family_id": family.question_family_id,
        "source_family_digest": source_digest,
        "admitted_family_digest": admitted_digest,
        "active_variant_ids": active_ids,
        "variant_admissions": [item.model_dump(mode="json") for item in admissions],
        "family_coherent_after_filtering": bool(active_ids),
        "rationale": (
            "At least one variant passed bounded, evidence-backed novelty admission."
            if active_ids
            else "No variant passed bounded novelty admission; no planning branch may be created."
        ),
    }
    admission = FamilyNoveltyAdmission.model_validate(
        {
            "admission_id": f"family-novelty-{stable_hash(admission_payload)[:16]}",
            **admission_payload,
        }
    )
    return FamilyNoveltyAdmissionResult(
        admitted_family=admitted_family,
        admission=admission,
        search_plans=tuple(plans),
        evidence_packs=tuple(packs),
        assessments=tuple(assessments),
        revisions=tuple(revisions),
        legacy_results=tuple(legacy),
    )


def _complete_novelty_revision_recheck(
    revision: NoveltyRevisionRecord,
    assessment: VariantNoveltyAssessment,
) -> NoveltyRevisionRecord:
    """Bind the one permitted revision to its persisted second search and judge receipt."""

    payload = revision.model_dump(mode="python", exclude={"revision_id"})
    payload.update(
        {
            "recheck_assessment_id": assessment.assessment_id,
            "novelty_recheck_completed": True,
        }
    )
    return NoveltyRevisionRecord(
        revision_id=f"novelty-revision-{stable_hash(payload)[:16]}",
        **payload,
    )


def _assess_once(
    family: QuestionFamily,
    variant: QuestionFamilyVariant,
    *,
    providers: list[NoveltySearchProvider],
    reviewer: StructuredModelProvider,
    search_cutoff: str,
    web_grounder: NoveltyWebGrounder | None,
    web_lead_resolver: NoveltyWebLeadResolver | None,
    fallback_terms: Sequence[str] = (),
) -> tuple[NoveltySearchPlan, NoveltyEvidencePack, VariantNoveltyAssessment]:
    provider_ids = [provider.provider_id for provider in providers]
    plan = build_novelty_search_plan(
        family,
        variant,
        provider_ids=provider_ids,
        search_cutoff=search_cutoff,
        search_terms=build_novelty_search_terms(variant, provider=reviewer),
        fallback_terms=fallback_terms,
    )
    web_resolved_priors: tuple[NoveltyPriorRecord, ...] = ()
    web_receipt_ids: tuple[str, ...] = ()
    web_resolution_ids: tuple[str, ...] = ()
    web_exclusion_ids: tuple[str, ...] = ()
    web_provider_attempt: NoveltyProviderAttempt | None = None
    web_grounding_insufficiency_reason = ""
    if web_grounder is not None:
        request = _build_novelty_web_grounding_request(
            family,
            variant,
            web_grounder=web_grounder,
            search_cutoff=search_cutoff,
        )
        grounding = web_grounder.ground(request)
        web_provider_attempt = _web_provider_attempt(grounding, web_grounder=web_grounder)
        if grounding.can_continue_with_web_evidence:
            if web_lead_resolver is None:  # defensive; public entrypoint supplies it above.
                raise ValueError("completed novelty web grounding has no deterministic resolver")
            web_resolved_priors, resolutions = _resolve_novelty_web_leads(
                grounding,
                web_grounder=web_grounder,
                resolver=web_lead_resolver,
            )
            if grounding.receipt is None:
                raise ValueError("completed novelty web grounding lost its receipt")
            web_receipt_ids = (grounding.receipt.receipt_id,)
            web_resolution_ids = tuple(resolution.resolution_id for resolution in resolutions)
            web_exclusion_ids = tuple(
                exclusion.exclusion_id for exclusion in grounding.receipt.exclusions
            )
        else:
            # This is deliberately an evidence insufficiency, not an exception that restarts a
            # whole Stage D.  The durable pre-call reservation prevents an ambiguous vendor call
            # from being retried; the affected variant closes honestly while siblings continue.
            # The status alone says only that the call did not complete. ``reason`` carries the
            # host-side classification (exception class plus our own finite failure kind, never
            # provider text) that separates an exhausted search ceiling from a rate limit or a
            # timeout — without it a deferral is undiagnosable after the fact, which is how a
            # four-in-twelve failure rate stayed unexplained across a whole live leg.
            classification = f"; {grounding.reason}" if grounding.reason else ""
            web_grounding_insufficiency_reason = (
                "configured web-grounding check did not complete "
                f"({grounding.status.value}{classification}); "
                "this variant was deferred without reissuing it"
            )
    pack = retrieve_novelty_evidence(
        plan,
        providers=providers,
        web_resolved_priors=web_resolved_priors,
        web_receipt_ids=web_receipt_ids,
        web_resolution_ids=web_resolution_ids,
        web_exclusion_ids=web_exclusion_ids,
        web_provider_attempt=web_provider_attempt,
        web_grounding_insufficiency_reason=web_grounding_insufficiency_reason,
    )
    try:
        assessment = review_variant_novelty(variant, pack, reviewer=reviewer)
    except (
        StructuredModelProviderError,
        ModelConfigurationError,
        NoveltyVariantRejection,
        ValidationError,
    ) as exc:
        # Symmetric with the revision handler: a reviewer reply this host refuses closes THIS
        # variant against its own already-built pack. Host invariants inside
        # review_variant_novelty (evidence/question binding, reviewer-identity separation) are
        # deliberately NOT of this type and still escape hard.
        assessment = _provider_unavailable_assessment(
            variant,
            pack,
            provider_id=getattr(exc, "provider_id", reviewer.provider_id),
            failure_class=_variant_failure_classification(exc),
        )
    return plan, pack, assessment


def _web_provider_attempt(
    grounding: NoveltyWebGroundingResult,
    *,
    web_grounder: NoveltyWebGrounder,
) -> NoveltyProviderAttempt:
    """Project the web-scoped receipt state without letting it count as a scholarly lane."""

    receipt = grounding.receipt
    provider_id = (
        f"novelty_web_scout:{receipt.provider_id}:{receipt.model_id}"
        if receipt is not None
        else (
            "novelty_web_scout:"
            f"{web_grounder.config.scout.provider.strip().lower()}:"
            f"{web_grounder.config.scout.model.strip()}"
        )
    )
    if receipt is not None:
        return NoveltyProviderAttempt(
            provider_id=provider_id,
            status=NoveltyProviderAttemptStatus.SUCCEEDED,
            lane=NoveltyEvidenceLane.WEB_DISCOVERY,
            query_ids=[action.action_id for action in receipt.actions],
            response_digests={receipt.receipt_id: receipt.response_digest},
            candidate_count=len(receipt.leads),
        )
    return NoveltyProviderAttempt(
        provider_id=provider_id,
        status=NoveltyProviderAttemptStatus.FAILED,
        lane=NoveltyEvidenceLane.WEB_DISCOVERY,
        error_class=grounding.status.value,
    )


def _provider_failure_classification(exc: BaseException) -> str:
    """Name the failure without quoting the provider.

    The class name alone collapsed a rate limit, a timeout and an unparsable reply into one
    string, and the reader-facing rationale then asserted an outage for all three. The kind is our
    own finite enum, so adding it carries no provider text.
    """

    kind = getattr(exc, "kind", None)
    kind_value = getattr(kind, "value", "")
    name = type(exc).__name__
    return f"{name}[{kind_value}]" if kind_value else name


def _variant_failure_classification(exc: BaseException) -> str:
    """Name the check that closed one variant, without ever quoting the model.

    Three safe sources, in order of precision. ``NoveltyVariantRejection`` messages are constants
    this module authored, so the message itself is the check's name. A ``ValidationError`` is named
    by field location and pydantic error type only -- both are our own schema's identifiers, while
    the exception's rendered message can echo the offending input value and must not be recorded.
    Everything else falls back to the provider classifier.

    Without this the 2026-07-26 family kill recorded nothing but ``ValidationError``, and the
    failing field -- ``distinction_axes`` -- was recoverable only from an out-of-band capture dir.
    """

    if isinstance(exc, NoveltyVariantRejection):
        return f"NoveltyVariantRejection[{exc}]"
    if isinstance(exc, ValidationError):
        fields = sorted(
            {
                f"{'.'.join(str(part) for part in error['loc'])}:{error['type']}"
                for error in exc.errors()
            }
        )
        return f"ValidationError[{'; '.join(fields[:5])}]"
    return _provider_failure_classification(exc)


def _provider_unavailable_assessment(
    variant: QuestionFamilyVariant,
    evidence: NoveltyEvidencePack,
    *,
    provider_id: str,
    failure_class: str,
) -> VariantNoveltyAssessment:
    evidence_digest = stable_hash(evidence)
    payload = {
        "variant": variant.variant_id,
        "question": evidence.question_digest,
        "evidence": evidence_digest,
        "provider": provider_id,
        "failure": failure_class,
    }
    return VariantNoveltyAssessment(
        assessment_id=f"novelty-assessment-{stable_hash(payload)[:16]}",
        question_family_id=evidence.question_family_id,
        variant_id=variant.variant_id,
        question_seed_id=variant.question_seed_id,
        question_digest=evidence.question_digest,
        evidence_pack_id=evidence.evidence_pack_id,
        evidence_pack_digest=evidence_digest,
        verdict=NoveltyVerdict.INSUFFICIENT_SEARCH_EVIDENCE,
        evidence_adequate=False,
        # The prose already said "infrastructure limitation" and every downstream consumer read the
        # VERDICT instead, which is why 97% of non-scientific losses reached the reader wearing a
        # scientific label. `reply_completeness` is the machine-readable version of that sentence.
        reply_completeness=NoveltyReplyCompleteness.NOT_REVIEWED,
        rationale=(
            f"Novelty review could not be completed ({failure_class}); this is an "
            "infrastructure limitation, "
            "not a scientific rejection."
        ),
        reviewer_provider_id=provider_id,
        reviewer_prompt_version=NOVELTY_REVIEWER_PROMPT_VERSION,
        reviewer_input_digest=stable_hash(payload),
        search_cutoff=evidence.search_cutoff,
        web_receipt_ids=evidence.web_receipt_ids,
        web_resolution_ids=evidence.web_resolution_ids,
    )


def _canonicalize_hits(
    hits: list[NoveltySearchHit],
) -> tuple[list[NoveltyPriorRecord], list[NoveltyEvidenceExclusion]]:
    groups: dict[str, list[NoveltySearchHit]] = {}
    for hit in hits:
        key = hit.doi.lower() if hit.doi else _normalized_title(hit.title)
        groups.setdefault(key, []).append(hit)
    records: list[NoveltyPriorRecord] = []
    exclusions: list[NoveltyEvidenceExclusion] = []
    for _key, group in groups.items():
        ranked = sorted(
            group,
            key=lambda hit: (bool(hit.abstract), hit.retrieval_score, len(hit.title)),
            reverse=True,
        )
        best = ranked[0]
        providers = sorted({hit.provider_id for hit in group})
        query_ids = sorted({hit.query_id for hit in group})
        source_id = f"https://doi.org/{best.doi}" if best.doi else best.source_record_id
        safe_hit: NoveltySearchHit | None = None
        for candidate in ranked:
            try:
                assert_proposal_safe_payload(
                    {"title": candidate.title, "abstract_or_excerpt": candidate.abstract},
                    context="novelty prior record",
                )
            except ValueError:
                continue
            safe_hit = candidate
            break
        if safe_hit is None:
            exclusions.append(
                NoveltyEvidenceExclusion(
                    source_record_id=source_id,
                    reason=NoveltyEvidenceExclusionReason.PROPOSAL_FIREWALL,
                    content_digest=stable_hash(
                        {
                            "title": best.title,
                            "abstract_or_excerpt": best.abstract,
                        }
                    ),
                )
            )
            continue
        best = safe_hit
        abstract = best.abstract.strip()
        basis = NoveltyEvidenceBasis.ABSTRACT if abstract else NoveltyEvidenceBasis.TITLE_ONLY
        source_id = f"https://doi.org/{best.doi}" if best.doi else best.source_record_id
        payload = {
            "source_record_id": source_id,
            "title": best.title,
            "year": best.year,
            "doi": best.doi,
            "url": best.url,
            "providers": providers,
            "query_ids": query_ids,
            "evidence_basis": basis.value,
            "scholarly_identity": _scholarly_identity(best, providers).value,
            "abstract_or_excerpt": abstract,
        }
        records.append(
            NoveltyPriorRecord.model_validate(
                {
                    **payload,
                    "evidence_digest": stable_hash(payload),
                    "retrieval_scores": {
                        provider: max(
                            hit.retrieval_score for hit in group if hit.provider_id == provider
                        )
                        for provider in providers
                    },
                }
            )
        )
    records.sort(
        key=lambda record: (
            -max(record.retrieval_scores.values(), default=0.0),
            record.title.lower(),
        )
    )
    return records, exclusions


def _scholarly_identity(
    hit: NoveltySearchHit,
    providers: list[str],
) -> NoveltyScholarlyIdentity:
    if hit.doi:
        return NoveltyScholarlyIdentity.DOI
    if "openalex" in providers:
        return NoveltyScholarlyIdentity.OPENALEX
    if "crossref" in providers:
        return NoveltyScholarlyIdentity.CROSSREF
    return NoveltyScholarlyIdentity.UNVERIFIED


def _disposition(assessment: VariantNoveltyAssessment) -> NoveltyVariantDisposition:
    """The variant's outcome, which is not the same question as what the literature said.

    A reviewer that never answered has made no finding about the literature at all. Reading only the
    verdict is what let 97% of non-scientific losses reach the reader wearing a scientific label,
    and why only 9 of 51 `insufficient_search_evidence` verdicts across 23 runs were genuine.
    """
    if assessment.reply_completeness is NoveltyReplyCompleteness.NOT_REVIEWED:
        return NoveltyVariantDisposition.NOT_ASSESSED_INFRASTRUCTURE
    return {
        NoveltyVerdict.NO_DIRECT_RECAP_FOUND_IN_SCOPE: NoveltyVariantDisposition.ADMITTED,
        NoveltyVerdict.DIRECT_RECAP: NoveltyVariantDisposition.REJECTED_DIRECT_RECAP,
        NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED: NoveltyVariantDisposition.DEFERRED_CLOSE_PRIOR,
        NoveltyVerdict.INSUFFICIENT_SEARCH_EVIDENCE: (
            NoveltyVariantDisposition.DEFERRED_INSUFFICIENT_EVIDENCE
        ),
    }[assessment.verdict]


def _legacy_projection(
    variant: QuestionFamilyVariant,
    assessment: VariantNoveltyAssessment,
    evidence: NoveltyEvidencePack,
) -> VariantNoveltyResult:
    status = {
        NoveltyVerdict.DIRECT_RECAP: VariantNoveltyStatus.DIRECT_RECAP,
        NoveltyVerdict.CLOSE_PRIOR_REVISION_REQUIRED: VariantNoveltyStatus.POSSIBLE_CLOSE_PRIOR,
        NoveltyVerdict.NO_DIRECT_RECAP_FOUND_IN_SCOPE: (
            VariantNoveltyStatus.NO_CLOSE_PRIOR_FOUND_IN_SEARCH_SCOPE
        ),
        NoveltyVerdict.INSUFFICIENT_SEARCH_EVIDENCE: (
            VariantNoveltyStatus.INSUFFICIENT_RETRIEVAL_EVIDENCE
        ),
    }[assessment.verdict]
    return VariantNoveltyResult(
        variant_id=variant.variant_id,
        question_seed_id=variant.question_seed_id,
        status=status,
        query="",
        providers=[attempt.provider_id for attempt in evidence.provider_attempts],
        knowledge_cutoff=evidence.search_cutoff,
        nearest_source_ids=[prior.source_record_id for prior in evidence.priors],
        nearest_candidates=[
            NearestPriorCandidate(
                source_record_id=prior.source_record_id,
                title=prior.title,
                similarity=max(prior.retrieval_scores.values(), default=0.0),
                url=prior.url,
                doi=prior.doi,
            )
            for prior in evidence.priors[:5]
        ],
        rationale=assessment.rationale,
    )


def _normalized_title(value: str) -> str:
    return " ".join(part for part in sanitize_novelty_query(value).lower().split() if part)


def _load_prompt(version: str) -> str:
    return resolve_asset(Path("prompts") / f"{version}.md").read_text(encoding="utf-8")
