"""
Interactive workflow tools for MCP server

These tools provide structured data for Claude to present to users,
enabling interactive decision-making on uncertain PR comments.
"""
import json
from typing import Any

from .analysis import analyze_comment_validity
from .code_ops import create_comment_reply, resolve_thread
from .comments import fetch_pr_comments, get_comment_context


async def prepare_comment_decisions(
    pr_number: int,
    repo: str | None = None,
    filters: dict[str, Any] | None = None,
    fast_mode: bool = False,
) -> str:
    """
    Prepare structured data for uncertain comments that need user decisions.

    This tool:
    1. Fetches all PR comments
    2. Analyzes each one
    3. Filters to comments needing user input (uncertain, low confidence)
    4. Returns structured data with context for Claude to present

    Args:
        pr_number: PR number to analyze
        repo: Repository in 'owner/name' format (optional)
        filters: Optional filters like {'status': 'open', 'author': 'Copilot'}

    Returns:
        JSON string with structure:
        {
            "total_comments": int,
            "actionable_comments": int,
            "decisions_needed": [
                {
                    "comment_id": str,
                    "file_path": str,
                    "line_number": int,
                    "author": str,
                    "body": str,
                    "status": str,
                    "code_context": str,
                    "ai_analysis": {
                        "status": str,
                        "confidence": float,
                        "reasoning": str,
                        "suggested_action": str
                    },
                    "suggested_questions": [
                        {
                            "label": str,
                            "description": str,
                            "action": str  # 'fix', 'dismiss', 'skip'
                        }
                    ]
                }
            ]
        }

    Example:
        >>> decisions = await prepare_comment_decisions(pr_number=74, repo="owner/repo")
        >>> data = json.loads(decisions)
        >>> for comment in data['decisions_needed']:
        >>>     # Claude presents this to user via AskUserQuestion
        >>>     print(comment['body'], comment['code_context'])
    """
    # Fetch all comments
    comments_raw = await fetch_pr_comments(pr_number=pr_number, repo=repo)

    if isinstance(comments_raw, str):
        comments = json.loads(comments_raw)
    else:
        comments = comments_raw

    # Filter to review comments
    review_comments = [c for c in comments if c.get("comment_type") == "review_comment"]

    # Apply any additional filters
    if filters:
        if "status" in filters:
            review_comments = [c for c in review_comments if c.get("status") == filters["status"]]
        if "author" in filters:
            review_comments = [c for c in review_comments if c.get("author") == filters["author"]]

    # Analyze each comment and gather context
    decisions_needed = []

    for comment in review_comments:
        comment_id = comment["id"]

        try:
            # Fast mode: Use simple pattern matching instead of LLM analysis
            if fast_mode:
                body_lower = comment.get("body", "").lower()

                # Simple heuristic classification
                if any(word in body_lower for word in ["import", "top of the file", "module level"]):
                    validity = {"status": "uncertain", "confidence": 0.5, "reasoning": "Import placement comment (fast mode)"}
                elif any(word in body_lower for word in ["duplicate", "redundant"]):
                    validity = {"status": "needs_fix", "confidence": 0.6, "reasoning": "Possible duplicate code (fast mode)"}
                elif any(word in body_lower for word in ["security", "vulnerability", "injection"]):
                    validity = {"status": "needs_fix", "confidence": 0.8, "reasoning": "Security issue (fast mode)"}
                else:
                    validity = {"status": "uncertain", "confidence": 0.3, "reasoning": "Needs review (fast mode)"}
            else:
                # Slow mode: Full LLM analysis
                validity_raw = await analyze_comment_validity(
                    comment_id=comment_id, pr_number=pr_number, repo=repo
                )

                if isinstance(validity_raw, str):
                    validity = json.loads(validity_raw)
                else:
                    validity = validity_raw

            # Only include comments that need user decision
            status = validity.get("status", "unknown")
            confidence = validity.get("confidence", 0)

            # Include if:
            # - Status is uncertain
            # - Status is needs_fix but confidence < 70%
            # - Status is already_fixed but confidence < 60%
            needs_decision = (
                status == "uncertain"
                or (status == "needs_fix" and confidence < 0.7)
                or (status == "already_fixed" and confidence < 0.6)
            )

            if not needs_decision:
                continue

            # Get code context
            context_raw = await get_comment_context(
                comment_id=comment_id, pr_number=pr_number, repo=repo, lines_before=5, lines_after=5
            )

            if isinstance(context_raw, str):
                context = json.loads(context_raw)
            else:
                context = context_raw

            # Determine suggested actions based on analysis
            suggested_questions = []

            if status == "needs_fix":
                suggested_questions = [
                    {
                        "label": "Fix this issue",
                        "description": "Keep thread open and acknowledge it will be fixed",
                        "action": "fix",
                    },
                    {
                        "label": "False positive",
                        "description": "Resolve thread - this is not actually an issue",
                        "action": "dismiss",
                    },
                    {
                        "label": "Skip for now",
                        "description": "Don't take any action on this comment",
                        "action": "skip",
                    },
                ]
            elif status == "already_fixed":
                suggested_questions = [
                    {
                        "label": "Confirmed fixed",
                        "description": "Resolve thread - issue has been addressed",
                        "action": "dismiss",
                    },
                    {
                        "label": "Not actually fixed",
                        "description": "Keep thread open - still needs work",
                        "action": "fix",
                    },
                    {
                        "label": "Skip for now",
                        "description": "Don't take any action on this comment",
                        "action": "skip",
                    },
                ]
            else:  # uncertain
                suggested_questions = [
                    {
                        "label": "Needs fixing",
                        "description": "Keep thread open and acknowledge",
                        "action": "fix",
                    },
                    {
                        "label": "Not an issue",
                        "description": "Resolve thread and dismiss",
                        "action": "dismiss",
                    },
                    {
                        "label": "Skip for now",
                        "description": "Don't take any action",
                        "action": "skip",
                    },
                ]

            # Build decision object
            decisions_needed.append(
                {
                    "comment_id": str(comment_id),
                    "file_path": comment.get("file_path", "N/A"),
                    "line_number": comment.get("line_number", 0),
                    "author": comment.get("author", "unknown"),
                    "body": comment.get("body", ""),
                    "status": comment.get("status", "unknown"),
                    "code_context": context.get("code_context", "No context available"),
                    "ai_analysis": {
                        "status": status,
                        "confidence": confidence,
                        "reasoning": validity.get("reasoning", ""),
                        "suggested_action": validity.get("suggested_action", ""),
                    },
                    "suggested_questions": suggested_questions,
                }
            )

        except Exception as e:
            # If we can't analyze a comment, include it as uncertain
            decisions_needed.append(
                {
                    "comment_id": str(comment_id),
                    "file_path": comment.get("file_path", "N/A"),
                    "line_number": comment.get("line_number", 0),
                    "author": comment.get("author", "unknown"),
                    "body": comment.get("body", ""),
                    "status": comment.get("status", "unknown"),
                    "code_context": "Error retrieving context",
                    "ai_analysis": {
                        "status": "error",
                        "confidence": 0,
                        "reasoning": f"Error analyzing comment: {str(e)}",
                        "suggested_action": "",
                    },
                    "suggested_questions": [
                        {
                            "label": "Skip this comment",
                            "description": "Could not analyze - skip for now",
                            "action": "skip",
                        }
                    ],
                }
            )

    return json.dumps(
        {
            "total_comments": len(comments),
            "review_comments": len(review_comments),
            "actionable_comments": len(decisions_needed),
            "decisions_needed": decisions_needed,
        },
        indent=2,
    )


