"""
Code operations tools

Provides MCP tools for applying code fixes and managing git operations.
"""

import os
from pathlib import Path
from typing import Any

import git

from ..models import FixResult
from .github_api import get_github_client


async def apply_code_fix(
    file_path: str,
    line_number: int,
    fix_content: str,
    repo: str,
    commit_message: str | None = None,
    repo_path: str | None = None,
) -> dict[str, Any]:
    """
    Apply a code fix to address a PR comment

    This MCP tool modifies a file, creates a git commit, and returns the results.

    Args:
        file_path: Path to file to modify (relative to repo root)
        line_number: Line number to start modification
        fix_content: New code content to apply
        repo: Repository in format "owner/repo"
        commit_message: Custom commit message (optional)
        repo_path: Local path to repository (defaults to current directory)

    Returns:
        Dictionary with:
            - success: Whether fix was applied successfully
            - commit_sha: Git commit SHA (if committed)
            - diff: Diff of changes
            - files_changed: Number of files changed
            - error: Error message (if failed)

    Example:
        >>> result = await apply_code_fix(
        ...     file_path="src/auth.py",
        ...     line_number=45,
        ...     fix_content="if not user or not user.email:\\n    raise ValueError('User email required')",
        ...     repo="MarkEnverus/my-repo",
        ...     commit_message="fix: add null check for user.email"
        ... )
        >>> print(f"Commit: {result['commit_sha']}")

    Note:
        - This modifies the local repository
        - Always creates a commit
        - Does NOT push to remote (user should do that manually)
        - Requires clean working tree or will fail
    """
    try:
        # Get repo path
        if repo_path is None:
            repo_path = os.getcwd()

        # Initialize git repo
        git_repo = git.Repo(repo_path)

        # Check for clean working tree
        if git_repo.is_dirty():
            return FixResult(
                success=False,
                error="Working tree is dirty. Commit or stash changes first.",
            ).model_dump(mode="json")

        # Get full file path
        full_path = Path(repo_path) / file_path

        if not full_path.exists():
            return FixResult(
                success=False,
                error=f"File not found: {file_path}",
            ).model_dump(mode="json")

        # Read current content
        with open(full_path) as f:
            lines = f.readlines()

        # Apply fix
        # This is a simple line replacement
        # In production, you'd want more sophisticated patching
        if line_number < 1 or line_number > len(lines):
            return FixResult(
                success=False,
                error=f"Line number {line_number} out of range (file has {len(lines)} lines)",
            ).model_dump(mode="json")

        # Replace the line(s)
        # For multi-line fixes, split by \n
        fix_lines = fix_content.split("\n")

        # Simple replacement: replace single line with fix_lines
        lines[line_number - 1 : line_number] = [
            line + "\n" for line in fix_lines
        ]

        # Write modified content
        with open(full_path, "w") as f:
            f.writelines(lines)

        # Stage the file
        git_repo.index.add([file_path])

        # Create commit
        if commit_message is None:
            commit_message = f"fix: apply code fix to {file_path}:{line_number}"

        commit = git_repo.index.commit(commit_message)

        # Get diff
        diff = git_repo.git.show(commit.hexsha, "--format=%b", "--")

        result = FixResult(
            success=True,
            commit_sha=commit.hexsha,
            diff=diff,
            files_changed=1,
        )

        return result.model_dump(mode="json")

    except Exception as e:
        return FixResult(
            success=False,
            error=str(e),
        ).model_dump(mode="json")


async def get_pr_diff(
    pr_number: int,
    repo: str,
) -> str:
    """
    Get full unified diff for a PR

    This MCP tool fetches the complete diff showing all changes in a PR.

    Args:
        pr_number: PR number
        repo: Repository in format "owner/repo"

    Returns:
        Unified diff string showing all changes

    Example:
        >>> diff = await get_pr_diff(pr_number=69, repo="MarkEnverus/my-repo")
        >>> print(diff)
    """
    client = get_github_client(repo=repo)
    return client.get_pr_diff(pr_number)


async def create_comment_reply(
    comment_id: str,
    pr_number: int,
    repo: str,
    message: str,
) -> dict[str, Any]:
    """
    Reply to a PR comment

    This MCP tool posts a reply to a comment thread.

    Args:
        comment_id: Comment ID to reply to
        pr_number: PR number
        repo: Repository in format "owner/repo"
        message: Reply message text

    Returns:
        Dictionary with reply details:
            - id: Reply comment ID
            - url: URL to reply
            - body: Reply body

    Example:
        >>> reply = await create_comment_reply(
        ...     comment_id="123456",
        ...     pr_number=69,
        ...     repo="MarkEnverus/my-repo",
        ...     message="Fixed! Added null check as suggested."
        ... )
    """
    client = get_github_client(repo=repo)
    return client.create_comment_reply(comment_id, pr_number, message)


async def resolve_thread(
    comment_id: str,
    pr_number: int,
    repo: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """
    Resolve a comment thread

    This MCP tool marks a comment thread as resolved.

    Args:
        comment_id: Comment/thread ID to resolve
        pr_number: PR number
        repo: Repository in format "owner/repo"
        reason: Optional reason for resolution

    Returns:
        Dictionary with resolution status

    Example:
        >>> result = await resolve_thread(
        ...     comment_id="123456",
        ...     pr_number=69,
        ...     repo="MarkEnverus/my-repo",
        ...     reason="Issue fixed in commit abc123"
        ... )

    Note:
        Full implementation requires GitHub GraphQL API.
        Current implementation is a placeholder.
    """
    client = get_github_client(repo=repo)
    result = client.resolve_thread(comment_id, pr_number)

    if reason:
        result["reason"] = reason

    return result
