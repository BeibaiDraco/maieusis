# Temporal organization of motor population geometry — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Asks whether population geometry during delayed reaching reflects a continuous evolution of one movement representation or a qualitative reorganization between preparation and execution.

The scientific tension is:

Similar reach behavior could arise from a continuously evolving population trajectory or from distinct preparatory and execution-related organizations; descriptive geometry alone cannot distinguish these accounts.

## Variant 1: Cross-phase relational-invariance account

### Why it matters

Testing cross-phase prediction of task-condition relationships can determine whether preparation and execution retain a common task organization even when their neural states or manifolds differ. This would connect changing population activity to a stable representational principle without equating smooth state evolution or manifold overlap with shared task geometry.

### Original and refined question

**Original Question Scientist proposal**

Does delayed-reach population activity preserve a common task-relevant geometry while continuously transforming from preparation into execution?

**Post-novelty revised proposal**

Are task-condition relationships in delayed-reach population activity preserved across preparation and execution under a shared geometry that predicts held-out cross-phase relationships better than phase-specific geometries, after accounting for measured kinematic and movement-timing covariates?

**Reviewed refined question**

In delayed reaching, does a single shared task-condition geometry predict held-out cross-phase task-condition relationships (preparation-to-execution and the reverse) better than phase-specific geometry models, after measured kinematic and movement-timing covariates are modeled and peri-movement/execution-feature signals are separated?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the delayed-reaching release contains distinguishable preparation and execution periods, repeated task conditions, and alignable neural and behavioral measurements, it may permit a later planner to compare shared and phase-specific geometry models through held-out cross-phase prediction while representing measured kinematic and movement-timing covariates.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 (MC_Maze_Small, version 0.220113.0408) contains sorted-unit spiking times and behavioral data from one rhesus macaque (Jenkins), single session (2009-09-28), performing a delayed center-out reaching task with obstructing barriers forming a maze, yielding straight and curved reaches. Neural activity was recorded from M1 (primary motor cortex) and PMd (dorsal premotor cortex) arrays. Cursor position, hand position, eye position, and offline-computed hand velocity were recorded. The public release is limited to 100 train trials and 100 test trials and is provided as part of the Neural Latents Benchmark '21. This delayed-reach paradigm (delay/preparation followed by go-cue and movement/execution) is the substrate for the family's phenomenon of temporal organization of motor population geometry across preparation and execution.
  - Limitation: Single subject, single session; the small release is 100 train + 100 test trials, limiting sampling power for population-geometry claims.
  - Limitation: Documentation-level fact; specific trial-event timing, condition counts, and channel availability are established separately by schema and metadata inspection.
- **Unverified planning evidence:** In the train file, cursor_pos, hand_pos, hand_vel, and eye_pos are each 2-D (x,y) TimeSeries with 287710 samples spanning the session, sampled at ~1 kHz (median inter-sample interval ~1.0 ms), units meters (positions/eye) and m/s (hand_vel). This provides continuous, high-temporal-resolution measured kinematics: instantaneous hand position and velocity track the ongoing reach, and eye/cursor position are additional behavioral covariates. Combined with per-trial move_onset_time, rt, and delay, these supply the measured kinematic and movement-timing covariates both variants require. The NLB test file (desc-test_ecephys.nwb) contains 107 units and 100 test trials but has NO behavior processing module and only start_time, stop_time, move_onset_time, split columns; its behavioral labels are withheld for the benchmark. Consequently the usable behavior-linked analysis surface is the 100-trial train file with its internal 75/25 train/val split for held-out evaluation.
  - Limitation: Behavioral covariates cover measured hand/cursor/eye kinematics only; unmeasured behavioral confounds (e.g. muscle activity, force) are not observed, so covariate control is necessarily incomplete.
  - Limitation: The NLB test file lacks behavior and withheld labels, so it cannot serve behavioral cross-phase or boundary analyses; all such analyses are confined to the 100 train trials with internal cross-validation.
