# Maieusis

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

The result is an inspectable **Scientific Question Dossier**—a grounded plan or
an explicit non-proceed outcome, such as revision, deferment, evidence-backed
rejection, or a validation warning—together with human-readable intermediate
artifacts and a provenance trail. Conceptually, Maieusis turns an open-ended
hypothesis space into a structured search surface constrained by scientific
precedent and dataset affordances.

> **Research Preview · v0.1.0.** Maieusis is designed to prioritize nontrivial,
> scientifically consequential questions, but it does not certify novelty,
> importance, or truth. It does not run the final scientific analysis, search
> for significant effects, or authorize confirmatory claims. The downstream
> analysis-execution bridge is closed.

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

## Start here

- **Run your own project:** use the [agent-guided setup](docs/AGENT_GUIDED_SETUP.md)
  or [manual setup](docs/MANUAL_SETUP.md).
- **See the scientific output first:** explore the
  [12-question demo gallery](demos/QUESTIONS.md).
- **Understand the method:** read the [method overview](docs/METHOD_OVERVIEW.md)
  and [architecture](docs/ARCHITECTURE.md).
- **Find a specific guide:** open the [documentation hub](docs/INDEX.md).

### Fastest route: ask a coding agent

After [installing Maieusis](docs/INSTALLATION.md), create a clean project
directory and paste this into Codex or Claude Code:

```text
Help me set up Maieusis v0.1.0 in this clean project directory.
1) Run `maieusis init`, then read AGENTS.md, CLAUDE.md, PROJECT_LAYOUT.md,
   and maieusis.yaml.
2) Help me place only lawfully obtained source-paper PDFs in papers/inbox.
3) Configure lawful read-only access to my target dataset, its documentation,
   and the source checkout used by the Dataset Planner.
4) Configure Codex or Claude Code as the coding host. Keep coding-host
   credentials separate from scientific API keys, and never put secrets in YAML.
5) Edit maieusis.yaml without inventing dataset facts.
6) Run `maieusis check` and resolve every zero-paid preflight error.
7) Explain the configured models, estimated calls, and output locations, then
   ask for my explicit approval before `maieusis run`.
8) After the run, open summary.md and the per-family scientific dossiers.
Do not execute the scientific analyses, inspect confirmation outcomes, or
weaken a provenance, isolation, or safety check.
```

### Manual route

Create the project directory *before* its virtual environment:

Set `PYTHON` to an installed Python 3.11, 3.12, or 3.13 executable and confirm
the reported version before continuing.

```bash
mkdir my-maieusis-project
cd my-maieusis-project
PYTHON=python3.11  # change to python3.12 or python3.13 when appropriate
"$PYTHON" --version
"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "maieusis[mcp,pdf,openai,anthropic]==0.1.0"
maieusis init
# Add lawful PDFs under papers/inbox, then edit maieusis.yaml.
maieusis check --project maieusis.yaml   # no paid model calls
maieusis run --project maieusis.yaml     # paid; run only after approval
```

