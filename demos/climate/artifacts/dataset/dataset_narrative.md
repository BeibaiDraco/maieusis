# Dataset Narrative — era5-derived-60n-stratospheric-dynamics coarse proposal-stage dataset narrative

- Dataset: `era5-derived-60n-stratospheric-dynamics`
- Review status: `automated_reviewed`

## Scientific purpose

Reanalysis-derived dataset for studying Northern Hemisphere stratospheric circulation and atmospheric dynamics, including circulation states, wave–mean-flow interaction, polar-vortex variability, vertical coupling, forcing history, dynamical memory, lifecycle asymmetry, recovery, extremes, and historical stability.

## Population

Atmospheric states of the Northern Hemisphere stratosphere at a high northern latitude, rather than human or animal participants.

## Task / design

Longitudinal observational/reanalysis design with repeated observations across the annual cycle over multiple decades. The package separates time-varying analysis fields, a seasonal background, and departures from that background.

## Recording modalities

Vertically resolved time-series information; Zonal-mean circulation; Wave activity; Reference-flow diagnostic; Eddy forcing

## Broad scale

Multi-decade atmospheric time series with repeated observations within annual cycles and vertical organization; exact record counts and dimensional scale are not specified in the supplied excerpt.

## Anatomical / spatial coverage

Narrow atmospheric spatial scope focused on Northern Hemisphere stratospheric circulation at a high northern latitude. The package does not provide horizontal or regional structure, surface conditions, or the wider atmospheric fields required for regional-impact, wave-source-geography, topographic-effect, or external-climate-attribution studies by itself.

## Temporal / trial structure

Repeated observations within the annual cycle across multiple decades, with seasonal background structure and departures from that background.; Multi-decade record; Annual-cycle and seasonal structure; Time-varying analysis fields; Seasonal background; Departures from seasonal background; Vertical organization

## Standardization

The package is described as reanalysis-derived, but physical units, equations, sign conventions, calendar mapping, missing-value handling, transformation provenance, and licensing assumptions remain unresolved at proposal stage and require later inspection of the files and documentation.

## Major variables

- Zonal-mean circulation
- Wave activity
- Reference-flow diagnostic
- Eddy forcing
- Seasonal background
- Departures from seasonal background
- Vertical structure
- Circulation states and transitions
- Polar-vortex variability
- Forcing history
- Recovery and extreme-event behavior

## Reuse opportunities

- Study recurrent circulation states and state transitions
- Examine wave–mean-flow interaction and vertical coupling
- Characterize polar-vortex variability, lifecycle asymmetry, recovery, and extremes
- Investigate forcing history, dynamical memory, and historical stability
- Develop multi-decade analyses of seasonal atmospheric dynamics

## Known high-level limitations

- The dataset has narrow spatial scope and lacks horizontal or regional structure.
- It lacks surface conditions and the broader atmospheric fields needed for regional impacts, wave-source geography, topographic effects, or external climate attribution by itself.
- Physical units, equations, sign conventions, calendar mapping, missing-value handling, transformation provenance, and licensing assumptions are unresolved in the supplied proposal-stage description.
- The package can constrain later operationalization but does not establish that a proposed relationship or mechanism is true.
- Exact question-specific coverage and feasibility require later inspection of read-only files and supporting documentation.

## Coarse scale facts

- temporal_extent_and_sampling_structure: Repeated observations within the annual cycle across multiple decades
- measurement_structure: Vertically resolved time-series information
- measurement_site_or_region: Northern Hemisphere stratospheric circulation at a high northern latitude
- public_dataset_hierarchy: Time-varying analysis fields, a seasonal background, and departures from that background
- access_mode: Read-only files and supporting documentation are intended for later planner inspection; licensing assumptions remain unresolved

## Provenance

- Fusion prompt marker: `dataset_narrative_fusion/v1`
- Generator provider(s): `cached-openai:gpt-5.6-luna`
- Source feeds fused: 1

## Review authority

Automated independent-AI fidelity gate dataset_narrative_fidelity_reviewer/v1 (provider anthropic, model claude-sonnet-5, session narrative_fidelity-review) returned accept; reviewer independent of generators ['cached-openai:gpt-5.6-luna'].

## Data basis & limitations

The local sample proves only what is present IN the sample. Absence of a feature in the sample is NOT absence in the full dataset; no joint-coverage across variables is proven; and a property the sample cannot resolve is recorded as insufficient_sample_evidence, never as a dataset mismatch.
- The dataset has narrow spatial scope and lacks horizontal or regional structure.
- It lacks surface conditions and the broader atmospheric fields needed for regional impacts, wave-source geography, topographic effects, or external climate attribution by itself.
- Physical units, equations, sign conventions, calendar mapping, missing-value handling, transformation provenance, and licensing assumptions are unresolved in the supplied proposal-stage description.
- The package can constrain later operationalization but does not establish that a proposed relationship or mechanism is true.
- Exact question-specific coverage and feasibility require later inspection of read-only files and supporting documentation.
