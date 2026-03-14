#!/usr/bin/env python3
"""
WhatsApp Rules Configuration Manager

Easy tool to customize WhatsApp message processing rules.
"""

import json
from pathlib import Path


class ConfigManager:
    """Manage WhatsApp processing configuration"""

    def __init__(self):
        self.config_file = Path("config/whatsapp_rules.json")
        self.config = self.load_config()

    def load_config(self):
        """Load current configuration"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}

    def save_config(self):
        """Save configuration to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
        print(f"✓ Configuration saved to {self.config_file}")

    def show_current_config(self):
        """Display current configuration"""
        print("\n" + "=" * 70)
        print("📋 Current WhatsApp Processing Rules")
        print("=" * 70)

        print("\n🔑 Priority Keywords:")
        for kw in self.config.get("priority_keywords", []):
            print(f"  - {kw}")

        print("\n🚫 Ignored Senders:")
        for sender in self.config.get("ignore_senders", []):
            print(f"  - {sender}")

        print("\n👥 Sender-Specific Rules:")
        sender_rules = self.config.get("sender_rules", {})
        if sender_rules:
            for sender, rules in sender_rules.items():
                print(f"  - {sender}:")
                print(f"    Action: {rules.get('action', 'N/A')}")
                print(f"    Auto-respond: {rules.get('auto_respond', False)}")
        else:
            print("  (none configured)")

        print("\n🤖 Auto-Response Settings:")
        auto_settings = self.config.get("auto_response_settings", {})
        print(f"  Enabled: {auto_settings.get('enabled', False)}")
        print(f"  Delay: {auto_settings.get('delay_seconds', 60)}s")

        print("\n💬 Keyword Auto-Responses:")
        keyword_responses = self.config.get("keyword_responses", {})
        if keyword_responses:
            for keyword, response_config in keyword_responses.items():
                if response_config.get("enabled", False):
                    print(f"  - '{keyword}': {response_config.get('response', '')[:50]}...")
        else:
            print("  (none enabled)")

        print("\n" + "=" * 70 + "\n")

    def add_priority_keyword(self, keyword: str):
        """Add a priority keyword"""
        keywords = self.config.get("priority_keywords", [])
        if keyword not in keywords:
            keywords.append(keyword)
            self.config["priority_keywords"] = keywords
            self.save_config()
            print(f"✓ Added priority keyword: {keyword}")
        else:
            print(f"⚠️  Keyword already exists: {keyword}")

    def add_ignored_sender(self, sender: str):
        """Add a sender to ignore list"""
        ignored = self.config.get("ignore_senders", [])
        if sender not in ignored:
            ignored.append(sender)
            self.config["ignore_senders"] = ignored
            self.save_config()
            print(f"✓ Added ignored sender: {sender}")
        else:
            print(f"⚠️  Sender already ignored: {sender}")

    def enable_auto_responses(self, enabled: bool = True):
        """Enable or disable auto-responses"""
        if "auto_response_settings" not in self.config:
            self.config["auto_response_settings"] = {}

        self.config["auto_response_settings"]["enabled"] = enabled
        self.save_config()
        status = "enabled" if enabled else "disabled"
        print(f"✓ Auto-responses {status}")

    def add_keyword_response(self, keyword: str, response: str, enabled: bool = True):
        """Add an auto-response for a keyword"""
        if "keyword_responses" not in self.config:
            self.config["keyword_responses"] = {}

        self.config["keyword_responses"][keyword] = {
            "enabled": enabled,
            "response": response,
            "notify": True
        }
        self.save_config()
        print(f"✓ Added auto-response for keyword: {keyword}")

    def add_sender_rule(self, sender: str, action: str = "log_only",
                       auto_respond: bool = False, response: str = None):
        """Add a sender-specific rule"""
        if "sender_rules" not in self.config:
            self.config["sender_rules"] = {}

        self.config["sender_rules"][sender] = {
            "action": action,
            "auto_respond": auto_respond,
            "response_template": response
        }
        self.save_config()
        print(f"✓ Added rule for sender: {sender}")


def main():
    """Interactive configuration manager"""
    import sys

    manager = ConfigManager()

    if len(sys.argv) == 1:
        # Show current config
        manager.show_current_config()
        print("\nUsage:")
        print("  python scripts/config_whatsapp.py show")
        print("  python scripts/config_whatsapp.py add-keyword <keyword>")
        print("  python scripts/config_whatsapp.py ignore-sender <sender>")
        print("  python scripts/config_whatsapp.py enable-auto-response")
        print("  python scripts/config_whatsapp.py add-response <keyword> <response>")
        return

    command = sys.argv[1]

    if command == "show":
        manager.show_current_config()

    elif command == "add-keyword" and len(sys.argv) > 2:
        manager.add_priority_keyword(sys.argv[2])

    elif command == "ignore-sender" and len(sys.argv) > 2:
        manager.add_ignored_sender(sys.argv[2])

    elif command == "enable-auto-response":
        manager.enable_auto_responses(True)

    elif command == "disable-auto-response":
        manager.enable_auto_responses(False)

    elif command == "add-response" and len(sys.argv) > 3:
        keyword = sys.argv[2]
        response = " ".join(sys.argv[3:])
        manager.add_keyword_response(keyword, response)

    elif command == "add-sender-rule" and len(sys.argv) > 3:
        sender = sys.argv[2]
        action = sys.argv[3]
        manager.add_sender_rule(sender, action)

    else:
        print("❌ Invalid command or missing arguments")
        print("\nAvailable commands:")
        print("  show - Display current configuration")
        print("  add-keyword <keyword> - Add priority keyword")
        print("  ignore-sender <sender> - Add sender to ignore list")
        print("  enable-auto-response - Enable auto-responses")
        print("  disable-auto-response - Disable auto-responses")
        print("  add-response <keyword> <response> - Add keyword auto-response")
        print("  add-sender-rule <sender> <action> - Add sender-specific rule")


if __name__ == "__main__":
    main()
