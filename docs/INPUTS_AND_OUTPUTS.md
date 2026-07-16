# Inputs, outputs, and run layout

## Required inputs

### Source papers

Provide PDF files under the configured `paperbank.inbox_dir`. Keep only one
version of each scientific work. Maieusis records content hashes and source
identity; it does not grant rights to use or redistribute a paper.

### Dataset context

Provide a stable dataset ID/link, documentation and/or metadata, an inspection
runtime, and at least one allowed inspection-resource description. A serious
planning branch also needs a real read-only dataset root or representative
sample and a source checkout the coding agent may inspect.

### Research intent

Choose one:

- `open`: no required topic prior;
- `topic_conditioned`: topic terms and optional description; or
- `seed_question`: a starting question.

Research intent shapes proposal framing. It does not certify feasibility and
does not replace literature or dataset evidence.

### Agent and model access

Configure Codex or Claude Code as the planner host plus supported model APIs for
generation, ownership, and independent review. Store credentials only outside
YAML.

## Human-readable products

| Product | What to inspect |
| --- | --- |
| Resolved inputs | The dataset identity, providers, host, and run mode actually resolved |
| PaperCase | What the source paper asked, why, and which source spans support the reconstruction |
| Formation trace | The paper's background → tension → data opportunity → question move |
| Question patterns | Compact cross-paper moves plus a detailed scientific-reading view of their source cases, formation logic, payoff, and limits |
| Research scope and topic brief | Current literature lanes, support, disagreement, and missing evidence |
| DatasetNarrative | Coarse proposal context with source-backed claims and explicit limits |
| QuestionFamilies | Compact and detailed views of every family and distinct variant before planning, including scientific motivation and unselected alternatives |
| Shortlist | Included, rejected, deferred, or revision-needed decisions |
| Family dossier | A compact/full scientific dossier plus a detailed reading guide to the refined question, dataset grounding, plan or rejection, review, interpretations, and limitations |
| Run summary | All family outcomes and the next action |

## Run directory

Each `maieusis run` creates one immutable-identity run below the configured
output root:

```text
<output-root>/<run-id>/
├── README.md
├── run_manifest.yaml
├── summary.md
├── inputs/resolved_inputs.md
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
├── dataset/dataset_narrative.md
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
└── artifacts/
```

Open the run `README.md` first. It is generated from the manifest and links the
currently valid products. `summary.md` is written after family closure.

The `artifacts/`, `receipts/`, and `stage_outputs/` trees support validation,
resume, and audit. They are not a substitute for the user-facing dossier.

Detailed pages are a deterministic post-finalization presentation add-on. They
read the persisted typed products already bound by scientific receipts and make
no model, API, or coding-agent call. A rendering warning cannot change the six
scientific stages, completion status, family outcome, compact files, or earned
authority; it only means the run is not yet presentation-ready. See the
[demo question gallery](../demos/QUESTIONS.md) for concrete examples.

## What is not an output

Maieusis v0.1.0 does not produce:

- a scientific finding or confirmatory result;
- a guarantee that a question is novel, important, or publishable;
- a locked analysis contract;
- permission to access restricted data; or
- an executed analysis or manuscript.
