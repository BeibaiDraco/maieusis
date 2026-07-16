# Provenance and audit model

Maieusis treats provenance as application state, not as a paragraph added at
the end. Every reusable scientific product is tied to the inputs, prompt,
provider/model, implementation, review, and content digests that produced it.

## What is recorded

- source-paper identities and content hashes;
- prompt family and version;
- provider and model IDs for generation and review;
- input and output digests;
- stage and resume receipts;
- review decisions and earned authority;
- branch, family, and variant scope;
- planner run records and validated inspection evidence;
- final branch outcomes; and
- run-manifest paths and hashes for current products.

Provider-owned conversation IDs are not authoritative state. A run can be
understood from its persisted, typed artifacts and receipts.

## Authority is earned, not renamed

An artifact can be verified/agent-reviewed, provisional, unknown, degraded, or
unavailable. Incomplete source evidence can remain visible and useful without
being promoted. Downstream families and dossiers cannot exceed the authority
ceiling of the context that supports them.

The visible product index means “discoverable,” not “true.” Independent review
means a separate review process with recorded model/provider identity; it is
still not a human or empirical guarantee.

## Resume and PaperBank reuse

`maieusis status` recomputes input/configuration identity and explains what a
resume would reuse. `maieusis resume` writes its decision receipt before work
begins and reuses only stages whose receipts, inputs, versions, providers,
models, and output hashes still validate.

A receipt-bound PaperBank import may reuse only paper-half products after
verifying the current PDF name/hash set, parser, prompts, implementation,
models, configuration digest, source receipt, and every imported output hash.
It does not import dataset context, topic evidence, QuestionFamilies, planner
branches, dossiers, raw captures, or source PDFs. The new run records the
source run identity and receipt/output digests without persisting an absolute
source path.

## Public demo audit subset

The v0.1.0 public demos are curated from one sealed, zero-resume IBL →
receipt-bound NLB validation pair. Detailed presentation pages were rendered
deterministically from copies of those roots after scientific finalization;
the paid scientific pair was not reexecuted and its compact products and
receipts were not changed. Start at the [question gallery](../demos/QUESTIONS.md)
and follow links to each demo's readable artifact tree.

Public demos retain only the information needed to inspect the scientific
question-development path and understand the reproduction binding:

- provider/model IDs and prompt versions;
- input and output hashes;
- review decisions and branch outcomes; and
- stage, resume, or reuse receipts after sanitization.

They exclude raw API captures, API logs, provider session IDs, absolute paths,
secrets, complete hidden audit sidecars, source PDFs, full text, and long source
excerpts. The NLB warning family remains visibly provisional/degraded and has
no accepted-plan authority; curation does not promote that outcome.
