# Functional geometry of shared neural variability — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

A family replacing correlation magnitude with structural alignment, separating sensory-information and decision-behavior meanings of shared variability.

The scientific tension is:

Shared variability can be nuisance, information-limiting structure, or behaviorally meaningful population organization; its consequence depends on orientation relative to candidate signal dimensions rather than magnitude alone.

## Variant 1: Decision-specific conditional behavioral-alignment variant

### Why it matters

Separating decision formation from motor implementation and testing incremental held-out behavioral prediction can clarify the functional meaning of shared-variability geometry without treating alignment as evidence of a causal neural readout.

### Original and refined question

**Original Question Scientist proposal**

Is shared population variability more selectively aligned with decision- or movement-related dimensions than with sensory-evidence dimensions, and does that alignment predict choices or response times?

**Post-novelty revised proposal**

Does the component of shared population variability aligned with an independently defined decision-formation dimension—but not a separately defined movement-execution dimension—provide out-of-sample prediction of both choices and response times beyond sensory-evidence alignment, movement covariates, and overall shared-variability magnitude?

**Reviewed refined question**

Across eligible BWM ephys populations, does pre-movement shared population variability projected onto a cross-fitted conditional choice dimension improve held-out prediction of choice and reaction time beyond sensory-evidence alignment, post-movement wheel/DLC execution alignment, and total shared-variability magnitude?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If synchronized population activity, sensory variables, choices, response times, and movement measurements are available with adequate reliability, they may support independently constructed sensory-evidence, decision-formation, and movement-execution dimensions and conditional held-out prediction.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavior build metadata reports 459 sessions, 396 sessions with wheel shards, 453 sessions with DLC shards, 258,614 wheel-trial feature rows, 847,042 DLC-trial feature rows, and 567,853 movement-state epochs.
  - Limitation: Aggregate availability does not guarantee that every ephys population has all movement measurements.
  - Limitation: The reported counts are structural metadata and not outcome analyses.
- **Unverified planning evidence:** The build metadata reports 459 sessions, 699 insertions, 75,395 units, 295,920 trials, and 4,152,659,397 stored spikes; it reports no missing, empty, or failed spike insertions.
  - Limitation: Aggregate build counts do not guarantee a sufficient simultaneously recorded population or eligible trial count in every insertion.
  - Limitation: The metadata are planning evidence and are not an analysis of neural-behavior associations.
- **Unverified planning evidence:** The shared trial keys are eid and trial_id. Trial behavior features include signed_contrast, choice_label, reaction_time, and movement_time; wheel features include movement onset, peak time, direction, amplitude, mean velocity, and maximum velocity; DLC features are indexed by camera and include feature summaries. The files report 295,920 trial-behavior rows, 258,614 wheel-feature rows, and 847,042 camera-specific DLC-feature rows.
  - Limitation: Feature availability and missingness must be assessed after the prespecified ephys-session and trial eligibility filters are applied.
  - Limitation: Footer inspection does not inspect participant-level values or estimate any behavioral association.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Eligible task trials from BWM sessions with a valid ephys insertion, trial timing and choice fields, and usable movement measurement for the movement-axis analysis; inference will be across independently recorded insertions or sessions, not individual trials treated as independent populations.
- Unit of observation: A trial-by-simultaneously-recorded-unit pre-movement spike-count or rate vector, joined to trial-level sensory, choice, reaction-time, and movement-feature variables.
- Unit of inference: Insertion or session-level population estimates, combined with hierarchical or cluster-robust inference across sessions and animals.
- Hierarchy and dependence: Fit geometry and prediction within each insertion or session using trial-blocked folds; preserve trial order for block construction; aggregate population-level contrasts with random effects for session and subject or with subject-clustered uncertainty. Never split individual trials from the same fitted population across a geometry-training and geometry-evaluation role.
- Validation: Before target evaluation, perform synthetic recovery using simulated populations with known sensory, decision, movement, and shared-covariance directions; verify the executor decodes shard timing and cluster identity against documented metadata; require fold-local axis fitting, temporal eligibility checks, and permutation of training-only choice labels to show that the pipeline does not leak outcomes.
- Split strategy: Use nested cross-fitting within insertion or session with contiguous or block-stratified trial folds to respect temporal dependence. All residualization, scaling, dimensionality reduction, axis fitting, covariance estimation, missing-data imputation, and hyperparameter selection occur inside training folds. The final outcome models are scored only on outer held-out trials; tuning choices are made from synthetic recovery and inner-fold stability, not held-out target scores.
- Claim ceiling: associational

**Analysis strategy**

