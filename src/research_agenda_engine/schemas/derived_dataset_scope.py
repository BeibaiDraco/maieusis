"""The scope a model derived by reading the dataset's own reviewed narrative.

WHY THIS TYPE EXISTS, measured. A run's literature scope was a hand-written list of search terms in
the project config. On 2026-08-17 two release configs were found carrying **byte-identical**
``research_intent`` blocks -- eight generic terms, no theme, no description -- for 139 mice doing a
decision task across twelve laboratories and for one macaque doing delayed reaches. Retrieval issues
four queries per term, so eight terms bought half the queries a sixteen-term scope buys, and both
candidate pools EXHAUSTED (75 and 79 of a requested 100) where the third leg's filled. The model
corpus selector, having read every abstract in the pool, reported the dimensions the reviewer grades
on as absent from the POOL; the independent reviewer, seeing only the kept corpus, failed
``generic_lane_coverage``. The papers were not mis-ranked. They were never retrieved.

Rewriting the terms by hand fixed retrieval and did not fix the verdicts: it introduced a NEW
failure, ``scope_fidelity``, because terms chosen to cover a grader's eight criteria have the shape
of the rubric rather than of a scientific question, and no brief can faithfully serve sixteen terms
spanning five sub-areas. ``docs/governance/RELEASE_PROCESS.md`` names re-aiming ``research_intent``
to obtain a pass as release-level p-hacking, and a human who edits the terms after reading the
verdicts cannot prove they did not do it.

So the default scope is derived once, before any verdict exists, by a model that reads the dataset's
reviewed narrative and nothing else. What the deriver is NOT shown is the point of the type:

* no gate verdict, criterion name, ``required_changes`` entry, or authority ceiling -- it is asked
  once, before review, and is not a loop, so it cannot optimise toward approval;
* no exact schema, sample, planner evidence, capability registry, or confirmation surface -- the
  same firewall ``services/context/research_scope.py`` already carries structurally;
* no retrieved literature -- it names what to search for, never what was found.

The per-term reasoning lives HERE and is persisted, but is deliberately absent from
``ResolvedResearchScope``: ``build_topic_evidence_turn_input`` passes the resolved scope verbatim
into the independent reviewer's packet, so a rationale attached there would be the deriver arguing
its case to the reviewer that grades ``scope_fidelity``. Identity crosses that boundary; prose does
not.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

DATASET_SCOPE_DERIVER_PROMPT_VERSION = "dataset_scope_deriver/v2"

#: A term measured at this pool size was not measured at all. It is NOT zero: an unreachable or
#: rate-limited index leaves a term uncounted, and recording that as "no literature exists" would
#: drop a good term on the strength of a failed HTTP request.
TERM_POOL_UNMEASURED = -1


class DerivedScopeStatus(StrEnum):
    """How the scope on this run was arrived at. Every run records one, including runs that derived
    nothing -- an absent record is indistinguishable from a step that shipped inert, and this
    repository has already published a feature that passed a conformance audit while producing
    nothing."""

    DERIVED_BY_MODEL = "derived_by_model"
    USER_DECLARED_SCOPE = "user_declared_scope"
    AUGMENTED_USER_SCOPE = "augmented_user_scope"
    DEGRADED_TO_DETERMINISTIC = "degraded_to_deterministic"
    DISABLED_BY_CONFIG = "disabled_by_config"
    LITERATURE_DISABLED = "literature_disabled"


class DerivedScopeTerm(BaseModel):
    """One proposed search term, and whether it survived to the scope.

    ``why`` is the only free text the deriver produces. It is persisted for a reader and for a later
    audit; it never reaches the topic-evidence reviewer.
    """

    model_config = ConfigDict(extra="forbid")

    term: str
    why: str = ""
    dataset_basis: list[str] = Field(
        default_factory=list,
        description="the narrative fields this term was drawn from, named by the deriver",
    )
    kept: bool = True
    pool: int = TERM_POOL_UNMEASURED
    dropped_reason: str = ""

    @field_validator("term")
    @classmethod
    def require_term(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DerivedScopeTerm term must be non-empty")
        return value


class DerivedDatasetScope(BaseModel):
    """The persisted, replayable record of one scope derivation.

    Identity is stamped by the host, never accepted from the model reply: a model that could name
    its own ``prompt_version`` or ``scope_id`` could claim an authority it does not have.
    """

    model_config = ConfigDict(extra="forbid")

    scope_id: str
    status: DerivedScopeStatus
    terms: list[str] = Field(default_factory=list)
    construct_families: list[str] = Field(default_factory=list)
    term_rationales: list[DerivedScopeTerm] = Field(default_factory=list)
    derivation_notes: str = ""

    #: What the deriver read. A thin narrative yields a thin scope, and this is where a reader sees
    #: which it was.
    narrative_id: str = ""
    narrative_digest: str = ""
    dataset_id: str = ""

    #: How much of this the deterministic fallback would have produced anyway. A derivation whose
    #: overlap equals its term count changed nothing and says so here.
    deterministic_overlap: int = 0
    #: What a reuse search asks for. Empty on every degraded path: keyword extraction over the
    #: narrative cannot invent the name a citing paper would use.
    dataset_identity_terms: list[str] = Field(default_factory=list)
    deterministic_terms: list[str] = Field(default_factory=list)

    prompt_version: str = DATASET_SCOPE_DERIVER_PROMPT_VERSION
    provider_id: str = ""
    model_id: str = ""
    input_digest: str = ""
    output_digest: str = ""
    #: Exception CLASS NAME only. Provider messages can carry signed URLs and account identifiers,
    #: and hard rule 13 keeps those out of artifacts, prompts and exports.
    degraded_reason: str = ""

    @field_validator("scope_id")
    @classmethod
    def require_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DerivedDatasetScope scope_id must be non-empty")
        return value

    @property
    def kept_terms(self) -> list[str]:
        return [item.term for item in self.term_rationales if item.kept]

    def activity_detail(self) -> str:
        """One countable clause for the run's source-activity file.

        Counts, not adjectives: a reader can check every number here against this artifact and
        against the query plan the run actually issued.
        """

        if self.status is DerivedScopeStatus.USER_DECLARED_SCOPE:
            return "scope derivation inactive: the config declared its own topic terms"
        if self.status is DerivedScopeStatus.DISABLED_BY_CONFIG:
            return "scope derivation inactive: disabled by scope_derivation=never"
        if self.status is DerivedScopeStatus.LITERATURE_DISABLED:
            return "scope derivation inactive: topic literature is not enabled for this run"
        proposed = len(self.term_rationales)
        dropped = sum(1 for item in self.term_rationales if not item.kept)
        if self.status is DerivedScopeStatus.DEGRADED_TO_DETERMINISTIC:
            return (
                f"scope derivation degraded to deterministic keyword extraction after "
                f"{self.degraded_reason or 'an error'}; {len(self.terms)} term(s) kept"
            )
        return (
            f"scope derived from the reviewed dataset narrative: {proposed} term(s) proposed, "
            f"{len(self.terms)} kept, {dropped} dropped for an empty literature pool, "
            f"{self.deterministic_overlap} also produced by deterministic extraction"
        )
