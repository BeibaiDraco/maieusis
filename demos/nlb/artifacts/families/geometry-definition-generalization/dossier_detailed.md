# Which geometric stability supports generalization in reaching? — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Accepted planning dossier**
- Authority: **Automated independent review, planning only; capped at provisional inspiration**
- Accepted-plan authority: **Yes, provisionally and for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Separates two meanings of stable neural geometry: reproducible relational structure within conditions and transferable geometry across reach demands, avoiding duplication of the close prior on generic geometry–behavior coupling.

The scientific tension is:

Geometric stability can mean reproducibility within a condition or transfer across conditions; either may coexist with centroid change, and only the latter directly addresses generalization across reach demands.

## Variant 1: within-condition stability-definition test

### Why it matters

The question clarifies what stability means in motor populations and tests regional boundaries rather than repeating the established geometry–behavior association.

### Original and refined question

**Original Question Scientist proposal**

Do M1 and PMd differ in whether relational reach geometry is reproducible despite shifts in population centroids?

**Reviewed refined question**

Within matched reach conditions, do M1 and PMd differ in the reproducibility of relational population geometry after centroid stability is separately quantified with matched reliability?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

M1 and PMd reach-related population observations may allow later planning of reliability-focused comparisons between relational and centroid-based stability.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 is a single-subject macaque delayed center-out reaching dataset with sorted spiking activity from M1 and PMd plus cursor position, hand position, eye position, and hand velocity. The task uses obstructing barriers that produce straight and curved reaches, and the scaled release contains 100 train and 100 test trials.
  - Limitation: The document describes the release but does not provide trial-wise class labels or certify the number of usable repetitions per trajectory class.
  - Limitation: The release has one subject and a small fixed trial count, so any regional or demand-specific inference requires uncertainty-aware resampling and restricted claims.
  - Limitation: This documentation inspection is planning-only and provides no outcome estimate.
- **Unverified planning evidence:** For MC_Maze releases, the first digit of a unit identifier is the authoritative region indicator: leading 1 denotes PMd and leading 2 denotes M1. The note records that stored M1 electrode indices require a plus-96 correction and reports both regions in the pinned train split after that reconciliation: 72 PMd and 70 M1 units.
  - Limitation: The release note is a conversion caveat and must be implemented and independently validated by the later executor before regional comparison.
  - Limitation: The stated counts do not establish trial-level coverage, unit quality equivalence, or a scientific effect.
  - Limitation: This documentation inspection is planning-only and does not use neural response values.
- **Unverified planning evidence:** The train NWB container exposes behavioral series named hand_pos, cursor_pos, eye_pos, and hand_vel; embedded descriptions identify two-dimensional hand position, cursor position, and hand velocity. It also contains PMd and M1 electrode-array and electrode-group labels.
  - Limitation: String-level schema inspection cannot establish the trial segmentation fields, temporal alignment details, missingness, or usable repetitions.
  - Limitation: No raw behavioral or neural observations were retained or analyzed.
  - Limitation: A later NWB adapter must inspect formal table structure and validate time bases before execution.

### Plan at a glance

- Population and scope: One rhesus macaque in the pinned MC_Maze-S train release; sorted units assigned to PMd or M1 by the documented unit-identifier rule; repeated delayed center-out reaches, subject to later verification of usable condition coverage.
- Unit of observation: A trial-level, event-aligned population response vector in a prespecified movement or preparatory epoch.
- Unit of inference: Independent trial partitions within reach condition, with region comparison interpreted within this one recorded subject.
- Hierarchy and dependence: Trials are nested in reach condition and repeated split assignments; units are nested in region. Estimate geometry separately by region, use the same trial partitions for both measures, and summarize split-to-split uncertainty rather than treating time bins or units as independent replicates.
- Validation: Before scientific estimation, validate corrected region assignment against the documented unit-ID convention, verify common time bases, confirm trial partitions are disjoint, and run synthetic geometry recovery showing that the selected metrics distinguish centroid translation from relational reorganization under matched noise.
- Split strategy: Repeated stratified trial-half splits within verified reach condition; all preprocessing parameters, time windows, and condition definitions are fit inside each training half and evaluated on its paired held-out half.
- Claim ceiling: descriptive

**Analysis strategy**

