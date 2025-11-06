# Claude Desktop/Code Usage Tips

Common issues and solutions when working with Claude.

---

## 🔄 Issue 1: Having to Approve Same Commands Repeatedly

### **Problem:**
Claude keeps asking for approval for commands you've already approved:
```
Do you want to run: git status? [y/N]
Do you want to run: git status? [y/N]  ← AGAIN!?
```

### **Solution: Use `claudeMd` to Remember Approvals**

Claude Code has a feature where it can "remember" your approval decisions!

#### **Create Global Rules** (`~/.claude/CLAUDE.md`):

```bash
# Create or edit your global Claude config
mkdir -p ~/.claude
nano ~/.claude/CLAUDE.md
```

**Add these rules:**

```markdown
# My Claude Code Preferences

## Bash Command Approvals

Please remember when I have accepted bash commands.

### Pre-approved commands (never ask):
- git status
- git diff
- git log
- git branch
- ls
- pwd
- cat
- grep
- find
- tree
- which
- python --version

### Pre-approved patterns (never ask):
- git status*
- git diff*
- git log*
- pytest*
- python test_*.py
- npm test
- make test

### Environment-specific approvals:
For this user (mark.johnson):
- Any read-only git commands are approved
- pytest in any directory is approved
- Reading files with cat/head/tail is approved

## Specific to my repos:
- Any commands in /Users/mark.johnson/Desktop/source/repos/ are pre-approved for:
  - git operations (except push)
  - test execution
  - linting/formatting
  - local builds
```

#### **Project-Specific Rules** (`.claude/CLAUDE.md` in repo):

```bash
cd /Users/mark.johnson/Desktop/source/repos/mark.johnson/claude_mcp_agent_github_comments
mkdir -p .claude
nano .claude/CLAUDE.md
```

**Add:**

```markdown
# Project: GitHub PR Comment Agent

## Pre-approved for this project:
- All pytest commands
- All git read commands (status, diff, log)
- Python script execution in this directory
- uv/pip commands for package installation
- Reading any file in this repository
```

### **How It Works:**

Claude will read these files and remember your preferences. After setting this up:

✅ **Before:**
```
Run: git status? [y/N]
Run: git status? [y/N]  ← Asked again!
```

✅ **After:**
```
Running git status...  ← No prompt!
```

### **Additional Claude Code Settings:**

Edit: `~/.claude/settings.json`

```json
{
  "autoApprove": {
    "enabled": true,
    "commands": [
      "git status",
      "git diff",
      "git log",
      "ls",
      "pwd"
    ],
    "patterns": [
      "git status*",
      "git diff*",
      "pytest*"
    ]
  }
}
```

---

## 🔍 Issue 2: How to Know if Claude is Using Your MCPs

### **Problem:**
You build MCPs but can't tell if Claude is actually using them vs built-in tools.

### **Solution 1: Check Logs** (Best Method)

#### **For github-pr-comments MCP:**

```bash
# Real-time monitoring
tail -f /tmp/github-pr-mcp.log

# Or use our checker script
cd /Users/mark.johnson/Desktop/source/repos/mark.johnson/claude_mcp_agent_github_comments
./check_mcp_usage.sh
```

**What you'll see when it's used:**
```
2025-11-05 16:45:12 - Tool called: fetch_pr_comments
2025-11-05 16:45:12 - Arguments: {"pr_number": 72, ...}
2025-11-05 16:45:13 - Tool fetch_pr_comments completed successfully
```

**What you'll see when it's NOT used:**
```
(empty log file or no new entries)
```

#### **For claude-python-mcp:**

```bash
# Check if it logs (might need to configure)
ls -la ~/Library/Logs/Claude/mcp*.log

# Or check Claude's main MCP log
tail -f ~/Library/Logs/Claude/mcp-*.log
```

### **Solution 2: Watch Claude's Response**

Claude usually announces when using an MCP:

✅ **Using MCP:**
```
Claude: "I'll use the github-pr-comments MCP to fetch those comments..."
Claude: "Using the mcp__github-pr-comments__fetch_pr_comments tool..."
```

❌ **NOT Using MCP:**
```
Claude: "Let me search for that PR..."
Claude: "I'll analyze the comments..."  (no MCP mentioned)
```

### **Solution 3: Ask Claude Directly**

```
You: "What tools did you just use?"

Claude: "I used mcp__github-pr-comments__fetch_pr_comments and
         mcp__github-pr-comments__analyze_comment_smart"
```

### **Solution 4: Make MCP Usage Explicit**

Instead of:
```
"Analyze PR 72"
```

Say:
```
"Use the github-pr-comments MCP to analyze PR 72"
```

This forces Claude to use your MCP.

### **Solution 5: Add Usage Logging to Your MCP**

We already added this! Every time a tool is called, it logs:

```python
# In mcp_server/server.py (already added)
logger.info(f"Tool called: {name}")
logger.info(f"Tool {name} completed successfully")
```

So you can **always verify** with:
```bash
./check_mcp_usage.sh
```

### **Solution 6: Compare Before/After**

Enable logging for ALL MCPs:

```json
// In ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "claude-python-mcp": {
      "command": "...",
      "env": {
        "MCP_LOG_FILE": "/tmp/python-mcp.log"
      }
    },
    "github-pr-comments": {
      "command": "...",
      "env": {
        "MCP_LOG_FILE": "/tmp/github-pr-mcp.log"
      }
    }
  }
}
```

Then compare:
```bash
# Check both
tail -f /tmp/python-mcp.log &
tail -f /tmp/github-pr-mcp.log &

# Or use script for each
MCP_LOG_FILE=/tmp/python-mcp.log ./check_mcp_usage.sh
MCP_LOG_FILE=/tmp/github-pr-mcp.log ./check_mcp_usage.sh
```

