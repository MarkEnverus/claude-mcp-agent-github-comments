"""
MCP Server for GitHub PR Comment Management

This module sets up and runs the MCP server that exposes
GitHub PR comment management tools.
"""

import asyncio
import logging
import os
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .tools import (
    analyze_comment_validity,
    apply_code_fix,
    batch_analyze_comments,
    create_comment_reply,
    fetch_pr_comments,
    get_comment_context,
    get_pr_diff,
    resolve_thread,
)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
log_file = os.getenv("MCP_LOG_FILE")

log_config = {
    "level": getattr(logging, log_level.upper()),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

if log_file:
    log_config["filename"] = log_file
    log_config["filemode"] = "a"

logging.basicConfig(**log_config)
logger = logging.getLogger("github-pr-mcp")

# Log startup
logger.info("=" * 80)
logger.info("GitHub PR Comment MCP Server Starting")
logger.info(f"Log Level: {log_level}")
if log_file:
    logger.info(f"Logging to: {log_file}")
logger.info("=" * 80)


def create_github_pr_mcp_server(
    server_name: str = "github-pr-comments",
    version: str = "0.1.0",
) -> Server:
    """
    Create and configure MCP server for GitHub PR comments

    Args:
        server_name: Name of the MCP server
        version: Server version

    Returns:
        Configured MCP Server instance
    """
    # Create MCP server
    server = Server(server_name)

    # Register tools
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List all available tools"""
        return [
            Tool(
                name="fetch_pr_comments",
                description=(
                    "Fetch PR comments with intelligent filtering. "
                    "Filter by authors (e.g., github-copilot), status (open/resolved), "
                    "comment types, keywords, and age. Returns structured comment data."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pr_number": {
                            "type": "integer",
                            "description": "PR number to fetch comments from",
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository in format 'owner/repo'",
                        },
                        "filters": {
                            "type": "object",
                            "description": "Optional filters",
                            "properties": {
                                "authors": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Filter by comment authors",
                                },
                                "status": {
                                    "type": "string",
                                    "enum": ["open", "resolved", "all"],
                                    "description": "Filter by comment status",
                                },
                                "keywords": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Keywords to search for in comment body",
                                },
                                "min_age_days": {
                                    "type": "integer",
                                    "description": "Only include comments older than N days",
                                },
                            },
                        },
                    },
                    "required": ["pr_number", "repo"],
                },
            ),
            Tool(
                name="get_comment_context",
                description=(
                    "Get code context around a comment's location. "
                    "Returns the code snippet with surrounding lines, diff hunk, "
                    "and related changes in the PR."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "comment_id": {
                            "type": "string",
                            "description": "Comment ID",
                        },
                        "pr_number": {
                            "type": "integer",
                            "description": "PR number",
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository in format 'owner/repo'",
                        },
                        "lines_before": {
                            "type": "integer",
                            "description": "Lines to show before comment location",
                            "default": 10,
                        },
                        "lines_after": {
                            "type": "integer",
                            "description": "Lines to show after comment location",
                            "default": 10,
                        },
                    },
                    "required": ["comment_id", "pr_number", "repo"],
                },
            ),
            Tool(
                name="analyze_comment_validity",
                description=(
                    "Analyze if the issue mentioned in a comment is still present. "
                    "Compares comment suggestion vs current code state. "
                    "Returns validity status, confidence score, and reasoning."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "comment_id": {
                            "type": "string",
                            "description": "Comment ID to analyze",
                        },
                        "pr_number": {
                            "type": "integer",
                            "description": "PR number",
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository in format 'owner/repo'",
                        },
                    },
                    "required": ["comment_id", "pr_number", "repo"],
                },
            ),
            Tool(
                name="batch_analyze_comments",
                description=(
                    "Analyze multiple comments at once with categorization and prioritization. "
                    "Returns breakdown by category (security, quality, bugs), priority levels, "
                    "and validity status."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pr_number": {
                            "type": "integer",
                            "description": "PR number",
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository in format 'owner/repo'",
                        },
                        "filters": {
                            "type": "object",
                            "description": "Same filters as fetch_pr_comments",
                        },
                    },
                    "required": ["pr_number", "repo"],
                },
            ),
            Tool(
                name="apply_code_fix",
                description=(
                    "Apply a code fix to address a PR comment. "
                    "Modifies the file, creates a git commit, and returns the diff. "
                    "Does NOT push to remote."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to file (relative to repo root)",
                        },
                        "line_number": {
                            "type": "integer",
                            "description": "Line number to modify",
                        },
                        "fix_content": {
                            "type": "string",
                            "description": "New code content to apply",
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository in format 'owner/repo'",
                        },
                        "commit_message": {
                            "type": "string",
                            "description": "Custom commit message (optional)",
                        },
                        "repo_path": {
                            "type": "string",
                            "description": "Local path to repository (optional)",
                        },
                    },
                    "required": ["file_path", "line_number", "fix_content", "repo"],
                },
            ),
            Tool(
                name="get_pr_diff",
                description=(
                    "Get full unified diff for a PR showing all changes."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pr_number": {
                            "type": "integer",
                            "description": "PR number",
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository in format 'owner/repo'",
                        },
                    },
                    "required": ["pr_number", "repo"],
                },
            ),
            Tool(
                name="create_comment_reply",
                description=(
                    "Reply to a PR comment thread with a message."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "comment_id": {
                            "type": "string",
                            "description": "Comment ID to reply to",
                        },
                        "pr_number": {
                            "type": "integer",
                            "description": "PR number",
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository in format 'owner/repo'",
                        },
                        "message": {
                            "type": "string",
                            "description": "Reply message text",
                        },
                    },
                    "required": ["comment_id", "pr_number", "repo", "message"],
                },
            ),
            Tool(
                name="resolve_thread",
                description=(
                    "Mark a comment thread as resolved. "
                    "Note: Full implementation requires GraphQL API. "
                    "Current implementation is a placeholder."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "comment_id": {
                            "type": "string",
                            "description": "Comment/thread ID to resolve",
                        },
                        "pr_number": {
                            "type": "integer",
                            "description": "PR number",
                        },
                        "repo": {
                            "type": "string",
                            "description": "Repository in format 'owner/repo'",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Optional reason for resolution",
                        },
                    },
                    "required": ["comment_id", "pr_number", "repo"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Call a tool by name with arguments"""
        logger.info(f"Tool called: {name}")
        logger.debug(f"Arguments: {arguments}")

        try:
            result = None

            if name == "fetch_pr_comments":
                result = await fetch_pr_comments(**arguments)
            elif name == "get_comment_context":
                result = await get_comment_context(**arguments)
            elif name == "analyze_comment_validity":
                result = await analyze_comment_validity(**arguments)
            elif name == "batch_analyze_comments":
                result = await batch_analyze_comments(**arguments)
            elif name == "apply_code_fix":
                result = await apply_code_fix(**arguments)
            elif name == "get_pr_diff":
                result = await get_pr_diff(**arguments)
            elif name == "create_comment_reply":
                result = await create_comment_reply(**arguments)
            elif name == "resolve_thread":
                result = await resolve_thread(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            # Convert result to string if it's not already
            if isinstance(result, str):
                content = result
            else:
                import json
                content = json.dumps(result, indent=2)

            logger.info(f"Tool {name} completed successfully")
            logger.debug(f"Result length: {len(content)} chars")

            return [TextContent(type="text", text=content)]

        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}",
                )
            ]

    return server


async def main():
    """Run the MCP server"""
    # Check for required environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")

    if not github_token:
        logger.error("GITHUB_TOKEN environment variable is required")
        sys.exit(1)

    if not github_repo:
        logger.warning("GITHUB_REPO not set. Will need to specify in each call.")

    logger.info("Starting GitHub PR Comment MCP Server")
    logger.info(f"Repository: {github_repo or 'Not set - specify per call'}")

    # Create server
    server = create_github_pr_mcp_server()

    # Run server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