async def execute_comment_decision(
    comment_id: str,
    pr_number: int,
    action: str,
    message: str | None = None,
    repo: str | None = None,
) -> str:
    """
    Execute a user's decision on a PR comment.

    This tool takes a user's decision and performs the appropriate GitHub actions.

    Args:
        comment_id: ID of the comment to act on
        pr_number: PR number
        action: User's decision - 'fix', 'dismiss', or 'skip'
        message: Optional custom message to post (if not provided, uses default)
        repo: Repository in 'owner/name' format (optional)

    Returns:
        JSON string with result:
        {
            "action_taken": str,
            "comment_id": str,
            "reply_posted": bool,
            "reply_id": str | None,
            "thread_resolved": bool,
            "message": str
        }

    Actions:
        - 'fix': Posts acknowledgment, keeps thread open
        - 'dismiss': Posts explanation, resolves thread
        - 'skip': Takes no action

    Example:
        >>> result = await execute_comment_decision(
        ...     comment_id="123456",
        ...     pr_number=74,
        ...     action="dismiss",
        ...     message="Not an issue - this is intentional for Docker compatibility"
        ... )
    """
    if action == "skip":
        return json.dumps(
            {
                "action_taken": "skip",
                "comment_id": comment_id,
                "reply_posted": False,
                "reply_id": None,
                "thread_resolved": False,
                "message": "Skipped - no action taken",
            }
        )

    # Determine message if not provided
    if not message:
        if action == "fix":
            message = "✅ Acknowledged - this will be addressed in the next update."
        elif action == "dismiss":
            message = "✅ Reviewed and confirmed - this is not an issue or has been addressed."
        else:
            return json.dumps(
                {
                    "action_taken": "error",
                    "comment_id": comment_id,
                    "reply_posted": False,
                    "reply_id": None,
                    "thread_resolved": False,
                    "message": f"Invalid action: {action}. Must be 'fix', 'dismiss', or 'skip'.",
                }
            )

    # Post reply
    try:
        reply_raw = await create_comment_reply(
            comment_id=comment_id, pr_number=pr_number, repo=repo, message=message
        )

        if isinstance(reply_raw, str):
            reply = json.loads(reply_raw)
        else:
            reply = reply_raw

        reply_id = reply.get("id")
        reply_posted = True

    except Exception as e:
        return json.dumps(
            {
                "action_taken": "error",
                "comment_id": comment_id,
                "reply_posted": False,
                "reply_id": None,
                "thread_resolved": False,
                "message": f"Error posting reply: {str(e)}",
            }
        )

    # Resolve thread if action is 'dismiss'
    thread_resolved = False
    if action == "dismiss":
        try:
            resolution_raw = await resolve_thread(
                comment_id=comment_id, pr_number=pr_number, repo=repo
            )

            if isinstance(resolution_raw, str):
                resolution = json.loads(resolution_raw)
            else:
                resolution = resolution_raw

            thread_resolved = resolution.get("is_resolved", False)

        except Exception as e:
            # Reply was posted but resolution failed - still return success
            return json.dumps(
                {
                    "action_taken": action,
                    "comment_id": comment_id,
                    "reply_posted": True,
                    "reply_id": reply_id,
                    "thread_resolved": False,
                    "message": f"Reply posted but failed to resolve thread: {str(e)}",
                }
            )

    return json.dumps(
        {
            "action_taken": action,
            "comment_id": comment_id,
            "reply_posted": reply_posted,
            "reply_id": reply_id,
            "thread_resolved": thread_resolved,
            "message": "Success",
        }
    )


