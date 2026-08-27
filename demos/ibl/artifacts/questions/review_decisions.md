# What the Owner decided, what the independent reviewer decided

Every plan here was reviewed twice: once by the Question Owner that developed it with the dataset planner, and once by a reviewer on a different vendor that never saw that conversation. This page is both decisions for every family that reached that stage, so "independently reviewed" is something you can check rather than something you are told.

In this run the two agreed on 5 of 5 families.

Agreement is not the same as a rubber stamp and it is not proof of one either. Read the reviewer's own reasoning below and decide which it looks like; that is why it is printed rather than summarised.

## Covariance geometry and alternative population accounts of evidence accumulation

- **Question Owner** — Accepted (`openai` / `gpt-5.6-terra`)
- **Independent reviewer** — Accepted (`anthropic` / `claude-sonnet-5`)

**The reviewer's reasoning.** The v1 plan preserves the protected fixed-axis versus time-local contrast, explicitly separates axis orientation from state displacement along the axis, and specifies fold-safe nested estimation with cross-time and cross-condition held-out evaluation against matched-complexity time-local/condition-local alternatives. Sensory, action, movement, and quality confounds are enumerated as alternative explanations and addressed through joint incremental prediction modeling. Claim ceiling is associational with explicit interpretation limits disclaiming causal integrator or whole-animal claims, consistent with dataset grounding in the ephys/behavior schema evidence. The v2 sibling is honestly rejected for dataset mismatch (no pulse-sequence input surface), and the Owner's ruling that the v1 signed-contrast proxy cannot substitute for pulse control is correctly carried into the v1 interpretation limits, preserving the forbidden-merge boundary between the stable-axis and sequential accounts. Both remaining Owner-classified issues concern binning/smoothing/residualization/quality-screen finalization and movement-covariate admissibility/missing-modality handling; these are bounded, outcome-blind execution details rather than defects that make the plan unable to answer the protected question, so they are correctly pre-execution locks rather than blockers. No new scientific blocker or hard-boundary concern is identified at this round.

**Per criterion:**

- *intent preservation* — **pass**. The plan retains the independently estimated within-region axis, cross-time/condition generalization requirement, and explicit orientation-versus-displacement separation from the protected v1 intent.
- *scientific value* — **pass**. The nested fixed-axis versus time-local comparison with held-out conditional behavioral prediction offers a genuine, non-trivial test of competing temporal-geometry accounts of accumulation.
- *dataset grounding* — **pass**. Required variables and data sources are traceable to the ephys schema and trial/behavior metadata evidence views; the v2 rejection is grounded in a documented absence of pulse-sequence fields.
- *overclaim* — **pass**. Claim ceiling is associational with explicit interpretation limits disclaiming causal, whole-animal, and pulse-control claims; the signed-contrast proxy is labeled only as a sensory-feature alternative.
- *competing explanations* — **pass**. Alternative explanations enumerate averaging artifacts, sensory/elapsed-time confounds, movement/action confounds, and quality/imbalance issues, each addressed in the analysis strategy.
- *controls* — **pass**. Synthetic fixed-versus-rotating-axis recovery simulations serve as positive controls and trial-identity permutation plus misaligned-bin tests serve as negative controls, both under the same split structure.
- *material revision* — **not_applicable**. This is review round zero with no prior accepted plan to compare against for material revision.
- *sibling separation* — **pass**. v2 is honestly and separately rejected for a documented dataset gap rather than merged with or substituted by the v1 proxy, preserving the family's forbidden-merge boundary between stable-axis and sequential accounts.
- *prior issue resolution* — **not_applicable**. The issue ledger is empty at round zero, so there are no prior issues to verify as resolved.

## Embodied and internal-state explanations of apparent noise correlations

- **Question Owner** — Sent back for revision (`openai` / `gpt-5.6-terra`)
- **Independent reviewer** — Sent back for revision (`anthropic` / `claude-sonnet-5`)

