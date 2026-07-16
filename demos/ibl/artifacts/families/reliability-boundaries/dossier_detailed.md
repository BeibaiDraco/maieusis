# Reliability and boundary conditions of population-dynamical claims — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether geometric and dynamical signatures reproduce across acquisition contexts and whether their failures identify scientific boundaries rather than merely technical instability.

The scientific tension is:

A population-level relation may be a robust organizing principle, a context-bound regularity, or an artifact of unreliable estimation and heterogeneous pooling.

## Variant 1: Geometric reproducibility branch

### Why it matters

Treating reproducibility and informative failure as scientific outcomes constrains the scope of representational claims.

### Original and refined question

**Original Question Scientist proposal**

Which decision-related geometric relations reproduce across subjects, sessions, and laboratories, and do their failures track behavioral or task boundaries rather than measurement instability?

**Reviewed refined question**

Across prespecified matched task and behavioral operating points, which decision-related representational geometries reproduce across subjects, sessions, and laboratories, and do nonreproductions remain after accounting for sampling, measurement quality, and movement?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

The multi-laboratory organization and broad anatomical sampling may allow later planning of reproducibility and boundary-condition comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The companion behavior release documents session and trial keys, trial-level choice, feedback, stimulus contrast, event timings, reaction and movement-time features, and wheel-defined movement or quiescence summaries; its session table includes subject, date, session number, and lab.
  - Limitation: Wheel and pose availability can be partial, so movement-adjusted analyses require prespecified complete-case and missingness sensitivity rules.
  - Limitation: The documented compact behavior features are proxies for behavioral state rather than a full behavioral phenotyping battery.
- **Unverified planning evidence:** The local ephys release reports 459 sessions, 699 insertions, 75,395 good units, 295,920 trials, and a spike store for 699 insertions; its paired schema records sessions, insertions, units, trials, and events as separate keyed tables.
  - Limitation: This is aggregate build metadata and does not establish the number of usable matched contexts after prespecified inclusion criteria.
  - Limitation: No neural outcomes, fitted geometry, or behavioral association was inspected.

### Plan at a glance

- Population and scope: Good-unit recordings from included BWM sessions, analyzed within prespecified comparable anatomical regions and task epochs; cross-context inference is limited to contexts with sufficient independent subjects and laboratory coverage.
- Unit of observation: A trial-aligned, region-specific population-response representation estimated independently within each recording context.
- Unit of inference: Independent subject-context groups, with laboratory and session treated as clustered or crossed context factors.
- Hierarchy and dependence: Split and resample by subject and laboratory-context group, never by trial alone; retain nested trial, session, insertion, subject, laboratory, and region structure in uncertainty estimation.
- Validation: Use split-half reliability within each context, label-permutation nulls that preserve session structure, simulation-based recovery for unequal unit counts, and blinded metadata-only eligibility checks before neural fitting.
- Split strategy: Outer held-out subject or laboratory-context groups evaluate generalization; inner splits construct geometry and choose only prespecified nuisance-handling settings. No trials from a held-out context enter representation estimation.
- Claim ceiling: associational

**Analysis strategy**

1. Prespecify decision-relevant task epochs and matched operating-point strata using contrast, choice, performance, reaction time, and movement summaries without inspecting neural outcomes.
2. Within each region and context, construct cross-validated population response geometry from held-out trials using a fixed distance or alignment family declared before outcome access.
3. Estimate cross-context similarity with a hierarchical model that separates within-context reliability, unit-count or sampling adequacy, movement imbalance, and contextual mismatch.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permuted task labels within session, preserving trial counts and timing structure.; Cross-region comparisons not predicted to share the selected task geometry, interpreted only as specificity checks.
- Positive controls: Within-context split-half geometry should exceed its session-structured label-permutation reference before any cross-context interpretation.
- Alternative explanations: Unequal unit yield, unit quality, anatomical coverage, or event-alignment precision.; Residual movement, reaction-time, performance, or trial-composition imbalance.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Observational multi-laboratory data cannot establish that any context causes a neural geometric change.
- Matched anatomical populations are comparable samples, not longitudinally identified neurons.
- A null or unstable result may reflect limited coverage in prespecified strata.

