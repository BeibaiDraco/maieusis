"""Release metadata contracts shared by the dev truth and public projection."""

from __future__ import annotations

import hashlib
import html
import re
import tomllib
from pathlib import Path
from urllib.parse import unquote

import yaml

from research_agenda_engine import __version__
from research_agenda_engine.services.presentation import family_page

ROOT = Path(__file__).resolve().parents[1]

IMMUTABLE_RC_COMMIT = "a897715b065ee50251924307aaa96771f0e16e3a"
RC_WHEEL_SHA256 = "a5826a426f2e708ae1aaa4d42719bf491d78597519db49b208780d3ff5a3ce99"
PAIR_RECEIPT_SHA256 = "2da077057e92f30a0022a0856ad11b7476654223c67e9919c487e65ca243df06"
PAPER_HALF_RECEIPT_SHA256 = "fbfa86c4ee1e1f925488f3d5c5b8f388a61700ab6e37fac5d613e85ffd03e4d6"
PAPERBANK_IMPORT_RECEIPT_SHA256 = "75bc8baaf98629e8deaaead956e025fa07a0de54cdfb1061463cdc6872728f34"
SHARED_PATTERN_DETAILED_SHA256 = "4940bbcae206d2c14f3f74062d3174a2b6f2e4ffdacfcda2425c3f5bf91c1467"


def _demo_root() -> Path:
    source_root = ROOT / "demos" / "public"
    return source_root if source_root.is_dir() else ROOT / "demos"


def _docs_root() -> Path:
    """Where the published docs live: under `public/` in this tree, at the root in the projection.

    Derived from the demo root rather than written out, because the exporter rewrites exactly one
    literal spelling of that path and a second copy would ship unprojected into the public tree.
    Both trees keep docs and demos in the same shape, so one answers for the other.
    """
    demo_root = _demo_root()
    return ROOT / "docs" / demo_root.name if demo_root.name == "public" else ROOT / "docs"


def _public_roots() -> list[Path]:
    public_roots = [ROOT / "docs", ROOT / "demos"]
    if public_roots[0].is_dir():
        return public_roots
    return [ROOT / "docs", ROOT / "demos"]


def _load_demo_manifest(demo_id: str) -> dict[str, object]:
    return yaml.safe_load(
        (_demo_root() / demo_id / "demo_manifest.yaml").read_text(encoding="utf-8")
    )


def _family_status(guide: str, terminal_page: str = "") -> str:
    """The status label the run wrote, read by prefix from a published reading guide.

    Deliberately a second implementation of the rule in `scripts/refresh_demo_release.py`, not an
    import of it: a judge that shares code with the builder cannot catch the builder being wrong.
    The two are held together by the tally comparison at the end of the gallery gate -- if they
    ever classify a family differently, that assertion fails.

    By prefix because the labels are sentences, not enums: `Mixed family: accepted and non-accepted
    sibling variants` does not equal `Mixed family`, and matching the short form exactly reported
    zero mixed families in a set that had two.
    """
    match = re.search(r"(?m)^.*Family status: \*\*(.+?)\*\*", guide)
    if match is None:
        # A family closed before the shortlist gate has no reading guide, and refusing it would mean
        # this judge can only grade sets that happen to contain no honest early terminal. Its own
        # page states the disposition the product wrote. Resolved independently of the builder, like
        # everything else here; the tally comparison is what holds the two answers together.
        shortlist = re.search(r"(?m)^- Shortlist: `(.+?)`", terminal_page)
        assert shortlist is not None, (
            "a family has neither a reading-guide status line nor a `- Shortlist:` disposition"
        )
        assert shortlist.group(1) == "deferred", (
            f"no gallery label is defined for a guide-less family at shortlist "
            f"{shortlist.group(1)!r}"
        )
        return "Deferred on prior-art grounds"
    label = match.group(1)
    # Read from the product, not transcribed. This was four hand-copied strings against the twelve
    # `family_page._STATUS_LABELS` defines, and the first set to contain a thirteenth-of-twelve --
    # `Validation warning`, produced by the 2026-08-23 IBL leg -- turned a status the product emits
    # routinely into a test failure that said nothing about the release. The sibling generators had
    # already been taught to derive this list; the test that checks them kept its private copy,
    # which is the shape their own comments warn about.
    #
    # Longest first, so a prefix match cannot let a shorter label shadow a longer one that begins
    # with the same words.
    from research_agenda_engine.services.presentation.family_page import _STATUS_LABELS

    for known in sorted(_STATUS_LABELS.values(), key=len, reverse=True):
        if label.startswith(known):
            return known
    raise AssertionError(f"unrecognised family status: {label!r}")


_REDACTION_MARKER = family_page._REDACTED_INTERNAL_ID


def _families_per_demo() -> int:
    """The family count the release contract requests, read from the pinned set.

    Every demonstration in a set runs the same requested breadth, so one number answers for all of
    them; asserting it per demonstration as well is what makes a short tree fail loudly.
    """

    counts = {block["families"] for block in _expectations()["demos"].values()}
    assert len(counts) == 1, f"demonstrations disagree on family count: {sorted(counts)}"
    return counts.pop()


def _demo_ids() -> tuple[str, ...]:
    """Which demonstrations this release publishes, DERIVED from the pinned set.

    These were seven hardcoded `("climate", "ibl", "nlb")` tuples plus two count assertions. The
    0.1.1 qualification set has FOUR legs -- the IBL pair is deliberate, one anchored on a declared
    topic and one open on the same recordings -- and a hardcoded triple silently drops whichever
    leg is not in it, which is the narrowing-without-a-complement defect this release exists to
    remove. Reading the set means a leg added or removed is a one-line change to
    `release_set.yaml`, not a scavenger hunt through the gates.
    """

    return tuple(sorted(_expectations()["demos"]))


