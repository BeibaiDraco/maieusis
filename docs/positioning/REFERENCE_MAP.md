# Evidence notes for the positioning map

This appendix records the publications used to interpret the
[Maieusis positioning map](POSITIONING.md). Publication status refers to the
version linked below; the [primary-source log](PRIMARY_SOURCE_LOG.csv) records
when each source was checked. Each placement is an author interpretation of
the task described in that publication, not a score of scientific quality or
overall capability.

## Works shown in the map

| # | Work | Publication | Status |
| --- | --- | --- | --- |
| 1 | SciMON | [Wang et al., ACL 2024](https://aclanthology.org/2024.acl-long.18/) | Peer-reviewed conference paper |
| 2 | ResearchAgent | [Baek et al., NAACL 2025](https://aclanthology.org/2025.naacl-long.342/) | Peer-reviewed conference paper |
| 3 | Scideator | [Radensky et al., ACM Conference on AI and Agentic Systems 2026](https://doi.org/10.1145/3786335.3813161) | Peer-reviewed conference paper; preprint first posted in 2024 |
| 4 | HypER | [Vasu et al., EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1292/) | Peer-reviewed conference paper |
| 5 | HypoGen / *Sparks of Science* | [O'Neill et al., 2025](https://arxiv.org/abs/2504.12976) | arXiv preprint |
| 6 | CrossTrace | [Bouras, 2026](https://arxiv.org/abs/2603.28924) | arXiv preprint |
| 7 | Graphs of Research (GoR) | [Gao et al., 2026](https://arxiv.org/abs/2605.14790) | arXiv preprint |
| 8 | Literature Meets Data / HypoRefine | [Liu et al., ACL 2025](https://aclanthology.org/2025.acl-long.12/) | Peer-reviewed conference paper |
| 9 | HARPA | [Vasu et al., 2025](https://arxiv.org/abs/2510.00620) | arXiv preprint |
| 10 | DiscoveryBench | [Majumder et al., ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/0d70af566e69f1dfb687791ecf955e28-Abstract-Conference.html) | Peer-reviewed conference paper |
| 11 | DataVoyager / *Data-driven Discovery with Large Generative Models* | [Majumder et al., 2024](https://arxiv.org/abs/2402.13610) | arXiv preprint (position paper) |
| 12 | AutoDiscovery | [Agarwal et al., NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/23b127521af7ca7a42f5cdb7507be4f2-Abstract-Conference.html) | Peer-reviewed conference paper |
| 13 | data-to-paper | [Ifargan et al., NEJM AI 2025](https://doi.org/10.1056/AIoa2400555) | Peer-reviewed journal article |
| 14 | HLER | [Zhu and Wang, 2026](https://arxiv.org/abs/2603.07444) | arXiv preprint |
| 15 | The AI Scientist | [Lu et al., *Nature* 2026](https://doi.org/10.1038/s41586-026-10265-5) | Peer-reviewed journal article; earlier preprint posted in 2024 |
| 16 | Kosmos | [Mitchener et al., 2025](https://arxiv.org/abs/2511.02824) | arXiv preprint |
| 17 | RQ-Bench / *On the Limits of LLM-as-Judge for Scientific Novelty Assessment* | [Sinhahajari et al., 2026](https://arxiv.org/abs/2606.12071) | arXiv preprint |

“Preprint” is used conservatively where the sources checked for this release do
not establish a peer-reviewed publication.

## Placement evidence

### 1. SciMON

SciMON retrieves prior-paper inspirations and iteratively improves idea
novelty. The cited workflow is literature-conditioned ideation; it does not
describe a reusable question-formation trace or a concrete target-dataset
planning gate.

### 2. ResearchAgent

ResearchAgent combines a core paper, related literature, entity augmentation,
and reviewer feedback to generate a problem, method, and experiment design. The
cited workflow provides structured ideation but does not describe either
transferable question-forming moves or a target-dataset answerability screen.

### 3. Scideator

Scideator extracts purpose, mechanism, and evaluation facets and recombines
them with novelty support. These are explicit paper components, but the cited
workflow does not reconstruct and transfer the transition from literature
state and data opportunity to a question.

### 4. HypER

HypER models literature-guided reasoning chains and generates
provenance-backed hypotheses, placing it toward the structured-reasoning end of
X. The cited task does not independently plan or reject a question against a
user-supplied target dataset.

### 5. HypoGen / *Sparks of Science*

HypoGen uses structured paper supervision and ideation traces such as
assumption, conceptual leap, and counterproposal. It transfers a paper-derived
reasoning pattern, while the cited publication does not add pre-execution
target-dataset planning.

### 6. CrossTrace

CrossTrace supplies step-level grounded scientific reasoning traces and a
cross-domain discovery-pattern taxonomy. It therefore sits near the explicit
trace-transfer end of X; its dataset and training task do not describe a
concrete target-dataset plan-or-reject branch.

### 7. Graphs of Research

Graphs of Research uses citation-evolution structures as supervision for idea
generation. This is explicit structural supervision, but the cited publication
does not present reviewed question-formation traces or target-dataset planning.

### 8. Literature Meets Data / HypoRefine

This approach refines hypotheses by combining literature and observational
data. Data informs hypothesis utility, but the cited workflow is not a gate
that decides whether a newly formed question should proceed before analysis.

### 9. HARPA

HARPA is literature-grounded and testability-driven, explores hypothesis design
spaces, and learns from experimental feedback. This gives it more contact with
testability than literature-only ideation, while the cited workflow remains
distinct from screening a question against one user-supplied target dataset
before execution.

### 10. DiscoveryBench

DiscoveryBench provides a discovery goal and datasets, then evaluates
multi-step code-based hypothesis search and verification. Because the goal is
supplied, the benchmark evaluates solving it rather than developing and
screening a new question before execution.

### 11. DataVoyager

DataVoyager searches and verifies hypotheses in supplied data. In the cited
position paper, the dataset is the discovery substrate rather than a later
feasibility constraint on a transferred literature-derived question.

### 12. AutoDiscovery

AutoDiscovery performs open-ended, data-first exploration using Bayesian
surprise and experiment outcomes. Its selection mechanism is driven by data
and experiments rather than by transferred question-forming moves followed by
a separate planning gate.

### 13. data-to-paper

data-to-paper begins from annotated data, raises hypotheses, designs plans,
writes analysis code, interprets outputs, and produces a traceable paper. It
includes planning and execution, but the cited workflow does not separate
literature-move transfer from an independent target-dataset plan-or-reject gate.

### 14. HLER

HLER profiles a dataset before dataset-aware research-question generation and
uses a question-quality and feasibility loop before econometric analysis. It
therefore overlaps substantially with the Y-axis criterion. The cited workflow
does not describe the same isolated Owner–Planner plan/reject/defer protocol or
reviewed cross-paper formation-pattern transfer.

### 15. The AI Scientist

The AI Scientist generates ideas, writes code, runs experiments, writes papers,
and performs automated review. These axes do not measure that extensive
automation. The published workflow does not make an independent,
pre-execution target-dataset answerability object central to its task design.

### 16. Kosmos

Kosmos receives an objective and dataset and iterates literature search, data
analysis, hypothesis generation, and synthesis. Its deep use of data gives it
more contact with Y than literature-only systems, but the cited loop performs
discovery and execution rather than a separate question-planning gate.

### 17. RQ-Bench

RQ-Bench studies limits of LLM-as-judge scientific novelty assessment. It
reconstructs author-anchored research questions from background, gaps, and
contributions, making it directly relevant to question reconstruction; as a
benchmark, it has no target-dataset planning branch.

## Supplemental records

- [BibTeX](references.bib)
- [Primary-source log](PRIMARY_SOURCE_LOG.csv)
- [Qualitative plotting coordinates](positioning_coordinates.csv)
