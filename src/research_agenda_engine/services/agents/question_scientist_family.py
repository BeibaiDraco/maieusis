from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
    model_validator,
)
from pydantic.json_schema import SkipJsonSchema

from ...assets import resolve_asset
from ...io import dump_data, load_model
from ...provenance import stable_hash
from ...providers.models.base import (
    StructuredModelFailureKind,
    StructuredModelProvider,
    StructuredModelProviderError,
)
from ...schemas._r5_firewall import (
    FIREWALL_REJECTION_MARKER as _FIREWALL_REJECTION_MARKER,
)
from ...schemas._r5_firewall import assert_proposal_safe_payload
from ...schemas.front_half_authority import FrontHalfAuthorityCeiling
from ...schemas.question_family import (
    QuestionFamily,
    QuestionFamilyBatch,
    QuestionFamilyEnsembleManifest,
    QuestionFamilyGenerationReviewStatus,
    QuestionFamilyProposerBranch,
    QuestionFamilyQualityReport,
    QuestionFamilyQualitySeverity,
    QuestionFamilyQualityWarning,
    QuestionFamilyQualityWarningKind,
    QuestionFamilyReviewDecision,
    QuestionFamilyReviewDecisionBatch,
    QuestionFamilyReviewItem,
    QuestionFamilyReviewPack,
    QuestionFamilyReviewStatus,
    QuestionFamilyShortlistManifest,
    QuestionFamilyVariant,
    QuestionFamilyVariantReviewDecision,
    QuestionFamilyVariantReviewStatus,
    ShortlistedQuestionFamily,
    question_family_batch_content_digest,
)
from ...schemas.question_scientist_context_v2 import QuestionScientistContextPayloadV2
from ...schemas.question_seed import QuestionSeed
from ...schemas.stage_d import StageDCandidateDisposition, StageDProcessedCandidate
from .generation_mirrors import QuestionFamilyModelOutput
from .question_scientist_ensemble import (
    _context_subset_digest,
    _select_pattern_ids,
    _selected_source_case_ids,
)

QUESTION_SCIENTIST_FAMILY_PROMPT_VERSION = "question_scientist/v2"

#: Reply-SHAPED first-call failures a second identical ask can plausibly fix, because the next
#: sample is a different sample. Everything else is deliberately absent: `OUTPUT_TRUNCATED` cannot
#: be fixed by replaying (same packet, same ceiling, same cut -- see `providers/models/base.py`),
#: and the transport/auth/quota kinds are either already retried inside the adapter or are states a
#: duplicate billed call cannot change. Re-asking those would be cost without recourse.
_REASKABLE_FIRST_CALL_KINDS = frozenset(
    {
        StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID,
        StructuredModelFailureKind.INVALID_RESPONSE,
    }
)


#: The blocker kinds ``build_question_family_quality_report`` raises that are HOST machinery rather
#: than a judgement about the science: the proposal firewall, the provenance allowlists, and the
#: structural completeness checks on a family's own required fields. No model reviews a family at
#: this seam -- these are deterministic predicates the host runs over the model's reply -- so a batch
#: emptied by them was never scientifically judged, and recording it as a scientific verdict would
#: make a host bug unrescuable (``schemas/stage_receipt.py:22``; ``resume.py:233`` reuses a
#: scientific terminal instead of re-running it). Every kind that can currently reach BLOCKER
#: severity is listed here; a kind that is NOT listed is treated as a verdict, which is the
#: conservative direction for a reject.
HOST_STRUCTURAL_FAMILY_BLOCKER_KINDS: frozenset[str] = frozenset(
    {
        QuestionFamilyQualityWarningKind.FIREWALL_CHECK.value,
        QuestionFamilyQualityWarningKind.MISSING_PROVENANCE.value,
        QuestionFamilyQualityWarningKind.UNALLOWED_PROVENANCE.value,
        QuestionFamilyQualityWarningKind.WEAK_VARIANT_DISTINCTION.value,
    }
)


class NoValidFamilies(Exception):
    """Stage-D family generation produced no family that passed the quality gates (every family was
    dropped for a blocker). An HONEST zero-families signal — the driver degrades to a stage-D
    terminal, never a bare whole-batch raise.

    ``blocker_kinds`` names WHICH checks emptied the batch, so the driver can classify the terminal
    from the cause instead of from the exception type. An empty ``blocker_kinds`` means no blocker
    dropped anything, so nothing was judged at all."""

    def __init__(
        self,
        message: str,
        *,
        processed_candidates: list[StageDProcessedCandidate],
        blocker_kinds: Sequence[str] = (),
    ):
        self.processed_candidates = list(processed_candidates)
        self.blocker_kinds = list(dict.fromkeys(blocker_kinds))
        super().__init__(message)


class StageDPromptBudgetError(RuntimeError):
    """The code-owned family prompt exceeded its configured hard resource bound."""


def _rejected_fields(exc: BaseException) -> str:
    """Name WHICH fields rejected the reply, using our own schema's identifiers only.

    The corpus's single whole-run kill recorded nothing but "structured_output_invalid" and was
    recovered only by an operator resume ten minutes later. Field location plus pydantic error type
    are our own identifiers; the exception's rendered message can echo the offending input value and
    is deliberately not included.
    """

    errors = getattr(exc, "errors", None)
    if not callable(errors):
        return type(exc).__name__
    try:
        raised = list(errors())
        fields = sorted(
            {f"{'.'.join(str(part) for part in item['loc'])}:{item['type']}" for item in raised}
        )
    except (TypeError, KeyError, AttributeError):
        # A diagnostic must never mask the failure it is describing.
        return type(exc).__name__
    located = "; ".join(fields[:8]) or type(exc).__name__
    # Name the CAUSE when the proposal firewall is what rejected the reply. Without this a vetoed
    # word is reported as `variants.0.seed:value_error` and rendered publicly as "the model's reply
    # did not match the required structure" -- indistinguishable from malformed JSON. A shepherd then
    # burns its bounded per-site repair budget against an invisible cause, which is exactly the
    # visibility failure that makes a break unrecoverable. The offending VALUE is still never echoed:
    # this adds a fixed sentence, never any part of the matched text.
    if any(_FIREWALL_REJECTION_MARKER in str(item.get("msg", "")) for item in raised):
        return f"{located} (a proposal-firewall rule rejected generated prose)"
    return located


class _QuestionScientistSemanticOutputError(ValueError):
    """Schema-shaped model output violated a cross-object semantic invariant."""


@dataclass(frozen=True)
class _UnparsedFamilyCandidate:
    """One family the generation-boundary mirror refused, kept IN PLACE of the parsed object.

    The batch is a single structured parse, so before this existed one family the model rendered
    badly failed the whole `families` list and every well-formed sibling died with it -- at
    `max_families: 6`, six families riding on one all-or-nothing validation while the per-family
    quality filter that would have dropped exactly one of them ran only after the parse succeeded.
    Standing in for the family lets the siblings through and keeps the refusal nameable.
    """

    family_id: str
    detail: str


def _candidate_family_id(value: Any) -> str:
    """The rejected family's own id when it supplied a usable one, else ``""``.

    Model-authored text: bounded, because it becomes a diagnostic filename slug and a Stage-D
    lineage id. Never the reason for the drop -- that is `_rejected_fields` output only.
    """
    if isinstance(value, Mapping):
        raw = value.get("question_family_id")
        if isinstance(raw, str):
            return raw.strip()[:64]
    return ""


def _family_mirror_error(value: Any) -> ValidationError | None:
    """The error the FAMILY mirror alone raises for ``value``, or None if it accepts it.

    The tolerant annotation below is a union, so the wrap handler's own error also carries the
    rejection member's complaints -- one `missing`/`unexpected_keyword_argument` per key of a
    family payload -- which crowds the real cause out of the eight locations `_rejected_fields`
    keeps. Re-running the mirror alone costs one validation on the FAILURE path only and names
    our own schema.
    """
    try:
        QuestionFamilyModelOutput.model_validate(value)
    except ValidationError as exc:
        return exc
    return None


def _tolerate_one_family(value: Any, handler: ValidatorFunctionWrapHandler) -> Any:
    """Validate ONE family, turning a refusal into a named rejection instead of failing the list."""
    try:
        parsed = handler(value)
    except ValidationError:
        parsed = None
    # A REPLY may never produce a rejection. The union's second member exists so this function has
    # somewhere to put its own verdict, and it is two plain strings, so a payload shaped like it
    # validates as one -- which would let the model author the text of a drop reason that travels
    # into a diagnostic rationale and a provider error. Such a payload is just a family that is not
    # a family, and it is refused here in our words.
    if parsed is None or isinstance(parsed, _UnparsedFamilyCandidate):
        error = _family_mirror_error(value)
        return _UnparsedFamilyCandidate(
            family_id=_candidate_family_id(value),
            detail=(
                _rejected_fields(error)
                if error is not None
                else "family payload does not describe a question family"
            ),
        )
    return parsed


