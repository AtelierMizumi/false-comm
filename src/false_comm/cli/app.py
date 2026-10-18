"""Typer application entry point for false-comm CLI."""

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from false_comm import __version__
from false_comm.cli.audit_cmd import handle_audit
from false_comm.cli.backfill_cmd import handle_backfill, parse_intensity
from false_comm.cli.doctor_cmd import run_doctor
from false_comm.cli.preview_cmd import render_heatmap
from false_comm.cli.replay_cmd import handle_replay
from false_comm.cli.undo_cmd import handle_undo
from false_comm.cli.wizard import run_mission_control
from false_comm.core.planner import CommitPlanner
from false_comm.core.profile import ProfileRegistry
from false_comm.git.adapter import GitAdapter
from false_comm.i18n import set_locale, t
from false_comm.models.config import DateRange, RepositoryRules
from false_comm.utils.dates import resolve_date_range

app = typer.Typer(
    name="false-comm",
    help="⚡ Realistic, professional Git commit history synthesizer for stealth and perfectionism.",
    add_completion=True,
    rich_markup_mode="rich",
    invoke_without_command=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        ver_str = t("cli.version", version=__version__)
        console.print(f"[bold cyan]{ver_str}[/bold cyan]")
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show false-comm version and exit",
        ),
    ] = False,
    lang: Annotated[
        str,
        typer.Option(
            "--lang",
            help="Interface language (en, vi)",
        ),
    ] = "en",
) -> None:
    """⚡ Realistic, professional Git commit history synthesizer for stealth and perfectionism."""
    set_locale(lang)
    if ctx.invoked_subcommand is None:
        # Launch interactive Mission Control Wizard by default
        run_mission_control(console=console)


@app.command("backfill")
def backfill(
    from_date: Annotated[
        str,
        typer.Option(
            "--from",
            "-f",
            help="Start date (YYYY-MM-DD) or relative lookback (e.g. 30d, 90d, 6m, 1y)",
        ),
    ] = "90d",
    to_date: Annotated[
        str | None,
        typer.Option(
            "--to",
            "-t",
            help="End date (YYYY-MM-DD, defaults to today/lookback end)",
        ),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            "-p",
            help="Behavior profile (standard, grinder, opensource, student, comeback)",
        ),
    ] = "standard",
    branch: Annotated[
        str | None,
        typer.Option(
            "--branch",
            "-b",
            help="Target branch (defaults to active branch)",
        ),
    ] = None,
    intensity: Annotated[
        str,
        typer.Option(
            "--intensity",
            "-i",
            help="Activity intensity (light, normal, heavy, or multiplier float like 1.2)",
        ),
    ] = "normal",
    no_vacation: Annotated[
        bool,
        typer.Option("--no-vacation", help="Disable synthetic vacation blackout periods"),
    ] = False,
    fill_gaps: Annotated[
        bool,
        typer.Option(
            "--fill-gaps",
            "-g",
            help="Gap-filling mode: prioritize inactive days, avoid stacking days that already have commits",
        ),
    ] = False,
    author_name: Annotated[
        str | None, typer.Option("--author-name", help="Override Git author name")
    ] = None,
    author_email: Annotated[
        str | None, typer.Option("--author-email", help="Override Git author email")
    ] = None,
    timezone: Annotated[
        str | None, typer.Option("--timezone", help="Override Git author timezone (e.g. +0700)")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", "-d", help="Simulate without writing git commits")
    ] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
    seed: Annotated[int | None, typer.Option("--seed", "-s", help="Random seed")] = None,
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Synthesize realistic commit distribution across a historical date range."""
    handle_backfill(
        from_date_str=from_date,
        to_date_str=to_date,
        profile_name=profile,
        target_branch=branch,
        intensity=intensity,
        no_vacation=no_vacation,
        fill_gaps=fill_gaps,
        author_name=author_name,
        author_email=author_email,
        timezone_str=timezone,
        dry_run=dry_run,
        auto_confirm=yes,
        seed=seed,
        repo_path=repo_path,
        console=console,
    )


@app.command("preview")
def preview(
    from_date: Annotated[
        str,
        typer.Option(
            "--from",
            "-f",
            help="Start date (YYYY-MM-DD) or relative lookback (e.g. 30d, 90d, 6m, 1y)",
        ),
    ] = "90d",
    to_date: Annotated[
        str | None,
        typer.Option(
            "--to",
            "-t",
            help="End date (YYYY-MM-DD, defaults to today/lookback end)",
        ),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            "-p",
            help="Behavior profile (standard, grinder, opensource, student, comeback)",
        ),
    ] = "standard",
    branch: Annotated[
        str | None,
        typer.Option(
            "--branch",
            "-b",
            help="Target branch (defaults to active branch)",
        ),
    ] = None,
    intensity: Annotated[
        str,
        typer.Option(
            "--intensity",
            "-i",
            help="Activity intensity (light, normal, heavy, or multiplier float like 1.2)",
        ),
    ] = "normal",
    no_vacation: Annotated[
        bool,
        typer.Option("--no-vacation", help="Disable synthetic vacation blackout periods"),
    ] = False,
    fill_gaps: Annotated[
        bool,
        typer.Option(
            "--fill-gaps",
            "-g",
            help="Gap-filling mode: prioritize inactive days, avoid stacking days that already have commits",
        ),
    ] = False,
    compare: Annotated[
        bool,
        typer.Option(
            "--compare",
            "-c",
            help="Show visual Before vs After side-by-side heatmaps",
        ),
    ] = False,
    seed: Annotated[int | None, typer.Option("--seed", "-s", help="Random seed")] = None,
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Render terminal contribution heatmap matrix without modifying repository state."""
    adapter = GitAdapter(repo_path)
    if not adapter.is_git_repo():
        console.print(f"[red]Error:[/red] {t('error.not_git_repo', path=str(adapter.repo_path))}")
        sys.exit(1)

    start_d, end_d = resolve_date_range(from_date, to_date)
    date_range = DateRange(start_date=start_d, end_date=end_d)

    prof = ProfileRegistry.load_profile(profile)
    identity = adapter.get_git_identity()
    target_b = branch or adapter.get_current_branch()
    rules = RepositoryRules(target_branch=target_b)

    existing_counts = adapter.get_commit_counts_by_date(
        start_date=start_d, end_date=end_d, branch=target_b
    )
    parsed_intensity = parse_intensity(intensity)

    planner = CommitPlanner(
        repo_root=adapter.get_repo_root(),
        profile=prof,
        identity=identity,
        rules=rules,
        seed=seed,
        intensity=parsed_intensity,
        no_vacation=no_vacation,
        fill_gaps=fill_gaps,
        existing_commits=existing_counts,
    )
    plan = planner.generate_plan(date_range)
    render_heatmap(plan, console=console, existing_counts=existing_counts, compare_mode=compare)


