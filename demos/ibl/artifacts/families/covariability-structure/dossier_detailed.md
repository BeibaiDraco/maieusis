# Task relevance of structured neural co-variability — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Separates the magnitude of population co-variability from its alignment and organization relative to decision and movement dimensions.

The scientific tension is:

Co-variability may be a global nuisance, a task-aligned computational resource, or structured modulation associated primarily with embodied state rather than decision processing.

## Variant 1: Stimulus-parallel versus stimulus-orthogonal choice-related co-variability beyond established population summaries

### Why it matters

Separating stimulus-parallel from stimulus-orthogonal choice structure can determine whether a co-variability–behavior relationship concerns sensory evidence, feedback or action-related signals, or only established changes in population signal and projected precision. This avoids assigning one functional meaning to all task-aligned variability.

### Original and refined question

**Original Question Scientist proposal**

Is the relationship between neural co-variability and decision performance better explained by alignment with stimulus- or choice-relevant population dimensions than by overall co-variability magnitude?

**Post-novelty revised proposal**

After decomposing the choice-related population dimension into stimulus-parallel and stimulus-orthogonal components, do their separate co-variability orientations make different, incremental predictions of decision performance beyond population signal, projected precision along the condition-modulation axis, mean correlation, global activity, and overall co-variability magnitude?

**Reviewed refined question**

Across eligible insertion-level neural populations, do independently estimated stimulus-parallel and stimulus-orthogonal components of the choice-related dimension show distinct, incremental associations with stimulus-conditioned decision performance beyond population signal, projected precision, mean correlation, global activity, covariance magnitude, and measured movement?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If repeated neural observations paired with stimulus, choice, performance, response-time, and embodied-state references are sufficiently comparable, they may support separate estimation of stimulus and choice dimensions and an incremental comparison of their covariance components with established population summaries.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** All 459 ephys session keys occur in the behavior availability metadata; 458 have wheel availability, 458 have DLC availability, and 458 have both. This supports session-level joining by eid while requiring planned complete-case and modality-missingness sensitivity analyses.
  - Limitation: The intersection establishes recorded-modality availability, not usable synchronized coverage in every planned time window.
  - Limitation: No claim about neural-behavioral effect size, decoding performance, or covariance structure is implied.
- **Unverified planning evidence:** Behavior tables share eid and trial_id with the ephys trial table. They provide trial correctness, reaction and movement times, wheel kinematics, camera- and event-aligned DLC summaries, and wheel-derived movement-state epochs. The inspected shard manifest also documents timestamped wheel arrays and DLC coordinate, likelihood, and pupil-feature arrays for body, left, and right cameras, including nose, pupil, paw, and tongue landmarks.
  - Limitation: DLC and wheel availability are incomplete for a small subset of sessions and measurements are camera-view-specific.
  - Limitation: The plan must treat pose as measured embodied state rather than an exhaustive measure of movement, engagement, or latent state.
  - Limitation: Raw behavioral-array decoding and synchronization verification require a later executor capability.
- **Unverified planning evidence:** The ephys release has insertion-keyed spike shards and metadata that link pid to eid, plus trial_id-keyed task records with contrastLeft, contrastRight, choice, feedbackType, stimulus, movement, response, and feedback timestamps. Units are keyed by pid and cluster_id; events are keyed by eid, trial_id, and event identifier. The build report records 459 sessions, 699 insertions, 75,395 units, and 295,920 trials.
  - Limitation: This is a structural documentation and schema inspection, not a confirmation analysis.
  - Limitation: Spike reconstruction, trial binning, quality filtering, and the number of usable units per planned population remain execution-time eligibility checks.

### Plan at a glance

- Population and scope: Eligible task sessions with an insertion-level population, documented trial stimulus and choice records, and sufficient prespecified trials in held-out condition cells; inference will generalize across sessions and animals only to the recorded BWM task population.
- Unit of observation: A trial-level neural response vector in a prespecified stimulus-aligned and response-aligned time window.
- Unit of inference: A held-out session or animal-level aggregate of prespecified cross-fitted trial estimates, with session and subject dependence retained in inference.
- Hierarchy and dependence: Keep trials nested within insertion, session, and subject. Estimate geometry and covariance within insertion and cross-fit by trial folds; use hierarchical or cluster-robust uncertainty at the session and subject levels rather than treating trials as independent replicates.
- Validation: Before target modeling, use synthetic response matrices with known overlapping stimulus and choice vectors to recover the component decomposition and verify that fold separation prevents circular construction. Verify spike decoding, event alignment, and joins on structural checks only.
- Split strategy: Use nested cross-fitting: trial folds construct geometry and covariance features separately from folds used for outcome models; group outer evaluation folds by session, and where feasible by subject, so repeated trials and shared populations cannot leak.
- Claim ceiling: associational

