# Selective population coupling between PMd and M1 — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Asks whether PMd–M1 relationships are organized around reach-relevant dimensions rather than generic shared activity, with separate behavioral-demand and temporal-progression variants.

The scientific tension is:

Cross-region association may reflect selective coordination of task-relevant dimensions, but it may instead arise from dominant local fluctuations, shared inputs, movement covariation, or generic predictability.

## Variant 1: task-dimension specificity test

### Why it matters

A specificity test would refine broad claims of interregional coordination without interpreting predictive alignment as causal transmission.

### Original and refined question

**Original Question Scientist proposal**

Are PMd–M1 population relationships selectively aligned with dimensions distinguishing straight from curved reaches, rather than with dominant local variability alone?

**Reviewed refined question**

Within train-only MC_Maze_Small trials, are PMd-M1 population correspondences stronger for independently defined straight-versus-curved reach-geometry dimensions than for matched high-variance local dimensions or behavioral shared-input controls?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Broadly joint M1 and PMd recordings and reach-geometry variation may support later planning of selective-alignment comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** For MC_Maze releases, the first digit of a unit ID is the authoritative region indicator: 1 denotes PMd and 2 denotes M1. Stored electrode indices for M1 require a documented plus-96 correction, so uncorrected units/electrodes metadata cannot establish PMd-only coverage.
  - Limitation: This is a conversion rule that must be implemented and validated against the pinned NWB schema before execution.
  - Limitation: The note reports bounded release-preparation metadata, not an analysis result.
- **Unverified planning evidence:** The pinned MC_Maze_Small release is a one-subject delayed center-out reaching dataset with obstructing barriers that produce straight and curved reaches; it documents sorted-unit recordings from M1 and PMd plus cursor, hand, and eye position and offline hand velocity. The release contains 100 train and 100 test trials.
  - Limitation: Documentation establishes dataset-level availability, not exact NWB field names, event timestamps, unit counts, or usable trial coverage.
  - Limitation: The described 100-test-trial portion must not be used for confirmation or target-outcome inspection during planning.
  - Limitation: The single-subject, scaled release limits population generalization and precision.

### Plan at a glance

- Population and scope: The documented scaled release from one rhesus macaque, restricted to train trials with valid jointly timed PMd and M1 units and complete behavioral trajectories; inference is within this recorded session, not a population-level or causal claim.
- Unit of observation: A predeclared time bin or trial-level neural summary within a behaviorally defined reach epoch.
- Unit of inference: Train trials, with blocked resampling at the trial level and no claim of independent animals.
- Hierarchy and dependence: Retain nesting of bins within trials and units within region; fit trial-blocked multilevel or regularized models and resample whole trials so bins and units are not treated as independent replicates.
- Validation: Before target testing, validate the NWB reader on schema names and region assignment, verify no unit or trial leakage across folds, and run synthetic recovery simulations showing that the estimator distinguishes injected geometry-specific cross-region structure from common behavioral drive.
- Split strategy: Use nested, trial-blocked cross-validation within train trials; fit geometry definitions, nuisance models, scaling, and dimensionality choices only in each training fold, then score the paired PMd-M1 correspondence in its held-out fold.
- Claim ceiling: associational

**Analysis strategy**

1. Use only training trials to compute one preregistered curvature or path-deviation score from hand trajectories and divide trials into straight and curved strata by a fixed, distribution-independent rule where feasible.
2. Define geometry-discriminating dimensions separately within each region using one training split, then estimate cross-region correspondence on held-out training trials or nested trial-blocked folds.
3. Compare geometry-dimension correspondence against rank- and dimension-matched local high-variance dimensions, and against models residualizing documented hand velocity, cursor position, eye position, and trial timing where available.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Trial-blocked pairing of PMd and M1 from different trials within matched geometry strata.; Rank- and dimension-matched local principal components that are not selected for reach geometry.
- Positive controls: Within-region decoding or discrimination of the train-only straight-versus-curved label on held-out folds, used only to establish that the independently defined focal dimensions carry the intended behavioral construct.
- Alternative explanations: Shared movement kinematics, cursor state, or eye behavior produces apparent regional alignment.; Higher signal variance or unit count in one region drives a correspondence difference.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Joint recordings and predictive correspondence cannot identify anatomical transmission, directionality, or causal coordination.
- One macaque and a 100-train-trial scaled release restrict generalization and may limit stable high-dimensional estimation.
- Geometry is operationalized from behavior and does not by itself distinguish motor planning from all correlated task variables.

