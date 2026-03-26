#!/usr/bin/env python3
"""
WhatsApp Message Processor

Processes WhatsApp action files based on configurable rules.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class WhatsAppProcessor:
    """Process WhatsApp messages with configurable rules"""

    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.done = self.vault_path / "Done"
        self.logs = self.vault_path / "Logs"

        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.done.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

        # Load processing rules
        self.rules = self.load_rules()

    def load_rules(self) -> Dict:
        """Load processing rules from config file or use defaults"""
        config_file = Path("config/whatsapp_rules.json")

        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"✓ Loaded rules from {config_file}")
                return config
            except Exception as e:
                print(f"⚠️  Error loading config: {e}, using defaults")

        # Default rules if config file doesn't exist
        return {
            "priority_keywords": [
                "urgent", "asap", "important", "help",
                "invoice", "payment", "emergency", "critical", "deadline"
            ],
            "ignore_senders": ["WhatsApp"],
            "sender_rules": {},
            "keyword_responses": {},
            "default_actions": {
                "priority": "notify_and_log",
                "group": "log_only",
                "personal": "notify_and_log",
                "ignored": "archive"
            },
            "auto_response_settings": {"enabled": False},
            "notification_settings": {"dashboard": True}
        }

    def parse_action_file(self, file_path: Path) -> Optional[Dict]:
        """Parse WhatsApp action file and extract metadata"""
        try:
            content = file_path.read_text()

            # Extract metadata from frontmatter
            metadata = {}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    for line in frontmatter.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip()

            # Extract message content
            message_section = re.search(r"### Message Content\s*\n\n(.*?)\n\n###", content, re.DOTALL)
            message_content = message_section.group(1).strip() if message_section else ""

            return {
                "file_path": file_path,
                "file_name": file_path.name,
                "sender": metadata.get("from", "Unknown"),
                "priority": metadata.get("priority", "normal"),
                "timestamp": metadata.get("received", ""),
                "message": message_content,
                "metadata": metadata
            }
        except Exception as e:
            print(f"⚠️  Error parsing {file_path.name}: {e}")
            return None

    def classify_message(self, parsed: Dict) -> str:
        """Classify message type based on rules"""
        sender = parsed["sender"]
        message = parsed["message"].lower()

        # Check if ignored sender
        for ignored in self.rules.get("ignore_senders", []):
            if ignored.lower() in sender.lower():
                return "ignored"

        # Check sender-specific rules
        sender_rules = self.rules.get("sender_rules", {})
        for rule_sender, rule_config in sender_rules.items():
            if rule_sender.lower() in sender.lower():
                return rule_config.get("classification", "group")

        # Check if priority
        if parsed["priority"] == "high":
            return "priority"

        for keyword in self.rules.get("priority_keywords", []):
            if keyword in message:
                return "priority"

        # Default to personal
        return "personal"

    def process_message(self, parsed: Dict) -> Dict:
        """Process a single message based on its classification"""
        classification = self.classify_message(parsed)
        action_type = self.rules.get("default_actions", {}).get(classification, "log_only")

        result = {
            "file": parsed["file_name"],
            "sender": parsed["sender"],
            "classification": classification,
            "action": action_type,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "auto_response": None
        }

        print(f"\n📨 Processing: {parsed['sender']}")
        print(f"   Classification: {classification}")
        print(f"   Action: {action_type}")

        # Check for auto-response
        auto_response = self.check_auto_response(parsed)
        if auto_response:
            result["auto_response"] = auto_response
            print(f"   🤖 Auto-response suggested: {auto_response[:50]}...")

            # Create approval request for reply
            approval_file = self.create_reply_approval_request(parsed, auto_response)
            result["approval_file"] = str(approval_file)

        # Execute action
        if action_type == "notify_and_log":
            result["actions_taken"] = ["logged", "notification_created"]
            if auto_response:
                result["actions_taken"].append("approval_request_created")
            self.log_message(parsed, classification)
            self.create_notification(parsed, auto_response)
            result["success"] = True

        elif action_type == "log_only":
            result["actions_taken"] = ["logged"]
            self.log_message(parsed, classification)
            result["success"] = True

        elif action_type == "archive":
            result["actions_taken"] = ["archived"]
            self.log_message(parsed, "archived")
            result["success"] = True

        # Move to Done
        if result["success"]:
            self.move_to_done(parsed["file_path"])
            print(f"   ✅ Processed and moved to Done/")

        return result

    def check_auto_response(self, parsed: Dict) -> Optional[str]:
        """Check if message should get an auto-response"""
        auto_settings = self.rules.get("auto_response_settings", {})

        if not auto_settings.get("enabled", False):
            return None

        sender = parsed["sender"]
        message = parsed["message"].lower()

        # Check sender-specific rules first
        sender_rules = self.rules.get("sender_rules", {})
        for rule_sender, rule_config in sender_rules.items():
            if rule_sender.lower() in sender.lower():
                if rule_config.get("auto_respond", False):
                    return rule_config.get("response_template")

        # Check keyword-based responses
        keyword_responses = self.rules.get("keyword_responses", {})
        for keyword, response_config in keyword_responses.items():
            if response_config.get("enabled", False) and keyword in message:
                return response_config.get("response")

        return None

    def log_message(self, parsed: Dict, classification: str):
        """Log message to daily log file"""
        log_date = datetime.now().strftime("%Y-%m-%d")
        log_file = self.logs / f"{log_date}.json"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "whatsapp_processed",
            "sender": parsed["sender"],
            "classification": classification,
            "priority": parsed["priority"],
            "message_preview": parsed["message"][:100]
        }

        # Append to log
        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except:
                logs = []

        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))

    def create_notification(self, parsed: Dict, auto_response: Optional[str] = None):
        """Create a notification summary"""
        notification_settings = self.rules.get("notification_settings", {})

        if not notification_settings.get("dashboard", True):
            return

        notification_file = self.vault_path / "Dashboard.md"

        notification = f"\n## 🔔 New WhatsApp Message\n"
        notification += f"**From**: {parsed['sender']}\n"
        notification += f"**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        notification += f"**Priority**: {parsed['priority']}\n"
        notification += f"**Preview**: {parsed['message'][:100]}...\n"

        if auto_response:
            notification += f"\n**Auto-Response Suggested**: {auto_response[:80]}...\n"
            notification += f"**Status**: Pending approval in /Pending_Approval\n"

        notification += "\n"

        # Append to dashboard
        if notification_file.exists():
            content = notification_file.read_text()
            notification_file.write_text(content + notification)
        else:
            notification_file.write_text(notification)

    def create_reply_approval_request(self, parsed: Dict, auto_response: str):
        """Create approval request for WhatsApp reply.

        Args:
            parsed: Parsed message data
            auto_response: Suggested response text
        """
        pending_approval = self.vault_path / "Pending_Approval"
        pending_approval.mkdir(parents=True, exist_ok=True)

        # Generate approval ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sender_safe = parsed['sender'].replace(' ', '_').replace('/', '_')[:30]
        approval_id = f"whatsapp_reply_{sender_safe}_{timestamp}"

        # Create approval file
        approval_file = pending_approval / f"APPROVAL_{approval_id}.md"

        # Calculate expiration (24 hours from now)
        from datetime import timedelta
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat() + 'Z'

        approval_content = f"""---
