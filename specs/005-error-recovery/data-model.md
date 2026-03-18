# Data Model: Error Recovery System

**Feature**: 005-error-recovery
**Date**: 2026-03-16
**Purpose**: Define core entities and their relationships for the error recovery system

---

## Entity Overview

The error recovery system consists of four core entities:

1. **RetryPolicy** - Configuration for retry behavior
2. **CircuitBreaker** - State machine for failure protection
3. **ServiceHealth** - Health status tracking per service
4. **RecoveryState** - Persistent state container

---

## 1. RetryPolicy

**Purpose**: Encapsulates retry configuration and logic for exponential backoff

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_delay` | float | 1.0 | Base delay in seconds for first retry |
| `max_attempts` | int | 5 | Maximum number of retry attempts |
| `max_delay` | float | 60.0 | Maximum delay cap in seconds |
| `backoff_multiplier` | float | 2.0 | Exponential backoff multiplier |
| `jitter_enabled` | bool | True | Whether to add random jitter |
| `jitter_max` | float | 1.0 | Maximum jitter in seconds |

### Methods

- `calculate_delay(attempt: int) -> float`: Calculate delay for given attempt number
- `should_retry(attempt: int, error: Exception) -> bool`: Determine if retry should be attempted
- `is_transient_error(error: Exception) -> bool`: Check if error is transient (retryable)

### Validation Rules

- `base_delay` must be > 0
- `max_attempts` must be >= 1
- `max_delay` must be >= `base_delay`
- `backoff_multiplier` must be >= 1.0
- `jitter_max` must be >= 0

### Behavior

**Delay Calculation**:
```
delay = min(base_delay * (backoff_multiplier ^ attempt), max_delay)
if jitter_enabled:
    delay += random(0, jitter_max)
```

**Transient Errors** (retryable):
- `ConnectionError`, `TimeoutError`, `ConnectionResetError`
- HTTP 429 (Rate Limit), 500, 502, 503, 504
- `BrokenPipeError`, `OSError` with network-related errno

**Permanent Errors** (not retryable):
- HTTP 400, 401, 403, 404
- `ValueError`, `TypeError`, `KeyError`
- Authentication failures

---

## 2. CircuitBreaker

**Purpose**: State machine that prevents cascading failures by failing fast when service is unhealthy

### States

| State | Description | Behavior |
|-------|-------------|----------|
| `CLOSED` | Normal operation | Allow all requests, track failures |
| `OPEN` | Service failing | Reject all requests immediately |
| `HALF_OPEN` | Testing recovery | Allow single test request |

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `service_name` | str | (required) | Unique identifier for service |
| `state` | str | "CLOSED" | Current state (CLOSED/OPEN/HALF_OPEN) |
| `failure_count` | int | 0 | Consecutive failures in CLOSED state |
| `last_failure_time` | datetime | None | Timestamp of last failure |
| `cooldown_period` | float | 60.0 | Seconds to wait before HALF_OPEN |
| `failure_threshold` | int | 5 | Failures before opening circuit |
| `success_threshold` | int | 1 | Successes in HALF_OPEN to close |

### Methods

- `call(operation: Callable) -> Any`: Execute operation with circuit breaker protection
- `record_success()`: Record successful operation
- `record_failure()`: Record failed operation
- `transition_state(new_state: str)`: Change circuit state
- `should_attempt_request() -> bool`: Check if request should be attempted
- `is_cooldown_expired() -> bool`: Check if cooldown period has elapsed

### State Transitions

```
CLOSED:
  - On success: failure_count = 0
  - On failure: failure_count++
  - If failure_count >= failure_threshold: → OPEN

OPEN:
  - All requests rejected immediately
  - If cooldown_period elapsed: → HALF_OPEN

HALF_OPEN:
  - Allow single test request
  - On success: → CLOSED
  - On failure: → OPEN (reset cooldown)
