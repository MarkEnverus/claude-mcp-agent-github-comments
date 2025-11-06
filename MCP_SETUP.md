# MCP Server Setup for Claude Code CLI

This guide shows you how to install the GitHub PR Comments MCP server for use with Claude Code CLI.

## Quick Install (Recommended)

```bash
# Run the automated installer
cd claude_mcp_agent_github_comments
./scripts/install-mcp-wrapper.sh
```

The installer will:
1. Create a venv at `~/.venvs/github-pr-mcp`
2. Install the package with `uv pip install -e .`
3. Create wrapper script at `~/.claude/mcp-servers/github-pr-comments.py`

## Manual Setup

If you prefer manual installation:

### 1. Install the Package

```bash
# Create venv
uv venv ~/.venvs/github-pr-mcp
source ~/.venvs/github-pr-mcp/bin/activate

# Install package (editable mode)
cd claude_mcp_agent_github_comments
uv pip install -e .
```

### 2. Create MCP Wrapper

Copy the template to your MCP servers directory:

```bash
cp scripts/github-pr-comments-template.py ~/.claude/mcp-servers/github-pr-comments.py
chmod +x ~/.claude/mcp-servers/github-pr-comments.py
```

### 3. Configure Credentials

Edit `~/.claude/mcp-servers/github-pr-comments.py` and update:

```python
GITHUB_TOKEN = "your_github_token_here"
GITHUB_REPO = "owner/repo"
```

Or use environment variables:

```python
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "your-token-here")
GITHUB_REPO = os.getenv("GITHUB_REPO", "owner/repo")
```

### 4. Restart Claude Code CLI

The MCP server will be auto-discovered on next startup.

## Verify Installation

```bash
# Check logs
tail -f /tmp/github-pr-mcp.log

# Or check Claude Code debug logs
tail -f ~/.claude/debug/latest
```

You should see:
```
MCP server "github-pr-comments": Starting connection...
MCP server "github-pr-comments": Successfully connected
```

## Available Tools

Once installed, these tools are available:

- `mcp__github-pr-comments__fetch_pr_comments` - Fetch and filter PR comments
- `mcp__github-pr-comments__get_comment_context` - Get code context around comments
- `mcp__github-pr-comments__analyze_comment_validity` - Check if issue still exists
- `mcp__github-pr-comments__batch_analyze_comments` - Analyze multiple comments
- `mcp__github-pr-comments__apply_code_fix` - Apply code fixes
- `mcp__github-pr-comments__get_pr_diff` - Get full PR diff
- `mcp__github-pr-comments__create_comment_reply` - Reply to comments
- `mcp__github-pr-comments__resolve_thread` - Resolve comment threads

## Troubleshooting

### Server not showing up

Check if the wrapper is executable:
```bash
ls -la ~/.claude/mcp-servers/github-pr-comments.py
# Should show: -rwxr-xr-x
```

Test the wrapper directly:
```bash
~/.claude/mcp-servers/github-pr-comments.py
# Should start the server (Ctrl+C to stop)
```

### Import errors

Verify package installation:
```bash
~/.venvs/github-pr-mcp/bin/python -c "import mcp_server; print('OK')"
```

### Wrong Python version

Update `VENV_PATH` in the wrapper if you installed elsewhere:
```python
VENV_PATH = Path.home() / ".venvs" / "github-pr-mcp"
```

## For Distribution

When sharing this MCP server:

1. Users clone your repo
2. Run `./scripts/install-mcp-wrapper.sh`
3. Edit `~/.claude/mcp-servers/github-pr-comments.py` with their credentials
4. Restart Claude Code CLI

No hardcoded paths - everything uses `Path.home()` for portability!
