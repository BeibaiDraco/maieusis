# Replicable and idiosyncratic components of decision geometry — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Mixed family: accepted and non-accepted sibling variants**
- Authority: **Automated independent review, planning only**
- Accepted-plan authority: **Yes, for planning only**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Uses standardized multi-context recordings to ask whether population geometry contains a shared organizational component alongside subject- or laboratory-specific variation.

The scientific tension is:

A common task may induce reproducible population organization, but apparent replication can arise from shared observables, while genuine computational solutions may remain individual-specific.

## How to read this mixed family

Accepted and non-accepted sibling variants coexist here. Authority applies only to the variants explicitly marked as reviewed and accepted; it does not spill across the family.

## Variant 1: Laboratory-level reproducibility of specified geometry and predictive meaning

### Why it matters

The revision tests a specific structural and predictive claim about decision geometry across acquisition contexts. It distinguishes recurrence of prespecified geometric relationships from generic cross-laboratory decodability and separates biological generalization from behavioral, sampling, and measurement explanations.

### Original and refined question

**Original Question Scientist proposal**

Which aspects of decision-related population geometry are reproducible across laboratories rather than specific to laboratory context?

**Post-novelty revised proposal**

Across laboratories with comparable anatomical targeting, included cell populations, recording quality, and estimate reliability, and after matching training state and distributions of task performance, choice, reaction time, and trial history, do the relative orientations of sensory-evidence and choice axes and the corresponding condition-level representational distances recur during the decision epoch and incrementally predict reaction time in a held-out laboratory beyond behavioral and measurement covariates, rather than merely permitting cross-laboratory alignment or decoding?

**Refined-question status**

No refined question earned accepted-plan authority for this sibling.

**Reviewed planning disposition**

Rejected because a faithful operationalization was not established. The metadata expose behavioral and measurement covariates but no documented training-state field. Because the protected contrast requires matching training state across laboratories, substituting session_number would silently weaken the intended control; the laboratory-level variant cannot be faithfully operationalized from the inspected dataset surface.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

If the multi-laboratory recordings contain sufficiently comparable decision epochs, behavioral and training-state variables, anatomical coverage, cell-population inclusion information, and recording-quality indicators, they may support a held-out-laboratory test of whether prespecified axis relationships and representational distances recur and add prediction of reaction time beyond behavioral and measurement covariates.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The metadata contain 459 sessions from 12 laboratories and 139 subjects, 699 insertions, and 75,395 units. Session, insertion, unit, trial, and event tables expose laboratory and subject fields; trials expose choice, left and right contrast, block probability, stimulus, go-cue, first-movement, response, feedback, interval, and inclusion fields; units expose anatomical acronyms, quality labels, firing rate, and spike count. Session order is available as session_number, but no documented training-state field is present in the inspected schemas.
  - Limitation: Aggregate coverage does not demonstrate balanced laboratory-by-region or subject-by-condition support after future prespecified exclusions.
  - Limitation: Session number is not evidence of training state.
  - Limitation: This query did not inspect behavioral or neural outcomes.

### Scientific stakes

**Discriminating observation**

Evidence for laboratory-general organization would require both recurrence in held-out laboratories of the prespecified relative orientation of sensory-evidence and choice axes and their condition-level representational distances during the decision epoch, and incremental prediction of matched reaction time from those features beyond behavioral and measurement covariates. Alignment or decoding success without geometric correspondence would not suffice. Differences should be attributed to context-sensitive organization only if behavioral-state variables, anatomical targeting, cell-population inclusion, recording quality, and estimate reliability do not account for laboratory labels or the observed discrepancy.

**What possible outcomes would mean**

- Positive pattern: If both geometric correspondence and incremental held-out-laboratory reaction-time prediction recur after the stated comparisons, the result would support a bounded claim that these selected features of decision geometry generalize across laboratory contexts and have predictive meaning beyond standardized behavior and measurement covariates.
- Negative pattern: If reliable estimates show that the prespecified geometric relationships do not recur and do not incrementally predict reaction time after behavioral, anatomical, sampling, and measurement explanations are addressed, the result would favor context-sensitive organization over a laboratory-general geometry for these features. If only correspondence or prediction fails, the claim would narrow respectively to shared predictive information without structural invariance or structural recurrence without demonstrated incremental behavioral meaning.
- Null or ambiguous pattern: If geometric correspondence or incremental prediction remains uncertain because behavioral and training-state distributions cannot be matched, targeting or included populations are incomparable, recording quality differs, estimates are unreliable, or the two criteria yield unstable evidence, the result would be indeterminate and would not distinguish context-sensitive biology from sampling or measurement limitations.

## Variant 2: Subject-specific geometry with label-independent shared joint function

### Why it matters

Distinguishing intrinsic shared computational meaning from label-induced alignment and decision-parameter heterogeneity would clarify whether universality of decision function requires universality of neural geometric form.

### Original and refined question