Until the v0.1.0 package is available from PyPI, follow the
[source-install route](docs/INSTALLATION.md#install-from-source). The current
standard configuration uses distinct OpenAI and Anthropic API providers so
Question Owner work and independent review do not share a provider. See
[configuration](docs/CONFIGURATION.md) before the first paid run.

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

<p align="center"><em>A qualitative task-design comparison, not a performance, priority, or superiority ranking.</em></p>

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

<p align="center"><em>Published evidence supports formation traces; cross-paper abstraction turns those traces into reusable question-forming patterns.</em></p>

Maieusis uses current literature to motivate and contextualize questions, but
v0.1.0 does not certify novelty. Novelty remains `not_assessed` until dedicated
search and expert judgment are performed. Users must obtain source papers
lawfully; neither Maieusis nor its demos distribute the PDFs.

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

> **The current demos are neuroscience examples; Maieusis is for any
> scientific discipline and any scientific dataset.** A serious run still
> needs lawful, read-only access to enough documentation, metadata, code, or
> representative data for the Dataset Planner to inspect. We are testing
> Maieusis with researchers at different universities across climate science,
> physics, astronomy, finance, social science, and psychology, using datasets
> from their own fields. If you would like to join these scientific
> collaborations, contact **Draco (Yunlong) Xu** at `dracoxu@uchicago.edu`.

The two public demos preserve readable scientific artifacts while excluding
source PDFs, raw model payloads, credentials, and private runtime state. They
show question development and planning, not completed analyses or scientific
results.

- **[IBL Brain-Wide Map](demos/ibl/README.md):** six question families and
  planning dossiers developed against the International Brain Laboratory
  (IBL) Brain-Wide Map—a standardized, multi-laboratory collection of
  brain-wide recordings from mice performing a sensory decision-making task.
  See the [primary Nature paper](https://doi.org/10.1038/s41586-025-09235-0)
  and [official release guide](https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html).
- **[NLB MC_Maze-S](demos/nlb/README.md):** six question families, five
  planning dossiers, and one explicit validation-warning family developed
  against a pinned dataset from the Neural Latents Benchmark (NLB), a benchmark
  for latent-variable models of neural population activity. MC_Maze-S contains
  recordings from macaque primary motor cortex (M1) and dorsal premotor cortex
  (PMd) during delayed straight and curved reaches. See the
  [benchmark paper](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/979d472a84804b9f647bc185a877a8b5-Abstract-round2.html)
  and [pinned DANDI dataset](https://doi.org/10.48324/dandi.000140/0.220113.0408).

### IBL-002 — When does shared neural variability matter for a decision?

Neural populations fluctuate from trial to trial, but the size of those
fluctuations is only part of the story. Variability aligned with a
decision-relevant direction could affect a choice, while equally large
variability in an orthogonal direction may be largely irrelevant.

Maieusis developed two complementary variants: one asks whether alignment with
an independently defined decision direction predicts held-out choice and
reaction time beyond overall covariance magnitude; the other asks whether
pose and ongoing behavioral state better explain apparently decision-related
dimensions. Both produced provisionally accepted planning dossiers after
automated independent review. No analysis was executed, and novelty was not
assessed.

**[Explore both variants, their competing explanations, and what positive,
negative, or null outcomes would mean](demos/ibl/artifacts/questions/question_families_detailed.md#family-002-which-shared-variability-dimensions-matter-for-decisions).**
[See the study plan at a glance](demos/ibl/artifacts/families/covariance-alignment/dossier_detailed.md)
or [open the complete planning record](demos/ibl/artifacts/families/covariance-alignment/dossier.md).

### NLB-006 — What kind of neural stability supports generalization?

“Stable representation” can mean several things. Average population activity
for each reach may move while the relationships among reaches remain
reproducible; geometry that repeats within straight or curved reaches may
still fail to transfer between those movement demands.

Using MC_Maze-S recordings from primary motor cortex (M1) and dorsal premotor
cortex (PMd), Maieusis separated these claims into two variants. One compares
relational stability with centroid stability within matched reach conditions.
The other first requires reliable geometry within each demand, then asks
whether it transfers between straight and curved barrier-maze reaches or is
consistently remapped. Both produced provisionally accepted planning dossiers.
The dataset contains one recorded subject, the claims remain descriptive or
predictive rather than causal, and no analysis was executed.

**[Explore both variants, their competing explanations, and what positive,
negative, or null outcomes would mean](demos/nlb/artifacts/questions/question_families_detailed.md#family-006-which-geometric-stability-supports-generalization-in-reaching).**
[See the study plan at a glance](demos/nlb/artifacts/families/geometry-definition-generalization/dossier_detailed.md)
or [open the complete planning record](demos/nlb/artifacts/families/geometry-definition-generalization/dossier.md).

These two highlights are entry points, not a ranking. **Continue to the
[complete gallery](demos/QUESTIONS.md) for all 12 families and all 24 variants,**
including scientific background, competing explanations, assumptions,
positive/negative/null interpretations, planning outcomes, and the NLB
validation warning.

## Trust, limits, and community

An independently reviewed plan is not a result, and model agreement is not
truth. Dataset inspection can expose feasibility problems, but cannot by
itself establish novelty or importance. Human domain expertise remains
valuable, especially before any downstream analysis is authorized.

- [Method overview](docs/METHOD_OVERVIEW.md)
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

Use [CITATION.cff](CITATION.cff) for the exact software citation. A
version-specific Zenodo software DOI will be added after the immutable v0.1.0
GitHub release is archived; no DOI is invented in advance. A technical report
is planned after the software release and will receive a separate DOI and
preferred citation.

See [LICENSE](LICENSE), [NOTICE](NOTICE), [AUTHORS.md](AUTHORS.md),
[CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md).
