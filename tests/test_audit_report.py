"""
Test suite for compliance reporting functionality.

Tests cover:
- Generating reports in JSON format
- Generating reports in CSV format
- Verifying 90-day retention policy
- Exporting user data for GDPR compliance
"""

import pytest
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from scripts.audit_logger import AuditLogger
from scripts.audit_report import ComplianceReporter


class TestAuditReport:
    """Test cases for compliance reporting."""

    def test_generate_report_json(self, audit_logger_with_data):
        """Test generating compliance report in JSON format."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        reporter = ComplianceReporter(log_directory=str(log_dir), config_path=str(config_path))

        # Generate report for today
        today = datetime.utcnow().date()
        report = reporter.generate_report(
            start_date=today.isoformat(),
            end_date=today.isoformat(),
            format="json"
        )

        assert report is not None
        assert "metadata" in report
        assert "entries" in report
        assert report["metadata"]["format"] == "json"
        assert len(report["entries"]) > 0

    def test_generate_report_csv(self, audit_logger_with_data, tmp_path):
        """Test generating compliance report in CSV format."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        reporter = ComplianceReporter(log_directory=str(log_dir), config_path=str(config_path))

        # Generate CSV report
        today = datetime.utcnow().date()
        output_file = tmp_path / "report.csv"

        reporter.generate_report(
            start_date=today.isoformat(),
            end_date=today.isoformat(),
            format="csv",
            output_file=str(output_file)
        )

        # Verify CSV file was created and has content
        assert output_file.exists()

        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0
            # Check required columns
            assert "id" in rows[0]
            assert "timestamp" in rows[0]
            assert "action_type" in rows[0]

    def test_verify_retention(self, audit_logger_with_old_logs):
        """Test verifying 90-day retention policy."""
        audit_logger, log_dir, config_path = audit_logger_with_old_logs

        reporter = ComplianceReporter(log_directory=str(log_dir), config_path=str(config_path))

        # Verify retention policy
        retention_report = reporter.verify_retention(retention_days=90)

        assert retention_report is not None
        assert "total_files" in retention_report
        assert "files_within_retention" in retention_report
        assert "files_beyond_retention" in retention_report
        assert "compliance_status" in retention_report

        # Should identify old logs beyond retention
        if retention_report["files_beyond_retention"] > 0:
            assert retention_report["compliance_status"] == "action_required"

    def test_export_user_data(self, audit_logger_with_user_data):
        """Test exporting all data for a specific user (GDPR compliance)."""
        audit_logger, log_dir, config_path, user_email = audit_logger_with_user_data

        reporter = ComplianceReporter(log_directory=str(log_dir), config_path=str(config_path))

        # Export all data related to the user
        user_data = reporter.export_user_data(user_identifier=user_email)

        assert user_data is not None
        assert "user_identifier" in user_data
        assert user_data["user_identifier"] == user_email
        assert "entries" in user_data
        assert len(user_data["entries"]) > 0

        # All entries should reference the user
        for entry in user_data["entries"]:
            entry_str = json.dumps(entry)
            assert user_email in entry_str

    def test_generate_report_markdown(self, audit_logger_with_data, tmp_path):
        """Test generating compliance report in Markdown format."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        reporter = ComplianceReporter(log_directory=str(log_dir), config_path=str(config_path))

        # Generate Markdown report
        today = datetime.utcnow().date()
        output_file = tmp_path / "report.md"

        reporter.generate_report(
            start_date=today.isoformat(),
            end_date=today.isoformat(),
            format="markdown",
            output_file=str(output_file)
        )

        # Verify Markdown file was created
        assert output_file.exists()

        content = output_file.read_text()
        assert "# Compliance Report" in content
        assert "## Summary" in content
        assert "## Log Entries" in content

    def test_soc2_access_logging(self, audit_logger_with_data):
        """Test SOC 2 compliance: all authentication and approval actions are logged."""
        audit_logger, log_dir, config_path = audit_logger_with_data

        # Log authentication and approval actions
        audit_logger.log_action(
            action_type="user_login",
            actor="auth_service",
            target="admin@example.com",
            parameters={"ip_address": "192.168.1.100"},
            result="success"
        )

        audit_logger.log_action(
            action_type="approval_granted",
            actor="admin@example.com",
            target="action_123",
            parameters={"action_type": "email_send"},
            result="success",
            approval={
                "required": True,
                "status": "approved",
                "approver": "admin@example.com"
            }
        )

        audit_logger.flush()

        # Generate SOC 2 report
        reporter = ComplianceReporter(log_directory=str(log_dir), config_path=str(config_path))

        today = datetime.utcnow().date()
        report = reporter.generate_report(
            start_date=today.isoformat(),
            end_date=today.isoformat(),
            format="json"
        )

        # Verify authentication and approval actions are included
        action_types = [e["action_type"] for e in report["entries"]]
        assert "user_login" in action_types
        assert "approval_granted" in action_types

    def test_quarterly_report(self, audit_logger_with_quarterly_data):
        """Test generating quarterly compliance report (Q1 2026)."""
        audit_logger, log_dir, config_path = audit_logger_with_quarterly_data

        reporter = ComplianceReporter(log_directory=str(log_dir), config_path=str(config_path))

        # Generate Q1 2026 report (Jan 1 - Mar 31)
        report = reporter.generate_report(
            start_date="2026-01-01",
            end_date="2026-03-31",
            format="json"
        )

        assert report is not None
        assert len(report["entries"]) > 0

        # Verify all entries are within Q1 2026
        for entry in report["entries"]:
            entry_date = datetime.fromisoformat(entry["timestamp"].replace('Z', '')).date()
            assert entry_date >= datetime(2026, 1, 1).date()
            assert entry_date <= datetime(2026, 3, 31).date()


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
        target="user@example.com",
        parameters={"subject": "Test"},
        result="success"
    )

    logger.log_action(
        action_type="invoice_create",
        actor="odoo_mcp",
        target="customer_123",
        parameters={"amount": 1000.00},
        result="success"
    )

    logger.flush()

    yield logger, log_dir, config_path


@pytest.fixture
def audit_logger_with_old_logs(tmp_path):
    """Fixture that creates logs beyond 90-day retention."""
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

    # Create old log file (100 days ago)
    old_date = datetime.utcnow() - timedelta(days=100)
    old_log_file = log_dir / f"audit_{old_date.strftime('%Y-%m-%d')}.jsonl"

    with open(old_log_file, 'w') as f:
        log_entry = {
            "id": "old-log-123",
            "timestamp": old_date.isoformat() + 'Z',
            "action_type": "old_action",
            "actor": "test",
            "target": "test",
            "parameters": {},
            "result": "success"
        }
        f.write(json.dumps(log_entry) + '\n')

    logger = AuditLogger(config_path=str(config_path))
    yield logger, log_dir, config_path


@pytest.fixture
def audit_logger_with_user_data(tmp_path):
    """Fixture that creates logs with user-specific data."""
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

    user_email = "john.doe@example.com"

    # Create logs related to specific user
    logger.log_action(
        action_type="email_send",
        actor="email_mcp",
        target=user_email,
        parameters={"subject": "Welcome"},
        result="success"
    )

    logger.log_action(
        action_type="user_login",
        actor="auth_service",
        target=user_email,
        parameters={"ip_address": "192.168.1.100"},
        result="success"
    )

    logger.flush()

    yield logger, log_dir, config_path, user_email


@pytest.fixture
def audit_logger_with_quarterly_data(tmp_path):
    """Fixture that creates logs for Q1 2026."""
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

    # Create log files for Q1 2026
    q1_dates = [
        datetime(2026, 1, 15),
        datetime(2026, 2, 15),
        datetime(2026, 3, 15)
    ]

    for date in q1_dates:
        log_file = log_dir / f"audit_{date.strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'w') as f:
            log_entry = {
                "id": f"q1-log-{date.strftime('%Y%m%d')}",
                "timestamp": date.isoformat() + 'Z',
                "action_type": "quarterly_action",
                "actor": "test",
                "target": "test",
                "parameters": {},
                "result": "success"
            }
            f.write(json.dumps(log_entry) + '\n')

    logger = AuditLogger(config_path=str(config_path))
    yield logger, log_dir, config_path