approval_id: {approval_id}
action_type: whatsapp_reply
created_at: {datetime.now().isoformat()}Z
expires_at: {expires_at}
status: pending
risk_assessment: low
action_params:
  chat_name: "{parsed['sender']}"
  message_text: "{auto_response}"
reasoning: |
  Automated reply to WhatsApp message from {parsed['sender']}.
  Message priority: {parsed['priority']}.
  Suggested response acknowledges receipt.
---

## WhatsApp Reply Approval Request

**To**: {parsed['sender']}
**Message**: "{auto_response}"

### Original Message Context
- **From**: {parsed['sender']}
- **Received**: {parsed['timestamp']}
- **Content**: {parsed['message'][:200]}
- **Priority**: {parsed['priority']}

### Suggested Action
Send automated reply via WhatsApp Web.

### To Approve
Move this file to `/Approved` folder.

### To Reject
Move this file to `/Rejected` folder.

### Notes
- Reply will be sent via Playwright automation to WhatsApp Web
- Session must be active (logged in)
- Message will be logged in audit trail
"""

        approval_file.write_text(approval_content)
        print(f"   📋 Created approval request: {approval_file.name}")

        return approval_file

    def move_to_done(self, file_path: Path):
        """Move processed file to Done folder"""
        done_path = self.done / file_path.name
        file_path.rename(done_path)

    def process_all(self) -> Dict:
        """Process all WhatsApp action files"""
        whatsapp_files = list(self.needs_action.glob("WHATSAPP_*.md"))

        if not whatsapp_files:
            print("📭 No WhatsApp messages to process")
            return {"processed": 0, "results": []}

        print(f"\n{'='*70}")
        print(f"📱 WhatsApp Message Processor")
        print(f"{'='*70}")
        print(f"Found {len(whatsapp_files)} message(s) to process\n")

        results = []
        for file_path in whatsapp_files:
            parsed = self.parse_action_file(file_path)
            if parsed:
                result = self.process_message(parsed)
                results.append(result)

        # Summary
        successful = sum(1 for r in results if r["success"])
        print(f"\n{'='*70}")
        print(f"📊 Processing Summary")
        print(f"{'='*70}")
        print(f"✅ Processed: {successful}/{len(results)}")
        print(f"{'='*70}\n")

        return {
            "processed": len(results),
            "successful": successful,
            "results": results
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Process WhatsApp messages")
    parser.add_argument(
        "--vault-path",
        default="AI_Employee_Vault",
        help="Path to vault (default: AI_Employee_Vault)"
    )
    parser.add_argument(
        "--file",
        help="Process specific file"
    )

    args = parser.parse_args()

    processor = WhatsAppProcessor(args.vault_path)

    if args.file:
        file_path = processor.needs_action / args.file
        if file_path.exists():
            parsed = processor.parse_action_file(file_path)
            if parsed:
                processor.process_message(parsed)
        else:
            print(f"❌ File not found: {args.file}")
    else:
        processor.process_all()


if __name__ == "__main__":
    main()
