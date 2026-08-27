# Wave forcing versus vortex susceptibility before rapid weakening — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Scientific rejection terminal**
- Authority: **Automated host authorization, planning only; no independent review was recorded**
- Accepted-plan authority: **No**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether rapid polar-vortex weakening is organized mainly by anomalous wave forcing or by the susceptibility of the pre-existing stratospheric state. The two variants separate event-level precursor discrimination from a state-conditioned response comparison.

The scientific tension is:

Upward planetary-wave forcing is central to vortex variability, but the literature remains divided over whether unusually strong forcing or a preconditioned, receptive vortex state better distinguishes rapid weakening episodes.

## How to read this terminal

The scientific planning/review process closed this family without an accepted plan. Rejection is a scientific terminal, not evidence that the proposed phenomenon is false.

**Recorded public status note**

automated_reject

## Variant 1: Joint, regime-conditioned event-versus-control precursor discrimination

### Why it matters

A joint event-and-control comparison would show whether forcing and state offer incremental, regime-portable observational information rather than merely recurring before events. This would refine precursor interpretation while avoiding causal claims and explicitly accounting for false positives and event heterogeneity.

### Original and refined question

**Original Question Scientist proposal**

Do histories of anomalous wave activity and eddy forcing distinguish rapid polar-vortex weakening episodes more consistently than histories of the pre-existing zonal-mean circulation?

**Post-novelty revised proposal**

Across split-like, displacement-like, and other rapid Arctic polar-vortex weakening regimes, does antecedent upward planetary-wave flux provide incremental observational discrimination of threshold-defined weakening versus matched non-weakening windows beyond the antecedent vortex state, and does either precursor retain discrimination when conditioning on the other?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If documentation confirms suitable temporal and vertical coverage, repeated circulation and wave diagnostics may support aligned antecedent histories for qualifying weakening windows and matched non-weakening controls, separate representation of wave generation, upward transmission, and stratospheric drag, and morphology-conditioned comparison. Coverage and feasibility are not established at this stage.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The package is described as a 60 degrees North one-dimensional vertical-grid product with ana60n, sea60n, and tran60n files and four fields: fawa, ubar, uref, and epz. The document explicitly states that it has no longitude or latitude dependence and cannot by itself support regional or wave phase structure questions. It also states that the NetCDF files lack user-visible units, long names, calendar semantics, fill-value conventions, and transformation provenance.
  - Limitation: This is operator-supplied context rather than independent dataset-owner documentation.
  - Limitation: The description does not establish the physical definition, sign, pressure-equivalent level, or wavenumber decomposition of epz or fawa.
  - Limitation: The inspection was planning-only and did not inspect raw data values.
- **Unverified planning evidence:** ana60n.nc, sea60n.nc, and tran60n.nc are HDF5-backed NetCDF files. The bounded schema surface exposes height and time-structure labels plus field labels including fawa and uref; the documentation, rather than file metadata, remains the authoritative available source for the complete field and dimensional interpretation because no readable user-visible descriptive metadata was available through the configured inspection environment.
  - Limitation: This bounded structural inspection cannot verify absent variables from embedded strings alone.
  - Limitation: No raw arrays, event outcomes, or scientific diagnostics were inspected.
  - Limitation: A NetCDF-capable reader and source metadata would be required to verify dimensions, units, signs, levels, and missing-value conventions.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

Define a rapid-weakening case provisionally as a decrease of at least 1.5 calendar-day standard deviations in 60°N, 10-hPa zonal-mean zonal wind within 10 consecutive days, with onset assigned to the first endpoint completing that decline; test sensitivity to alternative thresholds and durations. Compare cases with eligible boreal-winter 10-day windows that do not meet the threshold and are matched, where support permits, on calendar timing and starting vortex strength, retaining near-misses so false-positive behavior is represented. The primary forcing construct is the 45°–75°N zonal-mean meridional eddy heat flux at 100 hPa, aggregated over days −20 to −1 and expressed relative to a calendar-day baseline. Treat lower-tropospheric eddy forcing near 300 hPa, upward Eliassen–Palm flux crossing 100 hPa, and Eliassen–Palm-flux divergence or wave drag within 100–10 hPa as separate pathway diagnostics rather than interchangeable measures. Contrast forcing with an antecedent-state construct formed independently of the outcome from vortex strength, horizontal geometry, vertical coherence or tilt, and waveguide- or resonance-relevant reference-flow configuration over days −30 to −1. A forcing-dominant observational pattern requires upward flux to retain case-control separation within comparable state strata; a susceptibility-dominant pattern requires state to retain separation within comparable forcing strata. Evaluate these patterns separately for split-like, displacement-like, and other qualifying weakening events. Reciprocal or reversed separation across regimes indicates regime dependence, whereas lack of separation within each regime indicates no supported discriminator under the tested definitions.

**What possible outcomes would mean**

