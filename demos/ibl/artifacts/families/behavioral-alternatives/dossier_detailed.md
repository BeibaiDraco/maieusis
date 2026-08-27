# Embodied and internal-state explanations of apparent noise correlations — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Validation warning**
- Authority: **Provisional / degraded**
- Accepted-plan authority: **No**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Asks whether apparently unexplained neural covariance is better understood as rich movement-related structure or as non-motor internal-state variation.

The scientific tension is:

Residual correlations associated with choice and response time may reflect decision computation, but conventional controls may omit multidimensional behavior or internal state. Richer alternatives can either explain away a decision interpretation or reveal scientifically meaningful embodied structure.

## How to read this terminal

Returned planning material did not pass strict typed validation. The family is complete as a readable soft terminal, but it remains provisional and degraded with no accepted-plan authority.

**Recorded public status note**

Returned planning material could not be fully validated; a readable family dossier was retained with a validation warning.

## Variant 1: Conditional uninstructed-pose explanation of shared covariance

### Why it matters

Separating shared covariance from total neural variance and uninstructed pose from response execution would clarify whether an apparently decision-related population component reflects omitted embodied structure or remains compatible with latent decision or internal-state accounts.

### Original and refined question

**Original Question Scientist proposal**

How much apparently choice- or response-time-related shared neural variability is predictively accounted for by multidimensional pose and movement structure beyond simpler behavioral summaries?

**Post-novelty revised proposal**

Does time-resolved multidimensional structure in uninstructed and ongoing pose incrementally predict the held-out trial-to-trial shared neural covariance component remaining after task events, response-executing movements, coarse movement summaries, and measured arousal are conditioned on, and does adding that pose structure attenuate the component’s association with choice or response time?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If sufficiently synchronized neural, pose, task, choice, response-time, movement, and arousal measurements overlap, they may support held-out nested comparisons for a trial-to-trial shared neural component rather than total single-neuron or widefield activity variance.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The sampled semantic shard declares fixed-rate body-camera timestamps at 30 Hz and time-resolved DLC feature matrices. Its body stream includes tail-start coordinates and likelihood; left and right streams include nose, pupil landmarks, paws, tongue landmarks, likelihoods, and pupil-diameter signals. The shard also contains wheel position, velocity, and timestamps.
  - Limitation: This is a one-shard structural inspection and does not establish coverage or quality for any individual session.
  - Limitation: The coordinates are camera-view keypoints, not a complete three-dimensional whole-body reconstruction.
- **Unverified planning evidence:** The behavior product is keyed by eid and trial_id and exposes task timing, choice, feedback, contrasts, response times, first movement times, trial-derived reaction and movement times, wheel features, DLC feature summaries, movement epochs, and per-camera availability.
  - Limitation: DLC feature tables are summaries; time-resolved pose must be decoded from the documented session shards.
  - Limitation: Availability is uneven across sessions and cameras, so eligibility must be determined before modeling.
- **Unverified planning evidence:** The ephys product provides sessions, insertions, units, trials, events, and per-insertion spike shards. Spike shards encode delta-tick spike times and local cluster indices, while unit records are linked to insertion and session identifiers, enabling session-level alignment with behavior and cross-unit covariance construction.
  - Limitation: The planner did not decode spikes or calculate neural covariance.
  - Limitation: Units are nested within insertions and sessions, so trial-level observations are not independent.
- 1 additional typed inspection statement(s) remain in the complete planning record.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

First define the neural estimand as trial-to-trial cross-neuron shared covariance, or a prespecified latent component representing it, distinct from marginal activity variance. Compare held-out prediction under a baseline conditioned on available stimulus and task events, choice and response time, instructed response execution such as recorded lick or saccade variables, coarse locomotion and movement summaries, and measured pupil or other arousal summaries, against a model that additionally represents time-resolved multidimensional body, face, and postural keypoint configurations and dynamics where available. Partition or otherwise separately assess response-linked pose and uninstructed or ongoing pose. Estimate the shared component’s held-out association with choice or response time under the baseline and again after pose adjustment; unique pose prediction plus attenuation attributable to the uninstructed or ongoing block would discriminate the embodied account, but would not establish that pose mechanistically causes the covariance.

