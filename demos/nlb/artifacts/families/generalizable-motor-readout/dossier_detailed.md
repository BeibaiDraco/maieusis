# Generalizable readout across trajectory contexts and cortical populations — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Separates two forms of generalization: transfer between straight and curved behavior and transfer between PMd and M1 population organization.

The scientific tension is:

A readout may succeed because it captures reusable motor structure or because it exploits context- or population-specific associations. Generalization failures can therefore reveal scientific boundaries, but they must not be treated as proof of distinct mechanisms.

## Variant 1: Cross-trajectory generalization test

### Why it matters

This turns decoder generalization into a test of representational scope rather than a methods leaderboard.

### Original and refined question

**Original Question Scientist proposal**

Does a neural representation associated with reach trajectory generalize between straight and curved paths, and what does asymmetric transfer imply about shared versus context-specific motor structure?

**Reviewed refined question**

Does a neural population readout of reach kinematics learned in one trajectory context (straight center-out vs curved maze reaches) generalize to the other, and is any transfer asymmetry consistent with shared reusable trajectory structure versus context-specific organization once unequal behavioral range and linear-readout limits are accounted for?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Straight and curved reach trajectories may support later planning of cross-context predictive evaluation.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 (version 0.220113.0408) is MC_Maze_Small: sorted-unit spiking times and behavioral data from ONE rhesus macaque (subject Jenkins) performing a delayed center-out reaching task with obstructing barriers forming a maze, yielding a variety of straight and curved reaches. Neural activity was recorded simultaneously from electrode arrays in primary motor cortex (M1) and dorsal premotor cortex (PMd). Cursor, hand, and eye position were recorded; hand velocity was computed offline. The release is limited to 100 train trials and 100 test trials (two NWB files).
  - Limitation: Single subject, single session: no across-subject or across-session generalization is possible.
  - Limitation: Small release (100 train / 100 test trials) constrains statistical power and per-condition counts.
  - Limitation: Documentation-level claim; specific counts are verified in separate schema/metadata evidence records.
- **Unverified planning evidence:** processing/behavior provides hand_pos, hand_vel, cursor_pos, and eye_pos, each a (287710, 2) timeseries with a matching (287710,) timestamps vector sampled at ~1 ms (median dt = 1.0 ms), spanning 0.0-293.665 s. Trial start times span 0.0-290.8 s and lie within the behavioral timestamp range, so continuous hand kinematics can be windowed to per-trial movement epochs (e.g. relative to move_onset_time). hand_vel is present as a derived signal. This continuous, trial-alignable 2D kinematic record supports trajectory/ velocity decoding targets. Behavioral timeseries are present in the train NWB file; the companion test file is 'desc-test_ecephys.nwb' (ecephys only), i.e. its trial-level behavior is a held-out NLB target and was NOT inspected.
  - Limitation: Only the train file carries behavior; analysis/evaluation must stay within the 100 train-file trials (train/val split), and NLB held-out test outcomes must not be used.
  - Limitation: 2D planar kinematics only; no force/EMG. Eye position present but not required for reach-trajectory constructs.
  - Limitation: Sampling and alignment verified structurally; kinematic quality per trial not assessed here.
- **Unverified planning evidence:** The train file contains 142 sorted units. Applying the documented MC_Maze unit-ID convention (leading digit 1 =&gt; PMd, leading digit 2 =&gt; M1) yields 72 PMd and 70 M1 units, matching the DATASET_NOTES.md and verify_region_mapping.py expected counts. The electrode table has 192 rows with location/group_name evenly split PMd=96 / M1=96 and named electrode groups electrode_group_PMd and electrode_group_M1 (devices electrode_array_PMd, electrode_array_M1). DATASET_NOTES.md documents a conversion error: stored units/electrodes indices for M1 units are off and the correct electrode-table row requires adding 96; before correction all stored unit electrode indices fall in the first 96 rows, so raw electrode indices alone must not be used to infer region. Both regions are present after the unit-ID rule and +96 correction. A units/heldout boolean flags 35 units True and 107 False (the NLB co-smoothing held-out-neuron split).
  - Limitation: Region assignment relies on the documented unit-ID convention plus the +96 electrode correction; any unresolved metadata disagreement must be surfaced, not silently resolved.
  - Limitation: The heldout-unit flag is an NLB benchmark artifact; region analyses should decide explicitly whether to use held-in units only.
  - Limitation: Unit quality/yield equivalence between regions is not established by these counts.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: One rhesus macaque (Jenkins), single delayed center-out maze session; combined M1+PMd sorted units. Inference is within-subject across trials; no across-subject or across-session claim.
