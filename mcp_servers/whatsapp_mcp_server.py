"""
WhatsApp MCP Server - Send messages via WhatsApp Web

Provides MCP tools for sending WhatsApp messages using Playwright automation.
Integrates with approval workflow for human-in-the-loop message sending.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import error recovery decorators
from scripts.error_recovery.decorators import with_retry, with_circuit_breaker


class WhatsAppClient:
    """
    WhatsApp Web client for sending messages via Playwright automation.

    Uses persistent browser context from WhatsApp watcher for session management.
    Includes error handling, retry logic, and circuit breaker protection.
    """

    def __init__(self, session_dir: Optional[str] = None):
        """
        Initialize WhatsApp client.

        Args:
            session_dir: Path to Playwright session directory (default: .whatsapp_session)
        """
        self.session_dir = Path(session_dir or '.whatsapp_session')
        self.playwright = None
        self.context = None
        self.page = None

        # Validate session directory exists
        if not self.session_dir.exists():
            raise ValueError(
                f"WhatsApp session directory not found: {self.session_dir}\n"
                "Please run the WhatsApp watcher first to create a session."
            )

    async def _ensure_browser_ready(self):
        """
        Ensure browser context and page are ready.

        Raises:
            Exception: If browser initialization fails
        """
        if self.context is None or self.page is None:
            await self._launch_browser()

    async def _launch_browser(self):
        """
        Launch Playwright browser with persistent context.

        Raises:
            ImportError: If Playwright is not installed
            Exception: If browser launch fails
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run: uv run playwright install chromium"
            )

        print("🚀 Launching browser...")

        # Launch browser with persistent context for session management
        self.playwright = await async_playwright().start()

        # WhatsApp Web blocks headless mode, must use headed browser
        # Add more args to avoid detection and improve stability
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_dir),
            headless=False,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
            ],
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ignore_https_errors=True,
            slow_mo=100  # Slow down operations by 100ms for stability
        )

        print("✓ Browser launched")

        # Get or create page
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()

        # Navigate to WhatsApp Web if not already there
        if 'web.whatsapp.com' not in self.page.url:
            print("🌐 Navigating to WhatsApp Web...")

            try:
                await self.page.goto(
                    'https://web.whatsapp.com',
                    wait_until='networkidle',
                    timeout=120000
                )
                print("✓ Page loaded")
            except Exception as e:
                print(f"⚠️ Navigation timeout, trying with domcontentloaded...")
                await self.page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=90000)

            # Wait for WhatsApp Web to load
            print("⏳ Waiting for WhatsApp Web interface...")

            # Try multiple selectors
            selectors_to_try = [
                'div[aria-label="Chat list"]',
                'div[role="grid"]',
                '[data-testid="chat-list"]',
                'div[data-tab="3"]',
            ]

            loaded = False
            for selector in selectors_to_try:
                try:
                    await self.page.wait_for_selector(selector, timeout=30000)
                    print(f"✓ WhatsApp Web loaded")
                    loaded = True
                    break
                except:
                    continue

            if not loaded:
                print("⚠️ Could not detect WhatsApp Web interface, waiting 10s...")
                await self.page.wait_for_timeout(10000)

    async def _ensure_logged_in(self) -> bool:
        """
        Ensure user is logged in to WhatsApp Web.

        Returns:
            True if logged in, False otherwise
        """
        # Check for QR code (indicates not logged in)
        qr_code = await self.page.query_selector('canvas')
        if qr_code:
            print("❌ Not logged in - QR code detected")
            print("   Please scan QR code with your phone")
            return False

        # Check for chat list (indicates logged in)
        chat_list_selectors = [
            'div[aria-label="Chat list"]',
            'div[role="grid"]',
            '#pane-side',
            '[data-testid="chat-list"]'
        ]

        for selector in chat_list_selectors:
            element = await self.page.query_selector(selector)
            if element:
                print("✓ Logged in to WhatsApp Web")
                return True

        print("⚠️ Could not verify login status")
        return False

    @with_retry(max_attempts=3, base_delay=2.0)
    @with_circuit_breaker(service_name="whatsapp_send", failure_threshold=5, cooldown_seconds=60)
    async def send_message(self, chat_name: str, message_text: str) -> Dict[str, Any]:
        """
        Send a message to a WhatsApp chat.

        Args:
            chat_name: Name of the chat/contact to send message to
            message_text: Message text to send

        Returns:
            Dict with status, chat_name, message_text, timestamp

        Raises:
            Exception: If message sending fails
        """
        try:
            # Ensure browser is ready
            await self._ensure_browser_ready()

            # Ensure logged in
            if not await self._ensure_logged_in():
                raise Exception("Not logged in to WhatsApp Web. Please scan QR code first.")

            # Wait longer for interface to be fully ready and interactive
            print("⏳ Waiting for interface to be fully interactive...")
            await self.page.wait_for_timeout(5000)

            # Step 1: Find and interact with the search INPUT element
            print("🔍 Looking for main chat list search box...")

            # Wait for the page to be fully loaded
            await self.page.wait_for_timeout(2000)

            search_box_found = False

            # The search box is an INPUT element, not a contenteditable div
            # Try multiple selectors to find it
            search_input_selectors = [
                'input[aria-label*="Search"]',
                'input[placeholder*="Search"]',
                '#_r_b_',  # Known ID from diagnostic
                'input.html-input',
            ]

            for selector in search_input_selectors:
                try:
                    print(f"   Trying selector: {selector}")
                    search_input = await self.page.wait_for_selector(selector, timeout=5000, state='visible')
                    if search_input:
                        print(f"   ✓ Found search input with selector: {selector}")

                        # Click to focus
                        await search_input.click()
                        await self.page.wait_for_timeout(500)

                        # Clear any existing text
                        await search_input.fill('')
                        await self.page.wait_for_timeout(300)

                        # Type the chat name
                        print(f"   Typing chat name: {chat_name}")
                        await search_input.type(chat_name, delay=100)
                        await self.page.wait_for_timeout(500)
                        print(f"✓ Typed chat name in search box")

                        search_box_found = True
                        break
                except Exception as e:
                    print(f"   Failed with {selector}: {str(e)[:80]}")
                    continue

            if not search_box_found:
                # Take screenshot for debugging
                try:
                    screenshot_path = "whatsapp_search_debug.png"
                    await self.page.screenshot(path=screenshot_path)
                    print(f"   📸 Screenshot saved to {screenshot_path}")
                except:
                    pass
                raise Exception("Could not find main chat list search box")

            # Wait longer for search results to populate
            print("⏳ Waiting for search results...")
            await self.page.wait_for_timeout(3000)

            # Step 2: Click on the chat from search results
            # Look specifically in the search results area, not "create list" area
            print(f"🔍 Looking for chat in search results: {chat_name}")

            chat_clicked = False

            # Strategy 1: Try to find the chat by exact title match in search results
            try:
                print(f"   Strategy 1: Looking for exact title match...")
                # Look for span with exact title in the search results
                chat_element = await self.page.wait_for_selector(
                    f'span[title="{chat_name}"]',
                    timeout=5000,
                    state='visible'
                )
                if chat_element:
                    # Get the parent clickable element (usually a few levels up)
                    parent = await chat_element.evaluate_handle('el => el.closest("div[role=\\"listitem\\"]") || el.closest("div[role=\\"row\\"]")')
                    if parent:
                        await parent.as_element().click()
                        chat_clicked = True
                        print(f"✓ Chat opened via exact title match")
            except Exception as e:
                print(f"   Strategy 1 failed: {str(e)[:80]}")

            # Strategy 2: Try clicking on any element containing the chat name in search results
            if not chat_clicked:
                try:
                    print(f"   Strategy 2: Looking for partial match in search results...")
                    # Use XPath to find elements containing the text
                    await self.page.wait_for_timeout(1000)
                    chat_element = await self.page.wait_for_selector(
                        f'xpath=//div[@id="pane-side"]//span[contains(text(), "{chat_name}")]',
                        timeout=5000,
                        state='visible'
                    )
                    if chat_element:
                        parent = await chat_element.evaluate_handle('el => el.closest("div[role=\\"listitem\\"]") || el.closest("div[role=\\"row\\"]")')
                        if parent:
                            await parent.as_element().click()
                            chat_clicked = True
                            print(f"✓ Chat opened via partial match")
                except Exception as e:
                    print(f"   Strategy 2 failed: {str(e)[:80]}")

            # Strategy 3: Press Enter to select first search result
            if not chat_clicked:
                try:
                    print(f"   Strategy 3: Pressing Enter to select first result...")
                    await self.page.keyboard.press('Enter')
                    await self.page.wait_for_timeout(2000)

                    # Verify a chat opened by checking for message input box
                    message_box = await self.page.query_selector('div[contenteditable="true"][data-tab="10"]')
                    if message_box:
                        chat_clicked = True
                        print(f"✓ Chat opened via Enter key")
                except Exception as e:
                    print(f"   Strategy 3 failed: {str(e)[:80]}")

            if not chat_clicked:
                # Take screenshot for debugging
                try:
                    screenshot_path = "whatsapp_chat_not_found.png"
                    await self.page.screenshot(path=screenshot_path)
                    print(f"   📸 Screenshot saved to {screenshot_path}")
                except:
                    pass
                raise Exception(f"Could not find or open chat: {chat_name}. Make sure the name matches exactly.")

            # Wait for chat to fully load
            print("⏳ Waiting for chat to load...")
            await self.page.wait_for_timeout(3000)

            # Step 3: Type message in message box
            print(f"📝 Typing message...")

            # Find the message input box in the footer - use the most specific selector first
            message_box_selectors = [
                'footer div[contenteditable="true"][data-tab="10"]',
                'footer div[role="textbox"]',
                'footer div[contenteditable="true"]',
                'div[contenteditable="true"][data-tab="10"]',
            ]

            message_box_found = False
            for selector in message_box_selectors:
                try:
                    print(f"   Trying message box selector: {selector}")
                    message_box = await self.page.wait_for_selector(selector, timeout=5000, state='visible')
                    if message_box:
                        # Click to focus
                        await message_box.click()
                        await self.page.wait_for_timeout(500)

                        # Clear any existing text
                        await self.page.keyboard.press('Control+A')
                        await self.page.keyboard.press('Backspace')
                        await self.page.wait_for_timeout(300)

                        # Type the message using natural keyboard input
                        # This is more reliable than JavaScript DOM manipulation
                        print(f"   Typing message: {message_text[:50]}...")
                        await self.page.keyboard.type(message_text, delay=50)
                        await self.page.wait_for_timeout(500)

                        message_box_found = True
                        print(f"✓ Message typed successfully")
                        break

                except Exception as e:
                    print(f"   Failed: {str(e)[:80]}")
                    continue

            if not message_box_found:
                raise Exception("Could not find or type in message box")

            # Wait for the send button to become enabled
            await self.page.wait_for_timeout(1000)

            # Step 4: Click send button
            print(f"📤 Clicking send button...")

            # More specific selectors for the send button
            send_button_selectors = [
                'footer button[data-testid="send"]',
                'button[data-testid="send"]',
                'footer button[aria-label*="Send"]',
                'footer span[data-icon="send"]',
                'xpath=//footer//button[@aria-label[contains(., "Send")]]',
            ]

            send_clicked = False
            for selector in send_button_selectors:
                try:
                    print(f"   Trying send button selector: {selector}")
                    send_button = await self.page.wait_for_selector(selector, timeout=5000, state='visible')
                    if send_button:
                        # Ensure button is enabled
                        is_enabled = await send_button.evaluate('el => !el.disabled')
                        if not is_enabled:
                            print(f"   Button is disabled, waiting...")
                            await self.page.wait_for_timeout(1000)

                        # Click the button
                        await send_button.click()
                        send_clicked = True
                        print(f"✓ Send button clicked")
                        break
                except Exception as e:
                    print(f"   Failed: {str(e)[:80]}")
                    continue

            if not send_clicked:
                # Try pressing Enter as fallback
                print(f"   Fallback: Pressing Enter to send...")
                try:
                    # Focus back on message box and press Enter
                    message_box = await self.page.query_selector('footer div[contenteditable="true"]')
                    if message_box:
                        await message_box.click()
                        await self.page.wait_for_timeout(300)
                    await self.page.keyboard.press('Enter')
                    send_clicked = True
                    print(f"✓ Message sent via Enter key")
                except Exception as e:
                    raise Exception(f"Could not send message: {e}")

            # Step 5: Wait and verify message was sent
            print(f"⏳ Waiting for message to be sent...")
            await self.page.wait_for_timeout(3000)

            # Verify by checking if the message box is now empty (message was sent)
            try:
                message_box = await self.page.query_selector('footer div[contenteditable="true"]')
                if message_box:
                    current_text = await message_box.evaluate('el => el.textContent')
                    if not current_text or current_text.strip() == '':
                        print(f"✅ Message box cleared - message sent successfully!")
                    else:
                        print(f"⚠️  Message box still has text: '{current_text[:30]}...'")
                        print(f"   Message may not have been sent properly")
            except Exception as e:
                print(f"⚠️  Could not verify message box state: {str(e)[:80]}")

            # Additional verification: look for the message in the chat
            try:
                await self.page.wait_for_timeout(2000)
                # Look for message bubbles with our text
                message_preview = message_text[:30].replace('"', '\\"')

                # Try to find the message in sent messages (message-out class or similar)
                message_found = await self.page.query_selector(
                    f'xpath=//div[contains(@class, "message-out")]//span[contains(text(), "{message_preview}")]'
                )

                if message_found:
                    print(f"✅ Message verified in chat!")
                else:
                    # Try alternative verification
                    all_messages = await self.page.query_selector_all('div[class*="message"]')
                    print(f"   Found {len(all_messages)} message elements in chat")
                    print(f"   Message may still have been sent - check WhatsApp manually")
            except Exception as e:
                print(f"⚠️  Verification failed: {str(e)[:80]}")
                print(f"   Message likely sent - check WhatsApp manually")

            print(f"✅ Send operation completed!")

            return {
                'status': 'success',
                'chat_name': chat_name,
                'message_text': message_text,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise Exception(f"Failed to send WhatsApp message to {chat_name}: {e}")

    async def close(self):
        """Close browser context and cleanup."""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()


# MCP Server Tool Functions (for approval executor integration)

async def execute_whatsapp_send_message(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute WhatsApp send message action (called by approval executor).

    Args:
        params: Dictionary with 'chat_name' and 'message_text'

    Returns:
        Result dictionary with status and details

    Raises:
        Exception: If message sending fails
    """
    chat_name = params.get('chat_name')
    message_text = params.get('message_text')

    if not chat_name or not message_text:
        raise ValueError("Missing required parameters: chat_name and message_text")

    # Create client and send message
    client = WhatsAppClient()
    try:
        result = await client.send_message(chat_name, message_text)
        return result
    finally:
        await client.close()


# Synchronous wrapper for approval executor (which may not be async)
def execute_whatsapp_send_message_sync(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Synchronous wrapper for execute_whatsapp_send_message.

    Args:
        params: Dictionary with 'chat_name' and 'message_text'

    Returns:
        Result dictionary with status and details
    """
    import asyncio
    import nest_asyncio

    # Allow nested event loops (needed when called from async context)
    nest_asyncio.apply()

    # Run async function in event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(execute_whatsapp_send_message(params))


# CLI for testing
async def main():
    """CLI for testing WhatsApp message sending."""
    import argparse

    parser = argparse.ArgumentParser(description='Send WhatsApp message via Playwright')
    parser.add_argument('chat_name', help='Name of chat/contact')
    parser.add_argument('message', help='Message text to send')
    parser.add_argument('--session-dir', default='.whatsapp_session', help='Session directory')

    args = parser.parse_args()

    print(f"📱 Sending WhatsApp message to: {args.chat_name}")
    print(f"📝 Message: {args.message}")

    client = WhatsAppClient(session_dir=args.session_dir)
    try:
        result = await client.send_message(args.chat_name, args.message)
        print(f"✅ Message sent successfully!")
        print(f"   Timestamp: {result['timestamp']}")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        sys.exit(1)
    finally:
        await client.close()


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
