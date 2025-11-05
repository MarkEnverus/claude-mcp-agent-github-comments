#!/usr/bin/env python3
"""
Apply Phase 1.5 fixes to PR #72

Interactive workflow to:
1. Apply suggested code fixes
2. Post replies to comments
3. Resolve threads
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from mcp_server.tools import (
    fetch_pr_comments,
    analyze_comment_smart,
    get_bot_comment_filters,
    create_comment_reply,
    resolve_thread,
)


async def main():
    print("=" * 80)
    print("PR #72 Fix Application Workflow")
    print("=" * 80)
    print("\nThis script will help you apply Phase 1.5 fixes to PR #72\n")

    repo = "enverus-nv/genai-idp"
    pr_number = 72

    if not os.getenv("GITHUB_TOKEN"):
        print("❌ ERROR: GITHUB_TOKEN not set!")
        sys.exit(1)

    # Step 1: Fetch fixable comments
    print("Step 1: Finding auto-fixable comments...")
    print("-" * 80)

    bot_comments = await fetch_pr_comments(
        pr_number=pr_number,
        repo=repo,
        filters=get_bot_comment_filters()
    )

    fixable = []
    for comment in bot_comments:
        try:
            analysis = await analyze_comment_smart(
                comment_id=comment['id'],
                pr_number=pr_number,
                repo=repo
            )

            if analysis.get('can_auto_fix') and analysis['confidence'] >= 0.7:
                fixable.append({
                    'comment': comment,
                    'analysis': analysis
                })
        except:
            pass

    print(f"\n✅ Found {len(fixable)} auto-fixable comments\n")

    # Step 2: Show fixes and get confirmation
    print("\nStep 2: Review suggested fixes")
    print("-" * 80)

    for i, item in enumerate(fixable, 1):
        comment = item['comment']
        analysis = item['analysis']

        print(f"\n{'=' * 80}")
        print(f"FIX #{i} of {len(fixable)}")
        print(f"{'=' * 80}")

        print(f"\n📍 Location:")
        print(f"   File: {comment.get('file_path')}")
        print(f"   Line: {comment.get('line_number')}")

        print(f"\n💬 Comment (ID: {comment['id']}):")
        body = comment['body']
        if len(body) > 200:
            body = body[:200] + "..."
        print(f"   {body}")

        print(f"\n📊 Analysis:")
        print(f"   Pattern: {analysis.get('pattern_detected')}")
        print(f"   Confidence: {analysis['confidence']:.2f}")
        print(f"   Status: {analysis['status']}")

        if analysis.get('suggested_fix'):
            fix = analysis['suggested_fix']
            print(f"\n🔧 Suggested Fix:")
            print(f"   Original: {fix.get('original', 'N/A')}")
            print(f"   Fixed:    {fix.get('fixed', 'N/A')}")
            print(f"   Explanation: {fix.get('explanation', 'N/A')}")

        if analysis.get('reply_template'):
            print(f"\n📝 Reply Template:")
            print(f"   {analysis['reply_template']}")

    # Step 3: Manual fix instructions
    print("\n\n" + "=" * 80)
    print("Step 3: Apply Fixes Manually")
    print("=" * 80)

    print("""
Since we're working on a remote repository (enverus-nv/genai-idp),
you'll need to apply these fixes manually. Here's the workflow:

📋 FIXES TO APPLY:
""")

    # Group by file
    by_file = {}
    for item in fixable:
        file_path = item['comment'].get('file_path', 'unknown')
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(item)

    for file_path, items in by_file.items():
        print(f"\n{'─' * 80}")
        print(f"📄 File: {file_path}")
        print(f"{'─' * 80}")

        for item in items:
            comment = item['comment']
            analysis = item['analysis']

            print(f"\n  • Line {comment.get('line_number')}:")
            print(f"    Pattern: {analysis.get('pattern_detected')}")

            if analysis.get('suggested_fix'):
                fix = analysis['suggested_fix']
                if fix.get('original'):
                    print(f"    Change:")
                    print(f"      FROM: {fix['original']}")
                    print(f"      TO:   {fix['fixed']}")

            print(f"    Comment ID: {comment['id']}")

    # Step 4: Post replies and resolve
    print("\n\n" + "=" * 80)
    print("Step 4: Post Replies and Resolve Threads")
    print("=" * 80)

    print("\nAfter applying the fixes above, run this to post replies:")
    print("\n" + "─" * 80)

    for i, item in enumerate(fixable, 1):
        comment = item['comment']
        analysis = item['analysis']
        reply = analysis.get('reply_template', 'Fixed!')

        print(f"\n# Fix #{i}")
        print(f"# Comment ID: {comment['id']}")
        print(f"# File: {comment.get('file_path')}:{comment.get('line_number')}")
        print(f"await create_comment_reply(")
        print(f"    comment_id='{comment['id']}',")
        print(f"    pr_number={pr_number},")
        print(f"    repo='{repo}',")
        print(f"    message='{reply}'")
        print(f")")
        print(f"await resolve_thread(")
        print(f"    comment_id='{comment['id']}',")
        print(f"    pr_number={pr_number},")
        print(f"    repo='{repo}'")
        print(f")")

    # Step 5: Interactive mode
    print("\n\n" + "=" * 80)
    print("Step 5: Interactive Mode")
    print("=" * 80)

    response = input("\nWould you like to post replies now? (y/N): ")

    if response.lower() == 'y':
        print("\n🚀 Posting replies and resolving threads...\n")

        for i, item in enumerate(fixable, 1):
            comment = item['comment']
            analysis = item['analysis']
            reply = analysis.get('reply_template', 'Fixed!')

            print(f"\n{i}. Replying to comment {comment['id']}...")
            print(f"   Message: {reply[:60]}...")

            try:
                # Post reply
                reply_result = await create_comment_reply(
                    comment_id=comment['id'],
                    pr_number=pr_number,
                    repo=repo,
                    message=reply
                )

                print(f"   ✅ Reply posted: {reply_result.get('url', 'success')}")

                # Resolve thread
                resolve_result = await resolve_thread(
                    comment_id=comment['id'],
                    pr_number=pr_number,
                    repo=repo,
                    reason=f"Fixed per Phase 1.5 analysis"
                )

                print(f"   ✅ Thread resolved")

            except Exception as e:
                print(f"   ❌ Error: {e}")

        print("\n" + "=" * 80)
        print("✅ All replies posted and threads resolved!")
        print("=" * 80)
    else:
        print("\n📋 Skipped posting replies.")
        print("   You can post them manually using the code above.")

    # Step 6: Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"""
✅ Analysis Complete:
   - {len(fixable)} comments can be auto-fixed
   - {len(by_file)} files need changes
   - High confidence fixes ready to apply

📝 Next Steps:
   1. Clone the repo: git clone git@github.com:enverus-nv/genai-idp.git
   2. Checkout PR branch: gh pr checkout 72
   3. Apply the fixes shown above
   4. Commit: git commit -am "fix: address PR comments from bots"
   5. Push: git push
   6. Run this script again with 'y' to post replies

Or, if you've already applied the fixes:
   - Run this script again
   - Answer 'y' when prompted
   - Replies will be posted and threads resolved

🎉 Phase 1.5 makes this easy!
""")


if __name__ == "__main__":
    asyncio.run(main())
