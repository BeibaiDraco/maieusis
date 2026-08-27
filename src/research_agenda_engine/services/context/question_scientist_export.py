from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import ValidationError

from ...io import dump_data, load_data, load_model
from ...provenance import sha256_file, stable_hash
from ...schemas.dataset_narrative import DatasetNarrative
from ...schemas.front_half_authority import FrontHalfCeilingCause, FrontHalfCeilingReason
from ...schemas.question_pattern import QuestionPatternCard
from ...schemas.question_scientist_context_v2 import (
    ClaimLevel,
    ClosePriorCard,
    ContentAvailabilityClass,
    ContextProvenanceSummary,
    DatasetContextPack,
    DatasetLimitationCard,
    DatasetOpportunityCard,
    DatasetStorySection,
    EvidenceBasis,
    EvidenceQualitySummary,
    EvidenceRequestProtocol,
    FormationTraceSummaryForProposer,
    LaneCoverageSummary,
    MethodLimitCard,
    OpenGapCard,
    OpenGapKind,
    PatternContextPack,
    ProposalSafeScaleFact,
    ProposalStageGuidance,
    ProposerSourceEvidenceCard,
    QuestionPatternForProposer,
    QuestionScientistContextPayloadV2,
    QuestionScientistEvidenceRequest,
    QuestionScientistEvidenceResolution,
    QuestionScientistEvidenceResolutionStatus,
    ReviewedSynthesisSection,
    ReviewedTopicClaimCard,
    SourceEvidenceRole,
    SourceExclusionSummary,
    SourceExportStatus,
    TopicLiteratureContextPack,
    derive_evidence_basis,
    question_scientist_context_v2_ids,
)
from ...schemas.research_intent import ResearchIntent
from ...schemas.review_authority import is_automated_authority
from ...schemas.scientific_context import (
    TopicEvidenceBrief,
    TopicEvidenceClaim,
    TopicEvidenceClaimStatus,
)
from ..paper_patterns.retrieval import QuestionPatternBank
from ..retrieval.generic_topic_lanes import GENERIC_SCOPE_TERM_QUERY_LANE
from .evidence_basis_labels import (
    abstract_only_gap_and_strong_claim_counts,
    provenance_evidence_basis_note,
)
from .export_gate import build_proposer_source_evidence_card, require_exportable_source_cards
from .review_gates import assert_question_scientist_inputs_are_reviewed
from .topic_evidence import (
    R5TopicEvidenceSourceTable,
    R5TopicSourceRecordEvidence,
    TopicSourceSnippetKind,
    build_source_evidence_cards,
    claim_supporting_source_ids,
)
from .topic_evidence_readiness import evaluate_topic_evidence_readiness


class QuestionScientistContextReadinessError(ValueError):
    """Verified topic evidence no longer satisfies the structural readiness predicate.

    This typed exception separates an expected readiness terminal from compiler, schema,
    provenance, and identity invariant failures.  Only this exception is eligible for the Stage-C
    contained-terminal path; everything else reaches the run envelope as incomplete.

    N3: it is NOT a scientific verdict.  ``evaluate_topic_evidence_readiness`` is a deterministic
    host predicate; the topic-evidence gate runs it as its own pre-check, and the dataset half runs
    it too, where a failure merely CAPS the run at provisional inspiration.  A brief that reaches
    this raise therefore passed the predicate when a reviewer judged it and fails it now, which is a
    machinery inconsistency -- a rights-safe projection that dropped sources, a brief and table that
    disagree -- not a judgement that the science is wanting.
    """


@dataclass(frozen=True)
class RightsSafeTopicSourceProjection:
    """One validated legacy source-table projection for deterministic Stage-C compilation.

    This is deliberately not a general alternate source loader.  Resume constructs it only after
    verifying the dataset receipt and rights-degradation sidecar.  The context builder then binds
    it back to the immutable legacy bytes and permits only the exact removal of unverified fetched
    passages; independently retained abstracts/provider snippets remain usable.
    """

    source_table: R5TopicEvidenceSourceTable
    original_semantic_digest: str
    excluded_source_record_ids: tuple[str, ...]
    projection_reason: Literal["legacy_v0_1_rights_degradation"] = "legacy_v0_1_rights_degradation"


def _topic_basis_note(topic_pack: TopicLiteratureContextPack) -> str:
    """Cause-neutral note counting abstract-only open gaps + strong claims."""
    abstract_only, total = abstract_only_gap_and_strong_claim_counts(
        topic_pack.open_gap_cards, topic_pack.claim_cards
    )
    return provenance_evidence_basis_note(abstract_only, total)


def _require_stage_artifact(path: Path, *, artifact: str, produced_by: str) -> Path:
    """Fail with an HONEST message (not a bare FileNotFoundError) when a required upstream artifact is
    missing — the producing stage yielded nothing (e.g. a zero-accepted paper half)."""
    if not path.exists():
        raise ValueError(
            f"stage-C context build requires {artifact} at {path}, but it is missing: the "
            f"{produced_by} stage produced no usable output. This run has no front-half evidence to "
            f"develop; re-run with usable inputs."
        )
    return path


def _validate_rights_safe_topic_source_projection(
    source_table_path: Path,
    projection: RightsSafeTopicSourceProjection,
) -> R5TopicEvidenceSourceTable:
    """Bind a legacy-only projection to raw bytes without widening the normal loader."""

    raw_payload = load_data(source_table_path)
    if stable_hash(raw_payload) != projection.original_semantic_digest:
        raise ValueError(
            "rights-safe topic projection does not match the immutable source-table semantics"
        )
    try:
        R5TopicEvidenceSourceTable.model_validate(raw_payload)
    except ValidationError:
        pass
    else:
        raise ValueError(
            "rights-safe topic projection is reserved for the validated legacy no-provenance path"
        )
    if not isinstance(raw_payload, dict) or not isinstance(raw_payload.get("records"), list):
        raise ValueError("legacy rights-safe topic projection requires a typed table envelope")

    excluded_ids = tuple(projection.excluded_source_record_ids)
    if not excluded_ids or len(excluded_ids) != len(set(excluded_ids)):
        raise ValueError("legacy rights-safe topic projection requires unique excluded source IDs")
    raw_records = raw_payload["records"]
    if any(not isinstance(record, dict) for record in raw_records):
        raise ValueError("legacy rights-safe topic projection requires object records")
    raw_by_id = {
        record.get("source_record_id"): record
        for record in raw_records
        if isinstance(record.get("source_record_id"), str)
    }
    if len(raw_by_id) != len(raw_records):
        raise ValueError("legacy rights-safe topic projection requires unique source IDs")
    projected_by_id = {
        record.source_record_id: record for record in projection.source_table.records
    }
    if len(projected_by_id) != len(projection.source_table.records) or set(projected_by_id) != set(
        raw_by_id
    ):
        raise ValueError("legacy rights-safe topic projection changed the source identity set")
    if not set(excluded_ids).issubset(raw_by_id):
        raise ValueError("legacy rights-safe topic projection excludes an unknown source ID")

    for source_id, raw_record in raw_by_id.items():
        projected_record = projected_by_id[source_id]
        if source_id not in excluded_ids:
            try:
                unchanged_record = R5TopicSourceRecordEvidence.model_validate(raw_record)
            except ValidationError as exc:
                raise ValueError(
                    "legacy rights-safe topic projection cannot validate an independently "
                    "retained source"
                ) from exc
            if projected_record != unchanged_record:
                raise ValueError(
                    "legacy rights-safe topic projection changed an independently retained source"
                )
            continue
        if raw_record.get("snippet_kind") != "fulltext_excerpt":
            raise ValueError("legacy rights-safe projection may exclude only fetched full text")
        safe_payload = {
            **raw_record,
            "abstract_or_snippet": "",
            "abstract_status": "metadata_only",
            "snippet_kind": "metadata",
            "source_quality_flags": [
                *raw_record.get("source_quality_flags", []),
                "fulltext_rights_unverified",
                "legacy_fulltext_removed_from_safe_projection",
            ],
        }
        try:
            expected_degraded_record = R5TopicSourceRecordEvidence.model_validate(safe_payload)
        except ValidationError as exc:
            raise ValueError(
                "legacy rights-safe projection could not construct the exact degraded record"
            ) from exc
        if projected_record != expected_degraded_record:
            raise ValueError(
                "legacy rights-safe projection did not remove the unverified fetched passage"
            )

    for field_name in ("table_id", "query_plan_id", "protocol_version", "lane_coverage"):
        if projection.source_table.model_dump(mode="json").get(field_name) != raw_payload.get(
            field_name
        ):
            raise ValueError("legacy rights-safe topic projection changed table identity")
    expected_table_flags = [
        *raw_payload.get("source_quality_flags", []),
        "legacy_v0_1_rights_safe_projection",
    ]
    if projection.source_table.source_quality_flags != expected_table_flags:
        raise ValueError("legacy rights-safe topic projection changed table quality flags")
    return projection.source_table


