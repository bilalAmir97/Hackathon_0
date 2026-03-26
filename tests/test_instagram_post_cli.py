#!/usr/bin/env python3
"""
Quick CLI test for Instagram posting - creates approval request
Usage: uv run python tests/test_instagram_post_cli.py "path/to/image.jpg" "Caption text"
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.facebook_instagram_mcp_server import instagram_post_image_handler


async def main():
    if len(sys.argv) < 3:
        print("Usage: uv run python tests/test_instagram_post_cli.py 'path/to/image.jpg' 'Caption text'")
        print("Example: uv run python tests/test_instagram_post_cli.py 'test_image.jpg' 'Hello from AI Employee! 🚀'")
        sys.exit(1)

    image_path = sys.argv[1]
    caption = sys.argv[2]

    # Verify image exists
    if not Path(image_path).exists():
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)

    print("=" * 70)
    print("  📸 Instagram Post Test")
    print("=" * 70)
    print(f"  Image: {image_path}")
    print(f"  Caption: {caption}")
    print("=" * 70)
    print()

    try:
        # Create approval request
        print("📝 Creating approval request...")
        result = await instagram_post_image_handler({
            "image_path": image_path,
            "caption": caption
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
            print(f"  3. The approval executor will post it to Instagram")
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
