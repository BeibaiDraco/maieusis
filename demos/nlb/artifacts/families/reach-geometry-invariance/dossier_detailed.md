# Invariant and reconfigured population geometry across reach demands — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether population organization across straight and curved reaching reflects a conserved motor scaffold or demand-specific reconfiguration, while separating regional and temporal forms of invariance.

The scientific tension is:

Similar behavior can coexist with neural remapping, but a static geometric resemblance cannot establish whether motor-cortical population organization is conserved, input-bound, or phase-specific.

## Variant 1: regional scope test of geometric invariance

### Why it matters

The question tests structure rather than activity magnitude and asks whether apparent geometric conservation has a regional boundary.

### Original and refined question

**Original Question Scientist proposal**

Is the population geometry distinguishing reach configurations conserved between straight and curved reaches within M1 and PMd, or selectively reconfigured in one region?

**Reviewed refined question**

Within the documented MC_Maze_Small training session, is independently estimated relational population geometry over matched reach configurations conserved between prespecified straight and curved reach classes in both M1 and PMd, or is conservation selectively absent in one region?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

The broad presence of M1 and PMd activity and straight and curved reaching may allow later planning of region-stratified geometric comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 is MC_Maze_Small: sorted-unit spiking and behavioral data from one macaque performing a delayed center-out reach task with obstructing barriers that produce straight and curved reaches; recordings are described as M1 and PMd, and cursor position, hand position, eye position, and hand velocity are provided. The release is limited to 100 train and 100 test trials.
  - Limitation: The narrative does not establish condition balance, trajectory classification thresholds, or reliability for a geometric analysis.
  - Limitation: The release has one subject and a small trial count, so conclusions must be session-specific and dependence-aware.
- **Unverified planning evidence:** For MC_Maze releases, the documented authoritative region rule is the first digit of each unit ID: 1 denotes PMd and 2 denotes M1. The note warns that raw stored M1 electrode indices need a +96 correction and must not be used alone to infer region. Its bounded train metadata summary reports 72 PMd and 70 M1 units.
  - Limitation: The note is a conversion caveat and bounded metadata summary, not a substitute for execution-time validation of the region parser.
  - Limitation: Region-stratified estimates remain limited by the single session and each region's available units.
- **Unverified planning evidence:** The train NWB schema exposes an intervals/trials table with start_time, stop_time, success, target, go_cue, and move_onset fields, plus documented hand-position, cursor-position, eye-position, and hand-velocity behavioral time series. These fields provide proposal-level anchors for prespecified preparation and execution windows and for kinematic trajectory classification.
  - Limitation: This schema inspection does not establish the numerical timing distribution, missingness, or usable trial counts for any condition.
  - Limitation: Preparation and execution windows must be prespecified from these event fields before neural geometry is inspected.

### Plan at a glance

- Population and scope: One macaque, one released training session, successful delayed center-out maze reaches, and region-stratified sorted units assigned by the documented unit-ID rule. The target population is the observed session, not macaques or motor cortex generally.
- Unit of observation: A successful trial represented by a prespecified neural feature vector from a fixed task-aligned window and its kinematic trajectory descriptors.
- Unit of inference: Repeated trials within this recording session, with inference interpreted as conditional on the session and not as independent-animal replication.
- Hierarchy and dependence: Trials are nested in one session and neural features are repeated measures over units; use trial-level resampling that preserves region and reach-class membership, never treat units as independent biological replicates, and report region-specific coverage.
- Validation: Validate the loader against NWB schema fields and the documented region-ID rule; run synthetic recovery tests showing that the geometry procedure distinguishes conserved geometry, rotation, and condition-specific remapping at the planned cell counts; require within-class split-half reliability before interpreting cross-class correspondence.
- Split strategy: Partition trials independently within each reach-class, target, and region stratum into balanced folds; derive configuration summaries in disjoint folds and reserve fold pairing for crossvalidation. All trajectory-class rules, window definitions, and feature preprocessing are fixed before neural geometry is viewed.
- Claim ceiling: predictive

**Analysis strategy**

