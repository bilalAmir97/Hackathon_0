"""
CircuitBreaker - State machine for failure protection

Implements three-state circuit breaker (CLOSED/OPEN/HALF_OPEN) to prevent
cascading failures when services are unhealthy.
"""

from datetime import datetime, timedelta
from typing import Callable, Any, Optional


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    State machine that prevents cascading failures by failing fast.

    Implements three-state circuit breaker pattern:
    - CLOSED: Normal operation, track failures
    - OPEN: Fail fast, reject all requests
    - HALF_OPEN: Test recovery with single request
    """

    def __init__(self, service_name: str, failure_threshold: int = 5,
                 cooldown_period: float = 60.0, success_threshold: int = 1):
        """
        Initialize CircuitBreaker.

        Args:
            service_name: Name of the service to protect
            failure_threshold: Number of failures before opening circuit (default: 5)
            cooldown_period: Seconds to wait before testing recovery (default: 60.0)
            success_threshold: Successes needed in HALF_OPEN to close (default: 1)
        """
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.cooldown_period = cooldown_period
        self.success_threshold = success_threshold
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None

    def call(self, operation: Callable[[], Any]) -> Any:
        """
        Execute operation with circuit breaker protection.

        Args:
            operation: Callable to execute

        Returns:
            Result of operation

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN
        """
        # Check if we should attempt the request
        if not self.should_attempt_request():
            raise CircuitBreakerOpenError(
                f"Circuit breaker is OPEN for service '{self.service_name}'. "
                f"Cooldown period: {self.cooldown_period}s"
            )

        # If cooldown expired, transition to HALF_OPEN
        if self.state == "OPEN" and self.is_cooldown_expired():
            self.transition_state("HALF_OPEN")

        try:
            # Execute operation
            result = operation()

            # Record success
            self.record_success()

            return result

        except Exception as error:
            # Record failure
            self.record_failure()
            raise

    def record_success(self):
        """Record successful operation and potentially close circuit"""
        if self.state == "HALF_OPEN":
            # Success in HALF_OPEN -> close circuit
            self.transition_state("CLOSED")

        # Reset failure count
        self.failure_count = 0

    def record_failure(self):
        """Record failed operation and potentially open circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == "CLOSED":
            # Check if we've reached failure threshold
            if self.failure_count >= self.failure_threshold:
                self.transition_state("OPEN")

        elif self.state == "HALF_OPEN":
            # Failure in HALF_OPEN -> reopen circuit
            self.transition_state("OPEN")

    def transition_state(self, new_state: str):
        """
        Change circuit state.

        Args:
            new_state: New state (CLOSED, OPEN, or HALF_OPEN)
        """
        old_state = self.state
        self.state = new_state

        # Reset failure count when closing
        if new_state == "CLOSED":
            self.failure_count = 0

        # TODO: Log state transition to audit trail (Phase 4 integration)

    def should_attempt_request(self) -> bool:
        """
        Check if request should be attempted.

        Returns:
            True if request should be attempted, False otherwise
        """
        if self.state == "CLOSED":
            return True

        if self.state == "HALF_OPEN":
            return True

        if self.state == "OPEN":
            # Check if cooldown expired
            if self.is_cooldown_expired():
                return True
            return False

        return False

    def is_cooldown_expired(self) -> bool:
        """
        Check if cooldown period has elapsed.

        Returns:
            True if cooldown expired, False otherwise
        """
        if self.last_failure_time is None:
            return False

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.cooldown_period
