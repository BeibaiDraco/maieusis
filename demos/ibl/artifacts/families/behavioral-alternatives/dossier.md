# Embodied and internal-state explanations of apparent noise correlations

Asks whether apparently unexplained neural covariance is better understood as rich movement-related structure or as non-motor internal-state variation.

## Scientific tension

Residual correlations associated with choice and response time may reflect decision computation, but conventional controls may omit multidimensional behavior or internal state. Richer alternatives can either explain away a decision interpretation or reveal scientifically meaningful embodied structure.

## Question variants

### Rich embodied-behavior branch

How much apparently choice- or response-time-related shared neural variability is predictively accounted for by multidimensional pose and movement structure beyond simpler behavioral summaries?

Why it matters: The result would refine interpretation of brain-wide noise correlations and prevent residual movement structure from being mislabeled as latent decision computation.

Distinctive focus: This branch treats multidimensional pose and movement as the principal alternative and asks how they revise decision-related covariance interpretations.

Conditional dataset leverage: Synchronized spiking, pose, choices, and response times may allow a later planner to compare rich embodied prediction with simpler behavioral alternatives.

Discriminating observation: Rich pose structure would predict held-out shared neural variability beyond simpler behavioral summaries and substantially alter the apparent choice- or response-time association.

Competing explanations:
- Neural covariance reflects latent decision formation that happens to correlate with movement.
- A simpler global arousal or engagement variable explains both pose and neural activity.
- Pose prediction is inflated by temporal leakage or shared task timing.

### Residual internal-state branch

After accounting for measured movement, does a residual shared-variability component predict response-time and choice-history effects consistent with a non-motor internal state?

Why it matters: This branch tests whether richer movement adjustment reveals rather than eliminates a predictive internal-state signal.

Distinctive focus: This branch targets the non-motor residual after rich movement adjustment and uses history and response-time prediction as its discriminator; the sibling makes embodied structure the target explanation.

Conditional dataset leverage: Behavior, trial history, response times, pose, and neural activity may permit later planning of nested predictive comparisons.

Discriminating observation: A reliable residual covariance component would predict held-out response-time or history-dependent choice variation after rich pose adjustment and would not be reducible to generic recording drift.

Competing explanations:
- The residual is unmeasured movement, posture, or physiological state rather than a decision-related internal state.
- Trial-history associations arise from sensory or reward contingencies.
- Residual covariance reflects recording drift or spike-sorting instability.

## What the possible outcomes would mean

### Rich embodied-behavior branch

- Positive pattern: Would support an embodied interpretation of a substantial component of apparent neural noise while identifying behavior-related activity as scientifically structured.
- Negative pattern: Would strengthen the case that measured movement is not the principal explanation for the target covariance.
- Null or ambiguous pattern: Would leave ambiguity because weak prediction could reflect absent embodied structure or incomplete and uneven pose measurement.

### Residual internal-state branch

- Positive pattern: Would support a predictive distinction between embodied behavior and a non-motor internal-state component of shared variability.
- Negative pattern: Would favor embodied, sensory, or measurement explanations over a separable internal-state account.
- Null or ambiguous pattern: Would leave the internal-state construct unresolved because absence of residual prediction may reflect inadequate measurement of either neural covariance or alternatives.

## Dataset evidence status

- Claim status: `unverified`
- Planner inspection records were retained, but their locators and digests do not by themselves prove the stated observations.
- Dataset leverage statements above remain hypotheses unless a retained, host-bound source supports them.

## Current disposition

- Shortlist: `shortlisted`
- Planning: `not_reached`
- Closure: `degraded`
- Authority: `provisional`
- Status note: Returned planning material could not be fully validated; a readable family dossier was retained with a validation warning.

## Retained products

- audit_sidecar — `provisional`, digest `690c32fdd6db`
- diagnostic — `provisional`, digest `ffd2697baa65`
- inspection_evidence — `provisional`, digest `ccb714e0d080`
- inspection_evidence — `provisional`, digest `1acae608ac73`
- inspection_evidence — `provisional`, digest `94ec45714d7d`
- inspection_evidence — `provisional`, digest `f2b20ed7fa2a`
- plan — `provisional`, digest `0ccbef650165`
- plan — `agent_reviewed`, digest `0e8615f31922`
- plan — `agent_reviewed`, digest `1872d96f53e5`
- planner_handoff — `unknown`, digest `8d901d158e06`
- planner_import_manifest — `unknown`, digest `def5a5c4e7ad`
- planner_run_record — `unknown`, digest `2a4f96a0703f`
- planner_validation_report — `unknown`, digest `b03242c57a95`