#: A family slot that degrades to a named rejection instead of failing its siblings. The rejection
#: member is `SkipJsonSchema`, so the JSON schema this output model sends to the provider stays
#: BYTE-IDENTICAL to the strict `list[QuestionFamilyModelOutput]` it replaces: the model is asked
#: for exactly what it was asked for before, and only our own parse became per-family.
_TolerantFamilyCandidate = Annotated[
    QuestionFamilyModelOutput | SkipJsonSchema[_UnparsedFamilyCandidate],
    WrapValidator(_tolerate_one_family),
]


class _QuestionScientistFamilyModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    families: list[_TolerantFamilyCandidate] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_family_candidates(self) -> _QuestionScientistFamilyModelOutput:
        if not self.families:
            raise ValueError("Question Scientist v2 output requires at least one family")
        return self


class QuestionFamilyReviewPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack: QuestionFamilyReviewPack
    decision_template: QuestionFamilyReviewDecisionBatch
    markdown: str


class QuestionFamilyReviewImportResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shortlist: QuestionFamilyShortlistManifest | None = None
    errors: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class _FamilyVariantRef:
    family: QuestionFamily
    variant: QuestionFamilyVariant


def generate_question_family_batch(
    *,
    provider: StructuredModelProvider,
    context_payload: QuestionScientistContextPayloadV2,
    family_count: int = 6,
    variants_per_family: int = 3,
    max_prompt_chars: int = 300_000,
    selected_pattern_ids: list[str] | None = None,
    proposer_branch_id: str = "",
    context_subset_digest: str = "",
    on_family_dropped: Callable[[str, list[str]], None] | None = None,
    on_retry_failed: Callable[[str], None] | None = None,
    on_first_call_reasked: Callable[[str], None] | None = None,
    on_valid_batch: Callable[[QuestionFamilyBatch], None] | None = None,
) -> QuestionFamilyBatch:
    if family_count < 1 or family_count > 20:
        raise ValueError("family_count must be between 1 and 20")
    if variants_per_family < 1 or variants_per_family > 8:
        raise ValueError("variants_per_family must be between 1 and 8")
    user_packet = build_question_family_user_packet(
        context_payload,
        family_count=family_count,
        variants_per_family=variants_per_family,
        provider_id=provider.provider_id,
        selected_pattern_ids=selected_pattern_ids,
        proposer_branch_id=proposer_branch_id,
        context_subset_digest=context_subset_digest,
    )
    user_prompt = json.dumps(user_packet, sort_keys=True, ensure_ascii=False)
    if len(user_prompt) > max_prompt_chars:
        raise StageDPromptBudgetError(
            "Question Scientist family context packet exceeds prompt budget"
        )
    system_prompt = _load_prompt(QUESTION_SCIENTIST_FAMILY_PROMPT_VERSION)
    input_digest = stable_hash(user_packet)

    def _generate() -> tuple[QuestionFamilyBatch | None, list[StageDProcessedCandidate]]:
        try:
            output = provider.generate_structured(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                output_model=_QuestionScientistFamilyModelOutput,
            )
        except (TypeError, AssertionError, StructuredModelProviderError):
            raise
        except ValidationError as exc:
            raise StructuredModelProviderError(
                StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=provider.provider_id,
                detail=_rejected_fields(exc),
            ) from exc
        try:
            return _force_question_family_batch(
                output,
                context_payload=context_payload,
                provider_id=provider.provider_id,
                input_digest=input_digest,
            )
        except (TypeError, AssertionError):
            raise
        except (ValidationError, _QuestionScientistSemanticOutputError) as exc:
            # Per-FAMILY rejections never reach here any more: the force step drops them one at a
            # time. What is left is a genuinely batch-level invariant, and it keeps the finite
            # provider-error shape that `_classify_stage_d_failure` knows how to file.
            raise StructuredModelProviderError(
                StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=provider.provider_id,
                detail=_rejected_fields(exc),
            ) from exc

    # N3: WHICH checks dropped candidates, not just how the drop read. `reason_codes` carries the
    # human message; the driver needs the kind to tell a host structural refusal from a judgement
    # about the science, and it must not have to pattern-match prose to do it.
    quality_blocker_kinds: list[str] = []

    def _quality_filter(
        candidate_batch: QuestionFamilyBatch,
    ) -> tuple[QuestionFamilyBatch, list[StageDProcessedCandidate]]:
        clean_families: list[QuestionFamily] = []
        processed: list[StageDProcessedCandidate] = []
        for family in candidate_batch.families:
            single = candidate_batch.model_copy(update={"families": [family]})
            report = build_question_family_quality_report(
                single,
                allowed_pattern_ids=user_packet["allowed_pattern_ids"],
                allowed_topic_claim_ids=user_packet["allowed_topic_claim_ids"],
                allowed_topic_pack_ids=user_packet.get("allowed_topic_pack_ids"),
                allowed_dataset_context_ids=user_packet["allowed_dataset_context_ids"],
            )
            blocking_warnings = [
                warning
                for warning in report.warnings
                if warning.severity == QuestionFamilyQualitySeverity.BLOCKER
            ]
            blockers = [warning.message for warning in blocking_warnings]
            quality_blocker_kinds.extend(warning.kind.value for warning in blocking_warnings)
            if blockers:
                processed.append(
                    StageDProcessedCandidate(
                        question_family_id=family.question_family_id,
                        disposition=StageDCandidateDisposition.QUALITY_DROPPED,
                        reason_codes=blockers,
                    )
                )
                if on_family_dropped is not None:
                    on_family_dropped(family.question_family_id, blockers)
                continue
            clean_families.append(family)
            processed.append(
                StageDProcessedCandidate(
                    question_family_id=family.question_family_id,
                    disposition=StageDCandidateDisposition.RETAINED,
                )
            )
        return candidate_batch.model_copy(update={"families": clean_families}), processed

    def _attempt() -> tuple[QuestionFamilyBatch, list[StageDProcessedCandidate]]:
        """One provider call: tolerant per-family parse, then the per-family quality filter.

        Every family that does not survive either step leaves a drop record, so the two stages
        report one continuous lineage and no candidate is silently lost.
        """
        raw, parse_dropped = _generate()
        for dropped in parse_dropped:
            if on_family_dropped is not None:
                on_family_dropped(dropped.question_family_id, dropped.reason_codes)
        if raw is None:
            # NOT ONE family survived the generation boundary. That is a reply the schema refused,
            # which is what it was before this change and what it must stay: a schema terminal a
            # resume and a shepherd can act on, never a scientific verdict, because no gate judged
            # anything here. Tolerance is for a batch with survivors; a batch with none is unusable.
            raise StructuredModelProviderError(
                StructuredModelFailureKind.STRUCTURED_OUTPUT_INVALID,
                provider_id=provider.provider_id,
                detail=_no_family_survived_detail(parse_dropped),
            )
        filtered, quality_processed = _quality_filter(raw)
        return filtered, [*parse_dropped, *quality_processed]

    # ONE bounded re-ask for the whole call, spent on whichever need arises first. The corpus's
    # single whole-run Stage-D kill (nlb6 20260724T230141Z, `structured_output_invalid`) died on an
    # unguarded first call while a re-ask sat further down this same function; the budget is where
    # it always was, two provider calls, and now the first call can reach it.
    reask_spent = False
    try:
        batch, processed = _attempt()
    except StructuredModelProviderError as exc:
        if exc.kind not in _REASKABLE_FIRST_CALL_KINDS:
            raise
        reask_spent = True
        if on_first_call_reasked is not None:
            on_first_call_reasked(exc.kind.value)
        batch, processed = _attempt()
    if batch.families and on_valid_batch is not None:
        on_valid_batch(batch)
    retained = len(batch.families)
    # D6(a): tolerate an under-count instead of raising for the whole batch. Allow AT MOST ONE bounded
    # re-ask when the model returned fewer families than requested; then proceed with whatever is valid.
    if retained < family_count:
        if not reask_spent:
            try:
                retry, retry_processed = _attempt()
            except (StructuredModelProviderError, StageDPromptBudgetError) as exc:
                if retained == 0:
                    raise
                if on_retry_failed is not None:
                    kind = (
                        exc.kind.value
                        if isinstance(exc, StructuredModelProviderError)
                        else "prompt_budget"
                    )
                    on_retry_failed(kind)
            else:
                processed.extend(retry_processed)
                if len(retry.families) > retained:
                    batch = retry
                    retained = len(retry.families)
        if on_family_dropped is not None and retained < family_count:
            on_family_dropped(
                "shape",
                [f"family undercount: requested {family_count}, got {retained}"],
            )
    if not batch.families:
        raise NoValidFamilies(
            "QuestionFamilyBatch produced no family that passed the quality gates",
            processed_candidates=_unique_processed_candidates(processed),
            blocker_kinds=quality_blocker_kinds,
        )
    return batch


