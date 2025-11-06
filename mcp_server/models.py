"""
Pydantic models for GitHub PR comment data structures
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class CommentType(str, Enum):
    """Type of GitHub comment"""
    REVIEW_COMMENT = "review_comment"
    ISSUE_COMMENT = "issue_comment"
    REVIEW = "review"


class CommentStatus(str, Enum):
    """Status of comment thread"""
    OPEN = "open"
    RESOLVED = "resolved"
    OUTDATED = "outdated"


class ValidityStatus(str, Enum):
    """Validity assessment of a comment"""
    NEEDS_FIX = "needs_fix"
    ALREADY_FIXED = "already_fixed"
    INVALID = "invalid"
    UNCERTAIN = "uncertain"


class Priority(str, Enum):
    """Priority level for comments"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PRComment(BaseModel):
    """GitHub PR comment model"""
    id: str
    comment_type: CommentType
    author: str
    body: str
    created_at: datetime
    updated_at: datetime | None = None
    status: CommentStatus

    # Location information
    file_path: str | None = None
    line_number: int | None = None
    diff_hunk: str | None = None

    # Metadata
    url: HttpUrl
    html_url: HttpUrl
    pr_number: int
    repo: str

    # Analysis results (populated later)
    validity: ValidityStatus | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    priority: Priority | None = None


class CommentContext(BaseModel):
    """Code context around a comment"""
    comment_id: str
    file_path: str
    line_number: int
    code_snippet: str
    lines_before: int
    lines_after: int
    diff_hunk: str | None = None
    related_changes: list[str] = Field(default_factory=list)


class ValidityAnalysis(BaseModel):
    """Analysis of comment validity"""
    comment_id: str
    is_valid: bool
    status: ValidityStatus
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    suggested_action: str


class CodeFix(BaseModel):
    """Proposed code fix"""
    file_path: str
    line_number: int
    original_code: str
    fixed_code: str
    explanation: str
    commit_message: str | None = None


class FixResult(BaseModel):
    """Result of applying a code fix"""
    success: bool
    commit_sha: str | None = None
    diff: str | None = None
    files_changed: int = 0
    error: str | None = None


class CommentFilters(BaseModel):
    """Filters for fetching PR comments"""
    authors: list[str] | None = None
    status: CommentStatus | None = None
    types: list[CommentType] | None = None
    keywords: list[str] | None = None
    min_age_days: int = 0


class BatchAnalysisResult(BaseModel):
    """Result of batch comment analysis"""
    total_comments: int
    categories: dict[str, int] = Field(default_factory=dict)
    priorities: list[dict[str, Any]] = Field(default_factory=list)
    by_status: dict[ValidityStatus, int] = Field(default_factory=dict)
