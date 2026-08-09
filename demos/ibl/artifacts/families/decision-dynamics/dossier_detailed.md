# Population-dynamical transitions from sensation to action — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Mixed family: accepted and non-accepted sibling variants**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Examines whether decision-related population activity exhibits a meaningful transition in input sensitivity or instead reflects continuous evolution confounded with movement preparation.

The scientific tension is:

Similar choices can emerge from sequential decision regimes, continuous single-regime dynamics, or trajectories dominated by impending movement.

## How to read this mixed family

Accepted and non-accepted sibling variants coexist here. Authority applies only to the variants explicitly marked as reviewed and accepted; it does not spill across the family.

## Variant 1: Behavioral-timing consequence of a choice-contractive regime transition

### Why it matters

Demonstrating both a pre-to-post transition change in sensory sensitivity and trial-level response-time prediction beyond evidence and motor timing would connect a population-flow transition to behavioral timing rather than identifying commitment solely from changing sensory efficacy or lack of response-onset locking.

### Original and refined question

**Original Question Scientist proposal**

Do population dynamics exhibit a transition from stimulus-sensitive to choice-stabilizing organization whose timing predicts response-time variation?

**Post-novelty revised proposal**

In the dataset’s perceptual-decision population, does trial-wise entry into a choice-specific contractive population-flow regime mark a bilateral loss of sensory-evidence sensitivity and incrementally predict response time after conditioning on evidence variables and movement-onset or kinematic timing?

**Reviewed refined question**

In BWM sessions passing prespecified neural and timing-quality gates, does a response-time-blind, cross-fitted earliest sustained entry into a choice-specific contractive population-flow region precede a lower cross-validated signed-contrast sensitivity and add held-out trial-level response-time information beyond contrast, choice, and measured movement timing and kinematics?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the dataset provides sufficiently aligned population activity, sensory-evidence timing, choices, response times, and movement observations, it may support estimation of trial-wise entry into a choice-specific contractive flow region and independent tests of pre- versus post-entry evidence sensitivity and incremental response-time prediction.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The build summary reports 459 sessions, 699 insertions, 75395 units, 295920 trials, and spike times stored with 100-microsecond quantization.
  - Limitation: Build totals do not demonstrate that any selected session has sufficient cells, trials, or pre-movement time for the proposed model.
- **Unverified planning evidence:** The shared eid and trial_id keys link ephys trials carrying choice, contrastLeft, contrastRight, stimOn_times, goCue_times, firstMovement_times, response_times, and feedback times to 258614 wheel-feature trial rows with movement-onset, peak-time, direction, amplitude, mean velocity, and maximum velocity fields.
  - Limitation: The coverage query establishes field presence and linked-table grain, not usable observations after future inclusion and quality filters.
  - Limitation: Contrast is a static task-evidence proxy; this inspection does not establish a temporally varying post-entry input stream.
- **Unverified planning evidence:** The ephys dataset declares trial-level records keyed by eid and trial_id, unit metadata keyed by pid and cluster_id, and a spike store sharded by pid with delta-encoded spike times and cluster assignments.
  - Limitation: The schema establishes available surfaces but not stable flow-estimation quality for a particular session or population.
  - Limitation: This planning inspection did not load neural activity values.

### Plan at a glance

- Population and scope: Ephys sessions with trial-aligned spike shards, adequate good-unit counts, valid stimulus-to-first-movement intervals, and linked wheel features; inference is across sessions or animals after within-session trial modeling, rather than across correlated trials as if independent.
- Unit of observation: A time-binned neural population state within a behaviorally valid trial from one insertion.
- Unit of inference: Recording session or animal, with trial-level estimates summarized using hierarchical or cluster-respecting inference.
- Hierarchy and dependence: Trials are nested in sessions, sessions in subjects, and units in insertions. Fit state and predictive models within session or explicitly include session-level structure; resample and split by session and never treat bins, units, or trials as independent replications.
- Validation: Before target interpretation, use simulated trajectories with known continuous and contractive regimes to verify recovery, perturb bin width and latent dimension within prespecified ranges, test estimator reproducibility across trial splits, and require temporal ordering checks showing that the entry estimate is not constructed from response-time labels or post-response data.
- Split strategy: Use outer held-out folds grouped by session or subject for aggregate generalization and inner trial splits within each training session for state/flow fitting; all normalization, dimensionality reduction, contraction thresholds, and feature selection are fit only on the relevant training partition.
- Claim ceiling: associational

**Analysis strategy**

