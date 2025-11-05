# Installation & Usage Guide

## Global Installation

Install the MCP server globally so you can use it from anywhere (including Claude Desktop/Code).

### Method 1: Install with uv (Recommended)

```bash
cd /Users/mark.johnson/Desktop/source/repos/mark.johnson/claude_mcp_agent_github_comments

# Install globally
uv pip install -e . --system

# Or create a dedicated environment
uv venv ~/.venvs/github-pr-mcp
source ~/.venvs/github-pr-mcp/bin/activate
uv pip install -e .
```

### Method 2: Install with pip

```bash
cd /Users/mark.johnson/Desktop/source/repos/mark.johnson/claude_mcp_agent_github_comments
pip install -e .
```

## Claude Desktop/Code Configuration

Add to your Claude MCP settings file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "github-pr-comments": {
      "command": "/Users/mark.johnson/.venvs/github-pr-mcp/bin/python",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here",
        "GITHUB_REPO": "enverus-nv/genai-idp"
      }
    }
  }
}
```

**Or for system Python:**

```json
{
  "mcpServers": {
    "github-pr-comments": {
      "command": "python3",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here",
        "GITHUB_REPO": "enverus-nv/genai-idp"
      }
    }
  }
}
```

## Verify Installation

### Test 1: Check MCP Server Starts

```bash
# With venv
/Users/mark.johnson/.venvs/github-pr-mcp/bin/python -m mcp_server.server

# Should see: "Starting GitHub PR Comment MCP Server"
# Press Ctrl+C to stop
```

### Test 2: Check from Claude

Open Claude Desktop/Code and ask:
```
What MCP tools are available?
```

You should see:
- `mcp__github-pr-comments__fetch_pr_comments`
- `mcp__github-pr-comments__get_comment_context`
- `mcp__github-pr-comments__analyze_comment_smart`
- etc.

### Test 3: Use a Tool

In Claude:
```
Use the github-pr-comments MCP to fetch comments from PR 72 in enverus-nv/genai-idp
```

## Usage Tracking

The MCP server now logs all tool usage.

### Enable Detailed Logging

Edit your MCP config to add logging:

```json
{
  "mcpServers": {
    "github-pr-comments": {
      "command": "/Users/mark.johnson/.venvs/github-pr-mcp/bin/python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here",
        "GITHUB_REPO": "enverus-nv/genai-idp",
        "LOG_LEVEL": "INFO",
        "MCP_LOG_FILE": "/tmp/github-pr-mcp.log"
      }
    }
  }
}
```

### View Logs

```bash
# Watch logs in real-time
tail -f /tmp/github-pr-mcp.log

# Or view recent activity
cat /tmp/github-pr-mcp.log | grep "Tool called"
```

### Usage Statistics

```bash
# Count tool usage
grep "Tool called" /tmp/github-pr-mcp.log | wc -l

# See which tools are used most
grep "Tool called" /tmp/github-pr-mcp.log | cut -d':' -f4 | sort | uniq -c | sort -nr
```

## Troubleshooting

### Issue: MCP server not showing in Claude

**Check:**
1. Config file location is correct
2. JSON is valid (use `cat claude_desktop_config.json | python -m json.tool`)
3. Python path is correct
4. Restart Claude Desktop/Code

### Issue: Tools appear but don't work

**Check:**
1. GITHUB_TOKEN is valid
2. Logs for error messages: `tail -f /tmp/github-pr-mcp.log`
3. Network access to GitHub API

### Issue: Can't tell if MCP is being used

**Enable verbose logging:**

```bash
# Add to your shell profile (~/.zshrc or ~/.bashrc)
export MCP_DEBUG=1

# Then restart Claude
```

**Check logs:**

```bash
# See all MCP activity
tail -f ~/Library/Logs/Claude/mcp*.log

# Or check our server log
tail -f /tmp/github-pr-mcp.log
```

## Testing with Your PR

Once installed, in Claude Desktop/Code:

```
I'm working on PR 72 in enverus-nv/genai-idp.

Can you:
1. Fetch all bot comments using the github-pr-comments MCP
2. Use smart analysis to identify fixable issues
3. Show me the suggested fixes
```

Claude should automatically use the MCP tools!

## Comparing Multiple MCPs

To see which MCP servers are being used:

```bash
# List all MCP servers in config
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | grep -A 10 mcpServers

# Check logs for each
tail -f /tmp/github-pr-mcp.log       # This one
tail -f /tmp/python-mcp.log          # Your Python MCP

# Or enable MCP debug mode for all
export MCP_DEBUG=1
```

## Usage Patterns

**When MCP tools are used, you'll see in logs:**

```
2025-11-05 15:30:12 - INFO - Tool called: fetch_pr_comments
2025-11-05 15:30:12 - INFO - Arguments: {"pr_number": 72, "repo": "enverus-nv/genai-idp"}
2025-11-05 15:30:13 - INFO - Result: 9 comments fetched
2025-11-05 15:30:15 - INFO - Tool called: analyze_comment_smart
2025-11-05 15:30:15 - INFO - Arguments: {"comment_id": "2496256806", ...}
```

**When MCP is ignored, you'll see:**
- No log entries
- Claude uses built-in tools instead
- Check if tool names match exactly

## Uninstall

```bash
# Remove package
pip uninstall github-pr-comment-agent

# Remove from Claude config
# Edit: ~/Library/Application Support/Claude/claude_desktop_config.json
# Remove the "github-pr-comments" section

# Restart Claude
```

---

**Next Steps:**
1. Install globally with one of the methods above
2. Configure Claude Desktop/Code with MCP settings
3. Restart Claude
4. Test: "What MCP tools do I have?"
5. Use: "Analyze PR 72 with github-pr-comments MCP"
