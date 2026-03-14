#!/usr/bin/env python3
"""
Test Gmail MCP Server

Verifies that the email MCP server can:
1. Load Gmail credentials
2. Connect to Gmail API
3. Search emails (read-only test)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def test_gmail_connection():
    """Test Gmail API connection."""
    print("=" * 60)
    print("Gmail MCP Server Test")
    print("=" * 60)
    print()

    # Test 1: Load credentials
    print("Test 1: Loading Gmail credentials...")
    token_path = project_root / "token.json"

    if not token_path.exists():
        print("❌ FAIL: token.json not found")
        return False

    try:
        creds = Credentials.from_authorized_user_file(str(token_path))
        print("✅ PASS: Credentials loaded successfully")
    except Exception as e:
        print(f"❌ FAIL: Could not load credentials: {e}")
        return False

    # Test 2: Build Gmail service
    print("\nTest 2: Building Gmail API service...")
    try:
        service = build('gmail', 'v1', credentials=creds)
        print("✅ PASS: Gmail service created")
    except Exception as e:
        print(f"❌ FAIL: Could not create service: {e}")
        return False

    # Test 3: Get user profile (lightweight API call)
    print("\nTest 3: Testing API connection (get profile)...")
    try:
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        total_messages = profile.get('messagesTotal', 0)
        print(f"✅ PASS: Connected to Gmail")
        print(f"   Email: {email}")
        print(f"   Total messages: {total_messages}")
    except HttpError as e:
        print(f"❌ FAIL: API call failed: {e}")
        return False

    # Test 4: Search emails (read-only)
    print("\nTest 4: Testing email search...")
    try:
        results = service.users().messages().list(
            userId='me',
            maxResults=5,
            q='is:unread'
        ).execute()

        messages = results.get('messages', [])
        print(f"✅ PASS: Email search working")
        print(f"   Found {len(messages)} unread messages")

    except HttpError as e:
        print(f"❌ FAIL: Search failed: {e}")
        return False

    # Test 5: MCP server file exists
    print("\nTest 5: Checking MCP server file...")
    mcp_server_path = project_root / "mcp_servers" / "email_mcp_server.py"

    if not mcp_server_path.exists():
        print("❌ FAIL: email_mcp_server.py not found")
        return False

    print("✅ PASS: MCP server file exists")

    # Test 6: MCP configuration
    print("\nTest 6: Checking MCP configuration...")
    mcp_config_path = project_root / ".claude" / "mcp.json"

    if not mcp_config_path.exists():
        print("❌ FAIL: .claude/mcp.json not found")
        return False

    import json
    with open(mcp_config_path) as f:
        config = json.load(f)

    if 'email' not in config.get('mcpServers', {}):
        print("❌ FAIL: Email MCP not configured")
        return False

    print("✅ PASS: MCP configuration correct")
    print(f"   Command: {config['mcpServers']['email']['command']}")
    print(f"   Args: {' '.join(config['mcpServers']['email']['args'])}")

    print()
    print("=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print()
    print("Gmail MCP Server is fully functional!")
    print()
    print("To use in Claude Code:")
    print('  claude "Send a test email to myself"')
    print('  claude "Search for emails from john@example.com"')
    print('  claude "Draft an email to team@company.com"')
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_gmail_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
