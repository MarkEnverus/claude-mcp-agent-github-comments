# Quick Start Guide

Get started with the GitHub PR Comment Management Agent in minutes!

## Prerequisites

- Python 3.11+
- GitHub personal access token with `repo` scope
- Git repository with a pull request

## Installation

```bash
# Clone the repository
git clone https://github.com/MarkEnverus/claude-mcp-agent-github-comments.git
cd claude-mcp-agent-github-comments

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e ".[dev]"
```

## Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your credentials:
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
# GITHUB_REPO=MarkEnverus/my-repo
# ANTHROPIC_API_KEY=sk-ant-xxxxx (for agent features)
```

## Usage

### Option 1: Use MCP Server Directly from Claude Code

Add to your Claude Code MCP settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "github-pr-comments": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "/path/to/claude-mcp-agent-github-comments",
      "env": {
        "GITHUB_TOKEN": "ghp_xxxxxxxxxxxxx",
        "GITHUB_REPO": "MarkEnverus/my-repo"
      }
    }
  }
}
```

Then in Claude Code, you can use the tools:

```
You: Show me all Copilot comments on PR #69

Claude Code will use: mcp__github-pr-comments__fetch_pr_comments
```

### Option 2: Test MCP Server Directly (Python)

```python
import asyncio
from mcp_server.tools import fetch_pr_comments, analyze_comment_validity

async def test():
    # Fetch comments
    comments = await fetch_pr_comments(
        pr_number=69,
        repo="MarkEnverus/my-repo",
        filters={"authors": ["github-copilot"]}
    )

    print(f"Found {len(comments)} comments")

    # Analyze first comment
    if comments:
        analysis = await analyze_comment_validity(
            comment_id=comments[0]["id"],
            pr_number=69,
            repo="MarkEnverus/my-repo"
        )
        print(f"Status: {analysis['status']}")
        print(f"Reasoning: {analysis['reasoning']}")

asyncio.run(test())
```

### Option 3: CLI (Coming Soon in Phase 5)

```bash
# Interactive review session
pr-comment-agent review --pr 69

# Auto-resolve fixed comments
pr-comment-agent auto-resolve --pr 69 --filter already-fixed

# Fix specific comment
pr-comment-agent fix --comment-id 123456
```

## Examples

### Example 1: Fetch and Filter Comments

```python
from mcp_server.tools import fetch_pr_comments

comments = await fetch_pr_comments(
    pr_number=69,
    repo="MarkEnverus/my-repo",
    filters={
        "authors": ["github-copilot", "github-advanced-security"],
        "status": "open",
        "keywords": ["security", "null check"]
    }
)

for comment in comments:
    print(f"{comment['author']}: {comment['body'][:100]}")
```

### Example 2: Get Code Context

```python
from mcp_server.tools import get_comment_context

context = await get_comment_context(
    comment_id="123456789",
    pr_number=69,
    repo="MarkEnverus/my-repo",
    lines_before=10,
    lines_after=10
)

print(f"File: {context['file_path']}")
print(f"Line: {context['line_number']}")
print("\nCode:")
print(context['code_snippet'])
```

### Example 3: Batch Analysis

```python
from mcp_server.tools import batch_analyze_comments

result = await batch_analyze_comments(
    pr_number=69,
    repo="MarkEnverus/my-repo",
    filters={"authors": ["github-copilot"]}
)

print(f"Total: {result['total_comments']}")
print(f"Categories: {result['categories']}")

# Show high priority comments
high_priority = [p for p in result['priorities'] if p['priority'] == 'high']
print(f"\n{len(high_priority)} high priority comments:")
for p in high_priority:
    print(f"  - {p['file_path']}:{p['line_number']} - {p['preview'][:80]}")
```

### Example 4: Apply Code Fix

```python
from mcp_server.tools import apply_code_fix, create_comment_reply, resolve_thread

# Apply fix
result = await apply_code_fix(
    file_path="src/auth.py",
    line_number=45,
    fix_content="if not user or not user.email:\n    raise ValueError('User email required')",
    repo="MarkEnverus/my-repo",
    commit_message="fix: add null check for user.email"
)

if result['success']:
    print(f"Fix applied! Commit: {result['commit_sha']}")

    # Reply to comment
    await create_comment_reply(
        comment_id="123456",
        pr_number=69,
        repo="MarkEnverus/my-repo",
        message=f"Fixed! Added null check in commit {result['commit_sha'][:7]}"
    )

    # Resolve thread
    await resolve_thread(
        comment_id="123456",
        pr_number=69,
        repo="MarkEnverus/my-repo",
        reason="Issue addressed"
    )
```

## Testing the MCP Server

```bash
# Set environment variables
export GITHUB_TOKEN="ghp_xxxxx"
export GITHUB_REPO="MarkEnverus/my-repo"

# Run MCP server (will wait for stdio input)
python -m mcp_server.server
```

To test with MCP Inspector:

```bash
# Install MCP Inspector (if not already installed)
npm install -g @anthropic/mcp-inspector

# Run inspector
mcp-inspector python -m mcp_server.server
```

## Next Steps

1. **Read the architecture**: See [ARCHITECTURE.md](./ARCHITECTURE.md) for full details
2. **Explore examples**: Check out the `examples/` directory
3. **Customize config**: Edit `.github-pr-agent.yaml` for your preferences
4. **Integrate with Claude Code**: Add MCP server to your settings
5. **Stay tuned**: Phase 2+ will add CLI and Agent SDK features

## Troubleshooting

### "GITHUB_TOKEN environment variable is required"
Make sure you've set `GITHUB_TOKEN` in your `.env` file or environment.

### "Comment not found"
The comment ID might be incorrect. Use `fetch_pr_comments` first to get valid IDs.

### "Working tree is dirty"
The `apply_code_fix` tool requires a clean git working tree. Commit or stash changes first.

### Rate Limiting
If you hit GitHub API rate limits, the tools will retry automatically. Consider adding delays between operations.

## Support

- **Issues**: https://github.com/MarkEnverus/claude-mcp-agent-github-comments/issues
- **Documentation**: See README.md and ARCHITECTURE.md
- **Examples**: Check `examples/` directory

## What's Working Now (Phase 1)

✅ All 8 MCP tools functional:
- fetch_pr_comments
- get_comment_context
- analyze_comment_validity
- batch_analyze_comments
- apply_code_fix
- get_pr_diff
- create_comment_reply
- resolve_thread

✅ Use directly from Claude Code
✅ Python API available
✅ Comprehensive documentation

## Coming Soon

- Phase 2: Advanced analysis with Claude integration
- Phase 3: Complete code fix workflow
- Phase 4: Agent SDK for intelligent orchestration
- Phase 5: CLI interface with interactive mode
- Phase 6: GitHub Action for automation

Enjoy managing your PR comments with AI! 🚀
