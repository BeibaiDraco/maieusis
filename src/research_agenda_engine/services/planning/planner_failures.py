"""Typed family-closeout failures at the coding-agent planning boundary.

Ordinary provider exhaustion and imperfect structured output may end one family with a
user-readable warning dossier.  Integrity, isolation, authority, and confirmation-firewall
violations must remain hard blockers and must never be downgraded by the tolerant closeout path.
"""

from __future__ import annotations


class RecoverableFamilyTerminal(ValueError):
    """One family can close with a degraded dossier without invalidating its siblings."""


class CodingAgentProviderUnavailable(RecoverableFamilyTerminal):
    """The coding-agent provider was explicitly unavailable for this invocation."""


class HardFamilyIntegrityViolation(ValueError):
    """A trust-boundary violation whose untrusted products must not be promoted."""
