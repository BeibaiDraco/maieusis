# Troubleshooting

Start with:

```bash
maieusis --help
maieusis check --project maieusis.yaml
```

Preflight makes zero paid calls. Fix it before running.

## `maieusis` is not found

Activate the environment where you installed the package, then verify:

```bash
python -m pip show maieusis
python -m pip check
```

Reinstall the needed extras if provider, MCP, or PDF imports are missing:

```bash
python -m pip install "maieusis[openai,anthropic,mcp,pdf]==0.1.0"
```

## PDF parsing fails

- Confirm `pdftotext -v` works.
- Confirm the PDF opens and contains extractable text.
- Check that it is not an HTML error page renamed `.pdf`.
- Compare its SHA-256 with the demo manifest.
- If one paper remains bad while others work, remove that paper instead of
  weakening source/evidence checks.

## A credential appears missing

- Check that the variable name—not its value—matches the configured provider.
- Load the runtime file with `set -a; source ...; set +a`.
- Keep every assignment on one line.
- Do not print the secret or add it to YAML.
- Remember that coding-agent login/subscription auth and scientific API keys
  are separate.

## Claude Code planner cannot authenticate

Run `claude doctor`. If ordinary interactive login works but the relocated
planner does not, create a fresh `claude setup-token` and set
`CLAUDE_CODE_OAUTH_TOKEN` in the untracked runtime file.

## Codex planner cannot authenticate or Terra asks for an upgrade

Verify the subscription CLI independently:

```bash
codex --version
codex login status
```

The final-quality `gpt-5.6-terra` profile requires `codex-cli >=0.144.4`.
Upgrade an older CLI with the same package manager used to install it. Codex
auth normally lives at `~/.codex/auth.json`; when a cleanroom changes `HOME`,
set `CODEX_HOME` to the already-authenticated Codex home before running
`maieusis check`. Do not copy `auth.json` into the project or output tree. The
runner stages only that file into a short-lived private home, deletes the staged
copy after `thread.started`, and removes the temporary home at process exit.

## Dataset preflight fails

- Use a stable official dataset link or source-backed local docs.
- If `dataset.seed_link_content` fails, the URL returned no substantive text;
  replace it with the current canonical documentation page or add readable
  `dataset.seed.docs`.
- Set a real, readable, read-only dataset root.
- Provide exactly one of `inspection_python` and `inspection_command`.
- Ensure the inspection environment can import the dataset's required tools.
- For an installed wheel outside a source checkout, provide a clean Git source
  tree with a valid `HEAD` for planner source-integrity checks.

## A model is blocked as expensive or unauthorized

Verify the configured model name and account entitlement. Only if you intended
that exact role/model, set `MAIEUSIS_ALLOW_PRO_MODEL=1`. Never enable a blanket
fallback or change models during a run.

## Literature is incomplete

This can be an honest external limitation. Inspect the retrieval summary and
authority labels. Missing open full text must not be fabricated. Add lawful
source material or accept the provisional ceiling.

## A family is rejected

Read its dossier or fallback closure and planner evidence. Dataset mismatch,
operationalization failure, scientific drift, or an unresolvable ambiguity may
be the correct scientific outcome. Do not edit the artifact to turn rejection
into acceptance.

## A run was interrupted

```bash
maieusis status <run-id> --project maieusis.yaml
```

Review the reuse/re-run table. If inputs and configuration are correct:

```bash
maieusis resume <run-id> --project maieusis.yaml
```

If source, config, prompts, models, or artifacts changed, expect the affected
stage to re-run.

## Reporting a problem

Share the package version, operating system, sanitized config, run ID,
diagnostic code, and the smallest redacted reproduction. Do not share keys,
private data, source PDFs, absolute paths, session IDs, or raw model captures.
Use [SECURITY.md](../SECURITY.md) for vulnerabilities.
