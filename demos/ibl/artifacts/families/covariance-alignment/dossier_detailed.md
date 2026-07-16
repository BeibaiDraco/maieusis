# Which shared-variability dimensions matter for decisions? — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Replaces aggregate co-variability magnitude with tests of whether shared-variability structure aligns with independently defined decision or embodied-state dimensions.

The scientific tension is:

Shared variability may be consequential because it aligns with task-relevant readout directions, or it may primarily reflect movement and global state; aggregate magnitude cannot resolve these alternatives.

## Variant 1: Decision-alignment branch

### Why it matters

This reframes neural co-variability from a magnitude heuristic into a structural hypothesis tied to behavior.

### Original and refined question

**Original Question Scientist proposal**

Does alignment of shared neural variability with independently defined decision-relevant geometry predict choice and response-time variation better than the overall magnitude of shared variability?

**Reviewed refined question**

Across eligible BWM population recordings, does cross-fitted alignment of residual shared neural variability with an independently trained decision-relevant neural direction predict held-out trial choice or reaction-time variation beyond covariance magnitude and matched generic dimensions?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Repeated task-related neural observations with choices and response times may allow later planning of structural-alignment comparisons across regions.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavior release reports 459 sessions, 295920 trial-behavior feature rows, 453 sessions with DLC, and 847042 DLC trial-feature rows. Trial metadata names choice, left/right contrast, stimulus, go-cue, first-movement, response, and feedback times; trial features name signed_contrast, choice_label, correct, reaction_time, and movement_time. DLC trial features are keyed by eid, trial_id, camera, and window_spec with feature_mean and feature_peak.
  - Limitation: DLC feature-table summaries are lower-dimensional aggregates and cannot by themselves establish a multidimensional pose geometry.
  - Limitation: Availability and timing exclusions must be recomputed prospectively within the executor.
- **Unverified planning evidence:** Existing local pilot code joins wheel and DLC trial features by eid and trial_id, filters declared temporal windows, and calls a spike-count helper with unit subsets and trial event times. It is supporting loader precedent only: it does not implement cross-fitted shared-variability decomposition, neural-to-pose geometry alignment, or the proposed inference.
  - Limitation: Repository code is not an approved executor and may not be reused as an execution artifact without later capability review.
  - Limitation: The inspection establishes interface precedent, not correctness of the proposed analysis.
- **Unverified planning evidence:** The inspected behavior archive contains compressed coordinate and likelihood streams for multiple body, left-camera, and right-camera landmarks, including nose, pupil landmarks, paws, tongue, and tail. The ephys summary reports 459 sessions, 699 insertions, 75395 units, and insertion-keyed spike shards containing spike-time and cluster arrays.
  - Limitation: One archive demonstrates the raw pose surface but does not prove every session or camera has every landmark.
  - Limitation: No raw coordinate or spike values, participant identifiers, or scientific outcomes were retained.
- 1 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Eligible BWM task sessions with synchronized trial metadata, sufficient quality-controlled units in a prespecified region or population, and outcome-appropriate pre-outcome neural windows.
- Unit of observation: A held-out eligible trial with a trial-aligned population response and behavioral outcome.
- Unit of inference: Session-level effect estimate, pooled across sessions with a hierarchical meta-analytic model; trial-level dependence remains nested within session.
- Hierarchy and dependence: Split and fit within session; do not mix trials across splits. Estimate session-specific effects with clustered uncertainty, then model session and region heterogeneity rather than treating trials or units as independent replicates.
- Validation: Use train-validation-test nesting, label/permutation nulls that preserve session and task structure, direction-split stability checks, and synthetic recovery tests showing that the executor distinguishes oriented covariance from equal-magnitude covariance.
- Split strategy: Blocked or stratified trial folds within session, with all geometry, nuisance fitting, dimensionality selection, and hyperparameters learned only from the corresponding training fold; final predictions use untouched held-out trials.
- Claim ceiling: associational

**Analysis strategy**

