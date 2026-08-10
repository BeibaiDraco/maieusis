# Dataset Narrative — dandi-000140-nlb-mc-maze-s coarse proposal-stage dataset narrative

- Dataset: `dandi-000140-nlb-mc-maze-s`
- Review status: `automated_reviewed`

## Scientific purpose

The dataset supports study of neural population activity associated with delayed reaching, including comparisons between primary motor cortex (M1) and dorsal premotor cortex (PMd), across straight and curved reach trajectories around barriers.

## Population

One rhesus macaque performing delayed center-out reaching tasks.

## Task / design

Delayed center-out reaching around barriers, including both straight and curved reaches. The supplied excerpt does not provide a complete description of task events or experimental conditions.

## Recording modalities

Sorted-unit spiking times; Cursor measurements; Hand-position measurements; Eye measurements; Hand-velocity measurements; Sorted unit spiking times; Cursor position; Hand position; Eye position; Hand velocity calculated offline from hand position

## Broad scale

A small, single-subject release with sorted-unit recordings from M1 and PMd. The scaled release is described as containing 100 training trials and 100 test trials; bounded metadata checks reported 142 training units and 107 held-in test units, but these counts do not establish trial-level coverage or unit-quality equivalence.

## Anatomical / spatial coverage

Recordings include primary motor cortex (M1) and dorsal premotor cortex (PMd). The supplied documentation identifies these regions through the leading digit of unit IDs and describes a correction required for M1 electrode-table indices.

## Temporal / trial structure

The task includes a delayed reaching period and reach trajectories around barriers, with straight and curved reaches. Event timing and session structure are not specified in the supplied excerpt and require later verification.; Single rhesus macaque; Recordings organized by train and test releases; Sorted recording units nested within M1 and PMd regions; Behavioral measurements associated with delayed reaching trials

## Standardization

The release contains sorted-unit spiking times and behavioral measurements. The documentation specifies a region-identification convention based on unit IDs and an M1 electrode-index correction; these mappings must be reconciled with unit, electrode, DANDI, and official benchmark documentation before region-specific use.

## Major variables

- Neural spiking activity from sorted units
- Cortical region: M1 or PMd
- Reach trajectory type: straight or curved
- Barrier-related reaching context
- Cursor position
- Hand position
- Eye measurements
- Hand velocity
- Training versus test release
- Neural spiking activity
- Eye position
- Reaching trajectory type, including straight and curved reaches
- Delayed center-out maze-reaching task structure

## Reuse opportunities

- Study population-level neural dynamics during delayed reaching
- Compare activity associated with M1 and PMd at a broad regional level
- Relate neural activity to cursor, hand, eye, and hand-velocity measurements
- Examine differences between straight and curved reaches or other broad task contexts
- Develop or evaluate latent-variable models of neural population activity using the released neural and behavioral measurements
- Study relationships between motor and premotor spiking activity and reaching behavior.
- Examine neural representations associated with delayed movement preparation and execution.
- Compare neural and behavioral dynamics across straight and curved maze-constrained reaches.
- Develop or evaluate neural population analyses and movement-decoding approaches using paired spiking and kinematic measurements.

## Known high-level limitations

- The release represents one rhesus macaque, limiting population-level generalization.
- The scaled release is small, and the supplied metadata checks do not establish trial-level coverage, unit-quality equivalence, or region-specific feasibility for a particular analysis.
- M1 electrode indices contain a documented conversion error and require the specified correction before anatomical interpretation.
- Region assignment and electrode metadata must be reconciled across unit IDs, electrode metadata, DANDI metadata, and official documentation.
- Sessions, exact event timing, and detailed region-specific trial coverage are not stated in the supplied excerpt.
- The supplied excerpt describes available measurements broadly but does not certify coverage for any specific future scientific question.
- The public excerpt describes a release limited to 100 train trials and 100 test trials.
- The supplied excerpts do not state the number of recording sessions, electrode channels, sorted units, or exact measurement-site coverage beyond M1 and PMd.
- The excerpt describes the task and recorded variables but does not establish coverage for questions requiring other brain regions, subjects, tasks, or experimental conditions.

## Coarse scale facts

- subjects or participants: 1 rhesus macaque
- trials: 100 training trials and 100 test trials
- recording units: Train: 72 PMd and 70 M1 units, 142 total; test held-in: 52 PMd and 55 M1 units, 107 total
- measurement sites or regions: Raw electrode table has 96 PMd and 96 M1 rows
- task or experimental structure: Delayed center-out reaches around barriers, including straight and curved reaches
- behavioral or auxiliary measurements: Cursor, hand, eye, and hand-velocity measurements
- public access mode and hierarchy: Public DANDI release, version 0.220113.0408, with train and test releases and official Neural Latents Benchmark documentation
- subjects or participants: One macaque is described as performing the task.
- trials or samples: 100 train trials and 100 test trials are provided.
- recording units, channels, or sensors: Sorted unit spiking activity was recorded using electrode arrays; the number of units or channels is not stated.
- measurement sites or regions: Two named cortical regions are covered: primary motor cortex (M1) and dorsal premotor cortex (PMd).
- task or experimental structure: Delayed center-out reaching through a barrier-defined maze, yielding straight and curved reaches.
- behavioral or auxiliary measurements: Cursor position, hand position, eye position, and hand velocity derived offline from hand position were recorded or calculated.
- public access mode and hierarchy: The dataset is publicly described through the DANDI Archive and is identified as part of the Neural Latents Benchmark.

## Provenance

- Fusion prompt marker: `dataset_narrative_fusion/v1`
- Generator provider(s): `cached-openai:gpt-5.6-luna`
- Source feeds fused: 2

## Review authority

Automated independent-AI fidelity gate dataset_narrative_fidelity_reviewer/v1 (provider anthropic, model claude-sonnet-5, session narrative_fidelity-review) returned accept; reviewer independent of generators ['cached-openai:gpt-5.6-luna']. The gate accepted while suggesting 1 non-blocking improvement(s); they are recorded on the persisted fidelity review in the reviewer's own wording and did not gate promotion.

## Data basis & limitations

The local sample proves only what is present IN the sample. Absence of a feature in the sample is NOT absence in the full dataset; no joint-coverage across variables is proven; and a property the sample cannot resolve is recorded as insufficient_sample_evidence, never as a dataset mismatch.
- The release represents one rhesus macaque, limiting population-level generalization.
- The scaled release is small, and the supplied metadata checks do not establish trial-level coverage, unit-quality equivalence, or region-specific feasibility for a particular analysis.
- M1 electrode indices contain a documented conversion error and require the specified correction before anatomical interpretation.
- Region assignment and electrode metadata must be reconciled across unit IDs, electrode metadata, DANDI metadata, and official documentation.
- Sessions, exact event timing, and detailed region-specific trial coverage are not stated in the supplied excerpt.
- The supplied excerpt describes available measurements broadly but does not certify coverage for any specific future scientific question.
- The public excerpt describes a release limited to 100 train trials and 100 test trials.
- The supplied excerpts do not state the number of recording sessions, electrode channels, sorted units, or exact measurement-site coverage beyond M1 and PMd.
- The excerpt describes the task and recorded variables but does not establish coverage for questions requiring other brain regions, subjects, tasks, or experimental conditions.
