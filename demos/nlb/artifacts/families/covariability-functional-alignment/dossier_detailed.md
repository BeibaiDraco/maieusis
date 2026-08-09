# Functional meaning of motor-population co-variability — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether the consequences of neural co-variability depend on its alignment with movement-relevant or context-relevant dimensions rather than on aggregate variability magnitude.

The scientific tension is:

Changes in overall population variability may be descriptively prominent but functionally uninformative if only particular covariance components align with task-relevant geometry.

## Variant 1: Movement-alignment branch

### Why it matters

The question replaces a coarse variability claim with a structural criterion connecting co-variability to movement representation.

### Original and refined question

**Original Question Scientist proposal**

Does the predictive consequence of motor-population co-variability depend more on alignment with movement-relevant dimensions than on its overall magnitude?

**Reviewed refined question**

In delayed maze reaching, does the predictive consequence of motor-population co-variability depend more on its alignment with an independently characterized movement-representation subspace than on its aggregate magnitude?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Repeated population activity paired with hand, cursor, and velocity measurements may allow later planning of movement-relevant alignment comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** Dataset MC_Maze_Small (DANDI:000140 v0.220113.0408) contains sorted-unit spiking and behavioral data from ONE rhesus macaque (sub-Jenkins) performing a delayed center-out reaching task with obstructing barriers forming a maze, producing a mix of straight and curved reaches. Neural activity was recorded from electrode arrays in primary motor cortex (M1) and dorsal premotor cortex (PMd). Cursor, hand, and eye position were recorded; hand velocity was computed offline. The public release is limited to 100 train and 100 test trials. This establishes the behavioral task (delayed maze reaching, straight vs curved), the recorded regions (M1 + PMd), and the single-subject scope relevant to both variants' population.
  - Limitation: Single subject, single session; no across-animal or across-session replication is possible.
  - Limitation: Documentation-level fact; trial-level coverage and reliability verified separately.
  - Limitation: Planning-only inspection; no scientific outcome computed.
- **Unverified planning evidence:** The analyzable surface with both neural and behavioral data is the train file: 100 trials (75 train / 25 val by the split column), 142 units. Straight (num_barriers=0) vs curved (num_barriers=9) split is 32 vs 68; the 9 maze layouts have only 8-12 trials each. The separate test file (sub-...desc-test) has 100 trials, 107 held-in units, and NO processing/behavior module (held out for the NLB benchmark). This bounds covariance-reliability: estimating a 142-unit covariance (or region-stratified covariance) from ~100 trials, or within small per-condition subsets, is sampling-limited and requires shrinkage, cross-validation, and explicit split-half / bootstrap reliability estimation before any alignment or residual-alignment claim. It directly motivates each variant's requirement to distinguish a genuinely shared / low-alignment covariance structure from failure to estimate covariance reliably.
  - Limitation: Small single-session sample caps the claim ceiling at descriptive/associational and makes an 'inconclusive due to unreliable estimation' outcome a real possibility that the plan must be able to declare honestly.
  - Limitation: Test-file behavioral outcomes are benchmark held-out and must not be inspected; all planning uses only the train-file behavior.
  - Limitation: Counting-level metadata inspection only; no covariance or reliability statistics computed.
- **Unverified planning evidence:** The train file has 100 trials with rich, neural-independent condition metadata in intervals/trials. Distinguishing fields include: num_barriers (value 0 on 32 trials = barrier-free straight reaches; value 9 on 68 trials = maze reaches with barriers), maze_id (9 distinct maze layouts, 8-12 trials each), trial_type, trial_version (0/1/2), num_targets (1 on 66 trials, 3 on 34 trials with distractor targets), per-trial barrier_pos (612x4 with barrier_pos_index), target_pos (168x2 with target_pos_index), and active_target. Timing fields include target_on_time, go_cue_time, move_onset_time, rt, delay, start_time, stop_time. All trials have success=True. The 'split' column marks 75 train / 25 val within this file. These layout/geometry fields let a straight-versus-curved reach-context label and the obstacle/trajectory-demand dimensions be defined independently of the neural covariance data (num_barriers / maze_id / barrier geometry), and provide movement epoch anchors (go cue, move onset) for both variants.
  - Limitation: Curvature/straightness is inferred here only from num_barriers and maze layout metadata; an explicit trajectory-curvature label must be derived at execution from kinematics or barrier geometry, not from neural data.
  - Limitation: Per-condition trial counts are small (roughly 8-12 per maze layout), constraining within-condition covariance estimation.
  - Limitation: Metadata-level inspection only; no per-trial trajectories analyzed.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Full simultaneously recorded M1+PMd population (142 sorted units: 72 PMd, 70 M1) from single subject sub-Jenkins, single session (100 train trials; 75 train / 25 val split column). Inference is within-subject/within-session; region-stratified M1-vs-PMd analyses are sensitivity checks per the Owner ruling. No cross-subject/cross-session/causal claims.
