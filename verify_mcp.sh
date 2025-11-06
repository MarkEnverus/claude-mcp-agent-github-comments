#!/bin/bash
# Verify MCP installation and help troubleshoot

echo "========================================"
echo "GitHub PR Comments MCP - Verification"
echo "========================================"
echo ""

# 1. Check venv exists
echo "1. Checking virtual environment..."
if [ -d ~/.venvs/github-pr-mcp ]; then
    echo "   ✅ venv exists at ~/.venvs/github-pr-mcp"
else
    echo "   ❌ venv not found"
    echo "   Run: uv venv ~/.venvs/github-pr-mcp && source ~/.venvs/github-pr-mcp/bin/activate && uv pip install -e ."
    exit 1
fi

# 2. Check package installed
echo "2. Checking package installation..."
if ~/.venvs/github-pr-mcp/bin/python -c "import mcp_server.server" 2>/dev/null; then
    echo "   ✅ Package installed"
else
    echo "   ❌ Package not installed"
    echo "   Run: source ~/.venvs/github-pr-mcp/bin/activate && uv pip install -e ."
    exit 1
fi

# 3. Check config file
echo "3. Checking Claude config..."
CONFIG_FILE=~/Library/Application\ Support/Claude/claude_desktop_config.json
if [ -f "$CONFIG_FILE" ]; then
    echo "   ✅ Config file exists"

    # Check if our MCP is in config
    if grep -q "github-pr-comments" "$CONFIG_FILE"; then
        echo "   ✅ github-pr-comments MCP configured"
    else
        echo "   ❌ github-pr-comments not in config"
        exit 1
    fi

    # Validate JSON
    if cat "$CONFIG_FILE" | python3 -m json.tool > /dev/null 2>&1; then
        echo "   ✅ Config is valid JSON"
    else
        echo "   ❌ Config has invalid JSON"
        exit 1
    fi
else
    echo "   ❌ Config file not found"
    exit 1
fi

# 4. Test server startup
echo "4. Testing MCP server startup..."
timeout 3 ~/.venvs/github-pr-mcp/bin/python -m mcp_server.server > /tmp/mcp_test.log 2>&1 &
PID=$!
sleep 2

if ps -p $PID > /dev/null 2>&1; then
    echo "   ✅ Server starts successfully"
    kill $PID 2>/dev/null
else
    echo "   ⚠️  Server stopped (may be normal for stdio mode)"
    # Check logs for errors
    if grep -i error /tmp/mcp_test.log > /dev/null 2>&1; then
        echo "   ❌ Errors found in startup:"
        grep -i error /tmp/mcp_test.log
        exit 1
    else
        echo "   ✅ No errors detected"
    fi
fi

echo ""
echo "========================================"
echo "✅ All checks passed!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Close Claude Desktop COMPLETELY"
echo "2. Reopen Claude Desktop"
echo "3. In Claude, ask: 'What MCP servers do I have?'"
echo "4. You should see both:"
echo "   - claude-python-mcp"
echo "   - github-pr-comments"
echo ""
echo "If github-pr-comments still doesn't show:"
echo "1. Check Claude logs:"
echo "   tail -f ~/Library/Logs/Claude/mcp*.log"
echo ""
echo "2. Or check our server log:"
echo "   tail -f /tmp/github-pr-mcp.log"
echo ""
echo "3. Restart Claude Desktop again"
echo ""
