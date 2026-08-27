# Shepherd mode: the contract a run is driven under

[Documentation home](INDEX.md) · [When a run stops](RUN_SUPERVISION.md) ·
[Agent-guided setup](AGENT_GUIDED_SETUP.md)

Maieusis is agent-operated. A live run is driven by a coding-agent session in your own terminal —
your Codex or Claude Code — not by a person watching one and not by a service we operate. That
session is the run's **shepherd**, and carrying a run through failure is one of its jobs. Four rules
bound what it may do while it does that, and they are not negotiable: it may **never write on top of
a stopped run**, never **intervene without recording it**, never **carry a run past a scientific
verdict**, and never **repair past a guard**.

Nothing on this page requires you to have installed anything. The contract below is not a
description of a contract: it is the text `maieusis init` writes into your project as `AGENTS.md`,
which your coding agent reads before it touches your data or spends your money. You can read it
first, and decide against it, at no cost.

## This page, and "When a run stops"

Two pages, two readers, no overlap.

- **This page is the operator-facing contract.** What the shepherd may do, what it must record, what
  it must refuse, and what the system enforces mechanically as against what it takes on the agent's
  word. Read it before a run — or when you are deciding whether a specific repair is permitted.
- **[When a run stops](RUN_SUPERVISION.md) is the outcome-facing guide.** How to read a run that
  ended early: the two verdicts, the three honest terminal shapes, and how to tell a scientific
  rejection from an infrastructure fault. Read it after a run.

If you are holding a stopped run and want to know what it means, start there and come back here only
if you need to know whether a particular repair is permitted.

## Why a coding agent drives the run at all

A run against a real dataset is not a pipeline that either completes or does not. Papers fail to
parse. A provider rate-limits at hour two. A dataset turns out not to carry the field a question
needed. A model returns something malformed on the one call that mattered. None of this is
exceptional; it is what real data and real services do.

A rigid pipeline answers by ending the run, and you get nothing — an hour of paid calls and no
dossier, because one unreadable PDF was not anticipated in code written a year earlier.

Most flexible systems answer the other way: they absorb the problem. Retry quietly, substitute a
default, degrade a little, keep going. You get output, and you cannot audit it, because the record
no longer distinguishes what was planned from what was patched. For a scientific artifact that is
the worse failure, and it is not the one that looks worse at the time.

Maieusis takes the third option. **A coding agent drives the run, because judgment is exactly what
these situations need** — whether a stop is a fault or a finding is not a call a retry policy can
make — and that agent works under a written contract about what its judgment may reach. It can
diagnose a stop and resume what is safe to resume. It cannot write over the run that stopped, it
cannot repair past a guard, and it cannot turn a scientific rejection into an acceptance.

Flexibility is why you put an agent in the driver's seat; the ledger is what makes the flexibility
worth trusting. Half of that ledger is a receipt and half is the shepherd's word, and the section
that draws the line is below.

**Two agent roles, not one.** The shepherd drives the run from outside it. The Dataset Planner is a
different, isolated coding agent that the orchestrator launches inside one question family's branch,
with read-only access to permitted dataset surfaces. A shepherd never impersonates a planner or
launches that role by hand; [architecture](ARCHITECTURE.md) covers the separation.

## The four rules

Quoted exactly as they appear in the `AGENTS.md` that `maieusis init` writes into your project,
under the heading **Your role**:

> **You are also the run's shepherd.** A run against real data can stop -- a provider rate-limits, a
> paper will not parse, a service returns something malformed. Carrying the run through that is a
> designed part of your job, not an emergency. It is why an agent drives the run instead of a fixed
> pipeline: the situations need judgment. Four rules bound that judgment, and they are not
> negotiable:
>
> 1. **Never write on top of a stopped run.** Preserve it and work beside it, so its history stays
>    readable.
> 2. **Record every intervention.** Not as an apology -- as provenance. A run you helped completed
>    honestly with that help disclosed; it did not complete untouched, and you must never report it
>    as though it did.
> 3. **Repair carries a run past infrastructure, never past a scientific verdict.** A family the
>    evidence rejected stays rejected. No retry, resume, or configuration change may turn a rejection
>    into an acceptance.
> 4. **Never repair past a guard.** If a run can only continue by weakening a provenance, evidence,
>    identity, authority, source-tree, branch-isolation, filesystem, confirmation, or execution check,
>    it stops and you say so. Treat that list as illustrative, not exhaustive: a check you can only
>    pass by loosening it is a check you stop at, whether or not it is named here.

