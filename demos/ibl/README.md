# IBL Brain-Wide Map demo

This demo applies Maieusis to the International Brain Laboratory (IBL)
Brain-Wide Map: a standardized, multi-laboratory collection of brain-wide
Neuropixels recordings from mice performing a sensory decision task. For the
dataset and its scientific context, see the International Brain Laboratory's
[*A brain-wide map of neural activity during complex behaviour*
(2025)](https://doi.org/10.1038/s41586-025-09235-0) and the official
[Brain-Wide Map release guide](https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html).

Maieusis used 12 source papers, the public dataset documentation, and bounded
read-only inspection of the dataset to develop six two-variant question
families. Each family then received its own Question Owner–Dataset Planner
dialogue and independent plan review. The output is a plan, an explicit reason
not to proceed, or a readable warning—not an executed scientific analysis.

## Featured question — When does shared neural variability matter for a decision?

Neural populations fluctuate from trial to trial, but the size of those
fluctuations is only part of the story. Two populations can vary by the same
amount and still have very different behavioral consequences: variability
aligned with a decision-relevant direction could change a choice, whereas
equally large variability in an orthogonal direction may be largely irrelevant.

IBL-002 turns that distinction into two complementary questions. The first asks
whether alignment with an independently defined decision direction predicts
held-out choice and reaction time beyond overall covariance magnitude. The
second asks whether apparently decision-related dimensions are better explained
by pose and ongoing behavioral state. Together they distinguish a task-specific
account of population variability from a generic movement-or-state account.

Both variants produced provisionally accepted planning dossiers. No analysis
was executed, and novelty remained `not_assessed`.

**[Explore both variants, their alternatives, assumptions, and possible
outcomes](artifacts/questions/question_families_detailed.md#family-002-which-shared-variability-dimensions-matter-for-decisions)**

[See the planned study at a glance](artifacts/families/covariance-alignment/dossier_detailed.md)
· [Open the complete planning record](artifacts/families/covariance-alignment/dossier.md)

## Explore the completed demo

Start with the **[complete question gallery](../QUESTIONS.md)**. It introduces
all twelve families across both public demos and links every variant to its
scientific background and planning outcome. Within the IBL run:

- five families produced provisional plans for both variants;
- one family is mixed: one variant stopped because it could not be
  operationalized faithfully, while its sibling produced a plan that would
  require a new execution skill; and
- all six families retain readable closure records.

To follow the IBL question-development process from its inputs:

1. **Prior papers:** read the [12-paper source guide](../PAPER_SOURCES.md), then
   browse the [PaperBank overview](artifacts/paperbank/paperbank_summary.md),
   [PaperCases](artifacts/paperbank/papers/), and
   [question-formation traces](artifacts/paperbank/formation_traces/).
2. **Reusable question-forming moves:** read the
   [full pattern explanation](artifacts/paperbank/question_patterns_detailed.md).
3. **Dataset and current literature:** read the
   [dataset narrative](artifacts/dataset/dataset_narrative.md),
   [research scope](artifacts/literature/research_scope.md), and
   [topic-evidence summary](artifacts/literature/topic_evidence_summary.md).
4. **All proposed questions:** open the
   [full two-variant family page](artifacts/questions/question_families_detailed.md).
5. **Dataset-grounded outcomes:** continue from each family in the gallery to
   its plan guide and complete planning record.

The published gallery contains reader-facing scientific artifacts. Source
PDFs, downloaded IBL data, model transcripts, credentials, and private recovery
records are not distributed.

## Reproduce the demo

The instructions below run the final-quality route once. An earlier lower-cost
qualification sequence was a maintainer validation exercise, not a prerequisite
for a normal demo run; it is documented in the technical record at the end.

### 1. Install Maieusis and prepare credentials

Complete [installation](../../docs/INSTALLATION.md) and either the
[coding-agent setup](../../docs/AGENT_GUIDED_SETUP.md) or
[manual setup](../../docs/MANUAL_SETUP.md). The standard route requires:

- scientific-model API credentials from two supported providers so the
  Question Owner and independent reviewer use different providers; and
- a separately authenticated Codex CLI or Claude Code coding-agent host.

Keep credentials out of YAML and out of the repository.

### 2. Obtain the 12 source papers

Use the human-readable [paper source guide](../PAPER_SOURCES.md) to obtain the
12 PDFs lawfully. For exact reproduction with the checked-in profile, place them
under their listed filenames as direct children of a private inbox:

```text
ibl-demo-work/
├── papers/inbox/<the 12 listed PDF filenames>
├── maieusis-final.yaml
└── runs/
```

Verify the local files against the SHA-256 values in the
[machine-readable source manifest](../shared/paper_sources.yaml):

```bash
export MAIEUSIS_REPO=/absolute/path/to/your/maieusis-source-checkout
cd /absolute/path/to/ibl-demo-work
shasum -a 256 papers/inbox/*.pdf       # macOS
# sha256sum papers/inbox/*.pdf         # Linux
```

Keep the PDFs outside git. The run starts all 12 candidates and preserves
honest downstream dispositions; it does not require every paper-derived
intermediate to be accepted.

### 3. Prepare the IBL dataset read-only

Use the public IBL services and follow the official
[Brain-Wide Map release guide](https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html).
The release tag is `Brainwidemap`. Follow the official
[ONE data-download guide](https://int-brain-lab.github.io/iblenv/notebooks_external/data_download.html)
to install the IBL environment and cache the required sessions, metadata, and
bounded samples under a dedicated external root.

A minimal public-session discovery check is:

```python
from one.api import ONE

one = ONE(base_url="https://openalyx.internationalbrainlab.org")
brainwide_sessions = one.search(project="brainwide")
print(len(brainwide_sessions))
```

Use public OpenAlyx, not a private member endpoint. Keep the downloaded dataset
outside the repository and make the prepared root read-only for the run, for
example:

```bash
chmod -R a-w /data/maieusis/ibl-bwm
```

The Dataset Planner may inspect documentation, code, metadata, and bounded
samples. It may not run the final scientific analysis or search for a desired
result.

### 4. Configure the final-quality run

Copy the checked-in profile into the private work directory:

```bash
cp "$MAIEUSIS_REPO/examples/release/ibl-final-quality.yaml" maieusis-final.yaml
```

In the copy, replace only the explicit `/ABSOLUTE/PATH/...` values:

- `paperbank.inbox_dir` → the private PDF inbox;
- `dataset.inspection_runtime.dataset_root` → the read-only IBL root;
- `inspection_python` → the IBL environment's Python executable;
- `source_tree_root` → a clean checkout of Maieusis; and
- `run.output_root` → a new, empty output root.

The checked-in profile requests six families with two variants each, at most three
concurrent family workers, and three bounded revision rounds. It uses Codex CLI
with `coding_model=gpt-5.6-terra` and
`coding_reasoning_effort=high`; this coding-host subscription is distinct from
the scientific-model API credentials. Novelty assessment is disabled and must
remain reported as `not_assessed`.

### 5. Check, authorize, and run

Preflight makes zero paid calls:

```bash
maieusis check --project maieusis-final.yaml
```

Resolve every reported problem, inspect the selected models and paths, and make
an explicit human decision before starting the paid run:

```bash
maieusis run --project maieusis-final.yaml
```

Do not edit source, configuration, or generated artifacts while the run is
active. Honest scientific rejection, mixed outcomes, and readable warnings are
valid outcomes; infrastructure or provenance failures are not scientific
rejections.

Model-generated prose is not expected to be byte-identical to this published
demo. Reproduction here means using the pinned inputs and configuration through
the same typed, bounded workflow and receiving inspectable terminal outcomes.

## Read a newly generated run

Open `<output-root>/<run-id>/README.md`, then follow this order:

1. `summary.md` for overall completion and family outcomes;
2. `paperbank/question_patterns_detailed.md` for the source-derived patterns;
3. `questions/question_families_detailed.md` for every proposed variant;
4. each `families/<family-slug>/dossier_detailed.md` for a guided plan overview;
5. each `families/<family-slug>/dossier.md` for the complete planning record;
6. `run_manifest.yaml` and private provenance records when auditing integrity or
   resuming a local run.

A dossier is a reviewed plan-or-stop decision produced before execution, not a
scientific result.

## Copy/paste prompt for a coding agent

```text
Reproduce the Maieusis IBL demo using demos/ibl/README.md. Work in a new
directory and isolated environment. Obtain the 12 listed papers lawfully,
verify every filename and SHA-256 against demos/shared/paper_sources.yaml, and
keep PDFs out of git. Prepare the public IBL Brain-Wide Map data read-only by
following the linked official guides. Copy the final-quality profile and
replace only its path placeholders. Keep secrets outside YAML. Run maieusis
check first; it must make zero paid calls. Report the resolved models, coding
host, paths, input hashes, and estimated calls, then ask me before starting the
paid run. Do not change source, configuration, or artifacts during the run.
Afterward, show me all six two-variant family outcomes and guide me through the
detailed question pages and dossiers. Never execute the downstream analysis.
```

## Technical validation record

The published artifacts come from final IBL run
`20260715T173301Z-4eefe86a`. It began from all 12 PDFs in one fresh command,
used no `resume`, and closed all six family branches. Five families produced
plans for both variants; the sixth was mixed, with
`rejected_operationalization_failure` for one variant and
`accepted_requires_new_skill` for the other.

The same immutable v0.1.0 wheel was later used for the NLB run. The pair is
bound by pair-verification digest
`2da077057e92f30a0022a0856ad11b7476654223c67e9919c487e65ca243df06`.
The [demo manifest](demo_manifest.yaml) records the complete public inventory
and checksums.

An earlier pre-release qualification used an uninterrupted 12-PDF front half
followed by one bounded two-family back-half resume after bounded closeout
corrections. It was useful validation, but it was not the one-shot final run
and is not required for an ordinary reproduction attempt.

The guided presentation pages were rendered deterministically later from
copies of the persisted scientific artifacts. That rendering made no model,
API, or coding-agent call and did not change the original questions, plans,
outcomes, or authority.
