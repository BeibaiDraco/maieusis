# Recurrent states versus transition-centered organization of the polar stratosphere — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Mixed family: accepted and non-accepted sibling variants**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether large-scale stratospheric variability is most informatively organized as recurrent states or as dynamically distinctive transition episodes, without assuming that either representation is uniquely physical.

The scientific tension is:

Long-lived circulation states may be substantive recurrent organizations of the system, but apparent regimes can also emerge from continuous evolution whose scientifically distinctive structure is concentrated near transitions.

## How to read this mixed family

Accepted and non-accepted sibling variants coexist here. Authority applies only to the variants explicitly marked as reviewed and accepted; it does not spill across the family.

## Variant 1: State-centered validation and matched-representation test

### Why it matters

Determining whether these configurations retain reproducible vertical organization and add information about subsequent circulation evolution would clarify when discrete state labels have scientific meaning beyond a continuous description of the same Northern Hemisphere winter polar-stratospheric circulation.

### Original and refined question

**Original Question Scientist proposal**

Do recurrent vertically organized circulation states recur robustly across seasonal and multi-decade partitions, and do they provide information about persistence beyond a continuous circulation description?

**Post-novelty revised proposal**

Across the Northern Hemisphere polar stratosphere (60–90°N, November–February, 1–100 hPa), do vertically reformulated states anchored to the previously studied upper-stratospheric narrow- and wide-jet vortex configurations recur across separated winter-season and multidecadal partitions and improve prediction of subsequent vertical circulation evolution relative to a commensurate continuous representation?

**Refined-question status**

No refined question earned accepted-plan authority for this sibling.

**Reviewed planning disposition**

Rejected because the inspected dataset did not support the required design. The protected 60-90-degree-N and 1-100-hPa domain cannot be faithfully operationalized: the documented package is a fixed 60-degree-N one-dimensional vertical record with no latitude dimension, and verified files expose neither a pressure coordinate nor a source-backed height-to-pressure mapping. Owner clarification requires retaining the exact pressure domain rather than using an approximate height proxy. Future support requires data with a documented 60-90-degree-N spatial aggregation and a documented 1-100-hPa coordinate, or a source-backed mapping applicable to such data.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If a consistent vertically resolved record covers the proposed Northern Hemisphere winter domain, it may support partitioned comparisons of a state representation and a continuous representation constructed from identical circulation fields, temporal sampling, vertical coverage, and information available at the prediction time.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The supplied context describes an ERA5-derived dataset at fixed 60 degrees North on a one-dimensional vertical grid, with full analysis, seasonal-background, and transient-anomaly products. It describes fawa, ubar, uref, and epz as wave-activity, zonal-wind, reference-flow, and eddy-forcing diagnostics, respectively, and explicitly states that the package has no latitude or longitude dimension.
  - Limitation: This is operator-supplied documentation rather than owner-authored metadata.
  - Limitation: The document explicitly leaves units, sign conventions, calendar semantics, missing-value conventions, and transformation provenance unresolved.
  - Limitation: A fixed 60-degree-N series cannot itself establish spatial variation or a 60-90-degree-N area domain.
- **Unverified planning evidence:** The verified ana60n.nc and tran60n.nc files each contain four float32 arrays named fawa, ubar, uref, and epz with dimensions (height=97, time=124, month=12, year=43); sea60n.nc has the same variables with dimensions (height=97, time=124, month=12). The report records no user-visible global or variable attributes, including no units, pressure coordinate, calendar interpretation, or missing-value convention.
  - Limitation: The source establishes structural readability and dimensions, not the physical meaning, units, or sign of the arrays.
  - Limitation: It does not establish a mapping from the encoded height coordinate to 1-100 hPa.
  - Limitation: It does not establish how time slots, month boundaries, leap days, or padded days map to chronological timestamps.

### Scientific stakes

**Discriminating observation**

Support for discrete-state organization would require vertically coherent counterparts of the upper-stratospheric narrow- and wide-jet configurations to recur in independently separated winter-season and multidecadal partitions, remain recognizable across plausible algorithms, state numbers, filtering choices, persistence constraints, and sample-size perturbations, and improve prediction of subsequent circulation evolution when compared with a continuous predictor using the same fields, sampling, 1–100 hPa domain, and prediction-time information. Added information concerns subsequent vertical evolution rather than residence time alone or persistence imposed by the construction method.

**What possible outcomes would mean**

