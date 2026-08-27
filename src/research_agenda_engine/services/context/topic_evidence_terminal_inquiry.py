"""One-shot, source-locked cause inquiry before a topic-evidence insufficiency terminal."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ...assets import resolve_asset
from ...io import dump_data
from ...provenance import sha256_file, stable_hash
from ...providers.models.base import (
    TRANSIENT_FAILURE_KINDS,
    StructuredModelProvider,
    StructuredModelProviderError,
)
from ...schemas.gate_outcome import GateDecision, GateOutcome
from ...schemas.scientific_context import TopicEvidenceBrief
from ...schemas.topic_evidence_inquiry import (
    TopicEvidenceGapDisposition,
    TopicEvidenceInquiryDisposition,
    TopicEvidenceTerminalInquiryOutput,
    TopicEvidenceTerminalInquiryRecord,
)
from ..agents.topic_evidence_reviewer import TopicEvidenceTurnInput

TOPIC_EVIDENCE_TERMINAL_INQUIRY_PROMPT_VERSION = "topic_evidence_terminal_inquiry/v1"

#: One clear budget, matching the extraction lane's shape. Three attempts, transient kinds only.
TERMINAL_INQUIRY_MAX_ATTEMPTS = 3


class TopicEvidenceTerminalInquiryError(ValueError):
    """The inquiry crossed its evidence, decision, or provenance boundary."""


class TopicEvidenceTerminalInquiryInput(BaseModel):
    """Exact persisted packet sent to the non-accepting inquiry model."""

    model_config = ConfigDict(extra="forbid")

    prompt_version: str = TOPIC_EVIDENCE_TERMINAL_INQUIRY_PROMPT_VERSION
    original_review_input: TopicEvidenceTurnInput
    original_outcome: GateOutcome
    allowed_source_record_ids: list[str]
    eligible_source_record_ids: list[str]
    engineering_correction_diagnostics: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_closed_packet(self) -> TopicEvidenceTerminalInquiryInput:
        if self.original_outcome.decision != GateDecision.INSUFFICIENT_EVIDENCE:
            raise ValueError("terminal inquiry requires an insufficient_evidence outcome")
        if not self.original_outcome.evidence_resolved:
            raise ValueError("terminal inquiry requires deterministic evidence closure")
        allowed = set(self.allowed_source_record_ids)
        eligible = set(self.eligible_source_record_ids)
        supplied = {
            source.source_record_id for source in self.original_review_input.source_record_summaries
        }
        if not allowed or supplied != allowed:
            raise ValueError("terminal inquiry source summaries must exactly match allowed IDs")
        if not eligible or not eligible.issubset(allowed):
            raise ValueError("terminal inquiry requires a nonempty eligible source subset")
        if any(
            not diagnostic.startswith("field_state_dropped_unknown_")
            for diagnostic in self.engineering_correction_diagnostics
        ):
            raise ValueError("terminal inquiry engineering diagnostics were not host-classified")
        return self


def load_topic_evidence_terminal_inquiry_prompt(
    prompt_version: str = TOPIC_EVIDENCE_TERMINAL_INQUIRY_PROMPT_VERSION,
) -> str:
    return resolve_asset(Path("prompts") / f"{prompt_version}.md").read_text(encoding="utf-8")


def inquire_topic_evidence_terminal(
    provider: StructuredModelProvider,
    *,
    brief: TopicEvidenceBrief,
    original_review_input: TopicEvidenceTurnInput,
    original_review_input_path: Path,
    original_review_input_reference: str,
    inquiry_input_path: Path,
    original_outcome: GateOutcome,
    allowed_source_record_ids: set[str],
    eligible_source_record_ids: set[str],
    engineering_correction_diagnostics: list[str],
) -> tuple[TopicEvidenceTerminalInquiryInput, TopicEvidenceTerminalInquiryRecord]:
    """Ask one model to classify the cause; never grant acceptance or new evidence authority."""

    candidate_digest = stable_hash(brief)
    if original_outcome.candidate_digest != candidate_digest:
        raise TopicEvidenceTerminalInquiryError(
            "terminal inquiry outcome is not bound to the supplied topic brief"
        )
    if not original_review_input_path.is_file():
        raise TopicEvidenceTerminalInquiryError(
            "terminal inquiry requires the persisted original review input"
        )
    try:
        packet = TopicEvidenceTerminalInquiryInput(
            original_review_input=original_review_input,
            original_outcome=original_outcome,
            allowed_source_record_ids=sorted(allowed_source_record_ids),
            eligible_source_record_ids=sorted(eligible_source_record_ids),
            engineering_correction_diagnostics=list(engineering_correction_diagnostics),
            instructions=[
                "Classify alleged gaps only from the supplied rights-safe packet.",
                "Engineering correction diagnostics are provenance, not evidence of literature absence.",
                "Never accept the brief or introduce a source.",
            ],
        )
    except ValueError as exc:
        raise TopicEvidenceTerminalInquiryError(
            "topic-evidence inquiry input crossed its closed-packet boundary"
        ) from exc
    input_digest = stable_hash(packet)
    dump_data(packet, inquiry_input_path)
    user_prompt = json.dumps(packet.model_dump(mode="json"), ensure_ascii=False, indent=2)
    output: TopicEvidenceTerminalInquiryOutput | None = None
    for attempt in range(1, TERMINAL_INQUIRY_MAX_ATTEMPTS + 1):
        try:
            output = provider.generate_structured(
                system_prompt=load_topic_evidence_terminal_inquiry_prompt(),
                user_prompt=user_prompt,
                output_model=TopicEvidenceTerminalInquiryOutput,
            )
            break
        except StructuredModelProviderError as exc:
            # One transient hiccup on this single call ended a ~7-minute live leg that had already
            # cleared the independent narrative gate, and a hand replay of the identical persisted
            # packet succeeded on the first attempt. The repository already classifies which
            # failures a replay can clear; this lane had the taxonomy available and did not use it.
            # Only transient kinds replay -- a truncation or an auth failure fails closed here, as
            # it must.
            if exc.kind not in TRANSIENT_FAILURE_KINDS or attempt >= TERMINAL_INQUIRY_MAX_ATTEMPTS:
                raise
    if output is None:  # pragma: no cover - the loop either breaks with a value or raises
        raise AssertionError("terminal inquiry ended without a provider result")
    try:
        record = TopicEvidenceTerminalInquiryRecord(
            brief_id=brief.brief_id,
            candidate_digest=candidate_digest,
            original_outcome=original_outcome,
            original_review_input_path=original_review_input_reference,
            original_review_input_sha256=sha256_file(original_review_input_path),
            prompt_version=TOPIC_EVIDENCE_TERMINAL_INQUIRY_PROMPT_VERSION,
            input_digest=input_digest,
            provider_id=provider.provider_id,
            model_id=getattr(provider, "model_name", "") or provider.provider_id,
            execution_kind=provider.execution_kind,
            allowed_source_record_ids=sorted(allowed_source_record_ids),
            eligible_source_record_ids=sorted(eligible_source_record_ids),
            output_digest=stable_hash(output),
            output=output,
        )
    except ValueError as exc:
        raise TopicEvidenceTerminalInquiryError(
            "topic-evidence inquiry crossed its source lock"
        ) from exc
    return packet, record


def inquiry_revision_outcome(
    record: TopicEvidenceTerminalInquiryRecord,
    *,
    brief: TopicEvidenceBrief,
) -> GateOutcome:
    """Convert only the typed revise route into existing-loop revision authority.

    This outcome can trigger a redraft but cannot be promoted: its gate name is the inquiry family,
    and the ordinary independent topic reviewer must still produce the eventual accept.
    """

    if record.output.disposition != TopicEvidenceInquiryDisposition.SOURCE_LOCKED_REVISE:
        raise TopicEvidenceTerminalInquiryError(
            "inquiry did not authorize a source-locked revision"
        )
    if record.candidate_digest != stable_hash(brief):
        raise TopicEvidenceTerminalInquiryError(
            "inquiry record is not bound to the revision candidate"
        )
    return GateOutcome(
        gate_name="topic_evidence_terminal_inquiry",
        decision=GateDecision.REVISE,
        candidate_digest=record.candidate_digest,
        generator_provider_ids=[record.provider_id],
        reviewer_execution_kind=record.execution_kind,
        rationale=record.output.rationale,
        required_changes=list(record.output.required_changes),
        evidence_resolved=True,
        reviewer_provider_id=record.provider_id,
        reviewer_model_id=record.model_id,
        reviewer_session_id="topic-evidence-terminal-inquiry",
        input_digest=record.input_digest,
        output_digest=record.output_digest,
    )


def assert_inquiry_revision_coverage(
    record: TopicEvidenceTerminalInquiryRecord,
    *,
    cited_source_record_ids: set[str],
) -> None:
    """Require source-locked scientific coverage without turning alternatives into quotas.

    The inquiry may identify several eligible examples for one omitted semantic dimension.  A
    revision must use at least one inquiry-selected source overall and at least one selected source
    for every scope-essential packet-present dimension.  Requiring every listed alternative would
    reward citation stuffing and make a scientifically complete revision fail for omitting a
    redundant example.  The independent reviewer remains responsible for judging sufficiency.
    """

    if record.output.disposition != TopicEvidenceInquiryDisposition.SOURCE_LOCKED_REVISE:
        raise TopicEvidenceTerminalInquiryError(
            "inquiry did not authorize a source-locked revision"
        )
    selected = set(record.output.revision_source_record_ids)
    if cited_source_record_ids.isdisjoint(selected):
        raise TopicEvidenceTerminalInquiryError(
            "source-locked topic revision used no inquiry-bound source"
        )

    missing_dimensions: list[str] = []
    for assessment in record.output.gap_assessments:
        if not assessment.essential_to_scope or assessment.disposition != (
            TopicEvidenceGapDisposition.PACKET_PRESENT_BUT_OMITTED
        ):
            continue
        dimension_sources = set(assessment.source_record_ids) & selected
        if not dimension_sources or cited_source_record_ids.isdisjoint(dimension_sources):
            missing_dimensions.append(assessment.semantic_dimension.value)
    if missing_dimensions:
        raise TopicEvidenceTerminalInquiryError(
            "source-locked topic revision omitted inquiry-bound coverage for essential dimensions: "
            + ", ".join(sorted(missing_dimensions))
        )


def topic_evidence_inquiry_review_guidance(
    record: TopicEvidenceTerminalInquiryRecord,
) -> str:
    """Project typed inquiry context into the next independent review without granting authority."""

    if record.output.disposition != TopicEvidenceInquiryDisposition.SOURCE_LOCKED_REVISE:
        return ""
    essential_present = sorted(
        assessment.semantic_dimension.value
        for assessment in record.output.gap_assessments
        if assessment.essential_to_scope
        and assessment.disposition == TopicEvidenceGapDisposition.PACKET_PRESENT_BUT_OMITTED
    )
    optional_absent = sorted(
        assessment.semantic_dimension.value
        for assessment in record.output.gap_assessments
        if not assessment.essential_to_scope
        and assessment.disposition == TopicEvidenceGapDisposition.PACKET_ABSENT
    )
    optional_indeterminate = sorted(
        assessment.semantic_dimension.value
        for assessment in record.output.gap_assessments
        if not assessment.essential_to_scope
        and assessment.disposition == TopicEvidenceGapDisposition.INDETERMINATE
    )

    def render(values: list[str]) -> str:
        return ", ".join(values) if values else "none"

    return (
        "A prior non-accepting, source-locked cause inquiry supplied review context, not "
        "acceptance authority. It classified scope-essential packet-present dimensions as "
        f"[{render(essential_present)}], scope-optional packet-absent dimensions as "
        f"[{render(optional_absent)}], and scope-optional indeterminate dimensions as "
        f"[{render(optional_indeterminate)}]. Independently judge every criterion from the "
        "research intent, resolved scope, revised brief, and eligible evidence. The eight semantic "
        "dimensions are review axes, not automatic evidence quotas. Treat field-state severity or "
        "completeness wording as candidate scientific content, not as a host rule about which "
        "dimensions are essential."
    )
