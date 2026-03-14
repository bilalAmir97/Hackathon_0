#!/usr/bin/env python3
"""
Generate Gmail OAuth authorization URL
"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose'  # Includes send + draft management
]

credentials_path = Path('credentials.json')

if not credentials_path.exists():
    print("❌ credentials.json not found!")
    exit(1)

flow = InstalledAppFlow.from_client_secrets_file(
    str(credentials_path),
    SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)

auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

print("\n" + "="*70)
print("🔐 Gmail OAuth Setup - Step 1: Get Authorization Code")
print("="*70)
print("\n📋 Instructions:")
print("   1. Copy the URL below")
print("   2. Open it in your Windows browser")
print("   3. Select your Google account")
print("   4. Click 'Allow' to grant permissions")
print("   5. Google will show you an authorization code")
print("   6. Copy that code")
print("\n🔗 Authorization URL:")
print("-"*70)
print(auth_url)
print("-"*70)
print("\n⏭️  After you get the code, run:")
print("   source .venv/bin/activate && python complete_oauth.py YOUR_CODE_HERE")
print("="*70)
