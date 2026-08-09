# Population geometry across straight and curved reaches — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Examines whether motor population representations preserve reusable movement structure across straight and curved maze contexts or remap in a context-specific manner.

The scientific tension is:

Stable task-relevant representations may support generalization across trajectory contexts, but apparent stability could reflect shared kinematics, while remapping could reflect either useful context specialization or incidental differences.

## Variant 1: Cross-context invariance branch

### Why it matters

The question links geometric stability to predictive generalization rather than equating visual similarity of latent spaces with functional reuse.

### Original and refined question

**Original Question Scientist proposal**

Is a task-relevant population geometry conserved across straight and curved reaches in a way that supports cross-context prediction of movement?

**Reviewed refined question**

Is a task-relevant motor population geometry conserved across straight (barrier-free) and curved (barrier) reaches to matched endpoints such that a relational organization characterized in one context predicts task-relevant movement relationships in the other, beyond matched kinematic similarity and generic decoding baselines, and not merely because separate context-specific codes carry similar decodable movement information?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

The described straight and curved reaches with paired spiking and movement measurements may allow later planning of context-transfer comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- No safely resolved, typed inspection statement was available for this view.

### Plan at a glance

- Population and scope: Single macaque (Jenkins), single delayed center-out maze reaching session (DANDI:000140 small release). 107 held-in sorted units spanning M1 and PMd. Scope is the 9 reach endpoints attained in both trajectory contexts. Inference is about this subject/session; generalization beyond it is not claimed.
- Unit of observation: A single trial (a reach to one of 9 endpoints in either the straight or curved context).
- Unit of inference: The reach endpoint x context cell; cross-context inference treats endpoints as the shared relational elements, with trials nested within endpoint x context.
- Hierarchy and dependence: Trials are nested within (endpoint x context) cells and within a single session. Dependence is handled with leave-one-endpoint-out and leave-one-condition-out cross-validation and trial-level bootstrap for uncertainty, ensuring no trial appears in both the fit and test folds of any alignment or readout.
- Validation: Leakage-safe, dependence-aware validation: leave-one-endpoint-out and leave-one-condition-out folds for cross-context transfer, trial bootstrap for confidence intervals, and a synthetic method-recovery probe on simulated shared-geometry vs separate-code populations to confirm the test discriminates the two before touching the real comparison. No target outcomes are inspected to tune choices; decision rules are prespecified.
- Split strategy: Cross-context folds defined by context and endpoint so that alignment is always fit and tested on disjoint trials; within-context baselines use nested trial folds.
- Claim ceiling: predictive

**Analysis strategy**

1. Define trajectory context from num_barriers (0=straight, 9=curved) and confirm the curvature separation on the analysis window before modeling.
2. Build binned spike-count / smoothed-rate population representations per trial aligned to movement onset; screen units by a prespecified rate/quality rule.
3. Estimate a task-relevant population geometry per context as the relational structure over the 9 matched endpoints (condition-averaged low-dimensional subspace plus an endpoint representational dissimilarity matrix).
4. 4 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Shuffled context labels (destroys any true straight/curved distinction).; A scientifically irrelevant contrast (e.g., trial-index halves or eye-position-only readout) that should show no genuine cross-context geometric reuse.
- Positive controls: Within-context endpoint readout should recover endpoint structure well.; A documented structural signal (e.g., movement-direction tuning) should be recoverable within each context.
- Alternative explanations: Cross-context prediction driven by shared hand/cursor kinematics rather than conserved neural organization (addressed by the matched-kinematic baseline and endpoint matching).; Separate context-specific codes carrying similar decodable information without shared geometry (addressed by the transfer-vs-within-context and shared-vs-separate-subspace comparisons).; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- Single subject and single session; observational, not experimentally manipulated neural organization.
- Small per-condition trial counts limit precision; results are provisional planning targets, not scientific outcomes.
- Geometry is inferred; no causal or mechanistic claim is licensed.

**Why the plan serves the question**

The plan preserves the variant's central phenomenon (conserved task-relevant geometry across straight and curved reaches supporting cross-context prediction) and its discriminating observation (one-context representation predicts the other beyond matched kinematics and generic baselines), while explicitly separating shared relational geometry from separate context-specific codes with similar information, as the Owner required. The endpoint-matched design and behavioral curvature validation guard against the forbidden kinematic-confound and coarse-classification reinterpretations.

**Before any later execution**

- Unresolved planning decisions: Prespecified movement window and geometry estimator to be locked before execution.

### Scientific stakes

**Discriminating observation**

A representation characterized in one broad trajectory context predicts task-relevant movement relationships in the other beyond matched kinematic similarity and generic decoding baselines.

**What possible outcomes would mean**

- Positive pattern: A positive result would support reusable population organization across trajectory contexts.
- Negative pattern: A negative result would favor context-specific organization or stronger dependence on trajectory-specific inputs.
- Null or ambiguous pattern: A null result would leave open whether weak transfer reflects genuine remapping or inadequate representational estimation.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan credibly tests the protected cross-context reuse variant using matched endpoints across behaviorally distinct straight and curved reaches, a leakage-safe transferred representation/readout, and comparisons that distinguish shared geometry from separate context-specific codes with similar decodable information. Its predictive, single-session claim ceiling and limitations are appropriate. Movement-window and geometry-estimator choices remain explicit pre-execution locks, not planning blockers.

Retained changes and locks:

- **Pre execution lock:** Prespecify the movement window, curvature/matching procedure, and associated unit/trial quality rules before execution.
- **Pre execution lock:** Prespecify a non-outcome-tuned rule for selecting the geometry estimator, dimensionality, and any regularization before execution.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan credibly operationalizes the protected cross-context-reuse variant using an endpoint-matched design (all 9 reach goals attained in both barrier conditions) validated by a real behavioral curvature difference (1.09 vs 1.61), 107 held-in M1+PMd units, and recorded kinematics for baselines. The core test (fit-on-one-context, apply-without-refitting-to-other, with a shared-vs-separate subspace comparison and cross-context RDM correlation) is genuinely geometry-sensitive and explicitly designed to distinguish conserved relational structure from separate context-specific codes carrying similar decodable information, per the family's theoretical tension. Alternative explanations (kinematic confound, coarse classification, separate-but-similar codes) are each matched to a specific analytic safeguard. Controls are adequate: positive controls (within-context recovery, direction tuning), negative controls (shuffled labels, irrelevant contrasts), and a pre-registered synthetic method-recovery probe that validates discriminability before touching real data. Validation is leakage-safe (leave-one-endpoint-out/leave-one-condition-out, trial bootstrap). The claim ceiling is predictive/associational with honest single-subject, single-session, small-per-condition-count limitations, and no causal or mechanistic overreach. Sibling separation is intact: target_contrast and forbidden_semantic_merges keep this variant's cross-context predictive-reuse focus distinct from the sibling's context-dependent remapping focus, and nothing in the plan collapses the two into one claim. The two Owner-identified items (movement-window/curvature-matching/quality-rule prespecification; non-outcome-tuned geometry-estimator selection rule) are legitimate pre-execution locks — the plan already fixes the relevant constructs, comparisons, and safeguards, and these are implementation choices to fix before running, not gaps in the scientific design. No new scientific blocker is identified, so this is an accept carrying two pre-execution locks rather than a revision.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
