# Scientific questions from the public demos

Maieusis developed twelve scientific question families—six for the
International Brain Laboratory (IBL) Brain-Wide Map and six for the Neural
Latents Benchmark (NLB) MC_Maze-S dataset. Each family contains two
deliberately distinct variants, so the gallery preserves 24 possible lines of
inquiry rather than collapsing them into one generic proposal.

These are worked neuroscience examples, not the scope of the product.
Maieusis is designed for any scientific discipline and any scientific dataset
that provides the lawful, read-only inspection surface needed for planning.
The [main project page](../README.md#explore-the-demos) explains how to try it
with data from another field or join the scientific collaboration program.

> **These are questions and analysis plans, not scientific results.** No final
> analysis was executed, novelty was not established, and no hypothesis was
> confirmed. A plan marked as accepted below was accepted provisionally for
> planning after automated independent review.

## Featured questions

### IBL-002 — When does shared neural variability matter for a decision?

Neural populations fluctuate from trial to trial, but the size of those
fluctuations is only part of the story. Two populations can vary by the same
amount and still have very different behavioral consequences: variability
aligned with a decision-relevant direction could change a choice, whereas
equally large variability in an orthogonal direction may be largely irrelevant.

Maieusis developed this distinction into two complementary questions. The first
asks whether alignment with an independently defined decision direction
predicts held-out choice and reaction time beyond overall covariance magnitude.
The second asks whether apparently decision-related dimensions are better
explained by pose and ongoing behavioral state. Together they distinguish a
task-specific account of population variability from a generic movement-or-state
account, rather than treating all shared “noise” as equivalent.

Both variants produced provisionally accepted planning dossiers. No analysis
was executed, and novelty remained `not_assessed`.

**[Explore both variants, their competing explanations, and what different
outcomes would mean](ibl/artifacts/questions/question_families_detailed.md#family-002-which-shared-variability-dimensions-matter-for-decisions)**

[See the planned study at a glance](ibl/artifacts/families/covariance-alignment/dossier_detailed.md)
· [Open the complete planning record](ibl/artifacts/families/covariance-alignment/dossier.md)

### NLB-006 — What kind of neural stability supports generalization?

“Stable representation” can mean several different things. The average
population activity for each reach may move while the relationships among
reaches remain reproducible. And geometry that repeats reliably within straight
or curved reaches does not necessarily transfer between those two movement
demands.

Using MC_Maze-S recordings from primary motor cortex (M1) and dorsal premotor
cortex (PMd), Maieusis separated these claims into two tests. One compares
relational stability with centroid stability within matched reach conditions
and asks whether the distinction differs between regions. The other first
requires reliable geometry within each demand, then asks whether that geometry
transfers between straight and curved barrier-maze reaches or is consistently
remapped. This distinction separates a shared motor scaffold from stable but
demand-specific organization without mistaking unreliable estimates for
remapping.

Both variants produced provisionally accepted planning dossiers. The dataset
contains one recorded subject, the proposed claims remain descriptive or
predictive rather than causal, and no analysis was executed.

**[Explore both variants, their competing explanations, and what different
outcomes would mean](nlb/artifacts/questions/question_families_detailed.md#family-006-which-geometric-stability-supports-generalization-in-reaching)**

[See the planned study at a glance](nlb/artifacts/families/geometry-definition-generalization/dossier_detailed.md)
· [Open the complete planning record](nlb/artifacts/families/geometry-definition-generalization/dossier.md)

These highlights are entry points, not a ranking. The complete gallery below
shows every family, including a mixed IBL outcome and an NLB validation warning.

## How to read the gallery

- **Plan developed (provisional):** an automated independent reviewer accepted
  the plan as a credible next step. The analysis has not been run.
- **Mixed:** sibling variants reached different outcomes; inspect each one
  separately.
- **Validation warning:** the scientific question remains visible, but the
  returned planning material did not pass validation. There is no accepted
  analysis plan for that family.

For each family, start with **Explore the question**. That page explains the
scientific background, alternatives, assumptions, and possible positive,
negative, or null outcomes for both variants. The shorter plan guide then shows
how the real dataset shaped the proposal, while the complete planning record
preserves the full closure.

## IBL Brain-Wide Map

The International Brain Laboratory is a multi-institution collaboration. Its
Brain-Wide Map contains standardized, multi-laboratory recordings from mice
performing a sensory decision-making task, as described in [*A brain-wide map
of neural activity during complex behaviour*
(2025)](https://doi.org/10.1038/s41586-025-09235-0) and the
[official release guide](https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html).
The demo asks how stable decisions can emerge from heterogeneous, brain-wide
population activity. Five families produced plans for both variants; one
family is intentionally mixed.

### 1. Stable decisions under changing population organization

Stable behavior could arise from an invariant population organization or from
flexible dynamics that preserve an effective readout. The variants separate
cross-context relational invariance from within-episode reconfiguration.

1. [Cross-context invariance](ibl/artifacts/questions/question_families_detailed.md#variant-001001-cross-context-invariance-branch): Across subjects, sessions, and laboratories,
   does relational population geometry predict stable decisions better than
   preservation of particular activity patterns?
2. [Within-episode reconfiguration](ibl/artifacts/questions/question_families_detailed.md#variant-001002-within-episode-reconfiguration-branch): Can task- and state-dependent
   trajectories reconfigure while preserving a stable decision-relevant
   subspace?

Outcome: **plan developed for both variants (provisional).**

[Explore the question](ibl/artifacts/questions/question_families_detailed.md#family-001-stable-decisions-under-changing-population-organization)
· [See the plan at a glance](ibl/artifacts/families/stability-reconfiguration/dossier_detailed.md)
· [Open the complete planning record](ibl/artifacts/families/stability-reconfiguration/dossier.md)

### 2. Which shared-variability dimensions matter for decisions?

Aggregate co-variability magnitude cannot show whether shared fluctuations are
decision-relevant or merely reflect movement and global state. These variants
ask whether the orientation of variability relative to independently defined
dimensions carries the more informative signal.

1. [Decision alignment](ibl/artifacts/questions/question_families_detailed.md#variant-002001-decision-alignment-branch): Does alignment with decision geometry predict choice
   and response-time variation better than overall shared-variability magnitude?
2. [Embodied-state specificity](ibl/artifacts/questions/question_families_detailed.md#variant-002002-embodied-state-specificity-branch): Are apparently decision-related variability
   dimensions better explained by multidimensional pose and ongoing behavioral
   state?

Outcome: **plan developed for both variants (provisional).**

[Explore the question](ibl/artifacts/questions/question_families_detailed.md#family-002-which-shared-variability-dimensions-matter-for-decisions)
· [See the plan at a glance](ibl/artifacts/families/covariance-alignment/dossier_detailed.md)
· [Open the complete planning record](ibl/artifacts/families/covariance-alignment/dossier.md)

### 3. Latent decision state versus observable embodied state

History-dependent population activity can be interpreted as an internal
decision state, observable behavior, immediate task variables, or unexplained
intrinsic dynamics. The variants make those explanations compete instead of
assuming that unexplained neural variation is latent cognition.

1. [Inferred internal state](ibl/artifacts/questions/question_families_detailed.md#variant-003001-inferred-internal-state-branch): Is a history-dependent decision state
   represented across regions beyond sensory input, choice, response time, and
   measured pose?
2. [Observed embodied state](ibl/artifacts/questions/question_families_detailed.md#variant-003002-observed-embodied-state-branch): Does multidimensional pose explain distributed
   activity otherwise attributed to latent state or intrinsic noise?

Outcome: **plan developed for both variants (provisional).**

[Explore the question](ibl/artifacts/questions/question_families_detailed.md#family-003-latent-decision-state-versus-observable-embodied-state)
· [See the plan at a glance](ibl/artifacts/families/latent-decision-state/dossier_detailed.md)
· [Open the complete planning record](ibl/artifacts/families/latent-decision-state/dossier.md)

### 4. How input influence changes during a decision

This family contrasts a discrete within-episode change in input sensitivity
with a distributed transformation of information across regions. The two
scientifically attractive accounts did not receive the same dataset-grounded
outcome.

1. [Within-episode sensitivity transition](ibl/artifacts/questions/question_families_detailed.md#variant-004001-within-episode-sensitivity-transition-branch): Do trajectories show a
   reproducible input-sensitivity change whose timing predicts choice stability
   and response time? **No plan—`rejected_operationalization_failure`.**
2. [Cross-region transformation](ibl/artifacts/questions/question_families_detailed.md#variant-004002-cross-region-transformation-branch): Does decision information transform from
   stimulus-aligned toward choice- and response-aligned organization across
   regions? **Plan developed as `accepted_requires_new_skill`.**

Outcome: **mixed family.** Only the second variant has provisional accepted-plan
authority.

[Explore the question](ibl/artifacts/questions/question_families_detailed.md#family-004-how-input-influence-changes-during-a-decision)
· [See the plan at a glance](ibl/artifacts/families/input-to-choice-dynamics/dossier_detailed.md)
· [Open the complete planning record](ibl/artifacts/families/input-to-choice-dynamics/dossier.md)

### 5. Expansion and compression of decision geometry

Dimensional expansion can separate confusable states, while compression can
support stable readout across heterogeneous activity. The family asks whether
these are distinct computational roles rather than generic consequences of
population size, reliability, or pooling.

1. [Expansion for separation](ibl/artifacts/questions/question_families_detailed.md#variant-005001-expansion-for-separation-branch): Is transient geometric expansion associated
   with better separation of otherwise confusable sensory-decision states?
2. [Compression for generalization](ibl/artifacts/questions/question_families_detailed.md#variant-005002-compression-for-generalization-branch): Is lower-dimensional decision geometry
   associated with stable readout across subjects, sessions, or laboratories?

Outcome: **plan developed for both variants (provisional).**

[Explore the question](ibl/artifacts/questions/question_families_detailed.md#family-005-expansion-and-compression-of-decision-geometry)
· [See the plan at a glance](ibl/artifacts/families/dimensional-transformation/dossier_detailed.md)
· [Open the complete planning record](ibl/artifacts/families/dimensional-transformation/dossier.md)

### 6. Reliability and boundary conditions of population-dynamical claims

An apparent organizing principle can be robust, context-bound, or an artifact
of unreliable estimation. This family treats reproducibility and model
comparison as scientific boundary questions rather than afterthoughts.

1. [Geometric reproducibility](ibl/artifacts/questions/question_families_detailed.md#variant-006001-geometric-reproducibility-branch): Which decision-related geometric relations
   reproduce across acquisition contexts, and do failures track scientific
   rather than measurement boundaries?
2. [Dynamical-model reliability](ibl/artifacts/questions/question_families_detailed.md#variant-006002-dynamical-model-reliability-branch): Are fitted dynamical signatures
   reproducible enough to predict behavior beyond simpler geometric
   descriptions?

Outcome: **plan developed for both variants (provisional).**

[Explore the question](ibl/artifacts/questions/question_families_detailed.md#family-006-reliability-and-boundary-conditions-of-population-dynamical-claims)
· [See the plan at a glance](ibl/artifacts/families/reliability-boundaries/dossier_detailed.md)
· [Open the complete planning record](ibl/artifacts/families/reliability-boundaries/dossier.md)

## Neural Latents Benchmark MC_Maze-S

The Neural Latents Benchmark evaluates latent-variable methods for neural
population activity. Its MC_Maze-S dataset contains spiking activity from one
rhesus macaque's primary motor cortex (M1) and dorsal premotor cortex (PMd)
during delayed straight and curved barrier-maze reaches. See [Pei et al.,
*Neural Latents Benchmark ’21*](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/979d472a84804b9f647bc185a877a8b5-Abstract-round2.html)
and [DANDI:000140, version
0.220113.0408](https://doi.org/10.48324/dandi.000140/0.220113.0408). Five
families produced provisional plans. One family remains visible as a
validation warning and has no accepted-plan authority.

### 1. Invariant and reconfigured population geometry across reach demands

Do straight and curved reaching share a conserved motor scaffold, or do they
require demand-specific reconfiguration? The variants separate regional from
temporal scope.

1. [Regional scope](nlb/artifacts/questions/question_families_detailed.md#variant-001001-regional-scope-test-of-geometric-invariance): Is reach-configuration geometry conserved between
   straight and curved reaches within M1 and PMd, or selectively reconfigured
   in one region?
2. [Temporal scope](nlb/artifacts/questions/question_families_detailed.md#variant-001002-temporal-scope-test-of-geometric-invariance): Does relational reach geometry persist from preparation
   into execution, and is that persistence shared by PMd and M1?

Outcome: **plan developed for both variants (provisional).**

[Explore the question](nlb/artifacts/questions/question_families_detailed.md#family-001-invariant-and-reconfigured-population-geometry-across-reach-demands)
· [See the plan at a glance](nlb/artifacts/families/reach-geometry-invariance/dossier_detailed.md)
· [Open the complete planning record](nlb/artifacts/families/reach-geometry-invariance/dossier.md)

### 2. Selective population coupling between PMd and M1

Cross-region association may reflect task-relevant coordination, dominant local
fluctuations, shared input, or movement covariation. The variants test
specificity without turning predictive alignment into a causal claim.

1. [Task-dimension specificity](nlb/artifacts/questions/question_families_detailed.md#variant-002001-task-dimension-specificity-test): Are PMd–M1 relationships selectively aligned
   with straight-versus-curved reach dimensions rather than dominant local
   variability?
2. [Temporal reorganization](nlb/artifacts/questions/question_families_detailed.md#variant-002002-temporal-reorganization-test): Does coordination specificity change from
   preparation to execution rather than remain a stationary shared-activity
   relationship?

Outcome: **plan developed for both variants (provisional).**

[Explore the question](nlb/artifacts/questions/question_families_detailed.md#family-002-selective-population-coupling-between-pmd-and-m1)
· [See the plan at a glance](nlb/artifacts/families/selective-pmd-m1-coupling/dossier_detailed.md)
· [Open the complete planning record](nlb/artifacts/families/selective-pmd-m1-coupling/dossier.md)

### 3. Preparatory population dynamics as operating regimes for movement

Preparatory trajectories might establish movement-specific operating
conditions, but they might instead reflect elapsed time, impending movement,
or behaviorally irrelevant variation. The question remains scientifically
interesting, but its returned planning material did not pass validation.

1. [Trajectory-class boundary](nlb/artifacts/questions/question_families_detailed.md#variant-003001-trajectory-class-boundary-test): Do straight and curved reaches recruit
   distinct preparatory operating regimes, or diverge only after movement
   begins?
2. [Independent behavioral consequence](nlb/artifacts/questions/question_families_detailed.md#variant-003002-independent-behavioral-consequence-test): Does proximity to a reach-specific
   preparatory state predict the subsequent trajectory better than preparatory
   activity magnitude?

Outcome: **validation warning; provisional/degraded; no accepted-plan authority
for either variant.** This is a pipeline outcome, not evidence that the
scientific idea is false or that the dataset is unsuitable.

[Explore the question](nlb/artifacts/questions/question_families_detailed.md#family-003-preparatory-population-dynamics-as-operating-regimes-for-movement)
· [Read the warning guide](nlb/artifacts/families/preparatory-operating-regimes/dossier_detailed.md)
· [Open the readable warning record](nlb/artifacts/families/preparatory-operating-regimes/dossier.md)

### 4. Behavioral-state explanations for motor-cortical variability

Apparently unexplained motor-cortical variability may reflect intrinsic neural
dynamics, latent readiness, or measured movement and embodied state. The
variants test these alternatives across regions and population subspaces.

1. [Regional distribution](nlb/artifacts/questions/question_families_detailed.md#variant-004001-regional-distribution-test): Is variability associated with multidimensional
   behavioral state distributed similarly across PMd and M1 or concentrated in
   one region?
2. [Task-state geometric overlap](nlb/artifacts/questions/question_families_detailed.md#variant-004002-task-state-geometric-overlap-test): Do behavioral-state dimensions overlap
   with or remain distinct from dimensions that distinguish reach demands?

Outcome: **plan developed for both variants (provisional).**

[Explore the question](nlb/artifacts/questions/question_families_detailed.md#family-004-behavioral-state-explanations-for-motor-cortical-population-variability)
· [See the plan at a glance](nlb/artifacts/families/behavior-explains-neural-variance/dossier_detailed.md)
· [Open the complete planning record](nlb/artifacts/families/behavior-explains-neural-variance/dossier.md)

### 5. Neural co-variability relative to movement-relevant readouts

Large or small shared variability is not intrinsically helpful or harmful; its
consequence may depend on alignment with movement-relevant or interregional
dimensions. The variants separate within-region readout from cross-region
organization.

1. [Within-region readout alignment](nlb/artifacts/questions/question_families_detailed.md#variant-005001-within-region-behavioral-readout-alignment-test): Does alignment with a reach-relevant
   dimension predict movement readout better than aggregate co-variability
   magnitude within PMd and M1?
2. [Cross-region variability alignment](nlb/artifacts/questions/question_families_detailed.md#variant-005002-cross-region-variability-alignment-test): Is co-variability in one region
   selectively aligned with dimensions associated with the other beyond
   dominant local modes?

Outcome: **plan developed for both variants (provisional).**

[Explore the question](nlb/artifacts/questions/question_families_detailed.md#family-005-structure-of-neural-co-variability-relative-to-movement-relevant-readouts)
· [See the plan at a glance](nlb/artifacts/families/variability-alignment-readout/dossier_detailed.md)
· [Open the complete planning record](nlb/artifacts/families/variability-alignment-readout/dossier.md)

### 6. Which geometric stability supports generalization in reaching?

Within-condition reproducibility and transfer across reach demands are
different meanings of “stable geometry.” The variants keep centroid change,
relational stability, and demand-specific remapping as distinct claims.

1. [Within-condition stability](nlb/artifacts/questions/question_families_detailed.md#variant-006001-within-condition-stability-definition-test): Do M1 and PMd differ in whether relational
   reach geometry is reproducible despite shifts in population centroids?
2. [Cross-demand generalization](nlb/artifacts/questions/question_families_detailed.md#variant-006002-cross-demand-generalization-test): Does relational geometry transfer across
   straight and curved reaches, or can within-condition stability coexist with
   demand-specific remapping?

Outcome: **plan developed for both variants (provisional).**

[Explore the question](nlb/artifacts/questions/question_families_detailed.md#family-006-which-geometric-stability-supports-generalization-in-reaching)
· [See the plan at a glance](nlb/artifacts/families/geometry-definition-generalization/dossier_detailed.md)
· [Open the complete planning record](nlb/artifacts/families/geometry-definition-generalization/dossier.md)

## How Maieusis reached these questions

Both demos began from the same [12 source papers](PAPER_SOURCES.md). Maieusis
made a PaperCase for each usable source, reconstructed question-forming moves
from published evidence, and abstracted reusable patterns without copying the
papers' conclusions. NLB reused those reviewed paper-derived products, then
generated a new dataset narrative, literature context, question families,
dataset inspections, plans, and reviews for MC_Maze-S.

- IBL: [question-formation patterns](ibl/artifacts/paperbank/question_patterns_detailed.md)
  · [dataset narrative](ibl/artifacts/dataset/dataset_narrative.md)
  · [topic evidence](ibl/artifacts/literature/topic_evidence_summary.md)
- NLB: [question-formation patterns](nlb/artifacts/paperbank/question_patterns_detailed.md)
  · [dataset narrative](nlb/artifacts/dataset/dataset_narrative.md)
  · [topic evidence](nlb/artifacts/literature/topic_evidence_summary.md)

To reproduce the runs, continue to the [IBL guide](ibl/README.md) and then the
[IBL → NLB guide](nlb/README.md). Machine-readable checksums and technical
validation facts are available in the [IBL manifest](ibl/demo_manifest.yaml) and
[NLB manifest](nlb/demo_manifest.yaml).
