# Behavioral-state explanations for motor-cortical population variability — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Reclassifies apparently unexplained M1 and PMd variability by testing multidimensional behavioral-state explanations, with distinct regional-distribution and task-subspace-overlap variants.

The scientific tension is:

Population variability may reflect intrinsic neural dynamics or latent readiness, but it may also encode measured movement, gaze, or other embodied state; predictability alone does not determine its scientific meaning.

## Variant 1: regional distribution test

### Why it matters

The question reframes nuisance variance as a candidate representation and tests its anatomical scope without inferring neural causation of behavior.

### Original and refined question

**Original Question Scientist proposal**

Is population variability associated with multidimensional behavioral state distributed similarly across PMd and M1, or selectively concentrated in one region?

**Reviewed refined question**

Within the documented MC_Maze_Small training session, is neural population structure associated with multidimensional measured behavioral state comparably detectable in PMd and M1 after matched reliability and task-condition checks?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

The broad availability of hand, cursor, eye, and velocity measurements alongside M1 and PMd activity may support later planning of multidimensional state comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** For MC_Maze releases, the first digit of unit ID is documented as the authoritative region indicator: leading 1 denotes PMd and leading 2 denotes M1. The notes warn that stored M1 electrode indices require a plus-96 correction, so raw unit-electrode indices alone must not be used for regional assignment; the pinned training metadata summary reports representation from both regions.
  - Limitation: Regional assignment must be implemented from the documented unit-ID convention and audited against the conversion caveat.
  - Limitation: The note is release-specific and does not establish equal unit counts, equal recording quality, or comparable reliability.
  - Limitation: This documentation does not provide a scientific result.
- **Unverified planning evidence:** The pinned MC_Maze_Small release contains sorted unit spike times and behavioral data from one rhesus macaque performing a delayed center-out reaching task with maze barriers; recordings are described as M1 and PMd, and the release is limited to 100 train and 100 test trials.
  - Limitation: The documented sample is one subject and one release, so any regional result has limited population generalizability.
  - Limitation: This metadata inspection does not establish behavioral coverage, neural effect size, or subspace reliability.
  - Limitation: Test data are not proposed for planning or analysis.
- **Unverified planning evidence:** The training NWB schema documents continuous hand position, cursor position, eye position, and hand velocity; trial fields include target position, active target, maze ID, trial type, trial version, target-on time, and number of targets; the units table documents spike times, held-out status, and electrode linkage.
  - Limitation: Schema presence does not establish complete observations, timestamp alignment, or adequate coverage of each task condition.
  - Limitation: The reach-demand construct is a plausible proxy using target geometry and maze descriptors and requires Owner review before execution.
  - Limitation: No raw values or outcome estimates were inspected.

### Plan at a glance

- Population and scope: Sorted units assigned to PMd and M1 by the documented unit-ID convention, and successful training trials from the one macaque delayed reaching session; no test trials are used.
- Unit of observation: Cross-validated, event-aligned time-bin population activity paired with contemporaneous and lagged measured behavioral features.
- Unit of inference: Region-specific held-out trial blocks within the one session; region comparison is a within-session associational contrast.
- Hierarchy and dependence: Preserve trial blocks during all splitting and resampling; model temporal autocorrelation with blocked folds and aggregate comparisons at the trial-block level rather than treating bins as independent.
- Validation: Verify timestamp alignment and trial coverage before fitting; use fold-separated preprocessing, within-fold dimension selection, label and time-shift controls, and recovery on synthetic data with known regional equality or selectivity.
- Split strategy: Use outer blocked trial folds stratified by documented task descriptors; retain whole trials and contiguous bins in one fold, with inner blocked folds for regularization and dimension selection.
- Claim ceiling: associational

**Analysis strategy**

1. Construct a multidimensional behavioral-state feature set from hand position, hand velocity, cursor position, eye position, and prespecified lags, standardized within training folds.
2. For each region, estimate cross-validated behavior-associated population dimensions using a regularized reduced-rank encoding model or canonical latent-variable model with dimensions selected only by inner-fold stability.
3. Compare held-out explained neural variance or aligned latent reliability using matched unit-count subsampling, matched trial blocks, and uncertainty intervals over blocked resamples.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Circularly time-shift behavioral features within intact trial blocks beyond the prespecified lag window.; Permute behavioral-feature blocks across matched trials while preserving region and task labels.
- Positive controls: Recover known simulated behavior-to-population coupling and known equal-versus-selective regional structure using the planned blocked validation procedure.
- Alternative explanations: Unequal unit yield, firing reliability, or region-label conversion error.; Task-condition imbalance or reach-dependent behavior rather than general behavioral state.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- The analysis cannot causally attribute neural variability to behavior or exclude latent readiness.
- The plan addresses only measured behavioral state in one macaque session and cannot generalize prevalence across animals or tasks.

**Why the plan serves the question**

It preserves the regional-distribution contrast by estimating the same measured behavioral-state construct independently in PMd and M1 and treating reliability, region labels, and task covariation as explicit alternatives rather than collapsing the question into task-subspace overlap.

**Before any later execution**

- Unresolved planning decisions: Prespecify event window, bin width, lag set, and minimum modality-coverage threshold before execution.

### Scientific stakes

**Discriminating observation**

Reliable behavior-associated population structure in both regions versus selective structure in one region, evaluated against simpler state summaries and matched reliability checks, would distinguish distributed from localized accounts.

**What possible outcomes would mean**

- Positive pattern: Distributed structure would support an associational account of embodied state represented across motor-cortical levels.
- Negative pattern: Reliable regional selectivity would support a localized or differentiated organization rather than a common global state.
- Null or ambiguous pattern: Poor or inconsistent prediction would leave open intrinsic variability, unmeasured behavior, and insufficient reliability.