**The reviewer's reasoning.** Variant 2's prospective residual-covariance design, alternative-explanation set, controls, and cross-segment stability checks are scientifically coherent, well grounded in the available behavior/ephys schema and shard evidence, and appropriately bounded to an associational claim ceiling. Variant 1 preserves the intended embodied-versus-response-execution contrast and specifies matching controls, but its analysis_strategy includes choice and response-time as nuisance predictors when constructing the very shared-covariance target whose held-out association with choice/response-time is later evaluated. Conditioning the covariance estimand on the outcome and then testing that outcome's association with the (partially outcome-conditioned) component is circular: it can mechanically suppress or manufacture the reported attenuation regardless of any true pose contribution, so the plan as written cannot credibly answer its own protected conditional-association question. This is a genuine scientific blocker rather than a pre-execution detail, matching the Question Owner's independent flag. The remaining two Owner-identified issues (prespecifying camera/keypoint coverage and neural bin window for v1; prespecifying the behavioral latent-state model class, outcome links, neural-history windows, and minimum segment length for v2) are legitimate but are bounded implementation choices that do not undermine the current planning dossier, so they are correctly pre-execution locks rather than blockers. Sibling separation between the embodied (v1) and internal-state (v2) contrasts is intact and the family's forbidden semantic merge is avoided. No hard integrity boundary is implicated; the circularity is repairable by excluding choice/response-time from the covariance-stage baseline and evaluating the outcome association only afterward, as the Owner already specified.

**Per criterion:**

- *intent preservation* — **pass**. Both variants retain the protected conditional-prediction and source-discrimination intents without collapsing the embodied and internal-state contrasts into one another.
- *scientific value* — **pass**. The incremental-prediction and source-discrimination designs would meaningfully advance the family's shared theoretical tension if executed as revised.
- *dataset grounding* — **pass**. Behavior schema, pose shard, ephys schema, and unit-quality evidence views credibly support the required variables, joins, and quality covariates for both variants, subject to the noted unverified coverage caveats.
- *overclaim control* — **pass**. Both variants declare an associational claim ceiling and enumerate interpretation limits distinguishing incremental prediction from causal or unitary-state conclusions.
- *alternative explanations* — **pass**. Each variant enumerates concrete competing accounts (response execution, arousal, overfitting, drift for v1; behavioral history, movement-linked dynamics, recurrent excitability, recording instability for v2) and builds them into the comparison design.
- *controls and diagnostics* — **pass**. Positive and negative controls, leakage checks, and stability diagnostics are specified for both variants and are adequate for a planning-stage dossier.
- *circularity of covariance stage conditioning* — **fail**. Variant 1's covariance-stage baseline includes choice and response-time as nuisance predictors while the downstream estimand is that same component's held-out association with choice or response time, making the intended attenuation test circular and unable to support a valid inference until the outcome variables are removed from the covariance-target construction stage.
- *material revision* — **not_applicable**. This is the first review round for this plan draft; there is no prior accepted plan version against which to assess material revision.
- *sibling separation* — **pass**. Variant 1 (embodied pose explaining covariance) and variant 2 (residual covariance as non-motor predictive state) remain distinct, non-overlapping estimands consistent with the family's forbidden-merge constraint.
- *prior issue resolution* — **not_applicable**. The issue ledger is empty and this is review round zero, so there are no prior issues to verify as resolved.

**What it asked to be changed:**

- For variant 1, do not include choice or response time as covariance-stage nuisance predictors when the downstream estimand is that component’s association with choice or response time; define the covariance target and pose comparison conditional only on the stated non-outcome alternatives, with the outcome association evaluated subsequently.

## Functional alignment of shared variability during perceptual decisions

- **Question Owner** — Accepted (`openai` / `gpt-5.6-terra`)
- **Independent reviewer** — Accepted (`anthropic` / `claude-sonnet-5`)

**The reviewer's reasoning.** The v1 sensory-fidelity plan is a credible, leakage-protected associational design that preserves the protected sensory-versus-task/action geometry contrast: it estimates the sensory axis independently of held-out discriminability, cross-fits nested folds, matches or residualizes comparison axes on reliability/dimensionality/spectrum opportunity, and conditions on both overall correlation magnitude and a to-be-specified established information-limiting covariance measure. Claim ceiling is properly associational, alternative explanations and positive/negative controls are substantive, and hierarchy/dependence is handled at the population level. The v2 choice-state sibling is honestly rejected on branch-scoped evidence: no exposed report-mapping, response-form, or modality dissociation exists to satisfy its invariant, and the plan correctly declines to substitute motor covariates for the required dissociation rather than silently narrowing the claim. This satisfies the family standard of at least one evidence-backed variant with every sibling reaching an honest non-pending outcome, and the two variants remain properly separated per the forbidden-semantic-merge guidance. The three Owner-identified issues (non-outcome inclusion rules, a distinct information-limiting comparator, and axis-matching/failure rules) are all pre-execution locks: they name necessary but boundable execution-stage choices already anticipated in the plan's unresolved_decisions, not defects that prevent the planning product from credibly answering the protected question. No scientific blocker or hard-boundary issue remains at round zero.