- Unit of observation: A single reach trial (movement epoch) with its binned population activity and hand-kinematic trajectory.
- Unit of inference: Reach trial within the single session; generalization is assessed across trials via resampling, not across subjects.
- Hierarchy and dependence: Trials are nested within one session/subject and within target directions; resampling and evaluation will respect target-direction balance and avoid leakage between train and evaluation folds. Temporal autocorrelation within a trial is handled by trial-level (not sample-level) splitting.
- Validation: Trial-level cross-validation/bootstrap within the train-file trials using the provided train/val split as an outer check; prespecified method-recovery on synthetic data with known shared vs context-specific structure to confirm the pipeline distinguishes them; no use of NLB held-out test outcomes.
- Split strategy: Leakage-safe trial-level splits stratified by target direction; contexts never mixed within a single train/evaluate fold for the transfer estimand.
- Claim ceiling: associational

**Analysis strategy**

1. Define contexts by the Owner-accepted maze task condition: num_barriers==0 (straight) vs num_barriers==9 (curved); core contrast on single-target trials, with distractor-target curved trials as a robustness set.
2. Build a population decoder (prespecified family, e.g. regularized linear/Wiener or a fixed nonlinear baseline) mapping binned population activity to hand velocity/trajectory.
3. Estimate directional transfer: train within straight and evaluate on curved and vice versa, reporting both directions alongside within-context cross-validated prediction.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Shuffled trial-label / time-reversed kinematics decoding to establish chance transfer.
- Positive controls: Within-context decoding should recover reach kinematics well above chance, confirming decodable trajectory signal.
- Alternative explanations: Asymmetry driven by unequal behavioral range/complexity (curved trials span wider kinematics) rather than representational structure.; Linear readout missing shared nonlinear structure.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Decoding is a predictive method used to license an associational claim about representational generalization, not a causal or mechanistic claim.
- Single subject/session and small per-context counts preclude population-level generalization beyond this dataset.
- Transfer asymmetry is interpreted only after range and model-class alternatives are addressed; planning evidence is not a scientific result.

**Why the plan serves the question**

It tests directional straight&lt;-&gt;curved transfer with within-context baselines and treats asymmetry as informative, preserving the variant's intent while explicitly guarding the range and nonlinearity alternatives named in the intent invariant.

**Before any later execution**

- Unresolved planning decisions: Lock decoder family, validation/resampling scheme, bin width, and movement-epoch window before execution (Owner-required).

### Scientific stakes

**Discriminating observation**

Bidirectional versus directional transfer, interpreted alongside within-condition prediction and geometry-sensitive alternatives, would distinguish common-scope, nested-scope, and context-specific accounts.

**What possible outcomes would mean**

- Positive pattern: Reliable bidirectional transfer would support a reusable representation spanning trajectory contexts.
- Negative pattern: Reliable context-specific prediction with failed transfer would support a boundary on representational generalization, subject to nonlinear and sampling alternatives.
- Null or ambiguous pattern: Poor within-condition and cross-condition prediction would not adjudicate generalization and would instead question signal reliability or construct definition.

## Variant 2: Cross-region compatibility and transfer test

### Why it matters

The question tests distributed compatibility without equating regional similarity with identical computation.

### Original and refined question

**Original Question Scientist proposal**

Are trajectory-related population organizations in PMd and M1 related by a shared readout or transformation, or are their predictive relationships region-specific?

**Reviewed refined question**

Are trajectory-related population organizations in PMd and M1 related by a shared or simply transformed readout, or are their predictive relationships to reach behavior region-specific, once unequal sampling and signal quality across regions are accounted for?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

