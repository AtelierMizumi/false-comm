"""Replay command rewriting a monolithic commit into a multi-day atomic progression."""

import json
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from false_comm.core.profile import ProfileRegistry
from false_comm.git.adapter import GitAdapter
from false_comm.git.snapshot import SnapshotManager
from false_comm.i18n import t
from false_comm.replay.analyzer import CommitDiffAnalysis, ReplayAnalyzer
from false_comm.replay.repartitioner import DiffRepartitioner, ReplayStep
from false_comm.replay.replayer import CommitReplayer


def build_replay_plan_payload(
    commit_ref: str,
    analysis: CommitDiffAnalysis,
    steps: list[ReplayStep],
    span_days: int,
) -> dict[str, object]:
    """Build a machine-readable replay plan without touching the repository."""
    return {
        "commit": commit_ref,
        "original_message": analysis.original_message,
        "span_days": span_days,
        "total_files": analysis.total_files,
        "total_steps": len(steps),
        "steps": [
            {
                "step_index": step.step_index,
                "phase": step.phase.value,
                "message": step.message,
                "files": list(step.files),
            }
            for step in steps
        ],
    }


def handle_replay(
    commit_ref: str,
    span: str = "7d",
    profile_name: str = "standard",
    auto_confirm: bool = False,
    dry_run: bool = False,
    json_output: bool = False,
    repo_path: Path | None = None,
    console: Console | None = None,
) -> None:
    """Preview and execute semantic replay of a commit."""
    console = console or Console()
    adapter = GitAdapter(repo_path)

    if not adapter.is_git_repo():
        console.print(
            f"[bold red]Error:[/bold red] {t('error.not_git_repo', path=str(adapter.repo_path))}"
        )
        return

    # Parse span (e.g. 7d, 3d, 14d)
    span_clean = span.lower().rstrip("d")
    span_days = int(span_clean) if span_clean.isdigit() else 7

    profile = ProfileRegistry.load_profile(profile_name)

    # 1. Analyze and preview steps
    analyzer = ReplayAnalyzer(adapter)
    try:
        analysis = analyzer.analyze_commit(commit_ref)
    except Exception as e:
        console.print(f"[bold red]Failed to inspect commit '{commit_ref}':[/bold red] {e}")
        return

    repartitioner = DiffRepartitioner()
    steps = repartitioner.partition(analysis)

    if not steps:
        console.print(f"[yellow]{t('replay.no_files', ref=commit_ref)}[/yellow]")
        return

    # Machine-readable plan export: never mutates the repository.
    if json_output:
        payload = build_replay_plan_payload(
            commit_ref=commit_ref,
            analysis=analysis,
            steps=steps,
            span_days=span_days,
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    # Show preview table
    title_str = t("replay.preview_title", ref=commit_ref[:8], count=len(steps), span=span_days)
    table = Table(
        title=f"[bold cyan]{title_str}[/bold cyan]",
        border_style="cyan",
    )
    table.add_column(t("replay.col_step"), style="bold green", no_wrap=True)
    table.add_column(t("replay.col_phase"), style="cyan")
    table.add_column(t("replay.col_message"))
    table.add_column(t("replay.col_files"), style="dim")

    for s in steps:
        files_str = ", ".join(s.files[:2]) + (
            f" (+{len(s.files) - 2} more)" if len(s.files) > 2 else ""
        )
        table.add_row(f"#{s.step_index}", s.phase.value, s.message, files_str)

    console.print(table)

    if dry_run:
        console.print(f"[bold yellow]{t('replay.dry_run_notice')}[/bold yellow]")
        return

    if not auto_confirm:
        prompt_str = t(
            "replay.confirm_prompt",
            ref=f"[bold green]{commit_ref[:8]}[/bold green]",
            count=f"[bold green]{len(steps)}[/bold green]",
        )
        confirm = Confirm.ask(prompt_str, default=False)
        if not confirm:
            console.print(f"[yellow]{t('replay.aborted')}[/yellow]")
            return

    # Execute replay
    snapshot_mgr = SnapshotManager(adapter)
    replayer = CommitReplayer(git_adapter=adapter, snapshot_manager=snapshot_mgr, profile=profile)

    with console.status(f"[cyan]{t('replay.status_running')}[/cyan]"):
        res = replayer.execute_replay(commit_ref=commit_ref, span_days=span_days)

    console.print(
        f"\n[bold green]{t('replay.success_title')}[/bold green]\n"
        f"  {t('replay.original_commit', sha=f'[dim]{res.original_sha[:8]}[/dim]')}\n"
        f"  {t('replay.steps_created', count=f'[bold]{res.total_steps}[/bold]')}\n"
        f"  {t('replay.new_head', sha=f'[cyan]{res.new_head_sha[:8]}[/cyan]')}\n"
        f"  {t('backfill.snapshot_info', snapshot_id=f'[yellow]{res.snapshot_id}[/yellow]')}\n"
    )
