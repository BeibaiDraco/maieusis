"""De-jargon standing gate for *rendered public output*.

Public, user-facing Markdown — the translated end-user dossier and ``summary.md`` — must never carry
development-era internal jargon: phase codes (``R5-...``), milestone codes (``M1H``), dev fixture
family IDs (``cfam-003``), or internal branch/event IDs. Those are engineering handles, not scientific
content.

This is a *pattern* net, complementary to (not a replacement for) per-run ID redaction. Redaction only
knows the *specific* IDs a given run minted; this gate catches the internal-ID *shape* even when a
stray literal (a hard-coded fixture ID, a leaked phase marker in a template) slips through. It runs at
render time inside the public-dossier / summary validators, and again in ``make hygiene`` + CI over
freshly rendered output.

It deliberately scans ONLY rendered product output — never source, prompts, or governance docs (those
legitimately name the internal phases and schemas). The redaction and hidden-audit-sidecar machinery
is untouched; this only adds a gate.
"""

from __future__ import annotations

import re

# Each entry is (human label, compiled pattern). Patterns are tuned to catch the internal-ID *shape*
# without flagging legitimate scientific prose — notably bare ``M1`` (primary motor cortex) must pass,
# so the milestone pattern requires a trailing capital letter (``M1H``).
INTERNAL_JARGON_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Dev-era phase codes: R5, R5-011, R5-008B, R5-M1H. Real product output never carries them.
    ("phase code", re.compile(r"\bR5(?:-[A-Za-z0-9]+)?\b")),
    # Milestone codes: M1B .. M1H. Letter-suffixed so bare "M1" (primary motor cortex) is NOT flagged.
    ("milestone code", re.compile(r"\bM1[A-Z]\d*\b")),
    # Dev fixture family/variant IDs: cfam-003, cfam_003, variant_cfam_003. Real families are
    # ``qfamily-...``; the lookbehind keeps mid-word "cfam" (none today) from matching.
    ("fixture family id", re.compile(r"(?<![A-Za-z])cfam[-_]\d+")),
    # Internal branch IDs: qfamily-branch-<hash> / branch-<hash>. Bare "branch" (a common word) is
    # fine; only the hashed-ID shape is flagged.
    ("internal branch id", re.compile(r"\bbranch-[0-9a-f]{6,}\b", re.I)),
    # Internal event IDs: event-<hash>.
    ("internal event id", re.compile(r"\bevent-[0-9a-f]{6,}\b", re.I)),
)


def find_public_markdown_jargon(text: str) -> list[str]:
    """Return sorted, de-duplicated labels of internal dev-era jargon present in *rendered public text*.

    An empty list means the text is clean. Mirrors ``validate_aggregate_report_text`` (the scientific
    firewall-term gate); the two are complementary and run together on public surfaces.
    """
    return sorted({label for label, pattern in INTERNAL_JARGON_PATTERNS if pattern.search(text)})
