"""Git parsing skill - extract changed files from git diff."""

import os
from typing import List, Optional
from git import Repo, GitCommandError
from core.models import FileDiff, ChangeType


class GitParser:
    """Parse git diff to extract changed files."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        try:
            self.repo = Repo(repo_path)
        except Exception as e:
            raise ValueError(f"Invalid git repository: {repo_path}") from e

    def get_current_branch(self) -> str:
        """Get current branch name."""
        return self.repo.active_branch.name

    def parse_diff(self, base_branch: str = "main") -> List[FileDiff]:
        """
        Parse git diff against base branch.

        Only returns changed TypeScript/JavaScript files.
        """
        changed_files = []

        try:
            # Get diff against base branch
            diff_index = self.repo.head.commit.diff(base_branch)

            for diff_item in diff_index:
                # Only process TS/JS files
                if not self._is_supported_file(diff_item.a_path or diff_item.b_path):
                    continue

                file_diff = self._parse_diff_item(diff_item)
                if file_diff:
                    changed_files.append(file_diff)

        except GitCommandError as e:
            print(f"Git command error: {e}")

        return changed_files

    def _is_supported_file(self, path: Optional[str]) -> bool:
        """Check if file is TypeScript or JavaScript."""
        if not path:
            return False
        return path.endswith(('.ts', '.tsx', '.js', '.jsx'))

    def _parse_diff_item(self, diff_item) -> Optional[FileDiff]:
        """Parse a single diff item."""
        change_type = self._get_change_type(diff_item.change_type)

        if change_type == ChangeType.DELETED:
            return FileDiff(
                path=diff_item.a_path,
                change_type=change_type,
                old_content=self._read_blob(diff_item.a_blob),
                new_content=None
            )
        elif change_type == ChangeType.ADDED:
            return FileDiff(
                path=diff_item.b_path,
                change_type=change_type,
                old_content=None,
                new_content=self._read_blob(diff_item.b_blob)
            )
        else:  # MODIFIED
            return FileDiff(
                path=diff_item.b_path,
                change_type=change_type,
                old_content=self._read_blob(diff_item.a_blob),
                new_content=self._read_blob(diff_item.b_blob)
            )

    def _get_change_type(self, git_change_type: str) -> ChangeType:
        """Convert git change type to our enum."""
        if git_change_type == 'A':
            return ChangeType.ADDED
        elif git_change_type == 'D':
            return ChangeType.DELETED
        else:  # 'M', 'R', 'T', etc.
            return ChangeType.MODIFIED

    def _read_blob(self, blob) -> Optional[str]:
        """Read content from git blob."""
        if blob is None:
            return None
        try:
            return blob.data_stream.read().decode('utf-8')
        except Exception:
            return None


def parse_git_diff(repo_path: str, base_branch: str = "main") -> tuple[str, List[FileDiff]]:
    """
    Parse git diff for current branch against base branch.

    Returns:
        Tuple of (current_branch_name, list_of_changed_files)
    """
    parser = GitParser(repo_path)
    branch_name = parser.get_current_branch()
    changed_files = parser.parse_diff(base_branch)

    return branch_name, changed_files
