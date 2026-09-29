"""Commit diff analyzer categorizing file changes into semantic development phases."""

from enum import StrEnum
from pathlib import Path
from typing import NamedTuple

from false_comm.git.adapter import GitAdapter


class SemanticPhase(StrEnum):
    INTERFACE_SCHEMA = "interface_schema"  # Models, interfaces, schemas, types, configs
    CORE_LOGIC = "core_logic"  # Core logic, algorithms, engines, services
    TESTS = "tests"  # Test files, fixtures, mocks
    DOCS_POLISH = "docs_polish"  # Documentation, readme, changelog, helpers


class DiffFileEntry(NamedTuple):
    path: str
    status: str  # A (Added), M (Modified), D (Deleted)
    lines_added: int
    lines_deleted: int
    phase: SemanticPhase


class CommitDiffAnalysis(NamedTuple):
    commit_sha: str
    original_message: str
    total_files: int
    total_added: int
    total_deleted: int
    files_by_phase: dict[SemanticPhase, list[DiffFileEntry]]


class ReplayAnalyzer:
    """Extracts and categorizes changes from an existing Git commit or reference."""

    def __init__(self, git_adapter: GitAdapter) -> None:
        self.git = git_adapter

    def categorize_path(self, path_str: str) -> SemanticPhase:
        """Classify a relative file path into a developer semantic phase."""
        lower = path_str.lower()
        parts = Path(lower).parts

        # Tests
        if any("test" in p or "spec" in p for p in parts) or lower.endswith(
            ("_test.py", ".spec.ts", ".test.ts", "_test.go")
        ):
            return SemanticPhase.TESTS

        # Docs and polish
        if (
            any("doc" in p for p in parts)
            or lower.endswith((".md", ".rst", ".txt"))
            or "readme" in lower
            or "license" in lower
        ):
            return SemanticPhase.DOCS_POLISH

        # Interface, models, config
        if any(
            p
            in {"model", "models", "schema", "schemas", "types", "interfaces", "config", "configs"}
            for p in parts
        ):
            return SemanticPhase.INTERFACE_SCHEMA
        if lower.endswith(
            ("types.ts", "models.py", "schema.json", "config.yaml", "config.py", ".env.example")
        ):
            return SemanticPhase.INTERFACE_SCHEMA

        # Core logic default
        return SemanticPhase.CORE_LOGIC

    def analyze_commit(self, commit_ref: str) -> CommitDiffAnalysis:
        """Inspect a commit ref and return categorized diff analysis."""
        # Get commit message
        msg_res = self.git.run_git(["log", "-1", "--format=%B", commit_ref])
        orig_msg = msg_res.stdout.strip()

        # Get diff stats: additions, deletions, path
        numstat_res = self.git.run_git(["show", "--numstat", "--format=", commit_ref])

        files_by_phase: dict[SemanticPhase, list[DiffFileEntry]] = {
            phase: [] for phase in SemanticPhase
        }
        total_added = 0
        total_deleted = 0

        for line in numstat_res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                added_str, deleted_str, path = parts[0], parts[1], parts[2]
                added = int(added_str) if added_str.isdigit() else 0
                deleted = int(deleted_str) if deleted_str.isdigit() else 0
                total_added += added
                total_deleted += deleted

                phase = self.categorize_path(path)
                entry = DiffFileEntry(
                    path=path,
                    status="M" if deleted > 0 and added > 0 else ("A" if added > 0 else "M"),
                    lines_added=added,
                    lines_deleted=deleted,
                    phase=phase,
                )
                files_by_phase[phase].append(entry)

        all_entries = [e for group in files_by_phase.values() for e in group]

        return CommitDiffAnalysis(
            commit_sha=commit_ref,
            original_message=orig_msg,
            total_files=len(all_entries),
            total_added=total_added,
            total_deleted=total_deleted,
            files_by_phase=files_by_phase,
        )
