"""Deterministic, presentation-only reading guide for one family dossier.

The renderer consumes already-validated typed artifacts.  It does not discover files, call a
provider, change scientific state, or decide whether a plan was accepted.  Family-level authority
comes only from ``FamilyCompletionRecord.family_run_outcome``; variant-level accepted-plan wording
additionally requires agreement across the receipt-bound plan, Question Owner review, and independent
review.  A planner-authored plan can therefore remain visible as planning context for a terminal, but
it can never promote itself to accepted authority.

This module deliberately renders none of the identities that bind those artifacts.  The final
validator permits only the sibling ``dossier.md`` link and rejects paths, digests, internal IDs,
raw-payload vocabulary, PDF links, and audit-sidecar links.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from enum import StrEnum
from pathlib import PurePosixPath

from pydantic import BaseModel

from ...schemas.analysis_plan import AnalysisPlan
from ...schemas.front_half_authority import FrontHalfAuthorityCeiling
from ...schemas.multi_family_dossier import (
    AutomatedReviewKind,
    FamilyDossierStatus,
    ReviewAuthority,
    classify_automated_review,
)
from ...schemas.planning_dialogue import (
    BranchDecisionKind,
    FamilyVariantPlanningEntry,
    IndependentPlanReviewMessage,
    PlanDraftMessage,
    PlanReviewDecisionValue,
    QuestionOwnerPlanReviewMessage,
)
from ...schemas.question_family import QuestionFamily
from ...schemas.question_family_branch import QuestionFamilyInspectionEvidence
from ...schemas.resume import FamilyCompletionRecord
from ...schemas.run_outcome import (
    DossierAxis,
    FamilyWarningClass,
    PlanningAxis,
    ReviewAxis,
    ShortlistAxis,
)
from .privacy import is_identifier_shaped


class FamilyDetailedPageError(ValueError):
    """The typed presentation inputs cannot produce a safe, faithful page."""


class FamilyDetailedPagePrivacyError(FamilyDetailedPageError):
    """Rendered presentation text crosses a public-output privacy boundary."""


class FamilyDetailedDisposition(StrEnum):
    ACCEPTED = "accepted"
    MIXED = "mixed"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    MATERIAL_DEFERRED = "material_deferred"
    BUDGET_EXHAUSTED = "budget_exhausted"
    REVIEW_TERMINAL = "review_terminal"
    PUBLIC_DOSSIER_REVISION = "public_dossier_revision"
    VALIDATION_WARNING = "validation_warning"
    PROVIDER_WARNING = "provider_warning"
    INTEGRITY_TERMINAL = "integrity_terminal"
    NOT_REACHED = "not_reached"


_ABSOLUTE_POSIX_PATH = re.compile(
    r"(?<![A-Za-z0-9:])/(?:Users|Volumes|private|tmp|var|home|root|opt|etc|mnt|workspace|"
    r"data|srv)(?:/[^\s)>\]]+)+"
)
_ABSOLUTE_WINDOWS_PATH = re.compile(r"\b[A-Za-z]:[\\/][^\s)>\]]+")
_SHA256 = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
_INTERNAL_FIELD = re.compile(
    r"\b(?:provider|model|session|request|thread|branch|event|evidence|claim|context|payload)"
    r"_(?:id|digest)\b",
    re.IGNORECASE,
)
_INTERNAL_VALUE = re.compile(
    r"\b(?:qfamily-branch-[a-z0-9-]+|owner-session-[a-z0-9-]+|"
    r"qsc-v\d+-context-[a-z0-9-]+|event-[a-f0-9]{8,}[a-z0-9-]*|"
    r"request-[a-f0-9]{6,}[a-z0-9-]*|thread-[a-f0-9]{6,}[a-z0-9-]*)\b",
    re.IGNORECASE,
)
_FORBIDDEN_PUBLIC_FRAGMENT = re.compile(
    r"(?:https?://|file://|raw payload|audit sidecar|hidden sidecar|\.pdf\b)",
    re.IGNORECASE,
)
_MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


_STATUS_LABELS = {
    FamilyDetailedDisposition.ACCEPTED: "Accepted planning dossier",
    FamilyDetailedDisposition.MIXED: "Mixed family: accepted and non-accepted sibling variants",
    FamilyDetailedDisposition.REJECTED: "Scientific rejection terminal",
    FamilyDetailedDisposition.ESCALATED: "Optional-review escalation terminal",
    FamilyDetailedDisposition.MATERIAL_DEFERRED: "Material revision deferred",
    FamilyDetailedDisposition.BUDGET_EXHAUSTED: "Bounded revision budget exhausted",
    FamilyDetailedDisposition.REVIEW_TERMINAL: "Review terminal without accepted-plan authority",
    FamilyDetailedDisposition.PUBLIC_DOSSIER_REVISION: "Public dossier revision required",
    FamilyDetailedDisposition.VALIDATION_WARNING: "Validation warning",
    FamilyDetailedDisposition.PROVIDER_WARNING: "Service warning",
    FamilyDetailedDisposition.INTEGRITY_TERMINAL: "Integrity terminal",
    FamilyDetailedDisposition.NOT_REACHED: "Planning not reached",
}


def variant_ids_are_ordered_subset(
    original_variant_ids: Sequence[str], current_variant_ids: Sequence[str]
) -> bool:
    """True when novelty retained known variants without changing their relative order."""
    current = list(current_variant_ids)
    if not current or len(current) != len(set(current)):
        return False
    current_set = set(current)
    return current == [
        variant_id for variant_id in original_variant_ids if variant_id in current_set
    ]


def render_family_detailed_page(
    *,
    completion: FamilyCompletionRecord,
    family: QuestionFamily,
    original_family: QuestionFamily | None = None,
    plan_draft: PlanDraftMessage | None = None,
    owner_review: QuestionOwnerPlanReviewMessage | None = None,
    independent_review: IndependentPlanReviewMessage | None = None,
    inspection_evidence: Sequence[QuestionFamilyInspectionEvidence] = (),
    dossier_href: str = "dossier.md",
    extra_private_tokens: Sequence[str] = (),
) -> str:
    """Render one light scientific reading guide from persisted typed artifacts.

    ``dossier_href`` is intentionally constrained to a sibling relative Markdown file.  The
    materializer remains responsible for checking that the target exists inside the run root.
    """

    _validate_dossier_href(dossier_href)
    original_family = original_family or family
    _validate_source_bindings(
        completion=completion,
        family=family,
        original_family=original_family,
        plan_draft=plan_draft,
        owner_review=owner_review,
        independent_review=independent_review,
        inspection_evidence=inspection_evidence,
    )
    disposition = _family_disposition(completion, plan_draft=plan_draft)
    accepted_family = disposition in {
        FamilyDetailedDisposition.ACCEPTED,
        FamilyDetailedDisposition.MIXED,
    }
    if accepted_family:
        _require_reviewed_plan_sources(
            family=family,
            plan_draft=plan_draft,
            owner_review=owner_review,
            independent_review=independent_review,
        )

    record = completion.dossier_record
    lines = [
        f"# {_public_text(record.family_title, field='family title')} — scientific reading guide",
        "",
        (
            "> **Planning-only boundary:** This page explains a question-development outcome. "
            "It reports no scientific result, authorizes no execution, and does not open the "
            "downstream bridge."
        ),
        "",
        "## Status and authority",
        "",
        f"- Family status: **{_STATUS_LABELS[disposition]}**",
        f"- Authority: **{_authority_label(completion, family=family, disposition=disposition)}**",
        _accepted_plan_authority_line(
            completion,
            family=family,
            disposition=disposition,
        ),
        "- Scientific results: **None; the analysis has not been executed.**",
        "",
        "## Why this question matters",
        "",
        _public_text(family.summary, field="family summary"),
        "",
        "The scientific tension is:",
        "",
        _public_text(family.shared_scientific_tension, field="scientific tension"),
        "",
    ]
    _append_terminal_explanation(lines, completion=completion, disposition=disposition)

    outcome_by_variant = (
        {entry.variant_id: entry for entry in plan_draft.variant_outcomes}
        if plan_draft is not None
        else {}
    )
    plan_by_variant = _plan_entries_by_variant(
        disposition=disposition,
        plan_draft=plan_draft,
    )
    reviewed_decisions = _reviewed_variant_decisions(
        disposition=disposition,
        family=family,
        plan_draft=plan_draft,
        owner_review=owner_review,
        independent_review=independent_review,
    )
    original_by_variant = {variant.variant_id: variant for variant in original_family.variants}

    for index, variant in enumerate(family.variants, start=1):
        original_variant = original_by_variant[variant.variant_id]
        role = _public_text(variant.variant_role, field=f"variant {index} role")
        lines.extend(
            [
                f"## Variant {index}: {role}",
                "",
                "### Why it matters",
                "",
                _public_text(
                    variant.seed.why_scientifically_important,
                    field=f"variant {index} scientific importance",
                ),
                "",
                "### Original and refined question",
                "",
                "**Original Question Scientist proposal**",
                "",
                _public_text(
                    original_variant.seed.question,
                    field=f"variant {index} original question",
                ),
                "",
            ]
        )
        if variant.seed.question != original_variant.seed.question:
            lines.extend(
                [
                    "**Post-novelty revised proposal**",
                    "",
                    _public_text(
                        variant.seed.question,
                        field=f"variant {index} post-novelty question",
                    ),
                    "",
                ]
            )
        plan = plan_by_variant.get(variant.variant_id)
        final_decision = reviewed_decisions.get(variant.variant_id)
        if accepted_family and final_decision is not None and final_decision.is_accepted:
            if plan is None:
                raise FamilyDetailedPageError(
                    "an accepted variant is missing its validated detailed analysis plan"
                )
            lines.extend(
                [
                    "**Reviewed refined question**",
                    "",
                    _public_text(
                        plan.refined_question,
                        field=f"variant {index} refined question",
                    ),
                    "",
                    "**Reviewed planning disposition**",
                    "",
                    _variant_decision_text(final_decision),
                    "",
                ]
            )
        elif accepted_family and final_decision is not None:
            outcome_entry = outcome_by_variant.get(variant.variant_id)
            summary = (
                _public_text(outcome_entry.summary, field=f"variant {index} disposition summary")
                if outcome_entry is not None
                else "No validated summary was available."
            )
            lines.extend(
                [
                    "**Refined-question status**",
                    "",
                    "No refined question earned accepted-plan authority for this sibling.",
                    "",
                    "**Reviewed planning disposition**",
                    "",
                    f"{_variant_decision_text(final_decision)} {summary}",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "**Refined-question status**",
                    "",
                    (
                        "A refined question did not earn accepted-plan authority in this family "
                        "terminal. Any retained planner wording remains planning context only."
                    ),
                    "",
                ]
            )

        lines.extend(
            [
                "### Proposal hypothesis versus inspected evidence",
                "",
                "**Proposal-stage dataset-leverage hypothesis**",
                "",
                _public_text(
                    variant.seed.dataset_leverage_hypothesis,
                    field=f"variant {index} dataset-leverage hypothesis",
                ),
                "",
                (
                    "This was a proposal-stage hypothesis, not a feasibility certification or "
                    "scientific finding."
                ),
                "",
                "**What the planner actually inspected**",
                "",
            ]
        )
        evidence = _evidence_for_variant(
            variant_id=variant.variant_id,
            inspection_evidence=inspection_evidence,
            accepted_outcome=outcome_by_variant.get(variant.variant_id)
            if accepted_family
            else None,
        )
        if evidence:
            for item in evidence[:3]:
                finding = _public_text(item.finding, field=f"variant {index} evidence finding")
                claim_status = item.dataset_claim_status.value.replace("_", " ")
                lines.append(f"- **{claim_status.capitalize()} planning evidence:** {finding}")
                for limitation in item.limitations:
                    lines.append(
                        "  - Limitation: "
                        + _public_text(
                            limitation,
                            field=f"variant {index} evidence limitation",
                        )
                    )
            if len(evidence) > 3:
                lines.append(
                    f"- {len(evidence) - 3} additional typed inspection statement(s) remain in "
                    "the complete planning record."
                )
        elif inspection_evidence:
            # A page may not assert an absence it did not verify. "None was available" conflated two
            # different facts -- this family retained none, versus none of what it retained is in
            # scope for this variant -- and for nine families it was simply false, because the
            # loader discovered evidence by filename substring and matched none of their files.
            # Now the loader accounts for the whole import manifest, so this branch can say which
            # of the two states actually holds, and both statements are counts.
            lines.append(
                f"- None of the {len(inspection_evidence)} typed inspection statement(s) retained "
                "for this family are in scope for this variant."
            )
        else:
            lines.append("- No typed inspection statement was retained for this family.")
        if not accepted_family:
            lines.append("- These retained inspection notes do not create accepted-plan authority.")
        lines.append("")

        if plan is not None and final_decision is not None and final_decision.is_accepted:
            _append_plan_at_a_glance(lines, plan=plan, variant_index=index, accepted=True)
        elif plan is not None and disposition not in {
            FamilyDetailedDisposition.VALIDATION_WARNING,
            FamilyDetailedDisposition.INTEGRITY_TERMINAL,
        }:
            _append_plan_at_a_glance(lines, plan=plan, variant_index=index, accepted=False)

        lines.extend(
            [
                "### Scientific stakes",
                "",
                "**Discriminating observation**",
                "",
                _public_text(
                    variant.seed.discriminating_observation,
                    field=f"variant {index} discriminating observation",
                ),
                "",
                "**What possible outcomes would mean**",
                "",
                "- Positive pattern: "
                + _public_text(
                    variant.seed.positive_result_consequence,
                    field=f"variant {index} positive consequence",
                ),
                "- Negative pattern: "
                + _public_text(
                    variant.seed.negative_result_consequence,
                    field=f"variant {index} negative consequence",
                ),
                "- Null or ambiguous pattern: "
                + _public_text(
                    variant.seed.null_result_consequence,
                    field=f"variant {index} null consequence",
                ),
                "",
            ]
        )

    _append_review_dispositions(
        lines,
        completion=completion,
        disposition=disposition,
        owner_review=owner_review,
        independent_review=independent_review,
    )
    lines.extend(
        [
            "## Continue to the complete dossier",
            "",
            (
                "This guide is an orientation layer. The existing dossier remains the complete "
                "human-readable planning record."
            ),
            "",
            f"[Read the complete scientific dossier]({dossier_href})",
            "",
        ]
    )
    markdown = "\n".join(lines)
    # The caller's run-wide set is unioned in, because the promotion step validates against it:
    # a token only IT knows about would otherwise survive redaction, fail validation, and be
    # swallowed by the page-isolation handler -- costing the family its whole reading guide. Found
    # 2026-07-28 by the fault-injection harness; the residue PR #109 did not close.
    forbidden = _internal_tokens(
        completion,
        family,
        plan_draft,
        owner_review,
        independent_review,
        *inspection_evidence,
    ) | {token for token in extra_private_tokens if token}
    # Redact, then validate. The boundary is unchanged -- the identifier still never reaches the
    # page -- but it is now enforced by removing the token rather than by destroying the page
    # around it. Live-found 2026-07-28: two families with accepted plans lost their entire reading
    # guide (12,915 and 18,180 characters) to exactly one internal id each, quoted inside the
    # agents' own scientific prose where it was doing useful work -- "exactly as ratified by the
    # Question Owner in <operationalization id>" and "(9 signed-contrast levels x 3 prior blocks;
    # <evidence id>)". Citing your own evidence id is the traceability this project asks for; it
    # should not cost the reader the page. The sibling context-page renderer already redacts.
    markdown = _redact_internal_tokens(markdown, forbidden)
    validate_family_detailed_page(
        markdown,
        dossier_href=dossier_href,
        forbidden_tokens=forbidden,
    )
    return markdown


def validate_family_detailed_page(
    markdown: str,
    *,
    dossier_href: str = "dossier.md",
    forbidden_tokens: Iterable[str] = (),
) -> None:
    """Fail closed when a detailed family page contains private/audit-only material."""

    if not markdown.strip():
        raise FamilyDetailedPagePrivacyError("family detailed page is empty")
    _validate_dossier_href(dossier_href)
    checks = (
        (_ABSOLUTE_POSIX_PATH, "local absolute path"),
        (_ABSOLUTE_WINDOWS_PATH, "local absolute path"),
        (_SHA256, "digest"),
        (_INTERNAL_FIELD, "internal identity field"),
        (_INTERNAL_VALUE, "internal identity value"),
        (_FORBIDDEN_PUBLIC_FRAGMENT, "private source or sidecar reference"),
    )
    for pattern, label in checks:
        if pattern.search(markdown):
            raise FamilyDetailedPagePrivacyError(f"family detailed page contains forbidden {label}")
    # The SAME shape test the redactor uses, and it has to be: they read one token set, so a token
    # the redactor is told to leave alone must not be one this refuses the page over. Splitting them
    # was measured on the 2026-08-14 NLB leg and it is worse than either half alone -- the redactor
    # skipped the ordinary word `subjects`, the validator still found it, and three reading guides
    # were lost entirely instead of merely losing a word.
    leaked = [
        token
        for token in forbidden_tokens
        if token and is_identifier_shaped(token) and token in markdown
    ]
    if leaked:
        raise FamilyDetailedPagePrivacyError(
            "family detailed page contains forbidden internal identity value"
        )
    links = _MARKDOWN_LINK.findall(markdown)
    if links != [dossier_href]:
        raise FamilyDetailedPagePrivacyError(
            "family detailed page may link only once to its sibling dossier.md"
        )


def _validate_dossier_href(dossier_href: str) -> None:
    try:
        candidate = PurePosixPath(dossier_href)
    except (TypeError, ValueError) as exc:
        raise FamilyDetailedPagePrivacyError("invalid dossier link") from exc
    if dossier_href != "dossier.md" or candidate.is_absolute() or ".." in candidate.parts:
        raise FamilyDetailedPagePrivacyError(
            "the detailed page dossier link must be the sibling dossier.md"
        )


def _validate_source_bindings(
    *,
    completion: FamilyCompletionRecord,
    family: QuestionFamily,
    original_family: QuestionFamily,
    plan_draft: PlanDraftMessage | None,
    owner_review: QuestionOwnerPlanReviewMessage | None,
    independent_review: IndependentPlanReviewMessage | None,
    inspection_evidence: Sequence[QuestionFamilyInspectionEvidence],
) -> None:
    record = completion.dossier_record
    outcome = completion.family_run_outcome
    if record.question_family_id != completion.question_family_id:
        raise FamilyDetailedPageError("dossier record family binding mismatch")
    if outcome.question_family_id != completion.question_family_id:
        raise FamilyDetailedPageError("family outcome binding mismatch")
    if family.question_family_id != completion.question_family_id:
        raise FamilyDetailedPageError("shortlisted family identity mismatch")
    if original_family.question_family_id != completion.question_family_id:
        raise FamilyDetailedPageError("original family identity mismatch")
    if family.context_id != record.context_id:
        raise FamilyDetailedPageError("shortlisted family context mismatch")
    if original_family.context_id != family.context_id:
        raise FamilyDetailedPageError("original and shortlisted family context mismatch")
    if family.title != record.family_title:
        raise FamilyDetailedPageError("shortlisted family title mismatch")
    source_variant_ids = [item.variant_id for item in family.variants]
    original_variant_ids = [item.variant_id for item in original_family.variants]
    if not variant_ids_are_ordered_subset(original_variant_ids, source_variant_ids):
        raise FamilyDetailedPageError(
            "shortlisted family variants are not an ordered subset of the original family"
        )
    if source_variant_ids != record.variant_ids:
        raise FamilyDetailedPageError("shortlisted family variant order or coverage mismatch")

    expected_message = {
        "branch_id": record.branch_id,
        "context_id": record.context_id,
        "owner_session_id": record.owner_session_id,
    }
    for label, message in (
        ("plan draft", plan_draft),
        ("Question Owner review", owner_review),
        ("independent review", independent_review),
    ):
        if message is not None and any(
            getattr(message, key) != value for key, value in expected_message.items()
        ):
            raise FamilyDetailedPageError(f"{label} identity mismatch")
        # COVERAGE is the invariant; ORDER is not. A variant's identity is its id, never its
        # position in a list an agent happened to return. Requiring positional equality cost a whole
        # reading guide on the 2026-08-14 NLB leg: the family listed
        # `regional-geometry, regional-dynamics` and the plan draft and both reviews listed the same
        # two the other way round, so the page was discarded over an ordering with no meaning.
        #
        # It also produced the reader-facing defect that made the page wrong even when it rendered:
        # sections keyed off the family order and sections keyed off the draft order both said
        # "Variant 1", meaning different variants, so a reader cross-referencing them concluded the
        # opposite branch had been refused. Rendering below reads outcomes by id, so one order wins.
        if message is not None:
            message_variant_ids = [item.variant_id for item in message.variant_outcomes]
            if sorted(message_variant_ids) != sorted(source_variant_ids):
                raise FamilyDetailedPageError(f"{label} variant coverage mismatch")
            if len(set(message_variant_ids)) != len(message_variant_ids):
                raise FamilyDetailedPageError(f"{label} repeats a variant")

    for evidence in inspection_evidence:
        if (
            evidence.branch_id != record.branch_id
            or evidence.question_family_id != completion.question_family_id
            or (evidence.variant_id and evidence.variant_id not in set(source_variant_ids))
        ):
            raise FamilyDetailedPageError("inspection evidence identity mismatch")


def _require_reviewed_plan_sources(
    *,
    family: QuestionFamily,
    plan_draft: PlanDraftMessage | None,
    owner_review: QuestionOwnerPlanReviewMessage | None,
    independent_review: IndependentPlanReviewMessage | None,
) -> None:
    if plan_draft is None or owner_review is None or independent_review is None:
        raise FamilyDetailedPageError(
            "accepted family presentation requires plan, owner, and independent review sources"
        )
    if not owner_review.review_complete or owner_review.decision != PlanReviewDecisionValue.ACCEPT:
        raise FamilyDetailedPageError("accepted family lacks a complete accepting Owner review")
    if (
        not independent_review.review_complete
        or independent_review.decision != PlanReviewDecisionValue.ACCEPT
    ):
        raise FamilyDetailedPageError(
            "accepted family lacks a complete accepting independent review"
        )
    expected = [item.variant_id for item in family.variants]
    for label, entries in (
        ("plan", plan_draft.variant_outcomes),
        ("Owner", owner_review.variant_outcomes),
        ("independent", independent_review.variant_outcomes),
    ):
        # Coverage, not order — the same rule as the identity check above, and it has to be stated
        # twice because the accepted-family path re-checks what that one already checked. Fixing
        # only the first left this one to discard the same page for the same meaningless reason.
        entry_ids = [item.variant_id for item in entries]
        if sorted(entry_ids) != sorted(expected) or len(set(entry_ids)) != len(entry_ids):
            raise FamilyDetailedPageError(f"accepted family {label} variant coverage mismatch")
    plan_decisions = {item.variant_id: item.decision for item in plan_draft.variant_outcomes}
    for label, entries in (
        ("Owner", owner_review.variant_outcomes),
        ("independent", independent_review.variant_outcomes),
    ):
        decisions = {item.variant_id: item.decision for item in entries}
        if decisions != plan_decisions:
            raise FamilyDetailedPageError(
                f"accepted family {label} variant dispositions disagree with receipt-bound plan"
            )


def _family_disposition(
    completion: FamilyCompletionRecord,
    *,
    plan_draft: PlanDraftMessage | None,
) -> FamilyDetailedDisposition:
    outcome = completion.family_run_outcome
    status = completion.dossier_record.status
    if outcome.warning_class == FamilyWarningClass.VALIDATION or (
        status == FamilyDossierStatus.FAILED_VALIDATION
    ):
        return FamilyDetailedDisposition.VALIDATION_WARNING
    if outcome.warning_class == FamilyWarningClass.PROVIDER or (
        status == FamilyDossierStatus.INFRASTRUCTURE_INCOMPLETE
    ):
        return FamilyDetailedDisposition.PROVIDER_WARNING
    if outcome.failure_class is not None or status in {
        FamilyDossierStatus.PROVENANCE_INTEGRITY_TERMINAL,
        FamilyDossierStatus.HARD_INTEGRITY_TERMINAL,
    }:
        return FamilyDetailedDisposition.INTEGRITY_TERMINAL
    if status == FamilyDossierStatus.PUBLIC_DOSSIER_REVISION_REQUIRED:
        return FamilyDetailedDisposition.PUBLIC_DOSSIER_REVISION
    if outcome.planning_axis == PlanningAxis.BUDGET_EXHAUSTED:
        return FamilyDetailedDisposition.BUDGET_EXHAUSTED
    if (
        outcome.planning_axis == PlanningAxis.MATERIAL_DEFERRED
        or outcome.shortlist_axis == ShortlistAxis.DEFERRED_MATERIAL_REVISION
    ):
        return FamilyDetailedDisposition.MATERIAL_DEFERRED
    if (
        outcome.planning_axis == PlanningAxis.ESCALATION
        or outcome.review_axis == ReviewAxis.HUMAN_ESCALATION
    ):
        return FamilyDetailedDisposition.ESCALATED
    if (
        outcome.planning_axis == PlanningAxis.PLANNER_REJECTION
        or outcome.review_axis == ReviewAxis.REJECT
        or outcome.shortlist_axis == ShortlistAxis.REJECTED_SCIENTIFIC
    ):
        return FamilyDetailedDisposition.REJECTED
    if outcome.review_axis == ReviewAxis.REVISION_TERMINAL:
        return FamilyDetailedDisposition.REVIEW_TERMINAL
    if (
        outcome.planning_axis == PlanningAxis.PLAN
        and outcome.review_axis == ReviewAxis.ACCEPT
        and outcome.dossier_axis == DossierAxis.RENDERED
    ):
        if plan_draft is not None:
            decisions = [entry.decision for entry in plan_draft.variant_outcomes]
            if any(item.is_accepted for item in decisions) and not all(
                item.is_accepted for item in decisions
            ):
                return FamilyDetailedDisposition.MIXED
        return FamilyDetailedDisposition.ACCEPTED
    return FamilyDetailedDisposition.NOT_REACHED


def _authority_label(
    completion: FamilyCompletionRecord,
    *,
    family: QuestionFamily,
    disposition: FamilyDetailedDisposition,
) -> str:
    if disposition in {
        FamilyDetailedDisposition.VALIDATION_WARNING,
        FamilyDetailedDisposition.PROVIDER_WARNING,
    }:
        return "Provisional / degraded"
    if disposition == FamilyDetailedDisposition.INTEGRITY_TERMINAL:
        return "No promoted scientific authority"
    authority = completion.dossier_record.human_review_authority
    # `AUTOMATED` alone does not say a reviewer read this — see `classify_automated_review`. The
    # sibling renderer in `services/dossier/generic_family_dossier.py` was repaired for exactly this
    # and this one was not, so a family could be published twice with two different answers.
    automated = {
        AutomatedReviewKind.INDEPENDENT_MODEL: "Automated independent review, planning only",
        AutomatedReviewKind.HOST_AUTHORIZATION: (
            "Automated host authorization, planning only; no independent review was recorded"
        ),
        AutomatedReviewKind.UNRESOLVED: "Provisional; review authority unresolved",
    }[classify_automated_review(authority, completion.dossier_record.provider_id)]
    label = {
        ReviewAuthority.REAL_HUMAN_EXPERT: "Human reviewed, planning only",
        ReviewAuthority.AUTOMATED: automated,
        ReviewAuthority.DEVELOPMENT_MODEL_SURROGATE: (
            "Development-model surrogate; not serious-use acceptance"
        ),
        ReviewAuthority.FIXTURE: "Fixture only; not scientific authority",
        ReviewAuthority.MISSING: "Provisional; review authority missing",
        ReviewAuthority.UNKNOWN: "Provisional; review authority unresolved",
    }[authority]
    if family.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION:
        return label + "; capped at provisional inspiration"
    return label


def _accepted_plan_authority_line(
    completion: FamilyCompletionRecord,
    *,
    family: QuestionFamily,
    disposition: FamilyDetailedDisposition,
) -> str:
    if not _has_accepted_plan_authority(completion, disposition=disposition):
        return "- Accepted-plan authority: **No**"
    if family.authority_ceiling == FrontHalfAuthorityCeiling.PROVISIONAL_INSPIRATION:
        return "- Accepted-plan authority: **Yes, provisionally and for planning only**"
    return "- Accepted-plan authority: **Yes, for planning only**"


def _has_accepted_plan_authority(
    completion: FamilyCompletionRecord,
    *,
    disposition: FamilyDetailedDisposition,
) -> bool:
    return disposition in {
        FamilyDetailedDisposition.ACCEPTED,
        FamilyDetailedDisposition.MIXED,
    } and completion.dossier_record.human_review_authority in {
        ReviewAuthority.AUTOMATED,
        ReviewAuthority.REAL_HUMAN_EXPERT,
    }


def _append_terminal_explanation(
    lines: list[str],
    *,
    completion: FamilyCompletionRecord,
    disposition: FamilyDetailedDisposition,
) -> None:
    if disposition in {
        FamilyDetailedDisposition.ACCEPTED,
        FamilyDetailedDisposition.MIXED,
    }:
        if disposition == FamilyDetailedDisposition.MIXED:
            lines.extend(
                [
                    "## How to read this mixed family",
                    "",
                    (
                        "Accepted and non-accepted sibling variants coexist here. Authority applies "
                        "only to the variants explicitly marked as reviewed and accepted; it does "
                        "not spill across the family."
                    ),
                    "",
                ]
            )
        return
    explanation = {
        FamilyDetailedDisposition.REJECTED: (
            "The scientific planning/review process closed this family without an accepted plan. "
            "Rejection is a scientific terminal, not evidence that the proposed phenomenon is false."
        ),
        FamilyDetailedDisposition.ESCALATED: (
            "The automated workflow closed with an optional-review escalation. It does not pause "
            "the run and does not create accepted-plan authority."
        ),
        FamilyDetailedDisposition.MATERIAL_DEFERRED: (
            "A material revision would change protected scientific meaning. Renewed literature "
            "review and a novelty recheck are required before a revised plan could be accepted."
        ),
        FamilyDetailedDisposition.BUDGET_EXHAUSTED: (
            "The bounded revise loop ended before all scientific blockers were resolved. The "
            "retained plan is inspectable but not accepted."
        ),
        FamilyDetailedDisposition.REVIEW_TERMINAL: (
            "Review reached an honest terminal without conferring accepted-plan authority."
        ),
        FamilyDetailedDisposition.PUBLIC_DOSSIER_REVISION: (
            "Planning and review accepted the plan, but the normal public dossier needs repair. "
            "This guide does not silently substitute for that missing publication gate."
        ),
        FamilyDetailedDisposition.VALIDATION_WARNING: (
            "Returned planning material did not pass strict typed validation. The family is "
            "complete as a readable soft terminal, but it remains provisional and degraded with "
            "no accepted-plan authority."
        ),
        FamilyDetailedDisposition.PROVIDER_WARNING: (
            "A planning or review service remained unavailable after bounded retries. Safe prior "
            "products remain visible, but this terminal has no accepted-plan authority."
        ),
        FamilyDetailedDisposition.INTEGRITY_TERMINAL: (
            "A hard integrity boundary stopped untrusted promotion. This page preserves only the "
            "safe question surface and grants no scientific authority."
        ),
        FamilyDetailedDisposition.NOT_REACHED: (
            "Planning did not reach an accepted terminal for this family."
        ),
    }[disposition]
    lines.extend(["## How to read this terminal", "", explanation, ""])
    reason = completion.family_run_outcome.reason.strip()
    if reason:
        lines.extend(
            [
                "**Recorded public status note**",
                "",
                _public_text(reason, field="family status note"),
                "",
            ]
        )


def _plan_entries_by_variant(
    *,
    disposition: FamilyDetailedDisposition,
    plan_draft: PlanDraftMessage | None,
) -> dict[str, AnalysisPlan]:
    if disposition in {
        FamilyDetailedDisposition.VALIDATION_WARNING,
        FamilyDetailedDisposition.INTEGRITY_TERMINAL,
    }:
        return {}
    entries = plan_draft.variant_analysis_plans if plan_draft is not None else []
    return {entry.variant_id: entry.analysis_plan for entry in entries}


def _reviewed_variant_decisions(
    *,
    disposition: FamilyDetailedDisposition,
    family: QuestionFamily,
    plan_draft: PlanDraftMessage | None,
    owner_review: QuestionOwnerPlanReviewMessage | None,
    independent_review: IndependentPlanReviewMessage | None,
) -> dict[str, BranchDecisionKind]:
    if disposition not in {
        FamilyDetailedDisposition.ACCEPTED,
        FamilyDetailedDisposition.MIXED,
    }:
        return {}
    _require_reviewed_plan_sources(
        family=family,
        plan_draft=plan_draft,
        owner_review=owner_review,
        independent_review=independent_review,
    )
    assert plan_draft is not None
    return {entry.variant_id: entry.decision for entry in plan_draft.variant_outcomes}


def _evidence_for_variant(
    *,
    variant_id: str,
    inspection_evidence: Sequence[QuestionFamilyInspectionEvidence],
    accepted_outcome: FamilyVariantPlanningEntry | None,
) -> list[QuestionFamilyInspectionEvidence]:
    allowed_ids = set(accepted_outcome.evidence_ids) if accepted_outcome is not None else None
    evidence = [
        item
        for item in inspection_evidence
        if item.can_support_variant(variant_id)
        and (allowed_ids is None or item.evidence_id in allowed_ids)
    ]
    return sorted(
        evidence,
        key=lambda item: (
            item.scope.value,
            item.source_type.value,
            item.dataset_claim_status.value,
            " ".join(item.finding.split()).casefold(),
            tuple(" ".join(value.split()).casefold() for value in item.limitations),
        ),
    )


def _append_plan_at_a_glance(
    lines: list[str],
    *,
    plan: AnalysisPlan,
    variant_index: int,
    accepted: bool,
) -> None:
    title = "Plan at a glance" if accepted else "Retained plan at a glance — not accepted"
    lines.extend(
        [
            f"### {title}",
            "",
            "- Population and scope: "
            + _public_text(plan.population_and_scope, field=f"variant {variant_index} population"),
            "- Unit of observation: "
            + _public_text(
                plan.unit_of_observation,
                field=f"variant {variant_index} observation unit",
            ),
            "- Unit of inference: "
            + _public_text(
                plan.unit_of_inference,
                field=f"variant {variant_index} inference unit",
            ),
            "- Hierarchy and dependence: "
            + _public_text(
                plan.hierarchy_and_dependence,
                field=f"variant {variant_index} hierarchy",
            ),
            "- Validation: "
            + _public_text(
                plan.validation_strategy,
                field=f"variant {variant_index} validation strategy",
            ),
            "- Split strategy: "
            + _public_text(plan.split_strategy, field=f"variant {variant_index} split strategy"),
            "- Claim ceiling: " + plan.claim_ceiling.value.replace("_", " "),
            "",
            "**Analysis strategy**",
            "",
            *_numbered_lines(
                plan.analysis_strategy,
                field=f"variant {variant_index} analysis strategy",
                limit=3,
            ),
            "",
            "**Controls**",
            "",
            "- Negative controls: "
            + _inline_list(
                plan.negative_controls,
                field=f"variant {variant_index} negative control",
                limit=2,
            ),
            "- Positive controls: "
            + _inline_list(
                plan.positive_controls,
                field=f"variant {variant_index} positive control",
                limit=2,
            ),
            "- Alternative explanations: "
            + _inline_list(
                plan.alternative_explanations,
                field=f"variant {variant_index} plan alternative",
                limit=2,
            ),
            "",
            "**Interpretation limits**",
            "",
            *_bullet_lines(
                plan.interpretation_limits,
                field=f"variant {variant_index} interpretation limit",
                empty="No additional source-backed interpretation limit was recorded.",
                limit=3,
            ),
            "",
            "**Why the plan serves the question**",
            "",
            _public_text(
                plan.why_plan_serves_question,
                field=f"variant {variant_index} plan rationale",
            ),
            "",
        ]
    )
    if plan.unresolved_decisions or plan.required_new_skills:
        lines.extend(["**Before any later execution**", ""])
        if plan.unresolved_decisions:
            lines.append(
                "- Unresolved planning decisions: "
                + _inline_list(
                    plan.unresolved_decisions,
                    field=f"variant {variant_index} unresolved decision",
                    limit=2,
                )
            )
        if plan.required_new_skills:
            lines.append(
                "- Required future skills: "
                + _inline_list(
                    plan.required_new_skills,
                    field=f"variant {variant_index} required skill",
                    limit=2,
                )
            )
        lines.append("")


def _append_review_dispositions(
    lines: list[str],
    *,
    completion: FamilyCompletionRecord,
    disposition: FamilyDetailedDisposition,
    owner_review: QuestionOwnerPlanReviewMessage | None,
    independent_review: IndependentPlanReviewMessage | None,
) -> None:
    lines.extend(["## Owner and independent review", ""])
    if disposition in {
        FamilyDetailedDisposition.VALIDATION_WARNING,
        FamilyDetailedDisposition.PROVIDER_WARNING,
        FamilyDetailedDisposition.INTEGRITY_TERMINAL,
    }:
        lines.extend(
            [
                (
                    "Any typed review records below are retained context only. They cannot "
                    "override this system terminal or create accepted-plan authority."
                ),
                "",
            ]
        )
    _append_one_review(lines, label="Question Owner", review=owner_review)
    _append_one_review(lines, label="Independent reviewer", review=independent_review)
    if owner_review is None or independent_review is None:
        lines.extend(
            [
                (
                    "A missing review is shown as unavailable rather than inferred from planner "
                    "prose or the family status."
                ),
                "",
            ]
        )
    if not _has_accepted_plan_authority(completion, disposition=disposition):
        lines.extend(
            [
                "**Authority reminder:** these dispositions do not yield an accepted plan here.",
                "",
            ]
        )


def _append_one_review(
    lines: list[str],
    *,
    label: str,
    review: QuestionOwnerPlanReviewMessage | IndependentPlanReviewMessage | None,
) -> None:
    lines.extend([f"### {label}", ""])
    if review is None:
        lines.extend(
            [
                "No safely resolved typed review statement was available for this view.",
                "",
            ]
        )
        return
    decision = review.decision.value.replace("_", " ").capitalize()
    lines.extend(
        [
            f"- Disposition: **{decision}**",
            "- Review complete: **" + ("Yes" if review.review_complete else "No") + "**",
            "- Scientific-intent/material-revision note: "
            + (
                "A material revision was detected and requires a novelty recheck."
                if review.material_revision_detected
                else "No material revision was detected in this review."
            ),
            "",
            # Rendered whole. A 700-character cap used to sit here, arriving with PR #64 and never
            # explained in its commit; it was not a policy, it was an unmotivated number. It cut 60
            # of 124 live plan-review rationales (median overflow 1202 characters, 32567 characters
            # of reviewer reasoning in total) and left the remainder reachable only inside the
            # machine-side *_plan_review.yaml, which no reader-facing surface points at. A character
            # count is not a verdict; the reviewer decides what its reasoning needs to say.
            _public_text(review.rationale, field=f"{label} rationale"),
            "",
        ]
    )
    if review.classified_required_changes:
        lines.extend(["Retained changes and locks:", ""])
        for item in review.classified_required_changes[:3]:
            change = _public_text(item.change, field=f"{label} classified change")
            classification = item.classification.value.replace("_", " ")
            lines.append(f"- **{classification.capitalize()}:** {change}")
        if len(review.classified_required_changes) > 3:
            lines.append(
                f"- {len(review.classified_required_changes) - 3} additional review item(s) "
                "remain in the complete dossier."
            )
        lines.append("")


def _variant_decision_text(decision: BranchDecisionKind) -> str:
    return {
        BranchDecisionKind.ACCEPTED: "Accepted for planning.",
        BranchDecisionKind.ACCEPTED_REQUIRES_NEW_SKILL: (
            "Accepted for planning; later execution requires a new skill."
        ),
        BranchDecisionKind.REJECTED_DATASET_MISMATCH: (
            "Rejected because the inspected dataset did not support the required design."
        ),
        BranchDecisionKind.REJECTED_OPERATIONALIZATION_FAILURE: (
            "Rejected because a faithful operationalization was not established."
        ),
        BranchDecisionKind.REJECTED_SCIENTIFIC_DRIFT: (
            "Rejected because the available plan would drift from the protected question."
        ),
        BranchDecisionKind.REJECTED_INSUFFICIENT_EVIDENCE: (
            "Rejected because planning evidence remained insufficient."
        ),
        BranchDecisionKind.REJECTED_LOW_SCIENTIFIC_VALUE: (
            "Rejected after review of the proposed scientific contribution."
        ),
        BranchDecisionKind.HUMAN_ESCALATION: (
            "Closed as an optional-review escalation without accepted-plan authority."
        ),
        BranchDecisionKind.PENDING: "No terminal planning disposition was recorded.",
    }[decision]


def _spell_out_internal_field(match: re.Match[str]) -> str:
    """Rewrite only the SUFFIX of a matched internal field name.

    `str.replace("id", "identifier")` rewrites every occurrence of the substring, not the suffix
    the match is about, and four of this pattern's twenty-two names carry `id` inside their stem:
    measured 2026-08-18, `provider_id` published as `providentifierer identifier` and
    `evidence_digest` as `evidentifierence digest`. Both stems are ordinary words a planner writes
    about provenance, so the corruption reaches the reader on exactly the sentences this
    normalisation exists to keep.
    """

    stem, _, suffix = match.group(0).rpartition("_")
    spelled = "identifier" if suffix.lower() == "id" else suffix
    return f"{stem.replace('_', ' ')} {spelled}"


def _public_text(value: object, *, field: str) -> str:
    text = " ".join(str(value).split()).strip()
    if not text:
        raise FamilyDetailedPageError(f"{field} is empty")
    # Dataset schemas legitimately use these names as public columns, and the private identity
    # boundary below protects run provenance, not that scientific schema fact. The carve-out used
    # to be `event_id` alone and only inside evidence fields, which left the rest of the family
    # fail-closed on prose the planner had every reason to write.
    #
    # Measured on the 2026-08-14 NLB leg: the dataset narrative reads "a single subject (subject_id
    # Jenkins), single scaled session (session_id small)". `session_id` raises
    # `FamilyDetailedPagePrivacyError`, `materialize.py` swallows it as page isolation, and the
    # family's ENTIRE reading guide is dropped. It survived that run only by ranking outside the
    # rendered top three.
    #
    # Normalising the whole family in every field removes the machine-readable field NAME and keeps
    # the sentence. It weakens nothing: `_INTERNAL_VALUE` below still refuses an actual identifier
    # value such as `owner-session-052a081a167b`, which is what a leak looks like.
    text = _INTERNAL_FIELD.sub(_spell_out_internal_field, text)
    for pattern, label in (
        (_ABSOLUTE_POSIX_PATH, "local absolute path"),
        (_ABSOLUTE_WINDOWS_PATH, "local absolute path"),
        (_SHA256, "digest"),
        (_INTERNAL_FIELD, "internal identity field"),
        (_INTERNAL_VALUE, "internal identity value"),
        (_FORBIDDEN_PUBLIC_FRAGMENT, "private source or sidecar reference"),
        (_MARKDOWN_LINK, "untrusted Markdown link"),
    ):
        if pattern.search(text):
            raise FamilyDetailedPagePrivacyError(f"{field} contains forbidden {label}")
    # Neutralise Markdown and HTML meaning WITHOUT destroying scientific notation. Substituting a
    # different character does both, and this function did it twice:
    #   `<` -> `(` published `move_onset ) tau` where the planner wrote `move_onset > tau`;
    #   `[` -> `(` published the OPEN interval `(go_cue, go_cue + W)` where `dossier.md`, rendered
    #   by the sibling renderer, published the CLOSED interval `[go_cue, go_cue + W]` — two public
    #   pages of one family stating different mathematics.
    # Escaping and HTML entities remove the syntax and keep the sentence, which is what
    # `context_pages.py:1033` already does for the same characters.
    return (
        text.replace("\\", "\\\\")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("`", "\\`")
    )


#: Parentheses, not brackets. `[internal id]` immediately before a `(` composes into
#: `[internal id](…)` — a syntactically valid Markdown link — and `validate_family_detailed_page`
#: requires the page's link list to equal exactly `[dossier_href]`, so the whole reading guide is
#: discarded over a marker that was supposed to keep the sentence readable.
_REDACTED_INTERNAL_ID = "(internal id)"


def _redact_internal_tokens(markdown: str, forbidden_tokens: set[str]) -> str:
    """Replace internal identifiers with a readable marker, keeping the prose around them.

    Longest-first so a token that contains a shorter sibling cannot be half-replaced and leave the
    remainder behind — the validator runs immediately after and would still catch that, but a
    partial redaction would be a confusing way to fail.

    This does not soften the privacy boundary. The identifier is still absent from the published
    page; what changes is that the sentence carrying it survives. The alternative in place until
    2026-07-28 was to raise, which the add-on's page-isolation handler swallowed, so the reader
    silently received no reading guide at all for that family.
    """

    for token in sorted((item for item in forbidden_tokens if item), key=len, reverse=True):
        if not is_identifier_shaped(token):
            # A token that reads as an ordinary word is not an identifier a reader could act on,
            # and replacing it eats prose. Measured on the 2026-08-14 NLB leg: the dataset
            # narrative carries a scale fact whose `scale_fact_id` is literally `subjects`, the
            # collector took it because the field name ends in `_id`, and every occurrence of the
            # English word vanished from the reading guides -- including "inference is conditional
            # on this one session and does not generalize across subjects", which is the single
            # most important scope caveat those pages carry. The word appeared zero times in any
            # published detailed page.
            continue
        if token in markdown:
            markdown = markdown.replace(token, _REDACTED_INTERNAL_ID)
    return markdown


def _internal_tokens(*models: object) -> set[str]:
    """Collect exact persisted identity/provenance values without guessing from prose."""

    tokens: set[str] = set()

    def add(value: object) -> None:
        token = str(value).strip()
        if len(token) >= 4:
            tokens.add(token)

    def visit(value: object, *, identity_field: bool = False) -> None:
        if isinstance(value, BaseModel):
            visit(value.model_dump(mode="json"))
            return
        if isinstance(value, dict):
            if identity_field:
                for key, item in value.items():
                    add(key)
                    visit(item, identity_field=True)
                return
            for key, item in value.items():
                key_text = str(key)
                is_identity = key_text.endswith(
                    ("_id", "_ids", "_digest", "_digests", "_path")
                ) or key_text in {
                    "provider_id",
                    "model_id",
                    "prompt_version",
                    "session_id",
                    "source_locator",
                }
                visit(item, identity_field=is_identity)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                visit(item, identity_field=identity_field)
            return
        if identity_field and value is not None:
            add(value)

    for model in models:
        if model is not None:
            visit(model)
    return tokens


def _bullet_lines(
    values: Iterable[object],
    *,
    field: str,
    empty: str = "No source-backed statement was available.",
    limit: int | None = None,
) -> list[str]:
    rendered = [_public_text(value, field=field) for value in values if str(value).strip()]
    shown = rendered if limit is None else rendered[:limit]
    lines = [f"- {value}" for value in shown] or [f"- {empty}"]
    if limit is not None and len(rendered) > limit:
        lines.append(
            f"- {len(rendered) - limit} additional item(s) remain in the complete dossier."
        )
    return lines


def _numbered_lines(values: Iterable[object], *, field: str, limit: int | None = None) -> list[str]:
    rendered = [_public_text(value, field=field) for value in values if str(value).strip()]
    shown = rendered if limit is None else rendered[:limit]
    lines = [f"{index}. {value}" for index, value in enumerate(shown, start=1)] or [
        "1. No source-backed strategy statement was available."
    ]
    if limit is not None and len(rendered) > limit:
        lines.append(
            f"{len(shown) + 1}. {len(rendered) - limit} additional step(s) remain in the "
            "complete dossier."
        )
    return lines


def _inline_list(values: Iterable[object], *, field: str, limit: int | None = None) -> str:
    rendered = [_public_text(value, field=field) for value in values if str(value).strip()]
    if not rendered:
        return "None recorded."
    shown = rendered if limit is None else rendered[:limit]
    text = "; ".join(shown)
    if limit is not None and len(rendered) > limit:
        text += f"; plus {len(rendered) - limit} additional item(s) in the complete dossier"
    return text
