# Quickstart: Error Recovery System Integration

**Feature**: 005-error-recovery
**Date**: 2026-03-16
**Purpose**: Guide for integrating error recovery into existing and new components

---

## Overview

The error recovery system provides centralized retry logic, circuit breaker protection, and service health management. This guide shows how to integrate these capabilities into your code.

---

## Installation

No additional dependencies required - the error recovery system uses only Python standard library and existing project dependencies.

**Module Location**: `scripts/error_recovery/`

---

## Quick Start

### 1. Basic Retry with Exponential Backoff

**Use Case**: Retry transient failures automatically

```python
from scripts.error_recovery.decorators import with_retry

@with_retry(max_attempts=5, base_delay=1.0)
def fetch_emails():
    """Fetch emails from Gmail API with automatic retry"""
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', q='is:unread').execute()
    return results.get('messages', [])
```

**What it does**:
- Retries on transient errors (network timeouts, rate limits, 5xx errors)
- Uses exponential backoff: 1s, 2s, 4s, 8s, 16s
- Logs each retry attempt to audit trail
- Raises exception after max attempts exhausted

---

### 2. Circuit Breaker Protection

**Use Case**: Prevent cascading failures when external service is down

```python
from scripts.error_recovery.decorators import with_circuit_breaker

@with_circuit_breaker(service_name="gmail_api")
def call_gmail_api():
    """Call Gmail API with circuit breaker protection"""
    # API call here
    pass
```

**What it does**:
- Opens circuit after 5 consecutive failures
- Rejects requests immediately when circuit is open (fail fast)
- Tests recovery after 60-second cooldown
- Logs all state transitions to audit trail
- Creates alert in `/Needs_Action` when circuit opens

---

### 3. Combined Retry + Circuit Breaker

**Use Case**: Best practice for external API calls

```python
from scripts.error_recovery.decorators import with_retry, with_circuit_breaker

@with_circuit_breaker(service_name="gmail_api")
@with_retry(max_attempts=5, base_delay=1.0)
def fetch_emails_safe():
    """Fetch emails with full error recovery protection"""
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', q='is:unread').execute()
    return results.get('messages', [])
```

**Execution Flow**:
1. Circuit breaker checks if service is healthy
2. If circuit open: Raise `CircuitBreakerOpenError` immediately
3. If circuit closed/half-open: Attempt operation
4. On failure: Retry with exponential backoff (up to 5 attempts)
5. If all retries fail: Record failure in circuit breaker
6. If failure threshold reached: Open circuit

---

## Advanced Usage

### Custom Retry Policy

```python
from scripts.error_recovery.retry_policy import RetryPolicy
from scripts.error_recovery.decorators import with_retry

# Create custom retry policy
custom_policy = RetryPolicy(
    base_delay=2.0,        # Start with 2-second delay
    max_attempts=3,        # Only 3 attempts
    max_delay=30.0,        # Cap at 30 seconds
    backoff_multiplier=3.0, # Faster backoff (3x instead of 2x)
    jitter_enabled=True,   # Add randomization
    jitter_max=0.5         # Up to 0.5s jitter
)

@with_retry(policy=custom_policy)
def quick_operation():
    """Operation with custom retry behavior"""
    pass
```

---

### Manual Circuit Breaker Control

```python
from scripts.error_recovery.circuit_breaker import CircuitBreaker
from scripts.error_recovery.recovery_state import RecoveryState

# Load recovery state
state = RecoveryState.load()

# Get circuit breaker for service
cb = state.get_circuit_breaker("gmail_api")

# Check circuit state
if cb.state == "OPEN":
    print("Circuit is open, service is failing")

# Manually call operation with circuit breaker
try:
    result = cb.call(lambda: fetch_emails())
except CircuitBreakerOpenError:
    print("Circuit breaker rejected request")
```

---

### Service Health Monitoring

```python
from scripts.error_recovery.service_health import ServiceHealth
from scripts.error_recovery.recovery_state import RecoveryState

# Load recovery state
state = RecoveryState.load()

# Get service health
health = state.get_service_health("gmail_watcher")

# Check health status
if health.health_status == "DEGRADED":
    print(f"Service degraded: {health.consecutive_failures} failures")

# Mark service as healthy after recovery
health.mark_healthy()
state.save()
```

---

## Integration Examples

### Example 1: Migrating Gmail Watcher

**Before** (existing code in `watchers/gmail_watcher.py`):

