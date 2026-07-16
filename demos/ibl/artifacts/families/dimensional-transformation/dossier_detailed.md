# Expansion and compression of decision geometry — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether population dimensionality changes serve distinct computational roles: separating confusable task states or compressing variable activity into behaviorally stable decision structure.

The scientific tension is:

Dimensional changes may implement task-relevant expansion or compression, or may instead reflect population size, reliability, heterogeneous pooling, and other measurement properties.

## Variant 1: Expansion-for-separation branch

### Why it matters

The question links dimensional expansion to a specific predictive consequence—state separation—rather than treating dimensionality as intrinsically beneficial.

### Original and refined question

**Original Question Scientist proposal**

Is transient expansion of population geometry associated with improved separation of sensory-decision states that would otherwise be confusable?

**Reviewed refined question**

Within independently analyzed BWM insertions, does a transient increase in trial-aligned population dimensionality precede or accompany improved separation of independently defined confusable stimulus-decision states and greater held-out decision consistency beyond movement, activity, and reliability alternatives?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Task stimuli, decisions, response times, pose, and neural populations may permit later planning of state-separation comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The companion BWM behavior release has trial-level stimulus contrast, choice, correctness, event timing, wheel summaries, and camera-level pose magnitude summaries keyed by eid and trial_id, providing documented controls for task state and movement alternatives.
  - Limitation: Wheel and pose availability is partial by session and must be handled by prespecified complete-case and missingness sensitivity analyses.
  - Limitation: Pose summaries are compact magnitude-like proxies rather than full pose trajectories.
- **Unverified planning evidence:** The local BWM ephys release documents 459 sessions, 699 insertions, 75,395 units, 295,920 trials, and per-insertion spike shards with 100-us time quantization; this supports a future trial-aligned, within-insertion population-geometry analysis.
  - Limitation: The summary establishes availability and aggregate scale, not per-insertion unit yield or trial balance for any prespecified analysis subset.
  - Limitation: No neural outcomes or dimensionality estimates were inspected.

### Plan at a glance

- Population and scope: Quality-screened BWM ephys insertions with prespecified unit and matched-trial coverage; inference is across insertions nested in sessions, subjects, laboratories, and regions, not individual neurons or a universal code.
- Unit of observation: A prespecified trial-by-time-bin population response vector within one insertion.
- Unit of inference: An insertion-level estimate with hierarchical aggregation across session, subject, laboratory, and region.
- Hierarchy and dependence: Keep all bins and trials from an insertion in the same fold; use insertion-clustered or hierarchical uncertainty and leave whole sessions or subjects out for transfer checks.
- Validation: Use synthetic populations to recover known rank changes and null rotations, verify fold isolation, and audit state matching and eligibility before target fitting.
- Split strategy: Use blocked trial folds within insertion and leave-session or leave-subject-out folds for generalization; fit every transformation and nuisance scale in training folds only.
- Claim ceiling: predictive

**Analysis strategy**

1. Define confusable states before neural fitting by matching stimulus evidence and timing while contrasting decision labels only where both states meet coverage rules.
2. Estimate time-resolved effective dimensionality on training trials only after equalizing trial counts across compared states.
3. Estimate held-out state separation with a cross-validated distance or decoder and model held-out decision consistency from independently estimated expansion.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Time-shifted geometry labels preserving marginal activity but breaking trial correspondence.; A matched nondecision state contrast.
- Positive controls: Recovery of simulated rank changes.; Stimulus-side separation in stimulus-aligned windows.
- Alternative explanations: Unit yield, firing rates, and reliability can inflate apparent dimensionality.; Wheel and pose-related activity can create task-correlated dimensions without a state-separation role.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Observational data cannot show that expansion causes decisions or separation.
- Compact movement features may leave residual motor or arousal confounding.

**Why the plan serves the question**

It preserves the expansion-versus-epiphenomenon tension by testing state separation and decision consistency while comparing population-size, reliability, and movement explanations.

**Before any later execution**

- Unresolved planning decisions: Lock bin width, smoothing, estimator family, and coverage minimum using synthetic and structural criteria before target analysis.
- Required future skills: Leakage-safe BWM compressed-spike trial binning with hierarchical resampling.

### Scientific stakes

**Discriminating observation**

The functional account would be favored if independently estimated expansion precedes or accompanies improved separation and predicts decision consistency beyond pose, aggregate activity, and reliability controls.

**What possible outcomes would mean**

- Positive pattern: A positive result would support a predictive role for transient geometric expansion in state separation.
- Negative pattern: A negative result would weaken functional-expansion accounts and favor epiphenomenal or measurement explanations.
- Null or ambiguous pattern: A null result would suggest that dimensionality and state separation cannot be distinguished reliably or are not systematically related.

## Variant 2: Compression-for-generalization branch

### Why it matters

This distinguishes behaviorally useful compression from generic low dimensionality and asks whether informative failure reveals boundaries of generalization.

### Original and refined question

**Original Question Scientist proposal**

Is compression into a lower-dimensional decision geometry associated with stable readout across subjects, sessions, or laboratories despite heterogeneous neural activity?

**Reviewed refined question**

