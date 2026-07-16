# Changelog

Maieusis follows semantic versioning. This file records public releases, not
the private development history.

## 0.1.0 — Research Preview

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
- IBL and NLB reproducible demonstration packages without source-paper PDFs.

### Boundaries

- Research Preview: outputs require scientific review and are not scientific
  findings, novelty certifications, or guarantees of answerability.
- The downstream analysis-execution bridge and confirmatory analysis remain
  closed.
- The technical report planned within one week of first release will have a
  citation separate from the software release citation.
