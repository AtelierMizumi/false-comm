"""Unit tests for enhanced UX CLI commands: audit, relative dates, and wizards."""

import subprocess
from pathlib import Path

from typer.testing import CliRunner

from false_comm.cli.app import app

runner = CliRunner()


def test_cli_audit_command(tmp_path: Path) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Tester"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "tester@example.com"], check=True
    )

    f = tmp_path / "hello.txt"
    f.write_text("initial")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "chore: init"], check=True)

    result = runner.invoke(app, ["audit", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "Authenticity Score" in result.output
    assert "Forensic Metric" in result.output


def test_cli_audit_json_output(tmp_path: Path) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Tester"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "tester@example.com"], check=True
    )

    f = tmp_path / "hello.txt"
    f.write_text("initial")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "chore: init"], check=True)

    result = runner.invoke(app, ["audit", "--json", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert '"score":' in result.output
    assert '"metrics":' in result.output


def test_cli_preview_with_relative_date(tmp_path: Path) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Tester"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "tester@example.com"], check=True
    )
    f = tmp_path / "init.txt"
    f.write_text("init")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "init"], check=True)

    # Use relative offset '30d' without --to
    result = runner.invoke(app, ["preview", "--from", "30d", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "Contribution Heatmap Preview" in result.output
    assert "Activity Trend:" in result.output


def test_cli_backfill_relative_date_dry_run(tmp_path: Path) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Tester"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "tester@example.com"], check=True
    )
    f = tmp_path / "init.txt"
    f.write_text("init")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "init"], check=True)

    result = runner.invoke(app, ["backfill", "--from", "30d", "--dry-run", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "Dry-run mode active" in result.output
