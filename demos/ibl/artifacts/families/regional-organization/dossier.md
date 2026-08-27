# Regional organization of behaviorally relevant covariance geometry

Tests whether behaviorally relevant covariance follows a shared brain-wide geometry or consists of regionally distinct population solutions.

## Scientific tension

Decision and movement signals can be distributed across the brain, but distribution does not establish a common population mechanism. Similar behavior may be associated with a recurrent geometry across regions or with distinct local geometries.

## Question variants

### Shared brain-wide motif branch

Does a common covariance geometry aligned with sensory-to-choice progression recur across anatomically separated populations during decision formation?

Why it matters: A recurring geometry would offer a stronger population-level account of distributed decision signals than widespread detectability alone.

Distinctive focus: This branch tests cross-region recurrence and generalization of a common geometry; the sibling tests whether region-specific geometries carry distinct predictive relationships.

Conditional dataset leverage: Broad anatomical sampling under a standardized task may allow a later planner to compare representational relations across suitably sampled populations.

Discriminating observation: A geometry defined without pooling target populations would generalize across regions or recordings and retain similarity after comparison with task-timing, sensory, and movement alternatives.

Competing explanations:
- Common geometry is imposed by shared sensory and motor events rather than a shared decision organization.
- Geometry appears similar because of analysis choices or unequal sampling.
- Only a subset of interconnected regions shares the organization, making a brain-wide claim misleading.

### Region-specific solutions branch

Do anatomically distinct populations exhibit different covariance geometries whose associations with sensory evidence, choice, movement, or response time imply region-specific computational solutions?

Why it matters: Identifying structured regional heterogeneity would constrain claims that distributed decision signals instantiate one common mechanism.

Distinctive focus: This branch treats reproducible regional heterogeneity and differential task associations as the target, rather than cross-region recurrence of one geometry.

Conditional dataset leverage: Broad multisite neural and behavioral measurements may allow later planning of region-sensitive comparisons under a common task framework.

Discriminating observation: Regional geometries would differ reproducibly and show distinct held-out associations with sensory, choice, movement, or timing variables beyond what sampling-matched comparisons predict.

Competing explanations:
- Regional differences reflect unequal unit sampling or recording quality.
- Differences arise from varying sensory or movement mixtures rather than distinct population solutions.
- A common geometry is transformed by local readout or timing rather than replaced by region-specific mechanisms.

## What the possible outcomes would mean

### Shared brain-wide motif branch

- Positive pattern: Would support a descriptive or predictive common organizational motif for behaviorally relevant covariance.
- Negative pattern: Would weaken a shared brain-wide motif and favor regional specialization or heterogeneous solutions.
- Null or ambiguous pattern: Would leave recurrence unresolved if cross-population estimates are too uncertain or sensitive to sampling.

### Region-specific solutions branch

- Positive pattern: Would support a descriptive or predictive account of region-specific population solutions.
- Negative pattern: Would favor a common motif or indicate that regional distinctions do not organize behaviorally relevant covariance.
- Null or ambiguous pattern: Would leave specialization unresolved if observed differences fail to generalize or cannot be separated from sampling heterogeneity.

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

- audit_sidecar — `provisional`, digest `9fff645ad163`
- diagnostic — `provisional`, digest `6318e24c699f`
- inspection_evidence — `provisional`, digest `877508576cc3`
- inspection_evidence — `provisional`, digest `4d1d5601f70e`
- inspection_evidence — `provisional`, digest `5cef544147ad`
- plan — `provisional`, digest `0d217ef9c4cb`
- plan — `agent_reviewed`, digest `e22d3f4a30f9`
- plan — `agent_reviewed`, digest `6dd97aa31d5c`
- planner_handoff — `unknown`, digest `e12c698e3bc5`
- planner_import_manifest — `unknown`, digest `797fa9e34db1`
- planner_run_record — `unknown`, digest `5d5835bd4170`
- planner_validation_report — `unknown`, digest `158640b53d29`