## Retained planning and review disposition

- The returned planning material could not be fully validated. The scientific question and any safely retained products remain available with a validation warning.

## Safely retained planner draft

The planner returned a complete-looking draft, but it did not pass strict typed validation and has not received scientific review. The scientific content below is a sanitized inspection copy: provenance identifiers are omitted, and no accepted-plan authority is implied.

### Family summary

The linked BWM behavior and ephys products credibly support both conditional, held-out variants. Execution requires a capability to decode the compressed synchronized pose and spike shards and fit leakage-safe hierarchical latent models.

- Planner assessment label: `serves_question`

### Variant 1

- Planner-stated disposition: `accepted_requires_new_skill`
- Planner summary: Time-resolved pose, arousal-proxy, wheel, task, trial, and spike surfaces permit the intended held-out incremental-prediction and attenuation plan, subject to a new shard-decoding and joint covariance-model executor capability.

#### Refined question

Does held-out, time-resolved ongoing pose add prediction of a prespecified trial-level shared neural covariance component beyond task, response-execution, wheel, coarse movement, and pupil covariates, and does that addition attenuate its association with choice or response time?

#### Population and scope

BWM sessions having an ephys insertion, included trials, usable spike data, and prespecified synchronized pose coverage; analyses will report coverage by session, insertion, camera, and keypoint rather than generalizing beyond eligible recordings.

#### Unit of observation

A held-out trial-level estimate of a shared cross-unit covariance component from prespecified non-overlapping neural time bins.

#### Unit of inference

Session/insertion clusters, with trial-level effects aggregated using cluster-aware uncertainty.

#### Hierarchy and dependence

Fit within-session/insertion neural representations; retain session and insertion intercepts or hierarchical partial pooling; block resampling and all uncertainty at session or insertion level, never treating time bins or units as independent biological replicates.

#### Validation strategy

Before target evaluation, verify decoder time alignment against shard metadata, recover known synthetic covariance under controlled simulated pose confounding, fit representation and regularization only on training folds, and freeze all feature windows and rank choices before held-out scoring.

#### Split strategy

Use contiguous blocked trial segments within session for temporal leakage control, with outer held-out session or insertion folds where coverage permits; keep all time bins from a trial and all fitted preprocessing within the relevant training partition.

#### Planner-stated claim ceiling (not yet schema-validated)

associational

#### Resource estimate

A later executor needs compressed-shard decoders, time synchronization, blocked cross-validation, regularized latent covariance modeling, and session-clustered resampling; storage can be streamed per insertion/session.

#### Why this plan serves the question

The plan preserves the variant's decisive contrast by distinguishing ongoing multidimensional pose from response execution and by testing incremental held-out prediction beyond explicit task, arousal, and coarse-movement controls.

#### Data sources

1. Behavior trial/event tables and synchronized semantic pose, pupil, and wheel shards joined by eid and trial timing.
   - Expected grain: Trial with time bins nested in session.
   - Required variables: choice and response timing; stimulus and task-event timing; wheel and movement summaries; camera keypoints, likelihoods, and pupil signals
   - Limitations: Pose coverage and camera view vary by session.
2. Per-insertion spike shards and unit-quality features joined through pid and eid.
   - Expected grain: Unit-by-time-bin observations nested in insertion and session.
   - Required variables: spike times and cluster assignments; unit drift and quality covariates
   - Limitations: Shared covariance must be estimated separately within compatible insertion/session groups.

#### Analysis strategy

- Define a stable shared-covariance estimand from training trials only, using residualized binned spike counts after task-event and mean-rate terms.
- Decode pose at native documented timestamps, align it to trial windows, and form prespecified ongoing versus response-linked blocks using event-time exclusions and temporal offsets.
- Compare blocked held-out prediction from a baseline containing task variables, choice and response-time nuisance terms for the covariance stage, wheel/coarse movement, response execution, pupil proxy, and quality covariates against the baseline plus regularized pose dynamics.
- Estimate the component's held-out association with choice or response time before and after the pose block; attribute attenuation only to the ongoing-pose block when it persists after response-linked exclusions.

