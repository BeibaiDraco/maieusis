# Neural trajectory geometry versus richer behavioral explanations — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Scientific rejection terminal**
- Authority: **Automated host authorization, planning only; no independent review was recorded**
- Accepted-plan authority: **No**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether apparent neural organization for curved reaching reflects trajectory-level structure beyond simple kinematics, while separating prospective geometry from execution-related residual structure.

The scientific tension is:

Population activity may encode or dynamically organize path-level structure, but apparent trajectory representations can also arise from hand, cursor, eye, timing, or other correlated behavioral variables. Richer covariates can adjudicate these accounts without being treated merely as nuisance.

## How to read this terminal

The scientific planning/review process closed this family without an accepted plan. Rejection is a scientific terminal, not evidence that the proposed phenomenon is false.

**Recorded public status note**

automated_reject

## Variant 1: Prospective endpoint-matched test of path-level population geometry beyond component movement features and pre-movement state proxies

### Why it matters

This tests whether preparatory activity has path-level population organization rather than merely carrying decodable curvature-related or component-feature information, while directly confronting measured proxy explanations and geometric-construction dependence.

### Original and refined question

**Original Question Scientist proposal**

Before movement, does population geometry distinguish intended curved versus straight path structure beyond endpoint and immediately observable hand or eye state?

**Post-novelty revised proposal**

Before movement, do endpoint-matched curved and straight plans exhibit a population-geometric distinction that is independent of initial direction, endpoint direction, distance, speed, and immediately observable hand and eye state, and concordant across scientifically justified geometry-sensitive representations or metrics?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If delayed straight and curved reaches include sufficiently overlapping pre-movement neural, hand, and eye measurements and permit endpoint-matched comparisons, they may support a later evaluation of residual path-level population geometry; these conditions require verification.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 (MC_Maze_Small, version 0.220113.0408) is a single-subject (rhesus macaque 'Jenkins') delayed center-out reaching task with obstructing barriers forming a maze, producing a mix of straight and curved reaches. Neural activity was recorded from electrode arrays in primary motor cortex (M1) and dorsal premotor cortex (PMd). Behavioral channels recorded are cursor position, hand position, and eye position; hand velocity was computed offline from hand position. The release is deliberately limited to 100 train and 100 test trials and is distributed as part of the Neural Latents Benchmark '21.
  - Limitation: Single subject, single session; no cross-animal or cross-session generalization is possible.
  - Limitation: This is dataset-scope documentation, not a scientific result; it establishes what surfaces exist, not any effect.
- **Unverified planning evidence:** The train file exposes 100 trials with a trials table containing: start_time, stop_time, trial_type, trial_version, maze_id, success (all True), target_on_time, go_cue_time, move_onset_time, rt, delay, num_targets, target_pos, num_barriers, barrier_pos, active_target, split. There are 9 unique maze_id values, each crossed with 3 trial_version values, giving 27 unique conditions. Trials-per-condition is small: 21 conditions have 4 trials, 4 have 3, and 2 have 2. The three versions per maze are structurally distinct: version 0 has 0 barriers and 1 target (straight reach), version 1 has 9 barriers and 1 target (curved reach), and version 2 has 9 barriers and 3 targets (curved reach with distractor targets). Overall 32 trials have 0 barriers and 68 have 9 barriers; 66 have 1 target and 34 have 3 targets.
  - Limitation: Only ~2-4 trials per condition, which severely limits any per-condition or repeated-execution estimation.
  - Limitation: Counts describe the train file only; the test file is inspected separately.
- **Unverified planning evidence:** The train units table has 142 sorted units with columns (heldout, spike_times, obs_intervals, electrodes). Using the documented NLB unit-ID region convention (leading digit 1 = PMd, leading digit 2 = M1), the leading-digit distribution is 72 units with leading 1 (PMd) and 70 with leading 2 (M1), so both regions are represented. The heldout flag partitions units into 107 held-in and 35 held-out; these held-out units are the NLB co-smoothing modeling target, not a behavioral hold-out. Per DATASET_NOTES.md, raw electrode indices for M1 units require a documented +96 electrode-row correction and must not be used alone to conclude the population is PMd-only. A combined M1+PMd population is available, with region stratification possible via the unit-ID convention.
  - Limitation: Region assignment relies on the documented unit-ID convention plus the M1 +96 electrode correction; any residual disagreement must remain visible rather than being resolved by assuming a region is absent.
  - Limitation: Single session; unit yield and quality are fixed and cannot be increased.
- 3 additional typed inspection statement(s) remain in the complete planning record.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

Support for prospective path organization would require an endpoint-matched curved-versus-straight preparatory distinction that remains after accounting for initial direction, endpoint direction, distance, speed, and immediately observable hand and eye state, and whose interpretation is concordant across prespecified, scientifically justified geometry-sensitive representations or metrics. Generic decoding, tuning, or a distinction confined to one geometric construction would not satisfy this observation.

**What possible outcomes would mean**

- Positive pattern: A residual and cross-representation-concordant distinction would support a bounded associational claim that preparatory population geometry contains path-level organization not explained by the specified movement features or immediately observable hand and eye state.
- Negative pattern: If the apparent distinction is consistently eliminated after accounting for the specified variables, or is consistently absent under informative endpoint-matched comparisons, the result would weaken the prospective path-organization account and favor a component-feature or observable-state explanation.
- Null or ambiguous pattern: If conclusions vary across scientifically justified geometric constructions, endpoint matching or covariate separation is inadequate, or relevant pre-movement measurements lack sufficient overlap, prospective path organization would remain unresolved rather than being supported or rejected.

