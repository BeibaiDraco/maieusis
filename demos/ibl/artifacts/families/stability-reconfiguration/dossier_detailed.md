# Stable decisions under changing population organization — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether stable decision-related behavior is associated with preserved relational geometry or with context-sensitive reconfiguration of neural trajectories.

The scientific tension is:

Behavior may remain stable because task-relevant geometric relations are preserved, or because neural dynamics reconfigure while maintaining an effective readout; descriptive geometry alone cannot distinguish these accounts.

## Variant 1: Cross-context invariance branch

### Why it matters

This would clarify which population-level properties are plausible carriers of generalizable decision information while avoiding the assumption that stable centroids or individual-unit tuning define the code.

### Original and refined question

**Original Question Scientist proposal**

Across subjects, sessions, and laboratories, is stable decision behavior predicted more strongly by preservation of relational population geometry than by preservation of particular activity patterns?

**Reviewed refined question**

Across independently sampled BWM insertion populations from subjects, sessions, and laboratories, does held-out preservation of task-state relational geometry predict cross-context decision consistency more strongly than activity-pattern similarity?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

The dataset narrative suggests comparisons across subjects, sessions, laboratories, and brain regions may allow later planning of a generalization test, subject to verification of comparable task structure and recordings.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The snapshot reports 459 sessions, 699 insertions, 75,395 units, 295,920 trials, 2,066,041 events, and a compressed spike store covering all 699 insertions.
  - Limitation: Counts are dataset documentation, not a test of usable coverage after prespecified inclusion criteria.
  - Limitation: The evidence does not establish repeated recordings of identical neurons across sessions.
- **Unverified planning evidence:** Behavior tables share eid and trial_id keys with the ephys trial table. Trial behavior features provide signed contrast, choice label, correctness, reaction time, movement time, and stimulus-to-feedback time. Wheel features provide movement onset, peak, direction, amplitude, and velocity summaries; DLC features provide camera-specific feature mean and peak summaries. The behavior build report records wheel data for 396 sessions and DLC data for 453 sessions.
  - Limitation: Wheel and DLC availability is incomplete and camera-specific, so pose-adjusted analyses require a prespecified complete-case and missingness sensitivity strategy.
  - Limitation: Feature summaries are not a substitute for full pose trajectories.
- **Unverified planning evidence:** Ephys tables are keyed by eid for sessions and trials, by pid for insertions, and by pid plus cluster_id for units; the spike store is keyed by pid. Session metadata include subject, date, lab, trial counts, and insertion counts. Trial metadata include choice, feedbackType, probabilityLeft, left and right contrasts, and stimulus, cue, movement, response, and feedback times. Unit metadata include quality label, anatomical annotations, and firing rate.
  - Limitation: A pid-level spike population is an insertion-specific sample rather than a longitudinally identified cell population.
  - Limitation: The schema establishes field availability but not nonmissingness or balance for each proposed stratum.

### Plan at a glance

- Population and scope: Good-quality units from pid-keyed insertions in the BWM ephys snapshot, grouped only across contexts with prespecified shared task-state coverage; contexts are subject, session, laboratory, and anatomical grouping where supported by the metadata.
- Unit of observation: A held-out trial representation within a pid-keyed insertion population and prespecified task-state cell.
- Unit of inference: Independent context pair, with uncertainty clustered by subject and session and evaluated by leave-context-out resampling.
- Hierarchy and dependence: Trials nest in sessions, sessions nest in subjects and laboratories, and units nest in insertions; fit hierarchical or cluster-robust models and never treat units or trials as independent cross-context replications.
- Validation: Use nested leave-session, leave-subject, and leave-laboratory-out validation; define state geometry only in the training partition; use label and state-permutation method-recovery checks that preserve within-context dependence.
- Split strategy: Split by eid or broader context before constructing centroids and tuning representation dimensionality; do not allow trials from one session in both geometry definition and cross-context evaluation folds.
- Claim ceiling: predictive

**Analysis strategy**

