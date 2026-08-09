# Degeneracy and semantic equivalence in motor population codes — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Scientific rejection terminal**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **No**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Investigates whether structurally different population states can carry similar movement meaning and whether such degeneracy reflects robustness or hidden task distinctions.

The scientific tension is:

Different neural activity patterns may be semantically equivalent for movement, but apparent equivalence could instead result from coarse behavioral measurement or unobserved distinctions in task context.

## How to read this terminal

The scientific planning/review process closed this family without an accepted plan. Rejection is a scientific terminal, not evidence that the proposed phenomenon is false.

**Recorded public status note**

automated_reject

## Variant 1: Execution-specific hidden trajectory-history branch

### Why it matters

This question tests whether semantic equivalence based on an immediate motor readout extends across trajectory histories, while separating such history dependence from established population sensitivity to trajectory planning and general task context.

### Original and refined question

**Original Question Scientist proposal**

Do population states that appear equivalent for immediate movement preserve distinct information about straight versus curved reach context?

**Post-novelty revised proposal**

During execution of a common reach segment, do primary motor cortex population states matched for immediate movement prediction retain information about the preceding route across held-out route instances, when current kinematics, movement phase, target location, environmental conditions, and task demands are held constant?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If paired M1 population and movement measurements contain repeated common reach segments reached through different preceding routes under otherwise comparable task conditions, they may support a proposal-stage test of whether execution states preserve route history beyond immediate movement prediction.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** M1 units are identifiable: the documented convention assigns leading unit-ID digit 1 to PMd and 2 to M1, with a required +96 electrode-row correction for M1. The training units table has 142 sorted units, of which 70 have leading digit 2 (M1) and 72 leading digit 1 (PMd); 35 units are marked heldout. An M1-restricted population is therefore constructible, so the variant's requirement of a primary-motor-cortex population is met at the unit-labeling level.
  - Limitation: Region labeling relies on the documented convention plus the +96 correction; it certifies unit provenance, not trial-level coverage or statistical power for the specific contrast.
  - Limitation: M1 unit count (70; ~55 in the test held-in set) is modest for population-state matching.
- **Unverified planning evidence:** The training file contains 100 successful trials spanning 9 maze_id values and 27 unique (maze_id, trial_version) conditions, i.e. ~4 trials per condition (21 conditions with 4, 4 with 3, 2 with 2). There are 9 distinct active target locations; each target is reached by at most 3 distinct (maze, version) routes, and the maximum trial count in any single (target x route-type) cell is 8 (median 4.5). The published release is limited to 100 train and 100 test trials total.
  - Limitation: Planning-only metadata inspection; no neural or behavioral analysis was run.
  - Limitation: Test-split neural data is the NLB held-out benchmark set and was not inspected; even counting it (~200 trials across 27 conditions) does not materially change per-route repeat counts.
- **Unverified planning evidence:** Trials encode start/stop, trial_type, trial_version, maze_id, success, target_on/go_cue/move_onset times, rt, delay, num_targets (1 or 3), target_pos, num_barriers (0-9), barrier_pos, and active_target. The center-out maze task yields both straight (no-barrier) and curved (barrier) reaches: all 9 targets are reached by both a no-barrier and a barrier route, so distinct 'preceding routes' toward shared endpoints are present in principle. Continuous behavior is available as cursor_pos, eye_pos, hand_pos (meters), and hand_vel, enabling instantaneous-kinematics matching. Reach durations (move_onset to stop) are ~0.98-1.63 s (median 1.14 s).
  - Limitation: Planning-only; trajectory overlap of a genuine common reach segment with matched instantaneous kinematics across routes was not analyzed and cannot be assumed.
  - Limitation: Straight vs curved reaches to a shared target share the center start and target endpoint but diverge in path; a matched common segment would occupy only a narrow convergence window.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

Within the execution epoch of a common reach segment in an M1 population, states matched for immediate movement prediction remain separable by preceding-route identity on held-out observations and route instances that were not used to define state equivalence, select the execution epoch, or establish the route boundary; the separation must persist when instantaneous kinematics, movement phase, target location, speed, curvature, environmental conditions, and task-flexibility demands are comparable.

**What possible outcomes would mean**

- Positive pattern: A positive result would support the interpretation that apparently movement-equivalent M1 execution states retain trajectory-history content, narrowing the conditions under which those states can be treated as semantically synonymous.
- Negative pattern: A negative result under adequate matching and held-out evaluation would favor semantic equivalence of the measured M1 execution states across preceding routes and would weaken a trajectory-history account distinct from planning or general task context.
- Null or ambiguous pattern: An inconclusive result would leave the semantic boundary unresolved if route conditions lack sufficient behavioral overlap, held-out generalization is unstable, or measured variables cannot separate trajectory history from planning, drift, or broader task demands.

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
