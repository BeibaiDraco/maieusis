from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...io import dump_data, load_model
from ...provenance import stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas.cited_literature import PaperLocalLiteratureContext, literature_context_digest
from ...schemas.paper_case import PaperCase
from ...schemas.paper_ingest import ParsedPaper
from ..paper_patterns.citation_importance import select_key_citations_product
from .cited_abstracts import build_paper_local_literature_context
from .external_lookup import ProcessedPaperLookupProvider, SourceReferenceProvider


class PaperLocalLiteratureBuildConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    corpus_root: Path = Path("corpus")
    paper_ids: list[str] = Field(default_factory=list)
    select_key_citations: bool = False
    write_paper_case_links: bool = False
    min_local_reference_count: int = Field(default=10, ge=1)
    max_prompt_chars: int = Field(default=120_000, ge=1)


class PaperLocalLiteratureBuildItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_id: str
    paper_case_path: str = ""
    parsed_path: str = ""
    sidecar_artifact: str = ""
    reference_count: int = 0
    cited_work_count: int = 0
    citation_context_count: int = 0
    abstract_count: int = 0
    selection_status: str = "not_attempted"
    selected_count: int = 0
    paper_case_links_written: bool = False
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class PaperLocalLiteratureBuildManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    corpus_root: str
    select_key_citations: bool = False
    write_paper_case_links: bool = False
    item_count: int = 0
    sidecar_count: int = 0
    selected_count: int = 0
    failed_count: int = 0
    items: list[PaperLocalLiteratureBuildItem] = Field(default_factory=list)


def build_reviewed_paper_local_literature(
    *,
    config: PaperLocalLiteratureBuildConfig,
    lookup_providers: list[ProcessedPaperLookupProvider],
    source_reference_providers: list[SourceReferenceProvider],
    selection_provider: StructuredModelProvider | None = None,
) -> PaperLocalLiteratureBuildManifest:
    case_paths = _reviewed_case_paths(config.corpus_root, config.paper_ids)
    items: list[PaperLocalLiteratureBuildItem] = []
    for case_path in case_paths:
        items.append(
            _build_one(
                case_path=case_path,
                config=config,
                lookup_providers=lookup_providers,
                source_reference_providers=source_reference_providers,
                selection_provider=selection_provider,
            )
        )
    manifest = PaperLocalLiteratureBuildManifest(
        manifest_id=f"paper-local-literature-{stable_hash([item.model_dump(mode='json') for item in items])[:12]}",
        corpus_root=str(config.corpus_root),
        select_key_citations=config.select_key_citations,
        write_paper_case_links=config.write_paper_case_links,
        item_count=len(items),
        sidecar_count=sum(1 for item in items if item.sidecar_artifact),
        selected_count=sum(1 for item in items if item.selected_count > 0),
        failed_count=sum(1 for item in items if item.errors),
        items=items,
    )
    dump_data(
        manifest, config.corpus_root / "cited_literature" / "paper_local_literature_manifest.yaml"
    )
    return manifest


def _build_one(
    *,
    case_path: Path,
    config: PaperLocalLiteratureBuildConfig,
    lookup_providers: list[ProcessedPaperLookupProvider],
    source_reference_providers: list[SourceReferenceProvider],
    selection_provider: StructuredModelProvider | None,
) -> PaperLocalLiteratureBuildItem:
    paper_case = load_model(case_path, PaperCase)
    parsed_path = config.corpus_root / "parsed" / f"{paper_case.paper_case_id}.parsed.yaml"
    item = PaperLocalLiteratureBuildItem(
        paper_id=paper_case.paper_case_id,
        paper_case_path=str(case_path),
        parsed_path=str(parsed_path),
    )
    if not parsed_path.exists():
        return item.model_copy(update={"errors": [f"parsed artifact not found: {parsed_path}"]})

    try:
        parsed = load_model(parsed_path, ParsedPaper)
        context = build_paper_local_literature_context(
            parsed=parsed,
            paper_case=paper_case,
            lookup_providers=lookup_providers,
            source_reference_providers=source_reference_providers,
            min_local_reference_count=config.min_local_reference_count,
        )
        if config.select_key_citations:
            if selection_provider is None:
                return item.model_copy(update={"errors": ["selection provider is required"]})
            context = select_key_citations_product(
                selection_provider,
                paper_case=paper_case,
                literature_context=context,
                max_prompt_chars=config.max_prompt_chars,
            )
        sidecar_path = (
            config.corpus_root
            / "cited_literature"
            / f"{paper_case.paper_case_id}.paper_local_literature.yaml"
        )
        dump_data(context, sidecar_path)
        links_written = False
        if config.write_paper_case_links:
            _write_paper_case_links(case_path, paper_case, context)
            links_written = True
        return _item_from_context(
            item=item,
            context=context,
            sidecar_path=sidecar_path,
            paper_case_links_written=links_written,
        )
    except Exception as exc:
        return item.model_copy(update={"errors": [str(exc)]})


def _item_from_context(
    *,
    item: PaperLocalLiteratureBuildItem,
    context: PaperLocalLiteratureContext,
    sidecar_path: Path,
    paper_case_links_written: bool,
) -> PaperLocalLiteratureBuildItem:
    selection = context.importance_selection
    return item.model_copy(
        update={
            "sidecar_artifact": str(sidecar_path),
            "reference_count": len(context.raw_references),
            "cited_work_count": len(context.cited_works),
            "citation_context_count": len(context.citation_contexts),
            "abstract_count": sum(1 for work in context.cited_works if work.abstract),
            "selection_status": selection.selection_status.value if selection else "not_attempted",
            "selected_count": len(selection.selected_cited_work_ids) if selection else 0,
            "paper_case_links_written": paper_case_links_written,
            "warnings": context.warnings,
        }
    )


def _write_paper_case_links(
    case_path: Path, paper_case: PaperCase, context: PaperLocalLiteratureContext
) -> None:
    selection = context.importance_selection
    key_cited_work_ids = selection.selected_cited_work_ids if selection else []
    updated = PaperCase.model_validate(
        {
            **paper_case.model_dump(mode="python"),
            "local_literature_context_id": context.context_id,
            "local_literature_context_digest": literature_context_digest(context),
            "key_cited_work_ids": key_cited_work_ids,
        }
    )
    dump_data(updated, case_path)


def _reviewed_case_paths(corpus_root: Path, paper_ids: list[str]) -> list[Path]:
    reviewed_dir = corpus_root / "cases" / "reviewed"
    if paper_ids:
        paths = [reviewed_dir / f"{paper_id}.paper_case.yaml" for paper_id in paper_ids]
    else:
        paths = sorted(reviewed_dir.glob("*.paper_case.yaml"))
    return paths
