# Functional meaning of motor-manifold form — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Compares whether simple versus curved population-manifold structure is associated with reusable movement readout or context-specific trajectory organization.

The scientific tension is:

Motor population activity may occupy an approximately simple reusable structure or a nonlinear context-dependent manifold, but geometric complexity alone does not establish computational function.

## Variant 1: Frozen shared-geometry cross-context transfer branch

### Why it matters

This tests a stronger functional claim than low dimensionality or within-context decoding sufficiency: whether an explicitly defined neural geometry and readout can be frozen and reused to predict reach kinematics outside its training context while separating geometric invariance from decoder flexibility.

### Original and refined question

**Original Question Scientist proposal**

Does an approximately simple population geometry support reusable prediction of reach kinematics across trajectory contexts?

**Post-novelty revised proposal**

Does one prespecified common linear latent subspace, fixed coordinate system, and fixed neural-to-reach-kinematic mapping transfer without refitting from one trajectory context to an entirely held-out trajectory context, rather than merely benefiting from pooled or context-specific decoding?

**Reviewed refined question**

Does one prespecified common linear latent subspace, fixed coordinate system, and fixed linear neural-to-reach-kinematic mapping, fit within one entire trajectory context (straight or curved) and then frozen, retain practically meaningful predictive value for reach kinematics in the entirely held-out context, with no reliable advantage for capacity-matched nonlinear-global or context-specific alternatives?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the population and kinematic observations include separable trajectory contexts such as straight and curved reaches, they may permit training the shared object in one context and evaluating it without refitting in the other, potentially with reciprocal context holdouts. Later coverage checks must establish whether such held-out evaluations and uncertainty estimates are supported.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 (MC_Maze_Small, Churchland & Kaufman 2022) is a single rhesus macaque (sub-Jenkins), single-session delayed center-out reaching task with obstructing maze barriers producing "a variety of straight and curved reaches." Neural activity was recorded from M1 and PMd electrode arrays; cursor, hand, and eye position were recorded and hand velocity computed offline. The public release is deliberately limited to 100 train and 100 test trials and is distributed as part of the Neural Latents Benchmark '21. This establishes that the target constructs (motor-population activity, straight-vs-curved reach contexts, reach kinematics) are named data surfaces in this dataset, at the scale of one subject and one session.
  - Limitation: Documentation-level only; specific counts and stream shapes are verified in separate evidence records.
  - Limitation: Single subject, single session, small release: no cross-subject or cross-session generalization is available.
- **Unverified planning evidence:** The NLB test file (desc-test_ecephys) contains units and spike times but NO processing/behavior module and only a stripped trials table (move_onset_time, split, start_time, stop_time) with none of the behavioral or condition columns (no hand kinematics, no num_barriers, no maze_id, no target_pos). Behavioral outcomes for the 100 test trials are the benchmark's held-out targets and are not present locally. Consequently, all behavioral, context-label, and kinematic analyses for both variants must be confined to the 100-trial train file, and its provided train/val split (75/25) is the available basis for internal cross-validation.
  - Limitation: The official held-out test behavior cannot be used as an independent evaluation set here; generalization claims are limited to internal cross-validation within the 100 behavior-labeled train trials.
  - Limitation: This further tightens the effective sample and reinforces dependence-aware, leakage-safe resampling as the only sound evaluation route.
- **Unverified planning evidence:** The train file has 100 trials (all success=True), pre-split into 75 'train' and 25 'val' (intervals/trials/split). A prespecified reach-class / trajectory-context label is available as num_barriers: 32 trials with 0 barriers (straight center-out reaches) and 68 with 9 barriers (curved reaches around the maze). Nine distinct maze geometries (maze_id in {2,3,4,7,8,10,75,76,77}) each appear in BOTH a straight (num_barriers=0, ~2-4 trials each) and a curved (num_barriers=9, ~5-8 trials each) version, so trajectory identity (maze_id) is crossed with context (barrier class) and reach endpoints are shared across contexts. Trial event times (start/stop, target_on_time, go_cue_time, move_onset_time, rt, delay) and per-trial target_pos/target_pos_index/active_target are present. This supports: (a) defining an entire trajectory context (straight vs curved) to withhold for V1's out-of-context transfer test, and (b) holding out trajectory identities (maze_id) while matching/conditioning movement segments across contexts for V2's context-by-movement interaction test.
  - Limitation: Very small per-cell counts: straight reaches number only ~2-4 trials per maze (32 total), so context-transfer and interaction estimates will be low-powered and require dependence-aware resampling and explicit uncertainty propagation.
  - Limitation: Context is operationalized as barrier class (straight vs curved); alternative context definitions (e.g. maze geometry) are possible but the barrier-class reading matches the variant invariants' stated straight-vs-curved example.
