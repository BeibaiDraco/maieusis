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
5. If anything stops, read [when a run stops](RUN_SUPERVISION.md) for what kind of stop it
   is, then [troubleshooting](TROUBLESHOOTING.md) for how to fix it.

## Understand the method

- [Method overview](METHOD_OVERVIEW.md): how papers, current literature,
  dataset context, and research intent become question families and dossiers.
- [Architecture and trust boundaries](ARCHITECTURE.md): agent roles,
  isolation, and the line between planning and analysis execution.
- [Provenance](PROVENANCE.md): what Maieusis records and what its authority
  labels do—and do not—mean.
- [Scanned PDFs](SCANNED_PDFS.md): three short steps to use a scanned paper
  while the original file stays the paper's identity.
- [Reading the labels](LABELS.md): every label an artifact can carry, its permitted values, and
  what each one licenses you to conclude. Read this before judging any published plan.
- [Shepherd mode](SHEPHERD_MODE.md): the contract your own coding agent works under while it
  drives a run — what it may repair, what it must record, and what repair may never reach.
  Readable before you install anything.
- [When a run stops](RUN_SUPERVISION.md): the two questions to ask, the three honest
  terminal shapes, and how to tell a
  scientific rejection from an infrastructure fault.
- [Limitations](LIMITATIONS.md): scientific, operational, and scope limits of
  the Research Preview.
- [Citation guide](CITATION.md): the exact v0.1.1 software citation and the
  difference between the version and concept DOIs.
- [Related-work positioning](positioning/POSITIONING.md): the narrow
  task-design comparison behind the positioning figure.

## Explore the examples

- [All demo questions and variants](../demos/QUESTIONS.md) — eighteen question families across
  three datasets, including the three that closed without a plan
- [Climate demo](../demos/climate/README.md): ERA5-derived stratospheric dynamics, and
  [its dataset notes](../demos/climate/DATASET_NOTES.md)
- [International Brain Laboratory (IBL) Brain-Wide Map demo](../demos/ibl/README.md)
- [Neural Latents Benchmark (NLB) MC_Maze-S demo](../demos/nlb/README.md), with
  [dataset notes](../demos/nlb/DATASET_NOTES.md) and a
  [runnable region-mapping check](../demos/nlb/verify_region_mapping.py)
- [Source papers](../demos/PAPER_SOURCES.md) for both cohorts

Two of the three are neuroscience and one is atmospheric science; nothing in the system was adapted
for either. Maieusis is designed for any scientific discipline and any scientific dataset that
offers the lawful, read-only inspection surface needed for planning.

If you read only one page to judge whether any of this is real, read the
[NLB dataset notes](../demos/nlb/DATASET_NOTES.md): it makes a specific, checkable claim about a
pinned public dataset, hands you a script to verify it, and then says what that check does not
prove.

The examples publish readable scientific artifacts and paper-identification
manifests, not source-paper PDFs, private datasets, credentials, raw model
traffic, or hidden local audit files.

## Get help or contribute

- Use [troubleshooting](TROUBLESHOOTING.md) for common setup and run failures.
- Open a GitHub issue for a reproducible software or documentation problem.
- Read [CONTRIBUTING.md](../CONTRIBUTING.md) before proposing a change.
- Follow [SECURITY.md](../SECURITY.md) for a vulnerability or sensitive report.
- For scientific collaboration, contact `dracoxu@uchicago.edu`.