- **Unverified planning evidence:** Per-trial event landmarks yield well-formed preparation and execution windows. The delay (go_cue_time - target_on_time) has median ~615 ms (range ~14-999 ms), giving a variable-length preparatory/delay phase after target onset and before the go cue. Reaction time rt (move_onset_time - go_cue_time) has median ~321 ms (range ~241-758 ms). The execution window (stop_time - move_onset_time) has median ~1.14 s (min ~0.98 s), and total trial duration median ~2.88 s. The delay column equals (go_cue_time - target_on_time) in milliseconds. Because target_on_time, go_cue_time, and move_onset_time are all populated with no missing values, trials can be aligned to a delay/preparation epoch and a movement/execution epoch, and movement onset, reaction time, and delay are available as movement-timing covariates. The variable delay supports separating condition-invariant timing signals from task-condition structure across phases.
  - Limitation: Some trials have very short delays (min ~14 ms); a minimum-delay inclusion threshold is required so the preparation epoch is well-defined, reducing usable trials for cross-phase preparation analyses.
  - Limitation: Timing statistics are aggregate; they establish phase separability for planning, not the precision of any specific decoding or boundary estimate.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: One rhesus macaque (Jenkins), single session, 100 successful delayed-reach trials from the MC_Maze_Small train file; combined M1+PMd sorted-unit population (142 units). Task conditions are the 9 (trial_type, maze_id) combinations spanning straight and maze/curved reaches, each with ~8-12 repeats. Scope is a within-session, single-subject descriptive/predictive analysis; no cross-session or cross-subject generalization is claimed.
- Unit of observation: Trial-by-time-bin population activity vectors (binned spike counts across 142 units), grouped into a preparation epoch and an execution epoch per trial.
- Unit of inference: Trial (nested within the 9 conditions); relational-prediction performance is aggregated across conditions with trial-level resampling for uncertainty.
- Hierarchy and dependence: Trials are nested within conditions and within one session. Cross-validation and bootstrap resample at the trial level within conditions to respect repeated-trial dependence; condition means are treated as the relational objects, and uncertainty is propagated from trial-level variability. Temporal autocorrelation within an epoch is handled by using epoch-summarized states and by autocorrelation-preserving (block/circular-shift) null models.
- Validation: Trial-held-out nested cross-validation within conditions plus the internal 75/25 train/val split; method-recovery on synthetic data with known shared vs phase-specific geometry to confirm the estimator distinguishes the two before touching held-out real trials. No held-out NLB test outcomes are inspected.
- Split strategy: Leakage-safe trial-level splits within conditions; use the file's internal train/val partition for the outer evaluation and k-fold trial resampling for inner tuning.
- Claim ceiling: predictive

**Analysis strategy**

1. Define preparation-epoch and execution-epoch population states per trial (e.g. go-cue-aligned pre-movement window and move-onset-aligned movement window), after excluding trials with insufficient delay.
2. Construct task-condition relational structure (pairwise distances / representational geometry among the 9 condition means) within each phase from population activity.
3. Fit a shared-geometry model (single latent condition geometry constrained to be common across phases) and phase-specific geometry models (independent per-phase geometries); evaluate each by predicting held-out task-condition relationships in the opposite phase using trial-held-out cross-validation and the internal 75/25 split.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Shuffled condition labels should abolish any cross-phase relational advantage.; Autocorrelation-preserving circular-shift null for within-epoch temporal structure.
- Positive controls: Within-phase condition decoding should recover known task structure (straight vs maze, target identity), confirming the population carries condition information.
- Alternative explanations: Apparent cross-phase preservation driven by measured hand/cursor kinematics, movement timing, or peri-movement activity rather than task-condition organization.; Partial manifold overlap or temporal autocorrelation/dimensional reduction making phase-local structure appear relationally invariant.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject, single session, 9 conditions, 100 trials: results are within-session predictive comparisons, not causal or mechanistic, and do not generalize across animals.
- A shared-geometry advantage would support relational preservation but would not by itself establish temporal continuity of neural trajectories; covariate control is incomplete because not all behavioral confounds are measured.
- Planning evidence is not a scientific result; no outcomes have been computed.

**Why the plan serves the question**

The plan evaluates exactly the relational-invariance contrast the invariant protects (shared vs phase-specific task-condition geometry by held-out cross-phase relational prediction), keeps kinematic/timing covariates and peri-movement separation as first-class controls, and preserves the meaning of positive and negative outcomes without collapsing into trajectory continuity or execution-feature decoding.

**Before any later execution**

- Unresolved planning decisions: Bin width/smoothing, epoch window definitions, and minimum-delay threshold are prespecified decision rules to fix before execution.

### Scientific stakes

**Discriminating observation**

A shared-geometry model predicts held-out task-condition relationships from preparation to execution, and conversely where support permits, better than phase-specific geometry models, with that advantage remaining after measured kinematic and movement-timing covariates are modeled and after peri-movement activity or execution-feature decoding is separated from the target comparison. Distinct or partially overlapping phase manifolds count as evidence for common task geometry only if this cross-phase relational prediction criterion is met.

**What possible outcomes would mean**

