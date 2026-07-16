# Dataset Narrative — ibl-brain-wide-map coarse proposal-stage dataset narrative

- Dataset: `ibl-brain-wide-map`
- Review status: `automated_reviewed`

## Scientific purpose

To understand the neural basis of decision-making in the mouse by constructing a whole-brain activity map from electrophysiological recordings collected across multiple laboratories.

## Population

Mice performing the IBL decision-making task; the released data include recordings from 139 subjects.

## Task / design

A multi-laboratory, brain-wide electrophysiological recording study using Neuropixels probes during a mouse decision-making task, with associated sensory stimuli, decisions, response times, and video-derived pose information.

## Recording modalities

Electrophysiological recordings with Neuropixels probes; Video recordings with DeepLabCut-derived pose information; Task sensory stimuli, decisions, and response times

## Broad scale

The release contains 459 experimental sessions, 699 probe insertions, 139 subjects, 621,733 spike-sorted units, 75,708 units classified as good quality, and 241 brain regions included in the analyses, across 12 laboratories.

## Anatomical / spatial coverage

Recordings were systematically collected from nearly all major brain areas using a grid system for sampling. The release reports 241 brain regions recorded in sufficient numbers for inclusion in the analyses.

## Temporal / trial structure

Data were collected across experimental sessions during a decision-making task. The task-associated information includes mouse decisions and response times; the supplied excerpt does not specify the detailed trial timing or session schedule.; Multiple laboratories; Subjects; Experimental sessions; Neuropixels probe insertions; Spike-sorted units; Brain regions; Decision-making task events and behavioral measurements

## Standardization

The data organization follows the standard IBL data structure. The documentation also refers to associated technical descriptions of the experiment and data-processing pipelines.

## Major variables

- Electrophysiological spiking activity
- Sensory stimuli presented during the task
- Mouse decisions
- Response times
- Video-derived mouse pose
- Subject, laboratory, session, probe-insertion, unit, and brain-region organization

## Reuse opportunities

- Brain-wide analyses of neural activity during mouse decision-making
- Comparative analyses across brain regions, subjects, sessions, probe insertions, and laboratories
- Joint study of electrophysiology with task events, decisions, response times, and video-derived pose
- Investigation of cellular-resolution activity patterns across a broad anatomical sampling grid

## Known high-level limitations

- The supplied excerpt does not specify detailed trial timing, preprocessing decisions, or the complete experimental design; these require consultation of the associated dataset article and technical paper.
- The dataset pools recordings from multiple laboratories and uses a sampling grid with replicated recording sites, so branch-specific questions require later verification of the relevant recordings and coverage.
- The excerpt reports regions included in the published analyses but does not establish question-specific joint coverage or feasibility.

## Coarse scale facts

- subjects: 139 subjects
- experimental sessions: 459 Neuropixel experimental sessions
- recording probe insertions: 699 distinct recordings, referred to as probe insertions
- spike-sorted units: 621,733 units, including 75,708 considered good quality
- laboratories: 12 laboratories
- recorded brain regions: 241 brain regions included in the IBL analyses
- task or experimental structure: Mouse decision-making task with sensory stimuli, decisions, and response times
- behavioral and auxiliary measurements: Mouse pose information from video recordings and DeepLabCut analysis, alongside stimuli, decisions, and response times
- public access mode and hierarchy: Released dataset organized according to the standard IBL data structure, with an accompanying visualization website

## Provenance

- Fusion prompt marker: `dataset_narrative_fusion/v1`
- Generator provider(s): `cached-openai:gpt-5.6-luna`
- Source feeds fused: 1

## Review authority

Automated independent-AI fidelity gate dataset_narrative_fidelity_reviewer/v1 (provider anthropic, model claude-opus-4-8) returned accept; reviewer independent of generators ['cached-openai:gpt-5.6-luna'].

## Data basis & limitations

The local sample proves only what is present IN the sample. Absence of a feature in the sample is NOT absence in the full dataset; no joint-coverage across variables is proven; and a property the sample cannot resolve is recorded as insufficient_sample_evidence, never as a dataset mismatch.
- The supplied excerpt does not specify detailed trial timing, preprocessing decisions, or the complete experimental design; these require consultation of the associated dataset article and technical paper.
- The dataset pools recordings from multiple laboratories and uses a sampling grid with replicated recording sites, so branch-specific questions require later verification of the relevant recordings and coverage.
- The excerpt reports regions included in the published analyses but does not establish question-specific joint coverage or feasibility.
