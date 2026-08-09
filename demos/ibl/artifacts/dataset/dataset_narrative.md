# Dataset Narrative — ibl_bwm coarse proposal-stage dataset narrative

- Dataset: `ibl_bwm`
- Review status: `automated_reviewed`

## Scientific purpose

To understand the neural basis of decision-making in the mouse by constructing a brain-wide activity map from electrophysiological recordings collected across multiple laboratories.

## Population

Mice performing the IBL decision-making task; the release includes recordings from 139 subjects across 12 laboratories.

## Task / design

A multi-laboratory, brain-wide electrophysiological recording study using Neuropixels probes during a mouse decision-making task, with repeated sampling of recording sites across laboratories.

## Recording modalities

Electrophysiological recordings with Neuropixels probes; Spike-sorted neural activity; Sensory stimulus measurements; Mouse decisions and response times; Video-based mouse pose measurements processed with DeepLabCut

## Broad scale

The documentation reports 459 Neuropixels experimental sessions, 699 probe insertions, 139 subjects, 12 laboratories, 621,733 spike-sorted units, 75,708 units classified as good quality, and 241 brain regions represented in sufficient numbers for inclusion in the reported analyses.

## Anatomical / spatial coverage

The dataset is intended to provide brain-wide coverage. Recordings were systematically collected from nearly all major brain areas using a grid system; 241 brain regions are reported as represented in sufficient numbers for the IBL analyses.

## Temporal / trial structure

Recordings are organized into experimental sessions and probe insertions during performance of a decision-making task. The excerpt does not specify the detailed timing structure, trial counts, or duration of individual recordings.; 12 laboratories; 139 subjects; 459 experimental sessions; 699 probe insertions; Spike-sorted neural units; 241 brain regions represented in sufficient numbers for reported analyses

## Standardization

The data are organized according to the standard IBL data structure. Recording sites were sampled using a grid system, and each site was replicated in at least two laboratories to support systematic and replicated coverage.

## Major variables

- Neural spiking activity
- Sensory stimuli
- Mouse decisions
- Response times
- Mouse pose and movement information from video

## Reuse opportunities

- Study brain-wide neural correlates of mouse decision-making
- Relate neural activity to sensory stimuli, decisions, and response times
- Investigate cross-region and cross-laboratory organization of neural activity
- Analyze relationships between neural activity and video-derived pose or movement measures
- Compare recordings across subjects, sessions, probe insertions, and laboratories within a standardized data organization

## Known high-level limitations

- The supplied excerpt does not specify detailed trial structure, recording durations, preprocessing choices, or the exact temporal and anatomical coverage available for any particular future analysis.
- The documentation reports regions represented in sufficient numbers for the IBL analyses, but this broad statement does not establish question-specific coverage or feasibility.
- The excerpt does not provide detailed information about behavioral variability, missingness, or measurement quality beyond the reported distinction between total spike-sorted units and units classified as good quality.

## Coarse scale facts

- subjects: 139 subjects
- experimental sessions: 459 experimental sessions
- probe insertions: 699 distinct recordings, referred to as probe insertions
- spike-sorted units: 621,733 units
- good-quality units: 75,708 units
- laboratories: 12 laboratories
- brain regions: 241 brain regions recorded in sufficient numbers for inclusion in the IBL analyses
- task or experimental structure: Mouse decision-making task with sensory stimuli, recorded decisions, response times, and video-derived pose information
- public access mode and hierarchy: Released dataset organized according to the standard IBL data structure, with exploration through a visualization website

## Provenance

- Fusion prompt marker: `dataset_narrative_fusion/v1`
- Generator provider(s): `cached-openai:gpt-5.6-luna`
- Source feeds fused: 1

## Review authority

Automated independent-AI fidelity gate dataset_narrative_fidelity_reviewer/v1 (provider anthropic, model claude-sonnet-5, session narrative_fidelity-review) returned accept; reviewer independent of generators ['cached-openai:gpt-5.6-luna'].

## Data basis & limitations

The local sample proves only what is present IN the sample. Absence of a feature in the sample is NOT absence in the full dataset; no joint-coverage across variables is proven; and a property the sample cannot resolve is recorded as insufficient_sample_evidence, never as a dataset mismatch.
- The supplied excerpt does not specify detailed trial structure, recording durations, preprocessing choices, or the exact temporal and anatomical coverage available for any particular future analysis.
- The documentation reports regions represented in sufficient numbers for the IBL analyses, but this broad statement does not establish question-specific coverage or feasibility.
- The excerpt does not provide detailed information about behavioral variability, missingness, or measurement quality beyond the reported distinction between total spike-sorted units and units classified as good quality.
