# IBL demo: the Brain-Wide Map of mouse decision-making

A mouse sees a visual stimulus on the left or the right of a screen, at varying contrast, and
reports which side by turning a wheel with its forepaws. While it does that, Neuropixels probes
record spiking activity and cameras record its face and body. The International Brain Laboratory
ran that one task, under one shared protocol, in twelve laboratories, and released everything
together: 459 recording sessions, 699 probe insertions, 139 mice, probes placed on a grid across
nearly all major brain areas, and 241 brain regions with enough coverage to analyse. See the
[primary Nature paper](https://doi.org/10.1038/s41586-025-09235-0) and the
[official release guide](https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html).

Two properties of that design carry most of the questions below.

**The task repeats.** Same protocol, same wheel, twelve different laboratories. That makes a
question askable here that no single-laboratory dataset can even pose: which part of a neural
result belongs to the phenomenon, and which part belongs to the laboratory or the individual
animal.

**The camera runs the whole time.** Video-derived body and face measurements sit beside the spikes
on the same trials. So "is this signal about the decision, or is the animal just moving?" stops
being a rhetorical objection and becomes something a plan can actually test.

Maieusis was handed twelve neuroscience papers and a coarse, source-backed description of this
dataset — not its schema — and developed six questions against it. All twelve papers were accepted;
ten of them produced reviewed reconstructions of how their authors moved from an open problem to a
question, and eight reusable question-forming patterns were induced across those.

**Three demonstrations share this twelve-paper cohort, and none of them is another one repeated.**
NLB is a different dataset entirely — one monkey, one session, two motor areas recorded at the same
instant, against IBL's many brains, one task, twelve laboratories and most of the brain sampled
shallowly. The [open-mode IBL run](../ibl-open/README.md) is this same dataset with the topic anchor
removed. Different data allow different questions; the same data asked differently produce different
questions too, and this release publishes both comparisons.

One caveat about what is published here. Two of the demonstrations ship a separate **dataset
note** — a precise statement of the data's real shape — which you can set beside the coarse
narrative the proposing model was given, to measure the gap between them. This one does not. For
IBL, the [dataset narrative](artifacts/dataset/dataset_narrative.md) is the only dataset
description on these pages, so read it knowing it is the deliberately incomplete one.

## Featured: what a declared topic buys, and what it costs

**This run was told what to think about.** Its research intent declares one topic anchor —
*noise correlations* — and every question below is downstream of that phrase. The
[open-mode run next door](../ibl-open/README.md) is the same recordings, the same twelve papers and
the same models with no anchor at all, and the two produced twelve questions with no family in
common. Read them side by side; it is the most direct evidence in this release for what a research
intent actually does.

The featured family is where the anchor pays. Behaviour that looks like evidence accumulation can
come from persistent integration along one stable population direction, or from a moving sequence of
population states. Those are different claims about how a decision is formed, and they are hard to
separate from averaged activity. Shared trial-to-trial variability constrains them differently — so
a question pointed at noise correlations can get at a question about *time*.

Maieusis asked it two ways, as it asks everything twice:

1. **Fixed axis, or a rotating one?** Within a region, does the geometry of shared variability sit
   on one stable accumulation direction across the trial, or does it rotate — indicating time-local
   states rather than a single integrator?
2. **Does choice information arrive in sequence?** Within a region, is choice-related information
   carried sequentially across population states rather than accumulating along one axis?

**The first reached a plan and an independent reviewer accepted it. The second did not.** The family
is labelled **Mixed family** for exactly that reason, and the closed version stays on the page with
its reasoning. Authority does not spill: the family's own guide says in as many words that it
applies only to the variant marked reviewed and accepted.

### What the planner found when it opened the files

Filed as *unverified planning evidence*, which is the run's own label for it: planning hypotheses
about the data, not certified facts.

It read the build. 459 sessions, 699 insertions, 75,395 units, 295,920 trials. It read the trial
table's actual columns — `choice`, `contrastLeft`, `contrastRight`, `stimOn_times`, `goCue_times`,
`firstMovement_times`, `response_times`, `feedback_times`, `probabilityLeft`, `bwm_include` — and
the derived behaviour features beside them, including reaction and movement times, and checked what
video-derived measurements were available per session. Region annotations sit on units; spike times
and cluster assignments are sharded per insertion.

That inventory is what makes the featured question askable rather than merely sayable: a geometry
question about *time within a trial* needs the event times to exist, per trial, aligned to the
spikes. The planner established that they do before it wrote anything about what to do with them.

Open the family's two records together. The reading guide's *proposal hypothesis versus inspected
evidence* section sets what the proposal stage assumed the recordings offered beside what the
planner actually found in them; the planning record carries the controls, the estimand and the
stated limits. Neither contains the other, which is why both are linked.

## Three families here are closed by the machinery, not by the science

**Three of the six produced no plan, and none of the three reasons is a finding about the brain.**
Read the labels rather than the absence.

Two carry **Validation warning**. The planner did its work and the material it returned could not be
fully validated on the way back in, so no plan is claimed. The cause is written down rather than
smoothed over: the planner revised its own evidence files under new names and left the earlier
drafts beside them, and both copies were read back as if both had been returned. That is a defect in
how this system reads a planner's output — it is scheduled for repair, and it says nothing about
[embodied and internal-state explanations of apparent noise
correlations](artifacts/families/behavioral-alternatives/dossier.md) or [the regional organization of
behaviourally relevant covariance geometry](artifacts/families/regional-organization/dossier.md),
which are the two questions it cost.

One carries **Service warning**: a provider stayed unavailable after bounded retries, so the run
kept the material it had, published it with a warning, and claimed no plan. That is a statement
about our infrastructure on the night this ran.
[Read the family and its warning](artifacts/families/noise-origin/dossier.md).

**None of these is a refusal.** A refusal — the run inspecting the data and concluding the question
cannot honestly be asked of it — is a scientific answer, and the
[climate](../climate/README.md) and [NLB](../nlb/README.md) demonstrations each carry one.

## The six questions, and what happened to each

<!-- generated: six questions -- scripts/render_demo_gallery.py -->

**One of the six reached plans for both versions**, and every other family is below with what happened to each — a closed version stays on the page with the reason it closed. Three of the six questions produced plans at all.

### 1. Functional alignment of shared variability during perceptual decisions

*Family 001: Functional alignment of shared variability during perceptual decisions*

Noise correlations may be largely nonspecific fluctuations, or their geometry may selectively align with population dimensions carrying sensory evidence or impending choice. These alternatives can produce similar average correlation magnitudes but different functional interpretations.

1. [**Sensory-code alignment branch**](artifacts/questions/question_families_detailed.md#variant-001001-sensory-code-alignment-branch) — Is shared trial-to-trial variability selectively aligned with sensory-evidence representations, and does that alignment predict reduced or preserved stimulus discriminability beyond overall noise-correlation magnitude?
2. [**Choice and behavior alignment branch**](artifacts/questions/question_families_detailed.md#variant-001002-choice-and-behavior-alignment-branch) — Is shared trial-to-trial variability selectively aligned with choice-related population structure, and does that alignment predict choices or response-time variation after distinguishing sensory and embodied alternatives?

**Outcome: Mixed family.** One version got a plan; the other was closed during planning, once the planner had inspected the dataset. The closed one stays on the page with its reason.

[The question in full](artifacts/questions/question_families_detailed.md#family-001-functional-alignment-of-shared-variability-during-perceptual-decisions) ·
[full planning record](artifacts/families/noise-alignment/dossier.md)

### 2. Input-linked versus internally generated origins of correlated variability

*Family 002: Input-linked versus internally generated origins of correlated variability*

Limited sensory input, circuit organization, and internal fluctuations can all generate information-limiting correlations, but they predict different changes in covariance around sensory input and decision formation.

1. [**Sensory-input origin branch**](artifacts/questions/question_families_detailed.md#variant-002001-sensory-input-origin-branch) — Does correlated variability track the strength and timing of sensory drive in a manner consistent with an input-linked origin?
2. [**Persistent internal-state origin branch**](artifacts/questions/question_families_detailed.md#variant-002002-persistent-internal-state-origin-branch) — Does correlated variability persist beyond immediate sensory drive and predict subsequent decision timing in a manner consistent with internally generated state or decision dynamics?

**Outcome: Service warning.** No plan survives here, and the reason is the machinery rather than the science: the run closed this family with a warning.

[The question in full](artifacts/questions/question_families_detailed.md#family-002-input-linked-versus-internally-generated-origins-of-correlated-variability) ·
[full planning record](artifacts/families/noise-origin/dossier.md)

### 3. Embodied and internal-state explanations of apparent noise correlations

*Family 003: Embodied and internal-state explanations of apparent noise correlations*

Residual correlations associated with choice and response time may reflect decision computation, but conventional controls may omit multidimensional behavior or internal state. Richer alternatives can either explain away a decision interpretation or reveal scientifically meaningful embodied structure.

1. [**Rich embodied-behavior branch**](artifacts/questions/question_families_detailed.md#variant-003001-rich-embodied-behavior-branch) — How much apparently choice- or response-time-related shared neural variability is predictively accounted for by multidimensional pose and movement structure beyond simpler behavioral summaries?
2. [**Residual internal-state branch**](artifacts/questions/question_families_detailed.md#variant-003002-residual-internal-state-branch) — After accounting for measured movement, does a residual shared-variability component predict response-time and choice-history effects consistent with a non-motor internal state?

**Outcome: Validation warning.** No accepted plan is published for this family: the run closed it as “Validation warning”. The reasoning that got this far stays on the page.

[The question in full](artifacts/questions/question_families_detailed.md#family-003-embodied-and-internal-state-explanations-of-apparent-noise-correlations) ·
[full planning record](artifacts/families/behavioral-alternatives/dossier.md)

### 4. Regional organization of behaviorally relevant covariance geometry

*Family 004: Regional organization of behaviorally relevant covariance geometry*

Decision and movement signals can be distributed across the brain, but distribution does not establish a common population mechanism. Similar behavior may be associated with a recurrent geometry across regions or with distinct local geometries.

1. [**Shared brain-wide motif branch**](artifacts/questions/question_families_detailed.md#variant-004001-shared-brain-wide-motif-branch) — Does a common covariance geometry aligned with sensory-to-choice progression recur across anatomically separated populations during decision formation?
2. [**Region-specific solutions branch**](artifacts/questions/question_families_detailed.md#variant-004002-region-specific-solutions-branch) — Do anatomically distinct populations exhibit different covariance geometries whose associations with sensory evidence, choice, movement, or response time imply region-specific computational solutions?

**Outcome: Validation warning.** No accepted plan is published for this family: the run closed it as “Validation warning”. The reasoning that got this far stays on the page.

[The question in full](artifacts/questions/question_families_detailed.md#family-004-regional-organization-of-behaviorally-relevant-covariance-geometry) ·
[full planning record](artifacts/families/regional-organization/dossier.md)

### 5. Covariance geometry and alternative population accounts of evidence accumulation

*Family 005: Covariance geometry and alternative population accounts of evidence accumulation*

Behavior consistent with evidence accumulation can arise from persistent integration along a stable population direction or from sequential, time-varying population states. Shared variability may constrain these organizations differently.

1. [**Stable accumulation-axis branch**](artifacts/questions/question_families_detailed.md#variant-005001-stable-accumulation-axis-branch) — Is behaviorally relevant shared variability aligned with a temporally stable evidence-accumulation direction whose state predicts choice and response time?
2. [**Sequential population-state branch**](artifacts/questions/question_families_detailed.md#variant-005002-sequential-population-state-branch) — Is evidence accumulation associated with a sequence of changing population states whose covariance structure preserves choice-relevant information across time?

**Outcome: Mixed family.** One version got a plan; the other was closed during planning, once the planner had inspected the dataset. The closed one stays on the page with its reason.

[The question in full](artifacts/questions/question_families_detailed.md#family-005-covariance-geometry-and-alternative-population-accounts-of-evidence-accumulation) ·
[full planning record](artifacts/families/accumulation-geometry/dossier.md)

### 6. Reproducibility of noise-correlation statistics and geometry across laboratories

*Family 006: Reproducibility of noise-correlation statistics and geometry across laboratories*

Standardized multisite processes may yield reproducible neural summaries, but existing process-level evidence does not establish whether noise correlations reproduce quantitatively. Coarse magnitude and functional geometry may have different reproducibility profiles.

1. [**Coarse-statistic reproducibility branch**](artifacts/questions/question_families_detailed.md#variant-006001-coarse-statistic-reproducibility-branch) — Are coarse summaries of noise-correlation magnitude reproducible across laboratories after accounting for subject, session, region, and behavioral-context heterogeneity?
2. [**Functional-geometry reproducibility branch**](artifacts/questions/question_families_detailed.md#variant-006002-functional-geometry-reproducibility-branch) — Is task-aligned covariance geometry more reproducible across laboratories than coarse noise-correlation magnitude, and does any reproducible geometry retain similar behavioral associations?

**Outcome: Plan developed (provisional).** Both versions got a plan.

[The question in full](artifacts/questions/question_families_detailed.md#family-006-reproducibility-of-noise-correlation-statistics-and-geometry-across-laboratories) ·
[full planning record](artifacts/families/reproducibility/dossier.md)

<!-- /generated -->

## Follow this run from its inputs

Or continue to the [complete gallery](../ALL_QUESTIONS.md) for every question across all four
demonstrations.

1. [The source papers and how they were screened](../PAPER_SOURCES.md)
2. [The paper bank](artifacts/paperbank/paperbank_summary.md) and the ten
   [reconstructions](artifacts/paperbank/) built from the accepted papers — evidence-bound accounts
   of how each one moved from an open problem to its question
3. [The reusable question-forming patterns](artifacts/paperbank/question_patterns_detailed.md)
   induced across those
4. [The dataset narrative](artifacts/dataset/dataset_narrative.md) — the coarse, source-backed
   description the proposal stage was given, deliberately without the schema
5. [Topic evidence](artifacts/literature/topic_evidence_summary.md) and
   [research scope](artifacts/literature/research_scope.md)
6. [All six questions in full](artifacts/questions/question_families_detailed.md), then each
   question's planning record

Source PDFs, raw dataset files, model transcripts, credentials, and private recovery records are
not distributed.

## What produced these artifacts

Run `20260823T100038Z-46ce083d`, executed by the published package itself. This is the first release in which that
sentence is true: the wheel this repository publishes is the wheel that produced these pages, and
the qualification receipt binds the two. Earlier demonstrations disclosed the gap because the
process had no way to close it.

This run needed no resume and carries one build identity: the reader pages were produced inside the
run itself, by the same wheel that did the science, and [its manifest](demo_manifest.yaml) records
one `science_build_sha256` with no separate presentation build. Earlier demonstrations could not say
that; this release is the first where the pages and the science share a single lineage.

The evidence supporting these questions is visibly draft and largely abstract-only, and the pages
say so where it applies. Prior-art review ran on every version within a recorded scope. No question
is claimed to be novel, no plan is a result, and nothing here was ever run.

---

[All demo questions](../ALL_QUESTIONS.md) · [Source papers](../PAPER_SOURCES.md) ·
[Documentation home](../../docs/INDEX.md)
