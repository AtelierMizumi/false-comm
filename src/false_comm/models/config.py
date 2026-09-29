"""Domain models and data schemas for false-comm."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class DayOfWeek(StrEnum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class CommitAction(StrEnum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


class MessageStyle(StrEnum):
    CONVENTIONAL = "conventional"  # feat(scope): message
    FREEFORM = "freeform"  # Fix edge case in parser
    MIXED = "mixed"


class TimeWindow(BaseModel):
    """Working hours slot with activity probability weighting."""

    name: str = "core_hours"
    start_hour: int = Field(ge=0, le=23, default=9)
    end_hour: int = Field(ge=0, le=23, default=18)
    probability: float = Field(ge=0.0, le=1.0, default=0.85)
    peak_hour: int = Field(ge=0, le=23, default=14)


class DateRange(BaseModel):
    """Start and end dates for backfill / replay."""

    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        if self.start_date > self.end_date:
            raise ValueError(
                f"start_date ({self.start_date}) must be <= end_date ({self.end_date})"
            )
        return self


class BehaviorProfile(BaseModel):
    """Statistical behavioral profile mimicking a human developer."""

    name: str = "standard"
    description: str = "Typical professional developer with 9-5 work hours and weekend rest"

    # Negative Binomial parameters for daily commit count
    # r (dispersion) and p (success prob). Mean = r*(1-p)/p
    dispersion_r: float = Field(gt=0, default=2.5)
    prob_p: float = Field(gt=0, lt=1, default=0.45)

    # Active day probability (chance of at least 1 commit on a given working day)
    weekday_active_prob: float = Field(ge=0.0, le=1.0, default=0.85)
    weekend_active_prob: float = Field(ge=0.0, le=1.0, default=0.15)

    # Day-of-week relative activity weights (Monday=0 ... Sunday=6)
    weekday_weights: list[float] = Field(
        default=[1.0, 1.15, 1.2, 1.1, 0.9, 0.2, 0.15],
        description="Weights for Mon, Tue, Wed, Thu, Fri, Sat, Sun",
    )

    # Working hours distribution
    time_windows: list[TimeWindow] = Field(
        default_factory=lambda: [
            TimeWindow(name="morning", start_hour=9, end_hour=12, probability=0.35, peak_hour=10),
            TimeWindow(
                name="afternoon", start_hour=13, end_hour=18, probability=0.55, peak_hour=15
            ),
            TimeWindow(name="evening", start_hour=19, end_hour=22, probability=0.10, peak_hour=20),
        ]
    )

    # Lunch dip: commit probability drops sharply between 12:00 and 13:00
    lunch_dip_start: int = 12
    lunch_dip_end: int = 13
    lunch_suppression_factor: float = Field(ge=0.0, le=1.0, default=0.10)

    # Bursts / streaks: multiple commits within 5-45 minutes (bug fixing, quick review iterations)
    burst_probability: float = Field(ge=0.0, le=1.0, default=0.35)
    burst_min_commits: int = 2
    burst_max_commits: int = 5
    burst_gap_minutes_min: int = 4
    burst_gap_minutes_max: int = 35

    # Vacation / quiet periods (number of vacation weeks per year)
    vacation_weeks_per_year: int = Field(ge=0, le=10, default=3)

    # Holiday calendar region (e.g. "VN", "US", "GLOBAL", "NONE")
    holiday_region: str = "GLOBAL"

    # Commit message styling
    message_style: MessageStyle = MessageStyle.CONVENTIONAL
    multiline_message_prob: float = Field(ge=0.0, le=1.0, default=0.25)

    # Branch & Merge simulation
    branch_simulation_enabled: bool = True
    branch_ratio: float = Field(
        ge=0.0, le=1.0, default=0.20, description="Fraction of commits on feature branches"
    )
    merge_commit_enabled: bool = True


class GitIdentity(BaseModel):
    """Git author and committer identity extracted or specified."""

    name: str
    email: str
    timezone: str = "+0700"
    gpg_sign: bool = False
    signing_key: str | None = None


class RepositoryRules(BaseModel):
    """Safety and boundary rules for a target repository."""

    protected_branches: list[str] = Field(default_factory=lambda: ["production", "release"])
    target_branch: str = "main"
    allowed_extensions: list[str] = Field(
        default_factory=lambda: [
            ".py",
            ".md",
            ".json",
            ".yaml",
            ".yml",
            ".txt",
            ".ts",
            ".js",
            ".sh",
        ]
    )
    max_files_per_commit: int = 4
    max_lines_per_file: int = 25
    stealth_content_dir: str = ".github/workflows/helpers"
    modify_existing_files: bool = True
