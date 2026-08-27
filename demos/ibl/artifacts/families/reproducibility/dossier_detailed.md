# Reproducibility of noise-correlation statistics and geometry across laboratories — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Distinguishes reproducibility of coarse correlation magnitude from reproducibility of task-aligned covariance geometry in a standardized multisite setting.

The scientific tension is:

Standardized multisite processes may yield reproducible neural summaries, but existing process-level evidence does not establish whether noise correlations reproduce quantitatively. Coarse magnitude and functional geometry may have different reproducibility profiles.

## Variant 1: Metric-specific residual-laboratory reproducibility branch

### Why it matters

A metric-specific variance decomposition would establish whether a commonly interpreted population summary has a portable descriptive meaning, rather than inferring portability from standardized procedures or conflating reproducibility with known context sensitivity.

### Original and refined question

**Original Question Scientist proposal**

Are coarse summaries of noise-correlation magnitude reproducible across laboratories after accounting for subject, session, region, and behavioral-context heterogeneity?

**Post-novelty revised proposal**

Across laboratories, is the median signed Pearson noise correlation of trial-wise spike counts within a prespecified behaviorally aligned task epoch reproducible for simultaneously recorded unit pairs passing common quality rules, after matching or adjustment for subject, session, anatomical region and targeting, behavioral condition, unit-composition strata, and inter-unit sampling geometry?

**Reviewed refined question**

Across laboratories, is the prespecified median signed Pearson noise correlation of simultaneously recorded, quality-screened unit pairs reproducible within matched region, behavior, unit-composition, and pair-geometry strata of the documented task dataset?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the multisite resource contains sufficiently comparable task epochs, metadata, anatomical coverage, and simultaneously recorded units, it may support matched comparisons and decomposition of variation attributable to laboratory, subject, session, region or targeting, behavioral condition, unit composition, and pairwise sampling geometry.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The metadata has 459 sessions from 12 laboratories, with 17 to 62 sessions per laboratory; subjects are nested within laboratory in this snapshot. Units include label, anatomical acronyms, coordinates, depth, spike count, and firing rate. Trials include choice, feedbackType, contrasts, bwm_include, stimOn_times, and firstMovement_times; choice is documented for every trial and trial timing anchors are broadly available.
  - Limitation: No subject appears in more than one laboratory, so observational laboratory differences cannot be given a causal laboratory interpretation independent of subject composition.
  - Limitation: Aggregate coverage does not establish sufficient repeated trials or eligible unit pairs in every planned stratum; execution must apply prespecified minimum-information rules.
- **Unverified planning evidence:** The inspected shard declares a documented insertion-to-session linkage and laboratory field, dense local cluster encoding, cluster IDs, spike-cluster assignments, delta-encoded spike times, a zero time origin, and 100-microsecond time quantization. This supplies a planned route to reconstruct unit-specific counts in trial-aligned epochs after validation of decoder recovery.
  - Limitation: This is one structural shard inspection and does not establish successful decoding across all insertions.
  - Limitation: No pairwise correlation, geometry, behavioral association, or laboratory contrast was calculated.
- **Unverified planning evidence:** The snapshot defines sessions, insertions, units, channels, and trials tables, keyed so trial behavior can join through eid and units can join through pid/eid. The spike store is partitioned by pid and declares spike_times_delta_ticks, spike_clusters, cluster_ids, and cluster_spike_counts.
  - Limitation: The schema establishes available surfaces and keys, not their inferential adequacy or a scientific result.
  - Limitation: Spike decoding and trial-window counting remain future execution steps.

### Plan at a glance

