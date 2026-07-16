# Security policy

## Supported versions

During the Research Preview, security fixes are provided for the latest
published `0.1.x` release. Upgrade to the newest patch before reporting a
problem that may already be fixed.

## Report a vulnerability privately

Email `dracoxu@uchicago` with:

- the affected version and operating system;
- the smallest safe reproduction;
- the expected impact; and
- any suggested mitigation.

Do not open a public issue for an unpatched vulnerability. Do not send real API
keys, subscription tokens, private datasets, source-paper PDFs, raw model
captures, or sensitive participant data. Use synthetic placeholders and ask
for a secure transfer method if a private artifact is essential.

## Security boundaries users should preserve

- Keep `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, coding-agent credentials, and
  similar secrets outside `maieusis.yaml` and outside the repository.
- Treat a coding agent as a local process with repository and tool access.
  Review its permissions and run it only in a project you intend it to inspect.
- Keep target datasets read-only during question planning.
- Run `maieusis check` before `maieusis run`; preflight performs no paid model
  calls.
- Inspect the run manifest, receipts, and audit subset before relying on a
  dossier.

Scientific error, weak novelty, an unanswerable question, or a rejected family
is not normally a software vulnerability. Report those as scientific-quality
issues unless they arise from a security, provenance, identity, privacy, or
authorization failure.
