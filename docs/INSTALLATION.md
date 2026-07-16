# Installation

[Documentation home](INDEX.md)

## What you need

- Python 3.11, 3.12, or 3.13;
- Git;
- Poppler's `pdftotext` for the default PDF parser;
- a local coding-agent host: Codex or Claude Code; and
- access to two supported scientific model providers for a standard run,
  because the Question Owner and independent reviewer must use different
  providers.

Dataset files, source papers, provider credentials, and coding-host login are
configured after installation. They should not be placed in the Maieusis
source-code checkout.

### Install Poppler

On macOS with Homebrew:

```bash
brew install poppler
```

On Debian or Ubuntu:

```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

Confirm that the executable is available:

```bash
pdftotext -v
```

## Recommended: install the published package

Create the scientific project first, then keep its Python environment inside
that project. Set `PYTHON` to an installed Python 3.11, 3.12, or 3.13
executable and confirm the reported version before continuing:

```bash
mkdir my-maieusis-project
cd my-maieusis-project

PYTHON=python3.11  # change to python3.12 or python3.13 when appropriate
"$PYTHON" --version
"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "maieusis[openai,anthropic,mcp,pdf]==0.1.0"

maieusis --help
maieusis init
```

Installing both provider extras matches the standard cross-provider review
path. If you deliberately configure different supported providers, install the
extras required by those providers instead. The `mcp` and `pdf` extras are
needed for the standard Dataset Planner and PDF workflow.

## Install from source

Keep the source checkout and the scientific project in separate directories:

```bash
mkdir -p "$HOME/src"
cd "$HOME/src"
git clone https://github.com/BeibaiDraco/maieusis.git
cd maieusis

PYTHON=python3.11  # change to python3.12 or python3.13 when appropriate
"$PYTHON" --version
"$PYTHON" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[openai,anthropic,mcp,pdf]"
maieusis --help

cd "$HOME"
mkdir my-maieusis-project
cd my-maieusis-project
maieusis init
```

Do not create the scientific project inside the cloned Maieusis repository.
Keeping them separate prevents project inputs and outputs from being confused
with package source files.

For exact reproduction of a published version, use its versioned wheel or tag
rather than a mutable branch.

## What `maieusis init` creates

`maieusis init` is local and makes no model or network call. It creates files
only when they do not already exist:

```text
maieusis.yaml
AGENTS.md
CLAUDE.md
PROJECT_LAYOUT.md
.codex/agents/dataset-planner.toml
.claude/agents/dataset-planner.md
```

It does not create credentials, download papers or data, call a model, or run
an analysis.

Next, choose [agent-guided setup](AGENT_GUIDED_SETUP.md) or
[manual setup](MANUAL_SETUP.md).

---

[Documentation home](INDEX.md) · [Configuration](CONFIGURATION.md) ·
[Troubleshooting](TROUBLESHOOTING.md)
