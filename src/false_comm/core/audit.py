"""Stealth & Authenticity Audit Engine analyzing git history for bot fingerprints."""

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from false_comm.git.adapter import GitAdapter


@dataclass
class AuditFinding:
    severity: str  # "info", "warning", "critical"
    title: str
    detail: str


@dataclass
class AuditResult:
    total_commits: int
    score: int  # 0 to 100
    rating_label: str
    round_seconds_pct: float
    round_minutes_pct: float
    empty_commits_count: int
    identical_intervals_pct: float
    night_commits_pct: float
    weekend_commits_pct: float
    findings: list[AuditFinding] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class AuditEngine:
    """Analyzes git commit history against statistical bot detection heuristics."""

    def __init__(self, git_adapter: GitAdapter) -> None:
        self.adapter = git_adapter

    def audit(
        self,
        max_commits: int = 500,
        author_filter: str | None = None,
    ) -> AuditResult:
        """Audit up to max_commits from current branch."""
        cmd = ["log", "--format=%H|%an|%ae|%aI|%s", f"-n{max_commits}"]
        if author_filter:
            cmd.append(f"--author={author_filter}")

        res = self.adapter.run_git(cmd, check=False)
        if res.returncode != 0 or not res.stdout.strip():
            return AuditResult(
                total_commits=0,
                score=100,
                rating_label="N/A (No commits found)",
                round_seconds_pct=0.0,
                round_minutes_pct=0.0,
                empty_commits_count=0,
                identical_intervals_pct=0.0,
                night_commits_pct=0.0,
                weekend_commits_pct=0.0,
                findings=[
                    AuditFinding(
                        severity="info",
                        title="Repository Empty",
                        detail="No commits found on current branch to audit.",
                    )
                ],
                recommendations=[
                    "Run 'false-comm backfill' to generate your initial realistic commit history."
                ],
            )

        lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
        total_commits = len(lines)

        timestamps: list[datetime] = []
        commit_shas: list[str] = []

        for line in lines:
            parts = line.split("|", 4)
            if len(parts) >= 4:
                sha, _, _, iso_ts = parts[0], parts[1], parts[2], parts[3]
                commit_shas.append(sha)
                try:
                    dt = datetime.fromisoformat(iso_ts)
                    timestamps.append(dt)
                except ValueError:
                    pass

        valid_count = len(timestamps)
        if valid_count == 0:
            return AuditResult(
                total_commits=total_commits,
                score=50,
                rating_label="Unknown",
                round_seconds_pct=0.0,
                round_minutes_pct=0.0,
                empty_commits_count=0,
                identical_intervals_pct=0.0,
                night_commits_pct=0.0,
                weekend_commits_pct=0.0,
            )

        # 1. Round seconds (:00)
        round_sec_count = sum(1 for dt in timestamps if dt.second == 0)
        round_sec_pct = (round_sec_count / valid_count) * 100.0

        # 2. Round minutes (:00, :15, :30, :45)
        round_min_count = sum(1 for dt in timestamps if dt.minute in (0, 15, 30, 45))
        round_min_pct = (round_min_count / valid_count) * 100.0

        # 3. Intervals between consecutive commits in chronological order
        sorted_ts = sorted(timestamps)
        intervals: list[int] = []
        for i in range(1, len(sorted_ts)):
            delta_sec = int((sorted_ts[i] - sorted_ts[i - 1]).total_seconds())
            if 0 < delta_sec <= 86400:  # within 24h
                intervals.append(delta_sec)

        identical_intervals_pct = 0.0
        if intervals:
            interval_counts = Counter(intervals)
            most_common_val, most_common_count = interval_counts.most_common(1)[0]
            if most_common_count > 2:
                identical_intervals_pct = (most_common_count / len(intervals)) * 100.0

        # 4. Night commits (01:00 - 05:00)
        night_count = sum(1 for dt in timestamps if 1 <= dt.hour <= 5)
        night_pct = (night_count / valid_count) * 100.0

        # 5. Weekend commits (Saturday=5, Sunday=6)
        weekend_count = sum(1 for dt in timestamps if dt.weekday() in (5, 6))
        weekend_pct = (weekend_count / valid_count) * 100.0

        # 6. Check for empty commits
        empty_res = self.adapter.run_git(
            ["log", "--shortstat", f"-n{min(max_commits, 200)}"], check=False
        )
        empty_count = 0
        if empty_res.returncode == 0:
            commit_blocks = re.split(r"\n(?=commit [0-9a-f]{40})", empty_res.stdout)
            for block in commit_blocks:
                if block.strip() and not re.search(r"\d+ files? changed", block):
                    # Check if it's a merge commit (merges often don't have shortstat by default)
                    if "Merge:" not in block:
                        empty_count += 1

        # Calculate Authenticity Score (Start at 100, deduct penalties)
        score = 100
        findings: list[AuditFinding] = []
        recommendations: list[str] = []

        # Round seconds penalty (normal chance ~1.7%)
        if round_sec_pct > 60:
            score -= 30
            findings.append(
                AuditFinding(
                    severity="critical",
                    title="Robotic Round Seconds Detected",
                    detail=f"{round_sec_pct:.1f}% of commits were created at exact :00 seconds.",
                )
            )
            recommendations.append(
                "Avoid scripts that commit on exact clock boundaries. false-comm applies natural second jitter."
            )
        elif round_sec_pct > 25:
            score -= 15
            findings.append(
                AuditFinding(
                    severity="warning",
                    title="Elevated Round Seconds",
                    detail=f"{round_sec_pct:.1f}% of commits have :00 seconds (higher than typical human 1-5%).",
                )
            )

        # Round minutes penalty (normal chance ~6.7%)
        if round_min_pct > 50:
            score -= 20
            findings.append(
                AuditFinding(
                    severity="critical",
                    title="Clock-Clustered Minutes",
                    detail=f"{round_min_pct:.1f}% of commits are at :00, :15, :30, or :45 minutes.",
                )
            )
        elif round_min_pct > 30:
            score -= 10
            findings.append(
                AuditFinding(
                    severity="warning",
                    title="Elevated Quarter-Hour Minutes",
                    detail=f"{round_min_pct:.1f}% of commits occur at exact quarter hours.",
                )
            )

        # Identical intervals penalty
        if identical_intervals_pct > 40:
            score -= 25
            findings.append(
                AuditFinding(
                    severity="critical",
                    title="Constant Time Interval Fingerprint",
                    detail=f"{identical_intervals_pct:.1f}% of consecutive commits share identical intervals.",
                )
            )
            recommendations.append(
                "Use negative binomial / gamma-poisson inter-arrival times provided by false-comm."
            )
        elif identical_intervals_pct > 20:
            score -= 10
            findings.append(
                AuditFinding(
                    severity="warning",
                    title="Suspicious Interval Regularity",
                    detail=f"{identical_intervals_pct:.1f}% of intervals are identical.",
                )
            )

        # Empty commits penalty
        if empty_count > 0:
            score -= min(30, empty_count * 5)
            findings.append(
                AuditFinding(
                    severity="critical",
                    title=f"Empty Commits Detected ({empty_count})",
                    detail="Commits with zero changed files (--allow-empty) are immediate bot red flags.",
                )
            )
            recommendations.append(
                "Never use '--allow-empty'. false-comm produces real semantic documentation & code diffs."
            )

        # Extreme night ratio penalty (> 40% between 1 AM and 5 AM)
        if night_pct > 40:
            score -= 10
            findings.append(
                AuditFinding(
                    severity="warning",
                    title="Abnormal Night Activity",
                    detail=f"{night_pct:.1f}% of commits occurred between 1:00 AM and 5:00 AM.",
                )
            )
            recommendations.append(
                "Align commit timestamps with your local business hours via false-comm's --timezone."
            )

        score = max(0, min(100, score))

        if score >= 90:
            label = "A+ (Undetectable & Organic)"
        elif score >= 80:
            label = "A (High Authenticity)"
        elif score >= 65:
            label = "B (Moderate - Minor Anomaly)"
        elif score >= 45:
            label = "C (Suspicious Bot Patterns)"
        else:
            label = "F (Blatant Script Signature)"

        if not findings:
            findings.append(
                AuditFinding(
                    severity="info",
                    title="Healthy Developer Patterns",
                    detail="No obvious robotic commit signatures or artificial fingerprints found.",
                )
            )

        if not recommendations:
            recommendations.append(
                "Your history looks authentic! Keep using false-comm profiles to maintain organic distribution."
            )

        return AuditResult(
            total_commits=valid_count,
            score=score,
            rating_label=label,
            round_seconds_pct=round_sec_pct,
            round_minutes_pct=round_min_pct,
            empty_commits_count=empty_count,
            identical_intervals_pct=identical_intervals_pct,
            night_commits_pct=night_pct,
            weekend_commits_pct=weekend_pct,
            findings=findings,
            recommendations=recommendations,
        )