1. Before outcome testing, prespecify quality filters, anatomical grouping, pre-outcome windows, and a trial split stratified by task condition.
2. Within each training split, regress task covariates and allowed pre-outcome movement covariates from neural counts, estimate a low-rank residual covariance basis, and calculate total shared-variability magnitude.
3. Independently train the decision-relevant neural direction on a disjoint training partition using task-relevant choice information with stimulus, prior, and movement-time covariates; align its sign only by the training convention.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: A random orthogonal direction matched to the decision direction's norm and reliability.; Within-session outcome-label permutation refit under the same cross-fitting protocol.
- Positive controls: Synthetic count data with known decision-aligned covariance and equal-magnitude orthogonal covariance.; Recovery of task-condition information by the independently trained direction on its validation partition.
- Alternative explanations: Aggregate covariance magnitude, dimensionality, or population reliability drives apparent alignment.; Stimulus, prior, response preparation, or residual movement explains behavioral prediction.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- This observational plan can establish predictive association, not causal influence of covariance orientation on behavior.
- Trial timing and incomplete behavioral measurement can leave state-related confounding.

**Why the plan serves the question**

The primary contrast remains orientation versus aggregate shared-variability magnitude, with decision geometry estimated independently and all behavior prediction evaluated on held-out trials.

**Before any later execution**

- Unresolved planning decisions: Whether reaction-time inference will use survival, robust continuous, or ordinal modeling after prospective distribution checks.
- Required future skills: Decode compressed BWM spike and pose streams into time-aligned arrays without producing raw-data artifacts.; Perform cross-fitted residual covariance decomposition, direction-alignment scoring, hierarchical inference, and synthetic method recovery.

### Scientific stakes

**Discriminating observation**

Alignment would be favored if independently estimated decision-relevant orientation predicts choice or response-time variation beyond aggregate shared-variability magnitude and matched generic dimensions.

**What possible outcomes would mean**

- Positive pattern: A positive result would support a predictive structural account of behaviorally consequential co-variability.
- Negative pattern: A negative result would favor magnitude-based, generic-state, or region-specific alternatives.
- Null or ambiguous pattern: A null result would indicate that alignment and magnitude are not distinguishable at the available reliability or population scale.

## Variant 2: Embodied-state specificity branch

### Why it matters

Separating decision alignment from embodied-state alignment prevents generic co-variation from being interpreted as a task-specific neural code.

### Original and refined question

**Original Question Scientist proposal**

Are shared-variability dimensions that appear decision-related better explained by alignment with multidimensional pose and ongoing behavioral state?

**Reviewed refined question**

For eligible BWM population recordings, are cross-fitted shared-variability dimensions more geometrically aligned with independently estimated multidimensional pose and ongoing behavioral state than with independently estimated decision geometry, after matched reliability and temporal controls?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

The narrative's joint electrophysiology, task, response, and video-derived pose modalities may support later planning of matched representational comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavior release reports 459 sessions, 295920 trial-behavior feature rows, 453 sessions with DLC, and 847042 DLC trial-feature rows. Trial metadata names choice, left/right contrast, stimulus, go-cue, first-movement, response, and feedback times; trial features name signed_contrast, choice_label, correct, reaction_time, and movement_time. DLC trial features are keyed by eid, trial_id, camera, and window_spec with feature_mean and feature_peak.
  - Limitation: DLC feature-table summaries are lower-dimensional aggregates and cannot by themselves establish a multidimensional pose geometry.
  - Limitation: Availability and timing exclusions must be recomputed prospectively within the executor.
- **Unverified planning evidence:** Existing local pilot code joins wheel and DLC trial features by eid and trial_id, filters declared temporal windows, and calls a spike-count helper with unit subsets and trial event times. It is supporting loader precedent only: it does not implement cross-fitted shared-variability decomposition, neural-to-pose geometry alignment, or the proposed inference.
  - Limitation: Repository code is not an approved executor and may not be reused as an execution artifact without later capability review.
  - Limitation: The inspection establishes interface precedent, not correctness of the proposed analysis.
- **Unverified planning evidence:** The inspected behavior archive contains compressed coordinate and likelihood streams for multiple body, left-camera, and right-camera landmarks, including nose, pupil landmarks, paws, tongue, and tail. The ephys summary reports 459 sessions, 699 insertions, 75395 units, and insertion-keyed spike shards containing spike-time and cluster arrays.
  - Limitation: One archive demonstrates the raw pose surface but does not prove every session or camera has every landmark.
  - Limitation: No raw coordinate or spike values, participant identifiers, or scientific outcomes were retained.
