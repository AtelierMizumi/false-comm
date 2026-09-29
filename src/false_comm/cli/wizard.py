"""Interactive Mission Control Wizard for false-comm."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from false_comm import __version__
from false_comm.cli.audit_cmd import handle_audit
from false_comm.cli.backfill_cmd import handle_backfill
from false_comm.cli.doctor_cmd import run_doctor
from false_comm.cli.preview_cmd import render_heatmap
from false_comm.cli.replay_cmd import handle_replay
from false_comm.cli.undo_cmd import handle_undo
from false_comm.core.planner import CommitPlanner
from false_comm.core.profile import ProfileRegistry
from false_comm.git.adapter import GitAdapter
from false_comm.i18n import t
from false_comm.models.config import DateRange, RepositoryRules
from false_comm.utils.dates import resolve_date_range

BANNER = r"""
  ███████╗ █████╗ ██╗     ███████╗███████╗      ██████╗ ██████╗ ███╗   ███╗███╗   ███╗
  ██╔════╝██╔══██╗██║     ██╔════╝██╔════╝     ██╔════╝██╔═══██╗████╗ ████║████╗ ████║
  █████╗  ███████║██║     ███████╗█████╗  ═════██║     ██║   ██║██╔████╔██║██╔████╔██║
  ██╔══╝  ██╔══██║██║     ╚════██║██╔══╝       ██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║
  ██║     ██║  ██║███████╗███████║███████╗     ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║
