#!/usr/bin/env python3
"""
Discover WhatsApp Web selectors while logged in with chats visible.
Run this AFTER logging in and seeing your chats.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

session_dir = Path(".whatsapp_session")

print("🔍 Discovering WhatsApp Web Chat Selectors")
print("=" * 60)
print("Make sure you're logged in and can see your chats!")
print("=" * 60)

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        str(session_dir),
        headless=False,
        args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
    )

    page = context.pages[0] if context.pages else context.new_page()

    print("\n1. Navigating to WhatsApp Web...")
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    print("2. Waiting for chats to fully load (up to 60 seconds)...")
    print("   Looking for chat list to appear...")

    # Wait for chat list to appear (try multiple selectors)
    chat_loaded = False
    for attempt in range(12):  # 12 attempts x 5 seconds = 60 seconds
        time.sleep(5)
        print(f"   Attempt {attempt + 1}/12...")

        # Try to find any chat elements
        try:
            count = page.locator('div[role="listitem"], div[role="row"], div[tabindex="-1"]').count()
            if count > 0:
                print(f"   ✓ Found {count} elements! Chats are loaded.")
                chat_loaded = True
                break
        except:
            pass

    if not chat_loaded:
        print("   ⚠️  Chats didn't load within 60 seconds")

    print("\n3. Testing chat list selectors...")

    selectors_to_test = [
        'div[role="listitem"]',
        'div[role="row"]',
        'div[data-testid="cell-frame-container"]',
        'div[aria-label*="Chat" i]',
        '#pane-side div',
        'div._2EXPL',
        'div[class*="chat"]',
    ]

    for selector in selectors_to_test:
        try:
            count = page.locator(selector).count()
            print(f"  {selector}: {count} elements")
            if count > 0:
                print(f"    ✓ FOUND!")
        except Exception as e:
            print(f"  {selector}: Error - {str(e)[:50]}")

    print("\n4. Getting page HTML structure...")
    # Get a sample of the page structure
    try:
        html_sample = page.evaluate("""() => {
            const paneEl = document.querySelector('#pane-side');
            if (paneEl) {
                return paneEl.innerHTML.substring(0, 2000);
            }
            return 'No #pane-side found';
        }""")

        with open('whatsapp_html_sample.txt', 'w', encoding='utf-8') as f:
            f.write(html_sample)
        print("  ✓ HTML sample saved to whatsapp_html_sample.txt")
    except Exception as e:
        print(f"  ✗ Error getting HTML: {e}")

    print("\n5. Taking screenshot...")
    page.screenshot(path="whatsapp_logged_in.png")
    print("  ✓ Screenshot saved to whatsapp_logged_in.png")

    print("\n" + "=" * 60)
    print("✅ Discovery complete!")
    print("\nPress Enter to close...")
    input()
    context.close()