@app.command("replay")
def replay(
    commit_ref: Annotated[
        str,
        typer.Argument(
            help="Commit hash or reference to deconstruct and replay (e.g. HEAD, HEAD~1, a1b2c3d)"
        ),
    ],
    span: Annotated[
        str,
        typer.Option("--span", "-s", help="Time span to spread commits over (e.g. 7d, 3d, 14d)"),
    ] = "7d",
    profile: Annotated[
        str, typer.Option("--profile", "-p", help="Behavior profile to use for scheduling")
    ] = "standard",
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Deconstruct a monolithic commit into realistic progressive atomic steps across multiple days."""
    handle_replay(
        commit_ref=commit_ref,
        span=span,
        profile_name=profile,
        auto_confirm=yes,
        repo_path=repo_path,
        console=console,
    )


@app.command("undo")
def undo(
    snapshot_id: Annotated[
        str | None,
        typer.Option(
            "--snapshot", "-s", help="Specific snapshot ID to restore (defaults to latest)"
        ),
    ] = None,
    list_all: Annotated[
        bool, typer.Option("--list", "-l", help="List available safety snapshots")
    ] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Restore repository state to a previous pre-execution safety checkpoint."""
    handle_undo(
        snapshot_id=snapshot_id,
        list_all=list_all,
        auto_confirm=yes,
        repo_path=repo_path,
        console=console,
    )


@app.command("doctor")
def doctor(
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Diagnose git environment, author identity, repository health, and permissions."""
    run_doctor(repo_path=repo_path, console=console)


@app.command("audit")
def audit(
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Emit raw JSON forensic analysis")
    ] = False,
    max_commits: Annotated[
        int, typer.Option("--max-commits", "-m", help="Maximum commits to inspect")
    ] = 500,
    author: Annotated[
        str | None, typer.Option("--author", "-a", help="Filter commits by author name/email")
    ] = None,
) -> None:
    """Scan commit history for bot fingerprints, uniform timestamps, and robotic commit patterns."""
    handle_audit(
        max_commits=max_commits,
        author=author,
        as_json=json_output,
        repo_path=repo_path,
        console=console,
    )


@app.command("profiles")
def profiles() -> None:
    """List all available developer behavior profiles and their statistical characteristics."""
    table = Table(title=f"[bold cyan]{t('profiles.title')}[/bold cyan]", border_style="cyan")
    table.add_column(t("profiles.col_name"), style="bold green")
    table.add_column(t("profiles.col_desc"))
    table.add_column(t("profiles.col_prob"))
    table.add_column(t("profiles.col_disp"))

    for name in ProfileRegistry.list_available_profiles():
        p = ProfileRegistry.load_profile(name)
        table.add_row(
            p.name,
            p.description,
            f"{int(p.weekday_active_prob * 100)}% / {int(p.weekend_active_prob * 100)}%",
            f"{p.dispersion_r:.1f}",
        )

    console.print(table)


def main() -> None:
    """Application CLI entry point."""
    app()


if __name__ == "__main__":
    main()