**Analysis strategy**

1. Select good units and trial cells using prespecified quality and coverage rules without reference to behavioral associations.
2. In training folds, estimate a stimulus coding vector from signed contrast and a choice vector conditional on stimulus, then residualize the choice vector into stimulus-parallel and stimulus-orthogonal components.
3. In disjoint folds, estimate conditionally centered trial covariance and separately normalized covariance orientations along both components, plus their contrast.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permute choice labels within session and stimulus strata before construction to test for geometry-to-outcome leakage.; Use a time-shifted neural window outside the prespecified task-response window as a temporal specificity control.
- Positive controls: Recover the signed-contrast stimulus dimension from held-out neural responses when prespecified quality thresholds are met.; Verify that observed wheel and DLC trial features align with their recorded event labels without using decision-performance outcomes to tune processing.
- Alternative explanations: Population signal, projected precision, mean correlation, global activity, or covariance magnitude explains any apparent component association.; Measured wheel or camera-derived movement and engagement proxies explain the apparent choice-related structure.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Conditional predictive associations cannot establish feedforward transmission, feedback, or action-plan causation.
- Recorded movement and pose do not exhaust latent embodied or engagement state.
- Planning evidence establishes available data surfaces, not an observed neural or behavioral result.

**Why the plan serves the question**

It evaluates the protected parallel-versus-orthogonal covariance contrast with independently constructed components and asks for incremental information beyond the named conventional covariance and state alternatives, rather than replacing the question with generic choice decoding.

**Before any later execution**

- Unresolved planning decisions: Fix analysis-window widths and covariance regularization using synthetic recovery and data-quality criteria before inspecting target associations.; Specify the primary performance link as correctness conditional on signed contrast and reserve response-time analyses as secondary.
- Required future skills: Decode the documented delta-encoded blosc spike shards into trial-aligned population matrices without materializing the full dataset.; Implement leakage-safe cross-fitted geometry, regularized covariance orientation, projected-precision, and hierarchical held-out evaluation.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

The proposed orientation quantity is the separately normalized covariance expressed along the stimulus-parallel and stimulus-orthogonal components of an independently defined choice dimension, together with their contrast; unlike projected precision, it is not inverse covariance along the population-signal or condition-modulation axis. A discriminating result requires the two components to show separable or complementary performance relationships and to add explanatory value beyond population signal, projected precision, mean correlation, global activity, overall covariance magnitude, and available embodied-state references. Preferential association of the parallel component with stimulus-conditioned performance would favor a feedforward account, whereas association of the orthogonal component with choice or response variation but not improved stimulus-conditioned performance would favor a feedback or action-plan account.

**What possible outcomes would mean**

- Positive pattern: Distinct incremental relationships would support the view that the orientation of choice-related covariance partitions functionally different signals: stimulus-parallel structure associated with sensory-evidence use and stimulus-orthogonal structure associated with feedback or action-related variation. Complementary contributions would instead support a joint account without collapsing them into one alignment score.
- Negative pattern: If established population signal, projected precision, mean correlation, global activity, or overall covariance magnitude account for the behavioral relationship, or if the orthogonal and parallel components show the same behavioral meaning, the proposed component-resolved structural account would be weakened.
- Null or ambiguous pattern: If neither component nor the established alternatives has a stable relationship with decision variation, the observations would not adjudicate the competing functional accounts and could indicate insufficiently reliable geometry, covariance, or behavioral references.

## Variant 2: Conditional decision-specific versus embodied covariance structure

### Why it matters

Distinguishing unique decision-linked covariance, unique movement-linked covariance, and shared predictive covariance is necessary before assigning cognitive or embodied meaning to population structure. This focuses inference on relationships among neurons rather than on already-established movement prediction of mean activity or overall neural variance.

### Original and refined question

**Original Question Scientist proposal**

Is structured population co-variability associated more strongly with decision variables or with video-derived movement and pose states?

**Post-novelty revised proposal**

Does structured inter-neuronal covariance uniquely predict decisions after accounting for video-derived movement and pose, and reciprocally predict task-aligned or spontaneous movement after accounting for decision variables, when both conditional comparisons use comparable temporal support and model capacity?

