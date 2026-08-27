# Regional organization of behaviorally relevant covariance geometry — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Validation warning**
- Authority: **Provisional / degraded**
- Accepted-plan authority: **No**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether behaviorally relevant covariance follows a shared brain-wide geometry or consists of regionally distinct population solutions.

The scientific tension is:

Decision and movement signals can be distributed across the brain, but distribution does not establish a common population mechanism. Similar behavior may be associated with a recurrent geometry across regions or with distinct local geometries.

## How to read this terminal

Returned planning material did not pass strict typed validation. The family is complete as a readable soft terminal, but it remains provisional and degraded with no accepted-plan authority.

**Recorded public status note**

Returned planning material could not be fully validated; a readable family dossier was retained with a validation warning.

## Variant 1: Independently estimated cross-population covariance-geometry recurrence branch

### Why it matters

This distinction tests whether distributed decision signals share a population-level organizational motif rather than merely co-occurring across regions, while allowing informative local decision coding to coexist with regional geometric specialization.

### Original and refined question

**Original Question Scientist proposal**

Does a common covariance geometry aligned with sensory-to-choice progression recur across anatomically separated populations during decision formation?

**Post-novelty revised proposal**

Across anatomically separated populations, do separately estimated residual-covariance–whitened representational distance geometries of sensory-to-choice states recur and transfer across recordings beyond matched sensory, trial-time, choice, and movement-preparatory alternatives?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Broad anatomical sampling under a standardized decision task may permit selected populations or recordings to yield independently estimated, covariance-whitened distance matrices over comparable task states and may support cross-recording evaluation; actual comparability and coverage remain to be established by later planning.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The build summary reports 459 sessions, 699 insertions, 75,395 units, and 295,920 trials. The unit table provides Beryl-region labels and quality labels. Aggregate coverage includes 880 VISp units from 51 insertions across 47 sessions and 1,293 MOs units from 49 insertions across 45 sessions; the two sets have no overlapping session in this snapshot.
  - Limitation: VISp and MOs are not simultaneous within a session here, so the regional comparison must generalize across independently recorded sessions and cannot estimate within-session interregional covariance.
  - Limitation: Aggregate counts do not establish matched subject, laboratory, trial-composition, or per-recording covariance precision.
- **Unverified planning evidence:** The ephys build declares keyed sessions, insertions, units, trials, events, and clusters tables; its spike store is sharded by insertion and contains delta-encoded spike times, spike-cluster assignments, cluster IDs, and cluster spike counts.
  - Limitation: The schema establishes available surfaces but not the adequacy of any individual recording for covariance estimation.
  - Limitation: No neural response matrix or scientific outcome was computed during planning.
- **Unverified planning evidence:** Trial keys are eid and trial_id. Ephys trials contain left and right contrasts, choice, stimulus, go-cue, first-movement, response, and interval times; behavior features provide signed contrast, choice label, reaction time, and movement time; wheel features provide movement onset, direction, amplitude, and velocity summaries.
  - Limitation: Availability of wheel features is not universal and must be an explicit inclusion or missing-data rule.
  - Limitation: Schema presence does not demonstrate that covariate matching will retain sufficient trials in every recording.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

For each anatomical population or recording separately, estimate residual covariance after accounting for specified sensory, trial-time, choice, and movement-preparatory variables, then use that covariance to construct a cross-validated whitened distance matrix among sensory-to-choice states. Evidence for recurrence would require quantitative matrix correspondence or transfer to held-out populations or recordings without pooled estimation or a jointly fitted latent space, exceeding matched alternatives that preserve sensory, timing, choice, or movement modulation. Regional specialization would instead be supported if populations retain decision-related information or local choice dynamics but their independently estimated geometries differ reproducibly and fail the same cross-population transfer criterion.

**What possible outcomes would mean**

- Positive pattern: If independently estimated geometries correspond and transfer beyond the matched alternatives, the result would support a recurring descriptive organization of behaviorally relevant residual covariance across the sampled populations, distinct from previously reported widespread evidence or movement-preparation activity.
- Negative pattern: If adequately estimated populations retain decision-related information but show reproducibly different geometries and fail cross-population transfer, the result would weaken the shared-motif account and favor regional specialization or heterogeneous population solutions.
- Null or ambiguous pattern: If correspondence and specialization cannot be distinguished because geometry estimates are unstable, coverage is uneven, or conclusions depend on state definitions or controls, recurrence would remain unresolved without contradicting prior findings of distributed representations or local choice geometry.

## Variant 2: Task-specific VISp–MOs covariance-alignment and response-time branch

### Why it matters

A sampling-matched, out-of-sample link between regional covariance-axis alignment and response-time variation would constrain claims that distributed decision-related activity follows one common population organization, while avoiding the stronger inference that detectability establishes local or causal computation.

### Original and refined question

**Original Question Scientist proposal**

Do anatomically distinct populations exhibit different covariance geometries whose associations with sensory evidence, choice, movement, or response time imply region-specific computational solutions?

**Post-novelty revised proposal**

