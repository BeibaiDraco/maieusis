# What the Owner decided, what the independent reviewer decided

Every plan here was reviewed twice: once by the Question Owner that developed it with the dataset planner, and once by a reviewer on a different vendor that never saw that conversation. This page is both decisions for every family that reached that stage, so "independently reviewed" is something you can check rather than something you are told.

In this run the two agreed on 5 of 5 families.

Agreement is not the same as a rubber stamp and it is not proof of one either. Read the reviewer's own reasoning below and decide which it looks like; that is why it is printed rather than summarised.

## Context-dependent balance of autonomous and input-linked motor dynamics

- **Question Owner** — Accepted (`openai` / `gpt-5.6-terra`)
- **Independent reviewer** — Accepted (`anthropic` / `claude-sonnet-5`)

**The reviewer's reasoning.** Both variants are well-grounded in the cited evidence (schema, sample inspection, and variant-specific window/behavior evidence), preserve the family's forbidden-merge boundaries (separate temporal loci for preparation vs execution; shared/selective preparatory structure not conflated with autonomous/input-linked execution; execution kept strictly associational), and hold claims at an appropriate predictive/associational ceiling rather than a causal one. Each plan names concrete competing explanations (task-structure/adaptation confounds and movement-demand covariates for preparation; autonomous-generator and duration/complexity confounds for execution) and specifies matched positive/negative controls and leakage-safe, dependence-aware validation. The two Owner-flagged issues (preparation-window/unit-selection rules; execution-binning/template/matching rules) are legitimate but concern implementation choices needed only before execution, not the current scientific validity of the plan, so they are correctly pre-execution locks rather than blockers. No scientific blocker or hard-boundary concern is present.

**Per criterion:**

- *Intent preservation* — **pass**. The preparation plan targets prospective, graded curvature prediction beyond binary condition separability, matching the protected variant intent; the execution plan remains strictly associational and preserves the autonomy-input tension. Forbidden semantic merges (temporal loci, shared-vs-selective preparation vs autonomous-vs-input execution, associational-only execution claims) are all respected.
- *Scientific value* — **pass**. Both estimands are non-trivial and address the stated theoretical tensions with named competing explanations rather than a foregone conclusion; the predicted result patterns for support versus weakening are clearly differentiated.
- *Dataset grounding* — **pass**. Required variables, event times, unit counts, region correction, and behavioral sampling rates are documented via schema and sample-inspection evidence directly tied to each data source; small-sample limitations (trials per maze_id, straight/curved imbalance) are explicitly acknowledged rather than concealed.
- *Overclaim* — **pass**. Claim ceilings are explicitly predictive (preparation) and associational (execution); interpretation_limits sections explicitly disclaim causal or trajectory-control conclusions and note that a binary condition effect alone is insufficient evidence.
- *Alternative explanations* — **pass**. Each variant names concrete, dataset-relevant competitors (learned task structure/adaptation and movement-demand confounds for preparation; autonomous trajectory generator and duration/kinematic-complexity confounds for execution) and builds them into the covariate/control strategy rather than merely listing them.
- *Controls* — **pass**. Both plans specify positive controls (direction/target decodability; velocity/direction association), negative controls (label shuffling, time-reversal/phase-randomization), and dependence-aware, leakage-safe cross-validation with permutation nulls.
- *Material revision risk* — **not_applicable**. This is the initial review round with no prior accepted draft to compare against; there is no revision history to assess for material drift.
- *Sibling separation* — **pass**. The preparation and execution plans use distinct windows, distinct data sources, distinct estimands, and distinct claim ceilings, with explicit cross-references confirming they are kept scientifically separate as required by the family boundary.
- *Prior issue resolution* — **not_applicable**. Review round is 0 with an empty issue ledger and no prior review history, so there are no previously raised issues to verify as resolved.

**What it asked to be changed:**

- Prespecify a multiple-comparison or family-wise error control plan across the two named preparation estimands (cross-condition correspondence score and incremental curvature-prediction information) and, symmetrically, across any duration-matched sensitivity variants of the execution association estimand, so that reported significance is not inflated by post hoc selection among related tests.

