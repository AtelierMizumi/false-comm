"""Multi-country holiday calendar support for suppressing unnatural commit activity."""

from datetime import date
from typing import ClassVar


class HolidayCalendar:
    """Detects national and international holidays."""

    # Fixed global holidays (Month, Day)
    GLOBAL_FIXED_HOLIDAYS: ClassVar[set[tuple[int, int]]] = {
        (1, 1),  # New Year's Day
        (5, 1),  # International Workers' Day
        (12, 24),  # Christmas Eve
        (12, 25),  # Christmas Day
        (12, 31),  # New Year's Eve
    }

    # Vietnam solar & precalculated lunar holidays (Tet & Hung Kings) for 2022-2030
    VN_FIXED_SOLAR: ClassVar[set[tuple[int, int]]] = {
        (1, 1),  # New Year
        (4, 30),  # Reunification Day
        (5, 1),  # Labor Day
        (9, 2),  # National Day
        (9, 3),  # National Day observed
    }

    # Range of dates for Lunar New Year (Tet) and Hung Kings in Vietnam
    VN_LUNAR_RANGES: ClassVar[list[tuple[date, date]]] = [
        # 2022
        (date(2022, 1, 29), date(2022, 2, 6)),  # Tet Nham Dan
        (date(2022, 4, 10), date(2022, 4, 11)),  # Hung Kings
        # 2023
        (date(2023, 1, 20), date(2023, 1, 26)),  # Tet Quy Mao
        (date(2023, 4, 29), date(2023, 5, 3)),  # Hung Kings + 30/4 + 1/5
        # 2024
        (date(2024, 2, 8), date(2024, 2, 14)),  # Tet Giap Thin
        (date(2024, 4, 18), date(2024, 4, 18)),  # Hung Kings
        # 2025
        (date(2025, 1, 25), date(2025, 2, 2)),  # Tet At Ty
        (date(2025, 4, 7), date(2025, 4, 7)),  # Hung Kings
        # 2026
        (date(2026, 2, 15), date(2026, 2, 22)),  # Tet Binh Ngo
        (date(2026, 4, 26), date(2026, 4, 26)),  # Hung Kings
        # 2027
        (date(2027, 2, 5), date(2027, 2, 11)),  # Tet Dinh Mui
        (date(2027, 4, 16), date(2027, 4, 16)),  # Hung Kings
        # 2028
        (date(2028, 1, 25), date(2028, 1, 31)),  # Tet Mau Than
        (date(2028, 4, 4), date(2028, 4, 4)),  # Hung Kings
        # 2029
        (date(2029, 2, 12), date(2029, 2, 18)),  # Tet Ky Dau
        (date(2029, 4, 22), date(2029, 4, 22)),  # Hung Kings
        # 2030
        (date(2030, 2, 2), date(2030, 2, 8)),  # Tet Canh Tuat
        (date(2030, 4, 11), date(2030, 4, 11)),  # Hung Kings
    ]

    # US Federal fixed holidays
    US_FIXED_HOLIDAYS: ClassVar[set[tuple[int, int]]] = {
        (1, 1),  # New Year
        (6, 19),  # Juneteenth
        (7, 4),  # Independence Day
        (11, 11),  # Veterans Day
        (12, 25),  # Christmas
    }

    def __init__(self, region: str = "GLOBAL", custom_holidays: set[date] | None = None) -> None:
        self.region = region.upper()
        self.custom_holidays = custom_holidays or set()

    def is_holiday(self, check_date: date) -> bool:
        """Return True if check_date is considered a holiday under the active region."""
        if check_date in self.custom_holidays:
            return True

        if self.region == "NONE":
            return False

        month_day = (check_date.month, check_date.day)

        # Global base holidays
        if month_day in self.GLOBAL_FIXED_HOLIDAYS:
            return True

        if self.region == "VN":
            if month_day in self.VN_FIXED_SOLAR:
                return True
            for start_d, end_d in self.VN_LUNAR_RANGES:
                if start_d <= check_date <= end_d:
                    return True

        elif self.region == "US":
            if month_day in self.US_FIXED_HOLIDAYS:
                return True
            # Thanksgiving: Fourth Thursday in November
            if check_date.month == 11 and check_date.weekday() == 3:
                # Is it the 4th Thursday?
                if 22 <= check_date.day <= 28:
                    return True

        return False