- Positive pattern: A covariate-robust cross-phase predictive advantage for the shared-geometry model would support preservation of task-relevant relational organization between preparation and execution. This interpretation could coexist with distinct or only partially overlapping phase manifolds and would not, by itself, establish temporal continuity of neural trajectories.
- Negative pattern: If phase-specific geometry models reliably predict held-out task-condition relationships better than the shared model after the same covariate treatment, the result would favor phase-dependent reorganization of task relations. Partial manifold overlap or smooth state shifts would not overturn that interpretation, although the result would not alone establish a discrete dynamical transition.
- Null or ambiguous pattern: If shared and phase-specific models cannot be distinguished, or if any cross-phase advantage disappears after accounting for measured movement and timing covariates, relational invariance would remain unresolved. Claims would be limited to phase-local geometry, decoding, trajectory continuity, or manifold overlap as separately supported descriptions.

## Variant 2: Behavioral-relation boundary account

### Why it matters

A behavioral-relation switch would distinguish a functional regime boundary from previously reported preparation–execution subspace reorganization, continuous state shifts, and rapid timing-related components. This would constrain the temporal organization of motor population activity more strongly than geometry alone.

### Original and refined question

**Original Question Scientist proposal**

Is delayed reaching organized by a qualitative population-dynamics transition from movement preparation to execution rather than by one continuous regime?

**Post-novelty revised proposal**

Does delayed-reach population activity cross a localized functional boundary from prospectively predicting the forthcoming reach to tracking the ongoing reach, beyond any continuous evolution, subspace separation, or movement-timing signal?

**Reviewed refined question**

Does delayed-reach population activity cross a localized functional boundary from prospectively predicting the forthcoming reach to tracking the ongoing reach, providing a better account than a continuous single-regime evolution, where the switch is measured as a crossover in the conditional (incremental) predictive information population activity carries about the forthcoming reach versus the ongoing reach, over and above movement onset, reaction time, and condition-invariant timing?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the delayed-reaching release contains sufficiently time-resolved population activity, task events, repeated reach conditions, and alignable behavioral measurements, it may support a later comparison of localized-boundary and continuous accounts while assessing whether any apparent boundary persists beyond available timing and kinematic covariates.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 (MC_Maze_Small, version 0.220113.0408) contains sorted-unit spiking times and behavioral data from one rhesus macaque (Jenkins), single session (2009-09-28), performing a delayed center-out reaching task with obstructing barriers forming a maze, yielding straight and curved reaches. Neural activity was recorded from M1 (primary motor cortex) and PMd (dorsal premotor cortex) arrays. Cursor position, hand position, eye position, and offline-computed hand velocity were recorded. The public release is limited to 100 train trials and 100 test trials and is provided as part of the Neural Latents Benchmark '21. This delayed-reach paradigm (delay/preparation followed by go-cue and movement/execution) is the substrate for the family's phenomenon of temporal organization of motor population geometry across preparation and execution.
  - Limitation: Single subject, single session; the small release is 100 train + 100 test trials, limiting sampling power for population-geometry claims.
  - Limitation: Documentation-level fact; specific trial-event timing, condition counts, and channel availability are established separately by schema and metadata inspection.
- **Unverified planning evidence:** In the train file, cursor_pos, hand_pos, hand_vel, and eye_pos are each 2-D (x,y) TimeSeries with 287710 samples spanning the session, sampled at ~1 kHz (median inter-sample interval ~1.0 ms), units meters (positions/eye) and m/s (hand_vel). This provides continuous, high-temporal-resolution measured kinematics: instantaneous hand position and velocity track the ongoing reach, and eye/cursor position are additional behavioral covariates. Combined with per-trial move_onset_time, rt, and delay, these supply the measured kinematic and movement-timing covariates both variants require. The NLB test file (desc-test_ecephys.nwb) contains 107 units and 100 test trials but has NO behavior processing module and only start_time, stop_time, move_onset_time, split columns; its behavioral labels are withheld for the benchmark. Consequently the usable behavior-linked analysis surface is the 100-trial train file with its internal 75/25 train/val split for held-out evaluation.
  - Limitation: Behavioral covariates cover measured hand/cursor/eye kinematics only; unmeasured behavioral confounds (e.g. muscle activity, force) are not observed, so covariate control is necessarily incomplete.
  - Limitation: The NLB test file lacks behavior and withheld labels, so it cannot serve behavioral cross-phase or boundary analyses; all such analyses are confined to the 100 train trials with internal cross-validation.
