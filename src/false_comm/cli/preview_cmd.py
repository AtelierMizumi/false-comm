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


def _calculate_streaks(counts_by_date: dict[date, int]) -> int:
    """Calculate the longest consecutive active streak in days."""
    longest_streak = 0
    curr_s = 0
    for d_item in sorted(counts_by_date.keys()):
        if counts_by_date[d_item] > 0:
            curr_s += 1
            if curr_s > longest_streak:
                longest_streak = curr_s
        else:
            curr_s = 0
    return longest_streak


def generate_heatmap_panel(
    start_d: date,
    end_d: date,
    counts_by_date: dict[date, int],
    title: str,
    border_style: str = "cyan",
) -> Panel:
    """Build a rich visual heatmap panel for a given date mapping."""
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

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

    month_header = Text("     ")
    last_month = None
    for week in display_weeks:
        first_day_of_week = week[0]
        if first_day_of_week.month != last_month and first_day_of_week.day <= 7:
            m_abbr = first_day_of_week.strftime("%b")
            month_header.append(f"{m_abbr:<2} ")
            last_month = first_day_of_week.month
        else:
            month_header.append("  ")

    grid_lines: list[Text] = [month_header]

    for row_idx, label in enumerate(weekday_names):
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

    weekly_totals: list[int] = []
    for week in display_weeks:
        w_sum = sum(counts_by_date.get(day, 0) for day in week)
        weekly_totals.append(w_sum)

    sparkline_str = render_sparkline(weekly_totals)

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

    return Panel(
        full_heatmap,
        title=f"[bold {border_style}]{title}[/bold {border_style}]",
        border_style=border_style,
        padding=(1, 2),
    )


def render_heatmap(
    plan: CommitPlan,
    console: Console | None = None,
    existing_counts: dict[date, int] | None = None,
    compare_mode: bool = False,
) -> None:
    """Render a GitHub-like contribution heatmap grid and key metrics in the terminal."""
    console = console or Console()

    if not plan.commits:
        console.print(f"[yellow]{t('heatmap.empty_plan')}[/yellow]")
        return

    start_d = datetime.strptime(plan.start_date, "%Y-%m-%d").date()
    end_d = datetime.strptime(plan.end_date, "%Y-%m-%d").date()

    # Planned counts
    plan_counts: dict[date, int] = {}
    weekday_counts = [0] * 7
    curr = start_d
    while curr <= end_d:
        plan_counts[curr] = 0
        curr += timedelta(days=1)

    for c in plan.commits:
        d = c.timestamp.date()
        if d in plan_counts:
            plan_counts[d] += 1
            weekday_counts[d.weekday()] += 1

    # Existing counts & Combined counts
    exist_counts: dict[date, int] = {}
    combined_counts: dict[date, int] = {}
    curr = start_d
    while curr <= end_d:
        e_cnt = existing_counts.get(curr, 0) if existing_counts else 0
        exist_counts[curr] = e_cnt
        combined_counts[curr] = e_cnt + plan_counts[curr]
        curr += timedelta(days=1)

    has_existing = sum(exist_counts.values()) > 0

    if compare_mode and has_existing:
        # Side-by-side comparison mode
        panel_before = generate_heatmap_panel(
            start_d,
            end_d,
            exist_counts,
            title=t("heatmap.before_title"),
            border_style="yellow",
        )
        console.print(panel_before)

        panel_combined = generate_heatmap_panel(
            start_d,
            end_d,
            combined_counts,
            title=t("heatmap.combined_title"),
            border_style="green",
        )
        console.print(panel_combined)
    else:
        # Default view: show combined if existing history exists, or planned view
        target_counts = combined_counts if has_existing else plan_counts
        panel_title = (
            t("heatmap.combined_title")
            if has_existing
            else t("heatmap.title", start=plan.start_date, end=plan.end_date)
        )
        panel = generate_heatmap_panel(
            start_d,
            end_d,
            target_counts,
            title=panel_title,
            border_style="cyan",
        )
        console.print(panel)

    # Statistical summary calculations
    total_planned = len(plan.commits)
    total_existing = sum(exist_counts.values())
    total_combined = sum(combined_counts.values())

    total_days = len(plan_counts)
    active_days_plan = sum(1 for c in plan_counts.values() if c > 0)
    active_days_exist = sum(1 for c in exist_counts.values() if c > 0)
    active_days_combined = sum(1 for c in combined_counts.values() if c > 0)

    gaps_filled = sum(1 for d in plan_counts if exist_counts[d] == 0 and plan_counts[d] > 0)

    streak_plan = _calculate_streaks(plan_counts)
    streak_exist = _calculate_streaks(exist_counts)
    streak_combined = _calculate_streaks(combined_counts)

    active_days_target = active_days_combined if has_existing else active_days_plan
    mean_active = (
        (total_combined / active_days_target)
        if active_days_target > 0
        else (total_planned / active_days_plan if active_days_plan > 0 else 0)
    )
    max_daily = max((combined_counts if has_existing else plan_counts).values(), default=0)

    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    busiest_day_idx = weekday_counts.index(max(weekday_counts)) if max(weekday_counts) > 0 else 0
    busiest_day_str = f"{weekday_names[busiest_day_idx]} ({max(weekday_counts)} commits)"

    # Statistical summary table
    table = Table(title=f"[bold]{t('heatmap.metrics_title')}[/bold]", border_style="dim")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row(t("heatmap.total_commits"), str(total_planned))
    if has_existing:
        table.add_row(t("heatmap.existing_commits"), f"[dim yellow]{total_existing}[/dim yellow]")
        table.add_row(t("heatmap.combined_commits"), f"[bold green]{total_combined}[/bold green]")
        table.add_row(
            t("heatmap.gaps_filled"),
            f"[bold magenta]{t('heatmap.gaps_restored', count=gaps_filled)}[/bold magenta]",
        )
        table.add_row(
            t("heatmap.active_days"),
            f"{active_days_exist} → [bold green]{active_days_combined}[/bold green] / {total_days} ({active_days_combined / total_days * 100:.1f}%)",
        )
        table.add_row(
            t("heatmap.longest_streak"),
            f"{streak_exist}d → [bold green]{t('heatmap.streak_unit', count=streak_combined)}[/bold green]",
        )
    else:
        table.add_row(
            t("heatmap.active_days"),
            f"{active_days_plan} / {total_days} ({active_days_plan / total_days * 100:.1f}%)",
        )
        table.add_row(
            t("heatmap.longest_streak"),
            t("heatmap.streak_unit", count=streak_plan),
        )

    table.add_row(t("heatmap.avg_commits"), f"{mean_active:.2f}")
    table.add_row(t("heatmap.max_daily"), str(max_daily))
    table.add_row("Busiest Day", busiest_day_str)
    table.add_row(t("heatmap.sim_branches"), str(len(plan.branches)))
    table.add_row(t("heatmap.sim_merges"), str(plan.merge_commits_count))
    table.add_row(t("heatmap.profile"), plan.profile_name)
    table.add_row(t("heatmap.target_branch"), plan.branch)

    console.print(table)