---

## 🌐 Issue 3: Claude Hangs When Internet Drops

### **Problem:**
When your internet connection drops, Claude freezes/hangs and you lose context when reconnecting.

### **Solutions:**

#### **Solution 1: Soft Refresh (Keep Context)**

**Don't close the window!** Instead:

**Option A: Wait for Reconnection**
```
1. Claude shows: "Connection lost..."
2. Wait 30-60 seconds
3. Internet comes back
4. Claude auto-reconnects
5. Context preserved! ✅
```

**Option B: Force Reconnect**
```
1. Click the "Retry" or "Reconnect" button in Claude UI
2. Or refresh the conversation: Cmd+R (macOS) / Ctrl+R
3. Context usually preserved ✅
```

#### **Solution 2: Save Context Before It's Too Late**

**Create a backup while it's working:**

In Claude, say:
```
"Please summarize everything we've done in this conversation:
- Tasks completed
- Current file states
- Variables/config we set
- Next steps

Format as a detailed summary I can paste back to you."
```

Claude will generate a summary you can copy and paste into a new conversation if needed.

#### **Solution 3: Use Local-First Workflow**

**Work offline-friendly:**

1. **Save important outputs:**
   ```
   "Save all our fixes to /tmp/claude_backup.txt"
   ```

2. **Use files instead of just chat:**
   ```
   "Write all our changes to fix_plan.md"
   ```

3. **Commit frequently:**
   ```
   "Commit these changes now before we continue"
   ```

#### **Solution 4: Claude Code Offline Mode**

Claude Code has better offline handling:

```bash
# In ~/.claude/settings.json
{
  "offlineMode": {
    "enabled": true,
    "continueWithoutAPI": true
  }
}
```

This lets Claude Code continue with:
- File operations
- Git commands
- Bash commands
- MCP servers (if they're local)

Only API calls (Claude responses) need internet.

#### **Solution 5: Connection Quality Settings**

```bash
# In ~/.claude/settings.json
{
  "connection": {
    "timeout": 60000,
    "retries": 3,
    "keepAlive": true
  }
}
```

#### **Solution 6: Use a Connection Monitor**

```bash
# Create: ~/bin/claude-monitor.sh

#!/bin/bash
while true; do
    if ! ping -c 1 anthropic.com &> /dev/null; then
        echo "⚠️  Connection lost at $(date)"
        osascript -e 'display notification "Claude connection lost!" with title "Network Down"'
    fi
    sleep 10
done
```

Run in background:
```bash
chmod +x ~/bin/claude-monitor.sh
~/bin/claude-monitor.sh &
```

#### **Solution 7: Quick Recovery Steps**

**If Claude freezes:**

1. **Don't panic or close!**
2. **Check connection:**
   ```bash
   ping anthropic.com
   ```
3. **If connected, try:**
   - Click anywhere in Claude UI
   - Press Escape
   - Try typing a message
   - Cmd+R to refresh (keeps context)

4. **If truly hung:**
   - Take screenshot of conversation
   - Copy important text
   - Force quit: `killall Claude`
   - Reopen and paste context summary

#### **Solution 8: Context Preservation Trick**

**Before any network-heavy task:**

```
"Before we continue, can you:
1. List all files we've modified with their paths
2. List all environment variables we set
3. List our current git branch and status
4. Summarize where we are in the task

I want to save this as a checkpoint."
```

Copy the response. If connection drops, paste it to new Claude.

---

## 🎯 Pro Tips for Stable Claude Sessions

### **1. Keep Context Manageable**

Long conversations = more likely to have issues.

**Periodically:**
```
"Let's create a summary of our progress and start a fresh conversation"
```

### **2. Use Git as Backup**

Commit frequently:
```
"Commit our changes with a descriptive message"
```

If Claude hangs, your work is safe in git.

### **3. Save Critical Outputs**

```
"Write this analysis to /tmp/analysis.md so I don't lose it"
```

### **4. Test Internet-Dependent Tasks**

Before long operations:
```bash
ping -c 5 anthropic.com
```

If unstable, wait for stable connection.

### **5. Local MCP = Works Offline!**

Your MCPs (github-pr-comments, python-mcp) work locally!

Even offline, Claude Code can:
- Use your MCP tools (they run locally)
- Read/write files
- Run git commands
- Execute Python scripts

Only Claude's **responses** need internet.

---

## 📋 Quick Reference

### **Stop Repeated Approvals:**
```bash
# Add to ~/.claude/CLAUDE.md
echo "Please remember when I have accepted bash commands." >> ~/.claude/CLAUDE.md
```

### **Check MCP Usage:**
```bash
./check_mcp_usage.sh
tail -f /tmp/github-pr-mcp.log
```

### **Recovery from Hang:**
```
1. Wait 30 seconds (might auto-recover)
2. Try Cmd+R (refresh)
3. Last resort: killall Claude, reopen
```

### **Preserve Context:**
```
"Summarize our progress so I can resume if needed"
```

---

## 🔧 Advanced: Claude Code Config

Full config: `~/.claude/settings.json`

```json
{
  "autoApprove": {
    "enabled": true,
    "commands": ["git status", "git diff", "ls"],
    "patterns": ["git*", "pytest*"]
  },
  "connection": {
    "timeout": 60000,
    "retries": 3,
    "keepAlive": true
  },
  "offlineMode": {
    "enabled": true,
    "continueWithoutAPI": true
  },
  "logging": {
    "level": "INFO",
    "mcpLogs": true
  }
}
```

---

**Save this file! It answers your three most important questions.** 📚
