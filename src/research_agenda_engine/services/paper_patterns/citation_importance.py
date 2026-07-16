from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...assets import resolve_asset
from ...provenance import stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas.cited_literature import (
    CitationImportanceSelection,
    CitationImportanceSelectionItem,
    CitationSelectionPolicy,
    CitationSelectionStatus,
    PaperLocalLiteratureContext,
    PaperLocalLiteratureReviewStatus,
)
from ...schemas.paper_case import PaperCase

# Legacy fixed-count selector (10-15). FROZEN for the 15-paper EXPERT baseline — do NOT repoint it.
CITATION_IMPORTANCE_SELECTOR_PROMPT_VERSION = "citation_importance_selector/v2"
# Product evidence-driven selector (count is whatever the evidence supports; may be <10; thin support →
# insufficient_evidence). The serious/latest version of the family.
CITATION_IMPORTANCE_SELECTOR_PRODUCT_PROMPT_VERSION = "citation_importance_selector/v3"


class _CitationImportanceModelOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selection_id: str = ""
    paper_case_id: str = ""
    selection_status: CitationSelectionStatus = CitationSelectionStatus.SELECTED
    all_input_cited_work_ids: list[str] = Field(default_factory=list)
    selected_cited_work_ids: list[str] = Field(default_factory=list)
    selection_size_requested: int = 15
    selection_size_actual: int = 0
    provider_id: str = ""
    model_id: str = ""
    prompt_version: str = ""
    input_digest: str = ""
    items: list[CitationImportanceSelectionItem] = Field(default_factory=list)
    failure_reason: str = ""


def select_key_citations(
    provider: StructuredModelProvider,
    *,
    paper_case: PaperCase,
    literature_context: PaperLocalLiteratureContext,
    prompt_path: Path | None = None,
    max_prompt_chars: int = 120_000,
    selection_size_requested: int = 15,
) -> PaperLocalLiteratureContext:
    prompt = (prompt_path or _default_prompt_path()).read_text(encoding="utf-8")
    payload = _selection_payload(
        paper_case=paper_case,
        literature_context=literature_context,
        selection_size_requested=selection_size_requested,
    )
    user_prompt = json.dumps(payload, ensure_ascii=False, indent=2)
    input_digest = stable_hash({"system": prompt, "user": payload})
    if len(prompt) + len(user_prompt) > max_prompt_chars:
        selection = CitationImportanceSelection(
            selection_id=f"citation-selection-{literature_context.paper_case_id}-{input_digest[:12]}",
            paper_case_id=literature_context.paper_case_id,
            selection_status=CitationSelectionStatus.CONTEXT_TOO_LARGE,
            all_input_cited_work_ids=[
                work.cited_work_id for work in literature_context.cited_works
            ],
            selected_cited_work_ids=[],
            selection_size_requested=selection_size_requested,
            selection_size_actual=0,
            provider_id=provider.provider_name,
            model_id=provider.model_name,
            prompt_version=CITATION_IMPORTANCE_SELECTOR_PROMPT_VERSION,
            input_digest=input_digest,
            failure_reason="full all-citation selector prompt exceeded max_prompt_chars",
        )
        return _replace_selection(literature_context, selection)

    try:
        model_output = provider.generate_structured(
            system_prompt=prompt,
            user_prompt=user_prompt,
            output_model=_CitationImportanceModelOutput,
        )
        return _context_from_model_output(
            provider=provider,
            literature_context=literature_context,
            model_output=model_output,
            input_digest=input_digest,
            selection_size_requested=selection_size_requested,
        )
    except Exception as exc:
        return _repair_or_fail_selection(
            provider=provider,
            prompt=prompt,
            payload=payload,
            literature_context=literature_context,
            validation_error=str(exc),
            selection_size_requested=selection_size_requested,
        )


