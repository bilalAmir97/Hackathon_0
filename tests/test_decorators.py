"""
Unit tests for error recovery decorators

Tests @with_retry and @with_circuit_breaker decorators,
including audit logging integration.
"""

import pytest
from unittest.mock import Mock, patch
from scripts.error_recovery.decorators import with_retry, with_circuit_breaker


class TestDecorators:
    """Test suite for error recovery decorators"""

    # T027: Test @with_retry decorator succeeds on retry
    def test_with_retry_decorator_success_on_retry(self, flaky_service, mock_audit_logger):
        """Test that @with_retry succeeds after transient failures"""
        call_count = {'count': 0}

        @with_retry(max_attempts=5, base_delay=0.01)
        def flaky_operation():
            call_count['count'] += 1
            if call_count['count'] <= 2:
                raise ConnectionError("Temporary failure")
            return "Success"

        # Should succeed after 2 failures
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            result = flaky_operation()

        assert result == "Success"
        assert call_count['count'] == 3  # Failed twice, succeeded on third

    # T028: Test @with_retry exhausts attempts
    def test_with_retry_decorator_exhausts_attempts(self, mock_audit_logger):
        """Test that @with_retry gives up after max_attempts"""
        call_count = {'count': 0}

        @with_retry(max_attempts=3, base_delay=0.01)
        def always_failing_operation():
            call_count['count'] += 1
            raise ConnectionError("Always fails")

        # Should raise after exhausting attempts
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            with pytest.raises(ConnectionError, match="Always fails"):
                always_failing_operation()

        assert call_count['count'] == 3  # Tried 3 times

    # T029: Test @with_retry logs to audit
    def test_with_retry_decorator_logs_to_audit(self, mock_audit_logger):
        """Test that @with_retry logs retry attempts to audit trail"""
        call_count = {'count': 0}

        @with_retry(max_attempts=3, base_delay=0.01)
        def flaky_operation():
            call_count['count'] += 1
            if call_count['count'] <= 1:
                raise ConnectionError("Temporary failure")
            return "Success"

        # Execute with audit logging
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            result = flaky_operation()

        # Verify audit logger was called
        assert mock_audit_logger.log_action.called

        # Should have logged the retry attempt
        calls = mock_audit_logger.log_action.call_args_list
        assert len(calls) >= 1  # At least one retry logged

        # Verify log contains retry information
        first_call = calls[0]
        assert first_call[1]['action_type'] == 'error_recovery_retry'
        assert 'attempt' in first_call[1]['parameters']

    # Additional tests for decorator behavior
    def test_with_retry_preserves_function_metadata(self):
        """Test that @with_retry preserves function name and docstring"""
        @with_retry(max_attempts=3)
        def my_function():
            """My docstring"""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring"

    def test_with_retry_passes_arguments(self):
        """Test that @with_retry passes arguments correctly"""
        @with_retry(max_attempts=3, base_delay=0.01)
        def operation_with_args(x, y, z=10):
            return x + y + z

        result = operation_with_args(1, 2, z=3)
        assert result == 6

    def test_with_retry_does_not_retry_permanent_errors(self, mock_audit_logger):
        """Test that @with_retry does not retry permanent errors"""
        call_count = {'count': 0}

        @with_retry(max_attempts=5, base_delay=0.01)
        def operation_with_permanent_error():
            call_count['count'] += 1
            raise ValueError("Permanent error")

        # Should raise immediately without retries
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            with pytest.raises(ValueError, match="Permanent error"):
                operation_with_permanent_error()

        assert call_count['count'] == 1  # Only tried once

    def test_with_retry_respects_custom_policy(self):
        """Test that @with_retry respects custom retry policy parameters"""
        call_count = {'count': 0}

        @with_retry(max_attempts=2, base_delay=0.01)
        def operation():
            call_count['count'] += 1
            raise ConnectionError("Fail")

        # Should only try 2 times (max_attempts=2)
        with pytest.raises(ConnectionError):
            operation()

        assert call_count['count'] == 2

    # Tests for @with_circuit_breaker (Phase 4)

    # T054: Test @with_circuit_breaker normal operation
    def test_with_circuit_breaker_decorator_normal_operation(self, mock_audit_logger):
        """Test that @with_circuit_breaker allows requests in normal operation"""
        call_count = {'count': 0}

        @with_circuit_breaker(service_name="test_service")
        def normal_operation():
            call_count['count'] += 1
            return "success"

        # Should succeed multiple times
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            result1 = normal_operation()
            result2 = normal_operation()
            result3 = normal_operation()

        assert result1 == "success"
        assert result2 == "success"
        assert result3 == "success"
        assert call_count['count'] == 3

    # T055: Test @with_circuit_breaker opens on failures
    def test_with_circuit_breaker_decorator_opens_on_failures(self, mock_audit_logger):
        """Test that @with_circuit_breaker opens after threshold failures"""
        call_count = {'count': 0}

        @with_circuit_breaker(service_name="test_service")
        def failing_operation():
            call_count['count'] += 1
            raise ConnectionError("Service unavailable")

        # Should fail 5 times and open circuit
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            for i in range(5):
                with pytest.raises(ConnectionError):
                    failing_operation()

        assert call_count['count'] == 5

    # T056: Test @with_circuit_breaker rejects when open
    def test_with_circuit_breaker_decorator_rejects_when_open(self, mock_audit_logger):
        """Test that @with_circuit_breaker rejects requests when circuit is open"""
        from scripts.error_recovery.circuit_breaker import CircuitBreakerOpenError

        call_count = {'count': 0}

        @with_circuit_breaker(service_name="test_service_reject")
        def failing_operation():
            call_count['count'] += 1
            raise ConnectionError("Service unavailable")

        # Open the circuit by causing 5 failures
        with patch('scripts.error_recovery.decorators.audit_logger', mock_audit_logger):
            for i in range(5):
                with pytest.raises(ConnectionError):
                    failing_operation()

            # Verify circuit is now open - next call should be rejected immediately
            with pytest.raises(CircuitBreakerOpenError):
                failing_operation()

        # Should not have called the operation the 6th time (circuit blocked it)
        assert call_count['count'] == 5

    def test_with_circuit_breaker_placeholder(self):
        """Placeholder for circuit breaker tests (Phase 4)"""
        # Circuit breaker tests will be added in Phase 4 (User Story 2)
        pass