## Stable versus task-specific geometry across motor contexts

- **Question Owner** — Accepted (`openai` / `gpt-5.6-terra`)
- **Independent reviewer** — Accepted (`anthropic` / `claude-sonnet-5`)

**The reviewer's reasoning.** Both sibling variants preserve the family's protected scientific intent: the context-invariance plan tests within-region preservation/transformation/reorganization of straight-versus-curved geometry at matched epochs, phases, kinematic states, and submovement roles, while the regional-scope plan tests a reliability-normalized cross-trajectory transfer difference between PMd and M1 under held-constant task conditions. These remain distinct claims per the family's forbidden semantic merges, with no cross-contamination of estimands or data slices. Both plans are concretely grounded in verified dataset evidence (unit counts, trial partition by num_barriers, 1000 Hz kinematics, shared event timing), specify appropriate claim ceilings (descriptive, associational) with honest single-subject/session limits, and include alternative-explanation lists, positive/negative controls, and synthetic method-recovery probes that address the plausible confounds (state occupancy, submovement mix, detectability, temporal structure, unit-count imbalance). The two Owner-classified required changes (prespecifying matching tolerances/transformation family, and prespecifying the transfer metric/reliability normalizer/unit-matching scheme) are bounded implementation choices that do not touch the scientific logic or validity of the estimands; they are correctly classified as pre-execution locks rather than blockers. No scientific blocker or hard-boundary issue is present in either variant at this planning stage.

**Per criterion:**

- *intent preservation* — **pass**. Each variant maps cleanly onto its protected question_seed and target_contrast; the within-region plan excludes any cross-region comparison and the regional-scope plan defines scope via normalized transfer rather than task-dependence prevalence, avoiding the family's forbidden semantic merges.
- *scientific value* — **pass**. Both plans instantiate the shared theoretical tension (stable scaffold vs. lawful transformation vs. reorganization; common vs. specialized regional scope) with falsifiable, cross-validated estimands and clearly differentiated predicted result patterns.
- *dataset grounding* — **pass**. Required variables (unit IDs with region convention, trial event columns, num_barriers partition, 1000 Hz hand kinematics) are verified present with concrete counts (72 PMd/70 M1 units, 32 straight/68 curved trials) rather than assumed.
- *overclaim control* — **pass**. Claim ceilings are appropriately descriptive and associational, and interpretation_limits explicitly flag single-subject/session scope, small matched-cell counts, and wide uncertainty, preventing overgeneralization beyond this animal and session.
- *alternatives and confounds* — **pass**. Alternative_explanations sections identify plausible confounds (preparation/execution occupancy imbalance, submovement-role differences, detectability/signal-strength, shared temporal structure, generic task-dependence) and the analysis_strategy addresses each through matching, normalization, or modeling.
- *controls* — **pass**. Both plans specify positive controls (recoverable target-direction structure), negative controls (label shuffles or irrelevant re-labelings collapsing to reliability floor), and synthetic method-recovery probes with imposed known transformations/transfer values.
- *material revision risk* — **not_applicable**. This is round zero with no prior accepted plan version to compare against, so material-revision risk is not yet assessable.
- *sibling separation* — **pass**. The two variants use distinct estimands, distinct data-source framings, and distinct required_new_skills, consistent with the family's requirement that within-region transformation and cross-region specialization remain separate scientific claims.
- *prior issue resolution* — **not_applicable**. The issue_ledger is empty and this is the first review round, so there are no prior issues to verify as resolved.

## Functional structure of preparatory population variability

- **Question Owner** — Accepted (`openai` / `gpt-5.6-terra`)
- **Independent reviewer** — Accepted (`anthropic` / `claude-sonnet-5`)

