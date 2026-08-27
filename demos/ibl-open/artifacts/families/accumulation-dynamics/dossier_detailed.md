# Persistent versus sequential population dynamics during evidence accumulation — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

A family asking whether decision-related population activity is better understood as persistent evidence representation or as choice-selective sequential progression, while separating representational form from behavioral relevance.

The scientific tension is:

Evidence accumulation is established as a useful account of perceptual decisions, but persistent and sequential neural implementations remain unresolved and may differ across brain populations.

## Variant 1: Direct representational-form adjudication variant

### Why it matters

This adjudication would determine whether cross-population differences concern distinct representational forms of evidence accumulation, rather than only different sequential evidence-transfer mechanisms, without treating descriptive population structure as causal or behaviorally predictive.

### Original and refined question

**Original Question Scientist proposal**

Across brain populations engaged during decision formation, is accumulated evidence expressed predominantly through persistent population states or through choice-selective sequential trajectories?

**Post-novelty revised proposal**

When persistent evidence-conditioned states and choice-selective sequences are compared directly at the same task and population level, do decision-engaged populations differ among persistent, sequential, and mixed or scale-dependent representational organizations after sensory-locked timing, choice commitment, and overt movement activity are separated from evidence-carrying dynamics?

**Reviewed refined question**

Across eligible BWM ephys insertion-by-region populations in the visual contrast decision task, do evidence-conditioned pre-movement population dynamics meet symmetric, predeclared criteria for persistent, sequential, mixed, or scale-dependent organization after sensory timing and commitment or movement structure are separated without removing signed evidence?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the public resource contains sufficiently comparable task-aligned neural, sensory, choice, and movement information across decision-engaged populations, it may support a later direct comparison of persistent and sequential evidence organization under common definitions; exact coverage and suitability remain to be established.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavior trial table has the same eid and trial_id keys and the same task timing, contrast, choice, and response fields as the ephys trial table. Trial behavior features provide signed_contrast, choice_label, reaction_time, and movement_time; wheel features provide movement onset, peak, direction, amplitude, and velocity; DLC and event-aligned behavior features provide camera and event-aligned movement summaries.
  - Limitation: The inspection does not establish complete wheel or camera coverage for every ephys trial.
  - Limitation: No behavioral prediction, response-time distribution, or neural feature was inspected.
- **Unverified planning evidence:** The ephys release contains 295920 trial records with contrastLeft, contrastRight, stimOn_times, goCue_times, firstMovement_times, response_times, choice, bwm_include, and feedback fields; 75395 unit records carry insertion, session, quality-label, firing-rate, and atlas/BERYL region fields; insertion metadata includes trial and good-unit counts; and event records are keyed to session and trial.
  - Limitation: Counts are source metadata and do not demonstrate that every region or insertion satisfies a future eligibility rule.
  - Limitation: No neural-behavior association, population-dynamics estimate, or target-outcome diagnostic was calculated.
- **Unverified planning evidence:** The BWM behavior schema provides trials keyed by eid and trial_id, trial-level behavior features, wheel-trial features, DLC-trial features, event-aligned behavior features, movement-state epochs, and quiescence-state epochs. These surfaces permit documented session-trial joins and predecision movement covariates.
  - Limitation: Feature availability and coverage must be checked after the neural inclusion set is fixed.
  - Limitation: Compressed feature summaries are movement controls and do not by themselves establish full kinematic equivalence.
- 1 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Eligible BWM ephys insertion-by-region populations with quality-filtered units and bwm_include trials, analyzed in commensurate fixed stimulus-to-pre-movement windows. No claim is made for regions or sessions that fail prespecified structural coverage and overlap criteria.
- Unit of observation: Trial-by-time-bin population activity within one eligible insertion-by-region population.
- Unit of inference: Population estimates replicated across eligible insertion-by-region populations, sessions, and subjects; trials and individual units are not independent population replicates.
- Hierarchy and dependence: Fit each population separately; summarize classifications with hierarchical session and subject structure and use clustered resampling plus leave-session and leave-subject-out replication checks.
- Validation: Before target classification, verify spike-time decoding on synthetic delta-tick fixtures, key uniqueness, event alignment, joint-model recovery of injected signed-evidence plus nuisance signals, and failure of classification under signed-evidence-label permutation or unrecoverable E-versus-N overlap.
- Split strategy: For stability, split trials within session while preserving signed-contrast and choice strata; repeat with leave-session-out and leave-subject-out replication. Choice and response outcomes are never used to select form criteria, nuisance terms, thresholds, windows, populations, or scales.
- Claim ceiling: descriptive

**Analysis strategy**

