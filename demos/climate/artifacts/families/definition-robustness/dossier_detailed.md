# Scientific robustness across vortex-state and event definitions — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Asks whether substantive conclusions about polar-vortex variability survive changes in representation. One variant concerns event identity and lifecycle structure; the other concerns the stability of precursor relationships.

The scientific tension is:

Threshold events, continuous circulation states, and alternative vertical representations may identify different phenomena, so an apparent dynamical conclusion may be robust or may be induced by the chosen definition.

## Variant 1: Directional intensity-lifecycle portability across paired representations

### Why it matters

Separating portable intensity-lifecycle features from threshold artifacts and geometry mixtures would clarify which claims describe stable vortex evolution and which must remain tied to a particular representation or configuration.

### Original and refined question

**Original Question Scientist proposal**

Which features of rapid weakening and strengthening lifecycles remain stable when the polar vortex is represented by threshold events versus recurrent continuous circulation states?

**Post-novelty revised proposal**

Which ordering, vertical-evolution, and pre- versus post-extremum rate features of intensity-defined weak-to-strong strengthening and strong-to-weak weakening lifecycles remain portable between paired threshold-event and recurrent continuous-state representations, and do those features remain stable when conditioned on independently defined displacement, stretching, or wave-phase configurations?

**Reviewed refined question**

Across the documented multilevel record, which prespecified ordering, vertical-evolution, and pre-versus-post-extremum rate features agree between threshold-defined and recurrent continuous intensity-state lifecycles when weak-to-strong strengthening and strong-to-weak weakening are analyzed separately?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If documentation confirms a sufficiently resolved multilevel circulation-intensity record, it may support paired representations of the same winters: threshold events based on a reference-level intensity and its tendency, and recurrent trajectories based on the multilevel intensity profile and tendency. Geometry or wave-phase conditioning is an additional requirement for the broad portability claim and would depend on independently available, defensible diagnostics rather than being inferred from intensity states.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The report documents ana60n.nc and tran60n.nc as four float32 arrays named fawa, ubar, uref, and epz on fixed dimensions height=97, time=124, month=12, and year=43; each analysis variable has shape (97, 124, 12, 43).
  - Limitation: This is structural documentation rather than scientific validation of variable meaning.
  - Limitation: The files have no user-visible units, long names, calendar semantics, fill-value conventions, or transformation provenance.
- **Unverified planning evidence:** The supplied context describes a one-dimensional 60 degrees North vertical grid and explicitly states that the package has no longitude or latitude dependence and cannot by itself support wave phase structure, displacement, or stretching diagnostics.
  - Limitation: This is operator-supplied context, not independent dataset-owner documentation.
  - Limitation: It does not establish the physical units, sign conventions, or exact dates of the arrays.

### Plan at a glance

- Population and scope: Eligible repeated within-year observations from ana60n.nc or tran60n.nc after a prespecified seasonal window and calendar interpretation; the study concerns the supplied 60 degrees North one-dimensional record only.
- Unit of observation: One documented height-by-slot observation, assembled into prespecified contiguous episodes.
- Unit of inference: Independent winter-season or year block, with episodes nested within blocks.
- Hierarchy and dependence: Retain height and within-episode serial dependence; estimate episode features first and use year-blocked resampling or hierarchical models so repeated slots and multiple episodes do not inflate inference.
- Validation: Before outcome comparison, verify that recurrence coordinates recover held-out neighborhood assignments under year-blocked resampling, that episode roles can be assigned without using the target feature, and that both representations meet the frozen persistence convention.
- Split strategy: Block all tuning and validation by year or winter season; keep all heights and slots from a block together and select recurrence hyperparameters only in development blocks.
- Claim ceiling: associational

**Analysis strategy**

