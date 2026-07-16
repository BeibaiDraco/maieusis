# Contributing to Maieusis

Thank you for helping make scientific question development more inspectable.
Bug reports, documentation improvements, dataset-adapter examples, prompt
evaluations, and focused code changes are welcome.

## Before you open a change

1. Search existing issues and describe the user-visible problem.
2. Do not attach source-paper PDFs, private datasets, credentials, API logs,
   complete model captures, or other material you cannot redistribute.
3. For scientific behavior, state the evidence boundary and the expected
   authority level. Model agreement is not evidence.
4. Keep proposal-stage context coarse. Exact schema and feasibility checks
   belong to the isolated Dataset Planner after a family is proposed.
5. Do not open the downstream analysis-execution bridge. It remains closed
   pending explicit human authorization.

## Development setup

Maieusis supports Python 3.11 and uses `uv` for the maintainer environment:

```bash
git clone https://github.com/BeibaiDraco/maieusis.git
cd maieusis
uv sync --all-extras
uv run ruff format --check src tests
uv run ruff check src tests
uv run mypy src/research_agenda_engine
uv run pytest -m "not live_openai and not local_artifacts and not agent_host and not live_agent" tests
uv build
uvx twine check dist/*
```

Use focused tests while iterating, then run the commands above before requesting
review. They mirror the public repository's CI and do not assume the private
development Makefile exists. Unit tests and default CI must not make paid model
calls.

## Change standards

- Preserve the public commands: `init`, `check`, `run`, `status`, `resume`.
- Add tests for new schemas, state transitions, provenance checks, context
  firewalls, and branch-isolation behavior.
- Keep secrets in environment variables, never YAML or committed files.
- Keep external dataset access read-only in planning runs.
- Preserve useful partial products and label uncertainty honestly.
- Treat type, identity, digest, filesystem, confirmation, and execution
  boundaries as hard; do not turn writing style into a scientific truth gate.
- Update user documentation when behavior changes.

## How public contributions reach the canonical tree

The public repository is a deterministic projection of the project's canonical
development tree, not a second implementation line. Contributors need access
only to the public repository: open a normal public pull request and complete
the public review process there.

For an accepted change, a maintainer ports the patch into the canonical
development tree, preserving the contributor's original authorship and commit
attribution. The maintainer then regenerates the public projection and
reconciles the public pull request with that exact projection. Public-only
product behavior is not merged independently, because it would create two
divergent sources of truth.

## Legal

By submitting a contribution for inclusion, you agree that it is submitted
under the [Apache License 2.0](LICENSE), as described in Section 5, unless you
conspicuously mark it "Not a Contribution." You must have the right to submit
the work and must disclose copied or adapted third-party material.

Be respectful and follow the [Code of Conduct](CODE_OF_CONDUCT.md). For
security-sensitive reports, do not open a public issue; follow
[SECURITY.md](SECURITY.md).