- Unit of observation: Per-trial binned population spike-count vector within the movement epoch (aligned to move onset).
- Unit of inference: Trial (and condition) within the single session; dependence handled by cross-validation and condition-aware resampling.
- Hierarchy and dependence: Trials are nested within maze layouts/conditions with repeated observations; covariance and subspace estimation use disjoint trial folds, and reliability is assessed with condition-aware split-half and bootstrap resampling.
- Validation: Synthetic method-recovery on populations with known aligned-versus-magnitude structure to confirm the alignment estimator and the magnitude control before touching data; cross-validated subspace estimation; split-half covariance reliability gating.
- Split strategy: Leakage-safe nested cross-validation: movement subspace and covariance estimated on disjoint trial folds; the benchmark test file (no behavior) is never used for behavioral outcomes.
- Claim ceiling: associational

**Analysis strategy**

1. Bin spike counts within a prespecified movement epoch and build per-trial population activity; remove condition means to obtain trial-to-trial residuals and also retain across-condition structure.
2. On held-out folds, characterize an independent movement-representation subspace by mapping population activity to hand position/velocity (e.g., cross-validated reduced-rank/regression or kinematic-PSTH PCA), never using the covariance to be tested.
3. Estimate population co-variability with a shrinkage covariance estimator; decompose it into components aligned with versus orthogonal to the movement subspace and compute an alignment index.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Alignment of co-variability with a movement-irrelevant or random subspace; trial-label-shuffled covariance.
- Positive controls: Recovery of known velocity-tuned/movement-encoding directions that the alignment method should detect.
- Alternative explanations: Aggregate variability magnitude alone explains predictive differences.; Estimated alignment reflects limited sampling or dimensionality-estimation error.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject/single session; ~100 trials; no cross-subject or causal generalization.
- Cross-validated prediction is an analysis method, not a causal claim about co-variability.
- Planning evidence is not a scientific result.

**Why the plan serves the question**

It preserves the movement-representation alignment contrast, pits structural alignment against aggregate magnitude with an independent reference and circularity controls, and reports honestly within the dataset's within-session reliability limits.

**Before any later execution**

- Unresolved planning decisions: Bin width, movement-epoch window, shrinkage estimator, and alignment-index definition to be prespecified before execution.

### Scientific stakes

**Discriminating observation**

Movement prediction varies with the orientation of co-variability relative to independently characterized movement-relevant structure after accounting for aggregate magnitude.

**What possible outcomes would mean**

- Positive pattern: A positive result would support structural alignment as more informative than global variability magnitude.
- Negative pattern: A negative result would favor magnitude-based or alternative non-alignment accounts.
- Null or ambiguous pattern: A null result would leave open whether alignment is irrelevant or too uncertain to estimate in this setting.

## Variant 2: Residual context-alignment branch

### Why it matters

This distinguishes covariance structure specifically related to maze or trajectory demands from preserved movement-related covariance that could recur across behaviors without encoding reach context.

### Original and refined question

**Original Question Scientist proposal**

Is population co-variability selectively aligned with dimensions that distinguish straight from curved reach contexts, beyond alignment with generic movement dimensions?

**Post-novelty revised proposal**

After accounting for matched generic temporal, kinematic, and, where relevant, muscle-related structure, does motor-population co-variability retain selective alignment with independently defined dimensions of straight-versus-curved reach demands and improve prediction of reach context?

**Reviewed refined question**

After accounting for matched generic temporal, kinematic, and aggregate-magnitude structure, does M1+PMd co-variability retain reliable residual alignment with independently defined straight-versus-curved trajectory demands and improve prediction of reach context?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If trial-level straight and curved contexts, behavioral trajectories, and repeated population observations are available, they may support comparison of independently specified context-demand dimensions against generic reference dimensions spanning matched temporal trajectory structure, kinematics, and muscle-related structure where relevant measurements permit.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** Dataset MC_Maze_Small (DANDI:000140 v0.220113.0408) contains sorted-unit spiking and behavioral data from ONE rhesus macaque (sub-Jenkins) performing a delayed center-out reaching task with obstructing barriers forming a maze, producing a mix of straight and curved reaches. Neural activity was recorded from electrode arrays in primary motor cortex (M1) and dorsal premotor cortex (PMd). Cursor, hand, and eye position were recorded; hand velocity was computed offline. The public release is limited to 100 train and 100 test trials. This establishes the behavioral task (delayed maze reaching, straight vs curved), the recorded regions (M1 + PMd), and the single-subject scope relevant to both variants' population.
  - Limitation: Single subject, single session; no across-animal or across-session replication is possible.
  - Limitation: Documentation-level fact; trial-level coverage and reliability verified separately.
  - Limitation: Planning-only inspection; no scientific outcome computed.