1. Freeze a reference-height intensity variable, direction convention, baseline class, weak and strong levels, rapidity rule, and shared minimum persistence after field documentation is available.
2. Construct threshold episodes from sustained directional crossings without using geometry or phase information.
3. Construct recurrent episodes from persistent neighborhoods in a multilevel intensity-and-tendency coordinate set selected without encoding the desired lifecycle ordering.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: A temporally permuted within-season episode-role mapping that preserves sampling structure but breaks lifecycle ordering.; A height-order permutation for vertical-evolution summaries, used only to test whether the summary is sensitive to vertical ordering.
- Positive controls: Synthetic trajectories with known onset, extremum, recovery, and vertical ordering to verify that both extraction procedures recover injected features without forcing equal boundaries.
- Alternative explanations: Unequal seasonal sampling, duration, persistence, or temporal resolution across representations.; Agreement induced by common use of the scalar extremum rather than shared lifecycle dynamics.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- This design does not establish causal mechanisms.
- No geometry- or wave-phase-conditioned portability claim is available from the one-dimensional package.
- No physical interpretation is permitted until field definitions and sign conventions are documented.

**Why the plan serves the question**

It preserves the required paired threshold and continuous representations, directional separation, role-based lifecycle comparison, and feature-level—not count-level—portability criterion while honestly delimiting unavailable configuration conditioning.

**Before any later execution**

- Unresolved planning decisions: Field and reference-height selection must be justified from authoritative variable documentation.; The seasonal analysis window and thresholds must be frozen before target-feature estimation.
- Required future skills: NetCDF extraction with documented calendar and missing-value handling.; Persistent recurrent-state trajectory construction with year-blocked tuning and synthetic method-recovery tests.

### Scientific stakes

**Discriminating observation**

The threshold-event object will be a sustained crossing of a prespecified weak or strong level by a reference-level polar-vortex intensity variable, with rapidity defined separately by a prespecified intensity-change criterion. The recurrent continuous-state object will instead be a persistent trajectory through recurrent neighborhoods of a multilevel intensity-and-tendency state space, without using geometry or phase to define intensity states. Both will use the same prespecified minimum-persistence convention and the same onset–peak–recovery roles: onset is the first sustained entry toward the target intensity class, peak is the intervening intensity extremum, and recovery is the first sustained return toward the baseline class, with representation-specific entry boundaries recorded rather than forced to coincide. Portability requires feature-level agreement in the ordering of stages, vertical evolution, and pre- versus post-extremum transition rates, assessed separately for weak-to-strong strengthening and strong-to-weak weakening. Agreement in event counts or broad composites alone is insufficient. The same features must also remain stable within independently defined displacement, stretching, or wave-phase strata; if those diagnostics are unavailable or indefensible, geometry-conditioned portability cannot be claimed.

**What possible outcomes would mean**

- Positive pattern: If lifecycle ordering, vertical evolution, and rate asymmetries agree across the paired representations for each transition direction and remain stable within geometry or phase strata, the supported features could be treated as portable properties of intensity evolution rather than products of one event definition.
- Negative pattern: If feature ordering, vertical expression, or directional rate asymmetry systematically disappears or reverses across representations or geometry strata, lifecycle claims would need to remain explicitly tied to the defining representation and configuration.
- Null or ambiguous pattern: Mixed or imprecise agreement would support a layered account in which only specified lifecycle features are portable, while others remain definition- or geometry-dependent; inability to condition on geometry would leave the broader portability claim unresolved.

## Variant 2: Factorial robustness of precursor–transition relationships and downstream implications

### Why it matters

Separating precursor-measurement robustness from outcome-measurement robustness would clarify which parts of a forcing–transition relationship are scientifically portable. Stratifying rather than pooling major/minor, split/displacement, and downward/non-downward behavior would also prevent subclass composition or definition-sensitive tropospheric signals from being mistaken for a general precursor mechanism.

### Original and refined question

**Original Question Scientist proposal**

Are inferred associations between wave-forcing histories and subsequent vortex transitions robust across alternative circulation indices, vertical representations, and event thresholds?

