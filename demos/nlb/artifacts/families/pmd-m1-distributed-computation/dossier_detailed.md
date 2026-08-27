# Localized versus distributed organization of reach planning and execution — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Examines whether PMd/M1 distinctions are best understood through trajectory-demand sensitivity or through temporal transformation from preparation to execution.

The scientific tension is:

PMd and M1 may make distinguishable contributions to reaching, but observed regional differences could reflect distributed computation, temporal staging, trajectory complexity, or measurement sensitivity rather than strict localization.

## Variant 1: Spatial-scope test of trajectory-complexity structure

### Why it matters

The question tests spatial extent while explicitly avoiding the inference that regional detectability proves local computation.

### Original and refined question

**Original Question Scientist proposal**

Is population structure associated with curved-path demand concentrated in PMd, concentrated in M1, or distributed across both regions?

**Reviewed refined question**

Within a single-subject delayed reaching session, is curved-path-specific population structure (population variance uniquely attributable to trajectory curvature, after removing duration and other movement/target/distractor confounds) concentrated in PMd, concentrated in M1, or distributed comparably across both regions, judged on a reliability-standardized PMd-minus-M1 contrast with an affirmative equivalence rule?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

The combination of named regions and straight/curved reaches may support a later standardized region comparison.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The dataset note documents that for MC_Maze releases the first digit of each unit ID is the region indicator (leading 1 = PMd, leading 2 = M1) and that the stored electrode indices for M1 units are miscoded, with the correct electrode-table row obtained by adding 96. It records a bounded metadata check (train: 72 PMd, 70 M1; test held-in: 52 PMd, 55 M1) and requires, before any region-specific plan proceeds, that units be assigned by the unit-ID convention, the M1 +96 correction be applied and verified, unit IDs / electrode metadata / DANDI metadata be reconciled, unresolved disagreements be kept visible, and usable trial counts and region-specific coverage be verified. It states the combined M1+PMd population may support planning with region-stratified sensitivity analyses, subject to small single-subject limitations.
  - Limitation: Documentation of a required data-handling procedure, not a scientific result; the note explicitly states its counts do not establish any regional difference.
  - Limitation: The required handling must be implemented in the executor skill; this evidence records the requirement, not its execution.
- **Unverified planning evidence:** The dataset is a single-subject (monkey Jenkins), single-session (2009-09-28) release limited to 100 train and 100 test trials. The test file (desc-test_ecephys) has 107 units and a trials table with only start_time, stop_time, move_onset_time, and split; it has NO behavior processing module and NO trial_version / num_barriers / maze_id columns. Therefore the curved/straight label and the hand-path curvature signal required by this variant exist only in the 100-trial train file. Usable labeled behavioral trials for the contrast = 100 (68 curved, 32 straight). The test file cannot add curved/straight-labeled behavioral trials and is not usable as a held-out behavioral sample for this question.
  - Limitation: Planning-only scope summary; bounds the achievable sample and generalization, establishing a real ceiling, not a defect that can be repaired within planning.
  - Limitation: Single subject and single session cap the claim at a within-subject, within-session association; no across-subject or causal generalization is supported.
- **Unverified planning evidence:** The train file contains 142 sorted units. By the documented unit-ID convention the split is 72 PMd (leading digit 1) and 70 M1 (leading digit 2), matching the DATASET_NOTES verification table. The electrodes table has 192 rows with 'location' evenly split 96 M1 and 96 PMd (group_name electrode_group_M1 / electrode_group_PMd). Both regions are represented, so a region-stratified PMd-versus-M1 population comparison is supported at the dataset level. Unit-ID leading digit is the reliable region key; the stored per-unit electrode indices (values 1-142) must not be used alone because of the documented M1 +96 electrode-row conversion error.
  - Limitation: Planning-only region-count verification; establishes representation of both regions, not unit quality, trial coverage, or any regional effect.
  - Limitation: Region assignment relies on the documented unit-ID convention; the raw per-unit electrode index is known to be miscoded for M1 and is not used for region assignment.
- 4 additional typed inspection statement(s) remain in the complete planning record.

### Plan at a glance

- Population and scope: Sorted-unit populations from one rhesus macaque (Jenkins), one session (2009-09-28), MC_Maze_Small train file: 72 PMd and 70 M1 units by the documented unit-ID convention, over 100 successful delayed center-out reaches (68 barriered curved, 32 no-barrier straight). Scope is within-subject and within-session; no across-subject or causal generalization is claimed.
- Unit of observation: One reach trial (movement epoch), with per-region population activity vectors.
- Unit of inference: The trial is the resampling unit; the terminal inferential unit is the reliability-standardized PMd-minus-M1 curvature-unique structure contrast within this single subject/session. Inference is within-subject; the single session is the generalization ceiling.
- Hierarchy and dependence: Trials are nested within 9 maze configurations and 3 versions and share a single subject/session. Curved and straight trials are pooled for the primary contrast with maze configuration and target direction handled as covariates or via condition-matching. Dependence is handled by trial-level cross-validation and bootstrap resampling that keep whole trials together; units are not treated as independent replicates for the regional claim (region reliability is standardized instead).
- Validation: Prespecify a smallest regional difference of interest (SESOI) in standardized units before inspecting outcomes. Estimate the PMd-minus-M1 difference with a bootstrap/credible precision interval over unit-subsampling and trial resampling, and run an equivalence test (TOST / interval-based) against the SESOI. Decision: CONCENTRATED if the difference interval robustly excludes zero and exceeds the SESOI in one region; DISTRIBUTED only if the interval falls entirely within the equivalence bounds (affirmative comparability); INCONCLUSIVE otherwise. A non-significant contrast is never read as distributed. Report equivalence-test power given the 100-trial sample.
- Split strategy: Trial-level (leakage-safe) cross-validation and bootstrap: whole trials assigned to train/test folds so no trial contributes to both fitting and evaluation of the separability metric; nested resampling for the unit-subsampling draws. No use of the benchmark test file (it lacks behavioral labels).
- Claim ceiling: associational

