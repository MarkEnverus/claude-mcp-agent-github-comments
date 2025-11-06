#!/usr/bin/env python3
"""
Basic usage examples for GitHub PR Comment MCP tools

This script demonstrates how to use the MCP tools directly
from Python without the Agent SDK or CLI.
"""

import asyncio
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import MCP tools
from mcp_server.tools import (
    analyze_comment_validity,
    batch_analyze_comments,
    fetch_pr_comments,
    get_comment_context,
)


async def example_1_fetch_comments():
    """Example 1: Fetch all Copilot comments on a PR"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Fetch Copilot comments")
    print("=" * 80)

    repo = os.getenv("GITHUB_REPO", "MarkEnverus/my-repo")
    pr_number = 69  # Change to your PR number

    comments = await fetch_pr_comments(
        pr_number=pr_number,
        repo=repo,
        filters={"authors": ["github-copilot"]},
    )

    print(f"\nFound {len(comments)} Copilot comments on PR #{pr_number}")

    # Show first 3 comments
    for i, comment in enumerate(comments[:3], 1):
        print(f"\n{i}. Comment {comment['id']}:")
        print(f"   Author: {comment['author']}")
        print(f"   File: {comment['file_path']}:{comment['line_number']}")
        print(f"   Body: {comment['body'][:100]}...")

    return comments


async def example_2_get_context(comment_id: str, pr_number: int):
    """Example 2: Get code context for a comment"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Get code context")
    print("=" * 80)

    repo = os.getenv("GITHUB_REPO", "MarkEnverus/my-repo")

    context = await get_comment_context(
        comment_id=comment_id,
        pr_number=pr_number,
        repo=repo,
        lines_before=5,
        lines_after=5,
    )

    print(f"\nComment ID: {comment_id}")
    print(f"File: {context['file_path']}")
    print(f"Line: {context['line_number']}")
    print("\nCode Context:")
    print(context["code_snippet"])

    if context.get("diff_hunk"):
        print("\nDiff Hunk:")
        print(context["diff_hunk"])


async def example_3_analyze_validity(comment_id: str, pr_number: int):
    """Example 3: Analyze comment validity"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Analyze comment validity")
    print("=" * 80)

    repo = os.getenv("GITHUB_REPO", "MarkEnverus/my-repo")

    analysis = await analyze_comment_validity(
        comment_id=comment_id, pr_number=pr_number, repo=repo
    )

    print(f"\nComment ID: {comment_id}")
    print(f"Status: {analysis['status']}")
    print(f"Is Valid: {analysis['is_valid']}")
    print(f"Confidence: {analysis['confidence']:.2f}")
    print(f"\nReasoning: {analysis['reasoning']}")
    print(f"Suggested Action: {analysis['suggested_action']}")


async def example_4_batch_analysis(pr_number: int):
    """Example 4: Batch analyze all comments"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Batch analysis")
    print("=" * 80)

    repo = os.getenv("GITHUB_REPO", "MarkEnverus/my-repo")

    result = await batch_analyze_comments(
        pr_number=pr_number,
        repo=repo,
        filters={"authors": ["github-copilot", "github-advanced-security"]},
    )

    print(f"\nTotal Comments: {result['total_comments']}")
    print("\nCategories:")
    for category, count in result["categories"].items():
        print(f"  - {category}: {count}")

    print("\nPriorities:")
    high_priority = [
        p for p in result["priorities"] if p["priority"] == "high"
    ]
    medium_priority = [
        p for p in result["priorities"] if p["priority"] == "medium"
    ]
    low_priority = [
        p for p in result["priorities"] if p["priority"] == "low"
    ]

    print(f"  - High: {len(high_priority)}")
    print(f"  - Medium: {len(medium_priority)}")
    print(f"  - Low: {len(low_priority)}")

    if high_priority:
        print("\nHigh Priority Comments:")
        for p in high_priority[:3]:
            print(
                f"  - {p['file_path']}:{p['line_number']} ({p['category']})"
            )
            print(f"    {p['preview'][:80]}...")


async def example_5_complete_workflow():
    """Example 5: Complete workflow - fetch, analyze, report"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Complete workflow")
    print("=" * 80)

    repo = os.getenv("GITHUB_REPO", "MarkEnverus/my-repo")
    pr_number = 69  # Change to your PR number

    # Step 1: Fetch comments
    print("\n1. Fetching comments...")
    comments = await fetch_pr_comments(
        pr_number=pr_number,
        repo=repo,
        filters={"authors": ["github-copilot"]},
    )
    print(f"   Found {len(comments)} comments")

    # Step 2: Batch analyze
    print("\n2. Analyzing comments...")
    analysis = await batch_analyze_comments(
        pr_number=pr_number,
        repo=repo,
        filters={"authors": ["github-copilot"]},
    )

    # Step 3: Report
    print("\n3. Report:")
    print(f"   Total: {analysis['total_comments']}")
    print(f"   Categories: {', '.join(analysis['categories'].keys())}")

    # Step 4: Focus on high priority
    high_priority = [
        p for p in analysis["priorities"] if p["priority"] == "high"
    ]

    if high_priority:
        print(f"\n4. High Priority Issues ({len(high_priority)}):")
        for p in high_priority[:5]:
            print(f"\n   Comment: {p['comment_id']}")
            print(f"   File: {p['file_path']}:{p['line_number']}")
            print(f"   Category: {p['category']}")
            print(f"   Preview: {p['preview'][:100]}")

            # Get detailed analysis for first one
            if p == high_priority[0]:
                print("\n   Detailed Analysis:")
                validity = await analyze_comment_validity(
                    comment_id=p["comment_id"],
                    pr_number=pr_number,
                    repo=repo,
                )
                print(f"     Status: {validity['status']}")
                print(f"     Confidence: {validity['confidence']:.2f}")
                print(f"     Reasoning: {validity['reasoning']}")
    else:
        print("\n4. No high priority issues found!")


async def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("GitHub PR Comment MCP Tools - Basic Usage Examples")
    print("=" * 80)

    # Check environment
    if not os.getenv("GITHUB_TOKEN"):
        print("\n❌ ERROR: GITHUB_TOKEN not set!")
        print("   Please set GITHUB_TOKEN in .env file or environment")
        return

    if not os.getenv("GITHUB_REPO"):
        print("\n⚠️  WARNING: GITHUB_REPO not set!")
        print("   Using default: MarkEnverus/my-repo")
        print("   Set GITHUB_REPO in .env for your repository")

    pr_number = 69  # Change to your PR number

    try:
        # Run examples
        # Example 1: Fetch comments
        comments = await example_1_fetch_comments()

        if comments:
            # Use first comment for remaining examples
            first_comment_id = comments[0]["id"]

            # Example 2: Get context
            await example_2_get_context(first_comment_id, pr_number)

            # Example 3: Analyze validity
            await example_3_analyze_validity(first_comment_id, pr_number)

        # Example 4: Batch analysis
        await example_4_batch_analysis(pr_number)

        # Example 5: Complete workflow
        await example_5_complete_workflow()

        print("\n" + "=" * 80)
        print("✅ All examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
