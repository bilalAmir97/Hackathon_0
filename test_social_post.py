#!/usr/bin/env python3
"""
Test script for posting to Facebook and Instagram about gold tier progress.
"""
import asyncio
import sys
from pathlib import Path

# Add mcp_servers to path
sys.path.insert(0, str(Path(__file__).parent / "mcp_servers"))

from meta_graph_client import MetaGraphClient, create_approval_request_file, generate_approval_id
from image_validator import ImageValidator

async def test_social_posts():
    """Create test posts for Facebook and Instagram."""

    # Image path
    image_path = "/mnt/d/Bilal/Bilal/Bilal_Data/Hackathon/Hackathon_0/test_post.png"

    # Post content
    caption = """🎉 Gold Tier Progress Update!

All 27 tests passing! Our AI Employee system now has comprehensive test coverage:
✅ Facebook & Instagram MCP Server (7/7)
✅ Meta Graph Client (9/9)
✅ Rate Limiter (11/11)

Building towards full cross-domain integration with robust error handling and audit logging.

#AIEmployee #GoldTier #TestDrivenDevelopment #Hackathon"""

    # Validate image
    validator = ImageValidator()

    print("Validating image for Facebook...")
    fb_valid, fb_msg = validator.validate_for_facebook(image_path)
    if not fb_valid:
        print(f"❌ Facebook validation failed: {fb_msg}")
        return
    print(f"✅ Facebook validation passed: {fb_msg}")

    print("\nValidating image for Instagram...")
    ig_valid, ig_msg = validator.validate_for_instagram(image_path)
    if not ig_valid:
        print(f"❌ Instagram validation failed: {ig_msg}")
        return
    print(f"✅ Instagram validation passed: {ig_msg}")

    # Create approval requests
    print("\n" + "="*60)
    print("Creating approval requests...")
    print("="*60)

    # Facebook approval request
    fb_approval_id = generate_approval_id()
    fb_request = {
        "approval_id": fb_approval_id,
        "action": "facebook_post_image",
        "parameters": {
            "image_path": image_path,
            "caption": caption
        },
        "timestamp": None  # Will be set by create_approval_request_file
    }

    fb_file = create_approval_request_file(fb_request)
    print(f"\n📝 Facebook approval request created: {fb_file}")

    # Instagram approval request
    ig_approval_id = generate_approval_id()
    ig_request = {
        "approval_id": ig_approval_id,
        "action": "instagram_post_image",
        "parameters": {
            "image_path": image_path,
            "caption": caption
        },
        "timestamp": None  # Will be set by create_approval_request_file
    }

    ig_file = create_approval_request_file(ig_request)
    print(f"📝 Instagram approval request created: {ig_file}")

    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Review the approval requests in AI_Employee_Vault/Needs_Approval/")
    print("2. Move approved requests to AI_Employee_Vault/Approved/")
    print("3. The approval executor will process them and post to social media")
    print("\nOr run the approval executor manually:")
    print("  python scripts/approval_executor.py")

if __name__ == "__main__":
    asyncio.run(test_social_posts())
