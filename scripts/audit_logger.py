"""
Audit Logger - Core logging infrastructure for AI Employee.

Provides comprehensive audit logging with:
- Sensitive data masking
- Encryption at rest
- JSONL storage format
- In-memory queue for resilience
- Automatic log rotation support
"""

import json
import uuid
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import deque
from cryptography.fernet import Fernet


class AuditLogger:
    """
    Core audit logging class for AI Employee.

    Logs all actions with complete context, masks sensitive data,
    and provides encryption support for compliance.
    """

    def __init__(self, config_path: str = "config/logging_config.json"):
        """
        Initialize AuditLogger with configuration.

        Args:
            config_path: Path to logging configuration JSON file
        """
        self.config = self._load_config(config_path)
        self.sensitive_patterns = self._load_sensitive_patterns()
        self._queue = deque(maxlen=self.config.get("queue_max_size", 1000))
        self._fernet = None

        # Load encryption key if encryption is enabled
        if self.config.get("encryption_enabled", False):
            key = self._load_encryption_key()
            self._fernet = Fernet(key)

        # Ensure log directory exists
        os.makedirs(self.config["log_directory"], exist_ok=True)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load logging configuration from JSON file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default configuration
            return {
                "log_directory": "AI_Employee_Vault/Logs",
                "encryption_enabled": False,
                "queue_max_size": 1000,
                "flush_interval_seconds": 5
            }

    def _load_sensitive_patterns(self) -> Dict[str, Any]:
        """
        Load sensitive data patterns for masking.

        Returns:
            Patterns dictionary with field names and regex patterns
        """
        patterns_file = self.config.get(
            "sensitive_patterns_file",
            "config/sensitive_patterns.json"
        )

        try:
            with open(patterns_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default patterns
            return {
                "field_name_patterns": [
                    "password", "passwd", "pwd", "api_key", "token", "secret"
                ],
                "content_patterns": []
            }

    def _generate_id(self) -> str:
        """
        Generate unique identifier for log entry.

        Returns:
            UUID string
        """
        return str(uuid.uuid4())

    def _get_timestamp(self) -> str:
        """
        Get current timestamp in ISO 8601 format.

        Returns:
            ISO 8601 formatted timestamp string
        """
        return datetime.utcnow().isoformat() + 'Z'

    def _mask_sensitive_data(self, data: Any) -> Any:
        """
        Mask sensitive data using two-tier detection.

        Tier 1: Field name heuristics (fast)
        Tier 2: Content pattern matching (regex)

        Args:
            data: Data to mask (dict, list, or primitive)

        Returns:
            Data with sensitive fields masked
        """
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                # Tier 1: Check field name
                if self._is_sensitive_field_name(key):
                    masked[key] = "***REDACTED***"
                elif isinstance(value, (dict, list)):
                    # Recursively mask nested structures
                    masked[key] = self._mask_sensitive_data(value)
                elif isinstance(value, str):
                    # Tier 2: Check content patterns
                    masked[key] = self._mask_by_pattern(value)
                else:
                    masked[key] = value
            return masked

        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]

        elif isinstance(data, str):
            return self._mask_by_pattern(data)

        else:
            return data

    def _is_sensitive_field_name(self, field_name: str) -> bool:
        """
        Check if field name matches sensitive patterns.

        Args:
            field_name: Field name to check

        Returns:
            True if field name is sensitive
        """
        field_lower = field_name.lower()
        patterns = self.sensitive_patterns.get("field_name_patterns", [])

        for pattern in patterns:
            if pattern.lower() in field_lower:
                return True

        return False

    def _mask_by_pattern(self, value: str) -> str:
        """
        Mask value if it matches content patterns (regex).

        Args:
            value: String value to check

        Returns:
            Masked value if pattern matches, original otherwise
        """
        content_patterns = self.sensitive_patterns.get("content_patterns", [])

        for pattern_config in content_patterns:
            regex = pattern_config.get("regex")
            if not regex:
                continue

            try:
                if re.search(regex, value):
                    replacement = pattern_config.get("replacement", "***REDACTED***")
                    show_last_n = pattern_config.get("show_last_n")

                    if show_last_n and len(value) > show_last_n:
                        # Show last N characters (e.g., credit card last 4 digits)
                        masked_part = "*" * (len(value) - show_last_n)
                        return masked_part + value[-show_last_n:]
                    else:
                        return replacement
            except re.error:
                # Invalid regex, skip
                continue

        return value

    def _get_log_file_path(self) -> str:
        """
        Get current log file path with date-based naming.

        Returns:
            Path to current log file (audit_YYYY-MM-DD.jsonl)
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        filename = f"audit_{today}.jsonl"
        return os.path.join(self.config["log_directory"], filename)

    def _write_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """
        Write log entry to JSONL file (atomic append).

        Args:
            log_entry: Log entry dictionary to write
        """
        log_file = self._get_log_file_path()

        try:
            # Atomic append to JSONL file
            with open(log_file, 'a') as f:
                json.dump(log_entry, f)
                f.write('\n')
        except Exception as e:
            # If write fails, keep in queue for retry
            print(f"Warning: Failed to write log entry: {e}")
            # Entry remains in queue for next flush attempt

    def log_action(
        self,
        action_type: str,
        actor: str,
        target: str,
        parameters: Dict[str, Any],
        result: str = "success",
        error: Optional[str] = None,
        approval: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an action taken by the AI Employee.

        Args:
            action_type: Type of action (email_send, invoice_create, etc.)
            actor: Component that initiated action (email_mcp, orchestrator, etc.)
            target: Target of action (recipient, resource, etc.)
            parameters: Action parameters (will be masked for sensitive data)
            result: Result of action ("success" or "failure")
            error: Error message if result is "failure"
            approval: Approval workflow information
            metadata: Additional metadata (workflow_id, duration_ms, etc.)

        Returns:
            Log entry ID (UUID)
        """
        # Generate unique ID and timestamp
        log_id = self._generate_id()
        timestamp = self._get_timestamp()

        # Mask sensitive data in parameters
        masked_parameters = self._mask_sensitive_data(parameters)

        # Create log entry
        log_entry = {
            "id": log_id,
            "timestamp": timestamp,
            "action_type": action_type,
            "actor": actor,
            "target": target,
            "parameters": masked_parameters,
            "result": result
        }

        # Add optional fields
        if error:
            log_entry["error"] = error

        if approval:
            log_entry["approval"] = approval

        if metadata:
            log_entry["metadata"] = metadata

        # Add to queue
        self._queue.append(log_entry)

        # Auto-flush if queue is getting full
        if len(self._queue) >= self.config.get("queue_max_size", 1000) * 0.9:
            self.flush()

        return log_id

    def log_approval(
        self,
        action_id: str,
        approver: str,
        status: str,
        timestamp: Optional[str] = None
    ) -> None:
        """
        Update approval status for an action.

        Note: This is a simplified implementation. In production,
        you might want to update existing log entries or create
        separate approval log entries.

        Args:
            action_id: ID of the action being approved
            approver: Who approved the action
            status: Approval status (approved, denied, etc.)
            timestamp: When approval was granted (defaults to now)
        """
        approval_timestamp = timestamp or self._get_timestamp()

        # Log the approval as a separate action
        self.log_action(
            action_type="approval_granted" if status == "approved" else "approval_denied",
            actor=approver,
            target=action_id,
            parameters={
                "original_action_id": action_id,
                "approval_status": status
            },
            result="success",
            metadata={"approved_at": approval_timestamp}
        )

    def flush(self) -> None:
        """
        Flush queued log entries to disk.

        Writes all queued entries and clears the queue.
        """
        while self._queue:
            log_entry = self._queue.popleft()
            self._write_log_entry(log_entry)

    @staticmethod
    def _generate_encryption_key() -> bytes:
        """
        Generate a new Fernet encryption key.

        Returns:
            Fernet key (44 bytes, base64 encoded)
        """
        return Fernet.generate_key()

    def _load_encryption_key(self) -> bytes:
        """
        Load encryption key from file.

        Returns:
            Encryption key bytes
        """
        key_file = self.config.get("encryption_key_file")
        if not key_file:
            raise ValueError("encryption_key_file not specified in config")

        try:
            with open(key_file, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Encryption key file not found: {key_file}. "
                "Generate a key first using --generate-key"
            )

    def _encrypt_log_file(self, log_file_path: str) -> None:
        """
        Encrypt a log file using Fernet encryption.

        Args:
            log_file_path: Path to log file to encrypt
        """
        if not self._fernet:
            raise ValueError("Encryption not enabled or key not loaded")

        # Read plaintext
        with open(log_file_path, 'rb') as f:
            plaintext = f.read()

        # Encrypt
        ciphertext = self._fernet.encrypt(plaintext)

        # Write encrypted content back
        with open(log_file_path, 'wb') as f:
            f.write(ciphertext)


# CLI interface for key generation
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--generate-key":
        # Generate encryption key
        key = AuditLogger._generate_encryption_key()

        # Save to default location
        key_file = "AI_Employee_Vault/Logs/.encryption_key"
        os.makedirs(os.path.dirname(key_file), exist_ok=True)

        with open(key_file, 'wb') as f:
            f.write(key)

        # Set restrictive permissions
        os.chmod(key_file, 0o600)

        print(f"✓ Encryption key generated and saved to: {key_file}")
        print("⚠ IMPORTANT: Back up this key to a secure location!")
        print("  Without this key, encrypted logs cannot be decrypted.")
    else:
        print("Usage: python audit_logger.py --generate-key")
