# Functional structure of preparatory population variability — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Reframes preparatory variability from a scalar decline into geometric questions about alignment with upcoming movement or association with trial-to-trial behavioral performance.

The scientific tension is:

Preparatory variability may be generic noise that contracts before movement, or its orientation may contain structured information about upcoming trajectories and behavioral readiness.

## Variant 1: Geometric test of trajectory-selective preparatory stabilization

### Why it matters

A structural account could connect preparatory stabilization to prospective trajectory organization rather than treating reduced magnitude as sufficient evidence of preparation.

### Original and refined question

**Original Question Scientist proposal**

Does declining preparatory variability preferentially contract along dimensions associated with the upcoming reach trajectory, or does it decline without selective trajectory alignment?

**Reviewed refined question**

Across the delay period, does trial-to-trial preparatory variability in the PMd (with M1 sensitivity) population contract selectively along directions aligned with independently defined upcoming-trajectory dimensions, relative to matched-dimensionality nonaligned comparison directions, in straight and curved reaches?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Delayed reaching and trajectory measurements may allow a later planner to define candidate prospective signal directions independently of preparatory variability.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The configured dataset note documents that MC_Maze unit IDs encode region by leading digit (1 = PMd, 2 = M1) and that stored M1 electrode indices are off by 96 rows (correct electrode-table row = stored + 96). It records a bounded verified train tally of 72 PMd and 70 M1 units, matching this branch's own unit inspection. It mandates, before any region-specific claim: assign units by the ID convention; apply and verify the M1 +96 correction; reconcile unit IDs, electrode metadata, DANDI metadata, and NLB docs; keep unresolved disagreements visible rather than inferring M1 absence; and verify usable trial counts and region-specific coverage. It states the combined M1+PMd population may support planning with region-stratified sensitivity, subject to small single-subject limitations.
  - Limitation: Documentation-level guidance, not a scientific result; it does not certify tuning or per-trial coverage.
  - Limitation: The +96 correction concerns electrode-table reconciliation only; the leading-digit rule is what assigns region for analysis.
- **Unverified planning evidence:** Every train trial carries a complete event sequence with no missing values: target_on_time, go_cue_time (delay-period end), move_onset_time, and stop_time. The delay column (milliseconds) has median 615 ms (5th/95th percentile 127/966 ms); 84 of 100 trials have delay &gt;= 250 ms, 78 &gt;= 400 ms, 51 &gt;= 600 ms. Reaction time (rt) median is ~336 ms and go-to-move interval mean ~336 ms. A well-defined preparatory epoch (target onset to go cue / movement onset) is therefore delimitable per trial, supporting a delay-length inclusion criterion. The condition-invariant pre-movement transition and its per-trial change time can be estimated from population activity aligned to these events.
  - Limitation: A minority of trials (~16) have very short delays (&lt;250 ms), forcing an explicit preparatory-window inclusion rule that will reduce usable n below 100.
  - Limitation: Planning-only timing summary; does not estimate the condition-invariant transition dimension or its variance, only confirms the events needed to define it are present.
- **Unverified planning evidence:** The 100 train trials span 9 distinct maze_id values crossed with barrier presence (num_barriers 0 = straight, 9 = maze/curved), giving 18 maze-by-barrier conditions. Straight reaches number 32 and curved reaches 68, so both reach geometries the family targets are present. Repeats per maze-by-barrier condition are small and uneven: 7 conditions have 8 repeats, 6 have 4, and the remainder have 2, 3, 5, or 7 (minimum 2). num_targets is 1 on 66 trials and 3 on 34 trials (distractor-target trials). At the finer (trial_type, trial_version) grain there are 27 cells of ~2-4 trials each. Trial-to-trial preparatory covariance must therefore be estimated from very few within-condition repeats, requiring pooling across conditions after condition-mean removal and strong dimensionality reduction.
  - Limitation: Minimum 2 and typical 4-8 within-condition repeats make full per-condition neural covariance rank-deficient across 72-142 units; the analysis is confined to low-dimensional subspaces with cross-validated variance estimates.
  - Limitation: Planning-only condition tally; does not itself estimate any covariance or alignment quantity.
