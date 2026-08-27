# Inputs, outputs, and run layout

[Documentation home](INDEX.md) · [Configuration](CONFIGURATION.md)

Maieusis takes source literature, target-dataset context, research intent, and
agent access. It returns visible question-development products and one planning
dossier or honest non-proceed outcome for each attempted family. It does not
return a scientific result.

## Required inputs

### Source papers

Place lawfully obtained PDFs under `paperbank.inbox_dir`. Keep one file per
scientific work. Maieusis records file identity and source-addressable evidence;
it does not grant rights to use or redistribute a paper.

### Target-dataset context

Provide:

- a stable dataset identifier;
- a substantive official link, readable local documentation, or both;
- a real read-only dataset directory or representative sample;
- when needed, an inspection Python executable or command with the required
  dataset libraries;
- plain-language descriptions of the resources the planner may inspect; and
- a Maieusis Git checkout with a valid `HEAD` for planner source-integrity
  checks; a clean checkout is strongly recommended. Dataset loading code is a
  separate read-only inspection resource when the planner needs it.

The Question Scientist receives a coarse, source-backed DatasetNarrative.
Exact units, joins, events, hierarchy, missingness, and estimability are checked
later in isolated planning branches.

### Research intent

Choose one mode:

- `open`: no required topic prior;
- `topic_conditioned`: topic terms plus an optional description; or
- `seed_question`: a starting question that may be clarified but must not be
  silently replaced.

Research intent guides proposal framing. It is not scientific evidence or a
feasibility decision.

### Agents and credentials

Configure Codex or Claude Code as the Dataset Planner host. Standard scientific
operation also requires model APIs, with different providers for the Question
Owner and independent reviewer. Keep all credentials outside YAML.

## What to read after a run

Start with these files in order:

1. `README.md` — the run state and links to currently valid products;
2. `summary.md` — every attempted family and its outcome;
3. `questions/question_families_detailed.md` — the scientific background,
   meaning, and variants of every proposed family;
4. `families/<family-slug>/dossier_detailed.md` — a reading guide to one
   family's question, dataset grounding, plan, review, and limits; and
5. `families/<family-slug>/dossier.md` — the full plan, controls, estimands,
   and limits.

**Items 1 and 2 exist only in your own run directory.** The published demonstrations do not carry
a run `README.md` or a `summary.md`: those two narrate a live run — which stages ran, what state it
reached, which products are currently valid — and a curated tree published months later would be
narrating a run nobody can act on. What the demonstrations publish instead is the reader-facing
half, items 3 through 5, plus the pages this project writes over them. So when another page here
tells you to open `summary.md` first, it means the run on your machine; in a demonstration, start
at [the questions page](../demos/ALL_QUESTIONS.md) or the run's own landing page.

Both carry labels stating how much weight the work can bear;
[reading the labels](LABELS.md) lists every one with its permitted values.

**Read both; neither contains the other.** `dossier_detailed.md` is the reading
guide, and it alone carries two things you will want: what the planner actually
inspected in the data, and the Question Owner and independent reviewer in their
own words. `dossier.md` carries the complete plan itself — every variant's
design, controls, estimands, diagnostics, and interpretation limits — but not
the inspection evidence and not the review. The names suggest one is a subset of
the other. They are not. Neither is an executed analysis.

## Human-readable products

| Product | What it helps you inspect |
| --- | --- |
| Resolved inputs | Which dataset, papers, providers, host, and run settings were actually used |
| PaperCase | What a source paper asked and which published spans support the reconstruction |
| Formation trace | How published background, tension, data opportunity, and inferential move connect to the paper's question |
| Question patterns | Reusable cross-paper question-forming moves, their source cases, scientific payoff, and transfer limits |
| Research scope and topic evidence | Current literature lanes, supporting and conflicting evidence, and evidence gaps |
| DatasetNarrative | Coarse proposal context with source-backed claims and explicit unknowns |
| QuestionFamilies | Every family and variant before planning, including scientific motivation, alternatives, assumptions, and possible result meanings |
| Shortlist | Which families proceed to planning and which are rejected, deferred, or need revision |
| Family dossiers | The refined question, target-dataset evidence, plan or non-proceed reason, independent review, claim ceiling, and limitations |
| Run summary | The outcome of every attempted family and the next action |

Rejected, deferred, warning, and mixed outcomes remain visible. A run can be
technically complete without every family becoming an accepted plan.

## Run directory

Each `maieusis run` creates a new run identity beneath `run.output_root`:

```text
<output-root>/<run-id>/
├── README.md
├── run_manifest.yaml
├── summary.md
├── inputs/
│   └── resolved_inputs.md
├── paperbank/
│   ├── paperbank_summary.md
│   ├── papers/*.md
│   ├── formation_traces/*.md
│   ├── question_patterns.md
│   └── question_patterns_detailed.md
├── literature/
│   ├── research_scope.md
│   ├── retrieval_summary.md
│   └── topic_evidence_summary.md
├── dataset/
│   └── dataset_narrative.md
├── questions/
│   ├── question_families.md
│   ├── question_families_detailed.md
│   └── shortlist.md
├── families/<family-slug>/
│   ├── dossier.md
│   ├── dossier_detailed.md
│   ├── family_completion.yaml
│   └── artifacts/
├── receipts/
├── stage_outputs/
├── artifacts/
├── corpus/                     # the reviewed context the proposal stage was given
├── diagnostics/                # per-gate verdicts, including the ones that ACCEPTED
├── presentation/               # the reader-facing add-on's own receipt
├── imports/                    # present only when a stage was imported from another run
├── <run-id>/branches/          # one isolated workspace per shortlisted family
└── launch-<family>/            # one per launched planning branch
```

The last three are worth knowing about before you go looking for something.

`diagnostics/` holds a record for every gate that ran, and it records **accepts as well as
refusals** — a gate that passed silently is a gate you cannot audit later. `<run-id>/branches/`
repeats the run id inside the run directory; that is the branch workspace, not a second run, and
every leg has one. `imports/` appears only when a stage was reused from an earlier run rather than
recomputed, and it carries the source run id and the receipt digest that bound the reuse — its
absence is how you know a stage was produced fresh.

The compact pattern and question pages are useful for scanning. Their
`*_detailed.md` companions add scientific background, interpretation, and
links without changing the underlying scientific decisions.

Receipts, manifests, stage outputs, and hidden audit files support integrity,
status, and safe resume. They are useful for diagnosis and provenance, but the
family dossier is the main scientific reading surface. Do not hand-edit any of
these files to change an outcome or force reuse.

If a detailed page cannot be rendered, the scientific run state and compact
products remain unchanged. `maieusis status` reports the situation, and
`maieusis resume` can regenerate the readable detailed pages without repeating
scientific model work when all scientific stages remain reusable.

## What Maieusis does not output

Maieusis v0.1.1 does not produce:

- a scientific finding or confirmatory result;
- a guarantee that a question is novel, important, true, or publishable;
- a locked downstream analysis contract;
- permission to access or redistribute restricted material;
- an executed analysis; or
- a manuscript.

See the [method overview](METHOD_OVERVIEW.md) for how these products are formed
and [provenance](PROVENANCE.md) for how to interpret recorded authority.

---

[Documentation home](INDEX.md) · [Method overview](METHOD_OVERVIEW.md) ·
[Provenance](PROVENANCE.md) · [Troubleshooting](TROUBLESHOOTING.md)
