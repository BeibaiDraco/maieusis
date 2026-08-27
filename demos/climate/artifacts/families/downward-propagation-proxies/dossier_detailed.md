# Stratospheric signatures of downward communication and persistence — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Mixed family: accepted and non-accepted sibling variants**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Develops observationally bounded questions about downward-propagating stratospheric anomalies without claiming surface impacts. One variant asks whether propagation is a distinct state transition; the other asks whether a mechanistic proxy built from multiple stratospheric ingredients carries information beyond vortex weakness alone.

The scientific tension is:

Downward-extending anomalies may represent a distinct, dynamically organized mode of stratospheric evolution, or they may be a descriptive by-product of persistent vortex disturbances and measurement choices.

## How to read this mixed family

Accepted and non-accepted sibling variants coexist here. Authority applies only to the variants explicitly marked as reviewed and accepted; it does not spill across the family.

## Variant 1: Conditional classification and pathway test relative to published PJO events

### Why it matters

Determining whether downward extension is identical to, nested within, broader than, or cross-cutting relative to the published PJO population would clarify the ontology of recurrent stratospheric recovery behavior without extending the claim to tropospheric or surface impacts.

### Original and refined question

**Original Question Scientist proposal**

Do downward-extending stratospheric circulation anomalies form a recurrent transition class with distinctive wave-forcing and recovery histories, rather than simply the most persistent examples of vortex disturbance?

**Post-novelty revised proposal**

When downward-extending circulation episodes are treated as an alternative classification and cross-classified against published polar-night jet oscillation (PJO) events, do they identify a reproducible forcing-and-recovery pathway that separates from an independently defined vertically confined comparator after conditioning on disturbance magnitude and recovery persistence, or do they merely recover the PJO persistence–depth continuum?

**Refined-question status**

No refined question earned accepted-plan authority for this sibling.

**Reviewed planning disposition**

Rejected because a faithful operationalization was not established. The protected contrast requires cross-classification with published PJO status. The authorized package exposes continuous dynamics fields but no PJO catalog or calendar-validated mapping to a published PJO definition, so replacing PJO with a newly inferred label would change the question.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If vertically resolved circulation and wave-forcing histories are jointly available, they may support cross-classification of downward-extension and PJO-like episodes and a magnitude- and persistence-conditioned comparison. The confined comparator would need to be defined through an independent vertical-state criterion that does not use the downward-extension metric or the persistence quantity used for conditioning; availability and defensibility of such a criterion require later verification.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The package is described as vertically resolved, repeated time-series information for Northern Hemisphere stratospheric circulation, wave activity, a reference-flow diagnostic, and eddy forcing, with separate analysis, seasonal-background, and anomaly surfaces. It has no horizontal, regional, or surface fields.
  - Limitation: This is a bounded operator-prepared context rather than independently verified physical metadata.
  - Limitation: It does not establish units, sign conventions, calendar semantics, missing-value rules, or a scientific relationship.
- **Unverified planning evidence:** The supplied description identifies ana60n, sea60n, and tran60n as 60 degrees North one-dimensional vertical-grid files. It describes ana60n and tran60n at height by time by month by year grain, sea60n at height by time by month grain, and names fawa, ubar, uref, and epz as wave-activity, vortex-wind, reference-wind, and eddy-forcing surfaces.
  - Limitation: The document explicitly says that its variable meanings and temporal design are operator-supplied claims rather than file-verified metadata.
  - Limitation: The files do not provide user-visible units, long names, calendar semantics, fill-value conventions, transformation provenance, or derivative-data licensing in the supplied context.
  - Limitation: This evidence supports a conditional planning route only and cannot establish physical budgets, causal mechanism, or a result.
- **Unverified planning evidence:** The local package contains ana60n.nc, sea60n.nc, and tran60n.nc. All three are HDF5 files carrying NetCDF4 structural markers; ana60n and tran60n are each approximately 95 MB and sea60n is approximately 2.2 MB. Embedded structural text exposes height, time, month, and year dimension names, consistent with the supplied documentation.
  - Limitation: This bounded structural check did not enumerate variables reliably or inspect coordinate values, attributes, missing values, or raw observations.
  - Limitation: The configured inspection Python lacks a NetCDF reader, so a later execution environment must re-verify file schema and field availability before analysis.

### Scientific stakes

**Discriminating observation**

Support for an independently meaningful transition pathway would require, among episodes comparable in disturbance magnitude and recovery persistence, a reproducible temporal ordering linking changes in wave forcing to vertically ordered recovery that separates downward-extending episodes from a confined population defined with an independent vertical-state criterion. The separation must recur within PJO-status strata or otherwise show that the downward-extension class is not merely synonymous with PJO status; long-lived recovery, suppressed wave driving, or descending-stratopause structure alone would not qualify.

**What possible outcomes would mean**

