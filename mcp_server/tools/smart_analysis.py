"""
Smart analysis tools using pattern recognition

Enhanced version of analysis tools that use pattern matching
for higher accuracy without requiring LLM API calls.
"""

from typing import Dict, Any
from ..models import ValidityAnalysis, ValidityStatus
from ..patterns import SmartAnalyzer, COMMON_BOT_AUTHORS
from .comments import get_comment_context
from .github_api import get_github_client


async def analyze_comment_smart(
    comment_id: str,
    pr_number: int,
    repo: str,
) -> Dict[str, Any]:
    """
    Smart analysis using pattern recognition (Phase 1.5)

    This is an enhanced version of analyze_comment_validity that uses
    pattern matching to identify common issues with high confidence.

    Args:
        comment_id: Comment ID to analyze
        pr_number: PR number
        repo: Repository in format "owner/repo"

    Returns:
        Enhanced analysis with:
            - pattern_detected: Which pattern was matched (if any)
            - can_auto_fix: Whether we can automatically fix this
            - suggested_fix: Exact fix if available
            - reply_template: Pre-written reply message
            - Higher confidence scores (0.7-0.9 for matched patterns)

    Example:
        >>> analysis = await analyze_comment_smart(
        ...     comment_id="2496256806",
        ...     pr_number=72,
        ...     repo="enverus-nv/genai-idp"
        ... )
        >>> print(analysis['pattern_detected'])  # "unused_import"
        >>> print(analysis['confidence'])  # 0.85
        >>> print(analysis['can_auto_fix'])  # True
    """
    # Get GitHub client
    client = get_github_client(repo=repo)

    # Find the comment
    comments = client.get_all_pr_comments(pr_number)
    comment = next((c for c in comments if c.id == comment_id), None)

    if not comment:
        raise ValueError(f"Comment {comment_id} not found in PR {pr_number}")

    # Get code context
    context = await get_comment_context(comment_id, pr_number, repo)

    # Use smart analyzer
    analyzer = SmartAnalyzer()
    smart_result = analyzer.analyze_with_patterns(
        comment_body=comment.body,
        code_snippet=context.get("code_snippet", ""),
        file_path=context.get("file_path", ""),
        line_number=context.get("line_number", 0),
    )

    # Build result combining smart analysis with standard format
    result = ValidityAnalysis(
        comment_id=comment_id,
        is_valid=smart_result.get("is_valid", False),
        status=ValidityStatus(smart_result.get("status", "uncertain")),
        confidence=smart_result.get("confidence", 0.3),
        reasoning=smart_result.get("reasoning", "Pattern-based analysis"),
        suggested_action=smart_result.get("suggested_action", "Review manually"),
    )

    # Add smart analysis extras
    result_dict = result.model_dump(mode="json")
    result_dict.update({
        "pattern_detected": smart_result.get("pattern_detected"),
        "can_auto_fix": smart_result.get("can_auto_fix", False),
        "suggested_fix": smart_result.get("suggested_fix"),
        "reply_template": smart_result.get("reply_template"),
    })

    return result_dict


def is_bot_comment(author: str) -> bool:
    """
    Check if comment is from a bot

    Args:
        author: Comment author username

    Returns:
        True if author is a known bot
    """
    return author in COMMON_BOT_AUTHORS


def get_bot_comment_filters() -> Dict[str, Any]:
    """
    Get pre-configured filters for bot comments

    Returns:
        Filter dict ready to use with fetch_pr_comments
    """
    return {
        "authors": COMMON_BOT_AUTHORS
    }