**Reviewed refined question**

For matched prespecified temporal windows, does off-diagonal trial-level neural covariance remaining after conditional single-unit mean modeling add unique held-out prediction of decision variables beyond measured wheel and DLC state, and does the reciprocal covariance representation add unique prediction of task-aligned or spontaneous movement beyond decision variables?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If temporally overlapping population recordings, decisions, and video-derived movement or pose observations are sufficiently informative, they may support matched conditional comparisons of covariance-level prediction. A later planner must verify overlap, repeated-observation adequacy, temporal comparability, and whether task-aligned and spontaneous movements can be distinguished.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** All 459 ephys session keys occur in the behavior availability metadata; 458 have wheel availability, 458 have DLC availability, and 458 have both. This supports session-level joining by eid while requiring planned complete-case and modality-missingness sensitivity analyses.
  - Limitation: The intersection establishes recorded-modality availability, not usable synchronized coverage in every planned time window.
  - Limitation: No claim about neural-behavioral effect size, decoding performance, or covariance structure is implied.
- **Unverified planning evidence:** Behavior tables share eid and trial_id with the ephys trial table. They provide trial correctness, reaction and movement times, wheel kinematics, camera- and event-aligned DLC summaries, and wheel-derived movement-state epochs. The inspected shard manifest also documents timestamped wheel arrays and DLC coordinate, likelihood, and pupil-feature arrays for body, left, and right cameras, including nose, pupil, paw, and tongue landmarks.
  - Limitation: DLC and wheel availability are incomplete for a small subset of sessions and measurements are camera-view-specific.
  - Limitation: The plan must treat pose as measured embodied state rather than an exhaustive measure of movement, engagement, or latent state.
  - Limitation: Raw behavioral-array decoding and synchronization verification require a later executor capability.
- **Unverified planning evidence:** The ephys release has insertion-keyed spike shards and metadata that link pid to eid, plus trial_id-keyed task records with contrastLeft, contrastRight, choice, feedbackType, stimulus, movement, response, and feedback timestamps. Units are keyed by pid and cluster_id; events are keyed by eid, trial_id, and event identifier. The build report records 459 sessions, 699 insertions, 75,395 units, and 295,920 trials.
  - Limitation: This is a structural documentation and schema inspection, not a confirmation analysis.
  - Limitation: Spike reconstruction, trial binning, quality filtering, and the number of usable units per planned population remain execution-time eligibility checks.

### Plan at a glance

- Population and scope: Eligible BWM task sessions with an insertion-level neural population and both wheel and DLC availability; inference is limited to the recorded task context and measured movement modalities.
- Unit of observation: A trial-window residual response vector after conditional single-neuron mean modeling, paired with matched trial-window decision and movement features.
- Unit of inference: Cross-fitted insertion-session estimates, aggregated with subject-aware uncertainty.
- Hierarchy and dependence: Maintain trial nesting within insertion, session, and subject. Construct conditional-mean and covariance features in training folds and evaluate targets in held-out grouped folds; use session and subject clustering or a multilevel model for uncertainty.
- Validation: Use synthetic trial populations with known conditional means, diagonal variance changes, and off-diagonal covariance to verify that the pipeline attributes signal only to the intended covariance component. Confirm table-key joins and timestamp availability before model fitting.
- Split strategy: Construct residual mean models, covariance features, hyperparameter choices, and target models using nested cross-fitting. Hold out sessions in the outer loop and avoid sharing trials, units, or time-adjacent windows between feature construction and target evaluation.
- Claim ceiling: associational

**Analysis strategy**

1. Prespecify matched stimulus-aligned and response-aligned time supports, then construct decision labels and movement/pose features only from those supports.
2. Fit cross-fitted single-neuron conditional mean models using stimulus, task timing, and the conditioning domain; retain residual off-diagonal covariance features after excluding diagonal variance and mean activity summaries.
3. For the decision direction, compare held-out decision prediction from residual covariance after movement and pose conditioning against models with movement/pose, conditional means, total variance, and matched model capacity.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Time-shift movement and pose features within session outside their matched window to test temporal specificity.; Permute decision labels within signed-contrast and session strata for the decision-direction control.
- Positive controls: Recover recorded task-event alignment in wheel and DLC features from their documented event-aligned tables.; Recover known synthetic off-diagonal covariance effects while rejecting pure conditional-mean and diagonal-variance simulations.
- Alternative explanations: Task-event or choice-execution movement drives an apparent decision-specific covariance association.; Incomplete camera coverage, unmeasured movement, arousal, or shared task state yields apparently domain-unique structure.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Bidirectional conditional prediction does not identify causal neural, cognitive, or motor mechanisms.
- No measured video or wheel set can rule out all latent embodied or task-related state.
- Planning evidence establishes data availability and joins, not a domain-specific covariance finding.

