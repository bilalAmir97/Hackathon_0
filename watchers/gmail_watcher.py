"""Gmail Watcher for monitoring important emails.

This module implements the GmailWatcher class that polls Gmail for important
emails and creates action files in the vault for human review.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from watchers.gmail_state import GmailState, load_config
from scripts.audit_logger import AuditLogger
from scripts.error_recovery.decorators import with_retry, with_circuit_breaker


class GmailWatcher:
    """Watches Gmail inbox for important emails and creates action items.

    Polls Gmail API at configurable intervals, detects priority emails based on
    keywords, and creates structured action files in the vault. Maintains state
    to ensure idempotent operation across restarts.
    """

    def __init__(
        self,
        token_path: str = None,
        credentials_path: str = None,
        vault_path: str = None,
        state_file: str = None,
        priority_keywords: List[str] = None
    ):
        """Initialize Gmail watcher.

        Args:
            token_path: Path to OAuth token file (default: from config)
            credentials_path: Path to credentials file (default: from config)
            vault_path: Path to vault directory (default: from config)
            state_file: Path to state file (default: vault/.state/gmail_watcher_state.json)
            priority_keywords: List of priority keywords (default: from config)
        """
        # Load configuration
        config = load_config()

        self.token_path = token_path or config['gmail_token_path']
        self.credentials_path = credentials_path or config['gmail_credentials_path']
        self.vault_path = Path(vault_path or config['vault_path'])

        # Initialize state management
        if state_file is None:
            state_file = str(self.vault_path / '.state' / 'gmail_watcher_state.json')
        self.state = GmailState(state_file)

        # Priority keywords
        self.priority_keywords = priority_keywords or config['priority_keywords']
        self.priority_keywords = [kw.strip().lower() for kw in self.priority_keywords]

        # OAuth credentials
        self.credentials: Optional[Credentials] = None
        self.service = None

        # Initialize audit logger
        self.audit_logger = AuditLogger()

    @with_retry(max_attempts=3, base_delay=2.0)
    @with_circuit_breaker(service_name='gmail_api')
    def authenticate(self):
        """Authenticate with Gmail API using OAuth token.

        Loads token from file and refreshes if expired. Raises error if
        token file is missing.

        Raises:
            FileNotFoundError: If token file doesn't exist
        """
        token_path = Path(self.token_path)

        if not token_path.exists():
            raise FileNotFoundError(f"OAuth token not found at: {self.token_path}")

        # Load credentials from token file
        self.credentials = Credentials.from_authorized_user_file(
            str(token_path),
            scopes=['https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.send']
        )

        # Refresh token if expired
        if self.credentials.expired and self.credentials.refresh_token:
            self.credentials.refresh(Request())

            # Save refreshed token
            with open(token_path, 'w') as token_file:
                token_file.write(self.credentials.to_json())

        # Build Gmail service
        self.service = build('gmail', 'v1', credentials=self.credentials)

        # Log successful authentication
        self.audit_logger.log_action(
            action_type="watcher_authenticate",
            actor="gmail_watcher",
            target="gmail_api",
            parameters={"service": "gmail"},
            result="success"
        )

    def _is_priority(self, email: Dict[str, Any]) -> bool:
        """Check if email contains priority keywords.

        Searches both subject and body for priority keywords using case-insensitive
        whole word matching.

        Args:
            email: Email message dictionary from Gmail API

        Returns:
            True if email contains any priority keyword, False otherwise
        """
        # Extract subject and body
        subject = ""
        body = ""

        if 'payload' in email and 'headers' in email['payload']:
            for header in email['payload']['headers']:
                if header['name'] == 'Subject':
                    subject = header['value']
                    break

        # Get snippet as body preview
        if 'snippet' in email:
            body = email['snippet']

        # Combine subject and body for searching
        search_text = f"{subject} {body}".lower()

        # Check for priority keywords (whole word matching)
        for keyword in self.priority_keywords:
            # Use word boundary regex for whole word matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, search_text):
                return True

        return False

    def _sanitize_email_address(self, email_addr: str) -> str:
        """Sanitize email address for use in filename.

        Args:
            email_addr: Email address to sanitize

        Returns:
            Sanitized string safe for filenames
        """
        # Extract email from "Name <email@example.com>" format
        match = re.search(r'<(.+?)>', email_addr)
        if match:
            email_addr = match.group(1)

        # Replace special characters
        sanitized = email_addr.replace('@', '_at_')
        sanitized = sanitized.replace('.', '_')
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', sanitized)

        # Truncate to 30 characters
        return sanitized[:30]

    def create_action_file(self, email: Dict[str, Any]):
        """Create action file for email in Needs_Action folder.

        Checks if email has already been processed to prevent duplicates.
        Creates markdown file with email metadata.

        Args:
            email: Email message dictionary from Gmail API
        """
        email_id = email['id']

        # Check if already processed (idempotency)
        if self.state.is_processed(email_id):
            return

        # Extract email metadata
        from_addr = ""
        subject = ""
        date_str = ""

        if 'payload' in email and 'headers' in email['payload']:
            for header in email['payload']['headers']:
                if header['name'] == 'From':
                    from_addr = header['value']
                elif header['name'] == 'Subject':
                    subject = header['value']
                elif header['name'] == 'Date':
                    date_str = header['value']

        snippet = email.get('snippet', '')
        thread_id = email.get('threadId', email_id)

        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        sanitized_from = self._sanitize_email_address(from_addr)
        filename = f"EMAIL_{timestamp}_{sanitized_from}.md"

        # Create action file
        needs_action_dir = self.vault_path / 'Needs_Action'
        needs_action_dir.mkdir(parents=True, exist_ok=True)

        action_file_path = needs_action_dir / filename

        # Handle filename collisions
        counter = 2
        while action_file_path.exists():
            filename = f"EMAIL_{timestamp}_{sanitized_from}_{counter}.md"
            action_file_path = needs_action_dir / filename
            counter += 1

        # Write action file content
        content = f"""---
