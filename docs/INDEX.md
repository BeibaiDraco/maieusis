# Maieusis documentation

Maieusis develops scientific questions against real source literature and a
real target dataset, then stops at a plan-or-non-proceed dossier. It does not
execute the final scientific analysis.

Start with the [project overview](../README.md), then follow the path that
matches what you want to do.

## Run Maieusis for the first time

1. [Install Maieusis](INSTALLATION.md).
2. Choose either [agent-guided setup](AGENT_GUIDED_SETUP.md) or
   [manual setup](MANUAL_SETUP.md).
3. Use the [configuration guide](CONFIGURATION.md) while editing
   `maieusis.yaml`.
4. Run the zero-paid-call preflight, then inspect the
   [inputs, outputs, and run layout](INPUTS_AND_OUTPUTS.md).
5. If anything stops, use [troubleshooting](TROUBLESHOOTING.md).

## Understand the method

- [Method overview](METHOD_OVERVIEW.md): how papers, current literature,
  dataset context, and research intent become question families and dossiers.
- [Architecture and trust boundaries](ARCHITECTURE.md): agent roles,
  isolation, and the line between planning and analysis execution.
- [Provenance](PROVENANCE.md): what Maieusis records and what its authority
  labels do—and do not—mean.
- [Limitations](LIMITATIONS.md): scientific, operational, and scope limits of
  the Research Preview.
- [Citation guide](CITATION.md): the exact v0.1.0 software citation and the
  difference between the version and concept DOIs.
- [Related-work positioning](positioning/POSITIONING.md): the narrow
  task-design comparison behind the positioning figure.

## Explore the examples

- [All demo questions and variants](../demos/QUESTIONS.md)
- [International Brain Laboratory (IBL) Brain-Wide Map demo](../demos/ibl/README.md)
- [Neural Latents Benchmark (NLB) MC_Maze-S demo](../demos/nlb/README.md)

These are worked neuroscience examples, not the product boundary. Maieusis is
designed for any scientific discipline and any scientific dataset that offers
the lawful, read-only inspection surface needed for planning.

The examples publish readable scientific artifacts and paper-identification
manifests, not source-paper PDFs, private datasets, credentials, raw model
traffic, or hidden local audit files.

## Get help or contribute

- Use [troubleshooting](TROUBLESHOOTING.md) for common setup and run failures.
- Open a GitHub issue for a reproducible software or documentation problem.
- Read [CONTRIBUTING.md](../CONTRIBUTING.md) before proposing a change.
- Follow [SECURITY.md](../SECURITY.md) for a vulnerability or sensitive report.
- For scientific collaboration, contact `dracoxu@uchicago.edu`.
