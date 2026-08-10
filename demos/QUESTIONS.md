# All demo questions

[IBL](ibl/README.md) · [NLB](nlb/README.md) · [Climate](climate/README.md) ·
[Source papers](PAPER_SOURCES.md)

Eighteen scientific question families across three datasets, six each, two variants apiece. Thirty-six
lines of inquiry, developed from source papers and a real dataset.

> **Nothing here was executed.** No effect was measured, no hypothesis was tested, and no dossier
> reports an outcome. These are plans and reasons not to proceed. Prior-art review ran on every
> variant within a recorded scope, and no question is claimed to be novel.

**Three of these families closed without a plan, and five variants were held back before planning
because the prior-art review found a close prior work.** Those are on this page with the rest. A
system that only shows you what worked is not showing you anything.

Evidence in these runs is visibly draft and largely abstract-only: the literature supporting a
family was often not full-text verified, and the pages say so where it applies.

These artifacts were produced by demonstration runs on the release-candidate source tree, not by the
published package. They show the scientific workflow; they are not a statement about the exact bytes
you install. Each demo page names the run that produced it.


## IBL Brain-Wide Map — mouse decision-making

Standardized multi-laboratory Neuropixels recordings from mice performing a sensory decision task, with the same protocol repeated across laboratories. That repetition is what makes questions about reproducibility and idiosyncrasy askable at all.

Featured on the [ibl demo page](ibl/README.md): *Task relevance of structured neural co-variability*.

### 1. Invariant and reorganized population geometry during decision-making

Population representations may preserve decision-relevant organization across contexts, reorganize while preserving equivalent meaning, or change because sensory, movement, and sampling conditions differ.

