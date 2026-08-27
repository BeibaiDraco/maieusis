# Covariance geometry and alternative population accounts of evidence accumulation — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Mixed family: accepted and non-accepted sibling variants**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Connects noise-correlation geometry to competing temporal organizations of decision formation: a stable accumulation axis or a changing sequence of population states.

The scientific tension is:

Behavior consistent with evidence accumulation can arise from persistent integration along a stable population direction or from sequential, time-varying population states. Shared variability may constrain these organizations differently.

## How to read this mixed family

Accepted and non-accepted sibling variants coexist here. Authority applies only to the variants explicitly marked as reviewed and accepted; it does not spill across the family.

## Variant 1: Within-region fixed-axis versus rotating or time-local geometry branch

### Why it matters

Separating movement along a fixed axis from rotation of the axis would clarify whether behaviorally relevant shared variability identifies a persistent regional accumulation geometry rather than merely task-relevant sensory features, action plans, movement preparation, or heterogeneous time-varying states.

### Original and refined question

**Original Question Scientist proposal**

Is behaviorally relevant shared variability aligned with a temporally stable evidence-accumulation direction whose state predicts choice and response time?

**Post-novelty revised proposal**

Within individual brain regions, does the same independently estimated shared-variability direction generalize across decision time and sensory conditions, track accumulated evidence, and predict choice and response time beyond sensory-feature, action-plan, elapsed-time, and movement-related alternatives, or do time-local directions better explain the observations?

**Reviewed refined question**

Within each adequately sampled recorded region, does a shared-variability direction estimated on training trials retain orientation and held-out associations with the signed-contrast time proxy, choice, and response time across prespecified decision-time bins and contrast conditions better than matched time-local directions, after available task-timing and movement alternatives are represented?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If time-resolved regional population activity can be related to sensory evidence, choices, response times, and relevant measured covariates, it may permit comparison of fixed within-region directions with time-local or condition-specific directions without assuming a common cross-region or whole-animal axis.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The 295,920-row trial table contains eid, trial_id, choice, contrastLeft, contrastRight, stimOn_times, goCue_times, firstMovement_times, response_times, feedback_times, probabilityLeft, and bwm_include. Behavior features contain signed_contrast, reaction_time, and movement_time. DLC availability is recorded by eid and camera, and DLC trial features include feature_mean and feature_peak.
  - Limitation: Signed contrast and elapsed time can be a task-derived sensory-feature proxy for v1, not literal temporally sequenced evidence pulses.
  - Limitation: DLC coverage and feature adequacy must be screened before execution; availability metadata does not guarantee a usable trajectory on every retained trial.
- **Unverified planning evidence:** The ephys build defines session, insertion, unit, trial, and event tables keyed by eid or pid, region annotations on units, and per-insertion compressed spike-time and spike-cluster shards. The build summary reports 459 sessions, 699 insertions, 75,395 units, and 295,920 trials.
  - Limitation: The schema establishes available joins and raw spike storage but does not establish per-region trial counts or estimability.
  - Limitation: No spike array or scientific outcome was loaded during this inspection.

### Plan at a glance

- Population and scope: Recorded good-quality units from one atlas-labelled region within an insertion and session, evaluated region by region. Inference generalizes across retained session-region samples rather than claiming a common cross-region or whole-animal variable.
- Unit of observation: A held-out trial-by-time-bin regional population vector constructed from simultaneously recorded retained units, with no unit permitted to cross the train-test boundary for a direction it helped estimate.
- Unit of inference: Session-region sample, with uncertainty aggregated across sessions and subjects using cluster-aware resampling or hierarchical modeling.
- Hierarchy and dependence: Keep spikes nested in unit, units nested in insertion-region, and repeated bins nested in trial. Fit or resample at the session and subject levels; never treat time bins or units as independent replicates.
- Validation: Use entirely training-derived preprocessing, residualization, axis estimation, dimensionality selection, and model tuning. Conduct synthetic recovery simulations with known fixed versus rotating axes before target analysis, plus label-shuffle, time-permutation, and circular-shift tests that preserve appropriate trial or autocorrelation structure.
- Split strategy: Primary splits hold out complete trials within session-region while balancing prespecified contrast and choice strata. Secondary validation holds out sessions and, where feasible, subjects; all preprocessing and axis estimates are recomputed within each training fold.
- Claim ceiling: associational

