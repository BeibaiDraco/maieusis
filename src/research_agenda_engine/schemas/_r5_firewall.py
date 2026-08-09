from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel

FORBIDDEN_KEY_TOKENS = (
    "analysis_contract",
    "analysiscontract",
    "api_key",
    "auth_token",
    "branch_id",
    "bridge_approval",
    "bridge_authorized",
    "capability_registry",
    "capabilityregistry",
    "capability_receipt",
    "column",
    "columns",
    "confirmation_outcome",
    "confirmation_result",
    "credential",
    "credentials",
    "contract_readiness",
    "contractreadinessproof",
    "coverage_matrix",
    "dataframe_schema",
    "exact_column",
    "exact_columns",
    "exact_coverage",
    "executor_receipt",
    "executorreceiptbundle",
    "execution_authorized",
    "execution_result",
    "file_path",
    "filesystem_path",
    "joint_coverage",
    "jointcoveragereport",
    "operator_probe",
    "operator_receipt",
    "operatorprobereceipt",
    "owner_session_id",
    "parquet_schema",
    "question_card",
    "questioncard",
    "qbench",
    "readiness_proof",
    "required_variables",
    "row_count",
    "r4_readiness",
    "schema",
    "secret",
    "session_count",
    "table_schema",
    "workspace_path",
    "trial_count",
)

FORBIDDEN_TEXT_TOKENS = (
    "analysiscontract",
    "branch_id",
    "capabilityregistry",
    "confirmation outcome",
    "contractreadinessproof",
    "executorreceiptbundle",
    "execution authorization",
    "execution result",
    "jointcoveragereport",
    "joint coverage report",
    "operator probe receipt",
    "operator receipt",
    "operatorprobereceipt",
    "owner_session_id",
    "qbench",
    "questioncard",
    "readiness proof",
    "bridge approval",
    "execution is authorized",
    "approved for execution",
)

# The stable phrase a caller can key off to report that the FIREWALL, rather than a malformed reply,
# rejected generated prose. Callers must relay this cause without echoing the matched text.
FIREWALL_REJECTION_MARKER = "proposer-forbidden evidence"

# What makes a claim about columns a DISCLOSURE rather than domain prose: a token shaped like a
# machine identifier -- snake_case, camel_snake (`stimOn_times`), or an explicitly quoted/backticked
# name. Scientific writing does not produce these; a leaked schema is made of them.
_SCHEMA_IDENTIFIER_TOKEN = r"(?:[`'\"][A-Za-z_][\w.]*[`'\"]|\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+\b)"

FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"\bn[_\s-]?(trials|sessions|subjects|rows)\s*[=:]\s*\d+", re.IGNORECASE),
    re.compile(r"\b(row|trial|session|subject)\s+count\s*(is|=|:)?\s*\d+", re.IGNORECASE),
    re.compile(r"\b(joint|crossed)\s+coverage\s+(matrix|count|table)", re.IGNORECASE),
    re.compile(
        r"\b(choice|feedback_times|stim_on_times|probability_left)\s+column\b", re.IGNORECASE
    ),
    re.compile(r"\b(?:column|columns|schema)\s*(?:named|=|:)\s*\S+", re.IGNORECASE),
    # A schema noun is schema language on its own and needs no identifier.
    re.compile(
        r"\b(?:exact\s+)?(?:table|dataframe|parquet)\s+schema\b"
        r".{0,60}\b(?:exists?|includes?|contains?|verified|available)\b",
        re.IGNORECASE,
    ),
    # The bare noun does NOT. `column` alone is ordinary science vocabulary -- "the water column
    # contains", "total column ozone is available", "the atmospheric column includes", "a cortical
    # column contains" -- and this was the ONE pattern in this family with no identifier requirement
    # (:89 names real column identifiers, :91 requires `named|=|:` plus a token, the bridge/receipt
    # patterns below require a digit-bearing token). It runs inside the generation mirror, where the
    # batch is one list parse, so a single variant's sentence failed the WHOLE QuestionFamilyBatch --
    # and `first_raw = _generate()` has no retry, so the run ended at Stage D with zero families and
    # zero dossiers. One ordinary word could zero a leg.
    #
    # The boundary is unchanged and the SCOPE stays batch-wide: a genuine disclosure contaminates the
    # shared context, so failing closed is right there. Only the predicate is fixed -- a claim about
    # columns must carry what makes it a disclosure: a data-container qualifier, or an
    # identifier-shaped token. "total column ozone is available" names no column; "Columns include
    # stimOn_times, feedback_times, and choice" does, and that exact phrasing is what a real
    # branch-to-proposer leak looks like in this project's own planner evidence.
    # `exact column(s)` is the disclosure by itself -- it asserts that the real schema was inspected,
    # and no scientific writer describes "the exact atmospheric column". No identifier required.
    re.compile(
        r"\bexact\s+columns?\b.{0,60}\b(?:exists?|includes?|contains?|verified|available)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:table|dataframe|parquet|csv|data|dataset|trials?|sessions?)\s+columns?\b"
        r".{0,60}\b(?:exists?|includes?|contains?|verified|available)\b",
        re.IGNORECASE,
    ),
    # The identifier may sit in any of three positions relative to the `column ... verb` core, and
    # all three are the same disclosure: "the probability_left column exists", "exact column
    # trials.feedback_times exists", "Columns include stimOn_times". Enumerated rather than merged so
    # each window stays bounded and readable.
    re.compile(
        _SCHEMA_IDENTIFIER_TOKEN + r".{0,40}\b(?:exact\s+)?columns?\b"
        r".{0,60}\b(?:exists?|includes?|contains?|verified|available)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:exact\s+)?columns?\b.{0,60}?"
        + _SCHEMA_IDENTIFIER_TOKEN
        + r".{0,60}\b(?:exists?|includes?|contains?|verified|available)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:exact\s+)?columns?\b"
        r".{0,60}\b(?:exists?|includes?|contains?|verified|available)\b"
        r".{0,80}" + _SCHEMA_IDENTIFIER_TOKEN,
        re.IGNORECASE,
    ),
    re.compile(r"\bconfirmation\s+(?:outcome|result)\s+(?:was|is|=|:)", re.IGNORECASE),
    re.compile(
        r"\b(?:analysis\s*contract|question\s*card)\s+"
        r"(?:id\s*[:=]\s*)?(?=[a-z0-9_.:-]*\d)[a-z0-9][a-z0-9_.:-]*\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:operator|executor|capability)\s+(?:probe\s+)?receipt\s+"
        r"(?:id\s*[:=]\s*)?(?=[a-z0-9_.:-]*\d)[a-z0-9][a-z0-9_.:-]*\b",
        re.IGNORECASE,
    ),
)

HARD_TEXT_PATTERNS = (
    re.compile(
        r"\b[a-z0-9_]*(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret|credential)"
        r"\s*[:=]\s*\S+",
        re.IGNORECASE,
    ),
    re.compile(r"\bbearer\s+[a-z0-9._~+/-]{4,}\b", re.IGNORECASE),
    re.compile(r"(?<![\w:/])/(?:Users|home|private|var|tmp|etc|opt)/[^\s,;]+"),
    re.compile(r"\b[a-z]:\\(?:Users|home|private|var|tmp|etc|opt)\\[^\s,;]+", re.IGNORECASE),
    # Concrete bridge artifacts/receipts remain forbidden even when a surrounding sentence is
    # phrased as a disclaimer. The proposer never needs their IDs.
    FORBIDDEN_TEXT_PATTERNS[-2],
    FORBIDDEN_TEXT_PATTERNS[-1],
    # A concrete schema/count/coverage/confirmation/result/authority assertion discloses the hard
    # fact even when earlier prose says not to use it. Negation may protect only the generic boundary
    # vocabulary below, never a value-bearing assertion.
    *FORBIDDEN_TEXT_PATTERNS,
)