1. Define task-state centroids from training trials using signed contrast, choice, correctness, and prespecified decision epoch bins.
2. Compare contexts with an identity-free relational metric such as cross-validated representational-distance correlation or alignment of state-centered subspaces; use matched numbers of units and trials.
3. Compute an activity-pattern similarity baseline using the same held-out state cells and match its dimensionality and reliability correction to the relational metric.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Geometry after permutation of task-state labels within context.; A context-matched nuisance representation based on baseline firing or unit count alone.
- Positive controls: Recovery of within-context task-state structure from held-out trials before cross-context interpretation.
- Alternative explanations: Shared sensory inputs or standardized task structure produce apparent relational similarity.; Sampling, unit quality, or region composition differences explain cross-context differences.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Observational recordings cannot establish that geometry causally supports readout.
- The design evaluates comparable insertion populations, not preservation of the same neurons across time.

**Why the plan serves the question**

It preserves the variant's cross-context discriminator by directly comparing relational geometry with particular activity-pattern similarity on independently held-out behavior, while explicitly allowing the flexible-readout interpretation if geometry fails to generalize.

**Before any later execution**

- Unresolved planning decisions: Primary anatomical grouping and state-cell minimum require prespecification from metadata and resource constraints, not target outcomes.
- Required future skills: Decode and time-align the compressed blosc pid-keyed spike shards without materializing the full store.; Run leakage-safe cross-context representational-geometry and hierarchical validation workflows.

### Scientific stakes

**Discriminating observation**

Independent comparisons would favor geometric conservation if preservation of task-state relations predicts out-of-context behavioral consistency after accounting for overall activity similarity and reliability; preserved behavior with unreproducible geometry would favor flexible-readout accounts.

**What possible outcomes would mean**

- Positive pattern: A positive result would support a predictive claim that relational geometry, rather than specific activity patterns, marks a generalizable population code.
- Negative pattern: A negative result would weaken geometry-preservation accounts and elevate flexible readout or context-specific coding explanations.
- Null or ambiguous pattern: An indeterminate association would imply that geometric preservation and behavioral stability cannot be separated at the available reliability or contextual scale.

## Variant 2: Within-episode reconfiguration branch

### Why it matters

The question separates stability of a readout-relevant structure from stability of the full neural trajectory and links representational geometry to a concrete predictive consequence.

### Original and refined question

**Original Question Scientist proposal**

Within decision episodes, do population trajectories reconfigure with task and behavioral state while preserving a stable decision-relevant subspace?

**Reviewed refined question**

Within BWM mouse decision episodes, do full insertion-population trajectories vary with sensory and behavioral state while a cross-validated decision-relevant subspace remains stable and predicts choice beyond measured movement and pose summaries?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Joint neural, task, decision, response-time, and pose measurements may support later planning of trajectory and readout comparisons, but detailed timing and joint coverage require verification.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The snapshot reports 459 sessions, 699 insertions, 75,395 units, 295,920 trials, 2,066,041 events, and a compressed spike store covering all 699 insertions.
  - Limitation: Counts are dataset documentation, not a test of usable coverage after prespecified inclusion criteria.
  - Limitation: The evidence does not establish repeated recordings of identical neurons across sessions.
- **Unverified planning evidence:** Behavior tables share eid and trial_id keys with the ephys trial table. Trial behavior features provide signed contrast, choice label, correctness, reaction time, movement time, and stimulus-to-feedback time. Wheel features provide movement onset, peak, direction, amplitude, and velocity summaries; DLC features provide camera-specific feature mean and peak summaries. The behavior build report records wheel data for 396 sessions and DLC data for 453 sessions.
  - Limitation: Wheel and DLC availability is incomplete and camera-specific, so pose-adjusted analyses require a prespecified complete-case and missingness sensitivity strategy.
  - Limitation: Feature summaries are not a substitute for full pose trajectories.
- **Unverified planning evidence:** Ephys tables are keyed by eid for sessions and trials, by pid for insertions, and by pid plus cluster_id for units; the spike store is keyed by pid. Session metadata include subject, date, lab, trial counts, and insertion counts. Trial metadata include choice, feedbackType, probabilityLeft, left and right contrasts, and stimulus, cue, movement, response, and feedback times. Unit metadata include quality label, anatomical annotations, and firing rate.
  - Limitation: A pid-level spike population is an insertion-specific sample rather than a longitudinally identified cell population.
  - Limitation: The schema establishes field availability but not nonmissingness or balance for each proposed stratum.

### Plan at a glance

