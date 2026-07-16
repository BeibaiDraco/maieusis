"""Construct-probe map validation (product core).

Extracted from the retired ``semantic_metadata_probe.py``: the product handoff
packet builder (``dataset_planner_packet``) needs only these dataset-agnostic
validators, which have ZERO IBL dependencies. Keeping them here severs the product
-> the retired pilot-family -> dataset (local_bwm/manifest) closure edge that its probe runner
otherwise created (DEC-E: zero IBL Python in the product core).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ...schemas.planner_probe import ConstructProbeMap
from ...schemas.question_family_branch import (
    QuestionFamilyBranch,
    QuestionFamilyBranchEventScope,
    QuestionFamilyInspectionEvidence,
)
from .planner_boundaries import find_planner_boundary_violations

_RAW_IDENTIFIER_KEYS: dict[str, str] = {
    "eid": "raw session identifier",
    "eids": "raw session identifier",
    "pid": "raw probe identifier",
    "pids": "raw probe identifier",
    "subject": "raw subject identifier",
    "subjects": "raw subject identifier",
    "subject_id": "raw subject identifier",
    "subject_ids": "raw subject identifier",
    "session": "raw session identifier",
    "session_id": "raw session identifier",
    "session_ids": "raw session identifier",
    "unit_id": "raw unit identifier",
    "unit_ids": "raw unit identifier",
    "cluster_id": "raw unit identifier",
    "cluster_ids": "raw unit identifier",
}


_SENSITIVE_METADATA_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "credential",
        re.compile(
            r"\b(?:api[_ -]?key|authorization|bearer)\s*[:=]\s*\S+|"
            r"\bsk-[A-Za-z0-9_-]{12,}\b",
            re.I,
        ),
    ),
)


def validate_construct_probe_maps(
    branch: QuestionFamilyBranch,
    *,
    construct_probe_maps: Sequence[ConstructProbeMap | Mapping[str, Any]],
    evidence_by_id: Mapping[str, QuestionFamilyInspectionEvidence],
) -> list[str]:
    errors: list[str] = []
    for raw in construct_probe_maps:
        try:
            probe_map = (
                raw if isinstance(raw, ConstructProbeMap) else ConstructProbeMap.model_validate(raw)
            )
            _validate_probe_map_for_branch(branch, probe_map, evidence_by_id)
            forbidden = find_forbidden_metadata_probe_terms(probe_map.model_dump(mode="json"))
            if forbidden:
                errors.append(
                    f"construct probe map {probe_map.construct_probe_id} contains forbidden "
                    "metadata-probe terms: " + ", ".join(forbidden)
                )
        except Exception as exc:
            errors.append(f"construct probe map invalid: {exc}")
    return errors


def find_forbidden_metadata_probe_terms(value: Any) -> list[str]:
    matches = list(find_planner_boundary_violations(value))

    def add(term: str) -> None:
        if term not in matches:
            matches.append(term)

    def walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                normalized = _normalize_key(str(key))
                if normalized in _RAW_IDENTIFIER_KEYS:
                    add(_RAW_IDENTIFIER_KEYS[normalized])
                if normalized in {"raw_rows", "full_rows", "rows"} and _is_nonempty(nested):
                    add("raw rows")
                if normalized in {"alf_array_path", "alf_array_paths", "npy_path", "npy_paths"}:
                    add("alf array")
                walk(nested)
            return
        if isinstance(item, str):
            for label, pattern in _SENSITIVE_METADATA_PATTERNS:
                if pattern.search(item):
                    add(label)
            if _looks_like_array_path(item):
                add("alf array")
            return
        if isinstance(item, Sequence) and not isinstance(item, (bytes, bytearray)):
            for nested in item:
                walk(nested)

    walk(value)
    return matches


def validate_metadata_value_probe_summary(value: Mapping[str, Any]) -> None:
    forbidden = find_forbidden_metadata_probe_terms(value)
    if forbidden:
        raise ValueError(
            "metadata-value probe summary contains forbidden terms: " + ", ".join(forbidden)
        )


def _validate_probe_map_for_branch(
    branch: QuestionFamilyBranch,
    probe_map: ConstructProbeMap,
    evidence_by_id: Mapping[str, QuestionFamilyInspectionEvidence],
) -> None:
    if probe_map.branch_id != branch.branch_id:
        raise ValueError("construct probe map references another branch")
    if probe_map.question_family_id != branch.question_family_id:
        raise ValueError("construct probe map references another family")
    if (
        probe_map.scope == QuestionFamilyBranchEventScope.VARIANT
        and probe_map.variant_id not in branch.active_variant_ids
    ):
        raise ValueError("construct probe map references inactive variant")
    unsupported = [
        evidence_id
        for evidence_id in probe_map.evidence_ids
        if evidence_id not in evidence_by_id
        or not evidence_by_id[evidence_id].can_support_variant(probe_map.variant_id)
    ]
    if unsupported:
        raise ValueError(
            "construct probe map references unsupported evidence: " + ", ".join(unsupported)
        )


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _is_nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return bool(value)
    return bool(value)


def _looks_like_array_path(value: str) -> bool:
    path = Path(value)
    suffixes = {suffix.lower() for suffix in path.suffixes}
    lowered = value.lower()
    return bool({".npy", ".npz", ".pqt"} & suffixes and ("alf" in lowered or "spike" in lowered))
