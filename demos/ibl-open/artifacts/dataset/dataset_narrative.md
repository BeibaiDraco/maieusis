# Dataset Narrative — ibl_bwm coarse proposal-stage dataset narrative

- Dataset: `ibl_bwm`
- Review status: `automated_reviewed`

## Scientific purpose

The dataset supports construction of a whole-brain activity map to study the neural basis of decision-making in the mouse, using pooled electrophysiological recordings from multiple laboratories.

## Population

Mice performing the IBL decision-making task; the release includes data from 139 subjects across 12 laboratories.

## Task / design

A multi-laboratory, brain-wide electrophysiological recording study conducted during a mouse decision-making task. Sensory stimuli, decisions, response times, and video-derived pose information were collected alongside neural recordings.

## Recording modalities

Electrophysiological recordings with Neuropixels probes; Spike-sorted neural activity; Sensory-stimulus measurements; Behavioral decisions and response times; Video recordings with DeepLabCut-derived pose information

## Broad scale

The release contains hundreds of experimental sessions and probe-insertion recordings from over one hundred mice and multiple laboratories, with hundreds of thousands of spike-sorted units and coverage of hundreds of brain regions.

## Anatomical / spatial coverage

The study systematically recorded from nearly all major mouse brain areas using a grid system intended to support unbiased sampling and replication of recording sites across laboratories. The documentation reports 241 brain regions included in the analyses.

## Temporal / trial structure

Recordings were collected during task sessions and include neural activity aligned with sensory stimuli, mouse decisions, response times, and behavioral video measurements.

## Standardization

The data were collected using a standardized IBL task and organized according to the standard IBL data structure. Recording sites were sampled with a grid system, and each site was replicated in at least two laboratories. The documentation also refers to associated data-processing pipelines and a technical paper for further details.

## Major variables

- Neural spiking activity
- Sensory stimuli
- Mouse decisions
- Response times
- Mouse pose and movement
- Brain-region identity
- Laboratory and subject context
- Session and probe-insertion context

## Reuse opportunities

- Brain-wide analysis of neural activity during decision-making
- Comparison of activity across major brain regions
- Cross-laboratory and cross-subject comparisons
- Joint analysis of electrophysiological, behavioral, stimulus, and pose measurements
- Investigation of relationships between neural activity, decisions, response times, and movement

## Known high-level limitations

- The supplied documentation excerpt refers readers to an associated article and technical paper for detailed experiment and data-processing information; those details are not specified in this excerpt.

## Coarse scale facts

- subjects or participants: 139 mouse subjects
- sessions or recordings: 459 experimental sessions
- recording units, channels, or sensors: 699 probe-insertion recordings
- recording units, channels, or sensors: Over six hundred thousand spike-sorted units, including tens of thousands classified as good quality
- measurement sites or regions: 241 brain regions
- task or experimental structure: A standardized mouse decision-making task with brain-wide Neuropixels recordings pooled across 12 laboratories and recording sites replicated across at least two laboratories
- behavioral or auxiliary measurements: Sensory stimuli, mouse decisions, response times, and video-derived mouse pose information
- public access mode and hierarchy: Publicly released data organized in the standard IBL data structure, with an accompanying visualization website; the release is organized across laboratories, subjects, sessions, probe insertions, units, and brain regions

## Provenance

- Fusion prompt marker: `dataset_narrative_fusion/v1`
- Generator provider(s): `cached-openai:gpt-5.6-luna`
- Source feeds fused: 1

## Review authority

Automated independent-AI fidelity gate dataset_narrative_fidelity_reviewer/v2 (provider anthropic, model claude-sonnet-5, session narrative_fidelity-review) returned accept; reviewer independent of generators ['cached-openai:gpt-5.6-luna'].

## Data basis & limitations

The local sample proves only what is present IN the sample. Absence of a feature in the sample is NOT absence in the full dataset; no joint-coverage across variables is proven; and a property the sample cannot resolve is recorded as insufficient_sample_evidence, never as a dataset mismatch.
- The supplied documentation excerpt refers readers to an associated article and technical paper for detailed experiment and data-processing information; those details are not specified in this excerpt.
