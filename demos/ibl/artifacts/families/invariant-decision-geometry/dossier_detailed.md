# Invariant and reorganized population geometry during decision-making — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether population geometry preserves task-relevant meaning across naturally varying recording and behavioral contexts, or whether apparent stability and reorganization reflect different functional organizations.

The scientific tension is:

Population representations may preserve decision-relevant organization across contexts, reorganize while preserving equivalent meaning, or change because sensory, movement, and sampling conditions differ.

## Variant 1: Intrinsic cross-laboratory decision geometry without target-context calibration

### Why it matters

Separating zero-calibration transfer of stimulus–choice relations from movement-driven or alignment-enabled decoding would clarify when cross-context prediction supports a conserved decision organization rather than merely a reusable transfer procedure.

### Original and refined question

**Original Question Scientist proposal**

Does decision-relevant population geometry remain sufficiently conserved across subjects, sessions, and laboratories to support predictive generalization of stimulus and choice relationships?

**Post-novelty revised proposal**

In a decision task that dissociates stimulus evidence, choice, and movement output, does relational neural population geometry predict held-out stimulus–choice relationships across subjects, sessions, and explicitly characterized laboratory contexts without fitted target-context alignment, beyond movement, behavioral-state, recording-covariate, and distribution-alignment explanations?

**Reviewed refined question**

Across prespecified comparable BWM laboratory and session contexts, does a source-trained predictor based on a fixed relational population-geometry sketch predict held-out stimulus-conditioned choice without target labels, target fitting, or fitted cross-population alignment beyond movement and recording explanations?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If recordings include sufficiently comparable decision variables, movement measurements, behavioral-state indicators, and metadata about task contingencies, recording conditions, and preprocessing across contexts, they may support a later test of intrinsic stimulus–choice geometry against movement and alignment-based transfer explanations.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The inspected metadata contain 459 sessions, 295920 trials, 2066041 events, and 75395 units. Session and trial metadata include lab, while trials include choice, feedbackType, probabilityLeft, contrastLeft, contrastRight, stimOn_times, goCue_times, firstMovement_times, response_times, feedback_times, bwm_include, and rewardVolume. Aggregate metadata show 12 lab labels, each represented by sessions and trials. Unit metadata include pid, eid, cluster_id, probe_name, quality label, atlas and region annotations, location, spike_count, and firing_rate.
  - Limitation: Aggregate coverage by lab does not prove that task contingencies, probe placement, preprocessing, or behavioral measurement are comparable for each planned contrast.
  - Limitation: This bounded metadata query did not compute outcome associations, decoding performance, geometry, or any scientific result.
- **Unverified planning evidence:** The BWM behavior package provides eid/trial_id-keyed trial behavior features and wheel trial features, plus eid/trial_id/camera/window_spec-keyed DLC trial features. Wheel features include movement onset, peak time, direction, amplitude, mean velocity, and maximum velocity; DLC features include summary measures. The inspected feature surfaces contain 295920 trial-behavior rows, 258614 wheel-trial rows, and 847042 DLC-trial rows, with availability metadata for wheel and DLC.
  - Limitation: Wheel and DLC coverage is incomplete and varies by session or camera, so movement-controlled analyses must use prespecified complete-case and missingness sensitivity rules.
  - Limitation: The listed behavioral features are not direct measures of arousal or every behavioral state named in the scientific intent.
- **Unverified planning evidence:** The BWM ephys schema declares session, insertion, unit, trial, and event tables; trial records are keyed by eid and trial_id, unit records by pid and cluster_id, and a sharded spike store is keyed by pid. The schema also declares event-response features keyed by pid, cluster_id, event_name, and window_spec.
  - Limitation: The schema does not itself establish cross-laboratory protocol equivalence, behavioral-state coverage, or reliability for any particular planned comparison.
  - Limitation: No raw spike trains, event rows, or trial rows were inspected for this planning evidence.

### Plan at a glance

