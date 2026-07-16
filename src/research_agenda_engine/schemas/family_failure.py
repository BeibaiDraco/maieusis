"""Typed diagnostics and source sanitizer for back-half family failure text.

Raw exception text is internal evidence and may contain credentials, provider request identifiers,
local paths, serialized authority/result fields, or unbounded payload echoes.  The public sanitizer
removes those concrete hazards while leaving ordinary scientific and planning language alone.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .stage_receipt import FailureClass

MAX_PUBLIC_FAMILY_FAILURE_TEXT = 500
MAX_INTERNAL_FAMILY_FAILURE_TEXT = 2000
SAFE_FAMILY_FAILURE_REASON = (
    "This family did not complete its planning review; see the run diagnostics for details."
)

_UNSAFE_FAMILY_FAILURE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\brequest[_ -]?id\s*[:=]\s*\S+|\breq_[A-Za-z0-9_-]+\b",
        re.I,
    ),
    re.compile(r"\berror\s+code\s*:\s*[45]\d\d\b", re.I),
    re.compile(
        r"\b(?:api[_ -]?key|authorization|bearer)\s*[:=]\s*\S+|"
        r"\bsk-[A-Za-z0-9_-]{12,}\b",
        re.I,
    ),
    re.compile(r"(?:^|\s)/(?:Users|private/tmp|tmp|var/folders)/\S+", re.I),
    re.compile(
        r"\b(?:execution_authorized|bridge_created|questioncard_created|"
        r"analysiscontract_created)\s*[:=]\s*(?:true|yes|1)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:confirmation_outcomes?|confirmatory_results?|held[_ -]?out_results?)"
        r"\s*[:=]",
        re.I,
    ),
    re.compile(r"\bR5(?:-[A-Za-z0-9]+)?\b"),
    re.compile(r"\bM1[A-Z]\d*\b"),
    re.compile(r"(?<![A-Za-z])cfam[-_]\d+", re.I),
    re.compile(r"\b(?:qfamily-)?branch-[0-9a-f]{6,}(?:[/\\][^\s|]*)?", re.I),
    re.compile(r"\bevent-[0-9a-f]{6,}\b", re.I),
)


def sanitize_family_failure_text(value: str) -> str:
    """Return bounded public text without treating ordinary scientific prose as secret.

    The public sanitizer is intentionally about transport/internal identifiers, credentials,
    local paths, raw payload size, and serialized authority/result fields.  Method language such
    as ``execution``, ``p-value``, ``effect size``, ``significant``, or ``model result`` is not a
    security boundary and remains visible.  Typed schemas and structured boundary validators own
    scientific authority; an English-word deny-list must not impersonate them.
    """
    cleaned = " ".join(value.split())
    if not cleaned:
        return ""
    if len(cleaned) > MAX_PUBLIC_FAMILY_FAILURE_TEXT:
        return SAFE_FAMILY_FAILURE_REASON
    if any(pattern.search(cleaned) for pattern in _UNSAFE_FAMILY_FAILURE_PATTERNS):
        return SAFE_FAMILY_FAILURE_REASON
    return cleaned


class BackHalfLineage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    families_generated: bool
    family_ids: list[str] = Field(default_factory=list)
    planners_ran: bool
    processed_family_ids: list[str] = Field(default_factory=list)
    planner_run_record_paths: list[str] = Field(default_factory=list)


class BackHalfFailureDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    diagnostic_id: str
    code: Literal[
        "back_half_terminal",
        "family_failure_recorded",
        "family_failure_text_sanitized",
    ]
    scope: Literal["run", "family"]
    stage: Literal["back_half"] = "back_half"
    question_family_id: str = ""
    failure_class: FailureClass
    exception_type: str
    raw_text: str
    sanitized_text: str
    lineage: BackHalfLineage
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
