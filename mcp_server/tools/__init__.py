"""
MCP Tools for GitHub PR Comment Management

Provides discrete tools for:
- Fetching and filtering PR comments
- Analyzing comment validity
- Managing code fixes
- Resolving comment threads
"""

from .comments import fetch_pr_comments, get_comment_context
from .analysis import analyze_comment_validity, batch_analyze_comments
from .code_ops import (
    apply_code_fix,
    get_pr_diff,
    create_comment_reply,
    resolve_thread,
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
]
