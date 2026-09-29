"""Integration test for full backfill generation, execution, and rollback."""

from datetime import date
from pathlib import Path

from false_comm.core.executor import PlanExecutor
from false_comm.core.planner import CommitPlanner
from false_comm.core.profile import ProfileRegistry
from false_comm.git.adapter import GitAdapter
from false_comm.git.snapshot import SnapshotManager
from false_comm.models.config import DateRange, RepositoryRules


def test_full_backfill_and_undo_flow(
    git_adapter: GitAdapter, snapshot_manager: SnapshotManager, temp_git_repo: Path
) -> None:
    initial_head = git_adapter.get_head_sha()
    prof = ProfileRegistry.load_profile("standard")
    ident = git_adapter.get_git_identity()
    rules = RepositoryRules(target_branch="main")

    planner = CommitPlanner(
        repo_root=temp_git_repo,
        profile=prof,
        identity=ident,
        rules=rules,
        seed=42,
    )
    # Plan for 1 week
    date_range = DateRange(start_date=date(2024, 3, 11), end_date=date(2024, 3, 17))
    plan = planner.generate_plan(date_range)

    assert len(plan.commits) > 0

    executor = PlanExecutor(git_adapter=git_adapter, snapshot_manager=snapshot_manager)
    result = executor.execute(plan)

    assert result.commits_applied == len(plan.commits)
    new_head = git_adapter.get_head_sha()
    assert new_head != initial_head

    # Verify commits have realistic author dates matching the plan
    first_commit = plan.commits[0]
    log_check = git_adapter.run_git(
        ["log", "--format=%ad", "--date=iso", "-n", "1", result.commit_shas[0]]
    )
    assert first_commit.timestamp.strftime("%Y-%m-%d") in log_check.stdout

    # Now verify undo / rollback restores initial_head perfectly
    restored = snapshot_manager.rollback(result.snapshot_id)
    assert restored.head_sha == initial_head
    assert git_adapter.get_head_sha() == initial_head
