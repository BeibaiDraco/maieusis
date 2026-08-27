# Stable versus task-specific geometry across motor contexts — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Asks whether population organization is preserved across trajectory contexts, with separate variants for within-region context stability and cross-region division of representational scope.

The scientific tension is:

Prior literature supports both preserved motor manifolds and task-specific dynamics. The described straight/curved task and PMd/M1 recordings motivate distinct tests of condition invariance and regional representational scope.

## Variant 1: Within-region test of trajectory-shape preservation, lawful transformation, or residual reorganization at matched computational and submovement states

### Why it matters

Separating trajectory-shape dependence from computational-epoch and correction-related organization would sharpen the stability-versus-task-specificity debate and clarify whether curved reaching changes population organization beyond established control-phase differences.

### Original and refined question

**Original Question Scientist proposal**

Is the population geometry used for straight reaches preserved, smoothly transformed, or reorganized for curved reaches within a cortical region?

**Post-novelty revised proposal**

Within a cortical region, is population geometry for straight versus curved reaches preserved, related by a reproducible low-complexity transformation, or reorganized when comparisons are restricted to matched task epochs, movement phases, kinematic states, and initial-versus-corrective submovement roles?

**Reviewed refined question**

Within one cortical region (PMd or M1 analyzed separately), is population geometry for straight versus curved reaches preserved (reliable state-to-state correspondence), related by a reproducible low-complexity transformation, or reorganized (reliable residual condition-specific structure), when compared only at matched task epochs, movement phases, kinematic states, and initial-versus-corrective submovement roles?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the release contains sufficiently comparable straight and curved reaches, task epochs, kinematic states, and identifiable initial or corrective segments, it may support a later-planned within-region comparison; these properties require verification.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 (MC_Maze_Small) contains sorted-unit spiking and behavior from one rhesus macaque (Jenkins), one session dated 2009-09-28, performing a delayed center-out reaching task with obstructing maze barriers that produces a variety of straight and curved reaches. Neural activity was recorded from electrode arrays in primary motor cortex (M1) and dorsal premotor cortex (PMd). Cursor, hand, and eye position were recorded and hand velocity was computed offline. The release is limited to 100 train and 100 test trials. This establishes that the family's straight-versus-curved trajectory contrast and its PMd/M1 regional contrast are both directly grounded in the documented experimental design.
  - Limitation: Single subject and single session, so any conclusion is descriptive of this animal and cannot be generalized across subjects without new data.
  - Limitation: Only 100 train and 100 test trials exist; the test file is a held-out benchmark split with no behavior, so the analyzable behavior-linked surface is the 100-trial train file.
  - Limitation: Documentation establishes design intent, not per-condition trial coverage or unit-quality equivalence, which are verified in separate evidence records.
- **Unverified planning evidence:** The train file has 100 trials, all success == True, with an internal split of 75 train and 25 val. num_barriers takes two values: 0 on 32 trials (barrier-free straight center-out reaches) and 9 on 68 trials (maze-barrier trials producing curved reaches), giving a documented, source-backed straight-versus-curved partition; maze_id and trial_type further index distinct maze configurations and target directions, and num_targets is 1 (66 trials) or 3 (34 trials, with distractor targets). Each trial carries a full delayed-reach event sequence: target_on_time, go_cue_time (after a delay period, delay range 14 to 999 ms), move_onset_time, plus start/stop and reaction time (rt range 241 to 758 ms). This timing supports segmentation into preparatory/delay and execution epochs and alignment to movement onset, so straight and curved conditions can be compared at matched computational epochs and movement phases.
  - Limitation: Condition counts are small (32 straight vs 68 curved out of 100); stratifying further by target direction, region, and matched kinematic state will thin cells and bounds statistical resolution.
  - Limitation: The straight/curved partition uses num_barriers as the primary label; a trajectory-curvature check computed from hand position should confirm the label per trial rather than assuming barrier count fully determines path shape.
  - Limitation: Event-time columns define epochs but do not by themselves guarantee clean preparation/execution separation; per-trial phase boundaries must be derived and validated during analysis.
