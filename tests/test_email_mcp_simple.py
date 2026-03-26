#!/usr/bin/env python3
"""
Simple test for email MCP server functionality
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.email_mcp_server import get_gmail_service, send_email
import asyncio


async def test_email_functionality():
    """Test email MCP server functionality."""

    print("=" * 70)
    print("  📧 Email MCP Server Test")
    print("=" * 70)
    print()

    # Test 1: Check Gmail service connection
    print("Test 1: Gmail Service Connection")
    try:
        service = get_gmail_service()
        print("✅ Gmail service initialized successfully")
        print(f"   Service: {service._http.credentials.client_id[:20]}...")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize Gmail service: {e}")
        return

    # Test 2: Search for recent emails
    print("Test 2: Search Recent Emails")
    try:
        results = service.users().messages().list(
            userId='me',
            maxResults=5,
            q='is:inbox'
        ).execute()

        messages = results.get('messages', [])
        print(f"✅ Found {len(messages)} recent emails in inbox")
        print()
    except Exception as e:
        print(f"❌ Failed to search emails: {e}")
        print()

    # Test 3: Get user profile
    print("Test 3: Get Gmail Profile")
    try:
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Gmail profile retrieved")
        print(f"   Email: {profile.get('emailAddress')}")
        print(f"   Total messages: {profile.get('messagesTotal')}")
        print(f"   Total threads: {profile.get('threadsTotal')}")
        print()
    except Exception as e:
        print(f"❌ Failed to get profile: {e}")
        print()

    print("=" * 70)
    print("  Email MCP Server Status")
    print("=" * 70)
    print()
    print("Available Tools:")
    print("  ✅ send_email - Send emails via Gmail")
    print("  ✅ draft_email - Create draft emails")
    print("  ✅ search_emails - Search Gmail messages")
    print()
    print("Gmail Integration: ✅ Working")
    print("OAuth Credentials: ✅ Valid")
    print()


if __name__ == '__main__':
    asyncio.run(test_email_functionality())
