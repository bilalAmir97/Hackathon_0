#!/usr/bin/env python3
"""
Continuous WhatsApp Processor

Monitors Needs_Action folder and processes WhatsApp messages automatically.
"""

import sys
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.whatsapp_processor import WhatsAppProcessor


def main():
    """Run continuous processing loop"""
    vault_path = "AI_Employee_Vault"
    processor = WhatsAppProcessor(vault_path)

    print("=" * 70)
    print("🤖 WhatsApp Auto-Processor Started")
    print("=" * 70)
    print(f"Vault: {vault_path}")
    print(f"Check interval: 30 seconds")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    try:
        while True:
            # Check for new WhatsApp messages
            needs_action = Path(vault_path) / "Needs_Action"
            whatsapp_files = list(needs_action.glob("WHATSAPP_*.md"))

            if whatsapp_files:
                print(f"\n⏰ {time.strftime('%H:%M:%S')} - Found {len(whatsapp_files)} new message(s)")
                result = processor.process_all()
                print(f"✅ Processed {result['successful']}/{result['processed']} message(s)")

            # Wait before next check
            time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n⏹️  Auto-processor stopped")


if __name__ == "__main__":
    main()