- Population and scope: Trial-aligned good-quality units within pid-keyed BWM insertion populations, restricted to sessions with documented trial timing; wheel-adjusted analyses use available wheel sessions and pose-adjusted sensitivity analyses use available DLC sessions.
- Unit of observation: One trial's time-binned population trajectory within a pid-keyed insertion.
- Unit of inference: Insertion population and session, with trial-level estimates aggregated or hierarchically modeled rather than treated as independent populations.
- Hierarchy and dependence: Time bins and trials are repeated within insertion, insertions are nested in sessions, and sessions are nested in subject and lab; cross-validation and uncertainty resampling remain grouped at insertion and session levels.
- Validation: Use trial splits blocked within insertion, nested selection of dimensionality and epoch widths, and held-out task-state strata. Verify method recovery with simulated rotations that preserve a planted readout and with null labels that preserve timing and movement distributions.
- Split strategy: Separate trials used to define the decision-relevant subspace from trials used to estimate reconfiguration, stability, and choice prediction; retain all preprocessing choices inside the training fold.
- Claim ceiling: predictive

**Analysis strategy**

1. Align bounded spike reads to stimulus, cue, first movement, and response times, then construct variance-stabilized population trajectories with dimensionality selected only inside training folds.
2. Quantify full-space trajectory reconfiguration across prespecified sensory, choice, reaction-time, and movement-state strata using cross-validated trajectory-distance measures.
3. Define a decision-relevant subspace on training trials and test its reproducibility across behavioral and sensory strata on held-out trials.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Choice-label permutation within matched sensory and movement strata.; A time-shifted or pre-stimulus trajectory control matched for firing-rate scale.
- Positive controls: Recovery of known event-aligned population modulation from held-out trials before testing the focal contrast.
- Alternative explanations: Input contrast or prior probability causes both trajectory changes and choice.; Response timing, wheel movement, or pose accounts for apparent reconfiguration.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- This observational plan cannot establish a causal readout mechanism.
- DLC summary features cannot rule out all embodied-state explanations, especially where cameras are unavailable.

**Why the plan serves the question**

It keeps the within-episode target distinct from cross-context conservation by asking whether trajectory reconfiguration and an independently validated decision-relevant subspace coexist, while treating sensory and embodied state as live competing explanations.

**Before any later execution**

- Unresolved planning decisions: The primary decision epoch and bin width must be fixed through task timing and synthetic recovery checks before outcome evaluation.; The complete-case pose-adjusted analysis and the wheel-only primary analysis must be prespecified according to availability.
- Required future skills: Decode and time-align compressed spike shards for prespecified trial windows.; Implement nested, grouped trajectory and subspace validation with movement and pose covariates.

### Scientific stakes

**Discriminating observation**

Evidence would favor reconfiguration around a stable readout if full trajectories vary with context or state while an independently defined decision-relevant relation remains reproducible and predicts choices beyond measured pose and input differences.

**What possible outcomes would mean**

- Positive pattern: A positive result would support a predictive organization in which flexible dynamics and stable readout geometry coexist.
- Negative pattern: A negative result would favor fixed-dynamics, fully context-specific, or embodied-state explanations over stable-subspace reconfiguration.
- Null or ambiguous pattern: A null result would leave open whether readout instability is biological or reflects insufficient temporal or population reliability.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct protected contrasts and provide credible, non-executable predictive analysis routes using the supplied ephys and behavior schema evidence. The plan uses held-out, grouped validation; distinguishes independently sampled populations from longitudinally identified neurons; states observational limits; and treats sensory and embodied-state alternatives as active competing explanations. Remaining choices are appropriate pre-execution locks rather than deficiencies in the planning dossier.

Retained changes and locks:

- **Pre execution lock:** Before outcome evaluation, prespecify minimum task-state-cell trial counts, minimum good-unit inclusion criteria, the primary shared anatomical grouping, and the wheel-only primary versus pose-adjusted sensitivity-analysis strategy based on documented covariate availability.
- **Pre execution lock:** Before outcome evaluation, prespecify the primary decision epoch and bin width for the within-episode trajectory and subspace analysis using task timing and synthetic recovery checks.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variant plans preserve their distinct protected contrasts and provide credible, non-executable, leakage-safe predictive routes grounded in the supplied ephys/behavior schema and structure evidence. Variant 01 targets cross-context conservation using identity-free relational metrics with an explicit activity-pattern-similarity competitor and hierarchical leave-context-out validation; variant 02 targets within-episode trajectory reconfiguration versus a stably validated decision subspace with sensory, timing, wheel, and DLC controls. Sibling separation is honored: cross-context vs within-episode discriminators are not merged, and each plan explicitly disclaims the other's target. Claim…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