```

### Validation Rules

- `service_name` must be non-empty string
- `state` must be one of: "CLOSED", "OPEN", "HALF_OPEN"
- `failure_threshold` must be >= 1
- `cooldown_period` must be > 0
- `success_threshold` must be >= 1

---

## 3. ServiceHealth

**Purpose**: Track health status and restart attempts for each service

### States

| State | Description | Criteria |
|-------|-------------|----------|
| `healthy` | Service operating normally | No recent failures |
| `degraded` | Service experiencing issues | Non-critical service failing |
| `failed` | Service not operational | Critical service failing |

### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `service_name` | str | (required) | Unique identifier for service |
| `state` | str | "healthy" | Current health state |
| `is_critical` | bool | True | Whether service is critical |
| `last_check_time` | datetime | None | Last health check timestamp |
| `consecutive_failures` | int | 0 | Consecutive failure count |
| `restart_count` | int | 0 | Restart attempts in time window |
| `last_restart_time` | datetime | None | Last restart attempt timestamp |
| `restart_window` | float | 600.0 | Time window for restart tracking (seconds) |
| `max_restarts` | int | 3 | Max restarts in time window |
| `stability_period` | float | 300.0 | Seconds service must be healthy to reset counter |

### Methods

- `mark_healthy()`: Mark service as healthy
- `mark_degraded()`: Mark service as degraded
- `mark_failed()`: Mark service as failed
- `should_restart() -> bool`: Check if restart should be attempted
- `record_restart()`: Record restart attempt
- `reset_restart_counter()`: Reset restart counter after stability period
- `is_restart_threshold_exceeded() -> bool`: Check if max restarts exceeded

### Validation Rules

- `service_name` must be non-empty string
- `state` must be one of: "healthy", "degraded", "failed"
- `restart_window` must be > 0
- `max_restarts` must be >= 1
- `stability_period` must be > 0

### Behavior

**Restart Decision Logic**:
```
should_restart = (
    state == "failed" AND
    is_critical AND
    restart_count < max_restarts AND
    (now - last_restart_time) > restart_backoff
)
```

**Restart Backoff**:
- Attempt 1: Immediate (0 seconds)
- Attempt 2: 30 seconds
- Attempt 3: 60 seconds
- Attempt 4+: 120 seconds

**Restart Counter Reset**:
- If service healthy for `stability_period` (300s), reset `restart_count` to 0

---

## 4. RecoveryState

**Purpose**: Container for all recovery state, handles persistence and loading

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `version` | str | Schema version (e.g., "1.0.0") |
| `last_updated` | datetime | Last state update timestamp |
| `circuit_breakers` | Dict[str, CircuitBreaker] | Circuit breakers by service name |
| `service_health` | Dict[str, ServiceHealth] | Service health by service name |
| `retry_counters` | Dict[str, int] | In-memory retry counters (not persisted) |

### Methods

- `save()`: Persist state to disk (atomic write)
- `load() -> RecoveryState`: Load state from disk
- `get_circuit_breaker(service_name: str) -> CircuitBreaker`: Get or create circuit breaker
- `get_service_health(service_name: str) -> ServiceHealth`: Get or create service health
- `to_dict() -> dict`: Serialize to dictionary
- `from_dict(data: dict) -> RecoveryState`: Deserialize from dictionary

### Persistence

**File Location**: `AI_Employee_Vault/.state/recovery_state.json`

**Atomic Write Pattern**:
1. Serialize to JSON
2. Write to temporary file: `recovery_state.json.tmp`
3. Flush and sync to disk
4. Atomic rename to `recovery_state.json`

**Corruption Handling**:
- On JSON parse error: Create backup with timestamp
- Initialize fresh state with defaults
- Log corruption event to audit trail

**Schema Versioning**:
- Current version: "1.0.0"
- Future migrations handled by version check in `from_dict()`

### JSON Schema

```json
{
  "version": "1.0.0",
  "last_updated": "2026-03-16T12:34:56Z",
  "circuit_breakers": {
    "gmail_api": {
      "service_name": "gmail_api",
      "state": "CLOSED",
      "failure_count": 0,
      "last_failure_time": null,
      "cooldown_period": 60.0,
      "failure_threshold": 5,
      "success_threshold": 1
    }
  },
  "service_health": {
    "gmail_watcher": {
      "service_name": "gmail_watcher",
      "state": "healthy",
      "is_critical": true,
      "last_check_time": "2026-03-16T12:34:56Z",
      "consecutive_failures": 0,
      "restart_count": 0,
      "last_restart_time": null,
      "restart_window": 600.0,
      "max_restarts": 3,
      "stability_period": 300.0
    }
  }
}
```

---

## Entity Relationships

```
RecoveryState (1) ──┬── (0..*) CircuitBreaker
                    └── (0..*) ServiceHealth

