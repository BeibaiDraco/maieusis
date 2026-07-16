"""The strict user-input contract for a dataset.

For ANY dataset the user provides AT MOST: a `dataset_id`, an OPTIONAL seed `link`, and OPTIONAL
description `docs`. At least one of ``link`` or ``docs`` is required. The system derives everything
else (narrative, resources, exploration) from these. Documentation-side Source A consumes the link;
Source D consumes user-provided description files.

This module carries no dataset-specific names; it is enforced by the dataset-agnostic guard.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DatasetSeed(BaseModel):
    """One dataset's seed: ``dataset_id`` plus a link, description docs, or both."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    link: str
    docs: list[Path] = Field(default_factory=list)

    @field_validator("dataset_id")
    @classmethod
    def require_dataset_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("DatasetSeed requires a non-empty dataset_id")
        return value

    @field_validator("link")
    @classmethod
    def normalize_link(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def require_link_or_docs(self) -> DatasetSeed:
        if not self.link and not self.docs:
            raise ValueError("DatasetSeed requires a link or at least one description doc")
        return self
