# IBL Brain-Wide Map demo

Maieusis applied its question-development workflow to the International Brain Laboratory
Brain-Wide Map: a standardized, multi-laboratory collection of Neuropixels recordings from mice
performing a sensory decision-making task. See the
[primary Nature paper](https://doi.org/10.1038/s41586-025-09235-0) and the
[official release guide](https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html).

The distinguishing feature of this dataset is repetition: the same protocol, run across
laboratories. Several of the questions below exist only because that repetition makes
reproducibility and idiosyncrasy separable.

## Featured question — Task relevance of structured neural co-variability

Co-variability may be a global nuisance, a task-aligned computational resource, or structured modulation associated primarily with embodied state rather than decision processing.

Maieusis split that into two variants:

1. **Task-aligned structure versus aggregate magnitude** — Is the relationship between neural co-variability and decision performance better explained by alignment with stimulus- or choice-relevant population dimensions than by overall co-variability magnitude?
2. **Decision organization versus embodied co-variation** — Is structured population co-variability associated more strongly with decision variables or with video-derived movement and pose states?

Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans. No analysis was
executed and no result is reported.

**Every plan carries the depth of inspection behind it.** Maieusis records how far the planner
actually got into the data and does not round it up. This family's planner reached inspected schema
metadata (`schema_metadata_inspected`); one sibling in this run, the anatomical-breadth family, went
deeper and opened real data samples. This is also the one demonstration whose topic literature passed
independent review, so its dossiers carry a higher evidence ceiling than the climate and NLB runs.
The labels travel with each plan, so you can weigh it correctly instead of guessing.

**[Explore both variants, their competing explanations, and what positive, negative, or null
outcomes would mean](artifacts/questions/question_families_detailed.md#family-002-task-relevance-of-structured-neural-co-variability)**

Then read [the scientific reading guide](artifacts/families/covariability-structure/dossier_detailed.md). Its **proposal hypothesis versus
inspected evidence** section is the part worth your time: it sets what the proposal stage assumed
beside what the planner actually found when it inspected the data, including where the two did not
agree. [The complete planning record](artifacts/families/covariability-structure/dossier.md) holds the full plan, controls, and limits.

## Explore the completed demo

Six question families, twelve variants: 2 reached plans for both variants; 2 had one variant held back before planning by the prior-art review; 2 are mixed, with one variant planned and its sibling closed with a reason.

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

Run `20260806T190138Z-2249f35e`, executed on the release-candidate source tree rather than by the published
package. These pages therefore demonstrate the scientific workflow; they are not a statement about
the exact bytes you install from the package index.

The evidence supporting these families is visibly draft and largely abstract-only, and the pages
say so where it applies. Prior-art review ran on every variant within a recorded scope. No question
is claimed to be novel, no plan is a result, and the analysis-execution bridge stayed closed
throughout.

---

[All demo questions](../QUESTIONS.md) · [Source papers](../PAPER_SOURCES.md) ·
[Documentation home](../../docs/INDEX.md)
