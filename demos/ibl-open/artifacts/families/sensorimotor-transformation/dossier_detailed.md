# Population geometry of brain-wide sensorimotor transformation — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

A family asking whether sensory-to-choice transformation is organized as invariant shared geometry or region-specific transformation, with separate geometry-invariance and predictive-routing variants.

The scientific tension is:

Brain-wide evidence and preparation signals may reflect a shared population organization propagated across regions, region-specific transformations, or common task and movement inputs; broad encoding alone does not distinguish these accounts.

## Variant 1: Predictive-routing variant

### Why it matters

A predictive comparison can constrain distributed-routing accounts while explicitly avoiding causal claims from temporal association.

### Original and refined question

**Original Question Scientist proposal**

Do time-varying cross-region population relationships predict the transition from sensory evidence to movement preparation better than independent local representations or common task inputs?

**Reviewed refined question**

Across prespecified simultaneously recorded region pairs, does an earlier source-region population state improve held-out prediction of a later pre-first-movement target-region state beyond target information, task information, trial history, and measured movement information that were all available no later than the source bin?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Time-aligned population, stimulus, choice, response-time, and movement measurements may support later planning of predictive contrasts among routing accounts.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** Among 459 ephys sessions, 240 have two insertions and 452 have at least two Beryl regions represented by label-1 units; all 459 sessions have at least 100 BWM-included trials, with 196574 included trials overall.
  - Limitation: Aggregate coverage does not verify sufficient units in each proposed region pair after all quality, trial, and movement-availability filters.
  - Limitation: No neural responses, cross-region prediction values, or behavioral outcomes were computed.
- **Unverified planning evidence:** The ephys trial table provides stimulus, go-cue, first-movement, response, and feedback times with choice and contrast fields; unit metadata provides atlas and Beryl region labels; behavioral products provide reaction and movement times, wheel movement direction and velocity summaries, camera-specific DLC summaries, event-aligned summaries, and movement epochs.
  - Limitation: Feature-table summaries do not replace a prespecified neural population-state construction from the spike store.
  - Limitation: Wheel is present for 458 sessions and DLC coverage is camera-specific, requiring availability-aware covariate rules.
- **Unverified planning evidence:** The behavior dataset declares trial-aligned, wheel, DLC, event-aligned, movement-state, and quiescence-state products keyed by eid and trial_id, providing measured task and movement covariate surfaces that can be joined to ephys trials by those keys.
  - Limitation: Availability differs by session and camera, so complete-case requirements must be specified before execution.
  - Limitation: These products are measured covariates and cannot rule out unmeasured common inputs.
- 1 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: BWM ephys sessions with prespecified multi-region pair coverage, retained label-1 units, BWM-included trials, and a source-bin covariate-availability tier. Inference generalizes across eligible sessions and region pairs, not to physical communication.
- Unit of observation: A trial-by-time-bin regional population-state vector, with each source bin preceding its target bin by a prespecified lag.
- Unit of inference: Session-level and region-pair-level held-out predictive contrasts, combined with hierarchical uncertainty that accounts for repeated pairs within sessions and subjects.
- Hierarchy and dependence: Neurons are nested in insertion and region; bins are nested in trials; trials are nested in sessions and subjects. Split complete trials or blocked trial groups before model fitting, retain all bins of a held-out trial together, and use hierarchical or cluster-resampled uncertainty at session and subject levels.
- Validation: Before target evaluation, verify spike-shard decoding against metadata cluster counts on a small non-target structural sample; test synthetic recovery of a known lagged incremental-prediction signal; verify no trial or time-bin leakage across splits; and audit every primary covariate's timestamp and aggregation window to confirm it ends at or before the source bin.
- Split strategy: Primary evaluation uses grouped held-out trials within session, with all bins from a trial confined to one fold. Secondary generalization leaves out whole sessions and, where feasible, subjects. Region-pair and lag definitions are fixed from anatomy and task timing before fitting.
- Claim ceiling: predictive

**Analysis strategy**

