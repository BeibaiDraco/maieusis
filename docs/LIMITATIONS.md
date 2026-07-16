# Limitations

[Documentation home](INDEX.md) · [Method overview](METHOD_OVERVIEW.md)

Maieusis v0.1.0 is a Research Preview. Its outputs are structured scientific
planning products, not findings or certifications.

## Scientific limitations

- A source-backed question-forming pattern can still be unimportant, biased by
  the selected papers, or fail to transfer to a new field.
- PaperCase and formation-trace reconstruction is limited by what is present in
  the published record. It does not recover private author intent.
- Topic-literature retrieval may miss relevant work because of paywalls,
  indexing gaps, query design, language, or incomplete metadata.
- No product novelty search runs in v0.1.0. Novelty is `not_assessed`, even when
  a question appears unusual or well motivated.
- Dataset planning can miss undocumented structure, data-quality problems,
  selection effects, or domain-specific constraints.
- A feasible plan may still be scientifically weak, underpowered, ethically
  inappropriate, or uninformative in practice.
- Independent AI review reduces self-approval but does not establish truth.
- A plan is not a result. No dossier demonstrates an effect or supports a
  confirmatory claim.
- Authority labels describe source and review state, not scientific
  correctness.

Human domain expertise remains valuable for scientific importance, construct
validity, ethics, interpretation, and decisions about whether any later
analysis should proceed.

## Scope limitations

- The architecture is designed for any scientific discipline and any
  scientific dataset that can provide a lawful, read-only inspection surface
  with enough documentation, metadata, code, or representative data for
  responsible planning.
- The first public examples use the International Brain Laboratory Brain-Wide
  Map and Neural Latents Benchmark MC_Maze-S neuroscience datasets; they are
  worked examples, not limits on the intended scope.
- Testing with researchers at different universities across climate science,
  physics, astronomy, finance, social science, and psychology is ongoing on
  datasets from their own fields.
- Users remain responsible for lawful paper and dataset access, local
  dependencies, domain-specific loading code, and any dataset-specific adapter.
- Maieusis cannot make an undocumented or inaccessible dataset answerable.

## Operational limitations

- Standard runs require Codex or Claude Code, a usable local inspection
  environment, a real dataset or representative sample, and scientific model
  APIs from at least two providers for independent Owner/Reviewer operation.
- Runs may incur API charges and coding-agent subscription usage. Cost and
  latency depend on paper count, requested family breadth, revision limits,
  provider rates, and model availability.
- Provider outages, rate limits, account entitlements, and coding-agent
  concurrency can interrupt individual branches.
- A complete run may include accepted, rejected, deferred, mixed, or warning
  families. An unsuccessful scientific outcome is not automatically a software
  bug.
- `resume` avoids repeating work only when the recorded inputs,
  configuration, versions, and file hashes still match.
- Source-paper PDFs and many datasets cannot be redistributed with the
  software.

## Privacy and security limitations

- A coding agent is a local process with access to the files and tools the user
  grants it. Review those permissions before running.
- Do not give Maieusis restricted data unless local use is lawful and the
  configured providers, tools, and egress are compatible with its governance
  requirements.
- The public examples are not a template for handling protected participant
  data.
- Credentials must stay outside YAML, prompts, source control, and run outputs.

## Capabilities intentionally not provided

Maieusis v0.1.0 does not:

- execute a full scientific analysis;
- access a confirmation set;
- search for statistically significant effects;
- certify novelty, importance, truth, or publishability;
- create a downstream analysis contract; or
- authorize confirmatory analysis.

No model output, config change, accepted dossier, or example unlocks these
capabilities.

For setup or run failures, use [troubleshooting](TROUBLESHOOTING.md). For
scientific collaboration, contact `dracoxu@uchicago.edu`.

---

[Documentation home](INDEX.md) · [Architecture](ARCHITECTURE.md) ·
[Provenance](PROVENANCE.md) · [Troubleshooting](TROUBLESHOOTING.md)
