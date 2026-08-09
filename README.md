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

## One workflow, three layers

- **A local coding-agent host.** Serious use requires either Codex CLI or
  Claude Code. The Dataset Planner works in an isolated, branch-scoped
  workspace with read-only access to permitted dataset documentation, schemas,
  metadata, code, and bounded samples. Sandboxing and access checks reduce
  exposure; they are defense-in-depth, not a promise of perfect security.
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

**What v0.1.1 does not claim.** This is a research preview. Maieusis does not certify that a
question is novel, important, or true; no search proves absence, and agreement between models is
not evidence. It does not run the final analysis, search for significant effects, access a
confirmation set — the held-back data you would use to test an answer, which no stage of Maieusis
may see — or authorize a confirmatory claim. Every plan it produces says which of these
limits apply to it, in its own dossier, rather than leaving you to infer them.

## Start here

- **Run your own project:** use the [agent-guided setup](docs/AGENT_GUIDED_SETUP.md)
  or [manual setup](docs/MANUAL_SETUP.md).
- **See the scientific output first:** explore the
  [demo gallery](demos/QUESTIONS.md) — eighteen question families across three datasets.
- **Understand the method:** read the [method overview](docs/METHOD_OVERVIEW.md)
  and [architecture](docs/ARCHITECTURE.md).
- **Find a specific guide:** open the [documentation hub](docs/INDEX.md).

### Fastest route: ask a coding agent