1. Define reach conditions from verified task metadata and prespecified behavioral bins without using neural outcomes.
2. For each region and independent trial half, estimate condition-by-condition response patterns in matched time windows and compute a cross-validated representational dissimilarity matrix.
3. Quantify relational reproducibility as agreement between independent-half dissimilarity matrices and quantify centroid stability as independent-half distance or correlation of condition centroids using matched normalization.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Permute condition labels independently within split and region to test whether relational agreement exceeds label-free structure.; Use time-shifted non-task epochs when such epochs are available after event validation.
- Positive controls: Synthetic population patterns with fixed relational configuration and translated centroids, plus patterns with relational reorganization, to verify measurement separation.
- Alternative explanations: Unequal trial coverage or unit count across regions.; Different signal-to-noise ratios or estimator sensitivity between centroid and relational measures.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- This is an observational, single-subject recording and cannot establish a mechanism of stabilization or a population-level regional difference.
- A centroid-versus-relational dissociation does not imply transfer across changed reach demands.

**Why the plan serves the question**

It directly compares two non-equivalent definitions of within-condition stability across the documented M1 and PMd populations, while explicitly controlling the unequal-reliability explanation and avoiding a cross-demand transfer claim.

**Before any later execution**

- Unresolved planning decisions: Event-aligned epoch and reach-condition granularity await formal NWB table inspection.; Minimum per-condition trial count will be fixed from metadata before any neural-outcome inspection.
- Required future skills: Validated NWB adapter that extracts trial timing, aligns spike times and behavior, and applies the documented corrected M1/PMd unit assignment.; Cross-validated representational-geometry and centroid-reliability workflow with synthetic method-recovery checks.

### Scientific stakes

**Discriminating observation**

Reliable relational structure alongside unstable centroids, compared across regions with matched reliability assessment, would demonstrate a region-specific or shared dissociation between stability definitions.

**What possible outcomes would mean**

- Positive pattern: A reproducible relational structure despite centroid change would support a descriptive claim that motor representations can be stable at one geometric level while changing at another.
- Negative pattern: Coupled instability of both relational structure and centroids would weaken the proposed dissociation.
- Null or ambiguous pattern: If neither measure is reliable, the meaning and regional scope of stability would remain unresolved.

## Variant 2: cross-demand generalization test

### Why it matters

The question separates measurement reproducibility from scientific generalization and establishes an explicit boundary condition for invariance.

### Original and refined question

**Original Question Scientist proposal**

Does reproducible relational geometry within a reach class transfer across straight and curved reaches, or is within-condition stability compatible with demand-specific remapping?

**Reviewed refined question**

After establishing within-class relational reproducibility, does relational reach geometry transfer between prespecified straight and curved barrier-maze reaches, or remain reliable but demand-specific?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Straight and curved reaching may provide a later-plannable demand contrast for separating reliability from transfer.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** DANDI 000140 is a single-subject macaque delayed center-out reaching dataset with sorted spiking activity from M1 and PMd plus cursor position, hand position, eye position, and hand velocity. The task uses obstructing barriers that produce straight and curved reaches, and the scaled release contains 100 train and 100 test trials.
  - Limitation: The document describes the release but does not provide trial-wise class labels or certify the number of usable repetitions per trajectory class.
  - Limitation: The release has one subject and a small fixed trial count, so any regional or demand-specific inference requires uncertainty-aware resampling and restricted claims.
  - Limitation: This documentation inspection is planning-only and provides no outcome estimate.
- **Unverified planning evidence:** For MC_Maze releases, the first digit of a unit identifier is the authoritative region indicator: leading 1 denotes PMd and leading 2 denotes M1. The note records that stored M1 electrode indices require a plus-96 correction and reports both regions in the pinned train split after that reconciliation: 72 PMd and 70 M1 units.
  - Limitation: The release note is a conversion caveat and must be implemented and independently validated by the later executor before regional comparison.
  - Limitation: The stated counts do not establish trial-level coverage, unit quality equivalence, or a scientific effect.
  - Limitation: This documentation inspection is planning-only and does not use neural response values.
- **Unverified planning evidence:** The train NWB container exposes behavioral series named hand_pos, cursor_pos, eye_pos, and hand_vel; embedded descriptions identify two-dimensional hand position, cursor position, and hand velocity. It also contains PMd and M1 electrode-array and electrode-group labels.
  - Limitation: String-level schema inspection cannot establish the trial segmentation fields, temporal alignment details, missingness, or usable repetitions.
  - Limitation: No raw behavioral or neural observations were retained or analyzed.
  - Limitation: A later NWB adapter must inspect formal table structure and validate time bases before execution.

### Plan at a glance

