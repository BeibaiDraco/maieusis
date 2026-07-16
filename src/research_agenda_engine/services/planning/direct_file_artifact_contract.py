from __future__ import annotations

from ...schemas.analysis_plan import DatasetInspectionSourceType

DIRECT_FILE_ARTIFACT_CONTRACT_VERSION = "direct_file_planner_artifact_contract/v1.11"

DIRECT_FILE_ALLOWED_SOURCE_TYPES: tuple[str, ...] = tuple(
    source_type.value for source_type in DatasetInspectionSourceType
)

DIRECT_FILE_FORBIDDEN_ENVELOPE_KEYS: tuple[str, ...] = (
    "tool_name",
    "run_id",
    "sources",
    "observed_claims",
    "inspection_mode",
    "rejection_id",
    "variant_rejections",
    "terminal_artifact",
)

DIRECT_FILE_ARTIFACT_CONTRACT = f"""# Direct-file planner artifact contract

contract_version: {DIRECT_FILE_ARTIFACT_CONTRACT_VERSION}

Coding-agent hosts write YAML files directly. They do not call, emulate,
or serialize MCP/scientific-dialogue tools. The tool names listed in the packet
are optional MCP owner-dialogue schema context only.

Write typed artifacts themselves, not tool-call records. Do not include these
tool-call envelope keys in any returned artifact:
{", ".join(DIRECT_FILE_FORBIDDEN_ENVELOPE_KEYS)}.
Do not use a top-level status field as a shortcut for branch rejection or a
terminal artifact outcome; DatasetFeasibilityFinding.status is the only valid
status field in this contract.

YAML formatting (STRICT — invalid YAML voids the whole run). Every free-text
string value (finding, inspection_method, reason, summary, rationale,
coverage_summary, impact_on_question, requirement, etc.) MUST be either
double-quoted or written as a block scalar (`finding: |`), ESPECIALLY any value
that contains a colon (`:`), a `#`, or spans multiple lines. An unquoted value
like `finding: defines coding directions: contrastLeft, choice` makes the parser
read `contrastLeft, choice` as a nested mapping and fails. When in doubt, quote.

Inspection evidence files are one source per YAML file under the evidence
directory. The evidence directory accepts ONLY `QuestionFamilyInspectionEvidence`;
never place a PlanningMessage there. Use this shape and omit digest fields; the trusted host computes
source_digest, query_or_command_digest, and result_digest during Collect:

Use source_type exactly as one of:
{", ".join(DIRECT_FILE_ALLOWED_SOURCE_TYPES)}.
Never use `metadata`; use `metadata_query` for metadata-level queries.

Source type selection rules:
- README, narrative, and prose docs -> documentation.
- Schema files, data dictionaries, and column definitions -> schema.
- Headers, row counts, file manifests, metadata tables, and catalog lookups -> metadata_query.
- Bounded raw rows, small source excerpts, and example files -> sample_inspection.
- Loader, adapter, or config code inspected as code -> repository_code.
- Executor docs or capability descriptions -> executor_skill.
- Toy method-recovery or synthetic planning probes -> synthetic_probe.

Evidence scope. Set `scope: family` (and leave `variant_id` empty) for evidence that
supports the whole family — a shared dataset fact that backs the family-level
conclusion. Set `scope: variant` with the active `variant_id` for evidence that
supports only one variant; a variant may not rely on a sibling variant's evidence.
Evidence may be entirely variant-scoped when each accepted variant cites evidence
that can support that variant. Every `accepted` or `accepted_requires_new_skill`
variant MUST cite at least one valid branch-local evidence record; never borrow a
sibling variant's evidence merely to create a family-level anchor.

```yaml
evidence_id: evidence-branch-local-id
branch_id: <packet.branch_id>
question_family_id: <packet.question_family_id>
scope: family
variant_id: ""
source_type: schema
source_locator: relative/or/absolute/source/path
inspection_method: Short bounded inspection method.
finding: Source-backed planning finding.
limitations:
  - Planning-only limitation.
created_by: dataset_planner
planning_only: true
confirmation_firewall_checked: true
```

Dialogue, plan, rejection, and escalation files are PlanningMessage YAML files.
Use message_type exactly as the schema name requires. Omit input_digest,
output_digest, and payload_digest; the trusted host computes them during
Collect. Family-scoped terminal messages must carry variant_outcomes.

Write every `DatasetFeasibilityFinding` PlanningMessage under the packet's
dialogue directory, never under the evidence directory. A feasibility finding is
not a terminal artifact and cannot replace the root plan/rejection/escalation.

Choose the root terminal from the per-variant outcomes, not from the weakest
sibling. If at least one active variant is `accepted` or
`accepted_requires_new_skill`, write `plan_draft.yaml` and give every other
variant its own honest non-pending rejection or escalation outcome. Write
`rejection.yaml` only when every active variant is rejected. Write
`escalation.yaml` only when every active variant requires escalation.
One unsupported variant must never erase a supported sibling.

Write the single terminal artifact at the workspace root, as a sibling of the
packet paths: a plan at `plan_draft.yaml`, a rejection at `rejection.yaml`, or a
human escalation at `escalation.yaml`. Do NOT put the terminal artifact under the
evidence or dialogue directory.

Use each `variant_outcomes[].decision` exactly as one of:
`pending`, `accepted`, `accepted_requires_new_skill`, `rejected_dataset_mismatch`,
`rejected_operationalization_failure`, `rejected_scientific_drift`,
`rejected_insufficient_evidence`, `rejected_low_scientific_value`, or
`human_escalation`. There is no `accepted_with_constraints` decision: use `accepted`
and retain every constraint in that variant's `summary` and evidence-backed limitations.

Every accepted or accepted-requires-new-skill variant in a `plan_draft` MUST have exactly one
matching `variant_analysis_plans` entry. This is the inspectable scientific plan reviewed by the
Question Owner and independent reviewer; the short `summary` does not replace it. Historical
summary-only plan drafts remain readable, but the serious direct-file route rejects them before
review. Each detailed plan must use the same branch, active question seed, scientific-intent
invariant, and evidence available to that variant. Keep it planning-only and non-executable.
Evidence must close transitively at all three levels: every
`analysis_plan.data_sources[].evidence_ids` entry must also appear in that AnalysisPlan's
`evidence_ids`, and every AnalysisPlan evidence ID must appear in the matching
`variant_outcomes[].evidence_ids`. Each cited record must be family-scoped or scoped to that exact
variant. Never borrow a sibling variant's evidence or mechanically promote it to family scope.

Claim ceilings are structured authority fields, not prose. Use `claim_ceiling` exactly as one of
`descriptive`, `predictive`, `associational`, `mechanistic`, or `causal`. Use
`claim_ceiling_components: []` unless multiple exact values from that same five-value set are
needed; when non-empty, the list MUST include the exact primary `claim_ceiling`. Put every
explanation, caveat, observational limitation, and non-causal qualification under
`interpretation_limits`, never in either claim-ceiling field. Composite labels such as
`predictive_associational` and explanatory sentences are invalid claim-ceiling values.

```yaml
message_id: message-branch-local-id
branch_id: <packet.branch_id>
scope: family
context_id: <packet.context_id>
owner_session_id: <packet.owner_session_id>
actor_role: dataset_planner
message_type: branch_rejection
provider_id: <runner-provider-id>
model_id: <runner-model-id>
session_id: <runner-session-id>
prompt_version: dataset_planner/v2
decision: rejected_dataset_mismatch
reason: Source-backed planning reason.
blocking_evidence_ids:
  - evidence-branch-local-id
alternatives_for_future_data:
  - Future data requirement.
variant_outcomes:
  - variant_id: <active_variant_id>
    question_seed_id: <matching_question_seed_id>
    decision: rejected_dataset_mismatch
    summary: Variant-specific reason.
    evidence_ids:
      - evidence-branch-local-id
```

```yaml
message_id: message-branch-local-id
branch_id: <packet.branch_id>
scope: family
context_id: <packet.context_id>
owner_session_id: <packet.owner_session_id>
actor_role: dataset_planner
message_type: plan_draft
provider_id: <runner-provider-id>
model_id: <runner-model-id>
session_id: <runner-session-id>
prompt_version: dataset_planner/v2
analysis_plan_id: plan-branch-local-id
summary: Source-backed planning summary.
unresolved_decisions: []
planner_assessment: serves_question
variant_outcomes:
  - variant_id: <active_variant_id>
    question_seed_id: <matching_question_seed_id>
    decision: accepted
    summary: Variant-specific planning summary.
    evidence_ids:
      - evidence-branch-local-id
  - variant_id: <unsupported_sibling_variant_id>
    question_seed_id: <matching_sibling_question_seed_id>
    decision: rejected_dataset_mismatch
    summary: This sibling is unsupported, while the accepted sibling keeps the family plan alive.
    evidence_ids:
      - evidence-valid-for-this-sibling
variant_analysis_plans:
  - variant_id: <active_variant_id>
    question_seed_id: <matching_question_seed_id>
    analysis_plan:
      analysis_plan_id: plan-branch-local-id-variant
      branch_id: <packet.branch_id>
      question_version_id: <matching_question_seed_id>
      refined_question: How will this variant's preserved contrast be evaluated?
      scientific_intent_invariant_id: <matching invariant_id from packet>
      population_and_scope: Population and scope preserved from the scientific intent.
      data_sources:
        - data_source_id: source-branch-local-id
          branch_id: <packet.branch_id>
          description: Source-backed dataset surface used by this variant.
          expected_grain: Documented observational grain.
          required_variables: []
          evidence_ids:
            - evidence-branch-local-id
          limitations:
            - Planning-only evidence limitation.
      construct_operationalization_ids: []
      unit_of_observation: Documented observational unit.
      unit_of_inference: Independent sampling unit for inference.
      hierarchy_and_dependence: How nesting and repeated observations will be handled.
      analysis_strategy:
        - Define the source-backed construct and variant-specific contrast.
        - Estimate it with dependence-aware validation and sensitivity checks.
      candidate_estimands:
        - Variant-specific contrast at the documented unit of inference.
      validation_strategy: Validation and method-recovery checks planned before execution.
      split_strategy: Leakage-safe split or resampling strategy.
      diagnostics:
        - Coverage, missingness, and stability diagnostics.
      negative_controls:
        - Scientifically irrelevant contrast or label control.
      positive_controls:
        - Documented structural signal that the method should recover.
      alternative_explanations:
        - Sampling or coverage imbalance.
        - Imperfect construct operationalization.
      predicted_result_patterns:
        - Pattern that would support the proposed interpretation.
        - Pattern that would weaken it.
      claim_ceiling: descriptive
      claim_ceiling_components: []
      interpretation_limits:
        - Planning evidence is not a scientific result.
      resource_estimate: Bounded estimate for the proposed analysis.
      required_new_skills: []
      unresolved_decisions: []
      why_plan_serves_question: Why the plan preserves the scientific intent and contrast.
      evidence_ids:
        - evidence-branch-local-id
      contains_executable_code: false
```

```yaml
message_id: message-branch-local-id
branch_id: <packet.branch_id>
scope: family
context_id: <packet.context_id>
owner_session_id: <packet.owner_session_id>
actor_role: dataset_planner
message_type: human_escalation_request
provider_id: <runner-provider-id>
model_id: <runner-model-id>
session_id: <runner-session-id>
prompt_version: dataset_planner/v2
decision_needed: Human decision needed.
why_agents_cannot_resolve: Source-backed reason agents cannot resolve this.
options:
  - Option text.
consequences:
  - Consequence text.
variant_outcomes:
  - variant_id: <active_variant_id>
    question_seed_id: <matching_question_seed_id>
    decision: human_escalation
    summary: Variant-specific escalation reason.
    evidence_ids:
      - evidence-branch-local-id
```

```yaml
message_id: message-branch-local-id
branch_id: <packet.branch_id>
scope: variant
variant_id: <active_variant_id>
question_seed_id: <matching_question_seed_id>
context_id: <packet.context_id>
owner_session_id: <packet.owner_session_id>
actor_role: dataset_planner
message_type: dataset_feasibility_finding
provider_id: <runner-provider-id>
model_id: <runner-model-id>
session_id: <runner-session-id>
prompt_version: dataset_planner/v2
requirement_id: requirement-branch-local-id
requirement: Planning requirement.
status: unavailable
evidence_ids:
  - evidence-branch-local-id
coverage_summary: Source-backed coverage summary.
limitations:
  - Planning-only limitation.
impact_on_question: Impact on the variant question.
```
"""