**The reviewer's reasoning.** Both sibling plans are evidence-backed against the documented MC_Maze_Small single-session dataset and preserve distinct facets of the shared theoretical tension: the alignment variant tests trajectory-selective versus isotropic contraction using independently estimated trajectory directions and matched nonaligned controls with a circularity-breaking split and synthetic method-recovery; the readiness variant tests bounded incremental behavioral prediction from transition-excluded preparatory instability against a documented, dataset-limited set of competing predictors, with pupil/EMG absence explicitly carried as an unmeasured confound rather than glossed over. Claim ceilings (descriptive; predictive/noncausal) are appropriately modest given a single subject, single session, and few within-condition repeats. Negative and positive controls, leakage-safe validation, and condition-aware cross-validation are specified for both. The two remaining Owner issues concern prespecification of estimator, window, and validation choices needed only before an executor is built, not whether the current plan can credibly answer either question; they are correctly pre-execution locks rather than scientific blockers. No hard boundary is implicated, and the sibling questions remain non-overlapping per the family's forbidden-semantic-merge guidance.

**Per criterion:**

- *intent preservation* — **pass**. Each variant's refined_question and why_plan_serves_question map directly onto its distinct facet of the shared preparatory-variability tension (geometric alignment vs. behavioral-prediction) without drifting into the other's territory.
- *scientific value* — **pass**. Both plans target a substantive open question about the functional structure of preparatory variability with clear estimands and predicted result patterns that would discriminate competing accounts.
- *dataset grounding* — **pass**. Data sources, trial counts, region conventions, and timing fields are grounded in the cited evidence views (trial timing, condition structure, unit/region documentation, behavioral channel availability).
- *overclaim* — **pass**. Claim ceilings are explicitly descriptive (alignment) and predictive/associational/noncausal (readiness), with interpretation_limits repeatedly flagging single-subject, single-session, and small-sample constraints.
- *alternatives* — **pass**. Each plan enumerates concrete competing explanations (circularity, isotropic contraction, transition-timing confound, planned-path difficulty, eye/covert-movement proxies) and the readiness plan honestly documents pupil-arousal and EMG as unmeasured, not-ruled-out confounds per the Owner's operationalization ruling.
- *controls* — **pass**. Both plans specify positive and negative controls (decodability of movement direction; shuffled/random control directions; permuted instability nulls; post-outcome predictor nulls) appropriate to their designs.
- *material revision* — **not_applicable**. This is round zero with no prior review history or plan revision to assess.
- *sibling separation* — **pass**. The target_contrast and forbidden_semantic_merges are honored: the alignment variant is purely geometric and does not require behavioral prediction, while the readiness variant does not require or presuppose trajectory-dimension alignment.
- *prior issue resolution* — **not_applicable**. The issue ledger is empty and this is the first review round, so there are no prior issues to verify as resolved.

## Generalizable readout across trajectory contexts and cortical populations

- **Question Owner** — Accepted (`openai` / `gpt-5.6-terra`)
- **Independent reviewer** — Accepted (`anthropic` / `claude-sonnet-5`)

**The reviewer's reasoning.** Both sibling variants operationalize distinct, evidence-grounded generalization tests (behavioral-context transfer vs. cross-region compatibility) that faithfully preserve the family's protected intent and forbidden-merge boundaries. Dataset grounding is solid: task-condition and tortuosity-based straight/curved definitions, unit-region assignment with the documented +96 correction, and simultaneous PMd/M1 recording are all evidence-backed rather than invented. Both plans carry an associational claim ceiling with explicit interpretation limits, name concrete alternative explanations (kinematic-range confound, linear-readout limits, sampling/quality imbalance, alignment inflation), and include positive/negative controls plus diagnostics to adjudicate asymmetry versus artifact. The remaining Owner-required changes concern decoder family, binning, validation scheme, alignment method, latent dimensionality, and held-in-unit policy — all pre-execution implementation locks rather than defects in the scientific design, so they do not block acceptance of the planning product. No new scientific blocker or hard-boundary issue is identified at this round.

**Per criterion:**