- Positive pattern: Robust cross-partition recurrence together with added prediction of subsequent vertical circulation evolution would support treating the vertically reformulated narrow- and wide-jet configurations as scientifically informative polar-stratospheric states rather than merely convenient categories.
- Negative pattern: Failure of the configurations to recur, sensitivity dominated by construction choices, or superior prediction by the matched continuous representation would favor a continuous description and constrain broader state-based interpretations of polar-vortex persistence.
- Null or ambiguous pattern: If state and continuous representations provide indistinguishable predictive information and recurrence remains stable only within uncertainty, neither representation would be uniquely supported; conclusions would need to remain representation-dependent rather than treating the state inventory as independently physical.

## Variant 2: Transition-centered dynamical contrast

### Why it matters

A transition-centered test can determine whether regime changes mark scientifically special dynamical episodes rather than labels imposed on gradual evolution.

### Original and refined question

**Original Question Scientist proposal**

Are changes in wave activity, eddy forcing, and vertical circulation organization concentrated around transitions between circulation states, or do they evolve similarly during matched within-state intervals?

**Reviewed refined question**

Within the documented fixed-60-degree-N vertically resolved record, are predeclared changes in the native-coordinate vertical profiles of wave activity, eddy forcing, and circulation organization temporally localized around independently defined circulation-state transitions relative to seasonally and history-matched within-state intervals?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Repeated observations of circulation, wave activity, and eddy forcing may allow later planning of transition and matched non-transition comparisons across height.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The package is described as vertically resolved repeated Northern Hemisphere stratospheric circulation data that separates analysis fields, a seasonal background, and departures from that background; the stated scientific modalities include zonal-mean circulation, wave activity, a reference-flow diagnostic, and eddy forcing.
  - Limitation: This is a coarse planning description and does not establish exact physical units, equations, sign conventions, or calendar mapping.
  - Limitation: The description says the spatial scope is narrow and does not provide horizontal or regional structure.
- **Unverified planning evidence:** The supplied context describes an ERA5-derived dataset at fixed 60 degrees North on a one-dimensional vertical grid, with full analysis, seasonal-background, and transient-anomaly products. It describes fawa, ubar, uref, and epz as wave-activity, zonal-wind, reference-flow, and eddy-forcing diagnostics, respectively, and explicitly states that the package has no latitude or longitude dimension.
  - Limitation: This is operator-supplied documentation rather than owner-authored metadata.
  - Limitation: The document explicitly leaves units, sign conventions, calendar semantics, missing-value conventions, and transformation provenance unresolved.
  - Limitation: A fixed 60-degree-N series cannot itself establish spatial variation or a 60-90-degree-N area domain.
- **Unverified planning evidence:** The verified ana60n.nc and tran60n.nc files each contain four float32 arrays named fawa, ubar, uref, and epz with dimensions (height=97, time=124, month=12, year=43); sea60n.nc has the same variables with dimensions (height=97, time=124, month=12). The report records no user-visible global or variable attributes, including no units, pressure coordinate, calendar interpretation, or missing-value convention.
  - Limitation: The source establishes structural readability and dimensions, not the physical meaning, units, or sign of the arrays.
  - Limitation: It does not establish a mapping from the encoded height coordinate to 1-100 hPa.
  - Limitation: It does not establish how time slots, month boundaries, leap days, or padded days map to chronological timestamps.

### Plan at a glance

- Population and scope: Eligible observations are native vertical-profile time points from ana60n.nc and tran60n.nc after source-backed chronological decoding, restricted to a predeclared analysis season and records with complete required circulation descriptors. Inference is to repeated fixed-60-degree-N stratospheric time points across the documented 43 year-indexed record, not to a 60-90-degree-N area or regional dynamics.
- Unit of observation: A decoded chronological vertical-profile time point at fixed 60 degrees North.
- Unit of inference: A non-overlapping transition episode or matched within-state episode, with dependence retained within the same winter season and year.
- Hierarchy and dependence: Treat time points as nested within winter seasons and year indices. Define non-overlapping episode windows with a washout buffer; use year- or winter-blocked resampling and cluster-aware uncertainty rather than treating profile time points as independent.
- Validation: Validate chronological decoding and variable metadata against owner or source documentation before execution; use simulated profile trajectories with known transitions to verify episode construction, matching, overlap exclusion, and blocked uncertainty procedures; confirm that the same pre-outcome state procedure is applied to every analysis product and resampling fold.
- Split strategy: Fit and tune state construction only within training winter or multiyear blocks, assign out-of-block states by a frozen rule, and evaluate event-time contrasts on held-out blocks. Rotate blocks for coverage without allowing future target trajectories to define transitions.
- Claim ceiling: associational

**Analysis strategy**

