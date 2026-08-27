# Historical stability of ordinary and extreme vortex variability — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether historical variation appears as a broad distributional shift or as selective change in extremes. One variant emphasizes circulation-state tails; the other emphasizes forcing-history tails and their relationship to circulation outcomes.

The scientific tension is:

Multi-decadal stratospheric variability may be historically stable apart from ordinary sampling fluctuations, may shift approximately uniformly, or may change disproportionately in consequential tails.

## Variant 1: Circulation-distribution tail stability

### Why it matters

Extremes organize major stratospheric disturbances, so historical stability cannot be inferred safely from changes in the mean state alone.

### Original and refined question

**Original Question Scientist proposal**

Across the multi-decadal record, do extreme weak and strong vortex states change in step with the central circulation distribution, or do the tails exhibit disproportionate historical variation?

**Reviewed refined question**

Across the documented multi-decadal ubar record, do pre-specified weak and strong circulation tails vary relative to the central distribution more than is compatible with a common location shift?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Multiple decades of seasonal departures may allow a later planner to compare central and tail behavior under pre-specified distributional summaries.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The supplied description identifies ubar as a zonal-mean wind perturbation or polar-vortex wind diagnostic, ana60n as full analysis fields, tran60n as transient anomalies, and sea60n as a multi-year seasonal climatology over approximately 1979-2021.
  - Limitation: This is operator-supplied documentation rather than file-encoded metadata or independent owner documentation.
  - Limitation: Sign convention, physical units, exact calendar mapping, missing-value handling, and reanalysis homogeneity remain unresolved.
- **Unverified planning evidence:** The verified ana60n.nc and tran60n.nc files each contain float32 fawa, ubar, uref, and epz arrays with common dimensions (height=97, time=124, month=12, year=43); the seasonal file has the corresponding dimensions without year.
  - Limitation: The report verifies structural readability, not scientific meaning, temporal homogeneity, or a result.
  - Limitation: The files have no user-visible units, long names, calendar semantics, fill-value convention, or transformation provenance.

### Plan at a glance

- Population and scope: Observed six-hourly-slot-by-month circulation records on the dataset's 97-level 60 degrees North vertical grid across its 43 indexed years; inference is limited to this derived reanalysis product and its verified temporal indexing after calendar validation.
- Unit of observation: A pre-specified ubar value at one validated height representation and one validated seasonal time cell.
- Unit of inference: Year-block or winter-season block, with within-season observations treated as serially dependent rather than independent replicates.
- Hierarchy and dependence: Model repeated cells nested within year and season, preserve autocorrelation with block resampling or clustered uncertainty, and avoid treating adjacent six-hourly slots or heights as independent evidence.
- Validation: Before target estimation, verify coordinate decoding, missingness, ana-minus-sea versus tran consistency within a small predeclared structural check, and recovery of known synthetic common-shift versus tail-scale scenarios using the planned estimator.
- Split strategy: Use blocked year-level resampling and leave-contiguous-year-block-out sensitivity analysis; do not randomly split temporally adjacent cells.
- Claim ceiling: associational

**Analysis strategy**

1. Resolve ubar sign and representation from documentation, then choose a pre-specified physically motivated level or vertical summary without target-outcome tuning.
2. Use transient anomalies as the primary seasonal-adjusted representation and compare against analysis fields with explicit seasonal adjustment as a robustness representation.
3. Define weak and strong tails from fixed pooled reference quantiles or a pre-declared extreme-value threshold, and define the center by pre-declared central quantiles.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: A permutation of year-block labels that preserves within-block dependence, used only to check the analysis pipeline's null calibration.; A central-quantile contrast that should not be labeled as tail-specific change when all quantiles move together.
- Positive controls: Synthetic injected common-shift and tail-scale changes, which the estimator should distinguish before use on the target fields.
- Alternative explanations: Changing seasonal sampling or padded-calendar treatment.; Changing mixture of recurrent circulation states rather than within-state distributional change.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- This observational derived-product analysis cannot establish atmospheric causation or distinguish physical change from reanalysis-system changes without external corroboration.
- Planning evidence establishes variables and dimensions, not a historical trend, tail change, or statistical power.

