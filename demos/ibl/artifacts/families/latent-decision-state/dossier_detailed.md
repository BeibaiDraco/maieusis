# Latent decision state versus observable embodied state — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Asks whether neural population organization contains a predictive latent decision-state representation distinguishable from immediate stimuli, choices, response timing, and measured pose.

The scientific tension is:

History-dependent neural variation may represent an internal decision state, observable ongoing behavior, immediate task variables, or unexplained intrinsic dynamics.

## Variant 1: Inferred internal-state branch

### Why it matters

A successful distinction would connect latent-variable inference to distributed population geometry without equating experimenter-defined history with a subject's internal state.

### Original and refined question

**Original Question Scientist proposal**

Is a history-dependent latent decision state represented across multiple brain regions beyond immediate sensory input, current choice, response time, and measured pose?

**Reviewed refined question**

Across qualifying BWM sessions and recorded regions, does a behavior-only history-dependent decision-state estimate explain and predict pre-choice neural population geometry beyond current stimulus, current choice, response timing, measured pose, and slow session variation?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Task events, choices, response times, pose, and broad neural sampling may allow later planning of an inferred-state representation question.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavior release reports 458 session shards, 453 sessions with DLC, 1,324 camera-availability rows, 847,042 DLC-trial-feature rows, and 5,509,305 event-aligned behavior-feature rows. The bounded shard metadata documents timestamped body, left, and right camera feature matrices with DLC coordinates and likelihoods for nose, pupil landmarks, paws, tube landmarks, tongue endpoints, and pupil-diameter features, plus wheel position and velocity.
  - Limitation: The one-shard inspection demonstrates format and terminology only; it does not establish coverage for every neural session or camera.
  - Limitation: DLC coordinates are an observed-pose proxy and do not exhaust behavioral or physiological state.
  - Limitation: This inspection retained no raw frame values, timestamps, or session identifiers.
- **Unverified planning evidence:** The local ephys release reports 459 sessions, 699 insertions, 75,395 units, 295,920 trials, and a complete spike store for 699 insertions. Its schema keys units by pid and cluster_id, links insertions and sessions through metadata tables, and provides trial and event surfaces plus raw spike shards suitable for later time-aligned population features.
  - Limitation: Release-wide totals do not establish a balanced number of regions, units, or trials per session.
  - Limitation: Anatomical aggregation and unit-quality rules require prespecification from the metadata at execution.
  - Limitation: The compressed spike format requires a dedicated read-and-bin capability before execution.
- **Unverified planning evidence:** Both releases define session-level records keyed by eid and trial-level records keyed by eid plus trial_id. The behavior release also defines trial_behavior_features, DLC trial features, event-aligned behavior features, wheel features, and state-epoch tables; the ephys release defines insertion, unit, trial, event-response-feature, and spike-store surfaces.
  - Limitation: Schemas establish table grain and keys, not complete-case overlap or numeric quality.
  - Limitation: Cross-release eid alignment and camera-specific coverage must be checked before execution.

### Plan at a glance

- Population and scope: Local BWM sessions joining by eid with usable trials, prespecified neural quality, and preregistered pose coverage; inference is restricted to represented recorded regions.
- Unit of observation: A trial-aligned pre-choice regional population feature with covariates computed using prior trials only.
- Unit of inference: Session or animal, with trials treated as dependent nested observations.
- Hierarchy and dependence: Use partial pooling for animal, session, insertion, and region; use cluster-robust uncertainty and session-blocked evaluation.
- Validation: Use behavior-only held-out choice prediction and synthetic recovery to select the state model; verify alignment, pose likelihood coverage, and training-only tuning before target evaluation.
- Split strategy: Use forward-chaining state inference and blocked leave-session-out or leave-animal-out outer evaluation; fit all scaling and tuning on training sessions only.
- Claim ceiling: predictive

**Analysis strategy**

