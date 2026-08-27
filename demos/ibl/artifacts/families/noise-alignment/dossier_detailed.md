# Functional alignment of shared variability during perceptual decisions — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Mixed family: accepted and non-accepted sibling variants**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether shared trial-to-trial variability is scientifically informative because of its orientation relative to sensory or choice-related population structure, rather than because of its overall magnitude.

The scientific tension is:

Noise correlations may be largely nonspecific fluctuations, or their geometry may selectively align with population dimensions carrying sensory evidence or impending choice. These alternatives can produce similar average correlation magnitudes but different functional interpretations.

## How to read this mixed family

Accepted and non-accepted sibling variants coexist here. Authority applies only to the variants explicitly marked as reviewed and accepted; it does not spill across the family.

## Variant 1: Sensory-specific information-limiting alignment branch

### Why it matters

Separating sensory-limiting geometry from fidelity-preserving task or action alignment would clarify when shared variability constrains sensory coding and when it instead marks dimensions used for behavior, without reducing the question to average correlation strength or an existing information-limiting covariance decomposition.

### Original and refined question

**Original Question Scientist proposal**

Is shared trial-to-trial variability selectively aligned with sensory-evidence representations, and does that alignment predict reduced or preserved stimulus discriminability beyond overall noise-correlation magnitude?

**Post-novelty revised proposal**

Does shared trial-to-trial variability aligned specifically with an independently estimated sensory encoding/likelihood direction predict lower held-out sensory discriminability, beyond overall correlation magnitude and an established information-limiting covariance measure, whereas comparably estimated task-feature and action/readout alignment predicts preserved rather than reduced coding fidelity?

**Reviewed refined question**

Across sufficiently sampled BWM recording populations, does covariance alignment with a sensory-likelihood axis estimated independently from held-out discriminability predict lower held-out sensory discriminability beyond correlation magnitude and a prespecified information-limiting covariance measure, more than reliability- and geometry-matched task-feature, action/readout, and mixed axes?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the available population recordings support independent estimation of residual covariance, sensory-conditioned responses, task features, action-related activity, and sensory discriminability, their standardized decision setting may permit held-out comparisons of the predictive specificity of sensory, task-feature, and action/readout alignment. These measurement and separation requirements remain to be verified by later planning.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** Both releases expose a 295,920-row trial table keyed by eid and trial_id. Documented ephys trial fields include choice, feedbackType, probabilityLeft, contrastLeft, contrastRight, stimOn_times, goCue_times, firstMovement_times, response_times, feedback_times, and bwm_include. Behavior-derived trial features include signed_contrast, choice_label, reaction_time, and movement_time.
  - Limitation: Header inspection does not establish balance across stimulus, choice, session, or insertion strata.
  - Limitation: Stimulus onset and first-movement timestamps have documented missing entries in the bounded metadata check and require prespecified availability rules.
- **Unverified planning evidence:** The behavior release supplies trial-indexed wheel features, DLC features, and event-aligned behavior features. Wheel features include movement onset, peak, direction, amplitude, and velocity; DLC features are indexed by eid, trial_id, camera, and window; event-aligned features are indexed by eid, trial_id, signal_name, event_name, and window.
  - Limitation: Wheel-feature coverage is not complete for every trial and the appropriate prereport window must be locked before execution.
  - Limitation: These feature summaries may not fully capture posture, preparation, or movement execution.
- **Unverified planning evidence:** The BWM ephys release defines session, insertion, unit, trial, event, and cluster tables; trials are keyed by eid and trial_id, units by pid and cluster_id, and spike data are stored per pid with delta-encoded spike times and cluster assignments.
  - Limitation: This establishes available data surfaces and keys, not the quality or adequacy of any selected recording population.
  - Limitation: The compressed spike representation requires a later bounded shard decoder and trial-alignment implementation.

### Plan at a glance

- Population and scope: BWM ephys task trials from sessions with matched trial metadata, and recording populations formed only from simultaneously recorded quality-screened units within an insertion or an explicitly prespecified same-session population. Inference will aggregate recording-population estimates with session and subject dependence retained.
- Unit of observation: A trial-aligned vector of binned spike counts for one simultaneously recorded population in a prespecified sensory window, with all axis estimation partitions recorded separately.
- Unit of inference: An independently estimated recording-population-by-resampling-fold contrast, synthesized with hierarchical uncertainty across insertions, sessions, and subjects.
- Hierarchy and dependence: Keep trials nested within recording populations, populations nested within sessions, and sessions nested within subjects. Use population-level cross-fitting, cluster-respecting resampling, and hierarchical or cluster-robust aggregation; never treat trials or units as independent replicates for the primary population-level claim.
- Validation: Use nested cross-fitting with disjoint folds for axis definition, covariance estimation, and discriminability scoring; conduct synthetic method-recovery simulations before target analysis; verify decoder reconstruction, fold isolation, condition coverage, and stability under resampling recording populations.
- Split strategy: Assign entire trials to mutually exclusive folds within each recording population, stratified only by prespecified stimulus conditions. No held-out discriminability, choice, or response data may influence axis selection, tuning, inclusion thresholds, or model form.
- Claim ceiling: associational

