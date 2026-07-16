"""Deterministic demo topic field-state draft.

The config-reachable
``subscription_only_demo`` deterministic generation assets (public_optional). Demo mode is
an explicit mock + FakePlannerHost workflow demonstration — never a scientific-quality
claim (the demo banner and development_model_surrogate authority labels flow to every
output surface).
"""

from __future__ import annotations

from research_agenda_engine.services.context import (
    TOPIC_FIELD_STATE_REQUIRED_SECTIONS,
    TopicFieldStateDraft,
    TopicFieldStateSection,
)


def _field_state_draft(source_record_ids: list[str] | None = None) -> TopicFieldStateDraft:
    ids = source_record_ids or ["source-1"]
    return TopicFieldStateDraft(
        field_state_id="field-state-draft-test",
        sections=[
            TopicFieldStateSection(
                section_id=f"section-{index:02d}",
                heading=heading,
                synthesis=f"{heading} synthesis cites supplied sources.",
                source_record_ids=ids,
            )
            for index, heading in enumerate(TOPIC_FIELD_STATE_REQUIRED_SECTIONS, start=1)
        ],
        review_status="draft",
    )