1. Infer the latent state from prior behavioral trials only, with no neural inputs.
2. Construct fixed pre-choice population features and exclude post-choice movement from the primary window.
3. Compare task-plus-drift, task-plus-pose, and task-plus-pose-plus-history models.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Future-shifted history features.; Block-preserving circular permutations of the history state.
- Positive controls: Immediate stimulus and choice should be recoverable from task-aligned neural features under the same split.
- Alternative explanations: Persistent or unmeasured embodied state.; Slow drift, trial position, or block structure.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Conditional prediction cannot establish neural representation or causal mediation.
- A negative outcome can reflect imperfect state inference or incomplete pose measurement.

**Why the plan serves the question**

The unobserved construct is inferred only from prior behavior and is directly contrasted with pose, immediate task variables, response timing, and drift without collapsing into the sibling question.

**Before any later execution**

- Unresolved planning decisions: Choose state-model family by behavior-only validation.; Set camera completeness, unit quality, and regional aggregation thresholds after structural audit and before target modeling.
- Required future skills: Decode compressed BWM spike and camera shards into validated event-aligned arrays without retaining raw streams.; Construct leakage-safe cross-modal population features with blocked validation.

### Scientific stakes

**Discriminating observation**

A latent-state account would be favored if an independently inferred history-dependent variable predicts neural geometry and future decisions beyond immediate task variables and measured pose, with structured distribution across regions.

**What possible outcomes would mean**

- Positive pattern: A positive result would support a predictive distributed representation of history-dependent decision state.
- Negative pattern: A negative result would favor immediate-task, embodied-state, or localized accounts.
- Null or ambiguous pattern: A null result would leave unresolved whether the latent construct is absent, poorly operationalized, or obscured by limited behavioral measurement.

## Variant 2: Observed embodied-state branch

### Why it matters

Treating measured behavior as a candidate representation rather than only a nuisance can revise interpretations of distributed neural variability.

### Original and refined question

**Original Question Scientist proposal**

Does multidimensional pose explain a distributed component of neural activity that would otherwise be attributed to latent decision state or intrinsic noise?

**Reviewed refined question**

Across qualifying BWM sessions and recorded regions, does time-aligned multidimensional observed pose explain pre-choice neural population geometry beyond immediate task variables and simpler global-state summaries, and reduce structure otherwise assigned to history-derived or residual components?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Joint electrophysiology and video-derived pose across broad anatomical sampling may allow later planning of distributed embodied-state comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavior release reports 458 session shards, 453 sessions with DLC, 1,324 camera-availability rows, 847,042 DLC-trial-feature rows, and 5,509,305 event-aligned behavior-feature rows. The bounded shard metadata documents timestamped body, left, and right camera feature matrices with DLC coordinates and likelihoods for nose, pupil landmarks, paws, tube landmarks, tongue endpoints, and pupil-diameter features, plus wheel position and velocity.
  - Limitation: The one-shard inspection demonstrates format and terminology only; it does not establish coverage for every neural session or camera.
  - Limitation: DLC coordinates are an observed-pose proxy and do not exhaust behavioral or physiological state.
  - Limitation: This inspection retained no raw frame values, timestamps, or session identifiers.
- **Unverified planning evidence:** The local ephys release reports 459 sessions, 699 insertions, 75,395 units, 295,920 trials, and a complete spike store for 699 insertions. Its schema keys units by pid and cluster_id, links insertions and sessions through metadata tables, and provides trial and event surfaces plus raw spike shards suitable for later time-aligned population features.
  - Limitation: Release-wide totals do not establish a balanced number of regions, units, or trials per session.
  - Limitation: Anatomical aggregation and unit-quality rules require prespecification from the metadata at execution.
  - Limitation: The compressed spike format requires a dedicated read-and-bin capability before execution.
- **Unverified planning evidence:** Both releases define session-level records keyed by eid and trial-level records keyed by eid plus trial_id. The behavior release also defines trial_behavior_features, DLC trial features, event-aligned behavior features, wheel features, and state-epoch tables; the ephys release defines insertion, unit, trial, event-response-feature, and spike-store surfaces.
  - Limitation: Schemas establish table grain and keys, not complete-case overlap or numeric quality.
  - Limitation: Cross-release eid alignment and camera-specific coverage must be checked before execution.