def select_key_citations_product(
    provider: StructuredModelProvider,
    *,
    paper_case: PaperCase,
    literature_context: PaperLocalLiteratureContext,
    prompt_path: Path | None = None,
    max_prompt_chars: int = 120_000,
) -> PaperLocalLiteratureContext:
    """Product evidence-driven citation selection (``citation_importance_selector/v3``).

    Unlike the frozen legacy ``select_key_citations`` (fixed 10-15), the count is whatever the evidence
    supports and MAY be fewer than 10 — so the citation gate's ``revise`` can converge on the defensible
    subset. If NO cited work has defensible question-forming support, the selection is the honest
    ``insufficient_evidence`` terminal (a scientific terminal, NOT an infrastructure failure) — enforced
    in code from an empty selection, not taken on the model's say-so.
    """
    version = CITATION_IMPORTANCE_SELECTOR_PRODUCT_PROMPT_VERSION
    prompt = (prompt_path or _product_prompt_path()).read_text(encoding="utf-8")
    payload = _product_selection_payload(
        paper_case=paper_case, literature_context=literature_context
    )
    user_prompt = json.dumps(payload, ensure_ascii=False, indent=2)
    input_digest = stable_hash({"system": prompt, "user": payload})
    size_hint = max(1, len(literature_context.cited_works))
    if len(prompt) + len(user_prompt) > max_prompt_chars:
        return _replace_selection(
            literature_context,
            _terminal_selection(
                literature_context=literature_context,
                provider=provider,
                status=CitationSelectionStatus.CONTEXT_TOO_LARGE,
                input_digest=input_digest,
                size_hint=size_hint,
                version=version,
                failure_reason="product selector prompt exceeded max_prompt_chars",
            ),
        )
    try:
        model_output = provider.generate_structured(
            system_prompt=prompt,
            user_prompt=user_prompt,
            output_model=_CitationImportanceModelOutput,
        )
    except Exception as exc:
        return _replace_selection(
            literature_context,
            _failed_selection(
                provider=provider,
                literature_context=literature_context,
                input_digest=input_digest,
                selection_size_requested=size_hint,
                failure_reason=f"product selection failed: {exc}",
                prompt_version=version,
            ),
        )
    if (
        not model_output.selected_cited_work_ids
        or model_output.selection_status == CitationSelectionStatus.INSUFFICIENT_EVIDENCE
    ):
        return _replace_selection(
            literature_context,
            _terminal_selection(
                literature_context=literature_context,
                provider=provider,
                status=CitationSelectionStatus.INSUFFICIENT_EVIDENCE,
                input_digest=input_digest,
                size_hint=size_hint,
                version=version,
                failure_reason=(
                    model_output.failure_reason
                    or "no cited work had defensible question-forming support"
                ),
            ),
        )
    return _context_from_model_output(
        provider=provider,
        literature_context=literature_context,
        model_output=model_output,
        input_digest=input_digest,
        selection_size_requested=size_hint,
        prompt_version=version,
        selection_policy=CitationSelectionPolicy.EVIDENCE_DRIVEN,
    )


def _terminal_selection(
    *,
    literature_context: PaperLocalLiteratureContext,
    provider: StructuredModelProvider,
    status: CitationSelectionStatus,
    input_digest: str,
    size_hint: int,
    version: str,
    failure_reason: str,
) -> CitationImportanceSelection:
    return CitationImportanceSelection(
        selection_id=f"citation-selection-{literature_context.paper_case_id}-{input_digest[:12]}",
        paper_case_id=literature_context.paper_case_id,
        selection_status=status,
        selection_policy=CitationSelectionPolicy.EVIDENCE_DRIVEN,
        all_input_cited_work_ids=[work.cited_work_id for work in literature_context.cited_works],
        selected_cited_work_ids=[],
        selection_size_requested=size_hint,
        selection_size_actual=0,
        provider_id=provider.provider_name,
        model_id=provider.model_name,
        prompt_version=version,
        input_digest=input_digest,
        failure_reason=failure_reason[:1000],
    )


