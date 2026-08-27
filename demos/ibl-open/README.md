# IBL demo, asked open: the same recordings, with nothing declared

This page uses the same dataset as the [IBL demonstration next door](../ibl/README.md) — the
International Brain Laboratory's Brain-Wide Map, where a mouse reports which side of a screen a
visual stimulus appeared on by turning a wheel, while Neuropixels probes record spiking across
nearly all major brain areas and cameras record its face and body. That page describes the data;
this one is about a different question, which is what happens when you do not tell the system what
to look for.

**Two runs, one difference.** The IBL demonstration was given a research intent with a declared
anchor: the single topic term *noise correlations*. This run was given an intent with no terms at
all. Instead of being handed a subject, it read the dataset's own coarse description and derived its
own scope — the terms it would search the literature for, the construct families it would work in,
and the parts of the field it would stay out of. That derived scope is published as
[research scope](artifacts/literature/research_scope.md), and its `Mode: open_inferred` line is the
mark of a run that chose for itself.

Everything else was held fixed. Same twelve papers, same recordings, same models in every role, same
six-questions-by-two-versions shape, same wheel. The only difference between these two
demonstrations is one field in one configuration file.

## What the difference produced

**No family appears in both runs.** Not one shared title, not one renamed pair: twelve families,
twelve distinct framings.

That is a claim about how the runs *organised* the territory, not about whether they visited any of
the same ground. They did — both reached the geometry of shared variability, from opposite
directions — and the individual questions are worth reading side by side for exactly that reason.
What differs is which contrasts each run decided were the ones worth building six families around.

Declaring *noise correlations* did not restrict the anchored run to a subset of what this one found.
It moved it. The anchored run went to the alignment of shared variability, its regional
organization, and whether its statistics reproduce across laboratories. This one went to the
temporal structure of evidence accumulation, the origin of choice-predictive activity, what survives
richer movement accounting, the geometry of shared variability, the functional form of mixed
selectivity, and the population geometry of sensorimotor transformation.

Both lists are defensible questions about the same recordings. That is the point, and it is also the
cost: **an anchor is a commitment, not a hint.** A term that suits the dataset concentrates six
questions where they are worth asking. A term that does not will steer all six somewhere else, and
nothing downstream recovers the questions that were never proposed. Open mode does not remove that
risk so much as move it — the scope is then derived from a description of the dataset, and the
[research scope](artifacts/literature/research_scope.md) page exists so you can check what it decided
before you read anything built on it.

**One family here shows the shape of that check.** *Temporal origin of choice-predictive population
activity* never reached a planner. Prior-art review stopped every one of its versions and closed the family before the shortlist gate,
so there is no plan and no reading guide — a planning branch was never opened. Its page carries the
question in full and the disposition the run recorded for each version. A demonstration
that dropped it would be showing you a five-question run.

## Featured: the geometry of shared variability, arrived at without being asked

The [featured family](artifacts/families/variability-geometry/dossier.md) is the one worth putting
beside the anchored run. Nobody told this run to think about shared trial-to-trial variability. It
derived a scope from the dataset description, searched the literature inside it, and arrived at the
functional geometry of shared variability anyway — then asked whether that geometry is organized by
the population dimensions carrying sensory evidence and choice, rather than by overall correlation
magnitude.

