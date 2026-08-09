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
  performed with a specific version. The v0.1.0 version DOI is
  [`10.5281/zenodo.21388806`](https://doi.org/10.5281/zenodo.21388806); the
  v0.1.1 version DOI appears on the release's Zenodo record and in the GitHub
  Release notes.

A version DOI cannot be recorded in `CITATION.cff` ahead of publication: Zenodo
mints it from the published GitHub Release, while the release workflow validates
that file during the freeze that precedes publication. Recording the concept DOI
there keeps the file true at every step, and this guide carries the version DOIs.

## Citing the version you actually ran

If you ran v0.1.0, keep citing v0.1.0 and its version DOI — that release, its
tag, and its assets are immutable and are not rewritten by later releases:

> Xu, Y., & Doiron, B. (2026). *Maieusis* (Version v0.1.0) [Computer
> software]. Zenodo. https://doi.org/10.5281/zenodo.21388806

GitHub's **Cite this repository** panel reads the root
[`CITATION.cff`](https://github.com/BeibaiDraco/maieusis/blob/main/CITATION.cff)
and offers APA and BibTeX. The Zenodo record for each release provides
additional citation styles and export formats.

## Technical report

A separate technical report is planned but is not yet the preferred citation.
Until it is published, cite the software DOI above. Once the report has its own
DOI, this guide and `CITATION.cff` will distinguish citation of the method from
citation of the exact software release; existing tags and release assets are not
rewritten.
