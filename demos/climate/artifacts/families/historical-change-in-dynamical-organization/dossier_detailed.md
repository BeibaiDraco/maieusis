# Historical change in state occupancy versus within-state dynamics — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Mixed family: accepted and non-accepted sibling variants**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Decomposes multi-decade circulation change into changes in how often and how long states occur versus changes in the vertical and forcing structure expressed within comparable states.

The scientific tension is:

Historical circulation change may arise from redistribution among familiar dynamical states, alteration of the states themselves, or nonphysical inhomogeneity; aggregate change cannot distinguish these possibilities.

## How to read this mixed family

Accepted and non-accepted sibling variants coexist here. Authority applies only to the variants explicitly marked as reviewed and accepted; it does not spill across the family.

## Variant 1: Stable-repertoire pathway reorganization beyond state prevalence and duration

### Why it matters

Separating pathway reorganization from state prevalence and duration would clarify whether multi-decadal polar-stratospheric change concerns how a familiar repertoire is navigated, rather than merely how often weak-vortex conditions occur. Keeping the estimand within the polar stratosphere also avoids treating downstream weather impacts as evidence for the historical circulation change itself.

### Original and refined question

**Original Question Scientist proposal**

Across the multi-decade record, is historical change in polar-stratospheric circulation expressed primarily through altered occupancy, persistence, or transition pathways among recurrent states?

**Post-novelty revised proposal**

Within an objectively derived polar-stratospheric repertoire spanning recurrent differences in vortex strength, morphology, and vertical organization, is the repertoire structurally stable across historical periods, and do changes in state-to-state pathways carry historical circulation information beyond changes in state occupancy and duration?

**Reviewed refined question**

Within a reproducibly derived repertoire from the documented vertical fawa, ubar, uref, and epz profile representation, are states comparable across prespecified historical periods, and do conditional state-to-state pathways differ after occupancy and duration are represented?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the multi-decade record supports comparable representations across broad periods, repeated polar-stratospheric observations may permit evaluation of repertoire stability and separate comparisons of occupancy, state-duration distributions, and state-to-state pathway organization. This remains contingent on documentation and record-consistency assessment.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The package is described as vertically resolved time-series information at a high northern latitude and is explicitly described as lacking horizontal or regional structure. The documented separation of analysis fields, seasonal background, and departures provides temporal and vertical representations but not fields from which horizontal displacement or deformation can be estimated.
  - Limitation: The descriptive source is intentionally coarse and does not document variable units or dates.
  - Limitation: The absence statement establishes a dataset-scope limitation, not a claim about atmospheric dynamics.
  - Limitation: No scientific outcome, state classification, or historical contrast was inspected.
- **Unverified planning evidence:** The supplied context describes ana60n as full analysis fields, tran60n as transient anomalies, and sea60n as a seasonal climatology, each with fawa, ubar, uref, and epz. It describes these variables respectively as a wave-activity or pseudomomentum diagnostic, zonal-mean wind or polar-vortex diagnostic, reference zonal wind with radiative driving, and an eddy-forcing diagnostic.
  - Limitation: This is an operator-supplied description rather than metadata encoded in the NetCDF files.
  - Limitation: Units, signs, transformations, missing-value conventions, and exact calendar semantics remain undocumented.
  - Limitation: The descriptions support planning constructs only and do not establish physical-budget interpretation or any scientific result.
- **Unverified planning evidence:** The report verifies that ana60n and tran60n each contain contiguous float32 fawa, ubar, uref, and epz arrays with fixed dimensions (height=97, time=124, month=12, year=43), while sea60n has the same variables with (height=97, time=124, month=12) and no year dimension. The files have no user-visible global or variable attributes.
  - Limitation: The structural report establishes encoded dimensions and variable names, not the scientific meaning of the variables.
  - Limitation: No user-visible coordinate values, units, fill values, calendar mapping, or transformation provenance are encoded.
  - Limitation: This planning inspection did not read or summarize target-array values.

### Plan at a glance

- Population and scope: All valid, documented six-hourly nominal slots in prespecified Northern Hemisphere stratospheric seasonal windows across the 43 indexed years in ana60n and tran60n. Historical period labels are contingent on verified year coordinates; no external attribution or downstream-impact population is included.
- Unit of observation: A valid multivariate vertical-profile time slot represented by the four fields, with month and year retained as design variables.
- Unit of inference: Historical-period contrast at the year or season-year block, with within-block profile observations treated as serially dependent rather than independent replicates.
- Hierarchy and dependence: Profiles are nested in within-month slots, months, and years. State estimation will use blocked resampling by contiguous season-year blocks; transition inference will cluster or bootstrap at the year/season-year level and preserve observed valid adjacency.
- Validation: Use synthetic recovery experiments with known occupancy-only, duration-only, and conditional-transition changes to verify that the chosen estimator distinguishes these mechanisms. Use blocked out-of-period assignment and resampled state correspondence to assess whether a stable repertoire is defensible before estimating the target pathway contrast.
- Split strategy: Hold out complete contiguous season-year blocks for representation stability and use nonoverlapping year-blocked resampling for uncertainty. Never randomly split adjacent time slots across training and validation.
- Claim ceiling: associational

