#!/bin/bash
# Install MCP wrapper script for Claude Code CLI
#
# This script helps users install the github-pr-comments MCP server
# in their Claude Code CLI configuration.

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_WRAPPER_DIR="$HOME/.claude/mcp-servers"
WRAPPER_NAME="github-pr-comments.py"

echo "📦 Installing GitHub PR Comments MCP Server Wrapper"
echo ""

# Step 1: Check if repo package is installed
echo "Checking package installation..."
if [ ! -d "$HOME/.venvs/github-pr-mcp" ]; then
    echo "⚠️  Virtual environment not found at ~/.venvs/github-pr-mcp"
    echo ""
    echo "Creating venv and installing package..."

    cd "$REPO_DIR"
    uv venv ~/.venvs/github-pr-mcp
    source ~/.venvs/github-pr-mcp/bin/activate
    uv pip install -e .

    echo "✅ Package installed"
else
    echo "✅ Virtual environment found"
fi

# Step 2: Create MCP wrapper directory if needed
echo ""
echo "Creating MCP wrapper directory..."
mkdir -p "$MCP_WRAPPER_DIR"

# Step 3: Copy template
echo "Copying wrapper template..."
cat > "$MCP_WRAPPER_DIR/$WRAPPER_NAME" << 'EOF'
#!/usr/bin/env python3
"""
MCP Server wrapper for GitHub PR Comment Agent

SETUP INSTRUCTIONS:
1. Update GITHUB_TOKEN and GITHUB_REPO below
2. Update VENV_PATH if you installed in a different location
3. Make executable: chmod +x ~/.claude/mcp-servers/github-pr-comments.py
4. Restart Claude Code CLI
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
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "your-token-here")
GITHUB_REPO = os.getenv("GITHUB_REPO", "owner/repo")

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "/tmp/github-pr-mcp.log"

# =======================================================

def main():
    """Run the MCP server with configured environment"""
    # Validate configuration
    if GITHUB_TOKEN == "your-token-here":
        print("❌ Please update GITHUB_TOKEN in the wrapper script")
        print(f"   Edit: {__file__}")
        sys.exit(1)

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
        print(f"  uv venv {VENV_PATH}")
        print(f"  source {VENV_PATH}/bin/activate")
        print(f"  uv pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x "$MCP_WRAPPER_DIR/$WRAPPER_NAME"

echo "✅ Wrapper installed at: $MCP_WRAPPER_DIR/$WRAPPER_NAME"
echo ""
echo "📝 NEXT STEPS:"
echo "   1. Edit the wrapper to add your GitHub token:"
echo "      \$EDITOR $MCP_WRAPPER_DIR/$WRAPPER_NAME"
echo ""
echo "   2. Update these variables:"
echo "      - GITHUB_TOKEN"
echo "      - GITHUB_REPO"
echo ""
echo "   3. Restart Claude Code CLI"
echo ""
echo "   4. Verify with: claude mcp list"
echo ""
