# Configuration and credentials

[Documentation home](INDEX.md) · [Agent-guided setup](AGENT_GUIDED_SETUP.md) ·
[Manual setup](MANUAL_SETUP.md)

`maieusis init` creates a commented `maieusis.yaml`. Edit that generated file
rather than starting from an empty document. It contains non-secret run
settings; API keys and coding-host credentials belong in the runtime
environment.

Unknown YAML fields fail validation, and key-shaped secret values are rejected.
Always run `maieusis check --project maieusis.yaml` after editing.

## Configuration map

| Section | What it controls |
| --- | --- |
| `mode` | `standard` scientific operation or an explicitly non-scientific `subscription_only_demo` |
| `paperbank` | PDF inbox, parser, extraction model, citation processing, and paper concurrency |
| `dataset` | Dataset identity, source documents, read-only inspection runtime, and allowed resources |
| `research_intent` | Open, topic-conditioned, or seed-question direction |
| `models` | Scientific API roles, independent reviewer, coding host, and coding-host model |
| `literature` | Public literature retrieval, open-full-text enrichment, and optional Elicit use |
| `novelty` | Prior-art review and its bounded web-search lane; enabled in the shipped profile |
| `run` | Output directory, requested family/variant breadth, concurrency, and revision limit |

Paths are interpreted from the directory in which you run the CLI. The safest
practice is to run every command from the project directory containing
`maieusis.yaml`.

## Operation mode

Use:

```yaml
mode: standard
```

for a scientific question-development run. Standard mode requires real model
providers and a real Codex or Claude Code planner host.

`subscription_only_demo` replaces scientific API roles with mock providers and
disables literature retrieval. It demonstrates workflow mechanics only; it
does not produce scientific-quality questions or independent scientific
review.

## PaperBank

At minimum, point `inbox_dir` at the source PDFs and name an extraction
provider/model:

```yaml
paperbank:
  inbox_dir: papers/inbox
  extraction:
    provider: openai
    model: "<model-id>"
  parser: poppler_text
  evidence_mode: source_span
  max_workers: 4
  cited_literature: true
  select_key_citations: true
  crossref_mailto: you@example.org
  openalex_email: you@example.org
```

`max_workers` bounds concurrent paper processing. Contact emails help Crossref
and OpenAlex identify polite API use; use your real email rather than the
placeholder.

The optional `paperbank.import_from_run` route is for receipt-verified reuse of
a completed PaperBank. It requires both a source run path and the expected
receipt SHA-256. Do not use it for an ordinary first run.

## Dataset identity and inspection

The proposal stage receives only coarse, source-backed dataset context. Exact
schema and feasibility inspection occurs later in isolated family branches.

```yaml
dataset:
  seed:
    dataset_id: my_dataset
    link: https://example.org/my-dataset
    docs:
      - inputs/dataset_overview.md
  inspection_runtime:
    dataset_root: /absolute/path/to/read-only/sample
    dataset_access_mode: external_readonly
    inspection_python: /absolute/path/to/inspection-env/bin/python
    inspection_command: ""
    inspection_pythonpath: ""
    inspection_extra_env: {}
    source_tree_root: /absolute/path/to/clean/maieusis-checkout
    max_turns: 40
    timeout_seconds: 1800
  allowed_inspection_resources:
    - official dataset documentation
    - local metadata tables and small representative samples
    - public loading and preprocessing code
  official_online_resources:
    - https://example.org/my-dataset/docs
```

Important rules:

- Give `seed.link`, readable local `seed.docs`, or both. A link should resolve
  to substantive dataset information, not only a metadata stub.
- `external_readonly` requires `dataset_root`.
- `inspection_python` and `inspection_command` are mutually exclusive. Set one
  when the dataset requires a specific interpreter or multi-token environment
  command; leave both blank only when the coding host's environment already has
  everything needed for bounded inspection.
- `allowed_inspection_resources` requires at least one non-blank description.
- `source_tree_root` must point to a Maieusis Git checkout with a valid `HEAD`
  when the installed package is run outside that checkout. Use a clean
  checkout so the recorded identity is easy to interpret. Preflight verifies
  the Git state; the operator is responsible for selecting the Maieusis source
  tree rather than a dataset-code repository. Maieusis digests the full state
  before and after planner work to detect source changes.
- `timeout_seconds` applies to each planner invocation and cannot exceed 2400
  seconds.
