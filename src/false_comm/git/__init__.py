"""Git execution, snapshotting, and branching facilities."""

from false_comm.git.adapter import GitAdapter, GitExecutionError
from false_comm.git.branch_sim import BranchSimEngine
from false_comm.git.snapshot import SnapshotManager

__all__ = [
    "BranchSimEngine",
    "GitAdapter",
    "GitExecutionError",
    "SnapshotManager",
]
