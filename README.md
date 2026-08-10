# Maieusis

[![PyPI package version](https://img.shields.io/pypi/v/maieusis.svg)](https://pypi.org/project/maieusis/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/maieusis.svg)](https://pypi.org/project/maieusis/)
[![GitHub Actions test status](https://github.com/BeibaiDraco/maieusis/actions/workflows/tests.yml/badge.svg?branch=main&event=push)](https://github.com/BeibaiDraco/maieusis/actions/workflows/tests.yml)
[![Zenodo DOI for Maieusis](https://zenodo.org/badge/DOI/10.5281/zenodo.21388805.svg)](https://doi.org/10.5281/zenodo.21388805)
[![License: Apache-2.0](https://img.shields.io/pypi/l/maieusis.svg)](LICENSE)

**Data does not come with the right questions attached.**

AI is rapidly improving at executing well-specified analyses. But science
advances earlier, when observations are turned into questions. Across
neuroscience, astronomy, climate science, economics, and the social sciences,
researchers increasingly work with rich existing datasets; their value depends
not only on what can be computed, but on which questions are worth asking and
which claims the data can actually support.

**Maieusis is an agent-operated system for that upstream task.** Given a target
dataset, source papers, and an optional research direction, it builds
source-backed reconstructions of the published moves that lead to scientific
questions, abstracts those **question-forming moves** into reusable patterns,
and uses them to generate new question families. Each shortlisted family is
then evaluated against the real dataset through an isolated Question
Owner–Dataset Planner dialogue: are the required constructs present, is the
comparison identifiable, and can the question be operationalized without
changing its scientific meaning?

What you get back for each question family is a **Scientific Question Dossier**: either an
evidence-backed plan you could hand to an analyst, or a specific reason not to proceed — the
construct is not in the data, the comparison is not identifiable, the literature already answers
it. Every step that led there is readable, and every claim in it names the artifact it came from.

The rejections are not failures of the system. They are the point: a dataset that cannot answer a
question should say so before you spend three months finding out.

> **Maieusis stops where execution begins, on purpose.** It develops the question and the plan,
> hands them to you, and never runs the analysis or looks at the data you are holding back to test
> the answer. That boundary is what lets everything upstream of it be aggressive.

<p align="center">
  <img src="docs/assets/maieusis-question-development.png" width="100%" alt="Maieusis question-development flow: three source-bound inputs pass through the Question Scientist, optional consolidation and shortlisting, an isolated Question Owner and Dataset Planner branch, independent review, and a plan, reject, defer, or warning dossier.">
</p>

<p align="center"><em>Source papers, current literature, and a dataset narrative become distinct question families; each shortlisted family is planned against the real dataset and closes before execution.</em></p>


## Start here

- **Try it for free first:** set `mode: subscription_only_demo` and run the whole
  workflow with mock providers and no API key. It shows the machinery, not
  scientific quality.
- **Run your own project:** [agent-guided setup](docs/AGENT_GUIDED_SETUP.md) is
  the recommended route — your own Codex or Claude Code interviews you, fills in
  the configuration, and refuses to spend without your approval.
  [Manual setup](docs/MANUAL_SETUP.md) if you would rather edit the YAML
  yourself, and [installation](docs/INSTALLATION.md) for the commands.
- **See the scientific output first:** the [demo gallery](demos/QUESTIONS.md) —
  eighteen question families across three datasets.
- **Understand the method:** [method overview](docs/METHOD_OVERVIEW.md) and
  [architecture](docs/ARCHITECTURE.md).
- **Find a specific guide:** the [documentation hub](docs/INDEX.md).

**Three things decide whether you can run this at all**, and none is fixable by
reading further: a **paid** Codex or Claude Code subscription (a separate bill
from your API budget), **two funded API providers** because owner and reviewer
must differ, and **twelve to twenty source papers** you may lawfully use. Your
dataset does *not* need to be public — an unpublished lab dataset is fully
supported. [Installation](docs/INSTALLATION.md#before-you-install-three-things-you-cannot-fix-by-reading-further)
covers all four, plus the system prerequisites and the clone that trips up most
first runs.

### The fastest route

[Install Maieusis](docs/INSTALLATION.md), create a clean project directory, and paste this into
Codex or Claude Code:

```text
Help me set up Maieusis v0.1.1 in this clean project directory.
1) Run `maieusis init`, then read AGENTS.md, CLAUDE.md, PROJECT_LAYOUT.md, and maieusis.yaml.
2) Help me place only lawfully obtained source-paper PDFs in papers/inbox.
3) Configure lawful read-only access to my target dataset and its documentation.
4) Set dataset.inspection_runtime.source_tree_root to a clean clone of the Maieusis
   repository. This is NOT my dataset's code and NOT `git init` here; it is how a run
   records the identity of the software that produced it:
     git clone https://github.com/BeibaiDraco/maieusis.git ~/maieusis-source
5) Configure Codex or Claude Code as the coding host. Keep coding-host credentials
   separate from scientific API keys, and never put secrets in YAML.
6) Edit maieusis.yaml without inventing dataset facts.
7) Run `maieusis check` and resolve every zero-paid preflight error.
8) Explain the configured models, estimated calls, and output locations, then ask for
   my explicit approval before `maieusis run`.
9) Stay with the run — it takes about an hour — and tell me afterwards whether it
   reached a consistent terminal AND whether it produced anything worth reading.
Do not execute the scientific analyses, inspect confirmation outcomes, or weaken a
provenance, isolation, or safety check.
```

Maieusis v0.1.1 is on [PyPI](https://pypi.org/project/maieusis/0.1.1/). The
[manual route](docs/MANUAL_SETUP.md) and the
[source install](docs/INSTALLATION.md#install-from-source) are both supported.

## Why this is different

Most scientific agents begin after a goal has already been specified: they
retrieve literature, write code, analyze data, or generate reports. Maieusis
operates one step earlier. It makes question-forming moves explicit, generates
candidate question families, and subjects each shortlisted family to a
target-dataset plan-or-reject process before any full analysis begins.

That separation matters. Proposal agents receive a coarse, source-backed
dataset narrative so incomplete schemas do not prematurely narrow scientific
imagination. Only after a family exists does a coding-agent planner inspect
real documentation, metadata, code, and bounded samples. A separate Question
Owner protects scientific intent, and an independent reviewer checks the plan.

<p align="center">
  <img src="docs/assets/maieusis-positioning-map.png" width="100%" alt="Conceptual task-design map positioning Maieusis by explicit question-forming move transfer and pre-execution target-dataset plan-or-reject, alongside 17 related systems and benchmarks; this is not a performance ranking.">
</p>

<p align="center"><em>A qualitative task-design comparison, not a performance, priority, or superiority ranking.
Yes, we placed ourselves in the empty corner — that is what the axes were chosen to show, so treat the position as a
claim about what Maieusis attempts rather than evidence that it succeeds. Each of the seventeen systems is placed
from a primary source you can check in the
<a href="docs/positioning/REFERENCE_MAP.md">reference map</a>.</em></p>

The map compares two design choices: explicit transfer of question-forming
moves and pre-execution evaluation against a target dataset. Read
[where Maieusis fits](docs/positioning/POSITIONING.md), with sources and
placement evidence available separately.

## Learn the move, not the result

PaperBank builds evidence-bound reconstructions of how selected publications
move from a starting state and unresolved tension to a scientific question.
Formation traces do not claim to recover authors' private thought processes.
Across papers, independently reviewed traces support reusable patterns that
retain the question-forming transformation—not copied questions, conclusions,
or known outcomes.

<p align="center">
  <img src="docs/assets/maieusis-paperbank-pattern-induction.png" width="100%" alt="PaperBank pattern-induction flow from reviewed paper cases through evidence-bound reviewed formation traces, cross-paper induction, review and deterministic verification, to a reviewed Question Pattern Bank.">
</p>

<p align="center"><em>Published evidence supports formation traces; cross-paper abstraction turns those traces into reusable question-forming patterns.
In the published traces the four labelled elements appear as five sections — starting background, unresolved gap, dataset opportunity,
resulting question, scientific consequence — and the question-forming move is written into the dataset-opportunity section rather than
carrying a heading of its own.</em></p>

Every question here is checked against the literature before it is planned, so you are less
likely to spend a season re-asking something already answered. This reduces that risk; it does
not remove it, and these demonstrations ship a
[named case where the review missed an obvious prior the run had already read](docs/LIMITATIONS.md). Every variant goes through prior-art review,
drawing on both a deterministic scholarly lane and an independent bounded
web-search lane. A prior can only remove a variant after it resolves to a real
DOI or OpenAlex identity — a model's impression is not enough — and every
variant removed on prior-art grounds says so, with its evidence, where you can
read it.

What it cannot do is certify novelty: no search proves absence, and the final
judgment stays with you. Users must obtain source papers lawfully;
neither Maieusis nor its demos distribute the PDFs.

## Inputs, outputs, and inspectable artifacts

| You provide | Maieusis develops |
| --- | --- |
| Source-paper PDFs | PaperCases, citation decisions, formation traces, and question-forming patterns |
| Topic terms or an optional seed question | A research intent and current topic-evidence brief |
| Dataset link, documentation, metadata, and read-only local access | A DatasetNarrative and branch-local planning evidence |
| Scientific API providers plus Codex or Claude Code | Question families, typed Owner–Planner dialogue, and independent review |
| Explicit approval for a paid run | `summary.md` and per-family dossiers recording plans and non-proceed outcomes |

The intermediate artifacts are part of the product: readers can inspect what
each paper contributed, how patterns were induced, what every proposed variant
meant, what the planner observed, and why a family advanced or stopped. Local
runs also retain machine records needed for integrity and recovery. See the
[complete run layout](docs/INPUTS_AND_OUTPUTS.md).

## Explore the demos

> **Three worked demonstrations, in two very different fields.** Maieusis is for any scientific
> discipline and any scientific dataset. A serious run still needs lawful, read-only access to
> enough documentation, metadata, code, or representative data for the Dataset Planner to inspect.
> We are testing it with researchers at different universities across
> physics, astronomy, finance, social science, and psychology, using datasets from their own
> fields. If you would like to join these scientific collaborations, contact
> **Draco (Yunlong) Xu** at `dracoxu@uchicago.edu`.

Each demonstration publishes its whole chain — the papers it read, the patterns it induced, every
question it proposed, what the planner found in the data, and why each family advanced or stopped.
Nothing is summarised for you: the rejections are there next to the plans. Source PDFs, raw model
payloads, credentials, and private runtime state are excluded.

- **Neuroscience — mouse decision-making.** The
  **[IBL Brain-Wide Map](demos/ibl/README.md)**: brain-wide recordings from mice performing a
  sensory decision task, pooled across many laboratories
  ([Nature paper](https://doi.org/10.1038/s41586-025-09235-0),
  [release guide](https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html)).
  *When is shared trial-to-trial variability a nuisance, a computational resource, or just the
  animal moving?* Two variants pull against each other — task-aligned structure versus aggregate
  magnitude, and decision organization versus embodied co-variation — and both reached independently
  reviewed plans. Five sibling families ask, among other things, whether population geometry stays
  invariant across decision epochs.
  [Both variants, and what each outcome would mean](demos/ibl/artifacts/questions/question_families_detailed.md#family-002-task-relevance-of-structured-neural-co-variability) ·
  [Proposal hypothesis versus inspected evidence](demos/ibl/artifacts/families/covariability-structure/dossier_detailed.md) ·
  [the full record](demos/ibl/artifacts/families/covariability-structure/dossier.md)

- **Neuroscience — macaque reaching.** A pinned **[NLB MC_Maze-S](demos/nlb/README.md)** session
  from the Neural Latents Benchmark: simultaneous recordings from macaque primary motor cortex (M1)
  and dorsal premotor cortex (PMd) during delayed straight and curved reaches
  ([benchmark paper](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/979d472a84804b9f647bc185a877a8b5-Abstract-round2.html),
  [pinned DANDI dataset](https://doi.org/10.48324/dandi.000140/0.220113.0408)).
  *Does the geometric form of a motor manifold mean anything computationally, or does a more
  elaborate description merely fit better?* Two variants pull against each other — a frozen
  shared-geometry transfer test that refits nothing, and a nonlinear context-interaction test on
  kinematically matched segments — and both reached independently reviewed plans.
  [Both variants, and what each outcome would mean](demos/nlb/artifacts/questions/question_families_detailed.md#family-006-functional-meaning-of-motor-manifold-form) ·
  [Proposal hypothesis versus inspected evidence](demos/nlb/artifacts/families/manifold-form-functional-meaning/dossier_detailed.md) ·
  [the full record](demos/nlb/artifacts/families/manifold-form-functional-meaning/dossier.md)

- **Climate science — the polar stratosphere.** An
  **[ERA5-derived record](demos/climate/README.md)** of wave activity, zonal winds and eddy forcing
  at 60 degrees North, across 97 heights and roughly four decades. **Nothing in the system was
  adapted for atmospheric science.**
  *Is vertical coupling a propagating episode or a coherent mode spanning heights — and is that
  distinction real, or an artifact of how you represent it?* Two variants pull against each other —
  an event-first lagged coupling test, and a continuous-mode robustness test — and both reached
  independently reviewed plans. The dataset is a collaborator-supplied derived product and is not
  redistributed; [the dataset notes](demos/climate/DATASET_NOTES.md) say so plainly.
  [Both variants, and what each outcome would mean](demos/climate/artifacts/questions/question_families_detailed.md#family-005-propagating-episodes-versus-coherent-modes-of-vertical-coupling) ·
  [Proposal hypothesis versus inspected evidence](demos/climate/artifacts/families/vertical-coupling-representations/dossier_detailed.md) ·
  [the full record](demos/climate/artifacts/families/vertical-coupling-representations/dossier.md)

All three carry the gallery's **Plan developed (provisional)** label — reviewed by a second model on
a different provider rather than by a human expert, and never executed. Nothing on this page is a
result.

These are entry points, not a ranking. **Continue to the [complete gallery](demos/QUESTIONS.md) for
all 18 families and all 36 variants,** including scientific background, competing explanations,
assumptions, positive/negative/null interpretations, and the three families that closed as
scientific rejections rather than plans.

### And one that sounds right until you look at the task

The three above reached plans. This one did not, and it is the shortest way to see what the planner
is actually for.

The question: in a two-alternative visual discrimination, does the final pre-movement population
state carry incremental information about the animal's **perceptual choice** as against its
**movement direction**? Separating choice from movement in premotor activity is a real problem and
a reasonable thing to ask. Nothing about the sentence is wrong.

In this task the mouse reports its choice *by turning a wheel*. Wheel direction is therefore an
almost deterministic encoding of choice, and the release documents no alternative report mapping.
Conditioning on movement direction conditions on the choice report itself — the two things the
question wants to hold apart are one thing. The variant closed as an **operationalization failure**,
and the dossier says exactly that: the contrast "cannot preserve its intended contrast" for this
dataset-task pairing.

The question is not wrong in general. It is wrong *here*, and only a look at the task design shows
it. That is the check a proposal stage cannot do for itself, and it is why the dataset planner exists.

**[Read the family, both variants, and the closure](demos/ibl/artifacts/families/decision-dynamics/dossier.md)** ·
[See it in the gallery with the rest](demos/QUESTIONS.md)

## One workflow, three layers

- **A local coding-agent host.** Serious use requires either Codex CLI or
  Claude Code. The Dataset Planner works in an isolated, branch-scoped
  workspace with read-only access to permitted dataset documentation, schemas,
  metadata, code, and bounded samples. Sandboxing and access checks reduce
  exposure; they are defense-in-depth, not a promise of perfect security. That
  same session also carries the run through failures under a written contract —
  [the contract it works under](docs/SHEPHERD_MODE.md).
- **Remote scientific agents.** Frontier-model APIs support PaperBank,
  question generation, Question Owner dialogue, and independent review.
  Scientific API keys remain separate from coding-host subscription
  credentials.
- **A deterministic core.** Python orchestration validates typed outputs,
  preserves source and evidence identity, isolates families, bounds retries
  and budgets, enforces confirmation and execution firewalls, persists state,
  and renders readable outcomes.

Deterministic checks enforce boundaries and provenance; they do not establish
scientific truth.

## A coding agent drives the run, under a contract

Papers fail to parse. A provider rate-limits at hour two. A rigid pipeline answers by ending the run
and you get nothing; most flexible systems absorb the problem quietly, and you get output you cannot
audit. **Maieusis takes the third option: a coding agent drives the run, because judgment is exactly
what these situations need** — under a written contract. It can diagnose a stop and resume what is
safe to resume. It cannot write over the run that stopped, cannot repair past a guard, and cannot
turn a scientific rejection into an acceptance: **repair gets a run past infrastructure, never past a
scientific verdict.** That shepherd is your own coding-agent session, not a service we run, and
`maieusis init` writes these rules into your project before it drives anything of yours. The IBL
demonstration here was finished by a disclosed resume, and its manifest publishes two build
identities rather than one clean lineage.

The contract: [what a shepherd may repair, what it must record, and the three things repair may
never do](docs/SHEPHERD_MODE.md). Reading a stopped run: [the two questions, the three honest
terminal shapes, and how to tell a scientific "no" from a fault](docs/RUN_SUPERVISION.md) —
`maieusis status <run-id>` makes no paid call.

## Trust, limits, and community

This is a research preview. An independently reviewed plan is not a result, and two models agreeing
is not evidence — it is two models agreeing. Dataset inspection can expose feasibility problems but
cannot establish novelty or importance, no search proves absence, and human domain expertise remains
the thing that decides, especially before any downstream analysis is authorized.

What Maieusis does instead of claiming otherwise: **every plan states its own limits, in its own
dossier**, so you are never left inferring how much weight one can carry.

**What a run costs.** The climate demonstration on this page — six question families, two variants
each — took **219 model calls** and about an hour end to end; your wall clock depends mostly on your
dataset. Paid web search is the one lane with an exact price, and it came to **$0.45** against a
ceiling you set before the run. Token cost is not metered by Maieusis, so read it from your
provider's dashboard rather than from us.

`maieusis check` makes no paid call and prints what a run will do before you authorise it. To see
the machinery for nothing, set `mode: subscription_only_demo`. To bound a first real bill, set
`run.max_families: 2` and scale from what you measure.

- [Method overview](docs/METHOD_OVERVIEW.md)
- [When a run stops](docs/RUN_SUPERVISION.md)
- [Architecture and trust boundaries](docs/ARCHITECTURE.md)
- [Provenance](docs/PROVENANCE.md)
- [Limitations](docs/LIMITATIONS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

Maieusis is designed for any scientific discipline and any scientific dataset
that can provide the lawful inspection surface needed for responsible
planning. The invitation is open: researchers interested in applying it to
their field can contact **Draco (Yunlong) Xu** at `dracoxu@uchicago.edu` for help
or to join the scientific collaboration program.

## Citation and license

Maieusis is licensed under Apache-2.0. Copyright 2026 Yunlong Xu. Software
authors are [Draco (Yunlong) Xu](https://orcid.org/0000-0003-2589-7232) and
[Brent Doiron](https://orcid.org/0000-0002-6916-5511).

For reproducible use, cite the software and name the version you ran:

> Xu, Y., & Doiron, B. (2026). *Maieusis* (Version v0.1.1) [Computer
> software]. Zenodo. https://doi.org/10.5281/zenodo.21388805

The concept DOI
[`10.5281/zenodo.21388805`](https://doi.org/10.5281/zenodo.21388805) represents
Maieusis across versions and always resolves to the latest release; it is what
[CITATION.cff](CITATION.cff) records and what GitHub's **Cite this repository**
panel offers. Each release also has its own version DOI — v0.1.0's is
[`10.5281/zenodo.21388806`](https://doi.org/10.5281/zenodo.21388806) — for when
you need to point at one exact archived snapshot. See the
[citation guide](docs/CITATION.md) for which to use. A separate technical report
is planned and will be added as the preferred citation after it is published.

See [LICENSE](LICENSE), [NOTICE](NOTICE), [AUTHORS.md](AUTHORS.md),
[CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md).