_NEGATION_SCOPE_BOUNDARY_RE = re.compile(r"[.!?;:\n]")
_NEGATION_SCOPE_MAX_WORDS = 12
_NEGATION_OPERATORS = frozenset({"not", "never", "without", "avoid", "forbid"})
_POSTFIX_NEGATION_AUXILIARIES = frozenset(
    {
        "am",
        "are",
        "be",
        "been",
        "being",
        "can",
        "could",
        "did",
        "do",
        "does",
        "had",
        "has",
        "have",
        "is",
        "may",
        "might",
        "must",
        "shall",
        "should",
        "was",
        "were",
        "will",
    }
)
_NEGATED_REFERENCE_CONJUNCTIONS = frozenset({"and", "or"})
_NEGATED_REFERENCE_DETERMINERS = frozenset({"a", "an", "any", "the"})
_NEGATION_CLAUSE_BOUNDARIES = frozenset(
    {"although", "as", "because", "but", "since", "though", "where", "whereas"}
)
_NEGATED_REFERENCE_NOMINAL_ADJUNCTS = frozenset(
    {"after", "as", "before", "during", "for", "from", "in", "throughout", "within"}
)
_NEGATED_REFERENCE_WORKFLOW_DETERMINERS = frozenset({"a", "an", "any", "the"})
_NEGATED_REFERENCE_WORKFLOW_ADJECTIVES = frozenset(
    {
        "broad",
        "coarse",
        "current",
        "early",
        "generic",
        "initial",
        "optional",
        "provisional",
        "scientific",
        "source",
        "structured",
        "verified",
    }
)
_NEGATED_REFERENCE_WORKFLOW_TERMS = frozenset(
    {
        "context",
        "development",
        "evidence",
        "formation",
        "planning",
        "proposal",
        "question",
        "research",
        "review",
        "workflow",
    }
)
_NEGATED_REFERENCE_WORKFLOW_GERUNDS = frozenset(
    {"developing", "forming", "planning", "proposing", "researching", "reviewing"}
)
_ACTIVE_NEGATION_ACTIONS = frozenset(
    {
        "access",
        "accessing",
        "claim",
        "claiming",
        "consider",
        "considering",
        "create",
        "creating",
        "generate",
        "generating",
        "inspect",
        "inspecting",
        "persist",
        "persisting",
        "reference",
        "referencing",
        "request",
        "requesting",
        "use",
        "using",
    }
)
_ACTIVE_NEGATION_REFERENCE_GLUE = frozenset(
    {
        "a",
        "an",
        "and",
        "any",
        "column",
        "columns",
        "or",
        "schema",
        "table",
        "the",
    }
) | frozenset(
    part for token in FORBIDDEN_TEXT_TOKENS for part in re.findall(r"[a-z]+", token.casefold())
)


def assert_proposal_safe_payload(value: Any, *, context: str) -> None:
    """Reject evidence types that cannot enter R5 proposer context."""

    found = _find_forbidden_payload(value, path=context)
    if found:
        raise ValueError(f"{context} contains {FIREWALL_REJECTION_MARKER}: {found}")


def _find_forbidden_payload(value: Any, *, path: str) -> str:
    if isinstance(value, BaseModel):
        return _find_forbidden_payload(value.model_dump(mode="python"), path=path)
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            normalized_key = _normalize(key_text)
            if any(_normalize(token) in normalized_key for token in FORBIDDEN_KEY_TOKENS):
                return f"{path}.{key_text}"
            found = _find_forbidden_payload(nested, path=f"{path}.{key_text}")
            if found:
                return found
    elif isinstance(value, str):
        if _contains_forbidden_text(value):
            return path
    elif isinstance(value, Sequence) and not isinstance(value, bytes | bytearray):
        for index, item in enumerate(value):
            found = _find_forbidden_payload(item, path=f"{path}[{index}]")
            if found:
                return found
    return ""