Does a compact decision-relevant geometry learned independently in BWM source contexts support held-out decision readout in new sessions, subjects, or laboratories more reliably than matched full-rank, dominant-variance, or context-specific alternatives?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Comparisons across subjects, sessions, laboratories, and regions may allow later planning of whether compact decision geometry generalizes across heterogeneous activity patterns.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavior companion release reports 459 sessions, 295,920 trial-behavior feature rows, 258,614 wheel-trial feature rows, and 847,042 pose-trial feature rows, documenting substantial but modality-incomplete local control surfaces for later context-transfer planning.
  - Limitation: Coverage differs by wheel and pose modality, so context-transfer comparisons must not equate missing modality data with a neural property.
  - Limitation: Release-level counts do not establish the number of usable held-out contexts after prespecified quality filters.
- **Unverified planning evidence:** The ephys schema defines sessions keyed by eid, trials keyed by eid and trial_id, units keyed by pid and cluster_id, and spike shards keyed by pid; the documented relational surfaces allow future matching of task states within sessions and aggregation of independently estimated insertion-level geometry across sessions, subjects, and labs.
  - Limitation: Units are not longitudinally identified across sessions, so the release cannot establish neuron-for-neuron stability across contexts.
  - Limitation: Cross-context geometry requires a prespecified common task-state representation and out-of-context validation rather than direct unit identity matching.

### Plan at a glance

- Population and scope: BWM insertions and sessions meeting prespecified task-state, unit, and trial coverage thresholds; context is session and, where coverage permits, subject or laboratory; claims concern transferable condition geometry rather than shared neurons.
- Unit of observation: A trial-by-time-bin response representation within one insertion, standardized in its training context.
- Unit of inference: A context-level held-out readout-performance contrast modeled across sessions and grouped at subject and laboratory levels when coverage permits.
- Hierarchy and dependence: Do not split trials from a context across source and target roles; use context-clustered resampling and nested subject/laboratory grouping.
- Validation: Use synthetic multi-population simulations with and without a shared low-rank decision factor, test alignment and rank recovery, and audit all source-target splits and state coverage.
- Split strategy: Nested leave-session-out by default, escalating to leave-subject-out and leave-laboratory-out only after prespecified coverage thresholds; select rank entirely inside source training contexts.
- Claim ceiling: predictive

**Analysis strategy**

1. Construct matched task-state strata from stimulus, choice, correctness, and timing independently of neural outcomes.
2. Fit a compact source-context latent representation on training trials with rank selected by prespecified reconstruction or stability criteria, never target readout.
3. Map source and target populations into a common condition-level representation without assuming unit identity, then test source-trained decision readout in held-out contexts.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Decision labels permuted within matched task-state strata in source contexts.; Transfer after removing decision-label correspondence while retaining dominant activity and movement dimensions.
- Positive controls: Recovery of a simulated shared low-rank decision factor across nonoverlapping populations.; Within-context held-out readout as a feasibility control only.
- Alternative explanations: Global activity, movement, or recording quality can produce apparent compactness.; Shared task statistics or regional composition can drive cross-context transfer.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Transfer is observational and does not establish that compression causes stable behavior.
- No shared neuron identities permit only population-level condition-geometry conclusions.
- Sparse coverage can limit laboratory-level inference and require separate session-level reporting.

**Why the plan serves the question**

It tests compression as an independently learned decision-relevant summary that must transfer across contexts while contrasting global variance, activity similarity, movement, and context-specific readouts.

**Before any later execution**

- Unresolved planning decisions: Choose the common condition representation and compact-model family by simulation and preregistered structural criteria.; Set coverage required for subject- and laboratory-level, rather than session-level, transfer.
- Required future skills: Cross-context population-geometry alignment without unit identity and with nested leakage-safe validation.; Compressed BWM spike-shard trial-binning loader.

### Scientific stakes

**Discriminating observation**

Useful compression would be favored if a compact geometry defined independently in one context predicts decision structure in another beyond dominant generic dimensions and activity-pattern similarity.

**What possible outcomes would mean**

- Positive pattern: A positive result would support a predictive role for compressed geometry in stable decision readout.
- Negative pattern: A negative result would favor flexible readouts, context-specific geometry, or non-decision sources of low dimensionality.
- Null or ambiguous pattern: A null result would leave unresolved whether compact decision structure is absent or insufficiently reliable across contexts.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct protected scientific roles and provide credible observational, leakage-aware plans with appropriate predictive claim ceilings, controls, validation, and scope limits. Remaining choices are execution locks rather than scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Define and lock the held-out decision-consistency outcome for the expansion variant before execution.
- **Pre execution lock:** Prespecify geometry-estimation settings and structural eligibility rules before execution.
- **Pre execution lock:** Lock the common condition representation, compact-model family, and transfer-level coverage criteria for the compression variant before execution.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct protected scientific roles and stay within a predictive, observational claim ceiling. The expansion variant tests independently defined confusable-state separation and held-out decision consistency against population-size, reliability, and movement alternatives; the compression variant tests cross-context transfer of a compact decision geometry against full-rank, dominant-variance, shuffled-label, and context-specific baselines, explicitly avoiding any assumption of neuron identity across sessions. Leakage-safe splits, hierarchical/context-clustered resampling, negative and positive controls, synthetic recovery validation, and honest interpretation…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