1. Pre-register an inclusion rule: retain only trials with valid stimulus, first-movement, response, contrast, and selected-wheel features, and retain only sessions meeting prespecified good-unit, trial-count, and usable pre-movement-window thresholds.
2. Represent signed sensory evidence as a prespecified function of contrastLeft and contrastRight, with side, absolute contrast, choice, prior probability, and trial-history terms considered as covariates rather than selected from target response-time results.
3. On training folds only, bin spikes in a fixed pre-movement window and fit a low-dimensional population-state representation separately for each eligible insertion or simultaneously recorded set; estimate local flow and a choice-conditional contraction criterion without response-time labels.
4. 4 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: A time-shifted or trial-permuted entry-time label within session, evaluated under the identical response-time model.; A post-response neural window excluded from the primary estimator, used only to confirm that the primary procedure does not accidentally rely on future data.
- Positive controls: Synthetic continuous and contractive trajectory simulations with known entry structure, used to verify method recovery before target-data interpretation.; Known alignment of spike-derived time bins to recorded trial event times, verified structurally before modeling.
- Alternative explanations: A smooth evidence transformation rather than a discrete contractive regime.; Residual movement initiation or kinematics that are not captured by wheel summaries.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- This observational dataset cannot establish that a detected population-flow feature causes response time or choice commitment.
- Static contrast is a plausible proxy for sensory evidence; it cannot by itself establish sensitivity to new sensory input after entry.
- Wheel and DLC-derived measures may not capture all covert movement preparation.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

The plan keeps the protected sequence intact: it estimates a choice-specific contractive flow entry independently of response time, tests sensory-evidence sensitivity on both sides of that estimate, and only then asks whether entry adds held-out response-time information beyond evidence and measured motor timing.

**Before any later execution**

- Unresolved planning decisions: Prespecify quality and bilateral-coverage thresholds before target-data outcome evaluation.; Choose the latent representation family and contraction metric through synthetic recovery and held-out estimator stability rather than response-time performance.; plus 1 additional item(s) in the complete dossier
- Required future skills: Leakage-safe neural population-flow estimation from delta-encoded spike shards, including choice-conditional local contraction and sustained entry-time extraction.; Grouped cross-fitted comparison of time-resolved sensory sensitivity and conditional response-time prediction with hierarchical aggregation.

### Scientific stakes

**Discriminating observation**

First estimate, independently of response time, each trial’s earliest sustained entry into a population region whose local flow converges toward the ultimately chosen state and is less displaced by subsequent sensory evidence; this choice-contractive flow-entry criterion is distinct from the cited prior’s simplified-model estimate of a coupled dynamical-regime and neural-mode commitment time. Then require sensory evidence to have demonstrably greater influence before than after the estimated entry, with observations available on both sides. Finally, require entry time to improve trial-level response-time prediction conditional on relevant evidence variables and movement-onset or kinematic timing; lack of time-locking to response onset alone is insufficient.

**What possible outcomes would mean**

- Positive pattern: A reproducible choice-contractive flow-entry time that separates stronger pre-entry from weaker post-entry sensory influence and adds response-time information beyond evidence and motor timing would support a sequential organization account and identify behavioral timing as an additional consequence of the proposed transition.
- Negative pattern: If sensory sensitivity varies smoothly without a defensible pre/post change, or flow-entry time adds no response-time information after evidence and motor timing are considered, the stronger sequential-transition account would be disfavored in favor of continuous or behaviorally nonincremental dynamics.
- Null or ambiguous pattern: If flow fields, transition times, bilateral sensitivity, or motor timing cannot be estimated stably enough to distinguish the accounts, the result would leave the regime question unresolved and would not justify interpreting the fitted boundary as commitment.

## Variant 2: Reciprocal conditional attribution of final pre-movement distributed dynamics

### Why it matters

Reciprocal conditional prediction would distinguish the functional meaning of late brain-wide dynamics without requiring a discrete decision-to-action transition or treating simple choice correlation as evidence for choice formation.

### Original and refined question

**Original Question Scientist proposal**

Are late decision-related population trajectories specifically associated with choice formation, or are they better explained as distributed preparation of measured movements?

**Post-novelty revised proposal**

In distributed forebrain populations during a two-alternative visual discrimination reported by forepaw-controlled wheel turns, does the final pre-movement population state provide incremental out-of-sample information about perceptual choice beyond measured movement trajectory, kinematics, timing, and effector, or does it instead provide reciprocal information about movement beyond choice?

**Refined-question status**

No refined question earned accepted-plan authority for this sibling.

**Reviewed planning disposition**