- Population and scope: Good-quality recorded units from BWM sessions that pass prespecified trial, context-registry, and measurement-coverage rules. Inference is restricted to sampled BWM sessions, subjects, laboratories, and recording contexts.
- Unit of observation: One trial's fixed-dimensional population-geometry sketch, observed task covariates, and held-back binary choice label.
- Unit of inference: A held-out session or laboratory-context contrast, with subject and session dependence retained in resampling and uncertainty estimation.
- Hierarchy and dependence: Trials nest within sessions, units within insertions, and sessions within subjects and laboratories. Source-only tuning occurs in inner grouped source folds; outer evaluation holds out whole sessions and, separately, all sessions from one laboratory.
- Validation: Use nested source-only tuning, source-label permutation, source movement-matched label permutation, held-out pipeline audit logs, and synthetic method-recovery simulations. The audit must verify that target prediction inputs are invariant to replacing target choices and that no target-fitted transform is called. Simulations must distinguish conserved relational structure from shared movement structure and from target-label alignment.
- Split strategy: Primary outer splits hold out all trials from one target session; secondary splits hold out all sessions from one target laboratory. Source and target partitions are disjoint before any tuning. Target choices are inaccessible until scoring; target neural activity is passed only through the fixed per-trial sketch formula.
- Claim ceiling: predictive

**Analysis strategy**

1. For each trial, use fixed task-time bins and a fixed response transform to form each unit's within-trial temporal response profile. Create a neuron-permutation-invariant relational sketch by taking a fixed empirical-quantile grid of all pairwise distances among those profiles, together with fixed quantiles of the profile norms. This formula has no learned parameters, no neuron identities, no source-to-target correspondence, and no target-context normalization, template, or alignment.
2. Fit the predictive rule only in source data: source trial geometry sketches, pre-observation task covariates such as signed visual evidence and prior, and prespecified movement or recording covariates predict source choice. All model selection, imputation, residualization, and scaling parameters are estimated from source training folds only.
3. For every held-out target trial, calculate the same fixed sketch from that trial alone and attach only observed target task and prespecified covariates. Do not use target choice labels, target choice-conditioned cells, target response aggregates, target-fitted scalers, target calibration, or any source-target alignment. Reveal target choices only once to score the already-generated predictions.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permuted source choice labels and source geometry sketches built from task-irrelevant trial order.; Movement-matched source trials with source choice labels permuted within source contexts.; plus 1 additional item(s) in the complete dossier
- Positive controls: Within-source grouped cross-validated prediction using the same fixed trial sketch.; Synthetic recovery of injected relational structure under documented nesting and missingness patterns.
- Alternative explanations: Shared movement kinematics or behavioral-state proxies drive apparent transfer.; Target calibration, distribution alignment, recording placement, or preprocessing differences explain transfer patterns.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Observational cross-laboratory recordings cannot establish that geometry causes choice or that laboratory membership is causal.
- Wheel and DLC do not exhaust movement or behavioral state, and arousal is not directly established by the inspected surfaces.
- The fixed sketch tests one transferable relational summary and does not establish conservation of every possible neural geometry.

**Why the plan serves the question**

It retains the required no-target-calibration test of conserved decision-relevant relational geometry while solving noncorresponding-population transfer through a fixed identity-free representation instead of a target-conditioned geometry or fitted alignment.

**Before any later execution**

- Unresolved planning decisions: Lock the context registry and eligible context contrasts before execution.; Lock quality, support, reliability, and movement-missingness thresholds before any target outcome is accessed.; plus 1 additional item(s) in the complete dossier
- Required future skills: Streaming BWM spike-shard decoding into fixed trial-level, neuron-permutation-invariant geometry sketches.; Auditable source-only cross-context prediction with target-label firewall checks and group-aware resampling.

### Scientific stakes

**Discriminating observation**

Evidence favoring conserved decision geometry would require a source-defined relational geometry to predict held-out stimulus–choice relationships without target labels or fitted subject-, session-, domain-, or laboratory-specific alignment, after accounting for movement kinematics, behavioral state, and generic recording/session covariates, and to exceed non-geometric decoding and generic distribution-alignment baselines. Laboratory transfer must be evaluated separately for contexts that share versus differ in task contingencies, behavioral measurements, recording modality or placement, and preprocessing. Partial transfer that follows task contingencies despite adequate measurement and baseline performance would support context-specific coding; partial transfer that instead tracks recording or preprocessing differences, or is rescued only by calibration, would leave conservation unresolved because measurement or alignment limitations remain plausible.

