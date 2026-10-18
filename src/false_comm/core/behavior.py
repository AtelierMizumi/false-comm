"""Statistical behavior synthesizer modeling human commit distributions."""

import math
import random
from datetime import date, timedelta
from typing import NamedTuple

from false_comm.core.holidays import HolidayCalendar
from false_comm.models.config import BehaviorProfile, DateRange


class DayCommitSpec(NamedTuple):
    """Specification of commit count and burst clusters for a single date."""

    target_date: date
    commit_count: int
    is_burst_day: bool
    burst_groups: list[list[int]]  # Indices of commits that belong to bursts


def _sample_poisson(lam: float, rng: random.Random) -> int:
    """Sample from Poisson distribution using Knuth's algorithm or Gaussian approximation."""
    if lam <= 0:
        return 0
    if lam < 30.0:
        # Knuth's algorithm
        l_val = math.exp(-lam)
        k = 0
        p = 1.0
        while p > l_val:
            k += 1
            p *= rng.random()
        return k - 1
    # Gaussian approximation for large lambda
    val = rng.gauss(lam, math.sqrt(lam))
    return max(0, int(round(val)))


def _sample_negative_binomial(r: float, p: float, rng: random.Random) -> int:
    """Sample from Negative Binomial(r, p) using Gamma-Poisson mixture.

    r: number of successes (dispersion parameter > 0)
    p: probability of success (0 < p < 1)
    Mean = r * (1 - p) / p
    """
    scale = (1.0 - p) / p
    # Gamma distribution with shape r and scale (1-p)/p
    lam = rng.gammavariate(r, scale)
    return _sample_poisson(lam, rng)