#### Candidate estimands

- Blocked held-out difference in predictive log likelihood or squared-error loss for the shared-covariance component after adding ongoing pose.
- Cluster-aggregated change in the conditional association of the shared component with choice or response time after pose adjustment.

#### Diagnostics

- Camera/keypoint likelihood, missingness, and time-alignment coverage by fold.
- Covariance-component stability across neural bin widths, latent ranks, and recording segments.
- Collinearity and overlap between ongoing pose, pupil, wheel, task timing, and response-linked pose.

#### Negative controls

- Time-shift pose trajectories within recording segments while preserving their autocorrelation and refit the incremental-prediction comparison.
- Use post-outcome pose as a temporally invalid predictor for the pre-response covariance target to confirm that apparent effects are not generic feature capacity.

#### Positive controls

- Verify that response-linked wheel and pose features predict documented first-movement or response timing in training-only checks.

#### Alternative explanations

- Response preparation or execution rather than ongoing pose drives the apparent incremental prediction.
- Pupil-linked arousal, task timing, or coarse locomotion jointly influences pose and covariance.
- High-dimensional pose overfits through temporal leakage or recording-specific structure.
- Unit drift or measurement instability changes the covariance estimate.

#### Predicted result patterns

- Support for the embodied account requires reproducible held-out improvement from the ongoing-pose block and attenuation of the conditional choice or response-time association beyond the explicit baseline.
- No held-out incremental contribution, or contribution limited to response-linked blocks, weakens the measured ongoing-pose account.

#### Interpretation limits

- Attenuation after adjustment does not establish that pose causally generates neural covariance.
- Camera-view keypoints and pupil diameter are incomplete proxies for whole-body movement and arousal.

#### Required new skills

- Decode zip_semantic_shards_v2 pose and wheel arrays and blosc ephys spike shards without materializing the full dataset.
- Fit leakage-safe hierarchical shared-covariance prediction models with high-dimensional time-resolved pose.

#### Unresolved decisions

- The minimum usable camera/keypoint coverage and the primary neural bin window require prespecification before execution.

### Variant 2

- Planner-stated disposition: `accepted_requires_new_skill`
- Planner summary: Trial history, temporally extended movement/pose, behavioral outcomes, spikes, and unit-quality surfaces permit prospective residual-covariance tests with recording-stability sensitivity analyses, subject to the same new decoding and joint-model capability.

#### Refined question

Does a recording-stable residual shared neural covariance component prospectively improve held-out response-time and history-dependent choice prediction beyond trial history, behavioral latent state, temporally offset movement-related structure, recent neural activity proxies, and recording-quality alternatives?

#### Population and scope

BWM ephys sessions with included trials, usable spikes, and sufficient synchronized movement/pose coverage for the prespecified prospective windows; conclusions are limited to that eligible recording subset.

#### Unit of observation

An ordered trial with a pre-outcome residual shared-covariance score and prospective behavioral outcomes.

#### Unit of inference

Session/insertion clusters, with behavioral prediction assessed on blocked held-out trial segments and summarized across clusters.

#### Hierarchy and dependence

Construct neural residuals within insertion/session; model serial trial dependence explicitly; use session/insertion block resampling and cross-segment generalization rather than independent-trial inference.

#### Validation strategy

Verify prospective time ordering and decoder alignment, use synthetic method-recovery data with known movement, recurrent-state, and drift confounds, estimate behavioral latent states and neural residuals only in training partitions, and freeze model capacity before outer-fold scoring.

#### Split strategy

Use forward or contiguous blocked within-session folds that preserve trial order, with outer held-out recording segments and, where feasible, held-out sessions; prohibit features from the target or later trials.

#### Planner-stated claim ceiling (not yet schema-validated)

associational

#### Resource estimate

A later executor needs streamed shard decoding, prospective feature construction, nested blocked validation, behavioral latent-state fitting, residual covariance estimation, and cluster-aware stability analysis.

#### Why this plan serves the question

