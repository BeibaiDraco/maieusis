from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FrontHalfAuthorityCeiling(StrEnum):
    """Maximum authority a front-half product may earn without new evidence review."""

    VERIFIED = "verified"
    PROVISIONAL_INSPIRATION = "provisional_inspiration"


class FrontHalfCeilingReason(StrEnum):
    """WHY a front half was capped at ``PROVISIONAL_INSPIRATION``.

    Deliberately a SIBLING of the ceiling rather than a third ceiling member.  Roughly ten
    ``== PROVISIONAL_INSPIRATION`` comparisons across ``end_to_end.py``,
    ``question_scientist_family.py``, ``front_half_persist.py`` and
    ``question_scientist_context_v2.py`` decide demotion by equality, so a third ceiling value would
    be silently treated as verified by every one of them.  The ceiling therefore stays binary and
    every existing demotion keeps firing unchanged; only the explanation is new.

    The distinction is not cosmetic.  ``HARVEST_EMPTY`` means the topic brief never reached an
    independent reviewer: there was no claim-supporting source to review.  The other three all mean
    the brief WAS reviewed, and they differ in what the review found:

    * ``REVIEWED_COVERAGE_GAP`` -- the reviewer judged the coverage short of what this scope needs
      (and on the two 2026-08-11 legs a second inquiry agent then re-adjudicated that verdict).
    * ``READINESS_NOT_MET`` -- the review returned no adverse verdict, but the brief still lacks the
      typed structure a full-authority topic pack is compiled from (a close prior, an open gap, or
      claim citations that resolve).  It could not compile at full authority.
    * ``CLOSE_PRIOR_ABSENCE_REVIEWED_HONEST`` -- the one thing missing is a typed close prior, and
      the reviewer, reading the same sources, earned an accept, which is its judgement that the
      brief's silence about prior work is faithful to what the packet contains.  A genuinely new
      area has no already-answered prior work to report, and until 2026-08-13 that state was
      indistinguishable from a retrieval failure because no reviewer was ever asked.

    ``READINESS_NOT_MET`` predates that change and appears in runs capped before it, where nothing
    was reviewed.  Its wording therefore states what the brief lacks and what would lift the cap, and
    never asserts either that the literature was or that it was not reviewed -- the one sentence that
    stays true for a run from either era.
    """

    READINESS_NOT_MET = "readiness_not_met"
    HARVEST_EMPTY = "harvest_empty"
    REVIEWED_COVERAGE_GAP = "reviewed_coverage_gap"
    CLOSE_PRIOR_ABSENCE_REVIEWED_HONEST = "close_prior_absence_reviewed_honest"
    #: The reviewer never gave a verdict: it kept asking for changes until the configured rounds ran
    #: out, or the host had no lawful repair for what it asked. Distinct from all four above, which
    #: describe what a review FOUND. `end_to_end.py` already said in prose that neither of those is
    #: a statement that the science is wanting -- but the branch implementing it was gated on the
    #: brief being structurally unready, so a brief that WAS ready still died on a non-verdict. This
    #: member is what the ready path caps as instead.
    REVIEW_ROUNDS_EXHAUSTED = "review_rounds_exhausted"


@dataclass(frozen=True)
class FrontHalfCeilingCause:
    """The capped front half's reason, its residual dimensions, and its public sentence.

    Carried (not persisted directly) from the dataset half to the readers that must not misdescribe
    the cap: the Question Scientist topic pack, the open-gap export guard, and the dossier banner.
    ``public_reason`` is rendered upstream from controlled semantic labels only — never raw model
    prose — so plumbing it here cannot leak reviewer text into a public surface.
    """

    reason: FrontHalfCeilingReason
    #: The semantic dimensions the terminal inquiry could not establish from the packet -- its
    #: ``packet_absent`` and ``indeterminate`` assessments.  Deliberately NOT filtered by
    #: ``essential_to_scope``: the inquiry's essentiality judgement decides what the public sentence
    #: should name, but an OpenGapCard asserts that close-prior and open-gap coverage were CHECKED,
    #: and that assertion is unbacked whether or not the dimension was scope-essential.  Measured on
    #: a 2026-08-11 qualification leg, filtering by essentiality would have dropped its `open_gaps:
    #: indeterminate` row and left the guard inert on the case that motivated it.
    residual_dimensions: tuple[str, ...] = ()
    public_reason: str = ""
