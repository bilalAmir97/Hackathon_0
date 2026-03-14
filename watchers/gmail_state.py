"""Gmail Watcher State Management.

This module provides persistent state tracking for the Gmail watcher to ensure
idempotent operation across restarts. State is stored in JSON format in the vault.
"""

import json
import os
import time
import random
from pathlib import Path
from typing import Set, Dict, Any, Optional
from datetime import datetime


class GmailState:
    """Manages persistent state for Gmail watcher.

    Tracks processed email IDs to prevent duplicate action file creation
    across system restarts. State is persisted to JSON file in vault.
    """

    def __init__(self, state_file_path: str):
        """Initialize Gmail state manager.

        Args:
            state_file_path: Path to state JSON file
        """
        self.state_file_path = Path(state_file_path)
        self.processed_email_ids: Set[str] = set()
        self.last_poll_timestamp: Optional[str] = None
        self.error_count: int = 0
        self.last_error: Optional[Dict[str, Any]] = None
        self.config: Dict[str, Any] = {}
        self.queued_operations: list = []

        # Load existing state if file exists
        self._load()

    def _load(self):
        """Load state from JSON file.

        If file doesn't exist, creates a new state file with default values.
        If file exists, loads the state from it. Handles corrupted files gracefully.
        """
        if self.state_file_path.exists():
            try:
                # Load existing state
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)

                self.processed_email_ids = set(state_data.get('processed_email_ids', []))
                self.last_poll_timestamp = state_data.get('last_poll_timestamp')
                self.error_count = state_data.get('error_count', 0)
                self.last_error = state_data.get('last_error')
                self.config = state_data.get('config', {})
                self.queued_operations = state_data.get('queued_operations', [])

            except (json.JSONDecodeError, ValueError) as e:
                # Handle corrupted state file
                print(f"⚠️ Corrupted state file detected: {e}")
                print(f"   Creating new state file...")

                # Backup corrupted file
                backup_path = self.state_file_path.with_suffix('.json.corrupted')
                if self.state_file_path.exists():
                    import shutil
                    shutil.copy2(self.state_file_path, backup_path)
                    print(f"   Backed up to: {backup_path}")

                # Initialize with clean state
                self.processed_email_ids = set()
                self.last_poll_timestamp = None
                self.error_count = 0
                self.last_error = None
                self.config = {}

                # Save clean state
                self.save()

        else:
            # Create new state file with defaults
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
            self.save()

    def is_processed(self, email_id: str) -> bool:
        """Check if email ID has been processed.

        Args:
            email_id: Gmail message ID

        Returns:
            True if email has been processed, False otherwise
        """
        return email_id in self.processed_email_ids

    def mark_processed(self, email_id: str):
        """Mark email ID as processed and save state.

        Args:
            email_id: Gmail message ID to mark as processed
        """
        self.processed_email_ids.add(email_id)
        self.save()

    def queue_operation(self, operation: Dict[str, Any]):
        """Queue an operation for later execution.

        Args:
            operation: Operation dictionary with type and timestamp
        """
        self.queued_operations.append(operation)
        self.save()

    def get_queued_operations(self) -> list:
        """Get all queued operations.

        Returns:
            List of queued operation dictionaries
        """
        return self.queued_operations.copy()

    def clear_queued_operations(self):
        """Clear all queued operations after successful processing."""
        self.queued_operations = []
        self.save()

    def archive_old_entries(self, max_entries: int = 10000):
        """Archive old processed email IDs to prevent unbounded growth.

        Keeps the most recent max_entries in active state and archives the rest.

        Args:
            max_entries: Maximum number of entries to keep in active state
        """
        if len(self.processed_email_ids) <= max_entries:
            return

        # Convert to list and sort (assuming email IDs are chronological)
        all_ids = sorted(list(self.processed_email_ids))

        # Keep most recent entries
        keep_count = int(max_entries * 0.8)  # Keep 80% of max to avoid frequent archival
        ids_to_keep = set(all_ids[-keep_count:])
        ids_to_archive = set(all_ids[:-keep_count])

        # Create archive file
        archive_dir = self.state_file_path.parent / 'archives'
        archive_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        archive_file = archive_dir / f'processed_emails_{timestamp}.json'

        archive_data = {
            'archived_at': datetime.utcnow().isoformat() + 'Z',
            'count': len(ids_to_archive),
            'email_ids': list(ids_to_archive)
        }

        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, indent=2, ensure_ascii=False)

        # Update active state
        self.processed_email_ids = ids_to_keep

        print(f"📦 Archived {len(ids_to_archive)} old email IDs to: {archive_file.name}")
        print(f"   Kept {len(ids_to_keep)} recent entries in active state")

    def save(self):
        """Save current state to JSON file.

        Persists the current state (processed email IDs, timestamps, errors)
        to the JSON file for recovery across restarts.
        """
        state_data = {
            'last_poll_timestamp': self.last_poll_timestamp,
            'processed_email_ids': list(self.processed_email_ids),
            'error_count': self.error_count,
            'last_error': self.last_error,
            'config': self.config,
            'queued_operations': self.queued_operations
        }

        # Ensure parent directory exists
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write state to file
        with open(self.state_file_path, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)


# Constitution-driven helper functions (T013-T017)

