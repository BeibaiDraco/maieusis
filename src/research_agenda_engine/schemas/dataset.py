from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..enums import ClaimLevel, EvidenceMaturity, EvidenceSourceClass
from ..provenance import EvidenceConflict, EvidenceRef


class EvidenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    question_id: str = ""
    target_id: str = ""
    target_type: str = ""
    request_type: str
    blocking_stage: str = ""
    required_evidence_type: str = ""
    owner_lane: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    rationale: str
    blocking: bool = True


class IBLEvidenceSourceCategory(StrEnum):
    BUILT_IN_FIXTURE = "built_in_fixture"
    DECLARED_DOC_SOURCE = "declared_docs_source"
    LOCAL_METADATA_SURFACE = "local_metadata_surface"
    EXECUTOR_DECLARATION = "executor_declaration"
    FUTURE_PROBE_REQUIRED = "future_probe_required"


class IBLEvidenceVisibility(StrEnum):
    DEMO_ONLY = "demo_only"
    PROPOSER_SAFE = "proposer_safe"
    CRITIC_ONLY = "critic_only"
    CONTRACT_READINESS_ONLY = "contract_readiness_only"


class IBLEvidenceSourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    label: str
    category: IBLEvidenceSourceCategory
    source_class: EvidenceSourceClass
    evidence_maturity: EvidenceMaturity
    visibility: IBLEvidenceVisibility = IBLEvidenceVisibility.CONTRACT_READINESS_ONLY
    artifact_path: str = ""
    artifact_sha256: str = ""
    claims_may_support: list[str] = Field(default_factory=list)
    claims_cannot_support: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)

    @property
    def is_fixture(self) -> bool:
        return (
            self.category == IBLEvidenceSourceCategory.BUILT_IN_FIXTURE
            or self.source_class == EvidenceSourceClass.FIXTURE
            or self.evidence_maturity == EvidenceMaturity.E0_FIXTURE
        )

    @property
    def supports_contract_readiness(self) -> bool:
        return False


class IBLFixtureQuarantineRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fixture_id: str
    path_or_symbol: str
    reason: str
    allowed_use: str = "demo/testing/prototype debugging"
    blocked_in: list[str] = Field(
        default_factory=lambda: ["scientific_mode", "D2", "D3", "ContractReadinessProof"]
    )
    replacement_required: str


class IBLEvidenceSourceInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inventory_id: str
    dataset_id: str = "ibl_bwm"
    records: list[IBLEvidenceSourceRecord] = Field(default_factory=list)
    fixture_quarantine: list[IBLFixtureQuarantineRecord] = Field(default_factory=list)
    evidence_requests: list[EvidenceRequest] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @property
    def supports_contract_readiness(self) -> bool:
        return False


class IBLOfficialSourceKind(StrEnum):
    DATA_RELEASE_DOC = "data_release_doc"
    ACCESS_TOOL_DOC = "access_tool_doc"
    DATA_REGISTRY = "data_registry"
    PRIMARY_PAPER = "primary_paper"
    TECHNICAL_PAPER = "technical_paper"
    RELATED_RELEASE_DOC = "related_release_doc"


class IBLOfficialSourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    kind: IBLOfficialSourceKind
    title: str
    uri: str
    doi: str = ""
    source_version: str = ""
    evidence_maturity: EvidenceMaturity = EvidenceMaturity.E1_DECLARED
    source_class: EvidenceSourceClass = EvidenceSourceClass.USER_DECLARED
    reviewed_claims: list[str] = Field(default_factory=list)
    claims_may_support: list[str] = Field(default_factory=list)
    claims_cannot_support: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)

    @property
    def supports_contract_readiness(self) -> bool:
        return False


class IBLOfficialSourceReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: str
    dataset_id: str = "ibl_bwm"
    review_status: str = "source_inventory_only"
    records: list[IBLOfficialSourceRecord] = Field(default_factory=list)
    evidence_requests: list[EvidenceRequest] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @property
    def supports_contract_readiness(self) -> bool:
        return False


class IBLMetadataScreeningReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    screening_id: str
    dataset_id: str = "ibl_bwm"
    source_review_id: str = ""
    metadata_bundle_id: str = ""
    dataset_card_id: str = ""
    capability_registry_id: str = ""
    inspected_surface_ids: list[str] = Field(default_factory=list)
    expected_ibl_agent_remote_url: str = ""
    expected_ibl_agent_remote_head: str = ""
    local_ibl_agent_revision: str = ""
    local_ibl_agent_matches_expected_head: bool | None = None
    metadata_evidence_maturity: EvidenceMaturity = EvidenceMaturity.E2_METADATA_SCREENED
    executor_evidence_maturity: EvidenceMaturity = EvidenceMaturity.E1_DECLARED
    evidence_requests: list[EvidenceRequest] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @property
    def supports_contract_readiness(self) -> bool:
        return False


class CoverageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    counts: dict[str, int] = Field(default_factory=dict)
    crossed_factors: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    query_scope: str = "release_level"
    evidence: list[EvidenceRef] = Field(default_factory=list)

    def count(self, name: str) -> int | None:
        normalized = name.strip().lower().replace(" ", "_")
        candidates = [normalized]
        if normalized.endswith("s"):
            candidates.append(normalized[:-1])
        else:
            candidates.append(f"{normalized}s")
        for candidate in candidates:
            if candidate in self.counts:
                return self.counts[candidate]
        return None


class CoverageRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    factor: str
    minimum_count: int = 1
    scope: str = "question_specific"
    rationale: str = ""


class CoverageQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    factors: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    conditions: dict[str, list[str]] = Field(default_factory=dict)
    required_measurements: list[str] = Field(default_factory=list)
    minimum_counts: dict[str, int] = Field(default_factory=dict)
    query_scope: str = "question_specific"


class CoverageRequirementSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    question_id: str
    measurement: str = ""
    event: str = ""
    time_window: str = ""
    region: str = ""
    condition_set: str = ""
    condition_values: list[str] = Field(default_factory=list)
    unit: str = ""
    minimum_count: int = 1
    minimum_count_factor: str = ""
    rationale: str = ""
    blocking: bool = True


class JointCoverageQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_id: str
    question_id: str
    dataset_id: str
    dataset_version: str = ""
    requirements: list[CoverageRequirementSpec] = Field(default_factory=list)
    crossed_factors: list[str] = Field(default_factory=list)
    query_scope: str = "question_specific"
    provider_id: str = ""
    query_artifact_uri: str = ""
    query_artifact_hash: str = ""


class RequirementEvidenceBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    binding_id: str
    requirement_id: str
    evidence_id: str
    evidence_maturity: EvidenceMaturity = EvidenceMaturity.E0_FIXTURE
    evidence_source_class: EvidenceSourceClass = EvidenceSourceClass.FIXTURE
    satisfied: bool = False
    required_count: int = 1
    observed_count: int | None = None
    count_factor: str = ""
    scoped_counts: dict[str, int] = Field(default_factory=dict)
    scope: dict[str, str] = Field(default_factory=dict)
    rationale: str = ""

    @property
    def supports_contract_readiness(self) -> bool:
        return (
            self.satisfied
            and self.evidence_maturity.rank >= EvidenceMaturity.E4_QUESTION_VALIDATED.rank
            and self.evidence_source_class != EvidenceSourceClass.FIXTURE
        )


class JointCoverageReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    query: JointCoverageQuery
    counts: dict[str, int] = Field(default_factory=dict)
    missing_requirements: list[str] = Field(default_factory=list)
    thin_combinations: list[str] = Field(default_factory=list)
    balance_notes: list[str] = Field(default_factory=list)
    simultaneity_notes: list[str] = Field(default_factory=list)
    split_feasibility: str = ""
    bindings: list[RequirementEvidenceBinding] = Field(default_factory=list)
    evidence_requests: list[EvidenceRequest] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)

    @property
    def supports_contract_readiness(self) -> bool:
        requirement_ids = {requirement.requirement_id for requirement in self.query.requirements}
        satisfied_ids = {
            binding.requirement_id
            for binding in self.bindings
            if binding.supports_contract_readiness
        }
        return (
            bool(requirement_ids)
            and requirement_ids <= satisfied_ids
            and not any(request.blocking for request in self.evidence_requests)
        )


class IBLDatasetEvidenceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bundle_id: str
    dataset_id: str = "ibl_bwm"
    dataset_version: str
    source_refs: list[str] = Field(default_factory=list)
    dataset_card_id: str = ""
    joint_coverage_reports: list[JointCoverageReport] = Field(default_factory=list)
    evidence_requests: list[EvidenceRequest] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_versioned_sources(self) -> IBLDatasetEvidenceBundle:
        if not self.dataset_version.strip():
            raise ValueError("IBLDatasetEvidenceBundle requires dataset_version")
        return self

    @property
    def supports_contract_readiness(self) -> bool:
        return (
            bool(self.joint_coverage_reports)
            and all(report.supports_contract_readiness for report in self.joint_coverage_reports)
            and not any(request.blocking for request in self.evidence_requests)
        )


class HierarchyEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    child: str
    parent: str
    relation: str = "nested_in"
    note: str = ""
    evidence: list[EvidenceRef] = Field(default_factory=list)


class DataSurfaceCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surface_id: str
    version: str = ""
    root: str = ""
    schema_path: str = ""
    tables: dict[str, list[str]] = Field(default_factory=dict)
    row_counts: dict[str, int] = Field(default_factory=dict)
    join_keys: dict[str, list[str]] = Field(default_factory=dict)
    status: str = "declared"
    notes: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)

    def has_column(self, column: str) -> bool:
        normalized = column.strip().lower()
        return any(
            normalized == item.lower() for columns in self.tables.values() for item in columns
        )


class SurfaceInspectionReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_id: str
    surfaces: list[DataSurfaceCard] = Field(default_factory=list)
    coverage: CoverageSummary = Field(default_factory=CoverageSummary)
    warnings: list[str] = Field(default_factory=list)
    unavailable_optional_dependencies: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)


class MeasurementCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    measurement_id: str
    label: str
    constructs: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    modality: str
    direct_or_proxy: str = "direct"
    unit: str = ""
    hierarchy_level: str = ""
    time_reference: str = ""
    spatial_reference: str = ""
    valid_population: str = ""
    source_surfaces: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)

    def matches(self, term: str) -> bool:
        normalized = _normalize(term)
        candidates = {
            _normalize(self.measurement_id),
            _normalize(self.label),
            *(_normalize(c) for c in self.constructs),
            *(_normalize(v) for v in self.variables),
        }
        return normalized in candidates

    @property
    def is_proxy(self) -> bool:
        normalized = self.direct_or_proxy.lower()
        return "proxy" in normalized or "operationalized" in normalized


class DesignCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    design_types: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    observational: bool = True
    has_intervention: bool = False
    randomized_assignment: bool = False
    longitudinal: bool = False
    repeated_measures: bool = True
    sampling_frame: str = ""
    selection_notes: list[str] = Field(default_factory=list)
    known_confounders: list[str] = Field(default_factory=list)
    supported_claim_levels: list[ClaimLevel] = Field(
        default_factory=lambda: [
            ClaimLevel.DESCRIPTIVE,
            ClaimLevel.PREDICTIVE,
            ClaimLevel.ASSOCIATIONAL,
        ]
    )
    evidence: list[EvidenceRef] = Field(default_factory=list)

    def supports_feature(self, feature: str) -> bool:
        feature = _normalize(feature)
        built_ins = {
            "observational": self.observational,
            "intervention": self.has_intervention,
            "randomized_assignment": self.randomized_assignment,
            "longitudinal": self.longitudinal,
            "repeated_measures": self.repeated_measures,
        }
        if feature in built_ins:
            return built_ins[feature]
        return feature in {_normalize(item) for item in self.features}


class DatasetCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    version: str
    title: str
    description: str
    domain: str
    modalities: list[str] = Field(default_factory=list)
    populations: list[str] = Field(default_factory=list)
    hierarchy: list[str] = Field(default_factory=list)
    hierarchy_edges: list[HierarchyEdge] = Field(default_factory=list)
    identifiers: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    interventions: list[str] = Field(default_factory=list)
    measurements: list[MeasurementCard] = Field(default_factory=list)
    surfaces: list[DataSurfaceCard] = Field(default_factory=list)
    design: DesignCard = Field(default_factory=DesignCard)
    coverage: CoverageSummary = Field(default_factory=CoverageSummary)
    metadata: dict[str, Any] = Field(default_factory=dict)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    conflicts: list[EvidenceConflict] = Field(default_factory=list)

    def has_measurement(self, term: str) -> bool:
        return bool(self.find_measurements(term))

    def find_measurements(self, term: str) -> list[MeasurementCard]:
        return [measurement for measurement in self.measurements if measurement.matches(term)]

    def has_hierarchy_level(self, level: str) -> bool:
        normalized = _normalize(level)
        aliases = {"neuron": "unit", "animal": "subject", "mouse": "subject", "insertion": "probe"}
        normalized = aliases.get(normalized, normalized)
        return normalized in {_normalize(item) for item in self.hierarchy}

    def has_event(self, event: str) -> bool:
        normalized = _normalize(event)
        aliases = {
            "stimulus_onset": {"stimulus_onset", "stimon_times", "stim_on"},
            "first_movement": {"first_movement", "firstmovement_times", "movement_onset"},
            "response": {"response", "response_times"},
            "feedback": {"feedback", "feedback_times"},
        }
        available = {_normalize(item) for item in self.events}
        if normalized in available:
            return True
        return any(normalized in values and bool(values & available) for values in aliases.values())

    def supports_design_feature(self, feature: str) -> bool:
        normalized = _normalize(feature)
        identifier_features = {
            "subject_identifiers": "subject",
            "session_identifiers": "session",
            "probe_identifiers": "probe",
            "lab_identifiers": "lab",
            "trial_identifiers": "trial",
        }
        if normalized in identifier_features:
            target = identifier_features[normalized]
            return self.has_hierarchy_level(target) and any(
                target in _normalize(identifier) for identifier in self.identifiers
            )
        if normalized in {"temporal_alignment", "event_timing"}:
            return bool(self.events)
        if normalized in {"three_dimensional_coordinates", "spatial_coordinates"}:
            return self.has_measurement("three_dimensional_coordinates") or self.has_measurement(
                "anatomical_position"
            )
        return self.design.supports_feature(normalized)

    def hierarchy_rank(self, level: str) -> int | None:
        aliases = {"neuron": "unit", "animal": "subject", "mouse": "subject", "insertion": "probe"}
        normalized = aliases.get(_normalize(level), _normalize(level))
        levels = [_normalize(item) for item in self.hierarchy]
        try:
            return levels.index(normalized)
        except ValueError:
            return None


class ConstructResolution(BaseModel):
    model_config = ConfigDict(extra="forbid")

    construct_name: str
    candidate_measurements: list[str] = Field(default_factory=list)
    selected_measurement: str | None = None
    caveats: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    evidence: list[EvidenceRef] = Field(default_factory=list)


def _normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")