def _unique_processed_candidates(
    candidates: list[StageDProcessedCandidate],
) -> list[StageDProcessedCandidate]:
    """Collapse retry observations into one coherent lineage row per model-supplied family ID."""
    by_id: dict[str, StageDProcessedCandidate] = {}
    for candidate in candidates:
        existing = by_id.get(candidate.question_family_id)
        if existing is None:
            by_id[candidate.question_family_id] = candidate.model_copy(deep=True)
            continue
        if existing.disposition != candidate.disposition:
            raise AssertionError("Stage-D retry produced contradictory disposition lineage")
        existing.reason_codes = list(
            dict.fromkeys([*existing.reason_codes, *candidate.reason_codes])
        )
    return list(by_id.values())


def build_question_family_user_packet(
    context_payload: QuestionScientistContextPayloadV2,
    *,
    family_count: int,
    variants_per_family: int,
    provider_id: str,
    selected_pattern_ids: list[str] | None = None,
    proposer_branch_id: str = "",
    context_subset_digest: str = "",
) -> dict[str, Any]:
    context_payload_dict = context_payload.model_dump(mode="json")
    all_pattern_cards = context_payload.paperbank_patterns.pattern_cards
    selected_pattern_ids = selected_pattern_ids or [card.pattern_id for card in all_pattern_cards]
    selected_pattern_set = set(selected_pattern_ids)
    selected_pattern_cards = [
        card for card in all_pattern_cards if card.pattern_id in selected_pattern_set
    ]
    if not selected_pattern_cards:
        raise ValueError("Question Scientist family proposer branch selected no pattern cards")
    pattern_ids = [card.pattern_id for card in selected_pattern_cards]
    context_payload_dict["paperbank_patterns"] = {
        **context_payload_dict["paperbank_patterns"],
        "pattern_cards": [card.model_dump(mode="json") for card in selected_pattern_cards],
    }
    topic_claim_ids = [claim.claim_id for claim in context_payload.topic_literature.claim_cards]
    topic_source_record_ids = [
        source.source_record_id for source in context_payload.topic_literature.source_cards
    ]
    dataset_context_ids = _dataset_context_ids(context_payload)
    instructions: dict[str, Any] = {
        "return_only": "QuestionFamilyBatch.families payload via structured output",
        "generate_question_families_directly": True,
        "do_not_cluster_individual_seeds_after_generation": True,
        "do_not_generate_question_cards": True,
        "do_not_generate_analysis_contracts": True,
        "do_not_create_branches_or_execution_artifacts": True,
        "do_not_claim_dataset_feasibility": True,
        "exact_schema_or_column_details_forbidden": True,
        "positive_negative_null_consequences_required_for_every_variant": True,
        "semantic_distinction_axes_allowed": [
            "theoretical_tension",
            "target_contrast",
            "discriminating_observation",
            "claim_level",
            "population_scope",
            "outcome_meaning",
        ],
        "each_variant_must_explain_distinct_from_siblings": True,
    }
    if proposer_branch_id:
        instructions["respect_proposer_branch_pattern_subset"] = True
    packet = {
        "prompt_version": QUESTION_SCIENTIST_FAMILY_PROMPT_VERSION,
        "context_id": context_payload.context_id,
        "context_digest": context_payload.context_digest,
        "proposer_branch_id": proposer_branch_id,
        "context_subset_digest": context_subset_digest,
        "origin_provider_id": provider_id,
        "family_count_requested": family_count,
        "variants_per_family_requested": variants_per_family,
        "allowed_pattern_ids": pattern_ids,
        "allowed_topic_claim_ids": topic_claim_ids,
        "allowed_topic_source_record_ids": topic_source_record_ids,
        "allowed_dataset_context_ids": dataset_context_ids,
        "context_payload": context_payload_dict,
        "instructions": instructions,
    }
    if context_payload.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION:
        packet["allowed_topic_pack_ids"] = [context_payload.topic_literature.topic_pack_id]
        instructions["provisional_inspiration_authority_ceiling"] = True
        instructions["topic_claim_provenance_may_be_empty"] = True
        instructions["bind_real_topic_pack_id"] = True
    return packet


def write_question_family_batch(
    batch: QuestionFamilyBatch,
    *,
    corpus_root: str | Path = "corpus",
) -> Path:
    root = Path(corpus_root) / "question_families"
    return dump_data(batch, root / f"{batch.batch_id}.question_family_batch.yaml")


def write_question_family_quality_report(
    report: QuestionFamilyQualityReport,
    *,
    corpus_root: str | Path = "corpus",
) -> Path:
    root = Path(corpus_root) / "question_families" / "quality"
    return dump_data(report, root / f"{report.quality_report_id}.question_family_quality.yaml")


