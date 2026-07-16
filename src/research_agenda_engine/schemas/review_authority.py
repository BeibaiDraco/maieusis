"""Centralized honest-authority predicates across front-half artifact review statuses.

Front-half artifacts (PaperCase, PaperLocalLiterature, QuestionFormationTrace, QuestionPatternCard,
TopicEvidenceBrief, DatasetNarrative) each carry their own per-type review-status enum, but they share
a single authority ladder:

* **automated / non-human tier** — an independent-AI gate accepted the artifact. Two labels denote the
  **same** tier: ``ai_reviewed`` (the 5a-1 front-half gates) and ``automated_reviewed`` (5a-0's
  DatasetNarrative — kept for compatibility, NOT renamed). They are the same authority level.
* **human tier** — ``expert_reviewed`` (a real human decision import).

Downstream consumers accept BOTH honest tiers. To avoid scattering ``{AI_REVIEWED, AUTOMATED_REVIEWED}``
literals across N consumers (and the V2 min-authority rule), every consumer routes through the
predicates here. Passing a raw string or an enum member both work.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from enum import Enum

# The two labels for the SAME automated / non-human authority tier.
AUTOMATED_AUTHORITY_VALUES = frozenset({"ai_reviewed", "automated_reviewed"})
# The human tier. Two labels denote the SAME human authority: ``expert_reviewed`` (most artifacts) and
# ``human_reviewed`` (the QuestionFamily generation enum). Named HUMAN (not EXPERT) so the constant does
# not mislead — it holds both.
HUMAN_AUTHORITY_VALUES = frozenset({"expert_reviewed", "human_reviewed"})
# Every honest "accepted" (proposal-ready) authority a downstream consumer may admit.
ACCEPTED_AUTHORITY_VALUES = AUTOMATED_AUTHORITY_VALUES | HUMAN_AUTHORITY_VALUES


def _value(status: object) -> str:
    return status.value if isinstance(status, Enum) else str(status)


def is_automated_authority(status: object) -> bool:
    """True for an independent-AI-accepted status (``ai_reviewed`` or ``automated_reviewed``)."""
    return _value(status) in AUTOMATED_AUTHORITY_VALUES


def is_human_authority(status: object) -> bool:
    """True for a human-reviewed status (``expert_reviewed`` or ``human_reviewed``)."""
    return _value(status) in HUMAN_AUTHORITY_VALUES


def is_accepted_authority(status: object) -> bool:
    """True for either honest accepted tier (automated OR human). The downstream-admit predicate."""
    return _value(status) in ACCEPTED_AUTHORITY_VALUES
