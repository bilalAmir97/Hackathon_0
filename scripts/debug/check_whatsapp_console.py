#!/usr/bin/env python3
"""
Check WhatsApp Web console errors and try to bypass detection
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

print("🔍 Checking WhatsApp Web Console Errors")
print("=" * 60)

session_dir = Path(".whatsapp_session")
session_dir.mkdir(exist_ok=True)

try:
    with sync_playwright() as p:
        print("\n1. Launching browser with stealth settings...")

        # More aggressive anti-detection
        context = p.chromium.launch_persistent_context(
            str(session_dir),
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ],
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        page = context.pages[0] if context.pages else context.new_page()

        # Capture console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))

        print("   ✓ Browser launched")

        print("\n2. Navigating to WhatsApp Web...")
        page.goto("https://web.whatsapp.com", wait_until="networkidle", timeout=30000)
        print("   ✓ Navigation complete")

        print("\n3. Waiting 10 seconds for page to fully load...")
        page.wait_for_timeout(10000)

        print("\n4. Console messages:")
        for msg in console_messages:
            print(f"   {msg}")

        print("\n5. Checking page state...")
        print(f"   URL: {page.url}")
        print(f"   Title: {page.title()}")

        # Check if page has loaded
        app_html = page.evaluate('() => document.getElementById("app").innerHTML.length')
        print(f"   #app innerHTML length: {app_html}")

        # Check for specific WhatsApp elements
        has_qr = page.evaluate('() => document.querySelector("canvas") !== null')
        has_side = page.evaluate('() => document.querySelector("#side") !== null')
        print(f"   Has canvas (QR): {has_qr}")
        print(f"   Has #side (chat list): {has_side}")

        print("\n6. Taking screenshot...")
        page.screenshot(path="whatsapp_console_check.png")
        print("   ✓ Screenshot saved: whatsapp_console_check.png")

        print("\n" + "=" * 60)
        if app_html == 0:
            print("❌ WhatsApp Web is not loading properly!")
            print("\nPossible causes:")
            print("1. WhatsApp is detecting automation")
            print("2. Network/firewall blocking")
            print("3. WhatsApp Web service issue")
            print("\nRecommendation: Run from Windows instead of WSL2")
        else:
            print("✅ Page has content, checking why elements aren't visible...")

        input("\nPress Enter to close...")
        context.close()

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
