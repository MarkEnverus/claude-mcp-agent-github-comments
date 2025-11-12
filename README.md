# GitHub PR Comment MCP Server

An intelligent MCP server for managing GitHub PR comments directly from Claude Code. Automatically reviews, triages, and responds to automated PR comments (Copilot, security scanners, etc.) with context-aware analysis.

## Features

- **Smart Filtering**: Filter comments by author, status, age, keywords
- **Validity Analysis**: AI-powered detection of already-fixed or outdated issues
- **Batch Operations**: Process multiple comments efficiently
- **Interactive Workflows**: User-guided decision making for uncertain comments
- **Auto-Detection**: Automatically detects repository from git remote
- **Code Fixes**: Apply fixes with git commits (manual push)

## Quick Start

```bash
# Clone and install
git clone https://github.com/MarkEnverus/claude-mcp-agent-github-comments.git
cd claude-mcp-agent-github-comments
pip install -e .

# Configure
export GITHUB_TOKEN=ghp_your_token_here
# GITHUB_REPO is optional - auto-detected from git remote

# Add to Claude Code config
# See docs/installation.md for setup instructions
```

## Usage in Claude Code

Once installed, use natural language:

```
"Review open Copilot comments on PR 72"
"Batch close all resolved comments on PR 80"
"Show me context for comment ID 12345"
```

Or call tools directly:
```
mcp__github-pr-comments__fetch_pr_comments(pr_number=72)
mcp__github-pr-comments__prepare_comment_decisions(pr_number=72, fast_mode=true)
```

## Documentation

- [Installation Guide](./docs/installation.md) - Setup for Claude Desktop/Code
- [Usage Guide](./docs/usage.md) - Features and workflows
- [Troubleshooting](./docs/troubleshooting.md) - Common issues and solutions
- [Architecture](./docs/architecture.md) - Technical details
- [Interactive Workflow](./docs/features/interactive-workflow.md) - User decision workflow
- [Bulk Close](./docs/features/bulk-close.md) - Fast batch operations

## License

MIT License - see [LICENSE](./LICENSE)

---

Built with [Model Context Protocol](https://modelcontextprotocol.io/) and Claude Code
