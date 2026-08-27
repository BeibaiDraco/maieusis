> ⚠️ Data basis: this family's open gap / key claims rest on ABSTRACT-ONLY literature (full text was not available to this system). The questions are literature-motivated but NOT fulltext-verified; a domain expert should confirm against primary sources.

# Context-dependent balance of autonomous and input-linked motor dynamics

This is a development planning dossier. It is planning-only and does not report scientific results.
Dataset grounding level: `sample_inspected`.
Dataset claim status: `unverified`.

## Question Family

Tests whether delayed-reach population dynamics retain a common autonomous-like organization or become more input-linked when trajectory demands change, while keeping preparatory and execution-period interpretations separate.

## Scientific Motivation

Low-dimensional reach dynamics can be consistent with internally organized evolution, but trajectory constraints and behavioral feedback may also shape the observed activity. Straight and curved reaches offer a proposal-stage contrast without making either account uniquely identifiable from geometry alone.

## Dataset Leverage

Dataset claim status is unverified; observed-depth label is sample_inspected. Dataset leverage remains a planning hypothesis, by variant: Variant 1: If the described delayed-reaching release permits preparation periods, straight and curved trajectories, and relevant behavioral properties to be distinguished, it may support a population-level comparison of shared correspondence and curvature-selective future-path information. Exact coverage and identifiability remain for later verification. Variant 2: Concurrent spiking, hand, cursor, and eye measurements may support later planning of an associational test contrasting straight and curved execution. No scientific-result generation was performed.

## Variant Plans

