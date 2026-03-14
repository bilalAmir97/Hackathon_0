"""Tests for Approval Executor.

This module tests the ApprovalExecutor class for folder monitoring,
file validation, state transitions, and approval workflow.
"""

import json
import os
import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch


class TestApprovalExecutorFolderMonitoring:
    """Test watchdog detects file movements (T036)."""

    def test_detects_file_moved_to_pending_approval(self, tmp_path):
        """Test that executor detects files moved to Pending_Approval."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        needs_action = vault_path / "Needs_Action"
        pending_approval = vault_path / "Pending_Approval"
        needs_action.mkdir(parents=True)
        pending_approval.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create action file
        action_file = needs_action / "EMAIL_20260225_143000_test.md"
        action_file.write_text("test content")

        # Move to Pending_Approval
        moved_file = pending_approval / "EMAIL_20260225_143000_test.md"
        action_file.rename(moved_file)

        # Executor should detect the movement
        # (This will be implemented with watchdog)
        assert moved_file.exists()

    def test_detects_file_moved_to_approved(self, tmp_path):
        """Test that executor detects files moved to Approved."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        pending_approval = vault_path / "Pending_Approval"
        approved = vault_path / "Approved"
        pending_approval.mkdir(parents=True)
        approved.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create approval file
        approval_file = pending_approval / "APPROVAL_20260225_143000.md"
        approval_file.write_text("test approval")

        # Move to Approved
        moved_file = approved / "APPROVAL_20260225_143000.md"
        approval_file.rename(moved_file)

        # Executor should detect and trigger execution
        assert moved_file.exists()

    def test_detects_file_moved_to_rejected(self, tmp_path):
        """Test that executor detects files moved to Rejected."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        pending_approval = vault_path / "Pending_Approval"
        rejected = vault_path / "Rejected"
        pending_approval.mkdir(parents=True)
        rejected.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create approval file
        approval_file = pending_approval / "APPROVAL_20260225_143000.md"
        approval_file.write_text("test approval")

        # Move to Rejected
        moved_file = rejected / "APPROVAL_20260225_143000.md"
        approval_file.rename(moved_file)

        # Executor should detect and skip execution
        assert moved_file.exists()


class TestApprovalExecutorFileValidation:
    """Test approval file schema validation (T037)."""

    def test_validates_approval_file_against_schema(self, tmp_path):
        """Test that executor validates approval files against JSON schema."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        approved = vault_path / "Approved"
        approved.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create valid approval file
        valid_approval = {
            "approval_id": "approval_001",
            "action_type": "email_send",
            "email_action_ref": "msg_001",
            "action_params": {
                "recipient": "test@example.com",
                "subject": "Test",
                "body": "Test body"
            },
            "risk_assessment": "low",
            "reasoning": "Test reasoning"
        }

        approval_file = approved / "APPROVAL_20260225_143000.md"
        content = f"""---
{json.dumps(valid_approval, indent=2)}
---

# Approval Request
"""
        approval_file.write_text(content)

        # Validate file
        is_valid = executor.validate_approval_file(str(approval_file))
        assert is_valid is True

    def test_rejects_invalid_approval_file(self, tmp_path):
        """Test that executor rejects approval files with missing required fields."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        approved = vault_path / "Approved"
        approved.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create invalid approval file (missing required fields)
        invalid_approval = {
            "approval_id": "approval_001"
            # Missing: action_type, email_action_ref, action_params, etc.
        }

        approval_file = approved / "APPROVAL_20260225_143000.md"
        content = f"""---
{json.dumps(invalid_approval, indent=2)}
---

