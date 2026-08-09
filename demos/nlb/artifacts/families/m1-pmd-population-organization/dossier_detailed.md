# Shared and selective population organization across M1 and PMd — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Asks whether M1 and PMd express broadly shared movement geometry or complementary, selectively organized representations during delayed reaching.

The scientific tension is:

Regional activity may reflect a common motor representation expressed across both areas or complementary organizations emphasizing different aspects of preparation and movement; regional decodability alone cannot decide between them.

## Variant 1: Shared residual trajectory-geometry branch

### Why it matters

This distinction would determine whether different regional manifold shapes necessarily imply different reach content or can instead be alternative embeddings of the same trajectory-specific relational organization.

### Original and refined question

**Original Question Scientist proposal**

Do M1 and PMd express a shared population geometry for reach trajectories despite possible differences in local activity patterns?

**Post-novelty revised proposal**

During reach execution, do M1 and PMd preserve the same residual relational geometry among reach paths that differ in curvature or path while target direction, speed profile, task context, and time relative to movement onset are matched or accounted for, even if the regions have different raw manifold curvature and local activity patterns?

**Reviewed refined question**

During reach execution in this Jenkins MC_Maze_Small session, are the residual relations among executed-trajectory conditions (matched-target curved vs straight reaches) preserved across M1 and PMd under a prespecified orthogonal cross-region alignment, after direction, target, speed profile, generic temporal evolution, movement-onset locking, and task context are matched or accounted for, even if the two regions have different raw manifold curvature?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the delayed-reaching observations contain sufficiently matched M1 and PMd coverage of executed reaches that vary in path or curvature, they may support comparison of cross-validated condition-distance or distance-rank structure during the movement-onset-to-endpoint epoch after accounting for direction, target, speed profile, time, and task context.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- No safely resolved, typed inspection statement was available for this view.

### Plan at a glance

- Population and scope: One rhesus macaque (Jenkins), one recording session; M1 (70 units) and PMd (72 units) from the train file. Scope and claims are limited to this subject/session (Owner ruling A); no cross-subject/session or causal claim.
- Unit of observation: A single trial's population activity in one region, epoched from move_onset to reach endpoint and summarized as time-binned firing-rate vectors.
- Unit of inference: Trajectory condition (matched-target curved/straight maze version) within this session; cross-validation and held-out condition sets provide the inferential replication units. No generalization beyond this session.
- Hierarchy and dependence: Trials are nested within trajectory conditions; conditions share targets across curved/straight versions. Cross-validation folds are built over trials and, for the alignment test, over held-out conditions, so alignment is never learned on the conditions used to score preservation.
- Validation: Leave-conditions-out cross-validation for the alignment; trial-level cross-validation for distance estimation (crossnobis) to remove positive bias; within-region split-half reliability to set noise ceilings; method-recovery on synthetic data with known shared vs mismatched geometry to confirm the pipeline detects each when present.
- Split strategy: Held-out condition folds for alignment learning/scoring plus trial-level splits for cross-validated distances; alignment parameters never touch the scored held-out conditions (leakage-safe).
- Claim ceiling: associational

**Analysis strategy**

1. Assign each unit to M1 or PMd via the unit-ID leading-digit rule and reconcile with the electrodes table (M1 +96 correction); keep any disagreement flagged.
2. Define trajectory conditions from matched-target maze structure so that path/curvature varies (barrier vs no-barrier versions) while target endpoint, reach direction, and task context are matched or covaried; verify curvature separation behaviorally before neural analysis.
3. Epoch the execution window (move_onset to endpoint), time-normalize to movement onset, and build per-region, per-condition cross-validated population firing-rate representations.
4. 3 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Shuffle trajectory-condition labels before building RDMs (should abolish cross-region preservation).; Align on a scientifically irrelevant partition (e.g. trial index parity) as a false-alignment control.
- Positive controls: Within-region cross-validated RDM reproducibility across trial splits (must recover).; Synthetic populations sharing residual geometry with different raw curvature (alignment must recover preservation).
- Alternative explanations: Cross-region correspondence produced by shared direction/target/speed/elapsed-time/movement-onset/task-epoch structure rather than trajectory-specific relations (addressed by residualization).; A flexible alignment manufacturing similarity (addressed by restricting to an orthogonal alignment and reporting shuffle/false-alignment baselines).; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject, single session; no cross-subject/session or causal generalization (Owner ruling A).
- Sparse per-condition sampling means an underpowered non-detection must NOT be read as either shared geometry or a genuine mismatch; power must be demonstrated before any mismatch interpretation.
- An inappropriate alignment can yield a false mismatch; alignment choice is prespecified and its sensitivity reported.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

It tests held-out preservation of residual trajectory-condition relations across M1 and PMd under a constrained orthogonal alignment while permitting different raw manifold curvature, exactly the variant's discriminating observation, and it guards each forbidden semantic change (generic-structure confound, alignment over-fitting, sampling/reliability artifacts, alignment mis-specification).

