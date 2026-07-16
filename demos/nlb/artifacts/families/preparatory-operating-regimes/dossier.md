# Preparatory population dynamics as operating regimes for movement

Tests whether preparatory dynamics set movement-specific operating conditions, separating trajectory-class boundary tests from trial-level behavioral-consequence tests.

## Scientific tension

Preparatory trajectories may establish movement-generating operating conditions, but descriptive dynamics could instead reflect elapsed time, impending movement, or behaviorally irrelevant population variation.

## Question variants

### trajectory-class boundary test

Do straight and curved reaches recruit distinct preparatory population operating regimes, or do they diverge only after movement begins?

Why it matters: Locating the divergence at preparation versus execution constrains dynamical accounts without asserting a particular circuit mechanism.

Distinctive focus: This variant asks when straight and curved reach regimes diverge at the population level; it does not require trial-level variation in movement quality.

Conditional dataset leverage: Delayed straight and curved reaches may allow a later planner to compare when trajectory-class organization becomes distinguishable.

Discriminating observation: Reliable trajectory-class separation in preparatory population organization that anticipates later path differences would favor advance configuration; separation emerging only during movement would favor execution-driven divergence.

Competing explanations:
- Trajectory-specific operating regimes are established during preparation.
- A common preparatory regime branches only during execution.
- Apparent preparatory separation reflects subtle pre-movement behavior or timing differences.

### independent behavioral-consequence test

Does trial-to-trial proximity to a reach-specific preparatory population state predict subsequent movement trajectory more strongly than preparatory activity magnitude?

Why it matters: This variant demands an independent behavioral consequence and contrasts structural state with magnitude.

Distinctive focus: This variant makes a trial-level predictive claim about later movement and directly contrasts geometry with magnitude; the sibling tests the timing of condition-level divergence.

Conditional dataset leverage: Neural activity paired broadly with hand or cursor trajectories may allow later planning of trial-level predictive comparisons.

Discriminating observation: Out-of-sample trial-level prediction from independently defined geometric state that exceeds matched magnitude and behavioral controls would favor a structurally consequential preparatory state.

Competing explanations:
- Geometric proximity to a reach-specific preparatory state predicts the subsequent trajectory.
- Overall preparatory activity or generic readiness predicts behavior equally well.
- The relationship is induced by pre-movement behavioral differences or temporal autocorrelation.

## What the possible outcomes would mean

### trajectory-class boundary test

- Positive pattern: Preparatory divergence would support a predictive account in which upcoming reach geometry is configured before movement.
- Negative pattern: Reliable divergence confined to execution would weaken claims that preparation contains trajectory-specific operating regimes.
- Null or ambiguous pattern: Weak or temporally unstable separation would leave the onset of trajectory-specific organization unresolved.

### independent behavioral-consequence test

- Positive pattern: A specific predictive relationship would support the claim that preparatory geometry carries behaviorally relevant organization.
- Negative pattern: Prediction explained by magnitude or measured behavior would favor generic readiness or embodied-state accounts.
- Null or ambiguous pattern: No reliable prediction would leave open whether preparatory geometry is consequential or merely poorly estimated.

## Dataset evidence status

- Claim status: `unverified`
- Planner inspection records were retained, but their locators and digests do not by themselves prove the stated observations.
- Dataset leverage statements above remain hypotheses unless a retained, host-bound source supports them.

## Current disposition

- Shortlist: `shortlisted`
- Planning: `not_reached`
- Closure: `degraded`
- Authority: `provisional`
- Status note: Returned planning material could not be fully validated; a readable family dossier was retained with a validation warning.

## Retained products

The private run diagnostics, evidence identifiers, receipts, and audit sidecars are intentionally omitted from this public gallery. The scientific question and safely retained planning context remain below.

## Retained planning and review disposition

- The returned planning material could not be fully validated. The scientific question and any safely retained products remain available with a validation warning.

## Safely retained planner draft

The planner returned a complete-looking draft, but it did not pass strict typed validation and has not received scientific review. The scientific content below is a sanitized inspection copy: provenance identifiers are omitted, and no accepted-plan authority is implied.

### Family summary

Revised plan: both variants remain separately supported by the documented MC_Maze_Small delayed-reach release. Variant 2 now locks a leakage-safe held-out geometry predictor: every held-out trial is represented only by its preparatory neural vector, training-fold-fitted transforms, and its distances to every training-fold-defined reference state; its subsequent trajectory class, feature, and outcome cannot select or alter a reference. This is an operational safeguard, not a material change to either protected scientific contrast.

- Planner assessment label: `serves_question`

### Variant 1

- Planner-stated disposition: `accepted_requires_new_skill`
- Planner summary: The documented delayed maze-reach task supports a condition-level test of whether behaviorally defined straight and curved reaches become separable in preparation or only after movement. It remains distinct from the trial-level prediction question.

#### Refined question

Using behaviorally defined straight and curved reaches, does population organization become reliably distinguishable in a prespecified preparatory epoch before movement onset, or only in matched execution epochs?

#### Population and scope

Sorted M1 and PMd units in behaviorally valid train trials from the single documented MC_Maze_Small macaque session. Region-stratified sensitivity analysis requires the documented unit-ID region correction.

