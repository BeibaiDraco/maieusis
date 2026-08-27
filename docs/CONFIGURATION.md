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
placeholder — **they are transmitted with every request to those services.**

### The parser, and the field that depends on it

`parser` accepts `poppler_text` (or `poppler`), `docling`, and `auto`. Preflight verifies whichever
you choose: the Poppler binary must be on `PATH`, or Docling must be importable. `poppler_text` is
fast and adequate for well-structured PDFs. `docling` is slower and reconstructs prose from layout,
which matters for the field below; the published climate demonstration ran on it.

```yaml
paperbank:
  parser: docling
  citation_contexts_by_agent: true   # requires a parser that produces prose
  citation_context_agent_parallel: 4
```

**`citation_contexts_by_agent` is the most scientifically load-bearing option in this block.** It
replaces a regular-expression citation reader with a coding agent that reads each paper for the
passages a citation actually participates in. The measured difference is 5.7% coverage against 91%.
What is cited, and why, is what the PaperBank reconstructions are built from, so this changes the
evidence behind every question the run writes.

It is **coupled to the parser**, and the coupling is not enforced by the schema: the agent needs
continuous prose, so `citation_contexts_by_agent: true` with `poppler_text` produces far less than
it should. Pair it with `docling`. Preflight will not stop you; this paragraph is the warning.

Setting it also means a Claude Code agent is launched during the paper half **even when your planner
host is Codex** — the two are configured separately, and this one is always Claude Code. Be logged
in, or the reader yields nothing and the run records that honestly rather than failing.

It is **off by default**, and the example above turns it on. The starter profile ships it commented
out at the default so the switch is at least visible; nothing decides it for you.

