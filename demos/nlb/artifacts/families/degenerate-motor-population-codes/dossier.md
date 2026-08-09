> ⚠️ Provisional inspiration: planning continued from source-bound but not independently reviewed inputs. Dataset claims remain conditional or unverified, and this dossier cannot be elevated above provisional authority without independent review.

> ⚠️ Data basis: this family's open gap / key claims rest on ABSTRACT-ONLY literature (full text was not available to this system). The questions are literature-motivated but NOT fulltext-verified; a domain expert should confirm against primary sources.

# Degeneracy and semantic equivalence in motor population codes

This is a development rejection dossier. It is planning-only and does not report scientific results.
Dataset grounding level: `schema_metadata_inspected`.
Dataset claim status: `unverified`.

## Question Family

Investigates whether structurally different population states can carry similar movement meaning and whether such degeneracy reflects robustness or hidden task distinctions.

## Scientific Motivation

Different neural activity patterns may be semantically equivalent for movement, but apparent equivalence could instead result from coarse behavioral measurement or unobserved distinctions in task context.

## Why This Family Was Not Carried Forward

The single active variant requires testing whether M1 execution states in a common reach segment, matched for immediate movement prediction, retain preceding-route identity that generalizes to HELD-OUT route instances after equalizing instantaneous kinematics, speed, curvature, movement phase, target location, environmental conditions, and task demands. MC_Maze_Small (DANDI 000140) is a single-session, 100-train-trial release spanning 27 conditions (~4 trials/condition), with at most 8 trials (median 4.5) in any (target x route-type) cell. Although M1 units are identifiable (70) and straight/curved routes to shared targets exist with full hand kinematics, the per-route repeat structure cannot support a leakage-free three-way partition (state-equivalence definition, route-boundary definition, held-out route-instance evaluation) with the mandated multi-covariate matching. The dataset's scale and repeat structure are mismatched to the variant's held-out-generalization design. Relaxing 'held-out route instances' to held-out within-trial timepoints would violate the variant intent invariant (forbidden leakage/generalization changes) and is not a permissible repair. What would make this answerable: Use the full MC_Maze release (DANDI 000128), which provides many more trials per maze condition, enabling multiple held-out instances per preceding route and leakage-free definition/evaluation splits. A reaching dataset with deliberate route manipulations that converge on a repeated common segment to a fixed target (many instances per route), so that current kinematics, phase, and target can be equalized while varying only preceding route. Pooling multiple recording sessions of the same subject/task to raise per-route trial counts, provided cross-session drift is modeled as required by the variant invariant.

## Dataset Leverage

Dataset claim status is unverified; observed-depth label is schema_metadata_inspected. Dataset leverage remains a planning hypothesis, by variant: Variant 1, not carried forward (rejected dataset mismatch): If paired M1 population and movement measurements contain repeated common reach segments reached through different preceding routes under otherwise comparable task conditions, they may support a proposal-stage test of whether execution states preserve route history beyond immediate movement prediction. No scientific-result generation was performed.

## Variant Outcomes

- Variant 1 (Execution-specific hidden trajectory-history branch): During execution of a common reach segment, do primary motor cortex population states matched for immediate movement prediction retain information about the preceding route across held-out route instances, when current kinematics, movement phase, target location, environmental conditions, and task demands are held constant?
  - Distinguishing test: The sibling treats similar realized movement across distinct neural states as evidence for degeneracy. This revision instead asks whether matched M1 execution states retain preceding-route identity, with held-out generalization and explicit exclusion of current geometry, planning-region recruitment, environmental flexibility, and broader task demands. The discriminating observation is Within the execution epoch of a common reach segment in an M1 population, states matched for immediate movement prediction remain separable by preceding-route identity on held-out observations and route instances that were not used to define state equivalence, select the execution epoch, or establish the route boundary; the separation must persist when instantaneous kinematics, movement phase, target location, speed, curvature, environmental conditions, and task-flexibility demands are comparable.
  - Planning disposition: Rejected dataset mismatch. M1 units are identifiable and distinct straight/curved routes to shared targets with hand kinematics exist, but at most 8 trials (median 4.5) per (target x route-type) cell over 100 train trials cannot support leakage-free state-equivalence, route-boundary, and held-out route-instance partitions with the required covariate matching; the held-out-generalization intent cannot be preserved on this dataset.
  - What would support or weaken it: A positive result would support the interpretation that apparently movement-equivalent M1 execution states retain trajectory-history content, narrowing the conditions under which those states can be treated as semantically synonymous. A negative result under adequate matching and held-out evaluation would favor semantic equivalence of the measured M1 execution states across preceding routes and would weaken a trajectory-history account distinct from planning or general task context. An inconclusive result would leave the semantic boundary unresolved if route conditions lack sufficient behavioral overlap, held-out generalization is unstable, or measured variables cannot separate trajectory history from planning, drift, or broader task demands.

## Competing Explanations And Controls

Competing explanations that must remain visible, by variant: Variant 1, not carried forward (rejected dataset mismatch): Apparent route-history information reflects residual differences in instantaneous position, velocity, speed, curvature, movement phase, target location, or other measured kinematics. The distinction reflects planning-related activity rather than execution-related retention of trajectory history. Population separation reflects broader task difficulty, environmental flexibility, learning, attention, or other condition differences rather than route history. The apparent distinction arises from temporal drift, sampling noise, or leakage between state matching, context definition, and evaluation. The states are genuinely synonymous for the measured execution segment, with route history absent from the relevant population code.

## Outcome Meanings

Possible outcome meanings, by variant: Variant 1, not carried forward (rejected dataset mismatch): A positive result would support the interpretation that apparently movement-equivalent M1 execution states retain trajectory-history content, narrowing the conditions under which those states can be treated as semantically synonymous. A negative result under adequate matching and held-out evaluation would favor semantic equivalence of the measured M1 execution states across preceding routes and would weaken a trajectory-history account distinct from planning or general task context. An inconclusive result would leave the semantic boundary unresolved if route conditions lack sufficient behavioral overlap, held-out generalization is unstable, or measured variables cannot separate trajectory history from planning, drift, or broader task demands.

## Planning Status and Limits

This scientific rejection is a completed planning outcome under automated independent review. Optional post-hoc human review may be imported later. It remains planning-only and does not authorize a downstream bridge or execution or claim scientific results.

- Dataset statements are labeled `unverified`; planner-authored locators or digests alone do not verify an observation.
- Dataset grounding here reached dataset schema and metadata inspection; it includes no scientific-result values or execution outputs.
- A separate bridge approval is still required before downstream execution artifacts.
