#!/usr/bin/env python3
"""
Test Facebook API credentials and posting capability
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.meta_graph_client import MetaGraphClient


def main():
    print("=" * 70)
    print("  🔍 Facebook API Credentials Test")
    print("=" * 70)
    print()

    # Get credentials from .env
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")

    print(f"Page ID: {page_id}")
    print(f"Token: {token[:20]}...{token[-10:] if token else 'NOT SET'}")
    print()

    if not token or not page_id:
        print("❌ Facebook credentials not configured in .env")
        return

    # Create Meta client
    print("📡 Testing Facebook API connection...")
    try:
        client = MetaGraphClient()

        # Test API call - get page info
        url = f"{client.api_url}/{page_id}"
        params = {
            "access_token": token,
            "fields": "id,name,category,fan_count"
        }

        response = client._make_request("GET", url, params=params)

        if response.status_code == 200:
            data = response.json()
            print("✅ Facebook API connection successful!")
            print()
            print(f"Page Info:")
            print(f"  ID: {data.get('id')}")
            print(f"  Name: {data.get('name')}")
            print(f"  Category: {data.get('category')}")
            print(f"  Fans: {data.get('fan_count', 'N/A')}")
            print()

            # Try to post a test message
            print("📝 Testing post capability...")
            test_message = "Test post from AI Employee API test"

            post_url = f"{client.api_url}/{page_id}/feed"
            post_params = {
                "access_token": token,
                "message": test_message
            }

            print(f"   Message: {test_message}")
            print(f"   Attempting to post...")

            # Note: Uncomment below to actually post
            # post_response = client._make_request("POST", post_url, params=post_params)
            # if post_response.status_code == 200:
            #     print("✅ Post successful!")
            # else:
            #     print(f"❌ Post failed: {post_response.status_code}")
            #     print(f"Response: {post_response.text}")

            print("   (Skipped actual posting - uncomment code to test)")

        else:
            print(f"❌ Facebook API error: {response.status_code}")
            print(f"Response: {response.text}")
            print()

    except Exception as e:
        print(f"❌ Error testing Facebook API: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
