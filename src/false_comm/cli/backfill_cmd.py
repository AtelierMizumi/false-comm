"""Backfill command synthesizing realistic historical git commits."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.prompt import Confirm
from rich.text import Text

from false_comm.cli.preview_cmd import render_heatmap
from false_comm.core.executor import ExecutionResult, PlanExecutor
from false_comm.core.planner import CommitPlanner
from false_comm.core.profile import ProfileRegistry
from false_comm.git.adapter import GitAdapter
from false_comm.git.snapshot import SnapshotManager
from false_comm.i18n import t
from false_comm.models.commit import CommitPlan, PlannedCommit
from false_comm.models.config import DateRange, RepositoryRules
from false_comm.utils.dates import resolve_date_range


def parse_intensity(val: str | float | None) -> float:
    """Parse string or numeric intensity into a float multiplier."""
    if val is None:
        return 1.0
    if isinstance(val, (int, float)):
        return max(0.1, float(val))
    val_str = str(val).strip().lower()
    if val_str in ("light", "low", "nhe"):
        return 0.6
    if val_str in ("normal", "medium", "vua", "standard"):
        return 1.0
    if val_str in ("heavy", "high", "manh", "dense"):
        return 1.6
    try:
        return max(0.1, float(val_str))
    except ValueError:
        return 1.0


def render_celebration_card(res: ExecutionResult, plan: CommitPlan, console: Console) -> None:
    """Render a rewarding completion card confirming safety and next actions."""
    content = Text()
    content.append(f"🎉 {t('backfill.success_title')}\n\n", style="bold green")

    # Summary block
    content.append(f"📊 {t('celebrate.summary_title')}:\n", style="bold cyan")
    content.append(f"   • {t('celebrate.commits_created')} : ", style="dim")
    content.append(f"{res.commits_applied}\n", style="bold white")
    content.append(f"   • {t('celebrate.time_span')}       : ", style="dim")
    content.append(f"{plan.start_date} → {plan.end_date}\n", style="white")
    content.append(f"   • {t('celebrate.target_branch')}   : ", style="dim")
    content.append(f"{res.target_branch}\n", style="cyan")
    content.append(f"   • {t('celebrate.snapshot_id')}   : ", style="dim")
    content.append(f"{res.snapshot_id}\n\n", style="bold yellow")

    # Safety guarantee
    content.append("🛡️  Safety Guarantee:\n", style="bold")
    content.append(f"   {t('celebrate.safety_note')} ", style="dim")
    content.append("false-comm undo\n\n", style="bold green")

    # Next steps
    content.append(f"🚀 {t('celebrate.next_steps_title')}:\n", style="bold cyan")
    content.append("   • View git log   : ", style="dim")
    content.append("git log --graph --oneline -n 10\n", style="white")
    content.append("   • Audit stealth  : ", style="dim")
    content.append("false-comm audit\n", style="white")
    content.append("   • Push to remote : ", style="dim")
    content.append(f"git push origin {res.target_branch}\n", style="white")

    console.print(
        Panel(
            content,
            title=f"[bold green]✨ {t('celebrate.title')} ✨[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
    )


def handle_backfill(
    from_date_str: str,
    to_date_str: str | None = None,
    profile_name: str = "standard",
    target_branch: str | None = None,
    dry_run: bool = False,
    auto_confirm: bool = False,
    seed: int | None = None,
    author_name: str | None = None,
    author_email: str | None = None,
    timezone_str: str | None = None,
    intensity: str | float | None = 1.0,
    no_vacation: bool = False,
    fill_gaps: bool = False,
    repo_path: Path | None = None,
    console: Console | None = None,
) -> None:
    """Orchestrate backfill plan generation, preview, and execution."""
    console = console or Console()
    adapter = GitAdapter(repo_path)

    if not adapter.is_git_repo():
        console.print(
            f"[bold red]Error:[/bold red] {t('error.not_git_repo', path=str(adapter.repo_path))}"
        )
        return

    # Parse date range using human-friendly smart relative dates
    try:
        start_d, end_d = resolve_date_range(from_date_str, to_date_str)
        date_range = DateRange(start_date=start_d, end_date=end_d)
    except Exception as e:
        console.print(f"[bold red]{t('error.invalid_date', error=str(e))}[/bold red]")
        return

    # Resolve target branch
    current_branch = adapter.get_current_branch()
    branch = target_branch or current_branch

    # Resolve Git identity
    try:
        identity = adapter.get_git_identity()
    except Exception as e:
        console.print(f"[bold red]{e}[/bold red]")
        return

    if author_name:
        identity.name = author_name
    if author_email:
        identity.email = author_email
    if timezone_str:
        identity.timezone = timezone_str

    # Load profile
    try:
        profile = ProfileRegistry.load_profile(profile_name)
    except Exception as e:
        console.print(f"[bold red]{e}[/bold red]")
        return

    # Get existing commits for preview and gap-aware planning
    existing_counts = adapter.get_commit_counts_by_date(
        start_date=start_d, end_date=end_d, branch=branch
    )

    # Build plan
    parsed_intensity = parse_intensity(intensity)
    rules = RepositoryRules(target_branch=branch)
    planner = CommitPlanner(
        repo_root=adapter.get_repo_root(),
        profile=profile,
        identity=identity,
        rules=rules,
        seed=seed,
        intensity=parsed_intensity,
        no_vacation=no_vacation,
        fill_gaps=fill_gaps,
        existing_commits=existing_counts,
    )

    console.print(
        f"[dim]{t('backfill.planning', from_date=str(start_d), to_date=str(end_d))}[/dim]"
    )
    plan = planner.generate_plan(date_range)

    # Render terminal heatmap and statistics
    render_heatmap(plan, console=console, existing_counts=existing_counts)

    if dry_run:
        console.print(f"[bold yellow]{t('backfill.dry_run_notice')}[/bold yellow]")
        return

    if not auto_confirm:
        prompt_str = t(
            "backfill.confirm_prompt",
            count=f"[bold green]{len(plan.commits)}[/bold green]",
            branch=f"[cyan]{branch}[/cyan]",
        )
        confirm = Confirm.ask(prompt_str, default=False)
        if not confirm:
            console.print(f"[yellow]{t('backfill.aborted')}[/yellow]")
            return

    # Initialize snapshot manager and executor
    snapshot_mgr = SnapshotManager(adapter)
    executor = PlanExecutor(
        git_adapter=adapter,
        snapshot_manager=snapshot_mgr,
    )

    # Execute plan with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"[cyan]{t('backfill.task_title')}[/cyan]", total=len(plan.commits)
        )

        def on_step(idx: int, total: int, commit: PlannedCommit) -> None:
            clean_msg = commit.message.splitlines()[0][:50]
            progress.update(
                task,
                completed=idx,
                description=f"[cyan]{t('backfill.commit_progress', idx=idx, total=total, msg=clean_msg)}[/cyan]",
            )

        res = executor.execute(plan, progress_callback=on_step)

    # Display celebration card
    render_celebration_card(res, plan, console)
