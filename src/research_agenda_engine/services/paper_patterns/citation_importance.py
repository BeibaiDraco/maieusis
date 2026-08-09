from __future__ import annotations

import json
from collections.abc import Sequence
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
        # CLIM-04: partition instead of dropping the whole paper's citation selection.
        #
        # Inside the same guard as the direct path below, and for the same measured reason. This
        # `return` sat OUTSIDE it, so a merged selection the destination schema refuses escaped the
        # function -- and two of the three product call sites are unguarded per-paper loops, so one
        # paper ended the whole run. That is verbatim the defect the comment below records as
        # already measured at 3 of 18 selections; the fix covered the direct path only.
        try:
            return _select_key_citations_product_partitioned(
                provider=provider,
                paper_case=paper_case,
                literature_context=literature_context,
                prompt=prompt,
                max_prompt_chars=max_prompt_chars,
                version=version,
                measured_chars=len(prompt) + len(user_prompt),
            )
        except (ValidationError, ValueError) as exc:
            return _replace_selection(
                literature_context,
                _failed_selection(
                    provider=provider,
                    literature_context=literature_context,
                    input_digest=input_digest,
                    selection_size_requested=size_hint,
                    prompt_version=version,
                    selection_policy=CitationSelectionPolicy.EVIDENCE_DRIVEN,
                    failure_reason=_strict_selection_failure_reason(
                        exc=exc,
                        literature_context=literature_context,
                        boundary="partitioned outer boundary",
                    ),
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
                failure_reason=(
                    "citation-importance provider call failed before a typed reply was available "
                    f"({type(exc).__name__}); inspect the operator capture for raw transport evidence"
                ),
                prompt_version=version,
                selection_policy=CitationSelectionPolicy.EVIDENCE_DRIVEN,
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
    try:
        return _context_from_model_output(
            provider=provider,
            literature_context=literature_context,
            model_output=model_output,
            input_digest=input_digest,
            selection_size_requested=size_hint,
            prompt_version=version,
            selection_policy=CitationSelectionPolicy.EVIDENCE_DRIVEN,
        )
    except (ValidationError, ValueError) as exc:
        # The provider answered, but the destination schema refused the typed reply. That is a
        # model/shape failure, not evidence that no citation mattered. Persist structural evidence
        # without copying the provider's raw values; the operator capture owns those bytes.
        return _replace_selection(
            literature_context,
            _failed_selection(
                provider=provider,
                literature_context=literature_context,
                input_digest=input_digest,
                selection_size_requested=size_hint,
                prompt_version=version,
                selection_policy=CitationSelectionPolicy.EVIDENCE_DRIVEN,
                failure_reason=_strict_selection_failure_reason(
                    exc=exc,
                    literature_context=literature_context,
                    boundary="direct strict rebuild",
                    selected_ids=model_output.selected_cited_work_ids,
                    items=model_output.items,
                ),
            ),
        )


def _subset_context(literature_context, subset: list):
    """A chunk's literature view: its cited works AND only those works' citation contexts.

    `model_copy(update={"cited_works": subset})` replaced the works and let every context ride
    along, so each chunk carried the WHOLE paper's contexts. Two consequences, both dormant only
    because regex extraction produced 54 contexts for 950 cited works (5.7%, mean 337 chars):

    - the context block is a FIXED FLOOR paid once per chunk, so denser contexts push a one-work
      chunk over the budget and terminate the paper CONTEXT_TOO_LARGE;
    - the model is shown context ids belonging to works outside its chunk, and an item that cites
      one survives the merge (which filters by `cited_work_id` only) and hits the schema's
      foreign-context check at `cited_literature.py:337`, which RAISES.

    Verified on `12-charlton-polvani-2007`: a one-work chunk carried all 4 of the paper's contexts,
    none of them that work's.
    """
    work_ids = {work.cited_work_id for work in subset}
    return literature_context.model_copy(
        update={
            "cited_works": subset,
            "citation_contexts": [
                context
                for context in literature_context.citation_contexts
                if context.cited_work_id in work_ids
            ],
        }
    )


def _select_key_citations_product_partitioned(
    *,
    provider: StructuredModelProvider,
    paper_case: PaperCase,
    literature_context: PaperLocalLiteratureContext,
    prompt: str,
    max_prompt_chars: int,
    version: str,
    measured_chars: int,
) -> PaperLocalLiteratureContext:
    """CLIM-04: deterministic within-budget partitioned selection with honest measurements.

    Cited works are split IN ORDER into the fewest greedy chunks whose rendered packet each fits
    the budget; the selector runs per chunk; selections merge into one selection whose additive
    partition fields carry the measurements. An irreducible single over-budget record and a
    per-chunk model failure both close honestly with the measurements in ``failure_reason`` —
    never a raised budget, never a silent drop.
    """

    def _chunk_chars(subset: list) -> int:
        subset_context = _subset_context(literature_context, subset)
        payload = _product_selection_payload(
            paper_case=paper_case, literature_context=subset_context
        )
        return len(prompt) + len(json.dumps(payload, ensure_ascii=False, indent=2))

    size_hint = max(1, len(literature_context.cited_works))
    chunks: list[list] = []
    current: list = []
    for work in literature_context.cited_works:
        candidate = [*current, work]
        if current and _chunk_chars(candidate) > max_prompt_chars:
            chunks.append(current)
            current = [work]
        else:
            current = candidate
    if current:
        chunks.append(current)
    for chunk in chunks:
        if len(chunk) == 1 and _chunk_chars(chunk) > max_prompt_chars:
            digest = stable_hash({"system": prompt, "irreducible": chunk[0].cited_work_id})
            return _replace_selection(
                literature_context,
                _terminal_selection(
                    literature_context=literature_context,
                    provider=provider,
                    status=CitationSelectionStatus.CONTEXT_TOO_LARGE,
                    input_digest=digest,
                    size_hint=size_hint,
                    version=version,
                    failure_reason=(
                        "irreducible single citation record exceeds the budget "
                        f"(record={chunk[0].cited_work_id}, measured={_chunk_chars(chunk)}, "
                        f"budget={max_prompt_chars}, full_packet={measured_chars})"
                    ),
                ),
            )

    part_digests: list[str] = []
    merged_ids: list[str] = []
    merged_items: list[CitationImportanceSelectionItem] = []
    for index, chunk in enumerate(chunks):
        subset_context = _subset_context(literature_context, chunk)
        payload = _product_selection_payload(
            paper_case=paper_case, literature_context=subset_context
        )
        part_digests.append(stable_hash({"system": prompt, "user": payload}))
        try:
            model_output = provider.generate_structured(
                system_prompt=prompt,
                user_prompt=json.dumps(payload, ensure_ascii=False, indent=2),
                output_model=_CitationImportanceModelOutput,
            )
        except Exception as exc:
            return _replace_selection(
                literature_context,
                _failed_selection(
                    provider=provider,
                    literature_context=literature_context,
                    input_digest=stable_hash({"system": prompt, "parts": part_digests}),
                    selection_size_requested=size_hint,
                    failure_reason=(
                        f"partitioned product selection failed on part {index + 1}/"
                        f"{len(chunks)} (measured={measured_chars}, "
                        f"budget={max_prompt_chars}, error={type(exc).__name__}); inspect the "
                        "operator capture for raw transport evidence"
                    ),
                    prompt_version=version,
                    selection_policy=CitationSelectionPolicy.EVIDENCE_DRIVEN,
                ),
            )
        chunk_ids = {work.cited_work_id for work in chunk}
        merged_ids.extend(
            work_id for work_id in model_output.selected_cited_work_ids if work_id in chunk_ids
        )
        # Keep only the evidence contexts that belong to the item's OWN work. The merge filters
        # ITEMS by cited_work_id and never looked inside them, so a stray id reached
        # `_replace_selection` -> the schema's foreign-context check at cited_literature.py:337,
        # which RAISES -- and this partitioned call returns before the guard at the direct path, in
        # a per-paper loop, so one paper killed the batch.
        own_contexts: dict[str, set[str]] = {}
        for context in subset_context.citation_contexts:
            own_contexts.setdefault(context.cited_work_id, set()).add(context.context_id)
        merged_items.extend(
            item.model_copy(
                update={
                    "evidence_context_ids": [
                        context_id
                        for context_id in item.evidence_context_ids
                        if context_id in own_contexts.get(item.cited_work_id, set())
                    ]
                }
            )
            for item in model_output.items
            if item.cited_work_id in chunk_ids
        )

    # Ranks must stay contiguous from 1 across the merged selection (schema invariant);
    # merge order is chunk order then in-chunk rank — deterministic.
    merged_items = [
        item.model_copy(update={"rank": position})
        for position, item in enumerate(merged_items, start=1)
    ]
    input_digest = stable_hash({"system": prompt, "parts": part_digests})
    if not merged_ids:
        terminal = _terminal_selection(
            literature_context=literature_context,
            provider=provider,
            status=CitationSelectionStatus.INSUFFICIENT_EVIDENCE,
            input_digest=input_digest,
            size_hint=size_hint,
            version=version,
            failure_reason=(
                "no cited work had defensible question-forming support in any partition "
                f"(partitions={len(chunks)}, measured={measured_chars}, "
                f"budget={max_prompt_chars})"
            ),
        )
        terminal = terminal.model_copy(
            update={
                "partition_count": len(chunks),
                "partition_measured_chars": measured_chars,
                "partition_budget_chars": max_prompt_chars,
            }
        )
        return _replace_selection(literature_context, terminal)
    try:
        selection = CitationImportanceSelection(
            selection_id=(
                f"citation-selection-{literature_context.paper_case_id}-{input_digest[:12]}"
            ),
            paper_case_id=literature_context.paper_case_id,
            selection_status=CitationSelectionStatus.SELECTED,
            selection_policy=CitationSelectionPolicy.EVIDENCE_DRIVEN,
            all_input_cited_work_ids=[
                work.cited_work_id for work in literature_context.cited_works
            ],
            selected_cited_work_ids=merged_ids,
            selection_size_requested=size_hint,
            selection_size_actual=len(merged_ids),
            provider_id=provider.provider_name,
            model_id=provider.model_name,
            prompt_version=version,
            input_digest=input_digest,
            items=merged_items,
            partition_count=len(chunks),
            partition_measured_chars=measured_chars,
            partition_budget_chars=max_prompt_chars,
        )
        return _replace_selection(literature_context, selection)
    except (ValidationError, ValueError) as exc:
        failed = _failed_selection(
            provider=provider,
            literature_context=literature_context,
            input_digest=input_digest,
            selection_size_requested=size_hint,
            prompt_version=version,
            selection_policy=CitationSelectionPolicy.EVIDENCE_DRIVEN,
            failure_reason=_strict_selection_failure_reason(
                exc=exc,
                literature_context=literature_context,
                boundary="partitioned strict rebuild",
                selected_ids=merged_ids,
                items=merged_items,
            ),
        ).model_copy(
            update={
                "partition_count": len(chunks),
                "partition_measured_chars": measured_chars,
                "partition_budget_chars": max_prompt_chars,
            }
        )
        return _replace_selection(literature_context, failed)


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
    selection_policy: CitationSelectionPolicy = CitationSelectionPolicy.FIXED_COUNT,
) -> CitationImportanceSelection:
    return CitationImportanceSelection(
        selection_id=f"citation-selection-{literature_context.paper_case_id}-{input_digest[:12]}",
        paper_case_id=literature_context.paper_case_id,
        selection_status=CitationSelectionStatus.MODEL_FAILED,
        selection_policy=selection_policy,
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


def _strict_selection_failure_reason(
    *,
    exc: ValidationError | ValueError,
    literature_context: PaperLocalLiteratureContext,
    boundary: str,
    selected_ids: Sequence[str] | None = None,
    items: Sequence[CitationImportanceSelectionItem] | None = None,
) -> str:
    """Safe structural evidence for a typed reply the destination schema refused.

    Pydantic's raw error can contain the offending input and provider-authored prose. Persist only
    location/type pairs plus counts and boolean shape checks; the opt-in capture owns raw bytes.
    """
    issue_signatures: list[str] = []
    if isinstance(exc, ValidationError):
        for issue in exc.errors(
            include_url=False,
            include_context=False,
            include_input=False,
        )[:8]:
            location = ".".join(str(part) for part in issue.get("loc", ())) or "model"
            issue_signatures.append(f"{location}:{issue.get('type', 'unknown')}")
    if not issue_signatures:
        issue_signatures.append(type(exc).__name__)
    parts = [
        f"citation-importance reply failed at {boundary}",
        "validation_errors=" + ",".join(issue_signatures),
    ]
    if selected_ids is not None and items is not None:
        parts.append(
            _selection_reply_shape(
                selected_ids=selected_ids,
                items=items,
                literature_context=literature_context,
            )
        )
    else:
        parts.append("reply_shape=unavailable_at_outer_boundary")
    return "; ".join(parts)


def _selection_reply_shape(
    *,
    selected_ids: Sequence[str],
    items: Sequence[CitationImportanceSelectionItem],
    literature_context: PaperLocalLiteratureContext,
) -> str:
    selected = list(selected_ids)
    item_ids = [item.cited_work_id for item in items]
    ranks = [item.rank for item in items]
    allowed_work_ids = {work.cited_work_id for work in literature_context.cited_works}
    context_owner = {
        context.context_id: context.cited_work_id
        for context in literature_context.citation_contexts
    }
    context_refs = [
        (item.cited_work_id, context_id)
        for item in items
        for context_id in item.evidence_context_ids
    ]
    invalid_context_refs = sum(
        1 for work_id, context_id in context_refs if context_owner.get(context_id) != work_id
    )
    required_context_missing = sum(
        1
        for item in items
        if item.importance.value in {"central", "supporting"}
        and item.cited_work_id in set(context_owner.values())
        and not any(
            context_owner.get(context_id) == item.cited_work_id
            for context_id in item.evidence_context_ids
        )
    )
    return (
        "reply_shape("
        f"selected_ids={len(selected)},"
        f"unique_selected_ids={len(set(selected))},"
        f"unknown_selected_ids={sum(1 for item in selected if item not in allowed_work_ids)},"
        f"items={len(items)},"
        f"item_order_matches={str(item_ids == selected).lower()},"
        f"ranks_contiguous={str(sorted(ranks) == list(range(1, len(ranks) + 1))).lower()},"
        f"evidence_context_refs={len(context_refs)},"
        f"invalid_context_refs={invalid_context_refs},"
        f"required_context_missing={required_context_missing}"
        ")"
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
