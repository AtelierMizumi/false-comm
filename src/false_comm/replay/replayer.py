"""Replayer engine recreating large monolithic commits as progressive atomic histories."""

from datetime import date, datetime, timedelta
from typing import NamedTuple

from false_comm.core.behavior import BehaviorEngine, DayCommitSpec
from false_comm.core.holidays import HolidayCalendar
from false_comm.core.profile import ProfileRegistry
from false_comm.core.scheduler import ScheduleEngine
from false_comm.git.adapter import GitAdapter
from false_comm.git.snapshot import SnapshotManager
from false_comm.models.config import BehaviorProfile, DateRange, GitIdentity
from false_comm.replay.analyzer import ReplayAnalyzer
from false_comm.replay.repartitioner import DiffRepartitioner, ReplayStep


class ReplayResult(NamedTuple):
    original_sha: str
    snapshot_id: str
    total_steps: int
    new_head_sha: str
    steps_applied: list[ReplayStep]


class CommitReplayer:
    """Replays a monolithic commit across a realistic multi-day timeline."""

    def __init__(
        self,
        git_adapter: GitAdapter,
        snapshot_manager: SnapshotManager,
        profile: BehaviorProfile | None = None,
        identity: GitIdentity | None = None,
    ) -> None:
        self.git = git_adapter
        self.snapshots = snapshot_manager
        self.profile = profile or ProfileRegistry.load_profile("standard")
        self.identity = identity or self.git.get_git_identity()

    def plan_replay_schedule(self, steps: list[ReplayStep], span_days: int) -> list[datetime]:
        """Distribute steps chronologically across span_days."""
        if not steps:
            return []

        end_date = date.today()
        start_date = end_date - timedelta(days=max(1, span_days - 1))
        date_range = DateRange(start_date=start_date, end_date=end_date)

        holidays = HolidayCalendar(region=self.profile.holiday_region)
        behavior = BehaviorEngine(profile=self.profile, holiday_calendar=holidays)
        scheduler = ScheduleEngine(profile=self.profile, timezone_str=self.identity.timezone)

        # Distribute steps into active days
        total_steps = len(steps)
        days_specs = behavior.plan_daily_commits(date_range)
        active_days = [d.target_date for d in days_specs if d.commit_count > 0]
        if not active_days:
            # Fallback to working weekdays
            active_days = [
                start_date + timedelta(days=i)
                for i in range(span_days)
                if (start_date + timedelta(days=i)).weekday() < 5
            ]
            if not active_days:
                active_days = [end_date]

        # Allocate steps evenly among active days
        assigned_datetimes: list[datetime] = []
        step_idx = 0
        steps_per_day = max(1, total_steps // len(active_days) + 1)

        for d in active_days:
            if step_idx >= total_steps:
                break
            remaining = total_steps - step_idx
            daily_count = min(remaining, steps_per_day)
            spec = DayCommitSpec(
                target_date=d, commit_count=daily_count, is_burst_day=False, burst_groups=[]
            )
            timestamps = scheduler.schedule_day(spec)
            for ts in timestamps[:daily_count]:
                assigned_datetimes.append(ts)
                step_idx += 1

        # Pad any remaining steps on end_date
        while len(assigned_datetimes) < total_steps:
            last_ts = assigned_datetimes[-1] if assigned_datetimes else datetime.now()
            assigned_datetimes.append(last_ts + timedelta(minutes=15))

        assigned_datetimes.sort()
        return assigned_datetimes[:total_steps]

    def execute_replay(
        self,
        commit_ref: str,
        span_days: int = 7,
    ) -> ReplayResult:
        """Partition commit_ref and replay its file changes progressively."""
        analyzer = ReplayAnalyzer(self.git)
        analysis = analyzer.analyze_commit(commit_ref)

        if analysis.total_files == 0:
            raise ValueError(f"Commit '{commit_ref}' has 0 modified files to replay.")

        repartitioner = DiffRepartitioner()
        steps = repartitioner.partition(analysis)

        if not steps:
            raise ValueError(f"No progressive steps could be extracted from commit '{commit_ref}'.")

        # Capture parent of the commit to replay from
        parent_res = self.git.run_git(["rev-parse", f"{commit_ref}^"], check=False)
        has_parent = parent_res.returncode == 0
        parent_sha = parent_res.stdout.strip() if has_parent else None

        # Take safety snapshot
        snapshot = self.snapshots.create_snapshot(description=f"Pre-replay of {commit_ref}")

        # Compute timestamps
        timestamps = self.plan_replay_schedule(steps, span_days=span_days)

        active_branch = self.git.get_current_branch()
        replay_branch = f"replay-{commit_ref[:7]}"

        applied_shas: list[str] = []

        try:
            # Create and switch to replay branch starting at parent commit (or orphan if initial)
            if parent_sha:
                self.git.create_branch(replay_branch, start_point=parent_sha)
                self.git.checkout(replay_branch)
            else:
                self.git.create_branch(replay_branch)
                self.git.checkout(replay_branch)

            # Apply each step
            for step, ts in zip(steps, timestamps, strict=False):
                # Checkout files from original commit
                self.git.run_git(["checkout", commit_ref, "--", *step.files])
                self.git.add_files(step.files)

                # Format date
                dt_str = ts.strftime("%Y-%m-%dT%H:%M:%S")
                date_fmt = f"{dt_str} {self.identity.timezone}"

                sha = self.git.commit(
                    message=step.message,
                    author_date=date_fmt,
                    committer_date=date_fmt,
                    author_name=self.identity.name,
                    author_email=self.identity.email,
                )
                applied_shas.append(sha)

            # Reset original branch to replay branch
            self.git.checkout(active_branch)
            self.git.reset_hard(applied_shas[-1])
            # Delete temporary replay branch
            self.git.delete_branch(replay_branch, force=True)

            self.snapshots.update_snapshot_results(
                snapshot_id=snapshot.snapshot_id,
                applied_shas=applied_shas,
                branches_created=[],
            )

            return ReplayResult(
                original_sha=commit_ref,
                snapshot_id=snapshot.snapshot_id,
                total_steps=len(applied_shas),
                new_head_sha=applied_shas[-1],
                steps_applied=steps,
            )

        except Exception as e:
            # Restore original branch if failure occurs
            self.git.checkout(active_branch)
            raise RuntimeError(
                f"Replay failed: {e}\nRestore with: fc undo --snapshot {snapshot.snapshot_id}"
            ) from e
