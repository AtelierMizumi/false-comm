"""Base interface for realistic content modification strategies."""

import random
from abc import ABC, abstractmethod
from pathlib import Path

from false_comm.content.repo_analyzer import RepoCharacteristics
from false_comm.models.commit import FileChange


class ContentStrategy(ABC):
    """Abstract strategy for generating realistic, non-breaking file changes."""

    def __init__(
        self, repo_root: Path, characteristics: RepoCharacteristics, seed: int | None = None
    ) -> None:
        self.repo_root = repo_root
        self.characteristics = characteristics
        self.rng = random.Random(seed)

    @abstractmethod
    def generate_changes(self, commit_type: str, scope: str, step_index: int) -> list[FileChange]:
        """Produce a list of FileChange objects to be staged and committed."""
        pass
