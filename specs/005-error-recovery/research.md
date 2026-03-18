# Research: Error Recovery System

**Feature**: 005-error-recovery
**Date**: 2026-03-16
**Purpose**: Document research findings and design decisions for error recovery patterns

## Research Questions

1. What are the best practices for exponential backoff retry patterns?
2. How should circuit breaker state machines be designed?
3. What strategies exist for graceful degradation in distributed systems?
4. How should recovery state be persisted reliably?

---

## 1. Exponential Backoff Retry Patterns

### Decision: Exponential Backoff with Jitter

**Formula**: `delay = base_delay * (2 ^ attempt) + random(0, jitter_max)`

**Rationale**:
- Exponential backoff prevents overwhelming failing services
- Jitter prevents thundering herd problem (multiple clients retrying simultaneously)
- Industry standard used by AWS, Google Cloud, Azure

**Configuration**:
- Base delay: 1 second (fast enough for user experience)
- Max attempts: 5 (covers most transient failures)
- Max delay: 60 seconds (prevents excessive wait times)
- Jitter: 0-1 second (sufficient randomization)

**Alternatives Considered**:
- **Linear backoff** (1s, 2s, 3s, 4s, 5s): Rejected - too aggressive, doesn't give services time to recover
- **Fixed delay** (1s between all retries): Rejected - can overwhelm recovering services
- **Fibonacci backoff** (1s, 1s, 2s, 3s, 5s): Rejected - unnecessary complexity, exponential is standard

**Implementation Notes**:
- Retry only on transient errors (network timeouts, rate limits, 5xx errors)
- Do NOT retry on permanent errors (4xx client errors, authentication failures)
- Reset retry counter after successful operation
- Log each retry attempt to audit trail

**References**:
- AWS SDK retry strategy: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
- Google Cloud retry guidance: https://cloud.google.com/apis/design/errors#error_retries
- Existing implementation in `gmail_state.py`: `retry_with_backoff()` function

---

## 2. Circuit Breaker State Machine

### Decision: Three-State Circuit Breaker (Closed/Open/Half-Open)

**State Transitions**:
```
CLOSED (normal operation)
  ↓ (failure_count >= threshold)
OPEN (reject all requests)
  ↓ (cooldown_period elapsed)
HALF_OPEN (test with single request)
  ↓ (test succeeds)        ↓ (test fails)
CLOSED                    OPEN
```

**Rationale**:
- **CLOSED**: Normal operation, track failures
- **OPEN**: Fail fast, prevent cascading failures, give service time to recover
- **HALF_OPEN**: Test recovery with single request before full restoration

**Configuration**:
- Failure threshold: 5 consecutive failures (balances sensitivity vs false positives)
- Cooldown period: 60 seconds (sufficient for most service recoveries)
- Half-open test: Single request (minimal load on recovering service)

**Alternatives Considered**:
- **Two-state circuit breaker** (Closed/Open only): Rejected - no way to test recovery, requires manual intervention
- **Adaptive thresholds**: Rejected - adds complexity, fixed thresholds sufficient for current scale
- **Sliding window failure tracking**: Rejected - overkill for current needs, consecutive failures simpler

**Implementation Notes**:
- Circuit breaker per service (gmail_api, whatsapp_web, linkedin_api)
- State persisted to survive restarts
- All state transitions logged to audit trail
- Alert created when circuit opens (human notification)

**References**:
- Martin Fowler's Circuit Breaker pattern: https://martinfowler.com/bliki/CircuitBreaker.html
- Netflix Hystrix design: https://github.com/Netflix/Hystrix/wiki/How-it-Works
- Microsoft Azure circuit breaker guidance: https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker

---

## 3. Graceful Degradation Strategies

### Decision: Service Classification with Critical/Non-Critical Tiers

**Service Classification**:

**Critical Services** (must remain operational):
- `gmail_watcher` - Core business communication
- `whatsapp_watcher` - Core business communication
- `approval_workflows` - Required for action execution

**Non-Critical Services** (can degrade):
- `daily_briefing` - Nice to have, not blocking
- `health_check` - Monitoring only, not operational
- `dashboard_updates` - UI updates, not critical

**Degradation Strategy**:
1. Detect non-critical service failure
2. Mark service as degraded in state
3. Continue critical services normally
4. Create alert for human review
5. Automatically exit degraded state when service recovers

**Rationale**:
- Maintains core business functionality during partial outages
- Prevents non-critical failures from blocking critical operations
- Clear separation of concerns

**Alternatives Considered**:
- **All-or-nothing**: Rejected - unnecessary downtime for non-critical failures
- **Feature flags**: Rejected - adds complexity, service classification simpler
- **Load shedding**: Rejected - not applicable to current architecture (no load balancing)

**Implementation Notes**:
- Service classification hardcoded in `ServiceHealthManager`
- Degradation state persisted
- Alert includes list of degraded vs operational services
- Health check monitors degradation status

---

## 4. State Persistence Strategies

### Decision: Single JSON File with Atomic Writes

**File Location**: `AI_Employee_Vault/.state/recovery_state.json`

**Atomic Write Pattern**:
```python
1. Write to temporary file: recovery_state.json.tmp
2. Flush and sync to disk
3. Rename to recovery_state.json (atomic operation)
4. On corruption: Create backup, initialize fresh state
```

