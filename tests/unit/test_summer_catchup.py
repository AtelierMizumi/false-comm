"""Unit and integration tests for summer catchup, comeback profile, and preview compare."""

from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from false_comm.cli.app import app
from false_comm.core.behavior import BehaviorEngine
from false_comm.core.holidays import HolidayCalendar
from false_comm.core.profile import ProfileRegistry
from false_comm.git.adapter import GitAdapter
from false_comm.models.config import DateRange


def test_comeback_profile_registered_and_valid() -> None:
    profiles = ProfileRegistry.list_available_profiles()
    assert "comeback" in profiles
    prof = ProfileRegistry.load_profile("comeback")
    assert prof.name == "comeback"
    assert prof.vacation_weeks_per_year == 0
    assert prof.weekday_active_prob > 0.8


def test_intensity_scaling() -> None:
    prof = ProfileRegistry.load_profile("standard")
    cal = HolidayCalendar("GLOBAL")
    dr = DateRange(start_date=date(2024, 6, 1), end_date=date(2024, 8, 31))

    # Light intensity vs Heavy intensity
    engine_light = BehaviorEngine(profile=prof, holiday_calendar=cal, seed=42, intensity=0.5)
    plan_light = engine_light.plan_daily_commits(dr)
    total_light = sum(d.commit_count for d in plan_light)

    engine_heavy = BehaviorEngine(profile=prof, holiday_calendar=cal, seed=42, intensity=2.0)
    plan_heavy = engine_heavy.plan_daily_commits(dr)
    total_heavy = sum(d.commit_count for d in plan_heavy)

    assert total_heavy > total_light * 2.0


def test_fill_gaps_mode_skips_heavily_active_days() -> None:
    prof = ProfileRegistry.load_profile("comeback")
    cal = HolidayCalendar("GLOBAL")
    dr = DateRange(start_date=date(2024, 7, 1), end_date=date(2024, 7, 10))

    # Suppose day 2024-07-03 already has 5 commits
    existing = {date(2024, 7, 3): 5}
    engine = BehaviorEngine(
        profile=prof,
        holiday_calendar=cal,
        seed=123,
        fill_gaps=True,
        existing_commits=existing,
    )
    plan = engine.plan_daily_commits(dr)

    day_3 = next(d for d in plan if d.target_date == date(2024, 7, 3))
    assert day_3.commit_count == 0


def test_get_commit_counts_by_date(tmp_path: Path) -> None:
    adapter = GitAdapter(tmp_path)
    adapter.run_git(["init"])
    adapter.run_git(["config", "user.name", "Test User"])
    adapter.run_git(["config", "user.email", "test@example.com"])

    # Commit 1 on 2024-06-15
    f1 = tmp_path / "a.txt"
    f1.write_text("hello")
    adapter.add_files(["a.txt"])
    adapter.commit(
        message="feat: first",
        author_date="2024-06-15T10:00:00+00:00",
        committer_date="2024-06-15T10:00:00+00:00",
        author_name="Test User",
        author_email="test@example.com",
    )

    # Commit 2 on 2024-06-15
    f1.write_text("hello world")
    adapter.add_files(["a.txt"])
    adapter.commit(
        message="feat: second",
        author_date="2024-06-15T15:00:00+00:00",
        committer_date="2024-06-15T15:00:00+00:00",
        author_name="Test User",
        author_email="test@example.com",
    )

    counts = adapter.get_commit_counts_by_date(
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 30),
    )
    assert counts.get(date(2024, 6, 15)) == 2


def test_cli_preview_compare_and_comeback(tmp_path: Path) -> None:
    adapter = GitAdapter(tmp_path)
    adapter.run_git(["init", "-b", "main"])
    adapter.run_git(["config", "user.name", "Summer Coder"])
    adapter.run_git(["config", "user.email", "coder@example.com"])

    dummy = tmp_path / "init.txt"
    dummy.write_text("init")
    adapter.add_files(["init.txt"])
    adapter.commit(
        message="init",
        author_date="2024-06-01T12:00:00+00:00",
        committer_date="2024-06-01T12:00:00+00:00",
        author_name="Summer Coder",
        author_email="coder@example.com",
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "preview",
            "--from",
            "2024-06-01",
            "--to",
            "2024-08-31",
            "--profile",
            "comeback",
            "--intensity",
            "normal",
            "--fill-gaps",
            "--compare",
            "--repo",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    assert "Current Git History (Before)" in result.output
    assert "Current + Backfill" in result.output
    assert "blank days restored" in result.output
