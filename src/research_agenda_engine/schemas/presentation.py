"""Presentation-only add-on records for detailed human-readable run views.

These records deliberately sit outside the six scientific stage receipts and the indexed scientific
artifact inventory. A missing or damaged presentation file is therefore redrawable; it can never
change scientific processing state or authority.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PresentationAddonState(StrEnum):
    NOT_REACHED = "not_reached"
    PRODUCED = "produced"
    WARNING = "warning"


class PresentationArtifactKind(StrEnum):
    QUESTION_PATTERNS_DETAILED = "question_patterns_detailed"
    QUESTION_FAMILIES_DETAILED = "question_families_detailed"
    FAMILY_DOSSIER_DETAILED = "family_dossier_detailed"


class PresentationWarningCode(StrEnum):
    """The closed taxonomy of reasons a detailed page is incomplete.

    Deliberately constrained at source, unlike the wording heuristics elsewhere in this codebase:
    these values are emitted by the project's own deterministic renderers, never by a model, so a
    closed set is the right shape (AGENTS.md rule 11 — taxonomies hard, phrasing soft). Emitting
    members rather than bare strings is what keeps the enum and the renderers from drifting; a
    string mapped at the persistence boundary could fail on the project's own vocabulary and lose
    the whole add-on.

    Every renderer code below is identifier-free by construction, which is what makes it safe to
    persist and show. The last two are raised by the materializer itself, not a renderer.
    """

    CONFLICTING_PATTERN_SOURCE_LINK = "conflicting_pattern_source_link"
    INCOMPLETE_PATTERN_SOURCE_LINEAGE = "incomplete_pattern_source_lineage"
    LITERATURE_CONTEXT_UNAVAILABLE = "literature_context_unavailable"
    MISSING_PATTERN_SOURCE_LINK = "missing_pattern_source_link"
    MISSING_SHORTLIST_DISPOSITION = "missing_shortlist_disposition"
    MISSING_VARIANT_SHORTLIST_DISPOSITION = "missing_variant_shortlist_disposition"
    NO_PATTERNS_AVAILABLE = "no_patterns_available"
    SHORTLIST_UNAVAILABLE = "shortlist_unavailable"
    UNRESOLVED_LITERATURE_REFERENCE = "unresolved_literature_reference"
    UNRESOLVED_LITERATURE_SOURCE = "unresolved_literature_source"
    UNSAFE_PUBLIC_CONTENT_OMITTED = "unsafe_public_content_omitted"
    UNSAFE_TYPED_SOURCE_URL_OMITTED = "unsafe_typed_source_url_omitted"
    PAGE_RENDER_FAILED = "page_render_failed"
    EXPECTED_PAGE_MISSING = "expected_page_missing"
    UNCLASSIFIED_PAGE_WARNING = "unclassified_page_warning"


def classify_presentation_warning(value: str) -> PresentationWarningCode:
    """Map a rendered page's warning onto the taxonomy, degrading instead of discarding.

    The renderers emit enum members, so the enum cannot drift from them. But
    ``RenderedPresentationPage`` is an unvalidated dataclass, so an unrecognized value can still
    reach here -- and refusing it would fail strict receipt construction, which the caller swallows,
    which loses every detailed page in the run over the project's own vocabulary. That is the exact
    fail-closed mistake this programme exists to remove, so an unknown value is recorded as
    unclassified and the honest fact that a page was incomplete survives.
    """
    try:
        return PresentationWarningCode(value)
    except ValueError:
        return PresentationWarningCode.UNCLASSIFIED_PAGE_WARNING


# Codes for which another attempt is worth making: the page is ABSENT, or a whole input artifact
# was unavailable when the add-on ran, so a resume that re-runs the owning stage can change the
# outcome. Everything else is content-level — the page WAS drawn and an entry could not be resolved
# from what this run actually holds, so a fresh attempt reproduces it byte for byte.
#
# This split exists because the old receipt told every reader to run `maieusis resume`, which for a
# content-level warning is advice that cannot work. Fourteen of sixteen live runs carried a
# byte-identical warning sentence, so the receipt named neither the page nor the cause.
# ``UNCLASSIFIED_PAGE_WARNING`` is deliberately absent: an unknown value can only arrive from a page
# that DID render (the render-failure path appends its own code), so treating it as content-level is
# a deduction, not a guess.
RETRY_WORTHY_PRESENTATION_WARNING_CODES = frozenset(
    {
        PresentationWarningCode.PAGE_RENDER_FAILED,
        PresentationWarningCode.EXPECTED_PAGE_MISSING,
        PresentationWarningCode.LITERATURE_CONTEXT_UNAVAILABLE,
        PresentationWarningCode.SHORTLIST_UNAVAILABLE,
    }
)

_PRESENTATION_STATE_UNCHANGED = " Scientific run state and compact products are unchanged."


def presentation_warning_sentence(codes: Sequence[PresentationWarningCode]) -> str:
    """The reader-facing sentence, DERIVED from the codes so it can never contradict them.

    Deriving rather than hardcoding is the whole fix: a constant sentence cannot distinguish a page
    that does not exist from a page that exists with one unresolved entry, and those two need
    opposite advice.
    """
    if not codes:
        return ""
    retry_worthy = [code for code in codes if code in RETRY_WORTHY_PRESENTATION_WARNING_CODES]
    content_level = [code for code in codes if code not in RETRY_WORTHY_PRESENTATION_WARNING_CODES]
    if retry_worthy and content_level:
        body = (
            "Detailed presentation is incomplete: one or more applicable pages could not be drawn, "
            "and at least one page that was drawn has an entry that could not be resolved from this "
            "run's own reviewed records. Retrying the add-on may complete the missing pages; it "
            "will not change the unresolved entries."
        )
    elif retry_worthy:
        body = (
            "Detailed presentation is incomplete: one or more applicable pages could not be drawn. "
            "Retrying the add-on may complete them."
        )
    else:
        body = (
            "Every applicable detailed page was drawn, but at least one entry could not be resolved "
            "from this run's own reviewed records. Retrying the add-on will reproduce the same "
            "pages; the compact products carry the same science."
        )
    return body + _PRESENTATION_STATE_UNCHANGED


class PresentationArtifactRecord(BaseModel):
    """One current detailed projection; never part of scientific artifact integrity."""

    model_config = ConfigDict(extra="forbid")

    kind: PresentationArtifactKind
    path: str
    sha256: str
    family_id: str = ""

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        value = value.strip().replace("\\", "/")
        path = PurePosixPath(value)
        if not value or path.is_absolute() or ".." in path.parts or value.startswith("./"):
            raise ValueError("presentation paths must be normalized run-relative POSIX paths")
        if path.as_posix() != value:
            raise ValueError("presentation paths must be normalized run-relative POSIX paths")
        return value

    @field_validator("sha256")
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        value = value.strip().lower()
        if not _SHA256_RE.fullmatch(value):
            raise ValueError("presentation sha256 must be lowercase hexadecimal")
        return value

    @model_validator(mode="after")
    def family_identity_matches_kind(self) -> PresentationArtifactRecord:
        is_family = self.kind == PresentationArtifactKind.FAMILY_DOSSIER_DETAILED
        if is_family != bool(self.family_id.strip()):
            raise ValueError("only family dossier presentation records carry family_id")
        return self


class PresentationAddonReceipt(BaseModel):
    """Current deterministic add-on attempt, bound only to persisted typed source bytes."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["presentation_addon_receipt/v1"] = "presentation_addon_receipt/v1"
    run_id: str
    status: PresentationAddonState
    input_digests: dict[str, str] = Field(default_factory=dict)
    config_version: Literal["presentation_addon/v1"] = "presentation_addon/v1"
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    model_versions: dict[str, str] = Field(default_factory=dict)
    output_paths: list[str] = Field(default_factory=list)
    expected_output_paths: list[str] = Field(default_factory=list)
    output_digests: dict[str, str] = Field(default_factory=dict)
    external_call_ids: list[str] = Field(default_factory=list)
    warning: str = ""
    # The typed reasons behind ``warning``. Deliberately NOT required for a WARNING status: the
    # sixteen receipts already on disk predate this field, and making them unloadable to enforce a
    # new invariant would trade a real artifact for a rule. The materializer guarantees the codes at
    # the construction site instead, and derives ``warning`` from them so the two cannot disagree.
    warning_codes: list[PresentationWarningCode] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("input_digests", "output_digests")
    @classmethod
    def validate_digest_maps(cls, value: dict[str, str]) -> dict[str, str]:
        for key, digest in value.items():
            path = PurePosixPath(key)
            if (
                not key.strip()
                or path.is_absolute()
                or ".." in path.parts
                or key.startswith("./")
                or path.as_posix() != key
                or not _SHA256_RE.fullmatch(digest)
            ):
                raise ValueError("presentation receipt digest maps require named sha256 values")
        return value

    @field_validator("output_paths", "expected_output_paths")
    @classmethod
    def validate_output_paths(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            path = PurePosixPath(value)
            if (
                not value
                or path.is_absolute()
                or ".." in path.parts
                or value.startswith("./")
                or path.as_posix() != value
            ):
                raise ValueError("presentation receipt paths must be normalized run-relative paths")
            normalized.append(value)
        if len(normalized) != len(set(normalized)):
            raise ValueError("presentation receipt output paths must be unique")
        return normalized

    @model_validator(mode="after")
    def enforce_zero_call_addon(self) -> PresentationAddonReceipt:
        if not self.run_id.strip():
            raise ValueError("presentation receipt requires run_id")
        if self.prompt_versions or self.model_versions or self.external_call_ids:
            raise ValueError("presentation add-on receipts cannot record prompts, models, or calls")
        if self.ended_at < self.started_at:
            raise ValueError("presentation receipt ended_at cannot precede started_at")
        if set(self.output_paths) != set(self.output_digests):
            raise ValueError("presentation receipt output paths and digests must match")
        if len(self.warning_codes) != len(set(self.warning_codes)):
            raise ValueError("presentation receipt warning codes must be unique")
        if self.status == PresentationAddonState.PRODUCED:
            if self.warning.strip() or self.warning_codes:
                raise ValueError("a produced presentation receipt cannot carry a warning")
            if set(self.output_paths) != set(self.expected_output_paths):
                raise ValueError("a produced presentation receipt requires every expected output")
        elif self.status == PresentationAddonState.WARNING:
            if not self.warning.strip():
                raise ValueError("a warning presentation receipt requires a public warning")
        else:
            raise ValueError("an attempt receipt must be produced or warning, never not_reached")
        return self


class PresentationAddonRecord(BaseModel):
    """Soft current pointer stored in ``RunManifest`` without altering scientific state."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["presentation_addon/v1"] = "presentation_addon/v1"
    state: PresentationAddonState = PresentationAddonState.NOT_REACHED
    receipt_path: str = ""
    outputs: list[PresentationArtifactRecord] = Field(default_factory=list)
    warning: str = ""
    # Mirrored from the receipt so the README and the CLI can give cause-specific advice without
    # opening a second file. Same backward-compatibility reasoning as the receipt's copy.
    warning_codes: list[PresentationWarningCode] = Field(default_factory=list)

    @field_validator("receipt_path")
    @classmethod
    def validate_optional_receipt_path(cls, value: str) -> str:
        if not value:
            return value
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or ".." in path.parts
            or value.startswith("./")
            or path.as_posix() != value
        ):
            raise ValueError("presentation receipt path must be normalized and run-relative")
        return value

    @model_validator(mode="after")
    def state_matches_current_attempt(self) -> PresentationAddonRecord:
        paths = [item.path for item in self.outputs]
        if len(paths) != len(set(paths)):
            raise ValueError("presentation output paths must be unique")
        family_ids = [
            item.family_id
            for item in self.outputs
            if item.kind == PresentationArtifactKind.FAMILY_DOSSIER_DETAILED
        ]
        if len(family_ids) != len(set(family_ids)):
            raise ValueError("presentation family dossier records must have unique family IDs")
        if len(self.warning_codes) != len(set(self.warning_codes)):
            raise ValueError("presentation record warning codes must be unique")
        if self.state == PresentationAddonState.NOT_REACHED:
            if self.receipt_path or self.outputs or self.warning or self.warning_codes:
                raise ValueError("not_reached presentation record cannot carry attempt data")
        elif self.state == PresentationAddonState.PRODUCED:
            if not self.receipt_path or self.warning or self.warning_codes:
                raise ValueError("produced presentation record requires a receipt and no warning")
        elif not self.receipt_path or not self.warning.strip():
            raise ValueError("warning presentation record requires receipt and public warning")
        return self
