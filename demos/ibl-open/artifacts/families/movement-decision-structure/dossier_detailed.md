# Decision-related population structure after richer movement accounting — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

A family testing whether apparent decision-related activity survives richer embodied alternatives or is better understood as behaviorally structured activity, with target-preservation and reinterpretation variants.

The scientific tension is:

Population activity associated with decisions may encode a latent decision construct, richer movement and posture, or inseparable mixtures; coarse motor controls may leave this ambiguity unresolved.

## Variant 1: Decision-residual variant

### Why it matters

A temporally explicit, held-out comparison against the full available behavioral description can determine whether movement-accounted choice prediction extends beyond the cited report-movement result while keeping the conclusion at an associational rather than causal level.

### Original and refined question

**Original Question Scientist proposal**

Does population activity retain decision-related structure after accounting for richer concurrent movement and pose variation rather than only coarse behavioral covariates?

**Post-novelty revised proposal**

Before any report-relevant movement begins, does neural population activity provide reproducible out-of-sample incremental prediction of the eventual reported choice beyond a full model of available multidimensional movement and pose variables?

**Reviewed refined question**

Before a prespecified report-relevant movement boundary, does pre-response population activity add held-out prediction of eventual reported choice beyond synchronized multidimensional movement and pose?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Joint neural, choice, response-time, movement, and pose measurements may permit comparison of neural-plus-behavioral and behavior-only prediction of eventual reported choice before report-relevant movement, subject to verification of synchronization, coverage, and temporal precision.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The trial metadata has eid and trial_id with choice, stimOn_times, goCue_times, firstMovement_times, response_times, feedback_times, and bwm_include. The derived behavior table has reaction_time and movement_time keyed by the same trial identifiers.
  - Limitation: Column presence does not establish timestamp synchronization precision or the meaning of each movement onset for every trial.
  - Limitation: No outcome distribution, association, or scientific result was calculated.
- **Unverified planning evidence:** The inspected behavior shard contains delta-encoded DLC coordinate streams and likelihood streams for body, left, and right cameras, including tail, nose, pupil, paw, tongue, and pupil-diameter features. The package summary documents an aggressive DLC-delta and wheel-native compression profile.
  - Limitation: One shard was inspected only for storage member names; modality coverage and timing must be checked per retained session.
  - Limitation: The semantic shard codec must be decoded and its timestamps validated by a future executor capability before analysis.
- **Unverified planning evidence:** The behavior package documents session and trial keys plus trial-level behavior, wheel, DLC, event-aligned behavior, and behavioral-state feature tables; trial-level behavioral tables join on eid and trial_id, while DLC features additionally join on camera and window_spec.
  - Limitation: The schema establishes available surfaces and keys, not the validity of any particular behavioral construct.
  - Limitation: Planning must restrict analyses to sessions and trials with the required modalities and documented quality checks.
- 1 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Included task trials in sessions with a recorded insertion, valid choice and event timing, decodable synchronized behavioral streams, and prespecified modality-quality criteria; inference will generalize over retained sessions and insertions, not to unmeasured behavior or all mice.
- Unit of observation: A trial-by-insertion population feature vector built only from samples preceding that trial's prespecified movement boundary.
- Unit of inference: Session and insertion, with trial observations clustered within them.
- Hierarchy and dependence: Split and resample by session, keep all trials from a session in one fold, and summarize insertion-level estimates before session-level aggregation to avoid pseudo-replication.
- Validation: Before target evaluation, verify stream decoding on structural metadata, alignment against recorded trial anchors, feature availability, fold isolation, and a label-permutation negative-control pipeline; use only training data for scaling, imputation, dimension reduction, and hyperparameter selection.
- Split strategy: Primary split is grouped outer cross-validation by session; inner grouped folds tune each matched model family. A secondary leave-insertion-out analysis is conditional on multiple insertions per session.
- Claim ceiling: associational

**Analysis strategy**

1. Define the boundary as min(firstMovement_times, independently derived report-relevant onset when valid) minus a prespecified synchronization and onset-uncertainty margin; exclude trials without a defensible boundary.
2. Build a behavior-only model from training-fold standardized, likelihood-screened, pre-boundary pose, pupil, and wheel histories, using only training-fold dimension reduction and matched regularization.
3. Compare behavior-only with behavior-plus-pre-boundary population activity using nested, session-held-out validation and identical tuning budgets.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permute choice labels within session and task-condition strata after feature construction.; Use a post-boundary neural window only as a leakage-sensitivity diagnostic, never as evidence for the target claim.
- Positive controls: Verify that the decoder recovers documented trial-anchor ordering and that known wheel and camera streams produce nonconstant pre-boundary features when recorded.
- Alternative explanations: Residual neural prediction reflects unmeasured behavior, pupil-linked arousal, or clock misalignment.; The behavioral comparator absorbs a genuine incipient decision because movement is downstream of the decision.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- A surviving increment cannot establish a causal decision representation.
- The full available behavioral description remains an imperfect proxy for unmeasured movements and internal state.

