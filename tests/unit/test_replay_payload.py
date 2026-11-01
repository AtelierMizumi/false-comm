"""Unit tests for the replay plan JSON payload builder."""

from false_comm.cli.replay_cmd import build_replay_plan_payload
from false_comm.replay.analyzer import CommitDiffAnalysis, SemanticPhase
from false_comm.replay.repartitioner import ReplayStep


def _analysis(commit_sha: str = "abc1234") -> CommitDiffAnalysis:
    return CommitDiffAnalysis(
        commit_sha=commit_sha,
        original_message="feat: add auth",
        total_files=2,
        total_added=20,
        total_deleted=3,
        files_by_phase={phase: [] for phase in SemanticPhase},
    )


def test_build_replay_plan_payload_matches_schema() -> None:
    steps = [
        ReplayStep(
            step_index=1,
            phase=SemanticPhase.INTERFACE_SCHEMA,
            message="feat(models): define schemas",
            files=["models/user.py"],
        ),
        ReplayStep(
            step_index=2,
            phase=SemanticPhase.TESTS,
            message="test(auth): add tests",
            files=["tests/test_auth.py", "tests/conftest.py"],
        ),
    ]

    payload = build_replay_plan_payload(
        commit_ref="abc1234",
        analysis=_analysis(),
        steps=steps,
        span_days=5,
    )

    assert payload == {
        "commit": "abc1234",
        "original_message": "feat: add auth",
        "span_days": 5,
        "total_files": 2,
        "total_steps": 2,
        "steps": [
            {
                "step_index": 1,
                "phase": "interface_schema",
                "message": "feat(models): define schemas",
                "files": ["models/user.py"],
            },
            {
                "step_index": 2,
                "phase": "tests",
                "message": "test(auth): add tests",
                "files": ["tests/test_auth.py", "tests/conftest.py"],
            },
        ],
    }


def test_build_replay_plan_payload_handles_zero_steps() -> None:
    payload = build_replay_plan_payload(
        commit_ref="HEAD",
        analysis=_analysis("HEAD"),
        steps=[],
        span_days=7,
    )

    assert payload["total_steps"] == 0
    assert payload["steps"] == []
