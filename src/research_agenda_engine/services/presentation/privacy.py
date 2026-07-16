"""Narrow privacy and link gate for detailed presentation Markdown.

The gate targets literal authority/provenance boundaries and concrete run-owned identifiers. It is
not an English-style checker and deliberately leaves ordinary scientific language untouched.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from pathlib import PurePosixPath

from ..dossier.public_text_guard import find_public_markdown_jargon

_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
_ABSOLUTE_PATH_RE = re.compile(
    r"(?:^|[\s(`])/(?:Users|Volumes|private|tmp|home|root|var|opt|etc|mnt|workspace|data|srv)/|"
    r"\b[A-Za-z]:[\\/]",
    re.MULTILINE,
)
_DIGEST_RE = re.compile(r"\b[0-9a-f]{64}\b", re.IGNORECASE)
_INTERNAL_ID_RE = re.compile(
    r"\b(?:qfamily-branch|(?:branch|event|evidence|claim|context|session|request|thread)"
    r"[_-]id)[-_:][A-Za-z0-9][A-Za-z0-9_.:-]*\b|"
    r"\b(?:branch|event|evidence|claim|context|session|request|thread)-"
    r"(?:[A-Fa-f0-9]{16,}|[A-Fa-f0-9]{8}-[A-Fa-f0-9-]{19,})\b",
    re.IGNORECASE,
)
_QUESTION_ID_RE = re.compile(r"\b(?:qfamily|qseed|qpattern)-[A-Za-z0-9][A-Za-z0-9_.:-]*\b")
_PRIVATE_FIELD_RE = re.compile(
    r"\b(?:provider_id|origin_provider_id|session_id|request_id|thread_id|branch_id|event_id|"
    r"evidence_id|claim_id|context_id|raw_payload|input_digest|output_digest)\b",
    re.IGNORECASE,
)
_CREDENTIAL_RE = re.compile(
    r"(?:(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{12,}|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----)",
)


class PresentationMarkdownError(ValueError):
    """A candidate detailed page crossed a literal privacy or navigation boundary."""


def validate_detailed_markdown(
    text: str,
    *,
    private_tokens: Iterable[str] = (),
    required_headings: Sequence[str] = (),
) -> None:
    """Validate one complete candidate before it can replace the current detailed page."""
    if not text.startswith("# ") or not text.endswith("\n"):
        raise PresentationMarkdownError("detailed Markdown requires one H1 and a trailing newline")
    for heading in required_headings:
        if heading not in text:
            raise PresentationMarkdownError(
                f"detailed Markdown is missing required heading: {heading}"
            )
    if _ABSOLUTE_PATH_RE.search(text):
        raise PresentationMarkdownError("detailed Markdown contains a local absolute path")
    if _DIGEST_RE.search(text):
        raise PresentationMarkdownError("detailed Markdown contains a digest")
    if _INTERNAL_ID_RE.search(text) or _QUESTION_ID_RE.search(text):
        raise PresentationMarkdownError("detailed Markdown contains an internal identifier")
    if _PRIVATE_FIELD_RE.search(text):
        raise PresentationMarkdownError("detailed Markdown names a private provenance field")
    if _CREDENTIAL_RE.search(text):
        raise PresentationMarkdownError("detailed Markdown contains credential-shaped text")
    jargon = find_public_markdown_jargon(text)
    if jargon:
        raise PresentationMarkdownError(
            "detailed Markdown contains internal project jargon: " + ", ".join(jargon)
        )
    visible_text = _text_without_link_targets(text)
    for token in private_tokens:
        token = token.strip()
        if len(token) >= 6 and re.search(
            rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])", visible_text
        ):
            raise PresentationMarkdownError("detailed Markdown contains a run-private token")
    for href in _MARKDOWN_LINK_RE.findall(text):
        _validate_href(href.strip())


def _validate_href(href: str) -> None:
    lower = href.lower()
    base = href.split("#", 1)[0].split("?", 1)[0]
    if not href or any(char in href for char in ("\n", "\r", "\x00")):
        raise PresentationMarkdownError("detailed Markdown contains a malformed link")
    if lower.startswith(("file:", "data:", "javascript:")):
        raise PresentationMarkdownError("detailed Markdown contains a private or unsafe link")
    if base.lower().endswith((".pdf", ".yaml", ".yml", ".json")):
        raise PresentationMarkdownError("detailed Markdown links to a raw or hidden artifact")
    if lower.startswith(("https://", "http://")):
        return
    if href.startswith("#"):
        return
    path = PurePosixPath(base)
    if path.is_absolute() or ".." in path.parts or "\\" in base:
        raise PresentationMarkdownError("detailed Markdown link escapes its public directory")


def _text_without_link_targets(text: str) -> str:
    """Keep visible labels/prose while excluding explicitly allowed navigation destinations."""
    return _MARKDOWN_LINK_RE.sub(lambda match: match.group(0).replace(match.group(1), ""), text)