**Original Question Scientist proposal**

Can subject-specific population geometries implement a shared predictive relationship between sensory evidence, decisions, and response times?

**Post-novelty revised proposal**

Do structurally subject-specific population geometries preserve a joint, out-of-sample mapping from sensory evidence to choices and response times when alignment and model selection use no target-subject behavioral labels, and after separating geometric variation from variation in evidence-growth rate, decision threshold, and nondecision or movement time?

**Reviewed refined question**

Among reliability-qualified subjects with comparable prespecified anatomical sampling, do structurally subject-specific decision-epoch population geometries support a donor-derived, behavioral-label-independent and out-of-sample joint mapping from sensory evidence to choice and response time after accounting for decision-process parameters?

**Reviewed planning disposition**

Accepted for planning; later execution requires a new skill.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Repeated perceptual-decision observations across subjects may permit comparison of subject-specific population geometries, held-out evaluation of their joint relationship to sensory evidence, choice, and response time, and assessment of whether between-subject differences remain after accounting for decision-process parameters. Adequacy for these comparisons remains to be verified downstream.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The build summary reports 699 spike insertions and the schema documents per-insertion delta-time spike arrays with cluster assignments. Together with trial event timestamps, this provides a documented route to construct prespecified decision-epoch population responses during later execution.
  - Limitation: No neural response matrix, representational distance, axis, decoder, or scientific outcome was computed.
  - Limitation: A later executor must implement bounded shard decoding and event alignment with the documented encoding.
- **Unverified planning evidence:** The metadata contain 459 sessions from 12 laboratories and 139 subjects, 699 insertions, and 75,395 units. Session, insertion, unit, trial, and event tables expose laboratory and subject fields; trials expose choice, left and right contrast, block probability, stimulus, go-cue, first-movement, response, feedback, interval, and inclusion fields; units expose anatomical acronyms, quality labels, firing rate, and spike count. Session order is available as session_number, but no documented training-state field is present in the inspected schemas.
  - Limitation: Aggregate coverage does not demonstrate balanced laboratory-by-region or subject-by-condition support after future prespecified exclusions.
  - Limitation: Session number is not evidence of training state.
  - Limitation: This query did not inspect behavioral or neural outcomes.
- **Unverified planning evidence:** The schema declares sessions, insertions, units, trials, events, event-response features, and per-insertion spike shards; the documented primary keys support sessions-to-trials by eid, insertions-to-units by pid, and event-response features by pid and cluster_id.
  - Limitation: The schema documents storage and keys but does not establish that any selected laboratory or subject stratum will satisfy prespecified reliability thresholds.
  - Limitation: This was a planning-only structural inspection.

### Plan at a glance

- Population and scope: Subjects and sessions in the documented BWM ephys tables with retained trials, linked insertions and units, and sufficient prespecified within-subject reliability; inference is across subjects, not trials or units.
- Unit of observation: A retained trial's prespecified decision-epoch population-response representation within a subject and anatomical sampling stratum.
- Unit of inference: A held-out subject, with session and insertion dependence retained within subject-level resampling.
- Hierarchy and dependence: Model trials within sessions and subjects and units within insertions; aggregate geometric summaries to independent subject-level folds, use block resampling by subject, and never treat units or trials as independent replication units.
- Validation: Run synthetic recovery tests in which known shared and subject-specific mappings are embedded in spike-like responses; verify spike-shard decoding against metadata counts; audit that target behavioral labels are inaccessible to alignment and model-selection code; and verify within-subject split reliability before interpreting transfer failure.
- Split strategy: Outer leave-one-subject-out evaluation; donor subjects supply alignment and mapping training. Within every donor and target subject, reserve disjoint trial partitions for geometry reliability, any permitted unsupervised preprocessing, and final scoring. All trial-history features are computed within partition boundaries.
- Claim ceiling: predictive

**Analysis strategy**

1. Before evaluation, define the decision epoch relative to documented go-cue and first-movement timestamps, the contrast conditions, the anatomical inclusion stratum, unit-quality exclusions, feature normalization, and a within-subject split for reliability estimation.
2. Within each training subject, construct condition-level response vectors and prespecified sensory-evidence and choice representations from event-aligned spike counts; quantify geometry only after the reliability screen.
3. Fit an alignment using donor neural geometry and permissible nonbehavioral sampling metadata only; prohibit target-subject contrast, choice, response-time, trial-history, or other behavioral labels from fitting, selecting, or tuning the alignment.
4. 2 additional step(s) remain in the complete dossier.

**Controls**

- Negative controls: A donor geometry with trial-condition assignments permuted within donor subject after all nonbehavioral preprocessing, scored only on held-out target trials.; A time-shifted pre-task population window that is not the prespecified decision epoch.
- Positive controls: Within-subject held-out recovery of the prespecified sensory-evidence representation after the same reliability and split procedures.; Synthetic shared-mapping data in which the executor recovers transfer only when the implanted mapping is available.
- Alternative explanations: Differences in evidence-growth rate, threshold, nondecision time, or movement time rather than a difference in geometry-to-computation mapping.; Anatomical sampling, unit quality, unit count, session composition, or estimate reliability rather than subject-specific computation.; plus 2 additional item(s) in the complete dossier

