#!/usr/bin/env python3
"""
Test script for real PR: https://github.com/enverus-nv/genai-idp/pull/72

This script will:
1. Fetch all comments from the PR
2. Analyze them for validity
3. Categorize and prioritize
4. Show what actions would be recommended
"""

import asyncio
import os
import sys

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


async def main():
    """Test on real PR"""
    print("=" * 80)
    print("Testing GitHub PR Comment Agent on Real PR")
    print("=" * 80)
    print("\nPR: https://github.com/enverus-nv/genai-idp/pull/72")

    # Configuration
    repo = "enverus-nv/genai-idp"
    pr_number = 72

    # Check environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("\n❌ ERROR: GITHUB_TOKEN not set!")
        print("   Please set GITHUB_TOKEN in .env file")
        sys.exit(1)

    print(f"\nRepository: {repo}")
    print(f"PR Number: {pr_number}")
    print(f"GitHub Token: {github_token[:10]}..." if github_token else "Not set")

    try:
        # Step 1: Fetch ALL comments
        print("\n" + "=" * 80)
        print("STEP 1: Fetching all comments from PR")
        print("=" * 80)

        all_comments = await fetch_pr_comments(
            pr_number=pr_number,
            repo=repo,
            filters={}  # No filters - get everything
        )

        print(f"\n✅ Found {len(all_comments)} total comments")

        if len(all_comments) == 0:
            print("\nNo comments found on this PR.")
            return

        # Show comment breakdown by author
        authors = {}
        for comment in all_comments:
            author = comment['author']
            authors[author] = authors.get(author, 0) + 1

        print("\nComments by author:")
        for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {author}: {count}")

        # Step 2: Fetch bot comments specifically
        print("\n" + "=" * 80)
        print("STEP 2: Fetching bot comments (Copilot, etc.)")
        print("=" * 80)

        bot_authors = [
            "github-copilot",
            "github-advanced-security",
            "dependabot",
            "snyk-bot",
        ]

        bot_comments = await fetch_pr_comments(
            pr_number=pr_number,
            repo=repo,
            filters={"authors": bot_authors}
        )

        print(f"\n✅ Found {len(bot_comments)} bot comments")

        if bot_comments:
            print("\nBot comments:")
            for comment in bot_comments[:5]:  # Show first 5
                print(f"\n  ID: {comment['id']}")
                print(f"  Author: {comment['author']}")
                print(f"  File: {comment['file_path']}:{comment['line_number']}")
                print(f"  Body: {comment['body'][:100]}...")

        # Step 3: Show first few comments in detail
        print("\n" + "=" * 80)
        print("STEP 3: Detailed view of first 3 comments")
        print("=" * 80)

        for i, comment in enumerate(all_comments[:3], 1):
            print(f"\n{'─' * 80}")
            print(f"Comment #{i}")
            print(f"{'─' * 80}")
            print(f"ID: {comment['id']}")
            print(f"Author: {comment['author']}")
            print(f"Type: {comment['comment_type']}")
            print(f"Status: {comment['status']}")
            print(f"Created: {comment['created_at']}")

            if comment.get('file_path'):
                print(f"Location: {comment['file_path']}:{comment['line_number']}")

            print(f"\nBody:\n{comment['body']}")

            if comment.get('diff_hunk'):
                print(f"\nDiff Hunk:\n{comment['diff_hunk']}")

        # Step 4: Get context for first comment with a file location
        print("\n" + "=" * 80)
        print("STEP 4: Get code context for a comment")
        print("=" * 80)

        # Find first comment with file location
        comment_with_file = next(
            (c for c in all_comments if c.get('file_path') and c.get('line_number')),
            None
        )

        if comment_with_file:
            print(f"\nGetting context for comment {comment_with_file['id']}...")
            print(f"File: {comment_with_file['file_path']}")
            print(f"Line: {comment_with_file['line_number']}")

            try:
                context = await get_comment_context(
                    comment_id=comment_with_file['id'],
                    pr_number=pr_number,
                    repo=repo,
                    lines_before=10,
                    lines_after=10
                )

                print("\n✅ Code context retrieved")
                print("\nCode snippet:")
                print(context['code_snippet'])

                if context.get('related_changes'):
                    print("\nRelated changes in PR:")
                    for change in context['related_changes'][:5]:
                        print(f"  - {change}")

            except Exception as e:
                print(f"\n⚠️  Could not get context: {e}")
        else:
            print("\nNo comments with file locations found")

        # Step 5: Analyze validity of comments
        print("\n" + "=" * 80)
        print("STEP 5: Analyze comment validity")
        print("=" * 80)

        # Analyze first comment with file location
        if comment_with_file:
            print(f"\nAnalyzing comment {comment_with_file['id']}...")

            try:
                analysis = await analyze_comment_validity(
                    comment_id=comment_with_file['id'],
                    pr_number=pr_number,
                    repo=repo
                )

                print("\n✅ Analysis complete")
                print(f"\nStatus: {analysis['status']}")
                print(f"Is Valid: {analysis['is_valid']}")
                print(f"Confidence: {analysis['confidence']:.2f}")
                print(f"\nReasoning: {analysis['reasoning']}")
                print(f"\nSuggested Action: {analysis['suggested_action']}")

            except Exception as e:
                print(f"\n⚠️  Could not analyze: {e}")

        # Step 6: Batch analysis
        print("\n" + "=" * 80)
        print("STEP 6: Batch analysis and categorization")
        print("=" * 80)

        print(f"\nAnalyzing all {len(all_comments)} comments...")

        batch_result = await batch_analyze_comments(
            pr_number=pr_number,
            repo=repo,
            filters={}  # Analyze all
        )

        print("\n✅ Batch analysis complete")
        print(f"\nTotal Comments: {batch_result['total_comments']}")

        print("\nCategories:")
        for category, count in sorted(
            batch_result['categories'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  - {category}: {count}")

        # Show priorities
        high_priority = [
            p for p in batch_result['priorities'] if p['priority'] == 'high'
        ]
        medium_priority = [
            p for p in batch_result['priorities'] if p['priority'] == 'medium'
        ]
        low_priority = [
            p for p in batch_result['priorities'] if p['priority'] == 'low'
        ]

        print("\nPriorities:")
        print(f"  - High: {len(high_priority)}")
        print(f"  - Medium: {len(medium_priority)}")
        print(f"  - Low: {len(low_priority)}")

        if high_priority:
            print("\nHigh Priority Comments:")
            for p in high_priority[:5]:
                print(f"\n  Comment ID: {p['comment_id']}")
                print(f"  Author: {p['author']}")
                print(f"  Category: {p['category']}")
                if p.get('file_path'):
                    print(f"  Location: {p['file_path']}:{p['line_number']}")
                print(f"  Preview: {p['preview'][:100]}...")

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        print(f"""
Total Comments: {len(all_comments)}
Bot Comments: {len(bot_comments)}
High Priority: {len(high_priority)}
Medium Priority: {len(medium_priority)}
Low Priority: {len(low_priority)}

Categories:
{chr(10).join(f"  - {cat}: {count}" for cat, count in batch_result['categories'].items())}

Top Authors:
{chr(10).join(f"  - {author}: {count}" for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5])}
""")

        print("\n✅ Test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
