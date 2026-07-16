# Neural Latents Benchmark MC_Maze-S demo

> **v0.1.0 demo status:** a curated 43-file public artifact gallery is
> available below. It comes from the sealed high-configuration 6-family ×
> 2-variant receipt-bound NLB run. Source PDFs, NWB data, raw model traffic,
> private diagnostics, receipts, and hidden audit sidecars are intentionally
> excluded.

This demo applies Maieusis to Neural Latents Benchmark (NLB) MC_Maze-S data in
[DANDI:000140](https://dandiarchive.org/dandiset/000140). It reuses the sealed
IBL run's PaperBank through an exact typed receipt, then regenerates the
dataset narrative, literature context, QuestionFamilies, isolated planning
branches, reviews, and dossiers for NLB. It stops before analysis execution;
the downstream analysis bridge remains closed.

For a scientific tour of all questions, start at
[`../QUESTIONS.md`](../QUESTIONS.md). The two questions to feature on the
project homepage remain an operator editorial choice; that selection will not
change this demo's outcomes or authority.

## Sealed final proof

The final high-configuration NLB run was:

- run ID `20260715T182133Z-ec7b6cde`;
- six attempted family terminals and twelve proposed variants;
- one fresh command with no `resume`;
- five accepted planning-dossier stacks plus one complete, user-readable
  `failed_validation` family terminal;
- exact IBL PaperBank reuse bound to paper-half receipt
  `fbfa86c4ee1e1f925488f3d5c5b8f388a61700ab6e37fac5d613e85ffd03e4d6`;
- the same immutable v0.1.0 wheel as the source IBL run; and
- sealed with the IBL → NLB pair receipt
  `2da077057e92f30a0022a0856ad11b7476654223c67e9919c487e65ca243df06`.

The warning family, “Preparatory population dynamics as operating regimes for
movement,” is provisional/degraded and has **no accepted-plan authority** for
either variant. Retained scientific context remains useful, but Owner or
reviewer prose cannot override the typed validation terminal. The run is
processing-complete because this is an honest readable soft terminal, not
because the validation problem was relabeled as scientific acceptance.

“Accepted” elsewhere means accepted for provisional planning after automated
independent review. No result, novelty proof, execution authority, or bridge
approval is implied.

The earlier operator-accepted Luna gate belonged to the source IBL release
sequence and remains deliberately qualified: it used an uninterrupted 12-PDF
front half and then one bounded two-family back-half resume after
planner/dossier closeout fixes. It produced five readable dossiers, but it was
never a single-wheel one-shot run. The zero-resume sealed IBL → NLB pair—not an
inflated description of that gate—is the final release proof.

The detailed presentation pages were deterministically rendered later from
copies of the sealed typed artifacts. That presentation-only replay made no
model, API, or coding-agent call and did not modify the original scientific
run, compact Markdown, receipts, outcomes, or authority.

## Browse the public artifact gallery

The [artifact root](artifacts/) contains only an allowlisted public subset:

- the sanitized public
  [PaperBank import record](artifacts/provenance/paperbank_import.yaml);
- [PaperBank summary](artifacts/paperbank/paperbank_summary.md),
  [compact patterns](artifacts/paperbank/question_patterns.md), and
  [detailed patterns](artifacts/paperbank/question_patterns_detailed.md);
- imported public [PaperCases](artifacts/paperbank/papers/) and
  [question-formation traces](artifacts/paperbank/formation_traces/);
- [research scope](artifacts/literature/research_scope.md),
  [retrieval summary](artifacts/literature/retrieval_summary.md), and
  [topic-evidence summary](artifacts/literature/topic_evidence_summary.md);
- the NLB-specific [dataset narrative](artifacts/dataset/dataset_narrative.md);
- [compact QuestionFamilies](artifacts/questions/question_families.md) and the
  [detailed all-variant view](artifacts/questions/question_families_detailed.md);
  and
- six family directories under [`artifacts/families/`](artifacts/families/),
  each with a user-readable `dossier.md` and a lighter
  `dossier_detailed.md` scientific reading guide.

[`demo_manifest.yaml`](demo_manifest.yaml) is the machine-readable proof and
sanitized inventory. The gallery does not contain the full private run tree;
in particular, absence of private receipts, branch evidence, or sidecars from
this directory is intentional, not missing provenance in the sealed source
run.

## What is reused—and what is not

The NLB inbox must contain the same exact 12 PDF filenames and bytes as the IBL
source run. Before any provider is constructed, `paperbank.import_from_run`
checks the current filename/SHA-256 set, source paper-half receipt hash and
status, parser and implementation versions, prompt versions, provider/model
identities, configuration digest, and every imported output hash. A mismatch
fails closed with no paid call.

The import copies only receipt-owned typed PaperBank products and required
paper-half stage outputs. The private run records `imports/paperbank.yaml` with
the source run ID and full bindings; the public gallery contains only a
sanitized provenance projection and never the absolute source path.

NLB does **not** reuse the IBL DatasetNarrative, research scope, topic evidence,
QuestionFamilies, shortlist, Owner/planner conversations, inspection evidence,
plans, reviews, closures, dossiers, captures, or raw PDFs. Those scientific
products were rebuilt for NLB.

## Inputs for a new run

### 1. Identical private paper inbox

Obtain the sources in
[`../shared/paper_sources.yaml`](../shared/paper_sources.yaml) lawfully and use
the exact same 12-candidate filename/SHA-256 set as IBL:

```text
nlb-demo-work/
├── papers/inbox/<the exact papers[].filename values>
├── maieusis-final.yaml
└── runs/
```

Verify every digest with `shasum -a 256` on macOS or `sha256sum` on Linux.
The inbox path may differ from IBL; its filename/byte set may not. PDFs remain
outside the public repository and must never be committed.

### 2. NLB MC_Maze-S from DANDI

The release proof pins published DANDI version `0.220113.0408` in
[`demo_manifest.yaml`](demo_manifest.yaml). Do not silently substitute a draft
or another version.

Following the official
[DANDI download guide](https://docs.dandiarchive.org/user-guide-using/accessing-data/downloading/),
create a separate environment and download the pinned version:

```bash
python -m pip install dandi
export NLB_DANDI_VERSION='0.220113.0408'
mkdir -p /data/maieusis/nlb
cd /data/maieusis/nlb
dandi download "DANDI:000140/${NLB_DANDI_VERSION}"
chmod -R a-w /data/maieusis/nlb/000140
```

The planner's `dataset_root` must point to that read-only `000140` directory.
Consult the [NLB documentation](https://neurallatents.github.io/) and DANDI
metadata, retain their identifiers in run provenance, and include
[`DATASET_NOTES.md`](DATASET_NOTES.md) in `dataset.seed.docs`. That note records
the official MC_Maze M1-electrode conversion caveat; uncorrected
`units/electrodes` values must not be used to infer that the sorted-unit
population is PMd-only.

Verify the pinned file hashes from `demo_manifest.yaml`, then run the bounded
metadata-only region check in the NLB inspection environment:

```bash
python demos/nlb/verify_region_mapping.py /data/maieusis/nlb/000140
```

It must report train `PMd=72 M1=70` and test `PMd=52 M1=55` before a paid run.

### 3. Receipt-bound import configuration

Complete [installation](../../docs/INSTALLATION.md) and either the
[coding-agent setup](../../docs/AGENT_GUIDED_SETUP.md) or
[manual setup](../../docs/MANUAL_SETUP.md). Keep API keys outside YAML.

Copy `examples/release/nlb-final-quality.yaml` to `maieusis-final.yaml`, replace
only its explicit path/receipt placeholders, and preserve this shape:

```yaml
paperbank:
  inbox_dir: /ABSOLUTE/PATH/TO/THE/IDENTICAL/12-PDF-INBOX
  import_from_run:
    source_run_root: /ABSOLUTE/PATH/TO/ACCEPTED/IBL/FINAL/RUN
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

Compute the private source receipt digest locally:

```bash
shasum -a 256 /path/to/ibl-final-run/receipts/paper-half.yaml
# sha256sum /path/to/ibl-final-run/receipts/paper-half.yaml  # Linux
```

Keep the extraction, pattern, and reviewer identities exactly equal to the IBL
final profile. The importer validates those identities even though it makes no
paper-half model calls. The frozen profile requests six families with two
variants each, at most three concurrent family workers, and explicitly uses
Codex CLI with `coding_model=gpt-5.6-terra` and
`coding_reasoning_effort=high`.

## Reproduce the NLB route

The accepted IBL final-quality run is a prerequisite. With the same immutable
wheel and a clean source checkout:

```bash
maieusis check --project maieusis-final.yaml
maieusis run --project maieusis-final.yaml
```

Preflight and import validation make zero paid calls. Resolve every input,
receipt, model, prompt, path, and output-hash failure before authorizing the
run. Do not copy a PaperBank directory manually, edit imported files, or change
source/configuration while the run is active.

Every returned family must reach an honest readable terminal. Accepted,
mixed, rejected, and warning outcomes are valid scientific-product closures;
provider, provenance, filesystem, branch-isolation, or orchestration failures
are not scientific rejections. Model-driven prose is not expected to be
byte-identical to the sealed demo; the reproducibility contract is the pinned
configuration, receipt-bound import, typed stages, bounded orchestration,
visible intermediates, and honest terminals.

## Inspect a newly generated private run

Open `<output-root>/<run-id>/README.md`, then inspect:

- `imports/paperbank.yaml` for exact cross-run reuse bindings;
- `run_manifest.yaml` and `summary.md` for completion and outcomes;
- `paperbank/` for the user projection rebuilt from imported typed products;
- `literature/` and `dataset/dataset_narrative.md` for newly generated NLB
  context;
- `questions/question_families.md` and
  `questions/question_families_detailed.md` for all variants; and
- every `families/<family-slug>/dossier.md`, `dossier_detailed.md`, private
  completion record, receipt, and hidden sidecar.

Confirm that no IBL dataset narrative, family, branch-local evidence, or
dossier was carried into NLB as though it were NLB evidence. Do not treat a
dossier as a scientific result.

## Copy/paste prompt for a coding agent

```text
Reproduce the Maieusis NLB MC_Maze-S demo using demos/nlb/README.md. First
verify that the designated IBL final-quality source run is complete and
immutable. Prepare the same exact 12 paper filenames and bytes in a private NLB
inbox and verify them against demos/shared/paper_sources.yaml. Download pinned
DANDI:000140 version 0.220113.0408, keep it outside git, make it read-only, and
run the region-mapping check. Copy the NLB final profile and fill only its path
and source-receipt placeholders. Keep extraction, pattern, and reviewer
identities equal to IBL and keep secrets outside YAML. Run maieusis check first;
it must validate the PaperBank import before any paid call. Report bindings,
models, coding host, hashes, and estimated calls, and ask me before running.
Do not manually copy the PaperBank or edit source, configuration, or artifacts
during a run. Inspect all six two-variant terminals, including the honest
validation-warning path. Never execute an analysis or open the downstream
bridge.
```