- 4 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Sorted PMd units (72 by the documented leading-digit convention) as the primary population, with the 70 M1 units available for a region-stratified sensitivity analysis after the documented M1 +96 electrode-row reconciliation. Single subject (Jenkins), single session; delayed-reach trials with an adequate preparatory window; straight (32) and curved (68) reaches analyzed jointly and separately.
- Unit of observation: Single-trial preparatory population firing-rate state within the delay window.
- Unit of inference: Trial within one subject and session; population-geometry statistics summarized across trials and conditions.
- Hierarchy and dependence: Trials are nested within maze-by-barrier conditions. Condition means are removed before estimating trial-to-trial variability; alignment statistics are aggregated across conditions with cross-validation across trials to respect the limited-repeat structure and avoid double-counting.
- Validation: Synthetic method-recovery: generate surrogate populations with known aligned contraction, isotropic contraction, and no contraction under the observed repeat counts and dimensionality, and confirm the alignment index recovers the ground truth and controls false positives. Use cross-validated variance estimates and split-half stability. Estimate directions and variability on disjoint partitions to break circularity.
- Split strategy: Use disjoint trial partitions for direction estimation versus variability estimation; leave-one-condition-out and split-half resampling for stability. The provided train/val split is available; the held-out desc-test trials are not used.
- Claim ceiling: descriptive

**Analysis strategy**

1. Define a delay-window inclusion rule and extract per-trial preparatory firing-rate vectors over one or more sub-windows across the delay.
2. Estimate upcoming-trajectory directions in neural space from condition-averaged movement-epoch activity or from a regression of population activity onto condition-averaged hand trajectories, using a data partition disjoint from the variability estimate to avoid circularity.
3. After removing condition means, estimate trial-to-trial preparatory covariance in a low-dimensional subspace and compute a variance-alignment index: variance projected onto trajectory-aligned directions versus matched-dimensionality nonaligned/control directions.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Alignment to task-irrelevant or shuffled-trajectory directions should show no selective contraction.; Random matched-dimensionality directions as a null for the alignment index.
- Positive controls: Condition-averaged movement directions should be decodable from movement-epoch population activity, confirming the trajectory-direction estimate is meaningful.
- Alternative explanations: Apparent alignment arising from circular estimation of signal and variability axes.; Broad isotropic contraction reflecting generic state stabilization or arousal rather than trajectory-selective stabilization.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject and single session; geometric structure may not generalize.
- Few within-condition repeats constrain covariance estimation to low dimensions; results are structural/descriptive, not a scientific result produced here.
- Alignment is an associational geometric property and does not establish a causal or behavioral role of the aligned variability.

**Why the plan serves the question**

The plan measures where preparatory variability lies relative to independently defined prospective-trajectory directions, directly addressing whether contraction is trajectory-selective versus a magnitude-only decline, while explicitly guarding the circularity and isotropy alternatives named in the variant invariant.

**Before any later execution**

- Unresolved planning decisions: Delay-window inclusion threshold and number of delay sub-windows.; Subspace dimensionality and the construction of matched nonaligned control directions.
- Required future skills: A preparatory variance-geometry executor computing cross-validated aligned-vs-nonaligned variance-alignment indices with synthetic method-recovery, not currently available as a skill.

### Scientific stakes

**Discriminating observation**

Selective change in variability relative to independently defined future-trajectory directions, compared with plausible nonaligned directions, would distinguish structural stabilization from a magnitude-only decline.

**What possible outcomes would mean**

