# Changelog

Maieusis follows semantic versioning. This file records public releases.

## 0.1.1 — Maintenance (2026-08-07)

A maintenance release. It corrects how evidence authority is earned, adds a
prior-art review, defines how an agent-driven run is carried through failure,
and hardens the run machinery.

**An existing `0.1.0` project file loads unchanged and behaves as before.** The
schema defaults did not move, so a configuration that does not mention prior-art
review still does not perform one and still constructs no web-search provider.

**A newly scaffolded project is different.** `maieusis init` now writes the
profile the published demonstrations used, and that profile enables prior-art
review and its bounded web-search lane. A first run therefore makes paid
third-party search calls. `maieusis check` discloses the tool-fee reservation
and its ceiling before anything is spent, and it makes no paid call itself.

### Corrected — please read if you used 0.1.0 output

**Evidence could be labelled as open-access full text when it was not.** In
`0.1.0`, a reachable URL could by itself qualify a source as an open-access
full-text location. A reader could therefore see a claim presented with more
authority than the underlying evidence had earned. No fabricated source was
introduced, and no analysis was executed — the defect is one of labelling
strength, not invented content.

`0.1.1` separates the assertions that were previously conflated: metadata
existence, an exact provider rights assertion, a response-bound retrieval
attempt, and permission to persist are now recorded independently, and full-text
authority requires the rights assertion plus the retrieval receipt. Lawful
abstracts and snippets remain usable, honestly labelled as abstract-only.

**What to do:** re-derive any `0.1.0` artifact whose conclusion depended on a
source presented as full text. Under `0.1.1` some evidence that previously read
as full text will honestly read as abstract-only; that is the correction working,
not a regression. `0.1.0` remains installable and its release record is
unchanged.

### Added

- **A defined shepherd mode for live runs.** Maieusis is agent-operated: a run is
  driven by a coding-agent session rather than by a person watching a terminal,
  and a real run on real data can stop. `0.1.1` states what that session — the
  run's shepherd — may and may not do when it does. Repair is allowed, bounded,
  and disclosed; the stopped run is preserved unchanged and recovery happens
  beside it; no intervention may weaken a provenance, evidence, identity,
  filesystem, confirmation, or execution check, and none may turn a scientific
  rejection into an acceptance. That last clause is the line: repair carries a run
  past infrastructure, never past a scientific verdict. Shepherding is a designed
  part of the system rather than a fallback, so a run that used it is not a lesser
  run — the three published demonstrations were shepherded, one with a disclosed
  same-run resume. See
  [when a run stops](https://github.com/BeibaiDraco/maieusis/blob/main/docs/RUN_SUPERVISION.md);
  the setup interview carries the same four rules to your own coding agent.
- Opt-in prior-art review before shortlisting. A frontier model judges whether a
  proposed question is a direct recap of existing work, using both our own
  retrieval and — when separately enabled — its own bounded web search. A
  rejection requires a prior work resolved to a canonical identity (DOI,
  OpenAlex, or Crossref) on a deterministic lane; an unresolved web hit can never
  reject a question. Search plans, queries, results, and the search cutoff are
  persisted, and every positive finding is stated as scoped to that cutoff — no
  question is ever claimed novel. The schema defaults for `novelty.enabled` and
  `novelty.web_grounding.enabled` remain `false`; the shipped project template
  sets both to `true`.
- A receipt-bound admission contract for scanned-PDF text derivatives. Producing
  the derivative and its receipt is a local pre-processing step you perform with
  your own tools; see the
  [scanned-PDF guide](https://github.com/BeibaiDraco/maieusis/blob/main/docs/SCANNED_PDFS.md).
- One recommended project profile plus a planner-host variant, replacing the
  earlier development/scientific split. The scaffolded profile is now the
  configuration the published demonstrations used.
- [Citation guidance](https://github.com/BeibaiDraco/maieusis/blob/main/docs/CITATION.md).

### Changed

- Stage reuse is keyed on a timestamp-free semantic digest, so a scientifically
  identical re-run no longer forces downstream recomputation; the exact-byte
  digest still governs replay and corruption detection.
- Human-view pages state the prior-art outcome for every variant the review
  held back, with the priors it resolved and what would distinguish the
  question from them. A variant the review admitted is shown as active for
  planning and carries no prior-art narrative, so these pages show you why
  something was held back, not what a clean review examined.
- Measured prompt budgets, source-local degradation, per-document dataset-context
  admission, and partitioned citation selection replace several fixed limits, so
  a large or awkward input degrades honestly instead of failing the run.
- Sealed run closeout and typed provider-warning terminals are recorded rather
  than inferred.
- Recoverable provider or structured-reply failures preserve diagnostic bytes and useful sibling
  work. Family-scoped failures close with typed warning dossiers instead of aborting unrelated
  branches, and completed paper work can be reused on an honest resume without repayment.
- Shared topic-evidence insufficiency can enter one source-locked, non-accepting inquiry and the
  existing bounded revision/re-review loop. The inquiry may uphold, revise from packet-resident
  sources, or escalate; it cannot accept a brief or add evidence.
- Reader pages now distinguish scientific rejections, infrastructure warnings, provisional
  evidence, accepted plans, and non-inclusion reasons from their typed source records.

### What the demonstrations show

Three datasets were run under criteria fixed before the runs started. Climate produced four
independently accepted planning dossiers and two evidence-backed scientific rejections. IBL
produced six family dossiers containing eight accepted variants and two operationalization
rejections. NLB produced five independently accepted planning families containing nine accepted
variants and one evidence-backed scientific rejection.

Those runs show scientific breadth and how the system behaves when a run has to recover from a
fault. They were produced on the candidate source tree rather than by the published package, so
they are not a statement about the exact bytes you install; the demo pages say which run produced
them.

### Boundaries

- Unchanged from `0.1.0`: outputs require scientific review and are not
  scientific findings, novelty certifications, or guarantees of answerability.
- The downstream analysis-execution bridge and confirmatory analysis remain
  closed.
- A bounded prior-art review is not a global priority search or a novelty
  certification.

## 0.1.0 — Research Preview (2026-07-16)

Initial public release.

### Added

- End-to-end scientific question development from source papers, topic
  literature, a coarse dataset narrative, and optional research intent.
- User-visible PaperCases, citation decisions, formation traces, cross-paper
  question-formation patterns, QuestionFamilies, planning closures, and
  end-user Markdown dossiers.
- Isolated Question Owner–Dataset Planner branches with typed dialogue,
  evidence-backed plan/reject outcomes, and independent plan review.
- Five-command `maieusis` CLI: `init`, `check`, `run`, `status`, and `resume`.
- Resume receipts, artifact digests, authority labels, and a hidden audit
  sidecar.
- Codex and Claude Code planner-host support.
- International Brain Laboratory Brain-Wide Map and Neural Latents Benchmark
  MC_Maze-S reproducible demonstration packages without source-paper PDFs.

### Boundaries

- Research Preview: outputs require scientific review and are not scientific
  findings, novelty certifications, or guarantees of answerability.
- The downstream analysis-execution bridge and confirmatory analysis remain
  closed.