**Why the plan serves the question**

It retains the variant's required contrast between reach-relevant geometry dimensions and dominant generic local variability, uses independent foldwise definitions to avoid circularity, and tests behavioral shared-drive alternatives without converting association into causation.

**Before any later execution**

- Unresolved planning decisions: Exact curvature threshold and reach epoch must be locked from train-only behavioral documentation before cross-region scoring.; If documented timing fields cannot identify a common reach epoch, retain trial-level behavioral summaries only and narrow the temporal resolution without changing the geometry contrast.
- Required future skills: Read-only NWB extraction with train/test guarding, event-field discovery, and documented MC_Maze unit-ID region assignment.; Nested trial-blocked cross-region representational-alignment workflow with synthetic method-recovery tests.

### Scientific stakes

**Discriminating observation**

Cross-region correspondence that is stronger for independently defined reach-geometry dimensions than for matched local or behavioral controls would favor selective organization.

**What possible outcomes would mean**

- Positive pattern: Selective alignment would support a predictive account of coordinated task-relevant population structure across PMd and M1.
- Negative pattern: Association confined to dominant generic modes would weaken a reach-specific coordination interpretation.
- Null or ambiguous pattern: Comparable or unstable focal and control relationships would leave selectivity unresolved.

## Variant 2: temporal reorganization test

### Why it matters

The temporal form tests whether selective organization is phase-dependent while preserving an associational, noncausal claim level.

### Original and refined question

**Original Question Scientist proposal**

Does the specificity of PMd–M1 population coordination change from reach preparation to execution, rather than remaining a stationary shared-activity relationship?

**Reviewed refined question**

Within train-only delayed MC_Maze_Small trials, does the geometry-specific PMd-M1 correspondence contrast differ between prespecified preparation and execution epochs more than matched generic and behavioral-control contrasts?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

The delayed-reaching narrative and two recorded regions may allow later planning of phase-resolved coordination tests.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** For MC_Maze releases, the first digit of a unit ID is the authoritative region indicator: 1 denotes PMd and 2 denotes M1. Stored electrode indices for M1 require a documented plus-96 correction, so uncorrected units/electrodes metadata cannot establish PMd-only coverage.
  - Limitation: This is a conversion rule that must be implemented and validated against the pinned NWB schema before execution.
  - Limitation: The note reports bounded release-preparation metadata, not an analysis result.
- **Unverified planning evidence:** The pinned MC_Maze_Small release is a one-subject delayed center-out reaching dataset with obstructing barriers that produce straight and curved reaches; it documents sorted-unit recordings from M1 and PMd plus cursor, hand, and eye position and offline hand velocity. The release contains 100 train and 100 test trials.
  - Limitation: Documentation establishes dataset-level availability, not exact NWB field names, event timestamps, unit counts, or usable trial coverage.
  - Limitation: The described 100-test-trial portion must not be used for confirmation or target-outcome inspection during planning.
  - Limitation: The single-subject, scaled release limits population generalization and precision.

### Plan at a glance

- Population and scope: The documented one-macaque delayed-reaching release, restricted to train trials with verified common preparation and execution timing, jointly timed corrected-region PMd/M1 units, and required behavioral data.
- Unit of observation: A time bin or trial-epoch neural summary in a verified preparation or execution interval.
- Unit of inference: Train trials contributing both verified epochs, analyzed with trial-blocked resampling; the recorded session is the sole biological session.
- Hierarchy and dependence: Model bins nested within epoch and trial, and units nested within corrected region; preserve paired within-trial epoch comparisons and resample whole trials.
- Validation: Validate event-field extraction and epoch alignment before analysis, test that time-label permutations destroy a known simulated phase effect while the estimator recovers it in synthetic data, and verify foldwise independence of dimension definition, nuisance fitting, and scoring.
- Split strategy: Use nested trial-blocked folds, keeping all epochs of a trial in one fold; derive epoch windows, feature scaling, dimensions, and nuisance adjustments in the training partition before scoring the held-out partition.
- Claim ceiling: associational