**Analysis strategy**

1. Predefine decision-interval bins from stimulus, go-cue, movement, and response timestamps, with primary analyses restricted to bins preceding first movement and response; repeat in prespecified alignment and interval sensitivities.
2. Within each training split and session-region, estimate a residual shared-variability direction from trial population vectors after removing prespecified mean effects of signed contrast, elapsed time, block probability, and task-event timing. Retain a direction only under predeclared rank, unit-count, and stability-quality rules.
3. Project held-out vectors onto that fixed training direction and compare orientation transfer and held-out prediction with matched-complexity time-local and condition-local directions, using nested fitting so test trials do not influence axis estimation, hyperparameter selection, or preprocessing.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permute trial identities within session and prespecified condition strata before estimating the behavioral relation.; Use non-overlapping or temporally misaligned neural bins under the same split structure to test whether apparent stability is alignment-driven.
- Positive controls: Synthetic fixed-axis and rotating-axis data with matched trial counts and noise will verify that the planned comparison recovers the intended distinction without favoring the more flexible model.; Task-event alignment features should be recoverable from the recorded timestamps, verifying the join and alignment pathway without serving as evidence for the target claim.
- Alternative explanations: Averaging of rotating or sequential time-local states can create an apparently stable direction.; Signed visual contrast or generic elapsed-time structure can drive both neural projections and behavior.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- This observational dataset cannot establish a causal integrator, physical information transfer, or a whole-animal decision variable.
- The signed-contrast time proxy is a sensory-feature alternative for v1 and must not be described as evidence-pulse control.
- DLC feature availability does not ensure complete pose or movement representation, and unobserved movement or input may remain.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

The plan directly preserves v1's independently estimated within-region fixed-axis contrast, separates axis orientation from displacement along an axis, compares time-local alternatives under fold-safe matched validation, and treats signed contrast only as the Owner-approved sensory-feature alternative.

**Before any later execution**

- Unresolved planning decisions: Pre-register the finite binning, smoothing, residualization, and model-complexity grids before loading target neural outcomes.; Pre-register the minimum coverage thresholds for wheel and DLC covariates and whether analyses with unavailable movement modalities are excluded or reported as a defined sensitivity set.
- Required future skills: Fold-safe decoding of BWM compressed spike shards into trial-aligned regional population vectors.; Nested fixed-axis versus time-local covariance-geometry comparison with cluster-aware uncertainty and synthetic method recovery.

### Scientific stakes

**Discriminating observation**

A stable regional account requires the same independently estimated within-region direction—not separately fitted time- or condition-specific directions—to retain its orientation across decision formation and relevant sensory conditions while the represented state may move substantially along it; its projection must generalize to held-out evidence, choice, and response time after sensory-feature, action-plan, elapsed-time, and movement-related alternatives are represented. Axis rotation, changing feature alignment, or superior generalization by time-local, time-varying-readout, sequential, or externally driven shared-fluctuation accounts would favor changing or input-driven organization. Stability confined to one or more regions, alongside differing axes or dynamics elsewhere, would support regional stable representations but not a common cross-region or whole-animal decision variable.

**What possible outcomes would mean**

- Positive pattern: If one independently estimated direction satisfies the cross-time, cross-condition, and conditional-prediction criteria within a region, the result would support a stable regional accumulation-related geometry even if the represented state fluctuates strongly along that direction. Concordant stability across regions would motivate, but not establish, a more common organization; regional differences would limit the conclusion to the stable regions.
- Negative pattern: If axes rotate or change alignment and time-local, condition-specific, sequential, time-varying-readout, or externally driven accounts generalize better to held-out evidence and behavior, the result would weaken the stable-axis account and favor heterogeneous region-specific, sequential, or input-driven organization.
- Null or ambiguous pattern: If fixed and changing-axis accounts cannot be distinguished at the available temporal or observational resolution, or if neither generalizes reliably after the competing alignments are represented, the temporal geometry and its behavioral meaning would remain unresolved rather than demonstrating absence of behaviorally relevant shared variability.

## Variant 2: Within-region sequential choice-information branch

### Why it matters

Distinguishing predictive information transfer through changing within-region states from stable-subspace coding would clarify the population geometry of evidence accumulation without treating generic temporal dynamics or regional model differences as evidence for a sequence.

### Original and refined question

**Original Question Scientist proposal**

