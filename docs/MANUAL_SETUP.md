# Manual setup

This path is for users who prefer to prepare files and run the CLI themselves.

## 1. Scaffold a project

```bash
mkdir my-maieusis-project
cd my-maieusis-project
maieusis init
```

Expected starting layout:

```text
my-maieusis-project/
├── AGENTS.md
├── CLAUDE.md
├── PROJECT_LAYOUT.md
├── maieusis.yaml
├── .claude/
│   └── agents/
│       └── dataset-planner.md
└── .codex/
    └── agents/
        └── dataset-planner.toml
```

## 2. Add papers

Create `papers/inbox/`, then put only source-paper PDFs you may lawfully use
there. One
scientific paper should appear once: do not include both a preprint and the
publisher version unless you deliberately want them screened as possible
duplicates.

For a release demo, follow its paper manifest exactly. Verify every file's
SHA-256 before running. The public repository does not distribute PDFs.

## 3. Prepare the dataset

You need:

- a stable dataset ID and official URL;
- zero or more local documentation files;
- at least one allowed inspection-resource description;
- a local read-only dataset directory or representative sample; and
- an inspection Python executable or command with the dataset dependencies.

The source dataset should live outside the project output tree. Maieusis plans
against the dataset; it must not modify the dataset or run a full confirmatory
analysis.

## 4. Configure providers without storing secrets

Create the user-level runtime file:

```bash
mkdir -p ~/.config/maieusis
chmod 700 ~/.config/maieusis
touch ~/.config/maieusis/runtime.env
chmod 600 ~/.config/maieusis/runtime.env
```

Add only the variables required by your configured providers. For the release
profiles this normally includes:

```text
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
CLAUDE_CODE_OAUTH_TOKEN=...
MAIEUSIS_ALLOW_PRO_MODEL=1
```

Keep each value on one line. Never commit or paste this file. Model names and
provider choices belong in `maieusis.yaml`; keys do not.

## 5. Edit `maieusis.yaml`

Use [CONFIGURATION.md](CONFIGURATION.md). At minimum set:

- paper inbox and parser;
- dataset identity, documentation, local root, inspection command, and allowed
  resources;
- research intent;
- every model role, including the independent reviewer and coding host; and
- output root and bounded worker/turn/revision limits.

## 6. Preflight without spending money

```bash
set -a
source ~/.config/maieusis/runtime.env
set +a
maieusis check --project maieusis.yaml
```

`check` resolves paths, parses the config, checks inputs and credentials, and
confirms that a configured dataset link yields substantive public text rather
than only a metadata stub. It then prints estimated model/spawn work. It makes
zero paid model calls. Treat every failure as a stop signal.

## 7. Run and inspect

```bash
maieusis run --project maieusis.yaml
```

Open the run-local `README.md` first, then `summary.md`, visible PaperBank and
context artifacts, rendered QuestionFamilies, per-family closure packages, and
end-user dossiers. Use the hidden audit sidecar for provenance—not as a public
scientific narrative.

If interrupted, inspect before resuming:

```bash
maieusis status <run-id> --project maieusis.yaml
maieusis resume <run-id> --project maieusis.yaml
```

Resume reuses only receipt-bound stages whose inputs and configuration still
match. Do not hand-edit artifacts to force reuse.
