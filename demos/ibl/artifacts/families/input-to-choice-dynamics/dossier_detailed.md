# How input influence changes during a decision — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Mixed family: accepted and non-accepted sibling variants**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Develops two distinct dynamical accounts of decision formation: a within-episode change in input sensitivity and a distributed transformation of task information across processing levels.

The scientific tension is:

Changing neural trajectories may mark a genuine transition in how inputs influence decisions, or may reflect continuous input-driven evolution and distributed transformation without a discrete regime change.

## How to read this mixed family

Accepted and non-accepted sibling variants coexist here. Authority applies only to the variants explicitly marked as reviewed and accepted; it does not spill across the family.

## Variant 1: Within-episode sensitivity-transition branch

### Why it matters

The question requires a candidate dynamical feature to have an independent behavioral consequence rather than treating trajectory shape as mechanistic evidence by itself.

### Original and refined question

**Original Question Scientist proposal**

Do decision-related population trajectories exhibit a reproducible change in input sensitivity whose timing predicts subsequent choice stability and response time?

**Refined-question status**

No refined question earned accepted-plan authority for this sibling.

**Reviewed planning disposition**

Rejected because a faithful operationalization was not established. The available trial surface supports time-resolved responses to the original contrast and response-time outcomes, but not the invariant's discriminating requirement that an independently varying later task input be less influential after a candidate transition. Recasting the original stimulus effect as a later-input consequence would change the protected contrast.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Neural activity, sensory stimuli, choices, and response times may allow later planning of input-sensitivity and behavioral-consequence comparisons if detailed timing is adequate.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The trial table is keyed by eid and trial_id and documents choice, feedbackType, contrastLeft, contrastRight, stimOn_times, goCue_times, firstMovement_times, response_times, feedback_times, goCueTrigger_times, stimOff_times, and bwm_include.
  - Limitation: Footer metadata establishes available fields but not completeness or analytic eligibility of any specific session.
  - Limitation: The documented task-input fields are left and right contrast at stimulus onset; no separately documented later varying task-input field was found in this bounded surface.
- **Unverified planning evidence:** Trial behavior features are keyed by eid and trial_id and include signed_contrast, choice_label, correct, reaction_time, movement_time, and stim_to_feedback_time.
  - Limitation: These trial summaries do not rule out movement or event-timing confounding.
- **Unverified planning evidence:** Wheel trial features are keyed by eid, trial_id, and window_spec and document wheel_present, movement_onset_time, movement_peak_time, movement_direction, movement_amplitude, mean_velocity, and max_velocity.
  - Limitation: Wheel presence is explicit and incomplete coverage must be handled through prespecified complete-case and missingness sensitivity analyses.
  - Limitation: Wheel summaries are covariates and cannot rule out all unmeasured movement confounding.

### Scientific stakes

**Discriminating observation**

A regime-change account would be favored if an independently detected trajectory change predicts reduced sensitivity to later task input and increased choice stability or altered response timing beyond movement and event-timing explanations.

**What possible outcomes would mean**

- Positive pattern: A positive result would support a predictive transition-linked account of decision stabilization, without establishing a specific circuit mechanism.
- Negative pattern: A negative result would favor continuous input-driven or movement-linked explanations.
- Null or ambiguous pattern: A null result would indicate that any transition is behaviorally non-discriminating or not reliably identifiable.

## Variant 2: Cross-region transformation branch

### Why it matters

This tests the structure and consequence of distributed transformation while avoiding causal transmission claims from temporal ordering alone.

### Original and refined question

**Original Question Scientist proposal**

Does decision information undergo a distributed geometric transformation across brain regions, from stimulus-aligned organization toward choice- and response-aligned organization?

**Reviewed refined question**

Across preregistered atlas-defined region groups, do trial-aligned population geometries show an ordered shift from signed-contrast alignment toward choice and response-time alignment that predicts behavior beyond event timing and measured movement?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Broad anatomical sampling with task, choice, response-time, and pose information may support later planning of cross-region representational comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The trial table is keyed by eid and trial_id and documents choice, feedbackType, contrastLeft, contrastRight, stimOn_times, goCue_times, firstMovement_times, response_times, feedback_times, goCueTrigger_times, stimOff_times, and bwm_include.
  - Limitation: Footer metadata establishes available fields but not completeness or analytic eligibility of any specific session.
  - Limitation: The documented task-input fields are left and right contrast at stimulus onset; no separately documented later varying task-input field was found in this bounded surface.
- **Unverified planning evidence:** Trial behavior features are keyed by eid and trial_id and include signed_contrast, choice_label, correct, reaction_time, movement_time, and stim_to_feedback_time.
  - Limitation: These trial summaries do not rule out movement or event-timing confounding.