This is the recommended route, and the agent will interview you for what it
needs. It still cannot install Poppler, log you into a coding host, or create
your API keys — see [what must be in place first](#manual-route), which applies
to both routes.

After [installing Maieusis](docs/INSTALLATION.md), create a clean project
directory and paste this into Codex or Claude Code:

```text
Help me set up Maieusis v0.1.1 in this clean project directory.
1) Run `maieusis init`, then read AGENTS.md, CLAUDE.md, PROJECT_LAYOUT.md,
   and maieusis.yaml.
2) Help me place only lawfully obtained source-paper PDFs in papers/inbox.
3) Configure lawful read-only access to my target dataset and its documentation.
4) Set dataset.inspection_runtime.source_tree_root to a clean clone of the
   Maieusis repository. This is NOT my dataset's code and NOT `git init` here;
   it is how a run records the identity of the software that produced it. Clone
   it with:
     git clone https://github.com/BeibaiDraco/maieusis.git ~/maieusis-source
5) Configure Codex or Claude Code as the coding host. Keep coding-host
   credentials separate from scientific API keys, and never put secrets in YAML.
6) Edit maieusis.yaml without inventing dataset facts.
7) Run `maieusis check` and resolve every zero-paid preflight error.
8) Explain the configured models, estimated calls, and output locations, then
   ask for my explicit approval before `maieusis run`.
9) After the run, open summary.md and the per-family scientific dossiers.
Do not execute the scientific analyses, inspect confirmation outcomes, or
weaken a provenance, isolation, or safety check.
```

### Manual route

**First, three things you cannot fix by reading further.** Decide these before you install
anything — each one on its own ends the attempt:

- **A paid Codex or Claude Code subscription.** The Dataset Planner runs on it. This is a
  *separate* bill from your model API budget, and a coding-host login is not an API key.
- **Two funded API providers.** The Question Owner and the independent reviewer must sit on
  different providers, which preflight enforces — so one account is not enough.
- **Between roughly twelve and twenty source papers** you may lawfully use. The published
  demonstrations used twenty (climate) and twelve (neuroscience).

**Your dataset does not need to be public.** An unpublished lab dataset is fully supported: leave
`dataset.seed.link` empty and point `dataset.seed.docs` at your own local documentation. A public
link is one way to describe a dataset, not a requirement.

**Then four things must be in place before the install.** Each fails `maieusis check` if missing,
and the third is the most common first-run failure by a wide margin:

1. **Poppler** on your PATH, for `pdftotext` — the default PDF parser needs it.
   `brew install poppler`, or `apt install poppler-utils`. Preflight does not
   check this, so a missing binary passes `maieusis check` and fails during the
   paid run.
2. **A coding host** — Codex or Claude Code, installed and logged in. It runs
   the Dataset Planner. Its login is *not* an API key.
3. **A clean clone of Maieusis itself**, for `source_tree_root`. Every run
   records the identity of the software that produced it, and it needs a real
   checkout to read that from. Running `git init` in your own project does not
   work. Clone it once, anywhere outside your project:

   ```bash
   git clone https://github.com/BeibaiDraco/maieusis.git ~/maieusis-source
   ```

4. **Two API keys**, `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`, in
   `~/.config/maieusis/runtime.env` or exported. Owner and reviewer must sit on
   different providers, which is why there are two.

Then create the project directory *before* its virtual environment. Set
`PYTHON` to an installed Python 3.11, 3.12, or 3.13 executable and confirm the
reported version before continuing.

```bash
mkdir my-maieusis-project
cd my-maieusis-project
PYTHON=python3.11  # change to python3.12 or python3.13 when appropriate
"$PYTHON" --version
"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "maieusis[mcp,pdf,openai,anthropic]==0.1.1"
maieusis init
mkdir -p papers/inbox   # init does not create this
# Add lawful PDFs under papers/inbox, then edit maieusis.yaml —
# set dataset.seed.link, dataset_root, and source_tree_root.
maieusis check --project maieusis.yaml   # no paid model calls
maieusis run --project maieusis.yaml     # paid; run only after approval
```

Maieusis v0.1.1 is available from [PyPI](https://pypi.org/project/maieusis/0.1.1/).
The [source-install route](docs/INSTALLATION.md#install-from-source) remains
available for contributors. The current standard configuration uses distinct
OpenAI and Anthropic API providers so Question Owner work and independent
review do not share a provider. See [configuration](docs/CONFIGURATION.md)
before the first paid run.

### What a run actually costs

Numbers from the climate demonstration on this page — 20 source PDFs, six question families, two
variants each, one planner host:

| | |
| --- | --- |
| Model calls, all roles | **219** (129 structured generation, 67 planner-dialogue turns, 18 prior-art scout calls, 5 other) |
| Paid web searches | **45**, at $0.01 each under rate card `anthropic_direct_web_search_20250305` |
| **Web-search tool fee — actually billed** | **$0.45** (IBL $0.62, NLB $0.57), against a $1.00 ceiling reserved before the run |
| Free scholarly lookups (Crossref, OpenAlex) | 1,342 |
| Coding-agent planner launches | 6, one per family |
| Wall clock | hours, not minutes — the NLB run spent 32 minutes in family planning alone |

The web-search fee is exact rather than estimated: the rate card is named, and every search a scout
makes is counted against it in a receipt written during the run. Your own runs write those receipts
into your run directory; the demonstration's receipts are internal operator records and are not
published here.

**Model token cost is the part we cannot state honestly, so we do not state it.** Maieusis does not
meter token spend, and token prices differ per provider and change over time. The 219 calls above
are the durable number — price them against your own provider's rates, and note that two of the
shipped role pins are premium-tier. Read your provider's own dashboard for the real total; treat
the fee ceiling as a bound on the search lane only, not on the run.

`maieusis check` makes **no paid call** and prints the estimated calls, the planner launches, the
external services that will be contacted, and the web-search fee reservation before you authorise
anything. Run it first. If you want to see the machinery for nothing at all, set
`mode: subscription_only_demo`, which substitutes mock providers and costs zero — it demonstrates
the workflow, not scientific quality.

**How to bound your first bill.** Set `run.max_families: 2` for the first paid run rather than
changing the model pins, read your provider's dashboard afterwards, and scale from a number you
measured instead of one you guessed. The shipped six-family shape is the one the demonstrations
used, and it is what the cost table above describes.

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

A target dataset must provide lawful read-only access to documentation and
enough local structure—such as schema, metadata, code, or bounded samples—for
the Dataset Planner to evaluate whether a responsible analysis plan is
possible.

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

- **[IBL Brain-Wide Map](demos/ibl/README.md)** — *When is shared trial-to-trial variability a
  nuisance, a computational resource, or just the animal moving?* Six families, including whether
  population geometry stays invariant or reorganizes across decision epochs, and whether
  decision signals are broadly distributed or anatomically selective. Developed against the
  International Brain Laboratory Brain-Wide Map, a standardized multi-laboratory collection of
  brain-wide recordings from mice performing a sensory decision task
  ([Nature paper](https://doi.org/10.1038/s41586-025-09235-0),
  [release guide](https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html)).
- **[NLB MC_Maze-S](demos/nlb/README.md)** — *Does the geometric form of a motor manifold mean
  anything computationally, or does a more elaborate description merely fit better?* Six families,
  including whether M1 and PMd share one population geometry or divide the work, and whether
  co-variability matters by its alignment or by its magnitude. Developed against a pinned Neural
  Latents Benchmark session: simultaneous recordings from macaque primary motor cortex (M1) and
  dorsal premotor cortex (PMd) during delayed straight and curved reaches
  ([benchmark paper](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/979d472a84804b9f647bc185a877a8b5-Abstract-round2.html),
  [pinned DANDI dataset](https://doi.org/10.48324/dandi.000140/0.220113.0408)).
- **[Climate — ERA5-derived stratospheric dynamics](demos/climate/README.md)** — *Is vertical
  coupling in the polar stratosphere a propagating episode or a coherent mode spanning heights —
  and is that distinction real or an artifact of how you represent it?* Six families, including
  whether apparent persistence is memory or path dependence, and whether state occupancy or
  within-state dynamics changed over four decades. Developed against a one-dimensional record of
  wave activity, zonal winds, and eddy forcing at 60 degrees North, 97 heights, roughly four
  decades. **Nothing in the system was adapted for atmospheric science.** The dataset is a
  collaborator-supplied derived product and is not redistributed;
  [the dataset notes](demos/climate/DATASET_NOTES.md) say so plainly.

### IBL — when does shared neural variability matter for a decision?

Neural populations fluctuate together from trial to trial. Whether that shared variability is a nuisance, a task-aligned computational resource, or mostly a reflection of the animal's movement and posture is not settled by observing that it exists.

Maieusis developed two variants that pull in different directions: task-aligned structure versus aggregate magnitude, and
decision organization versus embodied co-variation. Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans. No analysis was executed.

**[Explore both variants, their competing explanations, and what positive, negative, or null
outcomes would mean](demos/ibl/artifacts/questions/question_families_detailed.md#family-002-task-relevance-of-structured-neural-co-variability)** ·
[See the study plan, including proposal hypothesis versus inspected evidence](demos/ibl/artifacts/families/covariability-structure/dossier_detailed.md) ·
[Open the complete planning record](demos/ibl/artifacts/families/covariability-structure/dossier.md)

### NLB — does the shape of a neural manifold mean anything?

Motor population activity can be described as lying on a simple reusable surface or on a curved,
context-dependent one. But a more elaborate geometric description can fit better and mean nothing,
so complexity alone settles nothing about computation.

Maieusis developed two variants that pull in different directions: a frozen shared-geometry transfer
test that refits nothing, and a nonlinear context-interaction test on kinematically matched
segments. Outcome: **Plan developed (provisional)** — both variants reached independently reviewed
plans. No analysis was executed.

**[Explore both variants, their competing explanations, and what positive, negative, or null
outcomes would mean](demos/nlb/artifacts/questions/question_families_detailed.md#family-006-functional-meaning-of-motor-manifold-form)** ·
[See the study plan, including proposal hypothesis versus inspected evidence](demos/nlb/artifacts/families/manifold-form-functional-meaning/dossier_detailed.md) ·
[Open the complete planning record](demos/nlb/artifacts/families/manifold-form-functional-meaning/dossier.md)

These three highlights are entry points, not a ranking. **Continue to the
[complete gallery](demos/QUESTIONS.md) for all 18 families and all 36 variants,** including
scientific background, competing explanations, assumptions, positive/negative/null interpretations,
and the three families that closed as scientific rejections rather than plans.
### Climate — vertical coupling in the polar stratosphere

Anomalies at one height in the stratosphere are followed by anomalies at another. Whether that is a temporally ordered propagation during discrete episodes, or a single coherent mode spanning heights that only looks like propagation, is a genuine open question -- and which answer you get can depend on the diagnostic you chose.

Maieusis developed two variants that pull in different directions: event-first lagged coupling test, and
continuous-mode robustness test. Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans. No analysis was executed.

**[Explore both variants, their competing explanations, and what positive, negative, or null
outcomes would mean](demos/climate/artifacts/questions/question_families_detailed.md#family-005-propagating-episodes-versus-coherent-modes-of-vertical-coupling)** ·
[See the study plan, including proposal hypothesis versus inspected evidence](demos/climate/artifacts/families/vertical-coupling-representations/dossier_detailed.md) ·
[Open the complete planning record](demos/climate/artifacts/families/vertical-coupling-representations/dossier.md)


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

## Trust, limits, and community

An independently reviewed plan is not a result, and model agreement is not
truth. Dataset inspection can expose feasibility problems, but cannot by
itself establish novelty or importance. Human domain expertise remains
valuable, especially before any downstream analysis is authorized.

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