def build_question_family_quality_report(
    batch: QuestionFamilyBatch,
    *,
    allowed_pattern_ids: list[str] | None = None,
    allowed_topic_claim_ids: list[str] | None = None,
    allowed_topic_pack_ids: list[str] | None = None,
    allowed_dataset_context_ids: list[str] | None = None,
) -> QuestionFamilyQualityReport:
    warnings: list[QuestionFamilyQualityWarning] = []
    warning_index = 1
    allowed_pattern_set = set(allowed_pattern_ids) if allowed_pattern_ids is not None else None
    allowed_topic_claim_set = (
        set(allowed_topic_claim_ids) if allowed_topic_claim_ids is not None else None
    )
    allowed_topic_pack_set = (
        set(allowed_topic_pack_ids) if allowed_topic_pack_ids is not None else None
    )
    allowed_dataset_context_set = (
        set(allowed_dataset_context_ids) if allowed_dataset_context_ids is not None else None
    )
    allowlist_payload = (
        {
            "allowed_pattern_ids": sorted(allowed_pattern_ids),
            "allowed_topic_claim_ids": sorted(allowed_topic_claim_ids),
            "allowed_dataset_context_ids": sorted(allowed_dataset_context_ids),
        }
        if allowed_pattern_ids is not None
        and allowed_topic_claim_ids is not None
        and allowed_dataset_context_ids is not None
        else None
    )
    if allowlist_payload is not None and allowed_topic_pack_ids is not None:
        allowlist_payload["allowed_topic_pack_ids"] = sorted(allowed_topic_pack_ids)
    allowlist_digest = stable_hash(allowlist_payload) if allowlist_payload is not None else ""

    def add_warning(
        *,
        severity: QuestionFamilyQualitySeverity,
        kind: QuestionFamilyQualityWarningKind,
        message: str,
        family_id: str = "",
        variant_ids: list[str] | None = None,
    ) -> None:
        nonlocal warning_index
        warnings.append(
            QuestionFamilyQualityWarning(
                warning_id=f"qfamily-quality-{warning_index:03d}",
                severity=severity,
                kind=kind,
                message=message,
                question_family_id=family_id,
                variant_ids=variant_ids or [],
            )
        )
        warning_index += 1

    try:
        assert_proposal_safe_payload(batch.model_dump(mode="python"), context="QuestionFamilyBatch")
    except ValueError as exc:
        add_warning(
            severity=QuestionFamilyQualitySeverity.BLOCKER,
            kind=QuestionFamilyQualityWarningKind.FIREWALL_CHECK,
            message=str(exc),
        )
    for family in batch.families:
        if not family.source_pattern_ids:
            add_warning(
                severity=QuestionFamilyQualitySeverity.BLOCKER,
                kind=QuestionFamilyQualityWarningKind.MISSING_PROVENANCE,
                message="Family is missing source pattern provenance.",
                family_id=family.question_family_id,
            )
        if allowed_pattern_set is not None:
            unallowed_family_pattern_ids = sorted(
                set(family.source_pattern_ids) - allowed_pattern_set
            )
            if unallowed_family_pattern_ids:
                add_warning(
                    severity=QuestionFamilyQualitySeverity.BLOCKER,
                    kind=QuestionFamilyQualityWarningKind.UNALLOWED_PROVENANCE,
                    message=(
                        "Family cites pattern provenance outside the proposer packet: "
                        + ", ".join(unallowed_family_pattern_ids)
                    ),
                    family_id=family.question_family_id,
                )
        if (
            not family.source_topic_claim_ids
            and family.authority_ceiling != FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
        ):
            add_warning(
                severity=QuestionFamilyQualitySeverity.BLOCKER,
                kind=QuestionFamilyQualityWarningKind.MISSING_PROVENANCE,
                message="Family is missing topic claim provenance.",
                family_id=family.question_family_id,
            )
        if allowed_topic_claim_set is not None:
            unallowed_topic_claim_ids = sorted(
                set(family.source_topic_claim_ids) - allowed_topic_claim_set
            )
            if unallowed_topic_claim_ids:
                add_warning(
                    severity=QuestionFamilyQualitySeverity.BLOCKER,
                    kind=QuestionFamilyQualityWarningKind.UNALLOWED_PROVENANCE,
                    message=(
                        "Family cites topic claim provenance outside the proposer packet: "
                        + ", ".join(unallowed_topic_claim_ids)
                    ),
                    family_id=family.question_family_id,
                )
        if family.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION:
            if not family.source_topic_pack_ids:
                add_warning(
                    severity=QuestionFamilyQualitySeverity.BLOCKER,
                    kind=QuestionFamilyQualityWarningKind.MISSING_PROVENANCE,
                    message="Provisional family is missing topic-pack provenance.",
                    family_id=family.question_family_id,
                )
            elif allowed_topic_pack_set is not None:
                foreign_pack_ids = sorted(
                    set(family.source_topic_pack_ids) - allowed_topic_pack_set
                )
                if foreign_pack_ids:
                    add_warning(
                        severity=QuestionFamilyQualitySeverity.BLOCKER,
                        kind=QuestionFamilyQualityWarningKind.UNALLOWED_PROVENANCE,
                        message=(
                            "Provisional family cites topic-pack provenance outside the proposer "
                            "packet: " + ", ".join(foreign_pack_ids)
                        ),
                        family_id=family.question_family_id,
                    )
        if not family.source_dataset_context_ids:
            add_warning(
                severity=QuestionFamilyQualitySeverity.BLOCKER,
                kind=QuestionFamilyQualityWarningKind.MISSING_PROVENANCE,
                message="Family is missing dataset context provenance.",
                family_id=family.question_family_id,
            )
        if allowed_dataset_context_set is not None:
            unallowed_dataset_context_ids = sorted(
                set(family.source_dataset_context_ids) - allowed_dataset_context_set
            )
            if unallowed_dataset_context_ids:
                add_warning(
                    severity=QuestionFamilyQualitySeverity.BLOCKER,
                    kind=QuestionFamilyQualityWarningKind.UNALLOWED_PROVENANCE,
                    message=(
                        "Family cites dataset context provenance outside the proposer packet: "
                        + ", ".join(unallowed_dataset_context_ids)
                    ),
                    family_id=family.question_family_id,
                )
        if _word_count(family.shared_scientific_tension) < 8:
            add_warning(
                severity=QuestionFamilyQualitySeverity.WARNING,
                kind=QuestionFamilyQualityWarningKind.WEAK_VARIANT_DISTINCTION,
                message="Family shared scientific tension is too thin to anchor variants.",
                family_id=family.question_family_id,
            )
        for variant in family.variants:
            if len(variant.seed.competing_explanations) < 2:
                add_warning(
                    severity=QuestionFamilyQualitySeverity.WARNING,
                    kind=QuestionFamilyQualityWarningKind.WEAK_VARIANT_DISTINCTION,
                    message=(
                        "Variant supplies fewer than two explicit competing explanations; "
                        "independent review should assess the scientific contrast."
                    ),
                    family_id=family.question_family_id,
                    variant_ids=[variant.variant_id],
                )
            if allowed_pattern_set is not None:
                unallowed_variant_pattern_ids = sorted(
                    set(variant.seed.source_pattern_ids) - allowed_pattern_set
                )
                if unallowed_variant_pattern_ids:
                    add_warning(
                        severity=QuestionFamilyQualitySeverity.BLOCKER,
                        kind=QuestionFamilyQualityWarningKind.UNALLOWED_PROVENANCE,
                        message=(
                            "Variant seed cites pattern provenance outside the proposer packet: "
                            + ", ".join(unallowed_variant_pattern_ids)
                        ),
                        family_id=family.question_family_id,
                        variant_ids=[variant.variant_id],
                    )
            if _word_count(variant.distinct_from_siblings) < 8:
                add_warning(
                    severity=QuestionFamilyQualitySeverity.WARNING,
                    kind=QuestionFamilyQualityWarningKind.WEAK_VARIANT_DISTINCTION,
                    message="Variant distinction rationale is brief; human review should check it.",
                    family_id=family.question_family_id,
                    variant_ids=[variant.variant_id],
                )
        for left_index, left in enumerate(family.variants):
            for right in family.variants[left_index + 1 :]:
                if _normalized_text(left.seed.question) == _normalized_text(right.seed.question):
                    add_warning(
                        severity=QuestionFamilyQualitySeverity.WARNING,
                        kind=QuestionFamilyQualityWarningKind.POSSIBLE_DUPLICATE_VARIANTS,
                        message="Sibling variants have identical question wording.",
                        family_id=family.question_family_id,
                        variant_ids=[left.variant_id, right.variant_id],
                    )
                    continue
                if _looks_like_wording_only_variant(left, right):
                    add_warning(
                        severity=QuestionFamilyQualitySeverity.WARNING,
                        kind=QuestionFamilyQualityWarningKind.POSSIBLE_DUPLICATE_VARIANTS,
                        message=(
                            "Sibling variants appear to differ mainly by wording and share "
                            "the same distinction axes."
                        ),
                        family_id=family.question_family_id,
                        variant_ids=[left.variant_id, right.variant_id],
                    )
        if len(family.variants) > 1 and not family.non_mergeable_distinctions:
            add_warning(
                severity=QuestionFamilyQualitySeverity.BLOCKER,
                kind=QuestionFamilyQualityWarningKind.WEAK_VARIANT_DISTINCTION,
                message="Multi-variant family lacks non-mergeable distinction grounds.",
                family_id=family.question_family_id,
            )
    content_digest = question_family_batch_content_digest(batch)
    return QuestionFamilyQualityReport(
        quality_report_id=f"question-family-quality-{stable_hash({'batch': batch.batch_id, 'content': content_digest, 'allowlist': allowlist_digest, 'warnings': [warning.model_dump(mode='json') for warning in warnings]})[:12]}",
        batch_id=batch.batch_id,
        context_id=batch.context_id,
        context_digest=batch.context_digest,
        batch_input_digest=batch.input_digest,
        batch_content_digest=content_digest,
        origin_provider_id=batch.origin_provider_id,
        model_id=_model_id_from_provider_id(batch.origin_provider_id),
        prompt_version=batch.prompt_version,
        provenance_allowlist_digest=allowlist_digest,
        warnings=warnings,
        passed_firewall=not any(
            warning.kind == QuestionFamilyQualityWarningKind.FIREWALL_CHECK
            and warning.severity == QuestionFamilyQualitySeverity.BLOCKER
            for warning in warnings
        ),
    )