1. Decode spike shards and construct a fixed stimulus-to-pre-movement neural window. Include only trials for which the full fixed window precedes first movement; censor all later bins.
2. Predeclare a joint population model with a protected signed-evidence block E: signed contrast and signed-contrast-by-time basis functions. Estimate E jointly with a nuisance block N containing time-from-stimulus and go-cue basis functions, unsigned contrast or visual side terms, trial timing offsets, and commitment or movement covariates aligned to their documented times. Do not residualize, regress out, permute, or threshold signed contrast before fitting E.
3. Define the candidate evidence-conditioned trajectory from the fitted E block at common reference nuisance values, and define the nuisance-adjusted residual only as observed activity minus the fitted N block while retaining the fitted E block. Assess persistence and sequentiality on the retained evidence-conditioned component, not on a residual from a model that has removed E.
4. 3 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permute signed-contrast labels within session before fitting the protected evidence block.; Apply the same machinery to post-movement windows only as an exclusionary motor-structure control, never as evidence-carrying dynamics.
- Positive controls: Synthetic injected persistent and ordered-sequence evidence components combined with correlated sensory and movement nuisance components.; Recovery of documented stimulus-locked alignment before joint nuisance separation.
- Alternative explanations: Sensory-locked latency differences can mimic sequences.; Choice commitment or movement preparation can create orderly turnover.; plus 3 additional item(s) in the complete dossier

**Interpretation limits**

- Observational recordings cannot establish causal evidence transfer or a circuit mechanism.
- The joint model separates modeled structure but cannot prove complete removal of sensory, commitment, or motor confounding.
- Results would concern the documented visual-contrast task and eligible recorded populations only.

**Why the plan serves the question**

It directly adjudicates representational form at the same population and task level, retains mixed and scale-dependent outcomes, and treats signed evidence as the estimand while explicitly accounting for timing, commitment, and movement alternatives. This is not a behavioral-prediction analysis.

**Before any later execution**

- Unresolved planning decisions: Lock structural eligibility and E-versus-N overlap thresholds using non-outcome metadata and synthetic recovery only.; Select one primary temporal scale and a bounded secondary scale grid before target classification.
- Required future skills: Decode BWM delta-tick blosc spike shards into bounded trial-aligned counts.; Fit evidence-preserving joint nuisance models and matched persistence or sequential population-dynamics signatures with hierarchical stability assessment.

### Scientific stakes

**Discriminating observation**

At the same population and task level, persistent organization would receive positive support when graded evidence remains represented by a sustained evidence-conditioned population state without requiring orderly neuronal turnover; sequential organization would receive positive support when graded evidence is carried through reproducible choice-selective state progression with orderly turnover. These assignments must remain after sensory-locked temporal structure, choice-commitment activity, and overt movement-related activity are separated from the candidate evidence component. A population would be classified as mixed or scale-dependent, rather than forced into either category, when both forms retain support in distinct subpopulations or temporal scales. Cross-population heterogeneity would require reproducible differences among these representational-form outcomes, not merely regional compatibility with different sequential models.

**What possible outcomes would mean**

- Positive pattern: Reproducible population differences that include persistent versus sequential organization, or principled mixed or scale-dependent cases, after the stated separations would support heterogeneity in the representational form of evidence accumulation beyond regional differences among sequential candidate mechanisms.
- Negative pattern: If populations consistently support only one representational form after the stated separations, the proposed cross-population representational heterogeneity would be weakened even if evidence tuning differs by region; uniform sequential support would favor focusing on distinctions among sequential mechanisms, whereas uniform persistent support would challenge a broad sequential-transfer account.
- Null or ambiguous pattern: If neither form receives stable support, or if assignments change with reasonable temporal or population scale without a reproducible mixed structure, the recordings would not adjudicate persistent versus sequential organization and the representational taxonomy would remain unresolved.

## Variant 2: Matched incremental behavioral-prediction variant

### Why it matters

A matched predictive comparison would distinguish temporal form from behavioral relevance and clarify whether persistent or sequential organization is the more consequential description of decision formation, without treating prediction as evidence of causality or a specific circuit mechanism.

### Original and refined question

**Original Question Scientist proposal**

Do persistent and sequential population signatures differ in how they predict trial-to-trial choice and response-time variation during evidence accumulation?

**Post-novelty revised proposal**

When persistent and sequential signatures are defined within the same population using common quantitative criteria, which signature provides greater out-of-sample incremental prediction of trial-level choice and response time during the same evidence-accumulation task, conditional on matched stimulus and movement-related information?

**Reviewed refined question**

