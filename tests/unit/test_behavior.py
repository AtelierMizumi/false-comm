"""Unit tests for BehaviorEngine and statistical synthesis."""

from datetime import date

from false_comm.core.behavior import BehaviorEngine
from false_comm.core.holidays import HolidayCalendar
from false_comm.core.profile import ProfileRegistry
from false_comm.models.config import DateRange


def test_behavior_engine_determinism_with_seed() -> None:
    prof = ProfileRegistry.load_profile("standard")
    cal = HolidayCalendar("GLOBAL")
    dr = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 1, 31))

    engine1 = BehaviorEngine(profile=prof, holiday_calendar=cal, seed=12345)
    plan1 = engine1.plan_daily_commits(dr)

    engine2 = BehaviorEngine(profile=prof, holiday_calendar=cal, seed=12345)
    plan2 = engine2.plan_daily_commits(dr)

    assert len(plan1) == len(plan2) == 31
    for d1, d2 in zip(plan1, plan2, strict=True):
        assert d1.target_date == d2.target_date
        assert d1.commit_count == d2.commit_count
        assert d1.is_burst_day == d2.is_burst_day
        assert d1.burst_groups == d2.burst_groups


def test_weekend_dampening_in_standard_profile() -> None:
    prof = ProfileRegistry.load_profile("standard")
    cal = HolidayCalendar("GLOBAL")
    dr = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 6, 30))

    engine = BehaviorEngine(profile=prof, holiday_calendar=cal, seed=42)
    daily = engine.plan_daily_commits(dr)

    weekday_commits = 0
    weekday_days = 0
    weekend_commits = 0
    weekend_days = 0

    for d in daily:
        if d.target_date.weekday() >= 5:
            weekend_commits += d.commit_count
            weekend_days += 1
        else:
            weekday_commits += d.commit_count
            weekday_days += 1

    mean_weekday = weekday_commits / weekday_days
    mean_weekend = weekend_commits / weekend_days

    # Standard profile should have dramatically higher weekday commits than weekends
    assert mean_weekday > mean_weekend * 3.0