**Analysis strategy**

1. Before comparison, document coordinate values, calendar semantics, fill values, and allowed transitions; exclude or explicitly model undefined slots and never manufacture adjacency across undocumented gaps.
2. Define a preprocessing protocol from a reference or pooled training period without using the historical pathway contrast: standardize fields within documented seasonal strata, retain the full vertical profile, and conduct sensitivity to analysis versus transient representation.
3. Derive a repertoire using a prespecified family of unsupervised or latent-state representations that jointly retains vortex-wind, wave-activity, reference-flow, eddy-forcing, and vertical-organization information; select complexity by held-out reconstruction and stability criteria rather than period separation.
4. 3 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permuted period labels within matched seasonal and year-block strata to verify that the transition procedure does not create a period signal by construction.; Synthetic occupancy-only and duration-only changes, for which the conditional pathway estimand should remain null under the recovery protocol.
- Positive controls: Synthetic injected conditional-transition change with stable occupancy and duration, which the method should recover without changing state correspondence.; The documented seasonal background structure as a check that seasonal stratification is represented, not as evidence of historical change.
- Alternative explanations: Changing occupancy of familiar states without conditional pathway reorganization.; Changed spell duration or persistence that mechanically alters transition counts.; plus 3 additional item(s) in the complete dossier

**Interpretation limits**

- The package contains no encoded units, signs, calendar mapping, fill-value conventions, or processing provenance, so physical mechanisms cannot be inferred until those metadata are verified.
- Observational reanalysis-derived profiles can describe period-associated organization but cannot attribute change to external forcing or establish causality.
- The 60 degrees North vertical-only representation cannot establish horizontal circulation morphology or downstream impacts.

**Why the plan serves the question**

The plan preserves the variant's required distinction between a period-stable repertoire, occupancy, duration, and conditional pathways. It does not substitute weak-state frequency or persistence for pathway organization, and it makes state comparability, seasonality, and record inhomogeneity explicit gates and competing explanations.

**Before any later execution**

- Unresolved planning decisions: Exact date and season-year mapping, including padded-day and cross-boundary adjacency rules.; Verified units, sign conventions, field transformations, and missing-data coding.; plus 1 additional item(s) in the complete dossier
- Required future skills: A NetCDF-aware, planning-firewall-compliant executor for multivariate vertical-profile state discovery and cross-period state correspondence.; A dependence-aware conditional transition and dwell-time modeling workflow with blocked resampling and synthetic method recovery.

### Scientific stakes

**Discriminating observation**

A pathway-reorganization interpretation would be favored only if the objectively derived polar-stratospheric repertoire remains structurally comparable across historical periods and period differences in state-to-state pathways persist after accounting for period differences in occupancy and state duration, including weak-state frequency and persistence. If the inferred differences instead change materially with state definition, seasonal composition, or plausible record discontinuities, those explanations would compete directly with a physical redistribution claim.

**What possible outcomes would mean**

- Positive pattern: Evidence for a stable repertoire together with pathway differences not explained by occupancy or duration would frame historical polar-stratospheric change as altered navigation among familiar dynamical states, independently of any downstream surface-temperature or weather-regime effect.
- Negative pattern: If stable states are recovered but pathway differences disappear after accounting for occupancy and duration, the historical account would reduce to changing prevalence or persistence rather than independent transition reorganization.
- Null or ambiguous pattern: If repertoire stability cannot be established or historical contrasts remain inseparable from state-definition sensitivity, seasonal composition, or record inhomogeneity, no determinate historical redistribution claim would follow; the scientific priority would shift to state comparability and record consistency.

## Variant 2: Reference-anchored, deformation-aware within-state dynamical residual test

### Why it matters

Separating population redistribution and horizontal structural evolution from a linked multi-diagnostic residual would clarify whether historical change merely changes the use or shape of familiar states or modifies the dynamical relationships operating within them.

### Original and refined question

**Original Question Scientist proposal**

Within comparable circulation states, is multi-decade change congruent with the established state structure, or does it contain systematic residual changes in vertical organization, wave activity, or eddy forcing?

**Post-novelty revised proposal**

After anchoring circulation states to reference-period definitions and matching later instances while allowing horizontal displacement or deformation, does multi-decade change leave a coherent within-state linkage among vertical circulation, wave activity, and eddy forcing once changes in occupancy, transitions, horizontal structure, and seasonal background are separated?

