# Feature Specification: Error Recovery System

**Feature Branch**: `005-error-recovery`
**Created**: 2026-03-16
**Status**: Draft
**Input**: User description: "Create error recovery system with retry patterns, circuit breaker, graceful degradation, and auto-restart for failed services"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Retry with Exponential Backoff (Priority: P1)

When a system component (watcher, processor, or service) encounters a transient failure (network timeout, API rate limit, temporary service unavailability), the system automatically retries the operation with exponentially increasing delays between attempts. This prevents immediate repeated failures and gives external services time to recover.

**Why this priority**: This is the foundation of error recovery. Transient failures are the most common type of failure in distributed systems. Without automatic retries, every temporary network glitch would require manual intervention. This delivers immediate value by making the system resilient to common transient issues.

**Independent Test**: Can be fully tested by simulating network failures or API timeouts and verifying that operations are retried with increasing delays (e.g., 1s, 2s, 4s, 8s) up to a maximum number of attempts. Delivers value by automatically recovering from 80%+ of transient failures without human intervention.

**Acceptance Scenarios**:

1. **Given** Gmail watcher encounters a network timeout, **When** the operation fails, **Then** system retries after 1 second, then 2 seconds, then 4 seconds, up to 5 total attempts
2. **Given** an API call fails with rate limit error (429), **When** retry is attempted, **Then** system waits for exponentially increasing delays and eventually succeeds
3. **Given** all retry attempts are exhausted, **When** operation still fails, **Then** system logs the failure, creates an alert in Needs_Action, and does not retry further
4. **Given** operation succeeds on retry attempt 3, **When** next operation is attempted, **Then** retry counter is reset to 0

---

### User Story 2 - Circuit Breaker Pattern (Priority: P2)

When a service or external API experiences sustained failures (e.g., 5 consecutive failures), the system "opens the circuit" and stops attempting to call that service for a cooldown period. This prevents cascading failures, reduces load on failing services, and allows them time to recover. After the cooldown period, the system attempts a single test request (half-open state) to check if the service has recovered.

**Why this priority**: Circuit breakers prevent cascading failures and resource exhaustion. Without this, the system would continue hammering a failing service, wasting resources and potentially making the problem worse. This is critical for system stability but builds on the retry mechanism from P1.

**Independent Test**: Can be fully tested by simulating sustained service failures (5+ consecutive failures) and verifying that the circuit opens, requests are rejected immediately during cooldown, and the circuit transitions to half-open for testing recovery. Delivers value by preventing resource waste and allowing graceful recovery.

**Acceptance Scenarios**:

1. **Given** Gmail API fails 5 consecutive times, **When** circuit breaker threshold is reached, **Then** circuit opens and subsequent requests fail immediately without attempting API call
2. **Given** circuit is open for 60 seconds, **When** cooldown period expires, **Then** circuit transitions to half-open state and allows one test request
3. **Given** circuit is half-open and test request succeeds, **When** request completes, **Then** circuit closes and normal operation resumes
4. **Given** circuit is half-open and test request fails, **When** request completes, **Then** circuit reopens for another cooldown period
5. **Given** circuit is open, **When** request is attempted, **Then** system logs circuit open event and creates alert for human review

---

### User Story 3 - Graceful Degradation (Priority: P3)

When a non-critical service fails (e.g., daily briefing generation, dashboard updates), the system continues operating with reduced functionality rather than stopping completely. Critical services (email watching, approval workflows) continue to function while non-critical features are temporarily disabled. The system logs degraded state and alerts humans for review.

**Why this priority**: Graceful degradation ensures the system remains partially operational even when components fail. This is important for user experience but less critical than preventing cascading failures. Users can still perform essential tasks while non-essential features are temporarily unavailable.

**Independent Test**: Can be fully tested by simulating failures in non-critical services (daily briefing, health check) and verifying that critical services (gmail_watcher, approval workflows) continue operating normally. Delivers value by maintaining core functionality during partial outages.

