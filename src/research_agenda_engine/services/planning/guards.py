from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

FORBIDDEN_PLANNER_OUTPUT_TERMS: tuple[str, ...] = (
    "questioncard",
    "analysiscontract",
    "contract_eligible",
    "execution_authorized",
    "execution receipt",
    "execution_id",
    "agent_run_id",
    "completion receipt",
    "ibl handoff",
    "confirmation outcome",
    "confirmatory result",
    "heldout_results",
    "held-out result",
    "p-value",
    "p_value",
    "effect-size scan",
    "effect search",
    "accepted closure",
    "closure_recorded",
)

_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("questioncard", re.compile(r"\bquestion\s*card\b|\bquestioncard\b", re.I)),
    ("analysiscontract", re.compile(r"\banalysis\s*contract\b|\banalysiscontract\b", re.I)),
    ("execution receipt", re.compile(r"\bexecution\s+receipt\b", re.I)),
    ("execution_id", re.compile(r"\bexecution[_ -]?id\b", re.I)),
    ("agent_run_id", re.compile(r"\bagent[_ -]?run[_ -]?id\b", re.I)),
    ("completion receipt", re.compile(r"\bcompletion\s+receipt\b", re.I)),
    ("ibl handoff", re.compile(r"\bibl\s+handoff\b", re.I)),
    ("confirmation outcome", re.compile(r"\bconfirmation\s+outcomes?\b", re.I)),
    ("confirmatory result", re.compile(r"\bconfirmatory\s+results?\b", re.I)),
    ("heldout_results", re.compile(r"\bheldout[_ -]?results?\b", re.I)),
    ("held-out result", re.compile(r"\bheld[- ]out\s+results?\b", re.I)),
    ("p-value", re.compile(r"\bp[-_\s]?values?\b", re.I)),
    ("effect-size scan", re.compile(r"\beffect[- ]size\s+scan\b", re.I)),
    ("effect search", re.compile(r"\beffect\s+search\b", re.I)),
    ("accepted closure", re.compile(r"\baccepted\s+closure\b", re.I)),
    ("closure_recorded", re.compile(r"\bclosure[_ -]?recorded\b", re.I)),
)

_FULL_LOCAL_RESULT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "raw uuid identifier",
        re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            re.I,
        ),
    ),
    ("raw rows", re.compile(r"\b(raw|full)\s+rows?\b", re.I)),
    ("raw spike times", re.compile(r"\braw\s+spike\s+times?\b|\bspike_times_seconds\b", re.I)),
    ("neural matrix values", re.compile(r"\b(matrix|tensor)\s+values?\b", re.I)),
    (
        "covariance result",
        re.compile(r"\b(covariance|shared[- ]?variance)\s+(estimate|value|result|score)s?\b", re.I),
    ),
    (
        "correlation result",
        re.compile(r"\bcorrelation\s+(coefficient|estimate|value|result|score)s?\b", re.I),
    ),
    (
        "regression result",
        re.compile(r"\bregression\s+(coefficient|estimate|value|result|score)s?\b", re.I),
    ),
    ("decoding score", re.compile(r"\bdecoding\s+(score|accuracy|auc|result)s?\b", re.I)),
    (
        "ranked effect",
        re.compile(r"\b(best|top|ranked)\s+(contrast|region|effect|score)s?\b", re.I),
    ),
    ("p-value", re.compile(r"\bp[-_\s]?values?\b|\bconfidence\s+intervals?\b|\bci95\b", re.I)),
    ("alf array path", re.compile(r"\balf\b.*\.(npy|npz)\b|\.(npy|npz)\b.*\balf\b", re.I)),
    ("spike shard path", re.compile(r"\bspikes/[0-9a-f-]{32,}/", re.I)),
)

_FORBIDDEN_KEYS_ALWAYS = {
    "agent_run_id": "agent_run_id",
    "execution_id": "execution_id",
    "execution_receipt": "execution receipt",
    "execution_receipt_id": "execution receipt",
    "completion_receipt": "completion receipt",
    "completion_receipt_id": "completion receipt",
    "questioncard": "questioncard",
    "question_card": "questioncard",
    "analysiscontract": "analysiscontract",
    "analysis_contract": "analysiscontract",
    "ibl_handoff": "ibl handoff",
    "confirmation_outcome": "confirmation outcome",
    "confirmation_outcomes": "confirmation outcome",
    "confirmatory_result": "confirmatory result",
    "confirmatory_results": "confirmatory result",
    "heldout_results": "heldout_results",
    "held_out_results": "held-out result",
    "closure_recorded": "closure_recorded",
}

