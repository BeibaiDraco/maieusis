# Troubleshooting

[Documentation home](INDEX.md) · [Installation](INSTALLATION.md) ·
[Configuration](CONFIGURATION.md)

Start from the project directory with:

```bash
maieusis --help
maieusis check --project maieusis.yaml
```

Preflight makes no paid model or coding-agent call. Fix every `FAIL` before
running. A `WARN` does not always block the run, but it may lower the authority
or completeness of the result.

## `maieusis` is not found

Activate the environment where you installed the package:

```bash
source .venv/bin/activate
python -m pip show maieusis
python -m pip check
maieusis --help
```

If provider, MCP, or PDF imports are missing, reinstall the needed extras:

```bash
python -m pip install "maieusis[openai,anthropic,mcp,pdf]==0.1.1"
```

Do not run from inside a different Maieusis source checkout unless that is the
installation you intend to test.

## `maieusis init` skipped a file

`init` never overwrites an existing file. A `skip` message is expected when
`maieusis.yaml`, `AGENTS.md`, `CLAUDE.md`, `PROJECT_LAYOUT.md`, or a Dataset
Planner role file already exists.

Inspect the existing file before deciding whether to move it aside. Do not
delete a project contract or configuration blindly.

## PDF parsing fails

- Confirm `pdftotext -v` works.
- Confirm the file opens and contains selectable text.
- Check that an HTML error page was not saved with a `.pdf` suffix.
- Keep only one version of each scientific work.
- For a demo reproduction, compare the filename and SHA-256 with its paper
  manifest.
- If one malformed paper blocks the run, replace or remove that input rather
  than weakening source-evidence checks.

## A credential appears missing

- Check the environment-variable name, not its value, against
  [CONFIGURATION.md](CONFIGURATION.md).
- Keep one `KEY=value` assignment per line.
- Confirm the recommended file exists and is readable:

  ```bash
  ls -l ~/.config/maieusis/runtime.env
  ```

- Remember that coding-host login and scientific API keys are separate.
- Do not print the secret, add it to YAML, or attach the runtime file to an
  issue.

Existing process variables take precedence over runtime files. A stale value
already exported in the shell can therefore override the file you just edited.

## Claude Code cannot authenticate

Verify Claude Code outside Maieusis:

```bash
claude doctor
```

The isolated planner does not reuse the ordinary interactive login. Create the
required subscription token with:

```bash
claude setup-token
```

Store the resulting token as `CLAUDE_CODE_OAUTH_TOKEN` in the untracked runtime
environment file, then rerun `maieusis check`.

## Codex cannot authenticate

Verify the subscription CLI independently:

```bash
codex --version
codex login status
```

If you intentionally keep Codex authentication outside the default
`~/.codex` directory, set `CODEX_HOME` to that Codex home before running
preflight. Do not copy `auth.json` into the scientific project or run-output
tree.

If preflight reports that a configured Codex model needs a newer CLI, upgrade
Codex with the same package manager used to install it, then repeat the version
and login checks.

## Dataset preflight fails

Check each part separately:

- `dataset.seed.link` should resolve to substantive official information. If it
  returns only a metadata stub, use the canonical documentation page or add
  readable files under `dataset.seed.docs`.
- `dataset.inspection_runtime.dataset_root` must exist and be readable.
- `external_readonly` requires `dataset_root`.
- Do not set both `inspection_python` and `inspection_command`. If neither is
  set, confirm that the coding host's own environment already contains the
  required inspection tools.
- Test the chosen inspection executable or command outside Maieusis and confirm
  it can import the dataset's required libraries.
- Add at least one non-blank `allowed_inspection_resources` entry describing a
  real resource.
- `source_tree_root` must be a Maieusis Git checkout with a valid `HEAD`. It is
  the source-integrity surface, not the dataset-code inspection checkout. Use a
  clean checkout unless you intentionally want uncommitted source bytes
  included in the run identity. If you installed from the package index you do
  not have one yet: `git clone https://github.com/BeibaiDraco/maieusis.git`
  somewhere outside your project and point the field at it. Leaving the field
  unset falls back to detecting a checkout from the current environment, which
  in a fresh project directory finds nothing -- and running `git init` in your
  own project does not help, because the checkout has to be Maieusis.

Do not make the dataset writable merely to pass preflight.

## Owner and reviewer are not independent

In standard mode, these providers must differ:

```yaml
models:
  owner: {provider: openai, model: "<model-id>"}
  reviewer: {provider: anthropic, model: "<model-id>"}
```

Changing only the model name while keeping the same provider does not satisfy
this check.

## A model is blocked as expensive or unavailable

Confirm that the provider/model identifier is correct and enabled for your
account. Maieusis does not silently fall back to another model.

Only when you deliberately intend to use that exact gated model, set:

```text
MAIEUSIS_ALLOW_PRO_MODEL=1
```

Then rerun preflight and review the disclosed work estimate. Do not change
models while a run is active.

## Literature evidence is incomplete

Open `literature/retrieval_summary.md` and
`literature/topic_evidence_summary.md`. Missing open full text or incomplete
metadata can be an honest external limitation.

- With `source_profile: public`, add lawful source material or accept the
  provisional authority ceiling.
- With `source_profile: auto`, Elicit is used only when its key is available.
- With `source_profile: elicit` or `hybrid`, a missing `ELICIT_API_KEY` is a
  preflight failure.

Never fill an evidence gap with an unsupported abstract or fabricated text.

## A family was rejected, deferred, or closed with a warning

Read `summary.md`, the family's `dossier_detailed.md`, and its complete
`dossier.md`. Dataset mismatch, an unfaithful operationalization, scientific
drift, material revision, or an unresolved ambiguity may be the correct
outcome.

A provider or validation warning is not an accepted plan. Do not edit a dossier
or completion file to promote it.

## Detailed pages are not ready

The scientific run state and compact products remain unchanged when only the
readable detailed pages fail to render. Inspect:

```bash
maieusis status <run-id> --project maieusis.yaml
```

If all scientific stages are reusable, this command retries only the readable
pages:

```bash
maieusis resume <run-id> --project maieusis.yaml
```

## A run was interrupted

First inspect what is present and what would repeat:

```bash
maieusis status <run-id> --project maieusis.yaml
```

If the project configuration and inputs are correct:

```bash
maieusis resume <run-id> --project maieusis.yaml
```

When source files, config, prompts, models, or recorded products changed,
expect the affected stages to run again. Do not remove receipts or hand-edit
hashes to force reuse.

## Reporting a problem

Share only:

- package version and operating system;
- the failing command;
- a sanitized configuration;
- run ID and diagnostic code;
- relevant `check` or `status` output; and
- the smallest redacted reproduction.

Do not share API keys, subscription tokens, private data, source PDFs,
absolute local paths, provider session/request IDs, or raw model traffic.
Follow [SECURITY.md](../SECURITY.md) for vulnerabilities or sensitive reports.

---

[Documentation home](INDEX.md) · [Manual setup](MANUAL_SETUP.md) ·
[Configuration](CONFIGURATION.md) · [Limitations](LIMITATIONS.md)
