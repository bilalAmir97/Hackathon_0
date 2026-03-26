#!/usr/bin/env python3
"""
Quick CLI test for Facebook posting - creates approval request
Usage: uv run python tests/test_facebook_post_cli.py "Post text here"
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.facebook_instagram_mcp_server import facebook_post_text_handler


async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python tests/test_facebook_post_cli.py 'Post text here'")
        print("Example: uv run python tests/test_facebook_post_cli.py 'Hello from AI Employee! 🚀'")
        sys.exit(1)

    message = sys.argv[1]

    print("=" * 70)
    print("  📘 Facebook Post Test")
    print("=" * 70)
    print(f"  Message: {message}")
    print("=" * 70)
    print()

    try:
        # Create approval request
        print("📝 Creating approval request...")
        result = await facebook_post_text_handler({
            "message": message
        })

        print()
        print("=" * 70)

        if result["success"]:
            print("  ✅ APPROVAL REQUEST CREATED!")
            print("=" * 70)
            print(f"  Approval ID: {result['approval_id']}")
            print(f"  Approval File: {result['approval_file']}")
            print()
            print("📋 Next steps:")
            print(f"  1. Review the approval file: {result['approval_file']}")
            print(f"  2. Move it to AI_Employee_Vault/Approved/ to post")
            print(f"  3. The approval executor will post it to Facebook")
            print()
        else:
            print("  ❌ FAILED")
            print("=" * 70)
            print(f"  Error: {result['error']}")
            print()
            sys.exit(1)

    except Exception as e:
        print()
        print("=" * 70)
        print("  ❌ FAILED")
        print("=" * 70)
        print(f"  Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
