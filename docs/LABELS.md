# Reading the labels

[Documentation home](INDEX.md) · [Demo gallery](../demos/QUESTIONS.md) ·
[What a run produces](INPUTS_AND_OUTPUTS.md)

Every artifact Maieusis publishes carries labels saying how much weight it can bear. They are the
point of the system — a plan without them is just confident prose — but there are several of them,
they appear on different pages, and two of them use the word *provisional* for different things.

This page lists all of them, with their permitted values. Read it once and the demonstrations stop
being ambiguous.

## The one to read first: how deep did the planner actually go?

`Dataset grounding level`, on each family's `dossier.md`. This is an ordered ladder, weakest first:

| Value | What the planner actually did |
| --- | --- |
| `documentation_inventory_only` | Read the dataset's documentation and file inventory. No schema was opened. |
| `schema_metadata_inspected` | Opened schemas, manifests, and metadata: field names, shapes, counts, coverage. |
| `sample_inspected` | Opened real data samples, not only their description. |

A plan at `documentation_inventory_only` can still be a good plan. It is a plan built on what the
dataset *says* about itself, and it has not yet met the data. Weigh it accordingly.

One caution the demonstrations themselves show: the label describes the deepest inspection the run
could *safely certify*, and a family's own evidence sometimes reads richer than its label. Where the
two disagree, believe the evidence bullets in `dossier_detailed.md` and treat the label as a floor.

## Outcome, on the gallery

Four values, from [the gallery](../demos/QUESTIONS.md):

| Value | Meaning |
| --- | --- |
| **Plan developed (provisional)** | Both variants reached independently reviewed plans. |
| **Mixed family** | One variant reached a plan; its sibling closed with a stated reason. |
| **Deferred on prior-art grounds** | A variant was held back before planning because the review resolved a close prior. |
| **Scientific rejection terminal** | The family closed without a plan, with the evidence that closed it. |

Here **provisional** means *reviewed by a second model rather than a human expert, and never
executed*. That is true of every family in every demonstration.

The flow figure on the front page ends with a dossier marked `plan • reject • defer • warning`.
Those are the four shapes a run can produce; the four names above are how a *family* is reported
once it has one. `plan` becomes **Plan developed** or, when only one variant made it, **Mixed
family**; `reject` becomes **Scientific rejection terminal**; `defer` becomes **Deferred on
prior-art grounds**. A `warning` dossier is produced when infrastructure fails rather than science,
and none of the published demonstrations contains one.

## Authority, on each dossier

`Authority` reads `Automated independent review, planning only` — and on some families adds
`capped at provisional inspiration`.

That cap is a **different** use of the word. It is not about who reviewed the plan; it is about the
evidence that reached the question generator in the first place. `Authority ceiling` states it
directly:

| Value | Meaning |
| --- | --- |
| `verified` | The topic-literature evidence behind these questions passed its own independent review. |
| `provisional_inspiration` | That evidence stayed at draft. The questions may be well-formed and still rest on unreviewed literature. |

In these demonstrations the IBL run is `verified`; the NLB and climate runs are
`provisional_inspiration`. So a family can be *provisional* in the gallery sense (automated review,
as all are) and additionally *capped* in this sense (unreviewed upstream literature). The two words
are unrelated, which is a wart in the vocabulary rather than a subtlety worth admiring.

## The rest

| Label | Where | Values | Meaning |
| --- | --- | --- | --- |
| `Proposal review status` | family page | `model_generated` | The question as first proposed, before any review. |
| `Review status` | context artifacts | `ai_reviewed`, `automated_reviewed` | An independent model reviewed this artifact. The two spellings mean the same thing and should not both exist. |
| `Dataset claim status` | dossier | `unverified` | Statements about the dataset are planning hypotheses, not certified facts. |
| `Claim ceiling` | dossier | `associational`, `predictive` | The strongest kind of claim this design could support if executed. Never causal. |
| `Evidence basis` | gallery, dossier | `abstract-only` | The supporting literature was read as abstracts and metadata, not full text. |
| `Shortlist disposition` | family page | `Shortlisted for planning`, `Active for planning`, `Not carried into planning — deferred` | Whether a variant reached the planning stage. Shortlisting is not scientific approval. |

## Two phrases worth knowing

**"Accepted for planning; later execution requires a new skill."** On many accepted variants. It
means the plan is sound but executing it would need a capability the planner does not have — a
decoder for a particular storage format, say. It is a note about implementation effort, not about
scientific quality.

**"A separate bridge approval is still required."** At the end of every dossier. The *bridge* is the
step from a plan to an executed analysis. Maieusis never opens it, and nothing in a dossier is
permission to. That step is yours.

---

[Documentation home](INDEX.md) · [Limitations](LIMITATIONS.md) ·
[When a run stops](RUN_SUPERVISION.md)
