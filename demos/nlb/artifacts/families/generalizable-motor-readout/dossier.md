> ⚠️ Data basis: this family's open gap / key claims rest on ABSTRACT-ONLY literature (full text was not available to this system). The questions are literature-motivated but NOT fulltext-verified; a domain expert should confirm against primary sources.

# Generalizable readout across trajectory contexts and cortical populations

This is a development planning dossier. It is planning-only and does not report scientific results.
Dataset grounding level: `sample_inspected`.
Dataset claim status: `unverified`.

## Question Family

Separates two forms of generalization: transfer between straight and curved behavior and transfer between PMd and M1 population organization.

## Scientific Motivation

A readout may succeed because it captures reusable motor structure or because it exploits context- or population-specific associations. Generalization failures can therefore reveal scientific boundaries, but they must not be treated as proof of distinct mechanisms.

## Dataset Leverage

Dataset claim status is unverified; observed-depth label is sample_inspected. Dataset leverage remains a planning hypothesis, by variant: Variant 1: Straight and curved reach trajectories may support later planning of cross-context predictive evaluation. Variant 2: The two named cortical regions and concurrent reach measurements may support a later region-stratified predictive comparison after metadata validation. No scientific-result generation was performed.

## Variant Plans

- Variant 1 (Cross-trajectory generalization test): Does a neural representation associated with reach trajectory generalize between straight and curved paths, and what does asymmetric transfer imply about shared versus context-specific motor structure?
  - Distinguishing test: This variant transfers between behavioral contexts within a neural population; it does not test whether regional population spaces are mutually readable. The discriminating observation is Bidirectional versus directional transfer, interpreted alongside within-condition prediction and geometry-sensitive alternatives, would distinguish common-scope, nested-scope, and context-specific accounts.
  - Planned analysis: Feasible. Straight vs curved contexts are cleanly defined by the Owner-accepted maze task condition
    - (32 straight vs 34 curved single-target trials), and continuous 2D hand kinematics plus 142 sorted
    - units support bidirectional cross-context decoding transfer with within-context baselines. Asymmetry
    - is interpreted, not collapsed, with unequal kinematic range modeled as an explicit alternative.
    - Constraints: small single-subject sample; claim ceiling associational; measured geometry used only
    - for validity/alternatives per the Owner ruling.
    - Refined question: Does a neural population readout of reach kinematics learned in one trajectory context (straight center-out vs curved maze reaches) generalize to the other, and is any transfer asymmetry consistent with shared reusable trajectory structure versus context-specific organization once unequal behavioral range and linear-readout limits are accounted for?
    - Population and scope: One rhesus macaque (Jenkins), single delayed center-out maze session; combined M1+PMd sorted units. Inference is within-subject across trials; no across-subject or across-session claim.
    - Data sources: Train NWB file: sorted-unit spike times (142 units), continuous 2D hand position/velocity, and the intervals/trials table providing num_barriers, num_targets, movement-event times, and train/val split.; Expected grain: Per-trial movement epochs aligned to move_onset_time; spikes binned per unit; kinematics sampled at ~1 ms.; Required variables: units/spike_times, units/id (region prefix), units/heldout, processing/behavior/hand_vel, hand_pos, timestamps, intervals/trials: num_barriers, num_targets, move_onset_time, go_cue_time, start_time, stop_time, split; Limitations: Small per-context sample (~32 straight, ~34 curved single-target trials). Only train-file behavior is available; NLB held-out test outcomes are excluded.
    - Unit of observation: A single reach trial (movement epoch) with its binned population activity and hand-kinematic trajectory.
    - Unit of inference: Reach trial within the single session; generalization is assessed across trials via resampling, not across subjects.
    - Hierarchy and dependence: Trials are nested within one session/subject and within target directions; resampling and evaluation will respect target-direction balance and avoid leakage between train and evaluation folds. Temporal autocorrelation within a trial is handled by trial-level (not sample-level) splitting.
    - Analysis strategy: Define contexts by the Owner-accepted maze task condition: num_barriers==0 (straight) vs num_barriers==9 (curved); core contrast on single-target trials, with distractor-target curved trials as a robustness set. Build a population decoder (prespecified family, e.g. regularized linear/Wiener or a fixed nonlinear baseline) mapping binned population activity to hand velocity/trajectory. Estimate directional transfer: train within straight and evaluate on curved and vice versa, reporting both directions alongside within-context cross-validated prediction. Quantify asymmetry as the difference between the two transfer directions, with resampled confidence intervals.
    - Candidate estimands: Within-context decoding accuracy (e.g. R^2 / correlation of predicted vs observed hand velocity) for straight and for curved. Cross-context transfer accuracy in each direction and the directional asymmetry contrast.
    - Validation strategy: Trial-level cross-validation/bootstrap within the train-file trials using the provided train/val split as an outer check; prespecified method-recovery on synthetic data with known shared vs context-specific structure to confirm the pipeline distinguishes them; no use of NLB held-out test outcomes.
    - Split strategy: Leakage-safe trial-level splits stratified by target direction; contexts never mixed within a single train/evaluate fold for the transfer estimand.
    - Diagnostics: Per-context trial and per-direction counts, kinematic range (speed/displacement distributions) by context. Decoder stability across resamples and sensitivity to bin width and epoch window. Comparison of linear vs a fixed nonlinear readout to separate scientific transfer from model-class limits.
    - Negative controls: Shuffled trial-label / time-reversed kinematics decoding to establish chance transfer.
    - Positive controls: Within-context decoding should recover reach kinematics well above chance, confirming decodable trajectory signal.
    - Alternative explanations: Asymmetry driven by unequal behavioral range/complexity (curved trials span wider kinematics) rather than representational structure. Linear readout missing shared nonlinear structure. Small-sample variance inflating apparent asymmetry.
    - Predicted result patterns: Reliable bidirectional transfer with symmetric accuracy would support reusable trajectory structure spanning contexts. Reliable within-context prediction with failed or strongly asymmetric transfer, surviving range and nonlinearity controls, would support a boundary on generalization.
    - Claim ceiling: associational
    - Interpretation limits: Decoding is a predictive method used to license an associational claim about representational generalization, not a causal or mechanistic claim. Single subject/session and small per-context counts preclude population-level generalization beyond this dataset. Transfer asymmetry is interpreted only after range and model-class alternatives are addressed; planning evidence is not a scientific result.
    - Resource estimate: Bounded: 100 train-file trials, 142 units; standard decoding and resampling on a single workstation; no large-scale compute.
    - Why this serves the question: It tests directional straight<->curved transfer with within-context baselines and treats asymmetry as informative, preserving the variant's intent while explicitly guarding the range and nonlinearity alternatives named in the intent invariant.
    - Unresolved planning decisions: Lock decoder family, validation/resampling scheme, bin width, and movement-epoch window before execution (Owner-required).
  - What would support or weaken it: Reliable bidirectional transfer would support a reusable representation spanning trajectory contexts. Reliable context-specific prediction with failed transfer would support a boundary on representational generalization, subject to nonlinear and sampling alternatives. Poor within-condition and cross-condition prediction would not adjudicate generalization and would instead question signal reliability or construct definition.