- Positive pattern: Selective trajectory alignment would support a structured account of preparatory variability associated with prospective movement organization.
- Negative pattern: A nonselective decline would constrain claims that preparatory variability reduction specifically stabilizes trajectory-relevant dimensions.
- Null or ambiguous pattern: Unreliable alignment would leave open whether variability is unstructured or simply underpowered and estimator-sensitive.

## Variant 2: Predictive test of whether preparatory instability has trajectory-quality meaning beyond a known transition-timing signal and measured path or state alternatives

### Why it matters

Focusing on trajectory quality rather than reaction time tests whether preparatory variability has behavioral meaning beyond the established association between a condition-invariant transition and movement timing, while directly evaluating measured state and path alternatives.

### Original and refined question

**Original Question Scientist proposal**

Is trial-to-trial preparatory variability associated with movement readiness or trajectory quality after accounting for planned path and concurrent behavioral state proxies?

**Post-novelty revised proposal**

Does trial-specific instability in movement-tuned preparatory population activity—defined independently of the condition-invariant pre-movement transition and its timing—incrementally predict subsequent trajectory quality beyond pre-specified planned-path representations and temporally prior or contemporaneous eye, covert-movement, and arousal proxies?

**Reviewed refined question**

Does trial-specific instability in a movement-tuned PMd (with M1 sensitivity) preparatory subspace, defined with the condition-invariant pre-movement transition and its timing excluded, incrementally predict held-out later spatial trajectory quality beyond condition-invariant transition timing, pre-movement planned-path variables, and the measured temporally eligible state proxies (eye position/velocity, covert movement) present in this dataset?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If delayed-reaching data jointly contain preparatory population activity, instructed path information, trajectories, and temporally aligned behavioral-state measurements, they may support a later test of whether a distinct preparatory-instability measure predicts trajectory quality beyond measured alternatives.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The configured dataset note documents that MC_Maze unit IDs encode region by leading digit (1 = PMd, 2 = M1) and that stored M1 electrode indices are off by 96 rows (correct electrode-table row = stored + 96). It records a bounded verified train tally of 72 PMd and 70 M1 units, matching this branch's own unit inspection. It mandates, before any region-specific claim: assign units by the ID convention; apply and verify the M1 +96 correction; reconcile unit IDs, electrode metadata, DANDI metadata, and NLB docs; keep unresolved disagreements visible rather than inferring M1 absence; and verify usable trial counts and region-specific coverage. It states the combined M1+PMd population may support planning with region-stratified sensitivity, subject to small single-subject limitations.
  - Limitation: Documentation-level guidance, not a scientific result; it does not certify tuning or per-trial coverage.
  - Limitation: The +96 correction concerns electrode-table reconciliation only; the leading-digit rule is what assigns region for analysis.
- **Unverified planning evidence:** Every train trial carries a complete event sequence with no missing values: target_on_time, go_cue_time (delay-period end), move_onset_time, and stop_time. The delay column (milliseconds) has median 615 ms (5th/95th percentile 127/966 ms); 84 of 100 trials have delay &gt;= 250 ms, 78 &gt;= 400 ms, 51 &gt;= 600 ms. Reaction time (rt) median is ~336 ms and go-to-move interval mean ~336 ms. A well-defined preparatory epoch (target onset to go cue / movement onset) is therefore delimitable per trial, supporting a delay-length inclusion criterion. The condition-invariant pre-movement transition and its per-trial change time can be estimated from population activity aligned to these events.
  - Limitation: A minority of trials (~16) have very short delays (&lt;250 ms), forcing an explicit preparatory-window inclusion rule that will reduce usable n below 100.
  - Limitation: Planning-only timing summary; does not estimate the condition-invariant transition dimension or its variance, only confirms the events needed to define it are present.
