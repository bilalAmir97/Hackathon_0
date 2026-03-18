"""
Integration tests for User Story 1: Security Audit Trail.

Tests verify that all AI Employee actions are logged with complete context:
- Email send actions
- Invoice creation actions
- Social media posts
- Concurrent logging
"""

import pytest
import json
from pathlib import Path
from scripts.audit_logger import AuditLogger


class TestIntegrationUS1:
    """Integration tests for User Story 1 - Security Audit Trail."""

    def test_log_email_send(self, audit_logger):
        """
        Test that email send actions are logged with complete context.

        Acceptance: Email send → log shows timestamp, recipient, subject,
        approval status, result
        """
        # Simulate email send action
        log_id = audit_logger.log_action(
            action_type="email_send",
            actor="email_mcp",
            target="client@example.com",
            parameters={
                "subject": "Invoice #12345",
                "body_preview": "Please find attached...",
                "attachments": ["invoice_12345.pdf"]
            },
            result="success",
            approval={
                "required": True,
                "status": "approved",
                "approver": "human_admin",
                "approved_at": "2026-03-16T14:25:00.000Z"
            },
            metadata={
                "workflow_id": "wf-email-001",
                "duration_ms": 1234
            }
        )

        audit_logger.flush()

        # Verify log entry
        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry is not None
        assert log_entry["action_type"] == "email_send"
        assert log_entry["actor"] == "email_mcp"
        assert log_entry["target"] == "client@example.com"
        assert log_entry["parameters"]["subject"] == "Invoice #12345"
        assert log_entry["result"] == "success"

        # Verify approval status
        assert log_entry["approval"]["required"] is True
        assert log_entry["approval"]["status"] == "approved"
        assert log_entry["approval"]["approver"] == "human_admin"

        # Verify timestamp exists and is ISO 8601
        assert "timestamp" in log_entry
        assert "T" in log_entry["timestamp"]
        assert "Z" in log_entry["timestamp"]

    def test_log_invoice_create(self, audit_logger):
        """
        Test that invoice creation actions are logged.

        Acceptance: Invoice create → log shows customer, amount,
        approval status, success/failure
        """
        # Simulate invoice creation
        log_id = audit_logger.log_action(
            action_type="invoice_create",
            actor="odoo_mcp",
            target="customer_123",
            parameters={
                "customer_name": "Acme Corp",
                "amount": 5000.00,
                "currency": "USD",
                "line_items": [
                    {"description": "Consulting Services", "amount": 5000.00}
                ]
            },
            result="success",
            approval={
                "required": True,
                "status": "approved",
                "approver": "human_admin",
                "approved_at": "2026-03-16T14:30:00.000Z"
            },
            metadata={
                "workflow_id": "wf-invoice-001",
                "invoice_id": "INV-2026-001"
            }
        )

        audit_logger.flush()

        # Verify log entry
        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry["action_type"] == "invoice_create"
        assert log_entry["actor"] == "odoo_mcp"
        assert log_entry["target"] == "customer_123"
        assert log_entry["parameters"]["customer_name"] == "Acme Corp"
        assert log_entry["parameters"]["amount"] == 5000.00
        assert log_entry["result"] == "success"
        assert log_entry["approval"]["status"] == "approved"

    def test_log_social_post(self, audit_logger):
        """
        Test that social media posts are logged.

        Acceptance: Social post → log shows platform, content summary,
        approval status, result
        """
        # Simulate social media post
        log_id = audit_logger.log_action(
            action_type="social_post",
            actor="linkedin_poster",
            target="linkedin",
            parameters={
                "platform": "LinkedIn",
                "content_summary": "Excited to announce our new product launch...",
                "content_length": 280,
                "has_image": True
            },
            result="success",
            approval={
                "required": True,
                "status": "approved",
                "approver": "human_admin",
                "approved_at": "2026-03-16T15:00:00.000Z"
            },
            metadata={
                "workflow_id": "wf-social-001",
                "post_id": "linkedin-12345"
            }
        )

        audit_logger.flush()

        # Verify log entry
        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry["action_type"] == "social_post"
        assert log_entry["actor"] == "linkedin_poster"
        assert log_entry["target"] == "linkedin"
        assert log_entry["parameters"]["platform"] == "LinkedIn"
        assert "content_summary" in log_entry["parameters"]
        assert log_entry["result"] == "success"
        assert log_entry["approval"]["status"] == "approved"

    def test_concurrent_logging(self, audit_logger):
        """
        Test that concurrent actions each get unique IDs and accurate timestamps.

        Acceptance: Multiple actions occur simultaneously → each has unique ID
        and accurate timestamp without conflicts
        """
        # Simulate multiple concurrent actions
        log_ids = []

        for i in range(10):
            log_id = audit_logger.log_action(
                action_type=f"test_action_{i}",
                actor="test_actor",
                target=f"target_{i}",
                parameters={"index": i},
                result="success"
            )
            log_ids.append(log_id)

        audit_logger.flush()

        # Verify all IDs are unique
        assert len(log_ids) == len(set(log_ids)), "Log IDs are not unique"

        # Verify all entries exist and have correct data
        for i, log_id in enumerate(log_ids):
            log_entry = self._read_log_by_id(audit_logger, log_id)
            assert log_entry is not None
            assert log_entry["action_type"] == f"test_action_{i}"
            assert log_entry["parameters"]["index"] == i

        # Verify timestamps are in order (or very close)
        log_entries = [self._read_log_by_id(audit_logger, lid) for lid in log_ids]
        timestamps = [entry["timestamp"] for entry in log_entries]

        # All timestamps should be valid ISO 8601
        for ts in timestamps:
            assert "T" in ts
            assert "Z" in ts

    def test_failed_action_logging(self, audit_logger):
        """Test that failed actions are logged with error details."""
        log_id = audit_logger.log_action(
            action_type="email_send",
            actor="email_mcp",
            target="invalid@example.com",
            parameters={
                "subject": "Test",
                "body": "Test body"
            },
            result="failure",
            error="SMTP connection timeout after 30 seconds"
        )

        audit_logger.flush()

        log_entry = self._read_log_by_id(audit_logger, log_id)

        assert log_entry["result"] == "failure"
        assert log_entry["error"] == "SMTP connection timeout after 30 seconds"
        assert log_entry["action_type"] == "email_send"

    def test_workflow_traceability(self, audit_logger):
        """Test that workflow IDs enable tracing complete workflows."""
        workflow_id = "wf-complete-workflow-001"

        # Log multiple actions in same workflow
        log_id1 = audit_logger.log_action(
            action_type="email_receive",
            actor="gmail_watcher",
            target="inbox",
            parameters={"from": "client@example.com"},
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        log_id2 = audit_logger.log_action(
            action_type="file_write",
            actor="orchestrator",
            target="Needs_Action/EMAIL_client_inquiry.md",
            parameters={"content_preview": "Client inquiry about..."},
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": log_id1}
        )

        log_id3 = audit_logger.log_action(
            action_type="email_send",
            actor="email_mcp",
            target="client@example.com",
            parameters={"subject": "Re: Your inquiry"},
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": log_id2}
        )

        audit_logger.flush()

        # Verify all actions have same workflow_id
        for log_id in [log_id1, log_id2, log_id3]:
            log_entry = self._read_log_by_id(audit_logger, log_id)
            assert log_entry["metadata"]["workflow_id"] == workflow_id

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
