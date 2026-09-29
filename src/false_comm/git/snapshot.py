"""Snapshot manager providing safety checkpoints and one-command rollback."""

import json
import uuid
from datetime import datetime

from false_comm.git.adapter import GitAdapter
from false_comm.models.snapshot import SnapshotMetadata


class SnapshotManager:
    """Manages pre-execution safety snapshots and atomic rollbacks."""

    def __init__(self, git_adapter: GitAdapter) -> None:
        self.git = git_adapter
        self.repo_root = self.git.get_repo_root()
        # Prefer keeping snapshots in .git directory so it never pollutes the user working tree
        git_dir = self.repo_root / ".git"
        if git_dir.is_dir():
            self.storage_dir = git_dir / "false_comm" / "snapshots"
        else:
            self.storage_dir = self.repo_root / ".false_comm" / "snapshots"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, description: str = "Pre-run safety checkpoint") -> SnapshotMetadata:
        """Capture current Git state and save metadata."""
        current_branch = self.git.get_current_branch()
        head_sha = self.git.get_head_sha()
        reflog_point = self.git.get_reflog_head()
        has_unstaged = self.git.has_uncommitted_changes()

        stash_sha: str | None = None
        if has_unstaged:
            stash_sha = self.git.stash_push("false-comm auto-stash for snapshot")

        snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        metadata = SnapshotMetadata(
            snapshot_id=snapshot_id,
            created_at=datetime.now(),
            repo_path=str(self.repo_root),
            branch_name=current_branch,
            head_sha=head_sha,
            previous_reflog_head=reflog_point,
            had_unstaged_changes=has_unstaged,
            stash_sha=stash_sha,
            description=description,
        )

        self._save_metadata(metadata)
        return metadata

    def update_snapshot_results(
        self,
        snapshot_id: str,
        applied_shas: list[str],
        branches_created: list[str],
    ) -> None:
        """Record the SHAs and branches created after a successful run."""
        metadata = self.get_snapshot(snapshot_id)
        if not metadata:
            return
        metadata.applied_commit_shas = applied_shas
        metadata.commits_applied_count = len(applied_shas)
        metadata.active_branches_created = branches_created
        self._save_metadata(metadata)

    def get_snapshot(self, snapshot_id: str) -> SnapshotMetadata | None:
        """Load a specific snapshot metadata file."""
        file_path = self.storage_dir / f"{snapshot_id}.json"
        if not file_path.is_file():
            return None
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return SnapshotMetadata.model_validate(data)

    def list_snapshots(self) -> list[SnapshotMetadata]:
        """List all snapshots sorted from newest to oldest."""
        snapshots: list[SnapshotMetadata] = []
        for p in self.storage_dir.glob("snap_*.json"):
            try:
                with open(p, encoding="utf-8") as f:
                    data = json.load(f)
                snapshots.append(SnapshotMetadata.model_validate(data))
            except Exception:
                continue
        snapshots.sort(key=lambda s: s.created_at, reverse=True)
        return snapshots

    def get_latest_snapshot(self) -> SnapshotMetadata | None:
        """Return the most recent snapshot."""
        all_snaps = self.list_snapshots()
        return all_snaps[0] if all_snaps else None

    def rollback(self, snapshot_id: str | None = None) -> SnapshotMetadata:
        """Restore repository state precisely to the snapshot checkpoint."""
        if snapshot_id:
            metadata = self.get_snapshot(snapshot_id)
            if not metadata:
                raise ValueError(f"Snapshot with ID '{snapshot_id}' does not exist.")
        else:
            metadata = self.get_latest_snapshot()
            if not metadata:
                raise ValueError("No safety snapshots found to rollback.")

        # 1. Switch back to the original branch
        current_branch = self.git.get_current_branch()
        if current_branch != metadata.branch_name:
            self.git.checkout(metadata.branch_name)

        # 2. Hard reset to the original HEAD SHA
        self.git.reset_hard(metadata.head_sha)

        # 3. Clean up any temporary branches that were created
        existing_branches = set(self.git.list_branches())
        for b in metadata.active_branches_created:
            if b in existing_branches and b != metadata.branch_name:
                try:
                    self.git.delete_branch(b, force=True)
                except Exception:
                    pass

        # 4. Restore stash if one was created
        if metadata.stash_sha:
            try:
                self.git.stash_pop()
            except Exception:
                pass

        # 5. Remove or archive the snapshot file
        snap_file = self.storage_dir / f"{metadata.snapshot_id}.json"
        if snap_file.is_file():
            snap_file.unlink()

        return metadata

    def _save_metadata(self, metadata: SnapshotMetadata) -> None:
        file_path = self.storage_dir / f"{metadata.snapshot_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=2))