**What possible outcomes would mean**

- Positive pattern: Reliable held-out improvement from uninstructed or ongoing multidimensional pose, together with attenuation of the shared component’s choice or response-time association after pose adjustment, would support an embodied interpretation of part of the apparent decision-related covariance. It would not by itself establish a causal effect of pose or movement on neural covariance.
- Negative pattern: If adequately measured multidimensional pose adds no held-out prediction beyond the explicit baseline and the choice or response-time association remains stable, the measured embodied account would be weakened and residual decision or internal-state explanations would gain relative support.
- Null or ambiguous pattern: An imprecise or unstable incremental comparison would remain inconclusive because incomplete pose coverage, uneven synchronization, weak estimation of shared covariance, or collinearity among task, response, arousal, and pose variables could obscure either an embodied contribution or a genuine residual component.

## Variant 2: Residual internal-state branch with prospective source discrimination

### Why it matters

This question tests whether richer controls reveal a stable neural source of prospective behavioral variation or instead show that apparent internal-state covariance is another expression of embodied behavior, recurrent dynamics, behavioral history, or measurement drift.

### Original and refined question

**Original Question Scientist proposal**

After accounting for measured movement, does a residual shared-variability component predict response-time and choice-history effects consistent with a non-motor internal state?

**Post-novelty revised proposal**

Does a recording-stable residual neural covariance component prospectively improve held-out prediction of response time and history-dependent choice beyond prior outcomes, trial history, behavioral latent-state models, temporally extended movement-related activity, and recent neural-activity or excitability proxies?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If sufficiently aligned behavior, trial history, response times, pose, neural activity, and recording-quality information overlap, they may permit nested held-out comparisons among behavioral-history, embodied-movement, recurrent-dynamics, measurement-instability, and residual-covariance explanations.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The sampled semantic shard declares fixed-rate body-camera timestamps at 30 Hz and time-resolved DLC feature matrices. Its body stream includes tail-start coordinates and likelihood; left and right streams include nose, pupil landmarks, paws, tongue landmarks, likelihoods, and pupil-diameter signals. The shard also contains wheel position, velocity, and timestamps.
  - Limitation: This is a one-shard structural inspection and does not establish coverage or quality for any individual session.
  - Limitation: The coordinates are camera-view keypoints, not a complete three-dimensional whole-body reconstruction.
- **Unverified planning evidence:** The behavior product is keyed by eid and trial_id and exposes task timing, choice, feedback, contrasts, response times, first movement times, trial-derived reaction and movement times, wheel features, DLC feature summaries, movement epochs, and per-camera availability.
  - Limitation: DLC feature tables are summaries; time-resolved pose must be decoded from the documented session shards.
  - Limitation: Availability is uneven across sessions and cameras, so eligibility must be determined before modeling.
- **Unverified planning evidence:** The ephys product provides sessions, insertions, units, trials, events, and per-insertion spike shards. Spike shards encode delta-tick spike times and local cluster indices, while unit records are linked to insertion and session identifiers, enabling session-level alignment with behavior and cross-unit covariance construction.
  - Limitation: The planner did not decode spikes or calculate neural covariance.
  - Limitation: Units are nested within insertions and sessions, so trial-level observations are not independent.
- 1 additional typed inspection statement(s) remain in the complete planning record.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

The non-motor account would be supported only by a residual covariance component that prospectively improves held-out prediction of both response-time variation and history-dependent choice beyond prior outcomes, trial history, a behavioral latent-state model, temporally offset pose, movement vigor or micro-movement descriptions, movement-linked neural dynamics, recent neural activity or excitability-state proxies, and recording-quality or drift structure. Its contribution should remain stable across held-out recording segments and across differing recent-activity histories. Loss of prediction after movement controls would favor an embodied account; loss after recent-activity or excitability controls would favor a recurrent-state account; and prediction that tracks quality or drift and fails cross-segment generalization would favor measurement instability.

