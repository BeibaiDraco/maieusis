"""Coarse-resume decision + per-family completion schemas.

`maieusis resume <run-id>` re-enters an existing ``runs/<id>/`` tree and finishes it. The decision layer is
COARSE and deliberately simple: stage-level completion-skip with per-stage input-digest invalidation on
the front half, family-level skip on the back half. A stage/family is REUSED only when its persisted
receipt/record proves completed-with-identical-inputs AND every recorded output artifact still exists
with a matching digest; everything else re-runs. There is no journal, no exactly-once, and no
generation/supersession machinery — a crash mid-stage simply re-runs that stage.

These schemas are the durable audit trail of that decision: ``StageResumeDecision`` /
``FamilyResumeDecision`` record what was skipped and WHY (with the digest evidence), and the
``ResumeReceipt`` persists the whole decision set to ``runs/<id>/receipts/resume-<n>.yaml`` BEFORE any
execution. ``FamilyCompletionRecord`` is the per-family durable completion record the driver writes at
back-half layout time so a later resume can feed completed families to the orchestrator's
``completed_records`` seam (zero re-spawn) without touching the orchestrator.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .multi_family_dossier import FamilyDossierOutputRecord
from .run_outcome import FamilyRunOutcome


class StageResumeDecisionKind(StrEnum):
    REUSE = "reuse"
    RUN = "run"
    TERMINAL_NOT_APPLICABLE = "terminal_not_applicable"


class PresentationResumeDecisionKind(StrEnum):
    REUSE = "reuse"
    RENDER = "render"


class PresentationResumeReason(StrEnum):
    REUSE_VERIFIED = "reuse_verified"
    SCIENTIFIC_STAGE_RAN = "scientific_stage_ran"
    NOT_RECORDED = "not_recorded"
    NOT_PRODUCED = "not_produced"
    RECEIPT_UNAVAILABLE = "receipt_unavailable"
    SOURCE_CHANGED = "source_changed"
    OUTPUT_UNAVAILABLE = "output_unavailable"


class PresentationResumeDecision(BaseModel):
    """Independent redraw decision; it has no authority over scientific stage reuse."""

    model_config = ConfigDict(extra="forbid")

    decision: PresentationResumeDecisionKind
    reason: PresentationResumeReason
    verified_output_paths: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def reason_matches_decision(self) -> PresentationResumeDecision:
        is_reuse = self.reason == PresentationResumeReason.REUSE_VERIFIED
        if (self.decision == PresentationResumeDecisionKind.REUSE) != is_reuse:
            raise ValueError("presentation REUSE requires reuse_verified and vice versa")
        return self


class StageRunReason(StrEnum):
    """Why a stage is REUSED or must RUN. Exactly one reason is a reuse reason (``REUSE_VERIFIED``)."""

    REUSE_VERIFIED = "reuse_verified"
    FRESH_RUN = "fresh_run"
    MISSING_RECEIPT = "missing_receipt"
    RECEIPT_NOT_COMPLETE = "receipt_not_complete"
    INPUT_DIGEST_CHANGED = "input_digest_changed"
    CONFIG_OR_MODEL_CHANGED = "config_or_model_changed"
    UPSTREAM_RAN = "upstream_ran"
    UPSTREAM_SCIENTIFIC_TERMINAL = "upstream_scientific_terminal"
    # back_half only: the stage receipt verified but one or more families are incomplete on disk —
    # the stage re-runs with the completed families fed to ``completed_records`` (family-level skip).
    INCOMPLETE_FAMILIES = "incomplete_families"


class StageResumeDecision(BaseModel):
    """One stage's REUSE/RUN decision + the digest evidence it was made from. ``extra='forbid'``."""

    model_config = ConfigDict(extra="forbid")

    stage_name: str
    decision: StageResumeDecisionKind
    reason: StageRunReason
    # The prior receipt's status value, or "missing" when no receipt was found.
    receipt_status: str = "missing"
    changed_input_keys: list[str] = Field(default_factory=list)
    recorded_input_digests: dict[str, str] = Field(default_factory=dict)
    current_input_digests: dict[str, str] = Field(default_factory=dict)
    # Output paths (run-root-relative) whose digests were verified for a REUSE decision.
    verified_output_paths: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _reason_matches_decision(self) -> StageResumeDecision:
        expected_reason = {
            StageResumeDecisionKind.REUSE: StageRunReason.REUSE_VERIFIED,
            StageResumeDecisionKind.TERMINAL_NOT_APPLICABLE: (
                StageRunReason.UPSTREAM_SCIENTIFIC_TERMINAL
            ),
        }.get(self.decision)
        if expected_reason is not None and self.reason != expected_reason:
            raise ValueError(
                f"stage decision {self.decision.value!r} is inconsistent with reason "
                f"{self.reason.value!r}"
            )
        if expected_reason is None and self.reason in {
            StageRunReason.REUSE_VERIFIED,
            StageRunReason.UPSTREAM_SCIENTIFIC_TERMINAL,
        }:
            raise ValueError(
                "stage decision is inconsistent: RUN stage cannot carry a reuse or "
                "terminal-barrier reason"
            )
        return self