def _project_brief_onto_rights_safe_sources(
    brief: TopicEvidenceBrief,
    *,
    excluded_source_record_ids: set[str],
) -> tuple[TopicEvidenceBrief, int]:
    """Retain only claims whose complete cited basis survives the rights downgrade.

    A mixed-source claim is dropped: co-citation does not prove that the remaining abstract alone
    supports the original synthesis.  Free-prose field-state summaries are likewise not carried
    across the boundary; the only scientific tension/prior text retained is rebuilt from surviving
    typed claims.
    """

    projected_claims: list[TopicEvidenceClaim] = []
    dropped_claim_count = 0
    for claim in brief.claims:
        source_ids = _claim_source_ids(claim)
        if not source_ids or set(source_ids) & excluded_source_record_ids:
            dropped_claim_count += 1
            continue
        projected_claims.append(claim)
    open_or_contested = [
        claim.claim
        for claim in projected_claims
        if claim.status
        in {TopicEvidenceClaimStatus.OPEN_QUESTION, TopicEvidenceClaimStatus.CONTESTED}
    ]
    answered = [
        claim.claim
        for claim in projected_claims
        if claim.status == TopicEvidenceClaimStatus.ALREADY_ANSWERED
    ]
    return (
        brief.model_copy(
            update={
                "claims": projected_claims,
                "canonical_scope": (
                    "Rights-safe projection of independently supported reviewed claims."
                ),
                "nearest_dataset_reuse_work": [],
                "questions_already_answered": answered,
                "unresolved_tensions": open_or_contested,
            }
        ),
        dropped_claim_count,
    )


def build_question_scientist_context_payload_v2(
    *,
    corpus_root: str | Path = "corpus",
    intent_path: str | Path = "examples/research_intent.yaml",
    dataset_id: str = "ibl_bwm",
    pattern_limit: int = 8,
    max_topic_sources: int = 30,
    provisional_inspiration: bool = False,
    rights_safe_topic_source_projection: RightsSafeTopicSourceProjection | None = None,
    ceiling_cause: FrontHalfCeilingCause | None = None,
) -> QuestionScientistContextPayloadV2:
    root = Path(corpus_root)
    intent_path = Path(intent_path)
    intent = load_model(intent_path, ResearchIntent)
    pattern_manifest_path = root / "question_pattern_manifest.yaml"
    _require_stage_artifact(
        pattern_manifest_path,
        artifact="the question-pattern manifest",
        produced_by="paper-half",
    )
    pattern_bank = QuestionPatternBank.from_corpus(root, serious_mode=True)
    reviewed_patterns = [
        hit.pattern
        for hit in pattern_bank.retrieve(
            intent.topic_terms or intent.target_constructs,
            limit=pattern_limit,
        )
    ]
    dataset_path = root / "context" / "dataset_narratives" / f"{dataset_id}.dataset_narrative.yaml"
    topic_path = root / "context" / "topic_evidence" / "research_intent.topic_evidence_brief.yaml"
    source_table_path = (
        root / "context" / "topic_evidence" / "sources" / "research_intent.topic_source_table.yaml"
    )
    _require_stage_artifact(
        dataset_path, artifact="the dataset narrative", produced_by="dataset-half"
    )
    _require_stage_artifact(
        topic_path, artifact="the topic-evidence brief", produced_by="dataset-half"
    )
    _require_stage_artifact(
        source_table_path, artifact="the topic source table", produced_by="dataset-half"
    )
    dataset_narrative = load_model(dataset_path, DatasetNarrative)
    topic_brief = load_model(topic_path, TopicEvidenceBrief)
    source_table = (
        _validate_rights_safe_topic_source_projection(
            source_table_path,
            rights_safe_topic_source_projection,
        )
        if rights_safe_topic_source_projection is not None
        else load_model(source_table_path, R5TopicEvidenceSourceTable)
    )
    # A legacy rights downgrade cannot retain the old verified topic-context authority.  It enters
    # the existing provisional-inspiration lane automatically, preserving usable lower-authority
    # abstracts/snippets without presenting the derived context as freshly reviewed.
    provisional_inspiration = (
        provisional_inspiration or rights_safe_topic_source_projection is not None
    )
    if provisional_inspiration:
        assert_question_scientist_inputs_are_reviewed(
            paperbank_question_patterns=reviewed_patterns,
            topic_literature_brief=topic_brief,
            dataset_narrative=dataset_narrative,
            allow_provisional_topic=True,
        )
    else:
        assert_question_scientist_inputs_are_reviewed(
            paperbank_question_patterns=reviewed_patterns,
            topic_literature_brief=topic_brief,
            dataset_narrative=dataset_narrative,
        )

    pattern_pack = _compile_pattern_context_pack(reviewed_patterns)
    topic_pack = _compile_topic_literature_context_pack(
        topic_brief,
        source_table,
        max_topic_sources=max_topic_sources,
        provisional_inspiration=provisional_inspiration,
        original_source_table_digest=(
            rights_safe_topic_source_projection.original_semantic_digest
            if rights_safe_topic_source_projection is not None
            else None
        ),
        excluded_source_record_ids=(
            set(rights_safe_topic_source_projection.excluded_source_record_ids)
            if rights_safe_topic_source_projection is not None
            else None
        ),
        ceiling_cause=ceiling_cause,
    )
    dataset_pack = _compile_dataset_context_pack(dataset_narrative)

    # Authority = MIN real authority of the inputs. Any AI-reviewed input ⇒ the pack and
    # the overall context are AI authority (never falsely "expert"); route through the F1 predicate.
    pattern_ai = any(is_automated_authority(p.review_status) for p in reviewed_patterns)
    topic_ai = is_automated_authority(topic_brief.review_status)
    dataset_ai = is_automated_authority(dataset_narrative.review_status)
    if pattern_ai:
        pattern_pack = pattern_pack.model_copy(update={"review_status": "ai_reviewed"})
    if topic_ai and not provisional_inspiration:
        topic_pack = topic_pack.model_copy(update={"review_status": "ai_reviewed"})
    if dataset_ai:
        dataset_pack = dataset_pack.model_copy(update={"review_status": "ai_reviewed"})
    context_review_status = (
        "provisional_inspiration"
        if provisional_inspiration
        else (
            "ai_reviewed_exportable"
            if (pattern_ai or topic_ai or dataset_ai)
            else "expert_reviewed_exportable"
        )
    )
    base = {
        "contract_version": "question_scientist_context/v2",
        "payload_id": "pending",
        "context_id": "pending",
        "context_digest": "0" * 64,
        "context_review_status": context_review_status,
        "research_intent": intent.model_dump(mode="json"),
        "scientific_intent_invariant_digest": stable_hash(intent.model_dump(mode="json")),
        "paperbank_patterns": pattern_pack.model_dump(mode="json"),
        "topic_literature": topic_pack.model_dump(mode="json"),
        "dataset_context": dataset_pack.model_dump(mode="json"),
        "proposer_guidance": _proposal_stage_guidance().model_dump(mode="json"),
        "evidence_request_protocol": EvidenceRequestProtocol().model_dump(mode="json"),
        "provenance_summary": ContextProvenanceSummary(
            pattern_pack_digest=stable_hash(pattern_pack),
            topic_pack_digest=stable_hash(topic_pack),
            dataset_pack_digest=stable_hash(dataset_pack),
            notes=[
                "V2 payload is proposer-facing only.",
                "Raw review Markdown, raw source tables, blocked drafts, and full abstracts are excluded.",
                # DP-2 surface 2: honest, ID-free, cause-neutral basis note the Question Scientist sees.
                *([_topic_basis_note(topic_pack)] if _topic_basis_note(topic_pack) else []),
                *(
                    [
                        "A receipt-bound legacy rights projection removed unverified fetched "
                        "passages; independently retained lower-authority source text remains."
                    ]
                    if rights_safe_topic_source_projection is not None
                    else []
                ),
            ],
        ).model_dump(mode="json"),
        "source_artifact_digests": {
            "research_intent": sha256_file(intent_path),
            "question_pattern_manifest": sha256_file(pattern_manifest_path),
            "dataset_narrative": sha256_file(dataset_path),
            "topic_evidence_brief": sha256_file(topic_path),
            "topic_source_table": sha256_file(source_table_path),
            **(
                {"topic_source_table_safe_projection": stable_hash(source_table)}
                if rights_safe_topic_source_projection is not None
                else {}
            ),
        },
    }
    payload_id, context_id, digest = question_scientist_context_v2_ids(base)
    base.update(
        {
            "payload_id": payload_id,
            "context_id": context_id,
            "context_digest": digest,
        }
    )
    return QuestionScientistContextPayloadV2.model_validate(base)


