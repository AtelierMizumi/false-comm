"""Audit CLI command evaluating repository git commit history authenticity."""

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from false_comm.core.audit import AuditEngine, AuditResult
from false_comm.git.adapter import GitAdapter
from false_comm.i18n import t


def render_score_gauge(score: int, width: int = 24) -> Text:
    """Render a colored visual block gauge for authenticity score."""
    filled_blocks = int(round((score / 100.0) * width))
    empty_blocks = width - filled_blocks

    if score >= 85:
        bar_color = "bold green"
    elif score >= 65:
        bar_color = "bold yellow"
    else:
        bar_color = "bold red"

    txt = Text()
    txt.append("▕", style="dim white")
    txt.append("█" * filled_blocks, style=bar_color)
    txt.append("░" * empty_blocks, style="dim grey")
    txt.append("▏ ", style="dim white")
    txt.append(f"{score:>3}/100", style="bold white")
    return txt


def render_audit_ui(result: AuditResult, repo_name: str, branch: str, console: Console) -> None:
    """Render rich visual audit report."""
    # Header panel
    title = t("audit.title")
    subtitle = t("audit.subtitle")

    header_text = Text()
    header_text.append(f"🛡️  {title}\n", style="bold cyan")
    header_text.append(f"{subtitle}\n\n", style="dim")
    header_text.append(f"Repository : {repo_name} (Branch: {branch})\n", style="cyan")
    header_text.append(f"Evaluated  : {result.total_commits} commits\n", style="dim")

    # Authenticity Score Display
    gauge = render_score_gauge(result.score)
    score_line = Text("\n" + t("audit.score_label") + ": ")
    score_line.append_text(gauge)
    score_line.append(f"  [{result.rating_label}]\n", style="bold")
    header_text.append_text(score_line)

    console.print(Panel(header_text, border_style="cyan", padding=(1, 2)))

    # Metrics Table
    table = Table(
        title=f"[bold]{t('audit.metric_col')}[/bold]",
        border_style="dim",
        header_style="bold cyan",
    )
    table.add_column(t("audit.metric_col"), style="white")
    table.add_column(t("audit.value_col"), justify="right")
    table.add_column(t("audit.status_col"), justify="center")
    table.add_column(t("audit.ideal_col"), style="dim")

    def status_badge(is_ok: bool, is_warn: bool = False) -> str:
        if is_ok:
            return f"[bold green]{t('audit.pass')}[/bold green]"
        if is_warn:
            return f"[bold yellow]{t('audit.warn')}[/bold yellow]"
        return f"[bold red]{t('audit.fail')}[/bold red]"

    # 1. Round seconds
    sec_ok = result.round_seconds_pct <= 10.0
    sec_warn = 10.0 < result.round_seconds_pct <= 25.0
    table.add_row(
        t("audit.round_sec"),
        f"{result.round_seconds_pct:.1f}%",
        status_badge(sec_ok, sec_warn),
        t("audit.ideal_sec"),
    )

    # 2. Round minutes
    min_ok = result.round_minutes_pct <= 30.0
    min_warn = 30.0 < result.round_minutes_pct <= 45.0
    table.add_row(
        t("audit.round_min"),
        f"{result.round_minutes_pct:.1f}%",
        status_badge(min_ok, min_warn),
        t("audit.ideal_min"),
    )

    # 3. Identical intervals
    int_ok = result.identical_intervals_pct <= 15.0
    int_warn = 15.0 < result.identical_intervals_pct <= 30.0
    table.add_row(
        t("audit.identical_intervals"),
        f"{result.identical_intervals_pct:.1f}%",
        status_badge(int_ok, int_warn),
        t("audit.ideal_interval"),
    )

    # 4. Empty commits
    empty_ok = result.empty_commits_count == 0
    table.add_row(
        t("audit.empty_commits"),
        f"{result.empty_commits_count}",
        status_badge(empty_ok, False),
        t("audit.ideal_empty"),
    )

    # 5. Night commits
    night_ok = result.night_commits_pct <= 25.0
    night_warn = 25.0 < result.night_commits_pct <= 40.0
    table.add_row(
        t("audit.night_commits"),
        f"{result.night_commits_pct:.1f}%",
        status_badge(night_ok, night_warn),
        t("audit.ideal_night"),
    )

    # 6. Weekend ratio
    table.add_row(
        t("audit.weekend_commits"),
        f"{result.weekend_commits_pct:.1f}%",
        status_badge(True, False),
        t("audit.ideal_weekend"),
    )

    console.print(table)

    # Findings Panel
    if result.findings:
        findings_text = Text()
        for f in result.findings:
            if f.severity == "critical":
                icon, color = "✘", "bold red"
            elif f.severity == "warning":
                icon, color = "⚠", "bold yellow"
            else:
                icon, color = "✔", "bold green"
            findings_text.append(f"{icon} {f.title}: ", style=color)
            findings_text.append(f"{f.detail}\n", style="white")

        console.print(
            Panel(
                findings_text,
                title=f"[bold]{t('audit.findings_title')}[/bold]",
                border_style="yellow" if result.score < 80 else "green",
            )
        )

    # Recommendations Panel
    if result.recommendations:
        recs_text = Text()
        for r in result.recommendations:
            recs_text.append(f"• {r}\n", style="dim cyan")

        console.print(
            Panel(
                recs_text,
                title=f"[bold]{t('audit.recommendations_title')}[/bold]",
                border_style="blue",
            )
        )


def handle_audit(
    max_commits: int = 500,
    author: str | None = None,
    as_json: bool = False,
    repo_path: Path | None = None,
    console: Console | None = None,
) -> int:
    """Execute stealth audit on repository and render results."""
    console = console or Console()
    adapter = GitAdapter(repo_path)

    if not adapter.is_git_repo():
        console.print(
            f"[bold red]Error:[/bold red] {t('error.not_git_repo', path=str(adapter.repo_path))}"
        )
        return 1

    branch = adapter.get_current_branch()
    repo_name = adapter.get_repo_root().name

    engine = AuditEngine(adapter)
    result = engine.audit(max_commits=max_commits, author_filter=author)

    if as_json:
        payload = {
            "repository": repo_name,
            "branch": branch,
            "total_commits": result.total_commits,
            "score": result.score,
            "rating": result.rating_label,
            "metrics": {
                "round_seconds_pct": result.round_seconds_pct,
                "round_minutes_pct": result.round_minutes_pct,
                "identical_intervals_pct": result.identical_intervals_pct,
                "empty_commits_count": result.empty_commits_count,
                "night_commits_pct": result.night_commits_pct,
                "weekend_commits_pct": result.weekend_commits_pct,
            },
            "findings": [
                {"severity": f.severity, "title": f.title, "detail": f.detail}
                for f in result.findings
            ],
            "recommendations": result.recommendations,
        }
        console.print_json(json.dumps(payload))
        return 0

    render_audit_ui(result, repo_name=repo_name, branch=branch, console=console)
    return 0
