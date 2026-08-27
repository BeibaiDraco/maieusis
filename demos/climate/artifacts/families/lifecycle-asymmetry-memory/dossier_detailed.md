# Lifecycle asymmetry and dynamical memory in vortex disturbances — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Examines whether vortex disturbance lifecycles are reversible or history-dependent. One variant compares onset and recovery pathways; the other asks whether forcing history organizes recovery among similarly weakened states.

The scientific tension is:

Vortex weakening and recovery may be approximately reverse expressions of one circulation mode, or recovery may follow distinct, history-dependent pathways with persistent dynamical memory.

## Variant 1: Reversibility of onset and recovery

### Why it matters

Lifecycle asymmetry would show that disturbance magnitude alone is insufficient to characterize vortex evolution and could expose distinct organizing processes during recovery.

### Original and refined question

**Original Question Scientist proposal**

Are the vertical circulation and wave–mean-flow pathways into major vortex weakening the time reverse of recovery, or do onset and recovery exhibit reproducible lifecycle asymmetry?

**Reviewed refined question**

Among predeclared major weakening episodes in the documented 60 degrees North transient circulation record, are vertically resolved approach trajectories and exit trajectories through matched circulation-departure states approximate time reverses, or do their duration, vertical ordering, and accompanying documented wave-activity and eddy-forcing histories differ after seasonal matching?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Repeated, vertically resolved circulation, wave, and forcing histories may allow later planning of matched trajectory comparisons into and out of similarly disturbed states.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The supplied context describes a 60 degrees North, vertically resolved, six-hourly nominal stratospheric dynamics package intended for polar-vortex variability and wave-mean-flow interaction. It describes tran60n.nc as transient anomalies relative to sea60n.nc and labels fawa as wave activity, ubar as a zonal-wind or polar-vortex diagnostic, uref as a reference zonal wind, and epz as eddy forcing.
  - Limitation: Variable meanings, anomaly formula, temporal mapping, units, signs, and fill values are operator-supplied claims rather than file-encoded metadata.
  - Limitation: The one-dimensional 60 degrees North product lacks horizontal structure and cannot adjudicate regional wave-source or attribution explanations.
  - Limitation: This documentation is planning evidence only and supplies no scientific outcome.
- **Unverified planning evidence:** The verified ana60n.nc and tran60n.nc files each contain fawa, ubar, uref, and epz as float32 arrays with dimensions (height=97, time=124, month=12, year=43); sea60n.nc contains the same variables over height, time, and month only. This supplies repeated vertically resolved observations and a supplied transient product suitable for a prospective trajectory-comparison design.
  - Limitation: This report establishes file readability and array structure, not the physical interpretation, units, signs, or transformations of the four fields.
  - Limitation: The encoded files have no user-visible calendar semantics, missing-value convention, or derivative provenance.
  - Limitation: No event frequencies, trajectory shapes, or target-outcome statistics were examined.

### Plan at a glance

- Population and scope: The target population is qualifying disturbance lifecycles represented in the 43-year, 60 degrees North, vertically resolved records. The claim is limited to this derived product and cannot generalize to horizontal wave geometry, regional sources, other latitudes, or impacts.
- Unit of observation: A vertical profile at one nominal six-hourly slot, month, and year; profile-derived state summaries will be specified before execution.
- Unit of inference: A distinct qualifying disturbance lifecycle, with year-level clustering retained because multiple lifecycles can occur within a year.
- Hierarchy and dependence: Slots are serially dependent within trajectories, heights are jointly observed within profiles, and trajectories are nested within years. Estimate trajectory contrasts at the episode level; use year-cluster or block-bootstrap uncertainty and never treat height-by-time cells as independent replicates.
- Validation: Implement deterministic synthetic trajectories with known mirrored and intentionally asymmetric paths to verify alignment, reversal, pairing, and clustered-resampling code. Before scientific estimation, audit profile coverage, temporal adjacency, duplicate/padded slots, missingness, event-window overlap, and whether matching remains possible under each prespecified severity rule.
- Split strategy: No predictive train-test split is primary. All tuning choices, event definitions, alignments, seasonal matching strata, and summary windows must be frozen from metadata, synthetic recovery tests, and non-outcome structural checks; uncertainty uses resampling blocks at the year or episode level.
- Claim ceiling: associational

**Analysis strategy**