1. Define straight and curved classes from hand-position trajectories using a prespecified curvature or path-efficiency rule, with target and endpoint matching before neural geometry is estimated.
2. Retain only reach-configuration cells with a prespecified minimum number of successful trials in each class and region; record excluded cells and do not relax thresholds after geometry is observed.
3. Within each region and reach class, estimate condition geometry from independently split trial halves using trial-averaged neural features and a cross-validated distance or correlation geometry.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permute trajectory-class labels within matched target and kinematic-coverage strata; correspondence should not exceed the constrained-label null.; Use shuffled configuration labels across split halves; a geometry-correspondence metric should collapse toward its null reference.
- Positive controls: Within the same trajectory class, independently estimated split-half geometry should exceed the shuffled-configuration control before cross-class conservation is interpreted.
- Alternative explanations: Unequal target, endpoint, speed, duration, or curvature sampling can mimic a trajectory-class geometry difference.; Different unit counts or region-assignment errors can mimic a PMd/M1 difference.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- This observational, one-session comparison cannot establish that trajectory demand causes a neural remapping or identify its mechanism.
- Behavioral matching reduces measured confounding but cannot remove unmeasured planning, feedback, or task-history differences.
- Planning evidence establishes data access and schema only; it contains no result from the proposed analysis.

**Why the plan serves the question**

The estimand directly compares independently estimated relational geometry across straight and curved reaches separately in PMd and M1, so it preserves the variant's regional conservation contrast rather than substituting a preparation-to-execution question or an activity-magnitude comparison.

**Before any later execution**

- Unresolved planning decisions: Choose and lock the curvature classifier, target/endpoint matching tolerance, neural analysis window, and minimum-cell reliability rule before neural geometry inspection.
- Required future skills: NWB-aware extraction of train trial metadata, behavioral kinematics, and sorted-unit features without accessing held-out outcomes.; Documented unit-ID based M1/PMd assignment with an electrode-index consistency check.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

Reliable preservation of independently estimated relational geometry across trajectory classes in both regions would favor a shared scaffold; selective preservation in one region would favor a regional boundary.

**What possible outcomes would mean**

- Positive pattern: Conservation in both regions would support the predictive claim that motor population organization generalizes across reach demands despite changes in activity patterns.
- Negative pattern: Reliable geometry specific to each trajectory class would argue that the organization is demand-bound rather than invariant.
- Null or ambiguous pattern: Indeterminate or unreliable geometry would leave conservation unresolved and shift attention to measurement stability and construct definition.

## Variant 2: temporal scope test of geometric invariance

### Why it matters

Temporal persistence would constrain theories linking preparatory state organization to movement generation without treating temporal continuity as causal proof.

### Original and refined question

**Original Question Scientist proposal**

Does reach-related relational geometry persist from preparation into movement execution, and is such temporal persistence shared by PMd and M1?

**Reviewed refined question**

Within the documented MC_Maze_Small training session, do independently estimated reach-configuration relationships persist from a prespecified preparation window to a prespecified execution window in PMd and M1, beyond each phase's reliability and measured movement covariation?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Delayed reaching and activity from PMd and M1 may permit later assessment of whether reach relationships are preserved across broad task phases.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 is MC_Maze_Small: sorted-unit spiking and behavioral data from one macaque performing a delayed center-out reach task with obstructing barriers that produce straight and curved reaches; recordings are described as M1 and PMd, and cursor position, hand position, eye position, and hand velocity are provided. The release is limited to 100 train and 100 test trials.
  - Limitation: The narrative does not establish condition balance, trajectory classification thresholds, or reliability for a geometric analysis.
  - Limitation: The release has one subject and a small trial count, so conclusions must be session-specific and dependence-aware.
- **Unverified planning evidence:** For MC_Maze releases, the documented authoritative region rule is the first digit of each unit ID: 1 denotes PMd and 2 denotes M1. The note warns that raw stored M1 electrode indices need a +96 correction and must not be used alone to infer region. Its bounded train metadata summary reports 72 PMd and 70 M1 units.
  - Limitation: The note is a conversion caveat and bounded metadata summary, not a substitute for execution-time validation of the region parser.
  - Limitation: Region-stratified estimates remain limited by the single session and each region's available units.
- **Unverified planning evidence:** The train NWB schema exposes an intervals/trials table with start_time, stop_time, success, target, go_cue, and move_onset fields, plus documented hand-position, cursor-position, eye-position, and hand-velocity behavioral time series. These fields provide proposal-level anchors for prespecified preparation and execution windows and for kinematic trajectory classification.
  - Limitation: This schema inspection does not establish the numerical timing distribution, missingness, or usable trial counts for any condition.
  - Limitation: Preparation and execution windows must be prespecified from these event fields before neural geometry is inspected.

### Plan at a glance

