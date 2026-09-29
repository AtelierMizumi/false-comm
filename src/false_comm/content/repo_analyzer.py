"""Analyzes target repository to detect language, directory conventions, and commit style."""

import re
import subprocess
from pathlib import Path
from typing import NamedTuple

from false_comm.models.config import MessageStyle


class RepoCharacteristics(NamedTuple):
    """Discovered characteristics of the target repository."""

    primary_language: str
    detected_scopes: list[str]
    detected_style: MessageStyle
    existing_files: list[str]
    has_tests: bool
    has_docs: bool


class RepoAnalyzer:
    """Inspects file tree and existing Git history."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def analyze(self) -> RepoCharacteristics:
        """Inspect repository files and commit history."""
        # Detect directories for potential scopes
        scopes: list[str] = []
        existing_files: list[str] = []
        has_tests = False
        has_docs = False
        lang_counts: dict[str, int] = {"python": 0, "typescript": 0, "javascript": 0, "generic": 0}

        ignore_dirs = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "dist",
            "build",
            "__pycache__",
            ".pytest_cache",
        }

        for item in self.repo_root.iterdir():
            if item.name.startswith(".") and item.name != ".github":
                continue
            if item.is_dir() and item.name not in ignore_dirs:
                scopes.append(item.name.lower())
                if "test" in item.name.lower():
                    has_tests = True
                if "doc" in item.name.lower():
                    has_docs = True

        # Scan top 100 files for language detection
        file_count = 0
        for p in self.repo_root.rglob("*"):
            if file_count > 150:
                break
            if any(part in ignore_dirs for part in p.parts):
                continue
            if p.is_file():
                file_count += 1
                rel = str(p.relative_to(self.repo_root))
                existing_files.append(rel)
                suffix = p.suffix.lower()
                if suffix == ".py":
                    lang_counts["python"] += 1
                elif suffix in {".ts", ".tsx"}:
                    lang_counts["typescript"] += 1
                elif suffix in {".js", ".jsx"}:
                    lang_counts["javascript"] += 1
                else:
                    lang_counts["generic"] += 1

        primary_lang = max(lang_counts, key=lang_counts.get)  # type: ignore

        # Inspect recent commit messages to match style
        detected_style = self._detect_commit_style()

        default_scopes = ["core", "utils", "config", "api", "cli"]
        final_scopes = list(dict.fromkeys(scopes + default_scopes))[:12]

        return RepoCharacteristics(
            primary_language=primary_lang,
            detected_scopes=final_scopes,
            detected_style=detected_style,
            existing_files=existing_files[:50],
            has_tests=has_tests,
            has_docs=has_docs,
        )

    def _detect_commit_style(self) -> MessageStyle:
        """Inspect last 20 git commits to infer conventional vs freeform style."""
        try:
            res = subprocess.run(
                ["git", "-C", str(self.repo_root), "log", "-n", "20", "--format=%s"],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0 or not res.stdout.strip():
                return MessageStyle.CONVENTIONAL

            lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            if not lines:
                return MessageStyle.CONVENTIONAL

            conventional_pattern = re.compile(
                r"^(feat|fix|docs|style|refactor|perf|test|chore|ci|build)(\([^)]+\))?:"
            )
            conventional_matches = sum(1 for line in lines if conventional_pattern.match(line))

            ratio = conventional_matches / len(lines)
            if ratio >= 0.5:
                return MessageStyle.CONVENTIONAL
            if ratio >= 0.2:
                return MessageStyle.MIXED
            return MessageStyle.FREEFORM
        except Exception:
            return MessageStyle.CONVENTIONAL
