# Interactive PR Comment Management - Now Available in MCP!

**Date**: November 6, 2025
**Status**: ✅ Production Ready

---

## What Changed

I've added **two new MCP tools** that enable interactive, user-driven PR comment management. Now when Claude uses the MCP server, it can ask YOU what to do with each uncertain comment instead of posting generic "will review" messages.

---

## New MCP Tools

### 1. `prepare_comment_decisions`

**Purpose**: Analyzes PR comments and prepares structured data for user decisions

**What it does**:
- Fetches all PR comments
- Analyzes each one (using existing `analyze_comment_validity`)
- Filters to comments needing user input (uncertain, low confidence)
- Returns rich structured data with:
  - Comment details (ID, file, line, author, body)
  - Full code context
  - AI analysis (status, confidence, reasoning)
  - Suggested questions to ask user

**When Claude calls this**:
```json
{
  "total_comments": 20,
  "actionable_comments": 8,
  "decisions_needed": [
    {
      "comment_id": "2499182468",
      "file_path": "libs/aws/src/idp_aws/config.py",
      "line_number": 43,
      "author": "Copilot",
      "body": "The validator reads directly from os.getenv...",
      "code_context": "... full code snippet ...",
      "ai_analysis": {
        "status": "uncertain",
        "confidence": 0.3,
        "reasoning": "Cannot determine if this is intentional..."
      },
      "suggested_questions": [
        {
          "label": "Needs fixing",
          "description": "Keep thread open and acknowledge",
          "action": "fix"
        },
        {
          "label": "Not an issue",
          "description": "Resolve thread and dismiss",
          "action": "dismiss"
        },
        {
          "label": "Skip for now",
          "description": "Don't take any action",
          "action": "skip"
        }
      ]
    },
    // ... more comments ...
  ]
}
```

### 2. `execute_comment_decision`

**Purpose**: Executes user's decision on a comment

**What it does**:
- Takes user's choice (`fix`, `dismiss`, or `skip`)
- Posts appropriate reply to GitHub
- Optionally resolves thread (if action is `dismiss`)
- Returns result confirmation

**Actions**:
- **`fix`**: Posts acknowledgment + keeps thread open
- **`dismiss`**: Posts explanation + resolves thread
- **`skip`**: Takes no action

---

## How Claude Will Use This

### Before (❌ Old Way)
```
Claude: I found 11 uncertain comments. I'll post "will review" to all of them.
[Posts generic responses without asking]
```

### After (✅ New Way)
```
User: Manage PR #74 comments

Claude: [Calls prepare_comment_decisions]
Claude: I found 8 comments that need your input. Let me show you each one.

Claude: Comment 1 of 8
📍 libs/aws/src/idp_aws/config.py:43
👤 Copilot flagged: "The validator reads directly from os.getenv
   instead of using Pydantic's field values..."

📄 Code:
    @field_validator('aws_access_key_id', 'aws_secret_access_key')
    def check_aws_credentials(cls, v, info):
        key_id = os.getenv('AWS_ACCESS_KEY_ID')
        secret = os.getenv('AWS_SECRET_ACCESS_KEY')

🤔 AI Analysis: uncertain (30% confidence)
   Cannot determine if direct os.getenv usage is intentional

[Uses AskUserQuestion tool]
Options:
1. Needs fixing - Keep thread open
2. Not an issue - Resolve and dismiss
3. Skip for now

User: [Selects "Not an issue"]
User: [Types reason:] "Intentional for Docker compatibility"

Claude: [Calls execute_comment_decision with action="dismiss", message="Not an issue - intentional for Docker compatibility"]
Claude: ✓ Posted reply and resolved thread

[Continues to next comment...]
```

---

## Files Modified

### New Files
- `mcp_server/tools/interactive.py` - New interactive workflow tools
  - `prepare_comment_decisions()` - 150 lines
  - `execute_comment_decision()` - 100 lines

### Modified Files
- `mcp_server/tools/__init__.py` - Added exports
- `mcp_server/server.py` - Registered new tools
  - Added imports
  - Added tool definitions (70 lines)
  - Added call handlers

---

## Testing

✅ **Unit tests passed**:
- Tools import correctly
- `prepare_comment_decisions` returns structured data
- `execute_comment_decision` handles all actions (fix/dismiss/skip)

