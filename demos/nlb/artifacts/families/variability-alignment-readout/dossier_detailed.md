# Structure of neural co-variability relative to movement-relevant readouts — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether the orientation of population co-variability, rather than its aggregate magnitude, is related to movement-relevant information, with distinct within-region and cross-region targets.

The scientific tension is:

Large or small shared variability is not inherently beneficial or harmful; its consequence may depend on alignment with independently defined movement-relevant or interregional dimensions.

## Variant 1: within-region behavioral-readout alignment test

### Why it matters

The question replaces a magnitude heuristic with a structural test tied to an independent behavioral consequence.

### Original and refined question

**Original Question Scientist proposal**

Within M1 and PMd, does alignment of trial-to-trial co-variability with a reach-relevant dimension predict movement readout better than aggregate co-variability magnitude?

**Reviewed refined question**

Within documented M1 and PMd train-trial populations, does the alignment of residual trial-to-trial co-variability with an independently estimated hand-velocity readout direction predict held-out hand-velocity decoding quality beyond matched aggregate shared-variability magnitude?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Repeated reaching with neural populations and movement measurements may allow later planning of regional co-variability and readout comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** For MC_Maze releases, the documented authoritative region indicator is the leading digit of the unit identifier: 1 denotes PMd and 2 denotes M1. The note warns that raw stored M1 electrode indices require a +96 correction and therefore cannot alone determine regional membership; its pinned metadata summary reports both regional populations in train and test-held-in splits.
  - Limitation: The note is a release-specific conversion caveat and does not replace executor verification of identifier parsing and regional exclusions.
  - Limitation: No claim about cross-region coupling or behavioral prediction follows from regional availability.
- **Unverified planning evidence:** The pinned DANDI:000140 MC_Maze_Small release describes sorted-unit recordings from M1 and PMd during a delayed center-out maze-reaching task, with cursor position, hand position, eye position, and offline-calculated hand velocity. It is one rhesus subject and is limited to 100 train and 100 test trials.
  - Limitation: Metadata establishes dataset availability and stated recording/task surfaces, not construct validity or an empirical effect.
  - Limitation: The release is single-subject and small, so any later inference is session-specific and requires resampling-based uncertainty.
  - Limitation: Test outcomes were not inspected.
- **Unverified planning evidence:** The training NWB exposes processed behavioral labels hand_pos, cursor_pos, hand_vel, and timestamps; its embedded descriptions define hand position and velocity as two-dimensional millimeter and millimeter-per-second signals. The same file labels separate 96-electrode Utah arrays in PMd and M1 and contains units-related schema labels.
  - Limitation: This structural inspection does not establish exact trial-event boundaries, timestamp precision, unit counts, or missingness; those must be verified by the executor before analysis.
  - Limitation: The inspection did not access held-out test outcomes or evaluate neural-behavior associations.

### Plan at a glance

- Population and scope: The pinned MC_Maze_Small training recording from one rhesus subject performing delayed maze reaches; analyze M1 and PMd separately after identifier-based region assignment, without generalizing beyond the recorded session.
- Unit of observation: A prespecified neural count bin within a movement-aligned time window, with its concurrent hand-velocity target and region label.
- Unit of inference: Resampled trial blocks within the single recorded session; bins are repeated measures and are never treated as independent animals or sessions.
- Hierarchy and dependence: Retain trial-to-bin nesting and region stratification. Use blocked folds by trial, trial-clustered uncertainty, and condition-balanced resampling; do not pool M1 and PMd units or randomize bins across trials.
- Validation: Use nested blocked cross-validation, permutation of the readout-direction-to-covariance pairing within outer training folds, and synthetic method-recovery simulations before target execution to verify that the estimator distinguishes aligned from isotropic covariance without leakage.
- Split strategy: Outer folds hold out whole trials, stratified by verified reach condition where possible; inner folds estimate temporal windows, regularization, and dimensionality. Any final held-out test surface remains untouched until the later executor stage.
- Claim ceiling: predictive

**Analysis strategy**