## Retained planning and review disposition

- The returned planning material could not be fully validated. The scientific question and any safely retained products remain available with a validation warning.

## Safely retained planner draft

The planner returned a complete-looking draft, but it did not pass strict typed validation and has not received scientific review. The scientific content below is a sanitized inspection copy: provenance identifiers are omitted, and no accepted-plan authority is implied.

### Family summary

Both variants have a planning route in BWM ephys plus behavior metadata: trial-aligned spike trains can support recording-specific population geometry, and the documented task and movement variables can support prespecified adjustment and matching. Both require a new executor skill for decoded spike shards, leakage-safe cross-validation, and dependence-aware covariance geometry estimation.

- Planner assessment label: `serves_question`

### Variant 1

- Planner-stated disposition: `accepted_requires_new_skill`
- Planner summary: A cross-recording, independently estimated residual-covariance geometry plan is supported by unit-region metadata, trial timing and covariates, and insertion-sharded spike storage. Its claim is restricted to sampled, eligible populations and requires a new spike-shard and cross-validated geometry executor.

#### Refined question

Across eligible, anatomically labeled BWM recordings, do independently estimated residual-covariance-whitened distances among a prespecified sensory-to-choice state grid correspond and transfer to held-out recordings beyond matched task-variable alternatives?

#### Population and scope

Eligible quality-labeled units from independently recorded BWM insertions, with recurrence claims limited to the sampled regions and recordings that pass prespecified coverage and stability criteria.

#### Unit of observation

A trial-by-unit response vector in prespecified stimulus- and response-aligned windows.

#### Unit of inference

A held-out insertion or session, with higher-level resampling clustered by subject and laboratory where coverage permits.

#### Hierarchy and dependence

Estimate geometry within insertion only; block every split at the insertion/session level, never pool units to create a common latent space, and cluster uncertainty across repeated recordings from a subject or laboratory.

#### Validation strategy

Before target evaluation, use synthetic spike-count data with known shared and region-specific covariance structures to verify recovery, fold isolation, shrinkage behavior, and false-recurrence controls.

#### Split strategy

Outer leave-recording-out evaluation, grouped by session and with subject or laboratory blocked whenever sufficient coverage permits; all state selection, covariance estimation, and any alignment choice occur within training folds.

#### Planner-stated claim ceiling (not yet schema-validated)

descriptive

#### Resource estimate

A new executor should stream one insertion shard at a time and retain only fold-level sufficient statistics and redacted aggregate diagnostics; expected work is moderate-to-high because covariance estimation is repeated across recordings and resamples.

#### Why this plan serves the question

It retains the intended independently estimated, covariance-whitened cross-population contrast and makes recurrence depend on held-out correspondence beyond matched task-variable alternatives rather than distributed detectability.

#### Data sources

1. Insertion-sharded spike trains linked to unit anatomical labels and quality metadata.
   - Expected grain: Spike events and units nested within insertion, session, subject, laboratory, and Beryl region.
   - Required variables: pid; cluster_id; beryl_acronym; label; spike_times_delta_ticks; spike_clusters
   - Limitations: Spike decoding and trial alignment require a new executor capability.
2. Trial timing, stimulus, choice, reaction-time, and wheel-derived movement covariates joined on eid and trial_id.
   - Expected grain: Trial nested within session.
   - Required variables: contrastLeft; contrastRight; choice; stimOn_times; goCue_times; firstMovement_times; response_times; reaction_time; movement_time; movement_onset_time
   - Limitations: Wheel-derived covariates must be handled by an explicit complete-case or missingness-indicator rule.

#### Analysis strategy

- Define a finite state grid from signed contrast, choice, and a prespecified sensory-to-choice time bin; require balanced trial support in every retained state.
- Within each recording, fit cross-fitted nuisance models for sensory condition, trial time, choice, and movement-preparatory covariates, then estimate residual covariance from training folds using a prespecified shrinkage rule.
- Construct cross-validated Mahalanobis distances among state means within each recording using only that recording's residual covariance.
- Compare independently estimated distance matrices and evaluate transfer to held-out recordings against sensory-only, timing-only, choice-only, movement-only, and matched full-variable alternatives.