**Analysis strategy**

1. Before outcome evaluation, restrict to bwm_include task trials with the prespecified stimulus and neural-window timestamps available; use a separate availability audit to set non-outcome inclusion rules.
2. Decode only selected insertion shards, reconstruct spike times, and form trial-by-unit responses in a sensory window that ends before movement-sensitive control windows; validate reconstruction against shard metadata and cluster counts.
3. Within training folds, estimate a sensory encoding or likelihood direction from stimulus-conditioned responses while excluding choice, response, and motor variables from this axis definition.
4. 4 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Shuffle trial-to-response pairing within prespecified stimulus strata before covariance alignment estimation; any retained sensory-specific association indicates a leakage or implementation failure.; Use stimulus labels permuted within session as a sensory-axis control while preserving response geometry.
- Positive controls: Synthetic spike-count populations with known sensory-aligned and orthogonal covariance components must recover the intended ranking and not spuriously favor matched task or action axes.; Within observed data, verify only the structural ability to decode shard counts and recover declared trial timing, without assessing target discriminability effects during planning.
- Alternative explanations: Overall correlation magnitude or the established information-limiting covariance measure accounts for apparent sensory alignment.; Sensory-axis reliability, signal strength, dimensionality, or high-variance spectral opportunity exceeds that of comparison axes.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- The observational BWM dataset cannot establish that covariance geometry causes changes in sensory coding fidelity.
- A sensory axis is an operational estimate rather than direct access to a neural likelihood, and movement or latent-state confounding may remain after measured controls.
- Results would generalize only to included recording populations and task conditions, not necessarily to all brain regions, behavioral contexts, or neural measurement methods.

**Why the plan serves the question**

The plan preserves the protected sensory-versus-task/action geometry contrast by defining the sensory axis independently, evaluating discriminability on held-out trials, comparing matched alternative axes, and conditioning on both generic correlation magnitude and an established information-limiting covariance measure.

**Before any later execution**

- Unresolved planning decisions: Prespecify sensory response window and stimulus contrast coding before any target-outcome inspection.; Choose a literature-grounded information-limiting covariance measure that remains mathematically distinct from the new alignment metric.; plus 1 additional item(s) in the complete dossier
- Required future skills: Validated decoder for the documented delta-encoded Blosc spike-shard format with cluster-to-unit mapping.; Leakage-safe, cross-fitted population covariance and sensory-discriminability executor with hierarchical aggregation.

### Scientific stakes

**Discriminating observation**

Using independent estimation and held-out evaluation, sensory-likelihood alignment would predict lower sensory discriminability after controlling for overall correlation magnitude and an established information-limiting covariance measure. This incremental association would exceed that of task-feature, action/readout, and formally defined mixed axes matched as closely as the observations permit on estimation reliability, signal strength, dimensionality, and covariance-spectrum opportunity. In contrast, selective task/action alignment with preserved discriminability would favor a fidelity-preserving account rather than sensory information limitation.

**What possible outcomes would mean**

- Positive pattern: If sensory-likelihood alignment uniquely and incrementally predicts reduced held-out discriminability while matched task/action alignment does not, the result would support a sensory-specific information-limiting interpretation of covariance geometry rather than generic task relevance, dominant variance, correlation magnitude, or a restatement of an established information-limiting covariance measure.
- Negative pattern: If task-feature or action/readout alignment is at least as predictive and accompanies preserved discriminability, or if sensory alignment adds no prediction beyond the established information-limiting covariance measure, the result would weaken the proposed sensory-specific account and favor fidelity-preserving task/action alignment or existing covariance explanations.
- Null or ambiguous pattern: If the matched axes yield indistinguishable held-out predictions, the observations would not resolve sensory-specific information limitation versus generic task/action alignment. Such a null could reflect genuine equivalence or inadequate separation, reliability matching, or independent estimation of the sensory, task-feature, action/readout, and mixed axes.

## Variant 2: Latent choice-state covariance and motor-report dissociation branch

### Why it matters

Separating a choice-state covariance component from sensory, action-plan, report-movement, and preparation-related structure would clarify whether covariance geometry provides a predictive signature of decision formation rather than merely reflecting task relevance or embodied reporting.

### Original and refined question

**Original Question Scientist proposal**

Is shared trial-to-trial variability selectively aligned with choice-related population structure, and does that alignment predict choices or response-time variation after distinguishing sensory and embodied alternatives?

**Post-novelty revised proposal**

Does shared trial-to-trial variability contain a latent pre-report decision/choice-state covariance component that incrementally predicts held-out choice and response time after conditioning on sensory evidence or stimulus strength, task condition and relevant history, and measured or decodable report-movement and motor-preparation structure—and does this relation persist when choice is dissociated from the mapping or form of its motor report?

**Refined-question status**

No refined question earned accepted-plan authority for this sibling.

**Reviewed planning disposition**