**Post-novelty revised proposal**

When precursor measurement and vortex-transition diagnosis are varied independently using scientifically non-equivalent constructions, does the association between a prespecified antecedent wave-forcing history and subsequent stratospheric transition retain its sign, magnitude, temporal ordering, and state dependence across major versus minor, split versus displacement, and downward versus non-downward event classes—and is any robustness of transition identification distinct from robustness of later tropospheric signals?

**Reviewed refined question**

Using one frozen antecedent-to-transition lag window, does the association between alternative documented wave-related histories and independently constructed multilevel stratospheric transition measures retain sign, standardized magnitude, and timing across prespecified circulation-severity classes?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If documentation review establishes that the available variables support multiple defensible and scientifically non-equivalent constructions, complementary wave diagnostics could represent antecedent forcing histories while circulation indices, vertical characterizations, and event definitions independently represent subsequent transitions. The same record might then permit separate assessment of stratospheric transition identification and any downward or tropospheric signal; this capability is not yet established.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The report documents repeated multilevel observations in ana60n.nc and transient anomalies in tran60n.nc, each containing fawa, ubar, uref, and epz with dimensions height=97, time=124, month=12, and year=43.
  - Limitation: The report establishes file structure and readability only.
  - Limitation: The NetCDF files contain no user-visible scientific attributes or transformation provenance.
- **Unverified planning evidence:** The supplied context labels fawa as wave activity or pseudomomentum density, epz as eddy forcing related to EP flux, ubar as a zonal-mean wind perturbation or polar-vortex wind diagnostic, and uref as reference zonal wind; it also states that the package lacks horizontal fields, temperature, geopotential height, potential vorticity, and surface variables.
  - Limitation: The variable labels are operator-supplied and lack equations, units, sign conventions, and provenance.
  - Limitation: The stated spatial scope precludes defensible split-versus-displacement, wave-phase, downward-propagation, and tropospheric-impact classifications from this package alone.

### Plan at a glance

- Population and scope: Eligible repeated observations in the documented 60 degrees North multilevel record; claims concern stratospheric transition measures only and exclude unobserved geometry, downward behavior, and tropospheric impacts.
- Unit of observation: One height-by-slot observation, aggregated only into prespecified antecedent histories and subsequent transition windows.
- Unit of inference: Independent winter-season or year block, with serially dependent observations nested within it.
- Hierarchy and dependence: Model histories and transitions with block-level resampling or hierarchical time-series methods; retain all observations from a year block together to avoid temporal leakage.
- Validation: Verify non-redundancy analytically from field definitions before target estimation; use synthetic lagged processes with known common and construction-specific signals to test recovery of sign, timing, and standardized magnitude contrasts.
- Split strategy: Use year-blocked development and evaluation partitions, retain complete seasonal histories within blocks, and freeze lag and construction rules without reference to held-out association outcomes.
- Claim ceiling: associational

**Analysis strategy**

1. Obtain authoritative definitions and demonstrate that selected fawa- and epz-based history families are scientifically non-equivalent rather than algebraic transformations.
2. Freeze one antecedent window and lag rule before estimating associations, then construct each forcing history independently of the transition labels.
3. Define at least two non-equivalent circulation or vertical transition constructions from documented ubar and uref information, rejecting constructions that are merely nearby thresholds of the same scalar.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Season-preserving circularly shifted forcing histories that break the prespecified antecedent ordering.; A future forcing window that cannot be an antecedent under the frozen ordering.
- Positive controls: Synthetic multilevel time series with injected lagged common and construction-specific components to verify independent-construction and timing recovery.
- Alternative explanations: Apparent agreement from shared information or algebraic redundancy between nominally different constructs.; Seasonal background, unequal scaling, precision, or event prevalence differences.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- The observational record cannot support a causal wave-forcing claim.
- The package lacks the fields needed for split-versus-displacement, wave-phase, downward-behavior, and tropospheric-impact classifications.
- No association interpretation is permitted until the derived-variable equations and signs establish scientific non-equivalence.