1. Before fitting, validate identifier-based regional assignment using the documented leading-digit rule and the M1 electrode-index caveat; exclude units with unresolved labels rather than infer region from uncorrected electrode indices.
2. In each outer training fold and region, align eligible bins to verified movement events, estimate condition and time mean responses, and form residual count vectors after removing prespecified movement/condition means.
3. Estimate a regularized residual covariance on an inner training split and define aggregate magnitude as a trace- or matched-leading-eigenvalue-based shared-variability summary chosen before outcome evaluation.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Use orthogonal or randomly rotated readout directions matched in norm and dimensionality.; Permute the mapping between training-fold covariance estimates and readout directions while preserving trial structure.
- Positive controls: On synthetic spike-count data with known anisotropic covariance and an independently specified readout direction, recover greater projected covariance in the aligned than orthogonal condition.; Verify that the hand-velocity stream has valid two-dimensional timestamps and that a within-fold baseline decoder exceeds a null-label decoder only as a data-integrity check, not as a scientific result.
- Alternative explanations: Apparent alignment could arise from movement-condition heterogeneity rather than residual co-variability.; Regional differences could reflect unit count, firing rate, covariance regularization, or readout reliability.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- This is an observational, single-session predictive analysis and cannot establish that co-variability causes movement or that either region is a causal readout.
- Hand velocity is a documented behavioral measure and a practical movement-readout proxy; it does not exhaust reach-relevant computation.
- Planning evidence establishes availability, not a result, effect size, or sufficient final precision.

**Why the plan serves the question**

It directly retains the within-region comparison of orientation against magnitude, independently estimates the behavioral readout and covariance geometry, and assigns the stated positive and negative patterns their intended predictive meanings without converting the question into a cross-region or causal claim.

**Before any later execution**

- Unresolved planning decisions: Exact event-alignment field and usable peri-movement interval.; Prespecified shared-variability magnitude summary and dimensionality rule after schema-only validation.; plus 1 additional item(s) in the complete dossier
- Required future skills: Leakage-safe nested estimation of covariance alignment with independently fit behavioral readout directions.; Trial-blocked resampling and synthetic method-recovery for neural covariance geometry.

### Scientific stakes

**Discriminating observation**

Alignment that predicts held-out movement readout after accounting for magnitude and reliability would favor the structural account; magnitude-only prediction would favor the coarse account.

**What possible outcomes would mean**

- Positive pattern: A specific alignment relationship would support a predictive claim that co-variability structure is behaviorally consequential.
- Negative pattern: Magnitude predicting readout without an alignment contribution would support a coarser variability account.
- Null or ambiguous pattern: Neither reliable relationship would leave co-variability consequence unresolved rather than proving irrelevance.

## Variant 2: cross-region variability-alignment test

### Why it matters

The question identifies which components of variability participate in cross-region association while avoiding causal routing claims.

### Original and refined question

**Original Question Scientist proposal**

Is PMd or M1 co-variability selectively aligned with population dimensions associated with the other region, beyond alignment with dominant local modes?

**Reviewed refined question**

On verified common training trial/time support, is residual PMd or M1 co-variability more aligned with a population dimension associated with the other region than with a dimensionality-matched dominant local mode, after behavioral and sampling controls?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Broadly concurrent M1 and PMd population observations may support later planning of cross-region versus local structural comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** For MC_Maze releases, the documented authoritative region indicator is the leading digit of the unit identifier: 1 denotes PMd and 2 denotes M1. The note warns that raw stored M1 electrode indices require a +96 correction and therefore cannot alone determine regional membership; its pinned metadata summary reports both regional populations in train and test-held-in splits.
  - Limitation: The note is a release-specific conversion caveat and does not replace executor verification of identifier parsing and regional exclusions.
  - Limitation: No claim about cross-region coupling or behavioral prediction follows from regional availability.
- **Unverified planning evidence:** The pinned DANDI:000140 MC_Maze_Small release describes sorted-unit recordings from M1 and PMd during a delayed center-out maze-reaching task, with cursor position, hand position, eye position, and offline-calculated hand velocity. It is one rhesus subject and is limited to 100 train and 100 test trials.
  - Limitation: Metadata establishes dataset availability and stated recording/task surfaces, not construct validity or an empirical effect.
  - Limitation: The release is single-subject and small, so any later inference is session-specific and requires resampling-based uncertainty.
  - Limitation: Test outcomes were not inspected.
- **Unverified planning evidence:** The training NWB exposes processed behavioral labels hand_pos, cursor_pos, hand_vel, and timestamps; its embedded descriptions define hand position and velocity as two-dimensional millimeter and millimeter-per-second signals. The same file labels separate 96-electrode Utah arrays in PMd and M1 and contains units-related schema labels.
  - Limitation: This structural inspection does not establish exact trial-event boundaries, timestamp precision, unit counts, or missingness; those must be verified by the executor before analysis.
  - Limitation: The inspection did not access held-out test outcomes or evaluate neural-behavior associations.

### Plan at a glance

