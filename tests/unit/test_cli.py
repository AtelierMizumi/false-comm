"""Unit tests for the Typer CLI commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from false_comm.cli.app import app
from false_comm.cli.backfill_cmd import parse_intensity

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "false-comm" in result.output
    assert "version 2.0.0" in result.output


def test_cli_profiles() -> None:
    result = runner.invoke(app, ["profiles"])
    assert result.exit_code == 0
    assert "standard" in result.output
    assert "grinder" in result.output
    assert "opensource" in result.output
    assert "student" in result.output


def test_cli_doctor(temp_git_repo: Path) -> None:
    result = runner.invoke(app, ["doctor", "--repo", str(temp_git_repo)])
    assert result.exit_code == 0
    assert "Git CLI" in result.output
    assert "Repository" in result.output


def test_cli_preview(temp_git_repo: Path) -> None:
    result = runner.invoke(
        app,
        [
            "preview",
            "--from",
            "2024-01-01",
            "--to",
            "2024-01-14",
            "--profile",
            "standard",
            "--repo",
            str(temp_git_repo),
            "--seed",
            "42",
        ],
    )
    assert result.exit_code == 0
    assert "Contribution Heatmap Preview" in result.output
    assert "Total Commits Planned" in result.output


def test_cli_backfill_dry_run(temp_git_repo: Path) -> None:
    result = runner.invoke(
        app,
        [
            "backfill",
            "--from",
            "2024-01-01",
            "--to",
            "2024-01-07",
            "--dry-run",
            "--repo",
            str(temp_git_repo),
            "--seed",
            "42",
        ],
    )
    assert result.exit_code == 0
    assert "Dry-run mode active" in result.output


def test_cli_undo_list(temp_git_repo: Path) -> None:
    result = runner.invoke(app, ["undo", "--list", "--repo", str(temp_git_repo)])
    assert result.exit_code == 0
    assert "No snapshots found" in result.output or "Available Safety Snapshots" in result.output


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, 1.0),
        (2, 2.0),
        (0.05, 0.1),
        ("light", 0.6),
        ("low", 0.6),
        ("NHE", 0.6),
        ("normal", 1.0),
        ("medium", 1.0),
        ("vua", 1.0),
        ("standard", 1.0),
        ("heavy", 1.6),
        ("high", 1.6),
        ("manh", 1.6),
        ("dense", 1.6),
        ("1.3", 1.3),
        ("0.01", 0.1),
        ("not-a-number", 1.0),
    ],
)
def test_parse_intensity(value: object, expected: float) -> None:
    assert parse_intensity(value) == pytest.approx(expected)
