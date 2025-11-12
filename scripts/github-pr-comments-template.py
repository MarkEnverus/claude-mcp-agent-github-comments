#!/usr/bin/env python3
"""
MCP Server wrapper for GitHub PR Comment Agent

SETUP INSTRUCTIONS:
1. Copy this file to: ~/.claude/mcp-servers/github-pr-comments.py
2. Update GITHUB_TOKEN below
3. Update VENV_PATH if you installed in a different location
4. Make executable: chmod +x ~/.claude/mcp-servers/github-pr-comments.py
5. Restart Claude Code CLI

GITHUB_REPO is now optional - it will auto-detect from git remote!

For more details, see: docs/installation.md
"""
import asyncio
import os
import sys
from pathlib import Path

# ==================== CONFIGURATION ====================
# TODO: Update these for your system

# Path to venv (default: ~/.venvs/github-pr-mcp)
VENV_PATH = Path.home() / ".venvs" / "github-pr-mcp"
PYTHON_PATH = VENV_PATH / "bin" / "python"

# TODO: Add your GitHub token
# Get token from: https://github.com/settings/tokens
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "your-token-here")

# Optional: GITHUB_REPO will auto-detect from git remote if not set
GITHUB_REPO = os.getenv("GITHUB_REPO", "")

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

    # GITHUB_REPO is now optional and auto-detected from git remote
    if not GITHUB_REPO:
        print("ℹ️  GITHUB_REPO not set - will auto-detect from git remote")
        print("   (You can set it explicitly in the wrapper or via environment variable)")

    # Set environment variables
    os.environ["GITHUB_TOKEN"] = GITHUB_TOKEN
    if GITHUB_REPO:  # Only set if provided
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
        print("\nTo install:")
        print("  cd <repo-directory>")
        print("  ./scripts/install-mcp-wrapper.sh")
        print("")
        print("Or manually:")
        print(f"  uv venv {VENV_PATH}")
        print(f"  source {VENV_PATH}/bin/activate")
        print("  uv pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
