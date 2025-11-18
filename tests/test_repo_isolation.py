"""
Integration tests for repository isolation

Tests that the MCP server correctly handles multiple repositories
and doesn't leak data between them due to singleton caching bugs.

This test suite was created to verify the fix for the bug where
the `get_github_client()` singleton cache was ignoring the `repo` parameter.
"""
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.tools.github_api import _clients, get_github_client


class TestRepositoryIsolation:
    """Test that client instances are isolated per repository"""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear the global client cache before each test"""
        _clients.clear()
        yield
        _clients.clear()

    def test_different_repos_get_different_clients(self):
        """Test that different repositories get separate client instances"""
        token = "test_token_123"

        with patch.dict(os.environ, {"GITHUB_TOKEN": token}):
            with patch("mcp_server.tools.github_api.Github"):
                with patch("mcp_server.tools.github_api.get_repo_with_fallback") as mock_fallback:
                    # First call with repo A
                    mock_fallback.return_value = "owner-a/repo-a"
                    client_a = get_github_client(token=token, repo="owner-a/repo-a")

                    # Second call with repo B
                    mock_fallback.return_value = "owner-b/repo-b"
                    client_b = get_github_client(token=token, repo="owner-b/repo-b")

                    # Should be different instances
                    assert client_a is not client_b
                    assert client_a.repo_name == "owner-a/repo-a"
                    assert client_b.repo_name == "owner-b/repo-b"

    def test_same_repo_gets_cached_client(self):
        """Test that the same repository reuses cached client"""
        token = "test_token_123"

        with patch.dict(os.environ, {"GITHUB_TOKEN": token}):
            with patch("mcp_server.tools.github_api.Github"):
                with patch("mcp_server.tools.github_api.get_repo_with_fallback") as mock_fallback:
                    mock_fallback.return_value = "owner/repo"

                    # Get client twice for same repo
                    client_1 = get_github_client(token=token, repo="owner/repo")
                    client_2 = get_github_client(token=token, repo="owner/repo")

                    # Should be the same instance (cached)
                    assert client_1 is client_2

    def test_cache_isolation(self):
        """Test that thread status cache is isolated per client"""
        token = "test_token_123"

        with patch.dict(os.environ, {"GITHUB_TOKEN": token}):
            with patch("mcp_server.tools.github_api.Github"):
                with patch("mcp_server.tools.github_api.get_repo_with_fallback") as mock_fallback:
                    # Create two clients for different repos
                    mock_fallback.return_value = "owner-a/repo-a"
                    client_a = get_github_client(token=token, repo="owner-a/repo-a")

                    mock_fallback.return_value = "owner-b/repo-b"
                    client_b = get_github_client(token=token, repo="owner-b/repo-b")

                    # Add data to cache of client A
                    from mcp_server.models import CommentStatus
                    client_a._thread_status_cache["comment_123"] = CommentStatus.OPEN

                    # Cache of client B should be independent
                    assert "comment_123" not in client_b._thread_status_cache

    def test_explicit_repo_overrides_auto_detection(self):
        """Test that explicit repo parameter takes precedence over auto-detection"""
        token = "test_token_123"

        with patch.dict(os.environ, {"GITHUB_TOKEN": token}):
            with patch("mcp_server.tools.github_api.Github"):
                with patch("mcp_server.tools.github_api.get_repo_with_fallback") as mock_fallback:
                    # Mock auto-detection to return a default repo
                    def fallback_side_effect(provided_repo):
                        # If repo is provided, return it; otherwise return auto-detected
                        return provided_repo if provided_repo else "auto-detected/repo"

                    mock_fallback.side_effect = fallback_side_effect

                    # Explicitly provide a repo
                    client = get_github_client(token=token, repo="explicit/repo")

                    # Should use the explicit repo, not auto-detected
                    assert client.repo_name == "explicit/repo"

    def test_multiple_repos_sequential_access(self):
        """
        Test sequential access to different repositories

        This simulates the bug scenario: Claude accesses repo A (auto-detected),
        then user explicitly requests repo B, but gets repo A's data instead.
        """
        token = "test_token_123"

        with patch.dict(os.environ, {"GITHUB_TOKEN": token}):
            with patch("mcp_server.tools.github_api.Github"):
                with patch("mcp_server.tools.github_api.get_repo_with_fallback") as mock_fallback:
                    def fallback_side_effect(provided_repo):
                        return provided_repo if provided_repo else "auto-detected/default-repo"

                    mock_fallback.side_effect = fallback_side_effect

                    # First, access auto-detected repo (simulates initial context)
                    client_auto = get_github_client(token=token)
                    assert client_auto.repo_name == "auto-detected/default-repo"

                    # Then, explicitly request a different repo
                    client_explicit = get_github_client(token=token, repo="user-provided/different-repo")

                    # CRITICAL: Should get the correct repo, not the auto-detected one
                    assert client_explicit.repo_name == "user-provided/different-repo"
                    assert client_explicit is not client_auto


class TestToolsRespectRepoParameter:
    """Test that MCP tools correctly use the repo parameter"""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear the global client cache before each test"""
        _clients.clear()
        yield
        _clients.clear()

    @pytest.fixture
    def mock_github_env(self):
        """Mock GitHub environment"""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
            with patch("mcp_server.tools.github_api.Github"):
                with patch("mcp_server.tools.github_api.get_repo_with_fallback") as mock_fallback:
                    def fallback_side_effect(provided_repo):
                        return provided_repo if provided_repo else "default/repo"

                    mock_fallback.side_effect = fallback_side_effect
                    yield mock_fallback

    @pytest.mark.asyncio
    async def test_fetch_pr_comments_respects_repo(self, mock_github_env):
        """Test that fetch_pr_comments uses the correct repository"""
        from mcp_server.tools.comments import fetch_pr_comments

        with patch("mcp_server.tools.github_api.GitHubAPIClient.get_all_pr_comments") as mock_get_comments:
            mock_get_comments.return_value = []

            # Call with explicit repo
            await fetch_pr_comments(pr_number=1, repo="user-repo/test-repo")

            # Verify the client was created for the correct repo
            assert "user-repo/test-repo" in _clients
            assert _clients["user-repo/test-repo"].repo_name == "user-repo/test-repo"

    @pytest.mark.asyncio
    async def test_bulk_close_comments_respects_repo(self, mock_github_env):
        """Test that bulk_close_comments uses the correct repository"""
        from mcp_server.tools.interactive import bulk_close_comments

        with patch("mcp_server.tools.github_api.GitHubAPIClient.get_all_pr_comments") as mock_get_comments:
            mock_get_comments.return_value = []

            # Call with explicit repo
            await bulk_close_comments(pr_number=1, repo="another-repo/test")

            # Verify the client was created for the correct repo
            assert "another-repo/test" in _clients
            assert _clients["another-repo/test"].repo_name == "another-repo/test"

    @pytest.mark.asyncio
    async def test_multiple_tools_use_same_client_for_same_repo(self, mock_github_env):
        """Test that multiple tools reuse the same client for the same repo"""
        from mcp_server.tools.comments import fetch_pr_comments, get_comment_context

        with patch("mcp_server.tools.github_api.GitHubAPIClient.get_all_pr_comments") as mock_get_comments:
            mock_get_comments.return_value = []

            # Call two different tools with same repo
            await fetch_pr_comments(pr_number=1, repo="shared-repo/test")

            # Second tool should reuse the same client
            initial_client = _clients["shared-repo/test"]

            try:
                await get_comment_context(comment_id="123", pr_number=1, repo="shared-repo/test")
            except ValueError:
                # Expected to fail (comment not found), but client should be reused
                pass

            # Verify same client instance was used
            assert _clients["shared-repo/test"] is initial_client