```python
def check_for_updates(self):
    """Poll Gmail for new unread emails"""
    try:
        results = self.service.users().messages().list(
            userId='me',
            q='is:unread',
            maxResults=20
        ).execute()
        # Process results...
    except Exception as e:
        # Manual error handling
        self.state.error_count += 1
        if self.state.error_count >= 3:
            self._create_error_alert(e)
        raise
```

**After** (with error recovery):

```python
from scripts.error_recovery.decorators import with_retry, with_circuit_breaker

@with_circuit_breaker(service_name="gmail_api")
@with_retry(max_attempts=5, base_delay=1.0)
def _fetch_messages(self):
    """Fetch messages with error recovery"""
    return self.service.users().messages().list(
        userId='me',
        q='is:unread',
        maxResults=20
    ).execute()

def check_for_updates(self):
    """Poll Gmail for new unread emails"""
    try:
        results = self._fetch_messages()
        # Process results...

        # Reset error count on success
        self.state.error_count = 0

    except CircuitBreakerOpenError:
        # Circuit is open, alert already created
        print("⚠️ Gmail API circuit breaker is open")

    except Exception as e:
        # All retries exhausted
        print(f"❌ Failed after retries: {e}")
        self._create_error_alert(e)
```

**Benefits**:
- Automatic retry with exponential backoff
- Circuit breaker prevents hammering failing API
- Audit logging built-in
- Alert created automatically when circuit opens

---

### Example 2: Adding Error Recovery to New Service

```python
from scripts.error_recovery.decorators import with_retry, with_circuit_breaker
from scripts.audit_logger import AuditLogger

class LinkedInPoster:
    def __init__(self):
        self.audit_logger = AuditLogger()

    @with_circuit_breaker(service_name="linkedin_api")
    @with_retry(max_attempts=5, base_delay=1.0)
    def post_update(self, content: str):
        """Post update to LinkedIn with error recovery"""
        # LinkedIn API call
        response = linkedin_api.post(content)

        # Log successful post
        self.audit_logger.log_action(
            action_type="social_post_publish",
            actor="linkedin_poster",
            target="linkedin",
            parameters={"content_length": len(content)},
            result="success"
        )

        return response
```

---

### Example 3: Health Check Integration

**Extend `scripts/health_check.py`**:

```python
from scripts.error_recovery.recovery_state import RecoveryState

class HealthCheck:
    def check_circuit_breakers(self) -> Dict:
        """Check circuit breaker states"""
        state = RecoveryState.load()

        open_circuits = [
            name for name, cb in state.circuit_breakers.items()
            if cb.state == "OPEN"
        ]

        half_open_circuits = [
            name for name, cb in state.circuit_breakers.items()
            if cb.state == "HALF_OPEN"
        ]

        status = "healthy"
        if open_circuits:
            status = "critical"
        elif half_open_circuits:
            status = "warning"

        return {
            "status": status,
            "open_circuits": open_circuits,
            "half_open_circuits": half_open_circuits,
            "total_circuits": len(state.circuit_breakers)
        }

    def check_service_degradation(self) -> Dict:
        """Check for degraded services"""
        state = RecoveryState.load()

        degraded_services = [
            name for name, health in state.service_health.items()
            if health.state == "degraded"
        ]

        failed_services = [
            name for name, health in state.service_health.items()
            if health.state == "failed"
        ]

        status = "healthy"
        if failed_services:
            status = "critical"
        elif degraded_services:
            status = "warning"

        return {
            "status": status,
            "degraded_services": degraded_services,
            "failed_services": failed_services,
            "total_services": len(state.service_health)
        }
```

---

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# Error Recovery Configuration
ERROR_RECOVERY_BASE_DELAY=1.0          # Base retry delay (seconds)
ERROR_RECOVERY_MAX_ATTEMPTS=5          # Max retry attempts
ERROR_RECOVERY_MAX_DELAY=60.0          # Max retry delay (seconds)
ERROR_RECOVERY_CIRCUIT_THRESHOLD=5     # Failures before circuit opens
ERROR_RECOVERY_CIRCUIT_COOLDOWN=60.0   # Circuit cooldown period (seconds)
ERROR_RECOVERY_RESTART_MAX=3           # Max service restarts in window
ERROR_RECOVERY_RESTART_WINDOW=600.0    # Restart tracking window (seconds)
```

### Service Classification

Edit `scripts/error_recovery/service_health.py`:

```python
CRITICAL_SERVICES = [
    "gmail_watcher",
    "whatsapp_watcher",
    "approval_workflows"
]

