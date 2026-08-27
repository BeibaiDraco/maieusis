# Dataset Narrative — era5-derived-60n-stratospheric-dynamics coarse proposal-stage dataset narrative

- Dataset: `era5-derived-60n-stratospheric-dynamics`
- Review status: `automated_reviewed`

## Scientific purpose

A reanalysis-derived atmospheric-dynamics dataset for studying Northern Hemisphere stratospheric circulation, including zonal-mean circulation, wave activity, a reference-flow diagnostic, and eddy forcing. Its structure supports investigation of recurrent circulation states, state transitions, wave–mean-flow interaction, polar-vortex variability, vertical coupling, dynamical memory, lifecycle asymmetry, recovery, extremes, and historical stability.

## Population

Atmospheric states and dynamics in the Northern Hemisphere stratosphere at a high northern latitude, rather than human or animal participants.

## Task / design

Observational and reanalysis-derived time-series design with repeated observations across the annual cycle over multiple decades. The package separates time-varying analysis fields, a seasonal background, and departures from that background; it is not described as an intervention-based experiment.

## Recording modalities

Vertically resolved time-series information about zonal-mean circulation; Wave activity; Reference-flow diagnostic; Eddy forcing

## Broad scale

Repeated annual-cycle observations spanning multiple decades, with vertical organization and multiple dynamical field categories.

## Anatomical / spatial coverage

Narrow spatial scope focused on Northern Hemisphere stratospheric circulation at a high northern latitude. The supplied description does not provide horizontal or regional structure, surface conditions, or broader atmospheric fields.

## Temporal / trial structure

Repeated observations within the annual cycle across multiple decades, with a seasonal background and departures from that background alongside time-varying fields.

## Standardization

Physical units, equations, sign conventions, calendar mapping, missing-value handling, transformation provenance, and licensing assumptions remain unresolved at proposal stage and require later inspection of the files and supporting documentation.

## Major variables

- Zonal-mean circulation
- Wave activity
- Reference-flow diagnostic
- Eddy forcing
- Seasonal background
- Departures from the seasonal background

## Reuse opportunities

- Study recurrent stratospheric circulation states and state transitions
- Analyze wave–mean-flow interaction and polar-vortex variability
- Investigate vertical coupling, forcing history, dynamical memory, lifecycle asymmetry, and recovery
- Characterize extremes and historical stability across repeated annual cycles

## Known high-level limitations

- The dataset has narrow spatial scope and does not provide horizontal or regional structure.
- It lacks surface conditions and the wider atmospheric fields needed by itself for regional impacts, wave-source geography, topographic effects, or external climate attribution.
- Physical units, equations, sign conventions, calendar mapping, missing-value handling, transformation provenance, and licensing assumptions require later verification.
- The dataset constrains possible operationalizations but does not establish that a proposed relationship or mechanism is true.

## Coarse scale facts

- temporal_extent: Multiple decades of repeated observations within the annual cycle.
- recording_units_or_sensors: Vertically resolved atmospheric time-series fields covering several broad dynamical quantities; no sensor or channel count is stated.
- task_or_experimental_structure: Repeated annual-cycle observations organized into time-varying fields, a seasonal background, and departures from that background.
- public_access_mode_and_hierarchy: The supplied description identifies a package with three broad data components—time-varying analysis fields, a seasonal background, and departures—but does not state its public access mode.

## Provenance

- Fusion prompt marker: `dataset_narrative_fusion/v1`
- Generator provider(s): `cached-openai:gpt-5.6-luna`
- Source feeds fused: 1

## Review authority

Automated independent-AI fidelity gate dataset_narrative_fidelity_reviewer/v2 (provider anthropic, model claude-sonnet-5, session narrative_fidelity-review) returned accept; reviewer independent of generators ['cached-openai:gpt-5.6-luna'].

## Data basis & limitations

The local sample proves only what is present IN the sample. Absence of a feature in the sample is NOT absence in the full dataset; no joint-coverage across variables is proven; and a property the sample cannot resolve is recorded as insufficient_sample_evidence, never as a dataset mismatch.
- The dataset has narrow spatial scope and does not provide horizontal or regional structure.
- It lacks surface conditions and the wider atmospheric fields needed by itself for regional impacts, wave-source geography, topographic effects, or external climate attribution.
- Physical units, equations, sign conventions, calendar mapping, missing-value handling, transformation provenance, and licensing assumptions require later verification.
- The dataset constrains possible operationalizations but does not establish that a proposed relationship or mechanism is true.
