# Bug Fix: Repository Isolation

## Summary

Fixed critical bug where the MCP server's singleton pattern was ignoring the explicit `repo` parameter, causing it to return data from the wrong repository.

## Problem

### User Report
> "The MCP tool is still returning the wrong repository's data even though I specified repo='enverus-nv/genai-idp'. This is clearly a bug in the MCP tool itself - it's ignoring the explicit repo parameter."

### Root Cause

**Location:** `mcp_server/tools/github_api.py:523-564`

The `get_github_client()` function used a global singleton pattern that cached only **one** client instance:

```python
# BEFORE (buggy code)
_client: GitHubAPIClient | None = None

def get_github_client(token: str | None = None, repo: str | None = None) -> GitHubAPIClient:
    global _client

    if _client is None:  # Only creates client ONCE
        # ... initialization
        _client = GitHubAPIClient(token=token, repo=repo)

    return _client  # Always returns same cached client
```

**Issue:** Once initialized with repository A, all subsequent calls (even with `repo="B"`) would return the client for repository A.

### Impact

1. Users working with multiple repositories would get data from the wrong repo
2. Explicit `repo=` parameters were silently ignored after the first call
3. Auto-detection from git would "lock in" the first repo for the entire session
4. Security concern: Users might accidentally post comments to the wrong repository

## Solution

Changed from a single global singleton to a **per-repository cache**:

```python
# AFTER (fixed code)
_clients: dict[str, GitHubAPIClient] = {}

def get_github_client(token: str | None = None, repo: str | None = None) -> GitHubAPIClient:
    global _clients

    token = token or os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GitHub token required (GITHUB_TOKEN env var)")

    repo = get_repo_with_fallback(repo)
    if not repo:
        raise ValueError("Repository could not be determined...")

    # Return cached client for this repo, or create new one
    if repo not in _clients:
        _clients[repo] = GitHubAPIClient(token=token, repo=repo)

    return _clients[repo]
```

### Key Changes

1. **Per-repo cache:** `_clients` is now a `dict[str, GitHubAPIClient]` instead of a single instance
2. **Repo-specific lookup:** Each repository gets its own client instance
3. **Preserved caching:** Same repository still reuses the cached client (performance)
4. **Isolated state:** Each client has its own thread status cache

## Testing

Created comprehensive integration test suite: `tests/test_repo_isolation.py`

### Test Coverage

1. **Repository Isolation**
   - Different repos get different client instances
   - Same repo reuses cached client
   - Cache isolation (thread status caches are independent)
   - Explicit repo parameter overrides auto-detection
   - Sequential access to multiple repos

2. **Tool Integration**
   - `fetch_pr_comments()` respects repo parameter
   - `bulk_close_comments()` respects repo parameter
   - Multiple tools reuse same client for same repo

3. **Regression Test**
   - Exact bug scenario documented and verified

### Test Results

```bash
$ .venv/bin/python -m pytest tests/test_repo_isolation.py -v
============================= test session starts ==============================
collected 9 items

tests/test_repo_isolation.py::TestRepositoryIsolation::test_different_repos_get_different_clients PASSED [ 11%]
tests/test_repo_isolation.py::TestRepositoryIsolation::test_same_repo_gets_cached_client PASSED [ 22%]
tests/test_repo_isolation.py::TestRepositoryIsolation::test_cache_isolation PASSED [ 33%]
tests/test_repo_isolation.py::TestRepositoryIsolation::test_explicit_repo_overrides_auto_detection PASSED [ 44%]
tests/test_repo_isolation.py::TestRepositoryIsolation::test_multiple_repos_sequential_access PASSED [ 55%]
tests/test_repo_isolation.py::TestToolsRespectRepoParameter::test_fetch_pr_comments_respects_repo PASSED [ 66%]
tests/test_repo_isolation.py::TestToolsRespectRepoParameter::test_bulk_close_comments_respects_repo PASSED [ 77%]
tests/test_repo_isolation.py::TestToolsRespectRepoParameter::test_multiple_tools_use_same_client_for_same_repo PASSED [ 88%]
tests/test_repo_isolation.py::TestRegressionBugScenarios::test_bug_scenario_explicit_repo_ignored PASSED [100%]

============================== 9 passed in 1.19s
```

All existing tests also pass:

```bash
$ .venv/bin/python -m pytest tests/test_github_api.py -v
============================== 18 passed in 0.73s ===============================
```

## Verification

### No Hardcoded Values

Verified that the codebase has **no hardcoded repositories, tokens, or user-specific values** in the actual code:

- GitHub API endpoint: Uses standard `https://api.github.com` (correct)
- Repository names: All dynamically determined via parameters or auto-detection
- Tokens: Only referenced from environment variables (`GITHUB_TOKEN`)
- Examples in docs: Use placeholder values like `owner/repo` or `MarkEnverus/my-repo`

### Code Locations Verified

- `mcp_server/tools/github_api.py` - Core fix applied
- `mcp_server/tools/comments.py` - Passes repo to client correctly
- `mcp_server/tools/interactive.py` - Passes repo to client correctly
- `mcp_server/tools/analysis.py` - Passes repo to client correctly
- `mcp_server/tools/code_ops.py` - Passes repo to client correctly

## Migration Notes

This is a **backward-compatible fix**:

- Existing code will work without changes
- Single-repository workflows are unaffected
- Multi-repository workflows now work correctly
- No API changes required

## Example Usage

### Before (Buggy Behavior)

```python
# First call - initializes client for repo A
client = get_github_client(repo="owner-a/repo-a")

# Second call - IGNORES repo parameter, returns client for repo A
client = get_github_client(repo="owner-b/repo-b")  # BUG: Still uses repo A!
```

### After (Fixed Behavior)

```python
# First call - initializes client for repo A
client_a = get_github_client(repo="owner-a/repo-a")

# Second call - Creates new client for repo B
client_b = get_github_client(repo="owner-b/repo-b")  # Works correctly!

assert client_a is not client_b
assert client_a.repo_name == "owner-a/repo-a"
assert client_b.repo_name == "owner-b/repo-b"
```

## Files Changed

1. **Modified:**
   - `mcp_server/tools/github_api.py:523-564` - Fixed singleton pattern

2. **Created:**
   - `tests/test_repo_isolation.py` - Comprehensive integration tests
   - `docs/bugfix-repo-isolation.md` - This document

## Commit Message Suggestion

```
fix: Repository isolation in GitHub API client singleton

Fixed critical bug where get_github_client() singleton was ignoring
the repo parameter after first initialization, causing data leakage
between repositories.

Changes:
- Replaced single _client singleton with per-repo _clients dict
- Each repository now gets its own cached client instance
- Explicit repo parameter is now respected correctly
- Added comprehensive integration test suite

Fixes: Repository data leakage bug reported by users
Tests: tests/test_repo_isolation.py (9 tests, all passing)
```

## Related Issues

- User report: "MCP tool returns wrong repository's data even with explicit repo parameter"
- Security: Prevents accidental cross-repository operations
- Reliability: Ensures explicit parameters are respected

## Future Improvements

Consider adding:

1. **Cache eviction:** Add TTL or max size to prevent unbounded memory growth
2. **Cache clearing:** Provide API to manually clear client cache if needed
3. **Monitoring:** Log cache hits/misses for debugging
4. **Token per repo:** Support different tokens for different repositories
