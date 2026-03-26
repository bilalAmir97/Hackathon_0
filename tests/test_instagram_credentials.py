#!/usr/bin/env python3
"""
Test Instagram API credentials and token validity
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
    print("  🔍 Instagram API Credentials Test")
    print("=" * 70)
    print()

    # Get credentials from .env
    token = os.getenv("INSTAGRAM_BUSINESS_ACCESS_TOKEN")
    account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

    print(f"Account ID: {account_id}")
    print(f"Token: {token[:20]}...{token[-10:] if token else 'NOT SET'}")
    print()

    if not token or not account_id:
        print("❌ Instagram credentials not configured in .env")
        return

    # Create Meta client
    print("📡 Testing Instagram API connection...")
    try:
        client = MetaGraphClient()

        # Test API call - get account info
        url = f"{client.api_url}/{account_id}"
        params = {
            "access_token": token,
            "fields": "id,username,name,profile_picture_url"
        }

        response = client._make_request("GET", url, params=params)

        if response.status_code == 200:
            data = response.json()
            print("✅ Instagram API connection successful!")
            print()
            print(f"Account Info:")
            print(f"  ID: {data.get('id')}")
            print(f"  Username: {data.get('username')}")
            print(f"  Name: {data.get('name')}")
            print()
        else:
            print(f"❌ Instagram API error: {response.status_code}")
            print(f"Response: {response.text}")
            print()

    except Exception as e:
        print(f"❌ Error testing Instagram API: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
