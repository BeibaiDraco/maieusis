# IBL Brain-Wide Map demo

> **v0.1.0 demo status:** a curated 43-file public artifact gallery is
> available below. It comes from the sealed high-configuration 6-family ×
> 2-variant run. Source PDFs, raw model traffic, private diagnostics, receipts,
> and hidden audit sidecars are intentionally excluded.

This demo applies Maieusis to the International Brain Laboratory (IBL)
Brain-Wide Map. It starts with 12 lawfully obtained paper PDFs, builds an
inspectable PaperBank, develops six two-variant QuestionFamilies, and gives
each family an isolated Question Owner ↔ dataset-planner branch. The product is
a supported plan, revision, honest rejection, or readable warning—not an
executed analysis. The downstream analysis bridge remains closed.

For a scientific tour of all questions, start at
[`../QUESTIONS.md`](../QUESTIONS.md). The two questions to feature on the
project homepage remain an operator editorial choice; that selection will not
change this demo's outcomes or authority.

## Sealed final proof

The final high-configuration IBL run was:

- run ID `20260715T173301Z-4eefe86a`;
- six attempted family terminals and twelve proposed variants;
- one fresh command from all 12 PDFs, with no `resume`;
- six family dossier stacks containing accepted planning material, with one
  honestly mixed family: its first variant ended
  `rejected_operationalization_failure`, while its second ended
  `accepted_requires_new_skill`;
- the same immutable v0.1.0 wheel later used by the receipt-bound NLB run; and
- sealed with the IBL → NLB pair receipt
  `2da077057e92f30a0022a0856ad11b7476654223c67e9919c487e65ca243df06`.

“Accepted” here means accepted for provisional planning after automated
independent review. No result, novelty proof, execution authority, or bridge
approval is implied.

The earlier operator-accepted Luna release gate is useful but deliberately
qualified: it used an uninterrupted 12-PDF front half and then one bounded
two-family back-half resume after planner/dossier closeout fixes. It produced
five readable dossiers and demonstrated the cap-three sliding refill, but it
was never a single-wheel one-shot run. The sealed final run above—not an
inflated description of the Luna gate—is the release demo proof.

The detailed presentation pages were deterministically rendered later from
copies of the sealed typed artifacts. That presentation-only replay made no
model, API, or coding-agent call and did not modify the original scientific
run, compact Markdown, receipts, outcomes, or authority.

## Browse the public artifact gallery

The [artifact root](artifacts/) contains only an allowlisted public subset:

- [PaperBank summary](artifacts/paperbank/paperbank_summary.md),
  [compact patterns](artifacts/paperbank/question_patterns.md), and
  [detailed patterns](artifacts/paperbank/question_patterns_detailed.md);
- public [PaperCases](artifacts/paperbank/papers/) and
  [question-formation traces](artifacts/paperbank/formation_traces/);
- [research scope](artifacts/literature/research_scope.md),
  [retrieval summary](artifacts/literature/retrieval_summary.md), and
  [topic-evidence summary](artifacts/literature/topic_evidence_summary.md);
- the [dataset narrative](artifacts/dataset/dataset_narrative.md);
- [compact QuestionFamilies](artifacts/questions/question_families.md) and the
  [detailed all-variant view](artifacts/questions/question_families_detailed.md);
  and
- six family directories under [`artifacts/families/`](artifacts/families/),
  each with the complete user-readable `dossier.md` and a lighter
  `dossier_detailed.md` scientific reading guide.

[`demo_manifest.yaml`](demo_manifest.yaml) is the machine-readable proof and
sanitized inventory. The gallery does not contain the full private run tree;
in particular, absence of a private receipt or sidecar from this directory is
intentional, not missing provenance in the sealed source run.

## Inputs for a new run

### 1. Papers

Consult [`../shared/paper_sources.yaml`](../shared/paper_sources.yaml). Obtain
the 12 content-unique PDFs lawfully and place them as direct children of one
private inbox:

```text
ibl-demo-work/
├── papers/inbox/<the exact papers[].filename values>
├── maieusis-luna.yaml
├── maieusis-final.yaml
└── runs/
```

Verify every local byte digest against `papers[].pdf_sha256` before preflight:

```bash
cd ibl-demo-work
shasum -a 256 papers/inbox/*.pdf       # macOS
# sha256sum papers/inbox/*.pdf         # Linux
```

The run starts all 12 candidates and preserves honest downstream dispositions;
it does not require every intermediate paper product to be perfect. Maieusis
identifies the cohort by its exact filename/SHA-256 set. PDFs remain outside
the public repository and must never be committed.

### 2. IBL data and documentation