**Per criterion:**

- *intent preservation* — **pass**. The plan keeps sensory coding and choice/action geometry as distinct axes and evaluates sensory discriminability specifically, matching the protected family's requirement that these not be conflated.
- *scientific value* — **pass**. The design targets a specific, theoretically motivated contrast (sensory-likelihood alignment vs. matched task/action axes) beyond generic correlation magnitude, which would meaningfully discriminate competing accounts of noise-correlation function.
- *dataset grounding* — **pass**. Evidence views document the linked trial, unit, and spike-shard tables needed for the plan; the acknowledged new-skill requirement (shard decoder, leakage-safe covariance executor) is an appropriate execution-bridge dependency, not a grounding failure at the planning stage.
- *overclaim control* — **pass**. Claim ceiling is explicitly associational, and interpretation_limits correctly disclaim causal inference, generalization beyond included populations, and the operational (not literal) status of the sensory axis.
- *competing explanations* — **pass**. Alternative explanations cover reliability/dimensionality asymmetries between axes, movement/state confounds, and estimation error, addressing the main routes by which axis alignment could spuriously appear informative.
- *controls and validation* — **pass**. Positive controls (synthetic recovery, structural decoding checks) and negative controls (trial shuffles, permuted stimulus labels) are specified alongside nested cross-fitting and a robustness grid, adequately guarding against leakage and artifact.
- *material revision risk* — **not_applicable**. This is review_round 0 with no prior review history or plan revision to assess for drift.
- *sibling separation* — **pass**. The v1 and v2 variants remain cleanly separated per target_contrast and the family's forbidden_semantic_merges; the v2 rejection does not attempt to fold choice-state claims into the sensory-fidelity plan.
- *prior issue resolution* — **not_applicable**. No prior review round or issue ledger entries exist to evaluate resolution of.

## Regional organization of behaviorally relevant covariance geometry

- **Question Owner** — Sent back for revision (`openai` / `gpt-5.6-terra`)
- **Independent reviewer** — Sent back for revision (`anthropic` / `claude-sonnet-5`)

**The reviewer's reasoning.** Both variants credibly instantiate the protected competing claims (recurrent covariance-whitened geometry vs. regionally distinct covariance-axis alignment) with matched task-variable and sampling-matched baselines, appropriate held-out recording-level splits, and honest scope limits. The v2 (VISp-MOs) plan, however, matches trials on response-time strata while also evaluating held-out prediction of response-time variation from the resulting geometry; this uses the outcome to shape the evaluated trial set and invalidates the incremental predictive estimand as currently specified. This is a genuine scientific blocker rather than a pre-execution detail because it undermines the validity of the target held-out comparison itself. The remaining unresolved items are legitimate pre-execution locks that do not require plan-level revision. I concur with the Owner's classification and do not identify additional blockers.

**Per criterion:**

- *intent preservation* — **pass**. Both variants preserve the family's competing organizational claims (shared brain-wide geometry vs. regionally distinct solutions) as separate, non-merged branches consistent with the protected invariant.
- *scientific value* — **pass**. Each variant targets a specific, falsifiable estimand (cross-population geometry transfer; regional alignment difference predicting response time) with clear discriminating baselines rather than a diffuse distributed-activity claim.
- *dataset grounding* — **pass**. Required variables and data sources (spike shards, unit anatomy/quality, trial timing, wheel features) are documented in the schema and coverage evidence views, supporting the planned recording-level analyses.
- *overclaim* — **pass**. Claim ceilings (descriptive for v1, predictive for v2) are matched by explicit interpretation limits disclaiming causal localization, brain-wide mechanism, or within-session interregional covariance.
- *alternative explanations* — **pass**. Both plans enumerate plausible confounds (sampling artifacts, unequal unit counts, shared timing, pooling effects) and address them via matched baselines and permutation/negative controls.
- *controls* — **concern**. Positive/negative controls and synthetic validation are well specified, but the v2 matching-on-outcome issue (see owner change this required change) shows the control design for the predictive comparison currently permits leakage that undermines the held-out test's validity.
- *material revision* — **not_applicable**. This is round zero; no prior plan version exists against which to assess material revision.
- *sibling separation* — **pass**. The two variants remain cleanly separated: v1 tests cross-population recurrence via independently estimated whitened distances, v2 tests a specific VISp-MOs alignment dissociation with predictive comparison; no forbidden semantic merge is present.
- *prior issue resolution* — **not_applicable**. No prior review history exists at round zero.

