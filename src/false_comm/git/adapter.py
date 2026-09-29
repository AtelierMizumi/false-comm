"""Subprocess-based Git adapter with strict safety and identity validation."""

import os
import subprocess
from pathlib import Path

from false_comm.models.config import GitIdentity


class GitExecutionError(RuntimeError):
    """Raised when a Git command fails."""

    def __init__(self, command: list[str], returncode: int, stderr: str) -> None:
        cmd_str = " ".join(command)
        super().__init__(f"Git command failed [{returncode}]: {cmd_str}\nError output:\n{stderr}")
        self.command = command
        self.returncode = returncode
        self.stderr = stderr


class GitAdapter:
    """Safely executes and inspects Git repository state."""

    def __init__(self, repo_path: str | Path | None = None) -> None:
        self.repo_path = Path(repo_path or os.getcwd()).resolve()

    def run_git(
        self,
        args: list[str],
        env_overrides: dict[str, str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """Execute a git subcommand with optional custom environment variables."""
        full_cmd = ["git", "-C", str(self.repo_path), *args]
        env = os.environ.copy()
        if env_overrides:
            env.update(env_overrides)

        res = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

        if check and res.returncode != 0:
            raise GitExecutionError(full_cmd, res.returncode, res.stderr.strip())
        return res

    def is_git_repo(self) -> bool:
        """Verify whether repo_path is inside a valid git working tree."""
        res = self.run_git(["rev-parse", "--is-inside-work-tree"], check=False)
        return res.returncode == 0 and res.stdout.strip() == "true"

    def get_repo_root(self) -> Path:
        """Return the absolute path to the repository root."""
        res = self.run_git(["rev-parse", "--show-toplevel"])
        return Path(res.stdout.strip()).resolve()

    def get_current_branch(self) -> str:
        """Return the name of the current active branch."""
        res = self.run_git(["rev-parse", "--abbrev-ref", "HEAD"], check=False)
        branch = res.stdout.strip()
        if branch == "HEAD":
            from false_comm.i18n import t

            raise ValueError(t("error.detached_head"))
        return branch

    def get_head_sha(self) -> str:
        """Return SHA of current HEAD commit."""
        res = self.run_git(["rev-parse", "HEAD"])
        return res.stdout.strip()

    def has_uncommitted_changes(self) -> bool:
        """Return True if working tree or index has uncommitted modifications."""
        res = self.run_git(["status", "--porcelain"])
        return len(res.stdout.strip()) > 0

    def stash_push(self, message: str = "false-comm safety stash") -> str | None:
        """Stash uncommitted changes and return stash sha or None if clean."""
        if not self.has_uncommitted_changes():
            return None
        res = self.run_git(["stash", "create", message])
        stash_sha = res.stdout.strip()
        if stash_sha:
            self.run_git(["stash", "store", "-m", message, stash_sha])
            self.run_git(["reset", "--hard", "HEAD"])
            return stash_sha
        return None

    def stash_pop(self) -> bool:
        """Restore stashed changes."""
        res = self.run_git(["stash", "pop"], check=False)
        return res.returncode == 0

    def detect_local_timezone(self) -> str:
        """Calculate local system timezone in Git format (+0700, -0500, etc.) respecting Linux configurations."""
        from false_comm.utils.platform import detect_linux_timezone

        return detect_linux_timezone()

    def get_git_identity(self) -> GitIdentity:
        """Extract user.name, user.email, and GPG configuration from git config."""
        name_res = self.run_git(["config", "user.name"], check=False)
        email_res = self.run_git(["config", "user.email"], check=False)
        gpg_res = self.run_git(["config", "commit.gpgsign"], check=False)
        key_res = self.run_git(["config", "user.signingkey"], check=False)

        name = name_res.stdout.strip()
        email = email_res.stdout.strip()
        gpg_sign = gpg_res.stdout.strip().lower() in {"true", "yes", "1"}
        signing_key = key_res.stdout.strip() or None

        if not name or not email:
            from false_comm.i18n import t

            raise ValueError(t("error.identity_missing"))

        tz = self.detect_local_timezone()
        return GitIdentity(
            name=name,
            email=email,
            timezone=tz,
            gpg_sign=gpg_sign,
            signing_key=signing_key,
        )

    def create_branch(self, branch_name: str, start_point: str | None = None) -> None:
        """Create a new branch."""
        args = ["branch", branch_name]
        if start_point:
            args.append(start_point)
        self.run_git(args)

    def checkout(self, branch_or_ref: str) -> None:
        """Checkout a branch or ref."""
        self.run_git(["checkout", branch_or_ref])

    def delete_branch(self, branch_name: str, force: bool = True) -> None:
        """Delete a branch."""
        flag = "-D" if force else "-d"
        self.run_git(["branch", flag, branch_name])

    def list_branches(self) -> list[str]:
        """List local branch names."""
        res = self.run_git(["branch", "--format=%(refname:short)"])
        return [line.strip() for line in res.stdout.splitlines() if line.strip()]

    def add_files(self, paths: list[str]) -> None:
        """Stage files for commit."""
        if not paths:
            return
        self.run_git(["add", *paths])

    def commit(
        self,
        message: str,
        author_date: str,
        committer_date: str,
        author_name: str,
        author_email: str,
        committer_name: str | None = None,
        committer_email: str | None = None,
        gpg_sign: bool = False,
        signing_key: str | None = None,
        allow_empty: bool = False,
    ) -> str:
        """Create a commit with precise timestamp and identity overrides."""
        c_name = committer_name or author_name
        c_email = committer_email or author_email

        env = {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_AUTHOR_DATE": author_date,
            "GIT_COMMITTER_NAME": c_name,
            "GIT_COMMITTER_EMAIL": c_email,
            "GIT_COMMITTER_DATE": committer_date,
        }

        args = ["commit", "-m", message]
        if allow_empty:
            args.append("--allow-empty")
        if gpg_sign:
            if signing_key:
                args.extend([f"-S{signing_key}"])
            else:
                args.append("-S")
        else:
            args.append("--no-gpg-sign")

        self.run_git(args, env_overrides=env)
        return self.get_head_sha()

    def merge(
        self,
        branch_to_merge: str,
        message: str,
        date_str: str,
        author_name: str,
        author_email: str,
    ) -> str:
        """Merge a branch creating a true merge commit with customized date and message."""
        env = {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_AUTHOR_DATE": date_str,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": author_email,
            "GIT_COMMITTER_DATE": date_str,
        }
        args = ["merge", "--no-ff", "-m", message, branch_to_merge]
        self.run_git(args, env_overrides=env)
        return self.get_head_sha()

    def reset_hard(self, target_sha: str) -> None:
        """Reset working tree and index hard to target_sha."""
        self.run_git(["reset", "--hard", target_sha])

    def get_reflog_head(self) -> str:
        """Return the current reflog top entry."""
        res = self.run_git(["rev-parse", "HEAD@{0}"], check=False)
        return res.stdout.strip()
