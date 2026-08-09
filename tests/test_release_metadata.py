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
    assert "https://pypi.org/project/maieusis/0.1.1/" in readme


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
    artifact_roots = [_demo_root() / demo / "artifacts" for demo in ("climate", "ibl", "nlb")]
    expected_counts = {"climate": 50, "ibl": 43, "nlb": 44}
    internal_id = _INTERNAL_ID_RE
    private_field = re.compile(
        r"\b(?:provider_)?session_id\b|\brequest_id\b|\braw_payload\b|"
        r"\bhidden_audit\b|\bsource_tree_root\b|\bcapture_path\b",
        re.I,
    )

    for root in artifact_roots:
        files = sorted(path for path in root.rglob("*") if path.is_file())
        assert len(files) == expected_counts[root.parent.name]
        for path in files:
            if path.suffix.lower() not in {".md", ".yaml", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8")
            assert internal_id.search(text) is None, path
            assert private_field.search(text) is None, path
            assert "EvidenceRequest[" not in text, path


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

    builds = set()
    for demo_id in ("climate", "ibl", "nlb"):
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

        assert provenance["qualification_class"] == "candidate_demonstration"
        assert "not from the byte-qualification run" in provenance["note"]
        assert re.fullmatch(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}", provenance["run_id"])
        assert re.fullmatch(r"[0-9a-f]{64}", provenance["science_build_sha256"])
        assert re.fullmatch(r"[0-9a-f]{64}", provenance["leg_receipt_sha256"])
        builds.add(provenance["science_build_sha256"])

    assert len(builds) == 3

    ibl = _load_demo_manifest("ibl")["demo_provenance"]
    assert re.fullmatch(r"[0-9a-f]{64}", ibl["presentation_build_sha256"])
    assert ibl["presentation_build_sha256"] != ibl["science_build_sha256"]
    for demo_id in ("climate", "nlb"):
        assert _load_demo_manifest(demo_id)["demo_provenance"]["presentation_build_sha256"] is None


def test_public_demo_artifact_inventories_exactly_match_the_curated_files() -> None:
    expected_showcases = {
        "climate": ["wave-forcing-and-state-dependence"],
        "ibl": ["covariability-structure"],
        "nlb": ["manifold-form-functional-meaning"],
    }
    expected_counts = {"climate": 50, "ibl": 43, "nlb": 44}
    selected_count = 0
    for demo_id in ("climate", "ibl", "nlb"):
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
        assert all(set(item) == {"path", "sha256"} for item in inventory)
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
        if demo_id == "nlb":
            assert (
                expected["provenance/paperbank_import.yaml"]
                == (manifest["paperbank_import"]["public_provenance_sha256"])
            )
    # One operator-selected showcase family per demonstration.
    assert selected_count == 3


def test_public_questions_index_covers_all_families_variants_and_resolves_links() -> None:
    questions_path = _demo_root() / "QUESTIONS.md"
    text = questions_path.read_text(encoding="utf-8")

    # Three demonstrations of six families with two variants each.
    assert len(re.findall(r"^###\s+\d+\.\s+", text, re.M)) == 18
    assert len(re.findall(r"^[12]\.\s+\[[^\]]+\]\(", text, re.M)) == 36
    family_links = re.findall(r"questions/question_families_detailed\.md#(family-[^)]+)", text)
    assert len(family_links) == len(set(family_links)) == 18
    assert len(re.findall(r"questions/question_families_detailed\.md#variant-", text)) == 36

    root = _demo_root().resolve()
    projected_root_readme = (questions_path.parent / ".." / "README.md").resolve()
    for destination, fragment in _local_markdown_links(questions_path):
        if destination == projected_root_readme:
            assert fragment == "explore-the-demos"
            if destination.is_file():
                assert destination == (ROOT / "README.md").resolve()
            continue
        # `../docs/x.md` from demos/QUESTIONS.md resolves inside the PROJECTION, where
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


def test_demo_reader_guides_carry_primary_citations_and_no_stale_editorial_state() -> None:
    demo_root = _demo_root()
    questions = (demo_root / "QUESTIONS.md").read_text(encoding="utf-8")
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

    # Every reader page names the run that produced it and refuses the stronger claim.
    for text in (climate, ibl, nlb):
        prose = " ".join(text.split())
        assert "release-candidate source tree" in prose
        assert "not a statement about the exact bytes" in prose
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
    text = (demo_root / "QUESTIONS.md").read_text(encoding="utf-8")

    prose = " ".join(text.split())
    assert "Mixed family" in prose
    assert "Scientific rejection terminal" in prose
    assert "not a failure" in prose
    assert "stays visible with its reason rather than disappearing" in prose

    rejections = []
    for demo_id in ("climate", "ibl", "nlb"):
        for family in sorted((demo_root / demo_id / "artifacts" / "families").iterdir()):
            guide = (family / "dossier_detailed.md").read_text(encoding="utf-8")
            if "Family status: **Scientific rejection terminal**" in guide:
                rejections.append(f"{demo_id}/{family.name}")
                assert "Rejection is a scientific terminal" in guide
    assert len(rejections) == 3
    assert any(name.startswith("climate/") for name in rejections)
    assert any(name.startswith("nlb/") for name in rejections)


def test_the_climate_demo_leads_with_its_rejection() -> None:
    """The climate page features a family that produced no plan, and that is deliberate.

    A plan cannot show a reader whether the planner opened their data; a refusal can. This family
    asked for Ural-versus-Aleutian precursor pathways from a one-dimensional 60N column that has no
    longitude, and stopped rather than substituting a height-indexed proxy. If someone later
    re-points this page at a family that succeeded, the demonstration loses the only artifact that
    distinguishes a grounded planner from a fluent one.
    """
    demo_root = _demo_root()
    manifest = _load_demo_manifest("climate")
    featured = manifest["artifacts"]["showcase_family_ids"]
    assert featured == ["wave-forcing-and-state-dependence"]

    page = (demo_root / "climate" / "README.md").read_text(encoding="utf-8")
    assert "a question this dataset could not answer" in page
    assert "Scientific rejection terminal" in page
    # The page must still say the run produced plans, or a reader concludes the leg failed.
    assert "Four of the six families in this run did produce plans" in page

    dossier = (
        demo_root / "climate" / "artifacts" / "families" / featured[0] / "dossier.md"
    ).read_text(encoding="utf-8")
    assert "Planned analysis:" not in dossier
    assert dossier.count("Planning disposition: Rejected") == 2


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
    gallery = (demo_root / "QUESTIONS.md").read_text(encoding="utf-8")
    entries = re.split(r"(?m)^### \d+\. ", gallery)[1:]
    assert len(entries) == 18

    # Read the presentation order from the gallery itself. Hardcoding it made this test fail when
    # the demonstrations were reordered for the reader, which is a presentation decision and not a
    # truth change -- a guard that breaks on those trains people to edit the guard.
    demo_order = [
        {"IBL": "ibl", "NLB": "nlb", "Climate": "climate"}[match]
        for match in re.findall(r"(?m)^## (IBL|NLB|Climate) ", gallery)
    ]
    assert sorted(demo_order) == ["climate", "ibl", "nlb"], demo_order

    checked = {"both": 0, "prior_art": 0, "rejection": 0, "mixed": 0}
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
            deferred = [d for d in dispositions if d.startswith("Not carried into planning")]

            outcome = re.search(r"(?m)^Outcome: (.+)$", entry)
            assert outcome is not None, entry[:120]
            claim = outcome.group(1)

            if claim.startswith("**Scientific rejection terminal**"):
                checked["rejection"] += 1
                if deferred:
                    # A family may both close scientifically AND have lost a variant to prior art;
                    # the entry must not silently drop the second fact.
                    assert "deferred on prior-art grounds" in claim
                continue

            if deferred:
                assert claim.startswith("**Deferred on prior-art grounds**"), (demo_id, claim)
                # The reader must be able to see WHICH variant was held back.
                assert "held back before planning" in entry
                checked["prior_art"] += 1
            elif claim.startswith("**Mixed family**"):
                checked["mixed"] += 1
            else:
                assert claim.startswith("**Plan developed (provisional)**"), (demo_id, claim)
                assert "both variants reached" in claim
                checked["both"] += 1

    # Measured from the runs, not chosen: seven families planned both variants, three lost a variant
    # to prior art before planning, five are mixed, and three closed scientifically.
    assert checked == {"both": 7, "prior_art": 3, "mixed": 5, "rejection": 3}


def test_demo_landing_page_tallies_match_the_gallery() -> None:
    """The per-demo counts a reader meets first must agree with the entries they summarize."""

    demo_root = _demo_root()
    gallery = (demo_root / "QUESTIONS.md").read_text(encoding="utf-8")
    sections = re.split(r"(?m)^## ", gallery)
    for demo_id, heading in (
        ("climate", "Climate —"),
        ("ibl", "IBL Brain-Wide Map"),
        ("nlb", "NLB MC_Maze-S"),
    ):
        section = next(s for s in sections if s.startswith(heading))
        both = len(re.findall(r"\*\*Plan developed \(provisional\)\*\*", section))
        readme = (demo_root / demo_id / "README.md").read_text(encoding="utf-8")
        tally = re.search(r"(?m)^Six question families, twelve variants: (.+)$", readme)
        assert tally is not None, demo_id
        claimed = re.search(r"(\d+) reached plans for both variants", tally.group(1))
        assert claimed is not None, (demo_id, tally.group(1))
        assert int(claimed.group(1)) == both, (demo_id, claimed.group(1), both)
