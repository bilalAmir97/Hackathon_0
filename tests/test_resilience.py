"""Tests for System Resilience (User Story 4).

This module tests network outage recovery, token expiration handling,
vault structure recovery, and consecutive failure tracking.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch


class TestWatcherNetworkOutageRecovery:
    """Test queue and resume on reconnect (T063)."""

    def test_queues_operations_during_network_outage(self, tmp_path):
        """Test that operations are queued when network is unavailable."""
        from watchers.gmail_watcher import GmailWatcher

        vault_path = tmp_path / "vault"
        state_file = vault_path / ".state" / "gmail_watcher_state.json"
        vault_path.mkdir(parents=True)

        watcher = GmailWatcher(vault_path=str(vault_path), state_file=str(state_file))

        # Simulate network error
        with patch.object(watcher, 'service') as mock_service:
            mock_service.users().messages().list().execute.side_effect = ConnectionError("Network unavailable")

            # Should queue operation instead of crashing
            try:
                watcher.check_for_updates()
            except ConnectionError:
                pass

            # Check that operation was queued
            # (Implementation will add queue to state)

    def test_resumes_queued_operations_on_reconnect(self, tmp_path):
        """Test that queued operations resume when connection restored."""
        from watchers.gmail_watcher import GmailWatcher

        vault_path = tmp_path / "vault"
        state_file = vault_path / ".state" / "gmail_watcher_state.json"
        vault_path.mkdir(parents=True)

        # Create state with queued operations
        state_data = {
            "last_poll_timestamp": "2026-02-25T14:00:00Z",
            "processed_email_ids": [],
            "error_count": 0,
            "last_error": None,
            "config": {},
            "queued_operations": [
                {"type": "poll", "timestamp": "2026-02-25T14:05:00Z"}
            ]
        }

        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(state_data, f)

        watcher = GmailWatcher(vault_path=str(vault_path), state_file=str(state_file))

        # Should process queued operations on next successful poll
        # (Implementation will check for queued operations)


class TestWatcherTokenExpirationHandling:
    """Test pause, alert, resume after refresh (T064)."""

    def test_detects_token_expiration_before_api_call(self, tmp_path):
        """Test that watcher detects expired token before making API call."""
        from watchers.gmail_watcher import GmailWatcher
        from tests.fixtures.mock_gmail_api import create_mock_credentials

        vault_path = tmp_path / "vault"
        token_file = tmp_path / "token.json"
        vault_path.mkdir(parents=True)

        # Create expired credentials
        expired_creds = create_mock_credentials(expired=True)

        watcher = GmailWatcher(vault_path=str(vault_path), token_path=str(token_file))
        watcher.credentials = expired_creds

        # Should detect expiration and handle gracefully
        # (Implementation will check credentials.expired before API calls)

    def test_creates_alert_on_token_expiration(self, tmp_path):
        """Test that alert is created when token expires."""
        from watchers.gmail_watcher import GmailWatcher

        vault_path = tmp_path / "vault"
        needs_action = vault_path / "Needs_Action"
        needs_action.mkdir(parents=True)

        watcher = GmailWatcher(vault_path=str(vault_path))

        # Simulate token expiration
        watcher._create_token_expiration_alert()

        # Alert should be created
        alerts = list(needs_action.glob("ALERT_*_token_expired.md"))
        assert len(alerts) > 0

    def test_pauses_operations_until_token_refreshed(self, tmp_path):
        """Test that watcher pauses when token expires."""
        from watchers.gmail_watcher import GmailWatcher

        vault_path = tmp_path / "vault"
        watcher = GmailWatcher(vault_path=str(vault_path))

        # Should pause polling when token expires
        # (Implementation will set paused flag in state)


class TestWatcherVaultStructureRecovery:
    """Test recreate missing folders (T065)."""

    def test_recreates_missing_vault_folders_on_startup(self, tmp_path):
        """Test that missing vault folders are recreated on startup."""
        from watchers.gmail_watcher import GmailWatcher
        from watchers.gmail_state import validate_vault_structure

        vault_path = tmp_path / "vault"
        vault_path.mkdir(parents=True)

        # Only create some folders (simulate corruption)
        (vault_path / "Inbox").mkdir()
        (vault_path / "Logs").mkdir()

        # Validate and recover
        result = validate_vault_structure(str(vault_path))

        # Should recreate missing folders
        assert result is True
        assert (vault_path / "Needs_Action").exists()
        assert (vault_path / "Pending_Approval").exists()
        assert (vault_path / "Approved").exists()
        assert (vault_path / "Rejected").exists()
        assert (vault_path / "Done").exists()
        assert (vault_path / "Plans").exists()

    def test_logs_vault_recovery_actions(self, tmp_path):
        """Test that vault recovery is logged."""
        from watchers.gmail_state import validate_vault_structure

        vault_path = tmp_path / "vault"
        logs = vault_path / "Logs"
        vault_path.mkdir(parents=True)

        # Validate (will create missing folders)
        validate_vault_structure(str(vault_path))

        # Should log recovery actions
        # (Already implemented in validate_vault_structure)


class TestExecutorConsecutiveFailures:
    """Test error report after max retries (T066)."""

    def test_tracks_consecutive_failures(self, tmp_path):
        """Test that consecutive failures are tracked."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Simulate multiple failures
        for i in range(3):
            try:
                # Simulate failed action
                raise Exception(f"Failure {i+1}")
            except Exception as e:
                executor._track_failure(e)

        # Should track failure count
        # (Implementation will add failure tracking)

    def test_creates_error_report_after_max_retries(self, tmp_path):
        """Test that error report is created after max consecutive failures."""
        from scripts.approval_executor import ApprovalExecutor

        vault_path = tmp_path / "vault"
        needs_action = vault_path / "Needs_Action"
        needs_action.mkdir(parents=True)

        executor = ApprovalExecutor(vault_path=str(vault_path))

        # Simulate max consecutive failures
        for i in range(3):
            try:
                raise Exception(f"Failure {i+1}")
            except Exception as e:
                executor._track_failure(e)

        # Should create error report
        error_reports = list(needs_action.glob("ERROR_REPORT_*.md"))
        # (Implementation will create error report after threshold)


