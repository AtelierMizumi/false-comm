"""Unit tests for the interactive Mission Control wizard wiring."""

import io
from pathlib import Path
from typing import Any

import pytest
from rich.console import Console

from false_comm.cli import wizard
from false_comm.cli.wizard import render_wizard_header, run_mission_control
from false_comm.git.adapter import GitAdapter


def _console() -> tuple[Console, io.StringIO]:
    buffer = io.StringIO()
    return Console(file=buffer, width=200, force_terminal=False), buffer


def _answer_with(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> None:
    pending = iter(answers)

    def fake_ask(*args: Any, **kwargs: Any) -> str:
        return next(pending)

    monkeypatch.setattr(wizard.Prompt, "ask", fake_ask)


def test_header_reports_active_repository(temp_git_repo: Path) -> None:
    console, buffer = _console()

    is_repo = render_wizard_header(GitAdapter(temp_git_repo), console)

    assert is_repo is True
    output = buffer.getvalue()
    assert "Active Repository" in output
    assert "test_repo" in output
    assert "Test Committer" in output


def test_header_warns_outside_git_repository(tmp_path: Path) -> None:
    console, buffer = _console()

    is_repo = render_wizard_header(GitAdapter(tmp_path), console)

    assert is_repo is False
    assert "Not inside a Git repository." in buffer.getvalue()


def test_menu_exit_does_not_run_any_action(
    monkeypatch: pytest.MonkeyPatch, temp_git_repo: Path
) -> None:
    console, buffer = _console()
    _answer_with(monkeypatch, ["q"])

    run_mission_control(repo_path=temp_git_repo, console=console)

    assert "Goodbye!" in buffer.getvalue()


def test_menu_backfill_maps_choices_to_backfill_options(
    monkeypatch: pytest.MonkeyPatch, temp_git_repo: Path
) -> None:
    console, _ = _console()
    # choice=1 (backfill), range=2 (30d), profile=5 (comeback),
    # intensity=3 (heavy), fill gaps=n
    _answer_with(monkeypatch, ["1", "2", "5", "3", "n"])

    captured: dict[str, Any] = {}

    def fake_backfill(**kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(wizard, "handle_backfill", fake_backfill)

    run_mission_control(repo_path=temp_git_repo, console=console)

    assert captured["from_date_str"] == "30d"
    assert captured["profile_name"] == "comeback"
    assert captured["intensity"] == "heavy"
    assert captured["fill_gaps"] is False
    assert captured["repo_path"] == temp_git_repo


def test_menu_undo_lists_snapshots(monkeypatch: pytest.MonkeyPatch, temp_git_repo: Path) -> None:
    console, _ = _console()
    _answer_with(monkeypatch, ["6"])

    captured: dict[str, Any] = {}

    def fake_undo(**kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(wizard, "handle_undo", fake_undo)

    run_mission_control(repo_path=temp_git_repo, console=console)

    assert captured["list_all"] is True
    assert captured["repo_path"] == temp_git_repo


def test_menu_blocks_repository_actions_outside_git_repo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    console, buffer = _console()
    _answer_with(monkeypatch, ["1"])

    def fail_backfill(**kwargs: Any) -> None:
        raise AssertionError("backfill must not run outside a Git repository")

    monkeypatch.setattr(wizard, "handle_backfill", fail_backfill)

    run_mission_control(repo_path=tmp_path, console=console)

    assert "This action requires a Git repository." in buffer.getvalue()
