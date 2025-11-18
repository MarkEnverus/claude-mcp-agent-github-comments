"""
GitHub API wrapper for PR comment operations

Provides low-level GitHub API interactions using PyGithub and GraphQL.
"""

import json
import os
import subprocess
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
from ..utils.git_detector import get_repo_with_fallback


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
        self.token = token
        self._repo: Repository | None = None
        self._thread_status_cache: dict[str, CommentStatus] = {}  # Cache for thread statuses

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
        """
        Determine comment thread status using GraphQL API

        Args:
            comment: PullRequestComment object

        Returns:
            CommentStatus.OPEN or CommentStatus.RESOLVED
        """
        comment_id = str(comment.id)

        # Check cache first
        if comment_id in self._thread_status_cache:
            return self._thread_status_cache[comment_id]

        try:
            # Query GraphQL for thread status
            # We need to find the thread that contains this comment
            owner, repo_name = self.repo_name.split("/")
            pr_number = comment.pull_request_url.split("/")[-1]

            query = f"""
            {{
              repository(owner: "{owner}", name: "{repo_name}") {{
                pullRequest(number: {pr_number}) {{
                  reviewThreads(first: 100) {{
                    nodes {{
                      id
                      isResolved
                      comments(first: 100) {{
                        nodes {{
                          databaseId
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            """

            data = self._graphql_query(query)

            # Find the thread containing this comment
            threads = data.get("repository", {}).get("pullRequest", {}).get("reviewThreads", {}).get("nodes", [])

            for thread in threads:
                comment_ids = [
                    c["databaseId"]
                    for c in thread.get("comments", {}).get("nodes", [])
                ]
                if comment.id in comment_ids:
                    is_resolved = thread.get("isResolved", False)
                    status = CommentStatus.RESOLVED if is_resolved else CommentStatus.OPEN

                    # Cache the result
                    self._thread_status_cache[comment_id] = status
                    return status

            # If thread not found, assume open
            self._thread_status_cache[comment_id] = CommentStatus.OPEN
            return CommentStatus.OPEN

        except Exception:
            # If GraphQL fails, fall back to OPEN
            # Don't cache failures to allow retry
            return CommentStatus.OPEN

    def create_comment_reply(
        self, comment_id: str, pr_number: int, body: str
    ) -> dict[str, Any]:
        """
        Reply to a PR comment (creates threaded reply for review comments)

        Args:
            comment_id: Comment ID to reply to
            pr_number: PR number
            body: Reply text

        Returns:
            Reply comment data with id, url, and body

        Raises:
            ValueError: If comment not found
            Exception: If API call fails
        """
        pr = self.get_pull_request(pr_number)

        # Try to find the comment among review comments
        try:
            review_comments = list(pr.get_review_comments())
            comment_id_int = int(comment_id)

            for comment in review_comments:
                if comment.id == comment_id_int:
                    # This is a review comment - create threaded reply
                    reply = pr.create_review_comment_reply(
                        comment_id=comment_id_int,
                        body=body
                    )

                    return {
                        "id": str(reply.id),
                        "url": reply.html_url,
                        "body": reply.body,
                        "type": "review_comment_reply",
                    }

        except ValueError:
            pass  # comment_id not an integer, might be an issue comment

        # Try issue comments
        try:
            issue_comments = list(pr.get_issue_comments())
            comment_id_int = int(comment_id)

            for comment in issue_comments:
                if comment.id == comment_id_int:
                    # This is an issue comment - create general PR comment
                    # Issue comments don't have direct threading, so post a reference
                    reply_body = f"> Replying to comment {comment_id}\n\n{body}"
                    reply = pr.create_issue_comment(reply_body)

                    return {
                        "id": str(reply.id),
                        "url": reply.html_url,
                        "body": reply.body,
                        "type": "issue_comment",
                    }

        except ValueError:
            pass

        # Comment not found
        raise ValueError(
            f"Comment {comment_id} not found in PR {pr_number}. "
            "It may have been deleted or is from a different PR."
        )

    def resolve_thread(
        self, comment_id: str, pr_number: int
    ) -> dict[str, Any]:
        """
        Resolve a comment thread using GraphQL API

        Args:
            comment_id: Comment ID (will find its thread)
            pr_number: PR number

        Returns:
            Resolution status with thread_id and is_resolved

        Raises:
            ValueError: If comment or thread not found
            Exception: If GraphQL mutation fails
        """
        try:
            # First, find the thread ID for this comment
            owner, repo_name = self.repo_name.split("/")

            query = f"""
            {{
              repository(owner: "{owner}", name: "{repo_name}") {{
                pullRequest(number: {pr_number}) {{
                  reviewThreads(first: 100) {{
                    nodes {{
                      id
                      isResolved
                      comments(first: 100) {{
                        nodes {{
                          databaseId
                        }}
                      }}
                    }}
                  }}
                }}
              }}
            }}
            """

            data = self._graphql_query(query)

            # Find the thread containing this comment
            threads = data.get("repository", {}).get("pullRequest", {}).get("reviewThreads", {}).get("nodes", [])

            thread_id = None
            already_resolved = False
            comment_id_int = int(comment_id)

            for thread in threads:
                comment_ids = [
                    c["databaseId"]
                    for c in thread.get("comments", {}).get("nodes", [])
                ]
                if comment_id_int in comment_ids:
                    thread_id = thread["id"]
                    already_resolved = thread.get("isResolved", False)
                    break

            if not thread_id:
                raise ValueError(
                    f"No review thread found containing comment {comment_id} in PR {pr_number}"
                )

            if already_resolved:
                # Already resolved, return success
                return {
                    "comment_id": comment_id,
                    "thread_id": thread_id,
                    "status": "already_resolved",
                    "is_resolved": True,
                }

            # Resolve the thread using GraphQL mutation
            mutation = f"""
            mutation {{
              resolveReviewThread(input: {{threadId: "{thread_id}"}}) {{
                thread {{
                  id
                  isResolved
                }}
              }}
            }}
            """

            result = self._graphql_mutation(mutation)

            # Extract result
            thread_data = result.get("resolveReviewThread", {}).get("thread", {})
            is_resolved = thread_data.get("isResolved", False)

            # Clear cache for this comment
            if comment_id in self._thread_status_cache:
                del self._thread_status_cache[comment_id]

            if is_resolved:
                return {
                    "comment_id": comment_id,
                    "thread_id": thread_id,
                    "status": "resolved",
                    "is_resolved": True,
                }
            else:
                raise Exception(f"Thread {thread_id} resolution failed - isResolved is still False")

        except ValueError as e:
            # Re-raise ValueError with original message
            raise e
        except Exception as e:
            raise Exception(f"Failed to resolve thread for comment {comment_id}: {e}") from e

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

    def _graphql_query(self, query: str) -> dict[str, Any]:
        """
        Execute a GraphQL query using gh CLI

        Args:
            query: GraphQL query string

        Returns:
            Query response data

        Raises:
            Exception: If GraphQL query fails
        """
        try:
            result = subprocess.run(
                ["gh", "api", "graphql", "-f", f"query={query}"],
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ, "GH_TOKEN": self.token},
            )
            response = json.loads(result.stdout)

            if "errors" in response:
                error_msg = "; ".join([e.get("message", str(e)) for e in response["errors"]])
                raise Exception(f"GraphQL query error: {error_msg}")

            return response.get("data", {})

        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to execute GraphQL query: {e.stderr}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse GraphQL response: {e}") from e

    def _graphql_mutation(self, mutation: str) -> dict[str, Any]:
        """
        Execute a GraphQL mutation using gh CLI

        Args:
            mutation: GraphQL mutation string

        Returns:
            Mutation response data

        Raises:
            Exception: If GraphQL mutation fails
        """
        # Mutations use the same API as queries
        return self._graphql_query(mutation)


# Cache of client instances per repository (singleton per repo)
_clients: dict[str, GitHubAPIClient] = {}


def get_github_client(
    token: str | None = None, repo: str | None = None
) -> GitHubAPIClient:
    """
    Get or create GitHub API client with intelligent repo detection

    Args:
        token: GitHub token (defaults to GITHUB_TOKEN env var)
        repo: Repository in "owner/repo" format (auto-detected if not provided)

    Returns:
        GitHubAPIClient instance

    Raises:
        ValueError: If token is missing or repo cannot be determined
    """
    global _clients

    token = token or os.getenv("GITHUB_TOKEN")

    if not token:
        raise ValueError("GitHub token required (GITHUB_TOKEN env var)")

    # Use intelligent repo detection with fallback
    # Priority: 1) Provided arg, 2) Auto-detect, 3) Prompt user
    repo = get_repo_with_fallback(repo)

    if not repo:
        raise ValueError(
            "Repository could not be determined. "
            "Please provide it explicitly or run from within a git repository."
        )

    # Return cached client for this repo, or create new one
    if repo not in _clients:
        _clients[repo] = GitHubAPIClient(token=token, repo=repo)

    return _clients[repo]
