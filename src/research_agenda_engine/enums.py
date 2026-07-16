from __future__ import annotations

from enum import StrEnum


class ClaimLevel(StrEnum):
    DESCRIPTIVE = "descriptive"
    PREDICTIVE = "predictive"
    ASSOCIATIONAL = "associational"
    MECHANISTIC = "mechanistic"
    CAUSAL = "causal"

    @property
    def rank(self) -> int:
        """Compatibility ordering used only for conservative claim ceilings.

        Predictive and associational claims are not philosophically a total order. The
        engine also records the explicit set of supported claim levels; callers should
        prefer that set over rank comparisons when possible.
        """
        return {
            ClaimLevel.DESCRIPTIVE: 0,
            ClaimLevel.PREDICTIVE: 1,
            ClaimLevel.ASSOCIATIONAL: 2,
            ClaimLevel.MECHANISTIC: 3,
            ClaimLevel.CAUSAL: 4,
        }[self]


class AnswerabilityVerdict(StrEnum):
    CONFIRMATORY_ANSWERABLE = "confirmatory_answerable"
    EXPLORATORY_ONLY = "exploratory_only"
    ANSWERABLE_AFTER_REPAIR = "answerable_after_repair"
    SCIENTIFICALLY_ANSWERABLE_BUT_SKILL_MISSING = "scientifically_answerable_but_skill_missing"
    UNDERPOWERED_OR_POOR_COVERAGE = "underpowered_or_poor_coverage"
    NOT_ANSWERABLE_BY_DESIGN = "not_answerable_by_design"
    INSUFFICIENT_METADATA = "insufficient_metadata"

    @property
    def is_accepted(self) -> bool:
        return self in {
            AnswerabilityVerdict.CONFIRMATORY_ANSWERABLE,
            AnswerabilityVerdict.EXPLORATORY_ONLY,
            AnswerabilityVerdict.ANSWERABLE_AFTER_REPAIR,
        }

    @property
    def is_scientifically_answerable(self) -> bool:
        return self in {
            AnswerabilityVerdict.CONFIRMATORY_ANSWERABLE,
            AnswerabilityVerdict.EXPLORATORY_ONLY,
            AnswerabilityVerdict.ANSWERABLE_AFTER_REPAIR,
            AnswerabilityVerdict.SCIENTIFICALLY_ANSWERABLE_BUT_SKILL_MISSING,
        }


class AnswerabilityDimension(StrEnum):
    QUESTION_SPECIFICATION = "question_specification"
    MEASUREMENT = "measurement"
    COVERAGE = "coverage"
    DESIGN = "design"
    HIERARCHY = "hierarchy"
    TEMPORAL = "temporal"
    ESTIMABILITY = "estimability"
    EXECUTABILITY = "executability"
    FALSIFIABILITY = "falsifiability"
    DATA_FIREWALL = "data_firewall"


class CheckStatus(StrEnum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class EvidenceKind(StrEnum):
    DOCUMENTATION = "documentation"
    AGENT_ASSERTION = "agent_assertion"
    TOOL_QUERY = "tool_query"
    STATIC_CODE_INSPECTION = "static_code_inspection"
    SCHEMA_INSPECTION = "schema_inspection"
    DRY_RUN = "dry_run"
    EXECUTION = "execution"
    EXPERT_REVIEW = "expert_review"
    LITERATURE = "literature"


class RunMode(StrEnum):
    DEMO = "demo"
    SCIENTIFIC = "scientific"


class EvidenceMaturity(StrEnum):
    E0_FIXTURE = "E0_fixture"
    E1_DECLARED = "E1_declared"
    E2_METADATA_SCREENED = "E2_metadata_screened"
    E3_OPERATOR_DEMONSTRATED = "E3_operator_demonstrated"
    E4_QUESTION_VALIDATED = "E4_question_validated"
    E5_EXECUTION_VALIDATED = "E5_execution_validated"

    @property
    def rank(self) -> int:
        return {
            EvidenceMaturity.E0_FIXTURE: 0,
            EvidenceMaturity.E1_DECLARED: 1,
            EvidenceMaturity.E2_METADATA_SCREENED: 2,
            EvidenceMaturity.E3_OPERATOR_DEMONSTRATED: 3,
            EvidenceMaturity.E4_QUESTION_VALIDATED: 4,
            EvidenceMaturity.E5_EXECUTION_VALIDATED: 5,
        }[self]


class EvidenceSourceClass(StrEnum):
    FIXTURE = "fixture"
    USER_DECLARED = "user_declared"
    API_METADATA = "api_metadata"
    LOCAL_METADATA_PROBE = "local_metadata_probe"
    DRY_RUN_RECEIPT = "dry_run_receipt"
    EXPERT_REVIEW = "expert_review"
    EXECUTION_RECEIPT = "execution_receipt"


class VerificationStatus(StrEnum):
    PROPOSED = "proposed"
    DECLARED = "declared"
    DEMONSTRATED = "demonstrated"
    VALIDATED = "validated"
    CONTRADICTED = "contradicted"

    @property
    def trust_weight(self) -> float:
        return {
            VerificationStatus.PROPOSED: 0.15,
            VerificationStatus.DECLARED: 0.35,
            VerificationStatus.DEMONSTRATED: 0.70,
            VerificationStatus.VALIDATED: 0.95,
            VerificationStatus.CONTRADICTED: 0.0,
        }[self]


class CapabilityStatus(StrEnum):
    DECLARED = "declared"
    DEMONSTRATED = "demonstrated"
    VALIDATED = "validated"
    CONTRADICTED = "contradicted"
    DEPRECATED = "deprecated"

    @property
    def rank(self) -> int:
        return {
            CapabilityStatus.CONTRADICTED: -1,
            CapabilityStatus.DECLARED: 0,
            CapabilityStatus.DEMONSTRATED: 1,
            CapabilityStatus.VALIDATED: 2,
            CapabilityStatus.DEPRECATED: -2,
        }[self]


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


class QuestionOrigin(StrEnum):
    DESIGN_DRIVEN = "design_driven"
    LITERATURE_DRIVEN = "literature_driven"
    EXPLORATION_DRIVEN = "exploration_driven"
    HUMAN = "human"
    MUTATION = "mutation"


class ContractState(StrEnum):
    DRAFT = "draft"
    EXPERT_REVIEWED = "expert_reviewed"
    LOCKED = "locked"
    EXECUTION_STARTED = "execution_started"
    COMPLETED = "completed"
    INVALIDATED = "invalidated"


class PipelineStage(StrEnum):
    INITIALIZED = "initialized"
    EVIDENCE_COMPILED = "evidence_compiled"
    QUESTIONS_GENERATED = "questions_generated"
    ANSWERABILITY_EVALUATED = "answerability_evaluated"
    VALUE_EVALUATED = "value_evaluated"
    PORTFOLIO_SELECTED = "portfolio_selected"
    CONTRACT_DRAFTED = "contract_drafted"
    CONTRACT_LOCKED = "contract_locked"
    HANDED_OFF = "handed_off"
    RESULT_INGESTED = "result_ingested"


class ExpertReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    REVIEWED = "reviewed"
    ADJUDICATED = "adjudicated"


class NonTrivialityVerdict(StrEnum):
    NON_TRIVIAL = "non_trivial"
    BORDERLINE = "borderline"
    TRIVIAL = "trivial"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class P5ReadinessStatus(StrEnum):
    PASS = "pass"
    REPAIR_REQUIRED = "repair_required"
    HOLD = "hold"