def _expectations() -> dict:
    """The pinned tallies for the published set, regenerated by `refresh_demo_release.py`.

    These used to be inline constants, which meant a re-run cost a dozen scattered hand edits and
    got them wrong: the 2026-08-15 artifacts shipped under the 2026-08-06 legs' build and receipt
    digests. Pinning them in one regenerated file does not by itself prove them -- a regeneration
    can bless a truncated tree -- so the gates below still compare each published page against the
    artifact it summarises, and use this file only for the totals a page cannot show.
    """
    return yaml.safe_load(
        (_demo_root() / ".release" / "release_expectations.yaml").read_text(encoding="utf-8")
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _local_markdown_links(path: Path) -> list[tuple[Path, str]]:
    links: list[tuple[Path, str]] = []
    text = path.read_text(encoding="utf-8")
    for raw_target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
        target = raw_target.strip().strip("<>")
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        target = target.split(maxsplit=1)[0]
        relative, _, fragment = target.partition("#")
        relative = unquote(relative)
        destination = path if not relative else path.parent / relative
        links.append((destination.resolve(), unquote(fragment)))
    return links


def _github_heading_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*$", path.read_text(encoding="utf-8"), re.M):
        heading = re.sub(r"<[^>]+>", "", html.unescape(heading)).strip().lower()
        base = re.sub(r"[^\w\s-]", "", heading)
        base = re.sub(r"\s", "-", base)
        occurrence = seen.get(base, 0)
        seen[base] = occurrence + 1
        anchors.add(base if occurrence == 0 else f"{base}-{occurrence}")
    return anchors


def _assert_mapping_contains(actual: dict[str, object], expected: dict[str, object]) -> None:
    assert {key: actual[key] for key in expected} == expected


def test_release_identity_and_license_are_consistent() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert pyproject["name"] == "maieusis"
    assert pyproject["version"] == __version__ == "0.1.1"
    assert pyproject["license"] == "Apache-2.0"
    assert pyproject["license-files"] == ["LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"]
    assert [author["name"] for author in pyproject["authors"]] == [
        "Yunlong Xu",
        "Brent Doiron",
    ]
    assert pyproject["maintainers"] == [{"name": "Yunlong Xu"}]
    assert (ROOT / "NOTICE").read_text(encoding="utf-8") == "Copyright 2026 Yunlong Xu\n"
    assert (ROOT / "THIRD_PARTY_NOTICES.md").is_file()

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text


def test_citation_metadata_names_only_the_two_software_authors() -> None:
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    assert citation["cff-version"] == "1.2.0"
    assert citation["title"] == "Maieusis"
    assert citation["version"] == "0.1.1"
    assert str(citation["date-released"]) == "2026-08-07"
    assert citation["license"] == "Apache-2.0"
    assert citation["repository-code"] == "https://github.com/BeibaiDraco/maieusis"
    assert len(citation["authors"]) == 2
    assert [(author["given-names"], author["family-names"]) for author in citation["authors"]] == [
        ("Yunlong", "Xu"),
        ("Brent", "Doiron"),
    ]
    assert [author["orcid"] for author in citation["authors"]] == [
        "https://orcid.org/0000-0003-2589-7232",
        "https://orcid.org/0000-0002-6916-5511",
    ]
    # Concept DOI on purpose. A version DOI cannot exist here: Zenodo mints it from the
    # published GitHub Release, while the release workflow validates this file during the
    # freeze that precedes publication, so a version DOI could only be invented or stale.
    assert citation["doi"] == "10.5281/zenodo.21388805"
    assert "preferred-citation" not in citation
    assert all("email" not in author for author in citation["authors"])


def test_public_citation_surfaces_bind_the_released_version_and_concept_dois() -> None:
    docs_root = _public_roots()[0]
    readme_path = docs_root / "README.md"
    if not readme_path.is_file():
        readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    guide = (docs_root / "CITATION.md").read_text(encoding="utf-8")
    index = (docs_root / "INDEX.md").read_text(encoding="utf-8")

    released_version_doi = "10.5281/zenodo.21388806"  # v0.1.0, which stays citable forever
    concept_doi = "10.5281/zenodo.21388805"
    expected_citation = (
        "Xu, Y., & Doiron, B. (2026). *Maieusis* (Version v0.1.1) [Computer software]. Zenodo."
    )
    readme_prose = " ".join(readme.replace("\n> ", " ").split())
    guide_prose = " ".join(guide.replace("\n> ", " ").split())

    # The current release's citation resolves through the CONCEPT DOI, because its own version DOI
    # does not exist until Zenodo mints it from the published release. Both surfaces must still
    # carry the earlier version DOI so a reader who ran v0.1.0 can cite exactly what they ran.
    for text in (readme, guide):
        assert concept_doi in text
        assert released_version_doi in text
    assert expected_citation in readme_prose
    assert expected_citation in guide_prose
    assert f"https://doi.org/{concept_doi}" in readme_prose
    assert "Version v0.1.0" in guide_prose
    assert "[Citation guide](CITATION.md)" in index
    assert "package is available from PyPI" not in readme
    assert "DOI will be added" not in readme

    badges = (
        "https://img.shields.io/pypi/v/maieusis.svg",
        "https://img.shields.io/pypi/pyversions/maieusis.svg",
        "https://github.com/BeibaiDraco/maieusis/actions/workflows/tests.yml/badge.svg?branch=main&event=push",
        # Concept DOI badge: a version-DOI badge goes stale on every release and cannot be correct
        # before the release it names has been published.
        "https://zenodo.org/badge/DOI/10.5281/zenodo.21388805.svg",
        "https://img.shields.io/pypi/l/maieusis.svg",
    )
    assert all(badge in readme for badge in badges)

    # A candidate tree is frozen and merged BEFORE the wheel is built and long before it is
    # promoted, so for that whole window the version it names is on no index at all. A
    # version-pinned link or a pinned `pip install` therefore cannot be correct when it ships — the
    # same reason the badge above is the concept DOI rather than a version DOI, reasoned out one
    # artifact over and then not applied here.
    #
    # This assertion used to run the other way, requiring the pinned link to be present. It was
    # green while the published README linked to a 404 and the recommended install command failed,
    # because it checked that the sentence existed rather than that it was true.
    version = __version__
    installation = (docs_root / "INSTALLATION.md").read_text(encoding="utf-8")
    troubleshooting = (docs_root / "TROUBLESHOOTING.md").read_text(encoding="utf-8")
    assert "https://pypi.org/project/maieusis/" in readme
    for surface, text in (
        ("README.md", readme),
        ("INSTALLATION.md", installation),
        ("TROUBLESHOOTING.md", troubleshooting),
    ):
        assert f"https://pypi.org/project/maieusis/{version}/" not in text, surface
        assert f"=={version}" not in text, surface


def test_public_source_tree_contains_no_raw_papers_or_private_release_records() -> None:
    public_roots = _public_roots()
    public_files = [path for root in public_roots for path in root.rglob("*") if path.is_file()]
    assert public_files
    assert not [path for path in public_files if path.suffix.lower() in {".pdf", ".nwb"}]
    assert not [path for path in public_files if path.name.endswith("_audit.yaml")]
    assert not [path for path in public_files if path.name.endswith(".capture.json")]
    assert not [
        candidate
        for root in public_roots
        for candidate in root.rglob("*")
        if candidate.is_symlink()
    ]

    private_path = re.compile(r"(?<![A-Za-z0-9:/])/(?:Users|home|private|var|tmp|opt|etc)/")
    secret = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[opsu]_[A-Za-z0-9]{12,})\b")
    for path in public_files:
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".csv", ".bib", ".py"}:
            continue
        text = path.read_text(encoding="utf-8")
        assert private_path.search(text) is None, path
        assert secret.search(text) is None, path
        assert "MAIEUSIS_RELEASE_BLOCKER" not in text, path

        if path.suffix.lower() == ".md":
            for raw_target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
                target = raw_target.strip().strip("<>").split("#", 1)[0].lower()
                assert not target.endswith((".pdf", ".nwb")), (path, target)


# `cc` (citation context) belongs in the DIGEST-SHAPED alternation, never beside `cw`: the loose
# `[A-Za-z0-9]` branch would match `CC-BY` under re.I, and the climate cohort cites CC-BY licensed
# articles. Real identifiers are `cc-<12 hex>`, which the hex branch catches while leaving licence
# names alone. `test_internal_identifier_scan_separates_digests_from_licence_names` pins both
# halves of that behaviour.
# Three internal tracker ids and one dangling redaction marker shipped in published dossiers while
# this guard was green, because the pattern below did not name them. `review-change-` was the leak;
# `[internal id]` is worse, because it is the sanitizer's own residue -- it means a citation was
# stripped and the sentence left pointing at nothing. Both are now matched. When a new internal id
# shape appears, it belongs here BEFORE it appears in an artifact.
_INTERNAL_ID_RE = re.compile(
    r"\b(?:cw|qfamily|qvariant|qpattern)-[A-Za-z0-9]"
    r"|\b(?:branch|cc|event|evidence|claim|context|request|session|thread|review-change)-"
    r"(?:[0-9a-f]{6,}|[0-9]{3,})\b"
    r"|\[internal id\]",
    re.I,
)


def test_internal_identifier_scan_separates_digests_from_licence_names() -> None:
    """The demo scan must catch citation-context identifiers without eating licence names.

    The four positive samples are verbatim identifiers from the 2026-08-06 climate leg's PaperBank
    summary, which the pre-D0 audit found the scan did not match at all.
    """

    for identifier in (
        "cc-217e489593e2",
        "cc-3bc2d4091d98",
        "cc-aadb6a28b306",
        "cc-e3a5463a88ad",
        "see cc-217e489593e2 for the surrounding sentence",
        "cw-abc123",
        "branch-1a2b3c4d",
    ):
        assert _INTERNAL_ID_RE.search(identifier) is not None, identifier

    for licence in (
        "CC-BY",
        "cc-by",
        "CC-BY-4.0",
        "cc-by-nc-sa",
        "published under CC-BY 4.0",
        "Creative Commons CC BY",
        "CC0",
    ):
        assert _INTERNAL_ID_RE.search(licence) is None, licence


