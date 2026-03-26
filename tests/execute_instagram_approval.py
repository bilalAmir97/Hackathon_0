#!/usr/bin/env python3
"""
Manually execute an Instagram post approval for testing
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.facebook_instagram_mcp_server import execute_instagram_post_image


def main():
    # Read the approval file
    approval_file = Path("AI_Employee_Vault/Approved/SOCIAL_INSTAGRAM_POST_IMAGE_20260325_182254.md")

    if not approval_file.exists():
        print(f"❌ Approval file not found: {approval_file}")
        return

    print("=" * 70)
    print("  📸 Executing Instagram Post Approval")
    print("=" * 70)
    print()

    # Parse the approval file to extract metadata
    content = approval_file.read_text()

    # Extract approval ID
    approval_id = "SOCIAL_INSTAGRAM_POST_IMAGE_20260325_182254"

    # Extract metadata JSON
    import re
    json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        metadata = json.loads(json_match.group(1))

        print(f"Approval ID: {approval_id}")
        print(f"Account ID: {metadata['account_id']}")
        print(f"Caption: {metadata['caption'][:100]}...")
        print(f"Image: {metadata['image_path']}")
        print()

        # Execute the post
        print("📤 Posting to Instagram...")
        try:
            result = execute_instagram_post_image(approval_id, metadata)

            print()
            print("=" * 70)
            if result.get("success"):
                print("  ✅ INSTAGRAM POST SUCCESSFUL!")
                print("=" * 70)
                print(f"  Media ID: {result.get('media_id')}")
                print(f"  Permalink: {result.get('permalink')}")
                print(f"  Created: {result.get('created_time')}")
                print()

                # Move to Done folder
                done_file = Path("AI_Employee_Vault/Done") / approval_file.name
                approval_file.rename(done_file)
                print(f"✓ Moved approval to Done folder")
            else:
                print("  ❌ INSTAGRAM POST FAILED")
                print("=" * 70)
                print(f"  Error: {result.get('error')}")
                print()

                # Move to quarantine
                quarantine_file = Path("AI_Employee_Vault/.quarantine") / approval_file.name
                approval_file.rename(quarantine_file)
                print(f"✓ Moved approval to quarantine")

        except Exception as e:
            print()
            print("=" * 70)
            print("  ❌ EXECUTION FAILED")
            print("=" * 70)
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ Could not parse metadata from approval file")


if __name__ == '__main__':
    main()
