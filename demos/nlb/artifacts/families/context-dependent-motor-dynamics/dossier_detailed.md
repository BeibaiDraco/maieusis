# Context-dependent balance of autonomous and input-linked motor dynamics — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether delayed-reach population dynamics retain a common autonomous-like organization or become more input-linked when trajectory demands change, while keeping preparatory and execution-period interpretations separate.

The scientific tension is:

Low-dimensional reach dynamics can be consistent with internally organized evolution, but trajectory constraints and behavioral feedback may also shape the observed activity. Straight and curved reaches offer a proposal-stage contrast without making either account uniquely identifiable from geometry alone.

## Variant 1: Preparation-focused test of whether reusable population organization coexists with curvature-selective prospective path specification

### Why it matters

Distinguishing a shared preparatory component from superimposed path-informative structure would refine accounts of how movement-producible states accommodate trajectory demands without treating any condition difference as evidence for a wholly separate preparation mechanism.

### Original and refined question

**Original Question Scientist proposal**

During movement preparation, does population-state organization generalize between straight and curved reaches, or does curvature demand produce distinct preparatory organization?

**Post-novelty revised proposal**

During movement preparation, do straight and curved reaches share a population-level preparatory organization with superimposed curvature-selective components that prospectively specify the future path, or is preparatory organization fully condition-general once covarying movement demands are separated?

**Reviewed refined question**

During movement preparation, do straight and curved delayed reaches share a population-level preparatory organization (a cross-condition mapping that preserves relative population-state structure) onto which a curvature-selective component is superimposed that prospectively predicts subsequently measured hand-path curvature (realized future path) beyond binary maze-condition separability, or is preparatory organization condition-general once designed condition and covarying movement demands are accounted for?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the described delayed-reaching release permits preparation periods, straight and curved trajectories, and relevant behavioral properties to be distinguished, it may support a population-level comparison of shared correspondence and curvature-selective future-path information. Exact coverage and identifiability remain for later verification.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The DANDI 000140 (MC_Maze_Small) release contains sorted-unit spiking times and behavioral data from one rhesus macaque (Jenkins) performing delayed center-out reaches around barriers, producing a mix of straight and curved reaches. Recordings span primary motor cortex (M1) and dorsal premotor cortex (PMd); cursor, hand, eye position and offline-computed hand velocity are recorded. The scaled release is limited to 100 train and 100 test trials. The first digit of each unit ID indicates region (leading 1 = PMd, leading 2 = M1); a documented conversion error makes stored M1 electrode indices low by 96 rows, so region assignment must use the unit-ID rule and the +96 electrode-row correction. A bounded metadata check in the note reports train units of 72 PMd and 70 M1. The note prescribes region reconciliation and verification of usable trial counts, event timing, and coverage before a region-specific plan proceeds, and states the combined M1+PMd population may support planning with region-stratified sensitivity analyses.
  - Limitation: Documentation-level claim; specific counts and timing were separately confirmed by bounded local inspection recorded in sibling evidence.
  - Limitation: Single subject, single session, small (100/100) release limits statistical power and generalization; proposal-stage scope only.
  - Limitation: The note explicitly states its metadata counts do not establish trial-level coverage, unit-quality equivalence, or any scientific outcome.
- **Unverified planning evidence:** DANDI:000140 version 0.220113.0408 ('MC_Maze_Small') is an OpenAccess (CC-BY-4.0) dataset of a macaque performing a delayed center-out reaching task with obstructing barriers forming a maze, yielding a variety of straight and curved reaches. Neural activity was recorded from electrode arrays in motor cortex (M1) and dorsal premotor cortex (PMd) (anatomy terms UBERON:0001384 Primary motor cortex and UBERON:0016634 Premotor cortex). Cursor, hand, and eye position were recorded and hand velocity computed offline. The manifest lists numberOfFiles=2, numberOfSubjects=1, species Rhesus monkey, NWB data standard, spike-sorting and analytical measurement techniques, and variableMeasured Units and ProcessingModule. The release is provided as part of the Neural Latents Benchmark and, per the description, is limited to 100 train and 100 test trials.
  - Limitation: Manifest-level metadata; does not itself enumerate per-trial conditions or event timing (confirmed separately by schema and sample inspection).
  - Limitation: Single subject and session; small release constrains power and generalization; proposal-stage scope only.
