# Contributing to Maieusis

Thank you for helping make scientific question development more inspectable.
Bug reports, documentation improvements, dataset-adapter examples, prompt
evaluations, and focused code changes are welcome.

## Before you open a change

1. Search existing issues, then describe the user-visible problem or proposed
   improvement.
2. Do not attach source-paper PDFs, private datasets, credentials, API logs,
   complete model captures, or anything you cannot lawfully redistribute.
3. If a change affects scientific behavior, explain what evidence it may use,
   how it changes the authority of an output, and how the boundary is tested.
4. Keep target-dataset access read-only during question planning. Full analysis
   execution and confirmatory claims are outside the v0.1.x product boundary.

## Development setup

Maieusis supports Python 3.11–3.13 and uses
[`uv`](https://docs.astral.sh/uv/) for its contributor environment:

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

Use focused tests while iterating, then run the full command set before
requesting review. Default tests and CI must not make paid model calls.

## Change standards

- Preserve compatibility for the public `init`, `check`, `run`, `status`, and
  `resume` commands unless a change explicitly documents a migration.
- Add tests for new schemas, state transitions, provenance checks, and
  isolation or security boundaries.
- Keep secrets in environment variables, never YAML or committed files.
- Preserve useful partial products and label uncertainty honestly.
- Keep identity, evidence, filesystem, confirmation, and execution boundaries
  fail-closed.
- Update user documentation whenever behavior changes.

## Pull requests

Open pull requests against this public repository. Keep each pull request
focused, explain its user impact, list the tests run, and disclose copied or
adapted third-party material.

The canonical development tree remains the implementation source of truth.
When a public contribution is accepted, a maintainer ports it into that tree,
preserving the contributor's authorship and attribution in the ported commit.
Public-only product behavior is not merged independently; it appears here
after the next reviewed public update. Contributors do not need access to the
development repository.

## Legal and community

By submitting a contribution for inclusion, you agree that it is submitted
under the [Apache License 2.0](LICENSE), as described in Section 5, unless you
conspicuously mark it “Not a Contribution.” You must have the right to submit
the work.

Be respectful and follow the [Code of Conduct](CODE_OF_CONDUCT.md). Report
security-sensitive issues privately as described in [SECURITY.md](SECURITY.md).