**What possible outcomes would mean**

- Positive pattern: Transfer meeting these criteria would support the bounded claim that a reusable decision-relevant relational organization spans the tested subjects, sessions, and laboratory contrasts and is not adequately explained by movement-linked structure or fitted alignment.
- Negative pattern: If reliable within-context decision geometry and adequate baseline performance are present but uncalibrated transfer fails selectively across changes in task contingencies while remaining robust to measurement differences, the result would favor context-specific decision coding over conservation across those tested contexts.
- Null or ambiguous pattern: If transfer is weak or partial and covaries with recording modality, placement, preprocessing, missing behavioral controls, low reliability, or dependence on target-context calibration, the result would not distinguish context-specific coding from measurement or alignment limitations and would leave conservation unresolved.

## Variant 2: Semantic preservation through full-geometric and relational reorganization

### Why it matters

Separating full geometric identity from invariant cross-context prediction would clarify whether stable neural meaning requires conserved population organization or can persist through a stronger form of functional reorganization, without mistaking behavioral modulation for representational change.

### Original and refined question

**Original Question Scientist proposal**

Can population geometry reorganize across behavioral contexts while preserving equivalent stimulus or decision meaning?

**Post-novelty revised proposal**

Across matched decision contexts, can the full representational distance geometry of task-condition population states genuinely reorganize while an out-of-context predictor preserves the same stimulus-conditioned choice relationship, even when low-dimensional or temporal task organization and behavioral-state modulation are assessed separately?

**Reviewed refined question**

Across prespecified matched BWM decision contexts, can full stimulus-and-epoch-defined population distance geometry genuinely reorganize while a source-trained, fixed-sketch predictor preserves the same held-out stimulus-conditioned choice relationship without target labels, target fitting, or alignment?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If recordings contain sufficiently comparable task conditions, choices, and behavioral-state measurements across contexts, they may support proposal-stage comparison of full distance geometry, lower-dimensional or temporal organization, and out-of-context prediction without treating successful behavior or context decoding as semantic equivalence.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The inspected metadata contain 459 sessions, 295920 trials, 2066041 events, and 75395 units. Session and trial metadata include lab, while trials include choice, feedbackType, probabilityLeft, contrastLeft, contrastRight, stimOn_times, goCue_times, firstMovement_times, response_times, feedback_times, bwm_include, and rewardVolume. Aggregate metadata show 12 lab labels, each represented by sessions and trials. Unit metadata include pid, eid, cluster_id, probe_name, quality label, atlas and region annotations, location, spike_count, and firing_rate.
  - Limitation: Aggregate coverage by lab does not prove that task contingencies, probe placement, preprocessing, or behavioral measurement are comparable for each planned contrast.
  - Limitation: This bounded metadata query did not compute outcome associations, decoding performance, geometry, or any scientific result.
- **Unverified planning evidence:** The BWM behavior package provides eid/trial_id-keyed trial behavior features and wheel trial features, plus eid/trial_id/camera/window_spec-keyed DLC trial features. Wheel features include movement onset, peak time, direction, amplitude, mean velocity, and maximum velocity; DLC features include summary measures. The inspected feature surfaces contain 295920 trial-behavior rows, 258614 wheel-trial rows, and 847042 DLC-trial rows, with availability metadata for wheel and DLC.
  - Limitation: Wheel and DLC coverage is incomplete and varies by session or camera, so movement-controlled analyses must use prespecified complete-case and missingness sensitivity rules.
  - Limitation: The listed behavioral features are not direct measures of arousal or every behavioral state named in the scientific intent.
