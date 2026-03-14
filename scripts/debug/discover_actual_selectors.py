#!/usr/bin/env python3
"""
Discover actual WhatsApp Web selectors by inspecting the live page
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

session_dir = Path(".whatsapp_session")

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
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    print("2. Waiting 15 seconds for page to fully load...")
    time.sleep(15)

    print("\n3. Discovering actual selectors...")

    # Try to find chat list container
    print("\n📋 Looking for Chat List Container:")
    possible_selectors = [
        "#pane-side",
        "div[role='grid']",
        "div[aria-label*='Chat list' i]",
        "div[aria-label*='Conversation list' i]",
        "._2EXPL",
        "._3ZW2E",
    ]

    for selector in possible_selectors:
        try:
            count = page.locator(selector).count()
            if count > 0:
                print(f"  ✓ Found: {selector} ({count} elements)")

                # Get more details
                elem = page.locator(selector).first
                try:
                    tag = elem.evaluate("el => el.tagName")
                    classes = elem.evaluate("el => el.className")
                    aria = elem.get_attribute("aria-label")
                    print(f"    Tag: {tag}")
                    if classes:
                        print(f"    Classes: {classes[:100]}")
                    if aria:
                        print(f"    Aria-label: {aria[:100]}")
                except:
                    pass
        except Exception as e:
            print(f"  ✗ {selector}: {str(e)[:50]}")

    # Try to find individual chat items
    print("\n💬 Looking for Individual Chat Items:")
    chat_selectors = [
        "div[role='listitem']",
        "div[data-testid='cell-frame-container']",
        "._2EXPL ._3j7s9",
        "div[aria-label*='Chat with' i]",
    ]

    for selector in chat_selectors:
        try:
            count = page.locator(selector).count()
            if count > 0:
                print(f"  ✓ Found: {selector} ({count} elements)")
        except Exception as e:
            print(f"  ✗ {selector}: {str(e)[:50]}")

    # Try to find message text
    print("\n📝 Looking for Message Text:")
    message_selectors = [
        "span[dir='ltr']",
        "span[class*='selectable-text']",
        "._11JPr",
        "span[data-testid='conversation-info-header-chat-title']",
    ]

    for selector in message_selectors:
        try:
            count = page.locator(selector).count()
            if count > 0:
                print(f"  ✓ Found: {selector} ({count} elements)")
                # Try to get sample text
                try:
                    text = page.locator(selector).first.text_content()
                    if text:
                        print(f"    Sample: {text[:50]}")
                except:
                    pass
        except Exception as e:
            print(f"  ✗ {selector}: {str(e)[:50]}")

    print("\n4. Getting page structure...")
    # Get all elements with role attribute
    roles = page.evaluate("""() => {
        const elements = document.querySelectorAll('[role]');
        const roles = {};
        elements.forEach(el => {
            const role = el.getAttribute('role');
            roles[role] = (roles[role] || 0) + 1;
        });
        return roles;
    }""")

    print("\n🎭 Elements by Role:")
    for role, count in sorted(roles.items()):
        print(f"  {role}: {count}")

    print("\n5. Taking screenshot...")
    page.screenshot(path="whatsapp_actual_selectors.png")
    print("  ✓ Screenshot saved")

    print("\n" + "=" * 60)
    print("✅ Discovery complete!")
    print("\nPress Enter to close...")
    input()
    context.close()
