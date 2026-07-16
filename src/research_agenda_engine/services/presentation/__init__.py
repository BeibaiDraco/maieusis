"""Deterministic, zero-provider detailed presentation add-on."""

from .materialize import (
    materialize_detailed_presentation,
    plan_presentation_resume,
    try_materialize_detailed_presentation,
)

__all__ = [
    "materialize_detailed_presentation",
    "plan_presentation_resume",
    "try_materialize_detailed_presentation",
]
