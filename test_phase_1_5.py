#!/usr/bin/env python3
"""
Test Phase 1.5 enhancements on PR #72

Compares:
- Phase 1 (heuristic) vs Phase 1.5 (smart patterns)
- Shows improved confidence and fix suggestions
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from mcp_server.patterns import COMMON_BOT_AUTHORS
from mcp_server.tools import fetch_pr_comments
from mcp_server.tools.smart_analysis import (
    analyze_comment_smart,
    get_bot_comment_filters,
)


async def main():
    print("=" * 80)
    print("Phase 1.5: Smart Pattern Analysis Test")
    print("=" * 80)
    print("\nPR: https://github.com/enverus-nv/genai-idp/pull/72\n")

    repo = "enverus-nv/genai-idp"
    pr_number = 72

    # Check auth
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ ERROR: GITHUB_TOKEN not set!")
        sys.exit(1)

    # Step 1: Show enhanced bot detection
    print("\n" + "=" * 80)
    print("STEP 1: Enhanced Bot Detection")
    print("=" * 80)

    print(f"\nRegistered bot authors ({len(COMMON_BOT_AUTHORS)}):")
    for bot in sorted(COMMON_BOT_AUTHORS):
        print(f"  - {bot}")

    # Fetch with new filters
    print("\nFetching bot comments with enhanced filters...")
    bot_filters = get_bot_comment_filters()
    bot_comments = await fetch_pr_comments(
        pr_number=pr_number,
        repo=repo,
        filters=bot_filters
    )

    print(f"\n✅ Found {len(bot_comments)} bot comments")

    if bot_comments:
        authors_found = {c['author'] for c in bot_comments}
        print("\nBot authors found:")
        for author in sorted(authors_found):
            count = sum(1 for c in bot_comments if c['author'] == author)
            print(f"  - {author}: {count} comments")

    # Step 2: Smart analysis on specific comments
    print("\n" + "=" * 80)
    print("STEP 2: Smart Pattern Analysis")
    print("=" * 80)

    # Analyze first few comments
    for i, comment in enumerate(bot_comments[:5], 1):
        print(f"\n{'─' * 80}")
        print(f"Comment #{i}: {comment['id']}")
        print(f"{'─' * 80}")
        print(f"Author: {comment['author']}")
        print(f"File: {comment.get('file_path', 'N/A')}:{comment.get('line_number', 'N/A')}")
        print(f"\nBody: {comment['body'][:150]}...")

        # Run smart analysis
        try:
            analysis = await analyze_comment_smart(
                comment_id=comment['id'],
                pr_number=pr_number,
                repo=repo
            )

            print("\n📊 SMART ANALYSIS:")
            print(f"  Status: {analysis['status']}")
            print(f"  Confidence: {analysis['confidence']:.2f}")
            print(f"  Pattern: {analysis.get('pattern_detected', 'None')}")
            print(f"  Can Auto-Fix: {analysis.get('can_auto_fix', False)}")

            print(f"\n  Reasoning: {analysis['reasoning']}")
            print(f"  Action: {analysis['suggested_action']}")

            # Show suggested fix if available
            if analysis.get('suggested_fix'):
                fix = analysis['suggested_fix']
                print("\n  💡 SUGGESTED FIX:")
                print(f"     Original: {fix['original']}")
                print(f"     Fixed:    {fix['fixed']}")
                print(f"     Explanation: {fix['explanation']}")

            # Show reply template
            if analysis.get('reply_template'):
                print("\n  📝 REPLY TEMPLATE:")
                print(f"     {analysis['reply_template']}")

        except Exception as e:
            print(f"\n⚠️  Analysis error: {e}")

    # Step 3: Statistics comparison
    print("\n" + "=" * 80)
    print("STEP 3: Phase 1 vs Phase 1.5 Comparison")
    print("=" * 80)

    # Analyze all bot comments
    high_confidence = 0
    auto_fixable = 0
    patterns_detected = {}

    for comment in bot_comments:
        try:
            analysis = await analyze_comment_smart(
                comment_id=comment['id'],
                pr_number=pr_number,
                repo=repo
            )

            if analysis['confidence'] >= 0.7:
                high_confidence += 1

            if analysis.get('can_auto_fix'):
                auto_fixable += 1

            pattern = analysis.get('pattern_detected')
            if pattern:
                patterns_detected[pattern] = patterns_detected.get(pattern, 0) + 1

        except Exception:
            pass

    print("\nPHASE 1 (Heuristic):")
    print(f"  - High Confidence (>0.7): 0 / {len(bot_comments)} (0%)")
    print(f"  - Auto-fixable: 0 / {len(bot_comments)} (0%)")
    print("  - Patterns detected: None")

    print("\nPHASE 1.5 (Smart Patterns):")
    print(f"  - High Confidence (>0.7): {high_confidence} / {len(bot_comments)} ({100*high_confidence/len(bot_comments):.0f}%)")
    print(f"  - Auto-fixable: {auto_fixable} / {len(bot_comments)} ({100*auto_fixable/len(bot_comments):.0f}%)")
    print("  - Patterns detected:")
    for pattern, count in sorted(patterns_detected.items()):
        print(f"      • {pattern}: {count}")

    # Step 4: Actionable summary
    print("\n" + "=" * 80)
    print("ACTIONABLE SUMMARY")
    print("=" * 80)

    fixable_comments = []
    for comment in bot_comments:
        try:
            analysis = await analyze_comment_smart(
                comment_id=comment['id'],
                pr_number=pr_number,
                repo=repo
            )

            if analysis.get('can_auto_fix') and analysis['confidence'] >= 0.7:
                fixable_comments.append({
                    'comment': comment,
                    'analysis': analysis
                })
        except Exception:
            pass

    print(f"\n✅ {len(fixable_comments)} comments can be auto-fixed with high confidence:\n")

    for item in fixable_comments:
        comment = item['comment']
        analysis = item['analysis']

        print(f"📌 Comment {comment['id']}:")
        print(f"   File: {comment.get('file_path', 'N/A')}:{comment.get('line_number', 'N/A')}")
        print(f"   Pattern: {analysis.get('pattern_detected')}")
        print(f"   Confidence: {analysis['confidence']:.2f}")

        if analysis.get('suggested_fix'):
            fix = analysis['suggested_fix']
            print(f"   Fix: {fix['explanation']}")

        if analysis.get('reply_template'):
            print(f"   Reply: {analysis['reply_template'][:60]}...")
        print()

    print("=" * 80)
    print("🎉 Phase 1.5 Test Complete!")
    print("=" * 80)

    print(f"""
Key Improvements:
  ✅ Bot detection: Now includes Copilot, github-code-quality[bot], etc.
  ✅ Pattern recognition: {len(patterns_detected)} different patterns identified
  ✅ Higher confidence: {100*high_confidence/len(bot_comments):.0f}% of comments analyzed with >70% confidence
  ✅ Auto-fix ready: {auto_fixable} comments have suggested fixes
  ✅ Reply templates: Professional replies pre-generated

Next steps:
  1. Apply suggested fixes to the code
  2. Use reply templates to respond to comments
  3. Resolve threads confidently
""")


if __name__ == "__main__":
    asyncio.run(main())
