"""Realistic semantic Git commit message generator."""

import random
from typing import ClassVar

from false_comm.models.config import MessageStyle


class MessageGenerator:
    """Generates natural, human-like commit messages."""

    CONVENTIONAL_TYPES: ClassVar[list[tuple[str, float]]] = [
        ("feat", 0.28),
        ("fix", 0.32),
        ("refactor", 0.16),
        ("docs", 0.10),
        ("test", 0.08),
        ("chore", 0.04),
        ("perf", 0.02),
    ]

    DEFAULT_SCOPES: ClassVar[list[str]] = [
        "core",
        "cli",
        "api",
        "auth",
        "models",
        "config",
        "utils",
        "worker",
        "db",
        "cache",
        "events",
        "router",
    ]

    TEMPLATES_BY_TYPE: ClassVar[dict[str, list[str]]] = {
        "feat": [
            "add support for custom configuration profiles",
            "implement rate-limiting check on incoming requests",
            "support pagination for batch query results",
            "add health-check and readiness probes",
            "support asynchronous event dispatcher",
            "introduce caching layer for recurring lookups",
            "add fallback mechanism for network timeouts",
            "implement structured logging format",
            "allow passing custom headers in client adapter",
        ],
        "fix": [
            "resolve off-by-one error in date range calculation",
            "prevent race condition during token renewal",
            "handle null reference when payload is incomplete",
            "fix incorrect status code on validation failure",
            "escape special characters in query filter",
            "correct timezone offset parsing in date serializer",
            "prevent unexpected socket hangup on reconnect",
            "fix memory accumulation in background queue",
            "handle empty collection gracefully without raising",
        ],
        "refactor": [
            "extract reusable validator into helper module",
            "simplify nested conditional logic in dispatcher",
            "streamline error response formatting",
            "decouple session state from transport adapter",
            "consolidate duplicate serialization routines",
            "modernize type definitions across core interfaces",
            "restructure configuration loader for better modularity",
        ],
        "docs": [
            "update setup instructions and prerequisites in README",
            "document error response schema and status codes",
            "add troubleshooting notes for local environment",
            "clarify parameter constraints in configuration guide",
            "add usage examples for batch execution mode",
        ],
        "test": [
            "add unit tests for boundary date calculations",
            "expand test coverage for error handler",
            "add test cases for malformed input payloads",
            "verify behavior on connection timeout retry",
            "add integration test for rollback workflow",
        ],
        "chore": [
            "bump dependency versions",
            "clean up unused imports and obsolete comments",
            "update linting rules and formatting configs",
            "remove deprecated internal utility functions",
        ],
        "perf": [
            "optimize lookup table access in hot path",
            "reduce redundant memory allocations during parsing",
            "batch database query operations to reduce roundtrips",
        ],
    }

    MULTILINE_DETAILS: ClassVar[list[list[str]]] = [
        [
            "- Add boundary condition check before proceeding",
            "- Ensure clean cleanup on failure",
        ],
        [
            "- Reorganize module imports according to style guide",
            "- Update corresponding test assertions",
        ],
        [
            "- Guard against None / empty inputs",
            "- Add descriptive error message",
        ],
        [
            "- Improve execution speed and reduce allocations",
            "- Pass existing regression suite",
        ],
    ]

    FREEFORM_MESSAGES: ClassVar[list[str]] = [
        "Update documentation and usage instructions",
        "Fix edge case in date validation logic",
        "Clean up redundant imports and format files",
        "Refactor request handler for better readability",
        "Add unit tests for error conditions",
        "Handle unexpected response structure gracefully",
        "Minor adjustments to configuration parser",
        "Tweak retry parameters for resilience",
        "Improve logging readability during startup",
        "Fix typo in variable naming and docs",
    ]

    def __init__(
        self,
        style: MessageStyle = MessageStyle.CONVENTIONAL,
        scopes: list[str] | None = None,
        seed: int | None = None,
    ) -> None:
        self.style = style
        self.scopes = scopes or self.DEFAULT_SCOPES
        self.rng = random.Random(seed)

    def _pick_conventional_type(self) -> str:
        types, weights = zip(*self.CONVENTIONAL_TYPES, strict=False)
        return self.rng.choices(types, weights=weights, k=1)[0]

    def generate(self, allow_multiline: bool = True) -> str:
        """Generate a realistic commit message."""
        use_conventional = self.style == MessageStyle.CONVENTIONAL or (
            self.style == MessageStyle.MIXED and self.rng.random() < 0.80
        )

        if not use_conventional:
            msg = self.rng.choice(self.FREEFORM_MESSAGES)
            if allow_multiline and self.rng.random() < 0.20:
                bullets = self.rng.choice(self.MULTILINE_DETAILS)
                return f"{msg}\n\n" + "\n".join(bullets)
            return msg

        c_type = self._pick_conventional_type()
        scope = self.rng.choice(self.scopes)
        templates = self.TEMPLATES_BY_TYPE.get(c_type, self.TEMPLATES_BY_TYPE["feat"])
        summary = self.rng.choice(templates)

        header = f"{c_type}({scope}): {summary}"

        if allow_multiline and self.rng.random() < 0.25:
            bullets = self.rng.choice(self.MULTILINE_DETAILS)
            return f"{header}\n\n" + "\n".join(bullets)

        return header
