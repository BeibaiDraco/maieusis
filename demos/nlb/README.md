# NLB demo: MC_Maze-S, two motor areas recorded at the same time

A rhesus macaque waits through a delay, then reaches to a target. Sometimes the path is clear and
the reach is straight; sometimes barriers stand in the way — a maze — and the reach has to curve
around them. Electrode arrays record spiking from two cortical areas simultaneously: primary motor
cortex (M1), which sits close to the movement itself, and dorsal premotor cortex (PMd), which is
more involved in preparing it. MC_Maze-S is a small, pinned slice of that experiment, published
through the Neural Latents Benchmark. See the
[benchmark paper](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/979d472a84804b9f647bc185a877a8b5-Abstract-round2.html)
and the [pinned DANDI dataset](https://doi.org/10.48324/dandi.000140/0.220113.0408).

**Simultaneity is the feature.** M1 and PMd are recorded in the same trials, in the same animal, at
the same moment — so you can ask whether the two areas express one shared organization or
complementary ones. That comparison falls apart if the two recordings come from different sessions.
Several of the questions below exist only because here they do not.

**The maze crosses trajectory with endpoint.** Nine maze geometries each appear in a straight
version and a curved version reaching the same target. Context can therefore be varied while the
endpoint is held fixed — the kind of matched contrast that is usually a design wish rather than
something already in the data.

**It is also small, and honest about it.** One monkey, one session, 142 sorted units (72 PMd,
70 M1), and 100 behaviour-labelled trials — 32 straight, 68 curved. That is the actual scale of the
public release, and it is what closed one of the twelve versions below.

**The IBL demonstration next door shares this run's twelve-paper source cohort, and the two are not
one run done twice.** IBL is wide: 139 mice, twelve laboratories, one task repeated, most of the
brain sampled shallowly. NLB is narrow and deep: one animal, two areas at the same instant,
endpoints crossed with context. This run did not re-read the twelve papers: it imported the paper
bank the anchored IBL run had already built from the identical cohort, bound by receipt digest,
parser configuration, model identity and prompt version. Re-extracting would have paid for the most
expensive stage twice to produce bytes that cannot differ. So what differs between the two
demonstrations is the
dataset description and nothing else. One cohort, genuinely, and two different demonstrations.

Read [the dataset notes](DATASET_NOTES.md) before the science. They carry the electrode and
unit-count detail that bounds every question here, and they make one claim that is easy to get
wrong: which brain region each unit belongs to. The official documentation says the leading digit
of a unit ID gives the region — 1 for PMd, 2 for M1 — and it also documents a conversion error: the
stored electrode indices for M1 units are wrong, and the correct electrode-table row is 96 further
down. Take the raw indices at face value and you will conclude the release is PMd-only. It is not.

**You do not have to take our word for any of that.**
[`verify_region_mapping.py`](verify_region_mapping.py) is 67 lines and does exactly one thing.
Point it at your own copy of DANDI 000140 version `0.220113.0408`:

```bash
python verify_region_mapping.py /path/to/000140   # needs h5py; opens the files read-only
```

It opens both NWB files, assigns every unit by the documented unit-ID rule, applies the +96
correction, and checks that the corrected electrode table agrees — expecting 72 PMd and 70 M1 in
the training file, 52 and 55 in the test file. If anything disagrees it exits with an error instead
of printing something reassuring. It runs no analysis and reports no scientific result. It checks a
piece of bookkeeping that everything downstream depends on, and it lets you catch us if we got it
wrong.

## Featured: does the movement run itself, or is it being driven?

Motor cortex during a reach is often described as an internally organized dynamical system: activity
set up during preparation, then evolving largely on its own. It can equally be described as
continuously shaped by inputs and feedback about the trajectory being executed. Both accounts fit
low-dimensional activity, and geometry alone does not separate them.

MC_Maze-S offers a contrast that bears on it. The same animal, in the same session, reaches straight
when there are no barriers and along a curved path when there are — so if the organization is
reusable across trajectory demands, it should survive the change, and if it is input-linked, it
should not.

Maieusis asked it two ways, as it asks everything twice — not a draft and a revision, but two ways
of asking one thing, built so they can fail differently:

1. **In preparation.** Does a reusable population organization coexist with curvature-selective
   specification of the path ahead, during the delay before movement begins?
2. **In execution.** During the movement itself, does the activity look autonomous-like, or
   input-linked to the trajectory being traced?

**Both reached plans and an independent reviewer accepted them.** Splitting preparation from
execution is what makes that possible: the two periods can disagree, and a design that pooled them
would report whichever dominated. Each version's reading guide carries a *proposal hypothesis versus
inspected evidence* section, which sets what the proposal stage assumed the recording offered beside
what the planner actually found in it; the planning record carries the controls, the estimands and
the stated limits. Neither contains the other.

## And one family was closed by counting

It is worth two minutes, because it is the clearest case on this page of the dataset answering back.

A sibling question asks whether neural trajectory geometry carries path-level structure beyond what
simpler kinematics explain — a reasonable question, and one the literature asks. The planner opened
the files before answering.

What it found: 100 training trials, nine maze layouts crossed with three versions, giving
**twenty-seven unique conditions**. Twenty-one of them hold four trials. Four hold three. Two hold
two. The planner wrote the consequence down as a limitation in its own record — *"only ~2-4 trials
per condition, which severely limits any per-condition or repeated-execution estimation"* — and
closed the family rather than proposing a design that could not be estimated from what is there.

It also recorded, from the dataset's own notes, that M1 unit identifiers need a documented +96
electrode-row correction and that raw electrode indices must not be used alone to conclude the
population is PMd-only. That is the kind of detail that decides whether a regional claim means
anything, and it is not visible from a dataset description.

The dossier records the outcome as a scientific rejection and does not itself say which of the
things the planner found was decisive. The counting is the most striking thing in its record, and it
is the kind of constraint a dataset description would never have surfaced — but read the family's
own page before concluding that one number closed it.

**This is a scientific answer, not a crash.** The run names what it found instead of substituting a
proxy that would have answered a different question.
[Read the family and its closure](artifacts/families/trajectory-geometry-alternatives/dossier.md).

## The six questions, and what happened to each

<!-- generated: six questions -- scripts/render_demo_gallery.py -->

**Four of the six reached plans for both versions**, and every other family is below with what happened to each — a closed version stays on the page with the reason it closed. Five of the six questions produced plans at all.

### 1. Context-dependent balance of autonomous and input-linked motor dynamics

*Family 001: Context-dependent balance of autonomous and input-linked motor dynamics*

Low-dimensional reach dynamics can be consistent with internally organized evolution, but trajectory constraints and behavioral feedback may also shape the observed activity. Straight and curved reaches offer a proposal-stage contrast without making either account uniquely identifiable from geometry alone.

1. [**Preparation-focused test of shared versus path-specific organization**](artifacts/questions/question_families_detailed.md#variant-001001-preparation-focused-test-of-shared-versus-path-specific-organization) — During movement preparation, does population-state organization generalize between straight and curved reaches, or does curvature demand produce distinct preparatory organization?
2. [**Execution-focused test of autonomous-like versus input-linked dynamics**](artifacts/questions/question_families_detailed.md#variant-001002-execution-focused-test-of-autonomous-like-versus-input-linked-dynamics) — During reach execution, are curved-path population dynamics disproportionately associated with ongoing behavioral input relative to straight-path dynamics?

**Outcome: Plan developed (provisional).** Both versions got a plan.

[The question in full](artifacts/questions/question_families_detailed.md#family-001-context-dependent-balance-of-autonomous-and-input-linked-motor-dynamics) ·
[full planning record](artifacts/families/context-dependent-motor-dynamics/dossier.md)

### 2. Stable versus task-specific geometry across motor contexts

*Family 002: Stable versus task-specific geometry across motor contexts*

Prior literature supports both preserved motor manifolds and task-specific dynamics. The described straight/curved task and PMd/M1 recordings motivate distinct tests of condition invariance and regional representational scope.

1. [**Within-region test of preserved, transformed, or reorganized geometry**](artifacts/questions/question_families_detailed.md#variant-002001-within-region-test-of-preserved-transformed-or-reorganized-geometry) — Is the population geometry used for straight reaches preserved, smoothly transformed, or reorganized for curved reaches within a cortical region?
2. [**Cross-region test of broad versus specialized trajectory-context scope**](artifacts/questions/question_families_detailed.md#variant-002002-cross-region-test-of-broad-versus-specialized-trajectory-context-scope) — Do PMd and M1 differ in whether their population organization spans both straight and curved trajectory contexts or is specialized by trajectory type?

**Outcome: Plan developed (provisional).** Both versions got a plan.

[The question in full](artifacts/questions/question_families_detailed.md#family-002-stable-versus-task-specific-geometry-across-motor-contexts) ·
[full planning record](artifacts/families/stable-versus-specific-geometry/dossier.md)

### 3. Functional structure of preparatory population variability

*Family 003: Functional structure of preparatory population variability*

Preparatory variability may be generic noise that contracts before movement, or its orientation may contain structured information about upcoming trajectories and behavioral readiness.

1. [**Geometric test of trajectory-selective preparatory stabilization**](artifacts/questions/question_families_detailed.md#variant-003001-geometric-test-of-trajectory-selective-preparatory-stabilization) — Does declining preparatory variability preferentially contract along dimensions associated with the upcoming reach trajectory, or does it decline without selective trajectory alignment?
2. [**Predictive test of the behavioral meaning of preparatory variability**](artifacts/questions/question_families_detailed.md#variant-003002-predictive-test-of-the-behavioral-meaning-of-preparatory-variability) — Is trial-to-trial preparatory variability associated with movement readiness or trajectory quality after accounting for planned path and concurrent behavioral state proxies?

**Outcome: Plan developed (provisional).** Both versions got a plan.

[The question in full](artifacts/questions/question_families_detailed.md#family-003-functional-structure-of-preparatory-population-variability) ·
[full planning record](artifacts/families/preparatory-variability-structure/dossier.md)

### 4. Generalizable readout across trajectory contexts and cortical populations

*Family 004: Generalizable readout across trajectory contexts and cortical populations*

A readout may succeed because it captures reusable motor structure or because it exploits context- or population-specific associations. Generalization failures can therefore reveal scientific boundaries, but they must not be treated as proof of distinct mechanisms.

1. [**Cross-trajectory generalization test**](artifacts/questions/question_families_detailed.md#variant-004001-cross-trajectory-generalization-test) — Does a neural representation associated with reach trajectory generalize between straight and curved paths, and what does asymmetric transfer imply about shared versus context-specific motor structure?
2. [**Cross-region compatibility and transfer test**](artifacts/questions/question_families_detailed.md#variant-004002-cross-region-compatibility-and-transfer-test) — Are trajectory-related population organizations in PMd and M1 related by a shared readout or transformation, or are their predictive relationships region-specific?

**Outcome: Plan developed (provisional).** Both versions got a plan.

[The question in full](artifacts/questions/question_families_detailed.md#family-004-generalizable-readout-across-trajectory-contexts-and-cortical-populations) ·
[full planning record](artifacts/families/generalizable-motor-readout/dossier.md)

### 5. Localized versus distributed organization of reach planning and execution

*Family 005: Localized versus distributed organization of reach planning and execution*

PMd and M1 may make distinguishable contributions to reaching, but observed regional differences could reflect distributed computation, temporal staging, trajectory complexity, or measurement sensitivity rather than strict localization.

1. [**Spatial-scope test of trajectory-complexity structure**](artifacts/questions/question_families_detailed.md#variant-005001-spatial-scope-test-of-trajectory-complexity-structure) — Is population structure associated with curved-path demand concentrated in PMd, concentrated in M1, or distributed across both regions?
2. [**Temporal-scope test of regional preparation-to-execution organization**](artifacts/questions/question_families_detailed.md#variant-005002-temporal-scope-test-of-regional-preparation-to-execution-organization) — Do PMd and M1 exhibit a shared preparation-to-execution population transformation, sequentially differentiated transformations, or region-specific temporal organizations?

**Outcome: Deferred on prior-art grounds.** One version got a plan; the second never reached planning, because prior-art review stopped it. Its disposition line on the question page says which finding stopped it: a close published prior it would have to be distinguished from, or a search that could not retrieve enough evidence to judge it.

[The question in full](artifacts/questions/question_families_detailed.md#family-005-localized-versus-distributed-organization-of-reach-planning-and-execution) ·
[what prior-art review found](artifacts/questions/prior_art.md) ·
[full planning record](artifacts/families/pmd-m1-distributed-computation/dossier.md)

### 6. Neural trajectory geometry versus richer behavioral explanations

*Family 006: Neural trajectory geometry versus richer behavioral explanations*

Population activity may encode or dynamically organize path-level structure, but apparent trajectory representations can also arise from hand, cursor, eye, timing, or other correlated behavioral variables. Richer covariates can adjudicate these accounts without being treated merely as nuisance.

1. [**Prospective test of path-level geometry beyond pre-movement state proxies**](artifacts/questions/question_families_detailed.md#variant-006001-prospective-test-of-path-level-geometry-beyond-pre-movement-state-proxies) — Before movement, does population geometry distinguish intended curved versus straight path structure beyond endpoint and immediately observable hand or eye state?
2. [**Execution-period alternative-explanation test using richer behavior**](artifacts/questions/question_families_detailed.md#variant-006002-execution-period-alternative-explanation-test-using-richer-behavior) — During movement, does population activity contain curved-path-specific structure beyond jointly measured hand, cursor, eye, and velocity-related behavior, or is the apparent neural distinction explained by those richer behavioral variables?

**Outcome: Scientific rejection terminal.** No version produced a plan; the run names what was missing rather than substituting a proxy for it.

[The question in full](artifacts/questions/question_families_detailed.md#family-006-neural-trajectory-geometry-versus-richer-behavioral-explanations) ·
[full planning record](artifacts/families/trajectory-geometry-alternatives/dossier.md)

<!-- /generated -->

## Follow this run from its inputs

Or continue to the [complete gallery](../ALL_QUESTIONS.md) for every question across all four
demonstrations.

1. [The source papers and how they were screened](../PAPER_SOURCES.md)
2. [The paper bank](artifacts/paperbank/paperbank_summary.md) and the
   [reconstructions](artifacts/paperbank/) built from the accepted papers — evidence-bound accounts
   of how each one moved from an open problem to its question
3. [The reusable question-forming patterns](artifacts/paperbank/question_patterns_detailed.md)
   induced across those
4. [The dataset narrative](artifacts/dataset/dataset_narrative.md) — the coarse, source-backed
   description the proposal stage was given. Set it beside [the dataset
   notes](DATASET_NOTES.md): the gap between them is the design, not an oversight
5. [Topic evidence](artifacts/literature/topic_evidence_summary.md) and
   [research scope](artifacts/literature/research_scope.md)
6. [All six questions in full](artifacts/questions/question_families_detailed.md), then each
   question's planning record

Source PDFs, raw dataset files, model transcripts, credentials, and private recovery records are
not distributed.

## What produced these artifacts

Run `20260823T124544Z-1acbc808`, executed by the published package itself. This is the first release in which that
sentence is true: the wheel this repository publishes is the wheel that produced these pages, and
the qualification receipt binds the two. Earlier demonstrations disclosed the gap because the
process had no way to close it.

The evidence supporting these questions is visibly draft and largely abstract-only, and the pages
say so where it applies. Prior-art review ran on every version within a recorded scope. No question
is claimed to be novel, no plan is a result, and nothing here was ever run.

---

[All demo questions](../ALL_QUESTIONS.md) · [Source papers](../PAPER_SOURCES.md) ·
[Documentation home](../../docs/INDEX.md)
