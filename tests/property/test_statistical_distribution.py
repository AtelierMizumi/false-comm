"""Property-based tests with Hypothesis verifying distribution invariants."""

from datetime import date, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from false_comm.core.behavior import BehaviorEngine
from false_comm.core.holidays import HolidayCalendar
from false_comm.core.profile import ProfileRegistry
from false_comm.models.config import DateRange


@given(
    start_offset=st.integers(min_value=0, max_value=300),
    duration_days=st.integers(min_value=1, max_value=60),
    seed=st.integers(min_value=1, max_value=100000),
)
@settings(max_examples=25)
def test_daily_commit_properties(start_offset: int, duration_days: int, seed: int) -> None:
    base_date = date(2024, 1, 1) + timedelta(days=start_offset)
    end_date = base_date + timedelta(days=duration_days - 1)
    dr = DateRange(start_date=base_date, end_date=end_date)

    prof = ProfileRegistry.load_profile("standard")
    holidays = HolidayCalendar("GLOBAL")
    engine = BehaviorEngine(profile=prof, holiday_calendar=holidays, seed=seed)

    specs = engine.plan_daily_commits(dr)

    # Invariants
    assert len(specs) == duration_days
    for i, s in enumerate(specs):
        assert s.target_date == base_date + timedelta(days=i)
        assert s.commit_count >= 0
        if s.is_burst_day:
            assert len(s.burst_groups) > 0
            for g in s.burst_groups:
                assert len(g) >= prof.burst_min_commits
