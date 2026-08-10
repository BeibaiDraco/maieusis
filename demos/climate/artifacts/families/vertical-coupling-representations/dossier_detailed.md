# Propagating episodes versus coherent modes of vertical coupling — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Compares event-first and continuous-mode accounts of coupling across stratospheric heights while treating agreement among diagnostics as evidence to test rather than assume.

The scientific tension is:

Vertical coupling may occur as temporally ordered propagation during discrete episodes, or as a continuously coherent mode spanning heights; either appearance could depend on the chosen representation.

## Variant 1: Event-first, state-conditioned test of level-resolved sequential coupling across transient ordinary and persistent extreme circulation episodes

### Why it matters

An event-first, level-resolved comparison can distinguish a predictive vertical sequence from a final tropospheric-response label and test whether episode persistence changes the organization of coupling across the full amplitude range. It also clarifies when an absent lower-level signal reflects failed sequencing versus masking by antecedent circulation.

### Original and refined question

**Original Question Scientist proposal**

When upper-stratospheric circulation or wave episodes are defined independently, do lower-stratospheric responses recur with consistent lagged vertical progression, and does that progression differ between ordinary and extreme episodes?

**Post-novelty revised proposal**

Among independently identified upper-stratospheric circulation episodes, do transient ordinary reorganizations and persistent extreme anomalies produce different level-by-level trajectories from the upper stratosphere through the lower stratosphere toward the troposphere, after accounting for preexisting lower-level circulation/PV structure and excluding seasonally expected persistence and near-simultaneous barotropic adjustment?

**Reviewed refined question**

Among independently selected upper-level ubar reorganizations, do persistent tail anomalies and isolated transient non-tail reorganizations have different state-conditioned, level-by-level nominal-time trajectories through the resolved vertical column after seasonality, autocorrelation, and near-simultaneous coherence are addressed?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the vertically resolved record contains compatible upper-stratospheric circulation measures and level-resolved circulation or PV descriptions below, it may support independent episode selection, reconstruction of intermediate vertical trajectories, and conditioning on antecedent lower-level state. Exact vertical coverage and timing compatibility remain to be verified.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The analysis and transient files each contain contiguous float32 fawa, ubar, uref, and epz arrays on fixed height=97, time=124, month=12, year=43 dimensions in (height, time, month, year) order. This supports level-resolved, repeated-observation episode definitions and antecedent circulation controls, but the files have no user-visible units, calendar semantics, fill-value convention, or variable attributes.
  - Limitation: This is a planning-only structural report and does not establish physical signs, units, or scientific effects.
  - Limitation: The report establishes no potential-vorticity field and no exact date or padded-day mapping.
- **Unverified planning evidence:** The supplied context describes a one-dimensional 60 degrees North, 97-level vertical grid from 0 to 48 km at 500 m spacing, nominal six-hourly slots across 12 months and approximately 43 years. It labels ubar as a zonal-mean wind perturbation or polar-vortex wind diagnostic, uref as a reference zonal wind, fawa as finite-amplitude wave activity, and epz as eddy forcing. It also explicitly states that potential vorticity is absent.
  - Limitation: Variable meanings, sign conventions, units, transformation provenance, and exact time/calendar mapping are operator-supplied rather than file-encoded metadata.
  - Limitation: No longitude, latitude, temperature, geopotential-height, surface, or potential-vorticity fields are available.

### Plan at a glance

- Population and scope: The available population is approximately 43 years of repeated nominal six-hourly observations at 60 degrees North across a 97-level 0-to-48-km vertical column; inference is limited to this reanalysis-derived one-dimensional diagnostic record.
- Unit of observation: A height-resolved nominal-time observation within a year-month-slot lattice.
- Unit of inference: A non-overlapping independently selected upper-level episode, with year-aware resampling to retain within-winter dependence.
- Hierarchy and dependence: Model height-by-lag responses nested within episodes and winters; block or cluster resampling by winter/year and enforce non-overlapping episode windows. Do not treat adjacent slots or heights as independent samples.
- Validation: Before execution, verify NetCDF dimension order, height coordinates, anomaly relation, temporal adjacency across month boundaries, missingness, and sign convention. Recover known timing from synthetic multilevel trajectories and confirm that the estimator separates sequential, simultaneous, and autocorrelated-but-nonsequential cases without tuning on target episodes.
- Split strategy: Use blocked resampling or cross-fitting by complete winter/year; derive episode thresholds and trajectory rules in a prespecified development partition and evaluate them in held-out winters, with no split based on downstream response.
- Claim ceiling: associational

