"""Typed, non-accepting inquiry over a topic-evidence insufficiency terminal."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .gate_outcome import GateOutcome, ReviewerExecutionKind


class TopicEvidenceInquiryDisposition(StrEnum):
    """The only legal outcomes of the non-authoritative shepherd inquiry."""

    UPHOLD_INSUFFICIENT = "uphold_insufficient"
    SOURCE_LOCKED_REVISE = "source_locked_revise"
    HUMAN_ESCALATION = "human_escalation"
    #: The inquiry found nothing scope-essential missing. Added because three ordinary answers had
    #: no legal home at all and therefore could not be returned: an empty gap table (the field's own
    #: ``default_factory``), a table whose absences are all scope-OPTIONAL, and a table whose
    #: indeterminates are all scope-optional. The prompt actively invites the second -- it tells the
    #: model optional breadth may remain absent when that limitation is honest -- so a model that
    #: obeyed it produced an object no disposition accepted, Pydantic raised inside
    #: ``generate_structured``, and the run recorded ``PROVIDER_FAILURE``: a scientific judgement
    #: filed as a broken machine, which inverts the ``FailureClass`` contract.
    NO_ESSENTIAL_GAP = "no_essential_gap"


class TopicEvidenceGapDisposition(StrEnum):
    """Whether an alleged gap is actually represented in the supplied packet."""

    PACKET_ABSENT = "packet_absent"
    PACKET_PRESENT_BUT_OMITTED = "packet_present_but_omitted"
    INDETERMINATE = "indeterminate"


class TopicEvidenceSemanticDimension(StrEnum):
    """The domain-neutral scientific dimensions used by the topic-evidence gate."""

    BACKGROUND_CORE_CONSTRUCTS = "background_core_constructs"
    UNRESOLVED_TENSIONS = "unresolved_tensions"
    METHODS_MEASUREMENT_LIMITS = "methods_measurement_limits"
    COMPETING_EXPLANATIONS_CONFOUNDS = "competing_explanations_confounds"
    BOUNDARY_CONDITIONS_GENERALIZATION = "boundary_conditions_generalization"
    DATASET_RESOURCE_REUSE = "dataset_resource_reuse"
    CLOSE_PRIOR_ALREADY_ANSWERED = "close_prior_already_answered"
    OPEN_GAPS = "open_gaps"


class TopicEvidenceGapAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semantic_dimension: TopicEvidenceSemanticDimension
    disposition: TopicEvidenceGapDisposition
    essential_to_scope: bool
    source_record_ids: list[str] = Field(default_factory=list)
    explanation: str

    @model_validator(mode="after")
    def bind_packet_present_findings(self) -> TopicEvidenceGapAssessment:
        source_ids = [
            source_id.strip() for source_id in self.source_record_ids if source_id.strip()
        ]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("gap assessment source_record_ids must be unique")
        if self.disposition == TopicEvidenceGapDisposition.PACKET_PRESENT_BUT_OMITTED:
            if not source_ids:
                raise ValueError("packet-present gap assessment requires source_record_ids")
        elif source_ids:
            raise ValueError("only packet-present gap assessments may cite source_record_ids")
        if not self.explanation.strip():
            raise ValueError("gap assessment explanation must be non-empty")
        self.source_record_ids = source_ids
        return self


class TopicEvidenceTerminalInquiryOutput(BaseModel):
    """Model-facing output. It deliberately has no accept disposition."""

    model_config = ConfigDict(extra="forbid")

    disposition: TopicEvidenceInquiryDisposition
    rationale: str
    gap_assessments: list[TopicEvidenceGapAssessment] = Field(default_factory=list)
    revision_source_record_ids: list[str] = Field(default_factory=list)
    required_changes: list[str] = Field(default_factory=list)
    evidence_needed: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_non_accepting_route(self) -> TopicEvidenceTerminalInquiryOutput:
        if not self.rationale.strip():
            raise ValueError("topic-evidence inquiry rationale must be non-empty")
        source_ids = [source_id.strip() for source_id in self.revision_source_record_ids]
        changes = [change.strip() for change in self.required_changes if change.strip()]
        needed = [item.strip() for item in self.evidence_needed if item.strip()]
        essential_absent = any(
            assessment.essential_to_scope
            and assessment.disposition == TopicEvidenceGapDisposition.PACKET_ABSENT
            for assessment in self.gap_assessments
        )
        essential_indeterminate = any(
            assessment.essential_to_scope
            and assessment.disposition == TopicEvidenceGapDisposition.INDETERMINATE
            for assessment in self.gap_assessments
        )
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("revision_source_record_ids must be unique")
        if self.disposition == TopicEvidenceInquiryDisposition.SOURCE_LOCKED_REVISE:
            packet_present_ids = {
                source_id
                for assessment in self.gap_assessments
                if assessment.disposition == TopicEvidenceGapDisposition.PACKET_PRESENT_BUT_OMITTED
                for source_id in assessment.source_record_ids
            }
            if not source_ids or not changes:
                raise ValueError(
                    "source_locked_revise requires source IDs and actionable required_changes"
                )
            if not set(source_ids).issubset(packet_present_ids):
                raise ValueError(
                    "revision source IDs must be bound by packet-present gap assessments"
                )
            if essential_absent or essential_indeterminate:
                raise ValueError(
                    "source_locked_revise cannot bypass an essential absent or indeterminate gap"
                )
        elif source_ids or changes:
            raise ValueError(
                "uphold/escalation cannot carry revision source IDs or required_changes"
            )
        if self.disposition == TopicEvidenceInquiryDisposition.UPHOLD_INSUFFICIENT:
            if not essential_absent:
                raise ValueError("uphold_insufficient requires an essential packet-absent gap")
            if not needed:
                raise ValueError("uphold_insufficient must name the evidence needed")
        if self.disposition == TopicEvidenceInquiryDisposition.NO_ESSENTIAL_GAP:
            essential_omitted = any(
                assessment.essential_to_scope
                and assessment.disposition == TopicEvidenceGapDisposition.PACKET_PRESENT_BUT_OMITTED
                for assessment in self.gap_assessments
            )
            if essential_absent or essential_indeterminate:
                raise ValueError(
                    "no_essential_gap cannot be returned alongside an essential absent or "
                    "indeterminate gap"
                )
            if essential_omitted:
                raise ValueError(
                    "an essential packet-present omission is repairable: return "
                    "source_locked_revise, not no_essential_gap"
                )
        if self.disposition == TopicEvidenceInquiryDisposition.HUMAN_ESCALATION:
            if essential_absent or not essential_indeterminate:
                raise ValueError(
                    "human_escalation requires an essential indeterminate gap and no established "
                    "essential absence"
                )
            if not needed:
                raise ValueError("human_escalation must name the evidence needed")
        self.revision_source_record_ids = source_ids
        self.required_changes = changes
        self.evidence_needed = needed
        return self


class TopicEvidenceTerminalInquiryRecord(BaseModel):
    """Persisted binding from the original verdict to the non-accepting inquiry route."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["topic_evidence_terminal_inquiry/v1"] = (
        "topic_evidence_terminal_inquiry/v1"
    )
    brief_id: str
    candidate_digest: str
    original_outcome: GateOutcome
    original_review_input_path: str
    original_review_input_sha256: str
    prompt_version: str
    input_digest: str
    provider_id: str
    model_id: str
    execution_kind: ReviewerExecutionKind
    allowed_source_record_ids: list[str]
    eligible_source_record_ids: list[str]
    output_digest: str
    output: TopicEvidenceTerminalInquiryOutput
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def enforce_record_bindings(self) -> TopicEvidenceTerminalInquiryRecord:
        allowed = set(self.allowed_source_record_ids)
        eligible = set(self.eligible_source_record_ids)
        if not eligible.issubset(allowed):
            raise ValueError("eligible inquiry sources must resolve to the allowed packet")
        cited = {
            source_id
            for assessment in self.output.gap_assessments
            for source_id in assessment.source_record_ids
        } | set(self.output.revision_source_record_ids)
        if not cited.issubset(eligible):
            raise ValueError("inquiry cited a source outside the eligible packet")
        return self
