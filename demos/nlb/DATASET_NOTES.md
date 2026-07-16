# MC_Maze-S dataset note: identifying M1 and PMd units

This note records a documented conversion caveat that must be handled before
using MC_Maze-S to compare primary motor cortex (M1) with dorsal premotor cortex
(PMd). It is a data-interpretation requirement, not a scientific result.

## Dataset and study references

- **Dataset:** Churchland, Mark; Kaufman, Matthew (2022), *MC_Maze_Small:
  macaque primary motor and dorsal premotor cortex spiking activity during
  delayed reaching*, [DANDI:000140, version
  0.220113.0408](https://doi.org/10.48324/dandi.000140/0.220113.0408).
- **Benchmark:** Pei et al. (2021), [*Neural Latents Benchmark ’21: Evaluating
  latent variable models of neural population
  activity*](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/979d472a84804b9f647bc185a877a8b5-Abstract-round2.html).
- **Original studies:** Kaufman et al. (2010), [*Cortical preparatory activity:
  representation of movement or first cog in a dynamical
  machine?*](https://doi.org/10.1016/j.neuron.2010.09.015); Churchland et al.
  (2012), [*Neural population dynamics during
  reaching*](https://doi.org/10.1038/nature11129).
- **Official dataset documentation:** [Neural Latents Benchmark dataset
  page](https://neurallatents.github.io/datasets.html).

The DANDI release contains sorted-unit spiking times and behavioral data from
one rhesus macaque performing delayed center-out reaches around barriers. It
includes straight and curved reaches, recordings from M1 and PMd, and cursor,
hand, eye, and hand-velocity measurements. The scaled release is limited to 100
training and 100 test trials.

## The region-index conversion caveat

The official NLB dataset page states that the first digit of each unit ID is the
region indicator for the MC_Maze releases:

- leading `1`: PMd;
- leading `2`: M1.

It also documents a conversion error: the stored electrode indices for M1 units
are incorrect, and the correct electrode-table row is obtained by adding 96.
Raw `units/electrodes` values therefore must not be used alone to conclude that
the released sorted-unit population is PMd-only.

## Verification of the pinned files

A bounded metadata check of DANDI version `0.220113.0408` found:

| split | PMd units | M1 units | total units |
| --- | ---: | ---: | ---: |
| train | 72 | 70 | 142 |
| test held-in | 52 | 55 | 107 |

The raw electrode table has 96 PMd and 96 M1 rows. Before correction, all stored
unit electrode indices fall in the first 96 rows. After applying the documented
unit-ID rule and the M1 `+96` correction, both regions are represented.

These counts verify metadata handling for the pinned files. They do not
establish trial-level coverage, unit quality equivalence, a regional difference,
or any other scientific outcome.

## Required handling for this dataset

Before a region-specific plan proceeds, the Dataset Planner must:

1. assign units using the documented unit-ID convention;
2. apply and verify the M1 `+96` electrode-row correction;
3. reconcile unit IDs, electrode metadata, DANDI metadata, and the official NLB
   documentation;
4. keep any unresolved disagreement visible rather than inferring that M1 units
   are absent; and
5. verify usable trial counts, event timing, and region-specific coverage before
   claiming feasibility.

The combined M1+PMd population may support planning, with region-stratified
sensitivity analyses subject to the ordinary limitations of a small,
single-subject release. The public helper
[`verify_region_mapping.py`](verify_region_mapping.py) performs only the bounded
metadata check described here; it does not execute a scientific analysis.
