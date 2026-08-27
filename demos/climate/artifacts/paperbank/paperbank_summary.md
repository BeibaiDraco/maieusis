# PaperBank — automated review summary

- Batch outcome: `accepted`
- Accepted (automated review passed): 18
- Excluded: 2

## Accepted papers

- Wallace and Gutzler, “Teleconnections in the Geopotential Height Field during the Northern Hemisphere Winter” (1981) — `ai_reviewed`
- Anthony G. Barnston and Robert E. Livezey (1987), "Classification, Seasonality and Persistence of Low-Frequency Atmospheric Circulation Patterns" — `ai_reviewed`
- Maurice L. Blackmon, John M. Wallace, Ngar-Cheung Lau, and Steven L. Mullen (1977), “An Observational Study of the Northern Hemisphere Wintertime Circulation” — `ai_reviewed`
- New Perspectives on the Northern Hemisphere Winter Storm Tracks — `ai_reviewed`
- Decadal Trends in the North Atlantic Oscillation: Regional Temperatures and Precipitation — `ai_reviewed`
- Thompson and Wallace (2000), “Annular Modes in the Extratropical Circulation. Part I: Month-to-Month Variability” — `ai_reviewed`
- Thompson, D. W. J., J. M. Wallace, and G. C. Hegerl (2000), Annular Modes in the Extratropical Circulation. Part II: Trends. — `ai_reviewed`
- David J. Lorenz and Dennis L. Hartmann, “Eddy-Zonal Flow Feedback in the Southern Hemisphere,” Journal of the Atmospheric Sciences — `ai_reviewed`
- James R. Holton and Hsiu-Chi Tan (1980), “The Influence of the Equatorial Quasi-Biennial Oscillation on the Global Circulation at 50 mb” — `ai_reviewed`
- Mark P. Baldwin and Timothy J. Dunkerton, “Stratospheric Harbingers of Anomalous Weather Regimes” — `ai_reviewed`
- Andrew Charlton-Perez and Lorenzo M. Polvani (2007), “A New Look at Stratospheric Sudden Warmings. Part I: Climatology and Modeling Benchmarks” — `ai_reviewed`
- A Proposed Algorithm for Moisture Fluxes from Atmospheric Rivers — Yong Zhu and Reginald E. Newell — `ai_reviewed`
- Held, I. M., and B. J. Soden, 2006: Robust Responses of the Hydrological Cycle to Global Warming. Journal of Climate, 19, 5686–5699. — `ai_reviewed`
- Global climatology and trends in convective environments from ERA5 and rawinsonde data — `ai_reviewed`
- Wills, Dong, Proistosescu, Armour, and Battisti (2022), "Systematic climate model biases in the large-scale pattern of recent sea-surface temperature and sea-level pressure change" — `ai_reviewed`
- Thackeray, Hall, Norris, and Chen (2022), “Constraining the increased frequency of global precipitation extremes under warming.” — `ai_reviewed`
- Rousi et al. (2022), “Accelerated western European heatwave trends linked to more-persistent double jets over Eurasia” — `ai_reviewed`
- Tiffany A. Shaw & Osamu Miyawaki, “Fast upper-level jet stream winds get faster under climate change” — `ai_reviewed`

## Excluded papers (honestly listed)

- 04-lau-1988 — citation_reject — Two of the three selected citations (this citation rank1, this citation rank2) are well supported by their cited contexts: the Blackmon-et-al climatology reference matches the introduction/discussion passages about subweekly spectral timescales, and the Blackmon 1976 methodological reference matches the medium-pass filter passage. However, the third selection, this citation (rank 3, 'supporting', framing the passive-vs-active eddy tension), has an empty evidence_context_ids list — no entry in citation_contexts ties this work to any passage in the paper. Its detailed rationale instead appears to be drawn from the malformed 'raw_reference' field of the resolved record, which itself reads as garbled self-referential paper prose ('In computing the eddy vorticity fluxes...our calculations') rather than a genuine external reference or documented citation context. This selection fabricates participation in the question-formation process without supporting evidence, so the selection set cannot be accepted as-is.
- 13-wernli-schwierz-2006 — fidelity_revise_budget_exhausted — the bounded revision round ran and the reviewer still asked for changes; The extracted question, dataset cue, and knowledge-state/question-design fields are faithful to the source paper (Wernli & Schwierz 2006): the central question, ERA-40 dataset details, and framing of prior nontracking/tracking climatology tensions all trace cleanly to the cited spans and match the paper's actual argument. However, the PaperCase's key_cited_work_ids field is empty, even though the case's own knowledge_state.nearest_prior_work and question_design sections explicitly name specific prior works (Sickmöller et al. 2000, Hoskins and Hodges 2002 [HH02], Sinclair 1995/1997, Simmonds and Keay 2000a/2000b, Petterssen 1956, Whittaker and Horn 1984) that are documented in the paper's own citation_contexts as background, precedent, and comparison points central to the paper's motivation and validation. Because no citations were actually linked, the key-citation criterion cannot be satisfied — this is an incompleteness gap, not a fabrication, and is straightforwardly fixable by mapping the already-named prior works to their corresponding cited_work_ids (e.g., this citation, this citation, this citation, this citation, this citation, this citation, this citation, this citation) and including them in key_cited_work_ids with supporting context. The upstream importance_selection also failed (model_failed status), which likely explains the omission. No hallucinated question, dataset cue, or citation was found; the missing-abstract situation (12/55 works) is not silently mishandled here because no citation resolution claims are made at all.; still required: Populate key_cited_work_ids by mapping the prior works already named in knowledge_state.nearest_prior_work and question_design (e.g., Sickmöller et al. 2000 -> this citation; Hoskins and Hodges 2002 [HH02] -> this citation; Sinclair 1995 -> this citation; Sinclair 1997 -> this citation; Simmonds and Keay 2000a -> this citation; Simmonds and Keay 2000b -> this citation; Petterssen 1956 -> this citation; Whittaker and Horn 1984 -> this citation) to their corresponding citation contexts.; still required: Re-run the citation-importance selection (previously model_failed) so that a properly ranked key-citation list backs the PaperCase before it proceeds downstream.

## If this looks wrong

This is a diagnostic summary, not an approval. Add/replace PDFs or fix a parse and re-run; the automated gate re-judges each paper independently.
