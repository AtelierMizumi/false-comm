"""Integration test for Replay Mode deconstructing monolithic commits."""

from pathlib import Path

from false_comm.git.adapter import GitAdapter
from false_comm.git.snapshot import SnapshotManager
from false_comm.replay.replayer import CommitReplayer


def test_monolithic_commit_replay(
    git_adapter: GitAdapter, snapshot_manager: SnapshotManager, temp_git_repo: Path
) -> None:
    initial_sha = git_adapter.get_head_sha()

    # Create a monolithic commit with multiple files across different phases
    models_file = temp_git_repo / "models" / "user.py"
    models_file.parent.mkdir(parents=True, exist_ok=True)
    models_file.write_text("class User:\n    id: int\n    name: str\n", encoding="utf-8")

    core_file = temp_git_repo / "core" / "auth.py"
    core_file.parent.mkdir(parents=True, exist_ok=True)
    core_file.write_text("def authenticate():\n    return True\n", encoding="utf-8")

    test_file = temp_git_repo / "tests" / "test_auth.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("def test_auth():\n    assert True\n", encoding="utf-8")

    docs_file = temp_git_repo / "docs" / "api.md"
    docs_file.parent.mkdir(parents=True, exist_ok=True)
    docs_file.write_text("# Auth API\nDetails\n", encoding="utf-8")

    git_adapter.add_files(["models/user.py", "core/auth.py", "tests/test_auth.py", "docs/api.md"])
    monolithic_sha = git_adapter.commit(
        message="feat: massive monolithic Sunday 3am commit",
        author_date="2024-03-10T03:15:00 +0700",
        committer_date="2024-03-10T03:15:00 +0700",
        author_name="Dev",
        author_email="dev@example.com",
    )

    # Now deconstruct and replay across 4 days
    replayer = CommitReplayer(git_adapter=git_adapter, snapshot_manager=snapshot_manager)
    res = replayer.execute_replay(commit_ref=monolithic_sha, span_days=4)

    assert res.total_steps >= 3  # At least 3 separate progressive steps
    assert res.new_head_sha != monolithic_sha

    # Verify git log now has multiple separate commits
    log_res = git_adapter.run_git(["log", "--oneline", f"{initial_sha}..HEAD"])
    commit_lines = [
        commit_line for commit_line in log_res.stdout.splitlines() if commit_line.strip()
    ]
    assert len(commit_lines) == res.total_steps

    # Verify working tree has all files intact
    assert models_file.is_file()
    assert core_file.is_file()
    assert test_file.is_file()
    assert docs_file.is_file()
