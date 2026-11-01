"""Test fixtures and temporary Git repository setups."""

import subprocess
from datetime import date
from pathlib import Path

import pytest

from false_comm.core.profile import ProfileRegistry
from false_comm.git.adapter import GitAdapter
from false_comm.git.snapshot import SnapshotManager
from false_comm.models.config import BehaviorProfile, DateRange, GitIdentity


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary initialized Git repository with initial commit and identity."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Initialize git
    subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test Committer"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo_dir, check=True)

    # Create initial file & commit
    readme = repo_dir / "README.md"
    readme.write_text("# Test Repo\nInitial commit.\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_dir, check=True)

    return repo_dir


@pytest.fixture
def git_adapter(temp_git_repo: Path) -> GitAdapter:
    return GitAdapter(temp_git_repo)


@pytest.fixture
def monolithic_commit(git_adapter: GitAdapter, temp_git_repo: Path) -> str:
    """Create a single commit spanning all replay semantic phases."""
    files = {
        "models/user.py": "class User:\n    id: int\n    name: str\n",
        "core/auth.py": "def authenticate():\n    return True\n",
        "tests/test_auth.py": "def test_auth():\n    assert True\n",
        "docs/api.md": "# Auth API\nDetails\n",
    }
    for relative_path, content in files.items():
        target = temp_git_repo / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    git_adapter.add_files(list(files))
    return git_adapter.commit(
        message="feat: massive monolithic Sunday 3am commit",
        author_date="2024-03-10T03:15:00 +0700",
        committer_date="2024-03-10T03:15:00 +0700",
        author_name="Dev",
        author_email="dev@example.com",
    )


@pytest.fixture
def snapshot_manager(git_adapter: GitAdapter) -> SnapshotManager:
    return SnapshotManager(git_adapter)


@pytest.fixture
def standard_profile() -> BehaviorProfile:
    return ProfileRegistry.load_profile("standard")


@pytest.fixture
def test_identity() -> GitIdentity:
    return GitIdentity(
        name="Test Committer",
        email="test@example.com",
        timezone="+0700",
    )


@pytest.fixture
def sample_date_range() -> DateRange:
    return DateRange(start_date=date(2024, 3, 1), end_date=date(2024, 3, 31))