#### Unit of observation

A trial-time-bin population vector with trajectory class assigned from the later behavioral path and never from neural features.

#### Unit of inference

A trial, with trial-respecting resampling rather than time-bin independence.

#### Hierarchy and dependence

Time bins are nested in trials and units are repeatedly observed within one session; use trial-level summaries or trial-clustered inference and report one biological session.

#### Validation strategy

Fit normalization, dimensionality reduction, and classifiers within trial-grouped training folds; use label permutation, time-shift, and synthetic recovery checks. A preparatory interpretation requires fold stability and persistence after behavioral adjustment.

#### Split strategy

Assign whole trials to balanced folds where possible and never use the held-out test asset to choose windows, curvature thresholds, or models.

#### Planner-stated claim ceiling (not yet schema-validated)

predictive

#### Resource estimate

A later executor needs train-NWB schema extraction, event-aligned neural-behavioral assembly, and trial-clustered decoding; data scale is modest.

#### Why this plan serves the question

The plan preserves the condition-level timing contrast between advance configuration and execution-driven divergence without substituting trial-quality prediction.

#### Data sources

1. The documented local train NWB asset supplies sorted spiking and aligned hand or cursor behavior for delayed reaches with straight and curved paths.
   - Expected grain: Repeated trial-by-time-bin population observations joined to trial-level behavior and event timing.
   - Required variables: Sorted unit spike times or binned spike counts.; Trial boundaries plus go-cue or equivalent preparatory timing.; Behavioral movement-onset timing, position, velocity, and pre-movement displacement.
   - Limitations: Exact field names and usable coverage require later train-NWB schema extraction.; The documented release has 100 train trials in one subject.

#### Analysis strategy

- Before neural analysis, define straight and curved classes from movement paths by a fixed curvature or path-efficiency rule, blind to neural features.
- Define preparatory and execution windows from prespecified event and velocity criteria; exclude or label detectable pre-movement displacement.
- Estimate balanced, trial-grouped cross-validated class discriminability over time, separately for preparation and execution.
- Adjust or stratify for reaction time, target geometry, path length, speed, and pre-movement kinematics; repeat regional analyses only after the documented correction.

#### Candidate estimands

- Cross-validated difference in trajectory-class discriminability between prespecified preparatory and execution epochs.
- Earliest stability-defined discriminability relative to movement onset, interpreted as a descriptive temporal boundary.

#### Diagnostics

- Trial and class counts after each exclusion.
- Event-alignment completeness and preparatory-window duration.
- Covariate overlap and foldwise discriminability stability.

#### Negative controls

- Permuted trajectory labels within prespecified target or timing strata.
- A pre-cue baseline window.

#### Positive controls

- Movement-epoch trajectory-class separation as a structural assay check, not evidence for preparation.

#### Alternative explanations

- Target layout, path length, reaction time, or speed drives class separation.
- Covert pre-movement behavior or smoothing and leakage produce apparent preparation.

#### Predicted result patterns

- Stable preparatory separation after controls would favor advance trajectory-specific configuration.
- Separation restricted to execution would favor execution-driven divergence and weaken the preparatory-regime interpretation.

#### Interpretation limits

- This observational single-session analysis cannot establish that neural-state intervention would change movement.
- Planning evidence is not a scientific result.

#### Required new skills

- NWB train-asset schema extraction and event-aligned neural-behavioral assembly.
- Leakage-safe population decoding with trial-clustered resampling.

#### Unresolved decisions

- Exact event columns, valid-trial flags, behaviorally blind curvature threshold, and minimum balanced class count.

### Variant 2

- Planner-stated disposition: `accepted_requires_new_skill`
- Planner summary: The documented paired neural and hand/cursor recordings support a trial-level, out-of-sample geometry-versus-magnitude comparison. The revised geometry feature is a complete fold-local distance vector and never uses a held-out behavioral outcome to choose a reach-specific state.

#### Refined question

On held-out train trials, does a leakage-safe preparatory geometry feature predict a neural-independent subsequent trajectory feature more strongly than matched preparatory activity magnitude and readiness or behavioral controls?

#### Population and scope

Behaviorally valid train trials from the single documented MC_Maze_Small macaque session, using sorted M1 and PMd units and hand or cursor trajectories. The target is within-session trial-level prediction, not population-wide generalization.

#### Unit of observation

A held-out trial's preparatory population vector transformed only by training-fold-fitted operations, paired with a later behavior-only trajectory outcome used only for scoring.

#### Unit of inference

A held-out trial within the session, with uncertainty summarized by trial-level resampling.

#### Hierarchy and dependence

Each trial contributes one neural feature vector; keep trials intact in folds and assess temporal dependence through blocked or forward-chaining sensitivity analyses.

#### Validation strategy

Use nested trial-grouped validation. Reference-state learning, reference ordering, scaling, dimensionality reduction, any distance summary, and hyperparameter selection are fit only within the relevant training partition. Use outcome permutation within prespecified behavioral strata, time-blocked sensitivity analysis, and synthetic recovery tests to audit leakage and signal limitations.

#### Split strategy

