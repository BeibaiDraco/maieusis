# When a run stops: reading outcomes honestly

[Documentation home](INDEX.md) · [Inputs and outputs](INPUTS_AND_OUTPUTS.md) ·
[Troubleshooting](TROUBLESHOOTING.md)

A real run on a real dataset can stop. Providers rate-limit, accounts exhaust, a paper turns out to
be unreadable, a dataset lacks a construct a question needed. That is expected, not exceptional.

What matters is that you can always tell **which kind** of stop you are looking at. This page is
about that distinction, because getting it wrong is the most damaging mistake available to a reader
of these outputs.

## This page, and the shepherd contract

This page is for reading a run that stopped: what the outcome means and what to do next. The rules
the driving agent works under — what it may repair, what it must record, and what repair may never
reach — are on [shepherd mode](SHEPHERD_MODE.md).

## The shepherd is part of the system, not a patch on it

Maieusis is agent-operated: a live run is driven by a coding-agent session, not by a person watching
a terminal. That session is the run's **shepherd**, and carrying the run through failure is one of
its jobs — a designed one, not an emergency measure.

This matters for how you read a run that needed help. A stopped family that was diagnosed and
resumed is not a damaged run or a lesser result. It is the system doing what it was built to do. The
backstop exists because real data and real services misbehave, and a design that pretends otherwise
just fails you at hour two.

What the shepherd owes you is not an unblemished run. It is a run whose history you can see: what
stopped, what it did about it, and what that leaves the results able to support.

### What bounded repair means in practice

- Recovery re-enters the same run rather than starting a new one, and replaces only what it
  re-runs: a resumed stage rewrites its own receipt and the run's `summary.md`, while stages it
  reuses are left untouched. What is never rewritten is the reasoning — no intervention may edit a
  dossier, a disposition, or an evidence record to make a run read better than it went.
- Every intervention is recorded. Not as an apology — as part of the run's provenance, the same way
  a lab notebook records a re-pipetted sample. Be precise about what "recorded" means here: a resume
  writes its own receipt under `runs/<id>/receipts/` before it acts, and you can read it. A retry, a
  corrected path, or a cleared quota leaves no machine trace, so it reaches you only because your
  shepherd tells you. That part is a promise rather than a receipt — ask for it if it is missing.
- No repair may weaken a provenance, evidence, identity, filesystem, confirmation, or execution
  check, and none may turn a scientific rejection into an acceptance. **This is the line.** Repair
  gets a run past infrastructure, never past a scientific verdict.
- The shepherd reports two verdicts, never one — which is the rest of this page.

The IBL demonstration carries a visible example: its reader pages were produced by a
zero-provider-call resume of the same run on a later build, so that demonstration has two build
identities. Its manifest says so rather than presenting a single clean lineage.

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

Neither is a review budget running out. A reviewer that keeps asking for a change has not decided
anything yet, so a stop of that kind is labelled as a fault rather than a finding, resuming is valid,
and the lever is `run.max_revise_rounds` in your project file. A `reject` is the opposite: it is the
reviewer's decision, and raising a budget will not change it.

Maieusis labels these differently on purpose, and a family terminal states which one it is. If you
are reading a summary that presents an infrastructure fault as a scientific finding, that summary
is wrong, and you should open the family's own page rather than trust it.

## Where the run id and the summary are

Every command that follows takes a `<run-id>`, and nothing so far has said where you get one.

It is the **name of the directory** the run created under your `run.output_root` — a timestamp and
a short hash, like `20260823T124544Z-1acbc808`. `maieusis run` prints it on the last line when it
finishes, as part of the path to the summary, and it is printed again by every `resume`. If you
lost the output, list the directory: the run ids are the directory names, and the newest is the one
you just ran.

`summary.md` sits at the top of that directory and is the page to open first. It is the run
narrating itself: which stages ran, which families it produced, what happened to each, and the
terminal it reached. `README.md` beside it is the reader-facing index into the artifacts. Neither
is generated for a run that never got past preflight, and their absence is itself a diagnosis.

## What to do when a run stops

1. Run `maieusis status <run-id>`. It reports what each stage did and whether resuming is valid,
   and makes no paid call. It is read-only except on a run whose indexed artifacts no longer match
   their digests, where it records that integrity failure rather than reporting a healthy run.
2. Read the run's own `summary.md` first, then `README.md`, then the per-family pages.
3. Then act on what kind of stop it was:
   - **a family-level scientific terminal** is a result — do not re-run it;
   - **a family-level infrastructure warning** is a fault, and what `resume` does with it depends
     on which of the two the run wrote. A family that kept a readable dossier — the page says
     *completed with a family-level warning* — is a finished terminal to `resume`: it is reused,
     not re-run, because a dossier the reader can already open is not something to spend money
     replacing. A family the run could not finish at all — *run incomplete, an infrastructure issue
     and not a scientific rejection* — has no completion record, and that is the one `resume`
     re-enters. Read which sentence the page carries before deciding whether resuming will change
     anything;
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
