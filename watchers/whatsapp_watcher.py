"""WhatsApp Watcher - Sensor Layer for WhatsApp Web Monitoring.

Monitors WhatsApp Web for priority messages using Playwright browser automation.
Creates structured action files in /Needs_Action for human review.

This is a sensor-only component (no reasoning or action execution) that integrates
with the existing approval workflow pipeline.
"""

import os
import re
import json
import time
import signal
import sys
import functools
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Callable
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.audit_logger import AuditLogger
from scripts.error_recovery.decorators import with_retry, with_circuit_breaker


# Default priority keywords
DEFAULT_PRIORITY_KEYWORDS = [
    "urgent",
    "asap",
    "important",
    "help",
    "invoice",
    "payment",
    "emergency",
    "critical",
    "deadline"
]


# OLD RETRY LOGIC - Replaced by error_recovery.decorators
# Kept commented for rollback if needed
# def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
#     """Decorator for exponential backoff retry logic.
#
#     Retries failed operations with exponential backoff: 1s, 2s, 4s.
#
#     Args:
#         max_retries: Maximum number of retry attempts (default: 3)
#         base_delay: Base delay in seconds (default: 1.0)
#
#     Returns:
#         Decorated function with retry logic
#     """
#     def decorator(func: Callable) -> Callable:
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             for attempt in range(max_retries):
#                 try:
#                     return func(*args, **kwargs)
#                 except Exception as e:
#                     if attempt < max_retries - 1:
#                         delay = base_delay * (2 ** attempt)  # 1s, 2s, 4s
#                         print(f"⚠️  Attempt {attempt + 1} failed: {e}")
#                         print(f"   Retrying in {delay}s...")
#                         time.sleep(delay)
#                     else:
#                         print(f"✗ All {max_retries} attempts failed")
#                         raise
#         return wrapper
#     return decorator


class WhatsAppState:
    """Manages persistent state for WhatsApp watcher.

    Adapted from GmailState pattern - tracks processed message IDs to prevent
    duplicate action file creation across system restarts.
    """

    def __init__(self, state_file_path: str):
        """Initialize WhatsApp state manager.

        Args:
            state_file_path: Path to state JSON file
        """
        self.state_file_path = Path(state_file_path)
        self.processed_ids: Set[str] = set()
        self.last_check: Optional[str] = None
        self.session_status: str = "unknown"
        self.total_messages_processed: int = 0
        self.last_error: Optional[str] = None

        # Load existing state if file exists
        self._load()

    def _load(self):
        """Load state from JSON file.

        If file doesn't exist, creates a new state file with default values.
        If file exists, loads the state from it. Handles corrupted files gracefully.
        """
        if self.state_file_path.exists():
            try:
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)

                self.processed_ids = set(state_data.get('processed_ids', []))
                self.last_check = state_data.get('last_check')
                self.session_status = state_data.get('session_status', 'unknown')
                self.total_messages_processed = state_data.get('total_messages_processed', 0)
                self.last_error = state_data.get('last_error')

            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ Corrupted state file detected: {e}")
                print(f"   Creating new state file...")

                # Backup corrupted file
                backup_path = self.state_file_path.with_suffix('.json.corrupted')
                if self.state_file_path.exists():
                    import shutil
                    shutil.copy2(self.state_file_path, backup_path)
                    print(f"   Backed up to: {backup_path}")

                # Initialize with clean state
                self.processed_ids = set()
                self.last_check = None
                self.session_status = 'unknown'
                self.total_messages_processed = 0
                self.last_error = None

                # Save clean state
                self.save()

        else:
            # Create new state file with defaults
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.save()

    def save(self):
        """Save current state to JSON file."""
        state_data = {
            'processed_ids': list(self.processed_ids),
            'last_check': self.last_check,
            'session_status': self.session_status,
            'total_messages_processed': self.total_messages_processed,
            'last_error': self.last_error
        }

        with open(self.state_file_path, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2)

    def is_processed(self, message_id: str) -> bool:
        """Check if message ID has been processed.

        Args:
            message_id: Composite message ID

        Returns:
            True if message has been processed, False otherwise
        """
        return message_id in self.processed_ids

    def mark_processed(self, message_id: str):
        """Mark message ID as processed and save state.

        Args:
            message_id: Composite message ID to mark as processed
        """
        self.processed_ids.add(message_id)
        self.total_messages_processed += 1
        self.last_check = datetime.utcnow().isoformat() + 'Z'
        self.save()


