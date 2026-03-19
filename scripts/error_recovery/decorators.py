"""
Decorators - Convenient integration for error recovery

Provides @with_retry and @with_circuit_breaker decorators for easy
integration of error recovery patterns into existing code.
"""

import time
from functools import wraps
from typing import Optional, Dict

from .retry_policy import RetryPolicy
from .circuit_breaker import CircuitBreaker
from .recovery_state import RecoveryState

# Import audit logger for logging retry attempts
try:
    from scripts.audit_logger import AuditLogger
    audit_logger = AuditLogger()
except (ImportError, FileNotFoundError, Exception):
    # Fallback if audit logger not available or not configured
    audit_logger = None

# Global registry of circuit breakers (one per service)
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_recovery_state: Optional[RecoveryState] = None


def _get_recovery_state() -> RecoveryState:
    """Get or create global RecoveryState instance"""
    global _recovery_state
    if _recovery_state is None:
        _recovery_state = RecoveryState.load()
    return _recovery_state


def _get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """
    Get or create circuit breaker for a service.

    Args:
        service_name: Name of the service

    Returns:
        CircuitBreaker instance
    """
    if service_name not in _circuit_breakers:
        # Load state from RecoveryState
        state = _get_recovery_state()
        cb_state = state.get_circuit_breaker(service_name)

        # Create circuit breaker with loaded state
        cb = CircuitBreaker(
            service_name=service_name,
            failure_threshold=cb_state.get('failure_threshold', 5),
            cooldown_period=cb_state.get('cooldown_period', 60.0),
            success_threshold=cb_state.get('success_threshold', 1)
        )

        # Restore state
        cb.state = cb_state.get('state', 'CLOSED')
        cb.failure_count = cb_state.get('failure_count', 0)
        if cb_state.get('last_failure_time'):
            from datetime import datetime
            # Parse as timezone-naive to match CircuitBreaker's use of datetime.utcnow()
            cb.last_failure_time = datetime.fromisoformat(cb_state['last_failure_time'].rstrip('Z'))

        _circuit_breakers[service_name] = cb

    return _circuit_breakers[service_name]


def _save_circuit_breaker_state(cb: CircuitBreaker):
    """
    Save circuit breaker state to RecoveryState.

    Args:
        cb: CircuitBreaker instance
    """
    state = _get_recovery_state()

    # Update circuit breaker state
    state.circuit_breakers[cb.service_name] = {
        'service_name': cb.service_name,
        'state': cb.state,
        'failure_count': cb.failure_count,
        'last_failure_time': cb.last_failure_time.isoformat() + 'Z' if cb.last_failure_time else None,
        'cooldown_period': cb.cooldown_period,
        'failure_threshold': cb.failure_threshold,
        'success_threshold': cb.success_threshold
    }

    # Persist to disk
    state.save()


