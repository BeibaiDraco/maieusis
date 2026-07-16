"""Deterministic demo assets (public_optional).

The config-reachable
``subscription_only_demo`` deterministic generation assets (public_optional). Demo mode is
an explicit mock + FakePlannerHost workflow demonstration — never a scientific-quality
claim (the demo banner and development_model_surrogate authority labels flow to every
output surface).
"""

from .family import _family_factory as family_factory
from .field_state import _field_state_draft as field_state_draft
from .narrative import _content as content
from .narrative import _user_doc_factory as user_doc_factory
from .paper import _linked_case_and_literature as linked_case_and_literature
from .paper import _trace_payload as trace_payload
from .reviewers import _owner_accept as owner_accept
from .reviewers import _reviewer_accept as reviewer_accept
from .topic import _generic_source_table as generic_source_table
from .topic import _ready_gpt_brief as ready_gpt_brief

__all__ = [
    "content",
    "family_factory",
    "field_state_draft",
    "generic_source_table",
    "linked_case_and_literature",
    "owner_accept",
    "ready_gpt_brief",
    "reviewer_accept",
    "trace_payload",
    "user_doc_factory",
]
