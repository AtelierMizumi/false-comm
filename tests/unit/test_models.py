"""Unit tests for domain models and validation rules."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from false_comm.models.commit import PlannedCommit
from false_comm.models.config import DateRange, TimeWindow


def test_date_range_validation() -> None:
    # Valid range
    dr = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 1, 31))
    assert dr.start_date <= dr.end_date

    # Same day is valid
    dr_same = DateRange(start_date=date(2024, 1, 1), end_date=date(2024, 1, 1))
    assert dr_same.start_date == dr_same.end_date

    # Inverted dates should fail
    with pytest.raises(ValidationError):
        DateRange(start_date=date(2024, 2, 1), end_date=date(2024, 1, 1))


def test_time_window_validation() -> None:
    # Valid
    w = TimeWindow(name="work", start_hour=9, end_hour=17, probability=0.8, peak_hour=14)
    assert w.start_hour == 9

    # Out of bounds hour
    with pytest.raises(ValidationError):
        TimeWindow(start_hour=25)


def test_planned_commit_date_format() -> None:
    commit = PlannedCommit(
        id="c1",
        timestamp=datetime(2024, 5, 12, 14, 23, 45),
        timezone_str="+0700",
        author_name="Alice",
        author_email="alice@example.com",
        committer_name="Alice",
        committer_email="alice@example.com",
        message="feat(core): test commit",
    )
    assert commit.formatted_git_date == "2024-05-12T14:23:45 +0700"