def write_question_scientist_context_payload_v2(
    payload: QuestionScientistContextPayloadV2,
    *,
    corpus_root: str | Path = "corpus",
) -> Path:
    path = (
        Path(corpus_root)
        / "context"
        / "question_scientist"
        / f"{payload.context_id}.question_scientist_context_v2.yaml"
    )
    return dump_data(payload, path)


def validate_question_scientist_context_payload_v2(
    path: str | Path,
) -> QuestionScientistContextPayloadV2:
    return load_model(path, QuestionScientistContextPayloadV2)


def render_question_scientist_context_export_report(
    payload: QuestionScientistContextPayloadV2,
) -> str:
    topic = payload.topic_literature
    dataset = payload.dataset_context
    lines = [
        "# Question Scientist Context V2 Export Report",
        "",
        f"- Context ID: `{payload.context_id}`",
        f"- Digest: `{payload.context_digest}`",
        f"- Review status: `{payload.context_review_status}`",
        "",
        "## Exported Families",
        "",
        f"- PatternContextPack: {len(payload.paperbank_patterns.pattern_cards)} pattern(s)",
        f"- TopicLiteratureContextPack: {len(topic.source_cards)} source card(s), "
        f"{len(topic.claim_cards)} claim card(s), {len(topic.open_gap_cards)} open gap(s)",
        f"- DatasetContextPack: {len(dataset.story_sections)} story section(s), "
        f"{len(dataset.proposal_safe_scale_facts)} scale fact(s)",
        "",
        "## Excluded Source Summary",
        "",
        (
            f"- Metadata-only: {topic.excluded_or_support_ineligible_summary.metadata_only_count}; "
            f"title-only: {topic.excluded_or_support_ineligible_summary.title_only_count}; "
            f"diagnostic/off-topic: {topic.excluded_or_support_ineligible_summary.diagnostic_or_offtopic_count}; "
            f"blocked: {topic.excluded_or_support_ineligible_summary.blocked_source_count}"
        ),
        "",
        "## Open Gaps",
        "",
    ]
    lines.extend(
        [
            f"- `{gap.gap_id}` [{gap.gap_kind.value}]: {gap.statement}"
            for gap in topic.open_gap_cards
        ]
        or ["- No exported open gaps."]
    )
    lines.extend(
        [
            "",
            "## Dataset Opportunity Surface",
            "",
            *[f"- {card.statement}" for card in dataset.opportunity_cards],
        ]
    )
    return "\n".join(lines)


def resolve_question_scientist_evidence_requests_dry_run(
    payload: QuestionScientistContextPayloadV2,
    requests: list[QuestionScientistEvidenceRequest],
) -> list[QuestionScientistEvidenceResolution]:
    source_ids = {card.source_record_id for card in payload.topic_literature.source_cards}
    claim_ids = {card.claim_id for card in payload.topic_literature.claim_cards}
    gap_ids = {card.gap_id for card in payload.topic_literature.open_gap_cards}
    resolutions: list[QuestionScientistEvidenceResolution] = []
    for request in requests:
        target = request.target_claim_or_gap_id
        if target and target in claim_ids | gap_ids:
            matching_cards = [
                card.source_record_id
                for card in payload.topic_literature.source_cards
                if target in card.support_claim_ids or target in card.support_gap_ids
            ]
            resolutions.append(
                QuestionScientistEvidenceResolution(
                    request_id=request.request_id,
                    resolution_status=(
                        QuestionScientistEvidenceResolutionStatus.RESOLVED_FROM_EXISTING_PACK
                        if matching_cards
                        else QuestionScientistEvidenceResolutionStatus.RESOLVED_AS_UNSUPPORTED
                    ),
                    new_source_evidence_card_ids=[],
                    updated_claim_card_ids=[target] if target in claim_ids else [],
                    updated_gap_card_ids=[target] if target in gap_ids else [],
                    unresolved_reason=""
                    if matching_cards
                    else "No gated evidence card supports target.",
                    notes_for_question_scientist=(
                        "Existing proposer-safe source cards: " + ", ".join(matching_cards)
                        if matching_cards
                        else "No new public-source search was performed in dry-run mode."
                    ),
                )
            )
        elif source_ids:
            resolutions.append(
                QuestionScientistEvidenceResolution(
                    request_id=request.request_id,
                    resolution_status=QuestionScientistEvidenceResolutionStatus.UNRESOLVED_NEEDS_HUMAN_REVIEW,
                    unresolved_reason=(
                        "Dry-run resolver cannot expand beyond the current export pack."
                    ),
                    notes_for_question_scientist=(
                        "Ask Maieusis to resolve through public-source acquisition if this is blocking."
                    ),
                )
            )
        else:
            resolutions.append(
                QuestionScientistEvidenceResolution(
                    request_id=request.request_id,
                    resolution_status=QuestionScientistEvidenceResolutionStatus.UNRESOLVED_NO_SOURCES_FOUND,
                    unresolved_reason="Current export pack contains no source cards.",
                )
            )
    return resolutions