class FamilyResumeReason(StrEnum):
    TERMINAL_COMPLETE = "terminal_complete"
    RECORD_MISSING = "record_missing"
    NON_TERMINAL_STATUS = "non_terminal_status"
    SHORTLIST_CHANGED = "shortlist_changed"
    BACK_HALF_CHANGED = "back_half_changed"
    UPSTREAM_RAN = "upstream_ran"


class FamilyResumeDecision(BaseModel):
    """One shortlisted family's REUSE/RUN decision for back-half re-entry. ``extra='forbid'``."""

    model_config = ConfigDict(extra="forbid")

    question_family_id: str
    slug: str
    decision: StageResumeDecisionKind
    reason: FamilyResumeReason
    # The persisted FamilyDossierOutputRecord status found on disk, or "" when no record exists.
    status_on_disk: str = ""

    @model_validator(mode="after")
    def _reason_matches_decision(self) -> FamilyResumeDecision:
        if self.decision == StageResumeDecisionKind.TERMINAL_NOT_APPLICABLE:
            raise ValueError("terminal_not_applicable is a shared-stage decision, not a family one")
        is_reuse_reason = self.reason == FamilyResumeReason.TERMINAL_COMPLETE
        if (self.decision == StageResumeDecisionKind.REUSE) != is_reuse_reason:
            raise ValueError(
                f"family decision {self.decision.value!r} is inconsistent with reason "
                f"{self.reason.value!r} (REUSE ⟺ terminal_complete)"
            )
        return self


class ResumeReceipt(BaseModel):
    """The persisted decision set of one resume attempt (written BEFORE any execution)."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    resume_index: int = Field(ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # Informational whole-config digest (per-stage drift is decided by the per-stage slices).
    config_digest: str = ""
    stage_decisions: list[StageResumeDecision] = Field(default_factory=list)
    family_decisions: list[FamilyResumeDecision] = Field(default_factory=list)
    presentation_decision: PresentationResumeDecision | None = None


class FamilyCompletionRecord(BaseModel):
    """One family's durable completion record (``families/<slug>/family_completion.yaml``).

    Written by the DRIVER at back-half layout time (the orchestrator is untouched). A later resume
    treats the family as complete only when the record parses, its ``dossier_record.status`` is a
    scientific terminal, the record binds to the CURRENT shortlist manifest digest, and every artifact
    listed in ``artifact_digests`` still exists with a matching digest. An unmapped/unknown status
    fails toward re-run, never toward reuse.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    question_family_id: str
    slug: str
    #: The shortlist's SHARED proposal context — pack, context id and digest, authority ceiling.
    #: What every family in a batch is planned against, and what genuinely invalidates all of them.
    shortlist_context_digest: str
    #: A digest over THIS family's own shortlist entry. Together with the shared digest above, this
    #: replaces a single `stable_hash` of the whole manifest.
    #:
    #: The whole-manifest binding was measured wrong on 2026-08-14: a transient connection drop put
    #: one qualification family in `run_incomplete_family_ids`, and moving it back into `shortlisted`
    #: have changed the manifest hash and therefore invalidated four accepted plans and a reject that
    #: were already earned and paid for. So the only lawful rescue cost more than the fault. A
    #: family's terminal depends on the shared context and on its own entry; a sibling being
    #: re-reviewed beside it changes neither.
    shortlist_entry_digest: str
    dossier_record: FamilyDossierOutputRecord
    family_run_outcome: FamilyRunOutcome
    # run-root-relative POSIX path → sha256 of every artifact this completion claims.
    artifact_digests: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _identity_is_consistent(self) -> FamilyCompletionRecord:
        if self.dossier_record.question_family_id != self.question_family_id:
            raise ValueError("FamilyCompletionRecord dossier_record is for a different family")
        if self.family_run_outcome.question_family_id != self.question_family_id:
            raise ValueError("FamilyCompletionRecord family_run_outcome is for a different family")
        return self