- `max_turns` applies to Claude Code. Codex is bounded by
  `timeout_seconds` rather than a Maieusis turn counter.

Do not put the dataset inside the run-output directory. Keep source data and
documentation read-only.

## Research intent

Choose exactly one mode:

### Open

```yaml
research_intent:
  mode: open
  topic_terms: []
  topic_description: ""
  seed_question: ""
```

### Topic-conditioned

The example below is deliberately domain-neutral. Replace it with concepts and
distinctions from your own field.

```yaml
research_intent:
  mode: topic_conditioned
  topic_terms:
    - system stability
    - response heterogeneity
  topic_description: >-
    Develop questions about how relationships change across conditions while
    separating the target mechanism from measured alternative explanations.
  seed_question: ""
```

### Seed question

```yaml
research_intent:
  mode: seed_question
  topic_terms: []
  topic_description: ""
  seed_question: >-
    Which dataset-supported distinctions would make this broad question
    scientifically discriminating?
```

Research intent guides proposal framing. It is not evidence, a feasibility
certificate, or permission to bypass literature and dataset inspection.

## Scientific model roles

Every role records an explicit provider and model:

| Field | Role |
| --- | --- |
| `paperbank.extraction` | Extract source-bound PaperCases from PDFs |
| `models.pattern` | Induce cross-paper question-forming patterns |
| `models.questioner` | Generate QuestionFamilies and variants |
| `models.narrator` | Build the coarse DatasetNarrative |
| `models.topic` | Synthesize current topic evidence |
| `models.owner` | Protect scientific intent inside a family branch |
| `models.reviewer` | Independently review the plan and scientific closure |
| `models.novelty_reviewer` | Review prior art (optional; falls back to `models.reviewer`) |

Example:

```yaml
models:
  pattern: {provider: openai, model: "<model-id>"}
  questioner: {provider: openai, model: "<model-id>"}
  narrator: {provider: openai, model: "<model-id>"}
  topic: {provider: openai, model: "<model-id>"}
  owner: {provider: openai, model: "<model-id>"}
  reviewer: {provider: anthropic, model: "<model-id>"}
  novelty_reviewer: {provider: openai, model: "<model-id>"}
  coding_host: claude_code
  coding_model: "<claude-model-id-or-alias>"
  coding_reasoning_effort: high
  allow_pro_model: true
```

`allow_pro_model` opens the gate for pro-tier models. The shipped profile pins
two pro-tier roles, so it sets this to `true`; leaving it `false` while pinning
such a model fails preflight unless `MAIEUSIS_ALLOW_PRO_MODEL` is exported. The
field is folded into every stage configuration digest, so changing it in an
existing project invalidates resume reuse for that project.

`models.novelty_reviewer` is optional and falls back to `models.reviewer`.
Pinning it separately is worth doing: on one measured live leg, half the
prior-art reviews were lost when this role shared the reviewer's model, because
a safety classifier fired on that model's reasoning output.

In standard mode, `models.owner.provider` and `models.reviewer.provider` must
be different. Other roles may share a provider, but every configured model
must be available to your account. Maieusis does not silently substitute a
different model.

Pin full model IDs rather than mutable aliases: the configuration file is part
of a run's scientific provenance, and run records additionally persist the
actually resolved CLI/model identity.

### Which profile should I use?

| Profile | Use it when |
| --- | --- |
| `maieusis.yaml` | **Start here.** This is what `maieusis init` writes into your project, and it is the configuration shape that produced the published demonstrations. It runs the Codex planner. |
| `maieusis.claude-planner.example.yaml` | You run the Claude Code planner instead. The same settings apart from the three `coding_*` lines; some comments are worded for that host. |
| `examples/release/*-cleanroom.yaml` | **Not a starting point.** Deliberately reduced byte-qualification inputs used to prove the published package ran untouched. They request two families, so they will not reproduce the six-family demonstrations. |

There is no separate "development" profile in the public distribution. The
recommended profile is the scientific one; if you want a cheaper first run,
lower `run.max_families` rather than changing the model pins, so what you
measure is still the configuration the demonstrations used.

## Coding-agent host

The coding host is a subscription CLI, not a scientific token-API role. Codex
and Claude Code are both fully supported hosts; choose per run, not per era.

For Codex:

```yaml
models:
  coding_host: codex
  coding_model: "<codex-model-id>"
  coding_reasoning_effort: high  # REQUIRED: minimal | low | medium | high | xhigh
```

