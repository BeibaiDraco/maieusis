from __future__ import annotations

from pathlib import Path

from ...schemas.question_family import QuestionFamilyShortlistManifest
from ...schemas.question_family_branch import QuestionFamilyBranch
from .branch_manager import QuestionFamilyBranchManager


class QuestionFamilyRunManager:
    def __init__(self, root: str | Path, *, run_id: str) -> None:
        self.branch_manager = QuestionFamilyBranchManager(root, run_id=run_id)

    def create_planning_branches(
        self,
        manifest: QuestionFamilyShortlistManifest,
    ) -> list[QuestionFamilyBranch]:
        return [
            self.branch_manager.create_branch(shortlisted, context_id=manifest.context_id)
            for shortlisted in manifest.shortlisted
        ]