**Before any later execution**

- Unresolved planning decisions: Final trajectory-condition grouping rule (which matched-target maze/version clusters) fixed from behavior before execution.; Minimum trials-per-condition threshold and pooling rule for reliability.

### Scientific stakes

**Discriminating observation**

For trajectory conditions defined primarily by executed path or curvature, compare cross-validated condition-distance matrices, including their rank structure, across M1 and PMd during the movement-onset-to-endpoint epoch using a prespecified orthogonal alignment learned without the held-out conditions. Shared geometry requires held-out preservation of residual trajectory-condition distances after direction, target, speed profile, generic temporal evolution, movement-onset locking, and task context are matched or accounted for. The criterion may be met despite different raw manifold curvature or dimensional embeddings; correspondence that disappears under these controls is not evidence for the shared reach code.

**What possible outcomes would mean**

- Positive pattern: Reliable held-out preservation of residual path- or curvature-condition relations would support a shared trajectory-specific relational code across M1 and PMd that can coexist with differently curved or dimensionally embedded regional manifolds, thereby distinguishing the claim from evidence that an integrated system can nevertheless have different raw regional manifold shapes.
- Negative pattern: A reliable residual mismatch under the same constrained alignment, supported across adequately represented trajectory conditions and not attributable to identified reliability or measurement differences, would favor regional specialization in executed-trajectory relations rather than merely different embeddings of a shared code.
- Null or ambiguous pattern: If residual correspondence is indistinguishable from its constrained reference but sensitivity, condition coverage, regional reliability, measurement comparability, or alignment adequacy remains insufficient, the shared-code and specialization accounts would remain unresolved; the result would not by itself overturn the cited regional manifold-shape difference.

## Variant 2: Information-specific regional-crossover branch

### Why it matters

An information-specific crossover would refine regional specialization from a one-sided PMd preparatory effect to a relational claim about complementary PMd and M1 population organization. Requiring matched information and explicit controls is necessary because regional decodability or geometric separation alone cannot establish different representational roles.

### Original and refined question

**Original Question Scientist proposal**

Are M1 and PMd population geometries selectively organized around complementary preparatory and movement-related information?

**Post-novelty revised proposal**

For fully specified delayed reaches, do PMd and M1 exhibit a regional crossover in population geometry—relatively stronger PMd organization by instructed future reach direction during preparation, but relatively stronger M1 organization by instantaneous hand-velocity direction during execution—after information matching and accounting for measured kinematics, overall activity magnitude, and arm/hemisphere organization?

**Reviewed refined question**

In this Jenkins MC_Maze_Small session, do PMd and M1 show a two-sided crossover in population geometry - relatively stronger PMd organization by instructed future reach direction during the delay and relatively stronger M1 organization by instantaneous hand-velocity direction during movement - in information-matched directional comparisons after accounting for measured kinematics, overall activity magnitude, and target certainty?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If verified M1 and PMd recordings contain comparable fully instructed delayed reaches, measured hand kinematics, and interpretable arm and hemisphere metadata, their common task structure may support comparison of regional geometry for future reach direction during the delay and instantaneous hand-velocity direction during movement.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- No safely resolved, typed inspection statement was available for this view.

### Plan at a glance

- Population and scope: One rhesus macaque (Jenkins), one session; M1 (70 units) and PMd (72 units) from the train file. Single arm and single hemisphere, so arm/hemisphere and bilateral-component composition are constant. Claims limited to this subject/session (Owner ruling A); associational only.
- Unit of observation: A single trial's region population activity in a specified epoch: delay (target_on to go_cue) labeled by instructed future reach direction, or execution (move_onset to endpoint) labeled by instantaneous hand-velocity direction.
- Unit of inference: Directional condition within this session, with cross-validation folds over trials; the estimand is the region x information-type interaction. No generalization beyond this session.
- Hierarchy and dependence: Trials nested within directional conditions; the same trials contribute a delay and an execution observation, so the crossover interaction is evaluated with trial-respecting cross-validation and matched folds across the two contrasts.
- Validation: Trial-level cross-validation with matched folds across contrasts; information matching verified by equalized class counts and a discriminability check; method-recovery on synthetic populations with a known crossover and with a shared-code null to confirm the interaction is detected only when present.
- Split strategy: Stratified trial folds balanced across direction classes and epochs; kinematic and certainty controls fit within-fold to avoid leakage.
- Claim ceiling: associational

**Analysis strategy**

