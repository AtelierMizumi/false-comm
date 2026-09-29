"""Unit tests for Stealth & Authenticity Audit Engine."""

import subprocess
from pathlib import Path

from false_comm.core.audit import AuditEngine
from false_comm.git.adapter import GitAdapter


def test_audit_empty_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    adapter = GitAdapter(tmp_path)
    engine = AuditEngine(adapter)
    result = engine.audit()

    assert result.total_commits == 0
    assert result.score == 100
    assert "No commits found" in result.rating_label


def test_audit_realistic_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    adapter = GitAdapter(tmp_path)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Tester"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "tester@example.com"], check=True
    )

    # Create several commits with realistic non-round seconds and varying times
    timestamps = [
        "2024-03-10T10:14:27+00:00",
        "2024-03-11T14:22:51+00:00",
        "2024-03-12T11:41:13+00:00",
        "2024-03-13T16:03:39+00:00",
        "2024-03-14T09:37:18+00:00",
    ]
    for i, ts in enumerate(timestamps):
        test_file = tmp_path / f"file_{i}.txt"
        test_file.write_text(f"content {i}")
        subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
        env = {
            "GIT_AUTHOR_DATE": ts,
            "GIT_COMMITTER_DATE": ts,
        }
        adapter.run_git(["commit", "-m", f"feat: add feature {i}"], env_overrides=env)

    engine = AuditEngine(adapter)
    result = engine.audit()

    assert result.total_commits == 5
    assert result.round_seconds_pct == 0.0  # 27 seconds is not :00
    assert result.score >= 80
    assert "A" in result.rating_label


def test_audit_detects_robotic_fingerprints(tmp_path: Path) -> None:
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    adapter = GitAdapter(tmp_path)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Bot"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "bot@example.com"], check=True
    )

    # Create commits with exact :00 seconds and :00 minutes
    for i in range(5):
        test_file = tmp_path / f"bot_{i}.txt"
        test_file.write_text(f"data {i}")
        subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
        env = {
            "GIT_AUTHOR_DATE": "2024-03-15T02:00:00+00:00",
            "GIT_COMMITTER_DATE": "2024-03-15T02:00:00+00:00",
        }
        adapter.run_git(["commit", "-m", f"bot commit {i}"], env_overrides=env)

    engine = AuditEngine(adapter)
    result = engine.audit()

    assert result.total_commits == 5
    assert result.round_seconds_pct == 100.0
    assert result.round_minutes_pct == 100.0
    assert result.score < 70
    assert any(f.severity == "critical" for f in result.findings)
