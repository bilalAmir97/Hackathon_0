#!/usr/bin/env python3
"""
LinkedIn Cookie Import Helper

Helps you import LinkedIn session cookies from your browser.
"""

import json
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 60)
    print("LinkedIn Cookie Import Helper")
    print("=" * 60)
    print()
    print("This script will help you import your LinkedIn session cookie.")
    print()
    print("Steps:")
    print("1. Open LinkedIn in your browser (Chrome/Firefox)")
    print("2. Log in if not already logged in")
    print("3. Press F12 to open Developer Tools")
    print("4. Go to Application/Storage tab")
    print("5. Click Cookies → https://www.linkedin.com")
    print("6. Find the cookie named 'li_at'")
    print("7. Copy its value (long string)")
    print()
    print("=" * 60)
    print()

    # Get cookie value
    cookie_value = input("Paste the li_at cookie value here: ").strip()

    if not cookie_value:
        print("❌ No cookie value provided. Exiting.")
        return

    if len(cookie_value) < 20:
        print("⚠️  Warning: Cookie value seems too short. Make sure you copied the full value.")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return

    # Create session file
    vault_path = Path("AI_Employee_Vault")
    state_folder = vault_path / ".state"
    state_folder.mkdir(exist_ok=True)

    session_file = state_folder / "linkedin_session.json"

    session_data = {
        "cookies": [
            {
                "name": "li_at",
                "value": cookie_value,
                "domain": ".linkedin.com",
                "path": "/",
                "expires": 1767225600,  # ~1 year from now
                "httpOnly": True,
                "secure": True,
                "sameSite": "None"
            },
            {
                "name": "JSESSIONID",
                "value": f"ajax:{cookie_value[:16]}",
                "domain": ".www.linkedin.com",
                "path": "/",
                "expires": 1767225600,
                "httpOnly": False,
                "secure": True,
                "sameSite": "None"
            }
        ],
        "saved_at": datetime.now().isoformat(),
        "imported_manually": True
    }

    # Save session file
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)

    print()
    print("=" * 60)
    print("✅ Session saved successfully!")
    print("=" * 60)
    print()
    print(f"Session file: {session_file}")
    print()
    print("Next steps:")
    print("1. Test the session:")
    print("   uv run python watchers/linkedin_poster.py")
    print()
    print("2. If it works, create a test post:")
    print("   mv AI_Employee_Vault/Pending_LinkedIn/EXAMPLE_post_ai_employee.md \\")
    print("      AI_Employee_Vault/Approved_LinkedIn/")
    print("   uv run python watchers/linkedin_poster.py")
    print()
    print("3. Start PM2 service for automatic posting:")
    print("   pm2 start ecosystem.config.json --only linkedin-poster")
    print()
    print("=" * 60)
    print()
    print("Note: This session will expire in ~30 days.")
    print("You'll need to re-import the cookie when it expires.")
    print()

if __name__ == "__main__":
    main()