def test_curated_demo_artifacts_do_not_leak_internal_identifiers_or_private_payloads() -> None:
    artifact_roots = [_demo_root() / demo / "artifacts" for demo in _demo_ids()]
    expected_counts = {
        demo_id: item["file_count"] for demo_id, item in _expectations()["demos"].items()
    }
    internal_id = _INTERNAL_ID_RE
    private_field = re.compile(
        r"\b(?:provider_)?session_id\b|\brequest_id\b|\braw_payload\b|"
        r"\bhidden_audit\b|\bsource_tree_root\b|\bcapture_path\b",
        re.I,
    )

    # `[internal id]` is the product's own disclosure that a reference was removed and the sentence
    # kept, and it is allowed HERE and refused everywhere else. This reverses an earlier reading of
    # the same marker as sanitizer residue: that was written when the alternative was a page that
    # merely lost a word, and the alternative is now a page the reader never receives at all --
    # raising inside the add-on made its page-isolation handler swallow the whole reading guide.
    # Its count is pinned so it cannot quietly spread across the prose.
    artifact_id = re.compile(
        "|".join(part for part in internal_id.pattern.split("|") if "internal id" not in part),
        re.IGNORECASE,
    )
    markers = 0

    # Content first, tally second. The other order hid fifteen leaked internal citation identifiers
    # across three published trees for as long as the pinned file counts were stale: the count
    # assertion failed first, so the leak assertions below it never ran. A cheap check that can
    # mask an expensive one belongs after it.
    miscounted = {}
    for root in artifact_roots:
        files = sorted(path for path in root.rglob("*") if path.is_file())
        if len(files) != expected_counts[root.parent.name]:
            miscounted[root.parent.name] = (len(files), expected_counts[root.parent.name])
        for path in files:
            if path.suffix.lower() not in {".md", ".yaml", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8")
            assert artifact_id.search(text) is None, path
            assert private_field.search(text) is None, path
            assert "EvidenceRequest[" not in text, path
            # BOTH spellings, read the same way the producer reads them. The product respelled
            # its placeholder from the square form to the paren form, `refresh_demo_release.py`
            # was taught to count both, and this judge was not — so the first set the current
            # product writes would have made `refresh`'s true total disagree with this assertion,
            # and the obvious way to make it green again is to re-pin `redaction_markers`, after
            # which the pin no longer bounds the marker the product actually writes.
            markers += text.count("[internal id]") + text.count(_REDACTION_MARKER)
    assert not miscounted, miscounted
    assert markers == _expectations()["redaction_markers"], markers


def test_public_runtime_names_exactly_one_product_identity() -> None:
    """The published runtime presents one product name, and the packaging agrees with the prose.

    This guard used to enumerate retired codenames literally, split across a `+` so the regex would
    not match itself. The concatenation hid those strings from the regex and from nobody else -- it
    was the only place they appeared in the published tree. The check is positive now: the console
    script, the distribution name, and the prose brand must be the same one word.
    """
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "maieusis"' in pyproject
    assert 'maieusis = "research_agenda_engine.product_cli:app"' in pyproject

    # `research_agenda_engine` is an import package name. It must never be used as the product's
    # name in user-facing prose, which is where a retired brand would surface.
    cli = (ROOT / "src" / "research_agenda_engine" / "product_cli.py").read_text(encoding="utf-8")
    for sentence in re.findall(r"[A-Z][^.\n]{10,200}\.", cli):
        assert "research_agenda_engine is" not in sentence
        assert "research-agenda-engine" not in sentence


def test_shared_neuroscience_cohort_serves_both_demos_from_twelve_unique_sources() -> None:
    demo_root = _demo_root()
    shared = yaml.safe_load(
        (demo_root / "shared" / "paper_sources.yaml").read_text(encoding="utf-8")
    )
    ibl = _load_demo_manifest("ibl")
    nlb = _load_demo_manifest("nlb")

    expected = {
        "1-s2.0-S0896627319300534-main.pdf": "a8e3bc43d4d592aedcbd2e3cbe2be62a49097a84122564876faf5f5e1e6a6482",
        "2024.08.30.610535v3.full.pdf": "4f5392320954ff98fd83da15a2f3b538b87753255e3d9e0cb3955bd950ad2614",
        "ibl-s41586-025-09226-1.pdf": "a014031cd0023347792305e807b565f833b7b4a00e39d5dfd2efc01561f9b2b9",
        "nature12160.pdf": "5e86b83a153d4cd3f65785a734888f9df0bfb7a5024aebfd77e5d3884f842cac",
        "nature12742.pdf": "7fbe1cee260ec93f6d9084406c032647be093c488d4a30b0169276aab1c549aa",
        "nn.3807.pdf": "8c019f3ed61e3e03644069d0b72466cdede4cb5c89c3f33bb45609ea73d52591",
        "s41586-019-1346-5.pdf": "95c774e6432cc6c29269b618a1d56f278e63c7b7aeb5e85ea9e0ab35d4389f4b",
        "s41586-021-04268-7.pdf": "ca9bdede2572d45e7ebed1f7cde1d64aec79046b80d57b1cbaeff742e65c7a7d",
        "s41586-025-09528-4 (1).pdf": "1dd19ac2906f4180c5cbb2ec6bc95a795b263d7d1f155cca2fca22aa6f501dca",
        "s41593-024-01758-5.pdf": "66defedae05ee2e1919b5390365cced4155bccf383de3dc3d812c1cbabebaf02",
        "science.aav7893.pdf": "380ac73d0c1fd7bc62e402a0dcc2244cc9064b5fbaf9bee530a65cc3b824b1c8",
        "srinath-et-al-2026-the-structure-of-correlated-variability-reflects-task-relevant-information-in-sensory-neurons.pdf": "afbade7cbdf5af1666a11a7d4b2038f4fec5fa5ecef8142f7a66ca027b8b60ce",
    }
    actual = {paper["filename"]: paper["pdf_sha256"] for paper in shared["papers"]}
    filenames = [paper["filename"] for paper in shared["papers"]]
    hashes = [paper["pdf_sha256"] for paper in shared["papers"]]
    dois = [paper["doi"] for paper in shared["papers"]]
    cohort_status = "shared_twelve_source_neuroscience_cohort"

    assert len(shared["papers"]) == len(expected) == 12
    assert len(filenames) == len(set(filenames))
    assert len(hashes) == len(set(hashes))
    assert len(dois) == len(set(dois))
    assert actual == expected
    assert shared["raw_pdfs_included"] is False
    assert shared["status"] == cohort_status
    assert ibl["paper_cohort_status"] == nlb["paper_cohort_status"] == cohort_status
    assert nlb["dataset"]["pinned_version"] == "0.220113.0408"
    assert nlb["dataset"]["source_note"] == "DATASET_NOTES.md"
    assert nlb["dataset"]["metadata_verifier"] == "verify_region_mapping.py"
    assert nlb["dataset"]["known_conversion_caveat"] == (
        "m1_unit_electrode_indices_require_plus_96"
    )
    dataset_note = (demo_root / "nlb" / "DATASET_NOTES.md").read_text(encoding="utf-8")
    assert "leading `1`: PMd" in dataset_note
    assert "leading `2`: M1" in dataset_note
    assert "adding 96" in dataset_note
    assert "| train | 72 | 70 | 142 |" in dataset_note
    assert nlb["dataset"]["access_mode"] == "external_readonly"

    private_manifest_path = ROOT / "docs" / "release" / "maieusis-v0.1.0-paper-cohort.private.yaml"
    if private_manifest_path.is_file():
        private = yaml.safe_load(private_manifest_path.read_text(encoding="utf-8"))
        private_candidates = {
            paper["filename"]: paper["sha256"]
            for paper in private["candidate_cohort"]["filenames_and_sha256"]
        }
        expected_exclusions = {
            "2026.01.07.698022v1.full.pdf",
            "PIIS009286741730538X.pdf",
            "PIIS0896627326000073.pdf",
        }
        excluded = {
            paper["filename"]
            for paper in private["papers"]
            if paper["disposition"] == "excluded_before_release_screen"
        }
        retained = {
            paper["filename"]
            for paper in private["papers"]
            if paper["disposition"] == "retained_in_final_paperbank"
        }
        final = {
            paper["filename"]: paper["sha256"]
            for paper in private["final_cohort"]["filenames_and_sha256"]
        }
        post_screen_exclusions = {
            paper["filename"] for paper in private["final_cohort"]["excluded_after_screen"]
        }

        assert private["candidate_cohort"]["count"] == len(expected)
        assert private_candidates == expected
        assert excluded == expected_exclusions
        assert post_screen_exclusions == {"s41593-024-01758-5.pdf"}
        assert retained == set(expected) - post_screen_exclusions
        assert final == {name: digest for name, digest in expected.items() if name in retained}
        assert private["pattern_contribution_acceptance"]["warnings_permitted"] is True
        assert (
            private["pattern_contribution_acceptance"]["pattern_review_policy"]
            == "configured_bounded_multi_round_revise_and_rereview_required"
        )
        assert private["pattern_contribution_acceptance"]["final_cohort_status"] == (
            "frozen_from_final_quality_ibl_run"
        )
        _assert_mapping_contains(
            private["candidate_summary"],
            {
                "accepted_luna_front_half_input_pdfs": 12,
                "accepted_luna_front_half_paper_cases": 12,
                "accepted_luna_front_half_reviewed_traces": 12,
                "accepted_luna_front_half_reviewed_patterns": 8,
                "final_paperbank_paper_cases": 11,
                "final_paperbank_reviewed_traces": 10,
                "final_paperbank_reviewed_patterns": 8,
                "final_quality_ibl_run_id": "20260715T173301Z-4eefe86a",
                "final_quality_ibl_run_manifest_sha256": (
                    "f8d73dda365f02ffedf336d1b5d25c4ee586e9133bce583bd18a30a0e3ff6a90"
                ),
                "final_paper_half_receipt_sha256": PAPER_HALF_RECEIPT_SHA256,
            },
        )
        _assert_mapping_contains(
            private["final_cohort"],
            {
                "status": "frozen_from_final_quality_ibl_run",
                "count": 11,
                "paper_cases": 11,
                "reviewed_formation_traces": 10,
                "reviewed_patterns": 8,
            },
        )


def test_public_demo_manifests_separate_demo_provenance_from_release_identity() -> None:
    """A demo says which run produced it; release-byte identity lives where it can be true.

    The 0.1.0 manifests carried a `release_candidate` block asserting one immutable wheel and one
    sealed pair receipt, identical across demos. That shape cannot survive: the contract is a
    three-dataset set rather than a pair, the three legs ran on four distinct builds, and under the
    build-once contract the package is built FROM the tree containing these files, so no file inside
    it can carry the resulting hash. Per-demo provenance stays here; wheel, sdist, tree, and seal
    digests move to the release receipt published after the build.
    """

    expected = _expectations()
    builds = set()
    for demo_id in _demo_ids():
        manifest = _load_demo_manifest(demo_id)
        provenance = manifest["demo_provenance"]

        assert manifest["schema_version"] == "maieusis.public_demo/v2"
        assert manifest["release"] == "0.1.1"
        assert manifest["release_contract"] == "release_validation_set/v2"
        assert "release_candidate" not in manifest
        assert "luna_gate" not in manifest
        flattened = yaml.safe_dump(manifest)
        for byte_identity_key in ("wheel_sha256", "sdist_sha256", "artifact_set_sha256"):
            assert byte_identity_key not in flattened

        assert provenance["qualification_class"] == "qualification_run"
        assert re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}", provenance["run_id"])
        assert re.fullmatch(r"[0-9a-f]{64}", provenance["science_build_sha256"])
        assert re.fullmatch(r"[0-9a-f]{64}", provenance["leg_receipt_sha256"])
        builds.add(provenance["science_build_sha256"])

        # The run named here is the run these artifacts were cut from. Shipped wrong once: the
        # 2026-08-15 artifacts carried the 2026-08-06 demo legs' build and receipt digests beside
        # their own run_id -- three fields, two different runs -- because the refresh was by hand
        # and nothing compared them.
        assert provenance["run_id"] == expected["demos"][demo_id]["run_id"]
        assert provenance["science_build_sha256"] == expected["science_build_sha256"]

    # The build-once contract, checkable without the operator's set root: three legs of one
    # qualified package are three legs of ONE build. Three distinct digests is the shape the
    # by-hand refresh left behind, and the old gate asserted it as though it were the contract.
    assert len(builds) == 1, sorted(builds)
    assert expected["distinct_science_builds"] == 1