1. Before examining fawa or epz trajectories, construct circulation states from predeclared ubar and uref profile features using a small prespecified representation set and training folds separated by winter or multiyear blocks.
2. Define a transition onset as an independently classified state change that satisfies a prespecified persistence rule; discard or separately label rapid reversals, overlapping windows, and boundary-spanning episodes.
3. For each transition episode, select within-state control episodes matched on calendar position, prior-state duration, pre-window circulation feature distance, and year-block availability, while excluding all transition washout windows.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Apply the same procedure to pseudo-boundaries placed within sufficiently persistent state intervals and require no comparable localized contrast.; Use time-shifted matched windows that cannot contain the defined boundary while preserving season and prior-state matching.
- Positive controls: On simulated trajectories with injected state changes and known event-time profile shifts, recover the injected transition timing while maintaining type-I control for pseudo-boundaries.; Verify that the documented seasonal product and the analysis-minus-seasonal product are treated as distinct sensitivity inputs rather than silently interchangeable physical measures.
- Alternative explanations: Seasonal drift or calendar-position imbalance may create both apparent state changes and profile changes.; State boundaries may be artifacts of clustering, filtering, persistence constraints, or unequal occupancy.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- The observational fixed-latitude record cannot by itself identify causal wave forcing, regional source mechanisms, or physical budgets.
- Any physical interpretation of fawa and epz awaits source-backed definitions, units, and sign conventions.
- The plan does not assess scientific outcomes and therefore makes no claim that transition-specific dynamics are present.

**Why the plan serves the question**

The plan preserves the sibling's distinct contrast by treating transitions, not state recurrence, as the focal population; it defines state changes independently of the proposed forcing outcomes, compares them to seasonally and history-matched within-state evolution, and specifies discriminating localized-versus-nonlocalized patterns without assuming that state boundaries are intrinsically physical.

**Before any later execution**

- Unresolved planning decisions: Source-backed chronology for encoded time, month, and year indices, including calendar and padded-day handling.; Source-backed definitions, units, signs, transformations, and missing-value conventions for all four arrays.; plus 2 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

A transition interpretation would be favored if independently defined state changes showed reproducible, temporally localized forcing and vertical-structure changes absent from seasonally matched within-state intervals.

**What possible outcomes would mean**

- Positive pattern: Distinct transition dynamics would justify treating transitions as a separate population of circulation episodes.
- Negative pattern: No transition-specific organization would weaken mechanistic interpretations of state boundaries and favor continuous evolution.
- Null or ambiguous pattern: Weak or representation-dependent contrasts would preserve uncertainty over whether transitions are dynamical events or classification artifacts.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family plan honestly rejects the unsupported recurrent-state sibling while providing a scientifically coherent, branch-isolated transition-centered design. It preserves the transition-versus-matched-within-state contrast, keeps inference associational, defines transitions without using the focal wave/forcing trajectories, and includes blocked evaluation, matching, sensitivity analyses, and negative controls. Remaining items are execution-stage locks rather than planning deficiencies.

Retained changes and locks:

- **Pre execution lock:** Obtain source-backed chronology, variable definitions, units, sign conventions, transformations, and missing-value rules before execution or physical interpretation.
- **Pre execution lock:** Lock the state-construction and episode-analysis choices before outcome inspection, including the representation family, persistence rule, event and washout windows, matching rule, and primary vertical summary.
- **Pre execution lock:** Document how the analysis, seasonal, and transient products relate before using them as seasonal-adjustment sensitivities.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family package is sound: the recurrent-state sibling is honestly rejected because the fixed-60-degree-N, height-indexed dataset cannot support the protected 60-90-degree-N, 1-100-hPa domain without unsupported semantic substitution, and the transition-centered sibling is accepted with a scientifically coherent, honestly scoped design. The accepted plan preserves the transition-versus-matched-within-state contrast, defines circulation states and transition timing independently of the fawa/epz outcome trajectories it later examines, keeps the claim ceiling associational, documents plausible competing explanations (seasonal drift, construction artifacts, autocorrelation, unresolved units), and specifies both positive controls (simulated injected transitions) and negative controls (pseudo-boundaries, time-shifted matched windows) plus construction-sensitivity checks. Remaining gaps (chronology decoding, variable units/signs, exact state-construction parameters, ana/tran/sea product reconciliation) are explicitly flagged as unresolved decisions to be locked before execution or physical interpretation, which is appropriate pre-execution detail rather than a planning-stage scientific blocker. Sibling separation is maintained: the accepted plan does not smuggle in a recurrent-state-inventory claim, and its narrowed population scope (fixed-60N time points, not a 60-90N area) is an honest dataset-grounded restriction rather than an overclaim.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