- **Unverified planning evidence:** Aggregate counts over the 100 train trials: - num_barriers: 32 trials with 0 barriers (straight condition) and 68 trials with 9 barriers (maze/curved condition); 9 distinct maze_id values (approximately 5-12 trials each, split across the straight and curved conditions), trial_version in {0,1,2}, num_targets in {1,3}, all success=True. - split column: 75 'train' and 25 'val' (an internal NLB split within the train file). - Timing (ms): preparation window (go_cue - target_on) median 615 (range 14-999); reaction time rt median ~336 (range 241-758); execution window (stop - move_onset) median 1138 (range 979-1626). - Units: 142 total split by unit-ID leading digit into 72 PMd (leading 1) and 70 M1 (leading 2), matching the documented convention; the heldout flag marks 35 units as NLB held-out and 107 as held-in. - Behavior streams (hand_pos) are sampled at ~1000 Hz (median inter-sample interval 0.0010 s).
  - Limitation: Small single-session release: ~11 trials per maze_id and 32 straight / 68 curved trials strongly limit power for per-condition population estimates and finely resolved curvature contrasts; dependence-aware validation and sensitivity analyses are required.
  - Limitation: A subset of trials have very short preparation windows (min 14 ms), so preparation-window trials must be screened by a minimum-delay inclusion rule.
  - Limitation: Region assignment via leading digit still requires the documented M1 +96 electrode-row correction before any region-stratified claim; counts here are aggregate only.
  - Limitation: Bounded planning diagnostic, not a scientific result; no significance testing or effect optimization performed.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Proposal-stage population scope, kept explicit per the Owner ruling: sorted-unit spiking from one macaque (Jenkins), one session, spanning M1 and PMd. Primary analysis pools held-in units across regions with region assignment via the documented unit-ID leading-digit rule plus the M1 +96 electrode-row correction, with region-stratified sensitivity checks. No dataset-specific generalization beyond this subject/session is claimed.
- Unit of observation: A single delayed-reach trial's preparatory population state (binned spike counts over the pre-movement window).
- Unit of inference: The trial (with condition/covariate structure); inference is over trials within this single subject/session.
- Hierarchy and dependence: Trials are nested within maze_id conditions and within one session. Dependence is handled by trial-level cross-validation and permutation that respect condition blocks, avoiding leakage of the same trial across preparatory-state estimation and curvature prediction, and by reporting maze_id-clustered variability rather than treating time bins as independent.
- Validation: Nested, trial-level cross-validation with condition-aware folds; permutation/label-shuffle nulls for the correspondence and prospective-prediction estimands; method-recovery on synthetic populations with known shared-plus-selective structure to confirm the pipeline can recover prospective curvature information when present and reject it when absent.
- Split strategy: Leakage-safe trial-level splits; the trial contributing a preparatory state never appears in both training and test for its own curvature prediction; internal train/val split respected.
- Claim ceiling: predictive

**Analysis strategy**

1. Define a pre-movement preparation window per trial (target_on_time to go_cue_time, with a prespecified minimum-delay inclusion threshold) and bin held-in population spike counts within it.
2. Estimate low-dimensional preparatory population states (e.g. PCA / factor-style latent estimation with cross-validated dimensionality) separately and jointly for straight and curved conditions.
3. Establish cross-condition population correspondence via alignment (e.g. cross-condition subspace/Procrustes or nonlinear mapping) that preserves relative population-state organization, explicitly not assuming linearity, and quantify shared-versus-selective structure.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Shuffle measured-curvature labels across trials within condition; prospective-prediction estimand should collapse to chance.; Predict a scientifically irrelevant/post-hoc-permuted target from the preparatory component as a null.
- Positive controls: Recover known coarse reach direction/target identity from preparatory states (expected to be decodable), confirming the population signal and pipeline sensitivity.
- Alternative explanations: Condition separation reflecting learned task structure, adaptation-like reassociation, or uniform memory-related state shifts rather than prospective curvature specification.; Apparent curvature selectivity driven by reach direction, endpoint, duration, speed, muscle/kinetic demand, or anticipated online-control requirements.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Prospective interpretation is pre-movement structure predicting subsequently measured path geometry; it is not causal and not a demonstration that preparation controls the path.
- Designed maze condition is not equated with realized curvature; a binary barrier-count effect is insufficient evidence of prospective path specification.
- Small single-subject/session data cap covariate separation and generalization; planning evidence is not a scientific result.

