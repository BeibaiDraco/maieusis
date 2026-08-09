# When a run stops: reading outcomes honestly

[Documentation home](INDEX.md) · [Inputs and outputs](INPUTS_AND_OUTPUTS.md) ·
[Troubleshooting](TROUBLESHOOTING.md)

A real run on a real dataset can stop. Providers rate-limit, accounts exhaust, a paper turns out to
be unreadable, a dataset lacks a construct a question needed. That is expected, not exceptional.

What matters is that you can always tell **which kind** of stop you are looking at. This page is
about that distinction, because getting it wrong is the most damaging mistake available to a reader
of these outputs.

## The two questions, never merged into one

Ask them separately, and expect separate answers:

1. **Did the run reach a consistent end state?** Did it stop somewhere it could describe, leaving
   enough behind to audit what happened?
2. **Did it produce anything worth reading?** Are there dossiers, and do they carry real scientific
   content?

A run can honestly answer yes to the first and no to the second. A run that reaches an honest
terminal with no families is a correct outcome and a disappointing one, and it should be reported
as both. Collapsing the two into a single word — "success", "failed" — destroys the information you
most need.

## Three honest terminal shapes

When the product can catch an outcome, it takes exactly one of these shapes. Every one of them is a
real product output, not an error path.

### 1. An accepted plan dossier

An analysis plan that passed independent review, with its evidence, its assumptions, and its
limits. It is a plan, not a result. Nothing has been executed and no effect has been measured.

### 2. A family terminal

One question family ended without a plan, and says why. This covers an evidence-backed scientific
rejection, an escalation, a revision budget that ran out, and a safe infrastructure warning. It
carries its reason, the evidence behind it, and the next action.

Sibling families continue. One family's failure does not cost the others their dossiers.

### 3. A run terminal

The run stopped before question families existed. It names the stage it reached, the finite class
of what went wrong, what partial work was retained, what never ran, whether resuming is valid, and
the exact next action. It never invents a family or a scientific verdict to fill the gap.

## Telling a scientific "no" from a fault

**This is the distinction that matters most.** An evidence-backed rejection is a result you should
read: the system looked at your dataset and your question and found a specific reason the question
cannot be answered responsibly with that data. That is often the most useful thing a run produces.

A provider outage, an exhausted account, or an unreadable file is not a verdict about your science.

Maieusis labels these differently on purpose, and a family terminal states which one it is. If you
are reading a summary that presents an infrastructure fault as a scientific finding, that summary
is wrong, and you should open the family's own page rather than trust it.

## What to do when a run stops

1. Run `maieusis status <run-id>`. It reports what each stage did and whether resuming is valid,
   without making any paid call.
2. Read the run's own `README.md` and `summary.md`, then the per-family pages.
3. Then act on what kind of stop it was:
   - **a family-level scientific terminal** is a result — do not re-run it;
   - **a family-level infrastructure warning** is a fault — siblings continued, and
     `maieusis resume <run-id>` may finish it;
   - **a run-level terminal** names its own next action — follow that.

`maieusis resume` re-enters an existing run and reuses the stages already proven complete with
identical inputs. It is not a way to run one stage in isolation, and it will re-run anything whose
inputs, configuration, prompts, or models have changed.

## What must never be done to a stopped run

Do not hand-edit a run artifact to force reuse or acceptance. Do not weaken a provenance, evidence,
identity, filesystem, confirmation, or execution check to get past a failure. Do not present a run
that needed intervention as one that completed untouched.

These are not stylistic preferences. Every artifact carries the identity of what produced it, and a
run whose records have been edited can no longer support the claims its own dossiers make.

## What this page does not promise

An independently reviewed plan is not a scientific result, and agreement between models is not
truth. Maieusis does not certify novelty, importance, or publishability, and it does not execute
the analysis or access confirmation outcomes. A stopped run handled well still leaves the
scientific judgment with you.

---

[Documentation home](INDEX.md) · [Method overview](METHOD_OVERVIEW.md) ·
[Limitations](LIMITATIONS.md)