- Variant 1 (Preparation-focused test of whether reusable population organization coexists with curvature-selective prospective path specification): During movement preparation, do straight and curved reaches share a population-level preparatory organization with superimposed curvature-selective components that prospectively specify the future path, or is preparatory organization fully condition-general once covarying movement demands are separated?
  - Distinguishing test: This variant concerns pre-movement population correspondence and the prospective meaning of curvature-selective components. Unlike the execution sibling, it does not test associations between ongoing behavior and neural evolution or interpret those associations through the autonomous-versus-input-linked tension. The discriminating observation is The central observation would be a reproducible population-level correspondence between preparatory states for straight and curved reaches—defined as a cross-condition mapping that preserves their relative population-state organization—together with a curvature-selective component that carries prospective information about future path variation beyond binary condition separability. Attribution to intended curvature would require that this component remain distinguishable, where the data permit, from reach direction, endpoint, duration, speed, muscle or kinetic demand, and online-control requirements. Mere condition separation, dimensionality differences, or uniform state shifts would not by themselves discriminate curvature specification from learned task structure, adaptation-like reassociation, or motor memory.
  - Planned analysis: Feasible as a predictive-ceiling analysis: estimate pre-movement population states in the
    - target-on-to-go-cue window, establish cross-condition population correspondence between straight
    - and curved preparatory states (not assumed linear), and test whether a curvature-selective
    - preparatory component predicts subsequently measured continuous hand-path curvature beyond binary
    - maze-condition separability, while accounting for designed condition, direction, endpoint,
    - duration, speed and kinetic-demand covariates where the data permit. Real limitations: ~11
    - trials/maze_id and 32 straight / 68 curved trials constrain covariate separation and graded
    - resolution; a population-dynamics executor skill must be implemented.
    - Refined question: During movement preparation, do straight and curved delayed reaches share a population-level
    - preparatory organization (a cross-condition mapping that preserves relative population-state
    - structure) onto which a curvature-selective component is superimposed that prospectively
    - predicts subsequently measured hand-path curvature (realized future path) beyond binary
    - maze-condition separability, or is preparatory organization condition-general once designed
    - condition and covarying movement demands are accounted for?
    - Population and scope: Proposal-stage population scope, kept explicit per the Owner ruling: sorted-unit spiking from
    - one macaque (Jenkins), one session, spanning M1 and PMd. Primary analysis pools held-in units
    - across regions with region assignment via the documented unit-ID leading-digit rule plus the M1
    - +96 electrode-row correction, with region-stratified sensitivity checks. No dataset-specific
    - generalization beyond this subject/session is claimed.
    - Data sources: Train NWB file trials table (event times, maze/barrier condition, target/barrier
    - geometry), units table (held-in sorted-unit spike_times with region-identifying IDs), and
    - behavior module hand_pos used to compute the subsequently measured hand-path curvature
    - outcome.
    - ; Expected grain: Per-trial spike times per unit; per-trial event times; ~1 kHz behavioral samples per trial.; Required variables: trials.target_on_time, trials.go_cue_time, trials.move_onset_time, trials.num_barriers, trials.maze_id, trials.trial_version, trials.target_pos, trials.barrier_pos, units.spike_times, units.heldout, units.electrodes, behavior.hand_pos; Limitations: Small single-session release (~11 trials/maze_id; 32 straight, 68 curved) limits covariate separation and graded-curvature resolution. Region-stratified claims require the documented M1 +96 electrode correction; some trials have very short delays and must be screened.
    - Unit of observation: A single delayed-reach trial's preparatory population state (binned spike counts over the pre-movement window).
    - Unit of inference: The trial (with condition/covariate structure); inference is over trials within this single subject/session.
    - Hierarchy and dependence: Trials are nested within maze_id conditions and within one session. Dependence is handled by
    - trial-level cross-validation and permutation that respect condition blocks, avoiding leakage of
    - the same trial across preparatory-state estimation and curvature prediction, and by reporting
    - maze_id-clustered variability rather than treating time bins as independent.
    - Analysis strategy: Define a pre-movement preparation window per trial (target_on_time to go_cue_time, with a prespecified minimum-delay inclusion threshold) and bin held-in population spike counts within it. Estimate low-dimensional preparatory population states (e.g. PCA / factor-style latent estimation with cross-validated dimensionality) separately and jointly for straight and curved conditions. Establish cross-condition population correspondence via alignment (e.g. cross-condition subspace/Procrustes or nonlinear mapping) that preserves relative population-state organization, explicitly not assuming linearity, and quantify shared-versus-selective structure. Compute the authoritative realized-path outcome: continuous measured hand-path curvature (max lateral deviation and integrated curvature of the executed hand trajectory) per trial. Test whether a curvature-selective preparatory component predicts the graded measured curvature beyond binary maze-condition separability, using nested cross-validated regression/decoding that includes designed condition and movement-demand covariates (direction, endpoint, duration, speed, kinetic-demand proxies) as competitors/controls, where the data permit.
    - Candidate estimands: Cross-condition population-correspondence score (fraction of preparatory-state structure preserved under the straight-to-curved mapping) at the population level. Incremental predictive information about graded measured hand-path curvature carried by the curvature-selective preparatory component beyond the binary maze condition and beyond direction/endpoint/speed/duration covariates.
    - Validation strategy: Nested, trial-level cross-validation with condition-aware folds; permutation/label-shuffle nulls
    - for the correspondence and prospective-prediction estimands; method-recovery on synthetic
    - populations with known shared-plus-selective structure to confirm the pipeline can recover
    - prospective curvature information when present and reject it when absent.
    - Split strategy: Leakage-safe trial-level splits; the trial contributing a preparatory state never appears in both training and test for its own curvature prediction; internal train/val split respected.
    - Diagnostics: Per-condition trial counts, held-in unit counts, and preparation-window coverage/missingness. Cross-validated dimensionality stability and correspondence-score stability under resampling. Covariate-balance and collinearity diagnostics between measured curvature and direction/endpoint/speed/duration.
    - Negative controls: Shuffle measured-curvature labels across trials within condition; prospective-prediction estimand should collapse to chance. Predict a scientifically irrelevant/post-hoc-permuted target from the preparatory component as a null.
    - Positive controls: Recover known coarse reach direction/target identity from preparatory states (expected to be decodable), confirming the population signal and pipeline sensitivity.
    - Alternative explanations: Condition separation reflecting learned task structure, adaptation-like reassociation, or uniform memory-related state shifts rather than prospective curvature specification. Apparent curvature selectivity driven by reach direction, endpoint, duration, speed, muscle/kinetic demand, or anticipated online-control requirements. Apparent condition-generality due to insufficiently distinct demands, limited trials, or failure to capture nonlinear correspondence.
    - Predicted result patterns: Support: robust cross-condition correspondence AND a curvature-selective component that predicts graded measured curvature beyond binary condition and covariates. Weaken: robust correspondence but no curvature-selective prospective information once covariates are accounted for, favoring condition-general preparation.
    - Claim ceiling: predictive
    - Interpretation limits: Prospective interpretation is pre-movement structure predicting subsequently measured path geometry; it is not causal and not a demonstration that preparation controls the path. Designed maze condition is not equated with realized curvature; a binary barrier-count effect is insufficient evidence of prospective path specification. Small single-subject/session data cap covariate separation and generalization; planning evidence is not a scientific result.
    - Resource estimate: Bounded: latent estimation, alignment, and cross-validated regression over 100 trials x ~107 units; modest compute, feasible on a single machine.
    - Why this serves the question: The plan preserves the variant intent by testing coexistence of a shared preparatory
    - organization and a curvature-selective component that prospectively predicts realized future
    - path, using the Owner-authorized measured-curvature operationalization, keeping it distinct from
    - binary maze decoding and from the execution-period question, and controlling the covariates the
    - invariant names, within the honest limits of the release.
    - Required new skills: A population-dynamics executor skill: windowed spike binning, cross-validated latent-state and cross-condition alignment estimation, curvature computation from hand_pos, and permutation-based prospective-prediction inference with region stratification.
    - Unresolved planning decisions: Final preparation-window bounds, minimum-delay threshold, and held-in unit / region-stratification rules.
  - What would support or weaken it: Evidence for both preserved cross-condition population correspondence and curvature-selective prospective path information would support a compositional account in which reusable preparation coexists with path-specific state formation; neither component would exclude the other. Robust population-level correspondence without detectable curvature-selective future-path information, despite adequate distinction of relevant covariates, would favor a fully condition-general preparatory organization for this contrast and constrain claims that curvature shapes preparation before movement. Unstable correspondence, weak curvature-selective estimates, or condition separation that lacks prospective path information or cannot be distinguished from behavioral demands and learned task structure would leave the curvature-specific interpretation unresolved rather than favoring either a wholly shared or compositional organization.