**Why the plan serves the question**

The plan preserves the variant intent by testing coexistence of a shared preparatory organization and a curvature-selective component that prospectively predicts realized future path, using the Owner-authorized measured-curvature operationalization, keeping it distinct from binary maze decoding and from the execution-period question, and controlling the covariates the invariant names, within the honest limits of the release.

**Before any later execution**

- Unresolved planning decisions: Final preparation-window bounds, minimum-delay threshold, and held-in unit / region-stratification rules.
- Required future skills: A population-dynamics executor skill: windowed spike binning, cross-validated latent-state and cross-condition alignment estimation, curvature computation from hand_pos, and permutation-based prospective-prediction inference with region stratification.

### Scientific stakes

**Discriminating observation**

The central observation would be a reproducible population-level correspondence between preparatory states for straight and curved reaches—defined as a cross-condition mapping that preserves their relative population-state organization—together with a curvature-selective component that carries prospective information about future path variation beyond binary condition separability. Attribution to intended curvature would require that this component remain distinguishable, where the data permit, from reach direction, endpoint, duration, speed, muscle or kinetic demand, and online-control requirements. Mere condition separation, dimensionality differences, or uniform state shifts would not by themselves discriminate curvature specification from learned task structure, adaptation-like reassociation, or motor memory.

**What possible outcomes would mean**

- Positive pattern: Evidence for both preserved cross-condition population correspondence and curvature-selective prospective path information would support a compositional account in which reusable preparation coexists with path-specific state formation; neither component would exclude the other.
- Negative pattern: Robust population-level correspondence without detectable curvature-selective future-path information, despite adequate distinction of relevant covariates, would favor a fully condition-general preparatory organization for this contrast and constrain claims that curvature shapes preparation before movement.
- Null or ambiguous pattern: Unstable correspondence, weak curvature-selective estimates, or condition separation that lacks prospective path information or cannot be distinguished from behavioral demands and learned task structure would leave the curvature-specific interpretation unresolved rather than favoring either a wholly shared or compositional organization.

## Variant 2: Execution-focused test of autonomous-like versus input-linked dynamics

### Why it matters

The contrast could clarify when autonomous-like and input-linked interpretations of motor-cortical dynamics are most plausible within a single reaching paradigm.

### Original and refined question

**Original Question Scientist proposal**

During reach execution, are curved-path population dynamics disproportionately associated with ongoing behavioral input relative to straight-path dynamics?

**Reviewed refined question**

During reach execution, is condition-specific neural population evolution preferentially associated with time-varying behavioral deviations during curved reaches relative to straight reaches, after accounting for broad trajectory structure and movement-duration/kinematic confounds, at an associational level?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Concurrent spiking, hand, cursor, and eye measurements may support later planning of an associational test contrasting straight and curved execution.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The DANDI 000140 (MC_Maze_Small) release contains sorted-unit spiking times and behavioral data from one rhesus macaque (Jenkins) performing delayed center-out reaches around barriers, producing a mix of straight and curved reaches. Recordings span primary motor cortex (M1) and dorsal premotor cortex (PMd); cursor, hand, eye position and offline-computed hand velocity are recorded. The scaled release is limited to 100 train and 100 test trials. The first digit of each unit ID indicates region (leading 1 = PMd, leading 2 = M1); a documented conversion error makes stored M1 electrode indices low by 96 rows, so region assignment must use the unit-ID rule and the +96 electrode-row correction. A bounded metadata check in the note reports train units of 72 PMd and 70 M1. The note prescribes region reconciliation and verification of usable trial counts, event timing, and coverage before a region-specific plan proceeds, and states the combined M1+PMd population may support planning with region-stratified sensitivity analyses.
  - Limitation: Documentation-level claim; specific counts and timing were separately confirmed by bounded local inspection recorded in sibling evidence.
  - Limitation: Single subject, single session, small (100/100) release limits statistical power and generalization; proposal-stage scope only.
  - Limitation: The note explicitly states its metadata counts do not establish trial-level coverage, unit-quality equivalence, or any scientific outcome.
