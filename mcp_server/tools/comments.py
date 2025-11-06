"""
Comment fetching and context tools

Provides MCP tools for fetching and filtering PR comments,
and getting code context around comments.
"""

from datetime import datetime, timedelta
from typing import Any

from ..models import CommentContext, CommentFilters, PRComment
from .github_api import get_github_client


async def fetch_pr_comments(
    pr_number: int,
    repo: str,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch PR comments with intelligent filtering

    This is an MCP tool that fetches comments from a GitHub PR
    and applies various filters.

    Args:
        pr_number: PR number to fetch comments from
        repo: Repository in format "owner/repo"
        filters: Filter options:
            - authors: List of author usernames to include
            - status: "open", "resolved", or "all"
            - types: List of comment types to include
            - keywords: List of keywords to search for in comment body
            - min_age_days: Only include comments older than N days

    Returns:
        List of comment dictionaries with full details

    Example:
        >>> comments = await fetch_pr_comments(
        ...     pr_number=69,
        ...     repo="MarkEnverus/my-repo",
        ...     filters={
        ...         "authors": ["github-copilot"],
        ...         "status": "open",
        ...         "keywords": ["security", "null check"]
        ...     }
        ... )
    """
    # Get GitHub client
    client = get_github_client(repo=repo)

    # Fetch all comments
    all_comments = client.get_all_pr_comments(pr_number)

    # Parse filters
    filter_obj = CommentFilters(**(filters or {}))

    # Apply filters
    filtered_comments = _apply_filters(all_comments, filter_obj)

    # Convert to dict for JSON serialization
    return [comment.model_dump(mode="json") for comment in filtered_comments]


def _apply_filters(
    comments: list[PRComment], filters: CommentFilters
) -> list[PRComment]:
    """
    Apply filters to comment list

    Args:
        comments: List of PRComment objects
        filters: CommentFilters object

    Returns:
        Filtered list of comments
    """
    filtered = comments

    # Filter by author
    if filters.authors:
        filtered = [c for c in filtered if c.author in filters.authors]

    # Filter by status
    if filters.status:
        filtered = [c for c in filtered if c.status == filters.status]

    # Filter by comment type
    if filters.types:
        filtered = [c for c in filtered if c.comment_type in filters.types]

    # Filter by keywords (case-insensitive search in body)
    if filters.keywords:
        filtered = [
            c
            for c in filtered
            if any(
                keyword.lower() in c.body.lower() for keyword in filters.keywords
            )
        ]

    # Filter by age
    if filters.min_age_days > 0:
        min_date = datetime.now() - timedelta(days=filters.min_age_days)
        filtered = [c for c in filtered if c.created_at < min_date]

    return filtered


async def get_comment_context(
    comment_id: str,
    pr_number: int,
    repo: str,
    lines_before: int = 10,
    lines_after: int = 10,
) -> dict[str, Any]:
    """
    Get code context around a comment location

    This MCP tool fetches the code surrounding a comment's location
    to provide context for analysis and fix generation.

    Args:
        comment_id: Comment ID
        pr_number: PR number
        repo: Repository in format "owner/repo"
        lines_before: Number of lines to show before comment location
        lines_after: Number of lines to show after comment location

    Returns:
        Dictionary with:
            - file_path: Path to file
            - line_number: Line number of comment
            - code_snippet: Code with context
            - diff_hunk: Diff hunk if available
            - related_changes: List of related changes in PR

    Example:
        >>> context = await get_comment_context(
        ...     comment_id="123456",
        ...     pr_number=69,
        ...     repo="MarkEnverus/my-repo",
        ...     lines_before=5,
        ...     lines_after=5
        ... )
        >>> print(context["code_snippet"])
    """
    # Get GitHub client
    client = get_github_client(repo=repo)

    # Find the comment
    comments = client.get_all_pr_comments(pr_number)
    comment = next((c for c in comments if c.id == comment_id), None)

    if not comment:
        raise ValueError(f"Comment {comment_id} not found in PR {pr_number}")

    if not comment.file_path or not comment.line_number:
        # Comment is not associated with a specific line
        return CommentContext(
            comment_id=comment_id,
            file_path="",
            line_number=0,
            code_snippet=comment.body,
            lines_before=0,
            lines_after=0,
            diff_hunk=comment.diff_hunk,
        ).model_dump(mode="json")

    # Get file content
    try:
        # Get PR to find the head ref
        pr = client.get_pull_request(pr_number)
        file_content = client.get_file_content(
            comment.file_path, ref=pr.head.ref
        )

        # Extract code snippet with context
        lines = file_content.split("\n")
        line_idx = comment.line_number - 1  # Convert to 0-based index

        start_idx = max(0, line_idx - lines_before)
        end_idx = min(len(lines), line_idx + lines_after + 1)

        snippet_lines = []
        for i in range(start_idx, end_idx):
            # Add line numbers
            marker = ">>>" if i == line_idx else "   "
            snippet_lines.append(f"{marker} {i+1:4d} | {lines[i]}")

        code_snippet = "\n".join(snippet_lines)

        # Get related changes (other files modified in PR)
        pr_files = client.get_pr_files(pr_number)
        related_changes = [
            f"{f['filename']} (+{f['additions']}/-{f['deletions']})"
            for f in pr_files
            if f["filename"] != comment.file_path
        ]

        context = CommentContext(
            comment_id=comment_id,
            file_path=comment.file_path,
            line_number=comment.line_number,
            code_snippet=code_snippet,
            lines_before=lines_before,
            lines_after=lines_after,
            diff_hunk=comment.diff_hunk,
            related_changes=related_changes,
        )

        return context.model_dump(mode="json")

    except Exception as e:
        # Fallback to just showing diff hunk
        context = CommentContext(
            comment_id=comment_id,
            file_path=comment.file_path or "",
            line_number=comment.line_number or 0,
            code_snippet=f"Error fetching file content: {e}\n\nDiff hunk:\n{comment.diff_hunk or 'Not available'}",
            lines_before=0,
            lines_after=0,
            diff_hunk=comment.diff_hunk,
        )

        return context.model_dump(mode="json")
