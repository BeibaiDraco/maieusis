# Regime dependence in wave–mean-flow organization — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether wave–mean-flow relationships are portable across circulation regimes. One variant compares weak and strong vortex states; the other compares vertically coherent and vertically confined transition episodes.

The scientific tension is:

A common wave–mean-flow relationship may organize polar-vortex variability across regimes, or its strength and meaning may change with circulation state and vertical expression.

## Variant 1: Opposing circulation-regime comparison

### Why it matters

Weak and strong extremes are often treated as opposite ends of one continuum; testing that assumption would clarify whether they share an organizing relationship.

### Original and refined question

**Original Question Scientist proposal**

Is the association between wave activity, eddy forcing, and subsequent circulation change symmetric across weak-vortex and strong-vortex regimes?

**Reviewed refined question**

Within the documented 60 degrees North vertically resolved record, are the lagged observational associations of transient wave activity and eddy forcing with subsequent polar-vortex circulation change comparable in magnitude and temporal ordering after sign-reversal across predeclared weak and strong ubar-defined background regimes?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

The long record of wave, forcing, reference-flow, and circulation departures may allow later planning of parallel weak- and strong-regime comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The dataset is described as repeated, vertically resolved observations across multiple decades with zonal-mean circulation, wave activity, a reference-flow diagnostic, eddy forcing, a seasonal background, and departures from that background. It is explicitly narrow in spatial scope and lacks horizontal, regional, surface, and external-attribution fields.
  - Limitation: This is a coarse planning context and defers exact units, equations, sign conventions, calendar mapping, missingness, and transformation provenance to later verification.
  - Limitation: This is planning-only documentation evidence and is not a scientific result.
- **Unverified planning evidence:** The supplied documentation describes ana60n as full fields, sea60n as a seasonal climatology, and tran60n as transient anomalies, each carrying fawa, ubar, uref, and epz. It describes fawa as finite-amplitude wave activity, ubar as a polar-vortex wind diagnostic, uref as a reference zonal wind, and epz as eddy forcing; it also limits the package to a 60 degrees North vertical column.
  - Limitation: These variable meanings, signs, units, and transformation details are operator-supplied rather than encoded file metadata.
  - Limitation: The data cannot establish regional wave sources, wave phase structure, external attribution, or causal forcing.
  - Limitation: This is planning-only documentation evidence and is not a scientific result.
- **Unverified planning evidence:** The local ana60n and tran60n files are readable NetCDF4/HDF5 products with fixed dimensions height=97, time=124, month=12, and year=43. Each exposes float32 fawa, ubar, uref, and epz arrays of shape (97, 124, 12, 43); sea60n provides the same variables without year. The report states that user-visible global and variable attributes are absent.
  - Limitation: This establishes structural availability, not the physical interpretation or numerical behavior of any variable.
  - Limitation: No units, long names, fill-value conventions, calendar semantics, or derivative provenance are available in user-visible NetCDF metadata.
  - Limitation: This is planning-only structural evidence and is not a scientific result.

### Plan at a glance

- Population and scope: All usable seasonal-cycle slots across the 43-year ana60n and tran60n records at 60 degrees North, restricted before outcome inspection to the season and height band justified by recovered metadata. The inference population is the available historical reanalysis-derived record, not regional atmosphere or a causal intervention population.
- Unit of observation: A timestamped vertical-profile record after calendar reconstruction, with predeclared band summaries of transient fawa, epz, and ubar or uref as justified by verified definitions.
- Unit of inference: Independent year blocks, with within-year serial observations retained for estimating predeclared lagged associations and uncertainty obtained by year-level or season-block resampling.
- Hierarchy and dependence: Profiles are nested within encoded seasonal slots and years and are serially dependent. Models will include year-level clustering or random intercepts, seasonal-slot controls, and blocked resampling that keeps contiguous within-year sequences intact; no individual six-hourly record will be treated as independent.
- Validation: Before fitting the substantive models, reproduce the documented anomaly relationship between ana60n, sea60n, and tran60n under verified indexing; check coordinate monotonicity, finite-value handling, profile aggregation, regime balance by season and year, and recovery of injected symmetric versus asymmetric signals in synthetic data using the planned blocked-resampling code.
- Split strategy: Use leave-one-year-out or grouped multi-year blocked cross-validation for any predictive formulation and year-block bootstrap or permutation within seasonal strata for association uncertainty. All choices are fixed before inspecting regime-specific target associations.
- Claim ceiling: associational

**Analysis strategy**