Rejected because a faithful operationalization was not established. The exposed tables measure choice and movement but do not document any report-mapping, response-form, or modality condition that dissociates them. Motor covariates alone cannot satisfy the invariant's required dissociation or demonstrate separability without silently narrowing the claim.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If neural population activity, trial variables, behavioral timing, and sufficiently informative movement measurements are jointly available, they may support proposal-stage comparisons of latent covariance components across sensory conditions and report contingencies. Whether the observations include adequate report remapping, alternative report forms, or other movement-separating variation must be verified later.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** Both releases expose a 295,920-row trial table keyed by eid and trial_id. Documented ephys trial fields include choice, feedbackType, probabilityLeft, contrastLeft, contrastRight, stimOn_times, goCue_times, firstMovement_times, response_times, feedback_times, and bwm_include. Behavior-derived trial features include signed_contrast, choice_label, reaction_time, and movement_time.
  - Limitation: Header inspection does not establish balance across stimulus, choice, session, or insertion strata.
  - Limitation: Stimulus onset and first-movement timestamps have documented missing entries in the bounded metadata check and require prespecified availability rules.
- **Unverified planning evidence:** The behavior release supplies trial-indexed wheel features, DLC features, and event-aligned behavior features. Wheel features include movement onset, peak, direction, amplitude, and velocity; DLC features are indexed by eid, trial_id, camera, and window; event-aligned features are indexed by eid, trial_id, signal_name, event_name, and window.
  - Limitation: Wheel-feature coverage is not complete for every trial and the appropriate prereport window must be locked before execution.
  - Limitation: These feature summaries may not fully capture posture, preparation, or movement execution.
- **Unverified planning evidence:** The exposed schema provides choice plus report-movement measurements, but no trial-level report-mapping condition, alternate response modality, report-form label, or other documented variable that dissociates choice from its motor report.
  - Limitation: Schema absence cannot rule out a future external augmentation, but no such augmentation is part of the exposed branch-local dataset.
  - Limitation: Measured movement covariates can reduce motor confounding but cannot create the required mapping or form dissociation.

### Scientific stakes

**Discriminating observation**

A component defined without held-out behavioral leakage would improve out-of-sample prediction of choice and, separately, response time after conditioning on sensory evidence or stimulus strength, task condition and relevant history, the common sensory/action-plan axis, and measured or decodable report movement. Its choice relation would persist across a dissociation of choice from report mapping or report form, or otherwise be demonstrably separable from movement direction and execution. Response-time prediction would count as decision-state evidence only if it arises before report execution and exceeds prediction from preparation-related covariance. Simple axis alignment or unconditioned choice association would not satisfy this observation.

**What possible outcomes would mean**

- Positive pattern: Such a result would support, at an associational claim level, a latent choice-state interpretation of covariance geometry that is predictively separable from shared sensory/action-plan information, report movement, and motor preparation.
- Negative pattern: If prediction disappears after sensory or task conditioning, follows the motor-report mapping, or is explained by preparation-related covariance, the result would favor a common task-relevant, sensorimotor, or motor-preparation account over a distinct choice-state component.
- Null or ambiguous pattern: If no component provides reliable incremental held-out prediction, or if report and decision variables cannot be separated, the observations would not distinguish absence of a choice-state component from inadequate measurement, insufficient report dissociation, or unstable covariance estimation.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The sensory-fidelity variant provides a credible associational, leakage-protected plan that preserves the required sensory-versus-task/action geometry contrast, uses held-out discriminability, and conditions on both generic correlation magnitude and an established information-limiting covariance measure. The choice-state sibling is honestly rejected on branch-scoped evidence because the required report dissociation is unavailable; this does not invalidate the family plan.

Retained changes and locks:

- **Pre execution lock:** Before execution, lock non-outcome population and trial inclusion rules, including the sensory response window and stimulus coding.
- **Pre execution lock:** Before execution, specify an established information-limiting covariance measure that is mathematically distinct from the proposed sensory-alignment metric.
- **Pre execution lock:** Before execution, define comparison-axis construction, matching criteria, and the admissible handling of populations for which matched comparison axes cannot be obtained.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The v1 sensory-fidelity plan is a credible, leakage-protected associational design that preserves the protected sensory-versus-task/action geometry contrast: it estimates the sensory axis independently of held-out discriminability, cross-fits nested folds, matches or residualizes comparison axes on reliability/dimensionality/spectrum opportunity, and conditions on both overall correlation magnitude and a to-be-specified established information-limiting covariance measure. Claim ceiling is properly associational, alternative explanations and positive/negative controls are substantive, and hierarchy/dependence is handled at the population level. The v2 choice-state sibling is honestly rejected on branch-scoped evidence: no exposed report-mapping, response-form, or modality dissociation exists to satisfy its invariant, and the plan correctly declines to substitute motor covariates for the required dissociation rather than silently narrowing the claim. This satisfies the family standard of at least one evidence-backed variant with every sibling reaching an honest non-pending outcome, and the two variants remain properly separated per the forbidden-semantic-merge guidance. The three Owner-identified issues (non-outcome inclusion rules, a distinct information-limiting comparator, and axis-matching/failure rules) are all pre-execution locks: they name necessary but boundable execution-stage choices already anticipated in the plan's unresolved_decisions, not defects that prevent the planning product from credibly answering the protected question. No scientific blocker or hard-boundary issue remains at round zero.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
