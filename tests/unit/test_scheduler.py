"""Unit tests for ScheduleEngine."""

from datetime import date

from false_comm.core.behavior import DayCommitSpec
from false_comm.core.profile import ProfileRegistry
from false_comm.core.scheduler import ScheduleEngine


def test_scheduler_chronological_ordering() -> None:
    prof = ProfileRegistry.load_profile("standard")
    scheduler = ScheduleEngine(profile=prof, timezone_str="+0700", seed=42)

    spec = DayCommitSpec(
        target_date=date(2024, 3, 15),
        commit_count=6,
        is_burst_day=True,
        burst_groups=[[1, 2, 3]],
    )
    timestamps = scheduler.schedule_day(spec)

    assert len(timestamps) == 6
    for i in range(len(timestamps) - 1):
        assert timestamps[i] < timestamps[i + 1]
        # At least 90s gap
        gap = (timestamps[i + 1] - timestamps[i]).total_seconds()
        assert gap >= 90


def test_scheduler_non_round_timestamps() -> None:
    prof = ProfileRegistry.load_profile("standard")
    scheduler = ScheduleEngine(profile=prof, timezone_str="+0700", seed=99)

    spec = DayCommitSpec(
        target_date=date(2024, 3, 15),
        commit_count=10,
        is_burst_day=False,
        burst_groups=[],
    )
    timestamps = scheduler.schedule_day(spec)

    # Not all commits should fall on exact 00 seconds
    zero_seconds = sum(1 for ts in timestamps if ts.second == 0)
    assert zero_seconds < len(timestamps) / 2