**Why the plan serves the question**

The plan preserves the target contrast by giving multidimensional behavior the competing-explanation role and asking only whether pre-movement neural information improves held-out eventual-choice prediction.

**Before any later execution**

- Unresolved planning decisions: Exact safety margin and eligibility threshold await codec-level timing validation.; The prespecified population representation must be selected before outcome evaluation.
- Required future skills: Decode zip_semantic_shards_v2 behavioral signals and expose timestamps, likelihood masks, and camera channels.; Decode delta-encoded spike shards into bounded per-trial pre-response counts without loading full recordings.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

Success requires that population activity improve out-of-sample prediction of eventual reported choice over a behavior-only model containing all available synchronized multidimensional movement and pose variables, rather than only the overt effector or a coarse motion summary. The increment must occur in a pre-response window ending before the earliest detected report-relevant movement by a prespecified margin justified by synchronization precision and movement-onset uncertainty, and it must reproduce across appropriate held-out trials and available units, populations, or sessions. Such a result supports only a residual decision-related association, not causal decision representation.

**What possible outcomes would mean**

- Positive pattern: A reproducible pre-movement predictive increment would support the bounded claim that neural populations contain choice-related information not reducible to the measured multidimensional behavioral description. It would motivate, but not substitute for, separate causal tests of decision representation.
- Negative pattern: If the full behavioral model eliminates reliable pre-movement incremental neural prediction, the evidence would favor the interpretation that apparent choice-related population structure is largely mediated by measured embodied and report-related variation, weakening a distinct residual-choice account.
- Null or ambiguous pattern: If incremental prediction is unstable across held-out partitions, sessions, population definitions, behavioral descriptions, or defensible temporal margins, the data would not discriminate residual choice association from behavioral confounding or measurement limitations.

## Variant 2: Conditional pre-response embodied-target variant

### Why it matters

Separating neural encoding of movement from prediction relevant to choice and response time would clarify whether multidimensional behavior contributes distinct structure to decision dynamics or primarily indexes movement-consequent and state-related neural variance.

### Original and refined question

**Original Question Scientist proposal**

Do brain-wide populations represent multidimensional movement and pose in ways that explain decision and response-time variation better than simpler state or locomotor summaries?

**Post-novelty revised proposal**

Do multidimensional pose and movement features add held-out prediction separately for brain-wide neural activity, choice, and response time beyond task-event timing, locomotion, arousal, and latent behavioral-state summaries—and do any choice and response-time gains arise before or independently of overt response execution?

**Reviewed refined question**

Do synchronized multidimensional pose and movement features improve held-out neural activity, eventual choice, and response-time prediction beyond task, locomotor, arousal, and latent-state comparators, with outcome prediction restricted before response execution?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If concurrent pose, movement, neural, choice, response-time, event, and state-related measurements are sufficiently synchronized and complete, they may support nested held-out comparisons of rich behavioral features against event timing, locomotion, arousal, and latent-state summaries, with pre-response and execution-independent outcome prediction assessed separately from neural prediction.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The trial metadata has eid and trial_id with choice, stimOn_times, goCue_times, firstMovement_times, response_times, feedback_times, and bwm_include. The derived behavior table has reaction_time and movement_time keyed by the same trial identifiers.
  - Limitation: Column presence does not establish timestamp synchronization precision or the meaning of each movement onset for every trial.
  - Limitation: No outcome distribution, association, or scientific result was calculated.
- **Unverified planning evidence:** The inspected behavior shard contains delta-encoded DLC coordinate streams and likelihood streams for body, left, and right cameras, including tail, nose, pupil, paw, tongue, and pupil-diameter features. The package summary documents an aggressive DLC-delta and wheel-native compression profile.
  - Limitation: One shard was inspected only for storage member names; modality coverage and timing must be checked per retained session.
  - Limitation: The semantic shard codec must be decoded and its timestamps validated by a future executor capability before analysis.
- **Unverified planning evidence:** The behavior package documents session and trial keys plus trial-level behavior, wheel, DLC, event-aligned behavior, and behavioral-state feature tables; trial-level behavioral tables join on eid and trial_id, while DLC features additionally join on camera and window_spec.
  - Limitation: The schema establishes available surfaces and keys, not the validity of any particular behavioral construct.
  - Limitation: Planning must restrict analyses to sessions and trials with the required modalities and documented quality checks.