CircuitBreaker (1) ── (1) RetryPolicy (implicit, configured per service)
ServiceHealth (1) ── (1) Service (external, monitored by health_check.py)
```

**Relationship Notes**:
- `RecoveryState` is the root aggregate, owns all circuit breakers and service health records
- Each `CircuitBreaker` protects one external service (gmail_api, whatsapp_web, linkedin_api)
- Each `ServiceHealth` tracks one internal service (gmail_watcher, whatsapp_watcher, etc.)
- `RetryPolicy` is configuration, not persisted (can be different per operation)

---

## Service Registry

**Critical Services** (must remain operational):
- `gmail_watcher` - Gmail monitoring
- `whatsapp_watcher` - WhatsApp monitoring
- `approval_workflows` - Action execution

**Non-Critical Services** (can degrade):
- `daily_briefing` - Daily report generation
- `health_check` - System monitoring
- `dashboard_updates` - UI updates

**External Services** (circuit breaker protected):
- `gmail_api` - Gmail API calls
- `whatsapp_web` - WhatsApp Web automation
- `linkedin_api` - LinkedIn API calls

---

## State Lifecycle

### Initialization (System Startup)

1. Load `recovery_state.json` from disk
2. If file missing: Initialize with empty state
3. If file corrupted: Create backup, initialize fresh
4. Validate schema version
5. Restore circuit breaker states
6. Restore service health states

### Runtime Updates

**Circuit Breaker State Changes**:
- Trigger: Failure threshold reached, cooldown expired, test request completed
- Action: Update state, persist to disk, log to audit trail

**Service Health Changes**:
- Trigger: Health check detects failure, service recovers, restart attempted
- Action: Update state, persist to disk, log to audit trail

**Retry Counter Updates**:
- Trigger: Operation retried
- Action: Increment in-memory counter (not persisted)
- Reset: After successful operation

### Persistence Frequency

- Circuit state change: Immediate (async)
- Service health change: Immediate (async)
- Retry counter: Not persisted (in-memory only)
- Batch updates: When multiple changes occur within 1 second

---

## Data Integrity

### Validation

All entities validate their attributes on creation and modification:
- Type checking (int, float, str, datetime)
- Range checking (positive values, thresholds)
- State validation (valid enum values)

### Consistency

- Atomic writes prevent partial state corruption
- Schema versioning enables future migrations
- Backup on corruption prevents data loss

### Auditability

All state changes logged to audit trail:
- Circuit breaker state transitions
- Service health changes
- Restart attempts
- State persistence events

---

## Performance Characteristics

### Memory Usage

- `RetryPolicy`: ~200 bytes (configuration only)
- `CircuitBreaker`: ~300 bytes per instance
- `ServiceHealth`: ~400 bytes per instance
- `RecoveryState`: ~10KB total (10 services × ~1KB)

### Disk Usage

- State file: ~10KB (JSON format)
- Backup files: ~10KB each (created on corruption)
- Total: < 100KB

### Latency

- State lookup: < 1ms (in-memory)
- State persistence: < 50ms (async write)
- Circuit breaker check: < 5ms
- Retry decision: < 10ms

---

## Summary

The error recovery data model provides:
- **Retry logic** via `RetryPolicy` with exponential backoff
- **Failure protection** via `CircuitBreaker` state machine
- **Health tracking** via `ServiceHealth` with restart management
- **State persistence** via `RecoveryState` with atomic writes

All entities are designed for:
- Type safety and validation
- Efficient memory usage
- Fast lookups and updates
- Reliable persistence
- Complete auditability