def generate_question_family_ensemble(
    *,
    provider: StructuredModelProvider,
    context_payload: QuestionScientistContextPayloadV2,
    branches: int = 3,
    families_per_branch: int = 4,
    variants_per_family: int = 3,
    corpus_root: str | Path = "corpus",
) -> QuestionFamilyEnsembleManifest:
    if branches < 3:
        raise ValueError("R5 family ensemble generation requires at least 3 proposer branches")
    if families_per_branch < 1 or families_per_branch > 20:
        raise ValueError("families_per_branch must be between 1 and 20")
    if variants_per_family < 1 or variants_per_family > 8:
        raise ValueError("variants_per_family must be between 1 and 8")
    pattern_ids = [card.pattern_id for card in context_payload.paperbank_patterns.pattern_cards]
    branch_specs: list[tuple[str, list[str], list[str], str]] = []
    seen_subset_digests: set[str] = set()
    for branch_index in range(1, branches + 1):
        proposer_branch_id = f"qfam-proposer-{branch_index:03d}"
        selected_pattern_ids = _select_pattern_ids(pattern_ids, branch_index, branches)
        selected_source_case_ids = _selected_source_case_ids(context_payload, selected_pattern_ids)
        subset_digest = _context_subset_digest(
            context_digest=context_payload.context_digest,
            selected_pattern_ids=selected_pattern_ids,
            selected_source_case_ids=selected_source_case_ids,
        )
        if subset_digest in seen_subset_digests:
            raise ValueError(
                "Question Scientist family ensemble contains duplicate scientific context subsets"
            )
        seen_subset_digests.add(subset_digest)
        branch_specs.append(
            (
                proposer_branch_id,
                selected_pattern_ids,
                selected_source_case_ids,
                subset_digest,
            )
        )
    proposer_branches: list[QuestionFamilyProposerBranch] = []
    for (
        proposer_branch_id,
        selected_pattern_ids,
        selected_source_case_ids,
        subset_digest,
    ) in branch_specs:
        batch = generate_question_family_batch(
            provider=provider,
            context_payload=context_payload,
            family_count=families_per_branch,
            variants_per_family=variants_per_family,
            selected_pattern_ids=selected_pattern_ids,
            proposer_branch_id=proposer_branch_id,
            context_subset_digest=subset_digest,
        )
        batch = _rename_ensemble_family_ids(batch, proposer_branch_id)
        quality_report = build_question_family_quality_report(
            batch,
            allowed_pattern_ids=selected_pattern_ids,
            allowed_topic_claim_ids=_topic_claim_ids(context_payload),
            allowed_dataset_context_ids=_dataset_context_ids(context_payload),
        )
        if quality_report.blocker_count:
            messages = [
                warning.message
                for warning in quality_report.warnings
                if warning.severity == QuestionFamilyQualitySeverity.BLOCKER
            ]
            raise ValueError(
                f"{proposer_branch_id} produced a blocked QuestionFamilyBatch: "
                + "; ".join(messages)
            )
        batch_path = write_question_family_batch(batch, corpus_root=corpus_root)
        quality_report_path = write_question_family_quality_report(
            quality_report,
            corpus_root=corpus_root,
        )
        proposer_branches.append(
            QuestionFamilyProposerBranch(
                proposer_branch_id=proposer_branch_id,
                context_id=context_payload.context_id,
                context_digest=context_payload.context_digest,
                context_subset_digest=subset_digest,
                selected_pattern_ids=selected_pattern_ids,
                selected_source_paper_case_ids=selected_source_case_ids,
                family_count_requested=families_per_branch,
                variants_per_family=variants_per_family,
                batch_id=batch.batch_id,
                batch_path=str(batch_path.resolve()),
                quality_report_id=quality_report.quality_report_id,
                quality_report_path=str(quality_report_path.resolve()),
                origin_provider_id=batch.origin_provider_id,
                prompt_version=batch.prompt_version,
                input_digest=batch.input_digest,
            )
        )
    ensemble = QuestionFamilyEnsembleManifest(
        ensemble_id=f"question-family-ensemble-{stable_hash([branch.model_dump(mode='json') for branch in proposer_branches])[:12]}",
        context_id=context_payload.context_id,
        context_digest=context_payload.context_digest,
        prompt_version=QUESTION_SCIENTIST_FAMILY_PROMPT_VERSION,
        proposer_branches=proposer_branches,
    )
    write_question_family_ensemble_manifest(ensemble, corpus_root=corpus_root)
    return ensemble


def write_question_family_ensemble_manifest(
    manifest: QuestionFamilyEnsembleManifest,
    *,
    corpus_root: str | Path = "corpus",
) -> Path:
    root = Path(corpus_root) / "question_families" / "ensemble"
    return dump_data(manifest, root / f"{manifest.ensemble_id}.question_family_ensemble.yaml")


def load_question_family_batches_from_ensemble(
    manifest: QuestionFamilyEnsembleManifest,
) -> list[QuestionFamilyBatch]:
    return [
        load_model(Path(branch.batch_path), QuestionFamilyBatch)
        for branch in manifest.proposer_branches
    ]


def load_question_family_quality_reports_from_ensemble(
    manifest: QuestionFamilyEnsembleManifest,
) -> list[QuestionFamilyQualityReport]:
    return [
        load_model(Path(branch.quality_report_path), QuestionFamilyQualityReport)
        for branch in manifest.proposer_branches
    ]


def prepare_question_family_review(
    *,
    batches: list[QuestionFamilyBatch],
    ensemble_manifest: QuestionFamilyEnsembleManifest | None = None,
    quality_reports: list[QuestionFamilyQualityReport] | None = None,
    source_consolidation_plan_id: str = "",
    source_consolidation_review_report_id: str = "",
    consolidation_blocker_count: int = 0,
    consolidation_warning_summaries: list[str] | None = None,
) -> QuestionFamilyReviewPreparation:
    if not batches:
        raise ValueError("QuestionFamily review pack requires at least one batch")
    context_ids = {batch.context_id for batch in batches}
    context_digests = {batch.context_digest for batch in batches}
    if len(context_ids) != 1 or len(context_digests) != 1:
        raise ValueError("QuestionFamily review batches must share context_id and context_digest")
    source_batch_ids = [batch.batch_id for batch in batches]
    if len(source_batch_ids) != len(set(source_batch_ids)):
        raise ValueError("QuestionFamily review batches must have unique batch IDs")
    if quality_reports is None:
        if ensemble_manifest is not None:
            quality_reports = load_question_family_quality_reports_from_ensemble(ensemble_manifest)
        else:
            raise ValueError(
                "QuestionFamily review requires persisted allowlist-bound quality reports"
            )
    report_by_batch = {report.batch_id: report for report in quality_reports}
    if set(report_by_batch) != set(source_batch_ids):
        raise ValueError("QuestionFamily review requires one quality report per source batch")
    for batch in batches:
        _validate_quality_report_matches_batch(report_by_batch[batch.batch_id], batch)
    blocked_reports = sorted(
        report.batch_id
        for report in quality_reports
        if report.blocker_count or not report.passed_firewall
    )
    if blocked_reports:
        raise ValueError(
            "QuestionFamily review pack cannot be built from blocked quality reports: "
            + ", ".join(blocked_reports)
        )
    branch_by_batch = (
        {branch.batch_id: branch for branch in ensemble_manifest.proposer_branches}
        if ensemble_manifest
        else {}
    )
    batch_by_id = {batch.batch_id: batch for batch in batches}
    families: list[tuple[QuestionFamily, str, QuestionFamilyProposerBranch | None]] = []
    for batch in batches:
        for family in batch.families:
            families.append((family, batch.batch_id, branch_by_batch.get(batch.batch_id)))
    items = [
        QuestionFamilyReviewItem(
            review_item_id=f"family-review-candidate-{index:03d}",
            family=family,
            source_batch_id=batch_id,
            proposer_branch_id=branch.proposer_branch_id if branch else "",
            input_digest=batch_by_id[batch_id].input_digest,
            context_subset_digest=branch.context_subset_digest if branch else "",
            origin_provider_id=batch_by_id[batch_id].origin_provider_id,
            model_id=_model_id_from_provider_id(batch_by_id[batch_id].origin_provider_id),
            prompt_version=batch_by_id[batch_id].prompt_version,
            quality_warning_ids=[
                warning.warning_id
                for warning in report_by_batch[batch_id].warnings
                if warning.question_family_id == family.question_family_id
            ],
            auto_flags=[
                f"{warning.severity.value}:{warning.kind.value}"
                for warning in report_by_batch[batch_id].warnings
                if warning.question_family_id == family.question_family_id
            ],
        )
        for index, (family, batch_id, branch) in enumerate(families, start=1)
    ]
    pack = QuestionFamilyReviewPack(
        pack_id=f"question-family-review-{stable_hash([item.family.model_dump(mode='json') for item in items])[:12]}",
        context_id=next(iter(context_ids)),
        context_digest=next(iter(context_digests)),
        source_batch_ids=source_batch_ids,
        source_ensemble_id=ensemble_manifest.ensemble_id if ensemble_manifest else "",
        quality_reports=quality_reports,
        items=items,
        source_consolidation_plan_id=source_consolidation_plan_id,
        source_consolidation_review_report_id=source_consolidation_review_report_id,
        consolidation_blocker_count=consolidation_blocker_count,
        consolidation_warning_summaries=consolidation_warning_summaries or [],
        instructions=[
            "Review each family for scientific value, coherence, and whether the variants are genuinely distinct.",
            "Shortlisting represents scientific value only; it does not certify dataset feasibility.",
            "Within shortlisted families, mark only scientifically useful, non-mergeable variants as active.",
            "Reject or revise families whose variants differ only by wording or lack positive/negative/null consequences.",
            "This import must not create QuestionBranches, QuestionCards, AnalysisContracts, or execution artifacts.",
        ],
    )
    decisions = QuestionFamilyReviewDecisionBatch(
        decision_batch_id=f"{pack.pack_id}-decisions-template",
        pack_id=pack.pack_id,
        decisions=[
            QuestionFamilyReviewDecision(
                review_item_id=item.review_item_id,
                question_family_id=item.family.question_family_id,
                variant_decisions=[
                    QuestionFamilyVariantReviewDecision(
                        variant_id=variant.variant_id,
                        question_seed_id=variant.question_seed_id,
                    )
                    for variant in item.family.variants
                ],
            )
            for item in items
        ],
    )
    return QuestionFamilyReviewPreparation(
        pack=pack,
        decision_template=decisions,
        markdown=render_question_family_review_markdown(pack),
    )


