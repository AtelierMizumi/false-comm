"""Executes a CommitPlan safely with atomic snapshots and progress reporting."""

from collections.abc import Callable
from typing import NamedTuple

from false_comm.git.adapter import GitAdapter
from false_comm.git.snapshot import SnapshotManager
from false_comm.models.commit import CommitPlan, PlannedCommit


class ExecutionResult(NamedTuple):
    """Summary of executed plan."""

    plan_id: str
    snapshot_id: str
    commits_applied: int
    commit_shas: list[str]
    branches_created: list[str]
    target_branch: str


class PlanExecutor:
    """Safely executes a CommitPlan on a target Git repository."""

    def __init__(self, git_adapter: GitAdapter, snapshot_manager: SnapshotManager) -> None:
        self.git = git_adapter
        self.snapshots = snapshot_manager
        self.repo_root = self.git.get_repo_root()

    def execute(
        self,
        plan: CommitPlan,
        progress_callback: Callable[[int, int, PlannedCommit], None] | None = None,
    ) -> ExecutionResult:
        """Execute all commits in the plan, applying snapshots and safety checkpoints."""
        if not self.git.is_git_repo():
            raise ValueError(f"Path '{self.repo_root}' is not a valid Git repository.")

        # Ensure we are on target branch
        orig_branch = self.git.get_current_branch()
        if orig_branch != plan.branch:
            self.git.checkout(plan.branch)

        # 1. Take safety snapshot
        snapshot = self.snapshots.create_snapshot(
            description=f"Pre-execution of plan {plan.plan_id}"
        )

        applied_shas: list[str] = []
        created_branches: set[str] = set()
        active_branch = plan.branch

        try:
            total = len(plan.commits)
            for idx, commit in enumerate(plan.commits, start=1):
                if progress_callback:
                    progress_callback(idx, total, commit)

                # Handle branch switching
                if commit.branch != active_branch:
                    if commit.branch not in self.git.list_branches():
                        self.git.create_branch(commit.branch)
                        created_branches.add(commit.branch)
                    self.git.checkout(commit.branch)
                    active_branch = commit.branch

                # Handle merge commits
                if commit.is_merge and commit.merge_parent_branch:
                    # Checkout destination branch
                    if active_branch != commit.branch:
                        self.git.checkout(commit.branch)
                        active_branch = commit.branch

                    sha = self.git.merge(
                        branch_to_merge=commit.merge_parent_branch,
                        message=commit.message,
                        date_str=commit.formatted_git_date,
                        author_name=commit.author_name,
                        author_email=commit.author_email,
                    )
                    applied_shas.append(sha)
                    continue

                # Apply file changes
                paths_to_stage: list[str] = []
                for change in commit.changes:
                    target_file = self.repo_root / change.relative_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    if change.content is not None:
                        target_file.write_text(change.content, encoding="utf-8")
                        if change.relative_path.endswith(".sh"):
                            from false_comm.utils.platform import set_executable_permission

                            set_executable_permission(target_file)
                        paths_to_stage.append(change.relative_path)

                if paths_to_stage:
                    self.git.add_files(paths_to_stage)

                # Commit (allow_empty=True if no files modified to prevent abort)
                sha = self.git.commit(
                    message=commit.message,
                    author_date=commit.formatted_git_date,
                    committer_date=commit.formatted_git_date,
                    author_name=commit.author_name,
                    author_email=commit.author_email,
                    committer_name=commit.committer_name,
                    committer_email=commit.committer_email,
                    allow_empty=not bool(paths_to_stage),
                )
                applied_shas.append(sha)

            # Ensure we finish on the target branch
            if active_branch != plan.branch:
                self.git.checkout(plan.branch)

            # Update snapshot record
            self.snapshots.update_snapshot_results(
                snapshot_id=snapshot.snapshot_id,
                applied_shas=applied_shas,
                branches_created=list(created_branches),
            )

            return ExecutionResult(
                plan_id=plan.plan_id,
                snapshot_id=snapshot.snapshot_id,
                commits_applied=len(applied_shas),
                commit_shas=applied_shas,
                branches_created=list(created_branches),
                target_branch=plan.branch,
            )

        except Exception as e:
            # If failed midway, notify user with snapshot ID
            raise RuntimeError(
                f"Execution failed on commit {len(applied_shas) + 1}/{len(plan.commits)}: {e}\n"
                f"You can restore the repository with:\n"
                f"  fc undo --snapshot {snapshot.snapshot_id}"
            ) from e