- **Unverified planning evidence:** The analyzable surface with both neural and behavioral data is the train file: 100 trials (75 train / 25 val by the split column), 142 units. Straight (num_barriers=0) vs curved (num_barriers=9) split is 32 vs 68; the 9 maze layouts have only 8-12 trials each. The separate test file (sub-...desc-test) has 100 trials, 107 held-in units, and NO processing/behavior module (held out for the NLB benchmark). This bounds covariance-reliability: estimating a 142-unit covariance (or region-stratified covariance) from ~100 trials, or within small per-condition subsets, is sampling-limited and requires shrinkage, cross-validation, and explicit split-half / bootstrap reliability estimation before any alignment or residual-alignment claim. It directly motivates each variant's requirement to distinguish a genuinely shared / low-alignment covariance structure from failure to estimate covariance reliably.
  - Limitation: Small single-session sample caps the claim ceiling at descriptive/associational and makes an 'inconclusive due to unreliable estimation' outcome a real possibility that the plan must be able to declare honestly.
  - Limitation: Test-file behavioral outcomes are benchmark held-out and must not be inspected; all planning uses only the train-file behavior.
  - Limitation: Counting-level metadata inspection only; no covariance or reliability statistics computed.
- **Unverified planning evidence:** The train file has 100 trials with rich, neural-independent condition metadata in intervals/trials. Distinguishing fields include: num_barriers (value 0 on 32 trials = barrier-free straight reaches; value 9 on 68 trials = maze reaches with barriers), maze_id (9 distinct maze layouts, 8-12 trials each), trial_type, trial_version (0/1/2), num_targets (1 on 66 trials, 3 on 34 trials with distractor targets), per-trial barrier_pos (612x4 with barrier_pos_index), target_pos (168x2 with target_pos_index), and active_target. Timing fields include target_on_time, go_cue_time, move_onset_time, rt, delay, start_time, stop_time. All trials have success=True. The 'split' column marks 75 train / 25 val within this file. These layout/geometry fields let a straight-versus-curved reach-context label and the obstacle/trajectory-demand dimensions be defined independently of the neural covariance data (num_barriers / maze_id / barrier geometry), and provide movement epoch anchors (go cue, move onset) for both variants.
  - Limitation: Curvature/straightness is inferred here only from num_barriers and maze layout metadata; an explicit trajectory-curvature label must be derived at execution from kinematics or barrier geometry, not from neural data.
  - Limitation: Per-condition trial counts are small (roughly 8-12 per maze layout), constraining within-condition covariance estimation.
  - Limitation: Metadata-level inspection only; no per-trial trajectories analyzed.
- 3 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Full simultaneously recorded M1+PMd population (142 units) from single subject sub-Jenkins, single session; straight (num_barriers=0, 32 trials) versus curved (num_barriers=9, 68 trials) reaches across 9 maze layouts. Within-subject/within-session inference with region-stratified sensitivity; no cross-subject/cross-session/causal claims.
- Unit of observation: Per-trial binned population spike-count vector within matched temporal windows, labeled by independently defined straight-versus-curved context.
- Unit of inference: Trial (and maze condition) within the single session; dependence handled by condition-aware cross-validation and permutation.
- Hierarchy and dependence: Trials nested within maze layouts and context; matched temporal/kinematic reference is fit and residualized on disjoint folds, and context prediction is cross-validated across trials with condition-aware splits to prevent layout leakage.
- Validation: Synthetic method-recovery distinguishing a genuinely shared (preserved-manifold) covariance from an unreliably estimated context-selective covariance, to calibrate the reliability threshold and confirm the residualization removes only generic structure; permutation of context labels as a null.
- Split strategy: Leakage-safe condition-aware cross-validation: reference fitting, residualization, and context decoding on disjoint trial/layout folds; benchmark test outcomes never inspected.
- Claim ceiling: associational

**Analysis strategy**