Within a defined visual decision task, do primary visual cortex (VISp) and secondary motor cortex (MOs) differ in the alignment between stimulus-conditioned and movement-conditioned covariance axes, and does that regional difference predict held-out response-time variation better than a common-geometry or sampling-matched baseline?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Broad anatomical sampling under a standardized task may permit a later planner to identify sufficiently comparable VISp and MOs recordings and evaluate whether covariance-axis alignment has region-specific held-out associations with the movement-timing variable family.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The build summary reports 459 sessions, 699 insertions, 75,395 units, and 295,920 trials. The unit table provides Beryl-region labels and quality labels. Aggregate coverage includes 880 VISp units from 51 insertions across 47 sessions and 1,293 MOs units from 49 insertions across 45 sessions; the two sets have no overlapping session in this snapshot.
  - Limitation: VISp and MOs are not simultaneous within a session here, so the regional comparison must generalize across independently recorded sessions and cannot estimate within-session interregional covariance.
  - Limitation: Aggregate counts do not establish matched subject, laboratory, trial-composition, or per-recording covariance precision.
- **Unverified planning evidence:** The ephys build declares keyed sessions, insertions, units, trials, events, and clusters tables; its spike store is sharded by insertion and contains delta-encoded spike times, spike-cluster assignments, cluster IDs, and cluster spike counts.
  - Limitation: The schema establishes available surfaces but not the adequacy of any individual recording for covariance estimation.
  - Limitation: No neural response matrix or scientific outcome was computed during planning.
- **Unverified planning evidence:** Trial keys are eid and trial_id. Ephys trials contain left and right contrasts, choice, stimulus, go-cue, first-movement, response, and interval times; behavior features provide signed contrast, choice label, reaction time, and movement time; wheel features provide movement onset, direction, amplitude, and velocity summaries.
  - Limitation: Availability of wheel features is not universal and must be an explicit inclusion or missing-data rule.
  - Limitation: Schema presence does not demonstrate that covariate matching will retain sufficient trials in every recording.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

The regional claim would require a prespecified comparison restricted to populations passing common recording-quality inclusion criteria, with neuron counts equalized by repeated subsampling and trial counts and distributions matched across stimulus, choice, movement, and response-time strata. Under those matches, the VISp–MOs difference in alignment between stimulus-conditioned and movement-conditioned covariance axes must reproduce in held-out recordings, and region-specific geometry must predict held-out response-time variation better than both a geometry shared across regions and the distribution expected from sampling-matched comparisons.

**What possible outcomes would mean**

- Positive pattern: If the matched VISp–MOs alignment difference reproduces and region-specific geometry improves held-out response-time prediction over both baselines, it would support a task-specific sensory-versus-movement-timing dissociation in cortical population organization. It would not by itself establish causal localization or a general principle across tasks.
- Negative pattern: If adequately estimated held-out results favor the common-geometry baseline and exclude a practically meaningful region-specific predictive advantage, the result would weaken this VISp–MOs dissociation and favor a shared organization for the tested task and behavioral-variable family.
- Null or ambiguous pattern: If estimates remain unstable across matched subsamples or held-out recordings, or if common and region-specific baselines are indistinguishable at the available precision, the regional dissociation would remain unresolved rather than support either specialization or commonality.

## Owner and independent review

Any typed review records below are retained context only. They cannot override this system terminal or create accepted-plan authority.

### Question Owner

- Disposition: **Revise**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The two variants preserve the protected competing organizational claims and have credible recording-level, held-out analysis routes. However, the regional-specialization variant currently uses response-time strata in trial matching while also evaluating trial-level response-time prediction. Unless held-out trial selection and matching are independent of held-out response-time labels, this creates outcome leakage and invalidates the claimed incremental predictive comparison. The remaining estimator and eligibility choices are appropriate pre-execution locks rather than planning blockers.

Retained changes and locks:

- **Scientific blocker:** Revise the VISp–MOs analysis so that held-out response-time labels are not used for trial selection, matching, tuning, or construction of predictors evaluated for response-time prediction. Trial matching may use predictors available at prediction time; any response-time-based stratification must be confined to a clearly separated descriptive or post-evaluation assessment.
- **Pre execution lock:** Before execution, lock the common-geometry state grid, recording eligibility and covariance-stability rules, shrinkage rule, and movement-covariate missingness/representation rule without inspecting target comparison outcomes.
- **Pre execution lock:** Before execution, lock the VISp–MOs response-time transform, predictive comparison criterion, common quality rule, and matching tolerance using blinded coverage and synthetic-recovery procedures.

### Independent reviewer

- Disposition: **Revise**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants credibly instantiate the protected competing claims (recurrent covariance-whitened geometry vs. regionally distinct covariance-axis alignment) with matched task-variable and sampling-matched baselines, appropriate held-out recording-level splits, and honest scope limits. The v2 (VISp-MOs) plan, however, matches trials on response-time strata while also evaluating held-out prediction of response-time variation from the resulting geometry; this uses the outcome to shape the evaluated trial set and invalidates the incremental predictive estimand as currently specified. This is a genuine scientific blocker rather than a pre-execution detail because it undermines the validity of the target held-out comparison itself. The remaining unresolved items are legitimate pre-execution locks that do not require plan-level revision. I concur with the Owner's classification and do not identify additional blockers.

Retained changes and locks:

- **Scientific blocker:** Revise the VISp–MOs analysis so that held-out response-time labels are not used for trial selection, matching, tuning, or construction of predictors evaluated for response-time prediction. Trial matching may use predictors available at prediction time; any response-time-based stratification must be confined to a clearly separated descriptive or post-evaluation assessment.

**Authority reminder:** these dispositions do not yield an accepted plan here.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
