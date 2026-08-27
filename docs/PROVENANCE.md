# Provenance and scientific authority

[Documentation home](INDEX.md) · [Architecture](ARCHITECTURE.md)

Maieusis treats provenance as application state. A reusable scientific product
is tied to the inputs, source evidence, models, prompts, review, implementation,
and content identity that produced it. This makes a dossier inspectable; it
does not make the dossier true.

It also does not make the run repeatable. Everything below pins what went *in* — which bytes, which
prompt version, which model at which effort. The model's output is not pinned, there is no seed, and
two runs of one unchanged profile can propose different questions. [What a reproduction does and
does not mean](LIMITATIONS.md#running-the-same-configuration-twice-does-not-reproduce-the-same-questions)
sets out how far apart two such runs have actually been measured to fall.

## What Maieusis records

Depending on the stage and artifact, a local run records:

- source-paper filenames, bibliographic identities, and content hashes;
- source spans and citation context used by PaperCases and formation traces;
- dataset identity, links, local source documents, and read-only inspection
  surfaces;
- research intent and the separated context shown to the Question Scientist;
- prompt family and version;
- provider and model identities for generation and review;
- input and output digests;
- stage-completion and resume receipts;
- review decisions and earned authority;
- family, variant, branch, and dialogue scope;
- Dataset Planner invocation records and validated inspection evidence;
- final family outcomes; and
- the current paths and hashes of run products.

Provider conversation or request IDs may help diagnose a local run, but they
are not the scientific source of truth. Persisted, validated artifacts and
their evidence relationships are authoritative for what Maieusis claims to
have produced.

## Source-backed does not mean correct

Provenance answers questions such as:

- Which paper span supports this reconstruction?
- Which current-literature record motivated this claim?
- Which dataset document or bounded inspection supports this planning fact?
- Which model generated the artifact, and which independent model reviewed it?
- Did a later stage consume the same bytes that were reviewed?

It does not answer:

- Is the scientific interpretation true?
- Is the question important or novel?
- Is the planned analysis adequately powered?
- Will executing the plan produce a positive result?

Those require scientific judgment and, eventually, empirical analysis outside
the v0.1.1 product boundary.

## Authority is earned, not renamed

Artifacts may be independently reviewed, provisional, unknown, degraded, or
unavailable. Incomplete but source-bound evidence can remain visible without
being promoted. A downstream family or dossier cannot receive greater
authority than the evidence on which it depends.

Common interpretations are:

| Label or condition | Meaning |
| --- | --- |
| Reviewed / verified route | The required source, identity, validation, and independent-review checks passed |
| Provisional | Useful source-bound material is present, but one or more evidence or review conditions limit authority |
| Degraded | A recoverable limitation reduced the completeness or reliability of the available surface |
| Warning | The family closed readably after a provider or validation problem; inspect the warning before use |
| Rejected or deferred | The scientific or dataset-planning branch found a reason not to proceed now |
| Unavailable / incomplete | A required trustworthy product could not be established |

An accepted plan is still not a scientific result. A visible artifact is
discoverable, not necessarily correct.

## Branch-local evidence

Each shortlisted family has an isolated planning branch. Family-scoped evidence
may support variants within that family; variant-scoped evidence may support
only its named variant. Evidence from one family cannot silently justify
another.

The Question Owner cannot certify dataset facts from model knowledge. Dataset
claims need validated Dataset Planner evidence. Conversely, the planner cannot
silently redefine the scientific question: material changes require explicit
versioning, Owner approval, and renewed literature and novelty review.

## Independent review

The standard path uses a Question Owner and independent reviewer from different
providers. Provider separation reduces shared generation context and
self-approval, while session and artifact identities prevent a generator from
being presented as its own reviewer.

Independence is procedural evidence, not a human or empirical guarantee. Read
the review findings and the plan, not only the final disposition.

## Resume and PaperBank reuse

`maieusis status <run-id>` recomputes current input and configuration identity
and reports what a resume would reuse or repeat. It is read-only.

`maieusis resume <run-id>` reuses a stage only when its receipt, inputs,
configuration, implementation, prompt and model identities, and output hashes
still validate. The resume decision is written before new scientific work
begins.

Optional PaperBank reuse applies the same principle to paper-derived products.
It verifies the current PDF filename/hash set, parser, prompts, models,
configuration, source receipt, and imported product hashes. It does not import
dataset context, current topic evidence, QuestionFamilies, planning branches,
dossiers, source PDFs, or raw model traffic.

## Readable pages and audit files

The run `README.md`, `summary.md`, detailed question-family page, and family
dossiers are the main human reading surfaces. Manifests, receipts, stage
outputs, and hidden audit files support integrity, diagnosis, and safe resume.
They should not be substituted for the scientific narrative or published with
credentials, restricted data, or raw provider traffic.

The four public examples -- the climate demonstration, two International Brain Laboratory (IBL)
Brain-Wide Map runs of the same recordings with and without a declared topic anchor, and the Neural
Latents Benchmark (NLB) MC_Maze-S demonstration -- contain curated readable scientific
products and sanitized inventories. They omit source PDFs, datasets,
credentials, raw model traffic, provider session IDs, absolute local paths,
hidden local audit files, and reviewer improvement notes addressed to the
development team. Each demonstration's manifest lists the curation steps applied. Curation cannot increase the authority of an
outcome; warnings and non-accepted families remain labeled as such.

## A practical reading checklist

Before relying on a dossier as a candidate plan, ask:

1. Are the relevant source and dataset claims linked to evidence?
2. What is the authority ceiling of the PaperBank, literature, and dataset
   context?
3. Did the Dataset Planner inspect the facts needed by this variant?
4. Did the Owner accept the operational meaning without changing the question?
5. What did the independent reviewer challenge?
6. Is the outcome accepted, provisional, rejected, deferred, or warning-only?
7. What does the claim ceiling explicitly forbid?

Then read [limitations](LIMITATIONS.md). Provenance makes uncertainty visible;
it does not remove it.

---

[Documentation home](INDEX.md) · [Inputs and outputs](INPUTS_AND_OUTPUTS.md) ·
[Architecture](ARCHITECTURE.md) · [Limitations](LIMITATIONS.md)