- 3 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Single subject sub-Jenkins, single MC_Maze_Small session; 142 sorted M1+PMd units (72 PMd, 70 M1 by the documented unit-id convention, with the +96 M1 electrode correction); 100 behavior-labeled train trials, of which 32 are straight (num_barriers=0) and 68 curved (num_barriers=9), spanning 9 maze geometries. Population scope is this subject/session; no cross-subject claim is made.
- Unit of observation: One trial's movement-epoch binned population activity paired with its time-aligned reach kinematics.
- Unit of inference: The held-out trajectory context, evaluated over its constituent trials with dependence-aware resampling that respects maze-geometry grouping; inference is about context-level transfer, not individual time bins.
- Hierarchy and dependence: Trials are nested within maze geometry and within barrier context; resampling blocks by maze_id to avoid endpoint leakage, and repeated within-trial time bins are treated as dependent, not independent observations.
- Validation: A synthetic method-recovery probe generating data with a known reusable-vs-context-specific structure to confirm the pipeline recovers the correct verdict; capacity matching audited by equalizing latent dimension, regularization, and training information; dependence-aware block cross-validation over maze geometries.
- Split strategy: Leave-entire-context-out as the primary split; within the source context, maze-blocked cross-validation so that shared endpoints never straddle train and evaluation folds.
- Claim ceiling: predictive

**Analysis strategy**

1. Prespecify the movement epoch and bin width; bin the M1+PMd population and epoch the 2-D hand kinematics onto the same grid.
2. In the source context only, estimate a common linear latent subspace and fixed coordinate orientation (e.g. PCA/factor analysis) and a fixed linear latent-to-kinematic mapping; freeze all parameters.
3. Evaluate frozen transfer of reach kinematics in the entirely held-out context without any refitting, in both context directions (fit-straight/test-curved and fit-curved/test-straight).
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Context-label shuffling and time-shuffled kinematics, which should collapse any genuine transfer signal.
- Positive controls: Within-source-context decoding should recover established reach-velocity tuning, confirming the mapping is well posed before transfer is tested.
- Alternative explanations: Apparent transfer driven by kinematic similarity across contexts rather than reuse of the neural subspace.; Model differences driven by unmatched effective capacity or training information rather than geometric assumptions.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject and single session; no generalization beyond this animal/session is claimed.
- Small straight-context sample limits power; a null transfer advantage must not be over-read as proof of invariance.
- Observational decoding evidence supports a reusable-description claim, not a unique mechanism.

**Why the plan serves the question**

It performs exactly the frozen out-of-context invariance test the invariant protects, with decoder-capacity controls and context-specific alternatives, rather than a pooled global-vs-piecewise decoding comparison or a within-context sufficiency test.

**Before any later execution**

- Unresolved planning decisions: Movement-epoch window, bin width, and the prespecified practically-meaningful transfer margin and capacity budget.
- Required future skills: A frozen cross-context transfer executor that fits a common linear subspace, fixed coordinates, and a fixed neural-to-kinematic map in one context, freezes them, and evaluates held-out-context transfer against capacity-matched nonlinear-global and context-specific alternatives with prespecified margins.

### Scientific stakes

**Discriminating observation**

Trajectory contexts are defined in advance as distinct reach classes, such as straight versus curved trajectories, and an entire context—not task subphases or pooled trials—is withheld while the common linear subspace, its coordinates, and the linear reach-kinematic mapping are fitted in another context and then frozen. Support requires the held-out-context transfer contrast to meet a prespecified practically meaningful criterion while its uncertainty excludes an unacceptable transfer loss, and requires no reliable advantage for capacity-matched nonlinear global or context-specific alternatives under prespecified comparisons. Evidence against requires a context-specific or nonlinear alternative to exceed the frozen shared model by the prespecified meaningful margin with uncertainty supporting that advantage. If intervals span both support and opposition criteria, or capacity-matched model comparisons disagree, the observation is indeterminate.

**What possible outcomes would mean**