- Positive pattern: Conditional, definition-robust separation based on a reproducible forcing-and-recovery sequence—and a demonstrated identity, subset, broader-category, or cross-cutting relation to PJO status—would support treating downward extension as an additional transition classification rather than a relabeling of documented PJO signatures.
- Negative pattern: If conditional separation exists only within the published PJO population or maps completely onto PJO status, the downward-extension construct should be interpreted as a nested or equivalent description of established PJO behavior rather than as an independent transition class.
- Null or ambiguous pattern: If no conditional separation remains after accounting for disturbance magnitude and recovery persistence, PJO-like downward evolution should be interpreted as evidence for a persistence–depth continuum rather than an independently supported transition regime. If conclusions vary materially with reasonable independent definitions, the classification should remain provisional.

## Variant 2: Conditional, temporally separated multicomponent discrimination test

### Why it matters

The comparison would clarify whether multiple stratospheric ingredients provide interpretable event-level information beyond vortex weakness while avoiding claims about tropospheric causation, surface impacts, generic coupling, or operational predictive skill.

### Original and refined question

**Original Question Scientist proposal**

Can a multicomponent stratospheric proxy combining disturbance persistence, vertical progression, and post-disturbance wave forcing distinguish sustained downward-extending evolution better than vortex weakness alone?

**Post-novelty revised proposal**

Among sudden-stratospheric-warming episodes matched or conditioned on initial vortex weakness, do antecedent measures of disturbance persistence and vertical progression, together with post-disturbance wave forcing measured before a separate outcome-evaluation period, add stable and interpretable discrimination of independently defined sustained downward-extending stratospheric evolution?

**Reviewed refined question**

Among validated sudden-stratospheric-warming-like episodes defined from the documented stratospheric circulation surface, do prespecified antecedent persistence and vertical-progression measures plus a post-disturbance, pre-outcome wave-forcing measure add stable retrospective discrimination of a separately scored later sustained downward-extension label beyond matched or conditioned initial vortex weakness?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Vertically resolved stratospheric circulation and wave histories may permit a later planner to separate an antecedent component window from a later outcome-evaluation window, condition on initial weakness, and compare component behavior across defensible definitions; exact feasibility and any independent credibility resource remain to be verified.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The package is described as vertically resolved, repeated time-series information for Northern Hemisphere stratospheric circulation, wave activity, a reference-flow diagnostic, and eddy forcing, with separate analysis, seasonal-background, and anomaly surfaces. It has no horizontal, regional, or surface fields.
  - Limitation: This is a bounded operator-prepared context rather than independently verified physical metadata.
  - Limitation: It does not establish units, sign conventions, calendar semantics, missing-value rules, or a scientific relationship.
- **Unverified planning evidence:** The supplied description identifies ana60n, sea60n, and tran60n as 60 degrees North one-dimensional vertical-grid files. It describes ana60n and tran60n at height by time by month by year grain, sea60n at height by time by month grain, and names fawa, ubar, uref, and epz as wave-activity, vortex-wind, reference-wind, and eddy-forcing surfaces.
  - Limitation: The document explicitly says that its variable meanings and temporal design are operator-supplied claims rather than file-verified metadata.
  - Limitation: The files do not provide user-visible units, long names, calendar semantics, fill-value conventions, transformation provenance, or derivative-data licensing in the supplied context.
  - Limitation: This evidence supports a conditional planning route only and cannot establish physical budgets, causal mechanism, or a result.
- **Unverified planning evidence:** The local package contains ana60n.nc, sea60n.nc, and tran60n.nc. All three are HDF5 files carrying NetCDF4 structural markers; ana60n and tran60n are each approximately 95 MB and sea60n is approximately 2.2 MB. Embedded structural text exposes height, time, month, and year dimension names, consistent with the supplied documentation.
  - Limitation: This bounded structural check did not enumerate variables reliably or inspect coordinate values, attributes, missing values, or raw observations.
  - Limitation: The configured inspection Python lacks a NetCDF reader, so a later execution environment must re-verify file schema and field availability before analysis.

### Plan at a glance

- Population and scope: Eligible Northern Hemisphere 60 degrees North stratospheric disturbance episodes represented in the validated analysis or transient files, restricted to seasons and years that can be established from file coordinates without imputing calendar semantics. The scope excludes regional, surface, and tropospheric impacts.
- Unit of observation: A validated height-by-time circulation or dynamical-field observation indexed within a year.
- Unit of inference: A non-overlapping stratospheric disturbance episode, with uncertainty clustered or resampled at the year level to respect shared seasonal and reanalysis dependence.
- Hierarchy and dependence: Retain the height-by-time field hierarchy during feature construction; create one prespecified feature vector and one later-outcome label per episode. Account for episodes nested within years and seasonal strata with blocked year-level resampling or hierarchical uncertainty estimation. Do not treat vertically adjacent slots or multiple windows from one episode as independent units.
- Validation: Use a synthetic method-recovery test with known temporal separation before target-data execution; verify that the pipeline rejects a component constructed solely from post-outcome information. On target data, use blocked year-level cross-validation, fit all preprocessing within training blocks, and predeclare minimum episode coverage and calibration checks. Compare results across reasonable but fixed alternative height ranges, persistence windows, and label-duration rules without selecting the most favorable specification.
- Split strategy: Leave out whole years, retaining all observations and episodes from a year in the same fold. If the validated record has too few independent years for stable folds, use blocked year-level bootstrap confidence summaries and label the analysis exploratory-to-replicate rather than treating individual time slots as independent.
- Claim ceiling: associational

