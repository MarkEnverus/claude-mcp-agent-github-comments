"""
Unit tests for GitHub API client

Tests all functions in mcp_server/tools/github_api.py with mocked GitHub API responses.
"""
import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from github.PullRequestComment import PullRequestComment

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.models import CommentStatus
from mcp_server.tools.github_api import GitHubAPIClient


@pytest.fixture
def mock_github_token():
    """Provide a test GitHub token"""
    return "test_token_12345"


@pytest.fixture
def mock_repo_name():
    """Provide a test repository name"""
    return "test-owner/test-repo"


@pytest.fixture
def client(mock_github_token, mock_repo_name):
    """Create a GitHubAPIClient instance with mocked Github client"""
    with patch("mcp_server.tools.github_api.Github"):
        client = GitHubAPIClient(token=mock_github_token, repo=mock_repo_name)
        return client


@pytest.fixture
def mock_review_comment():
    """Create a mock review comment"""
    comment = Mock(spec=PullRequestComment)
    comment.id = 12345
    comment.user = Mock()
    comment.user.login = "test-user"
    comment.body = "This is a test comment"
    comment.created_at = "2025-01-01T00:00:00Z"
    comment.updated_at = "2025-01-01T00:00:00Z"
    comment.path = "test/file.py"
    comment.line = 42
    comment.original_line = 42
    comment.diff_hunk = "@@ -40,3 +40,3 @@"
    comment.url = "https://api.github.com/repos/test-owner/test-repo/pulls/comments/12345"
    comment.html_url = "https://github.com/test-owner/test-repo/pull/1#discussion_r12345"
    comment.pull_request_url = "https://api.github.com/repos/test-owner/test-repo/pulls/1"
    return comment


@pytest.fixture
def sample_thread_data():
    """Load sample thread data from fixtures"""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_threads.json"
    with open(fixture_path) as f:
        return json.load(f)