def _product_selection_payload(
    *,
    paper_case: PaperCase,
    literature_context: PaperLocalLiteratureContext,
) -> dict:
    payload = _selection_payload(
        paper_case=paper_case,
        literature_context=literature_context,
        selection_size_requested=max(1, len(literature_context.cited_works)),
    )
    payload["prompt_version"] = CITATION_IMPORTANCE_SELECTOR_PRODUCT_PROMPT_VERSION
    payload["selection_instruction"] = (
        "Select ONLY the cited works with defensible question-forming support. The count is whatever "
        "the evidence supports and MAY be fewer than 10; give each an explicit role + evidence. If NO "
        "cited work has defensible support, return an empty selection (insufficient_evidence)."
    )
    payload["selection_size_rule"] = "evidence_driven"
    return payload


def _context_from_model_output(
    *,
    provider: StructuredModelProvider,
    literature_context: PaperLocalLiteratureContext,
    model_output: _CitationImportanceModelOutput,
    input_digest: str,
    selection_size_requested: int,
    prompt_version: str = CITATION_IMPORTANCE_SELECTOR_PROMPT_VERSION,
    selection_policy: CitationSelectionPolicy = CitationSelectionPolicy.FIXED_COUNT,
) -> PaperLocalLiteratureContext:
    selection = CitationImportanceSelection.model_validate(
        _selection_record(
            provider=provider,
            literature_context=literature_context,
            model_output=model_output,
            input_digest=input_digest,
            selection_size_requested=selection_size_requested,
            prompt_version=prompt_version,
            selection_policy=selection_policy,
        )
    )
    return _replace_selection(literature_context, selection)


def _selection_record(
    *,
    provider: StructuredModelProvider,
    literature_context: PaperLocalLiteratureContext,
    model_output: _CitationImportanceModelOutput,
    input_digest: str,
    selection_size_requested: int,
    prompt_version: str = CITATION_IMPORTANCE_SELECTOR_PROMPT_VERSION,
    selection_policy: CitationSelectionPolicy = CitationSelectionPolicy.FIXED_COUNT,
) -> dict:
    return {
        **model_output.model_dump(mode="python"),
        "selection_id": model_output.selection_id
        or f"citation-selection-{literature_context.paper_case_id}-{input_digest[:12]}",
        "paper_case_id": literature_context.paper_case_id,
        "selection_status": CitationSelectionStatus.SELECTED,
        "selection_policy": selection_policy,
        "all_input_cited_work_ids": [work.cited_work_id for work in literature_context.cited_works],
        "selection_size_requested": selection_size_requested,
        "selection_size_actual": len(model_output.selected_cited_work_ids),
        "provider_id": provider.provider_name,
        "model_id": provider.model_name,
        "prompt_version": prompt_version,
        "input_digest": input_digest,
    }


def _repair_or_fail_selection(
    *,
    provider: StructuredModelProvider,
    prompt: str,
    payload: dict,
    literature_context: PaperLocalLiteratureContext,
    validation_error: str,
    selection_size_requested: int,
) -> PaperLocalLiteratureContext:
    repair_payload = {
        "repair_instruction": (
            "Return a corrected CitationImportanceSelection. Use only allowed cited_work_ids. "
            "If an item is central/supporting and context IDs exist for that cited work, include "
            "one or more allowed evidence_context_ids for that same cited work."
        ),
        "validation_error": validation_error,
        "allowed_cited_work_ids": payload["all_cited_work_ids"],
        "available_evidence_context_ids_by_cited_work": payload[
            "available_evidence_context_ids_by_cited_work"
        ],
        "selection_size_rule": (
            "If there are at least 10 cited works, select 10-15. If fewer than 10, select all."
        ),
        "original_payload": payload,
    }
    repair_user_prompt = json.dumps(repair_payload, ensure_ascii=False, indent=2)
    repair_digest = stable_hash({"system": prompt, "repair": repair_payload})
    try:
        repaired_output = provider.generate_structured(
            system_prompt=prompt,
            user_prompt=repair_user_prompt,
            output_model=_CitationImportanceModelOutput,
        )
        return _context_from_model_output(
            provider=provider,
            literature_context=literature_context,
            model_output=repaired_output,
            input_digest=repair_digest,
            selection_size_requested=selection_size_requested,
        )
    except (ValidationError, ValueError, RuntimeError) as exc:
        return _replace_selection(
            literature_context,
            _failed_selection(
                provider=provider,
                literature_context=literature_context,
                input_digest=repair_digest,
                selection_size_requested=selection_size_requested,
                failure_reason=f"selection validation failed and repair failed: {exc}",
            ),
        )