**Why the plan serves the question**

It retains the factorial independence of precursor and transition constructions, preserves temporal ordering and sign-and-magnitude comparison, and distinctly limits the inference to supported stratospheric transition robustness rather than substituting unavailable subclass or downstream measures.

**Before any later execution**

- Unresolved planning decisions: Select forcing-history and transition-construction families only after equations establish their scientific distinction.; Freeze lag window, seasonal adjustment, vertical bands, and circulation-severity strata before target association estimation.
- Required future skills: Authoritative derived-field documentation ingestion and construct non-redundancy audit.; Leakage-safe lagged multilevel association modeling with block-level resampling and synthetic method recovery.

### Scientific stakes

**Discriminating observation**

Before comparing representations, specify one common antecedent-to-transition ordering and lag window. Independently vary candidate non-equivalent forcing-history families—such as eddy heat-flux, upward wave-activity-flux, or resolved wavenumber-component histories where defensible—and non-equivalent transition constructions based on distinct circulation or vertical information, excluding nearby thresholds and algebraic restatements as independent corroboration. Evaluate concordance in association sign, comparable magnitude, and dependence on major/minor, split/displacement, and downward/non-downward strata, rather than counting statistical detection alone. Assess robustness of stratospheric transition identification first and robustness of subsequent downward or tropospheric signals as a separate outcome. Geometry-based and downward-behavior strata enter only if they can be defensibly established from the available information; otherwise their absence remains an explicit scope limitation.

**What possible outcomes would mean**

- Positive pattern: Concordant sign, comparable magnitude, common temporal ordering, and similar subclass dependence across independently varied, non-equivalent precursor and transition constructions would support a representation-portable forcing–transition relationship. Separate concordance for downstream signals would be required before extending that conclusion to stratosphere–troposphere impacts.
- Negative pattern: Systematic sign changes, materially different magnitudes, or reversed subclass dependence attributable specifically to precursor construction, transition construction, or downstream-outcome construction would restrict the scientific claim to those representations and identify where portability fails.
- Null or ambiguous pattern: If no stable association is supported under the common ordering and lag window, or if available information cannot distinguish a weak relationship from representation-specific imprecision, the evidence would not support a portable precursor claim. Mixed agreement would instead motivate a layered conclusion separating robust stratospheric transition associations from construct-dependent subclass or tropospheric outcomes.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The paired plans preserve the distinct lifecycle-portability and precursor-association questions, use independent representation contrasts, preserve directional and temporal ordering, and appropriately limit claims to the documented one-dimensional stratospheric record. Remaining field-definition and operational choices are explicit pre-execution locks, not planning-stage scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Before execution, obtain authoritative definitions and provenance for the derived fields, including equations, units, signs, calendar mapping, and missing-data conventions; then freeze the corresponding construct, seasonal, lag, and threshold choices without using target outcomes.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve the protected family intent as a strict separation between construct-recovery (lifecycle ordering/vertical evolution) and association-robustness (precursor-transition link) questions, matching the allowed target_contrast axis and avoiding the forbidden semantic merge. Each plan is grounded only in the documented multilevel arrays and explicitly limits claims to what those arrays can support, deferring geometry, wave-phase, split-versus-displacement, downward-propagation, and tropospheric-impact claims as out-of-scope rather than smuggling them in as substantive conclusions. Alternative explanations, positive/negative controls, leakage-safe year-blocked validation, and duration/rate normalization are specified for both variants. The single outstanding item — obtaining authoritative field definitions, units, signs, and provenance before freezing construct/threshold choices without peeking at outcomes — is a pre-execution lock rather than a scientific blocker, since the plans already commit to outcome-independent specification once documentation is available. No hard boundary is implicated and no new scientific blocker is warranted at this planning stage.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
