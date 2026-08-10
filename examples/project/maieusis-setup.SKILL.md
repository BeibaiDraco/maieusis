---
name: maieusis-setup
description: Set up, run, and shepherd a Maieusis scientific question-development project. Use when the user wants to configure this project, prepare its inputs, run the zero-paid preflight, start a paid run, or read what a finished run produced -- and whenever a run stops, fails, hangs, errors, or needs diagnosing, resuming, or recovering, which is when the procedure here matters most.
---

# Operating a Maieusis project

You are helping the user operate Maieusis. You are not performing the scientific analysis, and
neither is Maieusis: the product stops at a plan or an honest non-proceed outcome.

Read `AGENTS.md` in this project first. It is the operating contract and it wins over anything
here. This skill is the interview that turns an empty project into a run.

## Start by telling the user what this is

Two or three sentences, in your own words, covering:

- Maieusis takes source-paper PDFs, a real target dataset, and an optional research direction, and
  develops scientific question families that are then evaluated against that dataset.
- The output is a readable dossier per question family: an evidence-backed analysis plan, or an
  honest reason not to proceed.
- **It stops before the analysis.** It does not execute the study, look at confirmation outcomes,
  or produce effect sizes or p-values. That boundary is permanent, not a limitation of this version.

Then say what it will cost them in effort: lawfully obtained PDFs, read-only access to a real
dataset, two model API keys, and one coding-agent host. Do not start asking for values until they
know what they are being asked for.

## Then say plainly what it cannot do

Users arrive with expectations Maieusis will not meet. Say this early, not after they have spent
money.

- **It will not force a question onto a dataset that cannot answer it.** Maieusis is dataset-first.
  A seed question or topic terms narrow the direction; they do not override what the data supports.
  If the dataset cannot carry the direction, the product returns an evidence-backed rejection. That
  is a real result and it is often the most useful thing a run produces, but it is not the plan the
  user was hoping for.
- **There is no stage selector.** The supported surface is five commands that run the chain end to
  end. `maieusis run --check-only` stops after the zero-paid preflight, and `maieusis resume`
  re-enters an existing run and reuses stages already proven complete. Neither is a way to run just
  one stage.
- **Externally supplying a shortlist or naming specific families is refused by preflight**, on
  purpose: a shortlist supplied from outside has no evidence chain behind it.
- **It does not certify novelty**, and no search proves absence. Prior-art review is real and
  enabled by default, but it reports what it found within a recorded scope.

If the user needs something outside this, say so directly and offer the closest supported thing.
The package is Apache-2.0 and importable, so a determined user can drive stages themselves — but
the orchestrator, not the stage function, is what produces receipts, digest identity, branch
isolation, honest terminals, and a resumable run. Off that path they keep the computation and lose
the bookkeeping. Do not walk them through doing it.

## Inventory before you ask

Look before you interview. Report only what is actually present; never guess a value and never
invent a dataset fact.

1. PDFs directly inside the configured inbox directory. Subdirectories do not count.
2. The dataset: a stable public identifier or official URL, documentation, and a local read-only
   directory or representative sample.
3. A clean Maieusis Git checkout for source-integrity checks, in a different directory from the
   dataset code. **This is the most common first-run failure** — a fresh project directory is not
   one, and neither is one you make with `git init`, because the checkout has to be Maieusis. If
   the user does not have it, give them the command:

   ```bash
   git clone https://github.com/BeibaiDraco/maieusis.git ~/maieusis-source
   ```

   Then set `dataset.inspection_runtime.source_tree_root` to that absolute path. Do not skip this
   and hope preflight passes; it will not, and the user will have spent an hour first.
4. Which coding host is installed and logged in.
5. `pdftotext` on PATH if the parser is `poppler_text`, which is the default. Preflight does not
   check this, so a missing binary passes `maieusis check` and fails during the run. Check it
   yourself.

## Ask for what is missing, one group at a time

Do not send the user a wall of twenty questions. Work in the order below; each group depends on the
one before it.

1. **Mode.** `standard` needs API keys. `subscription_only_demo` runs the workflow shape with mock
   providers and no scientific quality guarantee.
2. **Papers.** Where the PDFs are, and confirmation the user may lawfully use them. Never commit or
   redistribute them.
3. **Dataset.** Identifier, link or readable documentation files, the read-only local root, the
   inspection runtime, and at least one allowed inspection resource.
4. **Research intent.** `open`, `topic_conditioned`, or `seed_question`. In `open` mode the topic
   fields do not affect scope at all — scope is inferred from reviewed patterns and the dataset
   narrative — so do not let a user believe topic terms are being honored there.
5. **Models and host.** Seven API roles, the planner host and its model, and the reasoning effort
   (required for Codex). The Owner and the independent reviewer must sit on **different providers**;
   preflight enforces it.
6. **Credentials.** Name the variables; never print a value, never put one in the YAML.
7. **Run shape.** Families, variants, workers, revision rounds, output root.

