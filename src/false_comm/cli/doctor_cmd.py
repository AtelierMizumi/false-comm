"""Doctor diagnostic command inspecting environment and repository readiness."""

from pathlib import Path

from rich.console import Console
from rich.table import Table

from false_comm.git.adapter import GitAdapter
from false_comm.i18n import t
from false_comm.utils.platform import detect_distro


def run_doctor(repo_path: Path | None = None, console: Console | None = None) -> bool:
    """Run comprehensive environment diagnostics and return True if all passed."""
    console = console or Console()
    table = Table(title=f"[bold cyan]{t('doctor.title')}[/bold cyan]", border_style="cyan")
    table.add_column("Component", style="bold")
    table.add_column("Status", no_wrap=True)
    table.add_column("Details")

    all_passed = True
    adapter = GitAdapter(repo_path)

    # 1. OS & Linux distro detection
    distro = detect_distro()
    distro_str = f"{distro.name} {distro.version}".strip()
    if distro.in_container:
        distro_str += " (container)"
    table.add_row(t("doctor.os_distro"), f"[green]{t('doctor.pass')}[/green]", distro_str)

    # 2. Git binary check
    try:
        git_ver_res = adapter.run_git(["--version"])
        table.add_row(
            t("doctor.git_cli"), f"[green]{t('doctor.pass')}[/green]", git_ver_res.stdout.strip()
        )
    except Exception as e:
        table.add_row(
            t("doctor.git_cli"), f"[red]{t('doctor.fail')}[/red]", f"Git command failed: {e}"
        )
        all_passed = False

    # 3. Repository check
    is_repo = adapter.is_git_repo()
    if is_repo:
        repo_root = adapter.get_repo_root()
        table.add_row(t("doctor.repository"), f"[green]{t('doctor.pass')}[/green]", str(repo_root))
    else:
        table.add_row(
            t("doctor.repository"),
            f"[red]{t('doctor.fail')}[/red]",
            f"Not a git repo: {adapter.repo_path}",
        )
        all_passed = False

    if is_repo:
        # 4. Active branch
        try:
            branch = adapter.get_current_branch()
            table.add_row(t("doctor.active_branch"), f"[green]{t('doctor.pass')}[/green]", branch)
        except Exception as e:
            table.add_row(t("doctor.active_branch"), f"[red]{t('doctor.fail')}[/red]", str(e))
            all_passed = False

        # 5. Identity check
        try:
            ident = adapter.get_git_identity()
            table.add_row(
                t("doctor.author_identity"),
                f"[green]{t('doctor.pass')}[/green]",
                f"{ident.name} <{ident.email}> (tz: {ident.timezone})",
            )
        except Exception as e:
            table.add_row(
                t("doctor.author_identity"),
                f"[red]{t('doctor.fail')}[/red]",
                f"Missing git config: {e}",
            )
            all_passed = False

        # 6. Working tree dirty check
        has_dirty = adapter.has_uncommitted_changes()
        if has_dirty:
            table.add_row(
                t("doctor.working_tree"),
                f"[yellow]{t('doctor.warn')}[/yellow]",
                t("doctor.tree_dirty_warn"),
            )
        else:
            table.add_row(
                t("doctor.working_tree"),
                f"[green]{t('doctor.pass')}[/green]",
                t("doctor.tree_clean"),
            )

        # 7. Snapshot storage check
        snap_dir = repo_root / ".git" / "false_comm" / "snapshots"
        try:
            snap_dir.mkdir(parents=True, exist_ok=True)
            table.add_row(
                t("doctor.snapshot_storage"), f"[green]{t('doctor.pass')}[/green]", str(snap_dir)
            )
        except Exception as e:
            table.add_row(
                t("doctor.snapshot_storage"),
                f"[red]{t('doctor.fail')}[/red]",
                f"Cannot write snapshots: {e}",
            )
            all_passed = False

    console.print(table)
    return all_passed
