# Agent-guided setup

Maieusis is designed to be operated by a coding agent. The agent is not just an
installation helper: during a serious run, one isolated planner branch per
QuestionFamily inspects the real target dataset and returns typed planning
evidence. Use Codex, Claude Code, or an equivalent host that can read the
project, run commands, and work inside the configured safety boundary.

## 1. Install and authenticate a coding-agent host

Choose one host. You do not need both.

### Codex

Follow the current [official Codex CLI setup](https://developers.openai.com/codex/cli)
for your chosen Codex surface. For the command-line host, install or upgrade the
official package, then verify the executable:

```bash
npm install -g @openai/codex
codex --version
codex login status
```

Complete the sign-in flow shown by the client. A Codex/ChatGPT login is a
coding-agent credential; it is separate from the model API keys Maieusis uses
for scientific roles. The final-quality `gpt-5.6-terra` profile requires
`codex-cli >=0.144.4`; `maieusis check` verifies this before any paid call or
planner spawn.

### Claude Code

Follow Anthropic's [official Claude Code setup](https://docs.anthropic.com/en/docs/claude-code/getting-started):

```bash
npm install -g @anthropic-ai/claude-code
claude
claude doctor
```

Sign in with the account or provider you intend to use. When Maieusis launches
Claude Code in its relocated safety environment, it may need a subscription
token created by:

```bash
claude setup-token
```

Store the resulting value as `CLAUDE_CODE_OAUTH_TOKEN` in your untracked
runtime environment file. It is a secret; never paste it into an issue,
`maieusis.yaml`, or a prompt.

## 2. Install Maieusis and create the project

Follow [INSTALLATION.md](INSTALLATION.md), then:

```bash
mkdir my-question-project
cd my-question-project
maieusis init
```

Open the coding agent in this directory. `maieusis init` creates `AGENTS.md`,
`CLAUDE.md`, `PROJECT_LAYOUT.md`, `maieusis.yaml`, and the Codex and Claude Code
Dataset Planner role files. Keep those generated files in place: they are the
project-local operating and runtime assets.

## 3. Give the agent only the inputs it needs

Prepare:

- `papers/inbox/`: lawfully obtained source papers as PDFs;
- a dataset's stable public identifier or official URL;
- official dataset documentation and/or metadata files;
- a local read-only dataset root or small representative sample;
- a clean Git checkout that the Dataset Planner can inspect; and
- optional topic terms or a seed question.

Do not put keys in the project config. Do not commit source-paper PDFs or
restricted data. The IBL and NLB demo pages provide exact paper identities and
legal acquisition instructions without redistributing PDFs.

## 4. Use this setup prompt

```text
You are helping me operate Maieusis, not perform the scientific analysis.
Read the generated AGENTS.md, CLAUDE.md, PROJECT_LAYOUT.md, and maieusis.yaml.
Do not assume that this clean project contains a cloned Maieusis repository
README.md or docs/ tree. Inspect the available dataset documentation and small
sample without modifying them.

First, inventory my PDF filenames and dataset inputs. Do not infer missing
facts. Configure the dataset link/docs, read-only dataset root, inspection
runtime, coding host, model roles, literature profile, research intent, and
output directory. Keep credentials only in
~/.config/maieusis/runtime.env and tell me which variable names are needed;
never print their values.

Run `maieusis check --project maieusis.yaml`. Resolve all preflight failures
without weakening provenance, filesystem, authority, confirmation, or
execution guards. Show me the call/spawn estimate and ask before the paid
`maieusis run`. During the run, do not alter source, config, inputs, or models.
After completion, open summary.md, every family outcome, the end-user dossiers,
and the run README. Clearly separate accepted, rejected, deferred, provisional,
and incomplete products. Never claim a novelty search or scientific result
that the run did not perform.
```

## 5. Review before approving a paid run

The coding agent should show you:

1. exact project configuration and model identities;
2. PDF filenames and hashes;
3. dataset paths and access mode;
4. output and capture locations;
5. preflight results;
6. estimated model calls and planner spawns; and
7. any authority limitation caused by incomplete evidence.

Only then run:

```bash
maieusis run --project maieusis.yaml
```

The final scientific judgment remains yours. Maieusis makes question
development inspectable; it does not certify scientific importance,
publishability, or novelty.
