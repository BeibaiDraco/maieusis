# Dataset Narrative — ibl_bwm coarse proposal-stage dataset narrative

- Dataset: `ibl_bwm`
- Review status: `automated_reviewed`

## Scientific purpose

The dataset is intended to support a whole-brain map of neural activity in the mouse and to study the neural basis of decision-making. It pools electrophysiological recordings from multiple laboratories and samples major brain areas using a grid-based approach.

## Population

Mice performing the IBL decision-making task; the release includes data from 139 subjects across 12 laboratories.

## Task / design

A multisite, brain-wide electrophysiology study conducted during a mouse decision-making task. The experiment includes sensory stimuli, mouse decisions and response times, and video-based pose measurements.

## Recording modalities

Neuropixels electrophysiological recordings; Spike-sorted neural activity; Video recordings; DeepLabCut-derived mouse pose information; Sensory stimulus and behavioral measurements

## Broad scale

The public release comprises hundreds of experimental sessions and probe insertions, spanning 139 subjects and 12 laboratories, with neural recordings covering hundreds of brain regions and hundreds of thousands of spike-sorted units.

## Anatomical / spatial coverage

The study was designed for brain-wide coverage, with recordings from nearly all major brain areas. The documentation reports 241 brain regions recorded in sufficient numbers for inclusion in the associated analyses.

## Temporal / trial structure

Recordings and behavioral measurements are collected during decision-making task sessions, including sensory stimulus presentation, mouse decisions, response times, electrophysiological activity, and video-based pose over the task.

## Standardization

Recordings use Neuropixels probes and a grid system for systematic, unbiased sampling, with each recording site replicated in at least two laboratories. The data follow the standard IBL data structure and are accompanied by spike-sorting and data-processing pipelines.

## Major variables

- Neural spiking activity
- Brain region
- Sensory stimuli
- Mouse decisions
- Response times
- Mouse pose
- Task session and probe-insertion context
- Laboratory and subject context

## Reuse opportunities

- Comparative analysis of neural activity across brain regions during decision-making
- Investigation of relationships between neural activity, sensory stimuli, decisions, and response times
- Study of brain-wide and multisite reproducibility across laboratories
- Integration of electrophysiology with video-derived pose and behavioral measurements
- Analysis of neural activity at single-spike cellular resolution

## Known high-level limitations

- The supplied documentation excerpt does not provide detailed question-specific coverage or measurement-quality criteria beyond the reported high-level release summary.
- The reported 241 regions are those recorded in sufficient numbers for inclusion in the associated analyses, so they should not be interpreted as uniform coverage of every brain region.
- The excerpt does not specify the full details of preprocessing, spike-sorting quality criteria, or the availability of every behavioral and video-derived measurement for every recording.

## Coarse scale facts

- subjects or participants: 139 mouse subjects
- sessions or recordings: 459 experimental sessions and 699 probe insertions
- recording units, channels, or sensors: On the order of hundreds of thousands of spike-sorted units, including tens of thousands classified as good quality
- measurement sites or regions: Hundreds of brain regions; 241 were recorded in sufficient numbers for inclusion in the analyses
- task or experimental structure: A multisite, brain-wide Neuropixels study of mice performing a decision-making task, with sampling replicated across 12 laboratories
- behavioral or auxiliary measurements: Behavioral task variables plus video-derived pose measurements are released alongside neural recordings
- public access mode and hierarchy: Publicly released data organized in the standard IBL data structure, with an accompanying visualization website and documentation of processing pipelines

## Provenance

- Fusion prompt marker: `dataset_narrative_fusion/v1`
- Generator provider(s): `cached-openai:gpt-5.6-luna`
- Source feeds fused: 1

## Review authority

Automated independent-AI fidelity gate dataset_narrative_fidelity_reviewer/v2 (provider anthropic, model claude-sonnet-5, session narrative_fidelity-review) returned accept; reviewer independent of generators ['cached-openai:gpt-5.6-luna'].

## Data basis & limitations

The local sample proves only what is present IN the sample. Absence of a feature in the sample is NOT absence in the full dataset; no joint-coverage across variables is proven; and a property the sample cannot resolve is recorded as insufficient_sample_evidence, never as a dataset mismatch.
- The supplied documentation excerpt does not provide detailed question-specific coverage or measurement-quality criteria beyond the reported high-level release summary.
- The reported 241 regions are those recorded in sufficient numbers for inclusion in the associated analyses, so they should not be interpreted as uniform coverage of every brain region.
- The excerpt does not specify the full details of preprocessing, spike-sorting quality criteria, or the availability of every behavioral and video-derived measurement for every recording.