class WhatsAppWatcher:
    """Watches WhatsApp Web for priority messages and creates action items.

    Polls WhatsApp Web using Playwright, detects priority messages based on
    keywords, and creates structured action files in the vault. Maintains state
    to ensure idempotent operation across restarts.
    """

    def __init__(
        self,
        vault_path: str = None,
        state_file: str = None,
        priority_keywords: List[str] = None,
        check_interval: int = 30,
        dry_run: bool = False
    ):
        """Initialize WhatsApp watcher.

        Args:
            vault_path: Path to vault directory (default: AI_Employee_Vault)
            state_file: Path to state file (default: vault/.state/whatsapp_watcher_state.json)
            priority_keywords: List of priority keywords (default: DEFAULT_PRIORITY_KEYWORDS)
            check_interval: Seconds between checks (default: 30)
            dry_run: If True, log detections but don't create files (default: False)
        """
        # Vault path
        self.vault_path = Path(vault_path or 'AI_Employee_Vault')
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logs_dir = self.vault_path / 'Logs'

        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize state management
        if state_file is None:
            state_file = str(self.vault_path / '.state' / 'whatsapp_watcher_state.json')
        self.state = WhatsAppState(state_file)

        # Priority keywords (case-insensitive)
        self.priority_keywords = priority_keywords or DEFAULT_PRIORITY_KEYWORDS
        self.priority_keywords = [kw.strip().lower() for kw in self.priority_keywords]

        # Configuration
        self.check_interval = check_interval
        self.dry_run = dry_run or os.getenv('DRY_RUN', '').lower() == 'true'

        # Browser session directory
        self.session_dir = Path('.whatsapp_session')

        # Shutdown flag
        self._shutdown_requested = False

        # Initialize audit logger
        self.audit_logger = AuditLogger()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n⏹️  Shutdown signal received ({signum})")
        self._shutdown_requested = True

    def _generate_message_id(self, sender: str, timestamp: str, message_text: str) -> str:
        """Generate composite message ID for deduplication.

        Format: sender_timestamp_preview[:50]

        Args:
            sender: Contact or group name
            timestamp: WhatsApp's displayed timestamp
            message_text: Full message content

        Returns:
            Composite message ID string
        """
        # Truncate message preview to 50 characters
        preview = message_text[:50] if message_text else ""

        # Create composite ID
        message_id = f"{sender}_{timestamp}_{preview}"

        return message_id

    def _sanitize_sender_name(self, sender: str) -> str:
        """Convert sender name to filesystem-safe string.

        Args:
            sender: Contact or group name

        Returns:
            Sanitized string safe for filenames
        """
        if not sender or sender.strip() == "":
            return "unknown"

        # Remove special characters, keep alphanumeric and spaces
        safe = re.sub(r'[^\w\s-]', '', sender)

        # Replace spaces with underscores
        safe = safe.replace(' ', '_')

        # Remove multiple consecutive underscores
        safe = re.sub(r'_+', '_', safe)

        # Lowercase for consistency
        safe = safe.lower().strip('_')

        # Ensure not empty after sanitization
        return safe if safe else "unknown"

    def _is_priority_message(self, message_text: str) -> bool:
        """Check if message contains priority keywords.

        Args:
            message_text: Message content to check

        Returns:
            True if message contains any priority keyword, False otherwise
        """
        if not message_text:
            return False

        text_lower = message_text.lower()
        return any(keyword in text_lower for keyword in self.priority_keywords)

    def _create_log_entry(
        self,
        action_type: str,
        status: str,
        inputs: Dict[str, Any] = None,
        outputs: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a log entry in JSON Lines format.

        Args:
            action_type: Type of action (e.g., "message_detected")
            status: Status (e.g., "success", "error")
            inputs: Input parameters
            outputs: Output results

        Returns:
            Log entry dictionary
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'log_id': f"whatsapp_{int(time.time())}",
            'action_type': action_type,
            'status': status,
            'inputs': inputs or {},
            'outputs': outputs or {}
        }

        return log_entry

    def _write_log(self, log_entry: Dict[str, Any]):
        """Write log entry to daily log file.

        Args:
            log_entry: Log entry dictionary
        """
        # Daily log file
        log_date = datetime.utcnow().strftime('%Y-%m-%d')
        log_file = self.logs_dir / f"{log_date}.json"

        # Append log entry (JSON Lines format)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')

    def _create_action_file(
        self,
        sender: str,
        message_text: str,
        timestamp: str,
        message_id: str
    ) -> Optional[Path]:
        """Create structured action file in /Needs_Action.

        Args:
            sender: Contact or group name
            message_text: Full message content
            timestamp: WhatsApp's displayed timestamp
            message_id: Composite message ID

        Returns:
            Path to created file, or None if dry-run mode
        """
        # Generate filename
        now = datetime.utcnow()
        date_str = now.strftime('%Y%m%d')
        time_str = now.strftime('%H%M%S')
        sanitized_sender = self._sanitize_sender_name(sender)
        filename = f"WHATSAPP_{date_str}_{time_str}_{sanitized_sender}.md"
        filepath = self.needs_action / filename

        # YAML frontmatter
        frontmatter = f"""---
type: whatsapp_message
from: {sender}
received: {now.isoformat()}Z
priority: high
status: pending
original_timestamp: {timestamp}
---

## WhatsApp Message from {sender}

**Received**: {timestamp}

### Message Content

{message_text}

### Suggested Actions

- [ ] Reply to {sender}
- [ ] Forward to relevant party
- [ ] Create task or reminder
- [ ] Archive after processing

### Notes

Priority message detected by WhatsApp watcher.
"""

        if self.dry_run:
            print(f"[DRY-RUN] Would create file: {filename}")
            print(f"[DRY-RUN] Sender: {sender}, Keyword matched in: {message_text[:50]}...")
            return None

        # Write file atomically
        filepath.write_text(frontmatter, encoding='utf-8')

        return filepath

    def _shutdown(self):
        """Perform graceful shutdown."""
        print("⏹️  WhatsApp watcher stopped")
        self.state.save()
        sys.exit(0)

    async def _launch_browser(self):
        """Launch Playwright browser with persistent context.

        Returns:
            Playwright browser context with persistent session

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

        # Launch browser with persistent context for session management
        self.playwright = await async_playwright().start()

        # WhatsApp Web blocks headless mode, must use headed browser
        context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_dir),
            headless=False,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )

        return context

    async def _navigate_to_whatsapp_web(self, page):
        """Navigate to WhatsApp Web and wait for page load.

        Args:
            page: Playwright page object

        Raises:
            Exception: If navigation fails after retries
        """
        whatsapp_url = "https://web.whatsapp.com"

        # Navigate with timeout
        await page.goto(whatsapp_url, wait_until='domcontentloaded', timeout=60000)

        # Wait for WhatsApp Web to load (either QR code or chat list)
        print("⏳ Waiting for WhatsApp Web to load...")
        try:
            # Wait for main app container first
            await page.wait_for_selector('#app', timeout=30000)

            # Then wait for either QR code (canvas) or chat list grid
            # WhatsApp Web now uses role="grid" for the chat list
            await page.wait_for_selector(
                'canvas, div[aria-label="Chat list"][role="grid"]',
                timeout=180000  # 3 minutes for full load
            )
            print("✓ WhatsApp Web loaded")
        except Exception as e:
            print(f"⚠️ Timeout waiting for WhatsApp Web: {e}")
            raise

    async def _wait_for_login(self, page) -> bool:
        """Wait for user to complete QR code login if needed.

        Args:
            page: Playwright page object

        Returns:
            True if logged in, False if session expired

        Raises:
            Exception: If login check fails
        """
        # Check if QR code is present (canvas element indicates QR code)
        qr_code = await page.query_selector('canvas')

        if qr_code:
            print("\n📱 Please scan QR code to log in to WhatsApp Web")
            print("   Waiting for authentication...")

            # Wait for chat pane to appear (indicates successful login)
            try:
                await page.wait_for_selector(
                    '#pane-side, div[role="grid"]',
                    timeout=180000  # 3 minutes
                )
                print("✓ WhatsApp Web logged in")
                self.state.session_status = 'active'
                self.state.save()
                return True
            except Exception:
                print("✗ Login timeout - QR code not scanned")
                self.state.session_status = 'expired'
                self.state.save()
                return False
        else:
            # Already logged in - check for chat pane
            has_chats = await page.query_selector('#pane-side, div[role="grid"]')
            if has_chats:
                print("✓ WhatsApp Web loaded (already logged in)")
                self.state.session_status = 'active'
                self.state.save()
                return True
            else:
                print("⚠️ WhatsApp Web loaded but no chat pane found")
                return False

    async def _scan_unread_chats(self, page) -> List[Dict[str, str]]:
        """Scan WhatsApp Web for unread chats.

        Args:
            page: Playwright page object

        Returns:
            List of unread chat dictionaries with sender, message, timestamp
        """
        unread_chats = []

        try:
            # WhatsApp Web uses role="row" for chat items in a grid layout
            chat_elements = await page.query_selector_all('div[role="row"]')

            if not chat_elements:
                print("⚠️  No chat elements found")
                return unread_chats

            print(f"📋 Found {len(chat_elements)} chat(s)")

            for chat_elem in chat_elements:
                # Check if chat has unread indicator
                # Unread chats have spans with aria-label containing "unread message"
                unread_indicator = await chat_elem.query_selector('span[aria-label*="unread message" i]')

                if not unread_indicator:
                    continue

                # Extract message data
                chat_data = await self._extract_message_data(chat_elem)
                if chat_data:
                    unread_chats.append(chat_data)
                    print(f"  📨 Unread from: {chat_data['sender']}")

        except Exception as e:
            log_entry = self._create_log_entry(
                action_type='scan_error',
                status='error',
                inputs={'error': str(e)},
                outputs={'selector_failed': 'role=row'}
            )
            self._write_log(log_entry)
            print(f"⚠️  Error scanning chats: {e}")

        return unread_chats

    async def _extract_message_data(self, chat_element) -> Optional[Dict[str, str]]:
        """Extract sender, message, and timestamp from chat element.

        Args:
            chat_element: Playwright element representing a chat

        Returns:
            Dictionary with sender, message, timestamp, or None if extraction fails
        """
        try:
            # Get all text content from the chat element
            all_text = await chat_element.inner_text()
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]

            if len(lines) < 2:
                return None

            # First line is usually the chat/sender name
            sender = lines[0]

            # Look for message content - it usually comes after ":" marker
            message = ""
            found_colon = False

            for i, line in enumerate(lines):
                # Skip the sender/chat name line
                if i == 0:
                    continue

                # Skip timestamp lines (format like "7:30 PM" or "11:48 AM")
                if ':' in line and ('AM' in line or 'PM' in line or len(line) < 10):
                    continue

                # Skip unread count (single digit or double digit)
                if line.isdigit() and len(line) <= 3:
                    continue

                # Skip sender indicators in groups (lines starting with ~)
                if line.startswith('~'):
                    continue

                # Skip single colon markers
                if line == ':':
                    found_colon = True
                    continue

                # Skip phone numbers
                if line.startswith('+') and len(line) < 20:
                    continue

                # This should be the actual message content
                # It's usually a longer line (>15 chars) that's not metadata
                if len(line) > 15:
                    message = line
                    break

            message = message.strip()

            # Extract timestamp - usually in a span with title attribute or specific class
            timestamp = ""
            time_elem = await chat_element.query_selector('span[title]')
            if time_elem:
                timestamp = await time_elem.inner_text()
                timestamp = timestamp.strip()

            # If no timestamp found, try alternative selector
            if not timestamp:
                # Look for small text elements (timestamps are usually smaller)
                small_spans = await chat_element.query_selector_all('span')
                for span in small_spans:
                    text = await span.inner_text()
                    text = text.strip()
                    # Check if it looks like a time (contains : or AM/PM)
                    if ':' in text or 'AM' in text or 'PM' in text:
                        timestamp = text
                        break

            if not timestamp:
                # Use current time as fallback
                from datetime import datetime
                timestamp = datetime.now().strftime('%H:%M')

            return {
                'sender': sender,
                'message': message,
                'timestamp': timestamp
            }

        except Exception as e:
            print(f"⚠️  Error extracting message data: {e}")
            return None

    async def check_for_updates(self, page):
        """Scan WhatsApp Web for unread messages.

        Args:
            page: Playwright page object (browser must already be open)

        This method scans for all unread messages:
        1. Scan unread chats
        2. Check for duplicates
        3. Create action files for all unread messages
        4. Mark priority messages with special indicator
        5. Update state
        """
        try:
            # Scan unread chats
            print(f"🔍 Checking WhatsApp Web... ({datetime.utcnow().strftime('%H:%M:%S')})")
            unread_chats = await self._scan_unread_chats(page)

            # Process all unread messages
            processed_count = 0
            priority_count = 0

            for chat in unread_chats:
                sender = chat['sender']
                message = chat['message']
                timestamp = chat['timestamp']

                # Debug: Show extracted message content
                print(f"    Message content: {message[:80]}")

                # Generate message ID
                message_id = self._generate_message_id(sender, timestamp, message)

                # Check if already processed
                if not self.state.is_processed(message_id):
                    # Check if priority message
                    is_priority = self._is_priority_message(message)

                    if is_priority:
                        print(f"🔔 Priority message from {sender}")
                        priority_count += 1
                    else:
                        print(f"📨 New message from {sender}")

                    # Create action file for ALL unread messages
                    action_file = self._create_action_file(sender, message, timestamp, message_id)

                    if action_file:
                        print(f"📝 Created action file: {action_file.name}")

                    # Mark as processed
                    self.state.mark_processed(message_id)

                    # Log detection
                    log_entry = self._create_log_entry(
                        action_type='message_detected',
                        status='success',
                        inputs={'sender': sender, 'timestamp': timestamp, 'is_priority': is_priority},
                        outputs={'action_file': str(action_file) if action_file else 'dry-run'}
                    )
                    self._write_log(log_entry)

                    processed_count += 1

            # Summary
            if processed_count > 0:
                if priority_count > 0:
                    print(f"✅ Processed {processed_count} message(s) ({priority_count} priority)")
                else:
                    print(f"✅ Processed {processed_count} message(s)")
            else:
                print("✓ No new messages")

        except Exception as e:
            print(f"✗ Error during check: {e}")
            log_entry = self._create_log_entry(
                action_type='check_error',
                status='error',
                inputs={'error': str(e)}
            )
            self._write_log(log_entry)

    async def run(self):
        """Main loop - continuously check for updates."""
        print("=" * 60)
        print("📱 WhatsApp Watcher - Silver Tier")
        print("=" * 60)
        print(f"Vault: {self.vault_path}")
        print(f"Session: {self.session_dir}")
        print(f"Keywords: {', '.join(self.priority_keywords)}")
        print(f"Check interval: {self.check_interval}s")
        if self.dry_run:
            print("⚠️  DRY-RUN MODE: No files will be created")
        print("=" * 60)

        context = None
        page = None

        try:
            # Launch browser once
            context = await self._launch_browser()
            page = context.pages[0] if context.pages else await context.new_page()

            # Navigate to WhatsApp Web once
            await self._navigate_to_whatsapp_web(page)

            # Wait for login once
            if not await self._wait_for_login(page):
                # Session expired - create alert
                alert_file = self.needs_action / f"ALERT_WHATSAPP_SESSION_EXPIRED_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
                alert_content = """---
