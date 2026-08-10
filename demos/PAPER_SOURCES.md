# Source papers used by the demonstrations

[All demo questions](QUESTIONS.md) · [IBL](ibl/README.md) · [NLB](nlb/README.md) · [Climate](climate/README.md)

Maieusis does not distribute source PDFs. These tables identify exactly which papers each
demonstration read, so you can obtain lawful copies yourself and check what the published artifacts
were built from. A DOI link is an acquisition and metadata starting point, not a promise that
publisher full text is freely available.

Two cohorts, because the demonstrations used two.

## Neuroscience cohort — 12 papers, shared by the IBL and NLB demonstrations

The NLB run did not re-extract these. It imported the IBL run's reviewed paper half under a
receipt-bound check that verifies source digests, parser configuration, model identities, and
prompt versions all match, and it made no paper-stage provider call. One cohort genuinely serves
both demos.

Screen: 12 candidates in,
12 accepted PaperCases,
10 reviewed formation traces,
8 reviewed question-forming patterns.

The `pdf_sha256` column lets you verify you obtained the same file the run read.

| File | Paper | Authors | Year | Checksum (first 16) |
| --- | --- | --- | --- | --- |
| 1-s2.0-S0896627319300534-main.pdf | [Cortical Areas Interact through a Communication Subspace](https://doi.org/10.1016/j.neuron.2019.01.026) | João D. Semedo; Amin Zandvakili; Christian K. Machens; Byron M. Yu; Adam Kohn | 2019 | `a8e3bc43d4d592ae...` |
| 2024.08.30.610535v3.full.pdf | [Firing rate diversity lowers the dimension of population covariability in neuronal networks](https://doi.org/10.1101/2024.08.30.610535) | Gengshuo Tian; Ou Zhu; Vinay Shirhatti; Charles M. Greenspon; John E. Downey; David J. Freedman; Brent Doiron | 2024 | `4f5392320954ff98...` |
| ibl-s41586-025-09226-1.pdf | [Brain-wide representations of prior information in mouse decision-making](https://doi.org/10.1038/s41586-025-09226-1) | Charles Findling et al.; International Brain Laboratory | 2025 | `a014031cd0023347...` |
| nature12160.pdf | [The importance of mixed selectivity in complex cognitive tasks](https://doi.org/10.1038/nature12160) | Mattia Rigotti; Omri Barak; Melissa R. Warden; Xiao-Jing Wang; Nathaniel D. Daw; Earl K. Miller; Stefano Fusi | 2013 | `5e86b83a153d4cd3...` |
| nature12742.pdf | [Context-dependent computation by recurrent dynamics in prefrontal cortex](https://doi.org/10.1038/nature12742) | Valerio Mante; David Sussillo; Krishna V. Shenoy; William T. Newsome | 2013 | `7fbe1cee260ec93f...` |
| nn.3807.pdf | [Information-limiting correlations](https://doi.org/10.1038/nn.3807) | Rubén Moreno-Bote; Jeffrey M. Beck; Ingmar Kanitscheider; Xaq Pitkow; Peter E. Latham; Alexandre Pouget | 2014 | `8c019f3ed61e3e03...` |
| s41586-019-1346-5.pdf | [High-dimensional geometry of population responses in visual cortex](https://doi.org/10.1038/s41586-019-1346-5) | Carsen Stringer; Marius Pachitariu; Nicholas A. Steinmetz; Matteo Carandini; Kenneth D. Harris | 2019 | `95c774e6432cc6c2...` |
| s41586-021-04268-7.pdf | [Toroidal topology of population activity in grid cells](https://doi.org/10.1038/s41586-021-04268-7) | Richard J. Gardner; Erik Hermansen; Marius Pachitariu; Yoram Burak; Nils A. Baas; Benjamin Dunn; May-Britt Moser; Edvard I. Moser | 2022 | `ca9bdede2572d45e...` |
| s41586-025-09528-4 (1).pdf | [Transitions in dynamical regime and neural mode during perceptual decisions](https://doi.org/10.1038/s41586-025-09528-4) | Thomas Zhihao Luo; Timothy Doyeon Kim; Diksha Gupta; Adrian Bondy; Charles D. Kopec; Verity Alexander Elliott; Brian DePasquale; Carlos D. Brody | 2025 | `1dd19ac2906f4180...` |
| s41593-024-01758-5.pdf | [Semi-orthogonal subspaces for value mediate a binding and generalization trade-off](https://doi.org/10.1038/s41593-024-01758-5) | W. Jeffrey Johnston; Justin M. Fine; Seng Bum Michael Yoo; R. Becket Ebitz; Benjamin Y. Hayden | 2024 | `66defedae05ee2e1...` |
| science.aav7893.pdf | [Spontaneous behaviors drive multidimensional, brainwide activity](https://doi.org/10.1126/science.aav7893) | Carsen Stringer; Marius Pachitariu; Nicholas A. Steinmetz; Charu Bai Reddy; Matteo Carandini; Kenneth D. Harris | 2019 | `380ac73d0c1fd7bc...` |
| srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.pdf | [The structure of correlated variability reflects task-relevant information in sensory neurons](https://doi.org/10.1073/pnas.2523217123) | Ramanujan Srinath; Yunlong Xu; Douglas A. Ruff; Amy M. Ni; Brent Doiron; Marlene R. Cohen | 2026 | `afbade7cbdf5af16...` |

## Climate cohort — 20 papers

Screen: 20 candidates in,
13 accepted PaperCases,
7 excluded,
12 reviewed formation traces,
8 reviewed question-forming patterns.

**No checksums are published for this cohort, and that is deliberate.** Every one of these papers
was read through a text derivative produced locally, so a checksum taken from the run would not
match the file you download and would be a false verification aid. The neuroscience cohort above
does carry checksums because those papers were read directly.

Three of the seven exclusions were parse failures rather than scientific judgements:
`09-lorenz-hartmann-2001`, `12-charlton-polvani-2007`, and `19-rousi-et-al-2022` could not be
turned into the structured record the review stage requires. Two of those are canonical works in
the field. The demonstration lists them as excluded with that reason rather than quietly dropping
them, and the loss is a limitation of this run, not an assessment of those papers.

| File | Paper | Authors | Year |
| --- | --- | --- | --- |
| 01-wallace-gutzler-1981.pdf | [Teleconnections in the Geopotential Height Field during the Northern Hemisphere Winter](https://doi.org/10.1175/1520-0493(1981)109%3C0784:TITGHF%3E2.0.CO;2) | John M. Wallace; David S. Gutzler | 1981 |
| 02-barnston-livezey-1987.pdf | [Classification, Seasonality and Persistence of Low-Frequency Atmospheric Circulation Patterns](https://doi.org/10.1175/1520-0493(1987)115%3C1083:CSAPOL%3E2.0.CO;2) | Anthony G. Barnston; Robert E. Livezey | 1987 |
| 03-blackmon-et-al-1977.pdf | [An Observational Study of the Northern Hemisphere Wintertime Circulation](https://doi.org/10.1175/1520-0469(1977)034%3C1040:AOSOTN%3E2.0.CO;2) | Maurice L. Blackmon; John M. Wallace; Ngar-Cheung Lau; Steven L. Mullen | 1977 |
| 04-lau-1988.pdf | [Variability of the Observed Midlatitude Storm Tracks in Relation to Low-Frequency Changes in the Circulation Pattern](https://doi.org/10.1175/1520-0469(1988)045%3C2718:VOTOMS%3E2.0.CO;2) | Ngar-Cheung Lau | 1988 |
| 05-hoskins-hodges-2002.pdf | [New Perspectives on the Northern Hemisphere Winter Storm Tracks](https://doi.org/10.1175/1520-0469(2002)059%3C1041:NPOTNH%3E2.0.CO;2) | Brian J. Hoskins; Kevin I. Hodges | 2002 |
| 06-hurrell-1995.pdf | [Decadal Trends in the North Atlantic Oscillation: Regional Temperatures and Precipitation](https://doi.org/10.1126/science.269.5224.676) | James W. Hurrell | 1995 |
| 07-thompson-wallace-2000-part-i.pdf | [Annular Modes in the Extratropical Circulation. Part I: Month-to-Month Variability](https://doi.org/10.1175/1520-0442(2000)013%3C1000:AMITEC%3E2.0.CO;2) | David W. J. Thompson; John M. Wallace | 2000 |
| 08-thompson-wallace-hegerl-2000-part-ii.pdf | [Annular Modes in the Extratropical Circulation. Part II: Trends](https://doi.org/10.1175/1520-0442(2000)013%3C1018:AMITEC%3E2.0.CO;2) | David W. J. Thompson; John M. Wallace; Gabriele C. Hegerl | 2000 |
| 09-lorenz-hartmann-2001.pdf | [Eddy-Zonal Flow Feedback in the Southern Hemisphere](https://doi.org/10.1175/1520-0469(2001)058%3C3312:EZFFIT%3E2.0.CO;2) | David J. Lorenz; Dennis L. Hartmann | 2001 |
| 10-holton-tan-1980.pdf | [The Influence of the Equatorial Quasi-Biennial Oscillation on the Global Circulation at 50 mb](https://doi.org/10.1175/1520-0469(1980)037%3C2200:TIOTEQ%3E2.0.CO;2) | James R. Holton; Hsiu-Chi Tan | 1980 |
| 11-baldwin-dunkerton-2001.pdf | [Stratospheric Harbingers of Anomalous Weather Regimes](https://doi.org/10.1126/science.1063315) | Mark P. Baldwin; Timothy J. Dunkerton | 2001 |
| 12-charlton-polvani-2007.pdf | [A New Look at Stratospheric Sudden Warmings. Part I: Climatology and Modeling Benchmarks](https://doi.org/10.1175/JCLI3996.1) | Andrew J. Charlton; Lorenzo M. Polvani | 2007 |
| 13-wernli-schwierz-2006.pdf | [Surface Cyclones in the ERA-40 Dataset (1958-2001). Part I: Novel Identification Method and Global Climatology](https://doi.org/10.1175/JAS3766.1) | Heini Wernli; Cornelia Schwierz | 2006 |
| 14-zhu-newell-1998.pdf | [A Proposed Algorithm for Moisture Fluxes from Atmospheric Rivers](https://doi.org/10.1175/1520-0493(1998)126%3C0725:APAFMF%3E2.0.CO;2) | Yong Zhu; Reginald E. Newell | 1998 |
| 15-held-soden-2006.pdf | [Robust Responses of the Hydrological Cycle to Global Warming](https://doi.org/10.1175/JCLI3990.1) | Isaac M. Held; Brian J. Soden | 2006 |
| 16-taszarek-et-al-2021.pdf | [Global Climatology and Trends in Convective Environments from ERA5 and Rawinsonde Data](https://doi.org/10.1038/s41612-021-00190-x) | Mateusz Taszarek; John T. Allen; Mattia Marchio; Harold E. Brooks | 2021 |
| 17-wills-et-al-2022-author-manuscript.pdf | [Systematic Climate Model Biases in the Large-Scale Patterns of Recent Sea-Surface Temperature and Sea-Level Pressure Change](https://doi.org/10.1029/2022GL100011) | Robert C. J. Wills; Yue Dong; Cristian Proistosescu; Kyle C. Armour; David S. Battisti | 2022 |
| 18-thackeray-et-al-2022.pdf | [Constraining the Increased Frequency of Global Precipitation Extremes under Warming](https://doi.org/10.1038/s41558-022-01329-1) | Chad W. Thackeray; Alex Hall; Jesse Norris; Di Chen | 2022 |
| 19-rousi-et-al-2022.pdf | [Accelerated Western European Heatwave Trends Linked to More-Persistent Double Jets over Eurasia](https://doi.org/10.1038/s41467-022-31432-y) | Efi Rousi; Kai Kornhuber; Goratz Beobide-Arsuaga; Fei Luo; Dim Coumou | 2022 |
| 20-shaw-miyawaki-2024.pdf | [Fast Upper-Level Jet Stream Winds Get Faster under Climate Change](https://doi.org/10.1038/s41558-023-01884-1) | Tiffany A. Shaw; Osamu Miyawaki | 2024 |

## Author-affiliated sources — a disclosure

Two of the twelve neuroscience papers are by this project's own authors:

- **Tian et al. 2024** includes Brent Doiron.
- **Srinath et al. 2026** includes Yunlong Xu and Brent Doiron.

This matters because of what the neuroscience cohort was used for. Srinath et al. is a named source
for two of the eight reviewed question-forming patterns, and those patterns fed both the IBL and NLB
demonstrations. Maieusis argues that its patterns are earned from papers rather than asserted, so a
reader judging that argument should know the authors seeded part of the bank with their own work.

Nothing about this was hidden from the pipeline, and nothing about it is unusual — researchers
demonstrate on literature they know. But Maieusis does not screen for author affiliation, so
nothing in the system would have flagged it either. If you are reproducing this cohort, or judging
whether the pattern bank is independent of its builders, treat those two papers accordingly.

## Machine-readable manifests

- [`shared/paper_sources.yaml`](shared/paper_sources.yaml) — the neuroscience cohort
- [`climate/paper_sources.yaml`](climate/paper_sources.yaml) — the climate cohort

---

[All demo questions](QUESTIONS.md)
