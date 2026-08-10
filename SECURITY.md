# Security policy

## Supported versions

During the Research Preview, security fixes target the latest published
`0.1.x` release. Please upgrade to the newest patch before reporting a problem
that may already be fixed.

## Report a vulnerability privately

Use [GitHub private vulnerability reporting](https://github.com/BeibaiDraco/maieusis/security/advisories/new).
If that channel is unavailable, email `dracoxu@uchicago.edu`.

Include:

- the affected Maieusis version and operating system;
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
- Review provenance and authority labels before relying on a dossier; see the
  [provenance guide](https://github.com/BeibaiDraco/maieusis/blob/main/docs/PROVENANCE.md) for how
  Maieusis records them.

Scientific error, weak novelty, an unanswerable question, or a rejected family
is not normally a software vulnerability. Report those as scientific-quality
issues unless they arise from a security, provenance, identity, privacy, or
authorization failure.
