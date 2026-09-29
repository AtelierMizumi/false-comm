"""Unit tests for smart human-friendly date parser and relative ranges."""

from datetime import date, timedelta

import pytest

from false_comm.utils.dates import parse_date_or_relative, resolve_date_range


def test_parse_iso_date() -> None:
    d = parse_date_or_relative("2024-03-15")
    assert d == date(2024, 3, 15)


def test_parse_today_and_yesterday() -> None:
    assert parse_date_or_relative("today") == date.today()
    assert parse_date_or_relative("now") == date.today()
    assert parse_date_or_relative("yesterday") == date.today() - timedelta(days=1)


def test_parse_relative_days() -> None:
    expected_30d = date.today() - timedelta(days=30)
    assert parse_date_or_relative("30d") == expected_30d
    assert parse_date_or_relative("30 days") == expected_30d


def test_parse_relative_weeks() -> None:
    expected_2w = date.today() - timedelta(days=14)
    assert parse_date_or_relative("2w") == expected_2w
    assert parse_date_or_relative("2 weeks") == expected_2w


def test_parse_relative_years() -> None:
    expected_1y = date.today() - timedelta(days=365)
    assert parse_date_or_relative("1y") == expected_1y


def test_parse_invalid_date_raises_error() -> None:
    with pytest.raises(ValueError, match="Cannot parse date"):
        parse_date_or_relative("not-a-date")


def test_resolve_date_range_single_lookback() -> None:
    start_d, end_d = resolve_date_range("90d")
    assert end_d == date.today()
    assert start_d == date.today() - timedelta(days=90)


def test_resolve_date_range_explicit_pair() -> None:
    start_d, end_d = resolve_date_range("2024-01-01", "2024-03-31")
    assert start_d == date(2024, 1, 1)
    assert end_d == date(2024, 3, 31)


def test_resolve_date_range_inverted_raises_error() -> None:
    with pytest.raises(ValueError, match="cannot be after end date"):
        resolve_date_range("2024-05-01", "2024-01-01")