- **Unverified planning evidence:** The train file has 142 sorted units. Applying the documented leading-digit convention to /units/id yields 72 PMd units and 70 M1 units (unit ids range 1011 to 2951), exactly matching the DATASET_NOTES.md verified train counts. The electrodes table has 192 rows split 96 M1 and 96 PMd by group_name, with a location column of only 'M1' and 'PMd'. Stored /units/electrodes indices fall within 0 to 94, consistent with the documented caveat that M1 units require a +96 electrode-row correction; region assignment via the unit-ID convention is therefore reliable and independent of the raw electrode index. Both regions are represented with near-balanced unit counts, enabling identical, region-stratified population estimation.
  - Limitation: The +96 electrode-row correction must be applied before joining units to raw electrode metadata; region identity here rests on the unit-ID convention, which is documented and count-verified but is a convention rather than a per-unit anatomical re-check.
  - Limitation: Near-balanced counts (72 vs 70) still require explicit unit-count matching or subsampling before any cross-region comparison to avoid sampling-driven differences.
  - Limitation: Metadata confirms region membership only, not per-region signal quality or condition coverage.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Single macaque (Jenkins), single session (2009-09-28), delayed center-out maze reaching. Neural population is one region at a time: PMd (72 units) or M1 (70 units). Behavioral scope is the 100-trial train file with 1000 Hz 2D hand kinematics. No cross-region comparison is made in this variant.
- Unit of observation: A single reach trial within one region, represented as a time-resolved population neural state trajectory aligned to task events and paired with its hand kinematics.
- Unit of inference: The trial, treated as the independent sampling unit; condition-level geometry is estimated by resampling over trials with within-condition reliability benchmarks.
- Hierarchy and dependence: Trials are nested within maze/target conditions within one session; dependence is handled by trial-level cross-validation and condition-stratified resampling, keeping straight and curved comparisons within matched target directions where possible.
- Validation: Prespecify all matching tolerances, epoch/submovement rules, and the transformation family; use trial-level cross-validation and within-condition split-half reliability as the benchmark against which correspondence and residual structure are scored; run a synthetic method-recovery probe where a known transformation is imposed to confirm the pipeline distinguishes preservation, transformation, and reorganization.
- Split strategy: Trial-level cross-validation within region; reliability benchmarks from within-condition split-half; no held-out benchmark test file is used because it lacks behavior.
- Claim ceiling: descriptive

**Analysis strategy**

1. Confirm straight-versus-curved labels per trial by computing hand-path curvature from hand_pos, reconciling with num_barriers rather than assuming the barrier label.
2. Define delay/preparation and execution epochs from target_on/go_cue/move_onset and segment initial-versus-corrective submovements from the hand-speed profile using a prespecified rule.
3. Match straight and curved trials on epoch, movement phase, endpoint-related target position, speed, temporal progression, and submovement role using prespecified tolerances.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Shuffle straight/curved labels within matched cells; correspondence and residual-structure estimates should collapse to the reliability floor.
- Positive controls: Target-direction structure, which is known to be encoded, should be recoverable as reliable geometry within condition.
- Alternative explanations: Apparent condition-specific geometry driven by unequal occupancy of preparation vs execution states rather than trajectory shape.; Differences in correction demand or proportion of initial vs corrective submovements.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject and single session; descriptive of this animal only.
- Small matched-cell counts bound the resolution of any residual-structure test; provisional planning evidence is not a scientific result.
- Conclusions about preservation vs transformation vs reorganization are conditional on the prespecified matching and embedding choices and their sensitivity analyses.

**Why the plan serves the question**

The plan isolates trajectory shape within a single region at matched epochs, phases, kinematic states, and submovement roles, and preserves the three-way outcome distinction (preservation, low-complexity transformation, reorganization) without introducing any cross-region comparison, exactly matching the variant's protected intent.

**Before any later execution**

- Unresolved planning decisions: Final matching tolerances, submovement rule, and transformation family (with sensitivity analyses).
- Required future skills: A population-geometry alignment executor skill that estimates within-region condition-resolved neural state geometry and scores preservation, low-complexity transformation, and residual reorganization against within-condition reliability.; A submovement-segmentation and epoch/kinematic-matching skill operating on 1000 Hz hand kinematics with prespecified rules.