**The published demonstrations were produced both ways, and that is worth knowing before you read
them side by side.** The climate run used `parser: docling` with
`citation_contexts_by_agent: true`; the three neuroscience runs used `parser: poppler_text` with it
`false`. Each pairing is internally correct — the warning above is exactly why the poppler legs
leave the agent off — but they are not the same evidence regime. A climate family's citation
contexts were read out of the papers' prose; a neuroscience family's came from the regular-expression
reader, and `examples/release/ibl-cleanroom.yaml` records what that cost: 8 of its 12 papers get
zero citation contexts. Weigh a reconstruction accordingly, and do not read a difference between the
two cohorts as a difference between the datasets.

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

  The starter profile ships `inspection_command: "uvx --with pynwb python"`, and that line makes two
  assumptions you may not share. `uvx` is the tool runner from [uv](https://docs.astral.sh/uv/), a
  Python package manager that is **not** among this project's prerequisites — if you do not have it,
  the command fails the first time the planner tries to open your data, which is deep inside a paid
  run. `pynwb` reads Neurodata Without Borders files; unless your dataset is one, it is the wrong
  package.

  **All four published demonstrations used the other field.** Each set `inspection_python` to a
  prepared virtualenv interpreter and left `inspection_command` empty — see any file under
  `examples/release/`. That is the route to copy if you want to know in advance that inspection will
  work: build an environment that can read your data, point `inspection_python` at its interpreter,
  and let preflight check it before you spend anything. The `uvx` line is an example of the
  multi-token form, not a recommendation.
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

### What the choice actually changes

Research intent decides **which literature the run searches for**, and everything downstream is
built on what that search returns. It is the highest-leverage field in this file.

In `topic_conditioned` and `seed_question` your terms are used as written. In `open` there are no
terms to use, so the run reads the dataset's own reviewed narrative and derives a scope from it: the
terms it will search, the construct families it will work in, and the parts of the field it will
stay out of. That derived scope is published with the run, at
`artifacts/literature/research_scope.md`, and its `Mode: open_inferred` line marks a run that chose
for itself. **Read it before anything built on it**, in your own runs as much as in the
demonstrations.

`scope_derivation` controls how a declared scope and a derived one combine:

| Value | Behaviour |
| --- | --- |
| `auto` | The default. Declared terms win outright and no model is asked; only a mode with nothing declared — that is, `open` — reaches the deriver. Leaves an existing configuration's retrieval byte-identical. |
| `augment` | Your terms are kept, in order and unrewritten, and derived terms are appended. For the case this exists for: you know three terms and want the rest filled in. |
| `never` | No model is asked on this path, ever. |

`never` turns off the MODEL, not derivation: an `open` run with nothing declared still falls back to
deterministic keyword extraction from the same narrative. **The only way to search exactly what you
wrote is to write it.**

The field was added after two release configurations were found searching the same eight generic
terms for two unrelated datasets — both candidate pools exhausted, and the dimensions the
independent reviewer grades on absent from the corpus entirely. A scope that fits neither dataset
costs every question downstream of it.

### Choosing, with a measured example

**An anchor is a commitment, not a hint.** The published demonstrations include the same dataset run
both ways, deliberately, because that is the only honest way to show what the choice does. Same
recordings, same twelve papers, same models in every role. One declared the single topic term
`noise correlations` with `scope_derivation: augment` — its term kept, derived terms appended
around it — and the other declared nothing with `scope_derivation: auto`, so the whole scope came
from the dataset. Those two fields are the entire difference between them.

They produced twelve question families **with no family in common** — not one shared title, not one
renamed pair. Individual questions do touch the same ground from opposite directions; what the
anchor changed is which contrasts each run built its six families around. It did not narrow the run
to a subset of the open one. Compare
[the anchored run](../demos/ibl/README.md) with [the open one](../demos/ibl-open/README.md) before
you decide which your own dataset wants.

So: declare terms when you know the contrast you are after and want six questions concentrated
there, and accept that a term which does not suit the dataset will steer all of them away from what
was worth asking, with nothing downstream to recover them. Leave it open when you want the dataset
to propose the territory — and then read the derived scope page, because that is where the decision
you delegated is written down.

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

### What the published demonstrations actually used

The examples above say `<model-id>` because Maieusis does not ship a model list and does not
prefer a vendor — you pin what your accounts can reach. But a reader filling this in for the first
time deserves to see one real, complete answer rather than seven placeholders, so here is the
assignment every one of the four published runs used. The profiles are in `examples/release/`.

| Role | Provider | Model |
| --- | --- | --- |
| `paperbank.extraction` | openai | `gpt-5.6-luna` |
| `models.pattern` | openai | `gpt-5.6-sol` |
| `models.questioner` | openai | `gpt-5.6-sol` |
| `models.narrator` | openai | `gpt-5.6-luna` |
| `models.topic` | openai | `gpt-5.6-terra` |
| `models.owner` | openai | `gpt-5.6-terra` |
| `models.reviewer` | **anthropic** | `claude-sonnet-5` |
| `models.novelty_reviewer` | openai | `gpt-5.6-terra` |

Read the shape rather than the names, because the names go stale and the shape is the argument.
The reviewer sits on the other vendor from the Owner, which is what makes the independence
structural rather than a promise. The two roles that write the science — pattern induction and
question generation — get the strongest model, and the roles that summarise get a cheaper one.
Nothing here is a recommendation of a vendor; substitute the equivalents your accounts can reach.

**Both coding hosts were exercised, and by the same set.** Climate and the two IBL runs ran the
dataset planner on Codex with `coding_model: gpt-5.6-terra`; NLB ran it on Claude Code with
`coding_model: claude-opus-4-8`. Everything else in those four profiles is identical, so the pair
is also the evidence that the host is a choice and not a hidden dependency.

### Which profile should I use?

| Profile | Use it when |
| --- | --- |
| `maieusis.yaml` | **Start here.** This is what `maieusis init` writes into your project, and it is the configuration shape that produced the published demonstrations. It runs the Codex planner. |
| `maieusis.claude-planner.example.yaml` | You run the Claude Code planner instead. The same settings apart from the three `coding_*` lines; some comments are worded for that host. |
| `examples/release/*-cleanroom.yaml` | **Not a starting point.** These are the byte-qualification profiles used to prove the published package ran untouched, and they are pinned to that job: the sealer compares each one leaf by leaf against the profile it recorded, so an edit is a different candidate rather than a customised run. They are not reduced — `max_families: 6` and `variants_per_family: 2`, the same shape as the recommended profile — because they *are* what produced the published demonstrations. Start from `maieusis.yaml` and change it freely. |

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

### Per-role thinking and effort

Every entry in `models` may carry two more fields beyond `provider` and `model`, and both reach the
provider on the real run path:

```yaml
models:
  reviewer:
    provider: anthropic
    model: "<model-id>"
    thinking: enabled     # inherit | enabled | disabled
    effort: high          # inherit | minimal | low | medium | high | xhigh
```

`inherit` is the default for both and it means *send nothing* — the provider applies its own
default for that model. That is deliberate: a named value restates one vendor's behaviour and
silently inverts another's, so the neutral option had to be a real member rather than a guess.

Set them per role rather than globally. The roles differ in what they are for — a reviewer that
must find a flaw in someone else's plan is not the same job as an extractor pulling fields out of a
PDF — and this is where that difference is expressed.

## Credentials and cost authorization

The standard OpenAI/Anthropic arrangement uses:

| Variable | Needed when |
| --- | --- |
| `OPENAI_API_KEY` | Any scientific role uses the OpenAI provider |
| `ANTHROPIC_API_KEY` | Any scientific role uses the Anthropic provider |
| `CLAUDE_CODE_OAUTH_TOKEN` | The Claude Code host requires token-based login in its isolated environment |
| `ELICIT_API_KEY` | `literature.source_profile` is `elicit` or `hybrid`, or `auto` should enable Elicit |
| `OPENALEX_API_KEY` | You hold an OpenAlex key. OpenAlex is **usage-billed**; the product reads this on the paper-ingest and topic-retrieval paths |
| `OPENALEX_EMAIL`, `CROSSREF_EMAIL` | Polite-pool contact addresses. These are TRANSMITTED with every request to those services — do not use an address you would not publish |
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
  research_field: ""  # see below; the remedy for a starved-term preflight FAIL
  openalex_email: you@example.org
  fulltext_enrichment: false  # abstract-only in this version; see below
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
- **Topic evidence is abstract-only in this version, and `fulltext_enrichment`
  defaults to `false`.** The lane fetches lawful open text only where a source
  carries an explicit rights assertion the run can verify, and on every leg
  measured so far no source has: across 24 recorded legs, 113 attempts enriched
  0 records (no eligible rights assertion 59, rights rejected 41, HTTP error 9,
  media type rejected 4). Setting it to `true` is supported and costs a few HTTP
  calls; if the run again enriches nothing, its `fulltext_enrichment` stage
  receipt says so in words rather than leaving four counters to be read. Either
  way, missing full text remains visible and may lower authority.
- Prior-art review is enabled in the shipped profile. The schema default is `false`, so a project
  file that omits the `novelty` block loads unchanged and constructs no web provider.
- The web-search lane makes paid third-party search calls. `maieusis check` discloses the tool-fee
  reservation and its ceiling before any spend, and refuses when the ceiling cannot fund the
  configured run shape.

### When preflight fails on your topic terms

`literature.topic_term_pools` is a hard `FAIL`, and it is the one most likely to stop a first
scientific run. It fires when your declared terms cannot fill a literature lane — the message names
each starved term with the size of the pool behind it — and the run is refused rather than allowed
to proceed on a corpus that cannot support the questions it would write.

`literature.research_field` is the remedy the message assumes you have. Setting it ANDs a field
identity onto the scholarly query, which changes *which* works a term matches rather than how many
are asked for: a term that is ambiguous across fields stops competing with an unrelated literature.
Leave it empty and the search is unscoped, which is right for a term that is already specific and
wrong for one that is not.

The other two remedies are to choose terms with a literature behind them, or to run `open` and let
the scope be derived from the dataset, which is the case the derived-scope page above is about.

### The novelty block's three hard failures

`novelty.enabled: true` is the shipped default and it brings three preflight failures the block
itself does not mention:

- **`novelty.literature_enabled`** — prior-art review has nothing to review without
  `literature.enabled: true`. Enabling one and not the other is refused.
- **`novelty.independent_reviewer`** — `models.questioner` and `models.reviewer` may not resolve to
  the same provider-and-model identity. This is stricter than the general independence rule, and it
  exists because a model reviewing its own proposal for novelty is not a review.
- **`novelty.web_grounding.strict_capability`** — **only `anthropic` can run the web scout.** The
  check runs before any client is constructed, deliberately, so an unsupported adapter cannot even
  open a connection on a lane whose tool-fee ceiling it could not enforce. A scout pinned to OpenAI
  fails preflight rather than silently running without grounding.

**The web scout is a paid, metered lane** with its own fee ceiling, separate from model tokens.
Preflight prints the reservation it will hold before you authorize the run; read that number.

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
- **Six is also a ceiling, not only a request.** The run takes the smaller of `max_families` and a
  built-in six, so raising the field above six changes nothing — the extra families are never
  proposed. Lowering it works as you would expect. The published demonstrations are six by two,
  which is the largest shape this version produces.
- `max_parallel_family_workers` bounds concurrent family branches.
- `max_revise_rounds` bounds Owner–Planner repair after review.
- Leave `shortlist_path: null` and `target_family_ids: []`; external shortlist
  injection and family targeting are not supported by the product path.
- Do not change configuration while a run is active. A later `resume` reuses
  work only when all bound inputs still match.

### What happens when a bound is actually reached

A limit you are asked to set is only half a fact until the page says what happens on the other
side of it. `max_revise_rounds` is explained on [supervising a run](RUN_SUPERVISION.md) — the run
stops, it is labelled a fault, resuming is valid, and raising the budget is the lever. The other
three:

- **`novelty.web_grounding.hard_run_tool_spend_ceiling_micro_usd` degrades; it does not abort.**
  When the next reservation would cross the ceiling, that variant's prior-art review continues
  without the web lane and the assessment records that the lane was unavailable. Nothing is
  cancelled and no family is closed by it. Preflight is where it stops you: it refuses up front
  when the ceiling cannot fund the configured run shape, and the arithmetic it uses is
  `max_families * variants_per_family * 2 * max_searches_per_scout * 10000 <= ceiling`. Raise
  breadth without raising the ceiling and preflight fails — which is the intended order, since
  finding out mid-run costs money.

- **`dataset.inspection_runtime.timeout_seconds` ends that planner invocation**, and the family
  branch closes as an infrastructure fault rather than a scientific verdict. It is a wall-clock
  budget for the whole invocation, capped at 2400 seconds; `resume` may re-enter the branch.

- **`dataset.inspection_runtime.max_turns` applies on Claude Code only.** The Codex runner's
  budget policy is timeout-only and imposes no turn cap, so on a Codex planner host this field is
  inert — it is validated and recorded, and nothing enforces it. Worth knowing before you tune it
  to fix a run that is really hitting the timeout.

Both `max_turns` and `timeout_seconds` are deliberately excluded from the inputs a resume binds
against, so changing either does not invalidate reuse of completed work. They bound how long a
branch may take; they are not part of what it means.

## What a run costs, as far as we can tell you

**Maieusis does not meter token cost.** No run-wide accounting exists after the fact, which is a
real gap and is recorded as one. Read your spend from your provider's dashboard. What follows is
what the published demonstrations actually took, so you have something to scale from.

| Run | Papers | Families | Wall clock | Web-search fee |
| --- | --- | --- | --- | --- |
| Climate | 20, read fresh | 6 × 2 | 1 h 56 m | $0.46 |
| IBL | 12, read fresh | 6 × 2 | 1 h 50 m | $0.59 |
| IBL open | 12, imported | 6 × 2 | 50 m | $0.58 |
| NLB | 12, imported | 6 × 2 | 1 h 06 m | $0.45 |

The last column is the only exact figure in this table, and it is exact because it is the only lane
with a rate card: each receipt records the searches the provider reported and the rate they were
charged at, so the fee is a multiplication rather than an estimate. Four legs came to $2.08 in
total. Everything else on this page is wall clock, which you can measure, and token cost, which we
do not meter.

The paper half dominates a first run: the two legs that imported an existing paper bank finished in
roughly half the time of the ones that read the PDFs themselves. Wall clock beyond that depends
mostly on how deep the planner goes into your dataset, which you do not control directly.

Three levers actually change the bill:

- **`run.max_families`** — the biggest one. Two families cost roughly a third of six. Start there.
- **`paperbank.inbox_dir`** — the number of PDFs, and their length. This is the most expensive
  single stage on a first run.
- **`novelty.web_grounding`** — the only lane with an exact, enforced price. You set the ceiling,
  preflight prints the reservation it will hold, and the run cannot exceed it. Turning it off is
  the one saving you can predict exactly.

Everything else is provider token pricing on a workload whose size depends on your data. If you
need a number before committing, run once at `max_families: 2` and read the real figure off your
dashboard.

## Validate before spending

Run:

```bash
maieusis check --project maieusis.yaml
```

Preflight launches no coding agent and runs no stage. It does send one minimal request per configured provider — `max_tokens: 1`, a single full stop for content — because an API key is not a balance:
a key that authenticates but cannot be billed would otherwise fail deep inside a paid run. Expect a
fraction of a cent per provider. It reports failures, warnings, estimated model calls and planner
launches, and external egress.
Resolve every failure and review every warning before authorizing
`maieusis run`.

---

[Documentation home](INDEX.md) · [Manual setup](MANUAL_SETUP.md) ·
[Inputs and outputs](INPUTS_AND_OUTPUTS.md) · [Troubleshooting](TROUBLESHOOTING.md)
