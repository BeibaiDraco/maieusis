# Related-work positioning

This is a conceptual task-design audit, not a leaderboard. It compares systems
on two deliberately narrow questions:

- **X — explicit transfer of question-forming moves.** Does the method merely
  retrieve/recombine literature, or does it represent and transfer structured
  reasoning that turns scientific background and tension into a question?
- **Y — pre-execution target-dataset plan-or-reject.** Does a system merely use
  data, or does it inspect a concrete target dataset and decide whether a new
  question should be planned, revised, rejected, or deferred before full
  analysis?

Coordinates are visual jitter within broad bands, not measurements of quality,
accuracy, scientific impact, or overall capability. A lower position can
reflect a system solving a different task very well.

<p align="center">
  <img src="../assets/maieusis-positioning-map.png" width="100%" alt="Conceptual task-design map positioning Maieusis by explicit question-forming move transfer and pre-execution target-dataset plan-or-reject, alongside 17 related systems and benchmarks; this is not a performance ranking.">
</p>

<p align="center"><em>Coordinates are visual jitter within broad task-design bands, not measurements of quality or performance.</em></p>

The final image must be checked against
[`positioning_coordinates.csv`](positioning_coordinates.csv), the
[`PRIMARY_SOURCE_LOG.csv`](PRIMARY_SOURCE_LOG.csv), and the rationales below.

## One-by-one rationale

### [1] SciMON

SciMON retrieves prior-paper inspirations and iteratively improves idea
novelty. It is literature-conditioned ideation, but it does not expose a
reusable question-formation trace or a concrete target-dataset planning gate.

### [2] ResearchAgent

ResearchAgent combines a core paper, related literature, entity augmentation,
and reviewer feedback to generate a problem, method, and experiment design. It
is structured ideation without an explicit transferable question-forming move
or target-dataset answerability screen.

### [3] Scideator

Scideator extracts purpose, mechanism, and evaluation facets and recombines
them with novelty support. Those are explicit paper components, but not a
reconstructed transition from literature state and data opportunity to a
question.

### [4] HypER

HypER models literature-guided reasoning chains and generates provenance-backed
hypotheses. This places it high on structured reasoning transfer, while its task
does not independently plan/reject a question against a user-supplied target
dataset.

### [5] HypoGen / Sparks of Science

HypoGen uses structured paper supervision and explicit ideation traces such as
assumption, conceptual leap, and counterproposal. It transfers a paper-derived
reasoning pattern but does not perform pre-execution target-dataset planning.

### [6] CrossTrace

CrossTrace supplies step-level, grounded scientific reasoning traces and a
cross-domain discovery-pattern taxonomy. It is therefore near the explicit
trace-transfer end of X; its benchmark/training task does not add a concrete
target-dataset plan/reject branch.

### [7] Graphs of Research

Graphs of Research uses citation-evolution structures as supervision for idea
generation. This is explicit structural supervision, but not a reviewed
question-formation trace and not target-dataset planning.

### [8] Literature Meets Data / HypoRefine

This approach starts with a research question and refines hypotheses from
literature plus observational data. Data informs hypothesis utility, but the
system is not deciding whether a newly formed question should proceed.

### [9] HARPA

HARPA is literature-grounded and testability-driven, explores hypothesis design
spaces, and uses experimental feedback. That moves it above literature-only
ideation on Y, while remaining distinct from a question-level screen against a
specific target dataset before execution.

### [10] DiscoveryBench

DiscoveryBench provides a discovery goal and datasets, then evaluates
multi-step code-based hypothesis search and verification. The goal is supplied;
the benchmark evaluates solving it, not pre-execution question answerability.

### [11] DataVoyager

DataVoyager searches and verifies hypotheses in supplied data. The dataset is
the discovery substrate, not a later feasibility constraint on a transferred
literature-derived question.

### [12] AutoDiscovery

AutoDiscovery performs open-ended data-first exploration using Bayesian
surprise and experiment outcomes. Its selection mechanism is data/experiment
driven rather than transferred question-forming moves plus a separate planning
gate.

### [13] data-to-paper

data-to-paper begins from annotated data, raises hypotheses, designs plans,
writes analysis code, interprets outputs, and produces a traceable paper. It
includes planning and execution, but not the same literature-move transfer
followed by independent target-dataset plan/reject separation.

### [14] HLER

HLER audits/profiles a dataset before dataset-aware research-question
generation and applies a question-quality/feasibility loop before econometric
analysis. It is the closest prior work on the Y definition in this map, while
its published workflow does not expose the same isolated Owner–Planner
plan/reject/defer protocol or reviewed cross-paper formation-pattern transfer.

### [15] The AI Scientist

The AI Scientist generates ideas, writes code, runs experiments, writes papers,
and simulates review. It is highly automated; these axes do not measure
automation. Its workflow does not make a distinct pre-execution target-dataset
answerability object central.

### [16] Kosmos

Kosmos receives an objective and dataset and iterates literature search, data
analysis, hypothesis generation, and synthesis. Deep data use places it above
literature-only systems on Y, but its loop is discovery/execution rather than a
separate question-planning gate.

### [17] RQ-Bench

The 2026 RQ-Bench arXiv preprint studies limits of LLM-as-judge for scientific
novelty. Its benchmark reconstructs author-anchored research questions from
background, gaps, and contributions. It is directly relevant to question
reconstruction, but it is a benchmark without a target-dataset planning
branch.

## Maieusis

Maieusis is placed in the explicit-transfer / independent-plan-or-reject band
because its implemented task design:

1. reconstructs source-backed PaperCases and formation traces;
2. induces independently reviewed cross-paper question-formation patterns;
3. keeps those patterns separate from current topic evidence and a coarse
   DatasetNarrative during proposal; and
4. sends every shortlisted family to an isolated Question Owner–Dataset Planner
   branch that can plan, revise, reject, defer, or close incomplete before a
   full analysis.

This placement describes architecture, not benchmark superiority. The v0.1.0
demos test the workflow on IBL and NLB; broader cross-disciplinary evaluation is
ongoing.

## Interpretation rules

- The map displays Maieusis, not an earlier project name.
- The native image is 3840×2160; GitHub scales the same 16:9 asset responsively.
- A top-right position is not “better.” It means only that the task design
  explicitly implements both axes.
- Dataset use or experiment execution alone is not a pre-execution
  question-level plan-or-reject gate.
- Maieusis's position is an architectural classification, not a measured score.
- The reference map, BibTeX, coordinates, and source log remain adjacent to the
  rationale so readers can inspect every placement.

## Sources

- [Numbered reference map](REFERENCE_MAP.md)
- [BibTeX](references.bib)
- [Primary source log](PRIMARY_SOURCE_LOG.csv)
- [Coordinates](positioning_coordinates.csv)
- [Visual audit](VISUAL_AUDIT.md)
