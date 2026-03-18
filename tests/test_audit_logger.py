"""
Test suite for AuditLogger core functionality.

Tests cover:
- log_action() method
- Unique ID generation
- Timestamp validation (ISO 8601 format)
- JSONL file writing
"""

import pytest
import json
import os
import uuid
from datetime import datetime
from pathlib import Path


class TestAuditLogger:
    """Test cases for AuditLogger class."""

    def test_log_action_creates_entry(self, tmp_path, audit_logger):
        """Test that log_action creates a log entry."""
        log_id = audit_logger.log_action(
            action_type="test_action",
            actor="test_actor",
            target="test_target",
            parameters={"key": "value"},
            result="success"
        )

        assert log_id is not None
        assert isinstance(log_id, str)

        # Verify UUID format
        try:
            uuid.UUID(log_id)
        except ValueError:
            pytest.fail("log_id is not a valid UUID")

    def test_unique_ids_generated(self, audit_logger):
        """Test that each log entry gets a unique ID."""
        id1 = audit_logger.log_action(
            action_type="action1",
            actor="actor1",
            target="target1",
            parameters={},
            result="success"
        )

        id2 = audit_logger.log_action(
            action_type="action2",
            actor="actor2",
            target="target2",
            parameters={},
            result="success"
        )

        assert id1 != id2
        assert isinstance(id1, str)
        assert isinstance(id2, str)

    def test_timestamp_iso8601_format(self, audit_logger):
        """Test that timestamps are in ISO 8601 format."""
        audit_logger.log_action(
            action_type="test_action",
            actor="test_actor",
            target="test_target",
            parameters={},
            result="success"
        )

        audit_logger.flush()

        # Read the log file
        log_files = list(Path(audit_logger.config["log_directory"]).glob("audit_*.jsonl"))
        assert len(log_files) > 0

        with open(log_files[0], 'r') as f:
            log_entry = json.loads(f.readline())

        # Verify timestamp format
        timestamp = log_entry["timestamp"]
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Timestamp {timestamp} is not in ISO 8601 format")

    def test_log_entry_structure(self, audit_logger):
        """Test that log entries have required fields."""
        audit_logger.log_action(
            action_type="email_send",
            actor="email_mcp",
            target="user@example.com",
            parameters={"subject": "Test"},
            result="success"
        )

        audit_logger.flush()

        # Read the log file
        log_files = list(Path(audit_logger.config["log_directory"]).glob("audit_*.jsonl"))
        with open(log_files[0], 'r') as f:
            log_entry = json.loads(f.readline())

        # Verify required fields
        required_fields = ["id", "timestamp", "action_type", "actor", "target", "parameters", "result"]
        for field in required_fields:
            assert field in log_entry, f"Missing required field: {field}"

    def test_log_action_with_error(self, audit_logger):
        """Test logging failed actions with error details."""
        log_id = audit_logger.log_action(
            action_type="test_action",
            actor="test_actor",
            target="test_target",
            parameters={},
            result="failure",
            error="Connection timeout"
        )

        audit_logger.flush()

        # Read and verify
        log_files = list(Path(audit_logger.config["log_directory"]).glob("audit_*.jsonl"))
        with open(log_files[0], 'r') as f:
            log_entry = json.loads(f.readline())

        assert log_entry["result"] == "failure"
        assert log_entry["error"] == "Connection timeout"

    def test_log_action_with_metadata(self, audit_logger):
        """Test logging with metadata."""
        log_id = audit_logger.log_action(
            action_type="test_action",
            actor="test_actor",
            target="test_target",
            parameters={},
            result="success",
            metadata={"workflow_id": "wf-123", "duration_ms": 1234}
        )

        audit_logger.flush()

        # Read and verify
        log_files = list(Path(audit_logger.config["log_directory"]).glob("audit_*.jsonl"))
        with open(log_files[0], 'r') as f:
            log_entry = json.loads(f.readline())

        assert "metadata" in log_entry
        assert log_entry["metadata"]["workflow_id"] == "wf-123"
        assert log_entry["metadata"]["duration_ms"] == 1234


@pytest.fixture
def audit_logger(tmp_path):
    """Fixture to create AuditLogger instance with temp directory."""
    # This will be implemented after AuditLogger class is created
    # For now, this is a placeholder
    from scripts.audit_logger import AuditLogger

    # Create temp config
    config_path = tmp_path / "logging_config.json"
    config = {
        "log_directory": str(tmp_path / "logs"),
        "encryption_enabled": False,  # Disable for basic tests
        "queue_max_size": 1000,
        "flush_interval_seconds": 5
    }

    os.makedirs(config["log_directory"], exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    logger = AuditLogger(config_path=str(config_path))
    yield logger

    # Cleanup
    logger.flush()