def test_a_rehearsal_set_is_never_marked_ready_to_publish() -> None:
    """A set that did not qualify the package must say so in the flag a publisher reads.

    `release_ready: true` sat in every manifest through every rehearsal, including the set whose
    own pages were still being corrected. It is now derived from the set receipt's
    `qualification_status` rather than maintained by hand, and this is the gate that makes the
    derivation binding: publishing requires a qualifying run, not an edited flag.

    KILL MUTATION: set `qualification_status: qualifying` in the set receipt without re-running the
    three legs -- the presentation-basis assertion below then refuses, because a qualifying build
    renders its own pages and has no second basis to name.
    """
    expected = _expectations()
    status = expected["qualification_status"]
    assert status in ("qualifying", "rehearsal_only")
    release_ready = status == "qualifying"
    assert expected["release_ready"] is release_ready

    for demo_id in _demo_ids():
        manifest = _load_demo_manifest(demo_id)
        provenance = manifest["demo_provenance"]
        assert manifest["release_ready"] is release_ready
        assert (manifest["release_blocker"] is None) is release_ready
        if release_ready:
            # The qualifying build rendered these pages, so there is no second build to name.
            assert provenance["presentation_build_sha256"] is None
        else:
            assert provenance["presentation_build_sha256"], (
                "a rehearsal whose pages were re-rendered must name the basis that rendered them; "
                "a null here claims the qualifying build produced them"
            )


