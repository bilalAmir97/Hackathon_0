#!/usr/bin/env python3
"""
Comprehensive WhatsApp Web structure discovery.
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

session_dir = Path(".whatsapp_session")

print("🔍 Comprehensive WhatsApp Web Discovery")
print("=" * 60)

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        str(session_dir),
        headless=False,
        args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
    )

    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    print("\nWaiting 30 seconds for full load...")
    time.sleep(30)

    print("\n1. Getting full page structure...")

    # Get all elements with IDs
    ids = page.evaluate("""() => {
        const elements = document.querySelectorAll('[id]');
        return Array.from(elements).map(el => el.id).filter(id => id);
    }""")

    print(f"\n📋 Found {len(ids)} elements with IDs:")
    for id_name in ids[:20]:  # Show first 20
        print(f"  #{id_name}")

    # Get all elements with data attributes
    data_attrs = page.evaluate("""() => {
        const elements = document.querySelectorAll('[data-testid], [data-id]');
        const attrs = new Set();
        elements.forEach(el => {
            if (el.dataset.testid) attrs.add('data-testid="' + el.dataset.testid + '"');
            if (el.dataset.id) attrs.add('data-id="' + el.dataset.id + '"');
        });
        return Array.from(attrs);
    }""")

    print(f"\n📋 Found {len(data_attrs)} unique data attributes:")
    for attr in list(data_attrs)[:20]:  # Show first 20
        print(f"  {attr}")

    # Get main structure
    structure = page.evaluate("""() => {
        const app = document.querySelector('#app');
        if (!app) return 'No #app found';

        const getStructure = (el, depth = 0) => {
            if (depth > 3) return '';
            const tag = el.tagName.toLowerCase();
            const id = el.id ? '#' + el.id : '';
            const classes = el.className ? '.' + el.className.split(' ').slice(0, 2).join('.') : '';
            const children = Array.from(el.children).slice(0, 5);
            const childStr = children.map(c => getStructure(c, depth + 1)).join('');
            return '  '.repeat(depth) + tag + id + classes + '\\n' + childStr;
        };

        return getStructure(app);
    }""")

    print("\n📋 Page Structure (first 3 levels):")
    print(structure[:2000])

    # Save full HTML
    html = page.content()
    with open('whatsapp_full_page.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("\n✓ Full HTML saved to whatsapp_full_page.html")

    # Take screenshot
    page.screenshot(path="whatsapp_structure.png")
    print("✓ Screenshot saved")

    print("\n" + "=" * 60)
    print("✅ Discovery complete!")
    print("\nCheck whatsapp_full_page.html for complete structure")
    print("Press Enter to close...")
    input()
    context.close()