class TestRegressionBugScenarios:
    """
    Test specific bug scenarios reported by users

    These tests document the exact bug that was reported and verify the fix.
    """

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear the global client cache before each test"""
        _clients.clear()
        yield
        _clients.clear()

    def test_bug_scenario_explicit_repo_ignored(self):
        """
        Regression test for: MCP tool returns wrong repository's data

        User reported:
        "The MCP tool is still returning the wrong repository's data even though
        I specified repo='enverus-nv/genai-idp'. This is clearly a bug in the
        MCP tool itself - it's ignoring the explicit repo parameter."

        Root cause:
        - The singleton pattern in get_github_client() was caching the first client
        - Subsequent calls with different repo parameters were ignored
        - The same client instance was returned regardless of repo parameter
        """
        token = "test_token_123"

        with patch.dict(os.environ, {"GITHUB_TOKEN": token}):
            with patch("mcp_server.tools.github_api.Github"):
                with patch("mcp_server.tools.github_api.get_repo_with_fallback") as mock_fallback:
                    def fallback_side_effect(provided_repo):
                        return provided_repo

                    mock_fallback.side_effect = fallback_side_effect

                    # Step 1: Initial call (auto-detected or first call)
                    client_1 = get_github_client(token=token, repo="mark.johnson/claude-mcp")
                    assert client_1.repo_name == "mark.johnson/claude-mcp"

                    # Step 2: User explicitly provides different repo
                    # BUG: Before fix, this would return client_1 instead of creating new client
                    client_2 = get_github_client(token=token, repo="enverus-nv/genai-idp")

                    # VERIFY FIX: Should be a different client for different repo
                    assert client_2.repo_name == "enverus-nv/genai-idp"
                    assert client_2 is not client_1

                    # Step 3: Accessing original repo should return first client (cached)
                    client_3 = get_github_client(token=token, repo="mark.johnson/claude-mcp")
                    assert client_3 is client_1
                    assert client_3.repo_name == "mark.johnson/claude-mcp"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