def _compile_pattern_context_pack(
    patterns: list[QuestionPatternCard],
) -> PatternContextPack:
    return PatternContextPack(
        pattern_pack_id=f"pattern-context-pack-{stable_hash([pattern.pattern_id for pattern in patterns])[:12]}",
        review_status=(
            "ai_reviewed"
            if any(is_automated_authority(pattern.review_status) for pattern in patterns)
            else "expert_reviewed"
        ),
        pattern_cards=[_pattern_for_proposer(pattern) for pattern in patterns],
        diversity_guidance=[
            "Use patterns as transferable question-formation moves, not as templates to copy source-paper titles.",
            "Generate questions that can survive later dataset-planning clarification.",
        ],
    )


def _pattern_for_proposer(pattern: QuestionPatternCard) -> QuestionPatternForProposer:
    return QuestionPatternForProposer(
        pattern_id=pattern.pattern_id,
        title=pattern.pattern_name,
        abstract_pattern=pattern.unresolved_tension_pattern,
        scientific_move=pattern.question_formation_move,
        epistemic_move=pattern.scientific_payoff,
        typical_contrast_structure=pattern.starting_scientific_state,
        useful_when=pattern.dataset_cues,
        avoid_when=pattern.common_failure_modes,
        anti_patterns=pattern.non_transferable_details,
        evidence_role_template=["Look for literature tensions and construct/method precedents."],
        dataset_role_template=[
            "Use broad dataset opportunities as inspiration, not feasibility proof."
        ],
        review_status="ai_reviewed"
        if is_automated_authority(pattern.review_status)
        else "expert_reviewed",
        formation_trace_summaries=[
            FormationTraceSummaryForProposer(
                trace_id=trace_id,
                source_paper_case_id=case_id,
                question_forming_move=pattern.question_formation_move,
                literature_evidence_role=pattern.unresolved_tension_pattern,
                dataset_or_observation_role="Dataset cue used at proposal-stage granularity.",
                what_to_imitate=pattern.scientific_payoff,
                what_not_to_copy="Do not copy paper-specific biological scope or dataset idiosyncrasies.",
            )
            for trace_id, case_id in zip(
                pattern.source_trace_ids, pattern.source_case_ids, strict=False
            )
        ],
    )


# The two semantic dimensions an OpenGapCard makes an assertion ABOUT.  `close_prior_already_answered`
# is the card's own precondition; `open_gaps` is the finding itself.  Residual absence of either is
# the state in which the card would over-claim, so the export withholds it.  Names come from the
# inquiry's own semantic-dimension vocabulary (`_TOPIC_DIMENSION_PUBLIC_LABELS` in `end_to_end.py`).
_GAP_CARD_ASSERTED_DIMENSIONS = frozenset({"close_prior_already_answered", "open_gaps"})


def _reviewed_coverage_gap_undercuts_gap_cards(
    ceiling_cause: FrontHalfCeilingCause | None,
) -> bool:
    """True when a reviewed-coverage cap left unmet exactly what an OpenGapCard asserts."""

    if ceiling_cause is None:
        return False
    if ceiling_cause.reason is not FrontHalfCeilingReason.REVIEWED_COVERAGE_GAP:
        return False
    return bool(set(ceiling_cause.residual_dimensions) & _GAP_CARD_ASSERTED_DIMENSIONS)


