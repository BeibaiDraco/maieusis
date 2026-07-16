from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .planner_failures import HardFamilyIntegrityViolation

_HARD_KEYS_ALWAYS = {
    "agent_run_id",
    "execution_id",
    "execution_receipt",
    "execution_receipt_id",
    "completion_receipt",
    "completion_receipt_id",
    "questioncard",
    "question_card",
    "analysiscontract",
    "analysis_contract",
    "ibl_handoff",
    "confirmation_outcome",
    "confirmation_outcomes",
    "confirmatory_result",
    "confirmatory_results",
    "heldout_results",
    "held_out_results",
    "closure_recorded",
    "raw_rows",
    "full_rows",
    "raw_spike_times",
    "neural_matrix_values",
}
_HARD_KEYS_WHEN_TRUTHY = {
    "contract_eligible",
    "execution_authorized",
    "bridge_created",
    "questioncard_created",
    "analysiscontract_created",
}
_ARTIFACT_VALUE_KEYS = {
    "artifact",
    "artifact_type",
    "output_artifact",
    "output_type",
    "artifact_path",
    "output_path",
    "action",
}
_PROHIBITED_ARTIFACT_VALUE = re.compile(
    r"\b(question\s*card|analysis\s*contract|execution\s+receipt|ibl\s+handoff|"
    r"confirmation\s+outcome|confirmatory\s+result|held[-_ ]?out\s+result)\b",
    re.IGNORECASE,
)


def find_planner_boundary_violations(value: Any) -> list[str]:
    """Find concrete structured authority/result artifacts, without judging ordinary prose."""

    violations: list[str] = []

    def add(label: str) -> None:
        if label not in violations:
            violations.append(label)

    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for raw_key, nested in item.items():
                key = _normalize_key(str(raw_key))
                if key in _HARD_KEYS_ALWAYS:
                    add(key)
                if key in _HARD_KEYS_WHEN_TRUTHY and _is_truthy(nested):
                    add(key)
                if (
                    key in _ARTIFACT_VALUE_KEYS
                    and isinstance(nested, str)
                    and _PROHIBITED_ARTIFACT_VALUE.search(nested)
                ):
                    add(f"{key}:{nested.strip()}")
                walk(nested)
            return
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            for nested in item:
                walk(nested)
            return

    walk(value)
    return violations


def planner_language_warnings(value: Any) -> list[str]:
    """Return no context-free English-word warnings.

    Ordinary planning prose must be free to discuss execution locks, p-values, effects, models,
    significance, and explicitly negated boundary access.  Concrete structured authority/result
    artifacts remain fail-closed in :func:`find_planner_boundary_violations`.
    """

    del value
    return []


def assert_planner_boundary_safe(value: Any, *, context: str) -> None:
    violations = find_planner_boundary_violations(value)
    if violations:
        raise HardFamilyIntegrityViolation(
            f"{context} contains prohibited structured authority/result artifacts: "
            + ", ".join(violations)
        )


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _is_truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "none", "null"}
    return bool(value)
