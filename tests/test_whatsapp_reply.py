#!/usr/bin/env python3
"""
Test WhatsApp Reply Functionality

Tests the complete WhatsApp automation workflow:
1. Detect message (simulated)
2. Generate approval request
3. Approve request
4. Send reply via Playwright
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_servers.whatsapp_mcp_server import WhatsAppClient


async def test_send_message():
    """Test sending a WhatsApp message."""
    print("=" * 70)
    print("🧪 Testing WhatsApp Reply Functionality")
    print("=" * 70)

    # Get test parameters
    chat_name = input("\n📱 Enter chat name to send test message to: ").strip()
    if not chat_name:
        print("❌ Chat name is required")
        return

    message_text = input("📝 Enter test message: ").strip()
    if not message_text:
        message_text = "This is a test message from the AI Employee WhatsApp automation system."

    print(f"\n🚀 Sending message to: {chat_name}")
    print(f"📄 Message: {message_text}")
    print("\n⏳ Launching browser and sending message...")

    # Create client and send message
    client = WhatsAppClient()
    try:
        result = await client.send_message(chat_name, message_text)

        if result.get('status') == 'success':
            print("\n✅ SUCCESS! Message sent successfully!")
            print(f"   Chat: {result.get('chat_name')}")
            print(f"   Timestamp: {result.get('timestamp')}")
            print("\n📋 Result:")
            print(f"   {result}")
        else:
            print(f"\n❌ FAILED: {result.get('error')}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()
        print("\n🔒 Browser closed")


async def test_approval_workflow():
    """Test the complete approval workflow."""
    print("\n" + "=" * 70)
    print("🧪 Testing Complete Approval Workflow")
    print("=" * 70)

    vault_path = Path("AI_Employee_Vault")
    pending_approval = vault_path / "Pending_Approval"
    approved = vault_path / "Approved"

    # Check for pending approval files
    approval_files = list(pending_approval.glob("APPROVAL_whatsapp_reply_*.md"))

    if not approval_files:
        print("\n📭 No WhatsApp approval requests found in Pending_Approval/")
        print("   Run the WhatsApp watcher and processor first to generate approval requests.")
        return

    print(f"\n📋 Found {len(approval_files)} approval request(s):")
    for i, file in enumerate(approval_files, 1):
        print(f"   {i}. {file.name}")

    # Select file to test
    if len(approval_files) == 1:
        selected_file = approval_files[0]
    else:
        choice = input(f"\nSelect file to test (1-{len(approval_files)}): ").strip()
        try:
            selected_file = approval_files[int(choice) - 1]
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return

    print(f"\n📄 Selected: {selected_file.name}")

    # Read and display approval request
    content = selected_file.read_text()
    print("\n" + "-" * 70)
    print(content)
    print("-" * 70)

    # Ask for approval
    approve = input("\n✅ Approve and send this message? (yes/no): ").strip().lower()

    if approve == 'yes':
        # Move to Approved folder
        approved.mkdir(parents=True, exist_ok=True)
        approved_file = approved / selected_file.name
        selected_file.rename(approved_file)

        print(f"\n✅ Moved to Approved: {approved_file.name}")
        print("   The approval executor will process this and send the message.")
        print("\n💡 To execute immediately, run:")
        print("   python scripts/approval_executor.py")
    else:
        print("\n❌ Approval cancelled")


def main():
    """Main test menu."""
    print("\n" + "=" * 70)
    print("📱 WhatsApp Reply Automation - Test Suite")
    print("=" * 70)
    print("\nSelect test:")
    print("1. Test direct message sending (requires active WhatsApp session)")
    print("2. Test approval workflow (requires pending approval requests)")
    print("3. Exit")

    choice = input("\nEnter choice (1-3): ").strip()

    if choice == '1':
        asyncio.run(test_send_message())
    elif choice == '2':
        asyncio.run(test_approval_workflow())
    elif choice == '3':
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")


if __name__ == '__main__':
    main()
