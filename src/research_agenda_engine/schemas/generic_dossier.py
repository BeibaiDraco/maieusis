from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .generic_family_outcome import GenericFamilyOutcomeKind
from .generic_review_authority import GenericReviewDecisionValue
from .generic_scientific_source import DatasetClaimStatus, DatasetGroundingLevel
from .multi_family_dossier import ReviewAuthority
from .planning_dialogue import BranchDecisionKind


class GenericDossierSourceType(StrEnum):
    BRANCH_STATE = "branch_state"
    SCIENTIFIC_SOURCE_SNAPSHOT = "scientific_source_snapshot"
    FAMILY_OUTCOME = "family_outcome"
    REVIEW_DECISION = "review_decision"
    PLANNER_EVIDENCE = "planner_evidence"
    OWNER_REVIEW = "owner_review"
    INDEPENDENT_REVIEW = "independent_review"


class GenericDossierClaimScope(StrEnum):
    FAMILY = "family"
    VARIANT = "variant"
    FEASIBILITY = "feasibility"
    METHOD = "method"
    LIMITATION = "limitation"
    PROVENANCE = "provenance"


class GenericDossierSourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_type: GenericDossierSourceType
    artifact_id: str
    artifact_path: str
    artifact_digest: str
    contribution: str

    @field_validator("source_id", "artifact_id", "artifact_path", "contribution")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericDossierSourceRef fields must be non-empty")
        return value

    @field_validator("artifact_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="GenericDossierSourceRef artifact_digest")
        return value


class GenericDossierClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    scope: GenericDossierClaimScope
    text: str
    citation_ids: list[str]
    variant_id: str = ""

    @field_validator("claim_id", "text")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericDossierClaim fields must be non-empty")
        return value

    @field_validator("citation_ids")
    @classmethod
    def require_citation_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("GenericDossierClaim requires citation_ids")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierClaim citation_ids must be unique")
        return cleaned

    @model_validator(mode="after")
    def validate_variant_scope(self) -> GenericDossierClaim:
        if self.scope == GenericDossierClaimScope.VARIANT and not self.variant_id.strip():
            raise ValueError("variant-scoped generic dossier claims require variant_id")
        if self.scope != GenericDossierClaimScope.VARIANT and self.variant_id.strip():
            raise ValueError("non-variant generic dossier claims cannot carry variant_id")
        return self


class GenericDossierSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section_id: str
    title: str
    purpose: str
    claim_ids: list[str]

    @field_validator("section_id", "title", "purpose")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericDossierSection fields must be non-empty")
        return value

    @field_validator("claim_ids")
    @classmethod
    def require_claim_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("GenericDossierSection requires claim_ids")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierSection claim_ids must be unique")
        return cleaned


class GenericDossierCitationLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_ledger_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    sources: list[GenericDossierSourceRef]
    evidence_ids: list[str]
    allowed_citation_ids: list[str]
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "citation_ledger_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericDossierCitationLedger fields must be non-empty")
        return value

    @field_validator("allowed_citation_ids")
    @classmethod
    def require_unique_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("GenericDossierCitationLedger list fields must be non-empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierCitationLedger list fields must be unique")
        return cleaned

    @field_validator("evidence_ids")
    @classmethod
    def clean_optional_evidence_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierCitationLedger evidence IDs must be unique")
        return cleaned

    @model_validator(mode="after")
    def validate_ledger(self) -> GenericDossierCitationLedger:
        if not self.sources:
            raise ValueError("GenericDossierCitationLedger requires sources")
        expected = {source.source_id for source in self.sources} | set(self.evidence_ids)
        if set(self.allowed_citation_ids) != expected:
            raise ValueError("GenericDossierCitationLedger allowed citations must match sources")
        return self


class GenericDossierWritingPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dossier_writing_packet_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_snapshot_id: str
    source_snapshot_digest: str
    dataset_grounding_level: DatasetGroundingLevel
    dataset_claim_status: DatasetClaimStatus = DatasetClaimStatus.UNVERIFIED
    human_review_status: str = "not_imported"
    source_outcome_packet_id: str
    source_review_decision_packet_id: str
    review_authority: ReviewAuthority
    review_decision: GenericReviewDecisionValue
    outcome_kind: GenericFamilyOutcomeKind
    branch_decision: BranchDecisionKind
    citation_ledger_id: str
    allowed_citation_ids: list[str]
    evidence_ids: list[str]
    question_title: str
    question_statement: str
    family_intent_summary: str
    claim_ceiling: list[str]
    remaining_human_decisions: list[str]
    sections: list[GenericDossierSection]
    claims: list[GenericDossierClaim]
    dossier_skeleton_path: str
    citation_ledger_path: str
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    api_written: Literal[False] = False
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    final_dossier_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "dossier_writing_packet_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_snapshot_id",
        "human_review_status",
        "source_outcome_packet_id",
        "source_review_decision_packet_id",
        "citation_ledger_id",
        "question_title",
        "question_statement",
        "family_intent_summary",
        "dossier_skeleton_path",
        "citation_ledger_path",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericDossierWritingPacket fields must be non-empty")
        return value

    @field_validator("source_snapshot_digest")
    @classmethod
    def validate_snapshot_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="GenericDossierWritingPacket source_snapshot_digest")
        return value

    @field_validator(
        "allowed_citation_ids",
        "claim_ceiling",
        "remaining_human_decisions",
    )
    @classmethod
    def require_unique_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("GenericDossierWritingPacket list fields must be non-empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierWritingPacket list fields must be unique")
        return cleaned

    @field_validator("evidence_ids")
    @classmethod
    def clean_optional_evidence_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierWritingPacket evidence IDs must be unique")
        return cleaned

    @model_validator(mode="after")
    def validate_writing_packet(self) -> GenericDossierWritingPacket:
        if not self.sections:
            raise ValueError("GenericDossierWritingPacket requires sections")
        if not self.claims:
            raise ValueError("GenericDossierWritingPacket requires claims")
        claim_ids = [claim.claim_id for claim in self.claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("GenericDossierWritingPacket has duplicate claim IDs")
        unknown_claim_refs = sorted(
            {
                claim_id
                for section in self.sections
                for claim_id in section.claim_ids
                if claim_id not in set(claim_ids)
            }
        )
        if unknown_claim_refs:
            raise ValueError(
                "GenericDossierWritingPacket sections reference unknown claims: "
                + ", ".join(unknown_claim_refs)
            )
        allowed = set(self.allowed_citation_ids)
        unknown_citations = sorted(
            {
                citation_id
                for claim in self.claims
                for citation_id in claim.citation_ids
                if citation_id not in allowed
            }
        )
        if unknown_citations:
            raise ValueError(
                "GenericDossierWritingPacket claims reference unknown citations: "
                + ", ".join(unknown_citations)
            )
        if not set(self.evidence_ids).issubset(allowed):
            raise ValueError("GenericDossierWritingPacket evidence IDs must be citeable")
        required_sections = {
            "question_family",
            "scientific_motivation",
            "dataset_leverage",
            "variant_plans",
            "competing_explanations",
            "outcome_meanings",
            "limitations",
            "authority",
            "provenance",
        }
        missing = sorted(required_sections - {section.section_id for section in self.sections})
        if missing:
            raise ValueError(
                "GenericDossierWritingPacket missing required sections: " + ", ".join(missing)
            )
        return self


class GenericDossierManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dossier_manifest_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    dossier_writing_packet_id: str
    citation_ledger_id: str
    dossier_writing_packet_path: str
    dossier_writing_packet_digest: str
    citation_ledger_path: str
    citation_ledger_digest: str
    dossier_skeleton_path: str
    dossier_skeleton_digest: str
    source_packet_ids: list[str]
    source_packet_digests: dict[str, str]
    branch_event_id: str
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    final_dossier_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "dossier_manifest_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "dossier_writing_packet_id",
        "citation_ledger_id",
        "dossier_writing_packet_path",
        "citation_ledger_path",
        "dossier_skeleton_path",
        "branch_event_id",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericDossierManifest fields must be non-empty")
        return value

    @field_validator(
        "dossier_writing_packet_digest",
        "citation_ledger_digest",
        "dossier_skeleton_digest",
    )
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="GenericDossierManifest digest")
        return value

    @field_validator("source_packet_ids")
    @classmethod
    def require_source_packet_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("GenericDossierManifest requires source_packet_ids")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierManifest source_packet_ids must be unique")
        return cleaned

    @model_validator(mode="after")
    def validate_manifest(self) -> GenericDossierManifest:
        if set(self.source_packet_digests) != set(self.source_packet_ids):
            raise ValueError("GenericDossierManifest source digests must match source IDs")
        for digest in self.source_packet_digests.values():
            _validate_sha256(digest, field_name="GenericDossierManifest source digest")
        return self


class GenericDossierWriterInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    writer_input_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_dossier_writing_packet_id: str
    source_citation_ledger_id: str
    source_manifest_id: str
    expected_dossier_markdown_artifact_id: str
    allowed_citation_ids: list[str]
    evidence_ids: list[str]
    required_section_ids: list[str]
    claim_ids: list[str]
    dossier_writing_packet: dict[str, object]
    citation_ledger: dict[str, object]
    source_manifest: dict[str, object]
    dossier_skeleton_markdown: str
    instructions_summary: str
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "writer_input_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_dossier_writing_packet_id",
        "source_citation_ledger_id",
        "source_manifest_id",
        "expected_dossier_markdown_artifact_id",
        "dossier_skeleton_markdown",
        "instructions_summary",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericDossierWriterInput fields must be non-empty")
        return value

    @field_validator("allowed_citation_ids", "required_section_ids", "claim_ids")
    @classmethod
    def require_unique_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("GenericDossierWriterInput list fields must be non-empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierWriterInput list fields must be unique")
        return cleaned

    @field_validator("evidence_ids")
    @classmethod
    def clean_optional_evidence_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierWriterInput evidence IDs must be unique")
        return cleaned

    @model_validator(mode="after")
    def validate_writer_input(self) -> GenericDossierWriterInput:
        if not set(self.evidence_ids).issubset(set(self.allowed_citation_ids)):
            raise ValueError("GenericDossierWriterInput evidence IDs must be citeable")
        return self


class GenericDossierMarkdownArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dossier_markdown_artifact_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_dossier_writing_packet_id: str
    source_citation_ledger_id: str
    source_manifest_id: str
    title: str
    markdown: str
    section_ids: list[str]
    claim_ids: list[str]
    cited_source_ids: list[str]
    cited_evidence_ids: list[str]
    writer_limitations: list[str]
    citation_audit_summary: str
    api_written: Literal[False] = False
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    final_dossier_created: Literal[True] = True
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "dossier_markdown_artifact_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_dossier_writing_packet_id",
        "source_citation_ledger_id",
        "source_manifest_id",
        "title",
        "markdown",
        "citation_audit_summary",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericDossierMarkdownArtifact fields must be non-empty")
        return value

    @field_validator("section_ids", "claim_ids", "cited_source_ids", "writer_limitations")
    @classmethod
    def require_unique_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("GenericDossierMarkdownArtifact list fields must be non-empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierMarkdownArtifact list fields must be unique")
        return cleaned

    @field_validator("cited_evidence_ids")
    @classmethod
    def clean_unique_optional_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericDossierMarkdownArtifact optional list fields must be unique")
        return cleaned


class GenericDossierRenderManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rendered_dossier_manifest_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_dossier_manifest_id: str
    source_dossier_writing_packet_id: str
    source_citation_ledger_id: str
    writer_input_path: str
    writer_input_digest: str
    dossier_markdown_path: str
    dossier_markdown_digest: str
    dossier_markdown_artifact_path: str
    dossier_markdown_artifact_digest: str
    writer_session_snapshot_path: str
    writer_session_snapshot_digest: str
    provider_id: str
    model_id: str
    prompt_version: str
    session_id: str
    input_digest: str
    output_digest: str
    branch_event_id: str
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "rendered_dossier_manifest_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_dossier_manifest_id",
        "source_dossier_writing_packet_id",
        "source_citation_ledger_id",
        "writer_input_path",
        "dossier_markdown_path",
        "dossier_markdown_artifact_path",
        "writer_session_snapshot_path",
        "provider_id",
        "model_id",
        "prompt_version",
        "session_id",
        "branch_event_id",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericDossierRenderManifest fields must be non-empty")
        return value

    @field_validator(
        "writer_input_digest",
        "dossier_markdown_digest",
        "dossier_markdown_artifact_digest",
        "writer_session_snapshot_digest",
        "input_digest",
        "output_digest",
    )
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="GenericDossierRenderManifest digest")
        return value


class GenericEndUserDossierMarkdownArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    end_user_dossier_artifact_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_dossier_markdown_artifact_id: str
    source_render_manifest_id: str
    title: str
    markdown: str
    section_titles: list[str]
    public_limitations: list[str]
    visible_authority_statement: str
    redacted_internal_ids: list[str]
    cited_public_binding_labels: list[str]
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    final_dossier_created: Literal[True] = True
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "end_user_dossier_artifact_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_dossier_markdown_artifact_id",
        "source_render_manifest_id",
        "title",
        "markdown",
        "visible_authority_statement",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericEndUserDossierMarkdownArtifact fields must be non-empty")
        return value

    @field_validator(
        "section_titles",
        "public_limitations",
        "redacted_internal_ids",
        "cited_public_binding_labels",
    )
    @classmethod
    def require_unique_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("GenericEndUserDossierMarkdownArtifact list fields must be non-empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericEndUserDossierMarkdownArtifact list fields must be unique")
        return cleaned

    @model_validator(mode="after")
    def validate_public_redaction(self) -> GenericEndUserDossierMarkdownArtifact:
        leaked = sorted(token for token in self.redacted_internal_ids if token in self.markdown)
        if leaked:
            raise ValueError("end-user dossier leaked internal IDs: " + ", ".join(leaked))
        return self


class GenericEndUserDossierAuditBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    public_label: str
    public_section_id: str = ""
    public_text_digest: str = ""
    internal_claim_ids: list[str]
    internal_source_ids: list[str]
    internal_evidence_ids: list[str]
    source_artifact_paths: list[str]
    source_artifact_digests: list[str]
    source_snapshot_field_paths: list[str] = Field(default_factory=list)

    @field_validator("public_label")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericEndUserDossierAuditBinding public_label must be non-empty")
        return value

    @field_validator("public_section_id")
    @classmethod
    def clean_optional_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("public_text_digest")
    @classmethod
    def validate_optional_digest(cls, value: str) -> str:
        value = value.strip()
        if value:
            _validate_sha256(value, field_name="GenericEndUserDossierAuditBinding text digest")
        return value

    @field_validator(
        "internal_claim_ids",
        "internal_source_ids",
        "source_artifact_paths",
        "source_artifact_digests",
    )
    @classmethod
    def require_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("GenericEndUserDossierAuditBinding list fields must be non-empty")
        return cleaned

    @field_validator("internal_evidence_ids")
    @classmethod
    def clean_optional_evidence_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericEndUserDossierAuditBinding evidence IDs must be unique")
        return cleaned

    @field_validator("source_snapshot_field_paths")
    @classmethod
    def clean_optional_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericEndUserDossierAuditBinding field paths must be unique")
        return cleaned

    @field_validator("source_artifact_digests")
    @classmethod
    def validate_digests(cls, value: list[str]) -> list[str]:
        for digest in value:
            _validate_sha256(digest, field_name="GenericEndUserDossierAuditBinding digest")
        return value