type: alert
priority: high
status: pending
---

## WhatsApp Session Expired

The WhatsApp Web session has expired. Please re-authenticate:

1. Run the watcher: `uv run python watchers/whatsapp_watcher.py`
2. Scan the QR code with your phone
3. Session will persist for ~30 days

**Action Required**: Manual re-authentication needed.
"""
                alert_file.write_text(alert_content, encoding='utf-8')

                log_entry = self._create_log_entry(
                    action_type='session_expired',
                    status='error',
                    outputs={'alert_file': str(alert_file)}
                )
                self._write_log(log_entry)

                if context:
                    await context.close()
                return

            # Main loop - keep browser open and check repeatedly
            while not self._shutdown_requested:
                await self.check_for_updates(page)

                if not self._shutdown_requested:
                    print(f"\n💤 Sleeping for {self.check_interval} seconds...")
                    await asyncio.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n⏹️  Keyboard interrupt received")
        except ImportError as e:
            print(f"✗ {e}")
            print("   Install Playwright: uv run playwright install chromium")
        except Exception as e:
            print(f"✗ Error in main loop: {e}")
            log_entry = self._create_log_entry(
                action_type='run_error',
                status='error',
                inputs={'error': str(e)}
            )
            self._write_log(log_entry)
        finally:
            # Close browser on shutdown
            if context:
                await context.close()
            self._shutdown()


# Entry point for manual execution
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='WhatsApp Watcher - Monitor WhatsApp Web for priority messages')
    parser.add_argument('--vault', default='AI_Employee_Vault', help='Path to vault directory')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--dry-run', action='store_true', help='Log detections without creating files')
    parser.add_argument('--keywords', nargs='+', help='Priority keywords (space-separated)')

    args = parser.parse_args()

    watcher = WhatsAppWatcher(
        vault_path=args.vault,
        check_interval=args.interval,
        dry_run=args.dry_run,
        priority_keywords=args.keywords
    )

    asyncio.run(watcher.run())