- Population and scope: One rhesus macaque in the pinned MC_Maze-S train release; repeated barrier-maze reaches classified as straight or curved from verified task labels or a preregistered trajectory-curvature rule, with M1 and PMd analyzed separately and jointly only as sensitivity strata.
- Unit of observation: A trial-level, event-aligned population response vector assigned to a verified straight or curved reach class.
- Unit of inference: Independent trial partitions within demand class in the recorded subject.
- Hierarchy and dependence: Trials are nested in demand class, trajectory condition, and repeated resampling partitions; neural summaries are region-stratified. Cross-demand comparisons use matched condition sets or propensity-style kinematic matching so shared movement features do not masquerade as transfer.
- Validation: Validate trajectory time bases and class assignment; use synthetic populations with common versus class-specific relational geometry to test recovery; confirm that any alignment procedure is fixed before cross-demand scoring and that class labels cannot be reconstructed from leakage across splits.
- Split strategy: Disjoint, repeated stratified trial partitions within each demand class; construct each class geometry from separate trial halves and score cross-demand correspondence only across independent estimates.
- Claim ceiling: predictive

**Analysis strategy**

1. Prespecify straight and curved classes from task labels if present; otherwise classify trajectories using a curvature criterion fixed from behavior metadata before neural analysis.
2. Estimate within-class relational reliability from independent trial halves for each demand class.
3. Only when both classes meet a prespecified reliability floor, estimate cross-class correspondence between independently estimated relational dissimilarity matrices without outcome-driven alignment.
4. 1 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: Pair a straight-class estimate with a permuted curved-class condition mapping.; Use a behaviorally mismatched curved subset to demonstrate sensitivity to demand correspondence rather than generic population similarity.
- Positive controls: Synthetic common-scaffold and demand-specific-remapping populations with matched within-class reliability.; Split estimates from the same demand class to establish the expected reliability ceiling for correspondence.
- Alternative explanations: Apparent transfer caused by overlapping kinematics, target direction, or timing rather than a common scaffold.; Low cross-demand correspondence caused by lower within-class reliability or imbalanced class coverage.; plus 1 additional item(s) in the complete dossier

**Interpretation limits**

- The observational single-subject dataset can test predictive correspondence, not a causal mechanism for generalization.
- Any conclusion is limited to the verified trajectory definition and observed barrier-maze demand range.

**Why the plan serves the question**

It treats cross-demand transfer as the decisive contrast, gates that interpretation on independent within-class reliability, and directly tests the alternative of stable but demand-specific geometry without reducing the question to the sibling's centroid comparison.

**Before any later execution**

- Unresolved planning decisions: Whether explicit straight-versus-curved labels exist in the formal NWB trial table.; The behavior-only curvature threshold and matching variables require Owner approval before execution.; plus 1 additional item(s) in the complete dossier
- Required future skills: Validated NWB adapter that extracts trial timing, aligns spike times and behavior, and applies the documented corrected M1/PMd unit assignment.; Behavior-only trajectory curvature classifier with audit trail and no neural-outcome tuning.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

Strong within-condition reproducibility combined with either preserved or reorganized cross-condition relationships would distinguish transferable geometry from stable demand-specific geometry.

**What possible outcomes would mean**

- Positive pattern: Transfer would support a predictive account of a common geometric scaffold across reach demands.
- Negative pattern: Reliable within-condition but weak cross-condition correspondence would support stable demand-specific remapping.
- Null or ambiguous pattern: Low within-condition reproducibility would make cross-demand transfer uninterpretable rather than disproving invariance.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve the protected distinction between within-condition relational-versus-centroid stability and cross-demand transfer. The plans use appropriate independent splits, reliability gating, controls for region and kinematic confounding, and single-subject descriptive/predictive claim limits. Remaining choices are execution locks, not scientific blockers.

Retained changes and locks:

- **Pre execution lock:** Before execution, validate NWB trial segmentation, timing alignment, usable repetition coverage, and corrected M1/PMd assignment.
- **Pre execution lock:** Before execution, fix the behavior-only straight-versus-curved classification rule, kinematic matching variables, and reliability and class-coverage floors without neural-outcome tuning.
- **Pre execution lock:** Before execution, lock comparable reliability scaling or calibration for the relational and centroid stability measures in variant 01.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

Both variants preserve the protected family boundary: variant-01 keeps within-condition relational-versus-centroid stability as a measurement-level regional contrast at a descriptive ceiling, while variant-02 treats cross-demand transfer as the decisive generalization claim gated on within-class reliability at a predictive ceiling. The forbidden semantic merges are respected: neither variant collapses the two meanings, and variant-02 explicitly gates transfer on reliable within-condition geometry without inferring it. Plans are grounded in the bounded evidence (DANDI 000140 single-subject MC_Maze-S train release, documented region-index reconciliation, structural NWB surfaces), and each…

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
