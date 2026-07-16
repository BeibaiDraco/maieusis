# Neural Latents Benchmark MC_Maze-S demo

This demo applies Maieusis to MC_Maze-S, a scaled release of macaque primary
motor cortex (M1) and dorsal premotor cortex (PMd) recordings during delayed
straight and curved barrier-maze reaches. The dataset is part of [Neural Latents
Benchmark ’21](https://neurallatents.github.io/) and is published as
[DANDI:000140, version 0.220113.0408](https://doi.org/10.48324/dandi.000140/0.220113.0408).

Please cite the benchmark paper, [Pei et al., *Neural Latents Benchmark ’21:
Evaluating latent variable models of neural population activity*
(2021)](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/979d472a84804b9f647bc185a877a8b5-Abstract-round2.html), and the dataset citation provided by
DANDI. The release metadata also identifies the original studies [*Cortical
preparatory activity: representation of movement or first cog in a dynamical
machine?*](https://doi.org/10.1016/j.neuron.2010.09.015) and [*Neural population
dynamics during reaching*](https://doi.org/10.1038/nature11129).

Maieusis used the same reviewed, paper-derived question-forming patterns as the
IBL demo, then built new dataset context, questions, inspections, plans, and
reviews specifically for MC_Maze-S. It developed six two-variant families and
stopped before analysis execution.

## Featured question — What kind of neural stability supports generalization?

“Stable representation” can mean several different things. The average
population activity for each reach may move while the relationships among
reaches remain reproducible. And geometry that repeats reliably within straight
or curved reaches does not necessarily transfer between those two movement
demands.

NLB-006 separates these claims into two tests. One compares relational stability
with centroid stability within matched reach conditions and asks whether the
distinction differs between M1 and PMd. The other first requires reliable
geometry within each demand, then asks whether that geometry transfers between
straight and curved barrier-maze reaches or is consistently remapped. This
distinction separates a shared motor scaffold from stable but demand-specific
organization without mistaking unreliable estimates for remapping.

Both variants produced provisionally accepted planning dossiers. The dataset
contains one recorded subject, the claims remain descriptive or predictive
rather than causal, and no analysis was executed.

**[Explore both variants, their alternatives, assumptions, and possible
outcomes](artifacts/questions/question_families_detailed.md#family-006-which-geometric-stability-supports-generalization-in-reaching)**

[See the planned study at a glance](artifacts/families/geometry-definition-generalization/dossier_detailed.md)
· [Open the complete planning record](artifacts/families/geometry-definition-generalization/dossier.md)

## Explore the completed demo

Start with the **[complete question gallery](../QUESTIONS.md)**. It introduces
all twelve families across both demos and links every variant to its scientific
background and planning outcome. Within the NLB run:

- five families produced provisional plans for both variants; and
- one family remains visible as a validation warning.

The warning family, “Preparatory population dynamics as operating regimes for
movement,” is **provisional/degraded and has no accepted-plan authority for
either variant**. Its scientific motivation and proposed variants remain useful
to inspect, but the returned planning material did not pass validation. This is
a pipeline outcome—not evidence that the scientific idea is false or that the
dataset is unsuitable.

To follow the NLB question-development process:

1. **Source-derived patterns:** read the [12-paper source guide](../PAPER_SOURCES.md)
   and the [full pattern explanation](artifacts/paperbank/question_patterns_detailed.md).
2. **NLB-specific context:** read the
   [dataset narrative](artifacts/dataset/dataset_narrative.md),
   [research scope](artifacts/literature/research_scope.md), and
   [topic-evidence summary](artifacts/literature/topic_evidence_summary.md).
3. **All proposed questions:** open the
   [full two-variant family page](artifacts/questions/question_families_detailed.md).
4. **Dataset-grounded outcomes:** continue from each family in the gallery to
   its plan guide and complete planning or warning record.

The published gallery contains reader-facing scientific artifacts. Source
PDFs, NWB data, model transcripts, credentials, and private recovery records
are not distributed.

## What the NLB demo reuses

The IBL and NLB demos deliberately use the same 12-paper source cohort. NLB
reuses only the reviewed PaperCases, question-formation traces, and patterns
created from those papers. Its dataset narrative, literature context, question
families, dataset inspections, plans, reviews, and dossiers were generated anew
for MC_Maze-S.

For exact reproduction, Maieusis verifies this reuse against the completed IBL
run instead of trusting a manually copied directory. The technical bindings are
recorded in the [public provenance summary](artifacts/provenance/paperbank_import.yaml)
and [demo manifest](demo_manifest.yaml).

## Reproduce the IBL → NLB route

> **Required first step:** complete the [IBL final-quality run](../ibl/README.md)
> before starting a new receipt-reuse NLB run. You can browse every published
> NLB artifact without a private IBL run; the IBL run is required only to
> generate a new NLB run through this exact reuse route.

### 1. Install Maieusis and prepare credentials

Complete [installation](../../docs/INSTALLATION.md) and either the
[coding-agent setup](../../docs/AGENT_GUIDED_SETUP.md) or
[manual setup](../../docs/MANUAL_SETUP.md). The standard route requires
scientific-model API credentials from two supported providers for independent
Owner/Reviewer operation, plus a separately authenticated coding-agent host.
Keep all credentials outside YAML and outside the repository.

Use the same immutable Maieusis installation and clean Maieusis
source-integrity checkout for the IBL and NLB runs.

### 2. Prepare the identical private paper inbox

Obtain the sources in the [paper source guide](../PAPER_SOURCES.md) lawfully and
use the same 12 filenames and SHA-256 values as the source IBL run:

```text
nlb-demo-work/
├── papers/inbox/<the 12 listed PDF filenames>
├── maieusis-final.yaml
└── runs/
```

Verify every digest against the
[machine-readable source manifest](../shared/paper_sources.yaml) with
`shasum -a 256` on macOS or `sha256sum` on Linux. The inbox path may differ from
IBL; its filename and byte set may not. Keep PDFs outside git.

### 3. Download the pinned MC_Maze-S data

The demo uses published DANDI version `0.220113.0408`; do not silently
substitute a draft or another version. Follow the official
[DANDI download guide](https://docs.dandiarchive.org/user-guide-using/accessing-data/downloading/):

```bash
export MAIEUSIS_REPO=/absolute/path/to/your/maieusis-source-checkout
export NLB_DEMO_WORK=/absolute/path/to/nlb-demo-work
python -m pip install dandi
export NLB_DANDI_VERSION='0.220113.0408'
mkdir -p /data/maieusis/nlb
cd /data/maieusis/nlb
dandi download "DANDI:000140/${NLB_DANDI_VERSION}"
chmod -R a-w /data/maieusis/nlb/000140
```

Point the planner's `dataset_root` to the read-only `000140` directory. Read
[the M1/PMd mapping note](DATASET_NOTES.md) before configuration: the official
MC_Maze documentation records an electrode-index conversion caveat, so raw
`units/electrodes` values alone must not be used to infer that the population
contains only PMd units.

Verify the pinned file hashes from [the demo manifest](demo_manifest.yaml), then
run the bounded metadata-only check in the NLB inspection environment:

```bash
python "$MAIEUSIS_REPO/demos/nlb/verify_region_mapping.py" /data/maieusis/nlb/000140
```

For the pinned files it should report train `PMd=72 M1=70` and test
`PMd=52 M1=55` before any paid run.

### 4. Configure receipt-bound PaperBank reuse

Return to the private work directory and copy the checked-in profile:

```bash
cd "$NLB_DEMO_WORK"
cp "$MAIEUSIS_REPO/examples/release/nlb-final-quality.yaml" maieusis-final.yaml
```

Replace only its path and source-receipt placeholders, preserving this shape:

```yaml
paperbank:
  inbox_dir: /ABSOLUTE/PATH/TO/THE/IDENTICAL/12-PDF-INBOX
  import_from_run:
    source_run_root: /ABSOLUTE/PATH/TO/COMPLETED/IBL/FINAL/RUN
    expected_receipt_sha256: <SHA-256 of receipts/paper-half.yaml>

dataset:
  seed:
    dataset_id: dandi-000140-nlb-mc-maze-s
    link: https://dandiarchive.org/dandiset/000140
    docs:
      - /ABSOLUTE/PATH/TO/CLEAN_MAIEUSIS_CHECKOUT/demos/nlb/DATASET_NOTES.md
  inspection_runtime:
    dataset_root: /data/maieusis/nlb/000140
    dataset_access_mode: external_readonly
```

Compute the source receipt digest locally:

```bash
shasum -a 256 /path/to/ibl-final-run/receipts/paper-half.yaml
# sha256sum /path/to/ibl-final-run/receipts/paper-half.yaml  # Linux
```

Keep the paper extraction, pattern, and review model identities equal to the IBL
final profile. The checked-in NLB profile requests six families with two variants
each, at most three concurrent family workers, and Codex CLI with
`coding_model=gpt-5.6-terra` and `coding_reasoning_effort=high`.

### 5. Check, authorize, and run

Preflight and reuse validation make zero paid calls:

```bash
maieusis check --project maieusis-final.yaml
```

Resolve every reported input, model, path, and reuse-binding problem. Inspect
the selected models and estimated calls, then make an explicit human decision
before starting the paid run:

```bash
maieusis run --project maieusis-final.yaml
```

Do not manually copy the PaperBank or edit source, configuration, imported
files, or generated artifacts during the run. Model-generated prose is not
expected to be byte-identical to this published demo; reproduction means using
the pinned inputs and configuration through the same typed, bounded workflow
and receiving inspectable terminal outcomes.

## Read a newly generated run

Open `<output-root>/<run-id>/README.md`, then follow this order:

1. `summary.md` for overall completion and family outcomes;
2. `imports/paperbank.yaml` to audit exact cross-run reuse;
3. `questions/question_families_detailed.md` for every proposed variant;
4. each `families/<family-slug>/dossier_detailed.md` for a guided plan overview;
5. each `families/<family-slug>/dossier.md` for the complete planning or warning
   record;
6. `run_manifest.yaml` and private provenance records when auditing integrity or
   resuming a local run.

Confirm that no IBL dataset narrative, question family, branch evidence, or
dossier was carried into NLB as though it were NLB evidence. A dossier is a
planning product, not a scientific result.

## Copy/paste prompt for a coding agent

```text
Reproduce the Maieusis NLB MC_Maze-S demo using demos/nlb/README.md. First
verify that I have completed an immutable IBL final-quality source run. Prepare
the same 12 paper filenames and bytes in a private NLB inbox and verify them
against demos/shared/paper_sources.yaml. Download pinned DANDI:000140 version
0.220113.0408, keep it outside git, make it read-only, read DATASET_NOTES.md,
and run the region-mapping check. Copy the NLB final profile and fill only its
path and source-receipt placeholders. Keep secrets outside YAML. Run maieusis
check first; it must validate reuse before any paid call. Report the source
binding, models, coding host, paths, hashes, and estimated calls, then ask me
before starting the paid run. Do not manually copy the PaperBank or edit
source, configuration, or artifacts during the run. Afterward, show me all six
two-variant outcomes, including the validation-warning family. Never execute
the downstream analysis.
```

## Technical validation record

The published artifacts come from final NLB run
`20260715T182133Z-ec7b6cde`. It used the same immutable v0.1.0 wheel as the IBL
run, reused the IBL PaperBank through verified bindings, used no `resume`, and
closed all six family branches. Five families produced provisional planning
dossiers. NLB-003 closed as a complete readable `failed_validation` outcome:
it remains provisional/degraded and has no accepted-plan authority.

The IBL → NLB pair is bound by pair-verification digest
`2da077057e92f30a0022a0856ad11b7476654223c67e9919c487e65ca243df06`.
The [demo manifest](demo_manifest.yaml) records the public inventory, source
bindings, pinned dataset hashes, and checksums.

The guided presentation pages were rendered deterministically later from
copies of the persisted scientific artifacts. That rendering made no model,
API, or coding-agent call and did not change the original questions, plans,
outcomes, or authority.
