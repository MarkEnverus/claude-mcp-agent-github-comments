"""Git repository detection utilities for auto-detecting GitHub repos."""

import re
import subprocess
from pathlib import Path
from typing import Optional


def detect_github_repo() -> Optional[str]:
    """
    Auto-detect the GitHub repository from the current git directory.

    Returns:
        Optional[str]: Repository in "owner/repo" format, or None if not detected

    Examples:
        >>> detect_github_repo()
        'mark.johnson/claude_mcp_agent_github_comments'
    """
    try:
        # Try to get the remote URL from git
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )

        remote_url = result.stdout.strip()
        if not remote_url:
            return None

        # Parse the URL to extract owner/repo
        return parse_github_url(remote_url)

    except subprocess.CalledProcessError:
        # Not a git repo or no remote configured
        return None
    except subprocess.TimeoutExpired:
        # Git command took too long
        return None
    except FileNotFoundError:
        # git command not found
        return None


def parse_github_url(url: str) -> Optional[str]:
    """
    Parse a GitHub URL (HTTPS or SSH) to extract owner/repo format.

    Args:
        url: GitHub URL in various formats

    Returns:
        Optional[str]: Repository in "owner/repo" format, or None if not a GitHub URL

    Examples:
        >>> parse_github_url("https://github.com/owner/repo.git")
        'owner/repo'
        >>> parse_github_url("git@github.com:owner/repo.git")
        'owner/repo'
        >>> parse_github_url("https://github.com/owner/repo")
        'owner/repo'
    """
    if not url:
        return None

    # Remove .git suffix if present
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    # Pattern 1: HTTPS format - https://github.com/owner/repo
    https_pattern = r"https?://github\.com/([^/]+)/([^/]+)"
    match = re.match(https_pattern, url)
    if match:
        owner, repo = match.groups()
        return f"{owner}/{repo}"

    # Pattern 2: SSH format - git@github.com:owner/repo
    ssh_pattern = r"git@github\.com:([^/]+)/(.+)"
    match = re.match(ssh_pattern, url)
    if match:
        owner, repo = match.groups()
        return f"{owner}/{repo}"

    # Pattern 3: Short SSH format - github.com:owner/repo
    short_ssh_pattern = r"github\.com:([^/]+)/(.+)"
    match = re.match(short_ssh_pattern, url)
    if match:
        owner, repo = match.groups()
        return f"{owner}/{repo}"

    # Not a recognized GitHub URL
    return None


def prompt_for_repo() -> Optional[str]:
    """
    Interactively prompt the user for a GitHub repository.

    This is used as a fallback when auto-detection fails.

    Returns:
        Optional[str]: Repository in "owner/repo" format, or None if user cancels
    """
    try:
        print("\n⚠️  Could not auto-detect GitHub repository from git remote.")
        print("Please enter the repository in 'owner/repo' format (e.g., 'facebook/react'):")
        print("Or press Ctrl+C to cancel.\n")

        repo = input("> ").strip()

        if not repo:
            return None

        # Validate format
        if "/" not in repo:
            print(f"❌ Invalid format: '{repo}'. Expected 'owner/repo' format.")
            return None

        owner, name = repo.split("/", 1)
        if not owner or not name:
            print(f"❌ Invalid format: '{repo}'. Both owner and repo name are required.")
            return None

        return repo

    except (KeyboardInterrupt, EOFError):
        print("\n\n❌ Repository input cancelled.")
        return None


def get_repo_with_fallback(provided_repo: Optional[str] = None) -> Optional[str]:
    """
    Get the repository with intelligent fallback logic.

    Priority:
    1. Use provided_repo if given
    2. Try auto-detection from git remote
    3. Prompt user interactively

    Args:
        provided_repo: Explicitly provided repository string

    Returns:
        Optional[str]: Repository in "owner/repo" format, or None if all methods fail
    """
    # First priority: explicitly provided repo
    if provided_repo:
        return provided_repo

    # Second priority: auto-detect from git
    detected_repo = detect_github_repo()
    if detected_repo:
        return detected_repo

    # Third priority: prompt user
    return prompt_for_repo()


def is_valid_repo_format(repo: str) -> bool:
    """
    Validate that a repository string is in the correct 'owner/repo' format.

    Args:
        repo: Repository string to validate

    Returns:
        bool: True if valid format, False otherwise

    Examples:
        >>> is_valid_repo_format("owner/repo")
        True
        >>> is_valid_repo_format("invalid")
        False
        >>> is_valid_repo_format("owner/repo/extra")
        False
    """
    if not repo or not isinstance(repo, str):
        return False

    parts = repo.split("/")
    if len(parts) != 2:
        return False

    owner, name = parts
    return bool(owner.strip() and name.strip())