- Positive pattern: Successful frozen transfer of reach kinematics, without a meaningful advantage for matched nonlinear or context-specific alternatives, would support the common subspace, fixed coordinates, and fixed mapping as a useful reusable description of motor-population organization; it would not establish a unique mechanism.
- Negative pattern: A reproducible, meaningfully larger held-out-context advantage for nonlinear global or context-specific alternatives would weaken the claim that the prespecified simple shared geometry supports reusable reach-kinematic readout and would favor context dependence or a more flexible neural-output relationship.
- Null or ambiguous pattern: If uncertainty overlaps both the prespecified support and opposition regions, or matched comparisons cannot distinguish geometry from decoder capacity, the data would not determine whether the shared geometric object transfers; low dimensionality and within-context prediction would remain insufficient evidence for reuse.

## Variant 2: Nonlinear context-by-movement interaction branch

### Why it matters

Targeting a context-by-movement interaction makes nonlinear geometry scientifically informative only if it predicts how matched movements are represented differently across contexts after stronger shared-representation and kinematic alternatives are considered.

### Original and refined question

**Original Question Scientist proposal**

Does nonlinear population-manifold structure capture trajectory-context distinctions that are missed by a simple shared geometry?

**Post-novelty revised proposal**

For movement segments matched across global trajectory contexts on measured kinematics, including curvature, does nonlinear motor-population manifold form improve out-of-sample prediction of a context-by-movement interaction beyond a jointly fit shared geometry?

**Reviewed refined question**

For movement segments restricted to a prespecified demonstrated common-support region in measured kinematics (speed, direction, curvature) across straight-vs-curved trajectory contexts, does a constrained nonlinear motor-population manifold representation fit on held-in units improve reproducible out-of-sample prediction of a prespecified context-by-movement interaction - defined on the MEASURED activity of the disjoint held-out units - over a shared geometry fit jointly across contexts, when trajectory identities are held out and trajectory-library lookup and label-only prediction are excluded; and is the matched-context contrast treated as non-identifiable where common support is inadequate?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the available population and movement observations contain separable global trajectory contexts with sufficiently comparable movement segments, they may support a later comparison of nonlinear and jointly fit shared representations on held-out trajectory identities.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 (MC_Maze_Small, Churchland & Kaufman 2022) is a single rhesus macaque (sub-Jenkins), single-session delayed center-out reaching task with obstructing maze barriers producing "a variety of straight and curved reaches." Neural activity was recorded from M1 and PMd electrode arrays; cursor, hand, and eye position were recorded and hand velocity computed offline. The public release is deliberately limited to 100 train and 100 test trials and is distributed as part of the Neural Latents Benchmark '21. This establishes that the target constructs (motor-population activity, straight-vs-curved reach contexts, reach kinematics) are named data surfaces in this dataset, at the scale of one subject and one session.
  - Limitation: Documentation-level only; specific counts and stream shapes are verified in separate evidence records.
  - Limitation: Single subject, single session, small release: no cross-subject or cross-session generalization is available.
- **Unverified planning evidence:** The NLB test file (desc-test_ecephys) contains units and spike times but NO processing/behavior module and only a stripped trials table (move_onset_time, split, start_time, stop_time) with none of the behavioral or condition columns (no hand kinematics, no num_barriers, no maze_id, no target_pos). Behavioral outcomes for the 100 test trials are the benchmark's held-out targets and are not present locally. Consequently, all behavioral, context-label, and kinematic analyses for both variants must be confined to the 100-trial train file, and its provided train/val split (75/25) is the available basis for internal cross-validation.
  - Limitation: The official held-out test behavior cannot be used as an independent evaluation set here; generalization claims are limited to internal cross-validation within the 100 behavior-labeled train trials.
  - Limitation: This further tightens the effective sample and reinforces dependence-aware, leakage-safe resampling as the only sound evaluation route.
- **Unverified planning evidence:** The train file has 100 trials (all success=True), pre-split into 75 'train' and 25 'val' (intervals/trials/split). A prespecified reach-class / trajectory-context label is available as num_barriers: 32 trials with 0 barriers (straight center-out reaches) and 68 with 9 barriers (curved reaches around the maze). Nine distinct maze geometries (maze_id in {2,3,4,7,8,10,75,76,77}) each appear in BOTH a straight (num_barriers=0, ~2-4 trials each) and a curved (num_barriers=9, ~5-8 trials each) version, so trajectory identity (maze_id) is crossed with context (barrier class) and reach endpoints are shared across contexts. Trial event times (start/stop, target_on_time, go_cue_time, move_onset_time, rt, delay) and per-trial target_pos/target_pos_index/active_target are present. This supports: (a) defining an entire trajectory context (straight vs curved) to withhold for V1's out-of-context transfer test, and (b) holding out trajectory identities (maze_id) while matching/conditioning movement segments across contexts for V2's context-by-movement interaction test.
  - Limitation: Very small per-cell counts: straight reaches number only ~2-4 trials per maze (32 total), so context-transfer and interaction estimates will be low-powered and require dependence-aware resampling and explicit uncertainty propagation.
  - Limitation: Context is operationalized as barrier class (straight vs curved); alternative context definitions (e.g. maze geometry) are possible but the barrier-class reading matches the variant invariants' stated straight-vs-curved example.
