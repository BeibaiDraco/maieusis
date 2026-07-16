from __future__ import annotations

import stat
from pathlib import Path

from ...provenance import sha256_file, stable_hash
from ...schemas.generic_scientific_source import DatasetClaimStatus
from ...schemas.question_family_branch import QuestionFamilyInspectionEvidence


def bind_host_verified_evidence_source(
    evidence: QuestionFamilyInspectionEvidence,
    *,
    source_path: str | Path,
) -> QuestionFamilyInspectionEvidence:
    """Bind one existing evidence record to bytes the host can actually inspect.

    This is intentionally a narrow local-source seam, not a receipt warehouse. It verifies the
    source locator and bytes; it does not convert the planner's scientific interpretation into a
    result claim.
    """

    candidate = Path(source_path)
    candidate_stat = candidate.lstat()
    if candidate.is_symlink() or not stat.S_ISREG(candidate_stat.st_mode):
        raise ValueError("host evidence source must be a non-symlink regular file")
    if Path(evidence.source_locator).resolve() != candidate.resolve():
        raise ValueError("host evidence source does not match source_locator")
    source_digest = sha256_file(candidate)
    if source_digest != evidence.source_digest:
        raise ValueError("host evidence source digest mismatch")
    host_binding_digest = stable_hash(
        {
            "evidence_id": evidence.evidence_id,
            "source_path": str(candidate.resolve()),
            "source_digest": source_digest,
            "query_or_command_digest": evidence.query_or_command_digest,
            "result_digest": evidence.result_digest,
        }
    )
    return QuestionFamilyInspectionEvidence.model_validate(
        evidence.model_dump(mode="python")
        | {
            "dataset_claim_status": DatasetClaimStatus.VERIFIED,
            "host_binding_digest": host_binding_digest,
        }
    )


def require_planner_evidence_unverified(evidence: QuestionFamilyInspectionEvidence) -> None:
    if evidence.dataset_claim_status != DatasetClaimStatus.UNVERIFIED:
        raise ValueError("planner-authored evidence must enter with unverified dataset claims")