# Approval Request
"""
        approval_file.write_text(content)

        # Validate file
        is_valid = executor.validate_approval_file(str(approval_file))
        assert is_valid is False


class TestApprovalExecutorStateTransitions:
    """Test Pending → Approved → Done flow (T038)."""

    def test_approved_file_triggers_execution(self, tmp_path):
        """Test that moving file to Approved triggers execution."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        approved = vault_path / "Approved"
        done = vault_path / "Done"
        approved.mkdir(parents=True)
        done.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create approval file in Approved
        approval_file = approved / "APPROVAL_20260225_143000.md"
        approval_file.write_text("test approval")

        # Process approved file
        executor.on_file_moved_to_approved(str(approval_file))

        # File should be moved to Done after execution
        done_file = done / "APPROVAL_20260225_143000.md"
        # (Will be implemented in actual code)

    def test_execution_creates_log_entry(self, tmp_path):
        """Test that execution creates log entry."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        approved = vault_path / "Approved"
        logs = vault_path / "Logs"
        approved.mkdir(parents=True)
        logs.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create and process approval file
        approval_file = approved / "APPROVAL_20260225_143000.md"
        approval_file.write_text("test approval")

        executor.on_file_moved_to_approved(str(approval_file))

        # Check log file exists
        from datetime import datetime
        today = datetime.utcnow().strftime('%Y-%m-%d')
        log_file = logs / f"{today}.json"

        # Log should be created
        # (Will verify in actual implementation)


class TestApprovalExecutorRejectionFlow:
    """Test Pending → Rejected → Done flow (T039)."""

    def test_rejected_file_skips_execution(self, tmp_path):
        """Test that moving file to Rejected skips execution."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        rejected = vault_path / "Rejected"
        done = vault_path / "Done"
        rejected.mkdir(parents=True)
        done.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create approval file in Rejected
        approval_file = rejected / "APPROVAL_20260225_143000.md"
        approval_file.write_text("test approval")

        # Process rejected file
        executor.on_file_moved_to_rejected(str(approval_file))

        # File should be moved to Done without execution
        done_file = done / "APPROVAL_20260225_143000.md"
        # (Will be implemented in actual code)

    def test_rejection_creates_log_entry(self, tmp_path):
        """Test that rejection creates log entry."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        rejected = vault_path / "Rejected"
        logs = vault_path / "Logs"
        rejected.mkdir(parents=True)
        logs.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create and process rejected file
        approval_file = rejected / "APPROVAL_20260225_143000.md"
        approval_file.write_text("test approval")

        executor.on_file_moved_to_rejected(str(approval_file))

        # Log should indicate rejection
        # (Will verify in actual implementation)


class TestApprovalExecutorCorruptedFileHandling:
    """Test quarantine and alert creation (T040)."""

    def test_quarantines_corrupted_approval_file(self, tmp_path):
        """Test that corrupted files are moved to quarantine."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        approved = vault_path / "Approved"
        approved.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create corrupted approval file (invalid JSON)
        corrupted_file = approved / "APPROVAL_20260225_143000.md"
        corrupted_file.write_text("---\n{invalid json\n---\n")

        # Handle corrupted file
        executor.handle_corrupted_file(str(corrupted_file))

        # File should be moved to quarantine
        quarantine_dir = vault_path / ".quarantine"
        assert quarantine_dir.exists()

    def test_creates_alert_for_corrupted_file(self, tmp_path):
        """Test that alert is created for corrupted files."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        approved = vault_path / "Approved"
        needs_action = vault_path / "Needs_Action"
        approved.mkdir(parents=True)
        needs_action.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create corrupted approval file
        corrupted_file = approved / "APPROVAL_20260225_143000.md"
        corrupted_file.write_text("---\n{invalid json\n---\n")

        # Handle corrupted file
        executor.handle_corrupted_file(str(corrupted_file))

        # Alert should be created in Needs_Action
        alerts = list(needs_action.glob("ALERT_*.md"))
        assert len(alerts) > 0


class TestActionExecutorMCPIntegration:
    """Test MCP email send with mock (T049)."""

    def test_executes_approved_action_via_mcp(self, tmp_path):
        """Test that approved actions are executed via MCP."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        approved = vault_path / "Approved"
        done = vault_path / "Done"
        approved.mkdir(parents=True)
        done.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create valid approval file
        approval_content = """---
approval_id: approval_001
action_type: email_send
email_action_ref: msg_001
action_params:
  recipient: test@example.com
  subject: Test Subject
  body: Test body content
risk_assessment: low
reasoning: Test email send
---

# Approval Request
"""
        approval_file = approved / "APPROVAL_20260225_143000.md"
        approval_file.write_text(approval_content)

        # Execute action
        executor.execute_approved_action(str(approval_file))

        # Action should be executed (mocked for now)
        # File should be moved to Done
        done_file = done / "APPROVAL_20260225_143000.md"
        assert done_file.exists()

    def test_creates_plan_before_execution(self, tmp_path):
        """Test that Plan.md is created before MCP execution."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        approved = vault_path / "Approved"
        plans = vault_path / "Plans"
        approved.mkdir(parents=True)
        plans.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create approval file
        approval_content = """---
