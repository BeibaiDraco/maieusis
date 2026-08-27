> ⚠️ Data basis: this family's open gap / key claims rest on ABSTRACT-ONLY literature (full text was not available to this system). The questions are literature-motivated but NOT fulltext-verified; a domain expert should confirm against primary sources.

# Neural trajectory geometry versus richer behavioral explanations

This is a development rejection dossier. It is planning-only and does not report scientific results.
Dataset grounding level: `sample_inspected`.
Dataset claim status: `unverified`.

## Question Family

Tests whether apparent neural organization for curved reaching reflects trajectory-level structure beyond simple kinematics, while separating prospective geometry from execution-related residual structure.

## Scientific Motivation

Population activity may encode or dynamically organize path-level structure, but apparent trajectory representations can also arise from hand, cursor, eye, timing, or other correlated behavioral variables. Richer covariates can adjudicate these accounts without being treated merely as nuisance.

## Why This Family Was Not Carried Forward

Both active variants of this family require dissociations that the MC_Maze_Small dataset
(DANDI 000140; single subject Jenkins; 100 train trials with behavior across 27 conditions =
9 maze_ids x 3 versions; test file has no behavior) cannot provide without changing the
protected scientific intent.

Variant prospective-path-geometry: The only endpoint-matched curved-versus-straight
realization is barrier (version 1, curved) versus no-barrier (version 0, straight) trials to
the same 9 targets. Every curved condition displays 9 barriers and every straight condition
displays none; there are no curved reaches without barriers and no barrier configuration that
yields a straight plan. Intended path curvature is thus perfectly confounded with the visible
barrier / task-condition cue. The Question Owner ruled on operationalization
op-prospective-barrier-cue-001 that, because task-condition cues are an explicit protected
alternative explanation, residual preparatory separation in this design cannot be interpreted
as path-level organization independent of that alternative even under the specified covariates
and a bounded associational claim, and required a cue-matched dissociation "or do not pursue
this variant with this dataset." No cue-matched curved/straight condition exists here, so the
required change is unsatisfiable and the variant is a dataset mismatch.

Variant execution-residual: The variant's discriminating observation is a held-out double
contrast that must (a) distinguish task-defined route intentions across behaviorally matched
executions and (b) distinguish execution-specific trajectory variation within the same intended
route. Executed trajectories are organized almost entirely by route (within-route trajectory
distance median ~41 / p90 ~85 vs nearest cross-route condition distance ~64 min / ~196 median),
so distinct route intentions essentially never produce behaviorally matched executions; arm (a)
cannot be constructed. Within-route variation rests on only ~2-4 repeats (curvature std
~0.02-0.11), and behavior exists only in the 100-trial train file. The invariant forbids
reducing the double contrast, so no faithful repair exists within this dataset.

Because neither variant can be faithfully operationalized against this dataset, and no active
variant is accepted or accepted_requires_new_skill, the family branch is rejected on
dataset-mismatch grounds. The verified endpoint-matched curved/straight behavioral structure,
region composition, timing, and trajectory-overlap evidence are preserved for reuse if a
cue-matched or trajectory-decoupled dataset becomes available. What would make this answerable: For prospective-path-geometry: a dataset with curved and straight reaches under matched cue conditions (e.g., barriers present but path curvature manipulated independently, or curved reaches without a distinguishing visible cue), so intended path geometry can be dissociated from the visible task-condition cue. For execution-residual: a task in which the same task-defined route is executed with substantially varying trajectories AND different route intentions can share behaviorally matched executions, with many repeats per condition, so the double contrast can be built with full trajectory-history conditioning. For both: many more trials per condition and behavioral covariates available on an independent held-out split, rather than 100 train trials with behavior and a behavior-free test split.

## Dataset Leverage

Dataset claim status is unverified; observed-depth label is sample_inspected. Dataset leverage remains a planning hypothesis, by variant: Variant 1, not carried forward (rejected dataset mismatch): If delayed straight and curved reaches include sufficiently overlapping pre-movement neural, hand, and eye measurements and permit endpoint-matched comparisons, they may support a later evaluation of residual path-level population geometry; these conditions require verification. Variant 2, not carried forward (rejected dataset mismatch): If the release contains sufficiently overlapping neural, hand, cursor, eye, and task-context observations, it may support comparison of route-intention associations across matched trajectory histories and execution-specific associations within intended-route contexts. No scientific-result generation was performed.

## Variant Outcomes

- Variant 1 (Prospective endpoint-matched test of path-level population geometry beyond component movement features and pre-movement state proxies): Before movement, do endpoint-matched curved and straight plans exhibit a population-geometric distinction that is independent of initial direction, endpoint direction, distance, speed, and immediately observable hand and eye state, and concordant across scientifically justified geometry-sensitive representations or metrics?
  - Distinguishing test: This variant tests pre-movement, endpoint-matched curved-versus-straight population geometry and requires residual, cross-representation concordance after accounting for specified planning features and state proxies. The sibling instead concerns execution-period neural structure after accounting for concurrent multidimensional behavior. The discriminating observation is Support for prospective path organization would require an endpoint-matched curved-versus-straight preparatory distinction that remains after accounting for initial direction, endpoint direction, distance, speed, and immediately observable hand and eye state, and whose interpretation is concordant across prespecified, scientifically justified geometry-sensitive representations or metrics. Generic decoding, tuning, or a distinction confined to one geometric construction would not satisfy this observation.
  - Planning disposition: Rejected dataset mismatch. Endpoint-matched curved-vs-straight is only realizable as barrier-vs-no-barrier, perfectly confounding intended path curvature with the visible barrier cue; the Owner ruled this violates the protected intent and required a cue-matched dissociation that this dataset cannot provide.
  - What would support or weaken it: A residual and cross-representation-concordant distinction would support a bounded associational claim that preparatory population geometry contains path-level organization not explained by the specified movement features or immediately observable hand and eye state. If the apparent distinction is consistently eliminated after accounting for the specified variables, or is consistently absent under informative endpoint-matched comparisons, the result would weaken the prospective path-organization account and favor a component-feature or observable-state explanation. If conclusions vary across scientifically justified geometric constructions, endpoint matching or covariate separation is inadequate, or relevant pre-movement measurements lack sufficient overlap, prospective path organization would remain unresolved rather than being supported or rejected.