### Plan at a glance

- Population and scope: Local BWM sessions joining by eid that pass preregistered camera, neural-quality, and temporal-alignment rules; inference concerns observed camera-derived pose and represented recorded regions.
- Unit of observation: A pre-choice neural population feature paired with pose from a strictly antecedent aligned window.
- Unit of inference: Session or animal, with trials and units nested within sessions and insertions.
- Hierarchy and dependence: Use multilevel region and insertion effects with session- or animal-clustered inference and blocked temporal and session splits.
- Validation: Validate timestamp reconstruction, likelihood filtering, and pose dimensionality on training sessions only; use a synthetic time-shift recovery check to reject impossible lead-lag relations.
- Split strategy: Use session-blocked outer evaluation with preprocessing, imputation, dimension reduction, and tuning fitted only on training sessions; use blocked temporal folds for sensitivity checks.
- Claim ceiling: associational

**Analysis strategy**

1. Construct a prespecified quality-filtered pose representation from DLC coordinates, velocities, pupil, and wheel features.
2. Compare pose geometry against task-only and simple global-state models with held-out session prediction of neural features.
3. Add a behavior-only history-state covariate as a competing component and quantify residual structured variance.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Pose shifted outside plausible antecedent windows.; Within-camera block-preserving pose permutations.
- Positive controls: Wheel velocity and immediate movement summaries should be recoverable from their pose representation.
- Alternative explanations: A low-dimensional global arousal or movement state.; Pose as consequence rather than antecedent of choice.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Pose association does not prove causal influence or fully explain internal state.
- Residual activity cannot be uniquely assigned to latent decision state or intrinsic dynamics.

**Why the plan serves the question**

Observed multidimensional pose is the focal explanation and is contrasted with simple state, history-state, and residual alternatives rather than merged with the latent-state sibling.

**Before any later execution**

- Unresolved planning decisions: Prespecify pose representation and simple-state comparator on training-only data.; Set antecedent window and camera-completeness rule after structural audit and before target modeling.
- Required future skills: Decode compressed BWM camera and spike shards into validated aligned arrays without retaining raw streams.; Implement leakage-safe multimodal population-geometry evaluation.

### Scientific stakes

**Discriminating observation**

An embodied-state account would be favored if pose geometry predicts neural dimensions across regions and task periods beyond simpler state summaries, while reducing apparent latent-state or unexplained structure.

**What possible outcomes would mean**

- Positive pattern: A positive result would reclassify part of nominally intrinsic or cognitive variance as a distributed representation of ongoing behavior.
- Negative pattern: A negative result would strengthen latent-state or intrinsic-dynamics interpretations, conditional on adequate pose measurement.
- Null or ambiguous pattern: A null result would preserve a mixture account and highlight uncertainty about behavioral coverage and temporal alignment.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct scientific roles and provide credible, non-executable, evidence-scoped plans. They use antecedent/pre-choice neural windows, explicit competing explanations, leakage-aware blocked evaluation, and appropriately limited predictive or associational interpretations. Remaining choices are execution locks rather than planning-stage scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Before execution, fix structural-audit-informed coverage, neural-quality, regional-aggregation, camera-completeness, and temporal-window rules, with all selection and tuning confined to training data where applicable.
- **Pre execution lock:** Before execution, implement and validate decoding of compressed camera and spike shards, timestamp reconstruction, and leakage-safe cross-modal feature construction.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants provide credible, non-executable, evidence-scoped plans that preserve their distinct scientific roles. Variant-01 infers a history-dependent latent state from prior behavior only and treats measured pose, immediate task variables, and drift as competing covariates; variant-02 makes observed multidimensional pose the focal explanatory construct against task-only, simple-state, history-state, and residual alternatives. The forbidden semantic merges are respected: the inferred-state branch keeps behavior as a competitor while the embodied-state branch keeps pose as focal. Claim ceilings (predictive and associational) are honest, interpretation limits explicitly disclaim causal or…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
