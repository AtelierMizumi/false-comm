"""Unit tests for MessageGenerator."""

import re

from false_comm.content.messages import MessageGenerator
from false_comm.models.config import MessageStyle


def test_conventional_commit_message_format() -> None:
    gen = MessageGenerator(style=MessageStyle.CONVENTIONAL, seed=42)
    msg = gen.generate(allow_multiline=False)

    pattern = re.compile(r"^(feat|fix|refactor|docs|test|chore|perf)\([a-z0-9_-]+\): .+")
    assert pattern.match(msg) is not None


def test_multiline_commit_message() -> None:
    gen = MessageGenerator(style=MessageStyle.CONVENTIONAL, seed=1)
    # Generate multiple messages, at least one should have multiline details
    found_multiline = False
    for _ in range(20):
        m = gen.generate(allow_multiline=True)
        if "\n\n" in m and "-" in m:
            found_multiline = True
            break
    assert found_multiline
