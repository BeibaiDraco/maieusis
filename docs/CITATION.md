# Citing Maieusis

[Documentation home](INDEX.md)

For reproducibility, cite the exact software version you ran. The recommended
citation for Maieusis v0.1.1 is:

> Xu, Y., & Doiron, B. (2026). *Maieusis* (Version v0.1.1) [Computer
> software]. Zenodo. https://doi.org/10.5281/zenodo.21388805

## Which DOI should I use?

- **Concept DOI — [`10.5281/zenodo.21388805`](https://doi.org/10.5281/zenodo.21388805):**
  this represents Maieusis across all versions and resolves to the latest Zenodo
  record. It is the DOI recorded in `CITATION.cff`, so it is what GitHub's
  citation panel offers.
- **Version DOI:** each release also has its own DOI, which resolves to the
  archived source snapshot for that exact release. Use it when reporting work
  performed with a specific version.
  - v0.1.1 — [`10.5281/zenodo.22134742`](https://doi.org/10.5281/zenodo.22134742)
  - v0.1.0 — [`10.5281/zenodo.21388806`](https://doi.org/10.5281/zenodo.21388806)

A version DOI cannot be recorded in `CITATION.cff` ahead of publication: Zenodo
mints it from the published GitHub Release, while the release workflow validates
that file during the freeze that precedes publication. Recording the concept DOI
there keeps the file true at every step, and this guide carries the version DOIs.

That is why v0.1.1's DOI arrives here in a commit dated after the release it
describes. The commit changes this page and nothing else: the tag, the release
assets, the files on PyPI, and the Zenodo archive are fixed, and none of them is
rebuilt or replaced by it.

## Citing the version you actually ran

If you ran v0.1.0, keep citing v0.1.0 and its version DOI — that release, its
tag, and its assets are immutable and are not rewritten by later releases:

> Xu, Y., & Doiron, B. (2026). *Maieusis* (Version v0.1.0) [Computer
> software]. Zenodo. https://doi.org/10.5281/zenodo.21388806

GitHub's **Cite this repository** panel reads the root
[`CITATION.cff`](https://github.com/BeibaiDraco/maieusis/blob/main/CITATION.cff)
and offers APA and BibTeX. The Zenodo record for each release provides
additional citation styles and export formats.

## Citing a question, or a run's own output

Two different things get cited here and they are not the same act.

**A published demonstration question.** These are the families under `demos/`, each with its own
page and a stable path. Cite the software release plus the path, so a reader can open the exact
record rather than searching for a title — the family names are ours, not a literature identity.
For example: *Maieusis v0.1.1 demonstration `demos/ibl/artifacts/families/accumulation-geometry`*.
Nothing in them was executed, so a question is a proposal with its evidence attached, and citing one
as a finding would be a misreading of the artifact rather than of this page.

**Your own run.** The citable object is the run directory, not a sentence you copied out of it. It
carries the model identities, prompt-family versions, digests and review records that make any claim
in it checkable, and none of that survives being quoted alone. Cite the software release and version
DOI for the tool, and archive or attach the run directory for the result — remembering that
[a second run of the same profile does not reproduce the first](LIMITATIONS.md#running-the-same-configuration-twice-does-not-reproduce-the-same-questions),
so the directory is the evidence and the configuration is not.

## Terms of reuse

The repository declares one licence, [Apache-2.0](https://github.com/BeibaiDraco/maieusis/blob/main/LICENSE),
and no separate terms for any file in it. The demonstration dossiers, question pages and reading
guides are files in this repository, so they carry that licence like everything else: you may reuse,
adapt and build on them, with attribution and the notices Apache-2.0 requires.

Two things that licence does not reach, because they were never ours to give. The source-paper PDFs
are not distributed here at all and remain under their publishers' terms. The climate dataset is a
collaborator's derived product and is not redistributed; [its dataset notes](../demos/climate/DATASET_NOTES.md)
say so. What is published is what the runs wrote about them.

## Technical report

A separate technical report is planned but is not yet the preferred citation.
Until it is published, cite the software DOI above. Once the report has its own
DOI, this guide and `CITATION.cff` will distinguish citation of the method from
citation of the exact software release; existing tags and release assets are not
rewritten.