- **Unverified planning evidence:** The BWM ephys schema declares session, insertion, unit, trial, and event tables; trial records are keyed by eid and trial_id, unit records by pid and cluster_id, and a sharded spike store is keyed by pid. The schema also declares event-response features keyed by pid, cluster_id, event_name, and window_spec.
  - Limitation: The schema does not itself establish cross-laboratory protocol equivalence, behavioral-state coverage, or reliability for any particular planned comparison.
  - Limitation: No raw spike trains, event rows, or trial rows were inspected for this planning evidence.

### Plan at a glance

- Population and scope: BWM sessions and recording populations meeting prespecified task-condition, movement-coverage, reliability, and matched-context criteria. Conclusions are restricted to sampled recording contexts.
- Unit of observation: A trial-level fixed geometry sketch for prediction and a cross-validated stimulus-and-epoch-defined population distance matrix for the separate reorganization test.
- Unit of inference: A matched context pair or held-out session or laboratory contrast, with uncertainty propagated across sessions, subjects, and resampled trials.
- Hierarchy and dependence: Trials nest within sessions, units within insertions, and sessions within subjects and laboratories. Geometry split halves, source-model tuning, and outer context-pair resampling retain those groups. Prediction target labels remain unavailable before scoring.
- Validation: Use independent trial partitions for geometry and prediction; source-label and condition-label permutations; target-label invariance audits; reliability simulations varying population sampling; and synthetic recovery cases of neuron remapping, orthogonal drift, conserved low-dimensional organization, temporal conservation, and genuine full reorganization.
- Split strategy: For each context pair, estimate geometry in independent trial halves. For prediction, train and tune only in source sessions and hold target sessions or laboratories intact. Target choices remain inaccessible until the frozen predictions are scored, and the target neural stream is processed only by the fixed sketch formula.
- Claim ceiling: predictive

**Analysis strategy**

1. For the reorganization test, define matched task conditions only by observed exogenous task design variables: signed visual-evidence bin, prior-probability block, and fixed task epoch. Never make a target stimulus-by-choice cell. Estimate full cross-validated population distance matrices separately in each context without neuron pairing, using independent trial halves and fixed reliability correction.
2. Prespecify a metric family before execution: cross-validated squared Euclidean distances on fixed-duration, square-root transformed population counts as primary, with correlation distance and cosine distance as sensitivity metrics. Use fixed stimulus-to-movement and movement-to-response windows; summarize low-dimensional organization by fixed rank three and rank six classical-MDS distance preservation, and temporal organization by fixed time-bin trajectory-distance correlation. Adjust the primary full-geometry, low-dimensional, and temporal family by Holm correction across the three prespecified summary families.
3. Separately create the same parameter-free, neuron-permutation-invariant per-trial sketch defined for variant 01. Train the stimulus-conditioned choice rule only on source trials using that sketch, observed stimulus and prior covariates, and source-fitted nuisance handling. The frozen rule is applied to each target trial using only its neural response and observed non-choice covariates.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Source choice-label permutations for prediction, while preserving all target inputs.; Stimulus-condition-label permutations within context and time-bin-order permutations for temporal geometry.; plus 1 additional item(s) in the complete dossier
- Positive controls: Within-context split-half recovery of stimulus-and-epoch geometry above its condition-permutation null.; Within-source grouped cross-validated prediction using the fixed trial sketch.; plus 1 additional item(s) in the complete dossier
- Alternative explanations: Neuron sampling, recording instability, or orthogonal drift produces apparent full-geometry change.; Conserved low-dimensional or temporal organization rather than genuinely reorganized meaning supports prediction.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- The plan tests predictive preservation in observational recordings, not a causal identity of neural meaning.
- Fixed metric, rank, window, and behavioral-covariate choices do not exhaust all representational descriptions or behavioral states.
- Stimulus-and-epoch condition geometry intentionally avoids target choice leakage; it does not itself test a target choice-conditioned geometry.

**Why the plan serves the question**

It preserves the sibling's stronger distinction: full task-condition geometry is tested for reorganization independently of, and without leaking into, source-only prediction of the same stimulus-conditioned choice relationship. The choice-free target geometry is a necessary firewall refinement, not a change from reorganization to simple decoding.

**Before any later execution**

