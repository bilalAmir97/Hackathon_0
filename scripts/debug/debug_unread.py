#!/usr/bin/env python3
"""Debug script to check unread message detection."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def debug_unread():
    """Check what unread messages look like."""
    session_dir = Path('.whatsapp_session')

    playwright = await async_playwright().start()
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=str(session_dir),
        headless=False,
        args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
    )

    page = context.pages[0] if context.pages else await context.new_page()

    # Navigate to WhatsApp Web
    await page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=60000)
    await page.wait_for_selector('div[aria-label="Chat list"][role="grid"]', timeout=30000)

    print("=" * 60)
    print("Checking for unread messages...")
    print("=" * 60)

    # Get all chat rows
    chat_elements = await page.query_selector_all('div[role="row"]')
    print(f"\nTotal chats found: {len(chat_elements)}")

    unread_count = 0
    priority_keywords = ['urgent', 'asap', 'important', 'help', 'invoice', 'payment', 'emergency', 'critical', 'deadline']

    for i, chat_elem in enumerate(chat_elements):
        # Check for unread indicator
        unread_indicator = await chat_elem.query_selector('span[aria-label*="unread message" i]')

        if unread_indicator:
            unread_count += 1
            print(f"\n--- UNREAD CHAT #{unread_count} ---")

            # Get unread badge text
            badge_text = await unread_indicator.inner_text()
            print(f"Unread badge: {badge_text}")

            # Use updated extraction logic
            all_text = await chat_elem.inner_text()
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]

            if len(lines) >= 2:
                sender = lines[0]
                print(f"Sender: {sender}")

                # Look for message content
                message = ""
                for j, line in enumerate(lines):
                    if j == 0:
                        continue
                    # Skip timestamp lines
                    if ':' in line and ('AM' in line or 'PM' in line or len(line) < 10):
                        continue
                    # Skip unread count
                    if line.isdigit() and len(line) <= 3:
                        continue
                    # Skip sender indicators
                    if line.startswith('~'):
                        continue
                    # Skip single colon
                    if line == ':':
                        continue
                    # Skip phone numbers
                    if line.startswith('+') and len(line) < 20:
                        continue
                    # Get actual message (longer text)
                    if len(line) > 15:
                        message = line
                        break

                message = message.strip()
                print(f"Message: {message[:150]}")

                # Check for priority keywords
                if message:
                    message_lower = message.lower()
                    found_keywords = [kw for kw in priority_keywords if kw in message_lower]
                    if found_keywords:
                        print(f"🔔 PRIORITY! Keywords found: {', '.join(found_keywords)}")
                    else:
                        print("   (no priority keywords)")
                else:
                    print("   (no message content extracted)")
            else:
                print(f"⚠️  Could not extract message data")

    print(f"\n{'=' * 60}")
    print(f"Total unread chats: {unread_count}")
    print(f"{'=' * 60}")

    await context.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(debug_unread())