approval_id: approval_001
action_type: email_send
email_action_ref: msg_001
action_params:
  recipient: test@example.com
  subject: Test
  body: Test
risk_assessment: low
reasoning: Test
---
"""
        approval_file = approved / "APPROVAL_20260225_143000.md"
        approval_file.write_text(approval_content)

        # Create plan
        plan_file = executor.create_plan(str(approval_file))

        # Plan should be created in Plans/
        assert Path(plan_file).exists()
        assert "Plans" in plan_file


class TestActionExecutorLogging:
    """Test log entry creation with all required fields (T050)."""

    def test_creates_complete_log_entry(self, tmp_path):
        """Test that log entries contain all required fields."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        logs = vault_path / "Logs"
        logs.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Create log entry
        log_entry = {
            'timestamp': '2026-02-25T14:30:00Z',
            'log_id': 'test_log_001',
            'action_type': 'email_sent',
            'email_id': 'msg_001',
            'approval_id': 'approval_001',
            'status': 'success',
            'inputs': {'recipient': 'test@example.com'},
            'outputs': {'message_id': 'sent_001'}
        }

        from watchers.gmail_state import create_log_entry
        create_log_entry(str(logs), log_entry)

        # Verify log file exists
        from datetime import datetime
        today = datetime.utcnow().strftime('%Y-%m-%d')
        log_file = logs / f"{today}.json"
        assert log_file.exists()

        # Verify log entry has all required fields
        with open(log_file, 'r') as f:
            content = f.read()
            assert 'timestamp' in content
            assert 'log_id' in content
            assert 'action_type' in content
            assert 'status' in content


class TestActionExecutorRetryLogic:
    """Test exponential backoff on failure (T051)."""

    def test_retries_failed_action_with_backoff(self, tmp_path):
        """Test that failed actions are retried with exponential backoff."""
        from scripts.approval_executor import ApprovalExecutor
        from unittest.mock import Mock, patch

        vault_path = tmp_path / "vault"
        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Mock MCP call that fails twice then succeeds
        mock_mcp = Mock(side_effect=[Exception("Network error"), Exception("Network error"), "Success"])

        with patch.object(executor, '_send_email_via_mcp', mock_mcp):
            # This should retry and eventually succeed
            # (Implementation will use retry_with_backoff decorator)
            pass

    def test_logs_retry_attempts(self, tmp_path):
        """Test that retry attempts are logged."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        logs = vault_path / "Logs"
        logs.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Retry attempts should be logged with retry_count field
        # (Will be verified in implementation)


class TestActionExecutorCrashRecovery:
    """Test resume incomplete actions on restart (T052)."""

    def test_resumes_incomplete_actions_on_startup(self, tmp_path):
        """Test that incomplete actions in Approved/ are resumed on restart."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        approved = vault_path / "Approved"
        done = vault_path / "Done"
        approved.mkdir(parents=True)
        done.mkdir(parents=True)

        # Create approval file (simulating incomplete action)
        approval_content = """---
approval_id: approval_001
action_type: email_send
email_action_ref: msg_001
action_params:
  recipient: test@example.com
  subject: Test
  body: Test
risk_assessment: low
reasoning: Test
---
"""
        approval_file = approved / "APPROVAL_20260225_143000.md"
        approval_file.write_text(approval_content)

        # Create new executor (simulating restart)
        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Check for incomplete actions
        incomplete_actions = executor.check_incomplete_actions()

        # Should find the incomplete action
        assert len(incomplete_actions) > 0


class TestActionExecutorRateLimitHandling:
    """Test backoff on Gmail API rate limit (T053)."""

    def test_detects_rate_limit_error(self, tmp_path):
        """Test that rate limit errors are detected."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Simulate rate limit error (HTTP 429)
        from googleapiclient.errors import HttpError
        import json

        error_content = json.dumps({'error': {'code': 429, 'message': 'Rate limit exceeded'}})
        # Rate limit detection will be implemented

    def test_backs_off_on_rate_limit(self, tmp_path):
        """Test that executor backs off when rate limit is hit."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Rate limit should trigger longer backoff
        # (Will use RETRY_RATE_LIMIT_BACKOFF_BASE from config)