**Analysis strategy**

1. Define the upper stratospheric band from documented height coordinates after loader validation; select persistent extremes from prespecified upper-band ubar tail and duration rules using no lower-level response information.
2. Select ordinary episodes only from the non-tail range by a prespecified upper-band ubar tendency-and-duration rule, exclude windows adjacent to extreme episodes, and match or stratify on season and antecedent lower-level ubar state.
3. For each episode, estimate height-band anomaly trajectories from tran60n or seasonally adjusted ana60n, with onset and peak timing uncertainty propagated across prespecified adjacent-band and smoothing choices.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Seasonally matched non-event windows carrying the same nominal-time structure.; Time-shifted or block-resampled upper-band episode labels that preserve persistence but break episode alignment.
- Positive controls: Synthetic injected sequential trajectories with known ordering, assessed before access to target conclusions.; Synthetic simultaneous vertical perturbations, which should be flagged as near-simultaneous rather than sequential.
- Alternative explanations: Seasonal covariance or upper-band autocorrelation creates apparent lags.; Near-simultaneous barotropic adjustment produces same-signed multilevel anomalies.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- This observational reanalysis-derived record cannot establish that upper-level anomalies cause lower-level changes.
- ubar is a dataset_alias from operator context, not a file-verified physical definition; PV conditioning and horizontal mechanisms cannot be assessed.
- Physical time lags and signs remain conditional on future metadata validation.

**Why the plan serves the question**

It preserves independent upper-level episode selection, the ordinary-versus-persistent contrast, intermediate level-by-level timing, and the designated persistence, seasonal, simultaneous-adjustment, and antecedent-state alternatives without retrospectively defining events by tropospheric response.

**Before any later execution**

- Unresolved planning decisions: Exact upper, middle, and lower height-band boundaries after coordinate validation.; Exact tail, tendency, duration, lag, and near-simultaneous thresholds, fixed before target-outcome evaluation.; plus 1 additional item(s) in the complete dossier
- Required future skills: Metadata-aware loader that validates NetCDF dimensions, height coordinates, missingness, anomaly relation, and nominal-time adjacency.; Episode-first trajectory module with blocked resampling and synthetic sequential-versus-simultaneous recovery tests.

### Scientific stakes

**Discriminating observation**

Episodes would be selected solely from a prespecified upper-stratospheric circulation quantity: persistent tail anomalies would define the extreme class, while ordinary episodes would be isolated transient reorganizations within the non-tail range, separated from extreme-event windows and identified by an upper-level tendency-and-duration rule rather than by failure to propagate. Responses would be tracked in ordered altitude bands from the upper stratosphere through the middle and lower stratosphere toward the troposphere using a consistent level-resolved circulation anomaly, with PV structure used where available to characterize antecedent state. A sequential trajectory would require same-signed anomaly onset or peak times to progress monotonically downward within a prespecified lag tolerance and to be detectably separated from near-simultaneous adjustment; no lower-level response would enter episode classification. Support would require this ordering to recur more than under seasonally matched non-event or persistence-preserving comparisons and to remain distinguishable after stratification by preexisting lower-stratospheric and tropospheric circulation/PV structure.

**What possible outcomes would mean**

- Positive pattern: If persistent extremes show recurrent downward-ordered trajectories while independently defined transient ordinary reorganizations show a different or truncated sequence, this would support an event-first account in which upper-level persistence changes the vertical organization of coupling. If both classes share the sequence, it would instead support continuity of the event-level mechanism across non-tail and extreme circulation episodes.
- Negative pattern: If apparent ordering is removed by seasonally conditioned persistence controls, separation from near-simultaneous adjustment, or conditioning on antecedent lower-level structure, the evidence would weaken a distinct event-first sequential account and favor shared forcing, barotropic coherence, or state-dependent observability.
- Null or ambiguous pattern: If sequence occurrence or class differences remain inconsistent after the specified controls, the data would not distinguish a common vertical pathway from heterogeneous pathways or masking. Such a result would not imply that upper-level events lack lower-level influence; it would limit claims about a recurrent ordered trajectory.

## Variant 2: Low-frequency cross-diagnostic common-component and residual-structure test

### Why it matters

Distinguishing a cross-diagnostic common component from index robustness and mechanically induced agreement would clarify when vertical coupling can be summarized parsimoniously and when wave or forcing structure must remain explicit. Restricting the target to variability longer than 60 days also separates this claim from the documented intraseasonal, propagating vortex-displacement oscillation.