- **Unverified planning evidence:** DANDI:000140 version 0.220113.0408 ('MC_Maze_Small') is an OpenAccess (CC-BY-4.0) dataset of a macaque performing a delayed center-out reaching task with obstructing barriers forming a maze, yielding a variety of straight and curved reaches. Neural activity was recorded from electrode arrays in motor cortex (M1) and dorsal premotor cortex (PMd) (anatomy terms UBERON:0001384 Primary motor cortex and UBERON:0016634 Premotor cortex). Cursor, hand, and eye position were recorded and hand velocity computed offline. The manifest lists numberOfFiles=2, numberOfSubjects=1, species Rhesus monkey, NWB data standard, spike-sorting and analytical measurement techniques, and variableMeasured Units and ProcessingModule. The release is provided as part of the Neural Latents Benchmark and, per the description, is limited to 100 train and 100 test trials.
  - Limitation: Manifest-level metadata; does not itself enumerate per-trial conditions or event timing (confirmed separately by schema and sample inspection).
  - Limitation: Single subject and session; small release constrains power and generalization; proposal-stage scope only.
- **Unverified planning evidence:** Aggregate counts over the 100 train trials: - num_barriers: 32 trials with 0 barriers (straight condition) and 68 trials with 9 barriers (maze/curved condition); 9 distinct maze_id values (approximately 5-12 trials each, split across the straight and curved conditions), trial_version in {0,1,2}, num_targets in {1,3}, all success=True. - split column: 75 'train' and 25 'val' (an internal NLB split within the train file). - Timing (ms): preparation window (go_cue - target_on) median 615 (range 14-999); reaction time rt median ~336 (range 241-758); execution window (stop - move_onset) median 1138 (range 979-1626). - Units: 142 total split by unit-ID leading digit into 72 PMd (leading 1) and 70 M1 (leading 2), matching the documented convention; the heldout flag marks 35 units as NLB held-out and 107 as held-in. - Behavior streams (hand_pos) are sampled at ~1000 Hz (median inter-sample interval 0.0010 s).
  - Limitation: Small single-session release: ~11 trials per maze_id and 32 straight / 68 curved trials strongly limit power for per-condition population estimates and finely resolved curvature contrasts; dependence-aware validation and sensitivity analyses are required.
  - Limitation: A subset of trials have very short preparation windows (min 14 ms), so preparation-window trials must be screened by a minimum-delay inclusion rule.
  - Limitation: Region assignment via leading digit still requires the documented M1 +96 electrode-row correction before any region-stratified claim; counts here are aggregate only.
  - Limitation: Bounded planning diagnostic, not a scientific result; no significance testing or effect optimization performed.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Proposal-stage population scope kept explicit: sorted-unit spiking from one macaque (Jenkins), one session, M1 and PMd combined (held-in units, documented region correction) with region-stratified sensitivity. No generalization beyond this subject/session is claimed.
- Unit of observation: A time bin within a single reach-execution trial (population activity paired with concurrent behavioral state).
- Unit of inference: The trial (with condition structure); inference over trials within this single subject/session.
- Hierarchy and dependence: Time bins are nested within trials, trials within maze_id conditions and one session. Temporal autocorrelation and within-trial dependence are handled via trial-level cross-validation, block/circular-shift permutation nulls that preserve autocorrelation, and clustering of variance by trial and condition rather than by bin.
- Validation: Trial-level cross-validation with condition-aware folds; autocorrelation-preserving permutation nulls (block/circular shift) for the association estimand; duration-matched subsampling as a robustness check; synthetic method-recovery contrasting an input-linked generator against an autonomous generator with correlated behavior to confirm the estimand separates them only to the extent the data allow.
- Split strategy: Leakage-safe trial-level splits; no bins from a test trial appear in training; internal train/val split respected.
- Claim ceiling: associational

**Analysis strategy**

