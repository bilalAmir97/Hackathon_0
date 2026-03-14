#!/usr/bin/env python3
"""
Quick check of what's in the browser
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

session_dir = Path(".whatsapp_session")

try:
    with sync_playwright() as p:
        # Connect to existing browser session
        context = p.chromium.launch_persistent_context(
            str(session_dir),
            headless=False,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )

        if context.pages:
            page = context.pages[0]
            print(f"Current URL: {page.url}")
            print(f"Page title: {page.title()}")

            # Take screenshot
            page.screenshot(path="current_browser_state.png")
            print("Screenshot saved: current_browser_state.png")
        else:
            print("No pages open")

        context.close()

except Exception as e:
    print(f"Error: {e}")
    print("\nThe watcher is probably using the browser session.")
    print("Let me check the watcher's navigation code instead.")