- Variant 2 (Cross-region compatibility and transfer test): Are trajectory-related population organizations in PMd and M1 related by a shared readout or transformation, or are their predictive relationships region-specific?
  - Distinguishing test: This variant contrasts PMd and M1 population organizations; trajectory-context transfer could succeed within each region while cross-region compatibility still fails, or vice versa. The discriminating observation is Comparison of common-readout, transformed-readout, and region-specific predictive relationships, with region-wise reliability checks, would distinguish compatible, transformed, and apparently separate organization.
  - Planned analysis: Feasible. PMd (72) and M1 (70) units are recorded simultaneously across the same trials, enabling
    - cross-region population alignment on shared reach conditions without matched units, and a comparison
    - of common-readout, transformed-readout, and region-specific predictive relationships with region-wise
    - reliability checks. Region assignment uses the documented unit-ID convention plus the +96 electrode
    - correction. Constraints: single session/subject; possible unequal sampling/signal quality across
    - regions modeled as an alternative; claim ceiling associational.
    - Refined question: Are trajectory-related population organizations in PMd and M1 related by a shared or simply transformed readout, or are their predictive relationships to reach behavior region-specific, once unequal sampling and signal quality across regions are accounted for?
    - Population and scope: One rhesus macaque (Jenkins), single session; PMd (72) and M1 (70) sorted units recorded simultaneously. Inference is within-subject across trials; no across-subject claim.
    - Data sources: Train NWB file: region-labeled sorted-unit spike times (PMd vs M1 via unit-ID convention), continuous 2D hand kinematics, and the trials table for reach conditions and movement timing; both regions share one timebase and the same trials.; Expected grain: Per-trial movement-epoch population activity separately for PMd and M1, aligned to the same trials and kinematics.; Required variables: units/spike_times, units/id (leading digit 1=PMd / 2=M1), units/heldout, units/electrodes (+96 M1 correction for cross-checks), general/extracellular_ephys/electrodes location/group_name, processing/behavior/hand_vel, hand_pos, timestamps, intervals/trials: num_barriers, num_targets, move_onset_time, start_time, stop_time, split; Limitations: Region assignment depends on the documented unit-ID convention plus the +96 electrode correction; unresolved metadata disagreement must be surfaced, not assumed away. Unit yield/quality equivalence across regions is not established and is modeled as an alternative.
    - Unit of observation: A single reach trial's region-specific population activity (PMd and M1 observed on the same trial).
    - Unit of inference: Reach trial within the single session; cross-region relationships assessed across trials via resampling.
    - Hierarchy and dependence: PMd and M1 observations are paired within trials (shared conditions), enabling within-trial alignment; trial-level resampling stratified by target direction handles dependence; region comparisons control for differing unit counts by subsampling/matched-dimensionality checks.
    - Analysis strategy: Extract per-trial movement-epoch population activity separately for PMd and M1; build region-specific low-dimensional latent trajectories tied to reach conditions. Test cross-region compatibility three ways: (a) a common (shared) readout mapping either region's activity to the same kinematic/latent target; (b) a transformed readout (learned linear/affine alignment, e.g. regression/CCA/Procrustes on shared trials); (c) region-specific readouts as the baseline. Compare compatible vs transformed vs region-specific accounts by held-out predictive performance and alignment quality, with region-wise reliability checks.
    - Candidate estimands: Within-region decoding/reconstruction accuracy for PMd and for M1 (reliability baselines). Cross-region alignment quality (e.g. canonical correlations / Procrustes residual) and cross-region predictive accuracy under shared vs transformed readouts.
    - Validation strategy: Trial-level cross-validation within train-file trials; permutation/null alignment (shuffled trial correspondence) to calibrate chance alignment; synthetic method-recovery with known shared vs transformed vs independent regional codes; no NLB held-out test outcomes used.
    - Split strategy: Leakage-safe trial-level splits stratified by target direction; alignment learned on training trials and evaluated on held-out trials.
    - Diagnostics: Per-region unit counts, firing-rate/SNR distributions, and effective dimensionality. Sensitivity of alignment to unit-count matching (subsample PMd to M1 size and vice versa). Held-in vs all-units sensitivity using the units/heldout flag.
    - Negative controls: Shuffled cross-region trial correspondence to establish chance alignment/compatibility.
    - Positive controls: Within-region decoding should recover reach kinematics above chance in both PMd and M1, confirming usable region-specific signal.
    - Alternative explanations: Apparent region specificity driven by unequal sampling/signal quality rather than genuine representational difference. Alignment inflated by shared task/condition structure rather than shared neural coordinates (addressed by permutation nulls). Low-dimensional common behavior making any two decoders look compatible.
    - Predicted result patterns: A reliable shared or simple transformed relationship surviving controls would support distributed PMd/M1 compatibility. Reliable within-region prediction with poor cross-region compatibility surviving sampling controls would support region-specific relationships.
    - Claim ceiling: associational
    - Interpretation limits: Cross-region alignment is an associational compatibility claim, not evidence of a shared mechanism or causal coupling. Single session/subject; region assignment and unit-count imbalance are handled but not eliminated. Planning evidence is not a scientific result.
    - Resource estimate: Bounded: 142 region-labeled units across 100 trials; standard latent-alignment and decoding with resampling on a single workstation.
    - Why this serves the question: It contrasts common-readout, transformed-readout, and region-specific accounts with region-wise reliability and sampling controls, preserving the variant's target contrast (PMd vs M1 compatibility) and its distinct sampling/metadata alternatives without collapsing into the trajectory-context question.
    - Unresolved planning decisions: Fix the alignment method (regression/CCA/Procrustes), latent dimensionality, and held-in vs all-units policy before execution.
  - What would support or weaken it: A reliable shared or simple transformed relationship would support distributed compatibility between PMd and M1 trajectory representations. Reliable within-region prediction with poor cross-region compatibility would support region-specific representational relationships. Unreliable within-region prediction or unmatched sensitivity would prevent interpretation of cross-region transfer.