#### Candidate estimands

- Held-out recording-level correspondence between independently estimated whitened distance matrices.
- Incremental held-out prediction of a recording's distance structure by a training-recording geometry relative to matched task-variable alternatives.

#### Diagnostics

- Per-recording state coverage, retained-unit count, trial count, covariance conditioning, and bootstrap stability.
- Sensitivity to state-grid granularity, response-window definition, unit-quality rule, and covariance shrinkage strength.

#### Negative controls

- Permutation of recording-to-geometry pairings within matched coverage strata.
- Distances built after label-preserving nuisance-only simulations that contain matched task modulation but no shared residual covariance.

#### Positive controls

- Synthetic shared-covariance recordings processed through the identical cross-validation workflow.

#### Alternative explanations

- Shared sensory, timing, choice, or movement modulation rather than recurrent residual covariance.
- Similarity induced by pooling, evaluation-set alignment, unequal sampling, or unstable covariance estimates.

#### Predicted result patterns

- A recurring sampled-population motif requires held-out correspondence and transfer exceeding each matched alternative across eligible recordings.
- Decision-related signals without robust correspondence or transfer favor heterogeneous geometry or leave recurrence unresolved when precision fails.

#### Interpretation limits

- The plan cannot establish a brain-wide mechanism, causal localization, or recurrence outside sampled eligible recordings.
- A subset-only recurrence must be reported as subset-limited rather than a broad common motif.

#### Required new skills

- Decode delta-encoded BWM spike shards and construct trial-aligned unit responses.
- Run grouped cross-validated residual-covariance distance geometry with synthetic method-recovery tests.

#### Unresolved decisions

- Minimum state-cell count, unit count, and covariance-stability threshold must be locked without target-outcome inspection.
- The exact movement-preparatory covariate representation must be selected from documented timing and wheel fields before execution.

### Variant 2

- Planner-stated disposition: `accepted_requires_new_skill`
- Planner summary: VISp and MOs each have documented multi-recording coverage and trial-level behavioral timing variables. The absence of shared sessions is retained as a design limitation: this is an independently recorded, held-out-recording regional comparison, not a simultaneous interregional covariance study.

#### Refined question

Across eligible independently recorded BWM VISp and MOs insertions, does the held-out regional difference in stimulus-conditioned versus movement-conditioned covariance-axis alignment improve response-time prediction beyond common-geometry and sampling-matched baselines?

#### Population and scope

Quality-labeled units assigned to Beryl VISp or MOs in the documented BWM visual decision task, with inference restricted to separately recorded sessions and no claim about simultaneous interregional covariance.

#### Unit of observation

A trial-by-unit response vector and its trial-level stimulus, movement, and response-time covariates.

#### Unit of inference

A held-out VISp or MOs insertion/session, with group comparisons resampled across recordings and clustered by subject and laboratory where support permits.

#### Hierarchy and dependence

All covariance axes are estimated within insertion; training and test sets are disjoint in recordings, and region effects are evaluated only after matching or conditioning on documented recording and trial-composition variables.

#### Validation strategy

Use synthetic recordings with matched trial composition, unequal unit counts, and known shared or region-specific covariance axes to verify that matching, resampling, and grouped evaluation distinguish sampling artifacts from the target dissociation.

#### Split strategy

Outer held-out-recording folds stratified by region, with all matching, unit subsampling, axis definition, and model tuning confined to training recordings; group folds by subject or laboratory whenever feasible.

#### Planner-stated claim ceiling (not yet schema-validated)

predictive

#### Resource estimate

A new executor should stream one insertion at a time, execute repeated matched subsamples, and store only aggregate fold-level diagnostics; expected work is high because trial matching and covariance axes are repeated across folds.

