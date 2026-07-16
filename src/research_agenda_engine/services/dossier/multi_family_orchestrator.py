"""Neutral multi-family orchestrator seam.

The back-half orchestrator implementation still lives in
``multi_family_development_orchestrator.py`` under its ``development_*``-era
names ("development" = the automated, non-human-reviewed authority mode). This
module gives the product path a neutral seam so the 5d-C de-jargon rename is a
small diff: it wraps — the SAME objects, same behavior, no fork.
"""

from .multi_family_development_orchestrator import (
    MultiFamilyDevelopmentFamilyResult,
    MultiFamilyDevelopmentRunResult,
    run_multi_family_development_orchestrator,
)

MultiFamilyFamilyResult = MultiFamilyDevelopmentFamilyResult
MultiFamilyRunResult = MultiFamilyDevelopmentRunResult
run_multi_family_orchestrator = run_multi_family_development_orchestrator

__all__ = [
    "MultiFamilyFamilyResult",
    "MultiFamilyRunResult",
    "run_multi_family_orchestrator",
]