def test_public_demo_artifact_inventories_exactly_match_the_curated_files() -> None:
    expected_demos = _expectations()["demos"]
    expected_showcases = {
        demo_id: item["showcase_family_ids"] for demo_id, item in expected_demos.items()
    }
    expected_counts = {demo_id: item["file_count"] for demo_id, item in expected_demos.items()}
    selected_count = 0
    for demo_id in _demo_ids():
        manifest = _load_demo_manifest(demo_id)
        artifacts = manifest["artifacts"]
        artifact_root = _demo_root() / demo_id / artifacts["root"]
        inventory = artifacts["sanitized_inventory"]
        paths = [item["path"] for item in inventory]

        assert artifacts["status"] == "curated"
        assert artifacts["root"] == "artifacts"
        assert artifacts["file_count"] == len(inventory) == expected_counts[demo_id]
        assert artifacts["showcase_family_ids"] == expected_showcases[demo_id]
        assert artifacts["showcase_selection_status"] == "operator_selected"
        # A published manifest must not name a file that lives only in the private repo.
        assert "docs/plans" not in yaml.safe_dump(manifest)
        assert manifest["demo_provenance"]["leg_receipt"] == "withheld_private_operator_record"
        assert manifest["publication_gate"] == "operator_approved"
        selected_count += len(artifacts["showcase_family_ids"])
        # inventory_sha256 was previously shape-checked only, so it was a number nobody could
        # re-derive. Its derivation is now fixed and asserted: sha256 over "<path>\n<sha256>\n"
        # per entry, in listed order.
        assert re.fullmatch(r"[0-9a-f]{64}", artifacts["inventory_sha256"])
        assert (
            artifacts["inventory_sha256"]
            == hashlib.sha256(
                "".join(f"{item['path']}\n{item['sha256']}\n" for item in inventory).encode("utf-8")
            ).hexdigest()
        )
        assert paths == sorted(paths)
        assert len(paths) == len(set(paths))
        # Each entry now states where it came from. `{"path", "sha256"}` alone was the schema for as
        # long as nothing checked these trees against their runs: a digest of the published bytes
        # proves the file has not changed since it was recorded, and says nothing about whether it
        # was ever a redaction of anything. `scripts/check_demo_redaction.py` re-derives that proof
        # from these fields.
        for item in inventory:
            assert item.get("origin") in {"redacted", "derived"}
            if item["origin"] == "redacted":
                assert set(item) == {"path", "sha256", "source_path", "source_sha256", "origin"}
                assert re.fullmatch(r"[0-9a-f]{64}", item["source_sha256"])
            else:
                assert set(item) == {"path", "sha256", "origin", "derived_from"}
                assert item["derived_from"].strip()
        assert all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in paths)

        expected = {item["path"]: item["sha256"] for item in inventory}
        actual = {
            path.relative_to(artifact_root).as_posix(): _sha256(path)
            for path in sorted(artifact_root.rglob("*"))
            if path.is_file()
        }
        assert actual == expected
        assert (
            expected["paperbank/question_patterns_detailed.md"]
            == (manifest["presentation"]["pattern_detailed_sha256"])
        )
        assert (
            expected["questions/question_families_detailed.md"]
            == (manifest["presentation"]["question_families_detailed_sha256"])
        )
        # An import block is present only for a leg that actually imported its paper half. It was
        # a standing property of the NLB manifest instead, naming a run from nine days earlier
        # while that leg's own paper half had been produced from scratch.
        paperbank_import = manifest.get("paperbank_import")
        if paperbank_import is not None:
            provenance_path = paperbank_import["public_provenance_path"]
            assert provenance_path in expected, provenance_path
            assert expected[provenance_path] == paperbank_import["public_provenance_sha256"]
    # One operator-selected showcase family per demonstration, however many there are.
    assert selected_count == len(_demo_ids())


def test_the_review_agreement_the_gallery_publishes_is_what_the_ledgers_say() -> None:
    """The gallery states how often the two reviewers agreed; the ledgers have to say the same.

    "Every plan was checked by a second model, on a different provider" was the centre of the trust
    case and, until the ledgers were published, an assertion: no page said what either reviewer
    decided or how often they disagreed. Now that the number is on the front of the gallery it is a
    claim about the published tree, and a set that changes it must change the sentence too. The
    counts here are summed from the per-run pages, never written down.
    """

    ledgers = sorted(_demo_root().glob("*/artifacts/questions/review_decisions.md"))
    assert ledgers, "no run publishes a review ledger; re-read this assertion"
    agreed = total = 0
    for ledger in ledgers:
        match = re.search(r"the two agreed on (\d+) of (\d+)", ledger.read_text(encoding="utf-8"))
        assert match, f"{ledger} states no agreement count"
        agreed += int(match.group(1))
        total += int(match.group(2))
    words = {18: "eighteen", 19: "nineteen", 20: "twenty", 21: "twenty-one", 22: "twenty-two"}
    prose = " ".join((_demo_root() / "ALL_QUESTIONS.md").read_text(encoding="utf-8").split())
    assert re.search(rf"\b{words.get(total, total)} families carry both decisions", prose, re.I), (
        f"the gallery no longer says {total} families carry both decisions"
    )
    # Disagreements are the number this design is judged on. If one ever appears, the sentence
    # claiming none must stop being true before this test stops failing.
    disagreements = total - agreed
    claims_none = "the reviewer overturned nothing" in prose
    assert claims_none == (disagreements == 0), (
        f"the ledgers record {disagreements} disagreement(s) and the gallery "
        f"{'claims none' if claims_none else 'does not claim none'}"
    )


def test_no_published_page_divides_one_tally_by_a_tally_of_another_kind() -> None:
    """No "X of the Y" on a published page may state an X larger than its Y.

    The gallery counts plans per VERSION and questions per FAMILY, and one editorial sentence
    divided the first by the second: it published "twenty-seven of the twenty-four produced a
    plan". Both numbers were individually correct and derived from the artifacts, so every gate
    that checks a tally against its source was green -- the error was only in putting them in one
    sentence. This reads the arithmetic instead of the sources, and needs no page to word it any
    particular way.
    """

    units = [
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
        "twenty",
    ]
    words = {word: value for value, word in enumerate(units)}
    for tens, base in (("twenty", 20), ("thirty", 30)):
        words[tens] = base
        words |= {f"{tens}-{units[digit]}": base + digit for digit in range(1, 10)}

    def as_number(token: str) -> int | None:
        token = token.strip().lower()
        if token.isdigit():
            return int(token)
        return words.get(token)

    pages = sorted(_demo_root().rglob("*.md"))
    assert pages, "no published Markdown to check"
    offences: list[str] = []
    for page in pages:
        prose = " ".join(page.read_text(encoding="utf-8").split())
        for match in re.finditer(
            r"\*{0,2}([A-Za-z-]+|\d+)\*{0,2} of (?:the |these )?\*{0,2}([A-Za-z-]+|\d+)\*{0,2}",
            prose,
        ):
            part, whole = as_number(match.group(1)), as_number(match.group(2))
            if part is None or whole is None or part <= whole:
                continue
            offences.append(f"{page.relative_to(_demo_root())}: {match.group(0)!r}")
    assert not offences, (
        "a published page states a part larger than its whole, which means two tallies of "
        f"different kinds were put in one sentence: {offences}"
    )


def test_public_questions_index_covers_all_families_variants_and_resolves_links() -> None:
    questions_path = _demo_root() / "ALL_QUESTIONS.md"
    text = questions_path.read_text(encoding="utf-8")

    # Six families of two variants per demonstration, however many demonstrations there are. The
    # literals were 18 and 36, which silently stopped covering the set the moment it gained a
    # fourth leg: the counts still matched a three-leg gallery, so a page missing six families
    # would have passed.
    families = len(_demo_ids()) * _families_per_demo()
    variants = families * 2
    assert len(re.findall(r"^###\s+\d+\.\s+", text, re.M)) == families
    assert len(re.findall(r"^[12]\.\s+\[[^\]]+\]\(", text, re.M)) == variants
    family_links = re.findall(r"questions/question_families_detailed\.md#(family-[^)]+)", text)
    assert len(family_links) == len(set(family_links)) == families
    assert len(re.findall(r"questions/question_families_detailed\.md#variant-", text)) == variants

    root = _demo_root().resolve()
    projected_root_readme = (questions_path.parent / ".." / "README.md").resolve()
    for destination, fragment in _local_markdown_links(questions_path):
        if destination == projected_root_readme:
            assert fragment == "explore-the-demos"
            if destination.is_file():
                assert destination == (ROOT / "README.md").resolve()
            continue
        # `../docs/x.md` from demos/ALL_QUESTIONS.md resolves inside the PROJECTION, where
        # demos/public -> demos and docs/public -> docs. In this source tree it points at a
        # directory that does not exist, so resolve it the way a reader would and require the
        # projected source to be real.
        projected_docs = (questions_path.parent / ".." / "docs").resolve()
        if destination.is_relative_to(projected_docs):
            source = _docs_root() / destination.relative_to(projected_docs)
            assert source.is_file(), source
            continue
        assert destination.is_relative_to(root), destination
        assert destination.is_file(), destination
        if fragment:
            assert fragment in _github_heading_anchors(destination), (destination, fragment)