- **Unverified planning evidence:** Per-trial event landmarks yield well-formed preparation and execution windows. The delay (go_cue_time - target_on_time) has median ~615 ms (range ~14-999 ms), giving a variable-length preparatory/delay phase after target onset and before the go cue. Reaction time rt (move_onset_time - go_cue_time) has median ~321 ms (range ~241-758 ms). The execution window (stop_time - move_onset_time) has median ~1.14 s (min ~0.98 s), and total trial duration median ~2.88 s. The delay column equals (go_cue_time - target_on_time) in milliseconds. Because target_on_time, go_cue_time, and move_onset_time are all populated with no missing values, trials can be aligned to a delay/preparation epoch and a movement/execution epoch, and movement onset, reaction time, and delay are available as movement-timing covariates. The variable delay supports separating condition-invariant timing signals from task-condition structure across phases.
  - Limitation: Some trials have very short delays (min ~14 ms); a minimum-delay inclusion threshold is required so the preparation epoch is well-defined, reducing usable trials for cross-phase preparation analyses.
  - Limitation: Timing statistics are aggregate; they establish phase separability for planning, not the precision of any specific decoding or boundary estimate.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: One rhesus macaque (Jenkins), single session, 100 successful delayed-reach trials from the MC_Maze_Small train file; combined M1+PMd population (142 units). Time-resolved population activity is aligned to target onset, go cue, and movement onset. Scope is a within-session, single-subject predictive time-course analysis.
- Unit of observation: Trial-by-time population activity vectors (fine time bins) aligned to task events, paired with instantaneous behavioral covariates and forthcoming-reach labels.
- Unit of inference: Trial (with time as a within-trial dimension); boundary localization is inferred across trials with trial-level resampling and the internal held-out split.
- Hierarchy and dependence: Time bins are nested within trials, nested within conditions and one session. Within-trial temporal autocorrelation is modeled explicitly and used to build continuous single-regime and staggered-evolution nulls; cross-validation and bootstrap resample at the trial level to avoid using the same observations for boundary discovery and validation. The condition-invariant timing baseline is estimated at the trial-time level and shared across conditions so that condition-specific kinematic tracking is separable from a global timing ramp.
- Validation: Disjoint discovery/validation trial folds, the internal 75/25 split, and synthetic method-recovery for switch vs continuous vs timing-dominated generators to confirm the conditional estimand neither erases the tracking target nor manufactures a switch. No held-out NLB test outcomes or target-derived tuning are inspected; the boundary criterion and the conditional-estimator form are prespecified.
- Split strategy: Trial-level leakage-safe splits; boundary discovered on one fold and its localization/covariate-resistance validated on held-out trials.
- Claim ceiling: predictive

**Analysis strategy**

1. Build time-resolved population activity aligned to target onset, go cue, and movement onset (fine bins), retaining per-bin condition labels, instantaneous hand kinematics, and forthcoming-reach labels; population activity is always the predictor and is never residualized against the behavioral targets.
2. Define two behavioral readout targets decoded FROM population activity: (i) a prospective forthcoming-reach target (upcoming reach identity/direction and future hand kinematics at a positive lead), and (ii) a contemporaneous ongoing-reach target (instantaneous hand position/velocity at lag near zero). Both remain decoding targets; neither is regressed out of neural activity.
3. Estimate the construct as a conditional predictive comparison at each time bin: for each target, fit a nested baseline that predicts the behavioral target from condition-invariant timing (time-from-onset ramp), movement onset, and reaction time, then add population activity and take the incremental (partial R-squared / conditional mutual information) predictive gain. The timing/onset covariates are conditioned on in the target-readout model; they are NOT regressed out of the population activity, and the ongoing-kinematic tracking target is never residualized away.
4. 3 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: The condition-invariant timing regressor and movement-onset-aligned control, entered as the nested baseline, should not by themselves produce a movement-specific prospective-to-contemporaneous switch in the incremental (conditional) predictive advantage.; Trial-shuffled forthcoming-reach labels should abolish the prospective conditional predictive information.; plus 1 additional item(s) in the complete dossier
- Positive controls: Instantaneous hand-velocity decoding, conditioned on the timing baseline, should rise during movement (recovering the contemporaneous signal), confirming the ongoing-reach readout is present and separable from the timing ramp.
- Alternative explanations: Geometrically separable preparation/execution patterns whose behavioral relations nonetheless evolve smoothly within one continuous regime.; A rapid condition-invariant movement-onset/reaction-time signal creating an apparent boundary without changed movement-specific meaning (addressed by conditioning the readout on that signal rather than removing it from neural activity).; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject, single session, 100 trials, 9 conditions: modest power to localize a boundary and to separate it from steep-but-continuous or regionally staggered evolution; this is a within-session predictive comparison, not a causal or mechanistic claim.
- Conditional/partial predictive attribution is model-dependent; it controls measured timing and kinematic confounds by conditioning the behavioral readout on them without residualizing the tracking target, but covariate control remains incomplete because not all behavioral confounds are measured. A detected boundary is evidence about population predictive meaning, not about underlying circuit mechanism.
- Planning evidence is not a scientific result; no outcomes have been computed.