def _compile_topic_literature_context_pack(
    brief: TopicEvidenceBrief,
    source_table: R5TopicEvidenceSourceTable,
    *,
    max_topic_sources: int,
    provisional_inspiration: bool = False,
    original_source_table_digest: str | None = None,
    excluded_source_record_ids: set[str] | None = None,
    ceiling_cause: FrontHalfCeilingCause | None = None,
) -> TopicLiteratureContextPack:
    source_record_ids = [record.source_record_id for record in source_table.records]
    if len(source_record_ids) != len(set(source_record_ids)):
        raise ValueError("topic source table contains duplicate source_record_id values")
    actual_source_table_digest = stable_hash(source_table)
    source_table_binding_digest = original_source_table_digest or actual_source_table_digest
    if brief.source_table_digest != source_table_binding_digest:
        raise ValueError("TopicEvidenceBrief source_table_digest does not match source table")
    topic_card_review_status: Literal["expert_reviewed", "ai_reviewed", "provisional"] = (
        "provisional"
        if provisional_inspiration
        else ("ai_reviewed" if is_automated_authority(brief.review_status) else "expert_reviewed")
    )
    record_by_id = {record.source_record_id: record for record in source_table.records}
    evidence_cards = {
        card.source_record_id: card for card in build_source_evidence_cards(source_table)
    }
    # G3: the compiler and the topic-evidence gate share a single readiness function, so an
    # accepted brief always compiles (the gate cannot earn-accept a brief the compiler would reject on
    # a missing close-prior/open-gap or an unresolved claim source).
    # Use the same structural eligibility predicate as topic curation. Raw snippet availability is
    # insufficient when a record was explicitly classified off-topic/non-primary; provisional mode
    # may retain partial evidence, but it must never re-export a source the curator blocked.
    claim_supporting_ids = claim_supporting_source_ids(source_table)
    projected_brief = brief
    dropped_rights_claim_count = 0
    if excluded_source_record_ids:
        projected_brief, dropped_rights_claim_count = _project_brief_onto_rights_safe_sources(
            brief,
            excluded_source_record_ids=excluded_source_record_ids,
        )
        unknown_projected_sources = sorted(
            {
                source_id
                for claim in projected_brief.claims
                for source_id in _claim_source_ids(claim)
                if source_id not in record_by_id
            }
        )
        if unknown_projected_sources:
            raise ValueError(
                "legacy rights-safe TopicEvidenceBrief cites sources absent from its immutable "
                "source table: " + ", ".join(unknown_projected_sources)
            )
    safe_claims = [
        claim
        for claim in projected_brief.claims
        if _claim_source_ids(claim) and set(_claim_source_ids(claim)).issubset(claim_supporting_ids)
    ]
    working_brief = (
        projected_brief.model_copy(update={"claims": safe_claims})
        if provisional_inspiration
        else projected_brief
    )
    ready, issues = evaluate_topic_evidence_readiness(
        working_brief,
        source_record_ids=set(record_by_id),
        claim_supporting_record_ids=claim_supporting_ids,
    )
    if not ready and not provisional_inspiration:
        raise QuestionScientistContextReadinessError(
            "V2 topic pack readiness failed: " + "; ".join(issues)
        )
    claim_ids_by_source: dict[str, list[str]] = {}
    gap_ids_by_source: dict[str, list[str]] = {}
    close_prior_ids_by_source: dict[str, list[str]] = {}
    method_limit_ids_by_source: dict[str, list[str]] = {}
    close_prior_claims = [
        claim
        for claim in working_brief.claims
        if claim.status == TopicEvidenceClaimStatus.ALREADY_ANSWERED
    ]
    open_gap_claims = [
        claim
        for claim in working_brief.claims
        if claim.status == TopicEvidenceClaimStatus.OPEN_QUESTION
    ]
    # A provisional brief may preserve useful source-backed open-question CLAIMS even when retrieval
    # did not earn a typed close prior.  Such a claim cannot be promoted into an OpenGapCard: that
    # stronger card explicitly asserts that close-prior status has been checked.  Keep the claim and
    # its source card visible, but omit both the gap card and its reciprocal source linkage.  Verified
    # input never reaches this branch because readiness above remains strict.
    #
    # The absence of a close prior is not the only way that assertion can be unbacked.  A run capped
    # because independent review found the coverage short reaches here WITH close priors and would
    # otherwise ship full-strength gap cards -- measured worst case, one of the two 2026-08-11
    # qualification legs would have exported an open-question claim as a source-backed open gap
    # while its own inquiry rated that very dimension `indeterminate`.  So when the
    # dimensions the inquiry could not establish are the two the card asserts about, the same
    # suppression fires on the same mechanism.  A cap for any other residual dimension still ships
    # them: this is a targeted guard, not a blanket ban on gap cards from capped runs.
    # Operator ruling, 2026-08-17: a proposer must not be starved. The previous behaviour DELETED
    # these cards, and it deleted them at exactly the worst moment -- a run whose literature was
    # judged short is the run whose proposer most needs to be told where the field is open. The
    # concern behind the deletion is real and is kept: an OpenGapCard asserts that close-prior
    # status WAS checked, and a capped run has not earned that assertion. But the card was already
    # built to carry a downgrade (`review_status`, `forbidden_overclaims`), so the honest move is to
    # label it, not to remove it -- degrade honestly rather than discard a traceable artifact.
    #
    # TWO different situations hide behind the old single condition, and only one of them was ever
    # a policy choice:
    #   * no close prior AT ALL -- `OpenGapCard.require_evidence_and_close_prior` refuses to
    #     construct the card (`schemas/question_scientist_context_v2.py:388`). Nothing to rule on;
    #     the type does not exist in that state. The open question still reaches the proposer as an
    #     `open_question` claim card with its sources, so nothing is lost but the assertion.
    #   * close priors EXIST and the cap touched the dimensions the card asserts about -- here the
    #     card is constructible and the old code chose to drop it. That is the choice now reversed.
    unbacked_gap_assertion = _reviewed_coverage_gap_undercuts_gap_cards(ceiling_cause)
    gap_assertion_unearned = provisional_inspiration and unbacked_gap_assertion
    exported_open_gap_claims = [] if not close_prior_claims else open_gap_claims
    exported_open_gap_claim_ids = {claim.claim_id for claim in exported_open_gap_claims}
    method_limit_claims = [
        claim
        for claim in working_brief.claims
        if claim.status
        in {
            TopicEvidenceClaimStatus.KNOWN_LIMITATION,
            TopicEvidenceClaimStatus.METHODOLOGICAL_CHANGE,
        }
    ]
    for claim in working_brief.claims:
        for source_id in _claim_source_ids(claim):
            claim_ids_by_source.setdefault(source_id, []).append(claim.claim_id)
            if claim.claim_id in exported_open_gap_claim_ids:
                gap_ids_by_source.setdefault(source_id, []).append(f"gap-{claim.claim_id}")
            if claim.status == TopicEvidenceClaimStatus.ALREADY_ANSWERED:
                close_prior_ids_by_source.setdefault(source_id, []).append(
                    f"prior-{claim.claim_id}"
                )
            if claim in method_limit_claims:
                method_limit_ids_by_source.setdefault(source_id, []).append(
                    f"limit-{claim.claim_id}"
                )
    # EVERY id this returns is cited by a retained claim -- the function filters the source table
    # down to `cited_set` and raises on a citation it cannot resolve. These are not optional.
    cited_source_ids = _rank_topic_source_ids(working_brief, source_table)
    # `max_topic_sources` bounds what the PROPOSER is handed, and it used to be applied to the whole
    # list including the cited ids. That truncation could never be correct: `_evidence_basis` below
    # requires every cited source to be an exported card and raises otherwise, so a brief citing
    # more than the cap crashed the run outright.
    #
    # It was one bad draw away for four qualification sets. The corpus grew from 20 records to
    # 45-59 as retrieval widened, and the cited count tracked it -- 15, then 21, then 26, 25, 26 --
    # against a cap of 30. The 2026-08-23 climate leg retrieved 59 records, cited 43, and died at
    # 1h21m with `source topic-source-record-44194e35d502 is not an exported source card`. The leg
    # before it, byte-identical in config and prompt, cited 26 and cleared the cliff by four.
    #
    # So the cap now bounds only the PADDING: the claim-supporting sources a provisional-inspiration
    # export adds beyond what the brief actually cites. Raising the constant would have bought one
    # more corpus-growth cycle; this removes the cliff.
    padding = (
        [
            source_id
            for source_id in sorted(claim_supporting_ids)
            if source_id not in set(cited_source_ids)
        ]
        if provisional_inspiration
        else []
    )
    source_ids = [*cited_source_ids, *padding[: max(max_topic_sources - len(cited_source_ids), 0)]]
    proposer_cards: list[ProposerSourceEvidenceCard] = []
    blocked_count = 0
    for source_id in source_ids:
        source_card = evidence_cards.get(source_id)
        record = record_by_id.get(source_id)
        if source_card is None or record is None:
            raise ValueError(
                f"TopicEvidenceBrief cites source not present in source table: {source_id}"
            )
        roles = _source_roles_for_claims(
            source_id,
            working_brief.claims,
            gap_ids_by_source=gap_ids_by_source,
            close_prior_ids_by_source=close_prior_ids_by_source,
            method_limit_ids_by_source=method_limit_ids_by_source,
        )
        proposer_card = build_proposer_source_evidence_card(
            source_card,
            r5_record=record,
            evidence_roles=roles,
            support_claim_ids=claim_ids_by_source.get(source_id, []),
            support_gap_ids=gap_ids_by_source.get(source_id, []),
            support_close_prior_ids=close_prior_ids_by_source.get(source_id, []),
            support_method_limit_ids=method_limit_ids_by_source.get(source_id, []),
            review_status=topic_card_review_status,
        )
        if proposer_card.export_status == SourceExportStatus.BLOCKED_FROM_QUESTION_SCIENTIST:
            blocked_count += 1
            raise ValueError(
                "reviewed topic claim cites source blocked from Question Scientist export: "
                f"{source_id} ({', '.join(reason.value for reason in proposer_card.export_block_reasons)})"
            )
        proposer_cards.append(proposer_card)
    require_exportable_source_cards(proposer_cards)
    content_class_by_source = {
        card.source_record_id: card.content_availability_class for card in proposer_cards
    }

    def _evidence_basis(source_ids: list[str]) -> EvidenceBasis:
        classes: list[ContentAvailabilityClass] = []
        for source_id in source_ids:
            content_class = content_class_by_source.get(source_id)
            if content_class is None:
                raise ValueError(
                    f"cannot derive evidence_basis: source {source_id} is not an exported source card"
                )
            classes.append(content_class)
        return derive_evidence_basis(classes)

    excerpt_by_source = {
        card.source_record_id: [excerpt.excerpt_id for excerpt in card.excerpts]
        for card in proposer_cards
    }
    claim_cards = [
        ReviewedTopicClaimCard(
            claim_id=claim.claim_id,
            statement=claim.claim,
            status=claim.status,
            source_record_ids=_claim_source_ids(claim),
            source_excerpt_ids=_excerpt_ids_for_claim(claim, excerpt_by_source),
            confidence=claim.confidence,
            evidence_basis=_evidence_basis(_claim_source_ids(claim)),
        )
        for claim in working_brief.claims
    ]
    close_prior_cards = [
        ClosePriorCard(
            close_prior_id=f"prior-{claim.claim_id}",
            statement=claim.claim,
            implication=claim.synthesis_rationale
            or "Close prior must be considered before proposing redundant questions.",
            source_record_ids=_claim_source_ids(claim),
            source_excerpt_ids=_excerpt_ids_for_claim(claim, excerpt_by_source),
            review_status=topic_card_review_status,
        )
        for claim in close_prior_claims
    ]
    method_limit_cards = [
        MethodLimitCard(
            method_limit_id=f"limit-{claim.claim_id}",
            statement=claim.claim,
            consequence_for_question_generation=claim.synthesis_rationale
            or "QuestionSeeds should avoid overclaiming beyond this methodological limit.",
            source_record_ids=_claim_source_ids(claim),
            source_excerpt_ids=_excerpt_ids_for_claim(claim, excerpt_by_source),
            review_status=topic_card_review_status,
        )
        for claim in method_limit_claims
    ]
    close_prior_ids = [card.close_prior_id for card in close_prior_cards]
    open_gap_cards = [
        OpenGapCard(
            gap_id=f"gap-{claim.claim_id}",
            statement=claim.claim,
            gap_kind=_gap_kind(claim.claim),
            why_live=claim.synthesis_rationale or "Reviewed as an open literature tension.",
            proposal_relevance="Can motivate QuestionSeeds if later planning preserves the construct.",
            support_claim_ids=[claim.claim_id],
            support_source_record_ids=_claim_source_ids(claim),
            support_excerpt_ids=_excerpt_ids_for_claim(claim, excerpt_by_source),
            close_prior_ids=close_prior_ids,
            allowed_claim_levels=[
                ClaimLevel.DESCRIPTIVE,
                ClaimLevel.ASSOCIATIONAL,
                ClaimLevel.PREDICTIVE,
            ],
            forbidden_overclaims=[
                "Do not infer causal mechanism from public observational data alone.",
                # The card's whole point is the assertion "and nobody has answered this". On a
                # capped run that assertion was not earned, so it is withdrawn here IN THE CARD
                # rather than by removing the card: the open question and its sources remain usable
                # material for proposing, and only the unanswered-ness claim is forbidden.
                *(
                    [
                        "Do not treat this as an established gap in the literature. The close-prior "
                        "check this card's unanswered-ness rests on was not met by this run's "
                        "reviewed coverage. Use it as a lead worth asking about, and state that "
                        "the prior work is unverified."
                    ]
                    if gap_assertion_unearned
                    else []
                ),
            ],
            # NOT downgraded here, deliberately: `topic_card_review_status` is already
            # `provisional` whenever `provisional_inspiration` holds (see its derivation above), and
            # `gap_assertion_unearned` requires that flag -- so an override would be a line that can
            # never change a value. The withdrawal above is what carries the downgrade, and a
            # mutation test proved it is the load-bearing half.
            review_status=topic_card_review_status,
            evidence_basis=_evidence_basis(_claim_source_ids(claim)),
        )
        for claim in exported_open_gap_claims
    ]
    exported = len(proposer_cards)
    warnings = sum(
        1 for card in proposer_cards if card.export_status == SourceExportStatus.EXPORT_WITH_WARNING
    )
    source_counts = _source_exclusion_counts(source_table)
    return TopicLiteratureContextPack(
        topic_pack_id=f"topic-literature-context-pack-{stable_hash({'brief': brief.brief_id, 'sources': source_ids})[:12]}",
        source_table_digest=actual_source_table_digest,
        review_id=f"topic-literature-review-{brief.brief_id}",
        brief_id=brief.brief_id,
        brief_prompt_version=brief.prompt_version,
        review_status=topic_card_review_status,
        # NOT a prompt version, and it never was. The capsule below is recompiled from the reviewed
        # BRIEF by `_field_state_capsule_from_brief`; the run's actual field-state synthesis -- an
        # 11-section, ~10-13k-character dossier written by `topic_field_state_synthesizer` and graded
        # by the independent reviewer under its own `field_state_complete` criterion -- is persisted
        # at `context/topic_evidence/sources/research_intent.topic_field_state.yaml` and is not
        # opened by this projection at all. Naming a prompt here asserted a provenance this value
        # does not have. Corrected 2026-08-17 to say what actually produced it.
        field_state_prompt_version=f"compiled_from_brief:{brief.prompt_version or 'unversioned'}",
        lane_coverage=[
            LaneCoverageSummary(
                lane_id=lane,
                source_count=count,
                claim_supporting_source_count=sum(
                    1
                    for record in source_table.records
                    if lane in record.lane_ids and record.can_support_claims
                ),
            )
            for lane, count in sorted(source_table.lane_coverage.items())
            if lane != GENERIC_SCOPE_TERM_QUERY_LANE
        ],
        field_state_capsule=(
            _field_state_capsule_from_brief(working_brief) if working_brief.claims else []
        ),
        claim_cards=claim_cards,
        open_gap_cards=open_gap_cards,
        close_prior_cards=close_prior_cards,
        method_limit_cards=method_limit_cards,
        source_cards=proposer_cards,
        evidence_quality_summary=EvidenceQualitySummary(
            source_count=len(source_table.records),
            exported_source_count=exported,
            export_with_warning_count=warnings,
            blocked_source_count=blocked_count + source_counts["blocked"],
            notes=[
                # Measured on the 2026-08-14 ibl leg: 17 of 20 exported excerpts sit at 795-800
                # characters against an 800-character ceiling, median 800. They are abstracts cut at
                # a length limit, not passages anyone selected, and the previous wording -- "Full
                # abstracts are not exported; selected excerpts only" -- told the reader the
                # opposite of both halves of that.
                "Source excerpts are truncated at a fixed character limit, not curated passages; an "
                "excerpt at the limit is a cut abstract and may end mid-sentence.",
                *(
                    ["Partial literature coverage; provisional inspiration only."]
                    if provisional_inspiration
                    else []
                ),
                *(
                    [f"Provisional topic readiness issue: {issue}" for issue in issues]
                    if provisional_inspiration and issues
                    else []
                ),
                # Say WHY the pack is provisional when the answer is "it was reviewed", because the
                # note above and the published ceiling label otherwise read as "nobody looked".  The
                # sentence is rendered upstream from controlled semantic labels only.
                *(
                    [
                        "This topic literature WAS independently reviewed and was capped because "
                        f"{ceiling_cause.public_reason}."
                        if ceiling_cause is not None and ceiling_cause.public_reason
                        else "This topic literature was independently reviewed and found short of "
                        "the coverage this scope needs."
                    ]
                    if ceiling_cause is not None
                    and ceiling_cause.reason is FrontHalfCeilingReason.REVIEWED_COVERAGE_GAP
                    else []
                ),
                *(
                    [
                        "Open-gap cards are exported at `provisional` with their unanswered-ness "
                        "claim explicitly withdrawn: the reviewed coverage those cards assert "
                        "about was among the unmet dimensions, so each card carries the open "
                        "question and its sources but forbids treating it as an established gap."
                    ]
                    # `and open_gap_cards`: the sentence describes cards the reader can open, and a
                    # run with no open-question claim -- or no close prior, which
                    # `OpenGapCard.require_evidence_and_close_prior` refuses to build a card without
                    # -- exports none. Saying how they were labelled when there are none is a
                    # statement about something that does not exist, and this pack is read by a
                    # model that cannot go and check.
                    if gap_assertion_unearned and open_gap_cards
                    else []
                ),
                *(
                    [
                        "Legacy rights-safe projection omitted every claim touching unverified "
                        "fetched text while retaining independently supported claims."
                    ]
                    if excluded_source_record_ids
                    else []
                ),
                *(
                    [
                        f"Legacy rights-safe projection omitted {dropped_rights_claim_count} "
                        "claim(s) with no remaining independent support."
                    ]
                    if dropped_rights_claim_count
                    else []
                ),
            ],
        ),
        excluded_or_support_ineligible_summary=SourceExclusionSummary(
            metadata_only_count=source_counts["metadata_only"],
            title_only_count=source_counts["title_only"],
            diagnostic_or_offtopic_count=source_counts["diagnostic"],
            blocked_source_count=blocked_count + source_counts["blocked"],
        ),
    )