- Population and scope: Quality-screened simultaneously recorded units from the represented BWM ephys sessions, restricted before analysis to a common region ontology, a prespecified behaviorally aligned epoch, and predeclared trial-condition and information thresholds.
- Unit of observation: A pair of simultaneously recorded units within one session, trial condition, and prespecified task epoch, with correlation calculated across eligible trials after condition-specific mean removal.
- Unit of inference: Matched session-condition-pair summaries, with laboratory comparisons aggregated through subject and session nesting rather than treating pairs as independent replicates.
- Hierarchy and dependence: Keep pairs nested in insertion and session, sessions nested in subject and laboratory, and model repeated condition summaries jointly. Cluster or resample at the subject/session level; never use raw pair count as effective sample size.
- Validation: Use synthetic spike-count inputs with known residual correlations to verify timestamp reconstruction, binning, mean removal, pair construction, and median aggregation; compare decoded cluster counts with shard metadata; audit joins and condition coverage before fitting any target comparison.
- Split strategy: Use leave-one-subject-out or leave-one-session-out resampling within laboratory for uncertainty and leave-one-laboratory-out sensitivity summaries; no data-driven epoch, threshold, or tolerance selection.
- Claim ceiling: descriptive

**Analysis strategy**

1. Before reading target counts, declare one epoch anchored to a documented task timestamp, conditioning variables, unit-quality rules, pair-distance strata, common anatomy mapping, and a practical tolerance for residual matched-stratum laboratory variation.
2. Decode each eligible pid shard, reconstruct timestamps, bin one count per unit per eligible trial, and remove the mean within the prespecified condition before calculating signed Pearson correlations for simultaneous unit pairs.
3. Summarize each matched stratum by its median signed pairwise correlation and retain the signed distribution as a diagnostic; do not substitute absolute correlations.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Trial labels permuted within the prespecified condition before mean removal should remove condition-linked residual structure.; Pairs drawn from different sessions must not be treated as simultaneously recorded and should be excluded by construction.
- Positive controls: Synthetic data with injected signed correlations and known nesting must recover the known direction and tolerance decision under the fixed pipeline.
- Alternative explanations: Laboratory differences may reflect unmeasured subject composition because subjects are nested in laboratory.; Targeting, unit-quality, firing-rate, or pair-distance imbalance may shift median correlation summaries.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- This observational multisite snapshot cannot attribute a residual association causally to laboratory practices.
- Nested subjects and uneven regional or condition coverage can limit separation of laboratory and contextual variation.
- A plan and its future validation do not provide a scientific result.

**Why the plan serves the question**

The plan preserves the signed, median pairwise estimand and separates it from geometric preservation or behavioral prediction, while explicitly modeling the biological and sampling factors named in the invariant.

**Before any later execution**

- Unresolved planning decisions: Practical tolerance for residual matched-stratum laboratory variation.; Fixed minimum repeated-trial, pair, and cross-laboratory coverage criteria.
- Required future skills: Validated decoder for blosc-file spike shards with delta-tick timestamp reconstruction.; Dependence-aware trial-residual pairwise noise-correlation and matched-stratum variance-component executor.

### Scientific stakes

**Discriminating observation**

For each matched region, behavioral condition, and unit-composition stratum, define noise correlation as the Pearson correlation across repeated trials of two units' spike counts after removing the corresponding condition-specific mean, with each trial represented by one count from the same prespecified behaviorally aligned task epoch. Include only simultaneously recorded pairs whose units satisfy common prespecified quality and inclusion rules, and match or adjust pair sampling by anatomical targeting and inter-unit-distance strata. Aggregate with the median signed pairwise correlation, retaining its signed distribution as a secondary diagnostic rather than converting correlations to absolute magnitudes. Reproducibility would require the separately estimated residual laboratory component to remain below a prospectively declared practical-tolerance bound and matched-stratum summaries to preserve agreement or ordering, while subject, session, region, behavioral-condition, unit-composition, and sampling-geometry components are quantified separately. If laboratory and contextual components cannot be identified separately, the observation is unresolved rather than evidence of portability.

**What possible outcomes would mean**

- Positive pattern: If the residual laboratory component is distinguishable from contextual and sampling components and falls within the prospectively declared tolerance while matched summaries agree, the prespecified median signed noise correlation would be supported as a descriptively portable population summary for the represented conditions.
- Negative pattern: If the laboratory component is separable but exceeds the declared tolerance or matched-stratum summaries disagree materially, the prespecified correlation summary should not be treated as portable across laboratories even when procedures are standardized.
- Null or ambiguous pattern: If laboratory, subject, session, anatomical, behavioral, unit-composition, and pair-sampling contributions cannot be separated with adequate precision, reproducibility would remain unresolved; such a result would identify limits of the comparison rather than support either portability or non-portability.