The plan retains the revision's source-discrimination requirement by demanding prospective incremental information after behavioral, movement, recurrent-activity, and recording-stability alternatives rather than labeling any residual covariance as internal state.

#### Data sources

1. Trial history, outcomes, response timing, task timing, wheel, movement states, and synchronized pose/pupil signals.
   - Expected grain: Ordered trial nested in session.
   - Required variables: choice, feedback, contrasts, and response time; prior-trial outcomes and task contingencies; temporally offset pose, wheel, movement, and pupil features
   - Limitations: Measured movement and arousal are incomplete.
2. Spike shards, unit identifiers, and unit-quality features for constructing residual covariance and recording-stability sensitivity covariates.
   - Expected grain: Trial-by-unit time bins nested in insertion and session.
   - Required variables: spike times and cluster assignments; unit drift, contamination, presence ratio, and firing-rate fields
   - Limitations: Quality metrics proxy, rather than exhaust, spike-sorting and recording instability.

#### Analysis strategy

- Estimate the residual covariance score using only neural activity preceding the prospective response-time or choice outcome and residualize task events and mean-rate structure in training folds.
- Build a baseline prospective model from prior outcomes, contrasts and task contingencies, trial history, behavioral latent-state summaries estimated on training data, temporally offset wheel/pose/pupil features, and recent neural-activity summaries.
- Compare blocked held-out response-time and history-dependent choice prediction with versus without the residual covariance score, holding all temporal windows strictly prospective.
- Test source discrimination by adding movement-linked neural dynamics, recent-activity/excitability proxies, and drift/quality covariates in prespecified blocks; require cross-segment stability for a separable non-motor interpretation.

#### Candidate estimands

- Blocked held-out incremental predictive performance of the residual covariance score for response time beyond the full baseline.
- Blocked held-out incremental predictive performance for history-dependent choice beyond prior outcomes, task history, behavioral latent-state, movement, and recent-neural predictors.
- Cross-recording-segment stability of the covariance coefficient and out-of-segment predictive contribution.

#### Diagnostics

- Outcome and covariate missingness by recording segment and pose availability.
- Autocorrelation, calibration, and residual serial dependence of prospective models.
- Coefficient and predictive-contribution stability across recording segments, unit-quality strata, latent ranks, and neural history windows.

#### Negative controls

- Circularly time-shift the residual covariance score within valid recording blocks relative to future outcomes.
- Use a post-outcome covariance score as an invalid prospective predictor.

#### Positive controls

- Confirm that prior feedback and task-history variables recover their expected temporal availability in the training-only behavioral baseline.
- Confirm that known recent neural activity summaries predict their own held-out near-future activity before testing behavioral prediction.

#### Alternative explanations

- Behavioral history or a fitted behavioral latent state reconstructs the apparent neural contribution.
- Temporally offset movement or movement-linked neural dynamics accounts for the score.
- Recent neural activity or recurrent excitability generates both covariance and future behavior.
- Drift, quality changes, or spike-sorting instability produces a slow covariance component.

#### Predicted result patterns

- Support for a separable non-motor predictive component requires incremental prospective prediction of both specified behavioral outcomes after all prespecified alternative blocks, plus stable cross-segment contribution.
- Selective loss after movement, recent-activity, behavioral-state, or quality controls instead favors that corresponding alternative explanation.

#### Interpretation limits

- Incremental prospective prediction is not evidence for a unitary causal internal state.
- A residual component can still reflect unmeasured movement, physiology, or recording artifacts.

#### Required new skills

- Decode and align the compressed behavior and spike shard formats in a streaming workflow.
- Fit prospective leakage-safe joint behavioral/neural latent models with segment-stability and quality sensitivity analyses.

#### Unresolved decisions

- Prespecify the behavioral latent-state model class, outcome links, neural history windows, and minimum segment length independently of held-out results.

## Limitations

Accepted planning and review artifacts were retained, but dossier closure failed before a public dossier could be produced.

## Diagnostics

- `infrastructure/family_development_incomplete`: Returned planning material could not be fully validated; a readable family dossier was retained with a validation warning. (details)
This page preserves the generated scientific question; it is not a scientific finding or downstream authorization.

## Next action

Inspect the run diagnostic and retained products before deciding whether to revise inputs or resume.