**Interpretation limits**

- This observational dataset cannot establish that geometry causes choices or response times.
- The conclusion is limited to the included BWM subjects, chosen anatomical stratum, task conditions, feature family, and prespecified decision epoch.
- Label-independent alignment does not make differently sampled neuronal populations biologically identical.
- 1 additional item(s) remain in the complete dossier.

**Why the plan serves the question**

The plan retains the protected subject-level contrast between structural idiosyncrasy and common functional predictive meaning, forbids target behavioral labels from constructing alignment, evaluates choice and response time jointly, separates specified decision-process alternatives, and treats unreliable within-subject geometry as inconclusive.

**Before any later execution**

- Unresolved planning decisions: Choose and freeze the decision-epoch boundaries before target-subject scoring.; Choose and freeze the anatomical stratum and minimum coverage rule from metadata before inspecting geometric outcomes.; plus 1 additional item(s) in the complete dossier
- Required future skills: Decode documented delta-time spike shards and align them to trial events without materializing a full dataset-wide spike matrix.; Fit and audit a behavioral-label-independent cross-subject population-geometry alignment with subject-blocked evaluation.; plus 1 additional item(s) in the complete dossier

### Scientific stakes

**Discriminating observation**

Functional equivalence would be favored if an alignment fixed without target-subject choice, response-time, sensory-evidence, or other behavioral labels supports out-of-sample preservation of the joint evidence–choice–response-time mapping in held-out target subjects, with the result remaining after separating decision-process parameter variation. Genuinely different individual mappings would be favored if each subject shows a reliable within-subject joint mapping but a donor-derived mapping fails while a subject-specific mapping succeeds, with residual differences not attributable to evidence-growth rate, threshold, or nondecision or movement time. If the within-subject mappings or geometries are themselves unreliable, cross-subject failure would remain inconclusive rather than evidence of strategic difference.

**What possible outcomes would mean**

- Positive pattern: Reliable label-independent transfer of the joint mapping, beyond decision-parameter differences, would support the claim that shared decision computation can persist across structurally idiosyncratic population geometries.
- Negative pattern: Reliable within-subject mappings coupled with systematic cross-subject failure not explained by decision-process parameters would support individual-specific computational or strategic meanings of population geometry.
- Null or ambiguous pattern: If within-subject geometry or the joint behavioral mapping is insufficiently reliable, or if parameter and geometric contributions cannot be separated, the evidence would not distinguish functional equivalence from individual-specific computation.

## Owner and independent review

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family has an evidence-backed, scientifically coherent plan for the subject-level functional-equivalence variant and an honest evidence-supported rejection of the laboratory-level sibling because documented training-state matching is unavailable. The accepted variant preserves label-independent target alignment, subject-held-out evaluation, joint choice–response-time prediction, reliability-qualified interpretation, and separation of decision-process and measurement alternatives. Remaining choices are appropriate pre-execution locks rather than planning defects.

Retained changes and locks:

- **Pre execution lock:** Freeze the neural feature family, decision-epoch definition, dimensionality rule, and reliability criterion before target-subject scoring.
- **Pre execution lock:** Freeze the anatomical inclusion stratum and minimum coverage rule from metadata before geometric-outcome inspection.
- **Pre execution lock:** Freeze the joint prediction score and decision-process model family using synthetic recovery and donor-side procedures rather than target-outcome optimization.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The family plan is scientifically sound. Variant 02 (subject-level functional equivalence) is evidence-backed: alignment is fixed without target-subject behavioral labels, evaluation is subject-held-out, choice and response time are predicted jointly, decision-process and measurement alternatives are explicitly modeled as competing explanations, and synthetic recovery plus positive/negative controls guard against leakage and misinterpretation of unreliable geometry. Interpretation limits correctly bound the claim to predictive, observational, dataset-scoped conclusions. Variant 01 (laboratory-level recurrence) is honestly rejected for operationalization failure because no documented training-state field exists in the inspected metadata and session_number is explicitly and correctly refused as a silent substitute for the protected training-state-matching control; this rejection is evidence-grounded rather than a low-effort dismissal. The two siblings remain properly separated along the family's protected axis (laboratory recurrence vs. subject-level functional equivalence) with no forbidden semantic merge. The three Owner-classified required changes (freezing feature/epoch/dimensionality/reliability definitions, freezing the anatomical stratum and coverage rule, and freezing the joint scoring rule and decision-process model family via synthetic recovery rather than target-outcome optimization) are all bounded pre-execution choices needed only before a later execution bridge, not scientific blockers, and I concur with their classification.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