**Why the plan serves the question**

The plan directly distinguishes robust geometry, meaningful contextual boundaries, and apparent failures due to reliability or heterogeneous sampling, while retaining the variant's empirical rather than dynamical target contrast.

**Before any later execution**

- Unresolved planning decisions: Choose the fixed geometry metric family and region ontology level from method literature and synthetic recovery checks before target-data fitting.; Define the prespecified operating-point matching rule and minimum coverage gate from metadata alone.
- Required future skills: Leakage-safe BWM spike-shard loader and trial-alignment pipeline.; Cross-context representational-geometry and hierarchical reliability executor.

### Scientific stakes

**Discriminating observation**

A meaningful boundary would be supported if geometry reproduces within comparable operating points but changes systematically with independently defined behavioral or task conditions, beyond reliability and sampling differences.

**What possible outcomes would mean**

- Positive pattern: A positive result would establish the predictive scope and boundary conditions of a geometric relation.
- Negative pattern: A negative result would weaken claims of a robust organizing geometry and may favor context-specific representations.
- Null or ambiguous pattern: A null result would indicate that scientific boundaries cannot be distinguished from measurement instability.

## Variant 2: Dynamical-model reliability branch

### Why it matters

The question makes reliability and incremental predictive value prerequisites for interpreting dynamical signatures, while stopping short of causal or circuit claims.

### Original and refined question

**Original Question Scientist proposal**

Are fitted dynamical signatures of decision formation reproducible enough across comparable recordings to predict behavior beyond simpler geometric descriptions?

**Reviewed refined question**

Do prespecified temporal-dynamical signatures estimated from comparable task-related population recordings reproduce across separated contexts and improve out-of-context prediction of choice or reaction time beyond matched static geometry and measured behavioral state?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Multiple sessions and broad task-related neural observations may allow later planning of reliability and predictive-comparison tests, subject to verification of comparable recordings.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The behavior contract supplies trial-level choice, correctness, reaction time, movement time, stimulus and response timing, and wheel-derived movement measures linked by session and trial identifiers.
  - Limitation: Missing wheel or pose assets are documented as possible and must not be treated as random without sensitivity analysis.
  - Limitation: These observables support behavioral prediction and confound adjustment, not a causal claim about neural implementation.
- **Unverified planning evidence:** The ephys schema declares keyed session, insertion, unit, trial, and event tables, plus a spike store sharded by insertion with delta-encoded spike times, spike clusters, cluster identifiers, and per-cluster spike counts.
  - Limitation: The schema does not certify a particular dynamical model or cross-context match set.
  - Limitation: Decoding and fitting were not run during planning.

### Plan at a glance

- Population and scope: Included BWM good-unit recordings with trial-aligned spike data and linked behavioral trials, restricted to prespecified comparable regions, task epochs, and context cells with adequate independent holdouts.
- Unit of observation: A trial-aligned regional population time series and its held-out fitted signature, with behavior measured on the same trial.
- Unit of inference: Independent subject-context groups evaluated through grouped out-of-context prediction and grouped resampling.
- Hierarchy and dependence: Trials are nested within session and insertion, which are nested in subject and laboratory; all tuning, fitting, and evaluation splits remain disjoint at the held-out context level.
- Validation: Run synthetic recovery tests for known low-dimensional dynamics, time-shift and trial-label permutation nulls, repeated grouped resampling, and stability checks across bin widths and latent dimensionalities fixed by a prespecified grid.
- Split strategy: Use outer subject or laboratory-context holdouts for the final prediction comparison, with inner grouped folds for all model selection; prohibit trial-level random splitting across a shared recording context.
- Claim ceiling: predictive