NON_CRITICAL_SERVICES = [
    "daily_briefing",
    "health_check",
    "dashboard_updates"
]
```

---

## Testing

### Unit Tests

```python
import pytest
from scripts.error_recovery.decorators import with_retry

def test_retry_success_on_second_attempt():
    """Test that retry succeeds on second attempt"""
    call_count = 0

    @with_retry(max_attempts=3, base_delay=0.1)
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("Transient failure")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert call_count == 2
```

### Integration Tests

```python
import pytest
from scripts.error_recovery.circuit_breaker import CircuitBreaker

def test_circuit_breaker_opens_after_threshold():
    """Test that circuit opens after failure threshold"""
    cb = CircuitBreaker(service_name="test_service", failure_threshold=3)

    # Simulate 3 failures
    for _ in range(3):
        cb.record_failure()

    assert cb.state == "OPEN"

    # Verify requests are rejected
    with pytest.raises(CircuitBreakerOpenError):
        cb.call(lambda: "test")
```

---

## Monitoring

### Check Circuit Breaker Status

```bash
# View recovery state
cat AI_Employee_Vault/.state/recovery_state.json | jq '.circuit_breakers'

# Check for open circuits
cat AI_Employee_Vault/.state/recovery_state.json | jq '.circuit_breakers | to_entries[] | select(.value.state == "OPEN")'
```

### Check Service Health

```bash
# View service health
cat AI_Employee_Vault/.state/recovery_state.json | jq '.service_health'

# Check for degraded services
cat AI_Employee_Vault/.state/recovery_state.json | jq '.service_health | to_entries[] | select(.value.state != "healthy")'
```

### View Audit Logs

```bash
# View error recovery actions
cat AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl | jq 'select(.action_type | startswith("error_recovery"))'

# View circuit breaker state changes
cat AI_Employee_Vault/Logs/audit_$(date +%Y-%m-%d).jsonl | jq 'select(.action_type == "circuit_breaker_state_change")'
```

---

## Troubleshooting

### Circuit Breaker Stuck Open

**Symptom**: Circuit remains open even though service has recovered

**Solution**:
```python
from scripts.error_recovery.recovery_state import RecoveryState

# Load state
state = RecoveryState.load()

# Get circuit breaker
cb = state.get_circuit_breaker("gmail_api")

# Manually close circuit
cb.transition_state("CLOSED")
cb.failure_count = 0

# Save state
state.save()
```

### Too Many Retry Attempts

**Symptom**: Operations taking too long due to excessive retries

**Solution**: Reduce max_attempts or increase base_delay
```python
@with_retry(max_attempts=3, base_delay=2.0)  # Fewer, slower retries
def operation():
    pass
```

### Alert Flooding

**Symptom**: Too many alerts created when services fail

**Solution**: Rate limiting is built-in (max 1 alert per service per 5 minutes)

---

## Best Practices

1. **Always use circuit breaker for external APIs**
   - Gmail API, WhatsApp Web, LinkedIn API, etc.
   - Prevents cascading failures

2. **Combine retry + circuit breaker**
   - Retry handles transient failures
   - Circuit breaker handles sustained failures

3. **Use appropriate retry limits**
   - Fast operations: 3 attempts, 1s base delay
   - Slow operations: 5 attempts, 2s base delay
   - Critical operations: 7 attempts, 1s base delay

4. **Monitor circuit breaker states**
   - Add checks to health_check.py
   - Alert when circuits open
   - Track recovery time

5. **Test error scenarios**
   - Simulate network failures
   - Simulate API rate limits
   - Verify retry behavior
   - Verify circuit breaker opens

---

## Migration Checklist

- [ ] Identify external API calls requiring circuit breaker
- [ ] Replace manual retry logic with `@with_retry` decorator
- [ ] Add `@with_circuit_breaker` to external API calls
- [ ] Update health checks to monitor circuit breakers
- [ ] Add error recovery configuration to `.env`
- [ ] Write integration tests for error scenarios
- [ ] Update documentation with error recovery patterns
- [ ] Monitor audit logs for recovery actions

---

## Support

For questions or issues:
1. Check audit logs: `AI_Employee_Vault/Logs/audit_*.jsonl`
2. Check recovery state: `AI_Employee_Vault/.state/recovery_state.json`
3. Review error recovery tests: `tests/test_*_recovery.py`
4. Consult data model: `specs/005-error-recovery/data-model.md`
