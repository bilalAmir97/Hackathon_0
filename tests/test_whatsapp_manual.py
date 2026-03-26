#!/usr/bin/env python3
"""
Manual WhatsApp Test - Send to Real Contact

This script sends a test message to a real WhatsApp contact.
Use this to verify the complete end-to-end automation works.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_servers.whatsapp_mcp_server import WhatsAppClient


async def main():
    """Send test message to real contact."""
    print("=" * 70)
    print("  📱 WhatsApp Manual Test - Send to Real Contact")
    print("=" * 70)
    print()
    print("⚠️  This will send a REAL message to a WhatsApp contact!")
    print("   Make sure WhatsApp Web is logged in.")
    print()

    # Get contact name from user
    contact_name = input("Enter the EXACT contact name (as shown in WhatsApp): ").strip()
    if not contact_name:
        print("❌ No contact name provided")
        return

    # Get message
    message = input("Enter message to send: ").strip()
    if not message:
        message = "Test message from AI Employee automation system"

    # Confirm
    print()
    print(f"📤 Ready to send:")
    print(f"   To: {contact_name}")
    print(f"   Message: {message}")
    print()
    confirm = input("Send this message? (yes/no): ").strip().lower()

    if confirm != 'yes':
        print("❌ Cancelled")
        return

    print()
    print("🚀 Sending message...")

    # Create client and send
    client = WhatsAppClient()
    try:
        result = await client.send_message(contact_name, message)
        print()
        print("=" * 70)
        print("  ✅ SUCCESS!")
        print("=" * 70)
        print(f"   Message sent to: {result['chat_name']}")
        print(f"   Timestamp: {result['timestamp']}")
        print()
        print("🔍 Verify on your phone that the message was sent.")
        print()
    except Exception as e:
        print()
        print("=" * 70)
        print("  ❌ FAILED")
        print("=" * 70)
        print(f"   Error: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Make sure the contact name matches EXACTLY (case-sensitive)")
        print("   2. Check that WhatsApp Web is logged in")
        print("   3. Try opening WhatsApp Web manually first")
        print()
    finally:
        await client.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