## Variant 2: Execution-period double contrast separating full-trajectory encoding, behavior-specific residuals, and route-intention association

### Why it matters

This distinction would clarify whether execution-period population structure is adequately described by rich trajectory history, remains behavior-specific, or is associated with a route context that generalizes across execution differences, without treating any residual as evidence of a curvature-specific mechanism.

### Original and refined question

**Original Question Scientist proposal**

During movement, does population activity contain curved-path-specific structure beyond jointly measured hand, cursor, eye, and velocity-related behavior, or is the apparent neural distinction explained by those richer behavioral variables?

**Post-novelty revised proposal**

During movement, after conditioning on the full recorded time-varying hand trajectory—including nonlinear and history-dependent kinematic structure—and available cursor and eye behavior, does motor-cortical population structure track task-defined route intention across behaviorally matched executions, or instead track execution-specific trajectory variation within the same intended route context?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the release contains sufficiently overlapping neural, hand, cursor, eye, and task-context observations, it may support comparison of route-intention associations across matched trajectory histories and execution-specific associations within intended-route contexts.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 (MC_Maze_Small, version 0.220113.0408) is a single-subject (rhesus macaque 'Jenkins') delayed center-out reaching task with obstructing barriers forming a maze, producing a mix of straight and curved reaches. Neural activity was recorded from electrode arrays in primary motor cortex (M1) and dorsal premotor cortex (PMd). Behavioral channels recorded are cursor position, hand position, and eye position; hand velocity was computed offline from hand position. The release is deliberately limited to 100 train and 100 test trials and is distributed as part of the Neural Latents Benchmark '21.
  - Limitation: Single subject, single session; no cross-animal or cross-session generalization is possible.
  - Limitation: This is dataset-scope documentation, not a scientific result; it establishes what surfaces exist, not any effect.
- **Unverified planning evidence:** The train file exposes 100 trials with a trials table containing: start_time, stop_time, trial_type, trial_version, maze_id, success (all True), target_on_time, go_cue_time, move_onset_time, rt, delay, num_targets, target_pos, num_barriers, barrier_pos, active_target, split. There are 9 unique maze_id values, each crossed with 3 trial_version values, giving 27 unique conditions. Trials-per-condition is small: 21 conditions have 4 trials, 4 have 3, and 2 have 2. The three versions per maze are structurally distinct: version 0 has 0 barriers and 1 target (straight reach), version 1 has 9 barriers and 1 target (curved reach), and version 2 has 9 barriers and 3 targets (curved reach with distractor targets). Overall 32 trials have 0 barriers and 68 have 9 barriers; 66 have 1 target and 34 have 3 targets.
  - Limitation: Only ~2-4 trials per condition, which severely limits any per-condition or repeated-execution estimation.
  - Limitation: Counts describe the train file only; the test file is inspected separately.
- **Unverified planning evidence:** The train units table has 142 sorted units with columns (heldout, spike_times, obs_intervals, electrodes). Using the documented NLB unit-ID region convention (leading digit 1 = PMd, leading digit 2 = M1), the leading-digit distribution is 72 units with leading 1 (PMd) and 70 with leading 2 (M1), so both regions are represented. The heldout flag partitions units into 107 held-in and 35 held-out; these held-out units are the NLB co-smoothing modeling target, not a behavioral hold-out. Per DATASET_NOTES.md, raw electrode indices for M1 units require a documented +96 electrode-row correction and must not be used alone to conclude the population is PMd-only. A combined M1+PMd population is available, with region stratification possible via the unit-ID convention.
  - Limitation: Region assignment relies on the documented unit-ID convention plus the M1 +96 electrode correction; any residual disagreement must remain visible rather than being resolved by assuming a region is absent.
  - Limitation: Single session; unit yield and quality are fixed and cannot be increased.
- 2 additional typed inspection statement(s) remain in the complete planning record.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

The key observation would be a held-out double contrast: whether population structure distinguishes task-defined route intentions among executions matched or explicitly modeled on full recorded trajectory history and other available behavior, and whether it distinguishes execution-specific trajectory variation within the same intended route. Cross-execution persistence tied to route intention would favor an abstract-context association; tracking within-context trajectory variation would favor behavior-specific residual structure; loss of both distinctions after rich trajectory-history adjustment would favor generic full-trajectory encoding.

**What possible outcomes would mean**

- Positive pattern: If route-context structure persists across behaviorally matched executions and exceeds within-context sensitivity to execution variation, it would support only a bounded association between population activity and task-defined route intention conditional on the measured behavioral set. It would not establish a curvature-specific neural mechanism or exclude unmeasured behavioral causes.
- Negative pattern: If the apparent route-context distinction is attenuated by full nonlinear trajectory-history and available behavioral adjustment, or residual structure primarily follows within-context execution variation, the result would favor generic full-trajectory encoding or behavior-specific structure over an abstract route-intention interpretation.
- Null or ambiguous pattern: If trajectory histories cannot be adequately matched or modeled, route intention is confounded with execution, or held-out contrasts are unstable, the evidence would not discriminate among full-trajectory encoding, behavior-specific residual structure, and intention-related association.

## Owner and independent review

### Question Owner

No safely resolved typed review statement was available for this view.

### Independent reviewer

No safely resolved typed review statement was available for this view.

A missing review is shown as unavailable rather than inferred from planner prose or the family status.

**Authority reminder:** these dispositions do not yield an accepted plan here.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