**Why the plan serves the question**

It directly tests the invariant's symmetric, covariance-specific decision-versus-movement contrast under comparable support and capacity, while preserving the required shared and measurement-limited interpretations rather than forcing a cognitive or embodied label.

**Before any later execution**

- Unresolved planning decisions: Define the a priori duration and exclusion buffers for task-aligned versus non-event-aligned movement epochs.; Choose a prespecified low-dimensional pose representation and camera-missingness rule before viewing target predictive comparisons.
- Required future skills: Stream and synchronize ephys spike shards with semantic wheel and DLC shards without full-dataset materialization.; Implement cross-fitted conditional-mean residualization and regularized off-diagonal covariance features that separate diagonal variance and global activity.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

The inferential target is the structured off-diagonal inter-neuronal covariance remaining around conditionally modeled single-neuron activity, not changes in mean firing or total variance. Evidence for decision-specific structure would require decision prediction from covariance remaining after movement-predictable neural activity is removed; the reciprocal test would require movement or pose prediction from covariance remaining after decision-predictable activity is removed. Both tests must use comparable temporal support and model capacity, and movement-related evidence must be reported separately for task-event- or choice-execution-aligned movements and spontaneous or idiosyncratic movements. Structure predictive of both domains but not uniquely attributable to either would be identified as joint, latent, or measurement-limited rather than assigned to cognition or embodiment.

**What possible outcomes would mean**

- Positive pattern: Unique decision prediction from residual covariance, without a comparable movement-only explanation and beyond task-aligned movement, would support a decision-specific interpretation of population organization. Conversely, unique prediction of movement or pose—especially spontaneous or idiosyncratic movement—with little unique decision prediction would support an embodied interpretation.
- Negative pattern: If apparent decision-specific covariance disappears after accounting for movement-predictable activity while unique movement prediction remains, cognitive interpretation of that covariance would be weakened. If the reciprocal pattern occurs, a primarily embodied interpretation would be weakened.
- Null or ambiguous pattern: If neither conditional comparison yields stable unique prediction, the data would not support domain-specific meaning for the covariance target. If prediction is shared or indistinguishable, it would instead remain attributable to joint task-movement coupling, an unmeasured latent condition, insufficient measurement separation, or inadequate covariance estimation.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants retain their distinct protected contrasts, use the documented linked neural, task, wheel, and pose surfaces, maintain an associational claim ceiling, and include cross-fitting, matched comparisons, and controls for the principal alternative explanations. Remaining choices are execution-time locks rather than deficiencies in the planning dossier.

Retained changes and locks:

- **Pre execution lock:** For the component-orientation variant, prespecify analysis-window definitions, covariance regularization selection based only on synthetic recovery and data-quality criteria, and correctness conditional on signed contrast as the primary performance outcome before inspecting target associations.
- **Pre execution lock:** For the reciprocal decision-versus-movement variant, prespecify task-aligned and non-event-aligned movement-epoch durations and exclusion buffers, the low-dimensional pose representation, and the camera-missingness rule before comparing domain-unique predictive value.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both sibling plans in this family preserve their protected component-resolved and reciprocal decision/movement contrasts, are grounded in documented dataset surfaces (session/insertion/unit counts, wheel/DLC coverage, eid/trial_id joins), maintain an associational claim ceiling with explicit interpretation limits, and specify concrete alternative-explanation controls, positive/negative controls, and cross-fitted, nested, group-aware evaluation to guard against leakage and mean/variance artifacts. The two owner-identified issues concern analysis-window widths, regularization-selection criteria, primary-outcome specification, movement-epoch definitions, pose representation, and camera-missingness rules — all execution-time operational choices rather than defects that prevent the plan from credibly answering its protected question. No new scientific blocker is present at round zero, and the family satisfies the family-soundness bar with two independently evidence-backed, non-pending sibling outcomes that respect the magnitude-versus-alignment and decision-versus-movement semantic separation required by the invariant.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