Within each eligible BWM ephys insertion-by-region population, do behavior-independent persistent-only, sequential-only, hybrid, or neither signatures provide different out-of-sample incremental prediction of trial-level choice and reaction time beyond an identical covariate baseline that is available by a fixed pre-movement prediction time?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If neural activity, trial-level choices, response times, stimulus information, and relevant movement measurements can be aligned within a common evidence-accumulation task, the resource may support matched comparisons of the incremental behavioral prediction supplied by persistent and sequential signatures.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavior trial table has the same eid and trial_id keys and the same task timing, contrast, choice, and response fields as the ephys trial table. Trial behavior features provide signed_contrast, choice_label, reaction_time, and movement_time; wheel features provide movement onset, peak, direction, amplitude, and velocity; DLC and event-aligned behavior features provide camera and event-aligned movement summaries.
  - Limitation: The inspection does not establish complete wheel or camera coverage for every ephys trial.
  - Limitation: No behavioral prediction, response-time distribution, or neural feature was inspected.
- **Unverified planning evidence:** The ephys release contains 295920 trial records with contrastLeft, contrastRight, stimOn_times, goCue_times, firstMovement_times, response_times, choice, bwm_include, and feedback fields; 75395 unit records carry insertion, session, quality-label, firing-rate, and atlas/BERYL region fields; insertion metadata includes trial and good-unit counts; and event records are keyed to session and trial.
  - Limitation: Counts are source metadata and do not demonstrate that every region or insertion satisfies a future eligibility rule.
  - Limitation: No neural-behavior association, population-dynamics estimate, or target-outcome diagnostic was calculated.
- **Unverified planning evidence:** The BWM behavior schema provides trials keyed by eid and trial_id, trial-level behavior features, wheel-trial features, DLC-trial features, event-aligned behavior features, movement-state epochs, and quiescence-state epochs. These surfaces permit documented session-trial joins and predecision movement covariates.
  - Limitation: Feature availability and coverage must be checked after the neural inclusion set is fixed.
  - Limitation: Compressed feature summaries are movement controls and do not by themselves establish full kinematic equivalence.
- 1 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Eligible BWM ephys insertion-by-region populations with bwm_include trials, quality-filtered units, observed endpoints, and a fixed neural window ending before first movement. The same outcome-independent structural thresholds apply to every signature class.
- Unit of observation: A held-out trial for choice prediction and a held-out valid-response trial for reaction-time prediction, each represented only through the fixed neural window ending before first movement.
- Unit of inference: Eligible insertion-by-region population, with replication assessed across sessions and subjects rather than treating trials as independent population replicates.
- Hierarchy and dependence: Use cross-fitting within population and blocked outer folds by session where possible; aggregate population-level predictive differences with hierarchical session and subject structure and clustered uncertainty.
- Validation: Verify an auditable, fold-safe availability registry; ensure no trial, session, unit-selection, temporal-window, preprocessing, or hyperparameter leakage; test spike decoding and toy recovery; and confirm that held-out endpoint-label permutation removes incremental performance while retaining the complete selection procedure.
- Split strategy: Use nested cross-validation with session-blocked outer folds where possible. Freeze the covariate registry before outcome fitting; learn signature scores, imputation, scaling, feature reduction, and regularization from each training fold only, then apply them unchanged to its held-out fold. Leave-subject-out generalization is a sensitivity analysis.
- Claim ceiling: predictive

**Analysis strategy**

1. Before fitting any endpoint model, create and freeze a prediction-time availability registry for every candidate baseline variable: semantic source, acquisition time, window end, permitted endpoint, and transformation. The primary prediction time is the end of the fixed neural window and is strictly before first movement on every included trial.
2. Allow in both primary baselines only stimulus-side covariates known by that time: left and right contrast or their signed and unsigned prespecified transforms, fixed task-clock terms, and fold-local intercept or scaling terms. No covariate may be admitted because it improves a held-out endpoint.
3. Exclude from both primary choice and reaction-time baselines firstMovement_times, response_times, reaction_time, movement_time, movement_onset_time, movement direction, amplitude, velocity, DLC summaries, event-aligned movement summaries, and any feature window that encodes, coincides with, or extends beyond the prediction time. Use first-movement and response fields only to define endpoint validity and the pre-movement eligibility window, never as predictors.
4. 3 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Within-session permutation of held-out behavioral labels after all fold-local preprocessing.; Response-linked timing and movement features entered only in a clearly non-primary leakage demonstration, never in the primary comparison or its estimand.; plus 1 additional item(s) in the complete dossier
- Positive controls: Synthetic data with known persistent or sequential features and matched behavioral association structure under the same availability registry.; Recovery of prespecified stimulus-side covariates by baseline models before evaluating neural increments.
- Alternative explanations: Stimulus strength or fixed event timing may drive both neural signatures and behavior.; Pre-movement neural activity may retain unmeasured movement preparation.; plus 3 additional item(s) in the complete dossier

