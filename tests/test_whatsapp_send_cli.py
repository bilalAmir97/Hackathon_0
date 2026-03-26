#!/usr/bin/env python3
"""
Quick CLI test for WhatsApp sender - no interactive prompts
Usage: uv run python tests/test_whatsapp_send_cli.py "CONTACT_NAME" "message text"
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_servers.whatsapp_mcp_server import WhatsAppClient


async def main():
    if len(sys.argv) < 3:
        print("Usage: uv run python tests/test_whatsapp_send_cli.py 'CONTACT_NAME' 'message text'")
        print("Example: uv run python tests/test_whatsapp_send_cli.py 'LAIBA GIAIC' 'Test message'")
        sys.exit(1)

    contact_name = sys.argv[1]
    message_text = sys.argv[2]

    print("=" * 70)
    print("  📱 WhatsApp Send Test")
    print("=" * 70)
    print(f"  To: {contact_name}")
    print(f"  Message: {message_text}")
    print("=" * 70)
    print()

    client = WhatsAppClient()
    try:
        result = await client.send_message(contact_name, message_text)
        print()
        print("=" * 70)
        print("  ✅ SUCCESS!")
        print("=" * 70)
        print(f"  Timestamp: {result['timestamp']}")
        print()
        print("🔍 Please verify on your phone that the message was sent.")
        print()
    except Exception as e:
        print()
        print("=" * 70)
        print("  ❌ FAILED")
        print("=" * 70)
        print(f"  Error: {e}")
        print()
        sys.exit(1)
    finally:
        await client.close()


if __name__ == '__main__':
    asyncio.run(main())
