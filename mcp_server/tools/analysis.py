"""
Comment analysis tools

Provides MCP tools for analyzing comment validity and batch processing.
"""

from collections import defaultdict
from typing import Any

from ..models import (
    BatchAnalysisResult,
    Priority,
    ValidityAnalysis,
    ValidityStatus,
)
from .comments import get_comment_context
from .github_api import get_github_client


async def analyze_comment_validity(
    comment_id: str,
    pr_number: int,
    repo: str,
) -> dict[str, Any]:
    """
    Analyze if issue mentioned in comment is still present

    This MCP tool compares the comment's suggestion against the current
    code state to determine if the issue is still valid.

    Args:
        comment_id: Comment ID to analyze
        pr_number: PR number
        repo: Repository in format "owner/repo"

    Returns:
        Dictionary with:
            - is_valid: Whether issue is still present
            - status: "needs_fix", "already_fixed", "invalid", or "uncertain"
            - confidence: Confidence score (0.0-1.0)
            - reasoning: Explanation of the assessment
            - suggested_action: What should be done

    Example:
        >>> analysis = await analyze_comment_validity(
        ...     comment_id="123456",
        ...     pr_number=69,
        ...     repo="MarkEnverus/my-repo"
        ... )
        >>> if analysis["status"] == "needs_fix":
        ...     print("Issue still present:", analysis["reasoning"])

    Note:
        This is a heuristic-based analysis. For best results, use Claude
        to interpret the comment body and code context together.
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

    # Perform heuristic analysis
    # This is a simplified implementation - in practice, you'd use
    # Claude or more sophisticated analysis

    analysis = _heuristic_analysis(comment.body, context.get("code_snippet", ""))

    result = ValidityAnalysis(
        comment_id=comment_id,
        is_valid=analysis["is_valid"],
        status=analysis["status"],
        confidence=analysis["confidence"],
        reasoning=analysis["reasoning"],
        suggested_action=analysis["suggested_action"],
    )

    return result.model_dump(mode="json")


def _heuristic_analysis(
    comment_body: str, code_snippet: str
) -> dict[str, Any]:
    """
    Perform heuristic analysis of comment vs code

    This is a simple implementation. In production, you'd use Claude
    to understand the comment and analyze the code.

    Args:
        comment_body: Comment text
        code_snippet: Code context

    Returns:
        Analysis results
    """
    comment_lower = comment_body.lower()
    code_lower = code_snippet.lower()

    # Check for null/undefined checks
    if "null" in comment_lower or "undefined" in comment_lower:
        has_null_check = (
            "if" in code_lower
            and (
                "null" in code_lower
                or "undefined" in code_lower
                or "!=" in code_snippet
                or "is not none" in code_lower
            )
        )

        if has_null_check:
            return {
                "is_valid": False,
                "status": ValidityStatus.ALREADY_FIXED,
                "confidence": 0.7,
                "reasoning": "Code appears to have null/undefined check present",
                "suggested_action": "Verify the fix is correct and resolve thread",
            }
        else:
            return {
                "is_valid": True,
                "status": ValidityStatus.NEEDS_FIX,
                "confidence": 0.8,
                "reasoning": "No null/undefined check found in code",
                "suggested_action": "Add appropriate null check as suggested",
            }

    # Check for error handling
    if "error" in comment_lower or "exception" in comment_lower:
        has_error_handling = (
            "try" in code_lower
            or "catch" in code_lower
            or "except" in code_lower
            or "raise" in code_lower
        )

        if has_error_handling:
            return {
                "is_valid": False,
                "status": ValidityStatus.ALREADY_FIXED,
                "confidence": 0.6,
                "reasoning": "Error handling appears to be present",
                "suggested_action": "Review error handling and resolve if adequate",
            }
        else:
            return {
                "is_valid": True,
                "status": ValidityStatus.NEEDS_FIX,
                "confidence": 0.7,
                "reasoning": "No error handling found",
                "suggested_action": "Add error handling as suggested",
            }

    # Check for type hints/types
    if "type" in comment_lower:
        has_types = (
            ":" in code_snippet
            or "type" in code_lower
            or "->" in code_snippet
        )

        if has_types:
            return {
                "is_valid": False,
                "status": ValidityStatus.ALREADY_FIXED,
                "confidence": 0.6,
                "reasoning": "Type annotations appear to be present",
                "suggested_action": "Verify types and resolve thread",
            }

    # Default: uncertain
    return {
        "is_valid": False,  # Default to False for uncertain cases
        "status": ValidityStatus.UNCERTAIN,
        "confidence": 0.3,
        "reasoning": "Unable to automatically determine validity. Manual review recommended.",
        "suggested_action": "Review comment and code manually, or use Claude for deeper analysis",
    }


async def batch_analyze_comments(
    pr_number: int,
    repo: str,
    filters: dict[str, Any] = None,
) -> dict[str, Any]:
    """
    Analyze multiple comments at once with prioritization

    This MCP tool fetches and analyzes all comments matching filters,
    then categorizes and prioritizes them.

    Args:
        pr_number: PR number
        repo: Repository in format "owner/repo"
        filters: Same filters as fetch_pr_comments

    Returns:
        Dictionary with:
            - total_comments: Total number of comments analyzed
            - categories: Breakdown by category (security, quality, bugs)
            - priorities: List of comments with priority scores
            - by_status: Breakdown by validity status

    Example:
        >>> result = await batch_analyze_comments(
        ...     pr_number=69,
        ...     repo="MarkEnverus/my-repo",
        ...     filters={"authors": ["github-copilot"]}
        ... )
        >>> print(f"Found {result['total_comments']} comments")
        >>> print(f"High priority: {len([p for p in result['priorities'] if p['priority'] == 'high'])}")
    """
    # Import here to avoid circular dependency
    from .comments import fetch_pr_comments

    # Fetch comments
    comments_data = await fetch_pr_comments(pr_number, repo, filters)

    # Categorize comments
    categories = defaultdict(int)
    priorities = []
    by_status = defaultdict(int)

    for comment_data in comments_data:
        comment_id = comment_data["id"]
        body = comment_data["body"].lower()

        # Categorize
        category = _categorize_comment(body)
        categories[category] += 1

        # Determine priority
        priority = _determine_priority(body)

        # Analyze validity (simplified - don't call full analysis to avoid slowdown)
        status = ValidityStatus.UNCERTAIN

        priorities.append(
            {
                "comment_id": comment_id,
                "priority": priority.value,
                "category": category,
                "author": comment_data["author"],
                "file_path": comment_data.get("file_path"),
                "line_number": comment_data.get("line_number"),
                "preview": body[:100] + "..." if len(body) > 100 else body,
            }
        )

        by_status[status.value] += 1

    # Sort priorities by priority level
    priority_order = {"high": 0, "medium": 1, "low": 2}
    priorities.sort(key=lambda x: priority_order.get(x["priority"], 3))

    result = BatchAnalysisResult(
        total_comments=len(comments_data),
        categories=dict(categories),
        priorities=priorities,
        by_status=dict(by_status),
    )

    return result.model_dump(mode="json")


def _categorize_comment(body: str) -> str:
    """Categorize comment by content"""
    body_lower = body.lower()

    security_keywords = [
        "security",
        "vulnerability",
        "injection",
        "xss",
        "sql",
        "auth",
    ]
    bug_keywords = [
        "bug",
        "error",
        "crash",
        "exception",
        "null",
        "undefined",
        "race condition",
    ]
    quality_keywords = [
        "refactor",
        "extract",
        "simplify",
        "complexity",
        "duplicate",
        "naming",
    ]
    performance_keywords = [
        "performance",
        "optimize",
        "slow",
        "memory",
        "leak",
    ]

    if any(kw in body_lower for kw in security_keywords):
        return "security"
    elif any(kw in body_lower for kw in bug_keywords):
        return "bugs"
    elif any(kw in body_lower for kw in performance_keywords):
        return "performance"
    elif any(kw in body_lower for kw in quality_keywords):
        return "quality"
    else:
        return "other"


def _determine_priority(body: str) -> Priority:
    """Determine comment priority"""
    body_lower = body.lower()

    high_priority = [
        "security",
        "vulnerability",
        "critical",
        "injection",
        "authentication",
        "crash",
    ]
    medium_priority = [
        "bug",
        "error",
        "performance",
        "memory",
        "race condition",
    ]

    if any(kw in body_lower for kw in high_priority):
        return Priority.HIGH
    elif any(kw in body_lower for kw in medium_priority):
        return Priority.MEDIUM
    else:
        return Priority.LOW