def with_retry(max_attempts=5, base_delay=1.0, max_delay=60.0,
               backoff_multiplier=2.0, jitter_enabled=True):
    """
    Decorator for automatic retry with exponential backoff.

    Retries operations that fail with transient errors (ConnectionError, TimeoutError, etc.)
    using exponential backoff. Logs each retry attempt to the audit trail.

    Args:
        max_attempts: Maximum number of retry attempts (default: 5)
        base_delay: Base delay in seconds for first retry (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 60.0)
        backoff_multiplier: Exponential backoff multiplier (default: 2.0)
        jitter_enabled: Whether to add random jitter (default: True)

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(max_attempts=3, base_delay=1.0)
        def fetch_data():
            return api.get('/data')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create retry policy
            policy = RetryPolicy(
                base_delay=base_delay,
                max_attempts=max_attempts,
                max_delay=max_delay,
                backoff_multiplier=backoff_multiplier,
                jitter_enabled=jitter_enabled
            )

            attempt = 0
            last_error = None

            while attempt < max_attempts:
                try:
                    # Attempt the operation
                    result = func(*args, **kwargs)

                    # Success - log if we had previous failures
                    if attempt > 0 and audit_logger:
                        audit_logger.log_action(
                            action_type='error_recovery_retry',
                            actor='error_recovery',
                            target=func.__name__,
                            parameters={
                                'attempt': attempt,
                                'status': 'success_after_retry',
                                'total_attempts': attempt + 1
                            },
                            result='success'
                        )

                    return result

                except Exception as error:
                    last_error = error

                    # Check if we should retry
                    if not policy.should_retry(attempt, error):
                        # Permanent error or max attempts reached - don't retry
                        if audit_logger:
                            audit_logger.log_action(
                                action_type='error_recovery_retry',
                                actor='error_recovery',
                                target=func.__name__,
                                parameters={
                                    'attempt': attempt,
                                    'error_type': type(error).__name__,
                                    'error_message': str(error),
                                    'status': 'permanent_error' if attempt == 0 else 'max_attempts_exceeded'
                                },
                                result='failure'
                            )
                        raise

                    # Calculate delay and log retry attempt
                    delay = policy.calculate_delay(attempt)

                    if audit_logger:
                        audit_logger.log_action(
                            action_type='error_recovery_retry',
                            actor='error_recovery',
                            target=func.__name__,
                            parameters={
                                'attempt': attempt,
                                'error_type': type(error).__name__,
                                'error_message': str(error),
                                'delay': delay,
                                'status': 'retrying'
                            },
                            result='retry_scheduled'
                        )

                    # Wait before retry
                    time.sleep(delay)

                    # Increment attempt counter
                    attempt += 1

            # Should not reach here, but raise last error if we do
            if last_error:
                raise last_error

        return wrapper
    return decorator


def with_circuit_breaker(service_name: str, failure_threshold: int = 5,
                         cooldown_seconds: float = 60.0, success_threshold: int = 1):
    """
    Decorator for circuit breaker protection.

    Protects operations from cascading failures by implementing a three-state
    circuit breaker (CLOSED/OPEN/HALF_OPEN). Opens circuit after threshold
    failures, rejects requests during cooldown, tests recovery in half-open state.

    Args:
        service_name: Name of the service to protect
        failure_threshold: Number of failures before opening circuit (default: 5)
        cooldown_seconds: Cooldown period in seconds (default: 60.0)
        success_threshold: Number of successes to close circuit (default: 1)

    Returns:
        Decorated function with circuit breaker protection

    Example:
        @with_circuit_breaker(service_name='gmail_api')
        def fetch_emails():
            return gmail.users().messages().list().execute()

        @with_circuit_breaker(service_name='odoo', failure_threshold=10, cooldown_seconds=120)
        def create_invoice():
            return odoo.create_invoice()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get circuit breaker for this service
            cb = _get_circuit_breaker(service_name)

            # Store previous state for logging
            previous_state = cb.state

            try:
                # Execute operation with circuit breaker protection
                result = cb.call(lambda: func(*args, **kwargs))

                # Log state transition if changed
                if cb.state != previous_state and audit_logger:
                    audit_logger.log_action(
                        action_type='circuit_breaker_state_change',
                        actor='error_recovery',
                        target=service_name,
                        parameters={
                            'from_state': previous_state,
                            'to_state': cb.state,
                            'failure_count': cb.failure_count
                        },
                        result='success'
                    )

                # Save state if changed
                if cb.state != previous_state:
                    _save_circuit_breaker_state(cb)

                return result

            except Exception as error:
                # Log state transition if changed
                if cb.state != previous_state and audit_logger:
                    audit_logger.log_action(
                        action_type='circuit_breaker_state_change',
                        actor='error_recovery',
                        target=service_name,
                        parameters={
                            'from_state': previous_state,
                            'to_state': cb.state,
                            'failure_count': cb.failure_count,
                            'error_type': type(error).__name__
                        },
                        result='failure'
                    )

                # Save state if changed
                if cb.state != previous_state:
                    _save_circuit_breaker_state(cb)

                raise

        return wrapper
    return decorator