def render_question_family_review_markdown(pack: QuestionFamilyReviewPack) -> str:
    family_labels = {
        item.family.question_family_id: f"Family {index:03d}"
        for index, item in enumerate(pack.items, start=1)
    }
    lines = [
        f"# QuestionFamily Review Pack: {pack.pack_id}",
        "",
        "Boundary: this pack supports human scientific shortlisting only. It does not "
        "certify dataset feasibility, create QuestionFamilyBranches, generate "
        "QuestionCards, or authorize AnalysisContracts/execution.",
        "",
        f"- Families for review: {len(pack.items)}",
        f"- Blind review: {'yes' if pack.blind_review else 'no'}",
        f"- Consolidated candidate pool: {'yes' if pack.source_consolidation_plan_id else 'no'}",
        "",
        "## Review Instructions",
        "",
        *[f"- {instruction}" for instruction in pack.instructions],
        "",
    ]
    if pack.consolidation_warning_summaries:
        lines.extend(
            [
                "## Consolidation Reviewer Warnings",
                "",
                *[f"- {warning}" for warning in pack.consolidation_warning_summaries],
                "",
            ]
        )
    for item in pack.items:
        family = item.family
        family_label = family_labels[family.question_family_id]
        lines.extend(
            [
                f"## {family_label}: {family.title}",
                "",
                f"- Review item ID: `{item.review_item_id}`",
                f"- Variants: {len(family.variants)}",
                "",
                "### Family Summary",
                "",
                family.summary,
                "",
                "### Shared Scientific Tension",
                "",
                family.shared_scientific_tension,
                "",
                "### Semantic Axes",
                "",
                *[f"- {axis}" for axis in family.semantic_axes],
                "",
                "### Non-Mergeable Distinctions",
                "",
                *[f"- {distinction}" for distinction in family.non_mergeable_distinctions],
                "",
                "### Proposal-Stage Uncertainty And Assumptions",
                "",
                f"- Uncertainties: {'; '.join(family.proposal_stage_uncertainties) or 'none listed'}",
                f"- Dataset assumptions: {'; '.join(family.assumptions_about_dataset) or 'none listed'}",
                "",
            ]
        )
        for variant_index, variant in enumerate(family.variants, start=1):
            seed = variant.seed
            variant_label = f"Variant {variant_index:03d}"
            lines.extend(
                [
                    f"### {variant_label}: {variant.variant_role}",
                    "",
                    f"- Distinction axes: {', '.join(axis.value for axis in variant.distinction_axes)}",
                    f"- Distinct from siblings: {variant.distinct_from_siblings}",
                    "",
                    "#### Question",
                    "",
                    seed.question,
                    "",
                    "#### Scientific Tension",
                    "",
                    seed.scientific_tension,
                    "",
                    "#### Why It Matters",
                    "",
                    seed.why_scientifically_important,
                    "",
                    "#### Dataset Leverage Hypothesis",
                    "",
                    seed.dataset_leverage_hypothesis,
                    "",
                    "#### Competing Explanations",
                    "",
                    *[f"- {value}" for value in seed.competing_explanations],
                    "",
                    "#### Discriminating Observation",
                    "",
                    seed.discriminating_observation,
                    "",
                    "#### Outcome Meanings",
                    "",
                    f"- Positive: {seed.positive_result_consequence}",
                    f"- Negative: {seed.negative_result_consequence}",
                    f"- Null: {seed.null_result_consequence}",
                    "",
                    "#### Ambiguities And Planning Challenges",
                    "",
                    f"- Ambiguous constructs: {'; '.join(seed.ambiguous_constructs) or 'none listed'}",
                    f"- Implementation challenges: {'; '.join(seed.likely_implementation_challenges) or 'none listed'}",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def write_question_family_review_outputs(
    preparation: QuestionFamilyReviewPreparation,
    *,
    corpus_root: str | Path = "corpus",
) -> dict[str, Path]:
    root = Path(corpus_root) / "question_families" / "review"
    pack_path = dump_data(preparation.pack, root / "question_family_review_pack.yaml")
    template_path = dump_data(
        preparation.decision_template,
        root / "question_family_decisions.template.yaml",
    )
    decision_path = dump_data(
        preparation.decision_template,
        root / "question_family_decisions.yaml",
    )
    markdown_path = root / "question_family_review.md"
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(preparation.markdown, encoding="utf-8")
    return {
        "review_pack": pack_path,
        "decision_template": template_path,
        "decisions": decision_path,
        "markdown": markdown_path,
    }


def build_question_family_planning_admission_decisions(
    pack: QuestionFamilyReviewPack,
    *,
    reviewer: str = "planning-admission-policy",
) -> QuestionFamilyReviewDecisionBatch:
    """Admit a blocker-free family review pack for downstream planning only.

    This is not a dataset-feasibility decision. It creates ordinary review
    decisions so the existing import path still records explicit family and
    variant status before any branch runtime exists.
    """
    if pack.consolidation_blocker_count:
        raise ValueError("planning admission requires blocker-free consolidation review")
    blocked_reports = sorted(
        report.batch_id
        for report in pack.quality_reports
        if report.blocker_count or not report.passed_firewall
    )
    if blocked_reports:
        raise ValueError(
            "planning admission requires blocker-free quality reports: "
            + ", ".join(blocked_reports)
        )
    if pack.source_consolidation_plan_id and not pack.source_consolidation_review_report_id:
        raise ValueError("consolidated planning admission requires reviewer report provenance")
    return QuestionFamilyReviewDecisionBatch(
        decision_batch_id=f"{pack.pack_id}-planning-admission",
        pack_id=pack.pack_id,
        expert_reviewer=reviewer,
        decisions=[
            QuestionFamilyReviewDecision(
                review_item_id=item.review_item_id,
                question_family_id=item.family.question_family_id,
                status=QuestionFamilyReviewStatus.SHORTLISTED,
                reviewer=reviewer,
                notes=(
                    "Admitted to downstream owner/planner branch preparation only; "
                    "this does not certify dataset feasibility."
                ),
                scientific_value_notes=(
                    "No deterministic or independent-review blocker is present, "
                    "so this family remains scientifically worth planning."
                ),
                priority=index,
                variant_decisions=[
                    QuestionFamilyVariantReviewDecision(
                        variant_id=variant.variant_id,
                        question_seed_id=variant.question_seed_id,
                        status=QuestionFamilyVariantReviewStatus.ACTIVE,
                        notes=(
                            "Active for planning admission only; downstream planner "
                            "may accept, revise, reject, or escalate with evidence."
                        ),
                    )
                    for variant in item.family.variants
                ],
            )
            for index, item in enumerate(pack.items, start=1)
        ],
    )


def import_question_family_reviews(
    *,
    pack: QuestionFamilyReviewPack,
    decisions: QuestionFamilyReviewDecisionBatch,
    require_complete: bool = True,
) -> QuestionFamilyReviewImportResult:
    errors: list[str] = []
    if decisions.pack_id != pack.pack_id:
        raise ValueError("QuestionFamilyReviewDecisionBatch pack_id does not match review pack")
    item_by_family = {item.family.question_family_id: item for item in pack.items}
    decision_by_family = {decision.question_family_id: decision for decision in decisions.decisions}
    unknown = sorted(set(decision_by_family) - set(item_by_family))
    if unknown:
        errors.append(
            "QuestionFamily decisions reference unknown family IDs: " + ", ".join(unknown)
        )
    if require_complete:
        missing = sorted(set(item_by_family) - set(decision_by_family))
        if missing:
            errors.append("Missing QuestionFamily review decisions: " + ", ".join(missing))
    shortlisted: list[ShortlistedQuestionFamily] = []
    rejected: list[str] = []
    needs_revision: list[str] = []
    deferred: list[str] = []
    for family_id, item in item_by_family.items():
        decision = decision_by_family.get(family_id)
        if decision is None:
            continue
        family_variant_by_id = {variant.variant_id: variant for variant in item.family.variants}
        if not decision.reviewer.strip() or not decision.notes.strip():
            errors.append(f"{family_id}: QuestionFamily decision is unreviewed")
            continue
        if decision.review_item_id != item.review_item_id:
            errors.append(f"{family_id}: decision review_item_id does not match review pack")
            continue
        variant_decision_by_id = {
            variant_decision.variant_id: variant_decision
            for variant_decision in decision.variant_decisions
        }
        unknown_variants = sorted(set(variant_decision_by_id) - set(family_variant_by_id))
        if unknown_variants:
            errors.append(
                f"{family_id}: decisions reference unknown variants: " + ", ".join(unknown_variants)
            )
            continue
        if require_complete:
            missing_variants = sorted(set(family_variant_by_id) - set(variant_decision_by_id))
            if missing_variants:
                errors.append(
                    f"{family_id}: missing variant decisions: " + ", ".join(missing_variants)
                )
                continue
        mismatched_seed_ids = [
            variant_id
            for variant_id, variant_decision in variant_decision_by_id.items()
            if variant_decision.question_seed_id
            != family_variant_by_id[variant_id].question_seed_id
        ]
        if mismatched_seed_ids:
            errors.append(
                f"{family_id}: variant decisions carry mismatched seed IDs: "
                + ", ".join(sorted(mismatched_seed_ids))
            )
            continue
        active_variant_ids = [
            variant_decision.variant_id
            for variant_decision in decision.variant_decisions
            if variant_decision.status == QuestionFamilyVariantReviewStatus.ACTIVE
        ]
        if decision.status != QuestionFamilyReviewStatus.SHORTLISTED and active_variant_ids:
            errors.append(f"{family_id}: ACTIVE variants are only allowed in shortlisted families")
            continue
        if decision.status == QuestionFamilyReviewStatus.SHORTLISTED:
            if not active_variant_ids:
                errors.append(f"{family_id}: shortlisted family has no active variants")
                continue
            reviewed_family = item.family.model_copy(
                update={"review_status": QuestionFamilyGenerationReviewStatus.HUMAN_REVIEWED}
            )
            shortlisted.append(
                ShortlistedQuestionFamily(
                    family=reviewed_family,
                    review=decision,
                    active_variant_ids=active_variant_ids,
                    source_batch_id=item.source_batch_id,
                )
            )
        elif decision.status == QuestionFamilyReviewStatus.REJECTED:
            rejected.append(family_id)
        elif decision.status == QuestionFamilyReviewStatus.NEEDS_REVISION:
            needs_revision.append(family_id)
        else:
            deferred.append(family_id)
    if errors:
        return QuestionFamilyReviewImportResult(errors=errors)
    shortlist = QuestionFamilyShortlistManifest(
        shortlist_id=f"question-family-shortlist-{stable_hash({'pack': pack.pack_id, 'decisions': decisions.model_dump(mode='json')})[:12]}",
        pack_id=pack.pack_id,
        context_id=pack.context_id,
        context_digest=pack.context_digest,
        shortlisted=shortlisted,
        rejected_family_ids=rejected,
        needs_revision_family_ids=needs_revision,
        deferred_family_ids=deferred,
    )
    return QuestionFamilyReviewImportResult(shortlist=shortlist)


def write_question_family_shortlist(
    shortlist: QuestionFamilyShortlistManifest,
    *,
    corpus_root: str | Path = "corpus",
) -> Path:
    root = Path(corpus_root) / "question_families" / "reviewed"
    return dump_data(shortlist, root / "question_family_shortlist_manifest.yaml")


def _force_question_family_batch(
    output: _QuestionScientistFamilyModelOutput,
    *,
    context_payload: QuestionScientistContextPayloadV2,
    provider_id: str,
    input_digest: str,
) -> tuple[QuestionFamilyBatch | None, list[StageDProcessedCandidate]]:
    """Stamp the code-owned fields onto the model's families ONE FAMILY AT A TIME.

    Returns the batch of families that survived the strict rebuild plus one drop record per family
    that did not; ``None`` when no family survived, which is not a batch at all (the strict
    `QuestionFamilyBatch` refuses an empty families list) and is the caller's honest-terminal case.

    Nothing here is relaxed. Every family still faces the identical strict `QuestionSeed` /
    `QuestionFamilyVariant` / `QuestionFamily` rebuild it faced before, and a duplicate id still
    fails closed -- what changed is the BLAST RADIUS: the rejection now costs its own family
    instead of the whole batch.
    """
    families: list[QuestionFamily] = []
    dropped: list[StageDProcessedCandidate] = []
    seen_family_ids: set[str] = set()
    seen_seed_ids: set[str] = set()
    seen_variant_ids: set[str] = set()
    for ordinal, candidate in enumerate(output.families, start=1):
        if isinstance(candidate, _UnparsedFamilyCandidate):
            dropped.append(
                _family_drop_record(
                    candidate.family_id or f"unparsed-family-{ordinal:03d}",
                    "family payload rejected at the generation boundary: " + candidate.detail,
                )
            )
            continue
        label = candidate.question_family_id.strip() or f"family-{ordinal:03d}"
        try:
            family, family_seed_ids, family_variant_ids = _force_one_family(
                candidate,
                context_payload=context_payload,
                provider_id=provider_id,
                seen_family_ids=seen_family_ids,
                seen_seed_ids=seen_seed_ids,
                seen_variant_ids=seen_variant_ids,
            )
        except (TypeError, AssertionError):
            raise
        except _QuestionScientistSemanticOutputError as exc:
            # Our own fixed message, no model text: safe to record verbatim.
            dropped.append(_family_drop_record(label, f"family rejected by strict rebuild: {exc}"))
            continue
        except ValidationError as exc:
            dropped.append(
                _family_drop_record(
                    label, "family rejected by strict rebuild: " + _rejected_fields(exc)
                )
            )
            continue
        seen_family_ids.add(family.question_family_id)
        seen_seed_ids |= family_seed_ids
        seen_variant_ids |= family_variant_ids
        families.append(family)
    if not families:
        return None, dropped
    batch = QuestionFamilyBatch.model_validate(
        {
            "batch_id": f"question-family-batch-{stable_hash({'context': context_payload.context_digest, 'input': input_digest, 'families': [_family_identity_payload(family) for family in families]})[:12]}",
            "context_id": context_payload.context_id,
            "context_digest": context_payload.context_digest,
            "input_digest": input_digest,
            "families": families,
            "origin_provider_id": provider_id,
            "prompt_version": QUESTION_SCIENTIST_FAMILY_PROMPT_VERSION,
            "authority_ceiling": context_payload.authority_ceiling,
        }
    )
    return batch, dropped


def _no_family_survived_detail(dropped: list[StageDProcessedCandidate]) -> str:
    """Why a reply yielded no usable family, in our own schema's identifiers.

    Every reason here is `_rejected_fields` output or a fixed sentence of ours; the model-authored
    family ids that label the per-family diagnostics are deliberately NOT repeated into a provider
    error, which travels further and promises to be secret-free.
    """
    reasons = [reason for candidate in dropped for reason in candidate.reason_codes]
    if not reasons:
        return "no family candidate survived the generation boundary"
    return f"no family survived the generation boundary ({len(reasons)} refused): " + "; ".join(
        reasons[:8]
    )


def _family_drop_record(family_id: str, reason: str) -> StageDProcessedCandidate:
    """One Stage-D lineage row for a family that never reached the quality filter.

    `QUALITY_DROPPED` is the disposition on purpose: the family was dropped by a validation gate
    and did not reach the shortlist, which is exactly what that disposition means downstream and
    what keeps an all-dropped batch a `SCIENTIFIC_TERMINAL` with complete lineage rather than a
    bare infrastructure crash. Which gate refused it is named in the reason code.
    """
    return StageDProcessedCandidate(
        question_family_id=family_id,
        disposition=StageDCandidateDisposition.QUALITY_DROPPED,
        reason_codes=[reason],
    )


def _force_one_family(
    family: QuestionFamilyModelOutput,
    *,
    context_payload: QuestionScientistContextPayloadV2,
    provider_id: str,
    seen_family_ids: set[str],
    seen_seed_ids: set[str],
    seen_variant_ids: set[str],
) -> tuple[QuestionFamily, set[str], set[str]]:
    """Rebuild ONE family strictly; the ids it claims are returned rather than registered.

    The caller merges them only once the family survives, so a family that fails halfway does not
    leave its half-registered variant and seed ids behind to collide with a later good family.
    """
    family_id = family.question_family_id.strip()
    if family_id in seen_family_ids:
        raise _QuestionScientistSemanticOutputError(
            "Question Scientist family output contains duplicate family IDs"
        )
    family_seed_ids: set[str] = set()
    family_variant_ids: set[str] = set()
    variants: list[QuestionFamilyVariant] = []
    for variant in family.variants:
        variant_id = variant.variant_id.strip()
        if variant_id in seen_variant_ids or variant_id in family_variant_ids:
            raise _QuestionScientistSemanticOutputError(
                "Question Scientist family output contains duplicate variant IDs"
            )
        family_variant_ids.add(variant_id)
        # Deterministic fallback for an empty model-assigned seed id (code-stamped,
        # never model-required); genuinely duplicated non-empty ids still fail closed.
        seed_id = (
            variant.question_seed_id.strip()
            or f"qseed-auto-{len(seen_seed_ids) + len(family_seed_ids) + 1:03d}"
        )
        if seed_id in seen_seed_ids or seed_id in family_seed_ids:
            raise _QuestionScientistSemanticOutputError(
                "Question Scientist family output contains duplicate seed IDs"
            )
        family_seed_ids.add(seed_id)
        source_paper_case_ids = _source_paper_case_ids_for_patterns(
            context_payload,
            variant.seed.source_pattern_ids,
        )
        # Rebuild as the strict QuestionSeed (not model_copy): strict validators re-run
        # with the code-stamped values, so a mirror instance can never leak downstream.
        # Paper-case lineage is a code-owned projection of the selected pattern cards:
        # the proposer chooses pattern IDs, but must not be trusted to repeat the redundant
        # pattern -> formation trace -> PaperCase mapping without omissions or swaps.
        seed = QuestionSeed.model_validate(
            {
                **variant.seed.model_dump(mode="python"),
                "question_seed_id": seed_id,
                "source_paper_case_ids": source_paper_case_ids,
                "context_id": context_payload.context_id,
                "origin_provider_id": provider_id,
                "prompt_version": QUESTION_SCIENTIST_FAMILY_PROMPT_VERSION,
            }
        )
        variants.append(
            QuestionFamilyVariant.model_validate(
                {
                    **variant.model_dump(mode="python"),
                    "variant_id": variant_id,
                    "question_seed_id": seed_id,
                    "seed": seed,
                }
            )
        )
    family_payload = family.model_dump(mode="python")
    family_payload.update(
        {
            "question_family_id": family_id,
            "variants": variants,
            "context_id": context_payload.context_id,
            "origin_provider_id": provider_id,
            "prompt_version": QUESTION_SCIENTIST_FAMILY_PROMPT_VERSION,
            "source_topic_pack_ids": (
                [context_payload.topic_literature.topic_pack_id]
                if context_payload.authority_ceiling
                == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION
                else []
            ),
            "authority_ceiling": context_payload.authority_ceiling,
        }
    )
    return QuestionFamily.model_validate(family_payload), family_seed_ids, family_variant_ids


def _source_paper_case_ids_for_patterns(
    context_payload: QuestionScientistContextPayloadV2,
    source_pattern_ids: list[str],
) -> list[str]:
    cards_by_id = {
        card.pattern_id: card for card in context_payload.paperbank_patterns.pattern_cards
    }
    return sorted(
        {
            summary.source_paper_case_id
            for pattern_id in source_pattern_ids
            if (card := cards_by_id.get(pattern_id)) is not None
            for summary in card.formation_trace_summaries
            if summary.source_paper_case_id
        }
    )


def _family_identity_payload(family: QuestionFamily) -> dict[str, Any]:
    payload = family.model_dump(mode="json")
    if family.authority_ceiling == FrontHalfAuthorityCeiling.VERIFIED:
        payload.pop("authority_ceiling", None)
        if not family.source_topic_pack_ids:
            payload.pop("source_topic_pack_ids", None)
    return payload


def _rename_ensemble_family_ids(
    batch: QuestionFamilyBatch,
    proposer_branch_id: str,
) -> QuestionFamilyBatch:
    branch_suffix = proposer_branch_id.removeprefix("qfam-proposer-")
    families: list[QuestionFamily] = []
    for family_index, family in enumerate(batch.families, start=1):
        family_id = f"qfamily-{branch_suffix}-{family_index:03d}"
        variants: list[QuestionFamilyVariant] = []
        for variant_index, variant in enumerate(family.variants, start=1):
            variant_id = f"qvariant-{branch_suffix}-{family_index:03d}-{variant_index:03d}"
            seed_id = f"qseed-{branch_suffix}-{family_index:03d}-{variant_index:03d}"
            seed = variant.seed.model_copy(update={"question_seed_id": seed_id})
            variants.append(
                QuestionFamilyVariant.model_validate(
                    {
                        **variant.model_dump(mode="python"),
                        "variant_id": variant_id,
                        "question_seed_id": seed_id,
                        "seed": seed,
                    }
                )
            )
        family_payload = family.model_dump(mode="python")
        family_payload.update({"question_family_id": family_id, "variants": variants})
        families.append(QuestionFamily.model_validate(family_payload))
    payload = batch.model_dump(mode="python")
    payload["families"] = families
    payload["batch_id"] = (
        "question-family-batch-"
        + stable_hash(
            {
                "context_digest": batch.context_digest,
                "input_digest": batch.input_digest,
                "proposer_branch_id": proposer_branch_id,
                "families": [family.model_dump(mode="json") for family in families],
            }
        )[:12]
    )
    return QuestionFamilyBatch.model_validate(payload)


def _model_id_from_provider_id(provider_id: str) -> str:
    return provider_id.split(":", 1)[1] if ":" in provider_id else provider_id


def _validate_quality_report_matches_batch(
    report: QuestionFamilyQualityReport,
    batch: QuestionFamilyBatch,
) -> None:
    if report.context_id != batch.context_id:
        raise ValueError("QuestionFamily quality report context_id does not match batch")
    if report.context_digest != batch.context_digest:
        raise ValueError("QuestionFamily quality report context_digest does not match batch")
    if report.batch_input_digest != batch.input_digest:
        raise ValueError("QuestionFamily quality report input digest does not match batch")
    if report.batch_content_digest != question_family_batch_content_digest(batch):
        raise ValueError("QuestionFamily quality report content digest does not match batch")
    if report.origin_provider_id != batch.origin_provider_id:
        raise ValueError("QuestionFamily quality report provider does not match batch")
    if report.model_id != _model_id_from_provider_id(batch.origin_provider_id):
        raise ValueError("QuestionFamily quality report model does not match batch")
    if report.prompt_version != batch.prompt_version:
        raise ValueError("QuestionFamily quality report prompt does not match batch")
    if not report.provenance_allowlist_digest:
        raise ValueError("QuestionFamily quality report must be provenance-allowlist bound")


def _dataset_context_ids(context_payload: QuestionScientistContextPayloadV2) -> list[str]:
    dataset = context_payload.dataset_context
    ids = [dataset.dataset_id, dataset.narrative_id, dataset.review_id]
    ids.extend(section.section_id for section in dataset.story_sections)
    ids.extend(opportunity.opportunity_id for opportunity in dataset.opportunity_cards)
    return [value for value in ids if value]


def _topic_claim_ids(context_payload: QuestionScientistContextPayloadV2) -> list[str]:
    return [claim.claim_id for claim in context_payload.topic_literature.claim_cards]


def _looks_like_wording_only_variant(
    left: QuestionFamilyVariant,
    right: QuestionFamilyVariant,
) -> bool:
    left_axes = {axis.value for axis in left.distinction_axes}
    right_axes = {axis.value for axis in right.distinction_axes}
    if left_axes != right_axes:
        return False
    question_similarity = _jaccard(_tokens(left.seed.question), _tokens(right.seed.question))
    tension_similarity = _jaccard(
        _tokens(left.seed.scientific_tension + " " + left.seed.discriminating_observation),
        _tokens(right.seed.scientific_tension + " " + right.seed.discriminating_observation),
    )
    distinction_similarity = _jaccard(
        _tokens(left.distinct_from_siblings),
        _tokens(right.distinct_from_siblings),
    )
    return (
        question_similarity >= 0.78
        and tension_similarity >= 0.60
        and distinction_similarity >= 0.45
    )


def _word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", value))


def _tokens(text: str) -> set[str]:
    stop = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "into",
        "does",
        "are",
        "their",
        "through",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in stop
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _normalized_text(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _load_prompt(prompt_version: str) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")
