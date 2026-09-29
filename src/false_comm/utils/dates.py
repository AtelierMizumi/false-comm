"""Smart human-friendly date parser supporting natural expressions and relative offsets."""

import re
from datetime import date, datetime, timedelta


def parse_date_or_relative(input_str: str) -> date:
    """Parse date from standard ISO format or human-friendly relative expressions.

    Supported formats:
    - 'today', 'now'
    - 'yesterday'
    - '30d', '60d', '90d', '180d', '365d' (offset from today)
    - '1w', '2w', '4w'
    - '1m', '3m', '6m', '12m'
    - '1y', '2y'
    - 'YYYY-MM-DD'
    """
    cleaned = input_str.strip().lower()

    if cleaned in ("today", "now"):
        return date.today()

    if cleaned == "yesterday":
        return date.today() - timedelta(days=1)

    # Relative days: 30d, 90d
    match_d = re.match(r"^(\d+)\s*(?:d|days?)$", cleaned)
    if match_d:
        days = int(match_d.group(1))
        return date.today() - timedelta(days=days)

    # Relative weeks: 2w, 4w
    match_w = re.match(r"^(\d+)\s*(?:w|weeks?)$", cleaned)
    if match_w:
        weeks = int(match_w.group(1))
        return date.today() - timedelta(days=weeks * 7)

    # Relative months: 1m, 6m (approx 30 days/month)
    match_m = re.match(r"^(\d+)\s*(?:m|months?)$", cleaned)
    if match_m:
        months = int(match_m.group(1))
        return date.today() - timedelta(days=int(months * 30.4375))

    # Relative years: 1y
    match_y = re.match(r"^(\d+)\s*(?:y|years?)$", cleaned)
    if match_y:
        years = int(match_y.group(1))
        return date.today() - timedelta(days=years * 365)

    # Standard ISO format: YYYY-MM-DD
    try:
        return datetime.strptime(cleaned, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(
            f"Cannot parse date '{input_str}'.\n"
            f"Supported formats: 'YYYY-MM-DD', '30d', '90d', '6m', '1y', 'today', 'yesterday'."
        ) from e


def resolve_date_range(from_expr: str, to_expr: str | None = None) -> tuple[date, date]:
    """Resolve a pair of expressions into a validated (start_date, end_date) range.

    If to_expr is omitted and from_expr is a relative duration (e.g. '30d', '6m'):
    treats from_expr as a lookback duration ending today.
    """
    to_date = parse_date_or_relative(to_expr) if to_expr else date.today()

    from_cleaned = from_expr.strip().lower()
    # Check if from_expr is a lookback token like '30d' or '6m'
    if re.match(r"^\d+\s*(?:d|days?|w|weeks?|m|months?|y|years?)$", from_cleaned) and not to_expr:
        start_date = parse_date_or_relative(from_cleaned)
        end_date = date.today()
    else:
        start_date = parse_date_or_relative(from_expr)
        end_date = to_date

    if start_date > end_date:
        raise ValueError(f"Start date ({start_date}) cannot be after end date ({end_date}).")

    return start_date, end_date
