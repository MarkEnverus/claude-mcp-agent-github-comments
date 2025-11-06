"""
GitHub API wrapper for PR comment operations

Provides low-level GitHub API interactions using PyGithub.
"""

import os
from typing import Any

from github import Auth, Github
from github.IssueComment import IssueComment
from github.PullRequest import PullRequest
from github.PullRequestComment import PullRequestComment
from github.Repository import Repository

from ..models import (
    CommentStatus,
    CommentType,
    PRComment,
)


class GitHubAPIClient:
    """
    GitHub API client for PR comment operations
    """

    def __init__(self, token: str, repo: str):
        """
        Initialize GitHub API client

        Args:
            token: GitHub personal access token
            repo: Repository in format "owner/repo"
        """
        auth = Auth.Token(token)
        self.client = Github(auth=auth)
        self.repo_name = repo
        self._repo: Repository | None = None

    @property
    def repo(self) -> Repository:
        """Get repository object (cached)"""
        if self._repo is None:
            self._repo = self.client.get_repo(self.repo_name)
        return self._repo

    def get_pull_request(self, pr_number: int) -> PullRequest:
        """Get PR by number"""
        return self.repo.get_pull(pr_number)

    def get_pr_review_comments(self, pr_number: int) -> list[PullRequestComment]:
        """
        Get review comments (inline code comments) for a PR

        Args:
            pr_number: PR number

        Returns:
            List of review comments
        """
        pr = self.get_pull_request(pr_number)
        return list(pr.get_review_comments())

    def get_pr_issue_comments(self, pr_number: int) -> list[IssueComment]:
        """
        Get issue comments (general PR comments) for a PR

        Args:
            pr_number: PR number

        Returns:
            List of issue comments
        """
        pr = self.get_pull_request(pr_number)
        return list(pr.get_issue_comments())

    def get_all_pr_comments(self, pr_number: int) -> list[PRComment]:
        """
        Get all comments (both review and issue) for a PR

        Args:
            pr_number: PR number

        Returns:
            List of PRComment objects
        """
        comments = []

        # Get review comments (inline)
        review_comments = self.get_pr_review_comments(pr_number)
        for comment in review_comments:
            comments.append(self._convert_review_comment(comment, pr_number))

        # Get issue comments (general)
        issue_comments = self.get_pr_issue_comments(pr_number)
        for comment in issue_comments:
            comments.append(self._convert_issue_comment(comment, pr_number))

        return comments

    def _convert_review_comment(
        self, comment: PullRequestComment, pr_number: int
    ) -> PRComment:
        """Convert PyGithub review comment to PRComment model"""
        return PRComment(
            id=str(comment.id),
            comment_type=CommentType.REVIEW_COMMENT,
            author=comment.user.login if comment.user else "unknown",
            body=comment.body,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            status=self._get_comment_status(comment),
            file_path=comment.path,
            line_number=comment.line if comment.line else comment.original_line,
            diff_hunk=comment.diff_hunk,
            url=comment.url,
            html_url=comment.html_url,
            pr_number=pr_number,
            repo=self.repo_name,
        )

    def _convert_issue_comment(
        self, comment: IssueComment, pr_number: int
    ) -> PRComment:
        """Convert PyGithub issue comment to PRComment model"""
        return PRComment(
            id=str(comment.id),
            comment_type=CommentType.ISSUE_COMMENT,
            author=comment.user.login if comment.user else "unknown",
            body=comment.body,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            status=CommentStatus.OPEN,  # Issue comments don't have resolved status
            url=comment.url,
            html_url=comment.html_url,
            pr_number=pr_number,
            repo=self.repo_name,
        )

    def _get_comment_status(self, comment: PullRequestComment) -> CommentStatus:
        """Determine comment status"""
        # PyGithub doesn't directly expose resolved status
        # This is a simplified implementation
        # In practice, we'd need to check the review thread status
        if hasattr(comment, "pull_request_review_id"):
            return CommentStatus.OPEN
        return CommentStatus.OPEN

    def create_comment_reply(
        self, comment_id: str, pr_number: int, body: str
    ) -> dict[str, Any]:
        """
        Reply to a PR comment

        Args:
            comment_id: Comment ID to reply to
            pr_number: PR number
            body: Reply text

        Returns:
            Reply comment data
        """
        pr = self.get_pull_request(pr_number)

        # Try to find the comment and reply
        # This is a simplified implementation
        reply = pr.create_issue_comment(body)

        return {
            "id": str(reply.id),
            "url": reply.html_url,
            "body": reply.body,
        }

    def resolve_thread(
        self, comment_id: str, pr_number: int
    ) -> dict[str, Any]:
        """
        Resolve a comment thread

        Args:
            comment_id: Comment/thread ID to resolve
            pr_number: PR number

        Returns:
            Resolution status

        Note:
            GitHub's REST API doesn't directly support resolving threads.
            This would typically require GraphQL API.
            This is a placeholder implementation.
        """
        # TODO: Implement using GraphQL API
        # For now, return success status
        return {
            "comment_id": comment_id,
            "status": "resolved",
            "method": "placeholder",
            "note": "Full implementation requires GraphQL API",
        }

    def get_file_content(
        self, file_path: str, ref: str | None = None
    ) -> str:
        """
        Get file content from repository

        Args:
            file_path: Path to file in repo
            ref: Git ref (branch, commit, tag). Defaults to default branch.

        Returns:
            File content as string
        """
        try:
            content = self.repo.get_contents(file_path, ref=ref)
            if isinstance(content, list):
                # It's a directory, not a file
                raise ValueError(f"{file_path} is a directory, not a file")
            return content.decoded_content.decode("utf-8")
        except Exception as e:
            raise Exception(f"Failed to get file content: {e}") from e

    def get_pr_diff(self, pr_number: int) -> str:
        """
        Get unified diff for entire PR

        Args:
            pr_number: PR number

        Returns:
            Unified diff string
        """
        pr = self.get_pull_request(pr_number)

        # Get PR files and build diff
        files = pr.get_files()
        diff_parts = []

        for file in files:
            if file.patch:
                diff_parts.append(f"diff --git a/{file.filename} b/{file.filename}")
                diff_parts.append(file.patch)
                diff_parts.append("")

        return "\n".join(diff_parts)

    def get_pr_files(self, pr_number: int) -> list[dict[str, Any]]:
        """
        Get list of files changed in PR

        Args:
            pr_number: PR number

        Returns:
            List of file data with changes
        """
        pr = self.get_pull_request(pr_number)
        files = pr.get_files()

        result = []
        for file in files:
            result.append(
                {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "patch": file.patch,
                }
            )

        return result


# Singleton instance (can be initialized once and reused)
_client: GitHubAPIClient | None = None


def get_github_client(
    token: str | None = None, repo: str | None = None
) -> GitHubAPIClient:
    """
    Get or create GitHub API client

    Args:
        token: GitHub token (defaults to GITHUB_TOKEN env var)
        repo: Repository (defaults to GITHUB_REPO env var)

    Returns:
        GitHubAPIClient instance
    """
    global _client

    if _client is None:
        token = token or os.getenv("GITHUB_TOKEN")
        repo = repo or os.getenv("GITHUB_REPO")

        if not token:
            raise ValueError("GitHub token required (GITHUB_TOKEN env var)")
        if not repo:
            raise ValueError("Repository required (GITHUB_REPO env var)")

        _client = GitHubAPIClient(token=token, repo=repo)

    return _client
