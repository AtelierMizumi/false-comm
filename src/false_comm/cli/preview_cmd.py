"""Rich terminal contribution heatmap and statistical distribution renderer."""

from datetime import date, datetime, timedelta

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from false_comm.i18n import t
from false_comm.models.commit import CommitPlan

SPARK_CHARS = (" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█")


def render_sparkline(values: list[int]) -> str:
    """Render a sequence of integer values as a unicode sparkline."""
    if not values:
        return ""
    max_val = max(values)
    if max_val == 0:
        return SPARK_CHARS[0] * len(values)
    res = []
    for v in values:
        idx = int(round((v / max_val) * (len(SPARK_CHARS) - 1)))
        res.append(SPARK_CHARS[idx])
    return "".join(res)


def render_heatmap(plan: CommitPlan, console: Console | None = None) -> None:
    """Render a GitHub-like contribution heatmap grid and key metrics in the terminal."""
    console = console or Console()

    if not plan.commits:
        console.print(f"[yellow]{t('heatmap.empty_plan')}[/yellow]")
        return

    # Count commits per date
    counts_by_date: dict[date, int] = {}
    start_d = datetime.strptime(plan.start_date, "%Y-%m-%d").date()
    end_d = datetime.strptime(plan.end_date, "%Y-%m-%d").date()

    curr = start_d
    while curr <= end_d:
        counts_by_date[curr] = 0
        curr += timedelta(days=1)

    # Weekday counts for busiest day metric (Monday=0 ... Sunday=6)
    weekday_counts = [0] * 7

    for c in plan.commits:
        d = c.timestamp.date()
        if d in counts_by_date:
            counts_by_date[d] += 1
            weekday_counts[d.weekday()] += 1

    total_commits = len(plan.commits)
    active_days = sum(1 for count in counts_by_date.values() if count > 0)
    total_days = len(counts_by_date)
    max_daily = max(counts_by_date.values()) if counts_by_date else 0
    mean_active = total_commits / active_days if active_days > 0 else 0

    # Calculate streaks
    longest_streak = 0
    current_streak = 0
    curr_s = 0
    for d_item in sorted(counts_by_date.keys()):
        if counts_by_date[d_item] > 0:
            curr_s += 1
            if curr_s > longest_streak:
                longest_streak = curr_s
        else:
            curr_s = 0
    # Current active streak ending at end_d
    for d_item in reversed(sorted(counts_by_date.keys())):
        if counts_by_date[d_item] > 0:
            current_streak += 1
        else:
            break

    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    busiest_day_idx = weekday_counts.index(max(weekday_counts)) if max(weekday_counts) > 0 else 0
    busiest_day_str = f"{weekday_names[busiest_day_idx]} ({max(weekday_counts)} commits)"

    # Build weekly columns (Monday=0 ... Sunday=6)
    monday_start = start_d - timedelta(days=start_d.weekday())
    sunday_end = end_d + timedelta(days=(6 - end_d.weekday()))

    weeks: list[list[date]] = []
    current_week: list[date] = []
    d_ptr = monday_start
    while d_ptr <= sunday_end:
        current_week.append(d_ptr)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
        d_ptr += timedelta(days=1)
    if current_week:
        weeks.append(current_week)

    # TrueColor palette mapping thresholds matching GitHub dark mode
    def get_color_char(count: int, in_range: bool) -> tuple[str, str]:
        if not in_range:
            return ("·", "dim #30363d")
        if count == 0:
            return ("■", "#21262d")
        if count <= 2:
            return ("■", "#0e4429")
        if count <= 4:
            return ("■", "#006d32")
        if count <= 7:
            return ("■", "#26a641")
        return ("■", "bold #39d353")

    max_display_weeks = 52
    display_weeks = weeks[-max_display_weeks:]

    # Month header line
    month_header = Text("     ")  # align with 'Mon  '
    last_month = None
    for week in display_weeks:
        first_day_of_week = week[0]
        # Label month when a new month starts in this week column
        if first_day_of_week.month != last_month and first_day_of_week.day <= 7:
            m_abbr = first_day_of_week.strftime("%b")
            month_header.append(f"{m_abbr:<2} ")
            last_month = first_day_of_week.month
        else:
            month_header.append("  ")

    # Heatmap grid table
    grid_lines: list[Text] = [month_header]

    for row_idx, label in enumerate(weekday_names):
        # Only show labels for Mon, Wed, Fri for clean look like GitHub
        row_label = f"{label:<4} " if row_idx in (0, 2, 4) else "     "
        line = Text(row_label, style="dim white")
        for week in display_weeks:
            day_val = week[row_idx]
            in_range = start_d <= day_val <= end_d
            count = counts_by_date.get(day_val, 0)
            char, color = get_color_char(count, in_range)
            line.append(char + " ", style=color)
        grid_lines.append(line)

    grid_content = Text("\n").join(grid_lines)

    # Calculate weekly sums for sparkline
    weekly_totals: list[int] = []
    for week in display_weeks:
        w_sum = sum(counts_by_date.get(day, 0) for day in week)
        weekly_totals.append(w_sum)

    sparkline_str = render_sparkline(weekly_totals)

    # Legend
    legend = Text(f"\n{t('heatmap.legend_label')}  ")
    legend.append("■ ", style="#21262d")
    legend.append("0  ")
    legend.append("■ ", style="#0e4429")
    legend.append("1-2  ")
    legend.append("■ ", style="#006d32")
    legend.append("3-4  ")
    legend.append("■ ", style="#26a641")
    legend.append("5-7  ")
    legend.append("■ ", style="bold #39d353")
    legend.append(f"8+ {t('heatmap.commits_unit')}   ")
    legend.append("  Activity Trend: ", style="dim")
    legend.append(sparkline_str, style="bold green")

    full_heatmap = Text("\n").join([grid_content, legend])

    title_str = t("heatmap.title", start=plan.start_date, end=plan.end_date)
    console.print(
        Panel(
            full_heatmap,
            title=f"[bold cyan]{title_str}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # Statistical summary table
    table = Table(title=f"[bold]{t('heatmap.metrics_title')}[/bold]", border_style="dim")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row(t("heatmap.total_commits"), str(total_commits))
    table.add_row(
        t("heatmap.active_days"),
        f"{active_days} / {total_days} ({active_days / total_days * 100:.1f}%)",
    )
    table.add_row(t("heatmap.avg_commits"), f"{mean_active:.2f}")
    table.add_row(t("heatmap.max_daily"), str(max_daily))
    table.add_row("Busiest Day", busiest_day_str)
    table.add_row("Longest Streak", f"{longest_streak} consecutive active days")
    table.add_row(t("heatmap.sim_branches"), str(len(plan.branches)))
    table.add_row(t("heatmap.sim_merges"), str(plan.merge_commits_count))
    table.add_row(t("heatmap.profile"), plan.profile_name)
    table.add_row(t("heatmap.target_branch"), plan.branch)

    console.print(table)
