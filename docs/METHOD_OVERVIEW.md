# Method overview

[Documentation home](INDEX.md)

Maieusis develops candidate scientific questions into dataset-grounded
analysis plans or explicit non-proceed outcomes. It works upstream of analysis
execution: the product is a question-development dossier, not a scientific
result.

## The method in one minute

1. **Reconstruct published question-forming moves.** Each source paper becomes
   a PaperCase. Source spans and relevant citation context support an
   evidence-bound formation trace: published background → unresolved tension →
   data opportunity → inferential move → question → possible scientific
   consequence. This is a reconstruction of the published record, not a claim
   about an author's private thought process.
2. **Abstract moves that can transfer.** Independently reviewed traces across
   papers are compared to induce reusable question-forming patterns. The
   pattern captures a transformation, not a copied question, result, or
   conclusion.
3. **Propose with separated context.** The Question Scientist receives four
   distinct inputs: PaperBank patterns, current topic literature, a coarse
   DatasetNarrative, and the user's research intent. It renders visible
   QuestionFamilies with scientifically different variants.
4. **Inspect the real dataset after proposal.** Each shortlisted family enters
   an isolated branch. A Question Owner protects scientific meaning while a
   Dataset Planner inspects real documentation, code, metadata, and bounded
   samples. The branch may plan, revise, reject, defer, or close with an honest
   warning.
5. **Review before closure.** An independent reviewer checks intent
   preservation, dataset grounding, competing explanations, controls,
   overclaim, and material revision. Maieusis then renders the user-facing
   dossier and retains the provenance needed to audit it.

## DatasetNarrative: useful context without premature certainty

The DatasetNarrative is a coarse, source-backed account of what the target
dataset broadly contains and why it may be relevant. It is built from official
links, readable documentation, metadata, and bounded source packets.

It is deliberately not a complete schema, coverage guarantee, or feasibility
certificate. Giving the proposing model every exact variable and joint
coverage fact would bias question generation toward what looks easiest in the
current tables. Exact units, joins, events, hierarchy, missingness, controls,
and estimability are inspected later inside the isolated planning branch.

Every narrative claim retains its source identity. Missing or weak support
lowers the authority ceiling rather than being filled with plausible prose.

## PaperBank: learn the move, not the result

For each source paper, Maieusis:

1. parses the PDF into source-addressable spans;
2. extracts a PaperCase whose claims point back to those spans;
3. identifies cited works that contributed to the published question framing,
   using local citation context and available bibliographic or abstract
   evidence;
4. drafts a formation trace separating background, tension, data opportunity,
   inferential move, resulting question, and scientific stakes;
5. submits that trace to an independent reviewer; and
6. induces and independently reviews patterns across accepted traces.

A pattern summarizes a recurring move across source-bound cases. It does not
claim that papers used identical wording, that every cited work was available
in full text, or that an inferred move reflects private author intent. Paper
identity, supporting spans, citations, review status, model identity, and
content hashes remain part of the record.

## Current literature is separate from PaperBank

PaperBank provides historical examples of question formation. Topic-literature
retrieval instead describes the current field context around the user's
research direction. Keeping them separate prevents a historical example from
being mistaken for the present state of evidence.

The default route uses public scholarly metadata and can enrich records with
lawful open full text. Incomplete evidence may still be useful, but its limits
remain explicit:

- source-backed, independently reviewed material can support the verified
  route;
- incomplete but source-bound material may support provisional inspiration;
- title-only, metadata-only, diagnostic-only, blocked, or fabricated material
  cannot be renamed as verified evidence; and
- a family, plan, or dossier cannot outrank the evidence that supports it.

Novelty is a separate question. Maieusis v0.1.0 does not perform a product
novelty search, so novelty is reported as `not_assessed`.

## From a proposed question to a plan—or a reason not to proceed

The proposing model does not certify answerability. After a family is visible:

- the **Question Owner** states what must remain scientifically true and judges
  whether an operationalization still addresses the intended question;
- the **Dataset Planner** inspects target-dataset evidence about units,
  variables, joins, time structure, controls, hierarchy, limitations, and
  feasible diagnostics;
- every dialogue turn and evidence item is scoped to one family or variant;
- bounded revision may clarify a construct or change an operationalization;
- a material scientific change requires a new question version and renewed
  literature and novelty review; because v0.1.0 has no product novelty-search
  route, it must defer rather than accept a materially changed question; and
- when the dataset cannot support the distinction a question requires, the
  correct outcome is an evidence-backed rejection or deferment, not a smaller
  trivial question presented as equivalent.

For example, a family may ask whether a measured relationship remains stable
across a scientifically meaningful transition. If observations exist but the
transition cannot be aligned without circular selection, the planner should
not claim the question is answerable. The dossier can preserve the promising
idea, explain the missing discriminating evidence, and state what new data or
method would be needed.

## What the independent reviewer checks

Owner acceptance is not enough. The reviewer examines:

- whether the refined question preserves the original scientific intent;
- whether dataset claims are supported by branch-local inspection evidence;
- whether competing explanations and controls are adequate;
- whether the claim ceiling matches the design;
- whether a revision changed the scientific question materially; and
- whether the plan stays on the planning side of the execution boundary.

Independent AI review reduces self-approval; it does not establish truth or
replace domain expertise.

## The problem definition and system contribution

For AI for Science, Maieusis links three system-design ideas:

1. **Explicit transfer of question-forming moves.** It reconstructs and reviews
   how published background, tension, and data opportunity connect to a
   scientific question, then makes that move reusable across contexts.
2. **Pre-execution target-dataset planning.** It separates imaginative proposal
   from exact target-dataset inspection and makes plan, revise, reject, defer,
   and warning first-class outcomes before analysis.
3. **An inspectable question-development funnel.** It preserves visible
   intermediate products, source and evidence lineage, isolated branches,
   independent review, honest authority ceilings, and readable closure for
   successful and unsuccessful families.

These are problem-definition and system-design claims. They are not claims
that Maieusis automatically discovers true or important hypotheses,
outperforms every prior system, or replaces scientific judgment.

Next, read [architecture and trust boundaries](ARCHITECTURE.md), inspect the
[demo question gallery](../demos/QUESTIONS.md), or follow the
[installation guide](INSTALLATION.md).

---

[Documentation home](INDEX.md) · [Architecture](ARCHITECTURE.md) ·
[Provenance](PROVENANCE.md) · [Limitations](LIMITATIONS.md)