email_id: {email_id}
thread_id: {thread_id}
from: {from_addr}
subject: {subject}
snippet: {snippet}
date: {date_str}
created_at: {datetime.utcnow().isoformat()}Z
status: pending
---

# Email Action Item

**From:** {from_addr}
**Subject:** {subject}
**Date:** {date_str}

## Preview

{snippet}

## Suggested Actions

- [ ] Review email content
- [ ] Draft response if needed
- [ ] Move to Pending_Approval if action required

## Notes

(Add your notes here)
"""

        with open(action_file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Mark as processed
        self.state.mark_processed(email_id)

        # Log action file creation
        self.audit_logger.log_action(
            action_type="email_receive",
            actor="gmail_watcher",
            target=from_addr,
            parameters={
                "subject": subject,
                "email_id": email_id,
                "action_file": filename
            },
            result="success",
            metadata={"thread_id": thread_id}
        )

        print(f"✅ Created action item: {filename}")

    @with_retry(max_attempts=5, base_delay=1.0)
    @with_circuit_breaker(service_name='gmail_api')
    def check_for_updates(self):
        """Poll Gmail for new unread emails.

        Fetches unread emails from Gmail API, filters for priority emails,
        and creates action files for each important email.

        Returns:
            Number of priority emails detected
        """
        if self.service is None:
            self.authenticate()

        # Check for token expiration before API call
        if self.credentials and self.credentials.expired:
            if self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                    # Save refreshed token
                    with open(self.token_path, 'w') as token_file:
                        token_file.write(self.credentials.to_json())
                except Exception as e:
                    print(f"⚠️ Token refresh failed: {e}")
                    self._create_token_expiration_alert()
                    raise
            else:
                self._create_token_expiration_alert()
                raise Exception("OAuth token expired and cannot be refreshed")

        try:
            # Fetch unread emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=20
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                print("No unread emails found")
                return 0

            priority_count = 0

            for message in messages:
                # Get full message details
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                # Check if priority email
                if self._is_priority(msg):
                    self.create_action_file(msg)
                    priority_count += 1

            # Update last poll timestamp
            self.state.last_poll_timestamp = datetime.utcnow().isoformat() + 'Z'
            self.state.save()

            print(f"📬 Found {len(messages)} unread messages, {priority_count} priority")
            return priority_count

        except (ConnectionError, TimeoutError) as e:
            # Network error - queue operation for later
            print(f"⚠️ Network error: {e}")

            # Log network error
            self.audit_logger.log_action(
                action_type="watcher_poll",
                actor="gmail_watcher",
                target="gmail_api",
                parameters={"operation": "check_updates"},
                result="failure",
                error=f"Network error: {str(e)}"
            )

            operation = {
                'type': 'poll',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            self.state.queue_operation(operation)
            print(f"📋 Operation queued for retry when connection restored")
            raise

        except Exception as e:
            # Log error and increment error count
            self.state.error_count += 1
            self.state.last_error = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            self.state.save()

            # Log error to audit trail
            self.audit_logger.log_action(
                action_type="watcher_poll",
                actor="gmail_watcher",
                target="gmail_api",
                parameters={"operation": "check_updates"},
                result="failure",
                error=f"{type(e).__name__}: {str(e)}",
                metadata={"error_count": self.state.error_count}
            )

            print(f"❌ Error checking for updates: {str(e)}")

            # Create alert if too many consecutive errors
            if self.state.error_count >= 3:
                self._create_error_alert(e)

            raise

    def run(self):
        """Main polling loop.

        Continuously polls Gmail at configured intervals. Handles errors
        gracefully and creates alerts for human intervention when needed.
        """
        import signal

        # Setup graceful shutdown handler
        def signal_handler(signum, frame):
            print("\n⏹️  Received shutdown signal, saving state...")
            self.state.save()
            print("✅ State saved successfully")
            exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        config = load_config()
        check_interval = config.get('gmail_check_interval', 120)

        print("=" * 60)
        print("📧 Gmail Watcher - Silver Tier")
        print("=" * 60)
        print(f"Vault: {self.vault_path}")
        print(f"Check interval: {check_interval} seconds")
        print("=" * 60)

        # Validate vault structure on startup
        from watchers.gmail_state import validate_vault_structure
        if not validate_vault_structure(str(self.vault_path)):
            print("❌ Vault structure validation failed")
            return

        # Authenticate on startup
        try:
            self.authenticate()
            print(f"✅ Authenticated successfully")
        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            self._create_error_alert(e)
            return

        # Process any queued operations from previous network outage
        queued_ops = self.state.get_queued_operations()
        if queued_ops:
            print(f"📋 Found {len(queued_ops)} queued operations, processing...")
            try:
                self.check_for_updates()
                self.state.clear_queued_operations()
                print("✅ Queued operations processed successfully")
            except Exception as e:
                print(f"⚠️ Failed to process queued operations: {e}")

        # Main polling loop
        import time

        while True:
            try:
                self.check_for_updates()

                # Reset error count on successful poll
                if self.state.error_count > 0:
                    self.state.error_count = 0
                    self.state.save()

            except Exception as e:
                print(f"⚠️ Poll failed: {str(e)}")

                # Pause if too many errors
                if self.state.error_count >= 10:
                    print("❌ Too many consecutive errors. Pausing watcher.")
                    self._create_error_alert(Exception("Watcher paused due to repeated failures"))
                    break

            # Wait before next poll
            time.sleep(check_interval)

    def _create_error_alert(self, error: Exception):
        """Create error alert in Needs_Action folder.

        Args:
            error: Exception that occurred
        """
        needs_action_dir = self.vault_path / 'Needs_Action'
        needs_action_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        alert_file = needs_action_dir / f"ALERT_{timestamp}_gmail_watcher.md"

        content = f"""---