### What each rule prevents, and what happens if it is broken

**Rule 1 — never write on top of a stopped run.** Every stage records the digests of its inputs and
outputs. A hand-edited artifact does not become a better artifact; it becomes one whose receipt is a
false statement about it. Where a digest covers the edited bytes, `maieusis status` and
`maieusis resume` refuse to reuse that stage and the work is lost anyway. Where the edit lands
somewhere no digest covers, the run keeps rendering readable pages while its provenance has quietly
stopped being true — and a dossier whose records were edited can no longer support the claims it
makes.

**Rule 2 — record every intervention.** The system can only record what the system did; there is no
later pass that reconstructs the rest. An undisclosed retry is not a small omission, because the
next reader has no way to tell a run that went straight through from one that needed four attempts
to get past a malformed reply.

**Rule 3 — never past a scientific verdict.** Part of this is machine-enforced. Once a stage carries
a scientific terminal, resume marks every downstream stage `terminal_not_applicable` with the reason
`upstream_scientific_terminal` and does not run it, and a family whose completion record shows a
scientific terminal is reused rather than re-run. The barrier does not reach the input end of the
run, which is why the fourth decision below exists.

**Rule 4 — never repair past a guard.** The guards fail closed by design; a run that can only
continue by loosening one is a run that stops. The list in the rule is illustrative on purpose. The
test is not whether a check appears in it, but whether you would have to make the check weaker to
pass it.

## The four decisions the rules leave open

The same file settles four questions the rules do not, so that a shepherd is not deciding them
under pressure at hour two. Quoted exactly:

> Four things the rules above leave open, decided here so you do not have to decide them at hour two:
>
> - **`resume` spends money, so it needs the user's approval too.** The approval you got covers the
>   run you started, not an open-ended right to keep paying. Say what stopped, what a resume would
>   re-run, and ask.
> - **Two resumes, then stop and ask.** Bounded means bounded. If a run needs a third, the problem is
>   not transient and the user should decide whether to keep paying.
> - **`resume` is the sanctioned way to write into a stopped run.** Rule 1 forbids *you* editing its
>   files by hand; it does not forbid the orchestrator's own recovery path, which records its decision
>   before it acts.
> - **Do not restage a rejected question as a new run.** Narrowing `research_intent` toward a family
>   the evidence closed produces a fresh evidence chain for a question that already has an answer.
>   That is the rejection being laundered, and it is the one way around rule 3. If the user wants to
>   pursue it anyway, say plainly that the earlier rejection stands and this is a new question.

The fourth is the one to read twice, because it is the only one of the four that is a
scientific-integrity rule rather than an operational one, and because it describes something that
would otherwise look entirely legitimate. A rejected family cannot be resumed into an acceptance —
the machinery above stops that. But a *new* run, aimed by a narrowed `research_intent` at the
question that was just closed, is a fresh run with a clean evidence chain and no memory of the
verdict. Nothing in the software prevents it. It is your rejection, and you may pursue the question
anyway; what you may not do is present the second run as though the first had not happened.

## Recorded by the machine, or reported on your shepherd's word

The distinction matters more than any single rule, because it tells you which parts of a run's
history you can verify and which parts you are trusting someone for.

**Recorded by the machine.** A resume writes its own receipt to
`runs/<id>/receipts/resume-<n>.yaml` **before it acts**, so the decision exists whether or not the
resume then succeeds. The record is a fixed shape:

| Field | What it holds |
| --- | --- |
| `run_id` | the run this resume re-entered |
| `resume_index` | which resume this was — the `<n>`, counted from the receipts already on disk |
| `created_at` | when the decision was made |
| `config_digest` | whole-configuration digest at decision time (informational; per-stage drift is decided by the per-stage slices) |
| `stage_decisions` | one entry per stage, in stage order |
| `family_decisions` | one entry per shortlisted family |
| `presentation_decision` | whether the reader pages were reused or redrawn, and why |

