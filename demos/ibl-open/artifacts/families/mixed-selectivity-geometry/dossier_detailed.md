# Functional forms of mixed selectivity in decision populations — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

A family distinguishing the representational form of mixed selectivity from its functional relationship to behavioral success and cross-condition readout.

The scientific tension is:

Mixed responses may provide useful high-dimensional structure, reflect simpler additive mixing, or arise from correlated sensory and movement variables; identifying mixing alone does not establish function.

## Variant 1: Conditional behavioral-relevance and endpoint-dissociation variant

### Why it matters

Separating behavioral prediction from information content, decoder reliability, and generalization would clarify what mixed population geometry contributes beyond descriptive heterogeneity or reliable transmission, while supporting only predictive—not causal—claims about successful decisions.

### Original and refined question

**Original Question Scientist proposal**

Do nonlinear or higher-dimensional mixed population representations predict successful decisions and cross-condition readout better than additive or lower-dimensional alternatives?

**Post-novelty revised proposal**

When mixed/high-dimensional and additive/lower-dimensional population representations are comparably evaluated for task-variable signal and decoding reliability, does representational geometry incrementally predict held-out decision success, and is that behavioral association independent of, aligned with, or traded off against cross-condition readout?

**Reviewed refined question**

Across quality-screened BWM insertion-session populations, do prespecified nonlinear mixed/high-dimensional response models provide reproducible incremental held-out prediction of trial decision success over capacity-matched additive/lower-dimensional models after matching task-variable signal and decoding reliability, and is their cross-condition readout outcome aligned, independent, or traded off?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the available neural, task, movement, and behavioral measurements contain suitable outcome and condition variation, they may support comparison of representation classes at comparable task-variable signal and reliability, followed by separate held-out assessments of decision-success prediction and cross-condition readout.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The BWM ephys build summary documents 459 sessions, 699 insertions, 75,395 units, and 295,920 trials, with all required spike assets present. The schema and bounded metadata-file count confirm one spike-shard metadata record for each of the 699 insertions.
  - Limitation: Build-level counts are planning context rather than eligibility counts for a specific population, region, or cross-validation fold.
  - Limitation: No neural response, correct-versus-error contrast, decoding score, or other target outcome was computed or inspected.
- **Unverified planning evidence:** The aligned BWM behavior surface shares eid and trial_id keys with ephys trials and provides derived correct, reaction_time, movement_time, signed_contrast, and choice_label fields. Where available, it also provides trial-windowed wheel movement direction, amplitude, velocity and camera-specific DLC summary features.
  - Limitation: Wheel and DLC feature tables have fewer rows than the trial table, so movement covariates require availability indicators and complete-case sensitivity analyses.
  - Limitation: Feature names establish candidate confound controls, not that a particular pre-response window is free of decision-related movement.
- **Unverified planning evidence:** The BWM ephys snapshot keys trials by eid and trial_id, units by pid and cluster_id, and links units to eid. It supplies trial choice, feedbackType, probabilityLeft, contrastLeft, contrastRight, stimulus and movement timestamps, inclusion flags, unit quality and anatomical metadata, and per-insertion spike shards with cluster identities and delta-tick times.
  - Limitation: The schema establishes available fields and joins but does not establish data completeness after the plan's quality and valid-time checks.
  - Limitation: Representation geometry is not a precomputed field and must be derived from bounded, task-aligned spike representations during later execution.

### Plan at a glance

- Population and scope: All BWM ephys insertion-session populations with documented spike shards, valid task trials, and prespecified minimum quality-screened unit and trial counts. Primary inference generalizes across eligible insertion-session populations; region-stratified analyses are secondary and require prespecified minimum coverage.
- Unit of observation: A trial-aligned population response from one quality-screened insertion-session population, paired with its prespecified task, success, and movement covariates.
- Unit of inference: Insertion-session population, with uncertainty clustered and hierarchically partial-pooled across session, subject, lab, and region where coverage permits.
- Hierarchy and dependence: Keep all trials from a population within a fold; use grouped outer resampling by session or subject according to the target generalization claim, and retain insertion nesting within session in mixed-effects or cluster-robust aggregation. Units are features, not independent replicates.
- Validation: Before target evaluation, validate spike-shard decoding on synthetic delta-tick fixtures and verify eid, pid, cluster_id, and trial_id join uniqueness. On each training fold, verify model-capacity matching, condition coverage, response-window validity, calibration, and within-condition reliability; abort or label a population ineligible under locked criteria rather than adapting the representation definition.
- Split strategy: Nested grouped resampling: all preprocessing, unit selection, condition normalization, capacity tuning, reliability estimation, and nuisance fitting occur within training folds. Outer folds hold out complete sessions when enough sessions exist, otherwise complete insertion-session populations with subject-blocked sensitivity analysis. Cross-condition test sets are disjoint from the training condition levels and never used to select model family.
- Claim ceiling: associational

**Analysis strategy**

