# Reading the labels

[Documentation home](INDEX.md) · [Demo gallery](../demos/ALL_QUESTIONS.md) ·
[What a run produces](INPUTS_AND_OUTPUTS.md)

Every artifact Maieusis publishes carries labels saying how much weight it can bear. They are the
point of the system — a plan without them is just confident prose — but there are several of them,
they appear on different pages, and two of them use the word *provisional* for different things.

This page lists all of them, with their permitted values. Read it once and the demonstrations stop
being ambiguous.

## The one to read first: how deep did the planner actually go?

`Dataset grounding level`, on the `dossier.md` of every family whose planner opened the data. A
family that never reached planning has no grounding level, because nothing was inspected — four of
the twenty-four published families are in that state, and their pages carry a different vocabulary
entirely, described at the end of this page.

This is an ordered ladder, weakest first:

| Value | What the planner actually did |
| --- | --- |
| `unknown` | Nothing was recorded. Treat it as the bottom of the ladder, not as a middle rung. |
| `documentation_inventory_only` | Read the dataset's documentation and file inventory. No schema was opened. |
| `schema_metadata_inspected` | Opened schemas, manifests, and metadata: field names, shapes, counts, coverage. |
| `sample_inspected` | Opened real data samples, not only their description. |
| `full_local_structural_available` | The complete local structure was available to it, beyond sampling. |

A plan at `documentation_inventory_only` can still be a good plan. It is a plan built on what the
dataset *says* about itself, and it has not yet met the data. Weigh it accordingly.

One caution the demonstrations themselves show: the label describes the deepest inspection the run
could *safely certify*, and a family's own evidence sometimes reads richer than its label. Where the
two disagree, believe the evidence bullets in `dossier_detailed.md` and treat the label as a floor.

## Outcome, on the gallery

These are the values a family can be reported as on [the gallery](../demos/ALL_QUESTIONS.md). The first
three say a plan exists somewhere in the family; the rest say it does not, and they do not mean the
same thing as each other.

| Value | Meaning |
| --- | --- |
| **Plan developed (provisional)** | Both variants reached independently reviewed plans. |
| **Mixed family** | One variant reached a plan; its sibling closed with a stated reason after the planner had inspected the dataset. |
| **Deferred on prior-art grounds** | One variant reached a plan; the other was held back *before* planning, because prior-art review resolved a close published prior it would first have to be distinguished from. |
| **Stopped before planning on prior-art grounds** | The same review, and *every* variant stopped there — so the family has no plan and no planning record at all. Not a rejection: nothing was inspected and judged unanswerable; the question closed before it reached that stage. |
| **Scientific rejection terminal** | The planner read the data and closed the family without a plan, naming what was missing rather than substituting a proxy. This is a scientific answer. |
| **Service warning** | No plan survives, and the cause is a provider that stayed unavailable after bounded retries. Infrastructure, not science. |
| **Validation warning** | No plan survives, and the cause is that the material the planner returned could not be fully validated on the way back in. Infrastructure, not science. |

A family can also carry any other status the product defines; the page prints the product's own
label rather than inventing a friendlier word for an outcome nobody has read yet, and states that no
accepted plan is published for it.

Here **provisional** means *reviewed by a second model rather than a human expert, and never
executed*. That is what it means wherever a plan appears; a family with no plan has no such
authority to qualify.

The flow figure on the front page ends with a dossier marked `plan • reject • defer • warning`.
Those are the four shapes a run can produce; the names above are how a *family* is reported once it
has one. `plan` becomes **Plan developed** or, when only one variant made it, **Mixed family**;
`reject` becomes **Scientific rejection terminal**; `defer` becomes one of the two prior-art values
depending on whether a sibling survived; `warning` becomes **Service warning** or **Validation
warning** depending on where the failure was.

**The published demonstrations contain warning families**, and they are on the page rather than
quietly dropped. The `noise correlations` run carries three: one service warning, and two validation
warnings whose cause is written down — the planner revised its own evidence files under new names
and left the earlier drafts beside them, and both copies were read back. That is a defect in how
this system reads a planner's output, scheduled for repair, and it says nothing about the two
questions it cost.

## Authority, on each dossier