"""


def render_wizard_header(adapter: GitAdapter, console: Console) -> bool:
    """Render welcome header and return whether current directory is a git repo."""
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")
    console.print(
        f"  [bold white]false-comm v{__version__}[/bold white] — "
        f"[dim]{t('cli.description')}[/dim]\n"
    )

    is_repo = adapter.is_git_repo()
    if is_repo:
        try:
            repo_name = adapter.get_repo_root().name
            branch = adapter.get_current_branch()
            id_info = adapter.get_git_identity()
            repo_status = (
                f"[green]✔[/green] Active Repository: [bold cyan]{repo_name}[/bold cyan] "
                f"(Branch: [cyan]{branch}[/cyan], Author: [white]{id_info.name} <{id_info.email}>[/white])"
            )
        except Exception:
            repo_status = "[yellow]⚠ Inside Git repository (minimal config detected)[/yellow]"
    else:
        repo_status = (
            "[yellow]⚠ Not inside a Git repository.[/yellow] "
            "[dim]Some actions require initializing or navigating to a git project.[/dim]"
        )

    console.print(Panel(repo_status, border_style="cyan" if is_repo else "yellow"))
    return is_repo


def run_mission_control(repo_path: Path | None = None, console: Console | None = None) -> None:
    """Launch the interactive false-comm Mission Control Wizard."""
    console = console or Console()
    adapter = GitAdapter(repo_path)
    is_repo = render_wizard_header(adapter, console)

    menu_table = Table(
        title=f"\n[bold]{t('wizard.prompt_choice')}[/bold]",
        show_header=False,
        border_style="dim",
        padding=(0, 2),
    )
    menu_table.add_column("Key", style="bold cyan", justify="right")
    menu_table.add_column("Action", style="bold white")
    menu_table.add_column("Description", style="dim")

    menu_table.add_row("[1]", "🚀 Backfill History", "Synthesize realistic commits across a date range")
    menu_table.add_row("[2]", "🎬 Replay Commit", "Deconstruct a monolithic commit into progressive steps")
    menu_table.add_row("[3]", "🔍 Stealth Audit", "Scan repository for bot/artificial commit patterns")
    menu_table.add_row("[4]", "📊 Contribution Heatmap", "Preview contribution matrix without committing")
    menu_table.add_row("[5]", "🩺 Repository Doctor", "Diagnose git configuration, author identity & system")
    menu_table.add_row("[6]", "↩ Undo / Rollback", "Restore repository state to a previous safety checkpoint")
    menu_table.add_row("[7]", "🎭 Behavior Profiles", "Explore standard, grinder, opensource profiles")
    menu_table.add_row("[q]", "🚪 Exit", "Close Mission Control")

    console.print(menu_table)

    choice = Prompt.ask(
        "\n[bold green]?[/bold green] Select an option",
        choices=["1", "2", "3", "4", "5", "6", "7", "q"],
        default="1",
        console=console,
    )

    if choice == "q":
        console.print("[dim]Goodbye![/dim]")
        return

    if choice == "1":
        # Backfill
        if not is_repo:
            console.print("[bold red]Error: This action requires a Git repository.[/bold red]")
            return
        range_choice = Prompt.ask(
            "Select time range:\n  [1] Last 90 days (default)\n  [2] Last 30 days\n  [3] Last 6 months\n  [4] Custom date range\nEnter choice",
            choices=["1", "2", "3", "4"],
            default="1",
            console=console,
        )
        if range_choice == "1":
            from_str = "90d"
        elif range_choice == "2":
            from_str = "30d"
        elif range_choice == "3":
            from_str = "6m"
        else:
            from_str = Prompt.ask("Enter start date (e.g. 2024-01-01 or 120d)", console=console)

        prof_choice = Prompt.ask(
            "Select profile:\n  [1] standard (balanced dev)\n  [2] grinder (high intensity)\n  [3] opensource (bursty PRs)\n  [4] student (evening/weekend)\nEnter choice",
            choices=["1", "2", "3", "4"],
            default="1",
            console=console,
        )
        prof_map = {"1": "standard", "2": "grinder", "3": "opensource", "4": "student"}
        prof_name = prof_map[prof_choice]

        handle_backfill(
            from_date_str=from_str,
            profile_name=prof_name,
            repo_path=repo_path,
            console=console,
        )

    elif choice == "2":
        # Replay
        if not is_repo:
            console.print("[bold red]Error: This action requires a Git repository.[/bold red]")
            return
        commit_ref = Prompt.ask(
            "Enter commit hash or ref to replay",
            default="HEAD",
            console=console,
        )
        span = Prompt.ask(
            "Time span to spread commits over (e.g. 7d, 3d, 14d)",
            default="7d",
            console=console,
        )
        handle_replay(
            commit_ref=commit_ref,
            span=span,
            repo_path=repo_path,
            console=console,
        )

    elif choice == "3":
        # Audit
        if not is_repo:
            console.print("[bold red]Error: This action requires a Git repository.[/bold red]")
            return
        handle_audit(repo_path=repo_path, console=console)

    elif choice == "4":
        # Preview Heatmap
        if not is_repo:
            console.print("[bold red]Error: This action requires a Git repository.[/bold red]")
            return
        from_str = Prompt.ask(
            "Time range for preview (e.g. 90d, 30d, 6m, 1y, or YYYY-MM-DD)",
            default="90d",
            console=console,
        )
        start_d, end_d = resolve_date_range(from_str)
        date_range = DateRange(start_date=start_d, end_date=end_d)
        prof = ProfileRegistry.load_profile("standard")
        identity = adapter.get_git_identity()
        target_b = adapter.get_current_branch()
        rules = RepositoryRules(target_branch=target_b)
        planner = CommitPlanner(
            repo_root=adapter.get_repo_root(),
            profile=prof,
            identity=identity,
            rules=rules,
        )
        plan = planner.generate_plan(date_range)
        render_heatmap(plan, console=console)

    elif choice == "5":
        # Doctor
        run_doctor(repo_path=repo_path, console=console)

    elif choice == "6":
        # Undo
        if not is_repo:
            console.print("[bold red]Error: This action requires a Git repository.[/bold red]")
            return
        handle_undo(list_all=True, repo_path=repo_path, console=console)

    elif choice == "7":
        # Profiles
        table = Table(title="[bold cyan]Behavior Profiles[/bold cyan]", border_style="cyan")
        table.add_column("Profile", style="bold green")
        table.add_column("Description")
        table.add_column("Active Probability (Wkday/Wkend)")
        table.add_column("Dispersion (r)")

        for name in ProfileRegistry.list_available_profiles():
            p = ProfileRegistry.load_profile(name)
            table.add_row(
                p.name,
                p.description,
                f"{int(p.weekday_active_prob * 100)}% / {int(p.weekend_active_prob * 100)}%",
                str(p.dispersion_r),
            )
        console.print(table)