def _item_sources(
    narrative: DatasetNarrative, field: str, index: int, fallback: list[str]
) -> list[str]:
    """The source(s) that authored a single list item, not the sources that touched its field.

    Measured before this existed: 7/7 story, 11/11 opportunity and 10/10 limitation cards in both
    recorded two-source runs carried the same two-source id list, so a card only one lane ever wrote
    reached the Question Scientist as jointly asserted by two independent sources. Narratives fused
    from a single source, and every artifact written before ``list_item_source_ids`` existed, have no
    per-item map; there the field-level list is already per-item and is used unchanged.
    """

    per_item = narrative.list_item_source_ids.get(field)
    if per_item is not None and index < len(per_item) and per_item[index]:
        return list(per_item[index])
    field_level = narrative.field_evidence_source_ids.get(field)
    return list(field_level) if field_level else list(fallback[:2])


def _compile_dataset_context_pack(narrative: DatasetNarrative) -> DatasetContextPack:
    source_ids = [source.source_id for source in narrative.source_refs]
    field_sources = narrative.field_evidence_source_ids or {}
    story_fields = [
        ("scientific_purpose", "Scientific purpose", narrative.scientific_purpose),
        ("population", "Population", narrative.population),
        ("task_or_design", "Task and design", narrative.task_or_design),
        ("modalities", "Recording modalities", "; ".join(narrative.modalities)),
        (
            "spatial_or_anatomical_coverage",
            "Anatomical scope",
            narrative.spatial_or_anatomical_coverage,
        ),
        ("temporal_structure", "Temporal/trial structure", narrative.temporal_structure),
        ("standardization", "Standardization", narrative.standardization),
    ]
    story_sections = [
        DatasetStorySection(
            section_id=f"dataset-story-{field}",
            heading=heading,
            text=text,
            # A scalar field carries a single source's text. ``field_evidence_source_ids`` lists every
            # source that offered a value, including the ones _pick_scalar discarded, so stamping
            # the whole list onto the card asserts corroboration that never happened. The winner is
            # first: both loops walk ``present`` in trust order and the winner is the first non-empty.
            source_ids=(field_sources.get(field) or source_ids)[:1],
        )
        for field, heading, text in story_fields
        if text.strip()
    ]
    scale_facts = [
        ProposalSafeScaleFact(
            scale_fact_id=fact.scale_fact_id,
            quantity_kind=fact.quantity_kind,
            value_text=fact.value_text,
            source_ids=fact.source_ids,
        )
        for fact in narrative.scale_facts
        if fact.proposal_safe and not fact.planner_stage_only
    ]
    if not scale_facts and narrative.broad_scale.strip():
        scale_facts = [
            ProposalSafeScaleFact(
                scale_fact_id="dataset-scale-broad",
                quantity_kind="broad_scale",
                value_text=narrative.broad_scale,
                source_ids=(field_sources.get("broad_scale") or source_ids)[:1],
            )
        ]
    return DatasetContextPack(
        dataset_id=narrative.dataset_id,
        narrative_id=narrative.dataset_narrative_id,
        review_id=f"dataset-context-review-{narrative.dataset_narrative_id}",
        story_sections=story_sections,
        proposal_safe_scale_facts=scale_facts,
        broad_variable_taxonomy=narrative.major_variables,
        task_event_vocabulary=narrative.broad_interventions,
        opportunity_cards=[
            DatasetOpportunityCard(
                opportunity_id=f"dataset-opportunity-{index:02d}",
                statement=value,
                source_ids=_item_sources(narrative, "reuse_opportunities", index - 1, source_ids),
            )
            for index, value in enumerate(narrative.reuse_opportunities, start=1)
        ],
        limitation_cards=[
            DatasetLimitationCard(
                limitation_id=f"dataset-limitation-{index:02d}",
                statement=value,
                source_ids=_item_sources(
                    narrative, "known_high_level_limitations", index - 1, source_ids
                ),
            )
            for index, value in enumerate(narrative.known_high_level_limitations, start=1)
        ],
        forbidden_inference_notice=(
            "Dataset facts are proposal-stage inspiration only; feasibility is checked later by an isolated planner branch."
        ),
    )


