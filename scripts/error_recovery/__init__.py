"""
Error Recovery Module

Provides centralized error recovery patterns including:
- Automatic retry with exponential backoff
- Circuit breaker pattern for failing services
- Service health tracking and graceful degradation
- Intelligent auto-restart for crashed services

All recovery actions are logged to the audit trail and state persists across restarts.
"""

from .retry_policy import RetryPolicy
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from .service_health import ServiceHealth
from .recovery_state import RecoveryState
from .decorators import with_retry, with_circuit_breaker

__all__ = [
    'RetryPolicy',
    'CircuitBreaker',
    'CircuitBreakerOpenError',
    'ServiceHealth',
    'RecoveryState',
    'with_retry',
    'with_circuit_breaker',
]

__version__ = '1.0.0'