1. Pre-register a pre-movement neural window beginning after the chosen sensory event and ending before first movement with a fixed safety buffer; exclude trials lacking valid timing or required covariates.
2. Within outer held-out folds, residualize or stratify choice coding for signed contrast and probabilityLeft so the decision candidate is conditional on measured sensory evidence and prior block. Fit the decision axis only on inner-training pre-movement neural responses.
3. Independently estimate a sensory-evidence axis from signed contrast and a movement-execution axis from wheel/DLC kinematics measured after first movement; do not use post-movement neural responses to define the decision axis.
4. 3 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Use fold-local permutations of conditional choice labels when fitting the decision axis; this should eliminate decision-specific held-out utility while retaining the same computational workflow.; Project shared variability onto a matched random orthogonal direction and test whether its apparent utility matches the decision component.; plus 1 additional item(s) in the complete dossier
- Positive controls: Verify that the sensory-evidence axis can recover held-out signed-contrast structure from the pre-movement population under the same cross-fitting machinery.; Verify that the movement-execution axis predicts post-first-movement wheel/DLC features in held-out trials when those features are available.
- Alternative explanations: A residual sensory or block-prior axis may masquerade as conditional choice coding.; Pre-movement activity may contain movement preparation that is not captured by available wheel/DLC summaries.; plus 3 additional item(s) in the complete dossier

**Interpretation limits**

- This observational dataset cannot establish that shared variability causes decision formation, and conditional choice coding is not a direct measurement of an internal decision variable.
- Temporal exclusion and measured kinematic covariates reduce but cannot eliminate motor-preparation, latent-state, and unmeasured-movement confounding.
- Results must be framed as population-specific associations and may not generalize across regions, tasks, or recording configurations without separate support.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

The plan retains the protected contrast between decision formation and movement execution by defining them from temporally distinct and independently estimated sources, controls sensory evidence and overall covariance magnitude, and requires incremental held-out prediction of both choice and reaction time. It makes comparable alignment an explicit mixed-structure outcome rather than silently reinterpreting it as decision-specific.

**Before any later execution**

- Unresolved planning decisions: Owner confirmation of the conditional pre-movement choice axis as the decision-formation operationalization.; A fixed neural-window and pre-movement buffer specification selected independently of target associations.; plus 1 additional item(s) in the complete dossier
- Required future skills: A BWM spike-shard reader that decodes delta-int ticks and dense local cluster indices into bounded trial-aligned population counts.; A leakage-audited nested cross-fitted shared-variability geometry and multi-outcome prediction executor with synthetic recovery tests.

### Scientific stakes

**Discriminating observation**

The discriminating observation would be preferential alignment of shared variability with an independently estimated decision-formation dimension, distinct from movement execution, whose component predicts both choices and response times out of sample after accounting for sensory-evidence alignment, measured movement covariates, and overall shared-variability magnitude. Comparable sensory, decision, and movement alignment would instead indicate non-unique mixed structure.

**What possible outcomes would mean**

- Positive pattern: Decision-specific alignment with incremental held-out prediction of choices and response times would support the associational claim that part of shared variability tracks decision formation rather than merely sensory structure, generic variability strength, or motor implementation.
- Negative pattern: If prediction is absorbed by sensory or movement covariates, or if sensory, decision, and movement alignments are comparable, the result would weaken a singular decision-related interpretation and favor sensory, motor, or non-unique mixed structure.
- Null or ambiguous pattern: If candidate dimensions or their alignments cannot be estimated reliably enough to compare held-out prediction, the functional meaning of the shared-variability geometry would remain unresolved.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan preserves the decision-formation versus movement-execution contrast, uses temporally separated and independently estimated candidate dimensions, controls the specified sensory and shared-magnitude alternatives, and limits conclusions to associational, out-of-sample evidence. Remaining choices are execution locks rather than deficiencies in the planning dossier.

Retained changes and locks:

- **Pre execution lock:** Fix the pre-movement neural window and safety buffer independently of target associations before execution.
- **Pre execution lock:** Specify the primary movement-measurement eligibility and missing-data policy before execution, including treatment of wheel-only, DLC-only, and incomplete-coverage sessions.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan operationalizes the protected decision-formation versus movement-execution contrast using temporally separated, independently estimated axes, cross-fitted to avoid leakage, and requires incremental out-of-sample prediction of both choice and reaction time beyond sensory alignment, movement covariates, and total shared-variability magnitude. Comparable alignment is explicitly treated as mixed rather than silently reinterpreted as decision-specific, matching the family's forbidden-merge constraint. Claims are capped at associational, interpretation limits are honest about latent-decision and motor-confound uncertainty, and positive/negative controls plus diagnostics support falsifiability. The two Owner issues concern a pre-movement window/buffer specification and a movement-eligibility/missing-data policy; both are execution-stage parameter choices that do not undermine the plan's current scientific logic and are correctly pre-execution locks rather than blockers.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
