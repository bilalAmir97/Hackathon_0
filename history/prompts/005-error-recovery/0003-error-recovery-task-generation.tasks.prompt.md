---
id: 0003
title: error-recovery-task-generation
stage: tasks
date: 2026-03-16
surface: agent
model: claude-sonnet-4-5-20250929
feature: 005-error-recovery
branch: 005-error-recovery
user: user
command: /sp.tasks
labels: ["error-recovery", "tasks", "tdd", "implementation", "test-driven"]
links:
  spec: specs/005-error-recovery/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-error-recovery/tasks.md
tests:
  - 56 test tasks defined (TDD approach)
---

## Prompt

/sp.tasks (invoked after planning phase completion)

## Response snapshot

Generated comprehensive task breakdown for Error Recovery System (005-error-recovery) with 144 tasks organized by user story:

**Task Organization by User Story:**

**Phase 1: Setup (5 tasks)**
- Module structure creation
- Test infrastructure setup
- Pytest configuration

**Phase 2: Foundational (7 tasks)**
- RecoveryState class with atomic writes, JSON schema versioning, corruption recovery
- State directory creation
- Foundation tests

**Phase 3: User Story 1 - Automatic Retry with Exponential Backoff (23 tasks)**
- TDD: 8 test tasks written FIRST (exponential backoff, jitter, transient vs permanent errors, max attempts)
- Implementation: RetryPolicy class with calculate_delay(), should_retry(), is_transient_error()
- Decorator: @with_retry with audit logging integration
- Integration tests

**Phase 4: User Story 2 - Circuit Breaker Pattern (31 tasks)**
- TDD: 9 test tasks written FIRST (state transitions, failure threshold, cooldown, half-open recovery)
- Implementation: CircuitBreaker class with 3-state machine (CLOSED/OPEN/HALF_OPEN)
- Decorator: @with_circuit_breaker with audit logging
- Combined retry + circuit breaker tests
- Alert creation when circuit opens

**Phase 5: User Story 3 - Graceful Degradation (19 tasks)**
- TDD: 8 test tasks written FIRST (service classification, degradation detection, automatic recovery)
- Implementation: ServiceHealth class with critical/non-critical classification
- Alert creation with rate limiting
- Integration tests

**Phase 6: User Story 4 - Auto-Restart for Failed Services (21 tasks)**
- TDD: 7 test tasks written FIRST (restart backoff, threshold, counter reset)
- Implementation: Restart tracking in ServiceHealth with backoff (0s, 30s, 60s, 120s)
- Health check integration for process detection
- Service restart logic with subprocess

**Phase 7: Integration & Watcher Migration (9 tasks)**
- Migrate gmail_watcher.py and whatsapp_watcher.py to use decorators
- Remove old retry logic (keep commented for rollback)
- Watcher integration tests

**Phase 8: Health Check Integration (8 tasks)**
- Add circuit breaker monitoring
- Add degradation detection
- Add restart attempt tracking

**Phase 9: End-to-End Testing (8 tasks)**
- E2E transient failure recovery
- E2E sustained failure circuit breaker
- E2E service crash restart
- E2E graceful degradation
- E2E state persistence across restart

**Phase 10: Polish & Cross-Cutting Concerns (13 tasks)**
- Documentation (SETUP.md, quickstart.md updates)
- Environment configuration
- Code quality (docstrings, linting, coverage >90%)
- Manual testing validation

**Key Metrics:**
- Total tasks: 144
- Test tasks: 56 (TDD approach)
- Parallel opportunities: 78 tasks marked [P]
- MVP scope: User Story 1 only (35 tasks, ~4-6 hours)
- Incremental delivery: 5 sprints (US1 → US2 → US3 → US4 → Integration/Polish)

**Success Criteria Mapped:**
- SC-001: US1 (80% automatic recovery)
- SC-002: US2 (circuit breaker within 30s)
- SC-003: US3 (50% service failures tolerated)
- SC-004: US4 (restart within 2 minutes)
- SC-005-008: Cross-cutting (alerts, persistence, audit, reduction in manual intervention)

## Outcome

- ✅ Impact: Complete implementation roadmap with 144 executable tasks. Enables TDD approach with tests written first. Each user story independently testable and deliverable. MVP (US1) delivers immediate value with 35 tasks. Clear parallel execution opportunities (78 tasks). Comprehensive test coverage (56 test tasks).
- 🧪 Tests: 56 test tasks defined across all phases - unit tests (RetryPolicy, CircuitBreaker, ServiceHealth, RecoveryState, decorators), integration tests (watcher migration, health check), E2E tests (complete recovery workflows)
- 📁 Files: 1 file created (tasks.md with 144 tasks)
- 🔁 Next prompts: `/sp.implement` to begin TDD implementation starting with MVP (User Story 1), or suggest ADR creation for 3 architectural decisions identified in planning phase
- 🧠 Reflection: Task breakdown is comprehensive and immediately executable. TDD approach ensures quality with tests written first. User story organization enables independent implementation and incremental delivery. MVP scope (US1) provides clear starting point. Parallel opportunities well-identified (78 tasks). Each task has specific file paths and clear acceptance criteria. Format validation confirms all 144 tasks follow checklist format (checkbox, ID, [P]/[Story] labels, file paths). Ready for implementation phase.

## Evaluation notes (flywheel)

- Failure modes observed: None - task generation completed successfully with all required structure
- Graders run and results (PASS/FAIL): Format validation - PASS (all 144 tasks follow checklist format), User story organization - PASS (4 stories with clear phases), Test coverage - PASS (56 test tasks with TDD approach)
- Prompt variant (if applicable): Standard /sp.tasks workflow with TDD emphasis
- Next experiment (smallest change to try): Proceed to /sp.implement with MVP scope (US1 - 35 tasks), suggest ADR creation for centralized error recovery, circuit breaker scope, and state persistence decisions
