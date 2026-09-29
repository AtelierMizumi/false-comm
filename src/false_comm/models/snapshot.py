"""Snapshot models for atomic rollback and safety guarantees."""

from datetime import datetime

from pydantic import BaseModel, Field


class SnapshotMetadata(BaseModel):
    """Metadata recorded prior to any git history modification."""

    snapshot_id: str
    created_at: datetime
    repo_path: str
    branch_name: str
    head_sha: str
    previous_reflog_head: str = ""
    had_unstaged_changes: bool = False
    stash_sha: str | None = None
    commits_applied_count: int = 0
    applied_commit_shas: list[str] = Field(default_factory=list)
    description: str = "Pre-run safety snapshot"
    active_branches_created: list[str] = Field(default_factory=list)