async def bulk_close_comments(
    pr_number: int,
    repo: str | None = None,
    message: str = "✅ Acknowledged by MCP - thread closed",
    filters: dict[str, Any] | None = None,
    resolve_threads: bool = True,
) -> str:
    """
    Bulk close all comments with a generic message.

    This is a fast operation that doesn't use LLM analysis. It simply:
    1. Fetches all comments (with optional filters)
    2. Posts a generic acknowledgment to each
    3. Optionally resolves all threads

    Args:
        pr_number: PR number
        repo: Repository in 'owner/name' format (optional)
        message: Message to post to all comments (default: "✅ Acknowledged by MCP - thread closed")
        filters: Optional filters like {'status': 'open', 'author': 'Copilot'}
        resolve_threads: Whether to resolve threads after posting (default: True)

    Returns:
        JSON string with results:
        {
            "total_comments": int,
            "processed": int,
            "succeeded": int,
            "failed": int,
            "results": [
                {
                    "comment_id": str,
                    "success": bool,
                    "reply_posted": bool,
                    "thread_resolved": bool,
                    "error": str | None
                }
            ]
        }

    Example:
        >>> result = await bulk_close_comments(
        ...     pr_number=77,
        ...     repo="owner/repo",
        ...     message="✅ Reviewed by MCP",
        ...     filters={'status': 'open', 'author': 'Copilot'}
        ... )
    """
    # Fetch all comments
    comments_raw = await fetch_pr_comments(pr_number=pr_number, repo=repo)

    if isinstance(comments_raw, str):
        comments = json.loads(comments_raw)
    else:
        comments = comments_raw

    # Filter to review comments only
    review_comments = [c for c in comments if c.get("comment_type") == "review_comment"]

    # Apply additional filters if provided
    if filters:
        if "status" in filters:
            review_comments = [c for c in review_comments if c.get("status") == filters["status"]]
        if "author" in filters:
            review_comments = [c for c in review_comments if c.get("author") == filters["author"]]

    total_comments = len(review_comments)
    results = []
    succeeded = 0
    failed = 0

    # Process each comment
    for comment in review_comments:
        comment_id = str(comment["id"])
        result_entry = {
            "comment_id": comment_id,
            "success": False,
            "reply_posted": False,
            "thread_resolved": False,
            "error": None,
        }

        try:
            # Post reply
            reply_raw = await create_comment_reply(
                comment_id=comment_id, pr_number=pr_number, repo=repo, message=message
            )

            if isinstance(reply_raw, str):
                reply = json.loads(reply_raw)
            else:
                reply = reply_raw

            result_entry["reply_posted"] = True

            # Resolve thread if requested
            if resolve_threads:
                try:
                    resolution_raw = await resolve_thread(
                        comment_id=comment_id, pr_number=pr_number, repo=repo
                    )

                    if isinstance(resolution_raw, str):
                        resolution = json.loads(resolution_raw)
                    else:
                        resolution = resolution_raw

                    result_entry["thread_resolved"] = resolution.get("is_resolved", False)

                except Exception as e:
                    # Reply succeeded but resolution failed - still count as partial success
                    result_entry["error"] = f"Reply posted but resolution failed: {str(e)}"

            result_entry["success"] = True
            succeeded += 1

        except Exception as e:
            result_entry["error"] = str(e)
            failed += 1

        results.append(result_entry)

    return json.dumps(
        {
            "total_comments": total_comments,
            "processed": len(results),
            "succeeded": succeeded,
            "failed": failed,
            "results": results,
        },
        indent=2,
    )
