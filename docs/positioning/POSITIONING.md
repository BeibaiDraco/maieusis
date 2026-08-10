# Where Maieusis fits among related systems

Maieusis addresses a specific upstream problem: developing scientifically
motivated questions and determining whether a real target dataset can support
them before a full analysis begins. The map below compares related systems on
two deliberately narrow aspects of that task.

- **X — explicit transfer of question-forming moves.** Does the published
  method represent and transfer structured reasoning that connects scientific
  background or tension to a new question, rather than only retrieving or
  recombining literature?
- **Y — pre-execution target-dataset plan-or-reject.** Does the published
  method inspect a concrete target dataset and decide whether a newly developed
  question should be planned, revised, rejected, or deferred before full
  analysis?

These axes do not measure scientific quality, accuracy, impact, autonomy, or
overall capability. A system can sit lower on either axis because it solves a
different task very well.

<p align="center">
  <img src="../assets/maieusis-positioning-map.png" width="100%" alt="Conceptual task-design map positioning Maieusis by explicit question-forming move transfer and pre-execution target-dataset plan-or-reject, alongside 17 related systems and benchmarks; this is not a performance ranking.">
</p>

<p align="center"><em>An author-interpreted task-design map, not a performance ranking. Coordinates are visual jitter within broad qualitative bands.</em></p>

## What Maieusis adds

Maieusis combines two operations that are often treated separately in the
systems compared here. It first learns from prior science without copying prior
conclusions, then asks whether a new question survives contact with the user's
actual dataset.

Its implemented workflow:

1. reconstructs source-backed PaperCases and question-formation traces;
2. induces independently reviewed, cross-paper question-forming patterns;
3. keeps those patterns separate from current topic evidence and a coarse
   DatasetNarrative while new QuestionFamilies are proposed; and
4. sends every shortlisted family to an isolated Question Owner–Dataset
   Planner branch that can plan, revise, reject, defer, or close with a warning
   before full scientific analysis.

The public demonstrations exercise this workflow on the International Brain Laboratory (IBL)
Brain-Wide Map, the Neural Latents Benchmark (NLB) MC_Maze-S dataset, and an ERA5-derived
stratospheric record -- two fields, with no part of the system adapted for either. Cross-
disciplinary evaluation continues, so the placement describes the implemented task design rather
than benchmark superiority.

## How to read the map

- A top-right position is not “better”; it indicates only that the cited
  workflow explicitly implements more of these two task-design features.
- Using a dataset, running experiments, or automating an end-to-end research
  loop is not by itself a pre-execution question-level plan-or-reject gate.
- Absence statements are limited to the workflow described in the cited
  publication; they are not claims about unpublished features or later work.
- Coordinates distinguish broad qualitative bands and should not be read as
  numerical scores or measured distances.

## Evidence and references

Read the [evidence notes for all 17 placements](REFERENCE_MAP.md), including
publication status and the rationale for each comparison. Machine-readable
supporting material is available as [BibTeX](references.bib), a
[primary-source log](PRIMARY_SOURCE_LOG.csv), and the
[qualitative plotting coordinates](positioning_coordinates.csv).