1. Before seeing target comparisons, confirm calendar decoding, signs, units, missing-value rules, and the transient formula from owner documentation; stop or revise the operationalization if they contradict the supplied semantics.
2. Predeclare a ubar-based disturbance-state index from the documented vertical grid after sign and level interpretation are resolved; identify local minima crossing a severity threshold and require nonoverlapping onset and recovery windows with adequate observed coverage.
3. For each episode, align onset and recovery by matched values of the state index rather than by threshold dates alone; reverse the onset time axis only after alignment and retain all prespecified alternative alignments.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Apply the same matching and reversal procedure to temporally permuted whole-episode labels within seasonal strata; any apparent asymmetry in this control indicates an alignment or dependence artifact.; Compare equal-length windows drawn away from qualifying minima within the same seasonal strata; this assesses generic seasonal directional drift rather than lifecycle-specific asymmetry.
- Positive controls: Synthetic mirrored trajectories must yield near-zero planned distance and synthetic lagged/asymmetric trajectories must recover the implanted direction and duration difference.; The supplied transient field should pass a structural consistency check against the documented seasonal product only if the owner confirms the exact anomaly formula and calendar indexing.
- Alternative explanations: Residual seasonal evolution or padded-month timing may generate directional differences even after seasonal matching.; Threshold definition, episode severity mixtures, partial recoveries, or window overlap may create artificial duration asymmetry.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- This observational derived dataset can test reproducible trajectory association, not establish that any forcing causes recovery asymmetry.
- The plan is conditional on resolving missing metadata; it does not assume physical signs, units, dates, or budget closure.
- No estimate, effect, event count, or scientific result has been inspected or produced during planning.

**Why the plan serves the question**

The primary contrast remains the geometry of entire onset versus recovery trajectories through matched disturbance states. It explicitly tests time reversal with vertical circulation and documented wave-mean-flow aliases while treating seasonality, alignment, severity, and incomplete recovery as competing explanations rather than silently converting the question into a history-conditioned recovery prediction.

**Before any later execution**

- Unresolved planning decisions: Owner or source documentation must specify valid time ordering across month/year boundaries, leap-day and padded-slot treatment, and missing-value conventions.; Owner review is required for the semantic mapping of 'major vortex weakening' to a sign-resolved, vertically aggregated ubar transient index.; plus 1 additional item(s) in the complete dossier
- Required future skills: A planning-faithful lifecycle-trajectory executor with metadata validation, synthetic method recovery, prespecified event segmentation, constrained time-reversal alignment, and year-clustered resampling.

### Scientific stakes

**Discriminating observation**

Path dependence would be supported if matched circulation departures are approached and exited through systematically different forcing histories, vertical sequences, or transition durations after accounting for seasonal background; mirrored trajectories would favor approximate reversibility.

**What possible outcomes would mean**

- Positive pattern: Reproducible asymmetry would establish recovery as a distinct scientific phase rather than the passive reversal of onset.
- Negative pattern: Near-mirrored trajectories would support a lower-dimensional reversible-state description for these disturbances.
- Null or ambiguous pattern: Inconsistent asymmetry would suggest dependence on event class, season, or operational definition rather than a general lifecycle property.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan preserves the whole-trajectory time-reversal contrast and uses episode-level, dependence-aware comparisons with appropriate limits on causal and spatial interpretation. Remaining uncertainties concern operational details that must be resolved before execution, not the credibility of the planning dossier.

Retained changes and locks:

- **Pre execution lock:** Before execution, document temporal ordering across month and year boundaries, calendar and padded-slot treatment, and missing-value conventions; use these to freeze valid lifecycle windows and seasonal matching strata.
- **Pre execution lock:** Before execution, specify a sign- and level-resolved ubar-derived disturbance-state index, severity threshold, and episode rule that operationalize major vortex weakening.
- **Pre execution lock:** Before execution, confirm the transient-anomaly formula and the signs, vertical levels, and physical interpretation of fawa and epz; restrict any pathway interpretation to the confirmed semantics.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The plan operationalizes the protected reversibility contrast as a whole-trajectory time-reversal test through matched disturbance states, explicitly avoiding conversion into a forcing-history-conditioned prediction (the sibling variant's territory). Claims are capped at associational, controls (positive/negative, synthetic recovery) are specified, dependence structure (serial slots, nested profiles, year clustering) is respected in the inference plan, and alternative explanations including unresolved sign/unit/calendar semantics are named rather than assumed away. The three remaining Owner issues are correctly pre-execution locks: they concern operational thresholds, metadata decoding, and variable-semantics confirmation needed only before execution, not defects in the planning product itself. No scientific blocker or hard-boundary issue remains at this planning stage.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