- Positive pattern: If upward flux adds reproducible case-control separation after conditioning on antecedent state and retains the same meaning across morphology strata, anomalous upward transmission would be supported as the more portable observational discriminator, without establishing that it causally triggers weakening.
- Negative pattern: If multidimensional antecedent state retains separation within comparable upward-flux histories while forcing does not retain separation within comparable states, the evidence would favor susceptibility as the stronger observational discriminator. If the direction differs between split-like and displacement-like events, the consequence would instead be a regime-dependent precursor interpretation rather than universal state dominance.
- Null or ambiguous pattern: If neither forcing nor state separates weakening from controls within the morphology strata, the tested precursor families would lack supported incremental discrimination under these definitions. If pooled discrimination disappears but distinct within-regime relationships remain, the result would indicate aggregation across mechanisms rather than absence of both precursor signals.

## Variant 2: Matched-entry-forcing susceptibility response

### Why it matters

Separating variation in entering wave forcing from variation in the response to comparable forcing would clarify whether preconditioning is merely an event-associated marker or an effect modifier of wave–mean-flow response.

### Original and refined question

**Original Question Scientist proposal**

Does the subsequent vortex response to comparable wave-forcing episodes differ systematically between initially susceptible and resistant stratospheric circulation states?

**Post-novelty revised proposal**

At comparable lower-stratospheric planetary-wave forcing, does a pre-forcing vortex/reference-flow state modify the amplitude and rate of subsequent polar-vortex weakening, independently of its association with sudden-stratospheric-warming occurrence?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If temporally aligned reference-flow, planetary-wave, and zonal-mean circulation histories are available, a later planner may be able to classify states from a pre-forcing window, identify comparable entering-forcing episodes, and compare subsequent weakening. Joint coverage, variable definitions, and precision remain unverified.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The package is described as a 60 degrees North one-dimensional vertical-grid product with ana60n, sea60n, and tran60n files and four fields: fawa, ubar, uref, and epz. The document explicitly states that it has no longitude or latitude dependence and cannot by itself support regional or wave phase structure questions. It also states that the NetCDF files lack user-visible units, long names, calendar semantics, fill-value conventions, and transformation provenance.
  - Limitation: This is operator-supplied context rather than independent dataset-owner documentation.
  - Limitation: The description does not establish the physical definition, sign, pressure-equivalent level, or wavenumber decomposition of epz or fawa.
  - Limitation: The inspection was planning-only and did not inspect raw data values.
- **Unverified planning evidence:** ana60n.nc, sea60n.nc, and tran60n.nc are HDF5-backed NetCDF files. The bounded schema surface exposes height and time-structure labels plus field labels including fawa and uref; the documentation, rather than file metadata, remains the authoritative available source for the complete field and dimensional interpretation because no readable user-visible descriptive metadata was available through the configured inspection environment.
  - Limitation: This bounded structural inspection cannot verify absent variables from embedded strings alone.
  - Limitation: No raw arrays, event outcomes, or scientific diagnostics were inspected.
  - Limitation: A NetCDF-capable reader and source metadata would be required to verify dimensions, units, signs, levels, and missing-value conventions.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

Define susceptible and resistant categories before forcing onset from vortex-local zonal-mean wind, vortex-edge or reference-flow gradient, and vertical-shear properties; exclude all subsequent weakening variables and do not define categories by ENSO, QBO, or other remote modes. Treat episodes as comparable only when upward planetary-wave activity entering the lower stratosphere—provisionally the eddy heat-flux or equivalent Eliassen–Palm-flux quantity at a nominal 100-hPa entry level during a prespecified several-day pre-response window—is balanced in amplitude, temporal concentration, and wave-1/wave-2 structure, subject to verification of available variables and levels. Evidence for susceptibility requires both greater weakening amplitude and a faster weakening rate in the hypothesized susceptible state; vertical coherence across available stratospheric levels is corroborating rather than required. A state difference in entry forcing supports an altered-forcing account, not the claimed matched-forcing mechanism.

**What possible outcomes would mean**

- Positive pattern: A stable, directionally consistent increase in both weakening amplitude and weakening rate for the pre-defined susceptible state under comparable entering forcing would support effect modification by the initial vortex/reference flow. Additional vertical coherence would strengthen, but is not necessary for, that interpretation.
- Negative pattern: A stable reverse contrast, in which the state labeled resistant weakens more strongly and rapidly under comparable entering forcing, would challenge the proposed susceptibility classification and motivate a different account of how reference-flow properties regulate wave–mean-flow response.
- Null or ambiguous pattern: A precise, stable absence of conditional differences in both amplitude and rate across reasonable state and forcing definitions would weaken the susceptibility account and favor a more direct forcing–response interpretation. Wide uncertainty, sensitivity to matching choices, or opposing event-subclass responses would instead be treated as unresolved rather than as evidence of no effect modification.

## Owner and independent review

### Question Owner

No safely resolved typed review statement was available for this view.

### Independent reviewer

No safely resolved typed review statement was available for this view.

A missing review is shown as unavailable rather than inferred from planner prose or the family status.

**Authority reminder:** these dispositions do not yield an accepted plan here.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