1. Define the execution window per trial (move_onset_time to stop_time) and bin held-in population activity at a resolution matched to the behavioral streams.
2. Build a per-condition broad trajectory template and compute time-varying behavioral deviations (hand position/velocity residuals) from it as the ongoing-input regressor.
3. Model the association between condition-specific neural evolution and concurrent behavioral deviations (e.g. time-resolved encoding/decoding or state-space regression), separately for straight and curved reaches.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Shuffle behavioral-deviation regressors across trials within condition; the association estimand should collapse to chance.; Time-reverse or phase-randomize the behavioral deviation as an autocorrelation-matched null.
- Positive controls: Recover the known strong association between population activity and gross hand velocity/direction during movement, confirming pipeline sensitivity.
- Alternative explanations: An autonomous trajectory generator producing richer, correlated neural and behavioral trajectories in curved reaches without online input driving neural evolution.; Unequal movement duration or kinematic complexity between conditions rather than a different dynamical regime.

**Interpretation limits**

- Associational/predictive only; no causal-feedback or online-input claim follows from curvature-related association alone.
- Correlation under an autonomous generator remains an admitted competing explanation the dataset cannot fully exclude.
- Small single-subject/session data cap power and generalization; planning evidence is not a scientific result.

**Why the plan serves the question**

The plan preserves the variant intent by asking whether execution-period neural evolution is preferentially associated with ongoing behavioral deviations in curved reaches, interpreted through the autonomy-input tension at an associational ceiling, kept separate from the preparatory-state question, with the confounds the invariant names explicitly controlled.

**Before any later execution**

- Unresolved planning decisions: Final execution-window binning resolution, trajectory-template definition, and duration-matching scheme.
- Required future skills: A population-dynamics executor skill: matched neural/behavioral binning, per-condition trajectory-template and deviation construction, time-resolved association estimation, and autocorrelation-preserving permutation inference with duration matching and region stratification.

### Scientific stakes

**Discriminating observation**

The accounts would be differentiated by whether condition-specific neural evolution is preferentially associated with time-varying behavioral deviations during curved reaches after accounting for broad trajectory structure, versus remaining comparably organized across conditions.

**What possible outcomes would mean**

- Positive pattern: Selective association with ongoing behavioral deviations in curved reaches would support an input-linked interpretation for trajectory adjustment, at an associational claim level.
- Negative pattern: Comparable organization with little selective association would favor a common internally organized account across trajectory demands.
- Null or ambiguous pattern: Indeterminate condition differences would leave the autonomy-input tension unresolved and motivate better separation of planned geometry, movement complexity, and feedback proxies.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct temporal and inferential targets. The preparation plan tests prospective, graded path prediction beyond designed condition and stated movement-demand competitors without treating it as causal. The execution plan remains explicitly associational and retains the autonomous-generator alternative. Dataset scope and limited single-session generalizability are appropriately bounded. Remaining choices are pre-execution locks, not deficiencies in the planning dossier.

Retained changes and locks:

- **Pre execution lock:** Before execution, prespecify the preparation-window bounds and minimum-delay eligibility rule, plus the held-in-unit selection and documented region-reconciliation/stratification rule.
- **Pre execution lock:** Before execution, lock the execution binning resolution, cross-validated per-condition trajectory-template construction, and duration/kinematic-complexity matching or covariate rule.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants are well-grounded in the cited evidence (schema, sample inspection, and variant-specific window/behavior evidence), preserve the family's forbidden-merge boundaries (separate temporal loci for preparation vs execution; shared/selective preparatory structure not conflated with autonomous/input-linked execution; execution kept strictly associational), and hold claims at an appropriate predictive/associational ceiling rather than a causal one. Each plan names concrete competing explanations (task-structure/adaptation confounds and movement-demand covariates for preparation; autonomous-generator and duration/complexity confounds for execution) and specifies matched positive/negative controls and leakage-safe, dependence-aware validation. The two Owner-flagged issues (preparation-window/unit-selection rules; execution-binning/template/matching rules) are legitimate but concern implementation choices needed only before execution, not the current scientific validity of the plan, so they are correctly pre-execution locks rather than blockers. No scientific blocker or hard-boundary concern is present.

Retained changes and locks:

- **Optional improvement:** Prespecify a multiple-comparison or family-wise error control plan across the two named preparation estimands (cross-condition correspondence score and incremental curvature-prediction information) and, symmetrically, across any duration-matched sensitivity variants of the execution association estimand, so that reported significance is not inflated by post hoc selection among related tests.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
