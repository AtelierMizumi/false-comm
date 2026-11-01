"""Integration tests for CLI commands that mutate repository history.

These cover the real execution paths of `backfill`, `replay`, and `undo`
(not just dry-run/list), including the safety-snapshot contract.
"""

import subprocess
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
    """Keep CLI assertions independent from locale state left by other tests."""
    set_locale("en")


def _commit_count(repo: Path) -> int:
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return int(result.stdout.strip())


def _snapshots(repo: Path) -> list:
    return SnapshotManager(GitAdapter(repo)).list_snapshots()


def _backfill_args(repo: Path) -> list[str]:
    return [
        "backfill",
        "--from",
        "2024-01-01",
        "--to",
        "2024-01-07",
        "--profile",
        "standard",
        "--seed",
        "42",
        "--repo",
        str(repo),
    ]


def test_backfill_cli_applies_commits_and_records_snapshot(temp_git_repo: Path) -> None:
    adapter = GitAdapter(temp_git_repo)
    initial_head = adapter.get_head_sha()
    initial_count = _commit_count(temp_git_repo)

    result = runner.invoke(app, [*_backfill_args(temp_git_repo), "--yes"])

    assert result.exit_code == 0, result.output
    assert "Synthesis completed successfully!" in result.output

    snapshots = _snapshots(temp_git_repo)
    assert len(snapshots) == 1
    snapshot = snapshots[0]

    assert snapshot.head_sha == initial_head
    assert snapshot.commits_applied_count > 0
    assert snapshot.snapshot_id in result.output

    applied = snapshot.commits_applied_count
    assert _commit_count(temp_git_repo) == initial_count + applied
    assert adapter.get_head_sha() != initial_head


def test_undo_cli_restores_exact_pre_backfill_head(temp_git_repo: Path) -> None:
    adapter = GitAdapter(temp_git_repo)
    initial_head = adapter.get_head_sha()
    initial_count = _commit_count(temp_git_repo)

    backfill_result = runner.invoke(app, [*_backfill_args(temp_git_repo), "--yes"])
    assert backfill_result.exit_code == 0, backfill_result.output

    snapshot_id = _snapshots(temp_git_repo)[0].snapshot_id

    undo_result = runner.invoke(
        app,
        ["undo", "--snapshot", snapshot_id, "--yes", "--repo", str(temp_git_repo)],
    )

    assert undo_result.exit_code == 0, undo_result.output
    assert "Successfully restored repository state!" in undo_result.output
    assert adapter.get_head_sha() == initial_head
    assert _commit_count(temp_git_repo) == initial_count
    # The consumed snapshot must no longer be offered for rollback.
    assert _snapshots(temp_git_repo) == []


def test_backfill_cli_declined_confirmation_leaves_repo_untouched(temp_git_repo: Path) -> None:
    adapter = GitAdapter(temp_git_repo)
    initial_head = adapter.get_head_sha()
    initial_count = _commit_count(temp_git_repo)

    result = runner.invoke(app, _backfill_args(temp_git_repo), input="n\n")

    assert result.exit_code == 0, result.output
    assert "Operation aborted by user." in result.output
    assert adapter.get_head_sha() == initial_head
    assert _commit_count(temp_git_repo) == initial_count
    assert _snapshots(temp_git_repo) == []


