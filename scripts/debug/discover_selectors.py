#!/usr/bin/env python3
"""
Discover actual WhatsApp Web selectors
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

session_dir = Path(".whatsapp_session")
session_dir.mkdir(exist_ok=True)

print("🔍 Discovering WhatsApp Web Selectors")
print("=" * 60)

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        str(session_dir),
        headless=False,
        args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
    )

    page = context.pages[0] if context.pages else context.new_page()

    print("\n1. Navigating to WhatsApp Web...")
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=30000)

    print("2. Waiting 10 seconds for page to load...")
    time.sleep(10)

    print("\n3. Discovering selectors...")

    # Check for main app container
    selectors_to_check = [
        "#app",
        "#side",
        "#pane-side",
        "[role='application']",
        "[role='main']",
        "header",
        "canvas",
        "[aria-label*='chat' i]",
        "[aria-label*='conversation' i]",
        "[aria-label*='message' i]",
        "._2EXPL",  # Common WhatsApp class
        "._3ZW2E",  # Another common class
    ]

    print("\nFound selectors:")
    for selector in selectors_to_check:
        try:
            count = page.locator(selector).count()
            if count > 0:
                print(f"  ✓ {selector}: {count} element(s)")

                # Get first element's attributes
                if count > 0:
                    elem = page.locator(selector).first
                    try:
                        aria_label = elem.get_attribute("aria-label")
                        if aria_label:
                            print(f"    aria-label: {aria_label[:100]}")
                    except:
                        pass
        except Exception as e:
            print(f"  ✗ {selector}: Error - {str(e)[:50]}")

    print("\n4. Checking for chat list...")
    # Try to find chat list container
    chat_list_selectors = [
        "#pane-side",
        "[aria-label*='Chat list' i]",
        "[aria-label*='Conversation list' i]",
        "div[role='grid']",
        "div[role='list']",
    ]

    for selector in chat_list_selectors:
        try:
            if page.locator(selector).count() > 0:
                print(f"  ✓ Chat list found: {selector}")
        except:
            pass

    print("\n5. Taking screenshot...")
    page.screenshot(path="whatsapp_selectors.png")
    print("  ✓ Screenshot saved: whatsapp_selectors.png")

    print("\n" + "=" * 60)
    print("Press Enter to close...")
    input()
    context.close()