def test_every_published_demo_page_links_only_to_artifacts_that_exist() -> None:
    """Every local link on every published page resolves, not only the ones on the gallery.

    Measured 2026-08-15 on the three landing pages: all eighteen family links were dead, every one
    pointing at a directory from an earlier set that the current artifacts do not contain. The
    link-resolution gate covered `ALL_QUESTIONS.md` alone, so a reader arriving at a demonstration's
    front page and clicking anything under `artifacts/families/` got nothing, and nothing said so.

    KILL MUTATION: point one landing-page link at a family directory that is not published.
    """
    demo_root = _demo_root()
    pages = sorted(
        path
        for path in demo_root.rglob("*.md")
        # Artifacts are the run's own output and are checked as bytes against the run; these are
        # the hand-written pages around them.
        if "artifacts" not in path.relative_to(demo_root).parts
    )
    assert pages, "no published demonstration pages found"

    broken = []
    for page in pages:
        for destination, fragment in _local_markdown_links(page):
            if not destination.is_relative_to(demo_root.resolve()):
                # Links that leave the demo tree resolve inside the export projection and are
                # checked by the gallery gate, which knows how that projection is shaped.
                continue
            if not destination.exists():
                broken.append(f"{page.relative_to(demo_root)} -> {destination.name}")
            elif (
                fragment
                and destination.is_file()
                and fragment not in _github_heading_anchors(destination)
            ):
                broken.append(f"{page.relative_to(demo_root)} -> {destination.name}#{fragment}")
    assert not broken, broken


def test_demo_reader_guides_carry_primary_citations_and_no_stale_editorial_state() -> None:
    demo_root = _demo_root()
    questions = (demo_root / "ALL_QUESTIONS.md").read_text(encoding="utf-8")
    climate = (demo_root / "climate" / "README.md").read_text(encoding="utf-8")
    ibl = (demo_root / "ibl" / "README.md").read_text(encoding="utf-8")
    nlb = (demo_root / "nlb" / "README.md").read_text(encoding="utf-8")
    nlb_note = (demo_root / "nlb" / "DATASET_NOTES.md").read_text(encoding="utf-8")
    climate_note = (demo_root / "climate" / "DATASET_NOTES.md").read_text(encoding="utf-8")
    paper_sources = (demo_root / "PAPER_SOURCES.md").read_text(encoding="utf-8")

    assert "10.1038/s41586-025-09235-0" in ibl
    assert "2025_data_release_brainwidemap.html" in ibl
    neurips_source = (
        "datasets-benchmarks-proceedings.neurips.cc/paper/2021/hash/"
        "979d472a84804b9f647bc185a877a8b5-Abstract-round2.html"
    )
    for text in (nlb, nlb_note):
        assert neurips_source in text
        assert "10.48324/dandi.000140/0.220113.0408" in text
    for text in (nlb_note,):
        assert "10.1016/j.neuron.2010.09.015" in text
        assert "10.1038/nature11129" in text

    # The climate demonstration states its own provenance limit rather than implying parity with
    # the two citable neuroscience datasets.
    assert "www.ecmwf.int" in climate_note
    assert "is not redistributed" in climate_note
    assert "dracoxu@uchicago.edu" in climate_note
    assert "Copernicus" in climate_note

    # Every reader page names the run that produced it and states the provenance its own manifest
    # supports -- no more, and no less.
    #
    # This used to pin one era's wording: every page had to say "release-candidate source tree" and
    # "not a statement about the exact bytes", because for the whole life of these trees the
    # demonstrations could not be the output of the published package. The 2026-08-13 process change
    # existed to close that gap, and the 2026-08-23 set is the first to close it -- so a guard that
    # kept demanding the disclaimer would have required the pages to keep refusing a claim they had
    # finally earned. Reading `release_ready` means the assertion follows the artifact in both
    # directions: a rehearsal set must still disclaim, and a qualifying one must not pretend it is
    # one.
    for demo_id in _demo_ids():
        prose = " ".join((demo_root / demo_id / "README.md").read_text(encoding="utf-8").split())
        manifest = _load_demo_manifest(demo_id)
        run_id = manifest["demo_provenance"]["run_id"]
        assert run_id in prose, f"{demo_id}: the page does not name the run that produced it"
        if manifest["release_ready"]:
            assert "executed by the published package" in prose, (
                f"{demo_id}: the set qualified the published wheel and the page does not say so"
            )
            assert "not a statement about the exact bytes" not in prose, (
                f"{demo_id}: the page still disclaims a provenance its own manifest now carries"
            )
        else:
            assert "not a statement about the exact bytes" in prose, (
                f"{demo_id}: a rehearsal set must say its artifacts are not the published bytes"
            )
        assert "proposal hypothesis versus inspected evidence" in prose.lower()

    assert "does not distribute source PDFs" in paper_sources
    assert "shared/paper_sources.yaml" in paper_sources
    assert "climate/paper_sources.yaml" in paper_sources
    for cohort in ("shared/paper_sources.yaml", "climate/paper_sources.yaml"):
        manifest = yaml.safe_load((demo_root / cohort).read_text(encoding="utf-8"))
        for paper in manifest["papers"]:
            assert paper["title"] in paper_sources
            assert f"https://doi.org/{paper['doi']}" in paper_sources

    for stale_copy in (
        "remain an operator editorial choice",
        "allowlisted public subset",
        "showcase family is intentionally undecided",
        "the two public demos",
    ):
        assert stale_copy not in (questions + climate + ibl + nlb).lower()


def test_public_demo_outcome_boundaries_preserve_non_accepted_outcomes() -> None:
    """The gallery must show what did not work, in the vocabulary the runs actually used.

    This guards against a gallery that quietly shows only successes. The outcome labels changed
    with the runs -- `Scientific rejection terminal` and `Mixed family` replace the 0.1.0 strings --
    so the literals move while the guarantee does not.
    """

    demo_root = _demo_root()
    text = (demo_root / "ALL_QUESTIONS.md").read_text(encoding="utf-8")

    prose = " ".join(text.split())
    assert "Mixed family" in prose
    assert "Scientific rejection terminal" in prose
    assert "not a failure" in prose
    # Same reasoning: the guarantee is that a closed variant is still ON the page with its reason,
    # not that one particular sentence says so.
    assert re.search(r"stays (?:on the page|visible) with its reason", prose), (
        "the gallery no longer promises a closed variant stays on the page with its reason"
    )

    rejections = []
    for demo_id in _demo_ids():
        for family in sorted((demo_root / demo_id / "artifacts" / "families").iterdir()):
            # A family closed before the shortlist gate has no reading guide and cannot be a
            # rejection terminal -- that status is written INTO the guide. Reading it
            # unconditionally is the same crash the generators carried, made once more in the test
            # that checks them.
            guide_path = family / "dossier_detailed.md"
            if not guide_path.is_file():
                continue
            guide = guide_path.read_text(encoding="utf-8")
            if "Family status: **Scientific rejection terminal**" in guide:
                rejections.append(f"{demo_id}/{family.name}")
                assert "Rejection is a scientific terminal" in guide
    # Which families closed scientifically is a fact of the run, so it is pinned per name rather
    # than as a count: a count survives one rejection being swapped for another.
    assert rejections == _expectations()["scientific_rejections"]
    assert rejections, "a demonstration set with no scientific rejection shows only what worked"


