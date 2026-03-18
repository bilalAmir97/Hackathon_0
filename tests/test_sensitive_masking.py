"""
Test suite for sensitive data masking functionality.

Tests cover:
- Field name detection (password, api_key, token, etc.)
- Regex pattern matching (AWS keys, credit cards, JWT tokens)
- Masking replacement
- Show last N characters for credit cards
"""

import pytest
import json


class TestSensitiveMasking:
    """Test cases for sensitive data masking."""

    def test_mask_password_field(self, audit_logger):
        """Test that password fields are masked."""
        audit_logger.log_action(
            action_type="auth_login",
            actor="system",
            target="user@example.com",
            parameters={
                "username": "testuser",
                "password": "SuperSecret123!"
            },
            result="success"
        )

        audit_logger.flush()

        # Read and verify
        log_entry = self._read_last_log_entry(audit_logger)
        assert log_entry["parameters"]["password"] == "***REDACTED***"
        assert log_entry["parameters"]["username"] == "testuser"  # Not masked

    def test_mask_api_key_field(self, audit_logger):
        """Test that api_key fields are masked."""
        audit_logger.log_action(
            action_type="api_call",
            actor="email_mcp",
            target="gmail_api",
            parameters={
                "api_key": "FAKE_TEST_KEY_NOT_REAL_1234567890",
                "endpoint": "/send"
            },
            result="success"
        )

        audit_logger.flush()

        log_entry = self._read_last_log_entry(audit_logger)
        assert log_entry["parameters"]["api_key"] == "***REDACTED***"
        assert log_entry["parameters"]["endpoint"] == "/send"

    def test_mask_token_field(self, audit_logger):
        """Test that token fields are masked."""
        audit_logger.log_action(
            action_type="oauth_request",
            actor="system",
            target="oauth_server",
            parameters={
                "access_token": "ya29.a0AfH6SMBx...",
                "refresh_token": "1//0gHZ9K8...",
                "scope": "email profile"
            },
            result="success"
        )

        audit_logger.flush()

        log_entry = self._read_last_log_entry(audit_logger)
        assert log_entry["parameters"]["access_token"] == "***REDACTED***"
        assert log_entry["parameters"]["refresh_token"] == "***REDACTED***"
        assert log_entry["parameters"]["scope"] == "email profile"

    def test_mask_aws_key_pattern(self, audit_logger):
        """Test that AWS access keys are detected and masked by pattern."""
        audit_logger.log_action(
            action_type="aws_request",
            actor="system",
            target="s3",
            parameters={
                "credentials": "AKIAIOSFODNN7EXAMPLE",
                "bucket": "my-bucket"
            },
            result="success"
        )

        audit_logger.flush()

        log_entry = self._read_last_log_entry(audit_logger)
        # Should be masked even though field name is "credentials"
        assert "AKIAIOSFODNN7EXAMPLE" not in str(log_entry["parameters"])
        assert "***REDACTED" in str(log_entry["parameters"]["credentials"])

    def test_mask_credit_card_show_last_4(self, audit_logger):
        """Test that credit card numbers show only last 4 digits."""
        audit_logger.log_action(
            action_type="payment_process",
            actor="payment_mcp",
            target="stripe",
            parameters={
                "card_number": "4532-1234-5678-9010",
                "amount": 100.00
            },
            result="success"
        )

        audit_logger.flush()

        log_entry = self._read_last_log_entry(audit_logger)
        # Should show ****-****-****-9010 or similar
        masked_card = log_entry["parameters"]["card_number"]
        assert "9010" in masked_card
        assert "4532" not in masked_card
        assert "****" in masked_card

    def test_mask_jwt_token_pattern(self, audit_logger):
        """Test that JWT tokens are detected and masked."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

        audit_logger.log_action(
            action_type="api_auth",
            actor="system",
            target="api_server",
            parameters={
                "authorization": jwt,
                "method": "GET"
            },
            result="success"
        )

        audit_logger.flush()

        log_entry = self._read_last_log_entry(audit_logger)
        assert jwt not in str(log_entry["parameters"]["authorization"])
        assert "***REDACTED" in str(log_entry["parameters"]["authorization"])

    def test_mask_multiple_sensitive_fields(self, audit_logger):
        """Test masking when multiple sensitive fields are present."""
        audit_logger.log_action(
            action_type="complex_action",
            actor="system",
            target="multiple_services",
            parameters={
                "username": "testuser",
                "password": "secret123",
                "api_key": "sk_test_abc123",
                "token": "bearer_xyz789",
                "email": "user@example.com"
            },
            result="success"
        )

        audit_logger.flush()

        log_entry = self._read_last_log_entry(audit_logger)
        params = log_entry["parameters"]

        # Sensitive fields should be masked
        assert params["password"] == "***REDACTED***"
        assert params["api_key"] == "***REDACTED***"
        assert params["token"] == "***REDACTED***"

        # Non-sensitive fields should remain
        assert params["username"] == "testuser"
        assert params["email"] == "user@example.com"

    def test_nested_sensitive_data(self, audit_logger):
        """Test masking of sensitive data in nested structures."""
        audit_logger.log_action(
            action_type="nested_action",
            actor="system",
            target="service",
            parameters={
                "user": {
                    "name": "John Doe",
                    "password": "secret",
                    "email": "john@example.com"
                },
                "config": {
                    "api_key": "FAKE_TEST_KEY_NOT_REAL_123"
                }
            },
            result="success"
        )

        audit_logger.flush()

        log_entry = self._read_last_log_entry(audit_logger)

        # Check nested masking
        assert log_entry["parameters"]["user"]["password"] == "***REDACTED***"
        assert log_entry["parameters"]["config"]["api_key"] == "***REDACTED***"
        assert log_entry["parameters"]["user"]["name"] == "John Doe"

    def _read_last_log_entry(self, audit_logger):
        """Helper to read the last log entry from log file."""
        from pathlib import Path

        log_files = sorted(Path(audit_logger.config["log_directory"]).glob("audit_*.jsonl"))
        assert len(log_files) > 0, "No log files found"

        with open(log_files[-1], 'r') as f:
            lines = f.readlines()
            return json.loads(lines[-1])


@pytest.fixture
def audit_logger(tmp_path):
    """Fixture to create AuditLogger instance with temp directory."""
    from scripts.audit_logger import AuditLogger
    import os

    # Create temp config with sensitive patterns
    config_path = tmp_path / "logging_config.json"
    patterns_path = tmp_path / "sensitive_patterns.json"

    config = {
        "log_directory": str(tmp_path / "logs"),
        "encryption_enabled": False,
        "queue_max_size": 1000,
        "flush_interval_seconds": 5,
        "sensitive_patterns_file": str(patterns_path)
    }

    patterns = {
        "field_name_patterns": [
            "password", "passwd", "pwd", "pass",
            "api_key", "apikey", "api-key",
            "token", "access_token", "refresh_token",
            "secret", "client_secret"
        ],
        "content_patterns": [
            {
                "name": "aws_key",
                "regex": "AKIA[0-9A-Z]{16}",
                "replacement": "***REDACTED_AWS_KEY***"
            },
            {
                "name": "credit_card",
                "regex": "\\b(?:\\d{4}[- ]?){3}\\d{4}\\b",
                "replacement": "****-****-****-XXXX",
                "show_last_n": 4
            },
            {
                "name": "jwt_token",
                "regex": "eyJ[A-Za-z0-9-_]+\\.eyJ[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+",
                "replacement": "***REDACTED_JWT***"
            }
        ]
    }

    os.makedirs(config["log_directory"], exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    with open(patterns_path, 'w') as f:
        json.dump(patterns, f)

    logger = AuditLogger(config_path=str(config_path))
    yield logger
    logger.flush()