**Acceptance Scenarios**:

1. **Given** daily briefing generation fails, **When** failure is detected, **Then** system marks briefing service as degraded and continues email watching and approval workflows
2. **Given** health check service fails, **When** failure is detected, **Then** system logs degraded state but continues all watcher operations
3. **Given** system is in degraded state, **When** human reviews alert, **Then** alert clearly indicates which services are degraded and which are operational
4. **Given** degraded service recovers, **When** service becomes healthy, **Then** system automatically exits degraded state and logs recovery

---

### User Story 4 - Auto-Restart for Failed Services (Priority: P4)

When a critical service (watcher, processor) crashes or stops responding, the system automatically detects the failure and attempts to restart the service. The system tracks restart attempts and implements backoff to prevent restart loops. After a configurable number of restart attempts, the system creates an alert for human intervention.

**Why this priority**: Auto-restart reduces manual intervention for service crashes. However, this is lower priority because it requires more infrastructure (process monitoring, service management) and builds on the previous recovery mechanisms. It's valuable for long-term reliability but not essential for initial deployment.

**Independent Test**: Can be fully tested by simulating service crashes (kill process) and verifying that the system detects the failure, attempts restart with backoff, and creates alerts after max attempts. Delivers value by automatically recovering from service crashes without human intervention.

**Acceptance Scenarios**:

1. **Given** gmail_watcher process crashes, **When** health check detects missing process, **Then** system attempts to restart the service immediately
2. **Given** service fails to start on first attempt, **When** restart is attempted, **Then** system waits 30 seconds and tries again
3. **Given** service has been restarted 3 times in 10 minutes, **When** restart threshold is reached, **Then** system stops restart attempts and creates critical alert
4. **Given** service successfully restarts, **When** service is healthy for 5 minutes, **Then** restart counter is reset to 0

---

### Edge Cases

- What happens when retry delays exceed the polling interval (e.g., 8-second retry delay but 5-second poll interval)?
- How does the system handle multiple services failing simultaneously (cascading failure scenario)?
- What happens when circuit breaker cooldown expires but the service is still down?
- How does the system prevent restart loops when a service crashes immediately after starting?
- What happens when degraded services recover but then fail again quickly (flapping)?
- How does the system handle failures during the retry operation itself (e.g., retry logic crashes)?
- What happens when alert creation fails (Needs_Action directory unavailable)?
- How does the system recover state after a complete system restart (all circuits open, all services degraded)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement exponential backoff retry pattern with configurable base delay (default: 1 second) and maximum attempts (default: 5)
- **FR-002**: System MUST calculate retry delays as: delay = base_delay * (2 ^ attempt_number), capped at maximum delay (default: 60 seconds)
- **FR-003**: System MUST reset retry counters to 0 after successful operation completion
- **FR-004**: System MUST log each retry attempt with attempt number, delay, and reason for failure
- **FR-005**: System MUST create alert in Needs_Action when all retry attempts are exhausted
- **FR-006**: System MUST implement circuit breaker with three states: closed (normal), open (failing), half-open (testing recovery)
- **FR-007**: System MUST open circuit after configurable consecutive failures (default: 5 failures)
- **FR-008**: System MUST keep circuit open for configurable cooldown period (default: 60 seconds)
- **FR-009**: System MUST transition circuit to half-open state after cooldown and allow single test request
- **FR-010**: System MUST close circuit if half-open test request succeeds, or reopen if test fails
- **FR-011**: System MUST reject requests immediately when circuit is open, without attempting operation
- **FR-012**: System MUST log all circuit state transitions (closed→open, open→half-open, half-open→closed, half-open→open)
- **FR-013**: System MUST classify services as critical (email watching, approvals) or non-critical (briefing, health check, dashboard)
- **FR-014**: System MUST continue critical services when non-critical services fail
- **FR-015**: System MUST log degraded state with list of failed services and operational services
- **FR-016**: System MUST create alert when entering degraded state
- **FR-017**: System MUST automatically exit degraded state when failed services recover
- **FR-018**: System MUST detect failed services by checking process existence (ps aux) for watcher processes
- **FR-019**: System MUST attempt to restart failed critical services automatically
- **FR-020**: System MUST implement restart backoff: immediate first attempt, then 30s, 60s, 120s delays
- **FR-021**: System MUST track restart attempts per service within a time window (default: 10 minutes)
- **FR-022**: System MUST stop restart attempts after threshold (default: 3 restarts in 10 minutes)
- **FR-023**: System MUST create critical alert when restart threshold is exceeded
- **FR-024**: System MUST reset restart counter after service is healthy for stability period (default: 5 minutes)
- **FR-025**: System MUST persist circuit breaker states and retry counters to survive system restarts
- **FR-026**: System MUST load persisted state on startup and resume from last known state

