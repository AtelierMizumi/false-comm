"""Models representing individual file changes, planned commits, and commit plans."""

from datetime import datetime

from pydantic import BaseModel, Field

from false_comm.models.config import CommitAction


class FileChange(BaseModel):
    """A single file modification, creation, or deletion."""

    relative_path: str
    action: CommitAction = CommitAction.MODIFY
    content: str | None = None
    original_content: str | None = None
    diff_summary: str = ""


class PlannedCommit(BaseModel):
    """An atomic commit ready to be scheduled or executed."""

    id: str = Field(description="Unique planning identifier (UUID or sequence)")
    timestamp: datetime
    timezone_str: str = "+0700"
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    message: str
    branch: str = "main"
    is_merge: bool = False
    merge_parent_branch: str | None = None
    parent_hashes: list[str] = Field(default_factory=list)
    changes: list[FileChange] = Field(default_factory=list)
    tag: str | None = None

    @property
    def formatted_git_date(self) -> str:
        """Format as ISO 8601 with timezone for GIT_AUTHOR_DATE and GIT_COMMITTER_DATE."""
        # e.g. 2024-03-15T14:27:42 +0700
        dt_str = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S")
        tz = self.timezone_str
        if not tz.startswith(("+", "-")):
            tz = f"+{tz}"
        return f"{dt_str} {tz}"


class BranchPlan(BaseModel):
    """Information about a simulated branch and its merge commit."""

    branch_name: str
    base_branch: str = "main"
    start_commit_id: str
    commit_ids: list[str] = Field(default_factory=list)
    merge_commit_id: str | None = None


class CommitPlan(BaseModel):
    """A complete chronological schedule of planned commits."""

    plan_id: str
    created_at: datetime
    repo_path: str
    branch: str = "main"
    profile_name: str
    start_date: str
    end_date: str
    commits: list[PlannedCommit] = Field(default_factory=list)
    branches: list[BranchPlan] = Field(default_factory=list)

    @property
    def total_commits(self) -> int:
        return len(self.commits)

    @property
    def merge_commits_count(self) -> int:
        return sum(1 for c in self.commits if c.is_merge)
