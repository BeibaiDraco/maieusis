# Climate demo: ERA5-derived stratospheric dynamics

Maieusis was handed twenty climate-dynamics papers and a description of one dataset: an ERA5-derived
record of the polar stratosphere at 60 degrees North. Four quantities — wave activity, the zonal-mean
wind, a reference flow, and eddy forcing — on a 97-level column from 0 to 48 km, six-hourly, from
roughly 1979 to 2021. From those it wrote six scientific questions, then tried to plan each one
against the actual files.

**Nothing in the system was adapted for atmospheric science.** The same code that had read
neuroscience papers read these, reconstructed how each paper moved from an open problem to its
question, and used those moves to write the questions below. If they read like a stratospheric
dynamicist's questions, it is because twenty papers taught the moves — nobody wrote a climate
module. Eighteen of the twenty passed review; the two that did not are listed with the reason, and
neither reason is about the paper's science.

**Read [the dataset notes](DATASET_NOTES.md) before the science.** One fact in them governs this
whole page: the record is a *single column*. One latitude, no longitude, no temperature, no
geopotential height, no surface fields. It resolves height and time superbly and geography not at
all — and the most interesting thing that happened in this run is what the planner did when a
question needed geography.

## Featured: a plan, and the version that never got one

Five of the six questions produced a plan. This family produced one — and it is worth reading first
because of what happened to its *other* version.

The question in one line: **when the polar vortex is disturbed and then recovers, is recovery the
reverse of the disturbance, or does it follow its own path?** Weakening and recovery may be two
expressions of one circulation mode, or recovery may be history-dependent, carrying dynamical memory
of what disturbed it. Those are different claims about the atmosphere and they are hard to tell
apart from covariation.

Maieusis asked it twice, as it asks everything twice — not a draft and a revision, but two ways of
asking one thing, built so they can fail differently and show you which part failed.

1. **Reversibility of onset and recovery.** Do weakening and recovery trace approximately mirrored
   paths through the same vertically resolved state, or are the two limbs systematically different?
2. **Does forcing history organize recovery?** Among states weakened to a similar degree, does the
   preceding wave-forcing history sort what recovery looks like afterwards?

**The first reached a plan and an independent reviewer accepted it. The second never reached the
planner at all.** Prior-art review resolved a scholarly record close enough to it that the question
had to be made distinguishable from that work before any planning could be justified, and the run
stopped it there rather than carrying it forward. It stays on this page with the prior that stopped
it, because a version removed silently is the failure mode this whole system is built against.

That pairing is the most useful thing on this page. One version shows what a plan looks like when
the planner has read the files; the other shows the gate that runs *before* the planner, and what it
costs when it fires.

### What the planner found when it opened the files

Everything in this section is what the planner recorded, and the record labels it that way: each
observation is filed as *unverified planning evidence*, and the dossier carries
`Dataset claim status: unverified` — planning hypotheses about the data, not certified facts. The
file shapes are corroborated by [the dataset notes](DATASET_NOTES.md); the rest is the planner's own
report.

It read the three NetCDF files and their structure. `ana60n.nc` and `tran60n.nc` each carry `fawa`,
`ubar`, `uref` and `epz` as float32 arrays on 97 heights by 124 within-month time slots by 12 months
by 43 years; `sea60n.nc` carries the same four without the year. It read no values.

And it wrote down what it could not establish. The variable meanings, the anomaly formula, the
temporal mapping, the units, the signs and the fill values are **operator-supplied claims rather
than anything encoded in the files** — the planner says so in as many words, and the plan it built
is conditional on them being confirmed before anything is executed. It also recorded the constraint
that governs this entire demonstration: a one-dimensional 60°N product has no horizontal structure,
so it cannot adjudicate regional wave-source or attribution explanations, whatever the question.

Both links under the featured family are worth opening together. The reading guide's *proposal
hypothesis versus inspected evidence* section sets what the proposal stage assumed the dataset
offered beside what the planner actually found in it, and the planning record carries every control,
estimand and stated limit. Neither contains the other.

**That last limitation is not decoration.** One of the six questions asked for exactly the thing the
column does not contain, and the run closed it rather than substituting a proxy:
[the question this dataset could not answer](artifacts/families/precursor-susceptibility/dossier.md)
is the sixth entry below, and it is the shortest way to see the difference between a system that
reads your data and one that is merely fluent about it.

## The six questions, and what happened to each

<!-- generated: six questions -- scripts/render_demo_gallery.py -->

**Two of the six reached plans for both versions**, and every other family is below with what happened to each — a closed version stays on the page with the reason it closed. Five of the six questions produced plans at all.

### 1. Wave forcing versus vortex susceptibility before rapid weakening

*Family 001: Wave forcing versus vortex susceptibility before rapid weakening*

Upward planetary-wave forcing is central to vortex variability, but the literature remains divided over whether unusually strong forcing or a preconditioned, receptive vortex state better distinguishes rapid weakening episodes.