Split by whole trial and reserve an untouched train-trial subset only if coverage permits; otherwise use repeated nested cross-validation. No held-out trial's behavioral trajectory, class, feature, or outcome may determine its geometry predictor, reference-state selection, preprocessing, or tuning. Never use the held-out test asset.

#### Planner-stated claim ceiling (not yet schema-validated)

predictive

#### Resource estimate

A later executor needs NWB trial assembly, behavior-only outcome engineering, fold-local reference-state construction, explicit held-out feature audit logging, and nested low-sample predictive validation.

#### Why this plan serves the question

The plan preserves the trial-level contrast between preparatory geometry and activity magnitude. It makes reach-specific geometry operational through training-defined references while preventing the held-out outcome from selecting the purported predictor, so the discriminating observation remains an honest out-of-sample prediction.

#### Data sources

1. The documented local train NWB asset supplies trial-aligned sorted spiking and behavioral trajectories for independent outcome construction and pre-movement controls.
   - Expected grain: One trial-level preparatory state summary joined to one independently computed later movement-trajectory outcome.
   - Required variables: Sorted unit spike times or binned counts in a prespecified preparatory epoch.; Trial timing and movement-onset alignment.; Hand or cursor position time series for later path outcome construction.; Hand velocity, pre-movement displacement, and available target descriptors.
   - Limitations: Documentation does not establish exact event columns or usable trial-level coverage.; The one-session, 100-train-trial release constrains model complexity and precision.

#### Analysis strategy

- Fix the behavior-only trajectory outcome before neural modeling, such as curvature, path efficiency, or deviation from a behavior-only template.
- Within each outer training fold, use only training trials and their behavior-only labels to define a prespecified finite set of reference states, fit scaling and any low-dimensional transform, and record every reference.
- For each held-out trial, transform only its preparatory neural vector with those training-fitted operations and compute its full ordered vector of distances to every recorded training-defined reference state. Do not select, weight, drop, or rename a reference using that held-out trial's subsequent trajectory class, trajectory feature, or outcome.
- Use that complete distance vector, or a training-fold-fixed outcome-agnostic summary of it, as the geometry predictor; compute magnitude from the same held-out preparatory neural data. Only after predictors are fixed may the held-out behavior-only outcome be revealed for scoring.
- Fit matched low-complexity models for geometry plus covariates, magnitude plus the same covariates, and combined geometry and magnitude; assess incremental out-of-sample value beyond reaction time, target descriptors, pre-movement displacement, and velocity.

#### Candidate estimands

- Cross-validated incremental predictive performance of the complete fold-local distance-vector geometry predictor over matched magnitude and behavioral-control models.
- Cross-validated conditional association between the pre-outcome fixed geometry feature and the independently defined trajectory feature.

#### Diagnostics

- Per-fold reference-state count, reference definition, distance-vector dimensionality, and verification that these precede held-out outcome access.
- Outcome coverage, missing behavioral samples, exclusions, and covariate overlap.
- Foldwise calibration, incremental performance variability, autocorrelation, and temporal drift sensitivity.

#### Negative controls

- Permute held-out behavioral outcomes within prespecified target and timing strata after geometry features are fixed.
- Use a non-corresponding trial's time-shifted neural feature while retaining behavioral covariates.

#### Positive controls

- Recover a known simulated geometry-outcome association through the identical fold-local feature-construction pipeline.

#### Alternative explanations

- Overall preparatory firing magnitude or generic readiness explains prediction.
- Pre-movement displacement, velocity, reaction time, or target geometry drives both neural state and later path.
- Outcome-dependent reference selection, temporal autocorrelation, or model flexibility inflates held-out performance.

#### Predicted result patterns

- Incremental out-of-sample prediction from the fixed geometry feature beyond magnitude and controls would support behaviorally relevant preparatory organization.
- Magnitude or behavioral controls matching geometry would favor generic readiness or embodied-state explanations.
- No stable incremental prediction would leave consequentiality of preparatory geometry unresolved.

#### Interpretation limits

- Out-of-sample prediction in one observational session is not evidence that changing preparatory state would change movement.
- The small train set requires low-complexity models and broad uncertainty reporting.
- The protected prediction claim concerns a pre-outcome fixed geometry representation, not an outcome-selected reach-specific distance.

#### Required new skills

- NWB train-asset schema extraction and neural-behavioral alignment.
- Fold-local preparatory-state geometry construction that emits complete reference-distance vectors and audits outcome isolation.

#### Unresolved decisions

- Exact behavior-only trajectory outcome, reference-state partition, event mapping, exclusion rules, and minimum usable trial count after schema and coverage checks.
- Whether available target descriptors support residualization or require stratified evaluation.

## Limitations

The returned planner material did not pass typed validation. It is retained only as provisional planning context; neither variant has accepted-plan authority.

## Diagnostics

A family-local validation warning closed this family as a readable soft terminal. No scientific rejection, accepted plan, bridge, or execution authority is implied.
This page preserves the generated scientific question; it is not a scientific finding or downstream authorization.

## Next action

Use the detailed reading guide and the retained scientific context before deciding whether a future run should revise or retry this family.
