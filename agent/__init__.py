"""
Claude Agent for GitHub PR Comment Management

Intelligent orchestration layer that uses Claude Agent SDK to manage
complex PR comment review workflows.
"""

from .pr_comment_agent import PRCommentAgent

__all__ = ["PRCommentAgent"]