class TestGraphQLMethods:
    """Test GraphQL query/mutation methods"""

    def test_graphql_query_success(self, client):
        """Test successful GraphQL query execution"""
        mock_response = {
            "data": {
                "repository": {
                    "name": "test-repo"
                }
            }
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout=json.dumps(mock_response),
                returncode=0
            )

            result = client._graphql_query("{ repository { name } }")

            assert result == mock_response["data"]
            mock_run.assert_called_once()

    def test_graphql_query_with_errors(self, client):
        """Test GraphQL query with errors in response"""
        mock_response = {
            "errors": [
                {"message": "Field 'invalid' doesn't exist"}
            ]
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout=json.dumps(mock_response),
                returncode=0
            )

            with pytest.raises(Exception, match="GraphQL query error"):
                client._graphql_query("{ invalid }")

    def test_graphql_query_subprocess_failure(self, client):
        """Test GraphQL query when subprocess fails"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "gh", stderr="Authentication failed"
            )

            with pytest.raises(Exception, match="Failed to execute GraphQL query"):
                client._graphql_query("{ repository { name } }")


class TestGetCommentStatus:
    """Test _get_comment_status() method"""

    def test_get_comment_status_open(self, client, mock_review_comment, sample_thread_data):
        """Test getting status for an open comment"""
        # Mock the comment to have ID from sample data (open thread)
        mock_review_comment.id = 12345

        with patch.object(client, "_graphql_query", return_value=sample_thread_data["data"]):
            status = client._get_comment_status(mock_review_comment)

            assert status == CommentStatus.OPEN

    def test_get_comment_status_resolved(self, client, mock_review_comment, sample_thread_data):
        """Test getting status for a resolved comment"""
        # Mock the comment to have ID from sample data (resolved thread)
        mock_review_comment.id = 67890

        with patch.object(client, "_graphql_query", return_value=sample_thread_data["data"]):
            status = client._get_comment_status(mock_review_comment)

            assert status == CommentStatus.RESOLVED

    def test_get_comment_status_caching(self, client, mock_review_comment, sample_thread_data):
        """Test that comment status is cached"""
        mock_review_comment.id = 12345

        with patch.object(client, "_graphql_query", return_value=sample_thread_data["data"]) as mock_query:
            # First call - should query GraphQL
            status1 = client._get_comment_status(mock_review_comment)

            # Second call - should use cache
            status2 = client._get_comment_status(mock_review_comment)

            assert status1 == status2
            # GraphQL should only be called once
            assert mock_query.call_count == 1

    def test_get_comment_status_not_found(self, client, mock_review_comment):
        """Test getting status for comment not in any thread"""
        mock_review_comment.id = 99999  # Not in threads

        mock_data = {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": []
                    }
                }
            }
        }

        with patch.object(client, "_graphql_query", return_value=mock_data):
            status = client._get_comment_status(mock_review_comment)

            # Should default to OPEN if not found
            assert status == CommentStatus.OPEN

    def test_get_comment_status_graphql_failure(self, client, mock_review_comment):
        """Test fallback behavior when GraphQL fails"""
        with patch.object(client, "_graphql_query", side_effect=Exception("API error")):
            status = client._get_comment_status(mock_review_comment)

            # Should fall back to OPEN on error
            assert status == CommentStatus.OPEN


class TestCreateCommentReply:
    """Test create_comment_reply() method"""

    def test_create_review_comment_reply(self, client):
        """Test creating a threaded reply to a review comment"""
        mock_pr = Mock()
        mock_reply = Mock()
        mock_reply.id = 99999
        mock_reply.html_url = "https://github.com/test/test/pull/1#discussion_r99999"
        mock_reply.body = "Test reply"

        mock_review_comment = Mock()
        mock_review_comment.id = 12345

        mock_pr.get_review_comments.return_value = [mock_review_comment]
        mock_pr.create_review_comment_reply.return_value = mock_reply

        with patch.object(client, "get_pull_request", return_value=mock_pr):
            result = client.create_comment_reply(
                comment_id="12345",
                pr_number=1,
                body="Test reply"
            )

            assert result["id"] == "99999"
            assert result["type"] == "review_comment_reply"
            mock_pr.create_review_comment_reply.assert_called_once_with(
                comment_id=12345,
                body="Test reply"
            )

    def test_create_issue_comment_reply(self, client):
        """Test creating a reply to an issue comment"""
        mock_pr = Mock()
        mock_reply = Mock()
        mock_reply.id = 88888
        mock_reply.html_url = "https://github.com/test/test/pull/1#issuecomment-88888"
        mock_reply.body = "> Replying to comment 67890\n\nTest reply"

        mock_issue_comment = Mock()
        mock_issue_comment.id = 67890

        mock_pr.get_review_comments.return_value = []  # No review comments
        mock_pr.get_issue_comments.return_value = [mock_issue_comment]
        mock_pr.create_issue_comment.return_value = mock_reply

        with patch.object(client, "get_pull_request", return_value=mock_pr):
            result = client.create_comment_reply(
                comment_id="67890",
                pr_number=1,
                body="Test reply"
            )

            assert result["id"] == "88888"
            assert result["type"] == "issue_comment"
            mock_pr.create_issue_comment.assert_called_once()

    def test_create_comment_reply_not_found(self, client):
        """Test error when comment ID not found"""
        mock_pr = Mock()
        mock_pr.get_review_comments.return_value = []
        mock_pr.get_issue_comments.return_value = []

        with patch.object(client, "get_pull_request", return_value=mock_pr):
            with pytest.raises(ValueError, match="Comment .* not found"):
                client.create_comment_reply(
                    comment_id="99999",
                    pr_number=1,
                    body="Test reply"
                )


class TestResolveThread:
    """Test resolve_thread() method"""

    def test_resolve_thread_success(self, client):
        """Test successfully resolving an open thread"""
        # Mock query response (thread is open)
        query_response = {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": [
                            {
                                "id": "PRRT_test",
                                "isResolved": False,
                                "comments": {
                                    "nodes": [{"databaseId": 12345}]
                                }
                            }
                        ]
                    }
                }
            }
        }

        # Mock mutation response (thread now resolved)
        mutation_response = {
            "resolveReviewThread": {
                "thread": {
                    "id": "PRRT_test",
                    "isResolved": True
                }
            }
        }

        with patch.object(client, "_graphql_query", return_value=query_response):
            with patch.object(client, "_graphql_mutation", return_value=mutation_response):
                result = client.resolve_thread(
                    comment_id="12345",
                    pr_number=1
                )

                assert result["status"] == "resolved"
                assert result["is_resolved"] is True
                assert result["thread_id"] == "PRRT_test"

    def test_resolve_thread_already_resolved(self, client):
        """Test resolving a thread that's already resolved"""
        query_response = {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": [
                            {
                                "id": "PRRT_test",
                                "isResolved": True,  # Already resolved
                                "comments": {
                                    "nodes": [{"databaseId": 12345}]
                                }
                            }
                        ]
                    }
                }
            }
        }

        with patch.object(client, "_graphql_query", return_value=query_response):
            result = client.resolve_thread(
                comment_id="12345",
                pr_number=1
            )

            assert result["status"] == "already_resolved"
            assert result["is_resolved"] is True

    def test_resolve_thread_not_found(self, client):
        """Test error when comment's thread not found"""
        query_response = {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": []
                    }
                }
            }
        }

        with patch.object(client, "_graphql_query", return_value=query_response):
            with pytest.raises(ValueError, match="No review thread found"):
                client.resolve_thread(
                    comment_id="99999",
                    pr_number=1
                )

    def test_resolve_thread_mutation_fails(self, client):
        """Test error when GraphQL mutation fails"""
        query_response = {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": [
                            {
                                "id": "PRRT_test",
                                "isResolved": False,
                                "comments": {
                                    "nodes": [{"databaseId": 12345}]
                                }
                            }
                        ]
                    }
                }
            }
        }

        with patch.object(client, "_graphql_query", return_value=query_response):
            with patch.object(client, "_graphql_mutation", side_effect=Exception("API error")):
                with pytest.raises(Exception, match="Failed to resolve thread"):
                    client.resolve_thread(
                        comment_id="12345",
                        pr_number=1
                    )

    def test_resolve_thread_clears_cache(self, client):
        """Test that resolving a thread clears its status cache"""
        # Pre-populate cache
        client._thread_status_cache["12345"] = CommentStatus.OPEN

        query_response = {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "nodes": [
                            {
                                "id": "PRRT_test",
                                "isResolved": False,
                                "comments": {
                                    "nodes": [{"databaseId": 12345}]
                                }
                            }
                        ]
                    }
                }
            }
        }

        mutation_response = {
            "resolveReviewThread": {
                "thread": {
                    "id": "PRRT_test",
                    "isResolved": True
                }
            }
        }

        with patch.object(client, "_graphql_query", return_value=query_response):
            with patch.object(client, "_graphql_mutation", return_value=mutation_response):
                client.resolve_thread(comment_id="12345", pr_number=1)

                # Cache should be cleared
                assert "12345" not in client._thread_status_cache


class TestWorkingFunctions:
    """Regression tests for functions that already worked"""

    def test_get_pr_diff(self, client):
        """Test get_pr_diff() returns formatted diff"""
        mock_pr = Mock()
        mock_file = Mock()
        mock_file.filename = "test.py"
        mock_file.patch = "+++ new line\n--- old line"

        mock_pr.get_files.return_value = [mock_file]

        with patch.object(client, "get_pull_request", return_value=mock_pr):
            diff = client.get_pr_diff(pr_number=1)

            assert "diff --git a/test.py b/test.py" in diff
            assert "+++ new line" in diff

    def test_get_file_content(self, client):
        """Test get_file_content() returns file content"""
        mock_content = Mock()
        mock_content.decoded_content = b"print('hello')"

        mock_repo = Mock()
        mock_repo.get_contents.return_value = mock_content

        # Mock the private _repo attribute instead of the property
        client._repo = mock_repo

        content = client.get_file_content("test.py")

        assert content == "print('hello')"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