**Interpretation limits**

- Out-of-sample prediction is associational and does not establish causal contribution or a circuit mechanism.
- The primary estimand deliberately excludes response-linked movement information, so it measures incremental prediction beyond pre-movement stimulus information rather than prediction after movement execution.
- Residual unobserved preparatory signals and incomplete coverage remain threats despite the availability boundary and sensitivity analyses.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

It retains the within-population, common-criterion comparison of persistent and sequential signatures and tests their incremental held-out relevance for both endpoints. It does not turn movement or response timing into an endpoint proxy, and it remains distinct from regional representational-form adjudication.

**Before any later execution**

- Unresolved planning decisions: Lock response-time validity and transformation rules without examining predictive outcomes.; Fix the neural-window end and verify it is pre-movement for every included trial before execution.; plus 1 additional item(s) in the complete dossier
- Required future skills: Decode BWM delta-tick blosc spike shards into bounded trial-aligned counts inside fold-local preprocessing.; Implement fold-local matched dynamic-signature scoring, timestamped covariate availability auditing, and nested prediction comparison for binary choice and reaction time.

### Scientific stakes

**Discriminating observation**

For every eligible population, apply both signature tests to the same neural observation window: quantify persistence by evidence-conditioned state stability and cross-temporal generalization, and quantify sequentiality by reproducible ordered turnover of active population components while evidence information remains recoverable across time. Use predeclared, behavior-independent thresholds in this common metric space to classify populations as persistent-only, sequential-only, hybrid when both criteria are met, or neither when neither is met. Then compare equally constrained predictors on held-out trials under identical task inclusion rules, choice and response-time definitions, neural windows, and stimulus and movement-related baseline covariates. A reproducible difference in incremental prediction of both behavioral endpoints between the two signatures would discriminate their behavioral relevance; regional identity may qualify generality but is not the target contrast.

**What possible outcomes would mean**

- Positive pattern: If the persistent signature contributes greater reproducible held-out incremental prediction of choice and response time than the sequential signature under matched conditions, persistent organization would receive stronger predictive support as a behaviorally consequential description, without establishing causality.
- Negative pattern: If the sequential signature contributes greater reproducible held-out incremental prediction of both endpoints under the same conditions, sequential organization would receive stronger predictive support, without selecting among sequential circuit mechanisms or establishing causal evidence transfer.
- Null or ambiguous pattern: If the signatures provide comparable, weak, or unstable incremental prediction after matched baselines—or if hybrid classifications dominate—the results would argue against behaviorally privileging either pure form and would leave hybrid, scale-dependent, or inadequately measured dynamics as live explanations.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The revision resolves both prior scientific blockers. The representational-form plan retains signed evidence as a protected jointly estimated component and marks nonidentifiable populations unresolved. The behavioral-prediction plan establishes a fold-safe pre-movement availability boundary and excludes response-linked and movement-linked variables from primary baselines. Remaining choices are appropriate pre-execution locks and do not prevent a credible planning dossier.

Retained changes and locks:

- **Pre execution lock:** Before execution, fix structural eligibility thresholds, the primary temporal scale and bounded secondary scale grid, and outcome-independent movement-missingness and response-time validity policies.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: A material revision was detected and requires a novelty recheck.

Round 2 substantively resolves both round-0 scientific blockers. The representational-form variant now jointly estimates a protected signed-evidence block E with a separate nuisance block N, explicitly forbids residualizing/regressing out signed contrast before fitting E, requires an overlap/collinearity diagnostic, and labels non-identifiable populations 'unresolved' rather than forcing a classification — this makes the evidence-conditioned estimand identifiable while still separating sensory/commitment/movement structure. The behavioral-prediction variant now freezes a fold-safe, prediction-time availability registry before any endpoint fitting, restricts primary baselines to stimulus-side covariates knowable before a fixed pre-movement time, and excludes all response-linked and movement-linked fields from both primary choice and reaction-time models, with any early-movement feature relegated to a clearly separated, non-primary sensitivity analysis. Both revisions directly target the identified integrity concerns without drifting the protected scientific questions or merging representational-form and behavioral-relevance claims. The remaining unresolved items (structural eligibility thresholds, temporal-scale grid, movement-missingness and RT validity policy) are bounded, outcome-independent implementation choices appropriate to lock before execution and do not undermine the credibility of the planning dossier. No new scientific blocker is identified.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