**What possible outcomes would mean**

- Positive pattern: A result meeting the full discriminating pattern would support a stable neural covariance component with prospective behavioral information not recoverable from the tested behavioral-history, movement, recurrent-dynamics, or measurement alternatives, while remaining associational rather than proving a unitary internal state.
- Negative pattern: If the residual contribution is specifically eliminated by behavioral latent-state, movement-linked, recurrent-history, or recording-instability controls, the corresponding alternative would gain support over a separable non-motor component and would narrow the interpretation of apparent decision-related covariance.
- Null or ambiguous pattern: If no model provides reliable held-out prediction, or if results vary across controls or recording segments, the construct would remain unresolved because incomplete movement measurement, inadequate proxies, residualization of relevant signal, temporal misalignment, or unstable neural measurement could each produce a null.

## Owner and independent review

Any typed review records below are retained context only. They cannot override this system terminal or create accepted-plan authority.

### Question Owner

- Disposition: **Revise**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family plan preserves the two distinct scientific contrasts and uses appropriate held-out, temporally ordered, cluster-aware designs. However, variant 1 conditions the covariance-stage baseline on choice and response time and then proposes to assess that same component’s association with choice or response time. This makes the intended attenuation comparison scientifically incoherent unless the outcome variables are excluded from construction and prediction of the covariance target.

Retained changes and locks:

- **Scientific blocker:** For variant 1, do not include choice or response time as covariance-stage nuisance predictors when the downstream estimand is that component’s association with choice or response time; define the covariance target and pose comparison conditional only on the stated non-outcome alternatives, with the outcome association evaluated subsequently.
- **Pre execution lock:** Before execution, prespecify variant 1 camera/keypoint coverage eligibility and the primary neural bin window without using held-out outcomes.
- **Pre execution lock:** Before execution, prespecify variant 2 behavioral latent-state model class, outcome links, neural-history windows, and minimum recording-segment length independently of held-out results.

### Independent reviewer

- Disposition: **Revise**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Variant 2's prospective residual-covariance design, alternative-explanation set, controls, and cross-segment stability checks are scientifically coherent, well grounded in the available behavior/ephys schema and shard evidence, and appropriately bounded to an associational claim ceiling. Variant 1 preserves the intended embodied-versus-response-execution contrast and specifies matching controls, but its analysis_strategy includes choice and response-time as nuisance predictors when constructing the very shared-covariance target whose held-out association with choice/response-time is later evaluated. Conditioning the covariance estimand on the outcome and then testing that outcome's association with the (partially outcome-conditioned) component is circular: it can mechanically suppress or manufacture the reported attenuation regardless of any true pose contribution, so the plan as written cannot credibly answer its own protected conditional-association question. This is a genuine scientific blocker rather than a pre-execution detail, matching the Question Owner's independent flag. The remaining two Owner-identified issues (prespecifying camera/keypoint coverage and neural bin window for v1; prespecifying the behavioral latent-state model class, outcome links, neural-history windows, and minimum segment length for v2) are legitimate but are bounded implementation choices that do not undermine the current planning dossier, so they are correctly pre-execution locks rather than blockers. Sibling separation between the embodied (v1) and internal-state (v2) contrasts is intact and the family's forbidden semantic merge is avoided. No hard integrity boundary is implicated; the circularity is repairable by excluding choice/response-time from the covariance-stage baseline and evaluating the outcome association only afterward, as the Owner already specified.

Retained changes and locks:

- **Scientific blocker:** For variant 1, do not include choice or response time as covariance-stage nuisance predictors when the downstream estimand is that component’s association with choice or response time; define the covariance target and pose comparison conditional only on the stated non-outcome alternatives, with the outcome association evaluated subsequently.

**Authority reminder:** these dispositions do not yield an accepted plan here.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