class GenericEndUserDossierAuditSidecar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_sidecar_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_dossier_markdown_artifact_id: str
    source_render_manifest_id: str
    source_outcome_packet_id: str
    source_review_decision_packet_id: str
    authority: ReviewAuthority
    provider_id: str
    model_id: str
    prompt_version: str
    session_id: str
    input_digest: str
    output_digest: str
    branch_event_ids: list[str]
    redacted_internal_ids: list[str]
    bindings: list[GenericEndUserDossierAuditBinding]
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    development_only: Literal[True] = True
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "audit_sidecar_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_dossier_markdown_artifact_id",
        "source_render_manifest_id",
        "source_outcome_packet_id",
        "source_review_decision_packet_id",
        "provider_id",
        "model_id",
        "prompt_version",
        "session_id",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericEndUserDossierAuditSidecar fields must be non-empty")
        return value

    @field_validator("input_digest", "output_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="GenericEndUserDossierAuditSidecar digest")
        return value

    @field_validator("branch_event_ids", "redacted_internal_ids")
    @classmethod
    def require_unique_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("GenericEndUserDossierAuditSidecar list fields must be non-empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("GenericEndUserDossierAuditSidecar list fields must be unique")
        return cleaned

    @field_validator("bindings")
    @classmethod
    def require_bindings(
        cls, value: list[GenericEndUserDossierAuditBinding]
    ) -> list[GenericEndUserDossierAuditBinding]:
        if not value:
            raise ValueError("GenericEndUserDossierAuditSidecar requires bindings")
        return value


class GenericEndUserDossierManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    end_user_dossier_manifest_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_render_manifest_id: str
    source_dossier_markdown_artifact_id: str
    source_dossier_writing_packet_id: str
    source_citation_ledger_id: str
    translator_input_path: str
    translator_input_digest: str
    end_user_dossier_path: str
    end_user_dossier_digest: str
    end_user_dossier_artifact_path: str
    end_user_dossier_artifact_digest: str
    audit_sidecar_path: str
    audit_sidecar_digest: str
    translator_session_snapshot_path: str
    translator_session_snapshot_digest: str
    provider_id: str
    model_id: str
    prompt_version: str
    session_id: str
    input_digest: str
    output_digest: str
    branch_event_id: str
    planning_only: Literal[True] = True
    non_terminal: Literal[True] = True
    contract_eligible: Literal[False] = False
    execution_authorized: Literal[False] = False
    bridge_created: Literal[False] = False
    questioncard_created: Literal[False] = False
    analysiscontract_created: Literal[False] = False
    result_values_persisted: Literal[False] = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "end_user_dossier_manifest_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_render_manifest_id",
        "source_dossier_markdown_artifact_id",
        "source_dossier_writing_packet_id",
        "source_citation_ledger_id",
        "translator_input_path",
        "end_user_dossier_path",
        "end_user_dossier_artifact_path",
        "audit_sidecar_path",
        "translator_session_snapshot_path",
        "provider_id",
        "model_id",
        "prompt_version",
        "session_id",
        "branch_event_id",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("GenericEndUserDossierManifest fields must be non-empty")
        return value

    @field_validator(
        "translator_input_digest",
        "end_user_dossier_digest",
        "end_user_dossier_artifact_digest",
        "audit_sidecar_digest",
        "translator_session_snapshot_digest",
        "input_digest",
        "output_digest",
    )
    @classmethod
    def validate_digest(cls, value: str) -> str:
        _validate_sha256(value, field_name="GenericEndUserDossierManifest digest")
        return value


def _validate_sha256(value: str, *, field_name: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be sha256 hex")
