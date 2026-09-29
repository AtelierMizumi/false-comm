"""Unit tests for SnapshotManager and rollback safety."""

from pathlib import Path

from false_comm.git.adapter import GitAdapter
from false_comm.git.snapshot import SnapshotManager


def test_snapshot_creation_and_rollback(
    git_adapter: GitAdapter, snapshot_manager: SnapshotManager, temp_git_repo: Path
) -> None:
    initial_sha = git_adapter.get_head_sha()

    # Create safety snapshot
    snapshot = snapshot_manager.create_snapshot("Test snapshot")
    assert snapshot.head_sha == initial_sha

    # Add a commit
    dummy = temp_git_repo / "dummy.txt"
    dummy.write_text("temporary content\n")
    git_adapter.add_files(["dummy.txt"])
    new_sha = git_adapter.commit(
        message="temporary commit",
        author_date="2024-01-01T12:00:00 +0000",
        committer_date="2024-01-01T12:00:00 +0000",
        author_name="Tester",
        author_email="tester@example.com",
    )
    assert new_sha != initial_sha
    assert git_adapter.get_head_sha() == new_sha

    # Rollback to snapshot
    restored = snapshot_manager.rollback(snapshot.snapshot_id)
    assert restored.head_sha == initial_sha
    assert git_adapter.get_head_sha() == initial_sha
    assert not dummy.exists()