## Variant 2: task-state geometric overlap test

### Why it matters

Separating overlap from independence clarifies whether behavior is the explanatory construct of interest or an alternative explanation for apparent task coding.

### Original and refined question

**Original Question Scientist proposal**

Do behavioral-state-associated neural dimensions overlap with or remain geometrically distinct from dimensions distinguishing reach demands?

**Reviewed refined question**

Within the documented MC_Maze_Small training session, do independently defined neural dimensions associated with measured behavioral state align with, or remain distinct from, dimensions distinguishing prespecified reach demands?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Joint neural and broad behavioral measurements may allow later comparison of independently defined behavioral-state and reach-demand dimensions.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The pinned MC_Maze_Small release contains sorted unit spike times and behavioral data from one rhesus macaque performing a delayed center-out reaching task with maze barriers; recordings are described as M1 and PMd, and the release is limited to 100 train and 100 test trials.
  - Limitation: The documented sample is one subject and one release, so any regional result has limited population generalizability.
  - Limitation: This metadata inspection does not establish behavioral coverage, neural effect size, or subspace reliability.
  - Limitation: Test data are not proposed for planning or analysis.
- **Unverified planning evidence:** The training NWB schema documents continuous hand position, cursor position, eye position, and hand velocity; trial fields include target position, active target, maze ID, trial type, trial version, target-on time, and number of targets; the units table documents spike times, held-out status, and electrode linkage.
  - Limitation: Schema presence does not establish complete observations, timestamp alignment, or adequate coverage of each task condition.
  - Limitation: The reach-demand construct is a plausible proxy using target geometry and maze descriptors and requires Owner review before execution.
  - Limitation: No raw values or outcome estimates were inspected.

### Plan at a glance

- Population and scope: All documented training-session sorted units analyzed as a combined population and, secondarily, by documented region; successful training trials only from the one macaque session.
- Unit of observation: Cross-validated event-aligned time-bin population activity with independently fitted behavioral-state features and trial-level reach-demand design variables.
- Unit of inference: Held-out trial blocks within the one session, summarized with uncertainty across blocked resamples.
- Hierarchy and dependence: Keep all bins from a trial in the same fold; define behavioral and reach-demand subspaces in separate training partitions and evaluate alignment only on held-out blocks to prevent circular geometry estimates.
- Validation: Audit condition counts and modality coverage before fitting; use nested blocked folds, synthetic recovery of known overlapping and orthogonal subspaces, and null calibration with fold-preserving label permutations.
- Split strategy: Use outer trial-block folds stratified where feasible by documented maze and target descriptors; estimate each subspace only in the relevant training partition and reserve outer folds for alignment evaluation.
- Claim ceiling: associational

**Analysis strategy**

1. Define behavioral-state dimensions from continuous hand, velocity, cursor, and eye signals using training-fold-only regularized encoding or reduced-rank methods.
2. Define reach-demand dimensions independently from target geometry plus the prespecified maze or barrier descriptors, subject to Owner confirmation of this proxy.
3. Estimate held-out subspace alignment with principal angles or cross-validated shared-variance measures, using matched dimensionality and independently estimated bases.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permute reach-demand labels across matched trial blocks within prespecified strata.; Time-shift continuous behavioral features within trial blocks beyond the prespecified lag window.
- Positive controls: Recover known overlap and known orthogonality from synthetic population data using the same cross-validated alignment pipeline.
- Alternative explanations: Reach-dependent movement or gaze differences induce apparent subspace overlap.; Unequal task-condition coverage or limited trial count destabilizes the reach-demand basis.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- Overlap cannot establish that behavioral state causes task representation or that either construct encodes intention.
- The reach-demand definition is a dataset-supported proxy and must remain distinguishable from measured movement and gaze.
- One-session, one-subject scope limits generalization.

**Why the plan serves the question**

It preserves the geometric overlap-versus-separation contrast by defining behavioral and reach-demand dimensions independently, evaluating them on held-out trial blocks, and explicitly testing whether reach-dependent measured behavior explains any apparent alignment.

**Before any later execution**

- Unresolved planning decisions: Owner confirmation is required for the target-geometry-plus-maze definition of reach demands.; If task-condition coverage is insufficient for blocked stratification, execution must report the limitation and restrict the estimand rather than pool unsupported conditions.

### Scientific stakes

**Discriminating observation**

Cross-validated alignment between independently defined behavioral and reach-demand dimensions, compared with matched controls and condition-balanced behavior, would distinguish integration from separability.

**What possible outcomes would mean**

- Positive pattern: Specific overlap would support an associational account in which embodied state is integral to the observed task representation.
- Negative pattern: Reliable geometric separation would support distinct task and state components of population activity.
- Null or ambiguous pattern: Unstable alignment would leave the relation between behavioral state and task geometry underdetermined.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family plan preserves the distinct regional-distribution and task-subspace-overlap questions, uses only the documented training-session modalities and region convention, and limits claims to within-session associations. Fold-separated modeling, blocked validation, matched comparisons, and stated alternatives make both variants scientifically credible without requiring execution-ready parameter choices.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variant plans preserve the protected family intent and its forbidden-merge boundary: variant-01 estimates the regional distribution of behavior-associated population structure with matched unit counts and reliability, while variant-02 independently tests geometric overlap between behavioral-state and reach-demand subspaces on held-out blocks. Claims are held at an associational ceiling appropriate to a single-subject, single-session release, and dataset grounding is limited to documented training-session modalities, trial descriptors, and the audited unit-ID region convention with the plus-96 correction caveat. Alternatives (reliability/yield asymmetry, task-condition imbalance…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
