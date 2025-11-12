# Troubleshooting Guide

Common issues and solutions for the GitHub PR Comments MCP server.

## Installation Issues

### MCP Server Not Showing Up

**Symptoms:** Claude doesn't see the MCP tools after configuration.

**Solutions:**

1. **Check Configuration File Location:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Validate JSON Syntax:**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python3 -m json.tool
   ```

3. **Check Python Path:**
   ```bash
   ls -la ~/.venvs/github-pr-mcp/bin/python
   # Should exist and be executable
   ```

4. **Restart Claude:**
   - Quit Claude completely (not just close window)
   - Restart Claude Desktop or Claude Code CLI

5. **Check Wrapper Permissions (Claude Code CLI):**
   ```bash
   ls -la ~/.claude/mcp-servers/github-pr-comments.py
   # Should show: -rwxr-xr-x
   ```

### Tools Appear But Don't Work

**Symptoms:** Tools are listed but fail when called.

**Solutions:**

1. **Check GitHub Token:**
   ```bash
   # Test token
   curl -H "Authorization: token ghp_your_token" https://api.github.com/user
   ```

2. **Check Logs:**
   ```bash
   tail -f /tmp/github-pr-mcp.log
   ```

3. **Verify Package Installation:**
   ```bash
   ~/.venvs/github-pr-mcp/bin/python -c "import mcp_server; print('OK')"
   ```

4. **Test Server Manually:**
   ```bash
   ~/.venvs/github-pr-mcp/bin/python -m mcp_server.server
   # Should see startup message
   ```

### Import Errors

**Symptoms:** `ModuleNotFoundError` or `ImportError`

**Solutions:**

1. **Reinstall Package:**
   ```bash
   source ~/.venvs/github-pr-mcp/bin/activate
   pip install -e /path/to/claude_mcp_agent_github_comments
   ```

2. **Check Python Version:**
   ```bash
   ~/.venvs/github-pr-mcp/bin/python --version
   # Should be 3.10+
   ```

3. **Check Dependencies:**
   ```bash
   ~/.venvs/github-pr-mcp/bin/python -c "import github, mcp; print('OK')"
   ```

## Runtime Issues

### Repository Not Auto-Detected

**Symptoms:** Error: "Repository could not be determined"

**Solutions:**

1. **Check Git Remote:**
   ```bash
   git remote get-url origin
   # Should show a GitHub URL
   ```

2. **Explicitly Specify Repository:**
   Ask Claude: "Fetch comments from PR 72 in owner/repo"

3. **Check You're in a Git Repo:**
   ```bash
   git status
   # Should not say "not a git repository"
   ```

### Comment Not Found

**Symptoms:** Error: "Comment XYZ not found in PR 123"

**Solutions:**

1. **Verify Comment ID:**
   ```bash
   # Fetch all comments first to get valid IDs
   ```
   Ask Claude: "Show me all comments on PR 123"

2. **Check Comment Belongs to PR:**
   The comment might be from a different PR.

3. **Comment May Be Deleted:**
   The comment might have been deleted since you got the ID.

### "Working Tree is Dirty"

**Symptoms:** `apply_code_fix` fails with working tree error

**Solutions:**

1. **Commit or Stash Changes:**
   ```bash
   git status
   git add .
   git commit -m "WIP"
   # Or: git stash
   ```

2. **Clean Working Directory:**
   The tool requires a clean working tree for safety.

### Rate Limiting

**Symptoms:** Error: "API rate limit exceeded"

**Solutions:**

1. **Check Rate Limit Status:**
   ```bash
   curl -H "Authorization: token ghp_your_token" https://api.github.com/rate_limit
   ```

2. **Use Authenticated Requests:**
   Ensure `GITHUB_TOKEN` is set (provides 5000 requests/hour vs 60)

3. **Add Delays:**
   Wait a few minutes between large batch operations

4. **Use GitHub App Token:**
   Consider using a GitHub App token for higher limits

## Configuration Issues

### Wrong Repository Detected

**Symptoms:** Auto-detection picks wrong repo

**Solutions:**

1. **Check Current Directory:**
   ```bash
   pwd
   git remote get-url origin
   ```

2. **Change Directory:**
   Navigate to the correct repository before using tools

3. **Explicitly Specify Repository:**
   Always provide the `repo` parameter in your requests

### Token Permissions Issues

**Symptoms:** Error: "Resource not accessible by integration"

**Solutions:**

1. **Check Token Scopes:**
   Token needs `repo` scope for private repos or `public_repo` for public repos

2. **Create New Token:**
   Visit https://github.com/settings/tokens
   - Select `repo` scope
   - Save token securely

3. **Update Configuration:**
   Replace token in `claude_desktop_config.json` or wrapper script

## Logging and Debugging

### Enable Detailed Logging

Add to your MCP configuration:

```json
{
  "env": {
    "GITHUB_TOKEN": "ghp_your_token",
    "LOG_LEVEL": "DEBUG",
    "MCP_LOG_FILE": "/tmp/github-pr-mcp.log"
  }
}
```

### View Logs in Real-Time

```bash
tail -f /tmp/github-pr-mcp.log
```

### Check Claude's MCP Logs

```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log

# Linux
tail -f ~/.cache/Claude/logs/mcp*.log
```

### Usage Statistics

```bash
# Count total tool calls
grep "Tool called" /tmp/github-pr-mcp.log | wc -l

# Most used tools
grep "Tool called" /tmp/github-pr-mcp.log | cut -d':' -f4 | sort | uniq -c | sort -nr
```

## Common Error Messages

### "GITHUB_TOKEN environment variable is required"

**Solution:** Set token in configuration:
```json
{"env": {"GITHUB_TOKEN": "ghp_your_token_here"}}
```

### "No review thread found containing comment X"

**Solution:** Only review comments (not issue comments) have resolvable threads. Use `fetch_pr_comments` to check comment type.

### "Thread X resolution failed"

**Solution:** You may not have permission to resolve threads. Check repository access rights.

### "Failed to execute GraphQL query"

**Solution:**
- Check `gh` CLI is installed: `which gh`
- Authenticate: `gh auth login`
- Verify token has GraphQL access

## Getting Help

If you're still stuck:

1. **Check Logs:** Always check `/tmp/github-pr-mcp.log` first
2. **GitHub Issues:** https://github.com/MarkEnverus/claude-mcp-agent-github-comments/issues
3. **Verify Installation:** Run through [Installation Guide](./installation.md) again
4. **Test Components:** Use `Test` sections in docs to isolate the problem

## Claude Code Tips

### Repeated Command Approvals

Create `~/.claude/CLAUDE.md` with pre-approved commands:

```markdown
# My Claude Code Preferences

## Bash Command Approvals

### Pre-approved commands (never ask):
- git status
- git diff
- git log
- pytest*
- npm test

### Pre-approved in my repos:
- Any commands in /Users/YOUR_USER/repos/ are pre-approved for:
  - git operations (except push)
  - test execution
  - linting/formatting
```

Claude will remember these approvals!

---

For more help, see [Usage Guide](./usage.md) or [Installation Guide](./installation.md).
