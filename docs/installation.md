# Installation Guide

This guide covers installing the GitHub PR Comments MCP server for Claude Desktop and Claude Code CLI.

## Prerequisites

- Python 3.10+
- `uv` or `pip` for package management
- GitHub personal access token with `repo` scope
- Git repository (for auto-detection feature)

## Quick Install

### Option 1: Automated Installer (Recommended)

```bash
cd claude_mcp_agent_github_comments
./scripts/install-mcp-wrapper.sh
```

The installer will:
1. Create a venv at `~/.venvs/github-pr-mcp`
2. Install the package with `uv pip install -e .`
3. Create wrapper script at `~/.claude/mcp-servers/github-pr-comments.py`

### Option 2: Manual Installation

```bash
# Create virtual environment
uv venv ~/.venvs/github-pr-mcp
source ~/.venvs/github-pr-mcp/bin/activate

# Install package
cd claude_mcp_agent_github_comments
uv pip install -e .
```

## Configuration

### For Claude Desktop

Add to your Claude MCP settings file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "github-pr-comments": {
      "command": "/Users/YOUR_USER/.venvs/github-pr-mcp/bin/python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here"
      }
    }
  }
}
```

**Note**: `GITHUB_REPO` is now optional and will be auto-detected from your git remote!

### For Claude Code CLI

Copy the template wrapper:

```bash
cp scripts/github-pr-comments-template.py ~/.claude/mcp-servers/github-pr-comments.py
chmod +x ~/.claude/mcp-servers/github-pr-comments.py
```

Edit `~/.claude/mcp-servers/github-pr-comments.py` and set your token:

```python
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "your-token-here")
# GITHUB_REPO is auto-detected - no need to set!
```

Restart Claude Code CLI for changes to take effect.

## Verify Installation

### Test 1: Check Server Starts

```bash
~/.venvs/github-pr-mcp/bin/python -m mcp_server.server
# Should see: "Starting GitHub PR Comment MCP Server"
# Press Ctrl+C to stop
```

### Test 2: Check from Claude

Open Claude and ask:
```
What MCP tools are available?
```

You should see tools prefixed with `mcp__github-pr-comments__`.

### Test 3: Test Auto-Detection

Navigate to a git repository and verify:
```bash
~/.venvs/github-pr-mcp/bin/python -c "from mcp_server.utils.git_detector import detect_github_repo; print(detect_github_repo())"
# Should print: owner/repo
```

### Test 4: Use a Tool

In Claude:
```
Use the github-pr-comments MCP to fetch comments from PR 72
```

Claude should auto-detect your repository from git!

## Enable Logging (Optional)

Add logging configuration to track usage:

```json
{
  "mcpServers": {
    "github-pr-comments": {
      "command": "/Users/YOUR_USER/.venvs/github-pr-mcp/bin/python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "GITHUB_TOKEN": "ghp_your_token_here",
        "LOG_LEVEL": "INFO",
        "MCP_LOG_FILE": "/tmp/github-pr-mcp.log"
      }
    }
  }
}
```

View logs:
```bash
tail -f /tmp/github-pr-mcp.log
```

## Available Tools

Once installed, these MCP tools are available:

- `fetch_pr_comments` - Fetch and filter PR comments
- `get_comment_context` - Get code context around comments
- `analyze_comment_validity` - Check if issues still exist
- `batch_analyze_comments` - Analyze multiple comments
- `prepare_comment_decisions` - Interactive decision workflow
- `execute_comment_decision` - Execute user decisions
- `bulk_close_comments` - Fast bulk operations
- `apply_code_fix` - Apply code fixes with commits
- `get_pr_diff` - Get full PR diff
- `create_comment_reply` - Reply to comments
- `resolve_thread` - Resolve comment threads

## Uninstall

```bash
# Remove package
pip uninstall github-pr-comment-agent

# Remove from Claude config
# Edit: ~/Library/Application Support/Claude/claude_desktop_config.json
# Remove the "github-pr-comments" section

# Restart Claude
```

## Next Steps

See [Usage Guide](./usage.md) for workflows and examples.