**Why the plan serves the question**

The plan tests exactly the qualitative-boundary criterion the invariant protects - a localized prospective-to-contemporaneous switch that survives movement onset, reaction time, kinematics, and condition-invariant timing - while retaining ongoing kinematic tracking as the construct of interest. The revised covariate strategy conditions the behavioral readout on timing/onset (a conditional predictive comparison) instead of regressing the kinematic tracking target out of population activity, which would have removed the very post-boundary relation being tested. It pits the localized-boundary account against continuous single-regime and staggered alternatives and preserves the meaning of positive and negative outcomes rather than reducing the question to subspace separation or trajectory geometry.

**Before any later execution**

- Unresolved planning decisions: Bin width, alignment events, lead/lag offset, the conditional-estimator form (partial R-squared vs conditional mutual information), the nested-baseline covariate-model form, the boundary/change-point model family, and the localized-vs-staggered comparison thresholds are prespecified decision rules to fix before execution.
- Required future skills: A time-resolved conditional prospective-vs-contemporaneous boundary-comparison executor skill (nested/partial-information decoders that keep ongoing kinematics as a decoding target while conditioning on timing/onset, plus localized-switch vs continuous/staggered model comparison) may need implementation; the scientific plan is sound independent of that implementation.

### Scientific stakes

**Discriminating observation**

The qualitative account would be favored only if a reproducible, temporally localized crossover from information predictive of the forthcoming reach to information tracking the ongoing reach provides a better account than a continuous single-regime evolution, while the boundary remains after accounting for movement onset, reaction time, measured kinematics, and condition-invariant timing-related activity. The continuous account would be favored—even with separable preparation and movement patterns—if prospective and contemporaneous behavioral relations change smoothly or at staggered times, with no residual localized switch beyond those covariates.

**What possible outcomes would mean**

- Positive pattern: A localized, covariate-resistant switch in behavioral predictive meaning would support a qualitative functional boundary beyond prior evidence for orthogonal subspaces, altered correlations, or continuous state shifts.
- Negative pattern: Smooth or regionally staggered evolution of behavioral relations, without a residual localized switch after timing and kinematic accounting, would favor the continuous single-regime account even if preparation and execution occupy separable population organizations.
- Null or ambiguous pattern: If temporal coverage, behavioral measurements, or uncertainty cannot discriminate a localized crossover from a smooth or timing-driven change, the result would leave the regime-boundary question unresolved and support only phase-specific descriptive claims.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The revised v2 conditional-predictive design retains ongoing kinematics as a decoding target while controlling timing and onset covariates in the readout model, resolving the prior scientific blocker. Both variants directly test their protected, distinct contrasts with held-out evaluation, relevant controls, and appropriately limited within-session predictive claims. Remaining specification choices are pre-execution locks rather than planning deficiencies.

Retained changes and locks:

- **Pre execution lock:** Before execution, lock epoch/binning and model-selection specifications for both variants, including preparation-delay inclusion, covariate-model form, and the v2 localized-versus-continuous/staggered comparison rule.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The round-1 revision directly and adequately resolves the round-0 scientific blocker on v2: population activity remains the sole predictor throughout, and both the prospective (forthcoming-reach) and contemporaneous (ongoing-kinematic) targets remain genuine decoding targets rather than being residualized out. Timing, movement onset, and reaction time are folded into a nested baseline that the behavioral readout is conditioned on, so the estimand is an incremental/partial predictive-information gain rather than a covariate-scrubbed neural signal. This preserves exactly the behavioral relation the localized-boundary claim depends on while still controlling condition-invariant timing confounds, and it is paired with synthetic method-recovery checks, condition-specific kinematic contrasts, and lead/lag separation to guard against manufacturing a spurious switch. v1 is unchanged and was never implicated; its shared-vs-phase-specific relational design, covariate residualization, execution-feature control, and negative/positive controls remain sound and evidence-grounded. Both variants keep distinct, evidence-backed operationalizations of the protected relational-invariance and qualitative-boundary constructs, with no merging of the two theoretical accounts, appropriately bounded predictive (not causal/mechanistic) claim ceilings, and explicit small-sample interpretation limits. The one remaining Owner item is correctly scoped as a pre-execution specification lock (epoch/binning, minimum-delay threshold, covariate-model form, and the localized-vs-continuous/staggered comparison rule), not a defect in the planning product itself, so it does not block acceptance.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