1. Verify coordinate values, calendar mapping, finite-value coding, variable signs, and the formula relating ana60n, sea60n, and tran60n before defining physical lags or interpreting a forcing direction.
2. Define weak and strong background regimes symmetrically from a predeclared ubar-based vortex diagnostic, using season-stratified quantiles or standardized departures and a neutral exclusion band; repeat with uref only if its verified definition supports it as an alternative reference-flow diagnostic.
3. Summarize transient fawa and epz in metadata-justified lower and response height bands, retaining profile-resolved sensitivity analyses so vertically distinct forcing structures are not collapsed without inspection.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Use future wave-activity or forcing departures as a temporal-direction negative control for earlier circulation change, with the exact offset set before outcome inspection.; Use season-stratified circular time shifts within year blocks that preserve marginal distributions but break the predeclared lag alignment.
- Positive controls: Synthetic injected profile time series with known sign-reversed symmetric and asymmetric lag structures must be recovered by the complete preprocessing and blocked-resampling workflow.; The algebraic ana60n, sea60n, and tran60n relationship must reproduce within documented numerical tolerance after missing-value conventions are verified.
- Alternative explanations: Unequal occurrence of weak and strong regimes across seasonal slots or years could mimic an asymmetry.; Threshold choice or unequal background-magnitude distributions could manufacture a regime contrast.; plus 3 additional item(s) in the complete dossier

**Interpretation limits**

- The plan estimates temporal observational associations in a single-latitude reanalysis-derived record and cannot identify causal wave forcing, mechanisms, regional sources, or external drivers.
- Physical interpretation remains contingent on verified field definitions, signs, units, height coordinates, and calendar semantics.
- No numerical result, event count, association, or regime-specific outcome was inspected or claimed during planning.

**Why the plan serves the question**

It retains the protected weak-versus-strong polarity contrast, tests sign and response symmetry rather than treating weakening as canonical, explicitly separates magnitude from temporal asymmetry, and protects against the invariant's stated threats from seasonal imbalance, threshold manufacture, and vertical-structure confounding.

**Before any later execution**

- Unresolved planning decisions: Authoritative variable formulas, signs, units, and missing-value conventions are required before substantive interpretation.; The height coordinate and physical seasonal calendar must be verified before locking the vortex diagnostic band, forcing band, response band, and lag windows.; plus 1 additional item(s) in the complete dossier
- Required future skills: A reproducible NetCDF/HDF5 ingestion and metadata-audit capability that reconstructs encoded time without silently assuming a calendar.; A dependence-aware longitudinal profile-analysis capability with grouped resampling, predeclared lagged interaction models, and synthetic method-recovery tests.

### Scientific stakes

**Discriminating observation**

Symmetry would be supported if oppositely signed wave and forcing departures show comparable temporal ordering and circulation responses in weak and strong regimes; systematic differences in sensitivity, persistence, or vertical progression would support regime dependence.

**What possible outcomes would mean**

- Positive pattern: Symmetry would support treating weak and strong vortex behavior as opposing expressions of a shared relationship.
- Negative pattern: Robust asymmetry would imply that strong-vortex and weak-vortex dynamics require distinct observational descriptions.
- Null or ambiguous pattern: Definition-sensitive or inconsistent differences would leave regime symmetry unresolved and prioritize construct refinement.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan preserves the weak-versus-strong polarity contrast and uses a symmetric, associational framework with appropriate safeguards for seasonal imbalance, serial dependence, vertical aggregation, and non-causal interpretation. Remaining items are execution-stage specification and metadata-verification locks, not deficiencies in the planning dossier.

Retained changes and locks:

- **Pre execution lock:** Before execution, verify authoritative variable definitions, signs, units, missing-value handling, height coordinates, and calendar semantics; then lock the physically meaningful bands, lag windows, and symmetry transformation separately for fawa and epz.
- **Pre execution lock:** Before execution, fix symmetric regime cutoffs, neutral-band treatment, and the baseline-adjustment/timing specification so that associations with subsequent ubar change are not mechanically driven by defining regimes from baseline ubar.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan operationalizes a genuine symmetric test of weak-versus-strong vortex regimes without collapsing into the sibling's vertical-coherence axis, keeps the claim ceiling associational, and pre-registers regime definitions, lag windows, and validation before any target association is inspected. It includes credible positive controls (synthetic sign-reversed recovery, algebraic anomaly reproduction), negative controls (temporal-direction and circular-shift falsification), dependence-aware inference (year-block clustering, blocked resampling), and explicit alternative explanations for seasonal imbalance, threshold manufacture, and vertical-structure confounding. The two Owner-identified items concern metadata verification and regime-cutoff specification that the plan already treats as pre-execution gates rather than open scientific gaps, so they are correctly pre-execution locks rather than blockers.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