- 1 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Included task trials and insertions with valid outcome timing plus adequate decodable camera and wheel coverage; neural, choice, and response-time analyses will use the same eligibility ledger where possible and report outcome-specific attrition.
- Unit of observation: A trial-level feature history paired separately with a neural population target, choice target, or response-time target.
- Unit of inference: Session and insertion for neural targets, and session for choice and response-time targets.
- Hierarchy and dependence: Retain nesting of trials in session and units in insertion; group all session trials within a fold and aggregate target-specific improvements at the session level.
- Validation: Validate stream timestamps, modality coverage, task-anchor ordering, training-fold-only state estimation, and equal-flexibility tuning before evaluating target contrasts. Use label permutation and temporally shifted rich features as negative controls, preserving session grouping.
- Split strategy: Primary nested grouped cross-validation holds out sessions. Neural analyses additionally preserve insertion grouping and use no unit or trial from a held-out session during fitting or feature reduction.
- Claim ceiling: associational

**Analysis strategy**

1. Construct nested baseline models using task-event timing, wheel locomotion, pupil arousal when available, and training-fold latent-state summaries; construct matched rich-behavior models with equal regularization and tuning budgets.
2. Evaluate held-out improvement separately for neural population activity, eventual choice, and response time; do not merge these endpoints into one success score.
3. For choice and response time, permit only feature samples before a prespecified execution boundary derived from movement and response timing minus a validated safety margin.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Within-session condition-stratified label permutation for choice and response-time targets.; Time-shifted or post-boundary rich behavior as a leakage and temporal-specificity diagnostic rather than a target test.
- Positive controls: Verify documented task-event ordering and successful extraction of recorded wheel, camera, and pupil channels when availability metadata indicates presence.
- Alternative explanations: Rich features only encode overt or uninstructed movement and therefore improve neural targets without decision relevance.; Task locking, execution leakage, or clock error produces apparent outcome prediction.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- Prediction cannot demonstrate that embodied structure causes a decision or is a neural representation in the causal sense.
- Pupil, wheel, and learned state summaries are incomplete controls for internal state and unobserved behavior.

**Why the plan serves the question**

The plan treats rich behavior as the target, separately tests its neural and behavioral predictive value, and makes execution-independent outcome value a necessary condition for the stronger embodied interpretation.

**Before any later execution**

- Unresolved planning decisions: Exact pre-execution boundary and safety margin await timing validation.; The predeclared neural population target and response-time transformation must be fixed before outcome evaluation.
- Required future skills: Decode semantic behavior shards and synchronize multi-camera, pupil, and wheel timestamps to trial anchors.; Decode spike shards into bounded neural population targets and enforce insertion and session grouping.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

The stronger embodied interpretation would require reproducible held-out improvement from rich pose and movement over event timing, locomotion, arousal, and latent-state summaries, reported separately for neural activity, choice, and response time; critically, choice or response-time improvement would need to persist when features coincident with or following overt response execution cannot supply the prediction. Neural improvement without independent pre-response outcome improvement would count only as movement encoding or neural predictability, not decision-relevant embodied representation.

**What possible outcomes would mean**

- Positive pattern: If rich behavioral features improve all three outcomes under the nested comparisons and retain choice or response-time value before or independently of overt execution, the result would support an associational claim that multidimensional embodied structure contributes predictive information about decision dynamics beyond simple state accounts.
- Negative pattern: If rich features improve neural prediction but not pre-response or execution-independent choice and response-time prediction, or if their advantage disappears after latent-state adjustment, the result would favor movement encoding, task locking, or state-related variance rather than a distinct decision-relevant embodied representation.
- Null or ambiguous pattern: If held-out differences are small, unstable, or sensitive to behavioral representation, timing boundary, or comparator flexibility, the evidence would not distinguish multidimensional embodied structure from latent-state and movement-consequent explanations.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct target roles for movement and provide credible, held-out, session-grouped associational tests with explicit leakage, alignment, dependence, and interpretation safeguards. Remaining choices are appropriate pre-execution locks rather than deficiencies in the planning dossier.

Retained changes and locks:

- **Pre execution lock:** Prespecify and validate the timing-error safety margin, execution/movement boundaries, and resulting eligibility rule before outcome evaluation.
- **Pre execution lock:** Prespecify the behavioral and neural feature representations, including training-fold-only reduction, modality-quality criteria, and the response-time transformation before outcome evaluation.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their assigned, opposite roles for movement (competing explanation vs. target of interest) as required by the family's forbidden-semantic-merge guardrails, and each presents an evidence-grounded, associational plan with explicit boundary definitions, matched-flexibility comparisons, session/insertion-grouped validation, negative and positive controls, and honest interpretation limits (no causal decision-representation claim). Dataset grounding is adequate for planning: documented trial/behavior/ephys schemas support the proposed joins and constructs, with future shard-decoding and alignment work correctly flagged as required executor skills rather than treated as already solved. The two Owner-classified issues are properly scoped as pre-execution locks (timing-margin/eligibility rule; feature-representation and RT-transformation prespecification) that must be fixed before outcome evaluation but do not undermine the current planning product's scientific credibility. No scientific blocker or hard-boundary issue is present at this initial round.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