Rejected because a faithful operationalization was not established. Rejected for this dataset-task pairing: wheel direction is almost a deterministic encoding of nonzero choice, and the available task offers no evidenced alternative report mapping. Conditioning on movement direction therefore conditions on the choice report itself, so the proposed reciprocal choice-versus-movement attribution cannot preserve its intended contrast.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If neural recordings, trial choices, wheel behavior, pose-derived movement, and repeated choice-to-turn mappings overlap at suitable resolution, they may support conditional comparisons in a final pre-movement epoch across trials where perceptual choice varies while response movement is matched or controlled, and across trials where movement varies while choice is held fixed.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavior data contain 258614 wheel-feature trial rows from 396 sessions. The aggregate cross-tab shows that nonzero choice is almost deterministically paired with one wheel direction: choice -1 with right direction on 127289 rows and choice +1 with left direction on 129947 rows, with only sparse discordant or unknown rows.
  - Limitation: This structural diagnostic does not evaluate neural prediction or effect size.
  - Limitation: Sparse discordances may reflect errors, omissions, or feature classification and do not supply a designed independent report mapping.
- **Unverified planning evidence:** The ephys metadata supports session-level linkage to units with anatomical labels and reports 459 sessions; its insertion-count distribution is 219 sessions with one insertion and 240 with two insertions.
  - Limitation: Insertion count and unit anatomy do not establish simultaneous broad forebrain coverage or an operationally usable distributed population.

### Scientific stakes

**Discriminating observation**

Using held-out prediction or representational information rather than simple correlation, compare the incremental contribution of the final pre-movement neural state to choice beyond movement trajectory, direction, kinematics, timing, and effector, ideally where different mapping contexts permit choice variation with matched or explicitly controlled wheel movements. Reciprocally, test incremental movement prediction beyond choice within the same choice and effector. Choice-only incremental information favors choice specificity; movement-only incremental information favors preparation. If the same latent dimensions support overlapping conditional predictions, neither reciprocal increment is outcome-specific, and reproducible residual joint structure remains after conditioning on both measured choice and movement, the data do not justify assigning a distinct decision or motor function.

**What possible outcomes would mean**

- Positive pattern: Reliable incremental choice information beyond controlled movement features, without a comparable movement-only explanation, would support interpreting the final pre-movement distributed state as retaining choice-specific organization rather than merely marking a choice-to-action transition.
- Negative pattern: Reliable incremental prediction of movement beyond choice, with negligible incremental choice information after movement control, would favor an embodied movement-preparation interpretation of the late distributed state.
- Null or ambiguous pattern: If conditional choice and movement predictions overlap, neither provides reliable reciprocal incremental information, or residual joint structure cannot be separated into outcome-specific components, the functional assignment would remain unresolved and a shared-latent-state account would remain viable.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family has an evidence-backed, leakage-conscious plan for variant 01 that preserves its required sequence: response-time-blind flow-entry estimation, bilateral pre/post sensory-sensitivity assessment, and held-out conditional response-time prediction. Variant 02 has an honest operationalization-failure outcome rather than an unsupported pending analysis. Remaining choices are appropriate pre-execution locks, not planning-stage scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Fix session/trial quality and bilateral-coverage gates before target-data outcome evaluation.
- **Pre execution lock:** Fix the latent-state/flow estimator and sustained-entry definition using synthetic recovery and held-out estimator stability without optimizing response-time associations.
- **Pre execution lock:** Fix the population definition for each analysis unit (single insertion versus contemporaneous multi-insertion set) before execution.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family plan is sound: at least one variant (var-01) has a fully evidence-grounded, leakage-conscious plan that preserves the protected sequence (response-time-blind flow-entry estimation, bilateral pre/post sensory-sensitivity assessment, then held-out incremental response-time prediction), with explicit alternative explanations, positive/negative controls, an associational claim ceiling, and honest interpretation limits. The sibling variant (var-02) receives an honest, evidence-backed operationalization-failure rejection grounded in the near-deterministic choice-wheel coupling shown in the inspected evidence, which is a legitimate dataset-grounded rejection rather than a pending or unsupported outcome. Sibling separation is intact: var-01 targets a discrete flow-entry transition and changing sensory sensitivity, while var-02 targeted reciprocal choice/movement information without requiring a transition; neither plan collapses the two forbidden semantic merges. The three Owner-classified issues (quality/coverage gates, estimator/entry-definition freezing, population-unit definition) are all bounded execution-stage choices appropriately deferred to pre-execution locking rather than scientific blockers, since none of them undermine the plan's ability to credibly answer the protected question as currently specified. No new scientific blocker or hard-boundary issue is identified at this planning stage.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