**Why the plan serves the question**

It directly treats the circulation distribution as the outcome and contrasts weak and strong tails with its center, while making common shifts, state mixtures, sampling, and measurement instability competing explanations rather than silently redefining the question.

**Before any later execution**

- Unresolved planning decisions: Exact ubar physical interpretation, sign, units, and valid vertical representation.; Calendar decoding and the defensible seasonal and year-block definitions.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

Disproportionate tail variation would be supported if weak or strong extremes change relative to the center in a manner inconsistent with a common additive shift and stable under reasonable state and period definitions.

**What possible outcomes would mean**

- Positive pattern: A positive result would show that mean-state summaries understate historically varying extreme behavior.
- Negative pattern: Tail changes tracking the center would support a simpler common-shift description of the observed distribution.
- Null or ambiguous pattern: Imprecise or definition-sensitive differences would preclude a claim of either stability or tail-specific change.

## Variant 2: Forcing-distribution tail and response correspondence

### Why it matters

This question links distributional change in a candidate dynamical ingredient to response behavior while preserving the observational limit on mechanism claims.

### Original and refined question

**Original Question Scientist proposal**

Do historically extreme wave-activity or eddy-forcing episodes vary disproportionately relative to ordinary forcing, and is any tail variation mirrored by the distribution of subsequent vortex responses?

**Reviewed refined question**

Do pre-specified extreme fawa or epz episodes vary relative to ordinary forcing across the documented multi-decadal record, and does their subsequent ubar response distribution change in a manner distinguishable from changing background susceptibility?

**Reviewed planning disposition**

Accepted for planning.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Long, vertically resolved forcing and circulation histories may allow later comparison of ordinary and extreme forcing episodes and their subsequent responses.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The supplied description identifies fawa as finite-amplitude wave activity or pseudomomentum density, epz as eddy forcing related to EP flux, and ubar as a polar-vortex wind diagnostic; it describes ana60n as full fields and tran60n as anomalies with shared temporal dimensions.
  - Limitation: This is operator-supplied documentation rather than file-encoded metadata or independent owner documentation.
  - Limitation: The diagnostic equations, sign conventions, units, exact temporal mapping, and external reanalysis check remain unresolved.
- **Unverified planning evidence:** The verified ana60n.nc and tran60n.nc files each contain float32 fawa, ubar, uref, and epz arrays with common dimensions (height=97, time=124, month=12, year=43), permitting planning of aligned forcing-history and subsequent-response units.
  - Limitation: The report verifies structural readability, not a forcing-response relationship or causal mechanism.
  - Limitation: The files have no user-visible units, long names, calendar semantics, fill-value convention, or transformation provenance.

### Plan at a glance

- Population and scope: Observed co-indexed forcing and circulation cells on the dataset's 97-level 60 degrees North vertical grid across its 43 indexed years, subject to validation of time mapping and diagnostic provenance.
- Unit of observation: A pre-specified forcing episode constructed from validated fawa or epz values over a documented vertical and temporal window, linked to a later pre-specified ubar response window.
- Unit of inference: Independent or weakly dependent seasonal/year blocks containing candidate episodes, with episode clusters within a block handled as dependent.
- Hierarchy and dependence: Preserve temporal ordering and vertical structure, cluster uncertainty by year-season block, use non-overlapping or appropriately censored response windows, and account for repeated episodes within blocks.
- Validation: Before target estimation, verify common-coordinate alignment, missingness, bounded ana/tran/sea structural consistency, absence of response-window overlap errors, and synthetic recovery of stable correspondence versus changed susceptibility scenarios.
- Split strategy: Use chronology-respecting blocked year-level resampling and hold out contiguous year blocks for stability checks; thresholds and episode definitions remain fixed across resamples.
- Claim ceiling: associational

**Analysis strategy**

