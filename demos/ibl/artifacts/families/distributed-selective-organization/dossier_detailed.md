# Broad versus selective brain-wide organization of decision signals — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether stimulus and choice signals are broadly expressed across recorded populations or selectively organized by anatomical population and population dimension.

The scientific tension is:

Brain-wide detectability may reflect genuinely distributed computation, repeated local representations, common task covariates, or selective organization obscured by coarse summaries.

## Variant 1: Independent task-content selectivity versus generic cross-population prediction

### Why it matters

Testing predictive privilege for independently defined task content would distinguish selective large-scale organization from generic shared activity while avoiding the stronger and unsupported inference that prediction constitutes causal communication.

### Original and refined question

**Original Question Scientist proposal**

Are predictive relationships between anatomical populations carried by selective task-relevant dimensions rather than by broadly shared population activity?

**Post-novelty revised proposal**

Do dimensions defined independently by their representation of task variables have preferential cross-population predictive value over matched non-task-relevant dimensions, within-population predictive structure, and shared sensory, behavioral, and population-state covariates?

**Reviewed refined question**

Within simultaneously recorded, anatomically defined populations, do dimensions selected solely for cross-fitted representation of prespecified stimulus and choice variables predict activity in another population more strongly than reliability-matched non-task dimensions, within-population references, and models accounting for measured sensory, behavioral, and population-state covariates?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the resource contains suitable coordinated or otherwise comparable population observations, its broad standardized task coverage may permit task-relevant dimensions to be defined from task-variable representation independently of the cross-population prediction procedure and then compared with matched reference dimensions and covariates.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The metadata query found 459 ephys sessions, 699 insertions, and 240 sessions with two insertions; all 75,395 listed units had positive labels, 65,336 had Beryl labels spanning 266 labels, and 196,574 trials were marked bwm_include. Wheel features were present for 258,614 rows and DLC features for 847,042 rows across three cameras.
  - Limitation: These are aggregate coverage facts only and do not establish a usable number of trials or units for any selected anatomical pair.
  - Limitation: No neural response, decoding, cross-population prediction, effect size, or significance calculation was performed.
  - Limitation: Population-pair eligibility must be fixed by prespecified unit and trial thresholds before execution.
- **Unverified planning evidence:** The sampled shard declares dense local cluster indices, delta-encoded spike times with 100-microsecond quantization, and separate spike-time and cluster arrays, providing the structural information needed for later trial-aligned population-rate reconstruction.
  - Limitation: One shard metadata record does not prove every shard is readable or suitable.
  - Limitation: A later executor must implement validated decoding, time reconstruction, and trial alignment for this storage format.
- **Unverified planning evidence:** The behavior dataset provides eid and trial_id keyed trial, wheel, and DLC feature tables, plus movement and quiescence epoch tables; these support prespecified sensory, choice, movement, and behavioral-state covariates after an eid and trial_id join.
  - Limitation: Availability and completeness of each behavioral modality vary by session.
  - Limitation: The schema does not establish that measured covariates eliminate common-input confounding.
- 1 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Eligible BWM sessions with two insertions and sufficient included trials and quality-labeled units; anatomical populations are formed within session from a preregistered Beryl-level aggregation rule, and inference generalizes over eligible sessions rather than individual trials or units.
- Unit of observation: A held-out trial-by-time-bin population score from an eligible source or target anatomical population.
- Unit of inference: An eligible simultaneous-recording session, with pair-level estimates combined using session-respecting hierarchical or meta-analytic inference.
- Hierarchy and dependence: Trials are nested in source-target population pairs, which are nested in sessions and subjects. All feature fitting, tuning selection, and prediction assessment are split or resampled at the trial level within session; uncertainty is clustered by session and sensitivity analyses aggregate first to session.
- Validation: Use nested cross-fitting so task relevance, matching, model tuning, and final cross-population evaluation are separated. Verify decoded shard times against metadata constraints, verify trial alignment and unit uniqueness, and run synthetic method-recovery simulations before target-data execution to confirm that the pipeline recovers injected selective and generic shared-state patterns without using target outcomes to select the method.
- Split strategy: Within each session, partition included trials into outer assessment folds and inner discovery and tuning folds; retain all units from a population within a fold, never select dimensions using assessment-fold cross-population values, and use blocked or stratified folds when trial chronology or task-condition imbalance requires it.
- Claim ceiling: associational

**Analysis strategy**