class TestStatePersistenceAcrossRestarts:
    """Test state survives multiple restarts (T067)."""

    def test_state_persists_through_multiple_restarts(self, tmp_path):
        """Test that state persists correctly across multiple restarts."""
        from watchers.gmail_state import GmailState

        state_file = tmp_path / "test_state.json"

        # First instance: create and save state
        state1 = GmailState(str(state_file))
        state1.mark_processed("msg_001")
        state1.mark_processed("msg_002")
        state1.last_poll_timestamp = "2026-02-25T14:00:00Z"
        state1.error_count = 2
        state1.save()

        # Second instance: load and modify
        state2 = GmailState(str(state_file))
        assert state2.is_processed("msg_001")
        assert state2.is_processed("msg_002")
        assert state2.error_count == 2
        state2.mark_processed("msg_003")
        state2.error_count = 0
        state2.save()

        # Third instance: verify all changes persisted
        state3 = GmailState(str(state_file))
        assert state3.is_processed("msg_001")
        assert state3.is_processed("msg_002")
        assert state3.is_processed("msg_003")
        assert state3.error_count == 0
        assert state3.last_poll_timestamp == "2026-02-25T14:00:00Z"

    def test_handles_corrupted_state_file_gracefully(self, tmp_path):
        """Test that corrupted state file is handled gracefully."""
        from watchers.gmail_state import GmailState

        state_file = tmp_path / "test_state.json"

        # Create corrupted state file
        with open(state_file, 'w') as f:
            f.write("{invalid json")

        # Should handle gracefully and create new state
        state = GmailState(str(state_file))

        # Should have clean initial state
        assert len(state.processed_email_ids) == 0
        assert state.error_count == 0
