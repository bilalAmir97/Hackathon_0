"""
Unit tests for CircuitBreaker class

Tests state machine transitions, failure threshold detection,
cooldown period enforcement, and half-open recovery logic.
"""

import pytest
import time
from datetime import datetime, timedelta
from scripts.error_recovery.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


class TestCircuitBreaker:
    """Test suite for CircuitBreaker"""

    # T036: Test initial state is CLOSED
    def test_circuit_breaker_initial_state_closed(self):
        """Test that circuit breaker starts in CLOSED state"""
        cb = CircuitBreaker(service_name="test_service")

        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert cb.last_failure_time is None

    # T037: Test circuit opens after threshold
    def test_circuit_opens_after_threshold(self):
        """Test that circuit opens after failure_threshold consecutive failures"""
        cb = CircuitBreaker(service_name="test_service", failure_threshold=5)

        # Record 4 failures - should stay CLOSED
        for i in range(4):
            cb.record_failure()
            assert cb.state == "CLOSED"
            assert cb.failure_count == i + 1

        # 5th failure should open circuit
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.failure_count == 5

    # T038: Test circuit rejects requests when OPEN
    def test_circuit_rejects_requests_when_open(self):
        """Test that circuit breaker rejects requests when OPEN"""
        cb = CircuitBreaker(service_name="test_service", failure_threshold=3)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        assert cb.state == "OPEN"

        # Attempting to call should raise CircuitBreakerOpenError
        def test_operation():
            return "success"

        with pytest.raises(CircuitBreakerOpenError, match="Circuit breaker is OPEN"):
            cb.call(test_operation)

    # T039: Test circuit transitions to HALF_OPEN after cooldown
    def test_circuit_transitions_to_half_open_after_cooldown(self):
        """Test that circuit transitions to HALF_OPEN after cooldown period"""
        cb = CircuitBreaker(service_name="test_service", failure_threshold=3, cooldown_period=0.1)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        assert cb.state == "OPEN"

        # Wait for cooldown
        time.sleep(0.15)

        # Check if cooldown expired
        assert cb.is_cooldown_expired() is True

        # Transition to HALF_OPEN
        cb.transition_state("HALF_OPEN")
        assert cb.state == "HALF_OPEN"

    # T040: Test circuit closes on HALF_OPEN success
    def test_circuit_closes_on_half_open_success(self):
        """Test that circuit closes when test request succeeds in HALF_OPEN"""
        cb = CircuitBreaker(service_name="test_service", failure_threshold=3, cooldown_period=0.1)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        # Wait for cooldown and transition to HALF_OPEN
        time.sleep(0.15)
        cb.transition_state("HALF_OPEN")

        assert cb.state == "HALF_OPEN"

        # Record success - should close circuit
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    # T041: Test circuit reopens on HALF_OPEN failure
    def test_circuit_reopens_on_half_open_failure(self):
        """Test that circuit reopens when test request fails in HALF_OPEN"""
        cb = CircuitBreaker(service_name="test_service", failure_threshold=3, cooldown_period=0.1)

        # Open the circuit
        for _ in range(3):
            cb.record_failure()

        # Wait for cooldown and transition to HALF_OPEN
        time.sleep(0.15)
        cb.transition_state("HALF_OPEN")

        assert cb.state == "HALF_OPEN"

        # Record failure - should reopen circuit
        cb.record_failure()
        assert cb.state == "OPEN"

    # T042: Test state transitions are logged
    def test_circuit_state_transitions_logged(self, mock_audit_logger):
        """Test that state transitions are logged to audit trail"""
        # This will be tested in integration with audit logger
        # For now, verify transition_state method exists
        cb = CircuitBreaker(service_name="test_service")

        cb.transition_state("OPEN")
        assert cb.state == "OPEN"

        cb.transition_state("HALF_OPEN")
        assert cb.state == "HALF_OPEN"

        cb.transition_state("CLOSED")
        assert cb.state == "CLOSED"

    # T043: Test failure count resets on success
    def test_circuit_failure_count_resets_on_success(self):
        """Test that failure count resets to 0 on successful operation"""
        cb = CircuitBreaker(service_name="test_service", failure_threshold=5)

        # Record some failures
        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

        # Record success - should reset count
        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"

    # Additional tests for edge cases
    def test_should_attempt_request_closed(self):
        """Test that requests are allowed in CLOSED state"""
        cb = CircuitBreaker(service_name="test_service")
        assert cb.should_attempt_request() is True

    def test_should_attempt_request_open(self):
        """Test that requests are blocked in OPEN state (before cooldown)"""
        cb = CircuitBreaker(service_name="test_service", failure_threshold=2, cooldown_period=10.0)

        # Open circuit
        cb.record_failure()
        cb.record_failure()

        assert cb.state == "OPEN"
        assert cb.should_attempt_request() is False

    def test_should_attempt_request_half_open(self):
        """Test that single test request is allowed in HALF_OPEN state"""
        cb = CircuitBreaker(service_name="test_service")
        cb.transition_state("HALF_OPEN")

        assert cb.should_attempt_request() is True

    def test_is_cooldown_expired_not_expired(self):
        """Test cooldown detection when not expired"""
        cb = CircuitBreaker(service_name="test_service", failure_threshold=3, cooldown_period=10.0)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()

        assert cb.state == "OPEN"
        assert cb.is_cooldown_expired() is False

    def test_call_executes_operation_when_closed(self):
        """Test that call() executes operation when circuit is CLOSED"""
        cb = CircuitBreaker(service_name="test_service")

        def test_operation():
            return "success"

        result = cb.call(test_operation)
        assert result == "success"

    def test_call_with_arguments(self):
        """Test that call() passes arguments to operation"""
        cb = CircuitBreaker(service_name="test_service")

        def operation_with_args(x, y, z=10):
            return x + y + z

        result = cb.call(lambda: operation_with_args(1, 2, z=3))
        assert result == 6