**What it asked to be changed:**

- Revise the VISp–MOs analysis so that held-out response-time labels are not used for trial selection, matching, tuning, or construction of predictors evaluated for response-time prediction. Trial matching may use predictors available at prediction time; any response-time-based stratification must be confined to a clearly separated descriptive or post-evaluation assessment.

## Reproducibility of noise-correlation statistics and geometry across laboratories

- **Question Owner** — Accepted (`openai` / `gpt-5.6-terra`)
- **Independent reviewer** — Accepted (`anthropic` / `claude-sonnet-5`)

**The reviewer's reasoning.** Both sibling plans preserve the family's protected distinction between coarse noise-correlation magnitude reproducibility (v1) and task-aligned covariance-geometry reproducibility with behavioral association (v2). Each specifies a credible, evidence-grounded route using documented trial/unit/spike schema and coverage evidence, retains dependence-aware nesting (subject-in-lab, session-in-lab), states appropriately bounded claim ceilings (descriptive/predictive) with explicit interpretation limits about the observational subject-lab confound, and includes adequate positive/negative controls and leakage audits. The Owner's two remaining issues are legitimate pre-execution locks (fixing thresholds, tolerances, and a training-only geometry pipeline) rather than scientific blockers, so this is an accept that carries them forward rather than a revision.

**Per criterion:**

- *intent preservation* — **pass**. Each variant maps cleanly onto one allowed axis of the family (magnitude reproducibility vs. geometry-vs-magnitude contrast with behavioral association) without merging the forbidden semantic distinction between coarse-statistic agreement and geometric/behavioral preservation.
- *scientific value* — **pass**. The plans go beyond general reproducibility and within-study context-sensitivity literature by isolating a residual laboratory component after biological/sampling adjustment (v1) and by directly contrasting held-out reproducibility of geometry versus magnitude with an independent behavioral check (v2).
- *dataset grounding* — **pass**. Required variables (lab, subject, session, probe, trial timing, choice, cluster/anatomy fields, spike shards) are documented in the schema, coverage, and shard evidence views; unresolved decisions are appropriately deferred as pre-execution locks rather than treated as resolved facts.
- *overclaim boundary* — **pass**. Claim ceilings are descriptive (v1) and predictive (v2) with explicit interpretation limits noting the observational nature of laboratory comparisons and the subject-nested-in-laboratory confound; no causal or universal claims are asserted.
- *competing explanations* — **pass**. Both plans enumerate plausible alternative explanations (unmeasured subject composition, targeting/quality/geometry imbalance, decoder instability, superficial task-timing alignment, alignment-method-imposed similarity) that must be ruled out or acknowledged.
- *controls adequacy* — **pass**. Each variant specifies concrete positive and negative controls, leakage audits, and sensitivity diagnostics appropriate to its estimand (permutation and cross-session exclusion for v1; synthetic shared/laboratory-specific geometry recovery and choice-permutation leakage checks for v2).
- *material revision risk* — **not_applicable**. This is the round-zero initial plan draft with no prior review history, so material-revision risk relative to a prior accepted plan does not apply.
- *sibling separation* — **pass**. v1 and v2 target distinct, non-overlapping estimands (matched-stratum coarse magnitude agreement vs. held-out geometric similarity plus behavioral-association comparison), consistent with the family's target-contrast axis and without collapsing the two into a single claim.
- *prior issue resolution* — **not_applicable**. No prior review round or issue ledger entries exist yet for this branch (review_round=0, empty issue_ledger and prior_review_history).