**Analysis strategy**

1. Define a limited, preregistered set of low-dimensional temporal-dynamical model classes and identifiability diagnostics, with a matched static geometry baseline and a measured-state baseline.
2. Fit each model only in training contexts using trial-aligned binned population activity and extract a prespecified signature such as predictive state trajectory or stable latent-transition summary.
3. Quantify signature reproducibility across independently held-out comparable contexts separately from within-context goodness of fit.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Circularly shifted or time-reversed population sequences that preserve marginal activity but disrupt task-aligned temporal order.; Within-session behavior-label permutations evaluated with the identical grouped pipeline.
- Positive controls: Synthetic data with known latent dynamics and the same grouping structure must recover the selected signature within prespecified error bounds before target-data interpretation.
- Alternative explanations: Static task geometry, event timing, movement, or reaction-time variation can mimic apparent temporal dynamics.; Fitted signatures may be nonidentifiable or estimator-specific despite good within-context fit.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Predictive improvement or reproducibility does not prove biological mechanism or causal implementation.
- Model comparison is conditional on the declared model set, temporal preprocessing, and availability of measured covariates.
- Failure to find incremental prediction cannot prove the absence of meaningful dynamics.

**Why the plan serves the question**

The plan keeps the variant's required distinction between reproducible temporal-dynamical signatures and simpler geometry, and demands incremental out-of-context behavioral prediction rather than equating fit with mechanism.

**Before any later execution**

- Unresolved planning decisions: Select the restricted candidate dynamical-model family and signature definition using theory and synthetic recovery rather than target behavioral outcomes.; Set target-specific scoring rules and reaction-time transformation before execution.
- Required future skills: BWM trial-aligned spike-shard loader with grouped split enforcement.; Latent dynamical-model comparison, identifiability diagnostics, and synthetic recovery executor.

### Scientific stakes

**Discriminating observation**

The dynamical account would be favored if signatures estimated under separated observations reproduce across comparable contexts and improve prediction of behavior beyond reliable geometric and measured-state alternatives.

**What possible outcomes would mean**

- Positive pattern: A positive result would justify stronger predictive use of dynamical descriptions while not proving biological implementation.
- Negative pattern: A negative result would favor simpler geometric summaries or caution against interpreting unstable fitted dynamics.
- Null or ambiguous pattern: A null result would show that model reliability or incremental prediction is insufficient to distinguish dynamical and geometric accounts.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variant plans preserve their distinct protected contrasts and provide credible, non-executable routes to distinguish cross-context signal from sampling, reliability, and behavioral-state alternatives. Grouped held-out evaluation, reliability checks, null controls, and explicit interpretation limits prevent invalid causal or mechanistic inference. Remaining choices are appropriate pre-execution locks rather than planning deficiencies.

Retained changes and locks:

- **Pre execution lock:** Before execution, fix the geometry metric family, region ontology, operating-point matching rule, and metadata-only coverage gate for the geometry analysis.
- **Pre execution lock:** Before execution, fix the restricted dynamical-model family, signature definition, target scoring rules, and reaction-time transformation for the dynamical analysis.
- **Pre execution lock:** Before execution, specify missing-data sensitivity handling for incomplete movement or pose covariates and confirm metadata-only feasibility of independent context holdouts.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variant plans preserve their distinct protected contrasts and provide credible, non-executable routes to the family question. Variant 01 tests empirical cross-context representational geometry with reliability decomposition, sampling/movement adjustment, and boundary interactions; variant 02 tests reproducibility and incremental behavioral prediction of fitted dynamical signatures against static-geometry and measured-state baselines. Each uses grouped context-level holdouts, leakage-safe splits, synthetic recovery, and structured null controls, and each states honest interpretation limits (associational for geometry, predictive for dynamics). Sibling separation is respected: geometry…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