- 4 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Single subject sub-Jenkins, single MC_Maze_Small session; 142 M1+PMd units partitioned by the NLB units/heldout flag into 107 held-in units (used to fit representations) and 35 disjoint held-out units (20 PMd, 15 M1) that supply the independent interaction outcome; 100 behavior-labeled train trials across 9 maze geometries, each appearing in both straight and curved contexts so that endpoint-matched segments differing in curvature exist across contexts. Population scope is this subject/session; no cross-subject claim is made.
- Unit of observation: One kinematically-characterized movement segment inside the demonstrated common-support region: its held-in binned population activity plus measured kinematics (speed, direction, curvature) as predictors, paired with the measured binned activity of the disjoint held-out units that forms the independent context-by-movement interaction outcome.
- Unit of inference: The held-out trajectory identity (maze_id) under leave-trajectory-out evaluation, with dependence-aware resampling; inference is about incremental predictive value of nonlinear form for the measured held-out-unit interaction, not individual bins.
- Hierarchy and dependence: Segments are nested within trajectory identity and context; leave-trajectory-identity-out folds prevent the same maze from informing both fitting and evaluation, blocking trajectory-library lookup; the held-in/held-out unit partition is fixed a priori so the interaction-outcome units never enter representation fitting.
- Validation: Synthetic method-recovery probe with known shared-only vs nonlinear-context-specific generative structure targeting held-out-unit prediction, to confirm the pipeline detects incremental nonlinear value only when present; a common-support adequacy audit that reports the retained segment fraction and triggers the non-identifiability declaration when overlap is inadequate; equivalence audits of covariate access; and dependence-aware block resampling for uncertainty.
- Split strategy: Leave-trajectory-identity-out (leave-maze-out) cross-validation, with the held-in/held-out unit partition fixed a priori (NLB units/heldout flag) so the interaction-outcome units never enter representation fitting, and context labels used only to define and evaluate the interaction, never as standalone predictors.
- Claim ceiling: predictive

**Analysis strategy**

1. Prespecify the movement-segment definition, the movement variable M (measured instantaneous hand velocity: speed and direction) and the conditioning covariate set (speed, direction, curvature).
2. BEFORE any geometry comparison, compute a prespecified common-support/overlap diagnostic on the conditioning covariates across straight vs curved contexts and RESTRICT all downstream comparison to segments inside the demonstrated common-support region; if overlap fails the prespecified adequacy threshold, declare the matched-context beyond-kinematics contrast non-identifiable/infeasible rather than adjusting by extrapolation.
3. Define the independent interaction outcome Y as the measured binned activity of the 35 disjoint held-out units, and the prespecified context-by-movement interaction estimand as the out-of-sample improvement in predicting Y from an M-by-context interaction encoding over M + context main effects, evaluated only on common-support segments.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Curvature/label-permutation and trajectory-identity-shuffled controls that should remove any spurious interaction gain.; A held-out-unit outcome permutation, which should collapse the measured interaction signal.
- Positive controls: A representation given genuine trajectory identity should recover a detectable interaction on the measured held-out-unit outcome, confirming sensitivity.
- Alternative explanations: Measured kinematics including curvature account for the apparent interaction, addressed by the net-of-kinematics comparison within common support.; Residual kinematic differences or extrapolation outside common support masquerade as nonlinear geometry, addressed by the prespecified common-support gate and non-identifiability declaration.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject and session; small matched-cell counts and only 35 held-out target units limit power and preclude strong absence claims.
- The beyond-kinematics interpretation holds only within the demonstrated common-support region; where overlap is inadequate the contrast is treated as non-identifiable rather than extrapolated.
- A null incremental gain weakens this specific interaction claim only, not context-dependent encoding in general.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

