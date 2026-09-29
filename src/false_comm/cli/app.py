"""Typer application entry point for false-comm CLI."""

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from false_comm import __version__
from false_comm.cli.audit_cmd import handle_audit
from false_comm.cli.backfill_cmd import handle_backfill
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
        console.print(f"[bold cyan]false-comm[/bold cyan] {ver_str}")
        raise typer.Exit()


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
    lang: Annotated[
        str | None,
        typer.Option(
            "--lang",
            "-l",
            help="Language interface (en, vi)",
        ),
    ] = None,
) -> None:
    """Realistic Git commit history synthesizer."""
    if lang:
        set_locale(lang)

    # Launch Mission Control Wizard if invoked with 0 args in an interactive terminal
    if ctx.invoked_subcommand is None:
        if sys.stdin.isatty():
            run_mission_control(console=console)
            raise typer.Exit()
        else:
            console.print(ctx.get_help())
            raise typer.Exit()


@app.command("wizard")
def wizard(
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Launch the interactive Mission Control Setup Wizard."""
    run_mission_control(repo_path=repo_path, console=console)


@app.command("audit")
def audit(
    max_commits: Annotated[
        int, typer.Option("--max", "-m", help="Maximum commits to inspect")
    ] = 500,
    author: Annotated[
        str | None, typer.Option("--author", "-a", help="Filter by author name or email")
    ] = None,
    as_json: Annotated[
        bool, typer.Option("--json", help="Output audit report in raw JSON format")
    ] = False,
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Evaluate repository git commit history for bot fingerprints and artificial regularity."""
    code = handle_audit(
        max_commits=max_commits,
        author=author,
        as_json=as_json,
        repo_path=repo_path,
        console=console,
    )
    if code != 0:
        raise typer.Exit(code=code)


@app.command("backfill")
def backfill(
    from_date: Annotated[
        str,
        typer.Option(
            "--from",
            "-f",
            help="Start date (YYYY-MM-DD) or relative duration (e.g. 30d, 90d, 6m, 1y)",
        ),
    ],
    to_date: Annotated[
        str | None,
        typer.Option(
            "--to",
            "-t",
            help="End date (YYYY-MM-DD, defaults to today)",
        ),
    ] = None,
    profile: Annotated[
        str,
        typer.Option(
            "--profile",
            "-p",
            help="Behavior profile name (e.g. standard, grinder, opensource, student)",
        ),
    ] = "standard",
    branch: Annotated[
        str | None,
        typer.Option("--branch", "-b", help="Target branch name (defaults to active branch)"),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", "-n", help="Simulate and preview without writing commits")
    ] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
    seed: Annotated[
        int | None, typer.Option("--seed", "-s", help="Random seed for deterministic simulation")
    ] = None,
    author_name: Annotated[
        str | None, typer.Option("--author-name", help="Override Git author name")
    ] = None,
    author_email: Annotated[
        str | None, typer.Option("--author-email", help="Override Git author email")
    ] = None,
    timezone: Annotated[
        str | None, typer.Option("--timezone", help="Override Git timezone (e.g. +0700)")
    ] = None,
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Synthesize historical commits over a specified date range with realistic distributions."""
    handle_backfill(
        from_date_str=from_date,
        to_date_str=to_date,
        profile_name=profile,
        target_branch=branch,
        dry_run=dry_run,
        auto_confirm=yes,
        seed=seed,
        author_name=author_name,
        author_email=author_email,
        timezone_str=timezone,
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
            help="Start date (YYYY-MM-DD) or relative duration (e.g. 30d, 90d, 6m, 1y)",
        ),
    ],
    to_date: Annotated[
        str | None,
        typer.Option(
            "--to",
            "-t",
            help="End date (YYYY-MM-DD, defaults to today)",
        ),
    ] = None,
    profile: Annotated[
        str, typer.Option("--profile", "-p", help="Behavior profile name")
    ] = "standard",
    branch: Annotated[str | None, typer.Option("--branch", "-b", help="Target branch")] = None,
    seed: Annotated[int | None, typer.Option("--seed", "-s", help="Random seed")] = None,
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Preview the synthesized contribution heatmap and stats in terminal without committing."""
    adapter = GitAdapter(repo_path)
    if not adapter.is_git_repo():
        console.print(
            f"[bold red]Error:[/bold red] {t('error.not_git_repo', path=str(adapter.repo_path))}"
        )
        raise typer.Exit(code=1)

    try:
        start_d, end_d = resolve_date_range(from_date, to_date)
        date_range = DateRange(start_date=start_d, end_date=end_d)
    except Exception as e:
        console.print(f"[bold red]{t('error.invalid_date', error=str(e))}[/bold red]")
        raise typer.Exit(code=1)

    prof = ProfileRegistry.load_profile(profile)
    identity = adapter.get_git_identity()
    target_b = branch or adapter.get_current_branch()
    rules = RepositoryRules(target_branch=target_b)

    planner = CommitPlanner(
        repo_root=adapter.get_repo_root(),
        profile=prof,
        identity=identity,
        rules=rules,
        seed=seed,
    )
    plan = planner.generate_plan(date_range)
    render_heatmap(plan, console=console)


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
    snapshot: Annotated[
        str | None, typer.Option("--snapshot", "-s", help="Specific snapshot ID to restore")
    ] = None,
    list_snapshots: Annotated[
        bool, typer.Option("--list", "-l", help="List available safety snapshots")
    ] = False,
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Restore repository state to a previous pre-execution safety checkpoint."""
    handle_undo(snapshot_id=snapshot, list_all=list_snapshots, repo_path=repo_path, console=console)


@app.command("doctor")
def doctor(
    repo_path: Annotated[
        Path | None, typer.Option("--repo", "-r", help="Path to Git repository")
    ] = None,
) -> None:
    """Diagnose repository readiness, git configuration, and timezone alignment."""
    ok = run_doctor(repo_path=repo_path, console=console)
    if not ok:
        raise typer.Exit(code=1)


@app.command("profiles")
def list_profiles() -> None:
    """List available behavioral profiles and their characteristics."""
    table = Table(title=f"[bold cyan]{t('profiles.title')}[/bold cyan]", border_style="cyan")
    table.add_column(t("profiles.col_name"), style="bold green")
    table.add_column(t("profiles.col_desc"))
    table.add_column(t("profiles.col_prob"))
    table.add_column(t("profiles.col_disp"))

    for name in ProfileRegistry.list_available_profiles():
        prof = ProfileRegistry.load_profile(name)
        table.add_row(
            prof.name,
            prof.description,
            f"{int(prof.weekday_active_prob * 100)}% / {int(prof.weekend_active_prob * 100)}%",
            str(prof.dispersion_r),
        )

    console.print(table)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
