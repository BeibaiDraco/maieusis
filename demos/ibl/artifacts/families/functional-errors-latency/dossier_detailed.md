# Behavioral meaning of population geometry — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Requires neural geometry to make distinct predictions about choice errors or response-time variation, rather than interpreting structure or decodability alone as functional evidence.

The scientific tension is:

Population geometry may contribute to decision computation, merely correlate with task conditions, or reflect movement and state variables that independently shape behavior.

## Variant 1: Speed-independent directional organization and incremental graded decision-timing prediction

### Why it matters

Testing a defined, speed-independent trajectory property against state, sensory, and movement alternatives can determine whether population geometry carries specific predictive meaning for graded decision timing rather than merely separating fast and slow trials.

### Original and refined question

**Original Question Scientist proposal**

Does the organization of neural population trajectories predict response-time variation beyond sensory conditions and measured movement?

**Post-novelty revised proposal**

Does trial-by-trial directional consistency of poststimulus population-state change toward the eventual choice-related state predict graded response time incrementally beyond sensory evidence, prestimulus population state, broad behavioral-state correlates, and independently measured movement variables?

**Reviewed refined question**

Does a prospectively cross-fitted, speed-independent measure of poststimulus population-state directional consistency toward an eventual choice-related state incrementally predict continuous single-trial response time after sensory, prestimulus-state, broad-state, trajectory-speed, and measured-movement controls?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If time-resolved population activity can be related to response times, sensory conditions, prestimulus activity, broad behavioral-state correlates, and independently measured movement, the dataset may permit assessment of whether directional consistency contributes incremental graded response-time information.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavioral trial-feature table has 295920 rows and exposes signed contrast, correctness, reaction time, and movement time. Wheel features cover 258614 distinct trial keys in a stimOn:response window, DLC features cover 292072 distinct trial keys across three cameras in a stimOn:feedback window, and session-level behavioral-state features are present for 458 sessions.
  - Limitation: This is an aggregate structural and availability check, not a check of outcome distributions or neural-behavior associations.
  - Limitation: Movement and broad-state controls are incomplete for some sessions or trials and require prespecified complete-case and missingness handling.
  - Limitation: The window labels do not by themselves prove temporal separation from movement for a chosen neural landmark.
- **Unverified planning evidence:** The ephys release has 295920 trial records from 459 sessions, with trial timing fields including stimulus onset, go cue, first movement, and response time. Its unit metadata links 75395 unit rows from 698 insertions to all 459 sessions.
  - Limitation: This is an aggregate structural and availability check, not a check of outcome distributions, neural-behavior associations, or estimator performance.
  - Limitation: This source does not determine the coverage of behavioral covariates or the adequacy of a chosen neural landmark.
- **Unverified planning evidence:** The behavior release declares trial behavior features, wheel trial features, DLC trial features, event-aligned behavior features, and session-level behavioral-state features. Trial feature tables share eid and trial_id keys with the ephys trial table, while wheel and DLC features retain window-specification fields and DLC camera identity.
  - Limitation: Feature meanings and coverage can vary by window specification, camera, and session.
  - Limitation: The schema does not establish that every ephys trial has each movement measurement.
- 1 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Included task trials from ephys sessions with documented trial timing, usable spike populations, and the covariate coverage required by each prespecified analysis tier; inference generalizes across sampled sessions and animals rather than treating trials as independent subjects.
- Unit of observation: A trial at a prespecified poststimulus neural landmark that occurs before that trial's first movement, with neural features computed exclusively from cross-fitted training folds.
- Unit of inference: Session and animal, with trial-level observations clustered within session and animal.
- Hierarchy and dependence: Fit hierarchical or cluster-robust models with session and animal structure; estimate all representation components, choice-state templates, scaling, and nuisance transforms inside training folds and apply them only to held-out trials or sessions.
- Validation: Before target modeling, verify timestamp consistency, spike-to-trial alignment, cross-fitting isolation, template stability across folds, and synthetic recovery of a direction-only effect distinct from speed; report coverage and calibration but do not tune against response-time effects.
- Split strategy: Primary splits hold out whole sessions, with an animal-held-out sensitivity analysis when sample coverage permits; all trial-level preprocessing and choice-template estimation remain inside the corresponding training partition.
- Claim ceiling: associational

**Analysis strategy**