- Variant 2 (Execution-period double contrast separating full-trajectory encoding, behavior-specific residuals, and route-intention association): During movement, after conditioning on the full recorded time-varying hand trajectory—including nonlinear and history-dependent kinematic structure—and available cursor and eye behavior, does motor-cortical population structure track task-defined route intention across behaviorally matched executions, or instead track execution-specific trajectory variation within the same intended route context?
  - Distinguishing test: Unlike the prospective sibling, this variant concerns execution-period population structure and requires a double contrast across matched executions and within intended-route contexts after accounting for full nonlinear trajectory history; it does not ask whether pre-movement geometry predicts a future path. The discriminating observation is The key observation would be a held-out double contrast: whether population structure distinguishes task-defined route intentions among executions matched or explicitly modeled on full recorded trajectory history and other available behavior, and whether it distinguishes execution-specific trajectory variation within the same intended route. Cross-execution persistence tied to route intention would favor an abstract-context association; tracking within-context trajectory variation would favor behavior-specific residual structure; loss of both distinctions after rich trajectory-history adjustment would favor generic full-trajectory encoding.
  - Planning disposition: Rejected dataset mismatch. The required held-out double contrast cannot be built: route intention and executed trajectory are confounded by the maze design so no behaviorally matched executions span different route intentions, and within-route variation rests on ~2-4 repeats; reducing the double contrast would be scientific drift.
  - What would support or weaken it: If route-context structure persists across behaviorally matched executions and exceeds within-context sensitivity to execution variation, it would support only a bounded association between population activity and task-defined route intention conditional on the measured behavioral set. It would not establish a curvature-specific neural mechanism or exclude unmeasured behavioral causes. If the apparent route-context distinction is attenuated by full nonlinear trajectory-history and available behavioral adjustment, or residual structure primarily follows within-context execution variation, the result would favor generic full-trajectory encoding or behavior-specific structure over an abstract route-intention interpretation. If trajectory histories cannot be adequately matched or modeled, route intention is confounded with execution, or held-out contrasts are unstable, the evidence would not discriminate among full-trajectory encoding, behavior-specific residual structure, and intention-related association.

## Competing Explanations And Controls

Competing explanations that must remain visible, by variant: Variant 1, not carried forward (rejected dataset mismatch): Preparatory population geometry distinguishes intended curved and straight paths as path-level objects beyond the specified component features and observable states. Any apparent path distinction is explained by initial direction, endpoint direction, distance, speed, task-condition cues, or immediately observable hand or eye state. Residual separation reflects a particular geometric representation or metric rather than a stable feature of preparatory population organization. Insufficient overlap or measurement of relevant pre-movement states prevents the proxy and path-level accounts from being distinguished. Variant 2, not carried forward (rejected dataset mismatch): Population structure may be explained by nonlinear and history-dependent encoding of the full recorded hand trajectory together with available cursor and eye behavior. Residual structure may track execution-specific trajectory variation within a common intended-route context. Structure associated with route context may generalize across distinct but behaviorally matched executions, consistent with an abstract or intention-related association. Any surviving association may reflect unmeasured behavioral, sensory, timing, or task variables rather than either a curvature-specific mechanism or route intention.

## Outcome Meanings

Possible outcome meanings, by variant: Variant 1, not carried forward (rejected dataset mismatch): A residual and cross-representation-concordant distinction would support a bounded associational claim that preparatory population geometry contains path-level organization not explained by the specified movement features or immediately observable hand and eye state. If the apparent distinction is consistently eliminated after accounting for the specified variables, or is consistently absent under informative endpoint-matched comparisons, the result would weaken the prospective path-organization account and favor a component-feature or observable-state explanation. If conclusions vary across scientifically justified geometric constructions, endpoint matching or covariate separation is inadequate, or relevant pre-movement measurements lack sufficient overlap, prospective path organization would remain unresolved rather than being supported or rejected. Variant 2, not carried forward (rejected dataset mismatch): If route-context structure persists across behaviorally matched executions and exceeds within-context sensitivity to execution variation, it would support only a bounded association between population activity and task-defined route intention conditional on the measured behavioral set. It would not establish a curvature-specific neural mechanism or exclude unmeasured behavioral causes. If the apparent route-context distinction is attenuated by full nonlinear trajectory-history and available behavioral adjustment, or residual structure primarily follows within-context execution variation, the result would favor generic full-trajectory encoding or behavior-specific structure over an abstract route-intention interpretation. If trajectory histories cannot be adequately matched or modeled, route intention is confounded with execution, or held-out contrasts are unstable, the evidence would not discriminate among full-trajectory encoding, behavior-specific residual structure, and intention-related association.

## Planning Status and Limits

This scientific rejection is a completed planning outcome under automated host review. Optional post-hoc human review may be imported later. It remains planning-only and does not authorize a downstream bridge or execution or claim scientific results.

- Dataset statements are labeled `unverified`; planner-authored locators or digests alone do not verify an observation.
- Dataset grounding here reached bounded inspection of dataset samples; it includes no scientific-result values or execution outputs.
- A separate bridge approval is still required before downstream execution artifacts.