1. Restrict to bwm_include trials, quality-labeled units, and preregistered session, population, and reliability thresholds; join ephys and behavior only on eid and trial_id.
2. Reconstruct spike times from shard metadata and arrays, bin or smooth activity in prespecified stimulus-, movement-, and response-aligned windows, and derive population dimensions separately for each anatomical population and discovery split.
3. Define task-relevant dimensions on discovery trials only by cross-validated encoding or decoding of a finite prespecified set of task variables such as signed contrast and choice; do not use any cross-population covariance or prediction criterion in this definition.
4. 4 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permute source-to-target trial correspondence within session and assessment fold while preserving task-condition strata.; Use matched non-task dimensions and time-shifted source activity as references for generic shared activity.
- Positive controls: Require the cross-fitted task-relevance procedure to recover above-permutation representation of the prespecified task variable on discovery-validation data before designating any dimension as task-relevant.; Require the spike reconstruction and trial alignment pipeline to pass synthetic injected-signal recovery before execution on target comparisons.
- Alternative explanations: Shared sensory evidence, choice, movement timing, wheel movement, or camera-derived behavior drives both populations.; Global or local population-state fluctuations, rather than task content, produce broad cross-population predictability.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- Cross-population prediction does not establish directed communication, causal transmission, or a communication subspace.
- Observational covariate adjustment cannot eliminate unmeasured common inputs.
- The claim is limited to prespecified task variables, selected anatomical aggregation, eligible simultaneous sessions, and the recorded time scales.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

The plan preserves the decisive contrast: task relevance is established independently of inter-population covariance on separated trial information, then tested against matched non-task, within-population, and covariate references. Its positive and negative patterns retain the invariant's selective-organization versus generic-shared-state interpretation without making a causal claim.

**Before any later execution**

- Unresolved planning decisions: Preregister finite eligibility thresholds and anatomical aggregation before inspecting target predictive outcomes.; Preregister the finite task-variable set, time windows, regularization family, and population-state nuisance summary before execution.; plus 1 additional item(s) in the complete dossier
- Required future skills: Validated BLoSC spike-shard decoding and delta-time reconstruction.; Leakage-safe cross-fitted population-dimension selection, matching, prediction, and session-clustered inference.

### Scientific stakes

**Discriminating observation**

Task relevance must be established solely from a dimension's representation of prespecified task variables within a population, using information separated from the cross-population prediction assessment rather than selecting dimensions for inter-population covariance. Selective organization would require cross-population prediction for those dimensions to exceed matched non-task-relevant dimensions, within-population predictive references, and prediction attributable to shared sensory, behavioral, and population-state covariates. Broadly similar prediction across dimensions would favor generic shared fluctuations or common input, whereas no advantage over the matched references would provide no evidence for selective organization.

**What possible outcomes would mean**

- Positive pattern: A selective advantage for independently defined task-relevant dimensions over every matched reference would support preferential predictive organization of task content across populations, without establishing causal transmission or communication.
- Negative pattern: Broad prediction that is comparable for task-relevant and non-task-relevant dimensions, or substantially accounted for by shared covariates and within-population structure, would favor generic shared-state or common-input explanations over selective task-content organization.
- Null or ambiguous pattern: No reliable advantage over the matched references would leave selective cross-population organization unsupported and potentially unresolved because limited comparability or reliability could also produce a null result.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan preserves the protected selective-predictive-privilege question: task relevance is defined without cross-population covariance, assessment is held out, and the decisive comparisons include matched non-task dimensions, within-population references, and measured covariate/state references. It appropriately limits inference to associational prediction and eligible simultaneous sessions. Remaining items are pre-execution locks rather than planning-stage scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Before execution, preregister finite session/population eligibility and reliability thresholds, the Beryl-level anatomical aggregation rule, and the within-population reference construction without inspecting cross-population predictive outcomes.
- **Pre execution lock:** Before execution, fix the finite task-variable set, alignment windows, regularization family, task-relevance criterion, non-task matching rule, and nuisance population-state summary independently of assessment-fold cross-population outcomes.
- **Pre execution lock:** Before execution, declare the primary missing-modality rule for wheel and camera covariates and the corresponding complete-case or availability-based sensitivity analysis.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan operationalizes the protected question faithfully: task-relevant dimensions are established via cross-fitted encoding/decoding on discovery trials without reference to inter-population covariance, then evaluated on disjoint assessment trials against reliability-matched non-task dimensions, a within-population predictive reference, and nested covariate/nuisance-state models. Alternative explanations (shared sensory/behavioral drive, generic population-state fluctuations, sampling artifacts, temporal leakage) are explicitly enumerated and addressed via matching, negative controls (trial-permutation, time-shifted references), and positive controls (above-permutation task-recovery requirement, synthetic signal-recovery validation). The claim ceiling is associational and interpretation limits correctly disclaim causal/communication-subspace inference, consistent with the family's forbidden semantic merges. The three Owner-classified issues concern preregistration of eligibility thresholds, operational parameter choices, and a missing-modality rule -- all outcome-independent design locks needed only before execution, not defects in the current scientific test. No new scientific blocker is warranted.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