**Analysis strategy**

1. Before neural scoring, use only train-trial task-event fields to define fixed preparation and execution windows with matched duration or a prespecified duration-normalization rule.
2. Within each outer training fold and separately by epoch, define regional geometry-relevant dimensions from behavioral reach structure without using held-out PMd-M1 correspondence.
3. Estimate held-out PMd-M1 correspondence for focal dimensions and matched generic local dimensions in each epoch, then estimate the within-trial or foldwise epoch difference of these selectivity contrasts.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Cross-trial PMd-M1 pairings within the same epoch and matched behavioral strata.; Permuted preparation/execution labels within trial blocks, used to check that the phase estimator is not driven by unpaired sampling.
- Positive controls: Recovery of an injected synthetic phase-specific correspondence difference under the observed epoch lengths and trial-blocked split structure.
- Alternative explanations: Execution has higher movement variance, signal-to-noise, or unit availability than preparation.; Apparent phase differences reflect changing behavioral covariates rather than reorganized interregional specificity.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Observed phase dependence would be an association in one recorded session, not evidence of directional communication or causal reconfiguration.
- A delayed-task label does not guarantee that exact preparation and execution markers are available or comparable; the plan is conditional on schema verification.
- The scaled release may provide insufficient trials for fine temporal resolution, requiring predeclared coarser windows or an honest execution-stage stop.

**Why the plan serves the question**

It preserves the distinctive phase-dependent outcome rather than collapsing it into the sibling's aggregate geometry question, and it makes phase-specific signal quality and behavioral variance explicit competing explanations.

**Before any later execution**

- Unresolved planning decisions: Exact preparation and execution event names and duration-normalization rule await schema inspection.; If no common, behaviorally interpretable timing fields exist, this variant must stop rather than substitute an arbitrary temporal segmentation.
- Required future skills: Read-only NWB extraction with train/test guarding, event-timestamp verification, and documented MC_Maze unit-ID region assignment.; Paired trial-blocked phase-comparison workflow with phase-specific reliability and behavioral controls.

### Scientific stakes

**Discriminating observation**

A reliable change in which independently defined dimensions carry cross-region correspondence, beyond matched phase-specific controls, would favor dynamic reorganization.

**What possible outcomes would mean**

- Positive pattern: Phase-specific selectivity would support an associational account of dynamically reconfigured interregional coordination.
- Negative pattern: Stable correspondence dominated by the same generic modes would favor a stationary shared-activity account.
- Null or ambiguous pattern: Unreliable or non-specific phase differences would not distinguish reconfiguration from estimation noise.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct protected contrasts and support only within-session associational inference. The plans use train-only, trial-blocked evaluation, compare focal geometry-related structure against matched generic local structure, and address shared behavioral and reliability alternatives. Remaining choices are appropriate pre-execution locks rather than planning-stage scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Lock the geometry operationalization, reach epoch, and associated sensitivity settings using train-only behavioral information before cross-region scoring for the reach-dimension-specificity variant.
- **Pre execution lock:** Verify the NWB event fields and lock common preparation/execution windows and duration normalization before executing the temporal-reorganization variant; stop that variant if comparable interpretable epochs are unavailable.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variant plans preserve their distinct protected contrasts and support only within-session associational inference. The geometry variant contrasts independently defined straight-versus-curved reach dimensions against rank- and dimension-matched local high-variance dimensions plus behavioral shared-input controls, using nested trial-blocked cross-validation with foldwise definition to avoid circularity. The temporal variant preserves the phase-reorganization outcome as an epoch-difference-of-selectivity-contrasts, explicitly conditioning execution on schema verification of comparable preparation/execution epochs and stopping honestly if unavailable. Sibling separation is respected: the…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
