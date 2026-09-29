"""Unit tests for the Typer CLI commands."""

from pathlib import Path

from typer.testing import CliRunner

from false_comm.cli.app import app

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