def move_file_atomic(src: str, dst: str):
    """Move file atomically to prevent race conditions.

    Uses os.rename() which is atomic on POSIX systems. For cross-filesystem moves,
    falls back to copy + delete with error handling.

    Args:
        src: Source file path
        dst: Destination file path

    Raises:
        FileNotFoundError: If source file doesn't exist
        PermissionError: If insufficient permissions
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    # Ensure destination directory exists
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Atomic rename (works on same filesystem)
        os.rename(src, dst)
    except OSError:
        # Cross-filesystem move: copy then delete
        import shutil
        shutil.copy2(src, dst)
        os.remove(src)


def create_log_entry(log_dir: str, entry: Dict[str, Any]):
    """Create log entry in JSON Lines format.

    Appends a single JSON object to the daily log file. Each line is a complete
    JSON object, enabling atomic append operations and streaming reads.

    Args:
        log_dir: Directory for log files (e.g., AI_Employee_Vault/Logs)
        entry: Log entry dictionary with required fields:
            - timestamp: ISO 8601 timestamp
            - log_id: Unique identifier (UUID)
            - action_type: Type of action
            - status: success/failure/pending

    Raises:
        ValueError: If required fields are missing
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Validate required fields
    required_fields = ['timestamp', 'log_id', 'action_type', 'status']
    missing_fields = [f for f in required_fields if f not in entry]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    # Get today's log file (YYYY-MM-DD.json)
    today = datetime.utcnow().strftime('%Y-%m-%d')
    log_file = log_path / f"{today}.json"

    # Append JSON line (atomic operation)
    with open(log_file, 'a', encoding='utf-8') as f:
        json.dump(entry, f, ensure_ascii=False)
        f.write('\n')


def load_config(env_file: str = '.env') -> Dict[str, Any]:
    """Load and validate environment configuration.

    Loads configuration from .env file and validates required fields.
    Uses python-dotenv for environment variable loading.

    Args:
        env_file: Path to .env file (default: '.env')

    Returns:
        Configuration dictionary with validated settings

    Raises:
        ValueError: If required configuration is missing or invalid
    """
    from dotenv import load_dotenv

    # Load .env file
    load_dotenv(env_file)

    config = {
        'vault_path': os.getenv('VAULT_PATH', './AI_Employee_Vault'),
        'gmail_credentials_path': os.getenv('GMAIL_CREDENTIALS_PATH', './credentials.json'),
        'gmail_token_path': os.getenv('GMAIL_TOKEN_PATH', './token.json'),
        'gmail_check_interval': int(os.getenv('GMAIL_CHECK_INTERVAL', '120')),
        'priority_keywords': os.getenv('PRIORITY_KEYWORDS', 'urgent,important,asap,invoice,payment,client,deadline,action required').split(','),
        'max_retries': int(os.getenv('MAX_RETRIES', '3')),
        'retry_backoff_base': int(os.getenv('RETRY_BACKOFF_BASE', '2')),
        'retry_jitter_max': float(os.getenv('RETRY_JITTER_MAX', '1.0')),
        'dry_run': os.getenv('DRY_RUN', 'false').lower() == 'true',
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }

    # Validate critical paths exist
    if not Path(config['gmail_credentials_path']).exists():
        raise ValueError(f"Gmail credentials not found at: {config['gmail_credentials_path']}")

    if not Path(config['vault_path']).exists():
        raise ValueError(f"Vault directory not found at: {config['vault_path']}")

    # Validate intervals
    if config['gmail_check_interval'] < 60:
        raise ValueError("GMAIL_CHECK_INTERVAL must be at least 60 seconds")

    return config


def retry_with_backoff(func, max_retries: int = 3):
    """Retry decorator with exponential backoff.

    Implements exponential backoff with jitter for transient error handling.
    Formula: delay = (base ** attempt) + random(0, jitter_max)

    Args:
        func: Function to retry
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        Wrapped function with retry logic

    Example:
        @retry_with_backoff
        def fetch_emails():
            # API call that might fail
            pass
    """
    def wrapper(*args, **kwargs):
        config = load_config()
        base = config.get('retry_backoff_base', 2)
        jitter_max = config.get('retry_jitter_max', 1.0)

        last_exception = None

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if attempt == max_retries - 1:
                    # Last attempt failed, raise the exception
                    raise

                # Calculate delay with exponential backoff and jitter
                delay = (base ** attempt) + random.uniform(0, jitter_max)

                # Log retry attempt
                print(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s delay. Error: {str(e)}")

                time.sleep(delay)

        # Should never reach here, but raise last exception if it does
        if last_exception:
            raise last_exception

    return wrapper


def validate_vault_structure(vault_path: str) -> bool:
    """Validate vault directory structure.

    Checks that all required directories exist in the vault. Creates missing
    directories and logs recovery actions.

    Args:
        vault_path: Path to vault root directory

    Returns:
        True if structure is valid or was successfully repaired, False on error

    Required directories:
        - Inbox/
        - Needs_Action/
        - Pending_Approval/
        - Approved/
        - Rejected/
        - Done/
        - Plans/
        - Logs/
        - .state/
    """
    vault = Path(vault_path)

    if not vault.exists():
        print(f"ERROR: Vault directory does not exist: {vault_path}")
        return False

    required_dirs = [
        'Inbox',
        'Needs_Action',
        'Pending_Approval',
        'Approved',
        'Rejected',
        'Done',
        'Plans',
        'Logs',
        '.state'
    ]

    missing_dirs = []
    for dir_name in required_dirs:
        dir_path = vault / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)

    if missing_dirs:
        print(f"WARNING: Missing vault directories: {', '.join(missing_dirs)}")
        print("Attempting to create missing directories...")

        for dir_name in missing_dirs:
            dir_path = vault / dir_name
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created: {dir_name}/")

                # Log recovery action
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'log_id': f"recovery_{int(time.time())}",
                    'action_type': 'vault_structure_recovery',
                    'status': 'success',
                    'inputs': {'created_directory': dir_name}
                }
                create_log_entry(str(vault / 'Logs'), log_entry)

            except Exception as e:
                print(f"❌ Failed to create {dir_name}/: {str(e)}")
                return False

        print("✅ Vault structure validated and repaired")
        return True

    print("✅ Vault structure is valid")
    return True