def test_replay_cli_decomposes_monolithic_commit(
    temp_git_repo: Path, monolithic_commit: str
) -> None:
    adapter = GitAdapter(temp_git_repo)
    monolithic_sha = monolithic_commit
    assert adapter.get_head_sha() == monolithic_sha  # fixture commit is currently HEAD

    result = runner.invoke(
        app,
        ["replay", monolithic_sha, "--span", "3d", "--yes", "--repo", str(temp_git_repo)],
    )

    assert result.exit_code == 0, result.output
    assert "Replay completed successfully!" in result.output

    new_head = adapter.get_head_sha()
    assert new_head != monolithic_sha

    log = adapter.run_git(["log", "--oneline", f"{monolithic_sha}..HEAD"])
    replayed_commits = [line for line in log.stdout.splitlines() if line.strip()]
    assert len(replayed_commits) == 4

    for relative_path in (
        "models/user.py",
        "core/auth.py",
        "tests/test_auth.py",
        "docs/api.md",
    ):
        assert (temp_git_repo / relative_path).is_file()

    snapshots = _snapshots(temp_git_repo)
    assert len(snapshots) == 1
    # The checkpoint must capture the state *before* replay (the monolithic commit).
    assert snapshots[0].head_sha == monolithic_sha
    assert snapshots[0].commits_applied_count == 4

    undo_result = runner.invoke(
        app,
        [
            "undo",
            "--snapshot",
            snapshots[0].snapshot_id,
            "--yes",
            "--repo",
            str(temp_git_repo),
        ],
    )
    assert undo_result.exit_code == 0, undo_result.output
    assert "Successfully restored repository state!" in undo_result.output
    assert adapter.get_head_sha() == monolithic_sha
    assert _snapshots(temp_git_repo) == []


def test_undo_list_shows_recorded_snapshot(temp_git_repo: Path) -> None:
    adapter = GitAdapter(temp_git_repo)
    initial_head = adapter.get_head_sha()

    backfill_result = runner.invoke(app, [*_backfill_args(temp_git_repo), "--yes"])
    assert backfill_result.exit_code == 0, backfill_result.output

    result = runner.invoke(app, ["undo", "--list", "--repo", str(temp_git_repo)])

    assert result.exit_code == 0, result.output
    assert "Available Safety Snapshots" in result.output
    # Rich truncates narrow columns, so assert the stable visible fragments.
    assert "snap_" in result.output
    assert "Pre-executi" in result.output
    assert initial_head[:8] in result.output
    assert str(_snapshots(temp_git_repo)[0].commits_applied_count) in result.output


def test_undo_unknown_snapshot_reports_failure_without_moving_head(
    temp_git_repo: Path,
) -> None:
    adapter = GitAdapter(temp_git_repo)
    initial_head = adapter.get_head_sha()

    result = runner.invoke(
        app,
        [
            "undo",
            "--snapshot",
            "snap_does_not_exist",
            "--yes",
            "--repo",
            str(temp_git_repo),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Rollback failed" in result.output
    assert "snap_does_not_exist" in result.output
    assert adapter.get_head_sha() == initial_head


def test_backfill_cli_rejects_non_git_directory(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "backfill",
            "--from",
            "2024-01-01",
            "--to",
            "2024-01-07",
            "--yes",
            "--repo",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "is not a valid Git repository" in result.output


def test_backfill_cli_rejects_invalid_date(temp_git_repo: Path) -> None:
    result = runner.invoke(
        app,
        [
            "backfill",
            "--from",
            "not-a-date",
            "--to",
            "also-bad",
            "--yes",
            "--repo",
            str(temp_git_repo),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Invalid date format" in result.output


def test_backfill_cli_rejects_unknown_profile(temp_git_repo: Path) -> None:
    result = runner.invoke(
        app,
        [
            "backfill",
            "--from",
            "2024-01-01",
            "--to",
            "2024-01-07",
            "--profile",
            "does-not-exist",
            "--yes",
            "--repo",
            str(temp_git_repo),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Profile 'does-not-exist' not found" in result.output


def test_replay_cli_declined_confirmation_leaves_repo_untouched(
    temp_git_repo: Path, monolithic_commit: str
) -> None:
    adapter = GitAdapter(temp_git_repo)
    monolithic_sha = monolithic_commit

    result = runner.invoke(
        app,
        ["replay", monolithic_sha, "--span", "3d", "--repo", str(temp_git_repo)],
        input="n\n",
    )

    assert result.exit_code == 0, result.output
    assert "Replay cancelled by user." in result.output
    assert adapter.get_head_sha() == monolithic_sha
    assert _commit_count(temp_git_repo) == 2  # Initial commit + monolithic commit
    assert _snapshots(temp_git_repo) == []
