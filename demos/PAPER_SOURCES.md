# Source papers used in the public demos

The International Brain Laboratory (IBL) Brain-Wide Map and Neural Latents
Benchmark (NLB) MC_Maze-S demos use the same 12-paper source cohort. The IBL
run built the reviewed PaperBank; the NLB run reused those paper-derived
products through a receipt-bound import. Maieusis does not copy conclusions
from these papers. It extracts source-bound PaperCases, reconstructs reviewed
question-forming moves, and abstracts patterns that can inspire new questions
for a different target dataset.

This cohort belongs only to these demonstrations. A project in another field
should supply its own lawfully obtained, field-relevant source papers.

## Obtain the papers lawfully

The repository does **not** distribute the source PDFs. Each DOI below is a
publisher or metadata starting point, not a promise that the full text is free
to download. Obtain a lawful copy through an open-access link, the publisher,
your institution, or the authors, and comply with the applicable license and
terms of access.

To reproduce the exact demos, preserve the filename shown below. After
download, compare each file with the SHA-256 value in the
[machine-readable source manifest](shared/paper_sources.yaml). The hash verifies
that you have the same input bytes used for the published demo; it does not grant
permission to redistribute the PDF.

| # | Source | Year | Filename expected by the frozen profile |
| ---: | --- | ---: | --- |
| 1 | [Cortical Areas Interact through a Communication Subspace](https://doi.org/10.1016/j.neuron.2019.01.026) | 2019 | `1-s2.0-S0896627319300534-main.pdf` |
| 2 | [Firing rate diversity lowers the dimension of population covariability in neuronal networks](https://doi.org/10.1101/2024.08.30.610535) | 2024 | `2024.08.30.610535v3.full.pdf` |
| 3 | [Brain-wide representations of prior information in mouse decision-making](https://doi.org/10.1038/s41586-025-09226-1) | 2025 | `ibl-s41586-025-09226-1.pdf` |
| 4 | [The importance of mixed selectivity in complex cognitive tasks](https://doi.org/10.1038/nature12160) | 2013 | `nature12160.pdf` |
| 5 | [Context-dependent computation by recurrent dynamics in prefrontal cortex](https://doi.org/10.1038/nature12742) | 2013 | `nature12742.pdf` |
| 6 | [Information-limiting correlations](https://doi.org/10.1038/nn.3807) | 2014 | `nn.3807.pdf` |
| 7 | [High-dimensional geometry of population responses in visual cortex](https://doi.org/10.1038/s41586-019-1346-5) | 2019 | `s41586-019-1346-5.pdf` |
| 8 | [Toroidal topology of population activity in grid cells](https://doi.org/10.1038/s41586-021-04268-7) | 2022 | `s41586-021-04268-7.pdf` |
| 9 | [Transitions in dynamical regime and neural mode during perceptual decisions](https://doi.org/10.1038/s41586-025-09528-4) | 2025 | `s41586-025-09528-4 (1).pdf` |
| 10 | [Semi-orthogonal subspaces for value mediate a binding and generalization trade-off](https://doi.org/10.1038/s41593-024-01758-5) | 2024 | `s41593-024-01758-5.pdf` |
| 11 | [Spontaneous behaviors drive multidimensional, brainwide activity](https://doi.org/10.1126/science.aav7893) | 2019 | `science.aav7893.pdf` |
| 12 | [The structure of correlated variability reflects task-relevant information in sensory neurons](https://doi.org/10.1073/pnas.2523217123) | 2026 | `srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.pdf` |

## Verify the local cohort

Place the PDFs as direct children of a private inbox, then compute their hashes:

```bash
shasum -a 256 /path/to/papers/inbox/*.pdf       # macOS
# sha256sum /path/to/papers/inbox/*.pdf         # Linux
```

Compare the output with `papers[].pdf_sha256` in
[`shared/paper_sources.yaml`](shared/paper_sources.yaml). Never commit the PDF
inbox to git.

The demo run began with all 12 candidates. Eleven produced accepted
PaperCases, ten produced reviewed question-formation traces, and the reviewed
set yielded eight question-formation patterns. The paper *Semi-orthogonal
subspaces for value mediate a binding and generalization trade-off* remains
visible as an input candidate, but its citation context could not be verified
for this run, so it was not included in the accepted/importable PaperBank. That
is a provenance decision about this particular extraction, not a judgment about
the paper's scientific quality.

Continue to the [IBL reproduction guide](ibl/README.md) or, after completing
IBL, the [IBL → NLB reproduction guide](nlb/README.md). To browse the scientific
outputs first, open the [complete question gallery](QUESTIONS.md).
