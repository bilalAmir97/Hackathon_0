#!/usr/bin/env python3
"""
AI-Powered WhatsApp Message Generator

The AI Employee generates the message based on your intent/context.
You just provide the recipient and purpose, AI writes the message.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import anthropic
import os

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def generate_message_with_ai(recipient_name: str, context: str, tone: str = "professional") -> str:
    """Generate message using Claude AI."""
    
    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not found in environment")
        print("   Using fallback message generation...")
        return f"Hi {recipient_name}, {context}"
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""Generate a WhatsApp message for the following:

Recipient: {recipient_name}
Purpose/Context: {context}
Tone: {tone}

Requirements:
- Keep it concise (2-4 sentences max)
- Natural and conversational
- Appropriate for WhatsApp
- {tone} tone
- No subject line or formal headers
- Direct and friendly

Generate ONLY the message text, nothing else."""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text.strip()
        
    except Exception as e:
        print(f"⚠️  AI generation failed: {e}")
        print("   Using fallback message generation...")
        return f"Hi {recipient_name}, {context}"


def create_ai_approval_request():
    """Create WhatsApp approval with AI-generated message."""
    print("=" * 70)
    print("  🤖 AI-Powered WhatsApp Message Generator")
    print("=" * 70)
    print()
    print("The AI Employee will write the message for you!")
    print("You just provide the recipient and what you want to say.")
    print()
    
    # Get recipient
    recipient_name = input("📱 Recipient's EXACT WhatsApp name: ").strip()
    if not recipient_name:
        print("❌ No recipient provided")
        return
    
    # Get context/purpose
    print()
    print("💬 What do you want to say? (describe the purpose)")
    print("   Examples:")
    print("   - Follow up on the invoice we discussed")
    print("   - Thank them for yesterday's meeting")
    print("   - Ask about project timeline")
    print("   - Remind about upcoming deadline")
    print()
    context = input("> ").strip()
    if not context:
        print("❌ No context provided")
        return
    
    # Get tone
    print()
    print("🎭 Message tone:")
    print("   1. Professional (default)")
    print("   2. Friendly")
    print("   3. Casual")
    print("   4. Formal")
    tone_choice = input("Select (1-4) or press Enter for professional: ").strip()
    
    tone_map = {
        "1": "professional",
        "2": "friendly", 
        "3": "casual",
        "4": "formal",
        "": "professional"
    }
    tone = tone_map.get(tone_choice, "professional")
    
    # Generate message with AI
    print()
    print("🤖 AI Employee is writing your message...")
    print()
    
    message = generate_message_with_ai(recipient_name, context, tone)
    
    # Show generated message
    print("=" * 70)
    print("  📝 AI-Generated Message")
    print("=" * 70)
    print()
    print(f"To: {recipient_name}")
    print(f"Message:")
    print()
    print(f'"{message}"')
    print()
    print("=" * 70)
    print()
    
    # Options
    print("Options:")
    print("  1. Approve and create approval request")
    print("  2. Regenerate with different tone")
    print("  3. Edit message manually")
    print("  4. Cancel")
    print()
    choice = input("Select (1-4): ").strip()
    
    if choice == "2":
        print()
        print("🔄 Regenerating...")
        message = generate_message_with_ai(recipient_name, context, tone)
        print()
        print(f'New message: "{message}"')
        print()
        choice = input("Approve this version? (yes/no): ").strip().lower()
        if choice != "yes":
            print("❌ Cancelled")
            return
    
    elif choice == "3":
        print()
        print("✏️  Edit the message:")
        message = input("> ").strip()
        if not message:
            print("❌ No message provided")
            return
    
    elif choice != "1":
        print("❌ Cancelled")
        return
    
    # Create approval request
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    contact_safe = recipient_name.replace(' ', '_').replace('/', '_')[:30]
    approval_id = f"whatsapp_reply_{contact_safe}_{timestamp}"
    
    expires_at = (datetime.now() + timedelta(hours=24)).isoformat() + 'Z'
    
    approval_content = f"""---
approval_id: {approval_id}
action_type: whatsapp_reply
created_at: {datetime.now().isoformat()}Z
expires_at: {expires_at}
status: pending
risk_assessment: low
action_params:
  chat_name: "{recipient_name}"
  message_text: "{message}"
reasoning: |
  AI-generated WhatsApp message based on user intent.
  Context: {context}
  Tone: {tone}
  Generated by AI Employee for human approval.
---

## WhatsApp Message - AI Generated

**To**: {recipient_name}
**Message**: "{message}"

### Generation Context
- **Purpose**: {context}
- **Tone**: {tone}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### To Approve and Send
Move this file to the `Approved/` folder:
```bash
mv AI_Employee_Vault/Pending_Approval/APPROVAL_{approval_id}.md AI_Employee_Vault/Approved/
```

The approval-executor will automatically send the message via WhatsApp Web.

### To Reject
Move this file to the `Rejected/` folder.

### Notes
- Message generated by AI Employee (Claude)
- Human approval required before sending
- Will be logged in audit trail
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
    print("2. To APPROVE and send:")
    print(f"   mv {approval_file} AI_Employee_Vault/Approved/")
    print()
    print("3. Watch execution:")
    print("   pm2 logs approval-executor --lines 50")
    print()
    print("4. Verify:")
    print(f"   - Check {recipient_name}'s WhatsApp")
    print("   - File moves to Done/")
    print("   - Audit log entry created")
    print()


if __name__ == '__main__':
    try:
        create_ai_approval_request()
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