### Scientific stakes

**Discriminating observation**

At comparable task epochs and movement phases, compare straight and curved reaches at matched endpoint-related variables, speed, temporal progression, kinematic state, and initial-versus-corrective role. Preserved geometry means reliable state-to-state correspondence without a condition-dependent remapping; smooth transformation means a reproducible low-complexity correspondence across matched states; reorganization means reliable residual condition-specific structure only after phase-related, correction-related, and measured kinematic alternatives are weakened.

**What possible outcomes would mean**

- Positive pattern: A reproducible low-complexity transformation across matched states would support a flexible shared population scaffold rather than either strict invariance or a difference attributable solely to control phase or corrective submovements.
- Negative pattern: Reliable residual separation without a reproducible correspondence, persisting after phase-related, correction-related, and matched-kinematic alternatives are weakened, would support stronger trajectory-shape-specific organization within the region.
- Null or ambiguous pattern: If differences disappear after matching, a common organization or phase- and correction-based explanation would remain favored over trajectory-specific reorganization; if correspondence is unreliable or estimator-dependent, the three accounts would remain unresolved.

## Variant 2: Cross-region test of normalized trajectory-geometry generalization under held-constant task identity

### Why it matters

A geometry-specific, sensitivity-controlled regional comparison can distinguish trajectory-type scope from generic task dependence and clarify whether PMd and M1 have different predictive roles or share a distributed representational scope.

### Original and refined question

**Original Question Scientist proposal**

Do PMd and M1 differ in whether their population organization spans both straight and curved trajectory contexts or is specialized by trajectory type?

**Post-novelty revised proposal**

When task identity is held constant and trajectory kinematics, movement phase, target or obstacle structure, speed, and task demands are matched or explicitly modeled, do PMd and M1 differ in normalized cross-trajectory generalization between straight and curved movements?

**Reviewed refined question**

With the reaching task held constant and trajectory kinematics, movement phase, target/obstacle structure, speed, task demands, and shared temporal structure matched or modeled, do PMd and M1 differ in a common, reliability-normalized cross-trajectory generalization (transfer of population organization between straight and curved movements) estimated identically in both regions?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the described PMd and M1 recordings contain sufficiently comparable straight and curved contexts, they may support estimation of the same within-context and cross-context generalization quantities in each region after metadata and coverage checks.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 (MC_Maze_Small) contains sorted-unit spiking and behavior from one rhesus macaque (Jenkins), one session dated 2009-09-28, performing a delayed center-out reaching task with obstructing maze barriers that produces a variety of straight and curved reaches. Neural activity was recorded from electrode arrays in primary motor cortex (M1) and dorsal premotor cortex (PMd). Cursor, hand, and eye position were recorded and hand velocity was computed offline. The release is limited to 100 train and 100 test trials. This establishes that the family's straight-versus-curved trajectory contrast and its PMd/M1 regional contrast are both directly grounded in the documented experimental design.
  - Limitation: Single subject and single session, so any conclusion is descriptive of this animal and cannot be generalized across subjects without new data.
  - Limitation: Only 100 train and 100 test trials exist; the test file is a held-out benchmark split with no behavior, so the analyzable behavior-linked surface is the 100-trial train file.
  - Limitation: Documentation establishes design intent, not per-condition trial coverage or unit-quality equivalence, which are verified in separate evidence records.
- **Unverified planning evidence:** The train file has 100 trials, all success == True, with an internal split of 75 train and 25 val. num_barriers takes two values: 0 on 32 trials (barrier-free straight center-out reaches) and 9 on 68 trials (maze-barrier trials producing curved reaches), giving a documented, source-backed straight-versus-curved partition; maze_id and trial_type further index distinct maze configurations and target directions, and num_targets is 1 (66 trials) or 3 (34 trials, with distractor targets). Each trial carries a full delayed-reach event sequence: target_on_time, go_cue_time (after a delay period, delay range 14 to 999 ms), move_onset_time, plus start/stop and reaction time (rt range 241 to 758 ms). This timing supports segmentation into preparatory/delay and execution epochs and alignment to movement onset, so straight and curved conditions can be compared at matched computational epochs and movement phases.
  - Limitation: Condition counts are small (32 straight vs 68 curved out of 100); stratifying further by target direction, region, and matched kinematic state will thin cells and bounds statistical resolution.
  - Limitation: The straight/curved partition uses num_barriers as the primary label; a trajectory-curvature check computed from hand position should confirm the label per trial rather than assuming barrier count fully determines path shape.
  - Limitation: Event-time columns define epochs but do not by themselves guarantee clean preparation/execution separation; per-trial phase boundaries must be derived and validated during analysis.
