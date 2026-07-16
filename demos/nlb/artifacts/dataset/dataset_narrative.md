# Dataset Narrative — dandi-000140-nlb-mc-maze-s coarse proposal-stage dataset narrative

- Dataset: `dandi-000140-nlb-mc-maze-s`
- Review status: `automated_reviewed`

## Scientific purpose

A scaled release of MC_Maze recordings intended for neural data analysis involving activity recorded from primary motor cortex (M1) and dorsal premotor cortex (PMd).

## Population

Neural recordings from M1 and PMd are represented. The supplied source does not state the number or species of recorded subjects.

## Task / design

The release is organized as a train/test dataset for the MC_Maze task or experiment, with 100 train trials and 100 test trials stated in the dataset description. Further task details are not provided in the supplied excerpt.

## Recording modalities

Neural array recordings from M1 and PMd; Sorted unit spiking times; Cursor position; Hand position; Eye position; Hand velocity calculated offline from hand position

## Broad scale

The scaled release contains 100 train trials and 100 test trials. Release-preparation metadata inspection reports recordings from both PMd and M1, with 142 sorted units in train and 107 held-in test units.

## Anatomical / spatial coverage

Arrays cover primary motor cortex (M1) and dorsal premotor cortex (PMd). The source identifies the first digit of each unit ID as the authoritative region indicator: leading 1 denotes PMd and leading 2 denotes M1.

## Temporal / trial structure

The data are divided into train and test splits, with 100 trials in each split according to the supplied dataset description. Session count, trial timing, and temporal sampling details are not stated.; Dataset release: DANDI:000140 / MC_Maze_Small; Train and test splits; Neural units or sorted units; M1 and PMd anatomical regions; Unit IDs and electrode metadata, subject to the documented M1 index correction

## Standardization

The release has a pinned published version, 0.220113.0408, and a documented region-index and electrode-index conversion caveat. M1 stored electrode indices require a +96 correction when mapping to the electrode table; uncorrected electrode indices should not be used alone for regional assignment.

## Major variables

- Neural activity from sorted units
- Anatomical region identity for M1 versus PMd
- Train/test split membership
- Unit identity
- Electrode metadata after applying the documented M1 correction
- Sorted neural spiking activity
- Cursor position
- Hand position
- Eye position
- Hand velocity
- Delayed reaching behavior
- Reach geometry, including straight and curved trajectories
- M1 and PMd recording location

## Reuse opportunities

- Comparative analyses of neural activity across M1 and PMd
- Region-stratified analyses using the unit-ID region convention
- Train/test benchmarking for neural representation or decoding methods
- Reanalysis of the relationship between neural recordings and the MC_Maze task, subject to verifying task-specific fields and timing in the released data
- Study relationships between cortical spiking activity and reaching behavior.
- Compare neural dynamics associated with straight versus curved reaches.
- Investigate preparatory or delay-period activity in M1 and PMd.
- Relate neural activity to cursor, hand, eye, and derived hand-velocity measurements.
- Develop or evaluate neural decoding and latent-dynamics analyses using the stated train/test task partition.

## Known high-level limitations

- The supplied source does not state the number or species of subjects, the number of sessions, detailed trial timing, or behavioral and auxiliary measurement coverage.
- The release is explicitly scaled to 100 train and 100 test trials, which may limit analyses requiring broader sampling.
- A documented M1 electrode-index conversion error complicates direct interpretation of stored unit/electrode metadata; region assignment should use the authoritative unit-ID rule and the M1 +96 correction.
- The source notes ordinary single-session limitations for analyses using the combined within-session M1+PMd population.
- The supplied excerpt does not establish exact question-specific coverage or feasibility; those details require later branch-specific verification.
- The supplied public excerpts do not state the number of sorted units, electrode channels, recording sessions, or session-to-session structure.
- The dataset is explicitly limited to 100 train trials and 100 test trials, which may constrain analyses requiring broader sampling of task conditions.
- The supplied excerpts do not specify detailed timing parameters, preprocessing procedures, missing-data handling, or exact coverage across recording sites.
- The public description concerns a single macaque and therefore does not establish population-level generalizability.
- Exact question-specific feasibility and coverage require later branch-specific inspection and planning.

## Coarse scale facts

- trials in train split: 100 train trials
- trials in test split: 100 test trials
- sorted neural units in train split: 72 PMd units and 70 M1 units, 142 total
- sorted neural units in held-in test split: 52 PMd units and 55 M1 units, 107 total
- recording regions: M1 and PMd
- raw electrode-table region rows: 96 PMd rows and 96 M1 rows
- public dataset identity and release hierarchy: DANDI:000140, MC_Maze_Small, published version 0.220113.0408
- subjects_or_participants: 1 macaque
- trials: 100 train trials and 100 test trials
- recording_units: Sorted unit spiking times are provided; the number of units is not stated
- measurement_sites_or_regions: M1 and PMd electrode-array recordings
- task_structure: Delayed center-out reaching through a barrier-defined maze, including straight and curved reaches
- behavioral_or_auxiliary_measurements: Cursor, hand, and eye position, plus hand velocity calculated offline
- public_access_and_hierarchy: Publicly described as part of the Neural Latents Benchmark and hosted through the DANDI dataset record; data are divided into train and test trials

## Provenance

- Fusion prompt marker: `dataset_narrative_fusion/v1`
- Generator provider(s): `cached-openai:gpt-5.6-luna`
- Source feeds fused: 2

## Review authority

Automated independent-AI fidelity gate dataset_narrative_fidelity_reviewer/v1 (provider anthropic, model claude-opus-4-8) returned accept; reviewer independent of generators ['cached-openai:gpt-5.6-luna'].

## Data basis & limitations

The local sample proves only what is present IN the sample. Absence of a feature in the sample is NOT absence in the full dataset; no joint-coverage across variables is proven; and a property the sample cannot resolve is recorded as insufficient_sample_evidence, never as a dataset mismatch.
- The supplied source does not state the number or species of subjects, the number of sessions, detailed trial timing, or behavioral and auxiliary measurement coverage.
- The release is explicitly scaled to 100 train and 100 test trials, which may limit analyses requiring broader sampling.
- A documented M1 electrode-index conversion error complicates direct interpretation of stored unit/electrode metadata; region assignment should use the authoritative unit-ID rule and the M1 +96 correction.
- The source notes ordinary single-session limitations for analyses using the combined within-session M1+PMd population.
- The supplied excerpt does not establish exact question-specific coverage or feasibility; those details require later branch-specific verification.
- The supplied public excerpts do not state the number of sorted units, electrode channels, recording sessions, or session-to-session structure.
- The dataset is explicitly limited to 100 train trials and 100 test trials, which may constrain analyses requiring broader sampling of task conditions.
- The supplied excerpts do not specify detailed timing parameters, preprocessing procedures, missing-data handling, or exact coverage across recording sites.
- The public description concerns a single macaque and therefore does not establish population-level generalizability.
- Exact question-specific feasibility and coverage require later branch-specific inspection and planning.
