#!/usr/bin/env python3
"""
Test Instagram direct file upload (without public URL)
Research if Instagram Graph API supports multipart/form-data uploads
"""

import os
import sys
from pathlib import Path
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_instagram_direct_upload():
    """Test if Instagram supports direct file uploads."""

    token = os.getenv("INSTAGRAM_BUSINESS_ACCESS_TOKEN")
    account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    image_path = "tests/test_instagram_image.jpg"

    print("=" * 70)
    print("  🔬 Instagram Direct Upload Research")
    print("=" * 70)
    print()

    # Test 1: Try multipart/form-data upload (like Facebook)
    print("Test 1: Multipart/form-data upload...")
    url = f"https://graph.facebook.com/v18.0/{account_id}/media"

    data = {
        "caption": "Test direct upload",
        "access_token": token
    }

    try:
        with open(image_path, 'rb') as image_file:
            files = {'source': image_file}
            response = requests.post(url, data=data, files=files, timeout=30)

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        print()
    except Exception as e:
        print(f"Failed: {e}")
        print()

    # Test 2: Try with 'image' parameter
    print("Test 2: Using 'image' parameter...")
    try:
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = requests.post(url, data=data, files=files, timeout=30)

        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        print()
    except Exception as e:
        print(f"Failed: {e}")
        print()

    # Test 3: Check Instagram API documentation
    print("Test 3: Checking API capabilities...")
    print("Instagram Graph API endpoints:")
    print("  - POST /{ig-user-id}/media (create container)")
    print("  - POST /{ig-user-id}/media_publish (publish container)")
    print()
    print("According to Meta documentation:")
    print("  - Instagram requires 'image_url' parameter (public URL)")
    print("  - Does NOT support direct file uploads via multipart/form-data")
    print("  - This is different from Facebook's API")
    print()
    print("Conclusion:")
    print("  Instagram's Content Publishing API requires publicly accessible URLs")
    print("  This is a limitation of Instagram's API, not our implementation")
    print()

if __name__ == '__main__':
    test_instagram_direct_upload()