- **Unverified planning evidence:** The 100 train trials span 9 distinct maze_id values crossed with barrier presence (num_barriers 0 = straight, 9 = maze/curved), giving 18 maze-by-barrier conditions. Straight reaches number 32 and curved reaches 68, so both reach geometries the family targets are present. Repeats per maze-by-barrier condition are small and uneven: 7 conditions have 8 repeats, 6 have 4, and the remainder have 2, 3, 5, or 7 (minimum 2). num_targets is 1 on 66 trials and 3 on 34 trials (distractor-target trials). At the finer (trial_type, trial_version) grain there are 27 cells of ~2-4 trials each. Trial-to-trial preparatory covariance must therefore be estimated from very few within-condition repeats, requiring pooling across conditions after condition-mean removal and strong dimensionality reduction.
  - Limitation: Minimum 2 and typical 4-8 within-condition repeats make full per-condition neural covariance rank-deficient across 72-142 units; the analysis is confined to low-dimensional subspaces with cross-validated variance estimates.
  - Limitation: Planning-only condition tally; does not itself estimate any covariance or alignment quantity.
- 4 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Movement-tuned PMd units (primary), with M1 sensitivity after +96 reconciliation; single subject (Jenkins), single session; delayed-reach trials with an adequate preparatory window and a well-defined post-onset movement path. Outcome and predictors are per trial.
- Unit of observation: Single trial (preparatory instability, competing predictors, and trajectory-quality outcome).
- Unit of inference: Trial within one subject and session; held-out predictive performance summarized across cross-validation folds.
- Hierarchy and dependence: Trials nested within maze-by-barrier conditions; planned-path variables capture condition structure. Cross-validation folds respect condition grouping to avoid leakage, and all predictors are temporally gated to precede the outcome.
- Validation: Nested or repeated cross-validation with condition-aware folds; permutation of the instability predictor to form a null for the incremental gain; synthetic method-recovery for the transition-exclusion step; leakage audits confirming all predictors precede the outcome.
- Split strategy: Condition-grouped cross-validation on the 75 train / 25 val trials with repeated resampling; the 100 held-out desc-test trials are not accessed.
- Claim ceiling: predictive

**Analysis strategy**

1. Define trajectory-quality outcome as geometric deviation of the realized hand path from the instructed route over normalized path progress, orthogonalized against movement duration and reaction time.
2. Estimate the movement-tuned preparatory subspace and the condition-invariant transition dimension and its per-trial change time, then compute the transition-excluded trial-specific instability measure.
3. Fit a base held-out prediction model from transition timing, planned-path variables, and measured state proxies; then test whether adding preparatory instability yields reliable incremental held-out prediction of trajectory quality.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Post-outcome or scientifically irrelevant predictors should yield no incremental prediction.; Permuted instability labels as a null for the incremental gain.
- Positive controls: Planned-path difficulty should predict trajectory quality, confirming the outcome and base predictors behave sensibly.
- Alternative explanations: Apparent prediction attributable to condition-invariant transition timing rather than the distinct instability construct.; Planned-path identity, target/obstacle configuration, and preparation duration jointly driving preparatory activity and trajectory quality.; plus 3 additional item(s) in the complete dossier

**Interpretation limits**

- Pupil-arousal and EMG are unmeasured and therefore not ruled out; any positive interpretation is limited to prediction beyond the listed measured alternatives (per Owner operationalization ruling).
- Single subject, single session, and ~75 fitting trials sharply limit statistical power and generality; the claim is predictive/associational and noncausal.
- Held-out prediction is not a causal or mechanistic claim about readiness.

**Why the plan serves the question**

The plan tests incremental held-out prediction of route-referenced trajectory quality from transition-excluded preparatory instability against the measured alternatives present in the dataset, preserving the variant's behavioral-prediction contrast and its distinction from the sibling geometric variant, with the Owner-accepted bounding of the claim to the measured alternatives.

**Before any later execution**

- Unresolved planning decisions: Exact definitions of the movement-tuned subspace, the transition-exclusion procedure, and the trajectory-quality metric, to be prespecified and stability-checked.; Regularization and cross-validation scheme appropriate to the small sample.
- Required future skills: A readiness-prediction executor implementing the transition-excluded preparatory-instability measure, the route-referenced trajectory-quality outcome, and leakage-safe incremental held-out prediction; not currently available as a skill.