- Variant 2 (Execution-focused test of autonomous-like versus input-linked dynamics): During reach execution, are curved-path population dynamics disproportionately associated with ongoing behavioral input relative to straight-path dynamics?
  - Distinguishing test: This variant targets execution-period associations with ongoing behavior and interprets curvature effects through the autonomy-input tension rather than preparatory-state specificity. The discriminating observation is The accounts would be differentiated by whether condition-specific neural evolution is preferentially associated with time-varying behavioral deviations during curved reaches after accounting for broad trajectory structure, versus remaining comparably organized across conditions.
  - Planned analysis: Feasible as an associational-ceiling analysis: form time-resolved behavioral-deviation
    - regressors (hand position/velocity deviations from a per-condition broad trajectory template) at
    - the ~1 kHz behavioral resolution and test whether condition-specific neural evolution is
    - preferentially associated with these deviations during curved relative to straight reaches, after
    - accounting for broad trajectory structure and movement-duration/kinematic-complexity confounds.
    - Predictive/associational language only; no causal-feedback inference. Real limitations: small
    - trial count, duration/complexity confounds, and the competing autonomous-generator explanation;
    - a population-dynamics executor skill must be implemented.
    - Refined question: During reach execution, is condition-specific neural population evolution preferentially
    - associated with time-varying behavioral deviations during curved reaches relative to straight
    - reaches, after accounting for broad trajectory structure and movement-duration/kinematic
    - confounds, at an associational level?
    - Population and scope: Proposal-stage population scope kept explicit: sorted-unit spiking from one macaque (Jenkins),
    - one session, M1 and PMd combined (held-in units, documented region correction) with
    - region-stratified sensitivity. No generalization beyond this subject/session is claimed.
    - Data sources: Train NWB file units table (held-in spike_times) and behavior module time series (hand_pos,
    - hand_vel, cursor_pos, eye_pos) over the execution window, with trials-table event times and
    - maze/barrier condition labels.
    - ; Expected grain: Per-trial spike times per unit; ~1 kHz multi-stream behavioral samples per trial; per-trial event times and condition labels.; Required variables: trials.move_onset_time, trials.stop_time, trials.num_barriers, trials.maze_id, units.spike_times, units.heldout, units.electrodes, behavior.hand_pos, behavior.hand_vel, behavior.cursor_pos; Limitations: Small trial count (32 straight / 68 curved) limits power; unequal duration/complexity between conditions is a confound requiring explicit handling. Association only; the dataset cannot distinguish input-driven from autonomously-generated correlated trajectories on its own.
    - Unit of observation: A time bin within a single reach-execution trial (population activity paired with concurrent behavioral state).
    - Unit of inference: The trial (with condition structure); inference over trials within this single subject/session.
    - Hierarchy and dependence: Time bins are nested within trials, trials within maze_id conditions and one session. Temporal
    - autocorrelation and within-trial dependence are handled via trial-level cross-validation,
    - block/circular-shift permutation nulls that preserve autocorrelation, and clustering of variance
    - by trial and condition rather than by bin.
    - Analysis strategy: Define the execution window per trial (move_onset_time to stop_time) and bin held-in population activity at a resolution matched to the behavioral streams. Build a per-condition broad trajectory template and compute time-varying behavioral deviations (hand position/velocity residuals) from it as the ongoing-input regressor. Model the association between condition-specific neural evolution and concurrent behavioral deviations (e.g. time-resolved encoding/decoding or state-space regression), separately for straight and curved reaches. Compare the strength of neural-to-behavioral-deviation association between curved and straight conditions after regressing out broad trajectory structure and matching/covarying movement duration and kinematic complexity.
    - Candidate estimands: Difference (curved minus straight) in cross-validated neural-to-behavioral-deviation association strength during execution, after accounting for broad trajectory structure and duration/complexity.
    - Validation strategy: Trial-level cross-validation with condition-aware folds; autocorrelation-preserving permutation
    - nulls (block/circular shift) for the association estimand; duration-matched subsampling as a
    - robustness check; synthetic method-recovery contrasting an input-linked generator against an
    - autonomous generator with correlated behavior to confirm the estimand separates them only to the
    - extent the data allow.
    - Split strategy: Leakage-safe trial-level splits; no bins from a test trial appear in training; internal train/val split respected.
    - Diagnostics: Per-condition trial counts, execution-window durations, and behavioral-stream completeness. Duration/kinematic-complexity balance between conditions and sensitivity of the estimand to duration matching. Stability of the association estimand under resampling and bin-width choices.
    - Negative controls: Shuffle behavioral-deviation regressors across trials within condition; the association estimand should collapse to chance. Time-reverse or phase-randomize the behavioral deviation as an autocorrelation-matched null.
    - Positive controls: Recover the known strong association between population activity and gross hand velocity/direction during movement, confirming pipeline sensitivity.
    - Alternative explanations: An autonomous trajectory generator producing richer, correlated neural and behavioral trajectories in curved reaches without online input driving neural evolution. Unequal movement duration or kinematic complexity between conditions rather than a different dynamical regime.
    - Predicted result patterns: Support: selectively stronger neural-to-behavioral-deviation association in curved than straight reaches after controls, consistent with an input-linked interpretation. Weaken: comparable association across conditions, favoring a common internally organized account.
    - Claim ceiling: associational
    - Interpretation limits: Associational/predictive only; no causal-feedback or online-input claim follows from curvature-related association alone. Correlation under an autonomous generator remains an admitted competing explanation the dataset cannot fully exclude. Small single-subject/session data cap power and generalization; planning evidence is not a scientific result.
    - Resource estimate: Bounded: time-resolved regression/decoding over 100 trials x ~107 units x ~1 s execution windows; modest compute, single-machine feasible.
    - Why this serves the question: The plan preserves the variant intent by asking whether execution-period neural evolution is
    - preferentially associated with ongoing behavioral deviations in curved reaches, interpreted
    - through the autonomy-input tension at an associational ceiling, kept separate from the
    - preparatory-state question, with the confounds the invariant names explicitly controlled.
    - Required new skills: A population-dynamics executor skill: matched neural/behavioral binning, per-condition trajectory-template and deviation construction, time-resolved association estimation, and autocorrelation-preserving permutation inference with duration matching and region stratification.
    - Unresolved planning decisions: Final execution-window binning resolution, trajectory-template definition, and duration-matching scheme.
  - What would support or weaken it: Selective association with ongoing behavioral deviations in curved reaches would support an input-linked interpretation for trajectory adjustment, at an associational claim level. Comparable organization with little selective association would favor a common internally organized account across trajectory demands. Indeterminate condition differences would leave the autonomy-input tension unresolved and motivate better separation of planned geometry, movement complexity, and feedback proxies.

