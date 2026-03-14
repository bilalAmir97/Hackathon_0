#!/usr/bin/env python3
"""
WhatsApp Action File Creator - Interactive Helper

Makes it easy to create action files manually without worrying about formatting.
Just answer the prompts and the file is created automatically.
"""

from datetime import datetime
from pathlib import Path
import re

def sanitize_filename(name):
    """Convert name to filesystem-safe string."""
    # Remove special characters
    safe = re.sub(r'[^\w\s-]', '', name)
    # Replace spaces with underscores
    safe = safe.replace(' ', '_')
    # Remove multiple underscores
    safe = re.sub(r'_+', '_', safe)
    # Lowercase
    safe = safe.lower().strip('_')
    return safe if safe else "unknown"

def create_whatsapp_action_file():
    """Interactive prompt to create WhatsApp action file."""

    print("=" * 60)
    print("📱 WhatsApp Action File Creator")
    print("=" * 60)
    print("\nThis will help you create an action file for a priority WhatsApp message.")
    print("Just answer the questions below.\n")

    # Get information from user
    print("1. Who sent the message?")
    sender = input("   Sender name or phone number: ").strip()
    if not sender:
        print("❌ Sender is required!")
        return

    print("\n2. What is the message content?")
    print("   (Paste the full message, press Enter twice when done)")
    message_lines = []
    while True:
        line = input()
        if line == "" and message_lines and message_lines[-1] == "":
            message_lines.pop()  # Remove last empty line
            break
        message_lines.append(line)
    message = "\n".join(message_lines).strip()

    if not message:
        print("❌ Message content is required!")
        return

    print("\n3. Any context or background? (optional)")
    context = input("   Context: ").strip()
    if not context:
        context = "Priority WhatsApp message requiring attention."

    print("\n4. What action is required?")
    action = input("   Action: ").strip()
    if not action:
        action = "Review and respond to this message."

    # Generate timestamp
    now = datetime.now()
    iso_timestamp = now.strftime('%Y-%m-%dT%H:%M:%SZ')
    readable_timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    date_str = now.strftime('%Y%m%d_%H%M%S')

    # Create filename
    safe_sender = sanitize_filename(sender)
    filename = f"WHATSAPP_{date_str}_{safe_sender}.md"

    # Create file path
    vault_path = Path("AI_Employee_Vault")
    needs_action = vault_path / "Needs_Action"
    needs_action.mkdir(parents=True, exist_ok=True)

    filepath = needs_action / filename

    # Create content
    content = f"""---
type: whatsapp_message
from: {sender}
received: {iso_timestamp}
priority: high
status: pending
---

## WhatsApp Message from {sender}

**Received:** {readable_timestamp}

**Message:**
{message}

**Context:**
{context}

**Action Required:**
{action}
"""

    # Write file
    filepath.write_text(content, encoding='utf-8')

    print("\n" + "=" * 60)
    print("✅ Action file created successfully!")
    print("=" * 60)
    print(f"\nFile: {filepath}")
    print(f"Location: {filepath.absolute()}")
    print("\nThe approval executor will pick this up automatically.")
    print("\nFile preview:")
    print("-" * 60)
    print(content)
    print("-" * 60)

if __name__ == "__main__":
    try:
        create_whatsapp_action_file()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