- Unresolved planning decisions: Lock the matched-context registry and eligibility conditions without assuming semantic equivalence.; Lock quality, reliability, support, movement-missingness, fixed bin-edge, and response-transform choices before target outcomes are accessed.; plus 1 additional item(s) in the complete dossier
- Required future skills: Streaming BWM spike-shard decoding into fixed trial-level geometry sketches and stimulus-and-epoch population summaries.; Reliability-corrected geometry, low-dimensional and temporal summary evaluation with source-only target-label-firewalled prediction.

### Scientific stakes

**Discriminating observation**

Evidence favoring the focal account would require a reliable cross-context change in the full pairwise distance geometry of matched task-condition states that is not reducible to neuron remapping, orthogonal drift, measurement instability, or movement, arousal, and behavioral-state modulation; separate evidence that the relevant low-dimensional and temporal relational organization is not simply conserved; and preservation by a predictor trained in one context of the same stimulus-conditioned choice relationship in a held-out context. Geometry change with failed transfer would favor loss of meaning, whereas disappearance of the geometry change after reliability or behavioral controls would favor apparent reorganization.

**What possible outcomes would mean**

- Positive pattern: If genuine full-geometric and relational reorganization coexists with preserved out-of-context prediction of the stipulated decision relationship, stable representational meaning would not require conservation of either the full geometry or the task organization emphasized by the closest prior work.
- Negative pattern: If reliable geometric reorganization remains after behavioral and measurement controls but the stipulated cross-context predictive relationship is lost or altered, structural change would mark a corresponding change in decision meaning rather than synonymous coding.
- Null or ambiguous pattern: If the geometric difference is not distinguishable from measurement instability or behavioral-state modulation, or if only neuron-level patterns change while low-dimensional or temporal organization remains conserved, the proposed stronger dissociation would remain unsupported and the observations would be compatible with confounding or the closest conservation accounts.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The revision resolves the prior scientific blocker: both variants now use a fixed, neuron-identity-free trial representation that is computable independently in source and target contexts, with target choices unavailable until final scoring and no target-side fitting or alignment. Variant 01 retains the uncalibrated conserved-geometry transfer contrast, while variant 02 separately tests choice-free full-geometry reorganization and preserved source-only prediction. Remaining items are pre-execution locks, not planning-stage scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Create an auditable context registry that classifies each planned session and laboratory contrast by task contingency, probe placement, preprocessing, and movement-measurement comparability using documentation and metadata.
- **Pre execution lock:** Prespecify retained trial, unit, condition-cell, reliability, and movement-missingness rules without inspecting cross-context target outcomes.
- **Pre execution lock:** For the reorganized-geometry variant, prespecify the distance-metric family, low-dimensional and temporal summaries, time windows, and multiplicity treatment.
- 1 additional review item(s) remain in the complete dossier.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The round-1 revision credibly resolves the round-0 scientific blocker on leakage-free, cross-population-transferable prediction. Both siblings now compute a fixed, parameter-free, neuron-permutation-invariant per-trial relational sketch (quantile grid of pairwise unit-profile distances plus norm quantiles) that requires no neuron correspondence and no target-side fitting; the predictive rule is trained only on source data and applied to target trials using observed non-choice inputs, with target choice revealed solely to score frozen predictions. Variant 2 additionally redefines its reorganization test using stimulus-and-epoch-defined (not choice-conditioned) matched conditions, closing the prior leakage path while preserving the required distinction between full-geometry reorganization and source-only preserved stimulus-conditioned choice prediction. Claim ceilings remain predictive, alternative explanations (movement, behavioral state, distribution alignment, recording covariates) are addressed with matched baselines and permutation/synthetic controls, and the sibling contrast (uncalibrated conserved-geometry transfer vs. reorganization-with-preserved-meaning) is maintained without conflating geometric and semantic conservation. The four remaining items (context registry, eligibility/missingness rules, metric-family and window locks, and freezing the fixed sketch formula via synthetic recovery) are pre-execution implementation locks, not scientific blockers, consistent with their prior classification and this round's status.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