1. Define straight-versus-curved context and trajectory-demand dimensions from num_barriers, maze layout, and barrier/target geometry (and kinematic curvature), independently of the neural covariance.
2. Construct a matched generic reference space from temporal (time-in-trial) and kinematic (hand position/velocity) structure and aggregate covariance magnitude, matched across contexts; regress this reference out of population activity/covariance.
3. Test whether residual co-variability retains reliable alignment with the independent context dimensions and whether residual population activity improves cross-validated straight-versus-curved context classification beyond the generic reference and magnitude.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Context relabeled by a random split matched on movement magnitude; kinematic-only proxy standing in for the absent muscle reference.
- Positive controls: A synthetic residual context mode injected into the population that the pipeline should recover after generic-mode removal.
- Alternative explanations: Apparent context alignment attributable to generic temporal trajectory structure, kinematics, movement magnitude, or (unmeasured) muscle-related dimensions.; Covariance modes are reliably preserved across straight and curved reaches with no residual context organization.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- No EMG: muscle-mapping confound controlled only indirectly via kinematics; this is a documented limitation, not a resolved control.
- Small per-condition counts and a single session cap reliability; an inconclusive outcome is a genuine possibility distinct from a preserved-manifold null.
- Within-subject descriptive/associational only; context dimensions defined independently of neural covariance; planning evidence is not a scientific result.

**Why the plan serves the question**

It preserves the residual context-selective alignment contrast, separates it from generic temporal/kinematic/magnitude structure, defines context independently of neural data, and honestly gates on reliability, while documenting the unavailable muscle comparator as a limitation rather than silently dropping the control.

**Before any later execution**

- Unresolved planning decisions: Exact definition of the straight-versus-curved demand dimensions and the matched reference basis, and the reliability threshold for declaring an inconclusive result, to be prespecified before execution.
- Required future skills: A residualization-plus-reliability-gated context-alignment executor skill that removes a matched generic reference space, estimates residual covariance alignment with independently defined context dimensions, and reports inconclusive when covariance reliability is unmet.

### Scientific stakes

**Discriminating observation**

Context dimensions defined independently of the neural covariance data from obstacle or trajectory requirements—not by overall movement magnitude—show reliable residual alignment with co-variability and improve straight-versus-curved context prediction after variance attributable to matched temporal trajectories, kinematics, aggregate covariance magnitude, and, where relevant, muscle-related reference dimensions is accounted for. Conversely, a reliably estimated covariance structure that remains shared across contexts and is captured by the generic reference space, without residual context alignment or prediction improvement, favors a preserved-manifold account; insufficient reliability makes that contrast inconclusive.

**What possible outcomes would mean**

- Positive pattern: Reliable residual alignment and incremental context prediction would support the interpretation that motor-population co-variability contains organization selective for straight-versus-curved trajectory demands beyond shared movement-related covariance.
- Negative pattern: If covariance modes are estimated reliably, remain shared across straight and curved reaches, and are explained by the specified generic reference space without residual context alignment or prediction improvement, the result would favor a generic preserved-manifold account over context-selective organization.
- Null or ambiguous pattern: If covariance orientation, shared-mode preservation, or residual alignment cannot be estimated reliably, the result would not distinguish a preserved-manifold account from undetected context-selective covariance.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve the protected alignment-versus-magnitude family tension, maintain distinct movement- and context-alignment contrasts, use neural-independent behavioral/context references, and appropriately limit inference to within-session descriptive/associational claims. Remaining choices are execution-stage prespecification locks, not deficiencies in the planning dossier.

Retained changes and locks:

- **Pre execution lock:** Before execution, prespecify the variant 1 binning/epoch, covariance-shrinkage estimator, and alignment-index definition.
- **Pre execution lock:** Before execution, prespecify the variant 2 straight-versus-curved trajectory-demand operationalization, matched temporal/kinematic reference basis, and reliability threshold governing an inconclusive outcome.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both active variants preserve the protected alignment-versus-magnitude tension via distinct, non-overlapping axes: v1 defines functional relevance by alignment with a continuous movement-representation subspace and pits it against aggregate covariance magnitude with leakage-safe cross-validation, positive/negative controls, and an honest within-session associational claim ceiling; v2 defines functional relevance by residual alignment with independently defined (geometry-based, non-neural) straight-versus-curved context dimensions after regressing out a matched generic temporal/kinematic/magnitude reference, with reliability gating so an unreliable-estimation outcome is not mistaken for a preserved-manifold null. The unavailable EMG comparator in v2 is disclosed as a documented interpretation limit under the invariant's 'where relevant' scoping rather than concealed or treated as fatal. Dataset grounding is concrete (unit counts, region assignment convention, trial/context metadata, kinematic sampling, sample-size constraints) and drawn only from the bounded evidence views. Neither variant overclaims beyond within-subject descriptive/associational inference. The two Owner-required changes are genuine pre-execution prespecification locks (binning/epoch/estimator/index definitions for v1; context operationalization, reference basis, and reliability threshold for v2) rather than scientific blockers, since the plan already supplies an independently referenced, circularity-controlled, reliability-gated design capable of answering each variant's protected question as currently specified.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