`Authority` most often reads `Automated independent review, planning only`. On a run whose topic
literature did not clear its own review it also carries `capped at provisional inspiration`; no
family in these demonstrations does, because all four runs cleared it. It is not the only value. The others say something
weaker, and they say it plainly:

| Value | What it means |
| --- | --- |
| `Automated independent review, planning only` | A second model, on a different provider, reviewed the plan. The ordinary case. |
| `Automated host authorization, planning only; no independent review was recorded` | The plan exists and no independent review is on file for it. |
| `Human reviewed, planning only` | A human expert reviewed it. Nothing in the published demonstrations carries this. |
| `Provisional / degraded` | The family did not complete normally — a warning terminal. No review happened. |
| `Provisional; review authority unresolved` / `Provisional; review authority missing` | A review was expected and its record cannot be resolved. Read it as absent, not as passed. |
| `No promoted scientific authority` | Nothing here was promoted above the authority of its evidence. |

Two further values, `Development-model surrogate; not serious-use acceptance` and
`Fixture only; not scientific authority`, mark output from development or test configurations. They
should never appear on a scientific run; if you see one, the run was not configured for science.

That cap is a **different** use of the word. It is not about who reviewed the plan; it is about the
evidence that reached the question generator in the first place. `Authority ceiling` states it
directly:

| Value | Meaning |
| --- | --- |
| `verified` | The topic-literature evidence behind these questions passed its own independent review. |
| `provisional_inspiration` | That evidence did not earn verified authority. `Ceiling reason` says why, and the reasons are not equivalent. |

**In these demonstrations all four runs reached `verified`; none is capped.** That is new, and it is
the most substantive thing that changed between this release and the last: every previous published
set carried `provisional_inspiration` on every leg, because the topic-literature brief never cleared
its own independent review. These did.

The two words still mean different things and it is worth keeping them apart. A family is
*provisional* in the gallery sense — reviewed by a second model rather than a human expert, and
never executed — and that remains true of everything here. *Capped* is the separate, upstream
question of whether the literature the questions rest on passed review. Nothing on these pages is
capped; everything on them is provisional. The two words being so close is a wart in the vocabulary
rather than a subtlety worth admiring.

`Ceiling reason` records **why** a run was capped. It is one of five values, and they are not
interchangeable: the difference between "nobody reviewed this literature" and "somebody reviewed it
and said it was thin" changes what you should do with the questions.

| Value | Meaning |
| --- | --- |
| `harvest_empty` | No topic literature was retrieved to review at all. The questions rest on the dataset and the paper bank. |
| `readiness_not_met` | The brief did not reach the state review requires and stayed at draft. The run does not say the literature is thin, only that it was not reviewed — and neither should a reader. |
| `reviewed_coverage_gap` | The literature **was** independently reviewed, and a second agent re-checked that verdict. Both found it short of the coverage this question scope needs. It was read; there was not enough of it. |
| `close_prior_absence_reviewed_honest` | Prior-art review ran and found no already-answered prior work to report. The cap is for a different reason: the typed close-prior and open-gap structure that verified authority is compiled from is not closed. Review happened and had nothing to report; that is not a clean novelty finding. |
| `review_rounds_exhausted` | The review-and-revise loop hit its bound before the brief cleared. The last state stands, uncleared. |

The third one is the case worth pausing on. It does not mean the reading step was skipped — it means
the reading happened and reported a shortfall, and the run continued at a cap instead of stopping.
You will see it two places: the banner at the top of `summary.md` says the literature was
independently reviewed rather than saying it was not, and the run's `README.md` names the dimension
that came up short. Read that name — it tells you whether the gap touches the question you care
about.

Runs published before this label existed do not carry it. No run in the current demonstrations is
capped, so none of the five reasons above applies to anything on these pages — they are documented
because the label is part of the vocabulary a reader may meet in their own runs, not because you
will find one here.

## The rest