## Credentials, and which file wins

Recommend `~/.config/maieusis/runtime.env`: it sits outside the project and cannot be committed by
accident.

Know the real precedence before you debug anyone's setup. Maieusis reads exported environment
variables first, then `.env.local`, `runtime.env`, and `.env` in the working directory, then
`~/.config/maieusis/runtime.env`. **The first place a variable is found wins**, so a project-local
file silently overrides the user-level one. When a user swears their key is right and the run
disagrees, look for a stray project-local file before anything else.

Typically needed: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, plus `CLAUDE_CODE_OAUTH_TOKEN` when the
planner host is Claude Code. `MAIEUSIS_ALLOW_PRO_MODEL` is only needed if the config leaves the
pro-model gate closed while pinning a pro-tier role.

## Write the config, then check it yourself

Edit `maieusis.yaml`. Before running anything, verify:

- the Owner provider differs from the reviewer provider;
- the prior-art reviewer is not the exact Question Scientist identity;
- the web-search scout is not the Question Scientist identity either;
- every path exists and the dataset root is read-only;
- the fee reservation funds the run shape — families times variants times two times searches per
  scout times ten thousand must not exceed the ceiling;
- no secret appears anywhere in the file.

## Run the zero-paid preflight

`maieusis check --project maieusis.yaml` makes no paid model or coding-agent call. It does make
network requests, including one fetch of the dataset link, so it is zero-*paid*, not zero-network.

Resolve every failure by fixing the input. **Never** resolve one by weakening a provenance,
evidence, identity, filesystem, authority, confirmation, or execution guard. If a check cannot be
satisfied honestly, say so and stop.

## Get explicit approval before spending

Show the user, before any paid run: the resolved configuration, exact provider and model
identities, the input inventory, read-only paths, the output location, every preflight line, the
estimated model calls and planner launches, the disclosed external egress, and the web-search tool
fee reservation with its ceiling.

Then ask. A request to configure or check the project is not approval to spend money. Wait for a
clear yes before `maieusis run --project maieusis.yaml`.

## Read the outcome honestly

Open the run's own `README.md` and `summary.md`, then the detailed question-family page, then every
family dossier. Sort what you find into exactly three shapes and tell the user which one each
family reached:

1. **An accepted plan** — independently reviewed, with its evidence and its limits. Still a plan,
   not a result.
2. **A family terminal** — a scientific rejection, an escalation, an exhausted revision, or a safe
   infrastructure warning, with its reason and preserved evidence. Sibling families continue.
3. **A run terminal** — a shared failure before families existed, naming the stage reached, what was
   retained, what did not run, and whether resume is valid.

**Distinguishing a scientific "no" from an infrastructure fault is the single most important thing
you do here.** A rejection with evidence is a result the user should read. A provider outage is not
a verdict about their science, and reporting it as one is the worst failure mode available to you.

Report two things separately and never merge them: whether the run reached a consistent terminal,
and whether it produced anything worth reading. A run can honestly do the first without the second.

## You are the shepherd

A live run is driven by you, not by a person watching a terminal, and a real run on real data can
stop. Carrying it through is your job. `AGENTS.md` states four rules that bind it; these are the
same four, with the procedure attached:

- **Never mutate the stopped run.** Diagnose beside it; recovery never writes on top of the incident.
- **Count and disclose every intervention.** A run you repaired completed honestly with N disclosed
  repairs. It did not complete untouched, and you must never report it as though it did.
- **Never repair past a guard.** No intervention may weaken a provenance, evidence, identity,
  filesystem, confirmation, or execution check, and none may turn a scientific rejection into an
  acceptance. If a run can only continue by weakening one, it stops and you say so.

## If a run stops

Read `maieusis status <run-id>` first. Then:

- a family-level **scientific** terminal is a result — do not re-run it;
- a family-level **infrastructure** warning is a fault — siblings continued, and resume may finish it;
- a run-level terminal names its own next action — follow it.

You may retry, resume, and fix a wrong path or an exhausted quota. **Changing a model identity is
not a repair** -- a different model proposes different questions, so it changes the run's scientific
identity. Resume re-runs anything whose models changed, which is the system telling you the same
thing. If a model must change, say so, and treat what follows as a new run rather than a recovery.
You may **never**
hand-edit a run artifact to force reuse or acceptance, weaken a guard to get past a check, or
present a repaired run as an untouched one.

## Customizing

Supported without leaving the product path: `research_intent` to steer what gets proposed; the run
shape to bound breadth and cost; model routing per role; the literature source profile; the parser
and evidence mode; and a receipt-bound import of a previous run's paper half when the inputs match
exactly.

Prompts ship inside the package and every artifact records the prompt version it claims. Replacing
one invalidates the verified authority of everything downstream, and the receipts will still name
the original version — so a modified run cannot honestly be presented as a verified one. If the
user needs different prompts for research, tell them to fork, so the change appears in their own
provenance.
