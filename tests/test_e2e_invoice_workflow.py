"""
End-to-end test for complete invoice workflow.

Tests the complete invoice workflow from receipt to recording:
1. Invoice data received (odoo_mcp or email)
2. Action item created (orchestrator)
3. Invoice validated (odoo_mcp)
4. Approval requested (approval_executor)
5. Approval granted (approval_executor)
6. Invoice recorded in Odoo (odoo_mcp)

Verifies all steps are logged with correct workflow_id and traceability.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from scripts.audit_logger import AuditLogger
from scripts.audit_search import AuditSearch


class TestE2EInvoiceWorkflow:
    """End-to-end tests for complete invoice workflow."""

    def test_complete_invoice_workflow(self, audit_logger_with_config):
        """
        Test complete invoice workflow with full audit trail.

        Workflow:
        1. Invoice data received
        2. Action item created
        3. Invoice validated
        4. Approval requested
        5. Approval granted
        6. Invoice recorded in Odoo

        Verify: All actions logged with workflow_id and parent_action_id
        """
        audit_logger, log_dir, config_path = audit_logger_with_config

        workflow_id = "wf-invoice-001"

        # Step 1: Invoice data received
        step1_id = audit_logger.log_action(
            action_type="invoice_receive",
            actor="odoo_mcp",
            target="invoice_inbox",
            parameters={
                "vendor": "Acme Corp",
                "amount": 1500.00,
                "currency": "USD",
                "invoice_number": "INV-2024-001",
                "due_date": "2024-04-15"
            },
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        # Step 2: Action item created
        step2_id = audit_logger.log_action(
            action_type="file_write",
            actor="orchestrator",
            target="Needs_Action/INVOICE_acme_corp.md",
            parameters={
                "content_preview": "Invoice from Acme Corp for $1500.00"
            },
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step1_id
            }
        )

        # Step 3: Invoice validated
        step3_id = audit_logger.log_action(
            action_type="invoice_validate",
            actor="odoo_mcp",
            target="INV-2024-001",
            parameters={
                "vendor": "Acme Corp",
                "amount": 1500.00,
                "validation_checks": ["amount_valid", "vendor_exists", "due_date_valid"]
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
            target="Pending_Approval/APPROVAL_invoice_acme.md",
            parameters={
                "action_type": "invoice_record",
                "risk_assessment": "medium",
                "amount": 1500.00
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
            target="approval-inv-001",
            parameters={
                "approver": "human_admin",
                "action_type": "invoice_record"
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

        # Step 6: Invoice recorded in Odoo
        step6_id = audit_logger.log_action(
            action_type="invoice_record",
            actor="odoo_mcp",
            target="INV-2024-001",
            parameters={
                "vendor": "Acme Corp",
                "amount": 1500.00,
                "odoo_id": "invoice-12345"
            },
            result="success",
            metadata={
                "workflow_id": workflow_id,
                "parent_action_id": step5_id
            }
        )

        audit_logger.flush()

        # Verify workflow traceability
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))
        workflow_entries = searcher.trace_workflow(workflow_id)

        # Verify all 6 steps are logged
        assert len(workflow_entries) == 6

        # Verify workflow order
        assert workflow_entries[0]["action_type"] == "invoice_receive"
        assert workflow_entries[1]["action_type"] == "file_write"
        assert workflow_entries[2]["action_type"] == "invoice_validate"
        assert workflow_entries[3]["action_type"] == "approval_request"
        assert workflow_entries[4]["action_type"] == "approval_granted"
        assert workflow_entries[5]["action_type"] == "invoice_record"

        # Verify parent-child relationships
        assert workflow_entries[1]["metadata"]["parent_action_id"] == step1_id
        assert workflow_entries[2]["metadata"]["parent_action_id"] == step2_id
        assert workflow_entries[3]["metadata"]["parent_action_id"] == step3_id
        assert workflow_entries[4]["metadata"]["parent_action_id"] == step4_id
        assert workflow_entries[5]["metadata"]["parent_action_id"] == step5_id

        # Verify approval information
        assert workflow_entries[4]["approval"]["status"] == "approved"
        assert workflow_entries[4]["approval"]["approver"] == "human_admin"

        # Verify invoice details preserved
        assert workflow_entries[5]["parameters"]["odoo_id"] == "invoice-12345"

    def test_invoice_workflow_with_rejection(self, audit_logger_with_config):
        """Test invoice workflow where approval is denied."""
        audit_logger, log_dir, config_path = audit_logger_with_config

        workflow_id = "wf-invoice-rejected-001"

        # Steps 1-4: Same as above (receive, create, validate, request approval)
        step1_id = audit_logger.log_action(
            action_type="invoice_receive",
            actor="odoo_mcp",
            target="invoice_inbox",
            parameters={
                "vendor": "Suspicious Vendor",
                "amount": 50000.00,
                "invoice_number": "INV-FAKE-001"
            },
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        step2_id = audit_logger.log_action(
            action_type="approval_request",
            actor="orchestrator",
            target="Pending_Approval/APPROVAL_suspicious_invoice.md",
            parameters={
                "action_type": "invoice_record",
                "risk_assessment": "high",
                "amount": 50000.00
            },
            result="success",
            metadata={"workflow_id": workflow_id, "parent_action_id": step1_id}
        )

        # Step 3: Approval denied
        step3_id = audit_logger.log_action(
            action_type="approval_denied",
            actor="approval_executor",
            target="approval-inv-002",
            parameters={
                "approver": "human_admin",
                "reason": "Vendor not in approved list"
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

    def test_invoice_workflow_with_validation_failure(self, audit_logger_with_config):
        """Test invoice workflow with validation failure."""
        audit_logger, log_dir, config_path = audit_logger_with_config

        workflow_id = "wf-invoice-invalid-001"

        # Step 1: Invoice received
        step1_id = audit_logger.log_action(
            action_type="invoice_receive",
            actor="odoo_mcp",
            target="invoice_inbox",
            parameters={
                "vendor": "Unknown Vendor",
                "amount": -100.00,  # Invalid amount
                "invoice_number": "INV-BAD-001"
            },
            result="success",
            metadata={"workflow_id": workflow_id}
        )

        # Step 2: Validation fails
        step2_id = audit_logger.log_action(
            action_type="invoice_validate",
            actor="odoo_mcp",
            target="INV-BAD-001",
            parameters={
                "vendor": "Unknown Vendor",
                "amount": -100.00
            },
            result="failure",
            error="Invalid invoice: negative amount, vendor not found",
            metadata={"workflow_id": workflow_id, "parent_action_id": step1_id}
        )

        audit_logger.flush()

        # Verify failure is logged
        searcher = AuditSearch(log_directory=str(log_dir), config_path=str(config_path))
        workflow_entries = searcher.trace_workflow(workflow_id)

        assert len(workflow_entries) == 2
        assert workflow_entries[1]["result"] == "failure"
        assert "negative amount" in workflow_entries[1]["error"].lower()


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