The two named cortical regions and concurrent reach measurements may support a later region-stratified predictive comparison after metadata validation.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 (version 0.220113.0408) is MC_Maze_Small: sorted-unit spiking times and behavioral data from ONE rhesus macaque (subject Jenkins) performing a delayed center-out reaching task with obstructing barriers forming a maze, yielding a variety of straight and curved reaches. Neural activity was recorded simultaneously from electrode arrays in primary motor cortex (M1) and dorsal premotor cortex (PMd). Cursor, hand, and eye position were recorded; hand velocity was computed offline. The release is limited to 100 train trials and 100 test trials (two NWB files).
  - Limitation: Single subject, single session: no across-subject or across-session generalization is possible.
  - Limitation: Small release (100 train / 100 test trials) constrains statistical power and per-condition counts.
  - Limitation: Documentation-level claim; specific counts are verified in separate schema/metadata evidence records.
- **Unverified planning evidence:** processing/behavior provides hand_pos, hand_vel, cursor_pos, and eye_pos, each a (287710, 2) timeseries with a matching (287710,) timestamps vector sampled at ~1 ms (median dt = 1.0 ms), spanning 0.0-293.665 s. Trial start times span 0.0-290.8 s and lie within the behavioral timestamp range, so continuous hand kinematics can be windowed to per-trial movement epochs (e.g. relative to move_onset_time). hand_vel is present as a derived signal. This continuous, trial-alignable 2D kinematic record supports trajectory/ velocity decoding targets. Behavioral timeseries are present in the train NWB file; the companion test file is 'desc-test_ecephys.nwb' (ecephys only), i.e. its trial-level behavior is a held-out NLB target and was NOT inspected.
  - Limitation: Only the train file carries behavior; analysis/evaluation must stay within the 100 train-file trials (train/val split), and NLB held-out test outcomes must not be used.
  - Limitation: 2D planar kinematics only; no force/EMG. Eye position present but not required for reach-trajectory constructs.
  - Limitation: Sampling and alignment verified structurally; kinematic quality per trial not assessed here.
- **Unverified planning evidence:** The train file contains 142 sorted units. Applying the documented MC_Maze unit-ID convention (leading digit 1 =&gt; PMd, leading digit 2 =&gt; M1) yields 72 PMd and 70 M1 units, matching the DATASET_NOTES.md and verify_region_mapping.py expected counts. The electrode table has 192 rows with location/group_name evenly split PMd=96 / M1=96 and named electrode groups electrode_group_PMd and electrode_group_M1 (devices electrode_array_PMd, electrode_array_M1). DATASET_NOTES.md documents a conversion error: stored units/electrodes indices for M1 units are off and the correct electrode-table row requires adding 96; before correction all stored unit electrode indices fall in the first 96 rows, so raw electrode indices alone must not be used to infer region. Both regions are present after the unit-ID rule and +96 correction. A units/heldout boolean flags 35 units True and 107 False (the NLB co-smoothing held-out-neuron split).
  - Limitation: Region assignment relies on the documented unit-ID convention plus the +96 electrode correction; any unresolved metadata disagreement must be surfaced, not silently resolved.
  - Limitation: The heldout-unit flag is an NLB benchmark artifact; region analyses should decide explicitly whether to use held-in units only.
  - Limitation: Unit quality/yield equivalence between regions is not established by these counts.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: One rhesus macaque (Jenkins), single session; PMd (72) and M1 (70) sorted units recorded simultaneously. Inference is within-subject across trials; no across-subject claim.
- Unit of observation: A single reach trial's region-specific population activity (PMd and M1 observed on the same trial).
- Unit of inference: Reach trial within the single session; cross-region relationships assessed across trials via resampling.
- Hierarchy and dependence: PMd and M1 observations are paired within trials (shared conditions), enabling within-trial alignment; trial-level resampling stratified by target direction handles dependence; region comparisons control for differing unit counts by subsampling/matched-dimensionality checks.
- Validation: Trial-level cross-validation within train-file trials; permutation/null alignment (shuffled trial correspondence) to calibrate chance alignment; synthetic method-recovery with known shared vs transformed vs independent regional codes; no NLB held-out test outcomes used.
- Split strategy: Leakage-safe trial-level splits stratified by target direction; alignment learned on training trials and evaluated on held-out trials.
- Claim ceiling: associational