1. [Cross-context conservation and predictive transfer](ibl/artifacts/questions/question_families_detailed.md#variant-001001-cross-context-conservation-and-predictive-transfer): Does decision-relevant population geometry remain sufficiently conserved across subjects, sessions, and laboratories to support predictive generalization of stimulus and choice relationships?
2. [Semantic preservation despite geometric reorganization](ibl/artifacts/questions/question_families_detailed.md#variant-001002-semantic-preservation-despite-geometric-reorganization): Can population geometry reorganize across behavioral contexts while preserving equivalent stimulus or decision meaning?

Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](ibl/artifacts/questions/question_families_detailed.md#family-001-invariant-and-reorganized-population-geometry-during-decision-making)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](ibl/artifacts/families/invariant-decision-geometry/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](ibl/artifacts/families/invariant-decision-geometry/dossier.md)

### 2. Task relevance of structured neural co-variability

Co-variability may be a global nuisance, a task-aligned computational resource, or structured modulation associated primarily with embodied state rather than decision processing.

1. [Task-aligned structure versus aggregate magnitude](ibl/artifacts/questions/question_families_detailed.md#variant-002001-task-aligned-structure-versus-aggregate-magnitude): Is the relationship between neural co-variability and decision performance better explained by alignment with stimulus- or choice-relevant population dimensions than by overall co-variability magnitude?
2. [Decision organization versus embodied co-variation](ibl/artifacts/questions/question_families_detailed.md#variant-002002-decision-organization-versus-embodied-co-variation): Is structured population co-variability associated more strongly with decision variables or with video-derived movement and pose states?

Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](ibl/artifacts/questions/question_families_detailed.md#family-002-task-relevance-of-structured-neural-co-variability)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](ibl/artifacts/families/covariability-structure/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](ibl/artifacts/families/covariability-structure/dossier.md)

### 3. Population-dynamical transitions from sensation to action

Similar choices can emerge from sequential decision regimes, continuous single-regime dynamics, or trajectories dominated by impending movement.

1. [Sequential-regime versus continuous-dynamics test](ibl/artifacts/questions/question_families_detailed.md#variant-003001-sequential-regime-versus-continuous-dynamics-test): Do population dynamics exhibit a transition from stimulus-sensitive to choice-stabilizing organization whose timing predicts response-time variation?
2. [Choice dynamics versus movement preparation](ibl/artifacts/questions/question_families_detailed.md#variant-003002-choice-dynamics-versus-movement-preparation): Are late decision-related population trajectories specifically associated with choice formation, or are they better explained as distributed preparation of measured movements?

Outcome: **Mixed family** — one variant reached a reviewed plan; its sibling did not, and says why.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](ibl/artifacts/questions/question_families_detailed.md#family-003-population-dynamical-transitions-from-sensation-to-action)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](ibl/artifacts/families/decision-dynamics/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](ibl/artifacts/families/decision-dynamics/dossier.md)

### 4. Broad versus selective brain-wide organization of decision signals

Brain-wide detectability may reflect genuinely distributed computation, repeated local representations, common task covariates, or selective organization obscured by coarse summaries.

1. [Anatomical breadth versus differentiation](ibl/artifacts/questions/question_families_detailed.md#variant-004001-anatomical-breadth-versus-differentiation): Are stimulus- and choice-related population representations broadly conserved across anatomical populations, or selectively differentiated across the recorded brain? *(held back before planning: the prior-art review resolved a close prior work — the family page states which, and what would distinguish this variant from it)*
2. [Selective predictive dimensions versus generic shared activity](ibl/artifacts/questions/question_families_detailed.md#variant-004002-selective-predictive-dimensions-versus-generic-shared-activity): Are predictive relationships between anatomical populations carried by selective task-relevant dimensions rather than by broadly shared population activity?

Outcome: **Deferred on prior-art grounds** — one variant reached an independently reviewed plan; its sibling was held back before planning because the review resolved a close prior work, and the family page names it.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](ibl/artifacts/questions/question_families_detailed.md#family-004-broad-versus-selective-brain-wide-organization-of-decision-signals)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](ibl/artifacts/families/distributed-selective-organization/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](ibl/artifacts/families/distributed-selective-organization/dossier.md)

### 5. Replicable and idiosyncratic components of decision geometry

A common task may induce reproducible population organization, but apparent replication can arise from shared observables, while genuine computational solutions may remain individual-specific.

1. [Laboratory-level reproducibility](ibl/artifacts/questions/question_families_detailed.md#variant-005001-laboratory-level-reproducibility): Which aspects of decision-related population geometry are reproducible across laboratories rather than specific to laboratory context?
2. [Subject-specific geometry with shared function](ibl/artifacts/questions/question_families_detailed.md#variant-005002-subject-specific-geometry-with-shared-function): Can subject-specific population geometries implement a shared predictive relationship between sensory evidence, decisions, and response times?

Outcome: **Mixed family** — one variant reached a reviewed plan; its sibling did not, and says why.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](ibl/artifacts/questions/question_families_detailed.md#family-005-replicable-and-idiosyncratic-components-of-decision-geometry)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](ibl/artifacts/families/replicable-idiosyncratic-geometry/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](ibl/artifacts/families/replicable-idiosyncratic-geometry/dossier.md)

### 6. Behavioral meaning of population geometry

Population geometry may contribute to decision computation, merely correlate with task conditions, or reflect movement and state variables that independently shape behavior.

1. [Geometry-specific prediction of choice errors](ibl/artifacts/questions/question_families_detailed.md#variant-006001-geometry-specific-prediction-of-choice-errors): Do trial-to-trial deviations in decision-related population geometry predict choice errors in a manner that distinguishes distributed coding from simpler signal-strength accounts? *(held back before planning: the prior-art review resolved a close prior work — the family page states which, and what would distinguish this variant from it)*
2. [Trajectory organization and graded decision timing](ibl/artifacts/questions/question_families_detailed.md#variant-006002-trajectory-organization-and-graded-decision-timing): Does the organization of neural population trajectories predict response-time variation beyond sensory conditions and measured movement?

Outcome: **Deferred on prior-art grounds** — one variant reached an independently reviewed plan; its sibling was held back before planning because the review resolved a close prior work, and the family page names it.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](ibl/artifacts/questions/question_families_detailed.md#family-006-behavioral-meaning-of-population-geometry)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](ibl/artifacts/families/functional-errors-latency/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](ibl/artifacts/families/functional-errors-latency/dossier.md)


## NLB MC_Maze-S — macaque reaching

Simultaneous recordings from primary motor cortex and dorsal premotor cortex during delayed straight and curved reaches. Two areas recorded at once is the feature several of these questions turn on. [Dataset notes](nlb/DATASET_NOTES.md), and a [67-line script](nlb/verify_region_mapping.py) you can run to check the unit counts and electrode correction yourself.

Featured on the [nlb demo page](nlb/README.md): *Shared and selective population organization across M1 and PMd*.

### 1. Temporal organization of motor population geometry

Similar reach behavior could arise from a continuously evolving population trajectory or from distinct preparatory and execution-related organizations; descriptive geometry alone cannot distinguish these accounts.

1. [Continuous-organization account](nlb/artifacts/questions/question_families_detailed.md#variant-001001-continuous-organization-account): Does delayed-reach population activity preserve a common task-relevant geometry while continuously transforming from preparation into execution?
2. [Regime-transition account](nlb/artifacts/questions/question_families_detailed.md#variant-001002-regime-transition-account): Is delayed reaching organized by a qualitative population-dynamics transition from movement preparation to execution rather than by one continuous regime?

Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](nlb/artifacts/questions/question_families_detailed.md#family-001-temporal-organization-of-motor-population-geometry)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](nlb/artifacts/families/motor-geometry-temporal-organization/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](nlb/artifacts/families/motor-geometry-temporal-organization/dossier.md)

### 2. Population geometry across straight and curved reaches

Stable task-relevant representations may support generalization across trajectory contexts, but apparent stability could reflect shared kinematics, while remapping could reflect either useful context specialization or incidental differences.

1. [Cross-context invariance branch](nlb/artifacts/questions/question_families_detailed.md#variant-002001-cross-context-invariance-branch): Is a task-relevant population geometry conserved across straight and curved reaches in a way that supports cross-context prediction of movement?
2. [Adaptive-remapping branch](nlb/artifacts/questions/question_families_detailed.md#variant-002002-adaptive-remapping-branch): Does population geometry remap between straight and curved reaches in a manner that selectively represents barrier-dependent movement demands? *(held back before planning: the prior-art review resolved a close prior work — the family page states which, and what would distinguish this variant from it)*

Outcome: **Deferred on prior-art grounds** — one variant reached an independently reviewed plan; its sibling was held back before planning because the review resolved a close prior work, and the family page names it.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](nlb/artifacts/questions/question_families_detailed.md#family-002-population-geometry-across-straight-and-curved-reaches)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](nlb/artifacts/families/trajectory-context-generalization/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](nlb/artifacts/families/trajectory-context-generalization/dossier.md)

### 3. Shared and selective population organization across M1 and PMd

Regional activity may reflect a common motor representation expressed across both areas or complementary organizations emphasizing different aspects of preparation and movement; regional decodability alone cannot decide between them.

1. [Shared-geometry branch](nlb/artifacts/questions/question_families_detailed.md#variant-003001-shared-geometry-branch): Do M1 and PMd express a shared population geometry for reach trajectories despite possible differences in local activity patterns?
2. [Complementary-specialization branch](nlb/artifacts/questions/question_families_detailed.md#variant-003002-complementary-specialization-branch): Are M1 and PMd population geometries selectively organized around complementary preparatory and movement-related information?

Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](nlb/artifacts/questions/question_families_detailed.md#family-003-shared-and-selective-population-organization-across-m1-and-pmd)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](nlb/artifacts/families/m1-pmd-population-organization/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](nlb/artifacts/families/m1-pmd-population-organization/dossier.md)

### 4. Functional meaning of motor-population co-variability

Changes in overall population variability may be descriptively prominent but functionally uninformative if only particular covariance components align with task-relevant geometry.

1. [Movement-alignment branch](nlb/artifacts/questions/question_families_detailed.md#variant-004001-movement-alignment-branch): Does the predictive consequence of motor-population co-variability depend more on alignment with movement-relevant dimensions than on its overall magnitude?
2. [Context-alignment branch](nlb/artifacts/questions/question_families_detailed.md#variant-004002-context-alignment-branch): Is population co-variability selectively aligned with dimensions that distinguish straight from curved reach contexts, beyond alignment with generic movement dimensions?

Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](nlb/artifacts/questions/question_families_detailed.md#family-004-functional-meaning-of-motor-population-co-variability)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](nlb/artifacts/families/covariability-functional-alignment/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](nlb/artifacts/families/covariability-functional-alignment/dossier.md)

### 5. Degeneracy and semantic equivalence in motor population codes

Different neural activity patterns may be semantically equivalent for movement, but apparent equivalence could instead result from coarse behavioral measurement or unobserved distinctions in task context.

1. [Movement-equivalence branch](nlb/artifacts/questions/question_families_detailed.md#variant-005001-movement-equivalence-branch): Can structurally distinct motor-population states predict similar reach trajectories, indicating a degenerate population code for movement? *(held back before planning: the prior-art review resolved a close prior work — the family page states which, and what would distinguish this variant from it)*
2. [Hidden-context branch](nlb/artifacts/questions/question_families_detailed.md#variant-005002-hidden-context-branch): Do population states that appear equivalent for immediate movement preserve distinct information about straight versus curved reach context?

Outcome: **Scientific rejection terminal** — closed without a plan, with the evidence that closed it. One variant had already been deferred on prior-art grounds before planning began.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](nlb/artifacts/questions/question_families_detailed.md#family-005-degeneracy-and-semantic-equivalence-in-motor-population-codes)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](nlb/artifacts/families/degenerate-motor-population-codes/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](nlb/artifacts/families/degenerate-motor-population-codes/dossier.md)

### 6. Functional meaning of motor-manifold form

Motor population activity may occupy an approximately simple reusable structure or a nonlinear context-dependent manifold, but geometric complexity alone does not establish computational function.

1. [Simple reusable-manifold branch](nlb/artifacts/questions/question_families_detailed.md#variant-006001-simple-reusable-manifold-branch): Does an approximately simple population geometry support reusable prediction of reach kinematics across trajectory contexts?
2. [Nonlinear context-manifold branch](nlb/artifacts/questions/question_families_detailed.md#variant-006002-nonlinear-context-manifold-branch): Does nonlinear population-manifold structure capture trajectory-context distinctions that are missed by a simple shared geometry?

Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](nlb/artifacts/questions/question_families_detailed.md#family-006-functional-meaning-of-motor-manifold-form)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](nlb/artifacts/families/manifold-form-functional-meaning/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](nlb/artifacts/families/manifold-form-functional-meaning/dossier.md)


## Climate — ERA5-derived 60 degrees North stratospheric dynamics

A vertical column at one latitude: wave activity, zonal winds, and eddy forcing across 97 heights, six-hourly, over roughly four decades. It can say a great deal about vertical structure and almost nothing about geography, and several of these questions are bounded by exactly that. [Dataset notes](climate/DATASET_NOTES.md).

Featured on the [climate demo page](climate/README.md): *Propagating episodes versus coherent modes of vertical coupling*.

### 1. Recurrent states versus transition-centered organization of the polar stratosphere

Long-lived circulation states may be substantive recurrent organizations of the system, but apparent regimes can also emerge from continuous evolution whose scientifically distinctive structure is concentrated near transitions.

1. [State-centered representation test](climate/artifacts/questions/question_families_detailed.md#variant-001001-state-centered-representation-test): Do recurrent vertically organized circulation states recur robustly across seasonal and multi-decade partitions, and do they provide information about persistence beyond a continuous circulation description?
2. [Transition-centered dynamical contrast](climate/artifacts/questions/question_families_detailed.md#variant-001002-transition-centered-dynamical-contrast): Are changes in wave activity, eddy forcing, and vertical circulation organization concentrated around transitions between circulation states, or do they evolve similarly during matched within-state intervals?

Outcome: **Mixed family** — one variant reached a reviewed plan; its sibling did not, and says why.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](climate/artifacts/questions/question_families_detailed.md#family-001-recurrent-states-versus-transition-centered-organization-of-the-polar-stratosphere)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](climate/artifacts/families/state-versus-transition-organization/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](climate/artifacts/families/state-versus-transition-organization/dossier.md)

### 2. Wave forcing, circulation response, and state-dependent feedback

Wave and eddy activity may actively precede circulation transitions, while the circulation state may simultaneously regulate wave propagation and the persistence of the response; covariation alone cannot distinguish these directions.

1. [Forcing-first temporal-ordering test](climate/artifacts/questions/question_families_detailed.md#variant-002001-forcing-first-temporal-ordering-test): Do episodes of anomalous wave activity or eddy forcing consistently precede vertically coherent circulation transitions rather than merely accompanying or following them?
2. [Background-state effect-modification test](climate/artifacts/questions/question_families_detailed.md#variant-002002-background-state-effect-modification-test): Does the pre-existing vertical circulation state condition whether comparable wave or eddy-forcing episodes produce persistence, transition, or rapid recovery?

Outcome: **Scientific rejection terminal** — closed without a plan, with the evidence that closed it.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](climate/artifacts/questions/question_families_detailed.md#family-002-wave-forcing-circulation-response-and-state-dependent-feedback)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](climate/artifacts/families/wave-forcing-and-state-dependence/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](climate/artifacts/families/wave-forcing-and-state-dependence/dossier.md)

### 3. Persistence, apparent memory, and path-dependent recovery

Low-frequency persistence may arise from state switching without long intrinsic memory, while asymmetric trajectories and recovery may indicate that forcing history carries predictive information beyond the current circulation state.

1. [State-switching explanation of aggregate persistence](climate/artifacts/questions/question_families_detailed.md#variant-003001-state-switching-explanation-of-aggregate-persistence): Can apparent long-memory behavior in polar-stratospheric circulation be accounted for by seasonal evolution and switching among recurrent states, or does substantial persistence remain within states?
2. [Path-dependent recovery test](climate/artifacts/questions/question_families_detailed.md#variant-003002-path-dependent-recovery-test): For similar displaced circulation states, does prior wave-forcing and transition history predict distinct recovery trajectories beyond the information in the current vertical state and seasonal context?

Outcome: **Mixed family** — one variant reached a reviewed plan; its sibling did not, and says why.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](climate/artifacts/questions/question_families_detailed.md#family-003-persistence-apparent-memory-and-path-dependent-recovery)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](climate/artifacts/families/persistence-memory-and-hysteresis/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](climate/artifacts/families/persistence-memory-and-hysteresis/dossier.md)

### 4. Extreme polar-vortex episodes as distinct pathways and recovery classes

Extreme polar-vortex disruptions may be amplified members of ordinary variability with a common lifecycle, or they may comprise heterogeneous dynamical pathways whose onset and recovery cannot be summarized by one composite.

1. [Antecedent-pathway heterogeneity test](climate/artifacts/questions/question_families_detailed.md#variant-004001-antecedent-pathway-heterogeneity-test): Do extreme polar-vortex disruptions separate into recurrent onset pathways distinguished by the vertical timing and composition of antecedent wave and eddy forcing?
2. [Post-event recovery heterogeneity test](climate/artifacts/questions/question_families_detailed.md#variant-004002-post-event-recovery-heterogeneity-test): After comparably strong polar-vortex disruptions, are rapid recovery, prolonged displacement, and recurrent disruption associated with distinct vertical circulation and forcing trajectories? *(held back before planning: the prior-art review resolved a close prior work — the family page states which, and what would distinguish this variant from it)*

Outcome: **Scientific rejection terminal** — closed without a plan, with the evidence that closed it. One variant had already been deferred on prior-art grounds before planning began.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](climate/artifacts/questions/question_families_detailed.md#family-004-extreme-polar-vortex-episodes-as-distinct-pathways-and-recovery-classes)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](climate/artifacts/families/extreme-event-lifecycle-heterogeneity/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](climate/artifacts/families/extreme-event-lifecycle-heterogeneity/dossier.md)

### 5. Propagating episodes versus coherent modes of vertical coupling

Vertical coupling may occur as temporally ordered propagation during discrete episodes, or as a continuously coherent mode spanning heights; either appearance could depend on the chosen representation.

1. [Event-first lagged coupling test](climate/artifacts/questions/question_families_detailed.md#variant-005001-event-first-lagged-coupling-test): When upper-stratospheric circulation or wave episodes are defined independently, do lower-stratospheric responses recur with consistent lagged vertical progression, and does that progression differ between ordinary and extreme episodes?
2. [Continuous-mode robustness test](climate/artifacts/questions/question_families_detailed.md#variant-005002-continuous-mode-robustness-test): Is apparent vertical coupling captured by a robust continuous circulation mode across heights, or does coherence dissolve when circulation, wave activity, reference-flow, and forcing perspectives are compared?

Outcome: **Plan developed (provisional)** — both variants reached independently reviewed plans.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](climate/artifacts/questions/question_families_detailed.md#family-005-propagating-episodes-versus-coherent-modes-of-vertical-coupling)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](climate/artifacts/families/vertical-coupling-representations/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](climate/artifacts/families/vertical-coupling-representations/dossier.md)

### 6. Historical change in state occupancy versus within-state dynamics

Historical circulation change may arise from redistribution among familiar dynamical states, alteration of the states themselves, or nonphysical inhomogeneity; aggregate change cannot distinguish these possibilities.

1. [State-population change decomposition](climate/artifacts/questions/question_families_detailed.md#variant-006001-state-population-change-decomposition): Across the multi-decade record, is historical change in polar-stratospheric circulation expressed primarily through altered occupancy, persistence, or transition pathways among recurrent states?
2. [Within-state structural and residual change test](climate/artifacts/questions/question_families_detailed.md#variant-006002-within-state-structural-and-residual-change-test): Within comparable circulation states, is multi-decade change congruent with the established state structure, or does it contain systematic residual changes in vertical organization, wave activity, or eddy forcing?

Outcome: **Mixed family** — one variant reached a reviewed plan; its sibling did not, and says why.

**[Explore both variants, their competing explanations, and what positive, negative, or null outcomes would mean](climate/artifacts/questions/question_families_detailed.md#family-006-historical-change-in-state-occupancy-versus-within-state-dynamics)** · [See the study plan at a glance, including proposal hypothesis versus inspected evidence](climate/artifacts/families/historical-change-in-dynamical-organization/dossier_detailed.md) · [Open the full plan itself — every control, estimand, and stated limit](climate/artifacts/families/historical-change-in-dynamical-organization/dossier.md)


## How to read an entry

Every entry ends with three links, richest first. The first goes to the scientific background,
competing explanations, the discriminating observation, and what positive, negative, or null
outcomes would mean. The second goes to the reading guide, which sets the proposal-stage hypothesis
beside what the planner actually found when it inspected the data — and it is the only place the
Question Owner and the independent reviewer appear in their own words. The third is the plan
itself: every control, estimand, diagnostic and stated limit, and the full reasoning for any
variant closed **during planning**. Neither file contains the other, so read both.

One exception is worth knowing before you click: a variant the prior-art review held back **never
reached planning**, so it appears in no dossier at all. Its reasoning — the priors that were
resolved and what would distinguish the question from them — lives in the first link. Five of the
thirty-six variants are in that state, and each is annotated inline where it appears above.

Four outcomes appear. Every other label you will meet — how deeply the planner inspected the
data, what kind of claim a design could support, how the supporting literature was read — is listed
with its permitted values in [reading the labels](../docs/LABELS.md).

Four outcomes appear:

- **Plan developed (provisional)** — both variants reached independently reviewed plans. Provisional
  means reviewed by an automated independent reviewer, for planning only, with no execution.
- **Mixed family** — one variant reached a plan and its sibling did not. The non-accepted sibling
  stays visible with its reason rather than disappearing.
- **Deferred on prior-art grounds** — a variant held back before planning because the review
  resolved a real prior work. The family page names the prior and what would distinguish the
  question from it.
- **Scientific rejection terminal** — the family closed without a plan. This is an outcome, not a
  failure: the dossier states what the dataset could not support and what would be needed instead.


## How Maieusis reached these questions

Each demo publishes its full chain: the source papers it read, the formation traces it built from
them, the reusable question-forming patterns it induced, the dataset narrative the proposal stage
was given, and every family dossier.

**A comparison worth making:** open a dataset narrative and then the matching dataset notes. The
narrative is what the proposing model was actually given, and it is deliberately coarse — it does
not carry the schema. The notes carry the exact shape. That gap is the design, and you can check it
on the climate and NLB demonstrations. The IBL demonstration publishes no separate dataset notes,
so that comparison is available for two of the three.

- Climate: [paper bank](climate/artifacts/paperbank/paperbank_summary.md) ·
  [patterns](climate/artifacts/paperbank/question_patterns_detailed.md) ·
  [dataset narrative](climate/artifacts/dataset/dataset_narrative.md) ·
  [dataset notes](climate/DATASET_NOTES.md)
- IBL: [paper bank](ibl/artifacts/paperbank/paperbank_summary.md) ·
  [patterns](ibl/artifacts/paperbank/question_patterns_detailed.md) ·
  [dataset narrative](ibl/artifacts/dataset/dataset_narrative.md)
- NLB: [paper bank](nlb/artifacts/paperbank/paperbank_summary.md) ·
  [patterns](nlb/artifacts/paperbank/question_patterns_detailed.md) ·
  [dataset narrative](nlb/artifacts/dataset/dataset_narrative.md) ·
  [dataset notes](nlb/DATASET_NOTES.md) ·
  [region-mapping check](nlb/verify_region_mapping.py)

---

[IBL](ibl/README.md) · [NLB](nlb/README.md) · [Climate](climate/README.md) ·
[Source papers](PAPER_SOURCES.md)
