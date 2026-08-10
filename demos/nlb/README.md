# NLB MC_Maze-S demo

Maieusis applied its question-development workflow to a pinned dataset from the Neural Latents
Benchmark: MC_Maze-S, containing simultaneous recordings from macaque primary motor cortex (M1)
and dorsal premotor cortex (PMd) during delayed straight and curved reaches. See the
[benchmark paper](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/979d472a84804b9f647bc185a877a8b5-Abstract-round2.html)
and the [pinned DANDI dataset](https://doi.org/10.48324/dandi.000140/0.220113.0408).

Two areas recorded at once is the feature several of these questions turn on. Read
[the dataset notes](DATASET_NOTES.md) for the electrode and unit-count details that bound them.
Those notes make a specific, checkable claim about which brain region each electrode array
covers — and you do not have to take our word for it. [`verify_region_mapping.py`](verify_region_mapping.py) re-derives that mapping from the public
dataset and fails loudly if it disagrees. Run it against the real data and check us.

## Featured question — Does the shape of a neural manifold mean anything?

Motor population activity can be described as lying on a simple reusable surface, or on a curved,
context-dependent one. The trouble is that geometric complexity is not evidence of computational
function: a more elaborate description can fit better and mean nothing.

Maieusis split that into two variants, each with a different way of being wrong:

1. **Frozen shared-geometry transfer** — Does one prespecified linear subspace, with a fixed
   coordinate system and a fixed neural-to-kinematic mapping, transfer to an entirely different
   trajectory context **without refitting**? Freezing everything in advance is what makes this a
   test rather than a curve fit.
2. **Nonlinear context interaction** — For movement segments matched across contexts on measured
   kinematics including curvature, does nonlinear manifold form improve out-of-sample prediction of
   an independently defined neural outcome?

The two are deliberately not merged: cross-context generalization and added context-specific
prediction are different functional claims, and simple, low-dimensional, linear, and curved are not
interchangeable words.

Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans. No
analysis was executed and no result is reported.

**Every plan carries the depth of inspection behind it.** Maieusis records how far the planner
actually got into the data and does not round it up. This family's planner reached
`sample_inspected` by opening real data samples, as did two of its five siblings — the deepest
inspection tier of the three demonstrations. A second limit applies to the whole NLB run: its topic
literature was not independently reviewed, so these dossiers carry a lower evidence ceiling than the
IBL run's. Both labels travel with the plan, so you can weigh it correctly instead of guessing.

**[Explore both variants, their competing explanations, and what positive, negative, or null
outcomes would mean](artifacts/questions/question_families_detailed.md#family-006-functional-meaning-of-motor-manifold-form)**

Then read [the scientific reading guide](artifacts/families/manifold-form-functional-meaning/dossier_detailed.md). Its **proposal hypothesis
versus inspected evidence** section is the part worth your time: it sets what the proposal stage
assumed beside what the planner actually found in the data — one session, 142 units, 100 trials, and
a test file with no behavioural module at all — and that last fact reshaped the plan.
[The complete planning record](artifacts/families/manifold-form-functional-meaning/dossier.md) holds
the full plan, controls, and limits.

## Explore the completed demo

Six question families, twelve variants: 4 reached plans for both variants; 1 has one variant planned and its sibling held back before planning by the prior-art review; 1 closed as a scientific rejection terminal, and that family's other variant was held back on prior-art grounds too. Two variants in all were held back here, not one.

Continue to the [complete gallery](../QUESTIONS.md) for all eighteen families across the three
demonstrations, or follow this run from its inputs:

1. [Source papers and their screen](../PAPER_SOURCES.md)
2. [Paper bank summary](artifacts/paperbank/paperbank_summary.md) and the
   [formation traces](artifacts/paperbank/) built from accepted papers
3. [Reusable question-forming patterns](artifacts/paperbank/question_patterns_detailed.md)
4. [Dataset narrative](artifacts/dataset/dataset_narrative.md) — the coarse, source-backed
   description the proposal stage was given
5. [Topic evidence](artifacts/literature/topic_evidence_summary.md) and
   [research scope](artifacts/literature/research_scope.md)
6. [Question families](artifacts/questions/question_families_detailed.md), then every family dossier

Source PDFs, raw dataset files, model transcripts, credentials, and private recovery records are
not distributed.

## What produced these artifacts

Run `20260807T052026Z-f8c2bb19`, executed on the release-candidate source tree rather than by the published
package. These pages therefore demonstrate the scientific workflow; they are not a statement about
the exact bytes you install from the package index.

The evidence supporting these families is visibly draft and largely abstract-only, and the pages
say so where it applies. Prior-art review ran on every variant within a recorded scope. No question
is claimed to be novel, no plan is a result, and the analysis-execution bridge stayed closed
throughout.

---

[All demo questions](../QUESTIONS.md) · [Source papers](../PAPER_SOURCES.md) ·
[Documentation home](../../docs/INDEX.md)
