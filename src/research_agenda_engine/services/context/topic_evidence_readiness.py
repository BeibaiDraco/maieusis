"""Shared deterministic topic-evidence readiness check.

A single function, called by BOTH the topic-evidence gate (as its host-side ``evidence_resolved``
pre-check) AND the V2 compiler (before it builds the TopicLiteratureContextPack). Sharing it is
what makes "an accepted brief always compiles" a real guarantee (not two copies that can drift): the
gate cannot earn-accept a brief that the compiler would then reject on a missing close-prior/open-gap
or an unresolved claim source.

The predicate has TWO axes and they are not the same kind of fact, which is why
``assess_topic_evidence_readiness`` reports them separately:

* CLOSURE -- a claim cites a source id that is not in the table, or cites one that may not support a
  scientific claim. The artifact contradicts its own evidence; nothing downstream can trust it. This
  is the axis the gate's ``evidence_resolved`` pre-check owns, and a failure there makes the reviewed
  artifact unfaithful by the gate kernel's own definition.
* COMPLETENESS -- the brief carries no typed close prior, or no typed open gap. That is a fact about
  what the literature yielded, not about the artifact's honesty. It is a real precondition for
  compiling a full-authority topic pack (an OpenGapCard asserts close-prior status WAS checked), so
  it still decides the authority ceiling. It must not decide whether a reviewer is asked, and it must
  not be laundered into "this brief is unfaithful".

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...schemas.scientific_context import TopicEvidenceBrief, TopicEvidenceClaimStatus

NO_CLOSE_PRIOR_ISSUE = "no close-prior/already-answered claim"
NO_OPEN_GAP_ISSUE = "no open-gap/open-question claim"


@dataclass(frozen=True)
class TopicEvidenceReadiness:
    """The compile-safety predicate, with its two axes kept apart.

    ``ready`` and ``issues`` are exactly what ``evaluate_topic_evidence_readiness`` has always
    returned, in the same order, so persisted rationales and the compiler's terminal message do not
    move. The split fields are additive.
    """

    missing_close_prior: bool
    missing_open_gap: bool
    closure_issues: tuple[str, ...]

    @property
    def completeness_issues(self) -> tuple[str, ...]:
        """The typed close-prior / open-gap preconditions this brief does not meet."""
        issues: list[str] = []
        if self.missing_close_prior:
            issues.append(NO_CLOSE_PRIOR_ISSUE)
        if self.missing_open_gap:
            issues.append(NO_OPEN_GAP_ISSUE)
        return tuple(issues)

    @property
    def issues(self) -> tuple[str, ...]:
        return self.completeness_issues + self.closure_issues

    @property
    def ready(self) -> bool:
        """Compile-safety: a full-authority topic pack can be built from this brief."""
        return not self.issues

    @property
    def evidence_closed(self) -> bool:
        """Hard source/claim closure only -- the gate's ``evidence_resolved`` pre-check."""
        return not self.closure_issues

    @property
    def close_prior_absence_is_the_only_gap(self) -> bool:
        """True when a typed close prior is the single thing between this brief and full authority.

        This is the state the reviewer is asked to judge: the brief is otherwise closed and complete,
        and reports no already-answered prior work. Whether that is honest for the scope or a
        retrieval/typing failure is a scientific question, which is why it gets its own ceiling
        reason rather than being folded into a bare "not ready".
        """
        return self.missing_close_prior and not self.missing_open_gap and not self.closure_issues


def assess_topic_evidence_readiness(
    brief: TopicEvidenceBrief,
    *,
    source_record_ids: set[str],
    claim_supporting_record_ids: set[str],
) -> TopicEvidenceReadiness:
    """Evaluate both readiness axes over one brief and its source table.

    ``source_record_ids`` = every record id present in the source table; ``claim_supporting_record_ids``
    = the subset that may support a scientific claim (not title-only / metadata-only). Both are computed
    once by the caller from the source table and passed in, so this stays dependency-light.
    """
    closure_issues: list[str] = []
    for claim in brief.claims:
        for source_id in claim.source_record_ids:
            if source_id not in source_record_ids:
                closure_issues.append(f"claim {claim.claim_id} cites unknown source {source_id}")
            elif source_id not in claim_supporting_record_ids:
                closure_issues.append(
                    f"claim {claim.claim_id} cites a non-claim-supporting source {source_id}"
                )
    return TopicEvidenceReadiness(
        missing_close_prior=not any(
            claim.status == TopicEvidenceClaimStatus.ALREADY_ANSWERED for claim in brief.claims
        ),
        missing_open_gap=not any(
            claim.status == TopicEvidenceClaimStatus.OPEN_QUESTION for claim in brief.claims
        ),
        closure_issues=tuple(closure_issues),
    )


def evaluate_topic_evidence_readiness(
    brief: TopicEvidenceBrief,
    *,
    source_record_ids: set[str],
    claim_supporting_record_ids: set[str],
) -> tuple[bool, list[str]]:
    """Return (ready, issues). The compile-critical checks the gate and the compiler both require."""
    readiness = assess_topic_evidence_readiness(
        brief,
        source_record_ids=source_record_ids,
        claim_supporting_record_ids=claim_supporting_record_ids,
    )
    return (readiness.ready, list(readiness.issues))


def topic_evidence_readiness_statements(readiness: TopicEvidenceReadiness) -> list[str]:
    """The deterministic host observations handed to the reviewer as STATED FACTS.

    Neutral by construction: each line reports what the host counted, names nothing as a defect, and
    asks for no particular verdict. The reviewer decides what the absence means; before this existed
    the host decided it alone, by not calling the reviewer at all.

    Each line is strictly a COUNT over the typed claims, never an inference from one. Saying that an
    absent typed close prior also means the human-readable ``questions_already_answered`` summary is
    empty would be a host assertion about a field the host did not read -- and a prose-only close
    prior with no typed claim behind it is exactly the state ``close_prior_identified`` exists to
    catch, so a false host statement there would mislead the one judgement this packet exists for.
    """
    statements: list[str] = []
    if readiness.missing_close_prior:
        statements.append("This brief carries no typed already_answered (close-prior) claim.")
    else:
        statements.append(
            "This brief carries at least one typed already_answered (close-prior) claim."
        )
    if readiness.missing_open_gap:
        statements.append("This brief carries no typed open_question (open-gap) claim.")
    else:
        statements.append("This brief carries at least one typed open_question (open-gap) claim.")
    for issue in readiness.closure_issues:
        statements.append(f"Host source-closure observation: {issue}.")
    return statements
