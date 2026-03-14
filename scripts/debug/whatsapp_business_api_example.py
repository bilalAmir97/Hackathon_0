"""
WhatsApp Business API Integration Example (using Twilio)

This replaces the Playwright browser automation with API calls.
"""

from twilio.rest import Client
import os
from datetime import datetime
from pathlib import Path

class WhatsAppBusinessWatcher:
    def __init__(self, vault_path='AI_Employee_Vault'):
        # Twilio credentials (get from twilio.com/console)
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')  # e.g., 'whatsapp:+14155238886'

        self.client = Client(self.account_sid, self.auth_token)
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'

        # Priority keywords
        self.priority_keywords = ['urgent', 'asap', 'important', 'help', 'invoice', 'payment']

        # Track processed messages
        self.processed_ids = set()

    def check_for_updates(self):
        """Check for new incoming WhatsApp messages."""
        # Get recent messages (last 24 hours)
        messages = self.client.messages.list(
            to=self.whatsapp_number,
            limit=50
        )

        for msg in messages:
            # Skip if already processed
            if msg.sid in self.processed_ids:
                continue

            # Check if priority message
            if self._is_priority_message(msg.body):
                self._create_action_file(
                    sender=msg.from_,
                    message=msg.body,
                    timestamp=msg.date_created,
                    message_id=msg.sid
                )

                self.processed_ids.add(msg.sid)
                print(f"🔔 Priority message from {msg.from_}")

    def _is_priority_message(self, text):
        """Check if message contains priority keywords."""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.priority_keywords)

    def _create_action_file(self, sender, message, timestamp, message_id):
        """Create action file for priority message."""
        # Sanitize sender for filename
        safe_sender = sender.replace('whatsapp:', '').replace('+', '').replace(':', '_')

        # Create filename
        date_str = timestamp.strftime('%Y%m%d_%H%M%S')
        filename = f"WHATSAPP_{date_str}_{safe_sender}.md"
        filepath = self.needs_action / filename

        # Create YAML frontmatter
        content = f"""---
type: whatsapp_message
from: {sender}
received: {timestamp.isoformat()}
priority: high
status: pending
message_id: {message_id}
---

## WhatsApp Message from {sender}

**Received:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}

**Message:**
{message}

**Action Required:** Review and respond to this priority message.
"""

        filepath.write_text(content, encoding='utf-8')
        print(f"📝 Created: {filename}")
        return filepath

    def send_message(self, to_number, message):
        """Send a WhatsApp message (optional - for responses)."""
        msg = self.client.messages.create(
            from_=self.whatsapp_number,
            body=message,
            to=f'whatsapp:{to_number}'
        )
        return msg.sid

# Usage example
if __name__ == "__main__":
    import time

    # Set environment variables first:
    # export TWILIO_ACCOUNT_SID="your_account_sid"
    # export TWILIO_AUTH_TOKEN="your_auth_token"
    # export TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"

    watcher = WhatsAppBusinessWatcher()

    print("🚀 WhatsApp Business API Watcher Started")
    print("=" * 60)

    while True:
        try:
            watcher.check_for_updates()
            time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            print("\n⏹️  Stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)
