"""Unit tests for HolidayCalendar."""

from datetime import date

from false_comm.core.holidays import HolidayCalendar


def test_global_holidays() -> None:
    cal = HolidayCalendar("GLOBAL")
    assert cal.is_holiday(date(2024, 1, 1))  # New Year
    assert cal.is_holiday(date(2024, 5, 1))  # Workers Day
    assert cal.is_holiday(date(2024, 12, 25))  # Christmas
    assert not cal.is_holiday(date(2024, 3, 15))  # Normal workday


def test_vietnam_holidays() -> None:
    cal = HolidayCalendar("VN")
    assert cal.is_holiday(date(2024, 4, 30))  # 30/4
    assert cal.is_holiday(date(2024, 5, 1))  # 1/5
    assert cal.is_holiday(date(2024, 9, 2))  # 2/9
    # Tet Giap Thin 2024 (Feb 8 - Feb 14)
    assert cal.is_holiday(date(2024, 2, 10))
    assert not cal.is_holiday(date(2024, 6, 15))


def test_us_holidays() -> None:
    cal = HolidayCalendar("US")
    assert cal.is_holiday(date(2024, 7, 4))  # 4th July
    assert cal.is_holiday(date(2024, 12, 25))  # Christmas
    # Thanksgiving 2024 (4th Thursday in Nov = Nov 28)
    assert cal.is_holiday(date(2024, 11, 28))
    assert not cal.is_holiday(date(2024, 11, 27))