- **Unverified planning evidence:** The train file has 142 sorted units. Applying the documented leading-digit convention to /units/id yields 72 PMd units and 70 M1 units (unit ids range 1011 to 2951), exactly matching the DATASET_NOTES.md verified train counts. The electrodes table has 192 rows split 96 M1 and 96 PMd by group_name, with a location column of only 'M1' and 'PMd'. Stored /units/electrodes indices fall within 0 to 94, consistent with the documented caveat that M1 units require a +96 electrode-row correction; region assignment via the unit-ID convention is therefore reliable and independent of the raw electrode index. Both regions are represented with near-balanced unit counts, enabling identical, region-stratified population estimation.
  - Limitation: The +96 electrode-row correction must be applied before joining units to raw electrode metadata; region identity here rests on the unit-ID convention, which is documented and count-verified but is a convention rather than a per-unit anatomical re-check.
  - Limitation: Near-balanced counts (72 vs 70) still require explicit unit-count matching or subsampling before any cross-region comparison to avoid sampling-driven differences.
  - Limitation: Metadata confirms region membership only, not per-region signal quality or condition coverage.
- 2 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Single macaque (Jenkins), single session; both regions analyzed together in a matched contrast: PMd (72 units) vs M1 (70 units), recorded simultaneously across the identical straight and curved conditions in the 100-trial train file.
- Unit of observation: A trial's region-specific population state (PMd or M1) under a straight or curved condition, with paired kinematics.
- Unit of inference: The trial as the independent sampling unit; the regional contrast is a difference of reliability-normalized transfer quantities estimated per region with resampling-based uncertainty.
- Hierarchy and dependence: Trials nested in conditions in one session; the two regions are paired within the same trials, so the PMd-minus-M1 transfer difference is estimated on shared trials with trial-level resampling and unit-count matching.
- Validation: Prespecify the reliability normalizer and transfer metric; equalize unit counts across regions; run a synthetic method-recovery probe imposing known equal or unequal regional transfer to confirm the estimator neither invents nor hides a regional difference and is insensitive to raw firing-rate scale/detectability.
- Split strategy: Trial-level cross-validation with within-condition split-half reliability per region; region contrast computed on shared trials; no held-out test file (it lacks behavior and full units).
- Claim ceiling: associational

**Analysis strategy**

1. Assign units to PMd/M1 by the documented unit-ID convention (with M1 +96 electrode correction for any metadata join) and match unit counts by subsampling to equalize N across regions.
2. Define within-context population organization per region and per condition, and define cross-trajectory transfer as how well straight-condition organization predicts/aligns to curved-condition organization, normalized to each region's within-context reliability so scope does not equal raw signal strength or decoding accuracy.
3. Match or model trajectory kinematics, movement phase, target/obstacle structure, speed, task demands, and shared temporal structure before interpreting any regional difference as geometry-specific.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: A scientifically irrelevant re-labeling (for example arbitrary unit split within a region) should yield zero normalized-transfer difference.
- Positive controls: Within-condition organization (for example target-direction structure) should be recoverable in both regions above the reliability floor.
- Alternative explanations: Apparent regional difference from unequal detectability or signal strength (addressed by reliability normalization and unit matching).; Shared temporal movement structure or residual kinematic/task-demand differences rather than trajectory-type scope.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject and single session; a PMd/M1 difference is descriptive of this animal and is associational, not causal localization.
- Wide uncertainty from about 70 units per region and small trial counts; requires reported confidence intervals and subsampling sensitivity.
- Regional specialization is interpretable only after detectability, temporal-structure, and generic task-dependence controls are executed as planned; planning evidence is not a result.

