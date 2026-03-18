"""
Integration tests for User Story 2: Sensitive Data Protection.

Tests verify that sensitive information is never stored in plain text:
- API keys are masked
- Credit card numbers show only last 4 digits
- Passwords are completely masked
- Multiple sensitive fields are all masked
"""

import pytest
import json
from pathlib import Path
from scripts.audit_logger import AuditLogger


class TestIntegrationUS2:
    """Integration tests for User Story 2 - Sensitive Data Protection."""

    def test_mask_api_key(self, audit_logger):
        """
        Test that API keys are masked in log entries.

        Acceptance: API key in action → log shows "***REDACTED***"
        """
        # Simulate action with API key
        log_id = audit_logger.log_action(
            action_type="api_call",
            actor="test_service",
            target="external_api",
            parameters={
                "api_key": "FAKE_TEST_KEY_NOT_REAL_1234567890",
                "endpoint": "/v1/users",
                "method": "GET"
            },
            result="success"
        )

        audit_logger.flush()

        # Verify log entry
        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry is not None
        assert log_entry["parameters"]["api_key"] == "***REDACTED***"
        assert log_entry["parameters"]["endpoint"] == "/v1/users"
        assert log_entry["parameters"]["method"] == "GET"

    def test_mask_credit_card(self, audit_logger):
        """
        Test that credit card numbers show only last 4 digits.

        Acceptance: Credit card in payment → log shows only last 4 digits
        """
        # Simulate payment action with credit card
        log_id = audit_logger.log_action(
            action_type="payment_process",
            actor="payment_service",
            target="customer_123",
            parameters={
                "card_number": "4532-1234-5678-9010",
                "amount": 99.99,
                "currency": "USD"
            },
            result="success"
        )

        audit_logger.flush()

        # Verify log entry
        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry is not None
        # Credit card should be masked with last 4 digits visible
        masked_card = log_entry["parameters"]["card_number"]
        assert "9010" in masked_card or masked_card == "***REDACTED***"
        assert "4532" not in masked_card or masked_card == "***REDACTED***"
        assert log_entry["parameters"]["amount"] == 99.99

    def test_mask_password(self, audit_logger):
        """
        Test that passwords are completely masked.

        Acceptance: Password in auth → log shows complete masking
        """
        # Simulate authentication action with password
        log_id = audit_logger.log_action(
            action_type="user_login",
            actor="auth_service",
            target="user@example.com",
            parameters={
                "username": "user@example.com",
                "password": "MySecureP@ssw0rd123!",
                "ip_address": "192.168.1.100"
            },
            result="success"
        )

        audit_logger.flush()

        # Verify log entry
        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry is not None
        assert log_entry["parameters"]["password"] == "***REDACTED***"
        assert log_entry["parameters"]["username"] == "user@example.com"
        assert log_entry["parameters"]["ip_address"] == "192.168.1.100"

    def test_mask_multiple_fields(self, audit_logger):
        """
        Test that multiple sensitive fields are all masked.

        Acceptance: Multiple sensitive fields → all masked, non-sensitive data visible
        """
        # Simulate action with multiple sensitive fields
        log_id = audit_logger.log_action(
            action_type="service_config",
            actor="config_service",
            target="production_env",
            parameters={
                "database_host": "db.example.com",
                "database_password": "db_secret_password_123",
                "api_key": "AKIA1234567890ABCDEF",
                "api_secret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "service_name": "payment_processor",
                "port": 5432,
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
            },
            result="success"
        )

        audit_logger.flush()

        # Verify log entry
        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry is not None

        # Sensitive fields should be masked
        assert log_entry["parameters"]["database_password"] == "***REDACTED***"
        assert log_entry["parameters"]["api_key"] == "***REDACTED***"
        assert log_entry["parameters"]["api_secret"] == "***REDACTED***"
        assert log_entry["parameters"]["token"] == "***REDACTED***"

        # Non-sensitive fields should be visible
        assert log_entry["parameters"]["database_host"] == "db.example.com"
        assert log_entry["parameters"]["service_name"] == "payment_processor"
        assert log_entry["parameters"]["port"] == 5432

    def test_mask_aws_keys(self, audit_logger):
        """Test that AWS access keys are masked."""
        log_id = audit_logger.log_action(
            action_type="aws_config",
            actor="deployment_service",
            target="production",
            parameters={
                "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "region": "us-east-1"
            },
            result="success"
        )

        audit_logger.flush()

        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry is not None
        # AWS keys should be masked (either by field name or pattern)
        assert "AKIAIOSFODNN7EXAMPLE" not in str(log_entry["parameters"])
        assert "wJalrXUtnFEMI" not in str(log_entry["parameters"])
        assert log_entry["parameters"]["region"] == "us-east-1"

    def test_mask_github_token(self, audit_logger):
        """Test that GitHub tokens are masked."""
        log_id = audit_logger.log_action(
            action_type="github_integration",
            actor="ci_service",
            target="repository",
            parameters={
                "github_token": "ghp_1234567890abcdefghijklmnopqrstuvwxyz",
                "repository": "myorg/myrepo",
                "branch": "main"
            },
            result="success"
        )

        audit_logger.flush()

        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry is not None
        # GitHub token should be masked
        assert "ghp_1234567890" not in str(log_entry["parameters"])
        assert log_entry["parameters"]["repository"] == "myorg/myrepo"
        assert log_entry["parameters"]["branch"] == "main"

    def test_mask_nested_sensitive_data(self, audit_logger):
        """Test that sensitive data in nested structures is masked."""
        log_id = audit_logger.log_action(
            action_type="complex_config",
            actor="config_service",
            target="app_config",
            parameters={
                "app_name": "my_app",
                "database": {
                    "host": "db.example.com",
                    "password": "nested_db_password_123",
                    "port": 5432
                },
                "external_services": [
                    {
                        "name": "payment_api",
                        "api_key": "pk_live_abcdefghijklmnop",
                        "endpoint": "https://api.payment.com"
                    },
                    {
                        "name": "email_api",
                        "api_key": "sg_abcdefghijklmnop",
                        "endpoint": "https://api.sendgrid.com"
                    }
                ]
            },
            result="success"
        )

        audit_logger.flush()

        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry is not None

        # Nested password should be masked
        assert log_entry["parameters"]["database"]["password"] == "***REDACTED***"
        assert log_entry["parameters"]["database"]["host"] == "db.example.com"

        # API keys in array should be masked
        assert log_entry["parameters"]["external_services"][0]["api_key"] == "***REDACTED***"
        assert log_entry["parameters"]["external_services"][1]["api_key"] == "***REDACTED***"

        # Non-sensitive nested data should be visible
        assert log_entry["parameters"]["external_services"][0]["name"] == "payment_api"
        assert log_entry["parameters"]["app_name"] == "my_app"

    def _read_log_by_id(self, audit_logger, log_id: str):
        """Helper to find log entry by ID."""
        log_dir = Path(audit_logger.config["log_directory"])
        log_files = sorted(log_dir.glob("audit_*.jsonl"))

        for log_file in log_files:
            with open(log_file, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    if entry["id"] == log_id:
                        return entry

        return None


@pytest.fixture
def audit_logger(tmp_path):
    """Fixture for AuditLogger with temp directory."""
    import os

    config_path = tmp_path / "logging_config.json"
    config = {
        "log_directory": str(tmp_path / "logs"),
        "encryption_enabled": False,
        "queue_max_size": 1000,
        "flush_interval_seconds": 5
    }

    os.makedirs(config["log_directory"], exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    logger = AuditLogger(config_path=str(config_path))
    yield logger
    logger.flush()