#### Why this plan serves the question

It preserves the specified VISp-MOs alignment contrast, requires sampling-matched held-out regional reproduction, and tests predictive value against both common-geometry and matched baselines without converting the question into a general or causal claim.

#### Data sources

1. Unit anatomy and quality metadata plus insertion-sharded spike data for Beryl VISp and MOs populations.
   - Expected grain: Unit and spike event nested in an insertion and session; regional groups are independently recorded in this snapshot.
   - Required variables: pid; cluster_id; beryl_acronym; label; spike_times_delta_ticks; spike_clusters
   - Limitations: There are no sessions containing both VISp and MOs, so region is inseparable from recording session at the observation level.
2. Trial-level stimulus, choice, response-time, and movement timing/features joined to each recording session.
   - Expected grain: Trial nested within session.
   - Required variables: signed_contrast; choice_label; reaction_time; movement_time; movement_onset_time; movement_direction; mean_velocity
   - Limitations: Wheel coverage is incomplete and must be balanced or explicitly modeled as missing.

#### Analysis strategy

- Apply one common blinded quality rule and retain VISp and MOs recordings only if each supports the prespecified stimulus, choice, movement, and response-time strata.
- Repeatedly subsample units to a shared count and match trials across region, signed contrast, choice, movement timing or wheel features, and response-time strata.
- Within training recordings, estimate stimulus-conditioned and movement-conditioned covariance axes using cross-fitted responses and summarize their alignment with a prespecified angle or canonical-correlation metric.
- On held-out recordings, compare a region-specific alignment predictor of trial-level response-time variation with a common-geometry predictor and with the distribution from sampling-matched region-label permutations.

#### Candidate estimands

- Held-out difference in covariance-axis alignment between VISp and MOs after repeated unit and trial matching.
- Held-out incremental prediction of response-time variation from region-specific versus common geometry.

#### Diagnostics

- Regional overlap in retained trial strata, recording quality, unit-count distributions, and wheel-feature availability.
- Stability of alignment and response-time prediction across repeated matched subsamples and leave-recording-out folds.

#### Negative controls

- Sampling-matched permutation of region labels among eligible recordings.
- Response-time models using movement timing alone to quantify whether geometry adds information beyond shared timing.

#### Positive controls

- Synthetic region-specific covariance-axis data with known response-time association and matched nuisance distributions.

#### Alternative explanations

- Unequal neuron counts, recording quality, trial composition, subject, or laboratory distribution.
- Response-time prediction driven by movement onset or common task timing rather than regional geometry.

#### Predicted result patterns

- The regional dissociation requires a stable held-out VISp-MOs alignment difference and better held-out response-time prediction than both common-geometry and matched-label baselines.
- A common-geometry advantage or an unstable matched estimate weakens the proposed dissociation or leaves it unresolved, respectively.

#### Interpretation limits

- This observational, non-simultaneous regional comparison cannot establish causal localization or within-session interregional covariance.
- Any association is limited to the sampled task, eligible recordings, matching variables, and available precision.

#### Required new skills

- Decode delta-encoded BWM spike shards and build trial-aligned unit responses.
- Perform grouped recording-level matching, unit subsampling, covariance-axis estimation, and held-out predictive comparison.

#### Unresolved decisions

- Define the response-time transform and practically meaningful incremental-prediction threshold before target evaluation.
- Lock the common quality rule and matching tolerance through a blinded coverage and synthetic-recovery procedure.

## Limitations

Accepted planning and review artifacts were retained, but dossier closure failed before a public dossier could be produced.

## Diagnostics

- `infrastructure/family_development_incomplete`: Returned planning material could not be fully validated; a readable family dossier was retained with a validation warning. (details)
This page preserves the generated scientific question; it is not a scientific finding or downstream authorization.

## Next action

Inspect the run diagnostic and retained products before deciding whether to revise inputs or resume.