_FORBIDDEN_KEYS_WHEN_TRUTHY = {
    "contract_eligible": "contract_eligible",
    "execution_authorized": "execution_authorized",
    "bridge_created": "execution_authorized",
    "questioncard_created": "questioncard",
    "analysiscontract_created": "analysiscontract",
}

_FORBIDDEN_FULL_LOCAL_KEYS_ALWAYS = {
    "raw_rows": "raw rows",
    "full_rows": "raw rows",
    "row_excerpt": "raw rows",
    "row_excerpts": "raw rows",
    "raw_spike_times": "raw spike times",
    "spike_times_seconds": "raw spike times",
    "neural_matrix": "neural matrix values",
    "neural_matrix_values": "neural matrix values",
    "matrix_values": "neural matrix values",
    "covariance": "covariance result",
    "covariance_value": "covariance result",
    "covariance_estimate": "covariance result",
    "shared_variance_value": "covariance result",
    "correlation": "correlation result",
    "correlation_coefficient": "correlation result",
    "regression_coefficient": "regression result",
    "decoding_score": "decoding score",
    "decoding_accuracy": "decoding score",
    "p_value": "p-value",
    "p_values": "p-value",
    "confidence_interval": "p-value",
    "confidence_intervals": "p-value",
    "best_contrast": "ranked effect",
    "best_region": "ranked effect",
    "ranked_effects": "ranked effect",
}


def find_forbidden_planner_terms(value: Any) -> list[str]:
    """Return downstream/execution terms found in planner-facing payloads."""

    matches: list[str] = []

    def add(term: str) -> None:
        if term not in matches:
            matches.append(term)

    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                normalized_key = _normalize_key(str(key))
                if normalized_key in _FORBIDDEN_KEYS_ALWAYS:
                    add(_FORBIDDEN_KEYS_ALWAYS[normalized_key])
                if normalized_key in _FORBIDDEN_KEYS_WHEN_TRUTHY and _is_truthy(nested):
                    add(_FORBIDDEN_KEYS_WHEN_TRUTHY[normalized_key])
                walk(nested)
            return
        if isinstance(item, str):
            for label, pattern in _TEXT_PATTERNS:
                if pattern.search(item):
                    add(label)
            return
        if isinstance(item, Sequence) and not isinstance(item, (bytes, bytearray)):
            for nested in item:
                walk(nested)

    walk(value)
    return matches


def assert_no_forbidden_planner_terms(value: Any, *, context: str) -> None:
    matches = find_forbidden_planner_terms(value)
    if matches:
        raise ValueError(
            f"{context} contains forbidden downstream/execution terms: {', '.join(matches)}"
        )


def find_forbidden_full_local_result_terms(value: Any) -> list[str]:
    """Return result/raw-data leakage terms forbidden in full-local planning artifacts."""

    matches: list[str] = []

    def add(term: str) -> None:
        if term not in matches:
            matches.append(term)

    def walk(item: Any, *, parent_key: str = "") -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                normalized_key = _normalize_key(str(key))
                if normalized_key in _FORBIDDEN_FULL_LOCAL_KEYS_ALWAYS:
                    add(_FORBIDDEN_FULL_LOCAL_KEYS_ALWAYS[normalized_key])
                walk(nested, parent_key=normalized_key)
            return
        if isinstance(item, str):
            if parent_key in {
                "forbidden_persisted_outputs",
                "forbidden_computation_classes",
                "limitations",
            }:
                return
            for label, pattern in _FULL_LOCAL_RESULT_PATTERNS:
                if pattern.search(item):
                    add(label)
            return
        if isinstance(item, Sequence) and not isinstance(item, (bytes, bytearray)):
            for nested in item:
                walk(nested, parent_key=parent_key)

    walk(value)
    return matches


def assert_no_forbidden_full_local_result_terms(value: Any, *, context: str) -> None:
    matches = find_forbidden_full_local_result_terms(value)
    if matches:
        raise ValueError(
            f"{context} contains forbidden full-local planning outputs: {', '.join(matches)}"
        )


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "false", "no", "0", "none", "null"}
    if isinstance(value, Iterable):
        return bool(value)
    return bool(value)