**Analysis strategy**

1. First run a schema gate that verifies the four named fields, coordinate direction, usable seasonal indexing, numeric types, and missing-value treatment; stop execution if any required mapping cannot be documented.
2. Define initial vortex weakness from a prespecified disturbance-window summary of the validated ubar representation, with sign orientation established before labels or models are examined.
3. Identify candidate disturbance episodes from that baseline circulation definition using non-overlap and seasonal eligibility rules fixed before outcome scoring.
4. 4 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: A temporally permuted pre-outcome forcing component that preserves marginal distribution but destroys episode ordering.; A feature measured only after the outcome window, used solely to confirm the leakage detector rejects it from the permitted proxy.
- Positive controls: A synthetic injected temporally ordered signal with a known component contribution, used only to recover the intended split and leakage behavior before real-data analysis.; The documented seasonal-background versus transient-file relationship, if schema validation confirms it, as a structural consistency check rather than as evidence of the scientific hypothesis.
- Alternative explanations: Residual initial disturbance severity or depth that is not removed by the weakness baseline or matching rule.; Outcome leakage through overlapping vertical-progression, persistence, or forcing windows.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- Any added discrimination is retrospective and observational; it does not establish that wave forcing or vertical progression causes sustained downward extension.
- The single-latitude, zonal-mean package cannot support claims about geographic wave sources, tropospheric coupling, surface impacts, or external attribution.
- Units, signs, calendar semantics, and transformation provenance remain unresolved in the planning evidence and are hard execution prerequisites.

**Why the plan serves the question**

The plan preserves the protected event-level contrast by separating initial weakness, antecedent trajectory, post-disturbance forcing, and a later independently scored circulation outcome. It tests incremental, stable retrospective discrimination rather than relabeling severity, claiming a mechanism, or extending the question to surface impacts.

**Before any later execution**

- Unresolved planning decisions: Validated sign and physical interpretation of ubar, fawa, uref, and epz.; Validated time-coordinate semantics sufficient to define temporal ordering and year-level blocks.; plus 1 additional item(s) in the complete dossier
- Required future skills: A read-only NetCDF4/HDF5 schema reader that records validated dimensions, coordinate values, attributes, and missing-value conventions without persisting raw arrays.; A leakage-audited event-window feature builder with year-blocked resampling and synthetic method-recovery tests.

### Scientific stakes

**Discriminating observation**

Support would require that, among episodes matched or conditioned on initial weakness, antecedent persistence and vertical-progression measures plus wave forcing observed after the disturbance but before the outcome period discriminate a later sustained downward-extension label defined with a separate diagnostic excluded from proxy construction. Added discrimination must remain directionally stable and physically interpretable at the component level across reasonable definitions; a gain driven by an unstable component would remain provisional.

**What possible outcomes would mean**

- Positive pattern: Stable added discrimination with interpretable component contributions would justify using the construct as a transparent organizer of sustained stratospheric downward-evolution episodes beyond initial weakness, without establishing causation, tropospheric impact, or forecast skill.
- Negative pattern: If the components add no discrimination after conditioning on initial weakness, the simpler weakness measure would be favored and the multicomponent construct would not be scientifically warranted for this target.
- Null or ambiguous pattern: If conclusions depend on the outcome definition, temporal separation, matching choice, or an unstable component, the construct would remain provisional and no added-information claim would be supported.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan preserves the mechanistic-proxy variant’s event-level, associational contrast: it separates initial weakness, temporally eligible components, and a later independently scored circulation outcome, with leakage audits and year-blocked validation. It appropriately rejects the sibling state-class variant rather than substituting an unsupported PJO label. Remaining schema, temporal-coordinate, and parameter choices are execution locks rather than deficiencies in the planning dossier.

Retained changes and locks:

- **Pre execution lock:** Before execution, validate field availability, signs, units, missing-value conventions, and time/height coordinate semantics; then prespecify the disturbance, feature, forcing, outcome, non-overlap, and seasonal rules using validated metadata and published methodological rationale, without outcome-driven tuning.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family plan is sound: the surviving mechanistic-proxy variant preserves the protected event-level, temporally-separated discrimination contrast (initial weakness vs. antecedent persistence/vertical-progression plus post-disturbance forcing, scored against an independently constructed later outcome), keeps an associational claim ceiling with explicit interpretation limits, and specifies pre-registered positive/negative controls, a leakage audit, and year-blocked validation. Sibling separation is respected: rather than inventing a PJO label to preserve the state-class variant, the plan correctly rejects that sibling because the authorized package exposes no published PJO catalog or calendar-validated crosswalk, honoring the family's forbidden-semantic-merge boundary instead of collapsing the two variants. Every sibling has an honest non-pending outcome (one operationalization rejection, one accept-with-new-skill), satisfying the family soundness bar. The sole outstanding Owner issue concerns field/unit/coordinate validation and rule prespecification before execution; this is bounded, execution-stage detail rather than a defect in the planning product, so it is correctly a pre-execution lock rather than a blocker. No hard-boundary or scientific-intent drift is present.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