✅ **Integration test**:
- Tested against real PR #74 and #77
- All API calls working
- Data structure correct

---

## How to Use Right Now

### Option 1: Ask Me (Claude) to Do It
Since I'm already connected to the MCP server in this session:

```
You: "Manage PR #74 comments interactively"

Me: [Uses the new tools to present each comment and get your decisions]
```

### Option 2: After Restart
After you restart Claude:

1. The new MCP tools will be automatically available
2. Just ask: **"Manage PR #[number] comments interactively"**
3. I'll present each uncertain comment with context
4. You decide: fix, dismiss, or skip
5. I'll execute your decisions on GitHub

---

## Benefits

✅ **User stays in control** - No surprises on your PR
✅ **Context-aware** - See full picture before deciding
✅ **Efficient** - Handle all comments in one conversation
✅ **Transparent** - Know exactly what will be posted
✅ **Smart filtering** - Only shows comments that need input

---

## What Makes This Different

### Standalone Script
The `interactive_pr_comment_manager.py` script:
- Uses terminal `input()` prompts
- Runs independently
- Good for testing outside Claude

### MCP Integration (What I Just Built)
The new MCP tools:
- Work through Claude's conversation interface
- Use Claude's `AskUserQuestion` tool
- Fully integrated into Claude workflow
- Available to ALL Claude instances using this MCP

---

## Example Conversation Flow

```
User: "Please review PR #74 comments"

Claude: Let me analyze the comments first.
        [Calls prepare_comment_decisions]

Claude: I found 8 comments needing your input.
        Let me show you each one...

[For each comment]
Claude: Comment 2 of 8

        📍 services/genai-idp-kb-sync/tests/test_integration_e2e.py:508

        💬 Copilot says: "Keyword argument 'aws_service' is not a
           supported parameter name..."

        📄 Code shows:
           KafkaMessageHandler(aws_service=mock_aws_service)

        🤔 Analysis: needs_fix (70% confidence)
           Parameter name doesn't match __init__ signature

        ❓ What should I do?

[Uses AskUserQuestion]

User: [Clicks "Fix this"]

Claude: Got it! I'll acknowledge this and keep the thread open.
        [Calls execute_comment_decision]
        ✓ Posted: "Acknowledged - this will be addressed"
        ✓ Thread kept open

Claude: Moving to comment 3 of 8...
```

---

## Technical Details

### Decision Thresholds

Comments are flagged for user input when:
- `status == "uncertain"` (any confidence)
- `status == "needs_fix"` AND `confidence < 70%`
- `status == "already_fixed"` AND `confidence < 60%`

Auto-resolved without asking when:
- `status == "already_fixed"` AND `confidence >= 60%`
- Clear false positives (like intentional import placement)

### API Efficiency

The `prepare_comment_decisions` tool:
- Batches API calls where possible
- Uses existing caching (`_thread_status_cache`)
- Parallelizes comment analysis
- Minimizes redundant GitHub API calls

---

## Next Steps

1. **Restart Claude** to load the new tools (optional - they work now!)
2. **Try it**: "Manage PR #74 comments interactively"
3. **Watch** as I present each comment with full context
4. **Decide** what action to take
5. **Verify** on GitHub that actions were taken correctly

---

## Files Reference

**New Interactive Tools**:
- `/Users/mark.johnson/Desktop/source/repos/mark.johnson/claude_mcp_agent_github_comments/mcp_server/tools/interactive.py`

**MCP Server Registration**:
- `/Users/mark.johnson/Desktop/source/repos/mark.johnson/claude_mcp_agent_github_comments/mcp_server/server.py`

**Test Scripts**:
- `/Users/mark.johnson/Desktop/source/repos/mark.johnson/test_interactive_tools.py` (unit tests)
- `/Users/mark.johnson/Desktop/source/repos/mark.johnson/interactive_pr_comment_manager.py` (standalone)

**Documentation**:
- `/Users/mark.johnson/Desktop/source/repos/mark.johnson/CLAUDE_INTERACTIVE_WORKFLOW_GUIDE.md` (for Claude)
- This file (for you!)

---

**Created**: November 6, 2025
**Status**: ✅ Ready to use right now!

Want to try it? Just say: **"Manage PR #74 comments interactively"**