**Refined-question status**

No refined question earned accepted-plan authority for this sibling.

**Reviewed planning disposition**

Rejected because the inspected dataset did not support the required design. The required separation of horizontal displacement or deformation from within-state dynamical residuals is unavailable in a vertical-only 60 degrees North package with no horizontal or regional coordinate. Replacing that component with vertical structure would alter the protected discriminating observation.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the multi-decade package supports consistent state matching and complementary dynamical descriptions, its temporal fields, seasonal backgrounds, departures, and multiple diagnostic perspectives may allow a later planner to distinguish state-population change, matched horizontal-pattern evolution, and residual within-state dynamical organization.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The package is described as vertically resolved time-series information at a high northern latitude and is explicitly described as lacking horizontal or regional structure. The documented separation of analysis fields, seasonal background, and departures provides temporal and vertical representations but not fields from which horizontal displacement or deformation can be estimated.
  - Limitation: The descriptive source is intentionally coarse and does not document variable units or dates.
  - Limitation: The absence statement establishes a dataset-scope limitation, not a claim about atmospheric dynamics.
  - Limitation: No scientific outcome, state classification, or historical contrast was inspected.
- **Unverified planning evidence:** The report verifies that ana60n and tran60n each contain contiguous float32 fawa, ubar, uref, and epz arrays with fixed dimensions (height=97, time=124, month=12, year=43), while sea60n has the same variables with (height=97, time=124, month=12) and no year dimension. The files have no user-visible global or variable attributes.
  - Limitation: The structural report establishes encoded dimensions and variable names, not the scientific meaning of the variables.
  - Limitation: No user-visible coordinate values, units, fill values, calendar mapping, or transformation provenance are encoded.
  - Limitation: This planning inspection did not read or summarize target-array values.

### Scientific stakes

**Discriminating observation**

Support for altered internal dynamics would require later instances matched to reference-period state anchors—while explicitly permitting horizontal displacement or deformation—to retain reproducible residual changes after accounting separately for occupancy and transition frequencies, seasonal background, state-congruent amplitude, and horizontal structural evolution. Those residuals must jointly indicate a physically coherent linkage among vertical circulation, wave activity, and eddy forcing; displacement of a regime center, changed classification, or an isolated diagnostic residual would not suffice.

**What possible outcomes would mean**

- Positive pattern: A coherent linked residual across vertical circulation, wave activity, and eddy forcing would support the interpretation that multi-decade change alters dynamics within matched states rather than being exhausted by redistribution, reassignment, amplitude change, or horizontal pattern evolution.
- Negative pattern: If historical differences are absorbed by occupancy or transition changes and by matched horizontal displacement, deformation, or amplitude change, with no coherent linked residual, the evidence would favor redistribution or structural evolution of familiar states rather than altered within-state dynamics.
- Null or ambiguous pattern: If state matching is unstable or the residual diagnostics are weak, inconsistent, or sensitive to representation, no within-state dynamical-change claim would be supported; the result would remain ambiguous among limited physical change, classification sensitivity, and record or diagnostic inhomogeneity.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family plan preserves the separation between redistribution/pathway organization and within-state dynamics. Variant 1 has a credible associational, dependence-aware route with explicit state-comparability gates and safeguards against conflating pathways with occupancy or duration. Variant 2 is honestly rejected because the supplied vertical-only evidence cannot represent its required horizontal displacement or deformation contrast.

Retained changes and locks:

- **Pre execution lock:** Before execution, lock the time-coordinate, calendar, padding/gap, missing-value, and valid-adjacency conventions, together with historical period and seasonal-window definitions.
- **Pre execution lock:** Before execution, verify variable units, signs, transformations, and provenance before assigning physical meaning to the multivariate profile fields.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family plan is scientifically sound at the planning stage. Variant 1 (occupancy/transition-pathway change) offers a credible, associational plan that explicitly separates a period-stable repertoire from occupancy, duration, and conditional-pathway components, with pre-registered comparability gates, alternative explanations, positive/negative controls, and synthetic recovery checks that guard against conflating pathway change with occupancy or duration change. Variant 2 is honestly rejected because the vertical-only, no-horizontal-coordinate dataset cannot support its required displacement/deformation contrast, and the rejection does not substitute a different discriminating observation. Per family-level review guidance, one evidence-backed accepted variant plus an honest non-pending sibling outcome is sufficient; the family need not be rejected because one sibling fails on dataset grounds. The Owner's two required changes are correctly scoped as pre-execution documentation locks (time/calendar/adjacency conventions; variable unit/sign/provenance verification) rather than scientific blockers, since the plan already treats these as gates rather than inferring them from outcomes. No hard-boundary or scientific-intent drift is present, and sibling separation between redistribution-among-states and within-state structural change is preserved.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