1. Define the primary response window strictly before movement onset when timing permits, with a locked stimulus-aligned fallback and explicit exclusion of trials lacking the required temporal ordering.
2. Fit two preregistered representation families to the same population responses: an additive lower-dimensional task model with main effects for signed sensory evidence, prior, choice, and allowed timing or movement covariates; and a nonlinear mixed/high-dimensional model using the same inputs plus locked interaction basis terms.
3. Match effective capacity by parameter-count or degrees-of-freedom targets, identical regularization search spaces, training budgets, response normalization, and nested tuning procedure. Do not assign representation class from correct-versus-error performance.
4. 4 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Repeat the paired comparison after permuting success labels within session and prespecified task-condition strata; any retained improvement would indicate leakage or modeling artifact.; Use a temporally shifted neural window that cannot precede the indexed trial decision under the locked timing rule.
- Positive controls: Within training folds, recover documented task-variable signal from task-aligned responses above a label-permuted baseline without using the success endpoint to choose the representation class.; Verify that the task-and-movement baseline predicts choices better than a within-fold permuted-choice control.
- Alternative explanations: The nonlinear family has greater effective capacity, better optimization, or different regularization despite nominal matching.; Residual sensory evidence, prior, choice, reaction-time, or movement information explains success prediction rather than representational geometry.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- This observational dataset can support conditional out-of-sample predictive associations, not causal claims that a geometry enables successful behavior.
- Mixed and additive labels apply to locked model families and their fit to measured activity; they do not prove a unique biological coding mechanism.
- Any population-level conclusion is limited to quality-screened BWM insertion-session populations and the retained task and condition support.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

The plan directly compares prespecified mixed/high-dimensional and additive/lower-dimensional representation families, matches information and reliability rather than selecting on behavioral success, treats held-out success and cross-condition readout as separate endpoints, and specifies how aligned, independent, and trade-off outcomes retain their intended meanings.

**Before any later execution**

- Unresolved planning decisions: Locked numerical eligibility thresholds for unit count, valid trials, and condition-cell support.; Locked pre-response window and fallback timing rule.; plus 1 additional item(s) in the complete dossier
- Required future skills: Spike-shard decoder for documented delta_int_ticks and dense local cluster indices with synthetic method-recovery tests.; Nested group-aware capacity-matched representation comparison with leakage audits and paired endpoint aggregation.

### Scientific stakes

**Discriminating observation**

After comparably evaluating mixed/high-dimensional and additive/lower-dimensional representations for task-variable signal, model capacity, and decoding reliability, the key observation would be reproducible incremental prediction of held-out decision success across available condition or session partitions, assessed separately from cross-condition readout. The two endpoints should be classified as uniquely improved, jointly improved, jointly unimproved, or traded off across representation regimes.

**What possible outcomes would mean**

- Positive pattern: If mixed/high-dimensional geometry incrementally and reproducibly predicts held-out decision success after the stated comparisons, this would support a stable predictive association beyond reliability benefits and an aggregate correct-versus-error NMS comparison. Joint or selective improvement in cross-condition readout would further specify the association's outcome profile, without establishing causality.
- Negative pattern: If mixed/high-dimensional structure improves reliability or cross-condition readout but not held-out decision-success prediction—or if additive/lower-dimensional structure predicts success equally well or better—this would weaken the claim that nonlinear mixing has a distinct behavioral-predictive benefit in this setting while preserving possible coding or generalization benefits.
- Null or ambiguous pattern: If conditional behavioral-prediction and cross-condition-readout differences are indeterminate, unstable across available partitions, or sensitive to how representation classes and matching criteria are operationalized, the functional relationship would remain unresolved and would caution against treating dimensionality, reliability, or decoder performance as evidence of behavioral relevance.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan preserves the functional variant’s conditional, associational question: it compares prespecified additive and nonlinear representation families without choosing them on success, evaluates held-out decision-success prediction separately from cross-condition readout, accounts for dependence and confounding, and maintains an explicitly associational claim ceiling. Remaining numerical and implementation choices are appropriate pre-execution locks, not planning deficiencies.

Retained changes and locks:

- **Pre execution lock:** Before execution, lock outcome-blind eligibility and condition-support thresholds, response-window/fallback rules, and the interaction-basis and capacity-matching specification.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan operationalizes the functional variant faithfully: it pits prespecified additive and nonlinear representation families against each other without assigning class from the success outcome, matches capacity/training budget, and treats held-out decision-success prediction and cross-condition readout as separate, jointly reported endpoints (aligned/independent/traded-off), which is exactly the forbidden-merge distinction the family protects. Claim ceiling is associational and explicitly disclaims causal or unique-mechanism inference. Confounders (session/subject/lab/movement/reaction time) are addressed via nuisance covariates, grouped nested resampling, and positive/negative controls including label-permutation and non-causal timing checks. Dataset evidence (ephys and behavior schemas, coverage counts) grounds the described joins, spike-shard reconstruction, and covariate availability without inventing facts. The single Owner-identified issue (locking eligibility thresholds, timing window, interaction basis, and capacity-matching specification before execution) is correctly a pre-execution lock: these are bounded implementation parameters that do not undermine the credibility of the planning-stage design. No scientific blocker or hard-boundary issue is present at round 0.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
