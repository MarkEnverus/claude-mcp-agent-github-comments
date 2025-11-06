"""
MCP Tools for GitHub PR Comment Management

Provides discrete tools for:
- Fetching and filtering PR comments
- Analyzing comment validity
- Managing code fixes
- Resolving comment threads
"""

from .analysis import analyze_comment_validity, batch_analyze_comments
from .code_ops import (
    apply_code_fix,
    create_comment_reply,
    get_pr_diff,
    resolve_thread,
)
from .comments import fetch_pr_comments, get_comment_context
from .smart_analysis import (
    analyze_comment_smart,
    get_bot_comment_filters,
    is_bot_comment,
)

__all__ = [
    "fetch_pr_comments",
    "get_comment_context",
    "analyze_comment_validity",
    "batch_analyze_comments",
    "apply_code_fix",
    "get_pr_diff",
    "create_comment_reply",
    "resolve_thread",
    # Phase 1.5: Smart analysis
    "analyze_comment_smart",
    "is_bot_comment",
    "get_bot_comment_filters",
]