class BehaviorEngine:
    """Generates realistic day-by-day commit allocations based on behavioral profiles."""

    def __init__(
        self,
        profile: BehaviorProfile,
        holiday_calendar: HolidayCalendar | None = None,
        seed: int | None = None,
        intensity: float = 1.0,
        no_vacation: bool = False,
        fill_gaps: bool = False,
        existing_commits: dict[date, int] | None = None,
    ) -> None:
        self.profile = profile
        self.holiday_calendar = holiday_calendar or HolidayCalendar(region=profile.holiday_region)
        self.rng = random.Random(seed)
        self.intensity = max(0.1, float(intensity))
        self.no_vacation = no_vacation or (profile.vacation_weeks_per_year <= 0)
        self.fill_gaps = fill_gaps
        self.existing_commits = existing_commits or {}

    def _generate_vacation_dates(self, date_range: DateRange) -> set[date]:
        """Generate contiguous 7-day vacation blocks throughout each year in range."""
        vacation_dates: set[date] = set()
        if self.profile.vacation_weeks_per_year <= 0:
            return vacation_dates

        # Group dates by year
        start_year = date_range.start_date.year
        end_year = date_range.end_date.year

        for year in range(start_year, end_year + 1):
            year_start = max(date_range.start_date, date(year, 1, 1))
            year_end = min(date_range.end_date, date(year, 12, 31))
            total_days = (year_end - year_start).days

            if total_days < 14:
                continue

            weeks_to_pick = min(self.profile.vacation_weeks_per_year, max(1, total_days // 60))
            for _ in range(weeks_to_pick):
                # Pick a random Monday or start day
                offset = self.rng.randint(0, max(0, total_days - 7))
                block_start = year_start + timedelta(days=offset)
                for d in range(7):
                    vacation_day = block_start + timedelta(days=d)
                    if vacation_day <= year_end:
                        vacation_dates.add(vacation_day)

        return vacation_dates

    def plan_daily_commits(self, date_range: DateRange) -> list[DayCommitSpec]:
        """Compute commit count and burst structure for every day in date_range."""
        vacations = set() if self.no_vacation else self._generate_vacation_dates(date_range)
        results: list[DayCommitSpec] = []

        total_days = max(1, (date_range.end_date - date_range.start_date).days + 1)
        curr_date = date_range.start_date
        day_index = 0

        while curr_date <= date_range.end_date:
            existing_count = self.existing_commits.get(curr_date, 0)

            # In gap-filling mode: if day already has 3+ commits, preserve existing work without adding clutter
            if self.fill_gaps and existing_count >= 3:
                results.append(
                    DayCommitSpec(
                        target_date=curr_date, commit_count=0, is_burst_day=False, burst_groups=[]
                    )
                )
                curr_date += timedelta(days=1)
                day_index += 1
                continue

            weekday = curr_date.weekday()  # Mon=0, Sun=6
            is_weekend = weekday >= 5
            is_holiday = self.holiday_calendar.is_holiday(curr_date)
            is_vacation = curr_date in vacations

            # Organic ramp-up curve for post-hiatus / comeback profile
            if self.profile.name == "comeback":
                warmup_days = max(3, min(14, int(total_days * 0.25)))
                ramp = 0.55 + 0.45 * min(1.0, day_index / max(1, warmup_days))
            else:
                ramp = 1.0

            # Determine if this day has activity
            base_prob = (
                self.profile.weekend_active_prob if is_weekend else self.profile.weekday_active_prob
            )
            if self.intensity != 1.0 or ramp != 1.0:
                adjusted_prob = min(
                    0.98, max(0.05, base_prob * (0.8 + 0.2 * self.intensity) * ramp)
                )
            else:
                adjusted_prob = base_prob

            if is_vacation:
                # 95% zero commits during vacation, 5% solitary quick commit
                is_active = self.rng.random() < 0.05
            elif is_holiday:
                # Holidays typically suppress commits
                is_active = self.rng.random() < 0.04
            else:
                is_active = self.rng.random() < adjusted_prob

            if not is_active:
                results.append(
                    DayCommitSpec(
                        target_date=curr_date, commit_count=0, is_burst_day=False, burst_groups=[]
                    )
                )
                curr_date += timedelta(days=1)
                day_index += 1
                continue

            # Scale dispersion / mean by weekday weight, intensity, and ramp
            weight = (
                self.profile.weekday_weights[weekday]
                if weekday < len(self.profile.weekday_weights)
                else 1.0
            )
            if is_weekend:
                weight *= 0.5

            # Sample commit count from Negative Binomial with adjusted parameter
            adjusted_r = max(0.4, self.profile.dispersion_r * weight * self.intensity * ramp)
            raw_count = _sample_negative_binomial(adjusted_r, self.profile.prob_p, self.rng)
            commit_count = max(1, raw_count)

            # In gap-filling mode, if day already had 1-2 commits, top up gently
            if self.fill_gaps and existing_count > 0:
                target_total = max(existing_count + 1, min(commit_count + existing_count, 4))
                commit_count = max(0, target_total - existing_count)
                if commit_count == 0:
                    results.append(
                        DayCommitSpec(
                            target_date=curr_date,
                            commit_count=0,
                            is_burst_day=False,
                            burst_groups=[],
                        )
                    )
                    curr_date += timedelta(days=1)
                    day_index += 1
                    continue

            # Cap unreasonable spikes based on profile and intensity
            max_daily = int(18 * self.intensity) if not is_weekend else int(6 * self.intensity)
            commit_count = min(commit_count, max_daily)

            # Check for bursts (rapid succession of commits)
            is_burst = False
            burst_groups: list[list[int]] = []
            if commit_count >= self.profile.burst_min_commits:
                if self.rng.random() < self.profile.burst_probability:
                    is_burst = True
                    # Decide burst size (e.g. 2 to min(commit_count, burst_max_commits))
                    burst_size = self.rng.randint(
                        self.profile.burst_min_commits,
                        min(commit_count, self.profile.burst_max_commits),
                    )
                    # Pick consecutive indices for the burst
                    start_idx = self.rng.randint(0, commit_count - burst_size)
                    burst_group = list(range(start_idx, start_idx + burst_size))
                    burst_groups.append(burst_group)

            results.append(
                DayCommitSpec(
                    target_date=curr_date,
                    commit_count=commit_count,
                    is_burst_day=is_burst,
                    burst_groups=burst_groups,
                )
            )
            curr_date += timedelta(days=1)
            day_index += 1

        return results
