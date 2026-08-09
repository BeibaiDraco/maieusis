# Manual setup

[Documentation home](INDEX.md) · [Installation](INSTALLATION.md)

**Want to see the machinery before you commit to any of this?** Set `mode: subscription_only_demo`
in `maieusis.yaml`. Model providers resolve to mocks, no API key is used, and nothing is billed to
a model account. You still need the coding host, the Maieusis clone, Poppler, PDFs and a dataset
root — it drops the model spend, not the setup — and it demonstrates the workflow, not scientific
quality.

This path is for users who want to prepare the project files and run the CLI
themselves. Complete [installation](INSTALLATION.md) first.

## 1. Scaffold a clean project

From a directory outside the Maieusis source checkout:

```bash
mkdir my-maieusis-project
cd my-maieusis-project
maieusis init
```

The initial layout is:

```text
my-maieusis-project/
├── AGENTS.md
├── CLAUDE.md
├── PROJECT_LAYOUT.md
├── maieusis.yaml
├── .claude/
│   ├── agents/
│   │   └── dataset-planner.md
│   └── skills/
│       └── maieusis-setup/
│           └── SKILL.md
└── .codex/
    ├── agents/
    │   └── dataset-planner.toml
    └── skills/
        └── maieusis-setup/
            └── SKILL.md
```

The two `SKILL.md` files are byte-identical: one source written to both host paths. You are reading
the manual route, so you will not use them -- but they are what the
[agent-guided route](AGENT_GUIDED_SETUP.md) runs on.

Existing files are never overwritten. Read `PROJECT_LAYOUT.md` before editing
the generated configuration.

## 2. Add source papers

Create the configured inbox and add only PDFs you may lawfully use:

```bash
mkdir -p papers/inbox
```

Keep one file per scientific work. Do not include both a preprint and publisher
copy unless you deliberately want Maieusis to screen them as possible
duplicates. Do not commit the PDFs.

For an International Brain Laboratory (IBL) or Neural Latents Benchmark (NLB)
reproduction, use that demo's paper manifest and verify every filename and
SHA-256 before running. The repository does not redistribute the papers.

## 3. Prepare read-only dataset access

You need:

- a stable dataset ID;
- a substantive official URL, local documentation files, or both;
- a local read-only dataset directory or representative sample;
- when needed, a Python executable or command with the libraries required to
  inspect it;
- at least one plain-language description of what the planner may inspect; and
- for a standard installed-package run, a Maieusis Git checkout with a valid
  `HEAD` for source-integrity checks; use a clean checkout unless you
  deliberately need to bind uncommitted source bytes.

An allowed-resource entry should name a real inspection surface, for example:

```yaml
allowed_inspection_resources:
  - official dataset documentation
  - local metadata tables and small representative samples
  - the dataset's public loading and preprocessing code
```

The dataset should live outside the run-output tree. Keep it read-only: the
Dataset Planner may inspect structure, metadata, documentation, and bounded
samples, but it must not modify the source data or execute the final scientific
analysis.

## 4. Store credentials outside YAML

Create the recommended user-level environment file:

```bash
mkdir -p ~/.config/maieusis
chmod 700 ~/.config/maieusis
touch ~/.config/maieusis/runtime.env
chmod 600 ~/.config/maieusis/runtime.env
```

Add only the variables required by your configuration. A standard
OpenAI/Anthropic run normally needs:

```text
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

Host- and feature-specific variables are conditional:

```text
CLAUDE_CODE_OAUTH_TOKEN=...  # required when coding_host: claude_code
ELICIT_API_KEY=...           # only for source_profile: elicit or hybrid
MAIEUSIS_ALLOW_PRO_MODEL=1   # only for a deliberately selected gated model
```

A Codex/ChatGPT login is stored by the Codex CLI and is not an OpenAI API key.
Keep every assignment on one line. Maieusis loads the user-level runtime file
automatically and does not overwrite an environment variable already set in
the process.

## 5. Edit `maieusis.yaml`

Use the [configuration guide](CONFIGURATION.md). At minimum, replace the
placeholders for:

- the paper inbox, parser, and extraction model;
- dataset identity, link/docs, read-only root, inspection environment, allowed
  resources, and `source_tree_root`;
- research intent;
- all scientific API roles, with different providers for Owner and Reviewer;
- coding host, coding model, and Codex reasoning effort when applicable; and
- output directory, family/variant counts, concurrency, timeout, and revision
  limit.

Prior-art review is enabled in the shipped profile and is what `novelty` configures. Setting
`novelty.enabled: false` turns it off and removes its paid web-search egress; the run then makes
no statement about prior art at all.

## 6. Preflight without paid calls

```bash
maieusis check --project maieusis.yaml
```

`check` parses the configuration, resolves paths, verifies the paper and
dataset inputs, checks configured provider credentials and coding-host
installation/login indicators, tests the public dataset context route, and
reports estimated model calls, planner launches, and external services. It
makes no paid model or coding-agent call and does not authenticate by placing a
provider request.

Treat every `FAIL` as a stop signal. Read warnings before deciding whether the
resulting authority ceiling is acceptable.

## 7. Run and inspect

After you have reviewed the preflight cost and egress disclosure:

```bash
maieusis run --project maieusis.yaml
```

The CLI prints the run location. Open its `README.md` first, then `summary.md`,
the PaperBank and context pages, `questions/question_families_detailed.md`, and
every family dossier.

If a run is interrupted, inspect what would be reused before resuming:

```bash
maieusis status <run-id> --project maieusis.yaml
maieusis resume <run-id> --project maieusis.yaml
```

`status` is read-only. `resume` reuses only products whose recorded inputs,
configuration, versions, and file hashes still match. Do not edit run artifacts
to force reuse.

---

[Documentation home](INDEX.md) · [Configuration](CONFIGURATION.md) ·
[Inputs and outputs](INPUTS_AND_OUTPUTS.md) · [Troubleshooting](TROUBLESHOOTING.md)
