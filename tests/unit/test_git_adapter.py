"""Unit tests for GitAdapter."""

from pathlib import Path

from false_comm.git.adapter import GitAdapter


def test_git_adapter_repo_detection(git_adapter: GitAdapter) -> None:
    assert git_adapter.is_git_repo()
    assert git_adapter.get_current_branch() == "main"
    assert len(git_adapter.get_head_sha()) == 40
    assert not git_adapter.has_uncommitted_changes()


def test_git_adapter_identity(git_adapter: GitAdapter) -> None:
    ident = git_adapter.get_git_identity()
    assert ident.name == "Test Committer"
    assert ident.email == "test@example.com"
    assert ident.timezone.startswith(("+", "-"))


def test_git_adapter_commit_with_custom_dates(git_adapter: GitAdapter, temp_git_repo: Path) -> None:
    test_file = temp_git_repo / "test.txt"
    test_file.write_text("Hello world\n")
    git_adapter.add_files(["test.txt"])

    sha = git_adapter.commit(
        message="feat(core): initial test file",
        author_date="2023-01-15T10:30:00 +0700",
        committer_date="2023-01-15T10:30:00 +0700",
        author_name="Custom Author",
        author_email="custom@example.com",
    )
    assert len(sha) == 40

    # Verify log output for author date and name
    log_res = git_adapter.run_git(["log", "-1", "--format=%an|%ae|%ad", "--date=iso"])
    assert "Custom Author|custom@example.com|2023-01-15 10:30:00 +0700" in log_res.stdout
