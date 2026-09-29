"""Branch and merge simulator for realistic non-linear Git graphs."""

import random


class BranchSimEngine:
    """Plans realistic feature branches and merge commits."""

    BRANCH_PREFIXES = ["feat", "fix", "refactor", "chore", "docs", "perf"]
    BRANCH_TOPICS = [
        "auth-token-validation",
        "rate-limiting-middleware",
        "cache-invalidation-hook",
        "async-event-handler",
        "json-parser-optimization",
        "api-error-boundary",
        "metrics-collector",
        "retry-backoff-logic",
        "config-loader-cleanup",
        "database-pool-tuning",
        "session-timeout-check",
        "logging-formatter",
        "sanitize-user-input",
        "health-check-endpoint",
    ]

    def __init__(self, target_branch: str = "main", seed: int | None = None) -> None:
        self.target_branch = target_branch
        self.rng = random.Random(seed)
        self._pr_counter = 12

    def generate_branch_name(self) -> str:
        """Create a realistic branch name like 'feat/cache-invalidation-hook'."""
        prefix = self.rng.choice(self.BRANCH_PREFIXES)
        topic = self.rng.choice(self.BRANCH_TOPICS)
        suffix = self.rng.choice(["", f"-{self.rng.randint(2, 9)}", "-v2"])
        return f"{prefix}/{topic}{suffix}"

    def generate_merge_message(self, branch_name: str, target_branch: str = "main") -> str:
        """Create a GitHub/GitLab style merge commit message."""
        self._pr_counter += self.rng.randint(1, 3)
        patterns = [
            f"Merge pull request #{self._pr_counter} from {branch_name}",
            f"Merge branch '{branch_name}' into {target_branch}",
            f"Merge pull request #{self._pr_counter} from {branch_name}\n\n* {branch_name}: (resolves #{self._pr_counter})",
        ]
        return self.rng.choice(patterns)
