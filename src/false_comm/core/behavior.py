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
    ) -> None:
        self.profile = profile
        self.holiday_calendar = holiday_calendar or HolidayCalendar(region=profile.holiday_region)
        self.rng = random.Random(seed)

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
        vacations = self._generate_vacation_dates(date_range)
        results: list[DayCommitSpec] = []

        curr_date = date_range.start_date
        while curr_date <= date_range.end_date:
            weekday = curr_date.weekday()  # Mon=0, Sun=6
            is_weekend = weekday >= 5
            is_holiday = self.holiday_calendar.is_holiday(curr_date)
            is_vacation = curr_date in vacations

            # Determine if this day has activity
            if is_vacation:
                # 95% zero commits during vacation, 5% solitary quick commit
                is_active = self.rng.random() < 0.05
            elif is_holiday:
                # Holidays typically suppress commits
                is_active = self.rng.random() < 0.04
            elif is_weekend:
                is_active = self.rng.random() < self.profile.weekend_active_prob
            else:
                is_active = self.rng.random() < self.profile.weekday_active_prob

            if not is_active:
                results.append(
                    DayCommitSpec(
                        target_date=curr_date, commit_count=0, is_burst_day=False, burst_groups=[]
                    )
                )
                curr_date += timedelta(days=1)
                continue

            # Scale dispersion / mean by weekday weight
            weight = (
                self.profile.weekday_weights[weekday]
                if weekday < len(self.profile.weekday_weights)
                else 1.0
            )
            if is_weekend:
                weight *= 0.5

            # Sample commit count from Negative Binomial with adjusted parameter
            adjusted_r = max(0.5, self.profile.dispersion_r * weight)
            raw_count = _sample_negative_binomial(adjusted_r, self.profile.prob_p, self.rng)
            # Since is_active is True, day must have at least 1 commit
            commit_count = max(1, raw_count)

            # Cap unreasonable spikes based on profile
            max_daily = 18 if not is_weekend else 6
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

        return results
