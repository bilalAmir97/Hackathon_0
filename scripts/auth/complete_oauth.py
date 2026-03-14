#!/usr/bin/env python3
"""
Complete Gmail OAuth with authorization code
Usage: python complete_oauth.py <authorization_code>
"""

import sys
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose'  # Includes send + draft management
]

def complete_oauth(auth_code: str):
    """Complete OAuth flow with authorization code"""
    print("\n" + "="*60)
    print("🔐 Completing Gmail OAuth")
    print("="*60)

    credentials_path = Path('credentials.json')
    token_path = Path('token.json')

    if not credentials_path.exists():
        print("❌ credentials.json not found!")
        return False

    try:
        # Create flow with manual redirect URI
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path),
            SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )

        # Exchange code for credentials
        print("🔄 Exchanging authorization code for credentials...")
        flow.fetch_token(code=auth_code)
        creds = flow.credentials

        # Save credentials
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"✅ Saved credentials to token.json")

        # Test API access
        print("\n🧪 Testing Gmail API access...")
        service = build('gmail', 'v1', credentials=creds)

        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        total_messages = profile.get('messagesTotal', 0)

        print(f"✅ Successfully connected to Gmail API")
        print(f"📧 Email: {email}")
        print(f"📊 Total messages: {total_messages}")

        # Test reading recent messages
        print("\n📬 Testing message access (fetching 3 recent)...")
        results = service.users().messages().list(
            userId='me',
            maxResults=3
        ).execute()

        messages = results.get('messages', [])
        print(f"✅ Successfully retrieved {len(messages)} messages")

        if messages:
            print("\n📋 Recent messages:")
            for i, msg in enumerate(messages, 1):
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject']
                ).execute()

                headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
                print(f"   {i}. From: {headers.get('From', 'Unknown')[:50]}")
                print(f"      Subject: {headers.get('Subject', 'No subject')[:50]}")

        print("\n" + "="*60)
        print("🎉 Gmail OAuth Setup: SUCCESS")
        print("="*60)
        print("\n✅ token.json created and verified")
        print("✅ Gmail API access working")
        print("✅ Ready for Gmail Watcher implementation")

        return True

    except Exception as e:
        print(f"\n❌ OAuth completion failed: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python complete_oauth.py <authorization_code>")
        sys.exit(1)

    auth_code = sys.argv[1].strip()
    success = complete_oauth(auth_code)
    sys.exit(0 if success else 1)