## Competing Explanations And Controls

Competing explanations that must remain visible, by variant: Variant 1: Bidirectional transfer could reflect a shared trajectory representation across path types. Poor transfer could reflect genuinely context-specific organization. Asymmetric transfer could arise because one path class spans a broader behavioral range or because a linear readout misses shared nonlinear structure. Variant 2: A shared readout could indicate compatible distributed trajectory structure across PMd and M1. A systematic transformation could indicate related representations with distinct regional coordinates. Failed transfer could reflect genuine regional specificity or unequal sampling and signal quality.

## Outcome Meanings

Possible outcome meanings, by variant: Variant 1: Reliable bidirectional transfer would support a reusable representation spanning trajectory contexts. Reliable context-specific prediction with failed transfer would support a boundary on representational generalization, subject to nonlinear and sampling alternatives. Poor within-condition and cross-condition prediction would not adjudicate generalization and would instead question signal reliability or construct definition. Variant 2: A reliable shared or simple transformed relationship would support distributed compatibility between PMd and M1 trajectory representations. Reliable within-region prediction with poor cross-region compatibility would support region-specific representational relationships. Unreliable within-region prediction or unmatched sensitivity would prevent interpretation of cross-region transfer.

## Planning Status and Limits

This accepted plan is a completed planning outcome under automated independent review. Optional post-hoc human review may be imported later. It remains planning-only and does not authorize a downstream bridge or execution or claim scientific results.

- Dataset statements are labeled `unverified`; planner-authored locators or digests alone do not verify an observation.
- Dataset grounding here reached bounded inspection of dataset samples; it includes no scientific-result values or execution outputs.
- A separate bridge approval is still required before downstream execution artifacts.