def _proposal_stage_guidance() -> ProposalStageGuidance:
    return ProposalStageGuidance(
        allowed_claim_levels=[
            ClaimLevel.DESCRIPTIVE,
            ClaimLevel.ASSOCIATIONAL,
            ClaimLevel.PREDICTIVE,
        ],
        forbidden_outputs=[
            "Do not produce executable analysis specifications.",
            "Do not assert feasibility from proposal context.",
            "Do not use downstream bridge artifacts.",
        ],
        uncertainty_policy=(
            "State ambiguous constructs and dataset assumptions explicitly. "
            "Ambitious questions are allowed; exact operationalization belongs to planning."
        ),
    )


def _rank_topic_source_ids(
    brief: TopicEvidenceBrief,
    source_table: R5TopicEvidenceSourceTable,
) -> list[str]:
    cited: list[str] = []
    for claim in brief.claims:
        cited.extend(_claim_source_ids(claim))
    cited_set = set(cited)
    records = [record for record in source_table.records if record.source_record_id in cited_set]
    records.sort(
        key=lambda record: (
            -float(record.ranking_features.get("metadata_quality_score", 0.0)),
            -float(record.ranking_features.get("relevance_score", 0.0)),
            record.source_record_id,
        )
    )
    ranked = [record.source_record_id for record in records]
    unknown = sorted(cited_set - set(ranked))
    if unknown:
        raise ValueError(
            "TopicEvidenceBrief cites sources absent from source table: " + ", ".join(unknown)
        )
    return ranked


