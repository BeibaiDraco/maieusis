# Configuration and credentials

`maieusis.yaml` contains non-secret, versioned run configuration. Runtime
credentials come from environment variables or an untracked runtime file.
Unknown fields fail validation.

## Configuration sections

| Section | Controls |
| --- | --- |
| `paperbank` | PDF inbox, parser, extraction provider/model, evidence mode, paper worker cap, citation retrieval |
| `dataset` | stable identity/link/docs, read-only inspection root/runtime, allowed and official resources |
| `research_intent` | open, topic-conditioned, or seed-question mode |
| `models` | questioner, pattern, narrator, topic, owner, reviewer, coding host, and coding-host model profile |
| `literature` | free/public retrieval, full-text enrichment, optional paid source profile |
| `novelty` | currently off; unsearched novelty is `not_assessed` |
| `run` | output root, family/variant counts, worker cap, revision budget |

Paths are resolved from the project config. Secrets are rejected if they appear
inside YAML.

## Model roles

Each serious role records an explicit provider and model:

- `models.questioner`: Question Scientist family generation;
- `models.pattern`: cross-paper question-pattern induction;
- `models.narrator`: coarse source-backed DatasetNarrative;
- `models.topic`: topic evidence and field-state synthesis;
- `models.owner`: branch-local Question Owner;
- `models.reviewer`: independent reviewer; use a provider distinct from owner;
- `models.coding_host`: `codex` or `claude_code` Dataset Planner;
- `models.coding_model`: explicit subscription coding-agent model;
- `models.coding_reasoning_effort`: Codex-only reasoning effort; omit it for Claude Code.

The paper extractor is configured separately under
`paperbank.extraction`. PaperCase, citation, and formation-trace work is bound
to the paper-stage receipt along with pattern and reviewer identities. Changing
a bound model invalidates reuse.

The release validation uses two explicit profiles:

| Role | Luna clean gate | Final quality |
| --- | --- | --- |
| PaperCase, citations, formation trace | `gpt-5.6-luna` | `gpt-5.6-luna` |
| Pattern induction | `gpt-5.6-luna` | `gpt-5.6-sol` |
| DatasetNarrative | `gpt-5.6-luna` | `gpt-5.6-luna` |
| Topic synthesis | `gpt-5.6-luna` | `gpt-5.6-terra` |
| Question Scientist | `gpt-5.6-luna` | `gpt-5.6-sol` |
| Question Owner | `gpt-5.6-luna` | `gpt-5.6-terra` |
| Independent reviewer | `claude-opus-4-8` | `claude-opus-4-8` |
| Dataset Planner | Claude Code Opus | Codex CLI `gpt-5.6-terra`, effort `high` |

These exact model IDs are release provenance, not a promise of availability to
every account. Use only models your provider authorizes. Never allow a silent
fallback to a different or more expensive model.

## Credentials

Current standard release profiles use:

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI scientific API roles |
| `ANTHROPIC_API_KEY` | Anthropic scientific API roles |
| `CLAUDE_CODE_OAUTH_TOKEN` | relocated Claude Code planner host, when selected |
| `MAIEUSIS_ALLOW_PRO_MODEL=1` | explicit gate for configured expensive/pro roles |
| `ELICIT_API_KEY` | optional paid literature source; not used in the release demos |

The final-quality profile also requires a ChatGPT-authenticated Codex CLI. Its
cleanroom may use an explicit `CODEX_HOME` pointing at the already-authenticated
Codex home while `HOME` itself remains fresh; this path is not a secret, but its
`auth.json` is. Terra requires `codex-cli >=0.144.4` for this release profile.

Create API keys in the provider's official console. OpenAI recommends loading
API keys from environment variables or a key-management service; see its
[API authentication reference](https://platform.openai.com/docs/api-reference/authentication).
Never expose a key in client-side code, YAML, logs, screenshots, or model
prompts.

Runtime-file search order is:

1. existing process environment;
2. project `.env.local`;
3. project `runtime.env`;
4. project `.env`;
5. `~/.config/maieusis/runtime.env`.

The user-level file is recommended. Ensure project-local secret files are
ignored by Git.

## Literature and novelty

`literature.source_profile: public` uses free public sources. Full-text
enrichment may strengthen evidence when lawful open text is available; missing
full text remains visible and lowers authority rather than being fabricated.
`hybrid` or `elicit` requires `ELICIT_API_KEY` and is opt-in.

Novelty search is not wired in v0.1.0. Keep `novelty.enabled: false`.
The system must report `not_assessed`, never “novel,” when no novelty search
ran.

## Bounded execution

Use explicit limits:

- `paperbank.max_workers` controls PDF workers;
- `run.max_parallel_family_workers` is sliding concurrency, not a batch
  barrier;
- `run.max_revise_rounds` bounds owner/planner repair;
- `dataset.inspection_runtime.max_turns` bounds Claude Code only;
- `dataset.inspection_runtime.timeout_seconds` bounds either host.

For the final-quality release demos: six requested families, two requested
variants each, family cap three, three revise rounds, Codex CLI
`gpt-5.6-terra` at `high` effort, and the explicit bounded maximum of 2400
seconds per invocation. Codex has no Maieusis turn cap; the `max_turns` value
retained in the frozen YAML is Claude-only compatibility metadata and is not
passed to Codex. Returned breadth and scientific outcomes remain honest; the
product does not fabricate a perfect 6x2 cohort. Do not change a profile during
a run.

The IBL and NLB release demos use `topic_conditioned` research intent with the
same eight terms:

```yaml
research_intent:
  mode: topic_conditioned
  topic_terms:
    - neural population geometry
    - dynamical systems models
    - neural dynamics
    - neural population code
    - neural co-variability
    - neural manifolds
    - representational geometry
    - neural circuit models
  topic_description: ""
  seed_question: ""
```

They use the free/public literature profile with full-text enrichment enabled,
Elicit disabled, novelty disabled (`not_assessed`), and no family consolidation.
