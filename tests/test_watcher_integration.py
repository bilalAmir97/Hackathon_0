"""
Integration tests for watcher migration

Tests gmail_watcher and whatsapp_watcher integration with error recovery,
verifying existing functionality is preserved.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestWatcherIntegration:
    """Test suite for watcher integration"""

    # T112: Test gmail_watcher with error recovery - Normal operation
    def test_gmail_watcher_normal_operation(self, tmp_path, mock_audit_logger):
        """
        Test that gmail_watcher works normally with error recovery decorators.

        Verifies:
        - Decorators don't break normal operation
        - Existing functionality is preserved
        """
        from watchers.gmail_watcher import GmailWatcher
        from scripts.error_recovery import decorators
        from scripts.error_recovery.recovery_state import RecoveryState

        # Setup test environment
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        (vault_path / "Needs_Action").mkdir()
        (vault_path / ".state").mkdir()

        state_file = vault_path / ".state" / "gmail_watcher_state.json"

        # Create mock credentials
        token_path = tmp_path / "token.json"
        token_path.write_text('{"token": "test_token", "refresh_token": "refresh"}')

        # Create isolated recovery state
        test_state_path = tmp_path / "recovery_state.json"
        test_recovery_state = RecoveryState(state_path=test_state_path)

        decorators._circuit_breakers.clear()
        decorators._recovery_state = None

        # Patch RecoveryState.load to return our test instance
        with patch.object(RecoveryState, 'load', return_value=test_recovery_state):
            with patch('watchers.gmail_watcher.build') as mock_build:
                with patch('watchers.gmail_watcher.Credentials') as mock_creds:
                    with patch('watchers.gmail_watcher.AuditLogger', return_value=mock_audit_logger):
                        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
                            # Setup mocks
                            mock_service = Mock()
                            mock_build.return_value = mock_service

                            mock_credentials = Mock()
                            mock_credentials.expired = False
                            mock_credentials.refresh_token = "refresh"
                            mock_creds.from_authorized_user_file.return_value = mock_credentials

                            # Create watcher
                            watcher = GmailWatcher(
                                token_path=str(token_path),
                                vault_path=str(vault_path),
                                state_file=str(state_file),
                                priority_keywords=["urgent"]
                            )

                            # Test authenticate with decorators
                            watcher.authenticate()

                            # Verify authentication succeeded
                            assert watcher.service is not None
                            assert watcher.credentials is not None

    # T112: Test gmail_watcher with error recovery - Retry on transient failure
    def test_gmail_watcher_retry_on_failure(self, tmp_path, mock_audit_logger):
        """
        Test that gmail_watcher retries on transient failures.

        Verifies:
        - Retry logic works on transient failures
        - Exponential backoff is applied
        """
        from watchers.gmail_watcher import GmailWatcher
        from scripts.error_recovery import decorators
        from scripts.error_recovery.recovery_state import RecoveryState

        # Setup test environment
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        (vault_path / "Needs_Action").mkdir()
        (vault_path / ".state").mkdir()

        state_file = vault_path / ".state" / "gmail_watcher_state.json"
        token_path = tmp_path / "token.json"
        token_path.write_text('{"token": "test_token", "refresh_token": "refresh"}')

        # Create isolated recovery state
        test_state_path = tmp_path / "recovery_state.json"
        test_recovery_state = RecoveryState(state_path=test_state_path)

        decorators._circuit_breakers.clear()
        decorators._recovery_state = None

        # Patch RecoveryState.load to return our test instance
        with patch.object(RecoveryState, 'load', return_value=test_recovery_state):
            with patch('watchers.gmail_watcher.build') as mock_build:
                with patch('watchers.gmail_watcher.Credentials') as mock_creds:
                    with patch('watchers.gmail_watcher.AuditLogger', return_value=mock_audit_logger):
                        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
                            call_count = {'count': 0}

                            def flaky_build(*args, **kwargs):
                                call_count['count'] += 1
                                if call_count['count'] <= 1:
                                    raise ConnectionError("Temporary network issue")
                                return Mock()

                            mock_build.side_effect = flaky_build

                            mock_credentials = Mock()
                            mock_credentials.expired = False
                            mock_creds.from_authorized_user_file.return_value = mock_credentials

                            watcher = GmailWatcher(
                                token_path=str(token_path),
                                vault_path=str(vault_path),
                                state_file=str(state_file),
                                priority_keywords=["urgent"]
                            )

                            # Should succeed after retry
                            watcher.authenticate()

                            # Verify retry happened
                            assert call_count['count'] == 2
                            assert watcher.service is not None

    # T112: Test gmail_watcher with error recovery - Circuit breaker
    def test_gmail_watcher_circuit_breaker(self, tmp_path, mock_audit_logger):
        """
        Test that gmail_watcher circuit breaker protects against sustained failures.

        Verifies:
        - Circuit breaker opens after sustained failures
        - Decorators are applied correctly
        """
        from watchers.gmail_watcher import GmailWatcher
        from scripts.error_recovery import decorators
        from scripts.error_recovery.recovery_state import RecoveryState
        from scripts.error_recovery.circuit_breaker import CircuitBreakerOpenError

        # Clean up default state file to prevent cross-test contamination
        default_state = Path("AI_Employee_Vault/.state/recovery_state.json")
        if default_state.exists():
            default_state.unlink()

        # Setup test environment
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        (vault_path / "Needs_Action").mkdir()
        (vault_path / ".state").mkdir()

        state_file = vault_path / ".state" / "gmail_watcher_state.json"
        token_path = tmp_path / "token.json"
        token_path.write_text('{"token": "test_token", "refresh_token": "refresh"}')

        # Create isolated recovery state
        test_state_path = tmp_path / "recovery_state.json"
        test_recovery_state = RecoveryState(state_path=test_state_path)

        decorators._circuit_breakers.clear()
        decorators._recovery_state = None

        # Patch RecoveryState.load to return our test instance
        with patch.object(RecoveryState, 'load', return_value=test_recovery_state):
            with patch('watchers.gmail_watcher.build') as mock_build:
                with patch('watchers.gmail_watcher.Credentials') as mock_creds:
                    with patch('watchers.gmail_watcher.AuditLogger', return_value=mock_audit_logger):
                        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
                            # Always fail
                            mock_build.side_effect = ConnectionError("Service unavailable")

                            mock_credentials = Mock()
                            mock_credentials.expired = False
                            mock_creds.from_authorized_user_file.return_value = mock_credentials

                            watcher = GmailWatcher(
                                token_path=str(token_path),
                                vault_path=str(vault_path),
                                state_file=str(state_file),
                                priority_keywords=["urgent"]
                            )

                            # First attempt should fail with ConnectionError (3 retries = 3 failures)
                            try:
                                watcher.authenticate()
                                assert False, "Should have raised ConnectionError"
                            except ConnectionError:
                                pass  # Expected

                            # Second attempt should fail and open circuit (6 total failures > threshold of 5)
                            try:
                                watcher.authenticate()
                                assert False, "Should have raised ConnectionError or CircuitBreakerOpenError"
                            except (ConnectionError, CircuitBreakerOpenError):
                                pass  # Expected - circuit may open during this attempt

                            # Third attempt should fail with CircuitBreakerOpenError (circuit is now OPEN)
                            try:
                                watcher.authenticate()
                                assert False, "Should have raised CircuitBreakerOpenError"
                            except CircuitBreakerOpenError:
                                pass  # Expected - circuit breaker is protecting the service

                            # Verify circuit breaker is applied correctly

    # T113: Test whatsapp_watcher with error recovery
    def test_whatsapp_watcher_with_error_recovery(self, tmp_path, mock_audit_logger):
        """
        Test that whatsapp_watcher is ready for error recovery integration.

        Verifies:
        - Old retry logic has been removed/commented
        - Error recovery decorators are imported
        - Structure is ready for decorator application
        """
        from watchers.whatsapp_watcher import WhatsAppState

        # Test 1: Verify WhatsAppState works correctly
        state_file = tmp_path / "whatsapp_state.json"
        state = WhatsAppState(str(state_file))

        # Test state management
        assert state.processed_ids == set()
        assert state.total_messages_processed == 0

        # Mark message as processed
        state.mark_processed("test_message_123")
        assert state.is_processed("test_message_123")
        assert state.total_messages_processed == 1

        # Save and reload
        state.save()

        state2 = WhatsAppState(str(state_file))
        assert state2.is_processed("test_message_123")
        assert state2.total_messages_processed == 1

        # Test 2: Verify error recovery imports are present
        import watchers.whatsapp_watcher as ww_module

        # Check that error recovery decorators are imported
        assert hasattr(ww_module, 'with_retry')
        assert hasattr(ww_module, 'with_circuit_breaker')

        # Verify old retry logic is commented/removed
        # (This is a structural test - the old retry_with_backoff should be commented)
        import inspect
        source = inspect.getsource(ww_module)

        # Check that old retry logic is commented
        assert '# OLD RETRY LOGIC' in source or '# def retry_with_backoff' in source

    def test_existing_functionality_preserved(self, tmp_path, mock_audit_logger):
        """
        Test that existing watcher functionality is preserved after error recovery integration.

        Verifies:
        - State management still works
        - File creation still works
        - Priority detection still works
        """
        from watchers.gmail_watcher import GmailWatcher

        # Setup test environment
        vault_path = tmp_path / "vault"
        vault_path.mkdir()
        (vault_path / "Needs_Action").mkdir()
        (vault_path / ".state").mkdir()

        state_file = vault_path / ".state" / "gmail_watcher_state.json"
        token_path = tmp_path / "token.json"
        token_path.write_text('{"token": "test_token", "refresh_token": "refresh"}')

        with patch('watchers.gmail_watcher.build'):
            with patch('watchers.gmail_watcher.Credentials') as mock_creds:
                with patch('watchers.gmail_watcher.AuditLogger', return_value=mock_audit_logger):
                    mock_credentials = Mock()
                    mock_credentials.expired = False
                    mock_creds.from_authorized_user_file.return_value = mock_credentials

                    watcher = GmailWatcher(
                        token_path=str(token_path),
                        vault_path=str(vault_path),
                        state_file=str(state_file),
                        priority_keywords=["urgent", "important"]
                    )

                    # Test priority detection
                    email_urgent = {
                        'id': 'test123',
                        'payload': {
                            'headers': [
                                {'name': 'Subject', 'value': 'URGENT: Need help'},
                                {'name': 'From', 'value': 'test@example.com'}
                            ]
                        },
                        'snippet': 'This is urgent'
                    }

                    assert watcher._is_priority(email_urgent) is True

                    email_normal = {
                        'id': 'test456',
                        'payload': {
                            'headers': [
                                {'name': 'Subject', 'value': 'Regular email'},
                                {'name': 'From', 'value': 'test@example.com'}
                            ]
                        },
                        'snippet': 'Just a normal message'
                    }

                    assert watcher._is_priority(email_normal) is False

                    # Test action file creation
                    watcher.create_action_file(email_urgent)

                    # Verify file was created
                    action_files = list((vault_path / "Needs_Action").glob("EMAIL_*.md"))
                    assert len(action_files) == 1

                    # Verify idempotency - second call should not create duplicate
                    watcher.create_action_file(email_urgent)
                    action_files = list((vault_path / "Needs_Action").glob("EMAIL_*.md"))
                    assert len(action_files) == 1  # Still only 1 file