1. [**Event-level precursor discrimination**](artifacts/questions/question_families_detailed.md#variant-001001-event-level-precursor-discrimination) — Do histories of anomalous wave activity and eddy forcing distinguish rapid polar-vortex weakening episodes more consistently than histories of the pre-existing zonal-mean circulation?
2. [**State-conditioned forcing response**](artifacts/questions/question_families_detailed.md#variant-001002-state-conditioned-forcing-response) — Does the subsequent vortex response to comparable wave-forcing episodes differ systematically between initially susceptible and resistant stratospheric circulation states?

**Outcome: Scientific rejection terminal.** No version produced a plan; the run names what was missing rather than substituting a proxy for it.

[The question in full](artifacts/questions/question_families_detailed.md#family-001-wave-forcing-versus-vortex-susceptibility-before-rapid-weakening) ·
[full planning record](artifacts/families/precursor-susceptibility/dossier.md)

### 2. Scientific robustness across vortex-state and event definitions

*Family 002: Scientific robustness across vortex-state and event definitions*

Threshold events, continuous circulation states, and alternative vertical representations may identify different phenomena, so an apparent dynamical conclusion may be robust or may be induced by the chosen definition.

1. [**Construct and lifecycle robustness**](artifacts/questions/question_families_detailed.md#variant-002001-construct-and-lifecycle-robustness) — Which features of rapid weakening and strengthening lifecycles remain stable when the polar vortex is represented by threshold events versus recurrent continuous circulation states?
2. [**Relationship robustness across definitions**](artifacts/questions/question_families_detailed.md#variant-002002-relationship-robustness-across-definitions) — Are inferred associations between wave-forcing histories and subsequent vortex transitions robust across alternative circulation indices, vertical representations, and event thresholds?

**Outcome: Plan developed (provisional).** Both versions got a plan.

[The question in full](artifacts/questions/question_families_detailed.md#family-002-scientific-robustness-across-vortex-state-and-event-definitions) ·
[full planning record](artifacts/families/definition-robustness/dossier.md)

### 3. Lifecycle asymmetry and dynamical memory in vortex disturbances

*Family 003: Lifecycle asymmetry and dynamical memory in vortex disturbances*

Vortex weakening and recovery may be approximately reverse expressions of one circulation mode, or recovery may follow distinct, history-dependent pathways with persistent dynamical memory.

1. [**Reversibility of onset and recovery**](artifacts/questions/question_families_detailed.md#variant-003001-reversibility-of-onset-and-recovery) — Are the vertical circulation and wave–mean-flow pathways into major vortex weakening the time reverse of recovery, or do onset and recovery exhibit reproducible lifecycle asymmetry?
2. [**History-conditioned recovery**](artifacts/questions/question_families_detailed.md#variant-003002-history-conditioned-recovery) — Among episodes reaching comparable vortex weakness, do distinct preceding forcing histories predict different recovery persistence or vertical progression?

**Outcome: Deferred on prior-art grounds.** One version got a plan; the second never reached planning, because prior-art review stopped it. Its disposition line on the question page says which finding stopped it: a close published prior it would have to be distinguished from, or a search that could not retrieve enough evidence to judge it.

[The question in full](artifacts/questions/question_families_detailed.md#family-003-lifecycle-asymmetry-and-dynamical-memory-in-vortex-disturbances) ·
[what prior-art review found](artifacts/questions/prior_art.md) ·
[full planning record](artifacts/families/lifecycle-asymmetry-memory/dossier.md)

### 4. Regime dependence in wave–mean-flow organization

*Family 004: Regime dependence in wave–mean-flow organization*

A common wave–mean-flow relationship may organize polar-vortex variability across regimes, or its strength and meaning may change with circulation state and vertical expression.

1. [**Opposing circulation-regime comparison**](artifacts/questions/question_families_detailed.md#variant-004001-opposing-circulation-regime-comparison) — Is the association between wave activity, eddy forcing, and subsequent circulation change symmetric across weak-vortex and strong-vortex regimes?
2. [**Vertical-expression regime comparison**](artifacts/questions/question_families_detailed.md#variant-004002-vertical-expression-regime-comparison) — Do vertically coherent vortex transitions exhibit a different wave-forcing history and persistence than transitions confined to a narrower part of the stratospheric column?

**Outcome: Deferred on prior-art grounds.** One version got a plan; the second never reached planning, because prior-art review stopped it. Its disposition line on the question page says which finding stopped it: a close published prior it would have to be distinguished from, or a search that could not retrieve enough evidence to judge it.

[The question in full](artifacts/questions/question_families_detailed.md#family-004-regime-dependence-in-wavemean-flow-organization) ·
[what prior-art review found](artifacts/questions/prior_art.md) ·
[full planning record](artifacts/families/wave-mean-flow-regimes/dossier.md)

### 5. Historical stability of ordinary and extreme vortex variability

*Family 005: Historical stability of ordinary and extreme vortex variability*

Multi-decadal stratospheric variability may be historically stable apart from ordinary sampling fluctuations, may shift approximately uniformly, or may change disproportionately in consequential tails.

1. [**Circulation-distribution tail stability**](artifacts/questions/question_families_detailed.md#variant-005001-circulation-distribution-tail-stability) — Across the multi-decadal record, do extreme weak and strong vortex states change in step with the central circulation distribution, or do the tails exhibit disproportionate historical variation?
2. [**Forcing-distribution tail and response correspondence**](artifacts/questions/question_families_detailed.md#variant-005002-forcing-distribution-tail-and-response-correspondence) — Do historically extreme wave-activity or eddy-forcing episodes vary disproportionately relative to ordinary forcing, and is any tail variation mirrored by the distribution of subsequent vortex responses?

**Outcome: Plan developed (provisional).** Both versions got a plan.

[The question in full](artifacts/questions/question_families_detailed.md#family-005-historical-stability-of-ordinary-and-extreme-vortex-variability) ·
[full planning record](artifacts/families/distributional-stability/dossier.md)

### 6. Stratospheric signatures of downward communication and persistence

*Family 006: Stratospheric signatures of downward communication and persistence*

Downward-extending anomalies may represent a distinct, dynamically organized mode of stratospheric evolution, or they may be a descriptive by-product of persistent vortex disturbances and measurement choices.

1. [**Distinct-state test for downward extension**](artifacts/questions/question_families_detailed.md#variant-006001-distinct-state-test-for-downward-extension) — Do downward-extending stratospheric circulation anomalies form a recurrent transition class with distinctive wave-forcing and recovery histories, rather than simply the most persistent examples of vortex disturbance?
2. [**Multicomponent proxy comparison**](artifacts/questions/question_families_detailed.md#variant-006002-multicomponent-proxy-comparison) — Can a multicomponent stratospheric proxy combining disturbance persistence, vertical progression, and post-disturbance wave forcing distinguish sustained downward-extending evolution better than vortex weakness alone?

**Outcome: Mixed family.** One version got a plan; the other was closed during planning, once the planner had inspected the dataset. The closed one stays on the page with its reason.

[The question in full](artifacts/questions/question_families_detailed.md#family-006-stratospheric-signatures-of-downward-communication-and-persistence) ·
[full planning record](artifacts/families/downward-propagation-proxies/dossier.md)

<!-- /generated -->

## Follow this run from its inputs

Or continue to the [complete gallery](../ALL_QUESTIONS.md) for every question across all four
demonstrations.

1. [Source papers and how they were screened](../PAPER_SOURCES.md) — the twenty, and why two did
   not make it
2. [The paper bank](artifacts/paperbank/paperbank_summary.md) and the reviewed
   [reconstructions](artifacts/paperbank/) built from the accepted papers — each one tracing how a
   published paper moved from an open problem to its question

   The two exclusions are listed there with the reviewer's full reasoning, and neither is a
   judgement about the paper's science. One was refused because a citation the run selected as
   important carried no passage tying it to the paper — the review calls that fabricating
   participation in the question-formation process, and refuses the selection rather than keep it.
   The other was refused because its key-citation list came back empty while its own prose named
   eight specific prior works; the reviewer says plainly that this is an incompleteness gap and not
   a fabrication, and that it is straightforwardly fixable. Both are the review stage doing its job
   on the run's own output.
3. [Reusable question-forming patterns](artifacts/paperbank/question_patterns_detailed.md) — those
   moves abstracted across papers, which is what actually wrote the six questions
4. [The dataset narrative](artifacts/dataset/dataset_narrative.md) — the coarse, source-backed
   description the proposal stage was given, deliberately without the schema
5. [Topic evidence](artifacts/literature/topic_evidence_summary.md) and
   [research scope](artifacts/literature/research_scope.md) — the current literature it read, and the
   terms it searched
6. [All six questions in full](artifacts/questions/question_families_detailed.md), then each
   question's planning record

Source PDFs, model transcripts, credentials, and private recovery records are not distributed.
Neither is the dataset: this one-dimensional derived product is a collaborator's, it is not
redistributed, and the transformation that produces `fawa`, `ubar`, `uref`, and `epz` from ERA5 is
not published here — so unlike the two neuroscience demonstrations, you cannot rebuild these exact
three files from this repository. [The dataset notes](DATASET_NOTES.md) say so plainly.

## What produced these artifacts

Run `20260823T080305Z-1ff154d2`, executed by the published package itself. This is the first
release in which that sentence is true: the wheel this repository publishes is the wheel that
produced these pages, and the qualification receipt binds the two. Earlier demonstrations
disclosed the gap because the process had no way to close it.

The evidence supporting these questions is visibly draft and largely abstract-only — for much of the
literature behind them the system read the abstract and not the full text, and the pages say so
where it applies. Prior-art review ran on every version within a recorded scope. No question is
claimed to be novel, no plan is a result, and nothing here was ever run.

---

[All demo questions](../ALL_QUESTIONS.md) · [Source papers](../PAPER_SOURCES.md) ·
[Documentation home](../../docs/INDEX.md)
