"""
End-to-end test for complete email workflow.

Tests the complete email workflow from receipt to response:
1. Email received (gmail_watcher)
2. Action item created (orchestrator)
3. Draft response created (email_mcp)
4. Approval requested (approval_executor)
5. Approval granted (approval_executor)
6. Email sent (email_mcp)

Verifies all steps are logged with correct workflow_id and traceability.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from scripts.audit_logger import AuditLogger
from scripts.audit_search import AuditSearch


class TestE2EEmailWorkflow:
    """End-to-end tests for complete email workflow."""

    def test_complete_email_workflow(self, audit_logger_with_config):
        """
        Test complete email workflow with full audit trail.

        Workflow:
        1. Email received
        2. Action item created
        3. Draft created
        4. Approval requested
        5. Approval granted
        6. Email sent

        Verify: All actions logged with workflow_id and parent_action_id
        """
        audit_logger, log_dir, config_path = audit_logger_with_config

        workflow_id = "wf-email-001"

        # Step 1: Email received
        step1_id = audit_logger.log_action(
            action_type="email_receive",
            actor="gmail_watcher",
            target="inbox",
            parameters={
                "from": "client@example.com",
                "subject": "Project inquiry",
                "message_id": "msg-12345"
            },
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        # Step 2: Action item created
        step2_id = audit_logger.log_action(
            action_type="file_write",
            actor="orchestrator",
            target="Needs_Action/EMAIL_client_inquiry.md",
            parameters={
                "content_preview": "Client inquiry about project timeline"
            },
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step1_id
            }
        )

        # Step 3: Draft created
        step3_id = audit_logger.log_action(
            action_type="email_draft",
            actor="email_mcp",
            target="client@example.com",
            parameters={
                "subject": "Re: Project inquiry",
                "body_preview": "Thank you for your inquiry..."
            },
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step2_id
            }
        )

        # Step 4: Approval requested
        step4_id = audit_logger.log_action(
            action_type="approval_request",
            actor="orchestrator",
            target="Pending_Approval/APPROVAL_email_response.md",
            parameters={
                "action_type": "email_send",
                "risk_assessment": "low"
            },
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step3_id
            }
        )

        # Step 5: Approval granted
        step5_id = audit_logger.log_action(
            action_type="approval_granted",
            actor="approval_executor",
            target="approval-12345",
            parameters={
                "approver": "human_admin",
                "action_type": "email_send"
            },
            result="success",
            approval={
                "required": True,
                "status": "approved",
                "approver": "human_admin",
                "approved_at": datetime.utcnow().isoformat() + 'Z'
            },
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step4_id
            }
        )

        # Step 6: Email sent
        step6_id = audit_logger.log_action(
            action_type="email_send",
            actor="email_mcp",
            target="client@example.com",
            parameters={
                "subject": "Re: Project inquiry",
                "body_preview": "Thank you for your inquiry..."
            },
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step5_id,
                "message_id": "msg-67890"
            }
        )

        audit_logger.flush()

        # Verify workflow traceability
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))
        workflow_entries = searcher.trace_workflow(workflow_id)

        # Verify all 6 steps are logged
        assert len(workflow_entries) == 6

        # Verify workflow order
        assert workflow_entries[0]["action_type"] == "email_receive"
        assert workflow_entries[1]["action_type"] == "file_write"
        assert workflow_entries[2]["action_type"] == "email_draft"
        assert workflow_entries[3]["action_type"] == "approval_request"
        assert workflow_entries[4]["action_type"] == "approval_granted"
        assert workflow_entries[5]["action_type"] == "email_send"

        # Verify parent-child relationships
        assert workflow_entries[1]["metadata"]["parent_action_id"] == step1_id
        assert workflow_entries[2]["metadata"]["parent_action_id"] == step2_id
        assert workflow_entries[3]["metadata"]["parent_action_id"] == step3_id
        assert workflow_entries[4]["metadata"]["parent_action_id"] == step4_id
        assert workflow_entries[5]["metadata"]["parent_action_id"] == step5_id

        # Verify approval information
        assert workflow_entries[4]["approval"]["status"] == "approved"
        assert workflow_entries[4]["approval"]["approver"] == "human_admin"

    def test_email_workflow_with_rejection(self, audit_logger_with_config):
        """Test email workflow where approval is denied."""
        audit_logger, log_dir, config_path = audit_logger_with_config

        workflow_id = "wf-email-rejected-001"

        # Steps 1-4: Same as above (receive, create, draft, request approval)
        step1_id = audit_logger.log_action(
            action_type="email_receive",
            actor="gmail_watcher",
            target="inbox",
            parameters={"from": "spam@example.com"},
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        step2_id = audit_logger.log_action(
            action_type="approval_request",
            actor="orchestrator",
            target="Pending_Approval/APPROVAL_suspicious_email.md",
            parameters={"action_type": "email_send", "risk_assessment": "high"},
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": step1_id}
        )

        # Step 3: Approval denied
        step3_id = audit_logger.log_action(
            action_type="approval_denied",
            actor="approval_executor",
            target="approval-12346",
            parameters={
                "approver": "human_admin",
                "reason": "Suspicious sender"
            },
            result="success",
            approval={
                "required": True,
                "status": "denied",
                "approver": "human_admin",
                "denied_at": datetime.utcnow().isoformat() + 'Z'
            },
            metadata={"workflow_id": workflow_id, "parent_action_id": step2_id}
        )

        audit_logger.flush()

        # Verify workflow
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))
        workflow_entries = searcher.trace_workflow(workflow_id)

        assert len(workflow_entries) == 3
        assert workflow_entries[2]["action_type"] == "approval_denied"
        assert workflow_entries[2]["approval"]["status"] == "denied"

    def test_email_workflow_with_failure(self, audit_logger_with_config):
        """Test email workflow with failure scenario."""
        audit_logger, log_dir, config_path = audit_logger_with_config

        workflow_id = "wf-email-failed-001"

        # Step 1: Email received
        step1_id = audit_logger.log_action(
            action_type="email_receive",
            actor="gmail_watcher",
            target="inbox",
            parameters={"from": "client@example.com"},
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        # Step 2: Email send fails
        step2_id = audit_logger.log_action(
            action_type="email_send",
            actor="email_mcp",
            target="client@example.com",
            parameters={"subject": "Response"},
            result="failure",
            error="SMTP connection timeout",
            metadata={"workflow_id": workflow_id, "parent_action_id": step1_id}
        )

        audit_logger.flush()

        # Verify failure is logged
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))
        workflow_entries = searcher.trace_workflow(workflow_id)

        assert len(workflow_entries) == 2
        assert workflow_entries[1]["result"] == "failure"
        assert "timeout" in workflow_entries[1]["error"].lower()


@pytest.fixture
def audit_logger_with_config(tmp_path):
    """Fixture that creates an AuditLogger with configuration."""
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
    yield logger, log_dir, config_path
    logger.flush()