- Population and scope: The simultaneously documented M1 and PMd recording surfaces in the pinned single-subject MC_Maze_Small training session, restricted to trials and time bins with verified shared timestamp support and valid region labels.
- Unit of observation: A prespecified common neural count bin within a verified trial/event window, represented by paired PMd and M1 residual population vectors.
- Unit of inference: Blocked trial resamples from the single recording session, with joint bins treated as within-trial repeated measures.
- Hierarchy and dependence: Model paired regional observations within trial and time window. Hold out whole trials jointly for both regions and use trial-clustered/bootstrap uncertainty; never form pseudo-independent pairs by mixing different trials.
- Validation: Run synthetic paired-population method recovery with known selective shared and purely dominant-local structures; require symmetric region-label handling, inner-fold-only direction estimation, and recovery of null results under independent-region simulations.
- Split strategy: Use joint outer trial folds for both regions, stratified by verified condition; estimate cross-region directions, local modes, covariate adjustment, dimensionality, and regularization only in nested inner folds. Preserve all test-split outcomes for later execution.
- Claim ceiling: associational

**Analysis strategy**

1. Validate common timestamps, overlapping trial windows, and identifier-based M1/PMd labels before any joint analysis; if common support is not established, mark this variant unsupported rather than imputing synchrony.
2. Within each outer training fold, remove prespecified trial-condition, time, and behavioral covariate means from each regional population to form residual vectors.
3. Estimate regularized within-region covariance and cross-region covariance on inner training data only; derive each region's cross-region-associated direction using a cross-validated CCA, reduced-rank regression, or equivalent singular-vector formulation fixed before outcome comparison.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Trial-shift or within-condition trial-permutation controls that preserve each region's local covariance but break paired cross-region correspondence.; Time-shifted pairings outside a prespecified plausible alignment lag, plus random orthogonal directions matched to the local-mode spectrum.
- Positive controls: Synthetic paired-population data in which a known low-variance shared direction is recovered despite stronger unrelated local modes.; Schema validation that both regional populations and concurrent behavioral streams are available on the retained training support.
- Alternative explanations: Dominant local fluctuations can create apparent correspondence without selective coordination.; Shared movement state, reach condition, temporal autocorrelation, or unmeasured inputs can drive both regions.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Concurrent association cannot establish directed communication, anatomical routing, or causality between PMd and M1.
- Behavioral adjustment only addresses measured shared drive and cannot eliminate unmeasured common-input explanations.
- The single small release limits population-level generalization and final model complexity.

**Why the plan serves the question**

It preserves the cross-region target, explicitly compares it against dominant local modes, and uses matched shared-drive and dimensionality controls so that any later conclusion remains an associational statement about selective organization rather than a behavioral-readout or causal claim.

**Before any later execution**

- Unresolved planning decisions: Exact common timestamp and event-alignment rule after schema validation.; Choice among mathematically equivalent prespecified cross-region direction estimators based on implementation audit rather than target results.; plus 1 additional item(s) in the complete dossier
- Required future skills: Cross-validated cross-region aligned-subspace estimation with matched local-mode nulls.; Joint trial-blocked resampling and behavioral/temporal pairing controls for paired neural populations.

### Scientific stakes

**Discriminating observation**

Cross-region-associated dimensions that differ reliably from dominant local modes and survive matched behavioral and dimensionality controls would favor selective organization.

**What possible outcomes would mean**

- Positive pattern: Selective cross-region alignment would support an associational claim about structured coordination of population variability.
- Negative pattern: Correspondence restricted to dominant local modes would favor generic shared variability.
- Null or ambiguous pattern: Unstable or control-equivalent alignment would leave selective coordination unresolved.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct scientific targets and claim limits. The plans use region-appropriate, leakage-aware training-only estimation, trial-blocked resampling, and controls that address the principal alternative explanations. Remaining choices are execution locks rather than deficiencies in the planning dossier.

Retained changes and locks:

- **Pre execution lock:** Before execution, fix the variant-01 aggregate shared-variability summary and dimensionality rule without reference to held-out target outcomes.
- **Pre execution lock:** Before execution, fix the variant-02 cross-region direction estimator and matched-local-mode specification without reference to held-out target outcomes.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variant plans preserve their distinct protected targets and honor the forbidden semantic merge: variant-01 stays a within-region predictive comparison of readout alignment versus aggregate magnitude, and variant-02 stays an associational cross-region selective-coordination test against matched dominant local modes. Neither collapses into the other. Both are grounded in the pinned MC_Maze_Small evidence views (DANDI:000140 metadata, NWB training schema, region-index caveat) and correctly treat region labels via the leading-digit rule with the M1 +96 correction caveat, excluding rather than inferring ambiguous units. Leakage control is sound: whole-trial blocked outer folds…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
