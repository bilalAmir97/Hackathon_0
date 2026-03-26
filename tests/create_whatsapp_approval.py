#!/usr/bin/env python3
"""
Create Manual WhatsApp Approval Request

This creates a properly formatted approval request that you can move to
Approved/ folder to test the approval executor and message sending.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def create_approval_request():
    """Create a WhatsApp approval request file."""
    print("=" * 70)
    print("  📋 Create WhatsApp Approval Request")
    print("=" * 70)
    print()
    print("This will create an approval request file that you can approve")
    print("to test the complete workflow.")
    print()
    
    # Get contact name
    contact_name = input("Enter recipient's EXACT WhatsApp name: ").strip()
    if not contact_name:
        print("❌ No contact name provided")
        return
    
    # Get message
    print()
    print("Enter message to send (or press Enter for default):")
    message = input("> ").strip()
    if not message:
        message = "Hi! This is a test message from my AI Employee automation system. Testing the approval workflow. 🤖"
    
    # Confirm
    print()
    print("=" * 70)
    print("  📝 Approval Request Preview")
    print("=" * 70)
    print(f"To: {contact_name}")
    print(f"Message: {message}")
    print()
    confirm = input("Create this approval request? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Cancelled")
        return
    
    # Generate approval file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    contact_safe = contact_name.replace(' ', '_').replace('/', '_')[:30]
    approval_id = f"whatsapp_reply_{contact_safe}_{timestamp}"
    
    # Calculate expiration (24 hours)
    expires_at = (datetime.now() + timedelta(hours=24)).isoformat() + 'Z'
    
    # Create approval content
    approval_content = f"""---
approval_id: {approval_id}
action_type: whatsapp_reply
created_at: {datetime.now().isoformat()}Z
expires_at: {expires_at}
status: pending
risk_assessment: low
action_params:
  chat_name: "{contact_name}"
  message_text: "{message}"
reasoning: |
  Manual test of WhatsApp approval workflow.
  Testing approval executor and message sending functionality.
---

## WhatsApp Reply Approval Request (Manual Test)

**To**: {contact_name}
**Message**: "{message}"

### Test Purpose
This is a manual test to verify:
1. Approval executor detects file movement
2. WhatsApp MCP server sends message correctly
3. Audit logging captures the action
4. Message appears in recipient's WhatsApp

### To Approve and Send
Move this file to the `Approved/` folder:
```bash
mv AI_Employee_Vault/Pending_Approval/APPROVAL_{approval_id}.md AI_Employee_Vault/Approved/
```

The approval-executor will automatically:
1. Detect the file movement
2. Execute the WhatsApp send action
3. Log the result in audit trail
4. Move the file to Done/

### To Reject
Move this file to the `Rejected/` folder instead.

### Notes
- Message will be sent via Playwright automation to WhatsApp Web
- Session must be active (logged in)
- Message will be logged in audit trail
- Check PM2 logs: `pm2 logs approval-executor`
"""
    
    # Save to Pending_Approval
    vault_path = Path("AI_Employee_Vault")
    pending_approval = vault_path / "Pending_Approval"
    pending_approval.mkdir(parents=True, exist_ok=True)
    
    approval_file = pending_approval / f"APPROVAL_{approval_id}.md"
    approval_file.write_text(approval_content, encoding='utf-8')
    
    print()
    print("=" * 70)
    print("  ✅ Approval Request Created!")
    print("=" * 70)
    print(f"File: {approval_file}")
    print()
    print("📋 Next Steps:")
    print()
    print("1. Review the approval file:")
    print(f"   cat {approval_file}")
    print()
    print("2. To APPROVE and send the message:")
    print(f"   mv {approval_file} AI_Employee_Vault/Approved/")
    print()
    print("3. Watch the approval executor logs:")
    print("   pm2 logs approval-executor --lines 50")
    print()
    print("4. Check the result:")
    print("   - Message should appear in recipient's WhatsApp")
    print("   - File will move to Done/ folder")
    print("   - Audit log entry created")
    print()
    print("⚠️  Make sure WhatsApp Web is logged in before approving!")
    print()


if __name__ == '__main__':
    try:
        create_approval_request()
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
