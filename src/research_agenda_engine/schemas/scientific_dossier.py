from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ScientificDossierSourceType(StrEnum):
    BRANCH_STATE = "branch_state"
    HUMAN_GATE = "human_gate"
    HUMAN_REVIEW_PACK = "human_review_pack"
    CORRECTION = "correction"
    CLOSURE_CANDIDATE = "closure_candidate"
    PLAN_REVIEW = "plan_review"
    PLAN_DRAFT = "plan_draft"
    STRUCTURAL_EVIDENCE = "structural_evidence"
    METHOD_SPECIFICATION = "method_specification"
    OWNER_ACCEPTANCE = "owner_acceptance"


class ScientificDossierClaimScope(StrEnum):
    FAMILY = "family"
    VARIANT = "variant"
    PROVENANCE = "provenance"
    FEASIBILITY = "feasibility"
    METHOD = "method"


class ScientificDossierSourceRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    source_type: ScientificDossierSourceType
    artifact_id: str
    artifact_path: str
    artifact_digest: str
    contribution: str

    @field_validator("source_id", "artifact_id", "artifact_path", "contribution")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ScientificDossierSourceRef fields must be non-empty")
        return value

    @field_validator("artifact_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("ScientificDossierSourceRef artifact_digest must be sha256 hex")
        return value


class ScientificDossierClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    scope: ScientificDossierClaimScope
    text: str
    citation_ids: list[str]
    variant_id: str = ""

    @field_validator("claim_id", "text")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("ScientificDossierClaim fields must be non-empty")
        return value

    @field_validator("citation_ids")
    @classmethod
    def require_citations(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("ScientificDossierClaim requires citation IDs")
        return cleaned

    @model_validator(mode="after")
    def validate_variant_claim(self) -> ScientificDossierClaim:
        if self.scope == ScientificDossierClaimScope.VARIANT and not self.variant_id.strip():
            raise ValueError("variant dossier claims require variant_id")
        if self.scope != ScientificDossierClaimScope.VARIANT and self.variant_id.strip():
            raise ValueError("non-variant dossier claims cannot carry variant_id")
        return self


class ScientificDossierSection(BaseModel):
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
            raise ValueError("ScientificDossierSection fields must be non-empty")
        return value

    @field_validator("claim_ids")
    @classmethod
    def require_claims(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("ScientificDossierSection requires claim IDs")
        return cleaned


class ScientificDossierCitationLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_ledger_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    sources: list[ScientificDossierSourceRef]
    evidence_ids: list[str]
    allowed_citation_ids: list[str]
    planning_only: bool = True
    non_terminal: bool = True
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
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
            raise ValueError("ScientificDossierCitationLedger fields must be non-empty")
        return value

    @field_validator("evidence_ids", "allowed_citation_ids")
    @classmethod
    def require_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("ScientificDossierCitationLedger list fields must be non-empty")
        return cleaned

    @model_validator(mode="after")
    def validate_ledger(self) -> ScientificDossierCitationLedger:
        if not self.sources:
            raise ValueError("ScientificDossierCitationLedger requires sources")
        expected = {source.source_id for source in self.sources} | set(self.evidence_ids)
        if set(self.allowed_citation_ids) != expected:
            raise ValueError("ScientificDossierCitationLedger allowed citations must match sources")
        _validate_dossier_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        return self


class ScientificDossierWritingPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dossier_writing_packet_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_b2r_decision_import_packet_id: str
    source_b1r_review_pack_packet_id: str
    source_b1r_correction_packet_id: str
    source_b1_closure_candidate_packet_id: str
    source_a3_review_gate_packet_id: str
    source_a2_plan_draft_revision_packet_id: str
    source_b11_structural_packet_id: str
    source_m3_method_specification_revision_packet_id: str
    source_m4_owner_acceptance_packet_id: str
    citation_ledger_id: str
    allowed_citation_ids: list[str]
    evidence_ids: list[str]
    question_title: str
    question_statement: str
    family_intent_summary: str
    claim_ceiling: list[str]
    remaining_expert_decisions: list[str]
    sections: list[ScientificDossierSection]
    claims: list[ScientificDossierClaim]
    dossier_skeleton_path: str
    citation_ledger_path: str
    planning_only: bool = True
    non_terminal: bool = True
    api_written: bool = False
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    final_dossier_created: bool = False
    result_values_persisted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "dossier_writing_packet_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_b2r_decision_import_packet_id",
        "source_b1r_review_pack_packet_id",
        "source_b1r_correction_packet_id",
        "source_b1_closure_candidate_packet_id",
        "source_a3_review_gate_packet_id",
        "source_a2_plan_draft_revision_packet_id",
        "source_b11_structural_packet_id",
        "source_m3_method_specification_revision_packet_id",
        "source_m4_owner_acceptance_packet_id",
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
            raise ValueError("ScientificDossierWritingPacket fields must be non-empty")
        return value

    @field_validator(
        "allowed_citation_ids",
        "evidence_ids",
        "claim_ceiling",
        "remaining_expert_decisions",
    )
    @classmethod
    def require_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("ScientificDossierWritingPacket list fields must be non-empty")
        return cleaned

    @model_validator(mode="after")
    def validate_writing_packet(self) -> ScientificDossierWritingPacket:
        if not self.sections:
            raise ValueError("ScientificDossierWritingPacket requires sections")
        if not self.claims:
            raise ValueError("ScientificDossierWritingPacket requires claims")
        claim_ids = [claim.claim_id for claim in self.claims]
        if len(set(claim_ids)) != len(claim_ids):
            raise ValueError("ScientificDossierWritingPacket has duplicate claim IDs")
        known_claim_ids = set(claim_ids)
        unknown_claim_refs = sorted(
            {
                claim_id
                for section in self.sections
                for claim_id in section.claim_ids
                if claim_id not in known_claim_ids
            }
        )
        if unknown_claim_refs:
            raise ValueError(
                "ScientificDossierWritingPacket sections reference unknown claims: "
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
                "ScientificDossierWritingPacket claims reference unknown citations: "
                + ", ".join(unknown_citations)
            )
        if not set(self.evidence_ids).issubset(allowed):
            raise ValueError("ScientificDossierWritingPacket evidence IDs must be citeable")
        required_sections = {
            "question_family",
            "scientific_motivation",
            "dataset_leverage",
            "variant_cfam_003_v1",
            "variant_cfam_003_v2",
            "variant_cfam_003_v3",
            "feasibility_stamp",
            "method_definitions",
            "competing_explanations_controls",
            "outcome_meanings",
            "claim_ceiling_remaining_decisions",
            "provenance_manifest",
        }
        actual_sections = {section.section_id for section in self.sections}
        missing = sorted(required_sections - actual_sections)
        if missing:
            raise ValueError(
                "ScientificDossierWritingPacket missing required sections: " + ", ".join(missing)
            )
        _validate_dossier_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        if self.api_written:
            raise ValueError("R5-010A writing packet cannot be API-written")
        if self.final_dossier_created:
            raise ValueError("R5-010A cannot mark final_dossier_created")
        return self


class ScientificDossierManifest(BaseModel):
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
    planning_only: bool = True
    non_terminal: bool = True
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    final_dossier_created: bool = False
    result_values_persisted: bool = False
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
            raise ValueError("ScientificDossierManifest fields must be non-empty")
        return value

    @field_validator(
        "dossier_writing_packet_digest",
        "citation_ledger_digest",
        "dossier_skeleton_digest",
    )
    @classmethod
    def validate_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("ScientificDossierManifest digest fields must be sha256 hex")
        return value

    @field_validator("source_packet_ids")
    @classmethod
    def require_source_packet_ids(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("ScientificDossierManifest requires source packet IDs")
        return cleaned

    @model_validator(mode="after")
    def validate_manifest(self) -> ScientificDossierManifest:
        if set(self.source_packet_digests) != set(self.source_packet_ids):
            raise ValueError("ScientificDossierManifest source digests must match source IDs")
        invalid = [
            packet_id
            for packet_id, digest in self.source_packet_digests.items()
            if not packet_id.strip()
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ]
        if invalid:
            raise ValueError(
                "ScientificDossierManifest has invalid source digests: " + ", ".join(invalid)
            )
        _validate_dossier_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        if self.final_dossier_created:
            raise ValueError("R5-010A manifest cannot mark final_dossier_created")
        return self


class ScientificDossierWriterInput(BaseModel):
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
    planning_only: bool = True
    non_terminal: bool = True
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
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
            raise ValueError("ScientificDossierWriterInput fields must be non-empty")
        return value

    @field_validator("allowed_citation_ids", "evidence_ids", "required_section_ids", "claim_ids")
    @classmethod
    def require_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("ScientificDossierWriterInput list fields must be non-empty")
        return cleaned

    @model_validator(mode="after")
    def validate_writer_input(self) -> ScientificDossierWriterInput:
        if not set(self.evidence_ids).issubset(set(self.allowed_citation_ids)):
            raise ValueError("ScientificDossierWriterInput evidence IDs must be citeable")
        _validate_dossier_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        return self


class ScientificDossierMarkdownArtifact(BaseModel):
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
    uncited_or_added_claims: list[str] = Field(default_factory=list)
    api_written: bool = True
    planning_only: bool = True
    non_terminal: bool = True
    final_dossier_created: bool = True
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
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
            raise ValueError("ScientificDossierMarkdownArtifact fields must be non-empty")
        return value

    @field_validator("section_ids", "claim_ids", "cited_source_ids", "writer_limitations")
    @classmethod
    def require_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("ScientificDossierMarkdownArtifact list fields must be non-empty")
        return cleaned

    @field_validator("cited_evidence_ids", "uncited_or_added_claims")
    @classmethod
    def clean_optional_text_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_markdown_artifact(self) -> ScientificDossierMarkdownArtifact:
        _validate_dossier_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        if not self.api_written:
            raise ValueError("R5-010B rendered dossier must be api_written")
        if not self.final_dossier_created:
            raise ValueError("R5-010B rendered dossier must mark final_dossier_created")
        return self


class ScientificDossierRenderManifest(BaseModel):
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
    planning_only: bool = True
    non_terminal: bool = True
    final_dossier_created: bool = True
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
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
            raise ValueError("ScientificDossierRenderManifest fields must be non-empty")
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
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("ScientificDossierRenderManifest digest fields must be sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_render_manifest(self) -> ScientificDossierRenderManifest:
        _validate_dossier_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        if not self.final_dossier_created:
            raise ValueError("R5-010B render manifest must mark final_dossier_created")
        return self


class EndUserScientificDossierAuditBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    anchor_id: str
    section_id: str
    paragraph_index: int = Field(ge=1)
    paragraph_digest: str = ""
    public_claim_summary: str
    claim_ids: list[str]
    source_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)

    @field_validator("anchor_id", "section_id", "public_claim_summary")
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("EndUserScientificDossierAuditBinding fields must be non-empty")
        return value

    @field_validator("paragraph_digest")
    @classmethod
    def validate_paragraph_digest(cls, value: str) -> str:
        if not value:
            return value
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("EndUserScientificDossierAuditBinding paragraph_digest must be sha256")
        return value

    @field_validator("claim_ids", "source_ids", "evidence_ids")
    @classmethod
    def clean_text_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_binding(self) -> EndUserScientificDossierAuditBinding:
        if not self.claim_ids:
            raise ValueError("end-user audit bindings require claim IDs")
        if not self.source_ids and not self.evidence_ids:
            raise ValueError("end-user audit bindings require source or evidence IDs")
        return self


class EndUserScientificDossierTranslatorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    translator_input_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_dossier_markdown_artifact_id: str
    source_render_manifest_id: str
    source_dossier_writing_packet_id: str
    source_citation_ledger_id: str
    source_dossier_manifest_id: str
    expected_end_user_dossier_artifact_id: str
    allowed_source_ids: list[str]
    allowed_evidence_ids: list[str]
    allowed_claim_ids: list[str]
    required_section_ids: list[str]
    rendered_machine_dossier_markdown: str
    machine_dossier_artifact: dict[str, object]
    dossier_writing_packet: dict[str, object]
    citation_ledger: dict[str, object]
    source_manifest: dict[str, object]
    render_manifest: dict[str, object]
    evidence_glossary: dict[str, str]
    public_translation_requirements: list[str]
    audit_sidecar_requirements: list[str]
    planning_only: bool = True
    non_terminal: bool = True
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "translator_input_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "source_dossier_markdown_artifact_id",
        "source_render_manifest_id",
        "source_dossier_writing_packet_id",
        "source_citation_ledger_id",
        "source_dossier_manifest_id",
        "expected_end_user_dossier_artifact_id",
        "rendered_machine_dossier_markdown",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("EndUserScientificDossierTranslatorInput fields must be non-empty")
        return value

    @field_validator(
        "allowed_source_ids",
        "allowed_evidence_ids",
        "allowed_claim_ids",
        "required_section_ids",
        "public_translation_requirements",
        "audit_sidecar_requirements",
    )
    @classmethod
    def require_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError(
                "EndUserScientificDossierTranslatorInput list fields must be non-empty"
            )
        return cleaned

    @model_validator(mode="after")
    def validate_translator_input(self) -> EndUserScientificDossierTranslatorInput:
        _validate_dossier_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        return self


class EndUserScientificDossierMarkdownArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    end_user_dossier_artifact_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    source_dossier_markdown_artifact_id: str
    source_render_manifest_id: str
    source_dossier_writing_packet_id: str
    source_citation_ledger_id: str
    source_dossier_manifest_id: str
    title: str
    markdown: str
    section_ids: list[str]
    public_anchor_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str]
    cited_source_ids: list[str]
    cited_evidence_ids: list[str]
    audit_bindings: list[EndUserScientificDossierAuditBinding]
    translator_limitations: list[str]
    translation_audit_summary: str
    ungrounded_or_added_claims: list[str] = Field(default_factory=list)
    api_written: bool = True
    planning_only: bool = True
    non_terminal: bool = True
    final_dossier_created: bool = True
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
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
        "source_dossier_writing_packet_id",
        "source_citation_ledger_id",
        "source_dossier_manifest_id",
        "title",
        "markdown",
        "translation_audit_summary",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("EndUserScientificDossierMarkdownArtifact fields must be non-empty")
        return value

    @field_validator(
        "section_ids",
        "claim_ids",
        "cited_source_ids",
        "translator_limitations",
    )
    @classmethod
    def require_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError(
                "EndUserScientificDossierMarkdownArtifact list fields must be non-empty"
            )
        return cleaned

    @field_validator("cited_evidence_ids", "ungrounded_or_added_claims")
    @classmethod
    def clean_optional_text_list(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @model_validator(mode="after")
    def validate_end_user_artifact(self) -> EndUserScientificDossierMarkdownArtifact:
        if not self.audit_bindings:
            raise ValueError("end-user dossier artifact requires audit bindings")
        if not self.public_anchor_ids:
            self.public_anchor_ids = [binding.anchor_id for binding in self.audit_bindings]
        if set(self.public_anchor_ids) != {binding.anchor_id for binding in self.audit_bindings}:
            raise ValueError("end-user public anchors must match audit bindings")
        _validate_dossier_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        if not self.api_written:
            raise ValueError("R5-010D end-user dossier must be api_written")
        if not self.final_dossier_created:
            raise ValueError("R5-010D end-user dossier must mark final_dossier_created")
        return self


class EndUserScientificDossierAuditSidecar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_sidecar_id: str
    run_id: str
    branch_id: str
    question_family_id: str
    context_id: str
    owner_session_id: str
    end_user_dossier_artifact_id: str
    source_dossier_markdown_artifact_id: str
    source_render_manifest_id: str
    source_dossier_writing_packet_id: str
    source_citation_ledger_id: str
    source_dossier_manifest_id: str
    bindings: list[EndUserScientificDossierAuditBinding]
    claim_ids: list[str]
    source_ids: list[str]
    evidence_ids: list[str]
    source_packet_digests: dict[str, str]
    public_markdown_digest: str
    planning_only: bool = True
    non_terminal: bool = True
    final_dossier_created: bool = True
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "audit_sidecar_id",
        "run_id",
        "branch_id",
        "question_family_id",
        "context_id",
        "owner_session_id",
        "end_user_dossier_artifact_id",
        "source_dossier_markdown_artifact_id",
        "source_render_manifest_id",
        "source_dossier_writing_packet_id",
        "source_citation_ledger_id",
        "source_dossier_manifest_id",
    )
    @classmethod
    def require_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("EndUserScientificDossierAuditSidecar fields must be non-empty")
        return value

    @field_validator("claim_ids", "source_ids")
    @classmethod
    def require_text_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("EndUserScientificDossierAuditSidecar list fields must be non-empty")
        return cleaned

    @field_validator("evidence_ids")
    @classmethod
    def clean_evidence_ids(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]

    @field_validator("public_markdown_digest")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("EndUserScientificDossierAuditSidecar digest must be sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_sidecar(self) -> EndUserScientificDossierAuditSidecar:
        if not self.bindings:
            raise ValueError("end-user audit sidecar requires bindings")
        if set(self.source_packet_digests) != {
            self.source_dossier_markdown_artifact_id,
            self.source_render_manifest_id,
            self.source_dossier_writing_packet_id,
            self.source_citation_ledger_id,
            self.source_dossier_manifest_id,
        }:
            raise ValueError("end-user audit sidecar source digests must match source IDs")
        invalid = [
            source_id
            for source_id, digest in self.source_packet_digests.items()
            if not source_id.strip()
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
        ]
        if invalid:
            raise ValueError(
                "EndUserScientificDossierAuditSidecar has invalid source digests: "
                + ", ".join(invalid)
            )
        _validate_dossier_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        if not self.final_dossier_created:
            raise ValueError("R5-010D audit sidecar must mark final_dossier_created")
        return self


class EndUserScientificDossierManifest(BaseModel):
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
    source_dossier_manifest_id: str
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
    planning_only: bool = True
    non_terminal: bool = True
    final_dossier_created: bool = True
    contract_eligible: bool = False
    execution_authorized: bool = False
    bridge_created: bool = False
    questioncard_created: bool = False
    analysiscontract_created: bool = False
    result_values_persisted: bool = False
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
        "source_dossier_manifest_id",
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
            raise ValueError("EndUserScientificDossierManifest fields must be non-empty")
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
        if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError("EndUserScientificDossierManifest digest fields must be sha256 hex")
        return value

    @model_validator(mode="after")
    def validate_manifest(self) -> EndUserScientificDossierManifest:
        _validate_dossier_flags(
            planning_only=self.planning_only,
            non_terminal=self.non_terminal,
            contract_eligible=self.contract_eligible,
            execution_authorized=self.execution_authorized,
            bridge_created=self.bridge_created,
            questioncard_created=self.questioncard_created,
            analysiscontract_created=self.analysiscontract_created,
            result_values_persisted=self.result_values_persisted,
        )
        if not self.final_dossier_created:
            raise ValueError("R5-010D manifest must mark final_dossier_created")
        return self


def _validate_dossier_flags(
    *,
    planning_only: bool,
    non_terminal: bool,
    contract_eligible: bool,
    execution_authorized: bool,
    bridge_created: bool,
    questioncard_created: bool,
    analysiscontract_created: bool,
    result_values_persisted: bool,
) -> None:
    if not planning_only:
        raise ValueError("R5 dossier artifacts must remain planning_only")
    if not non_terminal:
        raise ValueError("R5 dossier artifacts must remain non_terminal")
    forbidden_flags = {
        "contract_eligible": contract_eligible,
        "execution_authorized": execution_authorized,
        "bridge_created": bridge_created,
        "questioncard_created": questioncard_created,
        "analysiscontract_created": analysiscontract_created,
        "result_values_persisted": result_values_persisted,
    }
    enabled = [name for name, value in forbidden_flags.items() if value]
    if enabled:
        raise ValueError("R5 dossier artifacts cannot enable: " + ", ".join(enabled))
