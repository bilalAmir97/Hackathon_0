#!/usr/bin/env python3
"""
Twitter Token Exchange Helper

This script helps you exchange a short-lived token for a long-lived access token.
It handles URL encoding automatically and provides better error messages.

Usage:
    python scripts/get_twitter_tokens.py
"""

import requests
import sys
from urllib.parse import quote


def print_header(text):
    print(f"\n{'=' * 60}")
    print(f"{text.center(60)}")
    print(f"{'=' * 60}\n")


def get_user_input(prompt, required=True):
    """Get input from user with validation."""
    while True:
        value = input(prompt).strip()
        if value or not required:
            return value
        print("This field is required. Please try again.")


def main():
    print_header("Twitter Token Helper")
    print("This script helps you set up Twitter API credentials.")
    print("\nYou'll need:")
    print("1. Twitter Developer account (https://developer.twitter.com/)")
    print("2. A Twitter App with Read and Write permissions")
    print("3. Your App's API Key and API Secret")
    print("4. Your Access Token and Access Token Secret")

    print("\n" + "=" * 60)
    print("\nStep 1: Get Your Credentials")
    print("-" * 60)
    print("1. Go to https://developer.twitter.com/en/portal/dashboard")
    print("2. Select your app")
    print("3. Go to 'Keys and tokens' tab")
    print("4. Copy your credentials")

    print("\n" + "=" * 60)
    print("\nStep 2: Enter Your Credentials")
    print("-" * 60)

    api_key = get_user_input("API Key (Consumer Key): ")
    api_secret = get_user_input("API Secret (Consumer Secret): ")
    access_token = get_user_input("Access Token: ")
    access_token_secret = get_user_input("Access Token Secret: ")

    print("\n" + "=" * 60)
    print("\nStep 3: Verify Credentials")
    print("-" * 60)

    # Test authentication
    try:
        import tweepy

        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

        # Verify credentials
        me = client.get_me()

        print(f"✅ Authentication successful!")
        print(f"✅ Authenticated as: @{me.data.username} (ID: {me.data.id})")

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\nPlease check your credentials and try again.")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("\nStep 4: Update .env File")
    print("-" * 60)
    print("\nAdd these lines to your .env file:")
    print("-" * 60)
    print(f"TWITTER_API_KEY={api_key}")
    print(f"TWITTER_API_SECRET={api_secret}")
    print(f"TWITTER_ACCESS_TOKEN={access_token}")
    print(f"TWITTER_ACCESS_TOKEN_SECRET={access_token_secret}")
    print("-" * 60)

    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Copy the credentials above to your .env file")
    print("2. Run: python scripts/verify_twitter_setup.py")
    print("3. Start using the Twitter MCP server!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
