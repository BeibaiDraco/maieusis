"""Zero-paid, fail-closed PaperBank reuse across otherwise independent runs."""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ...io import dump_data, load_model
from ...provenance import sha256_file, stable_hash
from ...providers.models.policy import model_versions_accept
from ...schemas.maieusis_project_config import MaieusisProjectConfig
from ...schemas.paperbank_import import PaperBankImportReceipt
from ...schemas.run_manifest import ProductProcessingState, RunStage
from ...schemas.stage_receipt import StageReceipt, StageStatus
from .resume import (
    PAPER_HALF_IMPLEMENTATION_VERSION,
    STAGE_PAPER_HALF,
    PaperHalfStageOutput,
    compute_paper_half_input_digests,
    stage_config_version,
    stage_model_versions,
    stage_prompt_versions,
)
from .run_envelope import RunContext, set_stage_state
from .run_layout import RunPaths, read_stage_receipt, write_stage_receipt


class PaperBankImportError(ValueError):
    """The requested source cannot prove exact, safe paper-half reuse."""


@dataclass(frozen=True)
class VerifiedPaperBankImport:
    source_root: Path
    source_receipt: StageReceipt
    source_receipt_sha256: str
    stage_output: PaperHalfStageOutput
    output_digests: dict[str, str]


def _owned_output_path(raw: str) -> PurePosixPath:
    rel = PurePosixPath(raw)
    if rel.is_absolute() or not rel.parts or "." in rel.parts or ".." in rel.parts:
        raise PaperBankImportError(f"paper-half receipt contains unsafe output path {raw!r}")
    allowed = (
        raw == "stage_outputs/paper-half.yaml"
        or raw == "corpus/question_pattern_manifest.yaml"
        or raw.startswith("corpus/patterns/")
    )
    if not allowed:
        raise PaperBankImportError(
            f"paper-half receipt claims non-PaperBank output {raw!r}; refusing cross-run import"
        )
    return rel


def _source_file(source_root: Path, rel: PurePosixPath) -> Path:
    root = source_root.resolve(strict=True)
    candidate = source_root.joinpath(*rel.parts)
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise PaperBankImportError(f"source output {rel.as_posix()!r} is missing") from exc
    expected = root.joinpath(*rel.parts)
    if candidate.is_symlink() or resolved != expected or not resolved.is_relative_to(root):
        raise PaperBankImportError(
            f"source output {rel.as_posix()!r} is external or symlink-aliased"
        )
    if not resolved.is_file():
        raise PaperBankImportError(f"source output {rel.as_posix()!r} is not a regular file")
    return resolved


