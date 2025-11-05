#!/bin/bash
# Check MCP server usage and activity

LOG_FILE="${MCP_LOG_FILE:-/tmp/github-pr-mcp.log}"

echo "========================================"
echo "GitHub PR Comments MCP - Usage Check"
echo "========================================"
echo ""

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo ""
    echo "To enable logging, add to your Claude MCP config:"
    echo "  \"MCP_LOG_FILE\": \"/tmp/github-pr-mcp.log\""
    echo ""
    exit 1
fi

echo "📁 Log file: $LOG_FILE"
echo "📊 File size: $(du -h $LOG_FILE | cut -f1)"
echo ""

# Check if server has been started
STARTUP_COUNT=$(grep "GitHub PR Comment MCP Server Starting" "$LOG_FILE" | wc -l | tr -d ' ')
echo "🚀 Server starts: $STARTUP_COUNT"

if [ "$STARTUP_COUNT" -eq 0 ]; then
    echo "⚠️  Server has never been started"
    echo "   Check your Claude MCP configuration"
    exit 0
fi

# Last startup time
LAST_START=$(grep "GitHub PR Comment MCP Server Starting" "$LOG_FILE" | tail -1 | cut -d' ' -f1-2)
echo "⏰ Last startup: $LAST_START"
echo ""

# Tool usage statistics
echo "========================================"
echo "Tool Usage Statistics"
echo "========================================"
echo ""

TOOL_CALLS=$(grep "Tool called:" "$LOG_FILE" | wc -l | tr -d ' ')
echo "📞 Total tool calls: $TOOL_CALLS"

if [ "$TOOL_CALLS" -eq 0 ]; then
    echo ""
    echo "⚠️  No tools have been called yet"
    echo "   The MCP server is running but not being used"
    echo ""
    echo "💡 Try in Claude:"
    echo "   'What MCP tools are available?'"
    echo "   'Use github-pr-comments to fetch PR 72 comments'"
    exit 0
fi

echo ""
echo "Most used tools:"
grep "Tool called:" "$LOG_FILE" | cut -d':' -f4 | sed 's/^ //' | sort | uniq -c | sort -nr | head -10 | while read count tool; do
    echo "  $count × $tool"
done

echo ""
echo "========================================"
echo "Recent Activity (last 10 calls)"
echo "========================================"
echo ""

grep "Tool called:" "$LOG_FILE" | tail -10 | while read line; do
    timestamp=$(echo "$line" | cut -d' ' -f1-2)
    tool=$(echo "$line" | cut -d':' -f4 | sed 's/^ //')
    echo "  $timestamp → $tool"
done

echo ""
echo "========================================"
echo "Errors (if any)"
echo "========================================"
echo ""

ERROR_COUNT=$(grep "ERROR" "$LOG_FILE" | wc -l | tr -d ' ')
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "✅ No errors found"
else
    echo "⚠️  Found $ERROR_COUNT errors:"
    echo ""
    grep "ERROR" "$LOG_FILE" | tail -5 | while read line; do
        echo "  $line"
    done
fi

echo ""
echo "========================================"
echo "Commands"
echo "========================================"
echo ""
echo "Watch live activity:"
echo "  tail -f $LOG_FILE"
echo ""
echo "Clear logs:"
echo "  > $LOG_FILE"
echo ""
echo "Compare with other MCPs:"
echo "  ./check_mcp_usage.sh  # This MCP"
echo "  MCP_LOG_FILE=/tmp/python-mcp.log ./check_mcp_usage.sh"
echo ""
