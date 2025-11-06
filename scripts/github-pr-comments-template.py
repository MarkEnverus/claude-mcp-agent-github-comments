#!/usr/bin/env python3
"""
MCP Server wrapper for GitHub PR Comment Agent

SETUP INSTRUCTIONS:
1. Copy this file to: ~/.claude/mcp-servers/github-pr-comments.py
2. Update GITHUB_TOKEN and GITHUB_REPO below
3. Update VENV_PATH if you installed in a different location
4. Make executable: chmod +x ~/.claude/mcp-servers/github-pr-comments.py
5. Restart Claude Code CLI

For more details, see: MCP_SETUP.md
"""
import os
import sys
import asyncio
from pathlib import Path

# ==================== CONFIGURATION ====================
# TODO: Update these for your system

# Path to venv (default: ~/.venvs/github-pr-mcp)
VENV_PATH = Path.home() / ".venvs" / "github-pr-mcp"
PYTHON_PATH = VENV_PATH / "bin" / "python"

# TODO: Add your GitHub token and repo
# Get token from: https://github.com/settings/tokens
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "your-token-here")
GITHUB_REPO = os.getenv("GITHUB_REPO", "owner/repo")

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FILE = "/tmp/github-pr-mcp.log"

# =======================================================


def main():
    """Run the MCP server with configured environment"""
    # Validate configuration
    if GITHUB_TOKEN == "your-token-here":
        print("❌ ERROR: Please update GITHUB_TOKEN in the wrapper script")
        print(f"   Edit: {__file__}")
        print("")
        print("Get a token from: https://github.com/settings/tokens")
        print("Required scopes: repo (full control)")
        sys.exit(1)

    if GITHUB_REPO == "owner/repo":
        print("⚠️  WARNING: GITHUB_REPO not configured")
        print(f"   Edit: {__file__}")
        print("   Or set GITHUB_REPO environment variable")

    # Set environment variables
    os.environ["GITHUB_TOKEN"] = GITHUB_TOKEN
    os.environ["GITHUB_REPO"] = GITHUB_REPO
    os.environ["LOG_LEVEL"] = LOG_LEVEL
    os.environ["MCP_LOG_FILE"] = LOG_FILE

    # If not using the correct Python, exec with it
    if PYTHON_PATH.exists() and Path(sys.executable).resolve() != PYTHON_PATH.resolve():
        os.execv(str(PYTHON_PATH), [str(PYTHON_PATH)] + sys.argv)

    # Import and run the server
    try:
        from mcp_server.server import main as server_main

        asyncio.run(server_main())
    except ImportError as e:
        print(f"❌ Package not found: {e}")
        print(f"   Expected location: {VENV_PATH}")
        print(f"\nTo install:")
        print(f"  cd <repo-directory>")
        print(f"  ./scripts/install-mcp-wrapper.sh")
        print("")
        print("Or manually:")
        print(f"  uv venv {VENV_PATH}")
        print(f"  source {VENV_PATH}/bin/activate")
        print(f"  uv pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