- **Unverified planning evidence:** Unit metadata links pid and eid to cluster_id and documents atlas_id, acronym, beryl_id, beryl_acronym, coordinates, spike_count, and firing_rate, providing anatomy labels for joining population summaries to trial-aligned neural data.
  - Limitation: Atlas and Beryl labels identify anatomical assignment but are a plausible proxy, not an exact measurement of functional processing level.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Included Brain-Wide Map ephys sessions with linked task trials, usable insertions and units, and sufficient per-session trial coverage after prespecified quality rules; wheel-control analyses are restricted to trials with documented wheel presence and compared with all-session analyses.
- Unit of observation: A trial-by-time-bin population-response vector within one anatomy-defined region group and recording insertion.
- Unit of inference: Session and subject, with insertion and trial repetition modeled as nested dependence rather than independent replicates.
- Hierarchy and dependence: Fit population summaries within insertion and session, then estimate regional-pattern contrasts with hierarchical or cluster-robust session/subject aggregation; preserve all trials from a session within the same validation fold.
- Validation: Use nested session/subject-respecting cross-validation, permutation tests that preserve session and trial structure, and synthetic method-recovery simulations spanning ordered transformation, broad mixed representation, unequal unit yield, and movement-locked timing. Lock preprocessing, region taxonomy, geometry metric, and folds before evaluating target contrasts.
- Split strategy: Outer folds are grouped by session and, where sample support permits, subject; all bins and trials from a session remain together. Inner folds select only nuisance regularization or low-dimensional rank under fixed candidate grids, never the region ordering or scientific target.
- Claim ceiling: associational

**Analysis strategy**

1. Prespecify comparable atlas/literature-defined sensory, association, and motor-region groups and minimum quality/trial-count rules without inspecting representational outcomes.
2. Construct trial-aligned population vectors in fixed stimulus-to-response and response-aligned windows using only retained units and documented event times.
3. Estimate cross-validated geometry alignment separately for signed contrast, choice, and response time using held-out trials, with model definitions fixed before outcome inspection.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permute trial labels within session and contrast strata to verify that the complete pipeline does not recover an ordered alignment profile from label-free data.; Use event-time and movement-only feature sets as nuisance baselines; an apparent transformation reproduced by these baselines weakens the neural-computation interpretation.
- Positive controls: Recover signed-contrast alignment in early stimulus-aligned windows from a held-out trial analysis, subject to prespecified reliability thresholds.; Recover wheel movement timing from documented wheel summaries in response-aligned windows when wheel data are available.
- Alternative explanations: Shared event locking or reaction-time differences can create apparent sequential regional changes.; Unequal unit yield, firing rates, or measurement sensitivity can alter geometry estimates by region.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- The observational dataset can support predictive or associational representational claims, not causal routing or transmission claims.
- A processing-level ordering is a theory-guided anatomical proxy requiring explicit approval and sensitivity to alternative taxonomies.
- Planning evidence establishes data surfaces, not a scientific result.

**Why the plan serves the question**

The plan preserves the variant's spatial target contrast by comparing independently defined stimulus, choice, and response geometries across anatomically distributed groups; it does not substitute a within-trial regime transition or make causal routing claims.

**Before any later execution**

- Unresolved planning decisions: Approve or document the preregistered mapping from atlas labels to processing-level groups before execution.; Set prespecified coverage and reliability thresholds using metadata and synthetic recovery checks, not target alignment outcomes.
- Required future skills: Trial-aligned spike-shard decoding and binning with leakage-safe grouped resampling.; Cross-region representational-geometry estimation with balanced sampling and hierarchical aggregation.

### Scientific stakes

**Discriminating observation**

A transformation account would be favored if independently defined task geometries show a reproducible shift in alignment across processing levels that predicts behavior beyond timing and pose controls.

**What possible outcomes would mean**

- Positive pattern: A positive result would support a predictive distributed-transformation account of decision information.
- Negative pattern: A negative result would favor broad replication, local specialization without an ordered transformation, or confounded temporal ordering.
- Null or ambiguous pattern: A null result would leave the spatial organization of decision transformation unresolved because of weak comparability or mixed representations.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family is handled honestly: the later-input sensitivity variant is rejected because the supplied trial surface lacks an independently varying later input, while the distributed-geometry variant retains its distinct spatial-transformation question, associational claim ceiling, appropriate dependence structure, and timing/movement alternatives. Remaining choices are execution locks rather than scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Before execution, document the atlas/literature mapping from anatomical labels to ordered processing-level groups, the geometry specification, and outcome-independent coverage and reliability rules; retain the stated unordered-region and balanced-sampling sensitivity analyses.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

This round-zero family plan is handled honestly. Variant-01 (within-episode sensitivity transition) is transparently rejected because the bounded trial surface documents only a single contrast input at stimulus onset with no independently varying later task input; recasting the stimulus effect as a later-input consequence would violate the protected contrast and the family's forbidden-merge rule. Variant-02 (distributed geometric transformation) retains its distinct spatial target contrast, an associational claim ceiling, session/subject-respecting nested cross-validation, permutation and synthetic-recovery controls, and timing/movement nuisance baselines. Sibling separation is preserved and…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
