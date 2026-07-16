# Method overview

Maieusis develops a question far enough to decide whether it deserves a real
analysis plan. It stops before analysis execution.

<!-- RELEASE-ASSET-SLOT: docs/assets/maieusis-question-development.png -->

## The idea in one minute

1. **Learn how questions were formed, not just what papers said.** Each source
   paper becomes a PaperCase. Its important cited works and local citation
   contexts support a reviewed formation trace: background → unresolved gap →
   noticed data opportunity → question → possible scientific consequence.
2. **Separate a reusable move from a paper-specific fact.** Reviewed traces
   across papers are compared to induce cross-paper question-formation
   patterns. A pattern is not a formula that forces every new question; it is
   a source-backed reasoning move the Question Scientist may adapt.
3. **Propose with broad context.** The Question Scientist sees reviewed
   patterns, current topic literature, a coarse DatasetNarrative, and the user's
   research intent as separate inputs. It proposes visible QuestionFamilies
   with scientifically distinct variants.
4. **Inspect the real target only after proposal.** Each shortlisted family gets
   an isolated Question Owner and Dataset Planner. The planner reads real
   documentation, code, metadata, and small samples. The owner protects the
   scientific meaning. Together they produce a grounded plan, revise the
   question, reject it, defer it, or close honestly as incomplete.
5. **Review before presenting closure.** An independent reviewer checks intent
   preservation, dataset grounding, competing explanations, controls,
   overclaim, and material revision. The system then renders an end-user
   dossier and retains a machine/audit record.

## DatasetNarrative: useful context without premature certainty

The DatasetNarrative is a source-backed, coarse description of what the target
dataset broadly contains and why it may be scientifically useful. It is built
from official links, documentation, metadata, and bounded source packets.

It is deliberately **not** a complete table/column schema, coverage guarantee,
or feasibility certificate. Giving a proposer every exact variable and joint
coverage fact can make ideation imitate the current schema instead of asking
important questions. Exact units, joins, events, hierarchy, missingness,
controls, and estimability are inspected later inside the isolated planning
branch.

Every narrative claim keeps its source identity. Missing or weak source support
lowers the authority ceiling rather than being filled with plausible prose.

## PaperBank: from papers to question-forming patterns

For each source paper, Maieusis:

1. parses the PDF into source-addressable spans;
2. extracts a PaperCase whose claims point back to those spans;
3. identifies citations that actually participated in forming the question,
   using local citation context and available bibliographic/abstract evidence;
4. drafts a formation trace that distinguishes the paper's background,
   tension, data opportunity, inferential move, resulting question, and
   scientific stakes;
5. sends the trace to an independent reviewer; and
6. induces and independently reviews patterns across accepted traces.

A pattern therefore summarizes a recurring move across source-bound cases. It
does not claim that the papers used identical wording or that every cited work
was available in full text. Paper identity, citations, evidence spans, review
status, prompt version, model identity, and content hashes remain visible.

## Literature retrieval and evidence authority

Topic literature is retrieved independently from the PaperBank so historical
question-formation examples are not confused with the current field state.
The default route uses public scholarly metadata sources and can enrich records
with lawful open full text where available.

Evidence can remain useful when incomplete, but its authority is explicit:

- source-backed and independently reviewed artifacts can support the verified
  route;
- incomplete but source-bound artifacts may support provisional inspiration;
- title-only, metadata-only, diagnostic-only, blocked, or fabricated material
  cannot be relabeled as verified evidence; and
- the final family, plan, and dossier cannot outrank the authority of the inputs
  that support it.

Novelty is separate. v0.1.0 does not run a product novelty search, so novelty is
reported as `not_assessed`.

## How a question becomes answerable—or is rejected

“Answerable” is not decided by the proposing model. After a family is visible:

- the **Question Owner** states what must remain scientifically true and judges
  whether proposed operationalizations still answer the intended question;
- the **Dataset Planner** inspects the target dataset and records concrete
  evidence about units, variables, joins, time structure, controls, hierarchy,
  limitations, and feasible diagnostics;
- typed messages bind every claim and decision to one family or variant;
- bounded revision may clarify a construct or change an operationalization;
  material scientific changes require a new question version and renewed
  literature/novelty review; and
- if the dataset cannot support the distinction the question requires, the
  correct result is an evidence-backed rejection, not a smaller trivial
  question.

Example: a family may ask whether a population geometry is stable across a
behavioral transition. If the dataset has the necessary population recordings
but cannot align the transition without circular selection, the planner can
reject the proposed operationalization. The dossier should show the promising
idea, the missing discriminating evidence, and what new data or method would be
needed.

## What is new and citable

For AI for Science, Maieusis defines a question-development problem with three
linked contributions:

1. **Explicit transfer of question-forming moves.** It reconstructs and reviews
   how prior papers transformed background, tension, and data opportunity into
   questions, then makes those moves reusable across new contexts.
2. **Pre-execution target-dataset answerability.** It separates imaginative
   proposal from exact target-dataset inspection and makes plan/revise/reject a
   first-class outcome before full analysis.
3. **A proof-carrying question-development funnel.** It preserves visible,
   digest-bound intermediate products, branch-local evidence, independent
   review, honest authority ceilings, and closure for accepted and rejected
   families.

These are problem-definition and system-design claims. They are not claims that
Maieusis automatically discovers true hypotheses, outperforms every prior
system, or replaces domain expertise.