It isolates the incremental predictive value of nonlinear manifold form for a context-by-movement interaction defined on an independent MEASURED neural outcome (disjoint held-out units, Owner-accepted as faithful), among kinematically matched movements within demonstrated common support, with the exact controls the invariant requires, rather than testing generic decoding, the presence of context dependence, or nonlinearity by itself.

**Before any later execution**

- Unresolved planning decisions: Segment definition; the conditioning covariate set and the prespecified common-support adequacy threshold; the exact interaction-estimand parameterization on the held-out-unit outcome; and the nonlinear-model capacity budget.
- Required future skills: A constrained-nonlinear-vs-shared-geometry incremental-interaction executor that (a) enforces a prespecified common-support gate on the conditioning covariates across contexts and declares non-identifiability when overlap is inadequate, (b) predicts the measured activity of the disjoint held-out units as the independent interaction outcome, (c) holds out trajectory identities, excludes trajectory-library lookup and label-only prediction, equalizes covariate access, and quantifies incremental out-of-sample interaction prediction net of measured kinematics.

### Scientific stakes

**Discriminating observation**

Using global trajectory class as the separable context and comparing movement segments matched or conditioned on measured kinematics, a constrained nonlinear representation must improve reproducible out-of-sample prediction of a prespecified context-by-movement interaction over a shared-geometry representation fit jointly across contexts. The comparison must hold out trajectory identities, exclude trajectory-library lookup, give competing models equivalent access to permitted covariates, use context labels only to define and evaluate the contrast rather than as standalone predictive evidence, and test whether any gain remains beyond measured kinematics, including curvature.

**What possible outcomes would mean**

- Positive pattern: A reproducible incremental gain under these controls would support nonlinear manifold form as a predictive description of context-specific motor organization, while not establishing a unique mechanism.
- Negative pattern: If the nonlinear representation does not improve prediction and the jointly fit shared representation plus measured kinematics accounts for the same reliable context-by-movement effect, nonlinear form would not be needed to explain that effect. If neither account captures a reliable interaction, the result would weaken this specific interaction claim but would not establish an absence of context-dependent neural encoding more generally.
- Null or ambiguous pattern: If uncertainty, limited matching, or unstable geometric estimates prevent discrimination between the nonlinear and shared accounts, nonlinear structure would remain descriptively possible but its incremental context-specific meaning would remain unresolved.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan preserves both protected variant contrasts. V1 implements a genuinely frozen, bidirectional out-of-context transfer test with capacity-matched alternatives. V2 now defines its interaction on measured activity from disjoint held-out units and gates the beyond-kinematics comparison on demonstrated common support, with non-identifiability declared when overlap is inadequate. Remaining choices are pre-execution locks, not planning blockers.

Retained changes and locks:

- **Pre execution lock:** Before execution, prespecify V1's movement epoch, neural bin width, practically meaningful transfer margin, and capacity-matching budget for all compared models.
- **Pre execution lock:** Before execution, prespecify V2's segment definition, held-out-unit interaction parameterization, common-support adequacy threshold, and nonlinear-model capacity budget; apply the declared non-identifiability outcome if the support rule fails.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Round 1 resolves both round-0 scientific blockers for V2 without drifting scientific intent. The context-by-movement interaction is now defined on the measured activity of the 35 disjoint held-out units (heldout=True), fit exclusively from the 107 held-in units used for the shared/nonlinear representations, so the evaluation target is never derived from the representation being tested — resolving the circularity concern (an earlier reviewer-raised blocker). The beyond-kinematics comparison is now gated on a prespecified demonstrated common-support region in speed, direction, and curvature, with an explicit non-identifiability declaration when overlap is inadequate rather than relying on extrapolative adjustment — resolving the curvature-confound concern (an earlier reviewer-raised blocker). V1 is unchanged and remains a credible frozen, bidirectional out-of-context transfer test with capacity-matched alternatives, negative/positive controls, and dependence-aware resampling. The two variants remain cleanly separated: V1 tests whether a frozen linear subspace/mapping transfers to reach kinematics without refitting; V2 tests whether nonlinear form adds incremental predictive value for an independent neural interaction outcome within demonstrated common support, holding out trajectory identity. Neither forbidden semantic merge is committed. The remaining Owner-listed changes (epoch/bin width/margin/capacity budget for V1; segment definition/interaction parameterization/support threshold/capacity budget for V2) are bounded pre-execution implementation choices layered on an already-credible design, not scientific blockers, and are consistent with the product boundary for this planning stage.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
