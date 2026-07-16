# Installation

## Requirements

- Python 3.11 (supported range: 3.11–3.13)
- Git
- Poppler's `pdftotext` for the default PDF parser
- a local coding-agent host: Codex or Claude Code
- credentials for the configured scientific model providers
- a real dataset repository, documentation, metadata, or small sample that the
  coding agent may inspect read-only

On macOS, Poppler is commonly installed with Homebrew:

```bash
brew install poppler
```

On Debian or Ubuntu:

```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

## Install the release

Create a fresh environment so Maieusis cannot accidentally import a development
checkout:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "maieusis[openai,anthropic,mcp,pdf]==0.1.0"
maieusis --help
```

For a source checkout before PyPI publication:

```bash
git clone https://github.com/BeibaiDraco/maieusis.git
cd maieusis
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[openai,anthropic,mcp,pdf]"
maieusis --help
```

Do not install from the development repository or a mutable branch when
reproducing a release demo. Use the versioned wheel or immutable release tag.

## Verify the installation

```bash
mkdir maieusis-project
cd maieusis-project
maieusis init
maieusis --help
```

`init` creates `maieusis.yaml`, `AGENTS.md`, `CLAUDE.md`, `PROJECT_LAYOUT.md`,
and the Codex and Claude Code Dataset Planner role files under `.codex/agents/`
and `.claude/agents/`. It does not create credentials, download papers, call a
model, or run an analysis.

Next: [agent-guided setup](AGENT_GUIDED_SETUP.md) or
[manual setup](MANUAL_SETUP.md).