Is evidence accumulation associated with a sequence of changing population states whose covariance structure preserves choice-relevant information across time?

**Post-novelty revised proposal**

Within an identified brain region during evidence accumulation, does choice information progress through reproducible covariance-defined population transitions, rather than remain decodable along a temporally stable axis, after accounting for evidence pulses, other task events, response-latency variation, and pose or movement trajectories?

**Refined-question status**

No refined question earned accepted-plan authority for this sibling.

**Reviewed planning disposition**

Rejected because a faithful operationalization was not established. The protected v2 discriminating observation requires accounting for evidence pulses. The available trial schema has only a single contrast condition and timestamps; the Owner ruled that the v1 signed-contrast proxy cannot substitute for pulse-sequence control in v2.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the available observations contain time-resolved population activity, evidence-related task variables, choices, response timing, region identities, and sufficiently informative event or pose measurements, they may support a later comparison of within-region sequential-transition and stable-subspace predictions.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The trial metadata provides one pair of visual contrast fields and task-event timestamps, but contains no evidence-pulse sequence, pulse identity, pulse timing, or time-varying sensory-input field.
  - Limitation: Column absence establishes only the absence of this recorded input surface in the inspected dataset table.
  - Limitation: No neural or behavioral outcomes were inspected.

### Scientific stakes

**Discriminating observation**

On held-out observations, a sequential account would be supported if time-specific choice codes show limited direct generalization across nonadjacent times but reproducible covariance-defined transitions predict the next population state and preserve or improve future choice-information prediction beyond a static projection. A stable-subspace account would instead be supported if a choice code learned at one accumulation time generalizes broadly across the decision interval without transition-specific prediction. Any sequential advantage must remain after comparisons accounting for stimulus or evidence-pulse alignment, response and other task-event timing, trial-to-trial response-latency variation, and available pose or movement trajectories.

**What possible outcomes would mean**

- Positive pattern: Would support a predictive within-region sequential organization of accumulation-related choice information that is not reducible to generic dynamic activity, stable-subspace coding, regional accumulation-model differences, or the specified event and movement alternatives. It would remain associational rather than evidence of physical or causal transfer.
- Negative pattern: If held-out choice information generalizes broadly through a stable direction and transition-specific prediction adds no explanatory value, the result would favor a stable-subspace account over the proposed within-region sequential organization.
- Null or ambiguous pattern: If neither reproducible transition-based preservation nor broad stable-axis generalization is reliable, or if their predictions cannot be distinguished after the specified controls, the temporal organization of accumulation-related choice information would remain unresolved.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The v1 plan preserves the within-region fixed-axis versus time-local contrast, separates axis orientation from displacement, uses held-out nested comparisons, and limits interpretation to associational regional evidence. The v2 operationalization is honestly rejected because the supplied schema lacks the required pulse-sequence input surface. Remaining items are pre-execution locks, not planning blockers.

Retained changes and locks:

- **Pre execution lock:** Before execution, fix the finite binning, smoothing, residualization, model-complexity, and quality-screen rules without reference to target outcomes.
- **Pre execution lock:** Before execution, define temporally admissible action and movement covariates, confirm or remove any wheel-feature covariates not supported by the selected data surface, and prespecify missing-modality handling.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The v1 plan preserves the protected fixed-axis versus time-local contrast, explicitly separates axis orientation from state displacement along the axis, and specifies fold-safe nested estimation with cross-time and cross-condition held-out evaluation against matched-complexity time-local/condition-local alternatives. Sensory, action, movement, and quality confounds are enumerated as alternative explanations and addressed through joint incremental prediction modeling. Claim ceiling is associational with explicit interpretation limits disclaiming causal integrator or whole-animal claims, consistent with dataset grounding in the ephys/behavior schema evidence. The v2 sibling is honestly rejected for dataset mismatch (no pulse-sequence input surface), and the Owner's ruling that the v1 signed-contrast proxy cannot substitute for pulse control is correctly carried into the v1 interpretation limits, preserving the forbidden-merge boundary between the stable-axis and sequential accounts. Both remaining Owner-classified issues concern binning/smoothing/residualization/quality-screen finalization and movement-covariate admissibility/missing-modality handling; these are bounded, outcome-blind execution details rather than defects that make the plan unable to answer the protected question, so they are correctly pre-execution locks rather than blockers. No new scientific blocker or hard-boundary concern is identified at this round.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
