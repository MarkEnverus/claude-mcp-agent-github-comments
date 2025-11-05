# GitHub PR Comment Management Agent

An intelligent MCP agent powered by Claude that helps developers efficiently review, triage, and respond to automated PR comments (like those from Copilot) with context-aware code fixes.

## Why This Tool?

If you use GitHub Copilot, security scanners, or other automated PR comment tools, you know the pain:
- Dozens of comments to review per PR
- Manually checking if each issue is valid or already fixed
- Writing replies and applying fixes one by one
- Resolving threads individually

This tool gives you superpowers:
- **Intelligent Analysis**: Claude determines if issues are valid, fixed, or outdated
- **Batch Operations**: Process multiple comments efficiently
- **Automated Fixes**: Generate and apply code fixes with approval
- **Smart Resolution**: Auto-resolve threads with appropriate replies

## Architecture: Hybrid MCP + Agent

This project uses a **hybrid approach** combining:

1. **MCP Server** (The "Hands"): Discrete tools for GitHub PR operations
   - Use directly from Claude Code: `mcp__github-pr__fetch_comments`
   - Composable, reusable, universal

2. **Claude Agent** (The "Brain"): Intelligent workflow orchestration
   - Natural language: `pr-comment-agent review --pr 69`
   - Context-aware decision making
   - Interactive workflows

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full details.

## Quick Start

**See [INSTALL.md](./INSTALL.md) for global installation in Claude Desktop/Code!**

### Option 1: Use in Claude Desktop/Code (Recommended)

```bash
# 1. Install
cd claude-mcp-agent-github-comments
uv venv ~/.venvs/github-pr-mcp
source ~/.venvs/github-pr-mcp/bin/activate
uv pip install -e .

# 2. Add to Claude config
# Edit: ~/Library/Application Support/Claude/claude_desktop_config.json
# See INSTALL.md for complete config

# 3. Restart Claude and use!
# "Fetch comments from PR 72 using github-pr-comments MCP"
```

### Option 2: Direct Python Usage

```bash
git clone https://github.com/MarkEnverus/claude-mcp-agent-github-comments.git
cd claude-mcp-agent-github-comments
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your GITHUB_TOKEN and GITHUB_REPO

# Run examples
python examples/basic_usage.py
```

### Check MCP Usage

```bash
# See if Claude is using your MCP tools
./check_mcp_usage.sh
```

## Usage

### CLI: Interactive Review Session

```bash
# Review all automated comments on a PR
pr-comment-agent review --pr 69

# Auto-resolve comments that are already fixed
pr-comment-agent auto-resolve --pr 69 --filter already-fixed --dry-run

# Fix a specific comment
pr-comment-agent fix --comment-id 123456789
```

### Direct MCP Tool Usage (from Claude Code)

Add to your Claude Code MCP settings:
```json
{
  "mcpServers": {
    "github-pr-comments": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxxx",
        "GITHUB_REPO": "MarkEnverus/my-repo"
      }
    }
  }
}
```

Then use tools directly:
```
mcp__github-pr__fetch_comments --pr 69
mcp__github-pr__analyze_comment_validity --comment-id abc123
mcp__github-pr__resolve_thread --thread-id xyz789
```

## Features

### Phase 1: MCP Server ✅ COMPLETE
- ✅ All 8 MCP tools implemented and functional
- ✅ Fetch and filter PR comments by author, type, status
- ✅ Analyze comment validity (is the issue still present?)
- ✅ Get code context around comments
- ✅ Apply code fixes with git commits
- ✅ Reply to comments and resolve threads
- ✅ Batch analysis with categorization and prioritization
- ✅ Full PR diff extraction
- ✅ Use directly from Claude Code or Python

### Coming Soon
- **Phase 2**: Advanced analysis with Claude integration
- **Phase 3**: Complete code fix workflow
- **Phase 4**: Agent SDK for intelligent orchestration
- **Phase 5**: CLI interface with interactive mode
- **Phase 6**: GitHub Action for automation
- **Future**: Multi-PR support, learning system, VS Code extension

## Examples

See [examples/](./examples/) directory for:
- `basic_review.py`: Simple review session
- `auto_resolve.py`: Automated resolution
- `direct_mcp_usage.py`: Using MCP tools directly

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Format code
black .

# Type checking
mypy .
```

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT License - see [LICENSE](./LICENSE)

## Architecture

For detailed architecture information, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## Credits

Built with:
- [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/python)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [PyGithub](https://pygithub.readthedocs.io/)
- [Click](https://click.palletsprojects.com/)
- [Rich](https://rich.readthedocs.io/)

---

Made with Claude Code by [@MarkEnverus](https://github.com/MarkEnverus)
