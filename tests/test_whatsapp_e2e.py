#!/usr/bin/env python3
"""
End-to-End WhatsApp Automation Test

Tests the complete workflow:
1. Create simulated WhatsApp message action file
2. Run processor to generate approval request
3. Simulate human approval
4. Run executor to send reply
5. Verify all steps completed successfully
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.whatsapp_processor import WhatsAppProcessor
from scripts.approval_executor import ApprovalExecutor


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def create_test_message(vault_path: Path, sender: str, message: str, priority: str = "high"):
    """Create a test WhatsApp message action file."""
    needs_action = vault_path / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"WHATSAPP_{sender.replace(' ', '_')}_{timestamp}.md"
    filepath = needs_action / filename

    content = f"""---
type: whatsapp_message
from: {sender}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
---

## WhatsApp Message

**From**: {sender}
**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Priority**: {priority}

### Message Content

{message}

### Suggested Actions

- [ ] Reply to {sender}
- [ ] Archive after processing

### Notes

Priority message detected by WhatsApp watcher.
"""

    filepath.write_text(content, encoding='utf-8')
    print(f"✅ Created test message: {filename}")
    return filepath


async def test_end_to_end(sender=None, message=None, non_interactive=False):
    """Run complete end-to-end test."""
    print_section("🧪 WhatsApp Automation - End-to-End Test")

    vault_path = Path("AI_Employee_Vault")

    # Step 1: Create test message
    print_section("Step 1: Create Test Message")
    print("\n📝 Creating simulated WhatsApp message...")

    if sender is None:
        if non_interactive:
            sender = "Test Contact"
        else:
            sender = input("Enter sender name (e.g., 'John Doe'): ").strip()
            if not sender:
                sender = "Test Contact"

    if message is None:
        if non_interactive:
            message = "Hi, I need urgent help with the invoice"
        else:
            message = input("Enter message with 'urgent' keyword: ").strip()
            if not message:
                message = "Hi, I need urgent help with the invoice"

    action_file = create_test_message(vault_path, sender, message, priority="high")
    print(f"   File: {action_file.name}")

    if not non_interactive:
        input("\n⏸️  Press Enter to continue to Step 2...")

    # Step 2: Process message
    print_section("Step 2: Process Message & Generate Approval")
    print("\n🔄 Running WhatsApp processor...")

    processor = WhatsAppProcessor(str(vault_path))
    result = processor.process_all()

    print(f"\n📊 Processing Results:")
    print(f"   Processed: {result['processed']}")
    print(f"   Successful: {result['successful']}")

    if result['successful'] == 0:
        print("\n❌ Processing failed!")
        return

    # Check for approval request
    pending_approval = vault_path / "Pending_Approval"
    approval_files = list(pending_approval.glob("APPROVAL_whatsapp_reply_*.md"))

    if not approval_files:
        print("\n❌ No approval request created!")
        print("   Check if auto_response_settings.enabled is true in config/whatsapp_rules.json")
        return

    approval_file = approval_files[0]
    print(f"\n✅ Approval request created: {approval_file.name}")

    # Show approval content
    print("\n📄 Approval Request Content:")
    print("-" * 70)
    content = approval_file.read_text()
    print(content[:500] + "..." if len(content) > 500 else content)
    print("-" * 70)

    if not non_interactive:
        input("\n⏸️  Press Enter to continue to Step 3...")

    # Step 3: Simulate approval
    print_section("Step 3: Simulate Human Approval")
    print("\n✅ Moving approval request to Approved/ folder...")

    approved = vault_path / "Approved"
    approved.mkdir(parents=True, exist_ok=True)

    approved_file = approved / approval_file.name
    approval_file.rename(approved_file)

    print(f"   Moved: {approved_file.name}")

    if not non_interactive:
        input("\n⏸️  Press Enter to continue to Step 4...")

    # Step 4: Execute approved reply
    print_section("Step 4: Execute Approved Reply")
    print("\n🚀 Running approval executor...")
    print("   This will send the WhatsApp message via Playwright")
    print("   Make sure WhatsApp Web is logged in!")

    if not non_interactive:
        confirm = input("\n⚠️  Ready to send message? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("\n❌ Test cancelled")
            return
    else:
        print("\n⚠️  Non-interactive mode: Auto-confirming message send...")

    # Import and run executor
    executor = ApprovalExecutor(str(vault_path))

    # Manually trigger the approved file handler
    print(f"\n📤 Executing: {approved_file.name}")
    executor.on_file_moved_to_approved(str(approved_file))

    # Check if file moved to Done
    done = vault_path / "Done"
    done_files = list(done.glob(approved_file.name))

    if done_files:
        print(f"\n✅ File moved to Done: {done_files[0].name}")
    else:
        print(f"\n⚠️  File not in Done folder (check for errors)")

    # Step 5: Verify
    print_section("Step 5: Verification")
    print("\n🔍 Checking results...")

    # Check audit log
    logs_dir = vault_path / "Logs"
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{today}.json"

    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
            whatsapp_logs = [log for log in logs if 'whatsapp' in log.get('action_type', '').lower()]
            print(f"\n✅ Found {len(whatsapp_logs)} WhatsApp-related log entries")

            if whatsapp_logs:
                latest = whatsapp_logs[-1]
                print(f"\n📋 Latest Log Entry:")
                print(f"   Action: {latest.get('action_type')}")
                print(f"   Status: {latest.get('result', latest.get('status'))}")
                print(f"   Time: {latest.get('timestamp')}")
        except Exception as e:
            print(f"\n⚠️  Could not read logs: {e}")

    # Final summary
    print_section("✅ End-to-End Test Complete")
    print("\n📊 Summary:")
    print("   1. ✅ Test message created")
    print("   2. ✅ Processor generated approval request")
    print("   3. ✅ Approval simulated (moved to Approved/)")
    print("   4. ✅ Executor attempted to send message")
    print("   5. ✅ Verification completed")

    print("\n🔍 Manual Verification:")
    print("   1. Check WhatsApp on your phone")
    print("   2. Verify message was sent to the contact")
    print("   3. Check AI_Employee_Vault/Done/ for completed approval")
    print("   4. Check AI_Employee_Vault/Logs/ for audit trail")

    print("\n" + "=" * 70)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='WhatsApp End-to-End Test')
    parser.add_argument('--sender', help='Sender name for test message', default=None)
    parser.add_argument('--message', help='Message text with urgent keyword', default=None)
    parser.add_argument('--non-interactive', action='store_true',
                        help='Run in non-interactive mode (no prompts)')

    args = parser.parse_args()

    try:
        asyncio.run(test_end_to_end(
            sender=args.sender,
            message=args.message,
            non_interactive=args.non_interactive
        ))
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
