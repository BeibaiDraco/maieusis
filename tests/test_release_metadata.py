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
    assert pyproject["version"] == __version__ == "0.1.0"
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
    assert citation["version"] == "0.1.0"
    assert str(citation["date-released"]) == "2026-07-15"
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
    assert "doi" not in citation
    assert "preferred-citation" not in citation
    assert all("email" not in author for author in citation["authors"])


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


def test_curated_demo_artifacts_do_not_leak_internal_identifiers_or_private_payloads() -> None:
    artifact_roots = [_demo_root() / demo / "artifacts" for demo in ("ibl", "nlb")]
    internal_id = re.compile(
        r"\b(?:cw|qfamily|qvariant|qpattern)-[A-Za-z0-9]"
        r"|\b(?:branch|event|evidence|claim|context|request|session|thread)-"
        r"(?:[0-9a-f]{6,}|[0-9]{3,})\b",
        re.I,
    )
    private_field = re.compile(
        r"\b(?:provider_)?session_id\b|\brequest_id\b|\braw_payload\b|"
        r"\bhidden_audit\b|\bsource_tree_root\b|\bcapture_path\b",
        re.I,
    )

    for root in artifact_roots:
        files = sorted(path for path in root.rglob("*") if path.is_file())
        assert len(files) == 43
        for path in files:
            if path.suffix.lower() not in {".md", ".yaml", ".yml"}:
                continue
            text = path.read_text(encoding="utf-8")
            assert internal_id.search(text) is None, path
            assert private_field.search(text) is None, path
            assert "EvidenceRequest[" not in text, path


def test_public_runtime_contains_no_retired_network_product_identity() -> None:
    retired_tokens = (
        "quae" + "ro",
        "zete" + "sis",
        "xete" + "sis",
        "research" + "-agenda-engine",
    )
    retired = re.compile(
        r"(?i)\b(?:" + "|".join(re.escape(token) for token in retired_tokens) + r")\b"
    )
    offenders = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        if retired.search(path.read_text(encoding="utf-8")):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_public_demo_paper_cohort_is_frozen_from_all_twelve_unique_sources() -> None:
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
    cohort_status = "frozen_twelve_source_release_input"

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
    assert nlb["dataset"]["files"] == {
        "dandiset.yaml": "2492a05c49b2e3024797b45bc8db263a1bf12078891ec668b0623f0db1e0ba5a",
        "sub-Jenkins_ses-small_desc-train_behavior+ecephys.nwb": (
            "dcaf3a524e2b2f65f163ee3b07789b8474bdfc6ca66098bc542ab93dff489884"
        ),
        "sub-Jenkins_ses-small_desc-test_ecephys.nwb": (
            "ca8a0bef5f189eafb9db1961d617e065cb461360718fde1c16a538922a6fa5fe"
        ),
    }

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


def test_public_demo_manifests_bind_the_sealed_pair_and_presentation_replay() -> None:
    ibl = _load_demo_manifest("ibl")
    nlb = _load_demo_manifest("nlb")
    expected_candidate = {
        "immutable_rc_commit": IMMUTABLE_RC_COMMIT,
        "immutable_rc_version": "0.1.0",
        "rc_wheel_sha256": RC_WHEEL_SHA256,
        "pair_receipt_sha256": PAIR_RECEIPT_SHA256,
    }

    for manifest in (ibl, nlb):
        assert manifest["schema_version"] == "maieusis.public_demo/v1"
        assert manifest["release"] == "0.1.0"
        assert manifest["release_ready"] is True
        assert manifest["release_readiness_scope"] == "curated_demo_artifacts_only"
        assert manifest["publication_gate"] == "operator_pending"
        assert manifest["release_blocker"] is None
        assert manifest["raw_pdfs_included"] is False
        assert manifest["release_candidate"] == expected_candidate
        assert manifest["bridge_status"] == "closed"

    _assert_mapping_contains(
        ibl["live_proof"],
        {
            "status": "passed",
            "run_id": "20260715T173301Z-4eefe86a",
            "config_sha256": ("be105e5d66291a6cb8b21b7f92f3802fb1cc3b36bd5fc02a7f871332df68198f"),
            "run_manifest_sha256": (
                "f8d73dda365f02ffedf336d1b5d25c4ee586e9133bce583bd18a30a0e3ff6a90"
            ),
            "family_count": 6,
            "variants_per_family": 2,
            "terminal_family_count": 6,
            "accepted_dossier_stack_count": 6,
            "mixed_family_count": 1,
            "run_used_resume": False,
            "planning_only": True,
        },
    )
    _assert_mapping_contains(
        nlb["live_proof"],
        {
            "status": "passed",
            "run_id": "20260715T182133Z-ec7b6cde",
            "config_sha256": ("8a6674564fd455a4c5d9def8dfec623abbe5f19e9f9d42625b3b5046d7b7a999"),
            "run_manifest_sha256": (
                "bf69416ff18dcda3478911b57400068169f75b5e8ed8a94f5e35fee85f95abf2"
            ),
            "family_count": 6,
            "variants_per_family": 2,
            "terminal_family_count": 6,
            "accepted_dossier_stack_count": 5,
            "validation_warning_family_count": 1,
            "run_used_resume": False,
            "planning_only": True,
        },
    )
    _assert_mapping_contains(
        nlb["paperbank_import"],
        {
            "status": "receipt_bound_exact_reuse",
            "source_demo": "ibl-brain-wide-map",
            "source_run_id": "20260715T173301Z-4eefe86a",
            "source_paper_half_receipt_sha256": PAPER_HALF_RECEIPT_SHA256,
            "import_receipt_sha256": PAPERBANK_IMPORT_RECEIPT_SHA256,
            "public_provenance_path": "artifacts/provenance/paperbank_import.yaml",
            "absolute_source_path_persisted": False,
        },
    )

    _assert_mapping_contains(
        ibl["presentation"],
        {
            "status": "deterministic_replay_from_sealed_scientific_run",
            "runtime_commit": "f7edb2151e83f5d096a007476b01c7a5f17bfd54",
            "pair_output_set_sha256": (
                "350cfa04d71361762b85cfb291b374e620a514c1689e3f525cab43e549cf7c62"
            ),
            "output_set_sha256": (
                "577e3728150e7b07a842b4588af886ed9c014eef2c0afa4bcc3af29891237970"
            ),
            "pattern_detailed_sha256": SHARED_PATTERN_DETAILED_SHA256,
            "question_families_detailed_sha256": (
                "1024364450596dc709314366def50b7f6316dd0bfd8a36e333aecc69e73c6895"
            ),
            "detailed_page_count": 8,
            "scientific_pair_reexecuted": False,
            "detailed_present_in_original_invocation": False,
        },
    )
    _assert_mapping_contains(
        nlb["presentation"],
        {
            "status": "deterministic_replay_from_sealed_scientific_run",
            "runtime_commit": "f7edb2151e83f5d096a007476b01c7a5f17bfd54",
            "pair_output_set_sha256": (
                "350cfa04d71361762b85cfb291b374e620a514c1689e3f525cab43e549cf7c62"
            ),
            "output_set_sha256": (
                "85a1be4bbda90976cbda422401ff56302bab9f4f98ca883f07dadddab158013c"
            ),
            "pattern_detailed_sha256": SHARED_PATTERN_DETAILED_SHA256,
            "question_families_detailed_sha256": (
                "b6db73f98ffb9ec157c3675846acceb3522ffae93bded50f616176ac2a0695ae"
            ),
            "detailed_page_count": 8,
            "scientific_pair_reexecuted": False,
            "detailed_present_in_original_invocation": False,
        },
    )