Each stage entry carries the stage name, the decision (`reuse`, `run`, or `terminal_not_applicable`),
the reason it was made, the prior receipt's status, which input keys changed, the recorded and the
current input digests, and the output paths whose digests were verified. Each family entry carries
the family identifier and slug, its decision, its reason, and the status found on disk. So "this
stage was reused" is not a claim you have to take: the receipt names the digests it was checked
against.

The run's own `summary.md` also states it in plain words, for example
`This run was resumed: 6 stage(s) reused, 2 stage(s) re-run.` — followed, where it applies, by a note
that some downstream stages "were not applicable after a reused scientific terminal".

**Reported on your shepherd's word.** Everything else. The contract is explicit about it:

> **Where the record lives.** A resume writes its own receipt under `runs/<id>/receipts/`. Everything
> else you do -- a retry, a fixed path, a cleared quota -- has no machine record, so it exists only if
> you tell the user. Put it in your final report in plain words: what stopped, what you did, how many
> times. A ledger nobody wrote is not a ledger.

Treat that as a promise rather than a receipt, and hold your shepherd to it. If a final report does
not say what stopped and what was done about it, the correct response is to ask, not to assume the
run went straight through.

## When the repair you want is forbidden

A prohibition with no sanctioned path is a prohibition that gets routed around. Each of these has
one.

| The situation | The sanctioned path |
| --- | --- |
| An infrastructure fault stopped the run | `maieusis status <run-id>` first — it makes no paid call — then `maieusis resume <run-id>` with your approval, at most twice. `status` is read-only **except** on a run whose indexed artifacts no longer match their recorded digests: there it records the integrity failure, marks the run failed, and writes an interruption summary, rather than reporting a healthy run over mutated bytes. That is the one case where looking changes something, and it is the case where you would want it to |
| A family closed for a scientific reason | Nothing. It is finished, not broken. Do not resume it |
| The run would only continue by weakening a check | It stops, and your shepherd says so. That is the correct outcome, not a failure to try hard enough |
| A model needs to change | Not a repair. `resume` re-runs anything whose models changed, and what follows is a new run rather than a recovery |
| You disagree with a rejection | Pursue the question, and say that the earlier rejection stands and this is a new question. Do not aim a narrowed `research_intent` at it and present the result as a first answer |

On the model case, the setup skill your project also receives puts it directly:

> **Changing a model identity is not a repair** -- a different model proposes different questions, so
> it changes the run's scientific identity. Resume re-runs anything whose models changed, which is the
> system telling you the same thing.

## A run that used shepherding is not a lesser run

Shepherding is a designed part of the system, not a fallback bolted on after the first bad night. A
stopped family that was diagnosed and resumed is not damaged goods; the backstop exists because real
data and real services misbehave, and a design that pretends otherwise fails you at hour two.

The published IBL demonstration was finished this way, and publishes that fact rather than a single
clean lineage. Its manifest records:

> The reader pages were produced by a zero-provider-call same-run resume on a later build, so this
> demo has two build identities.

What a shepherd owes you is not an unblemished run. It is a run whose history you can see.

## What this page does not promise

The machine-enforced parts are named above and only those: the digest and receipt checks, the
fail-closed guards, and the terminal barrier that stops a resume from carrying a run past a
scientific verdict. The rest is a contract that your coding-agent session is instructed to follow,
written into your project where you can read it and hold that session to it. That is exactly why the
record-versus-word distinction is on this page rather than buried: an honest description of shepherd
mode has to say which half of the ledger is a receipt.

Maieusis also does not decide the science. A repaired run that reached an independently reviewed
plan has produced a plan, not a result, and the scientific judgment still stays with you.

---

[Documentation home](INDEX.md) · [When a run stops](RUN_SUPERVISION.md) ·
[Provenance](PROVENANCE.md) · [Reading the labels](LABELS.md) ·
[Limitations](LIMITATIONS.md)
