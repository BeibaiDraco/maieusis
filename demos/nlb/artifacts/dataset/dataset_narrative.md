# Dataset Narrative — dandi-000140-nlb-mc-maze-s coarse proposal-stage dataset narrative

- Dataset: `dandi-000140-nlb-mc-maze-s`
- Review status: `automated_reviewed`

## Scientific purpose

Study neural population activity during delayed reaching, including comparisons of activity recorded from primary motor cortex (M1) and dorsal premotor cortex (PMd).

## Population

One rhesus macaque performing delayed center-out reaching tasks.

## Task / design

Delayed center-out reaches around barriers, including both straight and curved reaches. The scaled release is organized into training and test portions.

## Recording modalities

Sorted-unit spiking times; Cursor measurements; Hand position measurements; Eye measurements; Hand-velocity measurements; Sorted unit spiking times; Cursor position; Hand position; Eye position; Hand velocity calculated offline from hand position

## Broad scale

A small, single-subject release with on the order of a few hundred trials and a few hundred sorted units in the documented scaled files.

## Anatomical / spatial coverage

Motor-cortical recordings from PMd and M1. Unit identifiers follow a documented region-encoding convention that must be consulted before regional interpretation.

## Temporal / trial structure

Trial-based delayed reaching recordings with behavioral and neural measurements over the reach task; exact event timing and usable trial counts require later verification.

## Standardization

The release uses sorted-unit spike times and documented unit-ID and electrode-region conventions. M1 electrode indices require the documented correction before interpreting electrode metadata; unit, electrode, DANDI, and benchmark documentation should be reconciled.

## Major variables

- Neural spiking activity
- Reach trajectory and cursor behavior
- Hand position and hand velocity
- Eye measurements
- Cortical region identity: PMd or M1
- Reach condition involving straight or curved paths
- Cursor position
- Hand position
- Eye position
- Hand velocity
- Reach trajectory structure

## Reuse opportunities

- Analysis of neural population dynamics during reaching
- Comparison of PMd and M1 population activity with region-stratified sensitivity analyses
- Modeling relationships among spiking activity, reach behavior, cursor trajectories, eye measurements, and hand velocity
- Reuse in latent-variable and neural-population modeling benchmarks
- Relating motor and premotor population spiking to hand, cursor, and eye behavior
- Studying neural dynamics across delayed reaching and varied straight or curved trajectories
- Comparing neural representations across M1 and PMd
- Benchmarking neural-latent or behavior-decoding methods using the publicly described task and recordings

## Known high-level limitations

- The release contains data from only one rhesus macaque and is described as small.
- The documented M1 electrode-index conversion must be applied before using electrode metadata for regional interpretation.
- The supplied metadata verification does not establish trial-level coverage, unit-quality equivalence, or scientific regional differences.
- Usable trial counts, event timing, and region-specific coverage require later dataset-specific verification before claims of feasibility.
- The supplied excerpts do not establish broader subject, session, or recording coverage beyond the described release.
- The public description identifies a limited benchmark release rather than the full experimental collection.
- The excerpt does not state the number of sessions, recording units, channels, or sensors.
- The description does not establish detailed preprocessing, trial inclusion criteria, or fine-grained joint coverage across neural and behavioral variables.
- Exact question-specific feasibility requires later branch-specific verification.

## Coarse scale facts

- subjects or participants: One rhesus macaque
- trials or samples if publicly stated: On the order of 200 trials in the scaled release
- recording units, channels, or sensors: On the order of a few hundred sorted units
- measurement sites or regions: Two named cortical regions: PMd and M1
- task or experimental structure: Delayed center-out reaching around barriers, with straight and curved reaches
- behavioral or auxiliary measurements: Multiple behavioral and auxiliary streams, including cursor, hand, eye, and hand-velocity measurements
- public access mode and hierarchy: Public DANDI release, version 0.220113.0408, also represented in the Neural Latents Benchmark; the scaled release has training and test portions

## Provenance

- Fusion prompt marker: `dataset_narrative_fusion/v1`
- Generator provider(s): `cached-openai:gpt-5.6-luna`
- Source feeds fused: 2

## Review authority

Automated independent-AI fidelity gate dataset_narrative_fidelity_reviewer/v2 (provider anthropic, model claude-sonnet-5, session narrative_fidelity-review) returned accept; reviewer independent of generators ['cached-openai:gpt-5.6-luna'].

## Data basis & limitations

The local sample proves only what is present IN the sample. Absence of a feature in the sample is NOT absence in the full dataset; no joint-coverage across variables is proven; and a property the sample cannot resolve is recorded as insufficient_sample_evidence, never as a dataset mismatch.
- The release contains data from only one rhesus macaque and is described as small.
- The documented M1 electrode-index conversion must be applied before using electrode metadata for regional interpretation.
- The supplied metadata verification does not establish trial-level coverage, unit-quality equivalence, or scientific regional differences.
- Usable trial counts, event timing, and region-specific coverage require later dataset-specific verification before claims of feasibility.
- The supplied excerpts do not establish broader subject, session, or recording coverage beyond the described release.
- The public description identifies a limited benchmark release rather than the full experimental collection.
- The excerpt does not state the number of sessions, recording units, channels, or sensors.
- The description does not establish detailed preprocessing, trial inclusion criteria, or fine-grained joint coverage across neural and behavioral variables.
- Exact question-specific feasibility requires later branch-specific verification.
