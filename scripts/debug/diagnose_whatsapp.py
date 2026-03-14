#!/usr/bin/env python3
"""
Diagnostic script to see what's on WhatsApp Web when it loads
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

print("🔍 WhatsApp Web Diagnostic Tool")
print("=" * 60)

session_dir = Path(".whatsapp_session")
session_dir.mkdir(exist_ok=True)

try:
    with sync_playwright() as p:
        print("\n1. Launching browser...")
        context = p.chromium.launch_persistent_context(
            str(session_dir),
            headless=False,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        print("   ✓ Browser launched")

        page = context.pages[0] if context.pages else context.new_page()

        print("\n2. Navigating to WhatsApp Web...")
        page.goto("https://web.whatsapp.com", timeout=30000)
        print("   ✓ Navigation complete")

        print(f"\n3. Current URL: {page.url}")
        print(f"   Page title: {page.title()}")

        print("\n4. Waiting 5 seconds for page to load...")
        page.wait_for_timeout(5000)

        print("\n5. Taking screenshot...")
        screenshot_path = Path("whatsapp_diagnostic.png")
        page.screenshot(path=str(screenshot_path))
        print(f"   ✓ Screenshot saved: {screenshot_path}")

        print("\n6. Checking for key elements...")

        # Check for QR code
        qr_selectors = [
            'canvas[aria-label*="qr" i]',
            'canvas[aria-label*="code" i]',
            '[data-testid="qrcode"]',
            '.qr-code',
            'canvas'
        ]

        for selector in qr_selectors:
            try:
                if page.locator(selector).count() > 0:
                    print(f"   ✓ Found QR code element: {selector}")
                    break
            except:
                pass

        # Check for chat list
        chat_selectors = [
            '[data-testid="chat-list"]',
            '[aria-label*="chat" i]',
            '.chat-list',
            '#pane-side'
        ]

        for selector in chat_selectors:
            try:
                if page.locator(selector).count() > 0:
                    print(f"   ✓ Found chat list element: {selector}")
                    break
            except:
                pass

        print("\n7. Getting page HTML structure...")
        # Get main container classes
        body_html = page.locator('body').evaluate('el => el.innerHTML')
        print(f"   Body HTML length: {len(body_html)} characters")

        # Check for common WhatsApp Web elements
        common_elements = [
            '#app',
            '[data-testid]',
            'canvas',
            '[role="main"]',
            '[role="navigation"]'
        ]

        print("\n8. Element counts:")
        for selector in common_elements:
            try:
                count = page.locator(selector).count()
                print(f"   {selector}: {count}")
            except Exception as e:
                print(f"   {selector}: Error - {e}")

        print("\n9. Listing all data-testid attributes...")
        testids = page.evaluate('''() => {
            const elements = document.querySelectorAll('[data-testid]');
            return Array.from(elements).map(el => el.getAttribute('data-testid')).slice(0, 20);
        }''')
        for testid in testids:
            print(f"   - {testid}")

        print("\n" + "=" * 60)
        print("✅ Diagnostic complete!")
        print("\nNext steps:")
        print("1. Check the screenshot: whatsapp_diagnostic.png")
        print("2. Review the elements found above")
        print("3. If you see a QR code, scan it with your phone")
        print("4. Run this script again after logging in")

        input("\nPress Enter to close browser...")
        context.close()

except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
