from __future__ import annotations

from enum import StrEnum


class FrontHalfAuthorityCeiling(StrEnum):
    """Maximum authority a front-half product may earn without new evidence review."""

    VERIFIED = "verified"
    PROVISIONAL_INSPIRATION = "provisional_inspiration"
