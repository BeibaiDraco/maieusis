"""Bounded, source-locked revision of independently reviewed topic-evidence briefs."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from ...assets import resolve_asset
from ...io import dump_data
from ...provenance import sha256_file, stable_hash
from ...providers.models.base import StructuredModelProvider
from ...schemas._r5_firewall import assert_proposal_safe_payload
from ...schemas.gate_outcome import GateDecision, GateOutcome
from ...schemas.inferred_research_scope import ResolvedResearchScope
from ...schemas.scientific_context import (
    TopicEvidenceBrief,
    TopicEvidenceBriefReviewStatus,
    TopicEvidenceClaimOrigin,
)
from .topic_evidence import (
    R5TopicEvidenceSourceTable,
    _TopicEvidenceBriefModelOutput,
    project_questions_already_answered,
    rights_safe_source_text_and_kind,
)

TOPIC_EVIDENCE_BRIEF_REVISER_PROMPT_VERSION = "topic_evidence_brief_reviser/v1"


class TopicEvidenceRevisionError(ValueError):
    """A topic revisor response crossed its source, scope, or proposal boundary."""


class TopicEvidenceRevisionRound(BaseModel):
    """Typed provenance for one source-locked redraft between two independent reviews."""

    model_config = ConfigDict(extra="forbid")

    brief_id: str
    round_index: int = Field(ge=1)
    prompt_version: str = TOPIC_EVIDENCE_BRIEF_REVISER_PROMPT_VERSION
    candidate_digest_before: str
    reviewer_outcome: GateOutcome
    revision_input_digest: str
    generator_provider_id: str
    generator_model_id: str
    revised_candidate_digest: str
    revised_candidate_path: str
    revised_candidate_sha256: str
    cited_source_record_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class TopicEvidenceRevisionHistory(BaseModel):
    """Complete bounded revise/re-review disposition for one topic-evidence brief."""

    model_config = ConfigDict(extra="forbid")

    brief_id: str
    rounds: list[TopicEvidenceRevisionRound] = Field(default_factory=list)
    final_outcome: GateOutcome
    budget_exhausted: bool = False


def revise_topic_evidence_brief(
    provider: StructuredModelProvider,
    *,
    brief: TopicEvidenceBrief,
    r5_source_table: R5TopicEvidenceSourceTable,
    scope: ResolvedResearchScope,
    review_outcome: GateOutcome,
    claim_supporting_source_ids: set[str],
    round_index: int,
    revision_output_path: Path,
    revision_output_reference: str,
    prompt_path: Path | None = None,
) -> tuple[TopicEvidenceBrief, TopicEvidenceRevisionRound]:
    """Apply actionable review feedback without changing scope, identity, evidence, or authority."""

    if (
        review_outcome.decision != GateDecision.REVISE
        or not review_outcome.required_changes
        or not review_outcome.evidence_resolved
    ):
        raise TopicEvidenceRevisionError(
            "topic-evidence revision requires an evidence-resolved revise with actionable changes"
        )
    r5_ids = {record.source_record_id for record in r5_source_table.records}
    if not r5_ids:
        raise TopicEvidenceRevisionError("topic-evidence revision source table is empty")
    if not claim_supporting_source_ids.issubset(r5_ids):
        raise TopicEvidenceRevisionError(
            "topic-evidence revision claim-supporting IDs do not resolve to the source table"
        )

    safe_sources: list[dict[str, object]] = []
    for record in r5_source_table.records:
        safe_text, safe_kind = rights_safe_source_text_and_kind(record)
        safe_sources.append(
            {
                "source_record_id": record.source_record_id,
                "lane_ids": list(record.lane_ids),
                "title": record.title,
                "year": record.year,
                "venue": record.venue,
                "evidence_text": safe_text,
                "snippet_kind": safe_kind.value if safe_kind is not None else "metadata_only",
                "can_support_claims": record.source_record_id in claim_supporting_source_ids,
            }
        )
    payload = {
        "prompt_version": TOPIC_EVIDENCE_BRIEF_REVISER_PROMPT_VERSION,
        "round_index": round_index,
        "topic_evidence_brief": brief.model_dump(mode="json"),
        "resolved_scope": scope.model_dump(mode="json"),
        "review_feedback": {
            "decision": review_outcome.decision.value,
            "rationale": review_outcome.rationale,
            "criterion_assessments": [
                item.model_dump(mode="json") for item in review_outcome.criterion_assessments
            ],
            "criterion_audit": [
                item.model_dump(mode="json") for item in review_outcome.criterion_audit
            ],
            "required_changes": list(review_outcome.required_changes),
            "blocker_findings": list(review_outcome.blocker_findings),
            "hallucination_findings": list(review_outcome.hallucination_findings),
        },
        "eligible_source_record_ids": sorted(claim_supporting_source_ids),
        "source_records": safe_sources,
    }
    prompt = (
        prompt_path
        or resolve_asset(
            Path("prompts") / Path(TOPIC_EVIDENCE_BRIEF_REVISER_PROMPT_VERSION).with_suffix(".md")
        )
    ).read_text(encoding="utf-8")
    input_digest = stable_hash(payload)
    generated = provider.generate_structured(
        system_prompt=prompt,
        user_prompt=json.dumps(payload, ensure_ascii=False, indent=2),
        output_model=_TopicEvidenceBriefModelOutput,
    )

    # These are scientific content boundaries, not merely host-owned IDs. Reject a model that
    # tries to change them rather than silently making its output look compliant after the fact.
    if generated.topic_terms != brief.topic_terms:
        raise TopicEvidenceRevisionError("topic-evidence revision changed topic_terms")
    if generated.canonical_scope.strip() != brief.canonical_scope:
        raise TopicEvidenceRevisionError("topic-evidence revision changed canonical_scope")
    if generated.knowledge_cutoff != brief.knowledge_cutoff:
        raise TopicEvidenceRevisionError("topic-evidence revision changed knowledge_cutoff")
    generated_citations = {
        source_id
        for claim in generated.claims
        for source_id in {*claim.source_record_ids, *claim.source_refs}
    }
    ineligible_generated = sorted(generated_citations - claim_supporting_source_ids)
    if ineligible_generated:
        # The first-pass synthesizer may safely drop unusable citations while building a draft.
        # A correction pass is different: silently sanitizing a reviewed revision would hide that
        # the model ignored the explicit source lock and make the revision look compliant.
        raise TopicEvidenceRevisionError(
            "topic-evidence revision cited ineligible source IDs: "
            + ", ".join(ineligible_generated)
        )

    projected_questions = project_questions_already_answered(generated.claims)
    summary_projected = generated.questions_already_answered != projected_questions

    # Unlike first-pass synthesis, a correction response's authoritative claims are never sanitized
    # into compliance. Raw citations were checked above. The redundant close-prior summary has no
    # independent authority, so it is projected verbatim from typed claims while the strict type
    # restamps every code-owned identity from the reviewed candidate. This also avoids coupling
    # replay to an ephemeral pre-R5 table that was never part of the durable incident artifacts.
    revised = TopicEvidenceBrief.model_validate(
        {
            **generated.model_dump(mode="python"),
            # ``origin`` is code-owned like every identity below it, and was the one that escaped.
            # LOCAL_SUPPORTED and BOTH assert corroboration by the deterministic local lane, which
            # builds its brief with ``claims=[]`` (topic_evidence.py:873) and whose only claim
            # producer, ``_claim_from_record``, has no callers -- so that lane contributes nothing
            # and cannot corroborate anything. First-pass synthesis already force-stamps
            # GPT_SYNTHESIZED (topic_evidence.py:938); the reviser did not, which is why every
            # ``both`` in the recorded corpus appears only from round-0001 onward.
            "claims": [
                claim.model_copy(update={"origin": TopicEvidenceClaimOrigin.GPT_SYNTHESIZED})
                for claim in generated.claims
            ],
            "questions_already_answered": projected_questions,
            "brief_id": brief.brief_id,
            "topic_terms": list(brief.topic_terms),
            "canonical_scope": brief.canonical_scope,
            "knowledge_cutoff": brief.knowledge_cutoff,
            "retrieval_manifest_digest": brief.retrieval_manifest_digest,
            "review_status": TopicEvidenceBriefReviewStatus.DRAFT,
            # The final artifact remains a revision of the v4 synthesized brief; the dedicated
            # revision prompt/model/input identity is bound in TopicEvidenceRevisionRound.
            "prompt_version": brief.prompt_version,
            "provider_id": brief.provider_id,
            "model_id": brief.model_id,
            "input_digest": brief.input_digest,
            "source_table_digest": brief.source_table_digest,
            "field_state_digest": brief.field_state_digest,
            "reviewed_at": None,
            "expert_reviewer": "",
            "review_notes": "",
        }
    )
    claim_ids = [claim.claim_id for claim in revised.claims]
    if len(claim_ids) != len(set(claim_ids)):
        raise TopicEvidenceRevisionError("topic-evidence revision returned duplicate claim IDs")
    cited_ids = sorted(
        {
            source_id
            for claim in revised.claims
            for source_id in {*claim.source_record_ids, *claim.source_refs}
        }
    )
    try:
        assert_proposal_safe_payload(
            revised.model_dump(mode="python"), context="TopicEvidenceBrief revision"
        )
    except ValueError as exc:
        raise TopicEvidenceRevisionError(
            "topic-evidence revision crossed the proposal firewall"
        ) from exc

    # Persist the exact unpromoted candidate before independent re-review. The reviewer request and
    # the revision round both bind this shape; without these bytes, a reviewer transport failure
    # would leave only a dangling digest and the successful revision could not be replayed or audited.
    dump_data(revised, revision_output_path)

    return revised, TopicEvidenceRevisionRound(
        brief_id=brief.brief_id,
        round_index=round_index,
        candidate_digest_before=stable_hash(brief),
        reviewer_outcome=review_outcome,
        revision_input_digest=input_digest,
        generator_provider_id=provider.provider_id,
        generator_model_id=getattr(provider, "model_name", "") or provider.provider_id,
        revised_candidate_digest=stable_hash(revised),
        revised_candidate_path=revision_output_reference,
        revised_candidate_sha256=sha256_file(revision_output_path),
        cited_source_record_ids=cited_ids,
        warnings=(
            ["questions_already_answered_projected_from_typed_claims"] if summary_projected else []
        ),
    )