## Variant 2: Functional-geometry reproducibility branch

### Why it matters

This would test whether structural population descriptions provide a more portable scientific object than aggregate correlation strength.

### Original and refined question

**Original Question Scientist proposal**

Is task-aligned covariance geometry more reproducible across laboratories than coarse noise-correlation magnitude, and does any reproducible geometry retain similar behavioral associations?

**Reviewed refined question**

Does a prespecified task-aligned covariance representation generalize across held-out laboratories and retain a comparable association with trial choice more consistently than a matched coarse signed noise-correlation magnitude representation?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Standardized task observations across laboratories may allow later planning of cross-laboratory generalization tests for sensory-, choice-, or behavior-aligned covariance geometry.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The metadata has 459 sessions from 12 laboratories, with 17 to 62 sessions per laboratory; subjects are nested within laboratory in this snapshot. Units include label, anatomical acronyms, coordinates, depth, spike count, and firing rate. Trials include choice, feedbackType, contrasts, bwm_include, stimOn_times, and firstMovement_times; choice is documented for every trial and trial timing anchors are broadly available.
  - Limitation: No subject appears in more than one laboratory, so observational laboratory differences cannot be given a causal laboratory interpretation independent of subject composition.
  - Limitation: Aggregate coverage does not establish sufficient repeated trials or eligible unit pairs in every planned stratum; execution must apply prespecified minimum-information rules.
- **Unverified planning evidence:** The inspected shard declares a documented insertion-to-session linkage and laboratory field, dense local cluster encoding, cluster IDs, spike-cluster assignments, delta-encoded spike times, a zero time origin, and 100-microsecond time quantization. This supplies a planned route to reconstruct unit-specific counts in trial-aligned epochs after validation of decoder recovery.
  - Limitation: This is one structural shard inspection and does not establish successful decoding across all insertions.
  - Limitation: No pairwise correlation, geometry, behavioral association, or laboratory contrast was calculated.
- **Unverified planning evidence:** The snapshot defines sessions, insertions, units, channels, and trials tables, keyed so trial behavior can join through eid and units can join through pid/eid. The spike store is partitioned by pid and declares spike_times_delta_ticks, spike_clusters, cluster_ids, and cluster_spike_counts.
  - Limitation: The schema establishes available surfaces and keys, not their inferential adequacy or a scientific result.
  - Limitation: Spike decoding and trial-window counting remain future execution steps.

### Plan at a glance

- Population and scope: Quality-screened simultaneous-unit populations in predeclared common anatomical regions and trial conditions from the represented BWM ephys laboratories, with trial choice as the Owner-approved behavioral target.
- Unit of observation: A session-condition covariance representation derived from trial-by-unit residual counts in one prespecified event-aligned epoch, paired with trial-level choice labels.
- Unit of inference: Laboratory-held-out generalization units, with session and subject as nested dependence levels and region/condition as prespecified comparison strata.
- Hierarchy and dependence: Fit and evaluate at session and laboratory levels, keep trials within session and units within insertion, and aggregate uncertainty through resampling whole sessions/subjects and laboratories rather than unit or trial rows.
- Validation: Use synthetic datasets with known shared versus laboratory-specific covariance subspaces, independently varied task timing, and known choice associations to verify leakage prevention, cross-population alignment, held-out scoring, and discrimination from the coarse comparator. Audit timestamp reconstruction, trial joins, region mapping, and train/test laboratory isolation before target execution.
- Split strategy: Primary split is leave-one-laboratory-out. All representation choices, scaling, dimensions, anatomy harmonization parameters, and geometry-to-choice score construction are learned only in training laboratories; nested resampling keeps sessions and subjects intact.
- Claim ceiling: predictive

**Analysis strategy**