1. Restrict to BWM-included trials in sessions meeting prespecified simultaneous region-pair and unit-count thresholds, with sensitivity analyses across reasonable thresholds fixed before target evaluation.
2. Decode only required spike shards to create quality-filtered, variance-stabilized, event-aligned regional population states in prespecified time bins spanning evidence and pre-first-movement epochs.
3. For each directed region pair and lag, construct a primary baseline for the later target state from target-region state history ending at the source bin, signed contrast and task-event indicators already realized by the source bin, prior-trial history, and wheel, DLC, movement-state, or quiescence features whose recorded window ends no later than the source bin.
4. 4 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Time-shift or trial-permute source population states while preserving within-region autocorrelation and trial structure.; Use future source bins that cannot precede the target bin under the prespecified temporal ordering.; plus 1 additional item(s) in the complete dossier
- Positive controls: Verify recovery of known task-event alignment in event-response features and decoded population states without using it to select region pairs or lags.; Verify that target-region history ending at the source bin improves held-out target-state prediction over an intercept-only baseline.
- Alternative explanations: Shared sensory, task, or causal-past overt-movement inputs can induce cross-region temporal prediction.; Event-locking, temporal filtering, or region-specific signal quality can create apparent directionality.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- Incremental temporal prediction is not evidence of physical communication or causal routing.
- The pre-first-movement state is an accepted operational proxy for movement preparation, not a direct latent measurement.
- Primary causal-past adjustment reduces only measured pre-source common-input explanations; unmeasured or fast shared inputs remain possible.
- 2 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

The revised primary estimand directly tests the invariant's discriminating observation: whether earlier cross-region population information adds held-out prediction of a later preparation-related state beyond independent local representation and common inputs that were available at the source time. The revision preserves the predictive, non-causal routing contrast and makes no material change to the central phenomenon, target contrast, claim level, population scope, or discriminating observation.

**Before any later execution**

- Unresolved planning decisions: Prespecify region-pair and minimum-unit rules.; Prespecify the primary temporal bin, lag grid, local-history window, target-state representation, causal-past movement-feature windows, and covariate completeness tier.
- Required future skills: Decode BWM delta-tick spike shards and map local cluster indices to unit metadata without materializing the full spike corpus.; Construct leakage-safe regional population time series, timestamp causal-past behavioral features, and fit hierarchical held-out incremental-prediction models with time-shift controls.

### Scientific stakes

**Discriminating observation**

Cross-region population state information that adds held-out prediction of later preparation-related states beyond local history, task inputs, and measured movement would favor a routing-like predictive account.

**What possible outcomes would mean**

- Positive pattern: Incremental prediction would support a temporally organized distributed-transformation description, without establishing physical communication.
- Negative pattern: No incremental prediction would favor independent-local or common-input explanations over routing-like organization.
- Null or ambiguous pattern: Symmetric or unstable prediction would leave direction and organization unresolved.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The revision resolves the prior temporal-ordering problem: the primary baseline is restricted to information available by the source bin, while outcome-realized and post-source behavioral variables are explicitly secondary descriptive analyses. The plan now supports the intended predictive, non-causal contrast between temporally ordered cross-region prediction, independent local representation, and measured common-input accounts. Remaining choices are pre-execution locks, not planning blockers.

Retained changes and locks:

- **Pre execution lock:** Before execution, fix region-pair inclusion, unit-count, bin-width, lag-grid, local-history, target-state representation, and covariate-completeness rules without consulting target predictive performance.
- **Pre execution lock:** Before execution, define the primary causal-past movement-feature windows and missing-data tier, ensuring every primary behavioral feature ends at or before the source-bin timestamp.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The revised plan directly resolves the round-0 scientific blocker: the primary estimand now restricts every baseline covariate (target-state history, task/contrast indicators, prior-trial history, wheel/DLC/movement-state features) to information available at or before the source bin, and explicitly relegates outcome-realized choice, reaction-time, response, and post-source movement adjustments to secondary descriptive analyses that cannot override the primary temporal-ordering claim. This preserves the intended predictive, non-causal contrast between temporally ordered cross-region prediction, independent local representation, and measured common-input accounts, with an appropriate predictive claim ceiling, explicit interpretation limits against communication/causal-routing overclaim, and both positive and negative controls (time-shift/permutation, non-preparation target window, event-alignment recovery). The two remaining Owner issues concern bounded pre-execution parameter choices (inclusion thresholds, bin/lag/window specification, missing-data tiers) that must be fixed before running the analysis but do not themselves threaten the validity of the current planning product; they are pre-execution locks, not scientific blockers, and are carried forward rather than requiring another revision round.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