- 1 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Eligible BWM task sessions with synchronized spike, trial, and high-confidence multi-landmark camera data; analyses report camera and region coverage rather than generalizing beyond complete data.
- Unit of observation: A held-out eligible trial-window with neural population activity and a synchronized pose-state representation.
- Unit of inference: Session-level difference between pose and decision alignment, synthesized across sessions and regions.
- Hierarchy and dependence: All representations and comparisons are cross-fitted within session. Session-level contrasts are modeled hierarchically with region as a prespecified moderator; frame-level autocorrelation is absorbed during pose feature construction and not treated as independent evidence.
- Validation: Use nested cross-fitting, reliability matching, camera/landmark holdout sensitivity, time-shifted pose nulls that respect autocorrelation blocks, and synthetic mixtures with known pose and decision contributions.
- Split strategy: Assign complete trials to blocked folds; all pose basis, decision basis, covariance basis, imputation parameters, and dimensionality choices are trained only on the corresponding training fold.
- Claim ceiling: associational

**Analysis strategy**

1. Predefine pre-stimulus, deliberation, and pre-movement windows, and construct pose features from high-confidence landmark coordinates, velocities, pupil measures where available, and wheel state.
2. Fit a session-specific pose-state basis on training data only after camera normalization and confidence masking; fit a separate decision geometry from neural activity and task variables on disjoint training data.
3. Estimate residual neural shared-variability dimensions on a third training partition after task and timing covariates, then score their held-out geometric alignment with the locked pose and decision bases.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Circularly shifted pose trajectories within session using blocks longer than local autocorrelation.; Reliability-matched random neural and pose directions.
- Positive controls: Synthetic mixed-representation data with recoverable pose-only, decision-only, and overlapping dimensions.; Within-training-fold reconstruction of held-out pose features from the learned pose basis.
- Alternative explanations: Pose and decision covary because preparation or stimulus strength changes both.; Differential measurement reliability or camera coverage favors one geometry.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Alignment comparisons are observational and cannot determine whether pose causes neural variability or both are driven by unmeasured state.
- The planned pose construct is limited by camera visibility, landmark confidence, and two-dimensional viewpoints.

**Why the plan serves the question**

The plan makes pose-state geometry a competing representation rather than a nuisance, directly preserving the decision-versus-embodied-state discriminating observation.

**Before any later execution**

- Unresolved planning decisions: Choose the preregistered common landmark set and whether missing cameras trigger exclusion or a camera-stratified primary analysis.
- Required future skills: Decode and synchronize compressed multi-camera DLC landmarks and spike shards with trial events.; Fit cross-fitted reliability-matched neural, decision, and pose geometry with temporal nulls and hierarchical comparison.

### Scientific stakes

**Discriminating observation**

A decision-specific account would be favored if alignment with independently defined decision geometry remains predictive after comparison with pose-state geometry; stronger or exclusive pose alignment would favor an embodied-state account.

**What possible outcomes would mean**

- Positive pattern: A positive decision-specific result would narrow the interpretation of shared variability toward task computation.
- Negative pattern: A negative result favoring pose would reclassify apparently decision-related variance as embodied-state representation.
- Null or ambiguous pattern: A null result would suggest inseparable or weakly measured decision and pose geometries rather than proving either account.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct protected contrasts and provide credible associational, cross-fitted plans. The plans independently estimate the relevant geometries, evaluate held-out comparisons within session, address nested dependence, and retain appropriate observational limits. Remaining choices are pre-execution locks rather than planning-stage scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Prespecify eligibility thresholds, a leakage-safe pre-outcome neural window, and the reaction-time model before execution.
- **Pre execution lock:** Prespecify the common landmark set and whether missing cameras require exclusion or a camera-stratified primary analysis before execution.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variant plans preserve their distinct protected contrasts (structural consequence via alignment-vs-magnitude for variant-01; representational specificity via decision-vs-pose alignment for variant-02) and are grounded in the bounded BWM evidence views. Each independently estimates the relevant geometries, evaluates comparisons on held-out within-session trials with cross-fitting, addresses nested trial-within-session dependence hierarchically, and honestly caps claims at associational. The sibling separation is explicit and non-mergeable, matching the forbidden_semantic_merges. Alternative explanations, matched generic/reliability controls, permutation and time-shift nulls, and…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