1. Preprocess eligible units and bin spikes on a fixed poststimulus grid; standardize within training folds and form a low-dimensional population state using a cross-fitted dimensionality-reduction rule fixed before outcome modeling.
2. Define the eventual choice-related displacement from held-out-compatible, cross-fitted choice-state templates at the prespecified choice-related landmark, and define directional consistency as the mean cosine alignment of successive state-change vectors with that displacement.
3. Normalize direction vectors before alignment and include total state-change magnitude, elapsed neural-bin count, and landmark timing as nuisance terms so the focal feature is not a trajectory-speed proxy.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Replace the eventual-choice displacement with a fold-matched permuted choice label or an orthogonal displacement while retaining speed and timing covariates; any retained signal would indicate nonspecific geometry or leakage.; Use a pre-stimulus directional feature as a negative temporal control after accounting for prestimulus state.
- Positive controls: Verify that fold-trained choice-state templates discriminate the recorded choice label in held-out data, reported only as a representation-validity check rather than evidence for response-time prediction.; Verify synthetic recovery when a known direction-only signal is injected into simulated population states with independently varied speed.
- Alternative explanations: Signed sensory contrast or task condition jointly determines neural trajectories and response time.; Prestimulus population state or broad behavioral state jointly shapes later trajectories and response time.; plus 3 additional item(s) in the complete dossier

**Interpretation limits**

- Observational recordings cannot establish causal control of response timing by population geometry.
- Incomplete wheel, DLC, and session-state coverage can limit movement control and external generalization.
- The choice-related state and directional measure are operational definitions; successful prediction would not uniquely identify a decision mechanism.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

The focal feature is explicitly a direction-only, cross-fitted trajectory property toward an eventual choice-related state, while the design conditions on the exact sensory, prestimulus, broad-state, speed, elapsed-time, and measured-movement alternatives protected by the invariant. Its supportive, weakening, and movement-ambiguous outcomes preserve the intended scientific meaning without making a causal claim.

**Before any later execution**

- Unresolved planning decisions: Prespecify the neural landmark relative to stimulus, go cue, and first movement from timing documentation and coverage rules alone.; Prespecify the transform or survival-compatible model for skewed response times without comparing target-effect results.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

A prospectively defined and reproducible directional-consistency measure—alignment of successive population-state change directions with the eventual choice-related displacement, evaluated independently of change magnitude—predicts continuous single-trial response time incrementally after conditioning on sensory evidence or condition, prestimulus population state, broad behavioral-state correlates, generic trajectory speed or elapsed-time structure, and independently measured movement variables. If prediction remains but the feature is collinear with movement-related population dynamics, the observation supports behavioral prediction but does not uniquely favor a decision-dynamical interpretation.

**What possible outcomes would mean**

- Positive pattern: A stable incremental association not attributable to sensory, prestimulus, broad-state, speed, or measured-movement alternatives would support the interpretation that directional organization of population dynamics has specific predictive meaning for graded decision timing, without establishing causal control.
- Negative pattern: If sensory evidence, prestimulus or broad state, generic speed, or movement variables account for the apparent association, the claim that directional trajectory organization has distinct decision-timing meaning would be weakened; prediction that is inseparable from movement-related population dynamics would remain mechanistically ambiguous rather than uniquely supporting decision dynamics.
- Null or ambiguous pattern: If directional consistency provides no reproducible incremental prediction of continuous response time after the stated conditioning, this particular trajectory property would remain descriptive, although other population properties or unmeasured influences could still relate to decision timing.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan preserves the protected continuous response-time contrast and provides an associational, cross-fitted test of directional consistency while addressing sensory, prestimulus, broad-state, speed/timing, movement, and clustered-dependence alternatives. Remaining items are prospective execution locks, not scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Fix the poststimulus landmark and binning grid from timing and coverage rules alone, and retain only neural bins strictly before each trial's first movement; do not select these settings using response-time associations.
- **Pre execution lock:** Prespecify the wheel/DLC camera and window reduction rule plus missingness handling or analysis tiers without using response-time associations.
- **Pre execution lock:** Set prospective eligibility thresholds, the single- versus multi-insertion population rule, and the transformed-response versus survival-compatible response-time model without selecting among them by target-effect results.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan is a well-specified associational, cross-fitted test of the protected directional-consistency-to-response-time contrast. It explicitly conditions on sensory evidence, prestimulus population state, broad behavioral state, trajectory speed/elapsed time, and measured movement, with cross-fitted representation learning, session/animal clustering, negative controls (permuted/orthogonal displacement, pre-stimulus temporal control), positive controls (template validity check, synthetic direction-only recovery), and an explicitly associational claim ceiling with honest interpretation limits. The target contrast is clearly separated from the sibling's categorical-choice-error question, satisfying sibling separation and the family's forbidden-merge constraints. The three remaining Owner-identified issues (fixed landmark/binning grid before movement onset, movement-covariate reduction/missingness policy, and eligibility/model-form prespecification) are bounded, non-outcome-dependent implementation choices that do not alter the protected associational claim or its safeguards; they are correctly pre-execution locks rather than scientific blockers. No hard boundary or scientific-intent drift is implicated.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
