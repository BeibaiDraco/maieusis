"""Deterministic demo dataset-narrative payload + fidelity gate content.

The config-reachable
``subscription_only_demo`` deterministic generation assets (public_optional). Demo mode is
an explicit mock + FakePlannerHost workflow demonstration — never a scientific-quality
claim (the demo banner and development_model_surrogate authority labels flow to every
output surface).
"""

from __future__ import annotations

from typing import Literal

from research_agenda_engine.services.agents.dataset_narrative_reviewer import (
    DatasetNarrativeFidelityDecision,
    DatasetNarrativeFidelityReviewContent,
    FidelityCriterionAssessment,
)


def _user_doc_factory(_model, _system, _user) -> dict:
    return {
        "dataset_narrative_id": "dn",
        "dataset_id": "ibl_bwm",
        "title": "T",
        "scientific_purpose": "study decisions (from user notes)",
        "population": "mice",
        "task_or_design": "visual decision task",
        "modalities": ["spiking", "behaviour"],
        "broad_scale": "large multi-lab public resource",
        "spatial_or_anatomical_coverage": "brain-wide",
        "temporal_structure": "trial-structured",
        "standardization": "public release",
        "hierarchical_structure": ["subjects", "sessions"],
        "major_variables": ["neural activity"],
        "known_high_level_limitations": ["proposal-stage"],
        "reuse_opportunities": ["broad reuse"],
        "scale_facts": [],
    }


def _crit(
    name: Literal["faithful", "coarse", "trust_harmonized"], passed: bool = True
) -> FidelityCriterionAssessment:
    return FidelityCriterionAssessment(criterion=name, passed=passed, notes="ok")


def _content(
    decision: DatasetNarrativeFidelityDecision, **kw
) -> DatasetNarrativeFidelityReviewContent:
    passed = decision == DatasetNarrativeFidelityDecision.ACCEPT
    return DatasetNarrativeFidelityReviewContent(
        decision=decision,
        rationale=kw.get("rationale", "review"),
        criterion_assessments=[
            _crit("faithful", passed),
            _crit("coarse", passed),
            _crit("trust_harmonized", passed),
        ],
        **{k: v for k, v in kw.items() if k != "rationale"},
    )
