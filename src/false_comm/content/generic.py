"""Generic content strategy generating incremental docs, configs, and helper scripts."""

from pathlib import Path

from false_comm.content.base import ContentStrategy
from false_comm.content.repo_analyzer import RepoCharacteristics
from false_comm.models.commit import CommitAction, FileChange


class GenericContentStrategy(ContentStrategy):
    """Produces realistic, incremental documentation and tooling diffs."""

    DOC_TOPICS = [
        (
            "docs/architecture.md",
            "# System Architecture\n\n## Component Overview\n\n",
            "### Component Lifecycle\n- Initialization and dependency injection\n- Graceful shutdown handlers\n",
        ),
        (
            "docs/setup.md",
            "# Developer Setup\n\n## Environment Variables\n\n",
            "- `DEBUG`: Set to `true` for verbose diagnostic output\n- `LOG_LEVEL`: Configurable logging threshold\n",
        ),
        (
            "docs/troubleshooting.md",
            "# Troubleshooting Guide\n\n## Common Issues\n\n",
            "### Connection Timeouts\nEnsure local firewall permits traffic on assigned testing ports.\n",
        ),
        (
            "docs/api_reference.md",
            "# API Reference\n\n## Response Envelopes\n\n",
            '```json\n{\n  "status": "success",\n  "data": {}\n}\n```\n',
        ),
        (
            "docs/changelog.md",
            "# Changelog\n\n## Unreleased\n\n",
            "- Improved error handling and input sanitization\n- Performance optimization in batch parser\n",
        ),
    ]

    SCRIPT_TOPICS = [
        (
            "scripts/dev_healthcheck.sh",
            "#!/usr/bin/env bash\n# Health check helper\n\n",
            "echo 'Checking system dependencies...'\ncommand -v git >/dev/null || exit 1\n",
        ),
        (
            "scripts/lint_helper.sh",
            "#!/usr/bin/env bash\n# Lint helper script\n\n",
            "echo 'Running repository validation checks...'\n",
        ),
    ]

    def __init__(
        self, repo_root: Path, characteristics: RepoCharacteristics, seed: int | None = None
    ) -> None:
        super().__init__(repo_root, characteristics, seed)
        self._virtual_content: dict[str, str] = {}

    def _get_current_content(self, rel_path: str) -> str:
        """Get the current content (from in-memory planned state or disk)."""
        if rel_path in self._virtual_content:
            return self._virtual_content[rel_path]
        full_path = self.repo_root / rel_path
        if full_path.is_file():
            try:
                content = full_path.read_text(encoding="utf-8")
                self._virtual_content[rel_path] = content
                return content
            except Exception:
                pass
        return ""

    def generate_changes(self, commit_type: str, scope: str, step_index: int) -> list[FileChange]:
        """Generate one or two realistic file changes with guaranteed incremental diffs."""
        changes: list[FileChange] = []

        if commit_type in {"docs", "chore"} or self.rng.random() < 0.60:
            rel_path, header, entry = self.rng.choice(self.DOC_TOPICS)
            existing = self._get_current_content(rel_path)

            if not existing:
                new_content = header + entry + f"\n<!-- initial documentation for {scope} -->\n"
                action = CommitAction.CREATE
            else:
                timestamp_comment = f"\n<!-- updated step {step_index} ({scope}) -->\n"
                new_content = existing.rstrip() + "\n\n" + entry + timestamp_comment
                action = CommitAction.MODIFY

            self._virtual_content[rel_path] = new_content
            changes.append(
                FileChange(
                    relative_path=rel_path,
                    action=action,
                    content=new_content,
                    original_content=existing or None,
                    diff_summary=f"Update {rel_path} with {scope} details",
                )
            )
        else:
            rel_path, header, entry = self.rng.choice(self.SCRIPT_TOPICS)
            existing = self._get_current_content(rel_path)

            step_line = f"# Step {step_index}: configure {scope}\n"
            if not existing:
                new_content = header + step_line + entry
                action = CommitAction.CREATE
            else:
                new_content = existing.rstrip() + "\n\n" + step_line + entry
                action = CommitAction.MODIFY

            self._virtual_content[rel_path] = new_content
            changes.append(
                FileChange(
                    relative_path=rel_path,
                    action=action,
                    content=new_content,
                    original_content=existing or None,
                    diff_summary=f"Enhance {rel_path} for {scope}",
                )
            )

        return changes