**Analysis strategy**

1. Extract per-trial movement-epoch population activity separately for PMd and M1; build region-specific low-dimensional latent trajectories tied to reach conditions.
2. Test cross-region compatibility three ways: (a) a common (shared) readout mapping either region's activity to the same kinematic/latent target; (b) a transformed readout (learned linear/affine alignment, e.g. regression/CCA/Procrustes on shared trials); (c) region-specific readouts as the baseline.
3. Compare compatible vs transformed vs region-specific accounts by held-out predictive performance and alignment quality, with region-wise reliability checks.

**Controls**

- Negative controls: Shuffled cross-region trial correspondence to establish chance alignment/compatibility.
- Positive controls: Within-region decoding should recover reach kinematics above chance in both PMd and M1, confirming usable region-specific signal.
- Alternative explanations: Apparent region specificity driven by unequal sampling/signal quality rather than genuine representational difference.; Alignment inflated by shared task/condition structure rather than shared neural coordinates (addressed by permutation nulls).; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Cross-region alignment is an associational compatibility claim, not evidence of a shared mechanism or causal coupling.
- Single session/subject; region assignment and unit-count imbalance are handled but not eliminated.
- Planning evidence is not a scientific result.

**Why the plan serves the question**

It contrasts common-readout, transformed-readout, and region-specific accounts with region-wise reliability and sampling controls, preserving the variant's target contrast (PMd vs M1 compatibility) and its distinct sampling/metadata alternatives without collapsing into the trajectory-context question.

**Before any later execution**

- Unresolved planning decisions: Fix the alignment method (regression/CCA/Procrustes), latent dimensionality, and held-in vs all-units policy before execution.

### Scientific stakes

**Discriminating observation**

Comparison of common-readout, transformed-readout, and region-specific predictive relationships, with region-wise reliability checks, would distinguish compatible, transformed, and apparently separate organization.

**What possible outcomes would mean**

- Positive pattern: A reliable shared or simple transformed relationship would support distributed compatibility between PMd and M1 trajectory representations.
- Negative pattern: Reliable within-region prediction with poor cross-region compatibility would support region-specific representational relationships.
- Null or ambiguous pattern: Unreliable within-region prediction or unmatched sensitivity would prevent interpretation of cross-region transfer.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve the protected distinction between behavioral-context transfer and cross-region compatibility, use only the supplied train-file evidence, and set an appropriate within-session associational claim ceiling. The remaining choices are execution locks rather than deficiencies in the scientific planning dossier.

Retained changes and locks:

- **Pre execution lock:** Before execution, prespecify the trajectory decoder family, movement-epoch and binning definition, and validation/resampling procedure for the directional straight-versus-curved transfer estimands.
- **Pre execution lock:** Before execution, prespecify the cross-region alignment method and latent dimensionality, along with the primary held-in versus all-units policy.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both sibling variants operationalize distinct, evidence-grounded generalization tests (behavioral-context transfer vs. cross-region compatibility) that faithfully preserve the family's protected intent and forbidden-merge boundaries. Dataset grounding is solid: task-condition and tortuosity-based straight/curved definitions, unit-region assignment with the documented +96 correction, and simultaneous PMd/M1 recording are all evidence-backed rather than invented. Both plans carry an associational claim ceiling with explicit interpretation limits, name concrete alternative explanations (kinematic-range confound, linear-readout limits, sampling/quality imbalance, alignment inflation), and include positive/negative controls plus diagnostics to adjudicate asymmetry versus artifact. The remaining Owner-required changes concern decoder family, binning, validation scheme, alignment method, latent dimensionality, and held-in-unit policy — all pre-execution implementation locks rather than defects in the scientific design, so they do not block acceptance of the planning product. No new scientific blocker or hard-boundary issue is identified at this round.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