1. Predeclare the event-aligned epoch, common region ontology, condition residualization, unit inclusion, representation dimension-selection rule using only training laboratories, and a neural-population alignment method that does not use held-out laboratory labels or choices.
2. From decoded residual trial counts, estimate a task-aligned covariance representation in training laboratories and quantify held-out representation similarity with a population-invariant metric; estimate the matched median signed-correlation magnitude comparator from the same eligibility rules.
3. Assess geometry and coarse magnitude separately under leave-one-laboratory-out evaluation, then compare their reproducibility using the same split definitions and uncertainty units.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Within-session permutation of trial choice after all fixed feature construction should eliminate a genuine held-out choice association.; Randomly rotated or condition-mismatched covariance representations should not generalize better than the prespecified geometry.
- Positive controls: Synthetic shared geometry with known laboratory-specific magnitude variation must recover greater held-out geometric than magnitude reproducibility.; Synthetic laboratory-specific geometry must fail laboratory-held-out similarity despite common task timing.
- Alternative explanations: Common task structure or timestamp alignment may make geometry appear portable without shared functional organization.; A population-alignment or regularization method may impose similarity across laboratories.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Held-out laboratory prediction supports portability within the represented observational dataset, not causal functional organization or a universal population claim.
- Subjects are nested within laboratories, so cross-laboratory performance can still reflect unmeasured subject composition.
- A common task can provide a shared temporal scaffold; the specified controls are necessary to distinguish that from transferable geometry.

**Why the plan serves the question**

It retains the direct geometry-versus-coarse-magnitude comparison, requires genuine held-out laboratory generalization, and uses the Owner-approved trial-choice association independently of geometry construction.

**Before any later execution**

- Unresolved planning decisions: Fixed common-region coverage and minimum-information rules for every held-out laboratory.; Training-only representation dimension and covariance regularization selection rule.
- Required future skills: Validated decoder for blosc-file spike shards with delta-tick timestamp reconstruction.; Leakage-audited cross-population covariance-geometry and laboratory-held-out behavioral-association executor.

### Scientific stakes

**Discriminating observation**

Task-aligned geometry estimated in some laboratory contexts would generalize to held-out contexts and preserve its association with behavior more consistently than coarse correlation magnitude.

**What possible outcomes would mean**

- Positive pattern: Would support task-aligned covariance geometry as a comparatively reproducible predictive population descriptor.
- Negative pattern: Would indicate that structural geometry is no more portable than coarse magnitude or that laboratory and population context fundamentally shape it.
- Null or ambiguous pattern: Would leave relative reproducibility unresolved if neither summary generalizes reliably or their uncertainty overlaps substantially.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct protected contrasts and provide credible, non-executable analysis routes. The plans appropriately limit inference to descriptive or held-out predictive portability within the represented observational dataset, retain dependence-aware laboratory/session/subject structure, and acknowledge subject–laboratory nesting. Remaining choices are explicit pre-execution locks rather than scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Before execution, fix the v1 event anchor, practical tolerance for residual matched-stratum laboratory variation, and minimum repeated-trial, eligible-pair, and cross-laboratory coverage rules.
- **Pre execution lock:** Before execution, fix the v2 training-only covariance-geometry operationalization, including alignment and similarity metric, dimension/regularization selection rule, and minimum common-region and information coverage for each held-out laboratory.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both sibling plans preserve the family's protected distinction between coarse noise-correlation magnitude reproducibility (v1) and task-aligned covariance-geometry reproducibility with behavioral association (v2). Each specifies a credible, evidence-grounded route using documented trial/unit/spike schema and coverage evidence, retains dependence-aware nesting (subject-in-lab, session-in-lab), states appropriately bounded claim ceilings (descriptive/predictive) with explicit interpretation limits about the observational subject-lab confound, and includes adequate positive/negative controls and leakage audits. The Owner's two remaining issues are legitimate pre-execution locks (fixing thresholds, tolerances, and a training-only geometry pipeline) rather than scientific blockers, so this is an accept that carries them forward rather than a revision.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