- Population and scope: One macaque, one released training session, successful delayed center-out maze reaches, and region-stratified sorted units assigned by the documented unit-ID rule. The analysis concerns within-session temporal correspondence, not a causal preparatory mechanism or a cross-animal generalization.
- Unit of observation: A successful trial represented by separate prespecified preparation and execution neural feature vectors, its event timestamps, and reach-configuration descriptors.
- Unit of inference: Repeated trials within this recording session, with PMd/M1 comparisons conditional on the recorded unit populations rather than independent regional samples.
- Hierarchy and dependence: Preparation and execution observations are paired within trials and repeated over units; split trials rather than phase samples, retain pairing only for covariate diagnostics, and perform resampling within target and region strata.
- Validation: Validate event extraction against the NWB trial schema and region extraction against the documented unit-ID rule; use synthetic method-recovery data to test known persistent, rotated, and phase-specific geometries under unequal phase reliability; require reliable within-phase geometry before interpreting cross-phase loss.
- Split strategy: Assign complete trials, not individual phase observations, to balanced folds within target and region strata. Build phase-specific geometries from disjoint folds, use matching fold pairs only for crossvalidation, and lock phase windows and all transformations before neural geometry is viewed.
- Claim ceiling: predictive

**Analysis strategy**

1. Prespecify a preparation window ending before move_onset and an execution window beginning at or after move_onset using go_cue, move_onset, start_time, and stop_time; exclude trials that cannot support both nonoverlapping windows.
2. Define repeated reach configurations from target and prespecified kinematic descriptors without using neural activity, then retain only configurations represented in both phase windows and each region.
3. Within each phase and region, estimate relational geometry from disjoint trial folds using trial-averaged neural features and a crossvalidated distance or correlation geometry.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Pair preparation geometry with execution geometry from shuffled configuration labels within target strata; correspondence should approach the constrained null.; Use a temporally unrelated or label-shuffled phase pairing as a phase-correspondence control while preserving trial counts.
- Positive controls: Within-preparation and within-execution split-half geometries should each exceed shuffled-configuration controls before their cross-phase relationship is interpreted.
- Alternative explanations: Stable target or kinematic differences can create cross-phase correspondence without a persistent neural scaffold.; Phase-specific signal-to-noise, window duration, or unit-feature scaling can create an apparent loss of correspondence.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Cross-phase correspondence is observational and cannot establish that preparatory activity causally produces execution activity.
- Measured kinematic controls cannot eliminate all feedback, control, attention, or task-history confounding.
- Planning evidence establishes phase-anchor availability only and contains no observed geometry result.

**Why the plan serves the question**

The estimand compares independently estimated reach relationships across preparation and execution within each region, directly preserving the temporal-persistence discriminating observation and keeping it separate from the sibling's straight-versus-curved comparison.

**Before any later execution**

- Unresolved planning decisions: Choose and lock the preparation/execution window boundaries, configuration labels, movement-covariate adjustment, and minimum phase-specific reliability rule before neural geometry inspection.
- Required future skills: NWB-aware extraction of train trial events, behavioral kinematics, and sorted-unit features without accessing held-out outcomes.; Documented unit-ID based M1/PMd assignment with an electrode-index consistency check.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

Cross-phase preservation of independently estimated reach relationships, beyond within-phase reliability and behavioral similarity, would favor a persistent scaffold; reliable phase-specific structures would favor reorganization.

**What possible outcomes would mean**

- Positive pattern: Temporal preservation would support a predictive account in which preparation establishes organization retained during execution.
- Negative pattern: A reliable loss or inversion of reach relationships would support phase-specific population codes.
- Null or ambiguous pattern: Weak or inconsistent cross-phase correspondence would prevent choosing between persistence and reorganization.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct protected contrasts and provide credible, session-scoped, observational geometry analyses with independent-fold estimation, reliability gates, matched or controlled behavioral structure, and appropriate indeterminate outcomes. Remaining choices are explicit pre-execution operational locks, not deficiencies in the planning dossier.

Retained changes and locks:

- **Pre execution lock:** Before execution, lock the straight/curved classifier, target/endpoint matching rule, neural-feature window and preprocessing, and coverage/reliability thresholds for the regional cross-trajectory geometry analysis.
- **Pre execution lock:** Before execution, lock nonoverlapping preparation and execution windows, trial eligibility, configuration labels, measured-kinematics control, and phase-specific reliability thresholds for the temporal-persistence analysis.
- **Pre execution lock:** Before execution, implement and validate the authoritative unit-ID region parser and its electrode-metadata consistency check.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variant plans preserve their distinct protected contrasts: variant-01 tests cross-trajectory (straight vs curved) regional conservation of relational geometry, and variant-02 tests preparation-to-execution temporal persistence with a regional comparison. Neither collapses into the other, respecting the family's forbidden semantic merges. Each plan is grounded in the bounded evidence views (task/region documentation, train trial-phase schema, unit-ID region rule), uses leakage-safe split-half/cross-validated geometry estimation, requires within-class/within-phase reliability before interpreting correspondence, and specifies constrained-label negative controls and synthetic…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
