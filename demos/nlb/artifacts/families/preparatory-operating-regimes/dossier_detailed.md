# Preparatory population dynamics as operating regimes for movement — scientific reading guide

> **Planning-only boundary:** This page explains a question-development outcome. It reports no scientific result, authorizes no execution, and does not open the downstream bridge.

## Status and authority

- Family status: **Validation warning**
- Authority: **Provisional / degraded**
- Accepted-plan authority: **No**
- Scientific results: **None; the analysis has not been executed.**

## Why this question matters

Tests whether preparatory dynamics set movement-specific operating conditions, separating trajectory-class boundary tests from trial-level behavioral-consequence tests.

The scientific tension is:

Preparatory trajectories may establish movement-generating operating conditions, but descriptive dynamics could instead reflect elapsed time, impending movement, or behaviorally irrelevant population variation.

## How to read this terminal

Returned planning material did not pass strict typed validation. The family is complete as a readable soft terminal, but it remains provisional and degraded with no accepted-plan authority.

**Recorded public status note**

Returned planning material could not be fully validated; a readable family dossier was retained with a validation warning.

## Variant 1: trajectory-class boundary test

### Why it matters

Locating the divergence at preparation versus execution constrains dynamical accounts without asserting a particular circuit mechanism.

### Original and refined question

**Original Question Scientist proposal**

Do straight and curved reaches recruit distinct preparatory population operating regimes, or do they diverge only after movement begins?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Delayed straight and curved reaches may allow a later planner to compare when trajectory-class organization becomes distinguishable.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The pinned MC_Maze_Small release is a delayed center-out reaching task with obstructing barriers that produces straight and curved reaches. It contains sorted unit spike times from M1 and PMd and records cursor position, hand position, eye position, and offline-calculated hand velocity. The release is limited to 100 train and 100 test trials.
  - Limitation: This documentation establishes available modalities and task framing, not the exact train-file field names, event columns, or usable trial count after prespecified exclusions.
  - Limitation: The test split was not inspected because this is a planning-only handoff.
  - Limitation: The small single-subject release limits precision, condition balance, and generalization.
- **Unverified planning evidence:** The local release contains separate train and test NWB assets. The release notes state that both M1 and PMd are represented in the local train population, while warning that raw unit electrode indices alone mislabel M1 because the documented correction uses unit-ID region coding and a plus-96 electrode-table offset.
  - Limitation: The notes are release-specific metadata and do not establish per-trial behavioral coverage or exact event timing fields.
  - Limitation: Any regional analysis must implement and document the stated correction before assigning units to M1 or PMd.
  - Limitation: Only the train asset may be used for exploratory planning or later model development unless a separately authorized evaluation protocol specifies otherwise.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

Reliable trajectory-class separation in preparatory population organization that anticipates later path differences would favor advance configuration; separation emerging only during movement would favor execution-driven divergence.

**What possible outcomes would mean**

- Positive pattern: Preparatory divergence would support a predictive account in which upcoming reach geometry is configured before movement.
- Negative pattern: Reliable divergence confined to execution would weaken claims that preparation contains trajectory-specific operating regimes.
- Null or ambiguous pattern: Weak or temporally unstable separation would leave the onset of trajectory-specific organization unresolved.

## Variant 2: independent behavioral-consequence test

### Why it matters

This variant demands an independent behavioral consequence and contrasts structural state with magnitude.

### Original and refined question

**Original Question Scientist proposal**

Does trial-to-trial proximity to a reach-specific preparatory population state predict subsequent movement trajectory more strongly than preparatory activity magnitude?

**Refined-question status**

A refined question did not earn accepted-plan authority in this family terminal. Any retained planner wording remains planning context only.

### Proposal hypothesis versus inspected evidence

**Proposal-stage dataset-leverage hypothesis**

Neural activity paired broadly with hand or cursor trajectories may allow later planning of trial-level predictive comparisons.

This was a proposal-stage hypothesis, not a feasibility certification or scientific finding.

**What the planner actually inspected**

- **Unverified planning evidence:** The pinned MC_Maze_Small release is a delayed center-out reaching task with obstructing barriers that produces straight and curved reaches. It contains sorted unit spike times from M1 and PMd and records cursor position, hand position, eye position, and offline-calculated hand velocity. The release is limited to 100 train and 100 test trials.
  - Limitation: This documentation establishes available modalities and task framing, not the exact train-file field names, event columns, or usable trial count after prespecified exclusions.
  - Limitation: The test split was not inspected because this is a planning-only handoff.
  - Limitation: The small single-subject release limits precision, condition balance, and generalization.
- **Unverified planning evidence:** The local release contains separate train and test NWB assets. The release notes state that both M1 and PMd are represented in the local train population, while warning that raw unit electrode indices alone mislabel M1 because the documented correction uses unit-ID region coding and a plus-96 electrode-table offset.
  - Limitation: The notes are release-specific metadata and do not establish per-trial behavioral coverage or exact event timing fields.
  - Limitation: Any regional analysis must implement and document the stated correction before assigning units to M1 or PMd.
  - Limitation: Only the train asset may be used for exploratory planning or later model development unless a separately authorized evaluation protocol specifies otherwise.
- These retained inspection notes do not create accepted-plan authority.

### Scientific stakes

**Discriminating observation**

Out-of-sample trial-level prediction from independently defined geometric state that exceeds matched magnitude and behavioral controls would favor a structurally consequential preparatory state.

**What possible outcomes would mean**

- Positive pattern: A specific predictive relationship would support the claim that preparatory geometry carries behaviorally relevant organization.
- Negative pattern: Prediction explained by magnitude or measured behavior would favor generic readiness or embodied-state accounts.
- Null or ambiguous pattern: No reliable prediction would leave open whether preparatory geometry is consequential or merely poorly estimated.

## Owner and independent review

Any typed review records below are retained context only. They cannot override this system terminal or create accepted-plan authority.

### Question Owner

- Disposition: **Accept**
- Review complete: **Yes**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The revision resolves the prior scientific blocker: variant 2 constructs each held-out geometry predictor solely from held-out preparatory neural data and training-fold-defined references, with the held-out behavioral outcome unavailable until scoring. Both variants retain their distinct protected contrasts and have evidence-supported, appropriately bounded planning dossiers. Remaining schema-dependent choices are pre-execution locks, not planning deficiencies.

Retained changes and locks:

- **Pre execution lock:** Before later execution, fix behavior-only trajectory outcome and straight/curved classification rules, the train-asset event and movement-onset mapping, exclusion rules, and minimum usable balanced trial counts following authorized schema and coverage checks.

### Independent reviewer

- Disposition: **Accept**
- Review complete: **No**
- Scientific-intent/material-revision note: No material revision was detected in this review.

The revision resolves the round-0 scientific blocker (review-change-534b0d2b57d401fe) for variant 2. The held-out geometry predictor is now constructed strictly from held-out preparatory neural data transformed by training-fold-fitted operations, using the complete ordered distance vector to all training-fold-defined reference states; no held-out trajectory class, feature, or outcome selects, weights, or drops a reference, and the outcome is revealed only for scoring. This eliminates the outcome-dependent-selection leakage path and preserves an honest out-of-sample geometry-versus-magnitude comparison. Both variants retain distinct protected contrasts (variant 1: condition-level timing of…

**Authority reminder:** these dispositions do not yield an accepted plan here.

## Continue to the complete dossier

This guide is an orientation layer. The existing dossier remains the complete human-readable planning record.

[Read the complete scientific dossier](dossier.md)
