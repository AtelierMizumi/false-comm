"""Undo command for restoring repository to a previous safety checkpoint."""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from false_comm.git.adapter import GitAdapter
from false_comm.git.snapshot import SnapshotManager
from false_comm.i18n import t


def handle_undo(
    snapshot_id: str | None = None,
    list_all: bool = False,
    repo_path: Path | None = None,
    console: Console | None = None,
) -> None:
    """Execute undo/rollback or list available snapshots."""
    console = console or Console()
    adapter = GitAdapter(repo_path)
    if not adapter.is_git_repo():
        console.print(f"[red]Error:[/red] {t('error.not_git_repo', path=str(adapter.repo_path))}")
        return

    mgr = SnapshotManager(adapter)

    if list_all:
        snapshots = mgr.list_snapshots()
        if not snapshots:
            console.print(f"[yellow]{t('undo.no_snapshots')}[/yellow]")
            return

        table = Table(title=f"[bold cyan]{t('undo.snapshots_title')}[/bold cyan]")
        table.add_column(t("undo.col_id"), style="bold green")
        table.add_column(t("undo.col_created"), style="dim")
        table.add_column(t("undo.col_branch"), style="cyan")
        table.add_column(t("undo.col_head"), style="yellow")
        table.add_column(t("undo.col_commits"))
        table.add_column(t("undo.col_desc"))

        for s in snapshots:
            table.add_row(
                s.snapshot_id,
                s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                s.branch_name,
                s.head_sha[:8],
                str(s.commits_applied_count),
                s.description,
            )
        console.print(table)
        return

    # Perform rollback
    try:
        res = mgr.rollback(snapshot_id)
        console.print(
            f"[bold green]{t('undo.success')}[/bold green]\n"
            f"  Snapshot ID : {res.snapshot_id}\n"
            f"  Branch      : {res.branch_name}\n"
            f"  HEAD reset  : {res.head_sha[:8]}\n"
            f"  Branches rm : {len(res.active_branches_created)}"
        )
    except Exception as e:
        console.print(f"[bold red]{t('undo.failed', error=str(e))}[/bold red]")
