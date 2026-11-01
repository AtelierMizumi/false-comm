"""Integration tests for the replay dry-run and JSON plan export feature."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from false_comm.cli.app import app
from false_comm.git.adapter import GitAdapter
from false_comm.git.snapshot import SnapshotManager
from false_comm.i18n import set_locale

runner = CliRunner()


@pytest.fixture(autouse=True)
def _english_locale() -> None:
    set_locale("en")


def _repository_state(repo: Path) -> tuple[str, tuple[str, ...], tuple[str, ...], str]:
    """Observable repository state that replay must not change in dry-run mode."""
    adapter = GitAdapter(repo)
    branches = tuple(sorted(adapter.list_branches()))
    snapshots = tuple(s.snapshot_id for s in SnapshotManager(adapter).list_snapshots())
    status = adapter.run_git(["status", "--porcelain"]).stdout
    return adapter.get_head_sha(), branches, snapshots, status


def test_replay_dry_run_previews_without_mutating(
    git_adapter: GitAdapter, temp_git_repo: Path, monolithic_commit: str
) -> None:
    before = _repository_state(temp_git_repo)

    result = runner.invoke(
        app,
        [
            "replay",
            monolithic_commit,
            "--span",
            "3d",
            "--dry-run",
            "--repo",
            str(temp_git_repo),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Semantic Partitioning Preview" in result.output
    assert "Dry-run mode: no commits, branches, or snapshots were created." in result.output
    assert _repository_state(temp_git_repo) == before


def test_replay_dry_run_json_emits_parseable_plan(
    git_adapter: GitAdapter, temp_git_repo: Path, monolithic_commit: str
) -> None:
    before = _repository_state(temp_git_repo)

    result = runner.invoke(
        app,
        [
            "replay",
            monolithic_commit,
            "--span",
            "3d",
            "--dry-run",
            "--json",
            "--repo",
            str(temp_git_repo),
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)

    assert payload["commit"] == monolithic_commit
    assert payload["original_message"].startswith("feat: massive monolithic")
    assert payload["span_days"] == 3
    assert payload["total_files"] == 4
    assert payload["total_steps"] == 4
    assert [step["phase"] for step in payload["steps"]] == [
        "interface_schema",
        "core_logic",
        "tests",
        "docs_polish",
    ]
    assert payload["steps"][0]["files"] == ["models/user.py"]
    assert [step["step_index"] for step in payload["steps"]] == [1, 2, 3, 4]
    assert _repository_state(temp_git_repo) == before


def test_replay_json_flag_alone_implies_dry_run(
    git_adapter: GitAdapter, temp_git_repo: Path, monolithic_commit: str
) -> None:
    before = _repository_state(temp_git_repo)

    result = runner.invoke(
        app,
        ["replay", monolithic_commit, "--json", "--repo", str(temp_git_repo)],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["total_steps"] == 4
    assert payload["span_days"] == 7
    assert _repository_state(temp_git_repo) == before


def test_replay_dry_run_with_yes_still_does_not_mutate(
    git_adapter: GitAdapter, temp_git_repo: Path, monolithic_commit: str
) -> None:
    before = _repository_state(temp_git_repo)

    result = runner.invoke(
        app,
        [
            "replay",
            monolithic_commit,
            "--dry-run",
            "--yes",
            "--repo",
            str(temp_git_repo),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Dry-run mode:" in result.output
    assert _repository_state(temp_git_repo) == before


def test_replay_dry_run_rejects_invalid_commit_without_mutating(
    git_adapter: GitAdapter, temp_git_repo: Path
) -> None:
    before = _repository_state(temp_git_repo)

    result = runner.invoke(
        app,
        [
            "replay",
            "deadbeefdeadbeef",
            "--dry-run",
            "--repo",
            str(temp_git_repo),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Failed to inspect commit 'deadbeefdeadbeef'" in result.output
    assert _repository_state(temp_git_repo) == before


def test_replay_dry_run_outside_git_repo(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["replay", "HEAD", "--dry-run", "--repo", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert "is not a valid Git repository" in result.output
