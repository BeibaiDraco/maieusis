# Agent-guided setup

[Documentation home](INDEX.md) · [Installation](INSTALLATION.md)

Maieusis is designed to be operated with Codex or Claude Code. The coding
agent helps configure the project and, during a run, inspects the target
dataset inside an isolated planning workspace. It does not perform the final
scientific analysis.

If you prefer to prepare every file yourself, use [manual setup](MANUAL_SETUP.md).

## 1. Install and sign in to one coding host

Choose one coding host. You do not need both.

### Codex

Follow the current [official Codex CLI setup](https://developers.openai.com/codex/cli).
On macOS or Linux, the documented standalone installer and login checks are:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex --version
codex login
codex login status
```

Your Codex or ChatGPT login authorizes the coding-agent host. It is separate
from the API keys used by Maieusis scientific-model roles.

### Claude Code

Follow the current [official Claude Code setup](https://docs.anthropic.com/en/docs/claude-code/getting-started).
The npm route requires Node.js 22 or newer:

```bash
node --version
npm install -g @anthropic-ai/claude-code
claude
claude doctor
```

Maieusis runs the Claude planner with an isolated configuration directory, so
the ordinary interactive login is not reused. Create a subscription token with:

```bash
claude setup-token
```

Store that token as `CLAUDE_CODE_OAUTH_TOKEN` in the runtime environment file
described below. Never paste it into `maieusis.yaml`, a prompt, an issue, or a
committed file.

## 2. Install Maieusis in a clean project

Follow [INSTALLATION.md](INSTALLATION.md). Your scientific project should be
separate from any Maieusis source checkout. From the project directory, run:

```bash
maieusis init
```

The command is idempotent: it prints `skip` rather than overwriting an existing
file. It creates `AGENTS.md`, `CLAUDE.md`, `PROJECT_LAYOUT.md`,
`maieusis.yaml`, `.codex/agents/dataset-planner.toml`, and
`.claude/agents/dataset-planner.md`.

Open Codex or Claude Code in this project directory. Keep the generated files
in place; they define the operating rules and the isolated Dataset Planner
role.

## 3. Prepare the scientific inputs

Give the coding agent only what the run needs:

- lawfully obtained source-paper PDFs under `papers/inbox/`;
- a stable public dataset identifier or official URL;
- official dataset documentation and metadata where available;
- a local read-only dataset directory or representative sample;
- permitted read-only dataset loading or preprocessing code, when needed;
- a clean Maieusis Git checkout used only for source-integrity checks; and
- optional topic terms or a seed question.

Do not commit PDFs, restricted data, runtime credentials, or run outputs. The
The International Brain Laboratory (IBL) and Neural Latents Benchmark (NLB)
demo pages identify their papers and datasets without redistributing them.

## 4. Configure credentials separately

A standard run uses scientific model APIs as well as the coding-agent host.
The Question Owner and independent reviewer must use different providers, so
the common OpenAI/Anthropic configuration needs both keys:

```text
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

Depending on your choices, you may also need:

```text
CLAUDE_CODE_OAUTH_TOKEN=...  # required when coding_host: claude_code
ELICIT_API_KEY=...           # only for an opt-in Elicit literature profile
MAIEUSIS_ALLOW_PRO_MODEL=1   # only when you deliberately selected a gated model
```

Put the required assignments in `~/.config/maieusis/runtime.env`, one per line,
then restrict access to that file:

```bash
mkdir -p ~/.config/maieusis
chmod 700 ~/.config/maieusis
touch ~/.config/maieusis/runtime.env
chmod 600 ~/.config/maieusis/runtime.env
```

Do not ask the coding agent to print secret values. Provider/model names belong
in `maieusis.yaml`; credentials do not.

## 5. Give the coding agent this prompt

```text
You are helping me operate Maieusis, not perform the scientific analysis.
Read the generated AGENTS.md, CLAUDE.md, PROJECT_LAYOUT.md, and maieusis.yaml.
Do not assume that this clean project contains a cloned Maieusis repository
README.md or docs/ tree. Treat the dataset, dataset documentation, source
checkout, and source papers as read-only inputs.

First inventory the PDF filenames and the dataset materials that are actually
present. Do not invent missing dataset facts. Help me configure:
- the paper inbox and PDF parser;
- the dataset identity, official link/docs, read-only local root, inspection
  environment, allowed resources, and clean Maieusis source-integrity checkout;
- my open, topic-conditioned, or seed-question research intent;
- every scientific model role, using a different provider for the Question
  Owner and independent reviewer;
- Codex or Claude Code as the Dataset Planner host, with an explicit model;
- the literature source profile; and
- bounded output, concurrency, timeout, and revision settings.

Keep credentials only in ~/.config/maieusis/runtime.env. Tell me which variable
names are needed, but never print their values or put them in YAML.

Run `maieusis check --project maieusis.yaml`. Resolve every failure without
changing the scientific boundary, making the dataset writable, or disabling an
identity, evidence, filesystem, or execution safeguard. Show me the estimated
model calls, planner launches, and external services, then ask before starting
the paid `maieusis run --project maieusis.yaml`.

After the run, open the run README, summary.md, the detailed question-family
page, and every family dossier. Clearly distinguish accepted plans, rejections,
deferred or warning outcomes, and incomplete work. Do not claim novelty or a
scientific result that the run did not establish.
```

## 6. Review the zero-paid-call preflight

Before authorizing a run, confirm that the coding agent has shown you:

1. the resolved project configuration and exact provider/model identities;
2. the PDF filenames and hashes;
3. the dataset link, paths, and read-only access mode;
4. the clean Maieusis source-integrity checkout;
5. the output location and concurrency/revision limits;
6. every preflight result;
7. the estimated model calls and planner launches; and
8. any evidence limitation that lowers scientific authority.

`maieusis check` makes no paid model or coding-agent call. Once it passes and
you accept the disclosed cost and egress, run:

```bash
maieusis run --project maieusis.yaml
```

## 7. Read the result

Open the path printed by the CLI. Start with the run-local `README.md` and
`summary.md`, then read `questions/question_families_detailed.md` and the
per-family dossiers. A dossier is a planning product or an honest
non-proceed outcome, not a scientific finding.

The final scientific judgment remains yours. Maieusis does not certify
importance, novelty, publishability, or truth.

---

[Documentation home](INDEX.md) · [Configuration](CONFIGURATION.md) ·
[Inputs and outputs](INPUTS_AND_OUTPUTS.md) · [Troubleshooting](TROUBLESHOOTING.md)
