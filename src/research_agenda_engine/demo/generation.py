"""The subscription_only_demo generation seam.

Assembles the deterministic demo factories (this package) into a ``DemoStageExecutor`` and
the demo draft / topic-table sources, so ``execute_run_from_config`` runs the whole A→G chain
config-reachably with ZERO paid calls and ZERO coding-agent spawns. Demo mode is an explicit
mock + FakePlannerHost workflow demonstration — never a scientific-quality claim; the demo
banner and ``development_model_surrogate`` authority labels flow to every output surface.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from ..providers.coding_agents import FakePlannerHost
from ..providers.models.mock import MockModelProvider
from ..providers.scientific_agents.mock import MockScientificAgentProvider
from ..schemas.gate_outcome import (
    GateCriterionAssessment,
    GateModelDecision,
    GateReviewContent,
)
from ..schemas.paper_case import PaperCaseReview, PaperCaseReviewStatus
from ..schemas.question_pattern import QuestionPatternCard, QuestionPatternTransferScope
from ..schemas.topic_literature import TopicSourceTable
from ..services.agents.citation_importance_reviewer import CITATION_IMPORTANCE_CRITERIA
from ..services.agents.dataset_narrative_reviewer import DatasetNarrativeFidelityDecision
from ..services.agents.formation_trace_reviewer import FORMATION_TRACE_CRITERIA
from ..services.agents.paper_case_reviewer import PAPER_CASE_FIDELITY_CRITERIA
from ..services.agents.pattern_reviewer import QUESTION_PATTERN_CRITERIA
from ..services.agents.shortlist_reviewer import SHORTLIST_WORTHINESS_CRITERIA
from ..services.agents.topic_evidence_reviewer import (
    TOPIC_EVIDENCE_CRITERIA,
    TopicEvidenceReviewContent,
)
from ..services.orchestration.end_to_end import StageExecutor
from ..services.paper_ingest.paperbank_gate import PaperCaseDraft
from ..services.paper_patterns.induction import QuestionPatternInductionBatch
from ..services.retrieval.fulltext_fetch import NullFulltextFetcher
from .family import _family_factory
from .field_state import _field_state_draft
from .narrative import _content, _user_doc_factory
from .paper import _linked_case_and_literature, _trace_payload
from .reviewers import _owner_accept, _reviewer_accept
from .topic import _generic_source_table, _ready_gpt_brief

_GATE_CRITERIA = {
    "paper_case_fidelity": PAPER_CASE_FIDELITY_CRITERIA,
    "citation_importance": CITATION_IMPORTANCE_CRITERIA,
    "formation_trace": FORMATION_TRACE_CRITERIA,
    "question_pattern": QUESTION_PATTERN_CRITERIA,
    "topic_evidence": TOPIC_EVIDENCE_CRITERIA,
    "shortlist_worthiness": SHORTLIST_WORTHINESS_CRITERIA,
}


def _induced_pattern() -> QuestionPatternCard:
    """A pattern bound to the deterministic reviewed-record ids (case ``paper-1``, trace draft id)."""
    return QuestionPatternCard(
        pattern_id="pattern-demo",
        pattern_name="Dataset cue tension test",
        starting_scientific_state=["two explanations remain scientifically live"],
        unresolved_tension_pattern=(
            "A literature tension becomes testable when a dataset cue instantiates the "
            "discriminating contrast."
        ),
        dataset_cues=["broad reusable dataset cue"],
        question_formation_move=(
            "Translate the paper-local tension into a dataset-grounded discriminating question."
        ),
        scientific_payoff="Separates competing explanations without claiming execution results.",
        positive_result_consequence="Strengthens the transferred explanatory distinction.",
        negative_result_consequence="Shows the distinction does not survive the dataset cue.",
        common_failure_modes=["The pattern becomes a direct paper-question paraphrase."],
        non_transferable_details=["Original task details are source-paper specific."],
        source_case_ids=["paper-1"],
        source_trace_ids=["trace-draft-paper-1"],
        transfer_scope=QuestionPatternTransferScope.PAPER_SPECIFIC,
    )


def demo_generation_factory(output_model: type[BaseModel], system: str, user: str) -> Any:
    """Dispatch the demo generator by output-model name to a deterministic payload."""
    name = output_model.__name__
    if name == "_TraceDraftModelOutput":
        return _trace_payload(output_model)
    if name == "QuestionPatternInductionBatch":
        return QuestionPatternInductionBatch(patterns=[_induced_pattern()]).model_dump(mode="json")
    if name == "DatasetNarrativeModelOutput":
        return _user_doc_factory(output_model, system, user)
    if name == "TopicFieldStateDraft":
        payload = json.loads(user)
        card_ids = [c["source_record_id"] for c in payload.get("source_evidence_cards", [])[:2]]
        return _field_state_draft(source_record_ids=card_ids).model_dump(mode="json")
    if name == "_TopicEvidenceBriefModelOutput":
        return _ready_gpt_brief().model_dump(mode="json")
    if name in {"QuestionFamilyBatch", "_QuestionScientistFamilyModelOutput"}:
        return _family_factory(output_model, system, user)
    raise AssertionError(f"unexpected output_model in the demo A→G run: {name}")


class DemoStageExecutor(StageExecutor):
    """The subscription_only_demo executor: deterministic mock generation + accept gates +
    explicit FakePlannerHost (the demo is the explicit mock workflow — never a silent Fake)."""

    def generation_provider(self, role: str) -> MockModelProvider:
        # Every demo role rides the same deterministic mock generation.
        return MockModelProvider(factory=demo_generation_factory)

    def gate_session(self, *, gate_name, generator_provider_ids):
        if gate_name == "narrative_fidelity":
            content: Any = _content(DatasetNarrativeFidelityDecision.ACCEPT)
        elif gate_name == "topic_evidence":
            content = TopicEvidenceReviewContent(
                decision=GateModelDecision.ACCEPT,
                criterion_assessments=[
                    GateCriterionAssessment(criterion=c, passed=True)
                    for c in _GATE_CRITERIA[gate_name]
                ],
                essential_evidence_absent=False,
                essential_evidence_gaps=[],
            )
        else:
            content = GateReviewContent(
                decision=GateModelDecision.ACCEPT,
                criterion_assessments=[
                    GateCriterionAssessment(criterion=c, passed=True)
                    for c in _GATE_CRITERIA[gate_name]
                ],
            )
        return MockScientificAgentProvider(
            responses=[content], provider_id="anthropic:opus-4-8", model_id="opus-4-8"
        ).start_session(branch_id="b", session_id=f"{gate_name}-r", prompt_version="v")

    def owner_reviewer_providers(self):
        return _owner_accept(), _reviewer_accept()

    def planner_host_factory(self, run_root):
        return lambda _family_id: FakePlannerHost(outcome="plan")

    def inspection_resources(self):
        from ..services.planning.dataset_planner_packet import generic_inspection_resources

        return generic_inspection_resources()

    def fulltext_fetcher(self):
        return NullFulltextFetcher()


def demo_paper_drafts() -> list[PaperCaseDraft]:
    """One deterministic extracted paper draft for the demo paper half."""
    case, literature = _linked_case_and_literature()
    case = case.model_copy(
        update={
            "review": PaperCaseReview(status=PaperCaseReviewStatus.EXTRACTED),
            "source_sha256": "a" * 64,
        }
    )
    return [PaperCaseDraft(paper_id="paper-1", paper_case=case, literature=literature)]


def demo_topic_source_table() -> TopicSourceTable:
    """The demo generic-lane topic source table (abstract-only; stage C veto→label path)."""
    return _generic_source_table()


def resolve_demo_run_inputs(config, *, executor, drafts, topic_source_table):
    """In demo mode, resolve the executor + drafts + topic table to the deterministic demo assets.

    A no-op outside demo. Used by the run driver AND both resume entry points so the paper-half
    input digests recorded on the fresh run recompute identically on resume (a fully-completed demo
    run then resumes with every stage REUSED — zero re-pay, zero spawn).
    """
    if not config.is_demo:
        return executor, drafts, topic_source_table
    if executor is None:
        executor = DemoStageExecutor(config)
    if drafts is None:
        drafts = demo_paper_drafts()
    if topic_source_table is None:
        topic_source_table = demo_topic_source_table()
    return executor, drafts, topic_source_table
