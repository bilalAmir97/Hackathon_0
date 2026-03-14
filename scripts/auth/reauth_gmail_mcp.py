#!/usr/bin/env python3
"""
Re-authenticate Gmail with expanded scopes for MCP server.

This script updates the OAuth token to include compose/send permissions
needed by the Email MCP server.
"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

# Expanded scopes for MCP server
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read emails
    'https://www.googleapis.com/auth/gmail.compose'    # Send + draft emails
]

def main():
    credentials_path = Path('credentials.json')
    token_path = Path('token.json')

    if not credentials_path.exists():
        print("❌ credentials.json not found!")
        print("   Make sure you have downloaded OAuth credentials from Google Cloud Console")
        exit(1)

    # Backup existing token if it exists
    if token_path.exists():
        backup_path = token_path.with_suffix('.json.backup')
        try:
            token_path.rename(backup_path)
            print(f"✓ Backed up existing token to {backup_path}")
        except Exception as e:
            print(f"⚠️ Could not backup token: {e}")
    else:
        print("ℹ️ No existing token found (first-time authentication)")

    print("\n" + "="*70)
    print("🔐 Gmail OAuth Re-authentication for MCP Server")
    print("="*70)
    print("\n📋 New Scopes:")
    print("   - gmail.readonly (read emails)")
    print("   - gmail.compose (send + draft emails)")
    print("\n⚠️  You will need to re-authorize the application")
    print("="*70)

    # Create flow
    flow = InstalledAppFlow.from_client_secrets_file(
        str(credentials_path),
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )

    # Get authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

    print("\n🔗 Authorization URL:")
    print("-"*70)
    print(auth_url)
    print("-"*70)
    print("\n📋 Instructions:")
    print("   1. Copy the URL above")
    print("   2. Open it in your browser")
    print("   3. Select your Google account")
    print("   4. Click 'Allow' to grant permissions")
    print("   5. Copy the authorization code shown")
    print("\n✏️  Enter the authorization code: ", end='')

    # Get code from user
    code = input().strip()

    if not code:
        print("❌ No code provided")
        exit(1)

    try:
        # Exchange code for token
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Save token
        token_path.write_text(creds.to_json())

        print("\n" + "="*70)
        print("✅ Authentication successful!")
        print("="*70)
        print(f"✓ Token saved to {token_path}")
        print("\n📋 Next steps:")
        print("   1. Test the MCP server: uv run python test_email_mcp.py")
        print("   2. Verify drafts can be created in Gmail")
        print("   3. Update approval_executor.py to use MCP server")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        # Restore backup if it exists
        backup_path = token_path.with_suffix('.json.backup')
        if backup_path.exists():
            backup_path.rename(token_path)
            print(f"✓ Restored backup token")
        exit(1)


if __name__ == "__main__":
    main()