### Original and refined question

**Original Question Scientist proposal**

Is apparent vertical coupling captured by a robust continuous circulation mode across heights, or does coherence dissolve when circulation, wave activity, reference-flow, and forcing perspectives are compared?

**Post-novelty revised proposal**

During Northern Hemisphere winter, does variability longer than 60 days contain a vertically deep common component linking extratropical tropospheric annular circulation to stratospheric polar-vortex strength across circulation, reference-flow, wave-activity, and forcing diagnostics, after excluding propagating vortex-displacement structure and accounting for shared diagnostic inputs; or do recurrent wave and forcing residuals require a process-specific account?

**Reviewed refined question**

Within Northern Hemisphere winter observations, does the validated longer-than-60-day component of vertically resolved ubar and uref contain a deep circulation-vortex-strength organization that is corroborated by non-duplicative fawa and epz signatures, or do residual structures require a process-specific account?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the available vertically resolved record supports Northern Hemisphere winter circulation, reference-flow, wave-activity, and forcing descriptions, it may permit comparison of a low-frequency common component with residual structures while documenting which diagnostics share underlying inputs. Exact diagnostic coverage and separability remain to be verified.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The analysis and transient files each contain fawa, ubar, uref, and epz on 97 vertical levels with 124 time slots, 12 months, and 43 years, while the seasonal file has the corresponding 97-by-124-by-12 structure. The report says the NetCDF files have no user-visible calendar semantics, units, long names, fill-value convention, or transformation provenance.
  - Limitation: The structural report does not validate an exact 60-day calendar filter, physical sign, or independence of diagnostic constructions.
  - Limitation: This planning evidence contains no target-outcome analysis.
- **Unverified planning evidence:** The supplied context describes the package as ERA5-derived 60 degrees North stratospheric dynamics data and identifies fawa, ubar, uref, and epz as wave-activity, circulation or polar-vortex-wind, reference-flow, and eddy-forcing diagnostics. It describes tran60n as analysis minus a multi-year seasonal climatology and explicitly limits the package to one latitude with no horizontal structure.
  - Limitation: The stated diagnostic meanings and anomaly provenance are not independently encoded in the NetCDF metadata.
  - Limitation: The package cannot identify vortex location or horizontal displacement structure directly.

### Plan at a glance

- Population and scope: The available population is approximately 43 years of repeated observations across the 97-level 60 degrees North vertical column; it can address vertically resolved local diagnostic organization but not horizontal vortex displacement, wave geography, or regional impacts.
- Unit of observation: A vertically resolved nominal-time diagnostic profile.
- Unit of inference: A winter-season realization or year-blocked low-frequency segment, not individual adjacent nominal-time slots.
- Hierarchy and dependence: Represent profiles as repeated observations nested in winters/years and heights; estimate uncertainty with winter/year block resampling and preserve serial dependence during filtering and null generation.
- Validation: Before execution, validate exact temporal ordering, season handling, height coordinate, anomaly relation, missingness, units/signs, and diagnostic formula lineage. Use synthetic profiles containing a known common low-frequency component, phase-propagating structure, and residual wave/forcing structure to verify recovery and prevent selection of component count from target residuals.
- Split strategy: Block by complete winter/year; fit filtering and component construction in prespecified training winters and score vertical depth, reconstruction, and residual recurrence in held-out winters. Keep the dependency audit fixed across splits.
- Claim ceiling: associational

**Analysis strategy**

1. Validate the temporal coordinate and use a prespecified winter definition; derive the longer-than-60-day component only after the calendar mapping is confirmed, otherwise retain the analysis at a transparently labeled nominal-slot cutoff and do not make an exact physical-period claim.
2. Define the primary circulation lineage from vertically resolved ubar and uref, treating their likely shared circulation inputs as non-independent corroboration.
3. Construct a cross-height common-component model for that lineage, then evaluate fawa and epz as a coupled wave/forcing lineage rather than counting them as two independent tests.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Seasonally structured, serial-dependence-preserving surrogate profiles that should not yield stable cross-winter common structure.; Cross-lineage comparison after blocking shared-input diagnostics from being counted as independent corroboration.
- Positive controls: Synthetic vertically deep common component with known loading pattern.; Synthetic propagating and wave/forcing-residual profiles that should remain distinguishable after common-component fitting.
- Alternative explanations: Agreement between ubar and uref is mechanical reuse of circulation state rather than independent corroboration.; Agreement between fawa and epz reflects their wave/forcing derivation lineage rather than two independent processes.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- Common-component agreement cannot establish causal vertical coupling or a unique physical mechanism.
- The dataset cannot directly distinguish vortex-strength variability from horizontal displacement because it has no horizontal structure.
- The greater-than-60-day claim is contingent on resolving calendar semantics; diagnostic independence is contingent on formula provenance.

