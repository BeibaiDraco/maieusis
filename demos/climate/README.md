# Climate demo — ERA5-derived stratospheric dynamics

Maieusis applied its question-development workflow to an ERA5-derived record of 60 degrees North
stratospheric dynamics: wave activity, zonal winds, and eddy forcing on a 97-level vertical column
from 0 to 48 km, six-hourly, across roughly four decades.

This is the demonstration that shows Maieusis is not a neuroscience tool. Nothing in the system was
adapted for atmospheric science. The same pipeline was handed twenty climate-dynamics papers and a
source-backed description of this dataset, and developed six question families against it. Of the
twenty papers it read seventeen — three PDFs would not parse — and accepted thirteen into the bank.

Read [the dataset notes](DATASET_NOTES.md) before the science. This dataset is a single vertical
column with no longitude and no latitude, and that shapes what can honestly be asked of it.

## Featured — a question this dataset could not answer, and why that is the useful part

Most of what follows are plans. This one is not, and it is the artifact worth reading first, because
a plan cannot show you whether a system actually looked at your data. A refusal can.

The family asked two things about sudden stratospheric warmings:

1. **Forcing-first sequence** — Within Northern Hemisphere extended-winter warmings, does
   independently diagnosed eddy forcing follow a prespecified vertical sequence, and does that
   sequence differ between Ural and Aleutian precursor pathways, and between displacement and split
   morphologies?
2. **Antecedent susceptibility under matched forcing** — Among forcing episodes matched on
   magnitude, wave spectrum, duration, prior history and season, does the preceding 100–10 hPa
   zonal-mean wind structure change what happens next, after conditioning on ENSO and QBO?

Both are ordinary, publishable questions. A stratospheric dynamicist would nod at either.

Outcome: **Scientific rejection terminal** — both variants closed without a plan.

**The planner opened the data and found the question could not survive it.** Ural versus Aleutian is
a *longitudinal* distinction, and this dataset is a one-dimensional column at 60 degrees North: it
has no longitude and no latitude, so those pathways cannot be separated at all. The second variant
needs a 100–10 hPa pressure profile and matched ENSO and QBO series; the package documents no
pressure coordinate and carries no such series. The dossier states the alternative it refused:
substituting height-indexed or unconditioned proxies "would materially alter the question."

That refusal is the behaviour worth checking. A model that wanted to please would have swapped in a
height proxy, produced a competent-looking plan, and left the substitution buried in a methods
paragraph. This one stopped, said which construct was missing, and then said what data would make
the question answerable — an event-ready reanalysis product with documented calendar, pressure
coordinate, units and sign conventions, plus fields sufficient to define warming onset.

**[Explore both variants, their competing explanations, and what positive, negative, or null
outcomes would mean](artifacts/questions/question_families_detailed.md#family-002-wave-forcing-circulation-response-and-state-dependent-feedback)**

Then read [the scientific reading guide](artifacts/families/wave-forcing-and-state-dependence/dossier_detailed.md),
whose **proposal hypothesis versus inspected evidence** section sets what the proposal stage assumed
beside what the planner found. [The full record](artifacts/families/wave-forcing-and-state-dependence/dossier.md)
carries the complete reasoning and the data requirements.

**Four of the six families in this run did produce plans**, including a two-variant study of
propagating episodes versus coherent modes of vertical coupling. They are all in the gallery below.

## Explore the completed demo

Six question families, twelve variants: 1 reached plans for both variants; 3 are mixed, with one variant planned and its sibling closed with a reason; 2 closed as scientific rejection terminals. In one of those two, a variant had already been held back before planning by the prior-art review.

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

Run `20260806T144407Z-c6f4bf64`, executed on the release-candidate source tree rather than by the published
package. These pages therefore demonstrate the scientific workflow; they are not a statement about
the exact bytes you install from the package index.

The evidence supporting these families is visibly draft and largely abstract-only, and the pages
say so where it applies. Prior-art review ran on every variant within a recorded scope. No question
is claimed to be novel, no plan is a result, and the analysis-execution bridge stayed closed
throughout.

---

[All demo questions](../QUESTIONS.md) · [Source papers](../PAPER_SOURCES.md) ·
[Documentation home](../../docs/INDEX.md)
