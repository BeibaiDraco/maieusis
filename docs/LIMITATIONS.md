# Limitations

[Documentation home](INDEX.md) · [Method overview](METHOD_OVERVIEW.md)

Maieusis v0.1.1 is a Research Preview. Its outputs are structured scientific
planning products, not findings or certifications.

## Scientific limitations

- A source-backed question-forming pattern can still be unimportant, biased by
  the selected papers, or fail to transfer to a new field.
- **Prior-art review can miss an obvious prior, including one the run itself
  read.** A named case ships in these demonstrations, and it has survived a
  change of demonstration set. The climate family
  [*Stratospheric signatures of downward communication and persistence*](../demos/climate/artifacts/families/downward-propagation-proxies/dossier.md)
  asks whether downward-extending anomalies are a distinct, dynamically
  organized mode of stratospheric evolution or a descriptive by-product of
  persistent vortex disturbances. Baldwin and Dunkerton 2001 — the canonical
  downward-propagation paper — is in that run's own paper bank
  ([the record](../demos/climate/artifacts/paperbank/papers/11-baldwin-dunkerton-2001.md)),
  correctly extracted, carrying the competing explanation that apparent
  downward influence is an illusion of downward phase propagation. That is
  close to what the family proposes to distinguish, and it is named nowhere in
  any prior-art comparison this run recorded. The family is adjacent rather
  than duplicate, but a reviewer would send it back, and the review should have
  surfaced the paper.
  Read the closest-known-work sections as a starting point for your own search,
  never as a completed one.
- Maieusis does not screen source papers for author affiliation. Two of the
  twelve papers in the published neuroscience cohort are by this project's own
  authors, and one of them is a named source for two reviewed patterns used in
  both neuroscience demonstrations. That is
  [disclosed in the paper list](../demos/PAPER_SOURCES.md#author-affiliated-sources--a-disclosure);
  nothing in the system would have flagged it.
- PaperCase and formation-trace reconstruction is limited by what is present in
  the published record. It does not recover private author intent.
- Topic-literature retrieval may miss relevant work because of paywalls,
  indexing gaps, query design, language, or incomplete metadata.
- **Topic evidence in this version is read from abstracts and metadata, not
  from full text.** The open-access full-text lane exists and is exercised, but
  it promotes text only where a source carries a rights assertion the run can
  verify, and in every leg recorded so far none did: 149 attempts across 28
  legs enriched 0 records, the four legs of the sealed set included. `literature.fulltext_enrichment` therefore defaults to
  `false`; a run that turns it on and again enriches nothing says so in its
  stage receipt.
- Prior-art review is bounded, not exhaustive. It runs on every variant and draws on a
  deterministic scholarly lane and an independent web-search lane, but it reports what it found
  within a recorded scope and cutoff. No search proves absence, so Maieusis never claims a
  question is novel. A variant it does not flag has not been certified; it has been reviewed.
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
- The public examples are four runs over two neuroscience datasets (the International Brain
  Laboratory Brain-Wide Map, used twice — once told to think about noise correlations and once told
  nothing — and Neural Latents Benchmark MC_Maze-S) and one atmospheric-science dataset (an
  ERA5-derived stratospheric record). They are worked examples, not limits on the intended scope.
- All four published runs' topic literature cleared its independent review, so every one of them
  carries the `verified` evidence ceiling rather than the lower `provisional_inspiration`. That is
  new in this release; every previously published set carried the lower ceiling on every run.
  [Reading the labels](LABELS.md) explains what the ceiling does and does not limit — it is not a
  claim that any question here was executed or confirmed.
- The climate dataset is a collaborator-supplied derived product and is not redistributed;
  [its dataset notes](../demos/climate/DATASET_NOTES.md) say so plainly.
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

### Running the same configuration twice does not reproduce the same questions

This deserves saying plainly, because everything else about how this system records itself points
the other way. [Provenance and reproducibility](PROVENANCE.md) binds every artifact to digests,
prompt-family versions and pinned full model IDs; the profiles under `examples/release/` ship as the
exact inputs that qualified this release; and the setup pages talk about verifying a demonstration's
paper filenames and SHA-256 values. None of that is a promise that a second run writes the same
questions, and it should not be read as one.

What is pinned is the **identity** of everything that went in: which bytes, which prompts, which
model, at which effort. What is not pinned is the model's output. There is no temperature setting
and no seed in the configuration, because a provider API does not offer the determinism those would
imply. Two runs of one unchanged profile can propose different question families, cite different
literature, and reach different terminals — and the second run is not thereby wrong.

The size of that variation is not small, and this project has measured it on itself. Two climate
qualification legs, byte-identical in configuration and prompt, retrieved materially different
literature: one cited 26 sources, the next 43. The wider draw is what crashed a leg and cost a
qualification set. Across the whole qualification history the same profiles drew 8 to 59 records.

So: a reproduction here means re-running the pinned inputs and getting a scientifically comparable
result, not a byte-identical one. If you need the exact artifacts a run produced, keep the run
directory — that is the reproducible object, and everything in it is bound to the identities above.

## Privacy and security limitations

- A coding agent is a local process with access to the files and tools the user
  grants it. Review those permissions before running.
- Do not give Maieusis restricted data unless local use is lawful and the
  configured providers, tools, and egress are compatible with its governance
  requirements. The complete list of what leaves your machine is below; read it
  before pointing Maieusis at anything restricted.

### Everything that leaves your machine

In `standard` mode, a run contacts these and nothing else. `maieusis check`
prints a role-level version of this list before any paid call.

| What is sent | Where it goes | Key needed |
| --- | --- | --- |
| Extracted source-paper **text** | your configured extraction model provider | yes |
| Literature and citation queries, plus the `crossref_mailto` / `openalex_email` you configure | Crossref and OpenAlex (free, no key; the email is the required polite-pool identifier and **is** transmitted) | no |
| Open-access full text fetches, when `fulltext_enrichment` is on (it is **off** by default: topic evidence is abstract-only in this version) | publisher and repository hosts named in the metadata | no |
| One fetch of your configured `dataset.seed.link` | that URL's host | no |
| Dataset description, question families, variants, plans, reviews | the topic / owner / reviewer model APIs | yes |
| A redacted prior-art projection, then public web searches | the novelty scout provider | yes |
| Topic queries, when `source_profile` is `elicit` or `hybrid` — **or `auto` with `ELICIT_API_KEY` set** | Elicit (paid, opt-in, off by default) | yes |
| The dataset **path** and the planning task | your local coding-agent host | host login |

Two consequences worth stating plainly:

- **Raw source PDFs are never uploaded** — only text extracted from them. Dataset
  files are never uploaded either.
- **The Dataset Planner is an LLM-backed agent.** It reads your dataset locally,
  but whatever it reads, quotes, or reasons about enters its own host's model
  context and therefore that host's provider. Read-only access is not local-only
  processing. If your data governance forbids that, do not point the planner at
  restricted data.
- The public examples are not a template for handling protected participant
  data.
- Credentials must stay outside YAML, prompts, source control, and run outputs.

## Capabilities intentionally not provided

Maieusis v0.1.1 does not:

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