For Claude Code:

```yaml
models:
  coding_host: claude_code
  coding_model: "<claude-model-id>"
  coding_reasoning_effort: high  # OPTIONAL: low | medium | high | xhigh; omit for the CLI default
```

The host, model, and reasoning effort are explicit run inputs. Do not change
them during a run.

## Credentials and cost authorization

The standard OpenAI/Anthropic arrangement uses:

| Variable | Needed when |
| --- | --- |
| `OPENAI_API_KEY` | Any scientific role uses the OpenAI provider |
| `ANTHROPIC_API_KEY` | Any scientific role uses the Anthropic provider |
| `CLAUDE_CODE_OAUTH_TOKEN` | The Claude Code host requires token-based login in its isolated environment |
| `ELICIT_API_KEY` | `literature.source_profile` is `elicit` or `hybrid`, or `auto` should enable Elicit |
| `MAIEUSIS_ALLOW_PRO_MODEL=1` | You deliberately authorize a model classified as expensive/pro |

The supported user-level location for a clean scientific project is:

```text
~/.config/maieusis/runtime.env
```

An existing process environment variable takes precedence over this file.
Keep credentials out of project-local `.env` files: the generated project
contract is designed around the user-level location, which also reduces the
risk of accidental commits and coding-agent exposure.

`models.allow_pro_model: true` and `MAIEUSIS_ALLOW_PRO_MODEL=1` both authorize
gated models. The shipped profile sets this to `true` because it pins pro-tier roles. Use the YAML value when you want that
choice recorded with the project; use the environment variable when you want a
deliberate, run-specific authorization that leaves the project file alone.

## Literature sources and novelty

```yaml
literature:
  enabled: true
  openalex_email: you@example.org
  fulltext_enrichment: true
  source_profile: public  # public | auto | elicit | hybrid

novelty:
  enabled: true
  direct_recap_threshold: 0.9
  close_prior_threshold: 0.7
  max_candidates: 5
  web_grounding:
    enabled: true
    scout: {provider: anthropic, model: "<model-id>"}
    max_searches_per_scout: 3
    max_leads_per_scout: 5
    max_output_tokens: 21000
    rate_card: anthropic_direct_web_search_20250305
    # Micro-USD: 1000000 = one US dollar. This ceiling bounds THIRD-PARTY WEB SEARCH TOOL FEES
    # ONLY. It does not cap model tokens, the planner host, or anything else you are billed for.
    hard_run_tool_spend_ceiling_micro_usd: 1000000
```

- `public` uses free public scholarly sources.
- `auto` uses Elicit only when `ELICIT_API_KEY` is available; otherwise it stays
  on public sources.
- `elicit` and `hybrid` require `ELICIT_API_KEY` and fail preflight without it.
- Full-text enrichment uses lawful open text when available. Missing full text
  remains visible and may lower authority.
- Prior-art review is enabled in the shipped profile. The schema default is `false`, so a project
  file that omits the `novelty` block loads unchanged and constructs no web provider.
- The web-search lane makes paid third-party search calls. `maieusis check` discloses the tool-fee
  reservation and its ceiling before any spend, and refuses when the ceiling cannot fund the
  configured run shape.

## Run breadth and bounds

```yaml
run:
  output_root: runs/my-run
  shortlist_path: null
  target_family_ids: []
  max_families: 6
  variants_per_family: 2
  max_parallel_family_workers: 3
  max_revise_rounds: 3
```

- `max_families` and `variants_per_family` request breadth; they do not promise
  that every requested item will become an accepted plan.
- `max_parallel_family_workers` bounds concurrent family branches.
- `max_revise_rounds` bounds Owner–Planner repair after review.
- Leave `shortlist_path: null` and `target_family_ids: []`; external shortlist
  injection and family targeting are not supported by the product path.
- Do not change configuration while a run is active. A later `resume` reuses
  work only when all bound inputs still match.

## Validate before spending

Run:

```bash
maieusis check --project maieusis.yaml
```

Preflight performs no paid model or coding-agent call. It reports failures,
warnings, estimated model calls and planner launches, and external egress.
Resolve every failure and review every warning before authorizing
`maieusis run`.

---

[Documentation home](INDEX.md) · [Manual setup](MANUAL_SETUP.md) ·
[Inputs and outputs](INPUTS_AND_OUTPUTS.md) · [Troubleshooting](TROUBLESHOOTING.md)