### Security & Approval Requirements

- **SR-001**: System MUST log all error recovery actions (retries, circuit state changes, restarts) to audit trail
- **SR-002**: System MUST include error recovery context in audit logs: operation type, failure reason, recovery action taken
- **SR-003**: System MUST create alerts in Needs_Action for human review when automatic recovery fails
- **SR-004**: System MUST NOT expose sensitive data (API keys, tokens, passwords) in error messages or logs
- **SR-005**: System MUST implement rate limiting on alert creation to prevent alert flooding (max 1 alert per service per 5 minutes)

### Key Entities

- **RetryPolicy**: Configuration for retry behavior including base delay, max attempts, max delay, and backoff multiplier
- **CircuitBreaker**: State machine tracking circuit state (closed/open/half-open), failure count, last failure time, and cooldown period
- **ServiceHealth**: Health status of each service including state (healthy/degraded/failed), last check time, consecutive failures, and restart count
- **RecoveryState**: Persistent state including all circuit breaker states, retry counters, restart attempts, and degradation status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System automatically recovers from 80% or more of transient failures without human intervention
- **SC-002**: Circuit breaker prevents cascading failures by stopping requests to failing services within 30 seconds of sustained failure
- **SC-003**: System remains partially operational (critical services running) even when 50% of non-critical services fail
- **SC-004**: Failed services are automatically restarted within 2 minutes of detection
- **SC-005**: Manual intervention alerts are created within 1 minute of automatic recovery failure
- **SC-006**: System recovery state persists across restarts with 100% accuracy (no lost circuit states or counters)
- **SC-007**: Error recovery actions are logged to audit trail with 100% coverage
- **SC-008**: System reduces manual intervention incidents by 70% compared to current state (no automatic recovery)

## Assumptions

- Services can be restarted using standard process management (systemd, supervisord, or direct process spawn)
- Network failures and API rate limits are the most common transient failures
- Circuit breaker cooldown of 60 seconds is sufficient for most services to recover
- 5 retry attempts with exponential backoff (1s, 2s, 4s, 8s, 16s) covers most transient failure scenarios
- Critical services are: gmail_watcher, whatsapp_watcher, approval workflows
- Non-critical services are: daily_briefing, health_check, dashboard updates
- System has write access to state persistence location (AI_Employee_Vault/.state/)
- Alerts in Needs_Action directory are monitored by humans within reasonable time (hours, not days)

## Dependencies

- Existing audit logging system (004-audit-logging) for logging recovery actions
- Existing health check system (scripts/health_check.py) for service monitoring
- File system access for state persistence (AI_Employee_Vault/.state/)
- Process management capabilities (ps, kill, spawn) for service restart

## Out of Scope

- Distributed tracing across multiple services (future enhancement)
- Automatic rollback of failed deployments (separate feature)
- Load balancing or failover to backup services (requires infrastructure changes)
- Predictive failure detection using ML (future enhancement)
- Custom retry strategies per operation type (using single configurable strategy)
- Integration with external monitoring systems (Datadog, New Relic) - future enhancement