def _normalize(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _contains_forbidden_text(value: str) -> bool:
    if any(pattern.search(value) for pattern in HARD_TEXT_PATTERNS):
        return True
    for token in FORBIDDEN_TEXT_TOKENS:
        for match in _token_matches(value, token):
            if not _is_locally_negated(value, match.start(), match.end()):
                return True
    return False


def _token_matches(value: str, token: str) -> list[re.Match[str]]:
    parts = [re.escape(part) for part in re.split(r"[\s_-]+", token.casefold()) if part]
    pattern = r"(?<![a-z0-9])" + r"[\s_-]*".join(parts) + r"s?(?![a-z0-9])"
    return list(re.finditer(pattern, value, re.IGNORECASE))


def _is_locally_negated(value: str, forbidden_start: int, forbidden_end: int) -> bool:
    """Recognize bounded active or passive negation without enumerating prose phrases.

    Concrete value-bearing assertions have already been rejected by ``HARD_TEXT_PATTERNS``. For
    generic boundary vocabulary, a grammatical negation operator may protect only a nearby mention
    inside the same punctuation segment. A postfix operator is accepted only through modal/copular
    auxiliaries (``outcome must not ...``), so arbitrary later negation cannot mask the mention.
    """

    segment_start = 0
    for prior_boundary in _NEGATION_SCOPE_BOUNDARY_RE.finditer(value, 0, forbidden_start):
        segment_start = prior_boundary.end()
    next_boundary = _NEGATION_SCOPE_BOUNDARY_RE.search(value, forbidden_end)
    segment_end = next_boundary.start() if next_boundary is not None else len(value)
    segment = value[segment_start:segment_end].casefold()
    local_start = forbidden_start - segment_start
    local_end = forbidden_end - segment_start
    words = list(re.finditer(r"\b[a-z]+(?:'[a-z]+)?\b", segment))
    before = [match for match in words if match.end() <= local_start]
    after = [match for match in words if match.start() >= local_end]

    preceding_matches = before[-_NEGATION_SCOPE_MAX_WORDS:]
    negation_matches = [
        match for match in preceding_matches if match.group() in _NEGATION_OPERATORS
    ]
    if negation_matches:
        last_negation = negation_matches[-1]
        scoped_words = [
            match.group() for match in preceding_matches if match.start() > last_negation.end()
        ]
        if _active_negation_prefix_is_explicitly_safe(scoped_words):
            return _active_negation_tail_is_explicitly_safe(segment, local_end)

    postfix_window = after[:8]
    for index, match in enumerate(postfix_window):
        word = match.group()
        if word not in _NEGATION_OPERATORS:
            continue
        prefix = [item.group() for item in postfix_window[:index]]
        if all(
            auxiliary in _POSTFIX_NEGATION_AUXILIARIES or auxiliary.endswith("ly")
            for auxiliary in prefix
        ):
            predicate_end = _postfix_negated_predicate_end(after, index, match.end())
            return _active_negation_tail_is_explicitly_safe(segment, predicate_end)
    return False


def _postfix_negated_predicate_end(
    words: list[re.Match[str]], negation_index: int, fallback_end: int
) -> int:
    """Consume auxiliaries/adverbs plus one negated predicate without naming that predicate."""

    for match in words[negation_index + 1 :]:
        word = match.group()
        if word in _POSTFIX_NEGATION_AUXILIARIES or word.endswith("ly"):
            fallback_end = match.end()
            continue
        return match.end()
    return fallback_end


def _active_negation_prefix_is_explicitly_safe(words: list[str]) -> bool:
    """Accept only a closed action-plus-reference-list grammar before the protected reference."""

    if not words:
        return True
    if words[0] not in _ACTIVE_NEGATION_ACTIONS:
        return False
    return all(word in _ACTIVE_NEGATION_REFERENCE_GLUE for word in words[1:])


def _active_negation_tail_is_explicitly_safe(segment: str, forbidden_end: int) -> bool:
    """Allow only structurally explicit active-negation tails; unknown tails stay hard.

    This deliberately does not enumerate words meaning "approved" or "granted". An earlier
    negation can protect a boundary reference only when that reference closes the clause, continues
    a list of other boundary references, or has a small grammatical adjunct that unambiguously
    belongs to the negated action. Any other affirmative-looking tail is rejected by default.
    """

    tail = segment[forbidden_end:]
    words = list(re.finditer(r"\b[a-z]+(?:'[a-z]+)?\b", tail))
    if not words:
        return True

    next_reference = _next_forbidden_reference(tail)
    if next_reference is not None:
        prefix_words = [match.group() for match in words if match.end() <= next_reference.start()]
        if all(
            word in _NEGATED_REFERENCE_CONJUNCTIONS or word in _NEGATED_REFERENCE_DETERMINERS
            for word in prefix_words
        ):
            return _active_negation_tail_is_explicitly_safe(tail, next_reference.end())

    first = words[0].group()
    remaining = [match.group() for match in words[1:]]
    if first in _NEGATED_REFERENCE_NOMINAL_ADJUNCTS:
        return _is_closed_workflow_adjunct(remaining)
    if first == "while":
        return (
            bool(remaining)
            and remaining[0] in _NEGATED_REFERENCE_WORKFLOW_GERUNDS
            and _is_closed_workflow_adjunct(remaining[1:])
        )
    return False


def _next_forbidden_reference(value: str) -> re.Match[str] | None:
    matches = [match for token in FORBIDDEN_TEXT_TOKENS for match in _token_matches(value, token)]
    return min(matches, key=lambda match: match.start()) if matches else None


def _is_closed_workflow_adjunct(words: list[str]) -> bool:
    """Accept only a small auditable proposal-workflow noun phrase.

    This is intentionally an allowlist of harmless workflow vocabulary, not a classifier for
    authority or result predicates. Unknown words therefore cannot turn a negated boundary mention
    into an uninspected affirmative clause.
    """

    if not words:
        return False
    allowed = (
        _NEGATED_REFERENCE_WORKFLOW_DETERMINERS
        | _NEGATED_REFERENCE_WORKFLOW_ADJECTIVES
        | _NEGATED_REFERENCE_WORKFLOW_TERMS
    )
    return all(word in allowed for word in words)
