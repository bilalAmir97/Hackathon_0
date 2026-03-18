# Tasks: Error Recovery System

**Input**: Design documents from `/specs/005-error-recovery/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: This feature uses TDD (Test-Driven Development) - tests are written FIRST and must FAIL before implementation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and module structure

- [X] T001 Create error_recovery module directory at scripts/error_recovery/
- [X] T002 [P] Create __init__.py in scripts/error_recovery/ with module exports
- [X] T003 [P] Create pytest configuration in pyproject.toml for error recovery tests
- [X] T004 [P] Create tests directory structure (tests/test_retry_policy.py, tests/test_circuit_breaker.py, tests/test_service_health.py, tests/test_recovery_state.py, tests/test_decorators.py)
- [X] T005 [P] Create test fixtures in tests/conftest.py for error recovery (mock audit logger, temp state files, mock services)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create RecoveryState class skeleton in scripts/error_recovery/recovery_state.py (load, save, to_dict, from_dict methods)
- [X] T007 [P] Implement atomic file write pattern in RecoveryState.save() with temp file and rename
- [X] T008 [P] Implement JSON schema versioning in RecoveryState (version 1.0.0)
- [X] T009 [P] Implement corruption recovery in RecoveryState.load() with backup creation
- [X] T010 [P] Create state directory AI_Employee_Vault/.state/ if not exists
- [X] T011 Write unit tests for RecoveryState in tests/test_recovery_state.py (save, load, corruption recovery, schema versioning)
- [X] T012 Verify RecoveryState tests pass

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel ✅

---

## Phase 3: User Story 1 - Automatic Retry with Exponential Backoff (Priority: P1) 🎯 MVP

**Goal**: Implement automatic retry with exponential backoff for transient failures. System retries operations with increasing delays (1s, 2s, 4s, 8s, 16s) up to 5 attempts.

**Independent Test**: Simulate network failures and verify operations are retried with exponentially increasing delays. Verify retry counter resets after success.

### Tests for User Story 1 (TDD - Write FIRST) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Write test_calculate_delay_exponential_backoff() in tests/test_retry_policy.py
- [X] T014 [P] [US1] Write test_calculate_delay_with_jitter() in tests/test_retry_policy.py
- [X] T015 [P] [US1] Write test_calculate_delay_max_cap() in tests/test_retry_policy.py
- [X] T016 [P] [US1] Write test_should_retry_transient_errors() in tests/test_retry_policy.py (ConnectionError, TimeoutError, HTTP 429/500/502/503/504)
- [X] T017 [P] [US1] Write test_should_not_retry_permanent_errors() in tests/test_retry_policy.py (HTTP 400/401/403/404, ValueError, TypeError)
- [X] T018 [P] [US1] Write test_retry_counter_reset_after_success() in tests/test_retry_policy.py
- [X] T019 [P] [US1] Write test_max_attempts_enforced() in tests/test_retry_policy.py
- [X] T020 [US1] Run tests and verify they FAIL (no implementation yet)

### Implementation for User Story 1

- [X] T021 [P] [US1] Create RetryPolicy class in scripts/error_recovery/retry_policy.py with attributes (base_delay, max_attempts, max_delay, backoff_multiplier, jitter_enabled, jitter_max)
- [X] T022 [P] [US1] Implement calculate_delay(attempt) method in RetryPolicy with exponential backoff formula
- [X] T023 [P] [US1] Implement should_retry(attempt, error) method in RetryPolicy
- [X] T024 [P] [US1] Implement is_transient_error(error) method in RetryPolicy
- [X] T025 [P] [US1] Add validation in RetryPolicy.__init__() for all attributes
- [X] T026 [US1] Run RetryPolicy tests and verify they PASS
- [X] T027 [P] [US1] Write test_with_retry_decorator_success_on_retry() in tests/test_decorators.py
- [X] T028 [P] [US1] Write test_with_retry_decorator_exhausts_attempts() in tests/test_decorators.py
- [X] T029 [P] [US1] Write test_with_retry_decorator_logs_to_audit() in tests/test_decorators.py
- [X] T030 [US1] Implement @with_retry decorator in scripts/error_recovery/decorators.py
- [X] T031 [US1] Integrate AuditLogger in @with_retry decorator to log each retry attempt
- [X] T032 [US1] Run decorator tests and verify they PASS
- [X] T033 [US1] Update RecoveryState to track retry counters (in-memory only, not persisted)
- [X] T034 [US1] Write integration test test_retry_with_real_failure_simulation() in tests/test_integration_recovery.py
- [X] T035 [US1] Run integration test and verify it PASSES

**Checkpoint**: At this point, User Story 1 should be fully functional - automatic retry with exponential backoff works end-to-end ✅

---

## Phase 4: User Story 2 - Circuit Breaker Pattern (Priority: P2)

**Goal**: Implement circuit breaker to prevent cascading failures. Circuit opens after 5 consecutive failures, stays open for 60 seconds, then transitions to half-open for testing recovery.

**Independent Test**: Simulate sustained service failures (5+ consecutive) and verify circuit opens, requests are rejected immediately, and circuit transitions to half-open after cooldown.

### Tests for User Story 2 (TDD - Write FIRST) ⚠️

- [X] T036 [P] [US2] Write test_circuit_breaker_initial_state_closed() in tests/test_circuit_breaker.py
- [X] T037 [P] [US2] Write test_circuit_opens_after_threshold() in tests/test_circuit_breaker.py (5 failures)
- [X] T038 [P] [US2] Write test_circuit_rejects_requests_when_open() in tests/test_circuit_breaker.py
- [X] T039 [P] [US2] Write test_circuit_transitions_to_half_open_after_cooldown() in tests/test_circuit_breaker.py
- [X] T040 [P] [US2] Write test_circuit_closes_on_half_open_success() in tests/test_circuit_breaker.py
- [X] T041 [P] [US2] Write test_circuit_reopens_on_half_open_failure() in tests/test_circuit_breaker.py
- [X] T042 [P] [US2] Write test_circuit_state_transitions_logged() in tests/test_circuit_breaker.py
- [X] T043 [P] [US2] Write test_circuit_failure_count_resets_on_success() in tests/test_circuit_breaker.py
- [X] T044 [US2] Run tests and verify they FAIL (no implementation yet)

### Implementation for User Story 2

- [X] T045 [P] [US2] Create CircuitBreaker class in scripts/error_recovery/circuit_breaker.py with attributes (service_name, state, failure_count, last_failure_time, cooldown_period, failure_threshold)
- [X] T046 [P] [US2] Implement call(operation) method in CircuitBreaker
- [X] T047 [P] [US2] Implement record_success() method in CircuitBreaker
- [X] T048 [P] [US2] Implement record_failure() method in CircuitBreaker
- [X] T049 [P] [US2] Implement transition_state(new_state) method in CircuitBreaker
- [X] T050 [P] [US2] Implement should_attempt_request() method in CircuitBreaker
- [X] T051 [P] [US2] Implement is_cooldown_expired() method in CircuitBreaker
- [X] T052 [P] [US2] Add CircuitBreakerOpenError exception class in scripts/error_recovery/circuit_breaker.py
- [X] T053 [US2] Run CircuitBreaker tests and verify they PASS
- [X] T054 [P] [US2] Write test_with_circuit_breaker_decorator_normal_operation() in tests/test_decorators.py
- [X] T055 [P] [US2] Write test_with_circuit_breaker_decorator_opens_on_failures() in tests/test_decorators.py
- [X] T056 [P] [US2] Write test_with_circuit_breaker_decorator_rejects_when_open() in tests/test_decorators.py
- [X] T057 [US2] Implement @with_circuit_breaker decorator in scripts/error_recovery/decorators.py
- [X] T058 [US2] Integrate AuditLogger in @with_circuit_breaker to log state transitions
- [X] T059 [US2] Run decorator tests and verify they PASS
- [X] T060 [US2] Update RecoveryState to persist circuit breaker states (get_circuit_breaker, save circuit states)
- [X] T061 [US2] Write test_combined_retry_and_circuit_breaker() in tests/test_decorators.py
- [X] T062 [US2] Verify @with_circuit_breaker and @with_retry work together correctly
- [X] T063 [US2] Write integration test test_circuit_breaker_prevents_cascading_failure() in tests/test_integration_recovery.py
- [X] T064 [US2] Run integration test and verify it PASSES
- [X] T065 [US2] Implement alert creation in CircuitBreaker when circuit opens (create ALERT_*.md in Needs_Action/)
- [X] T066 [US2] Write test for alert creation when circuit opens

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - retry + circuit breaker protection

---

## Phase 5: User Story 3 - Graceful Degradation (Priority: P3)

**Goal**: Implement service health tracking and graceful degradation. System classifies services as critical/non-critical and continues critical services when non-critical services fail.

**Independent Test**: Simulate failures in non-critical services (daily briefing, health check) and verify critical services (gmail_watcher, approval workflows) continue operating normally.

### Tests for User Story 3 (TDD - Write FIRST) ⚠️

- [X] T067 [P] [US3] Write test_service_health_initial_state_healthy() in tests/test_service_health.py
- [X] T068 [P] [US3] Write test_mark_service_degraded() in tests/test_service_health.py
- [X] T069 [P] [US3] Write test_mark_service_failed() in tests/test_service_health.py
- [X] T070 [P] [US3] Write test_service_classification_critical_vs_noncritical() in tests/test_service_health.py
- [X] T071 [P] [US3] Write test_degradation_alert_created() in tests/test_service_health.py
- [X] T072 [P] [US3] Write test_automatic_recovery_from_degraded_state() in tests/test_service_health.py
- [X] T073 [P] [US3] Write test_consecutive_failures_tracked() in tests/test_service_health.py
- [X] T074 [US3] Run tests and verify they FAIL (no implementation yet)

### Implementation for User Story 3

- [X] T075 [P] [US3] Create ServiceHealth class in scripts/error_recovery/service_health.py with attributes (service_name, state, is_critical, last_check_time, consecutive_failures)
- [X] T076 [P] [US3] Implement mark_healthy() method in ServiceHealth
- [X] T077 [P] [US3] Implement mark_degraded() method in ServiceHealth
- [X] T078 [P] [US3] Implement mark_failed() method in ServiceHealth
- [X] T079 [P] [US3] Define CRITICAL_SERVICES and NON_CRITICAL_SERVICES constants in scripts/error_recovery/service_health.py
- [X] T080 [US3] Run ServiceHealth tests and verify they PASS
- [X] T081 [US3] Update RecoveryState to persist service health states (get_service_health, save health states)
- [X] T082 [P] [US3] Implement alert creation when entering degraded state (create ALERT_DEGRADATION_*.md in Needs_Action/)
- [X] T083 [P] [US3] Implement alert rate limiting (max 1 alert per service per 5 minutes)
- [X] T084 [US3] Write integration test test_graceful_degradation_maintains_critical_services() in tests/test_integration_recovery.py
- [X] T085 [US3] Run integration test and verify it PASSES

**Checkpoint**: All three user stories (retry, circuit breaker, graceful degradation) should now be independently functional ✅

---

## Phase 6: User Story 4 - Auto-Restart for Failed Services (Priority: P4)

**Goal**: Implement automatic service restart with intelligent backoff. System detects crashed services, attempts restart with backoff (0s, 30s, 60s, 120s), and creates alerts after threshold.

**Independent Test**: Simulate service crashes (kill process) and verify system detects failure, attempts restart with backoff, and creates alerts after max attempts.

### Tests for User Story 4 (TDD - Write FIRST) ⚠️

- [X] T086 [P] [US4] Write test_should_restart_critical_service() in tests/test_service_health.py
- [X] T087 [P] [US4] Write test_should_not_restart_noncritical_service() in tests/test_service_health.py
- [X] T088 [P] [US4] Write test_restart_backoff_delays() in tests/test_service_health.py (0s, 30s, 60s, 120s)
- [X] T089 [P] [US4] Write test_restart_threshold_exceeded() in tests/test_service_health.py (3 restarts in 10 minutes)
- [X] T090 [P] [US4] Write test_restart_counter_reset_after_stability() in tests/test_service_health.py (5 minutes healthy)
- [X] T091 [P] [US4] Write test_restart_alert_created_after_threshold() in tests/test_service_health.py
- [X] T092 [US4] Run tests and verify they FAIL (no implementation yet)

### Implementation for User Story 4

- [X] T093 [P] [US4] Add restart tracking attributes to ServiceHealth (restart_count, last_restart_time, restart_window, max_restarts, stability_period)
- [X] T094 [P] [US4] Implement should_restart() method in ServiceHealth
- [X] T095 [P] [US4] Implement record_restart() method in ServiceHealth
- [X] T096 [P] [US4] Implement reset_restart_counter() method in ServiceHealth
- [X] T097 [P] [US4] Implement is_restart_threshold_exceeded() method in ServiceHealth
- [X] T098 [P] [US4] Implement calculate_restart_backoff(attempt) method in ServiceHealth
- [X] T099 [US4] Run ServiceHealth restart tests and verify they PASS
- [X] T100 [US4] Extend health_check.py to detect failed services (check process existence with ps aux)
- [X] T101 [US4] Extend health_check.py to call ServiceHealth.should_restart() for failed services
- [X] T102 [US4] Implement service restart logic in health_check.py (spawn process with subprocess)
- [X] T103 [US4] Integrate restart attempt logging with AuditLogger
- [X] T104 [US4] Implement alert creation when restart threshold exceeded (create ALERT_RESTART_*.md in Needs_Action/)
- [X] T105 [US4] Write integration test test_auto_restart_with_backoff() in tests/test_integration_recovery.py
- [X] T106 [US4] Run integration test and verify it PASSES

**Checkpoint**: All four user stories should now be independently functional - complete error recovery system ✅

---

## Phase 7: Integration & Watcher Migration

**Purpose**: Integrate error recovery into existing watchers and validate end-to-end

- [X] T107 [P] Migrate gmail_watcher.py to use @with_retry and @with_circuit_breaker decorators
- [X] T108 [P] Migrate whatsapp_watcher.py to use @with_retry and @with_circuit_breaker decorators
- [X] T109 [P] Add circuit breaker protection to linkedin_api_poster.py
- [X] T110 [P] Remove old retry logic from gmail_watcher.py (keep commented for rollback)
- [X] T111 [P] Remove old retry logic from whatsapp_watcher.py (keep commented for rollback)
- [X] T112 Write test_gmail_watcher_with_error_recovery() in tests/test_watcher_integration.py
- [X] T113 Write test_whatsapp_watcher_with_error_recovery() in tests/test_watcher_integration.py
- [X] T114 Run watcher integration tests and verify they PASS
- [X] T115 Verify existing watcher functionality preserved (no regressions)

---

## Phase 8: Health Check Integration

**Purpose**: Extend health check system to monitor error recovery

- [X] T116 [P] Add check_circuit_breakers() method to health_check.py
- [X] T117 [P] Add check_service_degradation() method to health_check.py
- [X] T118 [P] Add check_restart_attempts() method to health_check.py
- [X] T119 Update health_check.run_health_check() to include new checks
- [X] T120 Update health alert creation to include circuit breaker and degradation status
- [X] T121 Write test_health_check_detects_open_circuits() in tests/test_integration_recovery.py
- [X] T122 Write test_health_check_detects_degraded_services() in tests/test_integration_recovery.py
- [X] T123 Run health check integration tests and verify they PASS

---

## Phase 9: End-to-End Testing

**Purpose**: Validate complete error recovery workflows

- [X] T124 [P] Write test_e2e_transient_failure_recovery() in tests/test_integration_recovery.py (network timeout → retry → success)
- [X] T125 [P] Write test_e2e_sustained_failure_circuit_breaker() in tests/test_integration_recovery.py (5 failures → circuit opens → cooldown → half-open → recovery)
- [X] T126 [P] Write test_e2e_service_crash_restart() in tests/test_integration_recovery.py (process crash → detect → restart → backoff → alert)
- [X] T127 [P] Write test_e2e_graceful_degradation() in tests/test_integration_recovery.py (non-critical fails → critical continues)
- [X] T128 [P] Write test_e2e_state_persistence_across_restart() in tests/test_integration_recovery.py (save state → restart system → load state → verify circuits/health preserved)
- [X] T129 Run all E2E tests and verify they PASS
- [X] T130 Verify all audit logs created correctly for recovery actions
- [X] T131 Verify all alerts created correctly in Needs_Action/

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final validation

- [X] T132 [P] Add environment variable configuration to .env.example (ERROR_RECOVERY_BASE_DELAY, ERROR_RECOVERY_MAX_ATTEMPTS, etc.)
- [X] T133 [P] Update quickstart.md with final integration examples
- [X] T134 [P] Create SETUP.md in specs/005-error-recovery/ with installation and configuration guide
- [X] T135 [P] Update CLAUDE.md with error recovery technology
- [X] T136 [P] Add docstrings to all error recovery classes and methods
- [X] T137 [P] Run pytest with coverage report and verify >90% coverage
- [X] T138 [P] Run linting (ruff, black) on error recovery module
- [X] T139 Validate quickstart.md examples work correctly
- [X] T140 Run full test suite (56 tests) and verify all PASS
- [X] T141 Manual testing: Simulate network failure and verify retry behavior
- [X] T142 Manual testing: Simulate sustained API failure and verify circuit breaker opens
- [X] T143 Manual testing: Kill watcher process and verify auto-restart
- [X] T144 Manual testing: Verify state persists across system restart

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Integration (Phase 7-8)**: Depends on all user stories being complete
- **E2E Testing (Phase 9)**: Depends on integration completion
- **Polish (Phase 10)**: Depends on all testing completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on retry but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Requires ServiceHealth from US3 but can be developed in parallel

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Core classes before decorators
- Decorators before integration
- Integration tests after implementation
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**: All 5 tasks can run in parallel

**Phase 2 (Foundational)**: Tasks T007-T010 can run in parallel after T006

**Phase 3 (US1 Tests)**: Tasks T013-T019 can run in parallel

**Phase 3 (US1 Implementation)**: Tasks T021-T025 can run in parallel after T020

**Phase 4 (US2 Tests)**: Tasks T036-T043 can run in parallel

**Phase 4 (US2 Implementation)**: Tasks T045-T052 can run in parallel after T044

**Phase 5 (US3 Tests)**: Tasks T067-T073 can run in parallel

**Phase 5 (US3 Implementation)**: Tasks T075-T079 can run in parallel after T074

**Phase 6 (US4 Tests)**: Tasks T086-T091 can run in parallel

**Phase 6 (US4 Implementation)**: Tasks T093-T098 can run in parallel after T092

**Phase 7 (Integration)**: Tasks T107-T111 can run in parallel

**Phase 8 (Health Check)**: Tasks T116-T118 can run in parallel

**Phase 9 (E2E Tests)**: Tasks T124-T128 can run in parallel

**Phase 10 (Polish)**: Tasks T132-T138 can run in parallel

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**MVP = User Story 1 (P1) only**: Automatic Retry with Exponential Backoff

This delivers immediate value:
- 80%+ of transient failures automatically recovered
- Centralized retry logic eliminates duplication
- Audit logging for all retry attempts
- Can be deployed independently

**MVP Tasks**: T001-T035 (35 tasks, ~4-6 hours)

### Incremental Delivery

1. **Sprint 1**: MVP (US1) - Retry with exponential backoff
2. **Sprint 2**: US2 - Circuit breaker pattern
3. **Sprint 3**: US3 - Graceful degradation
4. **Sprint 4**: US4 - Auto-restart
5. **Sprint 5**: Integration, E2E testing, polish

### Success Metrics

- [ ] 80%+ automatic recovery from transient failures (SC-001)
- [ ] Circuit breaker stops failing requests within 30 seconds (SC-002)
- [ ] System operational with 50% service failures (SC-003)
- [ ] Services restarted within 2 minutes (SC-004)
- [ ] Alerts created within 1 minute (SC-005)
- [ ] State persists across restarts 100% (SC-006)
- [ ] 100% audit trail coverage (SC-007)
- [ ] 70% reduction in manual intervention (SC-008)

---

## Task Summary

**Total Tasks**: 144
- Phase 1 (Setup): 5 tasks
- Phase 2 (Foundational): 7 tasks
- Phase 3 (US1 - Retry): 23 tasks
- Phase 4 (US2 - Circuit Breaker): 31 tasks
- Phase 5 (US3 - Graceful Degradation): 19 tasks
- Phase 6 (US4 - Auto-Restart): 21 tasks
- Phase 7 (Integration): 9 tasks
- Phase 8 (Health Check): 8 tasks
- Phase 9 (E2E Testing): 8 tasks
- Phase 10 (Polish): 13 tasks

**Parallel Opportunities**: 78 tasks marked [P] can run in parallel within their phase

**Test Coverage**: 56 test tasks (TDD approach)

**Format Validation**: ✅ All tasks follow checklist format with checkbox, ID, optional [P] and [Story] labels, and file paths