**Why the plan serves the question**

The plan defines regional scope as identical, reliability-normalized cross-trajectory transfer estimated per region within one held-constant task, and gates any regional claim on detectability, temporal-structure, and task-dependence controls, preserving the variant's distinction from the within-region sibling and from task-subspace prevalence.

**Before any later execution**

- Unresolved planning decisions: Final transfer metric, reliability normalizer, and unit-matching scheme (with sensitivity analyses).
- Required future skills: A reliability-normalized cross-region transfer executor skill that estimates identical cross-trajectory generalization per region, normalizes to within-context reliability, equalizes unit counts, and returns a PMd-minus-M1 difference with resampling uncertainty.; A confound-control skill matching/modeling kinematics, phase, speed, target/obstacle structure, and shared temporal structure across straight/curved conditions.

### Scientific stakes

**Discriminating observation**

Representational scope is the cross-context preservation or transfer of population organization, normalized to within-context reliability and estimated identically for PMd and M1 so that raw signal strength, decoding accuracy, or detectability does not define scope. Broader PMd scope with M1 specialization requires PMd cross-context transfer to approach its within-context organization while M1 transfer falls selectively below its own within-context benchmark; a common distributed scope requires comparable normalized transfer in both regions. Either regional pattern is geometry-specific only if it remains after matching or modeling trajectory kinematics, movement phase, target or obstacle structure, speed, task demands, shared temporal structure, and task-dependent versus task-independent activity.

**What possible outcomes would mean**

- Positive pattern: A reproducible PMd–M1 difference in normalized cross-trajectory generalization that survives the stated controls would support distinct regional predictive roles specifically for trajectory-geometry scope, without treating detectability or generic task dependence as localization evidence.
- Negative pattern: Comparable normalized cross-trajectory generalization in PMd and M1 would favor a common distributed trajectory-geometry scope and constrain accounts assigning broader geometric generalization to only one region, while remaining compatible with the cited prior's task-subspace dissociation.
- Null or ambiguous pattern: If regional transfer estimates are unreliable, control-dependent, or inseparable from temporal structure, detectability, or task-dependent versus task-independent activity, the data would not distinguish geometry-specific regional scope from generic task dependence or measurement differences.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct protected scientific intents and are supported by the supplied branch-scoped evidence. The within-region plan retains the preservation/transformation/reorganization distinction under matched behavioral states, while the regional plan defines scope as reliability-normalized cross-trajectory transfer rather than generic task dependence. Remaining choices are appropriate pre-execution locks, not planning blockers.

Retained changes and locks:

- **Pre execution lock:** Prespecify matching tolerances, epoch and submovement segmentation, and the transformation family for the within-region analysis before execution, with the stated sensitivity analyses.
- **Pre execution lock:** Prespecify the cross-trajectory transfer metric, within-region reliability normalizer, and unit-matching scheme for the PMd-versus-M1 analysis before execution, with the stated sensitivity analyses.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both sibling variants preserve the family's protected scientific intent: the context-invariance plan tests within-region preservation/transformation/reorganization of straight-versus-curved geometry at matched epochs, phases, kinematic states, and submovement roles, while the regional-scope plan tests a reliability-normalized cross-trajectory transfer difference between PMd and M1 under held-constant task conditions. These remain distinct claims per the family's forbidden semantic merges, with no cross-contamination of estimands or data slices. Both plans are concretely grounded in verified dataset evidence (unit counts, trial partition by num_barriers, 1000 Hz kinematics, shared event timing), specify appropriate claim ceilings (descriptive, associational) with honest single-subject/session limits, and include alternative-explanation lists, positive/negative controls, and synthetic method-recovery probes that address the plausible confounds (state occupancy, submovement mix, detectability, temporal structure, unit-count imbalance). The two Owner-classified required changes (prespecifying matching tolerances/transformation family, and prespecifying the transfer metric/reliability normalizer/unit-matching scheme) are bounded implementation choices that do not touch the scientific logic or validity of the estimands; they are correctly classified as pre-execution locks rather than blockers. No scientific blocker or hard-boundary issue is present in either variant at this planning stage.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
