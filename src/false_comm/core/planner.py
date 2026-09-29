"""Commit planning coordinator assembling behavior, schedule, and content into an executable plan."""

import uuid
from datetime import datetime
from pathlib import Path

from false_comm.content.generic import GenericContentStrategy
from false_comm.content.messages import MessageGenerator
from false_comm.content.repo_analyzer import RepoAnalyzer, RepoCharacteristics
from false_comm.core.behavior import BehaviorEngine
from false_comm.core.holidays import HolidayCalendar
from false_comm.core.scheduler import ScheduleEngine
from false_comm.git.branch_sim import BranchSimEngine
from false_comm.models.commit import (
    BranchPlan,
    CommitPlan,
    PlannedCommit,
)
from false_comm.models.config import (
    BehaviorProfile,
    DateRange,
    GitIdentity,
    RepositoryRules,
)


class CommitPlanner:
    """Orchestrates all synthesis engines to generate a complete CommitPlan."""

    def __init__(
        self,
        repo_root: Path,
        profile: BehaviorProfile,
        identity: GitIdentity,
        rules: RepositoryRules | None = None,
        characteristics: RepoCharacteristics | None = None,
        seed: int | None = None,
    ) -> None:
        self.repo_root = repo_root
        self.profile = profile
        self.identity = identity
        self.rules = rules or RepositoryRules(target_branch="main")
        self.characteristics = characteristics or RepoAnalyzer(repo_root).analyze()
        self.seed = seed

        self.holidays = HolidayCalendar(region=profile.holiday_region)
        self.behavior = BehaviorEngine(profile=profile, holiday_calendar=self.holidays, seed=seed)
        self.scheduler = ScheduleEngine(profile=profile, timezone_str=identity.timezone, seed=seed)
        self.messages = MessageGenerator(
            style=profile.message_style,
            scopes=self.characteristics.detected_scopes,
            seed=seed,
        )
        self.content_strategy = GenericContentStrategy(
            repo_root=repo_root,
            characteristics=self.characteristics,
            seed=seed,
        )
        self.branch_sim = BranchSimEngine(target_branch=self.rules.target_branch, seed=seed)

    def generate_plan(self, date_range: DateRange) -> CommitPlan:
        """Create a complete chronological schedule of planned commits."""
        daily_specs = self.behavior.plan_daily_commits(date_range)
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        planned_commits: list[PlannedCommit] = []
        branch_plans: list[BranchPlan] = []
        commit_seq = 0

        for day_spec in daily_specs:
            if day_spec.commit_count <= 0:
                continue

            timestamps = self.scheduler.schedule_day(day_spec)

            # Check if this day should start a feature branch simulation
            simulate_branch = (
                self.profile.branch_simulation_enabled
                and len(timestamps) >= 3
                and self.behavior.rng.random() < self.profile.branch_ratio
            )

            branch_name = (
                self.branch_sim.generate_branch_name()
                if simulate_branch
                else self.rules.target_branch
            )
            active_branch_commit_ids: list[str] = []

            for i, ts in enumerate(timestamps):
                commit_seq += 1
                c_id = f"commit_{commit_seq:04d}"
                is_last_in_sim = simulate_branch and (i == len(timestamps) - 1)

                if is_last_in_sim and self.profile.merge_commit_enabled:
                    # Final commit in this group will be a merge commit back to target_branch
                    merge_msg = self.branch_sim.generate_merge_message(
                        branch_name, self.rules.target_branch
                    )
                    commit = PlannedCommit(
                        id=c_id,
                        timestamp=ts,
                        timezone_str=self.identity.timezone,
                        author_name=self.identity.name,
                        author_email=self.identity.email,
                        committer_name=self.identity.name,
                        committer_email=self.identity.email,
                        message=merge_msg,
                        branch=self.rules.target_branch,
                        is_merge=True,
                        merge_parent_branch=branch_name,
                        changes=[],
                    )
                    planned_commits.append(commit)

                    if active_branch_commit_ids:
                        b_plan = BranchPlan(
                            branch_name=branch_name,
                            base_branch=self.rules.target_branch,
                            start_commit_id=active_branch_commit_ids[0],
                            commit_ids=active_branch_commit_ids,
                            merge_commit_id=c_id,
                        )
                        branch_plans.append(b_plan)
                else:
                    # Regular commit
                    target_b = branch_name if simulate_branch else self.rules.target_branch
                    msg = self.messages.generate(allow_multiline=True)
                    # Extract scope or default
                    scope = "core"
                    if "(" in msg and ")" in msg:
                        scope = msg.split("(")[1].split(")")[0]

                    changes = self.content_strategy.generate_changes("feat", scope, commit_seq)

                    commit = PlannedCommit(
                        id=c_id,
                        timestamp=ts,
                        timezone_str=self.identity.timezone,
                        author_name=self.identity.name,
                        author_email=self.identity.email,
                        committer_name=self.identity.name,
                        committer_email=self.identity.email,
                        message=msg,
                        branch=target_b,
                        is_merge=False,
                        changes=changes,
                    )
                    planned_commits.append(commit)
                    if simulate_branch:
                        active_branch_commit_ids.append(c_id)

        return CommitPlan(
            plan_id=plan_id,
            created_at=datetime.now(),
            repo_path=str(self.repo_root),
            branch=self.rules.target_branch,
            profile_name=self.profile.name,
            start_date=str(date_range.start_date),
            end_date=str(date_range.end_date),
            commits=planned_commits,
            branches=branch_plans,
        )
