> ⚠️ Provisional inspiration: planning continued from source-bound but not independently reviewed inputs. Dataset claims remain conditional or unverified, and this dossier cannot be elevated above provisional authority without independent review.

> ⚠️ Data basis: this family's open gap / key claims rest on ABSTRACT-ONLY literature (full text was not available to this system). The questions are literature-motivated but NOT fulltext-verified; a domain expert should confirm against primary sources.

# Population geometry across straight and curved reaches

This is a development planning dossier. It is planning-only and does not report scientific results.
Dataset grounding level: `schema_metadata_inspected`.
Dataset claim status: `unverified`.

## Question Family

Examines whether motor population representations preserve reusable movement structure across straight and curved maze contexts or remap in a context-specific manner.

## Scientific Motivation

Stable task-relevant representations may support generalization across trajectory contexts, but apparent stability could reflect shared kinematics, while remapping could reflect either useful context specialization or incidental differences.

## Dataset Leverage

Dataset claim status is unverified; observed-depth label is schema_metadata_inspected. Dataset leverage remains a planning hypothesis, by variant: Variant 1: The described straight and curved reaches with paired spiking and movement measurements may allow later planning of context-transfer comparisons. No scientific-result generation was performed.

## Variant Plans

- Variant 1 (Cross-context invariance branch): Is a task-relevant population geometry conserved across straight and curved reaches in a way that supports cross-context prediction of movement?
  - Distinguishing test: This variant treats cross-context predictive reuse as the critical outcome; the sibling treats context-dependent remapping and its possible behavioral relevance as the focal outcome. The discriminating observation is A representation characterized in one broad trajectory context predicts task-relevant movement relationships in the other beyond matched kinematic similarity and generic decoding baselines.
  - Planned analysis: Accepted. The dataset provides a behaviorally validated straight-vs-curved context
    - label with reach goals matched across contexts, a simultaneously recorded M1+PMd
    - population, and recorded kinematics for matched-kinematic and generic-decoding
    - baselines. The plan specifies a geometry-sensitive cross-context test that
    - distinguishes conserved relational geometry from separate context-specific codes
    - with similar decodable information, addressing the Owner's revise ruling. Main
    - limitations are single-subject, single-session scope and small per-condition counts.
    - Refined question: Is a task-relevant motor population geometry conserved across straight
    - (barrier-free) and curved (barrier) reaches to matched endpoints such that a
    - relational organization characterized in one context predicts task-relevant
    - movement relationships in the other, beyond matched kinematic similarity and
    - generic decoding baselines, and not merely because separate context-specific
    - codes carry similar decodable movement information?
    - Population and scope: Single macaque (Jenkins), single delayed center-out maze reaching session
    - (DANDI:000140 small release). 107 held-in sorted units spanning M1 and PMd. Scope
    - is the 9 reach endpoints attained in both trajectory contexts. Inference is about
    - this subject/session; generalization beyond it is not claimed.
    - Data sources: Held-in M1+PMd sorted-unit spike times with region assigned by the documented unit-ID convention and M1 +96 electrode caveat.; Expected grain: One spike train per unit per trial, aligned to trial timing events.; Required variables: spike_times, heldout, electrodes, unit_id_region; Limitations: Region assignment depends on the unit-ID rule and +96 correction; disagreements kept visible, not resolved by assuming M1 absent. Wide spike-count range across units requires a prespecified quality/rate screen. Per-trial condition and timing table used to assign trajectory context, reach endpoint, and movement-epoch alignment.; Expected grain: One row per trial (n=100 train).; Required variables: num_barriers, maze_id, active_target, target_pos, move_onset_time, go_cue_time, target_on_time; Limitations: Small per-condition counts (~3-4 straight trials per endpoint) bound precision. Endpoint matching is at goal-location level; moment-by-moment kinematic differences remain and are handled analytically. Time-stamped hand position/velocity, cursor, and eye signals at 1 kHz for kinematic baselines and readout targets.; Expected grain: Continuous 2D time series sampled at 1 kHz, segmented per trial.; Required variables: hand_pos, hand_vel, cursor_pos; Limitations: hand_vel is derived from hand_pos; kinematic-control analyses must note this dependence. Per-trial alignment and gaps to be verified at execution.
    - Unit of observation: A single trial (a reach to one of 9 endpoints in either the straight or curved context).
    - Unit of inference: The reach endpoint x context cell; cross-context inference treats endpoints as the shared relational elements, with trials nested within endpoint x context.
    - Hierarchy and dependence: Trials are nested within (endpoint x context) cells and within a single session.
    - Dependence is handled with leave-one-endpoint-out and leave-one-condition-out
    - cross-validation and trial-level bootstrap for uncertainty, ensuring no trial
    - appears in both the fit and test folds of any alignment or readout.
    - Analysis strategy: Define trajectory context from num_barriers (0=straight, 9=curved) and confirm the curvature separation on the analysis window before modeling. Build binned spike-count / smoothed-rate population representations per trial aligned to movement onset; screen units by a prespecified rate/quality rule. Estimate a task-relevant population geometry per context as the relational structure over the 9 matched endpoints (condition-averaged low-dimensional subspace plus an endpoint representational dissimilarity matrix). Run the geometry-sensitive cross-context reuse test: fit the readout/subspace on one context and apply it WITHOUT refitting to the other, quantifying preservation of the endpoint relational structure (cross-context RDM correlation and cross-context generalization of an endpoint/movement readout). Discriminate reuse from separate-but-similar codes: compare cross-context-transferred performance against independently fit within-context readouts (which index decodable information per context) and against a shared-subspace-vs-per-context-subspace nested model comparison; conserved geometry requires transfer to approach within-context performance AND a shared subspace/RDM, whereas high within-context but collapsed transfer indicates context-specific codes with similar information. Benchmark every reuse statistic against a matched-kinematic-similarity baseline (predicting the same movement relationships from hand position/velocity) and generic decoding baselines, requiring neural reuse to exceed both. Run region-stratified (M1 vs PMd) sensitivity and robustness to window, binning, and dimensionality choices.
    - Candidate estimands: Cross-context readout generalization index: performance of a one-context-fit endpoint/movement readout applied to the other context, relative to within-context performance. Cross-context representational-geometry correlation: correlation of endpoint RDMs (or aligned subspace overlap) between straight and curved contexts, above kinematic and shuffle baselines. Shared-vs-separate subspace model comparison: relative fit of a single shared endpoint subspace against per-context subspaces.
    - Validation strategy: Leakage-safe, dependence-aware validation: leave-one-endpoint-out and
    - leave-one-condition-out folds for cross-context transfer, trial bootstrap for
    - confidence intervals, and a synthetic method-recovery probe on simulated
    - shared-geometry vs separate-code populations to confirm the test discriminates the
    - two before touching the real comparison. No target outcomes are inspected to tune
    - choices; decision rules are prespecified.
    - Split strategy: Cross-context folds defined by context and endpoint so that alignment is always fit and tested on disjoint trials; within-context baselines use nested trial folds.
    - Diagnostics: Curvature-index separation and endpoint coverage per context. Per-unit rate/quality and per-condition spike coverage. Missing-data and kinematic-gap checks; stability across windows and dimensionalities.
    - Negative controls: Shuffled context labels (destroys any true straight/curved distinction). A scientifically irrelevant contrast (e.g., trial-index halves or eye-position-only readout) that should show no genuine cross-context geometric reuse.
    - Positive controls: Within-context endpoint readout should recover endpoint structure well. A documented structural signal (e.g., movement-direction tuning) should be recoverable within each context.
    - Alternative explanations: Cross-context prediction driven by shared hand/cursor kinematics rather than conserved neural organization (addressed by the matched-kinematic baseline and endpoint matching). Separate context-specific codes carrying similar decodable information without shared geometry (addressed by the transfer-vs-within-context and shared-vs-separate-subspace comparisons). Apparent invariance from overly coarse context classification (addressed by curvature validation). Sampling or coverage imbalance across small per-condition cells.
    - Predicted result patterns: Support for reuse: cross-context transfer approaches within-context performance and endpoint RDMs/subspaces are shared, exceeding matched-kinematic and shuffle baselines. Against reuse: within-context readouts are accurate but cross-context transfer collapses toward baseline and a shared subspace fits far worse than per-context subspaces, indicating context-specific codes.
    - Claim ceiling: predictive
    - Interpretation limits: Single subject and single session; observational, not experimentally manipulated neural organization. Small per-condition trial counts limit precision; results are provisional planning targets, not scientific outcomes. Geometry is inferred; no causal or mechanistic claim is licensed.
    - Resource estimate: Modest: fits in memory (142 units, 100 trials, 1 kHz kinematics); standard population-geometry and cross-validated decoding tooling; hours of compute including bootstrap and the synthetic recovery probe.
    - Why this serves the question: The plan preserves the variant's central phenomenon (conserved task-relevant
    - geometry across straight and curved reaches supporting cross-context prediction)
    - and its discriminating observation (one-context representation predicts the other
    - beyond matched kinematics and generic baselines), while explicitly separating
    - shared relational geometry from separate context-specific codes with similar
    - information, as the Owner required. The endpoint-matched design and behavioral
    - curvature validation guard against the forbidden kinematic-confound and
    - coarse-classification reinterpretations.
    - Unresolved planning decisions: Prespecified movement window and geometry estimator to be locked before execution.
  - What would support or weaken it: A positive result would support reusable population organization across trajectory contexts. A negative result would favor context-specific organization or stronger dependence on trajectory-specific inputs. A null result would leave open whether weak transfer reflects genuine remapping or inadequate representational estimation.

## Competing Explanations And Controls

Competing explanations that must remain visible, by variant: Variant 1: Cross-context prediction is driven by shared hand or cursor kinematics rather than conserved neural organization. Apparent invariance arises from an overly coarse trajectory classification. Separate context-specific codes contain similar information without sharing geometry.

## Outcome Meanings

Possible outcome meanings, by variant: Variant 1: A positive result would support reusable population organization across trajectory contexts. A negative result would favor context-specific organization or stronger dependence on trajectory-specific inputs. A null result would leave open whether weak transfer reflects genuine remapping or inadequate representational estimation.

## Planning Status and Limits

This accepted plan is a completed planning outcome under automated independent review. Optional post-hoc human review may be imported later. It remains planning-only and does not authorize a downstream bridge or execution or claim scientific results.

- Dataset statements are labeled `unverified`; planner-authored locators or digests alone do not verify an observation.
- Dataset grounding here reached dataset schema and metadata inspection; it includes no scientific-result values or execution outputs.
- A separate bridge approval is still required before downstream execution artifacts.
