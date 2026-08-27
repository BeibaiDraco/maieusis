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
  scientific quality. [What demo mode needs and skips](docs/MANUAL_SETUP.md#manual-setup) —
  no Poppler, no coding-host login, no source clone, but still your own PDFs and a dataset root.
- **Run your own project:** [agent-guided setup](docs/AGENT_GUIDED_SETUP.md) is
  the recommended route — your own Codex or Claude Code interviews you, fills in
  the configuration, and refuses to spend without your approval.
  [Manual setup](docs/MANUAL_SETUP.md) if you would rather edit the YAML
  yourself, and [installation](docs/INSTALLATION.md) for the commands.
- **See the scientific output first:** the [demo gallery](demos/ALL_QUESTIONS.md) —
  twenty-four question families across four demonstrations of three datasets.
- **Understand the method:** [method overview](docs/METHOD_OVERVIEW.md) and
  [architecture](docs/ARCHITECTURE.md).
- **Find a specific guide:** the [documentation hub](docs/INDEX.md).

**Three things decide whether you can run this at all**, and none is fixable by
reading further: a **paid** Codex or Claude Code subscription (a separate bill
from your API budget), **two funded API providers** because owner and reviewer
must differ, and **twelve to twenty source papers** you may lawfully use. Your
dataset does *not* need to be public — an unpublished lab dataset is fully
supported. [Installation](docs/INSTALLATION.md#before-you-install-three-things-you-cannot-fix-by-reading-further)
covers all three, plus the system prerequisites and the clone that trips up most
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

This documentation describes Maieusis v0.1.1; releases are published to
[PyPI](https://pypi.org/project/maieusis/), and the version badge above says which one is current.
The [manual route](docs/MANUAL_SETUP.md) and the
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
variant removed on prior-art grounds says so, with the priors it was measured
against. Most say it on the variant's own line. Where a whole family closed at
the gate, the disposition line reads simply *not shortlisted — deferred* and
the priors are listed on the family's page instead; the evidence is published
either way, one click further in the second case.

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

## What it produced

Four runs over three real datasets. Every question, and what happened to each:

| Dataset | Questions | Reached a plan | Closed |
| --- | --- | --- | --- |
| [Mice making decisions](demos/ibl/README.md) — IBL Brain-Wide Map, asked about *noise correlations* | 6 | 3 | 3 |
| [The same recordings](demos/ibl-open/README.md) — IBL Brain-Wide Map, asked nothing | 6 | 5 | 1 |
| [A monkey reaching](demos/nlb/README.md) — NLB MC_Maze-S | 6 | 5 | 1 |
| [The polar stratosphere](demos/climate/README.md) — ERA5-derived | 6 | 5 | 1 |

**→ [Every question in one table](demos/ALL_QUESTIONS.md)** — the complete gallery: all 24 questions
and all 48 versions, one row each, with what happened to it and a link into the run's own record.
Nothing is left out of it, including the questions that went nowhere.

Each run publishes its whole chain: the extracted record of each paper it read, the patterns it drew
from them, every question it proposed, what the planner found when it opened the data, and why each
question went forward or stopped. Nothing is summarised for you, and the refusals sit next to the
plans. Source PDFs, raw model payloads, credentials and private runtime state are not published.

> **Four worked demonstrations here, in two very different fields, and nothing in the system was
> adapted for either one.** Maieusis works on any scientific discipline and any dataset you can give
> the Dataset Planner lawful, read-only access to inspect: documentation, metadata, code, or
> representative data. We are testing it now with researchers at several universities across climate
> science, physics, astronomy, finance, social science, and psychology, on datasets from their own
> fields. To join those collaborations, write to **Draco (Yunlong) Xu** at `dracoxu@uchicago.edu`.

### The data behind each run

- **Mice making decisions, recorded across the whole brain.** The
  **[IBL Brain-Wide Map](demos/ibl/README.md)** pools Neuropixels recordings from mice performing one
  standard visual decision task, repeated laboratory after laboratory
  ([Nature 2025](https://doi.org/10.1038/s41586-025-09235-0),
  [release guide](https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html)).
  The repetition is the point: it lets a question separate what reproduces across laboratories from
  what belongs to the laboratory that recorded it. This run was handed one declared topic — *noise
  correlations*.

- **The same mice, asked nothing.** The **[open-mode run](demos/ibl-open/README.md)** is those
  identical recordings, the same twelve papers, the same models, with the topic removed: it read the
  dataset's own description and derived its own scope. The two runs produced twelve questions with no
  family in common — not one shared title. Reading them side by side is the most direct evidence here
  for what declaring a topic actually does.

- **A monkey reaching, two motor areas recorded at once.** A pinned session of
  **[NLB MC_Maze-S](demos/nlb/README.md)**, from the Neural Latents Benchmark, records macaque
  primary motor cortex (M1) and dorsal premotor cortex (PMd) together during delayed straight and
  curved reaches
  ([benchmark paper](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/979d472a84804b9f647bc185a877a8b5-Abstract-round2.html),
  [the pinned DANDI dataset](https://doi.org/10.48324/dandi.000140/0.220113.0408)). The demo page
  claims which electrode array covers which area, then ships
  [a script that re-derives the mapping from the public data and fails loudly if we got it wrong](demos/nlb/verify_region_mapping.py).

- **Four decades of the polar stratosphere, on a system adapted for none of it.** Twenty
  climate-dynamics papers and a source-backed description of an
  **[ERA5-derived record](demos/climate/README.md)**: wave activity, zonal winds, and eddy forcing at
  60 degrees North, on a 97-level column from the surface to 48 km, six-hourly, across roughly four
  decades. Nothing in the system was adapted for atmospheric science. The data is a collaborator's
  derived product and is not redistributed; [the dataset notes](demos/climate/DATASET_NOTES.md) say
  so plainly.

### Four questions worth opening

One from each run. Each was asked two ways on purpose: two framings of one question fail
differently, and which one fails tells you where the problem is.

**Does evidence accumulate along one fixed direction, or move through a sequence of states?**
([mice, asked about noise](demos/ibl/artifacts/families/accumulation-geometry/dossier.md))

Two accounts of the same behaviour. In one, activity slides along a single population axis that
stays put across the trial. In the other, the population passes through a succession of distinct
states, each briefly holding the decision. Trial-averaged firing looks much the same either way.
What separates them is how activity co-varies from trial to trial — which is what this run was
pointed at.

The accepted plan takes one shared-variability direction, estimated without reference to choice.
It asks whether that direction holds across decision time and across sensory conditions, tracks
accumulated evidence, and predicts choice and response time — after sensory features, action plans,
elapsed time and movement are accounted for. Those four are what make a slow drift look like an
accumulator.

The sibling asked the same question from the sequence side, and did not survive the data. Its test
needs the trial-by-trial sequence of evidence pulses; this release records one contrast value per
trial. The Owner ruled that the available proxy would answer a different question, not a weaker
version of this one.

**Is shared variability aligned with the decision, or merely large?**
([the same recordings, asked nothing](demos/ibl-open/artifacts/families/variability-geometry/dossier.md))

Shared trial-to-trial variability is usually summarised by its size. This question is about its
direction. Variability lying along the population dimension that carries evidence limits what can
be read out of the population; variability of the same magnitude lying elsewhere does not.

So the plan asks whether the component aligned with an independently defined decision dimension —
and specifically not with a movement dimension — predicts choice and response time on held-out
trials. It has to beat three things: alignment with sensory evidence, movement covariates, and
overall variability magnitude. The last of those is the question. Without it, a trial that is merely
noisier cannot be told from a trial that is informatively noisy.

Nothing told this run to look here. It read the dataset's own description, derived its own scope,
and arrived at shared variability by itself. The run above was handed *noise correlations* as a
topic and asked what accumulation geometry is; this one asked what shared variability is for. No
family title appears in both.

Its sibling was stopped at prior-art review, against work that had already run this alignment test
in macaque V1.

**Is preparation reusable across contexts, and is execution driven or autonomous?**
([a monkey reaching](demos/nlb/artifacts/families/context-dependent-motor-dynamics/dossier.md))

Motor cortex before a reach can be read two ways. Either preparation sets up an organisation that
is the same whatever path follows, or it specifies the path. Both fit low-dimensional averaged
activity, and geometry alone does not choose between them.

The manipulation does. The same animal reaches straight when the workspace is clear and curves when
a barrier is in the way.

The preparatory plan asks whether the two share one population organisation with curvature-selective
components laid on top, or whether preparation is entirely condition-general once the movements'
covarying demands are separated. The execution plan asks a different thing of the same trials:
whether curved-path dynamics track ongoing behavioural input more than straight-path dynamics do.
Autonomy tested as a difference between conditions, rather than asserted of one.

Splitting the trial is the point. Preparation and execution can answer in opposite directions, and a
design that ran them together would report the average of the two. Both reached reviewed plans.

**Is the vortex breakdown the same process run backwards?**
([the polar stratosphere](demos/climate/artifacts/families/lifecycle-asymmetry-memory/dossier.md))

A major weakening of the polar vortex has a descent and a recovery. If they are one process in two
directions, the same wave–mean-flow pathways should govern both, reversed. If they are not, the
recovery has a route of its own.

The accepted plan asks exactly that: are the vertical circulation and wave–mean-flow pathways into
weakening the time reverse of those out of it, or is the lifecycle reproducibly asymmetric? It is a
question about the shape of a trajectory rather than about either end of it.

The sibling went one step further and asked whether recovery carries dynamical memory of the forcing
that preceded it. Prior-art review stopped it before any planner opened the data. Published work
already attributes slow lower-stratospheric recovery to suppressed wave driving after the warming,
and to radiative relaxation; a memory term would have to be separated from both first. The records
it named are on the run's [prior-art page](demos/climate/artifacts/questions/prior_art.md).

### Two questions it refused, for two different reasons

The refusals are the part you cannot get from a system that shows you only what worked, and these
two fail in opposite ways.

**The dataset was missing a dimension.** A climate question asked whether rapid vortex weakening is
driven by unusual wave forcing or by the vortex already being susceptible. Telling those apart means
distinguishing a vortex that *splits* from one that is *pushed off centre* — two shapes. This record
is a single circle of latitude with longitude already averaged away, and you cannot see a shape in a
line. The planner named the missing construct and stopped, rather than substituting something
adjacent that would have answered a different question.
[Read the refusal](demos/climate/artifacts/families/precursor-susceptibility/dossier.md)

**Nothing was missing; the design never pulls the two apart.** An NLB question asked whether
preparatory activity carries the *shape* of an intended path, beyond the simpler features a reach can
be described by. Every quantity it names is in the data. Then the planner looked at how the trials
are built: every curved reach is a trial with barriers on the screen, every straight reach has none,
and there is no curved reach without barriers and no barrier layout that yields a straight plan. So
"planning a curved path" and "seeing a barrier" are the same trials, any separation you found could
be either, and the question had already named the visible cue as an alternative it must rule out. The
sibling version failed from the other side: separating route intention from execution needs two
different intended routes performed with matching movements, and here the movement is almost entirely
determined by the route, so those trials essentially do not exist.
[Read the closure](demos/nlb/artifacts/families/trajectory-geometry-alternatives/dossier.md)

Nothing in a dataset description tells you either of those. One is a dimension the recording does
not have. The other is a dataset that holds every quantity the question names and still cannot
separate the two accounts, because of how the trials were designed. Both are checks a proposal stage
cannot perform on itself: they need something to open the data and look.

### How to read any one of them

Eighteen of the 24 produced a plan; the other six are on the page with the reason each one closed,
and those reasons are not all the same kind. Twenty-three of the 24 also carry a reading guide, whose
*proposal hypothesis versus inspected evidence* section sets what the proposal stage assumed beside
what the planner actually found in the data. The twenty-fourth has none, and that is not an
oversight: prior-art review closed it before any planner opened the data, so there is no inspected
evidence to set anything beside. That comparison is the one this whole page is arguing for.

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
demonstration here carries three families that produced no plan for reasons that are not
scientific — one provider outage and two that the run could not validate on the way back in — and
they stay on the page with their causes named.

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
each — took **one hour and fifty-six minutes** end to end. The four demonstrations here ran between
fifty minutes and just under two hours; your wall clock depends mostly on your dataset and on how
deep the planner goes into it.

**Maieusis does not meter token cost**, so read that from your provider's dashboard rather than from
us. Paid web search is the one lane with a hard ceiling: you set it before the run, preflight prints
the reservation it will hold, and the run cannot exceed it.

`maieusis check` prints what a run will do before you authorise it. It launches no coding agent and
runs no stage, but it does send **one minimal request per configured provider** — a fraction of a
cent — because a key that authenticates but cannot be billed should fail there rather than an hour
into a paid run. To see the machinery for nothing at all, set `mode: subscription_only_demo`, which
uses no provider. To bound a first real bill, set `run.max_families: 2` and scale from what you
measure.

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