- *intent preservation* — **pass**. Both variants preserve the protected distinction between behavioral-context transfer and cross-region compatibility; neither collapses transfer into a single undifferentiated score, consistent with the family's intended_claim statements.
- *scientific value* — **pass**. Each variant tests a genuine, theoretically motivated generalization question (shared vs. context-specific trajectory structure; shared/transformed vs. region-specific readout) with a real chance of an informative asymmetric or null result.
- *dataset grounding* — **pass**. Trial counts, region assignment convention plus +96 electrode correction, tortuosity-based context definition, and dual-region simultaneity are all drawn from verified branch evidence rather than assumed.
- *overclaim* — **pass**. Both plans set an associational claim ceiling and explicitly limit inference to a single subject/session, ruling out causal or across-subject claims.
- *alternatives* — **pass**. Trajectory variant addresses unequal kinematic range and linear-readout limits; region variant addresses unequal sampling/signal quality and alignment inflation from shared task structure, both with concrete diagnostic checks.
- *controls* — **pass**. Both include positive controls (above-chance within-context/within-region decoding) and negative controls (shuffled-label or shuffled-correspondence nulls) to calibrate transfer/alignment estimates.
- *material revision* — **not_applicable**. This is the round-zero initial plan draft review; there is no prior accepted plan version against which to assess material revision.
- *sibling separation* — **pass**. The two variants use distinct estimands, data extraction paths, and alternative-explanation sets, respecting the family's forbidden-semantic-merges list (behavioral-context transfer is not conflated with regional compatibility).
- *prior issue resolution* — **not_applicable**. issue_ledger and prior_review_history are empty at review_round 0; there are no prior issues to verify as resolved.

## Localized versus distributed organization of reach planning and execution

- **Question Owner** — Accepted (`openai` / `gpt-5.6-terra`)
- **Independent reviewer** — Accepted (`anthropic` / `claude-sonnet-5`)

**The reviewer's reasoning.** The plan preserves the protected condition-relative PMd-versus-M1 curvature-structure contrast and does not merge it with preparation-to-execution staging. It is evidence-grounded (region mapping, trial/curvature structure, behavioral signal, neural coverage, and scope limits are all directly tied to inspected dataset facts), isolates curvature-unique structure from duration, target/distractor, and kinematic confounds, reliability-standardizes the regional comparison to prevent measurement-sensitivity artifacts, and requires an affirmative equivalence test rather than treating a null difference as distributed organization. Claim ceiling is honestly capped at within-subject/session association, and INCONCLUSIVE is acknowledged as a legitimate outcome given the 100-trial sample. The two Owner-identified items (numeric SESOI value; primary estimator and heldout-inclusion rule) are pre-execution implementation locks, not scientific blockers, so this remains an accept that carries them forward.

**Per criterion:**

- *intent preservation* — **pass**. Refined question and analysis retain the protected phenomenon (where curvature-specific structure is expressed) and do not conflate it with temporal staging.
- *scientific value* — **pass**. The reliability-standardized, confound-partialled, equivalence-based design can credibly discriminate concentration, distribution, or inconclusiveness.
- *dataset grounding* — **pass**. Region counts, trial structure, behavioral signal, neural coverage, and scope ceiling are all backed by specific bounded evidence views rather than assumed.
- *overclaim check* — **pass**. Claim ceiling is explicitly associational, single-subject/session generalization limits are stated, and a non-significant contrast is explicitly barred from being read as distributed.
- *competing explanations* — **pass**. Duration, target/distractor/barrier condition features, and unequal regional measurement sensitivity are each named and addressed by specific covariate, condition-matching, or reliability-standardization steps.
- *controls* — **pass**. Positive control (direction decodability) and negative controls (label shuffling, irrelevant-feature check) are specified before interpreting the curvature contrast.
- *material revision risk* — **not_applicable**. Round zero initial review; no prior plan version exists to compare against.
- *sibling separation* — **pass**. The plan's condition-relative framing and forbidden-merge list keep it distinct from the family's preparation-to-execution staging variant.
- *prior issue resolution* — **not_applicable**. No prior review history or issue ledger entries exist at round zero.