def test_public_demo_artifact_inventories_exactly_match_the_curated_files() -> None:
    expected_showcases = {"ibl": ["family-002"], "nlb": ["family-006"]}
    selected_count = 0
    for demo_id in ("ibl", "nlb"):
        manifest = _load_demo_manifest(demo_id)
        artifacts = manifest["artifacts"]
        artifact_root = _demo_root() / demo_id / artifacts["root"]
        inventory = artifacts["sanitized_inventory"]
        paths = [item["path"] for item in inventory]

        assert artifacts["status"] == "curated"
        assert artifacts["root"] == "artifacts"
        assert artifacts["file_count"] == len(inventory) == 43
        assert artifacts["showcase_family_ids"] == expected_showcases[demo_id]
        assert artifacts["showcase_selection_status"] == "operator_selected"
        selected_count += len(artifacts["showcase_family_ids"])
        assert re.fullmatch(r"[0-9a-f]{64}", artifacts["inventory_sha256"])
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
    assert selected_count in {1, 2}
    assert selected_count == 2


def test_public_questions_index_covers_all_families_variants_and_resolves_links() -> None:
    questions_path = _demo_root() / "QUESTIONS.md"
    text = questions_path.read_text(encoding="utf-8")

    assert len(re.findall(r"^###\s+\d+\.\s+", text, re.M)) == 12
    assert len(re.findall(r"^[12]\.\s+\[[^\]]+\]\(", text, re.M)) == 24
    assert len(re.findall(r"questions/question_families_detailed\.md#family-", text)) == 12
    assert len(re.findall(r"questions/question_families_detailed\.md#variant-", text)) == 24

    root = _demo_root().resolve()
    for destination, fragment in _local_markdown_links(questions_path):
        assert destination.is_relative_to(root), destination
        assert destination.is_file(), destination
        if fragment:
            assert fragment in _github_heading_anchors(destination), (destination, fragment)


def test_public_demo_outcome_boundaries_preserve_mixed_and_warning_families() -> None:
    questions = (_demo_root() / "QUESTIONS.md").read_text(encoding="utf-8").lower()
    assert "mixed family" in questions
    assert "rejected_operationalization_failure" in questions
    assert "accepted_requires_new_skill" in questions
    assert "validation warning" in questions
    assert "no accepted-plan authority" in questions

    ibl_mixed = (
        (
            _demo_root()
            / "ibl"
            / "artifacts"
            / "families"
            / "input-to-choice-dynamics"
            / "dossier_detailed.md"
        )
        .read_text(encoding="utf-8")
        .lower()
    )
    assert "mixed family" in ibl_mixed
    assert "no refined question earned accepted-plan authority" in ibl_mixed

    nlb_warning = (
        (
            _demo_root()
            / "nlb"
            / "artifacts"
            / "families"
            / "preparatory-operating-regimes"
            / "dossier_detailed.md"
        )
        .read_text(encoding="utf-8")
        .lower()
    )
    for required in ("validation warning", "provisional / degraded", "no accepted-plan authority"):
        assert required in nlb_warning
