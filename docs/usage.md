# Usage Guide

This guide covers common workflows and examples for using the GitHub PR Comments MCP server.

## Basic Usage

### Fetch Comments

```
"Show me all Copilot comments on PR 72"
"Fetch open comments from github-advanced-security bot"
```

The MCP server will automatically:
- Detect your repository from git remote
- Filter by the specified criteria
- Return structured comment data

### Interactive Review Workflow

```
"Review uncertain Copilot comments on PR 72 and let me decide what to do"
```

This triggers the interactive workflow:
1. Fetches and analyzes comments
2. Presents each uncertain comment with context
3. Asks you to choose: Fix, Dismiss, or Skip
4. Executes your decision (posts replies, resolves threads)

### Bulk Operations

```
"Close all resolved Copilot comments on PR 80 with a generic acknowledgment"
```

Fast bulk close without individual analysis - useful for cleanup.

## Common Workflows

### Workflow 1: Review New PR Comments

```
You: "I just got a bunch of Copilot comments on PR 72. Help me review them."

Claude will:
1. Fetch all Copilot comments
2. Analyze each for validity
3. Show you summaries
4. Help you respond appropriately
```

### Workflow 2: Fix Valid Issues

```
You: "Comment ID 12345 on PR 72 looks valid. Can you show me the code context?"

Claude will:
1. Get the file, line number, and surrounding code
2. Show the diff hunk
3. Help you understand the issue
4. Optionally suggest a fix
```

### Workflow 3: Batch Close Outdated Comments

```
You: "Batch close all Copilot comments older than 30 days on PR 72"

Claude will:
1. Filter comments by age
2. Post acknowledgment replies
3. Resolve all threads
4. Show summary of actions
```

## Available Tools

### `fetch_pr_comments`
Fetch and filter PR comments.

**Parameters:**
- `pr_number` (required): PR number
- `repo` (optional): Repository (auto-detected)
- `filters` (optional): Filter criteria
  - `authors`: List of author names
  - `status`: "open" or "resolved"
  - `keywords`: Search keywords
  - `min_age_days`: Minimum age in days

### `get_comment_context`
Get code context around a comment.

**Parameters:**
- `comment_id` (required): Comment ID
- `pr_number` (required): PR number
- `repo` (optional): Repository (auto-detected)
- `lines_before` (optional): Lines before (default: 10)
- `lines_after` (optional): Lines after (default: 10)

### `analyze_comment_validity`
Check if a comment's issue still exists.

**Parameters:**
- `comment_id` (required): Comment ID
- `pr_number` (required): PR number
- `repo` (optional): Repository (auto-detected)

### `batch_analyze_comments`
Analyze multiple comments with categorization.

**Parameters:**
- `pr_number` (required): PR number
- `repo` (optional): Repository (auto-detected)
- `filters` (optional): Same as fetch_pr_comments

### `prepare_comment_decisions`
Interactive workflow for uncertain comments.

**Parameters:**
- `pr_number` (required): PR number
- `repo` (optional): Repository (auto-detected)
- `fast_mode` (optional): Use pattern matching instead of LLM
- `filters` (optional): Filter criteria

### `execute_comment_decision`
Execute a user decision on a comment.

**Parameters:**
- `comment_id` (required): Comment ID
- `pr_number` (required): PR number
- `action` (required): "fix", "dismiss", or "skip"
- `repo` (optional): Repository (auto-detected)
- `message` (optional): Custom reply message

### `bulk_close_comments`
Fast bulk close with generic message.

**Parameters:**
- `pr_number` (required): PR number
- `repo` (optional): Repository (auto-detected)
- `message` (optional): Custom message
- `filters` (optional): Filter criteria
- `resolve_threads` (optional): Whether to resolve (default: true)

### `get_pr_diff`
Get full unified diff for PR.

**Parameters:**
- `pr_number` (required): PR number
- `repo` (optional): Repository (auto-detected)

### `create_comment_reply`
Reply to a comment thread.

**Parameters:**
- `comment_id` (required): Comment ID
- `pr_number` (required): PR number
- `message` (required): Reply text
- `repo` (optional): Repository (auto-detected)

### `resolve_thread`
Mark a comment thread as resolved.

**Parameters:**
- `comment_id` (required): Comment ID
- `pr_number` (required): PR number
- `repo` (optional): Repository (auto-detected)
- `reason` (optional): Resolution reason

### `apply_code_fix`
Apply a code fix with git commit.

**Parameters:**
- `file_path` (required): File path
- `line_number` (required): Line number
- `fix_content` (required): New code
- `repo` (optional): Repository (auto-detected)
- `commit_message` (optional): Custom commit message
- `repo_path` (optional): Local repo path

## Tips

### Repository Auto-Detection

The server automatically detects your repository from `git remote get-url origin`. If you're not in a git repo or want to override:

```
"Fetch comments from PR 72 in owner/repo"
```

Explicitly specify the repo parameter.

### Fast vs Thorough Mode

For `prepare_comment_decisions`:
- **Fast mode** (~5sec): Pattern matching, good for obvious issues
- **Thorough mode** (~60sec): LLM analysis, better for complex cases

Always ask the user which mode they prefer!

### Filtering Best Practices

- Use `authors` filter for bot-specific reviews
- Use `status: "open"` to focus on unresolved comments
- Use `keywords` to find specific types of issues
- Use `min_age_days` to ignore recent comments that might not be addressed yet

## Error Handling

If a tool fails:
- Check the error message in Claude's response
- Verify you're in a git repository (for auto-detection)
- Check `GITHUB_TOKEN` environment variable
- Look at logs: `tail -f /tmp/github-pr-mcp.log`

See [Troubleshooting](./troubleshooting.md) for common issues.