def test_every_refusal_is_reachable_in_the_gallery_and_honestly_labelled() -> None:
    """A refusal may not be quietly dropped. It need not be what a page LEADS with.

    Two rules were folded together here and only one of them was ever load-bearing.

    The one that matters: a set that shows only what worked hides the single artifact that
    distinguishes a grounded planner from a fluent one. A plan cannot show a reader whether the
    planner opened their data; a refusal can. So every scientific rejection the run produced must be
    published, reachable from the gallery a reader arrives at, and carrying its real outcome label.

    The one that was an editorial opinion wearing a gate's clothes: that some page must LEAD with
    one. `governance/RELEASE_PROCESS.md:88-91` puts that with the operator -- "Editorial selection
    is legitimate precisely because the complete artifact set ships beside it and is reachable:
    featuring one family out of six hides nothing when all six are published" -- and the reason it
    is legitimate is exactly the property this test now enforces instead. Reachability is what makes
    the editorial freedom safe, so guarding reachability is guarding the right thing.

    Operator ruling, 2026-08-23: the four showcases are chosen on what each demonstrates, and no leg
    is required to open with a refusal.
    """
    demo_root = _demo_root()
    expectations = _expectations()
    rejections = expectations["scientific_rejections"]
    assert rejections, "a demonstration set with no scientific rejection shows only what worked"

    gallery = (demo_root / "ALL_QUESTIONS.md").read_text(encoding="utf-8")
    unreachable: list[str] = []
    unlabelled: list[str] = []
    for entry in rejections:
        demo_id, slug = entry.split("/", 1)
        family_dir = demo_root / demo_id / "artifacts" / "families" / slug
        assert family_dir.is_dir(), f"{entry}: the run recorded a refusal with no published family"
        dossier = family_dir / "dossier.md"
        assert dossier.is_file(), f"{entry}: published with no reader-facing dossier"

        # Reachable: the gallery links into this family. Checked on the LINK, not on the family
        # name appearing somewhere in the prose -- a name can be mentioned in a page that offers no
        # way to open it, and the gallery is the page a reader arrives at.
        if f"{demo_id}/artifacts/families/{slug}/" not in gallery:
            unreachable.append(entry)

        # Honestly labelled: the family's own page states the terminal it reached. Read from the
        # detailed guide, which is where the product writes the status line.
        guide = family_dir / "dossier_detailed.md"
        text = guide.read_text(encoding="utf-8") if guide.is_file() else ""
        if "Family status: **Scientific rejection terminal**" not in text:
            unlabelled.append(entry)

    assert not unreachable, "scientific rejections the gallery does not link to: " + ", ".join(
        unreachable
    )
    assert not unlabelled, (
        "scientific rejections whose own page does not print the terminal they reached: "
        + ", ".join(unlabelled)
    )


def test_each_demo_features_the_family_its_operator_selected() -> None:
    """The showcase is an editorial choice, and the manifest must carry the one that was made.

    No constraint on WHICH family. The only property is that the published manifest agrees with the
    pinned set, so a showcase cannot drift away from the choice on record.
    """
    expectations = _expectations()
    for demo_id in _demo_ids():
        featured = _load_demo_manifest(demo_id)["artifacts"]["showcase_family_ids"]
        assert featured == expectations["demos"][demo_id]["showcase_family_ids"], demo_id
        assert len(featured) == 1, f"{demo_id}: exactly one family leads a page"
        family_dir = _demo_root() / demo_id / "artifacts" / "families" / featured[0]
        assert family_dir.is_dir(), f"{demo_id}: features a family that is not published"


def test_every_gallery_outcome_is_derived_from_its_variants_actual_dispositions() -> None:
    """A family's outcome sentence must match what happened to its variants.

    This is the assertion whose absence let a real defect ship to review: the gallery said "both
    variants reached independently reviewed plans" for three families where one variant had been
    held back at the shortlist stage by the prior-art review -- the very mechanism the project
    describes as never removing a variant silently. The existing gallery test checked anchor counts
    and link resolution, and the outcome test checked that certain strings appeared somewhere. Both
    passed. Neither compared a claim against the artifact it summarizes.

    The truth lives in each variant's `Shortlist disposition` line, which the run wrote.
    """

    demo_root = _demo_root()
    gallery = (demo_root / "ALL_QUESTIONS.md").read_text(encoding="utf-8")
    entries = re.split(r"(?m)^### \d+\. ", gallery)[1:]
    assert len(entries) == len(_demo_ids()) * _families_per_demo()

    # Read the presentation order from the gallery itself. Hardcoding it made this test fail when
    # the demonstrations were reordered for the reader, which is a presentation decision and not a
    # truth change -- a guard that breaks on those trains people to edit the guard.
    # Read by DATASET IDENTITY, not by a heading prefix. The comment above learned this once when
    # the demonstrations were reordered; it had to be learned again when the headings were rewritten
    # for a reader ("IBL Brain-Wide Map" became "Mice making decisions: the IBL Brain-Wide Map").
    # The identity is the section; the prose around it is presentation.
    # The section headings are editorial and live in `gallery_editorial.yaml`; the renderer prints
    # them verbatim. Reading them from there rather than transcribing three literals means a
    # reworded heading, or a fourth demonstration, does not silently drop a leg out of this check --
    # a heading no literal matched simply contributed nothing and the assertion still passed.
    editorial = yaml.safe_load(
        (_demo_root() / ".release" / "gallery_editorial.yaml").read_text(encoding="utf-8")
    )["datasets"]
    headings = {demo_id: block["section_heading"] for demo_id, block in editorial.items()}
    assert sorted(headings) == sorted(_demo_ids()), (
        "gallery_editorial.yaml names different demonstrations than the pinned set"
    )
    demo_order = [
        demo_id
        for heading in re.findall(r"(?m)^## (.+)$", gallery)
        for demo_id, identity in headings.items()
        if identity == heading
    ]
    assert sorted(demo_order) == sorted(_demo_ids()), demo_order

    # Reading guides keyed by family title, because the family directories sort alphabetically and
    # the questions page runs in Family 001..006 order -- for the climate leg those two orders
    # share no element, so pairing them by position attributes one family's outcome to another.
    # A family closed before the shortlist gate has no reading guide -- no planning branch was
    # opened to write one about -- and its title comes from its terminal page instead. Reading the
    # guide unconditionally is the crash the two generators carried; making it here for a third
    # time would mean the test could only ever run against sets that happen not to contain an
    # honest early terminal.
    def _title_and_guide(family_dir: Path) -> tuple[str, tuple[str, str]]:
        terminal_page = (family_dir / "dossier.md").read_text(encoding="utf-8")
        guide_path = family_dir / "dossier_detailed.md"
        guide = guide_path.read_text(encoding="utf-8") if guide_path.is_file() else ""
        heading = guide.splitlines()[0] if guide else terminal_page.splitlines()[0]
        title = heading.removeprefix("# ").removesuffix(" — scientific reading guide").strip()
        return title, (guide, terminal_page)

    guides = {
        demo_id: dict(
            _title_and_guide(family_dir)
            for family_dir in (demo_root / demo_id / "artifacts" / "families").iterdir()
            if family_dir.is_dir()
        )
        for demo_id in demo_order
    }

    # `other_terminal` added 2026-08-18 alongside the generator's bucket of the same name. The
    # product defines twelve family statuses and this tally had five buckets, so the seven with no
    # branch fell through to `both` -- counted as "both versions planned" in the figure the release
    # publishes. A bucket that stays at zero on today's set is the point: it is where a status
    # nobody has seen lands, instead of being silently counted as a plan.
    checked = {
        "both": 0,
        "prior_art": 0,
        "prior_art_none": 0,
        "rejection": 0,
        "mixed": 0,
        "warning": 0,
        "other_terminal": 0,
    }
    index = 0
    for demo_id in demo_order:
        detailed = (
            demo_root / demo_id / "artifacts" / "questions" / "question_families_detailed.md"
        ).read_text(encoding="utf-8")
        families = re.split(r"(?m)^## Family \d{3}: ", detailed)[1:]
        assert len(families) == 6, demo_id

        for family in families:
            entry = entries[index]
            index += 1
            # Split by variant first: the family-level section carries a disposition line of its
            # own, so searching the whole block returns three for a two-variant family.
            variants = re.split(r"(?m)^### Variant \d{3}\.\d{3}: ", family)[1:]
            assert len(variants) == 2, (demo_id, len(variants))
            dispositions = [
                re.search(r"Shortlist disposition: \*\*(.{0,40})", variant).group(1)
                for variant in variants
            ]
            # Keyed on the two POSITIVE labels, independently of the generators but by the same
            # reasoning: the negative side is four unrelated string families, this judge knew one of
            # them, and a variant stopped at the SHORTLIST gate carries `Not shortlisted - deferred`
            # and matched none. A label the product adds later then counts as NOT planned, which can
            # understate plans and never invent one.
            deferred = [
                d
                for d in dispositions
                if not d.startswith(("Active for planning", "Shortlisted for planning"))
            ]

            # The label is the guarantee; the sentence carrying it is presentation, and it moved
            # when these entries were rewritten for a reader. Each outcome line now reads
            # `**Outcome: <label>.** <plain-words consequence>`.
            outcome = re.search(r"(?m)^\*\*Outcome: (.+?)\.\*\*(.*)$", entry)
            assert outcome is not None, entry[:120]
            claim, consequence = outcome.group(1), outcome.group(2)

            # Derive what happened from the run's own record, THEN require the gallery to say it.
            # Reading the gallery's claim first and only cross-checking some branches is how a
            # wrong claim classified itself: "Plan developed" was accepted without ever being
            # compared to a status the run wrote.
            title = family.splitlines()[0].strip()
            guide, terminal_page = guides[demo_id][title]
            status = _family_status(guide, terminal_page)
            # `startswith`, and the ORDER is the renderer's, not this test's. Two things bit here.
            # `_family_status` now returns the product's full label, and `Mixed family: accepted and
            # non-accepted sibling variants` is not equal to `Mixed family` -- the exact comparison
            # reported every mixed family as "both versions planned", the same false claim
            # `render_demo_gallery._outcome` carries a comment about having shipped once. And the
            # branch order has to match `_outcome` (:225-262), which resolves `deferred` BEFORE
            # `Mixed family`: a private ordering here would grade the gallery against a rule the
            # gallery does not follow, which is how a test comes to disagree with the page it checks
            # while both are internally consistent.
            bucket = (
                # A guide-less family resolves to a GALLERY label rather than a product status --
                # no product status is spelled this way -- so it is placed before the status
                # branches. Left to fall through, "Deferred on prior-art grounds" is caught by the
                # not-an-accepted-dossier branch and counted as its own terminal, which is how the
                # judge came to disagree with the builder by exactly one family.
                "prior_art_none"
                if status == "Deferred on prior-art grounds"
                else "rejection"
                if status.startswith("Scientific rejection terminal")
                else "warning"
                if status.startswith("Service warning")
                # Split, because they are different outcomes: one family keeps a sibling's plan and
                # the other keeps none. While they shared a bucket the plan-less one counted as
                # plan-bearing, which put `families_with_a_plan: 6` on a leg where one of the six
                # produced no plan at all.
                else "prior_art_none"
                if deferred and len(deferred) == len(dispositions)
                else "prior_art"
                if deferred
                else "mixed"
                if status.startswith("Mixed family")
                # The other eight product statuses are their own terminal, never a plan. Without
                # this branch a `Validation warning` family fell through to `both` and the judge
                # reported two plans that do not exist -- while the builder counted them correctly,
                # so the tally comparison at the end is what surfaced it.
                else "other_terminal"
                if not status.startswith("Accepted planning dossier")
                else "both"
            )
            checked[bucket] += 1

            if bucket == "rejection":
                assert claim == "Scientific rejection terminal", (demo_id, claim)
                if deferred:
                    # A family may both close scientifically AND have lost a variant to prior art;
                    # the entry must not silently drop the second fact.
                    assert "prior-art" in entry or "prior art" in entry, (demo_id, claim)
            elif bucket == "warning":
                # The machinery, not the science, ended this one. A reader told "plan developed"
                # would count a plan that does not exist.
                assert claim == "Service warning", (demo_id, claim)
            elif bucket == "prior_art_none":
                # Every version stopped before planning, so the family keeps no plan and no planning
                # record. The entry must say that rather than borrow the sibling-survived sentence.
                assert claim == "Stopped before planning on prior-art grounds", (demo_id, claim)
                assert "No version reached planning" in " ".join(entry.split()), (
                    demo_id,
                    consequence,
                )
            elif bucket == "prior_art":
                assert claim == "Deferred on prior-art grounds", (demo_id, claim)
                # The reader must still be able to see WHICH version was held back, whatever words
                # the entry uses to say it -- or, when EVERY version was, that none reached
                # planning at all. Both shapes exist: a family with one plan and one prior-art
                # closure, and a family closed entirely at the shortlist gate. Requiring only the
                # first phrasing made the honest early terminal fail a guarantee it satisfies more
                # completely than the case the sentence was written for.
                # Whitespace-normalised: these sentences wrap, and a line break between "reached"
                # and "planning" is not a missing guarantee. Matching raw text here failed three
                # times in one session for exactly that reason.
                assert re.search(
                    r"(?:(?:first|second) never reached planning|No version reached planning)",
                    " ".join(entry.split()),
                ), (demo_id, consequence)
            elif bucket == "mixed":
                assert claim == "Mixed family", (demo_id, claim)
            elif not status.startswith("Accepted planning dossier"):
                # The other eight product statuses. `render_demo_gallery._outcome` (:271-276) prints
                # the product's own label rather than inventing a reader-facing sentence for an
                # outcome nobody has seen, so the claim IS the status -- and the entry must say no
                # accepted plan is published, or a reader takes the label for a softer word than it
                # is. `Validation warning` is the first of the eight a real set has produced.
                assert claim == status, (demo_id, claim, status)
                assert "No accepted plan is published" in consequence, (demo_id, consequence)
            else:
                assert claim == "Plan developed (provisional)", (demo_id, claim)
                assert "oth versions got a plan" in consequence, (demo_id, consequence)

    # Measured from the runs, not chosen.
    assert checked == _expectations()["gallery"]["outcomes"]


