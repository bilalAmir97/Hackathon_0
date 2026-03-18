"""
Test suite for audit log search functionality.

Tests cover:
- Searching by action type
- Searching by date range
- Searching by result (success/failure)
- Retrieving specific log entries by ID
- Tracing workflows by workflow_id
"""

import pytest
import json
import gzip
from pathlib import Path
from datetime import datetime, timedelta
from scripts.audit_logger import AuditLogger
from scripts.audit_search import AuditSearch


class TestAuditSearch:
    """Test cases for audit log search functionality."""

    def test_search_by_action_type(self, audit_logger_with_data):
        """Test searching logs by action type."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        # Create search instance
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))

        # Search for email_send actions
        results = searcher.search(action_type="email_send")

        assert len(results) == 2
        assert all(r["action_type"] == "email_send" for r in results)

    def test_search_by_date_range(self, audit_logger_with_data):
        """Test searching logs within a date range."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))

        # Search for today's logs
        today = datetime.utcnow().date()
        results = searcher.search(
            start_date=today.isoformat(),
            end_date=today.isoformat()
        )

        assert len(results) > 0
        # All results should be from today
        for result in results:
            log_date = datetime.fromisoformat(result["timestamp"].replace('Z', '')).date()
            assert log_date == today

    def test_search_by_result(self, audit_logger_with_data):
        """Test searching logs by result status."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))

        # Search for failed actions
        results = searcher.search(result="failure")

        assert len(results) == 1
        assert all(r["result"] == "failure" for r in results)

    def test_search_with_limit(self, audit_logger_with_data):
        """Test limiting search results."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))

        # Search with limit
        results = searcher.search(limit=2)

        assert len(results) == 2

    def test_get_by_id(self, audit_logger_with_data):
        """Test retrieving a specific log entry by ID."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        # Get the first log entry ID
        log_files = sorted(log_dir.glob("audit_*.jsonl"))
        with open(log_files[0], 'r') as f:
            first_entry = json.loads(f.readline())
            entry_id = first_entry["id"]

        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))

        # Retrieve by ID
        result = searcher.get_by_id(entry_id)

        assert result is not None
        assert result["id"] == entry_id

    def test_get_by_id_not_found(self, audit_logger_with_data):
        """Test retrieving a non-existent log entry."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))

        # Try to retrieve non-existent ID
        result = searcher.get_by_id("non-existent-id")

        assert result is None

    def test_trace_workflow(self, audit_logger_with_data):
        """Test tracing a complete workflow by workflow_id."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        # Log multiple actions with same workflow_id
        workflow_id = "wf-test-001"

        log_id1 = audit_logger.log_action(
            action_type="step_1",
            actor="test_actor",
            target="test_target",
            parameters={"step": 1},
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        log_id2 = audit_logger.log_action(
            action_type="step_2",
            actor="test_actor",
            target="test_target",
            parameters={"step": 2},
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": log_id1}
        )

        log_id3 = audit_logger.log_action(
            action_type="step_3",
            actor="test_actor",
            target="test_target",
            parameters={"step": 3},
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": log_id2}
        )

        audit_logger.flush()

        # Trace workflow
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))
        workflow_entries = searcher.trace_workflow(workflow_id)

        assert len(workflow_entries) == 3
        assert all(e["metadata"]["workflow_id"] == workflow_id for e in workflow_entries)
        # Should be in chronological order
        assert workflow_entries[0]["action_type"] == "step_1"
        assert workflow_entries[1]["action_type"] == "step_2"
        assert workflow_entries[2]["action_type"] == "step_3"

    def test_search_compressed_logs(self, audit_logger_with_compressed):
        """Test searching in compressed (.jsonl.gz) log files."""
        audit_logger, log_dir, config_path = audit_logger_with_compressed

        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))

        # Search should work with compressed files
        results = searcher.search(action_type="compressed_action")

        assert len(results) >= 1
        assert results[0]["action_type"] == "compressed_action"

    def test_search_multiple_filters(self, audit_logger_with_data):
        """Test searching with multiple filters combined."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))

        # Search with multiple filters
        today = datetime.utcnow().date()
        results = searcher.search(
            action_type="email_send",
            result="success",
            start_date=today.isoformat(),
            end_date=today.isoformat()
        )

        assert len(results) >= 1
        for result in results:
            assert result["action_type"] == "email_send"
            assert result["result"] == "success"

    def test_search_access_logging(self, audit_logger_with_data):
        """Test that search operations are logged for audit trail."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))

        # Perform a search
        results = searcher.search(action_type="email_send")

        # Check that the search was logged
        # The search should create a log entry with action_type="audit_search"
        search_logs = searcher.search(action_type="audit_search")

        assert len(search_logs) >= 1
        search_log = search_logs[-1]  # Get the most recent
        assert search_log["action_type"] == "audit_search"
        assert "action_type" in search_log["parameters"]["filters"]


@pytest.fixture
def audit_logger_with_data(tmp_path):
    """Fixture that creates an AuditLogger with sample data."""
    import os

    config_path = tmp_path / "logging_config.json"
    log_dir = tmp_path / "logs"
    config = {
        "log_directory": str(log_dir),
        "encryption_enabled": False,
        "queue_max_size": 1000,
        "flush_interval_seconds": 5
    }

    os.makedirs(config["log_directory"], exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    logger = AuditLogger(config_path=str(config_path))

    # Create sample log entries
    logger.log_action(
        action_type="email_send",
        actor="email_mcp",
        target="user1@example.com",
        parameters={"subject": "Test 1"},
        result="success"
    )

    logger.log_action(
        action_type="email_send",
        actor="email_mcp",
        target="user2@example.com",
        parameters={"subject": "Test 2"},
        result="success"
    )

    logger.log_action(
        action_type="invoice_create",
        actor="odoo_mcp",
        target="customer_123",
        parameters={"amount": 1000.00},
        result="success"
    )

    logger.log_action(
        action_type="social_post",
        actor="linkedin_poster",
        target="linkedin",
        parameters={"content": "Test post"},
        result="failure",
        error="API rate limit exceeded"
    )

    logger.flush()

    yield logger, log_dir, config_path


@pytest.fixture
def audit_logger_with_compressed(tmp_path):
    """Fixture that creates compressed log files."""
    import os

    config_path = tmp_path / "logging_config.json"
    log_dir = tmp_path / "logs"
    config = {
        "log_directory": str(log_dir),
        "encryption_enabled": False,
        "queue_max_size": 1000,
        "flush_interval_seconds": 5
    }

    os.makedirs(config["log_directory"], exist_ok=True)

    with open(config_path, 'w') as f:
        json.dump(config, f)

    logger = AuditLogger(config_path=str(config_path))

    # Create a log entry
    logger.log_action(
        action_type="compressed_action",
        actor="test_actor",
        target="test_target",
        parameters={"test": "data"},
        result="success"
    )

    logger.flush()

    # Compress the log file
    log_files = list(log_dir.glob("audit_*.jsonl"))
    for log_file in log_files:
        with open(log_file, 'rb') as f_in:
            with gzip.open(str(log_file) + '.gz', 'wb') as f_out:
                f_out.writelines(f_in)
        # Remove original uncompressed file
        log_file.unlink()

    yield logger, log_dir, config_path