def _failed_selection(
    *,
    provider: StructuredModelProvider,
    literature_context: PaperLocalLiteratureContext,
    input_digest: str,
    selection_size_requested: int,
    failure_reason: str,
    prompt_version: str = CITATION_IMPORTANCE_SELECTOR_PROMPT_VERSION,
) -> CitationImportanceSelection:
    return CitationImportanceSelection(
        selection_id=f"citation-selection-{literature_context.paper_case_id}-{input_digest[:12]}",
        paper_case_id=literature_context.paper_case_id,
        selection_status=CitationSelectionStatus.MODEL_FAILED,
        all_input_cited_work_ids=[work.cited_work_id for work in literature_context.cited_works],
        selected_cited_work_ids=[],
        selection_size_requested=selection_size_requested,
        selection_size_actual=0,
        provider_id=provider.provider_name,
        model_id=provider.model_name,
        prompt_version=prompt_version,
        input_digest=input_digest,
        failure_reason=failure_reason[:1000],
    )


def _selection_payload(
    *,
    paper_case: PaperCase,
    literature_context: PaperLocalLiteratureContext,
    selection_size_requested: int,
) -> dict:
    context_ids_by_work: dict[str, list[str]] = {}
    for context in literature_context.citation_contexts:
        context_ids_by_work.setdefault(context.cited_work_id, []).append(context.context_id)
    return {
        "prompt_version": CITATION_IMPORTANCE_SELECTOR_PROMPT_VERSION,
        "selection_instruction": (
            "Select the 10-15 cited works most important to how the source paper formed "
            "its scientific question. The cited_works list is complete; select only from it."
        ),
        "selection_size_requested": selection_size_requested,
        "source_paper": {
            "paper_case_id": paper_case.paper_case_id,
            "citation": paper_case.citation,
            "paper_type": paper_case.paper_type,
            "dataset_description": paper_case.dataset_description.model_dump(mode="json"),
            "knowledge_state": paper_case.knowledge_state.model_dump(mode="json"),
            "scientific_question": paper_case.scientific_question.model_dump(mode="json"),
            "question_design": paper_case.question_design.model_dump(mode="json"),
            "formation_trace": (
                paper_case.formation_trace.model_dump(mode="json")
                if paper_case.formation_trace is not None
                else None
            ),
        },
        "all_cited_work_ids": [work.cited_work_id for work in literature_context.cited_works],
        "cited_works": [work.model_dump(mode="json") for work in literature_context.cited_works],
        "citation_contexts": [
            context.model_dump(mode="json") for context in literature_context.citation_contexts
        ],
        "available_evidence_context_ids_by_cited_work": context_ids_by_work,
    }


def _replace_selection(
    context: PaperLocalLiteratureContext,
    selection: CitationImportanceSelection,
) -> PaperLocalLiteratureContext:
    review_status = (
        PaperLocalLiteratureReviewStatus.AGENT_SELECTED
        if selection.selection_status == CitationSelectionStatus.SELECTED
        else context.review_status
    )
    return PaperLocalLiteratureContext.model_validate(
        {
            **context.model_dump(mode="python", exclude={"importance_selection", "review_status"}),
            "importance_selection": selection,
            "review_status": review_status,
        }
    )


def _default_prompt_path() -> Path:
    return resolve_asset(
        Path("prompts") / Path(CITATION_IMPORTANCE_SELECTOR_PROMPT_VERSION).with_suffix(".md")
    )


def _product_prompt_path() -> Path:
    return resolve_asset(
        Path("prompts")
        / Path(CITATION_IMPORTANCE_SELECTOR_PRODUCT_PROMPT_VERSION).with_suffix(".md")
    )