| Label | Where | Values | Meaning |
| --- | --- | --- | --- |
| `Proposal review status` | family page | `model_generated` | The question as first proposed, before any review. |
| `Review status` | context artifacts | `ai_reviewed`, `automated_reviewed` | An independent model reviewed this artifact. The two spellings mean the same thing and should not both exist. |
| `Dataset claim status` | dossier | `unverified` | Statements about the dataset are planning hypotheses, not certified facts. |
| `Family status` | reading guide | twelve values, of which these demonstrations print `Accepted planning dossier`, `Mixed family: …`, `Scientific rejection terminal`, `Service warning` and `Validation warning` | The terminal the family reached. First line of every reading guide — and a family with no guide has none; read its `Closure` instead. |
| `Accepted-plan authority` | dossier | `No`, `Yes, for planning only`, `Yes, provisionally and for planning only` | Whether an accepted plan exists here, and under whose review. Never authorization to execute. |
| `Claim ceiling` | dossier | `descriptive`, `associational`, `predictive` | The strongest kind of claim this design could support if executed. Never causal. `descriptive` is the most constrained. |
| `Evidence basis` | gallery, question and topic-evidence pages | `abstract-only` | The supporting literature was read as abstracts and metadata, not full text. |
| `Shortlist disposition` | family page | see below | Whether a variant reached the planning stage. Shortlisting is not scientific approval. |

### Shortlist disposition, in full

Two of these mean the planner opened the variant. Everything else means it did not, and the reasons
are not interchangeable:

| Value | Meaning |
| --- | --- |
| `Active for planning` | The planner ran on this variant. |
| `Shortlisted for planning; this is not scientific approval` | The family was shortlisted, and this variant inherits that. The planner ran. |
| `Not carried into planning — bounded prior-art review found a close prior that directly recaps this variant` | Prior-art review resolved a published prior that recaps it. |
| `Not carried into planning — deferred: …` | Prior-art review stopped the variant before planning, and the full sentence says which of two reasons: it resolved a close prior the question must be distinguished from, or it could not retrieve enough evidence to judge the variant at all. Read the sentence — the second is not a finding about the literature. |
| `Not shortlisted — deferred` / `— rejected by the configured family review` / `— revision requested` | The whole FAMILY closed at the shortlist gate, so every variant carries the family's disposition. |
| `Not shortlisted — this family was not reviewed: the run could not complete its novelty review…` | Infrastructure, not a finding. The sentence says so in full rather than letting the family read as deferred. |
| `Not active; family review recorded no decision for this variant` | Family review carried the variant and recorded nothing. The one genuinely anomalous shape. |
| `Not active — deferred` / `— rejected by family review` / `— revision requested` | Family review decided on this variant specifically. |
| `Disposition unavailable` | Nothing was recorded. Read it as unknown, not as approved. |

Only the first two mean a plan could exist. When you are counting, count those.

## A family that never reached planning reads differently

Four of the twenty-four published families produced no plan for reasons that are not scientific, and
their pages do not carry the labels above at all — no grounding level, no `Family status`, no
authority line, no bridge sentence. There is nothing for those labels to describe: the planner never
opened the data.

What they carry instead is a `## Current disposition` block:

| Label | What it says |
| --- | --- |
| `Shortlist` | Where the family stood at the shortlist gate — `shortlisted`, `deferred`, `rejected`, `needs_revision`. A family can be `shortlisted` and still end here. |
| `Planning` | `not_reached` on all four. No planning branch was opened. |
| `Closure` | How it ended — `degraded` when the machinery stopped it. |
| `Authority` | `provisional`. Nothing here was promoted. |
| `Status note` | One sentence naming the actual cause, in the run's own words. |

**Read the status note.** It is the only place these pages say what happened, and the four causes in
this release are not alike: one provider stayed unavailable after bounded retries, two returned
material that could not be validated on the way back in, and one closed at prior-art review before
any planner was involved. None is a statement about the science.

## Two phrases worth knowing

**"Accepted for planning; later execution requires a new skill."** On many accepted variants. It
means the plan is sound but executing it would need a capability the planner does not have — a
decoder for a particular storage format, say. It is a note about implementation effort, not about
scientific quality.

**"A separate bridge approval is still required."** At the end of every dossier that carries a plan
or a scientific closure — twenty of the twenty-four. The four that never reached planning end on a
next action instead, because there is nothing to approve a bridge for. The *bridge* is the
step from a plan to an executed analysis. Maieusis never opens it, and nothing in a dossier is
permission to. That step is yours.

---

[Documentation home](INDEX.md) · [Limitations](LIMITATIONS.md) ·
[When a run stops](RUN_SUPERVISION.md)