Use the public IBL services and the official
[Brain-Wide Map release guide](https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html).
The release tag is `Brainwidemap`. Follow the official
[ONE data-download guide](https://int-brain-lab.github.io/iblenv/notebooks_external/data_download.html)
to install the IBL environment and cache the required sessions, metadata, and
small samples under a dedicated external root such as
`/data/maieusis/ibl-bwm`. Use public OpenAlyx, not a private member endpoint.

A minimal public-session discovery check is:

```python
from one.api import ONE

one = ONE(base_url="https://openalyx.internationalbrainlab.org")
brainwide_sessions = one.search(project="brainwide")
print(len(brainwide_sessions))
```

Keep the downloaded dataset outside the repository and make it read-only for
the run:

```bash
chmod -R a-w /data/maieusis/ibl-bwm
```

The planner may inspect documentation, code, metadata, and bounded samples. It
may not run a full scientific analysis, inspect confirmation outcomes, or
search for a result.

### 3. Models, coding-agent host, and configuration

Complete [installation](../../docs/INSTALLATION.md) and either the
[coding-agent setup](../../docs/AGENT_GUIDED_SETUP.md) or
[manual setup](../../docs/MANUAL_SETUP.md). Keep API keys outside YAML.

Copy the checked-in profiles into the private work directory:

```bash
cp "$MAIEUSIS_REPO/examples/release/ibl-luna-clean-gate.yaml" maieusis-luna.yaml
cp "$MAIEUSIS_REPO/examples/release/ibl-final-quality.yaml" maieusis-final.yaml
```

In each copy, replace only the explicit `/ABSOLUTE/PATH/...` values:

- `paperbank.inbox_dir` → the private PDF inbox;
- `dataset.inspection_runtime.dataset_root` → the read-only IBL root;
- `inspection_python` → the IBL environment's Python executable;
- `source_tree_root` → a clean checkout of the candidate source tree; and
- `run.output_root` → a new, empty output root for that profile.

The frozen profiles request six families with two variants each, at most three
concurrent family workers, three bounded revision rounds, and no consolidation.
The final-quality profile explicitly uses Codex CLI with
`coding_model=gpt-5.6-terra` and `coding_reasoning_effort=high`; this coding
host is distinct from the scientific model APIs. Novelty is disabled and must
be reported as `not_assessed`.

## Reproduce the release route

Preflight makes zero paid calls. Resolve every failure before authorizing a
run:

```bash
maieusis check --project maieusis-luna.yaml
maieusis run --project maieusis-luna.yaml
```

The Luna profile is a bounded readiness gate. For a new run, do not edit
artifacts or change source/configuration while it is active. Honest scientific
rejection, mixed outcomes, and typed readable warnings are valid; provider,
provenance, filesystem, branch-isolation, or orchestration failures are not
scientific rejections.

After inspecting the gate, run the final-quality profile from a new output
root:

```bash
maieusis check --project maieusis-final.yaml
maieusis run --project maieusis-final.yaml
```

The serious route requires a frontier model API, a coding-agent host, and the
real external dataset. Model-driven prose is not expected to be byte-identical
to the sealed demo; the reproducibility contract is the pinned configuration,
typed stages, bounded orchestration, receipts, visible intermediates, and
honest terminal outcomes.

## Inspect a newly generated private run

Open `<output-root>/<run-id>/README.md`, then inspect:

- `run_manifest.yaml` and `summary.md` for run completion and outcomes;
- `paperbank/papers/*.md`, `formation_traces/*.md`,
  `question_patterns.md`, and `question_patterns_detailed.md` for the
  paper-to-pattern chain;
- `literature/` and `dataset/dataset_narrative.md` for proposal context;
- `questions/question_families.md` and
  `questions/question_families_detailed.md` before planning;
- every `families/<family-slug>/dossier.md` and `dossier_detailed.md`; and
- the private manifests, receipts, and hidden sidecars for provenance.

Do not treat a dossier as a result. It is a reviewed plan-or-reject closure
package produced before execution.

## Copy/paste prompt for a coding agent

```text
Reproduce the Maieusis IBL demo using demos/ibl/README.md. Work in a new
directory and isolated environment. Obtain the 12 listed papers lawfully,
verify every filename and SHA-256 against demos/shared/paper_sources.yaml, and
keep PDFs out of git. Prepare the public IBL Brain-Wide Map subset read-only by
following the linked official guides. Copy the Luna and final-quality profiles,
replace only their path placeholders, and keep secrets outside YAML. Run
maieusis check first; it must make zero paid calls. Report the resolved models,
coding host, paths, input hashes, and estimated calls, and ask me before a paid
run. Do not change source, configuration, or artifacts during a run. Inspect
all six two-variant family terminals, the detailed presentation pages,
receipts, and dossiers. Never execute an analysis or open the downstream
bridge.
```
