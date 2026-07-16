"""Deterministic demo owner/reviewer accept providers.

The config-reachable
``subscription_only_demo`` deterministic generation assets (public_optional). Demo mode is
an explicit mock + FakePlannerHost workflow demonstration — never a scientific-quality
claim (the demo banner and development_model_surrogate authority labels flow to every
output surface).
"""

from __future__ import annotations

from research_agenda_engine.providers.scientific_agents import MockScientificAgentProvider


def _owner_accept() -> MockScientificAgentProvider:
    return MockScientificAgentProvider(
        provider_id="mock:owner",
        model_id="mock-owner-model",
        responses=[
            {
                "decision": "accept",
                "rationale": "Mock development owner accepts.",
                "required_changes": [],
                "preserves_scientific_intent": True,
                "material_revision_detected": False,
                "novelty_recheck_required": False,
            }
        ],
    )


def _reviewer_accept() -> MockScientificAgentProvider:
    return MockScientificAgentProvider(
        provider_id="mock:reviewer",
        model_id="mock-reviewer-model",
        responses=[
            {
                "decision": "accept",
                "rationale": "Mock independent reviewer accepts.",
                "required_changes": [],
                "rejection_reason": None,
                "criterion_assessments": [
                    {
                        "criterion": "intent preservation",
                        "status": "pass",
                        "rationale": "preserved",
                        "evidence_ids": [],
                    }
                ],
                "material_revision_detected": False,
                "novelty_recheck_required": False,
            }
        ],
    )