**Analysis strategy**

1. Assign region by the unit-ID leading digit (1=PMd, 2=M1); reconcile against electrodes.location after applying the documented M1 +96 electrode-row correction; keep any residual disagreement visible rather than dropping units (per DATASET_NOTES).
2. Define the movement epoch per trial from move_onset_time to reach completion; time-normalize (warp) each trial's population activity and behavior to a common epoch so curved-path structure is defined independently of movement duration.
3. Compute a continuous hand-path curvature index per trial (path-length / start-to-end displacement; maximum lateral deviation as a robustness variant) from hand_pos.
4. 4 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Shuffle the curvature label across trials within matched condition strata; curvature-unique structure should collapse to chance.; A scientifically irrelevant label (e.g., trial index parity or eye-position-only feature) should show no region-specific curvature-attributable structure.
- Positive controls: Target/endpoint direction should be decodable from both regions' population activity, confirming the population signal and metric are functioning before interpreting the curvature contrast.
- Alternative explanations: Duration and general movement-magnitude differences between curved and straight reaches (addressed by time-warping and kinematic partialling).; Visual/obstacle, target, and distractor differences carried by barrier/version condition (addressed by covariate partialling and condition-matching).; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject (Jenkins) and single session cap the claim at a within-subject, within-session association; no across-subject or causal generalization.
- Only 100 labeled trials (68 curved / 32 straight) limit power; a well-powered SESOI may be unreachable and INCONCLUSIVE is a legitimate result, not a failure of the plan.
- Region assignment depends on the documented unit-ID convention and the M1 +96 correction; any unresolved metadata disagreement is kept visible rather than resolved by dropping units.
- 2 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

The plan preserves the variant's protected phenomenon (where curved-path-specific structure is expressed across PMd and M1), its target contrast (condition-relative curved-vs-straight structure, not preparation-to-execution staging), and its outcome meanings (concentration = predictive regional specialization; distributed = affirmatively established comparability). All three Owner rulings were incorporated: curvature isolated from duration and condition confounds, reliability-standardized regional comparison, and an equivalence-based inference for the distributed outcome.

**Before any later execution**

- Unresolved planning decisions: Numeric SESOI value (framework fixed, number to be prespecified before execution).; Include vs exclude heldout=True units (default include-all with heldin-only sensitivity check).; plus 1 additional item(s) in the complete dossier
- Required future skills: Executor skill implementing: region assignment via unit-ID convention with the M1 +96 electrode-row correction and metadata reconciliation; continuous hand-path curvature index and movement-epoch time-warping; confound-partialled per-region population encoding/separability model; reliability-equalization (unit-count subsampling, bias-corrected cross-validated metric, per-region noise-ceiling normalization); and the prespecified SESOI equivalence/precision decision rule.

### Scientific stakes

**Discriminating observation**

A standardized comparison of curved-versus-straight population structure across both regions, interpreted relative to region-specific reliability, would distinguish concentrated and distributed accounts.

**What possible outcomes would mean**

- Positive pattern: A robust regional concentration would support a predictive regional specialization hypothesis for curved-path processing.
- Negative pattern: Comparable target-specific structure across regions would favor a distributed organization.
- Null or ambiguous pattern: Uncertain or sensitivity-dependent regional differences would leave spatial organization unresolved.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The variant plan preserves the protected condition-relative PMd-versus-M1 curvature-structure contrast, limits inference to a within-subject/session association, addresses measured trajectory, target, distractor, and kinematic alternatives, standardizes regional measurement sensitivity, and requires affirmative equivalence rather than interpreting a null difference as distributed organization. Remaining choices are appropriate pre-execution locks, not planning blockers.

Retained changes and locks:

- **Pre execution lock:** Prespecify the numerical standardized SESOI for the equivalence decision before execution.
- **Pre execution lock:** Fix the primary bias-corrected separability estimator and the heldout-unit inclusion rule before execution.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan preserves the protected condition-relative PMd-versus-M1 curvature-structure contrast and does not merge it with preparation-to-execution staging. It is evidence-grounded (region mapping, trial/curvature structure, behavioral signal, neural coverage, and scope limits are all directly tied to inspected dataset facts), isolates curvature-unique structure from duration, target/distractor, and kinematic confounds, reliability-standardizes the regional comparison to prevent measurement-sensitivity artifacts, and requires an affirmative equivalence test rather than treating a null difference as distributed organization. Claim ceiling is honestly capped at within-subject/session association, and INCONCLUSIVE is acknowledged as a legitimate outcome given the 100-trial sample. The two Owner-identified items (numeric SESOI value; primary estimator and heldout-inclusion rule) are pre-execution implementation locks, not scientific blockers, so this remains an accept that carries them forward.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