def _claim_source_ids(claim: TopicEvidenceClaim) -> list[str]:
    # source_record_ids are the authoritative IDs used by the source table.
    # source_refs may still carry legacy bibliographic refs such as DOIs.
    if claim.source_record_ids:
        return list(dict.fromkeys(claim.source_record_ids))
    return list(dict.fromkeys(claim.source_refs))


def _excerpt_ids_for_claim(
    claim: TopicEvidenceClaim,
    excerpt_by_source: dict[str, list[str]],
) -> list[str]:
    excerpt_ids: list[str] = []
    for source_id in _claim_source_ids(claim):
        excerpt_ids.extend(excerpt_by_source.get(source_id, []))
    if not excerpt_ids:
        raise ValueError(f"Topic claim lacks exportable source excerpts: {claim.claim_id}")
    return list(dict.fromkeys(excerpt_ids))


def _source_roles_for_claims(
    source_id: str,
    claims: list[TopicEvidenceClaim],
    *,
    gap_ids_by_source: dict[str, list[str]],
    close_prior_ids_by_source: dict[str, list[str]],
    method_limit_ids_by_source: dict[str, list[str]],
) -> list[SourceEvidenceRole]:
    roles = {SourceEvidenceRole.FIELD_STATE_BACKGROUND}
    if gap_ids_by_source.get(source_id):
        roles.add(SourceEvidenceRole.SUPPORTS_ACCEPTED_GAP)
    if close_prior_ids_by_source.get(source_id):
        roles.add(SourceEvidenceRole.CLOSE_PRIOR_OR_COMPETING_WORK)
    if method_limit_ids_by_source.get(source_id):
        roles.add(SourceEvidenceRole.METHOD_LIMIT_OR_FEASIBILITY_CONSTRAINT)
    if any(source_id in _claim_source_ids(claim) for claim in claims):
        roles.add(SourceEvidenceRole.SUPPORTS_REVIEWED_CLAIM)
    return sorted(roles, key=lambda role: role.value)


def _field_state_capsule_from_brief(brief: TopicEvidenceBrief) -> list[ReviewedSynthesisSection]:
    """Two sections rebuilt from the brief. This is NOT the run's field-state synthesis.

    Measured on the 2026-08-14 ibl leg: this capsule is 1,919 characters, of which the first section
    is `canonical_scope` -- which the drafter writes as the comma-joined search-term list, so the
    field named `synthesis` there contained the run's own INPUT echoed back. The run's real field
    synthesis is 11 sections and ~12.6k characters, is independently graded, and is not opened by
    this projection. Delivering it is a separate, measured change; until then this function must at
    least not present a term list to the proposer as though the field had been synthesised.
    """

    sections: list[ReviewedSynthesisSection] = []
    if brief.canonical_scope.strip():
        sections.append(
            ReviewedSynthesisSection(
                section_id="topic-field-state-scope",
                heading="Search scope (terms, not synthesis)",
                synthesis=(
                    "The literature below was retrieved for these terms. This is the scope "
                    f"statement itself, not a synthesis of the field: {brief.canonical_scope}"
                ),
                claim_ids=[claim.claim_id for claim in brief.claims[:6]],
                source_record_ids=list(
                    dict.fromkeys(
                        source_id
                        for claim in brief.claims
                        for source_id in _claim_source_ids(claim)
                    )
                )[:12],
            )
        )
    if brief.unresolved_tensions:
        sections.append(
            ReviewedSynthesisSection(
                section_id="topic-field-state-open-tensions",
                heading="Open tensions",
                synthesis=" ".join(brief.unresolved_tensions[:3]),
                claim_ids=[
                    claim.claim_id
                    for claim in brief.claims
                    if claim.status == TopicEvidenceClaimStatus.OPEN_QUESTION
                ],
                source_record_ids=list(
                    dict.fromkeys(
                        source_id
                        for claim in brief.claims
                        for source_id in _claim_source_ids(claim)
                    )
                )[:12],
            )
        )
    return sections


def _gap_kind(text: str) -> OpenGapKind:
    lowered = text.lower()
    if "noise" in lowered or "covariability" in lowered:
        return OpenGapKind.NOISE_OR_SHARED_VARIABILITY
    if "latent" in lowered or "state space" in lowered:
        return OpenGapKind.LATENT_DYNAMICS
    if "multi-area" in lowered or "communication" in lowered:
        return OpenGapKind.MULTI_AREA_CODING
    if "latency" in lowered or "temporal" in lowered:
        return OpenGapKind.TEMPORAL_OR_LATENCY_GEOMETRY
    if "movement" in lowered or "body" in lowered:
        return OpenGapKind.MOVEMENT_OR_STATE_CONFOUND
    if "circuit" in lowered:
        return OpenGapKind.CIRCUIT_INTERPRETATION_LIMIT
    if "session" in lowered or "generalization" in lowered:
        return OpenGapKind.CROSS_SESSION_OR_GENERALIZATION
    if "geometry" in lowered or "representation" in lowered:
        return OpenGapKind.REPRESENTATIONAL_GEOMETRY
    return OpenGapKind.OTHER


def _source_exclusion_counts(source_table: R5TopicEvidenceSourceTable) -> dict[str, int]:
    metadata_only = 0
    title_only = 0
    diagnostic = 0
    blocked = 0
    for record in source_table.records:
        if record.snippet_kind == TopicSourceSnippetKind.METADATA:
            metadata_only += 1
        if record.snippet_kind == TopicSourceSnippetKind.TITLE_ONLY:
            title_only += 1
        if not record.can_support_claims:
            blocked += 1
        if any("off_topic" in flag or "excluded" in flag for flag in record.source_quality_flags):
            diagnostic += 1
    return {
        "metadata_only": metadata_only,
        "title_only": title_only,
        "diagnostic": diagnostic,
        "blocked": blocked,
    }