**State Schema**:
```json
{
  "version": "1.0.0",
  "last_updated": "2026-03-16T12:34:56Z",
  "circuit_breakers": {
    "gmail_api": {
      "state": "CLOSED",
      "failure_count": 0,
      "last_failure_time": null,
      "cooldown_period": 60,
      "failure_threshold": 5
    }
  },
  "service_health": {
    "gmail_watcher": {
      "state": "healthy",
      "last_check_time": "2026-03-16T12:34:56Z",
      "consecutive_failures": 0,
      "restart_count": 0,
      "last_restart_time": null
    }
  },
  "retry_counters": {
    "gmail_api_fetch": 0
  }
}
```

**Rationale**:
- Single file simplifies consistency (no distributed state)
- JSON is human-readable for debugging
- Atomic rename prevents corruption
- Follows existing patterns in codebase (gmail_watcher_state.json, whatsapp_watcher_state.json)

**Alternatives Considered**:
- **SQLite database**: Rejected - adds dependency, overkill for current scale
- **Multiple JSON files**: Rejected - consistency challenges, atomic updates harder
- **In-memory only**: Rejected - violates constitution (state must persist)
- **Pickle format**: Rejected - not human-readable, security concerns

**Implementation Notes**:
- State loaded on startup
- State saved after each significant change (circuit state transition, service health change)
- Backup created on corruption with timestamp
- Schema versioning for future migrations

**References**:
- Existing implementation in `gmail_state.py`: `save()` method with atomic writes
- Existing implementation in `whatsapp_watcher.py`: `save_state()` method

---

## 5. Integration with Existing Systems

### Audit Logging Integration

**Existing System**: `scripts/audit_logger.py` (004-audit-logging)

**Integration Points**:
- Log retry attempts: `action_type="error_recovery_retry"`
- Log circuit breaker state changes: `action_type="circuit_breaker_state_change"`
- Log service restarts: `action_type="service_restart"`
- Log degradation events: `action_type="service_degradation"`

**Benefits**:
- Complete audit trail of all recovery actions
- Compliance with constitution (Principle VII: Auditability)
- Debugging and analysis capabilities

### Health Check Integration

**Existing System**: `scripts/health_check.py`

**New Checks**:
- `check_circuit_breakers()`: Monitor open circuits
- `check_service_degradation()`: Monitor degraded services
- `check_restart_attempts()`: Monitor restart thresholds

**Benefits**:
- Centralized monitoring
- Alerts created automatically
- Dashboard visibility

### Watcher Integration

**Existing Retry Logic**:
- `whatsapp_watcher.py`: `@retry_with_backoff(max_retries=3, base_delay=1.0)` decorator
- `gmail_state.py`: `retry_with_backoff()` function

**Migration Strategy**:
1. Keep existing retry logic commented out
2. Replace with centralized `@with_retry` decorator
3. Add `@with_circuit_breaker` decorator for external API calls
4. Verify existing functionality preserved
5. Remove old retry code after validation

**Benefits**:
- Consistent retry behavior across all components
- Circuit breaker protection added
- Easier to test and maintain

---

## 6. Performance Considerations

### Latency Impact

**Retry Decision**: < 10ms (in-memory calculation)
**Circuit Breaker Check**: < 5ms (in-memory state lookup)
**State Persistence**: < 50ms (async write to disk)

**Mitigation Strategies**:
- In-memory cache of recovery state
- Async state persistence (non-blocking)
- Batch state updates when possible

### Memory Impact

**State File Size**: < 100KB (estimated)
- 10 circuit breakers × 200 bytes = 2KB
- 10 service health records × 300 bytes = 3KB
- 50 retry counters × 100 bytes = 5KB
- Total: ~10KB (well under 100KB limit)

**In-Memory Cache**: < 1MB (negligible)

### Disk I/O Impact

**Write Frequency**:
- Circuit state change: ~1-10 per minute during failures
- Service health update: ~1 per 5 minutes (health check interval)
- Retry counter update: Not persisted (in-memory only)

**Mitigation**: Batch updates, async writes, rate limiting

---

## 7. Testing Strategy

### Unit Test Coverage

- Retry policy calculation (exponential backoff, jitter)
- Circuit breaker state transitions
- Service health state management
- State persistence (save/load/corruption recovery)

### Integration Test Coverage

- Retry + circuit breaker interaction
- Audit logging integration
- Health check integration
- Watcher migration validation

### E2E Test Coverage

- Complete recovery from transient failure
- Circuit breaker prevents cascading failure
- Service restart with backoff
- State persistence across restart

---

## Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Retry Pattern | Exponential backoff with jitter | Industry standard, prevents thundering herd |
| Circuit Breaker | Three-state (Closed/Open/Half-Open) | Enables automatic recovery testing |
| Service Classification | Critical vs Non-Critical | Maintains core functionality during partial outages |
| State Persistence | Single JSON file with atomic writes | Simple, consistent with existing patterns |
| Integration | Centralized module with decorators | Eliminates duplication, easier to maintain |

---

## Open Questions

None - all design decisions finalized based on existing codebase patterns and industry best practices.

---

## References

1. AWS Exponential Backoff and Jitter: https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
2. Martin Fowler Circuit Breaker: https://martinfowler.com/bliki/CircuitBreaker.html
3. Netflix Hystrix: https://github.com/Netflix/Hystrix/wiki
4. Microsoft Azure Patterns: https://learn.microsoft.com/en-us/azure/architecture/patterns/
5. Existing codebase: `scripts/audit_logger.py`, `scripts/health_check.py`, `watchers/gmail_watcher.py`