alert_type: gmail_watcher_error
created_at: {datetime.utcnow().isoformat()}Z
error_type: {type(error).__name__}
status: needs_attention
---

# Gmail Watcher Alert

**Error Type:** {type(error).__name__}
**Timestamp:** {datetime.utcnow().isoformat()}Z
**Consecutive Errors:** {self.state.error_count}

## Error Details

```
{str(error)}
```

## Recommended Actions

- [ ] Check OAuth token validity (token.json)
- [ ] Verify Gmail API credentials (credentials.json)
- [ ] Check network connectivity
- [ ] Review error logs in Logs/ folder
- [ ] Restart watcher after resolving issue

## Notes

(Add your investigation notes here)
"""

        with open(alert_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"🚨 Created error alert: {alert_file.name}")

    def _create_token_expiration_alert(self):
        """Create alert for expired OAuth token."""
        needs_action_dir = self.vault_path / 'Needs_Action'
        needs_action_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        alert_file = needs_action_dir / f"ALERT_{timestamp}_token_expired.md"

        content = f"""---
alert_type: oauth_token_expired
created_at: {datetime.utcnow().isoformat()}Z
status: needs_attention
---

# OAuth Token Expired

**Timestamp:** {datetime.utcnow().isoformat()}Z

## Issue

The Gmail OAuth token has expired and needs to be refreshed.

## Recommended Actions

- [ ] Run: `python test_gmail_oauth.py` to refresh token
- [ ] Verify credentials.json exists
- [ ] Check token.json permissions
- [ ] Restart watcher after token refresh

## Notes

The watcher has paused operations until the token is refreshed.
"""

        with open(alert_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"🚨 Created token expiration alert: {alert_file.name}")


if __name__ == "__main__":
    """Entry point for running Gmail watcher as a script."""
    watcher = GmailWatcher()
    watcher.run()