_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


def _as_count(token: str) -> int:
    """Read a tally the reader sees, spelled either way. Unknown words are a failure, not a zero."""

    if token.isdigit():
        return int(token)
    count = _NUMBER_WORDS.get(token.lower())
    assert count is not None, f"unreadable tally word: {token!r}"
    return count


def test_demo_landing_page_tallies_match_the_gallery() -> None:
    """The per-demo counts a reader meets first must agree with the entries they summarize."""

    demo_root = _demo_root()
    gallery = (demo_root / "ALL_QUESTIONS.md").read_text(encoding="utf-8")
    sections = re.split(r"(?m)^## ", gallery)
    # Matched on the DATASET IDENTITY rather than on the start of the heading, because the heading
    # prose is written for a reader and moves -- "IBL Brain-Wide Map" became "Mice making decisions:
    # the IBL Brain-Wide Map", and a startswith matcher turned that into a StopIteration rather than
    # a readable failure. Exactly one section must match, so an ambiguous heading fails loudly
    # instead of silently picking the first.
    # Matched on the editorial file's own `section_heading`, exactly. A dataset-identity substring
    # was the previous rule and it broke the moment one dataset carried two demonstrations: both
    # IBL headings contain "IBL Brain-Wide Map", so the check found two sections and could not say
    # which leg it was reading. The heading is declared per demonstration, so read it from there.
    headings = {
        demo_id: block["section_heading"]
        for demo_id, block in yaml.safe_load(
            (demo_root / ".release" / "gallery_editorial.yaml").read_text(encoding="utf-8")
        )["datasets"].items()
    }
    for demo_id in _demo_ids():
        identity = headings[demo_id]
        matched = [s for s in sections if s.split("\n", 1)[0].strip() == identity]
        assert len(matched) == 1, f"{demo_id}: {len(matched)} gallery sections named {identity!r}"
        section = matched[0]
        # The label may be bolded on its own or inside a bolded "Outcome:" sentence; the count is
        # the guarantee, not the emphasis around it.
        both = len(re.findall(r"Plan developed \(provisional\)", section))
        readme = (demo_root / demo_id / "README.md").read_text(encoding="utf-8")
        # Anchored on the whole claim rather than on a loose neighbourhood: a pattern that merely
        # looked backwards from "reached plans" captured "six" out of "One of the six reached
        # plans", which is a guard that fails for a reason unrelated to what it protects. The
        # landing pages are written for a reader and spell the number out, so accept either form.
        claimed = re.search(
            r"\*\*([A-Za-z]+|\d+) of the six reached plans for both versions\*\*", readme
        )
        assert claimed is not None, f"{demo_id} landing page states no both-versions tally"
        assert _as_count(claimed.group(1)) == both, (demo_id, claimed.group(1), both)