### Scientific stakes

**Discriminating observation**

The primary outcome is trajectory quality, not movement-onset timing. It is defined as spatial fidelity to the instructed route after movement onset, represented by geometric deviation over normalized path progress rather than by reaction time or movement duration; planned-path difficulty, duration, and timing-sensitive kinematic artifacts must be treated separately. The preparatory predictor is trial-specific fluctuation or deviation within a movement-tuned preparatory subspace, with the condition-invariant transition dimension and its estimated change time excluded. Planned path is represented from information fixed before movement, such as instructed route, target, or obstacle configuration, rather than from the realized trajectory or its timing. Eye position and velocity, pupil baseline and pre-movement change, and subtle hand or limb position, velocity, or muscle activity are candidate measured alternatives only when they precede or are contemporaneous with the preparatory measure. Incremental held-out prediction of trajectory quality beyond transition timing, path variables, and these state proxies would favor the readiness-marker account; loss of incremental prediction after a measured alternative is added would favor that alternative; weak or unstable held-out prediction would remain indeterminate.

**What possible outcomes would mean**

- Positive pattern: Reliable incremental held-out prediction would support the limited claim that movement-tuned preparatory instability is a predictive marker of later trajectory quality beyond the cited timing signal and measured path and state alternatives, without establishing causation or excluding unmeasured states.
- Negative pattern: If incremental prediction disappears after accounting for the condition-invariant transition, independently specified path variables, or temporally eligible state proxies, the corresponding measured alternative would be favored over a distinct readiness-marker interpretation.
- Null or ambiguous pattern: Weak, unstable, or definition-sensitive held-out prediction would leave the behavioral meaning of preparatory instability unresolved because it could reflect absent association, unreliable estimation, or incomplete measurement rather than evidence for any single competing account.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct scientific contrasts and have evidence-backed, non-executable plans appropriate to the available single-session dataset. The geometric variant separates trajectory-selective from isotropic contraction using independent direction estimation and matched controls. The readiness variant tests a bounded, noncausal incremental-prediction claim while retaining unavailable pupil and EMG measures as unruled-out confounds. Remaining choices are pre-execution locks, not planning blockers.

Retained changes and locks:

- **Pre execution lock:** Before execution, prespecify the delay inclusion/window rule, trajectory-direction estimator, low-dimensional subspace size, matched nonaligned directions, and nested disjoint-partition procedure for the alignment analysis; choose these without reference to observed alignment results.
- **Pre execution lock:** Before execution, prespecify the movement-tuned subspace and transition-exclusion procedure, route-referenced trajectory-quality metric, temporally eligible proxy windows, regularization, and nested condition-aware validation design for the readiness analysis.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both sibling plans are evidence-backed against the documented MC_Maze_Small single-session dataset and preserve distinct facets of the shared theoretical tension: the alignment variant tests trajectory-selective versus isotropic contraction using independently estimated trajectory directions and matched nonaligned controls with a circularity-breaking split and synthetic method-recovery; the readiness variant tests bounded incremental behavioral prediction from transition-excluded preparatory instability against a documented, dataset-limited set of competing predictors, with pupil/EMG absence explicitly carried as an unmeasured confound rather than glossed over. Claim ceilings (descriptive; predictive/noncausal) are appropriately modest given a single subject, single session, and few within-condition repeats. Negative and positive controls, leakage-safe validation, and condition-aware cross-validation are specified for both. The two remaining Owner issues concern prespecification of estimator, window, and validation choices needed only before an executor is built, not whether the current plan can credibly answer either question; they are correctly pre-execution locks rather than scientific blockers. No hard boundary is implicated, and the sibling questions remain non-overlapping per the family's forbidden-semantic-merge guidance.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
