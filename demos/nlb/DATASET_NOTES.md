# MC_Maze-S source-backed dataset notes

This file is an input document for the Maieusis NLB demo, not a portable-core
assumption. It records a release-specific conversion caveat that a dataset
planner must reconcile before making M1-versus-PMd feasibility claims.

## Pinned dataset identity

- DANDI:000140, MC_Maze_Small.
- Published version: `0.220113.0408`.
- DOI: <https://doi.org/10.48324/dandi.000140/0.220113.0408>.
- Official NLB dataset page: <https://neurallatents.github.io/datasets.html>.

The DANDI description states that the recording used arrays in primary motor
cortex (M1) and dorsal premotor cortex (PMd), and that this scaled release is
limited to 100 train and 100 test trials.

## Known region-index conversion caveat

The official NLB dataset page states that the first digit of each unit ID is the
authoritative region indicator for the MC_Maze releases:

- leading `1`: PMd;
- leading `2`: M1.

It also documents a conversion error: the stored electrode indices for M1 units
are incorrect and the correct electrode-table row is obtained by adding 96.
Therefore, raw `units/electrodes` values must not be used alone to conclude that
the released sorted-unit population is PMd-only.

For the pinned local files used during release preparation, a bounded metadata
inspection found:

| split | PMd units | M1 units | total units |
| --- | ---: | ---: | ---: |
| train | 72 | 70 | 142 |
| test held-in | 52 | 55 | 107 |

The raw electrode table has 96 PMd and 96 M1 rows. Before correction, all stored
unit electrode indices fall in the first 96 rows; after applying the documented
unit-ID rule and M1 `+96` correction, both regions are represented.

## Planning rule

A planner may use the combined within-session M1+PMd population and may propose
region-stratified sensitivity analyses, subject to ordinary sample-size and
single-session limitations. A terminal that claims M1 units are absent must not
rely only on the uncorrected electrode indices. Any disagreement among unit IDs,
electrode metadata, DANDI metadata, or the official NLB caveat must remain visible
and be reconciled before a scientific rejection is issued.

This note does not authorize scientific analysis, confirmation access, or the
downstream execution bridge.
