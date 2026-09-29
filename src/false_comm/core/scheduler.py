"""Timestamp generation and intra-day scheduling with natural human jitter."""

import random
from datetime import datetime, time, timedelta

from false_comm.core.behavior import DayCommitSpec
from false_comm.models.config import BehaviorProfile, TimeWindow


class ScheduleEngine:
    """Assigns realistic, non-round intra-day timestamps to planned commits."""

    def __init__(
        self, profile: BehaviorProfile, timezone_str: str = "+0700", seed: int | None = None
    ) -> None:
        self.profile = profile
        self.timezone_str = timezone_str
        self.rng = random.Random(seed)

    def _pick_active_window(self) -> TimeWindow:
        """Select a time window based on configured probabilities."""
        windows = self.profile.time_windows
        if not windows:
            return TimeWindow(
                name="default", start_hour=9, end_hour=18, probability=1.0, peak_hour=14
            )

        weights = [w.probability for w in windows]
        total_w = sum(weights)
        if total_w <= 0:
            return windows[0]

        normalized = [w / total_w for w in weights]
        r = self.rng.random()
        cumulative = 0.0
        for window, prob in zip(windows, normalized, strict=False):
            cumulative += prob
            if r <= cumulative:
                return window
        return windows[-1]

    def _sample_minute_second(self) -> tuple[int, int]:
        """Sample natural non-round minute and second."""
        minute = self.rng.randint(0, 59)
        # Avoid clustering on exact quarter hours (:00, :15, :30, :45)
        if minute in {0, 15, 30, 45} and self.rng.random() < 0.70:
            minute = (minute + self.rng.choice([-2, -1, 1, 2, 3])) % 60

        second = self.rng.randint(0, 59)
        if second in {0, 30} and self.rng.random() < 0.80:
            second = (second + self.rng.choice([-5, -3, 3, 7, 11])) % 60

        return minute, second

    def _sample_time_in_window(self, window: TimeWindow) -> time:
        """Sample a time within the window using triangular or normal distribution around peak."""
        # Hour sampled with preference around peak_hour
        mode_hour = float(window.peak_hour)
        low_hour = float(window.start_hour)
        high_hour = float(window.end_hour)

        # Triangular distribution gives natural bell-like shape around peak
        raw_hour = self.rng.triangular(low_hour, high_hour, mode_hour)
        hour = int(raw_hour)
        hour = max(window.start_hour, min(window.end_hour, hour))

        # Check lunch dip
        if self.profile.lunch_dip_start <= hour < self.profile.lunch_dip_end:
            if self.rng.random() > self.profile.lunch_suppression_factor:
                # Shift out of lunch window into early afternoon or late morning
                if self.rng.random() < 0.6:
                    hour = self.profile.lunch_dip_end + self.rng.randint(0, 1)
                else:
                    hour = self.profile.lunch_dip_start - 1

        minute, second = self._sample_minute_second()
        return time(hour=hour % 24, minute=minute, second=second)

    def schedule_day(self, day_spec: DayCommitSpec) -> list[datetime]:
        """Generate strictly sorted, realistic timestamps for all commits in a single day."""
        count = day_spec.commit_count
        if count <= 0:
            return []

        target_date = day_spec.target_date
        burst_indices: set[int] = set()
        for group in day_spec.burst_groups:
            burst_indices.update(group)

        # Allocate slot for each commit
        candidate_datetimes: list[datetime | None] = [None] * count

        # 1. Schedule burst clusters first
        for group in day_spec.burst_groups:
            if not group:
                continue
            window = self._pick_active_window()
            base_time = self._sample_time_in_window(window)
            anchor_dt = datetime.combine(target_date, base_time)

            curr_dt = anchor_dt
            for idx in group:
                candidate_datetimes[idx] = curr_dt
                gap_minutes = self.rng.randint(
                    self.profile.burst_gap_minutes_min,
                    self.profile.burst_gap_minutes_max,
                )
                gap_seconds = self.rng.randint(10, 55)
                curr_dt = curr_dt + timedelta(minutes=gap_minutes, seconds=gap_seconds)

        # 2. Schedule remaining standalone commits
        for i in range(count):
            if candidate_datetimes[i] is not None:
                continue
            window = self._pick_active_window()
            sampled_time = self._sample_time_in_window(window)
            candidate_datetimes[i] = datetime.combine(target_date, sampled_time)

        # 3. Resolve all None (type check) and sort chronologically
        valid_datetimes = [dt for dt in candidate_datetimes if dt is not None]
        valid_datetimes.sort()

        # 4. Guarantee minimum temporal separation (at least 90s between consecutive commits)
        adjusted: list[datetime] = []
        for i, dt in enumerate(valid_datetimes):
            if i == 0:
                adjusted.append(dt)
            else:
                prev = adjusted[-1]
                if dt <= prev:
                    # Bump forward by 90-300 seconds
                    min_separation = self.rng.randint(90, 300)
                    dt = prev + timedelta(seconds=min_separation)
                elif (dt - prev).total_seconds() < 90:
                    dt = prev + timedelta(seconds=self.rng.randint(90, 180))

                # Cap at 23:59:50 of same day
                max_dt = datetime.combine(target_date, time(23, 59, 50))
                if dt > max_dt:
                    dt = max_dt
                adjusted.append(dt)

        return adjusted