def validate_paperbank_import(config: MaieusisProjectConfig) -> VerifiedPaperBankImport | None:
    """Validate the complete reuse closure without constructing a provider or writing a file."""
    request = config.paperbank.import_from_run
    if request is None:
        return None

    source_root = Path(request.source_run_root)
    if not source_root.is_dir():
        raise PaperBankImportError(f"PaperBank source run does not exist: {source_root}")
    source_paths = RunPaths(root=source_root)
    receipt_path = source_paths.receipts / "paper-half.yaml"
    if not receipt_path.is_file():
        raise PaperBankImportError("PaperBank source has no paper-half stage receipt")
    actual_receipt_sha = sha256_file(receipt_path)
    if actual_receipt_sha != request.expected_receipt_sha256:
        raise PaperBankImportError(
            "PaperBank source receipt SHA-256 does not match expected_receipt_sha256"
        )
    source_receipt = read_stage_receipt(source_paths, STAGE_PAPER_HALF)
    if source_receipt is None or source_receipt.status != StageStatus.COMPLETE:
        raise PaperBankImportError("PaperBank source paper half is not complete")

    expected_inputs = compute_paper_half_input_digests(config, None)
    if not expected_inputs:
        raise PaperBankImportError("PaperBank import requires at least one current inbox PDF")
    if source_receipt.input_digests != expected_inputs:
        raise PaperBankImportError(
            "PaperBank source PDF filename/SHA-256 set does not match the current inbox"
        )
    expected_config = stage_config_version(config, STAGE_PAPER_HALF)
    if source_receipt.config_version != expected_config:
        raise PaperBankImportError("PaperBank source parser/config/implementation digest differs")
    expected_models = stage_model_versions(config, STAGE_PAPER_HALF)
    if not model_versions_accept(source_receipt.model_versions, expected_models):
        raise PaperBankImportError("PaperBank source extraction/pattern/reviewer models differ")
    expected_prompts = stage_prompt_versions(STAGE_PAPER_HALF)
    if source_receipt.prompt_versions != expected_prompts:
        raise PaperBankImportError("PaperBank source active prompt versions differ")

    output_digests = dict(sorted(source_receipt.output_digests.items()))
    if set(source_receipt.output_paths) != set(output_digests):
        raise PaperBankImportError("PaperBank source receipt output path/digest inventory differs")
    required = {
        "stage_outputs/paper-half.yaml",
        "corpus/question_pattern_manifest.yaml",
    }
    if not required.issubset(output_digests) or not any(
        rel.startswith("corpus/patterns/") for rel in output_digests
    ):
        raise PaperBankImportError(
            "PaperBank source receipt lacks its required typed output closure"
        )
    for raw, expected_digest in output_digests.items():
        source_file = _source_file(source_root, _owned_output_path(raw))
        if sha256_file(source_file) != expected_digest:
            raise PaperBankImportError(f"PaperBank source output digest mismatch: {raw}")

    stage_output = load_model(
        source_root / "stage_outputs" / "paper-half.yaml", PaperHalfStageOutput
    )
    if not stage_output.accepted or not stage_output.patterns:
        raise PaperBankImportError("PaperBank source has no accepted papers or reviewed patterns")
    if stable_hash(stage_output.accepted) != stable_hash(stage_output.gate_result.accepted):
        raise PaperBankImportError("PaperBank source stage output has inconsistent accepted papers")
    pdf_digests = set(expected_inputs.values())
    unmatched = sorted(
        item.paper_case.paper_case_id
        for item in stage_output.accepted
        if item.paper_case.source_sha256 not in pdf_digests
    )
    if unmatched:
        raise PaperBankImportError(
            "PaperBank source PaperCases are not bound to the current PDF bytes: "
            + ", ".join(unmatched)
        )
    return VerifiedPaperBankImport(
        source_root=source_root,
        source_receipt=source_receipt,
        source_receipt_sha256=actual_receipt_sha,
        stage_output=stage_output,
        output_digests=output_digests,
    )


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=destination.parent, prefix=f".{destination.name}.")
    os.close(fd)
    temp = Path(temp_name)
    try:
        shutil.copyfile(source, temp)
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)


def import_paperbank_from_run(
    config: MaieusisProjectConfig, context: RunContext
) -> PaperHalfStageOutput:
    """Copy only receipt-owned typed PaperBank outputs and persist target-side provenance."""
    verified = validate_paperbank_import(config)
    if verified is None:
        raise PaperBankImportError("paperbank.import_from_run is not configured")
    try:
        if context.paths.root.resolve() == verified.source_root.resolve():
            raise PaperBankImportError("PaperBank source and target run roots must differ")
    except OSError as exc:
        raise PaperBankImportError("PaperBank source/target root could not be resolved") from exc

    for raw, expected_digest in verified.output_digests.items():
        rel = _owned_output_path(raw)
        destination = context.paths.root.joinpath(*rel.parts)
        if destination.exists():
            raise PaperBankImportError(f"PaperBank target output already exists: {raw}")
        source = _source_file(verified.source_root, rel)
        _atomic_copy(source, destination)
        if sha256_file(destination) != expected_digest:
            raise PaperBankImportError(f"PaperBank target copy digest mismatch: {raw}")

    receipt_path = write_stage_receipt(context.paths, verified.source_receipt)
    set_stage_state(
        context,
        RunStage.PAPER_HALF,
        ProductProcessingState.PRODUCED,
        receipt_path=receipt_path.relative_to(context.paths.root).as_posix(),
    )
    import_receipt = PaperBankImportReceipt(
        source_run_id=verified.source_root.name,
        source_paper_half_receipt_sha256=verified.source_receipt_sha256,
        source_input_digests=verified.source_receipt.input_digests,
        imported_output_digests=verified.output_digests,
        parser=config.paperbank.parser,
        implementation_version=PAPER_HALF_IMPLEMENTATION_VERSION,
        config_version=verified.source_receipt.config_version,
        prompt_versions=verified.source_receipt.prompt_versions,
        model_versions=verified.source_receipt.model_versions,
    )
    dump_data(import_receipt, context.paths.root / "imports" / "paperbank.yaml")
    return verified.stage_output