## Competing Explanations And Controls

Competing explanations that must remain visible, by variant: Variant 1: Curvature-selective preparatory structure could prospectively specify future path geometry while coexisting with a reusable shared population component. Apparent curvature selectivity could instead reflect reach direction, endpoint, movement duration, speed, muscle or kinetic demand, or anticipated online-control requirements. Condition separation could reflect learned task structure or contextual labeling without encoding graded or within-condition variation in the future path. Condition-specific geometry could reflect adaptation-like reassociation or motor-memory-related state shifts rather than curvature-constrained preparation. An apparently condition-general organization could result from insufficiently distinct demands, measurement limitations, or failure to capture nonlinear population correspondence. Variant 2: Stronger behavioral association during curved reaches could indicate increased use of ongoing sensory or motor input. The same pattern could arise because an autonomous trajectory generator produces richer neural and behavioral trajectories that are correlated without online input driving neural evolution. Differences could reflect unequal movement duration or kinematic complexity rather than a different dynamical regime.

## Outcome Meanings

Possible outcome meanings, by variant: Variant 1: Evidence for both preserved cross-condition population correspondence and curvature-selective prospective path information would support a compositional account in which reusable preparation coexists with path-specific state formation; neither component would exclude the other. Robust population-level correspondence without detectable curvature-selective future-path information, despite adequate distinction of relevant covariates, would favor a fully condition-general preparatory organization for this contrast and constrain claims that curvature shapes preparation before movement. Unstable correspondence, weak curvature-selective estimates, or condition separation that lacks prospective path information or cannot be distinguished from behavioral demands and learned task structure would leave the curvature-specific interpretation unresolved rather than favoring either a wholly shared or compositional organization. Variant 2: Selective association with ongoing behavioral deviations in curved reaches would support an input-linked interpretation for trajectory adjustment, at an associational claim level. Comparable organization with little selective association would favor a common internally organized account across trajectory demands. Indeterminate condition differences would leave the autonomy-input tension unresolved and motivate better separation of planned geometry, movement complexity, and feedback proxies.

## Planning Status and Limits

This accepted plan is a completed planning outcome under automated independent review. Optional post-hoc human review may be imported later. It remains planning-only and does not authorize a downstream bridge or execution or claim scientific results.

- Dataset statements are labeled `unverified`; planner-authored locators or digests alone do not verify an observation.
- Dataset grounding here reached bounded inspection of dataset samples; it includes no scientific-result values or execution outputs.
- A separate bridge approval is still required before downstream execution artifacts.