**Why the plan serves the question**

It preserves the low-frequency continuous-mode target, distinguishes shared-input agreement from cross-lineage corroboration, and permits recurrent residual structure to falsify a sufficient single-mode account rather than selecting a preferred index or episode narrative.

**Before any later execution**

- Unresolved planning decisions: Documented calendar/padded-day convention and winter boundary needed for an exact 60-day cutoff.; Formula and primitive-variable provenance needed to finalize diagnostic dependency lineages.; plus 1 additional item(s) in the complete dossier
- Required future skills: Metadata-aware temporal and vertical-coordinate validation with auditable long-period filtering.; Dependency-audited multilevel component and residual-recurrence workflow with year-blocked validation and synthetic recovery.

### Scientific stakes

**Discriminating observation**

The common-mode account would be supported only if variability longer than 60 days shows a recurrent vertically deep structure connecting extratropical tropospheric annular circulation with stratospheric vortex strength, and if diagnostic components that do not algebraically reuse that circulation index provide physically consistent corroboration. Circulation and reference-flow measures sharing state variables would be treated as one evidence lineage, while wave activity and its derived forcing would not be counted as independent of each other. Recurrent residuals dominated by phase propagation or vortex-location shifts, or stable wave or forcing structure remaining after the common component is represented, would falsify a sufficient single-mode account; agreement confined to shared circulation inputs would count only as partial convergence.

**What possible outcomes would mean**

- Positive pattern: Robust cross-lineage agreement with no recurrent process-specific residual would support a parsimonious continuous-mode description of low-frequency Northern Hemisphere winter coupling, without implying that one multilevel index is uniquely preferred.
- Negative pattern: A recurrent propagating displacement pattern or substantial stable wave, forcing, or reference-flow residuals beyond the circulation component would reject a sufficient single-mode account and favor multiple process-specific coupling structures.
- Null or ambiguous pattern: Agreement among circulation-based constructions but weak or inconsistent corroboration from nonredundant diagnostic components would indicate partial convergence: a limited shared circulation field may exist, while the evidence would not establish a cross-diagnostic process-level mode.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct protected targets and provide credible associational planning routes. The event-first plan selects episodes without downstream-response information and tests ordered trajectories against seasonality, persistence, simultaneity, and antecedent-state alternatives. The continuous-mode plan separates the common-component target from diagnostic-lineage dependence and permits structured residuals to falsify a sufficient single-mode account. Remaining items are pre-execution operational locks, not scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Document temporal ordering, calendar and padded-day conventions, and winter boundaries before converting nominal-slot timing to physical lags or applying the exact greater-than-60-day filter; retain nominal-slot labeling if this cannot be resolved.
- **Pre execution lock:** Verify variable definitions, units, signs, missing-value handling, anomaly relation, and formula/shared-input provenance before execution; finalize physical-direction interpretation and diagnostic dependency lineages only after that audit.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants remain faithful to their protected estimands: the event-first variant tests state-conditioned, level-by-level ordered trajectories for independently selected episodes without downstream information, and the continuous-mode variant tests a dependency-audited, vertically deep common component that treats diagnostic agreement as testable rather than assumed. Neither plan collapses into the other's forbidden semantic merge (lagged episode-level prediction versus representation-robustness of shared organization). Grounding is honest: available variables (ubar, uref, fawa, epz) are used as documented aliases, PV and horizontal displacement are explicitly acknowledged as unavailable and are omitted rather than proxied, and claim ceilings are associational with causal language avoided. Both plans specify credible alternative explanations (seasonal covariance, barotropic adjustment, antecedent-state masking, mechanical shared-input agreement, phase-propagating structure) and pair them with concrete positive/negative controls and synthetic recovery tests. Dependence structure (winter/year blocking) and split strategy are prespecified and pre-registered before target evaluation. The two Owner-identified issues concern calendar/temporal-convention resolution and variable/provenance verification; both are appropriately deferred to a later execution-validation stage, and the plans already specify safe fallback behavior (nominal-slot labeling, dependency-audited lineage framing) if that validation is incomplete, so neither rises to a scientific blocker. This is a first-round review with no prior revision history, so material-revision and prior-issue-resolution criteria are not applicable.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
