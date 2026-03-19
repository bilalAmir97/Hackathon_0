#!/usr/bin/env python3
"""
Facebook Token Exchange Helper

This script helps you exchange a short-lived token for a long-lived page token.
It handles URL encoding automatically and provides better error messages.

Usage:
    python scripts/get_facebook_tokens.py
"""

import requests
import sys
from urllib.parse import quote

def print_header(text):
    print(f"\n{'=' * 60}")
    print(f"{text.center(60)}")
    print(f"{'=' * 60}\n")

def exchange_token(app_id, app_secret, short_token):
    """Exchange short-lived token for long-lived token"""
    print_header("Step 1: Exchange for Long-Lived User Token")

    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_token
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            long_lived_token = data.get("access_token")
            expires_in = data.get("expires_in", 0)

            print(f"✓ Success! Long-lived user token obtained")
            print(f"  Expires in: {expires_in // 86400} days")
            print(f"  Token: {long_lived_token[:20]}...{long_lived_token[-20:]}")

            return long_lived_token
        else:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            error_code = error_data.get("error", {}).get("code", "N/A")

            print(f"✗ Error {error_code}: {error_msg}")

            # Provide specific guidance based on error
            if "Invalid OAuth access token" in error_msg:
                print("\n  Possible causes:")
                print("  - Short-lived token has expired (they last 1-2 hours)")
                print("  - Token was copied incorrectly")
                print("\n  Solution: Generate a new token from Step 2")
            elif "Invalid App Secret" in error_msg or error_code == 2:
                print("\n  Possible causes:")
                print("  - App Secret is incorrect")
                print("  - You didn't click 'Show' button to reveal the secret")
                print("\n  Solution: Go to App Settings → Basic → Show App Secret")

            return None

    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {str(e)}")
        return None

def get_page_token(long_lived_token):
    """Get page access token from long-lived user token"""
    print_header("Step 2: Get Page Access Token")

    url = "https://graph.facebook.com/v19.0/me/accounts"
    params = {
        "access_token": long_lived_token
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            pages = data.get("data", [])

            if not pages:
                print("✗ No pages found. Make sure you manage at least one Facebook Page.")
                return None

            print(f"✓ Found {len(pages)} page(s):\n")

            for i, page in enumerate(pages, 1):
                print(f"  {i}. {page.get('name', 'Unnamed Page')}")
                print(f"     Page ID: {page.get('id')}")
                print(f"     Category: {page.get('category', 'N/A')}")
                print(f"     Token: {page.get('access_token', '')[:20]}...")
                print()

            # Return first page's info
            first_page = pages[0]
            return {
                "page_id": first_page.get("id"),
                "page_token": first_page.get("access_token"),
                "page_name": first_page.get("name")
            }
        else:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            print(f"✗ Error: {error_msg}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {str(e)}")
        return None

def get_instagram_account(page_id, page_token):
    """Get Instagram Business Account ID"""
    print_header("Step 3: Get Instagram Business Account")

    url = f"https://graph.facebook.com/v19.0/{page_id}"
    params = {
        "fields": "instagram_business_account",
        "access_token": page_token
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            ig_account = data.get("instagram_business_account")

            if not ig_account:
                print("✗ No Instagram Business Account linked to this page")
                print("\n  Solution:")
                print("  1. Open Instagram app")
                print("  2. Settings → Account → Switch to Professional Account")
                print("  3. Settings → Account → Linked Accounts → Facebook")
                print("  4. Link to your Facebook Page")
                return None

            ig_account_id = ig_account.get("id")
            print(f"✓ Instagram Business Account found")
            print(f"  Account ID: {ig_account_id}")

            return ig_account_id
        else:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            print(f"✗ Error: {error_msg}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"✗ Network error: {str(e)}")
        return None

def main():
    print_header("Facebook & Instagram Token Generator")

    print("This script will help you get all required tokens.\n")

    # Get inputs
    print("Enter your credentials (from App Settings → Basic):\n")
    app_id = input("App ID: ").strip()
    app_secret = input("App Secret (click 'Show' to reveal): ").strip()
    print("\nEnter your short-lived token (from Step 2 OAuth URL):\n")
    short_token = input("Short-lived token: ").strip()

    if not all([app_id, app_secret, short_token]):
        print("\n✗ Error: All fields are required")
        sys.exit(1)

    # Step 1: Exchange for long-lived token
    long_lived_token = exchange_token(app_id, app_secret, short_token)
    if not long_lived_token:
        sys.exit(1)

    # Step 2: Get page token
    page_info = get_page_token(long_lived_token)
    if not page_info:
        sys.exit(1)

    # Step 3: Get Instagram account
    ig_account_id = get_instagram_account(page_info["page_id"], page_info["page_token"])

    # Print final summary
    print_header("✓ Setup Complete!")

    print("Add these to your .env file:\n")
    print(f"FACEBOOK_PAGE_ACCESS_TOKEN={page_info['page_token']}")
    print(f"FACEBOOK_PAGE_ID={page_info['page_id']}")
    print(f"INSTAGRAM_BUSINESS_ACCESS_TOKEN={page_info['page_token']}")

    if ig_account_id:
        print(f"INSTAGRAM_BUSINESS_ACCOUNT_ID={ig_account_id}")
    else:
        print("# INSTAGRAM_BUSINESS_ACCOUNT_ID=<link Instagram account first>")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