1. Resolve fawa and epz equations, signs, units, and valid vertical aggregation before selecting a single primary forcing diagnostic and a pre-specified alternate diagnostic.
2. Construct seasonally adjusted forcing from tran60n or a documented ana60n adjustment, then define ordinary and extreme forcing categories with pooled fixed thresholds determined before historical comparisons.
3. Align each forcing episode to a pre-specified subsequent ubar response window only after validating the within-month time coordinate and calendar.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Temporally shifted response windows outside the pre-specified response lag, used to check alignment and leakage rather than to select a lag.; Year-block-label permutations that preserve within-block serial structure for pipeline calibration.
- Positive controls: Synthetic datasets with known forcing-category response correspondence and known susceptibility modification, used to verify estimator discrimination.
- Alternative explanations: Changing background susceptibility represented incompletely by uref or circulation state.; Diagnostic convention, vertical aggregation, or sign errors in fawa or epz.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- The forcing-response association is observational and cannot identify causal forcing potency or separate all background susceptibility pathways.
- The package's missing diagnostic equations, units, provenance, and external reanalysis comparison limit physical interpretation.
- Planning evidence establishes co-dimensioned variables, not episodes, response changes, or effect estimates.

**Why the plan serves the question**

It retains forcing extremes and their later circulation correspondence as the target, explicitly compares forcing-tail change with response change, and treats background susceptibility and diagnostic artifacts as alternatives rather than collapsing the question into the circulation-only sibling.

**Before any later execution**

- Unresolved planning decisions: Whether fawa, epz, or a documentation-supported combination is the primary forcing construct.; Diagnostic equations, units, signs, vertical aggregation, and lag windows.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

A forcing-tail-specific change would be supported if extremes vary relative to the center and the change is accompanied by a coherent alteration in subsequent circulation responses; stable forcing tails with changing responses would instead favor changing susceptibility.

**What possible outcomes would mean**

- Positive pattern: A positive result would motivate historical accounts that distinguish changes in extreme dynamical forcing from ordinary variability.
- Negative pattern: If forcing tails and responses remain proportional to their centers, a common-scale description would be favored.
- Null or ambiguous pattern: Unstable forcing–response correspondence would leave open diagnostic artifacts, changing susceptibility, or heterogeneous extreme pathways.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve their distinct scientific targets and provide credible observational, dependence-aware routes to distinguish broad distributional shifts from tail-specific variation. Remaining uncertainties are appropriately explicit execution-stage locks rather than planning blockers.

Retained changes and locks:

- **Pre execution lock:** Validate diagnostic semantics, units, signs, missing-value handling, and transformation provenance before operationalizing circulation or forcing measures.
- **Pre execution lock:** Validate calendar decoding and within-month temporal mapping before defining seasonal windows, lags, or forcing-response episodes.
- **Pre execution lock:** Lock the primary diagnostic, vertical representation, tail definitions, and response-window choices before target comparisons.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both sibling plans credibly operationalize their distinct scientific targets using the shared co-dimensioned ana60n/tran60n/sea60n arrays. The circulation-tail variant treats the ubar distribution itself as the outcome and contrasts pre-specified weak/strong tails against the center under a common-shift null, while the forcing-tail variant treats fawa/epz extremes and their subsequent ubar response correspondence as the target, explicitly preserving background-susceptibility as a competing explanation. This separation respects the family's forbidden-semantic-merge constraints. Claim ceilings are associational with explicit interpretation limits, competing explanations (state mixture, reanalysis discontinuities, calendar/seasonal artifacts, diagnostic sign/unit errors) are enumerated, and both plans specify positive/negative controls and dependence-aware estimation (blocked resampling, clustered uncertainty). The three Owner-identified issues (diagnostic semantics/provenance, calendar/temporal mapping, and locking primary diagnostic/tail definitions/response windows before comparisons) are all execution-stage validations that do not prevent approving the plan as a credible, non-executable analysis product; they are appropriately treated as pre-execution locks rather than scientific blockers. No hard-boundary or intent-drift concern is present at this review round.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