The anchored run reached related ground by being pointed at it. This one reached it by reading. Set
the two families side by side — this one, and
[the anchored run's covariance-geometry family](../ibl/artifacts/families/accumulation-geometry/dossier.md)
— and what you are comparing is not which question is better but what the declaration changed about
how each was arrived at, and how far into the data each planner then got.

Every family below links a reading guide whose *proposal hypothesis versus inspected evidence*
section sets what the proposal stage assumed the recordings offered beside what the planner actually
found in them. For this run that comparison carries extra weight: the proposal stage was working
from a scope the system derived itself, so the guide is where you can see whether the derivation
held up against the data.

Nothing here was executed. Every plan on this page was checked by a second model on a different
provider, independently of the model that wrote it, and then stopped. No analysis was run and no
result is reported.

## The six questions, and what happened to each

<!-- generated: six questions -- scripts/render_demo_gallery.py -->

**Two of the six reached plans for both versions**, and every other family is below with what happened to each — a closed version stays on the page with the reason it closed. Five of the six questions produced plans at all.

### 1. Persistent versus sequential population dynamics during evidence accumulation

*Family 001: Persistent versus sequential population dynamics during evidence accumulation*

Evidence accumulation is established as a useful account of perceptual decisions, but persistent and sequential neural implementations remain unresolved and may differ across brain populations.

1. [**Representational-form variant**](artifacts/questions/question_families_detailed.md#variant-001001-representational-form-variant) — Across brain populations engaged during decision formation, is accumulated evidence expressed predominantly through persistent population states or through choice-selective sequential trajectories?
2. [**Behavioral-prediction variant**](artifacts/questions/question_families_detailed.md#variant-001002-behavioral-prediction-variant) — Do persistent and sequential population signatures differ in how they predict trial-to-trial choice and response-time variation during evidence accumulation?

**Outcome: Plan developed (provisional).** Both versions got a plan.

[The question in full](artifacts/questions/question_families_detailed.md#family-001-persistent-versus-sequential-population-dynamics-during-evidence-accumulation) ·
[full planning record](artifacts/families/accumulation-dynamics/dossier.md)

### 2. Temporal origin of choice-predictive population activity

*Family 002: Temporal origin of choice-predictive population activity*

Choice-predictive activity may reflect bottom-up sensory variability, top-down decision-related feedback, movement preparation, or mixtures of these processes; choice association alone cannot adjudicate among them.

1. [**Temporal-origin variant**](artifacts/questions/question_families_detailed.md#variant-002001-temporal-origin-variant) — Does choice-predictive population activity shift over a trial from an early sensory-linked component to a later decision- or preparation-linked component?
2. [**Spatial-organization variant**](artifacts/questions/question_families_detailed.md#variant-002002-spatial-organization-variant) — Are sensory-linked and later decision-linked components of choice-predictive activity spatially concentrated in different processing populations or distributed across major brain regions?

**Outcome: Stopped before planning on prior-art grounds.** No version reached planning: prior-art review closed the family before the shortlist gate, so there is no plan and no planning record here. What each version ran into -- a published prior, or a search that could not retrieve enough to judge it -- is on the run's prior-art page, with the records named.

[The question in full](artifacts/questions/question_families_detailed.md#family-002-temporal-origin-of-choice-predictive-population-activity) ·
[what prior-art review found](artifacts/questions/prior_art.md) ·
[full planning record](artifacts/families/choice-signal-origin/dossier.md)

### 3. Decision-related population structure after richer movement accounting

*Family 003: Decision-related population structure after richer movement accounting*

Population activity associated with decisions may encode a latent decision construct, richer movement and posture, or inseparable mixtures; coarse motor controls may leave this ambiguity unresolved.

1. [**Decision-residual variant**](artifacts/questions/question_families_detailed.md#variant-003001-decision-residual-variant) — Does population activity retain decision-related structure after accounting for richer concurrent movement and pose variation rather than only coarse behavioral covariates?
2. [**Embodied-target variant**](artifacts/questions/question_families_detailed.md#variant-003002-embodied-target-variant) — Do brain-wide populations represent multidimensional movement and pose in ways that explain decision and response-time variation better than simpler state or locomotor summaries?

**Outcome: Plan developed (provisional).** Both versions got a plan.

[The question in full](artifacts/questions/question_families_detailed.md#family-003-decision-related-population-structure-after-richer-movement-accounting) ·
[full planning record](artifacts/families/movement-decision-structure/dossier.md)

### 4. Functional geometry of shared neural variability

*Family 004: Functional geometry of shared neural variability*

Shared variability can be nuisance, information-limiting structure, or behaviorally meaningful population organization; its consequence depends on orientation relative to candidate signal dimensions rather than magnitude alone.

1. [**Sensory-alignment variant**](artifacts/questions/question_families_detailed.md#variant-004001-sensory-alignment-variant) — Is shared population variability selectively aligned with sensory-evidence dimensions in a way that distinguishes potentially information-limiting structure from correlation magnitude alone?
2. [**Behavioral-alignment variant**](artifacts/questions/question_families_detailed.md#variant-004002-behavioral-alignment-variant) — Is shared population variability more selectively aligned with decision- or movement-related dimensions than with sensory-evidence dimensions, and does that alignment predict choices or response times?

**Outcome: Deferred on prior-art grounds.** One version got a plan; the first never reached planning, because prior-art review stopped it. Its disposition line on the question page says which finding stopped it: a close published prior it would have to be distinguished from, or a search that could not retrieve enough evidence to judge it.

[The question in full](artifacts/questions/question_families_detailed.md#family-004-functional-geometry-of-shared-neural-variability) ·
[what prior-art review found](artifacts/questions/prior_art.md) ·
[full planning record](artifacts/families/variability-geometry/dossier.md)

### 5. Functional forms of mixed selectivity in decision populations

*Family 005: Functional forms of mixed selectivity in decision populations*

Mixed responses may provide useful high-dimensional structure, reflect simpler additive mixing, or arise from correlated sensory and movement variables; identifying mixing alone does not establish function.

1. [**Representational-taxonomy variant**](artifacts/questions/question_families_detailed.md#variant-005001-representational-taxonomy-variant) — Across major brain populations, does joint representation of sensory evidence, choice, and movement exhibit additive, nonlinear, categorical, or category-free mixed selectivity?
2. [**Functional-consequence variant**](artifacts/questions/question_families_detailed.md#variant-005002-functional-consequence-variant) — Do nonlinear or higher-dimensional mixed population representations predict successful decisions and cross-condition readout better than additive or lower-dimensional alternatives?

**Outcome: Deferred on prior-art grounds.** One version got a plan; the first never reached planning, because prior-art review stopped it. Its disposition line on the question page says which finding stopped it: a close published prior it would have to be distinguished from, or a search that could not retrieve enough evidence to judge it.

[The question in full](artifacts/questions/question_families_detailed.md#family-005-functional-forms-of-mixed-selectivity-in-decision-populations) ·
[what prior-art review found](artifacts/questions/prior_art.md) ·
[full planning record](artifacts/families/mixed-selectivity-geometry/dossier.md)

### 6. Population geometry of brain-wide sensorimotor transformation

*Family 006: Population geometry of brain-wide sensorimotor transformation*

Brain-wide evidence and preparation signals may reflect a shared population organization propagated across regions, region-specific transformations, or common task and movement inputs; broad encoding alone does not distinguish these accounts.

1. [**Geometry-invariance variant**](artifacts/questions/question_families_detailed.md#variant-006001-geometry-invariance-variant) — Does the population geometry linking sensory evidence to choice preserve a shared organization across major brain regions, or transform systematically along the sensorimotor pathway?
2. [**Predictive-routing variant**](artifacts/questions/question_families_detailed.md#variant-006002-predictive-routing-variant) — Do time-varying cross-region population relationships predict the transition from sensory evidence to movement preparation better than independent local representations or common task inputs?

**Outcome: Deferred on prior-art grounds.** One version got a plan; the first never reached planning, because prior-art review stopped it. Its disposition line on the question page says which finding stopped it: a close published prior it would have to be distinguished from, or a search that could not retrieve enough evidence to judge it.

[The question in full](artifacts/questions/question_families_detailed.md#family-006-population-geometry-of-brain-wide-sensorimotor-transformation) ·
[what prior-art review found](artifacts/questions/prior_art.md) ·
[full planning record](artifacts/families/sensorimotor-transformation/dossier.md)

<!-- /generated -->

## Follow this run from its inputs

Or continue to the [complete gallery](../ALL_QUESTIONS.md) for every question across all four
demonstrations.

1. [The source papers and how they were screened](../PAPER_SOURCES.md)
2. [The paper bank](artifacts/paperbank/paperbank_summary.md) and the
   [reconstructions](artifacts/paperbank/) built from the accepted papers
3. [The reusable question-forming patterns](artifacts/paperbank/question_patterns_detailed.md)
   induced across those
4. [The dataset narrative](artifacts/dataset/dataset_narrative.md) — the coarse, source-backed
   description the proposal stage was given, deliberately without the schema
5. [Topic evidence](artifacts/literature/topic_evidence_summary.md) and the
   [derived research scope](artifacts/literature/research_scope.md) — for this run, read the scope
   page first: it is the decision every question below is downstream of
6. [All six questions in full](artifacts/questions/question_families_detailed.md), then each
   question's planning record

Source PDFs, raw dataset files, model transcripts, credentials, and private recovery records are
not distributed.

## What produced these artifacts

Run `20260823T115241Z-791b5cad`, executed by the published package itself. This is the first release
in which that sentence is true: the wheel this repository publishes is the wheel that produced these
pages, and the qualification receipt binds the two. Earlier demonstrations disclosed the gap because
the process had no way to close it.

## A note on the paper half

This run did not re-read the twelve papers. It imported the paper bank the anchored IBL run had
already built from the identical cohort, bound by receipt digest, parser configuration, model
identity and prompt version. Re-extracting would have paid for the most expensive stage twice to
produce bytes that cannot differ, and it would have made the comparison worse rather than better:
holding the paper half fixed is part of what makes the two runs comparable at all.
