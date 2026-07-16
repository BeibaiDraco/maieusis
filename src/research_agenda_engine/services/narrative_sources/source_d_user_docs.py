"""Source D — coarse facts from the USER's own description docs.

Highest-trust of the four sources (the user is the domain expert on their own dataset), but STILL
coarsened + firewalled before the Questioner. It reuses Source A's v4 extraction + shared import
firewall, fed the user's ``seed.docs`` instead of fetched documentation — no agent spawn.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from pathlib import Path

from ...provenance import sha256_file
from ...providers.models.base import StructuredModelProvider
from ...schemas.coarse_dataset_facts import CoarseUserDescriptionFacts
from ...schemas.dataset_narrative import DatasetNarrativeSourceType
from ...schemas.dataset_seed import DatasetSeed
from ..context.dataset_narrative import (
    ProposalSourceExcerpt,
    build_dataset_narrative_source_packet,
)
from ..paper_ingest.parsing import PdfParsingError, PopplerTextPdfProvider
from .coarse_facts_import import import_coarse_facts
from .source_a_documentation import extract_coarse_story_from_packet

USER_DESCRIPTION_SOURCE_LOCATOR_SCHEME = "user-provided-description"
_MAX_USER_DOC_CHARS = 4000


class UnreadableUserDocumentationError(ValueError):
    """Configured Source-D files yielded no readable text; other sources may still proceed."""


def user_description_source_locator(dataset_id: str) -> str:
    return f"{USER_DESCRIPTION_SOURCE_LOCATOR_SCHEME}://{dataset_id}"


def build_user_description_coarse_facts(
    *,
    seed: DatasetSeed,
    provider: StructuredModelProvider,
    max_prompt_chars: int = 250_000,
) -> CoarseUserDescriptionFacts:
    """Extract coarse facts from the user's ``seed.docs`` (Source D). Raises if no readable doc."""
    excerpts = _user_doc_excerpts(seed.docs, dataset_id=seed.dataset_id)
    if not excerpts:
        raise UnreadableUserDocumentationError(
            "Source D requires at least one readable user description doc in seed.docs"
        )
    packet = build_dataset_narrative_source_packet(
        dataset_id=seed.dataset_id, source_excerpts=excerpts
    )
    raw, source_ref_ids = extract_coarse_story_from_packet(
        packet=packet,
        provider=provider,
        dataset_id=seed.dataset_id,
        max_prompt_chars=max_prompt_chars,
    )
    return import_coarse_facts(
        raw,
        CoarseUserDescriptionFacts,
        provenance={
            "dataset_id": seed.dataset_id,
            "source_locator": user_description_source_locator(seed.dataset_id),
            "provider_id": provider.provider_id,
            "model_id": getattr(provider, "model_name", ""),
            "source_ref_ids": source_ref_ids,
        },
        belt_context="user_description_coarse_facts(raw)",
    )


def _user_doc_excerpts(
    docs: list[Path], *, dataset_id: str = "configured"
) -> list[ProposalSourceExcerpt]:
    excerpts: list[ProposalSourceExcerpt] = []
    for index, doc in enumerate(docs):
        path = Path(doc)
        if not path.exists() or not path.is_file():
            continue
        text = _read_doc_text(path)
        if not text.strip():
            continue
        excerpts.append(
            ProposalSourceExcerpt(
                source_id=f"user-doc:{index}:{path.name}",
                source_type=DatasetNarrativeSourceType.EXPERT_NOTE,
                title=path.name,
                locator=f"{user_description_source_locator(dataset_id)}/{index}/{path.name}",
                excerpt=text[:_MAX_USER_DOC_CHARS],
                source_digest=sha256_file(path),
                section="user_provided_description",
                snippet_kind="user_description",
            )
        )
    return excerpts


def _read_doc_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            parsed = PopplerTextPdfProvider().parse(path, paper_id=f"user-doc-{path.stem}")
        except PdfParsingError:
            return ""
        return " ".join(page.text for page in parsed.pages if page.text.strip())
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