1. Assign units to M1/PMd (unit-ID rule + M1 +96 reconciliation).
2. Define instructed future reach direction from the active target during the delay epoch and instantaneous hand-velocity direction from hand_vel during execution; bin directions into a common, prespecified set.
3. Quantify per-region directional geometry strength in each epoch with a cross-validated, magnitude-normalized measure (e.g. cross-validated directional decodability or variance-explained-by-direction) so that overall activity magnitude does not drive the estimate.
4. 3 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Shuffle direction labels within epoch (interaction should vanish).; Substitute a scientifically irrelevant label (e.g. trial parity) for direction (no crossover expected).
- Positive controls: Recover known single-region directional tuning in its expected epoch as a pipeline sanity check.; Synthetic crossover populations (PMd-prep/M1-exec) must yield the signed interaction.
- Alternative explanations: Shared directional code with apparent crossover from magnitude/timing/reliability/sampling differences (addressed by magnitude normalization and information matching).; PMd selectivity reflecting target uncertainty or conditional upcoming-target distribution rather than instructed direction (addressed by holding certainty constant / separating single- vs multi-target trials).; plus 3 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject, single session; no cross-subject/session or causal claim (Owner ruling A).
- Limited directions and trials cap power; a null or one-sided result must NOT be read as absence of the crossover.
- Target-certainty control has limited power due to few multi-target trials.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

It requires the prespecified, information-matched, two-sided PMd-preparation / M1-execution crossover for instructed future direction versus instantaneous velocity direction and controls each forbidden semantic change (magnitude/timing, uncertainty vs instructed direction, kinematic sensitivity, arm/hemisphere, unmatched information), keeping it distinct from the sibling shared-geometry test.

**Before any later execution**

- Unresolved planning decisions: Final direction-bin count and information-matching target fixed from behavior before execution.; Kinematic feature set used as the control regressors, prespecified before execution.

### Scientific stakes

**Discriminating observation**

The required signature is jointly stronger PMd than M1 geometry for instructed future reach direction during the delay and stronger M1 than PMd geometry for instantaneous hand-velocity direction during movement. Both directions of this crossover must persist in information-matched directional comparisons after accounting for measured kinematics and overall activity magnitude. The interpretation also requires target certainty and conditional upcoming-target distributions to be held constant or otherwise separated, and requires the pattern not to be attributable to arm identity, hemisphere, or dedicated-versus-distributed bilateral components.

**What possible outcomes would mean**

- Positive pattern: A robust two-sided crossover satisfying the information-matching and control requirements would support complementary population-level emphases: PMd organization around a specified future reach and M1 organization around ongoing movement velocity. It would go beyond the cited one-sided PMd preparatory effects without establishing a causal regional mechanism.
- Negative pattern: If reliable, comparable observations instead show shared geometry, only a PMd preparatory advantage, only magnitude-based regional differences, or loss of the crossover after the stated controls, the specific complementary-specialization claim would be weakened and the result would favor shared-code or confound-based explanations.
- Null or ambiguous pattern: If neither regional relation can be estimated reliably, or if information matching and arm/hemisphere comparability cannot be established, the evidence would remain insufficient to distinguish complementary specialization from shared organization; absence of a crossover would not by itself establish equivalence.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants retain their distinct protected contrasts and are supported as single-subject, single-session associational analyses. The plan uses the behavior-linked train data, appropriate epoch/condition structure, leakage-aware cross-validation, and explicit limits on null interpretation. Remaining choices are pre-execution operational locks, not scientific blockers.

Retained changes and locks:

- **Pre execution lock:** For v1, prespecify from behavioral metadata alone the matched-target maze/version grouping, curvature-separation criterion, and minimum-trial exclusion or pooling rule; apply it without reference to neural outcomes.
- **Pre execution lock:** For v2, prespecify from behavioral metadata alone the common direction-bin rule, class/trial-count and discriminability information-matching rule, and kinematic control feature set.
- **Pre execution lock:** Before execution, fix a deterministic inclusion, exclusion, or sensitivity-analysis rule for any disagreement between unit-ID-based and electrode-table-based regional assignment, and report affected units.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants operationalize distinct, protected contrasts (residual relational-geometry preservation under a constrained orthogonal alignment for v1; a signed, two-sided preparatory/execution crossover for v2) using real, cited dataset structure (DANDI:000140 MC_Maze_Small, single subject/session, region-labeled units, trials table, 1 ms kinematics). Claims are capped at associational, single-subject/session scope is explicit, and each plan includes residualization/information-matching, negative and positive controls, and synthetic method-recovery checks that guard against the specific confounds each theoretical tension raises. Alternative explanations are enumerated with concrete analytic countermeasures, and sparse per-condition/direction sampling is disclosed with explicit prohibitions on reading an underpowered null as evidence either way. The two variants remain cleanly separated on the family's allowed axes (target_contrast, theoretical_tension) with no merged estimands. The three Owner-identified issues (trajectory/direction-bin prespecification, region-assignment disagreement handling) are bounded, reproducibility-oriented choices that do not touch the protected questions or claim ceilings, so pre_execution_lock is the correct classification for all three; none rises to a scientific blocker or hard-boundary concern at this planning stage.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
